"""The Monarc Build mark (Jonathan, 2026-09-26: "we need a new favicon and logo to match the google app style").

Interview: brainstorms/2026-09-26-homepage-google-rebuild.md Q6 to Q10. A four-wing monarch butterfly, flat and rounded
like a Google app icon, in four Google-like hues of Monarc's own, mirror-symmetric (upper wings larger than the lower),
so it reads as neither Google Photos' pinwheel nor Gmail's M. The name beside it is "Monarc Build" in Outfit 500
(OFL), turned into outlines so no page has to load the font.

Usage: python make_brand.py           writes candidates/butterfly-a.svg to -e.svg, wordmark.svg, and sheet.html
Then render the sheet:  python .claude/skills/landing-page/assets/render.py "projects/Landing Page Build/brand/sheet.html" <out.png> 1440
       python make_brand.py export a  exports the picked candidate (Jonathan picked A, 2026-09-26):
         public_html/favicon.svg, favicon.ico (16, 32, 48), apple-touch-icon.png (180, on white),
         public_html/assets/brand/butterfly.svg, butterfly-512.png, lockup.svg (grey name), lockup-white.svg,
         and projects/Landing Page Build/build/brand-lockup.html (the inline lockup the page builds include,
         the name in currentColor so each page sets its color).
"""
import json
import re
import subprocess
import sys
import urllib.request
from math import acos, atan2, cos, hypot, sin
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAND = HERE / "candidates"
FONT = HERE / "fonts" / "Outfit[wght].ttf"
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/outfit/Outfit%5Bwght%5D.ttf"
LICENSE_URL = "https://github.com/google/fonts/raw/main/ofl/outfit/OFL.txt"

# Four hues, Google-like but Monarc's own (Q7), measured 2026-09-26. Blue carries text (5.75:1 on white);
# coral, amber, and teal pass only as graphics (3.4, 2.0, 3.4 on white), so they stay in the mark and the accents.
BLUE, CORAL, AMBER, TEAL = "#1F5ED8", "#E8604C", "#F2A93B", "#169C86"
INK, WORDMARK = "#202124", "#5F6368"
UL, UR, LL, LR = BLUE, CORAL, TEAL, AMBER  # upper wings take the stronger hues


def mix(a, b, t=0.5, dark=0.0):
    """Blend two hexes, then darken by `dark` (0 to 1)."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    c = [round((x * (1 - t) + y * t) * (1 - dark)) for x, y in zip(ca, cb)]
    return "#" + "".join(f"{v:02X}" for v in c)


def teardrop(px, py, cx, cy, r):
    """A wing: a round lobe of radius r at (cx, cy) drawn to a point at (px, py)."""
    dx, dy = px - cx, py - cy
    d = hypot(dx, dy)
    th, a = atan2(dy, dx), acos(r / d)
    t1 = (cx + r * cos(th + a), cy + r * sin(th + a))
    t2 = (cx + r * cos(th - a), cy + r * sin(th - a))
    return f"M{px:.2f},{py:.2f} L{t1[0]:.2f},{t1[1]:.2f} A{r:.2f},{r:.2f} 0 1 1 {t2[0]:.2f},{t2[1]:.2f} Z"


def mirror_x(x):
    return 64 - x


def svg(body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Monarc Build">'
            f'{"<defs>" + defs + "</defs>" if defs else ""}{body}</svg>')


def wing(d, color, round_w=2.6):
    # the same-color stroke with round joins rounds every tip, the Google app icon softness
    return f'<path d="{d}" fill="{color}" stroke="{color}" stroke-width="{round_w}" stroke-linejoin="round"/>'


def cand_a():
    """Four teardrop wings, a white gap for the body."""
    up, lo = (30.2, 31.0, 17.0, 19.0, 12.2), (30.2, 35.0, 21.0, 45.2, 8.6)
    parts = [wing(teardrop(*up), UL), wing(teardrop(mirror_x(up[0]), up[1], mirror_x(up[2]), up[3], up[4]), UR),
             wing(teardrop(*lo), LL), wing(teardrop(mirror_x(lo[0]), lo[1], mirror_x(lo[2]), lo[3], lo[4]), LR)]
    return svg("".join(parts))


def cand_b():
    """The teardrop wings with a slim body and two round-tipped antennae."""
    up, lo = (29.0, 30.5, 16.6, 19.4, 11.8), (29.0, 35.5, 20.6, 45.0, 8.3)
    parts = [wing(teardrop(*up), UL), wing(teardrop(mirror_x(up[0]), up[1], mirror_x(up[2]), up[3], up[4]), UR),
             wing(teardrop(*lo), LL), wing(teardrop(mirror_x(lo[0]), lo[1], mirror_x(lo[2]), lo[3], lo[4]), LR)]
    body = f'<rect x="30.4" y="21.5" width="3.2" height="27" rx="1.6" fill="{INK}"/>'
    ant = (f'<path d="M31.2,22.5 Q29.5,15 25.8,10.8 M32.8,22.5 Q34.5,15 38.2,10.8" fill="none" stroke="{INK}" stroke-width="1.5" stroke-linecap="round"/>'
           f'<circle cx="25.6" cy="10.6" r="1.7" fill="{INK}"/><circle cx="38.4" cy="10.6" r="1.7" fill="{INK}"/>')
    return svg("".join(parts) + body + ant)


def cand_c():
    """Ellipse wings that overlap in a darker tone where they meet, the layering of Google's app icons."""
    defs = ('<clipPath id="L"><rect x="0" y="0" width="32" height="64"/></clipPath>'
            '<clipPath id="R"><rect x="32" y="0" width="32" height="64"/></clipPath>'
            '<ellipse id="ul" cx="18.5" cy="22" rx="15.5" ry="11" transform="rotate(-32 18.5 22)"/>'
            '<ellipse id="ll" cx="22.5" cy="39.5" rx="11.5" ry="8.5" transform="rotate(34 22.5 39.5)"/>'
            '<clipPath id="llc"><use href="#ll"/></clipPath>')
    left = (f'<g clip-path="url(#L)"><use href="#ll" fill="{LL}"/><use href="#ul" fill="{UL}"/>'
            f'<g clip-path="url(#llc)"><use href="#ul" fill="{mix(UL, LL, 0.5, 0.18)}"/></g></g>')
    right_defs = ('<ellipse id="ur" cx="45.5" cy="22" rx="15.5" ry="11" transform="rotate(32 45.5 22)"/>'
                  '<ellipse id="lr" cx="41.5" cy="39.5" rx="11.5" ry="8.5" transform="rotate(-34 41.5 39.5)"/>'
                  '<clipPath id="lrc"><use href="#lr"/></clipPath>')
    right = (f'<g clip-path="url(#R)"><use href="#lr" fill="{LR}"/><use href="#ur" fill="{UR}"/>'
             f'<g clip-path="url(#lrc)"><use href="#ur" fill="{mix(UR, LR, 0.5, 0.18)}"/></g></g>')
    return svg(left + right, defs + right_defs)


def cand_d():
    """Rounded triangles over circles: the boldest at 16px."""
    ul = "30.5,30.5 6.5,9 7.5,32"
    ur = " ".join(f"{mirror_x(float(p.split(',')[0])):.1f},{p.split(',')[1]}" for p in ul.split())
    tri = lambda pts, c: f'<polygon points="{pts}" fill="{c}" stroke="{c}" stroke-width="6" stroke-linejoin="round"/>'
    return svg(tri(ul, UL) + tri(ur, UR) +
               f'<circle cx="22.5" cy="44" r="9" fill="{LL}"/><circle cx="41.5" cy="44" r="9" fill="{LR}"/>')


def cand_e():
    """Two back-to-back D shapes, each split into an upper and a lower wing."""
    ul = "M30.8,32.5 L30.8,7 C17,5.5 4.5,11.5 4.5,22.5 C4.5,29.5 11,32.5 19,32.5 Z"
    ll = "M30.8,35.5 L30.8,56 C21,58 10.5,53.5 10.5,45.5 C10.5,39.5 16.5,35.5 24,35.5 Z"

    def flip(d):
        # mirror every x of the "x,y" pairs across the center line
        return re.sub(r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", lambda m: f"{64 - float(m.group(1)):.1f},{m.group(2)}", d)
    return svg(wing(ul, UL, 1.2) + wing(flip(ul), UR, 1.2) + wing(ll, LL, 1.2) + wing(flip(ll), LR, 1.2))


CANDIDATES = {"a": ("Teardrop wings, a gap for the body", cand_a), "b": ("Teardrop wings, body and antennae", cand_b),
              "c": ("Overlapping ellipse wings, darker where they meet", cand_c), "d": ("Rounded triangles over circles", cand_d),
              "e": ("Back-to-back D shapes, split into wings", cand_e)}


def fetch_font():
    if FONT.exists():
        return
    FONT.parent.mkdir(parents=True, exist_ok=True)
    for url, out in [(FONT_URL, FONT), (LICENSE_URL, FONT.parent / "OFL.txt")]:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=120) as r:
            out.write_bytes(r.read())


def kerning(font):
    """Pair kerning from GPOS 'kern' (PairPos formats 1 and 2): {(left, right): x advance}."""
    pairs, classes = {}, []
    if "GPOS" not in font:
        return pairs, classes
    gpos = font["GPOS"].table
    idx = set()
    for fr in gpos.FeatureList.FeatureRecord:
        if fr.FeatureTag == "kern":
            idx.update(fr.Feature.LookupListIndex)
    for i in sorted(idx):
        lk = gpos.LookupList.Lookup[i]
        subs = lk.SubTable
        if lk.LookupType == 9:
            subs = [s.ExtSubTable for s in subs]
        for st in subs:
            if getattr(st, "LookupType", 2) != 2 and st.__class__.__name__ != "PairPos":
                continue
            if st.Format == 1:
                for g1, ps in zip(st.Coverage.glyphs, st.PairSet):
                    for rec in ps.PairValueRecord:
                        v = rec.Value1.XAdvance if rec.Value1 and hasattr(rec.Value1, "XAdvance") else 0
                        if v:
                            pairs.setdefault((g1, rec.SecondGlyph), v)
            elif st.Format == 2:
                classes.append(st)
    return pairs, classes


def pair_value(pairs, classes, a, b):
    if (a, b) in pairs:
        return pairs[(a, b)]
    for st in classes:
        if a not in st.Coverage.glyphs:
            continue
        c1 = st.ClassDef1.classDefs.get(a, 0)
        c2 = st.ClassDef2.classDefs.get(b, 0)
        rec = st.Class1Record[c1].Class2Record[c2]
        v = rec.Value1.XAdvance if rec.Value1 and hasattr(rec.Value1, "XAdvance") else 0
        if v:
            return v
    return 0


def wordmark(text="Monarc Build", weight=500):
    """The name as one outlined path, in font units, y down. Returns (d, (xmin, ymin, xmax, ymax), cap height)."""
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    fetch_font()
    font = instantiateVariableFont(TTFont(FONT), {"wght": weight}, inplace=False)
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    pairs, classes = kerning(font)
    pen = SVGPathPen(gs)
    bounds = BoundsPen(gs)
    x, prev = 0, None
    for ch in text:
        gn = cmap[ord(ch)]
        if prev:
            x += pair_value(pairs, classes, prev, gn)
        g = gs[gn]
        g.draw(TransformPen(pen, (1, 0, 0, -1, x, 0)))
        g.draw(TransformPen(bounds, (1, 0, 0, -1, x, 0)))
        x += g.width
        prev = gn
    cap = getattr(font["OS/2"], "sCapHeight", 0) or 700
    return pen.getCommands(), bounds.bounds, cap


def main():
    CAND.mkdir(parents=True, exist_ok=True)
    marks = {}
    for k, (label, fn) in CANDIDATES.items():
        s = fn()
        (CAND / f"butterfly-{k}.svg").write_text(s, encoding="utf-8")
        marks[k] = (label, s)
    d, (x0, y0, x1, y1), cap = wordmark()
    pad = 8
    vb = f"{x0 - pad:.0f} {y0 - pad:.0f} {x1 - x0 + 2 * pad:.0f} {y1 - y0 + 2 * pad:.0f}"
    (HERE / "wordmark.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-label="Monarc Build"><path d="{d}" fill="currentColor"/></svg>', encoding="utf-8")
    meta = {"wordmark_viewbox": vb, "cap_height": cap, "baseline_to_top": -y0, "descender": y1}
    (HERE / "wordmark.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_sheet(marks, d, vb)
    print("wrote", ", ".join(f"butterfly-{k}.svg" for k in marks), "wordmark.svg", "sheet.html")


def write_sheet(marks, d, vb):
    grounds = [("white", "#FFFFFF", WORDMARK), ("cream", "#FAF6EE", WORDMARK), ("feed grey", "#F0F2F5", WORDMARK),
               ("dark", "#0B1220", "#F5F7FA"), ("scrim", "#2F334D", "#FFFFFF")]
    word = lambda color, h: f'<svg viewBox="{vb}" height="{h}" style="display:block;color:{color}"><path d="{d}" fill="currentColor"/></svg>'
    rows = []
    for k, (label, s) in marks.items():
        sizes = "".join(f'<div class="sz"><img src="candidates/butterfly-{k}.svg" width="{n}" height="{n}" alt="Candidate {k} at {n}px"><span>{n}</span></div>' for n in (16, 32, 48, 180))
        zoom = f'<div class="sz"><canvas class="px" data-src="candidates/butterfly-{k}.svg" width="96" height="96"></canvas><span>16px, zoomed</span></div>'
        locks = "".join(f'<div class="lock" style="background:{bg}"><span class="bf">{s}</span>{word(fg, 20)}<em style="color:{fg}">{n}</em></div>' for n, bg, fg in grounds)
        rows.append(f'<section><h2>{k.upper()}. {label}</h2><div class="sizes">{sizes}{zoom}</div><div class="locks">{locks}</div></section>')
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Monarc Build mark: candidates</title>
<style>
body{{margin:0;padding:40px;font:400 14px/1.4 Roboto,Arial,sans-serif;color:#202124;background:#fff}}
h1{{font-size:22px;font-weight:500;margin:0 0 6px}} p.note{{margin:0 0 28px;color:#5F6368}}
section{{border-top:1px solid #DADCE0;padding:22px 0}} h2{{font-size:16px;font-weight:500;margin:0 0 14px}}
.sizes{{display:flex;align-items:flex-end;gap:28px;margin-bottom:16px}} .sz{{display:grid;justify-items:center;gap:6px;color:#70757A;font-size:12px}}
.px{{width:96px;height:96px;image-rendering:pixelated;border:1px solid #DADCE0}}
.locks{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}}
.lock{{display:flex;align-items:center;gap:8px;padding:16px 14px;border-radius:12px;position:relative;min-height:44px;overflow:hidden}}
.lock .bf svg{{width:30px;height:30px;display:block;flex:none}} .lock em{{position:absolute;right:10px;bottom:6px;font-style:normal;font-size:10px;opacity:.6}}
</style></head><body>
<h1>Monarc Build mark: five candidates</h1>
<p class="note">Four Monarc hues: blue {BLUE}, coral {CORAL}, teal {TEAL}, amber {AMBER}. Each row: the favicon sizes, the real 16px pixels zoomed, then the lockup with "Monarc Build" in Outfit 500 outlines on the five grounds it will sit on.</p>
{''.join(rows)}
<script>
window.addEventListener('load', function(){{
  document.querySelectorAll('canvas.px').forEach(function(cv){{
    var img = new Image(); img.onload = function(){{
      var s = document.createElement('canvas'); s.width = 16; s.height = 16;
      var sx = s.getContext('2d'); sx.fillStyle = '#fff'; sx.fillRect(0,0,16,16); sx.drawImage(img, 0, 0, 16, 16);
      var c = cv.getContext('2d'); c.imageSmoothingEnabled = false; c.drawImage(s, 0, 0, 96, 96);
    }}; img.src = cv.dataset.src;
  }});
}});
</script>
</body></html>"""
    (HERE / "sheet.html").write_text(html, encoding="utf-8")


ROOT = HERE.parents[2]
SITE = ROOT / "projects" / "monarcbuild-site" / "public_html"
BUILD = HERE.parent / "build"


def browser():
    sys.path.insert(0, str(ROOT / ".claude" / "skills" / "landing-page" / "assets"))
    from render import find_browser
    return find_browser()


def shoot(html, out, size=1024):
    """Screenshot an HTML string on a transparent ground at size x size (headless Chrome or Edge)."""
    page = out.with_suffix(".shoot.html")
    page.write_text(html, encoding="utf-8")
    subprocess.run([browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000",
                    "--force-device-scale-factor=1", f"--window-size={size},{size}", f"--screenshot={out}", page.as_uri()],
                   check=True, capture_output=True)
    page.unlink(missing_ok=True)


def inner(svg_text):
    return re.search(r"<svg[^>]*>(.*)</svg>", svg_text, re.S).group(1)


def export(k):
    from PIL import Image
    src = CAND / f"butterfly-{k}.svg"
    body = inner(src.read_text(encoding="utf-8"))
    tmp = HERE / "export"
    tmp.mkdir(exist_ok=True)

    # 1. tight bounds, from a 1024px transparent render of the 64-unit box (16px per unit)
    probe = tmp / "probe.png"
    shoot(f'<!doctype html><html style="background:transparent"><body style="margin:0;background:transparent">'
          f'<img src="{src.as_uri()}" width="1024" height="1024" style="display:block"></body></html>', probe)
    x0, y0, x1, y1 = Image.open(probe).convert("RGBA").split()[3].getbbox()
    bx0, by0, bx1, by1 = x0 / 16, y0 / 16, x1 / 16, y1 / 16
    cx, cy, side = (bx0 + bx1) / 2, (by0 + by1) / 2, max(bx1 - bx0, by1 - by0) * 1.04
    square = f"{cx - side / 2:.2f} {cy - side / 2:.2f} {side:.2f} {side:.2f}"
    tight = (bx0, by0, bx1 - bx0, by1 - by0)

    mark_svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{square}" role="img" aria-label="Monarc Build">{body}</svg>')
    (SITE / "assets" / "brand").mkdir(parents=True, exist_ok=True)
    (SITE / "favicon.svg").write_text(mark_svg, encoding="utf-8")
    (SITE / "assets" / "brand" / "butterfly.svg").write_text(mark_svg, encoding="utf-8")

    # 2. the lockup: the mark 100 units tall, the name's cap height 46 units centered on it, a 24 unit gap
    meta = json.loads((HERE / "wordmark.json").read_text(encoding="utf-8"))
    wx, wy, ww, wh = (float(v) for v in meta["wordmark_viewbox"].split())
    d = re.search(r'<path d="([^"]+)"', (HERE / "wordmark.svg").read_text(encoding="utf-8")).group(1)
    s_icon = 100 / tight[3]
    icon_w = tight[2] * s_icon
    s_word = 46 / meta["cap_height"]
    left_bearing = wx + 8  # the wordmark viewBox carries an 8 unit pad
    word_x = icon_w + 24
    word_w = (ww - 16) * s_word
    total_w = word_x + word_w + 2
    icon_g = f'<g transform="scale({s_icon:.4f}) translate({-tight[0]:.3f},{-tight[1]:.3f})">{body}</g>'
    word_g = lambda fill: (f'<g transform="translate({word_x:.2f},73) scale({s_word:.5f}) translate({-left_bearing:.1f},0)">'
                           f'<path d="{d}" fill="{fill}"/></g>')
    lockup = lambda fill, extra="": (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w:.1f} 100"{extra} role="img" '
                                     f'aria-label="Monarc Build">{icon_g}{word_g(fill)}</svg>')
    (SITE / "assets" / "brand" / "lockup.svg").write_text(lockup(WORDMARK), encoding="utf-8")
    (SITE / "assets" / "brand" / "lockup-white.svg").write_text(lockup("#FFFFFF"), encoding="utf-8")
    snippet = lockup("currentColor", ' class="lockup-svg" focusable="false"').replace(' xmlns="http://www.w3.org/2000/svg"', "")
    (BUILD / "brand-lockup.html").write_text(
        "<!-- The Monarc Build lockup: the butterfly (candidate " + k.upper() + ", Jonathan's pick 2026-09-26) and the name in Outfit 500 "
        "outlines. Made by projects/Landing Page Build/brand/make_brand.py; do not edit by hand. The name takes currentColor. -->\n"
        + snippet + "\n", encoding="utf-8")

    # 3. raster icons, each drawn by the browser at its own size (clean antialiasing), then cut out
    sizes = [16, 32, 48, 180, 512]
    xs, x = [], 0
    for n in sizes:
        xs.append(x)
        x += n + 8
    fav = SITE / "favicon.svg"
    imgs = "".join(f'<img src="{fav.as_uri()}" width="{n}" height="{n}" style="position:absolute;left:{xx}px;top:0">' for n, xx in zip(sizes, xs))
    sheet = tmp / "sizes.png"
    shoot(f'<!doctype html><html style="background:transparent"><body style="margin:0;background:transparent;position:relative">{imgs}</body></html>', sheet, 1024)
    big = Image.open(sheet).convert("RGBA")
    cut = {n: big.crop((xx, 0, xx + n, n)) for n, xx in zip(sizes, xs)}
    cut[512].save(SITE / "assets" / "brand" / "butterfly-512.png", optimize=True)
    # Pillow keeps only the sizes at or under the base image, so the 48px cut is the base and the 16 and 32 cuts ride along
    cut[48].save(SITE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=[cut[16], cut[32]])
    # apple-touch-icon: the mark at about 72 percent of a white 180px square (iOS rounds the corners itself)
    touch = Image.new("RGBA", (180, 180), (255, 255, 255, 255))
    m = cut[512].resize((130, 130), Image.LANCZOS)
    touch.alpha_composite(m, (25, 25))
    touch.convert("RGB").save(SITE / "apple-touch-icon.png", optimize=True)
    for p in (probe, sheet):
        p.unlink(missing_ok=True)
    try:
        tmp.rmdir()
    except OSError:
        pass
    print(f"exported candidate {k}: favicon.svg (viewBox {square}), favicon.ico, apple-touch-icon.png, "
          f"assets/brand/butterfly.svg, butterfly-512.png, lockup.svg, lockup-white.svg, build/brand-lockup.html "
          f"(lockup {total_w:.0f} x 100 units)")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "export":
        export(sys.argv[2])
    else:
        main()
