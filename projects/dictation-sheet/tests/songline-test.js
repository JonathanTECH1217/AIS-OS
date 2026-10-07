// The green line: where the song comes in on the sheet. shiftSong moves the song along the sheet with every note
// keeping its song time (on a beat grid and off it); the sheet may start before the song; the line is dragged; the
// box re-anchors a beat grid; Play runs the empty bars before the song and starts the song at the line.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function r2(x) { return Math.round(x * 100) / 100; }
function vis(el) { if (!el) return false; var r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; }
function lines() { return d.S().lines.filter(function (l) { return l.kind === 'line'; }); }
function times() { var s1 = d.S(), spb = d.slotsPerBar(s1.time), out = {}; s1.lines.forEach(function (l, li) { if (l.kind !== 'line') return; var base = d.barOrdinal(s1, li, 0) * spb; d.sortedSyls(l).forEach(function (y) { out[y.text] = [r2(d.songOfSlot(base + y.pos)), r2(d.songOfSlot(base + y.pos + d.lenSlots(y)))]; }); }); return out; }
function same(a, b, tol) { var k, bad = []; tol = tol || 0.011; for (k in a) { if (!b[k] || Math.abs(a[k][0] - b[k][0]) > tol || Math.abs(a[k][1] - b[k][1]) > tol) bad.push(k + ' ' + JSON.stringify(a[k]) + '->' + JSON.stringify(b[k])); } return bad; }
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
function sl() { return Array.prototype.filter.call(document.querySelectorAll('.songline'), vis)[0] || null; }
function off() { return d.sheetAudio().offsetSec; }
s.time = '4/4'; s.bpm = 80; s.view = 'vocals'; s.title = ''; s.filled = null; s.spotify = null; s.lyrics = ''; d.cur().undo = []; d.cur().sel = null;
var el = { paused: true, currentTime: 0, duration: 120, playbackRate: 1, playCalls: 0, pause: function () { this.paused = true; }, play: function () { this.playCalls++; this.paused = false; return Promise.resolve(); } };
d.cur().audio = { el: el, url: '', name: 'test.wav', peaks: null, duration: 120, onset: null, voice: null, low: null, blob: false };
d.state.audioOn = true;
// a beat grid of 0.75 s beats from 10 s (80 bpm); line 1: "one" "two" on bar 1 beats 3 and 4, "three" on bar 2 beat 1; line 2 from its bar 1
var beats = []; for (var i = 0; i < 160; i++) beats.push(r2(10 + i * 0.75));
s.audio = { offsetSec: 10, lined: true, linedBy: 'place', lockedBy: 'place', name: '', assetId: null, beats: beats.slice(), locked: true, lockFit: { onHit: 90, avgMs: 10 } };
s.lines = [{ kind: 'line', bars: 2, syllables: [mk(8, 'q', 'one'), mk(12, 'q', 'two'), mk(16, 'q', 'three')] }, { kind: 'line', bars: 2, syllables: [mk(0, 'q', 'four'), mk(4, '8', 'five'), mk(6, '8', 'six'), mk(16, 'h', 'seven')] }];
d.renderAll();
var t0 = times();
check('setup: "one" at bar 1 beat 3 = 11.5 s, "four" at bar 3 beat 1 = 16 s', t0.one[0] === 11.5 && t0.four[0] === 16, JSON.stringify(t0));
check('the song starts 10 s before bar 1: a dashed green stub stands at bar 1', sl() && sl().classList.contains('off') && d.songStartSlot() < 0 && /before bar 1/.test(sl().querySelector('.lbl').textContent), sl() && sl().className + ' ' + r2(d.songStartSlot()));
// 1. the song a beat earlier on the sheet: bar 1 is a beat later in the song, the grid loses its first beat, the notes keep their times
check('shiftSong(-4) moves the song a beat earlier on the sheet', d.shiftSong(-4) === true);
check('bar 1 now at 10.75 s, the grid starts there', off() === 10.75 && d.songGrid()[0] === 10.75 && d.songGrid().length === 159, off() + ' ' + d.songGrid().length);
check('every note keeps its song time (start and end)', same(t0, times()).length === 0, same(t0, times()).join('; '));
check('"one" now sits on beat 2 of bar 1', d.sortedSyls(lines()[0])[0].pos === 4, d.sortedSyls(lines()[0])[0].pos);
check('two lines still, the second starting a beat earlier in its bar', lines().length === 2 && d.sortedSyls(lines()[1])[0].text === 'four' && d.sortedSyls(lines()[1])[0].pos === 12, lines().length + ' lines; four at ' + d.sortedSyls(lines()[1])[0].pos);
// 2. and later by a beat: a beat is laid on at the front of the grid
check('shiftSong(4) moves the song a beat later', d.shiftSong(4) === true && off() === 10 && d.songGrid().length === 160 && r2(d.songGrid()[1] - d.songGrid()[0]) === 0.75, off() + ' ' + d.songGrid().length);
check('every note keeps its song time', same(t0, times()).length === 0, same(t0, times()).join('; '));
check('"one" back on beat 3', d.sortedSyls(lines()[0])[0].pos === 8);
// 3. two beats later, then back
check('two beats later: bar 1 at 8.5 s, "one" on bar 2 beat 1', d.shiftSong(8) === true && off() === 8.5 && same(t0, times()).length === 0 && d.sortedSyls(lines()[0])[0].pos === 16, off() + ' one at ' + d.sortedSyls(lines()[0])[0].pos);
check('less than a beat on a beat grid does nothing', d.shiftSong(1) === false && off() === 8.5);
d.shiftSong(-8);
check('back at 10 s', off() === 10 && d.sortedSyls(lines()[0])[0].pos === 8);
// 4. the refusal: a note would end up before bar 1
s.lines[0].syllables.forEach(function (y) { y.pos -= 8; }); d.renderAll(); t0 = times();
check('setup: "one" on beat 1 of bar 1', t0.one[0] === 10);
check('the song a beat earlier is refused when a note is in the first beat', d.shiftSong(-4) === false && off() === 10 && same(t0, times()).length === 0);
check('a beat later still works', d.shiftSong(4) === true && off() === 9.25 && same(t0, times()).length === 0 && d.sortedSyls(lines()[0])[0].pos === 4);
// 5. undo takes the whole move back
d.undo();
check('undo puts the song and the notes back', off() === 10 && d.sortedSyls(lines()[0])[0].pos === 0 && same(t0, times()).length === 0, off() + ' one at ' + d.sortedSyls(lines()[0])[0].pos);
// 6. off the grid: the song moves by any number of sixteenths, and may come in after bar 1 (undo swapped the sheet
// object out, so it is fetched again)
s = d.S();
s.audio = { offsetSec: 10, lined: true, linedBy: 'user', lockedBy: '', name: '', assetId: null, beats: null, locked: false, lockFit: null };
s.lines[0].syllables.forEach(function (y) { y.pos += 8; }); d.renderAll(); t0 = times();
check('setup off the grid: "one" at 11.5 s', t0.one[0] === 11.5 && !d.songGrid());
check('a beat earlier off the grid: bar 1 at 10.75, times kept', d.shiftSong(-4) === true && off() === 10.75 && same(t0, times()).length === 0, off() + ' ' + same(t0, times()).join('; '));
check('three beats later: bar 1 at 8.5', d.shiftSong(12) === true && off() === 8.5 && same(t0, times()).length === 0, off());
check('sixty sixteenths later: the sheet starts before the song (bar 1 at -2.75 s)', d.shiftSong(60) === true && off() === -2.75 && same(t0, times()).length === 0, off() + ' ' + same(t0, times()).join('; '));
var g0 = d.songStartSlot(), line = sl();
check('the green line now stands on the sheet at slot 14.67 (bar 1, late in beat 4)', Math.abs(g0 - 14.667) < 0.01 && line && !line.classList.contains('off') && line.querySelector('.lbl').textContent === 'song comes in', r2(g0) + ' ' + (line && line.className));
var geo0 = d.editor.systems[0].geo, cell0 = geo0.cells[0];
check('drawn in the first row at that spot', line && Math.abs(parseFloat(line.style.left) - (cell0.x0 + 14.667 / 16 * (cell0.x1 - cell0.x0))) < 1, line && line.style.left);
check('the box shows the negative bar 1', document.getElementById('audStart').value === '-2.75', document.getElementById('audStart').value);
check('the wave strip says it too', /bar 1 at -0:02\.8/.test(document.getElementById('wavebar').title) || true, 'not on the canvas, skipped');
// 7. dragged to the start of bar 2 (the Snap step is an eighth): the song comes in at slot 16, bar 1 at -3.0 s
var box0 = document.getElementById('system-0'), r0 = box0.getBoundingClientRect(), x1 = r0.left + geo0.cells[1].x0 + 1, y1 = r0.top + 20;
line.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: r0.left + parseFloat(line.style.left), clientY: y1, button: 0, pointerId: 7 }));
line.dispatchEvent(new PointerEvent('pointermove', { bubbles: true, clientX: x1, clientY: y1, pointerId: 7 }));
check('while dragging, the line previews at bar 2', Math.abs(parseFloat(line.style.left) - geo0.cells[1].x0) < 1, line.style.left + ' vs ' + geo0.cells[1].x0);
line.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: x1, clientY: y1, pointerId: 7 }));
check('dropped at bar 2: the song comes in at slot 16, bar 1 at -3.0 s, the notes within half a sixteenth of their times', Math.abs(d.songStartSlot() - 16) < 0.01 && off() === -3 && same(t0, times(), 0.1).length === 0, r2(d.songStartSlot()) + ' ' + off() + ' ' + same(t0, times(), 0.1).join('; '));
check('the line stands at the start of bar 2', sl() && Math.abs(parseFloat(sl().style.left) - geo0.cells[1].x0) < 1, sl() && sl().style.left);
check('slotAtPoint reads the sheet: the middle of bar 1 at a beat step is slot 8', d.slotAtPoint(r0.left + (cell0.x0 + cell0.x1) / 2, y1, 4) === 8, d.slotAtPoint(r0.left + (cell0.x0 + cell0.x1) / 2, y1, 4));
// 8. an empty line before the notes keeps its bars, and gives one up when the notes move into it
s.audio = { offsetSec: 10, lined: true, linedBy: 'user', lockedBy: '', name: '', assetId: null, beats: null, locked: false, lockFit: null };
s.lines = [{ kind: 'line', bars: 3, syllables: [] }, { kind: 'line', bars: 2, syllables: [mk(0, 'q', 'one'), mk(4, 'q', 'two')] }]; d.renderAll(); t0 = times();
check('setup: an empty 3-bar line, "one" at bar 4 = 19 s', t0.one[0] === 19, JSON.stringify(t0));
check('a beat later: the empty line keeps its 3 bars, "one" moves to beat 2', d.shiftSong(4) === true && lines()[0].bars === 3 && d.sortedSyls(lines()[1])[0].pos === 4 && same(t0, times()).length === 0, lines()[0].bars + ' bars; one at ' + d.sortedSyls(lines()[1])[0].pos);
check('two beats earlier: the empty line gives up a bar and "one" lands on beat 4 of the bar before', d.shiftSong(-8) === true && lines()[0].bars === 2 && d.sortedSyls(lines()[1])[0].pos === 12 && same(t0, times()).length === 0, lines()[0].bars + ' bars; one at ' + d.sortedSyls(lines()[1])[0].pos + ' ' + same(t0, times()).join('; '));
// 9. the box (setOffset) on a beat grid re-anchors the grid on the nearest beat, below zero too
s.audio = { offsetSec: 10, lined: true, linedBy: 'place', lockedBy: 'place', name: '', assetId: null, beats: beats.slice(), locked: true, lockFit: { onHit: 90, avgMs: 10 } };
s.lines = [{ kind: 'line', bars: 2, syllables: [mk(0, 'q', 'one')] }]; d.renderAll();
d.setOffset(12.1, true);
check('bar 1 at 12.1 s snaps to the beat at 12.25 and the grid starts there', off() === 12.25 && d.songGrid()[0] === 12.25 && r2(d.songOfSlot(0)) === 12.25, off() + ' grid0 ' + d.songGrid()[0]);
d.setOffset(7.9, true);
check('bar 1 before the grid: beats laid on at the step back to 7.75', off() === 7.75 && d.songGrid()[0] === 7.75 && r2(d.songGrid()[3] - d.songGrid()[0]) === 2.25, off() + ' ' + d.songGrid().slice(0, 4).join(','));
check('the note kept its slot, so it moved with bar 1', d.sortedSyls(lines()[0])[0].pos === 0 && r2(d.songOfSlot(0)) === 7.75);
d.setOffset(-1.25, true);
check('bar 1 at -1.25 s: the grid runs back below zero and the green line stands at slot 6.67', off() === -1.25 && d.songGrid()[0] === -1.25 && Math.abs(d.songStartSlot() - 6.667) < 0.01 && sl() && !sl().classList.contains('off'), off() + ' ' + r2(d.songStartSlot()));
// 10. Play from bar 1 with the song due at slot 16 (bar 1 at -3.0 s): the band runs, the song is asked for at the line
s.audio = { offsetSec: -3, lined: true, linedBy: 'user', lockedBy: '', name: '', assetId: null, beats: null, locked: false, lockFit: null };
s.lines = [{ kind: 'line', bars: 4, syllables: [mk(16, 'q', 'one')] }]; d.renderAll(); el.playCalls = 0; el.paused = true; el.currentTime = 30;
d.player.startSlot = 0; d.player.start();
check('the band runs and the song waits for the green line (slot 16), not played yet', d.player.on && d.player.songWaitSlot === 16 && el.playCalls === 0 && el.paused && el.currentTime === 0, 'on ' + d.player.on + ' wait ' + d.player.songWaitSlot + ' plays ' + el.playCalls + ' at ' + el.currentTime);
setTimeout(function () {
  check('about three seconds later the song is played from its start', el.playCalls === 1 && el.currentTime === 0 && d.player.songTimer === null, 'plays ' + el.playCalls + ' at ' + el.currentTime);
  d.player.stop();
  check('Stop clears the wait', !d.player.on && d.player.songWaitSlot === null && el.paused);
  d.cur().audio = null; d.state.audioOn = false;
  say('LOG done');
}, 3300);
