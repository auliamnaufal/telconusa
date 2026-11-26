"""Tabel inti SCM yang dipakai semua slice (SCM-0-05).

Slice tidak mengubah berkas ini; tabel tambahan dibuat di `models.py` slice sendiri
dengan migrasi tambahan.
"""
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    func,
)

from shared.event_receiver import make_processed_event_model
from shared.ids import make_counter_model
from shared.outbox import make_outbox_models

from app.database import Base

IdCounter = make_counter_model(Base)
OutboxEvent, DeadLetterEvent = make_outbox_models(Base)
ProcessedEvent = make_processed_event_model(Base)


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Warehouse(Base):
    __tablename__ = "warehouses"

    code = Column(String(16), primary_key=True)
    name = Column(String(80), nullable=False)
    city_code = Column(String(10), nullable=False)


class Item(Base):
    __tablename__ = "items"

    sku = Column(String(20), primary_key=True)
    name = Column(String(120), nullable=False)
    unit = Column(String(16), nullable=False)
    unit_cost = Column(BigInteger, nullable=False)
    reorder_point = Column(Integer, nullable=False, default=100)
    safety_stock = Column(Integer, nullable=False, default=50)
    is_serialized = Column(Boolean, nullable=False, default=False)
    specification = Column(Text, nullable=True)


class Vendor(Base):
    __tablename__ = "vendors"

    code = Column(String(16), primary_key=True)
    name = Column(String(120), nullable=False)
    category = Column(String(40), nullable=False)
    rating_score = Column(Numeric(4, 2), nullable=False, default=0)


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"
    __table_args__ = (UniqueConstraint("warehouse_code", "item_sku", name="uq_balance_warehouse_item"),)

    id = Column(String(36), primary_key=True, default=gen_uuid)
    warehouse_code = Column(String(16), ForeignKey("warehouses.code"), nullable=False)
    item_sku = Column(String(20), ForeignKey("items.sku"), nullable=False)
    qty_physical = Column(Integer, nullable=False, default=0)
    qty_reserved = Column(Integer, nullable=False, default=0)
    qty_damaged = Column(Integer, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)

    __mapper_args__ = {"version_id_col": version}

    @property
    def qty_available(self) -> int:
        return self.qty_physical - self.qty_reserved - self.qty_damaged


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    warehouse_code = Column(String(16), ForeignKey("warehouses.code"), nullable=False, index=True)
    item_sku = Column(String(20), ForeignKey("items.sku"), nullable=False, index=True)
    type = Column(String(24), nullable=False)
    qty = Column(Integer, nullable=False)
    ref_type = Column(String(24), nullable=False)
    ref_no = Column(String(40), nullable=False, index=True)
    correlation_id = Column(String(40), nullable=True)
    created_by = Column(String(40), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class StockLot(Base):
    """Batch stok non-serial untuk FIFO (SCM-A-11). Hanya stok baik: jumlah semua lot = fisik - rusak."""

    __tablename__ = "stock_lots"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    warehouse_code = Column(String(16), ForeignKey("warehouses.code"), nullable=False, index=True)
    item_sku = Column(String(20), ForeignKey("items.sku"), nullable=False, index=True)
    seq = Column(BigInteger, nullable=False, index=True)  # urutan masuk; FIFO mengurutkan menurut seq
    ref_no = Column(String(40), nullable=True)  # GR-... atau nomor permintaan asal
    qty_remaining = Column(Integer, nullable=False)
    received_at = Column(DateTime, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    actor = Column(String(40), nullable=False)
    role = Column(String(32), nullable=True)
    action = Column(String(60), nullable=False)
    entity = Column(String(40), nullable=False, index=True)
    entity_id = Column(String(40), nullable=False, index=True)
    detail = Column(Text, nullable=True)
    correlation_id = Column(String(40), nullable=True)
    at = Column(DateTime, server_default=func.now())


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (PrimaryKeyConstraint("key", "endpoint"),)

    key = Column(String(120), nullable=False)
    endpoint = Column(String(160), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_json = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
