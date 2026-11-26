---
id: SCM-D-01
title: "API data master: barang, gudang, vendor"
slice: D
tier: 1
priority: P1
owner: mike
status: TODO
contract: "DRAFT"
depends_on: [SCM-0]
touches:
  - "services/scm-api/app/catalog/**"
  - "services/scm-api/tests/catalog/**"
spec: "spec.md#3-katalog-awal"
---

# SCM-D-01: API data master: barang, gudang, vendor

## Konteks

Layar katalog dan form PO butuh daftar barang, gudang, vendor.

## Yang dikerjakan

- `GET /items`, `GET /warehouses`, `GET /vendors` (paginasi, role SCM dan `DIRECTOR`).
- `POST /items`, `PATCH /items/{sku}`, `POST /vendors`, `PATCH /vendors/{code}` (hanya `SCM_MANAGER`); kode `VEN-` dari `next_code`.
- Validasi: `is_serialized` tidak boleh diubah bila sudah ada saldo atau unit; SKU unik.

## Kriteria penerimaan

- [ ] Membuat barang baru muncul di daftar; SKU ganda `409`.
- [ ] Mengubah `is_serialized` pada ONT-01 yang sudah punya unit: `409`.
- [ ] Role selain `SCM_MANAGER` tidak bisa menulis (`403`).

## Tes

- `tests/catalog/test_master_data.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
