// Follow-ups: word integrity after a group drag, the tied extra under + / - / ' / Dotted, ties in the drawing, nudge toast.
var d = window.__ds, $ = function (id) { return document.getElementById(id); };
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mkLine(syls, bars) { return { kind: 'line', bars: bars || 1, syllables: syls.map(function (t, i) { return typeof t === 'string' ? { text: t, pos: i * 4 } : t; }) }; }
function build(lines) { var s = d.S(); s.time = '4/4'; s.bpm = 100; s.title = 'x'; s.audio = null; s.lines = d.normalize({ lines: lines }).lines; d.state.audioOn = false; d.player.on = false; d.state.prefs.snap = '2'; d.state.tool = 'move'; d.setSel(null); d.renderAll(); return s; }
function syls(l) { return d.sortedSyls(l).map(function (y) { return y.text + '@' + y.pos + 'x' + d.lenSlots(y); }).join(' '); }
function chipOf(li, pos) { var f = null; d.editor.systems.forEach(function (sy) { (sy.chips || []).forEach(function (c) { if (c.li === li && c.pos === pos) f = c; }); }); return f; }
function cellOf(li, b) { var f = null; d.editor.systems.forEach(function (sy) { if (sy.geo) sy.geo.cells.forEach(function (c) { if (c.li === li && c.b === b) f = c; }); }); return f; }
function pe(type, x, y, extra) { var o = { bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 1, pointerId: 7, pointerType: 'mouse', isPrimary: true }; if (extra) Object.keys(extra).forEach(function (k) { o[k] = extra[k]; }); return new PointerEvent(type, o); }
function stub(el) { el.setPointerCapture = function () {}; el.hasPointerCapture = function () { return true; }; }
function drag(el, dx) { var r = el.getBoundingClientRect(), x0 = r.left + 6, y0 = r.top + r.height / 2; el.dispatchEvent(pe('pointerdown', x0, y0)); el.dispatchEvent(pe('pointermove', x0 + dx / 2, y0)); el.dispatchEvent(pe('pointermove', x0 + dx, y0)); el.dispatchEvent(pe('pointerup', x0 + dx, y0)); }
function dragTo(chip, li, b, slot) { var cell = cellOf(li, b), sw = (cell.x1 - cell.x0) / 16, dx = (cell.x0 + slot * sw) - parseFloat(chip.el.style.left); stub(chip.el); drag(chip.el, dx); }
function key(k, o) { var init = { key: k, bubbles: true, cancelable: true }; if (o) Object.keys(o).forEach(function (q) { init[q] = o[q]; }); document.body.dispatchEvent(new KeyboardEvent('keydown', init)); }
function toast() { return $('toast').textContent; }
function menu(li, pos, label) { var c = chipOf(li, pos); if (!c) return 'no chip'; c.el.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: 300, clientY: 300 })); var m = $('ctxmenu'); if (!m) return 'no menu'; var b = Array.prototype.filter.call(m.querySelectorAll('button'), function (x) { return x.textContent.indexOf(label) > -1; })[0]; if (!b) { m.remove(); return 'no item ' + label; } var dis = b.disabled; if (!dis) b.click(); else m.remove(); return dis ? 'disabled' : 'clicked'; }
function groupTexts(line, y) { return d.groupOf(line, y).members.map(function (m) { return m.text; }).join('+'); }

// the word "beautiful" dragged so its last note would land inside "star"
var s = build([mkLine([{ text: 'beau', pos: 0, hy: true }, { text: 'ti', pos: 4, hy: true }, { text: 'ful', pos: 8 }, { text: 'star', pos: 12 }])]), L0 = s.lines[0];
dragTo(chipOf(0, 0), 0, 0, 6);
check('word dragged to 6: "beautiful" stays one word of 3 notes and "star" is behind it', groupTexts(L0, L0.syllables[0]) === 'beau+ti+ful' && d.sortedSyls(L0).map(function (y) { return y.text; }).join(' ') === 'beau ti ful star', syls(L0) + ' group ' + groupTexts(L0, L0.syllables[0]) + ' chips ' + d.editor.systems[0].chips.map(function (c) { return '"' + c.el.textContent + '"'; }).join(' '));
s = build([mkLine([{ text: 'beau', pos: 0, hy: true }, { text: 'ti', pos: 4, hy: true }, { text: 'ful', pos: 8 }, { text: 'star', pos: 12 }])]); L0 = s.lines[0];
dragTo(chipOf(0, 0), 0, 0, 8);
check('word dragged to 8: one word of 3 notes, star behind, nothing stacked', groupTexts(L0, L0.syllables[0]) === 'beau+ti+ful' && d.sortedSyls(L0).map(function (y) { return y.text + '@' + y.pos; }).join(' ') === 'beau@8 ti@12 ful@16 star@20', syls(L0) + ' group ' + groupTexts(L0, L0.syllables[0]));
// the same through dropAt alone, the way finish() does it
s = build([mkLine([{ text: 'beau', pos: 0, hy: true }, { text: 'ti', pos: 4, hy: true }, { text: 'ful', pos: 8 }, { text: 'star', pos: 12 }])]); L0 = s.lines[0];
say('LOG order-dependence: two-note word "Twin-kle" (0,4) dragged onto "lit-tle" (8,12) "star" 16 gave Twin@8 kle@12 lit@16 tle@20 star@24 in test 2 (correct because each tail note lands exactly on a note start)');

// the tied extra under the written-value keys
s = build([mkLine(['one', 'two', 'three'])]); L0 = s.lines[0]; var one = L0.syllables[0], two = L0.syllables[1];
one.len = 'q'; one.dot = false; one.xs = 8; d.renderAll(); d.setSel({ li: 0, si: 0 });
check('setup: one = quarter + 2 beats tied (12), two at 4', d.lenSlots(one) === 12 && d.lenText(one) === 'quarter + 2 beats', d.lenText(one));
key('+'); check('+ (Longer) on quarter+8 (12 slots): the note is not shorter afterwards', d.lenSlots(one) >= 12, 'now ' + d.lenSlots(one) + ' = ' + d.lenText(one) + ' | ' + syls(L0));
one.len = 'q'; one.dot = false; one.xs = 8; d.renderAll(); d.setSel({ li: 0, si: 0 });
key("'"); check("' (Dotted) on quarter+8 (12 slots): longer than 12", d.lenSlots(one) > 12, 'now ' + d.lenSlots(one) + ' = ' + d.lenText(one));
one.len = 'q'; one.dot = false; one.xs = 8; d.renderAll(); d.setSel({ li: 0, si: 0 });
key('-'); check('- (Shorter) on quarter+8 (12 slots): one step shorter, not a collapse to 2', d.lenSlots(one) < 12 && d.lenSlots(one) >= 8, 'now ' + d.lenSlots(one) + ' = ' + d.lenText(one));
one.len = '16'; one.dot = false; one.xs = 4; d.renderAll(); d.setSel({ li: 0, si: 0 });
key('-'); check('- on 16th+4 tied (5 slots): gets shorter (not "No shorter length")', d.lenSlots(one) < 5, 'now ' + d.lenSlots(one) + ' toast "' + toast() + '"');
d.setSlotsRaw(one, 64); d.renderAll(); d.setSel({ li: 0, si: 0 });
check('Dotted on whole+48 (64 slots): does not throw away the 48 tied', menu(0, 0, 'Dotted') === 'clicked' && d.lenSlots(one) >= 64, 'now ' + d.lenSlots(one) + ' = ' + d.lenText(one));
d.setSlotsRaw(one, 20); d.renderAll(); d.setSel({ li: 0, si: 0 });
check('menu Shorter on whole+4 (20): one step shorter', menu(0, 0, 'Shorter') === 'clicked' && d.lenSlots(one) >= 12 && d.lenSlots(one) < 20, 'now ' + d.lenSlots(one) + ' = ' + d.lenText(one));
// can applyLength overflow MAX_SLOTS? xs stays, len grows
one.len = 'h'; one.dot = false; one.xs = 56; d.renderAll(); d.setSel({ li: 0, si: 0 });
check('setup h+56 = 64', d.lenSlots(one) === 64);
d.applyLength(L0, one, 'w', true, 56);
check('applyLength itself has no MAX_SLOTS clamp: w.+56 = 80 > 64', d.lenSlots(one) === 80, String(d.lenSlots(one)));
var norm = d.normalize(d.plain(s)); check('normalize clamps it to 64 on the next load/undo', d.lenSlots(norm.lines[0].syllables[0]) === 64, String(d.lenSlots(norm.lines[0].syllables[0])));
d.setSel({ li: 0, si: 0 }); var b80 = d.lenSlots(one); key('/'); check('/ on an 80-slot note: growNote clamps to 64, so "hold longer" shortens it by 16', d.lenSlots(one) === 64 && b80 === 80, b80 + ' -> ' + d.lenSlots(one) + ' toast "' + toast() + '"');

// ties in the drawing: a 20-slot note across the barline
s = build([mkLine(['one', 'two'])]); L0 = s.lines[0]; one = L0.syllables[0]; d.setSlots(L0, one, 20); d.renderAll();
var svg = document.querySelector('#system-0 svg');
var groups = svg ? Array.prototype.map.call(svg.querySelectorAll('g[class]'), function (g) { return g.getAttribute('class'); }) : [];
var classes = {}; groups.forEach(function (c) { classes[c] = (classes[c] || 0) + 1; });
say('LOG svg groups: ' + JSON.stringify(classes));
say('LOG svg paths ' + (svg ? svg.querySelectorAll('path').length : 0) + ' notes ' + (svg ? svg.querySelectorAll('.vf-stavenote, .vf-note').length : 0));
check('a tie (curve) is drawn for the note held over the barline', svg && (svg.querySelectorAll('.vf-stavetie, .vf-tie, .vf-curve').length > 0), JSON.stringify(classes));

// nudge toast when the notes before are packed
s = build([mkLine(['A', 'B', 'C'])]); L0 = s.lines[0]; d.setSel({ li: 0, si: 2 }); key('ArrowLeft', { ctrlKey: true });
check('Ctrl+Left on C with A and B packed before it: nothing moves, toast says "Already at the start" (misleading: C is at slot 8)', L0.syllables[2].pos === 8 && toast() === 'Already at the start', '"' + toast() + '"');
