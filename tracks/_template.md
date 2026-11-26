---
track: TEMPLATE
owner_team: Nama tim
updated: YYYY-MM-DD
folders: []
owns: []
provides:
  api: []
  events: []
consumes:
  api: []
  events: []
---

# Track <nama>

**Pemilik:** <tim>. **Folder:** <daftar folder>.

## Lingkup

Satu paragraf: apa yang dimiliki track ini dan apa yang bukan.

## Slice requirements (acceptance untuk demo)

Butir yang bisa didemokan dan dites, turunan alur di `CONTEXT.md` bagian 5.

## Integrasi

Siapa yang dipanggil, siapa yang memanggil, event apa yang diterbitkan dan diterima. Detail ada di front matter.

## Backlog

| Prioritas | Temuan atau fitur | Lokasi |
| :--- | :--- | :--- |

## Open items

## Requests

_Tim lain menambah baris `- dari <track>, <tanggal>: <permintaan>` lewat PR._

## Decisions

- YYYY-MM-DD: keputusan dan alasannya.

Isi `provides` dan `consumes` memakai bentuk berikut, lalu jalankan `python tools/check_contracts.py`:

```yaml
provides:
  api:    [{id: "GET /api/v1/contoh", status: PLANNED, since: 2026-11-25}]
  events: [{id: contoh.dibuat, status: PLANNED, since: 2026-11-25}]
consumes:
  api:    [{id: "GET /api/v1/lain", from: crm, status: PLANNED}]
  events: [{id: lain.terjadi, from: finance, status: PLANNED}]
```
