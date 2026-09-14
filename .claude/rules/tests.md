---
paths: tests/**/*.py
---

# Aturan test

- Test tidak boleh menyentuh jaringan. Penyedia AI selalu di-override ke `FakeProvider` atau mock.
- Setiap test berdiri sendiri: tidak bergantung pada urutan eksekusi maupun sisa data dari test lain.
- Uji perilaku lewat API: status code, isi response, dan state database. Bukan detail implementasi internal.
- Setiap endpoint minimal punya satu test jalur gagal, bukan hanya happy path.
- Test otorisasi wajib: user lain tidak boleh mengakses resource yang bukan miliknya.
- Nama test menjelaskan perilaku: `test_register_rejects_duplicate_email`, bukan `test_register_2`.
- Jangan menaikkan angka coverage dengan test tanpa assertion.
