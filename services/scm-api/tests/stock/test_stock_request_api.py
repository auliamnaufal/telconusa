import pytest


def test_list_filters_by_status_city_and_ticket_and_paginates(client, auth, create_request, seeded_db):
    first = create_request("TKT-000001", "BDG")
    second = create_request("TKT-000002", "SBY")
    headers = auth("WAREHOUSE_STAFF")

    everything = client.get("/api/v1/stock-requests", headers=headers)
    assert everything.status_code == 200
    assert {r["stock_request_no"] for r in everything.json()} == {first, second}
    assert everything.headers["X-Total-Count"] == "2"

    assert [r["stock_request_no"] for r in client.get("/api/v1/stock-requests?city_code=SBY", headers=headers).json()] == [second]
    assert [r["ticket_code"] for r in client.get("/api/v1/stock-requests?ticket_code=TKT-000001", headers=headers).json()] == ["TKT-000001"]
    assert len(client.get("/api/v1/stock-requests?status=READY_TO_ISSUE", headers=headers).json()) == 2
    assert client.get("/api/v1/stock-requests?status=ISSUED", headers=headers).json() == []

    page = client.get("/api/v1/stock-requests?limit=1&page=2", headers=headers)
    assert len(page.json()) == 1 and page.headers["X-Total-Count"] == "2"


def test_list_item_has_the_contract_fields(client, auth, create_request):
    no = create_request("TKT-000001", "BDG")
    (row,) = client.get("/api/v1/stock-requests", headers=auth("SCM_MANAGER")).json()
    assert row == {
        "stock_request_no": no, "ticket_code": "TKT-000001", "status": "READY_TO_ISSUE",
        "technician_employee_id": "EMP-0042", "city_code": "BDG", "return_pending": False,
    }


def test_detail_has_lines_and_return_pending_after_issue(client, auth, create_request):
    no = create_request()
    detail = client.get(f"/api/v1/stock-requests/{no}", headers=auth("DIRECTOR")).json()
    assert detail["status"] == "READY_TO_ISSUE" and detail["return_pending"] is False
    assert detail["lines"][0] == {
        "item_sku": "ONT-01", "qty_required": 1, "qty_issued": 0, "qty_used": 0,
        "qty_returned": 0, "qty_damaged": 0, "unit": "UNIT", "is_extra": False,
    }

    issued = client.post(
        f"/api/v1/stock-requests/{no}/issue",
        json={"lines": [{"item_sku": "ONT-01", "qty": 1}, {"item_sku": "CBL-FO", "qty": 50}]},
        headers=auth("WAREHOUSE_STAFF"),
    )
    assert issued.status_code == 200
    detail = client.get(f"/api/v1/stock-requests/{no}", headers=auth("DIRECTOR")).json()
    assert detail["status"] == "ISSUED" and detail["return_pending"] is True
    assert detail["lines"][0]["qty_issued"] == 1


def test_unknown_number_is_a_standard_404(client, auth, seeded_db):
    response = client.get("/api/v1/stock-requests/SR-2026-999999", headers=auth("SCM_MANAGER"))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "STOCK_REQUEST_NOT_FOUND"


@pytest.mark.parametrize("path", ["/api/v1/stock-requests", "/api/v1/stock-requests/SR-2026-000001"])
def test_reads_need_an_scm_role(client, auth, seeded_db, path):
    assert client.get(path).status_code == 401
    assert client.get(path, headers=auth("TECHNICIAN")).status_code == 403
    assert client.get(path, headers=auth("CS_AGENT")).status_code == 403
