"""Lint the responsive search ads in a campaign brief (projects/google-ads/campaigns/*.md) before they go in the account.

Usage:
  python scripts/ads_lint.py <brief.md or campaign.json> [--term "google ads for av integrators"]
  python scripts/ads_lint.py --text "A headline or a description to check"

What it reads from a brief: any markdown table with a "Headline" column (and an optional "Pin" column), any table with a
"Description" column, a line starting "Descriptions:" with the descriptions in double quotes separated by " / ", and
"paths `One` / `Two`". Several ad groups in one brief are fine; each table is checked as it comes.

Hard checks (exit 1 on any): headline over 30 characters, description over 90, path over 15; em or en dash; a tier
price ($2,500 or $4,500); "setup fee"; a callback or answer clock ("within 5 minutes", "same day reply"); a tenure claim
("N years", "since 20XX", "decade"); PHA; "guarantee"; "free"; the pilot's terms ("pilot", "60 days", "matched");
"#1 agency"; more than 15 headlines or 4 descriptions, or fewer than 3 headlines or 2 descriptions; a duplicate headline.
Soft report: the Flesch-Kincaid grade of each description (sixth grade or under, Jonathan 2026-10-01; was 6 to 8), and
with --term how many headlines carry the ad group's term. New ads also follow the slot rule (README, "Writing a new
ad"): slot 1 the callout to the person, slot 2 the outcome they want, slot 3 the call to action.
"""
import json
import re
import sys
from pathlib import Path

H_MAX, D_MAX, P_MAX = 30, 90, 15
RULES = [
    (r"[—–]", "em or en dash (Copy 2)"),
    (r"\$\s?(2,?500|4,?500)\b", "tier price (Copy 4)"),
    (r"\bset[\s-]?up fee\b", "setup fee (Style Guide 6.7)"),
    (r"\b(calls?|call back|callback|respond|responds|response|repl(?:y|ies)|texts?|answer(?:s|ed)?)\b[^.]{0,40}?\b(within|inside|under|in)\s+(a\s+|an\s+)?(\d+|one|two|three|five|ten|fifteen|thirty|sixty)\s*(seconds?|minutes?|mins?|hours?)\b", "callback clock (Copy 9)"),
    (r"\b(\d+|one|two|five|ten|fifteen|thirty|sixty)[\s-]*(second|minute|hour)\s+(callback|call back|response|reply|text back)\b", "callback clock (Copy 9)"),
    (r"\bsame[\s-]day\b", "callback clock (Copy 9)"),
    (r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+years?\b|\bsince\s+(19|20)\d\d\b|\bdecades?\b", "tenure claim (Copy 3)"),
    (r"\bPHA\b|pha\.systems|Performance Home Automation", "names the integrator (Copy 5)"),
    (r"\bguarantee[ds]?\b", "guarantee (the agreement gives none)"),
    (r"\bfree\b", "free (invites tire kickers; the page says 'You leave with the audit')"),
    (r"\bpilot\b|\b60[\s-]?days?\b|\bsixty[\s-]days?\b|\bmatch(ed)?\b", "the pilot's terms (the page carries none)"),
    (r"#\s?1\s+(agency|firm|company)", "#1 agency (superlative without proof on the page)"),
]


def check_text(text):
    return [label for pat, label in RULES if re.search(pat, text, re.I)]


def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]+", w)))


def grade(text):
    guarded = re.sub(r"(?<=\w)\.(?=\w)", "", text)
    sents = [s for s in re.split(r"(?<=[.!?])\s+", guarded) if s.strip()]
    words = re.findall(r"[A-Za-z0-9$']+", guarded)
    if not words or not sents:
        return None
    syl = sum(1 if (i > 0 and w[:1].isupper()) else syllables(w) for i, w in enumerate(words))
    return round(0.39 * len(words) / len(sents) + 11.8 * syl / len(words) - 15.59, 1)


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse(md):
    """Yield (kind, text, pin) in document order. kind is headline, description, or path."""
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            header = [h.lower() for h in split_row(line)]
            col = next((n for n, h in enumerate(header) if h in ("headline", "headlines")), None)
            dcol = next((n for n, h in enumerate(header) if h in ("description", "descriptions")), None)
            pcol = next((n for n, h in enumerate(header) if h == "pin"), None)
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = split_row(lines[i])
                if col is not None and col < len(cells) and cells[col]:
                    yield "headline", cells[col], (cells[pcol] if pcol is not None and pcol < len(cells) else "")
                if dcol is not None and dcol < len(cells) and cells[dcol]:
                    yield "description", cells[dcol], ""
                i += 1
            continue
        if line.strip().lower().startswith("descriptions:"):
            for d in re.findall(r'"([^"]+)"', line):
                yield "description", d, ""
        for m in re.finditer(r"paths?\s+`([^`]+)`\s*/\s*`([^`]+)`", line, re.I):
            yield "path", m.group(1), ""
            yield "path", m.group(2), ""
        i += 1


def parse_json(text):
    """The ad in a campaign file (projects/google-ads/campaigns/NN-<service>.json), same tuples as parse()."""
    ad = json.loads(text).get("ad") or {}
    for h in ad.get("headlines", []):
        yield "headline", h["text"], str(h.get("pin") or "")
    for d in ad.get("descriptions", []):
        yield "description", d, ""
    for p in (ad.get("path1"), ad.get("path2")):
        if p:
            yield "path", p, ""


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "--text":
        text = " ".join(args[1:])
        flags = check_text(text)
        print(f"{len(text)} chars, grade {grade(text)}; " + ("; ".join(flags) if flags else "clean"))
        sys.exit(1 if flags else 0)
    path = Path(args[0])
    term = args[args.index("--term") + 1].lower() if "--term" in args and args.index("--term") + 1 < len(args) else None
    text = path.read_text(encoding="utf-8")
    items = list(parse_json(text) if path.suffix == ".json" else parse(text))
    heads = [(t, p) for k, t, p in items if k == "headline"]
    descs = [t for k, t, p in items if k == "description"]
    paths = [t for k, t, p in items if k == "path"]
    failures = 0
    print(path)
    for n, (t, pin) in enumerate(heads, 1):
        flags = check_text(t)
        if len(t) > H_MAX:
            flags.append(f"over {H_MAX} characters")
        failures += bool(flags)
        print(f"  H{n:<2} {len(t):>3}  {'pin ' + pin if pin else '     '}  {t}" + ("  <- " + "; ".join(flags) if flags else ""))
    for n, t in enumerate(descs, 1):
        flags = check_text(t)
        if len(t) > D_MAX:
            flags.append(f"over {D_MAX} characters")
        failures += bool(flags)
        g = grade(t)
        note = "" if g is None or g <= 6 else f"  (grade {g}, aim sixth grade or under)"
        print(f"  D{n:<2} {len(t):>3}  grade {g}  {t}" + ("  <- " + "; ".join(flags) if flags else "") + note)
    for n, t in enumerate(paths, 1):
        flags = check_text(t)
        if len(t) > P_MAX:
            flags.append(f"over {P_MAX} characters")
        failures += bool(flags)
        print(f"  P{n:<2} {len(t):>3}  {t}" + ("  <- " + "; ".join(flags) if flags else ""))
    lower = [t.lower() for t, _ in heads]
    dups = sorted({t for t in lower if lower.count(t) > 1})
    if dups:
        failures += 1
        print(f"  duplicate headlines: {dups}")
    if heads and not 3 <= len(heads) <= 15:
        failures += 1
        print(f"  {len(heads)} headlines (an RSA takes 3 to 15)")
    if descs and not 2 <= len(descs) <= 4:
        failures += 1
        print(f"  {len(descs)} descriptions (an RSA takes 2 to 4)")
    if term:
        full = sum(1 for t in lower if term in t)
        head = " ".join(term.split()[:2])
        near = sum(1 for t in lower if head in t)
        print(f"  term \"{term}\": in {full} headlines as typed, \"{head}\" in {near}")
    print(f"{failures} failures; {len(heads)} headlines, {len(descs)} descriptions, {len(paths)} paths")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
