"""Key notes from a call's words, for Monarc Calls (2026-10-03, brainstorms/2026-10-01-live-call-notes.md, Q32-Q45).

Plain rules, no model (Jonathan: "it is just a python script that runs deterministically"): the same words always give
the same notes. Kinds, in the order the window shows them:

  offering    what the company does: a phrase from "## Offering", or a service or brand word from "## Services and
              brands" in a sentence that also says we / we're / our / us (so Jonathan's own pitch, "EV charging
              station, generator install", doesn't count)
  constraint  what holds them back: "## Constraint" ("booked up", "can't find anybody", "months behind")
  objection   pushback: "## Objection" ("we're all set", "calls like this", "we handle it ourselves")
  email       an address written ("mike@acmeav.com") or spoken ("mike at acme a v dot com", spelled letters, "dash",
              "underscore"); checked against the company's website, a doubt flagged
  name        after "this is / my name is / ask for / speak with / talk to / what was your name", "Hey <Name>," and
              "Thank you, <Name>", or spelled out ("C O D Y"); never Jonathan or anyone under "## Not names"
  phone       ten digits written or spoken ("five one two, five five five...")
  meeting     a day and a time both said yes to (the last time mentioned in a call with a yes and a meeting word)

One mic hears both sides, so a sentence holding any "## Ignore" phrase (his pitch: "you guys", "landing page",
"Google Ads", "cold call"...) never makes an offering, constraint or objection note. The phrase file is Jonathan's:
references/call-note-phrases.md (STUDIO_PHRASES overrides it for tests). A phrase matches whole words, any case;
"*" stands for any one word.

  python scripts/calls_notes.py "We do mostly residential. Yeah we're booked up for three months."
"""
import hashlib
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHRASES = Path(os.environ.get("STUDIO_PHRASES") or (ROOT / "references" / "call-note-phrases.md"))
KINDS = ["offering", "constraint", "objection", "email", "name", "phone", "meeting"]
LABELS = {"offering": "Offering", "constraint": "Constraint", "objection": "Objection", "email": "Email",
          "name": "Name", "phone": "Phone", "meeting": "Meeting"}
SECTIONS = {"offering": "offering", "services and brands": "services", "constraint": "constraint",
            "objection": "objection", "ignore": "ignore", "not names": "not_names"}
WE = re.compile(r"\b(we|we're|were|we've|we'll|our|ours|us|i do|i install|i work)\b", re.I)
FREE_MAIL = {"gmail", "yahoo", "hotmail", "outlook", "icloud", "aol", "live", "msn", "comcast", "att", "verizon",
             "proton", "protonmail", "me"}
TLDS = {"com", "net", "org", "us", "io", "co", "biz", "info"}
NUM = {"zero": "0", "oh": "0", "o": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
       "seven": "7", "eight": "8", "nine": "9"}
HOURS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
         "eleven": 11, "twelve": 12, "noon": 12}
MINUTES = {"fifteen": 15, "thirty": 30, "forty five": 45, "forty-five": 45, "o'clock": 0}
DAYS = r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|today"
YES = re.compile(r"\b(sounds good|that works|works for me|that'll work|let's do it|let's do that|see you then|talk then|"
                 r"i'll be available|i'm available|i am available|meeting link|send (me )?(the|an|a) (invite|link)|"
                 r"put me down|book it|perfect)\b", re.I)
MEET = re.compile(r"\b(meeting|meet|invite|link|calendar|zoom|google meet|fifteen minutes|15 minutes)\b", re.I)
CALLBACK = re.compile(r"\b(call (me |you )?back|give me a call|call again)\b", re.I)


# ---------------------------------------------------------------- the phrase file

def load_phrases(path=None):
    """{offering, services, constraint, objection, ignore, not_names}: compiled patterns (and the plain words for
    not_names). Lines start with "- "; "#" lines and blank lines are notes."""
    out = {k: [] for k in ("offering", "services", "constraint", "objection", "ignore")}
    out["not_names"] = {"jonathan", "monarc", "monarch", "build"}
    sec = None
    p = Path(path) if path else PHRASES
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("## "):
            sec = SECTIONS.get(re.sub(r"\s*\(.*\)$", "", line[3:]).strip().lower())
            continue
        if not sec or not line.startswith("- "):
            continue
        phrase = line[2:].strip()
        if not phrase:
            continue
        if sec == "not_names":
            out["not_names"].add(phrase.lower())
        else:
            out[sec].append((phrase, compile_phrase(phrase)))
    return out


def compile_phrase(phrase):
    parts = []
    for w in phrase.split():
        parts.append(r"[\w'-]+" if w == "*" else re.escape(w))      # one word, never the period after it
    body = r"\s+".join(parts)
    return re.compile(r"(?<![\w'])" + body + r"(?![\w'])", re.I)


def first_match(text, pats):
    for phrase, rx in pats:
        m = rx.search(text)
        if m:
            return phrase, m.start(), m.end()
    return None


# ---------------------------------------------------------------- words to lines and sentences

def seg_text(seg):
    return " ".join(w[2] for w in seg.get("words") or []).strip()


def sentences(segments):
    """[(time, text)]: each segment's words split at . ? ! (Parakeet writes punctuation), timed by the first word."""
    out = []
    for seg in segments:
        cur, t0 = [], None
        for w in seg.get("words") or []:
            if t0 is None:
                t0 = w[0]
            cur.append(w[2])
            if re.search(r"[.?!]$", w[2]):
                out.append((t0, " ".join(cur)))
                cur, t0 = [], None
        if cur:
            out.append((t0, " ".join(cur)))
    return out


def _id(*parts):
    return hashlib.md5("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:10]


def note(kind, t, text, span=None, value=None, flag=None):
    n = {"id": _id(kind, round(t or 0, 2), value or text), "kind": kind, "t": round(t or 0, 3), "text": text.strip()}
    if span:
        n["match"] = [span[0], span[1]]
    if value:
        n["value"] = value
    if flag:
        n["flag"] = flag
    return n


# ---------------------------------------------------------------- artifacts

WRITTEN_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", re.I)


def site_domain(website):
    w = (website or "").strip().lower()
    w = re.sub(r"^https?://", "", w)
    w = re.sub(r"^www\.", "", w)
    return w.split("/")[0]


def _join_spelled(tokens):
    """['c','o','d','y'] -> 'cody'; words kept; 'dash' -> '-', 'underscore' -> '_', 'dot' -> '.'."""
    out = ""
    for t in tokens:
        lt = t.lower().strip(",;:?!")
        if lt in ("dash", "hyphen"):
            out += "-"
        elif lt == "underscore":
            out += "_"
        elif lt in ("dot", "period"):
            out += "."
        elif lt in NUM and len(lt) > 1:
            out += NUM[lt]
        else:
            out += re.sub(r"[^\w.-]", "", lt)
    return out.strip(".-")


def spoken_email(text):
    """Best guess at an address said out loud in one line, or None. 'mike at acme a v dot com' -> mike@acmeav.com."""
    low = " " + re.sub(r"\s+", " ", text.lower()) + " "
    low = low.replace("@", " at ")
    m = re.search(r" at ", low)
    if not m:
        return None
    before = low[:m.start()].split()
    after = low[m.end():].split()
    stop = {"is", "it's", "its", "email", "address", "the", "my", "it", "was", "use", "send", "to", "yeah", "okay", "so",
            "and", "uh", "um", "yep", "yes", "sure", "that's", "thats", "try", "reach", "me"}
    local = []
    for t in reversed(before[-6:]):
        if local and re.search(r"[,.;:?!]$", t):     # "Yep, mike at ..." : a comma ends the address
            break
        lt = t.strip(",.;:?!")
        if lt in stop or not lt:
            break
        local.insert(0, lt)
    dom, tld = [], None
    for t in after[:8]:
        lt = t.strip(",;:?!")
        if lt.endswith(".") and lt[:-1] in TLDS and dom:
            tld = lt[:-1]
            break
        if lt.rstrip(".") in ("dot", "period"):
            continue
        if "." in lt.rstrip("."):           # "acme.com", "gmail.com."
            head, _, tail = lt.rstrip(".").rpartition(".")
            if tail in TLDS:
                dom.append(head)
                tld = tail
                break
        if lt.rstrip(".") in TLDS and dom:
            tld = lt.rstrip(".")
            break
        dom.append(lt.rstrip("."))
    if not local or not dom or not tld:
        return None
    return f"{_join_spelled(local)}@{_join_spelled(dom)}.{tld}"


def email_notes(segments, website=None):
    """One note per line that holds an address, written or spoken, or sounds like one being given ('at ... dash',
    'at gmail'). The note's text is the whole line; value is the best guess; flag says what to check."""
    out, seen = [], set()
    dom = site_domain(website)
    for seg in segments:
        text = seg_text(seg)
        low = text.lower()
        guess = None
        m = WRITTEN_EMAIL.search(text)
        if m:
            guess = m.group(0).lower().rstrip(".")
        else:
            guess = spoken_email(text)
        sounds = guess or re.search(r"\bat\b.{0,40}\b(dash|underscore|dot|gmail|yahoo|hotmail|outlook|icloud|aol)\b", low) \
            or re.search(r"\b(dot com|dot net|\.com)\b", low)
        if not sounds:
            continue
        flag = None
        if guess:
            gdom = guess.split("@")[1]
            if gdom.split(".")[0] in FREE_MAIL:
                flag = "check the spelling"
            elif dom and gdom != dom:
                flag = f"their site is {dom}"
        else:
            flag = f"check it{': their site is ' + dom if dom else ''}"
        key = guess or text
        if key in seen:
            continue
        seen.add(key)
        out.append(note("email", seg.get("start"), text, value=guess, flag=flag))
    return out


def _digits(text):
    """Every run of digits in a line, spoken number words included ('five one two' -> '512')."""
    toks = re.findall(r"\(?\d[\d\-\.\)\s]*\d|\d|[a-zA-Z']+", text)
    runs, cur = [], ""
    for t in toks:
        lt = t.lower()
        if re.fullmatch(r"[\d\-\.\)\(\s]+", t):
            cur += re.sub(r"\D", "", t)
        elif lt in NUM:
            cur += NUM[lt]
        elif lt in ("double",):
            continue
        else:
            if cur:
                runs.append(cur)
            cur = ""
    if cur:
        runs.append(cur)
    return runs


def phone_notes(segments, own_phone=None):
    out, seen = [], set()
    own = re.sub(r"\D", "", own_phone or "")[-10:]
    for seg in segments:
        text = seg_text(seg)
        for run in _digits(text):
            if len(run) == 11 and run.startswith("1"):
                run = run[1:]
            if len(run) != 10 or run in seen:
                continue
            seen.add(run)
            value = f"({run[:3]}) {run[3:6]}-{run[6:]}"
            out.append(note("phone", seg.get("start"), text, value=value,
                            flag="same as the row's number" if run == own else None))
    return out


NAME = r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)"
NAME_PATTERNS = [re.compile(p) for p in (
    r"\b[Tt]his is " + NAME, r"\b[Mm]y name is " + NAME, r"\b[Mm]y name's " + NAME, r"\b" + NAME + r" speaking\b",
    r"\b[Aa]sk for " + NAME, r"\b[Ss]peak (?:with|to) " + NAME, r"\b[Tt]alk to " + NAME,
    r"\b(?:[Hh]ey|[Hh]i|[Hh]ello),? " + NAME + r"[,.!]", r"\b(?:[Tt]hank you|[Tt]hanks|[Nn]o problem),? " + NAME + r"[.!,]",
    r"\b[Ww]hat (?:was|is) your name\?\s*" + NAME)]
SPELLED = re.compile(r"\b((?:[A-Za-z][\s\-]){2,}[A-Za-z])\b")


ASKED = re.compile(r"\b(what(?:'s| was| is) your name|who am i speaking with|who's this|who is this)\??\s*$", re.I)
ANSWER = re.compile(r"^\s*(?:it's |this is |i'm )?([A-Z][a-z]+)[.?!,]?(?:\s|$)")


def name_notes(sents, not_names):
    out, seen = [], set()
    skip = {w.lower() for w in not_names} | {"this", "that", "the", "okay", "yeah", "yes", "sir", "ma'am", "man", "bro",
                                             "guys", "there", "everyone", "sorry", "perfect", "great", "thanks", "hello"}
    asked = False
    for t, text in sents:
        found = None
        if asked and len(text.split()) <= 4:          # "What was your name?" then "Stacy?" in the next sentence
            m = ANSWER.match(text)
            if m and m.group(1).lower() not in skip:
                found = (m.group(1), m.start(1), m.end(1))
        asked = bool(ASKED.search(text))
        for rx in ([] if found else NAME_PATTERNS):
            m = rx.search(text)
            if m:
                cand = m.group(1).strip()
                first = cand.split()[0].lower()
                if first not in skip and cand.lower() not in skip:
                    found = (cand, m.start(1), m.end(1))
                    break
        if not found:
            m = SPELLED.search(text)
            if m and len(re.sub(r"[\s\-]", "", m.group(1))) >= 3:
                cand = re.sub(r"[\s\-]", "", m.group(1)).capitalize()
                if cand.lower() not in skip:
                    found = (cand, m.start(1), m.end(1))
        if found and found[0].lower() not in seen:
            seen.add(found[0].lower())
            out.append(note("name", t, text, span=(found[1], found[2]), value=found[0]))
    return out


TIME_RX = re.compile(r"\b(?:at|around|by|after)?\s*(\d{1,2})(?::(\d{2}))?\s*(a\.?\s?m\.?|p\.?\s?m\.?)?(?![\d:])|"
                     r"\b(?:at|around|by|after)\s+(" + "|".join(HOURS) + r")(?:\s+(fifteen|thirty|forty[ -]five|o'clock))?\b",
                     re.I)


def _times(text):
    """[(position, 'h:mm am/pm')] in one line; Parakeet glues 'at2 p.m.' together, so 'at' needs no space."""
    out = []
    low = re.sub(r"\bat(\d)", r"at \1", text)
    for m in TIME_RX.finditer(low):
        if m.group(1):
            h, mm, ap = int(m.group(1)), m.group(2), m.group(3)
            if not (1 <= h <= 12) or (not mm and not ap and not re.match(r"\s*(at|around|by|after)", m.group(0), re.I)):
                continue
            label = f"{h}:{mm or '00'}" + (f" {'pm' if ap.lower().startswith('p') else 'am'}" if ap else "")
        else:
            h = HOURS[m.group(4).lower()]
            mm = MINUTES.get((m.group(5) or "").lower().replace("-", " "), 0)
            label = f"{h}:{mm:02d}"
        out.append((m.start(), label))
    return out


def meeting_notes(segments):
    """The day and time both said yes to: the last time mentioned in the call (with the nearest day before it), when
    the call also has a yes and a meeting word, and no 'call back' after that time."""
    texts = [(seg.get("start"), seg_text(seg)) for seg in segments]
    whole = " ".join(t for _, t in texts)
    if not YES.search(whole) or not MEET.search(whole):
        return []
    last, day = None, None
    for t, text in texts:
        days = [(m.start(), m.group(0).lower()) for m in re.finditer(DAYS, text, re.I)]
        for pos, label in _times(text):
            before = [d for p, d in days if p <= pos]
            day = before[-1] if before else (day if days == [] else days[0][1])
            last = (t, text, label, day)
        if days:
            day = days[-1][1]
    if not last:
        return []
    t, text, label, d = last
    after = " ".join(x for tt, x in texts if tt is not None and t is not None and tt > t)
    if CALLBACK.search(after):
        return []
    value = f"{d.capitalize()} {label}" if d else label
    return [note("meeting", t, text, value=value)]


# ---------------------------------------------------------------- everything

def extract(segments, phrases, website=None, phone=None):
    """The key notes of one call, in the order of KINDS, then by time."""
    notes = []
    sents = sentences(segments)
    for t, text in sents:
        if first_match(text, phrases["ignore"]):
            continue
        for kind in ("constraint", "objection"):
            hit = first_match(text, phrases[kind])
            if hit:
                notes.append(note(kind, t, text, span=hit[1:]))
        hit = first_match(text, phrases["offering"])
        if not hit and WE.search(text):
            hit = first_match(text, phrases["services"])
        if hit:
            notes.append(note("offering", t, text, span=hit[1:]))
    notes += email_notes(segments, website)
    notes += name_notes(sents, phrases["not_names"])
    notes += phone_notes(segments, phone)
    notes += meeting_notes(segments)
    order = {k: i for i, k in enumerate(KINDS)}
    seen, out = set(), []
    for n in sorted(notes, key=lambda n: (order[n["kind"]], n["t"])):
        key = (n["kind"], n.get("value") or n["text"])
        if key in seen:
            continue
        seen.add(key)
        out.append(n)
    return out


def as_text(notes):
    """The kept notes as plain lines, for the doc and the Outreach Log's Transcript."""
    return "\n".join(f"{LABELS.get(n['kind'], n['kind'].title())}: {n.get('value') or n['text']}"
                     if n["kind"] in ("email", "name", "phone", "meeting") and n.get("value") else
                     f"{LABELS.get(n['kind'], n['kind'].title())}: {n['text']}" for n in notes)


if __name__ == "__main__":
    import json
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    text = " ".join(sys.argv[1:]) or "We do mostly residential. We're booked up for three months. It's mike at acme a v dot com."
    words = [[i * 0.4, i * 0.4 + 0.3, w] for i, w in enumerate(text.split())]
    print(json.dumps(extract([{"start": 0, "end": len(words) * 0.4, "words": words}], load_phrases()), indent=1))
