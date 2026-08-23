# Block Clash — Puzzle Versus

Game puzzle bertumpuk blok (mirip Tetris) dengan sistem **versus** dan **tokoh yang bisa
dipilih** seperti game fighting. Dibuat dengan Pygame.

## Cara menjalankan

```bash
pip install -r requirements.txt
python main.py
```

## Cara bermain

- Menu utama: pilih **1 Pemain vs CPU** atau **2 Pemain (1 Keyboard)**.
- Layar pilih tokoh: gerak kiri/kanan untuk memilih, konfirmasi untuk mengunci pilihan.
- Saat bermain, susun balok yang jatuh agar membentuk satu baris penuh untuk
  menghapusnya. **Setiap baris yang berhasil dihapus di papanmu akan mengirim
  garbage (baris sampah) ke papan lawan** — semakin banyak baris sekaligus,
  semakin banyak garbage yang dikirim.
- **Kecepatan jatuh balok bertambah seiring waktu** — makin lama pertandingan,
  makin cepat dan makin sulit.
- **Siapa yang duluan tumpukan blok-nya mencapai puncak papan, dia kalah.**
  Lawan otomatis menang dan mendapat layar ending khusus sesuai tokoh yang dipakai.

### Kontrol

| Aksi | P1 (mode 2 pemain) | Pemain solo (vs CPU) |
|---|---|---|
| Geser kiri/kanan | `A` / `D` | Panah Kiri/Kanan |
| Putar | `W` | Panah Atas |
| Soft drop (turun cepat) | `S` | Panah Bawah |
| Hard drop (jatuh instan) | `F` | Enter |

| Aksi | P2 (mode 2 pemain) |
|---|---|
| Geser kiri/kanan | Panah Kiri/Kanan |
| Putar | Panah Atas |
| Soft drop | Panah Bawah |
| Hard drop | Enter |

Di menu & layar ending, gunakan Panah Atas/Bawah dan Enter.

## Menambah / mengedit tokoh (JSON, tanpa coding)

Semua tokoh — nama, gambar, warna placeholder, dan cerita ending — diatur di:

```
data/characters.json
```

Contoh satu entri tokoh:

```json
{
  "id": "rei",
  "name": "Rei \"Baja\"",
  "image": "assets/images/rei.png",
  "color": [230, 70, 70],
  "ending": {
    "title": "Sang Juara Tak Terkalahkan",
    "image": "assets/images/rei_ending.png",
    "text": [
      "Baris pertama cerita ending...",
      "Baris kedua cerita ending...",
      "dst."
    ]
  }
}
```

- `image` / `ending.image`: path relatif ke folder `puzzle/`, menunjuk ke file gambar
  di `assets/images/`. Bebas PNG/JPG, ukuran apa pun (otomatis di-scale).
  **Jika file belum ada, game tidak akan error** — otomatis memakai kotak warna
  (`color`) + inisial nama sebagai gambar sementara, jadi kamu bisa isi teks/JSON
  dulu dan tambahkan gambar belakangan.
- `color`: warna RGB `[R, G, B]` (0–255) dipakai untuk kartu pemilihan tokoh & gambar
  placeholder jika `image` tidak ditemukan.
- `ending.text`: list baris teks cerita kemenangan khusus tokoh tersebut, ditampilkan
  di layar ending saat tokoh itu menang.
- Tambahkan tokoh baru cukup dengan menambah satu object baru di array `"characters"`.
  Tidak ada batas jumlah tokoh — game otomatis menyesuaikan tampilan grid pemilihan.

## Struktur folder

```
puzzle/
├── main.py                 # entry point
├── requirements.txt
├── data/
│   └── characters.json     # data semua tokoh (edit di sini)
├── assets/
│   └── images/              # taruh gambar tokoh & ending di sini
└── src/
    ├── constants.py         # ukuran papan, warna, kecepatan, kontrol
    ├── pieces.py             # bentuk & rotasi tetromino
    ├── board.py               # logika papan: tabrakan, hapus baris, garbage
    ├── ai.py                    # AI lawan CPU (heuristik penempatan blok)
    ├── characters.py            # loader characters.json + fallback gambar
    └── game.py                  # state machine: menu/pilih tokoh/main/ending
```

## Mekanik ringkas

- Papan 10x20, 7 jenis tetromino standar dengan sistem "7-bag" (semua bentuk
  muncul merata, tidak ada bentuk yang keluar berulang-ulang).
- Garbage dikirim berdasarkan jumlah baris yang dihapus sekaligus: 1 baris = tidak
  mengirim apa-apa, 2 baris = 1 garbage, 3 baris = 2 garbage, 4 baris (Tetris) =
  4 garbage. Garbage punya satu lubang acak per baris supaya lawan masih bisa
  membersihkannya.
- Kecepatan jatuh bertambah setiap ~18 detik pertandingan, sampai batas maksimum
  kecepatan.
- Mode CPU memakai AI heuristik sederhana (menilai tinggi tumpukan, lubang, dan
  kerataan papan) untuk memilih rotasi & posisi terbaik setiap piece, lalu
  "menekan tombol" langkah demi langkah supaya animasinya tetap terlihat alami.
