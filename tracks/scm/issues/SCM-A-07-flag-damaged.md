---
id: SCM-A-07
title: "POST flag-damaged"
slice: A
tier: 1
priority: P1
owner: Naufal
status: TODO
contract: "K (`POST …/flag-damaged`)"
depends_on: [SCM-0, SCM-A-06]
touches:
  - "services/scm-api/app/stock/**"
  - "services/scm-api/tests/stock/**"
spec: "spec.md#f5-barang-rusak-slice-a-dengan-slice-c"
---

# SCM-A-07: POST flag-damaged

## Konteks

Barang rusak diurus staf SCM dan tidak boleh tercampur dengan stok layak pakai.

## Yang dikerjakan

- `POST /api/v1/stock-requests/{no}/flag-damaged` sesuai F5 (status `ISSUED` atau `RETURNED`).
- Non-serial: `ledger.return_damaged` atau `ledger.mark_damaged` sesuai status; serial: `AssetPort.mark_faulty`.
- Batas: total rusak per baris ≤ `qty_issued − qty_used`.

## Kriteria penerimaan

- [ ] Jumlah rusak melebihi batas: `409` dengan `error.code` yang jelas.
- [ ] Setelah ditandai, `qty_available` turun dan `qty_damaged` naik; unit serial menjadi `FAULTY`.
- [ ] Status permintaan lain (`READY_TO_ISSUE`) ditolak `409 INVALID_TRANSITION`.

## Tes

- `tests/stock/test_flag_damaged.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
