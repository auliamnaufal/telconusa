import pytest

from app.core import ledger

SMALL = 5


@pytest.fixture
def approved_po(create_po, decide):
    def _make(qty=SMALL, item_sku="ONT-01"):
        po_no = create_po(qty, item_sku)
        assert decide(po_no, "SCM_MANAGER").json()["status"] == "APPROVED"
        return po_no

    return _make


@pytest.fixture
def receive(client, auth):
    def _receive(po_no, qty, item_sku="ONT-01", warehouse="WH-BDG", key=None):
        headers = auth("WAREHOUSE_STAFF", "EMP-0023")
        if key:
            headers["Idempotency-Key"] = key
        return client.post(
            f"/api/v1/purchase-orders/{po_no}/receipts",
            json={"warehouse_code": warehouse, "lines": [{"item_sku": item_sku, "qty": qty}]},
            headers=headers,
        )

    return _receive


def _physical(db, sku="ONT-01", warehouse="WH-BDG"):
    db.expire_all()
    return ledger.get_balance(db, warehouse, sku).qty_physical


def test_partial_then_full_receipt(approved_po, receive, seeded_db, assets, stock_requests, client, auth):
    po_no = approved_po()
    before = _physical(seeded_db)
    first = receive(po_no, 2)
    assert first.status_code == 201, first.text
    assert first.json()["gr_no"].startswith("GR-")
    assert first.json()["po_status"] == "PARTIALLY_RECEIVED"
    assert len(first.json()["serial_numbers"]) == 2
    assert _physical(seeded_db) == before + 2
    assert assets.registered[0]["qty"] == 2
    assert stock_requests.calls == [("ONT-01", "WH-BDG")]

    assert receive(po_no, 3).json()["po_status"] == "RECEIVED"
    detail = client.get(f"/api/v1/purchase-orders/{po_no}", headers=auth("SCM_MANAGER")).json()
    assert detail["lines"][0]["qty_received"] == 5
    assert len(detail["receipts"]) == 2


def test_non_serial_receipt_has_no_serials(approved_po, receive, assets):
    po_no = approved_po(100, "CBL-FO")
    response = receive(po_no, 100, "CBL-FO")
    assert response.json() == {"gr_no": response.json()["gr_no"], "po_status": "RECEIVED", "serial_numbers": []}
    assert assets.registered == []


def test_over_receipt_changes_nothing(approved_po, receive, seeded_db):
    po_no = approved_po()
    before = _physical(seeded_db)
    response = receive(po_no, SMALL + 1)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "OVER_RECEIPT"
    assert _physical(seeded_db) == before


def test_po_must_be_approved(create_po, receive):
    response = receive(create_po(SMALL), 1)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_TRANSITION"


def test_unknown_line_and_warehouse(approved_po, receive):
    po_no = approved_po()
    assert receive(po_no, 1, "CBL-FO").json()["error"]["code"] == "ITEM_NOT_IN_PO"
    assert receive(po_no, 1, warehouse="WH-XXX").json()["error"]["code"] == "UNKNOWN_WAREHOUSE"


def test_idempotent_receipt(approved_po, receive, seeded_db):
    po_no = approved_po()
    before = _physical(seeded_db)
    first = receive(po_no, 2, key="gr-1")
    assert receive(po_no, 2, key="gr-1").json() == first.json()
    assert _physical(seeded_db) == before + 2
