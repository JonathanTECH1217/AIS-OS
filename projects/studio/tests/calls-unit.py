"""Unit checks for a recording's calls (scripts/studio_calls.py, 2026-10-01): where each call plays, best bits placed
by time, between-calls rows, watched marks, search, the words slice, and when Claude's pass may run by itself.

  python projects/studio/tests/calls-unit.py

Runs in a throwaway media folder (STUDIO_MEDIA), no network. The ring check writes a 30 s WAV with a made-up US
ringback (440 + 480 Hz) and runs the real studio_prep.find_ring on it.
"""
import json
import os
import shutil
import sys
import tempfile
import wave
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="studio-calls-"))
os.environ["STUDIO_MEDIA"] = str(TMP / "media")
os.environ["STUDIO_VOICEPRINT"] = str(TMP / "voiceprint.json")
os.environ["STUDIO_CONFIG"] = str(TMP / "config.json")
os.environ.pop("STUDIO_NO_CLAUDE", None)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import numpy as np  # noqa: E402
import studio_common as sc  # noqa: E402
import studio_calls as calls  # noqa: E402
import studio_prep as prep  # noqa: E402

FAILS, PASSES = [], [0]


def check(name, ok, detail=""):
    if ok:
        PASSES[0] += 1
        print(f"ok   {name}")
    else:
        FAILS.append(name)
        print(f"FAIL {name} {detail}")


def C(i, s, e, o="not_interested", label=None):
    return {"id": i, "start": s, "end": e, "outcome": o, "label": label or i, "summary": ""}


# ---- bounds: the margins add time and never cut a call (the 2026-09-28 session's overlaps)
real = [C("c19", 10800.0, 10900.0), C("c20", 10935.7, 11505.8, "no_answer"), C("c21", 11495.0, 11572.9),
        C("c22", 11574.7, 12222.8, "not_a_call"), C("c23", 12085.2, 12165.3), C("c24", 12300.0, 12340.0)]
asked = []


def ring_of(c):
    asked.append(c["id"])
    return {"c21": 11490.1}.get(c["id"])


b = calls.bounds_for(real, ring_of)
check("the Caitlin call starts at its ring, though c20 runs into it", b["c21"]["play"][0] == 11490.1, str(b["c21"]))
check("no call is cut: every play range holds its call",
      all(b[c["id"]]["play"][0] <= c["start"] and b[c["id"]]["play"][1] >= c["end"] for c in real))
check("no ring: play starts 0.7 s before the call (1 s before the first word)", abs(b["c19"]["play"][0] - 10799.3) < 1e-6)
check("the tail is 1.1 s (1.5 s after the last word)", abs(b["c19"]["play"][1] - 10901.1) < 1e-6)
check("a call inside a not-a-call stretch: margins from the calls around it", b["c23"]["play"] == [12084.5, 12166.4], str(b["c23"]))
check("stretches that aren't calls get no ring search", "c22" not in asked and b["c22"]["ring"] is None, str(asked))
two = [C("a", 0.0, 10.0), C("b", 10.5, 20.0)]
b2 = calls.bounds_for(two, lambda c: 5.0 if c["id"] == "b" else None)
check("a tail stops at the next call", b2["a"]["play"][1] == 10.5, str(b2["a"]))
check("a ring inside the previous call is not reached back to", b2["b"]["play"][0] == 10.0, str(b2["b"]))
b3 = calls.bounds_for([C("a", 30.0, 40.0)], lambda c: 30.5)
check("a 'ring' after the call has started is ignored", b3["a"]["ring"] is None and abs(b3["a"]["play"][0] - 29.3) < 1e-6)
check("play never starts before 0", calls.bounds_for([C("a", 0.2, 5.0)], lambda c: None)["a"]["play"][0] == 0.0)

# ---- the view: best bits by time overlap, between-calls rows, hidden stretches, watched marks
aid = "a_unit"
d = sc.CACHE / aid
d.mkdir(parents=True, exist_ok=True)
mo = {"created": "2026-10-01T10:00:00", "calls": [
    C("c01", 0.0, 20.0, "gatekeeper", "Front desk, Volt Electric"), C("c02", 25.0, 60.0, "booked", "Sean, C3 Electrical"),
    C("c03", 61.0, 120.0, "not_a_call", "Talking to the camera"), C("c04", 121.0, 130.0, "not_a_call", "Between dials")],
    "moments": [
    {"id": "m01", "call": "c02", "type": "objection", "start": 2.0, "end": 8.0, "title": "Wrong call field", "strength": 4},
    {"id": "m02", "call": "c02", "type": "best_line", "start": 70.0, "end": 80.0, "title": "To camera", "strength": 5},
    {"id": "m03", "call": "c01", "type": "best_line", "start": 200.0, "end": 205.0, "title": "Nobody's stretch", "strength": 3}]}
sc.write_json_atomic(d / "moments.json", mo)
v = calls.view(aid)
rows = {r["id"]: r for r in v["calls"]}
bits = {x["id"]: x for x in v["bits"]}
check("a best bit goes to the call it sits in, not Claude's call field", bits["m01"]["call"] == "c01", str(bits["m01"]))
check("a stretch that isn't a call but holds a bit shows as 'between calls'", rows["c03"]["between"] and not rows["c03"]["hidden"])
check("a stretch with no bits stays hidden, and is counted", rows["c04"]["hidden"] and v["hidden"] == 1, str(v["hidden"]))
check("a between-calls row plays from 2 s before its first bit", rows["c03"]["from"] == 68.0, str(rows["c03"]["from"]))
check("a call plays from its own start", rows["c02"]["from"] == rows["c02"]["play"][0])
check("a bit no stretch covers gets a between-calls row of its own", bits["m03"]["call"] == "xm03"
      and rows["xm03"]["between"] and rows["xm03"]["play"] == [198.0, 207.0], str(rows.get("xm03")))
check("rows come in time order", [r["id"] for r in v["calls"]] == ["c01", "c02", "c03", "c04", "xm03"])
check("without calls.json the view says the rings are still being found", v["bounding"] is True)
check("the row counts leave out stretches that aren't calls", calls.counts(aid) == {"n": 2, "booked": 1}, str(calls.counts(aid)))
calls.mark_watched(aid, 25.0, 60.0)
calls.mark_watched(aid, 25.0, 60.0)
check("a watched mark is saved once", len(calls.watched_ranges(aid)) == 1)
check("a watched call shows it; the others don't", calls.row(aid, "c02")["watched"] and not calls.row(aid, "c01")["watched"])
mo2 = json.loads(json.dumps(mo))
mo2["created"] = "2026-10-02T09:00:00"
mo2["calls"][1] = C("c05", 24.6, 60.4, "booked", "Sean, C3 Electrical")       # Claude listed the calls again
sc.write_json_atomic(d / "moments.json", mo2)
check("a watched mark follows its call when Claude lists the calls again", calls.row(aid, "c05")["watched"])

# ---- calls.json: the rings, kept apart from moments.json and redone when moments.json changes
real_find = prep.find_ring
prep.find_ring = lambda a, m, t, window=45.0, calls=None, cur=None: (t - 3.0) if cur and cur["id"] == "c05" else None
try:
    out = calls.compute_bounds(aid, {"kind": "video", "rel": "inbox/x.mkv", "orig": "source"})
finally:
    prep.find_ring = real_find
check("calls.json is written for this moments.json", out["for"] == "2026-10-02T09:00:00" and calls.load_bounds(aid) is not None)
check("the view uses the found ring", calls.row(aid, "c05")["play"][0] == 21.6, str(calls.row(aid, "c05")))
check("moments.json is left as it was", sc.read_json(d / "moments.json") == mo2)
mo2["created"] = "2026-10-03T09:00:00"
sc.write_json_atomic(d / "moments.json", mo2)
check("a new moments.json makes calls.json stale", calls.stale(aid) and calls.load_bounds(aid) is None)

# ---- words and search (spelling fixes included); no voice split here, so the words come without voices
texts = ["hi", "this", "is", "jonathan", "with", "monarc", "build"] * 20
ws = [[round(i * 0.5, 2), round(i * 0.5 + 0.4, 2), w] for i, w in enumerate(texts)]
ws[60][2], ws[61][2] = "C3", "Electrical."          # 30.0 s and 30.5 s: inside Sean's call
sc.write_json_atomic(d / "transcript.json", {"words": ws, "segments": [[0, 70, 0, len(ws) - 1]], "duration": 70})
sc.write_json_atomic(d / "transcript-edits.json", {"4": "Control4"})      # 2.0 s: the front desk call
w = calls.words(aid, 25.0, 30.0)
check("words: the ones overlapping the stretch, with absolute times (24.5-24.9 s ends before it)",
      w["first"] == 50 and w["words"][0][0] == 25.0 and w["words"][-1][0] == 29.5,
      str((w["first"], w["words"][:1], w["words"][-1:])))
check("words: no voice split, so no voices yet", w["voices"]["state"] == "none" and w["voices"]["spk"] is None, str(w["voices"]))
for bad in ((30, 30), (0, 4 * 3600)):
    try:
        calls.words(aid, *bad)
        check(f"words refuses {bad}", False)
    except ValueError:
        check(f"words refuses {bad}", True)
hits = calls.search(aid, "c3 elec")
check("search: a phrase, the last word half typed", list(hits) == ["c05"] and hits["c05"] == {"n": 1, "first": 30.0}, str(hits))
check("search: spelling fixes count", list(calls.search(aid, "control4")) == ["c01"], str(calls.search(aid, "control4")))
check("search: a call's title", "c01" in calls.search(aid, "volt"), str(calls.search(aid, "volt")))
check("search: nothing for nothing", calls.search(aid, "  ") == {})

# ---- when a recording was made: its title and its place in the Recordings list (2026-10-01)
import datetime as _dt  # noqa: E402
check("the date OBS writes into the name", calls.recorded_at({"name": "2026-09-30 10-27-42.mkv", "mtime": 1, "duration": 9})
      == ("2026-09-30T10:27:42", "name"))
check("a date anywhere in the name", calls.recorded_at({"name": "Calls 2026-09-28_10.38.17.mp4"}) == ("2026-09-28T10:38:17", "name"))
t_end = _dt.datetime(2026, 10, 1, 13, 0, 0).timestamp()
check("no date in the name: when the file was last written, less its length",
      calls.recorded_at({"name": "calls.mp4", "mtime": t_end, "duration": 3600}) == ("2026-10-01T12:00:00", "file time"),
      str(calls.recorded_at({"name": "calls.mp4", "mtime": t_end, "duration": 3600})))
check("a name with an impossible date falls back too", calls.recorded_at({"name": "2026-13-40 99-99-99.mkv", "mtime": t_end})[1] == "file time")
check("nothing to go on: no date", calls.recorded_at({"name": "x.mkv"}) == (None, None))

# ---- Claude's pass by itself (B16): nothing spends in tests, and only when it's due
meta = {"kind": "video", "rel": "inbox/new.mkv"}
done = {"transcript": {"state": "done"}, "speakers": {"state": "done"}}
check("test media never spends", calls.auto_check("a_new", meta, done, True, 3.0) == "tests never spend")
sc._TEST_MEDIA = False
try:
    check("due: a new inbox recording, prepared, voices split, a key and a cap",
          calls.auto_check("a_new", meta, done, True, 3.0) is None, str(calls.auto_check("a_new", meta, done, True, 3.0)))
    check("off without autoFindMax", calls.auto_check("a_new", meta, done, True, None) is not None)
    check("not for sounds or assets", calls.auto_check("a_new", {"kind": "video", "rel": "assets/b.mp4"}, done, True, 3.0) is not None)
    check("not before the voices are split",
          calls.auto_check("a_new", meta, {"transcript": {"state": "done"}, "speakers": {"state": "error"}}, True, 3.0) is not None)
    check("not without a key", calls.auto_check("a_new", meta, done, False, 3.0) == "no ANTHROPIC_API_KEY")
    check("not when it has calls already", calls.auto_check(aid, meta, done, True, 3.0) == "it has calls already")
    calls.auto_record("a_new", "wait", {"low": 1.7, "high": 3.05, "input_tokens": 59000}, 3.0)
    check("decided once", calls.auto_check("a_new", meta, done, True, 3.0) == "decided before")
    os.environ["STUDIO_NO_CLAUDE"] = "1"
    check("STUDIO_NO_CLAUDE never spends", calls.auto_check("a_other", meta, done, True, 3.0) == "tests never spend")
    os.environ.pop("STUDIO_NO_CLAUDE")
finally:
    sc._TEST_MEDIA = True
check("the top of the estimate decides", calls.auto_decide({"high": 2.95}, 3.0) == "run"
      and calls.auto_decide({"high": 3.05}, 3.0) == "wait" and calls.auto_decide({"high": 3.0}, 3.0) == "wait")
check("a waiting recording says why", (calls.auto_info("a_new") or {}).get("high") == 3.05)

# ---- the real find_ring on a made-up ringback: 2 s of 440 + 480 Hz at 12 s, the person answers at 16 s
sr = 16000
t = np.arange(sr * 30) / sr
x = np.zeros_like(t)
ring = (t >= 12.0) & (t < 14.0)
x[ring] = 0.2 * (np.sin(2 * np.pi * 440 * t[ring]) + np.sin(2 * np.pi * 480 * t[ring]))
talk = t >= 16.0
x[talk] = 0.3 * np.sin(2 * np.pi * 180 * t[talk]) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t[talk]))
(sc.MEDIA / "inbox").mkdir(parents=True, exist_ok=True)
with wave.open(str(sc.MEDIA / "inbox" / "ring.wav"), "wb") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(sr)
    f.writeframes((x * 32767).astype("<i2").tobytes())
rmeta = {"kind": "video", "rel": "inbox/ring.wav", "orig": "source"}
rcall = C("c01", 16.0, 25.0, "booked")
r = prep.find_ring("a_ring", rmeta, 16.0, calls=[rcall], cur=rcall)
check("find_ring finds the ringback before the pickup", r is not None and abs(r - 12.0) < 0.15, str(r))
(sc.CACHE / "a_ring").mkdir(parents=True, exist_ok=True)
sc.write_json_atomic(sc.CACHE / "a_ring" / "moments.json", {"created": "x", "calls": [rcall], "moments": []})
rb = calls.compute_bounds("a_ring", rmeta)
check("so the call plays from the ring", abs(rb["calls"]["c01"]["play"][0] - 12.0) < 0.15, str(rb["calls"]["c01"]))

shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{PASSES[0]} passed, {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
