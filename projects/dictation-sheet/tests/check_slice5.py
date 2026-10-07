import re, sys, io
import esprima

SRC = r"C:\Users\sumre\Documents\GitHub\AIS-OS\projects\dictation-sheet\index.html"
MD = r"C:\Users\sumre\AppData\Local\Temp\claude\c--Users-sumre-Documents-GitHub-AIS-OS-projects-dictation-sheet\e53776e8-9cfa-42a9-96ed-0d783532b8cb\scratchpad\slice-5.md"

html = io.open(SRC, encoding="utf-8", newline="").read()
md = io.open(MD, encoding="utf-8", newline="").read()

# split the md into the main part and the optional part
opt_idx = md.index("## Optional geometry fix")
parts = [("main", md[:opt_idx]), ("optional", md[opt_idx:])]

pat = re.compile(r"### (Edit 5\.\d+): ([^\n]*)\n<<<OLD\n(.*?)\nOLD\n>>>NEW\n(.*?)\nNEW\n", re.S)

def scripts_of(h):
    # every inline <script> without src
    out = []
    for m in re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", h, re.S):
        out.append(m.group(1))
    return out

def parse_all(h, label):
    ss = scripts_of(h)
    ok = True
    for i, s in enumerate(ss):
        if not s.strip():
            continue
        try:
            esprima.parseScript(s, {"tolerant": False})
        except Exception as e:
            ok = False
            print("  [%s] script %d PARSE ERROR: %s" % (label, i, e))
    print("  [%s] %d inline scripts, parse %s" % (label, len(ss), "OK" if ok else "FAILED"))
    return ok

print("original file:")
parse_all(html, "original")

cur = html
for name, text in parts:
    edits = pat.findall(text)
    print("%s: %d edits" % (name, len(edits)))
    for eid, title, old, new in edits:
        n = cur.count(old)
        if n != 1:
            print("  %s (%s): OLD occurs %d times -> STOP" % (eid, title, n))
            sys.exit(1)
        # also check the OLD occurs exactly once in the ORIGINAL file (the integrator applies to the current file)
        n0 = html.count(old)
        cur = cur.replace(old, new, 1)
        print("  %s applied (in original: %d)" % (eid, n0))
    parse_all(cur, "after " + name)
    if name == "main":
        io.open(MD.replace("slice-5.md", "index.slice5.html"), "w", encoding="utf-8", newline="").write(cur)

# sanity: the new identifiers exist exactly where expected
for ident in ["function highlightSlot(", "function highlightClear(", "function followFrame(", "function spPollNext(", "function spOffsetSample(", "function spMedian(", "tl.chips = chips;", "sy.chips = tl.chips;"]:
    print("  %-32s x%d" % (ident, cur.count(ident)))
for gone in ["setInterval(spPoll", "clearInterval(sp.pollTimer)", "sp.posAt = performance.now() - 80"]:
    print("  gone? %-40s x%d" % (gone, cur.count(gone)))
