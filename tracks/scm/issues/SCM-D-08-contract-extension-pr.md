---
id: SCM-D-08
title: "PR kontrak bersama dari `contract-extension.md`"
slice: D
tier: 1
priority: P1
owner: mike
status: TODO
contract: "DRAFT -> K"
depends_on: [SCM-0]
touches:
  - "contracts/openapi/scm.yaml"
  - "contracts/events/*.schema.json"
  - "contracts/examples/events/*.json"
  - "tracks/scm.md"
  - "tracks/scm/contract-extension.md"
spec: "contract-extension.md"
---

# SCM-D-08: PR kontrak bersama dari `contract-extension.md`

## Konteks

Area bersama: PR terpisah, review keempat track. Issue ini hanya menyiapkan dan membuka PR, tidak menunggu slice lain.

## Yang dikerjakan

- Pindahkan endpoint dan event di `contract-extension.md` ke `contracts/` (OpenAPI dengan `x-auth`, `x-roles`/`x-scope`, `x-consumers`; skema event dengan `x-publisher`, `x-consumers`; contoh event valid).
- Terapkan koreksi contoh (bagian 3 di `contract-extension.md`).
- Perbarui `provides` di `tracks/scm.md` dengan status `PLANNED`/`MOCKED` yang benar dan jalankan `python tools/check_contracts.py`.
- Buka PR terpisah dan minta review CRM, Finance, HRM. Tambahkan permintaan di bagian Requests file track mereka sesuai bagian 4.

## Kriteria penerimaan

- [ ] `python tools/check_contracts.py --check` lulus.
- [ ] PR tidak menyentuh `services/shared/` kecuali `EVENT_SUBSCRIBERS` yang memang diperlukan, dan hal itu disebut di deskripsi PR.
- [ ] Setelah di-merge, issue lanjutan penerbitan event dibuat (lihat `issues/README.md`).

## Tes

- `python tools/check_contracts.py` dan `pytest -q tests`.

## Selesai bila

- [ ] Semua kriteria di atas terpenuhi dan tes issue ini lulus (`pytest -q services/scm-api/tests`).
- [ ] Hanya berkas di `touches` yang berubah, selain baris `status` issue ini dan baris kontrak terkait di `tracks/scm.md`.
- [ ] `status` issue ini diubah menjadi `DONE` di PR yang sama.
