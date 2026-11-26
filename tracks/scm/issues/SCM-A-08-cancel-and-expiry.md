---
id: SCM-A-08
title: "Pembatalan permintaan dan reservasi kedaluwarsa 72 jam"
slice: A
tier: 1
priority: P1
owner: Naufal
status: DONE
contract: "DRAFT (`POST …/cancel`)"
depends_on: [SCM-0, SCM-A-01]
touches:
  - "services/scm-api/app/stock/**"
  - "services/scm-api/tests/stock/**"
spec: "spec.md#f7-reservasi-kedaluwarsa-slice-a"
---

# SCM-A-08: Pembatalan permintaan dan reservasi kedaluwarsa 72 jam

## Konteks

Menjawab masalah P-02: stok tidak boleh tertahan tanpa batas.

## Yang dikerjakan

- Pekerjaan berkala di lifespan (tiap menit) sesuai F7: `READY_TO_ISSUE` dengan `reserved_until` lewat → `ledger.release`, `AssetPort.release_units`, `CANCELLED`.
- `POST /api/v1/stock-requests/{no}/cancel` (body `{reason}`) untuk `REQUESTED`, `PENDING_STOCK`, `READY_TO_ISSUE`.
- Tulis `AuditLog` untuk setiap pembatalan. `stockrequest.cancelled` belum diterbitkan (kontrak belum ada).

## Kriteria penerimaan

- [x] Permintaan `READY_TO_ISSUE` lewat 72 jam menjadi `CANCELLED`, reservasi dilepas, unit serial kembali `IN_STOCK`.
- [x] Permintaan `PENDING_STOCK` tidak kedaluwarsa. `ISSUED` ditolak `409 INVALID_TRANSITION`.
- [x] Menjalankan pekerjaan dua kali tidak melepas dua kali.
- [x] Pembatalan manual wajib `reason`.

## Tes

- `tests/stock/test_cancel_expiry.py` dengan jam yang bisa diatur (suntik fungsi waktu).

## Di luar issue ini

- Menerbitkan `stockrequest.cancelled` (lanjutan setelah kontrak).

## Selesai bila

- [x] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [x] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [x] `status` issue ini diubah menjadi `DONE` di PR yang sama.
