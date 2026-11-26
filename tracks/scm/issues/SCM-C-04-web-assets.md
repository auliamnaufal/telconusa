---
id: SCM-C-04
title: "Layar register aset ONT"
slice: C
tier: 1
priority: P1
owner: sam
status: TODO
contract: "none"
depends_on: [SCM-0, SCM-0-06, SCM-C-02]
touches:
  - "apps/scm-web/src/app/(app)/assets/**"
  - "apps/scm-web/src/features/assets/**"
spec: "spec.md#10-layar-scm-web"
---

# SCM-C-04: Layar register aset ONT

## Konteks

Register aset dan pemeriksaan retur.

## Yang dikerjakan

- `/assets`: tabel unit dengan filter status, gudang, teknisi; badge status.
- `/assets/[serial]`: detail dan riwayat status; tombol Periksa (Baik atau Rusak) untuk unit `RETURNED` dengan catatan, tampil hanya untuk `SCM_MANAGER` dan `WAREHOUSE_STAFF`.

## Kriteria penerimaan

- [ ] `npm run build` lulus.
- [ ] Alur manual: unit `RETURNED` → Periksa Baik → `IN_STOCK`, riwayat bertambah.

## Tes

- Pemeriksaan manual di browser; tangkapan layar di PR.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
