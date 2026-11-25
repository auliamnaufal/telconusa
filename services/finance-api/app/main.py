import hmac
import json
import uuid
from datetime import date

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.auth import FINANCE_ROLES, require_roles
from shared.config import settings
from shared.events import publish_event, verify_signature
from shared.schemas import HealthResponse, now_wib_iso

from app.database import get_db
from app.models import (
    Account,
    Budget,
    FiscalPeriod,
    Invoice,
    JournalEntry,
    JournalLine,
    OutboxEvent,
    ProcessedEvent,
    VendorBill,
)
from app.posting_engine import post_journal

app = FastAPI(
    title="TelcoNusa Finance API",
    version="2.0.0",
    description="Divisi Finance (Kelompok 3) — AR/Invoice & VA, AP Three-Way Match, Posting Engine GL, Periode Fiskal, Anggaran, & Laporan.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BudgetCheckRequest(BaseModel):
    cost_center_code: str
    amount: int
    fiscal_year: int = 2026


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(service="finance-api", transport=settings.EVENT_TRANSPORT, timestamp=now_wib_iso())


@app.post("/api/v1/budgets/check")
def check_budget(body: BudgetCheckRequest, db: Session = Depends(get_db)):
    b = db.query(Budget).filter_by(cost_center_code=body.cost_center_code, fiscal_year=body.fiscal_year).first()
    if not b:
        raise HTTPException(status_code=422, detail="Cost center tidak ditemukan")
    remaining = b.allocated_amount - b.committed_amount - b.realized_amount
    return {
        "cost_center_code": b.cost_center_code,
        "requested": body.amount,
        "remaining": remaining,
        "approved": remaining >= body.amount,
    }


@app.get("/api/v1/internal/invoices-by-customer/{customer_code}")
def get_customer_invoices_internal(
    customer_code: str,
    x_telconusa_service_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not x_telconusa_service_key or not hmac.compare_digest(x_telconusa_service_key, settings.HMAC_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid inter-service key")
    invs = db.query(Invoice).filter_by(customer_code=customer_code).order_by(Invoice.created_at.desc()).all()
    return [
        {
            "invoice_no": i.invoice_no,
            "order_no": i.order_no,
            "subtotal": int(i.subtotal),
            "tax_amount": int(i.tax_amount),
            "total": int(i.total),
            "paid_amount": int(i.paid_amount),
            "virtual_account": i.virtual_account,
            "status": i.status,
        }
        for i in invs
    ]


@app.post("/api/v1/periods/{period_code}/toggle")
def toggle_period(
    period_code: str,
    user: dict = Depends(require_roles("FINANCE_MANAGER", "DIRECTOR")),
    db: Session = Depends(get_db),
):
    fp = db.query(FiscalPeriod).filter_by(period_code=period_code).first()
    if not fp:
        raise HTTPException(status_code=404, detail="Periode fiskal tidak ditemukan")
    fp.status = "OPEN" if fp.status == "LOCKED" else "LOCKED"
    db.commit()
    return {"period_code": fp.period_code, "status": fp.status}


@app.post("/api/v1/vendor-bills/{bill_no}/pay")
async def pay_vendor_bill(
    bill_no: str,
    user: dict = Depends(require_roles(*FINANCE_ROLES)),
    db: Session = Depends(get_db),
):
    bill = db.query(VendorBill).filter_by(bill_no=bill_no).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Tagihan vendor tidak ditemukan")
    if bill.status == "PAID":
        return {"bill_no": bill.bill_no, "status": "PAID"}
    if bill.match_status != "MATCHED":
        raise HTTPException(status_code=409, detail="Tagihan belum lulus Three-Way Match")

    bill.status = "PAID"
    post_journal(
        db,
        entry_date=date.today(),
        source_type="VENDOR_PAYMENT",
        source_id=bill.bill_no,
        rule_code="AP-PAY",
        description=f"Pembayaran vendor {bill.vendor_code} untuk {bill.po_no}",
        lines=[("2100", int(bill.total), 0), ("1100", 0, int(bill.total))],
    )
    payload = {"bill_no": bill.bill_no, "po_no": bill.po_no, "amount": int(bill.total)}
    db.add(OutboxEvent(event_type="vendor.paid", correlation_id=bill.po_no, payload_json=json.dumps(payload)))
    db.commit()
    await publish_event("vendor.paid", "finance", bill.po_no, payload)
    return {"bill_no": bill.bill_no, "status": "PAID", "journal_posted": "AP-PAY"}


@app.post("/api/v1/invoices/{invoice_no}/pay")
async def simulate_va_payment(
    invoice_no: str,
    user: dict = Depends(require_roles(*FINANCE_ROLES)),
    db: Session = Depends(get_db),
):
    inv = db.query(Invoice).filter_by(invoice_no=invoice_no).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice tidak ditemukan")
    if inv.status == "PAID":
        return {"invoice_no": inv.invoice_no, "status": "PAID", "message": "Sudah lunas"}

    inv.paid_amount = inv.total
    inv.status = "PAID"

    post_journal(
        db,
        entry_date=date.today(),
        source_type="PAYMENT",
        source_id=inv.invoice_no,
        rule_code="AR-PAY",
        description=f"Pembayaran VA {inv.virtual_account} ({inv.customer_name})",
        lines=[("1100", int(inv.total), 0), ("1200", 0, int(inv.total))],
        business_line=inv.business_line,
    )

    paid_payload = {
        "invoice_no": inv.invoice_no,
        "order_no": inv.order_no,
        "amount": int(inv.total),
        "paid_at": now_wib_iso(),
    }
    db.add(OutboxEvent(event_type="invoice.paid", correlation_id=inv.order_no or inv.invoice_no, payload_json=json.dumps(paid_payload)))

    if inv.referral_code and inv.monthly_price > 0:
        commission = round(int(inv.monthly_price) * settings.REFERRAL_INCENTIVE_RATE)
        post_journal(
            db,
            entry_date=date.today(),
            source_type="COMMISSION",
            source_id=inv.invoice_no,
            rule_code="COM-FIN",
            description=f"Insentif referral 10% ({inv.referral_code}) untuk {inv.order_no}",
            lines=[("6120", commission, 0), ("2600", 0, commission)],
            business_line=inv.business_line,
        )
        comm_payload = {
            "order_no": inv.order_no,
            "referral_code": inv.referral_code,
            "monthly_price": int(inv.monthly_price),
            "commission_amount": commission,
        }
        db.add(OutboxEvent(event_type="commission.finalized", correlation_id=inv.order_no or inv.invoice_no, payload_json=json.dumps(comm_payload)))
        db.commit()
        await publish_event("commission.finalized", "finance", inv.order_no or inv.invoice_no, comm_payload)
    else:
        db.commit()

    await publish_event("invoice.paid", "finance", inv.order_no or inv.invoice_no, paid_payload)
    return {"invoice_no": inv.invoice_no, "status": "PAID", "journal_posted": "AR-PAY"}


@app.get("/api/v1/reports/trial-balance")
def trial_balance(
    user: dict = Depends(require_roles(*FINANCE_ROLES)),
    db: Session = Depends(get_db),
):
    return _compute_trial_balance(db)


def _compute_trial_balance(db: Session) -> dict:
    rows = (
        db.query(
            Account.code,
            Account.name,
            Account.account_type,
            func.coalesce(func.sum(JournalLine.debit), 0).label("debit"),
            func.coalesce(func.sum(JournalLine.credit), 0).label("credit"),
        )
        .outerjoin(JournalLine, Account.code == JournalLine.account_code)
        .group_by(Account.code, Account.name, Account.account_type)
        .order_by(Account.code)
        .all()
    )
    items = [
        {"account_code": r.code, "account_name": r.name, "account_type": r.account_type, "debit": int(r.debit), "credit": int(r.credit)}
        for r in rows if int(r.debit) > 0 or int(r.credit) > 0
    ]
    total_debit = sum(i["debit"] for i in items)
    total_credit = sum(i["credit"] for i in items)
    return {
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": total_debit == total_credit,
        "accounts": items,
    }


@app.get("/api/v1/dashboard/summary")
def finance_dashboard_summary(
    user: dict = Depends(require_roles(*FINANCE_ROLES)),
    db: Session = Depends(get_db),
):
    invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).limit(25).all()
    bills = db.query(VendorBill).order_by(VendorBill.created_at.desc()).limit(20).all()
    entries = db.query(JournalEntry).order_by(JournalEntry.created_at.desc()).limit(25).all()
    lines = db.query(JournalLine).all()
    accounts_map = {a.code: a.name for a in db.query(Account).all()}
    lines_by_je: dict[str, list[dict]] = {}
    for ln in lines:
        lines_by_je.setdefault(ln.journal_entry_id, []).append({
            "account_code": ln.account_code,
            "account_name": accounts_map.get(ln.account_code, ln.account_code),
            "debit": int(ln.debit),
            "credit": int(ln.credit),
        })

    budgets = db.query(Budget).all()
    periods = db.query(FiscalPeriod).order_by(FiscalPeriod.period_code.desc()).all()
    tb = _compute_trial_balance(db)

    total_revenue = sum(a["credit"] - a["debit"] for a in tb["accounts"] if a["account_type"] == "REVENUE")
    total_expense = sum(a["debit"] - a["credit"] for a in tb["accounts"] if a["account_type"] in ("EXPENSE", "COGS"))
    total_cash = sum(a["debit"] - a["credit"] for a in tb["accounts"] if a["account_code"] == "1100")
    total_ar = sum(int(i.total) - int(i.paid_amount) for i in invoices if i.status != "VOID")
    total_ap = sum(int(b.total) for b in bills if b.status != "PAID")

    unpaid_total = sum(int(i.total) - int(i.paid_amount) for i in invoices if i.status in ("ISSUED", "PARTIALLY_PAID"))
    overdue_total = sum(int(i.total) - int(i.paid_amount) for i in invoices if i.status == "OVERDUE")
    aging_buckets = [
        {"bucket": "Belum Jatuh Tempo (1%)", "amount": unpaid_total, "allowance_rate": 1},
        {"bucket": "1-30 Hari (5%)", "amount": overdue_total, "allowance_rate": 5},
        {"bucket": "31-60 Hari (20%)", "amount": 0, "allowance_rate": 20},
        {"bucket": "61-90 Hari (50%)", "amount": 0, "allowance_rate": 50},
        {"bucket": "> 90 Hari (100%)", "amount": 0, "allowance_rate": 100},
    ]

    return {
        "kpis": {
            "cash_balance_idr": total_cash,
            "total_revenue_idr": total_revenue,
            "total_expense_idr": total_expense,
            "net_profit_idr": total_revenue - total_expense,
            "outstanding_ar_idr": total_ar,
            "outstanding_ap_idr": total_ap,
            "total_journals": db.query(JournalEntry).count(),
            "trial_balance_balanced": tb["is_balanced"],
        },
        "invoices": [
            {
                "invoice_no": i.invoice_no,
                "order_no": i.order_no,
                "customer_code": i.customer_code,
                "customer_name": i.customer_name,
                "business_line": i.business_line,
                "billing_period": i.billing_period,
                "subtotal": i.subtotal,
                "tax_amount": i.tax_amount,
                "total": i.total,
                "paid_amount": i.paid_amount,
                "virtual_account": i.virtual_account,
                "referral_code": i.referral_code,
                "status": i.status,
            }
            for i in invoices
        ],
        "aging_buckets": aging_buckets,
        "vendor_bills": [
            {
                "bill_no": b.bill_no,
                "po_no": b.po_no,
                "vendor_code": b.vendor_code,
                "subtotal": b.subtotal,
                "tax_amount": b.tax_amount,
                "total": b.total,
                "match_status": b.match_status,
                "status": b.status,
            }
            for b in bills
        ],
        "journals": [
            {
                "journal_no": j.journal_no,
                "entry_date": j.entry_date.isoformat(),
                "period_code": j.period_code,
                "rule_code": j.rule_code,
                "source_type": j.source_type,
                "source_id": j.source_id,
                "description": j.description,
                "status": j.status,
                "lines": lines_by_je.get(j.id, []),
            }
            for j in entries
        ],
        "fiscal_periods": [{"period_code": p.period_code, "status": p.status} for p in periods],
        "budgets": [
            {
                "cost_center_code": b.cost_center_code,
                "fiscal_year": b.fiscal_year,
                "allocated_amount": b.allocated_amount,
                "committed_amount": b.committed_amount,
                "realized_amount": b.realized_amount,
            }
            for b in budgets
        ],
        "trial_balance": tb,
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

    if event_type == "order.confirmed":
        order_no = data.get("order_no")
        if order_no and not db.query(Invoice).filter_by(order_no=order_no).first():
            subtotal = int(data.get("subtotal", 0))
            tax_amount = round(subtotal * settings.PPN_RATE)
            total = subtotal + tax_amount
            seq = db.query(Invoice).count() + 1
            inv_no = f"INV-2026-{seq:06d}"
            va_no = f"8808{seq:09d}"

            inv = Invoice(
                invoice_no=inv_no,
                order_no=order_no,
                customer_code=data.get("customer_code", "CUS-000000"),
                customer_name=data.get("customer_name", "Pelanggan"),
                business_line=data.get("business_line", "HOME"),
                billing_period=date.today().strftime("%Y-%m"),
                subtotal=subtotal,
                tax_amount=tax_amount,
                total=total,
                virtual_account=va_no,
                referral_code=data.get("referral_code"),
                monthly_price=int(data.get("monthly_price", subtotal)),
                status="ISSUED",
            )
            db.add(inv)
            db.flush()

            post_journal(
                db,
                entry_date=date.today(),
                source_type="INVOICE",
                source_id=inv_no,
                rule_code="AR-INV",
                description=f"Invoice awal otomatis dari {order_no}",
                lines=[("1200", total, 0), ("2500", 0, subtotal), ("2200", 0, tax_amount)],
                business_line=inv.business_line,
            )

            issued_payload = {"invoice_no": inv_no, "order_no": order_no, "total": total, "virtual_account": va_no}
            db.add(OutboxEvent(event_type="invoice.issued", correlation_id=order_no, payload_json=json.dumps(issued_payload)))
            db.add(ProcessedEvent(event_id=event_id, event_type=event_type))
            db.commit()
            await publish_event("invoice.issued", "finance", order_no, issued_payload)
            return {"status": "processed", "invoice_no": inv_no}

    elif event_type == "payroll.approved":
        period = data.get("payroll_period", date.today().strftime("%Y-%m"))
        gross = int(data.get("total_gross", 0))
        bpjs_co = int(data.get("total_bpjs_company", 0))
        pph21 = int(data.get("total_pph21", 0))
        net = int(data.get("total_net", 0))
        bpjs_total = gross + bpjs_co - net - pph21
        if gross > 0:
            post_journal(
                db,
                entry_date=date.today(),
                source_type="PAYROLL",
                source_id=f"PAY-{period}",
                rule_code="PR-ACC",
                description=f"Beban gaji & BPJS periode {period}",
                lines=[
                    ("6100", gross, 0),
                    ("6110", bpjs_co, 0),
                    ("2110", 0, net),
                    ("2300", 0, pph21),
                    ("2400", 0, bpjs_total),
                ],
            )

    db.add(ProcessedEvent(event_id=event_id, event_type=event_type or "unknown"))
    db.commit()
    return {"status": "processed", "event_id": event_id}
