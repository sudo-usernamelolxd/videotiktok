# How phones switch towers on a train — pixel TikTok

Output: `../phone-handover-train.mp4` (1080x1920, 30 fps, ~66 s).

Everything is generated offline:

- **Voice:** `espeak-ng` + MBROLA `mb-us2` (`apt-get install espeak-ng mbrola mbrola-us2`)
- **Music/SFX:** chiptune synthesized in numpy (`audio.py`)
- **Graphics:** drawn at 270x480 with Pillow and a hand-made 5x7 pixel font, upscaled 4x nearest-neighbour with scanlines (`render.py`)

```sh
cd handover
python3 audio.py          # voice, music, timeline
python3 render.py --stills  # optional preview PNGs in build/stills
python3 render.py         # final mp4
```

Edit the narration in `script.py`; scenes re-time themselves to the voice.
