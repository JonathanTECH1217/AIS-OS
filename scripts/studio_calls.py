"""Calls in a recording, for the Media panel's calls view (2026-10-01, brainstorms/2026-10-01-clip-browser.md).

A recording's clips are its calls, ring to hang-up (B1). Claude lists the calls and the best bits in moments.json
(studio_moments.find); this module adds, on the laptop and for free:

  bounds         where each call plays: from its ring (studio_prep.find_ring) to just after the hang-up. The margins
                 only add time and never cut a call: calls overlap in the 2026-09-28 session (c20 runs into the Caitlin
                 call). Kept in calls.json, never in moments.json, so it can't race short creation or moment edits.
  view           the rows the page shows: calls with their play range, best bits placed by time overlap (Claude's own
                 call field was wrong for 4 of 31), stretches that aren't calls hidden unless they hold a best bit,
                 then shown as "between calls" (B7, B22), and which calls were watched (B19).
  search         a phrase in what was said, or in a call's title or summary (B14).
  words          one stretch's words with their voice keys, for the captions on the player (B17).
  auto_check     whether Claude's pass may run by itself once a recording is prepared (B16); the server does the
                 free token count and the run.
"""
import os
import re
import threading
import time
import traceback

import studio_common as sc

V = 1
PRE_NO_RING = 0.7    # no ring found: play starts 1 s before the first word (a call's start already sits 0.3 s before it)
TAIL = 1.1           # play ends 1.5 s after the last word (a call's end already sits 0.4 s after it)
BETWEEN_LEAD = 2.0   # a between-calls stretch plays from 2 s before its first best bit (they can run 23 minutes)
ORPHAN_PAD = 2.0     # a best bit that no stretch covers gets a between-calls row of its own, padded this much
MAX_WORDS_SPAN = 3 * 3600


def _dir(aid):
    return sc.CACHE / aid


def moments(aid):
    return sc.read_json(_dir(aid) / "moments.json", {}) or {}


def _overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def file_rev(*paths):
    out = []
    for p in paths:
        try:
            out.append(str(int(p.stat().st_mtime * 1000)))
        except OSError:
            out.append("0")
    return "-".join(out)


_DATE_NAME = re.compile(r"(\d{4})-(\d{2})-(\d{2})[ _T](\d{2})[-.:](\d{2})[-.:](\d{2})")


def recorded_at(meta):
    """(when a recording was made, where that came from): local time, ISO. From the date OBS writes into the file
    name ("2026-09-30 10-27-42.mkv"); a name without one falls back to the file's modified time less its length (OBS
    writes to the end). OBS's MKV files carry no date inside. Recordings are titled and ordered by this (2026-10-01)."""
    from datetime import datetime
    m = _DATE_NAME.search(str((meta or {}).get("name") or ""))
    if m:
        try:
            return datetime(*map(int, m.groups())).isoformat(timespec="seconds"), "name"
        except ValueError:
            pass
    t = float((meta or {}).get("mtime") or 0) - float((meta or {}).get("duration") or 0)
    if t > 0:
        return datetime.fromtimestamp(t).isoformat(timespec="seconds"), "file time"
    return None, None


# ------------------------------------------------------------------ bounds

def bounds_for(calls, ring_of, duration=None):
    """{call id: {"ring": seconds or None, "play": [start, end]}}. ring_of(call) gives where its ring starts (or None);
    stretches that aren't calls get no ring. The previous and next call are the ones that don't overlap this one. With
    the recording's duration, no play range runs past the end."""
    cs = sorted(calls, key=lambda c: (c["start"], c["end"]))
    out = {}
    for c in cs:
        others = [o for o in cs if o is not c and _overlap(o["start"], o["end"], c["start"], c["end"]) <= 0]
        prev_end = max([o["end"] for o in others if o["end"] <= c["start"]] or [0.0])
        nxt = min([o["start"] for o in others if o["start"] >= c["end"]] or [float("inf")])
        ring = ring_of(c) if c.get("outcome") != "not_a_call" else None
        if ring is not None and not ring <= c["start"]:
            ring = None
        lead = ring if ring is not None else c["start"] - PRE_NO_RING
        s = min(c["start"], max(lead, prev_end))
        e = max(c["end"], min(c["end"] + TAIL, nxt))
        if duration:
            e = min(e, max(float(duration), c["start"] + 0.1))
        out[c["id"]] = {"ring": ring, "play": [round(max(0.0, s), 3), round(e, 3)]}
    return out


def _duration(aid):
    return (sc.read_json(_dir(aid) / "meta.json", {}) or {}).get("duration")


def bounds_path(aid):
    return _dir(aid) / "calls.json"


def load_bounds(aid, mo=None):
    """The saved bounds when they belong to the current moments.json, else None."""
    mo = moments(aid) if mo is None else mo
    b = sc.read_json(bounds_path(aid))
    if not mo.get("calls") or not b or b.get("v") != V or b.get("for") != mo.get("created"):
        return None
    return b


def stale(aid):
    mo = moments(aid)
    return bool(mo.get("calls")) and load_bounds(aid, mo) is None


def compute_bounds(aid, meta):
    """Find each call's ring and write calls.json. About half a second a call, on the laptop; blocking."""
    import studio_prep as prep
    mo = moments(aid)
    calls = mo.get("calls") or []

    def ring_of(c):
        try:
            return prep.find_ring(aid, meta, c["start"], calls=calls, cur=c)
        except Exception:  # noqa: BLE001  (a call without a ring still plays, from just before its first word)
            traceback.print_exc()
            return None

    t0 = time.time()
    b = {"v": V, "for": mo.get("created"), "t": time.strftime("%Y-%m-%dT%H:%M:%S"),
         "calls": bounds_for(calls, ring_of, (meta or {}).get("duration") or _duration(aid))}
    b["seconds"] = round(time.time() - t0, 1)
    sc.write_json_atomic(bounds_path(aid), b)
    return b


_bounding = set()
_bound_lock = threading.Lock()


def ensure_bounds(aid, meta, done=None, wait=False):
    """Start compute_bounds on a thread (or run it here, wait=True) when calls.json is missing or stale. done() runs
    after (the server bumps its feed so open pages fetch the calls again). Returns True if bounds were (being) found."""
    if not meta or not stale(aid):
        return False
    with _bound_lock:
        if aid in _bounding:
            return True
        _bounding.add(aid)

    def work():
        try:
            compute_bounds(aid, meta)
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        finally:
            with _bound_lock:
                _bounding.discard(aid)
            if done:
                done()

    if wait:
        work()
    else:
        threading.Thread(target=work, daemon=True).start()
    return True


def bounding(aid):
    with _bound_lock:
        return aid in _bounding


# ------------------------------------------------------------------ watched marks (B19)

_marks_lock = threading.Lock()


def marks_path(aid):
    return _dir(aid) / "call-marks.json"


def _same(r, s, e):
    """A saved range is this call when they overlap by at least half of the shorter one, so a mark follows its call if
    Claude lists the calls again (the call ids change, the times barely do)."""
    ov = _overlap(r[0], r[1], s, e)
    return ov > 0 and ov >= 0.5 * min(r[1] - r[0], e - s)


def watched_ranges(aid):
    return (sc.read_json(marks_path(aid), {}) or {}).get("watched", [])


def mark_watched(aid, start, end):
    with _marks_lock:
        data = sc.read_json(marks_path(aid), {}) or {}
        w = data.get("watched", [])
        if not any(_same(r, start, end) for r in w):
            w.append([round(start, 3), round(end, 3), int(time.time())])
        data.update(v=V, watched=w)
        sc.write_json_atomic(marks_path(aid), data)


# ------------------------------------------------------------------ the view

def _row(c, bb):
    return {"id": c["id"], "label": (c.get("label") or "").strip(), "outcome": c.get("outcome") or "other",
            "start": c["start"], "end": c["end"], "ring": bb["ring"], "play": bb["play"],
            "summary": (c.get("summary") or "").strip()}


def view(aid):
    """What the calls view shows. Row ids are moments.json's call ids ("x" + a best bit's id for a bit no stretch
    covers). Bounds come from calls.json, or the no-ring rule while the rings are still being found."""
    mo = moments(aid)
    calls = sorted(mo.get("calls") or [], key=lambda c: (c["start"], c["end"]))
    b = load_bounds(aid, mo)
    dur = _duration(aid)
    plain = bounds_for(calls, lambda c: None, dur)
    bmap = dict(plain, **((b or {}).get("calls") or {}))
    rows = [_row(c, bmap.get(c["id"]) or plain[c["id"]]) for c in calls]
    bits = []
    for m in sorted(mo.get("moments") or [], key=lambda m: m["start"]):
        best, best_ov = None, 0.0
        for r in rows:
            ov = _overlap(m["start"], m["end"], r["play"][0], r["play"][1])
            if ov <= 0:
                continue
            # a tie (overlapping calls) goes to a real call over a stretch that isn't one
            if best is None or ov > best_ov + 1e-6 or (abs(ov - best_ov) <= 1e-6 and best["outcome"] == "not_a_call"
                                                       and r["outcome"] != "not_a_call"):
                best, best_ov = r, ov
        if best is None:
            s, e = max(0.0, m["start"] - ORPHAN_PAD), m["end"] + ORPHAN_PAD
            e = min(e, float(dur)) if dur else e
            best = {"id": "x" + m["id"], "label": "Between calls", "outcome": "not_a_call", "start": s, "end": e,
                    "ring": None, "play": [round(s, 3), round(e, 3)], "summary": ""}
            rows.append(best)
        bits.append({"id": m["id"], "call": best["id"], "start": m["start"], "end": m["end"],
                     "title": (m.get("title") or "").strip(), "strength": m.get("strength") or 0,
                     "type": m.get("type"), "reason": (m.get("reason") or "").strip(), "state": m.get("state", "new")})
    holds = {x["call"] for x in bits}
    w = watched_ranges(aid)
    hidden = 0
    for r in rows:
        r["between"] = r["outcome"] == "not_a_call" and r["id"] in holds
        r["hidden"] = r["outcome"] == "not_a_call" and not r["between"]
        hidden += 1 if r["hidden"] else 0
        first = min([x["start"] for x in bits if x["call"] == r["id"]] or [None]) if r["between"] else None
        r["from"] = round(max(r["play"][0], first - BETWEEN_LEAD), 3) if first is not None else r["play"][0]
        r["watched"] = any(_same(x, r["start"], r["end"]) for x in w)
    rows.sort(key=lambda r: (r["play"][0], r["play"][1]))
    return {"asset": aid, "created": mo.get("created"), "calls": rows, "bits": bits, "hidden": hidden,
            "bounding": bool(calls) and b is None}


def row(aid, cid):
    return next((r for r in view(aid)["calls"] if r["id"] == cid), None)


_counts = {}


def counts(aid):
    """{n: calls that are real calls, booked} for the recording's row, read once per change of moments.json."""
    p = _dir(aid) / "moments.json"
    try:
        mt = p.stat().st_mtime
    except OSError:
        return None
    hit = _counts.get(aid)
    if hit and hit[0] == mt:
        return hit[1]
    cs = (sc.read_json(p, {}) or {}).get("calls") or []
    out = {"n": sum(1 for c in cs if c.get("outcome") != "not_a_call"),
           "booked": sum(1 for c in cs if c.get("outcome") == "booked")}
    _counts[aid] = (mt, out)
    return out


def calls_rev(aid):
    d = _dir(aid)
    return file_rev(d / "moments.json", d / "calls.json")


# ------------------------------------------------------------------ words (B17) and search (B14)

_cache = {}
_cache_lock = threading.Lock()


def _words_and_voices(aid):
    """The transcript's words (spelling fixes applied) and who said each, kept until either changes."""
    import studio_moments as sm
    import studio_speakers as ss
    d = _dir(aid)
    key = (file_rev(d / "transcript.json", d / "transcript-edits.json"), ss.voices_rev(aid))
    with _cache_lock:
        hit = _cache.get(aid)
        if hit and hit[0] == key:
            return hit[1], hit[2]
    tr = sm.load_transcript(aid)
    try:
        vo = ss.resolve(aid, tr["words"])
    except Exception as e:  # noqa: BLE001  (the words must still come, or the captions go empty)
        traceback.print_exc()
        vo = {"state": "error", "error": f"{type(e).__name__}: {e}"[:300], "spk": None, "speakers": []}
    with _cache_lock:
        _cache[aid] = (key, tr["words"], vo)
    return tr["words"], vo


def _first_after(ws, s):
    lo, hi = 0, len(ws)
    while lo < hi:
        mid = (lo + hi) // 2
        if ws[mid][1] <= s:
            lo = mid + 1
        else:
            hi = mid
    return lo


def words(aid, s, e):
    """The words that overlap s..e seconds (absolute times), each word's voice index and the speakers list: enough for
    js/model/captions.js to lay out the captions of one call."""
    s, e = max(0.0, float(s)), float(e)
    if not e > s:
        raise ValueError("The end must come after the start.")
    if e - s > MAX_WORDS_SPAN:
        raise ValueError("Ask for three hours of words at most.")
    ws, vo = _words_and_voices(aid)
    i0 = _first_after(ws, s)
    i1 = i0
    while i1 < len(ws) and ws[i1][0] < e:
        i1 += 1
    spk = vo.get("spk")
    return {"first": i0, "words": ws[i0:i1],
            "voices": {"state": vo.get("state"), "vrev": vo.get("vrev"), "speakers": vo.get("speakers") or [],
                       "spk": spk[i0:i1] if spk else None}}


_TOK = re.compile(r"[a-z0-9]+")


def _norm(text):
    """Lowercase letters and digits only: "Hello," -> "hello", "don't" -> "dont", "C-3" -> "c3"."""
    return "".join(_TOK.findall(str(text).lower().replace("’", "'").replace("'", "")))


def search(aid, q):
    """{row id: {"n": hits, "first": seconds}} for a phrase in what was said (the last word may be half typed), or for
    words in a row's title or summary. Hits count inside each row's play range."""
    toks = [t for t in (_norm(x) for x in str(q).split()) if t]
    if not toks:
        return {}
    v = view(aid)
    rows = v["calls"]
    ws, _ = _words_and_voices(aid)
    norm = [_norm(w[2]) for w in ws]
    hits = []
    k = len(toks)
    for i in range(len(norm) - k + 1):
        if all(norm[i + j] == toks[j] for j in range(k - 1)) and norm[i + k - 1].startswith(toks[-1]):
            hits.append(ws[i][0])
    out = {}
    for r in rows:
        s, e = r["play"]
        ts = [t for t in hits if s <= t < e]
        if ts:
            out[r["id"]] = {"n": len(ts), "first": round(min(ts), 3)}
        else:
            text = _norm(r["label"] + " " + r["summary"])
            if text and all(t in text for t in toks):
                out[r["id"]] = {"n": 1, "first": r["from"]}
    return out


# ------------------------------------------------------------------ Claude's pass by itself (B16)

def auto_path(aid):
    return _dir(aid) / "auto-find.json"


def auto_check(aid, meta, stages, have_key, cap):
    """None when the pass may be estimated now, else why not. Nothing here spends: the token count comes after."""
    if sc._TEST_MEDIA or os.environ.get("STUDIO_NO_CLAUDE"):
        return "tests never spend"
    if not cap or cap <= 0:
        return "no autoFindMax in config.json"
    if not meta or meta.get("kind") != "video" or not str(meta.get("rel") or "").startswith("inbox/"):
        return "not an inbox recording"
    if (_dir(aid) / "moments.json").exists():
        return "it has calls already"
    if auto_path(aid).exists():
        return "decided before"
    if (stages.get("transcript") or {}).get("state") != "done":
        return "the transcript isn't done"
    if (stages.get("speakers") or {}).get("state") != "done":
        return "the voices aren't split"   # without them the estimate leaves out the labels and the run skips them
    if not have_key:
        return "no ANTHROPIC_API_KEY"
    return None


def auto_decide(est, cap):
    """'run' when the top of the estimate is under the cap, else 'wait' (for his click)."""
    return "run" if float(est["high"]) < float(cap) else "wait"


def auto_record(aid, decision, est, cap):
    data = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "decision": decision, "low": est.get("low"),
            "high": est.get("high"), "cap": cap, "input_tokens": est.get("input_tokens")}
    sc.write_json_atomic(auto_path(aid), data)
    return data


def auto_info(aid):
    return sc.read_json(auto_path(aid))
