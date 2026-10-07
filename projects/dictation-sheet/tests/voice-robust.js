// voice-robust.js (body; voice-extract.py glues the page's functions in front and writes voice-robust.full.js)
// Synthetic voice envelopes at 100 fps, floor 0.4, syllables 2.3, through onsetCandidatesIn / assignVirtual / sungSpansIn
// with the true K and hy. 100 random lines per condition. Reports onset and release error, wrong onsets, DP misplacements.
var FPS = 100, FLOOR = 0.4, TOP = 2.3;
var seed = 1;
function rnd() { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; }
function gauss() { var u = 1 - rnd(), v = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
function U(a, b) { return a + (b - a) * rnd(); }
function r1(x) { return Math.round(x * 10) / 10; }
function r3(x) { return Math.round(x * 1000) / 1000; }

// One random line: K syllables (4..12) in words of 1..3, sung 120..450 ms, words 50..350 ms apart, syllables of one word
// legato (the release of one meets the attack of the next: a dip to ~1.7 for 20 ms). Attack 30 ms, release 60 ms.
// The window is the one autoPlaceWords passes: the stamp 100..500 ms before the voice minus 0.12, the next stamp minus 0.05.
function makeLine(o) {
  var K = o.K || (4 + Math.floor(U(0, 9))), hy = [], i = 0, w, q, k;
  while (i < K) { w = Math.min(K - i, 1 + Math.floor(U(0, 3))); for (q = 0; q < w; q++) hy.push(q < w - 1); i += w; }
  var A = o.rap ? 0.02 : 0.03, R = o.rap ? 0.02 : 0.06;
  var t = 2.0 + U(0, 0.3), on = [], off = [], gapAfter = [], wordEnds = [];
  for (i = 0; i < K; i++) if (!hy[i] && i < K - 1) wordEnds.push(i);
  var specialAt = wordEnds.length ? wordEnds[Math.floor(U(0, wordEnds.length))] : -1;
  for (i = 0; i < K; i++) {
    var dur = o.rap ? 0.06 : U(0.12, 0.45);
    on.push(t); off.push(t + dur);
    var gap = o.rap ? 0.03 : (hy[i] ? 0 : U(0.05, 0.35));
    if (!hy[i] && i < K - 1) {
      if (o.extra) gap = U(0.4, 0.6);
      else if (i === specialAt && (o.breath || o.snare)) gap = U(0.3, 0.5);
    }
    gapAfter.push(gap); t += dur + gap;
  }
  var lead = o.lateStamp ? U(-0.3, 0.1) : U(0.1, 0.5);
  var stamp = on[0] - lead, nextStamp = off[K - 1] + R + U(0.3, 1.2);
  var n = Math.ceil((nextStamp + 1.0) * FPS), env = new Float32Array(n);
  for (k = 0; k < n; k++) env[k] = FLOOR;
  function put(k, v) { if (k >= 0 && k < n && v > env[k]) env[k] = v; }
  function syl(a0, a1, top, vib) {
    for (var kk = Math.floor(a0 * FPS); kk <= Math.ceil((a1 + R) * FPS); kk++) {
      var tt = kk / FPS, v;
      if (tt < a0) continue;
      if (tt < a0 + A) v = FLOOR + (top - FLOOR) * (tt - a0) / A;
      else if (tt <= a1) v = top;
      else v = top - (top - FLOOR) * (tt - a1) / R;
      if (vib && tt >= a0 + A && tt <= a1) v = top - 0.4 * (1 - Math.cos(2 * Math.PI * 6 * (tt - a0))) / 2;
      if (o.burst && tt >= a0 && tt < a0 + 0.03) v = top + 0.15;
      put(kk, v);
    }
  }
  var shapeOff = off.slice(), skip = [];
  if (o.legato) for (i = K - 2; i >= 0; i--) if (hy[i]) { shapeOff[i] = shapeOff[i + 1]; skip[i + 1] = true; }
  for (i = 0; i < K; i++) if (!skip[i]) syl(on[i], shapeOff[i], TOP, o.vibrato);
  if (o.rap) for (i = 0; i < K - 1; i++) for (k = Math.ceil(off[i] * FPS); k <= Math.floor(on[i + 1] * FPS); k++) if (env[k] < o.rapDip) env[k] = o.rapDip;
  var extras = [];
  if (o.extra) for (i = 0; i < K - 1; i++) if (!hy[i]) { var ex = off[i] + R + 0.05, exd = U(0.12, 0.2); syl(ex, ex + exd, o.extraLevel || TOP, false); extras.push(ex); }
  if (o.breath && specialAt >= 0) { var b0 = off[specialAt] + R + 0.04; for (k = Math.floor(b0 * FPS); k <= Math.ceil((b0 + 0.19) * FPS); k++) { var tb = k / FPS - b0, vb = tb < 0.02 ? FLOOR + 0.5 * tb / 0.02 : tb < 0.17 ? 0.9 : 0.9 - 0.5 * (tb - 0.17) / 0.02; put(k, vb); } }
  var snareAt = -1;
  if (o.snare && specialAt >= 0) { var g0 = off[specialAt] + R + 0.02, g1 = on[specialAt + 1] - 0.02; snareAt = U(g0, g1); for (k = Math.floor(snareAt * FPS); k <= Math.ceil((snareAt + 0.08) * FPS); k++) { var ts = k / FPS - snareAt, vs = ts < 0 ? FLOOR : ts < 0.01 ? FLOOR + 2.0 * ts / 0.01 : ts < 0.04 ? 2.4 : 2.4 - 2.0 * (ts - 0.04) / 0.04; put(k, vs); } }
  if (o.swell) { var mid = (on[0] + off[K - 1]) / 2, s0 = mid - U(0.4, 0.8), s1 = mid + U(0.4, 0.8); for (k = Math.floor((s0 - 0.1) * FPS); k <= Math.ceil((s1 + 0.1) * FPS); k++) { var tw = k / FPS, vw = tw < s0 ? FLOOR + 0.8 * (tw - s0 + 0.1) / 0.1 : tw <= s1 ? 1.2 : 1.2 - 0.8 * (tw - s1) / 0.1; put(k, vw); } }
  var leak = -1;
  if (o.leak) { leak = nextStamp - U(0.0, 0.3); syl(leak, leak + 0.25, TOP, false); }
  if (o.noise) for (k = 0; k < n; k++) env[k] += o.noise * gauss();
  return { env: env, t0: stamp - 0.12, t1: nextStamp - 0.05, K: K, hy: hy, on: on, off: off, extras: extras, snareAt: snareAt, leak: leak, lead: lead, nextStamp: nextStamp };
}

var TOL = 0.06;
function nearest(arr, t) { var b = Infinity; for (var i = 0; i < arr.length; i++) b = Math.min(b, Math.abs(arr[i] - t)); return b; }
function mean(a) { if (!a.length) return 0; var s = 0; for (var i = 0; i < a.length; i++) s += a[i]; return s / a.length; }
function maxAbs(a) { var m = 0; for (var i = 0; i < a.length; i++) m = Math.max(m, Math.abs(a[i])); return m; }

function evalCond(name, o, lines) {
  var st = { nulls: 0, syl: 0, wrong: 0, onS: [], offS: [], offAll: [], nLess: 0, nEq: 0, fp: 0, fn: 0, cands: 0, dpLines: 0, dpBad: 0, dpSyl: 0, dpSylBad: 0, virt: 0, virtOnS: [], exPicked: 0, exTotal: 0, snarePicked: 0, leakPicked: 0, first: [], firstWrong: 0 };
  for (var L = 0; L < lines; L++) {
    var ln = makeLine(o), vc = { env: ln.env, rises: risesOf(ln.env), fps: FPS, start: 0 }, K = ln.K, i, j;
    var cand = onsetCandidatesIn(vc, ln.t0, ln.t1, K), spans = sungSpansIn(vc, ln.t0, ln.t1, K, ln.hy);
    st.exTotal += ln.extras.length;
    if (!spans) { st.nulls++; continue; }
    var N = cand.length; st.cands += N; if (N < K) st.nLess++; else st.nEq++;
    // candidates against the truth (the estimate sits ~20 ms after the true onset: the middle of a 30 ms attack)
    for (j = 0; j < N; j++) {
      var d = nearest(ln.on, cand[j] - 0.02);
      if (d > 0.045) { st.fp++; if (ln.extras.length && nearest(ln.extras, cand[j] - 0.02) <= 0.045) st.exPicked++; if (ln.snareAt >= 0 && Math.abs(cand[j] - ln.snareAt) <= 0.05) st.snarePicked++; if (ln.leak >= 0 && Math.abs(cand[j] - 0.02 - ln.leak) <= 0.045) st.leakPicked++; }
    }
    for (i = 0; i < K; i++) if (nearest(cand, ln.on[i] + 0.02) > 0.045) st.fn++;
    // the DP's owners against the truth (which found onset each true syllable sits after)
    if (N < K) {
      var lv = lineLevels(vc, ln.t0, ln.t1), len = [], e, lim;
      for (j = 0; j < N; j++) { lim = j + 1 < N ? cand[j + 1] : ln.t1; e = Math.max(cand[j], Math.min(lim, sungEndAfter(vc, cand[j], lim, lv.floor))); len.push(e - cand[j]); }
      var owner = assignVirtual(K, N, ln.hy, len), bad = 0;
      for (i = 0; i < K; i++) { var tj = 0; for (j = 0; j < N; j++) if (cand[j] <= ln.on[i] + 0.045) tj = j; if (owner[i] !== tj) bad++; }
      st.dpLines++; st.dpSyl += K; st.dpSylBad += bad; if (bad) st.dpBad++;
      for (i = 0; i < K; i++) if (i > 0 && owner[i] === owner[i - 1]) { st.virt++; st.virtOnS.push(spans[i].on - ln.on[i]); }
    }
    for (i = 0; i < K; i++) {
      var eOn = spans[i].on - ln.on[i], eOff = spans[i].off - ln.off[i];
      st.syl++;
      if (Math.abs(eOn) > TOL) st.wrong++; else { st.onS.push(eOn); st.offS.push(eOff); }
      st.offAll.push(eOff);
      if (i === 0) { st.first.push(eOn); if (Math.abs(eOn) > TOL) st.firstWrong++; }
    }
  }
  var ms = function (a) { return Math.round(mean(a) * 1000); }, mabs = function (a) { return Math.round(mean(a.map(Math.abs)) * 1000); }, wx = function (a) { return Math.round(maxAbs(a) * 1000); };
  console.log('COND ' + name + ': lines ' + lines + ' null ' + st.nulls + ' | syl ' + st.syl + ' wrongOnset ' + st.wrong + ' (' + r1(100 * st.wrong / Math.max(1, st.syl)) + '%)' +
    ' | onset err ms (right ones): mean ' + ms(st.onS) + ' abs ' + mabs(st.onS) + ' worst ' + wx(st.onS) +
    ' | release err ms (right ones): mean ' + ms(st.offS) + ' abs ' + mabs(st.offS) + ' worst ' + wx(st.offS) + ' (all: abs ' + mabs(st.offAll) + ' worst ' + wx(st.offAll) + ')' +
    ' | cands ' + st.cands + ' FP ' + st.fp + ' FN ' + st.fn + ' N<K lines ' + st.nLess + ' N=K ' + st.nEq +
    ' | DP: lines ' + st.dpLines + ' with a wrong owner ' + st.dpBad + ', syllables ' + st.dpSylBad + ' of ' + st.dpSyl + ', virtual ' + st.virt + ' (their onset err abs ' + mabs(st.virtOnS) + ' worst ' + wx(st.virtOnS) + ')' +
    (st.exTotal ? ' | backing bumps ' + st.exTotal + ' picked ' + st.exPicked : '') + (o.snare ? ' | snare picked ' + st.snarePicked : '') + (o.leak ? ' | next-line onset picked ' + st.leakPicked : '') +
    ' | first syllable: mean err ' + ms(st.first) + ' worst ' + wx(st.first) + ' wrong ' + st.firstWrong);
  return st;
}

var LINES = 100;
seed = 11; evalCond('clean', {}, LINES);
seed = 12; evalCond('(a) noise sd 0.10', { noise: 0.10 }, LINES);
seed = 13; evalCond('(a) noise sd 0.25', { noise: 0.25 }, LINES);
seed = 14; evalCond('(b) vibrato 0.4 at 6 Hz', { vibrato: true }, LINES);
seed = 15; evalCond('(c) consonant burst +0.15 for 30 ms', { burst: true }, LINES);
seed = 16; evalCond('(d) backing swell floor 1.2 mid-line', { swell: true }, LINES);
seed = 17; evalCond('(e) rap 90 ms apart, closure 0.8', { rap: true, rapDip: 0.8 }, LINES);
seed = 17; evalCond('(e) rap 90 ms apart, closure 1.3', { rap: true, rapDip: 1.3 }, LINES);
seed = 17; evalCond('(e) rap 90 ms apart, closure 1.6', { rap: true, rapDip: 1.6 }, LINES);
seed = 18; evalCond('(f) breath 0.9 for 150 ms in a gap', { breath: true }, LINES);
seed = 19; evalCond('(g) snare 2.4 in a gap', { snare: true }, LINES);
seed = 20; evalCond('(h) legato words: no rise inside a word', { legato: true }, LINES);
seed = 21; evalCond('(h) legato + noise 0.10', { legato: true, noise: 0.10 }, LINES);
seed = 22; evalCond('(x) backing bumps 2.3 between words (N>K)', { extra: true }, LINES);
seed = 22; evalCond('(x) backing bumps 1.9 between words', { extra: true, extraLevel: 1.9 }, LINES);
seed = 22; evalCond('(x) backing bumps 2.5 between words', { extra: true, extraLevel: 2.5 }, LINES);
seed = 23; evalCond('(s) stamp late: 0..300 ms after the voice', { lateStamp: true }, LINES);
seed = 24; evalCond('(t) next line leaks in (0..300 ms before its stamp)', { leak: true }, LINES);
seed = 25; evalCond('all mild: noise 0.1 + vibrato + burst', { noise: 0.10, vibrato: true, burst: true }, LINES);

// null threshold: how few onsets before sungSpansIn gives up (ceil(K/2))
var ln0 = makeLine({ K: 8, legato: true }), vc0 = { env: ln0.env, rises: risesOf(ln0.env), fps: FPS, start: 0 };
var c0 = onsetCandidatesIn(vc0, ln0.t0, ln0.t1, 8);
console.log('NULL-RULE K=8 legato: found ' + (c0 ? c0.length : 'null') + ' onsets, hy ' + JSON.stringify(ln0.hy) + ' -> spans ' + (sungSpansIn(vc0, ln0.t0, ln0.t1, 8, ln0.hy) ? 'given' : 'null'));
// a flat line (voice absent) and a line with 2 of 8 onsets
var flat = new Float32Array(800); for (var q = 0; q < 800; q++) flat[q] = 0.4;
var vcf = { env: flat, rises: risesOf(flat), fps: FPS, start: 0 };
console.log('NULL-RULE flat floor: cands ' + JSON.stringify(onsetCandidatesIn(vcf, 1, 6, 6)) + ' spans ' + JSON.stringify(sungSpansIn(vcf, 1, 6, 6, [false, false, false, false, false, false])));

// TIMING: a 12 s window with K = 20
seed = 99;
var big = makeLine({ K: 20 });
// stretch: makeLine gives ~6..9 s for 20 syllables; pad the window to 12 s and the envelope to 5 minutes to see what the cost follows
var envBig = new Float32Array(30000); for (q = 0; q < envBig.length; q++) envBig[q] = q < big.env.length ? big.env[q] : 0.4;
var vcBig = { env: envBig, rises: risesOf(envBig), fps: FPS, start: 0 }, t1w = big.t0 + 12;
var tA = performance.now(), reps = 20, res;
for (q = 0; q < reps; q++) res = sungSpansIn(vcBig, big.t0, t1w, 20, big.hy);
var perCall = (performance.now() - tA) / reps;
var tB = performance.now(); for (q = 0; q < reps; q++) risesOf(envBig); var risesMs = (performance.now() - tB) / reps;
var tC = performance.now(); for (q = 0; q < reps; q++) lineLevels(vcBig, big.t0, t1w); var lvMs = (performance.now() - tC) / reps;
console.log('TIMING sungSpansIn 12 s window K=20 (env 300 s): ' + r3(perCall) + ' ms per call; risesOf on 30000 frames ' + r3(risesMs) + ' ms; lineLevels (sort of 1260 frames) ' + r3(lvMs) + ' ms; spans ' + (res ? res.length : 'null'));
var tD = performance.now(); for (q = 0; q < reps; q++) res = sungSpansIn(vcBig, big.t0, big.t0 + 30, 20, big.hy); console.log('TIMING 30 s window K=20: ' + r3((performance.now() - tD) / reps) + ' ms per call');
var K60 = 60, hy60 = []; for (q = 0; q < K60; q++) hy60.push(false);
var tE = performance.now(); for (q = 0; q < reps; q++) res = sungSpansIn(vcBig, big.t0, big.t0 + 12, K60, hy60); console.log('TIMING 12 s window K=60: ' + r3((performance.now() - tE) / reps) + ' ms per call, spans ' + (res ? res.length : 'null'));
