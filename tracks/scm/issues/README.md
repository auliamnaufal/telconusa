# Issue SCM

Satu berkas satu issue. Rencana dan urutannya ada di [`../plan.md`](../plan.md), isi fitur di [`../spec.md`](../spec.md).

## Cara memakai

1. Pilih issue `status: TODO` dari slice Anda yang `depends_on`-nya sudah `DONE`. Isi `owner:` dengan nama Anda dan ubah `status: IN_PROGRESS` di PR pertama atau commit pertama cabang Anda.
2. Cabang: `scm/<id>-<slug>` (contoh `scm/SCM-A-04-issue-stock-request`). Satu issue, satu PR.
3. Ubah hanya berkas di `touches`. Bila perlu menyentuh berkas lain, berhenti dan tulis di PR atau minta pemilik slice itu menambah issue.
4. Selesai: semua kotak kriteria dicentang, tes lulus, `status: DONE` di PR yang sama. Status: `TODO`, `IN_PROGRESS`, `REVIEW`, `DONE`.
5. `depends_on: [SCM-0]` berarti `SCM-0-01` sampai `SCM-0-05` selesai. Issue web juga menyebut `SCM-0-06`.
6. `contract`: `K` = sudah di kontrak bersama; `DRAFT` = bentuknya ada di [`../contract-extension.md`](../contract-extension.md), dikembangkan lebih dulu dan belum boleh ditandai `LIVE`.

Aturan `depends_on`: hanya Slice 0 atau issue sebelumnya di slice yang sama. Satu-satunya pengecualian adalah `SCM-D-09` dan `SCM-D-07`, issue integrasi yang memang menunggu slice lain.

## Slice 0: fondasi

| Issue | Judul | Tier | Prioritas | Status | Owner |
| :--- | :--- | :---: | :---: | :---: | :--- |
| [SCM-0-01](SCM-0-01-restructure-and-remove-legacy.md) | Restrukturisasi paket per slice dan hapus kode lama | 1 | P0 | DONE | Naufal |
| [SCM-0-02](SCM-0-02-core-infrastructure.md) | Infrastruktur inti: event, auth, galat, idempotensi, outbox, audit, harness tes | 1 | P0 | DONE | Naufal |
| [SCM-0-03](SCM-0-03-stock-ledger.md) | Buku besar stok | 1 | P0 | DONE | Naufal |
| [SCM-0-04](SCM-0-04-ports-and-machines.md) | Port antar-slice dan mesin status | 1 | P0 | DONE | Naufal |
| [SCM-0-05](SCM-0-05-models-migrations-seed.md) | Model semua slice, migrasi per slice, dan seed | 1 | P0 | DONE | Naufal |
| [SCM-0-06](SCM-0-06-web-shell.md) | Kerangka web: layout, login, navigasi, klien API, komponen dasar | 1 | P0 | DONE | Naufal |

## Slice A: permintaan barang dan pengeluaran

| Issue | Judul | Tier | Prioritas | Status | Owner |
| :--- | :--- | :---: | :---: | :---: | :--- |
| [SCM-A-01](SCM-A-01-handle-ticket-created.md) | Handler `ticket.created` menjadi permintaan barang | 1 | P0 | DONE | Naufal |
| [SCM-A-02](SCM-A-02-handle-ticket-assigned.md) | Handler `ticket.assigned` mengisi teknisi | 1 | P1 | DONE | Naufal |
| [SCM-A-03](SCM-A-03-stock-request-read-api.md) | GET daftar dan detail permintaan barang | 1 | P1 | DONE | Naufal |
| [SCM-A-04](SCM-A-04-issue-stock-request.md) | POST issue: pengeluaran ke teknisi | 1 | P0 | DONE | Naufal |
| [SCM-A-05](SCM-A-05-issue-extra.md) | POST issue-extra: barang tambahan | 1 | P1 | DONE | Naufal |
| [SCM-A-06](SCM-A-06-handle-items-reported.md) | Handler `ticket.items_reported`: laporan pemakaian | 1 | P0 | DONE | Naufal |
| [SCM-A-07](SCM-A-07-flag-damaged.md) | POST flag-damaged | 1 | P1 | DONE | Naufal |
| [SCM-A-08](SCM-A-08-cancel-and-expiry.md) | Pembatalan permintaan dan reservasi kedaluwarsa 72 jam | 1 | P1 | DONE | Naufal |
| [SCM-A-09](SCM-A-09-reevaluate-pending.md) | Implementasi `StockRequestPort.reevaluate_pending` | 1 | P0 | DONE | Naufal |
| [SCM-A-10](SCM-A-10-web-stock-requests.md) | Layar permintaan barang | 1 | P1 | DONE | Naufal |
| [SCM-A-11](SCM-A-11-fifo-lots.md) | FIFO per batch untuk barang non-serial | 2 | P2 | DONE | Naufal |
| [SCM-A-12](SCM-A-12-low-stock-purchase-request.md) | Stok di bawah ROP membuat PR otomatis | 2 | P2 | DONE | Naufal |

## Slice B: pengadaan

| Issue | Judul | Tier | Prioritas | Status | Owner |
| :--- | :--- | :---: | :---: | :---: | :--- |
| [SCM-B-01](SCM-B-01-purchase-request-and-budget-check.md) | PR, cek anggaran Finance, dan implementasi `ProcurementPort` | 1 | P0 | TODO | Makro |
| [SCM-B-02](SCM-B-02-create-purchase-order.md) | Pembuatan PO dan daftar PO | 1 | P0 | TODO | Makro |
| [SCM-B-03](SCM-B-03-po-approval-chain.md) | Persetujuan PO berjenjang | 1 | P0 | TODO | Makro |
| [SCM-B-04](SCM-B-04-goods-receipt.md) | Penerimaan barang (GR) | 1 | P0 | TODO | Makro |
| [SCM-B-05](SCM-B-05-web-procurement.md) | Layar pengadaan | 1 | P1 | TODO | Makro |
| [SCM-B-06](SCM-B-06-po-quotes.md) | Tiga penawaran untuk PO di atas Rp50 juta | 2 | P2 | TODO | Makro |

## Slice C: aset ONT dan retur

| Issue | Judul | Tier | Prioritas | Status | Owner |
| :--- | :--- | :---: | :---: | :---: | :--- |
| [SCM-C-01](SCM-C-01-asset-port-implementation.md) | Implementasi `AssetPort` dan riwayat status unit | 1 | P0 | TODO | sam |
| [SCM-C-02](SCM-C-02-asset-read-api.md) | Daftar dan detail unit ONT | 1 | P1 | TODO | sam |
| [SCM-C-03](SCM-C-03-inspect-returned-unit.md) | Pemeriksaan unit retur | 1 | P0 | TODO | sam |
| [SCM-C-04](SCM-C-04-web-assets.md) | Layar register aset ONT | 1 | P1 | TODO | sam |
| [SCM-C-05](SCM-C-05-lost-and-write-off.md) | Unit hilang dan hapus buku | 2 | P2 | TODO | sam |
| [SCM-C-06](SCM-C-06-technician-holding-cap.md) | Batas 10 ONT per teknisi dan tampilan kepemilikan | 2 | P2 | TODO | sam |

## Slice D: data master, API stok, dashboard, integrasi

| Issue | Judul | Tier | Prioritas | Status | Owner |
| :--- | :--- | :---: | :---: | :---: | :--- |
| [SCM-D-01](SCM-D-01-master-data-api.md) | API data master: barang, gudang, vendor | 1 | P1 | DONE | mike |
| [SCM-D-02](SCM-D-02-package-kit-api.md) | Daftar barang paket: API untuk CRM dan pengelolaan | 1 | P0 | DONE | mike |
| [SCM-D-03](SCM-D-03-stock-availability-api.md) | API stok indikatif untuk CRM dan saldo per gudang | 1 | P0 | DONE | mike |
| [SCM-D-04](SCM-D-04-dashboard-summary-api.md) | API ringkasan dashboard | 1 | P1 | DONE | mike |
| [SCM-D-05](SCM-D-05-web-dashboard-stock-catalog.md) | Layar dashboard, stok, dan katalog | 1 | P1 | TODO | mike |
| [SCM-D-06](SCM-D-06-audit-log-page.md) | Halaman dan API audit log | 2 | P2 | IN_PROGRESS | mike |
| [SCM-D-07](SCM-D-07-status-and-demo-guide.md) | Status LIVE di `tracks/scm.md` dan panduan demo lokal | 1 | P1 | TODO | mike |
| [SCM-D-08](SCM-D-08-contract-extension-pr.md) | PR kontrak bersama dari `contract-extension.md` | 1 | P1 | TODO | mike |
| [SCM-D-09](SCM-D-09-e2e-demo-scenario.md) | Tes skenario demo end-to-end dan skenario gagal | 1 | P0 | TODO | mike |
| [SCM-D-10](SCM-D-10-warehouse-transfer.md) | Transfer antar-gudang dengan konfirmasi terima | 2 | P2 | TODO | mike |

## Lanjutan (belum jadi issue)

Dibuat setelah syaratnya terpenuhi.

| Pekerjaan | Syarat |
| :--- | :--- |
| Terbitkan `stockrequest.cancelled` dari `SCM-A-08` | Kontrak di-merge lewat `SCM-D-08` |
| Terbitkan `po.approved` dari `SCM-B-03` dan `goods.received` dari `SCM-B-04` | Kontrak di-merge lewat `SCM-D-08` |
| Terbitkan `stock.low` dari `SCM-A-12` dan `shipment.delivered` dari `SCM-D-10` | Kontrak di-merge |
| Lepas reservasi saat `ticket.cancelled` | CRM mengontrakkan `ticket.cancelled` |
| Tier 3 (lihat `spec.md` bagian 2) | Tier 1 dan 2 selesai |
