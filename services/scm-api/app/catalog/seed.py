"""Seed daftar barang paket layanan. Idempoten."""
from sqlalchemy.orm import Session

from app.catalog.models import PackageKit, PackageKitLine

# Paket rumah: satu ONT dan 50 m kabel fiber. Paket MOB-* dan B2B-* belum punya daftar barang.
KITS = {
    "HOME-20": [("ONT-01", 1, "UNIT"), ("CBL-FO", 50, "METER")],
    "HOME-50": [("ONT-01", 1, "UNIT"), ("CBL-FO", 50, "METER")],
    "HOME-100": [("ONT-01", 1, "UNIT"), ("CBL-FO", 50, "METER")],
}


def seed_catalog(db: Session) -> None:
    for service_sku, lines in KITS.items():
        if db.get(PackageKit, service_sku) is not None:
            continue
        kit = PackageKit(service_sku=service_sku)
        kit.lines = [PackageKitLine(item_sku=sku, qty=qty, unit=unit) for sku, qty, unit in lines]
        db.add(kit)
    db.flush()
