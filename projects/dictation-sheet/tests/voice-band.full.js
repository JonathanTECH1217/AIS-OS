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

// voice-band.js (body; voice-extract.py glues voiceIR/lowIR/bandOf/voiceOf/lowOf in front -> voice-band.full.js)
// runjs.py dumps the DOM right after load, and a render needs the main thread free, so the load event is held back by an
// image that slowserver.py (port 8799) answers after WAIT ms; every render is started at once and reports as it finishes.
// Tones at 60, 300, 1000, 1500, 2000, 3000, 5000 Hz in 1.5 s slots from 1.0, 3.0, ... 13.0 s of a 15 s buffer, at 44.1k and 48k,
// through voiceOf and lowOf: gain per tone (dB re the input RMS), the frame the 300 Hz (3.000 s) and 60 Hz (1.000 s) tones show at,
// the frame count, and stereo averaging.
var WAIT = 12000;
var hold = new Image(); hold.src = 'http://127.0.0.1:8799/slow?ms=' + WAIT; document.body.appendChild(hold);
function say(t) { __lines.push('LOG ' + t); var o = document.getElementById('out'); if (o) o.textContent += '\n' + t; }
// the box filters on paper: -3 dB edges and the worst sidelobe above 3 kHz of the voice band, the worst leak above 1 kHz of the low band
[44100, 48000].forEach(function (sr) {
  var lo3 = null, hi3 = null, worstV = -Infinity, worstVf = 0, worstL = -Infinity, worstLf = 0, f, g;
  for (f = 20; f <= 10000; f += 5) { g = theory(sr, 'voice', f); if (g >= -3 && lo3 === null) lo3 = f; if (g >= -3) hi3 = f; if (f >= 3000 && g > worstV) { worstV = g; worstVf = f; } g = theory(sr, 'low', f); if (f >= 1000 && g > worstL) { worstL = g; worstLf = f; } }
  say('THEORY @' + sr + ': voice band -3 dB from ' + lo3 + ' to ' + hi3 + ' Hz, worst leak above 3 kHz ' + worstV + ' dB at ' + worstVf + ' Hz; low band worst leak above 1 kHz ' + worstL + ' dB at ' + worstLf + ' Hz');
});
var TONES = [60, 300, 1000, 1500, 2000, 3000, 5000], AMP = 0.1, RMS = AMP / Math.SQRT2, DUR = 15;
function db(env) { var g = Math.expm1(env) / 100 / RMS; return g > 0 ? Math.round(20 * Math.log10(g) * 10) / 10 : -Infinity; }
function r2(x) { return Math.round(x * 100) / 100; }
function toneBuf(sr, chans, mode) {
  var n = Math.round(DUR * sr), oc = new OfflineAudioContext(1, 16, sr), buf = oc.createBuffer(chans, n, sr), c, i, ti;
  for (c = 0; c < chans; c++) {
    var d = buf.getChannelData(c), a = mode === 'left' && c === 1 ? 0 : AMP;
    for (ti = 0; ti < TONES.length; ti++) { var f = TONES[ti], s0 = Math.round((1 + 2 * ti) * sr), s1 = Math.round((2.5 + 2 * ti) * sr); for (i = s0; i < s1; i++) d[i] = a * Math.sin(2 * Math.PI * f * (i - s0) / sr); }
  }
  return buf;
}
function silentBuf(sr, n) { var oc = new OfflineAudioContext(1, 16, sr); return oc.createBuffer(1, n, sr); }
function theory(sr, kind, f) {
  // the box filters' own response: a box of m taps has |sin(pi f m / sr) / (m sin(pi f / sr))|
  function box(m) { var x = Math.PI * f / sr; return Math.sin(x * m) / (m * Math.sin(x)); }
  var g;
  if (kind === 'voice') g = box(Math.max(1, Math.round(sr / 3500))) - box(Math.max(1, Math.round(sr / 250)));
  else g = box(Math.max(1, Math.round(sr / 1000))) * box(Math.max(1, Math.round(sr / 800)));
  g = Math.abs(g); return g > 1e-9 ? Math.round(20 * Math.log10(g) * 10) / 10 : -Infinity;
}
var pending = 0, done = 0, lines = [];
function track(p, label, fn) { pending++; p.then(function (v) { done++; try { fn(v); } catch (e) { lines.push('FAIL ' + label + ': ' + (e && e.stack || e)); } }, function (e) { done++; lines.push('FAIL ' + label + ' rejected: ' + e); }); }
var t00 = performance.now(), envs = {};
[44100, 48000].forEach(function (sr) {
  [['voice', voiceOf], ['low', lowOf]].forEach(function (b) {
    var kind = b[0], fn = b[1];
    track(fn(toneBuf(sr, 1, 'mono')), kind + sr, function (env) {
      if (!env) { lines.push('FAIL ' + kind + 'Of null at ' + sr); return; }
      envs[kind + sr] = env;
      var rows = [];
      for (var ti = 0; ti < TONES.length; ti++) { var k = Math.round((1 + 2 * ti + 0.75) * 100); rows.push(TONES[ti] + 'Hz ' + db(env[k]) + 'dB (theory ' + theory(sr, kind, TONES[ti]) + ')'); }
      lines.push('BAND ' + kind + ' @' + sr + ': length ' + env.length + ' (want ' + Math.floor(DUR * 100) + ') done at ' + Math.round(performance.now() - t00) + ' ms | ' + rows.join(', '));
      var seq = function (k) { var s = []; for (var q = k - 2; q <= k + 2; q++) s.push(q + ':' + r2(env[q])); return s.join(' '); };
      lines.push('ALIGN ' + kind + ' @' + sr + ': 300 Hz starts at 3.000 s -> frames ' + seq(300) + ' | 60 Hz starts at 1.000 s -> frames ' + seq(100) + ' | 1 kHz starts at 5.000 s -> ' + seq(500) + ' | quiet frame 50: ' + r2(env[50]));
    });
  });
  track(voiceOf(toneBuf(sr, 2, 'both')), 'both' + sr, function (env) { envs['both' + sr] = env; });
  track(voiceOf(toneBuf(sr, 2, 'left')), 'left' + sr, function (env) { envs['left' + sr] = env; });
});
[[44100, 441000], [44100, 441163], [48000, 480000], [48000, 480178], [22050, 220500], [22050, 220600]].forEach(function (p) {
  var sr = p[0], n = p[1];
  track(voiceOf(silentBuf(sr, n)), 'len' + sr + '/' + n, function (env) { lines.push('LENGTH voice @' + sr + ' samples ' + n + ' duration ' + (n / sr).toFixed(4) + ' s: env ' + (env ? env.length : 'null') + ' frames, floor(duration*100) ' + Math.floor(n / sr * 100) + ', hop ' + Math.round(sr / 100) + ' -> ' + (sr / Math.round(sr / 100)).toFixed(3) + ' fps' + (Math.abs(sr / Math.round(sr / 100) - 100) > 1e-9 ? ' (NOT 100: frames drift ' + ((100 / (sr / Math.round(sr / 100)) - 1) * 300).toFixed(2) + ' s over 5 min)' : '')); });
});
track(voiceOf(silentBuf(8000, 8000 * 20 * 60 + 8000)), 'guard', function (env) { lines.push('GUARD 20 min + 1 s at 8 kHz -> ' + (env === null ? 'null (as documented)' : env.length + ' frames')); });
track(voiceOf({ length: 0, duration: 0, sampleRate: 48000, numberOfChannels: 1 }), 'empty', function (env) { lines.push('GUARD empty -> ' + (env === null ? 'null' : env.length)); });
say('RENDERS started ' + pending + '; the load event is held ' + WAIT + ' ms');
function report() {
  say('RENDERS done ' + done + ' of ' + pending + ' at ' + Math.round(performance.now() - t00) + ' ms');
  lines.forEach(say);
  [44100, 48000].forEach(function (sr) {
    var mono = envs['voice' + sr], both = envs['both' + sr], left = envs['left' + sr], k = 575;
    if (!mono || !both || !left) { say('STEREO @' + sr + ': missing renders'); return; }
    say('STEREO voice @' + sr + ' 1 kHz slot frame ' + k + ': mono ' + r2(mono[k]) + ' (' + db(mono[k]) + ' dB), same tone both channels ' + r2(both[k]) + ' (' + db(both[k]) + ' dB), left only ' + r2(left[k]) + ' (' + db(left[k]) + ' dB) -> ' + (Math.abs(both[k] - mono[k]) < 0.01 ? 'AVERAGED' : 'NOT averaged (summed would be +6 dB)') + '; left-only is ' + (db(left[k]) - db(mono[k])).toFixed(1) + ' dB re mono (averaged: -6.0)');
  });
}
// report once every render is in, or when the hold is about to end
var poll = setInterval(function () { if (done >= pending || performance.now() - t00 > WAIT - 800) { clearInterval(poll); report(); } }, 100);
