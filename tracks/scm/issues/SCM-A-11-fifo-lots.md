---
id: SCM-A-11
title: "FIFO per batch untuk barang non-serial"
slice: A
tier: 2
priority: P2
owner: Naufal
status: DONE
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

- Tabel `stock_lots` (gudang, SKU, `seq` urutan masuk, `ref_no`, `qty_remaining`, `received_at`); modelnya di `core/models.py`, migrasi tambahan `stock_0002` di cabang `stock` (mengisi satu lot awal dari saldo non-serial yang sudah ada).
- `receive` dan `return_good` membuat batch baru; `issue`, `issue_extra`, dan `mark_damaged` non-serial menghabiskan batch tertua lebih dulu; `return_damaged`, `write_off`, `reserve`, dan `release` tidak mengubah batch.
- Seed membuat satu batch awal per saldo.

## Kriteria penerimaan

- [x] Dua penerimaan berbeda lalu pengeluaran: batch tertua habis lebih dulu.
- [x] Jumlah semua `qty_remaining` sama dengan `qty_physical` minus `qty_damaged` untuk SKU non-serial (diperiksa tes); batch yang tidak cukup menutup pengeluaran menjawab `409 LOT_MISMATCH` tanpa mengubah saldo.
- [x] Semua tes `test_ledger.py` tetap lulus.

## Tes

- `tests/core/test_ledger_fifo.py`.

## Selesai bila

- [x] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [x] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [x] `status` issue ini diubah menjadi `DONE` di PR yang sama.
