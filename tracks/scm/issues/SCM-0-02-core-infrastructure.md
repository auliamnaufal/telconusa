---
id: SCM-0-02
title: "Infrastruktur inti: event, auth, galat, idempotensi, outbox, audit, harness tes"
slice: 0
tier: 1
priority: P0
owner: Naufal
status: DONE
contract: "none"
depends_on: [SCM-0-01, SCM-0-05]
touches:
  - "services/scm-api/app/core/**"
  - "services/scm-api/app/main.py"
  - "services/scm-api/tests/conftest.py"
spec: "spec.md#7-aturan-lintas-fitur"
---

# SCM-0-02: Infrastruktur inti: event, auth, galat, idempotensi, outbox, audit, harness tes

## Konteks

Semua slice memakai fondasi yang sama untuk menerima event, memeriksa peran, melaporkan galat, dan menerbitkan event.

## Yang dikerjakan

- `app/core/events.py`: daftar handler (`@handler("ticket.created")`) dan penerima event dari `shared.event_receiver.create_events_router` (tanda tangan wajib, `event_id` dicatat). Slice mendaftarkan handler di `events.py` masing-masing; `main.py` mengimpornya sekali.
- `app/core/auth.py`: `require_scm_roles(*roles)` (JWT pengguna) dan `require_scope("stock:read")` (token layanan) berbasis `shared.auth` dan `shared.service_auth`; mengembalikan identitas pelaku (`sub`, `role`).
- `app/core/errors.py`: `ScmError(code, status, message, details)` dan penangan yang menghasilkan format galat baku dengan `correlation_id` dari `X-Correlation-Id`.
- `app/core/idempotency.py`: dependensi `Idempotency-Key`; pengulangan dengan kunci sama mengembalikan respons tersimpan, tanpa efek ganda.
- `app/core/outbox.py`: `publish(db, event_type, correlation_id, data)` memanggil `shared.outbox.enqueue_event` (`source="scm"`) dalam transaksi pemanggil; relay dijalankan di lifespan lewat `shared.outbox.run_relay`.
- `app/core/audit.py`: `record(db, actor, action, entity, entity_id, detail, correlation_id)`.
- `tests/conftest.py`: secret uji, SQLite memori, `TestClient` dengan override `get_db`, pembuat token pengguna per role, pembuat event bertanda tangan.

## Kriteria penerimaan

- [x] Event tanpa atau dengan tanda tangan salah ditolak `401`.
- [x] Event dengan `event_id` yang sama diproses sekali.
- [x] Galat memakai format baku dan membawa `correlation_id`.
- [x] `POST` dengan `Idempotency-Key` yang sama mengembalikan respons yang sama dan tidak menjalankan handler dua kali.
- [x] Event yang di-`publish` berstatus pending di outbox bersama perubahan datanya, dan hilang bila transaksi di-rollback.

## Tes

- Satu berkas tes per modul `core` di `services/scm-api/tests/core/`.

## Selesai bila

- [x] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [x] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [x] `status` issue ini diubah menjadi `DONE` di PR yang sama.
