"""Monarc Studio UI checklist runner (G39): every tool, shortcut and panel, in headless Edge, with screenshots.

  python projects/studio/tests/run.py              all tests (t-*.js)
  python projects/studio/tests/run.py razor undo   just these

Copies tests/fixtures/seed (built by fixtures/make.py if missing) to a fresh temp media folder, starts the Studio
server on port 8781 against it (STUDIO_MEDIA), waits until the fixtures are prepared, then loads
http://127.0.0.1:8781/?test=<name> for each test in a new browser context, reads PASS / FAIL lines from
<pre id="__out">, and saves tests/shots/<name>.png. A page error counts as a failure. Exit code 1 if anything failed.

Monarc Calls tests (t-calls*.js) load calls.html at 510 x 780 instead (the notes window beside Airtable), run last,
and use the stand-ins: STUDIO_FAKE_MIC (lines the test says), STUDIO_FAKE_AIRTABLE (fixtures/prospects.json, copied)
and the test phrase file (fixtures/call-note-phrases.md).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SEED = HERE / "fixtures" / "seed"
SHOTS = HERE / "shots"
PORT = 8781
URL = f"http://127.0.0.1:{PORT}/"
# his screen (1920x1080 at 125 %); the notes window takes a third of it, beside Airtable
VIEWPORTS = {"browse": (1536, 780), "calls": (510, 780), "calls-layout": (510, 780)}


def get(path, timeout=5):
    with urllib.request.urlopen(URL + path, timeout=timeout) as r:
        return json.loads(r.read())


def main():
    names = sys.argv[1:] or sorted(p.stem[2:] for p in HERE.glob("t-*.js"))
    order = {n: i for i, n in enumerate(names)}
    names = sorted(names, key=lambda n: (n.startswith("calls"), order[n]))   # Monarc Calls last, its own page
    sys.path.insert(0, str(HERE / "fixtures"))
    import make as fixtures                       # noqa: E402  (tests/fixtures/make.py)
    if not fixtures.seed_current():               # missing, or built before the seed last changed
        subprocess.run([sys.executable, str(HERE / "fixtures" / "make.py")], check=True)
    base = Path(tempfile.gettempdir())
    for old in base.glob("studio-test-media*"):          # earlier runs; a locked one is left for next time
        shutil.rmtree(old, ignore_errors=True)
    media = base / f"studio-test-media-{int(time.time())}"
    shutil.copytree(SEED, media)
    # the palette and the voiceprint the tests change live in the throwaway copy, never in the real ones
    shutil.copy(HERE / "fixtures" / "prospects.json", media / "prospects.json")
    env = dict(os.environ, STUDIO_MEDIA=str(media), STUDIO_CONFIG=str(media / "config.json"),
               STUDIO_VOICEPRINT=str(media / "voiceprint.json"), STUDIO_NO_CLAUDE="1",   # tests never spend
               STUDIO_FAKE_MIC="1", STUDIO_FAKE_AIRTABLE=str(media / "prospects.json"),   # never the real mic or base
               STUDIO_PHRASES=str(HERE / "fixtures" / "call-note-phrases.md"),
               STUDIO_POLL_SECONDS="0.4", STUDIO_SETTLE_SECONDS="0.2",
               STUDIO_FAKE_LISTEN="1")                                     # Generate captions: fixtures' listen-fake.json
    (HERE / "out").mkdir(exist_ok=True)
    srv_log = open(HERE / "out" / "server.log", "w", encoding="utf-8")   # a file, never a pipe nobody reads
    srv = subprocess.Popen([sys.executable, "-u", str(ROOT / "scripts" / "studio_server.py"), "--port", str(PORT), "--no-open"],
                           env=env, stdout=srv_log, stderr=subprocess.STDOUT, cwd=str(ROOT))
    try:
        for _ in range(60):
            try:
                get("api/health")
                break
            except OSError:
                time.sleep(0.5)
        t0 = time.time()
        while time.time() - t0 < 240:
            b = get("api/bin")
            items = [a for f in b["folders"] if f["dir"] in ("inbox", "sfx", "assets") for a in f["items"]]
            if len(items) >= 4 and all(all(s.get("state") == "done" for s in a["stages"].values()) for a in items):
                break
            time.sleep(1)
        print(f"fixtures prepared in {time.time() - t0:.0f} s")
        SHOTS.mkdir(exist_ok=True)
        from playwright.sync_api import sync_playwright
        results, total_fail = {}, 0
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True, args=["--autoplay-policy=no-user-gesture-required",
                                        "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"])
            for name in names:
                vw, vh = VIEWPORTS.get(name, (1600, 960))
                ctx = browser.new_context(viewport={"width": vw, "height": vh})
                page = ctx.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                # a 409 is what the save test provokes on purpose (a stale save); the test itself checks it
                page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "favicon" not in m.text
                        and "status of 409" not in m.text else None)
                page.goto(URL + (f"calls.html?test={name}" if name.startswith("calls") else f"?test={name}"))
                text = ""
                deadline = time.time() + 90
                while time.time() < deadline:
                    text = page.eval_on_selector("#__out", "e => e.textContent")
                    if "DONE" in text:
                        break
                    time.sleep(0.25)
                page.screenshot(path=str(SHOTS / f"{name}.png"))
                lines = [l for l in text.splitlines() if l.strip()]
                fails = [l for l in lines if l.startswith("FAIL")]
                if "DONE" not in text:
                    fails.append("FAIL timeout (no DONE line)")
                for e in errors:
                    fails.append(f"FAIL page error: {e[:300]}")
                passes = [l for l in lines if l.startswith("PASS")]
                results[name] = {"pass": len(passes), "fail": fails}
                total_fail += len(fails)
                mark = "ok  " if not fails else "FAIL"
                print(f"{mark} {name:14} {len(passes):3} passed" + (f", {len(fails)} failed" if fails else ""))
                for f in fails:
                    print("       " + f)
                ctx.close()
            browser.close()
        (HERE / "out").mkdir(exist_ok=True)
        (HERE / "out" / "report.json").write_text(json.dumps(results, indent=1))
        n_pass = sum(r["pass"] for r in results.values())
        print(f"\n{len(results)} tests, {n_pass} checks passed, {total_fail} failed. Shots in {SHOTS}")
        return 1 if total_fail else 0
    finally:
        # the server and everything it started (renders, ffmpeg)
        subprocess.run(["taskkill", "/PID", str(srv.pid), "/T", "/F"], capture_output=True)
        srv.wait()


if __name__ == "__main__":
    sys.exit(main())
