"""Find moments in a long recording for Monarc Studio (2026-09-29).

One Anthropic API call over the transcript. The transcript goes out as numbered lines, one per speech segment
("412|01:12:34|text"), and Claude answers with line numbers only; this script turns them into times (first word
start -0.3 s, last word end +0.4 s), so a timestamp can never be made up. Only transcript text leaves the laptop.

Model claude-opus-5 (the Claude API reference's default), streamed, adaptive thinking, effort high, JSON schema
output, server-side fallbacks. Prices in PRICES were checked on https://platform.claude.com/docs/en/about-claude/pricing
on 2026-09-29 (Opus 5 $5 / $25 per million tokens). The first real run: a 4 h 03 m session, 1,823 lines, 42,567
input tokens, estimate $0.59 to $1.21.

  python scripts/studio_moments.py <asset-id> --estimate   token count (free) and a dollar range
  python scripts/studio_moments.py <asset-id>              run it; writes media/.studio/<id>/moments.json
  python scripts/studio_moments.py <asset-id> --speakers-only [--estimate]
                                                           label the voices only (moments.json untouched)

Voices (2026-09-30): once the voice split has run (studio_speakers.py), the lines carry inline tags for who is
speaking ("412|01:12:34|[S2] yeah we handle it [S1] okay have you..."; the numbering is unchanged) and a table of
tags goes on top (seconds of speech, pitch, voiceprint match). In the same call Claude names which tags are Jonathan
and, for everyone else, gender, first name, role and "same person as" to join split tags. That lands in
speaker-labels.json, which colors the captions. The labels are the expensive part: the labels-only run on the
4 h 03 m session (426 voice groups) cost $1.72 (58,416 tokens in, 57,068 out, nearly all thinking, 11 minutes),
against a first estimate of $0.54 to $1.04.

Key: ANTHROPIC_API_KEY through outreach_common (repo .env, then ~/.monarc/secrets.env, then the environment).
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_common as sc  # noqa: E402

MODEL = "claude-opus-5"
PRICES = {"claude-opus-5": (5.0, 25.0), "claude-sonnet-5": (2.0, 10.0)}   # $ per million tokens, in / out
OUT_TOKENS_RANGE = (15000, 40000)   # answer JSON plus thinking, for the estimate
# what the voice labels add (or cost alone, --speakers-only). Measured 2026-09-30 on the 4 h 03 m session (426 voice
# groups): 57,068 output tokens, nearly all thinking, $1.72; the first guess of 10-30k was far too low.
OUT_TOKENS_VOICES = (40000, 70000)
MAX_TOKENS = 128000                 # Opus 5's ceiling; moments plus voice labels plus thinking can pass 64k (streamed)
PAD_BEFORE, PAD_AFTER = 0.3, 0.4

TYPES = ["objection", "booking", "funny_awkward", "best_line"]
OUTCOMES = ["booked", "callback", "not_interested", "gatekeeper", "voicemail", "no_answer", "other", "not_a_call"]
GENDERS = ["woman", "man", "unknown"]
ROLES = ["gatekeeper", "owner", "service_rep", "voicemail_greeting", "phone_menu", "other"]

VOICES_PROPS = {
    "jonathan_tags": {"type": "array", "items": {"type": "string"}},
    "voices": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "tag": {"type": "string"},
            "gender": {"type": "string", "enum": GENDERS},
            "name": {"type": "string"},
            "role": {"type": "string", "enum": ROLES},
            "same_as": {"type": "string"},
        },
        "required": ["tag", "gender", "name", "role", "same_as"],
        "additionalProperties": False}},
}
SCHEMA_VOICES = {"type": "object", "properties": VOICES_PROPS, "required": ["jonathan_tags", "voices"],
                 "additionalProperties": False}

SCHEMA = {
    "type": "object",
    "properties": {
        "calls": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"},
                "label": {"type": "string"},
                "outcome": {"type": "string", "enum": OUTCOMES},
                "summary": {"type": "string"},
            },
            "required": ["start_line", "end_line", "label", "outcome", "summary"],
            "additionalProperties": False}},
        "moments": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "call": {"type": "integer"},
                "type": {"type": "string", "enum": TYPES},
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"},
                "title": {"type": "string"},
                "reason": {"type": "string"},
                "strength": {"type": "integer"},
            },
            "required": ["call", "type", "start_line", "end_line", "title", "reason", "strength"],
            "additionalProperties": False}},
    },
    "required": ["calls", "moments"],
    "additionalProperties": False,
}

INTRO = """You help Jonathan Beach, founder of Monarc Build, turn his recorded cold-calling sessions into short vertical videos.
Monarc Build sells managed Google Ads, SEO and websites to home integrators and electricians. Jonathan records his screen and
audio in OBS while he dials. One recording holds many calls, plus stretches that are not calls: dialing, ringing, voicemail
greetings, hold music, and Jonathan talking to himself or to someone in the room.

The transcript comes as numbered lines, one per stretch of speech: LINE|HH:MM:SS|text. """
MIXED = """The speech-to-text model mixes both
sides of each phone call into one voice and can mishear names and brand words; read for meaning.

Do two things.
"""
TAGGED = """Tags like [S12] inside the text mark who is
speaking (see task 3). The speech-to-text model can mishear names and brand words; read for meaning.

Do three things.
"""

TASKS = """1. calls: split the recording into its calls. A call runs from the first line where Jonathan reaches a person or a voicemail
   to the last line of that exchange. Give each a label, an outcome and a one-sentence summary. The label is the person's
   first name and the company when they are said ("Sean, C3 Electrical"); with no name, who answered and the company
   ("Front desk, Volt Electric", "Voicemail, Bright Home"). Keep it to a few words and leave the outcome out of it: the
   outcome has its own field. Long stretches that are not calls may be listed with outcome not_a_call so the list is
   complete; label those with what happens in them ("Between dials", "Talking to the camera").
2. moments: the best material for 20 to 90 second shorts, each one whole exchange around one point (it may run longer; Jonathan
   trims it). Types:
   - objection: a prospect pushes back ("we already have a guy", "send me an email", "not interested", price) and how Jonathan
     answers it, win or lose.
   - booking: a prospect agrees to a meeting, asks for pricing, or otherwise moves forward.
   - funny_awkward: hang-ups, gatekeepers, strange replies, awkward pauses, anything a viewer would laugh at.
   - best_line: an opener, pitch line or reframe of Jonathan's that lands, worth showing other owners.
   Give each a short title (under 8 words), a one-line reason it works as a short, and strength 1 to 5 (5 = post it first).
   A moment's call is the index (0-based) of its call in your calls list. Start a moment on the line that sets up the point,
   not in the middle of it, and end it once the point has landed."""

RULES = """Answer with line numbers only. Do not invent lines. Prefer fewer, stronger moments over many weak ones, but do not skip a
strong one: a four-hour session usually holds 15 to 40."""

SYSTEM = INTRO + MIXED + TASKS + "\n\n" + RULES      # a recording without a voice split (call labels reworded 2026-10-01)

VOICES_TASK = """voices: the transcript marks who is speaking with tags like [S12]; a tag holds until the next one. The tags
come from a voice split on the audio, not from the words: one person is often split into two or three tags, and a tag
can be off by a word or two at a turn edge. The table above the transcript gives each tag's seconds of speech, median
pitch (men mostly under 165 Hz, women above), and, when known, how closely it matches Jonathan's saved voiceprint (0 to 1;
a guide, not proof).
   - jonathan_tags: every tag that is Jonathan (he gives his name, says Monarc Build, pitches, asks for the meeting).
   - voices: one entry for every other tag with real speech. gender: woman or man (unknown only if neither the words nor
     the pitch tell). Judge from names, "sir" or "ma'am", and what people say about themselves first, pitch second.
     name: the person's first name if it is said on the call, else empty. role: gatekeeper (receptionist, office manager,
     front desk, answering service), owner, service_rep (technician, estimator, dispatcher or other staff),
     voicemail_greeting, phone_menu, or other (anyone else, like a voice in a video playing in the room). same_as: when
     one person was split into several tags within a call, the tag of their main one; else empty.
   Every tag with words gets an answer, short ones too: a tag holding a word or two usually belongs to whoever is talking
   around it, so put it in jonathan_tags if that is Jonathan, or give it that person's gender and name with same_as their
   main tag. Only a tag with no real words (a cough, a beep) may be left out."""

SYSTEM_VOICES = """You help Jonathan Beach, founder of Monarc Build, caption his recorded cold-calling sessions. Monarc Build sells
managed Google Ads, SEO and websites to home integrators and electricians. Jonathan records his screen and audio in OBS
while he dials; one recording holds many calls plus stretches that are not calls (dialing, voicemail greetings, videos
playing, Jonathan talking to someone in the room). The captions are colored by who is talking, so each voice needs a
label.

The transcript comes as numbered lines, one per stretch of speech: LINE|HH:MM:SS|text. The speech-to-text model can
mishear names and brand words; read for meaning.

One task. """ + VOICES_TASK

SYSTEM_TAGGED = INTRO + TAGGED + TASKS + "\n3. " + VOICES_TASK + "\n\n" + RULES


def _client():
    import anthropic
    from outreach_common import get_secret
    key = get_secret("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not found in .env, ~/.monarc/secrets.env or the environment")
    return anthropic.Anthropic(api_key=key)


def load_transcript(aid):
    d = sc.CACHE / aid
    tr = sc.read_json(d / "transcript.json")
    if not tr:
        raise RuntimeError("no transcript yet")
    edits = sc.read_json(d / "transcript-edits.json", {}) or {}
    for k, v in edits.items():
        i = int(k)
        if 0 <= i < len(tr["words"]):
            tr["words"][i][2] = v
    return tr


def hms(s):
    s = int(s)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def build_lines(tr, tags=None):
    """One line per segment. With tags (each word's voice group, or None), a [S12] tag opens each line and marks each
    change of voice inside it."""
    words = tr["words"]
    lines = []
    for i, (s, e, w0, w1) in enumerate(tr["segments"]):
        if tags is None:
            text = " ".join(w[2] for w in words[w0:w1 + 1])
        else:
            parts, cur = [], None
            for j in range(w0, w1 + 1):
                t = tags[j] if j < len(tags) else None
                if t is not None and t != cur:
                    parts.append(f"[{t}]")
                    cur = t
                parts.append(words[j][2])
            text = " ".join(parts)
        lines.append(f"{i}|{hms(s)}|{text}")
    return "\n".join(lines)


def voice_context(aid, tr):
    """(tags per word, the voice table text, the split's rev) once the voice split has run, else (None, "", None)."""
    import studio_speakers as ss
    sp = sc.read_json(sc.CACHE / aid / "speakers.json")
    tags = ss.raw_tags(aid, tr["words"])
    if tags is None or not sp:
        return None, "", None
    rows = ss.voice_table(aid)
    head = "Voices (tag: seconds of speech, median pitch" + (", voiceprint match to Jonathan" if any(
        "voiceprint" in r for r in rows) else "") + "):\n" + "\n".join(rows)
    return tags, head, sp["rev"]


def request(tr, aid=None, voices_only=False):
    """(the request, whether it carries voice tags, the split's rev the tags come from)."""
    tags, head, rev = voice_context(aid, tr) if aid else (None, "", None)
    body = "Transcript:\n" + build_lines(tr, tags)
    if tags is not None:
        body = head + "\n\n" + body
    if voices_only:
        if tags is None:
            raise RuntimeError("no voice split for this recording yet")
        mo = sc.read_json(sc.CACHE / aid / "moments.json", {}) or {}
        if mo.get("calls"):
            body = ("Calls already found (line ranges): " + "; ".join(
                f"{c['lines'][0]}-{c['lines'][1]} {c['label']}" for c in mo["calls"] if c.get("lines")) + "\n\n" + body)
        system = SYSTEM_VOICES
    else:
        system = SYSTEM_TAGGED if tags is not None else SYSTEM
    return dict(model=MODEL, max_tokens=MAX_TOKENS, system=system,
                messages=[{"role": "user", "content": body}]), tags is not None, rev


def schema_for(voices, voices_only=False):
    if voices_only:
        return SCHEMA_VOICES
    if not voices:
        return SCHEMA
    return {**SCHEMA, "properties": {**SCHEMA["properties"], **VOICES_PROPS},
            "required": SCHEMA["required"] + ["jonathan_tags", "voices"]}


def estimate(aid, voices_only=False):
    tr = load_transcript(aid)
    client = _client()
    req, voices, _ = request(tr, aid, voices_only)
    n = client.messages.count_tokens(model=req["model"], system=req["system"], messages=req["messages"]).input_tokens
    pin, pout = PRICES[MODEL]
    out = OUT_TOKENS_VOICES if voices_only else (
        (OUT_TOKENS_RANGE[0] + OUT_TOKENS_VOICES[0], OUT_TOKENS_RANGE[1] + OUT_TOKENS_VOICES[1]) if voices
        else OUT_TOKENS_RANGE)
    lo = n * pin / 1e6 + out[0] * pout / 1e6
    hi = n * pin / 1e6 + out[1] * pout / 1e6
    return {"model": MODEL, "input_tokens": n, "lines": len(tr["segments"]), "voices": voices,
            "low": round(lo, 2), "high": round(hi, 2),
            "prices": f"${pin:g} / ${pout:g} per million tokens (checked 2026-09-29)"}


def _call(client, req, schema, on_status, effort="high"):
    t0 = time.time()
    with client.beta.messages.stream(
        **req,
        thinking={"type": "adaptive"},
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},
    ) as stream:
        n = 0
        for _ in stream:
            n += 1
            if n % 200 == 0:
                on_status(f"Claude is reading ({int(time.time() - t0)} s)")
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        det = getattr(msg, "stop_details", None)
        raise RuntimeError(f"Claude declined ({getattr(det, 'category', None)}): {getattr(det, 'explanation', '')}")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("answer cut off at max_tokens; try again")
    text = next(b.text for b in msg.content if b.type == "text")
    u = msg.usage
    pin, pout = PRICES.get(MODEL, (5.0, 25.0))
    cost = (u.input_tokens or 0) * pin / 1e6 + (u.output_tokens or 0) * pout / 1e6
    return json.loads(text), msg, round(cost, 3), round(time.time() - t0, 1)


def _log(aid, row):
    with open(sc.CACHE / aid / "moments-log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


HEADLINE_SCHEMA = {"type": "object", "properties": {"headlines": {"type": "array", "items": {"type": "string"}}},
                   "required": ["headlines"], "additionalProperties": False}
HEADLINE_SYSTEM = """You write thumbnail headlines for Jonathan Beach's short vertical videos of his cold calls. He runs Monarc Build,
a marketing agency for home integrators and electricians. This short is a Trailer: it opens on the peak of the call and
cuts away before the reply, then rewinds to the dial tone. The headline sits in a white box on the first frame, so it
is the thumbnail.

Write exactly three options. Each: six words at most, plain words, curiosity or tension that makes someone watch
without giving away the reply. No emojis, no hashtags, no quotation marks, no em dashes, no clickbait words like
INSANE or SHOCKING. Sentence case."""


def headlines(aid, s0, s1, title=""):
    """Three thumbnail headlines for a Trailer (Make trailer, 2026-09-30): one small, low-effort Claude call over the
    words of the peak and the moment's title. Jonathan picks one or types his own; nothing goes on screen unseen."""
    tr = load_transcript(aid)
    import studio_speakers as ss
    words = tr["words"]
    try:
        v = ss.resolve(aid, words)
        name = lambda i: (v["speakers"][v["spk"][i]]["name"] if v.get("spk") and v["spk"][i] >= 0 else "?")  # noqa: E731
    except Exception:  # noqa: BLE001
        name = lambda i: "?"  # noqa: E731
    lines, cur = [], None
    for i, w in enumerate(words):
        if w[0] < s0 - 15 or w[0] >= s1:
            continue
        who = name(i)
        if who != cur:
            lines.append(f"\n{who}:")
            cur = who
        lines.append(w[2])
    body = (f"Moment title: {title}\n\nThe peak (the short opens on this and cuts before the reply; lines before it are "
            f"context):{' '.join(lines)}")
    req = dict(model=MODEL, max_tokens=4000, system=HEADLINE_SYSTEM, messages=[{"role": "user", "content": body}])
    data, msg, cost, secs = _call(_client(), req, HEADLINE_SCHEMA, lambda s: None, effort="low")
    out = [h.strip().strip('"').replace("—", ",")[:60] for h in data.get("headlines", []) if h.strip()][:3]
    _log(aid, {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": "headlines", "model": msg.model, "cost": cost,
               "seconds": secs, "usage": {"input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens}})
    return {"headlines": out, "cost": cost}


def label_voices(aid, on_status=None):
    """--speakers-only: Claude labels the voices; moments.json is left as it is."""
    import studio_speakers as ss
    on_status = on_status or (lambda s: None)
    tr = load_transcript(aid)
    req, _, rev = request(tr, aid, voices_only=True)
    on_status("calling Claude")
    data, msg, cost, secs = _call(_client(), req, SCHEMA_VOICES, on_status)
    out = ss.write_labels(aid, data["jonathan_tags"], data["voices"], msg.model, rev=rev)
    u = msg.usage
    _log(aid, {"t": out["created"], "kind": "voices", "model": msg.model, "cost": cost, "seconds": secs,
               "usage": {"input_tokens": u.input_tokens, "output_tokens": u.output_tokens},
               "jonathan": len(out["jonathan"]), "voices": len(out["voices"])})
    return {"cost": cost, "seconds": secs, "jonathan": out["jonathan"], "voices": out["voices"]}


def to_times(tr, a, b):
    segs, words = tr["segments"], tr["words"]
    a = max(0, min(len(segs) - 1, int(a)))
    b = max(a, min(len(segs) - 1, int(b)))
    start = words[segs[a][2]][0] - PAD_BEFORE
    end = words[segs[b][3]][1] + PAD_AFTER
    return round(max(0.0, start), 3), round(min(tr.get("duration") or end, end), 3)


def find(aid, on_status=None):
    on_status = on_status or (lambda s: None)
    tr = load_transcript(aid)
    req, voices, rev = request(tr, aid)
    on_status("calling Claude")
    data, msg, cost, secs = _call(_client(), req, schema_for(voices), on_status)
    u = msg.usage
    calls = []
    for i, c in enumerate(data["calls"]):
        s, e = to_times(tr, c["start_line"], c["end_line"])
        calls.append({"id": f"c{i + 1:02d}", "start": s, "end": e, "label": c["label"], "outcome": c["outcome"],
                      "summary": c["summary"], "lines": [c["start_line"], c["end_line"]]})
    old = {m["id"]: m for m in (sc.read_json(sc.CACHE / aid / "moments.json", {}) or {}).get("moments", [])}
    moments = []
    for i, m in enumerate(sorted(data["moments"], key=lambda m: (m["start_line"], m["end_line"]))):
        s, e = to_times(tr, m["start_line"], m["end_line"])
        call = calls[m["call"]]["id"] if 0 <= m["call"] < len(calls) else None
        mid = f"m{i + 1:02d}"
        moments.append({"id": mid, "call": call, "type": m["type"] if m["type"] in TYPES else "best_line",
                        "start": s, "end": e, "title": m["title"].strip(), "reason": m["reason"].strip(),
                        "strength": max(1, min(5, int(m["strength"]))), "lines": [m["start_line"], m["end_line"]],
                        "state": old.get(mid, {}).get("state", "new")})
    result = {"v": 1, "asset": aid, "model": msg.model, "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "transcriptRev": tr.get("rev"), "calls": calls, "moments": moments,
              "usage": {"input_tokens": u.input_tokens, "output_tokens": u.output_tokens}, "cost": cost,
              "seconds": secs}
    labels = None
    if voices:
        import studio_speakers as ss
        try:
            labels = ss.write_labels(aid, data.get("jonathan_tags") or [], data.get("voices") or [], msg.model, rev=rev)
            result["voices"] = {"jonathan": len(labels["jonathan"]), "others": len(labels["voices"])}
        except RuntimeError as e:         # the split changed mid-call: keep the moments, say why the labels are gone
            result["voices"] = {"error": str(e)}
    sc.write_json_atomic(sc.CACHE / aid / "moments.json", result)
    _log(aid, {"t": result["created"], "kind": "moments", "model": msg.model, "usage": result["usage"],
               "cost": result["cost"], "moments": len(moments), "calls": len(calls), "voices": result.get("voices")})
    return result


if __name__ == "__main__":
    aid = sys.argv[1]
    if "--speakers-only" in sys.argv:
        if "--estimate" in sys.argv:
            print(json.dumps(estimate(aid, voices_only=True), indent=1))
        else:
            r = label_voices(aid, on_status=print)
            print(f"Jonathan: {len(r['jonathan'])} tags; others: {len(r['voices'])}; ${r['cost']}, {r['seconds']} s")
            for k, v in r["voices"].items():
                print(f"  {k:5} {v['gender']:7} {v['role']:18} {v['name'] or '-':12} {v['same_as']}")
    elif "--estimate" in sys.argv:
        print(json.dumps(estimate(aid), indent=1))
    else:
        r = find(aid, on_status=print)
        print(f"{len(r['calls'])} calls, {len(r['moments'])} moments, ${r['cost']}, {r['seconds']} s")
        for m in r["moments"]:
            print(f"  {m['id']} {hms(m['start'])}-{hms(m['end'])} {m['type']:13} {m['strength']} {m['title']}")
