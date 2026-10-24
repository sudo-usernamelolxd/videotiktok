# Tech Nobody Explains: pixel TikToks

| Episode | Video | Folder |
| --- | --- | --- |
| 1. How phones switch towers on a train | `phone-handover-train.mp4` | `handover/` |
| 2. How 5G finds your phone in a stadium | `5g-stadium.mp4` | `stadium/` |

Everything is generated offline:

- **Voice:** `espeak-ng` + MBROLA `mb-us2` (`apt-get install espeak-ng mbrola mbrola-us2`)
- **Music/SFX:** chiptune synthesized in numpy (`common/audio.py`)
- **Graphics:** drawn at 270x480 with Pillow and a hand-made 5x7 pixel font, upscaled 4x
  nearest-neighbour with scanlines (`common/pixel.py`, `common/video.py`)

## Build an episode

```sh
cd stadium
python3 ../common/audio.py .     # voice, music, timeline -> build/
python3 render.py --stills       # optional preview PNGs in build/stills
python3 render.py                # final mp4 in the repo root
```

## New episode

Copy a folder, then edit:

- `script.py`: `SCENES` (narration per scene), `CAPTIONS` (on-screen rewrites) and
  `MARKS` (timed moments + sound effects). Scenes re-time themselves to the voice.
- `render.py`: one `scene_<name>(img, d, t)` function per scene, plus the output filename.

`branding/pfp.py` draws the profile picture.
