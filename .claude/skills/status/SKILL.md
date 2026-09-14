---
description: Ringkas posisi project sekarang terhadap roadmap 7 hari dan sarankan langkah berikutnya. Jalankan manual dengan /status.
disable-model-invocation: true
---

# Status Project

## Data mentah

- Commit: !`git log --oneline -25 2>/dev/null || echo "(belum ada commit)"`
- Branch: !`git branch --show-current 2>/dev/null || true`
- Perubahan belum di-commit: !`git status --short 2>/dev/null || true`
- Struktur app: !`find app -type f -name "*.py" 2>/dev/null | sort | head -50 || echo "(app/ belum ada)"`
- Migration: !`ls alembic/versions 2>/dev/null || echo "(belum ada)"`
- Test: !`find tests -name "test_*.py" 2>/dev/null || echo "(belum ada)"`
- Workflow CI: !`ls .github/workflows 2>/dev/null || echo "(belum ada)"`
- Container: !`docker compose ps 2>/dev/null || echo "(compose tidak berjalan)"`

## Tugasmu

Dari bukti di atas (bukan dari ingatan atau dari percakapan sebelumnya), laporkan singkat:

1. **Sudah selesai** — hari mana saja yang Definition of Done-nya terpenuhi. Sebut buktinya.
2. **Sedang berjalan** — pekerjaan yang setengah jadi, termasuk perubahan yang belum di-commit.
3. **Belum dikerjakan** — hari berikutnya beserta prasyarat yang masih kurang.
4. **Risiko** — hal yang akan menyakitkan kalau dibiarkan (schema yang salah, test yang hilang, rahasia yang bocor, file yang membengkak).
5. **Rekomendasi** — satu langkah berikutnya, bukan lima.

Maksimal 25 baris. Jangan menawarkan untuk mengerjakan; saya akan memanggil skill hari yang sesuai.
