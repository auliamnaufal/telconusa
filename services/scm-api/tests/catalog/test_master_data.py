"""SCM-D-01: API data master barang, gudang, vendor."""
import pytest

from app.assets.models import SerializedUnit
from app.core.models import AuditLog, InventoryBalance, Item

NEW_ITEM = {"sku": "SPL-14", "name": "Splitter 1:4", "unit": "PCS", "unit_cost": 25000, "reorder_point": 30, "safety_stock": 10}


@pytest.fixture
def seeded(seeded_db):
    return seeded_db


# ---------------------------------------------------------------------------- baca


@pytest.mark.parametrize("role", ["DIRECTOR", "SCM_MANAGER", "WAREHOUSE_STAFF", "PROCUREMENT_STAFF"])
def test_scm_roles_and_director_can_read_master_lists(client, auth, seeded, role):
    for path, key, expected in [
        ("/api/v1/items", "sku", "ONT-01"),
        ("/api/v1/warehouses", "code", "WH-BDG"),
        ("/api/v1/vendors", "code", "VEN-0001"),
    ]:
        response = client.get(path, headers=auth(role))
        assert response.status_code == 200, response.text
        assert expected in [row[key] for row in response.json()]


def test_other_roles_cannot_read(client, auth, seeded):
    assert client.get("/api/v1/items", headers=auth("CS_AGENT")).status_code == 403
    assert client.get("/api/v1/items").status_code == 401


def test_list_paginates_with_total_header(client, auth, seeded):
    response = client.get("/api/v1/items?page=2&limit=3", headers=auth("SCM_MANAGER"))
    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "4"
    assert [row["sku"] for row in response.json()] == ["SIM-01"]


def test_warehouse_list_shape(client, auth, seeded):
    rows = client.get("/api/v1/warehouses", headers=auth("DIRECTOR")).json()
    assert {"code": "WH-BDG", "name": "Gudang Cabang Bandung", "city_code": "BDG"} in rows


def test_vendor_filter_by_category(client, auth, seeded):
    rows = client.get("/api/v1/vendors?category=ROUTER", headers=auth("PROCUREMENT_STAFF")).json()
    assert [row["name"] for row in rows] == ["PT Router Mandiri"]
    assert isinstance(rows[0]["rating_score"], float)


# ---------------------------------------------------------------------------- barang


def test_create_item_appears_in_list(client, auth, seeded):
    response = client.post("/api/v1/items", json=NEW_ITEM, headers=auth("SCM_MANAGER"))
    assert response.status_code == 201, response.text
    assert response.json()["is_serialized"] is False

    skus = [row["sku"] for row in client.get("/api/v1/items?limit=100", headers=auth("SCM_MANAGER")).json()]
    assert "SPL-14" in skus
    seeded.expire_all()
    assert seeded.query(AuditLog).filter_by(action="item.created", entity_id="SPL-14").count() == 1


def test_duplicate_sku_is_409(client, auth, seeded):
    response = client.post("/api/v1/items", json={**NEW_ITEM, "sku": "ONT-01"}, headers=auth("SCM_MANAGER"))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DUPLICATE_SKU"


def test_patch_item_updates_fields(client, auth, seeded):
    response = client.patch("/api/v1/items/CBL-FO", json={"unit_cost": 4500, "reorder_point": 2500}, headers=auth("SCM_MANAGER"))
    assert response.status_code == 200, response.text
    seeded.expire_all()
    item = seeded.get(Item, "CBL-FO")
    assert (item.unit_cost, item.reorder_point, item.unit) == (4500, 2500, "METER")


def test_patch_unknown_item_is_404(client, auth, seeded):
    response = client.patch("/api/v1/items/NOPE-1", json={"name": "x"}, headers=auth("SCM_MANAGER"))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ITEM_NOT_FOUND"


def test_changing_is_serialized_on_ont_with_units_is_409(client, auth, seeded):
    seeded.add(SerializedUnit(serial_number="SN-TEST-0001", item_sku="ONT-01", warehouse_code="WH-BDG"))
    seeded.commit()

    response = client.patch("/api/v1/items/ONT-01", json={"is_serialized": False}, headers=auth("SCM_MANAGER"))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SERIALIZATION_LOCKED"
    seeded.expire_all()
    assert seeded.get(Item, "ONT-01").is_serialized is True


def test_changing_is_serialized_with_only_balance_is_409(client, auth, seeded):
    # RTR-AX non-serial dengan saldo di WH-BKS dan tanpa unit.
    response = client.patch("/api/v1/items/RTR-AX", json={"is_serialized": True}, headers=auth("SCM_MANAGER"))
    assert response.status_code == 409


def test_changing_is_serialized_without_stock_or_units_is_allowed(client, auth, seeded):
    assert client.post("/api/v1/items", json=NEW_ITEM, headers=auth("SCM_MANAGER")).status_code == 201
    response = client.patch("/api/v1/items/SPL-14", json={"is_serialized": True}, headers=auth("SCM_MANAGER"))
    assert response.status_code == 200, response.text
    assert response.json()["is_serialized"] is True


def test_zero_balance_row_does_not_lock_serialization(client, auth, seeded):
    assert client.post("/api/v1/items", json=NEW_ITEM, headers=auth("SCM_MANAGER")).status_code == 201
    seeded.add(InventoryBalance(warehouse_code="WH-BDG", item_sku="SPL-14", qty_physical=0, qty_reserved=0, qty_damaged=0))
    seeded.commit()
    response = client.patch("/api/v1/items/SPL-14", json={"is_serialized": True}, headers=auth("SCM_MANAGER"))
    assert response.status_code == 200


def test_same_is_serialized_value_is_not_a_change(client, auth, seeded):
    response = client.patch("/api/v1/items/ONT-01", json={"is_serialized": True, "name": "ONT Baru"}, headers=auth("SCM_MANAGER"))
    assert response.status_code == 200
    assert response.json()["name"] == "ONT Baru"


# ---------------------------------------------------------------------------- vendor


def test_create_vendor_gets_next_code(client, auth, seeded):
    body = {"name": "PT Splitter Jaya", "category": "PASIF", "rating_score": "4.25"}
    response = client.post("/api/v1/vendors", json=body, headers=auth("SCM_MANAGER"))
    assert response.status_code == 201, response.text
    assert response.json() == {"code": "VEN-0005", "name": "PT Splitter Jaya", "category": "PASIF", "rating_score": 4.25}


def test_create_vendor_is_idempotent(client, auth, seeded):
    headers = {**auth("SCM_MANAGER"), "Idempotency-Key": "vendor-1"}
    body = {"name": "PT Splitter Jaya", "category": "PASIF"}
    first = client.post("/api/v1/vendors", json=body, headers=headers)
    second = client.post("/api/v1/vendors", json=body, headers=headers)
    assert first.json() == second.json()
    assert client.get("/api/v1/vendors", headers=auth("SCM_MANAGER")).headers["X-Total-Count"] == "5"


def test_patch_vendor(client, auth, seeded):
    response = client.patch("/api/v1/vendors/VEN-0002", json={"rating_score": "3.90"}, headers=auth("SCM_MANAGER"))
    assert response.status_code == 200, response.text
    assert response.json()["rating_score"] == 3.9
    assert client.patch("/api/v1/vendors/VEN-9999", json={"name": "x"}, headers=auth("SCM_MANAGER")).status_code == 404


# ---------------------------------------------------------------------------- hak tulis


@pytest.mark.parametrize("role", ["DIRECTOR", "WAREHOUSE_STAFF", "PROCUREMENT_STAFF"])
def test_only_scm_manager_can_write(client, auth, seeded, role):
    headers = auth(role)
    assert client.post("/api/v1/items", json=NEW_ITEM, headers=headers).status_code == 403
    assert client.patch("/api/v1/items/CBL-FO", json={"unit_cost": 1}, headers=headers).status_code == 403
    assert client.post("/api/v1/vendors", json={"name": "X", "category": "Y"}, headers=headers).status_code == 403
    assert client.patch("/api/v1/vendors/VEN-0001", json={"name": "X"}, headers=headers).status_code == 403
    seeded.expire_all()
    assert seeded.get(Item, "SPL-14") is None
    assert seeded.get(Item, "CBL-FO").unit_cost == 4000
