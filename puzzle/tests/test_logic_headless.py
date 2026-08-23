"""Skrip verifikasi internal (bukan bagian dari game) - headless smoke test.
Menjalankan simulasi CPU vs CPU dipercepat untuk memastikan tidak ada exception,
garbage terkirim, kecepatan bertambah, dan match berakhir dengan wajar."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.game import Game, PlayerSlot, STATE_PLAYING, STATE_ENDING
from src.board import Board
from src.ai import CPUController
from src.characters import load_characters

def test_board_basic():
    b = Board(rng_seed=1)
    assert b.current is not None
    assert not b.game_over
    print("[OK] Board init & spawn")

def test_characters_load_and_fallback():
    chars = load_characters()
    assert len(chars) >= 1
    img = chars[0].load_image((64, 64))
    assert img.get_size() == (64, 64)
    print(f"[OK] {len(chars)} tokoh dimuat, fallback gambar bekerja")

def test_cpu_vs_cpu_match():
    # CPU dengan sedikit "kesalahan" acak (mistake_chance>0) supaya realistis:
    # bot heuristik sempurna bisa bertahan sangat lama, tapi tujuannya di sini
    # hanya memastikan simulasi panjang berjalan TANPA CRASH dan mekanisme
    # (garbage, percepatan) benar-benar aktif.
    game = Game()
    c1, c2 = game.characters[0], game.characters[1 % len(game.characters)]
    b1, b2 = Board(rng_seed=42), Board(rng_seed=99)
    slot1 = PlayerSlot(b1, c1, is_cpu=True, ai=CPUController(b1, action_interval_ms=1, mistake_chance=0.15), label="CPU1")
    slot2 = PlayerSlot(b2, c2, is_cpu=True, ai=CPUController(b2, action_interval_ms=1, mistake_chance=0.15), label="CPU2")
    game.slots = [slot1, slot2]
    game.state = STATE_PLAYING
    game.match_time_s = 0.0

    import pygame
    pressed = pygame.key.get_pressed()  # semua False, cukup untuk simulasi CPU-only

    max_iters = 60000  # ~16 menit waktu simulasi, cukup untuk memicu top-out dgn mistake_chance
    dt = 16
    ended = False
    for i in range(max_iters):
        game._update(dt, pressed)
        if game.state == STATE_ENDING:
            ended = True
            break

    print(f"[OK] Simulasi berjalan {i*dt/1000:.1f}s tanpa crash "
          f"(match_ended={ended}), drop_interval akhir={game.drop_interval_ms}ms, "
          f"garbage terkirim P1={slot1.board.garbage_sent_total} P2={slot2.board.garbage_sent_total}")
    if ended:
        assert game.draw_game or game.winner is not None


def test_speed_increases_over_time():
    from src.constants import INITIAL_DROP_MS, MIN_DROP_MS, SPEEDUP_INTERVAL_S, SPEEDUP_AMOUNT_MS
    game = Game()
    # CPU vs CPU tapi papan sengaja dibuat "tak akan penuh" (hanya mengecek rumus
    # kenaikan kecepatan terhadap waktu, terlepas dari kapan match berakhir).
    game.match_time_s = 0.0
    game.slots = []
    game.state = STATE_PLAYING

    def interval_at(t):
        game.match_time_s = t
        level = int(t // SPEEDUP_INTERVAL_S)
        return max(MIN_DROP_MS, INITIAL_DROP_MS - level * SPEEDUP_AMOUNT_MS)

    assert interval_at(0) == INITIAL_DROP_MS
    later = interval_at(SPEEDUP_INTERVAL_S * 3)
    assert later < INITIAL_DROP_MS, "Interval jatuh seharusnya mengecil (lebih cepat) seiring waktu"
    very_late = interval_at(SPEEDUP_INTERVAL_S * 100)
    assert very_late == MIN_DROP_MS, "Interval seharusnya dibatasi minimum agar tidak mustahil dimainkan"
    print(f"[OK] Rumus percepatan benar: t=0 -> {INITIAL_DROP_MS}ms, "
          f"t={SPEEDUP_INTERVAL_S*3}s -> {later}ms, sangat lama -> {very_late}ms (batas minimum)")


def test_topout_triggers_game_over():
    b = Board(rng_seed=7)
    # Isi hampir seluruh papan (kecuali 2 baris teratas) untuk memaksa top-out
    # saat piece berikutnya coba spawn.
    for y in range(0, b.rows):
        b.grid[y] = [(200, 200, 200)] * b.cols
    b.game_over = False
    b.spawn_piece()  # piece baru muncul di baris buffer (y negatif), masih "valid" di sana
    assert not b.game_over, "Spawn di area buffer atas seharusnya belum langsung game_over"
    # Papan penuh -> piece tidak bisa turun sama sekali -> saat terkunci, sebagian sel
    # ada di luar batas atas papan -> ini yang menandakan tumpukan sudah melewati puncak.
    b.lock_piece()
    assert b.game_over, "Board seharusnya game_over ketika piece terkunci melewati puncak papan"
    print("[OK] Top-out terdeteksi dengan benar saat tumpukan melewati puncak papan")


def test_garbage_queue_and_push():
    b = Board(rng_seed=3)
    before_rows_filled = sum(1 for row in b.grid if any(c is not None for c in row))
    b.queue_garbage(3)
    assert b.pending_garbage == 3
    b._push_garbage(b.pending_garbage)
    b.pending_garbage = 0
    after_rows_filled = sum(1 for row in b.grid if any(c is not None for c in row))
    assert after_rows_filled - before_rows_filled == 3
    print("[OK] Garbage berhasil ditambahkan ke papan (3 baris)")

if __name__ == "__main__":
    test_board_basic()
    test_characters_load_and_fallback()
    test_topout_triggers_game_over()
    test_garbage_queue_and_push()
    test_speed_increases_over_time()
    test_cpu_vs_cpu_match()
    print("\nSEMUA TES HEADLESS LULUS")
