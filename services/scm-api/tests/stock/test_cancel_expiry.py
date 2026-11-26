from datetime import timedelta

from app.core import clock, ledger
from app.core.jobs import run_job_once
from app.core.models import AuditLog
from app.stock.models import StockRequest

BODY = {"lines": [{"item_sku": "ONT-01", "qty": 1}, {"item_sku": "CBL-FO", "qty": 50}]}


def cancel(client, auth, no, reason="pelanggan batal", role="WAREHOUSE_STAFF"):
    return client.post(f"/api/v1/stock-requests/{no}/cancel", json={"reason": reason}, headers=auth(role))


def snapshot(db, sku="CBL-FO", warehouse="WH-BDG"):
    db.expire_all()
    b = ledger.get_balance(db, warehouse, sku)
    return b.qty_physical, b.qty_reserved


def status(db, ticket="TKT-000001"):
    db.expire_all()
    return db.query(StockRequest).filter_by(ticket_code=ticket).one().status


def test_manual_cancel_releases_the_reservation_and_the_units(client, auth, create_request, seeded_db, assets):
    no = create_request()
    assert snapshot(seeded_db) == (18500, 50)

    response = cancel(client, auth, no)

    assert response.status_code == 200
    assert response.json() == {"stock_request_no": no, "status": "CANCELLED"}
    assert status(seeded_db) == "CANCELLED"
    assert snapshot(seeded_db) == (18500, 0)
    assert snapshot(seeded_db, "ONT-01") == (20, 0)
    assert assets.status["SN-FAKE-0001"] == "IN_STOCK"
    request = seeded_db.query(StockRequest).one()
    assert request.cancel_reason == "pelanggan batal" and request.reserved_until is None
    assert seeded_db.query(AuditLog).filter_by(action="stock_request.cancel", entity_id=no).count() == 1


def test_cancel_needs_a_reason_and_a_warehouse_role(client, auth, create_request):
    no = create_request()
    assert client.post(f"/api/v1/stock-requests/{no}/cancel", json={}, headers=auth("WAREHOUSE_STAFF")).status_code == 422
    assert cancel(client, auth, no, reason="").status_code == 422
    assert cancel(client, auth, no, role="TECHNICIAN").status_code == 403
    assert cancel(client, auth, no, role="SCM_MANAGER").status_code == 200


def test_issued_request_cannot_be_cancelled(client, auth, create_request):
    no = create_request()
    client.post(f"/api/v1/stock-requests/{no}/issue", json=BODY, headers=auth("WAREHOUSE_STAFF"))
    response = cancel(client, auth, no)
    assert response.status_code == 409 and response.json()["error"]["code"] == "INVALID_TRANSITION"


def test_pending_request_can_be_cancelled_without_touching_stock(client, auth, send, seeded_db, make_ticket):
    ledger.issue_extra(seeded_db, warehouse_code="WH-BDG", item_sku="ONT-01", qty=20, ref_type="TEST", ref_no="drain")
    seeded_db.commit()
    send("ticket.created", make_ticket())
    no = seeded_db.query(StockRequest).one().stock_request_no
    before = snapshot(seeded_db)

    assert cancel(client, auth, no).status_code == 200
    assert snapshot(seeded_db) == before
    assert status(seeded_db) == "CANCELLED"


def test_reservation_expires_after_72_hours(create_request, seeded_db, session_factory, frozen_clock, assets):
    no = create_request()

    frozen_clock.advance(hours=71)
    assert run_job_once("stock.expire_reservations", session_factory) == []
    assert status(seeded_db) == "READY_TO_ISSUE"

    frozen_clock.advance(hours=2)
    assert run_job_once("stock.expire_reservations", session_factory) == [no]

    assert status(seeded_db) == "CANCELLED"
    assert snapshot(seeded_db) == (18500, 0)
    assert snapshot(seeded_db, "ONT-01") == (20, 0)
    assert assets.status["SN-FAKE-0001"] == "IN_STOCK"
    assert seeded_db.query(StockRequest).one().cancel_reason == "RESERVATION_EXPIRED"
    audit = seeded_db.query(AuditLog).filter_by(action="stock_request.cancel").one()
    assert audit.actor == "system"


def test_running_the_expiry_job_twice_releases_once(create_request, seeded_db, session_factory, frozen_clock):
    create_request()
    frozen_clock.advance(hours=73)

    assert len(run_job_once("stock.expire_reservations", session_factory)) == 1
    assert run_job_once("stock.expire_reservations", session_factory) == []
    assert snapshot(seeded_db) == (18500, 0)


def test_pending_requests_and_issued_requests_never_expire(client, auth, send, create_request, seeded_db, session_factory, frozen_clock, make_ticket):
    issued_no = create_request("TKT-000001")
    client.post(f"/api/v1/stock-requests/{issued_no}/issue", json=BODY, headers=auth("WAREHOUSE_STAFF"))
    ledger.issue_extra(seeded_db, warehouse_code="WH-BDG", item_sku="ONT-01", qty=19, ref_type="TEST", ref_no="drain")
    seeded_db.commit()
    send("ticket.created", make_ticket("TKT-000002"))

    frozen_clock.advance(hours=200)

    assert run_job_once("stock.expire_reservations", session_factory) == []
    assert status(seeded_db, "TKT-000001") == "ISSUED"
    assert status(seeded_db, "TKT-000002") == "PENDING_STOCK"


def test_released_stock_serves_a_waiting_request(client, auth, send, seeded_db, assets, events_of, make_ticket):
    ledger.issue_extra(seeded_db, warehouse_code="WH-BDG", item_sku="ONT-01", qty=19, ref_type="TEST", ref_no="drain")
    seeded_db.commit()  # tinggal 1 ONT tersedia
    send("ticket.created", make_ticket("TKT-000001"))
    send("ticket.created", make_ticket("TKT-000002"))
    first = seeded_db.query(StockRequest).filter_by(ticket_code="TKT-000001").one().stock_request_no
    assert status(seeded_db, "TKT-000001") == "READY_TO_ISSUE"
    assert status(seeded_db, "TKT-000002") == "PENDING_STOCK"

    assert cancel(client, auth, first).status_code == 200

    assert status(seeded_db, "TKT-000002") == "READY_TO_ISSUE"
    ready_tickets = [data["ticket_code"] for _, data in events_of("stockrequest.ready")]
    assert ready_tickets == ["TKT-000001", "TKT-000002"]
