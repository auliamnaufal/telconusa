# Usulan perluasan kontrak SCM

Draf satu PR ke `contracts/` (area bersama, perlu persetujuan keempat track). Slice SCM tidak menunggu PR ini: mereka mengembangkan endpoint di bawah sesuai bentuk di sini dan menandai issue-nya `contract: DRAFT`. Aturan:

- Endpoint **D** boleh dibuat di `scm-api` dan dipakai `scm-web` sebelum kontraknya di-merge, tetapi **tidak** dicantumkan di `provides.api` `tracks/scm.md` dan tidak ditandai `LIVE` sampai kontraknya masuk.
- Event **usulan** tidak diterbitkan dan tidak diterima sebelum skemanya di-merge. Issue "terbitkan event" ada di daftar lanjutan `issues/README.md`.
- Endpoint D hanya dipakai `scm-web` (`x-consumers: []`), jadi review track lain cukup memastikan tidak ada benturan nama.

Issue yang mengubah file ini menjadi PR: `SCM-D-08`.

## 1. Endpoint baru (`contracts/openapi/scm.yaml`)

Semua di bawah `/api/v1`, `x-auth: user`, `x-consumers: []`. Role lengkap per endpoint ada di `spec.md` bagian 8.

| Endpoint | Slice | Ringkasan |
| :--- | :---: | :--- |
| `POST /stock-requests/{stock_request_no}/cancel` | A | Batalkan permintaan; body `{reason}`; `200` `{stock_request_no, status: CANCELLED}` |
| `GET /stock/{sku}`: parameter query opsional `city_code` (`JKT`, `BDG`, `SBY`) | D | Aditif, tidak merusak CRM. Membatasi ketersediaan ke gudang kota itu; tanpa `warehouse_code` dan `city_code`, jumlah semua gudang |
| `GET /dashboard/summary`: tambah `kpis.active_reservations`, `kpis.open_purchase_orders`, `kpis.ont_installed` | D | Aditif; kolom lama tidak berubah |
| `GET /stock/balances` | D | Saldo per `warehouse_code` dan `item_sku`: `qty_physical`, `qty_reserved`, `qty_damaged`, `qty_available`, `reorder_point`, `below_rop` |
| `GET /items`, `GET /warehouses`, `GET /vendors` | D | Daftar master, paginasi `page`/`limit` |
| `POST /items`, `PATCH /items/{sku}`, `POST /vendors`, `PATCH /vendors/{code}` | D | Kelola master (`SCM_MANAGER`) |
| `GET /package-kits`, `PUT /package-kits/{sku}` | D | Daftar dan ubah daftar barang paket (`SCM_MANAGER`) |
| `GET /assets/units`, `GET /assets/units/{serial_number}` | C | Filter `status`, `warehouse_code`, `technician_employee_id`; detail memuat riwayat status |
| `POST /assets/units/{serial_number}/inspect` | C | Body `{result: GOOD\|FAULTY, notes}` |
| `GET /purchase-requests`, `GET /purchase-requests/{purchase_request_no}` | B | Filter `status` |
| `POST /purchase-requests/{purchase_request_no}/create-po` | B | Body `{vendor_code, unit_prices: [{item_sku, unit_price}]}` |
| `GET /purchase-orders`, `GET /purchase-orders/{po_no}` | B | Detail memuat baris, `approvals`, `required_roles`, `receipts` |
| `POST /purchase-orders/{po_no}/approve`, `POST /purchase-orders/{po_no}/reject` | B | Body `{comment}`; penyetuju dari JWT |
| `POST /purchase-orders/{po_no}/receipts` | B | Body `{warehouse_code, lines: [{item_sku, qty}]}`; respons `{gr_no, po_status, serial_numbers}` |

Tier 2 (kontrak boleh menyusul): `POST /purchase-orders/{po_no}/quotes`, `…/submit`, `POST /assets/units/{serial_number}/mark-lost`, `…/write-off`, `GET /assets/technicians/{employee_id}`, `POST /transfers`, `POST /transfers/{transfer_no}/dispatch`, `POST /transfers/{transfer_no}/receive`, `GET /audit-logs`.

## 2. Event baru (`contracts/events/`)

Envelope baku (`event_id`, `event_type`, `version: 1`, `occurred_at`, `source: scm`, `correlation_id`, `data`).

| Event | Penerima | `data` | Dipakai untuk |
| :--- | :--- | :--- | :--- |
| `stockrequest.cancelled` | CRM | `stock_request_no`, `ticket_code`, `status: CANCELLED`, `reason` (`RESERVATION_EXPIRED` \| `MANUAL`), `cancelled_at` | CRM memperbarui `materials_status`. Perlu nilai baru `CANCELLED` di enum `materials_status` (`variable_standards.md` bagian 4) |
| `po.approved` | Finance | `po_no`, `purchase_request_no`, `vendor_code`, `total_amount`, `cost_center_code`, `approvals` (array `role`, `employee_id`), `approved_at` | Finance menahan anggaran (`tracks/scm.md` backlog: saat ini tidak ada handler) |
| `goods.received` | Finance | `gr_no`, `po_no`, `vendor_code`, `warehouse_code`, `lines` (`item_sku`, `qty`, `unit_cost`), `total_value`, `received_at` | Finance mengakui persediaan |
| `stock.low` (Tier 2) | CRM, Finance (opsional) | `item_sku`, `warehouse_code`, `qty_available`, `reorder_point`, `purchase_request_no` | Peringatan stok di bawah ROP |
| `shipment.delivered` (Tier 2) | CRM, Finance (opsional) | `transfer_no`, `from_warehouse_code`, `to_warehouse_code`, `lines` (`item_sku`, `qty`), `delivered_at` | Transfer antar-gudang selesai |

Tiap event butuh `events/<nama>.schema.json` (`x-publisher: scm`, `x-consumers`), `examples/events/<nama>.json`, entri `provides.events` di `tracks/scm.md`, `consumes.events` di track penerima, dan baris `EVENT_SUBSCRIBERS` di `services/shared/events.py`. `po.approved`, `goods.received`, `shipment.delivered` sudah ada di `EVENT_SUBSCRIBERS` (tanpa skema); `stockrequest.cancelled` dan `stock.low` belum.

## 3. Koreksi contoh di kontrak

| Lokasi | Sekarang | Seharusnya |
| :--- | :--- | :--- |
| `scm.yaml` `POST /purchase-orders` contoh `201` | `status: APPROVED` | `status: PENDING_APPROVAL`; PO tidak pernah lahir `APPROVED` |
| `scm.yaml` `POST /purchase-orders` respons | Tanpa kode `503` dan `409` | Tambah `503 BUDGET_CHECK_UNAVAILABLE` dan `409 BUDGET_INSUFFICIENT` |
| `scm.yaml` `…/flag-damaged` contoh | `item_sku: RTR-AX`, `serial_number: SN-RTR-2026-000003` | Contoh non-serial (`CBL-FO`) atau ONT dengan `SN-ONT-…`; hanya ONT yang bernomor seri |
| `scm.yaml` `…/issue` | Respons galat hanya `401/403/409` tanpa kode spesifik | Dokumentasikan kode di `409`: `TECHNICIAN_NOT_ASSIGNED`, `SERIAL_NOT_RESERVED`, `INVALID_TRANSITION`, `INSUFFICIENT_STOCK` |

## 4. Permintaan ke track lain (lewat PR ke file track mereka)

- **CRM:** terbitkan `ticket.cancelled` (kontrak baru) agar SCM bisa melepas Reservasi saat tiket dibatalkan; terima `stockrequest.cancelled`; tambah nilai `CANCELLED` pada `materials_status`.
- **Finance:** terima `po.approved` (menahan anggaran) dan `goods.received`; pastikan `POST /budgets/check` menjawab idempoten dan membawa `X-Correlation-Id`.
- **HRM:** konfirmasi nama role `FINANCE_MANAGER` dan `DIRECTOR` di JWT agar bisa menyetujui PO di `scm-web`.
