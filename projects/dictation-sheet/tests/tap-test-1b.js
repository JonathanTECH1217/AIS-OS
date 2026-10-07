// Tap words with real timer gaps (the 40 ms redraw and 60 ms tapMark timers run between steps), the no-voice branch,
// the "fewer bars" branch, and a rest syllable sitting where a tap lands.
var d = window.__ds, $ = function (id) { return document.getElementById(id); };
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var fps = 100, N = 6000;
function fresh(n) { var e = new Float32Array(n || N); for (var i = 0; i < e.length; i++) e[i] = 0.4; return e; }
function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), k; for (k = k0; k < k1 + 6 && k < env.length; k++) { var v; if (k < k0 + 3) v = 0.4 + 1.9 * (k - k0 + 1) / 3; else if (k < k1) v = 2.3 + 0.05 * Math.sin(k); else v = 2.3 - 1.9 * (k - k1 + 1) / 6; if (v > env[k]) env[k] = v; } }
function mkLine(syls, bars) { return { kind: 'line', bars: bars || 1, syllables: syls.map(function (t, i) { return typeof t === 'string' ? { text: t, pos: i * 4 } : t; }) }; }
function setup(lines, voice) {
  var s = d.S(); s.time = '4/4'; s.bpm = 100; s.title = 'tap'; s.lyrics = ''; s.audio = null; s.spotify = null; s.filled = null;
  s.lines = d.normalize({ lines: lines }).lines;
  var el = { paused: false, currentTime: 0, duration: 60, playbackRate: 1, ended: false, seeking: false, readyState: 4, pause: function () { this.paused = true; }, play: function () { this.paused = false; return Promise.resolve(); } };
  d.cur().audio = { el: el, url: '', name: 'test.wav', peaks: null, duration: 60, onset: null, voice: voice, low: null, blob: false };
  var sa = d.sheetAudio(); sa.offsetSec = 3.0; sa.lined = true; sa.locked = false; sa.beats = null;
  d.state.audioOn = true; d.state.prefs.zoom = 200; d.state.prefs.snap = '2'; d.state.tool = 'move';
  d.setSel(null); d.renderAll(); d.player.on = true; d.player.spot = false;
  return { s: s, el: el };
}
function T(G) { return 3.0 + G * 0.15 + 0.07; }
function at(el, G) { el.currentTime = T(G); }
function syls(l) { return d.sortedSyls(l).map(function (y) { return y.text + '@' + y.pos + 'x' + d.lenSlots(y) + (y.rest ? 'r' : ''); }).join(' '); }
function laneChip() { var c = document.querySelector('.syl-chip.lane'); return c ? c.textContent + '@' + c.getAttribute('data-pos') : null; }
function later(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

var v = fresh(); sing(v, 3.0, 3.45); sing(v, 3.9, 4.35);
var ctx = setup([mkLine(['one', 'two', 'three']), mkLine(['four', 'five'])], v), s = ctx.s, el = ctx.el, L0 = s.lines[0], L1 = s.lines[1];
var one = L0.syllables[0], two = L0.syllables[1], three = L0.syllables[2], four = L1.syllables[0], five = L1.syllables[1];
at(el, 0); d.tapStart();
later(150).then(function () {
  check('outline on "one" after tapStart', laneChip() === 'one@0', laneChip());
  d.tapHit(); return later(150);
}).then(function () {
  check('after tap 1 (timers ran): outline on "two"', laneChip() === 'two@4', laneChip());
  at(el, 6); d.tapHit(); return later(150);
}).then(function () {
  check('after tap 2: two@6 drawn, outline on "three"', laneChip() === 'three@10' && document.querySelector('.syl-chip[data-li="0"][data-pos="6"]') !== null, laneChip() + ' ' + syls(L0));
  d.tapPause(); return later(150);
}).then(function () {
  check('paused: no outline (chips went dark)', laneChip() === null && !d.player.on, laneChip());
  d.tapPause(); return later(150);
}).then(function () {
  check('resumed: outline back on "three"', laneChip() === 'three@10' && d.player.on, laneChip() + ' on ' + d.player.on);
  d.player.stop(); return later(150);
}).then(function () {
  check('stopped: pass ended, no outline', !d.tapW.on && laneChip() === null, laneChip());
  // no voice curve: the word before keeps its length or is cut to the room, never read from the song
  var c2 = setup([mkLine(['one', 'two', 'three']), mkLine(['four', 'five'], 1)], null); s = c2.s; el = c2.el; L0 = s.lines[0]; L1 = s.lines[1];
  one = L0.syllables[0]; two = L0.syllables[1]; three = L0.syllables[2]; four = L1.syllables[0]; five = L1.syllables[1];
  L0.bars = 3; d.renderAll();
  at(el, 0); d.tapStart(); d.tapHit(); at(el, 6); d.tapHit();
  check('no voice: one = the gap to the next tap (6)', d.lenSlots(one) === 6 && two.pos === 6, syls(L0));
  d.setSlotsRaw(three, 4); at(el, 13); d.tapHit();
  check('no voice: two = 7, three@13', d.lenSlots(two) === 7 && three.pos === 13, syls(L0));
  at(el, 32); d.tapHit();
  check('first word of line 2 tapped at bar 3 while line 1 had 3 bars: line 1 shrinks to 2 bars, three cut to the barline (16-13=3)', L0.bars === 2 && d.lenSlots(three) === 3 && four.pos === 0 && d.barOrdinal(s, 1, 0) === 2, 'bars ' + L0.bars + ' ' + syls(L0) + ' | ' + syls(L1));
  return later(150);
}).then(function () {
  check('strip shows 3 cells (2 + 1)', document.querySelectorAll('.timeline .cell').length === 3, String(document.querySelectorAll('.timeline .cell').length));
  // a rest syllable sitting where a tap lands
  var c3 = setup([mkLine([{ text: 'one', pos: 0 }, { text: '', pos: 4, rest: true }, { text: 'two', pos: 8 }])], null); s = c3.s; el = c3.el; L0 = s.lines[0];
  at(el, 0); d.tapStart(); d.tapHit(); at(el, 4); d.tapHit();
  check('a rest syllable at 4 is not moved when "two" lands on 4 (stacked with the rest)', d.sortedSyls(L0).filter(function (y) { return y.pos === 4; }).length === 2, syls(L0));
  d.tapStop(true);
  // tapRest past the line's end grows the line; the next line's first tap then trims it to the barline
  var c4 = setup([mkLine(['one']), mkLine(['four'])], null); s = c4.s; el = c4.el; L0 = s.lines[0]; L1 = s.lines[1]; one = L0.syllables[0]; four = L1.syllables[0];
  at(el, 8); d.tapStart(); d.tapHit(); at(el, 30); d.tapRest();
  check('0 at slot 30 on a 1-bar line: one = 22 slots, line 1 now 2 bars (minBars)', d.lenSlots(one) === 22 && d.lineBars(L0, 16) === 2, syls(L0) + ' lineBars ' + d.lineBars(L0, 16));
  at(el, 20); d.tapHit();
  check('then line 2 tapped at bar 2 (slot 20): line 1 back to 1 bar, one cut to the barline (8), four@4', L0.bars === 1 && d.lineBars(L0, 16) === 1 && d.lenSlots(one) === 8 && four.pos === 4 && d.barOrdinal(s, 1, 0) === 1, 'bars ' + L0.bars + ' ' + syls(L0) + ' | ' + syls(L1));
  d.tapStop(true); d.player.on = false;
  say('LOG done');
}).catch(function (e) { say('FAIL 1b threw: ' + (e && e.stack || e)); });
