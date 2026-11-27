---
track: finance
owner_team: Kelompok Finance
updated: '2026-11-25'
folders: [apps/finance-web, services/finance-api]
owns:
- {entity: Invoice, id_format: INV-2026-000001}
- {entity: Payment, id_format: PMT-000001}
- {entity: Journal, id_format: JE-000001}
- {entity: VendorBill, id_format: BIL-000001}
- {entity: Budget, id_format: BGT-2026-...}
- {entity: Account, id_format: '1100'}
provides:
  api:
  - {id: GET /api/v1/invoices, status: MOCKED, since: '2026-11-25'}
  - {id: 'GET /api/v1/invoices/{invoice_no}', status: MOCKED, since: '2026-11-25'}
  - {id: 'POST /api/v1/invoices/{invoice_no}/send', status: MOCKED, since: '2026-11-25'}
  - {id: 'POST /api/v1/invoices/{invoice_no}/confirm-payment', status: MOCKED, since: '2026-11-25'}
  - {id: 'GET /api/v1/customers/{customer_code}/invoices', status: MOCKED, since: '2026-11-25'}
  - {id: POST /api/v1/budgets/check, status: MOCKED, since: '2026-11-25'}
  - {id: GET /api/v1/reports/trial-balance, status: MOCKED, since: '2026-11-25'}
  - {id: GET /api/v1/dashboard/summary, status: MOCKED, since: '2026-11-25'}
  events:
  - {id: invoice.issued, status: MOCKED, since: '2026-11-25'}
  - {id: invoice.paid, status: MOCKED, since: '2026-11-25'}
consumes:
  api:
  - {id: 'GET /api/v1/orders/{order_no}', from: crm, status: PLANNED}
  events:
  - {id: goods.received, from: scm, status: PLANNED}
  - {id: invoice.requested, from: crm, status: PLANNED}
  - {id: po.approved, from: scm, status: PLANNED}
  - {id: subscription.activated, from: crm, status: PLANNED}
---

# Track Finance

**Pemilik:** Kelompok Finance. **Folder:** `apps/finance-web` (Finance Suite), `services/finance-api`.

## Lingkup

Finance memiliki invoice, pembayaran, jurnal dan buku besar, tagihan vendor, anggaran, dan laporan. Hanya Finance yang menulis buku besar. Finance membuat invoice atas permintaan CRM dan mengonfirmasi pembayaran; CRM tidak membuat atau mengubah invoice.

## Slice requirements (acceptance untuk demo)

1. **Invoice dari permintaan CRM** (langkah 2): `invoice.requested` membuat invoice `DRAFT` dengan nomor virtual account, tepat satu invoice per order (idempotent walau event datang dobel), dengan PPN 11%. Jurnal piutang dibuat saat invoice terbit.
2. **Kirim invoice**: staf AR menekan kirim di Finance Suite (`POST /api/v1/invoices/{no}/send`); invoice menjadi `ISSUED` dan `invoice.issued` terbit. Pelanggan melihatnya di portal lewat `GET /api/v1/customers/{code}/invoices` (scope `invoices:read`).
3. **Konfirmasi pembayaran** (langkah 3): staf AR mengecek ulang lalu `POST /api/v1/invoices/{no}/confirm-payment` dengan jumlah dan referensi bank; hanya setelah itu `PAID`, jurnal kas dan piutang dibuat, dan `invoice.paid` terbit. Pembayaran kurang menjadi `PARTIALLY_PAID` dan tidak menerbitkan `invoice.paid`.
4. **Pemisahan tugas**: yang mengonfirmasi pembayaran adalah staf AR atau manajer keuangan; tidak ada tombol "simulasi bayar" untuk role lain.
5. **Cek anggaran** untuk SCM: `POST /api/v1/budgets/check` dengan token layanan (scope `budgets:check`).
6. **Laporan**: neraca saldo seimbang setelah seluruh demo.
7. **Pengakuan pendapatan**: `subscription.activated` memicu jurnal pengakuan pendapatan sesuai aturan Finance.

## Integrasi

- Menerima event: `invoice.requested`, `subscription.activated`.
- Menerbitkan: `invoice.issued`, `invoice.paid`.
- Pencatatan biaya penggajian dan insentif marketing dari HRM mengikuti kesepakatan notulen (HRM mengelola, Finance mencatat sebagai pengeluaran); definisinya dibuat tim HRM dan Finance dan belum ada di `contracts/`.

## Backlog

Temuan review `services/finance-api` per 2026-11-25. **P0** dikerjakan lebih dulu.

| Prioritas | Temuan | Lokasi |
| :--- | :--- | :--- |
| P0 | `receive_event` menerima event tanpa tanda tangan; event `payroll.approved` palsu menambah beban gaji Rp999 juta pada hasil uji. Pakai `create_events_router`. | `app/main.py` `receive_event` |
| P0 | `POST /invoices/{no}/pay` bisa dipanggil semua role Finance dan selalu melunasi penuh. Ganti `confirm-payment` dengan jumlah, referensi bank, dan pemisahan tugas. | `simulate_va_payment` |
| P0 | `POST /budgets/check` tanpa autentikasi; ganti token layanan `budgets:check`. | `check_budget` |
| P1 | Invoice dibuat otomatis dari `order.confirmed` sebagai `ISSUED`; ganti `invoice.requested` menjadi `DRAFT` dan tambah `send`. | `receive_event` |
| P1 | Nomor invoice, virtual account, dan jurnal dibuat dari `count()+1` (bentrok bila paralel); pakai `shared.ids.next_code`. | `receive_event`, `post_journal` |
| P1 | Pengakuan pendapatan (`REV-REC`) hanya ada di seed; tidak ada handler `subscription.activated`, sehingga akun 4100 dan 4200 tetap nol. | `receive_event` |
| P1 | Komisi dijurnal saat pembayaran (`COM-FIN`) dan event `commission.finalized`; aturan insentif milik HRM dan Finance, bukan baseline. | `simulate_va_payment` |
| P1 | `/internal/invoices-by-customer` memakai HMAC secret sebagai kunci layanan; ganti `GET /customers/{code}/invoices` dengan token layanan. | `get_customer_invoices_internal` |
| P1 | `outbox_events` berstatus `SENT` sejak dibuat dan tidak ada relay; pakai `shared.outbox`. | `models.py`, semua `publish_event` |
| P2 | Jurnal `payroll.approved` memakai angka sisa untuk Utang BPJS sehingga selalu seimbang walau data salah; validasi komponen. | `receive_event` |
| P2 | `toggle_period` membuka kembali periode yang terkunci dengan satu klik. | `toggle_period` |
| P2 | Dashboard menghitung piutang dan utang dari 25 dan 20 baris terakhir; umur piutang palsu. | `finance_dashboard_summary` |
| P2 | Tidak ada `POST /vendor-bills`, three-way match, atau pemisahan tugas pembayaran vendor; tagihan hanya dari seed. | `pay_vendor_bill`, `seed.py` |

## Open items

- Aturan insentif marketing dan pencatatan biaya penggajian bersama tim HRM.
- Penjurnalan aset ONT dan persediaan setelah `stock.issued` dan `stock.returned` (belum dikontrakkan ke Finance).

## Requests

- dari scm, 2026-11-27: terima `po.approved` untuk menahan anggaran dan `goods.received` untuk mengakui persediaan.
- dari scm, 2026-11-27: pastikan `POST /api/v1/budgets/check` idempoten dan meneruskan `X-Correlation-Id`.

## Decisions

- 2026-11-25: invoice dibuat di Finance atas `invoice.requested`; dikirim dan dikonfirmasi oleh staf AR; pembayaran dicek ulang sebelum `invoice.paid`.

## Cara membaca status

| Status | Arti untuk yang disediakan | Arti untuk yang dikonsumsi |
| :--- | :--- | :--- |
| `PLANNED` | Ada di kontrak, belum ada contoh atau implementasi | Belum diintegrasikan |
| `MOCKED` | Contoh respons atau event ada di `contracts/` dan bisa dipakai lewat mock | Sudah diintegrasikan terhadap mock |
| `LIVE` | Sudah diimplementasikan dan lolos tes (`test:` wajib diisi) | Sudah diintegrasikan terhadap layanan asli |
| `CHANGING` | Kontrak sedang diubah; baca bagian Decisions | Sedang menyesuaikan |
| `DEPRECATED` | Akan dihapus; pakai penggantinya | Harus pindah |

Hanya tim pemilik yang mengubah file ini. Tim lain menulis permintaan di bagian **Requests** lewat PR. Setelah mengubah front matter, jalankan `python tools/check_contracts.py` agar `tracks/STATUS.md` ikut diperbarui.
