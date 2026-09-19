# 0002. Masa berlaku access token tanpa refresh token

- Status: Accepted
- Tanggal: 2026-09-19

## Konteks

- Spec §7 mensyaratkan JWT dengan masa berlaku dan semua rahasia dari environment.
  Kontrak API (spec §4) memuat `/auth/register`, `/auth/login`, dan `/auth/me` — tidak ada
  endpoint refresh.
- Token ditandatangani HS256 dengan `SECRET_KEY` yang wajib ada di environment, minimal 32
  karakter, tanpa nilai default di kode.
- Tidak ada penyimpanan token di sisi server. `jti` dibuat di setiap token tetapi belum
  dibaca siapa pun; itu kait untuk revocation list kalau nanti dibutuhkan.
- Aturan 6 CLAUDE.md: Redis adalah cache dan state sementara, bukan sumber kebenaran, dan
  aplikasi harus tetap melayani request saat Redis mati. Jadi Redis tidak boleh menjadi
  tempat otoritatif untuk status sesi.
- `is_active` dibaca ulang dari Postgres pada setiap request terautentikasi
  (`AuthService.get_active_user`), jadi akun yang dinonaktifkan ditolak pada request
  berikutnya dengan 403.
- Ini project portfolio yang belum dideploy dan belum punya pengguna sungguhan (spec §9).

## Keputusan

Access token berlaku 30 menit, diatur lewat `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30).
Tidak ada refresh token dan tidak ada revocation list. Setiap token membawa klaim
`typ: "access"` yang diverifikasi saat decode, sehingga refresh token yang mungkin
ditambahkan nanti tidak bisa dipakai sebagai access token. Ketiadaan refresh token dicatat
eksplisit sebagai keterbatasan di README, bukan disembunyikan.

## Alternatif yang dipertimbangkan

**Token berumur panjang (mis. 24 jam) tanpa refresh.** Paling nyaman untuk demo: tidak perlu
login ulang di tengah presentasi. Tidak dipilih karena tanpa mekanisme pencabutan, masa
berlaku adalah satu-satunya rem yang ada. Jendela 24 jam untuk token yang bocor sulit
dipertahankan di project yang nilai jualnya justru kualitas arsitektur.

**Access token 15 menit + refresh token dengan rotasi dan deteksi reuse.** Ini jawaban yang
benar untuk produksi. Tidak dipilih sekarang karena butuh tabel penyimpanan refresh token,
rotasi, deteksi pemakaian ulang, dan pencabutan — satu fitur tersendiri yang akan menghabiskan
Day 2 dan kemungkinan besar dikerjakan setengah jadi. Ditunda secara sadar, bukan terlewat.

**Session di sisi server dengan Redis.** Memberi pencabutan seketika. Tidak dipilih karena
melanggar aturan 6: autentikasi akan bergantung pada Redis, dan saat Redis mati pilihannya
tinggal fail closed (seluruh aplikasi tidak bisa dipakai) atau fail open (lubang keamanan).
Keduanya lebih buruk daripada token yang kedaluwarsa sendiri.

## Konsekuensi

Positif:

- Tidak ada state token yang perlu disimpan, dirotasi, atau dibersihkan.
- Autentikasi hanya menyentuh Postgres, jadi tetap jalan saat Redis mati.
- Masa berlaku adalah satu setting, mudah diperketat tanpa perubahan kode.
- Klaim `typ` membuat penambahan refresh token nanti tidak merusak keamanan yang sekarang.

Negatif:

- Pengguna harus login ulang setiap 30 menit. Untuk sesi latihan yang panjang ini
  mengganggu.
- Token yang bocor tetap sah sampai 30 menit dan tidak bisa dicabut satu per satu.
- Menonaktifkan akun tidak membatalkan tokennya; yang menolaknya adalah pembacaan ulang
  `is_active`, dan itu berarti satu query Postgres di setiap request terautentikasi.
- Satu-satunya tombol darurat global adalah mengganti `SECRET_KEY`, yang mematikan token
  semua orang sekaligus.

## Kapan keputusan ini perlu ditinjau ulang

- Aplikasi dideploy dan mulai dipakai orang lain.
- Ada klien mobile atau SPA yang butuh sesi lebih panjang dari 30 menit tanpa login ulang.
- Muncul kebutuhan "logout dari semua perangkat" atau pencabutan seketika setelah insiden.
- Penanganan penyalahgunaan perlu memutus satu token tertentu, bukan menonaktifkan akunnya.
