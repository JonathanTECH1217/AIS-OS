// Undo (and an edit) never slides other music into view: the row at the top of the screen stays where it was, also
// when bars or rows above it come or go.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
function key(k, o) { o = o || {}; document.getElementById('work').dispatchEvent(new KeyboardEvent('keydown', { key: k, ctrlKey: !!o.ctrl, shiftKey: !!o.shift, bubbles: true, cancelable: true })); }
d.state.prefs.side = false; d.state.prefs.pad = false; d.cur().audio = null;
s = d.S(); s.time = '4/4'; var lines = [];
for (var i = 0; i < 16; i++) lines.push({ kind: 'line', bars: 4, syllables: [mk(0, 'q', 'w' + i), mk(4, 'q', 'x' + i)] });
s.lines = lines; d.cur().undo = []; d.cur().sel = null; d.state.tool = 'move'; d.syncTools(); d.renderAll();
var w = document.getElementById('work');
// the row of line 10 at the top of the screen
function rowTop(li) { var out = null; d.editor.systems.forEach(function (sy, k) { if (out === null && !sy.header && sy.bars.some(function (b) { return b.li === li; })) out = document.getElementById('system-' + k).getBoundingClientRect().top - w.getBoundingClientRect().top; }); return out; }
var target = document.getElementById('system-0'); w.scrollTop = 0;
w.scrollTop = rowTop(10) - 20; var before = rowTop(10);
check('setup: line 10 near the top of the screen', Math.abs(before - 20) < 2, before);
// an edit far above: line 2 grows by 8 bars (its row grows), then undo
d.S().lines[2].bars = 12; d.pushUndo(); d.S().lines[2].bars = 20; d.touch(); d.renderAll();
check('an edit that adds rows above keeps line 10 where it was on screen', Math.abs(rowTop(10) - before) < 2, rowTop(10) + ' vs ' + before);
d.undo();
check('undo that takes those rows away keeps line 10 where it was', Math.abs(rowTop(10) - before) < 2, rowTop(10) + ' vs ' + before);
d.redo();
check('redo too', Math.abs(rowTop(10) - before) < 2, rowTop(10) + ' vs ' + before);
// a plain undo with nothing above changing
d.cur().sel = { li: 11, si: 0 }; d.renderAll(); w.scrollTop = w.scrollTop; before = rowTop(10);
key(']'); d.undo();
check('an edit and undo on the line below keep the view', Math.abs(rowTop(10) - before) < 2, rowTop(10) + ' vs ' + before);
// deliberate scrolls still happen: selecting a word far away brings it into view
d.cur().sel = { li: 0, si: 0 }; d.renderAll(); var chip0 = document.querySelector('.syl-chip.on');
key('ArrowRight');
setTimeout(function () {
  var on = document.querySelector('.syl-chip.on'), r = on.getBoundingClientRect(), wr = w.getBoundingClientRect();
  check('stepping to a word off screen still brings it into view', r.top >= wr.top - 2 && r.bottom <= wr.bottom + 2, Math.round(r.top) + ' in ' + Math.round(wr.top) + '-' + Math.round(wr.bottom));
  say('LOG done');
}, 100);
