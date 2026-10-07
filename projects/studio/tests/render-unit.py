"""Unit checks for the exporter's math and helpers (no server, no browser).

  python projects/studio/tests/render-unit.py
"""
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import studio_captions as caps  # noqa: E402
import studio_moments as sm  # noqa: E402
import studio_render as r  # noqa: E402
import studio_transcribe as st  # noqa: E402

FAILS = []
PASSES = [0]


def check(name, ok, detail=""):
    if ok:
        PASSES[0] += 1
    else:
        FAILS.append(f"{name} {detail}")
        print(f"FAIL {name} {detail}")


# ---- keyframe easing: the shared vectors
vec = json.loads((HERE / "vectors.json").read_text())
bad = [c for c in vec if abs(r.value_at({"fx": {"scale": {"v": 100, "k": c["keys"]}}}, "scale", c["t"]) - c["want"]) > 1e-9]
check(f"all {len(vec)} easing vectors", not bad, str(bad[:2]))
check("ease linear at half", r.ease_frac(0.5, "linear", "linear") == 0.5)
check("ease out (slow start) at half", r.ease_frac(0.5, "out", "linear") == 0.25)
check("ease in (slow arrival) at half", r.ease_frac(0.5, "linear", "in") == 0.75)
check("ease both at half", r.ease_frac(0.5, "out", "in") == 0.5 and abs(r.ease_frac(0.25, "out", "in") - 0.15625) < 1e-12)
check("hold stays", r.ease_frac(0.9, "hold", "linear") == 0)


# ---- the volume expression ffmpeg evaluates matches the page's gain
def ffeval(expr, t):
    py = expr.replace("if(", "IF(").replace("lt(", "LT(").replace("pow(", "POW(")
    return eval(py, {"IF": lambda c, a, b: a if c else b, "LT": lambda a, b: a < b, "POW": pow, "t": t})


clip = {"in": 30, "out": 300, "start": 0, "fx": {"volume": {"v": 0, "k": [
    {"t": 60, "v": 0, "e": "out"}, {"t": 120, "v": -20, "e": "in"}, {"t": 200, "v": -6, "e": "hold"}, {"t": 250, "v": 3, "e": "linear"}]}}}
expr = r.volume_expr(clip)
for tf in (30, 60, 75, 90, 119, 120, 150, 199, 200, 220, 260, 299):
    t = (tf - 30) / 30
    want = 10 ** (r.value_at(clip, "volume", tf) / 20)
    got = ffeval(expr, t)
    check(f"volume expression at source frame {tf}", abs(got - want) < 1e-6, f"{got} vs {want}")
check("constant volume", r.volume_expr({"in": 0, "fx": {"volume": {"v": -6}}}) == f"{10 ** (-6 / 20):.6f}")

# ---- ASS writing
check("ass time floors to the centisecond", caps.ass_time(1) == "0:00:00.03" and caps.ass_time(2) == "0:00:00.06" and caps.ass_time(30 * 3661) == "1:01:01.00")
check("ass color #FFD400 -> &H0000D4FF", caps.ass_color("#FFD400") == "&H0000D4FF", caps.ass_color("#FFD400"))
cap = {"on": True, "size": 110, "y": 1340, "bord": 7, "events": [
    {"s": 10, "e": 40, "words": [{"w": "SO", "s": 10, "e": 20, "x": 400}, {"w": "HERE", "s": 20, "e": 35, "x": 600}]}]}
tmp = HERE / "out"
tmp.mkdir(exist_ok=True)
n = caps.write_ass(cap, tmp / "u.ass", palette=caps.DEFAULT_PALETTE)
txt = (tmp / "u.ass").read_text(encoding="utf-8")
check("one event per word span (SO: lit, white; HERE: white, lit, white)", n == 5, str(n))
check("the lit word pops (their spoken word is white since 2026-09-30)", "\\c&H00FFFFFF&\\t(0,110,\\fscx108\\fscy108)" in txt)
check("each word placed by its center", "\\an5\\pos(400,1340)" in txt and "\\an5\\pos(600,1340)" in txt)
check("font and size in the style", "Style: Cap,Montserrat Black,110," in txt)
check("captions off writes no events", caps.write_ass(dict(cap, on=False), tmp / "u2.ass", palette=caps.DEFAULT_PALETTE) == 0)
check("a word with no voice is white", "\\c&H00FFFFFF&}HERE" in txt)
# colored by voice (2026-09-30): Jonathan blue, women pink, men red; every spoken word white
cap2 = {"on": True, "size": 110, "y": 1340, "bord": 7, "events": [
    {"s": 0, "e": 60, "words": [{"w": "HI", "s": 0, "e": 10, "x": 300, "k": "me"}, {"w": "THERE", "s": 10, "e": 20, "x": 500, "k": "me"}]},
    {"s": 60, "e": 90, "words": [{"w": "YES", "s": 60, "e": 70, "x": 400, "k": "f"}]},
    {"s": 90, "e": 120, "words": [{"w": "NO", "s": 90, "e": 100, "x": 400, "k": "m"}]}]}
caps.write_ass(cap2, tmp / "u3.ass", palette=caps.DEFAULT_PALETTE)
t3 = (tmp / "u3.ass").read_text(encoding="utf-8")
check("Jonathan's words blue #4D80E6 (&H00E6804D)", "\\c&H00E6804D&}THERE" in t3)
check("Jonathan's spoken word white, with the pop", "\\c&H00FFFFFF&\\t(0,110,\\fscx108\\fscy108)}HI" in t3)
check("a woman's words pink #FF5FA2 (&H00A25FFF), her spoken word white", "\\c&H00A25FFF&}YES" in t3
      and "\\c&H00FFFFFF&\\t(0,110,\\fscx108\\fscy108)}YES" in t3)
check("a man's words red #FF3B30 (&H00303BFF), his spoken word white", "\\c&H00303BFF&}NO" in t3
      and "\\c&H00FFFFFF&\\t(0,110,\\fscx108\\fscy108)}NO" in t3)
caps.write_ass(cap2, tmp / "u5.ass", palette=dict(caps.DEFAULT_PALETTE, themWord="#FFD400"))
check("their spoken word still follows the palette (yellow if set)", "\\c&H0000D4FF&\\t(0,110,\\fscx108\\fscy108)}YES" in (tmp / "u5.ass").read_text(encoding="utf-8"))
caps.write_ass(dict(cap2, palette={"you": "#123456"}), tmp / "u4.ass")
check("a palette frozen into the job beats config.json", "\\c&H00563412&}THERE" in (tmp / "u4.ass").read_text(encoding="utf-8"))
check("colors for an unknown class: white text, their spoken-word color", caps.colors_for("u", caps.DEFAULT_PALETTE) == ("#FFFFFF", "#FFFFFF"))
old_cfg = caps.sc.CONFIG
caps.sc.CONFIG = tmp / "cfg-test.json"
caps.sc.CONFIG.write_text(json.dumps({"captionColors": {"man": "#AA0000", "bogus": "#000000"}}))
pal = caps.load_palette()
check("config.json colors layer over the defaults; unknown keys dropped", pal["man"] == "#AA0000" and pal["you"] == "#4D80E6" and "bogus" not in pal)
caps.sc.CONFIG.unlink()
check("no config.json: the defaults", caps.load_palette() == caps.DEFAULT_PALETTE)
caps.sc.CONFIG = old_cfg
ref = {"events": [{"s": 0, "e": 10, "words": [{"w": "X", "s": 0, "e": 10, "x": 540, "k": "me", "asset": "a_nosuchasset0", "id": 3}]}]}
check("the exporter looks each word's voice up again (no voice data: unknown)", caps.refresh_classes(ref) == 1 and ref["events"][0]["words"][0]["k"] == "u")
# ---- voice tracks: a voice clip's gate (1 on its speaker's stretches, 0 elsewhere, 2-frame ramps)
runs_t = [[0.0, 2.0, "me"], [2.0, 5.0, "them"], [5.0, 1e9, "me"]]
vc = {"id": "v", "asset": "a_x", "in": 30, "out": 210, "voice": "them", "fx": {}}      # source 1 s to 7 s
ge = r.gate_expr(vc, {"a_x": runs_t})
geval = lambda e, t: eval(e.replace("clip(", "CLIP("), {"CLIP": lambda x, a, b: max(a, min(b, x)), "t": t})  # noqa: E731
check("Them is silent on Jonathan's stretch", geval(ge, 0.5) == 0, ge)
check("Them opens over 2 frames at the change of speaker", 0 < geval(ge, 1.0 + 1 / 30) < 1 and geval(ge, 1.2) == 1)
check("Them closes at the next change", geval(ge, 4.0) == 0 and geval(ge, 3.9) > 0 and geval(ge, 3.5) == 1)
vm = dict(vc, voice="me")
gm = r.gate_expr(vm, {"a_x": runs_t})
check("You plays its own stretches from the clip's first frame (no ramp there)", geval(gm, 0.0) == 1 and geval(gm, 2.0) == 0 and geval(gm, 5.0) == 1)
check("a clip entirely inside one speaker needs no gate, or plays nothing", r.gate_expr(dict(vc, **{"in": 70, "out": 140}), {"a_x": runs_t}) is None
      and r.gate_expr(dict(vm, **{"in": 70, "out": 140}), {"a_x": runs_t}) == "0")
check("an ordinary clip has no gate", r.gate_expr({"id": "o", "asset": "a_x", "in": 0, "out": 30, "fx": {}}, {"a_x": runs_t}) is None)
check("without voice data You plays all and Them nothing", r.gate_expr(vm, {"a_x": None}) is None and r.gate_expr(vc, {"a_x": None}) == "0")
upm, asc, desc = caps.font_metrics(r.FONT)
check("font metrics read from OS/2", (upm, asc, desc) == (1000, 1109, 453), str((upm, asc, desc)))

# ---- layers and transitions (mirrors js/compositor.js layersAt)
doc = {"tracks": [{"id": "C", "kind": "caption"}, {"id": "V2", "kind": "video"}, {"id": "V1", "kind": "video"}],
       "clips": [{"id": "a", "track": "V1", "type": "video", "in": 0, "out": 90, "start": 0},
                 {"id": "b", "track": "V1", "type": "video", "in": 200, "out": 290, "start": 90},
                 {"id": "t", "track": "V2", "type": "text", "in": 0, "out": 30, "start": 80, "text": {"str": "X"}}],
       "transitions": [{"id": "x", "track": "V1", "a": "a", "b": "b", "kind": "dissolve", "dur": 14}]}
L = r.layers_at(doc, 90)
check("mid-dissolve: both clips at half", [(c["id"], round(al, 3)) for c, al in L if c["track"] == "V1"] == [("a", 0.5), ("b", 0.5)], str(L))
check("V2 draws over V1", [c["id"] for c, _ in L][-1] == "t")
doc["transitions"][0]["kind"] = "dip"
check("mid-dip draws nothing on V1", [c for c, al in r.layers_at(doc, 90) if c["track"] == "V1" and al > 1e-6] == [])
doc["tracks"][2]["hide"] = True
check("a hidden track draws nothing", [c for c, _ in r.layers_at(doc, 10) if c["track"] == "V1"] == [])

# ---- the compositor's transform
canvas = Image.new("RGB", (r.W, r.H), (0, 0, 0))
red = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
r.paste_layer(canvas, red, 100, 100, (540, 960, 200, 0), 1.0)
check("scale 200 %: center red", canvas.getpixel((540, 960)) == (255, 0, 0))
check("scale 200 %: 99 px right still red", canvas.getpixel((639, 960))[0] > 200)
check("scale 200 %: 102 px right black", canvas.getpixel((642, 960)) == (0, 0, 0))
canvas = Image.new("RGB", (r.W, r.H), (0, 0, 0))
bar = Image.new("RGBA", (200, 40), (0, 255, 0, 255))
r.paste_layer(canvas, bar, 200, 40, (540, 960, 100, 90), 1.0)
check("rotation 90: a wide bar stands up", canvas.getpixel((540, 1050))[1] > 200 and canvas.getpixel((630, 960)) == (0, 0, 0))
canvas = Image.new("RGB", (r.W, r.H), (0, 0, 200))
r.paste_layer(canvas, Image.new("RGBA", (50, 50), (255, 255, 255, 255)), 50, 50, (540, 960, 100, 0), 0.5)
px = canvas.getpixel((540, 960))
check("opacity 50 % blends", abs(px[0] - 128) <= 2 and abs(px[2] - 228) <= 2, str(px))

# ---- transcript tokens to words
words = st.tokens_to_words([" He", "ll", "o", ",", " this", " is", " C", "3", "."], [0, .16, .24, .4, .48, .56, .64, .8, .88],
                           [.16, .08, .16, .08, .08, .08, .16, .08, .1], 10.0, 12.0)
check("tokens join into words", [w[2] for w in words] == ["Hello,", "this", "is", "C3."], str(words))
check("word times are absolute and ordered", words[0][0] == 10.0 and all(words[i][0] <= words[i + 1][0] for i in range(len(words) - 1)))
check("word end from the model's durations", abs(words[0][1] - 10.48) < 1e-6, str(words[0]))

# ---- moment lines to times (Claude answers with line numbers only)
tr = {"duration": 100.0, "words": [[1.0, 1.5, "a"], [2.0, 2.4, "b"], [10.0, 10.5, "c"], [11.0, 11.8, "d"]],
      "segments": [[1.0, 2.4, 0, 1], [10.0, 11.8, 2, 3]]}
check("line range to times, padded -0.3 / +0.4", sm.to_times(tr, 0, 1) == (0.7, 12.2), str(sm.to_times(tr, 0, 1)))
check("out-of-range lines are clamped", sm.to_times(tr, -5, 99) == (0.7, 12.2))
lines = sm.build_lines(tr)
check("transcript goes out as numbered lines", lines.splitlines()[1] == "1|00:00:10|c d", lines)

print(f"\n{PASSES[0]} passed, {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
