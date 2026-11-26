---
id: SCM-C-06
title: "Batas 10 ONT per teknisi dan tampilan kepemilikan"
slice: C
tier: 2
priority: P2
owner: sam
status: TODO
contract: "DRAFT (`GET /assets/technicians/{employee_id}`)"
depends_on: [SCM-0, SCM-C-01]
touches:
  - "services/scm-api/app/assets/**"
  - "services/scm-api/tests/assets/**"
spec: "spec.md#f9-tier-2"
---

# SCM-C-06: Batas 10 ONT per teknisi dan tampilan kepemilikan

## Konteks

Aturan brief: satu teknisi memegang maksimal 10 unit ONT.

## Yang dikerjakan

- `AssetPort.mark_with_technician` menolak bila jumlah unit `WITH_TECHNICIAN` teknisi setelah operasi lebih dari 10: `409 TECHNICIAN_LIMIT_EXCEEDED` dengan `details` (`current`, `requested`, `limit`).
- `GET /api/v1/assets/technicians/{employee_id}`: daftar unit yang dipegang dan jumlahnya.
- Layar kecil di `/assets` (filter per teknisi).

## Kriteria penerimaan

- [ ] Teknisi dengan 9 unit mendapat 1 lagi (10): berhasil; tambah 1 lagi: `409`.
- [ ] Unit yang kemudian `INSTALLED` atau `RETURNED` tidak dihitung.

## Tes

- `tests/assets/test_technician_cap.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
