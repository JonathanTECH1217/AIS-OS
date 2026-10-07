"""Unit checks for Monarc Calls (reworked 2026-10-03, Q32-Q45): the key-note rules, the Prospects reads and writes,
the Status cut, cards and docs, a whole session against the stand-ins (the test microphone, the stand-in base), and
what comes back after a restart.

  python projects/studio/tests/session-unit.py

Runs in a throwaway media folder (STUDIO_MEDIA) with the stand-ins and the test phrase file; no network, no mic, no
model, nothing spent; F9 is never registered.
"""
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="studio-calls-"))
HERE = Path(__file__).resolve().parent
os.environ.update(STUDIO_MEDIA=str(TMP / "media"), STUDIO_VOICEPRINT=str(TMP / "voiceprint.json"),
                  STUDIO_CONFIG=str(TMP / "config.json"), STUDIO_NO_CLAUDE="1", STUDIO_FAKE_MIC="1",
                  STUDIO_FAKE_AIRTABLE=str(TMP / "prospects.json"), STUDIO_PHRASES=str(HERE / "fixtures" / "call-note-phrases.md"),
                  STUDIO_POLL_SECONDS="0.3", STUDIO_SETTLE_SECONDS="0.2")
shutil.copy(HERE / "fixtures" / "prospects.json", TMP / "prospects.json")
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import calls_notes as cn  # noqa: E402
import studio_common as sc  # noqa: E402
import studio_prospects as sp  # noqa: E402
import studio_session as ss  # noqa: E402

sc.ensure_dirs()
FAILS, PASSES = [], [0]


def check(name, ok, detail=""):
    if ok:
        PASSES[0] += 1
        print(f"ok   {name}")
    else:
        FAILS.append(name)
        print(f"FAIL {name} {detail}")


def until(fn, timeout=10.0, step=0.05):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = fn()
        if v:
            return v
        time.sleep(step)
    return None


def seg(text, t=1000.0):
    ws = [[t + i * 0.4, t + i * 0.4 + 0.3, w] for i, w in enumerate(text.split())]
    return {"start": t, "end": ws[-1][1] if ws else t, "words": ws}


PH = cn.load_phrases()


def notes(*texts, **kw):
    return cn.extract([seg(x, 1000.0 + i * 30) for i, x in enumerate(texts)], PH, **kw)


def kinds(ns):
    return [(n["kind"], n.get("value") or n["text"]) for n in ns]


# ---------------------------------------------------------------- the rules
n = notes("Yeah, we're pretty booked up at this point.")
check("constraint: the phrase, matched and marked", kinds(n) == [("constraint", "Yeah, we're pretty booked up at this point.")]
      and n[0]["text"][n[0]["match"][0]:n[0]["match"][1]] == "booked up", str(n))
check("objection", kinds(notes("We're handling it ourselves.")) == [("objection", "We're handling it ourselves.")])
check("offering: a phrase alone", [k for k, _ in kinds(notes("We do mostly residential."))] == ["offering"])
check("a service word counts only with we / our", [k for k, _ in kinds(notes("Our crew does a lot of Control4."))] == ["offering"]
      and notes("Control4 is big around here.") == [])
check("his pitch is ignored (you guys, landing page)", notes("You guys don't have landing pages for generators.") == []
      and notes("I noticed the landing page is booked up.") == [])
check("* stands for one word", kinds(notes("We're short on techs right now."))[0][0] == "constraint")
check("one sentence can be two kinds", [k for k, _ in kinds(notes("We're booked up and we're all set."))] == ["constraint", "objection"])

e = notes("Sure, it's mike at acme a v dot com.", website="https://www.acmeav.com/")
check("email spoken: the address put together", [(x["kind"], x.get("value"), x.get("flag")) for x in e] == [("email", "mike@acmeav.com", None)], str(e))
e = notes("Sure, it's mike at acme a v dot com.", website="otherco.com")
check("email whose domain isn't the site's: flagged", e and e[0].get("flag") == "their site is otherco.com", str(e))
check("email written", kinds(notes("Send it to Dana@BrioHome.com please."))[0] == ("email", "dana@briohome.com"))
check("a free-mail address asks for a spelling check", notes("four at gmail.com")[0].get("flag") == "check the spelling")
o = notes("Office at all dash pro.", website="allproelectrical.com")
check("an address too mangled to build still shows, flagged with the site", o and o[0]["kind"] == "email" and not o[0].get("value")
      and "allproelectrical.com" in o[0]["flag"], str(o))
p = notes("My cell is five one two, five five five, zero one three four.")
check("phone spoken", kinds(p) == [("phone", "(512) 555-0134")], str(p))
p = notes("Main line is (303) 555-0199.", phone="303.555.0199")
check("phone written; the row's own number flagged", p and p[0]["value"] == "(303) 555-0199" and p[0]["flag"] == "same as the row's number", str(p))
check("short number runs aren't phones", notes("We're three to four months behind.") == [] or all(x["kind"] != "phone" for x in notes("We're three to four months behind.")))
check("name: this is ...", kinds(notes("Hey, this is Sean with C3 Electrical."))[0] == ("name", "Sean"))
check("name: never Jonathan", notes("Hey, this is Jonathan.") == [])
check("name: what was your name", ("name", "Stacy") in kinds(notes("What was your name? Stacy? Stacy.")))
check("name: spelled out", ("name", "Cody") in kinds(notes("How do you spell that? C O D Y?")))
check("name: never one on the Not names list", notes("Hey Patrick, look at this.") == [])
m = notes("It would just be fifteen minutes of your time tomorrow. at2 p.m. What do you say?",
          "Any time after five. I'll be available.", "I'll send you over a meeting link. For tomorrow at five.")
check("meeting: the last time said yes to", ("meeting", "Tomorrow 5:00") in kinds(m), str(kinds(m)))
m = notes("Fifteen minutes tomorrow around four?", "Sounds good.", "Should I just call back when I remember?")
check("meeting: not when it ends in a call back", all(x["kind"] != "meeting" for x in m), str(kinds(m)))
check("meeting: not without a yes", all(x["kind"] != "meeting" for x in notes("Could we meet Tuesday at 2?")))
d = notes("It's mike at acme a v dot com.", "Yep, mike at acme a v dot com.")
check("the same address twice is one note", sum(1 for x in d if x["kind"] == "email") == 1)
check("notes come in the window's order", [x["kind"] for x in notes("Hey, this is Sean.", "We're all set.", "We're booked up.")]
      == ["constraint", "objection", "name"])
check("as_text: the doc's and the log's lines", cn.as_text([{"kind": "email", "text": "mike@acmeav.com"},
                                                            {"kind": "constraint", "text": "booked up"}])
      == "Email: mike@acmeav.com\nConstraint: booked up")
real = cn.load_phrases(HERE.parents[2] / "references" / "call-note-phrases.md")
check("the real phrase file loads, every section filled", all(real[k] for k in ("offering", "services", "constraint", "objection", "ignore")))

# ---------------------------------------------------------------- the Prospects base
fake = sp.Fake(TMP / "prospects.json")
s = sp.Schema(fake.meta())
check("columns: Status changed is required", s.name("changed") == "Status changed")
broken = json.loads(json.dumps(fake.meta()))
broken["tables"][0]["fields"] = [x for x in broken["tables"][0]["fields"] if x["name"] != "Status changed"]
try:
    sp.Schema(broken)
    check("a missing Status changed column stops Start, named", False)
except sp.SchemaError as e:
    check("a missing Status changed column stops Start, named", '"Status changed"' in str(e), str(e))
check("the poll formula", sp.Live.changes_formula(s, "2026-10-03T14:05:06.000Z") ==
      'IS_AFTER({Status changed}, DATETIME_PARSE("2026-10-03T14:05:06.000Z"))')
check("times both ways", sp.iso(1759500306.25) == "2025-10-03T14:05:06.250Z" and abs(sp.epoch("2025-10-03T14:05:06.250Z") - 1759500306.25) < 1e-3,
      sp.iso(1759500306.25))
p = sp.Prospects(sp.Fake(TMP / "prospects.json"))
p.open(add_key=True)
check("the Outreach Log gets its Call key column", "key" in p.schema.log and p.schema.log_id("transcript"))
t0 = time.time()
p.be.fake_status("recFox00000006", "No answer.", t0 + 1)
rows = p.changes(t0)
check("the poll sees a Status typed after since", [r["id"] for r in rows] == ["recFox00000006"] and rows[0]["status"] == "No answer.")
check("and not one at or before since", p.changes(t0 + 1) == [])

shutil.copy(HERE / "fixtures" / "prospects.json", TMP / "w.json")
wp = sp.Prospects(sp.Fake(TMP / "w.json"))
res = []
wr = sp.Writer(wp, lambda op, state, info: res.append((op["w"], state, info)))
wr.BACKOFF = (0.3, 0.3)
wr.add({"w": "n1", "kind": "log_note", "key": "s #1", "text": "Constraint: booked up"})
wr.add({"w": "l1", "kind": "log", "rec": "recBrio0000002", "mb": "MB-03502", "day": "2026-10-03", "key": "s #1"})
wr.add({"w": "o1", "kind": "set", "rec": "recBrio0000002", "role": "owner", "value": "Someone Else"})
wr.add({"w": "e1", "kind": "set", "rec": "recDelta000004", "role": "email", "value": "x@delta.com"})
wp.open(add_key=True)
until(lambda: len(res) >= 5, 8)
data = json.loads((TMP / "w.json").read_text(encoding="utf-8"))
brio = [r["fields"] for r in data["log"]["records"] if r["fields"].get("Company ID") == "MB-03502"]
check("the log row: touchpoint counted on, Call key set", brio[-1].get("Touchpoint #") == "2" and brio[-1].get("Call key") == "s #1"
      and brio[-1].get("Channel") == "Cold Call" and brio[-1].get("Company") == ["recBrio0000002"], str(brio))
check("a log note waits for its row, then fills Transcript", brio[-1].get("Transcript") == "Constraint: booked up"
      and [w for w, st_, _ in res if st_ == "ok"].index("n1") > [w for w, st_, _ in res if st_ == "ok"].index("l1"), str(res))
check("an Owner already on the row is kept", ("o1", "kept", {"kept": "Dana Brio (owner)"}) in res)
check("a dropped network: retried, then written", any(r[0] == "e1" and r[1] == "fail" for r in res)
      and {r["id"]: r["fields"] for r in data["contacts"]["records"]}["recDelta000004"].get("Email") == "x@delta.com")
check("Status is never written", all("Status (typed)" not in r["fields"] or r["id"] == "recCalled00007" for r in data["contacts"]["records"]))

# ---------------------------------------------------------------- a whole session
class Feed:
    def __init__(self):
        self.rev = 1

    def bump(self, throttle=0.0):
        self.rev += 1


ctl = ss.Controller(8799, Feed())
chk = ctl.check()
check("the start panel's checks", chk["mic"]["ok"] and chk["phrases"]["ok"] and chk["airtable"]["ok"], str(chk))
code, v = ctl.post("start", {"cid": "c0"})
check("Start: listening, the test mic ready", code == 200 and v["active"] and v["listening"], str(v)[:300])
until(lambda: ctl.st["mic"] and ctl.st["mic"].get("device"))
check("the mic says which device", ctl.st["mic"]["device"] == "Test microphone")
check("Studio holds off preparing files while listening", not ctl.idle.is_set())


def say(text):
    k = len(ctl.st["segs"])
    ctl._mic_send("say " + text)
    return until(lambda: len(ctl.st["segs"]) > k, 5)


say("Hey, this is Mike with Acme.")
say("We do mostly residential, but we're short on techs.")
say("Sure, it's mike at acme a v dot com.")
live = ctl.view()["live"]["notes"]
check("live notes while they talk", {"offering", "constraint", "email", "name"} <= {x["kind"] for x in live}, str(kinds(live)))
time.sleep(0.05)
ctl.p.be.fake_status("recAcme0000001", "Callback.")
card = until(lambda: ctl.view()["cards"], 5)
check("typing Status makes a card for that row", card and card[0]["rec"] == "recAcme0000001" and card[0]["mb"] == "MB-03501"
      and {"offering", "constraint", "email", "name"} <= {x["kind"] for x in card[0]["notes"]}, str(card)[:400])
check("the card's email is checked against the row's website", next(x for x in card[0]["notes"] if x["kind"] == "email").get("flag") is None)
check("and the live notes start over", ctl.view()["live"]["notes"] == [])
until(lambda: any(w.get("kind") == "log" and w["state"] == "ok" for w in ctl.st["writes"].values()), 5)
data = ctl.p.be.dump()
logs = [r["fields"] for r in data["log"]["records"] if r["fields"].get("Channel") == "Cold Call"]
check("the dial's Outreach Log row", len(logs) == 1 and logs[0]["Company ID"] == "MB-03501" and logs[0]["Call key"] == f"{ctl.st['id']} #1", str(logs))

ctl.p.be.fake_status("recAcme0000001", "Callback thursday.")
until(lambda: ctl.view()["cards"][0]["status"] == "Callback thursday.", 3)
check("a fix to the same row: no new cut, the card shows the new words", len(ctl.st["cuts"]) == 1
      and ctl.view()["cards"][0]["status"] == "Callback thursday.")

say("Do you want to make more money?")
ctl.p.be.fake_status("recBrio0000002", "Wrong vertical.")
time.sleep(1.0)
check("a skip word makes no cut and no log row", len(ctl.st["cuts"]) == 1
      and sum(1 for w in ctl.st["writes"].values() if w.get("kind") == "log") == 1)
say("Hello? Sorry, wrong number.")
ctl.p.be.fake_status("recCrest000003", "No answer.")
until(lambda: ctl.st["filed"].get(2), 5)
f2 = ctl.st["filed"].get(2)
check("a call with no key notes files its words at once, no card", f2 and f2["how"] == "words" and len(ctl.view()["cards"]) == 1, str(f2))
txt = next(iter(sorted((sc.PROSPECTS / "MB-03503 Crest Smart Homes").glob("*.md"))), None)
check("its doc: the company folder, the words heard (both lines since the last cut)", txt and "wrong number" in txt.read_text(encoding="utf-8")
      and "Do you want to make more money" in txt.read_text(encoding="utf-8") and "(none)" in txt.read_text(encoding="utf-8"))
ctl.p.be.fake_status("recDelta000004", "No answer.")
until(lambda: len(ctl.st["cuts"]) == 3, 5)
check("a call with no speech files nothing, but gets its log row", 3 not in ctl.st["filed"]
      and until(lambda: sum(1 for w in ctl.st["writes"].values() if w.get("kind") == "log") == 3, 3))

code, _ = ctl.post("pause", {"cid": "p1"})
check("Pause stops listening; Studio may prepare files again", code == 200 and not ctl.st["listening"] and ctl.idle.is_set())
k = len(ctl.st["segs"])
ctl._mic_send("say this should not be heard")
time.sleep(0.6)
check("nothing is kept while paused", len(ctl.st["segs"]) == k)
ctl.post("toggle", {"cid": "p2"})
check("F9 (toggle) resumes", ctl.st["listening"])

c1 = ctl.view()["cards"][0]
edited = [{"kind": "constraint", "text": "Short on techs."}, {"kind": "email", "text": "Mike@AcmeAV.com"},
          {"kind": "name", "text": "Mike"}, {"kind": "offering", "text": "Mostly residential, some commercial."}]
code, v = ctl.post("push", {"cid": "u1", "sid": c1["sid"], "n": c1["n"], "notes": edited})
check("Push files the card", code == 200 and v["cards"] == [] and ctl.st["cards"][1]["state"] == "pushed", str(v.get("errors")))
doc1 = sorted((sc.PROSPECTS / "MB-03501 Acme Audio Video").glob("*.md"))
body = doc1[0].read_text(encoding="utf-8") if doc1 else ""
check("the doc: record id, his edited notes, then the words", "recAcme0000001" in body and "- Constraint: Short on techs." in body
      and "- Email: Mike@AcmeAV.com" in body and "## Words heard" in body and "mike at acme a v dot com" in body, body[:400])
until(lambda: ctl.writer.pending() == 0, 6)
data = ctl.p.be.dump()
acme = next(r["fields"] for r in data["contacts"]["records"] if r["id"] == "recAcme0000001")
check("Push fills the blank Email and Owner", acme.get("Email") == "mike@acmeav.com" and acme.get("Owner") == "Mike", str(acme))
log1 = next(r["fields"] for r in data["log"]["records"] if r["fields"].get("Call key") == f"{ctl.st['id']} #1")
check("and the log row's Transcript", log1.get("Transcript", "").startswith("Constraint: Short on techs."), str(log1))
code, v = ctl.post("push", {"cid": "u2", "sid": c1["sid"], "n": c1["n"], "notes": edited})
check("a card can't be filed twice", code == 409)
code, v = ctl.post("push", {"cid": "u1", "sid": c1["sid"], "n": c1["n"], "notes": edited})
check("a click sent twice counts once", code == 200)

say("We're all set, thanks.")
ctl.p.be.fake_status("recEcho0000005", "No.")
until(lambda: ctl.view()["cards"], 5)
c5 = ctl.view()["cards"][0]
code, _ = ctl.post("discard", {"cid": "d1", "sid": c5["sid"], "n": c5["n"]})
check("Discard drops a card, files nothing", code == 200 and ctl.view()["cards"] == []
      and not (sc.PROSPECTS / "MB-03505 Echo Systems").exists())

say("We're booked up for months.")
ctl.p.be.fake_status("recHalo0000009", "Callback.")
until(lambda: ctl.view()["cards"], 5)
code, v = ctl.post("stop", {"cid": "s1"})
check("Stop ends the session; the open card stays to file", code == 200 and not v["active"] and len(v["cards"]) == 1
      and ctl.mic is None and ctl.idle.is_set(), str(v.get("cards")))
check("the doc's folder name drops what Windows refuses", ss.safe_name('MB-1 A/B: "C"?') == "MB-1 AB C")

ctl2 = ss.Controller(8799, Feed())
old = sc.SESSIONS / "2026-09-01 10-00-00.jsonl"
with open(old, "w", encoding="utf-8") as fh:
    for ln in [{"k": "start", "id": "2026-09-01 10-00-00", "t": time.time() - 3 * 86400},
               {"k": "write", "w": "o1", "kind": "set", "rec": "recFox00000006", "role": "email", "value": "a@b.com", "t": time.time() - 2 * 86400},
               {"k": "stop", "t": time.time() - 2 * 86400}]:
        fh.write(json.dumps(ln) + "\n")
ctl2.recover()
check("after a restart: the open card is back under To file", [c["rec"] for c in ctl2.view()["cards"]] == ["recHalo0000009"])
check("a write older than a day is marked stuck, not sent", ss.fold(ss.read_lines(old))["writes"]["o1"]["state"] == "stuck")
c9 = ctl2.view()["cards"][0]
code, _ = ctl2.post("push", {"cid": "u9", "sid": c9["sid"], "n": c9["n"], "notes": [{"kind": "constraint", "text": "Booked up for months."}]})
check("and it can still be pushed", code == 200 and ctl2.view()["cards"] == [] and sorted((sc.PROSPECTS / "MB-03509 Halo AV").glob("*.md")))

shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{PASSES[0]} passed, {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
