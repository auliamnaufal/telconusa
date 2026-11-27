"""Logika bisnis Slice D: data master (SCM-D-01), daftar barang paket (SCM-D-02), API stok (SCM-D-03), dashboard (SCM-D-04),
audit log (SCM-D-06).

Semua fungsi berjalan di transaksi pemanggil dan tidak melakukan commit.
"""
import json
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Query, Session

from app.assets.models import SerializedUnit
from app.catalog.models import PackageKit, PackageKitLine
from app.core import audit, clock
from app.core.auth import Actor
from app.core.codes import new_vendor_code
from app.core.errors import ScmError
from app.core.models import AuditLog, InventoryBalance, Item, Vendor, Warehouse
from app.procurement.models import PurchaseOrder
from app.stock.models import StockRequest

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


def create_item(db: Session, data: dict[str, Any], actor: Actor, correlation_id: str | None = None) -> dict[str, Any]:
    sku = data["sku"]
    if db.get(Item, sku) is not None:
        raise ScmError("DUPLICATE_SKU", f"SKU {sku} sudah ada", 409, {"item_sku": sku})
    item = Item(sku=sku, **{field: data[field] for field in ITEM_FIELDS if field in data})
    db.add(item)
    db.flush()
    audit.record(db, actor, "item.create", "Item", sku, item_to_dict(item), correlation_id)
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


def update_item(
    db: Session, sku: str, changes: dict[str, Any], actor: Actor, correlation_id: str | None = None
) -> dict[str, Any]:
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
    audit.record(db, actor, "item.update", "Item", sku, {"before": before, "after": after}, correlation_id)
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


def create_vendor(db: Session, data: dict[str, Any], actor: Actor, correlation_id: str | None = None) -> dict[str, Any]:
    vendor = Vendor(code=new_vendor_code(db), **{field: data[field] for field in VENDOR_FIELDS if field in data})
    db.add(vendor)
    db.flush()
    audit.record(db, actor, "vendor.create", "Vendor", vendor.code, vendor_to_dict(vendor), correlation_id)
    return vendor_to_dict(vendor)


def update_vendor(
    db: Session, code: str, changes: dict[str, Any], actor: Actor, correlation_id: str | None = None
) -> dict[str, Any]:
    vendor = get_vendor(db, code)
    before = vendor_to_dict(vendor)
    for field in VENDOR_FIELDS:
        if field in changes:
            setattr(vendor, field, changes[field])
    db.flush()
    after = vendor_to_dict(vendor)
    audit.record(db, actor, "vendor.update", "Vendor", code, {"before": before, "after": after}, correlation_id)
    return after


# ---------------------------------------------------------------------------- paket


def get_kit(db: Session, service_sku: str) -> PackageKit:
    kit = db.get(PackageKit, service_sku)
    if kit is None:
        raise ScmError(
            "PACKAGE_KIT_NOT_FOUND",
            f"Paket {service_sku} belum punya daftar barang",
            404,
            {"service_sku": service_sku},
        )
    return kit


def list_kits(db: Session, page: int, limit: int) -> tuple[list[PackageKit], int]:
    return _page(db.query(PackageKit), PackageKit.service_sku, page, limit)


def kit_to_dict(db: Session, kit: PackageKit) -> dict[str, Any]:
    """Bentuk respons `getPackageKit` di `contracts/openapi/scm.yaml`."""
    lines = sorted(kit.lines, key=lambda line: line.item_sku)
    names = {item.sku: item.name for item in db.query(Item).filter(Item.sku.in_([line.item_sku for line in lines]))}
    return {
        "service_sku": kit.service_sku,
        "items": [
            {"item_sku": line.item_sku, "name": names[line.item_sku], "qty": line.qty, "unit": line.unit}
            for line in lines
        ],
    }


def replace_kit(
    db: Session, service_sku: str, lines: list[tuple[str, int]], actor: Actor, correlation_id: str | None = None
) -> dict[str, Any]:
    """Ganti seluruh baris paket; buat paket bila belum ada. Satuan diambil dari master barang."""
    skus = [sku for sku, _ in lines]
    duplicates = sorted({sku for sku in skus if skus.count(sku) > 1})
    if duplicates:
        raise ScmError("DUPLICATE_KIT_LINE", "Satu barang hanya boleh muncul sekali", 422, {"item_skus": duplicates})
    items = {item.sku: item for item in db.query(Item).filter(Item.sku.in_(skus))}
    unknown = [sku for sku in skus if sku not in items]
    if unknown:
        raise ScmError("ITEM_NOT_FOUND", "Barang tidak dikenal", 422, {"item_skus": unknown})

    kit = db.get(PackageKit, service_sku)
    before = kit_to_dict(db, kit) if kit is not None else None
    if kit is None:
        kit = PackageKit(service_sku=service_sku)
        db.add(kit)
    kit.lines = [PackageKitLine(item_sku=sku, qty=qty, unit=items[sku].unit) for sku, qty in lines]
    db.flush()
    after = kit_to_dict(db, kit)
    audit.record(
        db, actor, "package_kit.replace", "PackageKit", service_sku, {"before": before, "after": after}, correlation_id
    )
    return after


# ---------------------------------------------------------------------------- stok


def _scope_warehouses(db: Session, warehouse_code: str | None, city_code: str | None) -> list[str]:
    """Gudang dalam lingkup; tanpa filter berarti semua gudang."""
    query = db.query(Warehouse.code)
    if warehouse_code:
        query = query.filter(Warehouse.code == warehouse_code)
    if city_code:
        query = query.filter(Warehouse.city_code == city_code)
    codes = [code for (code,) in query.order_by(Warehouse.code)]
    if not codes:
        raise ScmError(
            "WAREHOUSE_NOT_FOUND",
            "Tidak ada gudang untuk lingkup yang diminta",
            404,
            {"warehouse_code": warehouse_code, "city_code": city_code},
        )
    return codes


def stock_availability(db: Session, sku: str, warehouse_code: str | None, city_code: str | None) -> dict[str, Any]:
    """Ketersediaan indikatif untuk CRM (`getStock`). Barang rusak dan tereservasi tidak dihitung.

    `reorder_point` di master berlaku per gudang, jadi ROP lingkup = ROP x jumlah gudang dalam lingkup.
    """
    item = get_item(db, sku)
    codes = _scope_warehouses(db, warehouse_code, city_code)
    balances = (
        db.query(InventoryBalance)
        .filter(InventoryBalance.item_sku == sku, InventoryBalance.warehouse_code.in_(codes))
        .all()
    )
    qty_available = sum(balance.qty_available for balance in balances)
    reorder_point = item.reorder_point * len(codes)
    return {
        "sku": item.sku,
        "name": item.name,
        "unit": item.unit,
        "qty_available": qty_available,
        "reorder_point": reorder_point,
        "below_rop": qty_available < reorder_point,
    }


def list_balances(
    db: Session, warehouse_code: str | None, item_sku: str | None, page: int, limit: int
) -> tuple[list[tuple[InventoryBalance, Item]], int]:
    query = db.query(InventoryBalance, Item).join(Item, Item.sku == InventoryBalance.item_sku)
    if warehouse_code:
        query = query.filter(InventoryBalance.warehouse_code == warehouse_code)
    if item_sku:
        query = query.filter(InventoryBalance.item_sku == item_sku)
    total = query.count()
    rows = (
        query.order_by(InventoryBalance.warehouse_code, InventoryBalance.item_sku)
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return rows, total


def balance_to_dict(balance: InventoryBalance, item: Item) -> dict[str, Any]:
    return {
        "warehouse_code": balance.warehouse_code,
        "item_sku": balance.item_sku,
        "name": item.name,
        "unit": item.unit,
        "qty_physical": balance.qty_physical,
        "qty_reserved": balance.qty_reserved,
        "qty_damaged": balance.qty_damaged,
        "qty_available": balance.qty_available,
        "reorder_point": item.reorder_point,
        "below_rop": balance.qty_available < item.reorder_point,
    }


# ---------------------------------------------------------------------------- dashboard

# Tabel slice lain hanya dibaca lewat kueri; kode slice lain tidak dipanggil.
OPEN_STOCK_REQUEST_STATUSES = ("REQUESTED", "PENDING_STOCK", "READY_TO_ISSUE", "ISSUED")
OPEN_PURCHASE_ORDER_STATUSES = ("DRAFT", "PENDING_APPROVAL", "APPROVED", "PARTIALLY_RECEIVED")
RECENT_STOCK_REQUESTS = 10


def _count_stock_requests(db: Session, *statuses: str) -> int:
    return db.query(StockRequest).filter(StockRequest.status.in_(statuses)).count()


def dashboard_summary(db: Session) -> dict[str, Any]:
    valuation = (
        db.query(func.coalesce(func.sum((InventoryBalance.qty_physical - InventoryBalance.qty_damaged) * Item.unit_cost), 0))
        .select_from(InventoryBalance)
        .join(Item, Item.sku == InventoryBalance.item_sku)
        .scalar()
    )
    recent = (
        db.query(StockRequest)
        .order_by(StockRequest.created_at.desc(), StockRequest.stock_request_no.desc())
        .limit(RECENT_STOCK_REQUESTS)
        .all()
    )
    return {
        "kpis": {
            "total_skus": db.query(Item).count(),
            "inventory_valuation_idr": int(valuation),
            "open_stock_requests": _count_stock_requests(db, *OPEN_STOCK_REQUEST_STATUSES),
            "return_pending": _count_stock_requests(db, "ISSUED"),
            "active_reservations": _count_stock_requests(db, "READY_TO_ISSUE"),
            "open_purchase_orders": db.query(PurchaseOrder)
            .filter(PurchaseOrder.status.in_(OPEN_PURCHASE_ORDER_STATUSES))
            .count(),
            "ont_installed": db.query(SerializedUnit).filter(SerializedUnit.status == "INSTALLED").count(),
        },
        "stock_requests": [
            {"stock_request_no": row.stock_request_no, "ticket_code": row.ticket_code, "status": row.status}
            for row in recent
        ],
    }


# ---------------------------------------------------------------------------- audit log


def list_audit_logs(
    db: Session, entity: str | None, entity_id: str | None, actor: str | None, page: int, limit: int
) -> tuple[list[AuditLog], int]:
    query = db.query(AuditLog)
    if entity:
        query = query.filter(AuditLog.entity == entity)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if actor:
        query = query.filter(AuditLog.actor == actor)
    total = query.count()
    rows = query.order_by(AuditLog.at.desc(), AuditLog.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return rows, total


def audit_to_dict(row: AuditLog) -> dict[str, Any]:
    return {
        "id": row.id,
        "at": clock.to_wib_iso(row.at),
        "actor": row.actor,
        "role": row.role,
        "action": row.action,
        "entity": row.entity,
        "entity_id": row.entity_id,
        "detail": json.loads(row.detail) if row.detail else None,
        "correlation_id": row.correlation_id,
    }
