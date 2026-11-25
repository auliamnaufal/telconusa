# Standar Variabel, Atribut, & Kontrak Data — PT TelkoNusa Digital

Dokumen ini menyeragamkan seluruh penamaan variabel, tipe data, enum status, rumus bisnis, dan format payload antar 4 divisi (**CRM, HRM, SCM, Finance**) sesuai kesepakatan Notulen PDF poin A.1.

---

## 1. Konvensi Global (Berlaku di Semua Divisi)

| Aturan | Standar Baku | Contoh |
| :--- | :--- | :--- |
| **Gaya penamaan** | `snake_case` (JSON API & kolom MySQL) | `customer_id`, `install_address_id`, `unit_price` |
| **Primary Key internal** | `CHAR(36)` UUIDv4 + kode bisnis unik (`VARCHAR`) | `id` (UUID), `order_no` (`ORD-2026-000001`) |
| **Nominal uang** | `BIGINT` (Rupiah bulat, tanpa desimal/float) | `400000` (Rp400.000) |
| **Tanggal & Waktu** | ISO 8601 zona WIB (`+07:00`) | `"2026-11-25T16:30:00+07:00"` |
| **Periode bulanan** | `CHAR(7)` format `YYYY-MM` | `"2026-11"` |
| **Header Pelacakan** | `X-Correlation-Id` (wajib diteruskan antar-API) | `"ORD-2026-000123"` |
| **Header Idempotensi** | `Idempotency-Key` (wajib di semua `POST` transaksi) | `"ORD-2026-000123-inv-1"` |
| **Optimistic Locking** | Kolom `version` (`INT DEFAULT 1`) di tabel transaksi | `version: 1` |

### Format ID Bisnis Baku
| Entitas | Prefix & Format | Pemilik |
| :--- | :--- | :--- |
| Pelanggan | `CUS-000001` | CRM |
| Alamat Pemasangan | `ADR-000001` | CRM |
| Order | `ORD-2026-000001` | CRM |
| Langganan | `SUB-000001` | CRM |
| Work Order | `WO-000001` | CRM |
| Tiket Keluhan | `TKT-000001` | CRM |
| Campaign Marketing | `CMP-2026-001` | CRM |
| Karyawan | `EMP-0001` | HRM |
| Kode Referral Marketing | `REF-EMP0017` (atau custom `NUSA-BUDI`) | HRM |
| Pengajuan Tenaga Kerja | `REQ-2026-001` | HRM |
| Periode Payroll | `PAY-2026-11` | HRM |
| Purchase Order / GR | `PO-2026-0001` / `GR-2026-0001` | SCM |
| Paket Material Teknisi | `KIT-2026-000001` | SCM |
| Serial Number ONT | `SN-ONT-2026-000001` | SCM |
| Invoice / Payment / Jurnal | `INV-2026-000001` / `PMT-000001` / `JE-000001` | Finance |

---

## 2. Rumus & Parameter Bisnis yang Dikunci

| Variabel / Kebijakan | Rumus / Nilai Baku | Keterangan |
| :--- | :--- | :--- |
| **Insentif Referral Marketing & Komisi Sales** | `incentive_amount = ROUND(subscription_monthly_price * 0.10)` | **10% dari harga paket bulan pertama** (sebelum PPN, tidak termasuk biaya instalasi). Cair setelah invoice `PAID` & layanan `ACTIVE`. Ditarik (*clawback*) jika pelanggan berhenti dalam `90` hari. |
| **Poin Kinerja Referral (HRM)** | `referral_points = +10` per pelanggan aktif | Tercatat otomatis di HRM setiap kode referral berhasil sampai status `ACTIVE`. |
| **Bobot Rating Teknisi (HRM)** | `rating_score` (skala `1–5` → konversi `rating * 20`) | Masuk sebagai **40% dari komponen KPI Teknisi** (bagian dari total `60% KPI` kuartalan HRM); sisanya `60%` ketepatan instalasi & bebas tiket ulang 7 hari. |
| **PPN Simulasi** | `tax_rate = 0.11` (`11%`) | `tax_amount = ROUND((subtotal - discount) * 0.11)`. |
| **PPh 23 Jasa Vendor** | `wht_rate = 0.02` (`2%`) | Memotong transfer pembayaran vendor jasa. |
| **Toleransi Three-Way Match** | `match_tolerance = 0.02` (`2%`) | Selisih harga tagihan > 2% dari PO → `ON_HOLD`. |
| **Masa Reservasi Stok** | `reservation_ttl_hours = 72` | Lewat 72 jam belum bayar → invoice `VOID`, stok dilepas. |
| **Standar 1 Paket Material Teknisi (`KIT`)** | `1× ONT-01`, `50m CBL-FO`, `1× RTR-AX` *(opsional jika dipesan)* | Sisa kabel & perangkat tak terpakai wajib dikembalikan ke SCM via rekonsiliasi kit. |

---

## 3. Kamus Variabel Lintas Modul (Sinkron Blueprint + Notulen PDF)

### A. Pemesanan Pelanggan, Alamat Pemasangan & Referral (`CRM ↔ HRM ↔ Finance`)
| Nama Variabel | Tipe | Wajib | Pemilik | Deskripsi |
| :--- | :--- | :---: | :--- | :--- |
| `customer_id` | `string` | Ya | CRM | ID pelanggan (`CUS-000001`) |
| `full_name` | `string(120)` | Ya | CRM | Nama lengkap pelanggan |
| `whatsapp_number` | `string(20)` | Ya | CRM | Format E.164 (`62812...`) |
| `email` | `string(120)` | Ya | CRM | Email aktif pelanggan |
| `nik_or_npwp` | `string(20)` | Opsional* | CRM | Wajib unik untuk pascabayar/B2B |
| `install_address_id` | `string` | Ya | CRM | ID alamat pemasangan (`ADR-000001`), 1 pelanggan boleh punya banyak alamat |
| `install_address` | `text` | Ya | CRM | Alamat lengkap lokasi pemasangan layanan |
| `city_code` | `enum` | Ya | CRM | `JKT`, `BDG`, `SBY` (untuk validasi `coverage_areas` & penugasan teknisi) |
| `postal_code` | `string(10)` | Ya | CRM | Kode pos cakupan area |
| `referral_code` | `string(32)` | Opsional | HRM | Kode referral staf marketing (`REF-EMP0017`) |
| `campaign_id` | `string(20)` | Opsional | CRM | ID campaign asal order (`CMP-2026-001`) |
| `sales_employee_id` | `string(20)` | Opsional | HRM | ID staf sales/marketing pemilik referral (`EMP-0017`) |
| `sku` | `string(20)` | Ya | CRM | Kode produk (`HOME-50`, `MOB-PRE-50`, dll.) |
| `business_line` | `enum` | Ya | CRM | `PREPAID`, `POSTPAID`, `HOME`, `B2B` |

### B. Data Rumah Pelanggan, Penugasan & Rating Teknisi (`CRM ↔ HRM`)
| Nama Variabel | Tipe | Wajib | Pemilik | Deskripsi |
| :--- | :--- | :---: | :--- | :--- |
| `work_order_id` | `string` | Ya | CRM | ID work order (`WO-000001`) |
| `technician_employee_id` | `string` | Ya | HRM | ID teknisi (`EMP-0042`) |
| `work_order_type` | `enum` | Ya | CRM | `SURVEY`, `INSTALLATION`, `MAINTENANCE`, `DISMANTLE` |
| `installation_status` | `enum` | Ya | CRM | `PENDING_ASSIGNMENT` (Menunggu Penugasan), `IN_PROGRESS` (Sedang Diproses), `COMPLETED` (Selesai), `RESCHEDULED`, `FAILED` |
| `latitude` / `longitude` | `decimal(10,7)` | Opsional | CRM | Koordinat GPS rumah pelanggan (dicatat teknisi) |
| `ont_serial_number` | `string(40)` | Ya* | SCM/CRM | Nomor seri ONT terpasang (`SN-ONT-2026-000001`) |
| `cable_used_meters` | `int` | Ya* | CRM | Panjang kabel fiber terpakai (meter) |
| `signal_dbm` | `decimal(5,2)` | Opsional | CRM | Redaman optik saat instalasi (mis. `-18.50` dBm) |
| `speedtest_mbps` | `decimal(6,2)` | Opsional | CRM | Hasil uji kecepatan saat aktivasi |
| `site_condition_notes` | `text` | Opsional | CRM | Catatan kondisi rumah/jalur kabel untuk histori maintenance |
| `rating_score` | `tinyint (1–5)` | Ya | CRM | Penilaian bintang pelanggan ke teknisi |
| `rating_comment` | `text` | Opsional | CRM | Ulasan pelanggan (dikirim ke HRM via `technician.rated`) |

### C. Paket Material Teknisi & Stok (`SCM ↔ CRM ↔ Finance`)
| Nama Variabel | Tipe | Wajib | Pemilik | Deskripsi |
| :--- | :--- | :---: | :--- | :--- |
| `warehouse_code` | `enum` | Ya | SCM | `WH-BKS` (Pusat Bekasi), `WH-BDG`, `WH-SBY` |
| `item_sku` | `string(20)` | Ya | SCM | `ONT-01`, `SIM-01`, `RTR-AX`, `CBL-FO` |
| `qty_available` | `int` | Ya | SCM | `qty_physical - qty_reserved - qty_damaged` |
| `kit_id` | `string(20)` | Ya | SCM | ID paket peralatan & material yang dibawa teknisi (`KIT-2026-000001`) |
| `qty_issued` | `int` | Ya | SCM | Jumlah barang yang diambil teknisi dari gudang |
| `qty_used` | `int` | Ya | CRM | Jumlah barang yang benar-benar terpakai di lokasi pelanggan |
| `qty_returned` | `int` | Ya | CRM | Jumlah barang sisa yang dikembalikan (`qty_issued - qty_used`) |
| `unit_cost` | `bigint` | Ya | SCM | Harga pokok rata-rata tertimbang (Rupiah) |

### D. Invoice, Pembayaran, & Payroll (`Finance ↔ CRM ↔ HRM`)
| Nama Variabel | Tipe | Wajib | Pemilik | Deskripsi |
| :--- | :--- | :---: | :--- | :--- |
| `invoice_no` | `string(20)` | Ya | Finance | `INV-2026-000001` |
| `virtual_account` | `string(20)` | Ya | Finance | Nomor VA simulasi (`8808000000124`) |
| `subtotal`, `discount`, `tax_amount`, `total` | `bigint` | Ya | Finance | Semua bilangan bulat Rupiah (`total = subtotal - discount + tax_amount`) |
| `payment_status` | `enum` | Ya | Finance | `UNPAID`, `PARTIALLY_PAID`, `PAID`, `VOID`, `CREDITED` |
| `payroll_period` | `char(7)` | Ya | HRM | `YYYY-MM` (`2026-11`) |
| `cost_center_code` | `enum` | Ya | Finance | `CC-SALES`, `CC-MKT`, `CC-OPS`, `CC-SCM`, `CC-FIN`, `CC-HR` |
| `base_salary`, `allowance`, `overtime_pay`, `incentive_amount` | `bigint` | Ya | HRM | Komponen pendapatan gaji (Rupiah) |
| `bpjs_employee`, `bpjs_company`, `pph21_amount`, `net_salary` | `bigint` | Ya | HRM | Potongan, beban perusahaan, & take-home pay |
| `total_company_cost` | `bigint` | Ya | HRM/Fin | `gross_salary + bpjs_company` (masuk jurnal beban gaji) |

---

## 4. Standardisasi Enum & Nama Event yang Dikunci

- **Status Order Stok Kosong:** dikunci ke **`ON_HOLD`** di database & API *(di UI pelanggan/CRM ditampilkan ramah sebagai badge `"Pending — Menunggu Stok"`)*.
- **Nama Event Payroll:** dikunci ke **`payroll.approved`** *(menggantikan `payroll.submitted`)*.
- **Event Tambahan dari Notulen PDF:**
  - `referral.used` (`CRM → HRM`) — mencatat pemakaian kode referral saat order aktif & menambah poin kinerja marketing.
  - `technician.rated` (`CRM → HRM`) — mengirim rating 1–5 pelanggan ke penilaian kinerja teknisi di HRM.
  - `kit.reconciled` (`CRM → SCM`) — melaporkan pemakaian & retur material sisa teknisi untuk update saldo gudang.
- **Role Pengguna (`user_role` di JWT):**
  - `CUSTOMER` (Pelanggan — login via CRM)
  - `TECHNICIAN`, `CRM_MANAGER`, `CS_AGENT`, `MARKETING`, `SALES_EXEC`, `SALES_MANAGER`
  - `HR_STAFF`, `HR_MANAGER`, `PAYROLL_STAFF`, `EMPLOYEE`
  - `WAREHOUSE_STAFF`, `PROCUREMENT_STAFF`, `SCM_MANAGER`
  - `AR_STAFF`, `AP_STAFF`, `ACCOUNTANT`, `FINANCE_MANAGER`
  - `DIRECTOR` (Direktur Utama — akses baca seluruh dashboard)

---

> [!NOTE]
> Jika seluruh standar variabel di atas sudah cocok, dokumen ini akan langsung kita jadikan acuan **SQL migrations, Pydantic schemas, dan Seed Data** saat membangun base project di `C:\Mirza Personal\TelcoNusa\telconusa-platform`.
