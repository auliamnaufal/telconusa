---
track: hrm
owner_team: Kelompok HRM
updated: '2026-11-25'
folders: [apps/hrm-web, services/hrm-api]
owns:
- {entity: Employee, id_format: EMP-0001}
- {entity: Department, id_format: DEP-01}
- {entity: ReferralCode, id_format: REF-EMP0017}
- {entity: ReferralRoster, id_format: pelanggan di bawah staf marketing}
- {entity: TechnicianAvailability, id_format: is_busy dan shift}
- {entity: PayrollRun, id_format: PAY-2026-11}
provides:
  api:
  - {id: POST /api/v1/auth/login, status: MOCKED, since: '2026-11-25'}
  - {id: GET /api/v1/auth/me, status: MOCKED, since: '2026-11-25'}
  - {id: GET /api/v1/employees/available, status: MOCKED, since: '2026-11-25'}
  - {id: 'GET /api/v1/employees/{employee_code}', status: MOCKED, since: '2026-11-25'}
  - {id: 'GET /api/v1/referrals/{code}', status: MOCKED, since: '2026-11-25'}
  - {id: POST /api/v1/referrals, status: MOCKED, since: '2026-11-25'}
  events: []
consumes:
  api: []
  events:
  - {id: referral.used, from: crm, status: PLANNED}
  - {id: technician.rated, from: crm, status: PLANNED}
  - {id: ticket.assigned, from: crm, status: PLANNED}
  - {id: ticket.resolved, from: crm, status: PLANNED}
---

# Track HRM

**Pemilik:** Kelompok HRM. **Folder:** `apps/hrm-web` (dashboard Internal HR dan Internal Karyawan), `services/hrm-api`.

## Lingkup

HRM memiliki karyawan, departemen, ketersediaan teknisi, kode referral staf marketing, dan penggajian. Semua akun staf dibuat oleh HR dan satu akun HRM dipakai untuk masuk ke seluruh modul internal. Penggajian, tunjangan operasional, insentif, dan perhitungan komisi marketing adalah tanggung jawab tim HRM bersama Finance dan **tidak** diatur oleh baseline.

## Slice requirements (acceptance untuk demo)

1. **Akun staf** dibuat HR dan bisa login (`POST /api/v1/auth/login`); token membawa `role`, `city_code`, `department`.
2. **Kode referral**: HR membuat kode untuk setiap staf marketing (`POST /api/v1/referrals`). `GET /api/v1/referrals/{code}` publik dan hanya mengembalikan nama staf dan status aktif.
3. **Daftar teknisi tersedia** (`GET /api/v1/employees/available`, scope `employees:read`) memfilter kota, status aktif, tidak cuti, dan menampilkan `is_busy`, `open_tickets`, `kpi_score`.
4. **Teknisi sibuk dan bebas**: `ticket.assigned` menandai teknisi sibuk; `ticket.resolved` membebaskannya.
5. **Roster referral**: `referral.used` mencatat pelanggan di bawah staf marketing yang bersangkutan, tampil di dashboard Internal HR. Aturan uang dan poin di luar baseline.
6. **Rating teknisi**: `technician.rated` disimpan sebagai salah satu indikator kinerja.
7. **Data karyawan** untuk layanan lain: `GET /api/v1/employees/{employee_code}` (scope `employees:read`).

## Integrasi

- Menyediakan: login, ketersediaan, data karyawan, validasi referral, pembuatan referral.
- Menerima event: `referral.used`, `ticket.assigned`, `ticket.resolved`, `technician.rated`.
- Hubungan HRM dengan Finance untuk biaya penggajian dan insentif mengikuti kesepakatan notulen: HRM mengelola penggajian, Finance mencatatnya sebagai pengeluaran. Event `payroll.approved` masih dikirim `shared/events.py` untuk sementara dan belum ada di `contracts/`; tim HRM dan Finance mendefinisikannya sendiri.

## Backlog

Temuan review `services/hrm-api` per 2026-11-25. **P0** dikerjakan lebih dulu.

| Prioritas | Temuan | Lokasi |
| :--- | :--- | :--- |
| P0 | `receive_event` menerima event tanpa tanda tangan; pakai `create_events_router`. Event `payroll.paid` palsu bisa mengubah status payroll. | `app/main.py` `receive_event` |
| P0 | `approve_payroll_hr` tanpa pemeriksaan status: bisa dipanggil ulang dan menerbitkan ulang `payroll.approved`, juga setelah `PAID`. | `approve_payroll_hr` |
| P1 | `GET /employees/available` tanpa autentikasi; ganti ke token layanan dengan scope `employees:read`. `is_available` boolean manual diganti `is_busy` dari event tiket, ditambah cuti dan shift. | `available_employees`, `toggle_availability` |
| P1 | `GET /referrals/{code}` mengembalikan jumlah pakai dan poin ke publik; kontrak hanya nama dan `is_active`. | `get_referral` |
| P1 | Handler event masih `commission.finalized` dan `referral.used` dengan hitungan insentif sendiri (`REFERRAL_INCENTIVE_RATE`). Tentukan pemilik hitungan bersama Finance; kontrak baru hanya `referral.used`. | `receive_event` |
| P1 | Tidak ada endpoint membuat karyawan atau akun staf oleh HR, persetujuan cuti, `employee.hired`, `employee.terminated`, `leave.approved`. | `app/main.py` |
| P2 | `PAYROLL_STAFF` termasuk `HR_ADMIN_ROLES` sehingga bisa absen atas nama orang lain dan mengubah ketersediaan; pisahkan hak. | `check_in`, `toggle_availability`, `shared/auth.py` |
| P2 | Slip gaji sementara berisi angka karangan (BPJS 4%, PPh 1,5%, transport Rp500.000) saat belum ada `PayrollItem`; tampilkan kosong. | `employee_self_service` |
| P2 | Pengajuan tenaga kerja bisa dibuat semua karyawan tanpa cek anggaran. | `create_requisition` |
| P2 | Kode `REQ-` dibuat dengan `count()+1`; pakai `shared.ids.next_code`. | `create_requisition` |
| P2 | `outbox_events` berstatus `SENT` sejak dibuat dan tidak ada relay; pakai `shared.outbox`. | `models.py`, `approve_payroll_hr` |

## Di luar baseline (milik tim HRM)

Perhitungan payroll (gaji pokok, tunjangan operasional, insentif, BPJS, PPh 21, lembur), persetujuan dua tahap HR dan Finance, slip gaji, aturan insentif marketing berdasarkan penggunaan kode referral, rekrutmen, jadwal, absensi, cuti, lembur, sertifikat, kedisiplinan. Catatan notulen: ketentuan perhitungan insentif marketing masih dibahas.

## Open items

- Ketentuan insentif marketing dari penggunaan kode referral (notulen, catatan diskusi berikutnya).
- Rincian komponen gaji (notulen B3) dibuat tim HRM.

## Requests

_Belum ada. Tim lain menambah baris `- dari <track>, <tanggal>: <permintaan>` lewat PR._

## Decisions

- 2026-11-25: akun staf dibuat HR; referral dicatat di HRM sebagai dasar poin kinerja; baseline tidak mengatur payroll atau tunjangan.

## Cara membaca status

| Status | Arti untuk yang disediakan | Arti untuk yang dikonsumsi |
| :--- | :--- | :--- |
| `PLANNED` | Ada di kontrak, belum ada contoh atau implementasi | Belum diintegrasikan |
| `MOCKED` | Contoh respons atau event ada di `contracts/` dan bisa dipakai lewat mock | Sudah diintegrasikan terhadap mock |
| `LIVE` | Sudah diimplementasikan dan lolos tes (`test:` wajib diisi) | Sudah diintegrasikan terhadap layanan asli |
| `CHANGING` | Kontrak sedang diubah; baca bagian Decisions | Sedang menyesuaikan |
| `DEPRECATED` | Akan dihapus; pakai penggantinya | Harus pindah |

Hanya tim pemilik yang mengubah file ini. Tim lain menulis permintaan di bagian **Requests** lewat PR. Setelah mengubah front matter, jalankan `python tools/check_contracts.py` agar `tracks/STATUS.md` ikut diperbarui.
