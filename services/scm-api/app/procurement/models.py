"""Tabel Slice B: PR, PO, persetujuan, penerimaan barang (SCM-0-05)."""
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.models import gen_uuid
from app.database import Base


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    pr_no = Column(String(24), nullable=False, unique=True)
    source = Column(String(20), nullable=False)  # STOCK_REQUEST | LOW_STOCK | MANUAL
    stock_request_no = Column(String(24), nullable=True, index=True)
    warehouse_code = Column(String(16), ForeignKey("warehouses.code"), nullable=False)
    estimated_total = Column(BigInteger, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="PENDING_BUDGET", index=True)
    budget_checked_at = Column(DateTime, nullable=True)
    budget_remaining = Column(BigInteger, nullable=True)
    created_by = Column(String(40), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())

    lines = relationship("PurchaseRequestLine", back_populates="purchase_request", cascade="all, delete-orphan")


class PurchaseRequestLine(Base):
    __tablename__ = "purchase_request_lines"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    purchase_request_id = Column(String(36), ForeignKey("purchase_requests.id"), nullable=False, index=True)
    item_sku = Column(String(20), ForeignKey("items.sku"), nullable=False)
    qty = Column(Integer, nullable=False)
    estimated_unit_cost = Column(BigInteger, nullable=False)

    purchase_request = relationship("PurchaseRequest", back_populates="lines")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    po_no = Column(String(24), nullable=False, unique=True)
    purchase_request_no = Column(String(24), nullable=True, index=True)
    vendor_code = Column(String(16), ForeignKey("vendors.code"), nullable=False)
    total_amount = Column(BigInteger, nullable=False)
    status = Column(String(24), nullable=False, default="PENDING_APPROVAL", index=True)
    required_roles = Column(Text, nullable=False, default="[]")  # JSON array role penyetuju
    created_by = Column(String(40), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())

    lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")
    approvals = relationship("PoApproval", back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    purchase_order_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=False, index=True)
    item_sku = Column(String(20), ForeignKey("items.sku"), nullable=False)
    qty = Column(Integer, nullable=False)
    unit_price = Column(BigInteger, nullable=False)
    qty_received = Column(Integer, nullable=False, default=0)

    purchase_order = relationship("PurchaseOrder", back_populates="lines")


class PoApproval(Base):
    __tablename__ = "po_approvals"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    purchase_order_id = Column(String(36), ForeignKey("purchase_orders.id"), nullable=False, index=True)
    role = Column(String(32), nullable=False)
    approver_id = Column(String(40), nullable=False)
    decision = Column(String(10), nullable=False)  # APPROVED | REJECTED
    comment = Column(Text, nullable=True)
    at = Column(DateTime, server_default=func.now())

    purchase_order = relationship("PurchaseOrder", back_populates="approvals")


class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    gr_no = Column(String(24), nullable=False, unique=True)
    po_no = Column(String(24), nullable=False, index=True)
    warehouse_code = Column(String(16), ForeignKey("warehouses.code"), nullable=False)
    received_by = Column(String(40), nullable=False)
    received_at = Column(DateTime, server_default=func.now())

    lines = relationship("GoodsReceiptLine", back_populates="goods_receipt", cascade="all, delete-orphan")


class GoodsReceiptLine(Base):
    __tablename__ = "goods_receipt_lines"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    goods_receipt_id = Column(String(36), ForeignKey("goods_receipts.id"), nullable=False, index=True)
    item_sku = Column(String(20), ForeignKey("items.sku"), nullable=False)
    qty = Column(Integer, nullable=False)
    serial_numbers = Column(Text, nullable=True)  # JSON array

    goods_receipt = relationship("GoodsReceipt", back_populates="lines")
