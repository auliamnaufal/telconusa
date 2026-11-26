# AGENTS.md: apps/scm-web

Aturan tambahan untuk agen yang bekerja di `apps/scm-web` (Next.js, port 3003). Aturan repo di `AGENTS.md` akar tetap berlaku, termasuk larangan atribusi agen pada commit dan PR.

## Mulai dari sini

1. Tanyakan issue mana yang dikerjakan (`tracks/scm/issues/SCM-<slice>-<nn>-*.md`). Jangan menebak dan jangan mengerjakan hal yang tidak ada di issue.
2. Baca berurutan: `CONTEXT.md`, `tracks/scm.md`, `tracks/scm/spec.md` (bagian 10 dan bagian yang dirujuk issue), `tracks/scm/GLOSSARY.md`, berkas issue, lalu `contracts/openapi/scm.yaml` untuk endpoint yang dipanggil layar itu.
3. Periksa `depends_on`: semuanya `DONE`. Bila belum, berhenti dan laporkan.
4. Isi `owner:` dan ubah `status: IN_PROGRESS` di berkas issue.

## Batas

- Ubah hanya berkas di `touches`: folder rute slice (`src/app/(app)/<rute>/`) dan `src/features/<nama>/`. Jangan mengubah `src/components/`, `src/lib/`, layout `(app)`, atau rute slice lain; kebutuhan itu masuk issue Slice 0 atau permintaan ke pemiliknya.
- Layar hanya memanggil `scm-api` lewat `lib/api.ts`. Jangan memanggil API track lain dari browser.
- Jangan memakai data palsu atau fallback yang menyembunyikan galat. Bila API yang dibutuhkan belum selesai, jangan menampilkan kontrolnya.
- Endpoint bertanda `DRAFT` boleh dipakai di layar SCM (lihat `tracks/scm/contract-extension.md` untuk bentuknya).

## Aturan UI

- Bahasa antarmuka Indonesia; istilah mengikuti `tracks/scm/GLOSSARY.md` (Permintaan barang, Reservasi, Pengeluaran, Penerimaan barang, PO, PR).
- Gunakan token merek di `public/brand/tokens.css` dan komponen dasar di `src/components/`. Jangan menambah pustaka UI baru tanpa alasan di PR.
- Tombol dan menu mengikuti role di JWT (`WAREHOUSE_STAFF`, `PROCUREMENT_STAFF`, `SCM_MANAGER`, `FINANCE_MANAGER`, `DIRECTOR`); server tetap menjadi penentu. Lihat spec bagian 1.2.
- Galat API tampil dengan `error.message` lewat `Toast`; kode seperti `INSUFFICIENT_STOCK` tidak disamarkan.
- Status memakai nilai baku (`READY_TO_ISSUE`, `PENDING_STOCK`, `WITH_TECHNICIAN`, …) lewat `StatusBadge`; jangan membuat status baru.

## Perintah

```bash
cd apps/scm-web
npm install
npm run dev      # http://localhost:3003
npm run build    # wajib lulus sebelum PR
```

Jika `next build` atau `next dev` gagal dengan `Cannot read properties of null (reading '1')` dari `next/font`, itu masalah pemuat font Next 15.1.6 terhadap Google Fonts (bukan kode Anda). Jalankan dengan jawaban font palsu:

```bash
NEXT_FONT_GOOGLE_MOCKED_RESPONSES=$PWD/scripts/font-mock.js npm run build
```

Jalankan API lokal: `docker compose up -d --build mysql scm-api`.

## Selesai

Semua kotak "Kriteria penerimaan" dicentang, `npm run build` lulus, PR memuat tangkapan layar dari alur yang benar-benar dijalankan terhadap API, dan `status: DONE` di berkas issue dan `tracks/scm/issues/README.md`.
