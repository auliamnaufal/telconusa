---
id: SCM-D-09
title: "Tes skenario demo end-to-end dan skenario gagal"
slice: D
tier: 1
priority: P0
owner: mike
status: TODO
contract: "none"
depends_on: [SCM-0, SCM-A-06, SCM-B-04, SCM-C-03]
touches:
  - "services/scm-api/tests/e2e/**"
spec: "spec.md#11-pengujian"
---

# SCM-D-09: Tes skenario demo end-to-end dan skenario gagal

## Konteks

Satu tes yang membuktikan slice-slice menyatu.

## Yang dikerjakan

- Tes memakai implementasi nyata semua port (tanpa fake) dan event bertanda tangan: `ticket.created` → `READY_TO_ISSUE` → `ticket.assigned` → `issue` → `ticket.items_reported` → `RETURNED` → pemeriksaan unit.
- Skenario gagal 1: stok ONT 0 → `PENDING_STOCK` → PR (Finance palsu `approved`) → PO → persetujuan → penerimaan barang → permintaan kembali `READY_TO_ISSUE`.
- Skenario gagal 2: `ticket.created` ganda tetap satu permintaan. Skenario 3: Finance mati → PR tetap `PENDING_BUDGET`; event tetap di outbox. Skenario 5: event tanpa tanda tangan `401`.

## Kriteria penerimaan

- [ ] Semua skenario di atas lulus dengan `pytest -q services/scm-api/tests/e2e`.
- [ ] Nomor seri ONT di `stock.issued` sama dengan unit yang `INSTALLED`.
- [ ] Setelah seluruh alur, invarian saldo = unit (spec seed) tetap benar.

## Tes

- `tests/e2e/test_demo_flow.py` dan `test_failure_scenarios.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
