from app.core import ledger


def drain(db, qty, sku="ONT-01", warehouse="WH-BDG"):
    ledger.issue_extra(db, warehouse_code=warehouse, item_sku=sku, qty=qty, ref_type="TEST", ref_no="drain")
    db.commit()


def test_reservation_that_crosses_the_rop_asks_for_a_low_stock_purchase_once(send, seeded_db, procurement, make_ticket):
    drain(seeded_db, 10)  # ONT tersedia 10 = ROP

    send("ticket.created", make_ticket("TKT-000001"))  # tersedia 9, di bawah ROP 10
    send("ticket.created", make_ticket("TKT-000002"))  # sudah di bawah ROP: tidak menyeberang lagi

    assert procurement.low_stock == [{"item_sku": "ONT-01", "warehouse_code": "WH-BDG", "qty": 11}]  # 2 x ROP - tersedia


def test_stock_well_above_the_rop_asks_for_nothing(send, seeded_db, procurement, make_ticket):
    send("ticket.created", make_ticket())
    assert procurement.low_stock == []


def test_extra_issue_that_crosses_the_rop_asks_for_a_low_stock_purchase(client, auth, create_request, seeded_db, procurement):
    no = create_request()
    client.post(
        f"/api/v1/stock-requests/{no}/issue",
        json={"lines": [{"item_sku": "ONT-01", "qty": 1}, {"item_sku": "CBL-FO", "qty": 50}]},
        headers=auth("WAREHOUSE_STAFF"),
    )
    drain(seeded_db, 8)  # ONT tersedia 19 -> 11
    assert procurement.low_stock == []

    response = client.post(
        f"/api/v1/stock-requests/{no}/issue-extra", json={"lines": [{"item_sku": "ONT-01", "qty": 2}]}, headers=auth("WAREHOUSE_STAFF")
    )

    assert response.status_code == 200, response.text
    # tersedia 11 -> 9 (di bawah ROP 10); jumlah = 2 x ROP - tersedia = 11
    assert procurement.low_stock == [{"item_sku": "ONT-01", "warehouse_code": "WH-BDG", "qty": 11}]


def test_pending_request_reserves_nothing_so_it_triggers_no_low_stock_request(send, seeded_db, procurement, make_ticket):
    drain(seeded_db, 20)
    send("ticket.created", make_ticket())
    assert procurement.low_stock == []
    assert len(procurement.requests) == 1
