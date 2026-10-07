"""Parse every inline <script> in an HTML file with esprima and report syntax errors with file line numbers.

Usage: python jscheck.py path\\to\\index.html
"""
import re
import sys

import esprima

path = sys.argv[1]
html = open(path, encoding="utf-8").read()
ok = True
for m in re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S):
    js = m.group(1)
    if not js.strip():
        continue
    base_line = html.count("\n", 0, m.start(1)) + 1
    try:
        esprima.parseScript(js, {"tolerant": False, "loc": False})
        print(f"ok   script at line {base_line}: {js.count(chr(10))} lines")
    except esprima.Error as exc:  # esprima reports its own line numbers inside the script
        ok = False
        line = getattr(exc, "lineNumber", None)
        where = f"file line {base_line + line - 1}" if line else "unknown line"
        print(f"FAIL script at line {base_line}: {exc} ({where})")
sys.exit(0 if ok else 1)
