// tempo part, tests 4-5: gridFromSong end to end inside the staged page, lockToSong refusals, the listener view, the toasts
var d = window.__ds, fps = 100;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; if (k0 < 0) return; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
function fresh(N, f) { var e = new Float32Array(N); for (var i = 0; i < N; i++) e[i] = f; return e; }
function f2(x) { return (Math.round(x * 100) / 100).toFixed(2); }
function drums(o) {
  var len = o.len || 60, N = Math.round(len * fps), full = fresh(N, 0.5), low = fresh(N, 0.4), beats = [], t = 1.0, k = 0, tau;
  while (t < len - 0.5) {
    tau = 60 / (o.bpm * (1 + (o.drift || 0) * t / len)); beats.push(t);
    var pos = k % 4;
    if (o.halfTime) { if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else if (pos === 2) { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); } }
    else if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); }
    else if (pos === 2) { bump(low, t, 1.8, 12); bump(full, t, 1.9, 10); }
    else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); }
    if (o.hats !== 'none') { bump(full, t, 1.0, 4); bump(full, t + tau / 2, 1.0, 4); }
    t += tau; k++;
  }
  if (o.lowOnly) { var kick = fresh(N, 0.4); beats.forEach(function (b, i) { var p = i % 4; if (p === 0) bump(kick, b, 2.2, 12); else if (p === 2 && !o.halfTime) bump(kick, b, 1.8, 12); }); low = kick; full = kick; }
  var voice = fresh(N, 0.4);
  return { full: full, low: low, on: d.risesOf(full), voice: voice, beats: beats, bpm: o.bpm, N: N, len: len, downbeats: beats.filter(function (b, i) { return i % 4 === 0; }) };
}
function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), k; for (k = k0; k < k1 + 6 && k < env.length; k++) { var v; if (k < k0 + 3) v = 0.4 + 1.9 * (k - k0 + 1) / 3; else if (k < k1) v = 2.3 + 0.05 * Math.sin(k); else v = 2.3 - 1.9 * (k - k1 + 1) / 6; if (v > env[k]) env[k] = v; } }
function fakeTrack(tr, o) { o = o || {}; d.cur().audio = { el: { paused: true, currentTime: 0, duration: tr.len, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'Puddle of Mudd - Blurry.wav', peaks: null, duration: tr.len, onset: o.noOnset ? null : tr.on, voice: o.noVoice ? null : tr.voice, low: o.noLow ? null : tr.low, blob: false }; }
function reset(o) { o = o || {}; var s = d.S(); s.time = o.time || '4/4'; s.bpm = o.bpm || 100; s.audio = null; s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null; s.spotify = o.spotify ? { trackId: 'blurry', name: 'Blurry · Puddle of Mudd', durationMs: 304000, title: 'Blurry', artist: 'Puddle of Mudd', album: '' } : null; d.cur().audio = null; d.listen.env = []; d.listen.mid = []; d.listen.pairs = []; d.listen.t0 = null; return s; }
function nearest(arr, t) { var b = Infinity; arr.forEach(function (x) { b = Math.min(b, Math.abs(x - t)); }); return b; }
function mbrief(m) { return m ? 'per ' + m.per + ' bar ' + m.bar + ' time ' + m.time + ' phase ' + m.phase + ' sure ' + f2(m.sure) + ' phaseSure ' + f2(m.phaseSure) + ' half ' + (m.half ? 1 : 0) : 'null'; }
function fbrief(f) { if (!f) return 'null'; var o = {}; for (var k in f) if (k !== 'meter') o[k] = f[k]; return JSON.stringify(o) + ' meter{' + mbrief(f.meter) + '}'; }
function state(label) { var s = d.S(), sa = d.sheetAudio(), g = d.songGrid(); say(label + ' -> bpm ' + s.bpm + ' time ' + s.time + ' offsetSec ' + sa.offsetSec + ' lined ' + sa.lined + ' locked ' + sa.locked + ' lockFit ' + JSON.stringify(sa.lockFit) + (g ? ' beats ' + g.length + ' first3 ' + g.slice(0, 3).join(',') + ' spacing ' + f2(g[1] - g[0]) : ' beats none') + ' | face bpm "' + document.getElementById('bpmFace').textContent + '" time "' + document.getElementById('timeFace').textContent + '"'); }
// the toast autoPlaceWords would build from what gridFromSong returned (index.html line 3109-3111, verbatim logic)
function gridMsg(grid) { var s = d.S(); if (!grid) return (d.S().spotify && !d.cur().audio ? 'The song has not been heard yet: press Play so it plays through once with Listen on, then press Place words again. ' : 'The song has not been heard yet: wait a moment for the attached track to be read, then press Place words again. ') + 'Tempo and time signature kept as set. '; if (!grid.bpm) return 'No steady beat found, so the tempo and time signature stay as set. '; return (grid.kept ? 'Kept the lock at ' : 'Tempo ') + grid.bpm + ' bpm' + (grid.meterSure ? ' and ' + s.time : '') + (grid.kept ? '' : ' read from the song') + (grid.meterSure ? '' : ' (time signature kept at ' + s.time + ', the beats did not say)') + (grid.downbeat ? ', bar 1 on its downbeat' : '') + (grid.locked && !grid.kept ? ', locked to its beats' + (grid.fit ? ' (' + grid.fit.onHit + '% on a hit)' : '') : '') + '. '; }
var tr = drums({ bpm: 76, hats: 'straight', len: 60 });
var firstOn = 20.16, starts = tr.downbeats.filter(function (b) { return b > 4; }).map(function (b) { return b + 0.03; });
say('true downbeats near the first word: ' + tr.downbeats.filter(function (b) { return b > 15 && b < 25; }).map(f2).join(' ') + '; firstOn ' + firstOn);
// (a) fresh sheet, file track, not lined, not locked
reset(); fakeTrack(tr);
var fa = d.gridFromSong(firstOn, starts); state('(a) fresh 4/4 sheet at 100'); say('   found ' + fbrief(fa)); say('   toast: ' + gridMsg(fa));
check('(a) bpm read as 76', Math.abs(d.S().bpm - 76) < 0.5, String(d.S().bpm));
check('(a) bar 1 on the downbeat before the first word (19.95)', Math.abs(d.sheetAudio().offsetSec - 19.947) < 0.03, String(d.sheetAudio().offsetSec));
check('(a) locked, offsetSec is beats[0]', d.sheetAudio().locked && d.songGrid()[0] === d.sheetAudio().offsetSec);
check('(a) found.downbeat true', fa.downbeat);
// (a2) the same from a 3/4 sheet: does applyTime fire?
reset({ time: '3/4' }); fakeTrack(tr); var fa2 = d.gridFromSong(firstOn, starts); state('(a2) from a 3/4 sheet'); say('   found ' + fbrief(fa2)); say('   toast: ' + gridMsg(fa2));
check('(a2) time became 4/4', d.S().time === '4/4', d.S().time);
// (a3) a sheet already at 76 and 4/4 (nothing to see change)
reset({ bpm: 76 }); fakeTrack(tr); var fa3 = d.gridFromSong(firstOn, starts); say('(a3) sheet already 76/4/4: toast: ' + gridMsg(fa3));
// (b) sheet ALREADY LOCKED from before at a wrong tempo (100 bpm beats on the 76 bpm song)
reset(); fakeTrack(tr); var wrong = []; for (var t = 1.0; t < 59; t += 0.6) wrong.push(Math.round(t * 1000) / 1000);
d.S().audio = { offsetSec: 1.0, lined: true, name: '', assetId: null, beats: wrong, locked: true, lockFit: { onHit: 41, avgMs: 22 } }; d.S().bpm = 100;
var fb = d.gridFromSong(firstOn, starts); state('(b) pre-locked at 100 on the 76 song'); say('   found ' + fbrief(fb)); say('   toast: ' + gridMsg(fb));
check('(b) the wrong lock is kept: bpm still 100, beats untouched', d.S().bpm === 100 && d.songGrid() === wrong && fb.kept);
// (b2) pre-locked at the RIGHT tempo but with bar 1 on beat 3: kept too
reset(); fakeTrack(tr); var right = d.trackBeats(tr.on, fps, 76).map(function (b) { return Math.round(b * 1000) / 1000; }), i3 = 0; while (right[i3] < 1.0 + 2 * 60 / 76 - 0.01) i3++;
d.S().audio = { offsetSec: right[i3], lined: true, name: '', assetId: null, beats: right.slice(i3), locked: true, lockFit: { onHit: 99, avgMs: 0 } }; d.S().bpm = 76;
var fb2 = d.gridFromSong(firstOn, starts); say('(b2) pre-locked at 76 with bar 1 on beat 3 (' + right[i3] + '): offsetSec ' + d.sheetAudio().offsetSec + ' found ' + fbrief(fb2)); say('   toast: ' + gridMsg(fb2));
// (c) lined by hand, not locked: bar 1 at 20.5 (0.55 s after the downbeat, 0.24 s before beat 2)
reset(); fakeTrack(tr); d.S().audio = { offsetSec: 20.5, lined: true, name: '', assetId: null, beats: null, locked: false, lockFit: null };
var fc = d.gridFromSong(firstOn, starts); state('(c) lined by hand at 20.5'); say('   found ' + fbrief(fc)); say('   toast: ' + gridMsg(fc));
say('   bar 1 moved to ' + d.sheetAudio().offsetSec + ' = ' + (nearest(tr.downbeats, d.sheetAudio().offsetSec) < 0.03 ? 'a downbeat' : 'NOT a downbeat (beat ' + (Math.round((d.sheetAudio().offsetSec - 19.947) / (60 / 76)) + 1) + ' of the bar)'));
// (c2) lined by hand at 0 (before the first tracked beat)
reset(); fakeTrack(tr); d.S().audio = { offsetSec: 0, lined: true, name: '', assetId: null, beats: null, locked: false, lockFit: null };
var fc2 = d.gridFromSong(firstOn, starts); state('(c2) lined by hand at 0'); say('   found ' + fbrief(fc2)); say('   toast: ' + gridMsg(fc2)); say('   first tracked beat at ' + f2(d.trackBeats(tr.on, fps, 76)[0]) + ' s; refusal window 30/bpm = ' + f2(30 / 76) + ' s');
// (d) a.low null (file still rendering): phase capped, bar 1 rule; with and without enough starts
reset(); fakeTrack(tr, { noLow: true }); var fd = d.gridFromSong(firstOn, null); state('(d) low null, no starts'); say('   found ' + fbrief(fd)); say('   toast: ' + gridMsg(fd));
say('   bar 1 at ' + d.sheetAudio().offsetSec + ' = ' + (nearest(tr.downbeats, d.sheetAudio().offsetSec) < 0.03 ? 'a downbeat' : 'the beat at or before the first word, not the downbeat'));
reset(); fakeTrack(tr, { noLow: true }); var fd2 = d.gridFromSong(firstOn, starts); state('(d2) low null, ' + starts.length + ' starts on downbeats'); say('   found ' + fbrief(fd2)); say('   toast: ' + gridMsg(fd2));
say('   bar 1 at ' + d.sheetAudio().offsetSec + ' = ' + (nearest(tr.downbeats, d.sheetAudio().offsetSec) < 0.03 ? 'a downbeat' : 'not a downbeat'));
// (e) tempoOf returns 0: a 14 s track, and the half-time kick-only view at 76
reset(); fakeTrack(drums({ bpm: 76, hats: 'straight', len: 14 })); var fe = d.gridFromSong(5.0, null); state('(e) 14 s track'); say('   found ' + fbrief(fe)); say('   toast: ' + gridMsg(fe));
reset(); fakeTrack(drums({ bpm: 76, hats: 'straight', halfTime: true, lowOnly: true })); var fe2 = d.gridFromSong(firstOn, starts); state('(e2) half-time kick-only view at 76'); say('   found ' + fbrief(fe2)); say('   toast: ' + gridMsg(fe2));
// (f) beatCurve null: Spotify-linked with nothing heard; an attached file still decoding
reset({ spotify: true }); var ff = d.gridFromSong(firstOn, starts); state('(f) spotify, nothing heard'); say('   found ' + (ff === null ? 'null' : fbrief(ff))); say('   toast: ' + gridMsg(ff));
reset(); fakeTrack(tr, { noOnset: true }); var ff2 = d.gridFromSong(firstOn, starts); state('(f2) file attached, onset not yet read'); say('   found ' + (ff2 === null ? 'null' : fbrief(ff2))); say('   toast: ' + gridMsg(ff2));
// (g) x/8: a 6/8 song at a dotted-quarter pulse of 80, sheet at 4/4
function comp(pulse, len) { var N = Math.round(len * fps), full = fresh(N, 0.5), low = fresh(N, 0.4), beats = [], k = 0, tau = 60 / pulse; for (var t = 1.0; t < len - 0.5; t += tau, k++) { beats.push(t); if (k % 2 === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.3, 10); } else { bump(full, t, 1.6, 8); bump(low, t, 0.9, 6); } bump(full, t + tau / 3, 1.1, 4); bump(full, t + 2 * tau / 3, 1.1, 4); } return { full: full, low: low, on: d.risesOf(full), voice: fresh(N, 0.4), beats: beats, len: len, downbeats: beats.filter(function (b, i) { return i % 2 === 0; }) }; }
var c68 = comp(80, 60); reset(); fakeTrack(c68); var fg = d.gridFromSong(20.2, c68.downbeats.map(function (b) { return b + 0.03; })); state('(g) 6/8 at 80 dotted from a 4/4 sheet'); say('   found ' + fbrief(fg)); say('   toast: ' + gridMsg(fg));
var g = d.songGrid(); if (g) { say('   lock counts eighths? spacing ' + f2(g[1] - g[0]) + ' s (dotted quarter 0.75, eighth 0.25); beats ' + g.length + '; bar 1 ' + d.sheetAudio().offsetSec + ' on a downbeat: ' + (nearest(c68.downbeats, d.sheetAudio().offsetSec) < 0.03)); say('   slotOfSong(bar1 + 0.75) = ' + f2(d.slotOfSong(d.sheetAudio().offsetSec + 0.75)) + ' (expect 6), slotOfSong(bar1 + 1.5) = ' + f2(d.slotOfSong(d.sheetAudio().offsetSec + 1.5)) + ' (expect 12), songOfSlot(12) - bar1 = ' + f2(d.songOfSlot(12) - d.sheetAudio().offsetSec) + ' (expect 1.5)'); }
check('(g) time 6/8 and bpm tripled to 240', d.S().time === '6/8' && Math.abs(d.S().bpm - 240) < 1, d.S().time + ' ' + d.S().bpm);
var c110 = comp(110, 60); reset(); fakeTrack(c110); var fg2 = d.gridFromSong(20.2, c110.downbeats.map(function (b) { return b + 0.03; })); state('(g2) 6/8 at 110 dotted (3x = 330 > clamp 300)'); say('   found ' + fbrief(fg2)); say('   toast: ' + gridMsg(fg2));
if (d.songGrid()) say('   grid spacing ' + f2(d.songGrid()[1] - d.songGrid()[0]) + ' s = ' + Math.round(60 / (d.songGrid()[1] - d.songGrid()[0])) + ' eighths/min, but s.bpm ' + d.S().bpm + '; unlock -> straight ' + d.S().bpm);
// (g3) the sheet already in 6/8 (user set it) and a 4/4 song: applyTime to 4/4 first, then no tripling
reset({ time: '6/8' }); fakeTrack(tr); var fg3 = d.gridFromSong(firstOn, starts); state('(g3) sheet set to 6/8, song is 4/4'); say('   toast: ' + gridMsg(fg3));
// (5) lockToSong refusals and the tracker with bpmHint at half and double tempo
reset(); fakeTrack(tr); d.gridFromSong(firstOn, starts); var off0 = d.sheetAudio().offsetSec;
d.lockToSong(true, true, true, 38); state('(5a) lockToSong with bpmHint 38 (half)'); var gh = d.songGrid(); if (gh) say('   spacing ' + f2(gh[1] - gh[0]) + ' s, beats ' + gh.length + ', bar 1 moved from ' + off0 + ' to ' + d.sheetAudio().offsetSec);
d.unlockSong(true); d.sheetAudio().offsetSec = off0; d.lockToSong(true, true, true, 152); state('(5b) lockToSong with bpmHint 152 (double)'); var gd = d.songGrid(); if (gd) say('   spacing ' + f2(gd[1] - gd[0]) + ' s, fit ' + JSON.stringify(d.sheetAudio().lockFit));
d.unlockSong(true); d.sheetAudio().offsetSec = off0; d.lockToSong(true, true, true, 100); state('(5c) lockToSong with bpmHint 100 (wrong)'); var gw = d.songGrid(); if (gw) say('   spacing ' + f2(gw[1] - gw[0]) + ' s, fit ' + JSON.stringify(d.sheetAudio().lockFit) + ' <- a wrong tempo still locks and reports a fit');
// (5d) bar 1 exactly half a beat off any tracked beat: the refusal
d.unlockSong(true); d.sheetAudio().offsetSec = Math.round((off0 + 30 / 76 + 0.01) * 1000) / 1000; d.lockToSong(true, true, true, 76); state('(5d) bar 1 0.405 s off a beat (window 0.395)');
// (h) the listener path: no file, the low band only, clocks matched at 0
function listenerView(env, label, fo, st) { reset({ spotify: true }); d.listen.env = Array.prototype.slice.call(env); d.listen.mid = []; d.listen.midOk = false; d.listen.t0 = 0; d.listen.pairs = [0]; d.listen.latency = 0; d.listen.fps = 100; var bc = d.beatCurve(); say(label + ': beatCurve ' + (bc ? 'ok, start ' + bc.start + ', low is env: ' + (bc.low === undefined ? 'undefined' : 'yes') : 'null') + '; tempoOf(on) ' + (bc ? d.tempoOf(bc.on, 100) : '-')); var f = d.gridFromSong(fo, st); state('   ' + label); say('   found ' + (f === null ? 'null' : fbrief(f))); say('   toast: ' + gridMsg(f)); }
listenerView(drums({ bpm: 76, hats: 'straight' }).low, '(h1) listener low band, kick 1 and 3 + snare bleed', firstOn, starts);
listenerView(drums({ bpm: 76, hats: 'straight', halfTime: true }).low, '(h2) listener low band, half-time kick 1 + snare bleed on 3', firstOn, starts);
listenerView(drums({ bpm: 76, hats: 'straight', halfTime: true, lowOnly: true }).low, '(h3) listener low band, half-time kick only', firstOn, starts);
listenerView(drums({ bpm: 76, hats: 'straight', lowOnly: true }).low, '(h4) listener low band, kick 1 and 3 only', firstOn, starts);
// a Blurry-like listener view: kick 1, snare bleed on 3, bass on every eighth of the bar (the riff)
var bl = drums({ bpm: 76, hats: 'straight', halfTime: true }); for (var q = 0; q + 1 < bl.beats.length; q++) { bump(bl.low, bl.beats[q], 1.3, 8); bump(bl.low, (bl.beats[q] + bl.beats[q + 1]) / 2, 1.3, 8); }
listenerView(bl.low, '(h5) listener low band, half-time + bass eighths', firstOn, starts);
// a heard listener view but under 15 s
reset({ spotify: true }); d.listen.env = Array.prototype.slice.call(drums({ bpm: 76, hats: 'straight', len: 14 }).low); d.listen.t0 = 0; d.listen.pairs = [0]; say('(h6) 14 s heard: beatCurve ' + (d.beatCurve() ? 'ok' : 'null') + ' -> gridFromSong ' + (d.gridFromSong(5, null) === null ? 'null (not heard toast)' : 'found'));
reset({ spotify: true }); d.listen.env = Array.prototype.slice.call(drums({ bpm: 76, hats: 'straight', len: 30 }).low); d.listen.t0 = 0; d.listen.pairs = []; say('(h7) 30 s heard but no clock pairs: beatCurve ' + (d.beatCurve() ? 'ok' : 'null') + ' -> ' + gridMsg(d.gridFromSong(5, null)));
// (i) the real toast, through autoPlaceWords with a faked lyrics answer, for the fresh case and the pre-locked case
var spans = [[20.16, 20.4], [20.5, 20.7], [20.9, 21.4], [21.7, 21.9], [21.95, 22.15], [22.4, 23.2], [24.7, 24.9], [25.0, 25.2], [25.4, 26.3]];
var lrc = '[00:19.95] Silent night, holy night\n[00:24.45] All is calm\n';
var realFetch = window.fetch;
window.fetch = function (url, opts) { if (String(url).indexOf('/lyrics') === 0) return Promise.resolve({ ok: true, headers: new Headers({ 'content-type': 'application/json' }), json: function () { return Promise.resolve({ ok: true, synced: lrc, plain: '', duration: 60, track: 'Blurry', artist: 'Puddle of Mudd' }); } }); return realFetch(url, opts); };
function toastText() { return document.getElementById('toast').textContent; }
reset({ spotify: true }); var tv = drums({ bpm: 76, hats: 'straight' }); spans.forEach(function (p) { sing(tv.voice, p[0], p[1]); }); fakeTrack(tv);
d.autoPlaceWords().then(function () {
  say('(i1) REAL TOAST fresh + file: ' + toastText()); state('   after');
  return d.autoPlaceWords();
}).then(function () {
  say('(i2) REAL TOAST second press: ' + toastText());
  reset({ spotify: true }); fakeTrack(tv); d.S().audio = { offsetSec: 1.0, lined: true, name: '', assetId: null, beats: wrong, locked: true, lockFit: { onHit: 41, avgMs: 22 } }; d.S().bpm = 100;
  return d.autoPlaceWords();
}).then(function () {
  say('(i3) REAL TOAST pre-locked at 100: ' + toastText()); state('   after');
  reset({ spotify: true });
  return d.autoPlaceWords();
}).then(function () {
  say('(i4) REAL TOAST spotify, nothing heard: ' + toastText()); state('   after'); say('   filled ' + JSON.stringify(d.S().filled) + ' (a second Place words is ' + (d.S().filled ? 'refused' : 'allowed') + ')');
  reset({ spotify: true }); fakeTrack(drums({ bpm: 76, hats: 'straight', halfTime: true, lowOnly: true }));
  return d.autoPlaceWords();
}).then(function () {
  say('(i5) REAL TOAST no steady beat: ' + toastText()); state('   after'); say('   filled ' + JSON.stringify(d.S().filled));
  say('toast length (i1) chars: ' + toastText().length + '; toast shows for 1800 ms (index.html line 1170)');
  window.fetch = realFetch;
}, function (e) { say('FAIL rejected: ' + (e && e.stack || e)); window.fetch = realFetch; });
