# Template modul baru

Titik awal untuk **modul baru** (bukan untuk `crm-api`, `hrm-api`, `scm-api`, `finance-api` yang sudah ada).
Isinya sudah memakai helper baseline: kode berurutan, outbox + relay event, penerima event idempotent,
dan auth service-to-service.

## Langkah

1. Salin dan ganti nama (contoh modul `procurement`, port `8005`):

   ```bash
   cp -r services/_template services/procurement-api
   cd services/procurement-api
   grep -rl '__NAME__\|__PORT__' . | xargs sed -i.bak 's/__NAME__/procurement/g; s/__PORT__/8005/g'
   find . -name '*.bak' -delete
   ```

2. Tambahkan kontrak: `contracts/openapi/procurement.yaml` (tiap operasi punya `operationId`, `x-auth`,
   `x-roles`/`x-scope`, `x-consumers`), skema event di `contracts/events/`, dan contoh envelope di
   `contracts/examples/events/`.
3. Salin `tracks/_template.md` menjadi `tracks/procurement.md`, isi front matter (`owns`, `provides`, `consumes`).
   Item `provides` berstatus `LIVE` wajib punya `test` yang ada di repo.
4. Daftarkan service di `docker-compose.yml`: salin blok salah satu `*-api`, ganti nama, port, `DATABASE_URL`,
   dan tambahkan variabel `<NAMA>_API_URL_INTERNAL` bila modul lain perlu memanggilnya. Buat database-nya di `mysql/init`.
5. Ganti entity `Example` di `app/models.py`, endpoint contoh di `app/main.py`, dan handler event
   `EVENT_HANDLERS` dengan domain modul. Tambahkan migration baru setelah `0001_baseline_tables`.
6. Jalankan `pytest` dari folder service (`PYTHONPATH=.:..` agar `shared` terbaca).

## Checklist helper baseline

- [ ] ID bisnis berurutan lewat `next_code(db, Counter, key, template)` (`shared.ids`), bukan `count()+1`.
- [ ] Event keluar lewat `enqueue_event(db, OutboxEvent, event_type, correlation_id, data, source)` dalam
      transaksi yang sama dengan perubahan data; pengiriman dilakukan `run_relay` (sudah di lifespan `app/main.py`).
- [ ] Event masuk lewat `create_events_router(get_db, ProcessedEvent, handlers)`; handler harus aman diulang.
- [ ] Endpoint untuk user memakai `require_roles(...)`; endpoint untuk service lain memakai `require_service('<scope>')`.
- [ ] Tabel `id_counters`, `outbox_events`, `dead_letter_events`, `processed_events` ada di migration.
- [ ] `/health` mengembalikan `HealthResponse`.
- [ ] Setiap endpoint dan event tercatat di `contracts/` dan `tracks/<nama>.md`.
