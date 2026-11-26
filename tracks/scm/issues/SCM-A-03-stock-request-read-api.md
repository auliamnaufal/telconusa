---
id: SCM-A-03
title: "GET daftar dan detail permintaan barang"
slice: A
tier: 1
priority: P1
owner: Naufal
status: TODO
contract: "K (`GET /stock-requests`, `GET /stock-requests/{no}`)"
depends_on: [SCM-0, SCM-A-01]
touches:
  - "services/scm-api/app/stock/**"
  - "services/scm-api/tests/stock/**"
spec: "spec.md#8-api"
---

# SCM-A-03: GET daftar dan detail permintaan barang

## Konteks

Dipakai layar staf gudang dan pengujian lintas slice.

## Yang dikerjakan

- `GET /api/v1/stock-requests` dengan filter `status`, `city_code`, `ticket_code`, paginasi `page`/`limit`.
- `GET /api/v1/stock-requests/{no}` dengan baris, `return_pending`, `purchase_request_no`, `discrepancy`.
- `return_pending = true` bila status `ISSUED` (laporan teknisi belum diproses).
- Akses role: `DIRECTOR`, `SCM_MANAGER`, `WAREHOUSE_STAFF`, `PROCUREMENT_STAFF`.

## Kriteria penerimaan

- [ ] Bentuk respons sama dengan contoh di `contracts/openapi/scm.yaml`.
- [ ] Role lain mendapat `403`; tanpa token `401`; nomor tak dikenal `404` dengan format galat baku.
- [ ] Daftar bisa difilter per status dan kota.

## Tes

- `tests/stock/test_stock_request_read.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
