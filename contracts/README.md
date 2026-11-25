# contracts/

Kontrak antar-track yang bisa dibaca mesin. Aturan penamaan dan format ada di [`variable_standards.md`](variable_standards.md).

```text
contracts/
├── variable_standards.md        # konvensi, ID, status, role, kamus variabel
├── openapi/<track>.yaml         # API milik satu track (OpenAPI 3.0.3)
├── events/<event>.schema.json   # skema isi `data` satu event (JSON Schema 2020-12)
└── examples/events/<event>.json # contoh amplop event lengkap
```

## Aturan bacaan

- **API.** Kunci path sudah memuat `/api/v1`. Pengenal operasi di file track berbentuk `METHOD path`, contoh `GET /api/v1/catalog`. Setiap operasi memuat `operationId`, `x-auth` (`public`, `user`, atau `service`), `x-roles` (untuk `user`), `x-scope` (wajib untuk `service`), dan `x-consumers` (track yang memanggilnya).
- **Event.** Nama file sama dengan nama event. Skema memuat `x-publisher` dan `x-consumers`. Contoh di `examples/events/` harus lolos skema; contoh yang sama dipakai `tools/send_fixture.py`.
- **Mock.** `docker compose --profile mock up -d` menyajikan contoh respons `openapi/*.yaml` di port 9001–9004 (lihat `mock/README.md`).

## Menambah atau mengubah kontrak

1. Ubah file di sini lewat PR. Track terdampak (pemanggil, penerima, penerbit) harus me-review.
2. Perbarui `provides` dan `consumes` di `tracks/<track>.md` untuk track yang bersangkutan.
3. Jalankan `python tools/check_contracts.py`. Perintah ini memeriksa bahwa API, event, dan file track saling cocok dan memperbarui `tracks/STATUS.md`. CI menjalankan versi `--check`.
4. Menambah bidang opsional atau operasi baru boleh. Mengubah atau menghapus bidang wajib butuh `version` event baru atau `/api/v2`, dan persetujuan konsumen.

## Menambah event

1. Buat `events/<nama>.schema.json` dengan `x-publisher` dan `x-consumers`.
2. Buat `examples/events/<nama>.json` (amplop lengkap, `data` valid terhadap skema).
3. Daftarkan di `provides.events` penerbit dan `consumes.events` penerima. Tambahkan penerima ke `EVENT_SUBSCRIBERS` di `services/shared/events.py` (area bersama).

## Menambah endpoint

1. Tambahkan operasi di `openapi/<track>.yaml` beserta contoh respons dan `x-auth`.
2. Daftarkan di `provides.api` track pemilik dan `consumes.api` track yang memanggilnya.
