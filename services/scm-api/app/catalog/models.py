"""Tabel Slice D: daftar barang per paket layanan (SCM-0-05) dan transfer antar-gudang (SCM-D-10)."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.models import gen_uuid
from app.database import Base


class PackageKit(Base):
    __tablename__ = "package_kits"

    service_sku = Column(String(30), primary_key=True)

    lines = relationship("PackageKitLine", back_populates="kit", cascade="all, delete-orphan")


class PackageKitLine(Base):
    __tablename__ = "package_kit_lines"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    service_sku = Column(String(30), ForeignKey("package_kits.service_sku"), nullable=False, index=True)
    item_sku = Column(String(20), ForeignKey("items.sku"), nullable=False)
    qty = Column(Integer, nullable=False)
    unit = Column(String(16), nullable=False)

    kit = relationship("PackageKit", back_populates="lines")


class Transfer(Base):
    """Transfer antar-gudang (SCM-D-10): REQUESTED -> IN_TRANSIT -> RECEIVED."""

    __tablename__ = "transfers"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    transfer_no = Column(String(24), nullable=False, unique=True)
    from_warehouse_code = Column(String(16), ForeignKey("warehouses.code"), nullable=False)
    to_warehouse_code = Column(String(16), ForeignKey("warehouses.code"), nullable=False)
    status = Column(String(20), nullable=False, default="REQUESTED", index=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(40), nullable=True)
    dispatched_by = Column(String(40), nullable=True)
    dispatched_at = Column(DateTime, nullable=True)
    received_by = Column(String(40), nullable=True)
    received_at = Column(DateTime, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())

    __mapper_args__ = {"version_id_col": version}

    lines = relationship("TransferLine", back_populates="transfer", cascade="all, delete-orphan")


class TransferLine(Base):
    __tablename__ = "transfer_lines"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    transfer_id = Column(String(36), ForeignKey("transfers.id"), nullable=False, index=True)
    item_sku = Column(String(20), ForeignKey("items.sku"), nullable=False)
    qty = Column(Integer, nullable=False)
    serial_numbers = Column(Text, nullable=True)  # JSON array; terisi setelah AssetPort bisa memindahkan unit

    transfer = relationship("Transfer", back_populates="lines")
