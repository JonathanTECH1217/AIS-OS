"""Put the AV integrators into the Prospects call list (Contacts), right after the last call (Jonathan, 2026-10-01).

Usage: python scripts/integrators_to_call_list.py            dry run: counts and samples, writes nothing
       python scripts/integrators_to_call_list.py --write    add the fields and the rows

Jonathan: "place those into the call list ... directly below the last person I called ... until I exhaust the
integrator list, and then it'll be electricians and plumbers and HVAC." His pick: the 887 checked integrators first
(qualified-list-2026-09-11.csv, each site read and confirmed), then the rest of the national sweep
(meta-seed-2026-09-24-integrators.xlsx, one row per website from places-seed-2026-09-13.xlsx), best contact first
(grade A owner + email, B named email, C generic email, D phone only).

Airtable adds rows only at the bottom and its API cannot reorder a view, so the order rides on two new columns:
"Queue" (1, 2, 3 on the integrator rows) and "Call order", a formula: Queue rows sort just after the last call's
Company # (3270.00001, 3270.00002, ...), every other row sorts by its Company #. Sorting the grid by Call order puts
the integrators directly under Neely's Auto Electric (#3270) and the rest of the electricians, plumbers, and HVAC
after them. Also new: "Trade" (AV integrator on these rows) and "Owner" (the name and role the sweep found).

Left out: companies outside the US, closed ones, rows with no phone, and anyone already in Contacts (same website
or phone). September's integrator calls (the qualified-list.xlsx base) ride along in "notes"; a company that said
no, had a dead line, or was the wrong fit goes to the end of the checked block. Never prints a key.
"""
import csv
import re
import sys
import time
from pathlib import Path

import openpyxl
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import ROOT, load_env, norm_domain  # noqa: E402
from crm_server import Api  # noqa: E402  the call-word rules (call_outcome_from_text)

OUT = ROOT / "projects" / "outreach"
BASE, CONTACTS = "appPM1HmRfFlgA484", "tblGdourIuqa9onmp"
QUALIFIED_BASE, QUALIFIED_TABLE = "app0szjJtS3ecQCG4", "tbl4hyOi0SDLIce7c"
LAST_CALLED = 3270  # Neely's Auto Electric, 2026-09-30 12:26 pm ET
API = "https://api.airtable.com/v0"
US = set("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR "
         "PA RI SC SD TN TX UT VT VA WA WV WI WY".split())
GRADE_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
DEAD = {"Not interested", "Bad number", "Wrong vertical"}

env, _ = load_env()
S = requests.Session()
S.headers["Authorization"] = f"Bearer {env['AIRTABLE_API_KEY']}"


def call(method, url, **kw):
    for attempt in range(5):
        r = S.request(method, url, timeout=60, **kw)
        if r.status_code == 429:
            time.sleep(30)
            continue
        time.sleep(0.22)  # five requests a second at most
        return r
    return r


def list_all(base, table, fields):
    out, off = [], None
    while True:
        params = {"pageSize": 100, "fields[]": fields, **({"offset": off} if off else {})}
        j = call("GET", f"{API}/{base}/{table}", params=params).json()
        out += j.get("records", [])
        off = j.get("offset")
        if not off:
            return out


def digits(p):
    return re.sub(r"\D", "", str(p or ""))[-10:]


def sheet(path, name):
    ws = openpyxl.load_workbook(path, read_only=True)[name]
    it = ws.iter_rows(values_only=True)
    head = next(it)
    return [dict(zip(head, r)) for r in it]


def num(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def build():
    contacts = list_all(BASE, CONTACTS, ["Website", "Phone"])
    have_dom = {norm_domain(r["fields"].get("Website") or "") for r in contacts} - {""}
    have_tel = {digits(r["fields"].get("Phone")) for r in contacts} - {""}
    print(f"Contacts now: {len(contacts)} rows")

    places = sheet(OUT / "places-seed-2026-09-13.xlsx", "Integrators")
    by_dom = {}
    for p in places:
        d = norm_domain(str(p.get("Domain") or p.get("Website") or ""))
        if d:
            by_dom.setdefault(d, []).append(p)
    sweep = sheet(OUT / "meta-seed-2026-09-24-integrators.xlsx", "Seed")
    seed_by_dom = {norm_domain(str(r.get("Domain") or "")): r for r in sweep}

    # September's integrator calls, by website and by phone
    sept = {}
    for r in list_all(QUALIFIED_BASE, QUALIFIED_TABLE, ["Status", "Website", "Phone"]):
        words = (r["fields"].get("Status") or "").strip()
        if words:
            for k in (norm_domain(r["fields"].get("Website") or ""), digits(r["fields"].get("Phone"))):
                if k:
                    sept[k] = words

    rows, skipped = [], {"outside the US": 0, "closed": 0, "no phone": 0, "already in Contacts": 0}
    seen = set()

    def owner_of(seed):
        if not seed or not seed.get("Owner name"):
            return None
        return f"{seed['Owner name']}" + (f" ({seed['Owner role']})" if seed.get("Owner role") else "")

    def keep(dom, tel, state, status):
        if state not in US:
            skipped["outside the US"] += 1
            return False
        if status and status != "OPERATIONAL":
            skipped["closed"] += 1
            return False
        if not tel:
            skipped["no phone"] += 1
            return False
        if dom in have_dom or tel in have_tel or dom in seen or tel in seen:
            skipped["already in Contacts"] += 1
            return False
        seen.update({dom, tel})
        return True

    # block 1: the 887 checked, in the list's own order
    checked, checked_dead = [], []
    for q in csv.DictReader(open(OUT / "qualified-list-2026-09-11.csv", encoding="utf-8-sig")):
        dom, tel = norm_domain(q.get("Website") or ""), digits(q.get("Phone"))
        st = (q.get("State") or "").strip().upper()
        plist = by_dom.get(dom) or []
        status = next((p.get("Business status") for p in plist if p.get("Business status")), None)
        if not keep(dom, tel, st, status):
            continue
        seed = seed_by_dom.get(dom)
        words = sept.get(dom) or sept.get(tel) or (q.get("Status") or "").strip()
        f = {"Name": q["Name"], "City": q.get("City") or None, "State": st, "Zip": num(q.get("Zip")),
             "County": q.get("County") or None, "Local time at noon ET": q.get("Local time at noon ET") or None,
             "Rating": num(q.get("Rating")), "Review count": num(q.get("Review count")),
             "Reviews shown": str(q.get("Reviews shown")).strip().lower() in ("true", "yes", "1"),
             "Listings": num(q.get("Listings")), "Website": q.get("Website") or None, "Phone": q.get("Phone"),
             "Source": "cold", "Trade": "AV integrator", "Owner": owner_of(seed),
             "linkedin URL": (seed or {}).get("LinkedIn") or None, "Email": (seed or {}).get("Email 1") or None,
             "notes": f"Called in September: {words}"[:250] if words else "Checked integrator"}
        (checked_dead if words and Api.call_outcome_from_text(words) in DEAD else checked).append(f)
    # block 2: the rest of the sweep, best contact first
    rest = []
    for r in sweep:
        dom = norm_domain(str(r.get("Domain") or ""))
        if not dom or dom in seen:
            continue
        plist = by_dom.get(dom) or [{}]
        p = plist[0]
        tel = digits(r.get("Listing phone") or p.get("Phone"))
        st = str(r.get("State") or p.get("State") or "").strip().upper()
        if not keep(dom, tel, st, p.get("Business status")):
            continue
        rc = num(p.get("Review count"))
        f = {"Name": r.get("Name") or p.get("Name"), "City": r.get("City") or p.get("City") or None, "State": st,
             "Zip": num(r.get("Zip") or p.get("Zip")), "County": p.get("County") or None,
             "Local time at noon ET": p.get("Local Time @ 12pm ET") or None, "Rating": num(p.get("Rating")),
             "Review count": rc, "Reviews shown": bool(rc), "Listings": float(len(plist)) if plist != [{}] else None,
             "Website": f"https://{dom}/", "Phone": r.get("Listing phone") or p.get("Phone"), "Source": "cold",
             "Trade": "AV integrator", "Owner": owner_of(r), "linkedin URL": r.get("LinkedIn") or None,
             "Email": r.get("Email 1") or None, "notes": f"From the national sweep, not yet checked ({r.get('Grade')})"}
        rest.append((GRADE_ORDER.get(str(r.get("Grade") or "E")[:1], 9), f))
    rest = [f for _, f in sorted(rest, key=lambda x: x[0])]
    ordered = checked + checked_dead + rest
    for i, f in enumerate(ordered, start=1):
        f["Queue"] = i
        if f.get("Email") and not re.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", str(f["Email"]), re.I):
            f["Email"] = None
        if f.get("linkedin URL") and not str(f["linkedin URL"]).startswith("http"):
            f["linkedin URL"] = None
        for k in [k for k, v in f.items() if v in (None, "")]:
            del f[k]
    return ordered, len(checked), len(checked_dead), len(rest), skipped


def add_fields():
    have = {f["name"] for t in call("GET", f"{API}/meta/bases/{BASE}/tables").json()["tables"] if t["id"] == CONTACTS for f in t["fields"]}
    specs = [
        {"name": "Trade", "type": "singleSelect", "description": "The trade on the row (2026-10-01). Blank on the electrician list as imported.",
         "options": {"choices": [{"name": "AV integrator"}, {"name": "Electrician"}, {"name": "Plumber"}, {"name": "HVAC"}]}},
        {"name": "Owner", "type": "singleLineText", "description": "The owner's name and role, found on the company's own site (pattern matching, check before trusting)."},
        {"name": "Queue", "type": "number", "options": {"precision": 0},
         "description": "Call order of the integrators added 2026-10-01: 1 is called first. Blank on every other row."},
    ]
    for s in specs:
        if s["name"] not in have:
            r = call("POST", f"{API}/meta/bases/{BASE}/tables/{CONTACTS}/fields", json=s)
            print(f"field {s['name']}: {r.status_code} {r.text[:200] if r.status_code >= 300 else ''}")
    if "Call order" not in have:
        r = call("POST", f"{API}/meta/bases/{BASE}/tables/{CONTACTS}/fields", json={
            "name": "Call order", "type": "formula",
            "description": f"Sort the grid by this, 1 to 9. The integrators (Queue) sit right after the last call on 2026-09-30, #{LAST_CALLED}; every other row by its Company #.",
            "options": {"formula": f"IF({{Queue}}, {LAST_CALLED} + {{Queue}} / 100000, {{Company #}})"}})
        print(f"field Call order: {r.status_code} {r.text[:200] if r.status_code >= 300 else ''}")


def main():
    ordered, n_checked, n_dead, n_rest, skipped = build()
    print(f"integrators to add: {len(ordered)} = {n_checked} checked + {n_dead} checked but already turned down in September + {n_rest} from the sweep")
    print("left out:", skipped)
    for f in ordered[:2] + ordered[n_checked + n_dead:n_checked + n_dead + 2]:
        print("  sample:", {k: f[k] for k in ("Queue", "Name", "State", "Phone", "notes") if k in f}, "| owner:", bool(f.get("Owner")), "| email:", bool(f.get("Email")))
    if "--write" not in sys.argv:
        print("dry run: nothing written")
        return
    add_fields()
    made = 0
    for i in range(0, len(ordered), 10):
        chunk = [{"fields": f} for f in ordered[i:i + 10]]
        r = call("POST", f"{API}/{BASE}/{CONTACTS}", json={"records": chunk, "typecast": True})
        if r.status_code >= 300:
            print(f"stopped at Queue {ordered[i]['Queue']}: {r.status_code} {r.text[:300]}")
            break
        made += len(r.json().get("records", []))
        if made % 1000 < 10:
            print(f"  {made} added")
    print(f"added {made} of {len(ordered)}")


if __name__ == "__main__":
    main()
