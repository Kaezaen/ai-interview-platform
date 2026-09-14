---
description: Tulis Architecture Decision Record ke docs/adr/ untuk keputusan teknis penting. Jalankan manual dengan /adr <judul keputusan>.
disable-model-invocation: true
argument-hint: <judul keputusan>
---

# Architecture Decision Record

ADR yang sudah ada: !`ls docs/adr 2>/dev/null || echo "(belum ada)"`

Buat ADR untuk: **$ARGUMENTS**

1. Tentukan nomor urut berikutnya (`0001`, `0002`, …).
2. Tulis ke `docs/adr/NNNN-judul-dalam-kebab-case.md` dengan struktur:

```markdown
# NNNN. <Judul>

- Status: Accepted
- Tanggal: <YYYY-MM-DD>

## Konteks
Situasi dan kendala yang memaksa keputusan ini diambil. Fakta, bukan opini.

## Keputusan
Apa yang diputuskan, dalam kalimat aktif.

## Alternatif yang dipertimbangkan
Minimal dua, masing-masing dengan alasan kenapa tidak dipilih.

## Konsekuensi
Positif dan negatif. Bagian negatif wajib diisi.

## Kapan keputusan ini perlu ditinjau ulang
Kondisi konkret yang membuat keputusan ini tidak lagi tepat.
```

3. Kalau ada ADR lama yang digantikan, ubah statusnya menjadi `Superseded by NNNN`.
4. Commit dengan `docs(adr): record decision on <topik>`.

Tetap padat — satu halaman. ADR mencatat alasan, bukan mengulang dokumentasi.
