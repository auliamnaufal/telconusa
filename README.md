# TelcoNusa Platform

Monorepo sistem integrasi aplikasi korporasi untuk **PT TelkoNusa Digital** (UAS Mata Kuliah Integrasi Aplikasi Korporasi — S1 Teknologi Sains Data, Universitas Airlangga).

Repository ini menyatukan empat divisi operasional (**CRM**, **HRM**, **SCM**, **Finance**) dalam satu tumpukan Docker dengan prinsip pemisahan data per layanan (*database-per-service*). Setiap divisi memiliki aplikasi frontend, REST API, skema MySQL, dan migrasi database masing-masing, lalu berkomunikasi melalui panggilan HTTP internal dan event webhook bertanda tangan HMAC yang dikirim lewat outbox.

---

## Mulai dari Sini

| Baca | Untuk apa |
| :--- | :--- |
| [`CONTEXT.md`](CONTEXT.md) | Gambaran bersama: aturan, alur demo, keputusan, jadwal |
| `tracks/<crm\|hrm\|scm\|finance>.md` | Lingkup, kriteria penerimaan, backlog, dan status integrasi track Anda |
| [`tracks/STATUS.md`](tracks/STATUS.md) | Status semua track dalam satu tabel (dibuat otomatis) |
| [`contracts/README.md`](contracts/README.md) | Kontrak API dan event, serta cara mengubahnya |
| [`AGENTS.md`](AGENTS.md) | Aturan untuk agen pemrograman (`CLAUDE.md` hanya mengimpornya) |
| [`mock/README.md`](mock/README.md) | Cara memakai mock untuk modul yang belum jadi |

Baseline menyediakan fondasi ini saja. Logika bisnis tiap modul dikerjakan timnya masing-masing di atas fondasi tersebut.

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
- `services/shared/` — helper autentikasi JWT dan layanan, penerima dan pengirim event (outbox), ID, dan transisi status.
- `contracts/` — OpenAPI, skema event, contoh event, dan `variable_standards.md` (standar penamaan, ID, status, role, parameter bersama).
- `docker-compose.yml`, `.env.example`, dan `mysql/init/` — definisi container, port, jaringan, secret, dan inisialisasi skema database.
- `CONTEXT.md`, `AGENTS.md`, `.github/`, dan `tools/` — dokumen bersama, CI, dan alat pemeriksa.

---

## Struktur Direktori

```text
telconusa-platform/
├── CONTEXT.md                    # Gambaran bersama, aturan, alur demo, keputusan
├── AGENTS.md / CLAUDE.md         # Aturan untuk agen pemrograman
├── docker-compose.yml            # Orkestrasi MySQL, 4 API, 5 web app, dan profil mock
├── .env.example                  # Template environment variable (secret diisi tools/setup-env.sh)
├── contracts/                    # Kontrak lintas track
│   ├── variable_standards.md     # Standar variabel, ID, status, role
│   ├── openapi/                  # API per track
│   ├── events/                   # Skema event
│   └── examples/events/          # Contoh event
├── tracks/                       # Lingkup dan status per track + STATUS.md otomatis
├── tools/                        # Pemeriksa kontrak, pemeriksa atribusi git, hook, send_fixture, setup-env
├── mock/                         # Catatan penggunaan mock
├── tests/                        # Tes pustaka bersama dan tools
├── mysql/
│   └── init/                     # Script inisialisasi 4 skema MySQL
├── services/
│   ├── shared/                   # Modul Python bersama (auth, event, outbox, ID, status)
│   ├── _template/                # Titik awal modul baru
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
tools/setup-env.sh          # membuat .env dan mengisi JWT_SECRET dan HMAC_WEBHOOK_SECRET
tools/install-hooks.sh      # memasang hook commit-msg
docker compose up -d --build
```

Layanan menolak berjalan bila `JWT_SECRET` atau `HMAC_WEBHOOK_SECRET` kosong atau masih berisi nilai contoh.

Untuk menjalankan hanya layanan Anda dan memakai mock bagi track lain, lihat [`mock/README.md`](mock/README.md).

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
2. Jalankan `tools/setup-env.sh` untuk membuat `.env` (secret diisi otomatis). Event dikirim lewat webhook; tidak butuh RabbitMQ.
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

---

## Arsitektur Autentikasi dan Integrasi Antar-Divisi

### Autentikasi
- **Pelanggan** dikelola oleh `crm-api` (`/api/v1/auth/register` dan `/api/v1/auth/login`) untuk akses `:3000`. Pemesanan di `:3000/order` mewajibkan akun pelanggan yang sudah login; layanan CS publik tetap tersedia tanpa login melalui `POST /api/v1/public/support`.
- **Karyawan** menggunakan **satu akun terpusat** yang dikelola oleh `hrm-api` (`/api/v1/auth/login`). Hak akses tiap portal internal (`:3001`–`:3004`) dibatasi berdasarkan `role` pada payload JWT, sedangkan seluruh karyawan tetap dapat membuka Portal Karyawan (ESS) di `:3002/karyawan`.

### Alur Integrasi Lintas Layanan

Alur demo kanonik (sepuluh langkah, setiap langkah dengan pemilik, API atau event, dan perubahan status) ada di [`CONTEXT.md` bagian 5](CONTEXT.md). Kontrak API dan event ada di `contracts/`. Daftar event dan API lama yang masih dipakai kode modul, beserta penggantinya, ada di [`CONTEXT.md` bagian 9](CONTEXT.md).

Kode modul belum seluruhnya mengikuti alur kanonik tersebut. Selisihnya dicatat sebagai backlog di `tracks/<track>.md`.

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
6. **Tidak ada agen pemrograman sebagai kontributor.** Commit, PR, dan catatan git lain tidak boleh mencantumkan agen pemrograman (Claude, Codex, Copilot, Cursor, Gemini, dan sejenisnya) sebagai author atau co-author, dan tidak boleh memuat trailer atau kalimat atribusi untuk agen tersebut. Jalankan `tools/install-hooks.sh`; CI juga memeriksanya.
7. **Perubahan kontrak atau status integrasi** ikut memperbarui `tracks/<track>.md`; jalankan `python tools/check_contracts.py` sebelum membuka PR.

---

## Catatan Sebelum Push Pertama & Troubleshooting

- **File `.env` tidak boleh di-commit** (sudah masuk `.gitignore`). Perubahan konfigurasi baru cukup didokumentasikan di `.env.example`.
- **Cache Next.js lokal:** Jika ada anggota yang menjalankan `npm run dev` di luar Docker pada folder selain `apps/web`, pastikan folder `.next/` tidak ikut masuk staging Git (`git status` sebelum commit).
- **Port bentrok saat `docker compose up`:** Pastikan tidak ada proses MySQL (`3306`), Python (`8001`–`8004`), atau Node (`3000`–`3004`) lain yang sedang memakai port yang sama di mesin lokal.
- **Melihat log error service tertentu:**
  ```bash
  docker compose logs -f crm-api
  docker compose logs -f web
  ```
