"""Free campaign for a review (2026-10-03): the audit of a prospect's area and a free Google Ads campaign, built from
the domain, phone, and city on the call list, for near zero cost and none of Jonathan's time. He offers it on the
second call window, says he will ask for a Google review after, then sells the retainer. The review is asked after
delivery and never as the price of the free thing (Google's policy). Plan: C:\\Users\\sumre\\.claude\\plans, interview
brainstorms/2026-10-03-free-campaign-for-reviews.md, folder projects/free-campaign/README.md.

Usage:
  python scripts/free_campaign.py build --mb MB-00258 [--dry-run] [--max-cost 0.50] [--from-cache] [--no-serp]
  python scripts/free_campaign.py build --domain x.com --name "X" --city Naples --state FL --trade integrator ...
  python scripts/free_campaign.py queue [--dry-run]       every yes in the second-window call log with no folder yet
  python scripts/free_campaign.py deliver --mb MB-00258 [--to owner@x.com] [--dry-run]
  python scripts/free_campaign.py readback                Sent folder -> Delivered, Ask sent
  python scripts/free_campaign.py asks [--force-gate] [--dry-run]
  python scripts/free_campaign.py status
  python scripts/free_campaign.py check --mb MB-00258     every number in the audit is in the data
  python scripts/free_campaign.py setup                   the "Free campaign calls" table in the Prospects base

One delivery (projects/free-campaign/<MB-ID>-<domain>/): data.json, serp.json, places.json, campaign.json,
ads-editor.csv, audit.html, audit.pdf, delivery.draft.txt, review-ask.draft.txt. Every raw reply is kept in the
folder, so a rerun pays nothing. Cost per company about $0.10: three DataForSEO pages ($0.002 each), one volume call
($0.09), one or two Places queries ($0.035 each unless cached), an Opus site read ($0.02) only when not cached.
Keys (secrets.env): DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD, GOOGLE_MAPS_API_KEY, ANTHROPIC_API_KEY, AIRTABLE_API_KEY
(the Prospects base), AIRTABLE_PAT (Monarc CRM). The AIOS never sends email: drafts land in Proton Drafts.
"""
import argparse
import csv
import html as html_mod
import json
import os
import re
import statistics
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from string import Template
from urllib.parse import urlparse

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import (  # noqa: E402
    OUTREACH, ROOT, STATE_NAMES, BudgetExceeded, CostMeter, fetch, get_secret, norm_domain, report_key_sources,
)
import ads_lint  # noqa: E402
import ads_negative_check as negcheck  # noqa: E402
import meta_seed  # noqa: E402
import places_seed  # noqa: E402
import qualify_sites  # noqa: E402
from dataforseo import SERP_USD, VOLUME_TASK_USD, DataForSEO  # noqa: E402

FC = ROOT / "projects" / "free-campaign"
CONFIG = FC / "config.json"
LOG = FC / "log.jsonl"
TEMPLATE = FC / "templates" / "audit.html"
DELIVERY_TMPL = ROOT / "templates" / "free-campaign-delivery-email.md"
ASK_TMPL = ROOT / "templates" / "free-campaign-review-ask.md"
SHARED_NEG = ROOT / "projects" / "google-ads" / "negatives" / "shared-lists.md"

PROSPECTS_BASE = "appPM1HmRfFlgA484"
CONTACTS = "tblGdourIuqa9onmp"
CALLS_TABLE = "Free campaign calls"
CRM_BASE = "appgv3njf5Fk99QXo"
CRM_TABLE = "Free campaigns"
CAMPAIGN_PLATFORM_ID = "free-campaign"
STAGES = ["Built", "Approved", "Delivery drafted", "Delivered", "Ask drafted", "Ask sent", "Review left", "Declined"]

PLACES_USD = 35.00 / 1000.0
OPUS_USD = 0.03
YES_RE = re.compile(r"\byes\b|\bsend it\b|\bbuild it\b|\bfree campaign\b|\bsend (the|me the) (audit|campaign|check)\b", re.I)

# The negatives that fit a campaign a homeowner clicks (the Monarc lists block homeowners on purpose; these do not).
HOMEOWNER_SAFE_LISTS = ("Jobs and careers", "Learn and do it yourself", "Lead buyers", "Labor shoppers",
                        "Wrong country or language", "Account and support")
# Keyword words the method keeps out, whatever the trade (projects/google-ads/keywords/method.md).
OUT_WORDS = {"how", "what", "best", "top", "cost", "price", "vs", "tips", "guide", "examples", "template", "software",
             "tool", "app", "jobs", "course", "free", "diy", "cheap"}

VERTICAL_TO_TRADE = {"av integrator": "integrator", "low voltage / it": "integrator", "electrician": "electrician",
                     "hvac": "hvac", "plumber": "plumbing", "roofer": "roofing"}

# One service list per trade (context/trades/<trade>.md, in a buyer's words). label: on the audit and in the ad;
# phrases: what a buyer types, best first; words: how the site says it (nav, headings, text); llm: the Opus read's
# offering key (integrators only). The first service a site shows is the campaign's one service.
TRADES = {
    "integrator": {
        "person": "homeowner", "brands": ["lutron", "control4", "crestron", "savant", "sonos", "josh.ai"],
        "services": [
            {"key": "theater", "label": "Home theater", "llm": "home_theater",
             "phrases": ["home theater installation", "home theater installer", "media room installation"],
             "words": ["theater", "theatre", "media room", "cinema"]},
            {"key": "automation", "label": "Home automation", "llm": "automation_control",
             "phrases": ["home automation installer", "smart home installation", "smart home installer"],
             "words": ["automation", "smart home", "control4", "crestron", "savant", "josh"]},
            {"key": "lighting", "label": "Lighting control", "llm": "lighting_control",
             "phrases": ["lighting control installation", "lighting control installer", "lutron lighting installer"],
             "words": ["lighting control", "lutron", "ketra", "homeworks"]},
            {"key": "shades", "label": "Motorized shades", "llm": "motorized_shades",
             "phrases": ["motorized shades installer", "motorized window shades", "motorized blinds installation"],
             "words": ["shade", "shading", "blinds"]},
            {"key": "audio", "label": "Whole home audio", "llm": "audio_video",
             "phrases": ["whole home audio installation", "whole house audio installer", "outdoor speaker installation"],
             "words": ["audio", "speaker", "sonos", "sound system"]},
            {"key": "networking", "label": "Home networking", "llm": "networking",
             "phrases": ["home network installation", "home wifi installer", "whole home wifi installation"],
             "words": ["network", "wifi", "wi-fi"]},
        ]},
    "electrician": {
        "person": "homeowner", "brands": ["generac", "kohler", "tesla", "lutron", "span"],
        "services": [
            {"key": "panel", "label": "Electrical panel upgrade",
             "phrases": ["electrical panel upgrade", "panel upgrade electrician", "200 amp panel upgrade"],
             "words": ["panel", "200 amp", "service upgrade"]},
            {"key": "generator", "label": "Standby generator",
             "phrases": ["generator installation", "standby generator installer", "whole house generator installation"],
             "words": ["generator", "generac", "kohler"]},
            {"key": "ev", "label": "EV charger",
             "phrases": ["ev charger installation", "ev charger installer", "tesla charger installation"],
             "words": ["ev charger", "ev charging", "tesla", "chargepoint"]},
            {"key": "lighting", "label": "Lighting",
             "phrases": ["recessed lighting installation", "landscape lighting installer", "lighting installation electrician"],
             "words": ["lighting", "recessed", "landscape"]},
            {"key": "rewire", "label": "Rewiring",
             "phrases": ["house rewiring", "whole house rewire", "rewiring electrician"],
             "words": ["rewire", "rewiring", "knob and tube", "aluminum wiring"]},
            {"key": "general", "label": "Residential electrician",
             "phrases": ["residential electrician", "licensed electrician", "electrician"],
             "words": ["electric"]},
        ]},
    "hvac": {
        "person": "homeowner", "brands": ["carrier", "trane", "lennox", "mitsubishi", "daikin", "bryant"],
        "services": [
            {"key": "ac", "label": "AC installation",
             "phrases": ["ac installation", "air conditioning installation", "ac replacement"],
             "words": ["air conditioning", "cooling", "a/c"]},
            {"key": "heatpump", "label": "Heat pump",
             "phrases": ["heat pump installation", "heat pump installer", "heat pump replacement"],
             "words": ["heat pump"]},
            {"key": "furnace", "label": "Furnace",
             "phrases": ["furnace installation", "furnace replacement", "furnace installer"],
             "words": ["furnace", "heating"]},
            {"key": "minisplit", "label": "Ductless mini split",
             "phrases": ["mini split installation", "ductless ac installation", "mini split installer"],
             "words": ["mini split", "ductless"]},
            {"key": "general", "label": "HVAC",
             "phrases": ["hvac installation", "hvac company", "hvac contractor"],
             "words": ["hvac"]},
        ]},
    "plumbing": {
        "person": "homeowner", "brands": ["rinnai", "navien", "kohler", "moen", "bradford white"],
        "services": [
            {"key": "waterheater", "label": "Water heater",
             "phrases": ["water heater installation", "tankless water heater installer", "water heater replacement"],
             "words": ["water heater", "tankless"]},
            {"key": "repipe", "label": "Repiping",
             "phrases": ["repipe plumber", "whole house repipe", "repiping"],
             "words": ["repipe", "repiping"]},
            {"key": "remodel", "label": "Bathroom plumbing",
             "phrases": ["bathroom remodel plumber", "kitchen remodel plumbing", "remodel plumber"],
             "words": ["remodel", "bathroom", "kitchen"]},
            {"key": "sewer", "label": "Sewer line",
             "phrases": ["sewer line replacement", "sewer line repair", "sewer plumber"],
             "words": ["sewer", "drain"]},
            {"key": "general", "label": "Plumber",
             "phrases": ["plumber", "plumbing company", "residential plumber"],
             "words": ["plumb"]},
        ]},
    "roofing": {
        "person": "homeowner", "brands": ["gaf", "owens corning", "certainteed", "decra"],
        "services": [
            {"key": "replace", "label": "Roof replacement",
             "phrases": ["roof replacement", "roofing contractor", "new roof installation"],
             "words": ["replacement", "new roof", "roofing"]},
            {"key": "metal", "label": "Metal roofing",
             "phrases": ["metal roof installation", "metal roofing contractor", "standing seam metal roof"],
             "words": ["metal", "standing seam"]},
            {"key": "repair", "label": "Roof repair",
             "phrases": ["roof repair", "roof leak repair", "roofer"],
             "words": ["repair", "leak"]},
            {"key": "gutters", "label": "Gutters",
             "phrases": ["gutter installation", "gutter replacement", "seamless gutters"],
             "words": ["gutter"]},
            {"key": "general", "label": "Roofing",
             "phrases": ["roofing company", "roofer", "residential roofing"],
             "words": ["roof"]},
        ]},
}


# The short name that fits a 30-character headline, and what the shop does, said as a verb phrase for the ad's
# description ("{name} installs home theaters in {city}.").
SHORT_LINE = {
    ("integrator", "theater"): ("Home theater", "designs and installs home theaters"),
    ("integrator", "automation"): ("Home automation", "designs and installs smart home systems"),
    ("integrator", "lighting"): ("Lighting control", "installs lighting control"),
    ("integrator", "shades"): ("Motorized shades", "installs motorized shades"),
    ("integrator", "audio"): ("Whole home audio", "installs whole home audio"),
    ("integrator", "networking"): ("Home network", "installs home networks and wifi"),
    ("electrician", "panel"): ("Panel upgrade", "upgrades electrical panels"),
    ("electrician", "generator"): ("Generator", "installs standby generators"),
    ("electrician", "ev"): ("EV charger", "installs EV chargers"),
    ("electrician", "lighting"): ("Lighting", "installs lighting indoors and out"),
    ("electrician", "rewire"): ("Rewiring", "rewires homes"),
    ("electrician", "general"): ("Electrician", "handles electrical work for homes"),
    ("hvac", "ac"): ("AC install", "installs air conditioning"),
    ("hvac", "heatpump"): ("Heat pump", "installs heat pumps"),
    ("hvac", "furnace"): ("Furnace", "installs furnaces"),
    ("hvac", "minisplit"): ("Mini split", "installs ductless mini splits"),
    ("hvac", "general"): ("HVAC", "installs and services heating and cooling"),
    ("plumbing", "waterheater"): ("Water heater", "installs water heaters"),
    ("plumbing", "repipe"): ("Repiping", "repipes homes"),
    ("plumbing", "remodel"): ("Bath plumbing", "does remodel plumbing"),
    ("plumbing", "sewer"): ("Sewer line", "replaces and repairs sewer lines"),
    ("plumbing", "general"): ("Plumber", "handles plumbing for homes"),
    ("roofing", "replace"): ("Roof replacement", "replaces roofs"),
    ("roofing", "metal"): ("Metal roofing", "installs metal roofs"),
    ("roofing", "repair"): ("Roof repair", "repairs roofs and leaks"),
    ("roofing", "gutters"): ("Gutters", "installs gutters"),
    ("roofing", "general"): ("Roofing", "roofs homes"),
}
for (_trade, _key), (_short, _line) in SHORT_LINE.items():
    _svc = next(s for s in TRADES[_trade]["services"] if s["key"] == _key)
    _svc["short"], _svc["line"] = _short, _line


# ---------------------------------------------------------------- small things

def today():
    return date.today().isoformat()


def log(event, **kw):
    FC.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": datetime.now().isoformat(timespec="seconds"), "event": event, **kw}) + "\n")


def load_config():
    cfg = {"review_url": "", "asks_per_day": 3, "ask_delay_days": 2, "approvals_before_auto": 3,
           "max_cost_per_company": 0.50, "serp_depth": 10, "keywords": 12}
    if CONFIG.exists():
        cfg.update(json.loads(CONFIG.read_text(encoding="utf-8")))
    return cfg


def slug_for(mb, domain):
    d = re.sub(r"[^a-z0-9.-]", "", (domain or "").lower()) or "no-domain"
    return f"{mb or 'MB-00000'}-{d}"


def folder_for(mb, domain):
    return FC / slug_for(mb, domain)


def read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def first_name(owner):
    name = (owner or "").strip()
    name = re.split(r"[,(]", name)[0].strip()
    return name.split()[0] if name else ""


def state_name(st):
    return STATE_NAMES.get((st or "").upper(), st or "")


def airtable(base, key_name):
    """The Airtable REST client from the CRM server (scripts/crm_server.py), on the base and key given."""
    from crm_server import Airtable  # the module runs nothing on import
    return Airtable(get_secret(key_name, True, f"{key_name} is missing from secrets.env."), base)


def scalar(v):
    return v[0] if isinstance(v, list) and v else v


# ---------------------------------------------------------------- the company

def contacts_row(mb):
    air = airtable(PROSPECTS_BASE, "AIRTABLE_API_KEY")
    recs, _ = air.list_all("Contacts", formula=f"{{Company ID}}='{mb}'",
                           fields=["Name", "Website", "Phone", "City", "State", "Vertical", "Email", "Owner", "Rating",
                                   "Review count", "Company ID"])
    if not recs:
        sys.exit(f"No Contacts row with Company ID {mb} in the Prospects base.")
    f = recs[0]["fields"]
    return {"mb": mb, "record_id": recs[0]["id"], "name": (f.get("Name") or "").strip(), "website": (f.get("Website") or "").strip(),
            "phone": (f.get("Phone") or "").strip(), "city": scalar(f.get("City")) or "", "state": scalar(f.get("State")) or "",
            "vertical": scalar(f.get("Vertical")) or "", "email": (f.get("Email") or "").strip(), "owner": (f.get("Owner") or "").strip(),
            "rating": f.get("Rating"), "review_count": f.get("Review count")}


def company_from_args(a):
    if a.mb:
        c = contacts_row(a.mb)
        if a.trade:
            c["trade"] = a.trade
    else:
        if not (a.domain and a.city and a.state and a.trade):
            sys.exit("Without --mb give --domain, --name, --city, --state, and --trade.")
        c = {"mb": a.mb or "", "record_id": None, "name": a.name or a.domain, "website": a.domain, "phone": a.phone or "",
             "city": a.city, "state": a.state.upper(), "vertical": "", "email": a.to or "", "owner": a.owner or "",
             "rating": None, "review_count": None, "trade": a.trade}
    c["domain"] = norm_domain(c["website"])
    c["trade"] = c.get("trade") or VERTICAL_TO_TRADE.get((c.get("vertical") or "").lower())
    if c["trade"] not in TRADES:
        sys.exit(f"{c['name']}: the trade is {c.get('vertical') or 'blank'}; this build covers {', '.join(TRADES)}. Pass --trade.")
    if not c["domain"]:
        sys.exit(f"{c['name']}: no website on the row, and the audit reads the site. Add one first.")
    return c


# ---------------------------------------------------------------- caches already bought

_site_caches = None
_places_by_domain = None
_contact_caches = None


def site_caches():
    """Every site-cache-*.jsonl in projects/outreach, later files winning: {domain: site row}, {domain: llm row}."""
    global _site_caches
    if _site_caches is None:
        sites, llm = {}, {}
        for p in sorted(OUTREACH.glob("site-cache-*.jsonl")):
            s, l = qualify_sites.load_site_cache(p)
            sites.update(s)
            llm.update(l)
        _site_caches = (sites, llm)
    return _site_caches


def places_by_domain():
    global _places_by_domain
    if _places_by_domain is None:
        idx = {}
        for p in sorted(OUTREACH.glob("places-cache-*.jsonl")):
            recs, _, _ = places_seed.load_cache(p)
            for r in recs.values():
                d = norm_domain(r.get("Website"))
                if d and d not in idx:
                    idx[d] = r
        _places_by_domain = idx
    return _places_by_domain


def contact_caches():
    global _contact_caches
    if _contact_caches is None:
        recs = {}
        for p in sorted(OUTREACH.glob("contact-cache-*.jsonl")):
            recs.update(meta_seed.load_cache(p))
        _contact_caches = recs
    return _contact_caches


# ---------------------------------------------------------------- the site

def site_read(c, folder, meter, a):
    """The site: the cached read when one exists, else a fetch (free). The Opus read only for an integrator with no
    cached read, and never on --from-cache."""
    sites, llms = site_caches()
    site = sites.get(c["domain"])
    llm = (llms.get(c["domain"]) or {}).get("data")
    if not site or not site.get("ok"):
        if a.from_cache or a.dry_run:
            site = site or {"ok": False, "error": "not in the cache"}
        else:
            site = qualify_sites.scan_domain(c["domain"], c["website"])
            with qualify_sites.cache_path(today()).open("a", encoding="utf-8") as fh:
                qualify_sites.append_cache(fh, site)
    if c["trade"] == "integrator" and site.get("ok") and llm is None and not (a.from_cache or a.dry_run) \
            and not qualify_sites.is_thin(site):
        meter.assert_affordable(OPUS_USD, "the Opus site read")
        import anthropic
        client = anthropic.Anthropic(api_key=get_secret("ANTHROPIC_API_KEY", required=True))
        company = {"Name": c["name"], "City": c["city"], "State": c["state"], "Website": c["website"],
                   "Rating": c.get("rating"), "Review count": c.get("review_count")}
        res = qualify_sites.run_sync(client, [(c["domain"], qualify_sites.user_message(company, site))],
                                     qualify_sites.build_system_prompt(), today(), meter)
        llm = (res.get(c["domain"]) or {}).get("data")
    return site, llm


def blob_of(site):
    parts = [site.get("title") or "", site.get("desc") or ""] + list(site.get("headings") or []) + list(site.get("nav") or [])
    parts.append(site.get("text") or "")
    for sp in site.get("subpages") or []:
        parts += [sp.get("title") or "", sp.get("text") or ""]
    return " ".join(parts).lower()


def pick_services(c, site, llm):
    """The campaign's one service and the second search's service, from the site. Integrators with an Opus read:
    the first true offering in the list's order. Everyone else: the service with the most hits on the site."""
    t = TRADES[c["trade"]]
    services = t["services"]
    blob = blob_of(site or {})
    hits = {s["key"]: sum(blob.count(w) for w in s["words"]) for s in services}
    if llm and c["trade"] == "integrator":
        offered = [s for s in services if (llm.get("offerings") or {}).get(s.get("llm"))]
        if offered:
            main = offered[0]
            second = next((s for s in offered[1:]), None) or max((s for s in services if s is not main), key=lambda s: hits[s["key"]])
            return main, second, hits
    ranked = sorted(services, key=lambda s: (-hits[s["key"]], services.index(s)))
    main = ranked[0] if hits[ranked[0]["key"]] else services[-1]
    second = next((s for s in ranked if s is not main), services[0])
    return main, second, hits


def brands_on_site(c, site):
    blob = blob_of(site or {})
    return [b for b in TRADES[c["trade"]]["brands"] if b in blob]


# ---------------------------------------------------------------- Google Places: the market and their own listing

def places_read(c, main, folder, meter, a):
    cached = read_json(folder / "places.json", {})
    out = dict(cached) if cached else {"market": [], "own": None, "query": "", "cost": 0.0}
    own = out.get("own") or places_by_domain().get(c["domain"])
    query = f"{main['phrases'][0]} in {c['city']}, {c['state']}"
    if not out.get("market") and not (a.from_cache or a.dry_run):
        key = get_secret("GOOGLE_MAPS_API_KEY", True, "The Places key is missing from secrets.env.")
        meter.assert_affordable(PLACES_USD, "the Places market search")
        places, _, err = places_seed.search_page(key, query)
        meter.add("places", PLACES_USD)
        if err:
            print(f"  Places: {err}")
        out["market"] = [places_seed.flatten(p, query) for p in places]
        out["query"] = query
        if not own:
            hit = next((r for r in out["market"] if norm_domain(r.get("Website")) == c["domain"]), None)
            if not hit:
                meter.assert_affordable(PLACES_USD, "the Places listing search")
                places, _, err = places_seed.search_page(key, f"{c['name']} {c['city']} {c['state']}")
                meter.add("places", PLACES_USD)
                rows = [places_seed.flatten(p, "own") for p in places]
                hit = next((r for r in rows if norm_domain(r.get("Website")) == c["domain"]), None) or (rows[0] if rows else None)
            own = hit
        out["cost"] = round(float(out.get("cost") or 0) + meter.items.get("places", 0.0), 4)
    # the market search is the freshest read of their listing; the domain index and the call list row are older
    fresh = next((r for r in out.get("market") or [] if norm_domain(r.get("Website")) == c["domain"]), None)
    if fresh:
        own = fresh
    if own is None and (c.get("rating") is not None or c.get("review_count")):
        own = {"Name": c["name"], "Rating": c.get("rating"), "Review count": c.get("review_count"), "Website": c["website"],
               "source": "the call list row"}
    out["own"] = own
    out["query"] = out.get("query") or query
    write_json(folder / "places.json", out)
    return out


# ---------------------------------------------------------------- DataForSEO: the real page

def serp_read(c, main, second, brands, folder, meter, a):
    cached = read_json(folder / "serp.json", {})
    queries = [f"{main['phrases'][0]} {c['city']}",
               (f"{brands[0]} dealer {c['city']}" if brands and c["trade"] == "integrator" else f"{main['phrases'][1]} {c['city']}"),
               f"{second['phrases'][0]} {c['city']} {c['state']}"]
    out = cached if cached.get("pages") else {"pages": [], "location": None, "source": None, "cost": 0.0}
    if out["pages"]:
        return out
    if a.no_serp or a.from_cache or a.dry_run or not DataForSEO.keys_present():
        out["source"] = "none"
        out["why"] = ("--no-serp" if a.no_serp else "--from-cache" if a.from_cache else "dry run" if a.dry_run
                      else "DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD are not in secrets.env")
        out["queries"] = queries
        write_json(folder / "serp.json", out)
        return out
    dfs = DataForSEO.from_env()
    code, name = dfs.city_code(c["city"], c["state"])
    coord = None
    if not code:
        own = (read_json(folder / "places.json", {}) or {}).get("own") or {}
        loc = own.get("location") or {}
        if loc.get("latitude"):
            coord = f"{loc['latitude']},{loc['longitude']},25"
        else:
            print(f"  DataForSEO has no location for {c['city']}, {c['state']}; using the state.")
            code, name = dfs.city_code(state_name(c["state"]), "") if False else (None, None)
    meter.assert_affordable(len(queries) * SERP_USD, "the three results pages")
    pages = []
    for q in queries:
        page, cost = dfs.serp(q, location_code=code, location_coordinate=coord, depth=load_config()["serp_depth"])
        meter.add("serp", cost or SERP_USD)
        pages.append(page)
    out.update(pages=pages, location={"code": code, "name": name, "coordinate": coord}, source="dataforseo",
               fetched=today(), cost=round(meter.items.get("serp", 0.0), 4), queries=queries)
    write_json(folder / "serp.json", out)
    return out


def presence(c, page):
    """Where the company sits on one page: organic rank, ad, map rank, or absent. From the domain and the name."""
    dom, name = c["domain"], (c["name"] or "").lower()
    out = {"organic": None, "ad": False, "map": None}
    for o in page.get("organic") or []:
        if norm_domain(o.get("domain")) == dom:
            out["organic"] = o["n"]
            break
    out["ad"] = any(norm_domain(p.get("domain")) == dom for p in page.get("paid") or [])
    for p in page.get("local_pack") or []:
        if (p.get("domain") and norm_domain(p["domain"]) == dom) or (name and (p.get("title") or "").lower() == name):
            out["map"] = p["n"]
            break
    out["present"] = bool(out["organic"] or out["ad"] or out["map"])
    return out


# ---------------------------------------------------------------- keywords, negatives, ads, the page

def keywords_for(c, main, second, brands, n):
    city, st = c["city"], c["state"]
    geo = [city, f"{city} {st}", "near me"]
    cands = []
    for i, ph in enumerate(main["phrases"]):
        for g in geo if i < 2 else geo[:1]:
            cands.append(f"{ph} {g}")
    for b in brands[:2]:
        cands.append(f"{b} dealer {city}")
    cands.append(f"{main['phrases'][2]} near me")
    cands.append(f"{second['phrases'][0]} {city}")
    cands.append(f"{second['phrases'][0]} near me")
    cands.append(f"{second['phrases'][1]} {city}")
    cands.append(f"{main['phrases'][2]} {city} {st}")
    cands.append(f"{second['phrases'][1]} near me")
    out, seen = [], set()
    for k in cands:
        k = re.sub(r"\s+", " ", k.strip().lower())
        if k in seen or any(w in OUT_WORDS for w in k.split()):
            continue
        seen.add(k)
        out.append({"text": k, "match": ["exact", "phrase"]})
        if len(out) >= n:
            break
    return out


def negatives_for(c, keywords):
    """The shared lists that fit a homeowner-facing campaign plus the trade's own list, every term checked against
    the 12 keywords (a term that blocks one is dropped for this campaign, and named)."""
    lists = [l for l in negcheck.parse_lists(SHARED_NEG) if l["kind"] == "neg" and l["name"] in HOMEOWNER_SAFE_LISTS]
    own = FC / "negatives" / f"{c['trade']}.md"
    if own.exists():
        lists += [l for l in negcheck.parse_lists(own) if l["kind"] == "neg"]
    kws = [negcheck.words(k["text"]) for k in keywords]
    kept, dropped = [], []
    for lst in lists:
        for t in lst["terms"]:
            if t["problems"]:
                continue
            hit = next((" ".join(q) for q in kws if negcheck.blocks(t, q)), None)
            if hit:
                dropped.append({"term": t["raw"], "list": lst["name"], "blocks": hit})
                continue
            kept.append({"text": " ".join(t["words"]), "match": t["kind"], "list": lst["name"]})
    return kept, dropped


def fit(text, limit):
    return text if len(text) <= limit else None


def ads_for(c, main, brands, own):
    """Three responsive search ads by the slot rule (projects/google-ads/README.md, Writing a new ad): slot 1 the
    callout to the person, slot 2 the outcome they want, slot 3 the call to action. Sixth-grade words. Every claim from
    data: the rating and count from their Google listing, the brand from their site, the city from the row."""
    city, st = c["city"], c["state"]
    short = main.get("short") or main["label"]
    line = main.get("line") or f"installs {main['label'].lower()}"
    name = c["name"]
    rating, count = (own or {}).get("Rating"), int((own or {}).get("Review count") or 0)
    proof = rating is not None and float(rating) >= 4.5 and count >= 10
    brand = brands[0].title().replace("Josh.Ai", "Josh.ai") if brands else ""
    low = short.lower()

    def fits(*cands):
        return [x for x in cands if x and len(x) <= 30]

    h1 = fits(f"{short} in {city}", f"{city} {short}", f"{short}, {city} {st}", f"{short} Near {city}", f"{short} Near You",
              f"{short} for Your Home")
    plain2 = fits("Designed and Installed for You", f"Built for {city} Homes", "One Team, Start to Finish", "Done Right the First Time")
    proof2 = fits(f"{rating:g} Stars on Google", f"{count} Google Reviews") if proof else []
    brand2 = fits(f"{brand} Dealer in {city}", f"{brand} Dealer") if brand else []
    h3 = fits("Call for an Estimate", "Book a Home Visit", "Get a Quote Today", f"Call {name}", "Call Today")
    d_service = fit(f"{name} {line} in {city}. Call for an estimate.", 90) or fit(f"We {line} in {city}. Call for an estimate.", 90)
    d_team = fit(f"One team from the first visit to the last test. Serving {city} and nearby.", 90)
    d_proof = fit(f"Rated {rating:g} stars by {count} Google reviews. Call today and talk to the people who do the work.", 90) if proof else None
    d_brand = fit(f"{brand} dealer. Ask about {low} for your home in {city}.", 90) if brand else None
    d_home = fit(f"Tell us about your home in {city}. We plan the work and do it ourselves.", 90)

    def ad(name_, ones, twos, threes, descs):
        heads = [{"text": h, "pin": 1} for h in ones if h] + [{"text": h, "pin": 2} for h in twos if h] + [{"text": h, "pin": 3} for h in threes if h]
        seen, uniq = set(), []
        for h in heads:
            if h["text"].lower() not in seen:
                seen.add(h["text"].lower())
                uniq.append(h)
        return {"name": name_, "headlines": uniq[:15], "descriptions": [d for d in descs if d][:4]}

    ads = [ad("Service", h1[:3], plain2[:3], h3[:2], [d_service, d_team, d_home])]
    if proof:
        ads.append(ad("Proof", h1[:2], proof2[:2] + plain2[1:2], h3[:1] + h3[2:3], [d_proof, d_service, d_team]))
    else:
        ads.append(ad("Local", h1[3:5] + h1[:1], plain2[1:4], h3[1:2] + h3[:1], [d_home, d_service, d_team]))
    if brand:
        ads.append(ad("Brand", h1[:1] + fits(f"{brand} {short} {city}") + h1[1:2], brand2[:2] + plain2[:1], h3[:1] + h3[3:4], [d_brand, d_service, d_team]))
    else:
        ads.append(ad("Home", h1[1:3] + h1[:1], plain2[2:4] + plain2[:1], h3[2:3] + h3[-1:], [d_team, d_home, d_service]))
    return ads


def lint_ads(ads):
    problems = []
    for ad in ads:
        if len(ad["headlines"]) < 3 or len(ad["descriptions"]) < 2:
            problems.append(f"{ad['name']}: too few lines")
        for h in ad["headlines"]:
            for p in ads_lint.check_text(h["text"]):
                problems.append(f"{ad['name']} headline '{h['text']}': {p}")
        for d in ad["descriptions"]:
            for p in ads_lint.check_text(d):
                problems.append(f"{ad['name']} description '{d}': {p}")
            g = ads_lint.grade(d)
            if g is not None and g > 6:
                problems.append(f"{ad['name']} description grade {g}: '{d}'")
    return problems


def pick_page(c, site, main):
    words = [w.lower() for w in main["words"]] + [p.lower() for p in main["phrases"]]
    for sp in (site or {}).get("subpages") or []:
        hay = ((sp.get("url") or "") + " " + (sp.get("title") or "")).lower()
        if any(w in hay for w in words):
            return sp["url"], True
    return (site or {}).get("final_url") or f"https://{c['domain']}/", False


def page_checks(url, main, city, has_own_page, a):
    """What the landing page has and lacks, from one fetch of it. Every line names what was read."""
    out = {"url": url, "fetched": False, "has_service_page": has_own_page}
    if a.dry_run:
        return out
    r, err = fetch(url)
    if r is None:
        out["error"] = err
        return out
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script", "style", "noscript", "svg", "template"]):
        t.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
    h1 = soup.find("h1")
    forms = [f for f in soup.find_all("form") if len(f.find_all(["input", "textarea", "select"])) >= 2]
    words = [w.lower() for w in main["words"]]
    out.update(fetched=True, final_url=r.url, https=r.url.lower().startswith("https://"),
               tel_link=bool(soup.find("a", href=re.compile(r"^tel:", re.I))),
               phone_in_text=bool(re.search(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", text[:2000])),
               form=bool(forms), h1=(h1.get_text(" ", strip=True) if h1 else ""), title=(soup.title.get_text(" ", strip=True) if soup.title else ""),
               words=len(text.split()), testimonials=bool(re.search(r"\b(review|reviews|testimonial|testimonials|what our clients|stars)\b", text, re.I)))
    out["h1_says_service"] = any(w in out["h1"].lower() for w in words)
    out["h1_says_city"] = city.lower() in out["h1"].lower()
    out["title_says_city"] = city.lower() in out["title"].lower()
    return out


def fixes_for(pc, main, city):
    label = main["label"]
    if not pc.get("fetched"):
        return [{"what": "The page could not be read", "fix": f"Make sure {pc.get('url')} loads for a visitor. Read: the fetch failed ({pc.get('error', 'no reply')})."}]
    checks = [
        (not pc.get("has_service_page"), f"No page of its own for {label.lower()}",
         f"Add one page for {label.lower()} with its own address, and send the ad there. Read: no page on the site names it."),
        (not pc.get("tel_link"), "No tap-to-call phone number",
         "Put the phone number at the top as a link a phone can tap. Read: no tel: link on the page."),
        (not pc.get("form"), "No form on the page",
         "Add one short form: name, phone, email. Read: no form with two or more fields."),
        (not (pc.get("h1_says_service") and pc.get("h1_says_city")), f"The headline does not say {label.lower()} and {city}",
         f"Make the headline say {label.lower()} in {city}, the words the ad and the search use. Read: the h1 is \"{(pc.get('h1') or '')[:80]}\"."),
        (not pc.get("title_says_city"), f"The page title does not say {city}",
         f"Put {city} in the page title. Read: the title is \"{(pc.get('title') or '')[:80]}\"."),
        (not pc.get("https"), "The page is not on https",
         "Turn on https; Google marks the page as not secure. Read: the address starts with http."),
        ((pc.get("words") or 0) < 300, "Under 300 words",
         f"Write what you install, where, and what happens on the first visit. Read: {pc.get('words', 0)} words on the page."),
        (not pc.get("testimonials"), "No reviews on the page",
         "Put three Google reviews on the page, with names. Read: no review or testimonial words on the page."),
    ]
    return [{"what": w, "fix": f} for bad, w, f in checks if bad][:3]


def volume_read(keywords, serp, folder, meter, a):
    cached = read_json(folder / "volume.json", None)
    if cached:
        return cached
    if a.no_serp or a.from_cache or a.dry_run or not DataForSEO.keys_present():
        return {"rows": {}, "source": "none"}
    dfs = DataForSEO.from_env()
    code = (serp.get("location") or {}).get("code")
    meter.assert_affordable(VOLUME_TASK_USD, "the volume call")
    rows, cost = dfs.volume([k["text"] for k in keywords], location_code=code)
    meter.add("volume", cost or VOLUME_TASK_USD)
    out = {"rows": rows, "source": "dataforseo", "location_code": code, "fetched": today()}
    write_json(folder / "volume.json", out)
    return out


def budget_line(volume):
    """Median high top-of-page bid times three clicks a day, rounded up to $5; $10 when there is no bid data.
    A rule for Jonathan to confirm."""
    bids = [r["bid_high"] for r in (volume.get("rows") or {}).values() if r.get("bid_high")]
    if not bids:
        return 10, "no bid data; $10 a day as the floor"
    med = statistics.median(bids)
    usd = max(10, int(-(-med * 3 // 5) * 5))
    return usd, f"median top-of-page bid ${med:.2f} times three clicks a day, rounded up to $5"


# ---------------------------------------------------------------- the files in the folder

def write_campaign_json(c, main, keywords, negatives, ads, page, budget, folder):
    data = {"_note": "The free campaign, the shape of projects/google-ads/campaigns/NN-<service>.json. Built by scripts/free_campaign.py; "
                     "the Editor file beside it is what the prospect loads.",
            "name": f"{c['name']} | {main['label']} | {c['city']}", "service": main["key"], "trade": c["trade"],
            "page": page, "daily_budget": budget, "bidding": {"strategy": "maximize_clicks", "max_cpc": None},
            "network": {"search_partners": False, "display": False},
            "geo": {"location": f"{c['city']}, {state_name(c['state'])}, United States"}, "language": "en",
            "keywords": keywords, "negatives": negatives, "ads": ads, "status": "paused"}
    write_json(folder / "campaign.json", data)
    return data


EDITOR_COLS = ["Campaign", "Campaign Type", "Budget", "Campaign Status", "Networks", "Bid Strategy Type", "Languages",
               "Location", "Ad Group", "Ad Group Status", "Keyword", "Criterion Type", "Final URL", "Status", "Ad type"]
H_COLS = [f"Headline {i}" for i in range(1, 16)]
HP_COLS = [f"Headline {i} position" for i in range(1, 16)]
D_COLS = [f"Description {i}" for i in range(1, 5)]
PATH_COLS = ["Path 1", "Path 2"]


def write_editor_csv(camp, c, main, folder):
    """One Google Ads Editor import file: the campaign (paused), one ad group, the keywords, the campaign-level
    negatives, three responsive search ads. Column names follow Editor's own (verify against a 07 export once)."""
    cols = EDITOR_COLS + H_COLS + HP_COLS + D_COLS + PATH_COLS
    cname, gname = camp["name"], main["label"]
    rows = [{"Campaign": cname, "Campaign Type": "Search", "Budget": camp["daily_budget"], "Campaign Status": "Paused",
             "Networks": "Google search", "Bid Strategy Type": "Maximize clicks", "Languages": "en",
             "Location": camp["geo"]["location"]},
            {"Campaign": cname, "Ad Group": gname, "Ad Group Status": "Enabled"}]
    for k in camp["keywords"]:
        for m in k["match"]:
            rows.append({"Campaign": cname, "Ad Group": gname, "Keyword": k["text"], "Criterion Type": m.title(), "Status": "Enabled"})
    for n in camp["negatives"]:
        rows.append({"Campaign": cname, "Keyword": n["text"], "Criterion Type": f"Negative {n['match'].title()}"})
    path1 = re.sub(r"[^A-Za-z0-9]", "", main["label"].split()[0])[:15]
    path2 = re.sub(r"[^A-Za-z0-9]", "", c["city"])[:15]
    for ad in camp["ads"]:
        row = {"Campaign": cname, "Ad Group": gname, "Ad type": "Responsive search ad", "Final URL": camp["page"], "Status": "Enabled",
               "Path 1": path1, "Path 2": path2}
        for i, h in enumerate(ad["headlines"], 1):
            row[f"Headline {i}"] = h["text"]
            if h.get("pin"):
                row[f"Headline {i} position"] = h["pin"]
        for i, d in enumerate(ad["descriptions"], 1):
            row[f"Description {i}"] = d
        rows.append(row)
    with (folder / "ads-editor.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})
    return len(rows)


def esc(s):
    return html_mod.escape(str(s if s is not None else ""))


def who_shows(page, n=4):
    """The ads, the map, and the organic names on one page, as short html."""
    bits = []
    ads = [esc(p.get("domain") or p.get("title")) for p in page.get("paid") or []][:3]
    if ads:
        bits.append("<b>Ads:</b> " + ", ".join(ads))
    pack = [f"{esc(p.get('title'))} ({p['rating']:g}, {p['reviews']})" if p.get("rating") is not None else esc(p.get("title"))
            for p in page.get("local_pack") or []][:3]
    if pack:
        bits.append("<b>Map:</b> " + "; ".join(pack))
    org = [f"{o['n']}. {esc(o.get('domain'))}" for o in page.get("organic") or []][:n]
    if org:
        bits.append("<b>Page:</b> " + ", ".join(org))
    return "<br>".join(bits) or "No results read"


def you_cell(p):
    if not p["present"]:
        return '<span class="absent">Absent</span>'
    parts = []
    if p["ad"]:
        parts.append("ad")
    if p["map"]:
        parts.append(f"map #{p['map']}")
    if p["organic"]:
        parts.append(f"#{p['organic']} on the page")
    return '<span class="present">' + ", ".join(parts) + "</span>"


def write_audit_html(c, main, serp, places, page_url, fixes, camp, folder):
    cfg = Template(TEMPLATE.read_text(encoding="utf-8"))
    pages = serp.get("pages") or []
    rows = []
    if pages:
        for pg in pages:
            rows.append(f"<tr><td>{esc(pg['keyword'])}</td><td>{who_shows(pg)}</td><td>{you_cell(presence(c, pg))}</td></tr>")
        searches_note = (f"The live Google results page, read {esc(serp.get('fetched'))} for a searcher in "
                         f"{esc((serp.get('location') or {}).get('name') or c['city'])}.")
    else:
        market = places.get("market") or []
        names = "; ".join(f"{esc(m['Name'])} ({m['Rating']:g}, {m['Review count']})" if m.get("Rating") is not None else esc(m["Name"])
                          for m in market[:5]) or "No results read"
        mine = next((i for i, m in enumerate(market, 1) if norm_domain(m.get("Website")) == c["domain"]), None)
        you = f'<span class="present">#{mine} on the map</span>' if mine else '<span class="absent">Absent</span>'
        rows.append(f"<tr><td>{esc(places.get('query'))}</td><td><b>Map:</b> {names}</td><td>{you}</td></tr>")
        searches_note = "Google Maps results (Google Places). The live results page was not pulled for this build."
    own = places.get("own") or {}
    market = [m for m in (places.get("market") or []) if m.get("Review count") is not None]
    counts = sorted((int(m["Review count"]) for m in market), reverse=True)
    leader = max(market, key=lambda m: int(m["Review count"] or 0)) if market else None
    pack = next((pg.get("local_pack") for pg in pages if pg.get("local_pack")), None) or []
    own_line = (f"{esc(c['name'])}: {own['Rating']:g} stars, {int(own.get('Review count') or 0)} reviews on Google."
                if own.get("Rating") is not None else f"{esc(c['name'])}: no Google rating found.")
    pack_line = ("The map shows: " + "; ".join(f"{esc(p['title'])} {p['rating']:g} ({p['reviews']})" for p in pack[:3] if p.get("rating") is not None) + "."
                 if pack else "")
    market_line = (f"The top {len(counts)} shops for \"{esc(places.get('query'))}\": median {int(statistics.median(counts))} reviews; "
                   f"the leader, {esc(leader['Name'])}, has {int(leader['Review count'])}." if counts else "")
    fix_items = "".join(f"<li><b>{esc(f['what'])}.</b> {esc(f['fix'])}</li>" for f in fixes) or "<li>Nothing read.</li>"
    kw = ", ".join(k["text"] for k in camp["keywords"])
    html_out = cfg.safe_substitute(
        company=esc(c["name"]), city=esc(c["city"]), st=esc(c["state"]), date=today(), service=esc(main["label"]),
        service_lower=esc(main["label"].lower()), person=esc(TRADES[c["trade"]]["person"]), searches_rows="".join(rows),
        searches_note=searches_note, own_line=own_line, pack_line=pack_line, market_line=market_line, page_url=esc(page_url),
        fixes=fix_items, n_keywords=len(camp["keywords"]), n_negatives=len(camp["negatives"]), n_ads=len(camp["ads"]),
        budget=camp["daily_budget"], keywords=esc(kw), domain=esc(c["domain"]))
    (folder / "audit.html").write_text(html_out, encoding="utf-8")
    return folder / "audit.html"


BROWSERS = [os.environ.get("CHROME_PATH", ""),
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]


def html_to_pdf(html_path, pdf_path):
    exe = next((p for p in BROWSERS if p and os.path.exists(p)), None)
    if not exe:
        return False, "no Edge or Chrome found (set CHROME_PATH)"
    cmd = [exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--no-first-run", "--disable-extensions",
           f"--print-to-pdf={pdf_path}", Path(html_path).resolve().as_uri()]
    try:
        subprocess.run(cmd, capture_output=True, timeout=90)
    except subprocess.TimeoutExpired:
        return False, "the browser timed out"
    ok = Path(pdf_path).exists() and Path(pdf_path).stat().st_size > 1000
    return ok, "" if ok else "no PDF written"


# ---------------------------------------------------------------- emails (drafts only)

def template_email(path):
    """A template file: the block under "## Email" with a **Subject:** line, then the body."""
    md = path.read_text(encoding="utf-8")
    block = md.split("## Email", 1)[1] if "## Email" in md else md
    block = block.split("\n## ", 1)[0].strip()
    m = re.search(r"\*\*Subject:\*\*\s*(.+)", block)
    subject = m.group(1).strip() if m else "Monarc Build"
    body = block[m.end():].strip() if m else block
    return subject, body


def fill(text, vals):
    return re.sub(r"\{(\w+)\}", lambda m: str(vals.get(m.group(1), m.group(0))), text)


def email_values(c, data, cfg):
    return {"first_name": first_name(c.get("owner")) or "Hi", "company": c["name"], "city": c["city"], "service": (data.get("main") or {}).get("label", "").lower(),
            "service_label": (data.get("main") or {}).get("label", ""), "budget": (data.get("campaign") or {}).get("daily_budget", ""),
            "review_url": cfg.get("review_url") or "{review_url}", "domain": c["domain"], "page": (data.get("page") or {}).get("url", "")}


def write_drafts(c, data, folder, cfg):
    vals = email_values(c, data, cfg)
    for tmpl, name in ((DELIVERY_TMPL, "delivery.draft.txt"), (ASK_TMPL, "review-ask.draft.txt")):
        subject, body = template_email(tmpl)
        spec = f"To: {c.get('email') or '{email}'}\nSubject: {fill(subject, vals)}\n\n{fill(body, vals)}\n"
        (folder / name).write_text(spec, encoding="utf-8")


def place_draft(spec_path, attachments):
    import proton_mail
    m = proton_mail.connect()
    try:
        # a delivery to the same address with the same subject inside 7 days is not drafted twice
        ok = proton_mail.cmd_draft(m, str(spec_path), [str(p) for p in attachments])
        if not ok:
            raise RuntimeError("not drafted: the same email is already in Drafts or Sent (proton_mail.same_mail)")
    finally:
        try:
            m.logout()
        except Exception:  # noqa: BLE001
            pass


def sent_has(subject):
    import proton_mail
    m = proton_mail.connect()
    try:
        ids = proton_mail.fetch_ids(m, "Sent", f'SUBJECT "{subject}"')
        return bool(ids)
    finally:
        try:
            m.logout()
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------- Monarc CRM rows

def crm_rows():
    air = airtable(CRM_BASE, "AIRTABLE_PAT")
    recs, _ = air.list_all(CRM_TABLE)
    return air, [dict(r["fields"], id=r["id"]) for r in recs]


def crm_campaign_id(air):
    recs, _ = air.list_all("Campaigns", formula=f"{{Platform id}}='{CAMPAIGN_PLATFORM_ID}'", fields=["Name"])
    return recs[0]["id"] if recs else None


def crm_upsert(c, fields, dry_run=False):
    """One Free campaigns row per MB ID (or domain when there is none). Returns the row."""
    if dry_run:
        print(f"  (dry run) CRM row {c.get('mb') or c['domain']}: {fields}")
        return None
    air, rows = crm_rows()
    key = c.get("mb") or c["domain"]
    row = next((r for r in rows if (r.get("MB ID") or "") == key or (not c.get("mb") and (r.get("Folder") or "").endswith(c["domain"]))), None)
    if row:
        air.update(CRM_TABLE, [(row["id"], fields)])
        return dict(row, **fields)
    base = {"Company name": c["name"], "MB ID": key, "Trade": c["trade"], "City": f"{c['city']}, {c['state']}",
            "Folder": str(folder_for(c.get("mb"), c["domain"]).relative_to(ROOT)).replace("\\", "/")}
    cid = crm_campaign_id(air)
    if cid:
        base["Campaign"] = [cid]
    base.update(fields)
    created = air.create(CRM_TABLE, [base])
    return dict(created[0]["fields"], id=created[0]["id"]) if created else None


def link_company(c):
    """A delivered company joins the prospect list: its CRM Companies row by Key, created when missing (write rule 1)."""
    air = airtable(CRM_BASE, "AIRTABLE_PAT")
    key = c["domain"] or f"tel:{re.sub(r'[^0-9]', '', c['phone'])[-10:]}"
    recs, _ = air.list_all("Companies", formula=f"{{Key}}='{key}'", fields=["Name"])
    if recs:
        return recs[0]["id"]
    created = air.create("Companies", [{"Name": c["name"], "Key": key, "Website": c["website"] or None, "Phone": c["phone"] or None,
                                        "City": c["city"], "State": c["state"], "Source": ["cold"],
                                        "Vertical": "Integrator" if c["trade"] == "integrator" else "Electrician" if c["trade"] == "electrician" else None,
                                        "Notes": f"Free campaign for a review ({today()}): {c.get('mb') or ''}"}])
    return created[0]["id"] if created else None


# ---------------------------------------------------------------- commands

def cmd_build(a):
    cfg = load_config()
    c = company_from_args(a)
    folder = folder_for(c.get("mb"), c["domain"])
    folder.mkdir(parents=True, exist_ok=True)
    meter = CostMeter(a.max_cost if a.max_cost is not None else cfg["max_cost_per_company"])
    print(f"{c['name']} ({c.get('mb') or 'no MB ID'}), {c['city']}, {c['state']}, {c['trade']}: {folder.relative_to(ROOT)}")
    if a.dry_run:
        est = {"places": PLACES_USD * (1 if c["domain"] in places_by_domain() else 2), "serp": 3 * SERP_USD, "volume": VOLUME_TASK_USD,
               "opus": 0.0 if c["domain"] in site_caches()[1] or c["trade"] != "integrator" else OPUS_USD}
        print(f"  estimate ${sum(est.values()):.3f}: " + ", ".join(f"{k} ${v:.3f}" for k, v in est.items()))
        report_key_sources(["GOOGLE_MAPS_API_KEY", "DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD", "ANTHROPIC_API_KEY", "AIRTABLE_API_KEY", "AIRTABLE_PAT"])
    try:
        site, llm = site_read(c, folder, meter, a)
        main, second, hits = pick_services(c, site, llm)
        brands = brands_on_site(c, site)
        places = places_read(c, main, folder, meter, a)
        serp = serp_read(c, main, second, brands, folder, meter, a)
        keywords = keywords_for(c, main, second, brands, int(cfg["keywords"]))
        negatives, dropped = negatives_for(c, keywords)
        ads = ads_for(c, main, brands, places.get("own"))
        problems = lint_ads(ads)
        page_url, has_page = pick_page(c, site, main)
        pc = page_checks(page_url, main, c["city"], has_page, a)
        fixes = fixes_for(pc, main, c["city"])
        volume = volume_read(keywords, serp, folder, meter, a)
        budget, budget_why = budget_line(volume)
    except BudgetExceeded as e:
        sys.exit(str(e))
    camp = write_campaign_json(c, main, keywords, negatives, ads, page_url, budget, folder)
    n_rows = write_editor_csv(camp, c, main, folder)
    data = {"built": datetime.now().isoformat(timespec="seconds"), "company": c,
            "site": {k: site.get(k) for k in ("ok", "error", "final_url", "https_ok", "platform", "title", "headings", "nav", "subpages")} if site else None,
            "llm": llm, "service_hits": hits, "main": {k: main[k] for k in ("key", "label", "phrases", "words")},
            "second": {k: second[k] for k in ("key", "label", "phrases")}, "brands": brands,
            "places": {"query": places.get("query"), "own": places.get("own"), "market": places.get("market")},
            "serp": {"source": serp.get("source"), "why": serp.get("why"), "location": serp.get("location"), "queries": serp.get("queries"),
                     "presence": [{"keyword": p["keyword"], **presence(c, p)} for p in serp.get("pages") or []]},
            "page": pc, "fixes": fixes, "volume": volume, "budget": {"usd": budget, "why": budget_why},
            "campaign": {"keywords": keywords, "negatives": len(negatives), "negatives_dropped": dropped, "ads": ads, "lint": problems,
                         "daily_budget": budget, "editor_rows": n_rows},
            "cost": meter.summary()}
    write_json(folder / "data.json", data)
    audit = write_audit_html(c, main, serp, places, page_url, fixes, camp, folder)
    ok, why = html_to_pdf(audit, folder / "audit.pdf")
    write_drafts(c, data, folder, cfg)
    log("build", mb=c.get("mb"), domain=c["domain"], cost=meter.total, serp=serp.get("source"), pdf=ok)
    print(f"  service {main['label']} (second: {second['label']}); brands on the site: {', '.join(brands) or 'none'}")
    print(f"  results page: {serp.get('source')}" + (f" ({serp.get('why')})" if serp.get("why") else ""))
    print(f"  {len(keywords)} keywords, {len(negatives)} negatives ({len(dropped)} dropped), {len(ads)} ads, budget ${budget}/day ({budget_why})")
    print(f"  page {page_url}: {len(fixes)} fixes; editor rows {n_rows}; pdf {'ok' if ok else 'FAILED: ' + why}")
    if problems:
        print("  ad lint: " + "; ".join(problems))
    print(f"  spent ${meter.total:.3f}")
    if not a.dry_run and not a.no_crm and c.get("mb"):
        crm_upsert(c, {"Stage": "Built", "Built on": today(), "Email": c.get("email") or None,
                       "Notes": f"Service {main['label']}; {len(fixes)} fixes; results page {serp.get('source')}; ${meter.total:.2f}."})
    return folder


def calls_rows():
    """The second window's log in the Prospects base: every row with a typed Status, with its company's MB ID."""
    air = airtable(PROSPECTS_BASE, "AIRTABLE_API_KEY")
    recs, _ = air.list_all(CALLS_TABLE, formula="NOT({Status (typed)}='')")
    out = []
    for r in recs:
        f = r["fields"]
        out.append({"id": r["id"], "mb": scalar(f.get("Company ID")) or "", "name": scalar(f.get("Name")) or "",
                    "typed": (f.get("Status (typed)") or "").strip(), "email": (f.get("Email") or "").strip(),
                    "website": scalar(f.get("Website")) or "", "at": f.get("Status changed")})
    return out


def cmd_queue(a):
    rows = [r for r in calls_rows() if YES_RE.search(r["typed"])]
    print(f"{len(rows)} yes rows in {CALLS_TABLE}.")
    for r in rows:
        if not r["mb"]:
            print(f"  {r['name'] or r['id']}: no company linked; skipped")
            continue
        folder = folder_for(r["mb"], norm_domain(r["website"]))
        if (folder / "data.json").exists():
            continue
        print(f"  building {r['mb']} {r['name']}")
        sub = argparse.Namespace(mb=r["mb"], domain=None, name=None, city=None, state=None, trade=None, phone=None, to=r["email"],
                                 owner=None, dry_run=a.dry_run, max_cost=None, from_cache=False, no_serp=a.no_serp, no_crm=False)
        try:
            cmd_build(sub)
        except SystemExit as e:
            print(f"  {r['mb']}: {e}")
        if r["email"] and not a.dry_run:
            crm_upsert({"mb": r["mb"], "domain": norm_domain(r["website"]), "name": r["name"], "trade": "", "city": "", "state": ""},
                       {"Email": r["email"]})


def cmd_deliver(a):
    cfg = load_config()
    c = contacts_row(a.mb)
    c["domain"] = norm_domain(c["website"])
    c["trade"] = VERTICAL_TO_TRADE.get(c["vertical"].lower(), "")
    folder = folder_for(a.mb, c["domain"])
    data = read_json(folder / "data.json")
    if not data:
        sys.exit(f"Nothing built for {a.mb} yet: python scripts/free_campaign.py build --mb {a.mb}")
    air, rows = crm_rows()
    row = next((r for r in rows if r.get("MB ID") == a.mb), None)
    stage = (row or {}).get("Stage") or "Built"
    delivered = sum(1 for r in rows if STAGES.index(r.get("Stage") or "Built") >= STAGES.index("Delivered") and r.get("Stage") != "Declined")
    if delivered < int(cfg["approvals_before_auto"]) and stage == "Built":
        sys.exit(f"{a.mb}: the first {cfg['approvals_before_auto']} deliveries need Jonathan's word. Set the row's Stage to Approved in the CRM, then rerun.")
    if stage not in ("Built", "Approved"):
        sys.exit(f"{a.mb} is at {stage}; nothing to draft.")
    email = a.to or (row or {}).get("Email") or c.get("email")
    if not email:
        sys.exit(f"{a.mb}: no email on the call log row or the Contacts row. Pass --to.")
    c["email"] = email
    if not c.get("owner"):
        rec = contact_caches().get(c["domain"])
        if rec:
            c["owner"] = meta_seed.pick_owner(rec)[0]
    write_drafts(c, data, folder, cfg)
    spec = folder / "delivery.draft.txt"
    att = [folder / "audit.pdf", folder / "ads-editor.csv"]
    missing = [p.name for p in att if not p.exists()]
    if missing:
        sys.exit(f"{a.mb}: missing {', '.join(missing)}; rebuild first.")
    if a.dry_run:
        print(spec.read_text(encoding="utf-8"))
        print(f"(dry run) would draft with {', '.join(p.name for p in att)}")
        return
    place_draft(spec, att)
    subject = spec.read_text(encoding="utf-8").split("\n")[1].replace("Subject:", "").strip()
    crm_upsert(c, {"Stage": "Delivery drafted", "Email": email, "Delivery subject": subject})
    log("delivery drafted", mb=a.mb, to=email)
    print(f"{a.mb}: delivery draft in Proton Drafts, to {email}. Send it from Proton.")


def cmd_readback(a):
    cfg = load_config()
    air, rows = crm_rows()
    n = 0
    for r in rows:
        stage = r.get("Stage")
        if stage == "Delivery drafted" and r.get("Delivery subject") and sent_has(r["Delivery subject"]):
            d = date.today()
            air.update(CRM_TABLE, [(r["id"], {"Stage": "Delivered", "Delivered on": d.isoformat(),
                                               "Ask due": (d + timedelta(days=int(cfg["ask_delay_days"]))).isoformat()})])
            log("delivered", mb=r.get("MB ID"))
            n += 1
        elif stage == "Ask drafted" and r.get("Ask subject") and sent_has(r["Ask subject"]):
            air.update(CRM_TABLE, [(r["id"], {"Stage": "Ask sent", "Ask sent on": today()})])
            log("ask sent", mb=r.get("MB ID"))
            n += 1
    print(f"readback: {n} row(s) moved.")


def profile_live():
    air = airtable(CRM_BASE, "AIRTABLE_PAT")
    recs, _ = air.list_all("Listings", formula="{Directory}='Google Business Profile'", fields=["Status"])
    return bool(recs) and recs[0]["fields"].get("Status") == "Live"


def cmd_asks(a):
    cfg = load_config()
    gate_ok = a.force_gate or (bool(cfg.get("review_url")) and profile_live())
    air, rows = crm_rows()
    due = [r for r in rows if r.get("Stage") == "Delivered" and (r.get("Ask due") or "9999") <= today()]
    due.sort(key=lambda r: r.get("Delivered on") or "")
    drafted_today = sum(1 for r in rows if r.get("Ask drafted on") == today())
    room = max(0, int(cfg["asks_per_day"]) - drafted_today)
    if not gate_ok:
        print(f"{len(due)} ask(s) due, held: " + ("no review_url in projects/free-campaign/config.json" if not cfg.get("review_url")
                                                   else "the Google Business Profile listing is not Live yet") + ".")
        return
    for r in due[:room]:
        mb = r.get("MB ID")
        c = contacts_row(mb) if mb and mb.startswith("MB-") else {"name": r.get("Company name"), "owner": "", "email": r.get("Email"), "city": "", "domain": ""}
        c["domain"] = norm_domain(c.get("website") or "")
        c["email"] = r.get("Email") or c.get("email")
        folder = FC / (r.get("Folder") or "").split("/")[-1]
        data = read_json(folder / "data.json", {})
        if not c.get("owner"):
            rec = contact_caches().get(c["domain"])
            if rec:
                c["owner"] = meta_seed.pick_owner(rec)[0]
        write_drafts(c, data, folder, cfg)
        spec = folder / "review-ask.draft.txt"
        if a.dry_run:
            print(spec.read_text(encoding="utf-8"))
            continue
        place_draft(spec, [])
        subject = spec.read_text(encoding="utf-8").split("\n")[1].replace("Subject:", "").strip()
        air.update(CRM_TABLE, [(r["id"], {"Stage": "Ask drafted", "Ask drafted on": today(), "Ask subject": subject})])
        log("ask drafted", mb=mb)
        print(f"{mb}: review ask in Drafts, to {c['email']}.")
    rest = len(due) - min(len(due), room)
    if rest:
        print(f"{rest} more wait for tomorrow (cap {cfg['asks_per_day']} a day).")


def cmd_status(a):
    air, rows = crm_rows()
    by = {}
    for r in rows:
        by[r.get("Stage") or "Built"] = by.get(r.get("Stage") or "Built", 0) + 1
    print("Free campaigns: " + ", ".join(f"{k} {by[k]}" for k in STAGES if k in by) + (f" ({len(rows)} rows)" if rows else " (none yet)"))
    cfg = load_config()
    print(f"review link: {'set' if cfg.get('review_url') else 'not set'}; profile live: {profile_live()}")
    folders = [p for p in FC.glob("MB-*") if (p / "data.json").exists()]
    print(f"{len(folders)} folder(s) built on disk.")


def cmd_check(a):
    folder = folder_for(a.mb or "", a.domain) if a.domain else (next(FC.glob(f"{a.mb}-*"), None) if a.mb else None)
    if not folder or not (folder / "audit.html").exists():
        sys.exit("No built folder for that MB ID or domain.")
    data = (folder / "data.json").read_text(encoding="utf-8")

    def words_of(html_text):
        body = re.sub(r"<style>.*?</style>", " ", html_text, flags=re.S)
        text = html_mod.unescape(re.sub(r"<[^>]+>", " ", body))
        nums = {n.strip(".,") for n in re.findall(r"\d[\d,.]*", text) if n.strip(".,")}
        names = set(re.findall(r"[A-Z][A-Za-z&'.-]+(?: [A-Z][A-Za-z&'.-]+)*", text))
        return nums, names

    nums, names = words_of((folder / "audit.html").read_text(encoding="utf-8"))
    tmpl_nums, tmpl_names = words_of(TEMPLATE.read_text(encoding="utf-8"))
    # what the template itself says is not data; everything else on the page must be in data.json
    missing = sorted(n for n in nums - tmpl_nums if n.replace(",", "") not in data and n not in data)
    out = sorted(n for n in names - tmpl_names if n not in data and len(n) > 3 and not n.startswith("Google"))
    print(f"{folder.name}: {len(nums)} numbers in the audit, {len(missing)} not in data.json" + (f": {', '.join(missing)}" if missing else ""))
    if out:
        print(f"  names not in the data: {', '.join(out[:20])}")
    sys.exit(1 if missing or out else 0)


def cmd_setup(a):
    """The second window's call log, a table in the Prospects base, read by the CRM as the free-campaign push."""
    air = airtable(PROSPECTS_BASE, "AIRTABLE_API_KEY")
    meta = air.meta()
    contacts = next(t for t in meta["tables"] if t["id"] == CONTACTS)
    fid = {f["name"]: f["id"] for f in contacts["fields"]}
    body = {"name": CALLS_TABLE, "description": "The second call window (2026-10-03): the free campaign for a review. Pick the company, "
                                                "type the outcome in Status (typed) as on Contacts; a yes builds the delivery.",
            "fields": [{"name": "Call", "type": "singleLineText", "description": "Anything; the company link is what counts."},
                       {"name": "Company", "type": "multipleRecordLinks", "options": {"linkedTableId": CONTACTS}},
                       {"name": "Status (typed)", "type": "multilineText"},
                       {"name": "Email", "type": "email"},
                       {"name": "Notes", "type": "multilineText"}]}
    have = next((t for t in meta.get("tables", []) if t["name"] == CALLS_TABLE), None)
    if a.dry_run:
        print(f"{CALLS_TABLE}: {'exists, ' + have['id'] if have else 'would be created'}")
        print(json.dumps(body, indent=1))
        return None
    t = have or air._request("POST", f"meta/bases/{PROSPECTS_BASE}/tables", body=body)
    tid = t["id"]
    ids = {f["name"]: f["id"] for f in t["fields"]}
    # the fields added after the table (a lookup needs the link field's id; idempotent, so a rerun fills what is missing)
    for name, src in (("Company ID", "Company ID"), ("Name", "Name"), ("Website", "Website"), ("Phone", "Phone")):
        if name not in ids:
            air._request("POST", f"meta/bases/{PROSPECTS_BASE}/tables/{tid}/fields",
                         body={"name": name, "type": "multipleLookupValues",
                               "options": {"recordLinkFieldId": ids["Company"], "fieldIdInLinkedTable": fid[src]}})
    if "Status changed" not in ids:
        air._request("POST", f"meta/bases/{PROSPECTS_BASE}/tables/{tid}/fields",
                     body={"name": "Status changed", "type": "lastModifiedTime",
                           "options": {"referencedFieldIds": [ids["Status (typed)"]]}})
    print(f"{'found' if have else 'created'} {CALLS_TABLE}: {tid}")
    print("Config row call_sheets for the CRM:")
    print(json.dumps({"free-campaign": [{"label": CALLS_TABLE, "base": PROSPECTS_BASE, "table": tid, "field": None, "text_field": "Status (typed)",
                                          "changed_field": "Status changed", "key_fields": ["Website", "Phone"], "show_fields": ["Name", "Company ID"],
                                          "skip": ["Wrong vertical"], "token": "AIRTABLE_API_KEY",
                                          "url": f"https://airtable.com/{PROSPECTS_BASE}/{tid}"}]}, indent=1))
    return tid


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")

    def common(p):
        p.add_argument("--mb", default="")
        p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("build")
    common(p)
    for k in ("domain", "name", "city", "state", "trade", "phone", "to", "owner"):
        p.add_argument(f"--{k}", default="")
    p.add_argument("--max-cost", type=float, default=None)
    p.add_argument("--from-cache", action="store_true", help="no network at all: the caches only")
    p.add_argument("--no-serp", action="store_true", help="skip DataForSEO; the audit falls back to the map results")
    p.add_argument("--no-crm", action="store_true", help="do not write the Monarc CRM row")
    p = sub.add_parser("queue")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-serp", action="store_true")
    p = sub.add_parser("deliver")
    common(p)
    p.add_argument("--to", default="")
    p = sub.add_parser("readback")
    p = sub.add_parser("asks")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force-gate", action="store_true", help="draft even before the profile is live (a test only)")
    p = sub.add_parser("status")
    p = sub.add_parser("check")
    common(p)
    p.add_argument("--domain", default="")
    p = sub.add_parser("setup")
    p.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return
    {"build": cmd_build, "queue": cmd_queue, "deliver": cmd_deliver, "readback": cmd_readback, "asks": cmd_asks,
     "status": cmd_status, "check": cmd_check, "setup": cmd_setup}[a.cmd](a)


if __name__ == "__main__":
    main()
