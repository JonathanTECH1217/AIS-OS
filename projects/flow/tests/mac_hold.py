"""Checks for Monarc Flow's Mac key logic (scripts/flow_mac.py, Hold), runnable on any machine:
  python projects/flow/tests/mac_hold.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
import flow_mac as fm  # noqa: E402

FAILS = []


def check(name, got, want):
    ok = got == want
    print(f"{'OK  ' if ok else 'FAIL'}  {name}" + ("" if ok else f"\n      got  {got}\n      want {want}"))
    if not ok:
        FAILS.append(name)


def run(steps):
    out = []
    h = fm.Hold(lambda n, i: out.append(n))
    swallowed = []
    for s in steps:
        if s[0] == "flags":
            h.flags(*s[1:])
        elif s[0] == "down":
            swallowed.append(("down", s[1], h.key_down(s[1])))
        elif s[0] == "up":
            swallowed.append(("up", s[1], h.key_up(s[1])))
        elif s[0] == "wait":
            time.sleep(s[1])
    return out, swallowed


SP, ESC, A = fm.KEY_SPACE, fm.KEY_ESC, 0

out, _ = run([("flags", 1, 0), ("flags", 1, 1), ("flags", 0, 1)])
check("hold then let go: start, stop", out, ["start", "stop"])

out, sw = run([("flags", 1, 1), ("down", SP), ("up", SP), ("flags", 0, 0), ("flags", 1, 1), ("flags", 0, 0)])
check("Space locks; the combo again stops", out, ["start", "lock", "stop"])
check("that Space is swallowed, down and up", [x[2] for x in sw], [True, True])

out, sw = run([("flags", 1, 1), ("down", ESC), ("up", ESC), ("flags", 0, 0)])
check("Esc while holding cancels, no stop after", out, ["start", "cancel"])
check("that Esc is swallowed", [x[2] for x in sw], [True, True])

out, sw = run([("flags", 1, 1), ("down", A), ("up", A), ("flags", 0, 0)])
check("another key cancels and still works", out, ["start", "cancel"])
check("that key is not swallowed", [x[2] for x in sw], [False, False])

out, sw = run([("flags", 1, 1), ("down", SP), ("flags", 0, 0), ("down", ESC)])
check("Esc while locked cancels", out, ["start", "lock", "cancel"])

out, sw = run([("down", SP), ("up", SP)])
check("Space with no hold is left alone", (out, [x[2] for x in sw]), ([], [False, False]))

out, _ = run([("flags", 0, 1), ("flags", 1, 1), ("flags", 1, 0), ("flags", 1, 1), ("flags", 0, 0)])
check("Cmd first then Ctrl also starts; a second hold starts again", out, ["start", "stop", "start", "stop"])

print("\nall passed" if not FAILS else f"\n{len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
