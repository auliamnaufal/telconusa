# TelcoNusa Platform

Monorepo sistem integrasi aplikasi korporasi untuk **PT TelkoNusa Digital** (UAS Mata Kuliah Integrasi Aplikasi Korporasi — S1 Teknologi Sains Data, Universitas Airlangga).

Repository ini menyatukan empat divisi operasional (**CRM**, **HRM**, **SCM**, **Finance**) dalam satu tumpukan Docker dengan prinsip pemisahan data per layanan (*database-per-service*). Setiap divisi memiliki aplikasi frontend, REST API, skema MySQL, dan migrasi database masing-masing, lalu berkomunikasi melalui panggilan HTTP internal serta event bus (RabbitMQ + webhook bertanda tangan HMAC).

---

## Pembagian Modul dan Kepemilikan Tim

Setiap kelompok bertanggung jawab penuh atas folder frontend dan backend divisinya masing-masing.

| Kelompok / Divisi | Frontend | Backend | Skema Database | Port Web / API |
| :--- | :--- | :--- | :--- | :--- |
| **CRM** | `apps/web/`, `apps/crm-web/` | `services/crm-api/` | `telconusa_crm` | `3000`, `3001` / `8001` |
| **HRM** | `apps/hrm-web/` | `services/hrm-api/` | `telconusa_hrm` | `3002` / `8002` |
| **SCM** | `apps/scm-web/` | `services/scm-api/` | `telconusa_scm` | `3003` / `8003` |
| **Finance** | `apps/finance-web/` | `services/finance-api/` | `telconusa_finance` | `3004` / `8004` |

### Area Bersama (Perlu Kesepakatan 4 Kelompok)
Perubahan pada path berikut berdampak langsung ke seluruh divisi dan **tidak boleh diubah sepihak**:
- `services/shared/` — helper autentikasi JWT, role guard, konfigurasi env, serta publisher/daftar subscriber event.
- `contracts/variable_standards.md` — standar penamaan variabel, format kode entitas, dan parameter bisnis bersama (PPN 11%, insentif referral 10%, dsb.).
- `docker-compose.yml` dan `mysql/init/` — definisi container, port, jaringan, dan inisialisasi skema database.

---

## Struktur Direktori

```text
telconusa-platform/
├── docker-compose.yml            # Orkestrasi MySQL, RabbitMQ, 4 API, dan 5 web app
├── .env.example                  # Template environment variable
├── contracts/
│   └── variable_standards.md     # Kontrak data dan standar variabel lintas divisi
├── mysql/
│   └── init/                     # Script inisialisasi 4 skema MySQL
├── services/
│   ├── shared/                   # Modul Python bersama (auth JWT, event bus, schema)
│   ├── crm-api/                  # FastAPI + Alembic + seed (Port 8001)
│   ├── hrm-api/                  # FastAPI + Alembic + seed (Port 8002)
│   ├── scm-api/                  # FastAPI + Alembic + seed (Port 8003)
│   └── finance-api/              # FastAPI + Alembic + seed (Port 8004)
└── apps/
    ├── web/                      # Website pelanggan personal, CS 24/7, MyTelcoNusa (Port 3000)
    ├── crm-web/                  # Portal internal Manajer CRM, CS, Marketing, Teknisi (Port 3001)
    ├── hrm-web/                  # Portal Karyawan (ESS) dan Workspace HR/Payroll (Port 3002)
    ├── scm-web/                  # Control Tower SCM, gudang, kit teknisi, PO (Port 3003)
    └── finance-web/              # Finance Suite: AR/VA, AP, jurnal GL, neraca saldo (Port 3004)
```

---

## Menjalankan Aplikasi

### Prasyarat
- Docker Desktop (dengan Docker Compose v2)
- Git

### 1. Menjalankan Seluruh Stack (Docker)

```bash
cp .env.example .env
docker compose up -d --build
```

Saat container backend pertama kali naik, masing-masing service otomatis menjalankan `alembic upgrade head` dan `python -m app.seed` secara idempoten.

Cek status seluruh container:

```bash
docker compose ps
```

### 2. Rebuild Hanya Divisi Sendiri Saat Pengembangan

Setelah seluruh stack berjalan, masing-masing kelompok cukup me-rebuild layanan miliknya agar waktu build lebih singkat:

```bash
# Kelompok CRM
docker compose up -d --build crm-api web crm-web

# Kelompok HRM
docker compose up -d --build hrm-api hrm-web

# Kelompok SCM
docker compose up -d --build scm-api scm-web

# Kelompok Finance
docker compose up -d --build finance-api finance-web
```

### 3. Reset Total Database (Jika Skema / Seed Perlu Diulang)

```bash
docker compose down -v
docker compose up -d --build
```

### 4. Menjalankan Lokal Tanpa Docker (Opsional per Service)

1. Pastikan MySQL 8.0 lokal aktif dan jalankan script di `mysql/init/`.
2. Salin `.env.example` menjadi `.env`, lalu ubah `EVENT_TRANSPORT=webhook` bila tidak menjalankan RabbitMQ lokal.
3. Jalankan backend (contoh `crm-api`):
   ```bash
   cd services/crm-api
   pip install -r requirements.txt
   alembic upgrade head
   python -m app.seed
   uvicorn app.main:app --reload --port 8001
   ```
4. Jalankan frontend divisi terkait (contoh `apps/crm-web`):
   ```bash
   cd apps/crm-web
   npm install
   npm run dev
   ```

---

## Daftar URL Layanan

### Aplikasi Web
| Layanan | URL | Peruntukan |
| :--- | :--- | :--- |
| Website Pelanggan & MyTelcoNusa | `http://localhost:3000` | Katalog personal, cek cakupan, layanan CS 24/7 (`/bantuan`), registrasi (`/register`), order (`/order`), portal pelanggan (`/portal`) |
| Portal Internal CRM | `http://localhost:3001` | Login staf CRM/Teknisi (`/login`), operasional Manajer/CS/Marketing (`/manager`), dispatch teknisi (`/teknisi`) |
| Portal Karyawan & HRM | `http://localhost:3002` | Login terpusat karyawan, ESS (`/karyawan`), administrasi HR & Payroll (`/hr`) |
| SCM Control Tower | `http://localhost:3003` | Inventaris gudang, kit instalasi, pengadaan/PO, goods receipt |
| Finance Suite | `http://localhost:3004` | Invoice & Virtual Account (AR), vendor bill (AP), buku besar, trial balance |

### API Documentation & Infrastruktur
- CRM API Swagger: `http://localhost:8001/docs`
- HRM API Swagger: `http://localhost:8002/docs`
- SCM API Swagger: `http://localhost:8003/docs`
- Finance API Swagger: `http://localhost:8004/docs`
- RabbitMQ Management: `http://localhost:15672` (user: `telconusa`, pass: `telconusa123`)

---

## Arsitektur Autentikasi dan Integrasi Antar-Divisi

### Autentikasi
- **Pelanggan** dikelola oleh `crm-api` (`/api/v1/auth/register` dan `/api/v1/auth/login`) untuk akses `:3000`. Pemesanan di `:3000/order` mewajibkan akun pelanggan yang sudah login; layanan CS publik tetap tersedia tanpa login melalui `POST /api/v1/public/support`.
- **Karyawan** menggunakan **satu akun terpusat** yang dikelola oleh `hrm-api` (`/api/v1/auth/login`). Hak akses tiap portal internal (`:3001`–`:3004`) dibatasi berdasarkan `role` pada payload JWT, sedangkan seluruh karyawan tetap dapat membuka Portal Karyawan (ESS) di `:3002/karyawan`.

### Alur Integrasi Lintas Layanan
| Sumber -> Tujuan | Mekanisme | Deskripsi Singkat |
| :--- | :--- | :--- |
| CRM -> SCM | HTTP Sync | Cek ketersediaan stok `ONT-01` saat checkout (`ON_HOLD` jika stok habis) dan ambil checklist kit teknisi |
| CRM -> HRM | HTTP Sync | Validasi kode referral karyawan saat checkout dan ambil daftar teknisi yang tersedia |
| CRM -> Finance | Event (`order.confirmed`) | Finance menerbitkan invoice + VA dan memposting jurnal `AR-INV` secara otomatis |
| Finance -> CRM | Event (`invoice.issued`, `invoice.paid`) | Status order di CRM otomatis diperbarui ke `AWAITING_PAYMENT` lalu `PAID` |
| CRM -> Finance | HTTP Sync | `GET /api/v1/portal/me` mengambil daftar invoice dan nomor VA pelanggan secara langsung dari Finance |
| CRM -> SCM & HRM | Event (`workorder.assigned`, `kit.reconciled`, `technician.rated`) | Sinkronisasi penugasan teknisi, rekonsiliasi perangkat/kabel, dan pencatatan rating teknisi di HRM |
| Finance -> HRM | Event (`commission.finalized`, `payroll.paid`) | Mencatat komisi referral 10% saat invoice lunas dan memperbarui status pembayaran gaji |
| SCM -> Finance -> SCM | Event (`po.approved`, `goods.received`, `vendor.paid`) | Pembuatan tagihan vendor (AP), three-way match, dan sinkronisasi pelunasan PO |
| HRM -> Finance | Event (`payroll.approved`) | Posting jurnal beban gaji, BPJS, dan PPh 21 |

Detail skema variabel dan payload dapat dilihat pada `contracts/variable_standards.md` dan `services/shared/events.py`.

---

## Akun Pengujian (Seed Data)

Password default seluruh akun seed: `telconusa123`

### Akun Pelanggan (`http://localhost:3000/login`)
| Nama | Kode | Email | Catatan |
| :--- | :--- | :--- | :--- |
| Andi Pratama | `CUS-000456` | `andi@gmail.com` | Memiliki langganan aktif `HOME-50` dan riwayat instalasi |

### Akun Karyawan Internal (`:3001`–`:3004`)
| Role | Kode | Email | Portal Utama |
| :--- | :--- | :--- | :--- |
| `DIRECTOR` | `EMP-0001` | `direktur@telconusa.id` | Seluruh portal internal (`:3001`–`:3004`) |
| `CRM_MANAGER` | `EMP-0010` | `crm.manager@telconusa.id` | `:3001/manager`, `:3002/karyawan` |
| `MARKETING` | `EMP-0017` | `budi@telconusa.id` | `:3001/manager`, `:3002/karyawan` (kode referral: `REF-EMP0017`) |
| `TECHNICIAN` | `EMP-0042` | `rina@telconusa.id` | `:3001/teknisi`, `:3002/karyawan` |
| `HR_MANAGER` | `EMP-0040` | `hr.manager@telconusa.id` | `:3002/hr`, `:3002/karyawan` |
| `SCM_MANAGER` | `EMP-0020` | `scm.manager@telconusa.id` | `:3003`, `:3002/karyawan` |
| `FINANCE_MANAGER` | `EMP-0030` | `finance.manager@telconusa.id` | `:3004`, `:3002/karyawan` |

---

## Alur Kerja Git (4 Kelompok)

1. **Jangan push langsung ke `main`.** Aktifkan *Branch Protection* pada branch `main` di GitHub agar setiap perubahan wajib melalui Pull Request.
2. **Buat branch dari `main` dengan prefiks divisi:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b finance/tambah-filter-aging
   ```
   Format penamaan branch: `crm/<fitur>`, `hrm/<fitur>`, `scm/<fitur>`, `finance/<fitur>`.
3. **Patuhi batas folder divisi.** Hindari menyentuh folder milik kelompok lain agar tidak menimbulkan merge conflict.
4. **Uji perubahan sebelum membuka Pull Request:**
   - Pastikan container divisi Anda berjalan tanpa error (`docker compose logs <service>`).
   - Jika fitur menyentuh alur lintas divisi, uji sampai ke service penerima event.
5. **Perubahan di area bersama** (`services/shared/`, `contracts/`, `docker-compose.yml`, `mysql/init/`) dibuat di PR terpisah dengan persetujuan perwakilan 4 kelompok sebelum di-merge.

---

## Catatan Sebelum Push Pertama & Troubleshooting

- **File `.env` tidak boleh di-commit** (sudah masuk `.gitignore`). Perubahan konfigurasi baru cukup didokumentasikan di `.env.example`.
- **Cache Next.js lokal:** Jika ada anggota yang menjalankan `npm run dev` di luar Docker pada folder selain `apps/web`, pastikan folder `.next/` tidak ikut masuk staging Git (`git status` sebelum commit).
- **Port bentrok saat `docker compose up`:** Pastikan tidak ada proses MySQL (`3306`), RabbitMQ (`5672`/`15672`), Python (`8001`–`8004`), atau Node (`3000`–`3004`) lain yang sedang memakai port yang sama di mesin lokal.
- **Melihat log error service tertentu:**
  ```bash
  docker compose logs -f crm-api
  docker compose logs -f web
  ```
