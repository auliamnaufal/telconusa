"""Slice A: permintaan barang dan penugasan tertunda

Revision ID: stock_0001
Revises:
Create Date: 2026-11-26
"""
from alembic import op
import sqlalchemy as sa

revision = "stock_0001"
down_revision = None
branch_labels = ("stock",)
depends_on = "core_0001"


def upgrade() -> None:
    op.create_table(
        "stock_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("stock_request_no", sa.String(24), nullable=False, unique=True),
        sa.Column("ticket_code", sa.String(20), nullable=False, unique=True),
        sa.Column("order_no", sa.String(24), nullable=True),
        sa.Column("subscription_code", sa.String(20), nullable=True),
        sa.Column("city_code", sa.String(10), nullable=False),
        sa.Column("warehouse_code", sa.String(16), sa.ForeignKey("warehouses.code"), nullable=False),
        sa.Column("technician_employee_id", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reserved_until", sa.DateTime, nullable=True),
        sa.Column("purchase_request_no", sa.String(24), nullable=True),
        sa.Column("discrepancy", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("cancel_reason", sa.Text, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_stock_requests_status", "stock_requests", ["status"])
    op.create_table(
        "stock_request_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("stock_request_id", sa.String(36), sa.ForeignKey("stock_requests.id"), nullable=False),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("item_sku", sa.String(20), sa.ForeignKey("items.sku"), nullable=False),
        sa.Column("qty_required", sa.Integer, nullable=False),
        sa.Column("qty_issued", sa.Integer, nullable=False, server_default="0"),
        sa.Column("qty_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("qty_returned", sa.Integer, nullable=False, server_default="0"),
        sa.Column("qty_damaged", sa.Integer, nullable=False, server_default="0"),
        sa.Column("unit", sa.String(16), nullable=False),
        sa.Column("is_extra", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_stock_request_lines_stock_request_id", "stock_request_lines", ["stock_request_id"])
    op.create_table(
        "pending_assignments",
        sa.Column("ticket_code", sa.String(20), primary_key=True),
        sa.Column("technician_employee_id", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("pending_assignments")
    op.drop_table("stock_request_lines")
    op.drop_table("stock_requests")
