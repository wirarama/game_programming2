"""AI sederhana untuk lawan CPU: mencari penempatan piece terbaik lalu
mengeksekusinya langkah demi langkah (rotate/geser/hard drop) seolah ditekan
oleh pemain, supaya animasi tetap terlihat natural."""
import random

from .pieces import SHAPES

WEIGHT_HEIGHT = -0.51
WEIGHT_LINES = 0.76
WEIGHT_HOLES = -0.36
WEIGHT_BUMPINESS = -0.18


class CPUController:
    def __init__(self, board, action_interval_ms=75, mistake_chance=0.06, rng=None):
        self.board = board
        self.action_interval = action_interval_ms
        self.mistake_chance = mistake_chance
        self._rng = rng or random.Random()
        self._plan_piece = None
        self._actions = []
        self._timer = 0.0

    def update(self, dt_ms):
        board = self.board
        if board.game_over or board.current is None:
            return

        if self._plan_piece is not board.current:
            self._plan_piece = board.current
            self._actions = self._compute_actions(board.current)
            self._timer = 0.0

        self._timer += dt_ms
        while self._actions and self._timer >= self.action_interval:
            self._timer -= self.action_interval
            action = self._actions.pop(0)
            current_before = board.current
            self._perform(action)
            if board.current is not current_before:
                # piece baru saja terkunci (drop) -> sisa rencana tidak relevan lagi
                self._actions = []
                break

    def _perform(self, action):
        board = self.board
        if action == "rotate":
            board.try_rotate()
        elif action == "left":
            board.try_move(-1, 0)
        elif action == "right":
            board.try_move(1, 0)
        elif action == "drop":
            board.hard_drop()

    # ---------- Perencanaan ----------
    def _compute_actions(self, piece):
        best = self._find_best_placement(piece)
        if best is None:
            return ["drop"]

        target_rotation, target_x = best
        actions = []
        rotate_steps = (target_rotation - piece.rotation) % 4
        actions.extend(["rotate"] * rotate_steps)

        dx = target_x - piece.x
        step = "right" if dx > 0 else "left"
        actions.extend([step] * abs(dx))

        actions.append("drop")
        return actions

    def _find_best_placement(self, piece):
        grid = self.board.grid
        cols = self.board.cols
        rows = self.board.rows
        best_score = None
        best_choice = None
        candidates = []

        for rotation in range(4):
            shape = SHAPES[piece.kind][rotation]
            xs = [dx for dx, dy in shape]
            min_x, max_x = min(xs), max(xs)
            for x in range(-min_x, cols - max_x):
                landing_y = self._drop_y(grid, shape, x, rows, cols)
                if landing_y is None:
                    continue
                cells = [(x + dx, landing_y + dy) for dx, dy in shape]
                score = self._evaluate(grid, cells, rows, cols)
                candidates.append((score, rotation, x))

        if not candidates:
            return None

        candidates.sort(key=lambda c: c[0], reverse=True)

        if self._rng.random() < self.mistake_chance and len(candidates) > 1:
            # sesekali CPU "salah" memilih dari beberapa opsi terbaik agar tidak sempurna
            pick_from = candidates[: min(4, len(candidates))]
            _, rotation, x = self._rng.choice(pick_from)
        else:
            _, rotation, x = candidates[0]

        best_choice = (rotation, x)
        return best_choice

    @staticmethod
    def _fits(grid, cells, rows, cols):
        for cx, cy in cells:
            if cx < 0 or cx >= cols or cy >= rows:
                return False
            if cy >= 0 and grid[cy][cx] is not None:
                return False
        return True

    def _drop_y(self, grid, shape, x, rows, cols):
        y = -4
        last_valid = None
        while y <= rows:
            cells = [(x + dx, y + dy) for dx, dy in shape]
            if self._fits(grid, cells, rows, cols):
                last_valid = y
                y += 1
            else:
                break
        return last_valid

    def _evaluate(self, grid, cells, rows, cols):
        occupied = [row[:] for row in grid]
        for cx, cy in cells:
            if 0 <= cy < rows and 0 <= cx < cols:
                occupied[cy][cx] = True

        full_rows = set(y for y in range(rows) if all(occupied[y][x] is not None for x in range(cols)))
        lines_cleared = len(full_rows)
        if full_rows:
            remaining = [row for y, row in enumerate(occupied) if y not in full_rows]
            occupied = [[None] * cols for _ in range(lines_cleared)] + remaining

        heights = [0] * cols
        holes = 0
        for x in range(cols):
            found_top = False
            for y in range(rows):
                filled = occupied[y][x] is not None
                if filled and not found_top:
                    heights[x] = rows - y
                    found_top = True
                elif found_top and not filled:
                    holes += 1

        aggregate_height = sum(heights)
        bumpiness = sum(abs(heights[i] - heights[i + 1]) for i in range(cols - 1))

        return (
            WEIGHT_HEIGHT * aggregate_height
            + WEIGHT_LINES * lines_cleared
            + WEIGHT_HOLES * holes
            + WEIGHT_BUMPINESS * bumpiness
        )
