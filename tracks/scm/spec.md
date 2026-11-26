# Spesifikasi SCM

Spesifikasi lengkap track SCM TelcoNusa. Dibaca setelah `CONTEXT.md` dan `tracks/scm.md`. Rencana kerja ada di [`plan.md`](plan.md), istilah di [`GLOSSARY.md`](GLOSSARY.md), pekerjaan di [`issues/`](issues/README.md).

## 0. Urutan prioritas sumber

Bila dua sumber bertentangan, yang lebih atas menang:

1. `CONTEXT.md` dan `contracts/` (kesepakatan empat track).
2. `tracks/scm.md` (lingkup dan kriteria penerimaan SCM).
3. Dokumen ini.
4. *Ringkasan Proyek SCM PT TelkoNusa Digital* (visi produk; sebagian fiturnya sudah diubah keputusan di atas, lihat bagian 12).

Dokumen ini tidak memuat tanggal. Urutan kerja ada di `plan.md`.

## 1. Tujuan dan batas

SCM mengelola persediaan, pengadaan, nilai aset, dan pergerakan barang PT TelkoNusa Digital (Jakarta, cabang Bandung dan Surabaya, gudang pusat Bekasi).

SCM **tidak** membuat tiket, tidak memilih teknisi, tidak menulis buku besar, dan tidak membayar vendor. Itu milik CRM, HRM, dan Finance.

### 1.1 Masalah yang diselesaikan

| ID | Masalah | Dijawab oleh |
| :--- | :--- | :--- |
| P-01 | Saldo stok tersebar | Satu buku besar stok per gudang dan SKU (`InventoryBalance` + `StockMovement`) |
| P-02 | Reservasi tanpa batas | Reservasi per `StockRequest`, kedaluwarsa 72 jam |
| P-03 | ONT tidak terlacak per nomor seri | Register `SerializedUnit` dengan riwayat status |
| P-04 | Pengadaan terpisah dari anggaran dan penerimaan | PR, cek anggaran Finance, PO berjenjang, penerimaan barang |
| P-05 | Barang kembali tanpa status seragam | Retur diperiksa dulu, rusak ditandai, tidak dihitung tersedia |
| P-06 | Tukar data tanpa korelasi | `X-Correlation-Id` di setiap panggilan dan event, `event_id` dicatat |

### 1.2 Peran

| Role (JWT) | Boleh |
| :--- | :--- |
| `WAREHOUSE_STAFF` | Melihat permintaan barang, mengeluarkan barang, menandai rusak, menerima barang, memeriksa retur |
| `PROCUREMENT_STAFF` | Membuat dan melihat PR dan PO |
| `SCM_MANAGER` | Semua milik staf gudang dan pengadaan, menyetujui PO, mengelola data master |
| `FINANCE_MANAGER`, `DIRECTOR` | Menyetujui PO pada jenjang atasnya; `DIRECTOR` membaca seluruh dashboard |
| `TECHNICIAN` | Tidak mengakses SCM. Teknisi hanya mengambil dan mengembalikan barang secara fisik; semua perubahan status dilakukan staf SCM |

## 2. Tingkat (tier)

Setiap fitur punya tingkat. Kerjakan semua Tier 1 sebelum Tier 2. Tier 3 hanya dicatat, belum ada issue.

| Tier | Isi |
| :--- | :--- |
| **1: inti demo** | Alur `StockRequest` penuh, reservasi 72 jam, register ONT, PR + cek anggaran, PO + persetujuan berjenjang, penerimaan barang minimal, daftar barang paket, API stok, dashboard |
| **2: tambahan brief** | Aturan 3 penawaran (PO di atas Rp50 juta), batas 10 ONT per teknisi, `LOST` dan `WRITTEN_OFF`, transfer antar-gudang dengan konfirmasi terima, FIFO per batch non-serial, peringatan stok di bawah ROP, halaman audit log |
| **3: hanya dicatat** | Penjualan SIM dan router dengan HPP ke Finance, tagihan vendor, three-way match, penutupan PO oleh `vendor.paid`, estimasi material korporat, rekonsiliasi mingguan teknisi, pengembalian saat teknisi keluar, rekonsiliasi harian dengan Finance, halaman pemantau DLQ |

## 3. Katalog awal

| SKU | Barang | Satuan | Harga satuan | Perlakuan |
| :--- | :--- | :--- | ---: | :--- |
| `ONT-01` | Perangkat ONT | `UNIT` | 350.000 | Serial. Dipinjamkan, aset per nomor seri, tidak dijual |
| `SIM-01` | Kartu SIM | `PCS` | 5.000 | Non-serial. Dijual (Tier 3) |
| `RTR-AX` | Router AX | `UNIT` | 500.000 | Non-serial. Dijual (Tier 3). Berubah dari seed lama yang menandainya serial |
| `CBL-FO` | Kabel fiber optik | `METER` | 4.000 | Non-serial. Habis pakai |

Gudang dan kota:

| Gudang | `city_code` yang dilayani |
| :--- | :--- |
| `WH-BKS` (Bekasi, pusat) | `JKT` |
| `WH-BDG` (Bandung) | `BDG` |
| `WH-SBY` (Surabaya) | `SBY` |

Daftar barang paket awal (data seed, dapat diubah manajer SCM): `HOME-20`, `HOME-50`, `HOME-100` masing-masing 1 `ONT-01` dan 50 `CBL-FO`. Paket `MOB-*` dan `B2B-*` belum punya daftar barang: `GET /package-kits/{sku}` menjawab `404` dan CRM tidak mengirim `required_items`.

## 4. Model data

ID internal `CHAR(36)` UUID, kode bisnis dari `shared.ids.next_code`, uang `BIGINT` rupiah, waktu WIB, kolom `version` di tabel transaksi (lihat `contracts/variable_standards.md` bagian 1).

| Entitas | Kode bisnis | Slice | Bidang kunci |
| :--- | :--- | :---: | :--- |
| `Warehouse` | `WH-BDG` | 0 | `code`, `name`, `city_code` |
| `Item` | SKU | 0 | `sku`, `name`, `unit`, `unit_cost`, `reorder_point`, `safety_stock`, `is_serialized` |
| `Vendor` | `VEN-0001` | 0 | `code`, `name`, `category`, `rating_score` |
| `InventoryBalance` | | 0 | `warehouse_code`, `item_sku`, `qty_physical`, `qty_reserved`, `qty_damaged`, `version` |
| `StockMovement` | | 0 | `warehouse_code`, `item_sku`, `type`, `qty`, `ref_type`, `ref_no`, `correlation_id`, `created_by`, `created_at` |
| `StockRequest` + `StockRequestLine` | `SR-2026-000001` | A | `ticket_code` (unik), `subscription_code`, `city_code`, `warehouse_code`, `technician_employee_id`, `status`, `reserved_until`, `purchase_request_no`, `discrepancy`; baris: `item_sku`, `qty_required`, `qty_issued`, `qty_used`, `qty_returned`, `qty_damaged`, `unit`, `is_extra` |
| `SerializedUnit` + `UnitStatusLog` | `SN-ONT-2026-000001` | C | `item_sku`, `warehouse_code`, `status`, `stock_request_no`, `technician_employee_id`, `installed_ticket_code`, `received_gr_no`, `received_at`; log: `from_status`, `to_status`, `ref`, `by`, `at` |
| `PurchaseRequest` + baris | `PR-2026-0001` | B | `source` (`STOCK_REQUEST`, `LOW_STOCK`, `MANUAL`), `stock_request_no`, `warehouse_code`, `estimated_total`, `status`, `budget_checked_at`, `budget_remaining` |
| `PurchaseOrder` + baris + `PoApproval` | `PO-2026-0001` | B | `purchase_request_no`, `vendor_code`, `total_amount`, `status`, `created_by`; baris: `item_sku`, `qty`, `unit_price`, `qty_received`; persetujuan: `role`, `approver_id`, `decision`, `comment`, `at` |
| `GoodsReceipt` + baris | `GR-2026-0001` | B | `po_no`, `warehouse_code`, `received_by`; baris: `item_sku`, `qty`, `serial_numbers` |
| `PackageKit` + baris | per SKU paket | D | `service_sku`; baris: `item_sku`, `qty`, `unit` |
| `AuditLog`, `IdempotencyKey` | | 0 | Log: `actor`, `role`, `action`, `entity`, `entity_id`, `detail`, `correlation_id`, `at`. Kunci: `key`, `endpoint`, `response_json`, `status_code` |
| `PendingAssignment` | | A | `ticket_code`, `technician_employee_id` (penugasan yang tiba sebelum permintaan barang ada) |
| `PoQuote` (Tier 2) | | B | `po_no`, `vendor_code`, `unit_price`, `notes` (tabel dibuat lewat migrasi tambahan slice B) |
| `StockLot` (Tier 2) | | A | `warehouse_code`, `item_sku`, `gr_no`, `qty_remaining`, `received_at` (migrasi tambahan slice A) |
| `Transfer` + baris (Tier 2) | `TRF-2026-0001` | D | `from_warehouse_code`, `to_warehouse_code`, `status`; baris: `item_sku`, `qty`, `serial_numbers` (migrasi tambahan slice D) |
| `IdCounter`, `ProcessedEvent`, `OutboxEvent`, `DeadLetterEvent` | | 0 | Dari `shared/` |

Rumus tetap: `qty_available = qty_physical − qty_reserved − qty_damaged`.

### 4.1 Aturan buku besar stok

Semua perubahan saldo lewat `app/core/ledger.py`, satu transaksi dengan satu baris `StockMovement`, dan memeriksa `version` (kunci optimistik) agar unit terakhir tidak direbut dua permintaan. Slice tidak mengubah kolom saldo langsung.

| Operasi | `qty_physical` | `qty_reserved` | `qty_damaged` | Syarat |
| :--- | :---: | :---: | :---: | :--- |
| `receive` (barang masuk dari vendor atau transfer) | `+q` | | | |
| `reserve` | | `+q` | | `qty_available ≥ q`, jika tidak `409 INSUFFICIENT_STOCK` |
| `release` | | `−q` | | `qty_reserved ≥ q` |
| `issue` (keluar ke teknisi) | `−q` | `−q` | | Barang pernah direservasi untuk permintaan itu |
| `issue_extra` (barang tambahan) | `−q` | | | `qty_available ≥ q` |
| `return_good` | `+q` | | | |
| `return_damaged` | `+q` | | `+q` | |
| `mark_damaged` (barang sudah di gudang) | | | `+q` | `qty_available ≥ q` |
| `write_off` (Tier 2) | `−q` | | `−q` | `qty_damaged ≥ q` |

Barang yang sudah dipakai (`used`) tidak kembali ke saldo; ia habis dipakai pelanggan.

## 5. Status

Transisi `StockRequest` dan `Unit` memakai mesin status di `services/shared/transitions.py`. Mesin untuk PR, PO, dan GR dibuat di `app/core/machines.py` memakai kelas `StateMachine` yang sama (jangan mengubah `shared/`). Transisi lain ditolak `409 INVALID_TRANSITION`.

### 5.1 Permintaan barang (`StockRequest`)

| Dari | Ke | Pemicu | Pelaku |
| :--- | :--- | :--- | :--- |
| (baru) | `REQUESTED` | `ticket.created` diterima | Sistem |
| `REQUESTED` | `READY_TO_ISSUE` | Semua baris tersedia, direservasi | Sistem |
| `REQUESTED` | `PENDING_STOCK` | Ada baris kurang | Sistem |
| `PENDING_STOCK` | `READY_TO_ISSUE` | Barang masuk (penerimaan barang) dan semua baris kini tersedia | Sistem |
| `READY_TO_ISSUE` | `ISSUED` | `POST …/issue` | Staf gudang |
| `ISSUED` | `RETURNED` | `ticket.items_reported` diproses | Sistem |
| `REQUESTED`, `PENDING_STOCK`, `READY_TO_ISSUE` | `CANCELLED` | Reservasi kedaluwarsa 72 jam, atau `POST …/cancel` | Sistem, staf gudang |

### 5.2 Unit bernomor seri (`SerializedUnit`)

| Dari | Ke | Pemicu |
| :--- | :--- | :--- |
| (baru) | `IN_STOCK` | Penerimaan barang mendaftarkan unit |
| `IN_STOCK` | `RESERVED` | `StockRequest` menjadi `READY_TO_ISSUE` (dipilih FIFO: `received_at` tertua) |
| `RESERVED` | `IN_STOCK` | Reservasi dilepas |
| `RESERVED` | `WITH_TECHNICIAN` | `POST …/issue` |
| `WITH_TECHNICIAN` | `INSTALLED` | `ticket.items_reported` memuat `serial_numbers_installed` |
| `WITH_TECHNICIAN` | `RETURNED` | Dikembalikan teknisi tanpa dipasang |
| `RETURNED` | `IN_STOCK` atau `FAULTY` | Pemeriksaan staf gudang |
| `IN_STOCK`, `WITH_TECHNICIAN` | `FAULTY` | `flag-damaged` |
| `WITH_TECHNICIAN`, `INSTALLED` | `LOST` | Tier 2 |
| `FAULTY`, `LOST` | `WRITTEN_OFF` | Tier 2, hanya `SCM_MANAGER`, wajib alasan |

Setiap perubahan menulis satu baris `UnitStatusLog`.

### 5.3 Permintaan pembelian (`PurchaseRequest`)

`PENDING_BUDGET → BUDGET_OK | BUDGET_REJECTED`; `BUDGET_REJECTED → PENDING_BUDGET` (coba ulang); `BUDGET_OK → PO_CREATED`; `PENDING_BUDGET`, `BUDGET_REJECTED`, `BUDGET_OK → CANCELLED`.

Finance tidak terjangkau: PR tetap `PENDING_BUDGET`, tidak pernah lolos otomatis.

### 5.4 Purchase order (`PurchaseOrder`)

`DRAFT → PENDING_APPROVAL` (hanya bila PO butuh penawaran, Tier 2); `PENDING_APPROVAL → APPROVED | REJECTED | CANCELLED`; `APPROVED → PARTIALLY_RECEIVED | RECEIVED | CANCELLED` (batal hanya bila belum ada penerimaan); `PARTIALLY_RECEIVED → RECEIVED`; `RECEIVED → CLOSED` (Tier 3).

Tanpa Tier 2, PO langsung lahir sebagai `PENDING_APPROVAL`.

## 6. Alur

Semua handler event idempoten: `event_id` dicatat di `ProcessedEvent`, dan status saat ini diperiksa sebelum bertindak. Event diterbitkan lewat outbox dalam transaksi yang sama dengan perubahan datanya.

### F1. `ticket.created` menjadi permintaan barang (Slice A)

1. Tolak event tanpa tanda tangan (`401`), abaikan `event_id` yang sudah diproses.
2. Satu tiket satu permintaan: bila `ticket_code` sudah punya `StockRequest`, abaikan.
3. Gudang = gudang pada `install_address.city_code` (bagian 3). Tidak ada penarikan dari gudang lain di Tier 1.
4. Buat `StockRequest` `REQUESTED` dengan baris dari `required_items`, kode `SR-` dari sequence.
5. Semua baris cukup (`qty_available ≥ qty`): reservasi semua baris lewat `ledger.reserve`, reservasi unit serial lewat `AssetPort.reserve_units`, `reserved_until = sekarang + 72 jam`, status `READY_TO_ISSUE`, terbitkan `stockrequest.ready`.
6. Ada baris kurang: **tidak ada reservasi sebagian**. Status `PENDING_STOCK`, panggil `ProcurementPort.request_purchase` untuk kekurangan, terbitkan `stockrequest.pending` dengan `missing_items` dan `purchase_request_no`. Tiket tidak berubah.

### F2. Teknisi ditugaskan

`ticket.assigned` mengisi `technician_employee_id` pada permintaan milik tiket itu. Bila permintaan belum ada (event tiba tak berurutan), simpan teknisi di tabel `pending_assignment` dan terapkan saat F1 membuat permintaan. Bila ada, tidak mengubah status.

### F3. Pengeluaran oleh staf gudang (Slice A)

`POST /stock-requests/{no}/issue` (header `Idempotency-Key`).

1. Status harus `READY_TO_ISSUE`, jika tidak `409 INVALID_TRANSITION`. Teknisi harus sudah terisi, jika tidak `409 TECHNICIAN_NOT_ASSIGNED`.
2. Untuk SKU serial, `serial_numbers` bila diisi harus persis himpunan unit yang direservasi permintaan itu (`409 SERIAL_NOT_RESERVED`); bila kosong, pakai unit yang direservasi.
3. `ledger.issue`, `AssetPort.mark_with_technician` (`RESERVED → WITH_TECHNICIAN`), isi `qty_issued`, status `ISSUED`.
4. Terbitkan `stock.issued` (dengan `serial_numbers`). Teknisi tidak pernah mengubah status barang.

`POST …/issue-extra`: staf menambah baris pengeluaran pada tiket yang sama tanpa persetujuan ulang. Status harus `ISSUED`. Mengeluarkan langsung dari saldo tersedia (`ledger.issue_extra`); stok kurang menjawab `409 INSUFFICIENT_STOCK`. Baris ditandai `is_extra`. Kekurangan kecil di lapangan diselesaikan lewat telepon dan tidak masuk sistem.

### F4. Laporan pemakaian (Slice A, dengan Slice C)

`ticket.items_reported` (dari CRM) per baris:

1. Cari permintaan lewat `stock_request_no`; status harus `ISSUED`. Bila bukan, abaikan dan catat (event ganda atau tak berurutan).
2. Isi `qty_used` dan `qty_returned`. Selisih `qty_issued − qty_used − qty_returned` ≠ 0 menandai `discrepancy` pada permintaan dan `has_discrepancy: true`. `qty_returned` dipotong agar `qty_used + qty_returned ≤ qty_issued`.
3. Non-serial: `ledger.return_good` untuk `qty_returned − qty_damaged` dan `ledger.return_damaged` untuk jumlah yang sudah ditandai rusak. Tidak ada pemeriksaan tambahan.
4. Serial: unit di `serial_numbers_installed` menjadi `INSTALLED` (membawa `installed_ticket_code`). Unit yang dikeluarkan tetapi tidak terpasang menjadi `RETURNED` dan **belum** masuk saldo; saldo bertambah saat staf gudang memeriksanya (F6).
5. Status `RETURNED`, terbitkan `stock.returned` dengan `issued`, `used`, `returned`, `damaged`, `has_discrepancy`. Selisih tidak mengubah saldo otomatis; ia muncul di detail permintaan dan dashboard untuk ditinjau manajer.

### F5. Barang rusak (Slice A, dengan Slice C)

`POST …/flag-damaged` pada permintaan `ISSUED` atau `RETURNED`.

- Jumlah rusak total per baris ≤ `qty_issued − qty_used`.
- Permintaan `ISSUED`: catat `qty_damaged` pada baris; saldo disesuaikan saat F4.
- Permintaan `RETURNED`, non-serial: `ledger.return_damaged` sebesar selisih (bila barang belum masuk sebagai baik) atau `ledger.mark_damaged`.
- Serial: unit menjadi `FAULTY` (`AssetPort.mark_faulty`).
- Stok rusak tidak pernah dihitung tersedia.

### F6. Pemeriksaan retur (Slice C)

`POST /assets/units/{serial}/inspect` pada unit `RETURNED`: hasil `GOOD` menjadikannya `IN_STOCK` dan `ledger.return_good`; hasil `FAULTY` menjadikannya `FAULTY` dan `ledger.return_damaged`. Satu permintaan barang dianggap bebas dari "return pending" setelah laporan teknisi diproses (F4), bukan setelah pemeriksaan.

### F7. Reservasi kedaluwarsa (Slice A)

Pekerjaan berkala (tiap menit) mencari permintaan `READY_TO_ISSUE` dengan `reserved_until` terlewat. Untuk tiap permintaan, dalam satu transaksi: `ledger.release`, `AssetPort.release_units`, status `CANCELLED`. `POST …/cancel` oleh staf gudang melakukan hal yang sama untuk status `REQUESTED`, `PENDING_STOCK`, atau `READY_TO_ISSUE` dan wajib mengisi alasan. Permintaan `PENDING_STOCK` tidak punya reservasi dan tidak kedaluwarsa. `stockrequest.cancelled` belum dikontrakkan, jadi CRM belum diberi tahu (lihat `contract-extension.md`).

### F8. Pengadaan (Slice B)

1. **PR otomatis.** `ProcurementPort.request_purchase` dari F1: satu PR per permintaan barang, satu baris per SKU kurang, perkiraan biaya = `qty × unit_cost`, `source = STOCK_REQUEST`. PR diperiksa anggarannya: `POST /api/v1/budgets/check` ke Finance (`cost_center_code = CC-SCM`, `fiscal_year` tahun berjalan, token layanan scope `budgets:check`). `approved = true` → `BUDGET_OK`; `approved = false` → `BUDGET_REJECTED`; Finance tak terjangkau, timeout, atau galat → tetap `PENDING_BUDGET`, dicoba ulang oleh pekerjaan berkala. Tidak ada `except: pass`; kegagalan dicatat.
2. **PO.** Staf pengadaan membuat PO dari PR `BUDGET_OK` (`POST /purchase-requests/{no}/create-po`) dengan memilih vendor dan harga satuan. `POST /purchase-orders` (sudah dikontrakkan) membuat PR dan PO sekaligus: cek anggaran dulu; Finance tak terjangkau menjawab `503 BUDGET_CHECK_UNAVAILABLE` dan **tidak ada yang dibuat**; tidak cukup menjawab `409 BUDGET_INSUFFICIENT`. PO lahir `PENDING_APPROVAL`.
3. **Persetujuan berjenjang** (disimpan di SCM; penyetuju masuk ke `scm-web` dengan role dari JWT-nya, tanpa memanggil HRM):

   | Total PO | Persetujuan yang dibutuhkan |
   | :--- | :--- |
   | ≤ Rp10.000.000 | `SCM_MANAGER` |
   | > Rp10.000.000 sampai Rp100.000.000 | `SCM_MANAGER` + `FINANCE_MANAGER` |
   | > Rp100.000.000 | `SCM_MANAGER` + `FINANCE_MANAGER` + `DIRECTOR` |

   Aturan: pembuat PO tidak boleh menyetujui PO-nya (`403 APPROVAL_SELF_FORBIDDEN`); satu role menyetujui sekali (`409 DUPLICATE_APPROVAL`); role di luar rantai ditolak (`403 APPROVAL_ROLE_NOT_REQUIRED`); satu penolakan membuat PO `REJECTED`; PO `APPROVED` setelah semua role dalam rantai menyetujui. Urutan penyetujuan bebas.
4. **Penerimaan barang** (`GR-`): `POST /purchase-orders/{no}/receipts` pada PO `APPROVED` atau `PARTIALLY_RECEIVED`. Per baris `qty` ≤ sisa (`409 OVER_RECEIPT`). Tiap baris: `ledger.receive` ke gudang yang dipilih; SKU serial memanggil `AssetPort.register_units` (nomor seri `SN-ONT-` dari sequence, status `IN_STOCK`, `received_at` sekarang); `qty_received` bertambah; PO menjadi `PARTIALLY_RECEIVED` atau `RECEIVED`. Terakhir panggil `StockRequestPort.reevaluate_pending(sku, warehouse)`: permintaan `PENDING_STOCK` yang kini cukup menjadi `READY_TO_ISSUE` (urut `created_at` tertua lebih dulu) dan menerbitkan `stockrequest.ready`.

### F9. Tier 2

- **Penawaran:** PO di atas Rp50.000.000 butuh tiga penawaran vendor berbeda (`PoQuote`: vendor, harga, catatan) sebelum diajukan; PO dibuat `DRAFT`, `POST …/submit` menolak bila penawaran kurang dari tiga.
- **Batas teknisi:** `AssetPort.mark_with_technician` menolak bila teknisi akan memegang lebih dari 10 unit ONT berstatus `WITH_TECHNICIAN` (`409 TECHNICIAN_LIMIT_EXCEEDED`). Halaman kepemilikan per teknisi.
- **`LOST` dan `WRITTEN_OFF`:** lihat bagian 5.2.
- **Transfer antar-gudang:** `Transfer` (`TRF-2026-0001`): `REQUESTED → IN_TRANSIT → RECEIVED`. Saldo gudang asal turun saat dikirim (`issue`-setara), saldo gudang tujuan naik hanya setelah penerimaan dikonfirmasi.
- **FIFO per batch non-serial:** pengeluaran non-serial menghabiskan batch terlama lebih dulu (`StockLot`).
- **`stock.low`:** setelah gerakan stok, bila `qty_available` di bawah ROP, buat PR `LOW_STOCK` (satu PR terbuka per SKU dan gudang). Event `stock.low` terbit setelah dikontrakkan.
- **Audit log:** semua operasi tulis memanggil `core.audit.record`; halaman audit log hanya membaca.

## 7. Aturan lintas fitur

1. Tidak menulis ke basis data modul lain. SCM hanya memanggil Finance `budgets/check` dan menerima event CRM.
2. Hanya SCM mengubah status SCM. Tidak ada endpoint yang membiarkan CRM atau teknisi mengubah status barang.
3. Setiap `POST` transaksi menerima `Idempotency-Key`; pengulangan dengan kunci sama mengembalikan hasil yang sama tanpa efek ganda.
4. Setiap respons galat memakai format baku (`contracts/variable_standards.md` bagian 1) dan membawa `correlation_id` (tiket, PR, atau PO terkait bila ada).
5. Panggilan keluar membawa `X-Correlation-Id` dan token layanan (`shared/service_auth.py`).
6. Event masuk wajib bertanda tangan (`shared.event_receiver.create_events_router`).
7. Setiap endpoint di kontrak menyatakan `x-auth`, `x-roles` atau `x-scope`; endpoint baru mengikuti `contract-extension.md`.
8. Kode bisnis dari `shared.ids.next_code`, bukan `count()+1`.
9. Tidak ada kegagalan yang ditelan diam-diam; kegagalan Finance menahan PR.

## 8. API

Status: **K** = sudah di `contracts/openapi/scm.yaml`; **D** = draf di `contract-extension.md` (dikembangkan lebih dulu, belum di kontrak bersama).

| Endpoint | Auth | Slice | Tier | Status |
| :--- | :--- | :---: | :---: | :---: |
| `GET /stock/{sku}` (parameter opsional `warehouse_code`, `city_code`) | service `stock:read` | D | 1 | K + D (`city_code`) |
| `GET /package-kits/{sku}` | service `packagekits:read` | D | 1 | K |
| `GET /dashboard/summary` (kolom tambahan opsional `active_reservations`, `open_purchase_orders`, `ont_installed`) | user (SCM, `DIRECTOR`) | D | 1 | K + D (kolom tambahan) |
| `GET /stock-requests`, `GET /stock-requests/{no}` | user (SCM, `DIRECTOR`) | A | 1 | K |
| `POST /stock-requests/{no}/issue` | user (`SCM_MANAGER`, `WAREHOUSE_STAFF`) | A | 1 | K |
| `POST /stock-requests/{no}/issue-extra` | user (`SCM_MANAGER`, `WAREHOUSE_STAFF`) | A | 1 | K |
| `POST /stock-requests/{no}/flag-damaged` | user (`SCM_MANAGER`, `WAREHOUSE_STAFF`) | A | 1 | K |
| `POST /stock-requests/{no}/cancel` | user (`SCM_MANAGER`, `WAREHOUSE_STAFF`) | A | 1 | D |
| `GET /stock/balances` | user (SCM, `DIRECTOR`) | D | 1 | D |
| `GET /items`, `GET /warehouses`, `GET /vendors` | user (SCM, `DIRECTOR`) | D | 1 | D |
| `POST/PATCH /items`, `/vendors`, `/package-kits` | user (`SCM_MANAGER`) | D | 1 | D |
| `GET /assets/units`, `GET /assets/units/{serial}` | user (SCM, `DIRECTOR`) | C | 1 | D |
| `POST /assets/units/{serial}/inspect` | user (`SCM_MANAGER`, `WAREHOUSE_STAFF`) | C | 1 | D |
| `POST /purchase-orders` | user (`SCM_MANAGER`, `PROCUREMENT_STAFF`) | B | 1 | K |
| `GET /purchase-requests`, `GET /purchase-requests/{no}` | user (SCM, `DIRECTOR`) | B | 1 | D |
| `POST /purchase-requests/{no}/create-po` | user (`SCM_MANAGER`, `PROCUREMENT_STAFF`) | B | 1 | D |
| `GET /purchase-orders`, `GET /purchase-orders/{no}` | user (SCM, `FINANCE_MANAGER`, `DIRECTOR`) | B | 1 | D |
| `POST /purchase-orders/{no}/approve`, `…/reject` | user (`SCM_MANAGER`, `FINANCE_MANAGER`, `DIRECTOR`) | B | 1 | D |
| `POST /purchase-orders/{no}/receipts` | user (`SCM_MANAGER`, `WAREHOUSE_STAFF`) | B | 1 | D |
| `POST /purchase-orders/{no}/quotes`, `…/submit` | user (`SCM_MANAGER`, `PROCUREMENT_STAFF`) | B | 2 | D |
| `POST /assets/units/{serial}/mark-lost`, `…/write-off` | user (`SCM_MANAGER`) | C | 2 | D |
| `GET /assets/technicians/{employee_id}` | user (SCM, `DIRECTOR`) | C | 2 | D |
| `POST /transfers`, `…/dispatch`, `…/receive` | user (`SCM_MANAGER`, `WAREHOUSE_STAFF`) | D | 2 | D |
| `GET /audit-logs` | user (`SCM_MANAGER`, `DIRECTOR`) | D | 2 | D |

`POST /purchase-orders` (K) tetap menerima `{vendor_code, item_sku, qty}`. Contoh respons di kontrak memuat `status: APPROVED`; setelah spesifikasi ini ia `PENDING_APPROVAL` (perbaikan contoh masuk `contract-extension.md`).

### 8.1 Kode galat SCM

`INSUFFICIENT_STOCK` (409), `INVALID_TRANSITION` (409), `TECHNICIAN_NOT_ASSIGNED` (409), `SERIAL_NOT_RESERVED` (409), `OVER_RECEIPT` (409), `BUDGET_INSUFFICIENT` (409), `DUPLICATE_APPROVAL` (409), `BUDGET_CHECK_UNAVAILABLE` (503), `APPROVAL_SELF_FORBIDDEN` (403), `APPROVAL_ROLE_NOT_REQUIRED` (403), `TECHNICIAN_LIMIT_EXCEEDED` (409, Tier 2), `QUOTES_REQUIRED` (409, Tier 2).

## 9. Event

| Event | Arah | Tier | Status kontrak |
| :--- | :--- | :---: | :--- |
| `ticket.created` | masuk dari CRM | 1 | Dikontrakkan |
| `ticket.assigned` | masuk dari CRM | 1 | Dikontrakkan |
| `ticket.items_reported` | masuk dari CRM | 1 | Dikontrakkan |
| `stockrequest.ready` | keluar ke CRM | 1 | Dikontrakkan |
| `stockrequest.pending` | keluar ke CRM | 1 | Dikontrakkan |
| `stock.issued` | keluar ke CRM | 1 | Dikontrakkan |
| `stock.returned` | keluar ke CRM | 1 | Dikontrakkan |
| `stockrequest.cancelled` | keluar ke CRM | 1 | Usulan |
| `po.approved`, `goods.received` | keluar ke Finance | 1 | Usulan |
| `stock.low` | keluar | 2 | Usulan |
| `shipment.delivered` | keluar | 2 | Usulan |

Event berstatus "Usulan" **tidak diterbitkan** sebelum kontraknya di-merge. Handler dan outbox-nya disiapkan sebagai issue lanjutan.

## 10. Layar `scm-web`

Tampilan memakai token merek di `apps/scm-web/public/brand/tokens.css`. Satu folder rute per slice; kerangka (login, layout, navigasi, klien API) dibuat di Slice 0.

| Rute | Slice | Isi |
| :--- | :---: | :--- |
| `/` | D | Dashboard: stok tersedia, reservasi aktif, PO terbuka, ONT terpasang, permintaan retur tertunda |
| `/stock` | D | Saldo per SKU dan gudang (fisik, reservasi, rusak, tersedia, di bawah ROP) |
| `/catalog` | D | Barang, gudang, vendor, daftar barang paket |
| `/stock-requests`, `/stock-requests/[no]` | A | Daftar dengan filter status, detail baris, form keluarkan, barang tambahan, tandai rusak, batalkan, penanda "return pending" dan selisih |
| `/procurement`, `/procurement/purchase-orders/[no]` | B | PR, buat PO, detail PO dengan rantai persetujuan, terima barang |
| `/assets`, `/assets/[serial]` | C | Register ONT per nomor seri, riwayat status, pemeriksaan retur |
| `/audit` | D | Audit log (Tier 2) |

Menu dan tombol mengikuti role (tombol yang tidak boleh dipakai role itu disembunyikan, dan server tetap menolaknya).

## 11. Pengujian

- Tes layanan di `services/scm-api/tests/`, dijalankan `pytest -q services/scm-api/tests`, memakai SQLite memori seperti `tests/shared/conftest.py`. Secret uji diatur di `conftest.py`, bukan di repo.
- Tiap issue menulis tes untuk aturannya sendiri. Tes minimal: jalur sukses, setiap kode galat milik issue itu, dan idempotensi bila ada event atau `Idempotency-Key`.
- Satu tes skenario menjalankan alur demo langkah 4 sampai 9 dan skenario gagal 1, 2, 3, dan 5 dari `CONTEXT.md` bagian 5 (issue `SCM-D-09`).
- `LIVE` di `tracks/scm.md` hanya setelah tes lulus (isi `test:`).
- Setelah mengubah `tracks/scm.md`, jalankan `python tools/check_contracts.py`.

## 12. Perbedaan dari brief dan alasannya

| Brief | Spesifikasi ini | Alasan |
| :--- | :--- | :--- |
| Reservasi dibuat saat CRM mencatat order | Reservasi dibuat saat `ticket.created` | SCM tidak melihat order. Stok baru dibutuhkan setelah bayar dan tiket ada. Lihat ADR-0001 |
| Reservasi dilepas saat order batal atau bayar gagal | Dilepas saat 72 jam lewat atau batal manual | Belum ada event pembatalan tiket di kontrak |
| Persetujuan PO berjenjang "dari HRM" | Disimpan di SCM, role dari JWT | HRM memiliki karyawan, bukan PO. Lihat ADR-0002 |
| Router dan SIM serial/terlacak per nomor seri (contoh `flag-damaged` memakai `SN-RTR-…`) | Hanya ONT yang serial | Brief: hanya ONT yang aset per nomor seri. Contoh kontrak perlu disesuaikan (`contract-extension.md`) |
| `Work order` | `Ticket` | Keputusan `CONTEXT.md` |
| Lima modul lengkap dalam delapan minggu | Tiga tier tanpa tanggal | Lihat bagian 2 |

## 13. Pertanyaan terbuka

- Daftar barang paket `MOB-*` dan `B2B-*`: apakah paket seluler memuat `SIM-01`?
- Siapa yang meninjau `discrepancy` dan bagaimana menyelesaikannya (sementara: ditandai dan tampil di dashboard).
- Apakah staf gudang perlu konfirmasi fisik retur selain laporan teknisi (sementara: pemeriksaan unit serial saja).
- Hak `DIRECTOR` untuk menyetujui PO di `scm-web` bergantung pada role di JWT HRM; konfirmasi nama role dengan tim HRM.
