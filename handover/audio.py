"""Builds the voice-over (espeak-ng + MBROLA), a chiptune backing track and SFX.

Writes build/voice.wav, build/mix.wav and build/timeline.json.
"""
import json
import os
import subprocess
import wave

import numpy as np

from script import SCENES

SR = 44100
BUILD = os.path.join(os.path.dirname(__file__), "build")
VOICE = os.environ.get("VOICE", "mb-us2")
SPEED = os.environ.get("SPEED", "168")

LINE_GAP = 0.30      # silence between lines in a scene
SCENE_PAD = 0.55     # extra tail at the end of each scene
LEAD_IN = 0.35


def read_wav(path):
    with wave.open(path) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        return data.astype(np.float32) / 32768.0


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def tts(text, idx):
    raw = os.path.join(BUILD, f"line{idx:02d}_raw.wav")
    out = os.path.join(BUILD, f"line{idx:02d}.wav")
    subprocess.run(["espeak-ng", "-v", VOICE, "-s", SPEED, "-p", "48", "-w", raw, text], check=True)
    # Resample, clean up rumble, warm it a bit and even out the level.
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-ar", str(SR), "-ac", "1",
        "-af", "highpass=f=85,equalizer=f=220:t=q:w=1:g=3,equalizer=f=3200:t=q:w=1:g=4,"
               "acompressor=threshold=-20dB:ratio=3:attack=5:release=80,silenceremove=start_periods=1:start_threshold=-45dB,"
               "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
        out,
    ], check=True)
    return read_wav(out)


# ---------------------------------------------------------------- chiptune
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def freq(name, octave):
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octave + 1) - 69) / 12)


def square(f, n, duty=0.5):
    t = np.arange(n) / SR
    return np.where((t * f) % 1.0 < duty, 1.0, -1.0)


def triangle(f, n):
    t = np.arange(n) / SR
    return 2 * np.abs(2 * ((t * f) % 1.0) - 1) - 1


def env(n, attack=0.003, decay=0.12):
    t = np.arange(n) / SR
    return np.minimum(1, t / attack) * np.exp(-t / decay)


def chiptune(total):
    bpm = 124
    step = 60 / bpm / 4  # 16th note
    ns = int(step * SR)
    chords = [("A", ["A", "C", "E"]), ("F", ["F", "A", "C"]), ("C", ["C", "E", "G"]), ("G", ["G", "B", "D"])]
    out = np.zeros(int(total * SR) + SR)
    nsteps = int(total / step)
    rng = np.random.default_rng(7)
    noise = rng.uniform(-1, 1, ns)
    for s in range(nsteps):
        i = s * ns
        bar = (s // 16) % 4
        root, notes = chords[bar]
        # arpeggio
        nn = notes[s % 3]
        octv = 5 if (s // 3) % 2 == 0 else 6
        out[i:i + ns] += 0.18 * square(freq(nn, octv), ns, 0.25) * env(ns, decay=0.06)
        # bass on 8ths
        if s % 2 == 0:
            o = 2 if s % 4 == 0 else 3
            out[i:i + ns] += 0.35 * triangle(freq(root, o), ns) * env(ns, decay=0.2)
        # hats
        if s % 2 == 1:
            out[i:i + ns] += 0.07 * noise * env(ns, decay=0.015)
        # kick
        if s % 4 == 0:
            t = np.arange(ns) / SR
            f = 120 * np.exp(-t * 30) + 40
            out[i:i + ns] += 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(ns, decay=0.08)
        # snare
        if s % 8 == 4:
            out[i:i + ns] += 0.18 * noise * env(ns, decay=0.05)
    return out[: int(total * SR)]


def blip(up=True):
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    f = np.where(t < 0.08, 660, 990) if up else np.where(t < 0.08, 880, 440)
    ph = np.cumsum(f) / SR
    return 0.35 * np.where(ph % 1 < 0.5, 1.0, -1.0) * env(n, decay=0.09)


def whoosh():
    n = int(0.35 * SR)
    rng = np.random.default_rng(3)
    x = rng.uniform(-1, 1, n)
    # crude low-pass that opens up
    y = np.zeros(n)
    a = np.linspace(0.02, 0.4, n)
    for i in range(1, n):
        y[i] = y[i - 1] + a[i] * (x[i] - y[i - 1])
    w = np.sin(np.linspace(0, np.pi, n))
    return 0.3 * y * w


def main():
    os.makedirs(BUILD, exist_ok=True)
    timeline = {"scenes": []}
    voice_parts = []
    cursor = LEAD_IN
    idx = 0
    for name, lines in SCENES:
        scene = {"name": name, "start": cursor - (LEAD_IN if not timeline["scenes"] else 0), "lines": []}
        for j, text in enumerate(lines):
            audio = tts(text, idx)
            dur = len(audio) / SR
            scene["lines"].append({"text": text, "start": cursor, "end": cursor + dur})
            voice_parts.append((cursor, audio))
            cursor += dur + (LINE_GAP if j < len(lines) - 1 else 0)
            idx += 1
        cursor += SCENE_PAD
        scene["end"] = cursor
        timeline["scenes"].append(scene)
    total = cursor + 0.6
    timeline["duration"] = total

    voice = np.zeros(int(total * SR) + SR)
    for start, a in voice_parts:
        i = int(start * SR)
        voice[i:i + len(a)] += a
    voice = voice[: int(total * SR)]
    voice *= 0.9 / (np.abs(voice).max() + 1e-9)

    # duck the music under the voice
    music = chiptune(total)
    active = (np.abs(voice) > 0.02).astype(np.float32)
    k = int(0.25 * SR)
    active = np.convolve(active, np.ones(k) / k, mode="same")
    duck = 1.0 - 0.65 * np.clip(active * 4, 0, 1)
    music *= 0.16 * duck

    sfx = np.zeros_like(voice)

    def add(at, clip):
        i = int(at * SR)
        sfx[i:i + len(clip)] += clip[: len(sfx) - i]

    for sc in timeline["scenes"][1:]:
        add(sc["start"], whoosh())
    # handover moments
    g = next(s for s in timeline["scenes"] if s["name"] == "graph")
    add(g["lines"][1]["start"] - 0.05, blip())
    h = next(s for s in timeline["scenes"] if s["name"] == "handover")
    timeline["jump"] = h["lines"][2]["start"] + 0.9
    add(timeline["jump"], blip())

    mix = voice + music + sfx * 0.6
    mix *= 0.95 / np.abs(mix).max()
    write_wav(os.path.join(BUILD, "voice.wav"), voice)
    write_wav(os.path.join(BUILD, "mix.wav"), mix)
    with open(os.path.join(BUILD, "timeline.json"), "w") as f:
        json.dump(timeline, f, indent=1)
    print(f"total {total:.2f}s")


if __name__ == "__main__":
    main()
