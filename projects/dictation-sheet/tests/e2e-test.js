// End-to-end Place words inside the staged page: a synthetic voice envelope with known syllable spans, a faked
// /lyrics answer, then the sheet's positions, lengths and bars are printed and a few properties are asserted.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
// the sheet: 4/4 at 120 bpm (a sixteenth is 0.125 s), not lined yet, a fake linked song so the lyrics lookup runs
s.time = '4/4'; s.bpm = 120; s.audio = null;
s.spotify = { trackId: 'fake', name: 'Test Song · Tester', durationMs: 60000, title: 'Test Song', artist: 'Tester', album: '' };
s.lyrics = 'Si-lent night, ho-ly night\nAll is calm';
s.lines = d.parseLyrics(s.lyrics);
// the voice band: floor 0.4, each syllable a 30 ms attack to 2.3, a hold, and a 60 ms release, at 100 fps from song second 0
var fps = 100, env = new Float32Array(fps * 60), i; for (i = 0; i < env.length; i++) env[i] = 0.4;
function sing(on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), k; for (k = k0; k < k1 + 6 && k < env.length; k++) { var v; if (k < k0 + 3) v = 0.4 + 1.9 * (k - k0 + 1) / 3; else if (k < k1) v = 2.3 + 0.05 * Math.sin(k); else v = 2.3 - 1.9 * (k - k1 + 1) / 6; if (v > env[k]) env[k] = v; } }
var spans = [[20.10, 20.35], [20.40, 20.60], [20.85, 21.35], [21.60, 21.80], [21.85, 22.05], [22.35, 23.20], [24.60, 24.85], [24.90, 25.10], [25.35, 26.30]];
spans.forEach(function (p) { sing(p[0], p[1]); });
d.cur().audio = { el: { paused: true, currentTime: 0, duration: 60, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'test.wav', peaks: null, duration: 60, onset: d.risesOf(env), voice: env, blob: false };
// the lyrics service: line stamps 0.15 s before the first sung onset of each line, as karaoke files tend to be
var lrc = '[00:19.95] Silent night, holy night\n[00:24.45] All is calm\n';
var realFetch = window.fetch;
window.fetch = function (url, opts) { if (String(url).indexOf('/lyrics') === 0) return Promise.resolve({ ok: true, json: function () { return Promise.resolve({ ok: true, synced: lrc, plain: '', duration: 60, track: 'Test Song', artist: 'Tester' }); } }); return realFetch(url, opts); };
d.autoPlaceWords().then(function () {
  window.fetch = realFetch;
  var sa = d.sheetAudio(), spb = d.slotsPerBar(s.time), rows = [], allOk = true, prevEnd = -1, lineIdx = 0;
  say('LOG offsetSec ' + sa.offsetSec + ' lined ' + sa.lined);
  s.lines.forEach(function (l, li) {
    if (l.kind !== 'line') return;
    var syls = d.sortedSyls(l), base = d.barOrdinal(s, li, 0) * spb;
    say('LOG line ' + (lineIdx + 1) + ' bars ' + l.bars + ' (global bar ' + d.barOrdinal(s, li, 0) + ')');
    syls.forEach(function (y) {
      var g = base + y.pos, len = d.lenSlots(y), gap = g - prevEnd;
      rows.push({ t: y.text, pos: y.pos, len: len, g: g, rest: prevEnd >= 0 && gap > 0 ? gap : 0, hy: y.hy });
      say('LOG   ' + (y.text + '      ').slice(0, 6) + ' pos ' + y.pos + ' len ' + len + ' global ' + g + '-' + (g + len) + (prevEnd >= 0 && gap > 0 ? ' after a rest of ' + gap : '') + (y.hy ? ' hy' : ''));
      if (!isFinite(y.pos) || y.pos < 0 || len < 1) allOk = false;
      prevEnd = g + len;
    });
    lineIdx++;
  });
  check('every syllable has a finite position and a length of at least one sixteenth', allOk);
  var globals = rows.map(function (r) { return r.g; }), inc = globals.every(function (g, k) { return k === 0 || g > globals[k - 1]; });
  check('onsets strictly increase across the sheet', inc, globals.join(','));
  check('bar 1 starts at the first sung onset, not the lyric stamp', Math.abs(sa.offsetSec - 20.10) < 0.03, 'offsetSec ' + sa.offsetSec);
  var night2 = rows[5], ly = rows[4], calm = rows.filter(function (r) { return r.t === 'calm'; })[0] || { len: -1 };
  check('the held "night" at the end of line 1 is long (about 7 slots)', night2.len >= 6 && night2.len <= 8, 'len ' + night2.len);
  check('a rest sits between "ly" and the held "night" (0.3 s gap)', night2.rest >= 2, 'rest ' + night2.rest);
  check('"Si" runs into "lent" with no rest (one word)', rows[1].rest === 0, 'rest ' + rows[1].rest);
  check('line 2 starts on a later bar, on the sung onset', rows[6].g >= 32 && Math.abs(rows[6].g - Math.round((24.60 - sa.offsetSec) / 0.125)) <= 1, 'global ' + rows[6].g);
  check('"calm" is held about 8 slots', calm.len >= 7 && calm.len <= 9, 'len ' + calm.len);
  var textOk = document.querySelectorAll('.system').length > 0 && document.querySelectorAll('[style*="NaN"]').length === 0;
  check('the sheet redrew without NaN styles', textOk);
}, function (e) { say('FAIL autoPlaceWords rejected: ' + (e && e.stack || e)); });
