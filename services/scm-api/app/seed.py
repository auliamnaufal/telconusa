from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import InventoryBalance, Item, PurchaseOrder, SerializedUnit, TechnicianKit, Vendor, Warehouse


def seed_scm() -> None:
    db: Session = SessionLocal()
    try:
        # 1. 3 Gudang (Bekasi Pusat, Bandung, Surabaya)
        warehouses = [
            ("WH-BKS", "Gudang Pusat Bekasi", "JKT"),
            ("WH-BDG", "Gudang Cabang Bandung", "BDG"),
            ("WH-SBY", "Gudang Cabang Surabaya", "SBY"),
        ]
        for code, name, city in warehouses:
            if not db.query(Warehouse).filter_by(code=code).first():
                db.add(Warehouse(code=code, name=name, city_code=city))
        db.flush()

        # 2. 4 Barang Fisik Blueprint
        items = [
            ("ONT-01", "Modem ONT Dual-Band GPON", "UNIT", 350000, 380, 100, True, "GPON ONT Wi-Fi 6 Dual-Band, 4 GE Ports, 1 SC/APC Optical Port"),
            ("SIM-01", "Kartu SIM 5G Ready", "PCS", 5000, 1000, 300, False, "Triple-cut USIM 5G NSA/SA compatible"),
            ("RTR-AX", "Router Wi-Fi 6 Mesh Tambahan", "UNIT", 500000, 75, 25, True, "AX3000 Dual-Band Mesh Router untuk jangkauan rumah luas"),
            ("CBL-FO", "Kabel Fiber Optik Dropcore 1C", "METER", 4000, 15500, 5000, False, "Single-mode G.657A1 outdoor drop cable"),
        ]
        for sku, name, unit, cost, rop, safety, serial, spec in items:
            if not db.query(Item).filter_by(sku=sku).first():
                db.add(Item(
                    sku=sku, name=name, unit=unit, unit_cost=cost,
                    reorder_point=rop, safety_stock=safety, is_serialized=serial, specification=spec,
                ))
        db.flush()

        # 3. Saldo Persediaan Awal
        balances = [
            ("WH-BKS", "ONT-01", 420, 5, 2),
            ("WH-BDG", "ONT-01", 65, 2, 0),
            ("WH-SBY", "ONT-01", 48, 0, 1),
            ("WH-BKS", "SIM-01", 2500, 20, 0),
            ("WH-BKS", "RTR-AX", 110, 3, 0),
            ("WH-BDG", "CBL-FO", 18500, 200, 0),
        ]
        for wh, sku, phys, res, dmg in balances:
            if not db.query(InventoryBalance).filter_by(warehouse_code=wh, item_sku=sku).first():
                db.add(InventoryBalance(
                    warehouse_code=wh, item_sku=sku, qty_physical=phys, qty_reserved=res, qty_damaged=dmg
                ))

        # 4. Serialized ONT Units
        units = [
            ("SN-ONT-2026-000001", "ONT-01", "WH-BDG", "INSTALLED", "EMP-0042", "ORD-2026-000123"),
            ("SN-ONT-2026-000002", "ONT-01", "WH-BDG", "IN_STOCK", None, None),
            ("SN-ONT-2026-000003", "ONT-01", "WH-BDG", "IN_STOCK", None, None),
            ("SN-ONT-2026-000004", "ONT-01", "WH-SBY", "IN_STOCK", None, None),
        ]
        for sn, sku, wh, st, tech, ord_no in units:
            if not db.query(SerializedUnit).filter_by(serial_number=sn).first():
                db.add(SerializedUnit(
                    serial_number=sn, item_sku=sku, warehouse_code=wh, status=st,
                    assigned_technician_id=tech, installed_order_no=ord_no,
                ))

        # 5. Paket Material Teknisi Rina (Notulen PDF D.3-5)
        if not db.query(TechnicianKit).filter_by(kit_code="KIT-2026-000001").first():
            db.add(TechnicianKit(
                kit_code="KIT-2026-000001",
                work_order_code="WO-000001",
                technician_employee_id="EMP-0042",
                ont_serial_number="SN-ONT-2026-000001",
                cable_issued_meters=50,
                cable_used_meters=28,
                cable_returned_meters=22,
                status="RECONCILED",
            ))

        # 6. 3 Vendor & 1 PO Pembelian 100 ONT (Rp35.000.000 - Tabel 2.28 Proposal Finance)
        vendors = [
            ("VEN-0001", "PT FiberTech Nusantara", "PERANGKAT_ONT", 4.85),
            ("VEN-0002", "PT Kabel Prima Indonesia", "KABEL_FIBER", 4.60),
            ("VEN-0003", "PT Kartu Cerdas Global", "SIM_CARD", 4.70),
        ]
        for code, name, cat, rating in vendors:
            if not db.query(Vendor).filter_by(code=code).first():
                db.add(Vendor(code=code, name=name, category=cat, rating_score=rating))
        db.flush()

        if not db.query(PurchaseOrder).filter_by(po_no="PO-2026-0001").first():
            db.add(PurchaseOrder(
                po_no="PO-2026-0001",
                vendor_code="VEN-0001",
                item_sku="ONT-01",
                qty=100,
                unit_price=350000,
                total_amount=35000000,
                status="RECEIVED",
            ))

        db.commit()
        print("[scm-api] Seed completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_scm()
