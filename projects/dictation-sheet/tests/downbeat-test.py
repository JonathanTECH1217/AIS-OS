"""The downbeat read (align.downbeat_of through beats_of) on synthetic songs whose beat 1 is known.

Cases: lines starting on the downbeat, lines as pickups (0.6 beat early), lines starting on beat 3 (a vote that
misleads: the kick and the chord changes must outweigh it), no lines at all, and a song with no chord changes and
an even kick (little to go on: the read must at least not claim to be sure). Each at three lead-ins so the tracked
beats start on different classes.  Usage: python downbeat-test.py
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import align  # noqa: E402
import mksong  # noqa: E402

fails = 0


def truth_class(beats, downs):
    """The class (index mod 4) of the tracked beats that sit on the true downbeats, by majority."""
    b = np.asarray(beats)
    votes = [0, 0, 0, 0]
    for t in downs:
        i = int(np.argmin(np.abs(b - t)))
        if abs(b[i] - t) < 0.12:
            votes[i % 4] += 1
    return int(np.argmax(votes)), max(votes) / max(1, sum(votes))


def run(name, wave, downs, starts, want_sure, expect_right=True):
    """expect_right: the read must be the true class and at least want_sure sure; else it must be the true class or
    not sure (under 0.4, which the page does not act on)."""
    global fails
    res = align.beats_of(wave, stamps=None, starts=starts)
    truth, agree = truth_class(res["beats"], downs)
    ok_phase = res["phase"] == truth
    ok = (ok_phase and res["phaseSure"] >= want_sure) if expect_right else (ok_phase or res["phaseSure"] < 0.4)
    if not ok:
        fails += 1
    print("%s %-44s tempo %6.2f truth %d read %d sure %.2f (beats on downbeats %.0f%%) cues %s" % (
        "PASS" if ok else "FAIL", name, res["tempo"], truth, res["phase"], res["phaseSure"], 100 * agree,
        {k: [round(x, 3) for x in v] for k, v in res.get("phaseCues", {}).items()}))


for lead in (0.9, 1.5, 2.1):
    wave, downs, beats = mksong.song(bpm=78.0, bars=14, lead=lead)
    beat = 60.0 / 78.0
    on_down = [downs[i] + 0.05 for i in range(1, len(downs) - 1, 2)]  # every second bar, a touch late
    pickups = [downs[i] - 0.6 * beat for i in range(1, len(downs) - 1, 2)]
    on_three = [downs[i] + 2 * beat + 0.05 for i in range(1, len(downs) - 1)]
    run("lead %.1f: lines on the downbeat" % lead, wave, downs, on_down, 0.4)
    run("lead %.1f: lines as pickups" % lead, wave, downs, pickups, 0.4)
    run("lead %.1f: lines on beat 3 (misleading vote)" % lead, wave, downs, on_three, 0.0, expect_right=False)
    run("lead %.1f: no lines" % lead, wave, downs, None, 0.4)
wave, downs, beats = mksong.song(bpm=78.0, bars=14, lead=0.9, chords=False, heavy_one=False)
run("no chords, even kick, no lines: not sure", wave, downs, None, 0.0, expect_right=False)
wave, downs, beats = mksong.song(bpm=120.0, bars=20, lead=0.7)
run("120 bpm, lines on the downbeat", wave, downs, [downs[i] + 0.03 for i in range(1, len(downs) - 1, 2)], 0.4)
print("downbeat test:", "all passed" if not fails else "%d failed" % fails)
sys.exit(1 if fails else 0)
