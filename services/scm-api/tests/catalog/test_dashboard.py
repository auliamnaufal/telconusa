"""SCM-D-04: ringkasan dashboard SCM."""
from datetime import datetime, timedelta
from pathlib import Path

import jsonschema
import pytest
import yaml

from app.assets.models import SerializedUnit
from app.core.models import InventoryBalance
from app.procurement.models import PurchaseOrder
from app.stock.models import StockRequest

CONTRACT = Path(__file__).resolve().parents[4] / "contracts" / "openapi" / "scm.yaml"

# Seed: (fisik - rusak) x harga satuan.
# ONT-01 (39 + 20 + 15) x 350.000 + SIM-01 2.500 x 5.000 + RTR-AX 110 x 500.000 + CBL-FO 45.500 x 4.000
SEED_VALUATION = 74 * 350_000 + 2_500 * 5_000 + 110 * 500_000 + 45_500 * 4_000


@pytest.fixture(scope="module")
def dashboard_contract():
    spec = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    content = spec["paths"]["/api/v1/dashboard/summary"]["get"]["responses"]["200"]["content"]["application/json"]
    return content["schema"], content["example"]


def _add_requests(db, statuses: list[str]) -> None:
    start = datetime(2026, 11, 20, 8, 0, 0)
    for n, status in enumerate(statuses, start=1):
        db.add(
            StockRequest(
                stock_request_no=f"SR-2026-{n:06d}", ticket_code=f"TKT-{n:06d}", city_code="BDG",
                warehouse_code="WH-BDG", status=status, created_at=start + timedelta(hours=n),
            )
        )
    db.commit()


def _summary(client, auth, role="SCM_MANAGER") -> dict:
    response = client.get("/api/v1/dashboard/summary", headers=auth(role))
    assert response.status_code == 200, response.text
    return response.json()


def test_seed_valuation_and_shape_match_contract(client, auth, seeded_db, dashboard_contract):
    schema, example = dashboard_contract
    body = _summary(client, auth)
    jsonschema.validate(body, schema)
    jsonschema.validate(example, schema)
    assert set(example["kpis"]) <= set(body["kpis"])
    assert body["kpis"]["total_skus"] == 4
    assert body["kpis"]["inventory_valuation_idr"] == SEED_VALUATION == 275_400_000
    assert body["stock_requests"] == []


def test_valuation_excludes_damaged_but_counts_reserved(client, auth, seeded_db):
    balance = seeded_db.query(InventoryBalance).filter_by(warehouse_code="WH-BDG", item_sku="ONT-01").one()
    balance.qty_reserved, balance.qty_damaged = 5, 2
    seeded_db.commit()
    assert _summary(client, auth)["kpis"]["inventory_valuation_idr"] == SEED_VALUATION - 2 * 350_000


def test_open_and_return_pending_counts(client, auth, seeded_db):
    _add_requests(
        seeded_db,
        ["REQUESTED", "PENDING_STOCK", "READY_TO_ISSUE", "READY_TO_ISSUE", "ISSUED", "ISSUED", "ISSUED", "RETURNED", "CANCELLED"],
    )
    kpis = _summary(client, auth)["kpis"]
    assert kpis["open_stock_requests"] == 7
    assert kpis["return_pending"] == 3
    assert kpis["active_reservations"] == 2


def test_recent_stock_requests_newest_first_and_limited(client, auth, seeded_db):
    _add_requests(seeded_db, ["REQUESTED"] * 11 + ["ISSUED"])
    rows = _summary(client, auth)["stock_requests"]
    assert len(rows) == 10
    assert rows[0] == {"stock_request_no": "SR-2026-000012", "ticket_code": "TKT-000012", "status": "ISSUED"}
    assert rows[-1]["stock_request_no"] == "SR-2026-000003"


def test_open_purchase_orders_and_installed_onts(client, auth, seeded_db):
    statuses = ["DRAFT", "PENDING_APPROVAL", "APPROVED", "PARTIALLY_RECEIVED", "RECEIVED", "CLOSED", "REJECTED", "CANCELLED"]
    for n, status in enumerate(statuses, start=1):
        seeded_db.add(
            PurchaseOrder(po_no=f"PO-2026-{n:04d}", vendor_code="VEN-0001", total_amount=1_000_000, status=status, created_by="EMP-0001")
        )
    baseline = _summary(client, auth)["kpis"]["ont_installed"]
    for n, status in enumerate(["INSTALLED", "INSTALLED", "WITH_TECHNICIAN"], start=1):
        seeded_db.add(SerializedUnit(serial_number=f"SN-DASH-{n:04d}", item_sku="ONT-01", warehouse_code="WH-BDG", status=status))
    seeded_db.commit()

    kpis = _summary(client, auth)["kpis"]
    assert kpis["open_purchase_orders"] == 4
    assert kpis["ont_installed"] == baseline + 2


@pytest.mark.parametrize("role", ["DIRECTOR", "WAREHOUSE_STAFF", "PROCUREMENT_STAFF"])
def test_scm_roles_and_director_can_read(client, auth, seeded_db, role):
    assert client.get("/api/v1/dashboard/summary", headers=auth(role)).status_code == 200


def test_other_roles_and_anonymous_are_rejected(client, auth, seeded_db):
    assert client.get("/api/v1/dashboard/summary", headers=auth("CS_AGENT")).status_code == 403
    assert client.get("/api/v1/dashboard/summary").status_code == 401
