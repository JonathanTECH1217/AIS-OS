// The listener lines the bars up with the song's beats while it plays (so the words land) but never changes the tempo:
// a sheet set by hand at 78.5 bpm, a minute of a 78 bpm song heard: the 5-second re-lock and the final one follow the
// song's beats and the number stays 78.5; set at 156 (double) it stays 156. autoLock false turns it off.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var fps = 100;
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
function track(bpm, secs) { var N = fps * secs, full = new Float32Array(N), i, k = 0, beat = 60 / bpm; for (i = 0; i < N; i++) full[i] = 0.5; for (var t = 1.0; t < secs - 1; t += beat, k++) bump(full, t, k % 4 === 0 ? 2.0 : 1.6, 10); return full; }
function reset(bpm) { s = d.S(); s.time = '4/4'; s.bpm = bpm; s.spotify = { trackId: 'x', name: 'X · Y', durationMs: 120000, title: 'X', artist: 'Y', album: '' }; d.cur().audio = null; s.audio = { offsetSec: 1.05, lined: true, linedBy: 'user', lockedBy: '', name: '', assetId: null, forTrack: null, beats: null, locked: false, lockFit: null }; }
d.listen.env = Array.prototype.slice.call(track(78, 60)); d.listen.pairs = [0]; d.listen.t0 = 0; d.listen.latency = 0;
d.state.prefs.autoLock = undefined;
reset(78.5); d.liveLock();
var g = d.songGrid(), step = g ? (g[g.length - 1] - g[0]) / (g.length - 1) : 0;
check('the re-lock follows the song\'s beats (a grid about 0.77 s apart, bar 1 on a beat near 1 s)', !!g && Math.abs(step - 60 / 78) < 0.02 && Math.abs(g[0] - 1.0) < 0.06, g ? 'step ' + step.toFixed(3) + ' first ' + g[0] : 'no grid');
check('the tempo set by hand stays exactly 78.5', s.bpm === 78.5, s.bpm);
d.liveLock(true);
check('the final one too', s.bpm === 78.5 && !!d.songGrid(), s.bpm);
reset(156); d.liveLock(true);
g = d.songGrid(); step = g ? (g[g.length - 1] - g[0]) / (g.length - 1) : 0;
check('set at 156 (double) it stays 156, the grid at half-beats of the song', s.bpm === 156 && !!g && Math.abs(step - 30 / 78) < 0.02, s.bpm + ' step ' + step.toFixed(3));
reset(100); d.state.prefs.autoLock = false; d.liveLock(true);
check('autoLock false: nothing happens', s.bpm === 100 && !d.songGrid());
d.state.prefs.autoLock = undefined; s.audio.locked = false; s.audio.beats = null;
d.listen.env = []; d.listen.pairs = []; d.listen.t0 = null; s.spotify = null; s.bpm = 100;
document.getElementById('bpmUp').click();
check('the + button still sets it (101)', s.bpm === 101, s.bpm);
say('LOG done');
