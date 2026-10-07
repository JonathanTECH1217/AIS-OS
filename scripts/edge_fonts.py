"""Fetch Monarc Edge's fonts into projects/edge/fonts/ (2026-10-04).

The CRM's Google look (Google Sans, Google Sans Text, a Material Symbols subset, through crm_fonts.build), served by
the Edge server itself so the look holds offline. To use a new icon in the page, add its name to ICONS
(https://fonts.google.com/icons) and run:

  python scripts/edge_fonts.py
"""
import urllib.error
from pathlib import Path

import crm_fonts

OUT = Path(__file__).resolve().parent.parent / "projects" / "edge" / "fonts"

ICONS = sorted(set("""
check close warning trending_up trending_down lock lock_open refresh schedule sports_soccer payments history settings
play_arrow stop pause done_all error info open_in_new bolt visibility more_vert arrow_drop_down expand_more expand_less
cancel flag timer account_balance_wallet
""".split()))


def valid_icons(names):
    """Drop names the Material Symbols API does not know (one bad name fails the whole request)."""
    base = ("https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,300..500,"
            "0..1,0&icon_names=")
    try:
        crm_fonts.get(base + ",".join(names))
        return names
    except urllib.error.HTTPError:
        pass
    good = []
    for n in names:
        try:
            crm_fonts.get(base + n)
            good.append(n)
        except urllib.error.HTTPError:
            print(f"  skipped unknown icon: {n}")
    return good


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    crm_fonts.build(OUT, valid_icons(ICONS), writer="scripts/edge_fonts.py")
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name} {p.stat().st_size}")


if __name__ == "__main__":
    main()
