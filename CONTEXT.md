# CONTEXT — TelcoNusa ERP

Sumber kebenaran bersama untuk empat track: CRM, HRM, SCM, Finance. Bacalah ini lebih dulu, lalu file track milik Anda di `tracks/`. Perubahan di file ini lewat PR terpisah yang disetujui perwakilan keempat track (aturan area bersama di README).

## 1. Peta dokumen

| File | Fungsi |
| :--- | :--- |
| `CONTEXT.md` | Gambaran bersama: lingkup, aturan, alur demo, keputusan |
| `AGENTS.md`, `CLAUDE.md` | Aturan kerja untuk agen pemrograman. `CLAUDE.md` hanya mengimpor `AGENTS.md` |
| `tracks/<crm\|hrm\|scm\|finance>.md` | Lingkup, status integrasi, kriteria penerimaan, dan backlog satu track. Dimiliki satu tim |
| `tracks/STATUS.md` | Tabel status semua track. Dibuat otomatis, jangan diedit |
| `contracts/` | Kontrak yang bisa dibaca mesin: `openapi/`, `events/`, `examples/events/`, dan [`variable_standards.md`](contracts/variable_standards.md) |
| `services/shared/` | Pustaka bersama (auth, event, outbox, ID, status). Area bersama |
| `services/_template/` | Titik awal modul baru |
| `mock/README.md` | Cara memakai mock untuk modul yang belum jadi |

Dokumen sumber: *Blueprint Integrasi TelkoNusa* dan *Notulen Diskusi Integrasi* (final). Bila keduanya berbeda dengan keputusan di bagian 8, keputusan di sini yang berlaku.

## 2. Apa itu baseline

Baseline adalah fondasi agar empat tim bisa langsung membangun fitur sendiri dengan aturan yang sama dan melihat apa yang dikerjakan tim lain, sehingga integrasi lancar. Isinya: dokumen ini, kontrak, file track, CI, pustaka bersama tambahan, mock, dan template modul.

**Baseline tidak berisi** logika bisnis modul dan tidak mengubah kode di `services/*-api/app/` maupun `apps/`. Alur demo belum berjalan penuh saat baseline di-merge; ia berjalan setelah keempat track selesai mengerjakan bagiannya.

Pustaka bersama bersifat tambahan: fungsi lama tetap ada, fungsi baru dipakai bila tim memilih. Yang langsung berlaku untuk semua adalah file area bersama: `docker-compose.yml`, `.env.example`, `services/shared/config.py` (secret wajib diisi, tanpa nilai bawaan; RabbitMQ dihapus dari tumpukan bawaan).

## 3. Aturan

1. **Satu data, satu pemilik.** Modul lain membaca lewat API atau event dan hanya menyimpan salinan ringkas.
2. **Perintah lewat API, kabar lewat event.** API untuk pemanggil yang butuh jawaban langsung; event untuk memberi tahu bahwa sesuatu sudah terjadi.
3. **Hanya Finance menulis buku besar.**
4. **Status hanya diubah pemiliknya.** Transisi sah ada di `services/shared/transitions.py`; lainnya ditolak `409 INVALID_TRANSITION`.
5. **Kontrak dulu.** Ubah `contracts/` lewat PR yang direview track terdampak sebelum mengubah kode yang bergantung padanya.
6. **Status jujur.** Perbarui `tracks/<track>.md` saat status berubah. `LIVE` butuh tes yang lulus.
7. **Batas folder.** Edit hanya folder track Anda (`folders` di file track). Area bersama lewat PR terpisah dengan persetujuan empat track.
8. **Secret tidak ada di repo.** `.env` tidak di-commit; jalankan `tools/setup-env.sh`.
9. **Tidak ada atribusi agen pemrograman.** Agen pemrograman apa pun (Claude, Codex, Copilot, Cursor, Gemini, dan sejenisnya) tidak boleh menjadi author, co-author, atau kontributor commit, PR, atau catatan git lain. Tidak ada trailer `Co-Authored-By`, `Generated-by`, atau sejenisnya dan tidak ada kalimat "dibuat dengan <agen>" di pesan commit atau isi PR. Dicek otomatis oleh CI (`tools/check_agent_attribution.py`) dan oleh hook `commit-msg` (`tools/install-hooks.sh`).

## 4. Glosarium

| Istilah | Arti |
| :--- | :--- |
| Track | Satu modul ERP beserta timnya: CRM, HRM, SCM, Finance |
| Pelanggan (akun) | Pemilik akun dan pembayar. Login di CRM |
| Penerima (recipient) | Orang yang menerima layanan; boleh bukan pemilik akun; tanpa login; disimpan di langganan |
| Langganan (`SUB-`) | Satu paket di satu alamat. Satuan data utama: tiket, invoice, daftar barang, referral, dan profil lokasi merujuk ke sini |
| Tiket (`TKT-`) | Semua pekerjaan lapangan dan keluhan: pemasangan, maintenance, keluhan. Menggantikan work order |
| Paket barang (`PackageKit`) | Daftar barang yang dibutuhkan satu paket, dimiliki SCM |
| Permintaan barang (`SR-`) | Permintaan SCM yang dibuat otomatis dari tiket |
| Profil lokasi | Data lokasi, spesifikasi, dan kondisi pemasangan yang dicatat teknisi, dipakai ulang saat maintenance |
| Kode referral | Kode manual milik satu staf marketing yang dibuat HR; pelanggan memasukkannya saat berlangganan |
| `materials_status` | Bidang baca-saja di CRM yang menampilkan status barang tiket dari SCM |
| `installation_label` | Label baca-saja untuk pelanggan: Menunggu penugasan, Sedang diproses, Selesai |

## 5. Alur demo kanonik

Satu alur presentasi: pembuatan jaringan baru dari portal pelanggan sampai SCM, invoice, dan HR. Ini juga uji penerimaan integrasi. Setiap langkah punya satu pemilik.

| # | Langkah | Pemilik | API atau event | Perubahan status |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Pelanggan mengisi form pesan paket (penerima, alamat, kota, WhatsApp, email, paket, kode referral) | CRM | Validasi `GET /referrals/{code}` (HRM); terbit `invoice.requested` dan `referral.used` | Order `SUBMITTED`, langganan `PENDING` |
| 2 | Finance membuat invoice, staf AR mengirimnya | Finance | Konsumsi `invoice.requested`; terbit `invoice.issued` | Invoice `DRAFT → ISSUED`, order `AWAITING_PAYMENT` |
| 3 | Staf AR mengecek ulang dan mengonfirmasi pembayaran | Finance | Terbit `invoice.paid` | Invoice `PAID`, order `PAID` |
| 4 | CRM membuat tiket pemasangan dengan salinan `required_items` | CRM | `GET /package-kits/{sku}` (SCM); terbit `ticket.created` | Tiket `OPEN` |
| 5 | SCM membuat permintaan barang dan mengecek stok | SCM | Konsumsi `ticket.created`; terbit `stockrequest.ready` atau `stockrequest.pending` (plus permintaan pembelian dan cek anggaran Finance) | `READY_TO_ISSUE` atau `PENDING_STOCK` |
| 6 | Manajer CRM memilih teknisi dari daftar HRM | CRM | `GET /employees/available` (HRM); terbit `ticket.assigned` | Tiket `ASSIGNED`; HRM menandai teknisi sibuk |
| 7 | Staf SCM mengeluarkan paket barang ke teknisi | SCM | Terbit `stock.issued` | Permintaan `ISSUED`, unit `WITH_TECHNICIAN` |
| 8 | Teknisi mengerjakan, mengunggah foto, melaporkan barang terpakai dan kembali, mengisi profil lokasi, menyelesaikan tiket | CRM | Terbit `ticket.items_reported`, `ticket.resolved`, `subscription.activated` | Tiket `IN_PROGRESS → RESOLVED`, langganan `ACTIVE`, order `COMPLETED`, HRM membebaskan teknisi |
| 9 | SCM memperbarui persediaan dari laporan dan menandai selisih | SCM | Konsumsi `ticket.items_reported`; terbit `stock.returned` | Permintaan `RETURNED` |
| 10 | Pelanggan memberi rating teknisi | CRM | Terbit `technician.rated` (HRM menyimpan) | – |

Tiket maintenance dan keluhan memakai bagian tengah alur yang sama (langkah 4 sampai 10) tanpa invoice awal.

### Skenario gagal yang harus tetap benar

1. Stok ONT habis setelah pembayaran: permintaan barang `PENDING_STOCK`, permintaan pembelian dibuat, pelanggan melihat "menunggu barang", tiket tetap ada.
2. Event `invoice.requested` terkirim dua kali: tetap satu invoice.
3. Finance mati sementara: event menunggu di outbox CRM dan diproses setelah Finance hidup.
4. `invoice.paid` datang dengan data yang tidak sesuai status order: status tidak rusak.
5. Event tanpa tanda tangan ditolak (401).
6. Teknisi yang tidak ditugaskan tidak bisa menyelesaikan tiket; resolve tanpa foto ditolak.

## 6. Kepemilikan dan status

Tabel pemilik entitas, format ID, dan status ada di [`contracts/variable_standards.md`](contracts/variable_standards.md) bagian 2 dan 4. Pemilik tiap track ada di front matter `owns` pada file track masing-masing.

## 7. Teknis integrasi

| Aspek | Kesepakatan |
| :--- | :--- |
| Protokol | REST JSON; prefix `/api/v1` |
| Kontrak | OpenAPI 3 per track di `contracts/openapi/`; skema event JSON Schema di `contracts/events/`; contoh event di `contracts/examples/events/` |
| Event | Satu transportasi: outbox per layanan dan relay webhook bertanda tangan HMAC. Ulang pada menit 1, 5, 15, lalu dead letter. Tanpa RabbitMQ di tumpukan bawaan |
| Idempotensi | Penerima menyimpan `event_id`; `POST` transaksi memakai `Idempotency-Key` |
| Autentikasi pengguna | JWT dari HRM (karyawan) atau CRM (pelanggan) dengan `role` |
| Autentikasi antar-layanan | JWT layanan berumur pendek dengan `scopes` (`shared/service_auth.py`); setiap endpoint lintas modul menyatakan `x-scope` |
| ID | Dibuat dari sequence di database (`shared/ids.py`) |
| Uang dan waktu | Rupiah bulat; ISO 8601 `+07:00` |
| Mock | `docker compose --profile mock up` menyalakan mock dari contoh di `contracts/openapi`; `python tools/send_fixture.py <event> --to <url>` mengirim event contoh |

Cek konsistensi (`python tools/check_contracts.py`) berjalan di CI dan memeriksa bahwa file track, OpenAPI, dan skema event saling cocok dan bahwa `tracks/STATUS.md` mutakhir.

## 8. Keputusan

Semua keputusan di bawah dibuat pada 2026-11-25 dari rapat dan sesi baseline, kecuali disebut lain. Bila ada pertentangan, notulen final lebih tinggi dari ringkasan rapat, dan keduanya lebih tinggi dari blueprint.

**Produk dan peran**
- Tiga portal CRM: pelanggan, teknisi, manajer CRM. HRM, SCM, dan Finance masing-masing punya satu aplikasi internal.
- Semua pekerjaan (pemasangan baru, maintenance, keluhan) adalah tiket. `WorkOrder` dihapus.
- Data disimpan per langganan (satu paket di satu alamat) karena satu pelanggan bisa punya beberapa paket di beberapa alamat. Pemesanan boleh untuk orang lain: pemilik akun membayar, penerima tercatat di langganan.
- Akun staf dibuat HR. HR mengurus kepegawaian; pelanggan dan tiket ada di CRM.
- Manajer CRM menentukan penugasan teknisi dari daftar HRM. Customer service menerima keluhan dan membuat tiket. Hak `MARKETING` dan hak lanjutan customer service di CRM masih dibahas (catatan notulen).
- Dashboard teknisi hanya menampilkan tiket yang ditugaskan kepadanya: barang, lokasi, status. Notifikasi penugasan di dashboard.
- Dashboard KPI lintas divisi ditunda; selesaikan fitur dasar dulu.

**Pesanan, invoice, pembayaran**
- Order menunggu sampai pembayaran. Finance membuat invoice atas permintaan CRM (`invoice.requested`), staf AR mengirimnya, lalu pembayaran dicek ulang dan dikonfirmasi staf AR sebelum dianggap berhasil.
- Setelah lunas: tiket dibuat, teknisi yang tersedia ditugaskan, HRM diberi tahu teknisi sedang bekerja.

**Barang**
- Setiap paket punya daftar barang (dimiliki SCM). Tiket otomatis memicu permintaan barang ke SCM. Stok yang habis setelah pembayaran menjadi `PENDING_STOCK` dan SCM memesan ke vendor; CRM menampilkan status pending.
- Teknisi membawa semua barang sesuai paket dan mengembalikan yang tidak terpakai. Teknisi melaporkan jumlah terpakai dan dikembalikan di tiket; CRM mengirimkannya ke SCM (`ticket.items_reported`).
- Status barang `WITH_TECHNICIAN` diubah staf SCM, bukan teknisi. Barang rusak diurus SCM. Barang tambahan di lapangan: teknisi kembali ke SCM dan staf SCM menambah baris pengeluaran pada tiket yang sama. Kekurangan kecil cukup lewat telepon dan tidak masuk sistem.
- Penanda "return pending" tampil bila barang sudah keluar tetapi laporan teknisi belum masuk.

**Penyelesaian**
- Tiket selesai dengan bukti foto (minimal satu, oleh teknisi yang ditugaskan). Pelanggan memberi rating 1–5 sekali per tiket; dipakai HRM untuk penilaian kinerja.
- Data rumah pelanggan yang dicatat teknisi disimpan pada alamat dan langganan, dan dipakai ulang saat maintenance.
- Label status untuk pelanggan: Menunggu penugasan, Sedang diproses, Selesai (turunan dari status tiket).

**Marketing dan referral**
- HR membuat kode referral untuk setiap staf marketing. Pelanggan memasukkan kode (atau membuka tautan yang mengisi kode yang sama) saat berlangganan; bila cocok, pelanggan tercatat di bawah staf tersebut di HRM. Baseline berhenti di event `referral.used`; aturan angka dan waktunya ditentukan tim HRM dan Finance.
- Campaign dan tim marketing di CRM belum dikerjakan.

**Penggajian**
- Komponen gaji, tunjangan operasional (termasuk ongkos bensin dan makan teknisi, tanpa nota), dan insentif adalah tanggung jawab tim HRM. Finance mencatat biaya penggajian sebagai pengeluaran. Baseline tidak mengatur angka maupun alur payroll.

**Platform**
- Satu transportasi event (outbox dan relay webhook bertanda tangan). RabbitMQ dihapus dari tumpukan bawaan.
- JWT layanan dengan scope untuk panggilan antar-layanan; secret tanpa nilai bawaan.
- Penerima event wajib menolak event tanpa tanda tangan.
- Kontrak ditulis lebih dulu oleh tim baseline, terbatas pada alur demo; tiap track meninjau bagiannya.
- Tidak ada PRD terpisah; kriteria penerimaan ada di file track.
- Tidak ada agen pemrograman yang tercatat sebagai kontributor git (aturan 9).

## 9. Event dan API lama

Kode modul saat ini masih memakai nama lama. `shared/events.py` tetap mengirim event lama sampai track pemiliknya bermigrasi.

| Lama | Baru | Catatan |
| :--- | :--- | :--- |
| `order.confirmed` | `invoice.requested` | CRM meminta, Finance membuat `DRAFT` |
| `workorder.assigned` | `ticket.assigned` | |
| `workorder.completed`, `kit.reconciled` | `ticket.items_reported`, `ticket.resolved` | |
| `commission.finalized` | – | Aturan insentif di tangan HRM dan Finance |
| `POST /invoices/{no}/pay` | `POST /invoices/{no}/confirm-payment` | |
| `/internal/invoices-by-customer/{code}` | `GET /customers/{code}/invoices` | Token layanan |
| `GET /stock/{sku}`, `GET /employees/available` tanpa auth | Token layanan dengan scope | |
| `/work-orders/*` | `/tickets/{ticket_code}/*` | |

Event lain yang masih dikirim dan belum dikontrakkan (`payroll.approved`, `payroll.paid`, `po.approved`, `vendor.paid`, `goods.received`, `stock.adjusted`, `employee.*`, `subscription.terminated`, dan sejenisnya) adalah milik track terkait. Definisikan di `contracts/` bila Anda mulai memakainya.

## 10. Di luar baseline

Campaign dan halaman promo, perhitungan payroll dan slip gaji, dashboard KPI lintas divisi, pascabayar, B2B, penagihan bulanan dan tunggakan, siklus P2P penuh (goods receipt, tagihan vendor, three-way match), chat di tiket, notifikasi WhatsApp atau email, rekrutmen dan absensi detail.

## 11. Jadwal

| Tanggal | Tonggak |
| :--- | :--- |
| 25–28 Nov | Baseline: dokumen, kontrak, file track, CI, pustaka bersama, mock, template. Freeze area bersama 28 Nov |
| 29 Nov–5 Des | Tiap track membangun bagiannya di atas platform. Yang disediakan mencapai `MOCKED` paling lambat 30 Nov dan `LIVE` paling lambat 5 Des |
| 6–8 Des | Integrasi alur penuh dan skenario gagal; perbaikan di folder masing-masing |
| 9 Des | Demo |

Setelah freeze, perubahan area bersama butuh persetujuan keempat track.

## 12. Masalah terbuka

- Angka insentif marketing dan aturan penggajian: tim HRM dan Finance.
- Hak akses `CS_AGENT` dan `MARKETING` selain yang tercantum: dibahas lanjutan.
- Nama tim GitHub untuk `CODEOWNERS`: isi di `.github/CODEOWNERS`.
- Format penilaian demo (apa yang dinilai) belum diketahui.
