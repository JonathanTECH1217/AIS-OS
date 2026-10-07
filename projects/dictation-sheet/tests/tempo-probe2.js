var d = window.__ds, fps = 100;
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
function track(bpm, hatAmp, secs) { var N = fps * secs, full = new Float32Array(N), i, k = 0, beat = 60 / bpm; for (i = 0; i < N; i++) full[i] = 0.5; for (var t = 1.0; t < secs - 1; t += beat, k++) { var pos = k % 4; bump(full, t, pos === 0 ? 2.0 : pos === 2 ? 1.9 : 1.6, 10); bump(full, t + beat / 2, hatAmp, 6); } return full; }
function tempoOfLogged(on, fps) {
  var n = on.length, mean = 0, i, L, s, x = new Float32Array(n), log = [];
  for (i = 0; i < n; i++) mean += on[i]; mean /= n; for (i = 0; i < n; i++) x[i] = on[i] - mean;
  function ac(L) { L = Math.round(L); if (L < 1 || L >= n) return 0; var t = 0; for (var q = L; q < n; q++) t += x[q] * x[q - L]; return t / (n - L); }
  var lo = Math.floor(fps * 60 / 200), hi = Math.ceil(fps * 60 / 60), a = [], best = 0, bestL = 0;
  for (L = lo; L <= 3 * hi; L++) a[L] = ac(L);
  for (L = lo; L <= hi; L++) { s = a[L] + 0.5 * a[2 * L] + 0.25 * a[3 * L]; if (s > best) { best = s; bestL = L; } }
  log.push('coarse ' + bestL + ' best ' + best.toFixed(4));
  var h = Math.round(bestL / 2); var sh = a[h] + 0.5 * a[2 * h] + 0.25 * a[3 * h]; log.push('h ' + h + ' s(h) ' + sh.toFixed(4) + ' vs 0.75best ' + (0.75 * best).toFixed(4)); if (h >= lo && sh > 0.75 * best) bestL = h;
  var dbl = 2 * bestL, sd = a[dbl] + 0.5 * (a[2 * dbl] || 0) + 0.25 * (a[3 * dbl] || 0); log.push('after h: bestL ' + bestL + ' bpm ' + (6000 / bestL).toFixed(1) + '; dbl ' + dbl + ' s(dbl) ' + sd.toFixed(4) + ' vs 0.6best ' + (0.6 * best).toFixed(4) + ' hi ' + hi);
  if (bestL && 60 * fps / bestL > 135 && dbl <= hi && sd > 0.6 * best) bestL = dbl;
  log.push('after guard: bestL ' + bestL);
  var b0 = a[bestL - 1] || 0, b1 = a[bestL], b2 = a[bestL + 1] || 0, bden = b0 - 2 * b1 + b2, bd = bden ? (b0 - b2) / (2 * bden) : 0; if (bd > 0.5 || bd < -0.5) bd = 0;
  var m = Math.max(1, Math.min(16, Math.floor(n / 4 / bestL))), c0 = Math.round(m * (bestL + bd)), p = c0, pv = -Infinity, ll, y;
  for (ll = c0 - 5; ll <= c0 + 5; ll++) { y = ac(ll); if (y > pv) { pv = y; p = ll; } }
  var y0 = ac(p - 1), y2 = ac(p + 1), den = y0 - 2 * pv + y2, dd = den ? (y0 - y2) / (2 * den) : 0; if (dd > 0.5 || dd < -0.5) dd = 0;
  log.push('fine: m ' + m + ' c0 ' + c0 + ' p ' + p + ' -> ' + (Math.round(60 * fps * m / (p + dd) * 100) / 100));
  return log.join(' | ');
}
[[78, 1.8], [76, 2.2]].forEach(function (c) { var on = d.risesOf(track(c[0], c[1], 60)); console.log(c[0] + '/' + c[1] + ': ' + tempoOfLogged(on, fps) + ' || page tempoOf ' + d.tempoOf(on, fps)); });
