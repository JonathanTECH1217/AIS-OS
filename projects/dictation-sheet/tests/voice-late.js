// voice-late.js: pagecheck.py extra script. What the sheet shows when a timed line's voice starts 100 ms BEFORE its stamp:
// the line before's window (.. next stamp - 0.05) then holds that onset, and the last syllable of the line before takes it.
var d = window.__ds, fps = 100, N = fps * 60;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), k; for (k = k0; k < k1 + 6 && k < env.length; k++) { var v; if (k < k0 + 3) v = 0.4 + 1.9 * (k - k0 + 1) / 3; else if (k < k1) v = 2.3 + 0.05 * Math.sin(k); else v = 2.3 - 1.9 * (k - k1 + 1) / 6; if (v > env[k]) env[k] = v; } }
function song(lateBy) {
  var full = new Float32Array(N), low = new Float32Array(N), voice = new Float32Array(N), i, k = 0;
  for (i = 0; i < N; i++) { full[i] = 0.5; low[i] = 0.4; voice[i] = 0.4; }
  for (var t = 1.0; t < 59; t += 0.5, k++) { var pos = k % 4; if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else if (pos === 2) { bump(low, t, 1.8, 12); bump(full, t, 1.9, 10); } else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); } }
  // line 1 sung 20.10..23.20 (6 syllables), line 2 "All is calm" sung from 24.45 - lateBy
  var l2 = 24.45 - lateBy;
  [[20.10, 20.35], [20.40, 20.60], [20.85, 21.35], [21.60, 21.80], [21.85, 22.05], [22.35, 23.20], [l2, l2 + 0.25], [l2 + 0.30, l2 + 0.50], [l2 + 0.75, l2 + 1.65]].forEach(function (p) { sing(voice, p[0], p[1]); });
  return { full: full, low: low, voice: voice };
}
var lrc = '[00:19.95] Silent night, holy night\n[00:24.45] All is calm\n';
var realFetch = window.fetch;
window.fetch = function (url, opts) { if (String(url).indexOf('/lyrics') === 0) return Promise.resolve({ ok: true, headers: new Headers({ 'content-type': 'application/json' }), json: function () { return Promise.resolve({ ok: true, synced: lrc, plain: '', duration: 60, track: 'Test Song', artist: 'Tester' }); } }); return realFetch(url, opts); };
function setup(id, lateBy) {
  var s = d.S(); s.time = '4/4'; s.bpm = 100; s.audio = null; s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null;
  s.spotify = { trackId: id, name: 'Test Song · Tester', durationMs: 60000, title: 'Test Song', artist: 'Tester', album: '' };
  var sg = song(lateBy);
  d.cur().audio = { el: { paused: true, currentTime: 0, duration: 60, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'test.wav', peaks: null, duration: 60, onset: d.risesOf(sg.full), voice: sg.voice, low: sg.low, blob: false };
}
function report(label) {
  var s = d.S(), spb = d.slotsPerBar(s.time), rows = [];
  s.lines.forEach(function (l, li) { if (l.kind !== 'line') return; var base = d.barOrdinal(s, li, 0) * spb; say('LOG ' + label + ' line ' + li + ' bars ' + l.bars + ': ' + d.sortedSyls(l).map(function (y) { var g = base + y.pos; rows.push({ t: y.text, sec: d.songOfSlot(g), len: d.lenSlots(y) }); return y.text + '@' + (Math.round(d.songOfSlot(g) * 100) / 100) + 's x' + d.lenSlots(y); }).join(' ')); });
  return rows;
}
setup('late-0', 0);
d.autoPlaceWords().then(function () {
  var r = report('voice on time (stamp 24.45, voice 24.45)');
  check('on time: last syllable of line 1 ("night") ends near 23.2 s', r[5] && Math.abs(r[5].sec - 22.35) < 0.15 && r[5].len <= 8, JSON.stringify(r[5]));
  check('on time: "All" at 24.45', r[6] && Math.abs(r[6].sec - 24.45) < 0.15, JSON.stringify(r[6]));
  setup('late-100', 0.10);
  return d.autoPlaceWords();
}).then(function () {
  var r = report('voice 100 ms before its stamp (stamp 24.45, voice 24.35)');
  check('late stamp: line 1 last syllable still at 22.35 (not moved to 24.35)', r[5] && Math.abs(r[5].sec - 22.35) < 0.15, JSON.stringify(r[5]));
  check('late stamp: "All" at 24.35', r[6] && Math.abs(r[6].sec - 24.35) < 0.15, JSON.stringify(r[6]));
  var vc = d.voiceCurve(); vc.rises = d.risesOf(vc.env);
  say('LOG late stamp: line 1 window candidates (19.83..24.40, K=6): ' + JSON.stringify(d.onsetCandidatesIn(vc, 19.95 - 0.12, 24.45 - 0.05, 6)) + ' K=7: ' + JSON.stringify(d.onsetCandidatesIn(vc, 19.95 - 0.12, 24.45 - 0.05, 7)));
  setup('late-250', 0.25);
  return d.autoPlaceWords();
}).then(function () {
  var r = report('voice 250 ms before its stamp (stamp 24.45, voice 24.20)');
  check('stamp 250 ms late: "All" at 24.20', r[6] && Math.abs(r[6].sec - 24.20) < 0.15, JSON.stringify(r[6]));
  check('stamp 250 ms late: "is" at 24.50', r[7] && Math.abs(r[7].sec - 24.50) < 0.15, JSON.stringify(r[7]));
  var vc = d.voiceCurve(); vc.rises = d.risesOf(vc.env);
  say('LOG stamp 250 ms late: line 2 window candidates (24.33..36-0.05, K=3): ' + JSON.stringify(d.onsetCandidatesIn(vc, 24.45 - 0.12, 36.45 - 0.05, 3)));
  window.fetch = realFetch;
}, function (e) { say('FAIL rejected: ' + (e && e.stack || e)); window.fetch = realFetch; });
