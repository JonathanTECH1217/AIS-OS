"""Burned-in captions for Monarc Studio exports (2026-09-29; colored by voice 2026-09-30).

The editor builds the caption groups (2-4 words, each word's center x and its voice class k) and saves them in the
short as captions.events; this module writes them as an ASS file that ffmpeg's libass filter burns in. Each word is
its own event with \\an5\\pos(x,y) and its voice's color, so the spoken word can take the spoken-word color and pop to
108 % over 110 ms (\\t(0,110,\\fscx108\\fscy108)) without pushing its neighbours: the same rule the page draws with
(projects/studio/js/compositor.js drawCaptions).

Colors come from one palette for every short (projects/studio/config.json, "captionColors"; Jonathan's grill C1-C11):
his words #4D80E6 with his spoken word white, women #FF5FA2, men #FF3B30, their spoken word #FFD400, and words with
no voice yet white with the yellow spoken word. An export job freezes the palette into its project.json.

Times are floored to the centisecond, so an event is on screen from its first frame through its last.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_common as sc  # noqa: E402

FPS = 30
FONT_NAME = "Montserrat Black"
# their spoken word turned white too on 2026-09-30 (Jonathan: "It looks better"); it was #FFD400
DEFAULT_PALETTE = {"you": "#4D80E6", "youWord": "#FFFFFF", "woman": "#FF5FA2", "man": "#FF3B30",
                   "themWord": "#FFFFFF", "unknown": "#FFFFFF"}


def load_palette():
    data = sc.read_json(sc.CONFIG, {}) or {}
    return {**DEFAULT_PALETTE, **{k: v for k, v in (data.get("captionColors") or {}).items() if k in DEFAULT_PALETTE}}


def colors_for(k, pal):
    """(text color, spoken-word color) for a voice class: me, f (woman), m (man), anything else unknown."""
    if k == "me":
        return pal["you"], pal["youWord"]
    if k == "f":
        return pal["woman"], pal["themWord"]
    if k == "m":
        return pal["man"], pal["themWord"]
    return pal["unknown"], pal["themWord"]


def refresh_classes(captions):
    """Look up each word's voice again from its recording's current labels (a fix made after the short was saved
    must still color right). Returns how many words changed class."""
    import studio_speakers as ss
    import studio_gencaps as gc
    cache, gcache, changed = {}, {}, 0
    gen = captions.get("gen") or {}
    for ev in captions.get("events", []):
        for w in ev.get("words", []):
            a, i, gi = w.get("asset"), w.get("id"), w.get("gi")
            if a is not None and gi is not None and a in gen:      # a generated word (2026-10-02, studio_gencaps.py)
                if a not in gcache:
                    gcache[a] = gc.gen_classes(a, gen[a])
                cls = gcache[a]
                k = cls[gi] if cls is not None and 0 <= gi < len(cls) else w.get("k", "u")
                if w.get("k", "u") != k:
                    changed += 1
                w["k"] = k
                continue
            if a is None or i is None:
                continue
            if a not in cache:
                cache[a] = ss.word_classes(a)
            cls = cache[a]
            k = cls[i] if cls is not None and 0 <= i < len(cls) else "u"
            if w.get("k", "u") != k:
                changed += 1
            w["k"] = k
    return changed


def font_metrics(ttf):
    """(unitsPerEm, winAscent, winDescent) from the TTF's head and OS/2 tables (libass sizes by these)."""
    data = Path(ttf).read_bytes()
    n = struct.unpack(">H", data[4:6])[0]
    tables = {}
    for i in range(n):
        o = 12 + i * 16
        tables[data[o:o + 4].decode("latin-1")] = struct.unpack(">I", data[o + 8:o + 12])[0]
    upm = struct.unpack(">H", data[tables["head"] + 18:tables["head"] + 20])[0]
    o2 = tables["OS/2"]
    asc, desc = struct.unpack(">HH", data[o2 + 74:o2 + 78])
    return upm, asc, desc


def ass_time(frames):
    cs = int((frames / FPS) * 100 + 1e-6)     # floor to the centisecond
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, c = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def ass_color(hex_rgb, alpha=0):
    h = hex_rgb.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper().replace("&H", "&H", 1)


def escape(text):
    return text.replace("\\", "⧵").replace("{", "(").replace("}", ")")


def write_ass(captions, path, frame_offset=0, palette=None):
    """captions: the short's captions dict (on, size, y, bord, events; palette when an export job froze one).
    frame_offset shifts every time (used for a still, where the frame is placed at t=0)."""
    size = captions.get("size", 88)
    bord = captions.get("bord", 6)
    y = captions.get("y", 1340)
    pal = {**DEFAULT_PALETTE, **(palette or captions.get("palette") or load_palette())}
    lines = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "ScaledBorderAndShadow: yes",
        "WrapStyle: 2", "YCbCr Matrix: TV.709", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding",
        f"Style: Cap,{FONT_NAME},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,{bord:g},0,5,0,0,0,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    n = 0
    if captions.get("on", True):
        for ev in captions.get("events", []):
            gs, ge = ev["s"] + frame_offset, ev["e"] + frame_offset
            for w in ev["words"]:
                ws, we = w["s"] + frame_offset, w["e"] + frame_offset
                pos = f"\\an5\\pos({int(round(w['x']))},{int(y)})"
                text = escape(w["w"])
                text_c, word_c = colors_for(w.get("k"), pal)
                spans = [(gs, ws, False), (ws, we, True), (we, ge, False)]
                for a, b, active in spans:
                    a, b = max(a, gs), min(b, ge)
                    if b <= a or b <= 0:
                        continue
                    a = max(a, 0)
                    tag = pos + (f"\\c{ass_color(word_c)}&\\t(0,110,\\fscx108\\fscy108)" if active
                                 else f"\\c{ass_color(text_c)}&")
                    lines.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Cap,,0,0,0,,{{{tag}}}{text}")
                    n += 1
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return n
