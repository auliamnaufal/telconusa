---
id: SCM-A-06
title: "Handler `ticket.items_reported`: laporan pemakaian"
slice: A
tier: 1
priority: P0
owner: Naufal
status: DONE
contract: "K (event `ticket.items_reported`, `stock.returned`)"
depends_on: [SCM-0, SCM-A-04]
touches:
  - "services/scm-api/app/stock/**"
  - "services/scm-api/tests/stock/**"
spec: "spec.md#f4-laporan-pemakaian-slice-a-dengan-slice-c"
---

# SCM-A-06: Handler `ticket.items_reported`: laporan pemakaian

## Konteks

Langkah 9 alur demo. Menutup siklus permintaan dan memperbarui persediaan dari `used` dan `returned`.

## Yang dikerjakan

- Handler sesuai F4: isi `qty_used`, `qty_returned`; tandai `discrepancy`; non-serial lewat `ledger.return_good` dan `return_damaged`; serial lewat `AssetPort.mark_installed` dan `mark_returned`.
- Status `RETURNED`, terbitkan `stock.returned` dengan `has_discrepancy`.
- Event untuk permintaan yang bukan `ISSUED` diabaikan dan dicatat.

## Kriteria penerimaan

- [x] `used + returned = issued`: `has_discrepancy = false`, kabel 20 m kembali menambah saldo, ONT di `serial_numbers_installed` menjadi `INSTALLED`.
- [x] `used + returned < issued`: `discrepancy` tertandai, `has_discrepancy = true`, saldo tidak berubah untuk bagian yang hilang.
- [x] `used + returned > issued`: `returned` dipotong, ditandai selisih.
- [x] Event ganda tidak menambah saldo dua kali. Event untuk permintaan `READY_TO_ISSUE` diabaikan.
- [x] Payload `stock.returned` lolos skema kontrak.

## Tes

- `tests/stock/test_items_reported.py`.

## Selesai bila

- [x] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [x] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [x] `status` issue ini diubah menjadi `DONE` di PR yang sama.
