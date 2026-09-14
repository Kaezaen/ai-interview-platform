---
paths: alembic/**/*.py
---

# Aturan migration

- Migration yang sudah pernah dijalankan di luar mesin lokal tidak boleh diedit. Buat migration baru.
- Selalu baca hasil autogenerate sebelum menerimanya. Autogenerate kerap melewatkan perubahan tipe, rename, dan constraint.
- Setiap migration wajib punya `downgrade()` yang benar-benar berfungsi.
- Perubahan data dan perubahan schema dipisah ke migration berbeda.
- Menambah kolom NOT NULL ke tabel berisi data butuh tiga langkah: tambah nullable, isi datanya, baru ubah jadi NOT NULL.
- Beri nama constraint dan indeks secara eksplisit supaya bisa direferensikan di migration berikutnya.
