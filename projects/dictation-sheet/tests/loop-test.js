// - starts a loop at the red line, a bar long, with a [ bracket at its start and a ] at its end; dragging the ]
// sets the end to any spot; - again removes it; the band wraps at the exact end back to the exact start.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
function key(k) { document.getElementById('work').dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true })); }
function edges() { return Array.prototype.slice.call(document.querySelectorAll('.loopedge')); }
function bands() { return Array.prototype.slice.call(document.querySelectorAll('.loopband')); }
function L() { return d.loopSlots(d.cur().loop); }
s.time = '4/4'; s.bpm = 100; s.view = 'vocals'; d.cur().audio = null; d.state.audioOn = false; d.cur().sel = null; d.cur().loop = null; d.state.prefs.snap = '2'; d.state.tool = 'move';
s.lines = [{ kind: 'line', bars: 4, syllables: [mk(0, 'q', 'one'), mk(8, 'q', 'two'), mk(20, 'h', 'three'), mk(40, 'q', 'four')] }];
d.renderAll(); d.syncTools(); document.getElementById('work').focus();
// 1. - with the red line parked at slot 6
d.player.startSlot = 6; d.player.showAt(6);
key('-');
check('- starts a loop at the red line (slot 6), a bar long (to 22)', d.cur().loop && L().s0 === 6 && L().s1 === 22 && d.cur().loopOn !== false, JSON.stringify(d.cur().loop));
check('a [ and a ] bracket and a band are drawn', edges().length === 2 && edges()[0].classList.contains('a') && edges()[1].classList.contains('b') && bands().length >= 1);
var geo = d.editor.systems[0].geo, c0 = geo.cells[0], c1 = geo.cells[1], sw = (c0.x1 - c0.x0) / 16;
check('the [ sits at slot 6 and the ] at slot 22 on the sheet', Math.abs(parseFloat(edges()[0].style.left) - (c0.x0 + 6 * sw)) < 1 && Math.abs(parseFloat(edges()[1].style.left) - (c1.x0 + 6 * (c1.x1 - c1.x0) / 16)) < 1, edges().map(function (e) { return e.style.left; }).join(' '));
check('the Play panel says where it runs', /Loop from bar 1, beat 2&amp;?|Loop from bar 1, beat 2&/.test(document.getElementById('loopInfo').textContent) && /to bar 2, beat 2&/.test(document.getElementById('loopInfo').textContent), document.getElementById('loopInfo').textContent);
// 2. drag the ] to bar 3, beat 3 (slot 40)
var box = document.getElementById('system-0'), r = box.getBoundingClientRect(), eb = edges()[1], er = eb.getBoundingClientRect(), c2 = geo.cells[2];
var tx = r.left + c2.x0 + 8 * (c2.x1 - c2.x0) / 16 + 1, ty = er.top + 20;
eb.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: er.left + 7, clientY: ty, button: 0, pointerId: 9 }));
window.dispatchEvent(new PointerEvent('pointermove', { bubbles: true, clientX: tx, clientY: ty, pointerId: 9 }));
check('while dragging the ] follows (a preview, the loop itself unchanged)', L().s1 === 22 && Math.abs(parseFloat(edges()[1].style.left) - (c2.x0 + 8 * (c2.x1 - c2.x0) / 16)) < 1, edges()[1] && edges()[1].style.left);
window.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: tx, clientY: ty, pointerId: 9 }));
check('dropped at bar 3 beat 3: the loop runs 6 to 40', L().s0 === 6 && L().s1 === 40 && d.cur().loop.a === 0 && d.cur().loop.b === 2, JSON.stringify(d.cur().loop));
// the click that follows a drag does not turn the loop off
var bh = document.querySelectorAll('.barhit')[3], bhr = bh.getBoundingClientRect();
bh.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: bhr.left + 5, clientY: bhr.top + 5 }));
check('the click right after the drag leaves the loop on', d.cur().loopOn !== false);
// 3. the [ drags too, and a drag past the other edge swaps them
var ea = edges()[0], ear = ea.getBoundingClientRect();
ea.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: ear.left + 7, clientY: ty, button: 0, pointerId: 10 }));
window.dispatchEvent(new PointerEvent('pointermove', { bubbles: true, clientX: r.left + c0.x0 + 2 * sw + 1, clientY: ty, pointerId: 10 }));
window.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 10 }));
check('the [ dragged to slot 2: the loop runs 2 to 40', L().s0 === 2 && L().s1 === 40, JSON.stringify(L()));
// 4. playing: the band wraps at 40 back to 2
d.player.startSlot = -1; d.player.start();
check('Play starts at the loop start (2)', d.player.on && d.player.slot0 === 2 && d.player.loopS0 === 2 && d.player.loopS1 === 40, 'slot0 ' + d.player.slot0 + ' loop ' + d.player.loopS0 + '-' + d.player.loopS1);
d.player.slot0 = 39.95; d.player.t0 = d.player.now() - 0.2; d.player.frame();
check('past slot 40 the band wraps back to 2 (and keeps the time run past the end)', d.player.slot0 === 2 && d.player.position() >= 2 && d.player.position() < 4, 'slot0 ' + d.player.slot0 + ' at ' + d.player.position().toFixed(2));
d.player.stop();
// 5. - again removes it
key('-');
check('- again removes the loop and its marks', !d.cur().loop && edges().length === 0 && bands().length === 0 && d.player.loopS0 === -1);
// 6. - while nothing is parked and a word is selected: from that word
d.player.startSlot = -1; d.cur().sel = { li: 0, si: 2 };
key('-');
check('with no red line parked, - starts at the selected word (slot 20)', L() && L().s0 === 20 && L().s1 === 36, JSON.stringify(L()));
key('-'); d.cur().sel = null;
// 7. - in the word box is still the hyphen
d.state.tool = 'add'; d.syncTools(); d.addNoteAt(0, 44);
var wb = document.querySelector('.syl-chip.editing'); wb.textContent = 'ever';
var rr = document.createRange(); rr.setStart(wb.firstChild, 2); rr.collapse(true); window.getSelection().removeAllRanges(); window.getSelection().addRange(rr);
wb.dispatchEvent(new KeyboardEvent('keydown', { key: '-', bubbles: true, cancelable: true }));
check('- in the word box cuts the word, no loop', !d.cur().loop && d.sortedSyls(d.S().lines[0]).some(function (y) { return y.text === 'ev' && y.hy; }));
var nb = document.querySelector('.syl-chip.editing'); if (nb) nb.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
d.state.tool = 'move'; d.syncTools();
// 8. an edit that adds a bar before the loop's end: the loop moves with the music, and the running band follows
s = d.S();
s.lines = [{ kind: 'line', bars: 1, syllables: [mk(0, 'q', 'one'), mk(4, 'q', 'two'), mk(12, 'q', 'three')] }, { kind: 'line', bars: 2, syllables: [mk(0, 'q', 'four'), mk(8, 'q', 'five')] }];
d.cur().sel = null; d.renderAll();
d.cur().loop = d.makeLoop(4, 25); d.cur().loopOn = true; d.applyLoop();
d.player.startSlot = 4; d.player.start();
check('setup: loop from "two" (4) to just past "five" (25), playing', L().s0 === 4 && L().s1 === 25 && d.player.loopS1 === 25);
var c3 = Array.prototype.filter.call(document.querySelectorAll('.syl-chip'), function (x) { return x.textContent === 'three'; })[0];
c3.dispatchEvent(new MouseEvent('dblclick', { bubbles: true })); var eb3 = document.querySelector('.syl-chip.editing'); eb3.textContent = 'tree';
eb3.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
setTimeout(function () {
  var nb2 = document.querySelector('.syl-chip.editing'); if (nb2) nb2.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
  var five = d.barOrdinal(d.S(), 1, 0) * 16 + 8;
  check('line 1 grew a bar, "five" is now at slot ' + five + ', and the loop still runs from "two" to just past "five"', d.lineBars(d.S().lines[0], 16) === 2 && L().s0 === 4 && L().s1 === five + 1, JSON.stringify(L()));
  check('the running band loops over the same music', d.player.on && d.player.loopS0 === 4 && d.player.loopS1 === five + 1, d.player.loopS0 + '-' + d.player.loopS1);
  check('the ] bracket is drawn at the new end', document.querySelectorAll('.loopedge').length === 2);
  d.player.stop();
  // undo (back to before the bar was added) swaps the lines out: the loop keeps its place by line number
  while (d.lineBars(d.S().lines[0], 16) > 1 && d.cur().undo.length) d.undo();
  check('after undo the loop is back over "two" to "five" (25)', L().s0 === 4 && L().s1 === 25, JSON.stringify(L()));
  d.cur().loop = null; d.applyLoop();
  say('LOG done');
}, 100);
