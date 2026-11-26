"""Slice D: daftar barang per paket layanan

Revision ID: catalog_0001
Revises:
Create Date: 2026-11-26
"""
from alembic import op
import sqlalchemy as sa

revision = "catalog_0001"
down_revision = None
branch_labels = ("catalog",)
depends_on = "core_0001"


def upgrade() -> None:
    op.create_table(
        "package_kits",
        sa.Column("service_sku", sa.String(30), primary_key=True),
    )
    op.create_table(
        "package_kit_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("service_sku", sa.String(30), sa.ForeignKey("package_kits.service_sku"), nullable=False),
        sa.Column("item_sku", sa.String(20), sa.ForeignKey("items.sku"), nullable=False),
        sa.Column("qty", sa.Integer, nullable=False),
        sa.Column("unit", sa.String(16), nullable=False),
    )
    op.create_index("ix_package_kit_lines_service_sku", "package_kit_lines", ["service_sku"])


def downgrade() -> None:
    op.drop_table("package_kit_lines")
    op.drop_table("package_kits")
