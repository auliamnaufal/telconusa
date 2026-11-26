"""Tabel Slice D: daftar barang per paket layanan (SCM-0-05)."""
from sqlalchemy import Column, ForeignKey, Integer, String
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
