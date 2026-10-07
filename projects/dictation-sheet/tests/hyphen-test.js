// A hyphen typed in the word box cuts the word at the cursor: the part before stays on the note, linked on ("ev-"),
// the part after goes to a new eighth note right after it, box open, cursor at its start.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function box() { return document.querySelector('.syl-chip.editing'); }
function bkey(k) { box().dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true })); }
function caret(n) { var b = box(), r = document.createRange(), t = b.firstChild || b; r.setStart(t, n); r.collapse(true); var x = window.getSelection(); x.removeAllRanges(); x.addRange(r); }
function caretAt() { var x = window.getSelection(), pre = document.createRange(); pre.selectNodeContents(box()); pre.setEnd(x.getRangeAt(0).startContainer, x.getRangeAt(0).startOffset); return pre.toString().length; }
function snap() { return d.sortedSyls(d.S().lines[0]).map(function (y) { return (y.text || '_') + (y.hy ? '-' : '') + '@' + y.pos + 'x' + d.lenSlots(y); }).join(' '); }
s.time = '4/4'; s.bpm = 100; s.view = 'vocals'; s.lines = [{ kind: 'line', bars: 2, syllables: [] }]; d.cur().sel = null; d.cur().undo = []; d.state.tool = 'add'; d.syncTools(); d.renderAll();
d.addNoteAt(0, 0);
box().textContent = 'everything'; caret(2); bkey('-');
check('- after "ev": "ev-" stays on the note, "erything" goes to a new eighth at slot 4', snap() === 'ev-@0x4 erything@4x2', snap());
check('the new box is open with "erything", the cursor at its start', !!box() && box().textContent === 'erything' && caretAt() === 0, box() && box().textContent + ' caret ' + caretAt());
caret(3); bkey('-');
check('- after "ery": ev- ery- thing', snap() === 'ev-@0x4 ery-@4x2 thing@6x2' && box().textContent === 'thing', snap());
check('the strip shows three chips chained', Array.prototype.map.call(document.querySelectorAll('.syl-chip'), function (c) { return c.textContent; }).join(' ').indexOf('ev- ery-') === 0);
bkey('Enter');
setTimeout(function () {
  check('Enter keeps "thing" and opens the next word after it', snap() === 'ev-@0x4 ery-@4x2 thing@6x2 _@8x2', snap());
  bkey('Escape');
  // a hyphen at the very start does nothing; at the end it opens an empty linked note
  d.addNoteAt(0, 12); box().textContent = 'so'; caret(0); bkey('-');
  check('- at the start of the word does nothing', box() && box().textContent === 'so' && d.S().lines[0].syllables.length === 4, snap());
  caret(2); bkey('-');
  check('- at the end: "so-" and an empty next note to type into', snap() === 'ev-@0x4 ery-@4x2 thing@6x2 so-@12x4 _@16x2' && box() && box().textContent === '', snap());
  bkey('Escape');
  check('Escape on it drops the empty note', snap() === 'ev-@0x4 ery-@4x2 thing@6x2 so-@12x4', snap());
  d.state.tool = 'move'; d.syncTools();
  say('LOG done');
}, 50);
