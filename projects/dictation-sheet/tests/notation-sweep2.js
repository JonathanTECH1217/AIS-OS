// Second pass: classify the sweep mismatches (are any NOT the missing dots?), tie widths by first-piece value and
// by within-bar vs across-barline, dotted rests in 6/8, and the tie gap arithmetic for the "my" case.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function mk(syls) { return d.normalize({ lines: [{ kind: 'line', bars: 1, syllables: syls }] }).lines; }
function y(text, pos, slots, hy) { var o = { text: text, pos: pos, hy: !!hy }; var lv = d.lenFromSlots(slots); o.len = lv.len; o.dot = lv.dot; o.xs = slots - d.pieceSlots({ dur: lv.len, dots: lv.dot ? 1 : 0 }); return o; }
function r1(v) { return Math.round(v * 10) / 10; }
function bbox(p) { try { return p.getBBox(); } catch (e) { return { x: 0, y: 0, width: 0, height: 0 }; } }
function tiePaths(svg) { return Array.prototype.filter.call(svg.children, function (n) { if (n.tagName !== 'path') return false; var dd = n.getAttribute('d') || ''; return (dd.match(/Q/g) || []).length === 2 && !/[LC]/.test(dd); }); }
function grayHeads(svg) { return Array.prototype.filter.call(svg.querySelectorAll('g.vf-notehead path'), function (p) { return (p.getAttribute('fill') || '') === '#86868B'; }); }
function inkHeads(svg) { return Array.prototype.filter.call(svg.querySelectorAll('g.vf-notehead path'), function (p) { return (p.getAttribute('fill') || '') !== '#86868B'; }); }
function dots(svg) { return Array.prototype.filter.call(svg.querySelectorAll('g.vf-modifiers path'), function (p) { return /A/.test(p.getAttribute('d') || ''); }); }
function tokens(line, spb, time) { var out = []; for (var b = 0; b < d.lineBars(line, spb); b++) d.barTokens(line, b, spb, time).forEach(function (t) { t.bar = b; out.push(t); }); return out; }
try {
  var s = d.S(); s.time = '4/4'; s.view = 'vocals'; d.cur().sel = null; var spb = 16;
  var kinds = { heads: 0, ties: 0, rests: 0, dots: 0 }, headBad = [], tieBad = [], byFirst = {}, cross = [], within = [];
  for (var pos = 0; pos < 16; pos++) for (var len = 1; len <= 24; len++) {
    s.lines = mk([y('la', pos, len)]); d.renderWork();
    var line = s.lines[0], tks = tokens(line, spb, s.time), pieces = tks.filter(function (t) { return !t.rest; });
    var svgs = document.querySelectorAll('#sys svg'), heads = 0, ties = [], dts = 0, rests = 0;
    Array.prototype.forEach.call(svgs, function (svg) { heads += grayHeads(svg).length; rests += inkHeads(svg).length; dts += dots(svg).length; tiePaths(svg).forEach(function (p) { var b = bbox(p); ties.push({ w: r1(b.width), x: r1(b.x) }); }); });
    if (heads !== pieces.length) { kinds.heads++; headBad.push('pos' + pos + ' len' + len + ' heads ' + heads + ' vs ' + pieces.length); }
    if (ties.length !== pieces.length - 1) { kinds.ties++; tieBad.push('pos' + pos + ' len' + len + ' ties ' + ties.length + ' vs ' + (pieces.length - 1)); }
    if (rests !== tks.filter(function (t) { return t.rest; }).length) kinds.rests++;
    if (dts !== tks.filter(function (t) { return t.dots; }).length) kinds.dots++;
    // tie i joins piece i and i+1 (ties are drawn in piece order within a bar, then carries); classify by the first piece's value and whether the pair crosses a barline
    ties.sort(function (a, b) { return a.x - b.x; });
    ties.forEach(function (t, i) { var p = pieces[i], q = pieces[i + 1]; if (!p || !q) return; var k = p.dur + (p.dots ? '.' : '') + (q.bar !== p.bar ? '|' : '>') + q.dur; if (!byFirst[k]) byFirst[k] = { n: 0, min: 1e9, max: 0 }; byFirst[k].n++; byFirst[k].min = Math.min(byFirst[k].min, t.w); byFirst[k].max = Math.max(byFirst[k].max, t.w); (q.bar !== p.bar ? cross : within).push(t.w); });
  }
  say('MISMATCH KINDS over 384 renders: ' + JSON.stringify(kinds) + ' head problems: ' + (headBad.join('; ') || 'none') + ' tie-count problems: ' + (tieBad.join('; ') || 'none'));
  say('TIE WIDTH by pair (first piece > next, | = over the barline): ' + Object.keys(byFirst).sort().map(function (k) { return k + ' n' + byFirst[k].n + ' ' + byFirst[k].min + '..' + byFirst[k].max; }).join(' | '));
  say('TIES within a bar: ' + within.length + ' min ' + Math.min.apply(null, within) + '; over the barline: ' + cross.length + ' min ' + Math.min.apply(null, cross));
  // the "my" case: what x values does VexFlow 3.0.9 use for the tie ends?
  s.lines = mk([y('my', 11, 3)]); d.renderWork();
  var sv = document.querySelector('#sys svg'), gh = grayHeads(sv), tp = tiePaths(sv);
  say('MY CASE pos11 len3: heads at ' + gh.map(function (p) { var b = bbox(p); return r1(b.x) + '..' + r1(b.x + b.width); }).join(' and ') + '; tie path d="' + (tp[0] ? tp[0].getAttribute('d') : 'none') + '" slot width ' + r1((d.editor.systems[0].geo.cells[0].x1 - d.editor.systems[0].geo.cells[0].x0) / 16));
  // dotted rests in 6/8: a note on the second dotted-quarter group leaves a dotted-quarter rest
  s.time = '6/8'; s.lines = mk([y('la', 6, 6)]); d.renderWork();
  var sv2 = document.querySelector('#sys svg');
  say('6/8 REST: tokens ' + d.barTokens(s.lines[0], 0, 12, '6/8').map(function (t) { return (t.rest ? 'r' : '') + t.dur + (t.dots ? '.' : '') + 'x' + t.slots; }).join(' ') + '; ink heads ' + inkHeads(sv2).length + ' dots drawn ' + dots(sv2).length + ' (the rest should carry a dot)');
  s.time = '4/4';
  // beaming sanity for the user's line: which notes got flags (unbeamed) in candidate B
  s.lines = mk([y('You', 2, 3), y('could', 5, 3), y('be', 8, 3), y('my', 11, 3), y('some', 14, 4, true), y('one,', 18, 3)]); d.renderWork();
  var sv3 = document.querySelector('#sys svg');
  say('CANDIDATE B (one,=3 slots): gray heads ' + grayHeads(sv3).length + ' flags ' + sv3.querySelectorAll('g.vf-flag').length + ' ties ' + tiePaths(sv3).map(function (p) { return 'w' + r1(bbox(p).width); }).join(',') + ' dots ' + dots(sv3).length + ' rests ' + inkHeads(sv3).length);
  window.__sampleLines && (s.lines = window.__sampleLines);
} catch (e) { say('SWEEP2 FAILED ' + (e && e.stack || e)); }
