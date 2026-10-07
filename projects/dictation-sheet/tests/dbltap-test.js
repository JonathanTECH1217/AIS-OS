// Two taps on a word (its chip, or its note on the staff) within 450 ms open its text box, in Move, Edit and Add; two
// slow taps only select and deselect; Cut still cuts.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
function chip(t) { return Array.prototype.filter.call(document.querySelectorAll('.syl-chip'), function (c) { return c.textContent === t; })[0]; }
function tapAt(x, y) { var el = document.elementFromPoint(x, y); el.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: x, clientY: y, button: 0, pointerId: 1 })); var el2 = document.elementFromPoint(x, y) || el; (document.contains(el) ? el : el2).dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x, clientY: y, pointerId: 1 })); }
function editing() { return document.querySelector('.syl-chip.editing'); }
d.state.prefs.side = false; d.state.prefs.pad = false; // the words panel would cover the strip
function reset(tool) { var s1 = d.S(); s1.lines = [{ kind: 'line', bars: 2, syllables: [mk(0, 'q', 'one'), mk(4, 'q', 'two'), mk(8, 'q', 'three')] }]; d.cur().sel = null; d.state.tool = tool; d.syncTools(); d.renderAll(); }
function center(el) { var r = el.getBoundingClientRect(); return [r.left + 8, r.top + r.height / 2]; }
['move', 'edit', 'add'].forEach(function (tool) {
  reset(tool); var p = center(chip('two'));
  tapAt(p[0], p[1]); tapAt(p[0], p[1]);
  var b = editing();
  check(tool + ': two quick taps on "two" open its text box', !!b && b.textContent === 'two' && d.cur().sel && d.S().lines[0].syllables[d.cur().sel.si].text === 'two', b ? 'box "' + b.textContent + '"' : 'no box');
  if (b) b.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
});
// a tap sounds the word's note: the pitch of "two" (C4 = 60, a quarter at 100 bpm = 0.6 s)
var tones = [], realTone = d.player.playTone; d.player.playTone = function (m, dur) { tones.push([m, Math.round(dur * 100) / 100]); };
reset('move'); d.S().lines[0].syllables[1].note = 'E'; d.S().lines[0].syllables[1].oct = 4; d.S().lines[0].syllables[1].noteAuto = false; d.renderAll();
var p = center(chip('two')); tapAt(p[0], p[1]);
check('a tap on "two" sounds its note, E4 for a quarter (0.6 s)', tones.length === 1 && tones[0][0] === 64 && tones[0][1] === 0.6, JSON.stringify(tones));
var y3 = d.S().lines[0].syllables[2]; y3.note = 'G'; y3.oct = 4; y3.noteAuto = false; d.renderAll();
var nh0 = document.querySelectorAll('.notehit:not(.gap)')[2], q0 = center(nh0); d.state.tool = 'edit'; d.syncTools(); tones = []; d.cur().sel = null; tapAt(q0[0], q0[1]);
check('a tap on the note of "three" on the staff sounds it too (G4)', tones.length === 1 && tones[0][0] === 67, JSON.stringify(tones));
tones = []; var nhA = document.querySelectorAll('.notehit:not(.gap)')[0], qa = center(nhA); tapAt(qa[0], qa[1]);
check('a note with no pitch yet stays silent', tones.length === 0, JSON.stringify(tones));
d.player.playTone = realTone;
// two slow taps: select, then deselect, no box
reset('move'); p = center(chip('two'));
tapAt(p[0], p[1]);
setTimeout(function () {
tapAt(p[0], p[1]);
check('two slow taps keep the word selected (no toggle off), no box', !editing() && d.cur().sel && d.S().lines[0].syllables[d.cur().sel.si].text === 'two', JSON.stringify(d.cur().sel));
// taps on two different words: no box
reset('move'); var p1 = center(chip('one')), p2 = center(chip('two'));
tapAt(p1[0], p1[1]); tapAt(p2[0], p2[1]);
check('a tap on one word then another selects the second, no box', !editing() && d.cur().sel && d.S().lines[0].syllables[d.cur().sel.si].text === 'two');
// the note on the staff
reset('edit'); var nh = document.querySelectorAll('.notehit:not(.gap)')[2], q = center(nh);
tapAt(q[0], q[1]); tapAt(q[0], q[1]);
var b2 = editing();
check('two quick taps on the third note on the staff open "three"', !!b2 && b2.textContent === 'three', b2 ? b2.textContent : 'no box');
if (b2) { b2.textContent = 'free'; b2.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true })); }
check('typing and Enter keeps the new word', d.sortedSyls(d.S().lines[0])[2].text === 'free', d.sortedSyls(d.S().lines[0])[2].text);
var nb = editing(); if (nb) nb.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
// Cut: two taps cut, no box
reset('cut'); p = center(chip('two'));
tapAt(p[0] + 20, p[1]);
check('in Cut a tap still cuts the note', d.S().lines[0].syllables.length === 4 && !editing(), d.S().lines[0].syllables.length + ' notes');
d.state.tool = 'move'; d.syncTools();
say('LOG done');
}, 600);
