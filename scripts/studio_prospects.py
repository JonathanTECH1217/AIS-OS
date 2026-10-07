"""The Prospects base for Monarc Calls (2026-10-01; reworked 2026-10-03, brainstorms/2026-10-01-live-call-notes.md).

Jonathan's call sheet: base Prospects (appPM1HmRfFlgA484), table Contacts, plus the Outreach Log table. REST with
AIRTABLE_API_KEY (the MCP can't see this base), through the CRM's Airtable client (scripts/crm_server.py), which keeps
requests under 5 a second and waits out a 429 once.

He types Status himself in Airtable's own grid, in its own window beside the notes window (Q32). Monarc Calls reads:
  Status changed  every few seconds while listening (changes_since): the rows whose Status (typed) changed since the
                  last look. That edit cuts the call and names its company (Q33).
and writes (Q39), never Status:
  Contacts        Email and Owner, only when the field is blank (a fresh read first), when he pushes a card.
  Outreach Log    one row per dial (not skips): Company ID (the MB ID), Company (link), Channel "Cold Call", Day,
                  Direction "Outbound", Touchpoint # (that company's earlier rows + 1), Call key ("<session> #n", a
                  column added on first use, so a retried write never logs a dial twice). On push, Transcript gets his
                  kept key notes.

He renames columns himself, sometimes mid-task (references/airtable-api.md), so the schema is read at the start
panel and at Start, and every read and write after that goes by field id. A missing column stops Start, named.

Writes go through Writer, a thread with its own queue, in order: retried after 2, 5, 15, 30, then every 60 s on a
network error, a 429 or a 5xx; any other refusal is "stuck" and shown. The session file holds every write before it
goes out (scripts/studio_session.py), so none is lost if the laptop or the network drops.

  python scripts/studio_prospects.py --check        the columns and the last few Status changes (reads only)

STUDIO_FAKE_AIRTABLE=<json> swaps in Fake, a local stand-in for the tests (projects/studio/tests/fixtures/prospects.json).
"""
import hashlib
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

BASE = "appPM1HmRfFlgA484"
CONTACTS = "tblGdourIuqa9onmp"
LOG = "tblrWA2i5JNTo0xih"
CALL_KEY = "Call key"
GRID_URL = "https://airtable.com/appPM1HmRfFlgA484/tblGdourIuqa9onmp/viwIqkvcY7jm27SY0"   # his Grid view (Q41)

# role, column names tried in order, required
ROLES = [("name", ("Name",), True), ("mb", ("Company ID",), True), ("status", ("Status (typed)",), True),
         ("changed", ("Status changed",), True), ("email", ("Email",), True), ("owner", ("Owner",), True),
         ("website", ("Website",), False), ("phone", ("Phone",), False)]
LOG_ROLES = [("mb", ("Company ID",), True), ("company", ("Company",), True), ("channel", ("Channel",), True),
             ("day", ("Day",), True), ("direction", ("Direction",), True), ("touch", ("Touchpoint #",), True),
             ("key", (CALL_KEY,), False), ("mblookup", ("MB ID",), False), ("transcript", ("Transcript",), False)]
BLANK_ONLY = ("email", "owner")


class SchemaError(Exception):
    pass


def fq(s):
    """A value inside a double-quoted Airtable formula string."""
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def iso(t):
    """Epoch seconds as Airtable's UTC form, '2026-10-03T14:05:06.000Z'."""
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + f"{int((t % 1) * 1000):03d}Z"


def epoch(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return None


def _text(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return ", ".join(_text(x) for x in v)
    if isinstance(v, dict):
        return str(v.get("name") or v.get("text") or "")
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


# ---------------------------------------------------------------- columns

class Schema:
    """Roles to columns, from the base's meta (GET meta/bases/<base>/tables)."""

    def __init__(self, meta):
        tables = {t["id"]: t for t in (meta or {}).get("tables", [])}
        if CONTACTS not in tables:
            raise SchemaError("Can't see the Contacts table in the Prospects base. Check AIRTABLE_API_KEY.")
        self.f = self._map(tables[CONTACTS], ROLES, "Contacts")
        self.log, self.log_error = None, None
        try:
            self.log = self._map(tables[LOG], LOG_ROLES, "Outreach Log") if LOG in tables else None
            if self.log is None:
                self.log_error = "Can't see the Outreach Log table, so dials aren't logged there."
        except SchemaError as e:
            self.log_error = str(e) + " Dials aren't logged there until it's back."

    @staticmethod
    def _map(table, roles, label):
        by_name = {f["name"]: f for f in table.get("fields", [])}
        out, missing = {}, []
        for role, names, required in roles:
            hit = next((by_name[n] for n in names if n in by_name), None)
            if hit:
                out[role] = {"id": hit["id"], "name": hit["name"], "type": hit.get("type")}
            elif required:
                missing.append(names[0])
        if missing:
            cols = ", ".join(f'"{m}"' for m in missing)
            raise SchemaError(f"The {label} table has no {cols} column{'s' if len(missing) > 1 else ''} any more. "
                              "Put it back (or tell Claude its new name) and press Start again.")
        return out

    def id(self, role):
        return self.f[role]["id"] if role in self.f else None

    def name(self, role):
        return self.f[role]["name"] if role in self.f else None

    def ids(self):
        return [v["id"] for v in self.f.values()]

    def log_id(self, role):
        return self.log[role]["id"] if self.log and role in self.log else None

    def brief(self):
        return {"names": {k: v["name"] for k, v in self.f.items()}, "ids": {k: v["id"] for k, v in self.f.items()},
                "log": {k: v["name"] for k, v in (self.log or {}).items()}, "logError": self.log_error}

    def shape(self, rec):
        """A Contacts record (fields by id) as the session uses it."""
        f = rec.get("fields") or {}
        g = lambda role: _text(f.get(self.id(role))) if self.id(role) else ""  # noqa: E731
        return {"id": rec["id"], "mb": g("mb"), "name": g("name"), "status": g("status"), "changed": g("changed"),
                "changed_t": epoch(g("changed")), "email": g("email"), "owner": g("owner"), "website": g("website"),
                "phone": g("phone")}


# ---------------------------------------------------------------- the live base

class Live:
    """Airtable over REST. Formulas use column names; fields come back and go out by id."""

    def __init__(self, client=None):
        if client is None:
            from crm_server import Airtable
            from outreach_common import get_secret
            client = Airtable(get_secret("AIRTABLE_API_KEY"), BASE)
        self.client = client

    def meta(self):
        return self.client.meta()

    def _list(self, table, formula, ids, sort=None, direction="asc", limit=100):
        params = {"pageSize": min(100, limit), "maxRecords": limit, "returnFieldsByFieldId": "true"}
        if ids:
            params["fields[]"] = ids
        if formula:
            params["filterByFormula"] = formula
        if sort:
            params["sort[0][field]"] = sort
            params["sort[0][direction]"] = direction
        return self.client._request("GET", f"{BASE}/{table}", params=params).get("records", [])

    @staticmethod
    def changes_formula(s, since_iso):
        return f'IS_AFTER({{{s.name("changed")}}}, DATETIME_PARSE("{fq(since_iso)}"))'

    def changes_since(self, s, since_iso, limit=100):
        """Rows whose Status changed after since_iso, oldest first: one call."""
        return self._list(CONTACTS, self.changes_formula(s, since_iso), s.ids(), sort=s.name("changed"), limit=limit)

    def latest_changes(self, s, n=5):
        return self._list(CONTACTS, f'NOT({{{s.name("changed")}}}="")', s.ids(), sort=s.name("changed"),
                          direction="desc", limit=n)

    def get(self, s, rec):
        return self.client._request("GET", f"{BASE}/{CONTACTS}/{rec}", params={"returnFieldsByFieldId": "true"})

    def patch(self, s, rec, fields):
        self.client._request("PATCH", f"{BASE}/{CONTACTS}/{rec}", body={"fields": fields, "typecast": True})

    @staticmethod
    def log_formula(s, mb):
        conds = [f'{{{s.log["mb"]["name"]}}}="{fq(mb)}"']
        if "mblookup" in s.log:
            conds.append(f'FIND("{fq(mb)}", ARRAYJOIN({{{s.log["mblookup"]["name"]}}}))')
        return "OR(" + ",".join(conds) + ")"

    def log_rows(self, s, mb, rec):
        ids = [s.log_id("mb"), s.log_id("company")] + ([s.log_id("key")] if s.log_id("key") else [])
        return self._list(LOG, self.log_formula(s, mb), ids, limit=100)

    def log_find(self, s, key):
        if not s.log_id("key"):
            return None
        recs = self._list(LOG, f'{{{s.log["key"]["name"]}}}="{fq(key)}"', [s.log_id("key")], limit=1)
        return recs[0]["id"] if recs else None

    def log_create(self, s, fields):
        data = self.client._request("POST", f"{BASE}/{LOG}", body={"records": [{"fields": fields}], "typecast": True})
        return data["records"][0]["id"]

    def log_patch(self, s, rid, fields):
        self.client._request("PATCH", f"{BASE}/{LOG}/{rid}", body={"fields": fields, "typecast": True})

    def add_log_key(self):
        self.client._request("POST", f"meta/bases/{BASE}/tables/{LOG}/fields", body={
            "name": CALL_KEY, "type": "singleLineText",
            "description": "Monarc Calls: session and call number, so a retried write never logs a dial twice."})


# ---------------------------------------------------------------- the stand-in for tests

class Fake:
    """The same calls as Live over a JSON file: {"contacts": {"fields": [{name, type}], "records": [{id, fields by
    name}]}, "log": {...}, "failFirst": [record ids whose first write fails like a dropped network]}. Writes go back
    to the file, so a test can read what was written. fake_status() plays Jonathan typing Status in Airtable."""

    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.data = json.loads(self.path.read_text(encoding="utf-8"))
        self.failed = set()

    @staticmethod
    def fid(name):
        return "fld" + hashlib.md5(name.encode()).hexdigest()[:14]

    def _save(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)

    def meta(self):
        def table(tid, name, t):
            return {"id": tid, "name": name, "fields": [dict(f, id=self.fid(f["name"])) for f in t["fields"]]}
        out = [table(CONTACTS, "Contacts", self.data["contacts"])]
        if "log" in self.data:
            out.append(table(LOG, "Outreach Log", self.data["log"]))
        return {"tables": out}

    def _by_id(self, rec):
        return {"id": rec["id"], "fields": {self.fid(k): v for k, v in rec["fields"].items()}}

    def changes_since(self, s, since_iso, limit=100):
        since = epoch(since_iso) or 0
        cn = s.name("changed")
        with self.lock:
            recs = [r for r in self.data["contacts"]["records"] if (epoch(r["fields"].get(cn)) or 0) > since]
        recs.sort(key=lambda r: epoch(r["fields"].get(cn)) or 0)
        return [self._by_id(r) for r in recs[:limit]]

    def latest_changes(self, s, n=5):
        cn = s.name("changed")
        recs = [r for r in self.data["contacts"]["records"] if r["fields"].get(cn)]
        recs.sort(key=lambda r: epoch(r["fields"].get(cn)) or 0, reverse=True)
        return [self._by_id(r) for r in recs[:n]]

    def fake_status(self, rec, words, at=None):
        """Jonathan types words into Status (typed); Airtable stamps Status changed."""
        with self.lock:
            r = next(x for x in self.data["contacts"]["records"] if x["id"] == rec)
            r["fields"]["Status (typed)"] = words
            r["fields"]["Status changed"] = iso(at or time.time())
            self._save()
            return r["fields"]["Status changed"]

    def get(self, s, rec):
        r = next((x for x in self.data["contacts"]["records"] if x["id"] == rec), None)
        if not r:
            raise LookupError(rec)
        return self._by_id(r)

    def _fail_once(self, rec):
        if rec in self.data.get("failFirst", []) and rec not in self.failed:
            self.failed.add(rec)
            raise ConnectionError("fake: the network dropped")

    def patch(self, s, rec, fields):
        with self.lock:
            self._fail_once(rec)
            names = {self.fid(f["name"]): f["name"] for f in self.data["contacts"]["fields"]}
            r = next(x for x in self.data["contacts"]["records"] if x["id"] == rec)
            for k, v in fields.items():
                r["fields"][names[k]] = v
            self._save()

    def log_rows(self, s, mb, rec):
        mbn = s.log["mb"]["name"]
        return [self._by_id(r) for r in self.data["log"]["records"] if r["fields"].get(mbn) == mb]

    def log_find(self, s, key):
        if not s.log_id("key"):
            return None
        return next((r["id"] for r in self.data["log"]["records"] if r["fields"].get(CALL_KEY) == key), None)

    def log_create(self, s, fields):
        with self.lock:
            names = {self.fid(f["name"]): f["name"] for f in self.data["log"]["fields"]}
            rid = "recL" + hashlib.md5(json.dumps(fields, sort_keys=True).encode() + str(time.time()).encode()).hexdigest()[:10]
            self.data["log"]["records"].append({"id": rid, "fields": {names[k]: v for k, v in fields.items()}})
            self._save()
            return rid

    def log_patch(self, s, rid, fields):
        with self.lock:
            names = {self.fid(f["name"]): f["name"] for f in self.data["log"]["fields"]}
            r = next(x for x in self.data["log"]["records"] if x["id"] == rid)
            for k, v in fields.items():
                r["fields"][names[k]] = v
            self._save()

    def add_log_key(self):
        with self.lock:
            self.data["log"]["fields"].append({"name": CALL_KEY, "type": "singleLineText"})
            self._save()

    def dump(self):
        with self.lock:
            return json.loads(json.dumps(self.data))


def backend():
    p = os.environ.get("STUDIO_FAKE_AIRTABLE")
    return Fake(p) if p else Live()


# ---------------------------------------------------------------- the facade

class Prospects:
    def __init__(self, be=None):
        self.be = be or backend()
        self.schema = None
        self.lock = threading.Lock()

    def open(self, add_key=True):
        """Read the columns. With add_key, give the Outreach Log its Call key column if it has none."""
        s = Schema(self.be.meta())
        if add_key and s.log is not None and "key" not in s.log:
            try:
                self.be.add_log_key()
                s = Schema(self.be.meta())
            except Exception as e:  # noqa: BLE001  (the key may lack schema write; rows still go in)
                s.log_error = (f'Couldn\'t add the "{CALL_KEY}" column to the Outreach Log ({type(e).__name__}), so a '
                               f"retried write could log a dial twice. Add it by hand: single line text, \"{CALL_KEY}\".")
        with self.lock:
            self.schema = s
        return s

    def changes(self, since_t):
        """Rows whose Status changed after since_t (epoch seconds), oldest first, shaped."""
        return [self.schema.shape(r) for r in self.be.changes_since(self.schema, iso(since_t))]

    def get(self, rec):
        return self.schema.shape(self.be.get(self.schema, rec))


def retryable(e):
    import requests
    if isinstance(e, (requests.RequestException, ConnectionError, TimeoutError)):
        return True
    status = getattr(e, "status", None)
    return isinstance(status, int) and (status == 429 or status >= 500)


class Writer:
    """Writes to the Prospects base in order, on its own thread. Ops:
      {"w", "kind": "set", "rec", "role": email|owner, "value", "t"}    blank-only on the Contacts row
      {"w", "kind": "log", "rec", "mb", "day", "key", "t"}              the dial's Outreach Log row
      {"w", "kind": "log_note", "key", "text", "t"}                     its Transcript, after a push
    on_result(op, state, info): state ok | kept | fail | stuck. A failed op goes back in the queue behind later ones,
    except that a log_note always waits for an earlier log op with its key."""
    BACKOFF = (2, 5, 15, 30, 60)

    def __init__(self, prospects, on_result):
        self.p = prospects
        self.on_result = on_result
        self.q = []
        self.cv = threading.Condition()
        self.own = {}             # (rec, role) -> what this session wrote, so a second push can correct it
        self.busy = False
        threading.Thread(target=self._loop, daemon=True).start()

    def add(self, op):
        with self.cv:
            self.q.append(dict(op, tries=0, due=0.0))
            self.cv.notify()

    def retry_now(self):
        with self.cv:
            for x in self.q:
                x["due"] = 0.0
            self.cv.notify()

    def pending(self):
        with self.cv:
            return len(self.q) + (1 if self.busy else 0)

    def _emit(self, op, state, info=None):
        try:
            self.on_result({k: v for k, v in op.items() if k not in ("tries", "due")}, state, info)
        except Exception:  # noqa: BLE001
            pass

    def _ready(self, x):
        if x["kind"] != "log_note":
            return True
        return not any(y["kind"] == "log" and y.get("key") == x.get("key") for y in self.q)

    def _loop(self):
        while True:
            with self.cv:
                while True:
                    now = time.time()
                    due = [x for x in self.q if x["due"] <= now and self._ready(x)]
                    if due and self.p.schema is not None:
                        break
                    nxt = min((x["due"] for x in self.q), default=None)
                    # no columns read yet (offline at start): look again every second
                    self.cv.wait(1.0 if due or (nxt is not None and nxt <= now) else
                                 None if nxt is None else max(0.05, nxt - now))
                first = due[0]
                if first["kind"] == "set":     # every due write to this company goes in one PATCH
                    batch = [x for x in due if x["kind"] == "set" and x["rec"] == first["rec"]]
                else:
                    batch = [first]
                for x in batch:
                    self.q.remove(x)
                self.busy = True
            try:
                self._do(batch)
            except Exception as e:  # noqa: BLE001
                self._failed(batch, e)
            finally:
                with self.cv:
                    self.busy = False

    def _failed(self, batch, e):
        msg = f"{type(e).__name__}: {e}"[:300]
        if retryable(e):
            waits = []
            with self.cv:
                for x in batch:
                    x["tries"] += 1
                    wait = self.BACKOFF[min(x["tries"] - 1, len(self.BACKOFF) - 1)]
                    x["due"] = time.time() + wait
                    self.q.append(x)
                    waits.append((x, wait))
                self.cv.notify()
            for x, wait in waits:     # reported outside the lock: on_result takes the session's lock
                self._emit(x, "fail", {"error": msg, "retry_in": wait})
        else:
            for x in batch:
                self._emit(x, "stuck", {"error": msg})

    def _do(self, batch):
        s = self.p.schema
        kind = batch[0]["kind"]
        if kind == "log":
            return self._log(s, batch[0])
        if kind == "log_note":
            return self._log_note(s, batch[0])
        rec = batch[0]["rec"]
        fields, plan = {}, []
        cur = s.shape(self.p.be.get(s, rec))          # fresh: he may have typed it in Airtable meanwhile
        for x in batch:
            if x["role"] not in BLANK_ONLY:
                plan.append((x, "stuck", {"error": f"Monarc Calls doesn't write {x['role']}"}))
                continue
            have = (cur.get(x["role"]) or "").strip()
            if have and have != self.own.get((rec, x["role"])) and have != x["value"]:
                plan.append((x, "kept", {"kept": have}))
                continue
            fields[s.id(x["role"])] = x["value"]
            plan.append((x, "ok", None))
        if fields:
            self.p.be.patch(s, rec, fields)
        for x, state, info in plan:
            if state == "ok":
                self.own[(rec, x["role"])] = x["value"]
            self._emit(x, state, info)

    def _log(self, s, op):
        if s.log is None:
            return self._emit(op, "stuck", {"error": s.log_error or "no Outreach Log"})
        rows = self.p.be.log_rows(s, op["mb"], op["rec"])
        kid = s.log_id("key")
        if kid:
            hit = next((r for r in rows if (r.get("fields") or {}).get(kid) == op["key"]), None)
            if hit:
                return self._emit(op, "ok", {"already": True, "id": hit["id"]})
        fields = {s.log_id("mb"): op["mb"], s.log_id("company"): [op["rec"]], s.log_id("channel"): "Cold Call",
                  s.log_id("day"): op["day"], s.log_id("direction"): "Outbound", s.log_id("touch"): str(len(rows) + 1)}
        if kid:
            fields[kid] = op["key"]
        rid = self.p.be.log_create(s, fields)
        self._emit(op, "ok", {"id": rid, "touch": len(rows) + 1})

    def _log_note(self, s, op):
        if s.log is None or not s.log_id("transcript"):
            return self._emit(op, "stuck", {"error": s.log_error or 'the Outreach Log has no "Transcript" column'})
        rid = op.get("log_id") or self.p.be.log_find(s, op["key"])
        if not rid:
            return self._emit(op, "stuck", {"error": "no Outreach Log row for this call"})
        self.p.be.log_patch(s, rid, {s.log_id("transcript"): op["text"]})
        self._emit(op, "ok", {"id": rid})


# ---------------------------------------------------------------- command line

def _check():
    p = Prospects()
    s = p.open(add_key=False)
    b = s.brief()
    print("Contacts columns:")
    for role, name in b["names"].items():
        print(f"  {role:8} {name}")
    print("Outreach Log:", json.dumps(b["log"]) if b["log"] else "-", f"\n  {b['logError']}" if b["logError"] else "")
    if "key" not in (s.log or {}):
        print(f'  no "{CALL_KEY}" column yet: Monarc Calls adds it at the first Start')
    print("\nLast Status changes (the poll reads these):")
    for r in [s.shape(x) for x in p.be.latest_changes(s, 5)]:
        print(f"  {r['changed']:26} {r['mb']:9} {r['name'][:36]:36} {r['status'][:30]}")
    since = time.time() - 3600
    print(f"\nChanged in the last hour (the poll formula): {len(p.changes(since))}")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    sys.exit(_check())
