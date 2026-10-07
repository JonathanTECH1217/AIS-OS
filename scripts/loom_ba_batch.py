"""Loom B and A, the batch's end (Jonathan, 2026-10-06): "save all of these by date folders in a Loom B&A folder with the final
stitches that get attached as links to the email drafts. When a batch is done I should get an email notification saying batch
looms done and this is part of the SOP."

  python scripts/loom_ba_batch.py index  <date>    every cut in media/loom-ba/<date>/: length, the finisher's check, into index.md
  python scripts/loom_ba_batch.py pages  <date>    one page a video for monarcbuild.com, built in media/loom-ba/<date>/_site/v/<token>/
                                                   (the page and the video). Not pushed: the push waits on his go
                                                   (python scripts/site_sync.py push-as <local> v/<token>/<file>).
  python scripts/loom_ba_batch.py drafts <date>    one Proton draft a company with an address, its video's link in the body
  python scripts/loom_ba_batch.py notify <date>    "Batch looms done" laid in his inbox: each company, length, link, draft or why none
  python scripts/loom_ba_batch.py all    <date>    the four in order

The batch's rows (who gets each email, by what name) are projects/loom-b-and-a/batches/<date>.json. A video's link is
https://monarcbuild.com/v/<token>/, the token a short hash of the slug and the date, so no company's name is in a URL and
no link can be guessed. Nothing is sent: drafts wait in Proton Drafts, and the notice goes to his own inbox only.
"""
import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import social_content as scn  # noqa: E402

ROOT = scn.ROOT
BA = ROOT / "media" / "loom-ba"
BATCHES = ROOT / "projects" / "loom-b-and-a" / "batches"
SITE = "https://monarcbuild.com"
BOOK = "https://monarcbuild.com/av_marketing/"
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}


def rows(date):
    f = BATCHES / f"{date}.json"
    if not f.exists():
        sys.exit(f"No batch file: {f}")
    return json.loads(f.read_text(encoding="utf-8"))["rows"]


def token(slug, date):
    return hashlib.sha1(f"{slug}|{date}".encode()).hexdigest()[:10]


def video_of(date, slug):
    d = BA / date / slug
    vids = sorted(d.glob("*-loom-ba.mp4")) if d.exists() else []
    return vids[0] if vids else None


def seconds(path):
    p = scn.ff(["-i", str(path)], check=False)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", p.stderr)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0


def link(slug, date):
    return f"{SITE}/v/{token(slug, date)}/"


def cmd_index(date):
    out = ["# Loom B and A, batch " + date, "", "| Company | Video | Length | Check |", "|---|---|---|---|"]
    data = []
    for r in rows(date):
        v = video_of(date, r["slug"])
        if not v:
            out.append(f"| {r['company']} | not made | | |")
            data.append({**r, "video": None})
            continue
        s = seconds(v)
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok = scn.check(v)
        out.append(f"| {r['company']} | `{v.relative_to(ROOT).as_posix()}` | {scn.mmss(s)} | {'nothing wrong found' if ok else buf.getvalue().strip()} |")
        data.append({**r, "video": v.relative_to(ROOT).as_posix(), "seconds": round(s, 1), "ok": ok, "link": link(r["slug"], date)})
    (BA / date).mkdir(parents=True, exist_ok=True)
    (BA / date / "index.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    (BA / date / "index.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    made = sum(1 for d in data if d.get("video"))
    print(f"{(BA / date / 'index.md').relative_to(ROOT).as_posix()} | {made} of {len(data)} made")
    return data


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Your page, rebuilt</title>
<style>
:root{{--ink:#111;--bg:#0E0F11;--line:#2A2C30}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:#fff;font:400 17px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;min-height:100vh;display:grid;place-items:center;padding:24px}}
main{{width:100%;max-width:1100px;display:grid;gap:22px;justify-items:center;text-align:center}}
h1{{font-weight:400;font-size:clamp(24px,3vw,34px);letter-spacing:-.01em}}
video{{width:100%;border-radius:12px;background:#000;border:1px solid var(--line)}}
a.btn{{display:inline-flex;align-items:center;min-height:56px;padding:0 34px;border-radius:8px;background:#fff;color:var(--ink);font-weight:700;text-decoration:none}}
p{{color:rgba(255,255,255,.7);font-size:15px}}
</style>
</head>
<body>
<main>
<h1>{title}</h1>
<video src="video.mp4" controls playsinline preload="metadata" poster="poster.jpg"></video>
<a class="btn" href="{book}">Book a meeting</a>
<p>{minutes} minutes. Recorded for you; not posted anywhere.</p>
</main>
</body>
</html>
"""


def cmd_pages(date, data=None):
    data = data or json.loads((BA / date / "index.json").read_text(encoding="utf-8"))
    made = 0
    for d in data:
        if not d.get("video"):
            continue
        t = token(d["slug"], date)
        dest = BA / date / "_site" / "v" / t
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / d["video"], dest / "video.mp4")
        scn.ff(["-y", "-loglevel", "error", "-ss", "1", "-i", str(dest / "video.mp4"), "-frames:v", "1", "-vf", "scale=1280:-2", "-q:v", "4", str(dest / "poster.jpg")])
        mins = max(1, round(d.get("seconds", 180) / 60))
        title = f"Your {d['service']} page, rebuilt"
        (dest / "index.html").write_text(PAGE.format(title=html.escape(title), book=BOOK, minutes=WORDS.get(mins, str(mins)).capitalize()), encoding="utf-8")
        made += 1
    print(f"{made} pages built in media/loom-ba/{date}/_site/v/ (not pushed; links go live when he says push)")


def body_for(d, date):
    mins = WORDS.get(max(1, round(d.get("seconds", 180) / 60)), "a few")
    hello = f"{d['first']}," if d.get("first") else f"{d['company']} team,"
    return (f"{hello}\n\nI recorded {mins} minutes on your {d['service']} page: the first screen as it is, then each change as I make it. "
            f"The headline, the button, the words, the picture.\n\n{link(d['slug'], date)}\n\n"
            "Nothing to send me. Watch it, keep what fits, and if you want the changes made, give me the word.\n\nMy Best,\nJonathan\n")


def subject_for(d, i):
    mins = WORDS.get(max(1, round(d.get("seconds", 180) / 60)), "a few")
    choices = [("S1", f"Your {d['service']} page, rebuilt in {mins} minutes")]
    if d.get("first"):
        choices.append(("S2", f"{d['first']}, I rebuilt your first screen"))
    choices.append(("S3", f"{d['company']}: your page, {mins} minutes"))
    return choices[i % len(choices)]


def cmd_drafts(date):
    data = json.loads((BA / date / "index.json").read_text(encoding="utf-8"))
    by_slug = {r["slug"]: r for r in rows(date)}     # an address added to the batch file after the index was built
    placed, skipped = [], []
    for i, d in enumerate(data):
        r = by_slug.get(d["slug"], {})
        for k in ("to", "first", "note"):
            if r.get(k) is not None:
                d[k] = r[k]
        if (d.get("draft") or {}).get("placed"):
            continue                                  # drafted on an earlier run; never placed twice
        if not d.get("video"):
            skipped.append((d, "no video"))
            continue
        if not d.get("to"):
            skipped.append((d, d.get("note") or "no address on file"))
            continue
        key, subj = subject_for(d, i)
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(f"To: {d['to']}\nSubject: {subj}\n\n{body_for(d, date)}")
            spec = f.name
        p = subprocess.run([sys.executable, str(ROOT / "scripts" / "proton_mail.py"), "draft", spec], capture_output=True, text=True, encoding="utf-8", errors="replace")
        Path(spec).unlink(missing_ok=True)
        ok = p.returncode == 0 and "draft placed" in p.stdout
        d["draft"] = {"subject": subj, "key": key, "placed": ok, "out": (p.stdout + p.stderr).strip()[-300:]}
        (placed if ok else skipped).append((d, subj if ok else "draft refused: " + (p.stdout + p.stderr).strip()[-160:]))
    (BA / date / "index.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"{len(placed)} drafts placed; {len(skipped)} without a draft")
    for d, why in skipped:
        print(f"  no draft: {d['company']}: {why}")


def cmd_notify(date):
    data = json.loads((BA / date / "index.json").read_text(encoding="utf-8"))
    made = [d for d in data if d.get("video")]
    drafted = [d for d in made if (d.get("draft") or {}).get("placed")]
    lines = [f"{len(made)} videos made, {len(drafted)} email drafts in Proton Drafts. Nothing is sent.", "",
             f"Videos: media/loom-ba/{date}/ (index.md lists them).",
             "The links in the drafts go live when the video pages are pushed to monarcbuild.com. Say push first, then send.", ""]
    for d in data:
        if not d.get("video"):
            lines.append(f"{d['company']}: no video yet.")
            continue
        dr = d.get("draft") or {}
        state = f"draft to {d['to']}, subject \"{dr.get('subject')}\"" if dr.get("placed") else f"no draft ({d.get('note') or ('no address on file' if not d.get('to') else 'refused')})"
        lines.append(f"{d['company']}: {scn.mmss(d.get('seconds', 0))}, {d['link']}, {state}.")
    lines += ["", "Campaign: Loom B and A: cold audits, on the Email channel in the CRM."]
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(f"From: Monarc AIOS <jonathan@monarcbuild.com>\nSubject: Batch looms done: {date}, {len(made)} videos\nTest: batch\n\n" + "\n".join(lines) + "\n")
        spec = f.name
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "proton_mail.py"), "inbox-test", spec], capture_output=True, text=True, encoding="utf-8", errors="replace")
    Path(spec).unlink(missing_ok=True)
    print((p.stdout + p.stderr).strip())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["index", "pages", "drafts", "notify", "all"])
    ap.add_argument("date")
    a = ap.parse_args()
    if a.cmd == "index":
        cmd_index(a.date)
    elif a.cmd == "pages":
        cmd_pages(a.date)
    elif a.cmd == "drafts":
        cmd_drafts(a.date)
    elif a.cmd == "notify":
        cmd_notify(a.date)
    else:
        data = cmd_index(a.date)
        cmd_pages(a.date, data)
        cmd_drafts(a.date)
        cmd_notify(a.date)


if __name__ == "__main__":
    main()
