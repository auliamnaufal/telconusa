---
id: SCM-A-12
title: "Stok di bawah ROP membuat PR otomatis"
slice: A
tier: 2
priority: P2
owner: Naufal
status: DONE
contract: "DRAFT (event `stock.low` belum diterbitkan)"
depends_on: [SCM-0, SCM-A-06]
touches:
  - "services/scm-api/app/stock/**"
  - "services/scm-api/tests/stock/**"
spec: "spec.md#f9-tier-2"
---

# SCM-A-12: Stok di bawah ROP membuat PR otomatis

## Konteks

Menjawab P-01 dan P-04: pengadaan tidak menunggu permintaan pelanggan.

## Yang dikerjakan

- Saat `qty_available` menyeberang ke bawah ROP gudang itu (sebelum ≥ ROP, sesudah < ROP) karena reservasi, barang tambahan, atau tandai rusak, panggil `ProcurementPort.request_low_stock_purchase` (jumlah = ROP×2 dikurangi tersedia). Pengeluaran paket (`issue`) tidak mengubah `qty_available` karena stok sudah direservasi.
- Port baru `request_low_stock_purchase` (ditambahkan ke `core/ports.py`): Slice B menjaga satu PR `LOW_STOCK` terbuka per SKU dan gudang (`SCM-B-01`).

## Kriteria penerimaan

- [x] Reservasi atau barang tambahan yang membuat ONT di bawah ROP memanggil port satu kali.
- [x] Operasi berikutnya saat stok sudah di bawah ROP tidak memanggil port lagi (hanya penyeberangan yang dihitung).
- [x] Event `stock.low` tidak diterbitkan sebelum kontraknya ada.

## Tes

- `tests/stock/test_low_stock.py` dengan fake `ProcurementPort`.

## Selesai bila

- [x] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [x] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [x] `status` issue ini diubah menjadi `DONE` di PR yang sama.
