// A new pad key stops the last one at once (pagecheck-rt.py, TIMEOUT 8000): D4 struck at 0.05 s, A4 at 0.15 s; D4's
// own tone is measured before and after, over windows long enough to tell it from A4.
var d = window.__ds, p = d.player, out = document.getElementById('__out');
function say(t) { out.textContent += '\n' + t; }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var SR = 22050, off = new OfflineAudioContext(1, Math.round(SR * 0.3), SR), keep = { ac: p.ac, ng: p.noteGain, ens: p.ensureAudio, kv: p.keyVoice };
p.ac = off; p.noteGain = off.destination; p.ensureAudio = function () {}; p.keyVoice = null;
p.keyTone(62, 0.9, 0.04); p.keyTone(69, 0.9, 0.14);
off.startRendering().then(function (b) {
  var x = b.getChannelData(0);
  function amp(fq, a, e) { var c = 0, sn = 0, n = 0; for (var k = Math.floor(a * SR); k < Math.floor(e * SR); k++) { var ph = 2 * Math.PI * fq * k / SR; c += x[k] * Math.cos(ph); sn += x[k] * Math.sin(ph); n++; } return 2 * Math.sqrt(c * c + sn * sn) / n; }
  var dBefore = amp(293.66, 0.06, 0.14), dAfter = amp(293.66, 0.16, 0.26), aAfter = amp(440, 0.16, 0.26);
  check('D4 stops the moment A4 is pressed (under 3 % of itself 10 ms after)', dAfter < dBefore * 0.03, (dAfter / dBefore).toFixed(3));
  check('A4 sounds in its place', aAfter > dBefore * 0.3, (aAfter / dBefore).toFixed(2));
  var jump = 0; for (var k = Math.floor(0.148 * SR); k < Math.floor(0.158 * SR); k++) jump = Math.max(jump, Math.abs(x[k] - x[k - 1]));
  var typical = 0; for (k = Math.floor(0.08 * SR); k < Math.floor(0.12 * SR); k++) typical = Math.max(typical, Math.abs(x[k] - x[k - 1]));
  check('no click at the change (no sample-to-sample jump over twice the usual)', jump < typical * 2, (jump / typical).toFixed(2));
  p.ac = keep.ac; p.noteGain = keep.ng; p.ensureAudio = keep.ens; p.keyVoice = keep.kv;
  say('LOG done');
}, function (e) { say('FAIL render: ' + e); });
