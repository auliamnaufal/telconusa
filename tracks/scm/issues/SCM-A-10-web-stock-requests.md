---
id: SCM-A-10
title: "Layar permintaan barang"
slice: A
tier: 1
priority: P1
owner: Naufal
status: DONE
contract: "none"
depends_on: [SCM-0, SCM-0-06, SCM-A-03, SCM-A-04]
touches:
  - "apps/scm-web/src/app/(app)/stock-requests/**"
  - "apps/scm-web/src/features/stock-requests/**"
spec: "spec.md#10-layar-scm-web"
---

# SCM-A-10: Layar permintaan barang

## Konteks

Layar kerja utama staf gudang.

## Yang dikerjakan

- `/stock-requests`: tabel dengan filter status dan kota, badge status, penanda "return pending" dan selisih.
- `/stock-requests/[no]`: baris (diperlukan, dikeluarkan, terpakai, kembali, rusak; baris tambahan bertanda), tombol Keluarkan (unit ONT yang direservasi dipakai otomatis, urut masuk tertua; daftar nomor seri ada di layar Aset ONT, Slice C), Barang tambahan, Tandai rusak, Batalkan.
- Tombol hanya tampil untuk `SCM_MANAGER` dan `WAREHOUSE_STAFF`; galat API tampil lewat `Toast`.
- Bila API tindakan (`SCM-A-04` dan seterusnya) belum selesai, tombolnya tidak ditampilkan; jangan memakai data palsu.

## Kriteria penerimaan

- [x] `npm run build` lulus.
- [x] Alur manual: permintaan `READY_TO_ISSUE` → Keluarkan → status `ISSUED` tampil dengan penanda return pending.
- [x] Galat API (mis. `INSUFFICIENT_STOCK`) tampil dengan pesan API dan dialog tetap terbuka; permintaan tanpa teknisi tidak bisa dikeluarkan dari dialog.

## Tes

- Pemeriksaan manual di browser terhadap `scm-api` lokal; lampirkan tangkapan layar di PR.

## Selesai bila

- [x] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [x] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [x] `status` issue ini diubah menjadi `DONE` di PR yang sama.
