# Mock server antar-track

Profile `mock` di `docker-compose.yml` menjalankan [Prism](https://stoplight.io/open-source/prism) untuk tiap track.
Prism membaca `contracts/openapi/<track>.yaml` dan membalas dengan **contoh (`example`) yang ada di kontrak**,
sehingga kelompok bisa mengembangkan sisi konsumer tanpa menunggu API kelompok lain selesai.

## Port

| Mock           | Kontrak                          | URL dari host           | URL dari container      |
|----------------|----------------------------------|-------------------------|-------------------------|
| `mock-crm`     | `contracts/openapi/crm.yaml`     | `http://localhost:9001` | `http://mock-crm:4010`     |
| `mock-hrm`     | `contracts/openapi/hrm.yaml`     | `http://localhost:9002` | `http://mock-hrm:4010`     |
| `mock-scm`     | `contracts/openapi/scm.yaml`     | `http://localhost:9003` | `http://mock-scm:4010`     |
| `mock-finance` | `contracts/openapi/finance.yaml` | `http://localhost:9004` | `http://mock-finance:4010` |

## Menjalankan

Jalankan hanya service milik kelompok sendiri ditambah mock untuk track lain. Contoh tim CRM yang butuh SCM:

```bash
tools/setup-env.sh
SCM_API_URL_INTERNAL=http://mock-scm:4010 \
  docker compose --profile mock up --build mysql crm-api mock-scm
```

`<TRACK>_API_URL_INTERNAL` (`CRM`, `HRM`, `SCM`, `FINANCE`) menentukan alamat yang dipakai service lain.
Bisa diset di `.env` atau di depan perintah `docker compose`. Kosongkan untuk kembali ke API sungguhan
(`http://<track>-api:<port>`).

## Batasan

- Mock hanya menyajikan contoh yang ditulis di `contracts/openapi`; tidak ada state, validasi bisnis, atau database.
  Operasi tanpa `example` di kontrak akan dibalas data hasil generate Prism.
- Perubahan kontrak langsung terlihat setelah container mock di-restart.
- Mock tidak mengirim event. Untuk mensimulasikan event dari track lain, kirim fixture ke service Anda:

```bash
python tools/send_fixture.py invoice.issued --to http://localhost:8004
```

Argumen pertama adalah tipe event (nama file di `contracts/examples/events/`), `--to` adalah base URL
service penerima (event dikirim ke `/internal/events` dengan tanda tangan HMAC dari `HMAC_WEBHOOK_SECRET`).
