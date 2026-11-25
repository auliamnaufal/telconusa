import uuid
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, Integer, String, Text, func
from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Account(Base):
    __tablename__ = "accounts"
    code = Column(String(10), primary_key=True)
    name = Column(String(120), nullable=False)
    account_type = Column(String(24), nullable=False)
    normal_balance = Column(String(10), nullable=False)


class FiscalPeriod(Base):
    __tablename__ = "fiscal_periods"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    period_code = Column(String(7), nullable=False, unique=True)
    status = Column(String(16), nullable=False, default="OPEN")


class Budget(Base):
    __tablename__ = "budgets"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    cost_center_code = Column(String(16), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    allocated_amount = Column(BigInteger, nullable=False)
    committed_amount = Column(BigInteger, nullable=False, default=0)
    realized_amount = Column(BigInteger, nullable=False, default=0)


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    invoice_no = Column(String(24), nullable=False, unique=True)
    order_no = Column(String(24), nullable=True, unique=True)
    customer_code = Column(String(20), nullable=False)
    customer_name = Column(String(120), nullable=False)
    business_line = Column(String(15), nullable=False)
    billing_period = Column(String(7), nullable=False)
    subtotal = Column(BigInteger, nullable=False)
    discount = Column(BigInteger, nullable=False, default=0)
    tax_amount = Column(BigInteger, nullable=False)
    total = Column(BigInteger, nullable=False)
    paid_amount = Column(BigInteger, nullable=False, default=0)
    virtual_account = Column(String(24), nullable=False)
    referral_code = Column(String(32), nullable=True)
    monthly_price = Column(BigInteger, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="ISSUED")
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())


class VendorBill(Base):
    __tablename__ = "vendor_bills"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    bill_no = Column(String(24), nullable=False, unique=True)
    po_no = Column(String(24), nullable=False)
    vendor_code = Column(String(16), nullable=False)
    subtotal = Column(BigInteger, nullable=False)
    tax_amount = Column(BigInteger, nullable=False)
    total = Column(BigInteger, nullable=False)
    match_status = Column(String(20), nullable=False, default="MATCHED")
    status = Column(String(20), nullable=False, default="APPROVED")
    created_at = Column(DateTime, server_default=func.now())


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    journal_no = Column(String(24), nullable=False, unique=True)
    entry_date = Column(Date, nullable=False)
    period_code = Column(String(7), nullable=False)
    source_type = Column(String(32), nullable=False)
    source_id = Column(String(36), nullable=False)
    rule_code = Column(String(24), nullable=False)
    description = Column(String(200), nullable=False)
    status = Column(String(16), nullable=False, default="POSTED")
    created_at = Column(DateTime, server_default=func.now())


class JournalLine(Base):
    __tablename__ = "journal_lines"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    journal_entry_id = Column(String(36), ForeignKey("journal_entries.id"), nullable=False)
    account_code = Column(String(10), ForeignKey("accounts.code"), nullable=False)
    debit = Column(BigInteger, nullable=False, default=0)
    credit = Column(BigInteger, nullable=False, default=0)
    business_line = Column(String(15), nullable=True)


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
