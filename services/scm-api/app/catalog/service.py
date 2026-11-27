"""Logika bisnis Slice D: data master barang, gudang, vendor (SCM-D-01).

Semua fungsi berjalan di transaksi pemanggil dan tidak melakukan commit.
"""
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.assets.models import SerializedUnit
from app.core import audit
from app.core.auth import Actor
from app.core.codes import new_vendor_code
from app.core.errors import ScmError
from app.core.models import InventoryBalance, Item, Vendor, Warehouse

ITEM_FIELDS = ("name", "unit", "unit_cost", "reorder_point", "safety_stock", "is_serialized", "specification")
VENDOR_FIELDS = ("name", "category", "rating_score")


def _page(query: Query, order_by, page: int, limit: int) -> tuple[list, int]:
    total = query.count()
    rows = query.order_by(order_by).offset((page - 1) * limit).limit(limit).all()
    return rows, total


# ---------------------------------------------------------------------------- barang


def get_item(db: Session, sku: str) -> Item:
    item = db.get(Item, sku)
    if item is None:
        raise ScmError("ITEM_NOT_FOUND", f"Barang {sku} tidak ditemukan", 404, {"item_sku": sku})
    return item


def list_items(db: Session, q: str | None, page: int, limit: int) -> tuple[list[Item], int]:
    query = db.query(Item)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Item.sku.like(like), Item.name.like(like)))
    return _page(query, Item.sku, page, limit)


def item_to_dict(item: Item) -> dict[str, Any]:
    return {
        "sku": item.sku,
        "name": item.name,
        "unit": item.unit,
        "unit_cost": item.unit_cost,
        "reorder_point": item.reorder_point,
        "safety_stock": item.safety_stock,
        "is_serialized": bool(item.is_serialized),
        "specification": item.specification,
    }


def create_item(db: Session, data: dict[str, Any], actor: Actor) -> dict[str, Any]:
    sku = data["sku"]
    if db.get(Item, sku) is not None:
        raise ScmError("DUPLICATE_SKU", f"SKU {sku} sudah ada", 409, {"item_sku": sku})
    item = Item(sku=sku, **{field: data[field] for field in ITEM_FIELDS if field in data})
    db.add(item)
    db.flush()
    audit.record(db, actor, "item.created", "item", sku, item_to_dict(item))
    return item_to_dict(item)


def _has_stock_or_units(db: Session, sku: str) -> bool:
    has_balance = (
        db.query(InventoryBalance)
        .filter(
            InventoryBalance.item_sku == sku,
            or_(InventoryBalance.qty_physical != 0, InventoryBalance.qty_reserved != 0, InventoryBalance.qty_damaged != 0),
        )
        .first()
        is not None
    )
    # Hanya membaca tabel Slice C; tidak menulis.
    has_units = db.query(SerializedUnit).filter(SerializedUnit.item_sku == sku).first() is not None
    return has_balance or has_units


def update_item(db: Session, sku: str, changes: dict[str, Any], actor: Actor) -> dict[str, Any]:
    item = get_item(db, sku)
    if (
        "is_serialized" in changes
        and bool(changes["is_serialized"]) != bool(item.is_serialized)
        and _has_stock_or_units(db, sku)
    ):
        raise ScmError(
            "SERIALIZATION_LOCKED",
            f"is_serialized pada {sku} tidak bisa diubah karena sudah ada saldo atau unit",
            409,
            {"item_sku": sku},
        )
    before = item_to_dict(item)
    for field in ITEM_FIELDS:
        if field in changes:
            setattr(item, field, changes[field])
    db.flush()
    after = item_to_dict(item)
    audit.record(db, actor, "item.updated", "item", sku, {"before": before, "after": after})
    return after


# ---------------------------------------------------------------------------- gudang


def list_warehouses(db: Session, page: int, limit: int) -> tuple[list[Warehouse], int]:
    return _page(db.query(Warehouse), Warehouse.code, page, limit)


def warehouse_to_dict(warehouse: Warehouse) -> dict[str, Any]:
    return {"code": warehouse.code, "name": warehouse.name, "city_code": warehouse.city_code}


# ---------------------------------------------------------------------------- vendor


def get_vendor(db: Session, code: str) -> Vendor:
    vendor = db.get(Vendor, code)
    if vendor is None:
        raise ScmError("VENDOR_NOT_FOUND", f"Vendor {code} tidak ditemukan", 404, {"vendor_code": code})
    return vendor


def list_vendors(db: Session, category: str | None, page: int, limit: int) -> tuple[list[Vendor], int]:
    query = db.query(Vendor)
    if category:
        query = query.filter(Vendor.category == category)
    return _page(query, Vendor.code, page, limit)


def vendor_to_dict(vendor: Vendor) -> dict[str, Any]:
    return {
        "code": vendor.code,
        "name": vendor.name,
        "category": vendor.category,
        "rating_score": float(vendor.rating_score) if vendor.rating_score is not None else None,
    }


def create_vendor(db: Session, data: dict[str, Any], actor: Actor) -> dict[str, Any]:
    vendor = Vendor(code=new_vendor_code(db), **{field: data[field] for field in VENDOR_FIELDS if field in data})
    db.add(vendor)
    db.flush()
    audit.record(db, actor, "vendor.created", "vendor", vendor.code, vendor_to_dict(vendor))
    return vendor_to_dict(vendor)


def update_vendor(db: Session, code: str, changes: dict[str, Any], actor: Actor) -> dict[str, Any]:
    vendor = get_vendor(db, code)
    before = vendor_to_dict(vendor)
    for field in VENDOR_FIELDS:
        if field in changes:
            setattr(vendor, field, changes[field])
    db.flush()
    after = vendor_to_dict(vendor)
    audit.record(db, actor, "vendor.updated", "vendor", code, {"before": before, "after": after})
    return after
