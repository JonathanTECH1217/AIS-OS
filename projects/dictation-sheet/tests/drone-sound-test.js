// The drone's sound, rendered offline (pagecheck-rt.py, TIMEOUT 8000; kept short so the render ends before the page
// is saved): a soft steady level, the home note strongest, nothing up high.
var d = window.__ds, p = d.player, s = d.S(), out = document.getElementById('__out');
function say(t) { out.textContent += '\n' + t; }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var SR = 44100, off = new OfflineAudioContext(1, SR, SR);
p.ac = off; p.ensureAudio = function () {};
s.key = { tonic: 'G', mode: 'major', laMinor: true }; s.view = 'vocals'; s.tuning = 440; d.state.prefs.droneVol = 60;
d.drone.on = true; d.droneSync();
off.startRendering().then(function (buf) {
  var x = buf.getChannelData(0), peak = 0, i; for (i = 0; i < x.length; i++) peak = Math.max(peak, Math.abs(x[i]));
  function amp(fq) { var c = 0, sn = 0, n = 0; for (var k = Math.floor(0.5 * SR); k < Math.floor(0.95 * SR); k++) { var ph = 2 * Math.PI * fq * k / SR; c += x[k] * Math.cos(ph); sn += x[k] * Math.sin(ph); n++; } return 2 * Math.sqrt(c * c + sn * sn) / n; }
  function rms(a, b) { var q = 0, n = 0; for (var k = Math.floor(a * SR); k < Math.floor(b * SR); k++) { q += x[k] * x[k]; n++; } return Math.sqrt(q / n); }
  var root = amp(196), oct = amp(392), fifth = amp(294), hi = amp(2000);
  check('a soft level, peak under 0.25', peak > 0.02 && peak < 0.25, 'peak ' + peak.toFixed(3));
  check('it eases in (the first 20 ms well under the level after)', rms(0, 0.02) < rms(0.6, 0.7) * 0.3, (rms(0, 0.02) / rms(0.6, 0.7)).toFixed(2));
  check('steady once in (0.5 s and 0.9 s within 5 %)', Math.abs(rms(0.5, 0.55) / rms(0.9, 0.95) - 1) < 0.05, (rms(0.5, 0.55) / rms(0.9, 0.95)).toFixed(3));
  check('G3 strongest, its octave and fifth softer, nothing up high', root > oct && root > fifth && hi < root * 0.01, [root, oct, fifth, hi].map(function (v) { return v.toFixed(4); }).join(' / '));
  say('LOG done');
}, function (e) { say('FAIL render: ' + e); });
