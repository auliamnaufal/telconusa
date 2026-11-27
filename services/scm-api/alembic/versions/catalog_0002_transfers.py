"""Slice D: transfer antar-gudang (SCM-D-10)

Revision ID: catalog_0002
Revises: catalog_0001
Create Date: 2026-11-27
"""
from alembic import op
import sqlalchemy as sa

revision = "catalog_0002"
down_revision = "catalog_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transfers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("transfer_no", sa.String(24), nullable=False, unique=True),
        sa.Column("from_warehouse_code", sa.String(16), sa.ForeignKey("warehouses.code"), nullable=False),
        sa.Column("to_warehouse_code", sa.String(16), sa.ForeignKey("warehouses.code"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="REQUESTED"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by", sa.String(40), nullable=True),
        sa.Column("dispatched_by", sa.String(40), nullable=True),
        sa.Column("dispatched_at", sa.DateTime, nullable=True),
        sa.Column("received_by", sa.String(40), nullable=True),
        sa.Column("received_at", sa.DateTime, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_transfers_status", "transfers", ["status"])
    op.create_table(
        "transfer_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("transfer_id", sa.String(36), sa.ForeignKey("transfers.id"), nullable=False),
        sa.Column("item_sku", sa.String(20), sa.ForeignKey("items.sku"), nullable=False),
        sa.Column("qty", sa.Integer, nullable=False),
        sa.Column("serial_numbers", sa.Text, nullable=True),
    )
    op.create_index("ix_transfer_lines_transfer_id", "transfer_lines", ["transfer_id"])


def downgrade() -> None:
    op.drop_table("transfer_lines")
    op.drop_table("transfers")
