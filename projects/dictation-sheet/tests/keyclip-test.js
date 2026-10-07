// No crackle from the pad (pagecheck-rt.py, TIMEOUT 8000): Q to P pressed fast (every 40 ms) at full Notes volume,
// with the drone on and the sheet's notes sounding, all through the app's limiter, rendered offline: nothing near full
// scale, and the keys do not pile up.
var d = window.__ds, p = d.player, s = d.S(), out = document.getElementById('__out');
function say(t) { out.textContent += '\n' + t; }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var SR = 22050, off = new OfflineAudioContext(1, Math.round(SR * 0.6), SR), keep = { ac: p.ac, ng: p.noteGain, bus: p.bus, ens: p.ensureAudio, kv: p.keyVoice };
p.ac = off; p.ensureAudio = function () {}; p.bus = d.makeBus(off); p.noteGain = off.createGain(); p.noteGain.gain.value = 1; p.noteGain.connect(p.bus); p.keyVoice = null;
s.key = { tonic: 'C', mode: 'major', laMinor: true }; s.view = 'vocals'; d.state.prefs.droneVol = 100;
d.drone.on = true; d.droneSync();
var ms = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76];
ms.forEach(function (m, i) { p.keyTone(m, 0.9, 0.05 + i * 0.04); });
p.slotSec = 0.1; p.tone(0.05, { midi: 67, len: 8 }); p.tone(0.3, { midi: 64, len: 2 });
off.startRendering().then(function (buf) {
  var x = buf.getChannelData(0), peak = 0, hot = 0, i;
  for (i = 0; i < x.length; i++) { var a = Math.abs(x[i]); if (a > peak) peak = a; if (a > 0.98) hot++; }
  check('the loudest moment stays under full scale (under 0.9)', peak < 0.9, 'peak ' + peak.toFixed(3));
  check('no sample at full scale', hot === 0, hot + ' samples');
  // the pile-up: after the tenth key the level is about that of one key plus the drone and the note, not ten keys
  function rms(a, b) { var q = 0, n = 0; for (var k = Math.floor(a * SR); k < Math.floor(b * SR); k++) { q += x[k] * x[k]; n++; } return Math.sqrt(q / n); }
  check('the keys do not pile up: the level near the end is under twice the level at the first key', rms(0.47, 0.55) < rms(0.07, 0.085) * 2, (rms(0.47, 0.55) / rms(0.07, 0.085)).toFixed(2));
  function amp(fq, a, b) { var c = 0, sn = 0, n = 0; for (var k = Math.floor(a * SR); k < Math.floor(b * SR); k++) { var ph = 2 * Math.PI * fq * k / SR; c += x[k] * Math.cos(ph); sn += x[k] * Math.sin(ph); n++; } return 2 * Math.sqrt(c * c + sn * sn) / n; }
  d.drone.on = false; d.drone.nodes = null;
  p.ac = keep.ac; p.noteGain = keep.ng; p.bus = keep.bus; p.ensureAudio = keep.ens; p.keyVoice = keep.kv;
  say('LOG done');
}, function (e) { say('FAIL render: ' + e); });
