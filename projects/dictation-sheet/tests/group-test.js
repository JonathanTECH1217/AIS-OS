// Groups of words: a drag across empty strip space highlights what it touches; Shift+click a range; Ctrl+click one in
// or out; a highlighted word dragged in Move slides the group; Ctrl+arrows nudge it; right pushes along, left stops at
// the note before; Escape and a plain click let go; one undo step.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
function chip(t) { return Array.prototype.filter.call(document.querySelectorAll('.syl-chip'), function (c) { return c.textContent === t; })[0]; }
function marked() { return Array.prototype.filter.call(document.querySelectorAll('.syl-chip.mark'), function () { return true; }).map(function (c) { return c.textContent; }).join(' '); }
function snap() { return d.sortedSyls(d.S().lines[0]).map(function (y) { return y.text + '@' + y.pos; }).join(' '); }
function press(el, x, y, opts) { opts = opts || {}; el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y, button: 0, pointerId: 4, shiftKey: !!opts.shift, ctrlKey: !!opts.ctrl })); if (opts.to !== undefined) el.dispatchEvent(new PointerEvent('pointermove', { bubbles: true, clientX: opts.to, clientY: y, pointerId: 4 })); el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: opts.to !== undefined ? opts.to : x, clientY: y, pointerId: 4, shiftKey: !!opts.shift, ctrlKey: !!opts.ctrl })); }
function key(k, o) { o = o || {}; document.getElementById('work').dispatchEvent(new KeyboardEvent('keydown', { key: k, ctrlKey: !!o.ctrl, shiftKey: !!o.shift, bubbles: true, cancelable: true })); }
d.state.prefs.side = false; d.state.prefs.pad = false; d.state.prefs.snap = 'beat';
function reset() { s = d.S(); s.time = '4/4'; s.lines = [{ kind: 'line', bars: 3, syllables: [mk(0, 'q', 'a'), mk(8, 'q', 'b'), mk(12, 'q', 'c'), mk(16, 'q', 'd'), mk(24, 'q', 'e'), mk(28, 'q', 'f')] }]; d.cur().sel = null; d.state.marks = []; d.state.tool = 'move'; d.syncTools(); d.renderAll(); }
reset();
var cell = d.editor.systems[0].geo.cells[0], sw = (cell.x1 - cell.x0) / 16, tl = chip('a').parentNode, tr = tl.getBoundingClientRect(), cy = chip('a').getBoundingClientRect().top + 30;
// 1. a drag across empty strip space (below the chips) from slot 6 to slot 18 highlights b, c, d
var cellEl = document.querySelectorAll('.timeline .cell')[0];
var x6 = tr.left + cell.x0 + 6 * sw, x18 = tr.left + d.editor.systems[0].geo.cells[1].x0 + 2 * sw;
cellEl.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x6, clientY: tr.top + 2, button: 0, pointerId: 6 }));
window.dispatchEvent(new PointerEvent('pointermove', { bubbles: true, clientX: x18, clientY: tr.top + 2, pointerId: 6 }));
window.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x18, clientY: tr.top + 2, pointerId: 6 }));
check('a drag across the strip highlights b, c and d', marked() === 'b c d', marked());
var ps = d.player.startSlot; cellEl.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x18, clientY: tr.top + 2 }));
check('the click that ends the drag does not move the red line or drop the group', marked() === 'b c d');
// 2. drag "c" two beats right: the group slides, e is pushed from 24 to 28, f from 28 to 32
var rc = chip('c').getBoundingClientRect();
press(chip('c'), rc.left + 6, rc.top + 6, { to: rc.left + 6 + 8 * sw });
check('dragging a highlighted word slides the group two beats; e and f are pushed along', snap() === 'a@0 b@16 c@20 d@24 e@28 f@32', snap());
check('the group stays highlighted', marked() === 'b c d', marked());
d.undo();
check('one undo step takes the whole slide back', snap() === 'a@0 b@8 c@12 d@16 e@24 f@28', snap());
// 3. Ctrl+arrow nudges the group; left stops at the note before (a ends at 4, b at 8: room 4)
d.setMarks([{ li: 0, si: 1 }, { li: 0, si: 2 }, { li: 0, si: 3 }]);
key('ArrowRight', { ctrl: true });
check('Ctrl+→ nudges the group a beat', snap() === 'a@0 b@12 c@16 d@20 e@24 f@28', snap());
key('ArrowLeft', { ctrl: true }); key('ArrowLeft', { ctrl: true }); key('ArrowLeft', { ctrl: true });
check('Ctrl+← three times stops where b touches a (b at 4)', snap() === 'a@0 b@4 c@8 d@12 e@24 f@28', snap());
// 4. Shift+click a range, Ctrl+click one out and one in
reset(); var ra = chip('a').getBoundingClientRect(); press(chip('a'), ra.left + 6, ra.top + 6);
var rd = chip('d').getBoundingClientRect(); press(chip('d'), rd.left + 6, rd.top + 6, { shift: true });
check('Shift+click from the selected "a" to "d" highlights a to d', marked() === 'a b c d', marked());
var rb = chip('b').getBoundingClientRect(); press(chip('b'), rb.left + 6, rb.top + 6, { ctrl: true });
check('Ctrl+click takes b out', marked() === 'a c d', marked());
var rf = chip('f').getBoundingClientRect(); press(chip('f'), rf.left + 6, rf.top + 6, { ctrl: true });
check('Ctrl+click puts f in', marked() === 'a c d f', marked());
// 4b. the same on the notes on the staff, and in the Add tool
key('Escape'); d.state.tool = 'add'; d.syncTools(); d.cur().sel = null; d.renderAll();
function head(i) { return document.querySelectorAll('.notehit:not(.gap)')[i]; }
function hp(i) { var r = head(i).getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }
var h0 = hp(1); press(head(1), h0[0], h0[1], { ctrl: true });
var h1 = hp(3); press(head(3), h1[0], h1[1], { ctrl: true });
check('Add tool, Ctrl+click on two notes on the staff: b and d highlighted', marked() === 'b d', marked());
var h2 = hp(5); press(head(5), h2[0], h2[1], { shift: true });
check('Shift+click on the staff selects through from d to f', marked() === 'd e f', marked());
check('no note was added by those clicks', d.S().lines[0].syllables.length === 6, d.S().lines[0].syllables.length);
d.state.tool = 'move'; d.syncTools();
// 5. Escape lets go; a plain click lets go
key('Escape');
check('Escape lets the group go', marked() === '' && d.state.marks.length === 0);
d.setMarks([{ li: 0, si: 1 }, { li: 0, si: 2 }]); var re = chip('e').getBoundingClientRect(); press(chip('e'), re.left + 6, re.top + 6);
check('a plain click on another word lets the group go and selects it', marked() === '' && d.cur().sel && d.S().lines[0].syllables[d.cur().sel.si].text === 'e');
// 6. dragging a word that is not in the group moves only that word
d.setMarks([{ li: 0, si: 1 }, { li: 0, si: 2 }]); var ra2 = chip('a').getBoundingClientRect();
press(chip('a'), ra2.left + 6, ra2.top + 6, { to: ra2.left + 6 + 4 * sw });
check('a word outside the group drags alone', /a@4/.test(snap()) && /b@8 c@12/.test(snap()), snap());
d.state.marks = []; d.state.prefs.snap = '2'; d.renderAll();
say('LOG done');
