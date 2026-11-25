"""Initial Finance schema (Proposal Finance Kelompok 3 + Blueprint)

Revision ID: 0001_initial_finance
Revises:
Create Date: 2026-11-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_finance"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("code", sa.String(10), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("account_type", sa.String(24), nullable=False),
        sa.Column("normal_balance", sa.String(10), nullable=False),
    )
    op.create_table(
        "fiscal_periods",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("period_code", sa.String(7), nullable=False, unique=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="OPEN"),
    )
    op.create_table(
        "budgets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cost_center_code", sa.String(16), nullable=False),
        sa.Column("fiscal_year", sa.Integer, nullable=False),
        sa.Column("allocated_amount", sa.BigInteger, nullable=False),
        sa.Column("committed_amount", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("realized_amount", sa.BigInteger, nullable=False, server_default="0"),
    )
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("invoice_no", sa.String(24), nullable=False, unique=True),
        sa.Column("order_no", sa.String(24), nullable=True, unique=True),
        sa.Column("customer_code", sa.String(20), nullable=False),
        sa.Column("customer_name", sa.String(120), nullable=False),
        sa.Column("business_line", sa.String(15), nullable=False),
        sa.Column("billing_period", sa.String(7), nullable=False),
        sa.Column("subtotal", sa.BigInteger, nullable=False),
        sa.Column("discount", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.BigInteger, nullable=False),
        sa.Column("total", sa.BigInteger, nullable=False),
        sa.Column("paid_amount", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("virtual_account", sa.String(24), nullable=False),
        sa.Column("referral_code", sa.String(32), nullable=True),
        sa.Column("monthly_price", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ISSUED"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "vendor_bills",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("bill_no", sa.String(24), nullable=False, unique=True),
        sa.Column("po_no", sa.String(24), nullable=False),
        sa.Column("vendor_code", sa.String(16), nullable=False),
        sa.Column("subtotal", sa.BigInteger, nullable=False),
        sa.Column("tax_amount", sa.BigInteger, nullable=False),
        sa.Column("total", sa.BigInteger, nullable=False),
        sa.Column("match_status", sa.String(20), nullable=False, server_default="MATCHED"),
        sa.Column("status", sa.String(20), nullable=False, server_default="APPROVED"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "journal_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("journal_no", sa.String(24), nullable=False, unique=True),
        sa.Column("entry_date", sa.Date, nullable=False),
        sa.Column("period_code", sa.String(7), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_id", sa.String(36), nullable=False),
        sa.Column("rule_code", sa.String(24), nullable=False),
        sa.Column("description", sa.String(200), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="POSTED"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "journal_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("journal_entry_id", sa.String(36), sa.ForeignKey("journal_entries.id"), nullable=False),
        sa.Column("account_code", sa.String(10), sa.ForeignKey("accounts.code"), nullable=False),
        sa.Column("debit", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("credit", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("business_line", sa.String(15), nullable=True),
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
        "outbox_events", "processed_events", "journal_lines", "journal_entries",
        "vendor_bills", "invoices", "budgets", "fiscal_periods", "accounts",
    ]:
        op.drop_table(table)
