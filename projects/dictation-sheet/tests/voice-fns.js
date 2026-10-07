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
