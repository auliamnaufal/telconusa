---
id: SCM-D-03
title: "API stok indikatif untuk CRM dan saldo per gudang"
slice: D
tier: 1
priority: P0
owner: mike
status: TODO
contract: "K (`GET /stock/{sku}`) + DRAFT (`city_code`, `/stock/balances`)"
depends_on: [SCM-0]
touches:
  - "services/scm-api/app/catalog/**"
  - "services/scm-api/tests/catalog/**"
spec: "spec.md#8-api"
---

# SCM-D-03: API stok indikatif untuk CRM dan saldo per gudang

## Konteks

Menutup temuan P1: `GET /stock/{sku}` tanpa autentikasi dan menjumlah semua gudang.

## Yang dikerjakan

- `GET /api/v1/stock/{sku}` dengan token layanan scope `stock:read`. Parameter `warehouse_code` atau `city_code` (opsional) membatasi gudang; tanpa keduanya, jumlah seluruh gudang. Respons: `sku`, `name`, `unit`, `qty_available`, `reorder_point`, `below_rop`.
- `GET /api/v1/stock/balances`: saldo per gudang dan SKU (`qty_physical`, `qty_reserved`, `qty_damaged`, `qty_available`, `below_rop`), role SCM dan `DIRECTOR`.

## Kriteria penerimaan

- [ ] Tanpa token `401`, scope salah `403`; SKU tak dikenal `404`.
- [ ] `city_code=BDG` hanya menghitung `WH-BDG`.
- [ ] `below_rop` benar bila `qty_available` di bawah `reorder_point` untuk lingkup yang diminta.
- [ ] Barang rusak tidak dihitung tersedia.

## Tes

- `tests/catalog/test_stock_api.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
