// The note pad: eleven keys in a row along the scale, slid one note at a time by the arrows on either side (Shift: an
// octave); 1 is do in the Vocals view and the key's tonic elsewhere; it follows the key; the number keys sound it.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var pad = document.getElementById('pad'), btn = document.getElementById('padBtn'), down = document.getElementById('padDown'), up = document.getElementById('padUp');
function keys() { return Array.prototype.slice.call(pad.querySelectorAll('#padKeys button')); }
function nums() { return keys().map(function (b) { return b.querySelector('b').textContent; }).join(' '); }
function syls() { return keys().map(function (b) { return b.childNodes[1].textContent; }).join(' '); }
function names() { return keys().map(function (b) { return b.querySelector('.nm').textContent; }).join(' '); }
function midis() { return d.padNotes().map(function (n) { return n.midi; }); }
function rising() { var m = midis(); return m.length === 10 && m.every(function (x, i) { return i === 0 || x > m[i - 1]; }); }
function key(k) { document.dispatchEvent(new KeyboardEvent('keydown', { key: k, bubbles: true, cancelable: true })); }
function lit() { return keys().map(function (b, i) { return b.classList.contains('on') ? i : -1; }).filter(function (i) { return i >= 0; }); }
function clearLit() { keys().forEach(function (b) { b.classList.remove('on'); }); }
s.key = { tonic: 'C', mode: 'major', laMinor: true }; s.view = 'vocals'; s.tuning = 440; s.lines = []; d.cur().sel = null; d.state.prefs.pad = false; d.state.prefs.padStart = null; d.renderAll();
check('closed at first', pad.hidden && !btn.classList.contains('on'));
btn.click();
check('the Pad button opens it', !pad.hidden && btn.classList.contains('on') && d.state.prefs.pad === true);
check('ten keys, 1 to 7 then 1 to 3 again', keys().length === 10 && nums() === '1 2 3 4 5 6 7 1 2 3', nums());
check('do re mi fa sol la ti do re mi', syls() === 'do re mi fa sol la ti do re mi', syls());
check('C major from C4: C4 D4 E4 F4 G4 A4 B4 C5 D5 E5', names() === 'C4 D4 E4 F4 G4 A4 B4 C5 D5 E5' && rising(), names());
check('the head shows the range', document.getElementById('padRange').textContent === 'C4 to E5', document.getElementById('padRange').textContent);
check('arrows sit on either side of the keys', down.getBoundingClientRect().right <= keys()[0].getBoundingClientRect().left && up.getBoundingClientRect().left >= keys()[9].getBoundingClientRect().right);
check('a key tells its pitch', /Degree 1, do, C · 261\.6 Hz/.test(keys()[0].title), keys()[0].title);
var threw = false; try { keys()[0].click(); } catch (e) { threw = true; }
check('a press lights the key', !threw && keys()[0].classList.contains('on'));
// the arrows slide the row one note
up.click();
check('› slides up one note: D4 to F5, re first', names() === 'D4 E4 F4 G4 A4 B4 C5 D5 E5 F5' && syls().indexOf('re mi fa') === 0 && rising(), names());
down.click(); down.click();
check('‹ twice slides down to B3: ti do re ...', names() === 'B3 C4 D4 E4 F4 G4 A4 B4 C5 D5' && rising(), names());
up.dispatchEvent(new MouseEvent('click', { bubbles: true, shiftKey: true }));
check('Shift+› slides an octave up: B4 to D6', names().split(' ')[0] === 'B4' && names().split(' ')[9] === 'D6', names());
down.dispatchEvent(new MouseEvent('click', { bubbles: true, shiftKey: true })); up.click();
check('back to C4', names().split(' ')[0] === 'C4');
// the number keys: 1 to 7 the lowest key in view with that degree, 8 the second 1
clearLit(); key('3');
check('3 lights the first mi (E4, key 3)', lit().join() === '2', lit().join());
clearLit(); key('8');
check('8 lights the second do (C5, key 8)', lit().join() === '7', lit().join());
up.click(); up.click(); up.click(); clearLit(); key('1');
check('slid to F4: 1 lights the C5 in view (key 5)', names().split(' ')[0] === 'F4' && lit().join() === '4', names() + ' lit ' + lit().join());
down.click(); down.click(); down.click();
s.lines = [{ kind: 'line', bars: 2, syllables: [d.normalize({ lines: [{ kind: 'line', syllables: [{ text: 'one', pos: 0 }] }] }).lines[0].syllables[0]] }]; d.cur().sel = { li: 0, si: 0 }; d.renderAll();
clearLit(); key('5');
check('5 with a note selected sets it to sol and lights key 5', s.lines[0].syllables[0].sol === 'sol' && lit().join() === '4', s.lines[0].syllables[0].sol);
d.cur().sel = null; s.lines = []; d.renderAll();
// the key changes
s.key = { tonic: 'A', mode: 'minor', laMinor: true }; d.renderAll();
check('A minor (la-based), Vocals: 1 is do = C', syls() === 'do re mi fa sol la ti do re mi' && names().split(' ')[0] === 'C4' && /do = C/.test(document.getElementById('padKey').textContent), names());
s.view = 'guitar'; d.renderAll();
check('A minor, Guitar: 1 is A, la ti do re mi fa sol la ti do', syls() === 'la ti do re mi fa sol la ti do' && names().split(' ')[0] === 'A4' && rising(), names() + ' | ' + syls());
s.key = { tonic: 'G', mode: 'major', laMinor: true }; d.renderAll();
check('G major, Guitar: G A B C D E F# G A B', names().replace(/\d/g, '') === 'G A B C D E F# G A B' && rising(), names());
s.key = { tonic: 'Eb', mode: 'major', laMinor: true }; d.renderAll();
check('Eb major: Eb F G Ab Bb C D Eb F G', names().replace(/\d/g, '') === 'Eb F G Ab Bb C D Eb F G' && rising(), names());
// the letter row plays the keys; Shift+P closes the pad, P opens it
clearLit(); key('q');
check('Q plays the far-left key', lit().join() === '0', lit().join());
clearLit(); key('t');
check('T plays the fifth key', lit().join() === '4', lit().join());
clearLit(); key('p');
check('P plays the far-right key (the pad stays open)', lit().join() === '9' && !pad.hidden, lit().join());
check('each key shows its letter', keys().map(function (b) { return b.querySelector('.kk').textContent; }).join('') === 'QWERTYUIOP');
var tool0 = d.state.tool; clearLit(); key('e');
check('E plays the pad, it does not pick the Edit tool', d.state.tool === tool0 && lit().join() === '2', d.state.tool);
document.dispatchEvent(new KeyboardEvent('keydown', { key: 'P', shiftKey: true, bubbles: true, cancelable: true }));
check('Shift+P closes it', pad.hidden && d.state.prefs.pad === false);
key('e');
check('closed, E picks the Edit tool again', d.state.tool === 'edit');
key('p');
check('P opens it again', !pad.hidden && keys().length === 10);
var ta = document.getElementById('lyrics'); d.state.prefs.side = true; d.renderAll(); ta.focus(); ta.dispatchEvent(new KeyboardEvent('keydown', { key: 'p', bubbles: true, cancelable: true }));
check('P typed in the words box does not touch it', !pad.hidden);
document.getElementById('padClose').click();
check('the ✕ closes it', pad.hidden && d.state.prefs.pad === false);
s.key = { tonic: 'C', mode: 'major', laMinor: true }; s.view = 'vocals'; d.state.prefs.padStart = null; d.renderAll();
say('LOG done');
