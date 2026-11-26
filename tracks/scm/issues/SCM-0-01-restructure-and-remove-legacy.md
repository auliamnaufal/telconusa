---
id: SCM-0-01
title: "Restrukturisasi paket per slice dan hapus kode lama"
slice: 0
tier: 1
priority: P0
owner: Naufal
status: TODO
contract: "none"
depends_on: []
touches:
  - "services/scm-api/app/**"
  - "services/scm-api/requirements.txt"
spec: "spec.md#4-model-data; ADR-0003"
---

# SCM-0-01: Restrukturisasi paket per slice dan hapus kode lama

## Konteks

`app/main.py` dan `app/models.py` berisi logika lama (work order, `TechnicianKit`, PO yang langsung `APPROVED`, penerima event tanpa tanda tangan). Semua slice harus bisa bekerja di berkas masing-masing tanpa berbenturan.

## Yang dikerjakan

- Buat paket `app/core`, `app/stock`, `app/procurement`, `app/assets`, `app/catalog`; masing-masing berisi `__init__.py`, `models.py`, `service.py`, `router.py`, `events.py` (kosong tapi bisa diimpor).
- `app/main.py` hanya membuat aplikasi, CORS, `GET /health`, `include_router` untuk setiap router slice, dan pemasangan penerima event (diisi `SCM-0-02`).
- Hapus: `TechnicianKit`, `work_order_code`, `create_po` lama, `/items/requirements`, `reconcile_kit`, `receive_event` buatan sendiri, tabel `outbox_events` lokal, dan penanganan event lama (`kit.reconciled`, `workorder.*`).
- Hapus `aio-pika` dari `requirements.txt` bila tidak dipakai di `app/`.

## Kriteria penerimaan

- [ ] Aplikasi menyala dan `GET /health` menjawab 200.
- [ ] Pencarian `TechnicianKit`, `work_order`, `kit.reconciled`, `budget_approved = True`, dan `except Exception: pass` di `services/scm-api/app` tidak menemukan apa pun.
- [ ] Setiap slice punya paket kosong yang bisa diimpor; `main.py` sudah menyertakan semua router sehingga slice tidak perlu mengedit `main.py`.
- [ ] Tiga temuan P0 di backlog `tracks/scm.md` terhapus bersama kodenya (digantikan oleh `SCM-0-02`, `SCM-B-01`, `SCM-B-03`).

## Tes

- Tes `GET /health` di `services/scm-api/tests/test_health.py`.

## Di luar issue ini

- Model baru, migrasi, dan seed (`SCM-0-05`).

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
