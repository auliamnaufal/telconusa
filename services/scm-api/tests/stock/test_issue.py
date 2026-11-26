import pytest

from app.core import ledger
from app.core.models import AuditLog, IdempotencyKey
from app.stock.models import StockRequest

BODY = {"lines": [{"item_sku": "ONT-01", "qty": 1}, {"item_sku": "CBL-FO", "qty": 50}]}


def issue(client, auth, no, body=None, role="WAREHOUSE_STAFF", key=None, sub="EMP-0020"):
    headers = auth(role, sub)
    if key:
        headers["Idempotency-Key"] = key
    return client.post(f"/api/v1/stock-requests/{no}/issue", json=body or BODY, headers=headers)


def balance(db, sku, warehouse="WH-BDG"):
    db.expire_all()
    b = ledger.get_balance(db, warehouse, sku)
    return b.qty_physical, b.qty_reserved, b.qty_damaged


def test_issue_hands_the_package_to_the_technician(client, auth, create_request, seeded_db, assets, events_of, validate_event):
    no = create_request()

    response = issue(client, auth, no)

    assert response.status_code == 200, response.text
    assert response.json() == {"stock_request_no": no, "status": "ISSUED", "unit_status": "WITH_TECHNICIAN"}
    seeded_db.expire_all()
    request = seeded_db.query(StockRequest).one()
    assert request.status == "ISSUED" and request.reserved_until is None
    assert [(l.item_sku, l.qty_issued) for l in request.lines] == [("ONT-01", 1), ("CBL-FO", 50)]
    assert balance(seeded_db, "ONT-01") == (19, 0, 0)
    assert balance(seeded_db, "CBL-FO") == (18450, 0, 0)
    assert assets.status["SN-FAKE-0001"] == "WITH_TECHNICIAN"

    issued = [data for _, data in events_of("stock.issued")]
    assert len(issued) == 1
    assert issued[0]["technician_employee_id"] == "EMP-0042" and issued[0]["issued_by"] == "EMP-0020"
    assert issued[0]["lines"] == [
        {"item_sku": "ONT-01", "qty": 1, "unit": "UNIT", "serial_numbers": ["SN-FAKE-0001"]},
        {"item_sku": "CBL-FO", "qty": 50, "unit": "METER"},
    ]
    validate_event("stock.issued", issued[0])
    assert seeded_db.query(AuditLog).filter_by(action="stock_request.issue", entity_id=no).count() == 1


def test_omitted_serial_numbers_default_to_the_reserved_units(client, auth, create_request, assets):
    no = create_request()
    assert issue(client, auth, no).status_code == 200
    assert assets.calls[-1] == ("mark_with_technician", {"serials": ["SN-FAKE-0001"], "tech": "EMP-0042"})


def test_explicit_reserved_serial_is_accepted(client, auth, create_request):
    no = create_request()
    body = {"lines": [{"item_sku": "ONT-01", "qty": 1, "serial_numbers": ["SN-FAKE-0001"]}, {"item_sku": "CBL-FO", "qty": 50}]}
    assert issue(client, auth, no, body).status_code == 200


def test_serial_outside_the_reservation_is_refused_and_nothing_changes(client, auth, create_request, seeded_db, assets):
    no = create_request()
    body = {"lines": [{"item_sku": "ONT-01", "qty": 1, "serial_numbers": ["SN-FAKE-0007"]}, {"item_sku": "CBL-FO", "qty": 50}]}

    response = issue(client, auth, no, body)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SERIAL_NOT_RESERVED"
    seeded_db.expire_all()
    assert seeded_db.query(StockRequest).one().status == "READY_TO_ISSUE"
    assert balance(seeded_db, "ONT-01") == (20, 1, 0)
    assert balance(seeded_db, "CBL-FO") == (18500, 50, 0)
    assert assets.status["SN-FAKE-0001"] == "RESERVED"


def test_second_issue_without_idempotency_key_is_an_invalid_transition(client, auth, create_request):
    no = create_request()
    assert issue(client, auth, no).status_code == 200
    again = issue(client, auth, no)
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "INVALID_TRANSITION"


def test_pending_request_cannot_be_issued(client, auth, send, seeded_db, make_ticket):
    ledger.issue_extra(seeded_db, warehouse_code="WH-BDG", item_sku="ONT-01", qty=20, ref_type="TEST", ref_no="drain")
    seeded_db.commit()
    send("ticket.created", make_ticket())
    no = seeded_db.query(StockRequest).one().stock_request_no
    response = issue(client, auth, no)
    assert response.status_code == 409 and response.json()["error"]["code"] == "INVALID_TRANSITION"


def test_issue_needs_an_assigned_technician(client, auth, create_request, seeded_db):
    no = create_request(technician=None)
    response = issue(client, auth, no)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TECHNICIAN_NOT_ASSIGNED"
    assert balance(seeded_db, "CBL-FO") == (18500, 50, 0)


@pytest.mark.parametrize(
    "lines",
    [
        [{"item_sku": "ONT-01", "qty": 2}, {"item_sku": "CBL-FO", "qty": 50}],
        [{"item_sku": "ONT-01", "qty": 1}],
        [{"item_sku": "ONT-01", "qty": 1}, {"item_sku": "CBL-FO", "qty": 50}, {"item_sku": "SIM-01", "qty": 1}],
    ],
)
def test_lines_must_equal_the_package(client, auth, create_request, lines):
    no = create_request()
    response = issue(client, auth, no, {"lines": lines})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ISSUE_LINES_MISMATCH"


def test_same_idempotency_key_issues_once(client, auth, create_request, seeded_db, events_of):
    no = create_request()

    first = issue(client, auth, no, key="issue-1")
    second = issue(client, auth, no, key="issue-1")

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert len(events_of("stock.issued")) == 1
    assert balance(seeded_db, "CBL-FO") == (18450, 0, 0)
    assert seeded_db.query(IdempotencyKey).count() == 1


@pytest.mark.parametrize("role", ["TECHNICIAN", "PROCUREMENT_STAFF", "CS_AGENT", "DIRECTOR"])
def test_only_warehouse_roles_can_issue(client, auth, create_request, role):
    no = create_request()
    assert issue(client, auth, no, role=role).status_code == 403


def test_issue_requires_a_token_and_a_valid_body(client, auth, create_request):
    no = create_request()
    assert client.post(f"/api/v1/stock-requests/{no}/issue", json=BODY).status_code == 401
    assert issue(client, auth, no, {"lines": []}).status_code == 422
    assert issue(client, auth, no, {"lines": [{"item_sku": "CBL-FO", "qty": 0}]}).status_code == 422
    assert issue(client, auth, "SR-2026-999999").status_code == 404
    assert issue(client, auth, no, role="SCM_MANAGER").status_code == 200
