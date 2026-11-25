import json
import uuid
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.auth import SCM_ROLES, require_roles
from shared.config import settings
from shared.events import publish_event, verify_signature
from shared.schemas import HealthResponse, now_wib_iso

from app.database import get_db
from app.models import (
    InventoryBalance,
    Item,
    OutboxEvent,
    ProcessedEvent,
    PurchaseOrder,
    SerializedUnit,
    TechnicianKit,
    Vendor,
    Warehouse,
)

app = FastAPI(
    title="TelcoNusa SCM API",
    version="2.0.0",
    description="Divisi SCM — Gudang, Stok & ROP, Serialized ONT, Paket Material Teknisi & Retur, Vendor Scorecard, & PO + Cek Anggaran Finance.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class KitReconcileRequest(BaseModel):
    kit_code: str
    cable_used_meters: int
    ont_serial_number: Optional[str] = None


class CreatePORequest(BaseModel):
    vendor_code: str
    item_sku: str
    qty: int


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(service="scm-api", transport=settings.EVENT_TRANSPORT, timestamp=now_wib_iso())


@app.get("/api/v1/stock/{sku}")
def get_stock(sku: str, warehouse_code: Optional[str] = None, db: Session = Depends(get_db)):
    item = db.query(Item).filter_by(sku=sku).first()
    if not item:
        raise HTTPException(status_code=404, detail="SKU barang tidak ditemukan")
    q = db.query(InventoryBalance).filter_by(item_sku=sku)
    if warehouse_code:
        q = q.filter_by(warehouse_code=warehouse_code)
    rows = q.all()
    qty_available = sum(r.qty_physical - r.qty_reserved - r.qty_damaged for r in rows)
    return {
        "sku": item.sku,
        "name": item.name,
        "unit": item.unit,
        "unit_cost": item.unit_cost,
        "specification": item.specification,
        "qty_available": qty_available,
        "reorder_point": item.reorder_point,
        "below_rop": qty_available < item.reorder_point,
    }


@app.get("/api/v1/items/requirements")
def item_requirements(sku: str = "HOME-50", db: Session = Depends(get_db)):
    ont = db.query(Item).filter_by(sku="ONT-01").first()
    cable = db.query(Item).filter_by(sku="CBL-FO").first()
    if sku.startswith("HOME"):
        return {
            "service_sku": sku,
            "required_kit": [
                {"item_sku": "ONT-01", "name": ont.name if ont else "Modem ONT", "qty": 1, "unit": "UNIT", "specification": ont.specification if ont else ""},
                {"item_sku": "CBL-FO", "name": cable.name if cable else "Kabel Fiber", "qty": 50, "unit": "METER", "specification": cable.specification if cable else ""},
            ],
        }
    return {"service_sku": sku, "required_kit": [{"item_sku": "SIM-01", "name": "Kartu SIM 5G", "qty": 1, "unit": "PCS"}]}


@app.post("/api/v1/technician-kits/reconcile")
def reconcile_kit(
    body: KitReconcileRequest,
    user: dict = Depends(require_roles(*SCM_ROLES)),
    db: Session = Depends(get_db),
):
    kit = db.query(TechnicianKit).filter_by(kit_code=body.kit_code).first()
    if not kit:
        raise HTTPException(status_code=404, detail="Kit teknisi tidak ditemukan")
    kit.cable_used_meters = body.cable_used_meters
    kit.cable_returned_meters = max(0, kit.cable_issued_meters - body.cable_used_meters)
    kit.status = "RECONCILED"
    if body.ont_serial_number:
        unit = db.query(SerializedUnit).filter_by(serial_number=body.ont_serial_number).first()
        if unit:
            unit.status = "INSTALLED"
    bal = db.query(InventoryBalance).filter_by(warehouse_code="WH-BDG", item_sku="CBL-FO").first()
    if bal:
        bal.qty_physical += kit.cable_returned_meters
    db.commit()
    return {
        "kit_code": kit.kit_code,
        "cable_used_meters": kit.cable_used_meters,
        "cable_returned_meters": kit.cable_returned_meters,
        "status": kit.status,
    }


@app.post("/api/v1/purchase-orders", status_code=201)
async def create_po(
    body: CreatePORequest,
    user: dict = Depends(require_roles(*SCM_ROLES)),
    db: Session = Depends(get_db),
):
    item = db.query(Item).filter_by(sku=body.item_sku).first()
    if not item:
        raise HTTPException(status_code=404, detail="SKU tidak ditemukan")
    total = int(item.unit_cost) * body.qty

    budget_approved = True
    budget_remaining = None
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.post(
                f"{settings.FINANCE_API_URL}/api/v1/budgets/check",
                json={"cost_center_code": "CC-SCM", "amount": total},
            )
            if r.status_code == 200:
                bdata = r.json()
                budget_approved = bdata.get("approved", True)
                budget_remaining = bdata.get("remaining")
    except Exception:
        pass

    if not budget_approved:
        raise HTTPException(
            status_code=422,
            detail=f"Anggaran CC-SCM tidak cukup. Diminta Rp{total:,}, sisa Rp{budget_remaining:,}.",
        )

    po_no = f"PO-2026-{db.query(PurchaseOrder).count() + 1:04d}"
    po = PurchaseOrder(
        po_no=po_no,
        vendor_code=body.vendor_code,
        item_sku=body.item_sku,
        qty=body.qty,
        unit_price=item.unit_cost,
        total_amount=total,
        status="APPROVED",
    )
    db.add(po)
    payload = {"po_no": po_no, "vendor_code": body.vendor_code, "item_sku": body.item_sku, "qty": body.qty, "total_amount": total}
    db.add(OutboxEvent(event_type="po.approved", correlation_id=po_no, payload_json=json.dumps(payload)))
    db.commit()
    await publish_event("po.approved", "scm", po_no, payload)
    return {"po_no": po_no, "total_amount": total, "status": po.status, "budget_remaining_after_check": budget_remaining}


@app.get("/api/v1/dashboard/summary")
def scm_dashboard_summary(
    user: dict = Depends(require_roles(*SCM_ROLES)),
    db: Session = Depends(get_db),
):
    items_list = db.query(Item).all()
    items = {i.sku: i for i in items_list}
    balances = db.query(InventoryBalance).all()
    units = db.query(SerializedUnit).all()
    kits = db.query(TechnicianKit).order_by(TechnicianKit.created_at.desc()).limit(20).all()
    pos = db.query(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).limit(20).all()
    vendors_list = db.query(Vendor).all()
    vendors = {v.code: v for v in vendors_list}
    warehouses = db.query(Warehouse).all()

    total_val = sum((b.qty_physical - b.qty_damaged) * items[b.item_sku].unit_cost for b in balances if b.item_sku in items)
    return {
        "kpis": {
            "total_skus": len(items),
            "total_warehouses": len(warehouses),
            "inventory_valuation_idr": total_val,
            "active_kits": sum(1 for k in kits if k.status != "RECONCILED"),
            "total_purchase_orders": len(pos),
        },
        "warehouses": [{"code": w.code, "name": w.name, "city_code": w.city_code} for w in warehouses],
        "inventory": [
            {
                "warehouse_code": b.warehouse_code,
                "item_sku": b.item_sku,
                "item_name": items[b.item_sku].name if b.item_sku in items else b.item_sku,
                "unit": items[b.item_sku].unit if b.item_sku in items else "UNIT",
                "specification": items[b.item_sku].specification if b.item_sku in items else "",
                "qty_physical": b.qty_physical,
                "qty_reserved": b.qty_reserved,
                "qty_damaged": b.qty_damaged,
                "qty_available": b.qty_physical - b.qty_reserved - b.qty_damaged,
                "reorder_point": items[b.item_sku].reorder_point if b.item_sku in items else 100,
                "safety_stock": items[b.item_sku].safety_stock if b.item_sku in items else 50,
                "unit_cost": items[b.item_sku].unit_cost if b.item_sku in items else 0,
            }
            for b in balances
        ],
        "serialized_units": [
            {
                "serial_number": u.serial_number,
                "item_sku": u.item_sku,
                "warehouse_code": u.warehouse_code,
                "status": u.status,
                "assigned_technician_id": u.assigned_technician_id,
                "installed_order_no": u.installed_order_no,
            }
            for u in units
        ],
        "technician_kits": [
            {
                "kit_code": k.kit_code,
                "work_order_code": k.work_order_code,
                "technician_employee_id": k.technician_employee_id,
                "ont_serial_number": k.ont_serial_number,
                "cable_issued_meters": k.cable_issued_meters,
                "cable_used_meters": k.cable_used_meters,
                "cable_returned_meters": k.cable_returned_meters,
                "status": k.status,
            }
            for k in kits
        ],
        "vendors": [
            {"code": v.code, "name": v.name, "category": v.category, "rating_score": float(v.rating_score)}
            for v in vendors_list
        ],
        "purchase_orders": [
            {
                "po_no": p.po_no,
                "vendor_code": p.vendor_code,
                "vendor_name": vendors[p.vendor_code].name if p.vendor_code in vendors else p.vendor_code,
                "item_sku": p.item_sku,
                "qty": p.qty,
                "unit_price": p.unit_price,
                "total_amount": p.total_amount,
                "status": p.status,
            }
            for p in pos
        ],
    }


@app.post("/internal/events")
async def receive_event(
    request: Request,
    x_telconusa_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    raw_body = await request.body()
    if x_telconusa_signature is not None and not verify_signature(raw_body, x_telconusa_signature):
        raise HTTPException(status_code=401, detail="Invalid event HMAC signature")
    event = json.loads(raw_body.decode("utf-8"))
    event_id = event.get("event_id", str(uuid.uuid4()))
    if db.query(ProcessedEvent).filter_by(event_id=event_id).first():
        return {"status": "duplicate_ignored"}

    event_type = event.get("event_type")
    data = event.get("data", {})
    if event_type == "kit.reconciled":
        kit = db.query(TechnicianKit).filter_by(work_order_code=data.get("work_order_code")).first()
        if kit:
            used = int(data.get("cable_used_meters", 25))
            kit.cable_used_meters = used
            kit.cable_returned_meters = max(0, kit.cable_issued_meters - used)
            kit.status = "RECONCILED"
            bal = db.query(InventoryBalance).filter_by(warehouse_code="WH-BDG", item_sku="CBL-FO").first()
            if bal:
                bal.qty_physical += kit.cable_returned_meters

    db.add(ProcessedEvent(event_id=event_id, event_type=event_type or "unknown"))
    db.commit()
    return {"status": "processed", "event_id": event_id}
