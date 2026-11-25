import uuid
from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Department(Base):
    __tablename__ = "departments"
    code = Column(String(16), primary_key=True)
    name = Column(String(80), nullable=False)
    cost_center_code = Column(String(16), nullable=False)


class Employee(Base):
    __tablename__ = "employees"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    employee_code = Column(String(20), nullable=False, unique=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    department_code = Column(String(16), ForeignKey("departments.code"), nullable=False)
    role = Column(String(32), nullable=False)
    city_code = Column(String(10), nullable=False, default="JKT")
    shift_name = Column(String(24), nullable=False, default="OFFICE")
    base_salary = Column(BigInteger, nullable=False)
    allowance = Column(BigInteger, nullable=False, default=0)
    ptkp_status = Column(String(10), nullable=False, default="TK/0")
    status = Column(String(20), nullable=False, default="ACTIVE")
    manager_code = Column(String(20), nullable=True)
    is_available = Column(Boolean, nullable=False, default=True)
    kpi_score = Column(Numeric(5, 2), nullable=False, default=85.00)


class ReferralCode(Base):
    __tablename__ = "referral_codes"
    code = Column(String(32), primary_key=True)
    employee_code = Column(String(20), ForeignKey("employees.employee_code"), nullable=False)
    total_uses = Column(Integer, nullable=False, default=0)
    total_kpi_points = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())


class ReferralUsage(Base):
    __tablename__ = "referral_usages"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    referral_code = Column(String(32), ForeignKey("referral_codes.code"), nullable=False)
    order_no = Column(String(24), nullable=False, unique=True)
    monthly_price = Column(BigInteger, nullable=False)
    incentive_amount = Column(BigInteger, nullable=False)
    points_awarded = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime, server_default=func.now())


class TechnicianRatingLog(Base):
    __tablename__ = "technician_rating_logs"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    work_order_code = Column(String(20), nullable=False, unique=True)
    technician_employee_id = Column(String(20), ForeignKey("employees.employee_code"), nullable=False)
    rating_score = Column(Integer, nullable=False)
    rating_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    employee_code = Column(String(20), ForeignKey("employees.employee_code"), nullable=False)
    attendance_date = Column(Date, nullable=False)
    check_in_time = Column(String(10), nullable=True)
    status = Column(String(20), nullable=False, default="PRESENT")
    gps_location = Column(String(80), nullable=True)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    employee_code = Column(String(20), ForeignKey("employees.employee_code"), nullable=False)
    leave_type = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")


class JobRequisition(Base):
    __tablename__ = "job_requisitions"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    req_code = Column(String(20), nullable=False, unique=True)
    department_code = Column(String(16), nullable=False)
    position_title = Column(String(100), nullable=False)
    headcount = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="OPEN")


class PayrollRun(Base):
    __tablename__ = "payroll_runs"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    payroll_period = Column(String(7), nullable=False, unique=True)
    total_gross = Column(BigInteger, nullable=False, default=0)
    total_bpjs_company = Column(BigInteger, nullable=False, default=0)
    total_pph21 = Column(BigInteger, nullable=False, default=0)
    total_net = Column(BigInteger, nullable=False, default=0)
    total_company_cost = Column(BigInteger, nullable=False, default=0)
    status = Column(String(24), nullable=False, default="CALCULATED")


class PayrollItem(Base):
    __tablename__ = "payroll_items"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    payroll_run_id = Column(String(36), ForeignKey("payroll_runs.id"), nullable=False)
    employee_code = Column(String(20), ForeignKey("employees.employee_code"), nullable=False)
    base_salary = Column(BigInteger, nullable=False)
    allowance = Column(BigInteger, nullable=False)
    transport_meal = Column(BigInteger, nullable=False, default=0)
    overtime_pay = Column(BigInteger, nullable=False, default=0)
    incentive_amount = Column(BigInteger, nullable=False, default=0)
    gross_salary = Column(BigInteger, nullable=False)
    bpjs_employee = Column(BigInteger, nullable=False)
    bpjs_company = Column(BigInteger, nullable=False)
    pph21_amount = Column(BigInteger, nullable=False)
    net_salary = Column(BigInteger, nullable=False)


class ProcessedEvent(Base):
    __tablename__ = "processed_events"
    event_id = Column(String(40), primary_key=True)
    event_type = Column(String(60), nullable=False)
    processed_at = Column(DateTime, server_default=func.now())


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    event_type = Column(String(60), nullable=False)
    correlation_id = Column(String(40), nullable=False)
    payload_json = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="SENT")
    created_at = Column(DateTime, server_default=func.now())
