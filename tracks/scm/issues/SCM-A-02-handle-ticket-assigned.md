---
id: SCM-A-02
title: "Handler `ticket.assigned` mengisi teknisi"
slice: A
tier: 1
priority: P1
owner: Naufal
status: TODO
contract: "K (event `ticket.assigned`)"
depends_on: [SCM-0, SCM-A-01]
touches:
  - "services/scm-api/app/stock/**"
  - "services/scm-api/tests/stock/**"
spec: "spec.md#f2-teknisi-ditugaskan"
---

# SCM-A-02: Handler `ticket.assigned` mengisi teknisi

## Konteks

Langkah 6 alur demo. Event bisa tiba sebelum atau sesudah `ticket.created`.

## Yang dikerjakan

- Handler `ticket.assigned`: isi `technician_employee_id` pada permintaan milik `ticket_code`.
- Bila permintaan belum ada, simpan di `PendingAssignment` dan terapkan di `SCM-A-01` saat permintaan dibuat (ubah handler A-01 secukupnya).
- Penugasan ulang teknisi (event kedua dengan teknisi berbeda) menimpa teknisi selama status belum `ISSUED`; sesudahnya diabaikan dan dicatat.

## Kriteria penerimaan

- [ ] Event tiba sesudah permintaan: teknisi terisi.
- [ ] Event tiba sebelum permintaan: setelah `ticket.created` diproses, teknisi terisi.
- [ ] Event ganda tidak mengubah apa pun. Status permintaan tidak berubah oleh event ini.

## Tes

- `tests/stock/test_ticket_assigned.py`, termasuk kasus tak berurutan.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
