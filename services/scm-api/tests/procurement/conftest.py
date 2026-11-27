"""Fixture Slice B: Finance palsu (`httpx.MockTransport`) serta port aset dan permintaan barang palsu."""
import json

import httpx
import pytest

from app.core.ports import override
from app.procurement import finance_client


class FakeFinance:
    """`mode`: `approve`, `reject`, `down`, `timeout`, `error`, atau `garbage`."""

    def __init__(self) -> None:
        self.mode = "approve"
        self.remaining = 215_000_000
        self.calls: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        if self.mode == "down":
            raise httpx.ConnectError("Finance mati", request=request)
        if self.mode == "timeout":
            raise httpx.ReadTimeout("Finance lambat", request=request)
        if self.mode == "error":
            return httpx.Response(500)
        if self.mode == "garbage":
            return httpx.Response(200, json={"approved": "yes"})
        body = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "cost_center_code": body["cost_center_code"],
                "requested": body["amount"],
                "remaining": self.remaining,
                "approved": self.mode == "approve",
            },
        )


class FakeAssets:
    def __init__(self) -> None:
        self.registered: list[dict] = []

    def register_units(self, db, *, item_sku, warehouse_code, qty, gr_no):
        self.registered.append({"item_sku": item_sku, "warehouse_code": warehouse_code, "qty": qty, "gr_no": gr_no})
        start = sum(entry["qty"] for entry in self.registered) - qty
        return [f"SN-ONT-2026-{900000 + start + index:06d}" for index in range(qty)]


class FakeStockRequests:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def reevaluate_pending(self, db, *, item_sku, warehouse_code):
        self.calls.append((item_sku, warehouse_code))
        return []


@pytest.fixture(autouse=True)
def finance(monkeypatch):
    fake = FakeFinance()
    monkeypatch.setattr(finance_client, "transport", httpx.MockTransport(fake.handler))
    return fake


@pytest.fixture
def assets():
    return FakeAssets()


@pytest.fixture
def stock_requests():
    return FakeStockRequests()


@pytest.fixture(autouse=True)
def fake_ports(assets, stock_requests):
    with override(assets=assets, stock_requests=stock_requests):
        yield


@pytest.fixture
def create_po(client, auth, seeded_db):
    """PO lewat API; `ONT-01` seharga Rp350.000, jadi qty menentukan jenjang persetujuan.

    PO yang lahir `DRAFT` (di atas Rp50 juta) dilengkapi tiga penawaran lalu diajukan.
    """

    def _create(qty=100, item_sku="ONT-01", creator="EMP-0021") -> str:
        response = client.post(
            "/api/v1/purchase-orders",
            json={"vendor_code": "VEN-0001", "item_sku": item_sku, "qty": qty},
            headers=auth("PROCUREMENT_STAFF", creator),
        )
        assert response.status_code == 201, response.text
        po_no = response.json()["po_no"]
        if response.json()["status"] == "DRAFT":
            headers = auth("PROCUREMENT_STAFF", creator)
            for vendor in ("VEN-0001", "VEN-0002", "VEN-0003"):
                quote = client.post(
                    f"/api/v1/purchase-orders/{po_no}/quotes",
                    json={"vendor_code": vendor, "unit_price": 350_000},
                    headers=headers,
                )
                assert quote.status_code == 201, quote.text
            submitted = client.post(f"/api/v1/purchase-orders/{po_no}/submit", headers=headers)
            assert submitted.status_code == 200, submitted.text
        return po_no

    return _create


@pytest.fixture
def decide(client, auth):
    def _decide(po_no, role, action="approve", sub=None):
        sub = sub or {"SCM_MANAGER": "EMP-0020", "FINANCE_MANAGER": "EMP-0030", "DIRECTOR": "EMP-0001"}[role]
        return client.post(f"/api/v1/purchase-orders/{po_no}/{action}", json={"comment": "ok"}, headers=auth(role, sub))

    return _decide
