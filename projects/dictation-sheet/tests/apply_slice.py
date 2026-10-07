"""Apply the OLD/NEW pairs of one slice file to index.html.

Usage: python apply_slice.py slice-3.md path\\to\\index.html [--write]

Without --write nothing is changed: every pair is checked (OLD must occur exactly once in the file as it
would be after the earlier pairs of the same slice). With --write the pairs are applied in order and the
file is rewritten only when every pair passed.
"""
import re
import sys

slice_path, html_path = sys.argv[1], sys.argv[2]
write = "--write" in sys.argv
text = open(slice_path, encoding="utf-8").read()
html = open(html_path, encoding="utf-8").read()

# a pair: "### Edit ..." title, then <<<OLD ... OLD, then >>>NEW ... NEW (each marker on its own line)
pat = re.compile(r"^### (Edit[^\n]*)\n.*?^<<<OLD\n(.*?)^OLD\n.*?^>>>NEW\n(.*?)^NEW\s*$", re.S | re.M)
pairs = pat.findall(text)
if not pairs:
    print("no pairs found in", slice_path)
    sys.exit(2)

# skip an optional section the integrator applies later, if the slice marks one
cut = text.find("Optional geometry fix")
optional_titles = set()
if cut >= 0:
    optional_titles = {t for t, _, _ in pat.findall(text[cut:])}

only_optional = "--optional" in sys.argv  # apply just the optional section this time
ok = True
work = html
for title, old, new in pairs:
    old = old.rstrip("\n")
    new = new.rstrip("\n")
    if (title in optional_titles) != only_optional:
        print(f"skip {title}" + ("" if only_optional else " (optional, apply later)"))
        continue
    n = work.count(old)
    if n != 1:
        ok = False
        # help the integrator: is it a whitespace problem?
        loose = work.count(old.strip())
        print(f"FAIL {title}: OLD occurs {n} times (stripped: {loose})")
        continue
    work = work.replace(old, new, 1)
    print(f"ok   {title}")

if not ok:
    print("nothing written: fix the failing pairs first")
    sys.exit(1)
if write:
    open(html_path, "w", encoding="utf-8", newline="").write(work)
    print(f"written {html_path} ({len(work)} chars, was {len(html)})")
else:
    print("dry run passed; add --write to apply")
