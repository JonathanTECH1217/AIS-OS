"""Shared helpers for the outreach list scripts (places_seed.py, qualify_sites.py).

Secrets loader order (the bridge between the two OSes, see references/credentials.md):
  1. <AIOS root>/.env                       (this repo's convention, gitignored)
  2. %USERPROFILE%/.monarc/secrets.env      (Monarc OS convention, shared by every repo on the machine)
  3. os.environ
Key names follow Monarc OS: GOOGLE_MAPS_API_KEY, ANTHROPIC_API_KEY.

Also: domain normalization, homepage fetch, address parsing, the LinkedIn company-list header,
the noon-ET local time table, and a CostMeter that refuses to cross the run's spend cap.
No third-party packages beyond `requests`.
"""
import csv
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
OUTREACH = ROOT / "projects" / "outreach"
AIOS_ENV = ROOT / ".env"
SECRETS_ENV = Path.home() / ".monarc" / "secrets.env"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")

# Exact header of LinkedIn's Account Match Template (fetched 2026-09-13). Changing any name fails the upload.
# Sample row in the template: LinkedIn,linkedin.com,linkedin.com,https://www.linkedin.com/company/linkedin/,MSFT,
#   Internet,Sunnyvale,California,US,94085  (state spelled out, country as US)
LINKEDIN_HEADER = ["companyname", "companywebsite", "companyemaildomain", "linkedincompanypageurl",
                   "stocksymbol", "industry", "city", "state", "companycountry", "zipcode"]

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado",
    "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky",
    "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota",
    "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

DMV_STATES = {"DC", "MD", "VA"}

# Local time when it is noon in New York, by state. Matches the values in Integrator_List_2026-09-05.xlsx.
_PACIFIC = {"CA", "WA", "OR", "NV"}
_MOUNTAIN = {"AZ", "CO", "UT", "NM", "ID", "MT", "WY"}
_CENTRAL = {"TX", "IL", "MN", "MO", "KS", "TN", "WI", "IA", "NE", "OK", "AR", "LA", "MS", "AL", "ND", "SD"}
_ALASKA = {"AK"}
_HAWAII = {"HI"}

ONEFIREFLY_RE = re.compile(r"one\s*firefly")
INTEGRATOR_RE = re.compile(r"(theat|smart home|automat|audio|video|integrat|control4|crestron|savant|lutron|"
                           r"sonos|josh\.ai|low voltage|lighting|shades?|cinema|hi-?fi|sound|\bav\b|a/v)")


# ---------------------------------------------------------------- secrets

def _read_env_file(path):
    env = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def load_env():
    """Merged view of the three sources. Earlier sources win. Also returns where each key came from."""
    merged, source = {}, {}
    for label, values in (("AIOS .env", _read_env_file(AIOS_ENV)),
                          ("secrets.env", _read_env_file(SECRETS_ENV)),
                          ("environment", dict(os.environ))):
        for k, v in values.items():
            if v and k not in merged:
                merged[k] = v
                source[k] = label
    return merged, source


def get_secret(name, required=False, hint=""):
    env, _ = load_env()
    val = env.get(name)
    if required and not val:
        sys.exit(f"{name} not found in {AIOS_ENV}, {SECRETS_ENV}, or the environment. {hint}".strip())
    return val


def report_key_sources(names):
    """Print which source answered for each key. Never prints values. Returns True if all present."""
    env, source = load_env()
    ok = True
    print(f"AIOS .env:   {'present' if AIOS_ENV.exists() else 'missing'}  ({AIOS_ENV})")
    print(f"secrets.env: {'present' if SECRETS_ENV.exists() else 'missing'}  ({SECRETS_ENV})")
    for n in names:
        if env.get(n):
            print(f"  {n}: found in {source[n]}")
        else:
            print(f"  {n}: MISSING")
            ok = False
    return ok


# ---------------------------------------------------------------- cost cap

class BudgetExceeded(Exception):
    pass


class CostMeter:
    """Tracks spend by line item and refuses to start work that would cross the cap."""

    def __init__(self, cap_usd, already_spent=None):
        self.cap = float(cap_usd) if cap_usd else None
        self.items = dict(already_spent or {})

    def add(self, item, usd):
        self.items[item] = round(self.items.get(item, 0.0) + float(usd), 4)

    @property
    def total(self):
        return round(sum(self.items.values()), 4)

    def assert_affordable(self, next_cost, item=""):
        if self.cap is not None and self.total + next_cost > self.cap:
            raise BudgetExceeded(
                f"{item or 'next step'} would cost about ${next_cost:.2f}; spent ${self.total:.2f} of the "
                f"${self.cap:.2f} cap. Raise --max-cost / SEED_BUDGET_USD or narrow the run.")

    def summary(self):
        return {"cap_usd": self.cap, "spent_usd": self.total, "by_item": dict(self.items)}


def budget_cap(env=None, override=None):
    if override is not None:
        return float(override)
    env = env if env is not None else load_env()[0]
    return float(env.get("SEED_BUDGET_USD", "200"))


# ---------------------------------------------------------------- strings

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


def clean_name(name):
    n = str(name or "").strip()
    for sep in (" - ", " | ", " – ", " — ", ": "):
        if sep in n and len(n.split(sep)[0]) >= 3:
            n = n.split(sep)[0].strip()
    return n


def parse_addr(addr):
    """'1300 Industrial Rd, San Carlos, CA 94070, USA' -> ('San Carlos', 'CA', '94070')."""
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
        else:
            m = re.match(r"^([A-Z]{2})$", parts[-1])
            if m:
                state = m.group(1)
                if len(parts) >= 2:
                    city = parts[-2]
    return city, state, zipc


def local_time_noon_et(state):
    s = (state or "").upper()
    if s in _PACIFIC:
        return "9:00 AM"
    if s in _MOUNTAIN:
        return "10:00 AM"
    if s in _CENTRAL:
        return "11:00 AM"
    if s in _ALASKA:
        return "8:00 AM"
    if s in _HAWAII:
        return "7:00 AM"
    return "12:00 PM"


def reviews_string(rating, count):
    if rating is None and not count:
        return ""
    r = f"{rating:g}" if isinstance(rating, (int, float)) else str(rating or "")
    return f"{r} ({int(count or 0)})".strip()


# ---------------------------------------------------------------- fetch

def fetch(url, timeout=(6, 15)):
    """GET the site, trying https then http (or the reverse). Returns (response, error)."""
    u = str(url).strip()
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u
    alts = [u, ("http://" + u[8:]) if u.lower().startswith("https://") else ("https://" + u[7:])]
    last_err = None
    for a in alts:
        try:
            r = requests.get(a, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.8"},
                             timeout=timeout, allow_redirects=True)
            if r.status_code < 400 and r.text:
                return r, None
            last_err = f"HTTP {r.status_code}"
        except Exception as e:  # noqa: BLE001
            last_err = type(e).__name__
    return None, last_err


# ---------------------------------------------------------------- output

def write_linkedin_csv(rows, path):
    """rows: dicts with Name, Website, Domain, City, State, Zip, and optionally LinkedIn (company page URL),
    Industry (LinkedIn's label), Stock (symbol, public companies only). Writes the Campaign Manager company list."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(LINKEDIN_HEADER)
        for r in rows:
            st = (r.get("State") or "").upper()
            dom = r.get("Domain") or norm_domain(r.get("Website"))
            # template sample uses the bare domain for companywebsite, so mirror it
            w.writerow([r.get("Name", ""), dom, dom, r.get("LinkedIn", "") or "", r.get("Stock", "") or "", r.get("Industry", "") or "",
                        r.get("City", ""), STATE_NAMES.get(st, st), "US", r.get("Zip", "")])
    return len(rows)


def newest(pattern, folder=OUTREACH):
    files = sorted(Path(folder).glob(pattern))
    return files[-1] if files else None
