from app.core import ledger
from app.stock.models import StockRequest

BODY = {"lines": [{"item_sku": "ONT-01", "qty": 1}, {"item_sku": "CBL-FO", "qty": 50}]}


def issue(client, auth, no):
    response = client.post(f"/api/v1/stock-requests/{no}/issue", json=BODY, headers=auth("WAREHOUSE_STAFF"))
    assert response.status_code == 200, response.text


def extra(client, auth, no, lines, key=None, role="WAREHOUSE_STAFF"):
    headers = auth(role)
    if key:
        headers["Idempotency-Key"] = key
    return client.post(f"/api/v1/stock-requests/{no}/issue-extra", json={"lines": lines}, headers=headers)


def physical(db, sku):
    db.expire_all()
    return ledger.get_balance(db, "WH-BDG", sku).qty_physical


def test_extra_line_is_added_to_the_same_ticket_and_published(client, auth, create_request, seeded_db, events_of, validate_event):
    ledger.receive(seeded_db, warehouse_code="WH-BDG", item_sku="RTR-AX", qty=5, ref_type="TEST", ref_no="seed")
    seeded_db.commit()
    no = create_request()
    issue(client, auth, no)

    response = extra(client, auth, no, [{"item_sku": "RTR-AX", "qty": 1}])

    assert response.status_code == 200, response.text
    assert response.json() == {"stock_request_no": no, "status": "ISSUED", "lines_added": 1}
    seeded_db.expire_all()
    request = seeded_db.query(StockRequest).one()
    assert request.status == "ISSUED"
    last = request.lines[-1]
    assert (last.item_sku, last.qty_issued, last.is_extra) == ("RTR-AX", 1, True)
    assert physical(seeded_db, "RTR-AX") == 4
    published = [data for _, data in events_of("stock.issued")]
    assert len(published) == 2
    assert published[1]["lines"] == [{"item_sku": "RTR-AX", "qty": 1, "unit": "UNIT"}]
    validate_event("stock.issued", published[1])


def test_extra_serial_item_takes_the_next_unit_to_the_technician(client, auth, create_request, assets, events_of):
    no = create_request()
    issue(client, auth, no)

    response = extra(client, auth, no, [{"item_sku": "ONT-01", "qty": 1}])

    assert response.status_code == 200
    assert assets.status["SN-FAKE-0002"] == "WITH_TECHNICIAN"
    assert events_of("stock.issued")[-1][1]["lines"][0]["serial_numbers"] == ["SN-FAKE-0002"]


def test_extra_before_issue_is_an_invalid_transition(client, auth, create_request):
    no = create_request()
    response = extra(client, auth, no, [{"item_sku": "CBL-FO", "qty": 5}])
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_TRANSITION"


def test_extra_without_stock_is_refused_and_changes_nothing(client, auth, create_request, seeded_db):
    no = create_request()
    issue(client, auth, no)

    response = extra(client, auth, no, [{"item_sku": "RTR-AX", "qty": 1}])  # tidak ada RTR-AX di Bandung

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INSUFFICIENT_STOCK"
    assert seeded_db.query(StockRequest).one().lines[-1].item_sku == "CBL-FO"


def test_extra_is_idempotent(client, auth, create_request, seeded_db, events_of):
    no = create_request()
    issue(client, auth, no)
    before = physical(seeded_db, "CBL-FO")

    first = extra(client, auth, no, [{"item_sku": "CBL-FO", "qty": 10}], key="extra-1")
    second = extra(client, auth, no, [{"item_sku": "CBL-FO", "qty": 10}], key="extra-1")

    assert first.json() == second.json()
    assert physical(seeded_db, "CBL-FO") == before - 10
    assert len(events_of("stock.issued")) == 2


def test_extra_needs_warehouse_role_and_valid_input(client, auth, create_request):
    no = create_request()
    issue(client, auth, no)
    assert extra(client, auth, no, [{"item_sku": "CBL-FO", "qty": 5}], role="TECHNICIAN").status_code == 403
    assert extra(client, auth, no, []).status_code == 422
    assert extra(client, auth, no, [{"item_sku": "NOPE-99", "qty": 1}]).json()["error"]["code"] == "UNKNOWN_ITEM"
