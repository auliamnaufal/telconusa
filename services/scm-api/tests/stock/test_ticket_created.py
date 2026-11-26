from datetime import timedelta

from app.core import clock, ledger
from app.core.models import ProcessedEvent
from app.stock.models import StockRequest


def balance(db, warehouse, sku):
    db.expire_all()
    b = ledger.get_balance(db, warehouse, sku)
    return b.qty_physical, b.qty_reserved, b.qty_damaged


def drain_ont(db, warehouse="WH-BDG", qty=20):
    ledger.issue_extra(db, warehouse_code=warehouse, item_sku="ONT-01", qty=qty, ref_type="TEST", ref_no="drain")
    db.commit()


def test_enough_stock_reserves_everything_and_publishes_ready(send, seeded_db, assets, events_of, validate_event, make_ticket):
    response = send("ticket.created", make_ticket())
    assert response.status_code == 200 and response.json()["status"] == "processed"

    seeded_db.expire_all()
    request = seeded_db.query(StockRequest).one()
    assert request.status == "READY_TO_ISSUE"
    assert request.warehouse_code == "WH-BDG" and request.city_code == "BDG"
    assert [(l.item_sku, l.qty_required, l.unit) for l in request.lines] == [("ONT-01", 1, "UNIT"), ("CBL-FO", 50, "METER")]
    assert balance(seeded_db, "WH-BDG", "ONT-01") == (20, 1, 0)
    assert balance(seeded_db, "WH-BDG", "CBL-FO") == (18500, 50, 0)
    assert [c for c in assets.calls if c[0] == "reserve_units"] == [("reserve_units", {"sku": "ONT-01", "qty": 1, "request": request.stock_request_no})]

    remaining = request.reserved_until - clock.utcnow()
    assert timedelta(hours=71, minutes=59) < remaining <= timedelta(hours=72)

    (event_type, data), = events_of()
    assert event_type == "stockrequest.ready"
    assert data == {"stock_request_no": request.stock_request_no, "ticket_code": "TKT-000001", "status": "READY_TO_ISSUE"}
    validate_event("stockrequest.ready", data)


def test_missing_stock_holds_nothing_creates_purchase_request_and_publishes_pending(
    send, seeded_db, assets, procurement, events_of, validate_event, make_ticket
):
    drain_ont(seeded_db)

    assert send("ticket.created", make_ticket()).status_code == 200

    seeded_db.expire_all()
    request = seeded_db.query(StockRequest).one()
    assert request.status == "PENDING_STOCK"
    assert request.purchase_request_no == "PR-FAKE-0001"
    assert balance(seeded_db, "WH-BDG", "ONT-01") == (0, 0, 0)
    assert balance(seeded_db, "WH-BDG", "CBL-FO") == (18500, 0, 0), "kabel yang cukup pun tidak ditahan"
    assert not [c for c in assets.calls if c[0] == "reserve_units"]
    assert request.reserved_until is None

    (call,) = procurement.requests
    assert call["warehouse_code"] == "WH-BDG" and call["stock_request_no"] == request.stock_request_no
    assert [(s.item_sku, s.qty) for s in call["shortages"]] == [("ONT-01", 1)]

    (event_type, data), = events_of()
    assert event_type == "stockrequest.pending"
    assert data["missing_items"] == [{"item_sku": "ONT-01", "qty_short": 1}]
    assert data["purchase_request_no"] == "PR-FAKE-0001"
    validate_event("stockrequest.pending", data)


def test_shortage_counts_only_what_is_missing(send, seeded_db, procurement, make_ticket):
    ledger.issue_extra(seeded_db, warehouse_code="WH-BDG", item_sku="CBL-FO", qty=18480, ref_type="TEST", ref_no="drain")
    seeded_db.commit()  # tersisa 20 m kabel

    send("ticket.created", make_ticket())

    (call,) = procurement.requests
    assert [(s.item_sku, s.qty) for s in call["shortages"]] == [("CBL-FO", 30)]


def test_same_event_twice_creates_one_request(send, seeded_db, make_ticket):
    first = send("ticket.created", make_ticket(), event_id="evt_ABC123456789")
    second = send("ticket.created", make_ticket(), event_id="evt_ABC123456789")

    assert first.json()["status"] == "processed"
    assert second.json()["status"] == "duplicate_ignored"
    assert seeded_db.query(StockRequest).count() == 1
    assert balance(seeded_db, "WH-BDG", "CBL-FO")[1] == 50


def test_same_ticket_with_a_new_event_id_still_creates_one_request(send, seeded_db, make_ticket):
    send("ticket.created", make_ticket())
    send("ticket.created", make_ticket())

    assert seeded_db.query(StockRequest).count() == 1
    assert seeded_db.query(ProcessedEvent).count() == 2
    assert balance(seeded_db, "WH-BDG", "CBL-FO")[1] == 50


def test_availability_is_checked_in_the_ticket_city_only(send, seeded_db, procurement, make_ticket):
    drain_ont(seeded_db, "WH-SBY", 15)  # Bandung masih 20 ONT, Surabaya 0

    send("ticket.created", make_ticket("TKT-000002", city="SBY"))

    seeded_db.expire_all()
    request = seeded_db.query(StockRequest).one()
    assert request.warehouse_code == "WH-SBY"
    assert request.status == "PENDING_STOCK"
    assert procurement.requests[0]["warehouse_code"] == "WH-SBY"


def test_duplicate_skus_are_merged_into_one_line(send, seeded_db, make_ticket):
    send("ticket.created", make_ticket(items=[("CBL-FO", 30, "METER"), ("CBL-FO", 20, "METER")]))

    request = seeded_db.query(StockRequest).one()
    assert [(l.item_sku, l.qty_required) for l in request.lines] == [("CBL-FO", 50)]


def test_ticket_without_items_creates_nothing(send, seeded_db, events_of, make_ticket):
    assert send("ticket.created", make_ticket(items=[])).status_code == 200
    assert seeded_db.query(StockRequest).count() == 0
    assert events_of() == []


def test_unknown_item_is_rejected_loudly_and_can_be_retried(send, seeded_db, make_ticket):
    response = send("ticket.created", make_ticket(items=[("NOPE-99", 1, "UNIT")]), event_id="evt_RETRYABLE001")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "UNKNOWN_ITEM"
    assert seeded_db.query(StockRequest).count() == 0
    assert seeded_db.query(ProcessedEvent).count() == 0, "event tidak dicatat sehingga pengirim bisa mengulang"


def test_unknown_city_and_malformed_events_are_rejected(send, make_ticket):
    assert send("ticket.created", make_ticket(city="XXX")).json()["error"]["code"] == "UNKNOWN_CITY"
    assert send("ticket.created", {"ticket_code": "TKT-1"}).json()["error"]["code"] == "INVALID_EVENT"


def test_unsigned_ticket_created_is_rejected(client, make_ticket, seeded_db):
    response = client.post("/internal/events", json={"event_id": "evt_X", "event_type": "ticket.created", "data": make_ticket()})
    assert response.status_code == 401
    assert seeded_db.query(StockRequest).count() == 0
