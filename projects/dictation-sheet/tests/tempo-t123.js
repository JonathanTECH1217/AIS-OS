// tempo part, tests 1-3: tempoOf, trackBeats+beatFit, meterOf on synthetic drum tracks (100 fps, 60 s)
var d = window.__ds, fps = 100;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; if (k0 < 0) return; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
function fresh(N, f) { var e = new Float32Array(N); for (var i = 0; i < N; i++) e[i] = f; return e; }
function pad(s, n) { s = String(s); while (s.length < n) s += ' '; return s; }
// beatFit is not on the debug hook: verbatim copy of index.html lines 2258-2262
function beatFit(on, fps, beats) {
  var sorted = Array.prototype.slice.call(on).sort(function (a, b) { return a - b; }), thr = (sorted[Math.floor(sorted.length * 0.9)] || 0) * 0.3, win = Math.round(fps * 0.06), hits = 0, sum = 0;
  beats.forEach(function (t) { var c = Math.round(t * fps), bi = -1, bv = 0; for (var k = Math.max(0, c - win); k <= Math.min(on.length - 1, c + win); k++) if (on[k] > bv) { bv = on[k]; bi = k; } if (bi >= 0 && bv >= thr) { hits++; sum += Math.abs(bi - c) / fps; } });
  return { onHit: beats.length ? Math.round(100 * hits / beats.length) : 0, avgMs: hits ? Math.round(1000 * sum / hits) : 0 };
}
d.beatFit = beatFit;
function f2(x) { return (Math.round(x * 100) / 100).toFixed(2); }
// kick on 1 and 3, snare on 2 and 4, hats on every eighth. Options change one thing at a time:
// hats 'straight'|'swing'|'none', fill (snare sixteenths on beat 4 of every 8th bar), drift (2 % faster by the end),
// lowOnly (the listener's view: the low band only, kicks and nothing else), halfTime (kick 1, snare 3: the Blurry feel)
function drums(o) {
  var len = o.len || 60, N = Math.round(len * fps), full = fresh(N, 0.5), low = fresh(N, 0.4), beats = [], t = 1.0, k = 0, tau;
  while (t < len - 0.5) {
    tau = 60 / (o.bpm * (1 + (o.drift || 0) * t / len));
    beats.push(t);
    var pos = k % 4, bar = Math.floor(k / 4), fill = o.fill && bar % 8 === 7 && pos === 3;
    if (fill) { for (var q = 0; q < 4; q++) { bump(full, t + q * tau / 4, 2.3, 6); bump(low, t + q * tau / 4, 1.2, 6); } }
    else if (o.halfTime) { if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else if (pos === 2) { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); } }
    else if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); }
    else if (pos === 2) { bump(low, t, 1.8, 12); bump(full, t, 1.9, 10); }
    else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); }
    if (o.hats !== 'none' && !fill) { bump(full, t, 1.0, 4); bump(full, t + (o.hats === 'swing' ? 2 / 3 : 1 / 2) * tau, 1.0, 4); }
    t += tau; k++;
  }
  if (o.lowOnly) { var kick = fresh(N, 0.4); beats.forEach(function (b, i) { var p = i % 4; if (p === 0) bump(kick, b, 2.2, 12); else if (p === 2 && !o.halfTime) bump(kick, b, 1.8, 12); }); low = kick; full = kick; }
  return { full: full, low: low, on: d.risesOf(full), beats: beats, bpm: o.bpm, N: N, name: o.name };
}
function ratioName(found, truth) { var r = found / truth; if (Math.abs(r - 1) < 0.03) return 'BEAT'; if (Math.abs(r - 2) < 0.06) return 'DOUBLE'; if (Math.abs(r - 0.5) < 0.015) return 'HALF'; if (Math.abs(r - 4) < 0.12) return 'x4'; if (Math.abs(r - 3) < 0.09) return 'x3'; if (Math.abs(r - 1.5) < 0.05) return 'x1.5'; return 'other(' + f2(r) + ')'; }
// mean distance (ms) of tracked beats to the nearest true sixteenth, and the share within 30 ms of a true BEAT
function gridErr(tracked, truth) {
  var six = []; for (var i = 0; i + 1 < truth.length; i++) for (var q = 0; q < 4; q++) six.push(truth[i] + (truth[i + 1] - truth[i]) * q / 4); six.push(truth[truth.length - 1]);
  function near(arr, t) { var lo = 0, hi = arr.length - 1; while (hi - lo > 1) { var mid = (lo + hi) >> 1; if (arr[mid] <= t) lo = mid; else hi = mid; } return Math.min(Math.abs(arr[lo] - t), Math.abs(arr[hi] - t)); }
  var sum = 0, onBeat = 0, n = 0;
  tracked.forEach(function (t) { if (t < truth[0] - 0.02 || t > truth[truth.length - 1] + 0.02) return; n++; sum += near(six, t); if (near(truth, t) <= 0.03) onBeat++; });
  return { ms: n ? Math.round(1000 * sum / n) : -1, onBeatPct: n ? Math.round(100 * onBeat / n) : -1, n: n };
}
function brief(m) { return m ? 'per ' + m.per + ' bar ' + m.bar + ' time ' + pad(m.time, 4) + ' phase ' + m.phase + ' sure ' + f2(m.sure) + ' phaseSure ' + f2(m.phaseSure) + ' comp ' + (m.compound ? 1 : 0) + ' subSure ' + f2(m.subSure) + ' half ' + (m.half ? 1 : 0) : 'null'; }
var BPMS = [60, 70, 76, 90, 110, 128, 150, 180];
var VARS = [{ name: 'straight', hats: 'straight' }, { name: 'swing', hats: 'swing' }, { name: 'nohats', hats: 'none' }, { name: 'fill8', hats: 'straight', fill: true }, { name: 'drift2%', hats: 'straight', drift: 0.02 }, { name: 'lowOnly', hats: 'straight', lowOnly: true }, { name: 'halfTime', hats: 'straight', halfTime: true }, { name: 'halfTime+lowOnly', hats: 'straight', halfTime: true, lowOnly: true }];
say('=== TEST 1-3: tempoOf / trackBeats+beatFit / meterOf per bpm and variant (60 s tracks) ===');
say(pad('variant', 18) + pad('true', 6) + pad('tempoOf', 9) + pad('ratio', 13) + '| ' + pad('nBeats', 8) + pad('onHit%', 8) + pad('avgMs', 7) + pad('gridMs', 8) + pad('onBeat%', 9) + '| ' + 'meterOf at that tempo');
var summary = {};
VARS.forEach(function (v) {
  BPMS.forEach(function (bpm) {
    var o = {}; for (var kk in v) o[kk] = v[kk]; o.bpm = bpm;
    var tr = drums(o), truth = tr.bpm * (o.drift ? 1 + o.drift / 2 : 1);
    var found = d.tempoOf(tr.on, fps), rn = found ? ratioName(found, truth) : 'ZERO';
    summary[rn] = (summary[rn] || 0) + 1;
    var line = pad(v.name, 18) + pad(bpm, 6) + pad(found, 9) + pad(rn, 13) + '| ';
    if (found) {
      var beats = d.trackBeats(tr.on, fps, found), fit = d.beatFit(tr.on, fps, beats), ge = gridErr(beats, tr.beats);
      var m = d.meterOf(tr.on, tr.low, fps, beats, 60 / found, null);
      line += pad(beats.length, 8) + pad(fit.onHit, 8) + pad(fit.avgMs, 7) + pad(ge.ms, 8) + pad(ge.onBeatPct, 9) + '| ' + brief(m);
    }
    say(line);
  });
});
say('tempoOf outcomes over ' + (VARS.length * BPMS.length) + ' tracks: ' + JSON.stringify(summary));
// trackBeats at the TRUE tempo, for the tracker alone
say('--- trackBeats at the true tempo (straight hats): onHit / avgMs / gridMs / onBeat% / count vs truth');
BPMS.forEach(function (bpm) { var tr = drums({ bpm: bpm, hats: 'straight' }); var beats = d.trackBeats(tr.on, fps, bpm), fit = d.beatFit(tr.on, fps, beats), ge = gridErr(beats, tr.beats); say(pad(bpm, 6) + 'onHit ' + fit.onHit + '% avgMs ' + fit.avgMs + ' gridMs ' + ge.ms + ' onBeat ' + ge.onBeatPct + '% tracked ' + beats.length + ' true ' + tr.beats.length); });
// beatFit cannot tell the double: a grid at the eighths scores the same
var tr76 = drums({ bpm: 76, hats: 'straight' });
say('--- beatFit on 76 bpm straight: true beats ' + JSON.stringify(d.beatFit(tr76.on, fps, tr76.beats)) + ', true eighths ' + JSON.stringify(d.beatFit(tr76.on, fps, (function () { var e = []; tr76.beats.forEach(function (b, i) { e.push(b); if (i + 1 < tr76.beats.length) e.push((b + tr76.beats[i + 1]) / 2); }); return e; })())) + ', every other beat ' + JSON.stringify(d.beatFit(tr76.on, fps, tr76.beats.filter(function (b, i) { return i % 2 === 0; }))) + ', shifted by a sixteenth ' + JSON.stringify(d.beatFit(tr76.on, fps, tr76.beats.map(function (b) { return b + 0.197; }))));
// === TEST 3 extras: on the true beat grid AND through the pipeline (tempoOf -> trackBeats -> meterOf)
say('=== TEST 3 extras (true grid | pipeline) ===');
function both(name, tr, tau, starts) {
  var m1 = d.meterOf(tr.on, tr.low, fps, tr.beats, tau, starts);
  var found = d.tempoOf(tr.on, fps), m2 = found ? d.meterOf(tr.on, tr.low, fps, d.trackBeats(tr.on, fps, found), 60 / found, starts) : null;
  say(pad(name, 26) + 'true grid: ' + brief(m1) + (m1 ? ' r ' + JSON.stringify(m1.r, function (k, v) { return typeof v === 'number' ? Math.round(v * 100) / 100 : v; }) : ''));
  say(pad('', 26) + 'pipeline (tempoOf ' + found + ' = ' + ratioName(found, tr.truth || tr.bpm) + '): ' + brief(m2));
}
function make(len, fn) { var N = Math.round(len * fps), full = fresh(N, 0.5), low = fresh(N, 0.4), beats = []; fn(full, low, beats); return { full: full, low: low, on: d.risesOf(full), beats: beats }; }
// 3/4 at 120: kick on 1, lighter 2 and 3, hats on eighths
var w = make(60, function (full, low, beats) { var k = 0; for (var t = 1.0; t < 59; t += 0.5, k++) { beats.push(t); if (k % 3 === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.3, 10); } else { bump(full, t, 1.6, 8); bump(low, t, 0.7, 6); } bump(full, t + 0.25, 1.0, 4); } }); w.bpm = 120; both('3/4 at 120 (hats)', w, 0.5, null);
// 6/8 at a dotted-quarter pulse of 80 (tau 0.75), eighths between at thirds
var s68 = make(60, function (full, low, beats) { var k = 0; for (var t = 1.0; t < 59; t += 0.75, k++) { beats.push(t); if (k % 2 === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.3, 10); } else { bump(full, t, 1.6, 8); bump(low, t, 0.9, 6); } bump(full, t + 0.25, 1.1, 4); bump(full, t + 0.5, 1.1, 4); } }); s68.bpm = 80; both('6/8 at 80 dotted', s68, 0.75, null);
// 12/8 at 80 dotted: strong 1, medium 3, weak 2 and 4, thirds between
var s128 = make(60, function (full, low, beats) { var k = 0; for (var t = 1.0; t < 59; t += 0.75, k++) { beats.push(t); var p = k % 4; if (p === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.3, 10); } else if (p === 2) { bump(low, t, 1.8, 12); bump(full, t, 2.0, 10); } else { bump(full, t, 1.5, 8); bump(low, t, 0.8, 6); } bump(full, t + 0.25, 1.1, 4); bump(full, t + 0.5, 1.1, 4); } }); s128.bpm = 80; both('12/8 at 80 dotted', s128, 0.75, null);
// 2/4 at 120: kick, snare, kick, snare with no four-beat shape
var s24 = make(60, function (full, low, beats) { var k = 0; for (var t = 1.0; t < 59; t += 0.5, k++) { beats.push(t); if (k % 2 === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); } bump(full, t + 0.25, 1.0, 4); } }); s24.bpm = 120; both('2/4 at 120 (fold)', s24, 0.5, null);
// kicks equal on 1 and 3, snare 2 and 4; with and without phrase starts on beat 1 every 4 bars
var starts = [], eq = make(60, function (full, low, beats) { var k = 0; for (var t = 1.0; t < 59; t += 0.5, k++) { beats.push(t); var p = k % 4; if (p === 0 || p === 2) { bump(low, t, 2.0, 12); bump(full, t, 1.9, 10); } else { bump(full, t, 2.5, 8); bump(low, t, 0.8, 6); } if (k % 16 === 0 && t > 4) starts.push(t + 0.03); } }); eq.bpm = 120;
both('equal kicks, no starts', eq, 0.5, null); both('equal kicks, ' + starts.length + ' starts', eq, 0.5, starts);
var starts3 = starts.slice(0, 5); both('equal kicks, 5 starts', eq, 0.5, starts3);
// a bass line only, no drums: root on 1 loudest, notes on 1, 2.5, 3, 4
var bass = make(60, function (full, low, beats) { var k = 0; for (var t = 1.0; t < 59; t += 0.5, k++) { beats.push(t); var p = k % 4; var amp = p === 0 ? 1.9 : p === 2 ? 1.5 : p === 3 ? 1.3 : 0; if (amp) { bump(low, t, amp, 14); bump(full, t, amp, 12); } if (p === 1) { bump(low, t + 0.25, 1.3, 14); bump(full, t + 0.25, 1.3, 12); } } }); bass.bpm = 120; both('bass line only', bass, 0.5, null);
// the same bass line at 76
var bass76 = make(60, function (full, low, beats) { var k = 0, tau = 60 / 76; for (var t = 1.0; t < 59; t += tau, k++) { beats.push(t); var p = k % 4; var amp = p === 0 ? 1.9 : p === 2 ? 1.5 : p === 3 ? 1.3 : 0; if (amp) { bump(low, t, amp, 14); bump(full, t, amp, 12); } if (p === 1) { bump(low, t + tau / 2, 1.3, 14); bump(full, t + tau / 2, 1.3, 12); } } }); bass76.bpm = 76; both('bass line only at 76', bass76, 60 / 76, null);
// 20 random-accent tracks: how many come out sure?
var seed = 7; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
var sures = [], psures = [], passes = 0, ppasses = 0, halves = 0;
for (var si = 0; si < 20; si++) {
  seed = 1000 + si * 7919;
  var rt = make(60, function (full, low, beats) { for (var t = 1.0; t < 59; t += 0.5) { beats.push(t); bump(full, t, 0.8 + 2 * rnd(), 8); bump(low, t, 0.5 + 2 * rnd(), 8); } });
  var m = d.meterOf(rt.on, rt.low, fps, rt.beats, 0.5, null); sures.push(m ? f2(m.sure) : 'null'); psures.push(m ? f2(m.phaseSure) : 'null'); if (m && m.sure >= 0.5) passes++; if (m && m.phaseSure >= 0.5) ppasses++; if (m && m.half) halves++;
}
say('random accents, 20 seeds: sure ' + sures.join(' ') + ' -> ' + passes + ' would set the time signature; phaseSure ' + psures.join(' ') + ' -> ' + ppasses + ' sure of bar 1; half flagged ' + halves);
// the half path in the real pipeline: a waltz at 90 with eighths strummed on every eighth
var wz = make(60, function (full, low, beats) { var k = 0, tau = 60 / 90; for (var t = 1.0; t < 59; t += tau, k++) { beats.push(t); if (k % 3 === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.4, 10); } else { bump(full, t, 1.6, 8); bump(low, t, 0.7, 6); } bump(full, t + tau / 2, 1.3, 5); } }); wz.bpm = 90; both('waltz at 90 with eighths', wz, 60 / 90, null);
var wz2 = make(60, function (full, low, beats) { var k = 0, tau = 60 / 70; for (var t = 1.0; t < 59; t += tau, k++) { beats.push(t); if (k % 3 === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.4, 10); } else { bump(full, t, 1.6, 8); bump(low, t, 0.7, 6); } bump(full, t + tau / 2, 1.5, 5); } }); wz2.bpm = 70; both('waltz at 70 with loud eighths', wz2, 60 / 70, null);
// what the half path then does: meterOf at half the tempo
[wz, wz2].forEach(function (x, i) { var f = d.tempoOf(x.on, fps); var m1 = d.meterOf(x.on, x.low, fps, d.trackBeats(x.on, fps, f), 60 / f, null); if (m1 && m1.half) { var f2b = f / 2, b2 = d.trackBeats(x.on, fps, f2b), m2 = d.meterOf(x.on, x.low, fps, b2, 60 / f2b, null); say(pad('  half re-read ' + (i ? 'wz70' : 'wz90'), 26) + 'at ' + f2b + ': ' + brief(m2) + ' fit ' + JSON.stringify(d.beatFit(x.on, fps, b2)) + ' gridErr ' + JSON.stringify(gridErr(b2, x.beats))); } else say(pad('  half not flagged ' + (i ? 'wz70' : 'wz90'), 26) + 'tempoOf ' + f); });
// a short track: tempoOf under 15 s, and a flat one
var sh = drums({ bpm: 76, hats: 'straight', len: 14 }); say('tempoOf on 14 s: ' + d.tempoOf(sh.on, fps) + '; on 15 s: ' + d.tempoOf(drums({ bpm: 76, hats: 'straight', len: 15 }).on, fps) + '; flat: ' + d.tempoOf(new Float32Array(3000), fps) + '; meterOf on 11 beats: ' + d.meterOf(tr76.on, tr76.low, fps, tr76.beats.slice(0, 11), 60 / 76, null));
