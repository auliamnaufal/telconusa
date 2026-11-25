"""Initial HRM schema (Blueprint + Notulen PDF)

Revision ID: 0001_initial_hrm
Revises:
Create Date: 2026-11-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_hrm"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("code", sa.String(16), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("cost_center_code", sa.String(16), nullable=False),
    )
    op.create_table(
        "employees",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("employee_code", sa.String(20), nullable=False, unique=True),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(120), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("department_code", sa.String(16), sa.ForeignKey("departments.code"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("city_code", sa.String(10), nullable=False, server_default="JKT"),
        sa.Column("shift_name", sa.String(24), nullable=False, server_default="OFFICE"),
        sa.Column("base_salary", sa.BigInteger, nullable=False),
        sa.Column("allowance", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("ptkp_status", sa.String(10), nullable=False, server_default="TK/0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("manager_code", sa.String(20), nullable=True),
        sa.Column("is_available", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("kpi_score", sa.Numeric(5, 2), nullable=False, server_default="85.00"),
    )
    op.create_table(
        "referral_codes",
        sa.Column("code", sa.String(32), primary_key=True),
        sa.Column("employee_code", sa.String(20), sa.ForeignKey("employees.employee_code"), nullable=False),
        sa.Column("total_uses", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_kpi_points", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "referral_usages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("referral_code", sa.String(32), sa.ForeignKey("referral_codes.code"), nullable=False),
        sa.Column("order_no", sa.String(24), nullable=False, unique=True),
        sa.Column("monthly_price", sa.BigInteger, nullable=False),
        sa.Column("incentive_amount", sa.BigInteger, nullable=False),
        sa.Column("points_awarded", sa.Integer, nullable=False, server_default="10"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "technician_rating_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("work_order_code", sa.String(20), nullable=False, unique=True),
        sa.Column("technician_employee_id", sa.String(20), sa.ForeignKey("employees.employee_code"), nullable=False),
        sa.Column("rating_score", sa.Integer, nullable=False),
        sa.Column("rating_comment", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "attendances",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("employee_code", sa.String(20), sa.ForeignKey("employees.employee_code"), nullable=False),
        sa.Column("attendance_date", sa.Date, nullable=False),
        sa.Column("check_in_time", sa.String(10), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PRESENT"),
        sa.Column("gps_location", sa.String(80), nullable=True),
    )
    op.create_table(
        "leave_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("employee_code", sa.String(20), sa.ForeignKey("employees.employee_code"), nullable=False),
        sa.Column("leave_type", sa.String(20), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
    )
    op.create_table(
        "job_requisitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("req_code", sa.String(20), nullable=False, unique=True),
        sa.Column("department_code", sa.String(16), nullable=False),
        sa.Column("position_title", sa.String(100), nullable=False),
        sa.Column("headcount", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),
    )
    op.create_table(
        "payroll_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("payroll_period", sa.String(7), nullable=False, unique=True),
        sa.Column("total_gross", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("total_bpjs_company", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("total_pph21", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("total_net", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("total_company_cost", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("status", sa.String(24), nullable=False, server_default="CALCULATED"),
    )
    op.create_table(
        "payroll_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("payroll_run_id", sa.String(36), sa.ForeignKey("payroll_runs.id"), nullable=False),
        sa.Column("employee_code", sa.String(20), sa.ForeignKey("employees.employee_code"), nullable=False),
        sa.Column("base_salary", sa.BigInteger, nullable=False),
        sa.Column("allowance", sa.BigInteger, nullable=False),
        sa.Column("transport_meal", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("overtime_pay", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("incentive_amount", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("gross_salary", sa.BigInteger, nullable=False),
        sa.Column("bpjs_employee", sa.BigInteger, nullable=False),
        sa.Column("bpjs_company", sa.BigInteger, nullable=False),
        sa.Column("pph21_amount", sa.BigInteger, nullable=False),
        sa.Column("net_salary", sa.BigInteger, nullable=False),
    )
    op.create_table(
        "processed_events",
        sa.Column("event_id", sa.String(40), primary_key=True),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("processed_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("correlation_id", sa.String(40), nullable=False),
        sa.Column("payload_json", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="SENT"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table in [
        "outbox_events", "processed_events", "payroll_items", "payroll_runs",
        "job_requisitions", "leave_requests", "attendances", "technician_rating_logs",
        "referral_usages", "referral_codes", "employees", "departments",
    ]:
        op.drop_table(table)
