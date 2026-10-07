"""Research on one company: what its public page says and what its Google profile holds (2026-10-05).

The hands under the /research skill. Each read lands in projects/research/<slug>/ so the landing page skill, the SDR,
and the clone can use it without reading the company again.

  python scripts/research.py site <url> [--name slug]
        one public page: title, headings, word count, phone, colors, faces, social links, and every picture with a
        note when its file name says it is AI-made or a logo. Free. Writes site.json and site.html.
  python scripts/research.py google "<company name and address>" [--name slug] [--photos]
        the Google Business Profile through the Places API: rating, review count, the reviews Google hands out (five
        at most, names cut to a first name and a last initial), and with --photos the profile's photos (ten at most)
        and one sheet of them to look at. About 4 cents, about 12 with photos. Writes google.json and photos/.

The Instagram feed and its numbers are a separate script, scripts/instagram_api.py: they need the account's own
sign-in, so they cannot be read for a company that has not connected (references/instagram-api.md).

Keys: GOOGLE_MAPS_API_KEY through outreach_common (references/credentials.md).
"""
import argparse
import collections
import html
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import ROOT, get_secret  # noqa: E402

OUT = ROOT / "projects" / "research"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}
PLACES = "https://places.googleapis.com/v1"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:50] or "company"


def folder(name):
    d = OUT / slug(name)
    d.mkdir(parents=True, exist_ok=True)
    return d


def plain(markup):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", markup))).strip()


# ---------------------------------------------------------------- one public page

def cmd_site(a):
    r = requests.get(a.url, headers=UA, timeout=40)
    r.raise_for_status()
    t = r.text
    body = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>", " ", t)
    heads = [{"tag": tag, "text": plain(m)[:160]} for tag in ("h1", "h2", "h3")
             for m in re.findall(rf"(?is)<{tag}\b[^>]*>(.*?)</{tag}>", body) if plain(m)]
    pics, seen = [], set()
    for m in re.finditer(r"(?is)<img\b[^>]*>", body):
        src = re.search(r'(?:data-src|data-image|nitro-lazy-src|src)="([^"]+)"', m.group(0))
        if not src or src.group(1).startswith("data:"):
            continue
        u = urljoin(r.url, src.group(1)).split("?")[0]
        if u in seen:
            continue
        seen.add(u)
        name = u.rsplit("/", 1)[-1]
        alt = re.search(r'alt="([^"]*)"', m.group(0))
        note = ("AI-made by its file name" if re.search(r"chatgpt|dall|midjourney|generated|gemini_", name, re.I)
                else "a logo or an icon" if re.search(r"logo|icon|badge|favicon", name, re.I) else "")
        pics.append({"url": u, "alt": (alt.group(1) if alt else "")[:120], "note": note})
    text = plain(body)
    host = urlparse(r.url).netloc.replace("www.", "")
    d = folder(a.name or host.split(".")[0])
    out = {
        "read": date.today().isoformat(), "url": r.url,
        "title": plain((re.findall(r"(?is)<title[^>]*>(.*?)</title>", t) or [""])[0]),
        "description": html.unescape((re.findall(r'<meta name="description" content="(.*?)"', t) or [""])[0]),
        "words": len(text.split()), "headings": heads,
        "phones": sorted(set(re.findall(r"\(?\d{3}\)?[ .-]\d{3}[.-]\d{4}", text)))[:5],
        "colors": [c for c, _ in collections.Counter(x.lower() for x in re.findall(r"#[0-9a-fA-F]{6}\b", t)).most_common(10)],
        "faces": sorted({f.strip().strip("'\"") for f in re.findall(r"font-family:\s*([^;,}{]{3,40})", t)})[:10],
        "social": sorted(set(re.findall(r'https?://(?:www\.)?(?:instagram|facebook|linkedin|youtube|houzz)\.com/[A-Za-z0-9_./-]+', t)))[:10],
        "pictures": pics,
    }
    (d / "site.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (d / "site.html").write_text(t, encoding="utf-8")
    real = [p for p in pics if not p["note"]]
    print(f"{d.relative_to(ROOT).as_posix()}/site.json | {out['title'][:70]} | {out['words']} words | {len(heads)} headings | "
          f"{len(pics)} pictures ({len(pics) - len(real)} AI-named or logos) | faces {', '.join(out['faces'][:3])} | phone {', '.join(out['phones'][:1])}")
    for s in out["social"]:
        print("  ", s)


# ---------------------------------------------------------------- the Google Business Profile

def short_name(full):
    """A first name and a last initial (Jonathan, 2026-10-05: "do not include last names in the reviews that are shown")."""
    parts = (full or "").split()
    return parts[0] if len(parts) < 2 else f"{parts[0]} {parts[-1][0]}."


def cmd_google(a):
    key = get_secret("GOOGLE_MAPS_API_KEY", required=True, hint="Add it to %USERPROFILE%\\.monarc\\secrets.env.")
    mask = "places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.googleMapsUri,places.websiteUri,places.reviews"
    r = requests.post(f"{PLACES}/places:searchText", headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": mask},
                      json={"textQuery": a.query, "maxResultCount": 1}, timeout=40)
    places = r.json().get("places") or []
    if r.status_code != 200 or not places:
        sys.exit(f"Google found no profile for: {a.query} ({r.status_code} {str(r.json().get('error', {}).get('message', ''))[:160]})")
    p = places[0]
    name = p.get("displayName", {}).get("text", "")
    d = folder(a.name or name)
    reviews = [{"name": short_name(v.get("authorAttribution", {}).get("displayName")), "rating": v.get("rating"),
                "date": (v.get("publishTime") or "")[:10], "text": (v.get("originalText") or v.get("text") or {}).get("text", "")}
               for v in p.get("reviews") or []]
    out = {"read": date.today().isoformat(), "query": a.query, "place_id": p.get("id"), "name": name, "address": p.get("formattedAddress"),
           "website": p.get("websiteUri"), "maps": p.get("googleMapsUri"), "rating": p.get("rating"), "reviews_count": p.get("userRatingCount"),
           "reviews": reviews, "photos": []}
    if a.photos:
        det = requests.get(f"{PLACES}/places/{p['id']}", headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": "id,photos"}, timeout=40).json()
        (d / "photos").mkdir(exist_ok=True)
        for i, ph in enumerate(det.get("photos") or []):
            m = requests.get(f"{PLACES}/{ph['name']}/media", params={"maxWidthPx": 2000, "key": key}, timeout=90)
            if m.status_code != 200:
                continue
            f = d / "photos" / f"g{i:02d}.jpg"
            f.write_bytes(m.content)
            out["photos"].append({"file": f.relative_to(ROOT).as_posix(), "width": ph.get("widthPx"), "height": ph.get("heightPx"),
                                  "by": ", ".join(x.get("displayName", "") for x in ph.get("authorAttributions", []))})
        sheet(d / "photos", d / "photos-sheet.jpg")
    (d / "google.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{d.relative_to(ROOT).as_posix()}/google.json | {name} | {out['rating']} from {out['reviews_count']} reviews | "
          f"{len(reviews)} reviews read | {len(out['photos'])} photos")
    for v in reviews:
        print(f"   {v['rating']} | {v['name']} | {v['date']} | {v['text'][:110].replace(chr(10), ' ')}")


def sheet(photos_dir, out):
    """Every photo in a folder on one numbered sheet, so the clone can look once and pick."""
    import studio_common as sc
    files = sorted(photos_dir.glob("*.jpg"))
    if not files:
        return
    ins = [x for f in files for x in ("-i", str(f))]
    n = len(files)
    graph = "".join(f"[{i}:v]scale=360:270:force_original_aspect_ratio=decrease,pad=360:270:(ow-iw)/2:(oh-ih)/2:white,"
                    f"drawtext=text='{i}':x=8:y=6:fontsize=30:fontcolor=yellow:box=1:boxcolor=black@0.7[t{i}];" for i in range(n))
    graph += "".join(f"[t{i}]" for i in range(n)) + (f"xstack=inputs={n}:layout=" + "|".join(f"{(i % 4) * 360}_{(i // 4) * 270}" for i in range(n)) + ":fill=white[v]"
                                                      if n > 1 else "null[v]")
    subprocess.run([sc.ffmpeg_exe(), "-y", "-loglevel", "error", *ins, "-filter_complex", graph, "-map", "[v]", "-frames:v", "1", "-q:v", "4", str(out)],
                   capture_output=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("site")
    s.add_argument("url")
    s.add_argument("--name", default="")
    g = sub.add_parser("google")
    g.add_argument("query")
    g.add_argument("--name", default="")
    g.add_argument("--photos", action="store_true")
    a = ap.parse_args()
    {"site": cmd_site, "google": cmd_google}[a.cmd](a)


if __name__ == "__main__":
    main()
