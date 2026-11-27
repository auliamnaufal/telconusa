import pytest

from app.core.ports import Shortage
from app.procurement.models import PurchaseOrder, PurchaseRequest
from app.procurement.purchase_requests import ProcurementService, check_pending_budgets

URL = "/api/v1/purchase-orders"
BODY = {"vendor_code": "VEN-0001", "item_sku": "ONT-01", "qty": 100}


def _counts(db):
    db.expire_all()
    return db.query(PurchaseRequest).count(), db.query(PurchaseOrder).count()


def test_create_po_returns_contract_response(client, auth, seeded_db):
    response = client.post(URL, json=BODY, headers=auth("PROCUREMENT_STAFF"))
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["po_no"].startswith("PO-")
    assert body["total_amount"] == 35_000_000
    assert body["status"] == "PENDING_APPROVAL"
    assert body["budget_remaining_after_check"] == 215_000_000
    assert seeded_db.query(PurchaseRequest).one().status == "PO_CREATED"


@pytest.mark.parametrize(
    "price,roles",
    [
        (5_000_000, ["SCM_MANAGER"]),
        (10_000_000, ["SCM_MANAGER"]),
        (35_000_000, ["SCM_MANAGER", "FINANCE_MANAGER"]),
        (100_000_000, ["SCM_MANAGER", "FINANCE_MANAGER"]),
        (150_000_000, ["SCM_MANAGER", "FINANCE_MANAGER", "DIRECTOR"]),
    ],
)
def test_required_roles_follow_total(price, roles):
    from app.procurement.purchase_orders import required_roles_for

    assert required_roles_for(price) == roles


@pytest.mark.parametrize("mode,status,code", [("down", 503, "BUDGET_CHECK_UNAVAILABLE"), ("reject", 409, "BUDGET_INSUFFICIENT")])
def test_budget_failure_creates_nothing(client, auth, seeded_db, finance, mode, status, code):
    finance.mode = mode
    response = client.post(URL, json=BODY, headers=auth("SCM_MANAGER"))
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert _counts(seeded_db) == (0, 0)


@pytest.mark.parametrize("patch,status", [({"vendor_code": "VEN-9999"}, 404), ({"item_sku": "XXX"}, 404), ({"qty": 0}, 422)])
def test_invalid_input(client, auth, seeded_db, patch, status):
    response = client.post(URL, json={**BODY, **patch}, headers=auth("PROCUREMENT_STAFF"))
    assert response.status_code == status
    assert "code" in response.json()["error"]


def test_other_roles_are_forbidden(client, auth, seeded_db):
    assert client.post(URL, json=BODY, headers=auth("WAREHOUSE_STAFF")).status_code == 403


def test_idempotency_key_creates_one_po(client, auth, seeded_db):
    headers = {**auth("PROCUREMENT_STAFF"), "Idempotency-Key": "po-1"}
    first = client.post(URL, json=BODY, headers=headers)
    second = client.post(URL, json=BODY, headers=headers)
    assert first.json() == second.json()
    assert _counts(seeded_db) == (1, 1)


def _approved_pr(db):
    pr_no = ProcurementService().request_purchase(
        db, stock_request_no="SR-2026-000001", warehouse_code="WH-BDG",
        shortages=[Shortage("CBL-FO", 100)], correlation_id="TKT-000001",
    )
    db.commit()
    check_pending_budgets(db)
    return pr_no


def test_create_po_from_budgeted_request(client, auth, seeded_db, finance):
    pr_no = _approved_pr(seeded_db)
    url = f"/api/v1/purchase-requests/{pr_no}/create-po"
    body = {"vendor_code": "VEN-0002", "unit_prices": [{"item_sku": "CBL-FO", "unit_price": 3_900}]}
    response = client.post(url, json=body, headers=auth("PROCUREMENT_STAFF"))
    assert response.status_code == 201, response.text
    assert response.json()["total_amount"] == 390_000
    assert len(finance.calls) == 1
    again = client.post(url, json=body, headers=auth("PROCUREMENT_STAFF"))
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "INVALID_TRANSITION"


def test_price_above_estimate_is_checked_again(client, auth, seeded_db, finance):
    pr_no = _approved_pr(seeded_db)
    finance.mode = "down"
    response = client.post(
        f"/api/v1/purchase-requests/{pr_no}/create-po",
        json={"vendor_code": "VEN-0002", "unit_prices": [{"item_sku": "CBL-FO", "unit_price": 350_000_000}]},
        headers=auth("PROCUREMENT_STAFF"),
    )
    assert response.status_code == 503
    assert seeded_db.query(PurchaseOrder).count() == 0


def test_price_lines_must_match_request(client, auth, seeded_db):
    pr_no = _approved_pr(seeded_db)
    response = client.post(
        f"/api/v1/purchase-requests/{pr_no}/create-po",
        json={"vendor_code": "VEN-0002", "unit_prices": [{"item_sku": "ONT-01", "unit_price": 1}]},
        headers=auth("PROCUREMENT_STAFF"),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PRICE_LINES_MISMATCH"
