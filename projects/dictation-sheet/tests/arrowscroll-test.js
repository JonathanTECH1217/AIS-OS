// With nothing selected the up and down arrows scroll the sheet a row (Shift: a screenful); with a word selected they
// move between lines as before.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: 'q' }] }] }).lines[0].syllables[0]; }
function key(k, o) { o = o || {}; document.getElementById('work').dispatchEvent(new KeyboardEvent('keydown', { key: k, shiftKey: !!o.shift, bubbles: true, cancelable: true })); }
d.state.prefs.side = false; d.state.prefs.pad = false; d.cur().audio = null;
s = d.S(); s.time = '4/4'; var lines = []; for (var i = 0; i < 16; i++) lines.push({ kind: 'line', bars: 4, syllables: [mk(0, 'w' + i), mk(4, 'x' + i)] });
s.lines = lines; d.cur().sel = null; d.state.marks = []; d.state.tool = 'move'; d.syncTools(); d.renderAll();
var w = document.getElementById('work'), row = document.getElementById('system-0').getBoundingClientRect().height + 8; w.scrollTop = 0; w.focus();
key('ArrowDown');
check('↓ with nothing selected scrolls down a row', Math.abs(w.scrollTop - row) < 2, w.scrollTop + ' vs ' + row);
key('ArrowDown'); key('ArrowUp');
check('↓ then ↑: one row down in all', Math.abs(w.scrollTop - row) < 2, w.scrollTop);
var t0 = w.scrollTop; key('ArrowDown', { shift: true });
check('Shift+↓ scrolls about a screenful', w.scrollTop - t0 > w.clientHeight * 0.5, (w.scrollTop - t0) + ' of ' + w.clientHeight);
check('nothing got selected', !d.cur().sel);
d.cur().sel = { li: 3, si: 0 }; d.renderAll(); w.focus(); var s0 = w.scrollTop;
key('ArrowDown');
check('with a word selected ↓ moves to the line below instead', d.cur().sel && d.cur().sel.li === 4, JSON.stringify(d.cur().sel));
d.cur().sel = null; d.renderAll();
say('LOG done');
