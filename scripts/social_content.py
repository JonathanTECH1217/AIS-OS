"""Social content: the hands under the /social-content skill (2026-10-05).

The clone is the editor: it reads the words and decides what stays, and writes that down as a plan. This script does
what an editor's hands do with the plan, on this laptop, with the tools already here (Parakeet for the words through
scripts/studio_transcribe.py, ffmpeg for the cut). Nothing is uploaded and nothing is posted.

  python scripts/social_content.py fetch <loom share link> [--name momentum-review]
        the Loom's file into media/looms/<id>-<name>/ and its word-timed transcript. Refuses a Loom with no sound.
  python scripts/social_content.py words <folder> [--from 0 --to 60]
        the transcript by spoken stretch, with times, for the clone to read
  python scripts/social_content.py cut <plan.json>
        one video from one or more recordings with the plan's cuts, every "uh" and "um", and every long pause out.
        Writes the video and <name>.cuts.md: each cut, its reason, and the words that went.
  python scripts/social_content.py before-after <plan.json>
        a 1080x1920 short: the old page in the top panel, the new one below, the one being talked about playing and
        the other dimmed, captions between them in Monarc Studio's caption style
  python scripts/social_content.py long-form <plan.json>
        the cut, then the level set to -14 LUFS, a .srt caption file, and <name>.youtube.json beside it: the long
        version of a lead review for YouTube (2026-10-05). No burned captions, no title card: nothing he did not say.
  python scripts/social_content.py review-short <plan.json>
        a 1080x1920 short from one recording: the page in one tall panel, captions under it, 30 to 60 seconds, one
        idea. For Instagram and Facebook; he posts it himself (Jonathan, 2026-10-05: "I dont need metas API").
  python scripts/social_content.py check <video>
        the finisher's look before Jonathan sees it: length, picture and sound present, black frames, dead air, level

Plans are kept in projects/social-content/plans/. Their fields are listed in .claude/skills/social-content/SKILL.md.
The crops below fit his Loom recordings (1920x1080, the browser full width, his face bubble at the lower left).
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_common as sc  # noqa: E402
import studio_captions as caps_style  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LOOMS = ROOT / "media" / "looms"
FONT = sc.STUDIO_DIR / "fonts" / "Montserrat-Black.ttf"
FILLER = {"uh", "um", "erm", "er", "ah", "uhm"}
PAGE_CROP = "1420:630:240:110"    # the page only: no browser bar, no task bar, no face bubble
CLOSE_CROP = "1280:568:320:282"   # closer, for a form or a popup in the middle of the page
TALL_CROP = "1420:650:240:110"    # the whole page width, stopping above the face bubble (its top sits near y 780)
PANEL = "1080:480"
TALL_PANEL = "1080:494"
TOP_Y, BOT_Y, CAP_Y = 200, 1240, 960
ONE_Y, ONE_CAP_Y = 420, 1180      # the one-panel short sits in the phone's safe band (about 250 to 1620 of 1920)
SHORT_MIN, SHORT_MAX = 25.0, 65.0  # a review short is 30 to 60 seconds; outside this band the script refuses
LOUD = "loudnorm=I=-14:TP=-1.5:LRA=11"
BOOK_LINK = "https://monarcbuild.com/av_marketing/"
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000"]


def ff(args, cwd=None, check=True):
    p = subprocess.run([sc.ffmpeg_exe(), "-hide_banner", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and p.returncode:
        sys.exit(f"ffmpeg failed: {p.stderr[-700:]}")
    return p


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def folder(raw):
    p = Path(raw)
    return p if p.is_absolute() else ROOT / p


def transcript(fold):
    f = folder(fold) / "transcript.json"
    if not f.exists():
        sys.exit(f"No transcript in {fold}. Run: python scripts/social_content.py fetch <loom link>")
    return json.loads(f.read_text(encoding="utf-8"))


def mmss(t):
    t = round(float(t), 1)          # round first, so 179.98 reads 3:00.0, never 2:60.0
    return f"{int(t // 60)}:{t % 60:04.1f}"


# ---------------------------------------------------------------- fetch

def cmd_fetch(a):
    m = re.search(r"loom\.com/share/([0-9a-f]{32})", a.link)
    if not m:
        sys.exit("That is not a Loom share link (loom.com/share/...).")
    lid = m.group(1)
    share = f"https://www.loom.com/share/{lid}"
    meta = requests.get("https://www.loom.com/v1/oembed", params={"url": share}, timeout=20).json()
    page = requests.get(share, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).text
    state = (re.search(r'"transcription_status"\s*:\s*"([a-z_]+)"', page) or [None, ""])[1]
    if state == "no_audio":
        sys.exit(f"This Loom has no sound (Loom marks it no_audio): {meta.get('title')}. Nothing fetched. Record it again with the mic on.")
    out = LOOMS / f"{lid[:8]}-{re.sub(r'[^a-z0-9]+', '-', (a.name or 'loom').lower()).strip('-')}"
    out.mkdir(parents=True, exist_ok=True)
    src = out / "source.mp4"
    head = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json", "Accept": "application/json"}
    url = requests.post(f"https://www.loom.com/api/campaigns/sessions/{lid}/transcoded-url", headers=head, json={}, timeout=30).json().get("url")
    if not url:
        sys.exit("Loom did not hand over the file. Is the link public?")
    with requests.get(url, stream=True, timeout=600) as r, open(src, "wb") as fh:
        for chunk in r.iter_content(1 << 20):
            fh.write(chunk)
    if "Audio:" not in ff(["-i", str(src)], check=False).stderr:
        sys.exit(f"The file has no sound track: {src}. Record it again with the mic on.")
    subprocess.run([sys.executable, str(Path(__file__).with_name("studio_transcribe.py")), str(src), str(out), "--asset", f"loom_{lid[:8]}"],
                   check=True, stdout=subprocess.DEVNULL)
    (out / "loom.json").write_text(json.dumps({"id": lid, "url": share, "title": meta.get("title"), "seconds": meta.get("duration"),
                                               "fetched": date.today().isoformat()}, indent=1), encoding="utf-8")
    d = transcript(out)
    print(f"{out.relative_to(ROOT).as_posix()} | {meta.get('title')} | {mmss(d['duration'])} | {len(d['words'])} words")


def cmd_words(a):
    d = transcript(a.folder)
    w = d["words"]
    for s in d["segments"]:
        if s[1] >= a.start and s[0] <= a.end:
            print(f"[{s[0]:6.1f}-{s[1]:6.1f}] " + " ".join(x[2] for x in w[s[2]:s[3] + 1]))


# ---------------------------------------------------------------- the tight cut

def keep_ranges(words, cuts, keep_whole, pause, lead=0.10, tail=0.18):
    """Every word outside a cut that is not a filler, joined into runs across pauses up to `pause`; each run keeps a
    little air; a keep_whole stretch stays as it is (a form being filled in, a scroll)."""
    # a word belongs to a cut when its middle falls inside it, so a cut time rounded a hair after a word starts still takes
    # the word (two Loom B and A builds found "That's just" left in, 2026-10-06)
    mid = lambda w: (w[0] + w[1]) / 2
    kept = [w for w in words if not any(c[0] <= mid(w) < c[1] for c in cuts)
            and (norm(w[2]) not in FILLER or any(k[0] <= w[0] < k[1] for k in keep_whole))]
    runs = []
    for w in kept:
        if runs and w[0] - runs[-1][1] <= pause:
            runs[-1][1] = max(runs[-1][1], w[1])
        else:
            runs.append([w[0], w[1]])
    def air(s, e):  # the air around a run never reaches into a cut (a cut word's first sound would come back)
        s2, e2 = max(0.0, s - lead), e + tail
        for c in cuts:
            if e <= c[0] < e2:
                e2 = c[0]
            if s2 < c[1] <= s:
                s2 = c[1]
        return [s2, e2]

    ranges = sorted([air(s, e) for s, e in runs] + [[k[0], k[1]] for k in keep_whole])
    out = []
    for r in ranges:
        if out and r[0] <= out[-1][1] + 0.05:
            out[-1][1] = max(out[-1][1], r[1])
        else:
            out.append(r)
    return out


def _cut(plan, out, extra_af=""):
    """The tight cut into `out`. Returns (total, was, log, kept): kept is [(words, ranges)] per part, in order, for
    anything that needs the words on the new timeline (the .srt)."""
    pause = float(plan.get("pause", 0.5))
    vf = "fps=30,scale=1920:1080,setsar=1,format=yuv420p"
    graph, inputs, log, kept, total, was = [], [], [], [], 0.0, 0.0
    for i, part in enumerate(plan["parts"]):
        words = transcript(part["folder"])["words"]
        cuts = [(float(c[0]), float(c[1]), c[2]) for c in part.get("cuts", [])]
        ranges = keep_ranges(words, cuts, [(float(k[0]), float(k[1])) for k in part.get("keep_whole", [])], pause)
        sel = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in ranges)
        graph.append(f"[{i}:v]select='{sel}',setpts=N/FRAME_RATE/TB,{vf}[v{i}];"
                     f"[{i}:a]aselect='{sel}',asetpts=N/SR/TB,aresample=48000,aformat=channel_layouts=mono[a{i}]")
        inputs += ["-i", str(folder(part["folder"]) / "source.mp4")]
        total += sum(e - s for s, e in ranges)
        was += words[-1][1]
        kept.append((words, ranges))
        log.append((part["folder"], [(c[0], min(c[1], words[-1][1]), c[2], " ".join(w[2] for w in words if c[0] <= w[0] < c[1])) for c in cuts]))
    n = len(plan["parts"])
    graph.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v]" + (f"[a0_];[a0_]{extra_af}[a]" if extra_af else "[a]"))
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "graph.txt").write_text(";".join(graph), encoding="utf-8")
        ff(["-y", "-loglevel", "error", *inputs, "-filter_complex_script", str(Path(tmp) / "graph.txt"), "-map", "[v]", "-map", "[a]",
            *ENC, "-crf", "24", "-b:a", "128k", "-movflags", "+faststart", str(out)])
    return total, was, log, kept


def cuts_md(plan, out, total, was, log):
    pause = float(plan.get("pause", 0.5))
    lines = [f"# What was cut: {out.name}", "", plan.get("why", ""), "",
             f"Kept {mmss(total)} of {mmss(was)}. Besides the cuts below, every \"uh\" and \"um\" and every pause over {pause:g} seconds is out, "
             "except in a stretch marked to stay whole.", ""]
    for fold, rows in log:
        lines += [f"## {fold}", "", "| From | To | Why | What he said |", "|---|---|---|---|"]
        lines += [f"| {mmss(s)} | {mmss(e)} | {why} | {said[:260] or '(silence)'} |" for s, e, why, said in rows] + [""]
    out.with_suffix(".cuts.md").write_text("\n".join(lines), encoding="utf-8")


def cmd_cut(a):
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    out = folder(plan["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    total, was, log, _ = _cut(plan, out)
    cuts_md(plan, out, total, was, log)
    print(f"{out.relative_to(ROOT).as_posix()} | kept {mmss(total)} of {mmss(was)}")
    check(out)


# ---------------------------------------------------------------- the long version for YouTube

def remap(kept, fixes=None):
    """Each kept word on the cut's own timeline: [(start, end, text)] across every part, in order."""
    fixes = {k.lower(): v for k, v in (fixes or {}).items()}
    said, acc = [], 0.0
    for words, ranges in kept:
        for s, e in ranges:
            for w in words:
                if s <= w[0] < e and norm(w[2]) not in FILLER:
                    said.append((acc + w[0] - s, acc + min(w[1], e) - s, fixes.get(w[2].lower(), fixes.get(norm(w[2]), w[2]))))
            acc += e - s
    return said


def srt(said, path):
    """A caption file, two to six words a line, a new line on a long gap or the end of a sentence."""
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    groups, cur = [], []
    for w in said:
        chars = sum(len(x[2]) for x in cur) + len(cur)
        if cur and (len(cur) >= 6 or chars + len(w[2]) > 34 or w[0] - cur[-1][1] > 0.6 or re.search(r"[.?!]$", cur[-1][2])):
            groups.append(cur)
            cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    lines = []
    for i, g in enumerate(groups):
        end = min(g[-1][1] + 0.3, groups[i + 1][0][0]) if i + 1 < len(groups) else g[-1][1] + 0.4
        lines += [str(i + 1), f"{ts(g[0][0])} --> {ts(max(end, g[0][0] + 0.3))}", " ".join(x[2] for x in g), ""]
    Path(path).write_text("\n".join(lines), encoding="utf-8")
    return len(groups)


def cmd_long_form(a):
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    out = folder(plan["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    yt = plan.get("youtube") or {}
    if len(yt.get("title", "")) > 100:
        sys.exit(f"The YouTube title is {len(yt['title'])} characters; 100 is the most YouTube takes.")
    total, was, log, kept = _cut(plan, out, extra_af=LOUD)
    cuts_md(plan, out, total, was, log)
    said = remap(kept, plan.get("fixes"))
    n = srt(said, out.with_suffix(".srt"))
    meta = {"title": yt.get("title", ""), "description": yt.get("description", ""), "tags": yt.get("tags", []),
            "category": int(yt.get("category", 27)), "privacy": yt.get("privacy", "private"), "made_for_kids": False,
            "company_key": plan.get("company_key", ""), "srt": out.with_suffix(".srt").name, "video": out.name,
            "seconds": round(total, 1), "video_id": None, "url": None, "uploaded_on": None, "published_on": None}
    out.with_suffix(".youtube.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"{out.relative_to(ROOT).as_posix()} | kept {mmss(total)} of {mmss(was)} | {n} caption lines | level -14 LUFS")
    check(out)


# ---------------------------------------------------------------- the one-recording short

def pick_runs(segments, words_of, pause, fixes, lead=0.08, tail=0.16):
    """His words in the plan's order, as runs across pauses up to `pause`, fillers out. segments: [(which, s, e)].
    Returns (parts [(which, p0, p1)], said [(start, end, text)] on the short's own timeline)."""
    fixes = {k.lower(): v for k, v in (fixes or {}).items()}
    parts, said, t = [], [], 0.0
    for which, s, e in segments:
        s, e = float(s), float(e)
        kept = [w for w in words_of(which) if s <= w[0] < e and norm(w[2]) not in FILLER]
        runs = []
        for w in kept:
            if runs and w[0] - runs[-1][1] <= pause:
                runs[-1][1] = w[1]
                runs[-1][2].append(w)
            else:
                runs.append([w[0], w[1], [w]])
        for rs, re_, ws in runs:
            p0, p1 = max(s, rs - lead), min(e, re_ + tail)
            parts.append((which, p0, p1))
            said += [(t + w[0] - p0, t + min(w[1], p1) - p0, fixes.get(w[2].lower(), fixes.get(norm(w[2]), w[2]))) for w in ws]
            t += p1 - p0
    return parts, said


def cmd_review_short(a):
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    out = folder(plan["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    src = folder(plan["folder"]) / "source.mp4"
    words = transcript(plan["folder"])["words"]
    crop, close_crop = plan.get("crop", TALL_CROP), plan.get("close_crop", CLOSE_CROP)
    close = [(float(c[0]), float(c[1])) for c in plan.get("close", [])]
    cap_y, panel_y = int(plan.get("cap_y", ONE_CAP_Y)), int(plan.get("panel_y", ONE_Y))
    if plan.get("face"):
        print("face: not built yet; the short shows the page only (his call, 2026-10-05).")
    parts, said = pick_runs([("one", s, e) for s, e in plan["segments"]], lambda _w: words, float(plan.get("pause", 0.5)), plan.get("fixes"))
    t = sum(p1 - p0 for _, p0, p1 in parts)
    if not SHORT_MIN <= t <= SHORT_MAX:
        sys.exit(f"The short would run {t:.1f} seconds; a review short is {SHORT_MIN:.0f} to {SHORT_MAX:.0f}. Change the segments.")
    pal = caps_style.load_palette()
    blue, white = caps_style.ass_color(pal["you"]), caps_style.ass_color(pal["youWord"])
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "fonts").mkdir()
        shutil.copy(FONT, work / "fonts" / FONT.name)
        names = []
        for i, (_, p0, p1) in enumerate(parts):
            d = p1 - p0
            near = any(c0 <= p0 < c1 for c0, c1 in close)
            graph = (f"color=c=0x0E1116:s=1080x1920:d={d:.3f}:r=30[bg];"
                     f"[0:v]fps=30,crop={close_crop if near else crop},scale={TALL_PANEL},setsar=1[live];"
                     f"[bg][live]overlay=0:{panel_y}:shortest=1,format=yuv420p[v];"
                     f"[0:a]aresample=48000,aformat=channel_layouts=mono,afade=t=in:d=0.02,afade=t=out:st={max(0.0, d - 0.04):.3f}:d=0.04[a]")
            ff(["-y", "-loglevel", "error", "-ss", f"{p0:.3f}", "-t", f"{d:.3f}", "-i", str(src), "-filter_complex", graph,
                "-map", "[v]", "-map", "[a]", "-t", f"{d:.3f}", *ENC, "-crf", "19", "-r", "30", "-b:a", "160k", f"part_{i:02d}.mp4"], cwd=work)
            names.append(f"part_{i:02d}.mp4")
        (work / "list.txt").write_text("".join(f"file '{n}'\n" for n in names), encoding="utf-8")
        ff(["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "joined.mp4"], cwd=work)
        (work / "captions.ass").write_text(ass(said, blue, white, cap_y=cap_y), encoding="utf-8")
        ff(["-y", "-loglevel", "error", "-i", "joined.mp4", "-vf", "ass=captions.ass:fontsdir=fonts", "-af", LOUD,
            *ENC, "-crf", "20", "-b:a", "160k", "-movflags", "+faststart", str(out)], cwd=work)
    first = " ".join(x[2] for x in said[:8])
    rows = "".join(f"| {mmss(float(s))} to {mmss(float(e))} | {float(e) - float(s):.1f} |\n" for s, e in plan["segments"])
    post = plan.get("post") or {}
    out.with_suffix(".cuts.md").write_text(
        f"# {out.name}\n\nOne idea: {plan.get('idea', '')}. {t:.0f} seconds. The page in one tall panel, captions under it, "
        "Monarc Studio's caption style. No tag, no icons. Fillers and long pauses are out.\n\n"
        f"First words (the line that says who it is for): {first}\n\n"
        f"## What is in it, in order\n\n| From and to in the Loom | Seconds |\n|---|---|\n{rows}\n## The words\n\n"
        + " ".join(x[2] for x in said) + "\n\n## The caption to paste when he posts\n\n" + (post.get("caption") or "(none written)") + "\n",
        encoding="utf-8")
    print(f"{out.relative_to(ROOT).as_posix()} | {t:.1f}s | {len(parts)} parts | {len(said)} words | first words: {first!r}")
    check(out)


# ---------------------------------------------------------------- the before-and-after short

def cmd_before_after(a):
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    out = folder(plan["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    side = {k: {"folder": folder(plan[k]["folder"]), "words": transcript(plan[k]["folder"])["words"], "still": float(plan[k]["still_at"])}
            for k in ("before", "after")}
    crop, close_crop = plan.get("crop", PAGE_CROP), plan.get("close_crop", CLOSE_CROP)
    close = [(c[0], float(c[1]), float(c[2])) for c in plan.get("close", [])]
    fixes = {k.lower(): v for k, v in (plan.get("fixes") or {}).items()}
    pause = float(plan.get("pause", 0.5))
    parts, said, t = [], [], 0.0
    for which, s, e in plan["segments"]:
        s, e = float(s), float(e)
        kept = [w for w in side[which]["words"] if s <= w[0] < e and norm(w[2]) not in FILLER]
        runs = []
        for w in kept:
            if runs and w[0] - runs[-1][1] <= pause:
                runs[-1][1] = w[1]
                runs[-1][2].append(w)
            else:
                runs.append([w[0], w[1], [w]])
        for rs, re_, ws in runs:
            p0, p1 = max(s, rs - 0.08), min(e, re_ + 0.16)
            parts.append((which, p0, p1))
            said += [(t + w[0] - p0, t + min(w[1], p1) - p0, fixes.get(w[2].lower(), fixes.get(norm(w[2]), w[2]))) for w in ws]
            t += p1 - p0
    pal = caps_style.load_palette()
    blue, white = caps_style.ass_color(pal["you"]), caps_style.ass_color(pal["youWord"])
    tag = ("drawbox=x=24:y={y}:w={w}:h=64:color={c}:t=fill,"
           "drawtext=fontfile=fonts/Montserrat-Black.ttf:text='{txt}':fontcolor=white:fontsize=38:x=24+({w}-text_w)/2:y={y}+(64-text_h)/2")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "fonts").mkdir()
        shutil.copy(FONT, work / "fonts" / FONT.name)
        for k in side:  # the first screen of each page, for the panel that is not being talked about
            ff(["-y", "-loglevel", "error", "-ss", str(side[k]["still"]), "-i", str(side[k]["folder"] / "source.mp4"), "-frames:v", "1",
                "-vf", f"crop={crop},scale={PANEL},setsar=1", f"{k}.png"], cwd=work)
        names = []
        for i, (which, p0, p1) in enumerate(parts):
            d = p1 - p0
            near = any(c[0] == which and c[1] <= p0 < c[2] for c in close)
            live_y, still_y, other = (TOP_Y, BOT_Y, "after") if which == "before" else (BOT_Y, TOP_Y, "before")
            graph = (f"color=c=0x0E1116:s=1080x1920:d={d:.3f}:r=30[bg];"
                     f"[0:v]fps=30,crop={close_crop if near else crop},scale={PANEL},setsar=1[live];"
                     "[1:v]fps=30,eq=brightness=-0.28:saturation=0.35,setsar=1[dim];"
                     f"[bg][live]overlay=0:{live_y}:shortest=1[x];[x][dim]overlay=0:{still_y}:shortest=1,"
                     + tag.format(y=TOP_Y - 78, w=230, c="0xD93025", txt="BEFORE") + ","
                     + tag.format(y=BOT_Y - 78, w=200, c="0x1E8E3E", txt="AFTER") + ",format=yuv420p[v];"
                     f"[0:a]aresample=48000,aformat=channel_layouts=mono,afade=t=in:d=0.02,afade=t=out:st={max(0.0, d - 0.04):.3f}:d=0.04[a]")
            ff(["-y", "-loglevel", "error", "-ss", f"{p0:.3f}", "-t", f"{d:.3f}", "-i", str(side[which]["folder"] / "source.mp4"),
                "-loop", "1", "-t", f"{d:.3f}", "-i", f"{other}.png", "-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-t", f"{d:.3f}",
                *ENC, "-crf", "19", "-r", "30", "-b:a", "160k", f"part_{i:02d}.mp4"], cwd=work)
            names.append(f"part_{i:02d}.mp4")
        (work / "list.txt").write_text("".join(f"file '{n}'\n" for n in names), encoding="utf-8")
        ff(["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "joined.mp4"], cwd=work)
        (work / "captions.ass").write_text(ass(said, blue, white), encoding="utf-8")
        ff(["-y", "-loglevel", "error", "-i", "joined.mp4", "-vf", "ass=captions.ass:fontsdir=fonts", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
            *ENC, "-crf", "20", "-b:a", "160k", "-movflags", "+faststart", str(out)], cwd=work)
    rows = "".join(f"| {w} | {mmss(float(s))} to {mmss(float(e))} | {float(e) - float(s):.1f} |\n" for w, s, e in plan["segments"])
    out.with_suffix(".cuts.md").write_text(
        f"# {out.name}\n\nOne idea: {plan.get('idea', '')}. {t:.0f} seconds. The old page plays on top while he talks about it, the new one "
        "below while he talks about that. Captions in Monarc Studio's style. No emoji. Fillers and long pauses are out.\n\n"
        f"## What is in it, in order\n\n| Panel | From and to in its Loom | Seconds |\n|---|---|---|\n{rows}\n## The words\n\n"
        + " ".join(x[2] for x in said) + "\n", encoding="utf-8")
    print(f"{out.relative_to(ROOT).as_posix()} | {t:.1f}s | {len(parts)} parts | {len(said)} words")
    check(out)


def ass(said, blue, white, cap_y=CAP_Y, res=(1080, 1920), size=84, max_chars=17):
    """Two or three words at a time, his words in his color and the word being said in white (Studio's palette).
    `res` is the frame (the shorts are 1080x1920; loom_ba.py passes 1920x1080), `size` the type size on that frame."""
    def ts(x):
        cs = int(x * 100 + 1e-6)
        return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"

    groups, cur = [], []
    for w in said:
        chars = sum(len(x[2]) for x in cur) + len(cur)
        if cur and (len(cur) >= 3 or chars + len(w[2]) > max_chars or w[0] - cur[-1][1] > 0.4 or re.search(r"[.?!]$", cur[-1][2])):
            groups.append(cur)
            cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {res[0]}", f"PlayResY: {res[1]}", "ScaledBorderAndShadow: yes", "WrapStyle: 2", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
             "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             f"Style: Cap,{caps_style.FONT_NAME},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,6,0,5,0,0,0,1",
             "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for gi, g in enumerate(groups):
        g_end = min(g[-1][1] + 0.25, groups[gi + 1][0][0]) if gi + 1 < len(groups) else g[-1][1] + 0.3
        for wi, w in enumerate(g):
            s = w[0] if wi else g[0][0]
            e = g[wi + 1][0] if wi + 1 < len(g) else g_end
            if e > s:
                text = " ".join(f"{{\\c{white if k == wi else blue}&}}" + caps_style.escape(re.sub(r"[.,]+$", "", x[2])) for k, x in enumerate(g))
                lines.append(f"Dialogue: 0,{ts(s)},{ts(e)},Cap,,0,0,0,,{{\\an5\\pos({res[0] // 2},{cap_y})}}{text}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- the finisher's look

def check(path):
    """What an editor checks before the director watches: the picture and the sound are there, nothing is black, no
    dead air, and the level is sane. Prints one line per finding; returns True when nothing is wrong."""
    path = Path(path)
    p = ff(["-i", str(path), "-vf", "blackdetect=d=0.4:pix_th=0.06", "-af", "silencedetect=noise=-42dB:d=1.5,volumedetect", "-f", "null", "-"], check=False)
    err = p.stderr
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    secs = int(dur[1]) * 3600 + int(dur[2]) * 60 + float(dur[3]) if dur else 0.0
    video = re.search(r"Video: \w+.*?, (\d+x\d+)", err)
    mean = re.search(r"mean_volume: (-?[\d.]+) dB", err)
    black = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)
    quiet = re.findall(r"silence_start: ([\d.]+)", err)
    bad = []
    if not video:
        bad.append("no picture")
    if "Audio:" not in err:
        bad.append("no sound")
    if black:
        bad.append("black at " + ", ".join(mmss(float(s)) for s, _ in black))
    if quiet:
        bad.append("dead air at " + ", ".join(mmss(float(s)) for s in quiet))
    if mean and float(mean[1]) < -30:
        bad.append(f"very quiet ({mean[1]} dB)")
    print(f"check: {path.name} | {mmss(secs)} | {video[1] if video else '?'} | level {mean[1] if mean else '?'} dB | "
          + ("; ".join(bad) if bad else "nothing wrong found"))
    return not bad


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("link")
    f.add_argument("--name", default="")
    w = sub.add_parser("words")
    w.add_argument("folder")
    w.add_argument("--from", dest="start", type=float, default=0.0)
    w.add_argument("--to", dest="end", type=float, default=1e9)
    for name in ("cut", "before-after", "long-form", "review-short"):
        sub.add_parser(name).add_argument("plan")
    sub.add_parser("check").add_argument("video")
    a = ap.parse_args()
    {"fetch": cmd_fetch, "words": cmd_words, "cut": cmd_cut, "before-after": cmd_before_after,
     "long-form": cmd_long_form, "review-short": cmd_review_short,
     "check": lambda x: check(folder(x.video))}[a.cmd](a)


if __name__ == "__main__":
    main()
