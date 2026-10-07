"""Apply slice-1.md to a scratch copy of index.html: every OLD must occur exactly once, in order. Writes patched.html
and the inline script(s) as .js next to it, then does a string/comment-aware bracket balance pass on each NEW block."""
import io
import os
import re

SRC = r"C:\Users\sumre\Documents\GitHub\AIS-OS\projects\dictation-sheet\index.html"
SCR = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(SCR, "slice-1.md")

html = io.open(SRC, encoding="utf-8", newline="").read()
md = io.open(MD, encoding="utf-8", newline="").read().replace("\r\n", "\n")
pairs = re.findall(r"### (Edit 1\.\d+:[^\n]*)\n<<<OLD\n(.*?)\nOLD\n>>>NEW\n(.*?)\nNEW\n", md, re.S)
print("edits found:", len(pairs))
ok = True
for title, old, new in pairs:
    c = html.count(old)
    print("%s: OLD occurs %d time(s); %d -> %d lines" % (title, c, old.count("\n") + 1, new.count("\n") + 1))
    if c != 1:
        ok = False
        continue
    html = html.replace(old, new)

out = os.path.join(SCR, "patched.html")
io.open(out, "w", encoding="utf-8", newline="").write(html)
scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)
for i, s in enumerate(scripts):
    p = os.path.join(SCR, "script%d.js" % i)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("inline script %d: %d chars -> %s" % (i, len(s), p))


def balance(src):
    """Bracket balance ignoring strings, template literals and comments. No regex literals expected in these blocks."""
    stack = []
    pairs_ = {")": "(", "]": "[", "}": "{"}
    i, n = 0, len(src)
    line = 1
    while i < n:
        ch = src[i]
        if ch == "\n":
            line += 1
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if ch in "'\"`":
            q = ch
            i += 1
            while i < n and src[i] != q:
                if src[i] == "\\":
                    i += 1
                i += 1
            i += 1
            continue
        if ch in "([{":
            stack.append((ch, line))
        elif ch in ")]}":
            if not stack or stack[-1][0] != pairs_[ch]:
                return "unbalanced %r at line %d" % (ch, line)
            stack.pop()
        i += 1
    if stack:
        return "unclosed %r from line %d" % stack[-1]
    return "balanced"


for title, old, new in pairs:
    print("%s: NEW %s" % (title, balance(new)))

for name in ("voiceIR", "voiceOf", "voiceCurve"):
    print("function %s defined %d time(s)" % (name, len(re.findall(r"\bfunction %s\(" % name, html))))
print("ALL OLD UNIQUE" if ok else "PROBLEM: an OLD is missing or not unique")
