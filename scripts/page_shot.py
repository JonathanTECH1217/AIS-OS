"""A picture of a live monarcbuild.com page, desktop and phone, for the CRM's Google Ads page (2026-09-29).

Usage: python scripts/page_shot.py https://monarcbuild.com/google-ads/

Jonathan, 2026-09-29: a campaign's landing page card "should show me the wireframe of the landing page or just a copy of
the landing page". The copy is a full-page screenshot of the live page, at 1440 and 390 wide, saved as JPEG in
projects/crm/shots/ (git ignores it) and served by the CRM at /shots/<slug>-<width>.jpg.

The page is loaded with ?static=1 (the reveal and count-up rest, as in the /landing-page renders) and with the
tracking hosts blocked (Google Analytics, Google Ads, Meta, LinkedIn, Clarity), so taking a copy is never counted as a
visit or a conversion. It reuses the browser finder and tail trim of the landing-page skill's render.py.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "projects" / "crm" / "shots"
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "landing-page" / "assets"))
import render  # noqa: E402  find_browser, trim_tail

WIDTHS = (1440, 390)
HOSTS = ("monarcbuild.com", "www.monarcbuild.com")
BLOCK = ("googletagmanager.com", "*.googletagmanager.com", "google-analytics.com", "*.google-analytics.com",
         "analytics.google.com", "googleadservices.com", "*.googleadservices.com", "*.doubleclick.net",
         "googlesyndication.com", "*.googlesyndication.com", "connect.facebook.net", "*.facebook.com",
         "snap.licdn.com", "px.ads.linkedin.com", "*.clarity.ms")


def slug_for(url):
    path = urlparse(url).path.strip("/") or "home"
    return re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")


def check(url):
    u = urlparse(url or "")
    if u.scheme != "https" or u.hostname not in HOSTS:
        raise ValueError("Only https://monarcbuild.com pages.")
    return u


def paths(url):
    s = slug_for(url)
    return {w: SHOTS / f"{s}-{w}.jpg" for w in WIDTHS}


def shoot(url, timeout=90):
    """Render both widths; returns {width: Path}. Raises on a browser failure."""
    check(url)
    from PIL import Image
    SHOTS.mkdir(parents=True, exist_ok=True)
    page = url + ("&" if "?" in url else "?") + "static=1"
    browser = render.find_browser()
    rules = ", ".join(f"MAP {h} ~NOTFOUND" for h in BLOCK)
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for w in WIDTHS:
            narrow = w < 500
            scale, max_h = (2, 14000) if narrow else (1, 9000)
            target = page
            if narrow:  # headless will not open a window under 500 px, so phones render in an iframe (as render.py)
                wrapper = tmp / "phone.html"
                wrapper.write_text("<!doctype html><meta charset='utf-8'><style>html,body{margin:0;background:#fff}</style>"
                                   f"<iframe src='{page}' style='display:block;border:0;width:{w}px;height:{max_h}px'></iframe>",
                                   encoding="utf-8")
                target = wrapper.as_uri()
            png = tmp / f"{w}.png"
            subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={tmp / 'profile'}",
                            f"--host-resolver-rules={rules}", f"--force-device-scale-factor={scale}",
                            "--virtual-time-budget=10000", f"--window-size={max(w, 500)},{max_h}", f"--screenshot={png}", target],
                           check=True, capture_output=True, timeout=timeout)
            if narrow:
                im = Image.open(png)
                im.crop((0, 0, w * scale, im.size[1])).save(png)
            render.trim_tail(str(png))
            im = Image.open(png).convert("RGB")
            if narrow:  # back to 390 wide: sharp enough, a third of the bytes
                im = im.resize((w, round(im.size[1] / scale)), Image.LANCZOS)
            dest = paths(url)[w]
            # the copy it replaces goes to history/<slug>/, named by when it was taken (Jonathan, 2026-10-01: the current
            # page "and previous copies should all be archived here per landing page campaign")
            if dest.exists():
                hist = SHOTS / "history" / slug_for(url)
                hist.mkdir(parents=True, exist_ok=True)
                stamp = datetime.fromtimestamp(dest.stat().st_mtime).strftime("%Y-%m-%d-%H%M")
                shutil.copy2(dest, hist / f"{stamp}-{w}.jpg")
            im.save(dest, "JPEG", quality=82, optimize=True, progressive=True)
            out[w] = dest
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for w, p in shoot(sys.argv[1]).items():
        print(f"{w}: {p} ({p.stat().st_size // 1024} KB)")
