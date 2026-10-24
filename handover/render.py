"""Episode 1: how phones switch towers on a train. Renders ../phone-handover-train.mp4.

Run python3 ../common/audio.py . first, then python3 render.py [--stills].
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))

from pixel import *  # noqa: F401,F403  palette + sprites
from pixel import W, H
from pixelfont import draw_text, draw_text_centered, text_width
from script import CAPTIONS
from video import Episode

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "phone-handover-train.mp4")

EP = Episode(os.path.join(HERE, "build"), CAPTIONS, emph=[
    "HANDOVER", "TOWER", "CELLS", "DOPPLER", "SLOT", "DATA", "JUMPS", "TUNNEL", "BLINK",
    "DECIBELS", "REPEATERS", "MILLISECONDS"])
TL = EP.tl
SC = EP.sc
line_t = EP.line_t

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
    jump = EP.marks["jump"]
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
        end_card(d, t - l2, lt)


SCENE_FN = {
    "hook": scene_hook, "cells": scene_cells, "measure": scene_measure, "graph": scene_graph,
    "handover": scene_handover, "train": scene_train, "outro": scene_outro,
}


if __name__ == "__main__":
    EP.run(SCENE_FN, OUT, shake=[EP.marks["handover"] + 0.05, EP.marks["jump"]])
