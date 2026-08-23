"""
Generate all placeholder art assets for the scroll-shooting game.
All images are simple, colorful vector-style sprites drawn with PIL.
Users can freely replace any PNG in assets/img/ as long as the filename
referenced in config/*.json stays the same (or they update the JSON path).
"""
import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

random.seed(42)
OUT = "assets/img"

def new_img(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))

def save(img, name):
    img.save(f"{OUT}/{name}")
    print("saved", name)

def glow_poly(draw, pts, fill, glow=None):
    if glow:
        draw.polygon(pts, fill=glow)
    draw.polygon(pts, fill=fill)

# ---------- Player ship ----------
def make_player():
    w, h = 64, 64
    img = new_img(w, h)
    d = ImageDraw.Draw(img)
    body = (70, 200, 255, 255)
    dark = (20, 90, 160, 255)
    accent = (255, 230, 80, 255)
    # fuselage
    d.polygon([(32, 2), (46, 30), (40, 58), (32, 50), (24, 58), (18, 30)], fill=body)
    d.polygon([(32, 2), (38, 26), (32, 20), (26, 26)], fill=(255, 255, 255, 230))
    # wings
    d.polygon([(18, 30), (2, 46), (14, 50), (24, 40)], fill=dark)
    d.polygon([(46, 30), (62, 46), (50, 50), (40, 40)], fill=dark)
    # cockpit
    d.ellipse([26, 18, 38, 34], fill=(180, 240, 255, 255))
    # engine glow
    d.ellipse([24, 52, 30, 60], fill=accent)
    d.ellipse([34, 52, 40, 60], fill=accent)
    img = img.filter(ImageFilter.SMOOTH)
    save(img, "player.png")

# ---------- Bullets ----------
def make_bullet(name, color):
    w, h = 12, 24
    img = new_img(w, h)
    d = ImageDraw.Draw(img)
    d.ellipse([2, 0, 10, 16], fill=color)
    d.polygon([(2, 10), (10, 10), (6, 24)], fill=color)
    d.ellipse([4, 2, 8, 6], fill=(255, 255, 255, 220))
    save(img, name)

def make_enemy_bullet():
    w, h = 10, 18
    img = new_img(w, h)
    d = ImageDraw.Draw(img)
    d.ellipse([1, 1, 9, 17], fill=(255, 80, 90, 255))
    d.ellipse([3, 4, 7, 8], fill=(255, 200, 200, 230))
    save(img, "bullet_enemy.png")

# ---------- Bomb icon / effect ----------
def make_bomb_icon():
    w, h = 40, 40
    img = new_img(w, h)
    d = ImageDraw.Draw(img)
    d.ellipse([6, 12, 34, 40], fill=(40, 40, 50, 255))
    d.ellipse([10, 16, 30, 36], fill=(70, 70, 85, 255))
    d.line([(24, 10), (30, 2)], fill=(120, 80, 40, 255), width=3)
    d.ellipse([28, 0, 36, 8], fill=(255, 180, 60, 255))
    d.ellipse([30, 2, 34, 6], fill=(255, 240, 150, 255))
    save(img, "bomb_icon.png")

def make_bomb_blast():
    w, h = 256, 256
    img = new_img(w, h)
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2
    for r, col in [(120, (255, 200, 60, 60)), (90, (255, 150, 40, 110)),
                   (60, (255, 220, 120, 170)), (30, (255, 255, 220, 230))]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    save(img, "bomb_blast.png")

# ---------- Enemies (5 types) ----------
def make_enemy1():  # scout - small red triangle drone
    w, h = 44, 44
    img = new_img(w, h)
    d = ImageDraw.Draw(img)
    d.polygon([(22, 40), (4, 8), (22, 16), (40, 8)], fill=(230, 60, 60, 255))
    d.polygon([(22, 40), (14, 14), (22, 20), (30, 14)], fill=(255, 140, 120, 255))
    d.ellipse([18, 6, 26, 14], fill=(255, 240, 200, 255))
    save(img, "enemy1_scout.png")

def make_enemy2():  # fighter - purple with wings
    w, h = 52, 52
    img = new_img(w, h)
    d = ImageDraw.Draw(img)
    d.polygon([(26, 46), (12, 20), (26, 6), (40, 20)], fill=(150, 70, 210, 255))
    d.polygon([(0, 28), (16, 22), (16, 34)], fill=(100, 40, 160, 255))
    d.polygon([(52, 28), (36, 22), (36, 34)], fill=(100, 40, 160, 255))
    d.ellipse([20, 18, 32, 30], fill=(230, 200, 255, 255))
    save(img, "enemy2_fighter.png")

def make_enemy3():  # bomber - green hexagon hull
    w, h = 56, 56
    img = new_img(w, h)
    d = ImageDraw.Draw(img)
    pts = []
    for i in range(6):
        ang = math.pi / 6 + i * math.pi / 3
        pts.append((28 + 24 * math.cos(ang), 28 + 24 * math.sin(ang)))
    d.polygon(pts, fill=(70, 190, 90, 255))
    d.ellipse([16, 16, 40, 40], fill=(30, 130, 60, 255))
    d.ellipse([22, 22, 34, 34], fill=(180, 255, 190, 255))
    save(img, "enemy3_bomber.png")

def make_enemy4():  # interceptor - orange arrow, fast
    w, h = 46, 58
    img = new_img(w, h)
    d = ImageDraw.Draw(img)
    d.polygon([(23, 0), (46, 40), (23, 30), (0, 40)], fill=(255, 150, 30, 255))
    d.polygon([(23, 0), (23, 30), (14, 34), (23, 12)], fill=(255, 200, 110, 255))
    d.polygon([(4, 40), (12, 58), (18, 38)], fill=(200, 100, 10, 255))
    d.polygon([(42, 40), (34, 58), (28, 38)], fill=(200, 100, 10, 255))
    save(img, "enemy4_interceptor.png")

def make_enemy5():  # cruiser - teal saucer, tanky
    w, h = 60, 44
    img = new_img(w, h)
    d = ImageDraw.Draw(img)
    d.ellipse([2, 14, 58, 38], fill=(20, 170, 170, 255))
    d.ellipse([14, 4, 46, 28], fill=(60, 220, 210, 255))
    d.ellipse([24, 12, 36, 24], fill=(230, 255, 250, 255))
    for x in (10, 24, 36, 48):
        d.ellipse([x - 3, 28, x + 3, 34], fill=(255, 230, 100, 255))
    save(img, "enemy5_cruiser.png")

# ---------- Boss ----------
def make_boss():
    w, h = 220, 160
    img = new_img(w, h)
    d = ImageDraw.Draw(img)
    cx = w // 2
    # main hull
    d.polygon([(cx, 10), (w - 10, 60), (w - 40, 150), (40, 150), (10, 60)],
               fill=(160, 20, 40, 255))
    d.polygon([(cx, 30), (w - 30, 65), (w - 55, 130), (55, 130), (30, 65)],
               fill=(210, 40, 60, 255))
    # side cannons
    d.rectangle([0, 60, 26, 100], fill=(90, 10, 20, 255))
    d.rectangle([w - 26, 60, w, 100], fill=(90, 10, 20, 255))
    d.ellipse([2, 74, 20, 92], fill=(255, 210, 60, 255))
    d.ellipse([w - 20, 74, w - 2, 92], fill=(255, 210, 60, 255))
    # core eye
    d.ellipse([cx - 26, 55, cx + 26, 107], fill=(30, 20, 30, 255))
    d.ellipse([cx - 18, 63, cx + 18, 99], fill=(255, 60, 90, 255))
    d.ellipse([cx - 9, 72, cx + 9, 90], fill=(255, 220, 230, 255))
    save(img, "boss.png")

# ---------- Backgrounds ----------
def make_starfield(name, w=480, h=800, seed=1, base=(6, 10, 30)):
    rnd = random.Random(seed)
    img = Image.new("RGBA", (w, h), (*base, 255))
    d = ImageDraw.Draw(img)
    # nebula blobs
    for _ in range(6):
        x, y = rnd.randint(0, w), rnd.randint(0, h)
        r = rnd.randint(60, 160)
        col = rnd.choice([(60, 30, 90, 40), (20, 50, 90, 40), (90, 20, 50, 35)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    img = img.filter(ImageFilter.GaussianBlur(30))
    d = ImageDraw.Draw(img)
    for _ in range(220):
        x, y = rnd.randint(0, w - 1), rnd.randint(0, h - 1)
        s = rnd.choice([1, 1, 1, 2, 2, 3])
        b = rnd.randint(120, 255)
        d.ellipse([x, y, x + s, y + s], fill=(b, b, min(255, b + 20), 255))
    save(img, name)

def make_menu_bg():
    w, h = 480, 800
    make_starfield_base = None
    img = Image.new("RGBA", (w, h), (8, 8, 28, 255))
    d = ImageDraw.Draw(img)
    rnd = random.Random(7)
    for _ in range(8):
        x, y = rnd.randint(0, w), rnd.randint(0, h)
        r = rnd.randint(80, 220)
        col = rnd.choice([(40, 20, 90, 60), (10, 60, 100, 55), (90, 15, 60, 50)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    img = img.filter(ImageFilter.GaussianBlur(40))
    d = ImageDraw.Draw(img)
    for _ in range(260):
        x, y = rnd.randint(0, w - 1), rnd.randint(0, h - 1)
        s = rnd.choice([1, 1, 2, 2, 3])
        b = rnd.randint(140, 255)
        d.ellipse([x, y, x + s, y + s], fill=(b, b, min(255, b + 30), 255))
    save(img, "bg_menu.png")

def make_story_scene(name, mood="opening"):
    w, h = 480, 300
    img = Image.new("RGBA", (w, h), (10, 10, 30, 255))
    d = ImageDraw.Draw(img)
    rnd = random.Random(3 if mood == "opening" else 9)
    for _ in range(5):
        x, y = rnd.randint(0, w), rnd.randint(0, h)
        r = rnd.randint(60, 160)
        col = (rnd.randint(20, 90), rnd.randint(20, 90), rnd.randint(60, 140), 60) if mood == "opening" \
              else (rnd.randint(90, 160), rnd.randint(10, 40), rnd.randint(10, 40), 70)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    img = img.filter(ImageFilter.GaussianBlur(35))
    d = ImageDraw.Draw(img)
    for _ in range(140):
        x, y = rnd.randint(0, w - 1), rnd.randint(0, h - 1)
        s = rnd.choice([1, 1, 2])
        b = rnd.randint(120, 255)
        d.ellipse([x, y, x + s, y + s], fill=(b, b, b, 255))
    # small silhouette fleet / wreckage shapes for flavor
    if mood == "opening":
        for i, x in enumerate([120, 220, 320]):
            y = 150 + (i % 2) * 20
            d.polygon([(x, y), (x + 16, y + 26), (x, y + 18), (x - 16, y + 26)],
                       fill=(90, 180, 255, 220))
    else:
        d.polygon([(200, 190), (280, 170), (260, 230), (220, 240)], fill=(120, 40, 40, 220))
        d.line([(150, 140), (330, 210)], fill=(255, 160, 60, 160), width=3)
    save(img, name)

def make_life_icon():
    w, h = 28, 28
    img = new_img(w, h)
    d = ImageDraw.Draw(img)
    d.polygon([(14, 2), (20, 12), (14, 26), (8, 12)], fill=(70, 200, 255, 255))
    d.polygon([(14, 2), (17, 12), (14, 8), (11, 12)], fill=(255, 255, 255, 230))
    save(img, "life_icon.png")

if __name__ == "__main__":
    make_player()
    make_bullet("bullet_player.png", (120, 230, 255, 255))
    make_enemy_bullet()
    make_bomb_icon()
    make_bomb_blast()
    make_enemy1()
    make_enemy2()
    make_enemy3()
    make_enemy4()
    make_enemy5()
    make_boss()
    make_starfield("bg_game.png", seed=5)
    make_menu_bg()
    make_story_scene("story_opening.png", "opening")
    make_story_scene("story_ending_win.png", "win")
    make_story_scene("story_ending_lose.png", "lose")
    make_life_icon()
    print("DONE")
