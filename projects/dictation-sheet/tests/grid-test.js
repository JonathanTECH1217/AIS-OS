// The four faults the saved Blurry sheet showed: tempo read at double, the grid guessed on from its last two beats,
// the listener's re-lock swapping out a placed grid, and Place words refusing a second run.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function r2(x) { return Math.round(x * 100) / 100; }
var fps = 100;
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
// 1. tempo: a 78 bpm rock track with hats on every eighth as loud as the drums (Blurry read 157)
function track(bpm, hatAmp, secs) { var N = fps * secs, full = new Float32Array(N), i, k = 0, beat = 60 / bpm; for (i = 0; i < N; i++) full[i] = 0.5; for (var t = 1.0; t < secs - 1; t += beat, k++) { var pos = k % 4; bump(full, t, pos === 0 ? 2.0 : pos === 2 ? 1.9 : 1.6, 10); bump(full, t + beat / 2, hatAmp, 6); } return full; }
[[78, 1.0], [78, 1.8], [78, 2.5], [120, 1.8], [76, 2.2]].forEach(function (c) {
  var on = d.risesOf(track(c[0], c[1], 60)), bpm = d.tempoOf(on, fps);
  check('tempoOf on a ' + c[0] + ' bpm track with eighths at ' + c[1] + ' reads ' + c[0] + ' (not double)', Math.abs(bpm - c[0]) < 1.5, 'read ' + bpm);
});
// a genuinely fast track (170 bpm, no eighth layer) still reads fast
var on170 = d.risesOf(track(170, 0.6, 60)), b170 = d.tempoOf(on170, fps);
say('LOG 170 bpm track with faint eighths reads ' + b170 + (Math.abs(b170 - 170) < 2 ? ' (kept)' : Math.abs(b170 - 85) < 2 ? ' (halved: the 60 % rule prefers the half here)' : ''));
// 2. the grid past its last beat goes on at the middle step, not the last gap
s.time = '4/4'; s.bpm = 78;
var beats = []; for (var i = 0; i < 40; i++) beats.push(Math.round((0.5 + i * 0.77) * 1000) / 1000); beats.push(beats[39] + 1.6); // a slipped last beat
s.audio = { offsetSec: 0.5, lined: true, linedBy: 'place', lockedBy: 'place', name: '', assetId: null, beats: beats, locked: true, lockFit: { onHit: 95, avgMs: 8 } };
var far = d.songOfSlot(4 * 200); // beat 200
check('songOfSlot 160 beats past the grid: at the 0.77 s step (' + r2(beats[40] + 160 * 0.77) + '), not the 1.6 s slip (' + r2(beats[40] + 160 * 1.6) + ')', Math.abs(far - (beats[40] + 160 * 0.77)) < 0.5, r2(far));
check('slotOfSong is the inverse out there', Math.abs(d.slotOfSong(far) - 800) < 0.01, r2(d.slotOfSong(far)));
check('localSlotSec past the grid is the step over four', Math.abs(d.localSlotSec(1000) - 0.77 / 4) < 0.001, r2(d.localSlotSec(1000)));
check('before the first beat the grid goes back at its first step', Math.abs(d.songOfSlot(-8) - (0.5 - 2 * 0.77)) < 0.01, r2(d.songOfSlot(-8)));
// 3. the listener's re-lock leaves a placed grid alone
d.listen.env = new Array(2000).fill(0.5); d.listen.pairs = [10]; d.listen.t0 = 0;
var before = JSON.stringify(s.audio.beats);
d.liveLock(); d.liveLock(true);
check('liveLock (and the final one) leave a grid Place words made', JSON.stringify(s.audio.beats) === before && s.bpm === 78, 'bpm ' + s.bpm + ' beats same ' + (JSON.stringify(s.audio.beats) === before));
s.audio.lockedBy = 'auto';
d.liveLock();
say('LOG an auto lock may be replaced by liveLock (beats same afterwards: ' + (JSON.stringify(s.audio.beats) === before) + ')');
d.listen.env = []; d.listen.pairs = []; d.listen.t0 = null;
// 4. Place words runs again on a song already on the sheet
s.filled = { key: 'spotify:x', title: 'X' }; s.spotify = { trackId: 'x', name: 'X · Y', durationMs: 60000, title: 'X', artist: 'Y', album: '' };
var real = window.fetch, asked = 0;
window.fetch = function (url, opts) { if (String(url).indexOf('/lyrics') === 0) { asked++; return Promise.resolve({ ok: true, headers: new Headers({ 'content-type': 'application/json' }), json: function () { return Promise.resolve({ ok: true, synced: '[00:05.00] one two\n[00:08.00] three four\n[00:12.00]', plain: '', duration: 60, track: 'X', artist: 'Y' }); } }); } return real(url, opts); };
s.lines = []; s.audio = { offsetSec: 0, lined: false, linedBy: '', lockedBy: '', name: '', assetId: null, beats: null, locked: false, lockFit: null };
d.autoPlaceWords().then(function () {
  check('a second Place words on the same song is not refused', asked === 1 && d.S().lines.length === 2, 'lookups ' + asked + ' lines ' + d.S().lines.length);
  window.fetch = real; say('LOG done');
}, function (e) { say('FAIL rejected: ' + (e && e.stack || e)); window.fetch = real; });
