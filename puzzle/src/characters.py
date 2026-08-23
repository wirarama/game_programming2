"""Memuat data tokoh dari data/characters.json, dengan fallback gambar otomatis."""
import json
import os

import pygame

from .constants import CHARACTERS_JSON, BASE_DIR

_image_cache = {}


class Character:
    def __init__(self, data):
        self.id = data.get("id", "unknown")
        self.name = data.get("name", self.id)
        self.image_path = data.get("image", "")
        self.color = tuple(data.get("color", [180, 180, 180]))[:3]
        ending = data.get("ending", {}) or {}
        self.ending_title = ending.get("title", f"{self.name} Menang!")
        self.ending_image_path = ending.get("image", self.image_path)
        self.ending_text = ending.get("text", ["Kemenangan yang gemilang!"])

    def _resolve(self, rel_path):
        if not rel_path:
            return None
        if os.path.isabs(rel_path):
            return rel_path
        return os.path.join(BASE_DIR, rel_path)

    def load_image(self, size, ending=False):
        """Mengembalikan pygame.Surface. Jika file tidak ada/gagal dimuat,
        membuat placeholder kotak warna + inisial sehingga game tidak pernah crash."""
        rel = self.ending_image_path if ending else self.image_path
        cache_key = (rel, size)
        if cache_key in _image_cache:
            return _image_cache[cache_key]

        surf = None
        path = self._resolve(rel)
        if path and os.path.isfile(path):
            try:
                loaded = pygame.image.load(path)
                try:
                    loaded = loaded.convert_alpha()
                except pygame.error:
                    pass
                surf = pygame.transform.smoothscale(loaded, size)
            except pygame.error:
                surf = None

        if surf is None:
            surf = self._placeholder(size)

        _image_cache[cache_key] = surf
        return surf

    def _placeholder(self, size):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((*self.color, 255))
        border = max(2, size[0] // 40)
        pygame.draw.rect(surf, (0, 0, 0), surf.get_rect(), border)
        try:
            font_size = max(18, size[1] // 3)
            font = pygame.font.SysFont(None, font_size, bold=True)
            initial = (self.name.strip()[:2] or "?").upper()
            text_color = (255, 255, 255) if sum(self.color) < 400 else (20, 20, 20)
            label = font.render(initial, True, text_color)
            rect = label.get_rect(center=(size[0] // 2, size[1] // 2))
            surf.blit(label, rect)
        except pygame.error:
            pass
        return surf


def load_characters():
    if not os.path.isfile(CHARACTERS_JSON):
        raise FileNotFoundError(
            f"File tokoh tidak ditemukan: {CHARACTERS_JSON}\n"
            "Pastikan data/characters.json ada di folder puzzle/."
        )
    with open(CHARACTERS_JSON, "r", encoding="utf-8") as f:
        raw = json.load(f)
    chars_raw = raw.get("characters", [])
    if not chars_raw:
        raise ValueError("data/characters.json tidak berisi tokoh apa pun.")
    return [Character(c) for c in chars_raw]
