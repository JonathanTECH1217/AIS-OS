// Tap words end to end on a 2-line sheet with a fake file track whose clock is set by hand, plus tapEndSlots edge cases.
var d = window.__ds, $ = function (id) { return document.getElementById(id); };
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var fps = 100, N = 6000;
function fresh(n) { var e = new Float32Array(n || N); for (var i = 0; i < e.length; i++) e[i] = 0.4; return e; }
function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), k; for (k = k0; k < k1 + 6 && k < env.length; k++) { var v; if (k < k0 + 3) v = 0.4 + 1.9 * (k - k0 + 1) / 3; else if (k < k1) v = 2.3 + 0.05 * Math.sin(k); else v = 2.3 - 1.9 * (k - k1 + 1) / 6; if (v > env[k]) env[k] = v; } }
function mkLine(texts, bars) { return { kind: 'line', bars: bars || 1, syllables: texts.map(function (t, i) { return { text: t, pos: i * 4 }; }) }; }
function setup(voice) {
  var s = d.S(); s.time = '4/4'; s.bpm = 100; s.title = 'tap'; s.lyrics = ''; s.audio = null; s.spotify = null; s.filled = null;
  s.lines = d.normalize({ lines: [mkLine(['one', 'two', 'three']), mkLine(['four', 'five'])] }).lines;
  var el = { paused: false, currentTime: 0, duration: 60, playbackRate: 1, ended: false, seeking: false, readyState: 4, pause: function () { this.paused = true; }, play: function () { this.paused = false; return Promise.resolve(); } };
  d.cur().audio = { el: el, url: '', name: 'test.wav', peaks: null, duration: 60, onset: null, voice: voice, low: null, blob: false };
  var sa = d.sheetAudio(); sa.offsetSec = 3.0; sa.lined = true; sa.locked = false; sa.beats = null;
  d.state.audioOn = true; d.state.prefs.zoom = 200; d.state.prefs.snap = '2'; d.state.tool = 'move';
  d.setSel(null); d.renderAll();
  d.player.on = true; d.player.spot = false; // fake: the band runs; tapSlot reads the file clock
  return { s: s, el: el };
}
function T(G) { return 3.0 + G * 0.15 + 0.07; } // the song second that tapSlot reads as grid slot G (it takes 60 ms off)
function at(el, G) { el.currentTime = T(G); }
function syls(l) { return d.sortedSyls(l).map(function (y) { return y.text + '@' + y.pos + 'x' + d.lenSlots(y); }).join(' '); }
function laneChip() { var c = document.querySelector('.syl-chip.lane'); return c ? c.textContent : null; }
function toast() { return $('toast').textContent; }
function key(k, o) { var init = { key: k, bubbles: true, cancelable: true }; if (o) Object.keys(o).forEach(function (q) { init[q] = o[q]; }); document.body.dispatchEvent(new KeyboardEvent('keydown', init)); }

// ---- 1. a full pass ----
var v = fresh(); sing(v, 3.0, 3.45); sing(v, 3.9, 4.0); sing(v, 4.05, 4.65); sing(v, 8.4, 8.85); sing(v, 9.3, 10.5);
var ctx = setup(v), s = ctx.s, el = ctx.el, L0 = s.lines[0], L1 = s.lines[1];
var one = L0.syllables[0], two = L0.syllables[1], three = L0.syllables[2], four = L1.syllables[0], five = L1.syllables[1];
var undo0 = d.cur().undo.length;
at(el, 0); d.tapStart();
check('tapStart: on, 5 words listed, idx 0', d.tapW.on && d.tapW.list.length === 5 && d.tapW.idx === 0, 'on ' + d.tapW.on + ' n ' + d.tapW.list.length + ' idx ' + d.tapW.idx);
check('tapStart took one undo step', d.cur().undo.length === undo0 + 1, undo0 + ' -> ' + d.cur().undo.length);
check('tapSlot reads slot 0 at T(0)', d.tapSlot() === 0, String(d.tapSlot()));
at(el, 6); check('tapSlot reads slot 6 at T(6)', d.tapSlot() === 6, String(d.tapSlot()));
at(el, 0); d.tapHit();
check('tap 1: one@0, idx 1, prev=one', one.pos === 0 && d.tapW.idx === 1 && d.tapW.prev.y === one, syls(L0));
at(el, 6); d.tapHit();
check('tap 2: two@6; one trimmed to its 3 sung slots', two.pos === 6 && d.lenSlots(one) === 3, syls(L0));
d.tapHit();
check('tap 3 in the same sixteenth: three@7, two = 1 slot', three.pos === 7 && d.lenSlots(two) === 1, syls(L0));
at(el, 36); d.tapHit();
check('new line at bar 3 of the song: line 0 gets 2 bars', L0.bars === 2 && d.lineBars(L0, 16) === 2 && d.barOrdinal(s, 1, 0) === 2, 'bars ' + L0.bars + ' ord ' + d.barOrdinal(s, 1, 0));
check('new line: three trimmed to its 4 sung slots (room 9)', d.lenSlots(three) === 4, syls(L0));
check('new line: four@4 on line 1, untapped five pushed to 8', four.pos === 4 && five.pos === 8, syls(L1));
at(el, 39); d.tapRest();
check('0 after four: four = 3 slots, prevEnded', d.lenSlots(four) === 3 && d.tapW.prevEnded === true, syls(L1) + ' prevEnded ' + d.tapW.prevEnded);
at(el, 42); d.tapHit();
check('five@10; four keeps 3 (0 ended it); prevEnded reset', five.pos === 10 && d.lenSlots(four) === 3 && !d.tapW.prevEnded, syls(L1));
check('after the last word the pass stays open', d.tapW.on && d.tapW.idx === 5 && !d.tapTarget(), 'on ' + d.tapW.on + ' idx ' + d.tapW.idx);
el.currentTime = 9.97; d.tapStop();
check('tapStop, voice still sounding: five keeps its 4 slots', d.lenSlots(five) === 4 && !d.tapW.on, syls(L1) + ' toast "' + toast() + '"');
// ---- 1b. the voice stopped before tapStop ----
for (var k = 960; k < 1100; k++) v[k] = 0.4; // five now sung 9.3 to 9.6 only
d.setSel({ li: 1, si: 1 }); at(el, 42); d.tapStart();
check('restart from the selected word: idx 4, prev four', d.tapW.idx === 4 && d.tapW.prev && d.tapW.prev.y === four, 'idx ' + d.tapW.idx);
d.tapHit();
check('five@10 again, four = 3 from its sung end', five.pos === 10 && d.lenSlots(four) === 3, syls(L1));
el.currentTime = 10.2; d.tapStop();
check('tapStop, voice stopped: five = 2 sung slots', d.lenSlots(five) === 2, syls(L1));
// ---- 1c. 0 on line 2 (local vs global) ----
d.setSel({ li: 1, si: 1 }); at(el, 42); d.tapStart(); d.tapHit();
at(el, 42); d.tapRest();
check('0 in the same sixteenth as the tap: nothing changes (n=0), no feedback', d.lenSlots(five) === 4 && !d.tapW.prevEnded, syls(L1) + ' toast "' + toast() + '"');
at(el, 45); d.tapRest();
check('0 on line 2: five = 45-32-10 = 3 slots (line-local), prevEnded', d.lenSlots(five) === 3 && d.tapW.prevEnded, syls(L1));
check('0 after the last word ends the pass', !d.tapW.on, 'on ' + d.tapW.on + ' toast "' + toast() + '"');
// ---- 1d. keys route to the tap functions, Backspace goes back ----
d.setSel(null); at(el, 0); d.tapStart();
key(' '); check('Space key = tapHit', d.tapW.idx === 1, 'idx ' + d.tapW.idx);
at(el, 6); key(' '); check('second Space', d.tapW.idx === 2 && two.pos === 6, syls(L0));
key('Backspace'); check('Backspace goes back one word', d.tapW.idx === 1 && d.tapW.prev.y === one, 'idx ' + d.tapW.idx);
at(el, 8); key(' '); check('re-tap two at slot 8', two.pos === 8 && d.lenSlots(one) === 3, syls(L0));
at(el, 10); key('0'); check('0 key = tapRest: two = 2', d.lenSlots(two) === 2, syls(L0));
key('Escape'); check('Escape = tapStop', !d.tapW.on);
// ---- 1e. tapPause / resume ----
d.setSel(null); at(el, 0); d.tapStart(); d.tapHit();
d.tapPause();
check('pause: paused, band stopped, hint says so', d.tapW.paused && !d.player.on && /Paused/.test($('stHint').textContent), 'hint "' + $('stHint').textContent + '"');
d.tapHit(); check('tap while paused: toast, nothing placed', toast() === 'Paused. Press Enter to resume.' && d.tapW.idx === 1, '"' + toast() + '"');
check('lane outline lost while paused (laneClear in player.stop)', laneChip() === null, 'lane chip: ' + laneChip());
d.tapPause();
check('resume: band on, not paused, tapping still on', d.player.on && !d.tapW.paused && d.tapW.on, 'on ' + d.player.on + ' paused ' + d.tapW.paused + ' tapW.on ' + d.tapW.on);
check('resume: the outline is back on "two"', laneChip() === 'two', 'lane chip: ' + laneChip());
say('LOG resume: slot0 ' + d.player.slot0 + ' el.currentTime ' + el.currentTime + ' el.paused ' + el.paused);
d.player.stop();
check('player.stop ends the pass', !d.tapW.on && !d.player.on);
// ---- 1f. no words ----
var keep = s.lines; s.lines = []; d.tapStart(); check('tapStart with no words: toast', toast() === 'Put some words on the sheet first' && !d.tapW.on, '"' + toast() + '"'); s.lines = keep;

// ---- 2. tapEndSlots edge cases ----
d.player.on = true;
var v2 = fresh(); sing(v2, 3.0, 3.75); // one sung 5 slots
d.cur().audio.voice = v2; one.pos = 0; two.pos = 8;
var p = { li: 0, y: one };
at(el, 6); check('cap 1 returns 1', d.tapEndSlots(s, p, 1, false) === 1, String(d.tapEndSlots(s, p, 1, false)));
at(el, 8); check('sung 5 with cap 6: rounds up to the cap (no one-sixteenth rest)', d.tapEndSlots(s, p, 6, false) === 6, String(d.tapEndSlots(s, p, 6, false)));
check('sung 5 with cap 8: 5', d.tapEndSlots(s, p, 8, false) === 5, String(d.tapEndSlots(s, p, 8, false)));
el.currentTime = 3.5; check('open=true, voice still sounding at the limit: null', d.tapEndSlots(s, p, 8, true) === null, String(d.tapEndSlots(s, p, 8, true)));
check('open=false, voice still sounding at the limit: the cap', d.tapEndSlots(s, p, 8, false) === 8, String(d.tapEndSlots(s, p, 8, false)));
el.currentTime = 3.05; check('limit within 80 ms of the onset: null', d.tapEndSlots(s, p, 8, false) === null, String(d.tapEndSlots(s, p, 8, false)));
el.currentTime = 6.0; check('open=true, voice stopped: the sung length', d.tapEndSlots(s, p, 8, true) === 5, String(d.tapEndSlots(s, p, 8, true)));
check('cap 0.4 is treated as 1', d.tapEndSlots(s, p, 0.4, false) === 1, String(d.tapEndSlots(s, p, 0.4, false)));
var v3 = fresh(600); sing(v3, 3.0, 3.45); sing(v3, 5.55, 6.2); d.cur().audio.voice = v3; // 6 s of curve
at(el, 30); check('curve (6 s) shorter than the limit, word ended inside it: 3', d.tapEndSlots(s, p, 8, false) === 3, String(d.tapEndSlots(s, p, 8, false)));
var y17 = d.normalize({ lines: [mkLine(['x'])] }).lines[0].syllables[0]; y17.pos = 17;
check('curve ends while the word still sounds: null (not the cap)', d.tapEndSlots(s, { li: 0, y: y17 }, 8, false) === null, String(d.tapEndSlots(s, { li: 0, y: y17 }, 8, false)));
d.cur().audio.voice = fresh(400); check('voice curve of 400 frames is ignored: null', d.tapEndSlots(s, p, 8, false) === null);
d.cur().audio.voice = null; check('no voice curve: null', d.tapEndSlots(s, p, 8, false) === null);
d.cur().audio.voice = v2; d.state.audioOn = false; check('audio off: null', d.tapEndSlots(s, p, 8, false) === null); d.state.audioOn = true;
d.cur().audio = null; check('no track: null', d.tapEndSlots(s, p, 8, false) === null);
check('no track: tapRest does nothing and does not throw', (function () { try { d.tapW.prev = p; d.tapW.on = true; d.tapRest(); d.tapW.on = false; return true; } catch (e) { return 'threw ' + e; } })() === true);
d.player.on = false;
