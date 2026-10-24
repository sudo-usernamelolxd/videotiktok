"""Episode 2: how 5G finds your phone in a stadium. Renders ../5g-stadium.mp4.

Run python3 ../common/audio.py . first, then python3 render.py [--stills].
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))

from pixel import *  # noqa: F401,F403  palette + sprites
from pixel import W, H
from pixelfont import draw_text, draw_text_centered, text_width
from script import CAPTIONS
from video import Episode

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "5g-stadium.mp4")

EP = Episode(os.path.join(HERE, "build"), CAPTIONS, emph=[
    "50,000", "PIZZA", "SLICE", "SLICE.", "ANTENNAS", "BEAMS", "LIGHTHOUSE", "AIM", "SAME", "SCHEDULER",
    "MILLISECOND", "TURN", "GOAL", "CHEAT"])
SC = EP.sc
MARKS = EP.marks
line_t = EP.line_t

CROWD_COLS = [RED, BLUE, YELLOW, PINK, WHITE, ORANGE, LAV, PEACH]


# ------------------------------------------------------------- stadium bits
def _crowd(cx, cy, rx_in, ry_in, rx_out, ry_out, n, seed):
    r = np.random.default_rng(seed)
    pts = []
    while len(pts) < n:
        x = r.uniform(-rx_out, rx_out)
        y = r.uniform(-ry_out, ry_out)
        o = (x / rx_out) ** 2 + (y / ry_out) ** 2
        i = (x / rx_in) ** 2 + (y / ry_in) ** 2
        if o <= 1 and i > 1.15:
            pts.append((int(cx + x), int(cy + y), CROWD_COLS[int(r.integers(0, len(CROWD_COLS)))], float(r.uniform(0, 1))))
    return pts


BOWL = dict(cx=135, cy=222, rx_in=74, ry_in=44, rx_out=128, ry_out=96)
CROWD = _crowd(BOWL["cx"], BOWL["cy"], BOWL["rx_in"], BOWL["ry_in"], BOWL["rx_out"], BOWL["ry_out"], 1400, 3)


def bowl(d, t, phones=0.0, field=True):
    cx, cy = BOWL["cx"], BOWL["cy"]
    d.ellipse([cx - BOWL["rx_out"] - 4, cy - BOWL["ry_out"] - 4, cx + BOWL["rx_out"] + 4, cy + BOWL["ry_out"] + 4], fill=DGRAY)
    d.ellipse([cx - BOWL["rx_out"], cy - BOWL["ry_out"], cx + BOWL["rx_out"], cy + BOWL["ry_out"]], fill=(36, 30, 56))
    for (x, y, col, ph) in CROWD:
        lit = ph < phones and math.sin(t * 9 + ph * 40) > -0.6
        d.point((x, y), fill=WHITE if lit else col)
    if field:
        rx, ry = BOWL["rx_in"], BOWL["ry_in"]
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=DGREEN)
        for k in range(-rx, rx, 12):
            d.rectangle([cx + k, cy - ry + 6, cx + k + 5, cy + ry - 6], fill=(0, 150, 90))
        d.rectangle([cx - 52, cy - 26, cx + 52, cy + 26], outline=WHITE)
        d.line([cx, cy - 26, cx, cy + 26], fill=WHITE)
        d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], outline=WHITE)
        d.rectangle([cx - 52, cy - 10, cx - 44, cy + 10], outline=WHITE)
        d.rectangle([cx + 44, cy - 10, cx + 52, cy + 10], outline=WHITE)


def floodlights(d, t):
    for x in (18, 252):
        d.line([x, 120, x, 300], fill=DGRAY, width=2)
        d.rectangle([x - 8, 112, x + 8, 120], fill=LGRAY)
        for k in range(4):
            d.point((x - 6 + k * 4, 115), fill=YELLOW)


def you_marker(d, x, y, t, col=YELLOW):
    b = int(t * 4) % 2
    d.rectangle([x - 2, y - 2, x + 2, y + 2], fill=col)
    d.polygon([(x, y - 5), (x - 4, y - 11 - b), (x + 4, y - 11 - b)], fill=col)
    draw_text_centered(d, x, y - 20 - b, "YOU", col, outline=BLACK)


def wedge(d, ox, oy, ang, length, half, color, solid=False):
    for k in range(-half * 2, half * 2 + 1):
        a = math.radians(ang + k * 0.5)
        x1, y1 = ox + length * math.cos(a), oy + length * math.sin(a)
        if solid or k % 2 == 0:
            if solid:
                d.line([ox, oy, x1, y1], fill=color)
            else:
                dashed(d, (ox, oy), (x1, y1), color, on=2, off=2)


def antenna_panel(d, x, y, t, cols=8, rows=8, cell=5, glow=True):
    w, h = cols * cell + 4, rows * cell + 4
    d.rectangle([x - w // 2 - 1, y - 1, x + w // 2 + 1, y + h + 1], fill=LGRAY)
    d.rectangle([x - w // 2, y, x + w // 2, y + h], fill=NAVY)
    for r in range(rows):
        for c in range(cols):
            on = glow and math.sin(t * 8 - (c + r) * 0.6) > 0.2
            px, py = x - w // 2 + 2 + c * cell, y + 2 + r * cell
            d.rectangle([px, py, px + cell - 2, py + cell - 2], fill=GREEN if on else DGREEN)
    d.rectangle([x - 2, y + h + 2, x + 2, 340], fill=DGRAY)


# ------------------------------------------------------------- scenes
def scene_hook(img, d, t):
    s = SC["hook"]
    lt = t - s["start"]
    l2, _ = line_t("hook", 1)
    goal = MARKS["goal"]
    d.rectangle([0, 0, W, H], fill=INK)
    sky(d, lt, bands=(INK, NAVY, (30, 36, 80)), y1=340)
    floodlights(d, lt)
    phones = 0.08 + (0.55 * clamp((t - goal) / 0.8) if t > goal else 0)
    bowl(d, lt, phones)
    # the ball rolls into the right goal
    cx, cy = BOWL["cx"], BOWL["cy"]
    bp = clamp(lt / goal)
    bx = int(cx - 20 + ease(bp) * 70)
    by = int(cy + 8 - math.sin(bp * math.pi) * 10)
    d.rectangle([bx - 1, by - 1, bx + 1, by + 1], fill=WHITE)
    if goal <= t < goal + 1.4:
        k = t - goal
        draw_text_centered(d, W // 2, 196, "GOAL!", YELLOW if int(k * 8) % 2 else RED, 5, outline=BLACK, shadow=PURPLE)
    # counters
    box(d, 8, 108, 140, 134, fill=NAVY, border=GREEN)
    online = int(50000 * clamp(lt / 2.0) ** 0.5)
    draw_text(d, 14, 113, f"PHONES: {online:,}", GREEN)
    ups = int(31000 * clamp((t - goal) / 2.5)) if t > goal else 0
    draw_text(d, 14, 123, f"UPLOADING: {ups:,}", YELLOW if ups else LAV)
    if t >= l2:
        # a searching reticle that lands on you
        p = clamp((t - l2) / 1.6)
        tx, ty = 205, 258
        jx = int(math.sin(t * 7) * 40 * (1 - p))
        jy = int(math.cos(t * 5) * 25 * (1 - p))
        x, y = tx + jx, ty + jy
        d.rectangle([x - 7, y - 7, x + 7, y + 7], outline=GREEN)
        d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=GREEN)
        if p >= 1:
            you_marker(d, tx, ty, lt)
    d.rectangle([0, 340, W, H], fill=INK)
    if t < l2:
        title(d, ["50,000", "PHONES"], lt, 0.0, color=YELLOW, scale=4)
    else:
        title(d, ["WHICH ONE", "IS YOURS?"], t, l2, color=PINK)


PEPS = [(math.cos(a) * r, math.sin(a) * r) for a, r in zip(np.linspace(0, 20, 14), [20, 45, 52, 30, 12, 40, 55, 25, 48, 35, 15, 58, 28, 42])]


def pizza(d, cx, cy, r, slices, hi=True):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BROWN)
    d.ellipse([cx - r + 5, cy - r + 5, cx + r - 5, cy + r - 5], fill=ORANGE)
    d.ellipse([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8], fill=YELLOW)
    for (px, py) in PEPS:
        sc = (r - 14) / 60
        x, y = cx + px * sc, cy + py * sc
        pr = max(2, int(5 * r / 70))
        d.ellipse([x - pr, y - pr, x + pr, y + pr], fill=RED)
    if slices > 1:
        lines = min(slices, 180)
        for k in range(lines):
            a = -math.pi / 2 + 2 * math.pi * k / lines
            d.line([cx, cy, cx + r * math.cos(a), cy + r * math.sin(a)], fill=BROWN)
    if hi and slices > 1:
        # your slice, outlined
        a0 = -math.pi / 2
        a1 = a0 + 2 * math.pi / slices
        pts = [(cx, cy)] + [(cx + (r + 2) * math.cos(a0 + (a1 - a0) * i / 8), cy + (r + 2) * math.sin(a0 + (a1 - a0) * i / 8)) for i in range(9)]
        d.line(pts + [(cx, cy)], fill=GREEN, width=2)


def scene_pizza(img, d, t):
    s = SC["pizza"]
    lt = t - s["start"]
    l2, _ = line_t("pizza", 1)
    d.rectangle([0, 0, W, H], fill=INK)
    for y in range(100, 340, 10):
        for x in range(0, W, 10):
            if (x // 10 + y // 10) % 2 == 0:
                d.rectangle([x, y, x + 9, y + 9], fill=(40, 20, 40))
    if t < l2:
        n = [1, 2, 4, 8][min(3, int(lt / 0.8))]
    else:
        p = clamp((t - l2) / 1.4)
        n = int(8 * (50000 / 8) ** p)
    pizza(d, 135, 215, 72, n)
    box(d, 30, 300, 240, 330, fill=NAVY, border=LAV)
    draw_text(d, 38, 306, f"PHONES: {n:,}", WHITE)
    share = 100 / n
    txt = f"{share:.0f}%" if share >= 1 else f"{share:.3f}%"
    draw_text(d, 38, 318, f"YOUR SLICE: {txt}", GREEN if n < 100 else RED)
    d.rectangle([0, 340, W, H], fill=INK)
    if t < l2:
        title(d, ["BANDWIDTH", "= PIZZA"], lt, 0.0, color=ORANGE)
    else:
        title(d, ["TINY", "SLICE"], t, l2, color=RED, scale=4)


SPOTS = []
for k in range(28):
    a = 2 * math.pi * k / 28
    SPOTS.append((BOWL["cx"] + 101 * math.cos(a), BOWL["cy"] + 70 * math.sin(a)))
SPOTS += [(BOWL["cx"] + 84 * math.cos(2 * math.pi * (k + 0.5) / 14), BOWL["cy"] + 56 * math.sin(2 * math.pi * (k + 0.5) / 14)) for k in range(14)]


def scene_smallcells(img, d, t):
    s = SC["smallcells"]
    lt = t - s["start"]
    l2, _ = line_t("smallcells", 1)
    d.rectangle([0, 0, W, H], fill=INK)
    bowl(d, lt, 0.1)
    # the one big tower, crossed out, fading
    if lt < 2.0:
        x, base = 240, 330
        tower(d, x, base, 50, LGRAY, t=lt)
        if lt > 0.8:
            d.line([x - 14, base - 50, x + 14, base], fill=RED, width=2)
            d.line([x + 14, base - 50, x - 14, base], fill=RED, width=2)
    shown = int(len(SPOTS) * clamp((lt - 1.2) / 4.0))
    cols = [GREEN, BLUE, PINK, ORANGE]
    for i, (x, y) in enumerate(SPOTS[:shown]):
        col = cols[i % 4]
        r = 13
        for ang in range(0, 360, 20):
            a = math.radians(ang + lt * 40)
            d.point((int(x + r * math.cos(a)), int(y + r * math.sin(a) * 0.7)), fill=col)
    for i, (x, y) in enumerate(SPOTS[:shown]):
        d.rectangle([x - 1, y - 2, x + 1, y + 2], fill=WHITE)
        d.point((x, y - 3), fill=cols[i % 4])
        if t >= l2 and (i * 0.11) % 1 < clamp((t - l2) / 1.5):
            d.ellipse([x - 4, y - 13, x + 4, y - 5], fill=BROWN)
            d.ellipse([x - 3, y - 12, x + 3, y - 6], fill=YELLOW)
            d.point((x - 1, y - 10), fill=RED)
            d.point((x + 1, y - 8), fill=RED)
    box(d, 40, 300, 230, 330, fill=NAVY, border=GREEN)
    draw_text(d, 48, 306, f"SMALL CELLS: {shown * 7}", GREEN)
    draw_text(d, 48, 318, "EACH: FULL PIZZA" if t >= l2 else "UNDER SEATS + ROOF", YELLOW if t >= l2 else WHITE)
    d.rectangle([0, 340, W, H], fill=INK)
    if t < l2:
        title(d, ["STADIUMS", "CHEAT"], lt, 0.0, color=GREEN)
    else:
        title(d, ["MORE CELLS", "MORE PIZZA"], t, l2, color=YELLOW)


ANT = (135, 300)
BEAMS = [218 + i * 16 for i in range(8)]
BEST = 4
YOU = (int(ANT[0] + 150 * math.cos(math.radians(BEAMS[BEST]))), int(ANT[1] + 150 * math.sin(math.radians(BEAMS[BEST]))))


def stands(d, t, phones=0.1, seed=11):
    """Front-on view of a stand full of people, rows getting smaller with distance."""
    r = np.random.default_rng(seed)
    d.rectangle([0, 100, W, 300], fill=(36, 30, 56))
    for row in range(14):
        y = 112 + row * 11
        d.line([0, y + 7, W, y + 7], fill=DGRAY)
        step = 8
        for x in range(2 + (row % 2) * 4, W, step):
            col = CROWD_COLS[int(r.integers(0, len(CROWD_COLS)))]
            ph = float(r.uniform(0, 1))
            d.rectangle([x, y + 1, x + 3, y + 6], fill=col)
            d.rectangle([x + 1, y - 1, x + 2, y], fill=PEACH)
            if ph < phones and math.sin(t * 6 + ph * 30) > 0:
                d.point((x + 3, y), fill=WHITE)


def scene_sweep(img, d, t):
    s = SC["sweep"]
    lt = t - s["start"]
    l2, _ = line_t("sweep", 1)
    lock = MARKS["lock"]
    d.rectangle([0, 0, W, H], fill=INK)
    stands(d, lt)
    ox, oy = ANT
    locked = t >= lock
    if not locked:
        if t < l2 + 0.6:
            i = int(lt * 5) % len(BEAMS)
            wedge(d, ox, oy, BEAMS[i], 190, 3, BLUE)
            tip = (ox + 120 * math.cos(math.radians(BEAMS[i])), oy + 120 * math.sin(math.radians(BEAMS[i])))
            draw_text_centered(d, tip[0], tip[1], str(i + 1), WHITE, 2, outline=BLACK)
            if i == BEST:
                draw_text(d, YOU[0] + 8, YOU[1] - 4, "!!", YELLOW, outline=BLACK)
        # report packets from you back down to the antenna
        if t >= l2:
            for k in range(3):
                f = ((t - l2) * 1.2 + k / 3) % 1
                x = YOU[0] + (ox - YOU[0]) * f
                y = YOU[1] + (oy - YOU[1]) * f
                d.rectangle([x - 3, y - 2, x + 3, y + 2], fill=YELLOW)
            box(d, 8, 104, 120, 128, fill=NAVY, border=YELLOW)
            draw_text(d, 14, 110, "BEST = BEAM 5", YELLOW)
    else:
        wedge(d, ox, oy, BEAMS[BEST], 160, 2, GREEN, solid=True)
        k = t - lock
        if k < 0.3:
            r = int(k * 120)
            d.ellipse([YOU[0] - r, YOU[1] - r, YOU[0] + r, YOU[1] + r], outline=WHITE)
        box(d, 8, 104, 120, 128, fill=NAVY, border=GREEN)
        draw_text(d, 14, 110, "LOCKED ON", GREEN)
    you_marker(d, *YOU, lt, GREEN if locked else YELLOW)
    antenna_panel(d, ox, oy, lt, cols=6, rows=3, cell=4)
    d.rectangle([0, 340, W, H], fill=INK)
    if t < l2:
        title(d, ["BEAM", "SWEEP"], lt, 0.0, color=BLUE, scale=4)
    elif not locked:
        title(d, ["PHONE SAYS", "BEAM 5!"], t, l2, color=YELLOW)
    else:
        title(d, ["LOCKED", "ON"], t, lock, color=GREEN, scale=4)


USERS = [((40, 150), GREEN), ((210, 135), ORANGE), ((95, 205), PINK), ((175, 230), BLUE), ((240, 200), YELLOW), ((25, 245), LAV)]


def scene_mimo(img, d, t):
    s = SC["mimo"]
    lt = t - s["start"]
    d.rectangle([0, 0, W, H], fill=INK)
    stands(d, lt, seed=12)
    ox, oy = 135, 262
    n = 1 + int(clamp((lt - 0.5) / 3.5) * (len(USERS) - 1) + 0.001)
    for i, ((x, y), col) in enumerate(USERS[:n]):
        x += int(math.sin(lt * 2 + i) * 2)
        ang = math.degrees(math.atan2(y - oy, x - ox))
        wedge(d, ox, oy, ang, math.hypot(x - ox, y - oy), 1, col, solid=True)
        # pulse travelling along the beam
        f = (lt * 1.5 + i * 0.17) % 1
        px, py = ox + (x - ox) * f, oy + (y - oy) * f
        d.rectangle([px - 2, py - 2, px + 2, py + 2], fill=WHITE)
        d.rectangle([x - 3, y - 3, x + 3, y + 3], outline=col)
    antenna_panel(d, ox, oy, lt, cols=8, rows=8, cell=5)
    box(d, 8, 104, 128, 128, fill=NAVY, border=LAV)
    draw_text(d, 14, 110, f"BEAMS: {n}  3.5 GHZ", WHITE)
    if lt > 3.0:
        box(d, 150, 300, 262, 330, fill=NAVY, border=GREEN)
        draw_text(d, 156, 306, "SAME FREQUENCY", GREEN)
        draw_text(d, 156, 318, "SAME MOMENT", GREEN)
    d.rectangle([0, 340, W, H], fill=INK)
    title(d, ["MANY BEAMS", "AT ONCE"], lt, 0.0, color=PINK)


SCHED_COLS = [GREEN, ORANGE, PINK, BLUE, LAV, YELLOW]
_sched = np.random.default_rng(9).integers(0, len(SCHED_COLS), size=(10, 400))


def scene_scheduler(img, d, t):
    s = SC["scheduler"]
    lt = t - s["start"]
    d.rectangle([0, 0, W, H], fill=INK)
    gx0, gy0, cw, ch, ncol, nrow = 34, 124, 13, 15, 16, 10
    box(d, gx0 - 6, gy0 - 6, gx0 + ncol * cw + 5, gy0 + nrow * ch + 18, fill=(16, 22, 50), border=LAV)
    speed = 9  # slots per second
    head = lt * speed
    offset = max(0.0, head - ncol + 3)
    for r in range(nrow):
        for c in range(ncol):
            slot = int(c + offset)
            x, y = gx0 + c * cw, gy0 + r * ch
            if slot < head:
                col = SCHED_COLS[_sched[r, slot]]
                d.rectangle([x, y, x + cw - 2, y + ch - 2], fill=col)
                if col == YELLOW:
                    d.point((x + 2, y + 2), fill=WHITE)
            else:
                d.rectangle([x, y, x + cw - 2, y + ch - 2], outline=(45, 50, 90))
    hx = gx0 + int((head - offset) * cw)
    d.line([hx, gy0 - 4, hx, gy0 + nrow * ch], fill=WHITE)
    draw_text(d, gx0, gy0 + nrow * ch + 4, "TIME >", LAV)
    draw_text(d, 6, gy0, "F", LAV)
    draw_text(d, 6, gy0 + 9, "R", LAV)
    draw_text(d, 6, gy0 + 18, "E", LAV)
    draw_text(d, 6, gy0 + 27, "Q", LAV)
    # one slot callout
    d.rectangle([gx0 + 3 * cw - 1, gy0 - 1, gx0 + 4 * cw - 1, gy0 + nrow * ch - 1], outline=WHITE)
    draw_text(d, gx0 + 4 * cw + 4, gy0 + nrow * ch + 4, "1 SLOT < 1 MS", WHITE)
    # legend
    box(d, 30, 300, 240, 332, fill=NAVY, border=LAV)
    for i, col in enumerate(SCHED_COLS):
        d.rectangle([38 + i * 34, 307, 44 + i * 34, 313], fill=col)
        draw_text(d, 47 + i * 34, 307, "YOU" if col == YELLOW else f"P{i + 1}", col)
    mine = int(np.sum(_sched[:, : int(head)] == SCHED_COLS.index(YELLOW)))
    draw_text(d, 38, 320, f"YOUR TURNS: {mine}", YELLOW)
    d.rectangle([0, 340, W, H], fill=INK)
    title(d, ["EVERYONE", "GETS A TURN"], lt, 0.0, color=YELLOW)


def scene_outro(img, d, t):
    s = SC["outro"]
    lt = t - s["start"]
    l2, _ = line_t("outro", 1)
    stall = MARKS["stall"]
    if t >= l2:
        end_card(d, t - l2, lt)
        return
    d.rectangle([0, 0, W, H], fill=INK)
    bowl(d, lt, 0.6)
    sx0, sy0, sx1, sy1 = phone(d, 95, 150, 80, 140)
    draw_text(d, sx0 + 4, sy0 + 6, "GOAL.MP4", WHITE)
    # pixel thumbnail
    d.rectangle([sx0 + 4, sy0 + 18, sx1 - 4, sy0 + 58], fill=DGREEN)
    d.rectangle([sx0 + 28, sy0 + 30, sx0 + 34, sy0 + 46], outline=WHITE)
    d.rectangle([sx0 + 18, sy0 + 37, sx0 + 20, sy0 + 39], fill=WHITE)
    p = 0.99 * ease(clamp(lt / (stall - s["start"])))
    stuck = t >= stall
    draw_text(d, sx0 + 4, sy0 + 66, "UPLOADING", YELLOW if not stuck else ORANGE)
    d.rectangle([sx0 + 4, sy0 + 78, sx1 - 4, sy0 + 84], outline=LGRAY)
    d.rectangle([sx0 + 5, sy0 + 79, sx0 + 5 + int((sx1 - sx0 - 10) * p), sy0 + 83], fill=GREEN)
    draw_text(d, sx0 + 4, sy0 + 90, f"{int(p * 100)}%", WHITE)
    if stuck:
        # spinner of doom
        a = (t * 8) % (2 * math.pi)
        cx, cy = sx1 - 12, sy0 + 94
        for k in range(8):
            aa = a + k * math.pi / 4
            col = WHITE if k == 0 else DGRAY
            d.point((int(cx + 5 * math.cos(aa)), int(cy + 5 * math.sin(aa))), fill=col)
    d.rectangle([0, 340, W, H], fill=INK)
    if not stuck:
        title(d, ["UPLOADING", "THE GOAL"], lt, 0.0, color=GREEN)
    else:
        title(d, ["...MOST OF", "THE TIME"], t, stall, color=PINK)


SCENE_FN = {
    "hook": scene_hook, "pizza": scene_pizza, "smallcells": scene_smallcells, "sweep": scene_sweep,
    "mimo": scene_mimo, "scheduler": scene_scheduler, "outro": scene_outro,
}


if __name__ == "__main__":
    EP.run(SCENE_FN, OUT, shake=[MARKS["goal"], MARKS["lock"]])
