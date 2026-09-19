# 0001. Penyimpanan skills pada interview

- Status: Accepted
- Tanggal: 2026-09-19

## Konteks

- `interviews` menyimpan `position`, `level`, dan `skills` (spec §3). Skills adalah masukan
  untuk prompt generate pertanyaan di Day 3, dan nilainya dicocokkan dengan `questions.skill`.
- `questions.skill` di spec §3 adalah kolom string bebas, bukan foreign key ke katalog apa pun.
- Kontrak API (spec §4) memuat tiga endpoint interview: create, list milik user dengan
  paginasi, dan get by id. Tidak ada satu pun yang memfilter atau mengagregasi per skill.
- Contoh payload di spec: `"skills": ["Python", "FastAPI", "PostgreSQL"]` — daftar label
  bebas tanpa atribut tambahan.
- Spec §3 mensyaratkan indeks hanya untuk kolom yang benar-benar dipakai memfilter.
- Database PostgreSQL 16, dan test Day 5 berjalan di Postgres sungguhan, jadi tipe khusus
  Postgres tidak menambah beban infrastruktur.

## Keputusan

Menyimpan skills sebagai kolom `skills text[] NOT NULL` pada tabel `interviews`, dijaga
constraint `ck_interviews_skills_len` (`cardinality(skills) BETWEEN 1 AND 10`). Normalisasi
dilakukan di boundary Pydantic: whitespace dirapikan, elemen kosong dibuang, duplikat
dihapus case-insensitive, tiap elemen maksimal 60 karakter. Tidak ada indeks GIN.

## Alternatif yang dipertimbangkan

**Tabel relasi (`skills` + `interview_skills`).** Memberi integritas referensial, penamaan
kanonik, dan filter efisien. Tidak dipilih karena ketiga keuntungan itu belum punya pembaca:
tidak ada endpoint yang memfilter per skill, sehingga yang didapat sekarang hanya dua tabel
tambahan dan dua JOIN di setiap pembacaan. Integritasnya pun tetap bocor di tempat lain —
`questions.skill` di spec tetap string bebas. Katalog skill juga menyiratkan kurasi
kosakata, dan tidak ada yang mengurasinya.

**Kolom JSONB.** Sama fleksibelnya dan lebih mudah berkembang menjadi objek
`{name, weight}`. Tidak dipilih karena database tidak menegakkan tipe elemen — angka,
`null`, atau objek bersarang sama-sama sah masuk — sedangkan `text[]` menolaknya. Untuk
daftar string murni, JSONB hanya menambah verbositas query tanpa memberi apa pun hari ini.

**Satu kolom teks dengan pemisah koma.** Tidak dipilih: memindahkan parsing ke aplikasi dan
membuat skill yang mengandung koma tidak bisa direpresentasikan.

## Konsekuensi

Positif:

- Satu baris, satu tulisan, tanpa JOIN untuk membaca interview beserta skill-nya.
- Tipe elemen dan jumlah elemen ditegakkan database, bukan hanya oleh aplikasi.
- Indeks GIN bisa ditambahkan kapan saja tanpa migration data.

Negatif:

- Tidak ada integritas referensial. "Postgres" dan "PostgreSQL" adalah dua string berbeda,
  dan tidak ada yang mencegahnya.
- Statistik agregat per skill akan berisik karena penamaan tidak kanonik. Ini baru terasa
  saat ada fitur yang menghitungnya.
- Mengganti nama satu skill secara global berarti UPDATE atas banyak baris, bukan satu baris
  di tabel katalog.
- Tanpa indeks GIN, filter per skill akan sequential scan sampai indeksnya dibuat.
- `text[]` khusus PostgreSQL, jadi test tidak bisa pindah ke SQLite.

## Kapan keputusan ini perlu ditinjau ulang

- Muncul endpoint yang memfilter atau mengagregasi interview berdasarkan skill — langkah
  pertama menambah indeks GIN, bukan langsung normalisasi.
- Skill perlu membawa atribut (bobot, target proficiency, kategori). Saat itu JSONB atau
  tabel relasi menjadi pilihan yang benar.
- Ada katalog skill terkurasi dengan autocomplete atau validasi terhadap daftar tetap.
- Penamaan yang tidak konsisten mulai merusak kualitas pertanyaan yang dihasilkan AI.
