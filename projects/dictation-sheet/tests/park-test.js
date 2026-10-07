// The red line parks half a bar before the selected word: on a click on its chip or its note, on the arrows between
// words; Play then starts there. A click on a bar afterwards sets its own spot; the Add tool keeps its cursor.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
function chip(text) { return Array.prototype.filter.call(document.querySelectorAll('.syl-chip'), function (c) { return c.textContent === text; })[0]; }
function shown() { return Array.prototype.filter.call(document.querySelectorAll('.playhead.track'), function (p) { return p.style.display === 'block'; }); }
function press(el, x, y) { el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y, button: 0, pointerId: 5 })); el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y, pointerId: 5 })); }
function key(k) { document.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true })); }
s.time = '4/4'; s.bpm = 100; s.view = 'vocals'; s.spotify = null; s.filled = null; d.cur().audio = null; d.state.audioOn = false; d.cur().sel = null; d.cur().undo = []; d.state.prefs.pad = false;
// line 1: "one" at bar 1 beat 2, "two" at bar 2 beat 3; line 2: "three" at its bar 1 beat 1 (bar 3 of the sheet)
s.lines = [{ kind: 'line', bars: 2, syllables: [mk(4, 'q', 'one'), mk(24, 'q', 'two')] }, { kind: 'line', bars: 2, syllables: [mk(0, 'q', 'three')] }];
d.state.tool = 'move'; d.syncTools(); d.renderAll(); d.player.startSlot = -1;
// 1. a click on a chip in Move parks the red line half a bar (8 slots) before the word
var c2 = chip('two'), r = c2.getBoundingClientRect(); press(c2, r.left + 6, r.top + 6);
check('"two" selected by a click on its chip', d.cur().sel && d.cur().sel.li === 0 && d.cur().sel.si === 1, JSON.stringify(d.cur().sel));
check('the red line parks half a bar before it: slot 24 - 8 = 16 (bar 2, beat 1)', d.player.startSlot === 16, d.player.startSlot);
check('the line is drawn there in the first row', shown().length === 1, shown().length);
check('the status bar says so', /half a bar before "two"/.test(document.getElementById('stPos').textContent) && /bar 2, beat 1/.test(document.getElementById('stPos').textContent), document.getElementById('stPos').textContent);
// 2. a word inside the first half bar parks at the very start
var c1 = chip('one'); r = c1.getBoundingClientRect(); press(c1, r.left + 6, r.top + 6);
check('"one" at beat 2: the red line parks at slot 0, never before the sheet', d.player.startSlot === 0 && d.cur().sel.si === 0, d.player.startSlot);
// 3. the arrows between words park too; a word on the next line counts the bars before it
key('ArrowRight');
check('the right arrow selects "two" and parks at 16 again', d.cur().sel.si === 1 && d.player.startSlot === 16, d.player.startSlot);
key('ArrowRight');
check('and "three" (bar 3 beat 1 = slot 32) parks at 24 (bar 2, beat 3)', d.cur().sel.li === 1 && d.player.startSlot === 24, d.player.startSlot);
// 4. Play from a selection with no click starts half a bar before the word
d.player.startSlot = -1; d.player.start();
check('Play with "three" selected starts at slot 24', d.player.on && d.player.slot0 === 24, 'slot0 ' + d.player.slot0);
d.player.stop();
// 5. a click on a bar afterwards sets its own spot
var bh = document.querySelectorAll('.barhit')[0], br = bh.getBoundingClientRect();
bh.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: br.left + br.width * 0.5, clientY: br.top + 10 }));
check('a click at the middle of bar 1 wins: slot 8', d.player.startSlot === 8, d.player.startSlot);
// 6. in Edit a click on a note on the staff parks as well; in Add the cursor is left alone
d.state.tool = 'edit'; d.syncTools(); d.player.startSlot = -1;
var nh = Array.prototype.filter.call(document.querySelectorAll('.notehit:not(.gap)'), function (n) { return true; })[1]; r = nh.getBoundingClientRect(); press(nh, r.left + 5, r.top + 5);
check('a click on the second note head selects "two" and parks at 16', d.cur().sel && d.cur().sel.si === 1 && d.player.startSlot === 16, JSON.stringify(d.cur().sel) + ' ' + d.player.startSlot);
d.state.tool = 'add'; d.syncTools(); d.player.startSlot = 5; d.cur().sel = { li: 0, si: 0 };
d.parkBeforeSelected();
check('in the Add tool nothing parks: the typing cursor stays at 5', d.player.startSlot === 5, d.player.startSlot);
d.state.tool = 'move'; d.syncTools(); d.cur().sel = null; d.player.startSlot = -1; d.renderAll();
say('LOG done');
