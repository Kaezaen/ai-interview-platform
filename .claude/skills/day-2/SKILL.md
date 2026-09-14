---
description: Day 2 — Database dan Authentication. SQLAlchemy, Alembic, model User/Interview, JWT auth, dan pondasi layering service/repository. Jalankan manual dengan /day-2.
disable-model-invocation: true
argument-hint: [catatan atau penyesuaian opsional]
---

# Day 2 — Database + Authentication

## Kondisi repo saat ini

- Struktur app: !`find app -type f -name "*.py" 2>/dev/null | head -40 || echo "(app/ belum ada)"`
- Migration: !`ls alembic/versions 2>/dev/null || echo "(alembic belum diinisialisasi)"`
- Commit terakhir: !`git log --oneline -8 2>/dev/null || echo "(belum ada commit)"`

## Prasyarat

Day 1 harus selesai. Kalau `docker compose up -d` belum jalan, hentikan dan beri tahu saya.

## Scope

**Dikerjakan hari ini:**
- `app/db/session.py`: async engine + sessionmaker + dependency `get_db`
- `Base` deklaratif + mixin `id` (UUID) dan `created_at`/`updated_at` (timezone-aware)
- Model `User` (email unik + indeks, `password_hash`, `is_active`) dan `Interview` (FK ke user, position, level, skills, status enum, timestamps)
- Alembic: init, konfigurasi async, migration pertama
- `app/core/security.py`: hashing password (argon2 atau bcrypt) + encode/decode JWT
- `UserRepository`, `AuthService`
- Endpoint `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- Dependency `get_current_user` yang memvalidasi JWT dan memuat user
- `POST /interviews`, `GET /interviews` (dengan pagination), `GET /interviews/{id}` dengan pengecekan kepemilikan
- Envelope error yang konsisten + exception handler terpusat

**JANGAN dikerjakan hari ini:** apa pun yang menyentuh AI, Redis, atau generate pertanyaan.

## Langkah

1. **Inspeksi** struktur yang ada dan `docs/PROJECT_SPEC.md` bagian domain model.
2. **Rencana.** Plan mode. Tunjukkan skema tabel (kolom, tipe, indeks, constraint, ON DELETE) sebelum menulis kode, lalu tunggu persetujuan. Schema yang salah di Day 2 mahal diperbaiki di Day 5.
3. **Implementasi** urut: session → model → migration → security → repository → service → router.
4. **Verifikasi:**
   ```bash
   make migrate
   docker compose exec postgres psql -U postgres -d interview -c "\dt"
   docker compose exec postgres psql -U postgres -d interview -c "\d users"
   curl -s -X POST localhost:8000/auth/register -H 'content-type: application/json' \
     -d '{"email":"a@b.com","password":"Str0ngPassw0rd!"}'
   curl -s -X POST localhost:8000/auth/login -H 'content-type: application/json' \
     -d '{"email":"a@b.com","password":"Str0ngPassw0rd!"}'
   curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/auth/me
   ```
   Tunjukkan juga bahwa `GET /interviews/{id}` milik user lain mengembalikan 404 — bukan 403, supaya tidak membocorkan keberadaan resource.
5. **Commit** terpisah per lapisan: model, migration, security, auth endpoints, interview endpoints.

## Definition of Done

- [ ] `alembic upgrade head` sukses dari database kosong
- [ ] Register menolak email duplikat dengan 409, bukan 500
- [ ] Password tersimpan sebagai hash; response tidak pernah memuat `password_hash`
- [ ] `/auth/me` menolak token invalid atau kadaluarsa dengan 401
- [ ] User A tidak bisa membaca interview milik user B
- [ ] Tidak ada query SQLAlchemy di dalam file router

## Perhatian

- `SECRET_KEY` wajib dari environment, tanpa nilai default di kode.
- Tentukan masa berlaku access token dan catat alasannya. Kalau belum ada refresh token, tulis sebagai keterbatasan yang disadari di README — jangan disembunyikan.
- Simpan `skills` sebagai tabel relasi atau kolom array/JSONB. Putuskan secara sadar dan jelaskan trade-off-nya sebelum implementasi.

$ARGUMENTS
