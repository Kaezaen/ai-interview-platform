---
description: Verifikasi perubahan dan buat commit dengan pesan conventional commit. Jalankan manual dengan /ship.
disable-model-invocation: true
allowed-tools: Bash(git add:*) Bash(git commit:*) Bash(git status:*) Bash(git diff:*) Bash(make:*) Bash(ruff:*) Bash(pytest:*)
---

# Ship

- Status: !`git status --short 2>/dev/null || true`
- Diff ringkas: !`git diff --stat HEAD 2>/dev/null || true`

## Langkah

1. **Periksa kebersihan.** Pastikan tidak ada `.env`, kredensial, file sementara, atau `print()` sisa debug yang ikut. Kalau ada, hentikan dan laporkan.
2. **Verifikasi.** Jalankan `make lint` lalu `make test`. Kalau salah satu merah, berhenti — jangan commit kode yang gagal. Laporkan penyebabnya.
3. **Kelompokkan.** Pecah perubahan menjadi commit-commit logis. Satu commit tidak boleh mencampur fitur baru, refactor, dan perubahan dokumentasi.
4. **Commit.** Format conventional commit, subjek maksimal 72 karakter, dalam bentuk imperatif bahasa Inggris. Tambahkan badan pesan hanya kalau "kenapa"-nya tidak jelas dari subjek.
5. **Laporkan** daftar commit yang dibuat dan apa yang masih tersisa belum di-commit.

Jangan push kecuali saya memintanya.
