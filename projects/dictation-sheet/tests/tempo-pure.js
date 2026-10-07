  function risesOf(rms) {
    var n = rms.length, out = new Float32Array(n), i, v;
    for (i = 1; i < n; i++) { v = rms[i] - rms[i - 1]; out[i] = v > 0 ? v : 0; }
    for (i = 1; i < n - 1; i++) out[i] = (out[i - 1] + out[i] + out[i + 1]) / 3;
    return out;
  }
  function tempoOf(on, fps) {
    var n = on.length, mean = 0, i, L, s, x = new Float32Array(n);
    if (n < fps * 15) return 0;
    for (i = 0; i < n; i++) mean += on[i]; mean /= n;
    for (i = 0; i < n; i++) x[i] = on[i] - mean;
    function ac(L) { L = Math.round(L); if (L < 1 || L >= n) return 0; var t = 0; for (var q = L; q < n; q++) t += x[q] * x[q - L]; return t / (n - L); }
    var lo = Math.floor(fps * 60 / 200), hi = Math.ceil(fps * 60 / 60), a = [], best = 0, bestL = 0;
    for (L = lo; L <= 3 * hi; L++) a[L] = ac(L);
    for (L = lo; L <= hi; L++) { s = a[L] + 0.5 * a[2 * L] + 0.25 * a[3 * L]; if (s > best) { best = s; bestL = L; } }
    var h = Math.round(bestL / 2); if (h >= lo && a[h] + 0.5 * a[2 * h] + 0.25 * a[3 * h] > 0.75 * best) bestL = h;
    if (!bestL || best <= 0) return 0;
    // a first between-frame read at the coarse lag, so the fine window lands on the peak many beats out
    var b0 = a[bestL - 1] || 0, b1 = a[bestL], b2 = a[bestL + 1] || 0, bden = b0 - 2 * b1 + b2, bd = bden ? (b0 - b2) / (2 * bden) : 0;
    if (bd > 0.5 || bd < -0.5) bd = 0;
    var m = Math.max(1, Math.min(16, Math.floor(n / 4 / bestL))), c0 = Math.round(m * (bestL + bd)), p = c0, pv = -Infinity, ll, y;
    for (ll = c0 - 5; ll <= c0 + 5; ll++) { y = ac(ll); if (y > pv) { pv = y; p = ll; } }
    var y0 = ac(p - 1), y2 = ac(p + 1), den = y0 - 2 * pv + y2, d = den ? (y0 - y2) / (2 * den) : 0;
    if (d > 0.5 || d < -0.5) d = 0;
    return Math.round(60 * fps * m / (p + d) * 100) / 100;
  }
  function trackBeats(on, fps, bpm) {
    var n = on.length, tau = fps * 60 / bpm, tight = 100, i, j, mean = 0, sd = 0;
    for (i = 0; i < n; i++) mean += on[i]; mean /= n; for (i = 0; i < n; i++) sd += (on[i] - mean) * (on[i] - mean); sd = Math.sqrt(sd / n) || 1;
    var o = new Float32Array(n); for (i = 0; i < n; i++) o[i] = (on[i] - mean) / sd;
    var score = new Float32Array(n), back = new Int32Array(n), lo = Math.round(tau / 2), hi = Math.round(tau * 2);
    for (i = 0; i < n; i++) {
      var best = -Infinity, bj = -1;
      for (j = i - hi; j <= i - lo; j++) { if (j < 0) continue; var pen = Math.log((i - j) / tau), v = score[j] - tight * pen * pen; if (v > best) { best = v; bj = j; } }
      score[i] = o[i] + (bj >= 0 ? best : 0); back[i] = bj;
    }
    var end = n - 1, be = -Infinity; for (i = Math.max(0, n - hi); i < n; i++) if (score[i] > be) { be = score[i]; end = i; }
    var beats = []; for (i = end; i >= 0; i = back[i]) { beats.push(i / fps); if (back[i] < 0) break; }
    beats.reverse(); return beats;
  }
  function beatFit(on, fps, beats) {
    var sorted = Array.prototype.slice.call(on).sort(function (a, b) { return a - b; }), thr = (sorted[Math.floor(sorted.length * 0.9)] || 0) * 0.3, win = Math.round(fps * 0.06), hits = 0, sum = 0;
    beats.forEach(function (t) { var c = Math.round(t * fps), bi = -1, bv = 0; for (var k = Math.max(0, c - win); k <= Math.min(on.length - 1, c + win); k++) if (on[k] > bv) { bv = on[k]; bi = k; } if (bi >= 0 && bv >= thr) { hits++; sum += Math.abs(bi - c) / fps; } });
    return { onHit: beats.length ? Math.round(100 * hits / beats.length) : 0, avgMs: hits ? Math.round(1000 * sum / hits) : 0 };
  }
  var MET_SURE = 0.5;
  function zscore(v) { var n = v.length, m = 0, s = 0, i; for (i = 0; i < n; i++) m += v[i]; m /= n; for (i = 0; i < n; i++) s += (v[i] - m) * (v[i] - m); s = Math.sqrt(s / n); if (!(s > 1e-6)) return false; for (i = 0; i < n; i++) v[i] = (v[i] - m) / s; return true; }
  function lastBeatAtOrBefore(beats, t) { var lo = 0, hi = beats.length - 1, mid; if (!beats.length || beats[0] > t) return -1; while (lo < hi) { mid = (lo + hi + 1) >> 1; if (beats[mid] <= t) lo = mid; else hi = mid - 1; } return lo; }
  function meterOf(on, low, fps, beats, tau, starts) {
    var N = beats ? beats.length : 0, n = on ? on.length : 0, w = Math.round(0.05 * fps), a = new Float32Array(N), d = new Float32Array(N), i, k, c, lo, hi, v;
    if (N < 12 || !(tau > 0) || n < 2) return null;
    // 1. accents on the beats: a = the strongest onset within 50 ms (attack), d = the low band's mean level there (weight)
    for (i = 0; i < N; i++) {
      c = Math.round(beats[i] * fps); lo = Math.max(0, c - w); hi = Math.min(n - 1, c + w); if (hi < lo) lo = hi = Math.max(0, Math.min(n - 1, c));
      for (v = 0, k = lo; k <= hi; k++) if (on[k] > v) v = on[k];
      a[i] = v;
      if (low && low.length > hi) { for (v = 0, k = lo; k <= hi; k++) v += low[k]; d[i] = v / (hi - lo + 1); } else d[i] = a[i];
    }
    if (!zscore(a) || !zscore(d)) return null;
    // 2. the accents' period: autocorrelation at 2, 3, 4, 6, 8 beats; duple = 4 with its double and half, triple = 3 with its double
    var r = {}; [2, 3, 4, 6, 8].forEach(function (L) { var t = 0; for (i = L; i < N; i++) t += a[i] * a[i - L]; r[L] = t / (N - L); });
    var duple = r[4] + 0.5 * r[8] + 0.5 * r[2], triple = r[3] + 0.5 * r[6], per = duple >= triple ? 4 : 3;
    var sure = Math.max(duple, triple) > 0 ? Math.max(0, Math.min(1, Math.abs(duple - triple) * Math.sqrt(N) / 8)) : 0;
    // beats that pair up with the pairs in threes (6 above both 4 and 8, 3 against): a waltz at double tempo; unsure until re-read at half
    var half = per === 4 && r[6] >= 0.5 && r[6] > Math.max(r[4], r[8]) + 0.1 && r[3] < 0; if (half) sure = 0;
    // 3. the beat's subdivision on the frame curve: halves and quarters against thirds, read between frames
    var mean = 0, vr = 0, x = new Float32Array(n), T = tau * fps;
    for (i = 0; i < n; i++) mean += on[i]; mean /= n;
    for (i = 0; i < n; i++) { x[i] = on[i] - mean; vr += x[i] * x[i]; } vr = vr / n || 1;
    function acf(lag) { var L = Math.floor(lag), f = lag - L, t = 0, q; if (L < 1 || L + 2 >= n) return 0; for (q = L + 1; q < n; q++) t += x[q] * ((1 - f) * x[q - L] + f * x[q - L - 1]); return t / (n - L - 1) / vr; }
    var dup = Math.max(acf(T / 2), T / 4 >= 8 ? acf(T / 4) : 0), tri = Math.max(acf(T / 3), acf(2 * T / 3));
    var subSure = Math.max(0, Math.min(1, (tri - 1.5 * Math.max(dup, 0)) / 0.2)), compound = N >= 24 && subSure >= 0.5;
    // 4. the time signature and its bar in beats: 2/4 folds into 4/4; 6/8 has two beats to the bar, 12/8 four; 9/8 is written 3/4
    var time = per === 3 ? '3/4' : !compound ? '4/4' : (r[4] - r[2] >= 0.25 ? '12/8' : '6/8'), bar = per === 3 ? 3 : time === '6/8' ? 2 : 4;
    // 5. downbeat: the beat class (mod bar) carrying the most low band; the runner-up sets the margin
    var sum = [], cnt = [], m = [], phase = 0, alt = -1;
    for (k = 0; k < bar; k++) { sum[k] = 0; cnt[k] = 0; }
    for (i = 0; i < N; i++) { sum[i % bar] += d[i]; cnt[i % bar]++; }
    for (k = 0; k < bar; k++) { m[k] = sum[k] / (cnt[k] || 1); if (m[k] > m[phase]) phase = k; }
    for (k = 0; k < bar; k++) if (k !== phase && (alt < 0 || m[k] > m[alt])) alt = k;
    var phaseSure = Math.max(0, Math.min(1, (m[phase] - m[alt]) * Math.sqrt(N / bar) / 4));
    if (!low && per === 4) phaseSure = Math.min(phaseSure, 0.49); // the attack alone puts the snare's beats first
    // 6. tie-breaker between the two best classes: a line starts on its downbeat (a vote for that beat's class) or late
    // in the beat before it, as a pickup (half a vote for the next class)
    if (phaseSure < 0.5 && starts && starts.length >= 6) {
      var votes = []; for (k = 0; k < bar; k++) votes[k] = 0;
      starts.forEach(function (t) { var b = lastBeatAtOrBefore(beats, t + 0.06); if (b < 0) return; if (t - beats[b] < 0.35 * tau) votes[b % bar] += 1; else votes[(b + 1) % bar] += 0.5; });
      var vp = votes[phase], va = votes[alt];
      if (Math.max(vp, va) >= 2 * Math.min(vp, va) + 1) { if (va > vp) phase = alt; phaseSure = 0.5; }
    }
    return { per: per, bar: bar, phase: phase, phaseSure: phaseSure, sure: sure, compound: compound, subSure: subSure, time: time, half: half, r: r };
  }
  function timeFromMeter(m) { return m && m.sure >= MET_SURE && m.time ? m.time : null; }

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
