---
track: crm
owner_team: Kelompok CRM
updated: '2026-11-25'
folders: [apps/web, apps/crm-web, services/crm-api]
owns:
- {entity: Customer, id_format: CUS-000001}
- {entity: InstallAddress, id_format: ADR-000001}
- {entity: Order, id_format: ORD-2026-000001}
- {entity: Subscription, id_format: SUB-000001}
- {entity: Ticket, id_format: TKT-000001}
- {entity: SiteProfile, id_format: melekat pada ADR dan SUB}
- {entity: Catalog, id_format: SKU}
- {entity: TechnicianRating, id_format: per TKT}
provides:
  api:
  - {id: POST /api/v1/auth/register, status: MOCKED, since: '2026-11-25'}
  - {id: POST /api/v1/auth/login, status: MOCKED, since: '2026-11-25'}
  - {id: GET /api/v1/catalog, status: MOCKED, since: '2026-11-25'}
  - {id: GET /api/v1/coverage, status: MOCKED, since: '2026-11-25'}
  - {id: POST /api/v1/orders, status: MOCKED, since: '2026-11-25'}
  - {id: 'GET /api/v1/orders/{order_no}', status: MOCKED, since: '2026-11-25'}
  - {id: GET /api/v1/portal/me, status: MOCKED, since: '2026-11-25'}
  - {id: POST /api/v1/tickets, status: MOCKED, since: '2026-11-25'}
  - {id: GET /api/v1/tickets, status: MOCKED, since: '2026-11-25'}
  - {id: 'GET /api/v1/tickets/{ticket_code}', status: MOCKED, since: '2026-11-25'}
  - {id: GET /api/v1/technicians/available, status: MOCKED, since: '2026-11-25'}
  - {id: 'POST /api/v1/tickets/{ticket_code}/assign', status: MOCKED, since: '2026-11-25'}
  - {id: GET /api/v1/technician/tickets, status: MOCKED, since: '2026-11-25'}
  - {id: 'POST /api/v1/tickets/{ticket_code}/start', status: MOCKED, since: '2026-11-25'}
  - {id: 'POST /api/v1/tickets/{ticket_code}/photos', status: MOCKED, since: '2026-11-25'}
  - {id: 'POST /api/v1/tickets/{ticket_code}/items-report', status: MOCKED, since: '2026-11-25'}
  - {id: 'POST /api/v1/tickets/{ticket_code}/resolve', status: MOCKED, since: '2026-11-25'}
  - {id: 'POST /api/v1/tickets/{ticket_code}/rating', status: MOCKED, since: '2026-11-25'}
  - {id: 'GET /api/v1/subscriptions/{subscription_code}/site-profile', status: MOCKED, since: '2026-11-25'}
  - {id: GET /api/v1/dashboard/summary, status: MOCKED, since: '2026-11-25'}
  events:
  - {id: invoice.requested, status: MOCKED, since: '2026-11-25'}
  - {id: referral.used, status: MOCKED, since: '2026-11-25'}
  - {id: ticket.created, status: MOCKED, since: '2026-11-25'}
  - {id: ticket.assigned, status: MOCKED, since: '2026-11-25'}
  - {id: ticket.items_reported, status: MOCKED, since: '2026-11-25'}
  - {id: ticket.resolved, status: MOCKED, since: '2026-11-25'}
  - {id: subscription.activated, status: MOCKED, since: '2026-11-25'}
  - {id: technician.rated, status: MOCKED, since: '2026-11-25'}
consumes:
  api:
  - {id: 'GET /api/v1/customers/{customer_code}/invoices', from: finance, status: PLANNED}
  - {id: GET /api/v1/employees/available, from: hrm, status: PLANNED}
  - {id: 'GET /api/v1/employees/{employee_code}', from: hrm, status: PLANNED}
  - {id: 'GET /api/v1/package-kits/{sku}', from: scm, status: PLANNED}
  - {id: 'GET /api/v1/referrals/{code}', from: hrm, status: PLANNED}
  - {id: 'GET /api/v1/stock/{sku}', from: scm, status: PLANNED}
  events:
  - {id: invoice.issued, from: finance, status: PLANNED}
  - {id: invoice.paid, from: finance, status: PLANNED}
  - {id: shipment.delivered, from: scm, status: PLANNED}
  - {id: stock.issued, from: scm, status: PLANNED}
  - {id: stock.low, from: scm, status: PLANNED}
  - {id: stock.returned, from: scm, status: PLANNED}
  - {id: stockrequest.cancelled, from: scm, status: PLANNED}
  - {id: stockrequest.pending, from: scm, status: PLANNED}
  - {id: stockrequest.ready, from: scm, status: PLANNED}
---

# Track CRM

**Pemilik:** Kelompok CRM. **Folder:** `apps/web` (website dan portal pelanggan), `apps/crm-web` (portal CRM dan teknisi), `services/crm-api`.

## Lingkup

CRM memiliki tiga portal: pelanggan, teknisi, dan manajer CRM. CRM memiliki pelanggan, alamat pemasangan, order, langganan, tiket, profil lokasi, katalog, dan rating. CRM memulai hampir semua alur lintas modul. Data disimpan per langganan (satu paket di satu alamat), bukan per pelanggan.

## Slice requirements (acceptance untuk demo)

Kriteria ini turunan alur demo di `CONTEXT.md` bagian 5. Setiap butir harus bisa didemokan dan dites.

1. **Form pesan paket** (langkah 1): menerima nama penerima, alamat dan kota, nomor WhatsApp, email, pilihan paket, kode referral (boleh lewat tautan `?ref=<kode>` yang hanya mengisi kolom), dan boleh dipesan untuk orang lain. Alamat pemasangan wajib. Kode referral divalidasi lewat HRM (`GET /api/v1/referrals/{code}`) dan menghasilkan `referral.used`. Hasilnya order `SUBMITTED` dan langganan `PENDING`.
2. **Permintaan invoice** (langkah 1): order menerbitkan `invoice.requested` dengan payer, recipient, alamat, item, subtotal, dan kode referral. Tidak ada pengecekan stok di checkout yang menahan order.
3. **Status order dari Finance** (langkah 2 dan 3): `invoice.issued` menjadikan order `AWAITING_PAYMENT`; `invoice.paid` menjadikannya `PAID`. Semua perubahan status lewat `shared.transitions` dan event yang datang tidak berurutan tidak merusak status.
4. **Tiket pemasangan otomatis** (langkah 4): setelah `invoice.paid`, CRM membuat tiket `INSTALLATION` berstatus `OPEN` dengan salinan `required_items` dari `GET /api/v1/package-kits/{sku}` (SCM), lalu menerbitkan `ticket.created`.
5. **Penugasan oleh manajer CRM** (langkah 6): daftar teknisi dari `GET /api/v1/technicians/available` (diambil dari HRM; kota, aktif, tidak cuti, beban kerja ditampilkan). Hanya `CRM_MANAGER` dan `DIRECTOR` yang menugaskan. Hasilnya tiket `ASSIGNED`, event `ticket.assigned`, dan notifikasi di dashboard teknisi.
6. **Dashboard teknisi**: hanya tiket yang ditugaskan kepadanya, dengan barang yang dibutuhkan dan yang sudah dikeluarkan, lokasi penerima, `materials_status`, dan status pekerjaan.
7. **Pengerjaan** (langkah 8): teknisi memulai tiket (`IN_PROGRESS`), mengunggah foto, melaporkan barang terpakai dan dikembalikan (`ticket.items_reported`), mengisi profil lokasi, lalu `resolve`. Resolve ditolak tanpa foto atau bila bukan teknisi yang ditugaskan.
8. **Aktivasi**: tiket pemasangan `RESOLVED` mengaktifkan langganan dan menyelesaikan order, lalu menerbitkan `ticket.resolved` dan `subscription.activated`.
9. **Rating** (langkah 10): hanya pemilik akun, satu kali per tiket, setelah `RESOLVED` atau `CLOSED`; menerbitkan `technician.rated`.
10. **Portal pelanggan**: menampilkan langganan, pesanan, tiket, `installation_label`, `materials_status`, dan invoice dari Finance.
11. **Profil lokasi**: data lokasi dan kondisi dari teknisi melekat pada alamat dan langganan dan tampil di tiket maintenance berikutnya.

## Integrasi

- Memanggil HRM (`employees:read`), SCM (`packagekits:read`, `stock:read`), dan Finance (`invoices:read`) dengan token layanan dari `shared.service_auth.service_headers`.
- Menerbitkan event lewat outbox (`shared.outbox`), menerima event lewat `shared.event_receiver.create_events_router`.
- Daftar lengkap ada di front matter di atas dan di `tracks/STATUS.md`.

## Backlog

Temuan review kode `services/crm-api` per 2026-11-25. Baseline sengaja tidak mengubah kode modul, jadi semuanya milik tim CRM. **P0** dikerjakan lebih dulu.

| Prioritas | Temuan | Lokasi |
| :--- | :--- | :--- |
| P0 | `receive_event` menerima event tanpa tanda tangan (pemeriksaan dilewati bila header kosong). Pakai `create_events_router`. | `app/main.py` `receive_event` |
| P0 | Pelanggan atau staf lain bisa memberi rating ke tiket mana pun; teknisi default `EMP-0042`. Wajib pemilik akun dan tiket selesai. | `submit_technician_rating` |
| P0 | `invoice.paid` menimpa status order tanpa pemeriksaan (bisa menimpa `COMPLETED`). Pakai `shared.transitions`. | `receive_event` |
| P0 | `/complete` bisa dipanggil teknisi yang tidak ditugaskan dan tanpa syarat order sudah dibayar. | `update_work_order` |
| P1 | Cek stok dan referral gagal-buka (`except Exception: pass`); ganti dengan alur baru (tanpa hold stok di checkout, referral divalidasi dan event `referral.used`). | `_create_order_workflow` |
| P1 | Event masih `order.confirmed`; ganti ke `invoice.requested`. Event lama `workorder.assigned` dan `kit.reconciled` diganti `ticket.assigned` dan `ticket.items_reported`. | `_create_order_workflow`, `assign_work_order`, `update_work_order` |
| P1 | `WorkOrder` digabung ke `Ticket` (tipe, penugasan, foto, `required_items`, profil lokasi). Endpoint `/work-orders/*` diganti `/tickets/{ticket_code}/*`. | `models.py`, `main.py` |
| P1 | Tidak ada kode yang membuat `Subscription` (hanya seed); buat `PENDING` saat order, `ACTIVE` saat tiket pemasangan selesai. Simpan data penerima di langganan. | `models.py`, `main.py` |
| P1 | Fallback ke `db.query(Customer).first()` atau `CUS-000456` saat staf membuat order, tiket, atau melihat portal; kembalikan 404. | `create_authenticated_order`, `create_public_order`, `get_customer_portal`, `create_ticket` |
| P1 | Kode dibuat dengan `count()+1`; pakai `shared.ids.next_code`. | `_next_*_code` |
| P1 | Tabel `outbox_events` berstatus `SENT` sejak dibuat dan tidak ada relay; pakai `shared.outbox` (perlu migration). | `models.py`, semua `publish_event` |
| P2 | Pesanan prabayar ikut membuat work order; tiket hanya untuk pemasangan dan maintenance. | `_create_order_workflow` |
| P2 | Cakupan layanan (`coverage_areas`) tidak dipakai saat order; `/public/orders` memakai nama "public" padahal wajib login. | `create_public_order` |
| P2 | Panggilan ke HRM, SCM, dan Finance tanpa token layanan; halaman manajer memanggil HRM langsung dari browser. Pakai `GET /technicians/available`. | `_create_order_workflow`, `get_customer_portal`, `apps/crm-web/src/app/manager/page.tsx` |
| P2 | Form selesai teknisi terisi data palsu (`SN-ONT-2026-000002`, 30 m); wajib diisi teknisi. | `apps/crm-web/src/app/teknisi/page.tsx` |
| P2 | Pembuatan pelanggan otomatis dari `/public/support` tanpa pembatasan laju. | `create_public_support_ticket` |

## Open items

- Hak akses `CS_AGENT` dan `MARKETING` di CRM masih dibahas (catatan notulen). Sementara: `CS_AGENT` menerima keluhan dan membuat tiket; `MARKETING` tidak punya hak CRM.
- Fitur campaign dan tim marketing di CRM: `PLANNED`, di luar baseline dan demo.
- Notifikasi penugasan hanya di dashboard teknisi, belum WhatsApp atau email.
- Penyimpanan foto: volume Docker bersama yang dilayani CRM; jalur disimpan di tiket.

## Requests

- dari scm, 2026-11-27: terbitkan event `ticket.cancelled` (kontrak baru) agar SCM bisa melepas Reservasi saat tiket dibatalkan.
- dari scm, 2026-11-27: terima `stockrequest.cancelled` dan tambah nilai `CANCELLED` pada enum `materials_status` (`contracts/variable_standards.md` bagian 4).
- dari scm, 2026-11-27: `stock.low` dan `shipment.delivered` (Tier 2) tersedia bila CRM ingin menampilkan peringatan stok atau status transfer.

## Decisions

- 2026-11-25: tiket menggantikan work order; langganan menjadi satuan data; invoice diminta CRM lewat `invoice.requested`; penugasan oleh manajer CRM.

## Cara membaca status

| Status | Arti untuk yang disediakan | Arti untuk yang dikonsumsi |
| :--- | :--- | :--- |
| `PLANNED` | Ada di kontrak, belum ada contoh atau implementasi | Belum diintegrasikan |
| `MOCKED` | Contoh respons atau event ada di `contracts/` dan bisa dipakai lewat mock | Sudah diintegrasikan terhadap mock |
| `LIVE` | Sudah diimplementasikan dan lolos tes (`test:` wajib diisi) | Sudah diintegrasikan terhadap layanan asli |
| `CHANGING` | Kontrak sedang diubah; baca bagian Decisions | Sedang menyesuaikan |
| `DEPRECATED` | Akan dihapus; pakai penggantinya | Harus pindah |

Hanya tim pemilik yang mengubah file ini. Tim lain menulis permintaan di bagian **Requests** lewat PR. Setelah mengubah front matter, jalankan `python tools/check_contracts.py` agar `tracks/STATUS.md` ikut diperbarui.
