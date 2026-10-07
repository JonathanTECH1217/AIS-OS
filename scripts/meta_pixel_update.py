"""Meta wiring for every page that carries the shared booking popup (the Meta ads plan, 2026-10-03).

Usage: python scripts/meta_pixel_update.py [--check] [--pixel <PIXEL_ID>]

Two edits, each applied once per page, in the site mirror only (nothing is pushed; the push is Jonathan's go):

1. ``fbclid`` joins the popup's capture keys (``var KEYS = [...]``), so a Meta click id rides on the booking the way
   ``gclid`` and ``li_fat_id`` do. The booking script's TAG_KEYS carries it too (scripts/avmarketing-booking.gs).
   Runs with no argument.
2. With ``--pixel <id>``: the Meta Pixel base code (PageView on every page) goes in the head right before the
   ``journey.js`` tag. The events (CheckStarted, Lead, Schedule) live on /builder-check/ only and are written by that
   page's build (projects/meta-ads/check.md), not here. scripts/page_shot.py already blocks connect.facebook.net, so the
   CRM's page copies never fire it.

Pages: every index.html under the site mirror with the popup, the /av_marketing/ staging copies (the push source and
the pushed copy), and the archived /website-build/ build that scripts/build_service_page.py copies the popup from, so a
rebuilt page keeps the changes. The privacy page gets the Pixel too (it carries no popup; its two Meta lines were added
by hand 2026-10-03). A second run reports "already done". --check changes nothing and lists what would change.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "projects" / "monarcbuild-site"
PAGES = sorted(p for p in (SITE / "public_html").rglob("index.html") if "_wireframe" not in p.parts) + [
    SITE / "staging" / "av_marketing" / "index.html",
    SITE / "staging" / "av_marketing" / "index-push.html",
    ROOT / "archives" / "site-website-build-house-2026-09-25" / "index.html",
]

KEYS_OLD = '"li_fat_id","gclid"];'
KEYS_NEW = '"li_fat_id","gclid","fbclid"];'
ANCHOR = '<script src="/assets/journey.js" defer></script>\n'
PIXEL = (
    "<!-- Meta Pixel (base code, PageView; the events are on /builder-check/ only) -->\n"
    "<script>\n"
    "!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};"
    "if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;"
    "s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');\n"
    "fbq('init', '{pixel}');\n"
    "fbq('track', 'PageView');\n"
    "</script>\n"
    '<noscript><img height="1" width="1" style="display:none" src="https://www.facebook.com/tr?id={pixel}&ev=PageView&noscript=1"/></noscript>\n'
)


def main():
    args = sys.argv[1:]
    check = "--check" in args
    pixel = args[args.index("--pixel") + 1] if "--pixel" in args and args.index("--pixel") + 1 < len(args) else ""
    if pixel and not pixel.isdigit():
        print(f"--pixel wants the numeric Pixel id from Events Manager, got {pixel!r}")
        return 2
    for p in PAGES:
        if not p.exists():
            print(f"missing: {p.relative_to(ROOT)}")
            continue
        raw = p.read_bytes().decode("utf-8")
        crlf = "\r\n" in raw
        t = raw.replace("\r\n", "\n")
        notes = []
        if "var KEYS = [" in t:
            if KEYS_NEW in t:
                notes.append("fbclid already there")
            elif KEYS_OLD in t:
                t = t.replace(KEYS_OLD, KEYS_NEW, 1)
                notes.append("fbclid added")
            else:
                notes.append("KEYS line not in the expected shape, fbclid NOT added")
        if pixel:
            if "fbq('init'" in t:
                notes.append("pixel already there")
            elif ANCHOR in t:
                t = t.replace(ANCHOR, PIXEL.format(pixel=pixel) + ANCHOR, 1)
                notes.append("pixel added")
            else:
                notes.append("no journey.js tag to anchor on, pixel NOT added")
        name = p.relative_to(ROOT)
        if not notes:
            continue
        changed = t != raw.replace("\r\n", "\n")
        print(f"{name}: " + ", ".join(notes))
        if changed and not check:
            p.write_bytes((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
