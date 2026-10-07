"""Part: words. Compares the splitter's output on the real Blurry LRC (words-t1.out.txt, LINE| rows) with sung syllables.
Expected splits are written the way the splitter prints them: pieces of one word joined with '-', words with spaces.
"""
import os
import re
import sys

SP = os.path.dirname(os.path.abspath(__file__))
EXPECT = {
    "Everything's so blurry and everyone's so fake": "Ev-ery-thing's so blur-ry and ev-ery-one's so fake",
    "And everybody's empty and everything is so messed up": "And ev-ery-bod-y's emp-ty and ev-ery-thing is so messed up",
    "Preoccupied without you, I cannot live at all": "Pre-oc-cu-pied with-out you, I can-not live at all",
    "My whole world surrounds you, I stumble and I crawl": "My whole world sur-rounds you, I stum-ble and I crawl",
    "You could be my someone, you could be my scene": "You could be my some-one, you could be my scene",
    "You know that I'll protect you from all of the obscene": "You know that I'll pro-tect you from all of the ob-scene",
    "I wonder what you're doing, imagine where you are": "I won-der what you're do-ing, i-ma-gine where you are",
    "There's oceans in between us, but that's not very far": "There's o-ceans in be-tween us, but that's not ve-ry far",
    "Can you take it all away?": "Can you take it all a-way?",
    "Well, you shoved it in my face": "Well, you shoved it in my face",
    "This pain you gave to me": "This pain you gave to me",
    "Everyone is changing, there's no one left that's real": "Ev-ery-one is chang-ing, there's no one left that's real",
    "So make up your own ending and let me know just how you feel": "So make up your own end-ing and let me know just how you feel",
    "'Cause I am lost without you, I cannot live at all": "'Cause I am lost with-out you, I can-not live at all",
    "My whole world surrounds you, I stumble then I crawl": "My whole world sur-rounds you, I stum-ble then I crawl",
    "You know that I will save you from all of the unclean": "You know that I will save you from all of the un-clean",
    "I wonder what you're doing, I wonder where you are": "I won-der what you're do-ing, I won-der where you are",
    "Nobo-, nobody told me what you thought": "No-bo, no-bod-y told me what you thought",
    "Nobody told me what to say": "No-bod-y told me what to say",
    "Everyone showed you where to turn": "Ev-ery-one showed you where to turn",
    "Told you when to run away": "Told you when to run a-way",
    "Nobody told you where to hide": "No-bod-y told you where to hide",
    "Nobody told you what to say": "No-bod-y told you what to say",
    "Showed you when to run away": "Showed you when to run a-way",
    "This pain you gave to me, no": "This pain you gave to me, no",
    "Can you take it all, take it all away?": "Can you take it all, take it all a-way?",
}
# words a singer squeezes (ev-ry-thing): the full dictionary count is also acceptable, flagged as elision
ELIDE = {"everything's": 4, "everything": 4, "everyone's": 4, "everyone": 4, "everybody's": 5, "every": 3}

rows = []
for ln in open(os.path.join(SP, "words-t1.out.txt"), encoding="utf-8-sig"):
    ln = ln.rstrip("\n")
    if not ln.startswith("LINE|"):
        continue
    _, idx, stamp, text, count, split = ln.split("|", 5)
    rows.append((int(idx), stamp, text, int(count), split))

print(f"{len(rows)} LRC entries")
tot_got = tot_sung = 0
bad_words = {}
elided = {}
lines_off = 0
for idx, stamp, text, count, split in rows:
    if not text:
        print(f"{idx:2d} {stamp} (blank) got {count}")
        continue
    exp = EXPECT[text]
    got_words = split.split(" ")
    exp_words = exp.split(" ")
    sung = sum(len(w.split("-")) for w in exp_words)
    tot_got += count
    tot_sung += sung
    issues = []
    if len(got_words) != len(exp_words):
        issues.append(f"WORDCOUNT got {len(got_words)} words, expected {len(exp_words)}")
    for g, e in zip(got_words, exp_words):
        key = re.sub(r"[^a-z']", "", g.lower())
        gp, ep = g.split("-"), e.split("-")
        if len(gp) != len(ep):
            if key in ELIDE and len(gp) == ELIDE[key]:
                elided[key] = g
                issues.append(f"elision {g} ({len(gp)} for {len(ep)} sung)")
            else:
                kind = "too many" if len(gp) > len(ep) else "too few"
                issues.append(f"{kind}: {g} ({len(gp)} for {len(ep)}, want {e})")
                bad_words[key] = (g, e, kind)
        elif gp != ep and len(gp) > 1:
            issues.append(f"wrong break: {g} (want {e})")
            bad_words[key] = (g, e, "wrong break")
    flag = "" if count == sung else " <-- OFF"
    if count != sung:
        lines_off += 1
    print(f"{idx:2d} {stamp} got {count:2d} sung {sung:2d}{flag}  {split}")
    for i in issues:
        print(f"      {i}")
print()
print(f"total notes {tot_got} vs sung {tot_sung}; lines off {lines_off} of {len([r for r in rows if r[2]])}")
print("wrong words (unique):")
for k, (g, e, kind) in sorted(bad_words.items()):
    print(f"  {kind:10s} {g:16s} want {e}")
print("elided-only (dictionary count, singer squeezes):", ", ".join(sorted(elided.values())))
