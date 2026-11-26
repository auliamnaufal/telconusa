"""Tabel inti SCM: master, saldo, pergerakan stok, audit, idempotensi, outbox

Revision ID: core_0001
Revises:
Create Date: 2026-11-26
"""
from alembic import op
import sqlalchemy as sa

revision = "core_0001"
down_revision = None
branch_labels = ("core",)
depends_on = None


def upgrade() -> None:
    op.create_table(
        "id_counters",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", sa.BigInteger, nullable=False),
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
        sa.Column("event_id", sa.String(40), nullable=False, unique=True),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("correlation_id", sa.String(40), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("payload_json", sa.Text, nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempts", sa.Integer, nullable=False),
        sa.Column("next_attempt_at", sa.DateTime, nullable=False),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "dead_letter_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_id", sa.String(40), nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("correlation_id", sa.String(40), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("payload_json", sa.Text, nullable=False),
        sa.Column("attempts", sa.Integer, nullable=False),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("dead_at", sa.DateTime, nullable=False),
    )
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
        "vendors",
        sa.Column("code", sa.String(16), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("rating_score", sa.Numeric(4, 2), nullable=False, server_default="0"),
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
        sa.UniqueConstraint("warehouse_code", "item_sku", name="uq_balance_warehouse_item"),
    )
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("warehouse_code", sa.String(16), sa.ForeignKey("warehouses.code"), nullable=False),
        sa.Column("item_sku", sa.String(20), sa.ForeignKey("items.sku"), nullable=False),
        sa.Column("type", sa.String(24), nullable=False),
        sa.Column("qty", sa.Integer, nullable=False),
        sa.Column("ref_type", sa.String(24), nullable=False),
        sa.Column("ref_no", sa.String(40), nullable=False),
        sa.Column("correlation_id", sa.String(40), nullable=True),
        sa.Column("created_by", sa.String(40), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_stock_movements_warehouse_code", "stock_movements", ["warehouse_code"])
    op.create_index("ix_stock_movements_item_sku", "stock_movements", ["item_sku"])
    op.create_index("ix_stock_movements_ref_no", "stock_movements", ["ref_no"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor", sa.String(40), nullable=False),
        sa.Column("role", sa.String(32), nullable=True),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("entity", sa.String(40), nullable=False),
        sa.Column("entity_id", sa.String(40), nullable=False),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("correlation_id", sa.String(40), nullable=True),
        sa.Column("at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_table(
        "idempotency_keys",
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("endpoint", sa.String(160), nullable=False),
        sa.Column("status_code", sa.Integer, nullable=False),
        sa.Column("response_json", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("key", "endpoint"),
    )


def downgrade() -> None:
    for table in (
        "idempotency_keys",
        "audit_logs",
        "stock_movements",
        "inventory_balances",
        "vendors",
        "items",
        "warehouses",
        "dead_letter_events",
        "outbox_events",
        "processed_events",
        "id_counters",
    ):
        op.drop_table(table)
