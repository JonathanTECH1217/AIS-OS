// A highlighted group spanning a line break slides left as one (the screenshot of 2026-09-27): the end of one line
// ("... any- thing", a rest after it) and the start of the next ("Oth- er than what", at the line's first slot).
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text, hy) { var y = d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; if (hy) y.hy = true; return y; }
function key(k, o) { o = o || {}; document.getElementById('work').dispatchEvent(new KeyboardEvent('keydown', { key: k, ctrlKey: !!o.ctrl, shiftKey: !!o.shift, bubbles: true, cancelable: true })); }
function find(t) { var r = null; d.S().lines.forEach(function (l, li) { if (l.kind === 'line') l.syllables.forEach(function (y) { if (y.text === t) r = { li: li, y: y }; }); }); return r; }
function at(t) { var f = find(t); return f ? d.barOrdinal(d.S(), f.li, 0) * 16 + f.y.pos : null; }
function lineOf(t) { return find(t).li; }
d.state.prefs.side = false; d.state.prefs.pad = false; d.cur().audio = null; d.state.prefs.snap = 'beat';
s = d.S(); s.time = '4/4';
// line 0: "I don't want to be any- thing" from bar 2 beat 1 (after an empty bar), a quarter rest at the end of bar 3;
// line 1 (from sheet bar 4): "Oth- er than what" at its first slots
s.lines = [
  { kind: 'line', bars: 3, syllables: [mk(16, 'q', 'I'), mk(20, 'q', "don't"), mk(24, 'q', 'want'), mk(28, 'q', 'to'), mk(32, 'q', 'be'), mk(36, 'q', 'any', true), mk(40, 'q', 'thing')] },
  { kind: 'line', bars: 2, syllables: [mk(0, 'q', 'Oth', true), mk(4, 'q', 'er'), mk(8, 'q', 'than'), mk(12, 'q', 'what')] }
];
d.cur().sel = null; d.cur().undo = []; d.state.tool = 'move'; d.syncTools(); d.renderAll();
check('setup: "thing" ends at 44, a rest to 48, "Oth-" at the start of line 2 (48)', at('thing') === 40 && at('Oth') === 48 && lineOf('Oth') === 1);
var marks = []; [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6], [1, 0], [1, 1], [1, 2], [1, 3]].forEach(function (m) { marks.push({ li: m[0], si: m[1] }); });
d.setMarks(marks); document.getElementById('work').focus();
key('ArrowLeft', { ctrl: true });
check('Ctrl+← slides the whole group a beat left, no "already touches" error', at('I') === 12 && at('thing') === 36 && at('Oth') === 44 && at('what') === 56, [at('I'), at('thing'), at('Oth'), at('what')].join(' '));
check('"Oth-" crossed into the line before, into the space the group left there', lineOf('Oth') === 0 && lineOf('er') === 1, lineOf('Oth') + ' / ' + lineOf('er'));
check('the group is still highlighted, all eleven notes', d.state.marks.length === 11 && document.querySelectorAll('.syl-chip.mark').length === 11, d.state.marks.length);
key('ArrowLeft', { ctrl: true }); key('ArrowLeft', { ctrl: true }); key('ArrowLeft', { ctrl: true });
check('three more beats: "I" reaches the start of the sheet (slot 0), the rest follow', at('I') === 0 && at('thing') === 24 && at('what') === 44, [at('I'), at('thing'), at('what')].join(' '));
key('ArrowLeft', { ctrl: true });
check('at the sheet\'s start it stops with the message, nothing moves', at('I') === 0 && /already touches/.test(document.getElementById('toast').textContent));
var steps = d.cur().undo.length; while (d.cur().undo.length) d.undo();
check('undo puts every note back in its own line (' + steps + ' steps)', at('I') === 16 && at('Oth') === 48 && lineOf('Oth') === 1, [at('I'), at('Oth'), lineOf('Oth')].join(' '));
// dragging a highlighted word does the same
d.setMarks(marks); var chip = Array.prototype.filter.call(document.querySelectorAll('.syl-chip'), function (c) { return c.textContent === 'er'; })[0], cell = d.editor.systems[0].geo.cells[0], sw = (cell.x1 - cell.x0) / 16, r = chip.getBoundingClientRect();
chip.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: r.left + 6, clientY: r.top + 6, button: 0, pointerId: 3 }));
chip.dispatchEvent(new PointerEvent('pointermove', { bubbles: true, clientX: r.left + 6 - 8 * sw, clientY: r.top + 6, pointerId: 3 }));
chip.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: r.left + 6 - 8 * sw, clientY: r.top + 6, pointerId: 3 }));
check('dragging a highlighted word two beats left moves the whole group two beats', at('I') === 8 && at('Oth') === 40 && at('what') === 52, [at('I'), at('Oth'), at('what')].join(' '));
d.state.marks = []; d.state.prefs.snap = '2'; d.renderAll();
say('LOG done');
