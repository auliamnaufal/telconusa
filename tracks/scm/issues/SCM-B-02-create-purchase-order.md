---
id: SCM-B-02
title: "Pembuatan PO dan daftar PO"
slice: B
tier: 1
priority: P0
owner: Makro
status: TODO
contract: "K (`POST /purchase-orders`) + DRAFT (lainnya)"
depends_on: [SCM-0, SCM-B-01]
touches:
  - "services/scm-api/app/procurement/**"
  - "services/scm-api/tests/procurement/**"
spec: "spec.md#f8-pengadaan-slice-b"
---

# SCM-B-02: Pembuatan PO dan daftar PO

## Konteks

PO tidak boleh lahir `APPROVED` oleh pembuatnya (P0).

## Yang dikerjakan

- `POST /api/v1/purchase-orders` (bentuk kontrak): cek anggaran lebih dulu; Finance tak terjangkau → `503 BUDGET_CHECK_UNAVAILABLE` dan tidak ada yang dibuat; tidak cukup → `409 BUDGET_INSUFFICIENT`; lolos → PR `PO_CREATED` dan PO `PENDING_APPROVAL` dibuat atomik. Harga satuan dari `Item.unit_cost`.
- `POST /purchase-requests/{no}/create-po` (PR `BUDGET_OK`, body `{vendor_code, unit_prices}`).
- `GET /purchase-orders` dan `GET /purchase-orders/{po_no}` (baris, `approvals`, `required_roles`, `receipts`).
- `required_roles` dihitung dari total (spec bagian F8.3), disimpan saat PO dibuat.
- `Idempotency-Key` pada kedua `POST`.

## Kriteria penerimaan

- [ ] Respons `201` memuat `po_no`, `total_amount`, `status: PENDING_APPROVAL`, `budget_remaining_after_check`.
- [ ] Total Rp5 juta → `required_roles = [SCM_MANAGER]`; Rp35 juta → plus `FINANCE_MANAGER`; Rp150 juta → plus `DIRECTOR`.
- [ ] Finance mati: `503`, tabel PR dan PO tidak bertambah.
- [ ] Vendor atau SKU tak dikenal: `404`/`422` format galat baku. Role selain `SCM_MANAGER` dan `PROCUREMENT_STAFF`: `403`.
- [ ] Kode `PO-` dari `next_code`.

## Tes

- `tests/procurement/test_create_po.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
