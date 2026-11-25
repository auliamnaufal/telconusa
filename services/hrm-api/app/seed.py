from datetime import date
from sqlalchemy.orm import Session
from shared.auth import hash_password
from app.database import SessionLocal
from app.models import (
    Attendance, Department, Employee, JobRequisition,
    PayrollItem, PayrollRun, ReferralCode, ReferralUsage, TechnicianRatingLog,
)


def seed_hrm() -> None:
    db: Session = SessionLocal()
    try:
        # 1. Departemen & Cost Center
        depts = [
            ("DEP-DIR", "Direksi", "CC-DIR"),
            ("DEP-SALES", "Penjualan & Marketing", "CC-SALES"),
            ("DEP-OPS", "Operasional & Teknisi", "CC-OPS"),
            ("DEP-SCM", "Rantai Pasok (SCM)", "CC-SCM"),
            ("DEP-FIN", "Keuangan (Finance)", "CC-FIN"),
            ("DEP-HR", "SDM (HRM)", "CC-HR"),
        ]
        for code, name, cc in depts:
            if not db.query(Department).filter_by(code=code).first():
                db.add(Department(code=code, name=name, cost_center_code=cc))
        db.flush()

        # 2. Seed Karyawan Utama (Sesuai Skenario Demo Blueprint + Semua Role)
        pw = hash_password("telconusa123", salt="telconusa_seed_salt")
        employees = [
            ("EMP-0001", "Hendra Wijaya", "direktur@telconusa.id", "DEP-DIR", "DIRECTOR", "JKT", "OFFICE", 25000000, 5000000, "K/2", None, True, 96.0),
            ("EMP-0010", "Dewi Lestari", "crm.manager@telconusa.id", "DEP-SALES", "CRM_MANAGER", "JKT", "OFFICE", 12000000, 2500000, "K/1", "EMP-0001", True, 91.5),
            ("EMP-0017", "Budi Santoso", "budi@telconusa.id", "DEP-SALES", "MARKETING", "BDG", "OFFICE", 5500000, 1000000, "TK/0", "EMP-0010", True, 92.0),
            ("EMP-0020", "Raka Pratama", "scm.manager@telconusa.id", "DEP-SCM", "SCM_MANAGER", "JKT", "OFFICE", 12000000, 2000000, "K/1", "EMP-0001", True, 89.0),
            ("EMP-0030", "Mirza Muhyidin", "finance.manager@telconusa.id", "DEP-FIN", "FINANCE_MANAGER", "JKT", "OFFICE", 13000000, 2500000, "TK/0", "EMP-0001", True, 94.0),
            ("EMP-0040", "Nadia Kusuma", "hr.manager@telconusa.id", "DEP-HR", "HR_MANAGER", "JKT", "OFFICE", 12000000, 2000000, "K/0", "EMP-0001", True, 90.0),
            ("EMP-0042", "Rina Kartika", "rina@telconusa.id", "DEP-OPS", "TECHNICIAN", "BDG", "MORNING", 5000000, 1000000, "TK/0", "EMP-0010", True, 95.0),
            ("EMP-0043", "Doni Saputra", "doni@telconusa.id", "DEP-OPS", "TECHNICIAN", "BDG", "MORNING", 5000000, 1000000, "TK/0", "EMP-0010", False, 82.0),
            ("EMP-0044", "Fajar Nugroho", "fajar@telconusa.id", "DEP-OPS", "TECHNICIAN", "SBY", "MORNING", 5000000, 1000000, "K/0", "EMP-0010", True, 88.5),
        ]
        for code, name, email, dept, role, city, shift, base, allow, ptkp, mgr, avail, kpi in employees:
            if not db.query(Employee).filter_by(employee_code=code).first():
                db.add(Employee(
                    employee_code=code, full_name=name, email=email, password_hash=pw,
                    department_code=dept, role=role, city_code=city, shift_name=shift,
                    base_salary=base, allowance=allow, ptkp_status=ptkp, manager_code=mgr,
                    is_available=avail, kpi_score=kpi,
                ))
        db.flush()

        # 3. Kode Referral Staf Marketing Budi (Notulen PDF B.6-7)
        if not db.query(ReferralCode).filter_by(code="REF-EMP0017").first():
            db.add(ReferralCode(code="REF-EMP0017", employee_code="EMP-0017", total_uses=1, total_kpi_points=10))
            db.flush()
            db.add(ReferralUsage(
                referral_code="REF-EMP0017",
                order_no="ORD-2026-000123",
                monthly_price=400000,
                incentive_amount=40000,
                points_awarded=10,
            ))

        # 4. Log Rating Teknisi Rina dari CRM (Notulen PDF B.5)
        if not db.query(TechnicianRatingLog).filter_by(work_order_code="WO-000001").first():
            db.add(TechnicianRatingLog(
                work_order_code="WO-000001",
                technician_employee_id="EMP-0042",
                rating_score=5,
                rating_comment="Teknisi Rina sangat ramah, rapi, dan kecepatan langsung 52 Mbps!",
            ))

        # 5. Absensi Hari Ini
        if not db.query(Attendance).filter_by(employee_code="EMP-0042", attendance_date=date(2026, 11, 25)).first():
            db.add(Attendance(employee_code="EMP-0042", attendance_date=date(2026, 11, 25), check_in_time="06:55", status="PRESENT", gps_location="-6.8842,107.6138 (Bandung)"))
            db.add(Attendance(employee_code="EMP-0017", attendance_date=date(2026, 11, 25), check_in_time="07:58", status="PRESENT", gps_location="Kantor Cabang Bandung"))

        # 6. Pengajuan Tenaga Kerja (Notulen PDF B.2)
        if not db.query(JobRequisition).filter_by(req_code="REQ-2026-001").first():
            db.add(JobRequisition(req_code="REQ-2026-001", department_code="DEP-OPS", position_title="Teknisi Fiber Optik (Area Surabaya)", headcount=2, status="OPEN"))

        # 7. Payroll Run Contoh Rina (Sesuai Tabel 2.29 Proposal Finance: Total Biaya Rp7.374.515)
        pr = db.query(PayrollRun).filter_by(payroll_period="2026-11").first()
        if not pr:
            pr = PayrollRun(
                payroll_period="2026-11",
                total_gross=6760115,
                total_bpjs_company=614400,
                total_pph21=87906,
                total_net=6432209,
                total_company_cost=7374515,
                status="HR_APPROVED",
            )
            db.add(pr)
            db.flush()
            db.add(PayrollItem(
                payroll_run_id=pr.id,
                employee_code="EMP-0042",
                base_salary=5000000,
                allowance=1000000,
                transport_meal=500000,
                overtime_pay=260115,
                incentive_amount=0,
                gross_salary=6760115,
                bpjs_employee=240000,
                bpjs_company=614400,
                pph21_amount=87906,
                net_salary=6432209,
            ))

        db.commit()
        print("[hrm-api] Seed completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_hrm()
