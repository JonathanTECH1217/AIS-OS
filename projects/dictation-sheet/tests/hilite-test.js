// The strip lights a chip the moment the red line's right-most pixel touches the chip's left-most pixel, measured on
// screen: the red line is swept across two bars in steps of a twentieth of a sixteenth.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
s.time = '4/4'; s.bpm = 100; s.view = 'vocals'; d.cur().audio = null; d.state.audioOn = false; d.cur().sel = null;
// touching chips (one, two), a gap (rest) before three, a bar line inside four's span, a sixteenth (five)
s.lines = [{ kind: 'line', bars: 2, syllables: [mk(0, 'q', 'one'), mk(4, 'q', 'two'), mk(10, '8', 'three'), mk(14, 'q', 'four'), mk(18, '16', 'five')] }];
d.renderAll(); d.player.relayout();
var chips = Array.prototype.slice.call(document.querySelectorAll('.syl-chip')), ph = d.editor.systems[0].ph;
var early = [], late = [], double = 0, steps = 0, firstLit = {};
for (var g = 0; g < 31.99; g += 0.05) {
  steps++;
  d.player.showAt(g); d.highlightSlot(d.player.bars[Math.floor(g / 16)], g);
  var pr = ph.getBoundingClientRect(), right = pr.right, lit = chips.filter(function (c) { return c.classList.contains('playing'); });
  if (lit.length > 1) double++;
  chips.forEach(function (c) {
    var r = c.getBoundingClientRect(), on = c.classList.contains('playing');
    if (on && firstLit[c.textContent] === undefined) firstLit[c.textContent] = { g: Math.round(g * 100) / 100, gap: Math.round((right - r.left) * 100) / 100 };
    // the red line's right edge is left of the chip's left edge: it must be dark
    if (on && right <= r.left - 0.01) early.push(c.textContent + '@' + g.toFixed(2) + ' (' + (right - r.left).toFixed(2) + ' px)');
  });
}
check('no chip ever lights before the red line touches its left edge (' + steps + ' spots)', early.length === 0, early.slice(0, 5).join(', '));
Object.keys(firstLit).forEach(function (k) {
  check('"' + k + '" lights within one step after the red line reaches its left pixel', firstLit[k].gap > 0 && firstLit[k].gap <= 1.0, 'at slot ' + firstLit[k].g + ', overlap ' + firstLit[k].gap + ' px');
});
check('all five chips lit at some point', Object.keys(firstLit).length === 5, Object.keys(firstLit).join(' '));
check('never two chips lit at once', double === 0, double + ' spots with two');
d.player.showAt(8.5); d.highlightSlot(d.player.bars[0], 8.5);
check('in the rest after "two" (slot 8.5) nothing is lit', chips.every(function (c) { return !c.classList.contains('playing'); }), chips.filter(function (c) { return c.classList.contains('playing'); }).map(function (c) { return c.textContent; }).join(','));
d.highlightClear();
say('LOG done');
