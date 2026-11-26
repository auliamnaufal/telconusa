---
id: SCM-C-03
title: "Pemeriksaan unit retur"
slice: C
tier: 1
priority: P0
owner: sam
status: TODO
contract: "DRAFT (`POST …/inspect`)"
depends_on: [SCM-0, SCM-C-01]
touches:
  - "services/scm-api/app/assets/**"
  - "services/scm-api/tests/assets/**"
spec: "spec.md#f6-pemeriksaan-retur-slice-c"
---

# SCM-C-03: Pemeriksaan unit retur

## Konteks

P-05: unit yang kembali harus diperiksa sebelum masuk stok layak pakai.

## Yang dikerjakan

- `POST /api/v1/assets/units/{serial_number}/inspect` (body `{result: GOOD|FAULTY, notes}`) pada unit `RETURNED`.
- `GOOD`: `IN_STOCK` dan `ledger.return_good`; `FAULTY`: `FAULTY` dan `ledger.return_damaged`.
- Tulis `AuditLog`. Role: `SCM_MANAGER`, `WAREHOUSE_STAFF`.

## Kriteria penerimaan

- [ ] Unit `RETURNED` tidak masuk `qty_available` sebelum diperiksa.
- [ ] Setelah `GOOD`: `qty_physical` dan `qty_available` naik 1; setelah `FAULTY`: `qty_damaged` naik, `qty_available` tidak.
- [ ] Unit yang bukan `RETURNED`: `409 INVALID_TRANSITION`.

## Tes

- `tests/assets/test_inspect.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
