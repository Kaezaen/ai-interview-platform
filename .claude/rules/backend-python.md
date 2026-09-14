---
paths: app/**/*.py
---

# Aturan kode backend

- Arah dependensi: router → service → repository → database. Tidak boleh dibalik.
- Query SQLAlchemy hanya di `app/repositories/`. Router dan service tidak menyusun query sendiri.
- Router tidak memuat business logic. Tugasnya: validasi input, dependency, panggil service, mapping ke response schema.
- Service tidak mengimpor `fastapi` selain untuk tipe yang benar-benar netral. Tidak melempar `HTTPException`; lempar exception domain dan biarkan handler terpusat yang memetakannya.
- SDK penyedia AI hanya boleh diimpor di `app/services/ai/<provider>_provider.py`.
- Semua I/O async. Jangan memanggil driver sinkron di dalam fungsi async.
- Type hints wajib di fungsi publik. Hindari `Any` kecuali disertai komentar alasannya.
- Setiap panggilan jaringan keluar punya timeout eksplisit.
- Jangan menangkap `Exception` secara telanjang kecuali di boundary paling luar, dan di sana wajib di-log.
- Jangan pernah memasukkan rahasia, token, atau isi jawaban user secara utuh ke dalam log.
