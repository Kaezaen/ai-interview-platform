# AI Interview Platform

Backend platform untuk simulasi interview: AI membuat pertanyaan sesuai posisi/level/skill,
user menjawab, AI mengevaluasi dengan rubrik terstruktur, sistem menyimpan skor dan feedback.

Ini portfolio project production-oriented, bukan demo CRUD. Kualitas arsitektur, validasi,
dan testing lebih penting daripada jumlah fitur.

**Spesifikasi lengkap ada di `docs/PROJECT_SPEC.md` — baca file itu saat butuh detail
domain, kontrak API, atau roadmap. Jangan asumsikan isinya dari ingatan.**

## Stack

Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 (async) · Alembic · PostgreSQL 16 ·
Redis 7 · Gemini (via abstraksi provider) · Docker Compose · pytest · Ruff · GitHub Actions

## Perintah

```bash
docker compose up -d              # jalankan api + postgres + redis
docker compose logs -f api        # lihat log
make migrate                      # alembic upgrade head
make revision m="pesan"           # bikin migration baru (autogenerate)
make test                         # pytest
make lint                         # ruff check . && ruff format --check .
make fmt                          # ruff format . && ruff check --fix .
```

API: http://localhost:8000 · Swagger: http://localhost:8000/docs

## Arsitektur

Arah dependensi satu arah, tidak boleh dibalik:

```
Router  →  Service  →  Repository  →  Database
             ↓
         AIProvider (abstraksi)  →  GeminiProvider | FakeProvider
```

- Router: parsing request, auth dependency, panggil service, mapping ke response schema. Tidak ada business logic, tidak ada query SQL.
- Service: business logic, transaksi, orkestrasi AI. Tidak tahu soal objek HTTP (`Request`, `HTTPException`).
- Repository: satu-satunya tempat query SQLAlchemy.
- Service hanya mengenal interface `AIProvider`. Tidak boleh ada `import google.generativeai` di luar `app/services/ai/gemini_provider.py`.

## Aturan yang tidak bisa dinegosiasi

1. Jangan pernah commit `.env`, API key, atau kredensial. Hanya `.env.example` yang masuk git.
2. Perubahan schema database **selalu** lewat migration Alembic. Dilarang `Base.metadata.create_all()` di jalur aplikasi.
3. Test tidak boleh memanggil Gemini sungguhan. Pakai `FakeProvider` atau mock.
4. Output AI **wajib** divalidasi dengan Pydantic sebelum disimpan. Output yang gagal validasi tidak pernah masuk database.
5. Jangan pernah mengembalikan exception mentah / stack trace ke client. Semua error keluar dalam envelope error yang konsisten.
6. Redis adalah cache dan state sementara, bukan sumber kebenaran. Aplikasi harus tetap melayani request saat Redis mati (degradasi, bukan crash).
7. Skor agregat dihitung di Python dari sub-skor yang diberikan AI. Jangan percaya LLM untuk aritmatika.
8. Jangan log password, token, API key, atau isi jawaban user secara utuh.

## Konvensi kode

- Type hints di semua fungsi publik. Pydantic untuk semua boundary (request, response, output AI).
- Fungsi idealnya < 40 baris; file < 300 baris. Kalau lebih, pecah.
- Custom exception per domain (`AIUnavailableError`, `InterviewNotFoundError`), diterjemahkan ke HTTP di satu exception handler terpusat.
- Async konsisten: `async def` untuk semua I/O (DB, Redis, HTTP). Jangan campur driver sync.
- Nama eksplisit. `evaluate_answer()` bukan `process()`.

## Git

Conventional commits: `feat:`, `fix:`, `test:`, `refactor:`, `chore:`, `ci:`, `docs:`.
Satu commit = satu unit logis yang bisa dijelaskan. Jangan satu commit raksasa per hari.
Contoh: `feat(auth): add JWT login endpoint`, `test(interviews): cover ownership checks`.

Kerja di branch `feature/<nama>`, merge ke `main`. Jangan force push ke `main`.

## Cara kerja dengan saya (user)

1. **Inspeksi dulu, jangan berasumsi.** Baca file yang ada sebelum menulis. Jangan mengklaim sesuatu sudah ada tanpa mengeceknya.
2. **Rencana sebelum implementasi.** Untuk task yang menyentuh > 2 file, masuk plan mode dan tunggu persetujuan.
3. **Jangan overwrite implementasi yang sudah benar.** Kalau mau ganti pendekatan, jelaskan alasannya dulu.
4. **Jangan kerjakan di luar scope yang diminta.** Kalau menemukan masalah lain, catat, jangan langsung perbaiki.
5. **Selesai = terverifikasi.** Jalankan lint + test dan tunjukkan outputnya. Jangan bilang "sudah jalan" tanpa bukti.
6. **Kritis.** Kalau saya minta sesuatu yang tidak scalable, tidak aman, atau over-engineered, bilang langsung dan tawarkan alternatif.

Penjelasan mendalam (WHAT/WHY/HOW/TRADE-OFF) tidak perlu di setiap perubahan — saya akan
minta lewat `/mentor` kalau butuh. Keputusan arsitektur penting dicatat lewat `/adr`.

## Workflow harian

Roadmap 7 hari dijalankan lewat skill: `/day-1` … `/day-7`. Gunakan `/status` untuk
melihat posisi progres sekarang. Jangan lompat hari tanpa diminta.
