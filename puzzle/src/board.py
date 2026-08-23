"""Logika papan (grid) permainan: tabrakan, penguncian piece, hapus baris, garbage."""
import random

from .constants import BOARD_COLS, BOARD_ROWS, GARBAGE_TABLE, GARBAGE_COLOR
from .pieces import Piece, SevenBag


class Board:
    def __init__(self, rng_seed=None):
        self.cols = BOARD_COLS
        self.rows = BOARD_ROWS
        # grid[y][x] = warna (tuple) atau None jika kosong
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self._rng = random.Random(rng_seed)
        self.bag = SevenBag(self._rng)

        self.current = None
        self.next_kind = self.bag.next_kind()
        self.hold_kind = None

        self.pending_garbage = 0
        self.game_over = False
        self.lines_cleared_total = 0
        self.garbage_sent_total = 0

        self.spawn_piece()

    # ---------- Spawning & gerakan ----------
    def spawn_piece(self):
        kind = self.next_kind
        self.next_kind = self.bag.next_kind()
        spawn_x = self.cols // 2 - 2
        piece = Piece(kind, spawn_x)
        self.current = piece
        if not self.valid_position(piece):
            self.game_over = True
        return piece

    def valid_position(self, piece, rotation=None, dx=0, dy=0):
        for x, y in piece.cells(rotation=rotation, x=piece.x + dx, y=piece.y + dy):
            if x < 0 or x >= self.cols:
                return False
            if y >= self.rows:
                return False
            if y >= 0 and self.grid[y][x] is not None:
                return False
        return True

    def try_move(self, dx, dy):
        if self.current is None:
            return False
        if self.valid_position(self.current, dx=dx, dy=dy):
            self.current.x += dx
            self.current.y += dy
            return True
        return False

    def try_rotate(self):
        if self.current is None:
            return False
        new_rotation = (self.current.rotation + 1) % 4
        for kx, ky in self._kicks():
            if self.valid_position(self.current, rotation=new_rotation, dx=kx, dy=ky):
                self.current.rotation = new_rotation
                self.current.x += kx
                self.current.y += ky
                return True
        return False

    @staticmethod
    def _kicks():
        return [(0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)]

    def hard_drop(self):
        if self.current is None:
            return
        drop = 0
        while self.valid_position(self.current, dy=drop + 1):
            drop += 1
        self.current.y += drop
        self.lock_piece()

    def ghost_y(self):
        if self.current is None:
            return 0
        drop = 0
        while self.valid_position(self.current, dy=drop + 1):
            drop += 1
        return self.current.y + drop

    # ---------- Penguncian & pembersihan baris ----------
    def lock_piece(self):
        piece = self.current
        cells = piece.cells()
        overflowed = any(y < 0 for x, y in cells)
        for x, y in cells:
            if 0 <= y < self.rows and 0 <= x < self.cols:
                self.grid[y][x] = piece.color

        if overflowed:
            # Sebagian piece terkunci di luar batas atas papan -> tumpukan sudah
            # melewati puncak, pemain ini kalah.
            self.game_over = True
            self.current = None
            return 0

        cleared = self._clear_lines()

        # Terapkan garbage yang tertunda (dari serangan lawan) setelah piece dikunci.
        if self.pending_garbage > 0:
            self._push_garbage(self.pending_garbage)
            self.pending_garbage = 0

        self.spawn_piece()
        return cleared

    def _clear_lines(self):
        full_rows = set(y for y in range(self.rows) if all(cell is not None for cell in self.grid[y]))
        if not full_rows:
            return 0
        remaining = [row for y, row in enumerate(self.grid) if y not in full_rows]
        count = len(full_rows)
        self.grid = [[None for _ in range(self.cols)] for _ in range(count)] + remaining
        self.lines_cleared_total += count
        return count

    def garbage_for_clear(self, lines):
        return GARBAGE_TABLE.get(lines, 0)

    def queue_garbage(self, amount):
        """Dipanggil dari luar (papan lawan) untuk menambah antrean garbage."""
        if amount > 0:
            self.pending_garbage += amount

    def _push_garbage(self, amount):
        amount = min(amount, self.rows - 1)
        if amount <= 0:
            return
        hole = self._rng.randrange(self.cols)
        for _ in range(amount):
            self.grid.pop(0)
            row = [GARBAGE_COLOR for _ in range(self.cols)]
            row[hole] = None
            self.grid.append(row)
        # Setelah menambah garbage di bawah, piece yang sedang jatuh harus tetap valid;
        # jika sekarang bertabrakan, geser piece ke atas selama papan mengizinkan.
        if self.current is not None:
            tries = 0
            while not self.valid_position(self.current) and tries < self.rows:
                self.current.y -= 1
                tries += 1
            if not self.valid_position(self.current):
                self.game_over = True

    def add_lines_from_bottom(self, amount):
        self._push_garbage(amount)

    def is_topped_out(self):
        return self.game_over

    def height_profile(self):
        """Mengembalikan tinggi kolom (dipakai AI)."""
        heights = [0] * self.cols
        for x in range(self.cols):
            for y in range(self.rows):
                if self.grid[y][x] is not None:
                    heights[x] = self.rows - y
                    break
        return heights
