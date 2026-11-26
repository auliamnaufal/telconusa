"""Seed unit ONT bernomor seri; jumlahnya mengikuti saldo ONT di `app/core/seed.py`. Idempoten."""
from datetime import timedelta

from sqlalchemy.orm import Session

from app.assets.models import SerializedUnit, UnitStatusLog
from app.core import clock
from app.core.codes import new_serial_number
from app.core.models import InventoryBalance


def seed_assets(db: Session) -> None:
    base = clock.utcnow() - timedelta(days=30)
    minute = 0
    balances = (
        db.query(InventoryBalance)
        .filter(InventoryBalance.item_sku == "ONT-01")
        .order_by(InventoryBalance.warehouse_code)
        .all()
    )
    for balance in balances:
        existing = (
            db.query(SerializedUnit)
            .filter(SerializedUnit.item_sku == balance.item_sku, SerializedUnit.warehouse_code == balance.warehouse_code)
            .count()
        )
        faulty = balance.qty_damaged
        for index in range(existing, balance.qty_physical):
            status = "FAULTY" if index >= balance.qty_physical - faulty else "IN_STOCK"
            serial = new_serial_number(db)
            minute += 1
            db.add(
                SerializedUnit(
                    serial_number=serial,
                    item_sku=balance.item_sku,
                    warehouse_code=balance.warehouse_code,
                    status=status,
                    received_gr_no="SEED",
                    received_at=base + timedelta(minutes=minute),
                )
            )
            db.add(UnitStatusLog(serial_number=serial, from_status=None, to_status=status, ref="SEED", by="seed"))
    db.flush()
