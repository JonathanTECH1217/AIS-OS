"""Generate captions (Monarc Studio, 2026-10-02; Jonathan's grill G1-G7 in brainstorms/2026-10-02-captions-after-trim.md).

A new short has no captions while Jonathan trims it. When he presses Generate captions:
  1. studio_listen.py listens again to just the kept parts (whole sentences, no voice detector), in a child process.
  2. The two listens are lined up word by word (difflib on letters and digits only). Where they agree, the second
     listen's words go in (its punctuation came from whole sentences).
  3. Where they differ, Claude reads the short's own words and picks the reading that makes sense, A or B, never its
     own words (claude-opus-5, effort low, about 1 to 2 cents). Without Claude (no key, no network, tests) the second
     listen wins, since it was right most of the time on call c23. A word Jonathan fixed by hand always stays.
  4. Each word keeps a way to its voice: the first-transcript word it overlaps most (its voice follows every fix) and
     the voice split's group at its time (for words only the second listen heard).

The words are saved in the short (captions.gen[asset]) in the recording's seconds, so later cuts and moves keep them
right (G3); the page does that, this module never writes a short.
"""
import difflib
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_common as sc  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent
PAD_LISTEN = 2.0     # extra audio heard either side of a kept part, so the edge sentences are whole
PAD_KEEP = 1.0       # the words reach this far past a kept part, so a small trim outward later stays captioned
JOIN = 4.0           # kept parts closer than this are heard as one stretch
MAX_SECONDS = 1800   # the most a short can ask to have heard (a 30-minute short is a mistake, not a short)
LISTEN_ONE = threading.Semaphore(1)   # one second listen at a time: each loads the speech model (about 1 GB)

SYSTEM = """You help caption Jonathan Beach's short vertical videos of his cold calls. He runs Monarc Build, a marketing
agency for home integrators and electricians; the other side is a business owner, a gatekeeper, a voicemail or a phone menu.

The short's speech was transcribed twice. Listen A heard short pieces cut by a voice detector, so it drops quiet words and
loses the sentence around them. Listen B heard whole sentences, so it is usually right, above all when it has words A
missed, but it can mishear names, numbers and short words too. Where the two differ the text shows
[n| A: "..." | B: "..."]; an empty side means that listen heard nothing there.

For every numbered place, pick the reading that makes sense in the conversation around it: what a person on this call
would really say there. Answer with "A" or "B" for each number. Never write words of your own."""

SCHEMA = {"type": "object", "properties": {"picks": {"type": "array", "items": {
    "type": "object", "properties": {"n": {"type": "integer"}, "pick": {"type": "string", "enum": ["A", "B"]}},
    "required": ["n", "pick"], "additionalProperties": False}}}, "required": ["picks"], "additionalProperties": False}


def norm(text):
    return re.sub(r"[^0-9a-z]+", "", str(text).lower())


def plan_ranges(kept, duration=None):
    """The kept parts of the recording (source seconds) as (heard, captioned): merged, then padded."""
    dur = float(duration) if duration else float("inf")
    rs = sorted([max(0.0, float(s)), min(dur, float(e))] for s, e in kept if float(e) > float(s))
    merged = []
    for s, e in rs:
        if e <= s:
            continue
        if merged and s - merged[-1][1] < JOIN:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    heard = [[round(max(0.0, s - PAD_LISTEN), 3), round(min(dur, e + PAD_LISTEN), 3)] for s, e in merged]
    keep = [[round(max(0.0, s - PAD_KEEP), 3), round(min(dur, e + PAD_KEEP), 3)] for s, e in merged]
    return heard, keep


def inside(w, ranges):
    m = (w[0] + w[1]) / 2
    return any(s <= m < e for s, e in ranges)


def split_numbers(words):
    """A first transcript made before 2026-10-02 has "get15" where the transcriber now writes "get 15"
    (studio_transcribe.number_starts_word): split the same way, the time shared out by letters, so the two listens
    line up there. Both halves keep the word's id."""
    import studio_transcribe as st
    out = []
    for w in words:
        m = re.match(r"^([A-Za-z]+)(\d.*)$", str(w[2]))
        if m and st.number_starts_word(m.group(1), m.group(2)):
            cut = round(w[0] + (w[1] - w[0]) * len(m.group(1)) / len(w[2]), 3)
            out.append([w[0], cut, m.group(1)] + list(w[3:]))
            out.append([cut, w[1], m.group(2)] + list(w[3:]))
        else:
            out.append(list(w))
    return out


def diff(A, B):
    return difflib.SequenceMatcher(a=[norm(w[2]) for w in A], b=[norm(w[2]) for w in B], autojunk=False).get_opcodes()


def spans(A, B, edited):
    """The places the two listens differ: [{n, op, a0, a1, b0, b1, pinned}]. A is [[s, e, text, id]], B [[s, e, text]].
    pinned: a word Jonathan fixed by hand is in it, so his reading stays and Claude isn't asked."""
    out = []
    for op, a0, a1, b0, b1 in diff(A, B):
        if op == "equal":
            continue
        out.append({"n": len(out) + 1, "op": op, "a0": a0, "a1": a1, "b0": b0, "b1": b1,
                    "pinned": any(A[i][3] in edited for i in range(a0, a1))})
    return out


def apply(A, B, edited, sp, picks):
    """The generated words [[s, e, text, a_id or None]]: B where the listens agree (a word he fixed keeps his
    spelling), and at each difference the reading picked; B when nobody picked."""
    out, k = [], 0
    for op, a0, a1, b0, b1 in diff(A, B):
        if op == "equal":
            for i, j in zip(range(a0, a1), range(b0, b1)):
                out.append(list(A[i][:4]) if A[i][3] in edited else [B[j][0], B[j][1], B[j][2], None])
            continue
        s = sp[k]
        k += 1
        if s["pinned"] or picks.get(s["n"]) == "A":
            out += [list(w[:4]) for w in A[a0:a1]]
        else:
            out += [[w[0], w[1], w[2], None] for w in B[b0:b1]]
    out.sort(key=lambda w: w[0])
    for i in range(len(out) - 1):          # the two listens' neighbours can overlap by a few ms
        if out[i][1] > out[i + 1][0]:
            out[i][1] = round(max(out[i][0] + 0.04, out[i + 1][0]), 3)
    return out


def donors(words, A):
    """For each word, the first-transcript word it overlaps most (its voice follows every fix made there), or None."""
    out = []
    for w in words:
        if w[3] is not None:
            out.append(w[3])
            continue
        best, bo = None, 0.0
        for a in A:
            if a[0] >= w[1]:
                break
            o = min(a[1], w[1]) - max(a[0], w[0])
            if o > bo:
                best, bo = a[3], o
        out.append(best)
    return out


def side_of(runs, t):
    for a, b, side in runs or []:
        if a <= t < b:
            return side
    return None


def prompt(A, B, sp, runs):
    """The short's words in order with each askable difference marked, a new line where the speaker side changes."""
    pieces, k = [], 0          # (time, text), in the order the words are said
    for op, a0, a1, b0, b1 in diff(A, B):
        if op == "equal":
            pieces += [(B[j][0], B[j][2]) for j in range(b0, b1)]
            continue
        s = sp[k]
        k += 1
        ta = " ".join(w[2] for w in A[a0:a1])
        tb = " ".join(w[2] for w in B[b0:b1])
        t = A[a0][0] if a1 > a0 else B[b0][0]
        pieces.append((t, ta if s["pinned"] else f'[{s["n"]}| A: "{ta}" | B: "{tb}"]'))
    lines, cur = [], None
    for t, text in pieces:
        side = side_of(runs, t) or cur
        if side != cur or not lines:
            lines.append(("Jonathan: " if side == "me" else "Other side: " if side == "them" else "") + text)
            cur = side
        else:
            lines[-1] += " " + text
    return "\n".join(lines)


def ask_claude(aid, A, B, sp, runs):
    """{n: "A" | "B"} for the askable places, the cost in dollars, the model, the usage."""
    import studio_moments as sm
    body = prompt(A, B, sp, runs)
    req = dict(model=sm.MODEL, max_tokens=8000, system=SYSTEM, messages=[{"role": "user", "content": body}])
    data, msg, cost, secs = sm._call(sm._client(), req, SCHEMA, lambda s: None, effort="low")
    asked = {s["n"] for s in sp if not s["pinned"]}
    picks = {int(p["n"]): p["pick"] for p in data.get("picks", []) if int(p.get("n", -1)) in asked}
    return picks, cost, msg.model, {"input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens}, secs


def second_listen(aid, heard, on_status):
    """Run studio_listen.py over the stretches; returns its result dict."""
    out = sc.CACHE / aid / f"listen-{int(time.time() * 1000)}.json"
    args = [sc.python_exe(), "-u", str(SCRIPTS / "studio_listen.py"), aid,
            "--ranges", ",".join(f"{s}:{e}" for s, e in heard), "--out", str(out)]
    if not LISTEN_ONE.acquire(blocking=False):
        on_status("Waiting for another short's captions", 0)
        LISTEN_ONE.acquire()
    try:
        on_status("Listening again", 0)
        proc = sc.popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        err = []
        threading.Thread(target=lambda: [err.append(x.decode("utf-8", "replace")) for x in proc.stderr], daemon=True).start()
        for raw in proc.stdout:
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            if msg.get("total"):
                on_status("Listening again", min(1.0, msg["pos"] / msg["total"]))
        proc.wait()
        sc.untrack(proc)
        if proc.returncode != 0 or not out.exists():
            raise RuntimeError("the second listen failed: " + ("".join(err)[-600:].strip() or f"exit {proc.returncode}"))
        return sc.read_json(out)
    finally:
        LISTEN_ONE.release()
        out.unlink(missing_ok=True)


def generate(aid, kept, on_status=lambda msg, progress=None: None):
    """The generated captions for the kept parts of one recording (kept: [[s, e]] in source seconds), as saved in a
    short's captions.gen[aid]: {v, words: [[s, e, text, donor id, split group]], ranges, trRev, at, ...}."""
    import studio_moments as sm
    import studio_speakers as ss
    meta = sc.read_json(sc.CACHE / aid / "meta.json")
    if not meta:
        raise RuntimeError("no such recording")
    tr = sm.load_transcript(aid)              # raises RuntimeError without one
    heard, keep = plan_ranges(kept, meta.get("duration"))
    if not keep:
        raise ValueError("nothing kept to caption")
    if sum(e - s for s, e in heard) > MAX_SECONDS:
        raise ValueError("that is more than 30 minutes of the recording; trim the short first")
    res = second_listen(aid, heard, on_status)
    B = split_numbers([list(w[:3]) for w in res["words"] if inside(w, keep)])
    edits = sc.read_json(sc.CACHE / aid / "transcript-edits.json", {}) or {}
    edited = {int(k) for k in edits}
    A = split_numbers([[w[0], w[1], w[2], i] for i, w in enumerate(tr["words"]) if inside(w, keep)])
    sp = spans(A, B, edited)
    asked = [s for s in sp if not s["pinned"]]
    picks, cost, model, usage, note = {}, 0.0, None, None, ""
    runs = None
    try:
        runs = ss.runs_for(aid)
    except Exception:  # noqa: BLE001  (no voice data: the prompt just has no speaker lines)
        runs = None
    if asked and not os.environ.get("STUDIO_NO_CLAUDE"):
        on_status("Claude is picking the readings", None)
        try:
            picks, cost, model, usage, _ = ask_claude(aid, A, B, sp, runs)
        except Exception as e:  # noqa: BLE001  (the second listen wins everywhere instead)
            note = f"Claude couldn't pick ({type(e).__name__}: {str(e)[:200]}); the second listen's words are used."
    elif asked:
        note = "Claude is off for this run; the second listen's words are used."
    words = apply(A, B, edited, sp, picks)
    donor = donors(words, A)
    sp_data, _, _ = ss.load(aid)
    groups = ss.raw_assign(sp_data["turns"], [w[:3] for w in words]) if sp_data else [None] * len(words)
    out = [[round(w[0], 3), round(w[1], 3), w[2], donor[i], groups[i]] for i, w in enumerate(words)]
    picked_a = sum(1 for s in asked if picks.get(s["n"]) == "A")
    row = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": "captions", "kept": round(sum(e - s for s, e in keep), 1),
           "words": len(out), "first": len(A), "second": len(B), "places": len(sp), "asked": len(asked),
           "pickedA": picked_a, "cost": cost, "model": model, "usage": usage, "listenSeconds": res.get("seconds")}
    sm._log(aid, row)
    return {"v": 1, "words": out, "ranges": keep, "trRev": tr.get("rev"), "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "listen": res.get("model"), "claude": model, "cost": cost, "places": len(sp), "asked": len(asked),
            "pickedA": picked_a, "added": max(0, len(out) - len(A)), "note": note}


# ------------------------------------------------------------------ reading a short's generated words back

def gen_classes(aid, gen):
    """The voice class of each generated word ("me", "f", "m", "u"), by the same rules the page uses
    (js/model/captions.js genVoice): Jonathan's fix saved on the short, then the donor word's voice (only while the
    transcript is the one the words were made against), then the split group's voice."""
    import studio_speakers as ss
    r = ss.resolve(aid)
    if r["state"] != "ready":
        return None
    speakers = r["speakers"]
    by_key = {s["key"]: s for s in speakers}
    by_group = {g: s for s in speakers for g in s.get("groups") or []}
    rev = (sc.read_json(sc.CACHE / aid / "transcript.json", {}) or {}).get("rev")
    same = gen.get("trRev") == rev
    out = []
    for w in gen.get("words") or []:
        v = by_key.get(w[5]) if len(w) > 5 and w[5] else None
        if v is None and same and len(w) > 3 and w[3] is not None and 0 <= w[3] < len(r["spk"]) and r["spk"][w[3]] >= 0:
            v = speakers[r["spk"][w[3]]]
        if v is None and len(w) > 4 and w[4]:
            v = by_group.get(w[4])
        out.append(v["cls"] if v else "u")
    return out


def speech_ranges(doc):
    """{asset: [[s, e]]} the short's speech clips keep, in source seconds (the clips captions read: A1 and the voice
    tracks, as js/model/captions.js speechClips)."""
    fps = doc.get("fps") or sc.FPS
    out = {}
    for c in doc.get("clips") or []:
        if c.get("type") != "audio" or c.get("on") is False or not c.get("asset"):
            continue
        if c.get("track") != "A1" and c.get("voice") not in ("me", "them"):
            continue
        out.setdefault(c["asset"], []).append([c["in"] / fps, c["out"] / fps])
    return out


def missing(doc):
    """None when the short's captions are fine to export; "none" when a short in Generate mode has none for some of
    its speech; "part" when footage was added outside what was generated (more than half a second)."""
    cap = doc.get("captions") or {}
    if cap.get("mode") != "generate" or cap.get("on") is False:
        return None
    gen = cap.get("gen") or {}
    worst = None
    for aid, rs in speech_ranges(doc).items():
        g = gen.get(aid)
        if not g:
            return "none"
        if uncovered(rs, g.get("ranges") or []) > 0.5:
            worst = "part"
    return worst


def uncovered(rs, cover):
    """Seconds of the ranges rs that no range in cover holds."""
    total = 0.0
    for s, e in rs:
        left = [[s, e]]
        for a, b in cover:
            nxt = []
            for x, y in left:
                if b <= x or a >= y:
                    nxt.append([x, y])
                    continue
                if a > x:
                    nxt.append([x, a])
                if b < y:
                    nxt.append([b, y])
            left = nxt
        total += sum(y - x for x, y in left)
    return total
