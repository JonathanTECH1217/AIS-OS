"""Screenshot the built page in headless Edge after running an extra script, so the drawn notation can be looked at.

Usage: python shot.py page.html out.png [extra.js]
"""
import os
import subprocess
import sys
import tempfile

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
src, png = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
extra = open(sys.argv[3], encoding="utf-8").read() if len(sys.argv) > 3 else ""
page = open(src, encoding="utf-8").read()
trap = "<script>var __lines = []; function __put(k, a) { __lines.push(k + ' ' + Array.prototype.join.call(a, ' ')); }</script>"
tail = """
<script>
setTimeout(function () { try { %s } catch (e) { document.title = 'EXTRA FAILED ' + e; } }, 1500);
</script>
""" % extra.replace("</script", "<\\/script")
page = page.replace("<head>", "<head>" + trap, 1) if "<head>" in page else trap + page
page = page.replace("</body>", tail + "</body>", 1) if "</body>" in page else page + tail
fd, tmp = tempfile.mkstemp(suffix=".html", dir=os.path.dirname(src), prefix="__shot_")
with os.fdopen(fd, "w", encoding="utf-8") as f:
    f.write(page)
try:
    r = subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-extensions",
                        "--virtual-time-budget=" + os.environ.get("BUDGET", "8000"),
                        "--window-size=" + os.environ.get("SIZE", "1400,1000"), "--hide-scrollbars",
                        "--user-data-dir=" + os.path.join(tempfile.gettempdir(), os.environ.get("PROFILE", "runjs-profile")),
                        "--screenshot=" + png, "file:///" + tmp.replace("\\", "/")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    print("saved" if os.path.exists(png) else "no screenshot", png, (r.stderr or "")[-400:])
finally:
    os.unlink(tmp)
