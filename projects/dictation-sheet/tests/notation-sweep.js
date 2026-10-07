// Sweep: one syllable at every (pos 0..15, len 1..24) in 4/4. Count drawn heads vs written pieces, ties vs piece
// pairs, tie widths, dots. Then: rests, system break, chips, sample sheet, API checks (VexFlow really 3.0.9?).
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function mk(syls) { return d.normalize({ lines: [{ kind: 'line', bars: 1, syllables: syls }] }).lines; }
function y(text, pos, slots, hy) { var o = { text: text, pos: pos, hy: !!hy }; var lv = d.lenFromSlots(slots); o.len = lv.len; o.dot = lv.dot; o.xs = slots - d.pieceSlots({ dur: lv.len, dots: lv.dot ? 1 : 0 }); return o; }
function r1(v) { return Math.round(v * 10) / 10; }
function bbox(p) { try { return p.getBBox(); } catch (e) { return { x: 0, y: 0, width: 0, height: 0 }; } }
// VexFlow 3.0.9 draws a tie as a bare path at the svg root: M, two Q curves, Z. Beams are M+L paths, glyphs have L/C.
function tiePaths(svg) { return Array.prototype.filter.call(svg.children, function (n) { if (n.tagName !== 'path') return false; var dd = n.getAttribute('d') || ''; return (dd.match(/Q/g) || []).length === 2 && !/[LC]/.test(dd); }); }
function grayHeads(svg) { return Array.prototype.filter.call(svg.querySelectorAll('g.vf-notehead path'), function (p) { return (p.getAttribute('fill') || '') === '#86868B'; }); }
function inkHeads(svg) { return Array.prototype.filter.call(svg.querySelectorAll('g.vf-notehead path'), function (p) { return (p.getAttribute('fill') || '') !== '#86868B'; }); }
function dots(svg) { return Array.prototype.filter.call(svg.querySelectorAll('g.vf-modifiers path'), function (p) { return /A/.test(p.getAttribute('d') || ''); }); }
function tokens(line, spb, time) { var out = []; for (var b = 0; b < d.lineBars(line, spb); b++) d.barTokens(line, b, spb, time).forEach(function (t) { t.bar = b; out.push(t); }); return out; }
function tokStr(tks) { return tks.map(function (t) { return (t.rest ? 'r' : '') + t.dur + (t.dots ? '.' : '') + (t.bar ? '' : ''); }).join(' '); }
try {
  var s = d.S(); window.__sampleLines = JSON.parse(JSON.stringify(s.lines)); window.__sampleTitle = s.title; s.time = '4/4'; s.view = 'vocals'; d.cur().sel = null; var spb = 16;
  say('BOOT sheet "' + s.title + '" lines ' + s.lines.length);
  say('API: Vex.Flow.BUILD=' + JSON.stringify(Vex.Flow.BUILD) + ' Dot.buildAndAttach=' + typeof (Vex.Flow.Dot && Vex.Flow.Dot.buildAndAttach) + ' StaveNote.addDotToAll=' + typeof Vex.Flow.StaveNote.prototype.addDotToAll + ' Voice.Mode=' + typeof Vex.Flow.Voice.Mode + ' Stave.formatBegModifiers=' + typeof Vex.Flow.Stave.formatBegModifiers + ' Beam.getDefaultBeamGroups=' + typeof Vex.Flow.Beam.getDefaultBeamGroups);
  // --- 1. the (pos, len) sweep ---
  var bad = [], splitMap = [], invisible = [], minTie = 1e9, nRuns = 0, tieWidths = {};
  for (var pos = 0; pos < 16; pos++) {
    var row = [];
    for (var len = 1; len <= 24; len++) {
      s.lines = mk([y('la', pos, len)]); d.renderWork(); nRuns++;
      var line = s.lines[0], tks = tokens(line, spb, s.time), pieces = tks.filter(function (t) { return !t.rest; });
      var svgs = document.querySelectorAll('#sys svg'), heads = 0, ties = [], dts = 0, rests = 0;
      Array.prototype.forEach.call(svgs, function (svg) { heads += grayHeads(svg).length; rests += inkHeads(svg).length; dts += dots(svg).length; tiePaths(svg).forEach(function (p) { ties.push(r1(bbox(p).width)); }); });
      var wantDots = pieces.filter(function (t) { return t.dots; }).length + tks.filter(function (t) { return t.rest && t.dots; }).length;
      var probs = [];
      if (heads !== pieces.length) probs.push('heads ' + heads + ' != pieces ' + pieces.length);
      if (ties.length !== pieces.length - 1) probs.push('ties ' + ties.length + ' != ' + (pieces.length - 1));
      if (rests !== tks.filter(function (t) { return t.rest; }).length) probs.push('rests drawn ' + rests + ' != tokens ' + tks.filter(function (t) { return t.rest; }).length);
      if (dts !== wantDots) probs.push('dots drawn ' + dts + ' != wanted ' + wantDots);
      ties.forEach(function (w) { if (w < minTie) minTie = w; var k = w < 4 ? '<4' : w < 8 ? '4-8' : '>=8'; tieWidths[k] = (tieWidths[k] || 0) + 1; if (w < 4) invisible.push('pos' + pos + ' len' + len + ' [' + tokStr(pieces) + '] tie w' + w); });
      if (probs.length) bad.push('pos' + pos + ' len' + len + ' [' + tokStr(pieces) + ']: ' + probs.join('; '));
      row.push(pieces.length);
    }
    splitMap.push('pos' + (pos < 10 ? ' ' : '') + pos + ': ' + row.join(''));
  }
  say('SWEEP ' + nRuns + ' renders. pieces per (pos,len), len 1..24 left to right:'); splitMap.forEach(say);
  say('SWEEP mismatches (' + bad.length + '):'); bad.slice(0, 60).forEach(function (b) { say('  ' + b); }); if (bad.length > 60) say('  ... ' + (bad.length - 60) + ' more');
  say('SWEEP tie widths: ' + JSON.stringify(tieWidths) + ' min ' + minTie + '; ties under 4px (' + invisible.length + '): ' + invisible.slice(0, 40).join(' | '));
  // --- 2. dotted values on the beat, 3 slots on e / a ---
  say('PIECES beat1 x6: ' + JSON.stringify(d.notePiecesAt(0, 6, 16, '4/4')) + ' beat2 x6: ' + JSON.stringify(d.notePiecesAt(4, 6, 16, '4/4')) + ' beat1 x3: ' + JSON.stringify(d.notePiecesAt(0, 3, 16, '4/4')) + ' e x3: ' + JSON.stringify(d.notePiecesAt(1, 3, 16, '4/4')) + ' a x3: ' + JSON.stringify(d.notePiecesAt(3, 3, 16, '4/4')) + ' & x3: ' + JSON.stringify(d.notePiecesAt(2, 3, 16, '4/4')) + ' &of2 x4: ' + JSON.stringify(d.notePiecesAt(6, 4, 16, '4/4')) + ' beat1 x12: ' + JSON.stringify(d.notePiecesAt(0, 12, 16, '4/4')) + ' beat2 x12: ' + JSON.stringify(d.notePiecesAt(4, 12, 16, '4/4')));
  say('RESTS gap beat2 x3: ' + JSON.stringify(d.restPieces(4, 3, 16, '4/4')) + ' gap 6 x4: ' + JSON.stringify(d.restPieces(6, 4, 16, '4/4')) + ' gap 4 x12: ' + JSON.stringify(d.restPieces(4, 12, 16, '4/4')) + ' gap 1 x15: ' + JSON.stringify(d.restPieces(1, 15, 16, '4/4')) + ' 3/4 gap 0 x12: ' + JSON.stringify(d.restPieces(0, 12, 12, '3/4')));
  // empty bars: whole rests?
  s.lines = mk([y('la', 0, 4)]); s.lines[0].bars = 3; d.renderWork();
  var svg0 = document.querySelector('#sys svg'); say('EMPTY BARS: line with 3 bars, one quarter: tokens bar1=' + tokStr(d.barTokens(s.lines[0], 1, 16, '4/4')) + ' bar2=' + tokStr(d.barTokens(s.lines[0], 2, 16, '4/4')) + '; ink heads drawn ' + inkHeads(svg0).length + ' (want 2 whole rests + 8th? no: q rest + h rest in bar 0 = 2, plus 2 whole = 4)');
  s.time = '3/4'; s.lines = mk([y('la', 0, 4)]); s.lines[0].bars = 2; d.renderWork(); say('EMPTY BAR 3/4: bar1 tokens=' + tokStr(d.barTokens(s.lines[0], 1, 12, '3/4'))); s.time = '4/4';
  // --- 3. system break: one bar per system ---
  var zoom0 = d.state.prefs.zoom; d.state.prefs.zoom = 100000;
  s.lines = mk([y('hold', 14, 4), y('next', 18, 2)]); d.renderWork();
  var svgs2 = document.querySelectorAll('#sys svg');
  say('SYSTEM BREAK: systems ' + svgs2.length + ' bars/system ' + d.editor.systems.map(function (sy) { return sy.bars ? sy.bars.length : 'h'; }).join(','));
  Array.prototype.forEach.call(svgs2, function (svg, i) { var tp = tiePaths(svg); say('  sys ' + i + ': gray heads ' + grayHeads(svg).length + ' ties ' + tp.length + ' ' + tp.map(function (p) { var b = bbox(p); return r1(b.x) + '..' + r1(b.x + b.width) + ' w' + r1(b.width); }).join(' | ') + ' texts ' + Array.prototype.map.call(svg.querySelectorAll('text'), function (t) { return '"' + t.textContent + '"@' + r1(+t.getAttribute('x')); }).join(' ')); });
  d.editor.systems.forEach(function (sy, i) { if (sy.chips) say('  sys ' + i + ' chips: ' + sy.chips.map(function (c) { return '"' + c.el.textContent + '" left ' + c.el.style.left + ' w ' + c.el.style.width + ' pos ' + c.pos + ' end ' + c.end; }).join(' | ') + ' cells ' + sy.geo.cells.map(function (c) { return r1(c.x0) + '..' + r1(c.x1); }).join(' ') + ' width ' + r1(sy.geo.width)); });
  // a word group (hy) spanning the system break
  s.lines = mk([y('some', 14, 4, true), y('one', 18, 2)]); d.renderWork();
  d.editor.systems.forEach(function (sy, i) { if (sy.chips) say('  hy-group sys ' + i + ' chips: ' + sy.chips.map(function (c) { return '"' + c.el.textContent + '" left ' + c.el.style.left + ' w ' + c.el.style.width + ' pos ' + c.pos + ' end ' + c.end; }).join(' | ')); });
  Array.prototype.forEach.call(document.querySelectorAll('#sys svg'), function (svg, i) { say('  hy-group sys ' + i + ' texts ' + Array.prototype.map.call(svg.querySelectorAll('text'), function (t) { return '"' + t.textContent + '"@' + r1(+t.getAttribute('x')); }).join(' ')); });
  d.state.prefs.zoom = zoom0;
  // --- 4. chips: one per group, width = group length, clipped at the system end (8 bars per system: force a 2-system line) ---
  s.lines = mk([y('a', 0, 4), y('b', 4, 2, true), y('c', 6, 2), y('long', 12, 24)]); s.lines[0].bars = 9; d.renderWork();
  d.editor.systems.forEach(function (sy, i) { if (sy.chips) say('CHIPS sys ' + i + ' (' + sy.bars.length + ' bars): ' + sy.chips.map(function (c) { return '"' + c.el.textContent + '" left ' + c.el.style.left + ' w ' + c.el.style.width + ' pos ' + c.pos + ' end ' + c.end; }).join(' | ') + ' sw ' + r1((sy.geo.cells[0].x1 - sy.geo.cells[0].x0) / 16) + ' sysX1 ' + r1(sy.geo.cells[sy.geo.cells.length - 1].x1)); });
  // --- 5. lyric text vs head: is the word centred on the head or on its left edge? ---
  s.lines = mk([y('Twinkle', 0, 4), y('star', 4, 4)]); d.renderWork();
  var sv = document.querySelector('#sys svg'), gh = grayHeads(sv), tx = Array.prototype.filter.call(sv.querySelectorAll('text'), function (t) { return /Twinkle|star/.test(t.textContent); });
  tx.forEach(function (t, i) { var b = bbox(gh[i]), tb = bbox(t); say('LYRIC "' + t.textContent + '": text centre ' + r1(tb.x + tb.width / 2) + ' head left ' + r1(b.x) + ' head centre ' + r1(b.x + b.width / 2)); });
} catch (e) { say('SWEEP FAILED ' + (e && e.stack || e)); }
try {
  // sample: re-open the sample through the real path (a fresh sample sheet from the app's own function is not exported; use the boot sheet saved earlier)
  var s2 = d.S();
  if (window.__sampleLines) { s2.lines = window.__sampleLines; s2.view = 'vocals'; d.renderWork(); }
  var syl = 0; s2.lines.forEach(function (l) { if (l.kind === 'line') syl += l.syllables.length; });
  var heads2 = 0, ties2 = 0; Array.prototype.forEach.call(document.querySelectorAll('#sys svg'), function (svg) { heads2 += svg.querySelectorAll('g.vf-notehead path').length; ties2 += tiePaths(svg).length; });
  say('SAMPLE: syllables ' + syl + ' heads drawn ' + heads2 + ' ties ' + ties2 + ' (sample notes are pitched, so all heads are ink; rests would add to the count)');
} catch (e) { say('SAMPLE FAILED ' + (e && e.stack || e)); }
