// Why is the left of the staff hidden in the screenshots? Print the rects and scroll offsets of the sheet's ancestors.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function y(text, pos, slots, hy) { var o = { text: text, pos: pos, hy: !!hy }; var lv = d.lenFromSlots(slots); o.len = lv.len; o.dot = lv.dot; o.xs = slots - d.pieceSlots({ dur: lv.len, dots: lv.dot ? 1 : 0 }); return o; }
function r1(v) { return Math.round(v * 10) / 10; }
function rect(el) { var r = el.getBoundingClientRect(); return r1(r.left) + '..' + r1(r.right) + ' w' + r1(r.width) + ' sl' + el.scrollLeft + ' cw' + el.clientWidth + ' sw' + el.scrollWidth + ' ov=' + getComputedStyle(el).overflowX + ' pos=' + getComputedStyle(el).position; }
try {
  s.time = '4/4'; s.view = 'vocals'; d.cur().sel = null;
  s.lines = d.normalize({ lines: [{ kind: 'line', bars: 1, syllables: [y('You', 2, 3), y('could', 5, 3), y('be', 8, 3), y('my', 11, 3), y('some', 14, 4, true), y('one,', 18, 3)] }] }).lines;
  d.renderAll();
  say('window ' + window.innerWidth + 'x' + window.innerHeight + ' body class "' + document.body.className + '" prefs ' + JSON.stringify(d.state.prefs));
  var svg = document.querySelector('#sys svg'), e = svg;
  while (e && e !== document.body) { say((e.id ? '#' + e.id : '') + '.' + (e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className) + ' <' + e.tagName + '> ' + rect(e)); e = e.parentNode; }
  ['.tools', '.side', '.rail', '.ribbon', '.menubar', '.tabbar'].forEach(function (sel) { var el = document.querySelector(sel); if (el) say(sel + ' ' + rect(el) + ' hidden=' + el.hidden + ' display=' + getComputedStyle(el).display); });
  say('system-0 chips left: ' + d.editor.systems[0].chips.map(function (c) { return c.el.textContent + '@' + c.el.style.left; }).join(' ') + ' first text x ' + (svg.querySelector('text') ? svg.querySelector('text').getAttribute('x') : '?'));
} catch (er) { say('LAYOUT FAILED ' + (er && er.stack || er)); }
