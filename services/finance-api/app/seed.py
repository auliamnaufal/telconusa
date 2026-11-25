from datetime import date
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Account, Budget, FiscalPeriod, Invoice, VendorBill
from app.posting_engine import post_journal


def seed_finance() -> None:
    db: Session = SessionLocal()
    try:
        # 1. 28 Bagan Akun Lengkap (Tabel 2.21 Proposal Finance)
        accounts = [
            ("1100", "Kas dan bank", "ASSET", "DEBIT"),
            ("1200", "Piutang usaha", "ASSET", "DEBIT"),
            ("1210", "Cadangan kerugian piutang", "CONTRA_ASSET", "CREDIT"),
            ("1300", "Persediaan", "ASSET", "DEBIT"),
            ("1400", "PPN masukan", "ASSET", "DEBIT"),
            ("1500", "Aset ONT di pelanggan", "ASSET", "DEBIT"),
            ("1510", "Akumulasi penyusutan ONT", "CONTRA_ASSET", "CREDIT"),
            ("2100", "Utang usaha", "LIABILITY", "CREDIT"),
            ("2110", "Utang gaji", "LIABILITY", "CREDIT"),
            ("2200", "PPN keluaran", "LIABILITY", "CREDIT"),
            ("2300", "Utang PPh 21", "LIABILITY", "CREDIT"),
            ("2310", "Utang PPh 23", "LIABILITY", "CREDIT"),
            ("2400", "Utang BPJS", "LIABILITY", "CREDIT"),
            ("2500", "Pendapatan diterima di muka", "LIABILITY", "CREDIT"),
            ("2600", "Utang komisi", "LIABILITY", "CREDIT"),
            ("2700", "Barang diterima belum ditagih (GRNI)", "LIABILITY", "CREDIT"),
            ("3100", "Modal disetor", "EQUITY", "CREDIT"),
            ("3200", "Saldo laba", "EQUITY", "CREDIT"),
            ("4100", "Pendapatan langganan", "REVENUE", "CREDIT"),
            ("4200", "Pendapatan instalasi", "REVENUE", "CREDIT"),
            ("4300", "Penjualan perangkat", "REVENUE", "CREDIT"),
            ("5100", "Harga pokok perangkat", "COGS", "DEBIT"),
            ("6100", "Beban gaji", "EXPENSE", "DEBIT"),
            ("6110", "Beban BPJS perusahaan", "EXPENSE", "DEBIT"),
            ("6120", "Beban komisi", "EXPENSE", "DEBIT"),
            ("6200", "Beban penyusutan", "EXPENSE", "DEBIT"),
            ("6300", "Beban selisih stok", "EXPENSE", "DEBIT"),
            ("6400", "Beban kerugian piutang", "EXPENSE", "DEBIT"),
        ]
        for code, name, atype, nbal in accounts:
            if not db.query(Account).filter_by(code=code).first():
                db.add(Account(code=code, name=name, account_type=atype, normal_balance=nbal))
        db.flush()

        # 2. Periode Fiskal
        for pcode, st in [("2026-10", "LOCKED"), ("2026-11", "OPEN"), ("2026-12", "OPEN")]:
            if not db.query(FiscalPeriod).filter_by(period_code=pcode).first():
                db.add(FiscalPeriod(period_code=pcode, status=st))

        # 3. Anggaran per Cost Center
        budgets = [
            ("CC-SCM", 2026, 250000000, 35000000, 35000000),
            ("CC-OPS", 2026, 180000000, 0, 7374515),
            ("CC-SALES", 2026, 90000000, 0, 40000),
            ("CC-HR", 2026, 60000000, 0, 0),
        ]
        for cc, yr, alloc, comm, real in budgets:
            if not db.query(Budget).filter_by(cost_center_code=cc, fiscal_year=yr).first():
                db.add(Budget(
                    cost_center_code=cc, fiscal_year=yr,
                    allocated_amount=alloc, committed_amount=comm, realized_amount=real,
                ))

        # 4. Demo Invoice Pak Andi (Tabel 2.25 Proposal Finance: Rp610.500)
        inv = db.query(Invoice).filter_by(invoice_no="INV-2026-000001").first()
        if not inv:
            inv = Invoice(
                invoice_no="INV-2026-000001",
                order_no="ORD-2026-000123",
                customer_code="CUS-000456",
                customer_name="Andi Pratama",
                business_line="HOME",
                billing_period="2026-11",
                subtotal=550000,
                discount=0,
                tax_amount=60500,
                total=610500,
                paid_amount=610500,
                virtual_account="8808000000001",
                referral_code="REF-EMP0017",
                monthly_price=400000,
                status="PAID",
            )
            db.add(inv)
            db.flush()

            # 6 Jurnal Lengkap Satu Order (Tabel 2.25: Total Debit = Kredit = Rp1.010.222)
            d = date(2026, 11, 18)
            post_journal(db, entry_date=d, source_type="INVOICE", source_id=inv.invoice_no, rule_code="AR-INV",
                         description="Invoice awal HOME-50 + Instalasi (Pak Andi)",
                         lines=[("1200", 610500, 0), ("2500", 0, 550000), ("2200", 0, 60500)], business_line="HOME")
            post_journal(db, entry_date=d, source_type="PAYMENT", source_id=inv.invoice_no, rule_code="AR-PAY",
                         description="Pembayaran Virtual Account INV-2026-000001",
                         lines=[("1100", 610500, 0), ("1200", 0, 610500)], business_line="HOME")
            post_journal(db, entry_date=d, source_type="ASSET_ONT", source_id="SN-ONT-2026-000001", rule_code="INV-ONT",
                         description="Pemasangan aset ONT di lokasi pelanggan (Pak Andi)",
                         lines=[("1500", 350000, 0), ("1300", 0, 350000)], business_line="HOME")
            post_journal(db, entry_date=d, source_type="REVENUE", source_id=inv.invoice_no, rule_code="REV-REC",
                         description="Pengakuan pendapatan langganan HOME-50 & instalasi",
                         lines=[("2500", 550000, 0), ("4100", 0, 400000), ("4200", 0, 150000)], business_line="HOME")
            post_journal(db, entry_date=d, source_type="COMMISSION", source_id=inv.invoice_no, rule_code="COM-FIN",
                         description="Insentif referral 10% bulan pertama (Budi EMP-0017)",
                         lines=[("6120", 40000, 0), ("2600", 0, 40000)], business_line="HOME")
            post_journal(db, entry_date=d, source_type="DEPRECIATION", source_id="SN-ONT-2026-000001-2026-11", rule_code="FA-DEP",
                         description="Penyusutan ONT bulan 1 (350.000 / 36 bulan)",
                         lines=[("6200", 9722, 0), ("1510", 0, 9722)], business_line="HOME")

        # 5. Tagihan Vendor PO-2026-0001 (Tabel 2.28: 100 ONT Rp35.000.000 + PPN Rp3.850.000)
        if not db.query(VendorBill).filter_by(bill_no="BIL-000001").first():
            db.add(VendorBill(
                bill_no="BIL-000001",
                po_no="PO-2026-0001",
                vendor_code="VEN-0001",
                subtotal=35000000,
                tax_amount=3850000,
                total=38850000,
                match_status="MATCHED",
                status="APPROVED",
            ))

        db.commit()
        print("[finance-api] Seed completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_finance()
