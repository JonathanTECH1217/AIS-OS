"""The Monarc Build lockup and favicon links on the pages that are not built from parts (Jonathan, 2026-09-26: the new
logo and favicon on every page; brainstorms/2026-09-26-homepage-google-rebuild.md Q10).

Usage: python scripts/brand_mark.py

The homepage and the six service pages get the lockup from scripts/build_service_page.py (the <!-- brand-lockup -->
marker in their body files). This script handles the rest: /about/ and /book/ (the old export's header: the M square
and "MONARC BUILD" become the linked lockup), /privacy/ (the brand text becomes the linked lockup), and /av_marketing/
(the brand text over the hero scrim becomes the unlinked lockup with the name in white: an ad page carries no links off
it, Style Guide 6.1). The lockup is build/brand-lockup.html (made by brand/make_brand.py) with the name's color drawn
into the SVG, so no page gains a CSS color its theme does not list. Each page also gets the three favicon links.

The first run finds the old markup; after that the lockup sits between <!-- brand-mark --> markers and the head block
between <!-- brand-mark-assets --> markers, so a rerun replaces them in place.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "projects" / "monarcbuild-site" / "public_html"
SNIPPET = ROOT / "projects" / "Landing Page Build" / "build" / "brand-lockup.html"

OLD_HEADER_MARK = r'<a href="/" class="flex items-center gap-3"><svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true">.*?</svg><span class="mb-display text-sm font-black tracking-tight">MONARC BUILD</span></a>'
PAGES = [  # file, the old markup to find on the first run, linked or not, the name's color, the lockup height in px
    # /about/ left this list 2026-09-27: it is built from parts now (build_service_page.py about), lockup included
    ("book/index.html", OLD_HEADER_MARK, True, "#5F6368", 30),
    ("privacy/index.html", r'<span class="brand"><a href="/">Monarc Build</a></span>', True, "#5F6368", 34),
    ("av_marketing/index.html", r'<span class="brand">Monarc Build</span>', False, "#FFFFFF", 34),
]
FAVICONS = ('<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" href="/favicon.svg" type="image/svg+xml">'
            '<link rel="apple-touch-icon" href="/apple-touch-icon.png">')


def lockup_svg(fill):
    s = SNIPPET.read_text(encoding="utf-8")
    s = re.sub(r"<!--.*?-->\s*", "", s, flags=re.S).strip()
    return s.replace('fill="currentColor"', f'fill="{fill}"')


def assets(height):
    return ("<!-- brand-mark-assets -->" + FAVICONS +
            f"<style>.lockup{{display:inline-flex;align-items:center;line-height:0;text-decoration:none}}"
            f".lockup-svg{{display:block;height:{height}px;width:auto}}"
            f"@media (max-width:767px){{.lockup-svg{{height:{height - 4}px}}}}</style><!-- /brand-mark-assets -->")


def apply(text, find, linked, fill, height):
    svg = lockup_svg(fill)
    mark = (f'<a class="lockup" href="/" aria-label="Monarc Build home">{svg}</a>' if linked else f'<span class="lockup">{svg}</span>')
    block = f"<!-- brand-mark -->{mark}<!-- /brand-mark -->"
    if "<!-- brand-mark -->" in text:
        text = re.sub(r"<!-- brand-mark -->.*?<!-- /brand-mark -->", lambda m: block, text, flags=re.S)
    else:
        text, n = re.subn(find, lambda m: block, text, count=1, flags=re.S)
        if not n:
            raise SystemExit("old brand markup not found")
    text = re.sub(r'<link rel="icon" href="/favicon\.svg"\s*/?>', "", text)  # the old single icon link; the block carries all three
    if "<!-- brand-mark-assets -->" in text:
        text = re.sub(r"<!-- brand-mark-assets -->.*?<!-- /brand-mark-assets -->", lambda m: assets(height), text, flags=re.S)
    else:
        text = text.replace("</head>", assets(height) + "\n</head>", 1)
    return text


def main():
    for rel, find, linked, fill, height in PAGES:
        p = SITE / rel
        before = p.read_text(encoding="utf-8")
        after = apply(before, find, linked, fill, height)
        p.write_text(after, encoding="utf-8")
        print(f"{rel}: lockup {'linked' if linked else 'unlinked'}, name {fill}, {height}px{' (changed)' if after != before else ' (no change)'}")


if __name__ == "__main__":
    main()
