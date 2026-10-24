"""Shared episode runner: timeline loading, captions, transitions and the 4x encoder."""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

from pixel import BLACK, GREEN, INK, PURPLE, WHITE, YELLOW, H, W, clamp
from pixelfont import draw_text, text_width

SCALE = 4
FPS = 30
BLOCK = 15


class Episode:
    def __init__(self, build, captions=None, emph=()):
        self.build = build
        self.tl = json.load(open(os.path.join(build, "timeline.json")))
        self.sc = {s["name"]: s for s in self.tl["scenes"]}
        self.marks = self.tl.get("marks", {})
        self.replace = captions or {}
        self.emph = {e.upper().strip(".,?!") for e in emph}
        self.chunks = self._caption_chunks()

    def line_t(self, scene, i):
        ln = self.sc[scene]["lines"][i]
        return ln["start"], ln["end"]

    def _caption_chunks(self):
        chunks = []
        for s in self.tl["scenes"]:
            for ln in s["lines"]:
                text = ln["text"]
                for k, v in self.replace.items():
                    text = text.replace(k, v)
                groups, cur = [], []
                for w in text.split():
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

    def draw_caption(self, d, t):
        for (a, b, s) in self.chunks:
            if a <= t < b:
                s = s.upper()
                pop = clamp((t - a) / 0.08)
                scale = 2
                y = 360 - int((1 - pop) * 4)
                x = W // 2 - text_width(s, scale) // 2
                for w in s.split(" "):
                    col = YELLOW if w.strip(".,?!") in self.emph else WHITE
                    draw_text(d, x, y, w, col, scale, outline=BLACK, shadow=PURPLE)
                    x += text_width(w + " ", scale) + scale
                return

    def scene_at(self, t):
        for s in self.tl["scenes"]:
            if t < s["end"]:
                return s
        return self.tl["scenes"][-1]

    def render_frame(self, t, scene_fn):
        img = Image.new("RGB", (W, H), INK)
        d = ImageDraw.Draw(img)
        s = self.scene_at(t)
        scene_fn[s["name"]](img, d, t)
        p = t / self.tl["duration"]
        d.rectangle([10, 8, W - 10, 13], fill=BLACK)
        d.rectangle([11, 9, 11 + int((W - 22) * p), 12], fill=GREEN)
        self.draw_caption(d, t)
        return img, s

    def run(self, scene_fn, out, shake=()):
        if sys.argv[1:] and sys.argv[1] == "--stills":
            os.makedirs(os.path.join(self.build, "stills"), exist_ok=True)
            for s in self.tl["scenes"]:
                for f in (0.3, 0.6, 0.9):
                    t = s["start"] + (s["end"] - s["start"]) * f
                    img, _ = self.render_frame(t, scene_fn)
                    img.resize((W * 2, H * 2), Image.NEAREST).save(
                        os.path.join(self.build, "stills", f"{s['name']}_{int(f * 10)}.png"))
            return

        nframes = int(self.tl["duration"] * FPS)
        ff = subprocess.Popen([
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W*SCALE}x{H*SCALE}", "-r", str(FPS), "-i", "-",
            "-i", os.path.join(self.build, "mix.wav"),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-tune", "animation",
            "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out,
        ], stdin=subprocess.PIPE)
        perm = np.random.default_rng(1).permutation((W // BLOCK) * (H // BLOCK + 1))
        scan = np.ones((H * SCALE, 1, 1), dtype=np.float32)
        scan[3::4] = 0.82
        prev_last = last_img = cur_name = None
        for i in range(nframes):
            t = i / FPS
            img, s = self.render_frame(t, scene_fn)
            arr = np.asarray(img)
            if s["name"] != cur_name:
                prev_last = last_img
                cur_name = s["name"]
            # pixel-block dissolve from the previous scene
            tt = t - s["start"]
            if prev_last is not None and tt < 0.35:
                n = int(len(perm) * (1 - tt / 0.35))
                mask = np.zeros(len(perm), bool)
                mask[perm[:n]] = True
                mask = mask.reshape(H // BLOCK + 1, W // BLOCK)
                m = np.repeat(np.repeat(mask, BLOCK, 0), BLOCK, 1)[:H, :W]
                arr = np.where(m[..., None], prev_last, arr)
            last_img = np.asarray(img)
            for moment in shake:
                if 0 <= t - moment < 0.3:
                    arr = np.roll(arr, int(3 * math.sin((t - moment) * 80)), axis=1)
            big = np.repeat(np.repeat(arr, SCALE, 0), SCALE, 1).astype(np.float32)
            ff.stdin.write((big * scan).astype(np.uint8).tobytes())
            if i % 300 == 0:
                print(f"frame {i}/{nframes}", flush=True)
        ff.stdin.close()
        ff.wait()
        print("wrote", os.path.abspath(out))
