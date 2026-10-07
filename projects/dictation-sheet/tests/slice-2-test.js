// Slice 2 self-test: the new detector functions on the plan's worked example ("Si-lent night, [breath] peace").
// Run: node slice-2-test.js   (or ELECTRON_RUN_AS_NODE=1 Code.exe slice-2-test.js when node is missing)

// ---- copied from index.html (unchanged) ----
// onset strength from a loudness curve: rises only, lightly smoothed
function risesOf(rms) {
  var n = rms.length, out = new Float32Array(n), i, v;
  for (i = 1; i < n; i++) { v = rms[i] - rms[i - 1]; out[i] = v > 0 ? v : 0; }
  for (i = 1; i < n - 1; i++) out[i] = (out[i - 1] + out[i] + out[i + 1]) / 3;
  return out;
}
// today's picker, kept here only to check the wrapper reproduces it
function onsetTimesInOld(curve, fps, start, t0, t1, K) {
  if (!curve || start === null) return null;
  var k0 = Math.max(1, Math.floor((t0 - start) * fps)), k1 = Math.min(curve.length - 2, Math.ceil((t1 - start) * fps));
  if (k1 - k0 < fps * 0.3) return null;
  var peaks = [], k; for (k = k0; k <= k1; k++) if (curve[k] > curve[k - 1] && curve[k] >= curve[k + 1] && curve[k] > 0) peaks.push({ k: k, v: curve[k] });
  peaks.sort(function (a, b) { return b.v - a.v; });
  var chosen = []; peaks.forEach(function (p) { if (chosen.length >= K) return; if (chosen.every(function (c) { return Math.abs(c.k - p.k) >= fps * 0.08; })) chosen.push(p); });
  if (chosen.length < Math.ceil(K / 2)) return null;
  chosen.sort(function (a, b) { return a.k - b.k; });
  var times = chosen.map(function (c) { return start + c.k / fps; });
  while (times.length < K) { var gi = 0, gmax = -1; for (var q = 0; q < times.length; q++) { var g = (q + 1 < times.length ? times[q + 1] : t1) - times[q]; if (g > gmax) { gmax = g; gi = q; } } times.splice(gi + 1, 0, times[gi] + gmax / 2); }
  return times;
}

// ---- NEW: exactly the text that goes into index.html (Edit 2.1) ----
  // percentile q (0 to 1) of arr[k0..k1), the ends clamped to the array, the way beatFit reads its 90th; 0 when empty
  function pctl(arr, k0, k1, q) {
    k0 = Math.max(0, Math.floor(k0) || 0); k1 = Math.min(arr.length, Math.ceil(k1) || 0); if (k1 <= k0) return 0;
    var s = Array.prototype.slice.call(arr, k0, k1).sort(function (a, b) { return a - b; });
    return s[Math.min(s.length - 1, Math.floor(s.length * q))];
  }
  // the line's quiet and loud levels: 10th and 90th percentile of the voice envelope over the window plus 0.3 s each
  // side. The floor is the level between the syllables of this line, so backing that lifts it is handled per line.
  function lineLevels(vc, t0, t1) {
    if (!vc || !vc.env) return { floor: 0, top: 0 };
    var k0 = Math.floor((t0 - 0.3 - vc.start) * vc.fps), k1 = Math.ceil((t1 + 0.3 - vc.start) * vc.fps) + 1;
    return { floor: pctl(vc.env, k0, k1, 0.1), top: pctl(vc.env, k0, k1, 0.9) };
  }
  // where a syllable sung at tOn stops sounding, in seconds: the first 50 ms run below floor + 0.4 * (body - floor),
  // looked for from 60 ms after the onset (no sung syllable is shorter, and it skips a stop consonant's closure) up to
  // tLimit (the next onset or the line's end). The body is the loudest 50 ms of the first 150 ms, so a consonant burst
  // is not the reference; the floor is the line's, lowered to the 80 ms before the onset when that is quieter (found
  // from the window when not given). Returns tLimit when the voice still sounds there, when it is not visible (under
  // 0.25 above the floor) or when the curve does not reach that far: a stopped listener is not silence.
  function sungEndAfter(vc, tOn, tLimit, floor) {
    if (!vc || !vc.env || typeof vc.start !== 'number') return tLimit;
    var env = vc.env, fps = vc.fps, kOn = Math.round((tOn - vc.start) * fps), w = Math.max(1, Math.round(fps * 0.05)), span = Math.round(fps * 0.15), peak = -Infinity, j, q, m;
    if (!(kOn >= 0) || kOn >= env.length) return tLimit;
    if (typeof floor !== 'number' || !isFinite(floor)) floor = lineLevels(vc, tOn, tLimit).floor;
    for (j = kOn; j <= kOn + span - w && j + w <= env.length; j++) { m = 0; for (q = j; q < j + w; q++) m += env[q]; m /= w; if (m > peak) peak = m; }
    if (peak === -Infinity) return tLimit;
    for (q = Math.max(0, kOn - Math.round(fps * 0.08)); q < kOn; q++) if (env[q] < floor) floor = env[q];
    if (peak - floor < 0.25) return tLimit;
    var T = floor + 0.4 * (peak - floor), kLim = Math.round((tLimit - vc.start) * fps), run = 0;
    for (q = kOn + Math.round(fps * 0.06); q < env.length && q - w + 1 < kLim; q++) { run = env[q] < T ? run + 1 : 0; if (run >= w) return vc.start + (q - w + 1) / fps; }
    return tLimit;
  }
  // up to K voice onsets between t0 and t1, in time order, or null when the curve does not cover the window or fewer
  // than half of K are found. A local maximum of the rises curve counts only when the voice is still up 80 to 160 ms
  // later (at or above floor + 0.4 * (top - floor)), so a drum hit, a breath or a tremolo wiggle does not; ranked by
  // the rise times the share of the jump still present then, the ones under a fifth of the strongest dropped, 80 ms
  // apart, never filled. With no envelope (vc.env null) it ranks by rise alone, as the old picker did.
  function onsetCandidatesIn(vc, t0, t1, K) {
    if (!vc || !vc.rises || typeof vc.start !== 'number') return null;
    var rises = vc.rises, env = vc.env, fps = vc.fps, start = vc.start;
    var k0 = Math.max(1, Math.floor((t0 - start) * fps)), k1 = Math.min(rises.length - 2, Math.ceil((t1 - start) * fps));
    if (k1 - k0 < fps * 0.3) return null;
    var lv = env ? lineLevels(vc, t0, t1) : null, gate = lv ? lv.floor + 0.4 * (lv.top - lv.floor) : 0;
    var w0 = Math.round(fps * 0.08), w1 = Math.round(fps * 0.16), peaks = [], k, q, pre, low, v;
    for (k = k0; k <= k1; k++) {
      if (!(rises[k] > rises[k - 1] && rises[k] >= rises[k + 1] && rises[k] > 0)) continue;
      if (!env) { peaks.push({ k: k, key: rises[k] }); continue; }
      if (k + w0 >= env.length) continue;
      low = Infinity; for (q = k + w0; q <= Math.min(env.length - 1, k + w1); q++) if (env[q] < low) low = env[q];
      if (low < gate) continue;
      pre = env[k]; for (q = Math.max(0, k - w0); q < k; q++) if (env[q] < pre) pre = env[q];
      v = (low - pre) / Math.max(0.05, lv.top - pre); if (v > 1) v = 1; if (v < 0) v = 0;
      peaks.push({ k: k, key: rises[k] * v });
    }
    peaks.sort(function (a, b) { return b.key - a.key; });
    var chosen = [], minKey = env && peaks.length ? 0.2 * peaks[0].key : 0, i, p;
    for (i = 0; i < peaks.length && chosen.length < K; i++) { p = peaks[i]; if (p.key < minKey) break; if (chosen.every(function (c) { return Math.abs(c.k - p.k) >= w0; })) chosen.push(p); }
    if (chosen.length < Math.ceil(K / 2)) return null;
    chosen.sort(function (a, b) { return a.k - b.k; });
    return chosen.map(function (c) { return start + c.k / fps; });
  }
  // the K strongest voice onsets between t0 and t1, in time order, or null when the curve does not cover it: the old
  // picker (rise strength alone, the gaps filled to K by halving the largest), kept for its one caller until the
  // sung-span placer replaces it
  function onsetTimesIn(curve, fps, start, t0, t1, K) {
    if (!curve || start === null) return null;
    var times = onsetCandidatesIn({ env: null, rises: curve, fps: fps, start: start }, t0, t1, K); if (!times) return null;
    while (times.length < K) { var gi = 0, gmax = -1; for (var q = 0; q < times.length; q++) { var g = (q + 1 < times.length ? times[q + 1] : t1) - times[q]; if (g > gmax) { gmax = g; gi = q; } } times.splice(gi + 1, 0, times[gi] + gmax / 2); }
    return times;
  }
  // which syllables have no onset of their own when N onsets serve K syllables (N < K): per syllable, the index of the
  // onset whose sung span it sits in; a repeat of the index before it means no onset of its own (syllable 0 always
  // has one). A missing onset inside a word (hy on the syllable before) costs 1, a missing word start 3, less up to
  // 0.5 when that span is long enough (0.6 s, spanLen[j] in seconds) to hide it. A small K by N dynamic program.
  function assignVirtual(K, N, hy, spanLen) {
    var owner = new Array(K), best = [], from = [], i, j, c;
    if (N >= K) { for (i = 0; i < K; i++) owner[i] = i; return owner; }
    if (N < 1) { for (i = 0; i < K; i++) owner[i] = 0; return owner; }
    function miss(i, j) { var len = spanLen && spanLen[j] > 0 ? spanLen[j] : 0; return (hy && hy[i - 1] ? 1 : 3) - 0.5 * Math.min(1, len / 0.6); }
    for (i = 0; i < K; i++) { best.push(new Float64Array(N)); from.push(new Int32Array(N)); for (j = 0; j < N; j++) { best[i][j] = Infinity; from[i][j] = -1; } }
    best[0][0] = 0;
    for (i = 1; i < K; i++) for (j = 0; j < N; j++) {
      if (j > 0 && best[i - 1][j - 1] < best[i][j]) { best[i][j] = best[i - 1][j - 1]; from[i][j] = j - 1; }
      c = best[i - 1][j] + miss(i, j); if (c < best[i][j]) { best[i][j] = c; from[i][j] = j; }
    }
    for (i = K - 1, j = N - 1; i >= 0; i--) { owner[i] = j; j = from[i][j]; }
    return owner;
  }
  // K sung spans {on, off} in seconds for the K syllables sung between t0 and t1, or null when the curve does not
  // cover the window, the window is under 0.3 s, or too few onsets are found (the caller spreads them evenly).
  // Each span ends where the voice drops or at the next onset; a run of syllables without an onset of their own
  // shares the sung span of the syllable before them in equal parts.
  function sungSpansIn(vc, t0, t1, K, hy) {
    if (!vc || !vc.env || !vc.rises || typeof vc.start !== 'number' || !(K >= 1) || !(t1 - t0 >= 0.3)) return null;
    var lv = lineLevels(vc, t0, t1), on = onsetCandidatesIn(vc, t0, t1, K); if (!on) return null;
    var N = on.length, off = [], len = [], out = [], i, j, lim, e, a, b, o, step;
    for (j = 0; j < N; j++) { lim = j + 1 < N ? on[j + 1] : t1; e = Math.max(on[j], Math.min(lim, sungEndAfter(vc, on[j], lim, lv.floor))); off.push(e); len.push(e - on[j]); }
    var owner = assignVirtual(K, N, hy, len);
    for (i = 0; i < K; i++) {
      o = owner[i]; a = i; b = i; while (a > 0 && owner[a - 1] === o) a--; while (b + 1 < K && owner[b + 1] === o) b++;
      step = (off[o] - on[o]) / (b - a + 1);
      out.push({ on: on[o] + (i - a) * step, off: i === b ? off[o] : on[o] + (i - a + 1) * step });
    }
    return out;
  }
// ---- end of the new text ----

// ---- synthetic envelope from the plan's worked example: start = 30.02 s so that frame k110 is 31.12 s ----
var FPS = 100, START = 30.02, env = new Float32Array(360), k, i;
function put(k0, vals) { for (var i = 0; i < vals.length; i++) env[k0 + i] = vals[i]; }
function fill(k0, k1, v) { for (var i = k0; i <= k1; i++) env[i] = v; }
fill(0, 359, 0.40);                                   // floor
put(110, [2.0]); fill(111, 159, 2.35);                // "Si": attack k110, body 2.35 through k159
put(160, [1.6, 1.1, 0.8, 0.6, 0.5, 0.45, 0.42]);     // release k160-166
put(180, [2.0]); fill(181, 219, 2.30);                // "night": attack k180, body with vibrato dips
put(190, [1.85, 1.85]); put(206, [1.85, 1.85]);       // vibrato dips (about 6 Hz, 4 dB)
put(220, [1.7, 1.1, 0.75, 0.55, 0.45, 0.42]);        // release k220-225
fill(230, 239, 0.90);                                 // breath k230-239
put(240, [2.8, 2.6, 2.2, 1.7, 1.2, 0.8, 0.5]);       // snare k240-246
put(255, [1.8]); fill(256, 269, 2.0);                 // "peace": attack k255
for (i = 0; i < 30; i++) env[270 + i] = 2.0 + 0.6 * i / 29; fill(300, 329, 2.6);   // swell to 2.6
put(330, [2.3, 1.9, 1.4, 1.0, 0.75, 0.6, 0.5, 0.45, 0.42, 0.41]);                // release k330-339, floor after

var vc = { env: env, rises: risesOf(env), fps: FPS, start: START };
function r3(x) { return Math.round(x * 1000) / 1000; }
function fmt(a) { return '[' + a.map(r3).join(', ') + ']'; }
var fails = 0;
function check(name, ok, got) { console.log((ok ? 'PASS ' : 'FAIL ') + name + '  ->  ' + got); if (!ok) fails++; }
function near(a, b, tol) { return Math.abs(a - b) <= (tol === undefined ? 0.021 : tol); }

var lv = lineLevels(vc, 31.0, 33.5);
console.log('lineLevels(31.0, 33.5) = floor ' + r3(lv.floor) + ', top ' + r3(lv.top));

var e1 = sungEndAfter(vc, 31.12, 31.82, lv.floor);
check('sungEndAfter(Si 31.12, limit 31.82) ~ 31.63', near(e1, 31.63), r3(e1));
var e2 = sungEndAfter(vc, 31.82, 32.57, lv.floor);
check('sungEndAfter(night 31.82, limit 32.57) ~ 32.23', near(e2, 32.23), r3(e2));
var e3 = sungEndAfter(vc, 32.57, 33.5, lv.floor);
check('sungEndAfter(peace 32.57, limit 33.5) ~ 33.35', near(e3, 33.35), r3(e3));
var e4 = sungEndAfter(vc, 31.12, 31.82);
check('sungEndAfter without a floor argument gives the same end', near(e4, e1, 0.001), r3(e4));
// the 0.4 factor is not on a knife edge: 0.35 and 0.45 land on the same frame for "Si" (checked by hand: T 1.08 / 1.28 both fall at k161)
var short = { env: env.subarray(0, 163), rises: risesOf(env.subarray(0, 163)), fps: FPS, start: START };
var e5 = sungEndAfter(short, 31.12, 31.82, lv.floor);
check('curve stopping mid-release (k163) is unknown -> tLimit 31.82', e5 === 31.82, r3(e5));
var e6 = sungEndAfter(vc, 30.50, 30.70, lv.floor);
check('an "onset" on the flat floor (no voice visible) -> tLimit 30.70', e6 === 30.70, r3(e6));
var e6b = sungEndAfter(vc, 32.30, 32.50, lv.floor);
check('an "onset" 20 ms before the breath, snare inside its first 150 ms: body seen, ends on the breath (32.36)', near(e6b, 32.36), r3(e6b));
var e7 = sungEndAfter(vc, 31.12, 31.40, lv.floor);
check('voice still sounding at the limit -> tLimit 31.40', e7 === 31.40, r3(e7));

var cand = onsetCandidatesIn(vc, 31.0, 33.5, 4);
check('onsetCandidatesIn K=4 ~ [31.12, 31.82, 32.57]', cand && cand.length === 3 && near(cand[0], 31.12) && near(cand[1], 31.82) && near(cand[2], 32.57), cand ? fmt(cand) : 'null');
var cand8 = onsetCandidatesIn(vc, 31.0, 33.5, 8);
check('onsetCandidatesIn K=8 -> null (3 < ceil(8/2))', cand8 === null, cand8 ? fmt(cand8) : 'null');
var candNull = onsetCandidatesIn({ env: null, rises: vc.rises, fps: FPS, start: START }, 31.0, 33.5, 4);
console.log('     env-less ranking (old behaviour) K=4 -> ' + (candNull ? fmt(candNull) : 'null') + '  (snare or breath expected here, as today)');

var old = onsetTimesInOld(vc.rises, FPS, START, 31.0, 33.5, 4), nw = onsetTimesIn(vc.rises, FPS, START, 31.0, 33.5, 4);
check('onsetTimesIn wrapper == old picker on the example', JSON.stringify(old) === JSON.stringify(nw), fmt(nw) + ' vs old ' + fmt(old));
// and on random curves, for several K, including the null cases
var seed = 12345; function rnd() { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; }
var same = 0, total = 0;
for (i = 0; i < 300; i++) {
  var n = 200 + Math.floor(rnd() * 400), rc = new Float32Array(n); for (k = 0; k < n; k++) rc[k] = rnd() < 0.08 ? rnd() * 3 : rnd() * 0.3;
  var cr = risesOf(rc), t0 = rnd() * 2, t1 = t0 + 0.2 + rnd() * 4, K = 1 + Math.floor(rnd() * 12);
  var o = onsetTimesInOld(cr, FPS, 0, t0, t1, K), w = onsetTimesIn(cr, FPS, 0, t0, t1, K);
  total++; if (JSON.stringify(o) === JSON.stringify(w)) same++;
}
check('onsetTimesIn wrapper == old picker on 300 random curves', same === total, same + '/' + total);

var own = assignVirtual(4, 3, [true, false, false, false], [0.51, 0.41, 0.78]);
check('assignVirtual(4, 3, hy=[T,F,F,F]) -> [0, 0, 1, 2] (lent has no onset)', own.join() === '0,0,1,2', own.join());
var own2 = assignVirtual(4, 3, [false, false, true, false], [0.51, 0.41, 0.78]);
check('assignVirtual with hy on syllable 2 -> [0, 1, 2, 2]', own2.join() === '0,1,2,2', own2.join());
var own3 = assignVirtual(5, 2, [false, false, false, false, false], [0.2, 2.0]);
check('assignVirtual(5, 2) no hyphens: the long span hides the missing ones -> [0, 1, 1, 1, 1]', own3.join() === '0,1,1,1,1', own3.join());
var own4 = assignVirtual(3, 3, null, null);
check('assignVirtual(3, 3) identity', own4.join() === '0,1,2', own4.join());

var sp = sungSpansIn(vc, 31.0, 33.5, 4, [true, false, false, false]);
var want = [[31.12, 31.375], [31.375, 31.63], [31.82, 32.23], [32.57, 33.35]], okSp = !!sp && sp.length === 4;
if (okSp) for (i = 0; i < 4; i++) if (!near(sp[i].on, want[i][0]) || !near(sp[i].off, want[i][1])) okSp = false;
check('sungSpansIn hy=[T,F,F,F] -> Si [31.12, 31.375], lent [31.375, 31.63], night [31.82, 32.23], peace [32.57, 33.35]', okSp, sp ? sp.map(function (x) { return '[' + r3(x.on) + ', ' + r3(x.off) + ']'; }).join(' ') : 'null');
check('sungSpansIn on a window under 0.3 s -> null', sungSpansIn(vc, 31.0, 31.2, 2, [false, false]) === null, 'null');
check('sungSpansIn with no envelope -> null', sungSpansIn({ env: null, rises: vc.rises, fps: FPS, start: START }, 31.0, 33.5, 4, []) === null, 'null');
check('sungSpansIn with too few onsets (K=8) -> null', sungSpansIn(vc, 31.0, 33.5, 8, []) === null, 'null');
var sp3 = sungSpansIn(vc, 31.0, 33.5, 3, [false, false, false]);
check('sungSpansIn K=3 -> three spans, each its own onset', !!sp3 && sp3.length === 3 && near(sp3[0].off, 31.63) && near(sp3[2].on, 32.57), sp3 ? sp3.map(function (x) { return '[' + r3(x.on) + ', ' + r3(x.off) + ']'; }).join(' ') : 'null');

console.log(fails ? fails + ' FAILED' : 'ALL PASSED');
