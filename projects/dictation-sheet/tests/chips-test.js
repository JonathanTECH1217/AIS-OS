// One chip per syllable on the strip (a hyphenated word's syllables chained, never one box); a tied note stays in
// its syllable's chip; a chip drags on its own; a click on a rest or an empty spot puts the red line there in every
// tool but Add, where it puts a note there.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text, extra) { var y = d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; if (extra) Object.keys(extra).forEach(function (k) { y[k] = extra[k]; }); return y; }
function lines() { return d.S().lines.filter(function (l) { return l.kind === 'line'; }); }
function chips() { return Array.prototype.slice.call(document.querySelectorAll('.syl-chip')); }
function texts() { return chips().map(function (c) { return c.textContent; }).join(' '); }
function posOf(text) { var y = lines()[0].syllables.filter(function (y) { return y.text === text; })[0]; return y ? y.pos : null; }
s.time = '4/4'; s.bpm = 100; s.view = 'vocals'; s.title = ''; s.filled = null; s.spotify = null; d.cur().audio = null; d.state.audioOn = false; d.cur().sel = null; d.cur().undo = []; d.player.startSlot = -1;
d.state.prefs.snap = '2';
// 1. a hyphenated word from the words panel: separate chips chained by hyphens
d.wordsToNotes('Ev-ery-thing so', '', { noUndo: true, quiet: true }); d.renderAll();
var ys = d.sortedSyls(lines()[0]);
check('the words panel made four notes, the first two linked on', ys.length === 4 && ys[0].hy === true && ys[1].hy === true && !ys[2].hy && !ys[3].hy, ys.map(function (y) { return y.text + (y.hy ? '-' : ''); }).join(' '));
check('four chips, one per syllable, the hyphens shown', chips().length === 4 && texts() === 'Ev- ery- thing so', texts());
var c = chips();
check('the chain: Ev- goes on, ery- came on and goes on, thing came on, so stands alone', c[0].classList.contains('hy') && !c[0].classList.contains('cont') && c[1].classList.contains('hy') && c[1].classList.contains('cont') && c[2].classList.contains('cont') && !c[2].classList.contains('hy') && !c[3].classList.contains('hy') && !c[3].classList.contains('cont'), c.map(function (x) { return x.className; }).join(' | '));
var cell = d.editor.systems[0].geo.cells[0], sw = (cell.x1 - cell.x0) / 16;
check('each chip is its own quarter wide, one beat apart', c.every(function (x) { return Math.abs(parseFloat(x.style.width) - (4 * sw - 3)) < 1; }) && Math.abs(parseFloat(c[1].style.left) - parseFloat(c[0].style.left) - 4 * sw) < 1, c.map(function (x) { return Math.round(parseFloat(x.style.width)); }).join(','));
check('each chip ends where its own note ends', c.map(function (x) { return x.getAttribute('data-end'); }).join(',') === '4,8,12,16', c.map(function (x) { return x.getAttribute('data-end'); }).join(','));
check('the tip names the word', /one of the 3 syllables of a word/.test(c[1].title) && !/syllables of a word/.test(c[3].title), c[1].title);
// 2. the red line lights the chip it is over, one at a time
d.highlightSlot(d.player.bars[0], 5);
check('the red line at beat 2 lights only "ery-"', !c[0].classList.contains('playing') && c[1].classList.contains('playing') && !c[2].classList.contains('playing'));
d.highlightClear();
// 3. a note tied on to a syllable stays inside its chip
lines()[0].syllables.push(mk(16, '8', '', { tie: true })); ys[3].pos = 12; d.renderAll();
c = chips(); cell = d.editor.systems[0].geo.cells[0]; sw = (cell.x1 - cell.x0) / 16; // the line grew to two bars, so the bar width changed
check('a tied eighth after "so" makes no chip of its own; "so" runs to slot 18', c.length === 4 && c[3].getAttribute('data-end') === '18' && Math.abs(parseFloat(c[3].style.width) - (6 * sw - 3)) < 1 && /2 tied notes/.test(c[3].title), c.length + ' chips, so ends ' + c[3].getAttribute('data-end') + ', width ' + c[3].style.width + ' (want ' + (6 * sw - 3) + '), title: ' + c[3].title);
lines()[0].syllables.pop(); d.renderAll(); c = chips();
// 4. a chip drags on its own (Move): "ery-" two beats right; the other syllables stay
d.state.tool = 'move'; d.syncTools();
var tl = c[1].parentNode, r1 = c[1].getBoundingClientRect(), x0 = r1.left + 5, y0 = r1.top + 5;
c[1].dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x0, clientY: y0, button: 0, pointerId: 3 }));
c[1].dispatchEvent(new PointerEvent('pointermove', { bubbles: true, clientX: x0 + 8 * sw, clientY: y0, pointerId: 3 }));
c[1].dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x0 + 8 * sw, clientY: y0, pointerId: 3 }));
check('"ery" moved two beats (to slot 12), "so" slid on to 16, "Ev" and "thing" stayed, four notes still', lines()[0].syllables.length === 4 && posOf('ery') === 12 && posOf('so') === 16 && posOf('Ev') === 0 && posOf('thing') === 8, d.sortedSyls(lines()[0]).map(function (y) { return y.text + '@' + y.pos; }).join(' '));
d.undo();
check('undo puts it back', d.sortedSyls(lines()[0]).map(function (y) { return y.pos; }).join(',') === '0,4,8,12');
// 5. a click on a rest puts the red line at the rest, in Move, Edit and Cut; with Add it puts a note there
s = d.S(); s.lines = [{ kind: 'line', bars: 2, syllables: [mk(0, 'q', 'one'), mk(8, 'q', 'two')] }]; d.cur().sel = null; d.renderAll(); d.player.startSlot = -1;
function gap() { return document.querySelector('.notehit.gap'); }
check('a rest sits between the notes', !!gap() && /play from here/.test(gap().title), gap() && gap().title);
['move', 'edit', 'cut'].forEach(function (tool) {
  d.state.tool = tool; d.syncTools(); d.player.startSlot = -1; d.cur().sel = null;
  gap().dispatchEvent(new MouseEvent('click', { bubbles: true }));
  check(tool + ': a click on the rest puts the red line at its start (slot 4) and selects nothing', d.player.startSlot === 4 && !d.cur().sel && s.lines[0].syllables.length === 2, 'startSlot ' + d.player.startSlot + ' sel ' + JSON.stringify(d.cur().sel));
});
d.state.tool = 'add'; d.syncTools(); d.player.startSlot = -1;
gap().dispatchEvent(new MouseEvent('click', { bubbles: true }));
check('Add: a click on the rest puts a note at slot 4 with its box open', s.lines[0].syllables.length === 3 && d.sortedSyls(s.lines[0])[1].pos === 4 && !!document.querySelector('.syl-chip.editing'), s.lines[0].syllables.length + ' notes');
var box = document.querySelector('.syl-chip.editing'); if (box) box.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
// 6. a click on an empty spot of a bar still puts the red line there (Move), snapped to an eighth
d.state.tool = 'move'; d.syncTools(); d.player.startSlot = -1;
var bh = document.querySelector('.barhit'), br = bh.getBoundingClientRect();
bh.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: br.left + br.width * 0.72, clientY: br.top + 10 }));
check('a click at 72 % of bar 1 puts the red line at slot 12', d.player.startSlot === 12, d.player.startSlot);
d.state.tool = 'move'; d.syncTools();
say('LOG done');
