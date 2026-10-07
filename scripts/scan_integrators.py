"""Scan the integrator workbook, fetch each company's homepage once, flag One Firefly sites and
commercial-leaning companies, and write a seed list plus a LinkedIn company-list CSV.

Resumable: results are appended to projects/outreach/scan-cache-<DATE>.jsonl; rerun to continue.
Change DATE to rescan fresh on a new day.
Usage: python scan_integrators.py [--build-only]
"""
import sys, re, json, csv, time, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests, openpyxl
from bs4 import BeautifulSoup
from openpyxl.styles import Font

ROOT = Path(r"C:\Users\sumre\Documents\GitHub\AIS-OS")
SRC = ROOT / "projects" / "outreach" / "Integrator_List_2026-09-05.xlsx"
DATE = "2026-09-09"
CACHE = ROOT / "projects" / "outreach" / f"scan-cache-{DATE}.jsonl"
OUT_XLSX = ROOT / "projects" / "outreach" / f"seed-list-{DATE}.xlsx"
OUT_CSV = ROOT / "projects" / "outreach" / f"linkedin-company-list-{DATE}.csv"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")

COMM_STRONG = [r"commercial", r"conference rooms?", r"board ?rooms?", r"digital signage", r"corporate",
               r"hospitality", r"houses? of worship", r"worship", r"churche?s?", r"education", r"schools?",
               r"classrooms?", r"universit(?:y|ies)", r"healthcare", r"hospitals?", r"retail", r"government",
               r"huddle", r"video ?conferencing", r"pro[- ]av", r"enterprise", r"workplace", r"meeting rooms?",
               r"auditoriums?", r"stadiums?", r"arenas?", r"hotels?", r"casinos?", r"restaurants?",
               r"sports bars?", r"mass notification", r"paging", r"data centers?", r"industrial", r"campus",
               r"municipal", r"k-?12", r"bars? (?:and|&) restaurants?"]
RES_STRONG = [r"residential", r"home ?owners?", r"home theat(?:er|re)s?", r"home cinemas?", r"smart homes?",
              r"whole[- ]home", r"media rooms?", r"custom homes?", r"luxury", r"living rooms?", r"bedrooms?",
              r"kitchens?", r"backyards?", r"outdoor living", r"estates?", r"your home", r"condos?",
              r"penthouses?", r"interior designers?", r"architects?", r"builders?", r"motorized shades?",
              r"family", r"families", r"lifestyle", r"pool", r"patio", r"home offices?", r"new construction",
              r"remodels?", r"renovations?"]
RES_WEAK = [r"homes?", r"house"]
COMM_RE = [re.compile(r"\b" + p + r"\b") for p in COMM_STRONG]
RES_RE = [re.compile(r"\b" + p + r"\b") for p in RES_STRONG]
RESW_RE = [re.compile(r"\b" + p + r"\b") for p in RES_WEAK]
OFFICE_RE = re.compile(r"\boffices?\b")
HOME_OFFICE_RE = re.compile(r"\bhome offices?\b")
ONEFIREFLY_RE = re.compile(r"one\s*firefly")

lock = threading.Lock()


def norm_domain(url):
    if not url:
        return ""
    u = str(url).strip()
    if not re.match(r"^https?://", u, re.I):
        u = "http://" + u
    host = urlparse(u).netloc.lower()
    host = host.split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return host


def fetch(url):
    u = str(url).strip()
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u
    alts = [u, ("http://" + u[8:]) if u.lower().startswith("https://") else ("https://" + u[7:])]
    last_err = None
    for a in alts:
        try:
            r = requests.get(a, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.8"},
                             timeout=(6, 15), allow_redirects=True)
            if r.status_code < 400 and r.text:
                return r, None
            last_err = f"HTTP {r.status_code}"
        except Exception as e:  # noqa: BLE001
            last_err = type(e).__name__
    return None, last_err


def count(patterns, text):
    return sum(len(p.findall(text)) for p in patterns)


def analyze(html, final_url):
    low = html.lower()
    onefirefly = bool(ONEFIREFLY_RE.search(low))
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "svg", "template"]):
        t.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    meta = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    desc = (meta.get("content") or "") if meta else ""
    text = re.sub(r"\s+", " ", soup.get_text(" ")).lower()
    comm = count(COMM_RE, text)
    office = len(OFFICE_RE.findall(text)) - len(HOME_OFFICE_RE.findall(text))
    comm += 0.5 * max(office, 0)
    res = count(RES_RE, text) + 0.25 * count(RESW_RE, text)
    total = comm + res
    share = (comm / total) if total else 0.0
    head = (title + " " + desc).lower()
    head_comm = bool(re.search(r"\bcommercial\b", head)) and not re.search(
        r"\b(home|homes|residential|homeowners?|smart home|home theater)\b", head)
    return {
        "onefirefly": onefirefly, "title": title[:200], "desc": desc[:300], "text_len": len(text),
        "comm": round(comm, 2), "res": round(res, 2), "comm_share": round(share, 3),
        "head_comm": head_comm, "final_url": final_url,
    }


def scan_one(domain, url):
    r, err = fetch(url)
    rec = {"domain": domain, "url": url, "scanned": time.strftime("%Y-%m-%d %H:%M")}
    if r is None:
        rec.update({"ok": False, "error": err})
        return rec
    try:
        rec.update({"ok": True, **analyze(r.text, r.url)})
    except Exception as e:  # noqa: BLE001
        rec.update({"ok": False, "error": "parse:" + type(e).__name__})
    return rec


def classify(rec):
    """Return (decision, reason). decision in {keep, exclude}."""
    if not rec.get("ok"):
        return "keep", f"unverified: {rec.get('error')}"
    if rec["onefirefly"]:
        return "exclude", "One Firefly site"
    if rec["text_len"] < 300:
        return "keep", "unverified: thin page (JS-rendered)"
    if rec["head_comm"]:
        return "exclude", "commercial in title/description, no residential"
    head = (rec.get("title", "") + " " + rec.get("desc", "")).lower()
    head_res = bool(HEAD_RES_RE.search(head))
    cut = 0.6 if head_res else 0.5  # a site that calls itself residential needs a clearer commercial tilt
    if rec["comm"] >= 3 and rec["comm_share"] >= cut:
        return "exclude", f"commercial leaning (share {rec['comm_share']:.2f})"
    if rec["comm"] >= 3 and rec["comm_share"] >= 0.35:
        return "keep", f"mixed ({rec['comm_share']:.2f}), review"
    return "keep", ""


HEAD_RES_RE = re.compile(r"\b(home theat(?:er|re)s?|smart homes?|home automation|residential|home ?owners?|"
                         r"whole[- ]home|custom homes?|home technology|home cinema)\b")
INTEGRATOR_RE = re.compile(r"(theat|smart home|automat|audio|video|integrat|control4|crestron|savant|lutron|"
                           r"sonos|josh\.ai|low voltage|lighting|shades?|cinema|hi-?fi|sound|\bav\b|a/v)")


def integrator_signal(listing_name, rec):
    text = " ".join([str(listing_name or ""), (rec or {}).get("title", ""), (rec or {}).get("desc", "")]).lower()
    return len(INTEGRATOR_RE.findall(text))


def parse_addr(addr):
    parts = [p.strip() for p in (addr or "").split(",") if p.strip()]
    city = state = zipc = ""
    if parts and parts[-1].upper() in ("USA", "US", "UNITED STATES"):
        parts = parts[:-1]
    if parts:
        m = re.match(r"^([A-Z]{2})\s+(\d{5})", parts[-1])
        if m:
            state, zipc = m.group(1), m.group(2)
            if len(parts) >= 2:
                city = parts[-2]
    return city, state, zipc


def clean_name(name):
    n = str(name or "").strip()
    for sep in (" - ", " | ", " – ", " — ", ": "):
        if sep in n and len(n.split(sep)[0]) >= 3:
            n = n.split(sep)[0].strip()
    return n


def load_rows():
    wb = openpyxl.load_workbook(SRC, read_only=True)
    ws = wb["Integrators"]
    rows = []
    header = None
    for row in ws.iter_rows(values_only=True):
        if header is None:
            header = [h for h in row]
            continue
        d = dict(zip(header, row))
        if not d.get("Name"):
            continue
        rows.append(d)
    return rows


def load_cache():
    done = {}
    if CACHE.exists():
        for line in CACHE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done[rec["domain"]] = rec
    return done


def scan(rows):
    done = load_cache()
    targets = {}
    for d in rows:
        dom = norm_domain(d.get("Website"))
        if dom and dom not in done and dom not in targets:
            targets[dom] = str(d["Website"]).strip()
    print(f"{len(rows)} rows, {len(done)} domains cached, {len(targets)} to scan", flush=True)
    n = 0
    with ThreadPoolExecutor(max_workers=24) as ex, CACHE.open("a", encoding="utf-8") as fh:
        futs = {ex.submit(scan_one, dom, url): dom for dom, url in targets.items()}
        for fut in as_completed(futs):
            rec = fut.result()
            with lock:
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
            done[rec["domain"]] = rec
            n += 1
            if n % 50 == 0:
                print(f"  scanned {n}/{len(targets)}", flush=True)
    return done


def build(rows, done):
    # one row per domain (or per name when no website); keep the listing with most reviews
    def reviews_n(s):
        m = re.search(r"\((\d+)\)", str(s or ""))
        return int(m.group(1)) if m else 0

    best = {}
    for d in rows:
        dom = norm_domain(d.get("Website"))
        key = dom or ("name:" + clean_name(d["Name"]).lower())
        if key not in best or reviews_n(d.get("Reviews")) > reviews_n(best[key].get("Reviews")):
            best[key] = d

    seed, excluded, scores = [], [], []
    for key, d in best.items():
        dom = norm_domain(d.get("Website"))
        rec = done.get(dom) if dom else None
        if dom:
            decision, reason = classify(rec) if rec else ("keep", "unverified: not scanned")
        else:
            decision, reason = "keep", "no website"
        city, state, zipc = parse_addr(d.get("Address"))
        sig = integrator_signal(d["Name"], rec)
        if decision == "keep" and sig == 0:
            reason = (reason + "; " if reason else "") + "no integrator words in name/title, check"
        base = {
            "Integrator signal": sig,
            "Name": clean_name(d["Name"]), "Listing name": d["Name"], "Website": d.get("Website") or "",
            "Domain": dom, "City": city, "State": d.get("State") or state, "Zip": zipc,
            "County": d.get("County") or "", "Phone": d.get("Phone") or "", "Reviews": d.get("Reviews") or "",
            "Status": d.get("Status") or "", "Outcome": d.get("Outcome") or "",
            "Check": reason, "Commercial score": (rec or {}).get("comm", ""),
            "Residential score": (rec or {}).get("res", ""), "Commercial share": (rec or {}).get("comm_share", ""),
            "Site title": (rec or {}).get("title", ""),
        }
        scores.append({**base, "Decision": decision})
        (seed if decision == "keep" else excluded).append(base)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Seed"
    seed_cols = ["Name", "Website", "Domain", "City", "State", "Zip", "County", "Phone", "Reviews", "Check",
                 "Integrator signal", "Commercial share", "Site title", "Status", "Outcome"]
    ws.append(seed_cols)
    for r in seed:
        ws.append([r[c] for c in seed_cols])
    ws2 = wb.create_sheet("Excluded")
    ex_cols = ["Name", "Website", "Domain", "City", "State", "Check", "Commercial score", "Residential score",
               "Commercial share", "Site title"]
    ws2.append(ex_cols)
    for r in excluded:
        ws2.append([r[c] for c in ex_cols])
    ws3 = wb.create_sheet("All scored")
    all_cols = ["Decision"] + [c for c in scores[0].keys() if c != "Decision"]
    ws3.append(all_cols)
    for r in scores:
        ws3.append([r[c] for c in all_cols])
    ws4 = wb.create_sheet("Method")
    for line in [
        f"Built {DATE} from Integrator_List_2026-09-05.xlsx (Integrators sheet).",
        "One row per website domain; duplicate listings collapsed to the one with the most reviews.",
        "Each homepage fetched once. Exclude if the HTML mentions One Firefly.",
        "Exclude if the title or meta description says commercial with no residential word,",
        "or if commercial keyword hits >= 3 and commercial share of all hits >= 0.50",
        "(>= 0.60 when the site's own title or description says home theater, smart home, residential, etc).",
        "Integrator signal = count of integrator words (theater, automation, audio, video, Control4, Crestron,",
        "Savant, Lutron, low voltage, lighting, shades...) in the listing name, title, and description.",
        "A 0 means the source list picked up something that is probably not an integrator (IT shop, gate repair,",
        "alarm company). Kept, flagged 'check'. Filter the Seed sheet on that column before uploading if you want.",
        "Keep with 'mixed, review' when share is 0.35 to 0.50. Keep with 'unverified' when the site",
        "could not be fetched or is JS-rendered; those are not checked and may need a manual look.",
        "Commercial keywords: commercial, conference room, boardroom, digital signage, corporate, hospitality,",
        "house of worship, education, healthcare, retail, government, video conferencing, pro AV, enterprise, etc.",
        "Residential keywords: residential, homeowner, home theater, smart home, whole home, media room,",
        "custom home, luxury, interior designer, architect, builder, motorized shades, etc.",
        "LinkedIn upload file: linkedin-company-list-" + DATE + ".csv (Company list template, min 300 matches).",
    ]:
        ws4.append([line])
    for w in (ws, ws2, ws3):
        for c in w[1]:
            c.font = Font(bold=True)
        w.freeze_panes = "A2"
    wb.save(OUT_XLSX)

    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        # LinkedIn Account Match Template header, verified 2026-09-13 (was stockticker/country, which LinkedIn rejects)
        w.writerow(["companyname", "companywebsite", "companyemaildomain", "linkedincompanypageurl",
                    "stocksymbol", "industry", "city", "state", "companycountry", "zipcode"])
        for r in seed:
            w.writerow([r["Name"], r["Website"], r["Domain"], "", "", "", r["City"], r["State"], "US", r["Zip"]])

    reasons = {}
    for r in excluded:
        k = r["Check"].split(" (")[0]
        reasons[k] = reasons.get(k, 0) + 1
    unverified = sum(1 for r in seed if r["Check"].startswith("unverified"))
    mixed = sum(1 for r in seed if r["Check"].startswith("mixed"))
    nosite = sum(1 for r in seed if r["Check"].startswith("no website"))
    nosig = sum(1 for r in seed if r["Integrator signal"] == 0)
    clean = sum(1 for r in seed if r["Check"] == "")
    by_state = {}
    for r in seed:
        by_state[r["State"]] = by_state.get(r["State"], 0) + 1
    print(json.dumps({
        "source_rows": len(rows), "unique_companies": len(best), "seed": len(seed), "excluded": len(excluded),
        "excluded_by_reason": reasons, "seed_clean": clean, "seed_unverified": unverified,
        "seed_mixed_review": mixed, "seed_no_website": nosite, "seed_no_integrator_words": nosig,
        "seed_by_state": dict(sorted(by_state.items(), key=lambda kv: -kv[1])[:8]),
        "xlsx": str(OUT_XLSX), "csv": str(OUT_CSV),
    }, indent=2))


if __name__ == "__main__":
    rows = load_rows()
    if "--build-only" in sys.argv:
        done = load_cache()
    else:
        done = scan(rows)
    build(rows, done)
