---
id: SCM-0-04
title: "Port antar-slice dan mesin status"
slice: 0
tier: 1
priority: P0
owner: Naufal
status: DONE
contract: "none"
depends_on: [SCM-0-01]
touches:
  - "services/scm-api/app/core/ports.py"
  - "services/scm-api/app/core/machines.py"
  - "services/scm-api/tests/core/test_ports.py"
  - "services/scm-api/tests/core/test_machines.py"
spec: "ADR-0003; spec.md#5-status"
---

# SCM-0-04: Port antar-slice dan mesin status

## Konteks

Slice saling memanggil lewat antarmuka tetap, sehingga tidak ada yang menunggu implementasi slice lain.

## Yang dikerjakan

- `ports.py`: `Protocol` dan registri `ports.procurement`, `ports.assets`, `ports.stock_requests`, dengan fungsi `ports.override(...)` untuk tes.
- `ProcurementPort.request_purchase(db, *, stock_request_no, warehouse_code, shortages, correlation_id) -> str` (kode PR). Diimplementasikan `SCM-B-01`.
- `AssetPort` (diimplementasikan `SCM-C-01`): `register_units(db, *, item_sku, warehouse_code, qty, gr_no) -> list[str]`; `reserve_units(db, *, item_sku, warehouse_code, qty, stock_request_no) -> list[str]` (FIFO); `release_units(db, *, stock_request_no)`; `units_for_request(db, *, stock_request_no) -> list[str]`; `mark_with_technician(db, *, stock_request_no, serial_numbers, technician_employee_id) -> list[str]`; `mark_installed(db, *, serial_numbers, ticket_code)`; `mark_returned(db, *, serial_numbers)`; `mark_faulty(db, *, serial_number, notes)`.
- `StockRequestPort.reevaluate_pending(db, *, item_sku, warehouse_code) -> list[str]` (daftar `stock_request_no` yang menjadi siap). Diimplementasikan `SCM-A-09`.
- Implementasi bawaan (stub) setiap port melempar `NotImplementedError("<Port> belum diimplementasikan (<issue>)")`. Tidak ada stub yang pura-pura berhasil. Slice menguji dirinya dengan `ports.override` memakai fake di tesnya.
- `machines.py`: mesin status PR, PO, dan GR memakai `shared.transitions.StateMachine` (jangan mengubah `shared/`).

## Kriteria penerimaan

- [x] Memanggil port tanpa implementasi gagal dengan pesan yang menyebut issue pemiliknya.
- [x] `ports.override` memulihkan implementasi semula setelah tes.
- [x] Mesin PR dan PO sesuai spec bagian 5.3 dan 5.4; transisi lain menjawab `409 INVALID_TRANSITION`.

## Tes

- `services/scm-api/tests/core/test_ports.py` dan `test_machines.py`.

## Selesai bila

- [x] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [x] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [x] `status` issue ini diubah menjadi `DONE` di PR yang sama.
