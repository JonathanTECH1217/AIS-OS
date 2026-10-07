// voice-listen.js: pagecheck.py extra script. (4) voiceCurve()/beatCurve() under every listener state; (2) autoPlaceWords
// falling back to evenSpans when a line's voice gives too few onsets; the fallback's toast and where the even spread starts.
var d = window.__ds, L = d.listen;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function arr(n, v) { var a = []; for (var i = 0; i < n; i++) a.push(v); return a; }
function brief(c) { if (!c) return 'null'; return '{env ' + (c.env ? c.env.length : (c.on ? c.on.length : '?')) + (c.low ? ' low ' + c.low.length : (c.on ? ' low null' : '')) + ' fps ' + c.fps + ' start ' + (Math.round(c.start * 1000) / 1000) + '}'; }
var fps = 100;
function setListen(o) { L.env = o.env === undefined ? arr(1600, 0.5) : o.env; L.mid = o.mid === undefined ? arr(600, 0.4) : o.mid; L.midOk = o.midOk === undefined ? true : o.midOk; L.t0 = o.t0 === undefined ? 5.0 : o.t0; L.pairs = o.pairs === undefined ? [10.0, 10.02, 9.98] : o.pairs; L.latency = o.latency === undefined ? 0.1 : o.latency; L.fps = 100; }
d.cur().audio = null;
var cases = [
  ['nothing attached, listener empty', { env: [], mid: [], midOk: false, t0: null, pairs: [] }, null, null],
  ['listener full, matched (browser mode)', {}, 'curve', 'curve'],
  ['midOk false (older serve.py: no voice band)', { midOk: false }, null, 'curve'],
  ['pairs empty (clock never matched)', { pairs: [] }, null, null],
  ['t0 null (no frame yet)', { t0: null }, null, null],
  ['mid exactly 5 s (500 frames)', { mid: arr(500, 0.4) }, null, 'curve'],
  ['mid 5.01 s (501 frames)', { mid: arr(501, 0.4) }, 'curve', 'curve'],
  ['env exactly 15 s (1500 frames)', { env: arr(1500, 0.5) }, 'curve', null],
  ['env 15.01 s (1501)', { env: arr(1501, 0.5) }, 'curve', 'curve'],
  ['mid 6 s, env 10 s (heard 10 s)', { mid: arr(600, 0.4), env: arr(1000, 0.5) }, 'curve', null],
  ['latency null', { latency: null }, 'curve', 'curve']
];
cases.forEach(function (c) {
  setListen(c[1]); var v = d.voiceCurve(), b = d.beatCurve();
  var okV = c[2] === null ? v === null : !!v, okB = c[3] === null ? b === null : !!b;
  check('(4) ' + c[0] + ': voiceCurve ' + brief(v) + ' beatCurve ' + brief(b), okV && okB, 'wanted voice ' + (c[2] || 'null') + ', beat ' + (c[3] || 'null'));
});
setListen({}); var vv = d.voiceCurve(); check('(4) listener start = t0 + median(pairs) - latency = 5 + 10 - 0.1 = 14.9', vv && Math.abs(vv.start - 14.9) < 1e-6, vv && String(vv.start));
// a track attached with its bands still rendering (voice null, onset there) beats the listener for the beats, not for the voice
setListen({});
d.cur().audio = { el: { paused: true, currentTime: 0, duration: 60, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'test.wav', peaks: null, duration: 60, onset: new Float32Array(6000), voice: null, low: null, blob: false };
check('(4) file attached, voiceOf not done, listener full: voiceCurve comes from the listener, beatCurve from the file', (function () { var v = d.voiceCurve(), b = d.beatCurve(); return v && v.start !== 0 && b && b.start === 0 && b.on.length === 6000; })(), 'voice ' + brief(d.voiceCurve()) + ' beat ' + brief(d.beatCurve()));
d.cur().audio.voice = new Float32Array(500); check('(4) file voice of exactly 5 s (500 frames) is not used: listener wins', (function () { var v = d.voiceCurve(); return v && v.start !== 0; })(), brief(d.voiceCurve()));
d.cur().audio.voice = new Float32Array(501); check('(4) file voice of 501 frames wins over the listener', (function () { var v = d.voiceCurve(); return v && v.start === 0 && v.env.length === 501; })(), brief(d.voiceCurve()));
d.cur().audio = null; setListen({ env: [], mid: [], midOk: false, t0: null, pairs: [] });

// ---- (2) the evenSpans fallback inside autoPlaceWords ----
var N = fps * 60;
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), k; for (k = k0; k < k1 + 6 && k < env.length; k++) { var v; if (k < k0 + 3) v = 0.4 + 1.9 * (k - k0 + 1) / 3; else if (k < k1) v = 2.3 + 0.05 * Math.sin(k); else v = 2.3 - 1.9 * (k - k1 + 1) / 6; if (v > env[k]) env[k] = v; } }
var full = new Float32Array(N), low = new Float32Array(N), voice = new Float32Array(N), i;
for (i = 0; i < N; i++) { full[i] = 0.5; low[i] = 0.4; voice[i] = 0.4; }
var k = 0; for (var t = 1.0; t < 59; t += 0.5, k++) { var pos = k % 4; if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else if (pos === 2) { bump(low, t, 1.8, 12); bump(full, t, 1.9, 10); } else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); } }
// line 1 "Silent night, holy night" (6): all six sung. line 2 "All is calm" (3): all three. line 3 "Sleep in heavenly peace" (6): only 2 sung -> under ceil(6/2)=3 -> null -> evenSpans
[[20.10, 20.35], [20.40, 20.60], [20.85, 21.35], [21.60, 21.80], [21.85, 22.05], [22.35, 23.20], [24.60, 24.85], [24.90, 25.10], [25.35, 26.30], [28.40, 28.70], [30.10, 30.60]].forEach(function (p) { sing(voice, p[0], p[1]); });
var lrc = '[00:19.95] Silent night, holy night\n[00:24.45] All is calm\n[00:28.00] Sleep in heavenly peace\n';
var realFetch = window.fetch;
window.fetch = function (url, opts) { if (String(url).indexOf('/lyrics') === 0) return Promise.resolve({ ok: true, headers: new Headers({ 'content-type': 'application/json' }), json: function () { return Promise.resolve({ ok: true, synced: lrc, plain: '', duration: 60, track: 'Test Song', artist: 'Tester' }); } }); return realFetch(url, opts); };
var s = d.S(); s.time = '4/4'; s.bpm = 100; s.audio = null; s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null;
s.spotify = { trackId: 'fake-even', name: 'Test Song · Tester', durationMs: 60000, title: 'Test Song', artist: 'Tester', album: '' };
d.cur().audio = { el: { paused: true, currentTime: 0, duration: 60, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'test.wav', peaks: null, duration: 60, onset: d.risesOf(full), voice: voice, low: low, blob: false };
var vc = d.voiceCurve(); vc.rises = d.risesOf(vc.env);
say('LOG (2) direct: line 3 window 27.88..? sungSpansIn(K=6) -> ' + JSON.stringify(d.sungSpansIn(vc, 28.0 - 0.12, 40.0 - 0.05, 6, [false, false, true, true, false, false])) + '; onsetCandidatesIn -> ' + JSON.stringify(d.onsetCandidatesIn(vc, 27.88, 39.95, 6)));
say('LOG (2) direct: evenSpans(28.0, 40.0, 6) at 100 bpm -> ' + JSON.stringify(d.evenSpans(28.0, 40.0, 6).map(function (x) { return [Math.round(x.on * 100) / 100, Math.round(x.off * 100) / 100]; })));
d.autoPlaceWords().then(function () {
  var s1 = d.S(), sa = d.sheetAudio(), spb = d.slotsPerBar(s1.time), toastText = document.getElementById('toast').textContent;
  say('LOG (2) toast: ' + toastText);
  say('LOG (2) bpm ' + s1.bpm + ' time ' + s1.time + ' offsetSec ' + sa.offsetSec + ' locked ' + sa.locked);
  s1.lines.forEach(function (l, li) { if (l.kind !== 'line') return; var base = d.barOrdinal(s1, li, 0) * spb; say('LOG (2)   line ' + li + ' bars ' + l.bars + ': ' + d.sortedSyls(l).map(function (y) { var g = base + y.pos; return y.text + '@' + g + '(' + (Math.round(d.songOfSlot(g) * 100) / 100) + 's)x' + d.lenSlots(y); }).join(' ')); });
  check('(2) the toast says how many lines used the voice but not which', /on 2 of them/.test(toastText) && !/line 3|Sleep/.test(toastText), toastText.slice(0, 160));
  var l3 = s1.lines[2], base3 = d.barOrdinal(s1, 2, 0) * spb, ys = d.sortedSyls(l3), t0 = d.songOfSlot(base3 + ys[0].pos), gaps = [];
  for (var q = 1; q < ys.length; q++) gaps.push(Math.round((d.songOfSlot(base3 + ys[q].pos) - d.songOfSlot(base3 + ys[q - 1].pos)) * 100) / 100);
  say('LOG (2) line 3 first syllable at ' + Math.round(t0 * 100) / 100 + ' s (stamp 28.00, voice 28.40); gaps between its syllables ' + JSON.stringify(gaps) + ' s (even spread: (t1 - t0) * 0.85 / 6 with t1 = 28 + 12 -> 1.7 s each)');
  check('(2) the even spread starts at the stamp, not at the voice (first syllable within 0.15 s of 28.00)', Math.abs(t0 - 28.0) < 0.15, String(t0));
  window.fetch = realFetch;
}, function (e) { say('FAIL rejected: ' + (e && e.stack || e)); window.fetch = realFetch; });
