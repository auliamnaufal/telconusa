---
id: SCM-A-09
title: "Implementasi `StockRequestPort.reevaluate_pending`"
slice: A
tier: 1
priority: P0
owner: Naufal
status: TODO
contract: "none"
depends_on: [SCM-0, SCM-A-01]
touches:
  - "services/scm-api/app/stock/**"
  - "services/scm-api/tests/stock/**"
spec: "spec.md#f8-pengadaan-slice-b"
---

# SCM-A-09: Implementasi `StockRequestPort.reevaluate_pending`

## Konteks

Dipanggil Slice B setelah penerimaan barang agar `PENDING_STOCK` kembali `READY_TO_ISSUE`.

## Yang dikerjakan

- Implementasikan port dan daftarkan di `app/stock/__init__.py`.
- Untuk SKU dan gudang itu, ambil permintaan `PENDING_STOCK` urut `created_at` tertua; bila semua barisnya kini cukup: reservasi, `READY_TO_ISSUE`, `reserved_until` baru (72 jam), `stockrequest.ready`.
- Kembalikan daftar `stock_request_no` yang menjadi siap.

## Kriteria penerimaan

- [ ] Dua permintaan pending bersaing untuk stok yang baru masuk: yang lebih tua terpenuhi lebih dulu, yang lain tetap `PENDING_STOCK`.
- [ ] Permintaan yang masih kurang satu baris tetap `PENDING_STOCK` tanpa reservasi.
- [ ] Memanggil dua kali tidak menerbitkan `ready` dua kali.

## Tes

- `tests/stock/test_reevaluate_pending.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
