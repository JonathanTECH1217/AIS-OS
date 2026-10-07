// Spotify's delay measured from its readings, the loop's early ask using it, and the band starting right after Play
// instead of waiting for a reading.
var d = window.__ds, sp = d.sp, p = d.player, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function r3(x) { return Math.round(x * 1000) / 1000; }
// 1. the measurement: asked at T for 10 000 ms; a reading taken at T + 700 ms says 10 450 ms -> it restarted at T + 250
sp.startLat = null; d.spNoteAsk(10000); var T = sp.latFrom.at;
var lat = d.spMeasureLat(T + 700, 10450);
check('a reading 700 ms after the ask saying 450 ms in means a 0.25 s delay', r3(lat) === 0.25 && r3(sp.startLat) === 0.25, lat);
check('the ask is used once', d.spMeasureLat(T + 900, 10650) === null);
d.spNoteAsk(0); d.spMeasureLat(sp.latFrom.at + 500, 350);
check('a second one (0.15 s) is blended in: 0.6 x 0.25 + 0.4 x 0.15 = 0.21', r3(sp.startLat) === 0.21, sp.startLat);
check('the lead is that delay', r3(d.spLead()) === 0.21);
d.spNoteAsk(0); d.spMeasureLat(sp.latFrom.at + 100, 5000);
check('a reading that makes no sense (the song far ahead) is thrown away', r3(sp.startLat) === 0.21, sp.startLat);
sp.startLat = null;
check('with nothing measured yet the lead is 0.25 s, never the old half-second-plus guess', d.spLead() === 0.25);
// 2. the band waiting for Spotify after Play starts once the delay has passed, not when a reading comes
function mk(pos, len, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: len }] }] }).lines[0].syllables[0]; }
s.time = '4/4'; s.bpm = 60; d.cur().audio = null; d.state.audioOn = false; d.cur().loop = null;
s.lines = [{ kind: 'line', bars: 2, syllables: [mk(0, 'q', 'a'), mk(4, 'q', 'b')] }]; d.renderAll();
var clock = { currentTime: 50, state: 'running', resume: function () {} }; p.ac = clock; p.metroGain = {}; p.noteGain = {}; p.tone = function () {}; p.click = function () {};
p.startSlot = 0; p.start(); clearInterval(p.timer); cancelAnimationFrame(p.raf);
p.spot = true; p.hold = true; p.holdAt = 50; sp.startLat = 0.2;
sp.latFrom = { at: performance.now() - 100, pos: 0 }; // asked 0.1 s ago: not yet
clock.currentTime = 50.1; p.frame(); cancelAnimationFrame(p.raf);
check('0.1 s after the ask (delay 0.2 s) the band still waits', p.hold === true);
sp.latFrom = { at: performance.now() - 250, pos: 0 }; // asked 0.25 s ago: the song is sounding
clock.currentTime = 50.25; p.frame(); cancelAnimationFrame(p.raf);
clock.currentTime = 50.75; p.frame(); cancelAnimationFrame(p.raf);
check('once the delay has passed the band runs from when the song started (0.05 s before that frame), with no reading from Spotify', p.hold === false && Math.abs(p.position() - 2.2) < 0.05, 'hold ' + p.hold + ' at slot ' + p.position().toFixed(2));
p.spot = false; p.stop(); sp.latFrom = null; sp.startLat = null;
say('LOG done');
