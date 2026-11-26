---
id: SCM-D-05
title: "Layar dashboard, stok, dan katalog"
slice: D
tier: 1
priority: P1
owner: mike
status: TODO
contract: "none"
depends_on: [SCM-0, SCM-0-06, SCM-D-01, SCM-D-03, SCM-D-04]
touches:
  - "apps/scm-web/src/app/(app)/page.tsx"
  - "apps/scm-web/src/app/(app)/stock/**"
  - "apps/scm-web/src/app/(app)/catalog/**"
  - "apps/scm-web/src/features/catalog/**"
spec: "spec.md#10-layar-scm-web"
---

# SCM-D-05: Layar dashboard, stok, dan katalog

## Konteks

Tampilan awal setiap pengguna SCM.

## Yang dikerjakan

- `/`: kartu stok tersedia, reservasi aktif, PO terbuka, ONT terpasang, retur tertunda; daftar permintaan barang terbaru.
- `/stock`: saldo per SKU dan gudang dengan penanda di bawah ROP.
- `/catalog`: barang, gudang, vendor, daftar barang paket; form ubah hanya untuk `SCM_MANAGER`.

## Kriteria penerimaan

- [ ] `npm run build` lulus.
- [ ] Angka dashboard sama dengan hasil `GET /dashboard/summary`.
- [ ] Saldo rusak tampil terpisah dari tersedia.

## Tes

- Pemeriksaan manual di browser; tangkapan layar di PR.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
