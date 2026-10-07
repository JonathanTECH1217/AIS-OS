// quantizer-marker.js: the heard-song path (beat curve present, gridFromSong sets bar 1 on the downbeat before the first
// sung word) with a symbol-only "♪" LRC line before the first sung line. Setup copied from e2e2-test.js.
// Run: PROFILE=prof-quantizer BUDGET=20000 python pagecheck.py stage.html quantizer-marker.js
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var fps = 100, N = fps * 60;
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
function makeSong() {
  var full = new Float32Array(N), low = new Float32Array(N), voice = new Float32Array(N), i;
  for (i = 0; i < N; i++) { full[i] = 0.5; low[i] = 0.4; voice[i] = 0.4; }
  var k = 0;
  for (var t = 1.0; t < 59; t += 0.5, k++) { var pos = k % 4; if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else if (pos === 2) { bump(low, t, 1.8, 12); bump(full, t, 1.9, 10); } else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); } }
  return { full: full, low: low, voice: voice };
}
function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), k; for (k = k0; k < k1 + 6 && k < env.length; k++) { var v; if (k < k0 + 3) v = 0.4 + 1.9 * (k - k0 + 1) / 3; else if (k < k1) v = 2.3 + 0.05 * Math.sin(k); else v = 2.3 - 1.9 * (k - k1 + 1) / 6; if (v > env[k]) env[k] = v; } }
var spans = [[20.10, 20.35], [20.40, 20.60], [20.85, 21.35], [21.60, 21.80], [21.85, 22.05], [22.35, 23.20], [24.60, 24.85], [24.90, 25.10], [25.35, 26.30]];
var lrcText = '', realFetch = window.fetch;
window.fetch = function (url, opts) { if (String(url).indexOf('/lyrics') === 0) return Promise.resolve({ ok: true, headers: new Headers({ 'content-type': 'application/json' }), json: function () { return Promise.resolve({ ok: true, synced: lrcText, plain: '', duration: 60, track: 'Test Song', artist: 'Tester' }); } }); return realFetch(url, opts); };
var n = 0;
function setup(lrc) {
  lrcText = lrc;
  var s = d.S(); s.time = '4/4'; s.bpm = 100; s.audio = null; s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null;
  s.spotify = { trackId: 'fake-' + (++n), name: 'Test Song · Tester', durationMs: 60000, title: 'Test Song', artist: 'Tester', album: '' };
  var song = makeSong(); spans.forEach(function (p) { sing(song.voice, p[0], p[1]); });
  d.cur().audio = { el: { paused: true, currentTime: 0, duration: 60, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'test.wav', peaks: null, duration: 60, onset: d.risesOf(song.full), voice: song.voice, low: song.low, blob: false };
}
function report(label) {
  var s = d.S(), sa = d.sheetAudio(), spb = d.slotsPerBar(s.time), out = [];
  say('LOG ' + label + ': bpm ' + s.bpm + ' time ' + s.time + ' offsetSec ' + sa.offsetSec + ' locked ' + sa.locked);
  s.lines.forEach(function (l, li) { if (l.kind !== 'line') return; var ord = d.barOrdinal(s, li, 0); var row = { ord: ord, bars: l.bars, syls: d.sortedSyls(l).map(function (y) { return { t: y.text, g: ord * spb + y.pos, len: d.lenSlots(y), song: Math.round(d.slotOfSong(0) * 0) }; }) }; out.push(row); say('LOG   line ' + li + ' ord ' + ord + ' bars ' + l.bars + ': ' + row.syls.map(function (y) { return y.t + '@' + y.g + 'x' + y.len; }).join(' ')); });
  say('LOG ' + label + ' toast: ' + document.getElementById('toast').textContent);
  return out;
}
setup('[00:19.95] Silent night, holy night\n[00:24.45] All is calm\n');
d.autoPlaceWords().then(function () {
  var rows = report('without a marker line'), first = rows[0].syls[0];
  check('control: first word on slot 9 (beat 3 of bar 1, bar 1 at 19.0)', first.g === 9 && Math.abs(d.sheetAudio().offsetSec - 19.0) < 0.03, 'slot ' + first.g + ' offsetSec ' + d.sheetAudio().offsetSec);
  setup('[00:15.00] ♪\n[00:19.95] Silent night, holy night\n[00:24.45] All is calm\n');
  return d.autoPlaceWords();
}).then(function () {
  var rows = report('with a "♪" line before'), sung = rows[1], sa = d.sheetAudio(), spb = 16;
  var songSlots = [20.10, 20.40, 20.85, 21.60, 21.85, 22.35].map(function (t) { return Math.round(d.slotOfSong(t)); });
  say('LOG song slots of the first line\'s syllables on this grid: ' + JSON.stringify(songSlots) + ' sheet slots: ' + JSON.stringify(sung.syls.map(function (y) { return y.g; })));
  check('bar 1 still at 19.0 (gridFromSong takes no lead bars for the marker line)', Math.abs(sa.offsetSec - 19.0) < 0.03, String(sa.offsetSec));
  check('the marker line took bar 1 as a line with a note on it', rows[0].syls.length > 0, JSON.stringify(rows[0]));
  check('BUG: the first sung line sits a bar late and its syllables are crushed to consecutive sixteenths', sung.ord === 1 && sung.syls[0].g === 16 && sung.syls[1].g === 17, 'ord ' + sung.ord + ' slots ' + JSON.stringify(sung.syls.map(function (y) { return y.g; })) + ' (sung at ' + JSON.stringify(songSlots) + ')');
  window.fetch = realFetch;
}, function (e) { say('FAIL rejected: ' + (e && e.stack || e)); window.fetch = realFetch; });
