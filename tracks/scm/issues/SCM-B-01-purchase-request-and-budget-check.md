---
id: SCM-B-01
title: "PR, cek anggaran Finance, dan implementasi `ProcurementPort`"
slice: B
tier: 1
priority: P0
owner: Makro
status: TODO
contract: "K (konsumsi `POST /budgets/check`)"
depends_on: [SCM-0]
touches:
  - "services/scm-api/app/procurement/**"
  - "services/scm-api/tests/procurement/**"
spec: "spec.md#f8-pengadaan-slice-b; spec.md#53-permintaan-pembelian-purchaserequest"
---

# SCM-B-01: PR, cek anggaran Finance, dan implementasi `ProcurementPort`

## Konteks

Memperbaiki P0: cek anggaran gagal-buka. Finance mati harus menahan PR, bukan meloloskannya.

## Yang dikerjakan

- Klien Finance `app/procurement/finance_client.py`: `POST {FINANCE_API_URL}/api/v1/budgets/check` dengan `shared.service_auth.service_headers("scm", ["budgets:check"], correlation_id)`, timeout 5 detik. Galat jaringan, timeout, dan 5xx menjadi hasil "tidak terjangkau", dicatat, tidak ditelan.
- Layanan PR: buat PR (`PR-` dari sequence) dengan status mesin 5.3; hasil `approved` → `BUDGET_OK`, `approved: false` → `BUDGET_REJECTED`, tidak terjangkau → `PENDING_BUDGET`.
- Implementasi `ProcurementPort.request_purchase`: satu PR per permintaan barang, satu baris per SKU kurang, perkiraan biaya `qty × unit_cost`; panggilan kedua untuk permintaan yang sama mengembalikan PR yang sama.
- Implementasi `ProcurementPort.request_low_stock_purchase` (dipanggil Slice A saat stok tersedia menyeberang ke bawah ROP): buat PR `source=LOW_STOCK` untuk SKU dan gudang itu; idempoten: bila sudah ada PR `LOW_STOCK` terbuka (`PENDING_BUDGET` atau `BUDGET_OK`), kembalikan nomornya tanpa membuat PR kedua.
- Pekerjaan berkala mengulang cek anggaran PR `PENDING_BUDGET`.
- `GET /purchase-requests` dan `GET /purchase-requests/{no}` (role SCM dan `DIRECTOR`).

## Kriteria penerimaan

- [ ] Finance menjawab `approved: true`: PR `BUDGET_OK`. `approved: false`: `BUDGET_REJECTED`.
- [ ] Finance mati atau timeout: PR tetap `PENDING_BUDGET`; ketika Finance hidup lagi pekerjaan berkala membuatnya `BUDGET_OK`.
- [ ] PO Rp35 miliar saat Finance mati tidak pernah lolos.
- [ ] Pemanggilan Finance membawa token layanan dan `X-Correlation-Id`.
- [ ] Tidak ada `except: pass`.
- [ ] `request_low_stock_purchase` dua kali untuk SKU dan gudang yang sama menghasilkan satu PR `LOW_STOCK`.

## Tes

- `tests/procurement/test_purchase_request.py` dengan Finance palsu (`httpx.MockTransport`) untuk setiap hasil.

## Di luar issue ini

- Pembuatan PO (`SCM-B-02`).

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
