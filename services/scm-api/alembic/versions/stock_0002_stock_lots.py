"""Slice A: batch stok non-serial untuk FIFO

Revision ID: stock_0002
Revises: stock_0001
Create Date: 2026-11-26
"""
import uuid

from alembic import op
import sqlalchemy as sa

revision = "stock_0002"
down_revision = "stock_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_lots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("warehouse_code", sa.String(16), sa.ForeignKey("warehouses.code"), nullable=False),
        sa.Column("item_sku", sa.String(20), sa.ForeignKey("items.sku"), nullable=False),
        sa.Column("seq", sa.BigInteger, nullable=False),
        sa.Column("ref_no", sa.String(40), nullable=True),
        sa.Column("qty_remaining", sa.Integer, nullable=False),
        sa.Column("received_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_stock_lots_warehouse_code", "stock_lots", ["warehouse_code"])
    op.create_index("ix_stock_lots_item_sku", "stock_lots", ["item_sku"])
    op.create_index("ix_stock_lots_seq", "stock_lots", ["seq"])

    # Saldo non-serial yang sudah ada menjadi satu lot awal (stok baik = fisik - rusak).
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT b.warehouse_code, b.item_sku, b.qty_physical - b.qty_damaged AS good "
            "FROM inventory_balances b JOIN items i ON i.sku = b.item_sku "
            "WHERE i.is_serialized = :serialized AND b.qty_physical - b.qty_damaged > 0 "
            "ORDER BY b.warehouse_code, b.item_sku"
        ),
        {"serialized": False},
    ).fetchall()
    seq = 0
    for warehouse_code, item_sku, good in rows:
        seq += 1
        bind.execute(
            sa.text(
                "INSERT INTO stock_lots (id, warehouse_code, item_sku, seq, ref_no, qty_remaining) "
                "VALUES (:id, :warehouse_code, :item_sku, :seq, 'MIGRATION', :qty)"
            ),
            {"id": str(uuid.uuid4()), "warehouse_code": warehouse_code, "item_sku": item_sku, "seq": seq, "qty": good},
        )
    if seq:  # lanjutkan urutan FIFO dari lot yang baru dibuat
        counters = sa.table("id_counters", sa.column("key", sa.String), sa.column("value", sa.BigInteger))
        op.bulk_insert(counters, [{"key": "LOT", "value": seq}])


def downgrade() -> None:
    op.drop_table("stock_lots")
