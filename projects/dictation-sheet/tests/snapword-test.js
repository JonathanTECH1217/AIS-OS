// Ctrl+Shift+arrow slides the selected word (or group) until it touches the nearest word that way; across a line's
// start it goes to the end of the last word of the line before, over its empty bars.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
function key(k, o) { o = o || {}; document.getElementById('work').dispatchEvent(new KeyboardEvent('keydown', { key: k, ctrlKey: !!o.ctrl, shiftKey: !!o.shift, bubbles: true, cancelable: true })); }
function find(t) { var r = null; d.S().lines.forEach(function (l, li) { if (l.kind === 'line') l.syllables.forEach(function (y) { if (y.text === t) r = { li: li, y: y }; }); }); return r; }
function at(t) { var f = find(t); return f ? d.barOrdinal(d.S(), f.li, 0) * 16 + f.y.pos : null; }
function sel(t) { var f = find(t); d.cur().sel = { li: f.li, si: d.S().lines[f.li].syllables.indexOf(f.y) }; d.state.marks = []; d.renderAll(); document.getElementById('work').focus(); }
d.state.prefs.side = false; d.state.prefs.pad = false; d.cur().audio = null;
s = d.S(); s.time = '4/4';
// line 1: "it's" 0-4, "more" 4-8, empty bar 2; line 2 (sheet bar 3): "than" 0, "that" 8, "way" 14
s.lines = [{ kind: 'line', bars: 2, syllables: [mk(0, 'q', "it's"), mk(4, 'q', 'more')] }, { kind: 'line', bars: 2, syllables: [mk(0, 'q', 'than'), mk(8, 'q', 'that'), mk(14, 'q', 'way')] }];
d.state.tool = 'move'; d.syncTools(); d.renderAll();
sel('that'); key('ArrowLeft', { ctrl: true, shift: true });
check('Ctrl+Shift+← on "that" closes the gap to "than" (that 40 -> 36)', at('that') === 36 && /touch "than"/.test(document.getElementById('toast').textContent), at('that'));
key('ArrowLeft', { ctrl: true, shift: true });
check('pressed again it stays and says it already touches', at('that') === 36 && /Already touching/.test(document.getElementById('toast').textContent));
key('ArrowRight', { ctrl: true, shift: true });
check('Ctrl+Shift+→ closes the gap to "way" (that ends where way starts, 42)', at('that') === 42, at('that'));
sel('than'); key('ArrowLeft', { ctrl: true, shift: true });
check('"than" (first of its line) goes up into the line before to touch "more" (sheet slot 8); the rest stays', at('than') === 8 && find('than').li === 0 && at('more') === 4 && at('that') === 42 && at('way') === 46, [at('than'), find('than').li, at('more'), at('that'), at('way')].join(' '));
check('it stays selected, in its new line', d.cur().sel && d.cur().sel.li === 0 && d.S().lines[0].syllables[d.cur().sel.si].text === 'than');
d.undo();
check('one undo puts it back', at('than') === 32 && d.S().lines[0].bars === 2, at('than'));
// the group: "that" and "way" highlighted, snap left to "than"
s = d.S(); s.lines[1].syllables = [mk(0, 'q', 'than'), mk(8, 'q', 'that'), mk(12, 'q', 'way')]; d.cur().sel = null; d.renderAll();
d.setMarks([{ li: 1, si: 1 }, { li: 1, si: 2 }]); document.getElementById('work').focus();
key('ArrowLeft', { ctrl: true, shift: true });
check('a highlighted group snaps left to touch "than"', at('that') === 36 && at('way') === 40, at('that') + ' ' + at('way'));
s = d.S(); s.lines[1].syllables.push(mk(28, 'q', 'end')); d.renderAll(); d.setMarks([{ li: 1, si: 1 }, { li: 1, si: 2 }]); document.getElementById('work').focus();
key('ArrowRight', { ctrl: true, shift: true });
check('and right to touch "end"', at('way') === 56 && at('that') === 52, at('that') + ' ' + at('way'));
d.state.marks = []; d.renderAll();
say('LOG done');
