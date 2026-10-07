#!/usr/bin/env python3
"""Local preview of the monarcbuild.com mirror, with live reload.

Hands out projects/monarcbuild-site/public_html/ on 127.0.0.1 and tells every
open page to refresh itself when a file under the root shifts. The reload
script is slipped into each HTML answer as it is sent; nothing on disk changes,
so drift.py and site_sync.py never see it.

  python scripts/site_preview.py                # serve the mirror, open a browser window
  python scripts/site_preview.py --no-open      # serve, no window
  python scripts/site_preview.py --port 8800    # start the port hunt at 8800 (tries ten)
  python scripts/site_preview.py --root "projects/Landing Page Build/variants"

Endpoints the page script uses:
  GET /__live/version      -> {"v": N}                     also the "is it up?" check
  GET /__live/wait?v=N     -> hangs until version > N or 25 s, then {"v": M, "changed": [...]}

Standard library only. Ctrl+C stops it.
"""

import argparse
import json
import mimetypes
import re
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

REPO = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO / "projects" / "monarcbuild-site" / "public_html"
DEFAULT_PORT = 8790
SKIP_DIRS = {".git", "__pycache__", "node_modules"}

CLIENT_JS = r"""
<script data-mb-live>
(function () {
  var KEY = "mb-live-scroll";
  function restore() {
    var s = null;
    try { s = JSON.parse(sessionStorage.getItem(KEY) || "null"); sessionStorage.removeItem(KEY); } catch (e) {}
    if (!s) return;
    function put() {
      var snap = document.querySelector(".mb-snap");
      if (snap) snap.scrollTop = s.snap || 0;
      window.scrollTo(0, s.win || 0);
    }
    put();
    requestAnimationFrame(put);
    window.addEventListener("load", put, { once: true });
  }
  function stash() {
    try {
      var snap = document.querySelector(".mb-snap");
      sessionStorage.setItem(KEY, JSON.stringify({ win: window.scrollY, snap: snap ? snap.scrollTop : 0 }));
    } catch (e) {}
  }
  function reload() { stash(); location.reload(); }
  function swapCss(v) {
    document.querySelectorAll('link[rel="stylesheet"]').forEach(function (l) {
      var href = l.getAttribute("href");
      if (!href || /^https?:/i.test(href)) return;
      var u = new URL(href, location.href);
      u.searchParams.set("v", v);
      l.setAttribute("href", u.pathname + u.search);
    });
  }
  var v = __VERSION__, down = false, delay = 500;
  function loop() {
    fetch("/__live/wait?v=" + v, { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        delay = 500;
        if (down) { reload(); return; }
        if (d.v > v) {
          v = d.v;
          var cssOnly = d.changed.length > 0 && d.changed.every(function (p) { return /\.css$/i.test(p); });
          if (cssOnly) { swapCss(v); console.log("[mb-live] css swapped", d.changed); }
          else { console.log("[mb-live] reload", d.changed); reload(); return; }
        }
        loop();
      })
      .catch(function () {
        if (!down) console.log("[mb-live] server gone, retrying");
        down = true;
        setTimeout(loop, delay);
        delay = Math.min(5000, delay * 2);
      });
  }
  restore();
  loop();
})();
</script>
"""

BODY_END = re.compile(rb"</body\s*>", re.IGNORECASE)


def inject(html: bytes, version: int) -> bytes:
    tag = CLIENT_JS.replace("__VERSION__", str(version)).encode("utf-8")
    hits = list(BODY_END.finditer(html))
    if not hits:
        return html + tag
    at = hits[-1].start()
    return html[:at] + tag + html[at:]


class Watcher:
    """Polls the root every `interval` seconds. Bumps `version` after a change has sat still for `settle`."""

    def __init__(self, root: Path, interval: float = 0.25, settle: float = 0.2):
        self.root = root
        self.interval = interval
        self.settle = settle
        self.cond = threading.Condition()
        self.version = 0
        self.changed: list[str] = []
        self._snap = self.snapshot()
        threading.Thread(target=self._run, daemon=True, name="mb-live-watch").start()

    def snapshot(self) -> dict:
        snap = {}
        for p in self.root.rglob("*"):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if not p.is_file():
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            snap[p.relative_to(self.root).as_posix()] = (st.st_mtime_ns, st.st_size)
        return snap

    def _run(self):
        while True:
            time.sleep(self.interval)
            snap = self.snapshot()
            if snap == self._snap:
                continue
            while True:  # wait for the write to settle
                time.sleep(self.settle)
                again = self.snapshot()
                if again == snap:
                    break
                snap = again
            keys = set(snap) | set(self._snap)
            diff = sorted(k for k in keys if snap.get(k) != self._snap.get(k))
            self._snap = snap
            with self.cond:
                self.version += 1
                self.changed = diff
                self.cond.notify_all()
            print(f"[{time.strftime('%H:%M:%S')}] v{self.version}  {', '.join(diff)}", flush=True)

    def wait(self, since: int, timeout: float = 25.0):
        with self.cond:
            self.cond.wait_for(lambda: self.version > since, timeout=timeout)
            if self.version > since:
                return self.version, list(self.changed)
            return self.version, []


class Handler(BaseHTTPRequestHandler):
    root: Path = DEFAULT_ROOT
    watcher: Watcher = None  # set in main()

    def log_message(self, fmt, *args):  # keep the console for change lines only
        pass

    def _send(self, code: int, ctype: str, data: bytes):
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def _json(self, obj):
        self._send(200, "application/json; charset=utf-8", json.dumps(obj).encode("utf-8"))

    def _resolve(self, path: str):
        rel = unquote(path.lstrip("/"))
        root = self.root.resolve()
        file = (root / rel).resolve() if rel else root
        if file.is_dir():
            file = file / "index.html"
        if file != root and root not in file.parents:
            return None
        return file if file.is_file() else None

    def _static(self, path: str):
        file = self._resolve(path)
        if file is None:
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(str(file))[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/json", "text/javascript", "image/svg+xml"):
            ctype += "; charset=utf-8"
        data = file.read_bytes()
        if file.suffix.lower() in (".html", ".htm"):
            data = inject(data, self.watcher.version)
        self._send(200, ctype, data)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/__live/version":
            return self._json({"v": self.watcher.version, "root": str(self.root)})
        if u.path == "/__live/wait":
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                since = int(q.get("v", 0))
            except ValueError:
                since = 0
            ver, changed = self.watcher.wait(since)
            return self._json({"v": ver, "changed": changed})
        return self._static(u.path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="folder to hand out (default: the Hostinger mirror)")
    ap.add_argument("--path", default="/", help="page to open in the browser (default: /)")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    root = Path(args.root).resolve()
    if not root.is_dir():
        sys.exit(f"No such folder: {root}")

    Handler.root = root
    Handler.watcher = Watcher(root)
    ThreadingHTTPServer.daemon_threads = True

    httpd = None
    port = args.port
    for p in range(args.port, args.port + 10):
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    if not httpd:
        sys.exit(f"No free port from {args.port}.")

    url = f"http://127.0.0.1:{port}{args.path}"
    print(f"Serving {root}", flush=True)
    print(f"Live preview at {url}  (Ctrl+C stops it)", flush=True)
    if not args.no_open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
