---
description: Day 5 — Testing dan CI/CD. Pytest, fixture, test database, mocking AI, linting, dan GitHub Actions. Jalankan manual dengan /day-5.
disable-model-invocation: true
argument-hint: [catatan atau penyesuaian opsional]
---

# Day 5 — Testing + CI/CD

## Kondisi repo saat ini

- Test yang ada: !`find tests -type f -name "*.py" 2>/dev/null || echo "(tests/ belum ada)"`
- Workflow: !`ls .github/workflows 2>/dev/null || echo "(belum ada workflow)"`
- Router: !`find app/api -type f -name "*.py" 2>/dev/null | head -20 || echo "(app/api belum ada)"`

## Scope

**Dikerjakan hari ini:**
- `tests/conftest.py`: fixture app, database test terisolasi, `AsyncClient` httpx, fixture user terautentikasi, override dependency `AIProvider` ke `FakeProvider`.
- Strategi isolasi database: setiap test jalan dalam transaksi yang di-rollback, atau database dibuat ulang per sesi test. Pilih satu dan konsisten.
- `tests/test_auth.py`: register, duplikat email, login benar/salah, akses endpoint terproteksi tanpa token dan dengan token kadaluarsa.
- `tests/test_interviews.py`: pembuatan interview, validasi input, isolasi kepemilikan (user A vs user B), pagination.
- `tests/test_questions.py`: generate dengan provider palsu, idempotensi, penolakan output cacat.
- `tests/test_evaluation.py`: perhitungan skor berbobot (unit test murni, tanpa I/O), evaluasi ganda, penanganan `AIUnavailableError` → 503.
- `tests/test_cache.py`: perilaku ketika Redis tidak tersedia.
- `.github/workflows/ci.yml`: job lint + test dengan service container postgres dan redis, plus job build image Docker.

## Aturan kritis

1. **CI tidak boleh punya API key Gemini.** Semua test pakai `FakeProvider` atau mock. Kalau ingin smoke test terhadap API sungguhan, buat workflow terpisah yang dijalankan manual (`workflow_dispatch`) dengan secret, dan itu tidak memblokir merge.
2. Test yang gagal harus menggagalkan pipeline. Jangan ada `continue-on-error` pada langkah test.
3. Tes perilaku, bukan implementasi. Assert status code, isi response, dan state database — bukan berapa kali fungsi internal dipanggil (kecuali memang ingin membuktikan AI tidak dipanggil ulang).
4. Uji jalur gagal, bukan cuma happy path. Jalur gagal yang justru dilihat pewawancara.
5. Target cakupan yang jujur: fokus pada `services/` dan `api/`. Jangan mengejar angka dengan test kosong.

## Langkah

1. **Inspeksi** endpoint yang ada dan tentukan daftar perilaku yang perlu diuji.
2. **Rencana.** Plan mode: strategi isolasi database, daftar kasus uji per file, struktur pipeline CI. Tunggu persetujuan.
3. **Implementasi:** conftest dulu, lalu test per domain, baru workflow CI.
4. **Verifikasi:**
   ```bash
   make test
   pytest --cov=app --cov-report=term-missing -q
   ruff check . && ruff format --check .
   grep -rn "GEMINI_API_KEY\|api_key" .github/ tests/ || echo "OK: tidak ada kunci di CI/test"
   docker build -t interview-api:ci .
   ```
   Setelah push, tunjukkan hasil run CI. Buktikan pipeline bisa gagal: rusak satu test sengaja, jalankan, lalu perbaiki lagi.
5. **Commit:** `test(auth): cover registration and login flows`, `test(interviews): cover ownership and validation`, `test(evaluation): cover scoring and failure paths`, `ci: add lint, test and docker build pipeline`.

## Definition of Done

- [ ] `pytest` hijau dari database kosong tanpa setup manual
- [ ] Tidak ada satu pun test yang menyentuh jaringan
- [ ] CI hijau di GitHub, dan terbukti merah saat test gagal
- [ ] Image Docker berhasil dibuild di CI
- [ ] Waktu test suite masih wajar (di bawah ~60 detik)

$ARGUMENTS
