"""Tabel Slice C: unit bernomor seri dan riwayat statusnya (SCM-0-05)."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.core.models import gen_uuid
from app.database import Base


class SerializedUnit(Base):
    __tablename__ = "serialized_units"

    serial_number = Column(String(40), primary_key=True)
    item_sku = Column(String(20), ForeignKey("items.sku"), nullable=False, index=True)
    warehouse_code = Column(String(16), ForeignKey("warehouses.code"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="IN_STOCK", index=True)
    stock_request_no = Column(String(24), nullable=True, index=True)
    technician_employee_id = Column(String(20), nullable=True, index=True)
    installed_ticket_code = Column(String(20), nullable=True)
    received_gr_no = Column(String(24), nullable=True)
    received_at = Column(DateTime, nullable=False, server_default=func.now())
    version = Column(Integer, nullable=False, default=1)


class UnitStatusLog(Base):
    __tablename__ = "unit_status_logs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    serial_number = Column(String(40), ForeignKey("serialized_units.serial_number"), nullable=False, index=True)
    from_status = Column(String(20), nullable=True)
    to_status = Column(String(20), nullable=False)
    ref = Column(String(40), nullable=True)
    by = Column(String(40), nullable=True)
    at = Column(DateTime, server_default=func.now())
