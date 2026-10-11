# Sky Defender — Scroll Shooting

Game tembak-tembakan 2D scroll vertikal (atas ke bawah), dibuat dengan HTML5 Canvas + JavaScript murni (tanpa engine/library eksternal, tanpa instalasi apa pun).

## Cara menjalankan

Browser memblokir `fetch()` file JSON saat dibuka langsung lewat `file://`, jadi jalankan lewat server lokal sederhana:

**Windows (Python sudah terpasang):**
```
cd scroll-shooting
python -m http.server 8000
```
Lalu buka `http://localhost:8000` di browser.

**Alternatif (Node.js):**
```
npx serve .
```

**Alternatif (VS Code):** install extension "Live Server", klik kanan `index.html` → "Open with Live Server".

## Kontrol

- Panah / WASD: gerak pesawat
- Spasi (atau tahan joystick di HP): tembak
- X atau Shift (atau tombol BOM di HP): pakai bom (damage ke semua musuh di layar)

## Fitur

- Scroll background otomatis dari atas ke bawah, terus-menerus.
- 5 jenis musuh (scout, fighter, bomber, interceptor, cruiser), muncul acak berdasarkan bobot spawn, dengan pola gerak berbeda (lurus, zig-zag, sinus) dan sebagian bisa menembak balik.
- Setelah 30 musuh dikalahkan, Boss (Mothership) muncul. Boss punya fase 2 (di bawah 50% HP menembak lebih cepat).
- Bom: terisi otomatis setiap sejumlah tembakan (`bomb.shotsToChargeBomb` di config), memberi damage ke seluruh musuh di layar sekaligus. Bom di-refill setiap kali pemain kehilangan nyawa (`bomb.refillOnDeath`).
- 3 nyawa di awal (`player.startLives`), ada invincibility singkat setelah kena hit.
- Saat nyawa habis, muncul dialog "Lanjutkan / Selesai". Lanjutkan → nyawa & bom direset, skor & progres musuh tetap. Selesai → menuju layar ending kalah.
- Mengalahkan boss → layar ending menang.
- Menu, cerita opening, dan kedua ending (menang/kalah) sepenuhnya berbasis gambar + teks dari `config/story.json` — mudah diedit tanpa menyentuh kode.
- Mendukung kontrol sentuh (joystick virtual + tombol bom) untuk HP/tablet.

## Konfigurasi (tanpa coding)

### `config/game-config.json`
Atur semua angka gameplay:
- `player`: kecepatan, jumlah tembakan per detik, nyawa awal, gambar pesawat & peluru.
- `bomb`: `shotsToChargeBomb` (berapa kali tembak untuk dapat 1 bom baru), `startingBombs`, `maxBombs`, `refillOnDeath`.
- `enemiesToTriggerBoss`: jumlah musuh yang harus dikalahkan sebelum boss muncul (default 30).
- `enemyTypes`: array 5 musuh — masing-masing punya `hitsToKill` (jumlah tembakan untuk mengalahkan), `speed`, `score`, `spawnWeight` (peluang muncul), `movement` (`straight`/`zigzag`/`sine`), dan gambar sendiri.
- `boss`: `hitsToKill` (jumlah tembakan untuk mengalahkan boss), kecepatan tembak, jumlah peluru per tembakan, dsb.
- `spawning`: kecepatan & percepatan kemunculan musuh seiring waktu.

Tinggal ubah angka di file JSON ini lalu refresh browser — tidak perlu menyentuh file `.js`.

### `config/story.json`
Atur semua teks & gambar tampilan:
- `menu`: judul, subjudul, teks tombol, background menu.
- `opening`: judul, paragraf cerita pembuka, gambar.
- `endingWin` / `endingLose`: judul, paragraf cerita penutup (menang/kalah), gambar.
- `continuePrompt`: teks dialog "Lanjutkan / Selesai".
- `hud`: label-label di HUD (Nyawa, Bom, Skor, dst).

## Aset gambar

Semua gambar ada di `assets/img/` (dibuat otomatis, gaya vector sederhana):
`player.png`, `enemy1_scout.png` … `enemy5_cruiser.png`, `boss.png`, `bullet_player.png`, `bullet_enemy.png`, `bomb_icon.png`, `bomb_blast.png`, `bg_game.png`, `bg_menu.png`, `story_opening.png`, `story_ending_win.png`, `story_ending_lose.png`, `life_icon.png`.

Ingin ganti tampilan? Tinggal timpa (replace) file PNG dengan nama yang sama, atau ubah nama filenya lalu update path di `config/game-config.json` / `config/story.json`.

## Struktur folder

```
scroll-shooting/
├── index.html
├── css/style.css
├── js/main.js
├── config/
│   ├── game-config.json
│   └── story.json
├── assets/img/*.png
└── gen_assets.py        (script Python yang membuat semua PNG di atas, opsional)
```
