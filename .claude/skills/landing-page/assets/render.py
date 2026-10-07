"""Render an HTML file to a full-page PNG with headless Chrome or Edge.

Usage: python render.py <input.html> <output.png> <width> [max_height]

Opens the file at the given viewport width with a very tall window, screenshots it,
then trims the blank tail (rows that match the final background row) so the PNG
ends where the page ends. Used by the /landing-page skill for approval renders.
"""
import os
import subprocess
import sys
import pathlib

CANDIDATES = [
    os.environ.get("CHROME_PATH", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",       # a Mac (2026-10-07)
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_browser():
    for p in CANDIDATES:
        if p and os.path.exists(p):
            return p
    sys.exit("No Chrome or Edge found. Set CHROME_PATH.")


def trim_tail(png_path):
    try:
        from PIL import Image
    except ImportError:
        print("Pillow not installed; skipping trim.")
        return
    im = Image.open(png_path).convert("RGB")
    w, h = im.size
    px = im.load()
    last = [px[x, h - 1] for x in range(0, w, max(1, w // 64))]
    cut = h
    for y in range(h - 1, 0, -1):
        row = [px[x, y] for x in range(0, w, max(1, w // 64))]
        if row != last:
            cut = y + 1
            break
    cut = min(h, cut + 40)
    if cut < h:
        im.crop((0, 0, w, cut)).save(png_path)


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    # A file: URI (with an optional ?query, e.g. ?sent=1) or an http(s) address (a page served by a local server, for
    # pages that load /assets/... from the site root) is passed to the browser verbatim.
    src_uri = sys.argv[1] if sys.argv[1].startswith(("file:", "http:", "https:")) else None
    src = pathlib.Path(sys.argv[1]).resolve() if src_uri is None else None
    out = pathlib.Path(sys.argv[2]).resolve()
    width = int(sys.argv[3])
    max_h = int(sys.argv[4]) if len(sys.argv) > 4 else (9000 if width >= 1000 else 14000)
    out.parent.mkdir(parents=True, exist_ok=True)
    browser = find_browser()

    # Headless Chrome will not open a window narrower than 500 CSS px, so phone widths
    # are rendered inside an iframe of the requested width and cropped afterwards.
    narrow = width < 500
    scale = 2 if narrow else 1
    page_uri = src_uri or src.as_uri()
    target_uri = page_uri
    wrapper = None
    if narrow:
        wrapper = out.with_suffix(".wrapper.html")
        wrapper.write_text(
            "<!doctype html><meta charset='utf-8'><style>html,body{margin:0;background:#fff}</style>"
            f"<iframe src='{page_uri}' style='display:block;border:0;width:{width}px;height:{max_h}px'></iframe>",
            encoding="utf-8",
        )
        target_uri = wrapper.as_uri()
    win_w = max(width, 500)
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--force-device-scale-factor={scale}",
        "--virtual-time-budget=8000",
        f"--window-size={win_w},{max_h}",
        f"--screenshot={out}",
        target_uri,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    if narrow:
        try:
            from PIL import Image
            im = Image.open(str(out))
            im.crop((0, 0, width * scale, im.size[1])).save(str(out))
        except ImportError:
            print("Pillow not installed; narrow render left uncropped at 500px.")
        wrapper.unlink(missing_ok=True)
    trim_tail(str(out))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
