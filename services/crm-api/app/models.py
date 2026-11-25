import uuid
from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class CoverageArea(Base):
    __tablename__ = "coverage_areas"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    city_code = Column(String(10), nullable=False)
    city_name = Column(String(60), nullable=False)
    district = Column(String(80), nullable=False)
    postal_code = Column(String(10), nullable=False, unique=True)
    is_covered = Column(Boolean, nullable=False, default=True)


class CatalogProduct(Base):
    __tablename__ = "catalog_products"
    sku = Column(String(20), primary_key=True)
    name = Column(String(120), nullable=False)
    business_line = Column(String(15), nullable=False)
    unit_price = Column(BigInteger, nullable=False)
    billing_cycle = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    speed_label = Column(String(40), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    campaign_code = Column(String(20), nullable=False, unique=True)
    name = Column(String(120), nullable=False)
    channel = Column(String(40), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


class Customer(Base):
    __tablename__ = "customers"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    customer_code = Column(String(20), nullable=False, unique=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False, unique=True)
    whatsapp_number = Column(String(20), nullable=False)
    nik_or_npwp = Column(String(20), nullable=True, unique=True)
    password_hash = Column(String(255), nullable=False)
    segment = Column(String(20), nullable=False, default="INDIVIDUAL")
    created_at = Column(DateTime, server_default=func.now())


class CustomerInstallAddress(Base):
    __tablename__ = "customer_install_addresses"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    address_code = Column(String(20), nullable=False, unique=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    label = Column(String(60), nullable=False)
    install_address = Column(Text, nullable=False)
    city_code = Column(String(10), nullable=False)
    postal_code = Column(String(10), nullable=False)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    site_condition_notes = Column(Text, nullable=True)


class Order(Base):
    __tablename__ = "orders"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    order_no = Column(String(24), nullable=False, unique=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    install_address_id = Column(String(36), ForeignKey("customer_install_addresses.id"), nullable=True)
    sku = Column(String(20), ForeignKey("catalog_products.sku"), nullable=False)
    business_line = Column(String(15), nullable=False)
    sales_employee_id = Column(String(20), nullable=True)
    referral_code = Column(String(32), nullable=True)
    campaign_code = Column(String(20), nullable=True)
    subtotal = Column(BigInteger, nullable=False)
    discount = Column(BigInteger, nullable=False, default=0)
    status = Column(String(24), nullable=False, default="SUBMITTED")
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    subscription_code = Column(String(20), nullable=False, unique=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    install_address_id = Column(String(36), ForeignKey("customer_install_addresses.id"), nullable=True)
    sku = Column(String(20), nullable=False)
    monthly_price = Column(BigInteger, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    activated_at = Column(DateTime, nullable=True)


class WorkOrder(Base):
    __tablename__ = "work_orders"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    work_order_code = Column(String(20), nullable=False, unique=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    install_address_id = Column(String(36), ForeignKey("customer_install_addresses.id"), nullable=True)
    technician_employee_id = Column(String(20), nullable=True)
    work_order_type = Column(String(20), nullable=False, default="INSTALLATION")
    installation_status = Column(String(24), nullable=False, default="PENDING_ASSIGNMENT")
    kit_id = Column(String(24), nullable=True)
    ont_serial_number = Column(String(40), nullable=True)
    cable_used_meters = Column(Integer, nullable=True)
    signal_dbm = Column(Numeric(5, 2), nullable=True)
    speedtest_mbps = Column(Numeric(6, 2), nullable=True)
    site_condition_notes = Column(Text, nullable=True)
    scheduled_date = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    ticket_code = Column(String(20), nullable=False, unique=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    subscription_id = Column(String(36), nullable=True)
    priority = Column(String(4), nullable=False, default="P3")
    subject = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="OPEN")
    assigned_technician_id = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class TechnicianRating(Base):
    __tablename__ = "technician_ratings"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    work_order_id = Column(String(36), ForeignKey("work_orders.id"), nullable=False, unique=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    technician_employee_id = Column(String(20), nullable=False)
    rating_score = Column(Integer, nullable=False)
    rating_comment = Column(Text, nullable=True)
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
