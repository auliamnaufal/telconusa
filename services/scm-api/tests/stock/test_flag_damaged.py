import pytest

from app.core import ledger
from app.core.models import AuditLog
from app.stock.models import StockRequest

BODY = {"lines": [{"item_sku": "ONT-01", "qty": 1}, {"item_sku": "CBL-FO", "qty": 50}]}
REPORT = [
    {"item_sku": "ONT-01", "used": 0, "returned": 1},
    {"item_sku": "CBL-FO", "used": 30, "returned": 20},
]


def issued(client, auth, create_request):
    no = create_request()
    assert client.post(f"/api/v1/stock-requests/{no}/issue", json=BODY, headers=auth("WAREHOUSE_STAFF")).status_code == 200
    return no


def flag(client, auth, no, body, role="WAREHOUSE_STAFF", key=None):
    headers = auth(role)
    if key:
        headers["Idempotency-Key"] = key
    return client.post(f"/api/v1/stock-requests/{no}/flag-damaged", json=body, headers=headers)


def returned(send, no):
    data = {"ticket_code": "TKT-000001", "stock_request_no": no, "reported_by": "EMP-0042", "lines": REPORT, "reported_at": "2026-11-25T10:00:00+07:00"}
    assert send("ticket.items_reported", data).status_code == 200


def cable(db):
    db.expire_all()
    b = ledger.get_balance(db, "WH-BDG", "CBL-FO")
    return b.qty_physical, b.qty_damaged, b.qty_available


def test_non_serial_damage_while_issued_is_recorded_on_the_line(client, auth, create_request, seeded_db):
    no = issued(client, auth, create_request)

    response = flag(client, auth, no, {"item_sku": "CBL-FO", "qty": 5, "notes": "terkelupas"})

    assert response.status_code == 200, response.text
    assert response.json() == {"stock_request_no": no, "item_sku": "CBL-FO", "qty_damaged": 5}
    seeded_db.expire_all()
    assert seeded_db.query(StockRequest).one().lines[1].qty_damaged == 5
    assert cable(seeded_db) == (18450, 0, 18450), "saldo baru berubah saat laporan pemakaian diproses"
    assert seeded_db.query(AuditLog).filter_by(action="stock_request.flag_damaged").count() == 1


def test_serial_damage_while_issued_makes_the_unit_faulty(client, auth, create_request, assets):
    no = issued(client, auth, create_request)

    response = flag(client, auth, no, {"item_sku": "ONT-01", "qty": 1, "serial_number": "SN-FAKE-0001"})

    assert response.status_code == 200
    assert response.json()["qty_damaged"] == 1
    assert assets.status["SN-FAKE-0001"] == "FAULTY"


def test_serial_damage_needs_a_serial_that_belongs_to_the_request(client, auth, create_request):
    no = issued(client, auth, create_request)
    assert flag(client, auth, no, {"item_sku": "ONT-01", "qty": 1}).json()["error"]["code"] == "SERIAL_NUMBER_REQUIRED"
    other = flag(client, auth, no, {"item_sku": "ONT-01", "qty": 1, "serial_number": "SN-FAKE-0009"})
    assert other.status_code == 409 and other.json()["error"]["code"] == "SERIAL_NOT_IN_REQUEST"


def test_damage_cannot_exceed_what_was_issued(client, auth, create_request):
    no = issued(client, auth, create_request)
    assert flag(client, auth, no, {"item_sku": "CBL-FO", "qty": 40}).status_code == 200
    over = flag(client, auth, no, {"item_sku": "CBL-FO", "qty": 11})
    assert over.status_code == 409
    assert over.json()["error"]["code"] == "DAMAGED_EXCEEDS_LIMIT"
    assert over.json()["error"]["details"] == {"item_sku": "CBL-FO", "already_damaged": 40, "requested": 11, "limit": 50}


def test_non_serial_damage_after_return_moves_stock_out_of_available(client, auth, send, create_request, seeded_db):
    no = issued(client, auth, create_request)
    returned(send, no)
    assert cable(seeded_db) == (18470, 0, 18470)

    response = flag(client, auth, no, {"item_sku": "CBL-FO", "qty": 3})

    assert response.status_code == 200
    assert cable(seeded_db) == (18470, 3, 18467)


def test_damage_after_return_is_limited_to_the_returned_quantity(client, auth, send, create_request):
    no = issued(client, auth, create_request)
    returned(send, no)
    assert flag(client, auth, no, {"item_sku": "CBL-FO", "qty": 21}).json()["error"]["code"] == "DAMAGED_EXCEEDS_LIMIT"


def test_serial_unit_after_return_goes_through_inspection_instead(client, auth, send, create_request):
    no = issued(client, auth, create_request)
    returned(send, no)
    response = flag(client, auth, no, {"item_sku": "ONT-01", "qty": 1, "serial_number": "SN-FAKE-0001"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "USE_UNIT_INSPECTION"


def test_only_issued_or_returned_requests_can_be_flagged(client, auth, create_request):
    no = create_request()
    response = flag(client, auth, no, {"item_sku": "CBL-FO", "qty": 1})
    assert response.status_code == 409 and response.json()["error"]["code"] == "INVALID_TRANSITION"


def test_flag_is_idempotent_and_role_protected(client, auth, create_request, seeded_db):
    no = issued(client, auth, create_request)
    first = flag(client, auth, no, {"item_sku": "CBL-FO", "qty": 5}, key="flag-1")
    second = flag(client, auth, no, {"item_sku": "CBL-FO", "qty": 5}, key="flag-1")
    assert first.json() == second.json() == {"stock_request_no": no, "item_sku": "CBL-FO", "qty_damaged": 5}
    assert flag(client, auth, no, {"item_sku": "CBL-FO", "qty": 1}, role="TECHNICIAN").status_code == 403
    assert flag(client, auth, no, {"item_sku": "NOPE-99", "qty": 1}).json()["error"]["code"] == "ITEM_NOT_ISSUED"
