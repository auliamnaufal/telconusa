---
id: SCM-B-03
title: "Persetujuan PO berjenjang"
slice: B
tier: 1
priority: P0
owner: Makro
status: REVIEW
contract: "DRAFT (`approve`, `reject`)"
depends_on: [SCM-0, SCM-B-02]
touches:
  - "services/scm-api/app/procurement/**"
  - "services/scm-api/tests/procurement/**"
spec: "spec.md#f8-pengadaan-slice-b; ADR-0002"
---

# SCM-B-03: Persetujuan PO berjenjang

## Konteks

Memperbaiki P0: PO langsung disetujui pembuatnya tanpa rantai persetujuan atau pemisahan tugas.

## Yang dikerjakan

- `POST /purchase-orders/{po_no}/approve` dan `/reject` (body `{comment}`), penyetuju dan role dari JWT.
- Aturan F8.3: pemisahan tugas, satu role sekali, role di luar rantai ditolak, satu penolakan membuat `REJECTED`, `APPROVED` setelah semua `required_roles` menyetujui.
- Setiap keputusan menyimpan `PoApproval` dan menulis `AuditLog`.
- `po.approved` belum diterbitkan (kontrak belum ada).

## Kriteria penerimaan

- [ ] Pembuat PO menyetujui PO-nya: `403 APPROVAL_SELF_FORBIDDEN`.
- [ ] `SCM_MANAGER` menyetujui dua kali: `409 DUPLICATE_APPROVAL`. `DIRECTOR` menyetujui PO Rp5 juta: `403 APPROVAL_ROLE_NOT_REQUIRED`.
- [ ] PO Rp150 juta tetap `PENDING_APPROVAL` sampai tiga role menyetujui (urutan bebas), lalu `APPROVED`.
- [ ] Satu penolakan: `REJECTED`; setelahnya persetujuan ditolak `409 INVALID_TRANSITION`.

## Tes

- `tests/procurement/test_approval.py`: tabel kasus per jenjang.

## Di luar issue ini

- Menerbitkan `po.approved` (lanjutan setelah kontrak).

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
