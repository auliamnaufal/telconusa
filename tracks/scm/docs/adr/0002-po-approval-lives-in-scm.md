# Persetujuan PO disimpan di SCM, role dibaca dari JWT

Brief menyebut persetujuan berjenjang "dari HRM". SCM memiliki status PO (aturan satu pemilik per status), jadi rantai persetujuan (`PoApproval`) disimpan di SCM dan penyetuju (`SCM_MANAGER`, `FINANCE_MANAGER`, `DIRECTOR`) masuk ke `scm-web` dengan role dari JWT HRM. Tidak ada panggilan SCM ke HRM saat menyetujui.

Alternatif yang ditolak: SCM memanggil HRM untuk memeriksa wewenang tiap persetujuan (satu titik gagal tambahan, kontrak baru, dan HRM tidak memiliki PO). Konsekuensi: perubahan wewenang di HRM berlaku lewat role JWT berikutnya, bukan seketika.
