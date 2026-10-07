// The keyboard flow in the Add tool: arrows move the cursor by the snap step, ; and ' shrink and grow the step, n puts
// a note at the cursor with its box open, and the cursor waits after each note.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function key(k, opts) { document.dispatchEvent(new KeyboardEvent('keydown', Object.assign({ key: k, bubbles: true, cancelable: true }, opts || {}))); }
function editing() { return document.querySelector('.syl-chip.editing'); }
function snap(l) { return d.sortedSyls(l).map(function (y) { return (y.text || '_') + '@' + y.pos + 'x' + d.lenSlots(y); }).join(' '); }
function line() { return d.S().lines[0]; }
s.time = '4/4'; s.bpm = 100; s.view = 'vocals'; s.lines = [{ kind: 'line', bars: 4, syllables: [] }]; s.lyrics = ''; s.title = ''; s.filled = null; s.spotify = null; d.cur().undo = []; d.cur().audio = null; d.state.audioOn = false;
d.state.prefs.snap = '2'; d.state.tool = 'add'; d.syncTools(); d.renderAll();
d.player.startSlot = -1;
// 1. arrows move the cursor by the step (an eighth = 2 slots)
key('ArrowRight'); key('ArrowRight');
check('two right arrows at an eighth step put the cursor at slot 4', d.player.startSlot === 4, d.player.startSlot);
check('the status bar names the spot', document.getElementById('stPos').textContent.indexOf('Play starts at bar 1, beat 2') === 0, document.getElementById('stPos').textContent);
// 2. ' grows the step, ; shrinks it
key("'"); check("' grows the step to a beat", d.state.prefs.snap === 'beat', d.state.prefs.snap);
key("'"); key("'"); check("' again: two beats, then a bar", d.state.prefs.snap === 'bar', d.state.prefs.snap);
key("'"); check('a bar is the biggest step', d.state.prefs.snap === 'bar', d.state.prefs.snap);
key('ArrowRight'); check('a right arrow at a bar step moves 16 slots (to 20)', d.player.startSlot === 20, d.player.startSlot);
key(';'); key(';'); key(';'); key(';');
check('four ; shrink the step to a sixteenth', d.state.prefs.snap === '1', d.state.prefs.snap);
key(';'); check('a sixteenth is the smallest step', d.state.prefs.snap === '1', d.state.prefs.snap);
check('the Snap box follows', document.getElementById('snapSel').value === '1', document.getElementById('snapSel').value);
key('ArrowLeft'); check('a left arrow at a sixteenth moves one slot back (19)', d.player.startSlot === 19, d.player.startSlot);
key('ArrowLeft', { shiftKey: true }); check('Shift+arrow is always a sixteenth (18)', d.player.startSlot === 18, d.player.startSlot);
// 3. the cursor never leaves the sheet
d.state.prefs.snap = 'bar'; for (var i = 0; i < 10; i++) key('ArrowRight');
check('the cursor stops at the last slot (63)', d.player.startSlot === 63, d.player.startSlot);
for (var j = 0; j < 10; j++) key('ArrowLeft');
check('and at slot 0 going back', d.player.startSlot === 0, d.player.startSlot);
// 4. n puts a note at the cursor with its box open; the cursor waits after it
d.state.prefs.snap = 'beat'; key('ArrowRight'); key('ArrowRight');
key('n');
var ch = editing();
check('n adds a note at the cursor (slot 8) with its box open', line().syllables.length === 1 && line().syllables[0].pos === 8 && !!ch, snap(line()) + (ch ? ' box' : ' no box'));
check('the cursor now waits right after the note (slot 12)', d.player.startSlot === 12, d.player.startSlot);
ch.textContent = 'one'; ch.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
setTimeout(function () {
  var ch2 = editing();
  check('Enter opens the next note (an eighth) at 12, the cursor moves to 14', line().syllables.length === 2 && d.sortedSyls(line())[1].pos === 12 && !!ch2 && d.player.startSlot === 14, snap(line()) + ' cursor ' + d.player.startSlot);
  ch2.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
  setTimeout(function () {
    check('Enter on the empty box ends the line', line().syllables.length === 1 && !editing(), snap(line()));
    // 5. n on an empty sheet starts a line first
    d.S().lines = []; d.renderAll(); d.player.startSlot = -1;
    key('n');
    check('n on an empty sheet starts a line and puts the note at slot 0', d.S().lines.length === 1 && d.S().lines[0].syllables.length === 1 && d.S().lines[0].syllables[0].pos === 0 && !!editing(), d.S().lines.length + ' lines ' + (d.S().lines[0] ? snap(d.S().lines[0]) : ''));
    editing().dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
    // 6. in the Move tool the arrows keep their old meaning (no cursor move) and n does nothing
    d.state.tool = 'move'; d.syncTools(); d.player.startSlot = 4; key('ArrowRight');
    check('in Move the arrows do not move the cursor', d.player.startSlot === 4, d.player.startSlot);
    var before = d.S().lines[0].syllables.length; key('n');
    check('in Move n adds nothing', d.S().lines[0].syllables.length === before);
    // 7. a pause keeps the cursor where the song stopped: the arrows go on from there, and so does the next Play
    d.S().lines = [{ kind: 'line', bars: 4, syllables: [] }]; d.renderAll(); d.state.tool = 'add'; d.syncTools(); d.state.prefs.snap = 'beat';
    d.player.startSlot = 32; d.player.start();
    check('Play starts at bar 3 (slot 32)', d.player.on && d.player.slot0 === 32, 'on ' + d.player.on + ' slot0 ' + d.player.slot0);
    d.player.stop();
    check('after a pause the cursor stands at bar 3, not at the start', !d.player.on && d.player.startSlot === 32, d.player.startSlot);
    key('ArrowLeft');
    check('a left arrow goes one beat back from there (28), not to the start', d.player.startSlot === 28, d.player.startSlot);
    d.player.start(); check('Play picks up from the cursor (28)', d.player.slot0 === 28, d.player.slot0); d.player.stop();
    // a song that ran to its end starts over
    d.player.start(); d.player.t0 = d.player.now() - 1000 * d.player.slotSec; d.player.stop();
    check('a song that ran to its end starts over next time', d.player.startSlot === -1, d.player.startSlot);
    say('LOG done');
  }, 50);
}, 50);
