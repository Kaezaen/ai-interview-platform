---
description: Day 6 — Engineering polish. Review keamanan, penanganan error, logging terstruktur, konsistensi API, refactoring, README dan diagram arsitektur. Jalankan manual dengan /day-6.
disable-model-invocation: true
argument-hint: [area fokus opsional]
---

# Day 6 — Engineering Polish

## Kondisi repo saat ini

- Jumlah baris per file terbesar: !`find app -name "*.py" -exec wc -l {} + 2>/dev/null | sort -rn | head -12 || echo "(app/ belum ada)"`
- Status git: !`git status --short 2>/dev/null || true`
- Riwayat commit: !`git log --oneline -20 2>/dev/null || true`

## Scope

Hari ini **tidak menambah fitur**. Yang ada dirapikan sampai layak dibaca orang lain.

1. **Keamanan.** Jalankan `/security-review` pada diff kumulatif. Periksa juga secara manual:
   - tidak ada rahasia yang pernah masuk riwayat git (`git log -p | grep -i "api_key\|secret\|password ="`)
   - CORS tidak `allow_origins=["*"]` bersamaan dengan `allow_credentials=True`
   - batas ukuran payload pada endpoint jawaban
   - pesan error tidak membocorkan nama tabel, path file, atau versi library
2. **Penanganan error.** Satu exception handler terpusat, satu bentuk body error di seluruh API. Verifikasi 400/401/403/404/409/422/429/503 semua memakai bentuk yang sama.
3. **Observability.** Logging terstruktur JSON, middleware request-id yang diteruskan ke log dan header response, log khusus untuk kegagalan AI, database, dan autentikasi. Redaksi field sensitif diterapkan di formatter, bukan di tempat pemanggilan.
4. **Konsistensi API.** Penamaan, bentuk pagination, format timestamp (UTC ISO-8601), dan status code yang seragam. Perbaiki yang menyimpang.
5. **Database.** Cari query N+1 pada endpoint hasil; tambahkan `selectinload` seperlunya. Tinjau ulang indeks terhadap query yang benar-benar dijalankan.
6. **Refactor.** Jalankan `/code-review` pada diff. Pecah file atau fungsi yang membengkak. Hapus kode mati.
7. **Dokumentasi.** Tulis ulang `README.md` lengkap dan buat diagram arsitektur Mermaid di dalamnya. Catat keputusan penting lewat `/adr`.

## Langkah

1. Kerjakan berurutan dari nomor 1. Laporkan temuan tiap bagian sebelum lanjut.
2. Untuk setiap temuan, sebutkan tingkat keparahannya dan usulkan perbaikan. Jangan perbaiki hal berisiko tanpa persetujuan saya.
3. Setelah setiap perbaikan, jalankan `make test && make lint`.
4. Commit per kategori: `fix(security): ...`, `refactor(api): ...`, `feat(observability): ...`, `docs: ...`.

## Definition of Done

- [ ] `/security-review` tidak menyisakan temuan tingkat tinggi
- [ ] Semua error keluar dengan bentuk body yang sama
- [ ] Setiap baris log punya request id, dan tidak ada rahasia yang ter-log
- [ ] README bisa diikuti orang yang belum pernah melihat project ini sampai berhasil menjalankan
- [ ] Diagram arsitektur cocok dengan kode yang benar-benar ada
- [ ] Test tetap hijau

## Perhatian

README tidak boleh mengklaim apa yang tidak ada. Tidak ada angka performa palsu, tidak ada
klaim "production deployment" kalau belum dideploy, tidak ada metrik pengguna fiktif.
Bagian "Keterbatasan yang diketahui" justru menaikkan kredibilitas, bukan menurunkannya.

$ARGUMENTS
