---
description: Day 7 — Portfolio readiness. README final, screenshot, demo data, halaman portfolio, persiapan interview, dan pembersihan repository. Jalankan manual dengan /day-7.
disable-model-invocation: true
argument-hint: [catatan opsional]
---

# Day 7 — Portfolio Readiness

## Kondisi repo saat ini

- Statistik commit: !`git log --oneline 2>/dev/null | wc -l || echo 0`
- Dokumen: !`ls docs 2>/dev/null || echo "(docs/ belum ada)"`
- File terlacak paling besar: !`git ls-files 2>/dev/null | xargs -I{} du -k {} 2>/dev/null | sort -rn | head -5 || true`

## Scope

1. **Uji dari nol.** Clone repository ke direktori baru, ikuti README apa adanya, dan catat setiap langkah yang tidak jalan. Ini pengujian paling jujur terhadap dokumentasi.
   ```bash
   cd /tmp && rm -rf smoke && git clone <url> smoke && cd smoke
   cp .env.example .env && docker compose up -d && make migrate
   curl -s localhost:8000/health
   ```
2. **Skrip demo data.** Buat `scripts/seed_demo.py` yang menyiapkan satu user contoh, satu interview, pertanyaan dan evaluasi memakai `FakeProvider`. Tandai jelas sebagai data demo, bukan data pengguna sungguhan.
3. **Screenshot.** Kumpulkan di `docs/images/`: Swagger, satu response evaluasi, diagram skema database, pipeline CI yang hijau, `docker compose ps`. Sisipkan di README.
4. **README final.** Urutan: judul + satu kalimat deskripsi, masalah yang diselesaikan, arsitektur (diagram), tech stack beserta alasannya, fitur, cara menjalankan, cara test, keputusan engineering, keterbatasan yang diketahui, rencana lanjutan.
5. **Halaman portfolio** (`docs/PORTFOLIO.md`): teks siap salin untuk website pribadi — problem, solusi, arsitektur, keputusan engineering, tantangan dan cara mengatasinya, link repo. Tekankan engineering, bukan tampilan.
6. **Persiapan interview** (`docs/INTERVIEW_NOTES.md`): jawaban ringkas untuk pertanyaan yang pasti muncul —
   - Kenapa abstraksi AI provider, dan apa yang berubah kalau pindah dari Gemini?
   - Bagaimana menangani halusinasi dan output tidak valid dari LLM?
   - Kenapa skor agregat dihitung di backend?
   - Apa yang terjadi kalau Gemini down? Kalau Redis down? Kalau Postgres down?
   - Di mana bottleneck-nya, dan apa langkah pertama untuk menskalakan?
   - Bagaimana password dan API key dilindungi?
   - Apa yang akan kamu ubah kalau boleh menulis ulang?
   Jawaban harus merujuk file dan baris kode yang nyata.
7. **Pembersihan repo.** Deskripsi dan topics GitHub, LICENSE, hapus branch mati, pastikan `main` hijau, tidak ada file sampah atau `.env` yang ikut ter-commit.

## Definition of Done

- [ ] Clone segar berhasil jalan hanya dengan mengikuti README
- [ ] Screenshot tampil di README
- [ ] `docs/PORTFOLIO.md` dan `docs/INTERVIEW_NOTES.md` ada dan akurat
- [ ] Setiap klaim di README bisa ditunjuk ke kode yang nyata
- [ ] Riwayat commit terbaca sebagai perjalanan engineering, bukan satu dump

## Perhatian

Sebelum selesai, baca ulang README dan tandai setiap kalimat yang tidak bisa kamu buktikan
dari kode. Laporkan ke saya. Klaim yang tidak terbukti adalah risiko terbesar di interview.

$ARGUMENTS
