---
id: SCM-D-10
title: "Transfer antar-gudang dengan konfirmasi terima"
slice: D
tier: 2
priority: P2
owner: mike
status: IN_PROGRESS
contract: "DRAFT (`/transfers`, event `shipment.delivered` belum diterbitkan)"
depends_on: [SCM-0]
touches:
  - "services/scm-api/app/catalog/**"
  - "services/scm-api/tests/catalog/**"
spec: "spec.md#f9-tier-2"
---

# SCM-D-10: Transfer antar-gudang dengan konfirmasi terima

## Konteks

Stok di cabang bertambah setelah penerimaan dikonfirmasi, bukan saat barang meninggalkan gudang.

## Yang dikerjakan

- Tabel `transfers` dan baris (`TRF-2026-0001`; migrasi tambahan slice `catalog`), status `REQUESTED → IN_TRANSIT → RECEIVED` (tambahkan mesin di `core/machines.py` hanya untuk issue ini).
- `POST /transfers`, `POST /transfers/{no}/dispatch` (`ledger.issue_extra` gudang asal; unit serial berpindah lewat `AssetPort`), `POST /transfers/{no}/receive` (`ledger.receive` gudang tujuan).
- Saran transfer: `GET /stock/balances` menandai gudang yang kelebihan di atas ROP×2.

## Kriteria penerimaan

- [x] Setelah dispatch, saldo asal turun dan saldo tujuan belum berubah; setelah receive, saldo tujuan naik.
- [x] Transfer ke gudang yang sama ditolak `422`.
- [ ] Unit serial tetap utuh dan tercatat di riwayat selama perpindahan.

## Tes

- `tests/catalog/test_transfer.py`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
