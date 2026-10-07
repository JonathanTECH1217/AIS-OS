"""Check the negative keyword lists against each campaign's keywords before they go in the account.

Usage:
  python scripts/ads_negative_check.py [--campaign 03] [--top 15] [--quiet]

Reads each campaign's keywords (projects/google-ads/campaigns/NN-<service>.json when it exists, else
projects/google-ads/keywords/picks.json), the account-level lists in projects/google-ads/negatives/shared-lists.md,
and each campaign's own list in negatives/<service>.md.

List format (both files): a "## Name" heading starts a list; an optional "Applies to:" line ("all", "all except 06",
"01, 02"; shared lists only); the first fenced block under the heading holds the terms, one per line. The lists named
"Never negative" and "Watch list" are read for the checks, never pasted.

Google's negative rules. A negative never stretches to plurals, misspellings, or near words:
  plain words     blocks a search that has every word, in any order
  "quoted words"  blocks a search that has the words side by side, in that order
  [bracketed]     blocks only that exact search

Hard checks (exit 1): a negative blocks one of the campaign's keywords; a one-word negative is on the never-negative
list, or a negative is "near me" alone; a malformed line (over 80 characters, over 10 words, a character Google
refuses, a stray quote or bracket); the same term twice in one list.
Soft report: bench keywords a negative blocks; and per campaign, the negatives that block the most buy rows of the
long list (keywords/<service>.csv), so a negative that is too wide stands out.
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADS = ROOT / "projects" / "google-ads"
PICKS = ADS / "keywords" / "picks.json"
SHARED = ADS / "negatives" / "shared-lists.md"
ALLOWED = re.compile(r"^[a-z0-9 &'.+#-]+$")


def words(text):
    t = text.lower().replace("’", "'")
    return [w.strip(".,") for w in t.split() if w.strip(".,")]


def parse_term(line):
    s = line.strip()
    if s.startswith("[") and s.endswith("]"):
        kind, body = "exact", s[1:-1]
    elif s.startswith('"') and s.endswith('"') and len(s) > 1:
        kind, body = "phrase", s[1:-1]
    else:
        kind, body = "broad", s
    problems = []
    if any(c in body for c in '[]"'):
        problems.append("stray quote or bracket")
    if len(body) > 80:
        problems.append("over 80 characters")
    if len(body.split()) > 10:
        problems.append("over 10 words")
    if not ALLOWED.match(body.lower().replace("’", "'")):
        problems.append("a character Google refuses")
    return {"kind": kind, "words": words(body), "raw": s, "problems": problems}


def parse_lists(path):
    """Returns the lists in a negatives markdown file, in order."""
    lists, cur, in_block, got_block = [], None, False, False
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("## ") and not in_block:
            name = line[3:].strip()
            low = name.lower()
            cur = {"name": name, "applies": None, "except": set(), "terms": [], "file": path.name,
                   "kind": "never" if low.startswith("never negative") else "watch" if low.startswith("watch") else "neg"}
            lists.append(cur)
            got_block = False
            continue
        if cur is None:
            continue
        if not in_block and line.lower().startswith("applies to:"):
            spec = line.split(":", 1)[1].strip().lower()
            if spec.startswith("all"):
                cur["except"] = set(re.findall(r"\d\d", spec))
            else:
                cur["applies"] = set(re.findall(r"\d\d", spec))
            continue
        if line.strip().startswith("```"):
            if in_block:
                in_block, got_block = False, True
            elif not got_block:
                in_block = True
            continue
        if in_block and line.strip() and not line.strip().startswith("#"):
            t = parse_term(line)
            t["line"] = n
            cur["terms"].append(t)
    return lists


def applies(lst, nn):
    if lst["applies"] is not None:
        return nn in lst["applies"]
    return nn not in lst["except"]


def blocks(term, query_words):
    tw, q = term["words"], query_words
    if term["kind"] == "exact":
        return tw == q
    if term["kind"] == "phrase":
        k = len(tw)
        return any(q[i:i + k] == tw for i in range(len(q) - k + 1))
    return set(tw) <= set(q)


def campaigns():
    data = json.loads(PICKS.read_text(encoding="utf-8"))["campaigns"]
    out = []
    for c in data:
        f = ADS / "campaigns" / f"{c['nn']}-{c['service']}.json"
        if f.exists():
            cj = json.loads(f.read_text(encoding="utf-8"))
            c = {**c, "picks": [k["text"] for k in cj["keywords"]], "bench": cj.get("bench", c.get("bench", []))}
        out.append(c)
    return out


def long_list(service):
    path = ADS / "keywords" / f"{service}.csv"
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return [r["keyword"] for r in csv.DictReader(f)
                if r.get("status") in ("candidate", "approved") and r.get("intent") == "buy"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--campaign", default="", help="one campaign number, e.g. 03")
    ap.add_argument("--top", type=int, default=15, help="how many of the widest negatives to list per campaign")
    ap.add_argument("--quiet", action="store_true", help="hard checks only")
    a = ap.parse_args()

    shared = parse_lists(SHARED)
    never = {w for lst in shared if lst["kind"] == "never" for t in lst["terms"] for w in [" ".join(t["words"])]}
    errors, notes = [], []

    def lint(lists):
        for lst in lists:
            if lst["kind"] != "neg":
                continue
            seen = set()
            for t in lst["terms"]:
                where = f"{lst['file']}:{t['line']} ({lst['name']})"
                for p in t["problems"]:
                    errors.append(f"{where}: {t['raw']}: {p}")
                key = (t["kind"], tuple(t["words"]))
                if key in seen:
                    errors.append(f"{where}: {t['raw']}: listed twice")
                seen.add(key)
                text = " ".join(t["words"])
                if (len(t["words"]) == 1 and t["kind"] != "exact" and text in never) or text == "near me":
                    errors.append(f"{where}: {t['raw']}: on the never-negative list (it would block good searches)")

    lint(shared)
    camps = [c for c in campaigns() if not a.campaign or c["nn"] == a.campaign.zfill(2)]
    if not camps:
        sys.exit("No campaign matched --campaign.")
    total_terms = 0
    for c in camps:
        own_path = ADS / "negatives" / f"{c['service']}.md"
        own = parse_lists(own_path) if own_path.exists() else []
        if not own_path.exists():
            notes.append(f"{c['nn']} {c['service']}: no campaign list yet ({own_path.relative_to(ROOT)})")
        lint(own)
        active = [(lst, t) for lst in shared if lst["kind"] == "neg" and applies(lst, c["nn"]) for t in lst["terms"]]
        active += [(lst, t) for lst in own if lst["kind"] == "neg" for t in lst["terms"]]
        total_terms += len(active)
        for kw in c["picks"]:
            q = words(kw)
            for lst, t in active:
                if blocks(t, q):
                    errors.append(f"{c['nn']} {c['service']}: {t['raw']} ({lst['file']}, {lst['name']}) blocks the keyword "
                                  f"\"{kw}\"")
        for kw in c.get("bench", []):
            q = words(kw)
            for lst, t in active:
                if blocks(t, q):
                    notes.append(f"{c['nn']} {c['service']}: {t['raw']} ({lst['name']}) blocks the bench keyword \"{kw}\"")
        if a.quiet:
            continue
        rows = long_list(c["service"])
        counts = []
        for lst, t in active:
            hit = [r for r in rows if blocks(t, words(r))]
            if hit:
                counts.append((len(hit), t["raw"], lst["name"], hit[:2]))
        counts.sort(key=lambda x: -x[0])
        print(f"\n{c['nn']} {c['service']}: {len(c['picks'])} keywords, {len(active)} negatives "
              f"({len(own_path.read_text(encoding='utf-8').splitlines()) if own_path.exists() else 0} lines in its own file). "
              f"Widest against {len(rows)} buy rows of the long list:")
        for n, raw, name, ex in counts[:a.top]:
            print(f"  {n:4}  {raw}  ({name})  e.g. {'; '.join(ex)}")
        if not counts:
            print("  none")

    for n in notes:
        print(f"note: {n}")
    if errors:
        print(f"\n{len(errors)} problem(s):")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    print(f"\nOK: no negative blocks a keyword in {len(camps)} campaign(s); {total_terms} negatives checked.")


if __name__ == "__main__":
    main()
