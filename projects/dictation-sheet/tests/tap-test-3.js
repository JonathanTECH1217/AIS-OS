// Keys, the right-click menu, applyLength pushing, shove/nudge, bars, marks, and Place words after a rest toggle.
var d = window.__ds, $ = function (id) { return document.getElementById(id); };
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mkLine(syls, bars) { return { kind: 'line', bars: bars || 1, syllables: syls.map(function (t, i) { return typeof t === 'string' ? { text: t, pos: i * 4 } : t; }) }; }
function build(lines) { var s = d.S(); s.time = '4/4'; s.bpm = 100; s.title = 'keys'; s.audio = null; s.lines = d.normalize({ lines: lines }).lines; d.state.audioOn = false; d.player.on = false; d.state.prefs.snap = '2'; d.state.tool = 'move'; d.setSel(null); d.renderAll(); return s; }
function syls(l) { return d.sortedSyls(l).map(function (y) { return y.text + '@' + y.pos + 'x' + d.lenSlots(y) + (y.rest ? 'r' : ''); }).join(' '); }
function toast() { return $('toast').textContent; }
function key(k, o) { var init = { key: k, bubbles: true, cancelable: true }; if (o) Object.keys(o).forEach(function (q) { init[q] = o[q]; }); document.body.dispatchEvent(new KeyboardEvent('keydown', init)); }
function chipOf(li, pos) { var f = null; d.editor.systems.forEach(function (sy) { (sy.chips || []).forEach(function (c) { if (c.li === li && c.pos === pos) f = c; }); }); return f; }
function menu(li, pos, label) { var c = chipOf(li, pos); if (!c) return 'no chip'; c.el.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: 300, clientY: 300 })); var m = $('ctxmenu'); if (!m) return 'no menu'; var b = Array.prototype.filter.call(m.querySelectorAll('button'), function (x) { return x.textContent.indexOf(label) > -1; })[0]; if (!b) { m.remove(); return 'no item ' + label; } var dis = b.disabled; if (!dis) b.click(); else m.remove(); return dis ? 'disabled' : 'clicked'; }
function menuItems(li, pos) { var c = chipOf(li, pos); c.el.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: 300, clientY: 300 })); var m = $('ctxmenu'), out = Array.prototype.map.call(m.querySelectorAll('button'), function (x) { return x.textContent.replace(/\s+/g, ' ').trim() + (x.disabled ? ' [off]' : ''); }); m.remove(); return out; }

// ---- 5. keys and menu ----
var s = build([mkLine(['one', 'two', 'three', 'four'])]), L0 = s.lines[0], one = L0.syllables[0], two = L0.syllables[1], three = L0.syllables[2], four = L0.syllables[3];
say('LOG menu items: ' + menuItems(0, 0).join(' | '));
d.setSel({ li: 0, si: 0 }); check('setSel selects one; the drop-bar button wakes', d.selected() && d.selected().y === one && !$('dropBar').disabled);
d.setSlotsRaw(one, 64); d.setSel({ li: 0, si: 0 }); d.renderAll();
key('/'); check('/ at MAX_SLOTS: toast, length unchanged', toast() === 'Already as long as a note can be held' && d.lenSlots(one) === 64, '"' + toast() + '" len ' + d.lenSlots(one));
check('menu: Hold a beat longer is disabled at MAX_SLOTS', menu(0, 0, 'Hold a beat longer') === 'disabled');
s = build([mkLine(['one', 'two', 'three', 'four'])]); L0 = s.lines[0]; one = L0.syllables[0]; two = L0.syllables[1]; three = L0.syllables[2]; four = L0.syllables[3];
one.len = 'w'; d.renderAll(); d.setSel({ li: 0, si: 0 });
key('+'); check('+ at whole: toast, still whole', /Whole is the longest/.test(toast()) && one.len === 'w' && d.lenSlots(one) === 16, '"' + toast() + '"');
check('menu: Longer is disabled at whole', menu(0, 0, 'Longer') === 'disabled');
check('menu: Dotted on a whole = 24 slots, later notes pushed', menu(0, 0, 'Dotted') === 'clicked' && d.lenSlots(one) === 24 && one.dot && two.pos === 24 && four.pos === 32, syls(L0));
d.setSel({ li: 0, si: 0 }); key("'"); check("' key undoes the dot: 16 slots (nothing pulled back)", d.lenSlots(one) === 16 && !one.dot && two.pos === 24, syls(L0));
key('/'); check('/ key adds ONE sixteenth (17), while the menu item "Hold a beat longer (/)" adds a beat', d.lenSlots(one) === 17 && one.xs === 1, syls(L0) + ' toast "' + toast() + '"');
check('menu: Hold a beat longer adds 4 (21)', menu(0, 0, 'Hold a beat longer') === 'clicked' && d.lenSlots(one) === 21, syls(L0));
d.setSel({ li: 0, si: 0 }); key('.'); check('. key takes one sixteenth off (20)', d.lenSlots(one) === 20, syls(L0));
// Cut in half on a 3-slot note
s = build([mkLine(['one', 'two', 'three'])]); L0 = s.lines[0]; one = L0.syllables[0]; two = L0.syllables[1]; three = L0.syllables[2];
d.setSlotsRaw(two, 3); d.renderAll();
check('Cut in half on a 3-slot note (dotted eighth): a sixteenth "two" and a new 2-slot note at 5, pitch kept, word not', menu(0, 4, 'Cut in half') === 'clicked' && L0.syllables.length === 4 && d.lenSlots(two) === 1 && two.len === '16' && L0.syllables[2].pos === 5 && L0.syllables[2].len === '8' && L0.syllables[2].text === '' && d.lenSlots(L0.syllables[2]) === 2, syls(L0) + ' toast "' + toast() + '"');
check('Cut in half is disabled on a sixteenth', menu(0, 4, 'Cut in half') === 'disabled');
d.setSlotsRaw(two, 4); d.renderAll(); d.cutAt(0, 1, 7); check('cutAt clamps the cut inside the note (at 7 of 4 -> 3)', d.lenSlots(two) === 3 && d.lenSlots(L0.syllables[2]) === 1, syls(L0));
// the cut piece inherits hy: cutting a word's first syllable keeps the pieces in the word
s = build([mkLine([{ text: 'Twin', pos: 0, hy: true }, { text: 'kle', pos: 4 }])]); L0 = s.lines[0]; d.cutAt(0, 0, 2);
check('Cut on the first syllable of a word: the two halves and "kle" stay one group', d.groupOf(L0, L0.syllables[0]).members.length === 3, d.groupOf(L0, L0.syllables[0]).members.map(function (y) { return y.text + (y.hy ? '-' : '') + (y.tie ? '_' : ''); }).join(' '));
// tied extra and the written-value keys
s = build([mkLine(['one', 'two', 'three'])]); L0 = s.lines[0]; one = L0.syllables[0]; two = L0.syllables[1];
d.setSlotsRaw(one, 12); d.renderAll(); d.setSel({ li: 0, si: 0 });
check('setup: one is a half + a beat (12 slots), two at 4 (setSlotsRaw does not push)', d.lenSlots(one) === 12 && one.len === 'h' && one.xs === 4 && two.pos === 4, syls(L0));
key('+'); check('+ (Longer) on half + 1 beat (12): the note gets LONGER, not shorter', d.lenSlots(one) > 12, 'now ' + d.lenSlots(one) + ' (' + one.len + ' xs ' + one.xs + ') ' + syls(L0));
d.setSlotsRaw(one, 12); d.renderAll(); d.setSel({ li: 0, si: 0 }); key("'"); check("Dotted (') on half + 1 beat (12): the note gets longer, not shorter", d.lenSlots(one) > 12, 'now ' + d.lenSlots(one) + ' (' + one.len + (one.dot ? '.' : '') + ' xs ' + one.xs + ')');
d.setSlotsRaw(one, 5); d.renderAll(); d.setSel({ li: 0, si: 0 }); key('-'); check('- (Shorter) on quarter + 1 (5 slots): shorter than 5', d.lenSlots(one) < 5, 'now ' + d.lenSlots(one) + ' toast "' + toast() + '"');
one.len = '16'; one.dot = false; one.xs = 4; d.renderAll(); d.setSel({ li: 0, si: 0 }); key('-'); check('- on a sixteenth + 4 tied (5 slots): can still get shorter', d.lenSlots(one) < 5, 'now ' + d.lenSlots(one) + ' toast "' + toast() + '"');
// past MAX_SLOTS through Dotted, then / shrinks
s = build([mkLine(['one', 'two'])]); L0 = s.lines[0]; one = L0.syllables[0]; two = L0.syllables[1];
d.setSlotsRaw(one, 64); d.renderAll();
var r = menu(0, 0, 'Dotted'); check('Dotted on a 64-slot note stays within MAX_SLOTS', r === 'clicked' && d.lenSlots(one) <= 64, r + ' len ' + d.lenSlots(one) + ' (' + one.len + (one.dot ? '.' : '') + ' xs ' + one.xs + ')');
var before = d.lenSlots(one); d.setSel({ li: 0, si: 0 }); key('/'); check('/ (hold longer) never makes a note shorter', d.lenSlots(one) >= before, before + ' -> ' + d.lenSlots(one) + ' toast "' + toast() + '"');
var norm = d.normalize(d.plain(s)); check('normalize clamps a saved note to 64', d.lenSlots(norm.lines[0].syllables[0]) === 64, String(d.lenSlots(norm.lines[0].syllables[0])));
// rest toggle by key and by menu
s = build([mkLine(['one', 'two', 'three'])]); L0 = s.lines[0]; one = L0.syllables[0]; two = L0.syllables[1];
d.setSel({ li: 0, si: 1 }); key('0'); check('0 key makes two a rest', two.rest === true); key('0'); check('0 again clears it', two.rest === false);
check('menu: Rest toggles', menu(0, 4, 'Rest') === 'clicked' && two.rest === true);
check('a rest is not in the tap list', (function () { d.player.on = true; d.tapStart(); var n = d.tapW.list.length; d.tapStop(true); d.player.on = false; return n === 2; })());
// ---- 6. applyLength pushing through growNote, then undo ----
s = build([mkLine(['A', 'B', 'C', 'D'])]); L0 = s.lines[0]; var B = L0.syllables[1];
d.setSel({ li: 0, si: 1 }); var u0 = d.cur().undo.length; d.growNote(20);
check('growNote(20) on B: B = 24 (whole + 2 beats) at 4, C and D shoved to 28 and 32, line now 3 bars', d.lenSlots(B) === 24 && B.len === 'w' && B.xs === 8 && L0.syllables[2].pos === 28 && L0.syllables[3].pos === 32 && d.lineBars(L0, 16) === 3 && d.cur().undo.length === u0 + 1, syls(L0) + ' lineBars ' + d.lineBars(L0, 16));
check('the strip shows 3 bars', document.querySelectorAll('.timeline .cell').length === 3, document.querySelectorAll('.timeline .cell').length + ' cells');
d.undo(); s = d.S(); L0 = s.lines[0];
check('undo restores B, C, D and 1 bar', syls(L0) === 'A@0x4 B@4x4 C@8x4 D@12x4' && d.lineBars(L0, 16) === 1 && document.querySelectorAll('.timeline .cell').length === 1, syls(L0));
// applyLength direct: a gap after the pushed notes is kept, notes at the same slot (chord) are not pushed
s = build([mkLine([{ text: 'A', pos: 0 }, { text: 'a2', pos: 0 }, { text: 'B', pos: 4 }, { text: 'C', pos: 12 }])]); L0 = s.lines[0];
d.applyLength(L0, L0.syllables[0], 'h', false, 0);
check('applyLength A -> 8: B to 8, C keeps its 4-slot gap (16), the chord note a2 stays at 0', syls(L0) === 'A@0x8 a2@0x4 B@8x4 C@16x4', syls(L0));
// ---- shove and nudge by keys ----
s = build([mkLine(['A', 'B', 'C'])]); L0 = s.lines[0]; var A = L0.syllables[0]; B = L0.syllables[1]; var C = L0.syllables[2];
d.setSel({ li: 0, si: 1 });
key('ArrowRight', { altKey: true }); check('Alt+Right shoves B and C by the snap (2)', B.pos === 6 && C.pos === 10, syls(L0));
key('ArrowLeft', { altKey: true }); check('Alt+Left pulls them back', B.pos === 4 && C.pos === 8, syls(L0));
key('ArrowLeft', { altKey: true }); check('Alt+Left against A: toast, nothing moves', B.pos === 4 && toast() === 'No rest before this note', '"' + toast() + '"');
key('ArrowRight', { altKey: true, ctrlKey: true }); check('Ctrl+Alt+Right shoves by 1', B.pos === 5 && C.pos === 9, syls(L0));
key('Backspace'); check('Backspace shoves back up to 4, stopping at A\'s end', B.pos === 4 && C.pos === 8, syls(L0));
d.setSel({ li: 0, si: 0 }); key('ArrowLeft', { altKey: true }); check('shove A left: Already at the start', toast() === 'Already at the start' && A.pos === 0);
d.setSel({ li: 0, si: 1 }); key('ArrowRight', { shiftKey: true }); check('Shift+Right nudges B by 1, C pushed just enough (9)', B.pos === 5 && C.pos === 9, syls(L0));
key('ArrowLeft', { shiftKey: true }); check('Shift+Left nudges B back; C is not pulled back (stays 9)', B.pos === 4 && C.pos === 9, syls(L0));
d.setSel({ li: 0, si: 0 }); key('ArrowLeft', { ctrlKey: true }); check('Ctrl+Left on A: Already at the start', toast() === 'Already at the start' && A.pos === 0);
d.setSel({ li: 0, si: 2 }); key('ArrowLeft', { ctrlKey: true, shiftKey: true }); check('Ctrl+Shift+Left nudges C by 2 (7): B pulled? B ends at 8 > 7 so B moves to 3', C.pos === 7 && B.pos === 3, syls(L0));
// ---- bars ----
s = build([mkLine(['one', 'two']), mkLine(['four'])]); L0 = s.lines[0]; var L1 = s.lines[1];
var plus = Array.prototype.filter.call(document.querySelectorAll('.cellbtn'), function (b) { return b.textContent === '+'; });
check('two + buttons (one per line), no minus yet', plus.length === 2 && document.querySelectorAll('.cellbtn').length === 2, document.querySelectorAll('.cellbtn').length + ' buttons');
plus[0].click(); check('+ bar on line 0: bars 2, strip 3 cells, a minus button appears', L0.bars === 2 && document.querySelectorAll('.timeline .cell').length === 3 && document.querySelectorAll('.cellbtn').length === 3, 'bars ' + L0.bars + ' cells ' + document.querySelectorAll('.timeline .cell').length);
var minus = Array.prototype.filter.call(document.querySelectorAll('.cellbtn'), function (b) { return b.textContent === '−'; })[0];
check('the minus button sits in line 0\'s last cell', minus && minus.closest('.cell').title.indexOf('Line 1, bar 2') === 0, minus && minus.closest('.cell').title);
minus.click(); check('- bar: back to 1', L0.bars === 1 && document.querySelectorAll('.timeline .cell').length === 2);
d.setSel(null); d.addBarToSelected(-1); check('addBarToSelected with nothing selected: toast', toast() === 'Select a syllable on that line first');
d.setSel({ li: 0, si: 0 }); d.addBarToSelected(-1); check('addBarToSelected(-1) at minBars: toast', toast() === 'That bar has syllables in it' && L0.bars === 1);
d.addBarToSelected(1); check('addBarToSelected(+1): 2 bars', L0.bars === 2 && d.lineBars(L0, 16) === 2);
$('dropBar').click(); check('the Drop bar button drops it', L0.bars === 1, 'bars ' + L0.bars);
d.undo(); check('undo restores the bar', d.S().lines[0].bars === 2);
// ---- marks ----
d.state.marks = [{ li: 0, si: 0 }, { li: 0, si: 1 }]; d.clearMarks(); check('clearMarks empties marks and joinFirst', d.state.marks.length === 0 && d.state.joinFirst === null);
d.state.marks = [{ li: 0, si: 0 }]; d.drawSystems(); check('a marked chip draws with .mark', document.querySelectorAll('.syl-chip.mark').length === 1);
key('Escape'); check('Escape clears marks and redraws', d.state.marks.length === 0 && document.querySelectorAll('.syl-chip.mark').length === 0);
// select by clicking a chip (pointerdown/up without moving)
s = build([mkLine(['one', 'two'])]); L0 = s.lines[0];
var c2 = chipOf(0, 4); c2.el.setPointerCapture = function () {}; c2.el.hasPointerCapture = function () { return true; };
var rr = c2.el.getBoundingClientRect(), px = rr.left + 5, py = rr.top + 5;
c2.el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true, clientX: px, clientY: py, button: 0, buttons: 1, pointerId: 3, pointerType: 'mouse' }));
c2.el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, cancelable: true, clientX: px + 1, clientY: py, button: 0, pointerId: 3, pointerType: 'mouse' }));
check('a click on a chip selects it (setSel through attachChip)', d.selected() && d.selected().si === 1 && document.querySelector('.syl-chip.on') && document.querySelector('.syl-chip.on').textContent === 'two', d.selected() && d.selected().y.text);

// ---- rest toggle then Place words ----
var fps = 100, N = fps * 60;
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
function makeSong() { var full = new Float32Array(N), low = new Float32Array(N), voice = new Float32Array(N), i; for (i = 0; i < N; i++) { full[i] = 0.5; low[i] = 0.4; voice[i] = 0.4; } var k = 0; for (var t = 1.0; t < 59; t += 0.5, k++) { var pos = k % 4; if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else if (pos === 2) { bump(low, t, 1.8, 12); bump(full, t, 1.9, 10); } else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); } } return { full: full, low: low, voice: voice }; }
function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), k; for (k = k0; k < k1 + 6 && k < env.length; k++) { var v; if (k < k0 + 3) v = 0.4 + 1.9 * (k - k0 + 1) / 3; else if (k < k1) v = 2.3 + 0.05 * Math.sin(k); else v = 2.3 - 1.9 * (k - k1 + 1) / 6; if (v > env[k]) env[k] = v; } }
var spans = [[20.10, 20.35], [20.40, 20.60], [20.85, 21.35], [21.60, 21.80], [21.85, 22.05], [22.35, 23.20], [24.60, 24.85], [24.90, 25.10], [25.35, 26.30]];
var lrc = '[00:19.95] Silent night, holy night\n[00:24.45] All is calm\n';
var realFetch = window.fetch;
window.fetch = function (url, opts) { if (String(url).indexOf('/lyrics') === 0) return Promise.resolve({ ok: true, headers: new Headers({ 'content-type': 'application/json' }), json: function () { return Promise.resolve({ ok: true, synced: lrc, plain: '', duration: 60, track: 'Test Song', artist: 'Tester' }); } }); return realFetch(url, opts); };
s = d.S(); s.time = '4/4'; s.bpm = 100; s.audio = null; s.title = ''; s.filled = null;
s.lyrics = 'Silent night, holy night\nAll is calm'; s.lines = d.parseLyrics(s.lyrics);
s.spotify = { trackId: 'fake-rest', name: 'Test Song · Tester', durationMs: 60000, title: 'Test Song', artist: 'Tester', album: '' };
var song = makeSong(); spans.forEach(function (p) { sing(song.voice, p[0], p[1]); });
d.cur().audio = { el: { paused: true, currentTime: 0, duration: 60, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'test.wav', peaks: null, duration: 60, onset: d.risesOf(song.full), voice: song.voice, low: song.low, blob: false };
var l0 = s.lines[0]; say('LOG line 0 syllables: ' + l0.syllables.map(function (y) { return y.text; }).join(' '));
var ho = l0.syllables.filter(function (y) { return y.text === 'ho'; })[0]; ho.rest = true; d.renderAll();
var wordsBefore = l0.syllables.map(function (y) { return y.text; }).join(' ');
d.autoPlaceWords().then(function () {
  var s2 = d.S(), L = s2.lines[0], words = L.syllables.map(function (y) { return y.text; }).join(' ');
  var rests = 0; s2.lines.forEach(function (l) { if (l.kind === 'line') l.syllables.forEach(function (y) { if (y.rest) rests++; }); });
  check('Place words: no rest syllables remain', rests === 0, rests + ' rests');
  check('Place words keeps the word that was toggled to a rest ("ho")', words === wordsBefore, 'before "' + wordsBefore + '" after "' + words + '"');
  say('LOG after place: ' + s2.lines.map(function (l) { return l.kind === 'line' ? syls(l) : '[h]'; }).join(' | ') + ' bpm ' + s2.bpm + ' time ' + s2.time);
  window.fetch = realFetch;
}, function (e) { say('FAIL place rejected: ' + (e && e.stack || e)); window.fetch = realFetch; });
