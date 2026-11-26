import pytest

from app.core import ledger
from app.core.errors import ScmError
from app.core.models import StockMovement

WH = "WH-BDG"
SKU = "ONT-01"  # seed: 20 unit di WH-BDG, tanpa reservasi atau rusak


def kw(qty: int, warehouse: str = WH, sku: str = SKU, ref_no: str = "SR-2026-000001") -> dict:
    return {"warehouse_code": warehouse, "item_sku": sku, "qty": qty, "ref_type": "STOCK_REQUEST", "ref_no": ref_no}


def snapshot(db, warehouse: str = WH, sku: str = SKU) -> tuple[int, int, int]:
    balance = ledger.get_balance(db, warehouse, sku)
    return balance.qty_physical, balance.qty_reserved, balance.qty_damaged


def movements(db) -> int:
    return db.query(StockMovement).count()


def test_receive_creates_missing_balance_and_one_movement(seeded_db):
    db = seeded_db
    assert ledger.get_balance(db, "WH-BDG", "SIM-01") is None
    ledger.receive(db, **kw(100, sku="SIM-01"))
    db.commit()

    assert snapshot(db, sku="SIM-01") == (100, 0, 0)
    movement = db.query(StockMovement).filter_by(item_sku="SIM-01").one()
    assert (movement.type, movement.qty, movement.ref_no) == ("RECEIVE", 100, "SR-2026-000001")


def test_last_unit_cannot_be_reserved_twice(seeded_db):
    db = seeded_db
    ledger.receive(db, **kw(1, warehouse="WH-SBY", sku="RTR-AX"))
    ledger.reserve(db, **kw(1, warehouse="WH-SBY", sku="RTR-AX", ref_no="SR-2026-000001"))

    with pytest.raises(ScmError) as exc:
        ledger.reserve(db, **kw(1, warehouse="WH-SBY", sku="RTR-AX", ref_no="SR-2026-000002"))

    assert exc.value.code == "INSUFFICIENT_STOCK"
    assert exc.value.status == 409
    assert exc.value.details == {"sku": "RTR-AX", "warehouse_code": "WH-SBY", "requested": 1, "available": 0}


def test_available_is_physical_minus_reserved_minus_damaged_through_a_full_cycle(seeded_db):
    db = seeded_db
    steps = [
        (ledger.reserve, 5, (20, 5, 0)),
        (ledger.mark_damaged, 2, (20, 5, 2)),
        (ledger.issue, 3, (17, 2, 2)),
        (ledger.issue_extra, 1, (16, 2, 2)),
        (ledger.release, 2, (16, 0, 2)),
        (ledger.return_good, 1, (17, 0, 2)),
        (ledger.return_damaged, 1, (18, 0, 3)),
        (ledger.write_off, 2, (16, 0, 1)),
    ]
    for operation, qty, expected in steps:
        operation(db, **kw(qty))
        physical, reserved, damaged = snapshot(db)
        assert (physical, reserved, damaged) == expected, operation.__name__
        assert ledger.get_available(db, WH, SKU) == physical - reserved - damaged
        assert min(physical, reserved, damaged) >= 0


def test_damaged_stock_is_not_available_and_cannot_be_reserved(seeded_db):
    db = seeded_db
    ledger.mark_damaged(db, **kw(18))
    assert ledger.get_available(db, WH, SKU) == 2
    with pytest.raises(ScmError) as exc:
        ledger.reserve(db, **kw(3))
    assert exc.value.details["available"] == 2


def test_every_operation_writes_exactly_one_movement(seeded_db):
    db = seeded_db
    operations = [
        ledger.receive, ledger.reserve, ledger.release, ledger.reserve, ledger.issue,
        ledger.issue_extra, ledger.return_good, ledger.return_damaged, ledger.mark_damaged, ledger.write_off,
    ]
    before = movements(db)
    for index, operation in enumerate(operations, start=1):
        operation(db, **kw(1))
        assert movements(db) == before + index
    types = [m.type for m in db.query(StockMovement).order_by(StockMovement.created_at).all()]
    assert sorted(types) == sorted(
        ["RECEIVE", "RESERVE", "RELEASE", "RESERVE", "ISSUE", "ISSUE_EXTRA", "RETURN_GOOD", "RETURN_DAMAGED", "MARK_DAMAGED", "WRITE_OFF"]
    )


def test_each_change_bumps_the_version(seeded_db):
    db = seeded_db
    start = ledger.get_balance(db, WH, SKU).version
    ledger.reserve(db, **kw(1))
    ledger.release(db, **kw(1))
    db.commit()
    assert ledger.get_balance(db, WH, SKU).version == start + 2


@pytest.mark.parametrize(
    ("operation", "code"),
    [
        (ledger.issue, "RESERVATION_MISMATCH"),
        (ledger.release, "RESERVATION_MISMATCH"),
        (ledger.write_off, "DAMAGED_MISMATCH"),
    ],
)
def test_state_violations_change_nothing(seeded_db, operation, code):
    db = seeded_db
    before, moves = snapshot(db), movements(db)
    with pytest.raises(ScmError) as exc:
        operation(db, **kw(1))
    assert exc.value.code == code
    assert (snapshot(db), movements(db)) == (before, moves)


def test_issue_extra_and_mark_damaged_need_available_stock(seeded_db):
    db = seeded_db
    with pytest.raises(ScmError) as exc:
        ledger.issue_extra(db, **kw(21))
    assert exc.value.code == "INSUFFICIENT_STOCK"
    with pytest.raises(ScmError):
        ledger.mark_damaged(db, **kw(21))


@pytest.mark.parametrize("qty", [0, -3, True, 1.5])
def test_quantity_must_be_a_positive_integer(seeded_db, qty):
    with pytest.raises(ScmError) as exc:
        ledger.reserve(seeded_db, **kw(qty))
    assert exc.value.code == "INVALID_QUANTITY"
    assert exc.value.status == 422


def test_receive_rejects_unknown_warehouse_and_item(seeded_db):
    with pytest.raises(ScmError) as exc:
        ledger.receive(seeded_db, **kw(1, warehouse="WH-XXX"))
    assert exc.value.code == "UNKNOWN_WAREHOUSE"
    with pytest.raises(ScmError) as exc:
        ledger.receive(seeded_db, **kw(1, sku="NOPE-99"))
    assert exc.value.code == "UNKNOWN_ITEM"


def test_reserve_on_missing_balance_reports_zero_available(seeded_db):
    with pytest.raises(ScmError) as exc:
        ledger.reserve(seeded_db, **kw(1, warehouse="WH-SBY", sku="SIM-01"))
    assert exc.value.details["available"] == 0
