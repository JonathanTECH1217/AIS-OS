// Chip drag (attachChip/place/dropAt) and grip resize (attachGrip/setSlots/applyLength) through synthetic pointer events.
var d = window.__ds, $ = function (id) { return document.getElementById(id); };
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mkLine(syls, bars) { return { kind: 'line', bars: bars || 1, syllables: syls.map(function (t, i) { return typeof t === 'string' ? { text: t, pos: i * 4 } : t; }) }; }
function build(lines) { var s = d.S(); s.time = '4/4'; s.bpm = 100; s.title = 'drag'; s.audio = null; s.lines = d.normalize({ lines: lines }).lines; d.state.audioOn = false; d.player.on = false; d.state.prefs.snap = '2'; d.state.tool = 'move'; d.setSel(null); d.renderAll(); return s; }
function syls(l) { return d.sortedSyls(l).map(function (y) { return y.text + '@' + y.pos + 'x' + d.lenSlots(y); }).join(' '); }
function chipOf(li, pos) { var f = null; d.editor.systems.forEach(function (sy) { (sy.chips || []).forEach(function (c) { if (c.li === li && c.pos === pos) f = c; }); }); return f; }
function cellOf(li, b) { var f = null; d.editor.systems.forEach(function (sy) { if (sy.geo) sy.geo.cells.forEach(function (c) { if (c.li === li && c.b === b) f = c; }); }); return f; }
function sysOf(li, b) { var f = -1; d.editor.systems.forEach(function (sy, i) { if (sy.geo) sy.geo.cells.forEach(function (c) { if (c.li === li && c.b === b) f = i; }); }); return f; }
function pe(type, x, y, extra) { var o = { bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 1, pointerId: 7, pointerType: 'mouse', isPrimary: true }; if (extra) Object.keys(extra).forEach(function (k) { o[k] = extra[k]; }); return new PointerEvent(type, o); }
function stub(el) { el.setPointerCapture = function () {}; el.hasPointerCapture = function () { return true; }; }
function drag(el, dx, shift) { var r = el.getBoundingClientRect(), x0 = r.left + 6, y0 = r.top + r.height / 2; el.dispatchEvent(pe('pointerdown', x0, y0)); el.dispatchEvent(pe('pointermove', x0 + dx / 2, y0, { shiftKey: !!shift })); el.dispatchEvent(pe('pointermove', x0 + dx, y0, { shiftKey: !!shift })); el.dispatchEvent(pe('pointerup', x0 + dx, y0, { shiftKey: !!shift })); }
// drag a chip so its left edge lands on slot `slot` of cell (li, b)
function dragTo(chip, li, b, slot, shift) { var cell = cellOf(li, b), sw = (cell.x1 - cell.x0) / 16, dx = (cell.x0 + slot * sw) - parseFloat(chip.el.style.left); stub(chip.el); drag(chip.el, dx, shift); }
function dups(l) { var seen = {}, out = []; l.syllables.forEach(function (y) { if (seen[y.pos]) out.push(y.text + '/' + seen[y.pos] + '@' + y.pos); seen[y.pos] = y.text; }); return out; }

// ---- 0. does a synthetic pointerdown reach the drag code without a capture stub? (attachChip has no try/catch around setPointerCapture) ----
var s = build([mkLine(['one', 'two', 'three']), mkLine(['four', 'five'])]), L0 = s.lines[0], L1 = s.lines[1];
var c3 = chipOf(0, 8), cell0 = cellOf(0, 0), sw = (cell0.x1 - cell0.x0) / 16;
var threw = null; window.addEventListener('error', function onE(e) { threw = e.message; }, { once: true });
try { drag(c3.el, 4 * sw); } catch (e) { threw = 'sync ' + e; }
say('LOG unstubbed synthetic drag: moved? ' + (L0.syllables[2].pos !== 8) + ' error: ' + threw + ' (a real pointer never throws here)');
if (L0.syllables[2].pos !== 8) { L0.syllables[2].pos = 8; d.renderAll(); }

// ---- 3a. move a chip to another beat on its line ----
s = build([mkLine(['one', 'two', 'three']), mkLine(['four', 'five'])]); L0 = s.lines[0]; L1 = s.lines[1];
dragTo(chipOf(0, 8), 0, 0, 12);
check('three moved to beat 4 (slot 12)', L0.syllables[2].pos === 12 && d.lineBars(L0, 16) === 1, syls(L0) + ' lineBars ' + d.lineBars(L0, 16));
check('drag took an undo step; undo puts it back', (function () { d.undo(); return d.S().lines[0].syllables[2].pos === 8; })(), syls(d.S().lines[0]));
s = d.S(); L0 = s.lines[0]; L1 = s.lines[1];
dragTo(chipOf(0, 8), 0, 0, 14);
check('three to slot 14: the note spills over, the line grows to 2 bars through minBars (line.bars stays 1)', L0.syllables[2].pos === 14 && d.minBars(L0, 16) === 2 && d.lineBars(L0, 16) === 2 && L0.bars === 1, syls(L0) + ' bars ' + L0.bars + ' lineBars ' + d.lineBars(L0, 16));
check('layout now L0b0 L0b1 L1b0', !!cellOf(0, 1) && cellOf(0, 1).x0 < cellOf(1, 0).x0, d.editor.systems.map(function (sy) { return sy.bars ? sy.bars.map(function (b) { return 'L' + b.li + 'b' + b.b; }).join(',') : 'h'; }).join('|'));
check('no minus button on line 0 (lineBars == minBars), one on line 1? none either', document.querySelectorAll('.cellbtn').length === 2, document.querySelectorAll('.cellbtn').length + ' cell buttons');
// ---- 3b. drag past the line's end: the next cell belongs to line 1 ----
dragTo(chipOf(0, 0), 1, 0, 4);
check('one dragged past line 0 into L1 bar 1 slot 4: moves to line 1, five (at 4) pushed to 8', L1.syllables.length === 3 && L0.syllables.length === 2 && d.sortedSyls(L1).map(function (y) { return y.text + '@' + y.pos; }).join(' ') === 'four@0 one@4 five@8', 'L0: ' + syls(L0) + ' | L1: ' + syls(L1));
d.undo(); s = d.S(); L0 = s.lines[0]; L1 = s.lines[1];
check('undo restores both lines', L0.syllables.length === 3 && L1.syllables.length === 2, 'L0: ' + syls(L0) + ' | L1: ' + syls(L1));
// past the system's very end
var cFive = chipOf(1, 4); stub(cFive.el); drag(cFive.el, 3000);
check('five dragged far past the end: clamps to slot 15 of the last cell, line 1 grows a bar', L1.syllables[1].pos === 15 && d.lineBars(L1, 16) === 2, syls(L1) + ' lineBars ' + d.lineBars(L1, 16));
d.undo(); s = d.S(); L0 = s.lines[0]; L1 = s.lines[1];
// past the start of the system
var cFour = chipOf(1, 0); stub(cFour.el); drag(cFour.el, -3000);
check('four dragged far left: lands on line 0 slot 0 (system start), one pushed', L0.syllables.length === 4 && d.sortedSyls(L0)[0].text === 'four' && d.sortedSyls(L0)[0].pos === 0, 'L0: ' + syls(L0) + ' | L1: ' + syls(L1));
// ---- 3c. drag onto another chip ----
s = build([mkLine(['A', 'B', 'C', 'D'])]); L0 = s.lines[0];
dragTo(chipOf(0, 12), 0, 0, 4);
check('D dropped on B\'s start: D@4, B and C pushed by D\'s length', syls(L0) === 'A@0x4 D@4x4 B@8x4 C@12x4', syls(L0));
s = build([mkLine(['A', 'B', 'C', 'D'])]); L0 = s.lines[0];
dragTo(chipOf(0, 12), 0, 0, 2);
check('D dropped inside A (slot 2): lands after A at 4 and B is pushed, no two notes on one slot', dups(L0).length === 0 && d.sortedSyls(L0).map(function (y) { return y.text + '@' + y.pos; }).join(' ') === 'A@0 D@4 B@8 C@12', syls(L0) + ' stacked: ' + JSON.stringify(dups(L0)));
// the same rule straight through dropAt, both array orders
s = build([mkLine(['A', 'B', 'C'])]); L0 = s.lines[0]; d.dropAt(L0, L0.syllables[2], 2);
say('LOG dropAt(C -> 2) with array order A,B,C: ' + syls(L0) + ' stacked ' + JSON.stringify(dups(L0)));
s = build([mkLine([{ text: 'A', pos: 0 }, { text: 'C', pos: 8 }, { text: 'B', pos: 4 }])]); L0 = s.lines[0]; d.dropAt(L0, L0.syllables[1], 2);
say('LOG dropAt(C -> 2) with array order A,C,B: ' + syls(L0) + ' stacked ' + JSON.stringify(dups(L0)));
// ---- 3d. grouped chips ----
s = build([mkLine([{ text: 'Twin', pos: 0, hy: true }, { text: 'kle', pos: 4 }, { text: 'lit', pos: 8, hy: true }, { text: 'tle', pos: 12 }, { text: 'star', pos: 16 }])]); L0 = s.lines[0];
var g = chipOf(0, 0); check('one chip for the word Twinkle, spanning both notes', g && g.el.textContent === 'Twinkle' && g.end === 8 && g.el.classList.contains('grp'), g && g.el.textContent + ' end ' + g.end);
dragTo(g, 0, 0, 8);
check('group dragged onto "lit": both members move together, the rest pushed behind', d.sortedSyls(L0).map(function (y) { return y.text + '@' + y.pos; }).join(' ') === 'Twin@8 kle@12 lit@16 tle@20 star@24', syls(L0));
s = build([mkLine([{ text: 'beau', pos: 0, hy: true }, { text: 'ti', pos: 4, hy: true }, { text: 'ful', pos: 8 }, { text: 'star', pos: 12 }])]); L0 = s.lines[0];
dragTo(chipOf(0, 0), 0, 0, 8);
check('3-note group dragged to 8 with "star" at 12: no note stacked on another', dups(L0).length === 0, syls(L0) + ' stacked: ' + JSON.stringify(dups(L0)));
s = build([mkLine([{ text: 'beau', pos: 0, hy: true }, { text: 'ti', pos: 4, hy: true }, { text: 'ful', pos: 8 }, { text: 'star', pos: 12 }])]); L0 = s.lines[0];
dragTo(chipOf(0, 0), 0, 0, 6);
check('3-note group dragged to 6 with "star" at 12: no note stacked on another', dups(L0).length === 0, syls(L0) + ' stacked: ' + JSON.stringify(dups(L0)));
// group dragged to another line
s = build([mkLine([{ text: 'Twin', pos: 0, hy: true }, { text: 'kle', pos: 4 }, { text: 'star', pos: 8 }]), mkLine(['four', 'five'])]); L0 = s.lines[0]; L1 = s.lines[1];
dragTo(chipOf(0, 0), 1, 0, 8);
check('group dragged to line 1 slot 8: both members arrive linked, in order', d.sortedSyls(L1).map(function (y) { return y.text + '@' + y.pos + (y.hy ? '-' : ''); }).join(' ') === 'four@0 five@4 Twin@8- kle@12' && L0.syllables.length === 1, 'L0: ' + syls(L0) + ' | L1: ' + syls(L1));
// marks after a cross-line move
s = build([mkLine(['one', 'two', 'three']), mkLine(['four'])]); L0 = s.lines[0]; L1 = s.lines[1];
d.state.marks = [{ li: 0, si: 2 }]; dragTo(chipOf(0, 0), 1, 0, 4);
check('a mark on "three" (si 2) still points at "three" after "one" left the line', (function () { var m = d.state.marks[0]; return m && L0.syllables[m.si] && L0.syllables[m.si].text === 'three'; })(), 'marks ' + JSON.stringify(d.state.marks) + ' L0 ' + L0.syllables.map(function (y) { return y.text; }).join(','));
d.clearMarks();
// ---- 4. grip resize ----
s = build([mkLine(['one', 'two', 'three']), mkLine(['four', 'five'])]); L0 = s.lines[0]; L1 = s.lines[1];
var c1 = chipOf(0, 0), grip = c1.el.querySelector('.grip'); cell0 = cellOf(0, 0); sw = (cell0.x1 - cell0.x0) / 16;
var lastCell = document.querySelector('.timeline .cell.last'), maxW = lastCell.offsetLeft + lastCell.offsetWidth - c1.el.offsetLeft - 3, baseW = c1.el.getBoundingClientRect().width;
var gr = grip.getBoundingClientRect(), gx = gr.left + gr.width / 2, gy = gr.top + gr.height / 2;
grip.dispatchEvent(pe('pointerdown', gx, gy)); grip.dispatchEvent(pe('pointermove', gx + 16 * sw, gy));
var previewW = parseFloat(c1.el.style.width), previewTitle = c1.el.title;
check('grip preview at +16 slots: width grows by 16 slots, title says 5 beats', Math.abs(previewW - (baseW + 16 * sw)) < 1 && previewTitle === '5 beats', 'width ' + previewW + ' expected ' + (baseW + 16 * sw) + ' title "' + previewTitle + '"');
grip.dispatchEvent(pe('pointermove', gx + 60 * sw, gy));
check('grip preview far right is clipped at the system end', Math.abs(parseFloat(c1.el.style.width) - maxW) < 1, 'width ' + c1.el.style.width + ' maxW ' + maxW);
grip.dispatchEvent(pe('pointermove', gx + 16 * sw, gy)); grip.dispatchEvent(pe('pointerup', gx + 16 * sw, gy));
var one = L0.syllables[0];
check('one is now 20 slots (whole + a beat), two and three pushed to 20 and 24', d.lenSlots(one) === 20 && one.len === 'w' && one.xs === 4 && L0.syllables[1].pos === 20 && L0.syllables[2].pos === 24, syls(L0) + ' len ' + one.len + ' xs ' + one.xs);
check('line 0 grew to 2 bars', d.lineBars(L0, 16) === 2, String(d.lineBars(L0, 16)));
var ev1 = d.barEvents(L0, 1, 16);
check('bar 2 carries "one" as a tied piece of 4 slots', ev1.length && ev1[0].items[0].carry === true && ev1[0].items[0].len === 4 && ev1[0].s === 0, JSON.stringify(ev1.map(function (e) { return { s: e.s, len: e.len, carry: !!e.items[0].carry, t: e.items[0].y.text }; })));
check('the staff drew tied pieces (a tie in the SVG)', document.querySelectorAll('#system-0 svg path.vf-stavetie, #system-0 svg .vf-stavetie').length > 0, document.querySelectorAll('.vf-stavetie').length + ' ties');
c1 = chipOf(0, 0); var cx = parseFloat(c1.el.style.left), sysX1 = d.editor.systems[sysOf(0, 0)].geo.cells.slice(-1)[0].x1;
check('chip width after the redraw = 20 slots less 3 px', Math.abs(parseFloat(c1.el.style.width) - (20 * sw - 3)) < 1, c1.el.style.width + ' vs ' + (20 * sw - 3));
// a note that runs past the system's last cell: chip clipped, carry in the next system
d.state.prefs.zoom = 300; L0.bars = 4; d.renderAll(); L0 = d.S().lines[0];
say('LOG systems at zoom 300: ' + d.editor.systems.map(function (sy) { return sy.bars ? sy.bars.map(function (b) { return 'L' + b.li + 'b' + b.b; }).join(',') : 'h'; }).join(' | '));
var three = L0.syllables[2]; three.pos = 40; d.setSlotsRaw(three, 20); d.renderAll(); L0 = d.S().lines[0];
var c40 = chipOf(0, 40), sysI = sysOf(0, 2), sx1 = d.editor.systems[sysI].geo.cells.slice(-1)[0].x1;
check('a 20-slot note at bar 3 slot 8 crossing the system break: chip clipped at the system end', c40 && parseFloat(c40.el.style.width) <= sx1 - parseFloat(c40.el.style.left) - 2 && c40.end === 60, c40 && ('left ' + c40.el.style.left + ' width ' + c40.el.style.width + ' sysX1 ' + sx1 + ' end ' + c40.end));
check('next system has no chip for it but the staff carries it (barEvents bar 4)', !chipOf(0, 48) && d.barEvents(L0, 3, 16).some(function (e) { return e.items[0].carry && e.items[0].y === three; }), JSON.stringify(d.barEvents(L0, 3, 16).map(function (e) { return { s: e.s, len: e.len, carry: !!e.items[0].carry }; })));
d.state.prefs.zoom = 200;
// past MAX_SLOTS and down to 1
s = build([mkLine(['one', 'two'])]); L0 = s.lines[0]; c1 = chipOf(0, 0); grip = c1.el.querySelector('.grip'); cell0 = cellOf(0, 0); sw = (cell0.x1 - cell0.x0) / 16;
gr = grip.getBoundingClientRect(); gx = gr.left + gr.width / 2; gy = gr.top + gr.height / 2;
grip.dispatchEvent(pe('pointerdown', gx, gy)); grip.dispatchEvent(pe('pointermove', gx + 200 * sw, gy)); grip.dispatchEvent(pe('pointerup', gx + 200 * sw, gy));
one = L0.syllables[0];
check('grip past MAX_SLOTS clamps to 64 (whole + 48), two pushed to 64, line 5 bars', d.lenSlots(one) === 64 && one.len === 'w' && one.xs === 48 && L0.syllables[1].pos === 64 && d.lineBars(L0, 16) === 5, syls(L0) + ' lineBars ' + d.lineBars(L0, 16) + ' toast "' + $('toast').textContent + '"');
c1 = chipOf(0, 0); grip = c1.el.querySelector('.grip'); gr = grip.getBoundingClientRect(); gx = gr.left + gr.width / 2; gy = gr.top + gr.height / 2;
grip.dispatchEvent(pe('pointerdown', gx, gy)); grip.dispatchEvent(pe('pointermove', gx - 300 * sw, gy)); grip.dispatchEvent(pe('pointerup', gx - 300 * sw, gy));
check('grip shrink to 1: a sixteenth; two stays at 64 (no pull back)', d.lenSlots(one) === 1 && one.len === '16' && !one.dot && one.xs === 0 && L0.syllables[1].pos === 64, syls(L0));
c1 = chipOf(0, 0); grip = c1.el.querySelector('.grip'); gr = grip.getBoundingClientRect(); gx = gr.left + gr.width / 2; gy = gr.top + gr.height / 2;
grip.dispatchEvent(pe('pointerdown', gx, gy)); grip.dispatchEvent(pe('pointermove', gx + 6 * sw, gy, { shiftKey: true })); grip.dispatchEvent(pe('pointerup', gx + 6 * sw, gy, { shiftKey: true }));
check('grip with Shift snaps to single sixteenths: 1 + 6 = 7 (quarter dotted + 1)', d.lenSlots(one) === 7 && one.len === 'q' && one.dot && one.xs === 1, syls(L0) + ' ' + one.len + (one.dot ? '.' : '') + '+' + one.xs);
check('grip with no movement leaves the note and takes no undo step', (function () { var n = d.cur().undo.length; c1 = chipOf(0, 0); grip = c1.el.querySelector('.grip'); gr = grip.getBoundingClientRect(); grip.dispatchEvent(pe('pointerdown', gr.left + 2, gr.top + 2)); grip.dispatchEvent(pe('pointerup', gr.left + 2, gr.top + 2)); return d.cur().undo.length === n && d.lenSlots(one) === 7; })());
say('LOG uncaught so far: ' + (threw || 'none'));
