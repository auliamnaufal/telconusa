"""SCM-D-03: ketersediaan stok indikatif untuk CRM dan saldo per gudang.

Seed (app/core/seed.py): ONT-01 ROP 10 per gudang; WH-BKS 40 fisik (1 rusak), WH-BDG 20, WH-SBY 15.
SIM-01 ROP 200, hanya ada di WH-BKS (2500).
"""
from pathlib import Path

import jsonschema
import pytest
import yaml

from shared.service_auth import service_headers

from app.core.models import InventoryBalance

CONTRACT = Path(__file__).resolve().parents[4] / "contracts" / "openapi" / "scm.yaml"


@pytest.fixture(scope="module")
def stock_schema():
    spec = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    return spec["paths"]["/api/v1/stock/{sku}"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]


@pytest.fixture
def crm():
    return service_headers("crm", ["stock:read"])


def _balance(db, warehouse: str, sku: str) -> InventoryBalance:
    return db.query(InventoryBalance).filter_by(warehouse_code=warehouse, item_sku=sku).one()


# ---------------------------------------------------------------------------- GET /stock/{sku}


def test_all_warehouses_by_default_matches_contract(client, seeded_db, crm, stock_schema):
    response = client.get("/api/v1/stock/ONT-01", headers=crm)
    assert response.status_code == 200, response.text
    body = response.json()
    jsonschema.validate(body, stock_schema)
    # 39 baik di WH-BKS (1 rusak) + 20 + 15; ROP 10 x 3 gudang.
    assert body == {
        "sku": "ONT-01", "name": "Perangkat ONT Dual-Band GPON", "unit": "UNIT",
        "qty_available": 74, "reorder_point": 30, "below_rop": False,
    }


def test_city_code_counts_only_that_city(client, seeded_db, crm):
    body = client.get("/api/v1/stock/ONT-01?city_code=BDG", headers=crm).json()
    assert (body["qty_available"], body["reorder_point"]) == (20, 10)


def test_warehouse_code_limits_scope(client, seeded_db, crm):
    body = client.get("/api/v1/stock/ONT-01?warehouse_code=WH-SBY", headers=crm).json()
    assert (body["qty_available"], body["reorder_point"]) == (15, 10)


def test_damaged_and_reserved_are_not_available(client, seeded_db, crm):
    balance = _balance(seeded_db, "WH-BDG", "ONT-01")
    balance.qty_reserved, balance.qty_damaged = 4, 3
    seeded_db.commit()
    body = client.get("/api/v1/stock/ONT-01?city_code=BDG", headers=crm).json()
    assert body["qty_available"] == 13
    # WH-BKS punya 1 unit rusak dari seed.
    assert client.get("/api/v1/stock/ONT-01?warehouse_code=WH-BKS", headers=crm).json()["qty_available"] == 39


def test_below_rop_follows_requested_scope(client, seeded_db, crm):
    # SIM-01 hanya di WH-BKS: cukup secara total, kosong di Surabaya.
    assert client.get("/api/v1/stock/SIM-01", headers=crm).json()["below_rop"] is False
    sby = client.get("/api/v1/stock/SIM-01?city_code=SBY", headers=crm).json()
    assert (sby["qty_available"], sby["reorder_point"], sby["below_rop"]) == (0, 200, True)

    balance = _balance(seeded_db, "WH-BDG", "ONT-01")
    balance.qty_reserved = 11  # tersisa 9 < ROP 10
    seeded_db.commit()
    assert client.get("/api/v1/stock/ONT-01?city_code=BDG", headers=crm).json()["below_rop"] is True
    assert client.get("/api/v1/stock/ONT-01", headers=crm).json()["below_rop"] is False


def test_exactly_at_rop_is_not_below(client, seeded_db, crm):
    balance = _balance(seeded_db, "WH-SBY", "ONT-01")
    balance.qty_physical = 10
    seeded_db.commit()
    body = client.get("/api/v1/stock/ONT-01?city_code=SBY", headers=crm).json()
    assert (body["qty_available"], body["below_rop"]) == (10, False)


def test_without_token_is_401(client, seeded_db):
    assert client.get("/api/v1/stock/ONT-01").status_code == 401


@pytest.mark.parametrize(
    "headers_factory",
    [lambda auth: service_headers("crm", ["packagekits:read"]), lambda auth: auth("SCM_MANAGER")],
    ids=["wrong-scope", "user-token"],
)
def test_wrong_scope_is_403(client, seeded_db, auth, headers_factory):
    response = client.get("/api/v1/stock/ONT-01", headers=headers_factory(auth))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_unknown_sku_is_404(client, seeded_db, crm):
    response = client.get("/api/v1/stock/XXX-99", headers=crm)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ITEM_NOT_FOUND"


def test_unknown_city_or_warehouse_is_404(client, seeded_db, crm):
    for query in ("city_code=MDN", "warehouse_code=WH-XXX", "warehouse_code=WH-BDG&city_code=SBY"):
        response = client.get(f"/api/v1/stock/ONT-01?{query}", headers=crm)
        assert response.status_code == 404, query
        assert response.json()["error"]["code"] == "WAREHOUSE_NOT_FOUND"


# ---------------------------------------------------------------------------- GET /stock/balances


@pytest.mark.parametrize("role", ["DIRECTOR", "SCM_MANAGER", "WAREHOUSE_STAFF", "PROCUREMENT_STAFF"])
def test_balances_for_scm_roles_and_director(client, seeded_db, auth, role):
    response = client.get("/api/v1/stock/balances", headers=auth(role))
    assert response.status_code == 200, response.text
    assert response.headers["X-Total-Count"] == "8"


def test_balances_rejects_other_roles_and_service_tokens(client, seeded_db, auth):
    assert client.get("/api/v1/stock/balances", headers=auth("CS_AGENT")).status_code == 403
    assert client.get("/api/v1/stock/balances", headers=service_headers("crm", ["stock:read"])).status_code == 403
    assert client.get("/api/v1/stock/balances").status_code == 401


def test_balance_row_shape_and_damaged_excluded(client, seeded_db, auth):
    rows = client.get("/api/v1/stock/balances?warehouse_code=WH-BKS&item_sku=ONT-01", headers=auth("DIRECTOR")).json()
    assert rows == [{
        "warehouse_code": "WH-BKS", "item_sku": "ONT-01", "name": "Perangkat ONT Dual-Band GPON", "unit": "UNIT",
        "qty_physical": 40, "qty_reserved": 0, "qty_damaged": 1, "qty_available": 39,
        "reorder_point": 10, "below_rop": False, "overstock": True,
    }]


def test_balances_flag_below_rop_per_warehouse(client, seeded_db, auth):
    balance = _balance(seeded_db, "WH-SBY", "ONT-01")
    balance.qty_damaged = 6  # 9 tersedia < ROP 10
    seeded_db.commit()
    rows = client.get("/api/v1/stock/balances?item_sku=ONT-01", headers=auth("SCM_MANAGER")).json()
    assert {row["warehouse_code"]: row["below_rop"] for row in rows} == {"WH-BDG": False, "WH-BKS": False, "WH-SBY": True}


def test_balances_paginate(client, seeded_db, auth):
    response = client.get("/api/v1/stock/balances?page=2&limit=5", headers=auth("SCM_MANAGER"))
    assert response.headers["X-Total-Count"] == "8"
    assert len(response.json()) == 3
