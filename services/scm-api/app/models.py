import uuid
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from app.database import Base


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


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    warehouse_code = Column(String(16), ForeignKey("warehouses.code"), nullable=False)
    item_sku = Column(String(20), ForeignKey("items.sku"), nullable=False)
    qty_physical = Column(Integer, nullable=False, default=0)
    qty_reserved = Column(Integer, nullable=False, default=0)
    qty_damaged = Column(Integer, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)


class SerializedUnit(Base):
    __tablename__ = "serialized_units"
    serial_number = Column(String(40), primary_key=True)
    item_sku = Column(String(20), ForeignKey("items.sku"), nullable=False)
    warehouse_code = Column(String(16), nullable=False)
    status = Column(String(24), nullable=False, default="IN_STOCK")
    assigned_technician_id = Column(String(20), nullable=True)
    installed_order_no = Column(String(24), nullable=True)


class TechnicianKit(Base):
    __tablename__ = "technician_kits"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    kit_code = Column(String(24), nullable=False, unique=True)
    work_order_code = Column(String(20), nullable=False)
    technician_employee_id = Column(String(20), nullable=False)
    ont_serial_number = Column(String(40), nullable=True)
    cable_issued_meters = Column(Integer, nullable=False, default=50)
    cable_used_meters = Column(Integer, nullable=False, default=0)
    cable_returned_meters = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="ISSUED")
    created_at = Column(DateTime, server_default=func.now())


class Vendor(Base):
    __tablename__ = "vendors"
    code = Column(String(16), primary_key=True)
    name = Column(String(120), nullable=False)
    category = Column(String(40), nullable=False)
    rating_score = Column(Numeric(4, 2), nullable=False, default=4.50)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    po_no = Column(String(24), nullable=False, unique=True)
    vendor_code = Column(String(16), ForeignKey("vendors.code"), nullable=False)
    item_sku = Column(String(20), ForeignKey("items.sku"), nullable=False)
    qty = Column(Integer, nullable=False)
    unit_price = Column(BigInteger, nullable=False)
    total_amount = Column(BigInteger, nullable=False)
    status = Column(String(24), nullable=False, default="APPROVED")
    created_at = Column(DateTime, server_default=func.now())


class ProcessedEvent(Base):
    __tablename__ = "processed_events"
    event_id = Column(String(40), primary_key=True)
    event_type = Column(String(60), nullable=False)
    processed_at = Column(DateTime, server_default=func.now())


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    event_type = Column(String(60), nullable=False)
    correlation_id = Column(String(40), nullable=False)
    payload_json = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="SENT")
    created_at = Column(DateTime, server_default=func.now())
