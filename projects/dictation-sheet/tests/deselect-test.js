// A click on the sheet that is not on a note lets go of the selected note (and a highlighted group); the click still
// does its job; clicks on a note, or on the pad, keep or change the selection as before.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
function chip(t) { return Array.prototype.filter.call(document.querySelectorAll('.syl-chip'), function (c) { return c.textContent === t; })[0]; }
function down(el, x, y, o) { o = o || {}; el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, pointerId: 8, shiftKey: !!o.shift })); el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y, pointerId: 8, shiftKey: !!o.shift })); el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y, shiftKey: !!o.shift })); }
function selText() { var c = d.cur().sel; return c ? d.S().lines[c.li].syllables[c.si].text : null; }
d.state.prefs.side = false; d.state.prefs.pad = false; d.cur().audio = null; d.player.keyTone = function () {};
s = d.S(); s.time = '4/4'; s.view = 'vocals'; s.key = { tonic: 'C', mode: 'major', laMinor: true };
s.lines = [{ kind: 'line', bars: 2, syllables: [mk(0, 'q', 'one'), mk(4, 'q', 'two'), mk(12, 'q', 'three')] }];
d.state.tool = 'move'; d.syncTools(); d.cur().sel = { li: 0, si: 1 }; d.renderAll();
check('setup: "two" selected (blue)', selText() === 'two' && !!document.querySelector('.syl-chip.on'));
// 1. a click on empty bar space
var bh = document.querySelectorAll('.barhit')[1], r = bh.getBoundingClientRect();
down(bh, r.left + r.width * 0.6, r.top + 10);
check('a click on an empty spot of a bar lets go of it', selText() === null && !document.querySelector('.syl-chip.on'));
// 2. a click on a rest (the gap between "two" and "three")
d.cur().sel = { li: 0, si: 0 }; d.renderAll(); var gap = document.querySelector('.notehit.gap'), gr = gap.getBoundingClientRect();
down(gap, gr.left + gr.width / 2, gr.top + gr.height / 2);
check('a click on a rest lets go of it', selText() === null);
// 3. a click on the strip's empty space
d.cur().sel = { li: 0, si: 0 }; d.renderAll(); var cellEl = document.querySelectorAll('.timeline .cell')[1], cr = cellEl.getBoundingClientRect();
down(cellEl, cr.left + cr.width * 0.8, cr.top + 3);
check('a click on the empty strip lets go of it', selText() === null);
// 4. a click on the sheet's blank margin
d.cur().sel = { li: 0, si: 0 }; d.renderAll(); var work = document.getElementById('work'), wr = work.getBoundingClientRect();
down(work, wr.left + wr.width - 20, wr.bottom - 20);
check('a click on the blank page lets go of it', selText() === null);
// 5. a highlighted group lets go too; with Shift it stays
d.setMarks([{ li: 0, si: 0 }, { li: 0, si: 1 }]); cellEl = document.querySelectorAll('.timeline .cell')[1]; cr = cellEl.getBoundingClientRect();
down(cellEl, cr.left + cr.width * 0.8, cr.top + 3, { shift: true });
check('Shift+click on empty space keeps the group', d.state.marks.length === 2);
cellEl = document.querySelectorAll('.timeline .cell')[1]; cr = cellEl.getBoundingClientRect();
down(cellEl, cr.left + cr.width * 0.8, cr.top + 3);
check('a plain click on empty space lets the group go', d.state.marks.length === 0 && !document.querySelector('.syl-chip.mark'));
// 6. a click on a note selects it; a click on the pad keeps the selection (and writes to it)
var c3 = chip('three'), r3 = c3.getBoundingClientRect(); down(c3, r3.left + 8, r3.top + 8);
check('a click on a note still selects it', selText() === 'three');
d.cur().sel = { li: 0, si: 0 }; d.state.prefs.pad = true; d.renderAll();
document.querySelectorAll('#padKeys button')[4].click();
check('a click on the pad keeps the selection and writes to it (one is now sol, "two" selected)', d.S().lines[0].syllables[0].sol === 'sol' && selText() === 'two', d.S().lines[0].syllables[0].sol + ' | ' + selText());
d.state.prefs.pad = false; d.cur().sel = null; d.renderAll();
say('LOG done');
