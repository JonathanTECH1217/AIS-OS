// The drone's button, slider and pitch (pagecheck.py): the button turns it on and off and shows the volume slider; it
// sounds the key's home note low with its octave and fifth; the slider sets its level; a key or view change retunes it.
// Its sound is checked in drone-sound-test.js (rendered offline on the real clock).
var d = window.__ds, p = d.player, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var off = new OfflineAudioContext(1, 44100, 44100), keep = { ac: p.ac, ens: p.ensureAudio };
p.ac = off; p.ensureAudio = function () {};
s.key = { tonic: 'G', mode: 'major', laMinor: true }; s.view = 'vocals'; s.tuning = 440; d.state.prefs.droneVol = 40; d.renderAll();
var btn = document.getElementById('droneBtn'), vol = document.getElementById('droneVol');
check('off at first, no slider', !d.drone.on && vol.hidden && !btn.classList.contains('on'));
btn.click();
check('the button turns it on, lights up and shows the slider', d.drone.on && !vol.hidden && btn.classList.contains('on') && !!d.drone.nodes);
check('G major, Vocals: it sounds G3 (196 Hz), with its octave and fifth', d.droneMidi() === 55 && Math.abs(d.drone.nodes.oscs[0].o.frequency.value - 196) < 0.1 && Math.abs(d.drone.nodes.oscs[1].o.frequency.value - 392) < 0.2 && Math.abs(d.drone.nodes.oscs[2].o.frequency.value - 294) < 0.2, d.drone.nodes.oscs.map(function (x) { return x.o.frequency.value.toFixed(1); }).join(' '));
check('the level at 40 on the slider', Math.abs(d.droneLevel() - 0.048) < 0.001, d.droneLevel());
vol.value = 80; vol.dispatchEvent(new Event('input', { bubbles: true }));
check('the slider at 80 raises it and is kept', d.state.prefs.droneVol === 80 && Math.abs(d.droneLevel() - 0.192) < 0.001);
vol.value = 40; vol.dispatchEvent(new Event('input', { bubbles: true }));
s.key = { tonic: 'A', mode: 'minor', laMinor: true }; s.view = 'guitar'; d.renderAll();
check('a key change (A minor, Guitar view) moves it to A3', d.droneMidi() === 57 && d.drone.nodes.midi === 57, d.droneMidi());
s.view = 'vocals'; d.renderAll();
check('back in Vocals (A minor, la-based) it sits on do = C3', d.droneMidi() === 48 && d.drone.nodes.midi === 48, d.droneMidi());
btn.click();
check('the button again turns it off and hides the slider', !d.drone.on && vol.hidden && !d.drone.nodes);
s.key = { tonic: 'C', mode: 'major', laMinor: true }; d.renderAll();
p.ac = keep.ac; p.ensureAudio = keep.ens;
say('LOG done');
