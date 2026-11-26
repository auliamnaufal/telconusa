---
id: SCM-B-06
title: "Tiga penawaran untuk PO di atas Rp50 juta"
slice: B
tier: 2
priority: P2
owner: Makro
status: TODO
contract: "DRAFT (`quotes`, `submit`)"
depends_on: [SCM-0, SCM-B-03]
touches:
  - "services/scm-api/app/procurement/**"
  - "services/scm-api/tests/procurement/**"
spec: "spec.md#f9-tier-2"
---

# SCM-B-06: Tiga penawaran untuk PO di atas Rp50 juta

## Konteks

Aturan brief untuk PO besar.

## Yang dikerjakan

- PO dengan total di atas Rp50.000.000 lahir `DRAFT` dan butuh tiga `PoQuote` (vendor berbeda: vendor, harga, catatan).
- `POST /purchase-orders/{po_no}/quotes` dan `…/submit`; submit menolak bila penawaran kurang dari tiga (`409 QUOTES_REQUIRED`) lalu `PENDING_APPROVAL`.
- Layar mengikuti (tambah ke folder `procurement` web).

## Kriteria penerimaan

- [ ] Total Rp60 juta: status awal `DRAFT`; submit dengan dua penawaran `409 QUOTES_REQUIRED`; dengan tiga penawaran berbeda → `PENDING_APPROVAL`.
- [ ] Total Rp50 juta tepat tidak butuh penawaran.
- [ ] Vendor yang sama dua kali ditolak.

## Tes

- `tests/procurement/test_quotes.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
