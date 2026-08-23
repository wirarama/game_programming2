"""
Modul untuk memuat semua file konfigurasi JSON (units.json, waves.json,
story.json) dan gambar-gambar terkait.

Karena semua data gameplay & teks disimpan di JSON, mengganti isi
game (biaya prajurit, statistik musuh, teks pembuka/penutup, atau
nama file gambar) tidak memerlukan perubahan kode sama sekali.
"""
import json
import os

import pygame

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
IMAGE_DIR = os.path.join(BASE_DIR, "assets", "images")


def _load_json(name):
    path = os.path.join(CONFIG_DIR, name)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_units_config():
    return _load_json("units.json")


def load_waves_config():
    return _load_json("waves.json")


def load_story_config():
    return _load_json("story.json")


class ImageBank:
    """Memuat & meng-cache gambar dari assets/images sesuai nama file
    yang ditentukan di JSON. Jika gambar tidak ditemukan, otomatis
    membuat gambar pengganti (kotak warna) supaya game tetap berjalan."""

    def __init__(self):
        self._cache = {}

    def get(self, filename, size, fallback_color=(200, 60, 60)):
        key = (filename, size)
        if key in self._cache:
            return self._cache[key]

        surface = None
        if filename:
            path = os.path.join(IMAGE_DIR, filename)
            if os.path.isfile(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    surface = pygame.transform.smoothscale(img, size)
                except pygame.error:
                    surface = None

        if surface is None:
            surface = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.circle(
                surface,
                fallback_color,
                (size[0] // 2, size[1] // 2),
                min(size) // 2,
            )
            pygame.draw.circle(
                surface,
                (20, 20, 20),
                (size[0] // 2, size[1] // 2),
                min(size) // 2,
                2,
            )

        self._cache[key] = surface
        return surface
