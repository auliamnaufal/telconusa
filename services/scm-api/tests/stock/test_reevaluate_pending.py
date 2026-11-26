from app.core import ledger
from app.core.ports import ports
from app.stock.models import StockRequest


def drain(db, sku="ONT-01", qty=20, warehouse="WH-BDG"):
    ledger.issue_extra(db, warehouse_code=warehouse, item_sku=sku, qty=qty, ref_type="TEST", ref_no="drain")
    db.commit()


def arrive(db, assets, sku="ONT-01", qty=1, warehouse="WH-BDG"):
    ledger.receive(db, warehouse_code=warehouse, item_sku=sku, qty=qty, ref_type="TEST", ref_no="GR-TEST")
    if sku == "ONT-01":
        assets.stock(sku, warehouse, qty)
    db.commit()


def reevaluate(db, sku="ONT-01", warehouse="WH-BDG"):
    result = ports.stock_requests.reevaluate_pending(db, item_sku=sku, warehouse_code=warehouse)
    db.commit()
    return result


def statuses(db):
    db.expire_all()
    return {r.ticket_code: r.status for r in db.query(StockRequest).all()}


def test_registered_port_is_the_real_service():
    from app.stock.service import StockRequestService

    assert isinstance(ports.stock_requests, StockRequestService)


def test_oldest_pending_request_is_served_first(send, seeded_db, assets, events_of, make_ticket):
    drain(seeded_db)
    send("ticket.created", make_ticket("TKT-000001"))
    send("ticket.created", make_ticket("TKT-000002"))
    arrive(seeded_db, assets, qty=1)

    ready = reevaluate(seeded_db)

    seeded_db.expire_all()
    first = seeded_db.query(StockRequest).filter_by(ticket_code="TKT-000001").one()
    assert ready == [first.stock_request_no]
    assert statuses(seeded_db) == {"TKT-000001": "READY_TO_ISSUE", "TKT-000002": "PENDING_STOCK"}
    assert first.reserved_until is not None
    assert [d["ticket_code"] for _, d in events_of("stockrequest.ready")] == ["TKT-000001"]
    b = ledger.get_balance(seeded_db, "WH-BDG", "ONT-01")
    assert (b.qty_physical, b.qty_reserved) == (1, 1)


def test_calling_again_serves_nobody_and_publishes_nothing_new(send, seeded_db, assets, events_of, make_ticket):
    drain(seeded_db)
    send("ticket.created", make_ticket("TKT-000001"))
    arrive(seeded_db, assets, qty=1)
    assert len(reevaluate(seeded_db)) == 1

    assert reevaluate(seeded_db) == []
    assert len(events_of("stockrequest.ready")) == 1


def test_request_still_short_on_another_line_stays_pending_and_holds_nothing(send, seeded_db, assets, make_ticket):
    drain(seeded_db)
    drain(seeded_db, "CBL-FO", 18500)
    send("ticket.created", make_ticket("TKT-000001"))
    arrive(seeded_db, assets, qty=1)  # ONT tiba, kabel belum

    assert reevaluate(seeded_db) == []

    assert statuses(seeded_db) == {"TKT-000001": "PENDING_STOCK"}
    b = ledger.get_balance(seeded_db, "WH-BDG", "ONT-01")
    assert b.qty_reserved == 0


def test_other_warehouses_and_skus_are_not_affected(send, seeded_db, assets, make_ticket):
    drain(seeded_db, qty=20, warehouse="WH-BDG")
    send("ticket.created", make_ticket("TKT-000001"))
    arrive(seeded_db, assets, qty=1, warehouse="WH-SBY")

    assert reevaluate(seeded_db, warehouse="WH-SBY") == []
    assert reevaluate(seeded_db, sku="CBL-FO", warehouse="WH-BDG") == []
    assert statuses(seeded_db) == {"TKT-000001": "PENDING_STOCK"}
