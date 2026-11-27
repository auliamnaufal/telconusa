---
id: SCM-D-04
title: "API ringkasan dashboard"
slice: D
tier: 1
priority: P1
owner: mike
status: DONE
contract: "K (`GET /dashboard/summary`) + DRAFT (kolom tambahan)"
depends_on: [SCM-0, SCM-D-03]
touches:
  - "services/scm-api/app/catalog/**"
  - "services/scm-api/tests/catalog/**"
spec: "spec.md#10-layar-scm-web"
---

# SCM-D-04: API ringkasan dashboard

## Konteks

Sumber data dashboard SCM.

## Yang dikerjakan

- `GET /api/v1/dashboard/summary` sesuai kontrak: `kpis` (`total_skus`, `inventory_valuation_idr`, `open_stock_requests`, `return_pending`) dan `stock_requests`.
- Tambahan opsional (aditif): `kpis.active_reservations`, `kpis.open_purchase_orders`, `kpis.ont_installed`.
- `inventory_valuation_idr = Σ (qty_physical − qty_damaged) × unit_cost`. Hitung `open_purchase_orders` dan `ont_installed` lewat kueri tabel milik slice lain yang sudah ada (baca saja, tanpa memanggil kode slice lain).

## Kriteria penerimaan

- [x] Nilai persediaan benar untuk seed.
- [x] `open_stock_requests` menghitung status `REQUESTED`, `PENDING_STOCK`, `READY_TO_ISSUE`, `ISSUED`.
- [x] `return_pending` sama dengan jumlah permintaan `ISSUED`.
- [x] Bentuk lolos contoh di kontrak.

## Tes

- `tests/catalog/test_dashboard.py`.

## Selesai bila

- [x] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [x] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [x] `status` issue ini diubah menjadi `DONE` di PR yang sama.
