"""Monarc CRM: local dashboard server over an Airtable base.

Run:  python scripts/crm_server.py            (opens http://127.0.0.1:8770; 8765 belongs to the Dictation Sheet)
      python scripts/crm_server.py --check    (key source, one meta read, record counts)
      python scripts/crm_server.py --probe    (one raw REST page per table, for references/airtable-api.md)
      python scripts/crm_server.py --instance <slug>   (reads projects/crm/instances/<slug>.json)

Why local: the page talks to Airtable through this process, so the personal access token stays in
%USERPROFILE%/.monarc/secrets.env (or the repo .env) and never reaches the browser. Key name: AIRTABLE_PAT.
Scopes: data.records:read, data.records:write, schema.bases:read, limited to the CRM base.

Local-first so the Airtable Free plan caps (1,000 records per base, about 1,000 API calls a month) hold:
  - the dial queue is the qualified CSV on disk; a Company record exists only once it is touched
  - every dial is appended to projects/outreach/dial-log.jsonl before any Airtable call
  - no-contact dials bump two fields on the Company instead of creating an Activity
  - the whole base is cached in memory (TTL 120 s) and every write is applied to the cache
  - a failed write is queued in projects/crm/outbox.jsonl and replayed on the next request

Without AIRTABLE_PAT the server still runs: the queue and the dial log work, writes go to the outbox,
and the Airtable-backed views show an empty state that says what is missing.

Stdlib plus `requests` (already used by outreach_common). Field names, not ids, on the REST calls;
they are documented in references/airtable-api.md and must not be renamed in Airtable.
"""
import argparse
import csv
import json
import mimetypes
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import webbrowser
from datetime import datetime, timedelta, date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote, quote
from zoneinfo import ZoneInfo

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import ROOT, OUTREACH, get_secret, load_env, norm_domain, newest  # noqa: E402
import crm_butterfly as butterfly  # noqa: E402  (the logo's menu: run a skill, new project, work on a project)
import crm_chat as chat  # noqa: E402  (the chat box: the clone, talked to from the CRM page)

CRM_DIR = ROOT / "projects" / "crm"
API = "https://api.airtable.com/v0"
TABLES = ("Companies", "People", "Deals", "Activities", "Sources", "Config", "Campaigns", "Keywords", "Landing pages", "Leads",
          "Listings", "LinkedIn threads", "Portfolio builds", "Free campaigns")
# Tables added after the first client copies: a base without one reads as empty instead of failing the load.
# Listings: the Google Organic "NAP citations" campaign (2026-09-27). LinkedIn threads: the LinkedIn channel's messaging
# medium, one row per person reached out to, loaded from LinkedIn's data export by scripts/linkedin_import.py (2026-09-28).
# Portfolio builds: the "Review Generation Farm" campaign's free builds, read for its tasks and outcomes (2026-09-29).
# Free campaigns: the "Free campaign for a review" deliveries, one row per company from Built to Review left, written by
# scripts/free_campaign.py (2026-10-03).
OPTIONAL_TABLES = {"Listings", "LinkedIn threads", "Portfolio builds", "Free campaigns"}
SAVE_FIELDS = {
    "LinkedIn threads": ("Outcome", "Notes"),  # the import owns the rest
    "Free campaigns": ("Stage", "Email", "Delivered on", "Ask due", "Ask sent on", "Review left on", "Notes"),
    "Listings": ("Directory", "Order", "Kind", "Status", "Listing URL", "Link", "NAP matches", "Live on", "Login email", "Notes",
                 "Campaign"),
    "Campaigns": ("Name", "Status", "Platform id", "Objective", "Daily budget", "Started", "Ended", "Spend to date",
                  "Impressions", "Clicks", "Notes", "Channel", "Outcomes", "Tasks"),
    "Keywords": ("Keyword", "Match type", "Status", "Impressions", "Clicks", "Spend to date", "Notes", "Campaign", "Landing page"),
    "Landing pages": ("URL", "Name", "Service", "Area", "Status", "Form fields", "Notes", "Campaign"),
    "Leads": ("Name", "When", "Email", "Phone", "Status", "First call at", "Call at", "Technicians", "UTM", "gclid", "Message",
              "External id", "Notes", "Company", "Source", "Campaign", "Keyword", "Landing page", "Deal"),
}
LINK_FIELDS = {"Channel", "Campaign", "Landing page", "Company", "Source", "Keyword", "Deal"}
CACHE_TTL = 120
STALE_BLOCK = 900  # past this a page waits for the pull rather than show old data (the CRM left idle), 2026-10-02
SHEET_TTL = 900  # call sheets in other bases (2026-09-26): one API call per pull, so pull at most every 15 min or on Refresh
MIN_GAP = 0.25

# Jonathan's own bookings are tests, never leads (Jonathan, 2026-10-02: "anything that's from me or gets sent to
# jonathan@monarcbuild.com is a no-go"). A Leads row from his addresses, any @monarcbuild.com address, or his phone is
# left out of every read, so it never becomes a deal, a company, an Outreach Log row, or a number on any page.
SELF_EMAILS = {"jonathan@monarcbuild.com", "jonathanbeach17@gmail.com", "sumreat17@gmail.com"}
SELF_DOMAINS = {"monarcbuild.com"}
SELF_PHONES = {"4438226004"}


def is_self(fields):
    email = (fields.get("Email") or "").strip().lower()
    phone = re.sub(r"\D", "", str(fields.get("Phone") or ""))[-10:]
    return email in SELF_EMAILS or email.rpartition("@")[2] in SELF_DOMAINS or (len(phone) == 10 and phone in SELF_PHONES)


mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("application/json", ".json")


# ---------------------------------------------------------------- config

def load_instance(slug):
    path = CRM_DIR / "config.json" if slug in (None, "", "monarc") else CRM_DIR / "instances" / f"{slug}.json"
    if not path.exists():
        sys.exit(f"No instance file at {path}")
    return json.loads(path.read_text(encoding="utf-8")), path


def company_key(website, phone):
    host = norm_domain(website)
    if "." in host:
        return host
    digits = re.sub(r"\D", "", phone or "")[-10:]
    return f"tel:{digits}" if len(digits) == 10 else ""


def person_key(name, email, phone, ckey):
    if email:
        return email.strip().lower()
    digits = re.sub(r"\D", "", phone or "")[-10:]
    if len(digits) == 10:
        return f"tel:{digits}"
    return f"{(name or '').strip().lower()}|{ckey}"


# ---------------------------------------------------------------- time

class Clock:
    def __init__(self, tzname):
        self.tz = ZoneInfo(tzname)

    def now(self):
        return datetime.now(self.tz)

    def today(self):
        return self.now().date()

    def iso_now(self):
        return self.now().isoformat(timespec="seconds")

    def week_start(self, d=None):
        d = d or self.today()
        return d - timedelta(days=d.weekday())

    def to_local(self, iso):
        """Airtable dateTime arrives as UTC ISO ('2026-09-15T16:00:00.000Z')."""
        if not iso:
            return None
        s = iso.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(s).astimezone(self.tz)
        except ValueError:
            return None


# ---------------------------------------------------------------- airtable

class AirtableError(Exception):
    def __init__(self, status, payload):
        super().__init__(f"Airtable {status}: {payload}")
        self.status = status
        self.payload = payload


class Airtable:
    def __init__(self, token, base_id):
        self.token = token
        self.base = base_id
        self.lock = threading.Lock()
        self.last = 0.0
        self.calls = 0
        self._local = threading.local()  # one HTTP session per thread, so table pulls can overlap (2026-10-02)

    @property
    def session(self):
        s = getattr(self._local, "session", None)
        if s is None:
            s = self._local.session = requests.Session()
            s.headers["Authorization"] = f"Bearer {self.token}"
        return s

    @property
    def ready(self):
        return bool(self.token)

    def _request(self, method, path, params=None, body=None, retry=True):
        if not self.token:
            raise AirtableError(0, {"error": "AIRTABLE_PAT missing"})
        # Requests start at most every MIN_GAP seconds (4 a second, under Airtable's 5 per base), but no longer wait for
        # each other to finish: the lock only books the start time (2026-10-02, the slow-render fix).
        with self.lock:
            now = time.time()
            start = max(now, self.last + MIN_GAP)
            self.last = start
            self.calls += 1
        if start > now:
            time.sleep(start - now)
        r = self.session.request(method, f"{API}/{path}", params=params, json=body, timeout=30)
        if r.status_code == 429 and retry:
            time.sleep(30)
            return self._request(method, path, params, body, retry=False)
        if r.status_code >= 400:
            try:
                payload = r.json()
            except ValueError:
                payload = {"error": r.text[:300]}
            raise AirtableError(r.status_code, payload)
        return r.json() if r.text else {}

    def meta(self):
        return self._request("GET", f"meta/bases/{self.base}/tables")

    def list_all(self, table, formula=None, fields=None, page_size=100, one_page=False):
        params = {"pageSize": page_size}
        if formula:
            params["filterByFormula"] = formula
        if fields:
            params["fields[]"] = fields
        out, offset = [], None
        while True:
            if offset:
                params["offset"] = offset
            data = self._request("GET", f"{self.base}/{table}", params=params)
            out.extend(data.get("records", []))
            offset = data.get("offset")
            if not offset or one_page:
                return out, data

    def create(self, table, records):
        created = []
        for i in range(0, len(records), 10):
            chunk = [{"fields": f} for f in records[i:i + 10]]
            data = self._request("POST", f"{self.base}/{table}", body={"records": chunk, "typecast": True})
            created.extend(data.get("records", []))
        return created

    def update(self, table, records):
        updated = []
        for i in range(0, len(records), 10):
            chunk = [{"id": rid, "fields": f} for rid, f in records[i:i + 10]]
            data = self._request("PATCH", f"{self.base}/{table}", body={"records": chunk, "typecast": True})
            updated.extend(data.get("records", []))
        return updated

    def delete(self, table, ids):
        for i in range(0, len(ids), 10):
            self._request("DELETE", f"{self.base}/{table}", params={"records[]": ids[i:i + 10]})


# ---------------------------------------------------------------- store

class Store:
    """Whole-base cache plus the CSV queue, the dial log, and the outbox."""

    def __init__(self, inst, air):
        self.inst = inst
        self.air = air
        self.tables = {t: {} for t in TABLES}
        self.loaded_at = 0.0
        self.lock = threading.RLock()  # held only while a pull swaps its tables in, and around cache writes
        self.refresh_lock = threading.Lock()  # one Airtable pull at a time (ensure, 2026-10-02)
        self._touched = None  # (table, record id) written during a pull in flight
        self._bg_failed = 0.0
        self.cfg = dict(inst.get("fallback_config", {}))
        self.cfg_source = "config.json"
        self.clock = Clock(self.cfg.get("timezone", "America/New_York"))
        # Verticals (Jonathan, 2026-09-24: "Lump companies by vertical, separate this list from the integrators"):
        # one call list per trade, each from its own CSV; a company carries its vertical in Airtable.
        self.verticals = inst.get("verticals") or [{"key": "integrator", "label": "Integrators", "airtable": "Integrator",
                                                    "queue_csv_glob": inst.get("queue_csv_glob", "qualified-list-*.csv")}]
        self.queue_paths = {v["key"]: newest(v["queue_csv_glob"]) for v in self.verticals}
        self.queues = {v["key"]: self._load_queue(self.queue_paths[v["key"]], v["key"]) for v in self.verticals}
        self.queue_path = self.queue_paths[self.verticals[0]["key"]]
        self.queue = self.queues[self.verticals[0]["key"]]
        # Every trade's list in one, numbered through (2026-10-03: the vertical switch left the rail, Jonathan did not
        # know what it was for, so Today's call list no longer shows one trade at a time).
        self.queue_all = []
        for v in self.verticals:
            for r in self.queues[v["key"]]:
                self.queue_all.append(dict(r, n=len(self.queue_all) + 1))
        self.dial_log_path = ROOT / inst.get("dial_log", "projects/outreach/dial-log.jsonl")
        self.outbox_path = ROOT / inst.get("outbox", "projects/crm/outbox.jsonl")
        self.last_error = None
        self._seed_fallback_sources()
        if not air.ready:
            self._apply_outbox_to_cache()

    def _seed_fallback_sources(self):
        """Offline: the Sources rows from config.json, keyed by name. typecast:true lets Airtable
        match a link by primary field, so a name in a link field replays cleanly."""
        if self.tables["Sources"]:
            return
        for s in self.inst.get("fallback_sources", []):
            self.tables["Sources"][s["name"]] = {"Name": s["name"], "Type": s.get("type", ""),
                                                 "Active": bool(s.get("active", True)),
                                                 "Daily budget": s.get("daily_budget", 0), "_fallback": True}

    def _apply_outbox_to_cache(self):
        """Offline restart: rebuild what the last session wrote so a redial finds its company."""
        for item in self._outbox_items():
            t, f = item["table"], dict(item["fields"])
            if item["op"] == "create" and item.get("local_id"):
                self.tables[t][item["local_id"]] = f
            elif item["op"] == "update" and item.get("id"):
                self.tables[t].setdefault(item["id"], {}).update(f)

    # ---- loading

    def vertical(self, key=None):
        """The vertical dict for a key; the first one when the key is blank or unknown."""
        for v in self.verticals:
            if v["key"] == key:
                return v
        return self.verticals[0]

    def vertical_label(self, key=None):
        return self.vertical(key)["airtable"]

    def queue_rows(self, key=None):
        """One trade's list for a key; every trade's list in one when the key is blank (2026-10-03)."""
        if key:
            return self.queues.get(self.vertical(key)["key"], [])
        return self.queue_all

    def queue_files(self):
        """The list files' names, one per trade that has one."""
        return [self.queue_paths[v["key"]].name for v in self.verticals if self.queue_paths[v["key"]]]

    def queue_row(self, company_key_):
        """The list row for a company key, whichever vertical's list it sits on."""
        for rows in self.queues.values():
            for r in rows:
                if r["key"] == company_key_:
                    return r
        return None

    def _load_queue(self, path, vertical="integrator"):
        rows = []
        if not path:
            return rows
        with open(path, encoding="utf-8-sig", newline="") as fh:
            for i, r in enumerate(csv.DictReader(fh)):
                key = company_key(r.get("Website"), r.get("Phone"))
                rows.append({
                    "n": i + 1, "key": key, "vertical": vertical, "name": r.get("Name", "").strip(),
                    "city": r.get("City", ""), "state": r.get("State", ""), "county": r.get("County", ""),
                    "phone": r.get("Phone", ""), "local_time": r.get("Local time at noon ET", ""),
                    "rating": r.get("Rating", ""), "reviews": r.get("Review count", ""),
                    "website": r.get("Website", ""), "csv_status": r.get("Status", "").strip(),
                    "source": r.get("Source", "cold") or "cold",
                })
        return rows

    def ensure(self, force=False):
        """Keep the cache fresh without making a page wait (Jonathan, 2026-10-02: "the CRM takes a really long time to
        render"). Up to CACHE_TTL old: served as is. Older than that but under STALE_BLOCK: served as is while a
        background refresh pulls Airtable, so the next page has it. The first load, Refresh, or a cache older than
        STALE_BLOCK (the CRM left idle) waits for the pull, which now fetches the tables side by side."""
        if not self.air.ready:
            return
        age = time.time() - self.loaded_at
        if force or not self.loaded_at or age > STALE_BLOCK:
            with self.refresh_lock:  # a background pull in flight finishes first; then pull only if still needed
                if force or not self.loaded_at or time.time() - self.loaded_at > STALE_BLOCK:
                    self._reload()
            return
        if age > CACHE_TTL:
            self._refresh_in_background()

    def _refresh_in_background(self):
        if time.time() - self._bg_failed < 30 or not self.refresh_lock.acquire(blocking=False):
            return

        def run():
            try:
                self._reload()
            except Exception as e:  # noqa: BLE001  the old data stays; the next request tries again after 30 s
                self._bg_failed = time.time()
                self.last_error = f"Background refresh: {str(e)[:200]}"
            finally:
                self.refresh_lock.release()
        threading.Thread(target=run, daemon=True).start()

    def _touch(self, table, rid):
        """A write during a pull: the cache keeps this record as written rather than the pull's older copy."""
        t = self._touched
        if t is not None:
            t.add((table, rid))

    def _reload(self):
        started = time.time()
        self._touched = set()
        try:
            self.replay_outbox()

            def pull(t):
                try:
                    recs, _ = self.air.list_all(t)
                except AirtableError:
                    if t not in OPTIONAL_TABLES:
                        raise
                    recs = []
                return t, {r["id"]: r["fields"] for r in recs}
            with ThreadPoolExecutor(max_workers=4) as ex:
                fresh = dict(ex.map(pull, TABLES))
            with self.lock:
                for t, rows in fresh.items():
                    for tt, rid in self._touched:
                        if tt == t and rid in self.tables[t]:
                            rows[rid] = self.tables[t][rid]
                    self.tables[t] = rows
                self.loaded_at = started
                self._read_config()
        finally:
            self._touched = None

    def _read_config(self):
        rows = self.tables.get("Config", {})
        if not rows:
            return
        cfg = dict(self.inst.get("fallback_config", {}))
        for f in rows.values():
            k, v = f.get("Key"), f.get("Value")
            if k and v:
                try:
                    cfg[k] = json.loads(v)
                except ValueError:
                    cfg[k] = v
        self.cfg = cfg
        self.cfg_source = "Airtable Config"
        self.clock = Clock(cfg.get("timezone", "America/New_York"))

    # ---- config helpers

    def stages(self):
        return self.cfg.get("stages", [])

    def stage(self, name):
        return next((s for s in self.stages() if s["name"] == name), None)

    def outcome(self, name):
        return next((o for o in self.cfg.get("dial_outcomes", []) if o["name"] == name), None)

    def numbers(self):
        return self.cfg.get("numbers", {})

    # ---- lookups

    def rec(self, table, rid):
        f = self.tables[table].get(rid)
        return dict(f, id=rid) if f is not None else None

    def rows(self, table):
        if table == "Leads":  # Jonathan's own test bookings are never leads (is_self, 2026-10-02)
            return [dict(f, id=rid) for rid, f in self.tables[table].items() if not is_self(f)]
        return [dict(f, id=rid) for rid, f in self.tables[table].items()]

    def find(self, table, field, value):
        for rid, f in self.tables[table].items():
            if f.get(field) == value:
                return dict(f, id=rid)
        return None

    def source_id(self, name):
        s = self.find("Sources", "Name", name) or self.find("Sources", "Name", "cold")
        return s["id"] if s else None

    def open_deal(self, company_id):
        for d in self.rows("Deals"):
            if company_id in (d.get("Company") or []) and not d.get("Closed"):
                return d
        return None

    def record_total(self):
        return sum(len(v) for v in self.tables.values())

    # ---- writes (write-through)

    _seq = 0

    def _local_id(self):
        Store._seq += 1
        return f"local:{int(time.time() * 1000)}-{Store._seq}"

    def _local_create(self, table, fields):
        fake = self._local_id()
        self.queue_write("create", table, fields, local_id=fake)
        with self.lock:
            self.tables[table][fake] = fields
            self._touch(table, fake)
        return dict(fields, id=fake)

    def create(self, table, fields):
        if not self.air.ready or self.outbox_size():
            # keep order: once anything is queued, later writes queue too, so links resolve on replay
            return self._local_create(table, fields)
        try:
            rec = self.air.create(table, [fields])[0]
        except AirtableError as e:
            self.last_error = str(e)
            if e.status in (0, 429, 500, 502, 503):
                return self._local_create(table, fields)
            raise
        with self.lock:
            self.tables[table][rec["id"]] = rec["fields"]
            self._touch(table, rec["id"])
        return dict(rec["fields"], id=rec["id"])

    def cache_merge(self, table, rid, fields):
        """Fold written fields into the cached record (and keep them through a pull in flight)."""
        with self.lock:
            self.tables[table].setdefault(rid, {}).update(fields)
            self._touch(table, rid)

    def update(self, table, rid, fields):
        if rid.startswith("local:") or not self.air.ready or self.outbox_size():
            self.queue_write("update", table, fields, rid)
            self.cache_merge(table, rid, fields)
            return self.rec(table, rid)
        try:
            rec = self.air.update(table, [(rid, fields)])[0]
        except AirtableError as e:
            self.last_error = str(e)
            if e.status in (0, 429, 500, 502, 503):
                self.queue_write("update", table, fields, rid)
                self.cache_merge(table, rid, fields)
                return self.rec(table, rid)
            raise
        with self.lock:
            self.tables[table][rec["id"]] = rec["fields"]
            self._touch(table, rec["id"])
        return dict(rec["fields"], id=rec["id"])

    def queue_write(self, op, table, fields, rid=None, local_id=None):
        self.outbox_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.outbox_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"op": op, "table": table, "id": rid, "local_id": local_id, "fields": fields,
                                 "at": self.clock.iso_now()}, ensure_ascii=False) + "\n")

    def _outbox_items(self):
        if not self.outbox_path.exists():
            return []
        out = []
        for ln in self.outbox_path.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                try:
                    out.append(json.loads(ln))
                except ValueError:
                    pass
        return out

    def replay_outbox(self):
        """Replay queued writes in order, mapping local ids to the real ids Airtable hands back.
        Stops at the first failure so order is kept; the rest waits for the next request."""
        if not self.air.ready:
            return 0
        items = self._outbox_items()
        if not items:
            return 0
        idmap = {}

        def fix(v):
            if isinstance(v, list):
                return [idmap.get(x, x) for x in v if not (str(x).startswith("local:") and x not in idmap)]
            return v

        done = 0
        for item in items:
            fields = {k: fix(v) for k, v in item["fields"].items()}
            fields = {k: v for k, v in fields.items() if v not in ([], None)}
            try:
                if item["op"] == "create":
                    rec = self.air.create(item["table"], [fields])[0]
                    if item.get("local_id"):
                        idmap[item["local_id"]] = rec["id"]
                else:
                    rid = idmap.get(item["id"], item["id"])
                    if rid and not rid.startswith("local:"):
                        self.air.update(item["table"], [(rid, fields)])
                done += 1
            except AirtableError as e:
                self.last_error = f"outbox replay stopped at item {done + 1}: {e}"
                break
        rest = items[done:]
        self.outbox_path.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in rest), encoding="utf-8")
        return done

    def outbox_size(self):
        return len(self._outbox_items())

    # ---- dial log

    def append_dial(self, entry):
        self.dial_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.dial_log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def dials(self):
        if not self.dial_log_path.exists():
            return []
        out = []
        for ln in self.dial_log_path.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                try:
                    out.append(json.loads(ln))
                except ValueError:
                    pass
        return out


def s_rows_snapshot(store, table):
    """A stable list to iterate while writes update the cache underneath."""
    return list(store.rows(table))


# ---------------------------------------------------------------- business rules

class Rules:
    def __init__(self, store):
        self.s = store

    def validate_deal(self, f, partial=False):
        """Messages the form and the API both show. Empty list means valid."""
        s = self.s
        msgs = []
        stage = s.stage(f.get("Stage") or "")
        if not stage:
            msgs.append("Pick a stage.")
        if f.get("Value") in (None, "") or (isinstance(f.get("Value"), str) and not f["Value"].strip()):
            msgs.append("Every deal has a dollar value.")
        if not f.get("Close date"):
            msgs.append("Every deal has a close date.")
        if not f.get("Source"):
            msgs.append("Every deal has a source.")
        if stage and stage.get("closed"):
            if not f.get("Close reason"):
                msgs.append("A closed deal needs a reason.")
        elif stage:
            if not (f.get("Next action") or "").strip():
                msgs.append("An open deal needs a next action.")
            if not f.get("Next action date"):
                msgs.append("The next action needs a date.")
            if not (f.get("Owner") or "").strip():
                msgs.append("The next action needs an owner.")
        return msgs

    def stamp_closed(self, f):
        stage = self.s.stage(f.get("Stage") or "")
        f["Closed"] = bool(stage and stage.get("closed"))
        f["Won"] = bool(stage and stage.get("won"))
        if not f["Closed"]:
            f.pop("Close reason", None)
        return f


# ---------------------------------------------------------------- api

class Api:
    def __init__(self, store):
        self.s = store
        self.rules = Rules(store)
        self.sheet_cache = {}   # (base, table) -> {"at": epoch, "rows": [...], "error": str | None}
        self.sheet_clients = {}  # (token name, base) -> Airtable

    # ---- reads

    def health(self):
        s = self.s
        env, src = load_env()
        counts = {t: len(v) for t, v in s.tables.items()}
        return {
            "instance": s.inst.get("label", s.inst.get("instance")),
            "base_id": s.inst["base_id"], "base_url": s.inst.get("base_url"),
            "pat_source": src.get("AIRTABLE_PAT") if env.get("AIRTABLE_PAT") else None,
            "airtable_ready": s.air.ready,
            "queue_file": ", ".join(s.queue_files()) or None, "queue_rows": len(s.queue_all),
            "queues": [{"key": v["key"], "label": v["label"], "file": s.queue_paths[v["key"]].name if s.queue_paths[v["key"]] else None,
                        "rows": len(s.queues[v["key"]])} for v in s.verticals],
            "counts": counts, "records": s.record_total(),
            "record_cap": s.numbers().get("record_cap", 1000), "record_warn": s.numbers().get("record_warn", 850),
            "cache_age": int(time.time() - s.loaded_at) if s.loaded_at else None,
            "api_calls": s.air.calls, "outbox": s.outbox_size(), "last_error": s.last_error,
            "config_source": s.cfg_source, "now": s.clock.iso_now(), "today": s.clock.today().isoformat(),
        }

    def config(self):
        return dict(self.s.cfg, sources=[{"id": r["id"], "name": r.get("Name"), "type": r.get("Type"),
                                          "active": bool(r.get("Active")), "daily_budget": r.get("Daily budget", 0)}
                                         for r in self.s.rows("Sources")],
                    verticals=[{"key": v["key"], "label": v["label"], "airtable": v["airtable"]} for v in self.s.verticals])

    def _company_vertical(self, c):
        """A company's vertical key. Blank in Airtable reads as the first vertical (the integrators)."""
        name = (c or {}).get("Vertical") or ""
        for v in self.s.verticals:
            if v["airtable"] == name:
                return v["key"]
        return self.s.verticals[0]["key"]

    def company_state(self):
        return {f.get("Key"): dict(f, id=rid) for rid, f in self.s.tables["Companies"].items() if f.get("Key")}

    def queue(self, limit=22, q="", everything=False, vertical=None):
        s = self.s
        today = s.clock.today()
        redial = int(s.numbers().get("redial_days", 3))
        state = self.company_state()
        dialed_today = {d.get("key") for d in s.dials() if d.get("at", "")[:10] == today.isoformat()}
        # Dials today (2026-09-29): the calls typed in the Airtable call sheet today, plus any logged here, each company
        # once. Jonathan logs his calls in Airtable, so the count reflects the sheet; a company called there today also
        # drops off the list below.
        sheet = self.sheet_today()
        sheet_keys = {r["key"] or r["name"] for r in sheet["rows"] if r["kind"] == "dial"}
        called = dialed_today | sheet_keys
        out, ql = [], (q or "").lower()
        for row in s.queue_rows(vertical):
            c = state.get(row["key"])
            item = dict(row)
            if c:
                deal = s.open_deal(c["id"])
                item.update(company_id=c["id"], attempts=c.get("Dial attempts", 0), last_dial=c.get("Last dial"),
                            stage=deal.get("Stage") if deal else None, phase=c.get("Phase"), closed=any(
                                d.get("Closed") for d in s.rows("Deals") if c["id"] in (d.get("Company") or [])))
            else:
                item.update(company_id=None, attempts=0, last_dial=None, stage=None, phase=None, closed=False)
            item["dialed_today"] = row["key"] in called
            if ql and ql not in (row["name"] + " " + row["city"] + " " + row["state"] + " " + row["phone"]).lower():
                continue
            if not everything:
                if not row["phone"] or item["closed"] or item["dialed_today"]:
                    continue
                if item["stage"] and item["stage"] not in ("Cold", "Contacted"):
                    continue
                if item["last_dial"]:
                    try:
                        if (today - date.fromisoformat(item["last_dial"])).days < redial:
                            continue
                    except ValueError:
                        pass
            out.append(item)
            if not everything and limit and len(out) >= limit:
                break
        # no vertical asked (the usual case since 2026-10-03): every trade's list in one
        v = s.vertical(vertical) if vertical else None
        return {"rows": out, "dialed_today": len(called), "dialed_in_crm": len(dialed_today), "sheet_today": sheet,
                "target": s.numbers().get("dials_per_day", 22),
                "vertical": v["key"] if v else None, "vertical_label": v["label"] if v else "All trades",
                "list_rows": len(s.queue_rows(vertical)),
                "list_file": (s.queue_paths[v["key"]].name if s.queue_paths[v["key"]] else None) if v else (", ".join(s.queue_files()) or None),
                "campaign": self.campaign_tally()}

    def companies(self, q="", vertical=None):
        s = self.s
        ql = (q or "").lower()
        out = []
        for c in s.rows("Companies"):
            if vertical and self._company_vertical(c) != s.vertical(vertical)["key"]:
                continue
            if ql and ql not in (str(c.get("Name", "")) + " " + str(c.get("City", "")) + " " + str(c.get("State", ""))).lower():
                continue
            deal = s.open_deal(c["id"])
            people = sum(1 for p in s.tables["People"].values() if c["id"] in (p.get("Company") or []))
            phase, nch = self.phase_for(c["id"])
            out.append(dict(c, stage=deal.get("Stage") if deal else None, deal_id=deal["id"] if deal else None,
                            people=people, source_name=self._source_name(c), phase_calc=phase, channels=nch))
        out.sort(key=lambda c: (c.get("Last touch") or c.get("Created") or ""), reverse=True)
        return out

    def _source_name(self, rec):
        ids = rec.get("Source") or []
        src = self.s.rec("Sources", ids[0]) if ids else None
        return src.get("Name") if src else None

    def bundle(self, company_id):
        s = self.s
        c = s.rec("Companies", company_id)
        if not c:
            return None
        people = [dict(p, source_name=self._source_name(p)) for p in s.rows("People") if company_id in (p.get("Company") or [])]
        deals = [dict(d, source_name=self._source_name(d)) for d in s.rows("Deals") if company_id in (d.get("Company") or [])]
        acts = [a for a in s.rows("Activities") if company_id in (a.get("Company") or [])]
        acts.sort(key=lambda a: a.get("When") or "", reverse=True)
        queue_row = s.queue_row(c.get("Key"))
        phase, nch = self.phase_for(company_id)
        return {"company": dict(c, source_name=self._source_name(c), phase_calc=phase, channels=nch), "people": people,
                "deals": deals, "activities": acts, "queue": queue_row}

    # ---- the company file (2026-10-04, Jonathan: "when I search for a company, it displays me a neatly organized
    # file": the contacts made with it, the key people spoken with, and a triage of what he still owes it; his example,
    # a meeting booked on a call and the Loom brief not sent yet). One page for a company in the CRM or one that only
    # exists in the Prospects call list (id "mb:MB-00258"). Sources: the CRM (people, deals, activities, leads, LinkedIn
    # threads, free campaigns), the Prospects base (the Contacts row and its Outreach Log rows, two calls, kept 15
    # minutes), the call-note files Monarc Calls writes, and (asked for after the page draws) Proton mail to and from
    # the company. The triage: the steps of the stage the company is in (projects/crm/playbook.json, his to edit), the
    # flags the CRM reads itself, and his own to-dos. Ticks live in projects/crm/triage.json by company key, so they
    # hold before and after the company is added to the CRM. Everything else here is read only.

    PLAYBOOK = CRM_DIR / "playbook.json"
    TRIAGE = CRM_DIR / "triage.json"
    PROSPECT_FIELDS = ["Name", "City", "State", "Phone", "Website", "Vertical", "Email", "Owner", "Status (typed)",
                       "Status changed", "Company ID", "notes", "Local time at noon ET", "Rating", "Review count", "linkedin URL"]
    BOARD_STAGES = ("Booked", "Held", "Proposed", "Won")  # the stages whose open steps show under "Waiting on you"
    _triage_lock = threading.Lock()
    _prospect_cache = {}
    _file_mail = {}

    def _prospects(self):
        if not get_secret("AIRTABLE_API_KEY"):
            return None
        key = ("AIRTABLE_API_KEY", self.OUTREACH["base"])
        client = self.sheet_clients.get(key)
        if not client:
            client = self.sheet_clients[key] = Airtable(get_secret("AIRTABLE_API_KEY"), self.OUTREACH["base"])
        return client if client.ready else None

    @staticmethod
    def _cached(key, fn, ttl=SHEET_TTL):
        hit = Api._prospect_cache.get(key)
        if hit and time.time() - hit[0] < ttl:
            return hit[1]
        val = fn()
        Api._prospect_cache[key] = (time.time(), val)
        return val

    @staticmethod
    def _one(v):
        return v[0] if isinstance(v, list) and v else v

    def _when_et(self, iso):
        d = self.s.clock.to_local(iso) if iso else None
        return d.strftime("%a %b %d, %I:%M %p ET").replace(" 0", " ") if d else ""

    def _prospect_shape(self, rec):
        f, one = rec["fields"], self._one
        website, phone = str(f.get("Website") or "").strip(), str(f.get("Phone") or "").strip()
        typed = (f.get("Status (typed)") or "").strip()
        o = self.OUTREACH
        return {"rec": rec["id"], "mb": f.get("Company ID") or "", "name": (f.get("Name") or "").strip(),
                "city": one(f.get("City")) or "", "state": one(f.get("State")) or "", "phone": phone, "website": website,
                "key": company_key(website, phone), "vertical": one(f.get("Vertical")) or "",
                "email": (f.get("Email") or "").strip(), "owner": (f.get("Owner") or "").strip(), "typed": typed,
                "outcome": self.call_outcome_from_text(typed), "changed": f.get("Status changed"),
                "notes": (f.get("notes") or "").strip(), "local_noon": one(f.get("Local time at noon ET")) or "",
                "rating": f.get("Rating"), "reviews": f.get("Review count"), "linkedin": f.get("linkedin URL") or "",
                "url": f"https://airtable.com/{o['base']}/{o['contacts']}/{rec['id']}"}

    def prospect_row(self, mb=None, key=None, phone=None):
        """The company's row in the Prospects call list: by its MB ID, else by the website's domain or the phone."""
        client = self._prospects()
        if not client:
            return None
        dom, digits = "", ""
        if mb:
            if not re.fullmatch(r"MB-\d{1,7}", mb):
                return None
            formula = f"{{Company ID}}='{mb}'"
        else:
            digits = re.sub(r"\D", "", phone or "")[-10:]
            if key and key.startswith("tel:"):
                digits = digits or key[4:]
            elif key and "." in key:
                dom = key
            conds = []
            if len(digits) == 10:
                conds.append(f'RIGHT(REGEX_REPLACE({{Phone}}&"", "[^0-9]", ""), 10)="{digits}"')
            if dom and '"' not in dom:
                conds.append(f'FIND("{dom}", LOWER({{Website}}&""))')
            if not conds:
                return None
            formula = "OR(" + ",".join(conds) + ")"

        def pull():
            recs = client.list_all(self.OUTREACH["contacts"], formula=formula, fields=self.PROSPECT_FIELDS, page_size=10, one_page=True)[0]
            rows = [self._prospect_shape(r) for r in recs]
            if mb:
                return rows[0] if rows else None
            # the same domain or the same phone, exactly (FIND also matches a longer address that holds this one)
            for r in rows:
                if (dom and norm_domain(r["website"]) == dom) or (len(digits) == 10 and re.sub(r"\D", "", r["phone"])[-10:] == digits):
                    return r
            return None
        try:
            return self._cached(("row", mb or key or digits), pull)
        except (AirtableError, requests.RequestException) as e:
            self.s.last_error = f"Prospects: {str(e)[:160]}"
            return None

    def prospect_log(self, mb):
        """The Outreach Log rows for one company: every dial Monarc Calls logged, form fills, and typed touchpoints."""
        client = self._prospects()
        if not client or not mb:
            return []

        def pull():
            formula = f"OR({{Company ID}}='{mb}', FIND('{mb}', ARRAYJOIN({{MB ID}})&''))"
            recs = client.list_all(self.OUTREACH["log"], formula=formula,
                                   fields=["Company ID", "Channel", "Day", "Person", "Role", "Direction", "Touchpoint #", "Transcript"])[0]
            return [dict(r["fields"], id=r["id"], created=r.get("createdTime")) for r in recs]
        try:
            return self._cached(("log", mb), pull)
        except (AirtableError, requests.RequestException) as e:
            self.s.last_error = f"Outreach Log: {str(e)[:160]}"
            return []

    def prospect_search(self, q):
        """Companies in the Prospects call list by name, for the search box: most of the 15,000 are not in the CRM."""
        q = re.sub(r'["\\]', "", (q or "").strip().lower())
        client = self._prospects()
        if len(q) < 3 or not client:
            return []

        def pull():
            recs = client.list_all(self.OUTREACH["contacts"], formula=f'SEARCH("{q}", LOWER({{Name}}&""))',
                                   fields=self.PROSPECT_FIELDS, page_size=15, one_page=True)[0]
            return [self._prospect_shape(r) for r in recs]
        try:
            rows = self._cached(("search", q), pull, ttl=120)
        except (AirtableError, requests.RequestException) as e:
            self.s.last_error = f"Prospects search: {str(e)[:160]}"
            return []
        state = self.company_state()
        return [dict(r, crm_id=(state.get(r["key"]) or {}).get("id") if r["key"] else None) for r in rows]

    def _playbook(self):
        try:
            return json.loads(self.PLAYBOOK.read_text(encoding="utf-8")).get("stages", {})
        except (OSError, ValueError):
            return {}

    def _triage_all(self):
        try:
            return json.loads(self.TRIAGE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"_about": "Ticks and to-dos per company for the CRM's company file (2026-10-04). Keyed by the company key "
                              "(website domain, else tel:<10 digits>, else mb:<MB ID>). Written by the CRM; steps come from playbook.json.",
                    "companies": {}}

    def _file_stage(self, deals, prospect):
        """Where the company stands: its open deal's stage, else its last deal's, else what the call sheet says."""
        open_deal = next((d for d in deals if not d.get("Closed")), None)
        if open_deal:
            return open_deal.get("Stage") or "Cold", "the deal on the board"
        if deals:
            return sorted(deals, key=lambda d: d.get("Stage changed") or "")[-1].get("Stage") or "Lost", "the closed deal"
        out = (prospect or {}).get("outcome")
        if out == "Booked":
            return "Booked", "the call sheet"
        if out == "Not interested":
            return "Lost", "the call sheet"
        if out in self._contact_outcomes():
            return "Contacted", "the call sheet"
        return "Cold", "the call sheet" if out else "nothing logged yet"

    def _meeting_for(self, deals, leads, acts):
        """The meeting on file, if any: a site booking's call time, the deal's "Hold the call" line, or a Meeting activity."""
        times = sorted(l.get("Call at") for l in leads if l.get("Call at"))
        if times:
            return {"at": times[-1], "text": self._when_et(times[-1]), "from": "the site booking"}
        d = next((d for d in deals if not d.get("Closed")
                  and re.match(r"(?i)\s*(hold the|audit call|call with|meeting|consultation|kickoff)\b", d.get("Next action") or "")), None)
        if d:
            return {"at": d.get("Next action date"), "text": d.get("Next action"), "from": "the deal's next action"}
        m = next((a for a in acts if a.get("Type") == "Meeting"), None)
        if m:
            return {"at": m.get("When"), "text": m.get("Summary") or self._when_et(m.get("When")), "from": "the activity log"}
        return None

    @staticmethod
    def _step_seen(st, ctx):
        """What the CRM can see for itself, so he does not tick it: a step's "auto" rule in playbook.json."""
        rule = st.get("auto")
        if rule == "has_person" and ctx.get("people"):
            return "someone is on the record"
        if rule == "has_next_action":
            d = ctx.get("open_deal") or {}
            if (d.get("Next action") or "").strip() and (d.get("Next action date") or "") >= ctx.get("today", ""):
                return f"next action set for {d.get('Next action date')}"
        if rule == "has_meeting" and ctx.get("meeting"):
            return f"on file: {ctx['meeting'].get('text') or ctx['meeting'].get('at')}"
        return ""

    def _flags(self, stage, ctx):
        """What needs him that no step covers: an overdue or missing next action, a booked call that is not on the board,
        a callback typed in the sheet, no email address to send anything to."""
        flags, d = [], ctx.get("open_deal")
        today = ctx.get("today", "")
        if d and ctx.get("meeting") and d.get("Stage") in ("Cold", "Contacted"):
            flags.append({"id": "flag:move-booked", "act": "deal",
                          "text": f"A meeting is on file but the deal on the board still says {d.get('Stage')}. Move it to Booked."})
        if d:
            if not (d.get("Next action") or "").strip():
                flags.append({"id": "flag:no-next", "text": "The deal has no next action.", "act": "deal"})
            elif (d.get("Next action date") or "") < today:
                flags.append({"id": "flag:overdue", "act": "deal",
                              "text": f"Next action overdue since {d.get('Next action date')}: {d.get('Next action')}"})
        elif stage in ("Booked", "Contacted") and not ctx.get("in_crm"):
            flags.append({"id": "flag:not-in-crm", "act": "add",
                          "text": ("Booked in the call sheet but not on the board." if stage == "Booked" else
                                   "Contacted in the call sheet but not in the CRM.") + " Add the company and a deal so it is tracked."})
        elif stage in ("Booked", "Contacted") and not ctx.get("deals"):
            flags.append({"id": "flag:no-deal", "text": "No deal on the board for this company.", "act": "new-deal"})
        p = ctx.get("prospect") or {}
        if p.get("outcome") == "Callback":
            flags.append({"id": "flag:callback", "text": f"Call back. The sheet says: \"{p.get('typed')}\"", "act": "sheet"})
        if stage not in ("Cold", "Lost") and not ctx.get("emails"):
            flags.append({"id": "flag:no-email", "text": "No email address on file for anyone here.", "act": "person"})
        return flags

    def _triage_for(self, tkey, stage, ctx):
        """One company's to-do list: the stage's steps (ticked by him or seen by the CRM), the flags, his own to-dos."""
        saved = (self._triage_all().get("companies") or {}).get(tkey) or {}
        done, answers = saved.get("done") or {}, saved.get("answers") or {}
        steps = []
        for st in self._playbook().get(stage) or []:
            sid = f"{stage}:{st['id']}"
            # a step with "when" shows only after another step got that answer (the no-show steps, 2026-10-05)
            when = st.get("when") or {}
            if when and answers.get(f"{stage}:{when.get('step')}") != when.get("answer"):
                continue
            seen = self._step_seen(st, ctx)
            steps.append({"id": sid, "text": st["text"], "why": st.get("why", ""), "doc": st.get("doc", ""),
                          "done": sid in done or bool(seen), "done_on": done.get(sid) if isinstance(done.get(sid), str) else None,
                          "seen": seen, "mail_body": st.get("mail_body", ""), "mail_sent": bool(st.get("mail_sent")),
                          "ask": st.get("ask") or [], "answer": answers.get(sid) or ""})
        custom = [dict(c) for c in saved.get("custom") or []]
        flags = self._flags(stage, ctx)
        open_n = sum(1 for x in steps if not x["done"]) + sum(1 for c in custom if not c.get("done")) + len(flags)
        return {"stage": stage, "steps": steps, "custom": custom, "flags": flags, "open": open_n}

    def company_file(self, raw_id):
        s = self.s
        raw_id = str(raw_id or "")
        prospect, b = None, None
        if raw_id.startswith("mb:"):
            prospect = self.prospect_row(mb=raw_id[3:])
            if not prospect:
                return None
            c = self.company_state().get(prospect["key"]) if prospect["key"] else None
            if c:
                return {"redirect": c["id"]}
        else:
            b = self.bundle(raw_id)
            if not b:
                return None
            prospect = self.prospect_row(key=b["company"].get("Key"), phone=b["company"].get("Phone"))
        company = b["company"] if b else None
        deals = b["deals"] if b else []
        people_crm = b["people"] if b else []
        acts = b["activities"] if b else []
        cid = company["id"] if company else None
        p = prospect or {}
        mb = p.get("mb") or ""
        log_rows = self.prospect_log(mb) if mb else []
        leads = [l for l in s.rows("Leads") if cid and cid in (l.get("Company") or [])]
        threads = [t for t in s.rows("LinkedIn threads") if cid and cid in (t.get("Company") or [])]
        frees = [f for f in s.rows("Free campaigns") if (cid and cid in (f.get("Company") or [])) or (mb and f.get("MB ID") == mb)]
        tkey = (company or {}).get("Key") or p.get("key") or (f"mb:{mb}" if mb else raw_id)

        # ---- the people: the CRM's, then every name the other records hold
        people = {}

        def person(name, role="", email="", phone="", src="", last=None, crm=None, touch=False):
            name = re.sub(r"\s+", " ", str(name or "")).strip()
            if not name:
                return
            row = people.setdefault(name.lower(), {"name": name, "role": "", "email": "", "phone": "", "sources": [],
                                                   "touches": 0, "last": None, "crm": None, "primary": False})
            row["role"] = row["role"] or str(role or "")
            row["email"] = row["email"] or str(email or "")
            row["phone"] = row["phone"] or str(phone or "")
            if src and src not in row["sources"]:
                row["sources"].append(src)
            if last and (not row["last"] or str(last) > row["last"]):
                row["last"] = str(last)
            if touch:
                row["touches"] += 1
            if crm:
                row["crm"], row["primary"] = crm, bool(crm.get("Primary contact"))

        by_id = {x["id"]: x for x in people_crm}
        for x in people_crm:
            person(x.get("Full name"), x.get("Role"), x.get("Email"), x.get("Phone"), "CRM", crm=x)
        for a in acts:
            for pid in a.get("Person") or []:
                if pid in by_id:
                    person(by_id[pid].get("Full name"), last=(a.get("When") or "")[:10], touch=True)
        for r in log_rows:
            person(r.get("Person"), r.get("Role"), src="Outreach Log", last=r.get("Day"), touch=True)
        if p.get("owner"):
            m = re.match(r"\s*([^,(]+?)\s*(?:[,(]\s*([^)]*)\)?)?\s*$", p["owner"])
            person(m.group(1) if m else p["owner"], (m.group(2) if m else "") or "Owner (from their site)", p.get("email"), src="Call list")
        for l in leads:
            person(l.get("Name"), "", l.get("Email"), l.get("Phone"), "Site booking", (l.get("When") or "")[:10], touch=True)
        for t in threads:
            person(t.get("Person"), t.get("Position"), src="LinkedIn", last=t.get("Last message") or t.get("Accepted") or t.get("Request sent"))
        people_out = sorted(people.values(), key=lambda r: (not r["primary"], -(r["touches"]), r["name"]))
        emails = sorted({e.strip().lower() for e in [p.get("email")] + [r["email"] for r in people_out] + [l.get("Email") for l in leads] if e})

        # ---- the contacts made, every source in one list, newest first
        log = []

        def add(at, kind, summary, who="", notes="", src="", path=""):
            if at or summary:
                log.append({"at": str(at or ""), "kind": kind, "summary": summary, "who": who, "notes": notes, "src": src, "path": path})

        for a in acts:
            who = ", ".join(by_id[x].get("Full name", "") for x in a.get("Person") or [] if x in by_id)
            summary = a.get("Summary") or ""
            if a.get("Outcome") and a["Outcome"] not in summary:
                summary = f"{a['Outcome']}: {summary}" if summary else a["Outcome"]
            add(a.get("When"), {"Dial": "Call"}.get(a.get("Type"), a.get("Type") or "Note"), summary, who, a.get("Notes") or "", "CRM")
        for r in log_rows:
            ch = r.get("Channel") or "Touchpoint"
            n = r.get("Touchpoint #")
            add(r.get("Day") or (r.get("created") or "")[:10], {"Cold Call": "Call", "Website form": "Form"}.get(ch, ch),
                f"{r.get('Direction') or 'Outbound'} {ch.lower()}" + (f", touchpoint {n}" if n else ""),
                " · ".join(x for x in (r.get("Person"), r.get("Role")) if x), r.get("Transcript") or "", "Outreach Log")
        if p.get("typed"):
            add(p.get("changed"), "Call", f"Call sheet status: \"{p['typed']}\"", "", p.get("notes") or "", "Call sheet")
        for l in leads:
            call = f", call {self._when_et(l['Call at'])}" if l.get("Call at") else ""
            add(l.get("When"), "Form", f"Booked on the site ({l.get('Status') or 'New'}){call}", l.get("Name") or "", l.get("Message") or "", "Site")
        for t in threads:
            who = " · ".join(x for x in (t.get("Person"), t.get("Position")) if x)
            for field, word in (("Request sent", "Connection request sent"), ("Accepted", "They accepted the request"),
                                ("First message", "First message sent"), ("Replied", "They replied")):
                if t.get(field):
                    add(t[field], "LinkedIn", word, who, "", "LinkedIn")
        for f in frees:
            add(f.get("Delivered on") or f.get("Built on"), "Free campaign", f"Free search check and campaign file: {f.get('Stage') or 'Built'}",
                "", f.get("Notes") or "", "Free campaigns")
        for d in deals:
            add(d.get("Stage changed"), "Deal", f"Deal at {d.get('Stage')}" + (f": {d.get('Close reason')}" if d.get("Closed") and d.get("Close reason") else ""),
                "", "" if d.get("Closed") else (d.get("Next action") or ""), "CRM")
        looms_data = self._looms_all()
        looms = [l for l in looms_data.get("looms") or [] if l.get("company_key") == tkey]
        for l in looms:
            mins = f"{int(l.get('seconds') or 0) // 60}:{int(l.get('seconds') or 0) % 60:02d}"
            add(l.get("sent_on") or l.get("made"), "Loom", f"Loom brief {'sent' if l.get('sent_on') else 'recorded, not sent yet'}: {l.get('title') or l['url']} ({mins})",
                "", l.get("summary") or "", "Loom")
        files = []
        if mb:
            for path in sorted((ROOT / "projects" / "prospects").glob(f"{mb} */*.md")):
                item = self._file_item(path)
                files.append(dict(item, group="Call notes"))
                try:
                    add(item["at"], "Note", f"Call notes: {path.stem}", "", path.read_text(encoding="utf-8")[:900], "Monarc Calls", item["path"])
                except OSError:
                    pass
            for path in sorted((ROOT / "projects" / "free-campaign").glob(f"{mb}-*/*")):
                if path.name in ("audit.pdf", "ads-editor.csv"):
                    files.append(dict(self._file_item(path), group="Free campaign"))
        log.sort(key=lambda x: x["at"], reverse=True)

        stage, stage_from = self._file_stage(deals, prospect)
        meeting = self._meeting_for(deals, leads, acts)
        if meeting and stage in ("Cold", "Contacted"):
            # a meeting on the calendar is Booked (references/pipeline-process.md), whatever the board still says: the
            # to-dos are the Booked ones (the confirmation, the Loom brief, the reminder), and a flag says move the deal
            stage, stage_from = "Booked", f"a meeting on file; the deal on the board still says {stage}"
        open_deal = next((d for d in deals if not d.get("Closed")), None)
        ctx = {"people": people_out, "open_deal": open_deal, "deals": deals, "meeting": meeting, "emails": emails,
               "in_crm": bool(company), "prospect": prospect, "today": s.clock.today().isoformat()}
        c = company or {}
        head = {"id": cid or raw_id, "in_crm": bool(company), "name": c.get("Name") or p.get("name") or "", "key": tkey, "mb": mb,
                "city": c.get("City") or p.get("city") or "", "state": c.get("State") or p.get("state") or "",
                "phone": c.get("Phone") or p.get("phone") or "", "website": c.get("Website") or p.get("website") or "",
                "vertical": c.get("Vertical") or p.get("vertical") or "", "local_noon": c.get("Local time at noon ET") or p.get("local_noon") or "",
                "source": c.get("source_name") or "", "phase": c.get("phase_calc"), "channels": c.get("channels"),
                "dials": c.get("Dial attempts") if company else None, "stage": stage, "stage_from": stage_from, "meeting": meeting,
                "sheet": {"typed": p.get("typed"), "changed": p.get("changed"), "outcome": p.get("outcome"), "url": p.get("url")} if prospect else None,
                "rating": p.get("rating"), "reviews": p.get("reviews"), "linkedin": p.get("linkedin") or "",
                "notes": c.get("Notes") or "", "sheet_notes": p.get("notes") or ""}
        return {"head": head, "company": company, "prospect": prospect, "people": people_out, "deals": deals, "log": log,
                "triage": self._triage_for(tkey, stage, ctx), "files": files, "queue": b["queue"] if b else None, "emails": emails,
                "looms": looms, "loom_variations": looms_data.get("variations") or []}

    def company_mail(self, raw_id):
        """Mail to and from the company, read through Bridge after the file has drawn: the inbox, Sent, and Drafts, by the
        company's domain and any address on file. A step with "mail_body" in the playbook (the Loom brief) is seen as
        done when a sent message to them holds those words; drafts to them still waiting are listed for the triage."""
        f = self.company_file(raw_id)
        if not f or f.get("redirect"):
            return {"bridge": "none", "items": []}
        key = f["head"]["key"]
        hit = Api._file_mail.get(key)
        if hit and time.time() - hit[0] < self.MAIL_TTL:
            return hit[1]
        dom = key if key and "." in key and not key.startswith(("tel:", "mb:")) else ""
        terms = {dom} if dom and dom not in self.FREE_MAIL else set()
        for e in f.get("emails") or []:
            if not dom or not e.endswith("@" + dom) or dom in self.FREE_MAIL:
                terms.add(e)
        terms = sorted(t for t in terms if t and '"' not in t and not t.endswith("monarcbuild.com"))
        if not terms:
            data = {"bridge": "none", "items": [], "note": "No email address or website on file, so there is nothing to look for in the mailbox."}
        else:
            try:
                data = self._company_mail_read(terms, f)
            except SystemExit:
                data = {"bridge": "down", "items": [], "note": "Proton Mail Bridge is closed or signed out, so mail is not shown."}
            except Exception as e:  # noqa: BLE001  the file still stands without mail
                data = {"bridge": "error", "items": [], "note": f"Could not read the mailbox: {type(e).__name__}: {str(e)[:120]}"}
        Api._file_mail[key] = (time.time(), data)
        return data

    def _company_mail_read(self, terms, f):
        import email as email_lib
        import proton_mail as pm
        m = pm.connect()
        items = []
        try:
            for folder, field in (("INBOX", "FROM"), ("Sent", "TO"), ("Drafts", "TO")):
                try:
                    typ, _ = m.select(f'"{folder}"', readonly=True)
                except Exception:  # noqa: BLE001
                    continue
                if typ != "OK":
                    continue
                uids = []
                for t in terms:
                    for u in self._uids(m, f'{field} "{t}"'):
                        if u not in uids:
                            uids.append(u)
                for uid in uids[-15:]:
                    raw, _ = self._fetch(m, uid, "(BODY.PEEK[])")
                    msg = email_lib.message_from_bytes(raw)
                    body = self._text(msg, 6000)
                    items.append({"folder": folder, "uid": uid.decode(), "at": self._mail_when(msg), "from": self._who(pm.hdr(msg, "From")),
                                  "to": self._who(pm.hdr(msg, "To")), "subject": pm.hdr(msg, "Subject"),
                                  "snippet": body.replace("\n", " ")[:260], "attachments": sum(1 for x in msg.walk() if x.get_filename()),
                                  "_body": body.lower()})
        finally:
            try:
                m.logout()
            except Exception:  # noqa: BLE001
                pass
        items.sort(key=lambda x: x["at"] or "", reverse=True)
        seen = {}
        for st in f["triage"]["steps"]:
            needle = (st.get("mail_body") or "").lower()
            hit = next((i for i in items if needle and i["folder"] == "Sent" and needle in i["_body"]), None)
            if not hit and st.get("mail_sent"):  # any email he sent them counts (the confirmation)
                hit = next((i for i in items if i["folder"] == "Sent"), None)
            if hit:
                seen[st["id"]] = f"seen in Sent, {(hit['at'] or '')[:10]}: {hit['subject']}"
        # a Loom on this file went out the day its link first shows in a sent message to them
        if f.get("looms"):
            with Api._triage_lock:
                ldata, moved = self._looms_all(), False
                for l in ldata.get("looms") or []:
                    if l.get("company_key") == f["head"]["key"] and not l.get("sent_on"):
                        hit = next((i for i in reversed(items) if i["folder"] == "Sent" and l["id"] in i["_body"]), None)
                        if hit:
                            l["sent_on"], moved = (hit["at"] or "")[:10], True
                if moved:
                    self._looms_save(ldata)
        # a draft whose email already went out (same subject in Sent, later) is an old copy, not something waiting
        sent = [(i["subject"], i["at"] or "") for i in items if i["folder"] == "Sent"]
        for i in items:
            i.pop("_body", None)
            if i["folder"] == "Drafts":
                i["superseded"] = any(sub == i["subject"] and at >= (i["at"] or "") for sub, at in sent)
        if seen:  # keep what the mailbox showed, so the list of companies waiting on him counts it as done too
            with Api._triage_lock:
                data = self._triage_all()
                comp = data.setdefault("companies", {}).setdefault(f["head"]["key"], {})
                comp.setdefault("name", f["head"]["name"])
                comp.setdefault("id", f["head"]["id"])
                done = comp.setdefault("done", {})
                changed = False
                for sid, note in seen.items():
                    if sid not in done:
                        done[sid], changed = note[len("seen in Sent, "):][:10], True
                if changed:
                    self.TRIAGE.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        return {"bridge": "ok", "items": items, "seen": seen,
                "drafts": [{"subject": d["subject"], "to": d["to"], "at": d["at"]} for d in items
                           if d["folder"] == "Drafts" and not d.get("superseded")]}

    def triage_set(self, raw_id, body):
        """Tick or untick a step, add a to-do of his own, tick or remove one. Kept in projects/crm/triage.json."""
        f = self.company_file(raw_id)
        if not f or f.get("redirect"):
            return 404, {"errors": ["No such company."]}
        tkey, today = f["head"]["key"], self.s.clock.today().isoformat()
        with Api._triage_lock:
            data = self._triage_all()
            comp = data.setdefault("companies", {}).setdefault(tkey, {})
            comp["name"], comp["id"] = f["head"]["name"], f["head"]["id"]
            if "step" in body:
                done, answers = comp.setdefault("done", {}), comp.setdefault("answers", {})
                if body.get("done"):
                    done[str(body["step"])] = today
                    if body.get("answer"):  # a step that asks (showed or no-show) keeps which one
                        answers[str(body["step"])] = str(body["answer"])[:40]
                else:
                    done.pop(str(body["step"]), None)
                    answers.pop(str(body["step"]), None)
            elif body.get("add"):
                text = re.sub(r"\s+", " ", str(body["add"])).strip()[:300]
                if not text:
                    return 422, {"errors": ["Type the to-do first."]}
                comp.setdefault("custom", []).append({"id": f"c{int(time.time() * 1000)}", "text": text, "done": False, "added": today})
            elif "custom" in body:
                for c in list(comp.get("custom") or []):
                    if c.get("id") == body["custom"]:
                        if body.get("remove"):
                            comp["custom"].remove(c)
                        else:
                            c["done"] = bool(body.get("done"))
                            c["done_on"] = today if c["done"] else None
                        break
            else:
                return 422, {"errors": ["Nothing to change."]}
            self.TRIAGE.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        return 200, {"ok": True, "triage": self.company_file(raw_id)["triage"]}

    # ---- Loom briefs (2026-10-04, Jonathan: "analyze the Loom walkthrough, different variations of it, to see how that
    # affects things like show rate and close rate"). One record per Loom in projects/crm/looms.json: the company, the
    # link, its title and length (from Loom's own embed data), which variation it is, when it went out (read from Sent),
    # and whether they watched it (his to mark; Loom emails him on a view). Show or no-show is the Booked step he
    # answers on the file; the close is the deal. The report sets each variation beside the meetings that got no Loom.

    LOOMS = CRM_DIR / "looms.json"

    def _looms_all(self):
        try:
            return json.loads(self.LOOMS.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"_about": "Loom briefs sent before a booked meeting, one record each, and the variations being compared "
                              "(2026-10-04). Written by the CRM's company file; read by Reports, Loom briefs.",
                    "variations": [], "looms": []}

    def _looms_save(self, data):
        self.LOOMS.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    @staticmethod
    def _loom_id(url):
        m = re.search(r"loom\.com/(?:share|embed)/([0-9a-f]{20,40})", str(url or ""))
        return m.group(1) if m else None

    @staticmethod
    def _loom_meta(url):
        """The Loom's title, length, and Loom's own summary, from its public embed data. Blank when Loom does not answer."""
        try:
            r = requests.get("https://www.loom.com/v1/oembed", params={"url": url}, timeout=10)
            j = r.json() if r.status_code == 200 else {}
        except (requests.RequestException, ValueError):
            j = {}
        return {"title": j.get("title") or "", "seconds": int(round(float(j.get("duration") or 0))), "summary": j.get("description") or ""}

    def loom_set(self, raw_id, body):
        """Put a Loom on a company's file (a share link), name a new variation, or change a Loom's variation, watched
        mark, or notes; or take it off."""
        f = self.company_file(raw_id)
        if not f or f.get("redirect"):
            return 404, {"errors": ["No such company."]}
        h, today = f["head"], self.s.clock.today().isoformat()
        with Api._triage_lock:
            data = self._looms_all()
            looms, vs = data.setdefault("looms", []), data.setdefault("variations", [])
            if body.get("new_variation"):
                name = re.sub(r"\s+", " ", str(body["new_variation"])).strip()[:80]
                if not name:
                    return 422, {"errors": ["Name the variation first."]}
                key = chr(ord("A") + len(vs)) if len(vs) < 26 else f"V{len(vs) + 1}"
                vs.append({"key": key, "name": name, "what": str(body.get("what") or "")[:400], "added": today})
                body = dict(body, variation=key)
            if body.get("url"):
                lid = self._loom_id(body["url"])
                if not lid:
                    return 422, {"errors": ["That is not a Loom share link (loom.com/share/...)."]}
                if any(l["id"] == lid for l in looms):
                    return 422, {"errors": ["That Loom is already on a file."]}
                url = f"https://www.loom.com/share/{lid}"
                meta = self._loom_meta(url)
                # kind (2026-10-05): "brief" is the Loom before a booked meeting (the show-rate report reads it);
                # "review" is a page review of a lead for the YouTube and shorts pipeline, kept off that report.
                kind = "review" if str(body.get("kind") or "") == "review" else "brief"
                looms.append({"id": lid, "url": url, "company_key": h["key"], "company": h["name"], "company_id": h["id"], "mb": h["mb"],
                              "title": meta["title"], "seconds": meta["seconds"], "summary": meta["summary"], "made": today, "sent_on": None,
                              "kind": kind, "variation": "" if kind == "review" else str(body.get("variation") or (vs[-1]["key"] if vs else "")),
                              "watched": "", "notes": ""})
            elif body.get("id"):
                l = next((x for x in looms if x["id"] == body["id"] and x["company_key"] == h["key"]), None)
                if not l:
                    return 404, {"errors": ["No such Loom on this file."]}
                if body.get("remove"):
                    looms.remove(l)
                else:
                    for k in ("variation", "watched", "notes", "sent_on", "kind"):
                        if k in body:
                            l[k] = str(body[k])[:400] if body[k] not in (None, "") or k != "sent_on" else None
            elif not body.get("new_variation"):
                return 422, {"errors": ["Nothing to change."]}
            self._looms_save(data)
        return 200, {"ok": True}

    def loom_report(self):
        """Show rate and close rate by Loom variation: every company with a booked meeting (or a Loom), grouped by the
        variation its Loom is, with the meetings that got no Loom as the line to beat. Showed: his answer on the file's
        "show or no-show" step, else a deal that reached Held. Won: the deal."""
        s = self.s
        data = self._looms_all()
        saved = self._triage_all().get("companies") or {}
        names = {v["key"]: v["name"] for v in data.get("variations") or []}
        by_key = {}
        for l in data.get("looms") or []:
            if l.get("kind") == "review":
                continue               # a lead's page review is not a brief before a meeting; it stays off this report
            by_key[l["company_key"]] = l  # the latest Loom on a company is the one its meeting is read against
        rows, done = [], set()
        for d in sorted(s.rows("Deals"), key=lambda d: (bool(d.get("Closed")), d.get("Stage changed") or ""), reverse=False):
            c = s.rec("Companies", (d.get("Company") or [None])[0])
            if not c:
                continue
            key = c.get("Key") or c["id"]
            if key in done:
                continue
            leads = [l for l in s.rows("Leads") if c["id"] in (l.get("Company") or [])]
            acts = [a for a in s.rows("Activities") if c["id"] in (a.get("Company") or [])]
            meeting = self._meeting_for([d], leads, acts)
            loom = by_key.get(key)
            if not (self._reached(d, "Booked") or meeting or loom):
                continue
            done.add(key)
            ans = ((saved.get(key) or {}).get("answers") or {}).get("Booked:show")
            showed = True if (ans == "Showed" or self._reached(d, "Held")) else False if ans == "No-show" else None
            # A Loom counts for a meeting only if it went out, and on or before the meeting's day (2026-10-05: Momentum's
            # no-show was read against variation A while its Loom email was still in Drafts). One that was never sent,
            # or went out after the meeting, did not reach them in time: the meeting is read as No Loom.
            at = str((meeting or {}).get("at") or "")[:10]
            unsent = bool(loom) and not (loom.get("sent_on") and (not at or str(loom["sent_on"])[:10] <= at))
            if unsent:
                loom = None
            rows.append({"company": c.get("Name"), "id": c["id"], "loom": bool(loom), "loom_not_sent_in_time": unsent,
                         "variation": (loom or {}).get("variation") or "",
                         "variation_name": (names.get(loom.get("variation"), "") or "No variation set") if loom else "No Loom",
                         "sent_on": (loom or {}).get("sent_on"), "watched": (loom or {}).get("watched") or "",
                         "seconds": (loom or {}).get("seconds"), "stage": d.get("Stage"), "meeting": (meeting or {}).get("at"),
                         "showed": showed, "won": bool(d.get("Won"))})
        for key, l in by_key.items():
            if key not in done:
                rows.append({"company": l.get("company"), "id": l.get("company_id"), "loom": True, "variation": l.get("variation") or "",
                             "variation_name": names.get(l.get("variation"), "") or "No variation set", "sent_on": l.get("sent_on"),
                             "watched": l.get("watched") or "", "seconds": l.get("seconds"), "stage": "", "meeting": None, "showed": None, "won": False})
        groups = {}
        for r in rows:
            g = groups.setdefault(r["variation_name"], {"variation": r["variation_name"], "key": r["variation"], "meetings": 0, "sent": 0,
                                                         "watched": 0, "showed": 0, "no_show": 0, "pending": 0, "won": 0})
            g["meetings"] += 1
            g["sent"] += bool(r["sent_on"])
            g["watched"] += r["watched"] == "yes"
            g["showed"] += r["showed"] is True
            g["no_show"] += r["showed"] is False
            g["pending"] += r["showed"] is None
            g["won"] += r["won"]
        out = []
        for g in groups.values():
            g["show_rate"] = self._rate(g["showed"], g["showed"] + g["no_show"])
            g["close_rate"] = self._rate(g["won"], g["showed"])
            out.append(g)
        out.sort(key=lambda g: (g["variation"] == "No Loom", g["key"] or "zz"))
        return {"groups": out, "rows": rows, "variations": data.get("variations") or [], "enough": 20}

    def triage_board(self):
        """Every company that is waiting on him (2026-10-04): open deals from Booked on, a company the call sheet says
        is booked but that is not on the board yet, and any company with a to-do of his own still open. Each with how
        many steps are open and the first one."""
        s = self.s
        saved = self._triage_all().get("companies") or {}
        book, today = self._playbook(), s.clock.today().isoformat()
        order = {st: i for i, st in enumerate(self.BOARD_STAGES)}
        rows, listed = [], set()

        def entry(tkey, rid, name, stage, ctx, src, extra=None):
            sv = saved.get(tkey) or {}
            done = sv.get("done") or {}
            open_steps = [st["text"] for st in book.get(stage) or []
                          if f"{stage}:{st['id']}" not in done and not self._step_seen(st, ctx)]
            custom = [c["text"] for c in sv.get("custom") or [] if not c.get("done")]
            flags = self._flags(stage, ctx)
            n = len(open_steps) + len(custom) + len(flags)
            if not n:
                return
            listed.add(tkey)
            rows.append(dict({"id": rid, "name": name, "stage": stage, "open": n, "from": src,
                              "next": (flags[0]["text"] if flags else (custom or open_steps)[0]),
                              "overdue": any(f["id"] == "flag:overdue" for f in flags)}, **(extra or {})))

        comps = self.company_state()
        for d in s.rows("Deals"):
            stage = d.get("Stage")
            c = s.rec("Companies", (d.get("Company") or [None])[0])
            if d.get("Closed") or not c or (s.stage(stage) or {}).get("closed"):  # a deal at Lost is done, ticked Closed or not
                continue
            tkey = c.get("Key") or c["id"]
            people = [x for x in s.rows("People") if c["id"] in (x.get("Company") or [])]
            leads = [l for l in s.rows("Leads") if c["id"] in (l.get("Company") or [])]
            acts = [a for a in s.rows("Activities") if c["id"] in (a.get("Company") or [])]
            ctx = {"people": people, "open_deal": d, "deals": [d], "meeting": self._meeting_for([d], leads, acts),
                   "emails": [x.get("Email") for x in people if x.get("Email")] + [l.get("Email") for l in leads if l.get("Email")],
                   "in_crm": True, "prospect": None, "today": today}
            if ctx["meeting"] and stage in ("Cold", "Contacted"):
                stage = "Booked"  # a meeting on file: the Booked steps apply, as on the file
            if not ctx["emails"]:
                ctx["emails"] = [True]  # the board does not read the Prospects row, where the email may sit; the file says so itself
            if stage in order:
                entry(tkey, c["id"], c.get("Name"), stage, ctx, "the board", {"due": d.get("Next action date")})
            elif (saved.get(tkey) or {}).get("custom") or (d.get("Next action date") or today) < today:
                # an earlier stage shows only for a to-do of his own or an overdue next action
                sv = saved.get(tkey) or {}
                custom = [x["text"] for x in sv.get("custom") or [] if not x.get("done")]
                flags = [f for f in self._flags(stage, ctx) if f["id"] in ("flag:overdue", "flag:no-next")]
                if custom or flags:
                    listed.add(tkey)
                    rows.append({"id": c["id"], "name": c.get("Name"), "stage": stage, "open": len(custom) + len(flags), "from": "the board",
                                 "next": flags[0]["text"] if flags else custom[0], "overdue": any(f["id"] == "flag:overdue" for f in flags),
                                 "due": d.get("Next action date")})
        for camp in self._sheet_campaigns():
            for sh in self._sheets_for(camp):
                for r in self._sheet_rows(sh)["rows"]:
                    if r["v"] != "Booked":
                        continue
                    tkey = r.get("key") or (f"mb:{r['mb']}" if r.get("mb") else None)
                    if not tkey or tkey in listed:
                        continue
                    c = comps.get(r["key"]) if r.get("key") else None
                    if c and s.open_deal(c["id"]):
                        continue
                    rid = c["id"] if c else (f"mb:{r['mb']}" if r.get("mb") else None)
                    if not rid:
                        continue
                    ctx = {"people": [], "open_deal": None, "deals": [], "meeting": None, "emails": [], "in_crm": bool(c),
                           "prospect": {"outcome": "Booked", "typed": r.get("typed")}, "today": today}
                    entry(tkey, rid, r.get("name") or tkey, "Booked", ctx, "the call sheet", {"typed": r.get("typed"), "at": r.get("at")})
        for tkey, sv in saved.items():
            custom = [x["text"] for x in sv.get("custom") or [] if not x.get("done")]
            if custom and tkey not in listed and sv.get("id"):
                rows.append({"id": sv["id"], "name": sv.get("name") or tkey, "stage": "", "open": len(custom), "from": "your to-dos",
                             "next": custom[0], "overdue": False})
        rows.sort(key=lambda r: (not r["overdue"], order.get(r["stage"], 9), r.get("due") or "9999", r["name"] or ""))
        return {"rows": rows}

    def sync_leads_to_deals(self):
        """Every lead without a deal becomes one on the board (Jonathan, 2026-09-23: "this kind of just exists as
        the pipeline"). Booked leads land at the Booked stage with "Hold the call" dated the call day; form fills
        with no time land at Contacted with "Reply with two times" due today. Company and contact come from the
        existing key rules (one company per Key, one person per Person key, one open deal per company), the deal
        carries the lead's source, and a Meeting activity marks the booking on the timeline. Runs on every
        pipeline read; a failure never breaks the read."""
        s = self.s
        if not s.air.ready:
            return []
        made = []
        stage_booked = s.stage("Booked")
        stage_new = s.stage("Contacted")
        for lead in s.rows("Leads"):
            if lead.get("Deal") or lead.get("Status") not in ("Booked", "New"):
                continue
            booked = lead.get("Status") == "Booked"
            stage = stage_booked if booked else stage_new
            if not stage:
                continue
            try:
                company = self._company_for_lead(lead)
                person = None
                if lead.get("Name") or lead.get("Email") or lead.get("Phone"):
                    person = self.find_or_create_person(company, lead.get("Name", ""), lead.get("Email", ""),
                                                        lead.get("Phone", ""), "")
                call_at = lead.get("Call at")
                call_local = s.clock.to_local(call_at) if call_at else None
                call_day = call_local.date().isoformat() if call_local else s.clock.today().isoformat()
                next_action = (f"Hold the call, {call_local.strftime('%a %b %d %I:%M %p').replace(' 0', ' ')} ET, Meet link in the calendar"
                               if call_local else "Hold the call, time in the calendar") if booked else "Reply with two times"
                deal = s.open_deal(company["id"])
                if deal:
                    df = {}
                    if not deal.get("Closed") and self._rank(deal.get("Stage")) < self._rank(stage["name"]):
                        df["Stage"] = stage["name"]
                    if not (deal.get("Next action") or "").strip():
                        df["Next action"] = next_action
                        df["Next action date"] = call_day
                    if person and not deal.get("Contact"):
                        df["Contact"] = [person["id"]]
                    if "Stage" in df:
                        self.rules.stamp_closed(df)
                    if df:
                        deal = s.update("Deals", deal["id"], df)
                else:
                    offers = s.cfg.get("offers", [])
                    offer = offers[0] if offers else {"name": "", "value": 0}
                    df = {"Deal": f"{company.get('Name')} - {offer.get('name', '')}".strip(" -"), "Company": [company["id"]],
                          "Stage": stage["name"], "Offer": offer.get("name") or None, "Value": float(offer.get("value") or 0),
                          "Close date": (s.clock.today() + timedelta(days=int(s.numbers().get("default_close_days", 30)))).isoformat(),
                          "Owner": s.cfg.get("owner_default", ""), "Next action": next_action, "Next action date": call_day,
                          "Source": list(lead.get("Source") or company.get("Source") or [])}
                    if person:
                        df["Contact"] = [person["id"]]
                    self.rules.stamp_closed(df)
                    deal = s.create("Deals", {k: v for k, v in df.items() if v not in (None, "", [])})
                s.update("Leads", lead["id"], {"Deal": [deal["id"]], "Company": [company["id"]]})
                ext = lead.get("External id") or f"lead:{lead['id']}"
                if not s.find("Activities", "External id", ext):
                    when = lead.get("When") or s.clock.iso_now()
                    act = {"Summary": ("Booked from monarcbuild.com" + (f", call {call_local.strftime('%b %d %I:%M %p').replace(' 0', ' ')} ET" if call_local else ""))
                           if booked else "Form fill from monarcbuild.com, no time picked",
                           "Type": "Meeting" if booked else "Note", "When": when, "Company": [company["id"]], "Deal": [deal["id"]],
                           "Outcome": "Booked" if booked else None, "External id": ext, "Logged by": "AIOS calendar",
                           "Notes": " · ".join(x for x in [lead.get("Technicians") and f"Technicians {lead['Technicians']}",
                                                            lead.get("UTM") and f"UTM {lead['UTM']}"] if x)}
                    if person:
                        act["Person"] = [person["id"]]
                    s.create("Activities", {k: v for k, v in act.items() if v not in (None, "")})
                self.sync_phase(company["id"])
                made.append(deal["id"])
            except Exception as e:  # noqa: BLE001
                s.last_error = f"lead sync: {e}"
        return made

    def _company_for_lead(self, lead):
        """The lead's company: its link, else the company whose Key matches the email domain or the phone, else a new one."""
        s = self.s
        cid = (lead.get("Company") or [None])[0]
        c = s.rec("Companies", cid) if cid else None
        if c:
            return c
        email = (lead.get("Email") or "").lower()
        dom = email.split("@")[-1] if "@" in email else ""
        generic = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com", "me.com", "live.com", "msn.com"}
        website = f"https://{dom}" if dom and dom not in generic else ""
        key = company_key(website, lead.get("Phone") or "")
        if key:
            c = s.find("Companies", "Key", key)
            if c:
                return c
        name = (dom.split(".")[0].capitalize() if website else "") or (lead.get("Name") or "").strip() or "New lead"
        f = {"Name": name, "Key": key or f"lead:{lead['id']}", "Dial attempts": 0,
             "Source": list(lead.get("Source") or []) or ([s.source_id("inbound")] if s.source_id("inbound") else [])}
        if website:
            f["Website"] = website
        if lead.get("Phone"):
            f["Phone"] = lead["Phone"]
        return s.create("Companies", {k: v for k, v in f.items() if v not in (None, "", [])})

    def pipeline(self, vertical=None):
        s = self.s
        try:
            self.sync_leads_to_deals()
        except Exception as e:  # noqa: BLE001
            s.last_error = f"lead sync: {e}"
        want = s.vertical(vertical)["key"] if vertical else None
        cols = []
        for st in s.stages():
            deals = [d for d in s.rows("Deals") if d.get("Stage") == st["name"]]
            items = []
            for d in deals:
                cid = (d.get("Company") or [None])[0]
                c = s.rec("Companies", cid) if cid else None
                cv = self._company_vertical(c)
                if want and cv != want:
                    continue
                nad = d.get("Next action date")
                overdue = bool(nad and not d.get("Closed") and nad < s.clock.today().isoformat())
                items.append(dict(d, company_name=c.get("Name") if c else d.get("Deal"), company_id=cid,
                                  source_name=self._source_name(d), overdue=overdue, vertical=cv))
            items.sort(key=lambda d: d.get("Next action date") or "9999")
            cols.append({"stage": st["name"], "closed": bool(st.get("closed")), "won": bool(st.get("won")),
                         "count": len(items), "value": sum(float(d.get("Value") or 0) for d in items), "deals": items})
        open_total = sum(c["value"] for c in cols if not c["closed"])
        won_total = sum(c["value"] for c in cols if c["won"])
        return {"columns": cols, "open_value": open_total, "won_value": won_total,
                "won_count": sum(c["count"] for c in cols if c["won"]), "goal": s.cfg.get("goal", {})}

    def activity(self, limit=200):
        s = self.s
        out = []
        for a in s.rows("Activities"):
            cid = (a.get("Company") or [None])[0]
            c = s.rec("Companies", cid) if cid else None
            pid = (a.get("Person") or [None])[0]
            p = s.rec("People", pid) if pid else None
            out.append(dict(a, company_name=c.get("Name") if c else None, company_id=cid,
                            person_name=p.get("Full name") if p else None))
        out.sort(key=lambda a: a.get("When") or "", reverse=True)
        return out[:limit]

    def weekly(self, week=None):
        s = self.s
        start = date.fromisoformat(week) if week else s.clock.week_start()
        start = s.clock.week_start(start)
        prev = start - timedelta(days=7)

        def in_week(iso_day, ws):
            return ws.isoformat() <= iso_day < (ws + timedelta(days=7)).isoformat()

        def tally(ws):
            dials = [d for d in s.dials() if in_week(d.get("at", "")[:10], ws)]
            contact = [d for d in dials if (s.outcome(d.get("outcome")) or {}).get("class") == "contact"]
            died = {}
            for d in contact:
                if d.get("died_on"):
                    died[d["died_on"]] = died.get(d["died_on"], 0) + 1
            per_day = {}
            for d in dials:
                k = d.get("at", "")[:10]
                per_day[k] = per_day.get(k, 0) + 1
            booked = held = 0
            for a in s.rows("Activities"):
                when = s.clock.to_local(a.get("When"))
                if not when or not in_week(when.date().isoformat(), ws):
                    continue
                if a.get("Outcome") == "Booked":
                    booked += 1
                if a.get("Type") == "Meeting":
                    held += 1
            signed = 0
            for d in s.rows("Deals"):
                if d.get("Won"):
                    when = s.clock.to_local(d.get("Stage changed"))
                    if when and in_week(when.date().isoformat(), ws):
                        signed += 1
            return {"week_of": ws.isoformat(), "dials": len(dials), "connects": len(contact),
                    "booked": booked, "held": held, "signed": signed,
                    "recognized": sum(1 for d in contact if d.get("recognized")),
                    "died_on": died, "per_day": per_day,
                    "outcomes": self._count(dials, "outcome")}

        cur, last = tally(start), tally(prev)
        lines = s.cfg.get("died_on_lines", [])
        worst = max(lines, key=lambda ln: cur["died_on"].get(ln, 0)) if cur["died_on"] else None
        return {"current": cur, "previous": last, "lines": lines, "worst_line": worst,
                "target_week": int(s.numbers().get("dials_per_day", 22)) * 5,
                "min_week": 100, "clean_week": 110}

    @staticmethod
    def _count(items, field):
        out = {}
        for it in items:
            k = it.get(field) or "?"
            out[k] = out.get(k, 0) + 1
        return out

    # ---- funnel and channels (read from the base, so edits made in Airtable count too)

    LEGACY_CONTACT = ("Gatekeeper", "Connect", "Callback", "Booked", "Not interested")

    def _contact_outcomes(self):
        names = {o["name"] for o in self.s.cfg.get("dial_outcomes", []) if o.get("class") == "contact"}
        return names | set(self.LEGACY_CONTACT)

    # ---- campaign: the Config row active_campaign names a Campaigns row and every dial links to it (2026-09-25)

    def active_campaign(self):
        """The Campaigns row named by Config active_campaign: a name string, or {"name": ..., "goal_booked": n}. None when blank."""
        s = self.s
        raw = s.cfg.get("active_campaign")
        name = raw.get("name") if isinstance(raw, dict) else raw
        if not name:
            return None
        return s.find("Campaigns", "Name", name) or s.find("Campaigns", "Platform id", name)

    @staticmethod
    def _is_dial(a):
        """A dial row: Type Dial, or (typed by hand in Airtable) Type left blank with an Outcome picked (2026-09-26)."""
        return a.get("Type") == "Dial" or (not a.get("Type") and bool(a.get("Outcome")))

    def _sheets_for(self, camp):
        """Call sheets for a campaign: tables in other bases where each row is a company and one dropdown holds the
        call outcome (Jonathan logs Trade Call List in its own base, 2026-09-26). Named in Config active_campaign:
        {"name": ..., "sheets": [{"label", "base", "table", "field", "skip": [...], "token": "<secrets.env name>"}]}."""
        raw = self.s.cfg.get("active_campaign")
        if isinstance(raw, dict) and raw.get("name") in (camp.get("Name"), camp.get("Platform id")):
            return raw.get("sheets") or []
        # a second call campaign reads its own sheet (2026-10-03, the free-campaign window): Config call_sheets,
        # {"<Platform id or Name>": [sheet, ...]}, the same sheet shape as active_campaign.sheets
        extra = self.s.cfg.get("call_sheets")
        if isinstance(extra, dict):
            for key in (camp.get("Platform id"), camp.get("Name")):
                if key and extra.get(key):
                    return extra[key]
        return []

    def _sheet_campaigns(self):
        """Every campaign with a call sheet: the active one first, then those named in Config call_sheets."""
        camps = [c for c in [self.active_campaign()] if c]
        extra = self.s.cfg.get("call_sheets")
        if isinstance(extra, dict):
            for key in extra:
                c = self.s.find("Campaigns", "Platform id", key) or self.s.find("Campaigns", "Name", key)
                if c and c["id"] not in {x["id"] for x in camps}:
                    camps.append(c)
        return camps

    # Jonathan types the outcome as words as often as he picks the dropdown (2026-09-28: 46 of 47 calls went into the
    # typed column). Read the words when the dropdown is empty. First match wins; the order matters ("overbooked" before
    # "booked", "call back" before "gatekeeper", "gatekeeper" before "email", the judged-and-skipped words before "no").
    # His readings: "no" = picked up and said no; "wrong vertical", "unqualified", "bad fit", "commercial", "no website",
    # "zip code block" = judged from the listing, never dialed; "no service" / "bad service" = a dead line.
    CALL_TEXT_RULES = [
        (r"\boverbooked\b", "Not interested"),
        (r"\bbooked\b", "Booked"),
        # the free-campaign window (2026-10-03): a yes to the free audit and campaign file is a live owner conversation
        (r"^yes\b|\bsend it\b|\bbuild it\b|\bfree campaign\b", "Connected with owner"),
        (r"\bno answer\b", "No answer"),
        (r"voicemail|\bvm\b|left (a )?message|ai respond|answering (service|machine)", "Voicemail"),
        (r"no service|bad service|not in service|disconnected|bad number|wrong number|not real|dead line|#\s*bad", "Bad number"),
        (r"wrong vert|wrong segment|unqualified|bad company|bad fit|commercial|no website|zip code|too niche", "Wrong vertical"),
        (r"call ?back|\bcall (at|after|me|tomorrow|monday|tuesday|wednesday|thursday|friday|\d)", "Callback"),
        (r"gatekeeper", "Connected with non-owner"),
        (r"e-?mail", "Callback"),
        (r"not interested|^no\b|^nope\b|has (marketing|an? (seo|marketer|agency))|don'?t need|doesn'?t need|one firefly", "Not interested"),
    ]

    @classmethod
    def call_outcome_from_text(cls, text):
        t = (text or "").strip().lower()
        if not t:
            return None
        for pattern, outcome in cls.CALL_TEXT_RULES:
            if re.search(pattern, t):
                return outcome
        return None

    def _sheet_rows(self, sheet):
        """The sheet's outcome per called row, one API call per pull (filtered, two fields), cached SHEET_TTL. The dropdown
        when picked, else the typed words read by call_outcome_from_text, else the words themselves (shown as not
        counted on Today)."""
        key = (sheet["base"], sheet["table"])
        hit = self.sheet_cache.get(key)
        if hit and time.time() - hit["at"] < SHEET_TTL:
            return hit
        field = sheet.get("field", "Status")  # the outcome dropdown; null when the sheet has none
        text_field = sheet.get("text_field")
        key_fields = sheet.get("key_fields", ["Website", "Phone"])  # the company key, so a call the CRM also has counts once
        # when the outcome last changed (an Airtable last-modified-time column on the outcome), and what Today shows for
        # a call made today (2026-09-29, Jonathan: Today's dials "can just be a reflection of the status of the Airtable")
        extra = [f for f in (sheet.get("changed_field", "Status changed"), *sheet.get("show_fields", ["Name", "Company ID"])) if f]
        tok = sheet.get("token", "AIRTABLE_API_KEY")
        try:
            client = self.sheet_clients.get((tok, sheet["base"]))
            if not client:
                client = self.sheet_clients[(tok, sheet["base"])] = Airtable(get_secret(tok), sheet["base"])
            if not client.ready:
                raise AirtableError(0, {"error": f"{tok} missing from secrets.env"})

            def pull(field, text_field, key_fields, extra):
                outcome_cols = [f for f in (field, text_field) if f]
                formula = "OR(" + ",".join(f"NOT({{{f}}}='')" for f in outcome_cols) + ")"
                return client.list_all(sheet["table"], formula=formula, fields=outcome_cols + key_fields + extra)[0]
            try:
                recs = pull(field, text_field, key_fields, extra)
            except AirtableError as e:
                if "UNKNOWN_FIELD_NAME" not in json.dumps(e.payload):
                    raise
                # a column was renamed or deleted in Airtable (2026-09-29: the Status dropdown went and the table became
                # "Contacts"): read with the columns that still exist instead of counting zero
                meta = client._request("GET", f"meta/bases/{sheet['base']}/tables")
                names = {f["name"] for t in meta.get("tables", []) if t["id"] == sheet["table"] for f in t["fields"]}
                field = field if field in names else None
                text_field = text_field if text_field in names else None
                key_fields = [k for k in key_fields if k in names]
                extra = [k for k in extra if k in names]
                if not field and not text_field:
                    raise AirtableError(0, {"error": f"the sheet has neither {sheet.get('field')!r} nor {sheet.get('text_field')!r} any more"})
                recs = pull(field, text_field, key_fields, extra)
            changed = sheet.get("changed_field", "Status changed")
            name_f, *more = sheet.get("show_fields", ["Name", "Company ID"]) or [None]
            one = lambda v: v[0] if isinstance(v, list) and v else v  # noqa: E731  (a lookup column comes back as a list, 2026-10-03)
            vals = []
            for r in recs:
                rf = r["fields"]
                typed = (rf.get(text_field) or "").strip() if text_field else ""
                picked = rf.get(field) if field else None
                website, phone = (str(one(rf.get(k)) or "") for k in (key_fields + ["", ""])[:2])
                vals.append({"v": picked or self.call_outcome_from_text(typed) or typed,
                             "key": company_key(website, phone) if (website or phone) else None,
                             "at": rf.get(changed), "id": r["id"], "typed": typed or picked or "",
                             "name": one(rf.get(name_f)) if name_f else None, "mb": one(rf.get(more[0])) if more else None,
                             "phone": phone})
            hit = {"at": time.time(), "rows": vals, "error": None}
        except (AirtableError, requests.RequestException) as e:
            # keep the last good pull; say what failed
            hit = {"at": time.time(), "rows": (hit or {}).get("rows", []), "error": str(e)[:200]}
        self.sheet_cache[key] = hit
        return hit

    def campaign_counts(self, camp):
        """Dials, connects, booked, and the rates for one Campaigns row. From its Activities rows when the base is live
        (rows typed straight into Airtable count too), else from the local dial log. Same rule as the Airtable formulas.
        Plus the campaign's call sheets: every picked outcome is a dial except the sheet's skip list (Wrong vertical)."""
        out = self._activity_counts(camp)
        sheets = self._sheets_for(camp)
        if not sheets:
            return out
        contact = self._contact_outcomes()
        known = {o["name"] for o in self.s.cfg.get("dial_outcomes", [])} | set(self.LEGACY_CONTACT)
        pulled, errors, unsorted, sheet_dials = [], [], {}, 0
        for sh in sheets:
            got = self._sheet_rows(sh)
            skip = set(sh.get("skip", ["Wrong vertical"]))
            for r in got["rows"]:
                v = r["v"]
                if v in skip:
                    continue
                if v not in known:
                    unsorted[v] = unsorted.get(v, 0) + 1
                    continue
                sheet_dials += 1
                out["dials"] += 1
                out["connects"] += v in contact
                out["booked"] += v == "Booked"
                out["dials_today"] += self._sheet_row_today(r)
            pulled.append(got["at"])
            if got["error"]:
                errors.append(f"{sh.get('label', sh['table'])}: {got['error']}")
        d, c, b = out["dials"], out["connects"], out["booked"]
        out.update(connect_rate=self._rate(c, d), booking_rate=self._rate(b, c), booked_of_dials=self._rate(b, d),
                   sheet_dials=sheet_dials, unsorted=unsorted, sheet_errors=errors,
                   sheets=[{"label": sh.get("label", ""), "url": sh.get("url", "")} for sh in sheets],
                   pulled_at=datetime.fromtimestamp(min(pulled), self.s.clock.tz).isoformat() if pulled else None)
        return out

    def sheet_counts_outside_crm(self, camps):
        """The calls in the campaigns' sheets that the CRM does not already count (2026-09-29: the Cold call card showed
        7 dials while the sheet held 109). A sheet call is left out when its company is in the CRM with dials logged
        there; a sheet booking is left out when that company's deal already reached Booked."""
        s = self.s
        comps = {c.get("Key"): c for c in s.rows("Companies") if c.get("Key")}
        deals_by_co = {}
        for d in s.rows("Deals"):
            for cid in d.get("Company") or []:
                deals_by_co.setdefault(cid, []).append(d)
        contact = self._contact_outcomes()
        known = {o["name"] for o in s.cfg.get("dial_outcomes", [])} | set(self.LEGACY_CONTACT)
        out = {"dials": 0, "connects": 0, "booked": 0}
        for camp in camps:
            for sh in self._sheets_for(camp):
                skip = set(sh.get("skip", ["Wrong vertical"]))
                for r in self._sheet_rows(sh)["rows"]:
                    v = r["v"]
                    if v in skip or v not in known:
                        continue
                    c = comps.get(r["key"]) if r["key"] else None
                    if not (c and int(c.get("Dial attempts") or 0) > 0):
                        out["dials"] += 1
                        out["connects"] += v in contact
                    booked_in_crm = c and any(self._reached(d, "Booked") for d in deals_by_co.get(c["id"], []))
                    if v == "Booked" and not booked_in_crm:
                        out["booked"] += 1
        return out

    def _activity_counts(self, camp):
        s = self.s
        contact = self._contact_outcomes()
        if s.air.ready:
            acts = [a for a in s.rows("Activities") if camp["id"] in (a.get("Campaign") or []) and self._is_dial(a)]
            today = s.clock.today().isoformat()
            dials = len(acts)
            connects = sum(1 for a in acts if a.get("Outcome") in contact)
            booked = sum(1 for a in acts if a.get("Outcome") == "Booked")
            dials_today = sum(1 for a in acts if (s.clock.to_local(a.get("When")) or datetime.min).date().isoformat() == today)
        else:
            rows = [d for d in s.dials() if d.get("campaign") == camp.get("Name")]
            today = s.clock.today().isoformat()
            dials = len(rows)
            connects = sum(1 for d in rows if d.get("class") == "contact")
            booked = sum(1 for d in rows if d.get("outcome") == "Booked")
            dials_today = sum(1 for d in rows if str(d.get("at") or "")[:10] == today)
        return {"dials": dials, "connects": connects, "booked": booked, "dials_today": dials_today,
                "connect_rate": self._rate(connects, dials), "booking_rate": self._rate(booked, connects),
                "booked_of_dials": self._rate(booked, dials)}

    def _sheet_row_today(self, r):
        """True when the row's outcome was typed today (Eastern), read from the sheet's "Status changed" column."""
        at = self.s.clock.to_local(r.get("at")) if r.get("at") else None
        return bool(at) and at.date() == self.s.clock.today()

    def sheet_today(self):
        """Today's calls in the active campaign's call sheets, newest first, each with how the CRM reads it: a dial
        (the outcome), skipped (Wrong vertical: judged from the listing), or not counted (words no rule reads)."""
        camps = self._sheet_campaigns()  # the active push and, since 2026-10-03, the free-campaign window's own sheet
        if not camps:
            return {"rows": [], "sheets": [], "pulled_at": None}
        known = {o["name"] for o in self.s.cfg.get("dial_outcomes", [])} | set(self.LEGACY_CONTACT)
        rows, pulled, sheets = [], [], []
        for camp in camps:
            for sh in self._sheets_for(camp):
                got = self._sheet_rows(sh)
                skip = set(sh.get("skip", ["Wrong vertical"]))
                pulled.append(got["at"])
                sheets.append({"label": sh.get("label", ""), "url": sh.get("url", ""), "error": got["error"], "campaign": camp.get("Name")})
                for r in got["rows"]:
                    if not self._sheet_row_today(r):
                        continue
                    kind = "skipped" if r["v"] in skip else "dial" if r["v"] in known else "not counted"
                    rows.append({"at": self.s.clock.to_local(r["at"]).isoformat(), "name": r.get("name"), "mb": r.get("mb"),
                                 "phone": r.get("phone"), "typed": r.get("typed"), "outcome": r["v"] if kind == "dial" else None,
                                 "kind": kind, "key": r.get("key"), "campaign": camp.get("Name")})
        rows.sort(key=lambda x: x["at"], reverse=True)
        return {"rows": rows, "sheets": sheets, "campaign": camps[0].get("Name"), "campaigns": [c.get("Name") for c in camps],
                "pulled_at": datetime.fromtimestamp(min(pulled), self.s.clock.tz).isoformat() if pulled else None}

    def campaign_tally(self):
        """The active campaign's counts plus its goal, for the strip on Today."""
        camp = self.active_campaign()
        if not camp:
            return None
        raw = self.s.cfg.get("active_campaign")
        goal = int(raw.get("goal_booked") or 0) if isinstance(raw, dict) else 0
        return {"id": camp["id"], "name": camp.get("Name"), "goal_booked": goal, **self.campaign_counts(camp)}

    # ---- phase: the ladder on Companies. Only moves up. Set by the server, never by hand.

    def phase_for(self, company_id):
        s = self.s
        phases = s.cfg.get("phases") or ["Untouched", "Called", "Second channel", "Third channel", "Meeting booked", "Signed"]
        chan_map = s.cfg.get("channels") or {"Dial": "phone", "Email": "email", "Text": "text", "DM": "dm"}
        c = s.rec("Companies", company_id) or {}
        acts = [a for a in s.rows("Activities") if company_id in (a.get("Company") or [])]
        deals = [d for d in s.rows("Deals") if company_id in (d.get("Company") or [])]
        contact = self._contact_outcomes()
        channels = set()
        for a in acts:
            ch = chan_map.get(a.get("Type"))
            if not ch:
                continue
            if a.get("Type") == "Dial" and a.get("Outcome") not in contact:
                continue
            channels.add(ch)
        # a LinkedIn message Jonathan sent counts as the DM channel, same as a DM activity (2026-09-28)
        if any(t.get("First message") for t in s.rows("LinkedIn threads") if company_id in (t.get("Company") or [])):
            channels.add(chan_map.get("DM", "dm"))
        called = int(c.get("Dial attempts") or 0) > 0 or any(a.get("Type") == "Dial" for a in acts)
        booked = any(self._reached(d, "Booked") for d in deals) or any(a.get("Outcome") == "Booked" or a.get("Type") == "Meeting" for a in acts)
        signed = any(d.get("Won") for d in deals)
        if signed:
            idx = 5
        elif booked:
            idx = 4
        elif len(channels) >= 3:
            idx = 3
        elif len(channels) >= 2:
            idx = 2
        elif called or channels:
            idx = 1
        else:
            idx = 0
        return phases[min(idx, len(phases) - 1)], len(channels)

    def sync_phase(self, company_id):
        """Write Phase and Channels touched to the company when they changed. Never moves the phase down."""
        s = self.s
        c = s.rec("Companies", company_id)
        if not c:
            return None
        phases = s.cfg.get("phases") or []
        phase, n = self.phase_for(company_id)
        cur = c.get("Phase")
        if cur in phases and phase in phases and phases.index(cur) > phases.index(phase):
            phase = cur
        if c.get("Phase") != phase or int(c.get("Channels touched") or 0) != n:
            try:
                s.update("Companies", company_id, {"Phase": phase, "Channels touched": n})
            except AirtableError as e:
                s.last_error = str(e)
        return phase

    def rephase_all(self):
        out = {}
        for c in s_rows_snapshot(self.s, "Companies"):
            out[c["id"]] = self.sync_phase(c["id"])
        return {"updated": len(out), "phases": self._count([{"p": v} for v in out.values()], "p")}

    def _reached(self, deal, stage_name):
        """A deal at Held has been Booked. Stages are monotonic, so 'reached' is rank >= rank(stage).
        Lost deals count as reached for every stage at or below Contacted only."""
        names = [st["name"] for st in self.s.stages() if not st.get("closed")]
        cur = deal.get("Stage")
        if deal.get("Won"):
            return True
        if cur not in names:
            return stage_name == "Contacted" if deal.get("Closed") else False
        return names.index(cur) >= names.index(stage_name) if stage_name in names else False

    def _funnel_for(self, company_ids=None):
        """Counts for a set of companies (None = everyone)."""
        s = self.s
        comps = [c for c in s.rows("Companies") if company_ids is None or c["id"] in company_ids]
        ids = {c["id"] for c in comps}
        dials = sum(int(c.get("Dial attempts") or 0) for c in comps)
        keys = {c.get("Key") for c in comps}
        if company_ids is None:
            dials += sum(1 for d in s.dials() if d.get("key") not in keys)  # dialed but never created (connect mode)
        acts = [a for a in s.rows("Activities") if (a.get("Company") or [None])[0] in ids]
        contact = self._contact_outcomes()
        connects = sum(1 for a in acts if a.get("Type") == "Dial" and a.get("Outcome") in contact)
        meetings = {(a.get("Company") or [None])[0] for a in acts if a.get("Type") == "Meeting"}
        deals = [d for d in s.rows("Deals") if (d.get("Company") or [None])[0] in ids]
        contacted = sum(1 for d in deals if self._reached(d, "Contacted"))
        booked = sum(1 for d in deals if self._reached(d, "Booked"))
        held = sum(1 for d in deals if self._reached(d, "Held") or (d.get("Company") or [None])[0] in meetings)
        proposed = sum(1 for d in deals if self._reached(d, "Proposed"))
        won = sum(1 for d in deals if d.get("Won"))
        lost = sum(1 for d in deals if d.get("Closed") and not d.get("Won"))
        conversations = max(connects, contacted)
        return {
            "companies": len(comps), "dialed": sum(1 for c in comps if int(c.get("Dial attempts") or 0) > 0),
            "dials": dials, "connects": connects, "contacted": contacted, "booked": booked, "held": held,
            "proposed": proposed, "won": won, "lost": lost, "open": sum(1 for d in deals if not d.get("Closed")),
            "open_value": sum(float(d.get("Value") or 0) for d in deals if not d.get("Closed")),
            "revenue": sum(float(d.get("Value") or 0) for d in deals if d.get("Won")),
            "rates": {
                "connect": self._rate(connects, dials),
                "booking": self._rate(booked, conversations),
                "show": self._rate(held, booked),
                "close": self._rate(won, held),
                "close_of_booked": self._rate(won, booked),
            },
        }

    @staticmethod
    def _rate(a, b):
        return round(100.0 * a / b, 1) if b else None

    def funnel(self):
        f = self._funnel_for(None)
        f["assumed_rates"] = (self.s.cfg.get("goal") or {}).get("assumed_rates", {})
        f["stages"] = [st["name"] for st in self.s.stages()]
        return f

    def channels(self):
        """One card per source, the same shape the channel workspace uses (2026-09-23: inputs, outputs, activity)."""
        out = [self._channel_card(src) for src in self.s.rows("Sources")]
        order = {"Cold call": 0, "Cold": 0, "Google Ads": 1, "LinkedIn": 2, "Warm": 3, "Referral": 4, "Rep": 5, "Inbound": 6,
                 "Meta Ads": 7, "Google Organic": 8, "Email": 9, "Content": 10}
        out.sort(key=lambda r: (not r["active"], order.get(r["type"], 11), -r["revenue"], -r["open_value"]))
        total = self.funnel()
        total["spend"] = sum(c["spend"] or 0 for c in out)
        total["leads"] = sum(c["leads"] for c in out)
        # every campaign under its channel, each with its brief (2026-09-29)
        s, ads_cards, groups = self.s, self._ads_cards(), []
        for card in out:
            camps = [c for c in s.rows("Campaigns") if card["id"] in (c.get("Channel") or [])]
            if not camps:
                continue
            leads = [l for l in s.rows("Leads") if card["id"] in (l.get("Source") or [])]
            rows = sorted((self._camp_row(c, card, leads, ads_cards=ads_cards) for c in camps), key=self._camp_order)
            groups.append({"channel": card["name"], "label": card["label"], "type": card["type"], "id": card["id"],
                           "sort": card["sort"], "campaigns": rows})
        return {"channels": out, "total": total, "campaign_groups": groups}

    # ---- home and channel workspaces

    def _spend_for(self, campaigns, today):
        total, est = 0.0, False
        for c in campaigns:
            sp = c.get("Spend to date")
            if sp not in (None, ""):
                total += float(sp)
            elif c.get("Started") and c.get("Daily budget"):
                try:
                    end = date.fromisoformat(c["Ended"]) if c.get("Ended") else today
                    days = (end - date.fromisoformat(c["Started"])).days + 1
                    total += max(0, days) * float(c["Daily budget"])
                    est = True
                except ValueError:
                    pass
        return total, est

    def _lead_stats(self, leads):
        return {
            "leads": len(leads),
            "leads_called": sum(1 for l in leads if l.get("Status") not in (None, "New")),
            "leads_booked": sum(1 for l in leads if l.get("Status") in ("Booked", "Sold")),
            "leads_sold": sum(1 for l in leads if l.get("Status") == "Sold"),
            "minutes_to_call": self._median([self._minutes(l.get("When"), l.get("First call at")) for l in leads
                                             if l.get("When") and l.get("First call at")]),
        }

    def _minutes(self, a, b):
        ta, tb = self.s.clock.to_local(a), self.s.clock.to_local(b)
        return round((tb - ta).total_seconds() / 60) if ta and tb else None

    @staticmethod
    def _median(vals):
        vals = sorted(v for v in vals if v is not None)
        if not vals:
            return None
        n = len(vals)
        return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2

    def _thread_outcome(self, t):
        """Booked or Not interested for a LinkedIn thread: Jonathan's Outcome first, else the linked company's deal."""
        if t.get("Outcome"):
            return t["Outcome"]
        cid = (t.get("Company") or [None])[0]
        deals = [d for d in self.s.rows("Deals") if cid and cid in (d.get("Company") or [])]
        if any(self._reached(d, "Booked") for d in deals):
            return "Booked"
        if any(d.get("Closed") and not d.get("Won") for d in deals):
            return "Not interested"
        return None

    def messaging_stats(self, threads):
        """The LinkedIn messaging medium, request to booked (2026-09-28). Accept rate = accepted of requests sent;
        reply rate = replied of messaged; booking rate = booked of replied."""
        outcomes = [self._thread_outcome(t) for t in threads]
        requests = sum(1 for t in threads if t.get("Request sent"))
        accepted = sum(1 for t in threads if t.get("Request sent") and t.get("Accepted"))
        messaged = sum(1 for t in threads if t.get("First message"))
        replied = sum(1 for t in threads if t.get("Replied"))
        booked = sum(1 for o in outcomes if o == "Booked")
        imported = max((t.get("Imported") or "" for t in threads), default="") or None
        return {"people": len(threads), "requests": requests, "accepted": accepted, "messaged": messaged, "replied": replied,
                "booked": booked, "not_interested": sum(1 for o in outcomes if o == "Not interested"),
                "accept_rate": self._rate(accepted, requests), "reply_rate": self._rate(replied, messaged),
                "booking_rate": self._rate(booked, replied), "imported": imported}

    # ---- a booker's journey (2026-09-28): the lead, the click that brought them, each page and booking step (from
    # assets/journey.js on the site, saved on the lead by the booking script), and what happened in the CRM after.

    AD_MEDIUMS = ("paid-social", "paidsocial", "cpc", "ppc", "paid")
    DM_MEDIUMS = ("dm", "message", "messaging", "inmail")

    @staticmethod
    def _qs(raw):
        from urllib.parse import parse_qs
        raw = (raw or "").strip()
        if not raw:
            return {}
        qs = raw.split("?", 1)[1] if "?" in raw else raw
        return {k.lower(): v[0] for k, v in parse_qs(qs).items()}

    @staticmethod
    def _journey(lead):
        try:
            j = json.loads(lead.get("Journey") or "null")
        except ValueError:
            return None
        return j if isinstance(j, dict) and isinstance(j.get("ev"), list) else None

    def lead_medium(self, lead):
        """Ads, DMs, or Posts for a LinkedIn lead: from its link tags, else its journey's first click. An ad click carries
        li_fat_id or a paid medium; a DM link carries utm_medium=dm (or the messaging campaign); anything else from
        LinkedIn, tagged or not, is a post."""
        q = self._qs(lead.get("UTM"))
        j = self._journey(lead)
        if not q.get("utm_source") and not q.get("li_fat_id") and j and isinstance(j.get("first"), dict):
            q = {k: str(v) for k, v in j["first"].items()}
        med, camp = (q.get("utm_medium") or "").lower(), (q.get("utm_campaign") or "").lower()
        if q.get("li_fat_id") or med in self.AD_MEDIUMS:
            return "Ads"
        if med in self.DM_MEDIUMS or camp == "linkedin-messaging":
            return "DMs"
        return "Posts"

    def linkedin_mediums(self, camps, leads, messaging):
        """Booking rate per LinkedIn medium (2026-09-28). Ads: booked of ad clicks (typed on the ad campaign rows from
        Campaign Manager). Posts: booked of post clicks (typed on the "LinkedIn posts" row from LinkedIn's post
        analytics, until Google Analytics is read). DMs: booked of replies (the LinkedIn export)."""
        by = {"Ads": [], "Posts": [], "DMs": []}
        for l in leads:
            by[self.lead_medium(l)].append(l)
        booked = lambda ls: sum(1 for l in ls if l.get("Status") in ("Booked", "Sold"))  # noqa: E731
        clicks = lambda pred: sum(int(float(c.get("Clicks") or 0)) for c in camps if pred(c.get("Platform id")))  # noqa: E731
        ad_clicks = clicks(lambda p: p not in ("linkedin-posts", "linkedin-messaging"))
        post_clicks = clicks(lambda p: p == "linkedin-posts")
        m = messaging or {}
        dm_booked = max(m.get("booked", 0), booked(by["DMs"]))
        return [
            {"medium": "Ads", "base": ad_clicks, "base_label": "clicks", "leads": len(by["Ads"]), "booked": booked(by["Ads"]),
             "rate": self._rate(booked(by["Ads"]), ad_clicks)},
            {"medium": "Posts", "base": post_clicks, "base_label": "clicks", "leads": len(by["Posts"]), "booked": booked(by["Posts"]),
             "rate": self._rate(booked(by["Posts"]), post_clicks)},
            {"medium": "DMs", "base": m.get("replied", 0), "base_label": "replies", "leads": len(by["DMs"]), "booked": dm_booked,
             "rate": self._rate(dm_booked, m.get("replied", 0))},
        ]

    def lead_detail(self, lead_id):
        s = self.s
        l = s.rec("Leads", lead_id)
        if not l:
            return None
        j = self._journey(l)
        src = s.rec("Sources", (l.get("Source") or [None])[0]) or {}
        camp = s.rec("Campaigns", (l.get("Campaign") or [None])[0])
        deal = s.rec("Deals", (l.get("Deal") or [None])[0])
        comp = s.rec("Companies", (l.get("Company") or (deal or {}).get("Company") or [None])[0])
        at = lambda t: datetime.fromtimestamp(int(t), s.clock.tz).isoformat() if t else None  # noqa: E731
        tag_keys = ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "utm_id", "li_fat_id", "gclid", "fbclid")
        events = []
        for e in (j or {}).get("ev", []):
            if isinstance(e, dict):
                events.append({"at": at(e.get("t")), "kind": e.get("k"), "page": e.get("p"), "ref": e.get("ref"),
                               "tags": {k: e[k] for k in tag_keys if e.get(k)}})
        first = (j or {}).get("first") if isinstance((j or {}).get("first"), dict) else None
        after = []
        if comp:
            for a in s.rows("Activities"):
                if comp["id"] in (a.get("Company") or []) and (a.get("When") or "") >= (l.get("When") or ""):
                    after.append({"at": a.get("When"), "summary": a.get("Summary"), "type": a.get("Type"), "outcome": a.get("Outcome")})
        after.sort(key=lambda x: x["at"] or "")
        return {"lead": l, "source": src.get("Label") or src.get("Name"), "source_name": src.get("Name"),
                "campaign": camp.get("Name") if camp else None,
                "medium": self.lead_medium(l) if src.get("Name") == "linkedin" else None,
                "tags": self._qs(l.get("UTM")),
                "first": dict({k: first[k] for k in tag_keys if first.get(k)}, at=at(first.get("t")), ref=first.get("ref"), page=first.get("p")) if first else None,
                "events": events,
                "company": {"id": comp["id"], "name": comp.get("Name")} if comp else None,
                "deal": {"id": deal["id"], "stage": deal.get("Stage"), "value": deal.get("Value"), "next": deal.get("Next action")} if deal else None,
                "after": after}

    def _channel_card(self, src):
        s = self.s
        today = s.clock.today()
        ids = {c["id"] for c in s.rows("Companies") if src["id"] in (c.get("Source") or [])}
        f = self._funnel_for(ids)
        deals = [d for d in s.rows("Deals") if src["id"] in (d.get("Source") or [])]
        f["deals"] = len(deals)
        f["open_value"] = sum(float(d.get("Value") or 0) for d in deals if not d.get("Closed"))
        f["revenue"] = sum(float(d.get("Value") or 0) for d in deals if d.get("Won"))
        f["won"] = sum(1 for d in deals if d.get("Won"))
        camps = [c for c in s.rows("Campaigns") if src["id"] in (c.get("Channel") or [])]
        camp_ids = {c["id"] for c in camps}
        # calls logged in a campaign's own sheet (the Trade Call List base) count on the channel too, once (2026-09-29)
        extra = self.sheet_counts_outside_crm(camps)
        f["sheet_dials"] = extra["dials"]
        f["sheet_connects"] = extra["connects"]   # the Funnels tab adds these to the base's total (2026-10-03)
        f["sheet_booked"] = extra["booked"]
        if extra["dials"] or extra["booked"]:
            f["dials"] += extra["dials"]
            f["connects"] += extra["connects"]
            f["booked"] += extra["booked"]
            f["rates"] = dict(f["rates"], connect=self._rate(f["connects"], f["dials"]),
                              booking=self._rate(f["booked"], max(f["connects"], f["contacted"])))
        listings = [l for l in s.rows("Listings") if camp_ids & set(l.get("Campaign") or [])]
        threads = [t for t in s.rows("LinkedIn threads") if camp_ids & set(t.get("Campaign") or [])]
        has_messaging = bool(threads) or any(c.get("Platform id") == "linkedin-messaging" for c in camps)
        leads = [l for l in s.rows("Leads") if src["id"] in (l.get("Source") or [])]
        spend, est = self._spend_for(camps, today)
        if src.get("Spend to date") not in (None, ""):
            spend, est = float(src["Spend to date"]), False
        ls = self._lead_stats(leads)
        booked_any = max(f["booked"], ls["leads_booked"])
        # ad platform inputs, typed on the campaign rows until an API fills them (2026-09-23)
        impressions = sum(int(float(c.get("Impressions") or 0)) for c in camps)
        clicks = sum(int(float(c.get("Clicks") or 0)) for c in camps)
        statuses = {}
        for c in camps:
            st = c.get("Status") or "Planned"
            statuses[st] = statuses.get(st, 0) + 1
        # the last few things that happened on this channel: activities on its companies, and its leads
        recent = []
        for a in s.rows("Activities"):
            cid = (a.get("Company") or [None])[0]
            if cid in ids:
                comp = s.rec("Companies", cid)
                recent.append({"when": a.get("When"), "summary": a.get("Summary"), "outcome": a.get("Outcome"),
                               "company": comp.get("Name") if comp else None, "kind": a.get("Type")})
        for l in leads:
            recent.append({"when": l.get("When"), "summary": f"Lead: {l.get('Name') or 'no name'}", "outcome": l.get("Status"),
                           "company": None, "kind": "Lead"})
        recent.sort(key=lambda r: r["when"] or "", reverse=True)
        return {
            "id": src["id"], "name": src.get("Name"), "label": src.get("Label") or src.get("Name"), "type": src.get("Type"),
            "active": bool(src.get("Active")), "acquisition": bool(src.get("Acquisition")), "sort": src.get("Sort") or 99,
            "notes": src.get("Notes", ""), "campaigns": len(camps), "campaigns_live": sum(1 for c in camps if c.get("Status") == "Live"),
            "campaign_status": statuses,
            "spend": spend, "spend_is_estimate": est, "daily_budget": src.get("Daily budget") or 0,
            "impressions": impressions, "clicks": clicks,
            # the website's pages that are up, and the directory listings of this channel's campaigns (NAP citations),
            # for the Google Organic card (2026-09-27)
            # ad pages are noindex and tied to an ad campaign, so they are not the organic site (2026-09-29)
            "pages_live": sum(1 for p in s.rows("Landing pages") if p.get("Status") == "Live" and not p.get("Campaign")),
            "listings": len(listings), "listings_live": sum(1 for l in listings if l.get("Status") == "Live"),
            # the messaging medium (LinkedIn), when the channel has a messaging campaign or threads
            "messaging": self.messaging_stats(threads) if has_messaging else None,
            "ctr": round(clicks / impressions * 100, 2) if impressions else None,
            "cpc": round(spend / clicks, 2) if spend and clicks else None,
            "cost_per_lead": round(spend / ls["leads"]) if spend and ls["leads"] else None,
            "cost_per_booked": round(spend / booked_any) if spend and booked_any else None,
            "cost_per_won": round(spend / f["won"]) if spend and f["won"] else None,
            "recent": recent[:4],
            **f, **ls,
        }

    def home(self):
        cards = [self._channel_card(src) for src in self.s.rows("Sources")]
        acq = sorted([c for c in cards if c["acquisition"]], key=lambda c: c["sort"])
        other = sorted([c for c in cards if not c["acquisition"]], key=lambda c: c["sort"])
        return {"channels": acq, "other_sources": other, "total": self.funnel(), "goal": self.s.cfg.get("goal", {}),
                "today": self.queue(limit=22)["dialed_today"]}

    # ---- campaigns under their channel (2026-09-29, Jonathan: "all campaigns should be listed underneath the channels";
    # a click opens the tasks and the outcomes we want). One row shape for Channels and for each channel's page.

    CAMP_STATUS_ORDER = {"Live": 0, "Planned": 1, "Paused": 2, "Ended": 3}

    def _camp_order(self, c):
        return (self.CAMP_STATUS_ORDER.get(c.get("Status") or "Planned", 4), c.get("Name") or "")

    def _attrib(self, ls):
        """Lead counts and deal value for a set of leads (a campaign's, a keyword's, a page's)."""
        s = self.s
        st = self._lead_stats(ls)
        deal_ids = {(l.get("Deal") or [None])[0] for l in ls} - {None}
        deals = [s.rec("Deals", i) for i in deal_ids if s.rec("Deals", i)]
        st["deal_value"] = sum(float(d.get("Value") or 0) for d in deals)
        st["won_value"] = sum(float(d.get("Value") or 0) for d in deals if d.get("Won"))
        return st

    def _ads_cards(self):
        """The Ads screen's campaign files by name, for the Google Ads campaigns' tasks. Empty when they cannot be read."""
        try:
            import ads_publish as ap
            return {c["name"]: c for c in ap.cards()}
        except Exception:  # noqa: BLE001  the brief still shows its typed tasks
            return {}

    def _camp_row(self, c, card, leads, kws=(), ads_cards=None):
        a = self._attrib([l for l in leads if c["id"] in (l.get("Campaign") or [])])
        spend, est = self._spend_for([c], self.s.clock.today())
        impr = int(float(c.get("Impressions") or 0))
        clicks = int(float(c.get("Clicks") or 0))
        row = dict(c, spend=spend, spend_is_estimate=est, channel_name=card["name"], channel_label=card["label"],
                   channel_id=card["id"], keywords=sum(1 for k in kws if c["id"] in (k.get("Campaign") or [])),
                   ctr=round(clicks / impr * 100, 2) if impr else None,
                   cpc=round(spend / clicks, 2) if spend and clicks else None,
                   cost_per_lead=round(spend / a["leads"]) if spend and a["leads"] else None,
                   cost_per_booked=round(spend / a["leads_booked"]) if spend and a["leads_booked"] else None,
                   # conversion rate as Google Ads counts it: form fills (leads) over clicks (2026-09-29)
                   conv_rate=round(a["leads"] / clicks * 100, 1) if clicks else None,
                   calls=self.campaign_counts(c), **a)
        row["booked"] = max(int(row["calls"].get("booked") or 0), int(a["leads_booked"] or 0))
        row["brief"] = self.campaign_brief(row, card.get("type"), ads_cards)
        return row

    @staticmethod
    def _typed_lines(text, tasks=False):
        """Outcomes or Tasks as typed on the Campaigns row: one per line; a task line starting [x] is done. Each task
        keeps its line number so the CRM can tick it in place."""
        out = []
        for i, raw in enumerate((text or "").splitlines()):
            ln = raw.strip()
            if ln[:2] in ("- ", "* ", "• "):
                ln = ln[2:].strip()
            done = False
            if tasks and ln[:3].lower() in ("[x]", "[ ]"):
                done, ln = ln[1].lower() == "x", ln[3:].strip()
            if ln:
                out.append({"text": ln, "done": done, "line": i, "typed": True} if tasks else ln)
        return out

    def _goal_booked(self, c):
        raw = self.s.cfg.get("active_campaign")
        return int(raw.get("goal_booked") or 0) if isinstance(raw, dict) and raw.get("name") == c.get("Name") else 0

    def campaign_brief(self, c, channel_type, ads_cards=None):
        """What a campaign row opens into: the outcomes we want (typed), where it stands (counted), and the tasks,
        typed ones first, then the ones the CRM reads itself: the directory listings, the portfolio builds, or the
        Ads screen's approvals and gates."""
        s = self.s
        k = c.get("calls") or {}
        pct = lambda v: "–" if v is None else f"{v}%"  # noqa: E731
        usd = lambda v: f"${float(v):,.0f}"  # noqa: E731

        def m(label, value, sub=""):
            return {"label": label, "value": value, "sub": sub}

        def item(text, status, done, sub="", **kw):
            return dict(text=text, status=status, done=bool(done), sub=sub, **kw)

        booked = max(int(k.get("booked") or 0), int(c.get("leads_booked") or 0))
        clicks = int(float(c.get("Clicks") or 0))
        groups = [{"title": "Tasks", "items": self._typed_lines(c.get("Tasks"), tasks=True)}]
        listings = sorted((l for l in s.rows("Listings") if c["id"] in (l.get("Campaign") or [])),
                          key=lambda l: (l.get("Order") or 99, l.get("Directory") or ""))
        builds = [b for b in s.rows("Portfolio builds") if c["id"] in (b.get("Campaign") or [])]
        threads = [t for t in s.rows("LinkedIn threads") if c["id"] in (t.get("Campaign") or [])]
        ad = (ads_cards or {}).get(c.get("Name"))

        if channel_type == "Cold call" or k.get("sheets"):
            goal = self._goal_booked(c)
            measures = [m("Dials", k.get("dials", 0), f"{k['dials_today']} today" if k.get("dials_today") else ""),
                        m("Connects", k.get("connects", 0)), m("Connect rate", pct(k.get("connect_rate")), "of dials"),
                        m("Booked", f"{booked} of {goal}" if goal else booked),
                        m("Booking rate", pct(k.get("booking_rate")), "of connects")]
            headline = (f"{booked} of {goal} booked" if goal else f"{booked} booked") + f" · {k.get('dials', 0)} dials"
        elif listings:
            live = [l for l in listings if l.get("Status") == "Live"]
            measures = [m("Directories live", f"{len(live)} of {len(listings)}"),
                        m("NAP matches", f"{sum(1 for l in live if l.get('NAP matches'))} of {len(live)}" if live else "–",
                          "name, city, phone on the live ones"),
                        m("Links to the site", sum(1 for l in live if l.get("Link") == "Followed"), "followed")]
            groups.append({"title": "Directories", "note": "In order: the Business Profile first, the rest copy it. Click one to update it.",
                           "items": [item(l.get("Directory") or "", l.get("Status") or "To do", l.get("Status") == "Live",
                                          l.get("Kind") or "", table="Listings", id=l["id"], record=l) for l in listings]})
            headline = f"{len(live)} of {len(listings)} directories live"
        elif builds or c.get("Platform id") == "review-generation-farm":
            stage = lambda b: b.get("Stage") or "Request found"  # noqa: E731
            delivered = sum(1 for b in builds if stage(b) == "Delivered")
            reviews = sum(1 for b in builds if b.get("Google review") == "Left")
            measures = [m("Builds", len(builds), f"{sum(1 for b in builds if stage(b) in ('Offered', 'Building'))} in progress"),
                        m("Delivered", delivered), m("Google reviews", reviews),
                        m("Portfolio OK", sum(1 for b in builds if b.get("Portfolio OK"))),
                        m("Good ad fit", sum(1 for b in builds if b.get("Ad fit") == "Good fit"))]
            groups.append({"title": "Builds", "note": "One row per business in the Portfolio builds table (Airtable).",
                           "items": [item(b.get("Business") or "", stage(b), stage(b) in ("Delivered", "Declined"),
                                          b.get("Next step") or ", ".join(x for x in (b.get("Trade"), b.get("City")) if x))
                                     for b in sorted(builds, key=lambda b: b.get("Offered on") or "", reverse=True)]})
            headline = f"{delivered} delivered · {reviews} review{'' if reviews == 1 else 's'}"
        elif ad:
            appr = ad.get("approvals") or {}
            word = {"approved": "Approved", "changed": "Changed since approved", "open": "Open"}
            names = {"spend": f"Approve the spend (${ad['daily_budget']} a day)",
                     "keywords": f"Approve the {len(ad.get('keywords') or [])} keywords",
                     "negatives": "Approve the negatives", "ad": "Approve the ad"}
            here = "#/channel/google-ads"  # the approvals live on the Google Ads channel page (2026-09-29)
            items = [item(names[p], word.get(appr.get(p), "Open"), appr.get(p) == "approved", href=here)
                     for p in ("spend", "keywords", "negatives", "ad")]
            items.append(item("Publish to Google Ads, paused", "Published" if ad.get("published") else "Open",
                              ad.get("published"), href=here))
            items += [item(g["name"], "Done" if g["ok"] else "Open", g["ok"], "" if g["ok"] else (g.get("note") or ""), href=here)
                      for g in ad.get("gates") or []]
            live = ad.get("status") == "ENABLED"
            items.append(item("Go live", "Live" if live else ("Open" if ad.get("gates_ok") else "Locked"), live,
                              "" if live else "Held to $100 a day in total, one test campaign at a time", href=here))
            groups.append({"title": "Approvals and gates", "kind": "ads", "items": items,
                           "note": "Approve, take back, and edit on the Google Ads page. Click one to go there."})
            spend = c.get("spend") or 0
            measures = [m("Budget", f"${ad['daily_budget']}/day"), m("Spend", usd(spend) if spend else "$0"),
                        m("Clicks", clicks), m("CTR", pct(c.get("ctr"))), m("Leads", c.get("leads", 0)), m("Booked", booked),
                        m("Cost per booked", usd(c["cost_per_booked"]) if c.get("cost_per_booked") else "–")]
            n_ok = sum(1 for p in ("spend", "keywords", "negatives", "ad") if appr.get(p) == "approved")
            gates = ad.get("gates") or []
            headline = (f"{booked} booked · {clicks} clicks" if ad.get("published") and live
                        else f"{n_ok} of 4 approved · {sum(1 for g in gates if g['ok'])} of {len(gates)} gates")
        elif threads or c.get("Platform id") == "linkedin-messaging":
            ms = self.messaging_stats(threads)
            measures = [m("Requests", ms["requests"]), m("Accepted", ms["accepted"], f"{pct(ms['accept_rate'])} accept"),
                        m("Replied", ms["replied"], f"{pct(ms['reply_rate'])} reply"),
                        m("Booked", ms["booked"], f"{pct(ms['booking_rate'])} of replies")]
            headline = f"{ms['booked']} booked · {ms['replied']} replies"
        else:
            spend = c.get("spend") or 0
            measures = ([m("Spend", usd(spend), "est." if c.get("spend_is_estimate") else "")] if spend else []) + \
                       ([m("Clicks", clicks)] if clicks else []) + \
                       [m("Leads", c.get("leads", 0)), m("Booked", booked),
                        m("Won", usd(c["won_value"]) + "/mo" if c.get("won_value") else 0)]
            headline = f"{c.get('leads', 0)} lead{'' if c.get('leads') == 1 else 's'} · {booked} booked"
        frees = [f for f in s.rows("Free campaigns") if c["id"] in (f.get("Campaign") or [])]
        if frees or c.get("Platform id") == "free-campaign":
            # the free campaign for a review (2026-10-03): one row per company from Built to Review left, beside the
            # second window's dials above
            st = lambda f: f.get("Stage") or "Built"  # noqa: E731
            delivered = sum(1 for f in frees if st(f) in ("Delivered", "Ask drafted", "Ask sent", "Review left"))
            asked = sum(1 for f in frees if st(f) in ("Ask sent", "Review left"))
            reviews = sum(1 for f in frees if st(f) == "Review left")
            waiting = sum(1 for f in frees if st(f) in ("Built", "Approved", "Delivery drafted"))
            measures += [m("Built", len(frees), f"{waiting} not sent yet" if waiting else ""), m("Delivered", delivered),
                         m("Asks sent", asked), m("Reviews", reviews, f"{pct(self._rate(reviews, delivered))} of delivered" if delivered else "")]
            groups.append({"title": "Deliveries", "note": "One row per company (Free campaigns in Airtable). Click one to set its stage; the first three need Approved before the draft.",
                           "items": [item(f.get("Company name") or f.get("MB ID") or "", st(f), st(f) in ("Review left", "Declined"),
                                          ", ".join(x for x in (f.get("MB ID"), f.get("City")) if x), table="Free campaigns", id=f["id"], record=f)
                                     for f in sorted(frees, key=lambda f: f.get("Built on") or "", reverse=True)]})
            headline = f"{reviews} review{'' if reviews == 1 else 's'} · {delivered} delivered · {k.get('dials', 0)} dials"
        groups = [g for g in groups if g["items"]]
        every = [i for g in groups for i in g["items"]]
        out = {"headline": headline, "measures": measures, "outcomes": self._typed_lines(c.get("Outcomes")),
               "groups": groups, "done": sum(1 for i in every if i["done"]), "total": len(every)}
        if ad:
            # a Google Ads campaign opens into two cards (2026-09-29): the advertising (the ad's headlines and
            # descriptions) and the creative asset (a copy of its landing page)
            a = ad["ad"]
            out["ad"] = {"headlines": [{"text": h["text"], "pin": h.get("pin")} for h in a.get("headlines", [])],
                         "descriptions": list(a.get("descriptions", [])),
                         "path": "monarcbuild.com/" + "/".join(p for p in (a.get("path1"), a.get("path2")) if p),
                         "page": ad.get("page"), "approvals": ad.get("approvals"), "ready": ad.get("ready"),
                         "published": ad.get("published"), "status": ad.get("status"),
                         "shot": self.page_shot(ad["page"]) if ad.get("page") else None}
        return out

    # ---- a copy of a landing page (2026-09-29): full-page pictures of the live page at 1440 and 390 wide, taken by
    # scripts/page_shot.py with the tracking hosts blocked, kept in projects/crm/shots/ and served at /shots/.

    _shot_lock = threading.Lock()

    def page_shot(self, url, make=False):
        import page_shot as ps
        try:
            ps.check(url)
        except ValueError as e:
            return {"ok": False, "errors": [str(e)]}
        if make:
            if not Api._shot_lock.acquire(timeout=120):
                return {"ok": False, "errors": ["Another copy is being taken. Try again in a minute."]}
            try:
                ps.shoot(url)
            except Exception as e:  # noqa: BLE001
                return {"ok": False, "errors": [f"Could not take a copy of the page: {type(e).__name__}: {str(e)[:160]}"]}
            finally:
                Api._shot_lock.release()
        p = ps.paths(url)
        if not all(x.exists() for x in p.values()):
            return {"ok": False, "missing": True, "url": url}
        at = min(x.stat().st_mtime for x in p.values())
        return {"ok": True, "url": url, "desktop": f"/shots/{p[1440].name}?v={int(at)}", "phone": f"/shots/{p[390].name}?v={int(at)}",
                "taken_at": datetime.fromtimestamp(at, self.s.clock.tz).isoformat()}

    # ---- the journey map's channel cards (Jonathan, 2026-10-01): each channel's tasks and the artifacts it needs to work,
    # from projects/crm/journey.json. Artifacts are read-only here: files from the repo (a path, a glob, or path#Heading
    # for one markdown section), and four kinds read live: ads-pages (per Google Ads campaign: the landing page's HTML,
    # its current copy, earlier copies, and the ad brief), site-pages, listings (the NAP directories), messages (the
    # Prospects base's LinkedIn message copy), and shorts (Monarc Studio's finished videos).

    JOURNEY = CRM_DIR / "journey.json"
    FILE_ROOTS = ("projects", "references", "templates", "archives", "context", "media")
    FILE_TYPES = {".md", ".txt", ".html", ".csv", ".json", ".jpg", ".jpeg", ".png", ".gs", ".pdf"}
    RAW_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".pdf": "application/pdf"}
    SITE = ROOT / "projects" / "monarcbuild-site" / "public_html"
    _journey_lock = threading.Lock()
    _messages = None  # (read at, rows) from the Prospects base's Messages table, kept 15 minutes

    def _rel(self, p):
        return str(Path(p).resolve().relative_to(ROOT.resolve())).replace("\\", "/")

    def _file_item(self, p, name=None, section=None):
        st = p.stat()
        return {"name": name or p.name, "path": self._rel(p) + (f"#{section}" if section else ""), "ext": p.suffix.lower(),
                "at": datetime.fromtimestamp(st.st_mtime, self.s.clock.tz).isoformat(), "kb": max(1, st.st_size // 1024)}

    def _files(self, paths):
        out = []
        for raw in paths:
            pat, _, section = raw.partition("#")
            hits = sorted(ROOT.glob(pat)) if any(ch in pat for ch in "*?[") else [ROOT / pat]
            out += [self._file_item(h, f"{h.name}: {section}" if section else None, section or None) for h in hits if h.is_file()]
        return out

    def _ads_pages(self):
        import ads_publish as ap
        import page_shot as ps
        out = []
        for doc in ap.all_campaigns():
            url = doc.get("page") or ""
            slug = urlparse(url).path.strip("/") or "home"
            html = self.SITE / slug / "index.html"
            shots = ps.paths(url) if url else {}
            current = [self._file_item(f, f"Current copy, {w} wide") for w, f in sorted(shots.items(), reverse=True) if f.exists()]
            history = sorted((ps.SHOTS / "history" / ps.slug_for(url)).glob("*.jpg"), reverse=True) if url else []
            names = {slug, slug.replace("_", ""), slug.replace("_", "-")}
            older = [p for p in (ROOT / "archives").glob("*/**/index.html") if p.parent.name in names] + \
                [p for p in (ROOT / "archives").glob("*/*.html") if any(n in p.parent.name for n in names if len(n) > 4)]
            older = sorted(set(older), key=lambda p: p.parent.name if p.name == "index.html" else p.parent.name + p.name, reverse=True)
            brief = sorted(ap.CAMPAIGNS.glob(f"{doc['nn']}-*.md"))
            out.append({"nn": doc["nn"], "name": doc.get("name"), "url": url,
                        "status": {"ENABLED": "Live", "PAUSED": "Paused"}.get((doc.get("google") or {}).get("status"), "Not published"),
                        "html": [self._file_item(html, "Page HTML, the site copy")] if html.exists() else [],
                        "current": current,
                        "earlier": [self._file_item(p, f"Copy {p.stem.replace('-', ' ')}") for p in history] +
                                   [self._file_item(p, f"HTML from {p.relative_to(ROOT / 'archives').parts[0]}") for p in older],
                        "brief": [self._file_item(p, "Ad brief") for p in brief]})
        return out

    def _site_pages(self):
        import page_shot as ps
        out = []
        for html in sorted(self.SITE.glob("*index.html")) + sorted(self.SITE.glob("*/index.html")):
            slug = html.parent.name if html.parent != self.SITE else ""
            if slug.startswith("_") or slug == "privacy":  # landing pages only
                continue
            url = f"https://monarcbuild.com/{slug + '/' if slug else ''}"
            shot = ps.paths(url)[1440]
            out.append({"name": "/" + (slug + "/" if slug else ""), "url": url, "html": self._file_item(html, "Page HTML"),
                        "shot": f"/shots/{shot.name}" if shot.exists() else None})
        return out

    def _listings(self):
        rows = sorted(self.s.rows("Listings"), key=lambda l: (l.get("Order") or 99, l.get("Directory") or ""))
        return [{"name": l.get("Directory") or "", "status": l.get("Status") or "To do", "url": l.get("Listing URL") or l.get("Link") or "",
                 "live_on": l.get("Live on") or ""} for l in rows]

    def _message_rows(self):
        if Api._messages and time.time() - Api._messages[0] < SHEET_TTL:
            return Api._messages[1]
        if not get_secret("AIRTABLE_API_KEY"):
            return {"error": "AIRTABLE_API_KEY is not set."}
        o = self.OUTREACH
        client = self.sheet_clients.get(("AIRTABLE_API_KEY", o["base"])) or Airtable(get_secret("AIRTABLE_API_KEY"), o["base"])
        self.sheet_clients[("AIRTABLE_API_KEY", o["base"])] = client
        try:
            recs = client.list_all("tbldpkFbd6tho2Hdm")[0]
        except Exception as e:  # noqa: BLE001
            return {"error": f"Could not read the Messages table: {str(e)[:160]}"}
        rows = [{"id": r["fields"].get("MSG ID") or "", "framework": r["fields"].get("Framework") or "",
                 "variation": r["fields"].get("Variation") or "", "copy": r["fields"].get("Copy") or ""} for r in recs]
        order = {"Connect": 0, "Post-Connect": 1, "Response": 2}
        rows.sort(key=lambda x: (order.get(x["variation"], 9), x["id"]))
        Api._messages = (time.time(), rows)
        return rows

    def journey(self, light=False):
        """light: the map only (labels, sources, tasks); the artifacts are read when a card opens."""
        cfg = json.loads(self.JOURNEY.read_text(encoding="utf-8"))
        if light:
            return cfg
        for node in cfg.get("nodes", []):
            for g in node.get("artifacts", []):
                self._resolve_group(g)
        return cfg

    def _resolve_group(self, g):
        """Fill one artifact group in place, by its kind. One bad group never blanks the page."""
        kind = g.get("kind")
        try:
            if kind == "files":
                g["items"] = self._files(g.get("paths", []))
            elif kind == "ads-pages":
                g["campaigns"] = self._ads_pages()
            elif kind == "site-pages":
                g["pages"] = self._site_pages()
            elif kind == "listings":
                g["listings"] = self._listings()
            elif kind == "messages":
                m = self._message_rows()
                g["messages"], g["error"] = (m, None) if isinstance(m, list) else ([], m.get("error"))
            elif kind == "shorts":
                g["items"] = [self._file_item(p) for p in sorted((ROOT / "media" / "ready").glob("*.mp4"), reverse=True)]
        except Exception as e:  # noqa: BLE001
            g["error"] = f"{type(e).__name__}: {str(e)[:160]}"
        return g

    # Records, Artifacts (Jonathan, 2026-10-02: "add artifacts on the left side of the record section, including the
    # offering PDF, sales script, just cold email scripts, LinkedIn connection messages ... segmented by categories that
    # they're used for, I guess, by icon"): projects/crm/artifacts.json, one category per use, each a list of groups
    # read the same way as the journey cards' artifacts.
    ARTIFACTS = CRM_DIR / "artifacts.json"

    def artifacts(self):
        cfg = json.loads(self.ARTIFACTS.read_text(encoding="utf-8"))
        # Tasks on the files (Jonathan, 2026-10-05: "Add the rewrites as tasks and those live in the artifacts as
        # well"): the open boxes of the tasks.md sections named in task_sections show on every group they name.
        sections = tuple(cfg.get("task_sections", []))
        boxes = [t for t in self.tasks()["tasks"] if sections and t["section"].startswith(sections)]
        for cat in cfg.get("categories", []):
            for g in cat.get("groups", []):
                self._resolve_group(g)
                g["tasks"] = self._group_tasks(g, boxes)
        return cfg

    # Butterfly (Jonathan, 2026-10-05: "It should literally just be a button. That's the logo. When I click on the
    # logo, there should just be three little options"): run a skill, make a new project, or work on one. A project is
    # an artifact, a campaign, or a skill. Each opens its chat with the clone in VS Code (scripts/crm_butterfly.py).
    def _butterfly_args(self):
        return self.s.rows("Campaigns"), self.s.rows("Sources"), json.loads(self.ARTIFACTS.read_text(encoding="utf-8"))

    def butterfly(self):
        return butterfly.menu(*self._butterfly_args())

    def butterfly_open(self, body):
        if body.get("skill"):
            return butterfly.run_skill(str(body["skill"]))
        return butterfly.open_project(str(body.get("id") or ""), *self._butterfly_args())

    def butterfly_new(self, body):
        kind, name = str(body.get("kind") or "").lower(), str(body.get("name") or "").strip()
        rec = None
        if kind == "campaign" and name:  # a campaign also gets its row in the base, Planned, under the channel he picked
            if not body.get("channel"):
                return 422, {"errors": ["Pick the channel the campaign runs on."]}
            status, out = self.save_record("Campaigns", {"Name": name, "Status": "Planned", "Channel": body["channel"],
                                                         "Notes": str(body.get("line") or "")})
            if status != 200:
                return status, out
            rec = out["record"]["id"]
        return butterfly.new_project(kind, name, str(body.get("line") or ""), campaign=rec)

    def _group_tasks(self, g, boxes):
        """The boxes that name one of the group's files. A glob counts up to its first wildcard; task_words names a
        group that has no file path (the ads, the call lists)."""
        words = [re.split(r"[*?\[#]", raw)[0] for raw in g.get("paths", [])] + list(g.get("task_words", []))
        return [t for t in boxes if any(w and w in t["full"] for w in words)]

    def journey_task(self, body):
        key, i = body.get("node"), body.get("i")
        with Api._journey_lock:
            cfg = json.loads(self.JOURNEY.read_text(encoding="utf-8"))
            node = next((n for n in cfg.get("nodes", []) if n.get("key") == key), None)
            if not node or not isinstance(i, int) or not 0 <= i < len(node.get("tasks", [])):
                return 422, {"errors": ["No such task."]}
            node["tasks"][i]["done"] = bool(body.get("done"))
            self.JOURNEY.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return 200, {"ok": True, "task": node["tasks"][i]}

    # ---- Records, Creative (Jonathan, 2026-10-05: "There should be a creative tab in the CRM that holds unpublished
    # media"). What is made and not yet out: the cuts joined on this laptop (media/looms), the shorts Monarc Studio
    # exported (media/ready), and the clips OpusClip holds for the projects named in projects/crm/creative.json. A
    # click plays one beside the list. "Mark published" moves it to the folded Published list; the mark lives in
    # creative.json and nothing is posted from here.

    CREATIVE = CRM_DIR / "creative.json"
    VIDEO_TYPES = {".mp4": "video/mp4", ".m4v": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm"}
    _creative_lock = threading.Lock()
    _opus_clips = {}  # project id -> (read at, clips or None, error or None)

    def _creative_cfg(self):
        try:
            cfg = json.loads(self.CREATIVE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cfg = {}
        cfg.setdefault("opusclip_projects", [])
        cfg.setdefault("published", {})
        # Since 2026-10-05 a mark is {"on": day or None, "posts": [{platform, id, url, on, state}]}: "on" is his hand
        # mark or a public post; posts are what youtube_api.py recorded (scripts/creative_record.py). An old plain
        # date string is read as a hand mark.
        for k, v in list(cfg["published"].items()):
            if isinstance(v, str):
                cfg["published"][k] = {"on": v, "posts": []}
            elif isinstance(v, dict):
                v.setdefault("on", None)
                v.setdefault("posts", [])
        return cfg

    def media_file(self, raw):
        """A video under media/ the Creative tab may play. Never a folder that starts with a dot (Studio's own store)."""
        p = (ROOT / (raw or "").replace("\\", "/").lstrip("/")).resolve()
        try:
            parts = p.relative_to(ROOT.resolve()).parts
        except ValueError:
            return None
        if len(parts) < 2 or parts[0] != "media" or p.suffix.lower() not in self.VIDEO_TYPES or not p.is_file():
            return None
        return None if any(x.startswith(".") for x in parts) else p

    def _opus_project_clips(self, pid):
        hit = Api._opus_clips.get(pid)
        if hit and time.time() - hit[0] < (300 if hit[1] is not None else 60):
            return hit[1], hit[2]
        key = get_secret("OPUSCLIP_API_KEY")
        clips, err = None, None
        if not key:
            err = "OPUSCLIP_API_KEY is not in secrets.env."
        else:
            try:
                r = requests.get("https://api.opus.pro/api/exportable-clips", headers={"Authorization": f"Bearer {key}"},
                                 params={"q": "findByProjectId", "projectId": pid, "pageSize": 50}, timeout=20)
                body = r.json()
                if r.status_code == 200:
                    clips = body if isinstance(body, list) else (body.get("data") or body.get("clips") or [])
                else:
                    err = f"OpusClip answered {r.status_code}: {str((body or {}).get('errorMessage') or '')[:120]}"
            except Exception as e:  # noqa: BLE001
                err = f"Could not reach OpusClip: {type(e).__name__}."
        Api._opus_clips[pid] = (time.time(), clips, err)
        return clips, err

    def creative(self):
        cfg = self._creative_cfg()
        published = cfg["published"]
        tz = self.s.clock.tz

        def local(p, where):
            st = p.stat()
            rel = self._rel(p)
            return {"key": "file:" + rel, "title": p.stem.replace("-", " ").replace("_", " "), "where": where, "path": rel,
                    "src": f"/api/media?path={quote(rel)}", "mb": round(st.st_size / 1048576, 1),
                    "at": datetime.fromtimestamp(st.st_mtime, tz).isoformat()}

        groups = []
        cuts = [p for p in sorted((ROOT / "media" / "looms").glob("*/*"), key=lambda p: p.stat().st_mtime, reverse=True)
                if p.suffix.lower() in self.VIDEO_TYPES and p.stem != "source"]
        groups.append({"key": "cuts", "label": "Cuts made on this laptop", "note": "Joined or trimmed here from his Looms. media/looms.",
                       "items": [dict(local(p, "Laptop"), sub=p.parent.name) for p in cuts]})
        # Loom B and A batches (2026-10-07): every finished cut by date, so a cut with no draft can still be watched and noted
        for day in sorted((ROOT / "media" / "loom-ba").glob("20??-??-??"), reverse=True):
            idx = {}
            try:
                idx = {r["slug"]: r for r in json.loads((day / "index.json").read_text(encoding="utf-8"))}
            except (OSError, ValueError, KeyError):
                pass
            vids = sorted(day.glob("*/*-loom-ba.mp4"))
            items = []
            for v in vids:
                slug = v.parent.name
                r = idx.get(slug, {})
                it = dict(local(v, "Loom B and A"), title=r.get("company") or slug, sub=("draft to " + r["to"]) if (r.get("draft") or {}).get("placed") else "no draft",
                          seconds=round(r.get("seconds") or 0), notes={"date": day.name, "slug": slug},
                          script=f"media/loom-ba/{day.name}/{slug}/director-script.md")
                items.append(it)
            if items:
                groups.insert(0, {"key": f"loom-ba:{day.name}", "label": f"Loom B and A, batch {day.name}",
                                  "note": f"Step-by-step cuts with his face. media/loom-ba/{day.name}. Leave notes under the player; they go to projects/loom-b-and-a/notes/{day.name}.json.",
                                  "items": items})
        ready = sorted((ROOT / "media" / "ready").glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        groups.append({"key": "studio", "label": "Monarc Studio shorts", "note": "Exported from Studio, ready for the scheduler. media/ready.",
                       "items": [local(p, "Studio") for p in ready]})
        with ThreadPoolExecutor(max_workers=4) as ex:  # the projects side by side, each kept five minutes
            results = list(ex.map(lambda pr: self._opus_project_clips(pr["id"]), cfg["opusclip_projects"]))
        for pr, (clips, err) in zip(cfg["opusclip_projects"], results):
            items = [{"key": f"opus:{c.get('id')}", "title": c.get("title") or "(no title)", "where": "OpusClip",
                      "src": c.get("uriForPreview") or c.get("uriForExport"), "download": c.get("uriForExport"),
                      "thumb": c.get("uriForThumbnail"), "seconds": round((c.get("durationMs") or 0) / 1000),
                      "note": c.get("description") or "", "at": c.get("createdAt")} for c in clips or []]
            groups.append({"key": "opus:" + pr["id"], "label": pr.get("title") or pr["id"],
                           "note": " · ".join(x for x in ("OpusClip", pr.get("made"), pr.get("note")) if x),
                           "error": err, "wait": None if err or items else "OpusClip has no clips for this yet. It may still be working.",
                           "items": items})
        out, done = [], []
        for g in groups:
            mine = [dict(i, published=(published.get(i["key"]) or {}).get("on"), posts=(published.get(i["key"]) or {}).get("posts") or [])
                    for i in g["items"]]
            done += [dict(i, group=g["label"]) for i in mine if i["published"]]
            out.append(dict(g, items=[i for i in mine if not i["published"]]))
        return {"groups": out, "published": sorted(done, key=lambda i: i["published"], reverse=True),
                "total": sum(len(g["items"]) for g in out)}

    def creative_mark(self, body):
        key = str(body.get("key") or "")
        if not re.match(r"^(file:media/|opus:)[\w ./()\-]+$", key):
            return 422, {"errors": ["That is not an item on the Creative tab."]}
        with Api._creative_lock:
            cfg = self._creative_cfg()
            rec = cfg["published"].setdefault(key, {"on": None, "posts": []})
            if body.get("published"):
                rec["on"] = self.s.clock.today().isoformat()
            else:
                rec["on"] = None
                if not rec["posts"]:
                    cfg["published"].pop(key, None)
            self.CREATIVE.write_text(json.dumps(cfg, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        return 200, {"ok": True, "key": key, "published": (cfg["published"].get(key) or {}).get("on")}

    def _safe_file(self, raw):
        """A repo file the artifact viewer may read: under one of FILE_ROOTS, one of FILE_TYPES, never records/ or a secret."""
        rel = (raw or "").partition("#")[0].replace("\\", "/").lstrip("/")
        p = (ROOT / rel).resolve()
        try:
            parts = p.relative_to(ROOT.resolve()).parts
        except ValueError:
            return None
        if not parts or parts[0] not in self.FILE_ROOTS or p.suffix.lower() not in self.FILE_TYPES or not p.is_file():
            return None
        if any(x.startswith(".") or x in ("records",) for x in parts) or "secret" in p.name.lower():
            return None
        return p

    def file_text(self, raw):
        p = self._safe_file(raw)
        if not p:
            return 404, {"errors": ["Not a file the viewer can open."]}
        if p.suffix.lower() in (".jpg", ".jpeg", ".png"):
            return 200, {"path": self._rel(p), "image": f"/api/raw?path={quote(self._rel(p))}"}
        if p.suffix.lower() == ".pdf":
            return 200, {"path": self._rel(p), "pdf": f"/api/raw?path={quote(self._rel(p))}"}
        text = p.read_text(encoding="utf-8", errors="replace")
        section = raw.partition("#")[2]
        if section:  # one markdown section: the heading and everything under it until the next heading of its level
            lines, out, level = text.splitlines(), [], None
            for ln in lines:
                m = re.match(r"^(#+)\s+(.*)$", ln)
                if m and level is None and m.group(2).strip().lower() == section.strip().lower():
                    level = len(m.group(1))
                elif m and level is not None and len(m.group(1)) <= level:
                    break
                if level is not None:
                    out.append(ln)
            text = "\n".join(out) or text
        cut = len(text) > 400_000
        return 200, {"path": self._rel(p), "ext": p.suffix.lower(), "text": text[:400_000], "cut": cut}

    def channel(self, name):
        s = self.s
        src = s.find("Sources", "Name", name)
        if not src:
            return None
        card = self._channel_card(src)
        leads = [l for l in s.rows("Leads") if src["id"] in (l.get("Source") or [])]
        camps = [c for c in s.rows("Campaigns") if src["id"] in (c.get("Channel") or [])]
        camp_ids = {c["id"] for c in camps}
        kws = [k for k in s.rows("Keywords") if (k.get("Campaign") or [None])[0] in camp_ids]
        pages = [p for p in s.rows("Landing pages") if (p.get("Campaign") or [None])[0] in camp_ids or not p.get("Campaign")]

        def attrib(match):
            return self._attrib([l for l in leads if match(l)])

        ads_cards = self._ads_cards() if card.get("type") == "Google Ads" else {}
        out_camps = [self._camp_row(c, card, leads, kws, ads_cards) for c in camps]
        out_kws = []
        for k in kws:
            a = attrib(lambda l, kid=k["id"]: kid in (l.get("Keyword") or []))
            camp = s.rec("Campaigns", (k.get("Campaign") or [None])[0])
            out_kws.append(dict(k, campaign_name=camp.get("Name") if camp else "", **a))
        out_pages = []
        for p in pages:
            a = attrib(lambda l, pid=p["id"]: pid in (l.get("Landing page") or []))
            camp = s.rec("Campaigns", (p.get("Campaign") or [None])[0])
            out_pages.append(dict(p, campaign_name=camp.get("Name") if camp else "", **a))
        out_leads = []
        for l in sorted(leads, key=lambda l: l.get("When") or "", reverse=True):
            comp = s.rec("Companies", (l.get("Company") or [None])[0])
            camp = s.rec("Campaigns", (l.get("Campaign") or [None])[0])
            kw = s.rec("Keywords", (l.get("Keyword") or [None])[0])
            pg = s.rec("Landing pages", (l.get("Landing page") or [None])[0])
            out_leads.append(dict(l, company_name=comp.get("Name") if comp else None, campaign_name=camp.get("Name") if camp else None,
                                  medium=self.lead_medium(l) if card.get("type") == "LinkedIn" else None,
                                  has_journey=bool(l.get("Journey")),
                                  keyword_text=kw.get("Keyword") if kw else None, page_url=pg.get("URL") if pg else None))
        out_kws.sort(key=lambda k: (-k["leads"], -(k.get("Clicks") or 0)))
        out_pages.sort(key=lambda p: (-p["leads"], p.get("URL") or ""))
        out_camps.sort(key=self._camp_order)
        out_listings = sorted((l for l in s.rows("Listings") if camp_ids & set(l.get("Campaign") or [])),
                              key=lambda l: (l.get("Order") or 99, l.get("Directory") or ""))
        out_threads = []
        for t in s.rows("LinkedIn threads"):
            if camp_ids & set(t.get("Campaign") or []):
                comp = s.rec("Companies", (t.get("Company") or [None])[0])
                out_threads.append(dict(t, company_name=comp.get("Name") if comp else None, outcome=self._thread_outcome(t)))
        out_threads.sort(key=lambda t: t.get("Last message") or t.get("Accepted") or t.get("Request sent") or "", reverse=True)
        mediums = self.linkedin_mediums(camps, leads, card.get("messaging")) if card.get("type") == "LinkedIn" else None
        return {"channel": card, "campaigns": out_camps, "keywords": out_kws, "landing_pages": out_pages, "leads": out_leads,
                "listings": out_listings, "threads": out_threads, "mediums": mediums}

    # ---- the day: meetings from Google Calendar, tasks from tasks.md (2026-09-23)
    # Since 2026-10-05 the calendar is read with the Monarc login (scripts/google_calendar_api.py), which owns his own
    # calendar and the booking calendar (config "calendars"); the booking script's agenda action stands in only when
    # that login is missing. A meeting he sent the invite for carries the guest's answer (Jonathan, 2026-10-05: "a
    # yellow status for pending confirmation, green for confirmed on the receiver side and red for decline"): read
    # from the event's guests, or, for an invite sent as a calendar file on a Proton email, from the replies in the
    # inbox. Every meeting ahead also gets an email reminder an hour before ("a push notification should be sent to me
    # an hour prior to every meeting to my email"): Google sends it to jonathan@monarcbuild.com and no guest sees it.

    AGENDA_DAYS = 14  # how far ahead meetings and invites are read, whatever the page asks for
    _gcal = None
    _reminded = set()  # event ids tried in this run, so a refused reminder is not asked for again on every read

    def agenda(self, days=2):
        """Events for today and the days after, each sent invite with its answer. The calendar read is cached five
        minutes; the invites sent by email ride on the inbox read. Never throws: Today degrades to tasks only."""
        s = self.s
        cache = getattr(s, "_agenda", None)
        now = time.time()
        if not (cache and cache["days"] == days and now - cache["at"] < (300 if cache["data"]["source"] == "ok" else 60)):
            cache = s._agenda = {"at": now, "days": days, "data": self._agenda_google(days) or self._agenda_script(days)}
        return self._with_mail_invites(cache["data"])

    def _agenda_script(self, days):
        url = get_secret("BOOKING_URL")
        if not url:
            return {"source": "not configured", "events": [], "note": "The calendar login is missing (python scripts/google_calendar_api.py --login) and BOOKING_URL is not in .env."}
        try:
            r = requests.get(url, params={"action": "agenda", "days": days}, timeout=12, allow_redirects=True)
            j = r.json()
            if j.get("ok") and isinstance(j.get("events"), list):
                return {"source": "ok", "events": j["events"], "tz": j.get("tz", "America/New_York")}
            if j.get("error") == "unknown action":
                return {"source": "old script", "events": [], "note": "The booking script online is an older version. Paste the file into the project and publish a new version; then meetings show here."}
            return {"source": "error", "events": [], "note": f"The booking script answered: {j.get('error') or r.status_code}."}
        except Exception as e:  # noqa: BLE001
            return {"source": "offline", "events": [], "note": f"Could not reach the booking script: {type(e).__name__}."}

    def _agenda_google(self, days):
        """Both calendars through the Monarc login. None when the login is not set up, so the booking script stands in."""
        s = self.s
        try:
            import google_calendar_api as gcal
            cal = Api._gcal = Api._gcal or gcal.Calendar()
        except Exception:  # noqa: BLE001  no refresh token, or the Google Ads client it borrows is missing
            return None
        now = s.clock.now()
        lo = datetime.combine(s.clock.today(), datetime.min.time(), s.clock.tz)
        hi = lo + timedelta(days=max(days, self.AGENDA_DAYS))
        cals = s.inst.get("calendars") or [{"id": "primary", "label": "Monarc"}]
        own = {c["id"] for c in cals}
        events, seen, failed, reminders = [], set(), [], 0
        for c in cals:
            label = c.get("label") or c["id"]
            try:
                items, defaults = cal.window(c["id"], lo, hi)
            except Exception as e:  # noqa: BLE001
                failed.append(f"{label}: {str(e)[:140]}")
                continue
            for ev in items:
                key = ev.get("iCalUID") or ev.get("id")
                if ev.get("status") == "cancelled" or key in seen:
                    continue
                seen.add(key)
                st, en = ev.get("start") or {}, ev.get("end") or {}
                all_day = "date" in st
                people = ev.get("attendees") or []
                events.append({
                    "id": ev.get("id"), "title": ev.get("summary") or "(no title)",
                    "start": st.get("date") if all_day else st.get("dateTime"), "end": en.get("date") if all_day else en.get("dateTime"),
                    "all_day": all_day, "calendar": label, "meet": ev.get("hangoutLink") or "", "location": ev.get("location") or "",
                    "link": ev.get("htmlLink") or "",
                    "guests": [a.get("displayName") or a.get("email") for a in people if not a.get("self") and not a.get("organizer")][:4],
                    "invite": self._invite_of(ev, own)})
                declined = any(a.get("self") and a.get("responseStatus") == "declined" for a in people)
                if (not all_day and not declined and ev.get("id") not in Api._reminded and self._instant(st.get("dateTime")) > now.timestamp()
                        and not cal.has_email_reminder(ev, defaults)):
                    Api._reminded.add(ev["id"])
                    try:
                        cal.remind_by_email(c["id"], ev, defaults)
                        reminders += 1
                    except Exception as e:  # noqa: BLE001
                        failed.append(f"no email reminder on {ev.get('summary') or 'a meeting'}: {str(e)[:140]}")
        if len(failed) >= len(cals) and not events:
            return {"source": "error", "events": [], "note": "Google Calendar did not answer. " + " ".join(failed)}
        events.sort(key=self._start_key)
        return {"source": "ok", "events": events, "tz": str(s.clock.tz), "reminders_added": reminders,
                "note": " ".join(failed) if failed else None}

    @staticmethod
    def _instant(iso):
        try:
            return datetime.fromisoformat(str(iso).replace("Z", "+00:00")).timestamp()
        except (TypeError, ValueError):
            return 0.0

    def _start_key(self, ev):
        if ev.get("all_day"):
            return str(ev.get("start"))[:10]
        return datetime.fromtimestamp(self._instant(ev.get("start")), self.s.clock.tz).isoformat()

    @staticmethod
    def _invite_status(guests):
        """One status for the meeting: confirmed once a guest said yes, declined when every guest said no, pending until then."""
        said = [g["status"] for g in guests]
        return "confirmed" if "confirmed" in said else "declined" if said and all(x == "declined" for x in said) else "pending"

    def _invite_of(self, ev, own):
        """The guests of a meeting he sent the invite for, each with an answer. None for someone else's meeting and
        for one with no guest but him (his own test bookings are that)."""
        org = ev.get("organizer") or {}
        if not (org.get("self") or org.get("email") in own or is_self({"Email": org.get("email")})):
            return None
        word = {"accepted": "confirmed", "declined": "declined"}
        guests = [{"name": a.get("displayName") or a.get("email"), "email": (a.get("email") or "").lower(),
                   "status": word.get(a.get("responseStatus"), "pending"), "maybe": a.get("responseStatus") == "tentative"}
                  for a in ev.get("attendees") or []
                  if not a.get("self") and not a.get("resource") and not is_self({"Email": a.get("email")})]
        return {"status": self._invite_status(guests), "source": "calendar", "guests": guests} if guests else None

    def _with_mail_invites(self, data):
        """The calendar read with the invites sent by email laid over it: onto the hold at the same time when there is
        one (the hold has no guest, the email has), as a meeting of its own when there is not."""
        mail = self.mail()
        out = dict(data, events=[dict(e) for e in data.get("events") or []], invites_mail=mail.get("bridge"))
        for inv in mail.get("invites") or []:
            at = self._instant(inv["start"])
            card = {"status": inv["status"], "source": "email", "guests": inv["guests"], "sent_at": inv["sent_at"],
                    "replied_at": inv.get("replied_at"), "reply_uid": inv.get("reply_uid")}
            names = [g["name"] for g in inv["guests"]][:4]
            hold = next((e for e in out["events"] if not e.get("all_day") and not e.get("error") and not e.get("invite")
                         and self._instant(e.get("start")) == at), None)
            if hold:
                hold["invite"] = card
                hold["guests"] = hold.get("guests") or names
            else:
                out["events"].append({"id": "mail:" + inv["uid"], "title": inv["title"], "start": inv["start"], "end": inv["end"],
                                      "all_day": False, "calendar": "Email invite", "meet": inv["meet"], "location": inv["location"],
                                      "link": "", "guests": names, "invite": card})
        out["events"].sort(key=self._start_key)
        return out

    # ---- mail (2026-09-29, Jonathan: the top of Today is "a brief on my email inbox, any draft emails that I need to
    # approve for send, as well as a view of my Google Calendar"). Proton through Bridge on this laptop, with the
    # helpers in scripts/proton_mail.py. Read only: every fetch is BODY.PEEK (nothing gets marked read), and nothing
    # here can send; drafts are sent by Jonathan from Proton. Cached two minutes; the top bar's refresh reads again.

    MAIL_TTL = 120
    _mail = None

    def _mail_when(self, msg):
        """The Date header in Eastern, so dates from every sender sort together."""
        from email.utils import parsedate_to_datetime
        try:
            d = parsedate_to_datetime(msg.get("Date"))
            return (d if d.tzinfo else d.replace(tzinfo=self.s.clock.tz)).astimezone(self.s.clock.tz).isoformat()
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _text(msg, limit):
        """A message's plain text with HTML entities turned back into characters (&#x27; into ')."""
        import html
        import proton_mail as pm
        return html.unescape(pm.body_text(msg, limit))

    @staticmethod
    def _who(raw):
        from email.utils import getaddresses
        pairs = getaddresses([raw or ""])
        return ", ".join((n or a) for n, a in pairs if n or a) or raw or ""

    @staticmethod
    def _uids(m, criteria="ALL"):
        typ, data = m.uid("SEARCH", None, criteria)
        return data[0].split() if typ == "OK" and data and data[0] else []

    @staticmethod
    def _fetch(m, uid, what):
        typ, data = m.uid("FETCH", uid, what)
        raw, flags = b"", ""
        for item in data or []:
            if isinstance(item, tuple):
                flags, raw = item[0].decode(errors="replace"), item[1]
        return raw, flags

    _mail_lock = threading.Lock()  # the inbox panel and the calendar both ask on a cold Today; one read serves both

    def mail(self, force=False):
        if not force and Api._mail and time.time() - Api._mail["at"] < self.MAIL_TTL:
            return Api._mail["data"]
        with Api._mail_lock:
            if not force and Api._mail and time.time() - Api._mail["at"] < self.MAIL_TTL:
                return Api._mail["data"]
            try:
                data = self._mail_read()
            except SystemExit as e:  # proton_mail.connect() exits when Bridge is closed or signed out
                data = {"bridge": "down", "note": "Proton Mail Bridge is closed or signed out. Open Bridge and sign in; the inbox shows here on the next refresh.",
                        "detail": str(e)[:200]}
            except Exception as e:  # noqa: BLE001  Today still renders without mail
                data = {"bridge": "error", "note": f"Could not read the inbox: {type(e).__name__}: {str(e)[:160]}"}
            data["read_at"] = datetime.now(self.s.clock.tz).isoformat()
            Api._mail = {"at": time.time(), "data": data}
            return data

    # ---- invites sent as a calendar file on a Proton email (2026-10-05). The route for a prospect in another time
    # zone (CLAUDE.md): the hold on his calendar has no guest, so the answer is not on the event. It comes back as a
    # calendar reply in the inbox that carries the invite's own id. Read only, like the rest of the mail.

    INVITE_BACK = 45  # days of Sent read for invites
    FREE_MAIL = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "icloud.com", "me.com", "msn.com",
                 "live.com", "comcast.net", "att.net", "verizon.net", "sbcglobal.net", "proton.me", "protonmail.com"}

    @staticmethod
    def _imap_date(d):
        return f"{d.day:02d}-{'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()[d.month - 1]}-{d.year}"

    @staticmethod
    def _ics_parts(msg):
        """Every calendar part of a message as text, the folded lines joined."""
        out = []
        for p in msg.walk():
            if p.get_content_type() == "text/calendar" or (p.get_filename() or "").lower().endswith(".ics"):
                raw = p.get_payload(decode=True) or b""
                out.append(re.sub(r"\r?\n[ \t]", "", raw.decode(p.get_content_charset() or "utf-8", "replace")))
        return out

    @staticmethod
    def _ics_event(text, home_tz):
        """What one calendar part says: REQUEST or REPLY, the invite's id, when, and each guest's answer."""
        block = re.search(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S)
        if not block:
            return None
        body = block.group(1)

        def line(name):
            m = re.search(rf"^{name}([;:].*)$", body, re.M)
            return m.group(1).strip() if m else ""

        def value(name):
            return line(name).split(":", 1)[-1].replace("\\,", ",").replace("\\;", ";").replace("\\n", " ").strip()

        def when(name):
            raw = line(name)
            val = raw.rsplit(":", 1)[-1]
            try:
                if val.endswith("Z"):
                    return datetime.strptime(val, "%Y%m%dT%H%M%SZ").replace(tzinfo=ZoneInfo("UTC"))
                if "T" in val:
                    tzid = re.search(r"TZID=([^;:]+)", raw)
                    try:
                        tz = ZoneInfo(tzid.group(1).strip('"')) if tzid else home_tz
                    except Exception:  # noqa: BLE001  a zone name Windows does not know
                        tz = home_tz
                    return datetime.strptime(val, "%Y%m%dT%H%M%S").replace(tzinfo=tz)
            except ValueError:
                pass
            return None  # an all-day invite has no hour to remind on

        word = {"ACCEPTED": "confirmed", "DECLINED": "declined"}
        guests = []
        for a in re.findall(r"^ATTENDEE([;:].*)$", body, re.M):
            addr = re.search(r"mailto:([^\s;>\"]+)", a, re.I)
            if not addr:
                continue
            cn = re.search(r'CN=("[^"]*"|[^;:]*)', a)
            part = (re.search(r"PARTSTAT=([A-Za-z-]+)", a) or [None, ""])[1].upper()
            guests.append({"name": (cn.group(1).strip('"') if cn else "") or addr.group(1), "email": addr.group(1).lower(),
                           "status": word.get(part, "pending"), "maybe": part == "TENTATIVE"})
        method = re.search(r"^METHOD:(\w+)", text, re.M)
        return {"method": method.group(1).upper() if method else "", "uid": value("UID"), "start": when("DTSTART"),
                "end": when("DTEND"), "title": value("SUMMARY"), "location": value("LOCATION"), "guests": guests}

    def _sent_invites(self, m):
        """Each invite in Sent for a meeting from today on, with the guest's answer from the inbox. A second invite to
        the same guest for the same time replaces the first."""
        import email as email_lib
        import proton_mail as pm
        tz, today = self.s.clock.tz, self.s.clock.today()
        since = self._imap_date(today - timedelta(days=self.INVITE_BACK))
        if m.select('"Sent"', readonly=True)[0] != "OK":
            return []
        found = {}
        for uid in self._uids(m, f"SINCE {since}"):
            typ, data = m.uid("FETCH", uid, "(BODYSTRUCTURE)")  # the shape only, so no body is read for plain mail
            shape = b" ".join(x if isinstance(x, bytes) else b" ".join(y for y in x if isinstance(y, bytes)) for x in data or [] if x)
            if typ == "OK" and not re.search(rb"calendar|\.ics", shape, re.I):
                continue
            raw, _ = self._fetch(m, uid, "(BODY.PEEK[])")
            msg = email_lib.message_from_bytes(raw)
            sent = self._mail_when(msg)
            for text in self._ics_parts(msg):
                ev = self._ics_event(text, tz)
                if not ev or ev["method"] != "REQUEST" or not ev["start"] or ev["start"].astimezone(tz).date() < today:
                    continue
                guests = [g for g in ev["guests"] if not is_self({"Email": g["email"]})]
                if not guests:
                    continue
                key = (guests[0]["email"], ev["start"].timestamp())
                if key in found and (found[key]["sent_at"] or "") >= (sent or ""):
                    continue
                end = ev["end"] or ev["start"] + timedelta(minutes=15)
                found[key] = {"uid": ev["uid"], "title": ev["title"] or pm.hdr(msg, "Subject"), "start": ev["start"].astimezone(tz).isoformat(),
                              "end": end.astimezone(tz).isoformat(), "location": ev["location"],
                              "meet": ev["location"] if ev["location"].startswith("http") else "", "guests": guests,
                              "status": self._invite_status(guests), "sent_at": sent, "subject": pm.hdr(msg, "Subject"),
                              "replied_at": None, "reply_uid": None}
        invites = list(found.values())
        if not invites or m.select('"INBOX"', readonly=True)[0] != "OK":
            return invites
        by_uid = {i["uid"]: i for i in invites}
        needle = {}  # what to look for in From: the guest's company domain, or the whole address on a free mail host
        for i in invites:
            for g in i["guests"]:
                dom = g["email"].rpartition("@")[2]
                needle[g["email"] if dom in self.FREE_MAIL else "@" + dom] = i
        pool = set()
        for crit in [f'SINCE {since} SUBJECT "{w}"' for w in ("Accepted", "Declined", "Tentative")] + [f'SINCE {since} FROM "{n}"' for n in needle]:
            pool.update(self._uids(m, crit))
        answered = {}  # invite uid -> when its latest calendar reply came
        for uid in sorted(pool, key=int):
            raw, _ = self._fetch(m, uid, "(BODY.PEEK[])")
            msg = email_lib.message_from_bytes(raw)
            at = self._mail_when(msg) or ""
            reply = False
            for text in self._ics_parts(msg):
                ev = self._ics_event(text, tz)
                inv = by_uid.get(ev["uid"]) if ev and ev["method"] == "REPLY" else None
                if not inv:
                    continue
                reply = True
                if at < answered.get(inv["uid"], ""):
                    continue
                answered[inv["uid"]] = at
                for r in ev["guests"]:
                    g = next((x for x in inv["guests"] if x["email"] == r["email"]), inv["guests"][0])
                    g["status"], g["maybe"] = r["status"], r["maybe"]
            if reply:
                continue
            # a plain email from the guest after the invite went out: not an answer the CRM can read, so it says they wrote
            frm = pm.hdr(msg, "From").lower()
            inv = next((i for n, i in needle.items() if n in frm), None)
            if inv and at > (inv["sent_at"] or "") and at > (inv["replied_at"] or ""):
                inv["replied_at"], inv["reply_uid"] = at, uid.decode()
        for i in invites:
            i["status"] = self._invite_status(i["guests"])
        return invites

    def _mail_read(self):
        import email as email_lib
        import proton_mail as pm
        m = pm.connect()
        try:
            own = pm.load_env().get("PROTON_USER", "")
            m.select('"INBOX"', readonly=True)
            uids = self._uids(m)
            unseen = set(self._uids(m, "UNSEEN"))
            inbox, counts = [], {}
            for uid in reversed(uids[-40:]):
                raw, flags = self._fetch(m, uid, "(FLAGS BODY.PEEK[HEADER])")
                msg = email_lib.message_from_bytes(raw)
                kind = pm.classify(msg, own)
                counts[kind] = counts.get(kind, 0) + 1
                inbox.append({"uid": uid.decode(), "kind": kind, "from": self._who(pm.hdr(msg, "From")),
                              "subject": pm.hdr(msg, "Subject"), "at": self._mail_when(msg), "unread": "\\Seen" not in flags})
            # the latest AIOS brief: the flagged report the /inbox pass leaves in INBOX
            report = None
            rep = self._uids(m, f'SUBJECT "{pm.REPORT_SUBJECT_PREFIX}"')
            if rep:
                raw, _ = self._fetch(m, rep[-1], "(BODY.PEEK[])")
                msg = email_lib.message_from_bytes(raw)
                report = {"uid": rep[-1].decode(), "subject": pm.hdr(msg, "Subject"), "at": self._mail_when(msg),
                          "body": self._text(msg, 4000)}
            # what needs a look since the brief: not from Jonathan or Patrick, not on a thread, not a report; newest first
            inbox.sort(key=lambda x: x["at"] or "", reverse=True)
            # meeting replies (2026-10-01, Jonathan: "notify me when they opt in to the meeting"): Google mails every
            # guest's answer to the organizer, jonathan@monarcbuild.com, so an invite he sends from that account comes
            # back here as "Accepted: ...", "Declined: ...", and the rest; the panel shows them first
            rsvp = re.compile(r"^(Accepted|Declined|Tentatively accepted|Maybe|Proposed new time)\b", re.I)
            replies = [dict(r, reply=rsvp.match(r["subject"] or "").group(1).capitalize())
                       for r in inbox if rsvp.match(r["subject"] or "")][:6]
            since = (report or {}).get("at")
            pool = [r for r in inbox if r["kind"] == "review" and (not since or (r["at"] or "") > since)]
            review = pool[:8]
            for r in review:
                raw, _ = self._fetch(m, r["uid"].encode(), "(BODY.PEEK[])")
                r["snippet"] = self._text(email_lib.message_from_bytes(raw), 400).replace("\n", " ")[:220]
            # drafts waiting for Jonathan to read and send from Proton
            m.select('"Drafts"', readonly=True)
            duids = self._uids(m)
            drafts = []
            for uid in duids[-40:]:  # Proton's ids are not in date order; read them all, then sort by date
                raw, _ = self._fetch(m, uid, "(BODY.PEEK[])")
                msg = email_lib.message_from_bytes(raw)
                body = self._text(msg, 4000)
                drafts.append({"uid": uid.decode(), "to": self._who(pm.hdr(msg, "To")), "subject": pm.hdr(msg, "Subject"),
                               "at": self._mail_when(msg), "snippet": body.replace("\n", " ")[:220],
                               "attachments": sum(1 for p in msg.walk() if p.get_filename()),
                               "video": self.loom_ba_video(body)})
            drafts.sort(key=lambda x: x["at"] or "", reverse=True)
            try:
                invites = self._sent_invites(m)
            except Exception:  # noqa: BLE001  the inbox and the drafts still show
                invites = []
            return {"bridge": "ok", "total": len(uids), "unread": len(unseen), "counts": counts, "report": report,
                    "review": review, "review_since": len(pool), "since": since, "drafts": drafts, "drafts_total": len(duids),
                    "replies": replies, "invites": invites}
        finally:
            try:
                m.logout()
            except Exception:  # noqa: BLE001
                pass

    # His notes on each Loom B and A cut (Jonathan, 2026-10-07: "I will leave notes on each video for where it went wrong so
    # the SOP can be adjusted"): one file a batch, projects/loom-b-and-a/notes/<date>.json, {slug: [{at, text, on}]}. The
    # clone reads it in the batch workflow's notes step, recuts, and writes what holds into references/content-rules.md.
    LOOM_BA_NOTES = ROOT / "projects" / "loom-b-and-a" / "notes"
    _loom_notes_lock = threading.Lock()

    def _loom_notes_file(self, date):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date or ""):
            return None
        return self.LOOM_BA_NOTES / f"{date}.json"

    def loom_ba_notes_get(self, date, slug):
        f = self._loom_notes_file(date)
        if not f or not re.match(r"^[a-z0-9-]+$", slug or ""):
            return 422, {"errors": ["A batch date and a company slug, please."]}
        data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        return 200, {"date": date, "slug": slug, "notes": data.get(slug, [])}

    def loom_ba_notes_post(self, body):
        date, slug = str(body.get("date") or ""), str(body.get("slug") or "")
        f = self._loom_notes_file(date)
        if not f or not re.match(r"^[a-z0-9-]+$", slug):
            return 422, {"errors": ["A batch date and a company slug, please."]}
        with Api._loom_notes_lock:
            data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
            notes = data.setdefault(slug, [])
            if body.get("remove") is not None:
                i = int(body["remove"])
                if 0 <= i < len(notes):
                    notes.pop(i)
            else:
                text = str(body.get("text") or "").strip()
                if not text:
                    return 422, {"errors": ["The note is empty."]}
                at = body.get("at")
                notes.append({"at": round(float(at), 1) if at is not None else None, "text": text[:2000],
                              "on": datetime.now(self.s.clock.tz).isoformat(timespec="minutes")})
                notes.sort(key=lambda n: (n["at"] is None, n["at"] or 0))
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        return 200, {"date": date, "slug": slug, "notes": notes}

    LOOM_BA_LINK = re.compile(r"monarcbuild\.com/v/([0-9a-f]{10})/?")

    def loom_ba_video(self, text):
        """The finished Loom B and A cut a draft links to (Jonathan, 2026-10-06: "show me final renders in the crm under the
        waiting email approvals"). A draft carries https://monarcbuild.com/v/<token>/; the batch built that page from the cut
        in media/loom-ba/<date>/_site/v/<token>/, so the token finds the video on this laptop, playable before the page is live."""
        m = self.LOOM_BA_LINK.search(text or "")
        if not m:
            return None
        tok = m.group(1)
        for site in (ROOT / "media" / "loom-ba").glob(f"*/_site/v/{tok}"):
            vid = site / "video.mp4"
            if not vid.is_file():
                continue
            date = site.parents[2].name
            info = {}
            idx = site.parents[2] / "index.json"
            try:
                for row in json.loads(idx.read_text(encoding="utf-8")):
                    if (row.get("link") or "").rstrip("/").endswith(tok):
                        info = row
                        break
            except (OSError, ValueError):
                pass
            rel = vid.relative_to(ROOT).as_posix()
            return {"src": f"/api/media?path={quote(rel)}", "path": rel, "token": tok, "date": date, "slug": info.get("slug"),
                    "company": info.get("company"), "seconds": info.get("seconds"), "link": f"https://monarcbuild.com/v/{tok}/",
                    "live": False, "script": (f"media/loom-ba/{date}/{info['slug']}/director-script.md" if info.get("slug") else None)}
        return {"src": None, "token": tok, "missing": True}

    def mail_message(self, folder, uid):
        """One message or draft in full, read only, for the reader on Today."""
        import email as email_lib
        import proton_mail as pm
        if folder not in ("INBOX", "Drafts") or not str(uid).isdigit():
            return {"ok": False, "errors": ["Only INBOX and Drafts, by message id."]}
        try:
            m = pm.connect()
        except SystemExit:
            return {"ok": False, "errors": ["Proton Mail Bridge is closed or signed out."]}
        try:
            m.select(f'"{folder}"', readonly=True)
            raw, _ = self._fetch(m, str(uid).encode(), "(BODY.PEEK[])")
            if not raw:
                return {"ok": False, "errors": ["That message is gone (sent, moved, or edited)."]}
            msg = email_lib.message_from_bytes(raw)
            return {"ok": True, "folder": folder, "uid": uid, "from": pm.hdr(msg, "From"), "to": pm.hdr(msg, "To"),
                    "cc": pm.hdr(msg, "Cc"), "subject": pm.hdr(msg, "Subject"), "at": self._mail_when(msg),
                    "attachments": [str(pm.make_header(pm.decode_header(p.get_filename()))) for p in msg.walk() if p.get_filename()],
                    "body": self._text(msg, 12000), "video": self.loom_ba_video(self._text(msg, 12000)) if folder == "Drafts" else None}
        finally:
            try:
                m.logout()
            except Exception:  # noqa: BLE001
                pass

    TASKS_PATH = ROOT / "tasks.md"

    def tasks(self):
        """Open boxes in tasks.md with the tier they sit in. Line numbers let the Done button find the exact line."""
        out = []
        if not self.TASKS_PATH.exists():
            return {"tasks": out}
        section = ""
        for i, line in enumerate(self.TASKS_PATH.read_text(encoding="utf-8").splitlines(), start=1):
            m = re.search(r"<summary>(.*?)</summary>", line)
            if m:
                section = re.sub(r"<[^>]+>", "", m.group(1)).split("·")[0].strip()
                continue
            if line.lstrip().startswith("- [ ] "):
                full = line.strip()[6:].strip()
                short = re.split(r"(?<=[.!?])\s", full, maxsplit=1)[0]
                short = re.sub(r"\*\*|`", "", short)
                if len(short) > 150:
                    short = short[:147].rstrip() + "..."
                out.append({"line": i, "section": section, "text": short, "full": full})
        return {"tasks": out}

    def task_done(self, body):
        line_no = int(body.get("line") or 0)
        full = (body.get("full") or "").strip()
        lines = self.TASKS_PATH.read_text(encoding="utf-8").splitlines(keepends=True)
        if not (1 <= line_no <= len(lines)):
            return 404, {"errors": ["No such line in tasks.md."]}
        cur = lines[line_no - 1]
        if not cur.lstrip().startswith("- [ ] ") or cur.strip()[6:].strip() != full:
            return 409, {"errors": ["tasks.md changed under you. Reload and try again."]}
        stamp = self.s.clock.today().isoformat()
        lines[line_no - 1] = cur.replace("- [ ] ", "- [x] ", 1).rstrip("\r\n") + f" Done {stamp}.\n"
        self.TASKS_PATH.write_text("".join(lines), encoding="utf-8")
        return 200, {"done": True, "line": line_no, "date": stamp}

    # ---- money: reads the Books base (a second base, same token). Since 2026-09-28 the Books base is the money side of
    # the CRM: every won deal has a Clients row there (sync_books_clients), invoices link to it, and its rollups add up.

    BOOKS_TABLES = ("Accounts", "Transactions", "Invoices", "Months", "Clients")

    def _books_air(self):
        """One client for the Books base, kept, so a Money visit reuses its connection (2026-10-02)."""
        base_id = self.s.inst.get("books_base_id")
        if not (base_id and self.s.air.ready):
            return None
        air = getattr(self.s, "_books_client", None)
        if air is None or air.base != base_id:
            air = self.s._books_client = Airtable(self.s.air.token, base_id)
        return air

    def _load_books(self, force=False):
        """The Books base, cached CACHE_TTL. Clients may be missing on an older copy; it then reads empty. A refusal
        (the base not on the token) is remembered for CACHE_TTL too, so Money does not ask again on every visit."""
        s = self.s
        books = getattr(s, "_books", None)
        now = time.time()
        if books and not force and now - books["at"] <= CACHE_TTL:
            return books["data"]
        err = getattr(s, "_books_err", None)
        if err and not force and now - err[0] <= CACHE_TTL:
            raise err[1]
        air = self._books_air()
        data = {}
        try:
            for t in self.BOOKS_TABLES:
                try:
                    data[t] = [dict(r["fields"], id=r["id"]) for r in air.list_all(t)[0]]
                except AirtableError:
                    if t != "Clients":
                        raise
                    data[t] = []
        except AirtableError as e:
            s._books_err = (now, e)
            raise
        s._books_err = None
        s._books = {"at": now, "data": data}
        s.air.calls += air.calls
        return data

    def _client_fields(self, deal):
        """What the CRM owns on a Books Clients row, from one won deal."""
        s = self.s
        comp = s.rec("Companies", (deal.get("Company") or [None])[0]) or {}
        src = s.rec("Sources", (deal.get("Source") or comp.get("Source") or [None])[0]) or {}
        changed = s.clock.to_local(deal.get("Stage changed"))
        return {"Client": comp.get("Name") or deal.get("Deal") or "", "Monthly fee": float(deal.get("Value") or 0),
                "Offer": deal.get("Offer") or "", "Signed on": changed.date().isoformat() if changed else deal.get("Close date"),
                "Source": src.get("Label") or src.get("Name") or "", "CRM deal id": deal["id"], "CRM company id": comp.get("id") or ""}

    def sync_books_clients(self, data=None):
        """Every won deal in the CRM has one Clients row in the Books base, matched on CRM deal id. Creates the missing
        ones (Status Active) and updates what the CRM owns when it changed. Never writes Status or Notes after the
        first write, and never moves Signed on once set. No API call when nothing changed."""
        s = self.s
        air = self._books_air()
        if not air:
            return {"created": 0, "updated": 0}
        data = data if data is not None else self._load_books()
        rows = data.get("Clients", [])
        by_deal = {r.get("CRM deal id"): r for r in rows if r.get("CRM deal id")}
        creates, updates = [], []
        for d in s.rows("Deals"):
            if not d.get("Won"):
                continue
            want = self._client_fields(d)
            have = by_deal.get(d["id"])
            if not have:
                creates.append(dict(want, Status="Active"))
                continue
            diff = {k: v for k, v in want.items()
                    if (have.get(k) or None) != (v or None) and not (k == "Signed on" and have.get("Signed on"))}
            if diff:
                updates.append((have["id"], diff))
        if creates:
            rows.extend(dict(r["fields"], id=r["id"]) for r in air.create("Clients", creates))
        if updates:
            air.update("Clients", updates)
            for rid, f in updates:
                next(r for r in rows if r["id"] == rid).update(f)
        s.air.calls += air.calls
        data["Clients"] = rows
        return {"created": len(creates), "updated": len(updates)}

    def money(self):
        s = self.s
        base_id = s.inst.get("books_base_id")
        if not base_id or not s.air.ready:
            return {"ready": False, "reason": "Books base not configured. Set books_base_id in projects/crm/config.json and give the token access."}
        try:
            data = self._load_books()
        except AirtableError as e:
            s.last_error = str(e)
            return {"ready": False, "reason": "The Books base is not on the Airtable token yet. At airtable.com/create/tokens, "
                                              "edit the token and add the base \"Monarc Books\" to its access list, then reload this page."}
        sync_note = None
        try:
            self.sync_books_clients(data)
        except (AirtableError, requests.RequestException) as e:
            sync_note = f"Could not write won deals into the Books Clients table: {str(e)[:200]}"
        accounts = {a["id"]: a for a in data["Accounts"]}
        today = s.clock.today()
        this_m = today.strftime("%Y-%m")
        last_m = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

        def summarize(month):
            txs = [t for t in data["Transactions"] if (t.get("Date") or "").startswith(month)]
            rev = cost = 0.0
            by = {}
            unl = 0
            for t in txs:
                amt = float(t.get("Amount") or 0)
                a = accounts.get((t.get("Account") or [None])[0])
                if not a:
                    unl += 1
                    continue
                by.setdefault(a.get("Name"), {"name": a.get("Name"), "type": a.get("Type"), "amount": 0.0})["amount"] += amt
                if a.get("Type") == "Revenue":
                    rev += amt
                elif a.get("Type") == "Cost":
                    cost += -amt
            return {"month": month, "revenue": round(rev, 2), "costs": round(cost, 2), "profit": round(rev - cost, 2),
                    "rows": len(txs), "unlabeled": unl, "unreconciled": sum(1 for t in txs if not t.get("Reconciled")),
                    "by_account": sorted(by.values(), key=lambda x: x["amount"])}

        clients = data.get("Clients", [])
        names = {c["id"]: c.get("Client") or "" for c in clients}
        invoices = sorted((dict(i, client_name=", ".join(names.get(x, "") for x in (i.get("Client") or [])) or i.get("Client (old text)") or "")
                           for i in data["Invoices"]), key=lambda i: i.get("Issued") or "", reverse=True)
        open_inv = [i for i in invoices if i.get("Status") in ("Sent", "Late")]
        months = sorted(data["Months"], key=lambda m: m.get("Month") or "", reverse=True)[:12]
        active = [c for c in clients if c.get("Status", "Active") == "Active"]
        return {"ready": True, "this_month": summarize(this_m), "last_month": summarize(last_m) if any((t.get("Date") or "").startswith(last_m) for t in data["Transactions"]) else None,
                "open_invoices": len(open_inv), "late_invoices": sum(1 for i in open_inv if i.get("Status") == "Late"),
                "open_invoices_value": sum(float(i.get("Amount") or 0) for i in open_inv),
                "invoices": invoices[:50], "months": months, "accounts": list(accounts.values()),
                "clients": sorted(clients, key=lambda c: (c.get("Status", "Active") != "Active", c.get("Signed on") or "")),
                "active_clients": len(active), "mrr": sum(float(c.get("Monthly fee") or 0) for c in active),
                "sync_note": sync_note}

    # ---- generic record save for the workspace tables

    def save_record(self, table, body):
        s = self.s
        if table not in SAVE_FIELDS:
            return 404, {"errors": ["Unknown table."]}
        rid = body.pop("id", None)
        f = {k: body[k] for k in SAVE_FIELDS[table] if k in body}
        for k in list(f):
            if k in LINK_FIELDS:
                v = f[k]
                f[k] = [v] if isinstance(v, str) and v else (v if isinstance(v, list) else [])
            elif k == "NAP matches":  # a checkbox arrives from the form as text
                f[k] = f[k] in (True, "true", "yes", "Yes", "on", "1")
            elif f[k] == "":
                f[k] = None
        for k in ("Daily budget", "Spend to date", "Impressions", "Clicks", "Form fields"):
            if f.get(k) not in (None, ""):
                f[k] = float(f[k])
        primary = SAVE_FIELDS[table][0]
        if not rid and not f.get(primary):
            return 422, {"errors": [f"{primary} is required."]}
        if table == "Leads":
            if f.get("External id"):
                dup = s.find("Leads", "External id", f["External id"])
                if dup and dup["id"] != rid:
                    return 200, {"record": dup, "duplicate": True}
            if not rid:
                # New lead only. On an update (a status change from the Leads view) these would overwrite When
                # and re-attribute the lead to Google Organic (fixed 2026-09-23).
                f.setdefault("When", s.clock.iso_now())
                f.setdefault("Status", "New")
                self._attribute_lead(f)
        rec = s.update(table, rid, {k: v for k, v in f.items() if v is not None or k in LINK_FIELDS}) if rid \
            else s.create(table, {k: v for k, v in f.items() if v is not None})
        if table == "Leads" and (rec.get("Company") or []):
            self.sync_phase(rec["Company"][0])
        return 200, {"record": rec}

    def _attribute_lead(self, f):
        """Fill Source, Campaign, Keyword, Landing page, Company from the UTM string and the contact details."""
        s = self.s
        from urllib.parse import parse_qs, urlparse
        raw = (f.get("UTM") or "").strip()
        q = {}
        if raw:
            qs = raw.split("?", 1)[1] if "?" in raw else raw
            q = {k.lower(): v[0] for k, v in parse_qs(qs).items()}
        src_name = None
        u_src, u_med = (q.get("utm_source") or "").lower(), (q.get("utm_medium") or "").lower()
        if u_src == "google" and u_med in ("cpc", "ppc", "paid"):
            src_name = "google-ads"
        elif u_src in ("facebook", "instagram", "meta", "fb", "ig"):
            src_name = "meta-ads"
        elif u_src == "linkedin":
            src_name = "linkedin"
        elif u_src == "email" or u_med == "email":
            src_name = "email"
        elif u_med == "organic" or (not raw and not f.get("Source")):
            src_name = "google-organic"
        if not f.get("Source") and src_name:
            sid = s.source_id(src_name)
            if sid:
                f["Source"] = [sid]
        if not f.get("gclid") and q.get("gclid"):
            f["gclid"] = q["gclid"]
        camp = None
        if not f.get("Campaign") and q.get("utm_campaign"):
            camp = s.find("Campaigns", "Platform id", q["utm_campaign"]) or s.find("Campaigns", "Name", q["utm_campaign"])
            if camp:
                f["Campaign"] = [camp["id"]]
        camp_id = (f.get("Campaign") or [None])[0]
        if not f.get("Keyword") and q.get("utm_term"):
            term = q["utm_term"].strip().lower()
            for k in s.rows("Keywords"):
                if (k.get("Keyword") or "").strip().lower() == term and (not camp_id or camp_id in (k.get("Campaign") or [])):
                    f["Keyword"] = [k["id"]]
                    break
        if not f.get("Landing page") and raw and "://" in raw:
            path = urlparse(raw.split("?", 1)[0]).path.rstrip("/")
            for p in s.rows("Landing pages"):
                if urlparse(p.get("URL") or "").path.rstrip("/") == path:
                    f["Landing page"] = [p["id"]]
                    break
        if not f.get("Company"):
            email = (f.get("Email") or "").lower()
            dom = email.split("@")[-1] if "@" in email else ""
            generic = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com", "me.com"}
            key = None
            if dom and dom not in generic:
                key = dom
            else:
                key = company_key("", f.get("Phone") or "")
            if key:
                c = s.find("Companies", "Key", key)
                if c:
                    f["Company"] = [c["id"]]

    def sources_report(self):
        s = self.s
        dials_by = self._count(s.dials(), "source")
        out = []
        for src in s.rows("Sources"):
            comp_ids = set(src.get("Companies") or [])
            if src.get("_fallback"):
                comp_ids = {c["id"] for c in s.rows("Companies") if src["id"] in (c.get("Source") or [])}
            booked = sum(1 for a in s.rows("Activities") if a.get("Outcome") == "Booked"
                         and (a.get("Company") or [None])[0] in comp_ids)
            deals = [d for d in s.rows("Deals") if src["id"] in (d.get("Source") or [])]
            out.append({"name": src.get("Name"), "type": src.get("Type"), "active": bool(src.get("Active")),
                        "daily_budget": src.get("Daily budget") or 0,
                        "companies": len(comp_ids), "dials": dials_by.get(src.get("Name"), 0), "booked": booked,
                        "deals": len(deals), "open": sum(float(d.get("Value") or 0) for d in deals if not d.get("Closed")),
                        "won": sum(1 for d in deals if d.get("Won")),
                        "revenue": sum(float(d.get("Value") or 0) for d in deals if d.get("Won"))})
        out.sort(key=lambda r: (-r["revenue"], -r["open"], -r["dials"]))
        return out

    # ---- writes

    def find_or_create_company(self, key, row=None, source="cold"):
        s = self.s
        c = s.find("Companies", "Key", key)
        if c:
            return c
        if s.air.ready and s.loaded_at and time.time() - s.loaded_at > 30:
            # another writer (the AIOS through MCP) may have created it since the cache loaded
            recs, _ = s.air.list_all("Companies", formula="{Key}='%s'" % key.replace("'", "\\'"))
            if recs:
                s.tables["Companies"][recs[0]["id"]] = recs[0]["fields"]
                return dict(recs[0]["fields"], id=recs[0]["id"])
        row = row or s.queue_row(key) or {}
        fields = {"Name": row.get("name") or key, "Key": key, "Website": row.get("website") or None,
                  "Phone": row.get("phone") or None, "City": row.get("city") or "", "State": row.get("state") or "",
                  "Local time at noon ET": row.get("local_time") or "", "Dial attempts": 0,
                  "Vertical": s.vertical_label(row.get("vertical"))}
        if row.get("csv_status"):
            fields["Notes"] = f"From the list: {row['csv_status']}"
        sid = s.source_id(source)
        if sid:
            fields["Source"] = [sid]
        return s.create("Companies", {k: v for k, v in fields.items() if v is not None})

    def find_or_create_person(self, company, name, email="", phone="", role="", source=None):
        s = self.s
        pk = person_key(name, email, phone, company.get("Key"))
        p = s.find("People", "Person key", pk)
        if p:
            return p
        fields = {"Full name": name or "Unknown", "Person key": pk, "Company": [company["id"]],
                  "Role": role or "", "Primary contact": True}
        if email:
            fields["Email"] = email
        if phone:
            fields["Phone"] = phone
        sid = s.source_id(source) if source else (company.get("Source") or [None])[0]
        if sid:
            fields["Source"] = [sid]
        return s.create("People", fields)

    def log_dial(self, body):
        s = self.s
        key = body.get("key") or company_key(body.get("website"), body.get("phone"))
        if not key:
            return 422, {"errors": ["No company key: give a website or a 10 digit phone."]}
        outcome = s.outcome(body.get("outcome") or "")
        if not outcome:
            return 422, {"errors": ["Pick an outcome."]}
        contact = outcome.get("class") == "contact"
        row = s.queue_row(key)
        if not row and body.get("vertical"):
            row = {"vertical": body["vertical"], "name": body.get("name"), "phone": body.get("phone"), "website": body.get("website")}
        source = body.get("source") or (row or {}).get("source") or "cold"
        campaign = self.active_campaign()
        died_on = body.get("died_on") if contact else None
        if contact and outcome["name"] != "Booked" and not outcome.get("closes") and not died_on:
            return 422, {"errors": ["Which line did it die on?"]}
        to_stage = outcome.get("to_stage")
        stage = s.stage(to_stage) if to_stage else None
        deal_fields = None
        if contact:
            deal_fields = {"Stage": to_stage, "Owner": body.get("owner") or s.cfg.get("owner_default", ""),
                           "Next action": body.get("next_action", ""), "Next action date": body.get("next_action_date"),
                           "Close reason": body.get("close_reason"), "Close note": body.get("close_note", "")}
            if stage and not stage.get("closed"):
                errs = []
                if not (deal_fields["Next action"] or "").strip():
                    errs.append("A live conversation needs a next action.")
                if not deal_fields["Next action date"]:
                    errs.append("The next action needs a date.")
                if errs:
                    return 422, {"errors": errs}
            if stage and stage.get("closed") and not deal_fields["Close reason"]:
                return 422, {"errors": ["Closing needs a reason."]}

        entry = {"at": s.clock.iso_now(), "key": key, "name": (row or {}).get("name") or body.get("name"),
                 "state": (row or {}).get("state"), "outcome": outcome["name"], "class": outcome["class"],
                 "died_on": died_on, "recognized": bool(body.get("recognized")), "notes": body.get("notes", ""),
                 "source": source, "script": s.cfg.get("script_version", ""),
                 "campaign": campaign.get("Name") if campaign else None,
                 "vertical": s.vertical((row or {}).get("vertical"))["key"]}
        s.append_dial(entry)

        create_on = s.cfg.get("create_company_on", "any_dial")
        if not contact and create_on == "connect" and not s.find("Companies", "Key", key):
            return 200, {"logged": True, "company": None, "note": "No-contact dial logged locally only (create_company_on = connect)."}

        company = self.find_or_create_company(key, row, source)
        today = s.clock.today().isoformat()
        if not contact:
            activity = None
            if campaign:
                # A campaign counts every dial, so a no-answer gets its own row here (2026-09-25, Trade Call List).
                # Outside a campaign the no-contact dial only bumps the company, to keep the Free record count down.
                activity = s.create("Activities", {"Summary": f"Dial: {outcome['name']}", "Type": "Dial", "When": s.clock.iso_now(),
                                                   "Company": [company["id"]], "Outcome": outcome["name"],
                                                   "Script version": s.cfg.get("script_version", ""), "Notes": body.get("notes", ""),
                                                   "Logged by": "Dashboard", "Campaign": [campaign["id"]]})
            company = s.update("Companies", company["id"], {"Dial attempts": int(company.get("Dial attempts") or 0) + 1,
                                                             "Last dial": today})
            self.sync_phase(company["id"])
            return 200, {"logged": True, "company": s.rec("Companies", company["id"]), "activity": activity, "deal": None}

        person = None
        if body.get("person_name") or body.get("person_email") or body.get("person_phone"):
            person = self.find_or_create_person(company, body.get("person_name", ""), body.get("person_email", ""),
                                                body.get("person_phone", ""), body.get("person_role", ""))
        deal = s.open_deal(company["id"])
        offers = s.cfg.get("offers", [])
        offer = next((o for o in offers if o["name"] == body.get("offer")), offers[0] if offers else {"name": "", "value": 0})
        if deal:
            df = {k: v for k, v in deal_fields.items() if v not in (None, "")}
            if stage and self._rank(deal.get("Stage")) > self._rank(to_stage) and not stage.get("closed"):
                df.pop("Stage", None)  # never move a deal backwards from a dial
            self.rules.stamp_closed(df) if "Stage" in df else None
            if person and not deal.get("Contact"):
                df["Contact"] = [person["id"]]
            deal = s.update("Deals", deal["id"], df)
        else:
            df = {"Deal": f"{company.get('Name')} - {offer['name']}".strip(" -"), "Company": [company["id"]],
                  "Stage": to_stage, "Offer": offer["name"] or None, "Value": float(body.get("value") or offer.get("value") or 0),
                  "Close date": (s.clock.today() + timedelta(days=int(s.numbers().get("default_close_days", 30)))).isoformat(),
                  "Owner": deal_fields["Owner"], "Next action": deal_fields["Next action"],
                  "Next action date": deal_fields["Next action date"]}
            if company.get("Source"):
                df["Source"] = list(company["Source"])
            if person:
                df["Contact"] = [person["id"]]
            if stage and stage.get("closed"):
                df["Close reason"] = deal_fields["Close reason"]
                df["Close note"] = deal_fields["Close note"]
            self.rules.stamp_closed(df)
            deal = s.create("Deals", {k: v for k, v in df.items() if v is not None})

        summary = f"Dial: {outcome['name']}" + (f", died on {died_on}" if died_on else "")
        act = {"Summary": summary, "Type": "Dial", "When": s.clock.iso_now(), "Company": [company["id"]],
               "Deal": [deal["id"]], "Outcome": outcome["name"], "Recognized name": bool(body.get("recognized")),
               "Script version": s.cfg.get("script_version", ""), "Notes": body.get("notes", ""), "Logged by": "Dashboard"}
        if died_on:
            act["Died on"] = died_on
        elif outcome["name"] == "Booked":
            act["Died on"] = "Booked"
        if person:
            act["Person"] = [person["id"]]
        if campaign:
            act["Campaign"] = [campaign["id"]]
        activity = s.create("Activities", act)
        s.update("Companies", company["id"], {"Dial attempts": int(company.get("Dial attempts") or 0) + 1, "Last dial": today})
        self.sync_phase(company["id"])
        return 200, {"logged": True, "company": s.rec("Companies", company["id"]), "person": person,
                     "deal": deal, "activity": activity}

    def _rank(self, stage_name):
        names = [st["name"] for st in self.s.stages()]
        return names.index(stage_name) if stage_name in names else -1

    def save_deal(self, body):
        s = self.s
        rid = body.pop("id", None)
        allowed = ("Deal", "Stage", "Offer", "Value", "Close date", "Owner", "Next action", "Next action date",
                   "Close reason", "Close note", "Company", "Contact", "Source")
        f = {k: body[k] for k in allowed if k in body}
        if "Value" in f and f["Value"] not in (None, ""):
            f["Value"] = float(f["Value"])
        for k in ("Company", "Contact", "Source"):
            if k in f and isinstance(f[k], str):
                f[k] = [f[k]] if f[k] else []
        merged = dict(s.tables["Deals"].get(rid, {}), **f) if rid else f
        errs = self.rules.validate_deal(merged)
        if errs:
            return 422, {"errors": errs}
        self.rules.stamp_closed(f if "Stage" in f else merged)
        for k in ("Closed", "Won"):
            f[k] = merged.get(k, False)
        if merged.get("Closed") is False:
            f["Close reason"] = None
        if rid:
            deal = s.update("Deals", rid, f)
        else:
            if not f.get("Deal"):
                cid = (f.get("Company") or [None])[0]
                c = s.rec("Companies", cid) if cid else None
                f["Deal"] = f"{c.get('Name') if c else 'Deal'} - {f.get('Offer') or ''}".strip(" -")
            deal = s.create("Deals", f)
        cid = (deal.get("Company") or [None])[0]
        if cid:
            self.sync_phase(cid)
        if deal.get("Won"):
            # a signed client lands in the Books base at once (2026-09-28); if the Books base is out of reach, the next
            # Money page load catches up
            try:
                self.sync_books_clients()
            except (AirtableError, requests.RequestException) as e:
                s.last_error = f"Books sync: {str(e)[:200]}"
        return 200, {"deal": deal}

    def save_person(self, body):
        s = self.s
        rid = body.pop("id", None)
        allowed = ("Full name", "Role", "Phone", "Email", "Primary contact", "Notes", "Company", "Source")
        f = {k: body[k] for k in allowed if k in body}
        for k in ("Company", "Source"):
            if k in f and isinstance(f[k], str):
                f[k] = [f[k]] if f[k] else []
        if not rid and not (f.get("Full name") or "").strip():
            return 422, {"errors": ["A person needs a name."]}
        if not rid and not f.get("Company"):
            return 422, {"errors": ["A person is tied to a company."]}
        cid = (f.get("Company") or [None])[0]
        c = s.rec("Companies", cid) if cid else None
        pk = person_key(f.get("Full name"), f.get("Email"), f.get("Phone"), c.get("Key") if c else "")
        dup = s.find("People", "Person key", pk)
        if dup and dup["id"] != rid:
            return 422, {"errors": [f"That person already exists: {dup.get('Full name')}. Edit that record instead."],
                         "duplicate": dup}
        f["Person key"] = pk
        if f.get("Email") == "":
            f["Email"] = None
        if not rid and not f.get("Source") and c and c.get("Source"):
            f["Source"] = list(c["Source"])
        person = s.update("People", rid, f) if rid else s.create("People", f)
        return 200, {"person": person}

    def save_activity(self, body):
        s = self.s
        allowed = ("Summary", "Type", "When", "Company", "Person", "Deal", "Outcome", "Notes", "External id", "Logged by")
        f = {k: body[k] for k in allowed if k in body}
        for k in ("Company", "Person", "Deal"):
            if k in f and isinstance(f[k], str):
                f[k] = [f[k]] if f[k] else []
        if not f.get("Company"):
            return 422, {"errors": ["An activity lands on a company."]}
        f.setdefault("Type", "Note")
        f.setdefault("When", s.clock.iso_now())
        f.setdefault("Summary", f["Type"])
        f.setdefault("Logged by", "Manual")
        if f.get("External id"):
            dup = s.find("Activities", "External id", f["External id"])
            if dup:
                return 200, {"activity": dup, "duplicate": True}
        if not f.get("Deal"):
            d = s.open_deal(f["Company"][0])
            if d:
                f["Deal"] = [d["id"]]
        activity = s.create("Activities", f)
        self.sync_phase(f["Company"][0])
        return 200, {"activity": activity}

    def save_company(self, body):
        s = self.s
        rid = body.pop("id", None)
        allowed = ("Name", "Website", "Phone", "City", "State", "Notes", "Source", "Local time at noon ET", "Vertical")
        f = {k: body[k] for k in allowed if k in body}
        if "Source" in f and isinstance(f["Source"], str):
            f["Source"] = [f["Source"]] if f["Source"] else []
        if rid:
            return 200, {"company": s.update("Companies", rid, f)}
        f.setdefault("Vertical", s.vertical_label(body.get("vertical")))
        key = company_key(f.get("Website"), f.get("Phone"))
        if not key:
            return 422, {"errors": ["A company needs a website or a 10 digit phone."]}
        dup = s.find("Companies", "Key", key)
        if dup:
            return 422, {"errors": [f"That company already exists: {dup.get('Name')}."], "duplicate": dup}
        f["Key"] = key
        f.setdefault("Dial attempts", 0)
        if not f.get("Source"):
            sid = s.source_id("cold")
            if sid:
                f["Source"] = [sid]
        return 200, {"company": s.create("Companies", f)}

    # ---- the Ads screen (2026-09-28): approve spend, keywords, negatives, and the ad; publish paused; go live.
    # The rules and the Google calls live in scripts/ads_publish.py; this glue adds the Airtable side: a campaign-linked
    # Activity for every change, and after a publish the Campaigns row (Platform id = the Google campaign id) and one
    # Keywords row per keyword, so leads attribute by utm_campaign and utm_term (references/attribution.md).
    def ads(self):
        import ads_publish as ap
        from google_ads_api import missing_keys  # takes the client ID under either name (fixed 2026-09-29)
        log = []
        if ap.LOG.exists():
            log = [json.loads(ln) for ln in ap.LOG.read_text(encoding="utf-8").splitlines()[-12:] if ln.strip()][::-1]
        gates = json.loads(ap.GATES.read_text(encoding="utf-8")) if ap.GATES.exists() else {}
        terms = []
        latest = sorted(ap.ADS.glob("search-terms/*.json"))
        if latest:
            terms = json.loads(latest[-1].read_text(encoding="utf-8")).get("terms", [])
        return {"cards": ap.cards(), "running_total": ap.running_total(), "cap": ap.DAILY_CAP,
                "connected": not missing_keys(), "gates_read_at": (gates.get("clicks") or {}).get("at"),
                "log": log, "search_terms": terms, "search_terms_file": latest[-1].name if latest else None,
                "last_pull": ((json.loads((ap.ADS / "ads-pull.json").read_text(encoding="utf-8")) if (ap.ADS / "ads-pull.json").exists() else {}) or {}).get("last_run"),
                "shared_lists": [lst["name"] for lst in ap.negcheck.parse_lists(ap.SHARED_MD) if lst["kind"] == "neg" and lst["terms"]]}

    def _ads_campaign_row(self, doc):
        s = self.s
        gid = ((doc.get("google") or {}).get("campaign") or "").rsplit("/", 1)[-1]
        return (s.find("Campaigns", "Platform id", gid) if gid else None) or s.find("Campaigns", "Name", doc["name"])

    def _ads_sync_airtable(self, doc):
        """After a publish or a status change: the Campaigns row and the Keywords rows match the campaign file."""
        s = self.s
        g = doc.get("google") or {}
        if not g.get("campaign"):
            return None
        status = {"ENABLED": "Live", "PAUSED": "Paused"}.get(g.get("status"), "Planned")
        src = s.find("Sources", "Name", "google-ads")
        f = {"Name": doc["name"], "Status": status, "Platform id": g["campaign"].rsplit("/", 1)[-1],
             "Daily budget": float(doc["daily_budget"])}
        if src:
            f["Channel"] = [src["id"]]
        row = self._ads_campaign_row(doc)
        if status == "Live" and not (row or {}).get("Started"):
            f["Started"] = s.clock.today().isoformat()
        row = s.update("Campaigns", row["id"], f) if row else s.create("Campaigns", f)
        page = s.find("Landing pages", "URL", doc["page"])
        want = {k["text"] for k in doc["keywords"]}
        have = {r.get("Keyword"): r for r in s.rows("Keywords") if row["id"] in (r.get("Campaign") or [])}
        for kw in sorted(want):
            fields = {"Keyword": kw, "Match type": "Phrase", "Status": "Active" if status == "Live" else "Paused",
                      "Campaign": [row["id"]], "Notes": "Exact and phrase in Google Ads (the Ads screen)."}
            if page:
                fields["Landing page"] = [page["id"]]
            if kw in have:
                if have[kw].get("Status") != fields["Status"]:
                    s.update("Keywords", have[kw]["id"], {"Status": fields["Status"]})
            else:
                s.create("Keywords", fields)
        for kw, r in have.items():
            if kw not in want and r.get("Status") != "Paused":
                s.update("Keywords", r["id"], {"Status": "Paused", "Notes": "Swapped out on the Ads screen."})
        return row

    def ads_action(self, nn, action, body):
        import ads_publish as ap
        from google_ads_api import AdsError
        by = "Jonathan"
        try:
            if nn == "pull" and action == "run":
                return 200, {"result": self.ads_pull()}
            if nn == "gates":
                if action == "refresh":
                    return 200, {"gates": ap.refresh_gates(leads=self.s.rows("Leads"))}
                if action == "fix":
                    res = ap.fix(body.get("gate"), by=by)
                elif action == "tick":
                    ap.tick(body.get("gate"), by=by)
                    res = {"ticked": body.get("gate")}
                else:
                    return 404, {"errors": ["Unknown gates action."]}
                self._ads_activity(None, f"Ads: {action} {body.get('gate')}", json.dumps(res)[:500])
                return 200, {"result": res}
            if action == "approve":
                ap.approve(nn, body.get("part"), body.get("group") or None, by=by)
                return 200, {"card": ap.card(ap.load(nn))}
            # file-only edits (2026-09-29): nothing goes to Google, so no Airtable write; like an approval, each is
            # recorded in ads-log.jsonl only (a headline tweak per Activity row would eat the Free plan's record cap)
            if action in ("unapprove", "ad_remove", "ad_add", "ad_set", "kw_set"):
                if action == "kw_set":  # the edited keyword list, saved once (2026-10-01)
                    try:
                        res = ap.set_keywords(nn, body.get("keywords"), bool(body.get("allow_weak")), by=by)
                    except ap.WeakKeywords as e:
                        return 422, {"errors": [str(e)], "weak": e.weak}
                    return 200, {"result": res, "card": ap.card(ap.load(nn))}
                if action == "unapprove":
                    res = ap.unapprove(nn, body.get("part"), body.get("group") or None, by=by)
                elif action == "ad_set":  # the whole edited set of headlines and descriptions, saved once (2026-09-29)
                    res = ap.set_ad_lines(nn, body.get("headlines"), body.get("descriptions"), by=by)
                elif action == "ad_remove":
                    res = ap.remove_ad_line(nn, body.get("kind"), body.get("text", ""), by=by)
                else:
                    res = ap.add_ad_line(nn, body.get("kind"), body.get("text", ""), body.get("pin"), by=by)
                return 200, {"result": res, "card": ap.card(ap.load(nn))}
            if action == "publish":
                res = ap.publish(nn, validate_only=bool(body.get("validate_only")), by=by)
            elif action == "golive":
                ap.golive(nn, by=by)
                res = {"status": "ENABLED"}
            elif action == "pause":
                ap.pause(nn, by=by)
                res = {"status": "PAUSED"}
            elif action == "budget":
                ap.set_budget(nn, body.get("amount"), by=by)
                res = {"daily_budget": int(body.get("amount"))}
            elif action == "negative":
                res = ap.add_negative(nn, body.get("term", ""), body.get("shared") or None, by=by)
            elif action == "swap":
                res = ap.swap_keyword(nn, body.get("old", ""), body.get("new", ""), by=by)
            else:
                return 404, {"errors": ["Unknown ads action."]}
            doc = ap.load(nn)
            if action != "publish" or not body.get("validate_only"):
                try:
                    self._ads_sync_airtable(doc)
                except (AirtableError, requests.RequestException) as e:
                    self.s.last_error = f"Ads sync: {str(e)[:200]}"
                self._ads_activity(doc, f"Ads: {action} {doc['name']}", json.dumps(res)[:500])
            return 200, {"result": res, "card": ap.card(doc)}
        except ap.Refused as e:
            return 422, {"errors": [str(e)]}
        except AdsError as e:
            return 502, {"errors": ["Google refused: " + "; ".join(e.lines)]}

    def ads_pull(self):
        """Pull spend, clicks, and conversions from Google Ads, then write only the Airtable rows whose numbers
        changed, ten to a call (Airtable Free allows about 1,000 calls a month)."""
        import ads_pull
        r = ads_pull.pull()
        s = self.s
        status = {"ENABLED": "Live", "PAUSED": "Paused"}
        changes = {"Campaigns": [], "Keywords": []}
        rows_by_camp = {}
        for c in r.get("campaigns", []):
            row = s.find("Campaigns", "Platform id", c["platform_id"])
            if not row:
                continue
            rows_by_camp[c["nn"]] = row["id"]
            f = {"Spend to date": c["cost"], "Impressions": c["impressions"], "Clicks": c["clicks"],
                 "Status": status.get(c["status"], row.get("Status"))}
            if any(row.get(k) != v for k, v in f.items()):
                changes["Campaigns"].append((row["id"], f))
        for k in r.get("keywords", []):
            cid = rows_by_camp.get(k["nn"])
            row = next((x for x in s.rows("Keywords") if x.get("Keyword") == k["keyword"] and cid in (x.get("Campaign") or [])), None) if cid else None
            if not row:
                continue
            f = {"Spend to date": k["cost"], "Impressions": k["impressions"], "Clicks": k["clicks"]}
            if any(row.get(key) != v for key, v in f.items()):
                changes["Keywords"].append((row["id"], f))
        for table, recs in changes.items():
            if not recs:
                continue
            if s.air.ready and not s.outbox_size():
                s.air.update(table, recs)
                for rid, f in recs:
                    s.cache_merge(table, rid, f)
            else:
                for rid, f in recs:
                    s.update(table, rid, f)
        return {"campaigns": len(r.get("campaigns", [])), "search_terms": len(r.get("terms", [])),
                "airtable_rows": sum(len(v) for v in changes.values()), "note": r.get("note")}

    _pull_lock = threading.Lock()
    _pull_tried = 0.0

    def ads_maybe_pull(self):
        """Once a day, the first request after 6 am: pull in the background. At most one try an hour on failure."""
        try:
            import ads_pull
            from google_ads_api import missing_keys
            if not ads_pull.due() or time.time() - Api._pull_tried < 3600 or missing_keys():
                return
        except Exception:  # noqa: BLE001
            return
        if not Api._pull_lock.acquire(blocking=False):
            return
        Api._pull_tried = time.time()

        def run():
            try:
                self.ads_pull()
            except Exception as e:  # noqa: BLE001
                self.s.last_error = f"Ads pull: {str(e)[:200]}"
            finally:
                Api._pull_lock.release()
        threading.Thread(target=run, daemon=True).start()

    # ---- inbound form fills into the Prospects base's Outreach Log (2026-09-29, Jonathan: "Outreach log should take
    # inbound form submissions as well"). Every lead from the site (a Leads row: the booking script writes one per
    # booking) gets one Outreach Log row: Channel "Website form", Direction Inbound, the person, the day, what they
    # asked for and where they came from, linked to its Contacts company when the phone or the email's domain matches
    # (then Company ID is its MB ID). "CRM lead" holds the Leads record id, so each is written once. It runs in the
    # background, at most every 15 minutes and only when a lead is not in the log yet (about 3 Airtable calls a lead).

    OUTREACH = {"base": "appPM1HmRfFlgA484", "log": "tblrWA2i5JNTo0xih", "contacts": "tblGdourIuqa9onmp"}
    OUTREACH_FROM = "2026-09-29"  # form fills from this day on; older leads were test bookings
    FREE_MAIL = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com", "live.com", "msn.com",
                 "me.com", "comcast.net", "att.net", "verizon.net", "proton.me", "protonmail.com"}
    _log_lock = threading.Lock()
    _log_tried = 0.0
    _log_done = None  # CRM lead ids already in the log, read once per server start

    def _log_eligible(self, leads):
        out = []
        for l in leads:
            email = (l.get("Email") or "").strip().lower()
            day = (self.s.clock.to_local(l.get("When")) or datetime.min).date().isoformat()
            if day >= self.OUTREACH_FROM and not email.endswith("@monarcbuild.com") and not l["id"].startswith("local:"):
                out.append(l)
        return out

    def outreach_log_sync(self, force=False):
        s = self.s
        if not s.air.ready or not get_secret("AIRTABLE_API_KEY"):
            return
        if not force and time.time() - Api._log_tried < SHEET_TTL:
            return
        Api._log_tried = time.time()
        todo = [l for l in self._log_eligible(s.rows("Leads")) if Api._log_done is None or l["id"] not in Api._log_done]
        if not todo or not Api._log_lock.acquire(blocking=False):
            return

        def run():
            try:
                self._outreach_log_write(todo)
            except Exception as e:  # noqa: BLE001  never breaks a page; the next pass tries again
                Api._log_tried = time.time() - SHEET_TTL + 300
                s.last_error = f"Outreach Log: {str(e)[:200]}"
            finally:
                Api._log_lock.release()
        threading.Thread(target=run, daemon=True).start()

    def _outreach_log_write(self, todo):
        s, o = self.s, self.OUTREACH
        client = self.sheet_clients.get(("AIRTABLE_API_KEY", o["base"])) or Airtable(get_secret("AIRTABLE_API_KEY"), o["base"])
        self.sheet_clients[("AIRTABLE_API_KEY", o["base"])] = client
        meta = client._request("GET", f"meta/bases/{o['base']}/tables")
        have = {f["name"] for t in meta.get("tables", []) if t["id"] == o["log"] for f in t["fields"]}
        if "CRM lead" not in have:
            raise RuntimeError('the Outreach Log has no "CRM lead" column, so a form fill could be logged twice')
        rows = client.list_all(o["log"], formula="NOT({CRM lead}='')", fields=["CRM lead"])[0]
        Api._log_done = {r["fields"].get("CRM lead") for r in rows}
        todo = [l for l in todo if l["id"] not in Api._log_done]
        touches = {}
        if todo and "Company" in have:
            for r in client.list_all(o["log"], formula="NOT({Company}='')", fields=["Company"])[0]:
                for cid in r["fields"].get("Company") or []:
                    touches[cid] = touches.get(cid, 0) + 1
        new = []
        for l in sorted(todo, key=lambda x: x.get("When") or ""):
            match = self._contacts_match(client, l)
            comp = s.rec("Companies", (l.get("Company") or [None])[0]) or {}
            email = (l.get("Email") or "").strip().lower()
            dom = email.split("@")[-1] if "@" in email else ""
            f = {"Company ID": (match or {}).get("Company ID") or comp.get("Name") or (dom if dom and dom not in self.FREE_MAIL else "") or l.get("Name") or "Website form",
                 "Channel": "Website form", "Direction": "Inbound", "Person": l.get("Name") or "",
                 "Day": (s.clock.to_local(l.get("When")) or datetime.now()).date().isoformat(),
                 "Transcript": self._form_transcript(l), "CRM lead": l["id"]}
            if match:
                touches[match["id"]] = touches.get(match["id"], 0) + 1
                f["Company"] = [match["id"]]
                f["Touchpoint #"] = str(touches[match["id"]])
            else:
                f["Touchpoint #"] = "1"
            new.append({k: v for k, v in f.items() if k in have and v not in (None, "")})
        if new:
            client.create(o["log"], new)
            Api._log_done |= {f["CRM lead"] for f in new}

    def _contacts_match(self, client, lead):
        """The Contacts company a form fill belongs to: same phone (last 10 digits) or the email's domain on its website."""
        digits = re.sub(r"\D", "", lead.get("Phone") or "")[-10:]
        email = (lead.get("Email") or "").strip().lower()
        dom = email.split("@")[-1] if "@" in email else ""
        dom = "" if dom in self.FREE_MAIL or dom == "monarcbuild.com" else dom
        conds = []
        if len(digits) == 10:
            conds.append(f'RIGHT(REGEX_REPLACE({{Phone}}&"", "[^0-9]", ""), 10)="{digits}"')
        if dom and '"' not in dom:
            conds.append(f'FIND("{dom}", LOWER({{Website}}&""))')
        if not conds:
            return None
        recs = client.list_all(self.OUTREACH["contacts"], formula="OR(" + ",".join(conds) + ")",
                               fields=["Name", "Company ID", "Website", "Phone"], page_size=10, one_page=True)[0]
        for r in recs:
            f = r["fields"]
            if (dom and norm_domain(f.get("Website") or "") == dom) or \
                    (len(digits) == 10 and re.sub(r"\D", "", f.get("Phone") or "")[-10:] == digits):
                return dict(f, id=r["id"])
        return None

    def _form_transcript(self, l):
        s = self.s
        src = s.rec("Sources", (l.get("Source") or [None])[0]) or {}
        camp = s.rec("Campaigns", (l.get("Campaign") or [None])[0]) or {}
        kw = s.rec("Keywords", (l.get("Keyword") or [None])[0]) or {}
        came = ", ".join(x for x in (src.get("Label") or src.get("Name"), camp.get("Name"),
                                     f'keyword "{kw["Keyword"]}"' if kw.get("Keyword") else None) if x)
        lines = [l.get("Message") or "Filled in the form on monarcbuild.com.",
                 f"Came from: {came}." if came else "",
                 f"Technicians: {l['Technicians']}." if l.get("Technicians") else "",
                 " · ".join(x for x in (l.get("Email"), l.get("Phone")) if x),
                 f"CRM lead status when logged: {l.get('Status') or 'New'}."]
        return "\n".join(x for x in lines if x)

    def _ads_activity(self, doc, summary, notes):
        f = {"Summary": summary, "Type": "Note", "When": self.s.clock.iso_now(), "Logged by": "Dashboard", "Notes": notes}
        row = self._ads_campaign_row(doc) if doc else None
        if row:
            f["Campaign"] = [row["id"]]
        try:
            self.s.create("Activities", f)
        except (AirtableError, requests.RequestException) as e:
            self.s.last_error = f"Ads activity: {str(e)[:200]}"


# ---------------------------------------------------------------- http

class Handler(BaseHTTPRequestHandler):
    api: Api = None
    store: Store = None

    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            return
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def _json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except ValueError:
            return {}

    def _static(self, path):
        rel = "index.html" if path in ("", "/") else unquote(path.lstrip("/"))
        file = (CRM_DIR / rel).resolve()
        if not str(file).startswith(str(CRM_DIR.resolve())) or not file.is_file():
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(str(file))[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/json", "text/javascript"):
            ctype += "; charset=utf-8"
        data = file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    # ---- the chat box (2026-10-05, scripts/crm_chat.py). These start the clone on this machine, so they answer the
    # CRM's own page and nothing else: a request that another site's page sends to this port is refused.

    def _local(self):
        here = {f"127.0.0.1:{self.server.server_address[1]}", f"localhost:{self.server.server_address[1]}"}
        origin = self.headers.get("Origin")
        return (self.headers.get("Host") in here and (not origin or urlparse(origin).netloc in here)
                and self.headers.get("Sec-Fetch-Site") in (None, "same-origin", "none"))

    def _chat_events(self, q):
        if not self._local():
            return self._json(403, {"errors": ["Only the CRM's own page may use the chat."]})
        c = chat.get(q.get("chat", ""))
        if not c:
            return self._json(404, {"errors": ["That chat is not open on the server."]})
        since = int(q["since"]) if str(q.get("since", "")).isdigit() else 0
        try:
            return self._json(200, c.wait(since, 25 if q.get("wait") == "1" else 0))
        except ConnectionError:  # the page closed while this waited
            return None

    def _chat_post(self, p, body):
        if not self._local():
            return self._json(403, {"errors": ["Only the CRM's own page may use the chat."]})
        try:
            if p in ("chat/send", "chat/attach"):
                text = str(body.get("text") or "").strip()
                if p == "chat/send" and not text:
                    return self._json(422, {"errors": ["Type a line first."]})
                c = chat.get(str(body.get("chat") or "")) or chat.open_chat(
                    butterfly.workspace(butterfly.load(), butterfly.chats()), session=str(body.get("session") or "") or None)
                if p == "chat/send":
                    if c.busy:
                        return self._json(409, {"errors": ["The clone is still answering. Press Stop, or wait."]})
                    c.send(text[:20000])
                return self._json(200, {"chat": c.id, "session": c.session})
            c = chat.get(str(body.get("chat") or ""))
            if not c:
                return self._json(404, {"errors": ["That chat is not open on the server."]})
            if p == "chat/answer":
                ok = c.answer(str(body.get("id") or ""), bool(body.get("allow")), bool(body.get("always")))
                return self._json(200 if ok else 409, {"ok": ok} if ok else {"errors": ["That question is no longer waiting."]})
            if p == "chat/stop":
                c.stop()
                return self._json(200, {"ok": True})
            if p == "chat/open":  # the same chat in VS Code
                if not c.session:
                    return self._json(409, {"errors": ["Send a line first; the chat has nothing to open yet."]})
                return self._json(*butterfly.launch(c.cwd, session=c.session))
            return self._json(404, {"errors": ["Unknown endpoint."]})
        except Exception as e:  # noqa: BLE001
            return self._json(500, {"errors": [f"{type(e).__name__}: {e}"]})

    def _media(self, q):
        f = self.api.media_file(q.get("path", ""))
        if not f:
            return self._json(404, {"errors": ["Not a video the Creative tab can play."]})
        size = f.stat().st_size
        start, end = 0, size - 1
        m = re.match(r"bytes=(\d*)-(\d*)$", self.headers.get("Range") or "")
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                start, end = int(m.group(1)), min(int(m.group(2)), size - 1) if m.group(2) else size - 1
            else:  # the last N bytes
                start = max(0, size - int(m.group(2)))
            if start > end or start >= size:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return None
        self.send_response(206 if m else 200)
        self.send_header("Content-Type", self.api.VIDEO_TYPES[f.suffix.lower()])
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        if m:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            with open(f, "rb") as fh:
                fh.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = fh.read(min(262144, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (ConnectionError, OSError):  # the player moved on or closed
            pass
        return None

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if not u.path.startswith("/api/"):
            return self._static(u.path)
        if u.path == "/api/chat/events":
            return self._chat_events(q)
        if u.path == "/api/media":  # a video on the Creative tab, in pieces so the player can seek
            return self._media(q)
        try:
            self.store.ensure()
            a = self.api
            a.ads_maybe_pull()           # the morning read-back from Google Ads, once a day after 6 am (2026-09-28)
            a.outreach_log_sync()        # new form fills into the Prospects Outreach Log, every 15 min at most (2026-09-29)
            p = u.path[len("/api/"):]
            if p == "health":
                return self._json(200, a.health())
            if p == "config":
                return self._json(200, a.config())
            if p == "queue":
                return self._json(200, a.queue(int(q.get("limit", 22)), q.get("q", ""), q.get("all") == "1", q.get("vertical") or None))
            if p == "companies":
                return self._json(200, a.companies(q.get("q", ""), q.get("vertical") or None))
            # the company file (2026-10-04): the file itself, its mail (asked for after the page draws), the companies
            # in the Prospects call list by name, and every company waiting on him
            if p == "triage":
                return self._json(200, a.triage_board())
            if p == "reports/looms":  # show rate and close rate by Loom variation (2026-10-04)
                return self._json(200, a.loom_report())
            if p == "prospects":
                return self._json(200, a.prospect_search(q.get("q", "")))
            if p.startswith("companies/") and p.endswith("/file"):
                d = a.company_file(unquote(p[len("companies/"):-len("/file")]))
                return self._json(200 if d else 404, d or {"errors": ["No such company."]})
            if p.startswith("companies/") and p.endswith("/mail"):
                return self._json(200, a.company_mail(unquote(p[len("companies/"):-len("/mail")])))
            if p.startswith("companies/"):
                b = a.bundle(unquote(p.split("/", 1)[1]))
                return self._json(200 if b else 404, b or {"errors": ["No such company."]})
            if p == "pipeline":
                return self._json(200, a.pipeline(q.get("vertical") or None))
            if p == "activity":
                return self._json(200, a.activity(int(q.get("limit", 200))))
            if p == "reports/weekly":
                return self._json(200, a.weekly(q.get("week")))
            if p == "reports/sources":
                return self._json(200, a.sources_report())
            if p == "reports/funnel":
                return self._json(200, a.funnel())
            if p == "channels":
                return self._json(200, a.channels())
            if p == "home":
                return self._json(200, a.home())
            if p == "money":
                return self._json(200, a.money())
            if p == "agenda":
                return self._json(200, a.agenda(int(q.get("days", 2))))
            if p == "tasks":
                return self._json(200, a.tasks())
            if p == "sheet-today":  # Today's dials, shown on the Cold call channel page (2026-10-01)
                return self._json(200, a.sheet_today())
            if p == "journey":  # the journey map's tasks and artifacts (2026-10-01)
                return self._json(200, a.journey(light=q.get("light") == "1"))
            if p == "file":  # one artifact's text, read-only (an HTML page comes back as text, never run)
                return self._json(*a.file_text(q.get("path", "")))
            if p == "artifacts":  # Records, Artifacts (2026-10-02)
                return self._json(200, a.artifacts())
            if p == "creative":  # Records, Creative: media made and not yet published (2026-10-05)
                return self._json(200, a.creative())
            if p == "loom-ba/notes":  # his notes on one Loom B and A cut (2026-10-07)
                return self._json(*a.loom_ba_notes_get(q.get("date", ""), q.get("slug", "")))
            if p == "butterfly":  # the logo's menu: the skills and the projects (2026-10-05)
                return self._json(200, a.butterfly())
            if p == "raw":  # an artifact image or PDF
                f = a._safe_file(q.get("path", ""))
                if not f or f.suffix.lower() not in a.RAW_TYPES:
                    return self._json(404, {"errors": ["Not a file the viewer can show."]})
                data = f.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", a.RAW_TYPES[f.suffix.lower()])
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
                return
            if p == "mail":
                return self._json(200, a.mail(force=q.get("force") == "1"))
            if p == "page-shot":
                return self._json(200, a.page_shot(q.get("url", "")))
            if p == "mail/message":
                d = a.mail_message(q.get("folder", "INBOX"), q.get("uid", ""))
                return self._json(200 if d.get("ok") else 404, d)
            if p == "ads":
                return self._json(200, a.ads())
            if p.startswith("lead/"):
                d = a.lead_detail(unquote(p.split("/", 1)[1]))
                return self._json(200 if d else 404, d or {"errors": ["No such lead."]})
            if p.startswith("channel/"):
                data = a.channel(unquote(p.split("/", 1)[1]))
                return self._json(200 if data else 404, data or {"errors": ["No such channel."]})
            if p.startswith("records/"):
                t = unquote(p.split("/", 1)[1])
                return self._json(200 if t in SAVE_FIELDS else 404, self.store.rows(t) if t in SAVE_FIELDS else {"errors": ["Unknown table."]})
            if p == "dials":
                return self._json(200, self.store.dials()[-500:])
            return self._json(404, {"errors": ["Unknown endpoint."]})
        except AirtableError as e:
            self.store.last_error = str(e)
            return self._json(502, {"errors": [str(e)]})
        except Exception as e:  # noqa: BLE001
            return self._json(500, {"errors": [f"{type(e).__name__}: {e}"]})

    def do_POST(self):
        u = urlparse(self.path)
        p = u.path[len("/api/"):] if u.path.startswith("/api/") else ""
        body = self._body()
        if p.startswith("chat/"):
            return self._chat_post(p, body)
        try:
            self.store.ensure()
            a = self.api
            if p == "dial":
                return self._json(*a.log_dial(body))
            if p == "deals":
                return self._json(*a.save_deal(body))
            if p == "people":
                return self._json(*a.save_person(body))
            if p == "activities":
                return self._json(*a.save_activity(body))
            if p == "companies":
                return self._json(*a.save_company(body))
            if p.startswith("companies/") and p.endswith("/triage"):  # tick a step or add a to-do on a company file
                return self._json(*a.triage_set(unquote(p[len("companies/"):-len("/triage")]), body))
            if p.startswith("companies/") and p.endswith("/loom"):  # a Loom brief on a company file, its variation, watched
                return self._json(*a.loom_set(unquote(p[len("companies/"):-len("/loom")]), body))
            if p == "page-shot":  # take a fresh copy of a monarcbuild.com page (about 10 seconds)
                d = a.page_shot(body.get("url", ""), make=True)
                return self._json(200 if d.get("ok") else 422, d)
            if p == "refresh":
                a.sheet_cache.clear()  # the call sheets too, so a call typed in Airtable shows at once
                Api._prospect_cache.clear()  # and the company files' reads of the Prospects base and the mailbox
                Api._file_mail.clear()
                self.store._books = None  # and the Books base
                self.store.ensure(force=True)
                a.outreach_log_sync(force=True)  # and any new form fill goes to the Outreach Log now
                Api._mail = None                 # and the inbox and drafts on Today read again
                self.store._agenda = None        # and the calendar with its invites
                return self._json(200, a.health())
            if p == "rephase":
                return self._json(200, a.rephase_all())
            if p == "tasks/done":
                return self._json(*a.task_done(body))
            if p == "creative/published":  # mark a piece of media published, or take the mark back
                return self._json(*a.creative_mark(body))
            if p == "loom-ba/notes":  # add or take back a note on a Loom B and A cut (2026-10-07)
                return self._json(*a.loom_ba_notes_post(body))
            if p == "journey/task":  # tick a channel task on the journey map (2026-10-01)
                return self._json(*a.journey_task(body))
            if p == "butterfly/open":  # open a project's chat, or a new chat with a skill typed in (2026-10-05)
                return self._json(*a.butterfly_open(body))
            if p == "butterfly/new":  # a new artifact, campaign, or skill: the row, then its chat
                return self._json(*a.butterfly_new(body))
            if p.startswith("ads/") and p.count("/") == 2:
                _, nn, action = p.split("/")
                return self._json(*a.ads_action(nn, action, body))
            if p.startswith("records/"):
                return self._json(*a.save_record(unquote(p.split("/", 1)[1]), body))
            return self._json(404, {"errors": ["Unknown endpoint."]})
        except AirtableError as e:
            self.store.last_error = str(e)
            msg = e.payload.get("error", e.payload) if isinstance(e.payload, dict) else e.payload
            return self._json(502, {"errors": [f"Airtable refused the write: {msg}"]})
        except Exception as e:  # noqa: BLE001
            return self._json(500, {"errors": [f"{type(e).__name__}: {e}"]})

    do_PATCH = do_POST


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int)
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--instance", default="monarc")
    ap.add_argument("--check", action="store_true", help="key source, one meta read, record counts")
    ap.add_argument("--probe", action="store_true", help="print one raw REST page per table")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    inst, inst_path = load_instance(args.instance)
    token = get_secret("AIRTABLE_PAT")
    env, src = load_env()
    air = Airtable(token, inst["base_id"])
    store = Store(inst, air)
    api = Api(store)

    print(f"Instance: {inst.get('label')} ({inst_path.name}), base {inst['base_id']}")
    print(f"AIRTABLE_PAT: {'found in ' + src['AIRTABLE_PAT'] if token else 'MISSING (offline mode: queue and dial log only)'}")
    print(f"Queue: {', '.join(store.queue_files()) or 'none'} ({len(store.queue_all)} rows)")

    if args.check:
        if not token:
            sys.exit("Add AIRTABLE_PAT to %USERPROFILE%\\.monarc\\secrets.env (scopes: data.records:read, "
                     "data.records:write, schema.bases:read; access: the Monarc CRM base).")
        meta = air.meta()
        names = [t["name"] for t in meta.get("tables", [])]
        print(f"Meta read OK: {len(names)} tables: {', '.join(names)}")
        store.ensure(force=True)
        for t in TABLES:
            print(f"  {t}: {len(store.tables[t])}")
        print(f"Records: {store.record_total()} of {store.numbers().get('record_cap', 1000)}. API calls: {air.calls}. "
              f"Config from: {store.cfg_source}. Outbox: {store.outbox_size()}")
        return

    if args.probe:
        if not token:
            sys.exit("AIRTABLE_PAT missing; nothing to probe.")
        for t in TABLES:
            recs, page = air.list_all(t, page_size=2, one_page=True)
            print(f"\n=== {t} (pageSize=2) ===")
            print(json.dumps(page, indent=2)[:3000])
        return

    port = args.port or inst.get("port", 8770)  # 8765 is the Dictation Sheet's port (2026-09-23)
    Handler.api, Handler.store = api, store
    httpd = None
    for p in range(port, port + 10):
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    if not httpd:
        sys.exit(f"No free port from {port}.")
    url = f"http://127.0.0.1:{port}/"
    print(f"Monarc CRM at {url}  (Ctrl+C stops it)")
    if not args.no_open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
