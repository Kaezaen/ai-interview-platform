# Project Spec — AI Interview Platform

Dokumen referensi. Tidak dimuat otomatis ke setiap sesi Claude Code; dibaca saat butuh detail.
Aturan harian ada di `CLAUDE.md`, prosedur per hari ada di `.claude/skills/day-*/`.

---

## 1. Masalah dan posisi produk

Orang yang menyiapkan diri untuk interview teknis kesulitan mendapat latihan yang relevan
dengan posisi dan level yang mereka incar, dan kesulitan mendapat umpan balik terstruktur
atas jawaban mereka.

Platform ini: **AI-powered interview preparation and evaluation platform dengan arsitektur
backend yang production-oriented.**

Bukan: "website interview sederhana" atau "CRUD dengan chatbot". Nilai jual project ini ada
pada arsitektur, validasi output AI, penanganan kegagalan, dan testing — bukan pada jumlah fitur.

---

## 2. Alur inti

```
Register / Login
   ↓
Buat interview (position, level, skills)
   ↓
Generate pertanyaan  →  AIProvider  →  validasi Pydantic  →  simpan
   ↓
User menjawab pertanyaan
   ↓
Evaluasi jawaban     →  AIProvider  →  validasi Pydantic  →  skoring di backend  →  simpan
   ↓
Hasil interview: skor keseluruhan, skor per skill, kekuatan, kelemahan, rekomendasi
```

Arsitektur runtime:

```
Client → FastAPI ─┬─→ PostgreSQL   (sumber kebenaran)
                  ├─→ Redis        (cache, rate limit, kunci idempotensi — opsional)
                  └─→ AIProvider → Gemini | Fake
```

---

## 3. Domain model

Entitas dan relasi (kolom pasti ditentukan saat Day 2, ini kontrak konseptualnya):

```
users
  └── interviews          (satu user banyak interview)
        └── questions     (satu interview banyak pertanyaan)
              └── answers (satu pertanyaan satu jawaban per user)
                    └── evaluations (satu jawaban satu evaluasi)
```

| Tabel | Field penting | Catatan |
|---|---|---|
| `users` | `email` (unik, indeks), `password_hash`, `is_active` | Tidak pernah dikembalikan lewat API dalam bentuk apa pun selain id, email, timestamp |
| `interviews` | `user_id` FK, `position`, `level`, `skills`, `status` | `status`: `created` → `questions_generated` → `in_progress` → `completed` |
| `questions` | `interview_id` FK, `content`, `category`, `skill`, `difficulty`, `prompt_version`, `model_name` | `prompt_version` + `model_name` untuk keterlacakan |
| `answers` | `question_id` FK, `content`, `submitted_at` | Unique constraint pada `question_id` |
| `evaluations` | `answer_id` FK unik, sub-skor, `overall_score`, `weights`, `strengths`, `weaknesses`, `recommendations` | `overall_score` dihitung backend, bukan oleh LLM |

Semua tabel: primary key UUID, `created_at`/`updated_at` timezone-aware, foreign key dengan
perilaku ON DELETE yang eksplisit, indeks pada kolom yang benar-benar dipakai untuk filter.

Catatan `interview_sessions`: entitas terpisah untuk ini baru masuk akal kalau ada state
sementara yang tidak layak masuk Postgres (mis. progres voice interview). Untuk cakupan saat
ini, `interviews.status` sudah cukup. Jangan membuat tabel yang tidak punya pembaca.

---

## 4. Kontrak API

Semua endpoint kecuali `/health` dan `/auth/*` butuh `Authorization: Bearer <token>`.

| Method | Path | Keterangan |
|---|---|---|
| POST | `/auth/register` | 201; 409 kalau email sudah dipakai |
| POST | `/auth/login` | 200 + access token; 401 kalau kredensial salah |
| GET | `/auth/me` | Profil user saat ini |
| POST | `/interviews` | Buat sesi interview |
| GET | `/interviews` | Milik user saat ini, paginasi |
| GET | `/interviews/{id}` | 404 kalau bukan milik user (jangan 403) |
| POST | `/interviews/{id}/questions` | Generate pertanyaan; idempoten |
| GET | `/questions/{id}` | Satu pertanyaan |
| POST | `/questions/{id}/answer` | Kirim jawaban |
| POST | `/answers/{id}/evaluate` | Evaluasi; idempoten |
| GET | `/interviews/{id}/result` | Hasil teragregasi |

Contoh request pembuatan interview:

```json
{
  "position": "Software Engineer",
  "level": "Junior",
  "skills": ["Python", "FastAPI", "PostgreSQL"]
}
```

**Catatan desain:** memisahkan `POST /answers/{id}/evaluate` dari submit jawaban membuat API
lebih chatty dan memaparkan state internal ke client. Alternatif yang lebih rapi adalah
mengevaluasi otomatis saat jawaban dikirim, dan menyisakan endpoint evaluate hanya untuk
percobaan ulang. Putuskan ini di Day 4 dan catat alasannya lewat `/adr`.

**Bentuk error seragam** untuk semua status non-2xx:

```json
{
  "error": {
    "code": "INTERVIEW_NOT_FOUND",
    "message": "Interview tidak ditemukan",
    "request_id": "01H..."
  }
}
```

---

## 5. Kontrak AI

Interface yang dikenal business logic:

```python
class AIProvider(ABC):
    async def generate_questions(self, spec: QuestionSpec) -> GeneratedQuestionSet: ...
    async def evaluate_answer(self, req: EvaluationRequest) -> AnswerEvaluation: ...
```

Implementasi: `GeminiProvider` (produksi) dan `FakeProvider` (development dan test,
deterministik, tanpa jaringan). Dipilih lewat setting `AI_PROVIDER`.

Bentuk output generate pertanyaan:

```json
{
  "questions": [
    {
      "content": "...",
      "category": "technical",
      "skill": "FastAPI",
      "difficulty": "medium"
    }
  ]
}
```

Bentuk output evaluasi (perhatikan: tanpa `overall_score` — itu dihitung backend):

```json
{
  "correctness": 85,
  "relevance": 90,
  "clarity": 78,
  "technical_depth": 80,
  "strengths": ["Memahami dependency injection"],
  "weaknesses": ["Belum menjelaskan lifecycle dengan jelas"],
  "recommendations": ["Pelajari dependency scope", "Tinjau lifecycle dependency FastAPI"]
}
```

Aturan validasi yang tidak bisa ditawar:

1. Parse sebagai JSON, validasi dengan Pydantic, lalu validasi semantik: jumlah item sesuai
   permintaan, `skill` termasuk skill yang diminta, enum sah, sub-skor dalam rentang 0–100,
   tidak ada duplikat.
2. Gagal validasi → maksimal satu kali coba ulang dengan pesan error dikembalikan ke model →
   masih gagal → `AIInvalidOutputError` → HTTP 503. Output cacat tidak pernah masuk database.
3. `overall_score` = rata-rata berbobot dari sub-skor, dihitung di Python. Bobot disimpan
   bersama evaluasi supaya skor lama tetap bisa dijelaskan setelah bobot berubah.
4. Timeout eksplisit di setiap panggilan. Retry hanya untuk error transien (timeout, 5xx,
   rate limit), tidak pernah untuk error validasi konten.

---

## 6. Peran Redis

Boleh dipakai untuk: rate limiting per user pada endpoint AI, kunci idempotensi berumur
pendek saat evaluasi, cache hasil interview yang sering dibaca.

Tidak boleh dipakai sebagai: sumber kebenaran untuk apa pun.

Aturan: aplikasi harus tetap melayani request saat Redis mati. Kegagalan Redis hanya boleh
berarti cache terlewat atau rate limit terlewat, tidak pernah berarti request gagal.

---

## 7. Keamanan minimum

Hashing password (argon2 atau bcrypt) · JWT dengan masa berlaku · semua rahasia dari
environment · validasi input di boundary · pengecekan kepemilikan di setiap endpoint yang
menyentuh resource milik user · rate limiting · error yang tidak membocorkan detail internal ·
`.env.example` masuk git, `.env` tidak pernah.

---

## 8. Ringkasan roadmap

| Hari | Fokus | Definition of Done |
|---|---|---|
| 1 | Foundation | Compose jalan, `/health` 200, Swagger terbuka, lint bersih |
| 2 | Database + Auth | Migration jalan, register/login/JWT jalan, isolasi kepemilikan terbukti |
| 3 | Integrasi AI | Abstraksi provider, output tervalidasi tersimpan, alur jalan dengan provider palsu |
| 4 | Evaluasi + Redis | Alur jawab→evaluasi→hasil lengkap, idempoten, tahan Redis mati |
| 5 | Testing + CI | pytest hijau tanpa jaringan, CI hijau dan terbukti bisa merah |
| 6 | Polish | Keamanan, error seragam, logging, README, diagram |
| 7 | Portfolio | Clone segar jalan, screenshot, catatan interview |

Detail langkah per hari ada di `.claude/skills/day-*/SKILL.md`.

---

## 9. Bukan cakupan saat ini

Voice interview, STT/TTS, LiveKit, Vertex AI, MinIO, background job queue, microservices,
deployment ke cloud. Semua ini fase berikutnya. Memasukkannya sekarang akan mengorbankan
kualitas inti, dan stack panjang dengan implementasi dangkal justru merugikan saat interview.

Prinsip: sedikit teknologi dengan implementasi kuat lebih baik daripada banyak teknologi
dengan arsitektur rapuh.
