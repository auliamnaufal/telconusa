---
id: SCM-0-05
title: "Model semua slice, migrasi per slice, dan seed"
slice: 0
tier: 1
priority: P0
owner: Naufal
status: TODO
contract: "none"
depends_on: [SCM-0-01]
touches:
  - "services/scm-api/app/*/models.py"
  - "services/scm-api/app/seed.py"
  - "services/scm-api/app/*/seed.py"
  - "services/scm-api/alembic/**"
  - "services/scm-api/Dockerfile"
spec: "spec.md#4-model-data; spec.md#3-katalog-awal"
---

# SCM-0-05: Model semua slice, migrasi per slice, dan seed

## Konteks

Skema disepakati lebih dulu di spec supaya slice hanya menambah logika, bukan tabel. Perubahan skema berikutnya dibuat sebagai migrasi tambahan oleh slice pemiliknya.

## Yang dikerjakan

- Definisikan semua entitas di spec bagian 4 pada `models.py` slice pemiliknya. `app/core/models.py` memuat `Warehouse`, `Item`, `Vendor`, `InventoryBalance`, `StockMovement`, `AuditLog`, `IdempotencyKey`, serta `IdCounter`, `ProcessedEvent`, `OutboxEvent`, `DeadLetterEvent` dari `shared/`. Tambahkan juga `PendingAssignment` (A).
- Migrasi Alembic: satu berkas per slice (`core`, `stock`, `procurement`, `assets`, `catalog`), masing-masing dengan `branch_labels` sendiri dan `depends_on` ke `core` (selain `core`). Dockerfile menjalankan `alembic upgrade heads`.
- Seed idempoten per slice, dipanggil dari `app/seed.py`: 3 gudang, 4 barang (RTR-AX non-serial; ROP per gudang ONT 10, SIM 200, RTR 20, CBL 2000), vendor `VEN-0001` sampai `VEN-0004`, saldo awal (ONT: Bekasi 40, Bandung 20, Surabaya 15), unit ONT bernomor seri sebanyak saldo ONT berstatus `IN_STOCK` (`received_at` berurutan), daftar barang paket `HOME-20`, `HOME-50`, `HOME-100` (1 ONT-01 + 50 CBL-FO).

## Kriteria penerimaan

- [ ] `alembic upgrade heads` dari basis data kosong berhasil, dan diulang tanpa galat.
- [ ] Menjalankan seed dua kali tidak menggandakan data.
- [ ] Untuk setiap SKU serial dan gudang: `qty_physical` sama dengan jumlah unit `IN_STOCK`, `RESERVED`, dan `FAULTY` di gudang itu (diperiksa tes).
- [ ] Nama tabel dan kolom `snake_case`, uang `BIGINT`, setiap tabel transaksi punya `version`.

## Tes

- `services/scm-api/tests/core/test_seed.py`: seed pada SQLite memori, invarian saldo = unit, idempotensi seed.

## Di luar issue ini

- Logika bisnis apa pun.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
