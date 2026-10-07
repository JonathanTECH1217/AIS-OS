"""Build tempo-pure.js: the tempo functions copied verbatim out of index.html (by their line ranges) plus a timing
body, to run under runjs.py on the real clock (pagecheck's virtual clock freezes during sync work)."""
import re

SRC = r"C:\Users\sumre\Documents\GitHub\AIS-OS\projects\dictation-sheet\index.html"
OUT = r"C:\Users\sumre\AppData\Local\Temp\claude\c--Users-sumre-Documents-GitHub-AIS-OS-projects-dictation-sheet\e53776e8-9cfa-42a9-96ed-0d783532b8cb\scratchpad\tempo-pure.js"
lines = open(SRC, encoding="utf-8").read().split("\n")

def grab(start_pat, end_pat):
    s = next(i for i, l in enumerate(lines) if re.search(start_pat, l))
    e = next(i for i in range(s, len(lines)) if re.search(end_pat, lines[i]))
    return "\n".join(lines[s:e + 1])

parts = [
    grab(r"^\s*function risesOf\(", r"^  \}\s*$"),
    grab(r"^\s*function tempoOf\(", r"^  \}\s*$"),
    grab(r"^\s*function trackBeats\(", r"^  \}\s*$"),
    grab(r"^\s*function beatFit\(", r"^  \}\s*$"),
    grab(r"^\s*var MET_SURE = ", r"^\s*var MET_SURE = "),
    grab(r"^\s*function zscore\(", r"^\s*function zscore\("),
    grab(r"^\s*function lastBeatAtOrBefore\(", r"^\s*function lastBeatAtOrBefore\("),
    grab(r"^\s*function meterOf\(", r"^  \}\s*$"),
    grab(r"^\s*function timeFromMeter\(", r"^\s*function timeFromMeter\("),
]
body = r"""
var fps = 100;
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; if (k0 < 0) return; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
function fresh(N, f) { var e = new Float32Array(N); for (var i = 0; i < N; i++) e[i] = f; return e; }
function drums(o) {
  var len = o.len || 60, N = Math.round(len * fps), full = fresh(N, 0.5), low = fresh(N, 0.4), beats = [], t = 1.0, k = 0, tau;
  while (t < len - 0.5) {
    tau = 60 / (o.bpm * (1 + (o.drift || 0) * t / len)); beats.push(t);
    var pos = k % 4;
    if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else if (pos === 2) { bump(low, t, 1.8, 12); bump(full, t, 1.9, 10); } else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); }
    bump(full, t, 1.0, 4); bump(full, t + tau / 2, 1.0, 4);
    t += tau; k++;
  }
  return { full: full, low: low, on: risesOf(full), beats: beats };
}
function timeit(label, fn, reps) { var t0 = performance.now(), r; for (var i = 0; i < reps; i++) r = fn(); var ms = (performance.now() - t0) / reps; console.log(label + ': ' + ms.toFixed(1) + ' ms' + (reps > 1 ? ' (mean of ' + reps + ')' : '')); return r; }
[60, 304, 600].forEach(function (len) {
  var tr = drums({ bpm: 76, len: len }), n = tr.on.length;
  console.log('--- ' + len + ' s track (' + n + ' frames) at 76 bpm');
  var bpm = timeit('tempoOf', function () { return tempoOf(tr.on, fps); }, 3);
  var beats = timeit('trackBeats', function () { return trackBeats(tr.on, fps, bpm); }, 3);
  var m = timeit('meterOf', function () { return meterOf(tr.on, tr.low, fps, beats, 60 / bpm, null); }, 3);
  timeit('beatFit', function () { return beatFit(tr.on, fps, beats); }, 3);
  var lo = timeit('tempoOf at 60 bpm (widest lags)', function () { return tempoOf(drums({ bpm: 60, len: len }).on, fps); }, 1);
  var t180 = drums({ bpm: 180, len: len }); timeit('trackBeats at 180 bpm', function () { return trackBeats(t180.on, fps, 180); }, 1);
  console.log('   bpm ' + bpm + ' beats ' + beats.length + ' meter ' + (m ? m.time + ' sure ' + m.sure.toFixed(2) + ' phase ' + m.phase : 'null') + ' | 60 bpm read ' + lo);
});
// cross-check with the page: the same 60 s 76 track must give the same tempo as pagecheck did (76)
console.log('cross-check 76 straight 60 s: ' + tempoOf(drums({ bpm: 76, len: 60 }).on, fps));
"""
open(OUT, "w", encoding="utf-8").write("\n".join(parts) + "\n" + body)
print("wrote", OUT, "with", sum(p.count("\n") + 1 for p in parts), "source lines")
