# Standar Variabel dan Kontrak Data — PT TelkoNusa Digital

Dokumen ini adalah kesepakatan penamaan, format, enum, dan status yang berlaku di semua track (CRM, HRM, SCM, Finance). Sumbernya: Blueprint Integrasi, notulen diskusi, dan keputusan rapat yang dicatat di [`CONTEXT.md`](../CONTEXT.md). Bila dokumen ini bertentangan dengan kode lama, dokumen ini yang benar dan kode lama masuk `Backlog` di `tracks/<track>.md`.

Kontrak yang bisa dibaca mesin ada di folder yang sama: `openapi/` (API), `events/` (skema event), `examples/events/` (contoh event lengkap). Cara mengubahnya ada di [`README.md`](README.md).

---

## 1. Konvensi Global

| Aturan | Standar | Contoh |
| :--- | :--- | :--- |
| Gaya penamaan | `snake_case` untuk JSON dan kolom MySQL | `customer_id`, `install_address` |
| Primary key internal | `CHAR(36)` UUIDv4, ditambah kode bisnis unik | `id`, `order_no` |
| Kode bisnis | Dibuat dari sequence di database (`shared/ids.py`), bukan `count()+1` | `ORD-2026-000001` |
| Uang | `BIGINT` rupiah bulat, tanpa desimal | `400000` |
| Waktu | ISO 8601 zona WIB `+07:00` | `"2026-11-25T16:30:00+07:00"` |
| Periode bulanan | `CHAR(7)` `YYYY-MM` | `"2026-11"` |
| Pelacakan | Header `X-Correlation-Id` diteruskan di setiap panggilan dan event | `"ORD-2026-000125"` |
| Idempotensi | Header `Idempotency-Key` pada `POST` yang membuat transaksi | `"ORD-2026-000125-inv-1"` |
| Optimistic locking | Kolom `version INT DEFAULT 1` di tabel transaksi | `version: 1` |
| Prefix API | `/api/v1`; perubahan yang merusak lewat `/api/v2` | `/api/v1/orders` |
| Paginasi | `?page=1&limit=20` | |
| Galat | Format baku di bawah | |

Format galat:

```json
{ "error": { "code": "INSUFFICIENT_STOCK", "message": "Stok ONT-01 di gudang Bandung tidak cukup",
             "details": { "sku": "ONT-01", "requested": 1, "available": 0 }, "correlation_id": "ORD-2026-000123" } }
```

Kode status: 200/201 berhasil, 202 diterima dan diproses nanti, 400/422 data salah, 401/403 tidak berhak, 404 tidak ada, 409 bentrok status atau duplikat (termasuk `INVALID_TRANSITION`), 429 terlalu sering, 5xx gangguan server.

## 2. Format ID Bisnis

| Entitas | Format | Pemilik |
| :--- | :--- | :--- |
| Pelanggan | `CUS-000001` | CRM |
| Alamat pemasangan | `ADR-000001` | CRM |
| Order | `ORD-2026-000001` | CRM |
| Langganan (satu paket di satu alamat) | `SUB-000001` | CRM |
| Tiket (pemasangan, maintenance, keluhan) | `TKT-000001` | CRM |
| Karyawan | `EMP-0001` | HRM |
| Kode referral staf marketing | `REF-EMP0017` atau kode custom | HRM |
| Periode payroll | `PAY-2026-11` | HRM |
| Permintaan barang dari tiket | `SR-2026-000001` | SCM |
| Permintaan pembelian | `PR-2026-0001` | SCM |
| Purchase order / goods receipt | `PO-2026-0001` / `GR-2026-0001` | SCM |
| Nomor seri ONT | `SN-ONT-2026-000001` | SCM |
| Invoice / pembayaran / jurnal | `INV-2026-000001` / `PMT-000001` / `JE-000001` | Finance |

`WorkOrder` (`WO-…`) dan `installation_status` dari kode lama digantikan oleh `Ticket` dan label turunan `installation_label` (bagian 4).

## 3. Autentikasi dan Hak Akses

- **Pengguna** memakai JWT dengan `sub`, `role`, `name`. Karyawan login di HRM (satu akun terpusat, dibuat oleh HR). Pelanggan login di CRM dengan `role = CUSTOMER`.
- **Antar-layanan** memakai JWT layanan: `role = SERVICE`, `sub = svc:<track>`, `scopes = [...]`, umur pendek (`shared/service_auth.py`). Nama scope `<sumber_daya>:<aksi>`, contoh `stock:read`, `invoices:read`, `employees:read`.
- Setiap operasi di `openapi/*.yaml` menyatakan `x-auth` (`public`, `user`, atau `service`), `x-roles` untuk `user`, dan `x-scope` untuk `service`. Endpoint antar-layanan tidak boleh tanpa autentikasi.
- Secret (`JWT_SECRET`, `HMAC_WEBHOOK_SECRET`) wajib diisi di `.env` dan tidak boleh berisi nilai bawaan. Jalankan `tools/setup-env.sh`.
- Pengiriman event ditandatangani HMAC-SHA256 pada body mentah (`X-TelcoNusa-Signature`). Penerima **wajib menolak** event tanpa tanda tangan atau dengan tanda tangan salah (`shared/event_receiver.py`).

Role pengguna (`role` di JWT):

| Kelompok | Role |
| :--- | :--- |
| Pelanggan | `CUSTOMER` |
| CRM | `CRM_MANAGER`, `CS_AGENT`, `TECHNICIAN`, `MARKETING`, `SALES_EXEC`, `SALES_MANAGER` |
| HRM | `HR_MANAGER`, `HR_STAFF`, `PAYROLL_STAFF` |
| SCM | `SCM_MANAGER`, `WAREHOUSE_STAFF`, `PROCUREMENT_STAFF` |
| Finance | `FINANCE_MANAGER`, `ACCOUNTANT`, `AR_STAFF`, `AP_STAFF` |
| Direksi | `DIRECTOR` (akses baca seluruh dashboard) |

Pembagian hak akses CRM yang berlaku sekarang: pelanggan memesan, memantau, mengajukan keluhan, memberi rating; teknisi hanya melihat tiket yang ditugaskan kepadanya; manajer CRM (dan `DIRECTOR`) menugaskan teknisi; `CS_AGENT` menerima keluhan dan membuat tiket. Hak `MARKETING` di CRM belum ditentukan (catatan notulen) dan untuk sementara tidak ada.

## 4. Status Baku dan Pemiliknya

Setiap status hanya boleh diubah oleh modul pemiliknya. Modul lain meminta lewat API atau bereaksi pada event. Transisi yang sah ada di `services/shared/transitions.py`; transisi lain ditolak dengan `409 INVALID_TRANSITION`.

| Entitas | Pemilik | Alur normal | Pengecualian |
| :--- | :--- | :--- | :--- |
| Order | CRM | `SUBMITTED → AWAITING_PAYMENT → PAID → COMPLETED` | `CANCELLED` |
| Langganan | CRM | `PENDING → ACTIVE → TERMINATED` | `SUSPENDED`, `CANCELLED` |
| Tiket | CRM | `OPEN → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED` | `REOPENED`, `CANCELLED` |
| Invoice | Finance | `DRAFT → ISSUED → PARTIALLY_PAID → PAID` | `OVERDUE`, `VOID`, `CREDITED` |
| Permintaan barang | SCM | `REQUESTED → READY_TO_ISSUE → ISSUED → RETURNED` | `PENDING_STOCK`, `CANCELLED` |
| Unit barang bernomor seri | SCM | `IN_STOCK → RESERVED → WITH_TECHNICIAN → INSTALLED → RETURNED` | `FAULTY`, `LOST`, `WRITTEN_OFF` |

Aturan khusus:

- **`PENDING_STOCK` milik SCM.** Status tiket tidak berubah karena stok kurang. CRM menampilkan `materials_status` sebagai bidang baca-saja yang diperbarui dari event `stockrequest.*` dan `stock.*`. Nilainya: `NOT_REQUESTED`, `REQUESTED`, `READY_TO_ISSUE`, `PENDING_STOCK`, `ISSUED`, `RETURNED`.
- **`WITH_TECHNICIAN` hanya diubah staf SCM** saat barang dikeluarkan, bukan oleh teknisi.
- **`installation_label`** adalah label baca-saja untuk pelanggan, diturunkan CRM dari status tiket: `OPEN` → *Menunggu penugasan*; `ASSIGNED` dan `IN_PROGRESS` → *Sedang diproses*; `RESOLVED` dan `CLOSED` → *Selesai*. Ini bukan status baru.
- **Invoice dibuat Finance** sebagai `DRAFT`, dikirim staf AR (`ISSUED`), lalu pembayaran dicek ulang dan dikonfirmasi staf AR (`PAID`). CRM tidak membuat atau mengubah invoice.

## 5. Kamus Variabel Lintas Modul

### A. Pesanan, alamat, penerima (CRM → Finance, HRM)
| Variabel | Tipe | Wajib | Pemilik | Catatan |
| :--- | :--- | :---: | :--- | :--- |
| `customer_code` | string | Ya | CRM | Pemilik akun dan pembayar |
| `payer` | objek kontak | Ya | CRM | `name`, `whatsapp`, `email` pemilik akun |
| `recipient` | objek kontak | Ya | CRM | Penerima layanan; boleh orang lain; tanpa login. Disimpan di langganan |
| `install_address` | objek alamat | Ya | CRM | `address_code`, `address`, `city_code`, `postal_code`; satu pelanggan boleh banyak alamat |
| `city_code` | enum | Ya | CRM | `JKT`, `BDG`, `SBY` |
| `sku` | string | Ya | CRM | `HOME-50`, `MOB-PRE-50`, … |
| `business_line` | enum | Ya | CRM | `PREPAID`, `POSTPAID`, `HOME`, `B2B` |
| `referral_code` | string | Tidak | HRM | Kode staf marketing; boleh dari tautan `?ref=<kode>` yang hanya mengisi kolom kode |
| `sales_employee_id` | string | Tidak | HRM | Staf pemilik kode |
| `subscription_code` | string | Ya | CRM | Satu paket di satu alamat; tiket, invoice, daftar barang, referral, dan profil lokasi merujuk ke sini |

### B. Tiket, teknisi, profil lokasi (CRM, HRM)
| Variabel | Tipe | Pemilik | Catatan |
| :--- | :--- | :--- | :--- |
| `ticket_code` | string | CRM | |
| `type` | enum | CRM | `INSTALLATION`, `MAINTENANCE`, `COMPLAINT` |
| `technician_employee_id` | string | HRM | Satu penugasan per tiket, ditentukan manajer CRM dari daftar HRM |
| `required_items` | array | SCM → CRM | Salinan daftar barang paket saat tiket dibuat: `item_sku`, `qty`, `unit` |
| `photos` | array path | CRM | Minimal satu foto untuk `resolve`; hanya diunggah teknisi yang ditugaskan |
| `site_profile` | objek | CRM | `latitude`, `longitude`, `ont_serial_number`, `signal_dbm`, `speedtest_mbps`, `site_condition_notes`; melekat pada alamat pemasangan dan langganan pelanggan, dipakai ulang saat maintenance |
| `rating_score` | int 1–5 | CRM | Satu rating per tiket, oleh pemilik akun, setelah `RESOLVED` atau `CLOSED` |

### C. Barang (SCM ↔ CRM)
| Variabel | Tipe | Pemilik | Catatan |
| :--- | :--- | :--- | :--- |
| `stock_request_no` | string | SCM | Satu per tiket; baris pertama = paket barang, baris berikutnya = barang tambahan |
| `warehouse_code` | enum | SCM | `WH-BKS`, `WH-BDG`, `WH-SBY` |
| `item_sku` | string | SCM | `ONT-01`, `SIM-01`, `RTR-AX`, `CBL-FO` |
| `qty_available` | int | SCM | `qty_physical − qty_reserved − qty_damaged` |
| `used`, `returned` | int | CRM → SCM | Dilaporkan teknisi di tiket lewat `ticket.items_reported`; SCM memeriksa `issued = used + returned` dan menandai selisih |
| `damaged` | int | SCM | Ditandai staf SCM |

### D. Invoice dan pembayaran (Finance ↔ CRM)
| Variabel | Tipe | Pemilik | Catatan |
| :--- | :--- | :--- | :--- |
| `invoice_no`, `virtual_account` | string | Finance | |
| `subtotal`, `discount`, `tax_amount`, `total` | bigint | Finance | `tax_amount = ROUND((subtotal − discount) × 0.11)`; `total = subtotal − discount + tax_amount` |
| `status` invoice | enum | Finance | Lihat bagian 4 |
| `verified_by` | string | Finance | Staf AR yang mengonfirmasi pembayaran |

## 6. Parameter Bisnis Bersama

| Parameter | Nilai | Catatan |
| :--- | :--- | :--- |
| PPN simulasi | `0.11` | `PPN_RATE` |
| PPh 23 jasa vendor | `0.02` | Finance |
| Toleransi three-way match | `0.02` | Selisih tagihan lebih dari 2% dari PO menjadi `ON_HOLD` |
| Masa reservasi stok | 72 jam | Dikelola SCM |

Perhitungan insentif marketing, komponen gaji, dan tunjangan operasional **tidak** diatur di sini. Itu tanggung jawab tim HRM dan Finance (lihat `tracks/hrm.md` dan `tracks/finance.md`). Kontrak hanya membawa event `referral.used`.

## 7. Konvensi Event

- Nama `<entitas>.<kejadian lampau>` huruf kecil dipisah titik: `invoice.paid`, `ticket.assigned`.
- Amplop baku: `event_id`, `event_type`, `version`, `occurred_at`, `source`, `correlation_id`, `data`. Isi `data` dijelaskan oleh `events/<event>.schema.json`.
- Penerbit menulis event ke tabel outbox dalam transaksi yang sama dengan perubahan datanya; relay mengirimnya dan mengulang pada menit 1, 5, 15 sebelum masuk dead letter (`shared/outbox.py`).
- Penerima menyimpan `event_id` yang sudah diproses dan memeriksa status saat ini sebelum bertindak (event bisa datang dobel atau tidak berurutan).
- Menambah bidang opsional boleh. Mengubah atau menghapus bidang wajib butuh `version` baru dan persetujuan konsumen.
