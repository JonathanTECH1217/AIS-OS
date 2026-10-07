"""Write the Google Ads location list from the Places grid.

Usage: python scripts/ads_geo_export.py [out]

Reads LOCATIONS from scripts/places_grid.py (the 213 metros and enclaves behind the
national seed, decision 2026-09-13) and writes one line per location in the form Google
Ads' bulk location box accepts ("City, ST, United States"). Default output:
projects/google-ads/geo-targets.txt. Paste the file's lines into Campaign settings,
Locations, "Enter another location", "Add locations in bulk". Google matches each line to
its own city or neighborhood target; a line it cannot match is listed back for a hand pick.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from places_grid import LOCATIONS  # noqa: E402

OUT = HERE.parent / "projects" / "google-ads" / "geo-targets.txt"


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    lines = []
    seen = set()
    for loc in LOCATIONS:
        loc = " ".join(str(loc).split())
        if not loc or loc.lower() in seen:
            continue
        seen.add(loc.lower())
        lines.append(loc if loc.lower().endswith("united states") else f"{loc}, United States")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(lines)} locations written to {out}")


if __name__ == "__main__":
    main()
