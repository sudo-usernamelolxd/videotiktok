"""Renders the pixel-art video at 270x480 and upscales it 4x to 1080x1920.

Needs build/timeline.json and build/mix.wav from audio.py.
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

from pixelfont import draw_text, draw_text_centered, text_width
from script import CAPTIONS

W, H = 270, 480
SCALE = 4
FPS = 30
BUILD = os.path.join(os.path.dirname(__file__), "build")
OUT = os.path.join(os.path.dirname(__file__), "..", "phone-handover-train.mp4")

# PICO-8 palette
BLACK = (0, 0, 0)
NAVY = (29, 43, 83)
PURPLE = (126, 37, 83)
DGREEN = (0, 135, 81)
BROWN = (171, 82, 54)
DGRAY = (95, 87, 79)
LGRAY = (194, 195, 199)
WHITE = (255, 241, 232)
RED = (255, 0, 77)
ORANGE = (255, 163, 0)
YELLOW = (255, 236, 39)
GREEN = (0, 228, 54)
BLUE = (41, 173, 255)
LAV = (131, 118, 156)
PINK = (255, 119, 168)
PEACH = (255, 204, 170)
INK = (14, 18, 40)

GROUND_Y = 300

TL = json.load(open(os.path.join(BUILD, "timeline.json")))
SC = {s["name"]: s for s in TL["scenes"]}


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def line_t(scene, i):
    return SC[scene]["lines"][i]["start"], SC[scene]["lines"][i]["end"]


def prog(t, a, b):
    return clamp((t - a) / max(1e-6, b - a))


# ------------------------------------------------------------- primitives
rng = np.random.default_rng(42)
STARS = [(int(rng.integers(0, W)), int(rng.integers(0, 200)), float(rng.uniform(0, 6.28))) for _ in range(60)]


def sky(d, t, top=NAVY, bands=(NAVY, (40, 30, 90), PURPLE, (190, 60, 110), ORANGE), y0=0, y1=GROUND_Y):
    n = len(bands)
    h = y1 - y0
    for i, c in enumerate(bands):
        a = y0 + int(h * (i / n) ** 0.7)
        b = y0 + int(h * ((i + 1) / n) ** 0.7)
        d.rectangle([0, a, W, b], fill=c)
        # dithered seam
        if i + 1 < n:
            for x in range(0, W, 2):
                d.point((x + (b % 2), b), fill=bands[i + 1])
                d.point((x + ((b + 1) % 2), b - 1), fill=bands[i + 1])
    for (x, y, ph) in STARS:
        if y < y0 + h * 0.45 and math.sin(t * 3 + ph) > -0.3:
            d.point((x, y), fill=WHITE if math.sin(t * 3 + ph) > 0.6 else LGRAY)


def sun(d, cx, cy, r):
    for y in range(-r, r + 1):
        if y > r * 0.15 and (y // 3) % 2 == 0:
            continue  # retro stripes
        w = int(math.sqrt(max(0, r * r - y * y)))
        d.line([cx - w, cy + y, cx + w, cy + y], fill=YELLOW if y < 0 else ORANGE)


def hills(d, offset, base, amp, color, freq=0.03, seed=0.0):
    for x in range(0, W, 2):
        wx = x + offset
        h = amp * (0.6 * math.sin(wx * freq + seed) + 0.4 * math.sin(wx * freq * 2.3 + seed * 2))
        top = int(base - abs(h)) // 2 * 2
        d.rectangle([x, top, x + 1, GROUND_Y], fill=color)


def ground(d, scroll):
    d.rectangle([0, GROUND_Y, W, H], fill=INK)
    d.rectangle([0, GROUND_Y, W, GROUND_Y + 2], fill=DGREEN)
    # sleepers + rails
    ry = GROUND_Y + 16
    for x in range(-20, W + 20, 10):
        sx = x - int(scroll) % 10
        d.rectangle([sx, ry - 1, sx + 5, ry + 3], fill=BROWN)
    d.line([0, ry, W, ry], fill=LGRAY)
    d.line([0, ry + 2, W, ry + 2], fill=DGRAY)
    # gravel speckle
    for i in range(40):
        gx = (i * 37 - int(scroll * 1.0)) % W
        gy = GROUND_Y + 5 + (i * 13) % 9
        d.point((gx, gy), fill=DGRAY)


def tower(d, x, base, h=80, color=LGRAY, light=True, t=0.0, label=None, lcol=WHITE):
    top = base - h
    d.line([x - 10, base, x, top], fill=color)
    d.line([x + 10, base, x, top], fill=color)
    for k in range(1, 6):
        yy = base - int(h * k / 6)
        hw = int(10 * (1 - k / 6))
        d.line([x - hw, yy, x + hw, yy], fill=color)
        if k < 5:
            yy2 = base - int(h * (k + 1) / 6)
            hw2 = int(10 * (1 - (k + 1) / 6))
            d.line([x - hw, yy, x + hw2, yy2], fill=DGRAY)
    # antenna panels
    d.rectangle([x - 4, top + 2, x - 2, top + 10], fill=WHITE)
    d.rectangle([x + 2, top + 2, x + 4, top + 10], fill=WHITE)
    d.line([x, top, x, top - 6], fill=color)
    if light:
        d.point((x, top - 7), fill=RED if int(t * 2 + x) % 2 == 0 else PURPLE)
    if label:
        draw_text_centered(d, x, base + 4, label, lcol, 1, outline=BLACK)
    return x, top + 4


def rings(d, cx, cy, t, color, n=3, speed=30, maxr=60, period=None):
    period = period or maxr / speed
    for k in range(n):
        r = ((t + k * period / n) % period) * speed
        if r < 3:
            continue
        a = 1 - r / maxr
        if a <= 0:
            continue
        col = color if a > 0.4 else tuple(int(c * 0.6) for c in color)
        # draw upper arcs only, pixel style (dotted when fading)
        for ang in range(200, 341, 4 if a > 0.4 else 8):
            rad = math.radians(ang)
            d.point((int(cx + r * math.cos(rad)), int(cy + r * math.sin(rad))), fill=col)


def train(d, x, y, cars=3, t=0.0, antenna=False):
    """Draws a side-view train. y = bottom of wheels."""
    car_w, car_h = 70, 26
    for c in range(cars):
        x0 = x + c * (car_w + 3)
        top = y - car_h - 4
        if c == cars - 1:
            # nose
            d.polygon([(x0 + car_w - 12, top), (x0 + car_w + 10, y - 10), (x0 + car_w + 10, y - 4), (x0 + car_w - 12, y - 4)], fill=WHITE)
            d.polygon([(x0 + car_w - 10, top + 3), (x0 + car_w + 4, top + 12), (x0 + car_w - 10, top + 12)], fill=BLUE)
        d.rectangle([x0, top, x0 + car_w - 1 - (12 if c == cars - 1 else 0), y - 4], fill=WHITE)
        d.rectangle([x0, y - 12, x0 + car_w - 1 + (10 if c == cars - 1 else 0), y - 9], fill=RED)
        for wx in range(x0 + 5, x0 + car_w - 16, 11):
            d.rectangle([wx, top + 4, wx + 7, top + 10], fill=NAVY)
            d.point((wx + 1, top + 5), fill=BLUE)
        d.rectangle([x0 + 3, y - 4, x0 + 16, y - 1], fill=DGRAY)
        d.rectangle([x0 + car_w - 18, y - 4, x0 + car_w - 5, y - 1], fill=DGRAY)
        if c < cars - 1:
            d.rectangle([x0 + car_w, top + 6, x0 + car_w + 2, y - 6], fill=DGRAY)
    # pantograph on middle car
    px = x + (car_w + 3) + 30
    top = y - car_h - 4
    d.line([px, top, px + 8, top - 8], fill=LGRAY)
    d.line([px + 8, top - 8, px + 2, top - 13], fill=LGRAY)
    d.line([px - 2, top - 13, px + 10, top - 13], fill=LGRAY)
    if antenna:
        ax = x + 25
        d.rectangle([ax - 1, top - 6, ax + 1, top - 1], fill=YELLOW)
        d.rectangle([ax - 4, top - 8, ax + 4, top - 6], fill=YELLOW)
        return ax, top - 8
    return None


def catenary(d, scroll):
    wy = GROUND_Y - 44
    d.line([0, wy, W, wy], fill=DGRAY)
    for x in range(-60, W + 60, 90):
        px = x - int(scroll) % 90
        d.line([px, wy - 6, px, GROUND_Y], fill=DGRAY)
        d.line([px, wy - 4, px + 8, wy - 4], fill=DGRAY)


def speedlines(d, t):
    for i in range(10):
        y = 210 + (i * 23) % 90
        x = int((W - ((t * 600 + i * 97) % (W + 80))))
        d.line([x, y, x + 18 + (i % 3) * 8, y], fill=WHITE if i % 2 else PEACH)


def phone(d, x, y, w=60, h=110, screen=NAVY):
    d.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=DGRAY)
    d.rounded_rectangle([x + 1, y + 1, x + w - 1, y + h - 1], radius=5, fill=BLACK)
    d.rectangle([x + 4, y + 8, x + w - 4, y + h - 8], fill=screen)
    d.rectangle([x + w // 2 - 6, y + 3, x + w // 2 + 6, y + 4], fill=DGRAY)
    return x + 4, y + 8, x + w - 4, y + h - 8


def bars(d, x, y, level, color=GREEN, n=4, bw=3, gap=1, hmax=12):
    for i in range(n):
        bh = int(hmax * (i + 1) / n)
        col = color if i < level else DGRAY
        d.rectangle([x + i * (bw + gap), y + hmax - bh, x + i * (bw + gap) + bw - 1, y + hmax], fill=col)


def dashed(d, p0, p1, color, on=3, off=3, phase=0):
    x0, y0 = p0
    x1, y1 = p1
    L = max(1, int(math.hypot(x1 - x0, y1 - y0)))
    for i in range(L):
        if (i + int(phase)) % (on + off) < on:
            f = i / L
            d.point((int(x0 + (x1 - x0) * f), int(y0 + (y1 - y0) * f)), fill=color)


def title(d, lines, t, t0=0.0, color=YELLOW, y=26, scale=3):
    p = clamp((t - t0) / 0.25)
    if p <= 0:
        return
    yy = y - int((1 - ease(p)) * 30)
    for i, s in enumerate(lines):
        draw_text_centered(d, W // 2, yy + i * (8 * scale), s, color, scale, outline=BLACK, shadow=PURPLE)


def box(d, x0, y0, x1, y1, fill=NAVY, border=WHITE):
    d.rectangle([x0, y0, x1, y1], fill=border)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=BLACK)
    d.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], fill=fill)


# ------------------------------------------------------------- scenes
def scene_hook(img, d, t):
    s = SC["hook"]
    lt = t - s["start"]
    scroll = lt * 260
    sky(d, lt)
    sun(d, 200, 150, 34)
    hills(d, scroll * 0.1, 235, 30, PURPLE, 0.02, 1.0)
    hills(d, scroll * 0.3, 270, 22, NAVY, 0.035, 2.0)
    ground(d, scroll)
    # towers passing by
    spacing = 230
    passed = int((scroll + 135) // spacing)
    for k in range(-1, 3):
        tx = int(k * spacing - (scroll % spacing)) + 135 + spacing // 2
        idx = passed + k
        serving = abs(tx - 135) < spacing // 2
        _, ty = tower(d, tx, GROUND_Y + 6, 95, LGRAY, t=lt)
        rings(d, tx, ty, lt, GREEN if serving else LAV, n=3, maxr=70)
    catenary(d, scroll)
    train(d, 10, GROUND_Y + 15, cars=3, t=lt)
    speedlines(d, lt)

    # HUD
    tid = 14 + passed
    box(d, 10, 108, 118, 140, fill=NAVY)
    bars(d, 16, 114, 4 if (scroll % spacing) > 30 else 3)
    draw_text(d, 36, 113, f"TOWER #{tid}", WHITE)
    draw_text(d, 36, 124, "5G  ~ 300KM/H", GREEN)
    flash = (scroll % spacing) < 25
    if flash and lt > 0.5:
        draw_text(d, 124, 118, "SWITCH!", YELLOW, 1, outline=BLACK)

    a, b = line_t("hook", 0)
    c, e = line_t("hook", 2)
    if t < c:
        title(d, ["300 KM/H", "AND STILL", "ONLINE?"], lt, 0.0)
    else:
        title(d, ["HOW DOES IT", "NOT DROP?"], t, c, color=PINK)


HEX_R = 26


def hex_centers():
    cs = []
    dx = HEX_R * math.sqrt(3)
    dy = HEX_R * 1.5
    for row in range(-1, 8):
        for col in range(-1, 8):
            cx = col * dx + (dx / 2 if row % 2 else 0) - 10
            cy = 118 + row * dy
            cs.append((cx, cy))
    return cs


HEXES = hex_centers()


def hex_poly(cx, cy, r):
    return [(cx + r * math.cos(math.radians(60 * k + 30)), cy + r * math.sin(math.radians(60 * k + 30))) for k in range(6)]


def scene_cells(img, d, t):
    s = SC["cells"]
    lt = t - s["start"]
    dur = s["end"] - s["start"]
    d.rectangle([0, 0, W, H], fill=INK)
    # map bg checker
    for y in range(100, 340, 8):
        for x in range(0, W, 8):
            if (x // 8 + y // 8) % 2 == 0:
                d.rectangle([x, y, x + 7, y + 7], fill=(20, 26, 56))
    # track path (wavy)
    def path(u):
        x = -10 + u * (W + 20)
        y = 225 + 22 * math.sin(u * 5.0)
        return x, y
    pts = [path(u / 60) for u in range(61)]
    u = clamp(lt / (dur - 0.3)) * 0.92 + 0.04
    px, py = path(u)
    serving = min(HEXES, key=lambda c: (c[0] - px) ** 2 + (c[1] - py) ** 2)
    reveal = clamp(lt / 1.2)
    for i, (cx, cy) in enumerate(HEXES):
        if cy > 345 or cy < 95:
            continue
        if (i * 0.037) % 1 > reveal:
            continue
        poly = hex_poly(cx, cy, HEX_R - 1)
        if (cx, cy) == serving:
            d.polygon(poly, fill=(0, 80, 50), outline=GREEN)
        else:
            d.polygon(poly, outline=LAV)
    d.line(pts, fill=BROWN, width=3)
    d.line(pts, fill=PEACH, width=1)
    for (cx, cy) in HEXES:
        if 95 < cy < 345:
            on = (cx, cy) == serving
            d.rectangle([cx - 2, cy - 2, cx + 2, cy + 2], fill=GREEN if on else LGRAY)
            d.line([cx, cy - 2, cx, cy - 6], fill=GREEN if on else LGRAY)
    # link
    dashed(d, (px, py), serving, GREEN, phase=-lt * 20)
    # train marker
    d.rectangle([px - 5, py - 4, px + 5, py + 4], fill=WHITE)
    d.rectangle([px - 4, py - 3, px + 4, py + 3], fill=RED)
    d.point((px + 3, py - 1), fill=YELLOW)
    # count handovers
    count = 0
    prev = None
    for k in range(0, 101):
        uu = 0.04 + 0.92 * clamp(k / 100 * (lt / (dur - 0.3)))
        x, y = path(uu)
        sv = min(HEXES, key=lambda c: (c[0] - x) ** 2 + (c[1] - y) ** 2)
        if prev is not None and sv != prev:
            count += 1
        prev = sv
    d.rectangle([0, 340, W, H], fill=INK)
    box(d, 70, 300, 200, 320, fill=NAVY, border=GREEN)
    draw_text_centered(d, W // 2, 307, f"HANDOVERS: {count}", GREEN)
    title(d, ["THE NETWORK", "= CELLS"], lt, 0.0, color=BLUE)


TA = (45, GROUND_Y + 6)
TB = (225, GROUND_Y + 6)


def dbm_a(u):
    return -68 - 30 * u


def dbm_b(u):
    return -104 + 32 * u


def level(dbm):
    return 4 if dbm > -75 else 3 if dbm > -85 else 2 if dbm > -95 else 1


def scene_measure(img, d, t):
    s = SC["measure"]
    lt = t - s["start"]
    dur = s["end"] - s["start"]
    u = clamp(lt / dur)
    sky(d, lt, bands=(NAVY, (30, 36, 80), (50, 40, 100)))
    hills(d, lt * 20, 280, 14, (20, 30, 60), 0.04)
    ground(d, lt * 40)
    _, tay = tower(d, *TA, 100, LGRAY, t=lt, label="TOWER A", lcol=GREEN)
    _, tby = tower(d, *TB, 100, LGRAY, t=lt, label="TOWER B", lcol=ORANGE)
    rings(d, TA[0], tay, lt, GREEN, maxr=90, speed=40)
    rings(d, TB[0], tby, lt + 0.5, ORANGE, maxr=90, speed=40)

    # phone in the middle
    sx0, sy0, sx1, sy1 = phone(d, 105, 150, 60, 110)
    a, b = dbm_a(u), dbm_b(u)
    draw_text(d, sx0 + 3, sy0 + 4, "SCAN", BLUE)
    if int(lt * 4) % 2 == 0:
        d.point((sx1 - 4, sy0 + 6), fill=RED)
    for k, (lab, v, col) in enumerate([("A", a, GREEN), ("B", b, ORANGE)]):
        yy = sy0 + 18 + k * 34
        draw_text(d, sx0 + 3, yy, lab, col)
        bars(d, sx0 + 12, yy - 4, level(v), col)
        draw_text(d, sx0 + 3, yy + 12, f"{int(v)}DBM", WHITE)
    # waves from phone (listening)
    for k in range(3):
        r = ((lt * 25 + k * 8) % 24)
        d.arc([135 - r, 140 - r, 135 + r, 140 + r], 230, 310, fill=BLUE)

    # reports
    r0, r1 = line_t("measure", 1)
    if t > r0 - 0.2:
        for k in range(4):
            f = ((t - r0) * 0.9 + k * 0.25) % 1
            x = 105 + (TA[0] + 10 - 105) * f
            y = 190 + (tay + 20 - 190) * f - math.sin(f * math.pi) * 25
            d.rectangle([x - 3, y - 2, x + 3, y + 2], fill=YELLOW)
            d.point((x - 1, y), fill=BLACK)
            d.point((x + 1, y), fill=BLACK)
        draw_text_centered(d, 70, 280, "REPORT >", YELLOW, outline=BLACK)
    d.rectangle([0, 340, W, H], fill=INK)
    if t < r0:
        title(d, ["ALWAYS", "LISTENING"], lt, 0.0, color=BLUE)
    else:
        title(d, ["REPORTS", "BACK HOME"], t, r0, color=YELLOW)


def scene_graph(img, d, t):
    s = SC["graph"]
    lt = t - s["start"]
    l0, l1 = line_t("graph", 0)
    h0, h1 = line_t("graph", 1)
    d.rectangle([0, 0, W, H], fill=INK)
    gx0, gy0, gx1, gy1 = 30, 112, 252, 300
    box(d, gx0 - 6, gy0 - 6, gx1 + 6, gy1 + 22, fill=(16, 22, 50), border=LAV)
    for y in range(gy0, gy1 + 1, 20):
        for x in range(gx0, gx1, 4):
            d.point((x, y), fill=(45, 50, 90))
    draw_text(d, gx0, gy1 + 8, "TIME >", LAV)
    draw_text(d, gx1 - text_width("SIGNAL"), gy1 + 8, "SIGNAL", LAV)

    def ymap(v):
        return gy0 + (-v - 60) / 50 * (gy1 - gy0)

    def xmap(u):
        return gx0 + u * (gx1 - gx0)

    p = clamp((t - l0 + 0.3) / (l1 - l0 + 0.2)) * 0.82 + 0.0
    if t >= h0 - 0.1:
        p = 0.82 + 0.18 * clamp((t - h0) / 1.5)
    N = 80
    ptsA, ptsB, ptsO = [], [], []
    for i in range(N + 1):
        u = i / N
        if u > p:
            break
        ptsA.append((xmap(u), ymap(dbm_a(u))))
        ptsB.append((xmap(u), ymap(dbm_b(u))))
        ptsO.append((xmap(u), ymap(dbm_a(u) + 3)))
    for i in range(0, len(ptsO) - 1, 2):
        d.line([ptsO[i], ptsO[i + 1]], fill=PINK)
    if len(ptsA) > 1:
        d.line(ptsA, fill=GREEN, width=2)
        d.line(ptsB, fill=ORANGE, width=2)
        draw_text(d, ptsA[-1][0] + 3, ptsA[-1][1] - 3, "A", GREEN, outline=BLACK)
        draw_text(d, ptsB[-1][0] + 3, ptsB[-1][1] - 3, "B", ORANGE, outline=BLACK)
    if p > 0.15:
        draw_text(d, gx0 + 6, ymap(dbm_a(0.12) + 3) - 12, "A + 3 DB", PINK)
    # crossing point B = A + 3  ->  u = 0.6  ;  time to trigger until 0.8
    ucross = (104 - 71) / 62
    if p > ucross:
        xc = xmap(ucross)
        d.line([xc, gy0, xc, gy1], fill=YELLOW)
        fill = clamp((p - ucross) / (0.82 - ucross))
        bx0, bx1 = int(xc), int(xmap(0.82))
        d.rectangle([bx0, gy0 + 2, bx1, gy0 + 10], outline=YELLOW)
        d.rectangle([bx0 + 1, gy0 + 3, bx0 + 1 + int((bx1 - bx0 - 2) * fill), gy0 + 9], fill=YELLOW)
        draw_text(d, bx0 - 2, gy0 + 14, "TIME TO", YELLOW, outline=BLACK)
        draw_text(d, bx0 - 2, gy0 + 23, "TRIGGER", YELLOW, outline=BLACK)
    d.rectangle([0, 340, W, H], fill=INK)
    if t >= h0 - 0.1:
        k = t - h0
        if k < 0.25 and int(k * 20) % 2 == 0:
            d.rectangle([0, 0, W, 340], outline=WHITE, width=4)
        sc = 4 if k > 0.12 else 5
        draw_text_centered(d, W // 2, 190, "HANDOVER!", RED if int(k * 6) % 2 else YELLOW, sc, outline=BLACK, shadow=PURPLE)
        title(d, ["DECISION", "MADE"], t, h0, color=RED)
    else:
        title(d, ["B BEATS A", "BY 3 DB"], lt, 0.0, color=ORANGE)


def scene_handover(img, d, t):
    s = SC["handover"]
    lt = t - s["start"]
    a0, a1 = line_t("handover", 0)
    b0, b1 = line_t("handover", 1)
    c0, c1 = line_t("handover", 2)
    jump = TL["jump"]
    sky(d, lt, bands=(NAVY, (30, 36, 80), (50, 40, 100)))
    ground(d, 0)
    A = (55, GROUND_Y + 6)
    B = (215, GROUND_Y + 6)
    _, ay = tower(d, *A, 110, LGRAY, t=lt, label="OLD", lcol=GREEN)
    _, by = tower(d, *B, 110, LGRAY, t=lt, label="NEW", lcol=ORANGE)
    ph = (125, 238)
    sx0, sy0, sx1, sy1 = phone(d, ph[0], ph[1], 22, 40, screen=NAVY)
    pc = (ph[0] + 11, ph[1] + 6)
    switched = t >= jump
    # links
    if not switched:
        d.line([pc, (A[0], ay + 4)], fill=GREEN, width=2)
        bars(d, sx0 + 1, sy0 + 2, 3, GREEN, bw=2, hmax=8)
    else:
        dashed(d, pc, (A[0], ay + 4), DGRAY)
        d.line([pc, (B[0], by + 4)], fill=GREEN, width=2)
        bars(d, sx0 + 1, sy0 + 2, 4, GREEN, bw=2, hmax=8)
    if t < jump and t > a0:
        dashed(d, pc, (B[0], by + 4), ORANGE, phase=-lt * 15)
    # reserved slot
    if t > a0 + 0.6:
        pr = clamp((t - a0 - 0.6) / 1.5)
        bx, byy = B[0] - 34, by - 40
        box(d, bx, byy, bx + 50, byy + 24, fill=NAVY, border=ORANGE)
        draw_text(d, bx + 5, byy + 4, "SLOT", ORANGE)
        for k in range(4):
            col = ORANGE if k < int(pr * 4 + 0.001) else DGRAY
            d.rectangle([bx + 5 + k * 10, byy + 13, bx + 12 + k * 10, byy + 19], fill=col)
        if pr >= 1 and int(lt * 3) % 2 == 0:
            draw_text(d, bx + 30, byy + 4, "OK", GREEN)
    # forwarding packets old -> new along the backhaul (an arc above)
    if b0 - 0.2 < t < jump + 0.8:
        for k in range(5):
            f = ((t - b0) * 0.7 + k / 5) % 1
            x = A[0] + (B[0] - A[0]) * f
            y = ay - 6 - math.sin(f * math.pi) * 40
            d.rectangle([x - 3, y - 3, x + 3, y + 3], fill=YELLOW)
            d.rectangle([x - 2, y - 2, x + 2, y + 2], fill=ORANGE)
        draw_text_centered(d, W // 2, ay - 62 + 30, "DATA", YELLOW, outline=BLACK)
    # the jump
    if switched:
        k = t - jump
        if k < 0.3:
            r = int(k * 200)
            d.ellipse([pc[0] - r, pc[1] - r, pc[0] + r, pc[1] + r], outline=WHITE)
        # stopwatch comparison
        if k > 0.6:
            box(d, 22, 290, 248, 334, fill=NAVY, border=LAV)
            draw_text(d, 30, 297, "SWITCH GAP", GREEN)
            draw_text(d, 30, 317, "ONE BLINK", PINK)
            g = ease((k - 0.6) / 1.2)
            d.rectangle([110, 297, 110 + int(5 * g), 304], fill=GREEN)
            draw_text(d, 120, 297, "~30-50 MS", GREEN)
            d.rectangle([110, 317, 110 + int(130 * g), 324], fill=PINK)
            draw_text(d, 190, 309, "~300 MS", PINK, outline=BLACK)
    d.rectangle([0, 340, W, H], fill=INK)
    if t < b0:
        title(d, ["STEP 1:", "PREPARE"], t, a0, color=ORANGE)
    elif t < c0:
        title(d, ["STEP 2:", "FORWARD"], t, b0, color=YELLOW)
    else:
        title(d, ["STEP 3:", "JUMP!"], t, c0, color=GREEN)


def scene_train(img, d, t):
    s = SC["train"]
    lt = t - s["start"]
    l2, _ = line_t("train", 1)
    scroll = lt * 420
    sky(d, lt, bands=(NAVY, (40, 30, 90), PURPLE, (190, 60, 110)))
    hills(d, scroll * 0.15, 250, 26, (60, 30, 80), 0.025, 4.0)
    if t >= l2:
        # stretched elongated cells along the line
        for k in range(-1, 4):
            cx = int(k * 200 - (scroll * 0.5) % 200) + 60
            d.ellipse([cx - 95, 200, cx + 95, 300], outline=GREEN if k % 2 else BLUE)
    hills(d, scroll * 0.35, 280, 16, NAVY, 0.04, 1.0)
    ground(d, scroll)
    if t >= l2:
        for k in range(-1, 4):
            tx = int(k * 100 - (scroll * 0.5) % 100) + 40
            tower(d, tx, GROUND_Y + 2, 60, LGRAY, t=lt)
    catenary(d, scroll)
    ant = train(d, 10, GROUND_Y + 15, cars=3, t=lt, antenna=True)
    speedlines(d, lt)
    # doppler rings from the antenna: centres drift left with the world
    ax, ay = ant
    period = 0.18
    for k in range(10):
        age = (lt % period) + k * period
        r = age * 120
        cx = ax - age * 70
        if r > 150:
            continue
        col = BLUE if k % 2 == 0 else (90, 140, 230)
        d.arc([cx - r, ay - r, cx + r, ay + r], 200, 340, fill=col)
    if t < l2:
        box(d, 150, 110, 260, 140, fill=NAVY, border=BLUE)
        draw_text(d, 156, 116, "FREQ SHIFT", BLUE)
        draw_text(d, 156, 127, "+/- ~1 KHZ", WHITE)
    else:
        box(d, 10, 108, 132, 128, fill=NAVY, border=YELLOW)
        draw_text(d, 16, 114, "ONBOARD REPEATER", YELLOW)
        d.line([ax, ay - 2, 60, 128], fill=YELLOW)
    d.rectangle([0, 340, W, H], fill=INK)
    if t < l2:
        title(d, ["DOPPLER", "EFFECT"], lt, 0.0, color=BLUE)
    else:
        title(d, ["TOWERS ON", "THE TRACKS"], t, l2, color=GREEN)


def scene_outro(img, d, t):
    s = SC["outro"]
    lt = t - s["start"]
    l2, _ = line_t("outro", 1)
    if t < l2:
        scroll = lt * 300
        sky(d, lt)
        sun(d, 70, 160, 28)
        hills(d, scroll * 0.1, 240, 28, PURPLE, 0.02, 1.0)
        ground(d, scroll)
        catenary(d, scroll)
        train(d, 10, GROUND_Y + 15, cars=3, t=lt)
        # tunnel mountain slides in from the right and swallows the train
        mx = int(W + 40 - lt * 65)
        d.polygon([(mx - 60, GROUND_Y + 20), (mx + 40, 150), (mx + 400, 150), (mx + 400, GROUND_Y + 20)], fill=DGRAY)
        d.polygon([(mx - 40, GROUND_Y + 20), (mx + 45, 170), (mx + 400, 170), (mx + 400, GROUND_Y + 20)], fill=(70, 64, 60))
        d.rectangle([mx, GROUND_Y - 20, mx + 400, GROUND_Y + 18], fill=BLACK)
        d.arc([mx - 2, GROUND_Y - 34, mx + 44, GROUND_Y + 10], 180, 270, fill=LGRAY)
        inside = mx < 200
        box(d, 10, 108, 118, 130, fill=NAVY, border=RED if inside else GREEN)
        bars(d, 16, 112, 0 if inside else 4, RED if inside else GREEN)
        draw_text(d, 36, 115, "NO SERVICE" if inside else "TOWER #31", RED if inside else WHITE)
        d.rectangle([0, 340, W, H], fill=INK)
        title(d, ["BLAME THE", "TUNNEL"], lt, 0.0, color=RED)
    else:
        k = t - l2
        d.rectangle([0, 0, W, H], fill=INK)
        sky(d, lt, bands=(INK, NAVY, (40, 30, 90), PURPLE), y0=0, y1=340)
        for i in range(12):
            y = 340 - i * i * 2
            d.line([0, y, W, y], fill=PINK if i % 3 == 0 else PURPLE)
        for x in range(-300, W + 300, 30):
            d.line([W // 2 + (x - W // 2) * 0.15, 260, x, 340], fill=PURPLE)
        d.rectangle([0, 340, W, H], fill=INK)
        for i, ln in enumerate(["FOLLOW", "FOR MORE", "TECH", "NOBODY", "EXPLAINS"]):
            if k > i * 0.18:
                col = [YELLOW, YELLOW, GREEN, BLUE, PINK][i]
                draw_text_centered(d, W // 2, 104 + i * 32, ln, col, 4, outline=BLACK, shadow=PURPLE)
        if int(k * 2.5) % 2 == 0:
            draw_text_centered(d, W // 2, 278, "PRESS + TO CONTINUE", WHITE, 1)
        # little tower mascot
        tower(d, W // 2, 330, 36, LGRAY, t=lt)
        rings(d, W // 2, 298, lt, GREEN, maxr=40)


SCENE_FN = {
    "hook": scene_hook, "cells": scene_cells, "measure": scene_measure, "graph": scene_graph,
    "handover": scene_handover, "train": scene_train, "outro": scene_outro,
}


# ------------------------------------------------------------- captions
def caption_chunks():
    chunks = []
    for s in TL["scenes"]:
        for ln in s["lines"]:
            text = ln["text"]
            for k, v in CAPTIONS.items():
                text = text.replace(k, v)
            words = text.split()
            groups, cur = [], []
            for w in words:
                trial = " ".join(cur + [w])
                if cur and (len(trial) > 18 or cur[-1][-1] in ".?!,"):
                    groups.append(cur)
                    cur = [w]
                else:
                    cur.append(w)
            if cur:
                groups.append(cur)
            total = sum(len(" ".join(g)) + 2 for g in groups)
            t = ln["start"]
            dur = ln["end"] - ln["start"]
            for g in groups:
                s_ = " ".join(g)
                dt = dur * (len(s_) + 2) / total
                chunks.append((t, t + dt, s_))
                t += dt
    return chunks


CHUNKS = caption_chunks()
EMPH = {"HANDOVER", "TOWER", "CELLS", "DOPPLER", "SLOT", "DATA", "JUMPS.", "TUNNEL,", "BLINK.", "DECIBELS,", "REPEATERS", "MILLISECONDS."}


def draw_caption(d, t):
    for (a, b, s) in CHUNKS:
        if a <= t < b:
            s = s.upper()
            pop = clamp((t - a) / 0.08)
            scale = 2
            y = 360 - int((1 - pop) * 4)
            words = s.split(" ")
            total = text_width(s, scale)
            x = W // 2 - total // 2
            for w in words:
                col = YELLOW if any(e.strip(".,?!") == w.strip(".,?!") for e in EMPH) else WHITE
                draw_text(d, x, y, w, col, scale, outline=BLACK, shadow=PURPLE)
                x += text_width(w + " ", scale) + scale
            return


# ------------------------------------------------------------- main loop
def scene_at(t):
    for s in TL["scenes"]:
        if t < s["end"]:
            return s
    return TL["scenes"][-1]


BLOCK = 15
_perm = np.random.default_rng(1).permutation((W // BLOCK) * (H // BLOCK + 1))


def render_frame(t):
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    s = scene_at(t)
    SCENE_FN[s["name"]](img, d, t)
    # progress bar (retro hp bar)
    p = t / TL["duration"]
    d.rectangle([10, 8, W - 10, 13], fill=BLACK)
    d.rectangle([11, 9, 11 + int((W - 22) * p), 12], fill=GREEN)
    draw_caption(d, t)
    return img, s


def main():
    total = TL["duration"]
    nframes = int(total * FPS)
    only = sys.argv[1:] and sys.argv[1] == "--stills"
    if only:
        os.makedirs(os.path.join(BUILD, "stills"), exist_ok=True)
        for s in TL["scenes"]:
            for f in (0.3, 0.6, 0.9):
                t = s["start"] + (s["end"] - s["start"]) * f
                img, _ = render_frame(t)
                img.resize((W * 2, H * 2), Image.NEAREST).save(os.path.join(BUILD, "stills", f"{s['name']}_{int(f*10)}.png"))
        return

    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W*SCALE}x{H*SCALE}", "-r", str(FPS), "-i", "-",
        "-i", os.path.join(BUILD, "mix.wav"),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-tune", "animation",
        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT,
    ], stdin=subprocess.PIPE)
    scan = np.ones((H * SCALE, 1, 1), dtype=np.float32)
    scan[3::4] = 0.82
    prev_last = None
    cur_name = None
    last_img = None
    for i in range(nframes):
        t = i / FPS
        img, s = render_frame(t)
        arr = np.asarray(img)
        if s["name"] != cur_name:
            prev_last = last_img
            cur_name = s["name"]
        # pixel-block dissolve from the previous scene
        tt = t - s["start"]
        if prev_last is not None and tt < 0.35:
            n = int(len(_perm) * (1 - tt / 0.35))
            mask = np.zeros(len(_perm), bool)
            mask[_perm[:n]] = True
            mask = mask.reshape(H // BLOCK + 1, W // BLOCK)
            m = np.repeat(np.repeat(mask, BLOCK, 0), BLOCK, 1)[:H, :W]
            arr = np.where(m[..., None], prev_last, arr)
        last_img = np.asarray(img)
        # screen shake on the handover moments
        shake = 0
        gh = SC["graph"]["lines"][1]["start"]
        for moment in (gh, TL["jump"]):
            if 0 <= t - moment < 0.3:
                shake = int(3 * math.sin((t - moment) * 80))
        if shake:
            arr = np.roll(arr, shake, axis=1)
        big = np.repeat(np.repeat(arr, SCALE, 0), SCALE, 1).astype(np.float32)
        big = (big * scan).astype(np.uint8)
        ff.stdin.write(big.tobytes())
        if i % 300 == 0:
            print(f"frame {i}/{nframes}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
