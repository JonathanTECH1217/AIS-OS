// A note at the start of its line moves left into the empty bar at the end of the line before (that line hands the bar
// over), by Ctrl+arrow, Alt+arrow and as a group; a note held on in front of it is shortened to make room.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
function key(k, o) { o = o || {}; document.getElementById('work').dispatchEvent(new KeyboardEvent('keydown', { key: k, ctrlKey: !!o.ctrl, altKey: !!o.alt, shiftKey: !!o.shift, bubbles: true, cancelable: true })); }
function sheetSlot(li, y) { return d.barOrdinal(d.S(), li, 0) * 16 + y.pos; }
function find(t) { var r = null; d.S().lines.forEach(function (l, li) { if (l.kind === 'line') l.syllables.forEach(function (y) { if (y.text === t) r = { li: li, y: y }; }); }); return r; }
function at(t) { var f = find(t); return f ? sheetSlot(f.li, f.y) : null; }
d.state.prefs.side = false; d.state.prefs.pad = false; d.state.prefs.snap = 'beat'; d.cur().audio = null;
function reset() {
  s = d.S(); s.time = '4/4';
  // line 1: "it's" "more" in bar 1, then an empty bar 2 (its bars: 2); line 2: "than" "that" from its bar 1 (sheet bar 3)
  s.lines = [{ kind: 'line', bars: 2, syllables: [mk(0, 'q', "it's"), mk(4, 'q', 'more')] }, { kind: 'line', bars: 2, syllables: [mk(0, 'q', 'than'), mk(4, 'q', 'that'), mk(8, 'q', 'way')] }];
  d.cur().sel = null; d.state.marks = []; d.state.tool = 'move'; d.syncTools(); d.renderAll();
}
reset();
check('setup: "than" at sheet slot 32 (bar 3), bar 2 empty and part of line 1', at('than') === 32 && d.S().lines[0].bars === 2);
// 1. Ctrl+← on "than": into the empty bar 2
d.cur().sel = { li: 1, si: 0 }; d.renderAll(); document.getElementById('work').focus();
key('ArrowLeft', { ctrl: true });
check('Ctrl+← moves "than" a sixteenth left into bar 2 (sheet slot 31), no "Already at the start"', at('than') === 31, 'than at ' + at('than'));
check('line 1 handed its empty bar over (1 bar), line 2 grew to 3', d.S().lines[0].bars === 1 && d.lineBars(d.S().lines[1], 16) === 3, d.S().lines[0].bars + ' / ' + d.lineBars(d.S().lines[1], 16));
check('"that" and "way" did not move in the song', at('that') === 36 && at('way') === 40, at('that') + ' ' + at('way'));
for (var n = 0; n < 15; n++) key('ArrowLeft', { ctrl: true });
check('fifteen more: "than" at the start of bar 2 (sheet slot 16)', at('than') === 16, at('than'));
key('ArrowLeft', { ctrl: true });
check('one more: line 1 has no empty bar left, so "than" stays (no notes of line 1 are touched)', at('than') === 16 && at('more') === 4, at('than') + ' more ' + at('more'));
while (d.cur().undo.length) d.undo();
check('undo steps back to the start', at('than') === 32 && d.S().lines[0].bars === 2, at('than') + ' bars ' + d.S().lines[0].bars);
// 2. Alt+← (shove: "than" and everything after it)
reset(); d.cur().sel = { li: 1, si: 0 }; d.renderAll(); document.getElementById('work').focus();
key('ArrowLeft', { alt: true });
check('Alt+← shoves "than" and the rest a beat left into bar 2', at('than') === 28 && at('that') === 32 && at('way') === 36, [at('than'), at('that'), at('way')].join(' '));
// 3. the group: "than that way" highlighted, Ctrl+← twice
reset(); d.setMarks([{ li: 1, si: 0 }, { li: 1, si: 1 }, { li: 1, si: 2 }]); document.getElementById('work').focus();
key('ArrowLeft', { ctrl: true }); key('ArrowLeft', { ctrl: true });
check('the group slides two beats left into bar 2', at('than') === 24 && at('that') === 28 && at('way') === 32, [at('than'), at('that'), at('way')].join(' '));
// 4. a note held on in front (a whole note "held" filling bar 1 of the same line): Ctrl+← shortens it
s = d.S(); s.lines = [{ kind: 'line', bars: 2, syllables: [mk(0, 'w', 'held'), mk(16, 'q', 'than')] }]; d.cur().sel = { li: 0, si: 1 }; d.state.marks = []; d.renderAll(); document.getElementById('work').focus();
key('ArrowLeft', { ctrl: true });
key('ArrowLeft', { ctrl: true }); key('ArrowLeft', { ctrl: true });
check('a note held on in front gives way: three sixteenths in, "held" 13 long and "than" at slot 13', d.lenSlots(find('held').y) === 13 && at('than') === 13, d.lenSlots(find('held').y) + ' / ' + at('than'));
check('the toast says so', /"held" shortened/.test(document.getElementById('toast').textContent), document.getElementById('toast').textContent);
d.state.prefs.snap = '2';
say('LOG done');
