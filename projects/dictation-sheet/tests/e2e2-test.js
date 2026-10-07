// Second round, end to end inside the staged page: an EMPTY sheet, a faked /lyrics answer, a synthetic song (beats,
// low band, voice band). Place words must write the words, read tempo and time signature, put bar 1 on a downbeat,
// lock, and place. Then: a second run is refused; undo takes it all back in one step; a waltz gives 3/4.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var fps = 100, N = fps * 60;
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
// a song at 120 bpm from 1.0 s: kick on beats 1 (loud) and 3, snare on 2 and 4 louder than the kick in the full band
function makeSong(per, accentEvery) {
  var full = new Float32Array(N), low = new Float32Array(N), voice = new Float32Array(N), i;
  for (i = 0; i < N; i++) { full[i] = 0.5; low[i] = 0.4; voice[i] = 0.4; }
  var beat = 0.5, t0 = 1.0, k = 0;
  for (var t = t0; t < 59; t += beat, k++) {
    var pos = k % per;
    if (per === 4) {
      if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); }
      else if (pos === 2) { bump(low, t, 1.8, 12); bump(full, t, 1.9, 10); }
      else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); }
    } else {
      if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.3, 10); }
      else { bump(full, t, 1.7, 8); bump(low, t, 0.8, 6); }
    }
  }
  return { full: full, low: low, voice: voice };
}
function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), k; for (k = k0; k < k1 + 6 && k < env.length; k++) { var v; if (k < k0 + 3) v = 0.4 + 1.9 * (k - k0 + 1) / 3; else if (k < k1) v = 2.3 + 0.05 * Math.sin(k); else v = 2.3 - 1.9 * (k - k1 + 1) / 6; if (v > env[k]) env[k] = v; } }
var spans = [[20.10, 20.35], [20.40, 20.60], [20.85, 21.35], [21.60, 21.80], [21.85, 22.05], [22.35, 23.20], [24.60, 24.85], [24.90, 25.10], [25.35, 26.30]];
var lrc = '[00:19.95] Silent night, holy night\n[00:24.45] All is calm\n';
var realFetch = window.fetch;
window.fetch = function (url, opts) { if (String(url).indexOf('/lyrics') === 0) return Promise.resolve({ ok: true, headers: new Headers({ 'content-type': 'application/json' }), json: function () { return Promise.resolve({ ok: true, synced: lrc, plain: '', duration: 60, track: 'Test Song', artist: 'Tester' }); } }); return realFetch(url, opts); };
function setup(trackId, per) {
  var s = d.S(); s.time = '4/4'; s.bpm = 100; s.audio = null; s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null;
  s.spotify = { trackId: trackId, name: 'Test Song · Tester', durationMs: 60000, title: 'Test Song', artist: 'Tester', album: '' };
  var song = makeSong(per); spans.forEach(function (p) { sing(song.voice, p[0], p[1]); });
  d.cur().audio = { el: { paused: true, currentTime: 0, duration: 60, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'test.wav', peaks: null, duration: 60, onset: d.risesOf(song.full), voice: song.voice, low: song.low, blob: false };
  return s;
}
function report(label) {
  var s = d.S(), sa = d.sheetAudio(), spb = d.slotsPerBar(s.time), rows = [];
  say('LOG ' + label + ': bpm ' + s.bpm + ' time ' + s.time + ' offsetSec ' + sa.offsetSec + ' locked ' + sa.locked + (sa.lockFit ? ' fit ' + sa.lockFit.onHit + '%' : '') + ' filled ' + JSON.stringify(s.filled) + ' title "' + s.title + '"');
  s.lines.forEach(function (l, li) { if (l.kind !== 'line') return; var base = d.barOrdinal(s, li, 0) * spb; say('LOG   line bars ' + l.bars + ': ' + d.sortedSyls(l).map(function (y) { rows.push({ t: y.text, g: base + y.pos, len: d.lenSlots(y) }); return y.text + '@' + (base + y.pos) + 'x' + d.lenSlots(y); }).join(' ')); });
  return rows;
}
var s = setup('fake-44', 4);
d.autoPlaceWords().then(function () {
  var rows = report('4/4 song'), sa = d.sheetAudio(), s1 = d.S();
  check('words came from the lookup (9 syllables on 2 lines)', rows.length === 9 && s1.lines.length === 2, rows.length + ' syllables, ' + s1.lines.length + ' lines');
  check('title from the lookup', s1.title === 'Tester - Test Song', s1.title);
  check('tempo read from the song (120)', Math.abs(s1.bpm - 120) <= 1, String(s1.bpm));
  check('time signature 4/4', s1.time === '4/4', s1.time);
  check('locked to the beats with a good fit', sa.locked && sa.lockFit && sa.lockFit.onHit >= 80, JSON.stringify(sa.lockFit));
  var down = 19.0; check('bar 1 on the downbeat before the first sung word (19.0 s)', Math.abs(sa.offsetSec - down) < 0.03, String(sa.offsetSec));
  check('first word on beat 3 of bar 1 (slot 9, sung 1.10 s after bar 1)', rows[0].g === 9, 'slot ' + rows[0].g);
  check('song marked as on the sheet', !!(s1.filled && s1.filled.key === 'spotify:fake-44'), JSON.stringify(s1.filled));
  var before = JSON.stringify(s1.lines);
  return d.autoPlaceWords().then(function () {
    var s2 = d.S();
    check('second run for the same song changes nothing', JSON.stringify(s2.lines) === before && s2.filled.key === 'spotify:fake-44');
    d.undo();
    var s3 = d.S();
    check('one undo takes the whole fill back', s3.lines.length === 0 && !s3.filled && s3.bpm === 100 && s3.time === '4/4' && !(s3.audio && s3.audio.locked), 'lines ' + s3.lines.length + ' bpm ' + s3.bpm + ' time ' + s3.time + ' locked ' + (s3.audio && s3.audio.locked));
    setup('fake-34', 3);
    return d.autoPlaceWords();
  });
}).then(function () {
  var rows = report('3/4 song'), s4 = d.S(), sa = d.sheetAudio();
  check('waltz gives 3/4', s4.time === '3/4', s4.time);
  check('tempo still 120', Math.abs(s4.bpm - 120) <= 1, String(s4.bpm));
  check('bar 1 on a downbeat of the waltz (every 1.5 s from 1.0: 19.0)', Math.abs(sa.offsetSec - 19.0) < 0.03, String(sa.offsetSec));
  check('still locked', !!sa.locked, String(sa.locked));
  check('sheet redrew without NaN styles', document.querySelectorAll('[style*="NaN"]').length === 0);
  window.fetch = realFetch;
}, function (e) { say('FAIL rejected: ' + (e && e.stack || e)); window.fetch = realFetch; });
