"""SCM-D-06: API audit log.

Persetujuan PO (SCM-B-03) dan pemeriksaan unit (SCM-C-03) belum dibuat; tes untuk keduanya ditambahkan
setelah issue tersebut selesai.
"""
from datetime import datetime

import pytest

from app.core.models import AuditLog
from app.stock.models import StockRequest


def _ticket(ticket_code: str) -> dict:
    # Hanya barang non-serial agar alur tidak memerlukan AssetPort (Slice C).
    return {
        "ticket_code": ticket_code,
        "type": "INSTALLATION",
        "order_no": "ORD-2026-000125",
        "subscription_code": "SUB-000012",
        "customer_code": "CUS-000456",
        "install_address": {"address_code": "ADR-000010", "address": "Jl. Dago No. 12", "city_code": "BDG", "postal_code": "40135"},
        "recipient": {"name": "Andi", "whatsapp": "6281234567890", "email": "andi@gmail.com"},
        "required_items": [{"item_sku": "CBL-FO", "qty": 50, "unit": "METER"}],
    }


@pytest.fixture
def ready_request(client, signed_event, seeded_db):
    raw, headers, _ = signed_event("ticket.created", _ticket("TKT-000321"), "TKT-000321")
    assert client.post("/internal/events", content=raw, headers=headers).status_code == 200
    seeded_db.expire_all()
    request = seeded_db.query(StockRequest).filter_by(ticket_code="TKT-000321").one()
    assert request.status == "READY_TO_ISSUE"
    return request.stock_request_no


def _logs(client, auth, query: str = "", role: str = "SCM_MANAGER"):
    response = client.get(f"/api/v1/audit-logs{query}", headers=auth(role))
    assert response.status_code == 200, response.text
    return response


def test_cancel_appears_with_actor_and_correlation_id(client, auth, ready_request):
    headers = {**auth("WAREHOUSE_STAFF", sub="EMP-0077"), "X-Correlation-Id": "TKT-000321"}
    response = client.post(f"/api/v1/stock-requests/{ready_request}/cancel", json={"reason": "Pelanggan batal"}, headers=headers)
    assert response.status_code == 200, response.text

    rows = _logs(client, auth, f"?entity=StockRequest&entity_id={ready_request}").json()
    cancel = [row for row in rows if row["action"] == "stock_request.cancel"]
    assert len(cancel) == 1
    assert cancel[0]["actor"] == "EMP-0077"
    assert cancel[0]["role"] == "WAREHOUSE_STAFF"
    assert cancel[0]["correlation_id"] == "TKT-000321"
    assert cancel[0]["detail"] == {"reason": "Pelanggan batal"}
    assert cancel[0]["at"].endswith("+07:00")


def test_catalog_writes_carry_request_correlation_id(client, auth, seeded_db):
    headers = {**auth("SCM_MANAGER", sub="EMP-0005"), "X-Correlation-Id": "UI-ABC123"}
    body = {"sku": "SPL-14", "name": "Splitter 1:4", "unit": "PCS", "unit_cost": 25000}
    assert client.post("/api/v1/items", json=body, headers=headers).status_code == 201
    assert client.patch("/api/v1/vendors/VEN-0001", json={"rating_score": "4.90"}, headers=headers).status_code == 200
    put = {"lines": [{"item_sku": "SPL-14", "qty": 1}]}
    assert client.put("/api/v1/package-kits/B2B-10", json=put, headers=headers).status_code == 200

    rows = _logs(client, auth, "?actor=EMP-0005").json()
    assert {(row["action"], row["entity"], row["entity_id"]) for row in rows} == {
        ("item.create", "Item", "SPL-14"),
        ("vendor.update", "Vendor", "VEN-0001"),
        ("package_kit.replace", "PackageKit", "B2B-10"),
    }
    assert {row["correlation_id"] for row in rows} == {"UI-ABC123"}


def test_filters_and_pagination(client, auth, seeded_db):
    for n in range(5):
        seeded_db.add(
            AuditLog(actor="EMP-0001" if n % 2 else "system", role="SCM_MANAGER", action="item.update", entity="Item",
                     entity_id="ONT-01" if n < 3 else "CBL-FO", at=datetime(2026, 11, 20, 1, n))
        )
    seeded_db.commit()

    response = _logs(client, auth, "?entity=Item&entity_id=ONT-01&limit=2", role="DIRECTOR")
    assert response.headers["X-Total-Count"] == "3"
    rows = response.json()
    assert [row["at"] for row in rows] == ["2026-11-20T08:02:00+07:00", "2026-11-20T08:01:00+07:00"]
    assert _logs(client, auth, "?entity=Item&entity_id=ONT-01&limit=2&page=2").json()[0]["at"] == "2026-11-20T08:00:00+07:00"
    assert _logs(client, auth, "?actor=system").headers["X-Total-Count"] == "3"


@pytest.mark.parametrize("role", ["WAREHOUSE_STAFF", "PROCUREMENT_STAFF", "FINANCE_MANAGER", "CS_AGENT"])
def test_other_roles_are_forbidden(client, auth, seeded_db, role):
    response = client.get("/api/v1/audit-logs", headers=auth(role))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_anonymous_is_401(client, seeded_db):
    assert client.get("/api/v1/audit-logs").status_code == 401
