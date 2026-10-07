"""The SDR's inbox: a reply comes in, the drip stops, and a question about times is answered from the calendar.

Jonathan, 2026-10-05: "Only prospects in the pipeline get automated responses and a response cancels the drip
sequence." And, after he answered a test email with "What is your availability this afternoon?": "this one's asking
about availability, which should be an automated response that checks my calendar's availability and then schedules
for a meeting."

  python scripts/sdr_inbox.py check          one pass: find new replies on the SDR's threads and act on each
  python scripts/sdr_inbox.py watch [N]      the same, every N seconds (default 120), until stopped
  python scripts/sdr_inbox.py status         the threads and where each stands

One pass, per reply:
  1. Is it on a thread the SDR started (projects/sdr/threads.json)? Those are the prospects in the pipeline. Mail from
     anyone else is not touched.
  2. The drip on that thread is cancelled, whatever the reply says.
  3. The reply is sorted by plain rules (projects/sdr/config.json, "phrases"; no model): stop, a picked time, a
     question about times, or anything else. Anything else waits for him.
  4. A question about times: his calendars are read (the Monarc login, scripts/google_calendar_api.py), two open
     times are picked inside the hours in the config, and the answer is written from the "times" copy.
  5. A picked time: the meeting is put on the calendar and the "booked" copy answers.

What it can and cannot do today:
  - It cannot read patrick@monarcbuild.com. That mailbox is its own Proton sign-in, not an address on Jonathan's, and
    it is not in Bridge. Until PROTON_SDR_USER and PROTON_SDR_BRIDGE_PASS are in .env, only TEST threads work: he plays
    the prospect, so his answer sits in his own Sent folder, and that is where it is read.
  - It sends nothing. "send" and "book" in the config are off and the AIOS never turns them on. An answer on a test
    thread is laid in his own INBOX (IMAP append, as inbox-test does); on a real thread it is laid in Drafts. A picked
    time on a test thread puts a quiet hold on his calendar with no guest; on a real thread it waits for him.

No third-party mail packages; the calendar read uses requests through google_calendar_api.
"""
import email
import imaplib
import json
import re
import sys
import time
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import proton_mail as pm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "projects" / "sdr"
CONFIG, THREADS, LOG = DIR / "config.json", DIR / "threads.json", DIR / "log.jsonl"
HOME = ZoneInfo("America/New_York")
ZONES = {"America/New_York": "Eastern", "America/Chicago": "Central", "America/Denver": "Mountain",
         "America/Phoenix": "Arizona", "America/Los_Angeles": "Pacific"}
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def save_threads(threads):
    THREADS.write_text(json.dumps({"_about": "The threads the SDR started: its prospects in the pipeline. Written by scripts/sdr_inbox.py.",
                                   "threads": threads}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def log(**row):
    row = dict(at=datetime.now(HOME).isoformat(timespec="seconds"), **row)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


# ---------------------------------------------------------------- the mailbox

def fetch(m, folder, criteria):
    m.select(f'"{folder}"', readonly=True)
    typ, data = m.search(None, *criteria)
    out = []
    for i in (data[0].split() if typ == "OK" else []):
        typ, d = m.fetch(i, "(BODY.PEEK[])")
        if typ == "OK" and d and d[0]:
            out.append(email.message_from_bytes(d[0][1]))
    return out


def own_words(msg):
    """What the person wrote, without the mail they were answering."""
    text = pm.body_text(msg, 6000)
    keep = []
    for ln in text.splitlines():
        if re.match(r"^\s*On .{5,90} wrote:\s*$", ln) or ln.strip().startswith((">", "-----Original", "From:")):
            break
        keep.append(ln)
    return "\n".join(keep).strip()


def adopt_tests(m, cfg, threads, me):
    """A test email laid in his INBOX (proton_mail.py inbox-test) starts a test thread, with him as the prospect."""
    known = {t["id"] for t in threads}
    for msg in fetch(m, "INBOX", ("FROM", f'"{cfg["mailbox"]}"')):
        mid = (msg.get("Message-ID") or "").strip()
        if not msg.get("X-Monarc-Test") or not mid or mid in known or msg.get("In-Reply-To"):
            continue
        first = (re.match(r"\s*([A-Z][a-z]+),", pm.body_text(msg, 200)) or [None, "there"])[1]
        threads.append({"id": mid, "ids": [mid], "to": me, "first": first, "zone": "America/New_York", "test": True,
                        "subject": str(msg.get("Subject", "")), "started": datetime.now(HOME).isoformat(timespec="minutes"),
                        "drip": "running", "status": "sent", "seen": [], "offered": [], "scene": msg.get("X-Monarc-Test")})
        known.add(mid)
        log(what="thread adopted", thread=mid, test=True)


def replies(m, cfg, threads, me):
    """New messages on the SDR's threads. Test threads are read from his own Sent folder; real ones need the SDR mailbox."""
    out = []
    tests = [t for t in threads if t.get("test")]
    if tests:
        since = (datetime.now(HOME) - timedelta(days=14)).strftime("%d-%b-%Y")
        for msg in fetch(m, "Sent", ("TO", f'"{cfg["mailbox"]}"', "SINCE", since)):
            mid = (msg.get("Message-ID") or "").strip()
            refs = f'{msg.get("In-Reply-To", "")} {msg.get("References", "")}'
            t = next((t for t in tests if any(i in refs for i in t["ids"])), None)
            if t and mid and mid not in t["seen"]:
                out.append((t, msg, mid))
    return out


def lay(m, folder, cfg, t, body, me, subject=None, name=None):
    """Lay the SDR's answer where he will see it: his INBOX on a test thread, Drafts on a real one. Nothing is sent.
    With a subject of its own the message starts fresh (the booking confirmation); without one it answers the thread."""
    last = t["ids"][-1]
    msg = EmailMessage()
    msg["From"] = f'{name or cfg["name"]} <{cfg["mailbox"]}>'
    msg["To"] = t["to"]
    subj = t.get("subject", "")
    msg["Subject"] = subject or (subj if subj.lower().startswith("re:") else "Re: " + subj)
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=me.split("@")[-1])
    if not subject:
        msg["In-Reply-To"] = last
        msg["References"] = " ".join(t["ids"])
    if t.get("test"):
        msg["X-Monarc-Test"] = "sdr inbox-replies"
    msg.set_content(body.strip() + "\n")
    msg.add_alternative(pm.body_html(body), subtype="html")
    flags = "\\Draft" if folder == "Drafts" else ""
    if folder == "Drafts" and pm.same_mail(m, t["to"], msg["Subject"], days=2):
        raise RuntimeError(f'not drafted: mail to {t["to"]} with the subject "{msg["Subject"]}" is already in Drafts or Sent')
    typ, resp = m.append(folder, flags, imaplib.Time2Internaldate(time.time()), msg.as_bytes())
    if typ != "OK":
        raise RuntimeError(f"APPEND to {folder} failed: {resp}")
    if not subject:
        t["ids"].append(msg["Message-ID"])
    return msg["Message-ID"]


def booked_mail(m, folder, cfg, t, me, pick, meet):
    """What a prospect gets once a time is theirs (Jonathan, 2026-10-05: "it should just respond with the meeting
    link. I was also not sent a confirmation email"): the answer on the thread, which is the time and the Meet link and
    nothing else, and a confirmation of its own in the booking's voice (no person's name, as on the site)."""
    their = ZoneInfo(t["zone"])
    there, now = pick.astimezone(their), datetime.now(their)
    label = ZONES.get(t["zone"], t["zone"])
    day = "Today" if there.date() == now.date() else "Tomorrow" if there.date() == now.date() + timedelta(days=1) else DAYS[there.weekday()].capitalize()
    east = "" if t["zone"] == "America/New_York" else f" ({clock(pick, 'America/New_York')} Eastern)"
    when = f"{day} at {clock(pick, t['zone'])}, {label}{east}"
    ampm = "am" if there.hour < 12 else "pm"
    when_long = f"{DAYS[there.weekday()].capitalize()}, {there.strftime('%b')} {there.day}, {clock(pick, t['zone'])} {ampm} {label}{east}"
    reply = cfg["copy"]["booked"].format(first=t["first"], when=when, meet=meet)
    lay(m, folder, cfg, t, reply, me)
    conf = cfg["copy"]["confirmation"].format(first=t["first"], when_long=when_long, meet=meet)
    subject = cfg["copy"]["confirmation_subject"].format(weekday=DAYS[there.weekday()].capitalize(), time=f"{clock(pick, t['zone'])} {ampm}")
    lay(m, folder, cfg, t, conf, me, subject=subject, name=cfg.get("booking_name", "Monarc Build"))
    return reply, subject, conf


# ---------------------------------------------------------------- sorting, by plain rules

def sort(text, cfg, t):
    low = " " + re.sub(r"\s+", " ", text.lower()) + " "
    if any(re.search(r"\b" + re.escape(p) + r"\b", low) for p in cfg["phrases"]["stop"]):
        return "stop", None
    pick = picked(low, t)
    if pick:
        return "pick", pick
    if any(p in low for p in cfg["phrases"]["times"]):
        return "times", None
    return "other", None


def picked(low, t):
    """Which offered time the reply takes: by the clock time in it, or by "the first" or "the second"."""
    offered = [datetime.fromisoformat(x) for x in t.get("offered", [])]
    if not offered:
        return None
    for mm in re.finditer(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)?", low):
        h, mi, ap = int(mm.group(1)), int(mm.group(2) or 0), (mm.group(3) or "")[:1]
        for o in offered:
            for local in (o.astimezone(ZoneInfo(t.get("zone", "America/New_York"))), o.astimezone(HOME)):  # their clock, or his
                if h == (local.hour % 12 or 12) and mi == local.minute and (not ap or (ap == "p") == (local.hour >= 12)) \
                        and (mm.group(2) or ap or re.search(r"\bat\s+" + mm.group(1) + r"\b", low)):
                    return o
    if re.search(r"\b(first|earlier|former)\b", low):
        return offered[0]
    if len(offered) > 1 and re.search(r"\b(second|later|latter)\b", low):
        return offered[1]
    return None


# ---------------------------------------------------------------- the calendar

def busy(lo, hi):
    """Every stretch already taken on his calendars between two times. Raises if the calendar cannot be read."""
    import google_calendar_api as gcal
    cal = gcal.Calendar()
    cals = load(ROOT / "projects" / "crm" / "config.json", {}).get("calendars") or [{"id": "primary"}]
    out = []
    for c in cals:
        items, _ = cal.window(c["id"], lo, hi)
        for ev in items:
            st, en = ev.get("start") or {}, ev.get("end") or {}
            if ev.get("status") == "cancelled" or ev.get("transparency") == "transparent" or "dateTime" not in st:
                continue
            out.append((datetime.fromisoformat(st["dateTime"].replace("Z", "+00:00")), datetime.fromisoformat(en["dateTime"].replace("Z", "+00:00"))))
    return out


def asked_window(text, now):
    """The day and part of day the reply asks about, in the prospect's own clock. None means no day was named."""
    low = text.lower()
    day = None
    if "today" in low or "this afternoon" in low or "this morning" in low:
        day = now.date()
    elif "tomorrow" in low:
        day = (now + timedelta(days=1)).date()
    else:
        for i, name in enumerate(DAYS):
            if re.search(r"\b" + name + r"\b", low):
                day = (now + timedelta(days=(i - now.weekday()) % 7 or 7)).date()
                break
    part = "afternoon" if "afternoon" in low else "morning" if "morning" in low else None
    return day, part


def open_times(cfg, zone, day=None, part=None, now=None):
    """Two open times: inside his hours, clear of his calendar and the blocked stretches, far enough ahead. Looks in the
    day and part asked for first; if fewer than two are left there, it looks on through the next working days."""
    h = cfg["hours"]
    now = now or datetime.now(HOME)
    their = ZoneInfo(zone)
    length = timedelta(minutes=cfg["meeting"]["minutes"])
    first_day = now.date()
    taken = busy(datetime.combine(first_day, datetime.min.time(), HOME), datetime.combine(first_day + timedelta(days=h["days_ahead"] + 4), datetime.min.time(), HOME))

    def hm(s):
        return int(s[:2]), int(s[3:])

    def slots(d, only_part=None):
        out = []
        t = datetime.combine(d, datetime.min.time(), HOME).replace(hour=hm(h["start"])[0], minute=hm(h["start"])[1])
        end = t.replace(hour=hm(h["end"])[0], minute=hm(h["end"])[1])
        while t + length <= end:
            ok = t >= now + timedelta(minutes=h["lead_minutes"]) and d.weekday() < 5
            for a, b in h.get("blocked", []):
                ok = ok and not (t < t.replace(hour=hm(b)[0], minute=hm(b)[1]) and t + length > t.replace(hour=hm(a)[0], minute=hm(a)[1]))
            ok = ok and not any(t < e and t + length > s for s, e in taken)
            there = t.astimezone(their)
            hour_there = there.hour
            # inside working hours on their clock too: nobody is offered 6:00 in the morning
            ok = ok and (there.hour, there.minute) >= hm(h["start"]) and ((there + length).hour, (there + length).minute) <= hm(h["end"])
            if only_part == "afternoon":
                ok = ok and hour_there >= 12
            if only_part == "morning":
                ok = ok and hour_there < 12
            if ok:
                out.append(t)
            t += timedelta(minutes=h["step_minutes"])
        return out

    def two(found):
        if len(found) < 2:
            return found
        same_day = [x for x in found[1:] if x.date() == found[0].date()]
        # the second one is a different part of the day where it can be: 90 minutes on, else the last one left that day
        second = next((x for x in found[1:] if x - found[0] >= timedelta(minutes=90)), same_day[-1] if same_day else found[1])
        return [found[0], second]

    asked = two(slots(day, part)) if day else []
    if len(asked) == 2:
        return asked, True
    found, d = [], (day or first_day)
    for _ in range(h["days_ahead"] + 4):         # the part asked for is spent; the rest of that day still counts
        found += [x for x in slots(d) if x not in found]
        if len(found) >= 2:
            break
        d += timedelta(days=1)
    return two(found), False


def clock(t, zone):
    there = t.astimezone(ZoneInfo(zone))
    return f"{there.hour % 12 or 12}:{there.minute:02d}"


def times_line(times, zone, day, part, in_asked, now):
    """One sentence in his register: "This afternoon I have 3:00 or 4:30, Eastern." """
    label = ZONES.get(zone, zone)
    their = ZoneInfo(zone)
    today = now.astimezone(their).date()

    def when(t):
        d = t.astimezone(their).date()
        if d == today:
            return ("this afternoon" if t.astimezone(their).hour >= 12 else "this morning") + " at " + clock(t, zone)
        if d == today + timedelta(days=1):
            return "tomorrow at " + clock(t, zone)
        return DAYS[d.weekday()].capitalize() + " at " + clock(t, zone)

    east = "" if zone == "America/New_York" else f" ({clock(times[0], 'America/New_York')} or {clock(times[1], 'America/New_York')} Eastern)"
    same_day = times[0].astimezone(their).date() == times[1].astimezone(their).date()
    if in_asked and day == today and part:
        return f"This {part} I have {clock(times[0], zone)} or {clock(times[1], zone)}, {label}{east}."
    lead = f"Nothing is left this {part}. " if (day == today and part and not in_asked) else ""
    if same_day:
        d = times[0].astimezone(their).date()
        name = "Today" if d == today else "Tomorrow" if d == today + timedelta(days=1) else DAYS[d.weekday()].capitalize()
        return f"{lead}{name} I have {clock(times[0], zone)} or {clock(times[1], zone)}, {label}{east}."
    return f"{lead}I have {when(times[0])} or {when(times[1])}, {label}{east}."


# ---------------------------------------------------------------- one pass

def handle(m, cfg, t, msg, mid, me, say):
    text = own_words(msg)
    now = datetime.now(HOME)
    if mid not in t["ids"]:
        t["ids"].append(mid)                     # so the answer threads under the message it answers
    was = t["drip"]
    t["drip"] = "cancelled"                      # a response cancels the drip, whatever it says
    kind, pick = sort(text, cfg, t)
    folder = "INBOX" if t.get("test") else "Drafts"
    did = {"what": "reply", "thread": t["id"], "test": bool(t.get("test")), "said": text[:200], "sorted": kind,
           "drip": f"{was} -> cancelled"}
    if kind == "stop":
        t["status"] = "stop"
        did["did"] = "blocked; nothing goes back"
    elif kind == "times":
        day, part = asked_window(text, now.astimezone(ZoneInfo(t["zone"])))
        times, in_asked = open_times(cfg, t["zone"], day, part, now)
        if len(times) < 2:
            t["status"] = "needs him"
            did["did"] = "no two open times found; left for him"
        else:
            body = cfg["copy"]["times"].format(first=t["first"], times_line=times_line(times, t["zone"], day, part, in_asked, now))
            lay(m, folder, cfg, t, body, me)
            t["offered"] = [x.isoformat() for x in times]
            t["status"] = "times offered"
            did.update(did=f"answer laid in {folder}", offered=t["offered"], answer=body)
    elif kind == "pick":
        their = ZoneInfo(t["zone"])
        there = pick.astimezone(their)
        when = f"{DAYS[there.weekday()].capitalize()} at {clock(pick, t['zone'])}, {ZONES.get(t['zone'], t['zone'])}"
        if now.astimezone(their).date() == there.date():
            when = f"today at {clock(pick, t['zone'])}, {ZONES.get(t['zone'], t['zone'])}"
        if any(pick < e and pick + timedelta(minutes=cfg["meeting"]["minutes"]) > s for s, e in busy(pick - timedelta(hours=1), pick + timedelta(hours=1))):
            t["status"] = "needs him"
            did["did"] = "the picked time was taken in the meantime; left for him"
        elif t.get("test") or cfg.get("book"):
            import google_calendar_api as gcal
            title = cfg["meeting"]["title"].format(first=t["first"]) + (" (SDR test)" if t.get("test") else "")
            guests = () if t.get("test") else (t["to"],)
            ev = gcal.Calendar().create(title, pick, minutes=cfg["meeting"]["minutes"], guests=guests, meet=True,
                                        send=bool(cfg.get("send")) and not t.get("test"),
                                        description="Test booking made by the SDR inbox from a reply. Delete it." if t.get("test") else "Fifteen minutes with Monarc Build.")
            meet = ev.get("hangoutLink") or ""
            body, subject, _ = booked_mail(m, folder, cfg, t, me, pick, meet)
            t.update(status="booked", event=ev.get("id"), booked=pick.isoformat(), meet=meet)
            did.update(did=f'on the calendar; the answer with the Meet link and the confirmation "{subject}" laid in {folder}',
                       event=ev.get("htmlLink"), answer=body)
        else:
            t["status"] = "needs him"
            did["did"] = "a time was picked; booking for real prospects is off, left for him"
    else:
        t["status"] = "needs him"
        did["did"] = "no rule fits; left for him"
    t["seen"].append(mid)
    row = log(**did)
    if say:
        print(f'  {row["at"]}  "{text[:70]}"  ->  {kind}: {did["did"]}')
        if did.get("answer"):
            print("    " + did["answer"].replace("\n", "\n    "))
    return row


def check(say=True):
    cfg = load(CONFIG, None)
    if not cfg:
        sys.exit(f"Missing {CONFIG}")
    threads = load(THREADS, {}).get("threads", [])
    env = pm.load_env()
    me = env["PROTON_USER"]
    m = pm.connect()
    done = []
    try:
        adopt_tests(m, cfg, threads, me)
        for t, msg, mid in replies(m, cfg, threads, me):
            try:
                done.append(handle(m, cfg, t, msg, mid, me, say))
            except Exception as e:  # noqa: BLE001  one bad reply must not stop the pass; it waits for him
                t["status"] = "needs him"
                t["seen"].append(mid)
                done.append(log(what="reply", thread=t["id"], did=f"failed, left for him: {type(e).__name__}: {str(e)[:200]}"))
                if say:
                    print("  failed, left for him:", type(e).__name__, str(e)[:200])
    finally:
        save_threads(threads)
        try:
            m.logout()
        except Exception:  # noqa: BLE001
            pass
    if say:
        real = "not readable (no PROTON_SDR_USER in .env); test threads only"
        print(f"SDR inbox: {len(done)} new repl{'y' if len(done) == 1 else 'ies'} handled on {len(threads)} thread(s). {cfg['mailbox']}: {real}. Nothing was sent.")
    return done


def status():
    for t in load(THREADS, {}).get("threads", []):
        print(f'{t["status"]:14} drip {t["drip"]:9} {"TEST " if t.get("test") else ""}{t["to"]}  "{t.get("subject", "")}"  offered {t.get("offered") or "-"}')


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "check"
    if cmd == "check":
        check()
    elif cmd == "watch":
        import os
        every = int(argv[2]) if len(argv) > 2 else 120
        state = Path.home() / ".monarc" / "sdr-inbox.json"   # so the watcher can be found and stopped
        state.parent.mkdir(exist_ok=True)
        state.write_text(json.dumps({"pid": os.getpid(), "every": every, "started": datetime.now(HOME).isoformat(timespec="seconds")}), encoding="utf-8")
        log(what="watch started", every=every, pid=os.getpid())
        while True:
            try:
                check(say=False)
            except SystemExit as e:             # Bridge closed or signed out: wait and try again
                log(what="pass failed", why=str(e)[:200])
            except Exception as e:  # noqa: BLE001  a dropped connection must not end the watch
                log(what="pass failed", why=f"{type(e).__name__}: {str(e)[:200]}")
            time.sleep(every)
    elif cmd == "status":
        status()
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
