---
id: SCM-A-12
title: "Stok di bawah ROP membuat PR otomatis"
slice: A
tier: 2
priority: P2
owner: Naufal
status: TODO
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

- Setelah operasi ledger yang menurunkan `qty_available`, periksa ROP gudang itu; bila di bawah dan belum ada PR terbuka `LOW_STOCK` untuk SKU dan gudang itu, panggil `ProcurementPort.request_purchase` (jumlah = ROP×2 dikurangi tersedia).
- Satu PR terbuka per SKU dan gudang.

## Kriteria penerimaan

- [ ] Pengeluaran yang membuat ONT di bawah ROP membuat satu PR `LOW_STOCK`.
- [ ] Pengeluaran berikutnya tidak membuat PR kedua selama PR pertama belum `PO_CREATED` atau `CANCELLED`.
- [ ] Event `stock.low` tidak diterbitkan sebelum kontraknya ada.

## Tes

- `tests/stock/test_low_stock.py` dengan fake `ProcurementPort`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
