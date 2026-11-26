---
id: SCM-C-01
title: "Implementasi `AssetPort` dan riwayat status unit"
slice: C
tier: 1
priority: P0
owner: sam
status: TODO
contract: "none"
depends_on: [SCM-0]
touches:
  - "services/scm-api/app/assets/**"
  - "services/scm-api/tests/assets/**"
spec: "spec.md#52-unit-bernomor-seri-serializedunit"
---

# SCM-C-01: Implementasi `AssetPort` dan riwayat status unit

## Konteks

Register ONT per nomor seri (P-03). Semua perubahan status unit lewat satu tempat sehingga selalu tercatat.

## Yang dikerjakan

- Implementasikan semua metode `AssetPort` (lihat `SCM-0-04`) dan daftarkan di `app/assets/__init__.py`.
- Setiap perubahan status memakai `shared.transitions` mesin `UNIT` dan menulis `UnitStatusLog` (dari, ke, `ref`, pelaku).
- `register_units`: nomor seri `SN-ONT-{tahun}-{n:06d}` dari `next_code`, `IN_STOCK`, `received_at` sekarang, `received_gr_no`.
- `reserve_units`: pilih `IN_STOCK` di gudang itu dengan `received_at` tertua (FIFO), jadi `RESERVED`, kaitkan ke `stock_request_no`; kurang dari qty → `INSUFFICIENT_STOCK` tanpa mengubah apa pun.
- `mark_with_technician` hanya menerima unit `RESERVED` milik permintaan itu (`SERIAL_NOT_RESERVED`).

## Kriteria penerimaan

- [ ] `reserve_units` memilih nomor seri tertua lebih dulu; kekurangan tidak menyisakan unit setengah direservasi.
- [ ] `release_units` mengembalikan `RESERVED → IN_STOCK`.
- [ ] Transisi yang tidak sah menjawab `409 INVALID_TRANSITION` dengan `allowed`.
- [ ] Setiap perubahan menulis satu baris `UnitStatusLog`.

## Tes

- `tests/assets/test_asset_port.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
