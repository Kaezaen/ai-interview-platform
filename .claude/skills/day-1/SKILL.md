---
description: Day 1 — Foundation. Setup repository, struktur project, FastAPI skeleton, konfigurasi, health endpoint, dan Docker Compose. Jalankan manual dengan /day-1.
disable-model-invocation: true
argument-hint: [catatan atau penyesuaian opsional]
---

# Day 1 — Foundation

## Kondisi repo saat ini

- Isi direktori: !`ls -a 2>/dev/null || true`
- Git: !`git log --oneline -5 2>/dev/null || echo "(belum ada commit)"`
- Python: !`python3 --version 2>/dev/null || echo "(python tidak ditemukan)"`
- Docker: !`docker --version 2>/dev/null || echo "(docker tidak ditemukan)"`

## Scope

**Dikerjakan hari ini:**
- Git repository + `.gitignore` (Python, venv, `.env`, `__pycache__`, `.pytest_cache`)
- `pyproject.toml` dengan dependency inti + konfigurasi Ruff
- Struktur package `app/` sesuai layering di CLAUDE.md (buat direktori + `__init__.py`, belum diisi logic)
- `app/core/config.py`: `Settings` berbasis `pydantic-settings`, baca dari environment. Gagal keras saat startup kalau variabel wajib tidak ada.
- `app/main.py`: FastAPI app, lifespan handler, metadata OpenAPI yang rapi
- Endpoint `GET /health` (liveness, tanpa dependency) dan `GET /health/ready` (readiness, cek DB+Redis — koneksinya baru ada Day 2/4, siapkan strukturnya sekarang)
- `Dockerfile` multi-stage (builder + runtime slim, user non-root)
- `docker-compose.yml`: service `api`, `postgres`, `redis` + healthcheck + named volume
- `.env.example` lengkap dengan komentar (tanpa nilai rahasia)
- `Makefile` dengan target yang ada di CLAUDE.md
- `README.md` versi awal (overview, stack, cara menjalankan)

**JANGAN dikerjakan hari ini:** model database, Alembic, autentikasi, integrasi AI, Redis client, test suite.

## Langkah

1. **Inspeksi.** Baca apa yang sudah ada. Kalau sebagian sudah dibuat, lanjutkan — jangan timpa.
2. **Rencana.** Masuk plan mode. Tunjukkan daftar file yang akan dibuat dan pilihan teknis yang perlu saya putuskan (mis. package manager: `uv` vs `pip` + `requirements.txt`). Tunggu persetujuan.
3. **Implementasi.** Buat file sesuai rencana yang disetujui.
4. **Verifikasi.** Jalankan dan tunjukkan output nyata:
   ```bash
   docker compose build
   docker compose up -d
   docker compose ps
   curl -s localhost:8000/health
   curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/docs
   ruff check .
   ```
5. **Commit.** Pecah jadi beberapa commit bermakna, bukan satu commit besar:
   - `chore(repo): initialize project structure and tooling`
   - `feat(core): add settings loaded from environment`
   - `feat(api): add liveness and readiness endpoints`
   - `chore(docker): add Dockerfile and compose stack`
   - `docs: add initial README`

## Definition of Done

- [ ] `docker compose up -d` menjalankan 3 container dan semuanya `healthy`
- [ ] `GET /health` mengembalikan 200
- [ ] Swagger terbuka di `/docs`
- [ ] `ruff check .` bersih
- [ ] `.env` ada di `.gitignore`; `git status` tidak pernah menampilkan `.env`
- [ ] `README.md` menjelaskan cara menjalankan dari nol

## Perhatian

- Credential di `docker-compose.yml` hanya untuk development lokal — beri komentar yang menyatakan itu.
- Pisahkan liveness dan readiness sejak awal; ini keputusan yang bisa dijelaskan saat interview.
- Kalau menambah dependency di luar daftar, sebutkan alasannya.

$ARGUMENTS
