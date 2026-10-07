"""Cleanup rules for Monarc Flow (2026-10-03): what Parakeet heard, made ready to paste. No model, nothing leaves the
laptop (decisions/log.md, 2026-10-03).

Parakeet already writes periods, commas and capitals. The rules, in this order:
  1. fillers go (um, uh, er, erm, ah, hmm) with the comma that comes with them; "like" and "you know" stay
  2. stutters go ("I I think", "the, the"); real doubles stay ("had had", "that that", "very, very")
  3. "scratch that" said as its own sentence (or opening one) takes out the sentence before it
  4. "new line" / "new paragraph" between stops or commas become line breaks ("a new line of speakers" stays)
  5. word fixes from projects/flow/words.json: whole words, case ignored ("control four" -> "Control4")
  6. no em dashes (references/voice.md): " — " becomes ", "
  7. spacing, "I", a capital at each sentence start, and one space after the end so the next take joins on

  python scripts/flow_clean.py "um so I I think we should, uh, call them"     try a line
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORDS = ROOT / "projects" / "flow" / "words.json"

# 1. fillers; "uh-huh" and "Mm-hmm" stay (a dash after), and so does "ER" (capital R)
FILLER = re.compile(r"(,\s*)?(?<![\w'-])(?:[Uu]h*m+|[Uu]h+|[Ee]rm*|[Aa]h+|[Hh]m+)(?![\w'-])(\s*,)?")
# a filler between two commas after one of these keeps one comma: "So, um, I think" -> "So, I think"
KEEP_COMMA_AFTER = {"so", "well", "yeah", "yes", "no", "okay", "ok", "right", "alright", "anyway", "actually",
                    "honestly", "basically", "look", "listen", "hey", "hi", "hello", "sure", "also", "now"}

# 2. stutters: the same word again, letters only (a phone number's "443 443" is never touched)
STUTTER = re.compile(r"(?<![\w'-])([A-Za-z']+)((?:,?\s+\1)+)(?![\w'-])", re.I)
REAL_DOUBLES = {"had", "that", "is", "very", "really", "no", "yes", "yeah", "bye", "ha", "so", "now", "well", "far",
                "more", "again", "over", "many", "much", "too", "knock", "tick", "chop", "blah", "ok", "okay"}
# with a comma between ("I, I think") only these small words count as a stutter; "very, very" is meant
COMMA_STUTTER = {"i", "i'm", "i'll", "i've", "i'd", "we", "we're", "we'll", "you", "you're", "they", "they're", "he",
                 "she", "it", "it's", "the", "a", "an", "to", "and", "but", "or", "of", "in", "on", "at", "for", "with",
                 "my", "our", "your", "this", "if", "was", "were", "what", "when", "where", "how", "why", "who", "can",
                 "will", "would", "could", "should", "just"}

# 3. scratch that
SCRATCH_ALONE = re.compile(r"(?i)^scratch that[.!?]*$")
SCRATCH_OPENS = re.compile(r"(?i)^scratch that[,.!?]*\s+")
SCRATCH_CLOSES = re.compile(r"(?i)[,;]?\s*scratch that[.!?]*$")

# 4. line breaks: only when the words stand between stops, commas, or the ends of the take
NEWLINE = re.compile(r"(?:^|(?<=[.,!?;:\n]))\s*new (line|paragraph)\s*(?:[.,!?;:]+|$)", re.I)

_fixes_cache = {"mtime": None, "rules": []}


def load_fixes(path=WORDS):
    """[(compiled pattern, written form)] from words.json, longest heard form first. Re-read when the file changes,
    so an edit counts on the next take without a restart."""
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return []
    if _fixes_cache["mtime"] == mtime:
        return _fixes_cache["rules"]
    try:
        fixes = json.loads(path.read_text(encoding="utf-8")).get("fixes", {})
    except (OSError, ValueError):
        return _fixes_cache["rules"]
    _fixes_cache.update(mtime=mtime, rules=compile_fixes(fixes))
    return _fixes_cache["rules"]


def compile_fixes(fixes):
    rules = []
    for heard in sorted(fixes, key=len, reverse=True):
        parts = [re.escape(p) for p in heard.strip().split()]
        if parts:
            rules.append((re.compile(r"(?<!\w)" + r"[\s-]+".join(parts) + r"(?!\w)", re.I), fixes[heard]))
    return rules


def drop_fillers(t):
    def sub(m):
        if m.group(1) and m.group(2):
            prev = re.search(r"([A-Za-z']+)\W*$", t[:m.start()])
            if prev and prev.group(1).lower() in KEEP_COMMA_AFTER:
                return ", "
        return " "
    return FILLER.sub(sub, t)


def drop_stutters(t):
    def sub(m):
        word, rest = m.group(1), m.group(2)
        low = word.lower()
        if low in REAL_DOUBLES or ("," in rest and low not in COMMA_STUTTER):
            return m.group(0)
        return word
    return STUTTER.sub(sub, t)


def scratch(t):
    out = []
    for s in re.split(r"(?<=[.!?])\s+", t.strip()):
        if not s:
            continue
        if SCRATCH_ALONE.match(s):
            if out:
                out.pop()
            continue
        m = SCRATCH_OPENS.match(s)
        if m:
            if out:
                out.pop()
            s = s[m.end():]
        elif SCRATCH_CLOSES.search(s):
            continue                      # "Tuesday, scratch that." takes its own sentence with it
        if s:
            out.append(s)
    return " ".join(out)


def new_lines(t):
    return NEWLINE.sub(lambda m: "\n\n" if m.group(1).lower() == "paragraph" else "\n", t)


def fix_words(t, rules):
    for pat, written in rules:
        t = pat.sub(written, t)
    return t


def tidy(t):
    t = re.sub(r"\s*(?:[—–]|--)\s*", ", ", t)                    # 6. no em dashes
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    t = re.sub(r" +([,.!?;:%])", r"\1", t)
    t = re.sub(r",(?:\s*,)+", ",", t)
    t = re.sub(r",\s*([.!?])", r"\1", t)
    t = re.sub(r"([.!?])\s*,", r"\1", t)
    t = re.sub(r"^[ \t,.;:!?]+", "", t)                         # left over from a filler that opened the take
    t = re.sub(r"(?<![\w.'-])i(?=(?:'(?:m|ve|d|ll|s))?(?![\w.-]))", "I", t)
    t = re.sub(r"(^|[.!?][ \t]+|\n[ \t]*)([a-z])", lambda m: m.group(1) + m.group(2).upper(), t)
    return t.rstrip(" \t")


def clean(text, rules=None, space_after=True):
    """The words Parakeet heard -> the text to paste ("" when nothing is left)."""
    if rules is None:
        rules = load_fixes()
    t = re.sub(r"\s+", " ", text or "").strip()
    if not t:
        return ""
    t = drop_fillers(t)
    t = drop_stutters(t)
    t = scratch(t)
    t = new_lines(t)
    t = fix_words(t, rules)
    t = tidy(t)
    if t and space_after and not t.endswith("\n"):
        t += " "
    return t


if __name__ == "__main__":
    print(repr(clean(" ".join(sys.argv[1:]))))
