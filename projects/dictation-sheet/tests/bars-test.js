// Bars from the song: the sheet's bars from the song's length, bar 1, the tempo and the time signature, kept right as
// those change; the empty sheet's Start a line takes them; a new line takes the empty tail.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function lines() { return d.S().lines.filter(function (l) { return l.kind === 'line'; }); }
function total() { var spb = d.slotsPerBar(d.S().time), n = 0; lines().forEach(function (l) { n += d.lineBars(l, spb); }); return n; }
s.time = '4/4'; s.bpm = 120; s.view = 'vocals'; s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null; s.spotify = null; d.cur().undo = [];
s.audio = { offsetSec: 0, lined: false, linedBy: '', lockedBy: '', name: '', assetId: null, beats: null, locked: false, lockFit: null };
d.cur().audio = { el: { paused: true, currentTime: 30, duration: 60, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'test.wav', peaks: null, duration: 60, onset: null, voice: null, low: null, blob: false };
d.state.audioOn = true; d.renderAll();
// 1. 60 s song, bar 1 at 0, 120 bpm 4/4: a bar is 2 s -> 30 bars
check('barsFromSong: 60 s at 120 bpm in 4/4 from 0 s is 30 bars', d.barsFromSong() === 30, d.barsFromSong());
check('the Play panel says so', document.getElementById('audInfo').textContent.indexOf('30 bars') > 0, document.getElementById('audInfo').textContent);
// 2. Start a line takes them
document.querySelector('#sheet .empty button').click();
check('Start a line makes a line of 30 bars', lines().length === 1 && lines()[0].bars === 30, lines()[0] && lines()[0].bars);
// 3. bar 1 at 4 s: 56 s left -> 28 bars
d.setOffset(4, true);
check('bar 1 at 4 s: 28 bars', total() === 28 && d.sheetAudio().offsetSec === 4, total());
// 4. tempo 60: a bar is 4 s -> 14 bars
d.setBpm(60);
check('tempo 60: 14 bars', total() === 14, total());
// 5. time 3/4 at 60: a bar is 3 s -> 56/3 = 18.67 -> 19 bars
d.applyTime('3/4');
check('3/4: 19 bars', total() === 19, total());
d.applyTime('4/4'); d.setBpm(120);
check('back to 4/4 at 120: 28 bars', total() === 28, total());
// 6. notes on the line, then a new line: the empty tail moves to the new line
var l0 = lines()[0]; l0.syllables.push(d.normalize({ lines: [{ kind: 'line', syllables: [{ text: 'one', pos: 0 }, { text: 'two', pos: 20 }] }] }).lines[0].syllables[1]); l0.syllables[0].text = 'two'; l0.syllables[0].pos = 20; d.renderAll();
var nl = null; document.querySelectorAll('.cellbtn').forEach(function (b) { if (b.textContent === '↵') nl = b; });
nl.click();
check('a new line takes the empty bars after the last note: 2 + 26', lines().length === 2 && lines()[0].bars === 2 && lines()[1].bars === 26, lines().map(function (l) { return l.bars; }).join('+'));
check('the whole sheet still reaches the end of the song', total() === 28, total());
// 7. the last line never loses the bars its notes need
lines()[1].syllables.push(d.normalize({ lines: [{ kind: 'line', syllables: [{ text: 'far', pos: 25 * 16 + 4 }] }] }).lines[0].syllables[0]);
d.setBpm(240);
check('at 240 bpm the song needs 56 bars but line 2 keeps the 26 its note needs', lines()[1].bars >= 26 && total() >= 28, lines().map(function (l) { return l.bars; }).join('+'));
d.setBpm(120);
// 8. with a beat grid the bars follow it
d.sheetAudio().beats = []; for (var i = 0; i < 100; i++) d.sheetAudio().beats.push(4 + i * 0.6); d.sheetAudio().locked = true; d.sheetAudio().lockedBy = 'place';
check('on a beat grid of 0.6 s beats from 4 s: 56 s / 2.4 s = 23.3 -> 24 bars', d.barsFromSong() === 24, d.barsFromSong());
d.sheetAudio().locked = false; d.sheetAudio().beats = null;
// 9. the Now button and the box
d.cur().audio.el.currentTime = 12; d.state.audioOn = true; document.getElementById('audMark').click();
check('Now puts bar 1 where the song is (12 s) and the bars follow (24)', d.sheetAudio().offsetSec === 12 && total() >= 24, 'offset ' + d.sheetAudio().offsetSec + ' bars ' + total());
check('the box shows it', document.getElementById('audStart').value === '12.00', document.getElementById('audStart').value);
// 10. no song: nothing happens
d.cur().audio = null; d.state.audioOn = false;
check('with no song barsFromSong is 0', d.barsFromSong() === 0, d.barsFromSong());
say('LOG done');
