"""Pull the voice-analysis functions out of index.html (as they are now) into voice-fns.js, then glue each test body
onto it: voice-robust.full.js (pure functions), voice-band.full.js (bandOf renders). Nothing outside SP is touched."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path(r"C:\Users\sumre\Documents\GitHub\AIS-OS\projects\dictation-sheet\index.html").read_text("utf-8")
NAMES = ["risesOf", "voiceIR", "lowIR", "bandOf", "voiceOf", "lowOf", "pctl", "lineLevels", "sungEndAfter",
         "onsetCandidatesIn", "assignVirtual", "sungSpansIn", "evenSpans", "lrcWindows"]


def grab(name):
    m = re.search(r"^  (?:async )?function %s\(" % re.escape(name), SRC, re.M)
    assert m, name
    i = m.start()
    depth = 0
    j = SRC.index("{", i)
    k = j
    while True:
        c = SRC[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    line0 = SRC.count("\n", 0, i) + 1
    return "// index.html line %d\n%s\n" % (line0, SRC[i:k + 1])


prelude = "".join(grab(n) for n in NAMES)
(HERE / "voice-fns.js").write_text(prelude, "utf-8")
for body in ["voice-robust.js", "voice-band.js", "voice-diag.js"]:
    p = HERE / body
    if p.exists():
        (HERE / body.replace(".js", ".full.js")).write_text(prelude + "\n" + p.read_text("utf-8"), "utf-8")
        print("wrote", body.replace(".js", ".full.js"))
print("prelude lines", prelude.count("\n"))
