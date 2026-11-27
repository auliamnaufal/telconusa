---
id: SCM-D-02
title: "Daftar barang paket: API untuk CRM dan pengelolaan"
slice: D
tier: 1
priority: P0
owner: mike
status: DONE
contract: "K (`GET /package-kits/{sku}`) + DRAFT (admin)"
depends_on: [SCM-0]
touches:
  - "services/scm-api/app/catalog/**"
  - "services/scm-api/tests/catalog/**"
spec: "spec.md#3-katalog-awal"
---

# SCM-D-02: Daftar barang paket: API untuk CRM dan pengelolaan

## Konteks

Langkah 4 alur demo: CRM mengambil daftar barang paket dan menyalinnya ke tiket. Menggantikan daftar tertanam di kode lama.

## Yang dikerjakan

- `GET /api/v1/package-kits/{sku}` dengan token layanan scope `packagekits:read`; respons sesuai kontrak; SKU tanpa daftar menjawab `404` format galat baku.
- `GET /package-kits` dan `PUT /package-kits/{sku}` (ganti seluruh baris, `SCM_MANAGER`); baris merujuk `Item` yang ada.

## Kriteria penerimaan

- [x] `HOME-50` menjawab 1 `ONT-01` UNIT dan 50 `CBL-FO` METER; sama dengan contoh kontrak.
- [x] Tanpa token: `401`; scope salah: `403`; `MOB-PRE-50`: `404`.
- [x] `PUT` dengan SKU barang tak dikenal: `422`.

## Tes

- `tests/catalog/test_package_kit.py`; validasi respons terhadap contoh di `contracts/openapi/scm.yaml`.

## Selesai bila

- [x] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [x] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [x] `status` issue ini diubah menjadi `DONE` di PR yang sama.
