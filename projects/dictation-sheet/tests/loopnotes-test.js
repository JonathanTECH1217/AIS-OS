// The notes at the start of a loop sound on every round, on time, even when the page's frames come late: a fake audio
// clock drives the player; the scheduler runs every 25 ms, a frame only every 70 ms (a busy page).
var d = window.__ds, s = d.S(), p = d.player;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, len, text, note) { var y = d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; y.note = note; y.oct = 4; y.noteAuto = false; return y; }
s.time = '4/4'; s.bpm = 60; s.view = 'vocals'; d.cur().audio = null; d.state.audioOn = false; d.state.notes = true; d.state.metro = false; d.cur().sel = null; d.state.prefs.countIn = false;
// a sixteenth is 0.25 s at 60 bpm; notes at slots 0, 1, 2 (right at the loop start), 4 and 8; the loop runs 0 to 12
s.lines = [{ kind: 'line', bars: 2, syllables: [mk(0, '16', 'a', 'C'), mk(1, '16', 'b', 'D'), mk(2, '8', 'c', 'E'), mk(4, 'q', 'd', 'F'), mk(8, 'q', 'e', 'G')] }];
d.renderAll(); d.cur().loop = d.makeLoop(0, 12); d.cur().loopOn = true; d.applyLoop();
var clock = { currentTime: 100, state: 'running', resume: function () {} }, sent = [];
p.ac = clock; p.metroGain = {}; p.noteGain = {};
p.tone = function (t, n) { sent.push({ t: Math.round((t - 100) * 1000) / 1000, slot: n.slot }); };
p.click = function () {};
p.startSlot = 0; p.start();
clearInterval(p.timer); cancelAnimationFrame(p.raf);
var nextFrame = 100;
for (var t = 100; t <= 100 + 3 * 3 + 0.5; t = Math.round((t + 0.025) * 1000) / 1000) {
  clock.currentTime = t; p.schedule();
  if (t >= nextFrame) { p.frame(); cancelAnimationFrame(p.raf); nextFrame = t + 0.07; }
}
p.stop();
// three rounds of 3 s: the notes at slots 0, 1, 2, 4, 8 at 0, .25, .5, 1, 2 s into each round
var want = []; [0, 1, 2].forEach(function (r) { [0, 1, 2, 4, 8].forEach(function (sl) { want.push(r * 3 + sl * 0.25); }); });
var got = sent.map(function (x) { return x.t; });
var missing = want.filter(function (w) { return !got.some(function (g) { return Math.abs(g - w) < 0.03; }); });
var twice = want.filter(function (w) { return got.filter(function (g) { return Math.abs(g - w) < 0.03; }).length > 1; });
var worst = 0; want.forEach(function (w) { var near = got.filter(function (g) { return Math.abs(g - w) < 0.03; })[0]; if (near !== undefined) worst = Math.max(worst, Math.abs(near - w)); });
check('every note of three rounds sounds, the loop-start notes included (15 notes)', missing.length === 0, 'missing at ' + missing.join(', ') + ' | sent ' + got.join(', '));
check('none sounds twice', twice.length === 0, twice.join(', '));
check('each sounds on time (within 5 ms)', worst <= 0.005, 'worst ' + Math.round(worst * 1000) + ' ms');
check('nothing extra is sent in the three rounds', sent.filter(function (x) { return x.t < 9 - 0.001; }).length === 15, sent.length + ' sent');
// With Spotify: the song is asked to jump back to the loop start its measured delay (here 0.3 s) before the loop ends, the band does not stop to wait at the loop start, and the loop-start notes still sound on time
var sp = d.sp; sp.startLat = 0.3; sent = []; clock.currentTime = 200;
p.startSlot = 0; p.start(); clearInterval(p.timer); cancelAnimationFrame(p.raf);
p.spot = true; p.hold = false; p.needSnap = false;
var asked = null, seek0 = sp.seekAt; nextFrame = 200;
for (t = 200; t <= 200 + 2 * 3 - 0.05; t = Math.round((t + 0.025) * 1000) / 1000) {
  clock.currentTime = t; p.schedule();
  if (asked === null && sp.seekAt !== seek0 && sp.seekPos === 0) asked = t;
  if (t >= nextFrame) { p.frame(); cancelAnimationFrame(p.raf); nextFrame = t + 0.07; }
}
var holdAfter = p.hold; p.spot = false; p.stop();
var gotS = sent.map(function (x) { return Math.round((x.t - 100) * 1000) / 1000; });
check('Spotify is asked for the loop start about 0.3 s before the loop ends (at 3 s)', asked !== null && Math.abs((asked - 200) - 2.7) < 0.03, asked === null ? 'never asked' : 'asked at ' + Math.round((asked - 200) * 1000) / 1000 + ' s');
check('the band does not stop to wait for the song at the loop start', holdAfter === false);
check('the second round\'s loop-start notes sound on time (3, 3.25, 3.5 s)', [3, 3.25, 3.5].every(function (w) { return gotS.some(function (g) { return Math.abs(g - w) < 0.006; }); }), gotS.join(', '));
say('LOG done');
