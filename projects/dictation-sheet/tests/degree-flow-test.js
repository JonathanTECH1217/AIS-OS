// Typing degrees over existing notes: a number sets the selected note's degree and steps to the next note; a click on
// the note that is now selected keeps it selected (it used to toggle off); Escape lets go.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
function key(k) { document.getElementById('work').dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true })); }
function chip(t) { return Array.prototype.filter.call(document.querySelectorAll('.syl-chip'), function (c) { return c.textContent === t; })[0]; }
function tap(el) { var r = el.getBoundingClientRect(), x = r.left + 8, y = r.top + r.height / 2; el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y, button: 0, pointerId: 2 })); el.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y, pointerId: 2 })); }
function selText() { var c = d.cur().sel; return c ? d.S().lines[c.li].syllables[c.si].text : null; }
function sols() { return d.sortedSyls(d.S().lines[0]).map(function (y) { return y.sol; }).join(' '); }
d.state.prefs.side = false; d.state.prefs.pad = false; d.cur().audio = null;
s = d.S(); s.time = '4/4'; s.view = 'vocals'; s.key = { tonic: 'C', mode: 'major', laMinor: true };
s.lines = [{ kind: 'line', bars: 2, syllables: [mk(0, 'q', 'one'), mk(4, 'q', 'two'), mk(8, 'q', 'three'), mk(12, 'q', 'four')] }];
d.cur().sel = null; d.state.tool = 'move'; d.syncTools(); d.renderAll();
tap(chip('one')); document.getElementById('work').focus();
check('a click selects "one"', selText() === 'one');
key('3');
check('3 sets "one" to mi and steps to "two"', d.sortedSyls(d.S().lines[0])[0].sol === 'mi' && selText() === 'two', sols() + ' | sel ' + selText());
setTimeout(function () {
  tap(chip('two'));
  check('a click on "two", already selected, keeps it selected', selText() === 'two', 'sel ' + selText());
  document.getElementById('work').focus(); key('5');
  check('5 then sets "two" to sol and steps to "three"', d.sortedSyls(d.S().lines[0])[1].sol === 'sol' && selText() === 'three', sols() + ' | sel ' + selText());
  key('1'); key('7');
  check('1 and 7 overwrite "three" and "four" in turn', sols() === 'mi sol do ti', sols());
  key('Escape');
  check('Escape lets go of the selection', selText() === null);
  say('LOG done');
}, 600);
