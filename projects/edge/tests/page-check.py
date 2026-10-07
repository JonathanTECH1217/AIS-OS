"""Monarc Edge page tests: python projects/edge/tests/page-check.py [name ...]

Serves projects/edge/ with a plain static server on 8802 (the tests fake every /api/ route themselves), opens
index.html?test=<name> for each t-*.js in headless Edge at 1536 x 780 (his screen), waits for the DONE line in
<pre id="__out">, prints the PASS / FAIL lines, and saves tests/shots/<name>.png. Exit code 1 when anything failed.
"""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = 8802


def main():
    names = sys.argv[1:] or sorted(p.stem[2:] for p in HERE.glob("t-*.js"))
    (HERE / "shots").mkdir(exist_ok=True)
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"], cwd=str(HERE.parent),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    failed = 0
    try:
        time.sleep(0.8)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            for name in names:
                page = browser.new_page(viewport={"width": 1536, "height": 780})
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(f"http://127.0.0.1:{PORT}/index.html?test={name}")
                text = ""
                for _ in range(80):                                   # 20 s
                    text = page.eval_on_selector("#__out", "e => e.textContent")
                    if "DONE" in text:
                        break
                    time.sleep(0.25)
                page.screenshot(path=str(HERE / "shots" / f"{name}.png"))
                page.close()
                lines = [l for l in text.splitlines() if l.strip()] + [f"FAIL page error: {e[:300]}" for e in errors]
                if "DONE" not in text:
                    lines.append("FAIL timeout (no DONE line)")
                print(f"== {name}\n" + "\n".join(lines))
                failed += sum(l.startswith("FAIL") for l in lines)
            browser.close()
    finally:
        srv.kill()
    print("\nall green" if not failed else f"\n{failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
