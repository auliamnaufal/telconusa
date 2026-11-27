---
id: SCM-B-05
title: "Layar pengadaan"
slice: B
tier: 1
priority: P1
owner: Makro
status: REVIEW
contract: "none"
depends_on: [SCM-0, SCM-0-06, SCM-B-02]
touches:
  - "apps/scm-web/src/app/(app)/procurement/**"
  - "apps/scm-web/src/features/procurement/**"
spec: "spec.md#10-layar-scm-web"
---

# SCM-B-05: Layar pengadaan

## Konteks

Layar kerja staf pengadaan, manajer SCM, dan penyetuju.

## Yang dikerjakan

- `/procurement`: daftar PR (status, anggaran) dan PO; form buat PO.
- `/procurement/purchase-orders/[no]`: baris, rantai persetujuan (siapa sudah, role apa yang kurang), tombol Setujui atau Tolak sesuai role pengguna dan hanya bila boleh, form Terima barang.
- Status anggaran tampil jelas: `PENDING_BUDGET` dengan keterangan "menunggu Finance".
- Tombol untuk API yang belum selesai tidak ditampilkan.

## Kriteria penerimaan

- [ ] `npm run build` lulus.
- [ ] Alur manual: buat PO Rp35 juta → muncul `PENDING_APPROVAL` dengan dua role dibutuhkan → disetujui dua role → terima barang.
- [ ] Pembuat PO tidak melihat tombol Setujui pada PO-nya.

## Tes

- Pemeriksaan manual di browser; tangkapan layar di PR.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
