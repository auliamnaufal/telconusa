---
id: SCM-A-10
title: "Layar permintaan barang"
slice: A
tier: 1
priority: P1
owner: Naufal
status: TODO
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
- `/stock-requests/[no]`: baris (diperlukan, dikeluarkan, terpakai, kembali, rusak), nomor seri, tombol Keluarkan (pilih nomor seri yang direservasi), Barang tambahan, Tandai rusak, Batalkan.
- Tombol hanya tampil untuk `SCM_MANAGER` dan `WAREHOUSE_STAFF`; galat API tampil lewat `Toast`.
- Bila API tindakan (`SCM-A-04` dan seterusnya) belum selesai, tombolnya tidak ditampilkan; jangan memakai data palsu.

## Kriteria penerimaan

- [ ] `npm run build` lulus.
- [ ] Alur manual: permintaan `READY_TO_ISSUE` → Keluarkan → status `ISSUED` tampil dengan penanda return pending.
- [ ] Galat `INSUFFICIENT_STOCK` dan `TECHNICIAN_NOT_ASSIGNED` tampil dengan pesan API.

## Tes

- Pemeriksaan manual di browser terhadap `scm-api` lokal; lampirkan tangkapan layar di PR.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
