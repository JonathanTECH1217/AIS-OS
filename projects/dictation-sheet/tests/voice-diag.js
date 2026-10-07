// voice-diag.js (body; glued behind voice-fns.js by voice-extract.py as voice-diag.full.js). Why are clean onsets missed?
// (1) per missed onset: its length, whether it starts a word, what follows; (2) syllable spacing sweep; (3) the DP's
// wrong owners: was the missed onset a word start? (4) the last-syllable rule: a spurious onset at the window's end.
var FPS = 100, FLOOR = 0.4, TOP = 2.3, seed = 5;
function rnd() { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; }
function U(a, b) { return a + (b - a) * rnd(); }
function nearest(arr, t) { var b = Infinity; for (var i = 0; i < arr.length; i++) b = Math.min(b, Math.abs(arr[i] - t)); return b; }
// the same shapes as voice-robust.js: attack 30 ms, release 60 ms, legato inside a word
function build(on, off, hy, durOverride) {
  var K = on.length, n = Math.ceil((off[K - 1] + 2) * FPS), env = new Float32Array(n), i, k;
  for (k = 0; k < n; k++) env[k] = FLOOR;
  for (i = 0; i < K; i++) for (k = Math.floor(on[i] * FPS); k <= Math.ceil((off[i] + 0.06) * FPS); k++) {
    var tt = k / FPS, v; if (tt < on[i]) continue;
    if (tt < on[i] + 0.03) v = FLOOR + (TOP - FLOOR) * (tt - on[i]) / 0.03; else if (tt <= off[i]) v = TOP; else v = TOP - (TOP - FLOOR) * (tt - off[i]) / 0.06;
    if (k < n && v > env[k]) env[k] = v;
  }
  return env;
}
function randomLine(minDur, maxDur) {
  var K = 4 + Math.floor(U(0, 9)), hy = [], i = 0, w, q; while (i < K) { w = Math.min(K - i, 1 + Math.floor(U(0, 3))); for (q = 0; q < w; q++) hy.push(q < w - 1); i += w; }
  var t = 2.0, on = [], off = [], gap = [];
  for (i = 0; i < K; i++) { var d = U(minDur, maxDur); on.push(t); off.push(t + d); var g = hy[i] ? 0 : U(0.05, 0.35); gap.push(g); t += d + g; }
  return { K: K, hy: hy, on: on, off: off, gap: gap, t0: on[0] - U(0.1, 0.5) - 0.12, t1: off[K - 1] + 0.06 + U(0.3, 1.2) - 0.05 };
}
// (1) missed onsets by kind, 300 clean lines
var kinds = { 'word start, next is a gap': [0, 0], 'word start, next is legato': [0, 0], 'continuation, next is a gap': [0, 0], 'continuation, next is legato': [0, 0] }, durMissed = [], durAll = 0, tot = 0, missShort = 0, missLong = 0;
var dpWrongWordStart = 0, dpWrongCont = 0, dpLines = 0, dpBadLines = 0;
for (var L = 0; L < 300; L++) {
  var ln = randomLine(0.12, 0.45), env = build(ln.on, ln.off, ln.hy), vc = { env: env, rises: risesOf(env), fps: FPS, start: 0 };
  var cand = onsetCandidatesIn(vc, ln.t0, ln.t1, ln.K); if (!cand) continue;
  var missedKinds = [];
  for (var i = 0; i < ln.K; i++) {
    var kind = (i > 0 && ln.hy[i - 1] ? 'continuation' : 'word start') + ', next is ' + (ln.hy[i] ? 'legato' : 'a gap'), dur = ln.off[i] - ln.on[i];
    kinds[kind][1]++; tot++;
    if (nearest(cand, ln.on[i] + 0.02) > 0.045) { kinds[kind][0]++; durMissed.push(Math.round(dur * 1000)); missedKinds.push(kind); if (dur < 0.17) missShort++; else missLong++; }
  }
  if (cand.length < ln.K) {
    var lv = lineLevels(vc, ln.t0, ln.t1), len = [], j, e, lim;
    for (j = 0; j < cand.length; j++) { lim = j + 1 < cand.length ? cand[j + 1] : ln.t1; e = Math.max(cand[j], Math.min(lim, sungEndAfter(vc, cand[j], lim, lv.floor))); len.push(e - cand[j]); }
    var owner = assignVirtual(ln.K, cand.length, ln.hy, len), bad = 0;
    for (i = 0; i < ln.K; i++) { var tj = 0; for (j = 0; j < cand.length; j++) if (cand[j] <= ln.on[i] + 0.045) tj = j; if (owner[i] !== tj) bad++; }
    dpLines++; if (bad) { dpBadLines++; missedKinds.forEach(function (mk) { if (mk.indexOf('word start') === 0) dpWrongWordStart++; else dpWrongCont++; }); }
  }
}
durMissed.sort(function (a, b) { return a - b; });
console.log('MISSED by kind (missed/all): ' + JSON.stringify(kinds) + ' | total ' + tot + ' | missed lengths ms: min ' + durMissed[0] + ' median ' + durMissed[durMissed.length >> 1] + ' max ' + durMissed[durMissed.length - 1] + ' | under 170 ms ' + missShort + ', 170 ms or more ' + missLong);
console.log('DP wrong-owner lines ' + dpBadLines + ' of ' + dpLines + ' N<K lines; the missed onsets on those lines were word starts ' + dpWrongWordStart + ' times, continuations ' + dpWrongCont + ' times');
// (2) spacing sweep: 8 equal syllables S ms apart, each sung for S-30 ms, a 30 ms dip between (to `dip`), one word (hy) or separate words
[[0.4, 'gap to the floor'], [1.6, 'legato dip to 1.6']].forEach(function (dp) {
  var row = [];
  [0.09, 0.12, 0.15, 0.17, 0.2, 0.25, 0.3, 0.4].forEach(function (S) {
    var K = 8, on = [], off = [], hy = [], i; for (i = 0; i < K; i++) { on.push(2 + i * S); off.push(2 + i * S + S - 0.03); hy.push(false); }
    var env = build(on, off, hy), k; if (dp[0] > FLOOR) for (i = 0; i < K - 1; i++) for (k = Math.floor(off[i] * FPS); k <= Math.ceil(on[i + 1] * FPS); k++) if (env[k] < dp[0]) env[k] = dp[0];
    var vc = { env: env, rises: risesOf(env), fps: FPS, start: 0 }, c = onsetCandidatesIn(vc, 2 - 0.3 - 0.12, off[K - 1] + 0.5, K);
    row.push(Math.round(S * 1000) + 'ms:' + (c ? c.length : 'null'));
  });
  console.log('SPACING (' + dp[1] + ') onsets found of 8: ' + row.join(' '));
});
// (3) the v factor for a stream: print the keys of a 150 ms stream
(function () {
  var K = 6, on = [], off = [], hy = [], i; for (i = 0; i < K; i++) { on.push(2 + i * 0.15); off.push(2 + i * 0.15 + 0.12); hy.push(false); }
  var env = build(on, off, hy), vc = { env: env, rises: risesOf(env), fps: FPS, start: 0 }, lv = lineLevels(vc, 1.6, off[K - 1] + 0.5), gate = lv.floor + 0.4 * (lv.top - lv.floor), keys = [];
  for (i = 0; i < K; i++) { var k = Math.round(on[i] * 100) + 2, low = Infinity, pre = vc.env[k], q; for (q = k + 8; q <= k + 16; q++) low = Math.min(low, vc.env[q]); for (q = k - 8; q < k; q++) pre = Math.min(pre, vc.env[q]); var v = Math.max(0, Math.min(1, (low - pre) / Math.max(0.05, lv.top - pre))); keys.push('syl' + i + ' rise ' + vc.rises[k].toFixed(2) + ' pre ' + pre.toFixed(2) + ' low80-160 ' + low.toFixed(2) + (low < gate ? ' <gate' : '') + ' v ' + v.toFixed(2) + ' key ' + (vc.rises[k] * v).toFixed(3)); }
  console.log('STREAM 150 ms apart, sung 120 ms, gate ' + gate.toFixed(2) + ': ' + keys.join(' | '));
})();
// (5) sungEndAfter on its own
(function () {
  var env = build([2.0], [2.5], [false]), vc = { env: env, rises: risesOf(env), fps: FPS, start: 0 };
  console.log('ENDAFTER one syllable 2.0..2.5 (release ramp 60 ms): tLimit 3.0 -> ' + sungEndAfter(vc, 2.0, 3.0, 0.4) + ' (floor given), ' + sungEndAfter(vc, 2.0, 3.0) + ' (floor found); tLimit 2.3 (held past it) -> ' + sungEndAfter(vc, 2.0, 2.3, 0.4) + '; onset off the curve (t=90) -> ' + sungEndAfter(vc, 90, 91, 0.4) + '; 40 ms syllable -> ' + (function () { var e2 = build([2.0], [2.04], [false]); return sungEndAfter({ env: e2, rises: null, fps: FPS, start: 0 }, 2.0, 3.0, 0.4); })());
  var quiet = new Float32Array(400), k; for (k = 0; k < 400; k++) quiet[k] = 0.4; for (k = 200; k < 250; k++) quiet[k] = 0.6;
  console.log('ENDAFTER a syllable only 0.2 above the floor (under 0.25): -> ' + sungEndAfter({ env: quiet, fps: FPS, start: 0 }, 2.0, 3.0, 0.4) + ' (= tLimit 3, "not visible")');
  // a backing swell through the whole line: the line floor rises with it, the releases are still found
  var on = [2.0, 2.5, 3.0, 3.5], off = [2.3, 2.8, 3.3, 3.8], hy = [false, false, false, false], e3 = build(on, off, hy);
  for (k = 150; k < 450; k++) if (e3[k] < 1.2) e3[k] = 1.2;
  var vc3 = { env: e3, rises: risesOf(e3), fps: FPS, start: 0 }, lv3 = lineLevels(vc3, 1.6, 4.5), sp3 = sungSpansIn(vc3, 1.6, 4.5, 4, hy);
  console.log('SWELL whole line at 1.2: lineLevels ' + JSON.stringify(lv3) + ' spans ' + JSON.stringify(sp3 && sp3.map(function (s) { return [Math.round(s.on * 100) / 100, Math.round(s.off * 100) / 100]; })) + ' (true offs 2.3 2.8 3.3 3.8)');
  // the swell only under the middle two syllables: the floor stays 0.4 and those two hold to the next onset
  var e4 = build(on, off, hy); for (k = 240; k < 340; k++) if (e4[k] < 1.2) e4[k] = 1.2;
  var vc4 = { env: e4, rises: risesOf(e4), fps: FPS, start: 0 }, sp4 = sungSpansIn(vc4, 1.6, 4.5, 4, hy);
  console.log('SWELL mid-line 2.4..3.4 at 1.2: lineLevels ' + JSON.stringify(lineLevels(vc4, 1.6, 4.5)) + ' spans ' + JSON.stringify(sp4 && sp4.map(function (s) { return [Math.round(s.on * 100) / 100, Math.round(s.off * 100) / 100]; })) + ' (true offs 2.3 2.8 3.3 3.8)');
})();
// (4) a spurious onset at the window's end always takes the last syllable (assignVirtual backtracks from best[K-1][N-1])
(function () {
  var on = [2.0, 2.3, 2.6, 2.9], off = [2.2, 2.5, 2.8, 3.1], hy = [false, false, false, false], env = build(on, off, hy), k;
  // a drum hit 2.4 for 40 ms at 3.6 s, then the next line at 3.7 (inside the window that ends at 3.9)
  for (k = 360; k < 364; k++) env[k] = 2.4; for (k = 370; k < 400; k++) env[k] = 2.3;
  var vc = { env: env, rises: risesOf(env), fps: FPS, start: 0 }, c = onsetCandidatesIn(vc, 1.6, 3.9, 4), sp = sungSpansIn(vc, 1.6, 3.9, 4, hy);
  console.log('END-RULE 4 syllables at 2.0/2.3/2.6/2.9, a hit at 3.6 and the next line at 3.7 inside the window: candidates ' + JSON.stringify(c) + ' -> spans ' + JSON.stringify(sp && sp.map(function (s) { return [Math.round(s.on * 100) / 100, Math.round(s.off * 100) / 100]; })));
  var c5 = onsetCandidatesIn(vc, 1.6, 3.9, 5), o = assignVirtual(4, 5, hy, [0.2, 0.2, 0.2, 0.2, 0.1]);
  console.log('END-RULE with K=5 asked: ' + JSON.stringify(c5) + '; assignVirtual(K=4, N=5) owner ' + JSON.stringify(Array.prototype.slice.call(o)));
})();
