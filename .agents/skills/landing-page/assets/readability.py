"""Readability check for a monarcbuild.com page (Style Guide Copy 7, Jonathan 2026-09-25).

Usage: python readability.py <page.html> [--strict] [--json] [--exempt <file>] [--grade 8] [--sentence 25]

Strips <script>, <style>, <svg>, and <noscript>, then scores the visible text per
<section id> and for the whole page: words, sentences, average and longest sentence,
Flesch-Kincaid grade, Flesch reading ease, and the share of words with three or more
syllables. Three sub-scores per section: headline and sub (h1, h2, h3, and the first
paragraph after an h1 or h2), body (every other p, li, dd, summary), and card backs
(text under an element whose class carries "back"). Text inside the booking popup
(an element whose class carries "modal") is scored on its own line and left out of
the visible-word total, so the word budget of Style Guide 6.16 can be read straight
off the summary. A span inside a heading does not split it. A nested span, div, or button inside a block (the flip cards are
spans inside a button inside an li) starts a new run, so a card's counter, title,
line, and hint are never read as one sentence. A run with no word in it (a bare "02")
is skipped, and a section is only graded once it holds ten words.

Two scores are printed side by side. Raw counts every syllable. Whitelisted treats
every word in the exempt file (brand names, trade terms; default readability-exempt.txt
beside this script) and every capitalized word that does not open a sentence as one
syllable, so the score reads sentence length and everyday-word syllables only. The
rule is judged on the whitelisted score.

--strict exits 1 when any graded section's whitelisted grade is above the target
(default 8) or any sentence runs past the sentence cap (default 25 words). Without it
the script reports and exits 0. --json prints the same numbers as JSON for the page spec.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

DEFAULT_GRADE = 8.0
DEFAULT_SENTENCE = 25
MIN_WORDS_TO_GRADE = 10
EXEMPT_FILE = Path(__file__).resolve().parent / "readability-exempt.txt"
SKIP_TAGS = {"script", "style", "svg", "noscript", "template"}
HEAD_TAGS = {"h1", "h2", "h3"}
BODY_TAGS = {"p", "li", "dd", "dt", "summary", "figcaption", "blockquote", "td", "th"}
SPLIT_TAGS = {"span", "div", "button", "br", "a", "label", "small", "time", "cite"} | HEAD_TAGS | BODY_TAGS


class Text(HTMLParser):
    """Collects text runs tagged with section id, kind (head, sub, body, back), and popup."""

    def __init__(self):
        super().__init__()
        self.runs = []            # (section, kind, popup, text)
        self._stack = []          # (tag, attrs)
        self._section = "page"
        self._skip = 0
        self._block = None        # (section, kind, popup) while a block element is open
        self._parts = []
        self._await_sub = False   # the next p after an h1/h2 is the sub

    def _has_class(self, attrs, word):
        return word in (attrs.get("class") or "").split()

    def _in(self, word):
        return any(self._has_class(a, word) for t, a in self._stack)

    def _head_span(self, tag):
        # a span inside a heading is styling (an accent word, the colored Google letters): the heading stays one run
        return tag == "span" and self._block[1] == "head"

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._stack.append((tag, a))
        if tag in SKIP_TAGS:
            self._skip += 1
            return
        if tag == "section" and a.get("id"):
            self._section = a["id"]
        if a.get("id") == "sent":
            self._section = "sent"
        if tag in HEAD_TAGS or tag in BODY_TAGS:
            self._flush()
            if tag in HEAD_TAGS:
                kind = "head"
                self._await_sub = tag in ("h1", "h2")
            elif tag == "p" and self._await_sub:
                kind = "sub"
                self._await_sub = False
            elif self._in("back"):
                kind = "back"
            else:
                kind = "body"
            self._block = (self._section, kind, self._in("modal"))
        elif tag in SPLIT_TAGS and self._block is not None and not self._head_span(tag):
            # a nested element inside an open block: the text so far is one run, what follows is another
            self._flush(keep=True)
            if self._in("back") and self._block[1] == "body":
                self._block = (self._block[0], "back", self._block[2])

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self._skip:
            self._skip -= 1
        if tag in HEAD_TAGS or tag in BODY_TAGS:
            self._flush()
        elif tag in SPLIT_TAGS and self._block is not None and not self._head_span(tag):
            self._flush(keep=True)
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                del self._stack[i:]
                break

    def handle_data(self, data):
        if self._skip:
            return
        if self._block is not None:
            self._parts.append(data)
        elif data.strip():
            kind = "back" if self._in("back") else "body"
            self.runs.append((self._section, kind, self._in("modal"), " ".join(data.split())))

    def _flush(self, keep=False):
        if self._block is None:
            return
        section, kind, popup = self._block
        text = " ".join("".join(self._parts).split())
        if text:
            self.runs.append((section, kind, popup, text))
        self._parts = []
        if not keep:
            self._block = None


def load_exempt(path):
    words = set()
    p = Path(path)
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                words.add(line.lower())
    return words


def sentences(text):
    """Split on . ! ? followed by space or end; a dot between word characters ($2.5k, Josh.ai) does not end a sentence."""
    guarded = re.sub(r"(?<=\w)\.(?=\w)", "\u0000", text)
    parts = re.split(r"(?<=[.!?])\s+", guarded)
    return [s.replace("\u0000", ".").strip() for s in parts if s.strip()]


def tokens(sentence):
    return [w for w in re.findall(r"[A-Za-z0-9$][A-Za-z0-9$'\-\.]*", sentence) if re.search(r"[A-Za-z0-9]", w)]


def has_word(toks):
    return any(re.search(r"[A-Za-z]", t) for t in toks)


def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 1
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    groups = re.findall(r"[aeiouy]+", w)
    return max(1, len(groups))


def score(runs, exempt, sentence_cap):
    """Return the metrics for a list of text runs, or None when there is nothing to score."""
    n_words = n_sent = syl_raw = syl_wl = poly = longest = 0
    long_sentences = []
    for text in runs:
        for s in sentences(text):
            toks = tokens(s)
            if not toks or not has_word(toks):
                continue
            n_sent += 1
            n_words += len(toks)
            if len(toks) > longest:
                longest = len(toks)
            if len(toks) > sentence_cap:
                long_sentences.append(s[:90])
            for i, t in enumerate(toks):
                raw = syllables(t)
                syl_raw += raw
                exempt_word = t.lower().strip(".,;:'\"") in exempt or (i > 0 and t[:1].isupper())
                wl = 1 if exempt_word else raw
                syl_wl += wl
                if wl >= 3:
                    poly += 1
    if n_words == 0 or n_sent == 0:
        return None
    asl = n_words / n_sent
    fk = lambda syl: 0.39 * asl + 11.8 * (syl / n_words) - 15.59
    fre = lambda syl: 206.835 - 1.015 * asl - 84.6 * (syl / n_words)
    return {
        "words": n_words,
        "sentences": n_sent,
        "avg_sentence": round(asl, 1),
        "longest_sentence": longest,
        "fk_raw": round(fk(syl_raw), 1),
        "fk": round(fk(syl_wl), 1),
        "fre": round(fre(syl_wl), 0),
        "poly_share": round(poly / n_words, 2),
        "long_sentences": long_sentences,
    }


def flag_value(flags, name, default=None):
    if name in flags and flags.index(name) + 1 < len(flags):
        return flags[flags.index(name) + 1]
    return default


def main():
    flags = sys.argv[1:]
    args = [a for a in flags if not a.startswith("--")]
    for name in ("--exempt", "--grade", "--sentence"):
        v = flag_value(flags, name)
        if v in args:
            args.remove(v)
    if not args:
        sys.exit(__doc__)
    strict = "--strict" in flags
    as_json = "--json" in flags
    grade_cap = float(flag_value(flags, "--grade", DEFAULT_GRADE))
    sentence_cap = int(flag_value(flags, "--sentence", DEFAULT_SENTENCE))
    exempt = load_exempt(flag_value(flags, "--exempt", EXEMPT_FILE))

    html = open(args[0], encoding="utf-8", errors="replace").read()
    t = Text()
    t.feed(html)
    t._flush()

    order = []
    by_section = {}
    for section, kind, popup, text in t.runs:
        key = "popup" if popup else section
        if key not in by_section:
            by_section[key] = {"head": [], "sub": [], "body": [], "back": [], "all": []}
            order.append(key)
        by_section[key][kind].append(text)
        by_section[key]["all"].append(text)

    report = {"file": args[0], "grade_cap": grade_cap, "sentence_cap": sentence_cap, "sections": {}, "failures": []}
    visible_words = 0
    back_words = 0
    for key in order:
        parts = by_section[key]
        sec = {}
        for kind in ("head", "sub", "body", "back", "all"):
            m = score(parts[kind], exempt, sentence_cap)
            if m:
                sec[kind] = m
        report["sections"][key] = sec
        if "all" in sec and key != "popup":
            visible_words += sec["all"]["words"]
        if "back" in sec:
            back_words += sec["back"]["words"]
        for kind in ("head", "sub", "body", "back"):
            m = sec.get(kind)
            if not m:
                continue
            if m["words"] >= MIN_WORDS_TO_GRADE and m["fk"] > grade_cap:
                report["failures"].append(f"{key}/{kind}: grade {m['fk']} above {grade_cap}")
            for s in m["long_sentences"]:
                report["failures"].append(f"{key}/{kind}: a sentence over {sentence_cap} words: \"{s}...\"")

    page = score([text for section, kind, popup, text in t.runs if not popup], exempt, sentence_cap)
    report["page"] = page
    report["visible_words"] = visible_words
    report["back_words"] = back_words
    popup = report["sections"].get("popup", {}).get("all")
    report["popup_words"] = popup["words"] if popup else 0

    if as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{args[0]}")
        print(f"{'section':<14}{'kind':<6}{'words':>6}{'sent':>5}{'avg':>6}{'max':>5}{'FK raw':>8}{'FK':>6}{'ease':>6}{'3syl':>6}")
        for key in order:
            for kind in ("head", "sub", "body", "back"):
                m = report["sections"][key].get(kind)
                if m:
                    print(f"{key:<14}{kind:<6}{m['words']:>6}{m['sentences']:>5}{m['avg_sentence']:>6}{m['longest_sentence']:>5}{m['fk_raw']:>8}{m['fk']:>6}{m['fre']:>6.0f}{m['poly_share']:>6}")
        if page:
            print(f"{'PAGE':<14}{'all':<6}{page['words']:>6}{page['sentences']:>5}{page['avg_sentence']:>6}{page['longest_sentence']:>5}{page['fk_raw']:>8}{page['fk']:>6}{page['fre']:>6.0f}{page['poly_share']:>6}")
        print()
        print(f"Visible words outside the popup: {visible_words} (card backs {back_words}); popup {report['popup_words']}. Style Guide 6.16 budget: 400 visible, popup 130.")
        if report["failures"]:
            print(f"{len(report['failures'])} readability findings (grade cap {grade_cap}, sentence cap {sentence_cap}, sections under {MIN_WORDS_TO_GRADE} words not graded):")
            for f in report["failures"]:
                print("-", f)
        else:
            print(f"0 readability findings (grade cap {grade_cap}, sentence cap {sentence_cap}).")
    sys.exit(1 if strict and report["failures"] else 0)


if __name__ == "__main__":
    main()
