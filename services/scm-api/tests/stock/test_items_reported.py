from app.core import ledger
from app.stock.models import StockRequest

BODY = {"lines": [{"item_sku": "ONT-01", "qty": 1}, {"item_sku": "CBL-FO", "qty": 50}]}


def issued_request(client, auth, create_request):
    no = create_request()
    assert client.post(f"/api/v1/stock-requests/{no}/issue", json=BODY, headers=auth("WAREHOUSE_STAFF")).status_code == 200
    return no


def report(send, no, lines, ticket="TKT-000001", event_id=None):
    data = {"ticket_code": ticket, "stock_request_no": no, "reported_by": "EMP-0042", "lines": lines,
            "reported_at": "2026-11-25T10:00:00+07:00"}
    return send("ticket.items_reported", data, event_id=event_id)


def cable(db):
    db.expire_all()
    b = ledger.get_balance(db, "WH-BDG", "CBL-FO")
    return b.qty_physical, b.qty_reserved, b.qty_damaged


def returned_event(events_of):
    events = events_of("stock.returned")
    assert len(events) == 1
    return events[0][1]


EXACT = [
    {"item_sku": "ONT-01", "used": 1, "returned": 0, "serial_numbers_installed": ["SN-FAKE-0001"]},
    {"item_sku": "CBL-FO", "used": 30, "returned": 20},
]


def test_exact_report_updates_stock_installs_the_unit_and_publishes_returned(
    client, auth, send, create_request, seeded_db, assets, events_of, validate_event
):
    no = issued_request(client, auth, create_request)

    response = report(send, no, EXACT)

    assert response.status_code == 200 and response.json()["status"] == "processed"
    seeded_db.expire_all()
    request = seeded_db.query(StockRequest).one()
    assert request.status == "RETURNED" and request.discrepancy is False
    assert cable(seeded_db) == (18470, 0, 0)  # 18500 - 50 keluar + 20 kembali
    cable_line = request.lines[1]
    assert (cable_line.qty_issued, cable_line.qty_used, cable_line.qty_returned) == (50, 30, 20)
    assert assets.status["SN-FAKE-0001"] == "INSTALLED"
    assert not [c for c in assets.calls if c[0] == "mark_returned"]

    data = returned_event(events_of)
    assert data["has_discrepancy"] is False and data["status"] == "RETURNED"
    assert data["lines"] == [
        {"item_sku": "ONT-01", "issued": 1, "used": 1, "returned": 0, "damaged": 0},
        {"item_sku": "CBL-FO", "issued": 50, "used": 30, "returned": 20, "damaged": 0},
    ]
    validate_event("stock.returned", data)


def test_unused_serial_unit_comes_back_for_inspection_without_entering_stock(client, auth, send, create_request, seeded_db, assets):
    no = issued_request(client, auth, create_request)

    report(send, no, [{"item_sku": "ONT-01", "used": 0, "returned": 1}, {"item_sku": "CBL-FO", "used": 50, "returned": 0}])

    seeded_db.expire_all()
    assert seeded_db.query(StockRequest).one().discrepancy is False
    assert assets.status["SN-FAKE-0001"] == "RETURNED"
    assert ledger.get_balance(seeded_db, "WH-BDG", "ONT-01").qty_physical == 19, "masuk saldo setelah pemeriksaan (Slice C)"


def test_missing_quantity_marks_a_discrepancy_without_inventing_stock(client, auth, send, create_request, seeded_db, events_of):
    no = issued_request(client, auth, create_request)

    report(send, no, [EXACT[0], {"item_sku": "CBL-FO", "used": 30, "returned": 10}])

    seeded_db.expire_all()
    request = seeded_db.query(StockRequest).one()
    assert request.discrepancy is True and request.status == "RETURNED"
    assert cable(seeded_db) == (18460, 0, 0)
    assert returned_event(events_of)["has_discrepancy"] is True


def test_over_reporting_caps_the_returned_quantity(client, auth, send, create_request, seeded_db, events_of):
    no = issued_request(client, auth, create_request)

    report(send, no, [EXACT[0], {"item_sku": "CBL-FO", "used": 40, "returned": 20}])

    seeded_db.expire_all()
    assert cable(seeded_db) == (18460, 0, 0)  # hanya 10 m yang bisa kembali
    data = returned_event(events_of)
    assert data["has_discrepancy"] is True
    assert data["lines"][1] == {"item_sku": "CBL-FO", "issued": 50, "used": 40, "returned": 10, "damaged": 0}


def test_serial_report_without_the_installed_serial_is_a_discrepancy(client, auth, send, create_request, seeded_db):
    no = issued_request(client, auth, create_request)
    report(send, no, [{"item_sku": "ONT-01", "used": 1, "returned": 0}, {"item_sku": "CBL-FO", "used": 30, "returned": 20}])
    seeded_db.expire_all()
    assert seeded_db.query(StockRequest).one().discrepancy is True


def test_unreported_items_count_as_missing(client, auth, send, create_request, seeded_db, events_of):
    no = issued_request(client, auth, create_request)
    report(send, no, [EXACT[0]])
    seeded_db.expire_all()
    assert seeded_db.query(StockRequest).one().discrepancy is True
    assert cable(seeded_db) == (18450, 0, 0)


def test_flagged_damaged_quantity_enters_stock_as_damaged(client, auth, send, create_request, seeded_db, events_of):
    no = issued_request(client, auth, create_request)
    flagged = client.post(
        f"/api/v1/stock-requests/{no}/flag-damaged", json={"item_sku": "CBL-FO", "qty": 5}, headers=auth("WAREHOUSE_STAFF")
    )
    assert flagged.status_code == 200, flagged.text

    report(send, no, EXACT)

    seeded_db.expire_all()
    assert cable(seeded_db) == (18470, 0, 5)  # 15 baik + 5 rusak kembali
    assert ledger.get_available(seeded_db, "WH-BDG", "CBL-FO") == 18465
    assert returned_event(events_of)["lines"][1]["damaged"] == 5


def test_duplicate_report_does_not_return_stock_twice(client, auth, send, create_request, seeded_db, events_of):
    no = issued_request(client, auth, create_request)
    report(send, no, EXACT, event_id="evt_REPORT000001")
    report(send, no, EXACT, event_id="evt_REPORT000001")
    report(send, no, EXACT, event_id="evt_REPORT000002")  # event baru untuk permintaan yang sudah RETURNED

    seeded_db.expire_all()
    assert cable(seeded_db) == (18470, 0, 0)
    assert len(events_of("stock.returned")) == 1


def test_report_for_a_request_that_was_never_issued_is_ignored(send, create_request, seeded_db, events_of):
    no = create_request()
    response = report(send, no, EXACT)
    assert response.status_code == 200
    seeded_db.expire_all()
    assert seeded_db.query(StockRequest).one().status == "READY_TO_ISSUE"
    assert cable(seeded_db) == (18500, 50, 0)
    assert events_of("stock.returned") == []


def test_invalid_reports_are_rejected_loudly(client, auth, send, create_request):
    no = issued_request(client, auth, create_request)
    assert report(send, "SR-2026-999999", EXACT).json()["error"]["code"] == "STOCK_REQUEST_NOT_FOUND"
    assert report(send, no, EXACT, ticket="TKT-OTHER").json()["error"]["code"] == "TICKET_MISMATCH"
    assert report(send, no, [{"item_sku": "SIM-01", "used": 1, "returned": 0}]).json()["error"]["code"] == "ITEM_NOT_ISSUED"
    assert send("ticket.items_reported", {"ticket_code": "TKT-000001"}).json()["error"]["code"] == "INVALID_EVENT"


def test_extra_lines_are_reconciled_together_with_the_package(client, auth, send, create_request, seeded_db, events_of):
    no = issued_request(client, auth, create_request)
    extra = client.post(
        f"/api/v1/stock-requests/{no}/issue-extra", json={"lines": [{"item_sku": "CBL-FO", "qty": 10}]}, headers=auth("WAREHOUSE_STAFF")
    )
    assert extra.status_code == 200

    report(send, no, [EXACT[0], {"item_sku": "CBL-FO", "used": 45, "returned": 15}])

    seeded_db.expire_all()
    request = seeded_db.query(StockRequest).one()
    assert request.discrepancy is False
    assert cable(seeded_db) == (18455, 0, 0)  # 18500 - 60 + 15
    assert returned_event(events_of)["lines"][1] == {"item_sku": "CBL-FO", "issued": 60, "used": 45, "returned": 15, "damaged": 0}
    assert sum(l.qty_used for l in request.lines if l.item_sku == "CBL-FO") == 45
