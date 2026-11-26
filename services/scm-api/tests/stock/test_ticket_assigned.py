from app.stock.models import PendingAssignment, StockRequest


def assigned(technician, ticket="TKT-000001"):
    return {"ticket_code": ticket, "subscription_code": "SUB-000012", "technician_employee_id": technician,
            "assigned_by": "EMP-0010", "city_code": "BDG", "assigned_at": "2026-11-25T10:00:00+07:00"}


def technician_of(db):
    db.expire_all()
    return db.query(StockRequest).one().technician_employee_id


def test_assignment_after_request_fills_the_technician_without_changing_status(send, seeded_db, make_ticket):
    send("ticket.created", make_ticket())
    send("ticket.assigned", assigned("EMP-0042"))

    assert technician_of(seeded_db) == "EMP-0042"
    assert seeded_db.query(StockRequest).one().status == "READY_TO_ISSUE"


def test_assignment_before_request_is_kept_and_applied_when_the_request_is_created(send, seeded_db, make_ticket):
    send("ticket.assigned", assigned("EMP-0042"))
    assert seeded_db.query(StockRequest).count() == 0
    assert seeded_db.query(PendingAssignment).one().technician_employee_id == "EMP-0042"

    send("ticket.created", make_ticket())

    assert technician_of(seeded_db) == "EMP-0042"
    assert seeded_db.query(PendingAssignment).count() == 0


def test_reassignment_overrides_until_the_request_is_issued(send, seeded_db, make_ticket):
    send("ticket.created", make_ticket())
    send("ticket.assigned", assigned("EMP-0042"))
    send("ticket.assigned", assigned("EMP-0077"))

    assert technician_of(seeded_db) == "EMP-0077"


def test_duplicate_assignment_event_changes_nothing(send, seeded_db, make_ticket):
    send("ticket.created", make_ticket())
    send("ticket.assigned", assigned("EMP-0042"), event_id="evt_ASSIGN0001")
    send("ticket.assigned", assigned("EMP-0099"), event_id="evt_ASSIGN0001")

    assert technician_of(seeded_db) == "EMP-0042"


def test_assignment_after_issue_is_ignored(send, client, auth, seeded_db, make_ticket):
    send("ticket.created", make_ticket())
    send("ticket.assigned", assigned("EMP-0042"))
    no = seeded_db.query(StockRequest).one().stock_request_no
    issued = client.post(
        f"/api/v1/stock-requests/{no}/issue",
        json={"lines": [{"item_sku": "ONT-01", "qty": 1}, {"item_sku": "CBL-FO", "qty": 50}]},
        headers=auth("WAREHOUSE_STAFF"),
    )
    assert issued.status_code == 200, issued.text

    send("ticket.assigned", assigned("EMP-0099"))

    assert technician_of(seeded_db) == "EMP-0042"


def test_malformed_assignment_is_rejected(send):
    assert send("ticket.assigned", {"ticket_code": "TKT-000001"}).json()["error"]["code"] == "INVALID_EVENT"
