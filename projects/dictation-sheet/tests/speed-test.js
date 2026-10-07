// No slowdown: the Shift+5 / Shift+7 keys do nothing to the speed, Play always runs at 100 %, no percent badge, and an
// attached file plays at its own speed; even a speed left over in the saved state is ignored.
var d = window.__ds, s = d.S(), p = d.player;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: 'q' }] }] }).lines[0].syllables[0]; }
function key(k) { document.getElementById('work').dispatchEvent(new KeyboardEvent('keydown', { key: k, shiftKey: true, bubbles: true, cancelable: true })); }
var el = { paused: true, currentTime: 0, duration: 60, playbackRate: 1, pause: function () { this.paused = true; }, play: function () { this.paused = false; return Promise.resolve(); } };
s.time = '4/4'; s.bpm = 100; s.lines = [{ kind: 'line', bars: 2, syllables: [mk(0, 'a'), mk(4, 'b')] }];
s.audio = { offsetSec: 0, lined: true, linedBy: 'user', lockedBy: '', name: '', assetId: null, beats: null, locked: false, lockFit: null };
d.cur().audio = { el: el, url: '', name: 'song.wav', peaks: null, duration: 60, onset: null, voice: null, low: null, blob: false }; d.state.audioOn = true; d.renderAll();
document.getElementById('work').focus(); key('%'); key('&');
check('Shift+5 and Shift+7 leave the speed alone', (d.state.speed || 100) === 100, d.state.speed);
d.state.speed = 50; d.state.prac.on = true; // as if left over from before
p.startSlot = 0; p.start();
check('Play runs at 100 % whatever was left over', p.pct === 100 && el.playbackRate === 1, 'pct ' + p.pct + ' rate ' + el.playbackRate);
check('no percent badge on the tempo button', document.getElementById('speedFace').hidden === true);
p.stop(); d.cur().audio = null; d.state.audioOn = false;
say('LOG done');
