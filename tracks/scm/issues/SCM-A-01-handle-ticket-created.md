---
id: SCM-A-01
title: "Handler `ticket.created` menjadi permintaan barang"
slice: A
tier: 1
priority: P0
owner: Naufal
status: TODO
contract: "K (event `ticket.created`, `stockrequest.ready`, `stockrequest.pending`)"
depends_on: [SCM-0]
touches:
  - "services/scm-api/app/stock/**"
  - "services/scm-api/tests/stock/**"
spec: "spec.md#f1-ticketcreated-menjadi-permintaan-barang-slice-a"
---

# SCM-A-01: Handler `ticket.created` menjadi permintaan barang

## Konteks

Langkah 5 alur demo. Inti reservasi 72 jam dan `PENDING_STOCK`.

## Yang dikerjakan

- Handler `ticket.created` di `app/stock/events.py` sesuai F1: gudang dari `city_code`, satu permintaan per `ticket_code`, kode `SR-` dari `next_code`.
- Semua baris cukup: `ledger.reserve`, `AssetPort.reserve_units` untuk SKU serial, `reserved_until = sekarang + 72 jam`, `READY_TO_ISSUE`, `stockrequest.ready` lewat `core.outbox.publish`.
- Ada baris kurang: tanpa reservasi sebagian, `PENDING_STOCK`, `ProcurementPort.request_purchase` untuk kekurangan, `stockrequest.pending` dengan `missing_items` dan `purchase_request_no`.

## Kriteria penerimaan

- [ ] Stok ONT dan kabel cukup di Bandung: `READY_TO_ISSUE`, `qty_reserved` naik, event `ready` ada di outbox.
- [ ] Stok ONT 0: `PENDING_STOCK`, tidak ada reservasi (baris kabel pun tidak ditahan), PR dibuat lewat port, event `pending` membawa `purchase_request_no`.
- [ ] Event yang sama dua kali (`event_id` sama) menghasilkan satu permintaan. `ticket_code` sama dengan `event_id` berbeda tetap satu permintaan.
- [ ] Ketersediaan diperiksa di gudang kota tiket, bukan jumlah semua gudang.
- [ ] Payload event lolos `contracts/events/*.schema.json`.

## Tes

- `tests/stock/test_ticket_created.py` memakai `ports.override` untuk fake `ProcurementPort` dan `AssetPort`; validasi payload terhadap skema JSON kontrak.

## Di luar issue ini

- `ticket.assigned` (`SCM-A-02`).

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
