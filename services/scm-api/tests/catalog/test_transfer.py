"""SCM-D-10: transfer antar-gudang dengan konfirmasi terima.

Seed: CBL-FO WH-BKS 15.000, WH-SBY 12.000 (ROP 2.000); ONT-01 bernomor seri.
"""
import pytest

from app.core.models import AuditLog, InventoryBalance, StockLot, StockMovement


def _balance(db, warehouse: str, sku: str) -> InventoryBalance:
    db.expire_all()
    return db.query(InventoryBalance).filter_by(warehouse_code=warehouse, item_sku=sku).one()


def _create(client, auth, lines=None, src="WH-BKS", dst="WH-SBY", role="WAREHOUSE_STAFF"):
    body = {"from_warehouse_code": src, "to_warehouse_code": dst, "lines": lines or [{"item_sku": "CBL-FO", "qty": 1000}]}
    return client.post("/api/v1/transfers", json=body, headers=auth(role))


def test_full_flow_moves_stock_only_after_receive(client, auth, seeded_db):
    created = _create(client, auth)
    assert created.status_code == 201, created.text
    transfer = created.json()
    assert transfer["transfer_no"].startswith("TRF-") and transfer["status"] == "REQUESTED"
    assert _balance(seeded_db, "WH-BKS", "CBL-FO").qty_physical == 15000

    dispatched = client.post(f"/api/v1/transfers/{transfer['transfer_no']}/dispatch", headers=auth("WAREHOUSE_STAFF"))
    assert dispatched.status_code == 200, dispatched.text
    assert dispatched.json()["status"] == "IN_TRANSIT"
    assert _balance(seeded_db, "WH-BKS", "CBL-FO").qty_physical == 14000
    assert _balance(seeded_db, "WH-SBY", "CBL-FO").qty_physical == 12000  # belum berubah selama di jalan

    received = client.post(f"/api/v1/transfers/{transfer['transfer_no']}/receive", headers=auth("SCM_MANAGER"))
    assert received.status_code == 200, received.text
    body = received.json()
    assert body["status"] == "RECEIVED" and body["received_by"] == "EMP-0001" and body["received_at"].endswith("+07:00")
    assert _balance(seeded_db, "WH-SBY", "CBL-FO").qty_physical == 13000

    movements = seeded_db.query(StockMovement).filter_by(ref_type="TRANSFER", ref_no=transfer["transfer_no"]).all()
    assert sorted((m.warehouse_code, m.type, m.qty) for m in movements) == [("WH-BKS", "ISSUE_EXTRA", 1000), ("WH-SBY", "RECEIVE", 1000)]
    actions = {row.action for row in seeded_db.query(AuditLog).filter_by(entity="Transfer", entity_id=transfer["transfer_no"])}
    assert actions == {"transfer.create", "transfer.dispatch", "transfer.receive"}


def test_fifo_lots_follow_the_goods(client, auth, seeded_db):
    no = _create(client, auth).json()["transfer_no"]
    client.post(f"/api/v1/transfers/{no}/dispatch", headers=auth("WAREHOUSE_STAFF"))
    client.post(f"/api/v1/transfers/{no}/receive", headers=auth("WAREHOUSE_STAFF"))
    seeded_db.expire_all()
    lot_total = lambda wh: sum(lot.qty_remaining for lot in seeded_db.query(StockLot).filter_by(warehouse_code=wh, item_sku="CBL-FO"))
    assert lot_total("WH-BKS") == 14000
    assert lot_total("WH-SBY") == 13000
    assert seeded_db.query(StockLot).filter_by(warehouse_code="WH-SBY", item_sku="CBL-FO", ref_no=no).count() == 1


def test_same_warehouse_is_422(client, auth, seeded_db):
    response = _create(client, auth, src="WH-BDG", dst="WH-BDG")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SAME_WAREHOUSE"


def test_serialized_items_wait_for_asset_port(client, auth, seeded_db):
    response = _create(client, auth, lines=[{"item_sku": "ONT-01", "qty": 2}])
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SERIAL_TRANSFER_NOT_SUPPORTED"
    assert _balance(seeded_db, "WH-BKS", "ONT-01").qty_physical == 40


@pytest.mark.parametrize(
    "lines, code",
    [
        ([{"item_sku": "XXX-99", "qty": 1}], "ITEM_NOT_FOUND"),
        ([{"item_sku": "CBL-FO", "qty": 1}, {"item_sku": "CBL-FO", "qty": 2}], "DUPLICATE_TRANSFER_LINE"),
    ],
)
def test_invalid_lines_are_422(client, auth, seeded_db, lines, code):
    response = _create(client, auth, lines=lines)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == code


def test_unknown_warehouse_is_422(client, auth, seeded_db):
    assert _create(client, auth, dst="WH-XXX").json()["error"]["code"] == "WAREHOUSE_NOT_FOUND"


def test_dispatch_more_than_available_is_rejected_and_nothing_moves(client, auth, seeded_db):
    no = _create(client, auth, lines=[{"item_sku": "SIM-01", "qty": 1}, {"item_sku": "CBL-FO", "qty": 999999}]).json()["transfer_no"]
    response = client.post(f"/api/v1/transfers/{no}/dispatch", headers=auth("WAREHOUSE_STAFF"))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INSUFFICIENT_STOCK"
    assert _balance(seeded_db, "WH-BKS", "SIM-01").qty_physical == 2500
    assert client.post(f"/api/v1/transfers/{no}/receive", headers=auth("WAREHOUSE_STAFF")).status_code == 409


def test_status_order_is_enforced(client, auth, seeded_db):
    no = _create(client, auth).json()["transfer_no"]
    early = client.post(f"/api/v1/transfers/{no}/receive", headers=auth("WAREHOUSE_STAFF"))
    assert early.status_code == 409 and early.json()["error"]["code"] == "INVALID_TRANSITION"
    assert client.post(f"/api/v1/transfers/{no}/dispatch", headers=auth("WAREHOUSE_STAFF")).status_code == 200
    again = client.post(f"/api/v1/transfers/{no}/dispatch", headers=auth("WAREHOUSE_STAFF"))
    assert again.status_code == 409
    assert _balance(seeded_db, "WH-BKS", "CBL-FO").qty_physical == 14000


def test_dispatch_is_idempotent_with_key(client, auth, seeded_db):
    no = _create(client, auth).json()["transfer_no"]
    headers = {**auth("WAREHOUSE_STAFF"), "Idempotency-Key": "trf-dispatch-1"}
    first = client.post(f"/api/v1/transfers/{no}/dispatch", headers=headers)
    second = client.post(f"/api/v1/transfers/{no}/dispatch", headers=headers)
    assert first.status_code == second.status_code == 200
    assert _balance(seeded_db, "WH-BKS", "CBL-FO").qty_physical == 14000


def test_unknown_transfer_is_404(client, auth, seeded_db):
    assert client.post("/api/v1/transfers/TRF-2026-9999/dispatch", headers=auth("WAREHOUSE_STAFF")).status_code == 404


@pytest.mark.parametrize("role", ["DIRECTOR", "PROCUREMENT_STAFF"])
def test_only_manager_and_warehouse_staff_can_transfer(client, auth, seeded_db, role):
    assert _create(client, auth, role=role).status_code == 403


def test_balances_mark_overstock_as_transfer_hint(client, auth, seeded_db):
    rows = client.get("/api/v1/stock/balances?item_sku=ONT-01", headers=auth("SCM_MANAGER")).json()
    # ROP 10: WH-BKS 39 > 20 kelebihan; WH-BDG 20 dan WH-SBY 15 tidak.
    assert {row["warehouse_code"]: row["overstock"] for row in rows} == {"WH-BDG": False, "WH-BKS": True, "WH-SBY": False}
