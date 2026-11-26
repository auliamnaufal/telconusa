---
id: SCM-D-07
title: "Status LIVE di `tracks/scm.md` dan panduan demo lokal"
slice: D
tier: 1
priority: P1
owner: mike
status: TODO
contract: "none"
depends_on: [SCM-0, SCM-D-09]
touches:
  - "tracks/scm.md"
  - "tracks/scm/demo.md"
spec: "spec.md#11-pengujian"
---

# SCM-D-07: Status LIVE di `tracks/scm.md` dan panduan demo lokal

## Konteks

Status harus jujur: `LIVE` hanya dengan tes yang lulus. Tim lain membaca `tracks/STATUS.md`.

## Yang dikerjakan

- Setelah slice menyelesaikan issue yang menyentuh API atau event kontrak, ubah baris terkait di `provides` menjadi `LIVE` dengan `since` dan `test:` (jalur berkas tes), lalu jalankan `python tools/check_contracts.py`. Issue ini memeriksa tidak ada baris `LIVE` tanpa tes dan tidak ada tes lulus yang masih `MOCKED`.
- Tulis `tracks/scm/demo.md`: perintah menjalankan `scm-api` dengan mock tetangga, mengirim `ticket.created`, `ticket.assigned`, `ticket.items_reported` memakai `tools/send_fixture.py`, dan urutan klik di `scm-web` untuk langkah 5, 7, 9 dan skenario gagal 1.

## Kriteria penerimaan

- [ ] `python tools/check_contracts.py --check` lulus.
- [ ] Panduan demo dijalankan dari awal oleh orang selain penulisnya dan menghasilkan alur yang sama.

## Tes

- Menjalankan panduan demo apa adanya; catat hasilnya di PR.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
