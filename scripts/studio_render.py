"""Monarc Studio exporter (2026-09-29): a short (media/projects/<id>.json) to a finished MP4.

  python scripts/studio_render.py <project.json> --out media/ready/<name>.mp4 [--job <dir>]
  python scripts/studio_render.py <project.json> --still <frame> --png out.png [--scale 1]

How: a Python compositor (Pillow + numpy) builds every frame with the same rules the page previews with
(projects/studio/js/compositor.js): layers bottom video track first, each moved to (posX, posY), rotated
(degrees, clockwise), scaled (percent) about its center, times its opacity and any transition. Keyframes ease with
one definition shared with js/model/keyframes.js (tests/vectors.json checks both). Frames go to ffmpeg over a pipe;
ffmpeg burns the captions (libass, studio_captions.py), mixes the audio (volume keyframes, fades, sound effects),
evens loudness to -14 LUFS in two passes, and encodes 1080x1920 30 fps H.264 High + AAC with +faststart (G27).
Progress goes to stdout as JSON lines {"progress", "stage"}; a short over 90 s is a warning, never a block (G28).
"""
import argparse
import json
import math
import queue
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_common as sc  # noqa: E402
import studio_captions as caps  # noqa: E402

FPS = 30
W, H = 1080, 1920
FX_DEFAULTS = {"posX": 540, "posY": 960, "scale": 100, "rot": 0, "opacity": 100, "volume": 0}
FONT = sc.STUDIO_DIR / "fonts" / "Montserrat-Black.ttf"
LIMIT_90 = 90 * FPS


def say(**kw):
    print(json.dumps(kw), flush=True)


# ------------------------------------------------------------------ model (mirrors js/model)

def ease_frac(u, e0, e1):
    if e0 == "hold":
        return 0.0
    a = e0 in ("out", "both")
    b = e1 in ("in", "both")
    if a and b:
        return 3 * u * u - 2 * u * u * u
    if a:
        return u * u
    if b:
        return 1 - (1 - u) * (1 - u)
    return u


def value_at(clip, name, t):
    p = (clip.get("fx") or {}).get(name)
    base = p["v"] if p and "v" in p else FX_DEFAULTS[name]
    k = p.get("k") if p else None
    if not k:
        return base
    if t <= k[0]["t"]:
        return k[0]["v"]
    if t >= k[-1]["t"]:
        return k[-1]["v"]
    i = 0
    while i < len(k) - 1 and k[i + 1]["t"] <= t:
        i += 1
    k0, k1 = k[i], k[i + 1]
    u = (t - k0["t"]) / (k1["t"] - k0["t"])
    return k0["v"] + (k1["v"] - k0["v"]) * ease_frac(u, k0.get("e", "linear"), k1.get("e", "linear"))


def clip_end(c):
    return c["start"] + (c["out"] - c["in"])


def src_frame(c, f):
    return c["in"] + (f - c["start"])


def transition_window(doc, t):
    a = find(doc, t.get("a"))
    b = find(doc, t.get("b"))
    cut = clip_end(a) if a else b["start"]
    if a and b:
        return cut, cut - t["dur"] / 2, cut + t["dur"] / 2
    if a:
        return cut, cut - t["dur"], cut
    return cut, cut, cut + t["dur"]


def find(doc, cid):
    if not cid:
        return None
    return next((c for c in doc["clips"] if c["id"] == cid), None)


def draw_order(doc):
    return [t for t in doc["tracks"] if t["kind"] == "video"][::-1]


def layers_at(doc, f):
    out = []
    for tr in draw_order(doc):
        if tr.get("hide"):
            continue
        cs = sorted([c for c in doc["clips"] if c["track"] == tr["id"]], key=lambda c: c["start"])
        items = {}
        for c in cs:
            if c["start"] <= f < clip_end(c) and c.get("on", True) is not False:
                items[c["id"]] = (c, 1.0)
        for t in doc.get("transitions", []):
            if t["track"] != tr["id"]:
                continue
            cut, s, e = transition_window(doc, t)
            if f < s or f >= e:
                continue
            p = (f - s) / (e - s)
            A, B = find(doc, t.get("a")), find(doc, t.get("b"))
            if t["kind"] == "dissolve" and A and B:
                items[A["id"]] = (A, 1 - p)
                items[B["id"]] = (B, p)
            elif A and B:
                if p < 0.5:
                    items[A["id"]] = (A, 1 - p * 2)
                    items.pop(B["id"], None)
                else:
                    items[B["id"]] = (B, p * 2 - 1)
                    items.pop(A["id"], None)
            elif A:
                items[A["id"]] = (A, 1 - p)
            elif B:
                items[B["id"]] = (B, p)
        out.extend(sorted(items.values(), key=lambda x: x[0]["start"]))
    return out


# ------------------------------------------------------------------ assets

class Assets:
    def __init__(self):
        self.meta = {}

    def get(self, aid):
        if aid not in self.meta:
            m = sc.read_json(sc.CACHE / aid / "meta.json")
            if not m:
                raise RuntimeError(f"asset {aid} is missing (was the file moved out of media/?)")
            self.meta[aid] = m
        return self.meta[aid]

    def path(self, aid, for_video=True):
        m = self.get(aid)
        if m.get("kind") == "video" and m.get("orig") == "cache" and (sc.CACHE / aid / "orig.mp4").exists():
            return sc.CACHE / aid / "orig.mp4"
        return sc.MEDIA / m["rel"]

    def size(self, aid):
        m = self.get(aid)
        v = m.get("video") or {}
        return (v.get("w") or m.get("w") or W), (v.get("h") or m.get("h") or H)


BOX_PAD, BOX_RADIUS = 32, 20     # a text clip's box (text.bg), as js/compositor.js draws it


def text_image(t):
    size = int(t.get("size") or 110)
    sw = int(t.get("strokeW") or 0)
    font = ImageFont.truetype(str(FONT), size)
    lines = str(t.get("str") or "").split("\n")
    widths = [font.getlength(ln) for ln in lines]
    pad = (t.get("pad") if t.get("pad") is not None else BOX_PAD) if t.get("bg") else 0
    w = max([20.0] + widths) + sw * 2 + pad * 2
    h = size * 1.2 * len(lines) + sw * 2 + pad * 2
    img = Image.new("RGBA", (int(math.ceil(w)), int(math.ceil(h))), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if t.get("bg"):
        r = min(float(t.get("radius") if t.get("radius") is not None else BOX_RADIUS), w / 2, h / 2)
        d.rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=t["bg"])
    lh = size * 1.2
    upm, asc, desc = _font_metrics()
    off = (asc - desc) / (2 * upm) * size        # baseline below each line's center: js/compositor.js textBaselineOffset
    for i, ln in enumerate(lines):
        y = h / 2 + (i - (len(lines) - 1) / 2) * lh + off
        d.text((w / 2, y), ln, font=font, fill=t.get("color") or "#FFFFFF", anchor="ms",
               stroke_width=sw, stroke_fill=t.get("stroke") or "#000000")
    return img, (w, h)


_FM = None


def _font_metrics():
    global _FM
    if _FM is None:
        _FM = caps.font_metrics(FONT)
    return _FM


def shape_image(sh):
    w, h = float(sh.get("w") or 100), float(sh.get("h") or 100)
    img = Image.new("RGBA", (int(math.ceil(w)), int(math.ceil(h))), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fill = sh.get("fill")
    stroke = sh.get("stroke") if sh.get("strokeW") else None
    swd = int(sh.get("strokeW") or 0)
    kind = sh.get("kind", "rect")
    if kind == "ellipse":
        d.ellipse((0, 0, w - 1, h - 1), fill=fill, outline=stroke, width=swd)
    elif kind == "arrow":
        hw, hh = w / 2, h / 2
        head = min(w * 0.35, h * 1.2)
        shaft = h * 0.36
        pts = [(-hw, -shaft / 2), (hw - head, -shaft / 2), (hw - head, -hh), (hw, 0), (hw - head, hh),
               (hw - head, shaft / 2), (-hw, shaft / 2)]
        d.polygon([(x + hw, y + hh) for x, y in pts], fill=fill, outline=stroke)
    else:
        r = min(float(sh.get("radius") or 0), w / 2, h / 2)
        d.rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=fill, outline=stroke, width=swd)
    return img, (w, h)


def base_size(c, assets, text_cache):
    if c["type"] == "shape":
        return float(c["shape"]["w"]), float(c["shape"]["h"])
    if c["type"] == "text":
        return text_cache(c)[1]
    sw, sh = assets.size(c["asset"])
    if c["type"] == "image" and sw <= W and sh <= H:
        return float(sw), float(sh)
    k = min(W / sw, H / sh)
    return sw * k, sh * k


# ------------------------------------------------------------------ video sources

class FrameSource:
    """Decodes one clip's stretch of its file at 30 fps, RGB, in a background thread (so decode and compositing
    overlap). Frame k of the stream is source frame first + k."""

    def __init__(self, path, first, count, size):
        self.first, self.count = first, count
        self.w, self.h = size
        self.q = queue.Queue(maxsize=24)
        self.next = first
        self.last = None
        # seek a tenth of a frame early: an exact first/30 can round past the frame and drop it (the next frame
        # would then play one frame late); the fps filter still puts `first` in slot 0
        args = [sc.ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-ss", f"{max(0.0, (first - 0.1) / FPS):.6f}", "-i", str(path),
                "-t", f"{(count + 2) / FPS:.6f}", "-an",
                "-vf", f"fps={FPS},scale={self.w}:{self.h}:in_color_matrix=bt709:in_range=tv,format=rgb24",
                "-f", "rawvideo", "-"]
        self.proc = sc.popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.t = threading.Thread(target=self._read, daemon=True)
        self.t.start()

    def _read(self):
        n = self.w * self.h * 3
        try:
            while True:
                buf = self.proc.stdout.read(n)
                if len(buf) < n:
                    break
                self.q.put(buf)
        finally:
            self.q.put(None)

    def frame(self, src_f):
        """RGB Image for source frame src_f (must be asked in increasing order)."""
        while self.next <= src_f:
            buf = self.q.get()
            if buf is None:
                break
            self.last = buf
            self.next += 1
        if self.last is None:
            return None
        return Image.frombuffer("RGB", (self.w, self.h), self.last, "raw", "RGB", 0, 1)

    def close(self):
        try:
            self.proc.kill()
            self.proc.wait()
        except Exception:  # noqa: BLE001
            pass
        sc.untrack(self.proc)


# ------------------------------------------------------------------ compositor

def paste_layer(canvas, img, base_w, base_h, tf, alpha):
    """Draw img (RGB or RGBA) scaled to base size x scale, rotated, centered at (x, y), with alpha, onto canvas."""
    x, y, s, r = tf
    if s <= 0 or alpha <= 0:
        return
    sw, sh = img.size
    kx = (base_w / sw) * (s / 100.0)
    ky = (base_h / sh) * (s / 100.0)
    th = math.radians(r)
    cos, sin = math.cos(th), math.sin(th)
    # bounding box of the placed layer on the canvas
    hw, hh = sw * kx / 2, sh * ky / 2
    xs, ys = [], []
    for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)):
        xs.append(x + dx * cos - dy * sin)
        ys.append(y + dx * sin + dy * cos)
    x0, y0 = max(0, int(math.floor(min(xs)))), max(0, int(math.floor(min(ys))))
    x1, y1 = min(W, int(math.ceil(max(xs)))), min(H, int(math.ceil(max(ys))))
    if x1 <= x0 or y1 <= y0:
        return
    full = (abs(r) < 1e-6 and abs(kx - 1) < 1e-6 and abs(ky - 1) < 1e-6 and alpha >= 0.999 and img.mode == "RGB"
            and abs(x - sw / 2) < 1e-6 and abs(y - sh / 2) < 1e-6 and (sw, sh) == (W, H))
    if full:
        canvas.paste(img, (0, 0))
        return
    if abs(r) < 1e-6:
        # no rotation (zooms, moves, fades): crop the visible part of the layer and resize it, far quicker than an
        # affine transform of the whole frame. The box keeps sub-pixel precision, so it lands where the canvas does.
        left, top = x - sw * kx / 2, y - sh * ky / 2
        bx0, by0 = max(0.0, (x0 - left) / kx), max(0.0, (y0 - top) / ky)
        bx1, by1 = min(float(sw), (x1 - left) / kx), min(float(sh), (y1 - top) / ky)
        ox0, oy0 = max(0, int(round(left + bx0 * kx))), max(0, int(round(top + by0 * ky)))
        ox1, oy1 = min(W, int(round(left + bx1 * kx))), min(H, int(round(top + by1 * ky)))
        if ox1 <= ox0 or oy1 <= oy0 or bx1 <= bx0 or by1 <= by0:
            return
        part = img.resize((ox1 - ox0, oy1 - oy0), Image.Resampling.BILINEAR, box=(bx0, by0, bx1, by1))
        if part.mode == "RGBA":
            mask = part.getchannel("A")
            if alpha < 0.999:
                mask = mask.point(lambda v: int(v * alpha + 0.5))
            canvas.paste(part.convert("RGB"), (ox0, oy0), mask)
        elif alpha < 0.999:
            canvas.paste(part, (ox0, oy0), Image.new("L", part.size, int(alpha * 255 + 0.5)))
        else:
            canvas.paste(part, (ox0, oy0))
        return
    # output (X, Y) -> layer (u, v): inverse of translate . rotate . scale about the layer's center
    a = cos / kx
    b = sin / kx
    c = -(x * cos + y * sin) / kx + sw / 2
    d = -sin / ky
    e = cos / ky
    f = (x * sin - y * cos) / ky + sh / 2
    c2 = a * x0 + b * y0 + c
    f2 = d * x0 + e * y0 + f
    src = img if img.mode == "RGBA" else img.convert("RGBA")
    out = src.transform((x1 - x0, y1 - y0), Image.Transform.AFFINE, (a, b, c2, d, e, f2), resample=Image.Resampling.BILINEAR)
    mask = out.getchannel("A")
    if alpha < 0.999:
        mask = mask.point(lambda v: int(v * alpha + 0.5))
    canvas.paste(out.convert("RGB"), (x0, y0), mask)


class Compositor:
    def __init__(self, doc, assets):
        self.doc, self.assets = doc, assets
        self.sources = {}
        self.images = {}
        self.texts = {}
        self.shapes = {}
        # the stretch of each video clip's file the render needs (handles for transitions)
        self.need = {}
        for c in doc["clips"]:
            if c["type"] != "video":
                continue
            a, b = c["in"], c["out"]
            for t in doc.get("transitions", []):
                if t.get("a") == c["id"]:
                    b = c["out"] + (t["dur"] // 2 if t.get("b") else 0)
                if t.get("b") == c["id"] and t.get("a"):
                    a = c["in"] - t["dur"] // 2
            self.need[c["id"]] = (max(0, a), b)

    def text_cache(self, c):
        key = json.dumps(c["text"], sort_keys=True)
        if key not in self.texts:
            self.texts[key] = text_image(c["text"])
        return self.texts[key]

    def source(self, c):
        s = self.sources.get(c["id"])
        if s is None:
            a, b = self.need.get(c["id"], (c["in"], c["out"]))
            bw, bh = base_size(c, self.assets, self.text_cache)
            sw, shh = self.assets.size(c["asset"])
            # decode at the size it will be drawn at 100 %, never above the source's own size
            dw, dh = (int(round(min(bw, sw))) // 2 * 2, int(round(min(bh, shh))) // 2 * 2)
            s = FrameSource(self.assets.path(c["asset"]), a, b - a, (max(2, dw), max(2, dh)))
            self.sources[c["id"]] = s
        return s

    def release(self, f):
        for cid in list(self.sources):
            c = find(self.doc, cid)
            end = self.need.get(cid, (0, 0))[1]
            if c is None or f > c["start"] + (end - c["in"]) + 1:
                self.sources.pop(cid).close()

    def frame(self, f):
        canvas = Image.new("RGB", (W, H), (0, 0, 0))
        for c, alpha in layers_at(self.doc, f):
            t = src_frame(c, f)
            x, y = value_at(c, "posX", t), value_at(c, "posY", t)
            s, r = value_at(c, "scale", t), value_at(c, "rot", t)
            o = max(0.0, min(1.0, value_at(c, "opacity", t) / 100.0 * alpha))
            if o <= 0:
                continue
            bw, bh = base_size(c, self.assets, self.text_cache)
            if c["type"] == "video":
                img = self.source(c).frame(int(round(t)))
                if img is None:
                    continue
            elif c["type"] == "image":
                if c["asset"] not in self.images:
                    self.images[c["asset"]] = Image.open(self.assets.path(c["asset"])).convert("RGBA")
                img = self.images[c["asset"]]
            elif c["type"] == "text":
                img = self.text_cache(c)[0]
            elif c["type"] == "shape":
                key = json.dumps(c["shape"], sort_keys=True)
                if key not in self.shapes:
                    self.shapes[key] = shape_image(c["shape"])[0]
                img = self.shapes[key]
            else:
                continue
            paste_layer(canvas, img, bw, bh, (x, y, s, r), o)
        self.release(f)
        return canvas

    def close(self):
        for s in self.sources.values():
            s.close()
        self.sources.clear()


# ------------------------------------------------------------------ audio

def volume_expr(c):
    """ffmpeg expression (t = seconds into the clip) for the clip's linear gain from its volume keyframes (dB)."""
    p = (c.get("fx") or {}).get("volume") or {}
    k = p.get("k")
    if not k:
        return f"{10 ** ((p.get('v', 0)) / 20):.6f}"
    pts = [((kk["t"] - c["in"]) / FPS, kk["v"], kk.get("e", "linear")) for kk in k]
    expr = f"{pts[-1][1]}"
    for i in range(len(pts) - 2, -1, -1):
        t0, v0, e0 = pts[i]
        t1, v1, e1 = pts[i + 1]
        span = max(t1 - t0, 1e-6)
        u = f"((t-{t0:.6f})/{span:.6f})"
        a = e0 in ("out", "both")
        b = e1 in ("in", "both")
        if e0 == "hold":
            frac = "0"
        elif a and b:
            frac = f"(3*{u}*{u}-2*{u}*{u}*{u})"
        elif a:
            frac = f"({u}*{u})"
        elif b:
            frac = f"(1-(1-{u})*(1-{u}))"
        else:
            frac = u
        seg = f"({v0}+({v1}-({v0}))*{frac})"
        expr = f"if(lt(t,{t1:.6f}),{seg},{expr})"
    expr = f"if(lt(t,{pts[0][0]:.6f}),{pts[0][1]},{expr})"
    return f"pow(10,({expr})/20)"


GATE_RAMP = 2 / FPS      # seconds a voice track takes to open or close at a change of speaker


def gate_expr(c, runs_cache):
    """For a voice clip (c["voice"] = "me" or "them"): ffmpeg expression (t = seconds into the clip) that is 1 on its
    speaker's stretches and 0 elsewhere, with 2-frame ramps; None for an ordinary clip, "0" when it plays nothing."""
    side = c.get("voice")
    if side not in ("me", "them"):
        return None
    import studio_speakers as ss
    if c["asset"] not in runs_cache:
        try:
            runs_cache[c["asset"]] = ss.runs_for(c["asset"])
        except Exception:  # noqa: BLE001  (no voice data: "me" plays all, "them" nothing)
            runs_cache[c["asset"]] = None
    s0, s1 = c["in"] / FPS, c["out"] / FPS
    spans = ss.gate(runs_cache[c["asset"]], side, s0, s1)
    if not spans:
        return "0"
    if len(spans) == 1 and spans[0][0] <= s0 and spans[0][1] >= s1:
        return None
    r = GATE_RAMP
    terms = []
    for a, b in spans:
        a, b = a - s0, b - s0
        up = "1" if a <= 0 else f"clip((t-{a:.4f})/{r:.4f},0,1)"
        down = "1" if b >= s1 - s0 else f"clip(({b:.4f}-t)/{r:.4f},0,1)"
        terms.append(f"{up}*{down}" if up != "1" or down != "1" else "1")
    return "+".join(terms)


def build_mix(doc, assets, out_wav, total_frames):
    tracks = {t["id"]: t for t in doc["tracks"] if t["kind"] == "audio"}
    solo = any(t.get("solo") for t in tracks.values())
    clips = [c for c in doc["clips"] if c["type"] == "audio" and c.get("on", True) is not False and c["track"] in tracks
             and (tracks[c["track"]].get("solo") if solo else not tracks[c["track"]].get("mute"))]
    runs_cache = {}
    gates = {c["id"]: gate_expr(c, runs_cache) for c in clips}
    clips = [c for c in clips if gates[c["id"]] != "0"]     # a voice track with nothing of its speaker here
    dur = total_frames / FPS
    args = [sc.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error"]
    filters = []
    labels = []
    for i, c in enumerate(clips):
        length = (c["out"] - c["in"]) / FPS
        args += ["-ss", f"{c['in'] / FPS:.6f}", "-t", f"{length:.6f}", "-i", str(assets.path(c["asset"]))]
        chain = [f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo", "asetpts=PTS-STARTPTS"]
        g = gates.get(c["id"])
        chain.append(f"volume=eval=frame:volume='{volume_expr(c)}*({g})'" if g else f"volume=eval=frame:volume='{volume_expr(c)}'")
        if c.get("fadeIn"):
            chain.append(f"afade=t=in:st=0:d={c['fadeIn'] / FPS:.6f}:curve=tri")
        if c.get("fadeOut"):
            chain.append(f"afade=t=out:st={max(0.0, length - c['fadeOut'] / FPS):.6f}:d={c['fadeOut'] / FPS:.6f}:curve=tri")
        chain.append(f"adelay=delays={int(round(c['start'] * 48000 / FPS))}S:all=1")
        filters.append(",".join(chain) + f"[a{i}]")
        labels.append(f"[a{i}]")
    n = len(clips)
    args += ["-f", "lavfi", "-t", f"{dur:.6f}", "-i", "anullsrc=r=48000:cl=stereo"]
    labels.append(f"[{n}:a]")
    # apad needs a fixed length: an endless apad before atrim hangs ffmpeg 7.1 when the mix has several file
    # inputs (found 2026-09-29: a 22 s mix never finished)
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0:duration=longest,"
                   f"apad=whole_dur={dur:.6f},atrim=0:{dur:.6f}[mix]")
    args += ["-filter_complex", ";".join(filters), "-map", "[mix]", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2",
             str(out_wav)]
    r = subprocess.run(args, capture_output=True, text=True, stdin=subprocess.DEVNULL, creationflags=sc.NO_WINDOW,
                       timeout=max(120, dur * 3))
    if r.returncode:
        raise RuntimeError("audio mix failed: " + r.stderr[-800:])
    return len(clips)


def measure_loudness(wav):
    r = subprocess.run([sc.ffmpeg_exe(), "-hide_banner", "-nostats", "-i", str(wav), "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL, creationflags=sc.NO_WINDOW, timeout=600)
    txt = r.stderr
    j = txt[txt.rfind("{"):txt.rfind("}") + 1]
    try:
        return json.loads(j)
    except ValueError:
        return None


TARGET_I, CEILING_DB = -14.0, -1.5


def _gain_chain(gain):
    ceiling = 10 ** (CEILING_DB / 20)
    return f"volume={gain:.2f}dB,alimiter=limit={ceiling:.4f}:level=disabled:attack=5:release=60:asc=1,aresample=48000"


def _integrated(wav, chain):
    r = subprocess.run([sc.ffmpeg_exe(), "-hide_banner", "-nostats", "-i", str(wav), "-af", chain + ",ebur128=framelog=quiet",
                        "-f", "null", "-"], capture_output=True, text=True, stdin=subprocess.DEVNULL,
                       creationflags=sc.NO_WINDOW, timeout=600)
    return _last_i(r.stderr)


def _last_i(txt):
    for line in reversed(txt.splitlines()):
        if line.strip().startswith("I:"):
            try:
                return float(line.split()[1])
            except (IndexError, ValueError):
                return None
    return None


def range_loudness(src, ranges):
    """Integrated loudness (LUFS, EBU R128 gating, so pauses don't count) of these stretches of a file, played end to
    end: what "Normalize voices" measures for each voice track (2026-09-30). ranges: [[start, end]] in seconds."""
    ranges = sorted((float(a), float(b)) for a, b in ranges if float(b) - float(a) > 0.05)
    if not ranges:
        return None
    t0, t1 = ranges[0][0], max(b for _, b in ranges)
    n = len(ranges)
    graph = [f"[0:a]asplit={n}" + "".join(f"[s{i}]" for i in range(n)) if n > 1 else "[0:a]anull[s0]"]
    for i, (a, b) in enumerate(ranges):
        graph.append(f"[s{i}]atrim=start={a - t0:.3f}:end={b - t0:.3f},asetpts=PTS-STARTPTS[p{i}]")
    graph.append("".join(f"[p{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1,ebur128=framelog=quiet[out]")
    r = subprocess.run([sc.ffmpeg_exe(), "-hide_banner", "-nostats", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}",
                        "-i", str(src), "-filter_complex", ";".join(graph), "-map", "[out]", "-f", "null", "-"],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL, creationflags=sc.NO_WINDOW, timeout=300)
    return _last_i(r.stderr)


def loudness_filter(ln, wav=None):
    """Pass 2: one measured gain to -14 LUFS, then a peak limiter at -1.5 dBFS, then one correction for what the
    limiter took off (call audio is peaky). loudnorm's own second pass falls back to dynamic mode on call audio,
    whose loudness swings more than its LRA target, and lands about 1 LU low."""
    try:
        i = float(ln["input_i"])
    except (TypeError, KeyError, ValueError):
        return "aresample=48000"          # silence: nothing to even out
    if i < -70:
        return "aresample=48000"
    gain = TARGET_I - i
    if wav is not None:
        got = _integrated(wav, _gain_chain(gain))
        if got is not None and abs(TARGET_I - got) > 0.2:
            gain += max(-3.0, min(3.0, TARGET_I - got))
    return _gain_chain(gain)


# ------------------------------------------------------------------ main paths

def load_doc(path):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    for c in doc["clips"]:
        c.setdefault("fx", {})
    doc.setdefault("transitions", [])
    doc.setdefault("captions", {"on": False, "events": []})
    return doc


def job_dir_for(doc, job):
    d = Path(job) if job else sc.CACHE / "renders" / doc["id"] / "manual"
    d.mkdir(parents=True, exist_ok=True)
    (d / "fonts").mkdir(exist_ok=True)
    shutil.copy(FONT, d / "fonts" / FONT.name)
    return d


def render(doc, out, job=None):
    assets = Assets()
    total = max([clip_end(c) for c in doc["clips"]] or [0])
    if total <= 0:
        raise RuntimeError("nothing on the timeline")
    for c in doc["clips"]:
        if c.get("asset"):
            assets.get(c["asset"])
    if total > LIMIT_90:
        say(warn=f"runs {total / FPS:.1f} s, over the 90 s Facebook Reels limit")
    cap = doc.get("captions") or {}
    if cap.get("evRev") is not None and doc.get("rev") is not None and cap.get("evRev") != doc.get("rev"):
        say(warn="captions were built for another save of this short; exporting them as they are")
    moved = caps.refresh_classes(cap)
    if moved:
        say(warn=f"voices changed for {moved} caption words since this short was saved; the colors follow the "
                 "new labels, but open the short once to regroup its captions")
    jd = job_dir_for(doc, job)
    say(stage="audio", progress=0.0)
    wav = jd / "mix.wav"
    build_mix(doc, assets, wav, total)
    ln = measure_loudness(wav)
    caps.write_ass(cap, jd / "captions.ass")
    lnf = loudness_filter(ln, wav)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    part = jd / "out.mp4"
    args = [sc.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0", "-i", "mix.wav",
            "-filter_complex", f"[0:v]ass=captions.ass:fontsdir=fonts,scale=out_color_matrix=bt709:out_range=tv,"
                               f"format=yuv420p[v];[1:a]{lnf}[a]",
            "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-profile:v", "high",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-g", "60",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", "-f", "mp4", "out.mp4"]
    enc = sc.popen(args, cwd=str(jd), stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    err = []
    threading.Thread(target=lambda: err.extend(l.decode("utf-8", "replace") for l in enc.stderr), daemon=True).start()
    comp = Compositor(doc, assets)
    t0 = time.time()
    try:
        for f in range(total):
            img = comp.frame(f)
            enc.stdin.write(img.tobytes())
            if f % 15 == 0:
                say(stage="video", progress=round(0.05 + 0.93 * f / total, 4), fps=round((f + 1) / max(0.01, time.time() - t0), 1))
        enc.stdin.close()
        enc.wait()
    finally:
        comp.close()
        sc.untrack(enc)
    if enc.returncode:
        raise RuntimeError("encoder failed: " + "".join(err)[-1200:])
    final = out
    try:
        final.unlink(missing_ok=True)
        shutil.move(str(part), str(final))
    except PermissionError:   # the old export is open in a player: keep both
        final = out.with_name(out.stem + time.strftime("-%H%M%S") + out.suffix)
        shutil.move(str(part), str(final))
    say(stage="done", progress=1.0, out=str(final), seconds=round(time.time() - t0, 1))
    return final


def still(doc, f, png, scale=1.0):
    assets = Assets()
    comp = Compositor(doc, assets)
    try:
        img = comp.frame(int(f))
    finally:
        comp.close()
    jd = job_dir_for(doc, None)
    comp_png = jd / "still-comp.png"
    img.save(comp_png)
    cap = doc.get("captions") or {}
    caps.refresh_classes(cap)
    caps.write_ass(cap, jd / "still.ass")
    # the picture keeps its real time (setpts), so libass shows the words, colors and pops of frame f
    vf = f"setpts=PTS-STARTPTS+{int(f) / FPS:.6f}/TB,ass=still.ass:fontsdir=fonts"
    if scale != 1.0:
        vf += f",scale={int(W * scale) // 2 * 2}:{int(H * scale) // 2 * 2}"
    r = subprocess.run([sc.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error", "-i", "still-comp.png",
                        "-vf", vf, "-frames:v", "1", str(Path(png).resolve())], cwd=str(jd), capture_output=True,
                       text=True, creationflags=sc.NO_WINDOW)
    if r.returncode:
        raise RuntimeError(r.stderr[-600:])
    return png


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--out")
    ap.add_argument("--job")
    ap.add_argument("--still", type=int)
    ap.add_argument("--png")
    ap.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args()
    doc = load_doc(a.project)
    if a.still is not None:
        still(doc, a.still, a.png, a.scale)
        return
    if not a.out:
        sys.exit("--out is required")
    render(doc, a.out, a.job)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
