"""Konstanta global untuk game puzzle versus."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CHARACTERS_JSON = os.path.join(DATA_DIR, "characters.json")

# ---- Board ----
BOARD_COLS = 10
BOARD_ROWS = 20
CELL_SIZE = 24

# ---- Window ----
BOARD_PIXEL_W = BOARD_COLS * CELL_SIZE
BOARD_PIXEL_H = BOARD_ROWS * CELL_SIZE
SIDE_PANEL_W = 160
BOARD_GAP = 90

SCREEN_W = SIDE_PANEL_W + BOARD_PIXEL_W + BOARD_GAP + BOARD_PIXEL_W + SIDE_PANEL_W
SCREEN_H = BOARD_PIXEL_H + 80
FPS = 60

# ---- Warna ----
BLACK = (10, 10, 14)
WHITE = (240, 240, 240)
GRAY = (70, 70, 80)
DARK_GRAY = (35, 35, 42)
RED = (220, 60, 60)
GREEN = (60, 200, 100)
YELLOW = (240, 210, 60)
CYAN = (60, 200, 220)
GARBAGE_COLOR = (110, 110, 110)
BOARD_BG = (20, 20, 26)
GRID_LINE = (40, 40, 50)

PIECE_COLORS = {
    "I": (60, 200, 220),
    "O": (240, 210, 60),
    "T": (170, 90, 220),
    "S": (90, 210, 110),
    "Z": (220, 80, 80),
    "J": (70, 110, 220),
    "L": (230, 150, 60),
}

# ---- Timing / difficulty ----
INITIAL_DROP_MS = 800
MIN_DROP_MS = 110
SPEEDUP_INTERVAL_S = 18          # setiap sekian detik, permainan makin cepat
SPEEDUP_AMOUNT_MS = 55           # dikurangi dari drop interval tiap kenaikan level

LOCK_DELAY_MS = 450              # jeda sebelum piece benar-benar terkunci di lantai
SOFT_DROP_MULTIPLIER = 18        # soft drop mempercepat turun berapa kali lipat

# garbage yang dikirim berdasarkan jumlah baris yang dibersihkan sekaligus
GARBAGE_TABLE = {1: 0, 2: 1, 3: 2, 4: 4}

# ---- Kontrol ----
import pygame

CONTROLS_ARROWS = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "rotate": pygame.K_UP,
    "soft_drop": pygame.K_DOWN,
    "hard_drop": pygame.K_RETURN,
    "confirm": pygame.K_RETURN,
}

CONTROLS_WASD = {
    "left": pygame.K_a,
    "right": pygame.K_d,
    "rotate": pygame.K_w,
    "soft_drop": pygame.K_s,
    "hard_drop": pygame.K_f,
    "confirm": pygame.K_f,
}
