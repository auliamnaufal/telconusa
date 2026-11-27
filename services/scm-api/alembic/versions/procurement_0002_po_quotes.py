"""Slice B: penawaran vendor untuk PO (SCM-B-06)

Revision ID: procurement_0002
Revises: procurement_0001
Create Date: 2026-11-27
"""
from alembic import op
import sqlalchemy as sa

revision = "procurement_0002"
down_revision = "procurement_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "po_quotes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("po_no", sa.String(24), nullable=False),
        sa.Column("vendor_code", sa.String(16), sa.ForeignKey("vendors.code"), nullable=False),
        sa.Column("unit_price", sa.BigInteger, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("po_no", "vendor_code", name="uq_po_quote_vendor"),
    )
    op.create_index("ix_po_quotes_po_no", "po_quotes", ["po_no"])


def downgrade() -> None:
    op.drop_table("po_quotes")
