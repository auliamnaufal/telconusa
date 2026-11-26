"""Tabel Slice A: permintaan barang dari tiket (SCM-0-05)."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.models import gen_uuid
from app.database import Base


class StockRequest(Base):
    __tablename__ = "stock_requests"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    stock_request_no = Column(String(24), nullable=False, unique=True)
    ticket_code = Column(String(20), nullable=False, unique=True)
    order_no = Column(String(24), nullable=True)
    subscription_code = Column(String(20), nullable=True)
    city_code = Column(String(10), nullable=False)
    warehouse_code = Column(String(16), ForeignKey("warehouses.code"), nullable=False)
    technician_employee_id = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, default="REQUESTED", index=True)
    reserved_until = Column(DateTime, nullable=True)
    purchase_request_no = Column(String(24), nullable=True)
    discrepancy = Column(Boolean, nullable=False, default=False)
    cancel_reason = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    lines = relationship(
        "StockRequestLine",
        back_populates="stock_request",
        cascade="all, delete-orphan",
        order_by="StockRequestLine.position",
    )


class StockRequestLine(Base):
    __tablename__ = "stock_request_lines"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    stock_request_id = Column(String(36), ForeignKey("stock_requests.id"), nullable=False, index=True)
    position = Column(Integer, nullable=False, default=0)
    item_sku = Column(String(20), ForeignKey("items.sku"), nullable=False)
    qty_required = Column(Integer, nullable=False)
    qty_issued = Column(Integer, nullable=False, default=0)
    qty_used = Column(Integer, nullable=False, default=0)
    qty_returned = Column(Integer, nullable=False, default=0)
    qty_damaged = Column(Integer, nullable=False, default=0)
    unit = Column(String(16), nullable=False)
    is_extra = Column(Boolean, nullable=False, default=False)

    stock_request = relationship("StockRequest", back_populates="lines")


class PendingAssignment(Base):
    """Penugasan teknisi yang tiba sebelum permintaan barang dibuat (`ticket.assigned` lebih dulu)."""

    __tablename__ = "pending_assignments"

    ticket_code = Column(String(20), primary_key=True)
    technician_employee_id = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
