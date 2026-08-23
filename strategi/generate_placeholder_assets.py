"""
Script bantu (opsional) untuk membuat gambar placeholder sederhana
untuk setiap prajurit & musuh, supaya game bisa langsung dijalankan
walau belum punya aset gambar sendiri.

Jalankan sekali saja:
    python generate_placeholder_assets.py

Setelah itu kamu bebas mengganti file di assets/images/ dengan
gambar buatanmu sendiri (ukuran disarankan 64x64 px, PNG transparan),
selama nama file & path-nya cocok dengan yang ada di config/units.json
dan config/waves.json.
"""
import json
import math
import os

from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "assets", "images")
os.makedirs(IMG_DIR, exist_ok=True)

SIZE = 64


def save_icon(filename, color, shape="circle", accent=None):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = 6
    if shape == "circle":
        d.ellipse([pad, pad, SIZE - pad, SIZE - pad], fill=color, outline=(20, 20, 20, 255), width=3)
    elif shape == "square":
        d.rounded_rectangle([pad, pad, SIZE - pad, SIZE - pad], radius=10, fill=color, outline=(20, 20, 20, 255), width=3)
    elif shape == "triangle":
        d.polygon([(SIZE / 2, pad), (SIZE - pad, SIZE - pad), (pad, SIZE - pad)], fill=color, outline=(20, 20, 20, 255))
    elif shape == "diamond":
        d.polygon([(SIZE / 2, pad), (SIZE - pad, SIZE / 2), (SIZE / 2, SIZE - pad), (pad, SIZE / 2)], fill=color, outline=(20, 20, 20, 255))

    if accent:
        cx, cy = SIZE / 2, SIZE / 2
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=accent)

    img.save(os.path.join(IMG_DIR, filename))
    print("saved", filename)


def main():
    with open(os.path.join(BASE_DIR, "config", "units.json"), encoding="utf-8") as f:
        units_cfg = json.load(f)
    with open(os.path.join(BASE_DIR, "config", "waves.json"), encoding="utf-8") as f:
        waves_cfg = json.load(f)

    shapes = ["circle", "square", "triangle", "diamond"]
    for i, (key, u) in enumerate(units_cfg["units"].items()):
        color = tuple(u.get("color", [100, 100, 100])) + (255,)
        save_icon(u["image"], color, shapes[i % len(shapes)], accent=(255, 255, 255, 230))

    seen = set()
    for wave in waves_cfg["waves"]:
        for e in wave["enemies"]:
            if e["image"] in seen:
                continue
            seen.add(e["image"])
            color = tuple(e.get("color", [150, 40, 40])) + (255,)
            save_icon(e["image"], color, "triangle", accent=(0, 0, 0, 200))

    # background placeholder
    bg = Image.new("RGB", (1280, 720), (34, 44, 34))
    d = ImageDraw.Draw(bg)
    for x in range(0, 1280, 40):
        d.line([(x, 0), (x, 720)], fill=(38, 48, 38), width=1)
    for y in range(0, 720, 40):
        d.line([(0, y), (1280, y)], fill=(38, 48, 38), width=1)
    bg.save(os.path.join(IMG_DIR, "background.png"))
    print("saved background.png")


if __name__ == "__main__":
    main()
