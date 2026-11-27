---
id: SCM-D-06
title: "Halaman dan API audit log"
slice: D
tier: 2
priority: P2
owner: mike
status: IN_PROGRESS
contract: "DRAFT (`GET /audit-logs`)"
depends_on: [SCM-0, SCM-0-06]
touches:
  - "services/scm-api/app/catalog/**"
  - "services/scm-api/tests/catalog/**"
  - "apps/scm-web/src/app/(app)/audit/**"
  - "apps/scm-web/src/features/audit/**"
spec: "spec.md#f9-tier-2"
---

# SCM-D-06: Halaman dan API audit log

## Konteks

Jejak audit pembatalan, persetujuan, pemeriksaan, hapus buku.

## Yang dikerjakan

- `GET /api/v1/audit-logs` (filter `entity`, `entity_id`, `actor`, paginasi; `SCM_MANAGER`, `DIRECTOR`).
- Halaman `/audit`: tabel dengan filter.
- Pastikan issue-issue slice lain memakai `core.audit.record` (cek dan laporkan yang belum).

## Kriteria penerimaan

- [ ] Setelah pembatalan permintaan, persetujuan PO, dan pemeriksaan unit, tiap aksi muncul di audit dengan pelaku dan `correlation_id`.
- [x] Role lain mendapat `403`.

## Tes

- `tests/catalog/test_audit_logs.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
