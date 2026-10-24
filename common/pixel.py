"""Shared pixel-art toolkit: palette, sprites and helpers drawn at 270x480."""
import math

import numpy as np

from pixelfont import draw_text, draw_text_centered, text_width

W, H = 270, 480

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


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)



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


def end_card(d, k, lt):
    """"Follow for more" card; k = seconds since it started, lt = scene time."""
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
