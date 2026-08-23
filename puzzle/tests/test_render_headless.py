"""Tes headless tambahan: pastikan semua fungsi _draw_* untuk tiap state berjalan
tanpa exception (menu, pilih tokoh, bermain, ending menang, ending seri)."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.game import Game, PlayerSlot, STATE_MENU, STATE_CHAR_SELECT, STATE_PLAYING, STATE_ENDING
from src.board import Board
from src.ai import CPUController


def main():
    game = Game()

    game.state = STATE_MENU
    for i in range(3):
        game.menu_index = i
        game._draw()
    print("[OK] Render menu (semua opsi)")

    game.state = STATE_CHAR_SELECT
    game.mode = "vs_cpu"
    game._draw()
    game.mode = "vs_player"
    game.p1_confirmed = True
    game._draw()
    print("[OK] Render layar pilih tokoh (vs CPU & 2P, termasuk status siap)")

    c1, c2 = game.characters[0], game.characters[1 % len(game.characters)]
    b1, b2 = Board(rng_seed=1), Board(rng_seed=2)
    slot1 = PlayerSlot(b1, c1, controls=None, is_cpu=True, ai=CPUController(b1), label="P1")
    slot2 = PlayerSlot(b2, c2, controls=None, is_cpu=True, ai=CPUController(b2), label="CPU")
    game.slots = [slot1, slot2]
    game.state = STATE_PLAYING
    game.match_time_s = 12.5
    for _ in range(5):
        game._draw()
    b1.game_over = True  # cek overlay "KALAH"
    game._draw()
    print("[OK] Render layar bermain (normal & saat salah satu game over)")

    game.state = STATE_ENDING
    game.winner = slot2
    game.draw_game = False
    game._draw()
    game.draw_game = True
    game.winner = None
    game._draw()
    print("[OK] Render layar ending (menang & seri)")

    print("\nSEMUA TES RENDER HEADLESS LULUS")


if __name__ == "__main__":
    main()
