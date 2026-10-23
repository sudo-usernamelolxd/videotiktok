"""Pixel-art profile picture: a cell-tower mascot beaming signal. 128x128 -> 1024x1024."""
import math
import os

from PIL import Image, ImageDraw

S = 128
NAVY = (29, 43, 83)
INK = (14, 18, 40)
PURPLE = (126, 37, 83)
PINK = (255, 119, 168)
ORANGE = (255, 163, 0)
YELLOW = (255, 236, 39)
GREEN = (0, 228, 54)
DGREEN = (0, 135, 81)
WHITE = (255, 241, 232)
LGRAY = (194, 195, 199)
DGRAY = (95, 87, 79)
RED = (255, 0, 77)
BLACK = (0, 0, 0)

img = Image.new("RGB", (S, S), INK)
d = ImageDraw.Draw(img)

# sky bands with dithered seams
bands = [(0, INK), (30, NAVY), (62, (40, 30, 90)), (82, PURPLE), (98, (190, 60, 110))]
for i, (y, c) in enumerate(bands):
    y1 = bands[i + 1][0] if i + 1 < len(bands) else S
    d.rectangle([0, y, S, y1], fill=c)
    if i + 1 < len(bands):
        for x in range(0, S, 2):
            d.point((x + (y1 % 2), y1), fill=bands[i + 1][1])
for x, y in [(12, 10), (30, 22), (100, 14), (114, 30), (20, 44), (108, 52), (64, 8), (84, 26)]:
    d.point((x, y), fill=WHITE)

# striped retro sun behind the tower
cx, cy, r = 64, 92, 30
for yy in range(-r, 1):
    if yy > -12 and (yy // 3) % 2 == 0:
        continue
    w = int(math.sqrt(r * r - yy * yy))
    d.line([cx - w, cy + yy, cx + w, cy + yy], fill=YELLOW if yy < -14 else ORANGE)

# ground + rails
d.rectangle([0, 104, S, S], fill=INK)
d.rectangle([0, 104, S, 105], fill=DGREEN)
for x in range(0, S, 8):
    d.rectangle([x, 114, x + 4, 117], fill=(171, 82, 54))
d.line([0, 115, S, 115], fill=LGRAY)

# signal rings (upper arcs)
top = 40
for k, rad in enumerate([22, 34, 46]):
    col = GREEN if k < 2 else DGREEN
    for ang in range(205, 336, 3 if k < 2 else 5):
        a = math.radians(ang)
        d.point((int(64 + rad * math.cos(a)), int(top + rad * math.sin(a))), fill=col)
        d.point((int(64 + rad * math.cos(a)), int(top + 1 + rad * math.sin(a))), fill=col)

# tower lattice
base = 104
d.line([46, base, 64, top], fill=LGRAY, width=2)
d.line([82, base, 64, top], fill=LGRAY, width=2)
for k in range(1, 6):
    y = base - int((base - top) * k / 6)
    hw = int(18 * (1 - k / 6))
    d.line([64 - hw, y, 64 + hw, y], fill=LGRAY)
    y2 = base - int((base - top) * (k + 1) / 6)
    hw2 = int(18 * (1 - (k + 1) / 6))
    d.line([64 - hw, y, 64 + hw2, y2], fill=DGRAY)
d.line([64, top, 64, top - 10], fill=LGRAY, width=2)
d.rectangle([63, top - 13, 65, top - 11], fill=RED)

# mascot face: a little screen box on the tower
d.rectangle([50, 52, 78, 72], fill=BLACK)
d.rectangle([51, 53, 77, 71], fill=WHITE)
d.rectangle([53, 55, 75, 69], fill=NAVY)
d.rectangle([57, 58, 59, 62], fill=GREEN)   # eyes
d.rectangle([69, 58, 71, 62], fill=GREEN)
d.point((58, 58), fill=WHITE)
d.point((70, 58), fill=WHITE)
d.line([60, 65, 68, 65], fill=GREEN)        # smile
d.point((59, 64), fill=GREEN)
d.point((69, 64), fill=GREEN)
d.point((55, 64), fill=PINK)                # blush
d.point((73, 64), fill=PINK)

# antenna panels like little arms
d.rectangle([44, 56, 47, 66], fill=WHITE)
d.rectangle([81, 56, 84, 66], fill=WHITE)

out = os.path.join(os.path.dirname(__file__), "pfp.png")
img.resize((1024, 1024), Image.NEAREST).save(out)
print(out)
