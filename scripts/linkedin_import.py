"""LinkedIn messaging into the Monarc CRM, from LinkedIn's own data export (2026-09-28).

LinkedIn has no messaging API for a personal account, so once a week: LinkedIn, Settings & Privacy, Data privacy,
Get a copy of your data, pick Connections, Invitations, and Messages, Request archive. The email with the download
arrives in about ten minutes. Then:

  python scripts/linkedin_import.py <the .zip or the unzipped folder>            dry run: prints every thread it found
  python scripts/linkedin_import.py <zip> --write                                 upserts the LinkedIn threads table
  options: --since YYYY-MM-DD (default: the Started date of the "LinkedIn messaging" campaign), --me "Full Name"

One row per person Jonathan reached out to: a connection request he sent on or after --since, or a one-to-one
conversation he started on or after --since. Conversations the other person started (recruiters, pitches) are left
out. Matched on the profile URL. The import owns the dates, the message counts, and Stage (Request sent, Accepted,
Messaged, Replied); Outcome and Notes are Jonathan's and never written. A thread gets linked to a CRM company when the
person's company on LinkedIn matches a Companies name and the row has no company yet.

The export's column names are read loosely (case, spaces, and underscores ignored) because LinkedIn has renamed them
before. The dry run prints the counts per file so a changed export shows at once.
"""
import argparse
import csv
import io
import re
import sys
import zipfile
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import get_secret  # noqa: E402
from crm_server import Airtable  # noqa: E402

BASE_ID = "appgv3njf5Fk99QXo"      # Monarc CRM
THREADS = "LinkedIn threads"
CAMPAIGN_PID = "linkedin-messaging"
ET = ZoneInfo("America/New_York")


# ---------------------------------------------------------------- reading the export

def read_files(path):
    """{lowercase file name: text} for the CSVs in a LinkedIn export zip or folder."""
    p = Path(path)
    out = {}
    if p.is_file() and p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                if n.lower().endswith(".csv"):
                    out[Path(n).name.lower()] = z.read(n).decode("utf-8-sig", errors="replace")
    elif p.is_dir():
        for f in p.rglob("*.csv"):
            out[f.name.lower()] = f.read_text(encoding="utf-8-sig", errors="replace")
    else:
        sys.exit(f"Not a .zip or a folder: {p}")
    return out


def norm_key(k):
    return re.sub(r"[\s_]+", "", (k or "").strip().lower())


def table(text, must):
    """Rows as dicts with normalized keys. Skips the notes LinkedIn puts above the header (Connections.csv)."""
    if not text:
        return []
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if norm_key(must) in norm_key(ln)), 0)
    reader = csv.DictReader(io.StringIO("\n".join(lines[start:])))
    return [{norm_key(k): (v or "").strip() for k, v in r.items() if k} for r in reader]


def parse_day(s):
    """The date in Eastern time from any of LinkedIn's date styles, or None."""
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S UTC", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc).astimezone(ET).date()
        except ValueError:
            pass
    for fmt in ("%m/%d/%y, %I:%M %p", "%m/%d/%Y, %I:%M %p", "%d %b %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def norm_url(u):
    """https://www.linkedin.com/in/<slug>, or '' for anything that is not a profile link."""
    u = (u or "").strip().split("?")[0].rstrip("/").lower()
    m = re.search(r"linkedin\.com/in/([^/\s]+)", u)
    return f"https://www.linkedin.com/in/{m.group(1)}" if m else ""


def split_list(s):
    return [x.strip() for x in re.split(r"[,;]", s or "") if x.strip()]


def norm_company(n):
    n = re.sub(r"[^a-z0-9 ]+", " ", (n or "").lower())
    n = re.sub(r"\b(llc|inc|co|corp|corporation|company|ltd|the)\b", " ", n)
    return re.sub(r"\s+", " ", n).strip()


# ---------------------------------------------------------------- building the threads

def build(files, since, me_name=None):
    msgs = table(files.get("messages.csv"), "conversation id")
    invs = table(files.get("invitations.csv"), "direction")
    conns = table(files.get("connections.csv"), "first name")
    counts = {"messages.csv": len(msgs), "invitations.csv": len(invs), "connections.csv": len(conns)}

    # who is "me": the profile in the most conversations (every conversation includes the owner)
    seen = defaultdict(set)
    for m in msgs:
        cid = m.get("conversationid")
        for u in [norm_url(m.get("senderprofileurl"))] + [norm_url(x) for x in split_list(m.get("recipientprofileurls"))]:
            if u:
                seen[u].add(cid)
    me_url = max(seen, key=lambda u: len(seen[u])) if seen else ""
    me_names = {me_name.lower()} if me_name else set()
    if me_url and not me_name:
        me_names = {m.get("from", "").lower() for m in msgs if norm_url(m.get("senderprofileurl")) == me_url}

    def is_me(url, name):
        return (url and url == me_url) or (name or "").lower() in me_names

    people = {}

    def person(url, name):
        key = url or f"name:{(name or '').lower()}"
        by_name = f"name:{(name or '').lower()}"
        if url and name and by_name in people and key not in people:
            people[key] = people.pop(by_name)  # found by name first (an export without profile links), now by link
            people[key]["url"] = url
        p = people.setdefault(key, {"url": url, "name": name or "", "request": None, "accepted": None, "first_msg": None,
                                    "replied": None, "last": None, "sent": 0, "received": 0, "company": "", "position": ""})
        if name and not p["name"]:
            p["name"] = name
        return p

    # connection requests Jonathan sent
    for r in invs:
        if (r.get("direction") or "").upper() != "OUTGOING":
            continue
        d = parse_day(r.get("sentat"))
        if not d or d < since:
            continue
        p = person(norm_url(r.get("inviteeprofileurl")), r.get("to"))
        p["request"] = min(p["request"], d) if p["request"] else d

    # one-to-one conversations Jonathan started
    convs = defaultdict(list)
    for m in msgs:
        if (m.get("ismessagedraft") or "").lower() in ("yes", "true"):
            continue
        d = parse_day(m.get("date"))
        if d:
            convs[m.get("conversationid")].append((d, m))
    for cid, items in convs.items():
        items.sort(key=lambda x: x[0])
        others = {}
        for _, m in items:
            su, sn = norm_url(m.get("senderprofileurl")), m.get("from")
            if not is_me(su, sn):
                others[su or sn] = (su, sn)
            if is_me(su, sn):
                rus = [norm_url(x) for x in split_list(m.get("recipientprofileurls"))]
                rns = [x.strip() for x in (m.get("to") or "").split(",") if x.strip()]
                for i, ru in enumerate(rus or [""] * len(rns)):
                    rn = rns[i] if i < len(rns) else ""
                    if not is_me(ru, rn):
                        others[ru or rn] = (ru, rn)
        if len(others) != 1:
            continue  # group chats and empty threads are not prospecting
        ou, on = next(iter(others.values()))
        first_d, first_m = items[0]
        started_by_me = is_me(norm_url(first_m.get("senderprofileurl")), first_m.get("from"))
        key = ou or f"name:{(on or '').lower()}"
        requested = key in people and people[key]["request"]
        if not started_by_me and not requested:
            continue  # they wrote first (recruiters, pitches) and Jonathan never sent them a request
        mine = [d for d, m in items if is_me(norm_url(m.get("senderprofileurl")), m.get("from"))]
        if not mine or (mine[0] < since and not requested):
            continue
        p = person(ou, on)
        p["first_msg"] = min(p["first_msg"], mine[0]) if p["first_msg"] else mine[0]
        theirs_after = [d for d, m in items if not is_me(norm_url(m.get("senderprofileurl")), m.get("from")) and d >= mine[0]]
        if theirs_after:
            p["replied"] = min(p["replied"], theirs_after[0]) if p["replied"] else theirs_after[0]
        p["last"] = max(p["last"], items[-1][0]) if p["last"] else items[-1][0]
        p["sent"] += len(mine)
        p["received"] += len(items) - len(mine)

    # connections: accepted dates, company, position
    by_url = {norm_url(c.get("url")): c for c in conns if norm_url(c.get("url"))}
    by_name = {f"{c.get('firstname', '')} {c.get('lastname', '')}".strip().lower(): c for c in conns}
    for p in people.values():
        c = by_url.get(p["url"]) or by_name.get((p["name"] or "").lower())
        if not c:
            continue
        p["company"], p["position"] = c.get("company", ""), c.get("position", "")
        if not p["name"]:
            p["name"] = f"{c.get('firstname', '')} {c.get('lastname', '')}".strip()
        con = parse_day(c.get("connectedon"))
        if con and p["request"]:
            p["accepted"] = con  # only a request Jonathan sent can be accepted; an older connection is just messaged
    for p in people.values():
        p["stage"] = ("Replied" if p["replied"] else "Messaged" if p["first_msg"] else
                      "Accepted" if p["accepted"] else "Request sent")
    return people, counts, me_url or ", ".join(sorted(me_names))


# ---------------------------------------------------------------- writing

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("export", help="LinkedIn data export: the .zip, or the folder it unzips to")
    ap.add_argument("--since", help="YYYY-MM-DD; default the Started date of the LinkedIn messaging campaign")
    ap.add_argument("--me", help="your name as LinkedIn writes it, if the owner guess is wrong")
    ap.add_argument("--write", action="store_true", help="upsert the LinkedIn threads table (default: dry run)")
    a = ap.parse_args()

    air = Airtable(get_secret("AIRTABLE_PAT", required=True, hint="The CRM token, in %USERPROFILE%\\.monarc\\secrets.env."), BASE_ID)
    camps, _ = air.list_all("Campaigns", formula=f"{{Platform id}}='{CAMPAIGN_PID}'")
    camp = camps[0] if camps else None
    since = date.fromisoformat(a.since) if a.since else (
        date.fromisoformat(camp["fields"]["Started"]) if camp and camp["fields"].get("Started") else date(2026, 9, 1))

    people, counts, me = build(read_files(a.export), since, a.me)
    print(f"Export: {counts}. Owner read as: {me or '?'}. Window: {since} on.")
    if not counts["messages.csv"] and not counts["invitations.csv"]:
        sys.exit("No messages.csv or Invitations.csv in the export. Request Messages and Invitations in LinkedIn's data download.")

    comps, _ = air.list_all("Companies", fields=["Name"])
    comp_by = {norm_company(c["fields"].get("Name")): c["id"] for c in comps if c["fields"].get("Name")}
    existing, _ = air.list_all(THREADS)
    have = {}
    for r in existing:
        f = r["fields"]
        have[norm_url(f.get("Profile URL")) or f"name:{(f.get('Person') or '').lower()}"] = r

    creates, updates = [], []
    today = date.today().isoformat()
    for key, p in sorted(people.items(), key=lambda kv: (kv[1]["name"] or "").lower()):
        iso = lambda d: d.isoformat() if d else None  # noqa: E731
        f = {"Person": p["name"] or p["url"], "Profile URL": p["url"] or None, "Company on LinkedIn": p["company"] or None,
             "Position": p["position"] or None, "Stage": p["stage"], "Request sent": iso(p["request"]), "Accepted": iso(p["accepted"]),
             "First message": iso(p["first_msg"]), "Replied": iso(p["replied"]), "Last message": iso(p["last"]),
             "Sent": p["sent"], "Received": p["received"], "Imported": today}
        if camp:
            f["Campaign"] = [camp["id"]]
        cid = comp_by.get(norm_company(p["company"])) if p["company"] else None
        row = have.get(key)
        if row:
            if cid and not row["fields"].get("Company"):
                f["Company"] = [cid]
            updates.append((row["id"], f))
        else:
            if cid:
                f["Company"] = [cid]
            creates.append(f)
        print(f"  {p['stage']:13} {(p['name'] or '?')[:28]:28} {(p['company'] or '')[:28]:28} "
              f"req {iso(p['request']) or '-':10} acc {iso(p['accepted']) or '-':10} msg {iso(p['first_msg']) or '-':10} "
              f"rep {iso(p['replied']) or '-':10}{'  CRM: linked' if cid else ''}")

    n = len(people)
    st = {s: sum(1 for p in people.values() if p["stage"] == s) for s in ("Request sent", "Accepted", "Messaged", "Replied")}
    print(f"\n{n} people: {st}. New rows {len(creates)}, updated {len(updates)}.")
    if not a.write:
        print("Dry run. Nothing written. Add --write to save.")
        return
    air.create(THREADS, creates)
    air.update(THREADS, updates)
    print(f"Written to {THREADS}: {len(creates)} new, {len(updates)} updated. {air.calls} API calls.")


if __name__ == "__main__":
    main()
