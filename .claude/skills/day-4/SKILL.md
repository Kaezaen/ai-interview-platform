---
description: Day 4 — Evaluasi jawaban dan Redis. Submit answer, evaluasi AI berbasis rubrik, skoring deterministik, agregasi hasil, rate limiting dan caching. Jalankan manual dengan /day-4.
disable-model-invocation: true
argument-hint: [catatan atau penyesuaian opsional]
---

# Day 4 — Evaluation + Redis

## Kondisi repo saat ini

- AI layer: !`find app/services/ai -type f 2>/dev/null || echo "(belum ada — Day 3 belum selesai)"`
- Model: !`find app/models -type f -name "*.py" 2>/dev/null || echo "(app/models belum ada)"`
- Migration: !`ls alembic/versions 2>/dev/null | tail -5 || echo "(belum ada migration)"`

## Prasyarat

Generate pertanyaan dari Day 3 harus berfungsi dengan `AI_PROVIDER=fake`.

## Scope

**Dikerjakan hari ini:**
- Model `Answer` dan `Evaluation` + migration. Satu jawaban per pertanyaan per user (unique constraint), satu evaluasi per jawaban.
- `POST /questions/{id}/answer` — simpan jawaban, cek kepemilikan lewat rantai question → interview → user.
- `POST /answers/{id}/evaluate` — panggil AI, validasi, simpan evaluasi.
- `GET /interviews/{id}/result` — agregasi: skor keseluruhan, skor per skill, ringkasan kekuatan/kelemahan, rekomendasi, progres jumlah pertanyaan terjawab.
- Tambahkan `evaluate_answer()` ke interface `AIProvider` dan implementasikan di kedua provider.
- Redis: rate limiting pada endpoint AI, kunci idempotensi saat evaluasi, cache untuk `GET /interviews/{id}/result`.

## Aturan kritis

1. **Skor agregat dihitung di Python, bukan oleh LLM.** AI mengembalikan sub-skor (correctness, relevance, clarity, technical_depth) berikut alasannya; backend menghitung rata-rata berbobot dan menyimpan bobot yang dipakai. Deterministik, bisa diuji, bisa dijelaskan ke pewawancara.
2. Validasi rentang setiap sub-skor (0–100). Nilai di luar rentang = output tidak valid, bukan untuk di-clamp diam-diam.
3. **Idempotensi.** Evaluasi ulang jawaban yang sudah dievaluasi harus mengembalikan evaluasi yang tersimpan, bukan memanggil AI lagi. Pakai kunci Redis berumur pendek untuk mencegah dua request bersamaan memanggil AI dua kali, dan unique constraint di database sebagai penjaga terakhir.
4. **Redis boleh mati.** Bungkus setiap operasi Redis sehingga kegagalan koneksi hanya melewatkan cache atau melewatkan rate limit, tidak menggagalkan request. Tulis ini sebagai keputusan sadar.
5. Invalidasi cache hasil saat ada evaluasi baru. Cache basi di halaman skor lebih buruk daripada tidak ada cache.
6. Rate limit per user, bukan per IP — user sudah terautentikasi di endpoint ini.

## Langkah

1. **Inspeksi** model dan AI service yang ada.
2. **Rencana.** Plan mode: skema rubrik, bobot skoring, kunci Redis beserta TTL-nya, dan perilaku ketika Redis mati. Tunggu persetujuan.
3. **Implementasi** urut: model + migration → schema evaluasi → provider → service → Redis client → router.
4. **Verifikasi:**
   ```bash
   # alur lengkap
   curl -s -X POST localhost:8000/questions/<qid>/answer -H "authorization: Bearer <t>" \
     -H 'content-type: application/json' -d '{"content":"..."}'
   curl -s -X POST localhost:8000/answers/<aid>/evaluate -H "authorization: Bearer <t>"
   curl -s -X POST localhost:8000/answers/<aid>/evaluate -H "authorization: Bearer <t>"  # hasil identik
   curl -s localhost:8000/interviews/<id>/result -H "authorization: Bearer <t>"
   # buktikan Redis opsional
   docker compose stop redis
   curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/interviews/<id>/result   # harus tetap 200
   docker compose start redis
   ```
5. **Commit:** `feat(answers): add answer submission`, `feat(evaluation): add rubric-based AI evaluation`, `feat(results): aggregate interview results`, `feat(cache): add redis rate limiting and result cache`.

## Definition of Done

- [ ] Alur jawab → evaluasi → hasil berfungsi ujung ke ujung dengan provider palsu
- [ ] Evaluasi kedua tidak memanggil AI lagi (buktikan lewat log atau counter)
- [ ] Redis dimatikan, API tetap melayani request
- [ ] Skor keseluruhan bisa dihitung ulang secara manual dari sub-skor yang tersimpan
- [ ] Rate limit mengembalikan 429 dengan header `Retry-After`

$ARGUMENTS
