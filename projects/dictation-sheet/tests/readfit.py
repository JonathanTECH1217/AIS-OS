import json, re, statistics
res = json.load(open("real-result.json", encoding="utf-8"))
lrc = json.load(open("blurry.lrc.json", encoding="utf-8"))["synced"]
stamps = []
for ln in lrc.splitlines():
    m = re.match(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)", ln)
    if m and re.search(r"[A-Za-z0-9]", m.group(3)): stamps.append((int(m.group(1))*60 + float(m.group(2)), m.group(3).strip()))
lines = res["lines"]
print("fit lines", len(lines), "| lyric stamps", len(stamps), "| words", len(res["words"]), "| tempo", res.get("tempo"), "beats", len(res.get("beats", [])), "phase", res.get("phase"), res.get("phaseSure"))
b = res.get("beats", [])
if len(b) > 2:
    gaps = [b[i+1]-b[i] for i in range(len(b)-1)]
    gaps_s = sorted(gaps)
    print("beat gaps: median %.3f, min %.3f, max %.3f, 10th %.3f, 90th %.3f; beats span %.1f..%.1f s" % (statistics.median(gaps), gaps_s[0], gaps_s[-1], gaps_s[len(gaps)//10], gaps_s[9*len(gaps)//10], b[0], b[-1]))
    odd = [(round(b[i],2), round(g,3)) for i, g in enumerate(gaps) if abs(g - statistics.median(gaps)) > 0.12]
    print("beats whose gap is off by more than 0.12 s:", len(odd), odd[:12])
diffs = []
rows = []
for L in lines:
    st = stamps[L["index"]] if L["index"] < len(stamps) else None
    if st: diffs.append(L["start"] - st[0])
    rows.append((L["index"], L["start"], L["end"], st[0] if st else None, st[1][:28] if st else "", L["text"][:28]))
med = statistics.median(diffs)
print("fit start minus lyric stamp: median %+.2f s (the capture's offset), spread: min %+.2f max %+.2f" % (med, min(diffs), max(diffs)))
off = [d - med for d in diffs]
ok1 = sum(1 for d in off if abs(d) <= 0.5); ok2 = sum(1 for d in off if abs(d) <= 1.0)
print("lines within 0.5 s of their stamp (after the offset): %d of %d; within 1 s: %d" % (ok1, len(off), ok2))
for r in rows:
    d = (r[1] - r[3] - med) if r[3] is not None else None
    print("line %2d  fit %6.2f..%6.2f  stamp %6.2f  off %s  %s | %s" % (r[0]+1, r[1], r[2], r[3] if r[3] is not None else -1, ("%+6.2f" % d) if d is not None else "  n/a", r[4], "" if r[4] == r[5] else "sheet: " + r[5]))
scores = [s.get("score", 1) for w in res["words"] for s in w["syllables"]]
print("syllable fit scores: median %.2f, under 0.5: %d of %d" % (statistics.median(scores), sum(1 for s in scores if s < 0.5), len(scores)))
