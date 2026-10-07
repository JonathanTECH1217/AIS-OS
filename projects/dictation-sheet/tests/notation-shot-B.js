// Screenshot: the synthetic "You could be my someone" with the timing the user's picture implies (candidate B).
var d = window.__ds, s = d.S();
function y(text, pos, slots, hy) { var o = { text: text, pos: pos, hy: !!hy }; var lv = d.lenFromSlots(slots); o.len = lv.len; o.dot = lv.dot; o.xs = slots - d.pieceSlots({ dur: lv.len, dots: lv.dot ? 1 : 0 }); return o; }
s.time = '4/4'; s.view = 'vocals'; s.title = 'You could be my someone (synthetic)'; d.cur().sel = null;
s.lines = d.normalize({ lines: [{ kind: 'line', bars: 1, syllables: [y('You', 2, 3), y('could', 5, 3), y('be', 8, 3), y('my', 11, 3), y('some', 14, 4, true), y('one,', 18, 3)] }] }).lines;
d.state.prefs.side = false; d.state.prefs.tools = false; d.renderAll();
document.body.classList.remove('drawers-open', 'both-open', 'side-open', 'tools-open'); ['.tools', '.side', '.rail'].forEach(function (q) { var e = document.querySelector(q); if (e) e.hidden = true; });
d.drawSystems(); window.scrollTo(0, 0);
