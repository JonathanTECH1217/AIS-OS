// Notes only: one press makes the sheet play its notes and keeps the song silent (Notes on, Audio off); pressed
// again the song plays with the band again; while the band runs it pauses the song; with no song it turns the notes on.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
var b = document.getElementById('notesOnly'), notesBtn = document.getElementById('notesBtn'), audioBtn = document.getElementById('audioBtn');
var el = { paused: true, currentTime: 0, duration: 60, playbackRate: 1, playCalls: 0, pause: function () { this.paused = true; }, play: function () { this.playCalls++; this.paused = false; return Promise.resolve(); } };
s.time = '4/4'; s.bpm = 100; s.view = 'vocals'; s.spotify = null; s.filled = null; s.lines = [{ kind: 'line', bars: 4, syllables: [mk(0, 'q', 'one'), mk(4, 'q', 'two')] }];
s.audio = { offsetSec: 0, lined: true, linedBy: 'user', lockedBy: '', name: '', assetId: null, beats: null, locked: false, lockFit: null };
d.cur().audio = { el: el, url: '', name: 'song.wav', peaks: null, duration: 60, onset: null, voice: null, low: null, blob: false };
d.state.audioOn = true; d.state.notes = false; d.renderAll();
check('song on and notes off at first: the button is dark', !b.classList.contains('on') && audioBtn.classList.contains('on') && !notesBtn.classList.contains('on'));
b.click();
check('Notes only: the notes on, the song off, the button lit, the top-row buttons agree', d.state.notes === true && d.state.audioOn === false && b.classList.contains('on') && notesBtn.classList.contains('on') && !audioBtn.classList.contains('on'));
b.click();
check('pressed again: the song plays again and the notes stay on', d.state.notes === true && d.state.audioOn === true && !b.classList.contains('on') && audioBtn.classList.contains('on'));
// while the band runs with the file: Notes only pauses the song, the band runs on
d.player.startSlot = 0; d.player.start();
check('Play starts the song', d.player.on && el.playCalls === 1 && !el.paused, 'on ' + d.player.on + ' plays ' + el.playCalls);
b.click();
check('Notes only while playing pauses the song and the band runs on', el.paused && d.player.on && d.state.audioOn === false && d.state.notes === true && b.classList.contains('on'));
d.player.stop();
// no song linked: Notes only turns the notes on and says the sheet plays alone anyway
d.cur().audio = null; d.state.audioOn = false; d.state.notes = false; d.renderAll();
b.click();
check('with no song it turns the notes on and lights', d.state.notes === true && b.classList.contains('on'));
b.click();
check('with no song a second press keeps the notes on (nothing to bring back)', d.state.notes === true && b.classList.contains('on'));
d.state.notes = false; d.renderAll();
say('LOG done');
