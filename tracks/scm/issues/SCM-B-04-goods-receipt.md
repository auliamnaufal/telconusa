---
id: SCM-B-04
title: "Penerimaan barang (GR)"
slice: B
tier: 1
priority: P0
owner: Makro
status: TODO
contract: "DRAFT (`POST …/receipts`)"
depends_on: [SCM-0, SCM-B-03]
touches:
  - "services/scm-api/app/procurement/**"
  - "services/scm-api/tests/procurement/**"
spec: "spec.md#f8-pengadaan-slice-b"
---

# SCM-B-04: Penerimaan barang (GR)

## Konteks

Stok bertambah hanya setelah penerimaan. Penerimaan memulihkan permintaan `PENDING_STOCK`.

## Yang dikerjakan

- `POST /purchase-orders/{po_no}/receipts` (body `{warehouse_code, lines}`), PO harus `APPROVED` atau `PARTIALLY_RECEIVED`.
- Per baris: `qty ≤ sisa` (`409 OVER_RECEIPT`), `ledger.receive`, SKU serial memanggil `AssetPort.register_units` dan mengembalikan nomor seri, `qty_received` naik.
- PO menjadi `PARTIALLY_RECEIVED` atau `RECEIVED`; buat `GoodsReceipt` (`GR-`).
- Panggil `StockRequestPort.reevaluate_pending` untuk tiap SKU dan gudang.
- `goods.received` belum diterbitkan (kontrak belum ada).

## Kriteria penerimaan

- [ ] Penerimaan sebagian: PO `PARTIALLY_RECEIVED`, saldo naik sebesar qty, 2 unit ONT baru berstatus `IN_STOCK` dengan nomor seri `SN-ONT-…`.
- [ ] Penerimaan melebihi sisa: `409 OVER_RECEIPT`; PO belum `APPROVED`: `409 INVALID_TRANSITION`.
- [ ] Setelah barang masuk, `reevaluate_pending` terpanggil dengan SKU dan gudang yang benar.
- [ ] Respons memuat `gr_no`, `po_status`, `serial_numbers`.

## Tes

- `tests/procurement/test_goods_receipt.py` dengan fake `AssetPort` dan `StockRequestPort`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
