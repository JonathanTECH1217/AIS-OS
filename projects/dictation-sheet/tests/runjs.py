"""Run a JavaScript file in headless Edge (no Node on this machine) and print what it logs.

Usage: python runjs.py test.js
The script's console.log / console.error output and any uncaught error are written into the page body,
which Edge dumps after the page has loaded.
"""
import html as htmlmod
import os
import re
import subprocess
import sys
import tempfile

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
js_path = os.path.abspath(sys.argv[1])
js = open(js_path, encoding="utf-8").read().replace("</script", "<\\/script")
page = f"""<!doctype html><meta charset="utf-8"><title>runjs</title><body><pre id="out"></pre>
<script>
var __lines = [];
function __put(kind, args) {{ __lines.push(kind + ' ' + Array.prototype.map.call(args, function (a) {{ try {{ return typeof a === 'string' ? a : JSON.stringify(a); }} catch (e) {{ return String(a); }} }}).join(' ')); }}
console.log = function () {{ __put('LOG', arguments); }};
console.error = function () {{ __put('ERR', arguments); }};
window.onerror = function (m, s, l, c, e) {{ __put('UNCAUGHT', [m + ' at line ' + l + ':' + c]); }};
</script>
<script>
{js}
</script>
<script>document.getElementById('out').textContent = __lines.join('\\n');</script>
</body>"""
fd, tmp = tempfile.mkstemp(suffix=".html", dir=os.path.dirname(js_path))
with os.fdopen(fd, "w", encoding="utf-8") as f:
    f.write(page)
try:
    flags = [EDGE, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-extensions",
             "--autoplay-policy=no-user-gesture-required",
             "--user-data-dir=" + os.path.join(tempfile.gettempdir(), os.environ.get("PROFILE", "runjs-profile"))]
    if os.environ.get("TIMEOUT"):
        flags.append("--timeout=" + os.environ["TIMEOUT"])
    r = subprocess.run(flags + ["--dump-dom", "file:///" + tmp.replace("\\", "/")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    m = re.search(r'<pre id="out">(.*?)</pre>', r.stdout, re.S)
    print(htmlmod.unescape(m.group(1)) if m else "(no output captured)\n" + r.stdout[-2000:] + r.stderr[-2000:])
finally:
    os.unlink(tmp)
