---
id: SCM-0-03
title: "Buku besar stok"
slice: 0
tier: 1
priority: P0
owner: Naufal
status: TODO
contract: "none"
depends_on: [SCM-0-01, SCM-0-05]
touches:
  - "services/scm-api/app/core/ledger.py"
  - "services/scm-api/tests/core/test_ledger.py"
spec: "spec.md#41-aturan-buku-besar-stok"
---

# SCM-0-03: Buku besar stok

## Konteks

Saldo stok dipakai tiga slice (reservasi dan pengeluaran, penerimaan, retur). Satu modul kecil dan teruji mencegah dua slice menulis logika saldo berbeda.

## Yang dikerjakan

- `ledger.py` dengan operasi: `receive`, `reserve`, `release`, `issue`, `issue_extra`, `return_good`, `return_damaged`, `mark_damaged`, `write_off`, ditambah pembaca `get_balance` dan `get_available`.
- Setiap operasi mengubah saldo sesuai tabel di spec bagian 4.1, menulis satu `StockMovement` (`ref_type`, `ref_no`, `correlation_id`), menaikkan `version`, dan memakai `SELECT … FOR UPDATE`.
- Pelanggaran syarat menghasilkan `ScmError("INSUFFICIENT_STOCK", 409)` dengan `details` (`sku`, `requested`, `available`).

## Kriteria penerimaan

- [ ] Dua `reserve` berurutan untuk unit terakhir: yang kedua gagal `INSUFFICIENT_STOCK`.
- [ ] `qty_available = physical − reserved − damaged` benar setelah tiap operasi.
- [ ] Barang rusak tidak masuk `qty_available`.
- [ ] Tidak ada operasi yang membuat saldo negatif.
- [ ] Setiap operasi menulis tepat satu `StockMovement`.

## Tes

- `services/scm-api/tests/core/test_ledger.py`: satu tes per operasi dan per syarat gagal.

## Di luar issue ini

- FIFO per batch (`SCM-A-12`).

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
