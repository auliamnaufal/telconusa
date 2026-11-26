---
id: SCM-A-04
title: "POST issue: pengeluaran ke teknisi"
slice: A
tier: 1
priority: P0
owner: Naufal
status: DONE
contract: "K (`POST …/issue`, event `stock.issued`)"
depends_on: [SCM-0, SCM-A-01, SCM-A-02]
touches:
  - "services/scm-api/app/stock/**"
  - "services/scm-api/tests/stock/**"
spec: "spec.md#f3-pengeluaran-oleh-staf-gudang-slice-a"
---

# SCM-A-04: POST issue: pengeluaran ke teknisi

## Konteks

Langkah 7 alur demo. Hanya staf SCM yang mengubah status barang menjadi `WITH_TECHNICIAN`.

## Yang dikerjakan

- `POST /api/v1/stock-requests/{no}/issue` sesuai F3 dengan `Idempotency-Key`.
- `ledger.issue` per baris, `AssetPort.mark_with_technician`, `qty_issued`, status `ISSUED`, `stock.issued` (dengan `serial_numbers`).
- Role: `SCM_MANAGER`, `WAREHOUSE_STAFF`.

## Kriteria penerimaan

- [x] Status bukan `READY_TO_ISSUE`: `409 INVALID_TRANSITION`. Teknisi belum terisi: `409 TECHNICIAN_NOT_ASSIGNED`.
- [x] `serial_numbers` di luar himpunan yang direservasi: `409 SERIAL_NOT_RESERVED`; kosong: memakai unit yang direservasi.
- [x] Setelah issue: `qty_physical` dan `qty_reserved` turun sebesar qty; respons `{stock_request_no, status: ISSUED, unit_status: WITH_TECHNICIAN}`.
- [x] Pengulangan dengan `Idempotency-Key` sama tidak mengeluarkan dua kali. Teknisi (`TECHNICIAN`) mendapat `403`.

## Tes

- `tests/stock/test_issue.py` dengan fake `AssetPort`.

## Selesai bila

- [x] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [x] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [x] `status` issue ini diubah menjadi `DONE` di PR yang sama.
