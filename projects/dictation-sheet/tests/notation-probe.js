// Probe: build a synthetic "You could be my someone" line, render it, and dump what VexFlow put in the SVG.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function mk(syls) { return d.normalize({ lines: [{ kind: 'line', bars: 1, syllables: syls }] }).lines; }
function y(text, pos, slots, hy) { var o = { text: text, pos: pos, hy: !!hy }; var lv = d.lenFromSlots(slots); o.len = lv.len; o.dot = lv.dot; o.xs = slots - d.pieceSlots({ dur: lv.len, dots: lv.dot ? 1 : 0 }); return o; }
function r2(v) { return Math.round(v * 10) / 10; }
function dumpSystem(label) {
  var svgs = document.querySelectorAll('#sys svg');
  say('== ' + label + ': systems ' + svgs.length + ' per-system bars ' + d.editor.systems.map(function (sy) { return sy.bars ? sy.bars.length : 'h'; }).join(','));
  Array.prototype.forEach.call(svgs, function (svg, si) {
    var cls = {}; Array.prototype.forEach.call(svg.querySelectorAll('g'), function (g) { var c = g.getAttribute('class') || '(none)'; cls[c] = (cls[c] || 0) + 1; });
    say('  sys ' + si + ' groups: ' + JSON.stringify(cls));
    var heads = Array.prototype.map.call(svg.querySelectorAll('g.vf-notehead'), function (g) { var p = g.querySelector('path'); var bb; try { bb = p.getBBox(); } catch (e) { bb = { x: -1, y: -1, width: 0, height: 0 }; } return { x: r2(bb.x), y: r2(bb.y), w: r2(bb.width), h: r2(bb.height), fill: p.getAttribute('fill') || g.getAttribute('fill') || '' }; });
    say('  sys ' + si + ' noteheads(' + heads.length + '): ' + heads.map(function (h) { return h.x + ',' + h.y + ' ' + h.w + 'x' + h.h + ' ' + h.fill; }).join(' | '));
    var ties = Array.prototype.map.call(svg.querySelectorAll('g.vf-stavetie'), function (g) { var p = g.querySelector('path'); var bb; try { bb = p.getBBox(); } catch (e) { bb = { x: -1, y: -1, width: 0, height: 0 }; } return r2(bb.x) + '..' + r2(bb.x + bb.width) + ' w' + r2(bb.width) + ' h' + r2(bb.height) + ' y' + r2(bb.y); });
    say('  sys ' + si + ' ties(' + ties.length + '): ' + ties.join(' | '));
    var texts = Array.prototype.map.call(svg.querySelectorAll('text'), function (t) { return '"' + t.textContent + '"@' + r2(+t.getAttribute('x')) + ',' + r2(+t.getAttribute('y')); });
    say('  sys ' + si + ' texts(' + texts.length + '): ' + texts.join(' '));
    var dots = svg.querySelectorAll('g.vf-dot, g.vf-modifiers, g.vf-beam, g.vf-stem, g.vf-flag').length;
    say('  sys ' + si + ' dot/mod/beam/stem/flag groups: ' + dots);
  });
  var s = d.S(), spb = d.slotsPerBar(s.time);
  s.lines.forEach(function (l, li) { if (l.kind !== 'line') return; for (var b = 0; b < d.lineBars(l, spb); b++) say('  tokens L' + li + ' bar ' + b + ': ' + d.barTokens(l, b, spb, s.time).map(function (t) { return (t.rest ? 'R' : (t.items.map(function (it) { return it.y.text; }).join('+') + (t.carry ? '~' : ''))) + ':' + t.dur + (t.dots ? '.' : '') + (t.tieStart ? '>' : '') + (t.tieStop ? '<' : ''); }).join(' ')); });
  d.editor.systems.forEach(function (sy, i) { if (!sy.chips) return; say('  sys ' + i + ' chips: ' + sy.chips.map(function (c) { return '"' + c.el.textContent + '" left ' + c.el.style.left + ' w ' + c.el.style.width + ' pos ' + c.pos + ' end ' + c.end; }).join(' | ') + ' cells: ' + sy.geo.cells.map(function (c) { return r2(c.x0) + '..' + r2(c.x1); }).join(' ')); });
}
try {
  var s = d.S(); s.time = '4/4'; s.view = 'vocals'; d.cur().sel = null;
  say('boot: view ' + s.view + ' zoom ' + d.state.prefs.zoom + ' sheet width ' + (document.getElementById('sys') ? document.getElementById('sys').clientWidth : '?') + ' VF ' + (window.Vex && Vex.Flow && Vex.Flow.BUILD ? JSON.stringify(Vex.Flow.BUILD) : '?'));
  // Candidate A: plain eighths with 16th rests between (slots 4, 7, 10 empty)
  s.lines = mk([y('You', 2, 2), y('could', 5, 2), y('be', 8, 2), y('my', 11, 3), y('some', 14, 4, true), y('one,', 18, 2)]);
  d.renderAll(); dumpSystem('A: 8ths at 2,5,8 with 16th rests; my@11x3; some@14x4; one@18');
  // Candidate B: dotted eighths at 2,5,8 (no gaps)
  s.lines = mk([y('You', 2, 3), y('could', 5, 3), y('be', 8, 3), y('my', 11, 3), y('some', 14, 4, true), y('one,', 18, 2)]);
  d.renderAll(); dumpSystem('B: dotted 8ths at 2,5,8; my@11x3; some@14x4; one@18');
  // Candidate C: the literal brief: You 8th @0, could 8th @2, be 3 slots from the e (5), my, some held over
  s.lines = mk([y('You', 0, 2), y('could', 2, 2), y('be', 5, 3), y('my', 8, 3), y('some', 11, 7, true), y('one,', 18, 2)]);
  d.renderAll(); dumpSystem('C: You@0x2 could@2x2 be@5x3 my@8x3 some@11x7 one@18x2');
} catch (e) { say('PROBE FAILED ' + (e && e.stack || e)); }
