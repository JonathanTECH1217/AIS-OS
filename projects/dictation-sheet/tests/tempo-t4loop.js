// tempo part, follow-up: gridFromSong end to end per bpm and view; the doubling flip vs hat loudness; (5a) refusal; random accents at song length
var d = window.__ds, fps = 100;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; if (k0 < 0) return; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
function fresh(N, f) { var e = new Float32Array(N); for (var i = 0; i < N; i++) e[i] = f; return e; }
function f2(x) { return (Math.round(x * 100) / 100).toFixed(2); }
function pad(s, n) { s = String(s); while (s.length < n) s += ' '; return s; }
function drums(o) {
  var len = o.len || 60, N = Math.round(len * fps), full = fresh(N, 0.5), low = fresh(N, 0.4), beats = [], t = 1.0, k = 0, tau, hat = o.hat || 1.0;
  while (t < len - 0.5) {
    tau = 60 / (o.bpm * (1 + (o.drift || 0) * t / len)); beats.push(t);
    var pos = k % 4;
    if (o.halfTime) { if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else if (pos === 2) { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); } }
    else if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); }
    else if (pos === 2) { bump(low, t, 1.8, 12); bump(full, t, 1.9, 10); }
    else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); }
    if (o.hats !== 'none') { bump(full, t, hat, 4); bump(full, t + tau / 2, hat, 4); }
    if (o.bassEighths) { bump(low, t, 1.3, 8); bump(low, t + tau / 2, 1.3, 8); }
    t += tau; k++;
  }
  if (o.lowOnly) { var kick = fresh(N, 0.4); beats.forEach(function (b, i) { var p = i % 4; if (p === 0) bump(kick, b, 2.2, 12); else if (p === 2 && !o.halfTime) bump(kick, b, 1.8, 12); }); low = kick; full = kick; }
  return { full: full, low: low, on: d.risesOf(full), voice: fresh(N, 0.4), beats: beats, bpm: o.bpm, N: N, len: len, downbeats: beats.filter(function (b, i) { return i % 4 === 0; }) };
}
function fakeTrack(tr) { d.cur().audio = { el: { paused: true, currentTime: 0, duration: tr.len, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'x.wav', peaks: null, duration: tr.len, onset: tr.on, voice: tr.voice, low: tr.low, blob: false }; }
function listener(env) { d.cur().audio = null; d.listen.env = Array.prototype.slice.call(env); d.listen.mid = []; d.listen.midOk = false; d.listen.t0 = 0; d.listen.pairs = [0]; d.listen.latency = 0; d.listen.fps = 100; }
function reset() { var s = d.S(); s.time = '4/4'; s.bpm = 100; s.audio = null; s.lines = []; s.filled = null; s.spotify = null; d.cur().audio = null; d.listen.env = []; d.listen.pairs = []; d.listen.t0 = null; return s; }
function nearest(arr, t) { var b = Infinity; arr.forEach(function (x) { b = Math.min(b, Math.abs(x - t)); }); return b; }
function ratioName(found, truth) { var r = found / truth; if (Math.abs(r - 1) < 0.03) return 'BEAT'; if (Math.abs(r - 2) < 0.06) return 'DOUBLE'; if (Math.abs(r - 0.5) < 0.015) return 'HALF'; return 'x' + f2(r); }
say('=== gridFromSong end to end per bpm and view (fresh 4/4 sheet at 100; first word 0.21 s after the 7th downbeat) ===');
say(pad('view', 22) + pad('true', 6) + pad('s.bpm', 8) + pad('ratio', 8) + pad('time', 6) + pad('bar1', 7) + pad('onDown', 8) + pad('locked', 8) + pad('fit%', 6) + 'sure/phaseSure/half | toast head');
var VIEWS = [{ name: 'file full band', mk: function (bpm, len) { return drums({ bpm: bpm, len: len }); }, how: 'file' }, { name: 'file half-time', mk: function (bpm, len) { return drums({ bpm: bpm, len: len, halfTime: true }); }, how: 'file' }, { name: 'listener low', mk: function (bpm, len) { return drums({ bpm: bpm, len: len }); }, how: 'listen' }, { name: 'listener low half-time', mk: function (bpm, len) { return drums({ bpm: bpm, len: len, halfTime: true }); }, how: 'listen' }, { name: 'listener low ht+bass8', mk: function (bpm, len) { return drums({ bpm: bpm, len: len, halfTime: true, bassEighths: true }); }, how: 'listen' }];
var tally = {};
VIEWS.forEach(function (v) {
  [60, 70, 76, 90, 110, 128, 150, 180].forEach(function (bpm) {
    var tr = v.mk(bpm, 60), s = reset(); if (v.how === 'file') fakeTrack(tr); else { s.spotify = { trackId: 'x', name: 'x', durationMs: 60000, title: 'x', artist: 'y', album: '' }; listener(tr.low); }
    var firstOn = tr.downbeats[6] + 0.21, starts = tr.downbeats.filter(function (b) { return b > 4; }).map(function (b) { return b + 0.03; });
    var f = d.gridFromSong(firstOn, starts), sa = d.sheetAudio(), rn = f && f.bpm ? ratioName(f.bpm, bpm) : 'ZERO';
    tally[v.name + ':' + rn] = (tally[v.name + ':' + rn] || 0) + 1;
    say(pad(v.name, 22) + pad(bpm, 6) + pad(s.bpm, 8) + pad(rn, 8) + pad(s.time, 6) + pad(sa.offsetSec, 7) + pad(sa.lined ? (nearest(tr.downbeats, sa.offsetSec) < 0.03 ? 'yes' : 'NO') : '-', 8) + pad(sa.locked, 8) + pad(sa.lockFit ? sa.lockFit.onHit : '-', 6) + (f && f.meter ? f2(f.meter.sure) + '/' + f2(f.meter.phaseSure) + '/' + (f.meter.half ? 1 : 0) : '-') + ' | ' + (!f ? 'not heard' : !f.bpm ? 'No steady beat found' : (f.kept ? 'Kept' : 'Tempo ' + f.bpm + (f.meterSure ? ' and ' + s.time : ' (kept ' + s.time + ')') + (f.downbeat ? ', downbeat' : '') + (f.locked ? ', locked' : ', straight'))));
  });
});
say('tally: ' + JSON.stringify(tally));
// the doubling flip: 76 bpm straight, hats louder and louder (kick 2.0, snare 2.5)
say('=== tempoOf on 76 bpm 4/4 vs hat loudness (full band) ===');
[0.6, 1.0, 1.4, 1.8, 2.0, 2.2, 2.5, 3.0].forEach(function (h) { var tr = drums({ bpm: 76, hat: h }); say('hat ' + h + ' -> ' + d.tempoOf(tr.on, fps)); });
say('=== tempoOf on the listener low band, 76 bpm, kick 1&3 + snare bleed + bass eighths of loudness b ===');
[0.6, 0.9, 1.1, 1.3, 1.6, 2.0].forEach(function (b) { var tr = drums({ bpm: 76 }); tr.beats.forEach(function (t, i) { if (i + 1 < tr.beats.length) { bump(tr.low, t, b, 8); bump(tr.low, (t + tr.beats[i + 1]) / 2, b, 8); } }); say('bass ' + b + ' -> ' + d.tempoOf(d.risesOf(tr.low), fps)); });
say('=== the same at 304 s (Blurry length) ===');
[0.6, 1.1, 1.3, 1.6].forEach(function (b) { var tr = drums({ bpm: 76, len: 304 }); tr.beats.forEach(function (t, i) { if (i + 1 < tr.beats.length) { bump(tr.low, t, b, 8); bump(tr.low, (t + tr.beats[i + 1]) / 2, b, 8); } }); say('bass ' + b + ' -> ' + d.tempoOf(d.risesOf(tr.low), fps)); });
// (5a) again, explicit: lockToSong with a half-tempo hint on the (a) lock
var tr76 = drums({ bpm: 76 }); reset(); fakeTrack(tr76); d.gridFromSong(tr76.downbeats[6] + 0.21, null); var before = d.sheetAudio().beats, off0 = d.sheetAudio().offsetSec;
var half = d.trackBeats(tr76.on, fps, 38), nd = nearest(half, off0);
d.lockToSong(true, true, true, 38);
say('(5a) half hint 38: tracked beats at 38 bpm sit ' + f2(nd) + ' s from bar 1 (' + off0 + '); window 30/38 = ' + f2(30 / 38) + ' -> ' + (d.sheetAudio().beats === before ? 'REFUSED silently (lock unchanged, bpm ' + d.S().bpm + ')' : 'relocked at ' + d.S().bpm) + '; the 38-bpm tracker chose ' + (nearest(tr76.beats.filter(function (b, i) { return i % 2 === 1; }), half[10]) < 0.03 ? 'the snares (beats 2 and 4)' : 'the kicks (beats 1 and 3)'));
// random accents at 304 s: N ~ 385 beats
var seed = 7; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
var passes = 0, mx = 0, ppasses = 0;
for (var si = 0; si < 20; si++) { seed = 1000 + si * 7919; var N = 30400, full = fresh(N, 0.5), low = fresh(N, 0.4), beats = []; for (var t = 1.0; t < 303; t += 60 / 76) { beats.push(t); bump(full, t, 0.8 + 2 * rnd(), 8); bump(low, t, 0.5 + 2 * rnd(), 8); } var m = d.meterOf(d.risesOf(full), low, fps, beats, 60 / 76, null); if (m) { mx = Math.max(mx, m.sure); if (m.sure >= 0.5) passes++; if (m.phaseSure >= 0.5) ppasses++; } }
say('random accents at 304 s, 20 seeds: max sure ' + f2(mx) + ', ' + passes + ' would set the time signature, ' + ppasses + ' sure of bar 1');
// phase at 304 s for the straight track: does bar 1 land on a true downbeat when the first word is late in the song (2:00)?
var long = drums({ bpm: 76, len: 304 }); reset(); fakeTrack(long); var fl = d.gridFromSong(long.downbeats[38] + 0.21, long.downbeats.filter(function (b) { return b > 4; }).map(function (b) { return b + 0.03; }));
say('304 s file, first word at ' + f2(long.downbeats[38] + 0.21) + ': bpm ' + d.S().bpm + ' bar 1 ' + d.sheetAudio().offsetSec + ' on a downbeat ' + (nearest(long.downbeats, d.sheetAudio().offsetSec) < 0.03) + ' sure ' + f2(fl.meter.sure) + ' phaseSure ' + f2(fl.meter.phaseSure) + ' beats ' + d.songGrid().length + ' fit ' + JSON.stringify(d.sheetAudio().lockFit));
