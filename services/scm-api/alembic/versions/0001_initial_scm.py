"""Initial SCM schema (Blueprint + Notulen PDF)

Revision ID: 0001_initial_scm
Revises:
Create Date: 2026-11-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_scm"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "warehouses",
        sa.Column("code", sa.String(16), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("city_code", sa.String(10), nullable=False),
    )
    op.create_table(
        "items",
        sa.Column("sku", sa.String(20), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("unit", sa.String(16), nullable=False),
        sa.Column("unit_cost", sa.BigInteger, nullable=False),
        sa.Column("reorder_point", sa.Integer, nullable=False, server_default="100"),
        sa.Column("safety_stock", sa.Integer, nullable=False, server_default="50"),
        sa.Column("is_serialized", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("specification", sa.Text, nullable=True),
    )
    op.create_table(
        "inventory_balances",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("warehouse_code", sa.String(16), sa.ForeignKey("warehouses.code"), nullable=False),
        sa.Column("item_sku", sa.String(20), sa.ForeignKey("items.sku"), nullable=False),
        sa.Column("qty_physical", sa.Integer, nullable=False, server_default="0"),
        sa.Column("qty_reserved", sa.Integer, nullable=False, server_default="0"),
        sa.Column("qty_damaged", sa.Integer, nullable=False, server_default="0"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_table(
        "serialized_units",
        sa.Column("serial_number", sa.String(40), primary_key=True),
        sa.Column("item_sku", sa.String(20), sa.ForeignKey("items.sku"), nullable=False),
        sa.Column("warehouse_code", sa.String(16), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="IN_STOCK"),
        sa.Column("assigned_technician_id", sa.String(20), nullable=True),
        sa.Column("installed_order_no", sa.String(24), nullable=True),
    )
    op.create_table(
        "technician_kits",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("kit_code", sa.String(24), nullable=False, unique=True),
        sa.Column("work_order_code", sa.String(20), nullable=False),
        sa.Column("technician_employee_id", sa.String(20), nullable=False),
        sa.Column("ont_serial_number", sa.String(40), nullable=True),
        sa.Column("cable_issued_meters", sa.Integer, nullable=False, server_default="50"),
        sa.Column("cable_used_meters", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cable_returned_meters", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ISSUED"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "vendors",
        sa.Column("code", sa.String(16), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("rating_score", sa.Numeric(4, 2), nullable=False, server_default="4.50"),
    )
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("po_no", sa.String(24), nullable=False, unique=True),
        sa.Column("vendor_code", sa.String(16), sa.ForeignKey("vendors.code"), nullable=False),
        sa.Column("item_sku", sa.String(20), sa.ForeignKey("items.sku"), nullable=False),
        sa.Column("qty", sa.Integer, nullable=False),
        sa.Column("unit_price", sa.BigInteger, nullable=False),
        sa.Column("total_amount", sa.BigInteger, nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="APPROVED"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
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
        "outbox_events", "processed_events", "purchase_orders", "vendors",
        "technician_kits", "serialized_units", "inventory_balances", "items", "warehouses",
    ]:
        op.drop_table(table)
