"""Kelas-kelas entitas gameplay: Prajurit (Unit), Musuh (Enemy), dan
Proyektil (Projectile) untuk efek visual serangan jarak jauh."""
import math

import pygame


class Unit:
    """Prajurit yang ditempatkan pemain di grid."""

    def __init__(self, unit_key, cfg, col, row, pos, image):
        self.key = unit_key
        self.cfg = cfg
        self.col = col
        self.row = row
        self.pos = pygame.Vector2(pos)
        self.image = image

        self.max_hp = cfg["hp"]
        self.hp = cfg["hp"]
        self.damage = cfg["damage"]
        self.range = cfg["range"]
        self.attack_speed = max(cfg.get("attack_speed", 1.0), 0.05)
        self.splash_radius = cfg.get("splash_radius", 0)
        self.color = tuple(cfg.get("color", [150, 150, 150]))
        self.display_name = cfg.get("display_name", unit_key)

        self.cooldown = 0.0

    @property
    def alive(self):
        return self.hp > 0

    def update(self, dt, enemies, projectiles):
        self.cooldown -= dt
        if self.cooldown > 0:
            return

        target = self._find_target(enemies)
        if target is None:
            return

        self.cooldown = 1.0 / self.attack_speed
        projectiles.append(
            Projectile(
                origin=self.pos,
                target=target,
                damage=self.damage,
                splash_radius=self.splash_radius,
                color=self.color,
                enemies_ref=enemies,
            )
        )

    def _find_target(self, enemies):
        best = None
        best_dist = self.range
        for e in enemies:
            if not e.alive:
                continue
            dist = self.pos.distance_to(e.pos)
            if dist <= best_dist:
                best = e
                best_dist = dist
        return best

    def draw(self, screen, cell_size, font):
        rect = self.image.get_rect(center=self.pos)
        screen.blit(self.image, rect)

        # bar HP
        bar_w = cell_size * 0.8
        bar_h = 6
        x = self.pos.x - bar_w / 2
        y = self.pos.y - cell_size / 2 - 10
        pct = max(self.hp / self.max_hp, 0)
        pygame.draw.rect(screen, (40, 40, 40), (x, y, bar_w, bar_h))
        pygame.draw.rect(screen, (70, 200, 90), (x, y, bar_w * pct, bar_h))

        # lingkaran jangkauan tipis saat digambar (opsional, redup)
        # dibiarkan mati agar layar tidak penuh; bisa diaktifkan saat debug


class Enemy:
    """Musuh yang bergerak dari kanan ke kiri menuju benteng pemain."""

    def __init__(self, enemy_type, data, row, spawn_x, y, image):
        self.type = enemy_type
        self.row = row
        self.pos = pygame.Vector2(spawn_x, y)
        self.image = image

        self.max_hp = data["hp"]
        self.hp = data["hp"]
        self.damage = data["damage"]
        self.speed = data["speed"]
        self.reward = data.get("reward", 10)

        self.attack_cooldown = 0.0

    @property
    def alive(self):
        return self.hp > 0

    def update(self, dt, units_in_row, base_left_x, on_reach_base):
        blocker = self._find_blocker(units_in_row)
        if blocker is not None:
            self.attack_cooldown -= dt
            if self.attack_cooldown <= 0:
                self.attack_cooldown = 0.8
                blocker.hp -= self.damage
            return

        self.pos.x -= self.speed * dt
        if self.pos.x <= base_left_x:
            on_reach_base(self)

    def _find_blocker(self, units_in_row):
        closest = None
        closest_dist = 999999
        for u in units_in_row:
            if not u.alive:
                continue
            if u.pos.x >= self.pos.x:
                continue
            dist = self.pos.x - u.pos.x
            if dist < 46 and dist < closest_dist:
                closest = u
                closest_dist = dist
        return closest

    def draw(self, screen):
        rect = self.image.get_rect(center=self.pos)
        screen.blit(self.image, rect)

        bar_w = 40
        bar_h = 5
        x = self.pos.x - bar_w / 2
        y = self.pos.y - 30
        pct = max(self.hp / self.max_hp, 0)
        pygame.draw.rect(screen, (40, 40, 40), (x, y, bar_w, bar_h))
        pygame.draw.rect(screen, (200, 70, 70), (x, y, bar_w * pct, bar_h))


class Projectile:
    """Efek visual + penerap damage instan (hitscan sederhana dengan
    animasi garis/peluru bergerak) dari prajurit ke target."""

    SPEED = 700  # px/detik

    def __init__(self, origin, target, damage, splash_radius, color, enemies_ref):
        self.pos = pygame.Vector2(origin)
        self.target = target
        self.damage = damage
        self.splash_radius = splash_radius
        self.color = color
        self.enemies_ref = enemies_ref
        self.done = False

    def update(self, dt):
        if self.done:
            return
        if self.target is None or not self.target.alive:
            self.done = True
            return

        direction = self.target.pos - self.pos
        dist = direction.length()
        if dist < 8:
            self._apply_damage()
            self.done = True
            return

        direction.normalize_ip()
        self.pos += direction * self.SPEED * dt

    def _apply_damage(self):
        if self.splash_radius and self.splash_radius > 0:
            for e in self.enemies_ref:
                if not e.alive:
                    continue
                if self.target.pos.distance_to(e.pos) <= self.splash_radius:
                    e.hp -= self.damage
        else:
            self.target.hp -= self.damage

    def draw(self, screen):
        if self.done:
            return
        pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), 5)
