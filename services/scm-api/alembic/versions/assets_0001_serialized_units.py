"""Slice C: unit bernomor seri dan riwayat status

Revision ID: assets_0001
Revises:
Create Date: 2026-11-26
"""
from alembic import op
import sqlalchemy as sa

revision = "assets_0001"
down_revision = None
branch_labels = ("assets",)
depends_on = "core_0001"


def upgrade() -> None:
    op.create_table(
        "serialized_units",
        sa.Column("serial_number", sa.String(40), primary_key=True),
        sa.Column("item_sku", sa.String(20), sa.ForeignKey("items.sku"), nullable=False),
        sa.Column("warehouse_code", sa.String(16), sa.ForeignKey("warehouses.code"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("stock_request_no", sa.String(24), nullable=True),
        sa.Column("technician_employee_id", sa.String(20), nullable=True),
        sa.Column("installed_ticket_code", sa.String(20), nullable=True),
        sa.Column("received_gr_no", sa.String(24), nullable=True),
        sa.Column("received_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index("ix_serialized_units_item_sku", "serialized_units", ["item_sku"])
    op.create_index("ix_serialized_units_warehouse_code", "serialized_units", ["warehouse_code"])
    op.create_index("ix_serialized_units_status", "serialized_units", ["status"])
    op.create_index("ix_serialized_units_stock_request_no", "serialized_units", ["stock_request_no"])
    op.create_index("ix_serialized_units_technician_employee_id", "serialized_units", ["technician_employee_id"])
    op.create_table(
        "unit_status_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("serial_number", sa.String(40), sa.ForeignKey("serialized_units.serial_number"), nullable=False),
        sa.Column("from_status", sa.String(20), nullable=True),
        sa.Column("to_status", sa.String(20), nullable=False),
        sa.Column("ref", sa.String(40), nullable=True),
        sa.Column("by", sa.String(40), nullable=True),
        sa.Column("at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_unit_status_logs_serial_number", "unit_status_logs", ["serial_number"])


def downgrade() -> None:
    op.drop_table("unit_status_logs")
    op.drop_table("serialized_units")
