# AGENTS.md: services/scm-api

Aturan tambahan untuk agen yang bekerja di `services/scm-api`. Aturan repo di `AGENTS.md` akar tetap berlaku, termasuk larangan atribusi agen pada commit dan PR.

## Mulai dari sini

1. Tanyakan issue mana yang dikerjakan (`tracks/scm/issues/SCM-<slice>-<nn>-*.md`). Jangan menebak dan jangan mengerjakan hal yang tidak ada di issue.
2. Baca berurutan: `CONTEXT.md`, `tracks/scm.md`, `tracks/scm/spec.md` (bagian yang dirujuk issue), `tracks/scm/GLOSSARY.md`, berkas issue, lalu kontrak yang disentuh (`contracts/openapi/scm.yaml`, `contracts/events/*.schema.json`, `contracts/variable_standards.md`).
3. Periksa `depends_on` di berkas issue: semuanya harus `DONE`. Bila belum, berhenti dan laporkan.
4. Isi `owner:` dan ubah `status: IN_PROGRESS` di berkas issue.

## Batas

- Ubah hanya berkas yang tercantum di `touches` pada issue, ditambah baris `status` issue itu dan baris kontrak terkait di `tracks/scm.md`.
- Jangan mengubah `app/core/` kecuali issue menyebutnya. Jangan mengedit `app/main.py`; semua router dan handler slice sudah terpasang oleh Slice 0.
- Jangan mengubah `services/shared/`, `contracts/`, `docker-compose.yml`, `.env.example`, `mysql/init/`. Bila perlu, tulis permintaan di PR; perubahan kontrak lewat `SCM-D-08`.
- Jangan menulis ke tabel milik slice lain. Pakai port di `app/core/ports.py`. Port yang belum diimplementasikan melempar `NotImplementedError` dengan nama issue pemiliknya; di tes, pakai `ports.override` dengan fake. Jangan mengisi stub dengan perilaku pura-pura.

## Peta kode

| Jalur | Isi |
| :--- | :--- |
| `app/core/` | Buku besar stok (`ledger.py`), port, mesin status, event, auth, galat, idempotensi, outbox, audit (Slice 0) |
| `app/stock/` | Permintaan barang, reservasi, pengeluaran, laporan pemakaian (Slice A) |
| `app/procurement/` | PR, cek anggaran, PO, persetujuan, penerimaan barang (Slice B) |
| `app/assets/` | Unit bernomor seri, status, pemeriksaan retur (Slice C) |
| `app/catalog/` | Data master, paket barang, API stok, dashboard, transfer (Slice D) |
| `tests/<slice>/` | Tes milik slice |

## Aturan kode

- Semua perubahan saldo lewat `app/core/ledger.py`. Semua perubahan status lewat mesin status (`shared.transitions` atau `app/core/machines.py`); transisi tidak sah menjawab `409 INVALID_TRANSITION`.
- Event diterbitkan lewat `core.outbox.publish` dalam transaksi yang sama dengan perubahan datanya. Jangan menerbitkan event yang belum ada di `contracts/events/`. Event diterima lewat handler yang didaftarkan di `app/<slice>/events.py` (tanda tangan diperiksa oleh penerima bersama).
- Kode bisnis dari `shared.ids.next_code`, bukan `count()+1`. Uang `BIGINT` rupiah, waktu WIB `+07:00`.
- `POST` transaksi menerima `Idempotency-Key`. Galat memakai `ScmError` (format baku dengan `correlation_id`).
- Setiap endpoint menyatakan peran lewat `core.auth.require_scm_roles` atau cakupan layanan lewat `core.auth.require_scope`.
- Jangan menelan galat (`except: pass`). Kegagalan Finance menahan PR, tidak pernah meloloskannya.
- Gaya mengikuti kode yang ada; jangan menambah abstraksi atau fitur di luar kriteria issue.

## Perintah

```bash
pytest -q services/scm-api/tests               # tes layanan ini
pytest -q services/scm-api/tests/<slice>       # tes slice
python tools/check_contracts.py                # setelah mengubah tracks/scm.md
docker compose up -d --build mysql scm-api     # jalankan layanan
```

## Selesai

Semua kotak "Kriteria penerimaan" dicentang, tes issue lulus, `status: DONE` di berkas issue dan `tracks/scm/issues/README.md`. Baris kontrak di `tracks/scm.md` hanya `LIVE` bila tes lulus; endpoint berstatus `DRAFT` tidak ditandai `LIVE`.
