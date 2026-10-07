// quantizer-bars.js: the bars pass of autoPlaceWords (steps 5 and 6) on synthetic lines: fake /lyrics, fake attached
// track with a voice band but NO onset curve (beatCurve null), so tempo and time stay as set and the grid is a
// straight line from offsetSec 10. Run: PROFILE=prof-quantizer BUDGET=30000 python pagecheck.py stage.html quantizer-bars.js
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var fps = 100, N = fps * 60, trackN = 0;
function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), k; for (k = k0; k < k1 + 6 && k < env.length; k++) { var v; if (k < k0 + 3) v = 0.4 + 1.9 * (k - k0 + 1) / 3; else if (k < k1) v = 2.3 + 0.05 * Math.sin(k); else v = 2.3 - 1.9 * (k - k1 + 1) / 6; if (v > env[k]) env[k] = v; } }
function mkVoice(spans) { var v = new Float32Array(N), i; for (i = 0; i < N; i++) v[i] = 0.4; spans.forEach(function (p) { sing(v, p[0], p[1]); }); return v; }
var lrcText = '', realFetch = window.fetch;
window.fetch = function (url, opts) { if (String(url).indexOf('/lyrics') === 0) return Promise.resolve({ ok: true, headers: new Headers({ 'content-type': 'application/json' }), json: function () { return Promise.resolve({ ok: true, synced: lrcText, plain: '', duration: 60, track: 'Test Song', artist: 'Tester' }); } }); return realFetch(url, opts); };
function stamp(t) { var mm = Math.floor(t / 60), ss = (t - mm * 60).toFixed(2); return '[' + (mm < 10 ? '0' : '') + mm + ':' + (ss.length < 5 ? '0' : '') + ss + ']'; }
// a scenario: lines = [{text, on: [[on, off], ...]}] (on/off in song seconds); the LRC stamp sits 50 ms before the first onset
function setup(sc) {
  var s = d.S(); s.time = sc.time || '4/4'; s.bpm = sc.bpm || 120; s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null;
  s.audio = { offsetSec: 10, lined: true, name: '', assetId: null, beats: null, locked: false, lockFit: null };
  s.spotify = { trackId: 'fake-' + (++trackN), name: 'Test Song · Tester', durationMs: 60000, title: 'Test Song', artist: 'Tester', album: '' };
  var all = []; lrcText = sc.lines.map(function (l) { all = all.concat(l.on); return stamp(l.on[0][0] - 0.05) + ' ' + l.text; }).join('\n');
  d.cur().audio = { el: { paused: true, currentTime: 0, duration: 60, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'test.wav', peaks: null, duration: 60, onset: null, voice: mkVoice(all), low: null, blob: false };
}
function snapshot() { var s = d.S(); return s.lines.map(function (l, li) { if (l.kind !== 'line') return null; return { bars: l.bars, ord: d.barOrdinal(s, li, 0), syls: d.sortedSyls(l).map(function (y) { return { t: y.text, pos: y.pos, len: d.lenSlots(y) }; }) }; }); }
function fmt(snap) { return snap.map(function (l) { return l ? 'bars ' + l.bars + ' ord ' + l.ord + ': ' + l.syls.map(function (y) { return y.t + '@' + y.pos + 'x' + y.len; }).join(' ') : 'header'; }).join(' | '); }
function toastText() { var t = document.getElementById('toast'); return t ? t.textContent : ''; }
// invariants on every line: integer finite pos and len 1..64, no overlap, bars >= minBars, barOrdinal == sum of lineBars before, no NaN anywhere
function invariants(label) {
  var s = d.S(), spb = d.slotsPerBar(s.time), ok = true, why = [], sum = 0;
  s.lines.forEach(function (l, li) {
    if (l.kind !== 'line') return;
    var ys = d.sortedSyls(l), i;
    for (i = 0; i < ys.length; i++) {
      var y = ys[i], len = d.lenSlots(y);
      if (!isFinite(y.pos) || y.pos !== Math.round(y.pos) || y.pos < 0 || !isFinite(y.xs)) { ok = false; why.push('line ' + li + ' pos ' + y.pos + ' xs ' + y.xs); }
      if (!isFinite(len) || len < 1 || len > d.MAX_SLOTS) { ok = false; why.push('line ' + li + ' len ' + len); }
      if (i > 0 && ys[i - 1].pos + d.lenSlots(ys[i - 1]) > y.pos) { ok = false; why.push('line ' + li + ' overlap ' + ys[i - 1].text + '@' + ys[i - 1].pos + 'x' + d.lenSlots(ys[i - 1]) + ' vs ' + y.text + '@' + y.pos); }
    }
    if (!isFinite(l.bars) || l.bars < d.minBars(l, spb)) { ok = false; why.push('line ' + li + ' bars ' + l.bars + ' < minBars ' + d.minBars(l, spb)); }
    if (d.barOrdinal(s, li, 0) !== sum) { ok = false; why.push('line ' + li + ' barOrdinal ' + d.barOrdinal(s, li, 0) + ' != sum of lineBars before ' + sum); }
    sum += d.lineBars(l, spb);
  });
  if (JSON.stringify(s.lines).indexOf('NaN') >= 0) { ok = false; why.push('NaN in lines'); }
  check(label + ': invariants (int pos, len 1..64, no overlap, bars >= minBars, barOrdinal = sum of lineBars, no NaN)', ok, why.join('; '));
}
// expectation per placed line: [ord, [pos...]]; lens compared where given
function expect(label, sc, want) {
  var s = d.S(), spb = d.slotsPerBar(s.time), lines = s.lines.filter(function (l) { return l.kind === 'line'; }), snap = snapshot().filter(Boolean);
  say('LOG ' + label + ': time ' + s.time + ' bpm ' + s.bpm + ' spb ' + spb + ' offsetSec ' + d.sheetAudio().offsetSec + ' -> ' + fmt(snap));
  say('LOG ' + label + ' toast: ' + toastText());
  want.forEach(function (w, k) {
    var l = snap[k]; if (!l) { check(label + ' line ' + k + ' exists', false); return; }
    var songSlots = sc.lines[k].on.map(function (p) { return Math.round(d.slotOfSong(p[0])); }), startBar = Math.floor(songSlots[0] / spb);
    var sheetSlots = l.syls.map(function (y) { return l.ord * spb + y.pos; }), late = sheetSlots.map(function (v, i) { return v - songSlots[i]; });
    check(label + ' line ' + k + ' ord ' + w[0] + (w[0] === startBar ? ' = song bar' : ' (song bar ' + startBar + ')'), l.ord === w[0], 'got ' + l.ord);
    check(label + ' line ' + k + ' pos ' + JSON.stringify(w[1]), JSON.stringify(l.syls.map(function (y) { return y.pos; })) === JSON.stringify(w[1]), 'got ' + JSON.stringify(l.syls.map(function (y) { return y.pos; })));
    if (w[2]) check(label + ' line ' + k + ' bars ' + w[2], l.bars === w[2], 'got ' + l.bars);
    if (w[3]) check(label + ' line ' + k + ' lens ' + JSON.stringify(w[3]), JSON.stringify(l.syls.map(function (y) { return y.len; })) === JSON.stringify(w[3]), 'got ' + JSON.stringify(l.syls.map(function (y) { return y.len; })));
    say('LOG ' + label + ' line ' + k + ' sheet slot minus song slot per syllable: ' + JSON.stringify(late) + (late.some(function (x) { return x !== 0; }) ? '  <- syllables moved off the song grid' : ''));
  });
}
// undo, then fill again: the same sheet must come out
function rerun(label) {
  var before = fmt(snapshot()), off = d.sheetAudio().offsetSec;
  d.undo();
  var s2 = d.S();
  check(label + ': undo empties the sheet', s2.lines.length === 0 && !s2.filled && s2.audio && s2.audio.offsetSec === off, s2.lines.length + ' lines, filled ' + JSON.stringify(s2.filled) + ' offsetSec ' + (s2.audio && s2.audio.offsetSec));
  return d.autoPlaceWords().then(function () { var after = fmt(snapshot()); check(label + ': same sheet after undo and fill again', after === before, after === before ? '' : '\n  before ' + before + '\n  after  ' + after); });
}
var A = { lines: [{ text: 'one two three four five six', on: [[10.0, 10.3], [10.5, 10.8], [11.0, 11.3], [11.5, 11.8], [12.0, 12.3], [12.5, 12.8]] }, { text: 'day night sky sea', on: [[14.0, 14.3], [15.0, 15.3], [15.75, 16.05], [16.25, 16.55]] }] };
var B = { lines: [{ text: 'one two three four', on: [[10.0, 10.3], [10.5, 10.8], [11.0, 11.3], [11.5, 14.6]] }, { text: 'day night', on: [[15.0, 15.3], [15.5, 15.8]] }] };
var B2 = { lines: [{ text: 'one two three four', on: [[10.0, 10.3], [10.5, 10.8], [11.0, 11.3], [11.5, 15.6]] }, { text: 'day night', on: [[15.0, 15.3], [15.5, 15.8]] }] };
var C = { lines: [{ text: 'one two three four', on: [[10.0, 10.3], [10.5, 10.8], [11.0, 11.3], [12.25, 12.55]] }, { text: 'day night sky sea', on: [[13.5, 13.7], [13.75, 13.95], [14.0, 14.3], [14.5, 14.8]] }] };
var D = { lines: [{ text: 'one two three four', on: [[10.0, 10.3], [10.5, 10.8], [11.0, 11.3], [11.5, 11.8]] }, { text: 'day night', on: [[18.0, 18.3], [18.5, 18.8]] }] };
var E = { time: '3/4', lines: [{ text: 'one two three four', on: [[10.0, 10.3], [10.5, 10.8], [11.0, 11.3], [11.5, 11.8]] }, { text: 'day night sky', on: [[13.0, 13.3], [13.5, 13.8], [14.0, 14.3]] }] };
var F = { time: '6/8', bpm: 240, lines: [{ text: 'one two three four', on: [[10.0, 10.3], [10.5, 10.8], [11.0, 11.3], [11.5, 11.8]] }, { text: 'day night sky', on: [[13.0, 13.3], [13.5, 13.8], [14.0, 14.3]] }] };
// G: an instrumental marker line before the first sung line (bar 1 lined up by hand or by the song's beats)
var G = { lines: [{ text: '♪', on: [[8.0, 8.0]] }, { text: 'one two three', on: [[10.0, 10.3], [10.5, 10.8], [11.0, 11.3]] }, { text: 'day night', on: [[14.0, 14.3], [14.5, 14.8]] }] };
// J: a note on slot 63 of a 4-bar line, held across the barline into the bar the next line starts in (trimmed to 1)
var J = { lines: [{ text: 'one two three four', on: [[10.0, 10.3], [10.5, 10.8], [11.0, 11.3], [17.875, 18.9]] }, { text: 'day night', on: [[19.0, 19.3], [19.5, 19.8]] }] };
// K: a 64-slot hold, the next line 4 slots after it ends; L: a 66-slot hold, capped at 64
var K = { lines: [{ text: 'one', on: [[10.0, 18.0]] }, { text: 'day night', on: [[18.5, 18.8], [19.0, 19.3]] }] };
var L = { lines: [{ text: 'one', on: [[10.0, 18.2]] }, { text: 'day night', on: [[18.5, 18.8], [19.0, 19.3]] }] };
check('slotsPerBar 4/4 16, 3/4 12, 6/8 12; slotsPerBeat 4/4 4, 3/4 4, 6/8 2', d.slotsPerBar('4/4') === 16 && d.slotsPerBar('3/4') === 12 && d.slotsPerBar('6/8') === 12 && d.slotsPerBeat('4/4') === 4 && d.slotsPerBeat('3/4') === 4 && d.slotsPerBeat('6/8') === 2, [d.slotsPerBar('3/4'), d.slotsPerBar('6/8'), d.slotsPerBeat('3/4'), d.slotsPerBeat('6/8')].join(','));
function scenario(label, sc, want) {
  return function () {
    setup(sc);
    return d.autoPlaceWords().then(function () { invariants(label); expect(label, sc, want); return rerun(label); });
  };
}
var steps = [
  scenario('A two lines across barlines', A, [[0, [0, 4, 8, 12, 16, 20], 2, [4, 4, 4, 4, 4, 3]], [2, [0, 8, 14, 18], 2, [8, 6, 4, 3]]]),
  scenario('B held last word into the next line\'s bar', B, [[0, [0, 4, 8, 12], 2, [4, 4, 4, 20]], [2, [8, 12], 1, [4, 3]]]),
  scenario('B2 held last word past the next line\'s onset', B2, [[0, [0, 4, 8, 12], 2, [4, 4, 4, 20]], [2, [8, 12], 1, [4, 3]]]),
  scenario('C next line starts in the bar the last note of the line before sits in (pickup)', C, [[0, [0, 4, 8, 18], 2], [2, [0, 1, 2, 4], 1]]),
  scenario('D three bars of silence between lines', D, [[0, [0, 4, 8, 12], 4, [4, 4, 4, 3]], [4, [0, 4], 1, [4, 3]]]),
  scenario('E 3/4', E, [[0, [0, 4, 8, 12], 2, [4, 4, 4, 3]], [2, [0, 4, 8], 1, [4, 4, 3]]]),
  scenario('F 6/8 at 240 eighths a minute', F, [[0, [0, 4, 8, 12], 2, [4, 4, 4, 3]], [2, [0, 4, 8], 1, [4, 4, 3]]]),
  scenario('G marker line before the first sung line', G, [[1, [0, 4, 8], 2], [2, [0, 4], 1]]),
  scenario('J note on slot 63 of a 4-bar line, held over the barline', J, [[0, [0, 4, 8, 63], 4, [4, 4, 4, 1]], [4, [8, 12], 1, [4, 3]]]),
  scenario('K a 64-slot hold', K, [[0, [0], 4, [64]], [4, [4, 8], 1, [4, 3]]]),
  scenario('L a 66-slot hold capped at 64', L, [[0, [0], 4, [64]], [4, [4, 8], 1, [4, 3]]])
];
var p = Promise.resolve();
steps.forEach(function (st) { p = p.then(st); });
p.then(function () { say('LOG done'); window.fetch = realFetch; }, function (e) { say('FAIL rejected: ' + (e && e.stack || e)); window.fetch = realFetch; });
