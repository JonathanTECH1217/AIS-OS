// A pad key tapped while a note is selected writes that pitch (degree and octave of the key) and steps to the next note.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
function keys() { return Array.prototype.slice.call(document.querySelectorAll('#padKeys button')); }
function key(k) { document.getElementById('work').dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true })); }
function selText() { var c = d.cur().sel; return c ? d.S().lines[c.li].syllables[c.si].text : null; }
function pitch(i) { var y = d.sortedSyls(d.S().lines[0])[i]; return y.sol + ' ' + y.note + d.sylMidiFor(y, d.instFor(d.S())); }
d.player.keyTone = function () {}; // silent
d.state.prefs.side = false; d.state.prefs.padStart = null; d.cur().audio = null;
s = d.S(); s.time = '4/4'; s.view = 'vocals'; s.key = { tonic: 'C', mode: 'major', laMinor: true };
s.lines = [{ kind: 'line', bars: 2, syllables: [mk(0, 'q', 'one'), mk(4, 'q', 'two'), mk(8, 'q', 'three'), mk(12, 'q', 'four')] }];
d.state.tool = 'move'; d.syncTools(); d.cur().sel = { li: 0, si: 0 }; d.state.prefs.pad = true; d.renderAll(); document.getElementById('work').focus();
check('the pad shows C4 to E5', keys().length === 10 && keys()[0].querySelector('.nm').textContent === 'C4');
keys()[4].click();
check('a click on the pad\'s G4 (sol) writes sol G4 to "one" and steps to "two"', pitch(0) === 'sol G67' && selText() === 'two', pitch(0) + ' | sel ' + selText());
key('i');
check('I (the pad\'s C5, do) writes do C5 to "two" and steps to "three"', pitch(1) === 'do C72' && selText() === 'three', pitch(1) + ' | sel ' + selText());
keys()[0].dispatchEvent(new MouseEvent('click', { bubbles: true, shiftKey: true }));
check('Shift+click on C4 writes an octave down: do C3', pitch(2) === 'do C60'.replace('60', '48') && selText() === 'four', pitch(2) + ' | sel ' + selText());
var undoN = d.cur().undo.length; d.undo();
check('each write is one undo step', d.cur().undo.length === undoN - 1 && d.sortedSyls(d.S().lines[0])[2].note !== 'C' || d.sortedSyls(d.S().lines[0])[2].oct !== 3, pitch(2));
// nothing selected: the pad only sounds
d.cur().sel = null; d.renderAll(); var before = JSON.stringify(d.S().lines[0].syllables.map(function (y) { return [y.sol, y.oct]; }));
keys()[2].click();
check('with nothing selected a pad key only sounds', JSON.stringify(d.S().lines[0].syllables.map(function (y) { return [y.sol, y.oct]; })) === before);
// the Drums view: no write
d.S().view = 'drums'; d.cur().sel = { li: 0, si: 3 }; d.renderAll(); before = JSON.stringify(d.S().lines[0].syllables.map(function (y) { return [y.sol, y.oct]; }));
keys()[2].click();
check('in the Drums view a pad key writes nothing', JSON.stringify(d.S().lines[0].syllables.map(function (y) { return [y.sol, y.oct]; })) === before);
d.S().view = 'vocals'; d.state.prefs.pad = false; d.cur().sel = null; d.renderAll();
say('LOG done');
