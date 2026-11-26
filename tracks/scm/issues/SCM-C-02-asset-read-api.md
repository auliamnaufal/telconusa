---
id: SCM-C-02
title: "Daftar dan detail unit ONT"
slice: C
tier: 1
priority: P1
owner: sam
status: TODO
contract: "DRAFT (`GET /assets/units`, `…/{serial}`)"
depends_on: [SCM-0, SCM-C-01]
touches:
  - "services/scm-api/app/assets/**"
  - "services/scm-api/tests/assets/**"
spec: "spec.md#8-api"
---

# SCM-C-02: Daftar dan detail unit ONT

## Konteks

Register ONT dapat ditelusuri per nomor seri.

## Yang dikerjakan

- `GET /api/v1/assets/units` filter `status`, `warehouse_code`, `technician_employee_id`, `item_sku`, `serial_number`; paginasi.
- `GET /api/v1/assets/units/{serial_number}` memuat riwayat status (urut waktu).
- Akses: `SCM_MANAGER`, `WAREHOUSE_STAFF`, `PROCUREMENT_STAFF`, `DIRECTOR`.

## Kriteria penerimaan

- [ ] Unit yang melewati reservasi, pengeluaran, dan pemasangan menampilkan keempat langkah di riwayat.
- [ ] Nomor seri tak dikenal `404` format galat baku.

## Tes

- `tests/assets/test_asset_read.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
