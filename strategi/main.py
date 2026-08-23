"""
Game Strategi Penempatan Prajurit (Tower-Defense sederhana) - Pygame

Cara main singkat:
  1. Layar pembuka (Opening) muncul lebih dulu -> tekan tombol "Mulai".
  2. Fase Penempatan: pilih jenis prajurit (Pemanah/Pelindung/Penyerang/
     Penyihir) di panel bawah, lalu klik kotak grid di area biru muda
     (zona penempatan) untuk menempatkannya. Setiap prajurit memakan
     kredit sesuai harga masing-masing. Kredit terlihat di HUD atas.
  3. Setelah siap, klik tombol "Mulai Gelombang" untuk memulai
     pertarungan melawan musuh.
  4. Musuh yang berhasil dikalahkan menambah kredit (lihat reward di
     config/waves.json), sehingga bisa menempatkan lebih banyak
     prajurit lagi sebelum gelombang berikutnya.
  5. Jika benteng (base) kehabisan HP karena musuh yang lolos -> layar
     kalah muncul. Jika semua gelombang berhasil dihabisi -> layar
     menang muncul.

Semua teks pembuka/penutup ada di config/story.json.
Semua statistik & gambar prajurit ada di config/units.json.
Semua statistik & gambar musuh per gelombang ada di config/waves.json.
Mengubah file-file JSON tersebut TIDAK memerlukan perubahan kode.
"""
import random
import sys
import textwrap

import pygame

from game.config_loader import ImageBank, load_story_config, load_units_config, load_waves_config
from game.entities import Enemy, Unit

# ---------------------------------------------------------------- Konstanta
WIDTH, HEIGHT = 960, 680
FPS = 60

CELL = 60
COLS = 15
ROWS = 8

HUD_H = 60
FIELD_X0 = 0
FIELD_Y0 = HUD_H
FIELD_W = COLS * CELL
FIELD_H = ROWS * CELL
BOTTOM_Y0 = FIELD_Y0 + FIELD_H
BOTTOM_H = HEIGHT - BOTTOM_Y0

PLACEMENT_MAX_COL = 7  # kolom 0..7 boleh ditempati prajurit (zona pertahanan)

COLOR_BG = (24, 28, 22)
COLOR_FIELD = (40, 52, 36)
COLOR_FIELD_ZONE = (52, 70, 50)
COLOR_GRID_LINE = (60, 74, 56)
COLOR_HUD = (18, 20, 16)
COLOR_TEXT = (235, 235, 225)
COLOR_TEXT_DIM = (170, 175, 160)
COLOR_BTN = (70, 90, 70)
COLOR_BTN_HOVER = (95, 120, 95)
COLOR_BTN_DISABLED = (50, 50, 50)
COLOR_ACCENT = (230, 190, 90)


class Button:
    def __init__(self, rect, text, font, on_click=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.on_click = on_click
        self.enabled = True

    def draw(self, screen, hover):
        if not self.enabled:
            color = COLOR_BTN_DISABLED
        else:
            color = COLOR_BTN_HOVER if hover else COLOR_BTN
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (15, 15, 15), self.rect, 2, border_radius=8)
        label = self.font.render(self.text, True, COLOR_TEXT if self.enabled else COLOR_TEXT_DIM)
        screen.blit(label, label.get_rect(center=self.rect.center))

    def handle_click(self, pos):
        if self.enabled and self.rect.collidepoint(pos):
            if self.on_click:
                self.on_click()
            return True
        return False


def wrap_paragraphs(paragraphs, font, max_width):
    lines = []
    for p in paragraphs:
        # perkiraan lebar per karakter dari font untuk textwrap
        avg_char_w = font.size("x")[0] or 8
        wrap_chars = max(10, max_width // avg_char_w)
        wrapped = textwrap.wrap(p, wrap_chars) or [""]
        lines.extend(wrapped)
        lines.append("")  # baris kosong antar paragraf
    return lines


class GameApp:
    STATE_OPENING = "opening"
    STATE_PLACEMENT = "placement"
    STATE_BATTLE = "battle"
    STATE_ENDING_WIN = "ending_win"
    STATE_ENDING_LOSE = "ending_lose"

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Benteng Terakhir - Game Strategi")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_small = pygame.font.SysFont("segoeui,arial,sans-serif", 16)
        self.font_med = pygame.font.SysFont("segoeui,arial,sans-serif", 22, bold=True)
        self.font_big = pygame.font.SysFont("segoeui,arial,sans-serif", 40, bold=True)
        self.font_para = pygame.font.SysFont("segoeui,arial,sans-serif", 20)

        self.images = ImageBank()
        self.reload_config()

        self.state = self.STATE_OPENING
        self.reset_game()

        self.selected_unit_key = None
        self.unit_buttons = []
        self._build_unit_buttons()

        self.start_wave_btn = Button(
            (WIDTH - 190, 14, 170, 32), "Mulai Gelombang", self.font_small, self.start_wave
        )
        self.big_action_btn = Button((WIDTH // 2 - 110, HEIGHT - 110, 220, 54), "", self.font_med, None)

    # ------------------------------------------------------------ Config
    def reload_config(self):
        self.units_cfg = load_units_config()
        self.waves_cfg = load_waves_config()
        self.story_cfg = load_story_config()

    def reset_game(self):
        self.credit = self.units_cfg.get("starting_credit", 200)
        self.base_hp = self.waves_cfg.get("base_hp", 100)
        self.base_max_hp = self.base_hp
        self.wave_index = 0
        self.units = []
        self.enemies = []
        self.projectiles = []
        self.occupied = {}  # (col,row) -> Unit

        self.spawn_queue = []
        self.spawn_timer = 0.0
        self.wave_active = False
        self.wave_cleared_message_timer = 0.0

    # ------------------------------------------------------------ UI setup
    def _build_unit_buttons(self):
        keys = list(self.units_cfg["units"].keys())
        n = len(keys)
        btn_w = min(180, (WIDTH - 40) // n - 10)
        total_w = n * btn_w + (n - 1) * 12
        x0 = (WIDTH - total_w) // 2
        y0 = BOTTOM_Y0 + 10
        self.unit_buttons = []
        for i, key in enumerate(keys):
            rect = (x0 + i * (btn_w + 12), y0, btn_w, BOTTOM_H - 20)
            self.unit_buttons.append((key, pygame.Rect(rect)))

    # ------------------------------------------------------------ Placement helpers
    def cell_at_pixel(self, pos):
        x, y = pos
        if not (FIELD_X0 <= x < FIELD_X0 + FIELD_W and FIELD_Y0 <= y < FIELD_Y0 + FIELD_H):
            return None
        col = int((x - FIELD_X0) // CELL)
        row = int((y - FIELD_Y0) // CELL)
        return col, row

    def cell_center(self, col, row):
        return (FIELD_X0 + col * CELL + CELL / 2, FIELD_Y0 + row * CELL + CELL / 2)

    def try_place_unit(self, col, row):
        if self.selected_unit_key is None:
            return
        if col > PLACEMENT_MAX_COL:
            return
        if (col, row) in self.occupied:
            return
        cfg = self.units_cfg["units"][self.selected_unit_key]
        if self.credit < cfg["cost"]:
            return

        self.credit -= cfg["cost"]
        image = self.images.get(cfg.get("image"), (CELL - 10, CELL - 10), tuple(cfg.get("color", [150, 150, 150])))
        unit = Unit(self.selected_unit_key, cfg, col, row, self.cell_center(col, row), image)
        self.units.append(unit)
        self.occupied[(col, row)] = unit

    # ------------------------------------------------------------ Wave logic
    def start_wave(self):
        if self.state != self.STATE_PLACEMENT or self.wave_index >= len(self.waves_cfg["waves"]):
            return
        wave = self.waves_cfg["waves"][self.wave_index]
        self.spawn_queue = []
        for enemy_def in wave["enemies"]:
            for _ in range(enemy_def["count"]):
                self.spawn_queue.append(enemy_def)
        self.spawn_interval = wave.get("spawn_interval", 1.2)
        self.spawn_timer = 0.0
        self.wave_active = True
        self.state = self.STATE_BATTLE

    def on_enemy_reach_base(self, enemy):
        self.base_hp -= enemy.damage
        enemy.hp = 0  # tandai mati/hilang dari layar

    def update_battle(self, dt):
        # spawn musuh berikutnya dari antrian
        if self.spawn_queue:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.spawn_timer = self.spawn_interval
                enemy_def = self.spawn_queue.pop(0)
                row = random.randrange(ROWS)
                spawn_x = FIELD_X0 + FIELD_W - CELL / 2
                y = FIELD_Y0 + row * CELL + CELL / 2
                image = self.images.get(
                    enemy_def.get("image"), (CELL - 14, CELL - 14), tuple(enemy_def.get("color", [180, 60, 60]))
                )
                self.enemies.append(Enemy(enemy_def["type"], enemy_def, row, spawn_x, y, image))

        # update unit (menyerang musuh)
        for u in self.units:
            if u.alive:
                u.update(dt, self.enemies, self.projectiles)

        # update proyektil
        for p in self.projectiles:
            p.update(dt)
        self.projectiles = [p for p in self.projectiles if not p.done]

        # update musuh
        units_by_row = {}
        for u in self.units:
            if u.alive:
                units_by_row.setdefault(u.row, []).append(u)

        base_left_x = FIELD_X0
        for e in self.enemies:
            if e.alive:
                e.update(dt, units_by_row.get(e.row, []), base_left_x, self.on_enemy_reach_base)

        # beri kredit untuk musuh yang baru saja mati (sekali per musuh)
        self._collect_rewards()

        # bersihkan unit yang mati
        dead_units = [u for u in self.units if not u.alive]
        for u in dead_units:
            self.occupied.pop((u.col, u.row), None)
        self.units = [u for u in self.units if u.alive]

        # bersihkan musuh yang sudah mati/hilang
        self.enemies = [e for e in self.enemies if e.alive]

        if self.base_hp <= 0:
            self.state = self.STATE_ENDING_LOSE
            return

        wave_finished = not self.spawn_queue and not self.enemies
        if wave_finished:
            self.wave_index += 1
            if self.wave_index >= len(self.waves_cfg["waves"]):
                self.state = self.STATE_ENDING_WIN
            else:
                self.state = self.STATE_PLACEMENT

    def _collect_rewards(self):
        for e in list(self.enemies):
            if e.hp <= 0 and not getattr(e, "_reward_given", False):
                e._reward_given = True
                self.credit += e.reward

    # ------------------------------------------------------------ Event handling
    def handle_click(self, pos):
        if self.state == self.STATE_OPENING:
            if self.big_action_btn.rect.collidepoint(pos):
                self.state = self.STATE_PLACEMENT
            return

        if self.state in (self.STATE_ENDING_WIN, self.STATE_ENDING_LOSE):
            if self.big_action_btn.rect.collidepoint(pos):
                self.reset_game()
                self.state = self.STATE_OPENING
            return

        if self.state == self.STATE_PLACEMENT:
            if self.start_wave_btn.rect.collidepoint(pos):
                self.start_wave()
                return
            for key, rect in self.unit_buttons:
                if rect.collidepoint(pos):
                    self.selected_unit_key = key
                    return
            cell = self.cell_at_pixel(pos)
            if cell:
                self.try_place_unit(*cell)

    # ------------------------------------------------------------ Drawing
    def draw_field(self):
        pygame.draw.rect(self.screen, COLOR_FIELD, (FIELD_X0, FIELD_Y0, FIELD_W, FIELD_H))
        pygame.draw.rect(
            self.screen,
            COLOR_FIELD_ZONE,
            (FIELD_X0, FIELD_Y0, (PLACEMENT_MAX_COL + 1) * CELL, FIELD_H),
        )
        for c in range(COLS + 1):
            x = FIELD_X0 + c * CELL
            pygame.draw.line(self.screen, COLOR_GRID_LINE, (x, FIELD_Y0), (x, FIELD_Y0 + FIELD_H))
        for r in range(ROWS + 1):
            y = FIELD_Y0 + r * CELL
            pygame.draw.line(self.screen, COLOR_GRID_LINE, (FIELD_X0, y), (FIELD_X0 + FIELD_W, y))

        # garis benteng (base) di sisi kiri
        pygame.draw.rect(self.screen, COLOR_ACCENT, (FIELD_X0, FIELD_Y0, 5, FIELD_H))

    def draw_hud(self):
        pygame.draw.rect(self.screen, COLOR_HUD, (0, 0, WIDTH, HUD_H))
        credit_txt = self.font_med.render(f"Kredit: {self.credit}", True, COLOR_ACCENT)
        self.screen.blit(credit_txt, (16, 16))

        wave_num = min(self.wave_index + 1, len(self.waves_cfg["waves"]))
        wave_name = ""
        if self.wave_index < len(self.waves_cfg["waves"]):
            wave_name = self.waves_cfg["waves"][self.wave_index].get("name", f"Gelombang {wave_num}")
        wave_txt = self.font_small.render(
            f"{wave_name}  ({wave_num}/{len(self.waves_cfg['waves'])})", True, COLOR_TEXT
        )
        self.screen.blit(wave_txt, (240, 12))

        base_txt = self.font_small.render(
            f"HP Benteng: {max(self.base_hp, 0)}/{self.base_max_hp}", True, COLOR_TEXT
        )
        self.screen.blit(base_txt, (240, 34))

        if self.state == self.STATE_PLACEMENT:
            self.start_wave_btn.enabled = True
        else:
            self.start_wave_btn.enabled = False

    def draw_bottom_panel(self):
        pygame.draw.rect(self.screen, COLOR_HUD, (0, BOTTOM_Y0, WIDTH, BOTTOM_H))
        mouse = pygame.mouse.get_pos()
        for key, rect in self.unit_buttons:
            cfg = self.units_cfg["units"][key]
            selected = key == self.selected_unit_key
            affordable = self.credit >= cfg["cost"]
            base_color = COLOR_BTN_HOVER if rect.collidepoint(mouse) else COLOR_BTN
            if selected:
                base_color = COLOR_ACCENT
            if not affordable:
                base_color = COLOR_BTN_DISABLED
            pygame.draw.rect(self.screen, base_color, rect, border_radius=10)
            pygame.draw.rect(self.screen, (10, 10, 10), rect, 2, border_radius=10)

            icon = self.images.get(cfg.get("image"), (36, 36), tuple(cfg.get("color", [150, 150, 150])))
            icon_rect = icon.get_rect(midtop=(rect.centerx, rect.top + 8))
            self.screen.blit(icon, icon_rect)

            name_color = (20, 20, 20) if selected else COLOR_TEXT
            name_txt = self.font_small.render(cfg.get("display_name", key), True, name_color)
            self.screen.blit(name_txt, name_txt.get_rect(midtop=(rect.centerx, icon_rect.bottom + 4)))
            cost_txt = self.font_small.render(f"{cfg['cost']} kredit", True, name_color)
            self.screen.blit(cost_txt, cost_txt.get_rect(midtop=(rect.centerx, icon_rect.bottom + 22)))

    def draw_text_screen(self, data, extra_lines=None):
        self.screen.fill(COLOR_BG)
        title = self.font_big.render(data.get("title", ""), True, COLOR_ACCENT)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 120)))

        paragraphs = data.get("paragraphs", [])
        lines = wrap_paragraphs(paragraphs, self.font_para, WIDTH - 200)
        y = 190
        for line in lines:
            if line:
                txt = self.font_para.render(line, True, COLOR_TEXT)
                self.screen.blit(txt, txt.get_rect(center=(WIDTH // 2, y)))
            y += 30

        if extra_lines:
            for line in extra_lines:
                txt = self.font_med.render(line, True, COLOR_ACCENT)
                self.screen.blit(txt, txt.get_rect(center=(WIDTH // 2, y)))
                y += 34

        self.big_action_btn.text = data.get("button_text", "Lanjut")
        hover = self.big_action_btn.rect.collidepoint(pygame.mouse.get_pos())
        self.big_action_btn.draw(self.screen, hover)

    # ------------------------------------------------------------ Main loop
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)

            if self.state == self.STATE_BATTLE:
                self.update_battle(dt)

            self.render()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def render(self):
        if self.state == self.STATE_OPENING:
            self.draw_text_screen(self.story_cfg["opening"])
            return

        if self.state == self.STATE_ENDING_WIN:
            self.draw_text_screen(self.story_cfg["ending_win"], [f"Sisa kredit: {self.credit}"])
            return

        if self.state == self.STATE_ENDING_LOSE:
            self.draw_text_screen(self.story_cfg["ending_lose"], [f"Bertahan sampai {self.wave_index + 1}"])
            return

        self.screen.fill(COLOR_BG)
        self.draw_field()

        for u in self.units:
            u.draw(self.screen, CELL, self.font_small)
        for e in self.enemies:
            e.draw(self.screen)
        for p in self.projectiles:
            p.draw(self.screen)

        self.draw_hud()
        self.start_wave_btn.draw(self.screen, self.start_wave_btn.rect.collidepoint(pygame.mouse.get_pos()))
        self.draw_bottom_panel()

        if self.state == self.STATE_PLACEMENT and self.selected_unit_key:
            cfg = self.units_cfg["units"][self.selected_unit_key]
            hint = self.font_small.render(
                f"Klik area terang untuk menempatkan {cfg.get('display_name')}", True, COLOR_TEXT_DIM
            )
            self.screen.blit(hint, (16, HUD_H + 6))


if __name__ == "__main__":
    GameApp().run()
