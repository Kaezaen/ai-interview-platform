# Cara memasang dan memakai paket ini

## Apa isinya

```
CLAUDE.md                      ← dimuat otomatis di SETIAP sesi. Sengaja dibuat pendek.
docs/PROJECT_SPEC.md           ← spesifikasi lengkap. Dibaca hanya saat dibutuhkan.
.claude/settings.json          ← izin tool (kurangi prompt konfirmasi berulang)
.claude/rules/*.md             ← aturan yang aktif hanya saat menyentuh file tertentu
.claude/skills/day-1..day-7/   ← prosedur per hari, dipanggil dengan /day-1 … /day-7
.claude/skills/status/         ← /status
.claude/skills/mentor/         ← /mentor <topik>
.claude/skills/adr/            ← /adr <judul keputusan>
.claude/skills/ship/           ← /ship
```

## Pemasangan

```bash
mkdir ai-interview-platform && cd ai-interview-platform
git init
# salin CLAUDE.md, SETUP.md, docs/, dan .claude/ ke sini
claude
```

Di dalam sesi, jalankan `/memory` untuk memastikan `CLAUDE.md` terbaca, lalu `/context`
untuk melihat berapa besar konteks yang terpakai sebelum mulai bekerja.

Commit `.claude/` ke git. Ini bagian dari repository dan menunjukkan cara kerja yang rapi.

## Ritme harian

```
sesi baru → /status → /day-N → (plan mode: review rencana, setujui) → implementasi
          → verifikasi → /ship → /clear
```

Aturan praktis:

- **Satu hari roadmap = satu sesi.** Jalankan `/clear` sebelum pindah hari. Konteks yang
  menumpuk dari hari kemarin menurunkan kualitas jawaban di hari berikutnya, dan `/status`
  sudah cukup untuk memulihkan posisi.
- **Selalu lewat plan mode untuk pekerjaan besar.** Tekan Shift+Tab sampai masuk plan mode,
  atau ketik `/plan`. Baca rencananya. Menolak rencana yang salah jauh lebih murah daripada
  membongkar 15 file.
- **Pakai `/compact` saat konteks penuh di tengah pekerjaan**, bukan `/clear` — `/clear`
  menghapus semuanya.
- **`/mentor` dipanggil saat butuh**, tidak otomatis. Ini sengaja: penjelasan panjang di
  setiap perubahan memperlambat pekerjaan dan menghabiskan konteks.
- **`/adr` setiap kali ambil keputusan yang punya alternatif nyata.** File-file ini nanti
  jadi bahan jawaban interview yang paling kuat, karena isinya alasan, bukan kode.

## Kenapa CLAUDE.md dibuat sependek ini

`CLAUDE.md` dimuat ke konteks pada setiap sesi, apa pun yang sedang dikerjakan. Semakin
panjang isinya, semakin turun kepatuhan terhadap instruksi — termasuk instruksi penting
seperti "jangan commit `.env`". Dokumentasi resmi Claude Code sendiri menyarankan menjaga
file ini tetap ringkas, dan `/doctor` akan menawarkan memangkasnya kalau sudah membengkak.

Karena itu isinya dipecah:

| Jenis isi | Tempatnya | Kapan dimuat |
|---|---|---|
| Aturan yang selalu berlaku | `CLAUDE.md` | setiap sesi |
| Spesifikasi dan kontrak | `docs/PROJECT_SPEC.md` | saat dibaca |
| Aturan khusus jenis file | `.claude/rules/*.md` | saat menyentuh file yang cocok |
| Prosedur multi-langkah | `.claude/skills/*/SKILL.md` | saat dipanggil |

Catatan: jangan memindahkan spec ke `CLAUDE.md` lewat sintaks import `@docs/PROJECT_SPEC.md`.
Import tetap dimuat penuh saat startup, jadi cara itu merapikan tampilan file tanpa menghemat
konteks sama sekali.

## Menyesuaikan

Skill hanyalah file markdown. Kalau `/day-3` terasa terlalu besar untuk satu sesi, pecah jadi
`/day-3a` dan `/day-3b` dengan membuat direktori baru di `.claude/skills/`. Claude Code
memantau direktori skill dan memuat perubahan tanpa perlu restart.

Kalau ada instruksi yang harus kamu ulangi lebih dari dua kali ke Claude, itu tandanya
instruksi tersebut seharusnya masuk ke `CLAUDE.md` atau ke rules — bukan diketik ulang.

## Sanity check di hari pertama

```
/status            → harus melaporkan repo kosong, bukan mengarang progres
/day-1             → harus masuk plan mode dan bertanya, bukan langsung menulis 20 file
```

Kalau Claude langsung membuat file tanpa menunjukkan rencana, hentikan dan ingatkan.
Perilaku itu yang paling sering merusak project multi-hari.
