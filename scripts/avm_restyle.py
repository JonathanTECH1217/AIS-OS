"""/av_marketing/ in the homepage look (the monarc theme), look only (Jonathan, 2026-09-30).

Usage: python scripts/avm_restyle.py

Interview: brainstorms/2026-09-30-av-marketing-google-look.md (Q1 to Q7). Every block and word stays (Q2); this re-maps
the house palette and faces through one marked override block at the end of the page's style, swaps the font link to
Roboto, and adds the hero eyebrow "Marketing for AV integrators" (Q7). Reads the staging copy (the live page plus the
approved logo banner), keeps the before copies in archives/site-av_marketing-2026-09-30/, and writes the result to
staging/av_marketing/ and to the mirror, so the local server can render it. Pushes nothing.
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "projects" / "monarcbuild-site"
STAGING = SITE / "staging" / "av_marketing" / "index.html"
MIRROR = SITE / "public_html" / "av_marketing" / "index.html"
ARCHIVE = ROOT / "archives" / "site-av_marketing-2026-09-30"
MARK = "/* === monarc theme override"

OLD_FONTS = re.compile(r'<link href="https://fonts\.googleapis\.com/css2\?family=Cormorant\+Garamond[^"]*" rel="stylesheet">')
NEW_FONTS = '<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap" rel="stylesheet">'
EYEBROW = '<span class="label eyebrow">Marketing for AV integrators</span>\n'

CSS = """
/* === monarc theme override (Jonathan, 2026-09-30: "update the creative style to match the Google-esque style").
   brainstorms/2026-09-30-av-marketing-google-look.md: Q1 the homepage look (white, Roboto, the butterfly's four hues,
   butterfly blue buttons); Q2 look only, every block and word stays; Q3 and Q4 the full-bleed photo under a #202124
   wash, darker at the top; Q5 the services on the light band as white flip cards with the hues on their icons; Q6
   "Page 1" in butterfly blue; Q7 the eyebrow. The house variables above are re-mapped here, so the rules above keep
   working: --oak is now the button blue, --blue the ink, --sand the light band, --paper white; hairlines get --line. */
:root{--oak:#1F5ED8;--blue:#202124;--charcoal:#3C4043;--stone:#5F6368;--sand:#F8F9FA;--paper:#FFFFFF;--white:#FFFFFF;
--line:#DADCE0;--teal:#169C86;--coral:#E8604C;--amber:#F2A93B;
--serif:Roboto,system-ui,-apple-system,'Segoe UI',Arial,sans-serif;--sans:Roboto,system-ui,-apple-system,'Segoe UI',Arial,sans-serif}
body{color:var(--charcoal)}
h1,h2,h3{font-weight:400;letter-spacing:-0.01em}
h2{letter-spacing:-0.005em}
.sub{font-size:20px;line-height:1.5}
.btn,.step-btn{font-weight:500}
/* section labels: plain tracked caps in grey, no hairlines (the homepage rule, 2026-09-27) */
.label.rule::before,.label.rule::after{display:none !important}
.label{color:var(--stone)}
.head.center > .label{justify-self:center;justify-content:center}
.band .label{color:var(--stone)}
.band .sub,.band .caption,.band p{color:var(--charcoal)}
section.band{color:var(--blue)}
/* hero: the colonial photo under Google's near-black, darker at the top (Q3, Q4); the eyebrow above the h1 (Q7) */
.hero-bg::after{background:linear-gradient(180deg,rgba(32,33,36,0.80),rgba(32,33,36,0.56))}
.hero .eyebrow{color:rgba(255,255,255,0.86)}
.hero .btn:focus-visible{outline-color:var(--white)}
/* hairlines */
.ticker{border-top-color:var(--line);border-bottom-color:var(--line)}
.row{border-top-color:var(--line)}
.fit-cols .vr{background:var(--line);opacity:1}
.faq details{border-top-color:var(--line)}
.faq details:last-of-type{border-bottom-color:var(--line)}
footer{border-top-color:var(--line)}
/* proof: "Page 1" in butterfly blue (Q6); the case cards as the homepage's cards, 16px corners and a thin border */
.rows .fig{color:var(--oak);white-space:nowrap}
.row{grid-template-columns:auto 1fr;gap:40px}
.proof .line{font-size:20px}
.cards .face{border:1px solid var(--line);border-radius:16px;overflow:hidden}
.cards .face.front{padding:0;gap:0}
.cards .cap{padding:14px 16px 16px}
.card .title{font-size:20px;font-weight:500;color:var(--blue)}
/* services: the light band, white flip cards, the four hues on the icons (Q5) */
#services{background:var(--sand)}
#services .label{color:var(--stone)}
#services h2{color:var(--blue)}
#services .sub{color:var(--charcoal)}
#services .card:focus-visible{outline-color:var(--oak)}
.svc-card .face{border:1px solid var(--line);border-radius:16px}
.svc-card .ttl{font-size:22px;color:var(--blue)}
.svc-card .txt{color:var(--charcoal)}
#services .svc-card .label,#services .svc-card .hint{color:var(--stone)}
.svc-icon{stroke-width:1.7}
ol.services li:nth-child(4n+1) .svc-icon,ol.services li:nth-child(4n+1) .svc-visual{color:#1F5ED8}
ol.services li:nth-child(4n+2) .svc-icon,ol.services li:nth-child(4n+2) .svc-visual{color:#E8604C}
ol.services li:nth-child(4n+3) .svc-icon,ol.services li:nth-child(4n+3) .svc-visual{color:#169C86}
ol.services li:nth-child(4n+4) .svc-icon,ol.services li:nth-child(4n+4) .svc-visual{color:#F2A93B}
/* fit: teal and coral on the headings and the marks only (Color 3) */
.fit-cols > div:first-child h3,.fit-cols > div:first-child li::before{color:var(--teal)}
.fit-cols > div:last-child h3,.fit-cols > div:last-child li::before{color:var(--coral)}
/* popup, calendar, and form in the theme: white panel with 16px corners, 8px tiles and fields */
.modal{background:rgba(32,33,36,0.55)}
.dialog{border-radius:16px}
.close{border-color:var(--line)}
.q{font-size:28px}
.q .num{border-radius:4px}
.cal-title{font-size:20px}
.cal-nav{border-color:var(--line)}
.day{border-radius:8px}
.day.open{border-color:var(--line)}
.day.open:hover{border-color:var(--oak)}
.day.picked{background:var(--sand);border-color:var(--oak)}
.opt{border-color:var(--line);border-radius:8px}
.opt .key{border-radius:4px}
.opt:has(input:checked),.opt.is-checked{border-color:var(--oak);background:var(--sand)}
.opt:has(input:checked) .key,.opt.is-checked .key{border-color:var(--oak);color:var(--oak)}
.field input{border-color:var(--line);border-radius:8px}
.field input:focus{border-color:var(--oak)}
@media (max-width:767px){.dialog{border-radius:0}.step-nav{border-top-color:var(--line)}.q{font-size:24px}}
"""


def main():
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    for src, name in ((STAGING, "staging-before.html"), (MIRROR, "mirror-before.html")):
        if src.exists() and not (ARCHIVE / name).exists():
            shutil.copy2(src, ARCHIVE / name)
    t = (ARCHIVE / "staging-before.html").read_text(encoding="utf-8")
    assert MARK not in t, "the staging copy is already restyled"
    t, n = OLD_FONTS.subn(NEW_FONTS, t)
    assert n == 1, "font link not found"
    h1 = "<h1>Book more quality leads as an AV contractor.</h1>"
    assert t.count(h1) == 1
    t = t.replace(h1, EYEBROW + h1)
    # the house hexes change at the source too, so no stale color is left in the page (drift, Color 2)
    old_root = "--oak:#61534E;--blue:#2F334D;--charcoal:#4B4C5C;--stone:#6E6E78;--sand:#C2B3A9;--paper:#F6F3EF;"
    assert t.count(old_root) == 1, "the house :root line changed"
    t = t.replace(old_root, "--oak:#1F5ED8;--blue:#202124;--charcoal:#3C4043;--stone:#5F6368;--sand:#F8F9FA;--paper:#FFFFFF;")
    t = t.replace("rgba(47,51,77,", "rgba(32,33,36,")  # the old Charcoal Blue scrims, now the ink
    end = t.find("</style>")
    t = t[:end] + CSS + t[end:]
    for dest in (STAGING, MIRROR):
        dest.write_text(t, encoding="utf-8", newline="\r\n")  # the file is CRLF, as served
    print(f"wrote {STAGING.relative_to(ROOT)} and {MIRROR.relative_to(ROOT)} ({len(t)} bytes); before copies in {ARCHIVE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
