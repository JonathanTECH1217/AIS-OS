"""Apollo: the owner's email and LinkedIn for a company, by its domain (Jonathan, 2026-10-06: "Do we have apollo to get the
owner email and linkedin", then "lets hook up a clay account or apollo").

Two steps, the way Apollo's API splits them (references/apollo-api.md):
  1. search, free: POST /api/v1/mixed_people/api_search with the domain and the seniorities owner, founder, c_suite,
     partner. It returns people with an id, first name, title, and whether Apollo has an email. No email comes back yet.
  2. reveal, costs credits: POST /api/v1/people/bulk_match with those ids (10 a call). It returns the email and the
     LinkedIn URL. Nothing is revealed without --yes: the script quotes the people and the credits first.

  python scripts/apollo_enrich.py check                         is the key set and does Apollo answer
  python scripts/apollo_enrich.py search <domain> [<domain>...]  the owners and founders at each, free
  python scripts/apollo_enrich.py batch <date>                    search for every batch row with no address (free), and say
                                                                 how many credits the reveal would take
  python scripts/apollo_enrich.py batch <date> --reveal --yes     reveal, write to + first into projects/loom-b-and-a/batches/<date>.json
                                                                 (only rows with no address), save everything to projects/research/<slug>/apollo.json

Key: APOLLO_API_KEY in %USERPROFILE%/.monarc/secrets.env or the repo .env (scripts/outreach_common.get_secret). A master key,
or one scoped to mixed_people/api_search and people/bulk_match. Never written to any tracked file.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import ROOT, get_secret, load_env  # noqa: E402

API = "https://api.apollo.io/api/v1"
SENIORITY = ["owner", "founder", "c_suite", "partner"]
RANK = {"owner": 0, "founder": 1, "c_suite": 2, "partner": 3}


def headers():
    load_env()
    key = get_secret("APOLLO_API_KEY")
    if not key:
        sys.exit("APOLLO_API_KEY is not set. Put it in %USERPROFILE%/.monarc/secrets.env as APOLLO_API_KEY=... (never in chat).")
    return {"X-Api-Key": key, "Content-Type": "application/json", "Cache-Control": "no-cache", "Accept": "application/json"}


def post(path, body):
    for attempt in range(3):
        r = requests.post(f"{API}/{path}", headers=headers(), json=body, timeout=40)
        if r.status_code == 429:
            time.sleep(20 * (attempt + 1))
            continue
        if r.status_code >= 400:
            sys.exit(f"Apollo answered {r.status_code} on {path}: {r.text[:300]}")
        return r.json()
    sys.exit(f"Apollo kept answering 429 on {path}; try again later.")


def search(domain):
    """The owners and founders Apollo knows at a domain, best first. Free."""
    d = post("mixed_people/api_search", {"q_organization_domains_list": [domain], "person_seniorities": SENIORITY,
                                          "page": 1, "per_page": 10})
    people = d.get("people") or []
    def score(p):
        t = (p.get("title") or "").lower()
        hit = 0 if "owner" in t else 1 if "founder" in t else 2 if "president" in t or "ceo" in t else 3
        return (hit, 0 if p.get("has_email") else 1)
    return sorted(people, key=score)


def reveal(ids):
    out = []
    for i in range(0, len(ids), 10):
        d = post("people/bulk_match", {"details": [{"id": x} for x in ids[i:i + 10]], "reveal_personal_emails": False})
        out += d.get("matches") or []
    return out


def cmd_check(_a):
    d = post("mixed_people/api_search", {"q_organization_domains_list": ["apollo.io"], "person_seniorities": ["c_suite"], "per_page": 1})
    print(f"Apollo answers: {len(d.get('people') or [])} person back from a free search. The key works.")


def cmd_search(a):
    for dom in a.domains:
        people = search(dom)
        print(f"{dom}: {len(people)} owner, founder, or C-suite people")
        for p in people[:5]:
            print(f"   {p.get('first_name')} {p.get('last_name_obfuscated') or ''} | {p.get('title')} | email on file: {p.get('has_email')} | id {p.get('id')}")


def cmd_batch(a):
    f = ROOT / "projects" / "loom-b-and-a" / "batches" / f"{a.date}.json"
    batch = json.loads(f.read_text(encoding="utf-8"))
    targets = [r for r in batch["rows"] if not r.get("to")]
    if not targets:
        print("Every row in the batch has an address.")
        return
    picks = []
    for r in targets:
        dom = r.get("domain") or ""
        if not dom:
            site = ROOT / "projects" / "research" / r["slug"].replace("-v2", "") / "site.json"
            try:
                from urllib.parse import urlparse
                dom = urlparse(json.loads(site.read_text(encoding="utf-8")).get("url", "")).netloc.replace("www.", "")
            except (OSError, ValueError):
                dom = ""
        if not dom:
            print(f"{r['company']}: no domain on file; skipped")
            continue
        people = [p for p in search(dom) if p.get("has_email")]
        best = people[0] if people else None
        print(f"{r['company']} ({dom}): " + (f"{best.get('first_name')} {best.get('last_name_obfuscated') or ''}, {best.get('title')}" if best else "no owner with an email in Apollo"))
        if best:
            picks.append((r, dom, best))
    print(f"\nA reveal would take about {len(picks)} credits (one a person, Apollo's rate on email reveals).")
    if not a.reveal:
        print("Nothing revealed. Run again with --reveal --yes to spend them.")
        return
    if not a.yes:
        sys.exit("--reveal needs --yes: credits are spent only on his go.")
    found = {m.get("id"): m for m in reveal([p[2]["id"] for p in picks])}
    for r, dom, p in picks:
        m = found.get(p["id"]) or {}
        email, li = m.get("email"), m.get("linkedin_url")
        save = ROOT / "projects" / "research" / r["slug"].replace("-v2", "")
        save.mkdir(parents=True, exist_ok=True)
        (save / "apollo.json").write_text(json.dumps({"domain": dom, "person": {k: m.get(k) for k in ("first_name", "last_name", "title", "email", "linkedin_url", "email_status")},
                                                       "found": time.strftime("%Y-%m-%d")}, indent=1), encoding="utf-8")
        if email and not r.get("to"):
            r["to"], r["first"] = email, (m.get("first_name") or "")
            r["note"] = f"{(r.get('note') or '').strip()} Apollo, {time.strftime('%Y-%m-%d')}: {m.get('title')}; LinkedIn {li or 'none'}.".strip()
        print(f"{r['company']}: {email or 'no email'} | {li or 'no LinkedIn'}")
    f.write_text(json.dumps(batch, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Written to {f.relative_to(ROOT).as_posix()}. Then: python scripts/loom_ba_batch.py drafts {a.date}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    s = sub.add_parser("search")
    s.add_argument("domains", nargs="+")
    b = sub.add_parser("batch")
    b.add_argument("date")
    b.add_argument("--reveal", action="store_true")
    b.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    {"check": cmd_check, "search": cmd_search, "batch": cmd_batch}[a.cmd](a)


if __name__ == "__main__":
    main()
