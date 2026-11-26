"""Seed data inti: gudang, barang, vendor, saldo awal. Idempoten."""
from sqlalchemy.orm import Session

from app.core.codes import new_lot_seq, new_vendor_code
from app.core.models import InventoryBalance, Item, StockLot, Vendor, Warehouse

WAREHOUSES = [
    ("WH-BKS", "Gudang Pusat Bekasi", "JKT"),
    ("WH-BDG", "Gudang Cabang Bandung", "BDG"),
    ("WH-SBY", "Gudang Cabang Surabaya", "SBY"),
]

# sku, nama, satuan, harga satuan (rupiah), ROP per gudang, stok pengaman, serial, spesifikasi
ITEMS = [
    ("ONT-01", "Perangkat ONT Dual-Band GPON", "UNIT", 350000, 10, 5, True, "GPON ONT Wi-Fi 6 dual-band, 4 GE port, 1 SC/APC"),
    ("SIM-01", "Kartu SIM 5G", "PCS", 5000, 200, 50, False, "Triple-cut USIM 5G NSA/SA"),
    ("RTR-AX", "Router AX", "UNIT", 500000, 20, 10, False, "AX3000 dual-band mesh router"),
    ("CBL-FO", "Kabel Fiber Optik Dropcore 1C", "METER", 4000, 2000, 500, False, "Single-mode G.657A1 outdoor drop cable"),
]

VENDORS = [
    ("PT FiberTech Nusantara", "PERANGKAT_ONT", "4.85"),
    ("PT Kabel Prima Indonesia", "KABEL_FIBER", "4.60"),
    ("PT Kartu Cerdas Global", "SIM_CARD", "4.70"),
    ("PT Router Mandiri", "ROUTER", "4.40"),
]

# gudang, sku, fisik, reservasi, rusak. Untuk SKU serial, fisik harus sama dengan jumlah unit
# IN_STOCK + RESERVED + FAULTY di gudang itu (lihat app/assets/seed.py).
BALANCES = [
    ("WH-BKS", "ONT-01", 40, 0, 1),
    ("WH-BDG", "ONT-01", 20, 0, 0),
    ("WH-SBY", "ONT-01", 15, 0, 0),
    ("WH-BKS", "SIM-01", 2500, 0, 0),
    ("WH-BKS", "RTR-AX", 110, 0, 0),
    ("WH-BKS", "CBL-FO", 15000, 0, 0),
    ("WH-BDG", "CBL-FO", 18500, 0, 0),
    ("WH-SBY", "CBL-FO", 12000, 0, 0),
]


def seed_core(db: Session) -> None:
    for code, name, city in WAREHOUSES:
        if db.get(Warehouse, code) is None:
            db.add(Warehouse(code=code, name=name, city_code=city))
    for sku, name, unit, cost, rop, safety, serial, spec in ITEMS:
        if db.get(Item, sku) is None:
            db.add(
                Item(
                    sku=sku, name=name, unit=unit, unit_cost=cost, reorder_point=rop,
                    safety_stock=safety, is_serialized=serial, specification=spec,
                )
            )
    db.flush()

    for name, category, rating in VENDORS:
        if db.query(Vendor).filter(Vendor.name == name).first() is None:
            db.add(Vendor(code=new_vendor_code(db), name=name, category=category, rating_score=rating))

    for warehouse, sku, physical, reserved, damaged in BALANCES:
        exists = (
            db.query(InventoryBalance)
            .filter(InventoryBalance.warehouse_code == warehouse, InventoryBalance.item_sku == sku)
            .first()
        )
        if exists is None:
            db.add(
                InventoryBalance(
                    warehouse_code=warehouse, item_sku=sku, qty_physical=physical,
                    qty_reserved=reserved, qty_damaged=damaged,
                )
            )
    db.flush()

    # Satu lot awal per saldo non-serial (stok baik = fisik - rusak).
    serialized = {item.sku for item in db.query(Item).filter(Item.is_serialized.is_(True))}
    for balance in db.query(InventoryBalance).order_by(InventoryBalance.warehouse_code, InventoryBalance.item_sku):
        good = balance.qty_physical - balance.qty_damaged
        has_lot = (
            db.query(StockLot)
            .filter(StockLot.warehouse_code == balance.warehouse_code, StockLot.item_sku == balance.item_sku)
            .first()
        )
        if balance.item_sku not in serialized and good > 0 and has_lot is None:
            db.add(
                StockLot(
                    warehouse_code=balance.warehouse_code, item_sku=balance.item_sku,
                    seq=new_lot_seq(db), ref_no="SEED", qty_remaining=good,
                )
            )
    db.flush()
