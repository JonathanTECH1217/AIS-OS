// smoke: build a 2-line sheet, render, print the hook extras and the strip geometry
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
say('LOG extras: ' + ['growNote', 'cutAt', 'applyLength', 'shove', 'nudgeContact', 'addBarToSelected', 'setSel', 'clearMarks', 'dropAt', 'tapPause', 'tapSlot', 'selected', 'noteMenu', 'setSlots'].map(function (k) { return k + ':' + typeof d[k]; }).join(' '));
function mkLine(texts, bars) { return { kind: 'line', bars: bars || 1, syllables: texts.map(function (t, i) { return { text: t, pos: i * 4 }; }) }; }
var s = d.S(); s.time = '4/4'; s.bpm = 100; s.title = 'tap'; s.lyrics = '';
s.lines = d.normalize({ lines: [mkLine(['one', 'two', 'three']), mkLine(['four', 'five'])] }).lines;
d.state.prefs.zoom = 200; d.state.prefs.snap = '2'; d.state.tool = 'move';
d.renderAll();
var sysBox = document.getElementById('sys');
say('LOG sys width ' + (sysBox && sysBox.clientWidth) + ' systems ' + d.editor.systems.length + ' bw ' + d.editor.bw);
d.editor.systems.forEach(function (sy, i) {
  if (sy.header) { say('LOG system ' + i + ' header'); return; }
  say('LOG system ' + i + ' bars ' + sy.bars.map(function (b) { return 'L' + b.li + 'b' + b.b; }).join(',') + ' cells ' + (sy.geo ? sy.geo.cells.map(function (c) { return 'L' + c.li + 'b' + c.b + '[' + Math.round(c.x0) + '-' + Math.round(c.x1) + ']'; }).join(' ') : 'none') + ' width ' + (sy.geo && sy.geo.width));
  (sy.chips || []).forEach(function (c) { var r = c.el.getBoundingClientRect(); say('LOG   chip "' + c.el.textContent + '" li ' + c.li + ' pos ' + c.pos + ' end ' + c.end + ' left ' + c.el.style.left + ' width ' + c.el.style.width + ' rect ' + Math.round(r.left) + ',' + Math.round(r.top) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height) + ' grip ' + !!c.el.querySelector('.grip')); });
});
var tl = document.querySelector('.timeline'); if (tl) { var r = tl.getBoundingClientRect(); say('LOG timeline rect ' + Math.round(r.left) + ',' + Math.round(r.top) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height) + ' cells ' + tl.querySelectorAll('.cell').length + ' last ' + tl.querySelectorAll('.cell.last').length + ' cellbtns ' + tl.querySelectorAll('.cellbtn').length); }
say('LOG syls: ' + s.lines.map(function (l) { return d.sortedSyls(l).map(function (y) { return y.text + '@' + y.pos + 'x' + d.lenSlots(y); }).join(' '); }).join(' | '));
say('LOG audioOn ' + d.state.audioOn + ' player.on ' + d.player.on + ' slotSec ' + d.player.slotSec + ' nominal ' + d.audioNominalSlotSec());
