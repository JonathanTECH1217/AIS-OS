"""Loom B and A: his standing notes applied to a plan, so every cut follows them (Jonathan, 2026-10-07).

  python scripts/loom_ba_rules.py <plan.json> [<plan.json> ...] [--write]

Dry run by default: prints what would change. The rules, in his words:
  1. "It should only be the final adjustment that gets shown in the final cut, this goes for any change." A change he makes
     twice (the eyebrow, the headline, the button, the copy) shows its last version the first time he names it.
  2. "When I say review section, that's the review section. And when I say review banner, it's just that little five star
     ... right below the call to action." A step on the reviews band whose words are about a banner, stars, or the spot
     below the button shows the first screen (the banner under the button) instead.
  3. "When I say something about the booking form that goes into the calendar, there should be a visualization." His first
     mention of the calendar after the form shows the form's sent screen: the booking landing in the owner's calendar.
  4. The header (at the swap "it turned the header section white"): his first mention of the header, before the swap, lays
     the render's header over theirs (the 'header' step), so the header does not jump at the swap.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import social_content as scn  # noqa: E402

ONCE = ("headline", "eyebrow", "cta", "copy")


def words_near(words, at, before=2.0, after=6.0):
    return " ".join(w[2].lower() for w in words if at - before <= w[0] <= at + after)


def first_word_time(words, pattern, after=0.0, until=1e9):
    rx = re.compile(pattern, re.I)
    for i, w in enumerate(words):
        if after <= w[0] < until:
            pair = " ".join(x[2] for x in words[i:i + 3])
            if rx.search(w[2]) or rx.search(pair):
                return w[0]
    return None


def apply(plan):
    words = scn.transcript(plan["folder"])["words"]
    ch = plan["changes"]
    notes = []
    act_two = min([float(c["at"]) for c in ch if c["kind"] in ("section", "form")] or [1e9])

    # 1. final version only
    for kind in ONCE:
        same = {}
        for i, c in enumerate(ch):
            if c["kind"] == kind and float(c["at"]) < act_two:
                same.setdefault(c.get("selector") or "", []).append(i)
        for sel, idx in same.items():
            if len(idx) < 2:
                continue
            first, last = ch[idx[0]], ch[idx[-1]]
            merged = dict(last, at=first["at"])
            for i in reversed(idx[1:]):
                ch.pop(i)
            ch[idx[0]] = merged
            notes.append(f"final only: {kind} at {scn.mmss(float(first['at']))} now shows its last version ({len(idx)} steps became one)")

    # 2. review banner vs review section
    for c in ch:
        if c["kind"] == "section" and c.get("band") == "reviews":
            near = words_near(words, float(c["at"]))
            if re.search(r"\bbanner\b|\bstars?\b|below (the|that) (call to action|button)|under (the|that) (call to action|button)|right below the call", near):
                c["band"] = "hero"
                notes.append(f"review banner: the step at {scn.mmss(float(c['at']))} shows the banner under the button, not the reviews band")

    # 3. the calendar
    forms = [float(c["at"]) for c in ch if c["kind"] == "form"]
    if forms and not any(c["kind"] == "form" and str(c.get("step")) == "sent" for c in ch):
        t = first_word_time(words, r"\bcalendar\b", after=min(forms))
        if t is not None and t <= max(float(c["at"]) for c in ch) + 600:
            ch.append({"at": round(t, 2), "kind": "form", "step": "sent"})
            notes.append(f"calendar: the booking lands in the owner's calendar at {scn.mmss(t)}")

    # 4. the header
    if plan.get("render") and not any(c["kind"] == "header" for c in ch):
        t = first_word_time(words, r"\bheader\b", after=float(plan.get("start_at", 0)), until=act_two)
        if t is None:
            hs = [float(c["at"]) for c in ch if c["kind"] == "css" and re.search(r"header|masthead|navbar", c.get("selector") or "", re.I) and float(c["at"]) < act_two]
            t = min(hs) if hs else None
        if t is not None:
            ch.append({"at": round(t, 2), "kind": "header"})
            notes.append(f"header: the render's header takes their header's place at {scn.mmss(t)}")
    ch.sort(key=lambda c: float(c["at"]))
    return notes


def main():
    write = "--write" in sys.argv
    for path in [a for a in sys.argv[1:] if not a.startswith("--")]:
        p = Path(path)
        plan = json.loads(p.read_text(encoding="utf-8"))
        notes = apply(plan)
        print(f"== {p.name}: " + ("nothing to change" if not notes else ""))
        for n in notes:
            print("   " + n)
        if write and notes:
            p.write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
