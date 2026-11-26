# Empat slice vertikal paralel di atas Slice 0 dengan port

`scm-api` dibagi menjadi paket per slice (`stock`, `procurement`, `assets`, `catalog`) dan `scm-web` menjadi folder rute per slice, supaya empat orang bekerja tanpa saling menunggu. Hal yang dipakai bersama (buku besar stok, tabel inti, migrasi, kerangka web, penerima event) dibangun sekali di Slice 0 dan tidak diubah slice lain. Ketergantungan antar-slice lewat *port* (antarmuka dengan stub di `app/core/ports.py`); stub diganti implementasi nyata oleh slice pemiliknya tanpa mengubah tanda tangan.

Alternatif yang ditolak: potong per lapisan (satu orang API, satu orang web), yang memaksa orang web menunggu API; dan satu `main.py`/`models.py` bersama, yang membuat setiap PR berbenturan. Konsekuensi: perubahan pada `app/core/` hanya lewat issue yang menyebutnya, dan tiap slice memiliki migrasi Alembic sendiri dengan `branch_labels`.
