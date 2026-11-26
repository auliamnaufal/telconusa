# SCM

Istilah khusus track SCM TelcoNusa: persediaan, pengadaan, dan aset barang. Melengkapi glosarium bersama di `CONTEXT.md` bagian 4; istilah yang sudah ada di sana tidak diulang.

## Barang dan stok

**Barang (Item)**:
Satu jenis barang yang dikelola SCM, dikenali dari SKU: `SIM-01`, `ONT-01`, `RTR-AX`, `CBL-FO`.
_Avoid_: Produk, material

**SKU barang**:
Kode satu Barang. Berbeda dari SKU layanan di CRM (`HOME-50`) yang menyebut paket langganan.
_Avoid_: Kode produk

**Gudang**:
Lokasi penyimpanan stok: Bekasi (pusat), Bandung, Surabaya. Setiap Gudang melayani satu kota.
_Avoid_: Lokasi, cabang

**Stok fisik**:
Jumlah Barang yang secara nyata berada di Gudang, termasuk yang ditahan dan yang rusak.

**Stok tersedia**:
Stok fisik dikurangi Reservasi dan stok rusak. Satu-satunya angka yang boleh dijanjikan ke pelanggan.
_Avoid_: Stok bebas, stok bersih

**Stok rusak**:
Barang di Gudang yang tidak layak pakai. Tidak pernah dihitung sebagai Stok tersedia.

**Reservasi**:
Stok yang ditahan untuk satu Permintaan barang agar tidak diambil permintaan lain. Berlaku 72 jam sejak Permintaan barang siap dikeluarkan, lalu dilepas otomatis.
_Avoid_: Hold, booking, penahanan

**ROP (reorder point)**:
Batas stok tersedia per Barang dan Gudang. Di bawahnya SCM perlu membeli.
_Avoid_: Stok minimum

**Pergerakan stok**:
Satu catatan perubahan saldo: barang masuk, reservasi, pelepasan, keluar, kembali, rusak. Saldo selalu bisa dijelaskan dari Pergerakan stok-nya.
_Avoid_: Mutasi, transaksi stok

**FIFO**:
Barang yang masuk lebih dulu keluar lebih dulu.

## Permintaan barang

**Paket barang (PackageKit)**:
Daftar Barang dan jumlahnya yang dibutuhkan satu paket layanan CRM. Dimiliki SCM.
_Avoid_: Kit, bundle, BOM

**Permintaan barang (StockRequest)**:
Permintaan SCM yang lahir otomatis dari satu tiket CRM, memuat baris Barang yang dibutuhkan teknisi untuk tiket itu. Satu tiket, satu Permintaan barang.
_Avoid_: Work order, permintaan material, kit

**Pengeluaran**:
Staf SCM menyerahkan barang Permintaan barang ke teknisi. Hanya staf SCM yang mencatatnya.
_Avoid_: Issue, penyerahan, checkout

**Barang tambahan**:
Baris Pengeluaran yang ditambahkan staf SCM pada Permintaan barang yang sudah dikeluarkan, tanpa persetujuan ulang.
_Avoid_: Extra, tambahan lapangan

**Laporan pemakaian**:
Jumlah terpakai dan dikembalikan per Barang yang dilaporkan teknisi lewat tiket CRM.
_Avoid_: Rekonsiliasi kit

**Selisih (discrepancy)**:
Beda antara jumlah dikeluarkan dan jumlah terpakai ditambah dikembalikan pada Laporan pemakaian.
_Avoid_: Kehilangan, shrinkage

**Return pending**:
Penanda Permintaan barang yang sudah dikeluarkan tetapi Laporan pemakaiannya belum masuk.
_Avoid_: Retur tertunda

**Retur**:
Barang yang kembali dari lapangan ke Gudang.
_Avoid_: Pengembalian, return

**Pemeriksaan retur**:
Penilaian staf Gudang atas Unit bernomor seri yang kembali: layak pakai atau rusak.
_Avoid_: QC, inspeksi

## Aset

**Unit bernomor seri (SerializedUnit)**:
Satu perangkat ONT yang dilacak sendiri dengan nomor seri dari penerimaan sampai terpasang. Hanya ONT yang bernomor seri.
_Avoid_: Aset, perangkat, serial

**Nomor seri**:
Kode unik satu Unit bernomor seri, bentuk `SN-ONT-2026-000001`, dibuat SCM saat penerimaan.
_Avoid_: SN, serial number

**Teknisi memegang (`WITH_TECHNICIAN`)**:
Status Unit bernomor seri yang sudah dikeluarkan ke teknisi dan belum dipasang atau dikembalikan.
_Avoid_: Dipinjam, dibawa

**Terpasang (`INSTALLED`)**:
Status Unit bernomor seri yang sudah dipasang di rumah pelanggan sesuai Laporan pemakaian.
_Avoid_: Terpakai

**Hilang (`LOST`)**:
Status Unit bernomor seri yang tidak ditemukan lagi sejak dipegang teknisi atau terpasang.

**Hapus buku (`WRITTEN_OFF`)**:
Status akhir Unit bernomor seri rusak atau hilang yang dikeluarkan dari aset. Hanya manajer SCM.
_Avoid_: Dibuang, scrap

## Pengadaan

**Vendor**:
Pemasok yang menjual Barang ke TelcoNusa.
_Avoid_: Supplier, pemasok

**PR (permintaan pembelian)**:
Permintaan SCM untuk membeli Barang yang kurang, diperiksa anggarannya di Finance sebelum menjadi PO.
_Avoid_: Purchase requisition, requisition

**Cek anggaran**:
Pertanyaan SCM ke Finance apakah pusat biaya SCM masih punya anggaran untuk jumlah tertentu.
_Avoid_: Budget approval

**PO (purchase order)**:
Pesanan resmi ke satu Vendor, lahir dari PR dan perlu persetujuan berjenjang sebelum dikirim ke Vendor.
_Avoid_: Order pembelian, surat pesanan

**Persetujuan berjenjang**:
Daftar role yang harus menyetujui PO; makin besar total, makin banyak role.
_Avoid_: Approval flow

**Pemisahan tugas**:
Pembuat PO tidak boleh menyetujui PO-nya sendiri.
_Avoid_: Maker-checker

**Penerimaan barang (GR)**:
Catatan staf Gudang bahwa Barang dari satu PO sudah tiba. Stok bertambah hanya setelah ini.
_Avoid_: Goods receipt note, barang datang

**Transfer**:
Perpindahan Barang antar Gudang. Stok Gudang tujuan bertambah setelah penerimaan dikonfirmasi, bukan saat barang berangkat.
_Avoid_: Mutasi antar gudang, shipment
