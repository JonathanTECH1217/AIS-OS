// ] and [ grow and shrink the selected note by the Snap step (Shift: a sixteenth): the note keeps its start, grows to
// the right and pushes the notes after it later; shrinking leaves a rest. With nothing selected [ and ] still set the
// loop. Undo and redo keep the view where it was.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
function key(k, shift) { document.getElementById('work').dispatchEvent(new KeyboardEvent('keydown', { key: k, shiftKey: !!shift, bubbles: true, cancelable: true })); }
function snap() { return d.sortedSyls(d.S().lines[0]).map(function (y) { return y.text + '@' + y.pos + 'x' + d.lenSlots(y); }).join(' '); }
s.time = '4/4'; s.bpm = 100; s.view = 'vocals'; s.spotify = null; s.filled = null; d.cur().audio = null; d.state.audioOn = false; d.cur().undo = []; d.cur().loop = null; d.state.prefs.pad = false;
d.state.prefs.snap = '2'; d.state.tool = 'move';
s.lines = [{ kind: 'line', bars: 2, syllables: [mk(0, 'q', 'one'), mk(4, '8', 'two'), mk(6, '8', 'three'), mk(12, 'q', 'four')] }];
d.renderAll(); d.cur().sel = { li: 0, si: 1 }; d.renderAll(); document.getElementById('work').focus();
// 1. ] grows "two" by an eighth: it stays at 4, runs to 8, "three" is pushed from 6 to 8, "four" stays (no overlap)
key(']');
check('] grows "two" by an eighth, keeping its start; "three" pushed from 6 to 8', snap() === 'one@0x4 two@4x4 three@8x2 four@12x4', snap());
key(']');
check('] again: "two" a dotted quarter, "three" to 10, "four" untouched', snap() === 'one@0x4 two@4x6 three@10x2 four@12x4', snap());
key(']');
check('] again: "three" pushed to 12 runs into "four", which goes on to 14', snap() === 'one@0x4 two@4x8 three@12x2 four@14x4', snap());
// 2. [ shrinks it, leaving a rest; Shift a sixteenth
key('[');
check('[ shrinks "two" by an eighth, the notes after stay (a rest opens)', snap() === 'one@0x4 two@4x6 three@12x2 four@14x4', snap());
key('{', true);
check('Shift+[ shrinks by a sixteenth', snap() === 'one@0x4 two@4x5 three@12x2 four@14x4', snap());
key('}', true);
check('Shift+] grows by a sixteenth', snap() === 'one@0x4 two@4x6 three@12x2 four@14x4', snap());
check('the selection stays on "two"', d.cur().sel && d.S().lines[0].syllables[d.cur().sel.si].text === 'two');
// 3. undo steps it back, one press per resize
var steps = d.cur().undo.length; d.undo();
check('undo takes back one resize', snap() === 'one@0x4 two@4x5 three@12x2 four@14x4' && d.cur().undo.length === steps - 1, snap());
// 4. with nothing selected [ and ] set the loop as before
d.cur().sel = null; d.renderAll(); document.getElementById('work').focus(); var before = snap();
key('[');
check('with nothing selected [ changes no note', snap() === before, snap());
// 5. undo and redo keep the view where it was
s = d.S(); var lines = []; for (var i = 0; i < 14; i++) lines.push({ kind: 'line', bars: 2, syllables: [mk(0, 'q', 'w' + i), mk(4, 'q', 'x' + i)] });
s.lines = lines; d.cur().undo = []; d.renderAll();
var w = document.getElementById('work'); w.scrollTop = 600; var top0 = w.scrollTop;
d.cur().sel = { li: 9, si: 0 }; key(']');
d.undo();
check('after undo the page is scrolled where it was (' + top0 + ')', top0 > 100 && Math.abs(w.scrollTop - top0) < 2, 'scrollTop ' + w.scrollTop + ', was ' + top0);
d.redo();
check('after redo too', Math.abs(w.scrollTop - top0) < 2, 'scrollTop ' + w.scrollTop);
check('an edit that redraws the sheet keeps the view too', (function () { w.scrollTop = 500; var t = w.scrollTop; d.cur().sel = { li: 9, si: 0 }; key(']'); return Math.abs(w.scrollTop - t) < 2; })(), 'scrollTop ' + w.scrollTop);
// 6. while typing a word, ] and [ resize its note and the box stays open; Enter's next note starts where it ends
s = d.S(); s.lines = [{ kind: 'line', bars: 2, syllables: [] }]; d.cur().sel = null; d.state.tool = 'add'; d.syncTools(); d.renderAll();
d.addNoteAt(0, 0);
function box() { return document.querySelector('.syl-chip.editing'); }
function bkey(k, shift) { box().dispatchEvent(new KeyboardEvent('keydown', { key: k, shiftKey: !!shift, bubbles: true, cancelable: true })); }
box().textContent = 'Ev';
bkey(']');
check('] in the word box: the new note (a quarter) grows by an eighth to 6 slots, the box stays open with "Ev"', d.lenSlots(d.S().lines[0].syllables[0]) === 6 && !!box() && box().textContent === 'Ev', d.lenSlots(d.S().lines[0].syllables[0]) + ' slots, box ' + (box() && box().textContent));
bkey('[', false); bkey('{', true);
check('[ then Shift+[ : 6 - 2 - 1 = 3 slots, still typing', d.lenSlots(d.S().lines[0].syllables[0]) === 3 && !!box(), d.lenSlots(d.S().lines[0].syllables[0]));
bkey('Enter');
setTimeout(function () {
  var ys = d.sortedSyls(d.S().lines[0]);
  check('Enter keeps "Ev" and opens the next note (an eighth) where it ends, slot 3', ys.length === 2 && ys[0].text === 'Ev' && ys[1].pos === 3 && d.lenSlots(ys[1]) === 2 && !!box(), ys.map(function (y) { return (y.text || '_') + '@' + y.pos + 'x' + d.lenSlots(y); }).join(' '));
  bkey('Escape'); d.state.tool = 'move'; d.syncTools();
  say('LOG done');
}, 50);
