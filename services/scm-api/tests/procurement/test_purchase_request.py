import pytest

from shared.auth import decode_access_token

from app.core.jobs import run_job_once
from app.core.ports import Shortage
from app.procurement.models import PurchaseOrder, PurchaseRequest
from app.procurement.purchase_requests import ProcurementService


def _request(db, stock_request_no="SR-2026-000001"):
    pr_no = ProcurementService().request_purchase(
        db, stock_request_no=stock_request_no, warehouse_code="WH-BDG",
        shortages=[Shortage("ONT-01", 3), Shortage("CBL-FO", 100)], correlation_id="TKT-000001",
    )
    db.commit()
    return pr_no


def _status(db, pr_no):
    db.expire_all()
    return db.query(PurchaseRequest).filter_by(pr_no=pr_no).one().status


def test_request_purchase_creates_one_pr_per_stock_request(seeded_db, finance):
    first = _request(seeded_db)
    assert _request(seeded_db) == first
    row = seeded_db.query(PurchaseRequest).one()
    assert row.estimated_total == 3 * 350_000 + 100 * 4_000
    assert len(row.lines) == 2
    assert row.status == "PENDING_BUDGET"
    assert finance.calls == []  # transaksi stok tidak menunggu Finance


@pytest.mark.parametrize("mode,expected", [("approve", "BUDGET_OK"), ("reject", "BUDGET_REJECTED")])
def test_budget_job_applies_finance_answer(seeded_db, session_factory, finance, mode, expected):
    pr_no = _request(seeded_db)
    finance.mode = mode
    run_job_once("procurement.check_budgets", session_factory)
    assert _status(seeded_db, pr_no) == expected


@pytest.mark.parametrize("mode", ["down", "timeout", "error", "garbage"])
def test_unreachable_finance_holds_the_pr_until_it_recovers(seeded_db, session_factory, finance, mode):
    pr_no = _request(seeded_db)
    finance.mode = mode
    run_job_once("procurement.check_budgets", session_factory)
    assert _status(seeded_db, pr_no) == "PENDING_BUDGET"

    finance.mode = "approve"
    run_job_once("procurement.check_budgets", session_factory)
    assert _status(seeded_db, pr_no) == "BUDGET_OK"


def test_finance_call_carries_service_token_and_correlation_id(seeded_db, session_factory, finance):
    _request(seeded_db)
    run_job_once("procurement.check_budgets", session_factory)
    call = finance.calls[0]
    assert call.url.path == "/api/v1/budgets/check"
    assert call.headers["X-Correlation-Id"] == "TKT-000001"
    claims = decode_access_token(call.headers["Authorization"].split(" ", 1)[1])
    assert claims["scopes"] == ["budgets:check"]


def test_huge_po_never_passes_while_finance_is_down(client, auth, seeded_db, finance):
    finance.mode = "down"
    response = client.post(
        "/api/v1/purchase-orders",
        json={"vendor_code": "VEN-0001", "item_sku": "ONT-01", "qty": 100_000},  # Rp35 miliar
        headers=auth("PROCUREMENT_STAFF"),
    )
    assert response.status_code == 503
    assert seeded_db.query(PurchaseOrder).count() == 0


def test_low_stock_request_is_idempotent_per_sku_and_warehouse(seeded_db):
    service = ProcurementService()
    kwargs = {"item_sku": "CBL-FO", "warehouse_code": "WH-BDG", "qty": 500, "correlation_id": "TKT-000001"}
    first = service.request_low_stock_purchase(seeded_db, **kwargs)
    second = service.request_low_stock_purchase(seeded_db, **kwargs)
    seeded_db.commit()
    assert first == second
    assert seeded_db.query(PurchaseRequest).filter_by(source="LOW_STOCK").count() == 1


def test_list_and_detail(client, auth, seeded_db):
    pr_no = _request(seeded_db)
    listed = client.get("/api/v1/purchase-requests?status=PENDING_BUDGET", headers=auth("DIRECTOR"))
    assert [row["purchase_request_no"] for row in listed.json()] == [pr_no]
    detail = client.get(f"/api/v1/purchase-requests/{pr_no}", headers=auth("WAREHOUSE_STAFF"))
    assert len(detail.json()["lines"]) == 2
    assert client.get("/api/v1/purchase-requests/PR-2026-9999", headers=auth("DIRECTOR")).status_code == 404
    assert client.get("/api/v1/purchase-requests", headers=auth("FINANCE_MANAGER")).status_code == 403
