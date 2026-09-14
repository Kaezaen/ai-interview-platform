---
description: Day 3 — Integrasi AI. Abstraksi AIProvider, Gemini provider, FakeProvider, prompt terversi, structured output, dan validasi sebelum persist. Jalankan manual dengan /day-3.
disable-model-invocation: true
argument-hint: [catatan atau penyesuaian opsional]
---

# Day 3 — AI Integration

## Kondisi repo saat ini

- Services: !`find app/services -type f 2>/dev/null | head -30 || echo "(app/services belum ada)"`
- Model: !`find app/models -type f 2>/dev/null | head -20 || echo "(app/models belum ada)"`
- Commit terakhir: !`git log --oneline -8 2>/dev/null || echo "(belum ada commit)"`

## Prasyarat

Auth dan `POST /interviews` dari Day 2 harus berfungsi.

## Scope

**Dikerjakan hari ini:**
- `app/services/ai/base.py`: interface `AIProvider` (abstract) dengan method `generate_questions(spec) -> GeneratedQuestionSet`. Signature memakai tipe domain kita sendiri, bukan tipe dari SDK Gemini.
- `app/services/ai/schemas.py`: skema Pydantic untuk output AI, terpisah dari skema API dan model DB.
- `app/services/ai/gemini_provider.py`: satu-satunya file yang boleh mengimpor SDK Gemini. Pakai JSON/response schema mode, timeout eksplisit, retry terbatas hanya untuk error transien.
- `app/services/ai/fake_provider.py`: provider deterministik tanpa jaringan untuk development dan test, dipilih lewat setting `AI_PROVIDER=fake`.
- `app/services/ai/prompts/`: template prompt sebagai file terpisah dan berversi (mis. `question_generation.v1.md`).
- Model `Question` + migration
- `POST /interviews/{id}/questions`: generate, validasi, simpan, kembalikan. Idempoten — memanggil dua kali pada interview yang sudah punya pertanyaan tidak menggandakan data.
- Hirarki error: `AIError` → `AIUnavailableError`, `AIInvalidOutputError`, dipetakan ke 503 di handler terpusat.

**JANGAN dikerjakan hari ini:** evaluasi jawaban, Redis, caching.

## Aturan kritis

1. Output AI yang gagal validasi Pydantic **tidak pernah** disimpan. Alur: parse → validasi → (opsional) satu kali retry dengan pesan error dikembalikan ke model → kalau tetap gagal, lempar `AIInvalidOutputError`.
2. Validasi bukan cuma bentuk JSON. Cek isinya juga: jumlah pertanyaan sesuai permintaan, `skill` termasuk skill yang diminta, `difficulty` termasuk enum yang sah, tidak ada pertanyaan duplikat.
3. Setiap panggilan AI punya timeout. Tanpa timeout, satu request yang menggantung menahan worker.
4. Log: provider, nama model, versi prompt, latensi, hasil validasi. Jangan log prompt atau response mentah secara utuh.
5. Simpan `prompt_version` dan `model_name` di baris `questions`. Ini yang membuat hasil bisa ditelusuri ketika prompt berubah.

## Langkah

1. **Inspeksi** model dan service yang ada. Baca `docs/PROJECT_SPEC.md` bagian kontrak AI.
2. **Rencana.** Plan mode: tunjukkan interface, skema output, dan strategi penanganan kegagalan. Tunggu persetujuan.
3. **Implementasi** urut: schemas → base → fake_provider → gemini_provider → service → router → migration.
4. **Verifikasi:**
   ```bash
   AI_PROVIDER=fake docker compose up -d && make migrate
   curl -s -X POST localhost:8000/interviews/<id>/questions -H "authorization: Bearer <token>"
   docker compose exec postgres psql -U postgres -d interview \
     -c "select id, skill, difficulty, prompt_version from questions limit 10;"
   grep -rn "google.generativeai\|google.genai" app/ --include=*.py
   ```
   Panggil endpoint generate dua kali dan tunjukkan jumlah baris tidak bertambah. Lalu satu smoke test dengan `AI_PROVIDER=gemini` dan API key sungguhan.
5. **Commit:** `feat(ai): add provider abstraction`, `feat(ai): add gemini provider`, `feat(ai): add fake provider for local and test`, `feat(questions): generate and persist validated questions`.

## Definition of Done

- [ ] Hasil grep membuktikan SDK Gemini hanya diimpor di `gemini_provider.py`
- [ ] `AI_PROVIDER=fake` membuat seluruh alur berjalan tanpa jaringan
- [ ] Output cacat dari AI menghasilkan 503 yang rapi, bukan 500 dengan stack trace
- [ ] Memanggil endpoint generate dua kali tidak menggandakan pertanyaan
- [ ] `prompt_version` tersimpan di setiap baris pertanyaan

$ARGUMENTS
