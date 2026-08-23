"""Definisi bentuk tetromino dan rotasinya (bounding box 4x4)."""
import random

from .constants import PIECE_COLORS

# Setiap piece punya 4 state rotasi, masing-masing berupa list koordinat (x, y)
# di dalam grid 4x4 (0..3, 0..3).
SHAPES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

PIECE_TYPES = list(SHAPES.keys())

# Kick offsets sederhana yang dicoba berurutan saat rotasi terhalang.
WALL_KICKS = [(0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)]


class Piece:
    __slots__ = ("kind", "rotation", "x", "y", "color")

    def __init__(self, kind, spawn_x):
        self.kind = kind
        self.rotation = 0
        self.x = spawn_x
        self.y = -2 if kind != "I" else -2
        self.color = PIECE_COLORS[kind]

    def cells(self, rotation=None, x=None, y=None):
        rotation = self.rotation if rotation is None else rotation
        x = self.x if x is None else x
        y = self.y if y is None else y
        shape = SHAPES[self.kind][rotation % 4]
        return [(x + cx, y + cy) for cx, cy in shape]

    def clone(self):
        p = Piece(self.kind, self.x)
        p.rotation = self.rotation
        p.y = self.y
        return p


class SevenBag:
    """Generator standar '7-bag' agar semua tipe piece muncul merata."""

    def __init__(self, rng=None):
        self._rng = rng or random.Random()
        self._bag = []

    def _refill(self):
        self._bag = PIECE_TYPES[:]
        self._rng.shuffle(self._bag)

    def next_kind(self):
        if not self._bag:
            self._refill()
        return self._bag.pop()
