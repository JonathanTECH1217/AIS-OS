// Tap words: a rest where a tap lands, 0 past the line's end, and undo (Ctrl+Z) in the middle of a pass.
var d = window.__ds, $ = function (id) { return document.getElementById(id); };
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mkLine(syls, bars) { return { kind: 'line', bars: bars || 1, syllables: syls.map(function (t, i) { return typeof t === 'string' ? { text: t, pos: i * 4 } : t; }) }; }
function setup(lines) {
  if (d.tapW.on) { try { d.tapStop(true); } catch (e) { d.tapW.on = false; } }
  var s = d.S(); s.time = '4/4'; s.bpm = 100; s.title = 'tap'; s.lyrics = ''; s.audio = null; s.spotify = null; s.filled = null;
  s.lines = d.normalize({ lines: lines }).lines;
  var el = { paused: false, currentTime: 0, duration: 60, playbackRate: 1, ended: false, seeking: false, readyState: 4, pause: function () { this.paused = true; }, play: function () { this.paused = false; return Promise.resolve(); } };
  d.cur().audio = { el: el, url: '', name: 'test.wav', peaks: null, duration: 60, onset: null, voice: null, low: null, blob: false };
  var sa = d.sheetAudio(); sa.offsetSec = 3.0; sa.lined = true; sa.locked = false; sa.beats = null;
  d.state.audioOn = true; d.state.prefs.zoom = 200; d.state.prefs.snap = '2'; d.state.tool = 'move';
  d.setSel(null); d.renderAll(); d.player.on = true; d.player.spot = false;
  return { s: s, el: el };
}
function T(G) { return 3.0 + G * 0.15 + 0.07; }
function at(el, G) { el.currentTime = T(G); }
function syls(l) { return d.sortedSyls(l).map(function (y) { return y.text + '@' + y.pos + 'x' + d.lenSlots(y) + (y.rest ? 'r' : ''); }).join(' '); }
function key(k, o) { var init = { key: k, bubbles: true, cancelable: true }; if (o) Object.keys(o).forEach(function (q) { init[q] = o[q]; }); document.body.dispatchEvent(new KeyboardEvent('keydown', init)); }

// a rest syllable sitting where a tap lands
var c3 = setup([mkLine([{ text: 'one', pos: 0 }, { text: '', pos: 4, rest: true }, { text: 'two', pos: 8 }])]), s = c3.s, el = c3.el, L0 = s.lines[0];
at(el, 0); d.tapStart(); d.tapHit(); at(el, 4); d.tapHit();
check('a rest syllable at 4 stays put when "two" lands on 4: two notes on one slot', d.sortedSyls(L0).filter(function (y) { return y.pos === 4; }).length === 2, syls(L0));
d.tapStop(true);
// 0 past the line's end grows the line; the next line's first tap trims to the barline
var c4 = setup([mkLine(['one']), mkLine(['four'])]); s = c4.s; el = c4.el; L0 = s.lines[0]; var L1 = s.lines[1], one = L0.syllables[0], four = L1.syllables[0];
at(el, 8); d.tapStart(); d.tapHit(); at(el, 30); d.tapRest();
check('0 at slot 30 on a 1-bar line: one = 22 slots, line 1 now 2 bars through minBars', d.lenSlots(one) === 22 && d.lineBars(L0, 16) === 2, syls(L0) + ' lineBars ' + d.lineBars(L0, 16));
at(el, 20); d.tapHit();
check('then line 2 tapped at bar 2 (slot 20): line 1 back to 1 bar, one cut to the barline (8), four@4', L0.bars === 1 && d.lineBars(L0, 16) === 1 && d.lenSlots(one) === 8 && four.pos === 4 && d.barOrdinal(s, 1, 0) === 1, 'bars ' + L0.bars + ' ' + syls(L0) + ' | ' + syls(L1));
d.tapStop(true);
// undo in the middle of a pass
var c5 = setup([mkLine(['one', 'two', 'three'])]); s = c5.s; el = c5.el; L0 = s.lines[0];
d.pushUndo(); s.lines = d.normalize({ lines: [mkLine(['one', 'two', 'three'])] }).lines; L0 = s.lines[0]; d.renderAll(); // an undo step under the words
at(el, 0); d.tapStart(); d.tapHit(); at(el, 6); d.tapHit();
check('two taps: one@0x6 two@6', syls(L0) === 'one@0x6 two@6x4 three@10x4', syls(L0));
key('z', { ctrlKey: true }); // Ctrl+Z during the pass
var s2 = d.S(), L0b = s2.lines[0];
check('Ctrl+Z ran during the pass: the words are back where they were', syls(L0b) === 'one@0x4 two@4x4 three@8x4', syls(L0b));
check('tap mode is still on after undo, list points at the old objects', d.tapW.on && d.tapW.list[0].y !== L0b.syllables[0], 'on ' + d.tapW.on + ' same objects ' + (d.tapW.list[0].y === L0b.syllables[0]));
at(el, 12); d.tapHit();
check('the next tap changes nothing on the sheet (it moved an orphan)', syls(L0b) === 'one@0x4 two@4x4 three@8x4', syls(L0b));
key('z', { ctrlKey: true }); // Ctrl+Z again: back to the sheet before these words (still 1 line here)
var s3 = d.S();
say('LOG after 2nd undo: lines ' + s3.lines.length + ' tapW.on ' + d.tapW.on + ' idx ' + d.tapW.idx);
s3.lines = []; d.renderAll(); // the same as an undo to the empty sheet
var threw = null; try { key('Escape'); } catch (e) { threw = String(e); }
var stuck = d.tapW.on;
check('Escape (tapStop) with the pass pointing at lines that no longer exist: does not throw, tap mode ends', !stuck, 'tapW.on ' + d.tapW.on + ' (error is reported as UNCAUGHT above if it threw)');
if (stuck) { var t2 = null; try { d.player.stop(); } catch (e) { t2 = String(e); } check('player.stop in that state still pauses the track', el.paused === true, 'el.paused ' + el.paused + ' player.on ' + d.player.on + ' threw ' + t2); }
d.tapW.on = false; d.player.on = false; $('tapWords').classList.remove('on');
say('LOG done');
