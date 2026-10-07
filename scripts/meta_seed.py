"""meta_seed.py - build a Meta Ads customer-list seed from the integrator lists.

Takes the qualified seed workbook (Tier A and B by default, from qualify_sites.py) and the
qualified call list (the 887 from qualify_list.py), unions them by domain, then crawls each
company's homepage plus up to three contact / about / team pages for:
  emails (mailto links, page text, JSON-LD), an owner or founder name with the role it was
  found next to, phone numbers (tel links and JSON-LD), and Facebook / Instagram / LinkedIn links.

Writes:
  projects/outreach/meta-seed-<DATE>.xlsx            one row per company, everything found, with a quality grade
  projects/outreach/meta-customer-list-<DATE>.csv    Meta customer-list format, every company (email and/or phone)
  projects/outreach/meta-customer-list-<DATE>-strong.csv   only rows with an owner name and an email
  projects/outreach/contact-cache-<DATE>.jsonl       raw crawl results, so a rerun fetches only what is missing

Usage:
  python scripts/meta_seed.py                      (Tier A+B plus the call list)
  python scripts/meta_seed.py --tiers A,B,C
  python scripts/meta_seed.py --no-call-list
  python scripts/meta_seed.py --limit 20           (smoke test)

Meta column codes (Business Help Center, customer list formatting): email, phone, fn, ln, ct, st, zip, country.
Values are pre-normalized the way Meta hashes them: lowercase, no punctuation, phone as digits with the
country code, state as two letters, country as "us". Meta hashes on upload; nothing here is hashed.

No paid APIs. Network only to the companies' own sites. No third-party packages beyond requests, bs4, openpyxl.

bike-method-phase: 1 (run by hand, watch everything)
"""
import argparse
import csv
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse

import openpyxl
from bs4 import BeautifulSoup
from openpyxl.styles import Font

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import OUTREACH, fetch, newest, norm_domain  # noqa: E402

THREADS = 24
MAX_CONTACT_PAGES = 3
CONTACT_RE = re.compile(r"contact|about|team|our-story|story|staff|leadership|meet|who-we-are|founder|owner|"
                        r"management|people|company", re.I)
ROLE_WORDS = r"(?:co-?founder|founder|owner|co-?owner|president|ceo|principal|managing partner|managing director|proprietor)"
ROLE_RE = re.compile(ROLE_WORDS, re.I)
NAME = r"([A-Z][a-z]+(?:\s(?:[A-Z]\.?|[A-Z][a-z]+|[A-Z]'[A-Z][a-z]+|Mc[A-Z][a-z]+|O'[A-Z][a-z]+)){1,2})"
NAME_ROLE_RES = [
    re.compile(NAME + r"\s*[,|\-–—:/]\s*(?i:" + ROLE_WORDS + r")\b"),                   # Jane Doe, Owner
    re.compile(NAME + r"\s*\(\s*(?i:" + ROLE_WORDS + r")\s*\)"),                                  # Jane Doe (Owner)
    re.compile(r"\b(?i:" + ROLE_WORDS + r")\s*[,:|\-–—]?\s*" + NAME + r"\b"),            # Owner: Jane Doe
    # verbs match any case, the name itself must be capitalized: inline (?i:) keeps the flag off NAME
    # "owned by" is left out on purpose: on project pages it describes the house, not the company
    re.compile(r"\b(?i:founded|started|established|launched|opened)\s+(?i:by)\s+" + NAME + r"\b"),
    re.compile(r"\b" + NAME + r"\s+(?:is|as)\s+(?:the|our|its)?\s*(?i:" + ROLE_WORDS + r")\b"),   # Jane Doe is the owner
    re.compile(r"\b" + NAME + r",?\s+(?:who\s+)?(?i:founded|started|owns|opened)\s+"),
]
NAME_STOP = {"user", "super", "admin", "administrator", "webmaster", "editor", "author", "center", "centre",
             "development", "group", "company", "companies", "team", "staff", "studio", "studios", "designs",
             "entertainment", "integration", "integrations", "integrators", "concepts", "creations",
             "installations", "communications", "electronics", "environments", "living", "lifestyle", "cinema",
             "cinemas", "sales", "consulting", "consultants", "partners", "associates", "enterprises",
             "corporation", "holdings", "properties", "realty", "homes", "builders", "construction", "interiors",
             "reflections", "project", "projects", "overview", "gallery", "portfolio", "showcase", "client",
             "clients", "customer", "customers", "review", "reviews", "testimonial", "testimonials", "elvis",
             "presley", "beverly", "hollywood", "estates", "residence", "residences", "mansion", "manor",
             "llc", "inc", "corp", "co", "ltd", "was", "has", "is", "are", "were", "and", "of", "in", "at", "for",
             "with", "we", "he", "she", "they", "it", "who", "his", "her", "their", "this", "that", "from", "to",
             "home", "smart", "our", "the", "meet", "contact", "about", "custom", "whole", "audio", "video", "lighting",
             "control", "security", "media", "sound", "theater", "theatre", "design", "install", "installation",
             "read", "learn", "get", "free", "call", "email", "phone", "privacy", "terms", "google", "facebook",
             "instagram", "linkedin", "lutron", "control4", "crestron", "savant", "sonos", "josh", "kaleidescape",
             "ketra", "james", "sonance", "ubiquiti", "araknis", "snap", "one", "united", "north", "south", "east",
             "west", "new", "san", "los", "las", "santa", "saint", "st", "mount", "lake", "bay", "cedia", "htsa",
             "prosource", "best", "buy", "elite", "premier", "pro", "advanced", "modern", "digital", "integrated",
             "innovative", "luxury", "estate", "residential", "commercial", "service", "services", "system",
             "systems", "solutions", "technology", "technologies", "automation", "networks", "wire", "low",
             "voltage", "electric", "electrical", "since", "years", "family", "owned", "operated", "licensed",
             "insured", "certified", "dealer", "authorized", "showroom", "office", "hours", "monday", "friday",
             "saturday", "sunday", "copyright", "all", "rights", "reserved", "site", "map", "web", "website",
             "powered", "by", "built", "designed", "dolby", "atmos", "apple", "amazon", "alexa", "nest", "ring",
             "samsung", "sony", "lg", "bose", "denon", "marantz", "yamaha", "klipsch", "polk", "definitive",
             "screen", "innovations", "stewart", "filmscreen", "seura", "sunbrite", "hunter", "douglas", "somfy",
             "qmotion", "wifi", "wi", "fi", "cat", "fiber", "matter", "thread", "zigbee", "wave", "z", "hdmi",
             "us", "usa", "america", "american", "national", "regional", "local", "greater", "metro", "county",
             "city", "town", "village", "valley", "hill", "hills", "beach", "island", "coast", "harbor"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
EMAIL_BAD_DOMAINS = re.compile(r"(sentry|wix|wixpress|squarespace|godaddy|secureserver|shopify|hubspot|wordpress|"
                               r"example|domain\.com|email\.com|yourdomain|sitename|company\.com|schema\.org|"
                               r"w3\.org|googleapis|gstatic|cloudflare|jquery|bootstrap|fontawesome|adobe|"
                               r"duda|weebly|webflow|placeholder|test\.com|mail\.com$|@2x|\.png|\.jpg|\.gif|\.svg|"
                               r"\.webp|\.css|\.js)", re.I)
GENERIC_BOXES = {"info", "sales", "contact", "hello", "office", "support", "admin", "service", "services", "team",
                 "help", "inquiries", "inquiry", "mail", "email", "general", "customerservice", "billing", "orders",
                 "marketing", "press", "media", "careers", "jobs", "hr", "webmaster", "noreply", "no-reply",
                 "donotreply", "newsletter", "quotes", "quote", "estimates", "estimate", "scheduling", "schedule"}
PERSONAL_PROVIDERS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com", "me.com",
                      "live.com", "msn.com", "comcast.net", "att.net", "verizon.net", "sbcglobal.net", "cox.net",
                      "earthlink.net", "protonmail.com", "proton.me", "mac.com", "bellsouth.net", "charter.net"}
SOCIAL_RE = {
    "Facebook": re.compile(r"https?://(?:www\.|m\.|business\.)?facebook\.com/(?!sharer|share|plugins|dialog|login|"
                           r"tr\?|hashtag|groups/|events/|photo|watch|policies|privacy|help)([^\s\"'<>?#]+)", re.I),
    "Instagram": re.compile(r"https?://(?:www\.)?instagram\.com/(?!p/|explore|accounts|share|reel)([^\s\"'<>?#/]+)", re.I),
    "LinkedIn": re.compile(r"https?://(?:www\.)?linkedin\.com/(company|in)/([^\s\"'<>?#/]+)", re.I),
}
PHONE_RE = re.compile(r"(?:\+?1[\s.-]?)?\(?([2-9]\d{2})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})\b")

lock = threading.Lock()


# ---------------------------------------------------------------- inputs

def load_seed_workbook(path, tiers):
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb["Qualified"]
    rows = ws.iter_rows(values_only=True)
    hdr = [str(h) for h in next(rows)]
    ix = {h: i for i, h in enumerate(hdr)}
    out = []
    for r in rows:
        tier = str(r[ix["Tier"]] or "")
        if tier not in tiers:
            continue
        out.append({"Tier": tier, "Name": str(r[ix["Name"]] or ""), "Website": str(r[ix["Website"]] or ""),
                    "Domain": str(r[ix["Domain"]] or "") or norm_domain(r[ix["Website"]]),
                    "City": str(r[ix["City"]] or ""), "State": str(r[ix["State"]] or "").upper(),
                    "Zip": str(r[ix["Zip"]] or ""), "Phone": str(r[ix["Phone"]] or ""),
                    "Brands": str(r[ix["Brands"]] or ""), "Source": f"seed {tier}"})
    return out


def load_raw_sweep(path):
    """A places_seed workbook (first sheet), every row with a website, no tiers. For crawling a whole sweep, for
    instance to pick up LinkedIn company pages for the Campaign Manager upload (2026-09-24)."""
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    hdr = [str(h or "") for h in next(rows)]
    ix = {h: i for i, h in enumerate(hdr)}
    out = []
    for r in rows:
        site = str(r[ix["Website"]] or "") if "Website" in ix else ""
        dom = norm_domain(site)
        if not dom:
            continue
        out.append({"Tier": "raw", "Name": str(r[ix["Name"]] or ""), "Website": site, "Domain": dom,
                    "City": str(r[ix["City"]] or "") if "City" in ix else "", "State": str(r[ix["State"]] or "").upper(),
                    "Zip": str(r[ix["Zip"]] or "") if "Zip" in ix else "", "Phone": str(r[ix["Phone"]] or ""),
                    "Brands": "", "Source": f"sweep {Path(path).name}"})
    return out


def load_call_list(path):
    out = []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            site = r.get("Website") or ""
            out.append({"Tier": "call", "Name": r.get("Name", ""), "Website": site, "Domain": norm_domain(site),
                        "City": r.get("City", ""), "State": (r.get("State") or "").upper(), "Zip": r.get("Zip", ""),
                        "Phone": r.get("Phone", ""), "Brands": "", "Source": "call list 2026-09-11"})
    return out


def union_by_domain(*lists):
    seen, out = {}, []
    for lst in lists:
        for r in lst:
            d = r["Domain"]
            if not d:
                continue
            if d in seen:
                # keep the first, note the other source
                seen[d]["Source"] += " + " + r["Source"]
                continue
            seen[d] = r
            out.append(r)
    return out


# ---------------------------------------------------------------- crawl

def cache_path(run_date):
    return OUTREACH / f"contact-cache-{run_date}.jsonl"


def load_cache(path):
    recs = {}
    if not path.exists():
        return recs
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line.strip():
            try:
                row = json.loads(line)
                recs[row["domain"]] = row
            except ValueError:
                pass
    return recs


def clean_emails(found, domain):
    out = []
    for e in found:
        e = e.strip().strip(".,;:()<>[]\"'").lower()
        if "@" not in e or EMAIL_BAD_DOMAINS.search(e) or len(e) > 60:
            continue
        box, _, dom = e.partition("@")
        if not re.match(r"^[a-z0-9._%+-]+$", box) or "." not in dom:
            continue
        # keep only the company's own domain or a personal provider (gmail etc.). An address on some other
        # domain is a web agency, a scheduling tool, or a vendor: the wrong person for a Meta match.
        if dom == domain or dom.endswith("." + domain) or domain.endswith("." + dom) or dom in PERSONAL_PROVIDERS:
            out.append(e)
    # dedupe, keep order
    seen, res = set(), []
    for e in out:
        if e not in seen:
            seen.add(e)
            res.append(e)
    return res


def email_kind(e, domain):
    box, _, dom = e.partition("@")
    if dom in PERSONAL_PROVIDERS:
        return "personal provider"
    if box in GENERIC_BOXES or box.startswith(("info", "sales", "contact", "office", "support", "admin", "service")):
        return "generic"
    if dom == domain or dom.endswith("." + domain) or domain.endswith("." + dom):
        return "named on domain"
    return "named elsewhere"


def plausible_name(name, company):
    parts = name.replace(".", "").split()
    if len(parts) < 2 or len(parts) > 3:
        return False
    low = [p.lower().strip("'") for p in parts]
    if any(p in NAME_STOP for p in low):
        return False
    # every token capitalized then lowercase (allowing Mc/O' forms and initials); rejects LLC, WAS, all-caps nav
    for p in parts:
        core = re.sub(r"^(Mc|O')", "", p)
        if not re.fullmatch(r"[A-Z](?:[a-z]+|'[A-Z][a-z]+)?", core):
            return False
    comp = set(re.findall(r"[a-z]+", company.lower()))
    if all(p in comp for p in low):
        return False
    if any(len(p) < 2 for p in low):
        return False
    return True


def names_from_text(text, company):
    """Return [(name, role, evidence)]. Scans line by line so headings and captions stay separate."""
    hits = []
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    for i, ln in enumerate(lines):
        if len(ln) > 400:
            ln = ln[:400]
        for rx in NAME_ROLE_RES:
            for m in rx.finditer(ln):
                name = next((g for g in m.groups() if g and g[0].isupper() and " " in g), None)
                if name and plausible_name(name, company):
                    role = ROLE_RE.search(m.group(0))
                    hits.append((name.strip(), (role.group(0) if role else "founder").lower(), ln[:160]))
        # heading name on one line, role on the next: "Jane Doe" / "Owner"
        if i + 1 < len(lines) and re.fullmatch(NAME, ln) and re.fullmatch(r"\s*" + ROLE_WORDS + r"[\w\s&/,]*", lines[i + 1], re.I):
            if plausible_name(ln, company):
                hits.append((ln, ROLE_RE.search(lines[i + 1]).group(0).lower(), ln + " / " + lines[i + 1][:60]))
    return hits


def jsonld_contacts(soup):
    emails, phones, people = [], [], []
    for tag in soup.find_all("script", attrs={"type": re.compile("ld\\+json", re.I)}):
        try:
            data = json.loads(tag.string or "")
        except Exception:  # noqa: BLE001
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                t = str(node.get("@type", "")).lower()
                if "email" in node and isinstance(node["email"], str):
                    emails.append(node["email"].replace("mailto:", ""))
                if "telephone" in node and isinstance(node["telephone"], str):
                    phones.append(node["telephone"])
                for key in ("founder", "founders", "employee", "employees", "member", "author"):
                    v = node.get(key)
                    if isinstance(v, dict) and v.get("name"):
                        people.append((str(v["name"]), key))
                    elif isinstance(v, str) and key in ("founder", "founders"):
                        people.append((v, key))
                    elif isinstance(v, list):
                        for p in v:
                            if isinstance(p, dict) and p.get("name"):
                                people.append((str(p["name"]), key))
                if t == "person" and node.get("name"):
                    people.append((str(node["name"]), str(node.get("jobTitle", "person"))))
                stack.extend(v for v in node.values() if isinstance(v, (dict, list)))
    return emails, phones, people


def parse_page(html, url, domain, company):
    soup = BeautifulSoup(html, "html.parser")
    jl_emails, jl_phones, jl_people = jsonld_contacts(soup)
    raw_emails = [a["href"].split("mailto:", 1)[1].split("?")[0] for a in soup.find_all("a", href=True)
                  if a["href"].lower().startswith("mailto:")]
    raw_phones = [a["href"].split(":", 1)[1] for a in soup.find_all("a", href=True) if a["href"].lower().startswith("tel:")]
    links = [urljoin(url, a["href"].strip()) for a in soup.find_all("a", href=True)]
    social = {}
    for label, rx in SOCIAL_RE.items():
        for href in links:
            m = rx.search(href)
            if m:
                social.setdefault(label, href.split("?")[0].rstrip("/"))
                break
    host = urlparse(url).netloc.lower().replace("www.", "")
    candidates = []
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"].strip())
        p = urlparse(href)
        if p.scheme not in ("http", "https") or p.netloc.lower().replace("www.", "") != host:
            continue
        key = (p.path or "/").rstrip("/").lower()
        label = a.get_text(" ", strip=True)[:60]
        if CONTACT_RE.search(key) or CONTACT_RE.search(label):
            candidates.append(href.split("#")[0])
    for t in soup(["script", "style", "noscript", "svg", "template"]):
        t.decompose()
    text = soup.get_text("\n")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    raw_emails += EMAIL_RE.findall(html)
    emails = clean_emails(raw_emails + jl_emails, domain)
    phones = []
    for ph in raw_phones + jl_phones + [m.group(0) for m in PHONE_RE.finditer(text[:20000])]:
        m = PHONE_RE.search(ph)
        if m:
            digits = "1" + "".join(m.groups())
            if digits not in phones:
                phones.append(digits)
    names = names_from_text(text, company)
    for nm, role in jl_people:
        if plausible_name(nm, company):
            names.append((nm, f"json-ld {role}".lower(), "structured data"))
    # dedupe candidate pages, keep order
    seen, cands = set(), []
    for c in candidates:
        if c not in seen and urlparse(c).path.rstrip("/") != urlparse(url).path.rstrip("/"):
            seen.add(c)
            cands.append(c)
    return {"emails": emails, "phones": phones[:4], "names": names, "social": social, "candidates": cands[:12]}


def crawl(company):
    domain = company["Domain"]
    rec = {"domain": domain, "fetched": time.strftime("%Y-%m-%d %H:%M"), "pages": []}
    r, err = fetch(company["Website"] or domain)
    if r is None:
        rec.update({"ok": False, "error": err})
        return rec
    try:
        home = parse_page(r.text, r.url, domain, company["Name"])
        rec.update({"ok": True, "final_url": r.url})
        rec["pages"].append({"url": r.url, "kind": "home", **{k: home[k] for k in ("emails", "phones", "names", "social")}})
        # rank candidate pages: contact and about first, then team and story
        def rank(u):
            p = u.lower()
            return (0 if "contact" in p else 1 if "about" in p else 2 if re.search(r"team|staff|people|leadership|management", p) else 3)
        fetched = 0
        for url in sorted(home["candidates"], key=rank):
            if fetched >= MAX_CONTACT_PAGES:
                break
            sr, _ = fetch(url, timeout=(5, 12))
            if sr is None or not sr.text:
                continue
            fetched += 1
            page = parse_page(sr.text, sr.url, domain, company["Name"])
            rec["pages"].append({"url": sr.url, "kind": "contact", **{k: page[k] for k in ("emails", "phones", "names", "social")}})
    except Exception as e:  # noqa: BLE001
        rec.update({"ok": False, "error": "parse:" + type(e).__name__})
    return rec


def crawl_all(companies, run_date, limit=0, reuse=(), shard=None):
    """shard: (i, n) crawls only the domains whose hash lands in slice i of n and writes its own cache file, so
    n copies of this script can run side by side on one list (2026-09-24, Jonathan: "increase the speed")."""
    path = cache_path(run_date if shard is None else f"{run_date}-shard{shard[0]}of{shard[1]}")
    cache = load_cache(path)
    for old in reuse:  # an earlier date's cache: those domains are not fetched again
        for d, rec in load_cache(Path(old)).items():
            cache.setdefault(d, rec)
    if shard is not None:
        import zlib
        companies = [c for c in companies if zlib.crc32(c["Domain"].encode()) % shard[1] == shard[0]]
    todo = [c for c in companies if c["Domain"] not in cache]
    if limit:
        todo = todo[:limit]
    print(f"{len(companies)} companies, {len(cache)} cached, {len(todo)} to crawl", flush=True)
    n = 0
    with ThreadPoolExecutor(max_workers=THREADS) as ex, path.open("a", encoding="utf-8") as fh:
        futs = {ex.submit(crawl, c): c["Domain"] for c in todo}
        for fut in as_completed(futs):
            rec = fut.result()
            with lock:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fh.flush()
            cache[rec["domain"]] = rec
            n += 1
            if n % 100 == 0:
                print(f"  crawled {n}/{len(todo)}", flush=True)
    return cache


# ---------------------------------------------------------------- assemble

ROLE_RANK = {"owner": 0, "co-owner": 0, "founder": 1, "co-founder": 1, "president": 2, "ceo": 3, "principal": 4,
             "managing partner": 5, "managing director": 5, "proprietor": 0}


def pick_owner(rec):
    """Best (name, role, evidence, page) across pages: owner beats founder beats president; contact/about pages first."""
    best = None
    company = rec.get("company", "")
    for page in rec.get("pages", []):
        for name, role, ev in page.get("names", []):
            # re-validate cached hits against the current rules, so a rule fix does not need a re-crawl
            if not plausible_name(name, company):
                continue
            if role.startswith("json-ld") and re.search(r"author|member|employee", role):
                continue                      # CMS users and staff lists are not the owner
            if re.search(r"(?i)\b(formerly|previously|once|originally)\s+owned\b|\bowned by\b", ev) and "found" not in ev.lower():
                continue                      # a house's owner on a project page
            if re.search(r"(?i)\b(said|says|wrote|review|testimonial|thank you|thanks to|worked with)\b", ev):
                continue                      # a customer quote
            base = re.sub(r"^(json-ld|co-?)\s*", "", role).strip()
            score = ROLE_RANK.get(base, 6) + (0 if page["kind"] == "contact" else 0.5)
            if best is None or score < best[0]:
                best = (score, name, role, ev, page["url"])
    return best[1:] if best else ("", "", "", "")


def pick_emails(rec, domain):
    order = {"named on domain": 0, "personal provider": 1, "named elsewhere": 2, "generic": 3}
    pool = []
    for page in rec.get("pages", []):
        for e in page.get("emails", []):
            if e not in [p[0] for p in pool]:
                pool.append((e, email_kind(e, domain)))
    pool.sort(key=lambda x: order.get(x[1], 9))
    return pool


def norm_meta(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def split_name(full):
    parts = full.replace(".", "").split()
    if not parts:
        return "", ""
    return parts[0], parts[-1]


def phone_digits(s):
    m = PHONE_RE.search(s or "")
    return "1" + "".join(m.groups()) if m else ""


def build_rows(companies, cache):
    rows = []
    for c in companies:
        rec = cache.get(c["Domain"]) or {}
        rec["company"] = c["Name"]
        owner, role, evidence, page = pick_owner(rec) if rec.get("ok") else ("", "", "", "")
        emails = pick_emails(rec, c["Domain"]) if rec.get("ok") else []
        social = {}
        phones = []
        for p in rec.get("pages", []):
            for k, v in p.get("social", {}).items():
                social.setdefault(k, v)
            for ph in p.get("phones", []):
                if ph not in phones:
                    phones.append(ph)
        listing_phone = phone_digits(c["Phone"])
        e1 = emails[0][0] if emails else ""
        e2 = emails[1][0] if len(emails) > 1 else ""
        if owner and e1:
            grade = "A owner + email"
        elif e1 and emails[0][1] != "generic":
            grade = "B named email"
        elif e1:
            grade = "C generic email"
        elif listing_phone:
            grade = "D phone only"
        else:
            grade = "E nothing"
        fn, ln = split_name(owner)
        rows.append({
            "Grade": grade, "Tier": c["Tier"], "Name": c["Name"], "Domain": c["Domain"], "City": c["City"],
            "State": c["State"], "Zip": c["Zip"], "Listing phone": c["Phone"],
            "Owner name": owner, "First name": fn, "Last name": ln, "Owner role": role, "Owner evidence": evidence,
            "Owner page": page, "Email 1": e1, "Email 1 kind": emails[0][1] if emails else "",
            "Email 2": e2, "All emails": ", ".join(e for e, _ in emails[:6]),
            "Site phones": ", ".join(phones[:3]), "Facebook": social.get("Facebook", ""),
            "Instagram": social.get("Instagram", ""), "LinkedIn": social.get("LinkedIn", ""),
            "Pages read": len(rec.get("pages", [])), "Crawl": "ok" if rec.get("ok") else (rec.get("error") or "not crawled"),
            "Brands": c.get("Brands", ""), "Source": c["Source"],
        })
    return rows


META_HEADER = ["email", "email", "phone", "phone", "fn", "ln", "ct", "st", "zip", "country"]


def meta_row(r):
    phones = []
    lp = phone_digits(r["Listing phone"])
    if lp:
        phones.append(lp)
    for ph in (r["Site phones"] or "").split(", "):
        if ph and ph not in phones:
            phones.append(ph)
    return [r["Email 1"], r["Email 2"], phones[0] if phones else "", phones[1] if len(phones) > 1 else "",
            norm_meta(r["First name"]), norm_meta(r["Last name"]), norm_meta(r["City"]),
            (r["State"] or "").lower()[:2], re.sub(r"\D", "", r["Zip"] or "")[:5], "us"]


def write_outputs(rows, run_date, inputs):
    out = OUTREACH / f"meta-seed-{run_date}.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Seed"
    hdr = list(rows[0].keys())
    ws.append(hdr)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for r in sorted(rows, key=lambda x: (x["Grade"], x["State"], x["Name"])):
        ws.append([r[h] for h in hdr])
    ws.freeze_panes = "A2"
    m = wb.create_sheet("Method")
    counts = {}
    for r in rows:
        counts[r["Grade"]] = counts.get(r["Grade"], 0) + 1
    for line in [
        f"Built {run_date} by scripts/meta_seed.py. Inputs: {inputs}.",
        "One row per website domain. Crawl: homepage plus up to three same-domain contact, about, team, or story pages.",
        "Emails: mailto links, page text, JSON-LD. Ranked: named mailbox on the company domain, personal provider "
        "(gmail etc.), named elsewhere, generic (info@, sales@).",
        "Owner: a name found next to owner, founder, president, CEO, principal, or partner on any read page, or a "
        "founder/employee in JSON-LD. Owner beats founder beats president; contact and about pages beat the homepage. "
        "Evidence column shows the line it came from. Check before trusting: this is pattern matching, not a lookup.",
        "Grades: A owner + email, B named email, C generic email only, D phone only, E nothing found.",
        "Grade counts: " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())),
        "Meta CSVs: column codes per Meta's customer list formatting guide. Values pre-normalized (lowercase, "
        "no punctuation, phone digits with country code, state two letters, country us). Meta hashes on upload.",
        "No paid data source was used. Gaps (grades C, D, E) are the enrichment worklist for a paid provider.",
    ]:
        m.append([line])
    wb.save(out)
    full = OUTREACH / f"meta-customer-list-{run_date}.csv"
    strong = OUTREACH / f"meta-customer-list-{run_date}-strong.csv"
    n_full = n_strong = 0
    with full.open("w", newline="", encoding="utf-8") as f1, strong.open("w", newline="", encoding="utf-8") as f2:
        w1, w2 = csv.writer(f1), csv.writer(f2)
        w1.writerow(META_HEADER)
        w2.writerow(META_HEADER)
        for r in rows:
            mr = meta_row(r)
            if mr[0] or mr[2]:
                w1.writerow(mr)
                n_full += 1
            if r["Grade"].startswith("A"):
                w2.writerow(mr)
                n_strong += 1
    return out, full, strong, n_full, n_strong, counts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tiers", default="A,B", help="seed tiers to include, e.g. A,B,C")
    ap.add_argument("--no-call-list", action="store_true", help="skip the 887 qualified call list")
    ap.add_argument("--limit", type=int, default=0, help="crawl at most N uncached domains (smoke test)")
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--seed", default="", help="qualified-seed-*.xlsx path (default newest)")
    ap.add_argument("--raw", default="", help="a places-seed-*.xlsx: crawl every row with a website, no tiers (implies --no-call-list)")
    ap.add_argument("--reuse-cache", action="append", default=[], help="an earlier contact-cache-*.jsonl whose domains are not fetched again; repeatable")
    ap.add_argument("--shard", default="", help="i/n: crawl slice i of n into its own cache file, no outputs (run n copies, then a plain run with --reuse-cache on the shard files)")
    args = ap.parse_args(argv)
    shard = None
    if args.shard:
        i, n = args.shard.split("/")
        shard = (int(i), int(n))

    if args.raw:
        seed = load_raw_sweep(Path(args.raw))
        inputs = f"{Path(args.raw).name} every row with a website ({len(seed)})"
        args.no_call_list = True
    else:
        seed_path = Path(args.seed) if args.seed else newest("qualified-seed-*.xlsx")
        if not seed_path:
            sys.exit("No qualified-seed-*.xlsx in projects/outreach. Run qualify_sites.py first.")
        tiers = {t.strip().upper() for t in args.tiers.split(",") if t.strip()}
        seed = load_seed_workbook(seed_path, tiers)
        inputs = f"{seed_path.name} tiers {','.join(sorted(tiers))} ({len(seed)})"
    lists = [seed]
    if not args.no_call_list:
        call_path = newest("qualified-list-*.csv")
        if call_path:
            call = load_call_list(call_path)
            lists.append(call)
            inputs += f", {call_path.name} ({len(call)})"
    companies = union_by_domain(*lists)
    print(f"Inputs: {inputs}. {len(companies)} unique domains.", flush=True)
    t0 = time.time()
    cache = crawl_all(companies, args.date, args.limit, args.reuse_cache, shard)
    print(f"Crawl done in {int(time.time() - t0)}s", flush=True)
    if shard is not None:
        print(f"Shard {shard[0]} of {shard[1]} done; merge with a plain run that passes every shard file to --reuse-cache.", flush=True)
        return
    if args.limit:
        companies = [c for c in companies if c["Domain"] in cache]
    rows = build_rows(companies, cache)
    out, full, strong, n_full, n_strong, counts = write_outputs(rows, args.date, inputs)
    print(f"Wrote {out.name}: {len(rows)} companies")
    print("Grades: " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    print(f"Wrote {full.name}: {n_full} rows (email and/or phone)")
    print(f"Wrote {strong.name}: {n_strong} rows (owner name + email)")


if __name__ == "__main__":
    main()
