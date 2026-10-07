"""Render smoke test: a short that uses every feature, exported end to end, then the file checked.

  python projects/studio/tests/render-smoke.py

Makes a 10 s synthetic source (ffmpeg test pattern + tone) in a temp media folder, a short with: eased scale
keyframes and an 8 degree rotation on V1, a cut with a cross dissolve, a 50 % image, a text title and a box on V2,
audio with a fade and volume keyframes, a sound effect on A2, and captions. Checks: 1080x1920, a constant 30 fps
(frame count = length x 30), H.264 High yuv420p, AAC 48 kHz, faststart (moov before mdat), loudness -14 +-1 LUFS,
and the still of frame f against frame f of the export (PSNR >= 40 dB).
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
MEDIA = Path(tempfile.mkdtemp(prefix="studio-smoke-"))
os.environ["STUDIO_MEDIA"] = str(MEDIA)
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import studio_common as sc  # noqa: E402
import studio_prep as prep  # noqa: E402
import studio_render as r  # noqa: E402

FAILS, PASSES = [], [0]


def check(name, ok, detail=""):
    if ok:
        PASSES[0] += 1
        print(f"ok   {name}")
    else:
        FAILS.append(name)
        print(f"FAIL {name} {detail}")


def psnr(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    mse = ((a - b) ** 2).mean()
    return 99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse)


def register(path):
    aid = sc.asset_id(path)
    (sc.CACHE / aid).mkdir(parents=True, exist_ok=True)
    meta = prep.make_meta(aid, path)
    sc.write_json_atomic(sc.CACHE / aid / "meta.json", meta)
    return aid


def main():
    sc.ensure_dirs()
    ff = sc.ffmpeg_exe()
    src = sc.INBOX / "smoke10.mp4"
    subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=30:d=10",
                    "-f", "lavfi", "-i", "sine=f=330:r=48000:d=10", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", str(src)], check=True)
    sfx = sc.SFX / "blip.wav"
    subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=1000:r=48000:d=0.3", str(sfx)], check=True)
    logo = sc.ASSETS / "logo.png"
    Image.open(HERE / "fixtures" / "seed" / "assets" / "logo.png").save(logo)
    v, s, im = register(src), register(sfx), register(logo)
    doc = {
        "v": 1, "id": "smoke", "name": "Smoke", "fps": 30, "w": 1080, "h": 1920, "rev": 3,
        "tracks": [{"id": "C", "kind": "caption"}, {"id": "V2", "kind": "video"}, {"id": "V1", "kind": "video"},
                   {"id": "A1", "kind": "audio"}, {"id": "A2", "kind": "audio"}],
        "clips": [
            {"id": "c1", "track": "V1", "type": "video", "asset": v, "in": 0, "out": 120, "start": 0, "link": "L1",
             "fx": {"scale": {"v": 100, "k": [{"t": 10, "v": 100, "e": "out"}, {"t": 50, "v": 118, "e": "in"}]}, "rot": {"v": 8}}},
            {"id": "c3", "track": "V1", "type": "video", "asset": v, "in": 150, "out": 270, "start": 120, "link": "L2", "fx": {}},
            {"id": "c2", "track": "A1", "type": "audio", "asset": v, "in": 0, "out": 240, "start": 0, "fadeIn": 15, "fadeOut": 20,
             "fx": {"volume": {"v": 0, "k": [{"t": 60, "v": 0, "e": "linear"}, {"t": 120, "v": -12, "e": "linear"}]}}},
            {"id": "c4", "track": "A2", "type": "audio", "asset": s, "in": 0, "out": 9, "start": 90, "fx": {"volume": {"v": -3}}},
            {"id": "c5", "track": "V2", "type": "image", "asset": im, "in": 0, "out": 90, "start": 30, "fx": {"opacity": {"v": 50}, "posY": {"v": 400}}},
            {"id": "c6", "track": "V2", "type": "text", "in": 0, "out": 60, "start": 150, "fx": {"posY": {"v": 300}},
             "text": {"str": "SMOKE TEST", "size": 110, "color": "#FFFFFF", "stroke": "#000000", "strokeW": 8}},
            {"id": "c7", "track": "V2", "type": "shape", "in": 0, "out": 30, "start": 210, "fx": {},
             "shape": {"kind": "rect", "w": 600, "h": 120, "fill": "#FFD400", "radius": 24}},
        ],
        "transitions": [{"id": "t1", "track": "V1", "a": "c1", "b": "c3", "kind": "dissolve", "dur": 14}],
        "markers": [{"id": "m1", "t": 30, "color": "green", "note": ""}],
        "captions": {"on": True, "hl": "#FFD400", "size": 110, "y": 1340, "bord": 7, "evRev": 3, "events": [
            {"s": 6, "e": 50, "words": [{"w": "RENDER", "s": 6, "e": 25, "x": 380}, {"w": "CHECK", "s": 25, "e": 50, "x": 700}]}]},
    }
    proj = sc.PROJECTS / "smoke.json"
    proj.write_text(json.dumps(doc))
    out = sc.READY / "smoke.mp4"
    final = r.render(r.load_doc(proj), out)
    check("render wrote the MP4", Path(final).exists())
    info = subprocess.run([ff, "-hide_banner", "-i", str(final)], capture_output=True, text=True).stderr
    check("1080x1920", "1080x1920" in info, info)
    check("H.264 High, yuv420p", "h264 (High)" in info and "yuv420p" in info)
    check("30 fps", " 30 fps" in info)
    check("AAC 48 kHz", "aac" in info and "48000 Hz" in info)
    cnt = subprocess.run([ff, "-hide_banner", "-i", str(final), "-map", "0:v", "-f", "null", "-"], capture_output=True, text=True).stderr
    frames = int([l for l in cnt.replace("\r", "\n").splitlines() if l.startswith("frame=")][-1].split("=")[1].split()[0])
    check("constant 30 fps: 240 frames for 8 s", frames == 240, str(frames))
    head = Path(final).read_bytes()[:200000]
    check("faststart: moov before mdat", head.find(b"moov") != -1 and head.find(b"moov") < head.find(b"mdat"))
    lo = subprocess.run([ff, "-hide_banner", "-nostats", "-i", str(final), "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    i_line = [l for l in lo.splitlines() if l.strip().startswith("I:")][-1]
    lufs = float(i_line.split()[1])
    check("loudness -14 +-1 LUFS", abs(lufs + 14) <= 1.0, str(lufs))
    for f in (20, 60, 120, 160, 215):
        png = MEDIA / f"still-{f}.png"
        r.still(r.load_doc(proj), f, png)
        exp = MEDIA / f"exp-{f}.png"
        subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-i", str(final), "-vf", f"select=eq(n\\,{f})",
                        "-frames:v", "1", str(exp)], check=True)
        # brightness (luma): the export keeps color at quarter resolution (yuv420p), which alone costs this
        # synthetic, all-color-detail pattern several dB; luma carries position, scale, rotation and captions
        p = psnr(Image.open(png).convert("L"), Image.open(exp).convert("L"))
        check(f"still of frame {f} matches the export (luma PSNR {p:.1f} dB >= 40)", p >= 40, f"{p:.1f}")
    print(f"\n{PASSES[0]} passed, {len(FAILS)} failed  (media {MEDIA})")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
