"""Load the built Dictation Sheet page in headless Edge with an error trap and print what happened at boot.

Usage: python pagecheck.py "C:\\Users\\sumre\\Documents\\Applications\\Dictation Sheet\\Dictation Sheet.html" [extra.js]
extra.js, when given, runs after the page has booted (about 1.5 s later) and can console.log findings.
"""
import html as htmlmod
import os
import re
import subprocess
import sys
import tempfile

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
src = os.path.abspath(sys.argv[1])
extra = open(sys.argv[2], encoding="utf-8").read() if len(sys.argv) > 2 else ""
page = open(src, encoding="utf-8").read()
trap = """<script>
var __lines = [];
function __put(kind, args) { __lines.push(kind + ' ' + Array.prototype.map.call(args, function (a) { try { return typeof a === 'string' ? a : (a && a.stack) ? a.stack : JSON.stringify(a); } catch (e) { return String(a); } }).join(' ')); }
var __err = console.error, __warn = console.warn;
console.error = function () { __put('ERR', arguments); };
console.warn = function () { __put('WARN', arguments); };
console.log = function () { __put('LOG', arguments); };
window.addEventListener('error', function (e) { __put('UNCAUGHT', [e.message + ' at ' + (e.lineno || '?') + ':' + (e.colno || '?')]); });
window.addEventListener('unhandledrejection', function (e) { __put('REJECTED', [e.reason && e.reason.stack || String(e.reason)]); });
</script>
"""
tail = """
<script>
setTimeout(function () {
  try {
    %s
  } catch (e) { __put('EXTRA-FAILED', [e && e.stack || String(e)]); }
  var pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = __lines.length ? __lines.join('\\n') : '(no errors, warnings or logs)';
  document.body.appendChild(pre);
}, 1500);
</script>
""" % extra.replace("</script", "<\\/script")
if "<head>" in page:
    page = page.replace("<head>", "<head>" + trap, 1)
else:
    page = trap + page
page = page.replace("</body>", tail + "</body>", 1) if "</body>" in page else page + tail
fd, tmp = tempfile.mkstemp(suffix=".html", dir=os.path.dirname(src), prefix="__check_")
with os.fdopen(fd, "w", encoding="utf-8") as f:
    f.write(page)
try:
    r = subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-extensions",
                        "--virtual-time-budget=" + os.environ.get("BUDGET", "6000"), "--window-size=" + os.environ.get("SIZE", "1400,900"),
                        "--user-data-dir=" + os.path.join(tempfile.gettempdir(), os.environ.get("PROFILE", "runjs-profile")),
                        "--dump-dom", "file:///" + tmp.replace("\\", "/")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
    print(htmlmod.unescape(m.group(1)) if m else "(no output captured; page may not have reached the timeout)\n" + r.stdout[-1500:] + r.stderr[-1500:])
finally:
    os.unlink(tmp)
