---
id: SCM-A-11
title: "FIFO per batch untuk barang non-serial"
slice: A
tier: 2
priority: P2
owner: Naufal
status: TODO
contract: "none"
depends_on: [SCM-0, SCM-A-06]
touches:
  - "services/scm-api/app/stock/**"
  - "services/scm-api/tests/stock/**"
  - "services/scm-api/app/core/ledger.py"
spec: "spec.md#f9-tier-2"
---

# SCM-A-11: FIFO per batch untuk barang non-serial

## Konteks

Brief mewajibkan pengeluaran FIFO. Unit serial sudah FIFO lewat `received_at`; barang non-serial perlu batch. Issue ini boleh mengubah `core/ledger.py` untuk tabel batch.

## Yang dikerjakan

- Tabel `stock_lots` (gudang, SKU, `gr_no`, `qty_remaining`, `received_at`) lewat migrasi tambahan slice `stock`.
- `ledger.receive` membuat batch; `issue` dan `issue_extra` non-serial menghabiskan batch terlama lebih dulu dan mencatatnya di `StockMovement`.
- Seed membuat satu batch awal per saldo.

## Kriteria penerimaan

- [ ] Dua penerimaan berbeda lalu pengeluaran: batch tertua habis lebih dulu.
- [ ] Jumlah semua `qty_remaining` sama dengan `qty_physical` minus rusak untuk SKU non-serial (diperiksa tes).
- [ ] Semua tes `test_ledger.py` tetap lulus.

## Tes

- `tests/core/test_ledger_fifo.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
