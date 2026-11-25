import json
import uuid
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.auth import (
    EMPLOYEE_ROLES,
    HR_ADMIN_ROLES,
    create_access_token,
    get_current_user,
    require_roles,
    verify_password,
)
from shared.config import settings
from shared.events import publish_event, verify_signature
from shared.schemas import HealthResponse, now_wib_iso

from app.database import get_db
from app.models import (
    Attendance,
    Department,
    Employee,
    JobRequisition,
    LeaveRequest,
    OutboxEvent,
    PayrollItem,
    PayrollRun,
    ProcessedEvent,
    ReferralCode,
    ReferralUsage,
    TechnicianRatingLog,
)

app = FastAPI(
    title="TelcoNusa HRM API",
    version="2.0.0",
    description="Divisi HRM — Single Employee SSO, Rekrutmen, Ketersediaan Teknisi, Kode Referral Marketing 10%, Rating Teknisi, & Payroll.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    email: str
    password: str


class CreateReferralRequest(BaseModel):
    employee_code: str
    custom_code: Optional[str] = None


class CheckInRequest(BaseModel):
    employee_code: Optional[str] = None
    gps_location: str = "Kantor Pusat Jakarta"


class LeaveCreateRequest(BaseModel):
    employee_code: Optional[str] = None
    leave_type: str = "ANNUAL"
    start_date: date
    end_date: date
    reason: str


class RequisitionCreateRequest(BaseModel):
    department_code: str
    position_title: str
    headcount: int = 1


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(service="hrm-api", transport=settings.EVENT_TRANSPORT, timestamp=now_wib_iso())


@app.post("/api/v1/auth/login")
def employee_login(body: LoginRequest, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter_by(email=body.email, status="ACTIVE").first()
    if not emp or not verify_password(body.password, emp.password_hash):
        raise HTTPException(status_code=401, detail="Email atau password karyawan salah")
    token = create_access_token({
        "sub": emp.employee_code,
        "role": emp.role,
        "name": emp.full_name,
        "email": emp.email,
        "department": emp.department_code,
        "city_code": emp.city_code,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "code": emp.employee_code,
            "name": emp.full_name,
            "email": emp.email,
            "role": emp.role,
            "department": emp.department_code,
            "city_code": emp.city_code,
        },
    }


@app.get("/api/v1/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    return {
        "user": {
            "code": user.get("sub"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
            "department": user.get("department"),
            "city_code": user.get("city_code"),
        }
    }


@app.get("/api/v1/employees/available")
def available_employees(role: str = "TECHNICIAN", city_code: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Employee).filter_by(role=role, status="ACTIVE", is_available=True)
    if city_code:
        q = q.filter_by(city_code=city_code.upper())
    return [
        {
            "employee_code": e.employee_code,
            "full_name": e.full_name,
            "city_code": e.city_code,
            "shift_name": e.shift_name,
            "kpi_score": float(e.kpi_score),
        }
        for e in q.all()
    ]


@app.patch("/api/v1/employees/{employee_code}/availability")
def toggle_availability(
    employee_code: str,
    user: dict = Depends(require_roles(*HR_ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    emp = db.query(Employee).filter_by(employee_code=employee_code).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    emp.is_available = not emp.is_available
    db.commit()
    return {"employee_code": emp.employee_code, "is_available": emp.is_available}


@app.get("/api/v1/referrals/{code}")
def get_referral(code: str, db: Session = Depends(get_db)):
    ref = db.query(ReferralCode).filter_by(code=code.upper(), is_active=True).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Kode referral tidak ditemukan atau tidak aktif")
    emp = db.query(Employee).filter_by(employee_code=ref.employee_code).first()
    return {
        "code": ref.code,
        "employee_code": ref.employee_code,
        "employee_name": emp.full_name if emp else ref.employee_code,
        "total_uses": ref.total_uses,
        "total_kpi_points": ref.total_kpi_points,
    }


@app.post("/api/v1/referrals", status_code=201)
def create_referral(
    body: CreateReferralRequest,
    user: dict = Depends(require_roles(*HR_ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    emp = db.query(Employee).filter_by(employee_code=body.employee_code).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    code = (body.custom_code or f"REF-{emp.employee_code.replace('-', '')}").upper()
    if db.query(ReferralCode).filter_by(code=code).first():
        raise HTTPException(status_code=409, detail="Kode referral sudah terdaftar")
    ref = ReferralCode(code=code, employee_code=emp.employee_code)
    db.add(ref)
    db.commit()
    return {"code": ref.code, "employee_code": ref.employee_code}


@app.post("/api/v1/requisitions", status_code=201)
def create_requisition(
    body: RequisitionCreateRequest,
    user: dict = Depends(require_roles(*EMPLOYEE_ROLES)),
    db: Session = Depends(get_db),
):
    req_code = f"REQ-2026-{db.query(JobRequisition).count() + 1:03d}"
    req = JobRequisition(
        req_code=req_code,
        department_code=body.department_code,
        position_title=body.position_title,
        headcount=body.headcount,
        status="OPEN",
    )
    db.add(req)
    db.commit()
    return {"req_code": req.req_code, "status": req.status}


@app.post("/api/v1/attendance/check-in", status_code=201)
def check_in(
    body: CheckInRequest,
    user: dict = Depends(require_roles(*EMPLOYEE_ROLES)),
    db: Session = Depends(get_db),
):
    target_emp = body.employee_code if (body.employee_code and user.get("role") in HR_ADMIN_ROLES) else user.get("sub")
    att = Attendance(
        employee_code=target_emp,
        attendance_date=date.today(),
        check_in_time=now_wib_iso()[11:16],
        status="PRESENT",
        gps_location=body.gps_location,
    )
    db.add(att)
    db.commit()
    return {"employee_code": target_emp, "status": "PRESENT", "check_in_time": att.check_in_time, "gps_location": att.gps_location}


@app.post("/api/v1/leaves", status_code=201)
def request_leave(
    body: LeaveCreateRequest,
    user: dict = Depends(require_roles(*EMPLOYEE_ROLES)),
    db: Session = Depends(get_db),
):
    target_emp = body.employee_code if (body.employee_code and user.get("role") in HR_ADMIN_ROLES) else user.get("sub")
    lv = LeaveRequest(
        employee_code=target_emp,
        leave_type=body.leave_type,
        start_date=body.start_date,
        end_date=body.end_date,
        reason=body.reason,
    )
    db.add(lv)
    db.commit()
    return {"id": lv.id, "employee_code": target_emp, "status": lv.status}


@app.post("/api/v1/payroll-runs/{period}/approve-hr")
async def approve_payroll_hr(
    period: str,
    user: dict = Depends(require_roles("HR_MANAGER", "DIRECTOR")),
    db: Session = Depends(get_db),
):
    pr = db.query(PayrollRun).filter_by(payroll_period=period).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Periode payroll tidak ditemukan")
    pr.status = "HR_APPROVED"
    payload = {
        "payroll_period": pr.payroll_period,
        "total_gross": pr.total_gross,
        "total_bpjs_company": pr.total_bpjs_company,
        "total_pph21": pr.total_pph21,
        "total_net": pr.total_net,
        "total_company_cost": pr.total_company_cost,
    }
    db.add(OutboxEvent(event_type="payroll.approved", correlation_id=f"PAY-{period}", payload_json=json.dumps(payload)))
    db.commit()
    await publish_event("payroll.approved", "hrm", f"PAY-{period}", payload)
    return {"payroll_period": period, "status": pr.status, "event_published": "payroll.approved"}


@app.get("/api/v1/employees/{employee_code}/self-service")
def employee_self_service(
    employee_code: str,
    user: dict = Depends(require_roles(*EMPLOYEE_ROLES)),
    db: Session = Depends(get_db),
):
    # Critical RBAC guard: employee can ONLY view their own private data unless HR Admin/Director
    if user.get("sub") != employee_code and user.get("role") not in HR_ADMIN_ROLES:
        raise HTTPException(
            status_code=403,
            detail=f"Tidak berhak mengakses slip gaji & data pribadi milik {employee_code}",
        )

    emp = db.query(Employee).filter_by(employee_code=employee_code).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")

    atts = db.query(Attendance).filter_by(employee_code=emp.employee_code).order_by(Attendance.attendance_date.desc()).limit(10).all()
    leaves = db.query(LeaveRequest).filter_by(employee_code=emp.employee_code).all()
    slips = db.query(PayrollItem).filter_by(employee_code=emp.employee_code).all()

    # For employees without an explicit PayrollItem row yet, render their contractual baseline slip preview
    slip_list = [
        {
            "period": "2026-11",
            "base_salary": s.base_salary,
            "allowance": s.allowance,
            "transport_meal": s.transport_meal,
            "overtime_pay": s.overtime_pay,
            "incentive_amount": s.incentive_amount,
            "gross_salary": s.gross_salary,
            "bpjs_employee": s.bpjs_employee,
            "pph21_amount": s.pph21_amount,
            "net_salary": s.net_salary,
        }
        for s in slips
    ]
    if not slip_list:
        fixed = int(emp.base_salary) + int(emp.allowance)
        bpjs_emp = round(fixed * 0.04)
        pph21 = round(fixed * 0.015)
        slip_list = [
            {
                "period": "2026-11",
                "base_salary": int(emp.base_salary),
                "allowance": int(emp.allowance),
                "transport_meal": 500000,
                "overtime_pay": 0,
                "incentive_amount": 0,
                "gross_salary": fixed + 500000,
                "bpjs_employee": bpjs_emp,
                "pph21_amount": pph21,
                "net_salary": fixed + 500000 - bpjs_emp - pph21,
            }
        ]

    return {
        "profile": {
            "employee_code": emp.employee_code,
            "full_name": emp.full_name,
            "email": emp.email,
            "role": emp.role,
            "department_code": emp.department_code,
            "city_code": emp.city_code,
            "shift_name": emp.shift_name,
            "ptkp_status": emp.ptkp_status,
            "base_salary": emp.base_salary,
            "allowance": emp.allowance,
            "kpi_score": float(emp.kpi_score),
        },
        "attendances": [
            {"date": a.attendance_date.isoformat(), "check_in": a.check_in_time, "status": a.status, "gps": a.gps_location}
            for a in atts
        ],
        "leaves": [
            {"id": l.id, "leave_type": l.leave_type, "start_date": l.start_date.isoformat(), "end_date": l.end_date.isoformat(), "reason": l.reason, "status": l.status}
            for l in leaves
        ],
        "slips": slip_list,
    }


@app.get("/api/v1/dashboard/summary")
def hrm_dashboard_summary(
    user: dict = Depends(require_roles(*HR_ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    employees = db.query(Employee).all()
    emp_map = {e.employee_code: e for e in employees}
    referrals = db.query(ReferralCode).all()
    ref_usages = db.query(ReferralUsage).all()
    ratings = db.query(TechnicianRatingLog).order_by(TechnicianRatingLog.created_at.desc()).limit(15).all()
    payrolls = db.query(PayrollRun).order_by(PayrollRun.payroll_period.desc()).limit(6).all()
    payroll_items = db.query(PayrollItem).all()
    reqs = db.query(JobRequisition).all()
    leaves = db.query(LeaveRequest).all()

    return {
        "kpis": {
            "total_employees": len(employees),
            "available_technicians": sum(1 for e in employees if e.role == "TECHNICIAN" and e.is_available),
            "active_referral_codes": len(referrals),
            "open_requisitions": sum(1 for r in reqs if r.status == "OPEN"),
            "latest_payroll_cost": payrolls[0].total_company_cost if payrolls else 0,
        },
        "employees": [
            {
                "employee_code": e.employee_code,
                "full_name": e.full_name,
                "email": e.email,
                "role": e.role,
                "department_code": e.department_code,
                "city_code": e.city_code,
                "shift_name": e.shift_name,
                "is_available": e.is_available,
                "kpi_score": float(e.kpi_score),
                "base_salary": e.base_salary,
                "allowance": e.allowance,
            }
            for e in employees
        ],
        "referrals": [
            {
                "code": r.code,
                "employee_code": r.employee_code,
                "employee_name": emp_map[r.employee_code].full_name if r.employee_code in emp_map else r.employee_code,
                "total_uses": r.total_uses,
                "total_kpi_points": r.total_kpi_points,
                "total_incentive": sum(u.incentive_amount for u in ref_usages if u.referral_code == r.code),
            }
            for r in referrals
        ],
        "technician_ratings": [
            {
                "work_order_code": rt.work_order_code,
                "technician_employee_id": rt.technician_employee_id,
                "technician_name": emp_map[rt.technician_employee_id].full_name if rt.technician_employee_id in emp_map else rt.technician_employee_id,
                "rating_score": rt.rating_score,
                "rating_comment": rt.rating_comment,
            }
            for rt in ratings
        ],
        "requisitions": [
            {"req_code": r.req_code, "department_code": r.department_code, "position_title": r.position_title, "headcount": r.headcount, "status": r.status}
            for r in reqs
        ],
        "leaves": [
            {"id": l.id, "employee_code": l.employee_code, "leave_type": l.leave_type, "start_date": l.start_date.isoformat(), "end_date": l.end_date.isoformat(), "reason": l.reason, "status": l.status}
            for l in leaves
        ],
        "payroll_runs": [
            {
                "payroll_period": p.payroll_period,
                "total_gross": p.total_gross,
                "total_bpjs_company": p.total_bpjs_company,
                "total_pph21": p.total_pph21,
                "total_net": p.total_net,
                "total_company_cost": p.total_company_cost,
                "status": p.status,
            }
            for p in payrolls
        ],
        "payroll_items": [
            {
                "employee_code": pi.employee_code,
                "employee_name": emp_map[pi.employee_code].full_name if pi.employee_code in emp_map else pi.employee_code,
                "base_salary": pi.base_salary,
                "allowance": pi.allowance,
                "transport_meal": pi.transport_meal,
                "overtime_pay": pi.overtime_pay,
                "incentive_amount": pi.incentive_amount,
                "gross_salary": pi.gross_salary,
                "bpjs_employee": pi.bpjs_employee,
                "bpjs_company": pi.bpjs_company,
                "pph21_amount": pi.pph21_amount,
                "net_salary": pi.net_salary,
            }
            for pi in payroll_items
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

    if event_type == "technician.rated":
        existing = db.query(TechnicianRatingLog).filter_by(work_order_code=data.get("work_order_code")).first()
        if existing:
            existing.rating_score = int(data["rating_score"])
            existing.rating_comment = data.get("rating_comment")
        else:
            db.add(TechnicianRatingLog(
                work_order_code=data["work_order_code"],
                technician_employee_id=data["technician_employee_id"],
                rating_score=int(data["rating_score"]),
                rating_comment=data.get("rating_comment"),
            ))
    elif event_type in ("referral.used", "commission.finalized"):
        ref_code = data.get("referral_code")
        order_no = data.get("order_no")
        monthly_price = int(data.get("monthly_price", 0))
        if ref_code and order_no and not db.query(ReferralUsage).filter_by(order_no=order_no).first():
            ref = db.query(ReferralCode).filter_by(code=ref_code).first()
            if ref:
                incentive = round(monthly_price * settings.REFERRAL_INCENTIVE_RATE)
                db.add(ReferralUsage(
                    referral_code=ref_code,
                    order_no=order_no,
                    monthly_price=monthly_price,
                    incentive_amount=incentive,
                    points_awarded=settings.REFERRAL_KPI_POINTS,
                ))
                ref.total_uses += 1
                ref.total_kpi_points += settings.REFERRAL_KPI_POINTS
    elif event_type == "payroll.paid":
        pr = db.query(PayrollRun).filter_by(payroll_period=data.get("payroll_period")).first()
        if pr:
            pr.status = "PAID"

    db.add(ProcessedEvent(event_id=event_id, event_type=event_type or "unknown"))
    db.commit()
    return {"status": "processed", "event_id": event_id}
