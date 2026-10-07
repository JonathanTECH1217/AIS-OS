"""Publish and control Monarc's six Google Ads campaigns from their campaign files.

Usage:
  python scripts/ads_publish.py status                     approvals, gates, the spend cap, and live state
  python scripts/ads_publish.py plan 01                    what Publish would send, counted by kind; offline, no keys
  python scripts/ads_publish.py approve 01 spend|keywords|ad|negatives[:<list name>]
  python scripts/ads_publish.py publish 01 [--validate-only]   rehearse, then build it PAUSED (needs all approvals)
  python scripts/ads_publish.py golive 01 | pause 01 | budget 01 40
  python scripts/ads_publish.py negative 01 "term" [--shared "<list name>"]   block a search, then push it
  python scripts/ads_publish.py swap 01 "old keyword" "new keyword"
  python scripts/ads_publish.py fix clicks|conversion      set the account switch, read it back, tick the checklist
  python scripts/ads_publish.py tick billing               Jonathan says billing is fixed
  python scripts/ads_publish.py gates [--refresh]          the five gates (--refresh reads Google and the live pages)
  python scripts/ads_publish.py geo                        turn the 213 place names into Google location ids, once

The CRM calls the same functions from the Google Ads channel page (scripts/crm_server.py, #/channel/google-ads; the
old #/ads screen folded into it 2026-09-29), plus the ad edits there: take a headline or description out, add one,
put one back, and take an approval back. Every change is written to projects/google-ads/ads-log.jsonl; the CRM also
logs it as an Activity.

Rules (Jonathan, 2026-09-28, plan approved):
- Four approvals per campaign: spend (budget, bidding, where it runs), keywords, negatives (by list), the ad.
  An approval holds a fingerprint of what was approved; any later edit clears it. Shared lists are approved once for
  every campaign.
- Publish builds everything in Google Ads PAUSED, after a validate-only rehearsal. Publishing again pushes only what
  changed. Go live is a second step.
- Go live stays locked until the five gates are done: billing; one main conversion; click stamping (auto-tagging and
  the final URL suffix); the page h1 names the service; a test booking reached Airtable with its labels.
- Spend cap $3,000 a month: running campaigns may not pass $100 a day together, and only one test-slot campaign runs.
- Explorer access allows 2,880 actions a day; a first publish with every shared list is about 2,100 counting the
  rehearsal. Publish one new campaign a day until Basic access.
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ads_lint  # noqa: E402
import ads_negative_check as negcheck  # noqa: E402
from outreach_common import ROOT, get_secret  # noqa: E402

ADS = ROOT / "projects" / "google-ads"
CAMPAIGNS = ADS / "campaigns"
SHARED_MD = ADS / "negatives" / "shared-lists.md"
SHARED_APPROVALS = ADS / "negatives" / "approvals.json"
SHARED_SETS = ADS / "shared-sets.json"
GEO_IDS = ADS / "geo-target-ids.json"
GATES = ADS / "gates.json"
LOG = ADS / "ads-log.jsonl"
CHECKLIST = ADS / "tracking-checklist.md"
ACCOUNT_MD = ADS / "account.md"

DAILY_CAP = 100            # $3,000 a month (decision 10)
ENGLISH = "languageConstants/1000"
MATCH = {"exact": "EXACT", "phrase": "PHRASE", "broad": "BROAD"}
PIN = {1: "HEADLINE_1", 2: "HEADLINE_2", 3: "HEADLINE_3"}
SERVICE_WORDS = {"01": ["google ads"], "02": ["website"], "03": ["seo"], "04": ["email"],
                 "05": ["facebook"], "06": ["automation"],
                 "07": ["av contractor", "av integrator"]}  # /av_marketing/'s h1 (2026-09-30)
SWAP_SERVICE = {"01": ["google ads", "ppc", "adwords", "paid search"], "02": ["website", "web design"],
                "03": ["seo", "google business profile", "gbp", "google my business"], "04": ["email"],
                "05": ["facebook", "instagram", "meta ads"], "06": ["automation", "ai", "follow up", "back office"],
                "07": ["marketing"]}
# A dealer of the brands integrators sell is an integrator (Jonathan, 2026-09-30: dealer-brand keywords for campaign 07)
TRADE_WORDS = ["av integrator", "integrator", "home automation", "smart home", "low voltage", "home theater",
               "electrician", "electrical", "hvac", "heating", "roofing", "roofer", "plumber", "plumbing",
               "contractor", "home service", "control4 dealer", "lutron dealer", "crestron dealer", "savant dealer"]
NOT_BUYING = {"how", "what", "why", "best", "top", "cost", "price", "pricing", "vs", "tips", "guide", "examples",
              "template", "templates", "software", "tool", "tools", "app", "jobs", "job", "course", "free"}
GATE_NAMES = {"billing": "Billing fixed", "conversion": "One main conversion",
              "clicks": "Click stamping (auto-tagging and link labels)", "h1": "Page h1 names the service",
              "booking": "Test booking in Airtable"}
CHECK_ITEM = {"billing": 1, "conversion": 3, "clicks": 7, "booking": 13}


class Refused(Exception):
    """A plain-words reason an action cannot run."""


# ---------------------------------------------------------------- files

def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def fp(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


def _read_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def campaign_path(nn):
    hits = sorted(CAMPAIGNS.glob(f"{nn}-*.json"))
    if not hits:
        raise Refused(f"No campaign file for {nn} in {CAMPAIGNS.relative_to(ROOT)}.")
    return hits[0]


def load(nn):
    return _read_json(campaign_path(nn), None)


def save(doc):
    _write_json(campaign_path(doc["nn"]), doc)


def all_campaigns():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(CAMPAIGNS.glob("[0-9][0-9]-*.json"))]


def log(nn, action, detail="", by="Jonathan"):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": now(), "nn": nn, "action": action, "detail": detail, "by": by}) + "\n")


# ---------------------------------------------------------------- negatives

def negative_groups(doc):
    """The lists that apply to this campaign: [{key, scope, name, terms: [parsed term]}]."""
    out = []
    for lst in negcheck.parse_lists(SHARED_MD):
        if lst["kind"] == "neg" and lst["terms"] and negcheck.applies(lst, doc["nn"]):
            out.append({"key": f"shared:{lst['name']}", "scope": "shared", "name": lst["name"], "terms": lst["terms"]})
    own = ROOT / doc["negatives"]["campaign"]
    if own.exists():
        for lst in negcheck.parse_lists(own):
            if lst["kind"] == "neg" and lst["terms"]:
                out.append({"key": f"campaign:{lst['name']}", "scope": "campaign", "name": lst["name"],
                            "terms": lst["terms"]})
    return out


def term_key(t):
    return f"{MATCH[t['kind']]}|{' '.join(t['words'])}"


def group_fp(g):
    return fp(sorted(term_key(t) for t in g["terms"]))


def negatives_block_keywords(doc, extra_keywords=()):
    """Refusals from the negative check for this campaign's keywords (plus any extra, e.g. a swap)."""
    problems = []
    kws = [k["text"] for k in doc["keywords"]] + list(extra_keywords)
    for g in negative_groups(doc):
        for t in g["terms"]:
            for p in t["problems"]:
                problems.append(f"{t['raw']} ({g['name']}): {p}")
            for kw in kws:
                if negcheck.blocks(t, negcheck.words(kw)):
                    problems.append(f"{t['raw']} ({g['name']}) blocks \"{kw}\"")
    return problems


def _insert_term(path, group, line):
    """Add one line to the fenced block under '## group' in a negatives markdown file; make the list if missing."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    start = next((i for i, ln in enumerate(lines) if ln.strip() == f"## {group}"), None)
    if start is None:
        lines += ["", f"## {group}", "", "Added from the search terms on the Ads screen.", "", "```", line, "```"]
    else:
        opens = [i for i in range(start + 1, len(lines)) if lines[i].strip().startswith("```")]
        nxt = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        if len(opens) < 2 or opens[1] > nxt:
            raise Refused(f"The list \"{group}\" in {path.name} has no paste block.")
        lines.insert(opens[1], line)
    path.write_text("\n".join(lines), encoding="utf-8")
    return text


# ---------------------------------------------------------------- approvals

def parts(doc):
    return {
        "spend": {k: doc[k] for k in ("daily_budget", "bidding", "slot", "network", "geo", "language")},
        "keywords": doc["keywords"],
        "ad": {"ad": doc["ad"], "page": doc["page"]},
    }


def _state(stamp, current):
    if not stamp:
        return "open"
    return "approved" if stamp.get("fp") == current else "changed"


def approval_state(doc):
    shared_ok = _read_json(SHARED_APPROVALS, {})
    own_ok = (doc.get("approvals") or {}).get("negatives", {})
    out = {p: _state((doc.get("approvals") or {}).get(p), fp(v)) for p, v in parts(doc).items()}
    groups = []
    for g in negative_groups(doc):
        stamp = shared_ok.get(g["name"]) if g["scope"] == "shared" else own_ok.get(g["name"])
        groups.append({"key": g["key"], "scope": g["scope"], "name": g["name"], "count": len(g["terms"]),
                       "examples": [t["raw"] for t in g["terms"][:3]], "terms": [t["raw"] for t in g["terms"]],
                       "state": _state(stamp, group_fp(g)), "at": (stamp or {}).get("at")})
    out["negatives"] = "approved" if groups and all(g["state"] == "approved" for g in groups) else (
        "changed" if any(g["state"] == "changed" for g in groups) else "open")
    out["groups"] = groups
    out["ready"] = all(out[p] == "approved" for p in ("spend", "keywords", "ad", "negatives"))
    return out


def ad_problems(doc):
    ad = doc["ad"]
    out = []
    heads, descs = ad.get("headlines", []), ad.get("descriptions", [])
    for h in heads:
        flags = ads_lint.check_text(h["text"]) + ([f"over {ads_lint.H_MAX} characters"] if len(h["text"]) > ads_lint.H_MAX else [])
        out += [f"headline \"{h['text']}\": {f}" for f in flags]
    for d in descs:
        flags = ads_lint.check_text(d) + ([f"over {ads_lint.D_MAX} characters"] if len(d) > ads_lint.D_MAX else [])
        out += [f"description \"{d}\": {f}" for f in flags]
    for p in (ad.get("path1"), ad.get("path2")):
        if p and len(p) > ads_lint.P_MAX:
            out.append(f"path \"{p}\": over {ads_lint.P_MAX} characters")
    if not 3 <= len(heads) <= 15:
        out.append(f"{len(heads)} headlines (an ad takes 3 to 15)")
    if not 2 <= len(descs) <= 4:
        out.append(f"{len(descs)} descriptions (an ad takes 2 to 4)")
    low = [h["text"].lower() for h in heads]
    out += [f"headline \"{t}\" twice" for t in sorted({t for t in low if low.count(t) > 1})]
    return out


def approve(nn, part, group=None, by="Jonathan"):
    doc = load(nn)
    cur = parts(doc)
    doc.setdefault("approvals", {})
    if part in ("spend", "keywords", "ad"):
        if part == "keywords":
            probs = negatives_block_keywords(doc)
            if probs:
                raise Refused("A negative blocks a keyword: " + "; ".join(probs[:5]))
        if part == "ad":
            probs = ad_problems(doc)
            if probs:
                raise Refused("The ad fails the checks: " + "; ".join(probs[:5]))
        doc["approvals"][part] = {"at": now(), "by": by, "fp": fp(cur[part])}
        save(doc)
        log(nn, f"approve {part}", by=by)
        return doc
    if part != "negatives":
        raise Refused(f"Unknown approval \"{part}\" (spend, keywords, negatives, ad).")
    probs = negatives_block_keywords(doc)
    if probs:
        raise Refused("A negative blocks a keyword: " + "; ".join(probs[:5]))
    shared_ok = _read_json(SHARED_APPROVALS, {})
    own_ok = doc["approvals"].setdefault("negatives", {})
    hit = 0
    for g in negative_groups(doc):
        if group and g["name"] != group:
            continue
        stamp = {"at": now(), "by": by, "fp": group_fp(g)}
        if g["scope"] == "shared":
            shared_ok[g["name"]] = stamp
        else:
            own_ok[g["name"]] = stamp
        hit += 1
    if not hit:
        raise Refused(f"No negative list named \"{group}\" on campaign {nn}.")
    _write_json(SHARED_APPROVALS, shared_ok)
    save(doc)
    log(nn, "approve negatives", group or "all lists", by=by)
    return doc


# ---------------------------------------------------------------- gates

def checklist_ticked(item):
    if not CHECKLIST.exists():
        return False
    return bool(re.search(rf"^- \[x\] {item}\.", CHECKLIST.read_text(encoding="utf-8"), re.M))


def tick_checklist(item, note):
    text = CHECKLIST.read_text(encoding="utf-8")
    new, n = re.subn(rf"^- \[ \] ({item}\. .*)$", lambda m: f"- [x] {m.group(1)} **Done {datetime.now():%Y-%m-%d}:** {note}",
                     text, count=1, flags=re.M)
    if n:
        CHECKLIST.write_text(new, encoding="utf-8")


def url_suffix():
    m = re.search(r"Final URL suffix[^|]*\|\s*`([^`]+)`", ACCOUNT_MD.read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def _h1_text(url):
    r = requests.get(url, timeout=20, headers={"User-Agent": "MonarcAIOS/1.0"})
    m = re.search(r"<h1[^>]*>(.*?)</h1>", r.text, re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


def _google():
    from google_ads_api import GoogleAds
    return GoogleAds()


def refresh_gates(leads=None, g=None):
    """Read Google, the live pages, and Airtable; store the answers in gates.json. leads: Airtable Leads rows
    (the CRM passes its own), else read with AIRTABLE_PAT."""
    gates = _read_json(GATES, {})
    stamp = now()
    try:
        g = g or _google()
        rows = g.search("SELECT conversion_action.name, conversion_action.primary_for_goal, conversion_action.status "
                        "FROM conversion_action WHERE conversion_action.status = 'ENABLED'")
        prim = [r["conversionAction"]["name"] for r in rows if r["conversionAction"].get("primaryForGoal")]
        ok = len(prim) == 1 and "submit lead form" in prim[0].lower()
        gates["conversion"] = {"ok": ok, "at": stamp, "note": f"main: {', '.join(prim) or 'none'}"}
        c = (g.search("SELECT customer.auto_tagging_enabled, customer.final_url_suffix FROM customer") or [{}])[0]
        c = c.get("customer", {})
        want = url_suffix()
        ok = bool(c.get("autoTaggingEnabled")) and (c.get("finalUrlSuffix") or "") == want
        gates["clicks"] = {"ok": ok, "at": stamp, "note": f"auto-tagging {'on' if c.get('autoTaggingEnabled') else 'off'}; "
                           f"suffix {'matches account.md' if (c.get('finalUrlSuffix') or '') == want else 'differs or missing'}"}
    except Exception as e:  # noqa: BLE001  (not connected yet, or refused: say so on the card)
        why = ("Google Ads is not connected yet" if getattr(e, "status", None) == 0 and "Missing" in str(e)
               else f"not read from Google: {str(e)[:120]}")
        for k in ("conversion", "clicks"):
            gates.setdefault(k, {"ok": None, "at": stamp, "note": ""})
            gates[k]["note"] = why
    gates["h1"] = gates.get("h1", {})
    for doc in all_campaigns():
        try:
            h1 = _h1_text(doc["page"])
            ok = any(w in h1.lower() for w in SERVICE_WORDS[doc["nn"]])
            gates["h1"][doc["nn"]] = {"ok": ok, "at": stamp, "note": f"h1: {h1 or '(none found)'}"}
        except requests.RequestException as e:
            gates["h1"][doc["nn"]] = {"ok": None, "at": stamp, "note": f"page not read: {type(e).__name__}"}
    try:
        if leads is None:
            pat = get_secret("AIRTABLE_PAT")
            r = requests.get("https://api.airtable.com/v0/appgv3njf5Fk99QXo/Leads", timeout=20,
                             headers={"Authorization": f"Bearer {pat}"},
                             params={"filterByFormula": "FIND('utm_source=google', {UTM})"})
            leads = [x["fields"] for x in r.json().get("records", [])]
        hit = [x for x in leads if "utm_source=google" in (x.get("UTM") or "") and (x.get("Campaign") or x.get("gclid"))]
        gates["booking"] = {"ok": bool(hit), "at": stamp,
                            "note": f"{len(hit)} lead(s) with Google labels" if hit else "no lead with Google labels yet"}
    except Exception as e:  # noqa: BLE001
        gates.setdefault("booking", {"ok": None, "at": stamp})
        gates["booking"]["note"] = f"Airtable not read: {str(e)[:80]}"
    _write_json(GATES, gates)
    return gates


def gate_state(nn):
    """The five gates for one campaign: [{key, name, ok, note, fixable}]."""
    gates = _read_json(GATES, {})
    out = []
    for key in ("billing", "conversion", "clicks", "h1", "booking"):
        if key == "billing":
            ok, note = checklist_ticked(1), "ticked in tracking-checklist.md" if checklist_ticked(1) else "tick it when fixed"
        elif key == "h1":
            e = gates.get("h1", {}).get(nn, {})
            ok, note = e.get("ok"), e.get("note", "not read yet")
        else:
            e = gates.get(key, {})
            ok, note = e.get("ok"), e.get("note", "not read yet")
            if not ok and checklist_ticked(CHECK_ITEM[key]):
                ok, note = True, "ticked in tracking-checklist.md"
        out.append({"key": key, "name": GATE_NAMES[key], "ok": bool(ok), "note": note,
                    "fixable": key in ("conversion", "clicks"), "tickable": key == "billing"})
    return out


def tick(gate, by="Jonathan"):
    if gate != "billing":
        raise Refused("Only billing is ticked by hand; the other gates are read from Google, the pages, and Airtable.")
    tick_checklist(1, f"{by} confirmed on the Ads screen.")
    log("--", "tick billing", by=by)


def fix(gate, by="Jonathan"):
    g = _google()
    if gate == "clicks":
        suffix = url_suffix()
        g._call("POST", f"customers/{g.cid}:mutate", {"operation": {
            "update": {"resourceName": f"customers/{g.cid}", "autoTaggingEnabled": True, "finalUrlSuffix": suffix},
            "updateMask": "autoTaggingEnabled,finalUrlSuffix"}})
    elif gate == "conversion":
        rows = g.search("SELECT conversion_action.resource_name, conversion_action.name, conversion_action.primary_for_goal "
                        "FROM conversion_action WHERE conversion_action.status = 'ENABLED'")
        main = [r for r in rows if "submit lead form" in r["conversionAction"]["name"].lower()]
        if len(main) != 1:
            raise Refused(f"Found {len(main)} actions named Submit lead form; fix this one in Google Ads by hand.")
        ops = [{"update": {"resourceName": r["conversionAction"]["resourceName"], "primaryForGoal": r in main},
                "updateMask": "primaryForGoal"} for r in rows
               if bool(r["conversionAction"].get("primaryForGoal")) != (r in main)]
        if ops:
            g._call("POST", f"customers/{g.cid}/conversionActions:mutate", {"operations": ops})
    else:
        raise Refused("Fix works on clicks and conversion only.")
    gates = refresh_gates(g=g)
    if gates.get(gate, {}).get("ok"):
        for item in ((6, 7) if gate == "clicks" else (3,)):
            tick_checklist(item, f"set by the Ads screen Fix button and read back ({by}).")
    log("--", f"fix {gate}", json.dumps(gates.get(gate)), by=by)
    return gates.get(gate)


# ---------------------------------------------------------------- spend cap

def running_total(except_nn=None):
    return sum(d["daily_budget"] for d in all_campaigns()
               if (d.get("google") or {}).get("status") == "ENABLED" and d["nn"] != except_nn)


def cap_check(doc, budget=None):
    budget = doc["daily_budget"] if budget is None else budget
    total = running_total(doc["nn"]) + budget
    if total > DAILY_CAP:
        raise Refused(f"Over ${DAILY_CAP} a day: running campaigns plus this one come to ${total} a day "
                      f"(the $3,000 a month cap).")
    if doc["slot"] == "test":
        others = [d["name"] for d in all_campaigns() if d["slot"] == "test" and d["nn"] != doc["nn"]
                  and (d.get("google") or {}).get("status") == "ENABLED"]
        if others:
            raise Refused(f"One test campaign at a time: {others[0]} is running. Pause it first.")


# ---------------------------------------------------------------- publish

def geo_ids(g=None, names=None):
    names = names or [ln.strip() for ln in (ROOT / "projects/google-ads/geo-targets.txt").read_text(encoding="utf-8").splitlines()
                      if ln.strip()]
    have = _read_json(GEO_IDS, {})
    missing = [n for n in names if n not in have]
    if missing:
        g = g or _google()
        have.update(g.suggest_geo(missing))
        _write_json(GEO_IDS, have)
    return {n: have.get(n) for n in names}


class Ops:
    """Collects mutate operations with a label for each, so the replies can be filed back."""

    def __init__(self, cid):
        self.cid, self.ops, self.labels, self.tmp = cid, [], [], 0

    def temp(self, kind):
        self.tmp -= 1
        return f"customers/{self.cid}/{kind}/{self.tmp}"

    def add(self, kind, body, label):
        self.ops.append({kind: body})
        self.labels.append(label)

    def counts(self):
        out = {}
        for op, lab in zip(self.ops, self.labels):
            k = f"{lab[0]} {'remove' if 'remove' in next(iter(op.values())) else 'update' if 'update' in next(iter(op.values())) else 'create'}"
            out[k] = out.get(k, 0) + 1
        return out


def _kw(t):
    return {"text": " ".join(t["words"]), "matchType": MATCH[t["kind"]]}


def build_ops(doc, cid, geo=None):
    """Every operation Publish needs to make Google match the file. Returns Ops."""
    gstate = doc.get("google") or {}
    sets = _read_json(SHARED_SETS, {})
    o = Ops(cid)
    rn = lambda kind, rid: f"customers/{cid}/{kind}/{rid}"  # noqa: E731

    # shared lists (account level): create or bring up to date, then link to this campaign
    shared_rn = {}
    for grp in [x for x in negative_groups(doc) if x["scope"] == "shared"]:
        have = sets.get(grp["name"], {})
        set_rn = have.get("set")
        if not set_rn:
            set_rn = o.temp("sharedSets")
            o.add("sharedSetOperation", {"create": {"resourceName": set_rn, "name": f"Monarc: {grp['name']}",
                                                    "type": "NEGATIVE_KEYWORDS"}}, ("shared set", grp["name"]))
        shared_rn[grp["name"]] = set_rn
        want = {term_key(t): t for t in grp["terms"]}
        got = have.get("terms", {})
        for k, t in want.items():
            if k not in got:
                o.add("sharedCriterionOperation", {"create": {"sharedSet": set_rn, "keyword": _kw(t)}},
                      ("shared negative", grp["name"], k))
        for k, crit in got.items():
            if k not in want:
                o.add("sharedCriterionOperation", {"remove": crit}, ("shared negative", grp["name"], k))

    # budget and campaign
    micros = str(int(doc["daily_budget"] * 1_000_000))
    budget_rn = gstate.get("budget")
    if not budget_rn:
        budget_rn = o.temp("campaignBudgets")
        o.add("campaignBudgetOperation", {"create": {"resourceName": budget_rn,
                                                     "name": f"{doc['name']} budget {datetime.now():%Y%m%d%H%M}",
                                                     "amountMicros": micros, "deliveryMethod": "STANDARD",
                                                     "explicitlyShared": False}}, ("budget",))
    elif str(gstate.get("budget_micros")) != micros:
        o.add("campaignBudgetOperation", {"update": {"resourceName": budget_rn, "amountMicros": micros},
                                          "updateMask": "amountMicros"}, ("budget",))
    cpc = str(int(doc["bidding"]["max_cpc"] * 1_000_000))
    camp_rn = gstate.get("campaign")
    if not camp_rn:
        camp_rn = o.temp("campaigns")
        o.add("campaignOperation", {"create": {
            "resourceName": camp_rn, "name": doc["name"], "status": "PAUSED", "advertisingChannelType": "SEARCH",
            "campaignBudget": budget_rn,
            "networkSettings": {"targetGoogleSearch": True, "targetSearchNetwork": doc["network"]["search_partners"],
                                "targetContentNetwork": doc["network"]["display"], "targetPartnerSearchNetwork": False},
            "targetSpend": {"cpcBidCeilingMicros": cpc},
            "geoTargetTypeSetting": {"positiveGeoTargetType": "PRESENCE" if doc["geo"]["presence_only"] else
                                     "PRESENCE_OR_INTEREST", "negativeGeoTargetType": "PRESENCE"},
            "containsEuPoliticalAdvertising": "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING"}}, ("campaign",))
    elif str(gstate.get("cpc_micros")) != cpc:
        o.add("campaignOperation", {"update": {"resourceName": camp_rn, "targetSpend": {"cpcBidCeilingMicros": cpc}},
                                    "updateMask": "targetSpend.cpcBidCeilingMicros"}, ("campaign",))

    # where it runs: locations and language
    geo = geo if geo is not None else _read_json(GEO_IDS, {})
    want_geo = {v for v in geo.values() if v}
    got_geo = gstate.get("geo", {})
    for gtc in sorted(want_geo - set(got_geo)):
        o.add("campaignCriterionOperation", {"create": {"campaign": camp_rn, "location": {"geoTargetConstant": gtc}}},
              ("location", gtc))
    for gtc in sorted(set(got_geo) - want_geo):
        o.add("campaignCriterionOperation", {"remove": got_geo[gtc]}, ("location", gtc))
    if not gstate.get("language"):
        o.add("campaignCriterionOperation", {"create": {"campaign": camp_rn, "language": {"languageConstant": ENGLISH}}},
              ("language",))

    # this campaign's own negatives
    want_neg = {term_key(t): t for grp in negative_groups(doc) if grp["scope"] == "campaign" for t in grp["terms"]}
    got_neg = gstate.get("negatives", {})
    for k, t in want_neg.items():
        if k not in got_neg:
            o.add("campaignCriterionOperation", {"create": {"campaign": camp_rn, "negative": True, "keyword": _kw(t)}},
                  ("negative", k))
    for k, crit in got_neg.items():
        if k not in want_neg:
            o.add("campaignCriterionOperation", {"remove": crit}, ("negative", k))

    # link the shared lists
    links = gstate.get("shared_links", {})
    for name, set_rn in shared_rn.items():
        if name not in links:
            o.add("campaignSharedSetOperation", {"create": {"campaign": camp_rn, "sharedSet": set_rn}}, ("link", name))
    for name, link in links.items():
        if name not in shared_rn:
            o.add("campaignSharedSetOperation", {"remove": link}, ("link", name))

    # ad group, keywords, ad
    ag_rn = gstate.get("ad_group")
    if not ag_rn:
        ag_rn = o.temp("adGroups")
        o.add("adGroupOperation", {"create": {"resourceName": ag_rn, "name": f"{doc['name']} keywords",
                                              "campaign": camp_rn, "status": "ENABLED", "type": "SEARCH_STANDARD"}},
              ("ad group",))
    want_kw = {f"{MATCH[m]}|{k['text']}": (k["text"], MATCH[m]) for k in doc["keywords"] for m in k["match"]}
    got_kw = gstate.get("keywords", {})
    for key, (text, mt) in want_kw.items():
        if key not in got_kw:
            o.add("adGroupCriterionOperation", {"create": {"adGroup": ag_rn, "status": "ENABLED",
                                                           "keyword": {"text": text, "matchType": mt}}}, ("keyword", key))
    for key, crit in got_kw.items():
        if key not in want_kw:
            o.add("adGroupCriterionOperation", {"remove": crit}, ("keyword", key))
    ad_fp = fp(parts(doc)["ad"])
    if gstate.get("ad_fp") != ad_fp:
        ad = doc["ad"]
        rsa = {"headlines": [{"text": h["text"], **({"pinnedField": PIN[h["pin"]]} if h.get("pin") else {})}
                             for h in ad["headlines"]],
               "descriptions": [{"text": d} for d in ad["descriptions"]]}
        if ad.get("path1"):
            rsa["path1"] = ad["path1"]
        if ad.get("path2"):
            rsa["path2"] = ad["path2"]
        o.add("adGroupAdOperation", {"create": {"adGroup": ag_rn, "status": "ENABLED",
                                                "ad": {"finalUrls": [doc["page"]], "responsiveSearchAd": rsa}}}, ("ad",))
        if gstate.get("ad"):
            o.add("adGroupAdOperation", {"remove": gstate["ad"]}, ("old ad",))
    return o


def _file_results(doc, o, resp, cid):
    """Write the ids Google returned back into the campaign file and shared-sets.json."""
    gstate = doc.setdefault("google", {})
    sets = _read_json(SHARED_SETS, {})
    results = resp.get("mutateOperationResponses", [])
    tmp_real = {}
    for op, lab, res in zip(o.ops, o.labels, results):
        body = next(iter(op.values()))
        real = next((v.get("resourceName") for v in res.values() if isinstance(v, dict)), None)
        removing = "remove" in body
        created = body.get("create", {})
        if created.get("resourceName"):
            tmp_real[created["resourceName"]] = real
        kind = lab[0]
        if kind == "shared set":
            sets.setdefault(lab[1], {"terms": {}})["set"] = real
        elif kind == "shared negative":
            terms = sets.setdefault(lab[1], {"terms": {}}).setdefault("terms", {})
            terms.pop(lab[2], None) if removing else terms.__setitem__(lab[2], real)
        elif kind == "budget":
            gstate["budget"] = gstate.get("budget") or real
            gstate["budget_micros"] = str(int(doc["daily_budget"] * 1_000_000))
        elif kind == "campaign":
            gstate["campaign"] = gstate.get("campaign") or real
            gstate["cpc_micros"] = str(int(doc["bidding"]["max_cpc"] * 1_000_000))
            gstate.setdefault("status", "PAUSED")
        elif kind == "location":
            geo = gstate.setdefault("geo", {})
            geo.pop(lab[1], None) if removing else geo.__setitem__(lab[1], real)
        elif kind == "language":
            gstate["language"] = real
        elif kind == "negative":
            neg = gstate.setdefault("negatives", {})
            neg.pop(lab[1], None) if removing else neg.__setitem__(lab[1], real)
        elif kind == "link":
            links = gstate.setdefault("shared_links", {})
            links.pop(lab[1], None) if removing else links.__setitem__(lab[1], real)
        elif kind == "ad group":
            gstate["ad_group"] = real
        elif kind == "keyword":
            kws = gstate.setdefault("keywords", {})
            kws.pop(lab[1], None) if removing else kws.__setitem__(lab[1], real)
        elif kind == "ad":
            gstate["ad"] = real
            gstate["ad_fp"] = fp(parts(doc)["ad"])
    for name, s in sets.items():
        if s.get("set", "").startswith(f"customers/{cid}/sharedSets/-"):
            s["set"] = tmp_real.get(s["set"], s["set"])
    _write_json(SHARED_SETS, sets)
    gstate["published_at"] = now()
    gstate["published"] = {p: fp(v) for p, v in parts(doc).items()}
    gstate["published"]["negatives"] = {x["key"]: group_fp(x) for x in negative_groups(doc)}


def unpublished_changes(doc):
    pub = (doc.get("google") or {}).get("published")
    if not pub:
        return ["not published yet"]
    out = [p for p, v in parts(doc).items() if pub.get(p) != fp(v)]
    now_neg = {x["key"]: group_fp(x) for x in negative_groups(doc)}
    if pub.get("negatives") != now_neg:
        out.append("negatives")
    return out


def publish(nn, validate_only=False, by="Jonathan"):
    doc = load(nn)
    st = approval_state(doc)
    if not st["ready"]:
        open_parts = [p for p in ("spend", "keywords", "ad", "negatives") if st[p] != "approved"]
        raise Refused(f"Approve first: {', '.join(open_parts)}.")
    probs = negatives_block_keywords(doc) + ad_problems(doc)
    if probs:
        raise Refused("Checks failed: " + "; ".join(probs[:5]))
    g = _google()
    geo = geo_ids(g)
    unresolved = [n for n, v in geo.items() if not v]
    o = build_ops(doc, g.cid, geo)
    if not o.ops:
        return {"sent": 0, "note": "Google already matches the file."}
    g.mutate(o.ops, validate_only=True)                     # rehearsal: Google checks every step, creates nothing
    if validate_only:
        return {"sent": 0, "rehearsed": len(o.ops), "counts": o.counts(), "unresolved_places": unresolved}
    resp = g.mutate(o.ops)
    doc = load(nn)
    _file_results(doc, o, resp, g.cid)
    save(doc)
    log(nn, "publish", json.dumps(o.counts()), by=by)
    return {"sent": len(o.ops), "counts": o.counts(), "unresolved_places": unresolved,
            "status": doc["google"].get("status")}


def _set_status(nn, status, by):
    doc = load(nn)
    camp = (doc.get("google") or {}).get("campaign")
    if not camp:
        raise Refused("Not published yet.")
    g = _google()
    g.mutate([{"campaignOperation": {"update": {"resourceName": camp, "status": status}, "updateMask": "status"}}])
    doc["google"]["status"] = status
    save(doc)
    log(nn, status.lower(), by=by)
    return doc


def golive(nn, by="Jonathan"):
    doc = load(nn)
    if not (doc.get("google") or {}).get("campaign"):
        raise Refused("Publish first.")
    if not approval_state(doc)["ready"]:
        raise Refused("An approval was cleared by an edit; approve again and publish.")
    waiting = unpublished_changes(doc)
    if waiting:
        raise Refused(f"Changes not published yet: {', '.join(waiting)}. Publish first.")
    open_gates = [x["name"] for x in gate_state(nn) if not x["ok"]]
    if open_gates:
        raise Refused(f"Gate open: {', '.join(open_gates)}.")
    cap_check(doc)
    return _set_status(nn, "ENABLED", by)


def pause(nn, by="Jonathan"):
    return _set_status(nn, "PAUSED", by)


def set_budget(nn, amount, by="Jonathan"):
    doc = load(nn)
    amount = int(amount)
    if amount < 1:
        raise Refused("A daily budget is at least $1.")
    if (doc.get("google") or {}).get("status") == "ENABLED":
        cap_check(doc, amount)
    doc["daily_budget"] = amount
    doc.setdefault("approvals", {})["spend"] = {"at": now(), "by": by, "fp": fp(parts(doc)["spend"])}
    save(doc)
    log(nn, "budget", f"${amount} a day", by=by)
    if (doc.get("google") or {}).get("budget"):
        g = _google()
        micros = str(amount * 1_000_000)
        g.mutate([{"campaignBudgetOperation": {"update": {"resourceName": doc["google"]["budget"], "amountMicros": micros},
                                               "updateMask": "amountMicros"}}])
        doc = load(nn)
        doc["google"]["budget_micros"] = micros
        doc["google"]["published"]["spend"] = fp(parts(doc)["spend"])
        save(doc)
    return doc


def add_negative(nn, raw, shared_group=None, by="Jonathan"):
    """Block a search: write it into the campaign's own list (or a shared list), check it, approve it, push it."""
    doc = load(nn)
    t = negcheck.parse_term(raw)
    if t["problems"]:
        raise Refused(f"{raw}: {'; '.join(t['problems'])}")
    path = SHARED_MD if shared_group else ROOT / doc["negatives"]["campaign"]
    group = shared_group or "From search terms"
    before = _insert_term(path, group, raw)
    try:
        for d in (all_campaigns() if shared_group else [doc]):
            probs = negatives_block_keywords(d)
            if probs:
                raise Refused(f"Not added: {probs[0]}")
    except Refused:
        path.write_text(before, encoding="utf-8")
        raise
    approve(nn, "negatives", group, by=by)
    log(nn, "negative", f"{raw} -> {group}", by=by)
    if (doc.get("google") or {}).get("campaign"):
        return publish(nn, by=by)
    return {"sent": 0, "note": "Added to the list; it goes to Google on the next Publish."}


def buying_intent_problems(nn, text):
    w = negcheck.words(text)
    joined = " ".join(w)
    out = []
    if not any(s in joined for s in SWAP_SERVICE[nn]):
        out.append("it does not name this campaign's service")
    if not any(t in joined for t in TRADE_WORDS):
        out.append("it does not name a trade")
    bad = sorted(set(w) & NOT_BUYING)
    if bad:
        out.append(f"it has a not-buying word ({', '.join(bad)})")
    return out


def swap_keyword(nn, old, new, by="Jonathan"):
    doc = load(nn)
    old, new = old.strip().lower(), new.strip().lower()
    texts = [k["text"] for k in doc["keywords"]]
    if old not in texts:
        raise Refused(f"\"{old}\" is not one of campaign {nn}'s keywords.")
    if new in texts:
        raise Refused(f"\"{new}\" is already a keyword.")
    probs = buying_intent_problems(nn, new) + negatives_block_keywords(doc, [new])
    if probs:
        raise Refused(f"\"{new}\" fails: {'; '.join(probs[:3])}.")
    for k in doc["keywords"]:
        if k["text"] == old:
            k["text"] = new
    if new in doc.get("bench", []):
        doc["bench"].remove(new)
    doc["bench"] = doc.get("bench", []) + [old]
    doc.setdefault("approvals", {})["keywords"] = {"at": now(), "by": by, "fp": fp(parts(doc)["keywords"])}
    save(doc)
    log(nn, "swap keyword", f"{old} -> {new}", by=by)
    if (doc.get("google") or {}).get("campaign"):
        return publish(nn, by=by)
    return {"sent": 0, "note": "Swapped in the file; it goes to Google on the next Publish."}


# ---------------------------------------------------------------- ad edits and taking an approval back (2026-09-29)
# Jonathan, 2026-09-29: an X on each headline he does not approve of, and his own headlines added to the campaign, on
# the Google Ads channel page. A line taken out goes to the campaign's ad bench (kept outside "ad", so the bench never
# changes the ad's fingerprint) and can be put back. Any edit to the ad changes its fingerprint, which clears the ad's
# approval: nothing reaches Google until he approves the ad again and publishes.

AD_LIMITS = {"headlines": (3, 15, ads_lint.H_MAX), "descriptions": (2, 4, ads_lint.D_MAX)}
AD_WORD = {"headlines": "headline", "descriptions": "description"}


def _ad_text(line):
    return line["text"] if isinstance(line, dict) else line


def remove_ad_line(nn, kind, text, by="Jonathan"):
    if kind not in AD_LIMITS:
        raise Refused("Take out a headline or a description.")
    doc = load(nn)
    lo = AD_LIMITS[kind][0]
    lines = doc["ad"][kind]
    i = next((n for n, x in enumerate(lines) if _ad_text(x) == text), None)
    if i is None:
        raise Refused(f"\"{text}\" is not in this ad.")
    if len(lines) <= lo:
        raise Refused(f"An ad needs at least {lo} {kind}. Add one before you take this one out.")
    line = lines.pop(i)
    bench = doc.setdefault("ad_bench", {}).setdefault(kind, [])
    if all(_ad_text(b).lower() != text.lower() for b in bench):
        bench.append(line)
    save(doc)
    log(nn, f"take out {AD_WORD[kind]}", text, by=by)
    return {"removed": text, "note": "The ad needs your approval again before it is published."}


def add_ad_line(nn, kind, text, pin=None, by="Jonathan"):
    if kind not in AD_LIMITS:
        raise Refused("Add a headline or a description.")
    doc = load(nn)
    _, hi, cap = AD_LIMITS[kind]
    word = AD_WORD[kind]
    text = " ".join((text or "").split())
    if not text:
        raise Refused(f"Type the {word}.")
    if len(text) > cap:
        raise Refused(f"{len(text)} characters. A {word} takes at most {cap}.")
    flags = ads_lint.check_text(text)
    if flags:
        raise Refused(f"\"{text}\": {'; '.join(flags)}.")
    lines = doc["ad"][kind]
    if any(_ad_text(x).lower() == text.lower() for x in lines):
        raise Refused(f"\"{text}\" is already in the ad.")
    if len(lines) >= hi:
        raise Refused(f"The ad has {hi} {kind}, the most Google takes. Take one out first.")
    if kind == "headlines":
        pin = int(pin) if str(pin or "").strip() not in ("", "0") else None
        if pin and pin not in PIN:
            raise Refused("A headline pins to slot 1, 2, or 3.")
        lines.append({"text": text, **({"pin": pin} if pin else {})})
    else:
        lines.append(text)
    bench = (doc.get("ad_bench") or {}).get(kind)
    if bench:
        doc["ad_bench"][kind] = [b for b in bench if _ad_text(b).lower() != text.lower()]
    save(doc)
    log(nn, f"add {word}", text + (f" (slot {pin})" if kind == "headlines" and pin else ""), by=by)
    return {"added": text, "note": "The ad needs your approval again before it is published."}


def set_ad_lines(nn, headlines, descriptions, by="Jonathan"):
    """Save the ad's headlines and descriptions in one go (Jonathan, 2026-09-29: take out, move, and add as many as he
    wants, then save once). The whole set is checked before anything is written: 3 to 15 headlines, 2 to 4
    descriptions, the length caps, the copy rules, no line twice, pins 1 to 3. A line taken out goes to the ad bench;
    a line added back leaves it. The ad's approval clears, as with any edit."""
    doc = load(nn)
    heads = []
    for h in headlines or []:
        text = " ".join(str((h.get("text") if isinstance(h, dict) else h) or "").split())
        pin = h.get("pin") if isinstance(h, dict) else None
        pin = int(pin) if str(pin or "").strip() not in ("", "0", "None", "null") else None
        heads.append({"text": text, **({"pin": pin} if pin else {})})
    descs = [" ".join(str(d or "").split()) for d in descriptions or []]
    probs = []
    for kind, items in (("headlines", [h["text"] for h in heads]), ("descriptions", descs)):
        lo, hi, cap = AD_LIMITS[kind]
        word = AD_WORD[kind]
        if not lo <= len(items) <= hi:
            probs.append(f"{len(items)} {kind}: an ad takes {lo} to {hi}.")
        seen = set()
        for t in items:
            if not t:
                probs.append(f"An empty {word}.")
                continue
            if len(t) > cap:
                probs.append(f"\"{t}\" is {len(t)} characters: a {word} takes at most {cap}.")
            flags = ads_lint.check_text(t)
            if flags:
                probs.append(f"\"{t}\": {'; '.join(flags)}.")
            if t.lower() in seen:
                probs.append(f"\"{t}\" is in the ad twice.")
            seen.add(t.lower())
    probs += [f"\"{h['text']}\": a headline pins to slot 1, 2, or 3." for h in heads if h.get("pin") and h["pin"] not in PIN]
    if probs:
        raise Refused(" ".join(probs[:6]) + (f" And {len(probs) - 6} more." if len(probs) > 6 else ""))
    old_h, old_d = doc["ad"]["headlines"], doc["ad"]["descriptions"]
    old_h_clean = [{"text": h["text"], **({"pin": h["pin"]} if h.get("pin") else {})} for h in old_h]
    if heads == old_h_clean and descs == old_d:
        return {"changed": False, "note": "Nothing changed."}
    keep = {h["text"].lower() for h in heads} | {d.lower() for d in descs}
    was = {_ad_text(x).lower() for x in old_h + old_d}
    bench = doc.setdefault("ad_bench", {})
    for kind, old in (("headlines", old_h), ("descriptions", old_d)):
        b = bench.setdefault(kind, [])
        for line in old:
            if _ad_text(line).lower() not in keep and all(_ad_text(x).lower() != _ad_text(line).lower() for x in b):
                b.append(line)
        bench[kind] = [x for x in b if _ad_text(x).lower() not in keep]
    added = [t for t in [h["text"] for h in heads] + descs if t.lower() not in was]
    removed = [_ad_text(x) for x in old_h + old_d if _ad_text(x).lower() not in keep]
    doc["ad"]["headlines"], doc["ad"]["descriptions"] = heads, descs
    save(doc)
    log(nn, "edit ad", f"{len(added)} added, {len(removed)} taken out; now {len(heads)} headlines, {len(descs)} descriptions", by=by)
    return {"changed": True, "added": added, "removed": removed,
            "note": "Saved. The ad needs your approval again before it is published."}


KW_MAX = 50  # per campaign; the method picks about 12 (keywords/method.md), Google allows far more
KW_BAD_CHARS = re.compile(r"[!@%^*=;~`<>?\\|{}\[\]\"]")


class WeakKeywords(Refused):
    """New keywords that miss the buying-intent test; the screen offers Save anyway."""

    def __init__(self, weak):
        self.weak = weak
        super().__init__("These miss the buying-intent test: " + "; ".join(f"\"{k}\": {', '.join(v)}" for k, v in weak.items()))


def set_keywords(nn, keywords, allow_weak=False, by="Jonathan"):
    """Save the campaign's keywords in one go (Jonathan, 2026-10-01: "I should be able to delete and add keywords").
    Each goes in exact and phrase. Refused outright: none, more than 50, over 80 characters or 10 words, a character
    Google rejects, or any negative that blocks one (it would never show). A new keyword that misses the buying-intent
    test (a trade and this campaign's service, no learner words) is refused unless allow_weak: his call. A keyword taken
    out goes to the bench; one put back leaves it. The keywords' approval clears; Google changes only on Publish."""
    doc = load(nn)
    new = []
    for k in keywords or []:
        t = " ".join(str(k or "").lower().split())
        if t and t not in new:
            new.append(t)
    probs = []
    if not 1 <= len(new) <= KW_MAX:
        probs.append(f"{len(new)} keywords: a campaign takes 1 to {KW_MAX}.")
    for t in new:
        if len(t) > 80 or len(t.split()) > 10:
            probs.append(f"\"{t}\" is too long (80 characters and 10 words at most).")
        if KW_BAD_CHARS.search(t):
            probs.append(f"\"{t}\" has a character Google refuses in a keyword.")
    old_by_text = {k["text"]: k for k in doc["keywords"]}
    trial = dict(doc, keywords=[{"text": t, "match": (old_by_text.get(t) or {}).get("match", ["exact", "phrase"])} for t in new])
    probs += [p for p in negatives_block_keywords(trial) if "blocks" in p]
    if probs:
        raise Refused("Not saved: " + "; ".join(p.rstrip(".") for p in probs[:6]) + "."
                      + (f" And {len(probs) - 6} more." if len(probs) > 6 else ""))
    added = [t for t in new if t not in old_by_text]
    removed = [t for t in old_by_text if t not in new]
    weak = {t: p for t in added if (p := buying_intent_problems(nn, t))}
    if weak and not allow_weak:
        raise WeakKeywords(weak)
    if not added and not removed and [k["text"] for k in doc["keywords"]] == new:
        return {"changed": False, "note": "Nothing changed."}
    doc["keywords"] = trial["keywords"]
    bench = [b for b in doc.get("bench", []) if b not in new]
    doc["bench"] = bench + [t for t in removed if t not in bench]
    save(doc)
    log(nn, "edit keywords", f"{len(added)} added, {len(removed)} taken out; now {len(new)}"
        + (f"; saved anyway: {', '.join(weak)}" if weak else ""), by=by)
    return {"changed": True, "added": added, "removed": removed, "weak": weak,
            "note": "Saved. Approve the keywords again" + ("; Publish changes sends them to Google." if (doc.get("google") or {}).get("campaign") else ".")}


def unapprove(nn, part, group=None, by="Jonathan"):
    """Take an approval back. Publish is blocked until it is approved again; a live campaign keeps running until paused."""
    doc = load(nn)
    appr = doc.setdefault("approvals", {})
    if part in ("spend", "keywords", "ad"):
        if not appr.pop(part, None):
            raise Refused("It is not approved now.")
    elif part == "negatives":
        g = next((x for x in negative_groups(doc) if x["name"] == group), None)
        if not g:
            raise Refused(f"No negative list named \"{group}\" on campaign {nn}.")
        if g["scope"] == "shared":
            shared_ok = _read_json(SHARED_APPROVALS, {})
            if not shared_ok.pop(group, None):
                raise Refused("That list is not approved now.")
            _write_json(SHARED_APPROVALS, shared_ok)
        elif not (appr.get("negatives") or {}).pop(group, None):
            raise Refused("That list is not approved now.")
    else:
        raise Refused(f"Unknown approval \"{part}\" (spend, keywords, negatives, ad).")
    save(doc)
    log(nn, f"take back {part}", group or "", by=by)
    return {"taken_back": part, "group": group}


# ---------------------------------------------------------------- the screen's view

def card(doc):
    st = approval_state(doc)
    gstate = doc.get("google") or {}
    gates = gate_state(doc["nn"])
    waiting = unpublished_changes(doc) if gstate.get("campaign") else []
    try:
        cap_check(doc)
        cap_note = ""
    except Refused as e:
        cap_note = str(e)
    return {
        "nn": doc["nn"], "name": doc["name"], "service": doc["service"], "page": doc["page"], "slot": doc["slot"],
        "daily_budget": doc["daily_budget"], "max_cpc": doc["bidding"]["max_cpc"],
        "places": len(_read_json(GEO_IDS, {})) or sum(1 for ln in (ROOT / doc["geo"]["file"]).read_text(encoding="utf-8").splitlines() if ln.strip()),
        "keywords": [k["text"] for k in doc["keywords"]], "bench": doc.get("bench", []),
        "ad": doc["ad"], "ad_problems": ad_problems(doc), "ad_bench": doc.get("ad_bench") or {},
        "ad_limits": {k: {"min": v[0], "max": v[1], "chars": v[2]} for k, v in AD_LIMITS.items()},
        "approvals": {p: st[p] for p in ("spend", "keywords", "negatives", "ad")},
        "approved_at": {p: ((doc.get("approvals") or {}).get(p) or {}).get("at") for p in ("spend", "keywords", "ad")},
        "groups": st["groups"], "ready": st["ready"],
        "gates": gates, "gates_ok": all(x["ok"] for x in gates),
        "published": bool(gstate.get("campaign")), "published_at": gstate.get("published_at"),
        "status": gstate.get("status") or "not published", "waiting": waiting,
        "cap_note": cap_note, "running_total": running_total(), "cap": DAILY_CAP,
        "live": gstate.get("live") or {},
    }


def cards():
    return [card(d) for d in all_campaigns()]


# ---------------------------------------------------------------- CLI

def _print_status():
    for c in cards():
        a = c["approvals"]
        print(f"{c['nn']} {c['name']:<28} ${c['daily_budget']}/day {c['slot']:<6} {c['status']:<14} "
              f"spend {a['spend']}, keywords {a['keywords']}, negatives {a['negatives']}, ad {a['ad']}"
              + (f"; waiting: {', '.join(c['waiting'])}" if c["waiting"] else ""))
    print(f"Running: ${running_total()} of ${DAILY_CAP} a day.")
    gates = gate_state("01")
    print("Gates: " + "; ".join(f"{x['name']}: {'done' if x['ok'] else 'open'}" for x in gates))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--validate-only", action="store_true")
    ap.add_argument("--shared", default=None, help="add the negative to this shared list instead of the campaign's")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    nn = a.args[0].zfill(2) if a.args and a.args[0].isdigit() else None
    try:
        if a.cmd == "status":
            _print_status()
        elif a.cmd == "plan":
            doc = load(nn)
            o = build_ops(doc, "0000000000", {n: f"geoTargetConstants/{i}" for i, n in enumerate(
                ln.strip() for ln in (ROOT / doc["geo"]["file"]).read_text(encoding="utf-8").splitlines() if ln.strip())})
            print(f"Publish {doc['name']} would send {len(o.ops)} operations (x2 with the rehearsal):")
            for k, v in sorted(o.counts().items()):
                print(f"  {v:5}  {k}")
        elif a.cmd == "approve":
            part, _, group = a.args[1].partition(":")
            approve(nn, part, group or None)
            print(json.dumps({k: v for k, v in approval_state(load(nn)).items() if k != "groups"}))
        elif a.cmd == "publish":
            print(json.dumps(publish(nn, validate_only=a.validate_only), indent=1))
        elif a.cmd == "golive":
            golive(nn)
            print("Live.")
        elif a.cmd == "pause":
            pause(nn)
            print("Paused.")
        elif a.cmd == "budget":
            set_budget(nn, a.args[1])
            print(f"Budget ${a.args[1]} a day.")
        elif a.cmd == "negative":
            print(json.dumps(add_negative(nn, a.args[1], a.shared)))
        elif a.cmd == "swap":
            print(json.dumps(swap_keyword(nn, a.args[1], a.args[2])))
        elif a.cmd == "fix":
            print(json.dumps(fix(a.args[0])))
        elif a.cmd == "tick":
            tick(a.args[0])
            print("Ticked.")
        elif a.cmd == "gates":
            if a.refresh:
                refresh_gates()
            for x in gate_state(nn or "01"):
                print(f"  {'done' if x['ok'] else 'open':5} {x['name']}: {x['note']}")
        elif a.cmd == "geo":
            ids = geo_ids()
            miss = [n for n, v in ids.items() if not v]
            print(f"{len(ids) - len(miss)} of {len(ids)} places have a Google location id."
                  + (f" Not found: {'; '.join(miss)}" if miss else ""))
        else:
            sys.exit(__doc__)
    except Refused as e:
        sys.exit(f"Refused: {e}")
    except Exception as e:  # noqa: BLE001
        lines = getattr(e, "lines", None)
        sys.exit("Google refused:\n  " + "\n  ".join(lines) if lines else f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
