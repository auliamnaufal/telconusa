import json
import uuid
from datetime import date
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from shared.auth import (
    CRM_STAFF_ROLES,
    create_access_token,
    get_current_user,
    hash_password,
    require_roles,
    verify_password,
)
from shared.config import settings
from shared.events import publish_event, verify_signature
from shared.schemas import HealthResponse, now_wib_iso

from app.database import get_db
from app.models import (
    Campaign,
    CatalogProduct,
    CoverageArea,
    Customer,
    CustomerInstallAddress,
    Order,
    OutboxEvent,
    ProcessedEvent,
    Subscription,
    TechnicianRating,
    Ticket,
    WorkOrder,
)

app = FastAPI(
    title="TelcoNusa CRM API",
    version="2.1.0",
    description="Divisi CRM — Storefront Personal, Registrasi Pelanggan, Order + Referral (Auth-Gated), Work Order Teknisi, Tiket SLA & CS 24/7, Rating Teknisi.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CustomerRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=5, max_length=120)
    whatsapp_number: str = Field(..., min_length=8, max_length=20)
    password: str = Field(..., min_length=6, max_length=128)
    nik_or_npwp: Optional[str] = None


class CustomerLoginRequest(BaseModel):
    email: str
    password: str


class AuthenticatedOrderRequest(BaseModel):
    install_address: str = Field(..., min_length=5)
    city_code: str = Field(..., pattern="^(JKT|BDG|SBY)$")
    postal_code: str = Field(..., min_length=3, max_length=10)
    sku: str
    referral_code: Optional[str] = None
    customer_code: Optional[str] = None


class PublicOrderRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    whatsapp_number: Optional[str] = None
    install_address: str = Field(..., min_length=5)
    city_code: str = Field(..., pattern="^(JKT|BDG|SBY)$")
    postal_code: str = Field(..., min_length=3, max_length=10)
    sku: str
    referral_code: Optional[str] = None


class PublicSupportRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=5, max_length=120)
    whatsapp_number: Optional[str] = None
    priority: str = Field(default="P3", pattern="^P[1-4]$")
    subject: str = Field(..., min_length=3, max_length=160)
    description: str = Field(..., min_length=5)


class TechnicianRatingRequest(BaseModel):
    work_order_id: str
    rating_score: int = Field(..., ge=1, le=5)
    rating_comment: Optional[str] = None


class WorkOrderAssignRequest(BaseModel):
    technician_employee_id: str


class WorkOrderUpdateRequest(BaseModel):
    installation_status: str
    ont_serial_number: Optional[str] = None
    cable_used_meters: Optional[int] = None
    signal_dbm: Optional[float] = None
    speedtest_mbps: Optional[float] = None
    site_condition_notes: Optional[str] = None


class TicketCreateRequest(BaseModel):
    customer_code: Optional[str] = None
    priority: str = Field(default="P2", pattern="^P[1-4]$")
    subject: str = Field(..., min_length=3, max_length=160)
    description: str = Field(..., min_length=3)


def _next_customer_code(db: Session) -> str:
    n = db.query(Customer).count() + 459
    while db.query(Customer).filter_by(customer_code=f"CUS-{n:06d}").first():
        n += 1
    return f"CUS-{n:06d}"


def _next_address_code(db: Session) -> str:
    n = db.query(CustomerInstallAddress).count() + 1
    while db.query(CustomerInstallAddress).filter_by(address_code=f"ADR-{n:06d}").first():
        n += 1
    return f"ADR-{n:06d}"


def _next_order_no(db: Session) -> str:
    n = db.query(Order).count() + 124
    while db.query(Order).filter_by(order_no=f"ORD-2026-{n:06d}").first():
        n += 1
    return f"ORD-2026-{n:06d}"


def _next_wo_code(db: Session) -> str:
    n = db.query(WorkOrder).count() + 1
    while db.query(WorkOrder).filter_by(work_order_code=f"WO-{n:06d}").first():
        n += 1
    return f"WO-{n:06d}"


def _next_ticket_code(db: Session) -> str:
    n = db.query(Ticket).count() + 1
    while db.query(Ticket).filter_by(ticket_code=f"TKT-{n:06d}").first():
        n += 1
    return f"TKT-{n:06d}"


async def _create_order_workflow(
    db: Session,
    cust: Customer,
    install_address: str,
    city_code: str,
    postal_code: str,
    sku: str,
    referral_code: Optional[str],
) -> dict:
    product = db.query(CatalogProduct).filter_by(sku=sku, is_active=True).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"SKU {sku} tidak ditemukan")

    addr_code = _next_address_code(db)
    addr = CustomerInstallAddress(
        address_code=addr_code,
        customer_id=cust.id,
        label=f"Alamat {city_code} #{addr_code[-3:]}",
        install_address=install_address.strip(),
        city_code=city_code,
        postal_code=postal_code.strip(),
    )
    db.add(addr)
    db.flush()

    order_status = "CONFIRMED"
    if product.business_line == "HOME":
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{settings.SCM_API_URL}/api/v1/stock/ONT-01")
                if r.status_code == 200 and r.json().get("qty_available", 0) <= 0:
                    order_status = "ON_HOLD"
        except Exception:
            pass

    install_fee = 150000 if product.business_line == "HOME" else 0
    subtotal = int(product.unit_price) + install_fee
    order_no = _next_order_no(db)

    sales_emp_id = None
    cleaned_ref = referral_code.strip() if referral_code and referral_code.strip() else None
    if cleaned_ref:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                ref_res = await client.get(f"{settings.HRM_API_URL}/api/v1/referrals/{cleaned_ref}")
                if ref_res.status_code == 200:
                    sales_emp_id = ref_res.json().get("employee_code")
        except Exception:
            pass

    order = Order(
        order_no=order_no,
        customer_id=cust.id,
        install_address_id=addr.id,
        sku=product.sku,
        business_line=product.business_line,
        sales_employee_id=sales_emp_id,
        referral_code=cleaned_ref,
        subtotal=subtotal,
        status=order_status,
    )
    db.add(order)
    db.flush()

    wo_code = _next_wo_code(db)
    wo = WorkOrder(
        work_order_code=wo_code,
        order_id=order.id,
        install_address_id=addr.id,
        installation_status="PENDING_ASSIGNMENT",
        scheduled_date=date.today(),
    )
    db.add(wo)

    payload = {
        "order_no": order_no,
        "customer_code": cust.customer_code,
        "customer_name": cust.full_name,
        "sku": product.sku,
        "business_line": product.business_line,
        "subtotal": subtotal,
        "monthly_price": int(product.unit_price),
        "referral_code": cleaned_ref,
        "sales_employee_id": sales_emp_id,
    }
    db.add(OutboxEvent(event_type="order.confirmed", correlation_id=order_no, payload_json=json.dumps(payload)))
    db.commit()

    if order_status == "CONFIRMED":
        await publish_event("order.confirmed", "crm", order_no, payload)

    return {
        "order_no": order_no,
        "customer_code": cust.customer_code,
        "work_order_code": wo_code,
        "status": order_status,
        "subtotal": subtotal,
        "tax_amount": round(subtotal * settings.PPN_RATE),
        "estimated_total_with_ppn": round(subtotal * (1 + settings.PPN_RATE)),
    }


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(service="crm-api", transport=settings.EVENT_TRANSPORT, timestamp=now_wib_iso())


@app.get("/api/v1/catalog")
def list_catalog(business_line: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(CatalogProduct).filter(CatalogProduct.is_active == True)
    if business_line:
        q = q.filter(CatalogProduct.business_line == business_line.upper())
    items = q.all()
    return [
        {
            "sku": p.sku,
            "name": p.name,
            "business_line": p.business_line,
            "unit_price": p.unit_price,
            "billing_cycle": p.billing_cycle,
            "description": p.description,
            "speed_label": p.speed_label,
        }
        for p in items
    ]


@app.get("/api/v1/coverage")
def check_coverage(postal_code: Optional[str] = None, db: Session = Depends(get_db)):
    if postal_code:
        area = db.query(CoverageArea).filter_by(postal_code=postal_code.strip(), is_covered=True).first()
        return {
            "postal_code": postal_code.strip(),
            "is_covered": area is not None,
            "city_code": area.city_code if area else None,
            "city_name": area.city_name if area else None,
            "district": area.district if area else None,
        }
    return [
        {
            "city_code": a.city_code,
            "city_name": a.city_name,
            "district": a.district,
            "postal_code": a.postal_code,
            "is_covered": a.is_covered,
        }
        for a in db.query(CoverageArea).all()
    ]


@app.post("/api/v1/auth/register", status_code=201)
def customer_register(body: CustomerRegisterRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if db.query(Customer).filter_by(email=email).first():
        raise HTTPException(status_code=409, detail="Email sudah terdaftar. Silakan masuk dengan akun Anda.")

    nik_clean = (body.nik_or_npwp or "").strip() or None
    if nik_clean and db.query(Customer).filter_by(nik_or_npwp=nik_clean).first():
        raise HTTPException(status_code=409, detail="NIK/NPWP sudah terdaftar di sistem.")

    cust = Customer(
        customer_code=_next_customer_code(db),
        full_name=body.full_name.strip(),
        email=email,
        whatsapp_number=body.whatsapp_number.strip(),
        nik_or_npwp=nik_clean,
        password_hash=hash_password(body.password),
        segment="INDIVIDUAL",
    )
    db.add(cust)
    db.commit()
    db.refresh(cust)

    token = create_access_token({
        "sub": cust.customer_code,
        "role": "CUSTOMER",
        "name": cust.full_name,
        "email": cust.email,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "code": cust.customer_code,
            "name": cust.full_name,
            "email": cust.email,
            "whatsapp_number": cust.whatsapp_number,
            "role": "CUSTOMER",
        },
    }


@app.post("/api/v1/auth/login")
def customer_login(body: CustomerLoginRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    cust = db.query(Customer).filter_by(email=email).first()
    if not cust or not verify_password(body.password, cust.password_hash):
        raise HTTPException(status_code=401, detail="Email atau password pelanggan salah")
    token = create_access_token({
        "sub": cust.customer_code,
        "role": "CUSTOMER",
        "name": cust.full_name,
        "email": cust.email,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "code": cust.customer_code,
            "name": cust.full_name,
            "email": cust.email,
            "whatsapp_number": cust.whatsapp_number,
            "role": "CUSTOMER",
        },
    }


@app.get("/api/v1/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    return {"user": user}


@app.post("/api/v1/orders", status_code=201)
async def create_authenticated_order(
    body: AuthenticatedOrderRequest,
    user: dict = Depends(require_roles("CUSTOMER", *CRM_STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    if user.get("role") == "CUSTOMER":
        cust = db.query(Customer).filter_by(customer_code=user.get("sub")).first()
    else:
        target_code = body.customer_code or "CUS-000456"
        cust = db.query(Customer).filter_by(customer_code=target_code).first() or db.query(Customer).first()
    if not cust:
        raise HTTPException(status_code=404, detail="Profil pelanggan tidak ditemukan")

    return await _create_order_workflow(
        db=db,
        cust=cust,
        install_address=body.install_address,
        city_code=body.city_code,
        postal_code=body.postal_code,
        sku=body.sku,
        referral_code=body.referral_code,
    )


@app.post("/api/v1/public/orders", status_code=201)
async def create_public_order(
    body: PublicOrderRequest,
    user: dict = Depends(require_roles("CUSTOMER", *CRM_STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    if user.get("role") == "CUSTOMER":
        cust = db.query(Customer).filter_by(customer_code=user.get("sub")).first()
    elif body.email:
        email = body.email.strip().lower()
        cust = db.query(Customer).filter_by(email=email).first()
        if not cust:
            cust = Customer(
                customer_code=_next_customer_code(db),
                full_name=(body.full_name or "Pelanggan TelcoNusa").strip(),
                email=email,
                whatsapp_number=(body.whatsapp_number or "-").strip(),
                nik_or_npwp=None,
                password_hash=hash_password("telconusa123"),
                segment="INDIVIDUAL",
            )
            db.add(cust)
            db.flush()
    else:
        cust = db.query(Customer).filter_by(customer_code="CUS-000456").first() or db.query(Customer).first()

    if not cust:
        raise HTTPException(status_code=404, detail="Profil pelanggan tidak ditemukan")

    return await _create_order_workflow(
        db=db,
        cust=cust,
        install_address=body.install_address,
        city_code=body.city_code,
        postal_code=body.postal_code,
        sku=body.sku,
        referral_code=body.referral_code,
    )


@app.post("/api/v1/public/support", status_code=201)
def create_public_support_ticket(body: PublicSupportRequest, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    cust = db.query(Customer).filter_by(email=email).first()
    if not cust:
        cust = Customer(
            customer_code=_next_customer_code(db),
            full_name=body.full_name.strip(),
            email=email,
            whatsapp_number=(body.whatsapp_number or "-").strip(),
            nik_or_npwp=None,
            password_hash=hash_password(uuid.uuid4().hex),
            segment="PROSPECT",
        )
        db.add(cust)
        db.flush()

    t_code = _next_ticket_code(db)
    t = Ticket(
        ticket_code=t_code,
        customer_id=cust.id,
        priority=body.priority,
        subject=body.subject.strip()[:160],
        description=body.description.strip(),
        status="OPEN",
    )
    db.add(t)
    db.commit()
    return {
        "ticket_code": t.ticket_code,
        "status": t.status,
        "priority": t.priority,
        "customer_code": cust.customer_code,
        "message": "Tiket layanan CS 24/7 berhasil dibuat dan diteruskan ke antrean tim CRM.",
    }


@app.get("/api/v1/portal/me")
async def get_customer_portal(
    user: dict = Depends(require_roles("CUSTOMER", "CRM_MANAGER", "DIRECTOR")),
    db: Session = Depends(get_db),
):
    if user.get("role") == "CUSTOMER":
        cust = db.query(Customer).filter_by(customer_code=user.get("sub")).first()
    else:
        cust = db.query(Customer).filter_by(customer_code="CUS-000456").first() or db.query(Customer).first()
    if not cust:
        raise HTTPException(status_code=404, detail="Profil pelanggan tidak ditemukan")

    addresses = db.query(CustomerInstallAddress).filter_by(customer_id=cust.id).all()
    addr_map = {a.id: a for a in addresses}
    orders = db.query(Order).filter_by(customer_id=cust.id).order_by(Order.created_at.desc()).all()
    order_ids = [o.id for o in orders]
    order_map = {o.id: o for o in orders}
    subs = db.query(Subscription).filter_by(customer_id=cust.id).all()
    wos = db.query(WorkOrder).filter(WorkOrder.order_id.in_(order_ids)).order_by(WorkOrder.created_at.desc()).all() if order_ids else []
    tickets = db.query(Ticket).filter_by(customer_id=cust.id).order_by(Ticket.created_at.desc()).all()
    ratings = {r.work_order_id: r for r in db.query(TechnicianRating).filter_by(customer_id=cust.id).all()}

    invoices: list[dict] = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(
                f"{settings.FINANCE_API_URL}/api/v1/internal/invoices-by-customer/{cust.customer_code}",
                headers={"X-TelcoNusa-Service-Key": settings.HMAC_WEBHOOK_SECRET},
            )
            if r.status_code == 200:
                invoices = r.json()
    except Exception:
        pass

    return {
        "customer": {
            "customer_code": cust.customer_code,
            "full_name": cust.full_name,
            "email": cust.email,
            "whatsapp_number": cust.whatsapp_number,
            "segment": cust.segment,
        },
        "addresses": [
            {
                "address_code": a.address_code,
                "label": a.label,
                "install_address": a.install_address,
                "city_code": a.city_code,
                "postal_code": a.postal_code,
                "site_condition_notes": a.site_condition_notes,
            }
            for a in addresses
        ],
        "subscriptions": [
            {
                "subscription_code": s.subscription_code,
                "sku": s.sku,
                "monthly_price": s.monthly_price,
                "status": s.status,
                "install_address": addr_map[s.install_address_id].install_address if s.install_address_id in addr_map else "-",
            }
            for s in subs
        ],
        "orders": [
            {
                "order_no": o.order_no,
                "sku": o.sku,
                "subtotal": o.subtotal,
                "referral_code": o.referral_code,
                "status": o.status,
                "install_address": addr_map[o.install_address_id].install_address if o.install_address_id in addr_map else "-",
            }
            for o in orders
        ],
        "work_orders": [
            {
                "id": w.id,
                "work_order_code": w.work_order_code,
                "order_no": order_map[w.order_id].order_no if w.order_id in order_map else "-",
                "order_status": order_map[w.order_id].status if w.order_id in order_map else "-",
                "sku": order_map[w.order_id].sku if w.order_id in order_map else "-",
                "technician_employee_id": w.technician_employee_id,
                "installation_status": w.installation_status,
                "install_address": addr_map[w.install_address_id].install_address if w.install_address_id in addr_map else "-",
                "speedtest_mbps": float(w.speedtest_mbps) if w.speedtest_mbps else None,
                "rating_score": ratings[w.id].rating_score if w.id in ratings else None,
                "rating_comment": ratings[w.id].rating_comment if w.id in ratings else None,
            }
            for w in wos
        ],
        "tickets": [
            {
                "ticket_code": t.ticket_code,
                "priority": t.priority,
                "subject": t.subject,
                "description": t.description,
                "status": t.status,
            }
            for t in tickets
        ],
        "invoices": invoices,
    }


@app.post("/api/v1/tickets", status_code=201)
def create_ticket(
    body: TicketCreateRequest,
    user: dict = Depends(require_roles("CUSTOMER", *CRM_STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    target_code = user.get("sub") if user.get("role") == "CUSTOMER" else (body.customer_code or "CUS-000456")
    cust = db.query(Customer).filter_by(customer_code=target_code).first() or db.query(Customer).first()
    if not cust:
        raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan")
    t_code = _next_ticket_code(db)
    t = Ticket(
        ticket_code=t_code,
        customer_id=cust.id,
        priority=body.priority,
        subject=body.subject.strip()[:160],
        description=body.description.strip(),
        status="OPEN",
    )
    db.add(t)
    db.commit()
    return {"ticket_code": t.ticket_code, "status": t.status, "priority": t.priority}


@app.post("/api/v1/work-orders/{work_order_id}/assign")
async def assign_work_order(
    work_order_id: str,
    body: WorkOrderAssignRequest,
    user: dict = Depends(require_roles("CRM_MANAGER", "CS_AGENT", "DIRECTOR")),
    db: Session = Depends(get_db),
):
    wo = db.query(WorkOrder).filter_by(id=work_order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order tidak ditemukan")
    wo.technician_employee_id = body.technician_employee_id
    wo.installation_status = "IN_PROGRESS"
    db.commit()
    await publish_event("workorder.assigned", "crm", wo.work_order_code, {
        "work_order_code": wo.work_order_code,
        "technician_employee_id": body.technician_employee_id,
    })
    return {
        "work_order_code": wo.work_order_code,
        "technician_employee_id": wo.technician_employee_id,
        "installation_status": wo.installation_status,
    }


@app.post("/api/v1/work-orders/{work_order_id}/complete")
async def update_work_order(
    work_order_id: str,
    body: WorkOrderUpdateRequest,
    user: dict = Depends(require_roles("TECHNICIAN", "CRM_MANAGER", "DIRECTOR")),
    db: Session = Depends(get_db),
):
    wo = db.query(WorkOrder).filter_by(id=work_order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order tidak ditemukan")
    wo.installation_status = body.installation_status
    wo.ont_serial_number = body.ont_serial_number or wo.ont_serial_number
    wo.cable_used_meters = body.cable_used_meters if body.cable_used_meters is not None else wo.cable_used_meters
    wo.signal_dbm = body.signal_dbm if body.signal_dbm is not None else wo.signal_dbm
    wo.speedtest_mbps = body.speedtest_mbps if body.speedtest_mbps is not None else wo.speedtest_mbps
    wo.site_condition_notes = body.site_condition_notes or wo.site_condition_notes
    if wo.install_address_id and body.site_condition_notes:
        addr = db.query(CustomerInstallAddress).filter_by(id=wo.install_address_id).first()
        if addr:
            addr.site_condition_notes = body.site_condition_notes
    if body.installation_status == "COMPLETED":
        order = db.query(Order).filter_by(id=wo.order_id).first()
        if order:
            order.status = "COMPLETED"
    db.commit()

    if body.installation_status == "COMPLETED":
        await publish_event("kit.reconciled", "crm", wo.work_order_code, {
            "work_order_code": wo.work_order_code,
            "ont_serial_number": wo.ont_serial_number,
            "cable_used_meters": wo.cable_used_meters or 25,
        })
    return {"work_order_code": wo.work_order_code, "installation_status": wo.installation_status}


@app.post("/api/v1/ratings", status_code=201)
async def submit_technician_rating(
    body: TechnicianRatingRequest,
    user: dict = Depends(require_roles("CUSTOMER", *CRM_STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    wo = db.query(WorkOrder).filter_by(id=body.work_order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order tidak ditemukan")
    existing = db.query(TechnicianRating).filter_by(work_order_id=wo.id).first()
    if existing:
        existing.rating_score = body.rating_score
        existing.rating_comment = body.rating_comment
        db.commit()
        rating = existing
    else:
        order = db.query(Order).filter_by(id=wo.order_id).first()
        rating = TechnicianRating(
            work_order_id=wo.id,
            customer_id=order.customer_id,
            technician_employee_id=wo.technician_employee_id or "EMP-0042",
            rating_score=body.rating_score,
            rating_comment=body.rating_comment,
        )
        db.add(rating)
        db.commit()

    await publish_event("technician.rated", "crm", wo.work_order_code, {
        "work_order_code": wo.work_order_code,
        "technician_employee_id": rating.technician_employee_id,
        "rating_score": body.rating_score,
        "rating_comment": body.rating_comment,
    })
    return {"status": "recorded", "rating_score": body.rating_score}


@app.get("/api/v1/dashboard/summary")
def crm_dashboard_summary(
    user: dict = Depends(require_roles(*CRM_STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(25).all()
    wos = db.query(WorkOrder).order_by(WorkOrder.created_at.desc()).limit(25).all()
    tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).limit(25).all()
    ratings = db.query(TechnicianRating).all()
    campaigns = db.query(Campaign).all()
    customers = {c.id: c for c in db.query(Customer).all()}
    addresses = {a.id: a for a in db.query(CustomerInstallAddress).all()}
    orders_map = {o.id: o for o in orders}
    ratings_by_wo = {r.work_order_id: r for r in ratings}

    return {
        "kpis": {
            "total_customers": db.query(Customer).count(),
            "active_subscriptions": db.query(Subscription).filter_by(status="ACTIVE").count(),
            "pending_work_orders": db.query(WorkOrder).filter(WorkOrder.installation_status != "COMPLETED").count(),
            "open_tickets": db.query(Ticket).filter(Ticket.status != "CLOSED").count(),
            "avg_technician_rating": round(sum(r.rating_score for r in ratings) / len(ratings), 2) if ratings else 0,
        },
        "campaigns": [
            {"campaign_code": c.campaign_code, "name": c.name, "channel": c.channel, "is_active": c.is_active}
            for c in campaigns
        ],
        "orders": [
            {
                "id": o.id,
                "order_no": o.order_no,
                "customer_code": customers[o.customer_id].customer_code if o.customer_id in customers else "-",
                "customer_name": customers[o.customer_id].full_name if o.customer_id in customers else "-",
                "city_code": addresses[o.install_address_id].city_code if o.install_address_id in addresses else "BDG",
                "install_address": addresses[o.install_address_id].install_address if o.install_address_id in addresses else "-",
                "sku": o.sku,
                "business_line": o.business_line,
                "referral_code": o.referral_code,
                "subtotal": o.subtotal,
                "status": o.status,
            }
            for o in orders
        ],
        "work_orders": [
            {
                "id": w.id,
                "work_order_code": w.work_order_code,
                "order_no": orders_map[w.order_id].order_no if w.order_id in orders_map else "-",
                "sku": orders_map[w.order_id].sku if w.order_id in orders_map else "HOME-50",
                "customer_name": customers[orders_map[w.order_id].customer_id].full_name if w.order_id in orders_map and orders_map[w.order_id].customer_id in customers else "-",
                "technician_employee_id": w.technician_employee_id,
                "installation_status": w.installation_status,
                "city_code": addresses[w.install_address_id].city_code if w.install_address_id in addresses else "BDG",
                "install_address": addresses[w.install_address_id].install_address if w.install_address_id in addresses else "-",
                "ont_serial_number": w.ont_serial_number,
                "cable_used_meters": w.cable_used_meters,
                "signal_dbm": float(w.signal_dbm) if w.signal_dbm else None,
                "speedtest_mbps": float(w.speedtest_mbps) if w.speedtest_mbps else None,
                "site_condition_notes": w.site_condition_notes,
                "rating_score": ratings_by_wo[w.id].rating_score if w.id in ratings_by_wo else None,
            }
            for w in wos
        ],
        "tickets": [
            {
                "ticket_code": t.ticket_code,
                "customer_code": customers[t.customer_id].customer_code if t.customer_id in customers else "-",
                "customer_name": customers[t.customer_id].full_name if t.customer_id in customers else "-",
                "customer_email": customers[t.customer_id].email if t.customer_id in customers else "-",
                "priority": t.priority,
                "subject": t.subject,
                "description": t.description,
                "status": t.status,
                "assigned_technician_id": t.assigned_technician_id,
            }
            for t in tickets
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
    if event_type == "invoice.paid":
        order = db.query(Order).filter_by(order_no=data.get("order_no")).first()
        if order:
            order.status = "PAID"
    elif event_type == "invoice.issued":
        order = db.query(Order).filter_by(order_no=data.get("order_no")).first()
        if order and order.status == "CONFIRMED":
            order.status = "AWAITING_PAYMENT"

    db.add(ProcessedEvent(event_id=event_id, event_type=event_type or "unknown"))
    db.commit()
    return {"status": "processed", "event_id": event_id}
