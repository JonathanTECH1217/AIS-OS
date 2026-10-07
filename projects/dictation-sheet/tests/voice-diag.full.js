// index.html line 2121
  function risesOf(rms) {
    var n = rms.length, out = new Float32Array(n), i, v;
    for (i = 1; i < n; i++) { v = rms[i] - rms[i - 1]; out[i] = v > 0 ? v : 0; }
    for (i = 1; i < n - 1; i++) out[i] = (out[i - 1] + out[i] + out[i + 1]) / 3;
    return out;
  }
// index.html line 2129
  function voiceIR(ctx) {
    var sr = ctx.sampleRate, nh = Math.max(1, Math.round(sr / 3500)), nl = Math.max(1, Math.round(sr / 250)), off = (nl - nh) >> 1, i;
    var ir = ctx.createBuffer(1, nl, sr), d = ir.getChannelData(0);
    for (i = 0; i < nl; i++) d[i] = -1 / nl;
    for (i = 0; i < nh; i++) d[off + i] += 1 / nh;
    return ir;
  }
// index.html line 2138
  function lowIR(ctx) {
    var sr = ctx.sampleRate, n1 = Math.max(1, Math.round(sr / 1000)), n2 = Math.max(1, Math.round(sr / 800)), len = n1 + n2 - 1, i, j;
    var ir = ctx.createBuffer(1, len, sr), d = ir.getChannelData(0);
    for (i = 0; i < n1; i++) for (j = 0; j < n2; j++) d[i + j] += 1 / (n1 * n2);
    return ir;
  }
// index.html line 2147
  async function bandOf(ab, makeIR) {
    try {
      var OAC = window.OfflineAudioContext || window.webkitOfflineAudioContext;
      if (!OAC || !ab || !ab.length || ab.duration > 20 * 60) return null;
      var sr = ab.sampleRate, hop = Math.round(sr / 100);
      // 10 ms of slack after the track covers any impulse's delay (the longest is 4 ms); the frame count stays the track's own
      var ctx = new OAC(1, ab.length + hop, sr), src = ctx.createBufferSource(), conv = ctx.createConvolver(), ir = makeIR(ctx), skip = ir.length >> 1;
      conv.channelCount = 1; conv.channelCountMode = 'explicit'; conv.normalize = false; conv.buffer = ir;
      src.buffer = ab; src.connect(conv); conv.connect(ctx.destination); src.start(0);
      var out = (await ctx.startRendering()).getChannelData(0), n = Math.min(Math.floor(ab.length / hop), Math.floor((out.length - skip) / hop)), env = new Float32Array(n), i, j, k, acc;
      for (i = 0; i < n; i++) { acc = 0; for (j = skip + i * hop, k = j + hop; j < k; j++) acc += out[j] * out[j]; env[i] = Math.log1p(100 * Math.sqrt(acc / hop)); }
      return env;
    } catch (e) { return null; }
  }
// index.html line 2161
  function voiceOf(ab) { return bandOf(ab, voiceIR); }
// index.html line 2162
  function lowOf(ab) { return bandOf(ab, lowIR); }
// index.html line 2850
  function pctl(arr, k0, k1, q) {
    k0 = Math.max(0, Math.floor(k0) || 0); k1 = Math.min(arr.length, Math.ceil(k1) || 0); if (k1 <= k0) return 0;
    var s = Array.prototype.slice.call(arr, k0, k1).sort(function (a, b) { return a - b; });
    return s[Math.min(s.length - 1, Math.floor(s.length * q))];
  }
// index.html line 2857
  function lineLevels(vc, t0, t1) {
    if (!vc || !vc.env) return { floor: 0, top: 0 };
    var k0 = Math.floor((t0 - 0.3 - vc.start) * vc.fps), k1 = Math.ceil((t1 + 0.3 - vc.start) * vc.fps) + 1;
    return { floor: pctl(vc.env, k0, k1, 0.1), top: pctl(vc.env, k0, k1, 0.9) };
  }
// index.html line 2868
  function sungEndAfter(vc, tOn, tLimit, floor) {
    if (!vc || !vc.env || typeof vc.start !== 'number') return tLimit;
    var env = vc.env, fps = vc.fps, kOn = Math.round((tOn - vc.start) * fps), w = Math.max(1, Math.round(fps * 0.05)), span = Math.round(fps * 0.15), peak = -Infinity, kPk = kOn, j, q, m;
    if (!(kOn >= 0) || kOn >= env.length) return tLimit;
    if (typeof floor !== 'number' || !isFinite(floor)) floor = lineLevels(vc, tOn, tLimit).floor;
    for (j = kOn; j <= kOn + span - w && j + w <= env.length; j++) { m = 0; for (q = j; q < j + w; q++) m += env[q]; m /= w; if (m > peak) { peak = m; kPk = j; } }
    if (peak === -Infinity) return tLimit;
    for (q = Math.max(0, kOn - Math.round(fps * 0.08)); q < kOn; q++) if (env[q] < floor) floor = env[q];
    if (peak - floor < 0.25) return tLimit;
    // the drop is looked for after the body, never inside the attack that leads up to it
    var T = floor + 0.4 * (peak - floor), kLim = Math.round((tLimit - vc.start) * fps), run = 0;
    for (q = Math.max(kPk, kOn + Math.round(fps * 0.06)); q < env.length && q - w + 1 < kLim; q++) { run = env[q] < T ? run + 1 : 0; if (run >= w) return vc.start + (q - w + 1) / fps; }
    return tLimit;
  }
// index.html line 2887
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
// index.html line 2915
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
// index.html line 2933
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
// index.html line 2983
  function evenSpans(t0, t1, K) {
    var out = [], step = (t1 - t0) * 0.85 / K, barSec = slotsPerBar(S().time) * audioNominalSlotSec(), i;
    for (i = 0; i < K; i++) out.push({ on: t0 + i * step, off: null });
    for (i = 0; i < K; i++) out[i].off = i + 1 < K ? out[i + 1].on : Math.min(t1, out[i].on + barSec);
    return out;
  }
// index.html line 2992
  function lrcWindows(pairs, lrc, lastLen) {
    var out = [], dur = songMeta().duration || 0, i = 0, k;
    while (i < pairs.length) {
      var t0 = lrc[pairs[i].lrcIdx].t, w = { t0: t0, t1: 0, lis: [] }, last = pairs[i].lrcIdx, nx = null;
      while (i < pairs.length && lrc[pairs[i].lrcIdx].t - t0 <= 0.05) { w.lis.push(pairs[i].li); last = pairs[i].lrcIdx; i++; }
      for (k = last + 1; k < lrc.length; k++) if (lrc[k].t - t0 > 0.05) { nx = lrc[k].t; break; }
      var t1 = nx !== null ? nx : t0 + lastLen;
      if (t1 - t0 > 12) t1 = t0 + 12; if (dur > 0 && t1 > dur) t1 = dur; if (t1 - t0 < 0.4) t1 = t0 + 0.4;
      w.t1 = t1; out.push(w);
    }
    return out;
  }

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
