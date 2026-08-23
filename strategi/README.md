# Benteng Terakhir - Game Strategi (Pygame)

Game strategi sederhana bertema penempatan prajurit (mirip tower
defense). Pemain menempatkan 4 jenis prajurit di grid pertahanan
menggunakan kredit terbatas, lalu bertahan dari gelombang musuh.
Musuh yang berhasil dikalahkan menambah kredit untuk gelombang
berikutnya.

## Cara menjalankan

```
pip install -r requirements.txt
python generate_placeholder_assets.py   # sekali saja, membuat ikon placeholder
python main.py
```

## Cara main

1. **Opening** - layar cerita pembuka, klik "Mulai Permainan".
2. **Fase Penempatan** - pilih jenis prajurit di panel bawah (Pemanah,
   Pelindung, Penyerang, Penyihir), lalu klik kotak pada area terang
   (zona pertahanan) di sisi kiri grid untuk menempatkannya. Setiap
   prajurit mengurangi kredit sesuai harganya. Saat siap, klik tombol
   **"Mulai Gelombang"** di kanan atas.
3. **Fase Pertarungan** - musuh muncul dari kanan dan berjalan ke kiri
   menuju benteng. Prajurit yang berada dalam jangkauan otomatis
   menyerang. Pelindung memiliki HP besar dan bisa menahan musuh di
   jalurnya (musuh berhenti & menyerang balik saat berhadapan
   langsung dengan prajurit).
4. Musuh yang mati memberi **kredit** (nilai `reward` di
   `config/waves.json`) yang bisa dipakai membeli prajurit tambahan
   pada fase penempatan berikutnya.
5. Jika semua musuh di semua gelombang berhasil dikalahkan -> layar
   **Menang**. Jika HP benteng habis karena musuh yang lolos -> layar
   **Kalah**.

## Struktur folder & yang bisa diedit lewat JSON

```
strategi/
  main.py                      -> logika utama game
  game/
    config_loader.py           -> pemuat file JSON & gambar
    entities.py                -> kelas Unit, Enemy, Projectile
  config/
    units.json                 -> daftar 4 jenis prajurit: biaya (cost),
                                   HP, damage, jangkauan (range), kecepatan
                                   serang, splash_radius, warna fallback,
                                   dan NAMA FILE GAMBAR (image)
    waves.json                 -> daftar gelombang musuh: jenis, jumlah,
                                   HP, damage, kecepatan, reward kredit,
                                   dan nama file gambar musuh
    story.json                 -> teks Opening & Ending (menang/kalah),
                                   judul, paragraf, dan teks tombol
  assets/images/                -> tempat menaruh gambar (.png) prajurit
                                   & musuh. Nama file harus sama dengan
                                   yang ditulis di units.json / waves.json.
                                   Jika file tidak ditemukan, game otomatis
                                   memakai ikon bulat warna sebagai
                                   pengganti (tidak akan error/crash).
  generate_placeholder_assets.py -> skrip opsional pembuat ikon placeholder
```

### Menambah / mengganti gambar prajurit

1. Simpan gambar (disarankan PNG 64x64 transparan) di `assets/images/`,
   misal `pemanah_baru.png`.
2. Buka `config/units.json`, ubah nilai `"image"` pada prajurit terkait
   menjadi `"pemanah_baru.png"`.
3. Jalankan ulang `python main.py` - tidak perlu mengubah kode apa pun.

### Mengubah cerita pembuka/penutup

Edit `config/story.json` - ubah `title`, isi `paragraphs` (daftar
kalimat), dan `button_text` pada bagian `opening`, `ending_win`, atau
`ending_lose`.

### Menambah gelombang musuh baru / mengubah kesulitan

Edit `config/waves.json`, tambahkan objek baru pada array `waves`,
atau ubah `hp`, `damage`, `speed`, `count`, `reward` pada musuh yang
sudah ada.
