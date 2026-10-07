// Screenshot: the worst cases in one line. Bar 1: 16th+8th tied pairs starting on the "a" of beats 1, 2, 3 (ties 0.4 px
// wide) and a dotted 8th on beat 4 (no dot drawn). Bar 2: dotted quarter on beat 1 (no dot), 16th on the "a" of beat 2
// held 5 slots (16th + quarter tied), and an 8th on the "a" of beat 4 spilling over the barline (tie over the barline).
var d = window.__ds, s = d.S();
function y(text, pos, slots, hy) { var o = { text: text, pos: pos, hy: !!hy }; var lv = d.lenFromSlots(slots); o.len = lv.len; o.dot = lv.dot; o.xs = slots - d.pieceSlots({ dur: lv.len, dots: lv.dot ? 1 : 0 }); return o; }
s.time = '4/4'; s.view = 'vocals'; s.title = 'worst cases'; d.cur().sel = null;
s.lines = d.normalize({ lines: [{ kind: 'line', bars: 1, syllables: [y('a3', 3, 3), y('a7', 7, 3), y('a11', 11, 3), y('dot', 12, 3), y('dotq', 16, 6), y('a7b', 23, 5), y('spill', 31, 4), y('end', 36, 4)] }] }).lines;
d.state.prefs.side = false; d.state.prefs.tools = false; d.renderAll();
document.body.classList.remove('drawers-open', 'both-open', 'side-open', 'tools-open'); ['.tools', '.side', '.rail'].forEach(function (q) { var e = document.querySelector(q); if (e) e.hidden = true; });
d.drawSystems(); window.scrollTo(0, 0);
