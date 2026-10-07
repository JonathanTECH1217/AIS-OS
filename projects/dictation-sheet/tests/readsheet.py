import json, re, sys
p = r"C:\Users\sumre\Documents\Puddle of Mud - Blurry.json"
d = json.load(open(p, encoding="utf-8"))
s = d.get("sheet", d)
print("keys:", list(s.keys())[:20])
print("title:", s.get("title"), "| bpm:", s.get("bpm"), "| time:", s.get("time"), "| filled:", s.get("filled"), "| updatedAt:", s.get("updatedAt"))
a = s.get("audio") or {}
print("audio:", {k: (v if k != "beats" else ("%d beats" % len(v) if v else None)) for k, v in a.items()})
print("spotify:", s.get("spotify"))
beats = a.get("beats") or []
if beats: print("beats[0:6]:", beats[:6], "last:", beats[-1], "median gap:", sorted([beats[i+1]-beats[i] for i in range(len(beats)-1)])[len(beats)//2])
LEN = {"w": 64, "h": 32, "q": 16, "8": 8, "16": 4}
def slots(y): return max(1, round(LEN.get(y.get("len"), 16) / 4 * (1.5 if y.get("dot") else 1)) + int(y.get("xs") or 0))
tp = s.get("time", "4/4").split("/"); spb = round(int(tp[0]) * 16 / int(tp[1])); spbeat = 2 if int(tp[1]) == 8 else 4
def song_of_slot(g):
    if len(beats) > 1:
        b = g / spbeat; i = int(b // 1); last = len(beats) - 1
        if i < 0: return beats[0] + b * (beats[1] - beats[0])
        if i >= last: return beats[last] + (b - last) * (beats[last] - beats[last-1])
        return beats[i] + (b - i) * (beats[i+1] - beats[i])
    return (a.get("offsetSec") or 0) + g * 60.0 / float(s.get("bpm") or 100) / spbeat
lrc = json.load(open("blurry.lrc.json", encoding="utf-8"))["synced"]
stamps = []
for ln in lrc.splitlines():
    m = re.match(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)", ln)
    if m and m.group(3).strip(): stamps.append((int(m.group(1))*60 + float(m.group(2)), m.group(3).strip()))
lines = [l for l in s["lines"] if l.get("kind") == "line"]
print("lines:", len(lines), "| lyric stamps with words:", len(stamps))
ord_ = 0
si = 0
def norm(t): return re.sub(r"[^a-z0-9 ]", "", t.lower())
def linetext(l):
    ys = sorted(l["syllables"], key=lambda y: y["pos"]); t = ""
    for y in ys: t += (y.get("text") or "") + ("" if y.get("hy") else " ")
    return t.strip()
errs = []
for n, l in enumerate(lines):
    ys = sorted(l["syllables"], key=lambda y: y["pos"])
    if not ys: ord_ += l.get("bars", 1); continue
    first = ys[0]; g0 = ord_ * spb + first["pos"]; t0 = song_of_slot(g0)
    txt = linetext(l); words = norm(txt).split()
    # the lyric stamp whose first three words match
    st = None
    for k in range(si, len(stamps)):
        if norm(stamps[k][1]).split()[:3] == words[:3]: st = stamps[k]; si = k + 1; break
    if st is None:
        for k in range(len(stamps)):
            if norm(stamps[k][1]).split()[:3] == words[:3]: st = stamps[k]; break
    e = (t0 - st[0]) if st else None
    if e is not None: errs.append(e)
    # the last syllable end
    last = ys[-1]; g1 = ord_ * spb + last["pos"] + slots(last); t1 = song_of_slot(g1)
    lens = " ".join("%s@%d+%d" % (y.get("text"), y["pos"], slots(y)) for y in ys[:8])
    print("line %2d bar %3d bars %2d  %6.2fs..%6.2fs  stamp %s  first-vs-stamp %s | %s%s" % (n+1, ord_+1, l.get("bars",1), t0, t1, ("%6.2f" % st[0]) if st else "  none", ("%+.2f" % e) if e is not None else "  n/a", lens, " ..." if len(ys) > 8 else ""))
    ord_ += l.get("bars", 1)
if errs:
    import statistics
    print("first syllable minus lyric stamp: mean %+.2f s, median %+.2f, min %+.2f, max %+.2f, n=%d" % (statistics.mean(errs), statistics.median(errs), min(errs), max(errs), len(errs)))
