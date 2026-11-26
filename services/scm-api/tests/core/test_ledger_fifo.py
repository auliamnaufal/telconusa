import pytest
from sqlalchemy import func

from app.core import ledger
from app.core.errors import ScmError
from app.core.models import InventoryBalance, StockLot

WH, SKU = "WH-BDG", "SIM-01"  # seed: SIM-01 belum punya saldo di Bandung


def kw(qty, ref="GR-TEST", sku=SKU, warehouse=WH):
    return {"warehouse_code": warehouse, "item_sku": sku, "qty": qty, "ref_type": "TEST", "ref_no": ref}


def lots(db, sku=SKU, warehouse=WH):
    return [(lot.ref_no, lot.qty_remaining) for lot in ledger.get_lots(db, warehouse, sku)]


def lot_total(db, sku=SKU, warehouse=WH):
    return db.query(func.coalesce(func.sum(StockLot.qty_remaining), 0)).filter_by(item_sku=sku, warehouse_code=warehouse).scalar()


def assert_lots_match_good_stock(db):
    """Untuk semua SKU non-serial: jumlah lot = fisik - rusak."""
    for balance in db.query(InventoryBalance).filter(InventoryBalance.item_sku != "ONT-01"):
        assert lot_total(db, balance.item_sku, balance.warehouse_code) == balance.qty_physical - balance.qty_damaged, (
            balance.warehouse_code, balance.item_sku,
        )


def test_each_receipt_is_its_own_lot_and_issue_takes_the_oldest_first(seeded_db):
    db = seeded_db
    ledger.receive(db, **kw(10, "GR-A"))
    ledger.receive(db, **kw(5, "GR-B"))

    ledger.issue_extra(db, **kw(12, "SR-1"))

    assert lots(db) == [("GR-B", 3)], "GR-A habis dulu, sisanya diambil dari GR-B"
    assert ledger.get_balance(db, WH, SKU).qty_physical == 3


def test_issue_after_reservation_also_consumes_the_oldest_lot(seeded_db):
    db = seeded_db
    ledger.receive(db, **kw(4, "GR-A"))
    ledger.receive(db, **kw(4, "GR-B"))
    ledger.reserve(db, **kw(6, "SR-1"))

    ledger.issue(db, **kw(6, "SR-1"))

    assert lots(db) == [("GR-B", 2)]


def test_reserve_and_release_do_not_touch_lots(seeded_db):
    db = seeded_db
    ledger.receive(db, **kw(10, "GR-A"))
    ledger.reserve(db, **kw(4))
    ledger.release(db, **kw(4))
    assert lots(db) == [("GR-A", 10)]


def test_good_returns_become_a_new_lot_at_the_end(seeded_db):
    db = seeded_db
    ledger.receive(db, **kw(10, "GR-A"))
    ledger.issue_extra(db, **kw(4, "SR-1"))
    ledger.return_good(db, **kw(3, "SR-1"))
    ledger.receive(db, **kw(5, "GR-B"))

    assert lots(db) == [("GR-A", 6), ("SR-1", 3), ("GR-B", 5)]


def test_damaged_stock_leaves_the_lots_so_lots_always_equal_good_stock(seeded_db):
    db = seeded_db
    ledger.receive(db, **kw(10, "GR-A"))
    ledger.receive(db, **kw(10, "GR-B"))

    ledger.mark_damaged(db, **kw(12))  # 12 unit rusak diambil dari lot tertua
    assert lots(db) == [("GR-B", 8)]
    ledger.return_damaged(db, **kw(3, "SR-1"))  # rusak kembali dari lapangan: tidak menambah stok baik
    ledger.write_off(db, **kw(5, "WO-1"))  # hapus buku stok rusak: tidak mengubah stok baik

    assert lots(db) == [("GR-B", 8)]
    assert_lots_match_good_stock(db)


def test_fifo_holds_across_a_long_mixed_sequence(seeded_db):
    db = seeded_db
    ledger.issue_extra(db, **kw(50, "SR-1", "CBL-FO"))  # lot awal seed 18.500 m
    ledger.receive(db, **kw(100, "GR-1", "CBL-FO"))
    ledger.reserve(db, **kw(30, "SR-2", "CBL-FO"))
    ledger.issue(db, **kw(30, "SR-2", "CBL-FO"))
    ledger.return_good(db, **kw(10, "SR-2", "CBL-FO"))
    ledger.mark_damaged(db, **kw(5, "SR-2", "CBL-FO"))
    assert_lots_match_good_stock(db)
    assert lots(db, "CBL-FO")[0] == ("SEED", 18500 - 50 - 30 - 5)


def test_serial_items_have_no_lots(seeded_db):
    db = seeded_db
    ledger.receive(db, **kw(3, "GR-1", "ONT-01"))
    ledger.issue_extra(db, **kw(2, "SR-1", "ONT-01"))
    assert db.query(StockLot).filter_by(item_sku="ONT-01").count() == 0


def test_lots_that_do_not_cover_the_issue_fail_loudly_and_change_nothing(seeded_db):
    db = seeded_db
    ledger.receive(db, **kw(5, "GR-A"))
    db.query(StockLot).delete()  # data tidak konsisten: saldo ada, lot hilang
    before = ledger.get_balance(db, WH, SKU).qty_physical

    with pytest.raises(ScmError) as exc:
        ledger.issue_extra(db, **kw(3, "SR-1"))

    assert exc.value.code == "LOT_MISMATCH" and exc.value.status == 409
    assert ledger.get_balance(db, WH, SKU).qty_physical == before


def test_seed_creates_one_opening_lot_per_non_serial_balance(seeded_db):
    assert lots(seeded_db, "CBL-FO", "WH-BDG") == [("SEED", 18500)]
    assert lots(seeded_db, "SIM-01", "WH-BKS") == [("SEED", 2500)]
    assert lots(seeded_db, "ONT-01", "WH-BDG") == []
    assert_lots_match_good_stock(seeded_db)
