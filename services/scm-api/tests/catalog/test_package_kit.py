"""SCM-D-02: daftar barang paket untuk CRM dan pengelolaannya."""
from pathlib import Path

import jsonschema
import pytest
import yaml

from shared.service_auth import service_headers

from app.catalog.models import PackageKitLine
from app.core.models import AuditLog

CONTRACT = Path(__file__).resolve().parents[4] / "contracts" / "openapi" / "scm.yaml"


@pytest.fixture(scope="module")
def kit_contract():
    spec = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    content = spec["paths"]["/api/v1/package-kits/{sku}"]["get"]["responses"]["200"]["content"]["application/json"]
    return content["schema"], content["example"]


@pytest.fixture
def crm():
    return service_headers("crm", ["packagekits:read"])


def _comparable(body: dict) -> tuple[str, list[tuple]]:
    """Paket tanpa nama barang dan tanpa urutan baris."""
    return body["service_sku"], sorted((i["item_sku"], i["qty"], i["unit"]) for i in body["items"])


# ---------------------------------------------------------------------------- GET untuk CRM


def test_home_50_matches_contract_example(client, seeded_db, crm, kit_contract):
    schema, example = kit_contract
    response = client.get("/api/v1/package-kits/HOME-50", headers=crm)
    assert response.status_code == 200, response.text
    body = response.json()

    jsonschema.validate(body, schema)
    # Nama barang diambil dari master SCM, bukan teks contoh kontrak.
    assert _comparable(body) == _comparable(example) == ("HOME-50", [("CBL-FO", 50, "METER"), ("ONT-01", 1, "UNIT")])
    assert {i["item_sku"]: i["name"] for i in body["items"]} == {
        "ONT-01": "Perangkat ONT Dual-Band GPON",
        "CBL-FO": "Kabel Fiber Optik Dropcore 1C",
    }


def test_without_token_is_401(client, seeded_db):
    response = client.get("/api/v1/package-kits/HOME-50")
    assert response.status_code == 401
    assert "error" in response.json()


@pytest.mark.parametrize(
    "headers_factory",
    [
        lambda auth: service_headers("crm", ["stock:read"]),
        lambda auth: auth("SCM_MANAGER"),
    ],
    ids=["wrong-scope", "user-token"],
)
def test_wrong_scope_is_403(client, seeded_db, auth, headers_factory):
    response = client.get("/api/v1/package-kits/HOME-50", headers=headers_factory(auth))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_package_without_kit_is_404(client, seeded_db, crm):
    response = client.get("/api/v1/package-kits/MOB-PRE-50", headers={**crm, "X-Correlation-Id": "TKT-000777"})
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "PACKAGE_KIT_NOT_FOUND"
    assert error["details"] == {"service_sku": "MOB-PRE-50"}
    assert error["correlation_id"] == "TKT-000777"


# ---------------------------------------------------------------------------- pengelolaan


def test_list_kits_for_scm_roles(client, seeded_db, auth):
    response = client.get("/api/v1/package-kits", headers=auth("WAREHOUSE_STAFF"))
    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "3"
    assert [kit["service_sku"] for kit in response.json()] == ["HOME-100", "HOME-20", "HOME-50"]
    assert client.get("/api/v1/package-kits", headers=auth("CS_AGENT")).status_code == 403


def test_put_replaces_all_lines(client, seeded_db, auth, crm):
    body = {"lines": [{"item_sku": "ONT-01", "qty": 1}, {"item_sku": "CBL-FO", "qty": 80}, {"item_sku": "RTR-AX", "qty": 1}]}
    response = client.put("/api/v1/package-kits/HOME-100", json=body, headers=auth("SCM_MANAGER"))
    assert response.status_code == 200, response.text

    fetched = client.get("/api/v1/package-kits/HOME-100", headers=crm).json()
    assert {(i["item_sku"], i["qty"], i["unit"]) for i in fetched["items"]} == {
        ("ONT-01", 1, "UNIT"), ("CBL-FO", 80, "METER"), ("RTR-AX", 1, "UNIT"),
    }
    seeded_db.expire_all()
    assert seeded_db.query(PackageKitLine).filter_by(service_sku="HOME-100").count() == 3
    assert seeded_db.query(AuditLog).filter_by(action="package_kit.replace", entity_id="HOME-100").count() == 1


def test_put_creates_new_kit(client, seeded_db, auth, crm):
    body = {"lines": [{"item_sku": "SIM-01", "qty": 1}]}
    assert client.put("/api/v1/package-kits/MOB-PRE-50", json=body, headers=auth("SCM_MANAGER")).status_code == 200
    fetched = client.get("/api/v1/package-kits/MOB-PRE-50", headers=crm).json()
    assert fetched == {"service_sku": "MOB-PRE-50", "items": [{"item_sku": "SIM-01", "name": "Kartu SIM 5G", "qty": 1, "unit": "PCS"}]}


def test_put_with_unknown_item_is_422_and_keeps_kit(client, seeded_db, auth, crm):
    body = {"lines": [{"item_sku": "ONT-01", "qty": 1}, {"item_sku": "XXX-99", "qty": 2}]}
    response = client.put("/api/v1/package-kits/HOME-50", json=body, headers=auth("SCM_MANAGER"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ITEM_NOT_FOUND"
    assert response.json()["error"]["details"] == {"item_skus": ["XXX-99"]}
    assert len(client.get("/api/v1/package-kits/HOME-50", headers=crm).json()["items"]) == 2


def test_put_rejects_duplicate_and_invalid_lines(client, seeded_db, auth):
    headers = auth("SCM_MANAGER")
    duplicate = {"lines": [{"item_sku": "ONT-01", "qty": 1}, {"item_sku": "ONT-01", "qty": 1}]}
    assert client.put("/api/v1/package-kits/HOME-50", json=duplicate, headers=headers).status_code == 422
    assert client.put("/api/v1/package-kits/HOME-50", json={"lines": []}, headers=headers).status_code == 422
    zero = {"lines": [{"item_sku": "ONT-01", "qty": 0}]}
    assert client.put("/api/v1/package-kits/HOME-50", json=zero, headers=headers).status_code == 422


@pytest.mark.parametrize("role", ["DIRECTOR", "WAREHOUSE_STAFF", "PROCUREMENT_STAFF"])
def test_only_scm_manager_can_put(client, seeded_db, auth, role):
    body = {"lines": [{"item_sku": "ONT-01", "qty": 2}]}
    assert client.put("/api/v1/package-kits/HOME-50", json=body, headers=auth(role)).status_code == 403
