from datetime import date, datetime
from sqlalchemy.orm import Session
from shared.auth import hash_password
from app.database import SessionLocal
from app.models import (
    Campaign, CatalogProduct, CoverageArea, Customer,
    CustomerInstallAddress, Order, Subscription, TechnicianRating, Ticket, WorkOrder,
)


def seed_crm() -> None:
    db: Session = SessionLocal()
    try:
        # 1. Coverage Areas (Jakarta, Bandung, Surabaya)
        areas = [
            ("JKT", "Jakarta Selatan", "Kebayoran Baru", "12110"),
            ("JKT", "Jakarta Pusat", "Menteng", "10310"),
            ("BDG", "Bandung", "Coblong", "40132"),
            ("BDG", "Bandung", "Cicendo", "40171"),
            ("SBY", "Surabaya", "Gubeng", "60281"),
            ("SBY", "Surabaya", "Mulyorejo", "60115"),
        ]
        for city_code, city_name, district, postal_code in areas:
            if not db.query(CoverageArea).filter_by(postal_code=postal_code).first():
                db.add(CoverageArea(city_code=city_code, city_name=city_name, district=district, postal_code=postal_code))

        # 2. 10 SKU Katalog Produk (Sesuai Blueprint)
        products = [
            ("MOB-PRE-10", "Paket Data 5G 10 GB (30 Hari)", "PREPAID", 50000, "ONE_TIME", "Kuota 5G ultra cepat 10 GB aktif 30 hari di seluruh Nusantara.", "5G 10 GB"),
            ("MOB-PRE-50", "Paket Data 5G 50 GB (30 Hari)", "PREPAID", 150000, "ONE_TIME", "Kuota besar 50 GB tanpa batas kecepatan untuk streaming & kerja.", "5G 50 GB"),
            ("MOB-POST-50", "Pascabayar Priority 50 GB", "POSTPAID", 175000, "MONTHLY", "Tagihan bulanan fleksibel dengan prioritas jaringan 5G+.", "5G Priority"),
            ("HOME-20", "TelcoHome Fiber 20 Mbps", "HOME", 250000, "MONTHLY", "Internet rumah fiber optik stabil untuk keluarga kecil (up to 20 Mbps).", "20 Mbps"),
            ("HOME-50", "TelcoHome Fiber 50 Mbps", "HOME", 400000, "MONTHLY", "Favorit keluarga & WFH — fiber simetris 50 Mbps bebas FUP.", "50 Mbps"),
            ("HOME-100", "TelcoHome Fiber 100 Mbps", "HOME", 600000, "MONTHLY", "Ultra-fast fiber 100 Mbps untuk gaming, 4K, dan smart home.", "100 Mbps"),
            ("SVC-INST-H", "Biaya Instalasi Internet Rumah", "HOME", 150000, "ONE_TIME", "Instalasi kabel fiber, aktivasi ONT, dan uji kecepatan oleh teknisi.", "Instalasi"),
            ("B2B-DIA-100", "Dedicated Internet 100 Mbps (B2B)", "B2B", 7500000, "MONTHLY", "SLA 99.9% rasio 1:1 dengan IP Static dan dukungan 24/7.", "100 Mbps 1:1"),
            ("SVC-INST-B", "Instalasi Korporat & Proyek", "B2B", 5000000, "ONE_TIME", "Survei teknis, penarikan fiber dedicated, dan berita acara aktivasi.", "Proyek B2B"),
            ("B2B-SMS", "Enterprise SMS Blast", "B2B", 300, "USAGE", "Layanan pengiriman OTP & broadcast korporat per SMS.", "Rp300/SMS"),
        ]
        for sku, name, line, price, cycle, desc, speed in products:
            if not db.query(CatalogProduct).filter_by(sku=sku).first():
                db.add(CatalogProduct(
                    sku=sku, name=name, business_line=line, unit_price=price,
                    billing_cycle=cycle, description=desc, speed_label=speed,
                ))

        # 3. Campaigns (Notulen PDF)
        if not db.query(Campaign).filter_by(campaign_code="CMP-2026-001").first():
            db.add(Campaign(
                campaign_code="CMP-2026-001",
                name="Promo Nusantara Fiber Akhir Tahun",
                channel="DIGITAL_REFERRAL",
                start_date=date(2026, 11, 1),
                end_date=date(2026, 12, 31),
            ))

        # 4. Demo Customer: Pak Andi (CUS-000456) + 2 pelanggan tambahan
        pw = hash_password("telconusa123", salt="telconusa_seed_salt")
        customers = [
            ("CUS-000456", "Andi Pratama", "andi@gmail.com", "6281234560456", "3273011205880001", "INDIVIDUAL"),
            ("CUS-000457", "Siti Rahmawati", "siti@gmail.com", "6281234560457", "3578014506910002", "INDIVIDUAL"),
            ("CUS-000458", "PT Nusantara Logistik", "it@nusantaralogistik.co.id", "6281199887766", "01.234.567.8-012.000", "B2B"),
        ]
        cust_map = {}
        for code, name, email, wa, nik, seg in customers:
            obj = db.query(Customer).filter_by(customer_code=code).first()
            if not obj:
                obj = Customer(
                    customer_code=code, full_name=name, email=email,
                    whatsapp_number=wa, nik_or_npwp=nik, password_hash=pw, segment=seg,
                )
                db.add(obj)
                db.flush()
            cust_map[code] = obj

        # 5. Alamat Pemasangan Pak Andi (Bandung - Coblong)
        addr = db.query(CustomerInstallAddress).filter_by(address_code="ADR-000001").first()
        if not addr:
            addr = CustomerInstallAddress(
                address_code="ADR-000001",
                customer_id=cust_map["CUS-000456"].id,
                label="Rumah Utama Bandung",
                install_address="Jl. Dago Asri No. 18, Coblong, Bandung",
                city_code="BDG",
                postal_code="40132",
                latitude=-6.8842100,
                longitude=107.6138900,
                site_condition_notes="Tiang ODP berjarak 25m di depan rumah, jalur kabel atas aman.",
            )
            db.add(addr)
            db.flush()

        # 6. Demo Order Utama Blueprint: ORD-2026-000123 (HOME-50 + Instalasi, Sales Budi EMP-0017)
        order = db.query(Order).filter_by(order_no="ORD-2026-000123").first()
        if not order:
            order = Order(
                order_no="ORD-2026-000123",
                customer_id=cust_map["CUS-000456"].id,
                install_address_id=addr.id,
                sku="HOME-50",
                business_line="HOME",
                sales_employee_id="EMP-0017",
                referral_code="REF-EMP0017",
                campaign_code="CMP-2026-001",
                subtotal=550000,
                discount=0,
                status="COMPLETED",
            )
            db.add(order)
            db.flush()

        if not db.query(Subscription).filter_by(subscription_code="SUB-000001").first():
            db.add(Subscription(
                subscription_code="SUB-000001",
                order_id=order.id,
                customer_id=cust_map["CUS-000456"].id,
                install_address_id=addr.id,
                sku="HOME-50",
                monthly_price=400000,
                status="ACTIVE",
                activated_at=datetime(2026, 11, 18, 14, 0, 0),
            ))

        wo = db.query(WorkOrder).filter_by(work_order_code="WO-000001").first()
        if not wo:
            wo = WorkOrder(
                work_order_code="WO-000001",
                order_id=order.id,
                install_address_id=addr.id,
                technician_employee_id="EMP-0042",
                work_order_type="INSTALLATION",
                installation_status="COMPLETED",
                kit_id="KIT-2026-000001",
                ont_serial_number="SN-ONT-2026-000001",
                cable_used_meters=28,
                signal_dbm=-18.40,
                speedtest_mbps=52.80,
                site_condition_notes="ONT dipasang di ruang tamu, redaman optimal -18.4 dBm.",
                scheduled_date=date(2026, 11, 18),
            )
            db.add(wo)
            db.flush()

        if not db.query(TechnicianRating).filter_by(work_order_id=wo.id).first():
            db.add(TechnicianRating(
                work_order_id=wo.id,
                customer_id=cust_map["CUS-000456"].id,
                technician_employee_id="EMP-0042",
                rating_score=5,
                rating_comment="Teknisi Rina sangat ramah, rapi, dan kecepatan langsung 52 Mbps!",
            ))

        if not db.query(Ticket).filter_by(ticket_code="TKT-000001").first():
            db.add(Ticket(
                ticket_code="TKT-000001",
                customer_id=cust_map["CUS-000457"].id,
                priority="P2",
                subject="Modem ONT lampu LOS berkedip merah",
                description="Koneksi internet rumah terputus sejak pukul 09.00 WIB.",
                status="IN_PROGRESS",
                assigned_technician_id="EMP-0042",
            ))

        db.commit()
        print("[crm-api] Seed completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_crm()
