"""State machine utama: menu -> pilih mode -> pilih tokoh -> bermain -> ending."""
import sys

import pygame

from .constants import (
    SCREEN_W, SCREEN_H, FPS, BLACK, WHITE, GRAY, DARK_GRAY, YELLOW, GREEN, RED, CYAN,
    BOARD_COLS, BOARD_ROWS, CELL_SIZE, BOARD_PIXEL_W, BOARD_PIXEL_H, SIDE_PANEL_W, BOARD_GAP,
    BOARD_BG, GRID_LINE, GARBAGE_COLOR,
    INITIAL_DROP_MS, MIN_DROP_MS, SPEEDUP_INTERVAL_S, SPEEDUP_AMOUNT_MS,
    SOFT_DROP_MULTIPLIER, LOCK_DELAY_MS,
    CONTROLS_ARROWS, CONTROLS_WASD,
)
from .board import Board
from .characters import load_characters
from .ai import CPUController

STATE_MENU = "menu"
STATE_CHAR_SELECT = "char_select"
STATE_PLAYING = "playing"
STATE_ENDING = "ending"

MODE_VS_CPU = "vs_cpu"
MODE_VS_PLAYER = "vs_player"

DAS_DELAY_MS = 160
DAS_REPEAT_MS = 40


class PlayerSlot:
    """Satu sisi papan: bisa manusia atau CPU."""

    def __init__(self, board, character, controls=None, is_cpu=False, ai=None, label="P1"):
        self.board = board
        self.character = character
        self.controls = controls
        self.is_cpu = is_cpu
        self.ai = ai
        self.label = label

        self.drop_accum = 0.0
        self.lock_timer = 0.0
        self.is_grounded = False

        self.das_timer = {"left": 0.0, "right": 0.0}
        self.das_active = {"left": False, "right": False}
        self.prev_pressed = {"left": False, "right": False}

    def handle_keydown(self, key):
        if self.is_cpu or self.controls is None or self.board.game_over:
            return
        if key == self.controls["rotate"]:
            self.board.try_rotate()
        elif key == self.controls["hard_drop"]:
            self.board.hard_drop()
            self.lock_timer = 0.0
            self.is_grounded = False

    def update_movement(self, dt_ms, pressed_keys):
        if self.is_cpu or self.controls is None or self.board.game_over:
            return
        for direction, dx in (("left", -1), ("right", 1)):
            key = self.controls[direction]
            is_down = pressed_keys[key]
            if is_down and not self.prev_pressed[direction]:
                self.board.try_move(dx, 0)
                self.das_timer[direction] = 0.0
                self.das_active[direction] = False
            elif is_down:
                self.das_timer[direction] += dt_ms
                if not self.das_active[direction] and self.das_timer[direction] >= DAS_DELAY_MS:
                    self.das_active[direction] = True
                    self.das_timer[direction] = 0.0
                    self.board.try_move(dx, 0)
                elif self.das_active[direction] and self.das_timer[direction] >= DAS_REPEAT_MS:
                    self.das_timer[direction] = 0.0
                    self.board.try_move(dx, 0)
            else:
                self.das_active[direction] = False
                self.das_timer[direction] = 0.0
            self.prev_pressed[direction] = is_down

    def is_soft_dropping(self, pressed_keys):
        if self.is_cpu or self.controls is None:
            return False
        return pressed_keys[self.controls["soft_drop"]]


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Block Clash — Puzzle Versus")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont(None, 54, bold=True)
        self.font_mid = pygame.font.SysFont(None, 32, bold=True)
        self.font_small = pygame.font.SysFont(None, 22)
        self.font_tiny = pygame.font.SysFont(None, 18)

        self.characters = load_characters()
        self.state = STATE_MENU
        self.mode = MODE_VS_CPU
        self.menu_index = 0

        self.p1_char_index = 0
        self.p2_char_index = 1 % len(self.characters)
        self.p1_confirmed = False
        self.p2_confirmed = False

        self.slots = []
        self.match_time_s = 0.0
        self.drop_interval_ms = INITIAL_DROP_MS
        self.winner = None
        self.draw_game = False

        self.running = True

    # ------------------------------------------------------------------
    def run(self):
        while self.running:
            dt_ms = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_keydown(event.key)
            if not self.running:
                break

            pressed = pygame.key.get_pressed()
            self._update(dt_ms, pressed)
            self._draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit(0)

    # ------------------------------------------------------------------
    def _handle_keydown(self, key):
        if self.state == STATE_MENU:
            if key in (pygame.K_UP, pygame.K_w):
                self.menu_index = (self.menu_index - 1) % 3
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_index = (self.menu_index + 1) % 3
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.menu_index == 0:
                    self.mode = MODE_VS_CPU
                    self._enter_char_select()
                elif self.menu_index == 1:
                    self.mode = MODE_VS_PLAYER
                    self._enter_char_select()
                else:
                    self.running = False
            elif key == pygame.K_ESCAPE:
                self.running = False

        elif self.state == STATE_CHAR_SELECT:
            self._handle_char_select_key(key)

        elif self.state == STATE_PLAYING:
            for slot in self.slots:
                slot.handle_keydown(key)

        elif self.state == STATE_ENDING:
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self._back_to_menu()

    def _enter_char_select(self):
        self.state = STATE_CHAR_SELECT
        self.p1_char_index = 0
        self.p2_char_index = 1 % len(self.characters)
        self.p1_confirmed = False
        self.p2_confirmed = False

    def _handle_char_select_key(self, key):
        n = len(self.characters)
        p1_keys = CONTROLS_ARROWS if self.mode == MODE_VS_CPU else CONTROLS_WASD
        p2_keys = CONTROLS_ARROWS

        if not self.p1_confirmed:
            if key == p1_keys["left"]:
                self.p1_char_index = (self.p1_char_index - 1) % n
            elif key == p1_keys["right"]:
                self.p1_char_index = (self.p1_char_index + 1) % n
            elif key == p1_keys["confirm"]:
                self.p1_confirmed = True

        if self.mode == MODE_VS_PLAYER and not self.p2_confirmed:
            if key == p2_keys["left"]:
                self.p2_char_index = (self.p2_char_index - 1) % n
            elif key == p2_keys["right"]:
                self.p2_char_index = (self.p2_char_index + 1) % n
            elif key == p2_keys["confirm"]:
                self.p2_confirmed = True

        if key == pygame.K_ESCAPE:
            self.state = STATE_MENU

        ready = self.p1_confirmed and (self.mode == MODE_VS_CPU or self.p2_confirmed)
        if ready:
            self._start_match()

    def _start_match(self):
        p1_char = self.characters[self.p1_char_index]
        if self.mode == MODE_VS_CPU:
            import random
            choices = [i for i in range(len(self.characters)) if i != self.p1_char_index] or [self.p1_char_index]
            p2_char = self.characters[random.choice(choices)]
        else:
            p2_char = self.characters[self.p2_char_index]

        board1 = Board()
        board2 = Board()

        if self.mode == MODE_VS_CPU:
            slot1 = PlayerSlot(board1, p1_char, controls=CONTROLS_ARROWS, label="Kamu")
            slot2 = PlayerSlot(board2, p2_char, is_cpu=True, ai=CPUController(board2), label="CPU")
        else:
            slot1 = PlayerSlot(board1, p1_char, controls=CONTROLS_WASD, label="P1")
            slot2 = PlayerSlot(board2, p2_char, controls=CONTROLS_ARROWS, label="P2")

        self.slots = [slot1, slot2]
        self.match_time_s = 0.0
        self.drop_interval_ms = INITIAL_DROP_MS
        self.winner = None
        self.draw_game = False
        self.state = STATE_PLAYING

    def _back_to_menu(self):
        self.state = STATE_MENU
        self.menu_index = 0
        self.slots = []

    # ------------------------------------------------------------------
    def _update(self, dt_ms, pressed):
        if self.state != STATE_PLAYING:
            return

        self.match_time_s += dt_ms / 1000.0
        level = int(self.match_time_s // SPEEDUP_INTERVAL_S)
        self.drop_interval_ms = max(MIN_DROP_MS, INITIAL_DROP_MS - level * SPEEDUP_AMOUNT_MS)

        for slot in self.slots:
            if slot.board.game_over:
                continue
            slot.update_movement(dt_ms, pressed)
            if slot.is_cpu:
                slot.ai.update(dt_ms)
            self._update_gravity(slot, dt_ms, pressed)

        if any(slot.board.game_over for slot in self.slots):
            self._resolve_match_end()

    def _update_gravity(self, slot, dt_ms, pressed):
        board = slot.board
        soft = slot.is_soft_dropping(pressed)
        interval = self.drop_interval_ms
        if soft:
            interval = max(20, interval / SOFT_DROP_MULTIPLIER)

        slot.drop_accum += dt_ms
        if slot.drop_accum >= interval:
            slot.drop_accum = 0.0
            if board.valid_position(board.current, dy=1):
                board.try_move(0, 1)
                slot.lock_timer = 0.0
                slot.is_grounded = False
            else:
                slot.is_grounded = True
                slot.lock_timer += interval
                if slot.lock_timer >= LOCK_DELAY_MS:
                    cleared = board.lock_piece()
                    slot.lock_timer = 0.0
                    slot.is_grounded = False
                    self._apply_garbage(slot, cleared)

    def _apply_garbage(self, slot, cleared_lines):
        if cleared_lines <= 0:
            return
        amount = slot.board.garbage_for_clear(cleared_lines)
        if amount <= 0:
            return
        other = self.slots[1] if slot is self.slots[0] else self.slots[0]
        other.board.queue_garbage(amount)
        slot.board.garbage_sent_total += amount

    def _resolve_match_end(self):
        p1, p2 = self.slots
        if p1.board.game_over and p2.board.game_over:
            self.draw_game = True
            self.winner = None
        elif p1.board.game_over:
            self.winner = p2
        else:
            self.winner = p1
        self.state = STATE_ENDING

    # ------------------------------------------------------------------ draw
    def _draw(self):
        self.screen.fill(BLACK)
        if self.state == STATE_MENU:
            self._draw_menu()
        elif self.state == STATE_CHAR_SELECT:
            self._draw_char_select()
        elif self.state == STATE_PLAYING:
            self._draw_playing()
        elif self.state == STATE_ENDING:
            self._draw_ending()

    def _draw_menu(self):
        title = self.font_big.render("BLOCK CLASH", True, YELLOW)
        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 110)))
        subtitle = self.font_small.render("Puzzle Versus dengan Tokoh Pilihan", True, GRAY)
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_W // 2, 155)))

        options = ["1 Pemain vs CPU", "2 Pemain (1 Keyboard)", "Keluar"]
        for i, opt in enumerate(options):
            color = YELLOW if i == self.menu_index else WHITE
            prefix = "> " if i == self.menu_index else "   "
            text = self.font_mid.render(prefix + opt, True, color)
            self.screen.blit(text, text.get_rect(center=(SCREEN_W // 2, 260 + i * 50)))

        hint = self.font_tiny.render("Panah Atas/Bawah untuk pilih, Enter untuk konfirmasi", True, GRAY)
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - 40)))

    def _draw_char_select(self):
        title = self.font_mid.render("PILIH TOKOH", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 40)))

        card_w, card_h = 140, 170
        gap = 24
        n = len(self.characters)
        total_w = n * card_w + (n - 1) * gap
        start_x = (SCREEN_W - total_w) // 2
        y = 100

        for i, char in enumerate(self.characters):
            x = start_x + i * (card_w + gap)
            rect = pygame.Rect(x, y, card_w, card_h)
            pygame.draw.rect(self.screen, DARK_GRAY, rect, border_radius=8)

            img = char.load_image((card_w - 20, card_h - 60))
            self.screen.blit(img, (x + 10, y + 10))

            name = self.font_tiny.render(char.name, True, WHITE)
            self.screen.blit(name, name.get_rect(center=(x + card_w // 2, y + card_h - 34)))

            is_p1 = (i == self.p1_char_index) and not self.p1_confirmed
            is_p2 = (i == self.p2_char_index) and self.mode == MODE_VS_PLAYER and not self.p2_confirmed
            border_color = None
            if is_p1 and is_p2:
                border_color = (255, 255, 255)
            elif is_p1:
                border_color = CYAN
            elif is_p2:
                border_color = (255, 120, 200)
            if border_color:
                pygame.draw.rect(self.screen, border_color, rect, width=4, border_radius=8)

            if self.p1_confirmed and i == self.p1_char_index:
                tag = self.font_tiny.render("P1 SIAP", True, GREEN)
                self.screen.blit(tag, (x + 6, y + 6))
            if self.mode == MODE_VS_PLAYER and self.p2_confirmed and i == self.p2_char_index:
                tag = self.font_tiny.render("P2 SIAP", True, GREEN)
                self.screen.blit(tag, (x + 6, y + card_h - 56))

        p1_label = self.mode == MODE_VS_CPU and "Kamu (Panah + Enter)" or "P1: A/D geser, W putar, F pilih"
        info1 = self.font_small.render(p1_label, True, CYAN)
        self.screen.blit(info1, (40, SCREEN_H - 70))

        if self.mode == MODE_VS_PLAYER:
            info2 = self.font_small.render("P2: Panah geser/putar, Enter pilih", True, (255, 120, 200))
            self.screen.blit(info2, (40, SCREEN_H - 44))
        else:
            info2 = self.font_small.render("CPU akan memilih tokoh secara acak", True, GRAY)
            self.screen.blit(info2, (40, SCREEN_H - 44))

    def _draw_playing(self):
        p1, p2 = self.slots
        left_origin = (SIDE_PANEL_W, 40)
        right_origin = (SIDE_PANEL_W + BOARD_PIXEL_W + BOARD_GAP, 40)

        self._draw_side_panel(p1, (10, 40))
        self._draw_board_area(p1, left_origin)
        self._draw_board_area(p2, right_origin)
        self._draw_side_panel(p2, (SCREEN_W - SIDE_PANEL_W + 10, 40))

        timer_text = self.font_small.render(f"Waktu: {int(self.match_time_s)}s", True, WHITE)
        self.screen.blit(timer_text, timer_text.get_rect(center=(SCREEN_W // 2, 15)))
        speed_text = self.font_tiny.render(
            f"Kecepatan jatuh: {self.drop_interval_ms}ms", True, GRAY
        )
        self.screen.blit(speed_text, speed_text.get_rect(center=(SCREEN_W // 2, SCREEN_H - 12)))

    def _draw_side_panel(self, slot, pos):
        x, y = pos
        img = slot.character.load_image((SIDE_PANEL_W - 30, 110))
        self.screen.blit(img, (x, y))
        name = self.font_small.render(slot.character.name, True, WHITE)
        self.screen.blit(name, (x, y + 116))
        label = self.font_tiny.render(slot.label, True, CYAN)
        self.screen.blit(label, (x, y + 140))

        next_label = self.font_tiny.render("Next:", True, GRAY)
        self.screen.blit(next_label, (x, y + 170))
        next_box = pygame.Rect(x, y + 190, 90, 70)
        pygame.draw.rect(self.screen, DARK_GRAY, next_box, border_radius=4)
        self._draw_mini_piece(slot.board.next_kind, next_box)

        garbage_label = self.font_tiny.render(
            f"Garbage kirim: {slot.board.garbage_sent_total}", True, RED
        )
        self.screen.blit(garbage_label, (x, y + 270))

        if slot.board.pending_garbage > 0:
            warn = self.font_tiny.render(
                f"! {slot.board.pending_garbage} baris masuk", True, YELLOW
            )
            self.screen.blit(warn, (x, y + 292))

    def _draw_mini_piece(self, kind, box_rect):
        from .pieces import SHAPES
        from .constants import PIECE_COLORS
        shape = SHAPES[kind][0]
        cell = 14
        xs = [c[0] for c in shape]
        ys = [c[1] for c in shape]
        w = (max(xs) - min(xs) + 1) * cell
        h = (max(ys) - min(ys) + 1) * cell
        ox = box_rect.x + (box_rect.w - w) // 2 - min(xs) * cell
        oy = box_rect.y + (box_rect.h - h) // 2 - min(ys) * cell
        for cx, cy in shape:
            rect = pygame.Rect(ox + cx * cell, oy + cy * cell, cell - 1, cell - 1)
            pygame.draw.rect(self.screen, PIECE_COLORS[kind], rect, border_radius=2)

    def _draw_board_area(self, slot, origin):
        ox, oy = origin
        board_rect = pygame.Rect(ox, oy, BOARD_PIXEL_W, BOARD_PIXEL_H)
        pygame.draw.rect(self.screen, BOARD_BG, board_rect)

        for gy in range(BOARD_ROWS):
            for gx in range(BOARD_COLS):
                color = slot.board.grid[gy][gx]
                cell_rect = pygame.Rect(ox + gx * CELL_SIZE, oy + gy * CELL_SIZE, CELL_SIZE - 1, CELL_SIZE - 1)
                if color is not None:
                    pygame.draw.rect(self.screen, color, cell_rect, border_radius=2)
                else:
                    pygame.draw.rect(self.screen, GRID_LINE, cell_rect, width=1)

        board = slot.board
        if not board.game_over and board.current is not None:
            ghost_y = board.ghost_y()
            for cx, cy in board.current.cells(y=ghost_y):
                if cy >= 0:
                    rect = pygame.Rect(ox + cx * CELL_SIZE, oy + cy * CELL_SIZE, CELL_SIZE - 1, CELL_SIZE - 1)
                    pygame.draw.rect(self.screen, board.current.color, rect, width=2, border_radius=2)

            for cx, cy in board.current.cells():
                if cy >= 0:
                    rect = pygame.Rect(ox + cx * CELL_SIZE, oy + cy * CELL_SIZE, CELL_SIZE - 1, CELL_SIZE - 1)
                    pygame.draw.rect(self.screen, board.current.color, rect, border_radius=2)

        pygame.draw.rect(self.screen, GRAY, board_rect, width=2)

        if board.game_over:
            overlay = pygame.Surface((BOARD_PIXEL_W, BOARD_PIXEL_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.screen.blit(overlay, (ox, oy))
            text = self.font_mid.render("KALAH", True, RED)
            self.screen.blit(text, text.get_rect(center=(ox + BOARD_PIXEL_W // 2, oy + BOARD_PIXEL_H // 2)))

    def _draw_ending(self):
        if self.draw_game or self.winner is None:
            title = self.font_big.render("SERI!", True, YELLOW)
            self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 120)))
            sub = self.font_small.render("Kedua pemain kalah di saat bersamaan.", True, WHITE)
            self.screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, 170)))
        else:
            char = self.winner.character
            img = char.load_image((180, 180), ending=True)
            self.screen.blit(img, img.get_rect(center=(SCREEN_W // 2, 130)))

            title = self.font_mid.render(char.ending_title, True, YELLOW)
            self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 240)))

            winner_line = self.font_small.render(f"{self.winner.label} MENANG! ({char.name})", True, GREEN)
            self.screen.blit(winner_line, winner_line.get_rect(center=(SCREEN_W // 2, 270)))

            y = 305
            for line in char.ending_text:
                text = self.font_tiny.render(line, True, WHITE)
                self.screen.blit(text, text.get_rect(center=(SCREEN_W // 2, y)))
                y += 22

        hint = self.font_tiny.render("Tekan Enter untuk kembali ke menu", True, GRAY)
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - 30)))
