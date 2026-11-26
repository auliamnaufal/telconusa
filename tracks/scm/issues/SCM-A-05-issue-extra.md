---
id: SCM-A-05
title: "POST issue-extra: barang tambahan"
slice: A
tier: 1
priority: P1
owner: Naufal
status: TODO
contract: "K (`POST …/issue-extra`)"
depends_on: [SCM-0, SCM-A-04]
touches:
  - "services/scm-api/app/stock/**"
  - "services/scm-api/tests/stock/**"
spec: "spec.md#f3-pengeluaran-oleh-staf-gudang-slice-a"
---

# SCM-A-05: POST issue-extra: barang tambahan

## Konteks

Teknisi kembali ke gudang meminta barang tambahan; tidak perlu persetujuan ulang.

## Yang dikerjakan

- `POST /api/v1/stock-requests/{no}/issue-extra` menambah baris `is_extra` pada permintaan `ISSUED`.
- `ledger.issue_extra` dari saldo tersedia; SKU serial memakai `AssetPort.reserve_units` lalu `mark_with_technician`.
- Terbitkan `stock.issued` untuk baris tambahan (tiket yang sama).

## Kriteria penerimaan

- [ ] Permintaan belum `ISSUED`: `409 INVALID_TRANSITION`. Stok kurang: `409 INSUFFICIENT_STOCK`.
- [ ] Baris tambahan tercatat `is_extra = true` dan muncul di detail.
- [ ] Idempoten dengan `Idempotency-Key`.

## Tes

- `tests/stock/test_issue_extra.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
