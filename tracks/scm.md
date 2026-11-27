---
track: scm
owner_team: Kelompok SCM
updated: '2026-11-25'
folders: [apps/scm-web, services/scm-api]
owns:
- {entity: Item, id_format: SKU}
- {entity: SerializedUnit, id_format: SN-ONT-2026-000001}
- {entity: PackageKit, id_format: per SKU paket}
- {entity: StockRequest, id_format: SR-2026-000001}
- {entity: PurchaseRequest, id_format: PR-2026-0001}
- {entity: PurchaseOrder, id_format: PO-2026-0001}
- {entity: Vendor, id_format: VEN-0001}
- {entity: Warehouse, id_format: WH-BDG}
provides:
  api:
  - {id: 'GET /api/v1/stock/{sku}', status: MOCKED, since: '2026-11-25'}
  - {id: 'GET /api/v1/package-kits/{sku}', status: LIVE, since: '2026-11-27', test: services/scm-api/tests/catalog/test_package_kit.py}
  - {id: GET /api/v1/stock-requests, status: LIVE, since: '2026-11-26', test: services/scm-api/tests/stock/test_stock_request_api.py}
  - {id: 'GET /api/v1/stock-requests/{stock_request_no}', status: LIVE, since: '2026-11-26', test: services/scm-api/tests/stock/test_stock_request_api.py}
  - {id: 'POST /api/v1/stock-requests/{stock_request_no}/issue', status: LIVE, since: '2026-11-26', test: services/scm-api/tests/stock/test_issue.py}
  - {id: 'POST /api/v1/stock-requests/{stock_request_no}/issue-extra', status: LIVE, since: '2026-11-26', test: services/scm-api/tests/stock/test_issue_extra.py}
  - {id: 'POST /api/v1/stock-requests/{stock_request_no}/flag-damaged', status: LIVE, since: '2026-11-26', test: services/scm-api/tests/stock/test_flag_damaged.py}
  - {id: POST /api/v1/purchase-orders, status: MOCKED, since: '2026-11-25'}
  - {id: GET /api/v1/dashboard/summary, status: MOCKED, since: '2026-11-25'}
  events:
  - {id: stockrequest.ready, status: LIVE, since: '2026-11-26', test: services/scm-api/tests/stock/test_ticket_created.py}
  - {id: stockrequest.pending, status: LIVE, since: '2026-11-26', test: services/scm-api/tests/stock/test_ticket_created.py}
  - {id: stock.issued, status: LIVE, since: '2026-11-26', test: services/scm-api/tests/stock/test_issue.py}
  - {id: stock.returned, status: LIVE, since: '2026-11-26', test: services/scm-api/tests/stock/test_items_reported.py}
consumes:
  api:
  - {id: POST /api/v1/budgets/check, from: finance, status: PLANNED}
  events:
  - {id: ticket.assigned, from: crm, status: MOCKED}
  - {id: ticket.created, from: crm, status: MOCKED}
  - {id: ticket.items_reported, from: crm, status: MOCKED}
---

# Track SCM

**Pemilik:** Kelompok SCM. **Folder:** `apps/scm-web` (SCM Control Tower), `services/scm-api`.

## Lingkup

SCM memiliki barang dan stok, daftar barang per paket (`PackageKit`), permintaan barang dari tiket (`StockRequest`), pengadaan, dan retur. Semua status barang diubah staf SCM, termasuk `WITH_TECHNICIAN`. Teknisi membawa satu paket barang sesuai paketnya dan mengembalikan yang tidak terpakai.

## Dokumen kerja SCM

Spesifikasi, rencana, glosarium, dan pekerjaan track ini ada di `tracks/scm/` (dimiliki Kelompok SCM, bukan area bersama).

| Berkas | Isi |
| :--- | :--- |
| `tracks/scm/spec.md` | Spesifikasi lengkap: model data, status, alur, API, event, layar, tingkat (tier) |
| `tracks/scm/plan.md` | Pembagian slice, fase, aturan kerja tim, definisi selesai |
| `tracks/scm/issues/` | Satu berkas per issue dengan `status`, `owner`, `touches`, kriteria penerimaan; indeks di `issues/README.md` |
| `tracks/scm/GLOSSARY.md` | Istilah SCM (melengkapi glosarium `CONTEXT.md`) |
| `tracks/scm/contract-extension.md` | Usulan perluasan kontrak bersama |
| `tracks/scm/docs/adr/` | Keputusan arsitektur SCM |

**Alur agen pemrograman SCM:** baca `services/scm-api/AGENTS.md` atau `apps/scm-web/AGENTS.md`; kerjakan hanya satu issue dari `tracks/scm/issues/`, sesuai `touches`; perbarui `status` issue dan baris kontrak di berkas ini; jalankan `python tools/check_contracts.py`.

Backlog di bawah dikerjakan oleh issue berikut:

| Temuan backlog | Issue |
| :--- | :--- |
| P0 event tanpa tanda tangan; P1 outbox `SENT` tanpa relay | `SCM-0-01`, `SCM-0-02` |
| P0 cek anggaran gagal-buka | `SCM-B-01`, `SCM-B-02` |
| P0 PO langsung `APPROVED` | `SCM-B-02`, `SCM-B-03` |
| P1 belum ada `StockRequest` | `SCM-A-01` sampai `SCM-A-10` |
| P1 daftar barang tertanam | `SCM-D-02` |
| P1 `GET /stock/{sku}` tanpa autentikasi | `SCM-D-03` |
| P1 event lama `kit.reconciled` dan nomor seri tidak `INSTALLED` | `SCM-A-06`, `SCM-C-01` |
| P1 anggaran tidak ditahan, tidak ada goods receipt | `SCM-B-04`; `po.approved` setelah kontrak (`SCM-D-08`) |
| P1 nomor PO dari `count()+1` | `SCM-B-02` |
| P2 siklus P2P penuh | Tier 2 dan 3 di `tracks/scm/spec.md` bagian 2 |

## Slice requirements (acceptance untuk demo)

1. **Daftar barang per paket** dimiliki SCM: `GET /api/v1/package-kits/{sku}` (contoh `HOME-50` = 1 ONT-01 + 50 m CBL-FO), scope `packagekits:read`.
2. **Permintaan barang otomatis** (langkah 5): `ticket.created` membuat `StockRequest` dari `required_items`. Stok cukup menghasilkan `READY_TO_ISSUE` dan `stockrequest.ready`; stok kurang menghasilkan `PENDING_STOCK`, permintaan pembelian ke vendor (dengan cek anggaran lewat Finance, `POST /api/v1/budgets/check`), dan `stockrequest.pending`. Ketika barang masuk, status kembali `READY_TO_ISSUE`.
3. **Pengeluaran oleh staf SCM** (langkah 7): `POST /api/v1/stock-requests/{no}/issue` mengubah status menjadi `ISSUED` dan unit bernomor seri menjadi `WITH_TECHNICIAN`, lalu menerbitkan `stock.issued`. Teknisi tidak mengubah status barang.
4. **Barang tambahan**: staf SCM menambah baris pengeluaran pada tiket yang sama (`issue-extra`) tanpa persetujuan ulang. Koordinasi kekurangan di lapangan lewat telepon dan tidak masuk sistem.
5. **Laporan pemakaian** (langkah 9): `ticket.items_reported` memperbarui persediaan dari `used` dan `returned`; SCM memeriksa `issued = used + returned`, menandai selisih, dan menerbitkan `stock.returned`.
6. **Barang rusak** ditandai dan diurus staf SCM (`flag-damaged`).
7. **Penanda retur tertunda**: permintaan yang sudah `ISSUED` tanpa laporan teknisi tampil sebagai "return pending" di layar SCM dan di tiket.
8. **Stok indikatif untuk CRM**: `GET /api/v1/stock/{sku}`, scope `stock:read`.

## Integrasi

- Menyediakan stok, daftar barang paket, permintaan barang, pengadaan.
- Menerima event: `ticket.created`, `ticket.assigned`, `ticket.items_reported`.
- Memanggil Finance `POST /api/v1/budgets/check` dengan token layanan; kegagalan Finance menahan PR, tidak meloloskannya.

## Backlog

Temuan review `services/scm-api` per 2026-11-25. **P0** dikerjakan lebih dulu.

| Prioritas | Temuan | Lokasi |
| :--- | :--- | :--- |
| P0 | `receive_event` menerima event tanpa tanda tangan; pakai `create_events_router`. | `app/main.py` `receive_event` |
| P0 | Cek anggaran gagal-buka: `budget_approved = True` dan `except Exception: pass`, sehingga PO Rp35 miliar lolos saat Finance mati. Tahan PR bila Finance tak terjangkau. | `create_po` |
| P0 | PO langsung `APPROVED` oleh pembuatnya tanpa rantai persetujuan (Rp10 juta dan Rp100 juta) dan tanpa pemisahan tugas. | `create_po` |
| P1 | Belum ada `StockRequest`; tambah model dan endpoint `/stock-requests/*`. Reservasi, pengeluaran, dan retur belum ada di API. | `models.py`, `main.py` |
| P1 | `/items/requirements` memakai daftar barang tertanam (ONT 1, kabel 50 m); ganti `GET /package-kits/{sku}` dari tabel. | `item_requirements` |
| P1 | `GET /stock/{sku}` tanpa autentikasi; ganti token layanan `stock:read`. Ketersediaan menjumlah semua gudang, bukan kota pelanggan. | `get_stock` |
| P1 | Event lama `kit.reconciled` diganti `ticket.items_reported`; saldo selalu masuk `WH-BDG` dan nomor seri ONT tidak diubah menjadi `INSTALLED` oleh handler. | `receive_event`, `reconcile_kit` |
| P1 | Anggaran tidak pernah ditahan (`po.approved` tidak punya handler di Finance); PO tidak punya goods receipt. | `create_po` |
| P1 | Nomor `PO-2026-…` dari `count()+1`; pakai `shared.ids.next_code`. | `create_po` |
| P1 | `outbox_events` berstatus `SENT` sejak dibuat dan tidak ada relay; pakai `shared.outbox`. | `models.py`, `create_po` |
| P2 | Siklus P2P penuh (goods receipt, tagihan vendor, three-way match, `stock.low`) di luar demo. | – |

## Open items

- Mekanisme penerimaan barang vendor dan penutupan PO (`vendor.paid`) setelah demo.
- Apakah staf SCM perlu konfirmasi fisik retur selain laporan teknisi (sementara: tanda "return pending" saja).

## Requests

_Belum ada. Tim lain menambah baris `- dari <track>, <tanggal>: <permintaan>` lewat PR._

## Decisions

- 2026-11-25: SCM memiliki daftar barang paket; stok kurang setelah pembayaran menghasilkan `PENDING_STOCK` di SCM, bukan status tiket; teknisi melaporkan terpakai dan kembali lewat CRM; staf SCM yang mengubah status barang.

## Cara membaca status

| Status | Arti untuk yang disediakan | Arti untuk yang dikonsumsi |
| :--- | :--- | :--- |
| `PLANNED` | Ada di kontrak, belum ada contoh atau implementasi | Belum diintegrasikan |
| `MOCKED` | Contoh respons atau event ada di `contracts/` dan bisa dipakai lewat mock | Sudah diintegrasikan terhadap mock |
| `LIVE` | Sudah diimplementasikan dan lolos tes (`test:` wajib diisi) | Sudah diintegrasikan terhadap layanan asli |
| `CHANGING` | Kontrak sedang diubah; baca bagian Decisions | Sedang menyesuaikan |
| `DEPRECATED` | Akan dihapus; pakai penggantinya | Harus pindah |

Hanya tim pemilik yang mengubah file ini. Tim lain menulis permintaan di bagian **Requests** lewat PR. Setelah mengubah front matter, jalankan `python tools/check_contracts.py` agar `tracks/STATUS.md` ikut diperbarui.
