"""Slice B: PR, PO, persetujuan, penerimaan barang

Revision ID: procurement_0001
Revises:
Create Date: 2026-11-26
"""
from alembic import op
import sqlalchemy as sa

revision = "procurement_0001"
down_revision = None
branch_labels = ("procurement",)
depends_on = "core_0001"


def upgrade() -> None:
    op.create_table(
        "purchase_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pr_no", sa.String(24), nullable=False, unique=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("stock_request_no", sa.String(24), nullable=True),
        sa.Column("warehouse_code", sa.String(16), sa.ForeignKey("warehouses.code"), nullable=False),
        sa.Column("estimated_total", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("budget_checked_at", sa.DateTime, nullable=True),
        sa.Column("budget_remaining", sa.BigInteger, nullable=True),
        sa.Column("created_by", sa.String(40), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_purchase_requests_stock_request_no", "purchase_requests", ["stock_request_no"])
    op.create_index("ix_purchase_requests_status", "purchase_requests", ["status"])
    op.create_table(
        "purchase_request_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("purchase_request_id", sa.String(36), sa.ForeignKey("purchase_requests.id"), nullable=False),
        sa.Column("item_sku", sa.String(20), sa.ForeignKey("items.sku"), nullable=False),
        sa.Column("qty", sa.Integer, nullable=False),
        sa.Column("estimated_unit_cost", sa.BigInteger, nullable=False),
    )
    op.create_index("ix_purchase_request_lines_purchase_request_id", "purchase_request_lines", ["purchase_request_id"])
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("po_no", sa.String(24), nullable=False, unique=True),
        sa.Column("purchase_request_no", sa.String(24), nullable=True),
        sa.Column("vendor_code", sa.String(16), sa.ForeignKey("vendors.code"), nullable=False),
        sa.Column("total_amount", sa.BigInteger, nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("required_roles", sa.Text, nullable=False),
        sa.Column("created_by", sa.String(40), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_purchase_orders_purchase_request_no", "purchase_orders", ["purchase_request_no"])
    op.create_index("ix_purchase_orders_status", "purchase_orders", ["status"])
    op.create_table(
        "purchase_order_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("purchase_order_id", sa.String(36), sa.ForeignKey("purchase_orders.id"), nullable=False),
        sa.Column("item_sku", sa.String(20), sa.ForeignKey("items.sku"), nullable=False),
        sa.Column("qty", sa.Integer, nullable=False),
        sa.Column("unit_price", sa.BigInteger, nullable=False),
        sa.Column("qty_received", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_purchase_order_lines_purchase_order_id", "purchase_order_lines", ["purchase_order_id"])
    op.create_table(
        "po_approvals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("purchase_order_id", sa.String(36), sa.ForeignKey("purchase_orders.id"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("approver_id", sa.String(40), nullable=False),
        sa.Column("decision", sa.String(10), nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_po_approvals_purchase_order_id", "po_approvals", ["purchase_order_id"])
    op.create_table(
        "goods_receipts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("gr_no", sa.String(24), nullable=False, unique=True),
        sa.Column("po_no", sa.String(24), nullable=False),
        sa.Column("warehouse_code", sa.String(16), sa.ForeignKey("warehouses.code"), nullable=False),
        sa.Column("received_by", sa.String(40), nullable=False),
        sa.Column("received_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_goods_receipts_po_no", "goods_receipts", ["po_no"])
    op.create_table(
        "goods_receipt_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("goods_receipt_id", sa.String(36), sa.ForeignKey("goods_receipts.id"), nullable=False),
        sa.Column("item_sku", sa.String(20), sa.ForeignKey("items.sku"), nullable=False),
        sa.Column("qty", sa.Integer, nullable=False),
        sa.Column("serial_numbers", sa.Text, nullable=True),
    )
    op.create_index("ix_goods_receipt_lines_goods_receipt_id", "goods_receipt_lines", ["goods_receipt_id"])


def downgrade() -> None:
    for table in (
        "goods_receipt_lines",
        "goods_receipts",
        "po_approvals",
        "purchase_order_lines",
        "purchase_orders",
        "purchase_request_lines",
        "purchase_requests",
    ):
        op.drop_table(table)
