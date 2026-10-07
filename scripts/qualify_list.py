"""Qualify the integrator list for calling, on reviews alone.

Rules (Jonathan, 2026-09-11):
  1. Must have a website.
  2. Cannot be in DC, Maryland, or Virginia (agreement with the Annapolis integrator).
  3. Google review count between 0 and 30 inclusive. A listing with no count shown counts as 0
     and is flagged "Reviews shown = no" so it can be filtered out later.

Usage:
  python scripts/qualify_list.py [input.xlsx] [output-stem]
Defaults: input = %USERPROFILE%/Downloads/Integrator_List_2026-09-05.xlsx (falls back to the repo copy),
          output = projects/outreach/qualified-list-YYYY-MM-DD

Writes <stem>.xlsx (sheets: Qualified, Excluded) and <stem>.csv (Qualified only, Airtable import ready).
"""
import csv
import os
import re
import sys
from datetime import date
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IN = Path(os.path.expanduser("~")) / "Downloads" / "Integrator_List_2026-09-05.xlsx"
REPO_IN = ROOT / "projects" / "outreach" / "Integrator_List_2026-09-05.xlsx"
EXCLUDED_STATES = {"DC", "MD", "VA"}
MAX_REVIEWS = 30

OUT_COLS = [
    "Name", "City", "State", "Zip", "County", "Phone", "Local time at noon ET",
    "Rating", "Review count", "Reviews shown", "Listings", "Website", "Status", "Source",
]


def parse_reviews(value):
    """'5 (16)' -> (5.0, 16, True). None or no count -> (rating or None, 0, False)."""
    if value is None:
        return None, 0, False
    text = str(value)
    count = re.search(r"\((\d[\d,]*)\)", text)
    rating = re.match(r"\s*([\d.]+)", text)
    rating_val = float(rating.group(1)) if rating else None
    if count:
        return rating_val, int(count.group(1).replace(",", "")), True
    return rating_val, 0, False


def domain_of(url):
    """'https://www.regent5.com/pages/x' -> 'regent5.com'. Empty when no website."""
    if not url:
        return ""
    host = re.sub(r"^https?://", "", url.strip().lower()).split("/")[0].split("?")[0]
    return host[4:] if host.startswith("www.") else host


def parse_address(address):
    """'1300 Industrial Rd Ste 12, San Carlos, CA 94070, USA' -> ('San Carlos', '94070')."""
    if not address:
        return "", ""
    parts = [p.strip() for p in str(address).split(",")]
    city, zip_code = "", ""
    for i, part in enumerate(parts):
        m = re.match(r"^([A-Z]{2})\s+(\d{5})(?:-\d{4})?$", part)
        if m:
            zip_code = m.group(2)
            city = parts[i - 1] if i >= 1 else ""
            break
    return city, zip_code


def main(argv):
    src = Path(argv[1]) if len(argv) > 1 else (DEFAULT_IN if DEFAULT_IN.exists() else REPO_IN)
    stem = Path(argv[2]) if len(argv) > 2 else ROOT / "projects" / "outreach" / f"qualified-list-{date.today():%Y-%m-%d}"
    wb = openpyxl.load_workbook(src, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(h) for h in rows[0]]
    ix = {h: i for i, h in enumerate(hdr)}

    # Pass 1: one record per listing.
    recs = []
    for r in rows[1:]:
        if not r[ix["Name"]]:
            continue
        state = str(r[ix["State"]] or "").strip().upper()
        website = str(r[ix["Website"]] or "").strip()
        rating, count, shown = parse_reviews(r[ix["Reviews"]])
        city, zip_code = parse_address(r[ix["Address"]])
        recs.append({
            "Name": r[ix["Name"]], "City": city, "State": state, "Zip": zip_code,
            "County": r[ix["County"]], "Phone": r[ix["Phone"]],
            "Local time at noon ET": r[ix["Local Time @ 12pm ET"]],
            "Rating": rating, "Review count": count, "Reviews shown": "yes" if shown else "no",
            "Website": website, "Status": r[ix["Status"]], "Source": "cold",
            "Domain": domain_of(website), "Listings": 1,
        })

    # Pass 2: one company per website domain. The listing with the most reviews represents the
    # company (same convention as the seed list), and the company is judged on that count.
    groups = {}
    for rec in recs:
        key = rec["Domain"] or f"__row{id(rec)}"
        groups.setdefault(key, []).append(rec)

    qualified, excluded = [], []
    for key, listings in groups.items():
        rep = max(listings, key=lambda x: x["Review count"])
        rep["Listings"] = len(listings)
        others = [l for l in listings if l is not rep]
        reason = None
        if not rep["Website"]:
            reason = "no website"
        elif rep["State"] in EXCLUDED_STATES:
            reason = f"state {rep['State']}"
        elif rep["Review count"] > MAX_REVIEWS:
            reason = f"{rep['Review count']} reviews, over {MAX_REVIEWS}"
        if reason:
            excluded.append({**rep, "Excluded because": reason})
            for l in others:
                excluded.append({**l, "Excluded because": f"duplicate listing of {rep['Name']}; company {reason}"})
        else:
            qualified.append(rep)
            for l in others:
                excluded.append({**l, "Excluded because": f"duplicate listing of {rep['Name']} (kept the listing with most reviews)"})

    out = openpyxl.Workbook()
    ws_q = out.active
    ws_q.title = "Qualified"
    ws_q.append(OUT_COLS)
    for rec in qualified:
        ws_q.append([rec[c] for c in OUT_COLS])
    ws_x = out.create_sheet("Excluded")
    ws_x.append(OUT_COLS + ["Excluded because"])
    for rec in excluded:
        ws_x.append([rec[c] for c in OUT_COLS] + [rec["Excluded because"]])
    ws_m = out.create_sheet("Method")
    for line in __doc__.strip().splitlines():
        ws_m.append([line])
    ws_m.append([f"Source file: {src}"])
    stem.parent.mkdir(parents=True, exist_ok=True)
    out.save(str(stem) + ".xlsx")
    with open(str(stem) + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(qualified)

    by_state = {}
    for rec in qualified:
        by_state[rec["State"]] = by_state.get(rec["State"], 0) + 1
    print(f"source: {src}")
    print(f"qualified: {len(qualified)}  (no review count shown, counted as 0: {sum(1 for q in qualified if q['Reviews shown'] == 'no')})")
    print(f"excluded: {len(excluded)}")
    reasons = {}
    for rec in excluded:
        why = rec["Excluded because"]
        if why.startswith("duplicate listing"):
            key = "duplicate listing (company kept)" if "kept the listing" in why else "duplicate listing (company excluded)"
        elif "reviews, over" in why:
            key = f"over {MAX_REVIEWS} reviews"
        else:
            key = why
        reasons[key] = reasons.get(key, 0) + 1
    print("excluded by reason:", dict(sorted(reasons.items(), key=lambda kv: -kv[1])))
    print("qualified by state:", dict(sorted(by_state.items(), key=lambda kv: -kv[1])[:20]))
    print(f"wrote {stem}.xlsx and {stem}.csv")


if __name__ == "__main__":
    main(sys.argv)
