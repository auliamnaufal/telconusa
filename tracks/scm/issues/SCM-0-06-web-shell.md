---
id: SCM-0-06
title: "Kerangka web: layout, login, navigasi, klien API, komponen dasar"
slice: 0
tier: 1
priority: P0
owner: Naufal
status: TODO
contract: "none"
depends_on: [SCM-0-01]
touches:
  - "apps/scm-web/src/app/**"
  - "apps/scm-web/src/components/**"
  - "apps/scm-web/src/lib/**"
spec: "spec.md#10-layar-scm-web"
---

# SCM-0-06: Kerangka web: layout, login, navigasi, klien API, komponen dasar

## Konteks

`apps/scm-web` hanya punya satu halaman monolit (tab kit, PO) yang memakai konsep lama. Setiap slice butuh rute sendiri di atas kerangka yang sama.

## Yang dikerjakan

- Layout `(app)` dengan navigasi per role (matriks di spec bagian 1.2 dan 10), pengaman login memakai `lib/auth.ts`, dan tombol keluar.
- `lib/api.ts`: pembungkus `fetch` dengan token, `X-Correlation-Id` baru per aksi pengguna, penguraian galat baku (`error.code`, `error.message`), dan penanganan `401` (ke login).
- Komponen dasar memakai token merek: `DataTable`, `StatusBadge`, `Toast`, `Field`, `Button`, `ConfirmDialog`.
- Folder rute kosong dengan halaman "belum dikerjakan": `/stock-requests`, `/procurement`, `/assets`, `/stock`, `/catalog`, `/audit`; halaman `/` sementara kosong. Hapus `page.tsx` monolit lama.

## Kriteria penerimaan

- [ ] `npm run build` di `apps/scm-web` lulus.
- [ ] Pengguna tanpa role SCM atau `DIRECTOR` dialihkan ke login.
- [ ] Menu yang tampil sesuai role (`WAREHOUSE_STAFF` tidak melihat Procurement, `PROCUREMENT_STAFF` tidak melihat Assets dan Stock Requests).
- [ ] Galat dari API tampil lewat `Toast` dengan `error.message`.

## Tes

- Pemeriksaan manual di browser untuk tiap role (catat hasilnya di PR); tes unit `lib/api.ts` bila ada runner.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
