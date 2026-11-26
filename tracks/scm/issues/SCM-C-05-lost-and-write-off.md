---
id: SCM-C-05
title: "Unit hilang dan hapus buku"
slice: C
tier: 2
priority: P2
owner: sam
status: TODO
contract: "DRAFT (`mark-lost`, `write-off`)"
depends_on: [SCM-0, SCM-C-03]
touches:
  - "services/scm-api/app/assets/**"
  - "services/scm-api/tests/assets/**"
spec: "spec.md#52-unit-bernomor-seri-serializedunit"
---

# SCM-C-05: Unit hilang dan hapus buku

## Konteks

Penanganan ONT hilang dan rusak permanen.

## Yang dikerjakan

- `POST …/mark-lost` (`WITH_TECHNICIAN` atau `INSTALLED` → `LOST`) dan `POST …/write-off` (`FAULTY` atau `LOST` → `WRITTEN_OFF`), keduanya wajib `reason`; `write-off` hanya `SCM_MANAGER`.
- `write-off` unit `FAULTY` di gudang memanggil `ledger.write_off`.
- Tulis `AuditLog`; tombol di layar detail aset.

## Kriteria penerimaan

- [ ] Unit `LOST` tidak muncul di stok tersedia; `WRITTEN_OFF` tidak bisa berubah lagi.
- [ ] `WAREHOUSE_STAFF` mencoba `write-off`: `403`.
- [ ] Tanpa `reason`: `422`.

## Tes

- `tests/assets/test_lost_write_off.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
