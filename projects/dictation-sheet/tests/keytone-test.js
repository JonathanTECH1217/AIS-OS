// The note pad's keyboard voice, rendered offline (run with pagecheck-rt.py, TIMEOUT 8000): a clean level, no click at
// the start, a natural decay, a smooth end after the key is let go, most of the sound in the note itself, little up high.
var d = window.__ds, p = d.player, out = document.getElementById('__out');
function say(t) { out.textContent += '\n' + t; }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var SR = 44100, off = new OfflineAudioContext(1, SR * 2.5, SR), keep = { ac: p.ac, ng: p.noteGain, ens: p.ensureAudio };
p.ac = off; p.noteGain = off.destination; p.ensureAudio = function () {};
p.keyTone(69, 0.9, 0.1); // A4 at 440 Hz, struck at 0.1 s, let go at 1.0 s
p.ac = keep.ac; p.noteGain = keep.ng; p.ensureAudio = keep.ens;
off.startRendering().then(function (buf) {
  var x = buf.getChannelData(0), peak = 0, i;
  for (i = 0; i < x.length; i++) peak = Math.max(peak, Math.abs(x[i]));
  function rms(a, b) { var s = 0, n = 0; for (var k = Math.floor(a * SR); k < Math.floor(b * SR); k++) { s += x[k] * x[k]; n++; } return Math.sqrt(s / Math.max(1, n)); }
  check('a clean level: peak between 0.1 and 0.6, never clipping', peak > 0.1 && peak < 0.6, 'peak ' + peak.toFixed(3));
  check('silent before the strike', rms(0, 0.095) < 1e-4);
  // the first 2 ms after the strike stay well under the peak: a soft attack, no click
  var early = 0; for (i = Math.floor(0.1 * SR); i < Math.floor(0.1015 * SR); i++) early = Math.max(early, Math.abs(x[i]));
  check('no click: the first 1.5 ms stay under half the peak', early < peak * 0.5, (early / peak).toFixed(2) + ' of the peak');
  var a = rms(0.12, 0.2), b = rms(0.6, 0.7);
  check('it decays like a struck key while held (0.6 s in, under 70 % of the start)', b < a * 0.7 && b > a * 0.05, (b / a).toFixed(2));
  check('it fades out after the key is let go, silent by 0.6 s after', rms(1.6, 1.7) < a * 0.01, (rms(1.6, 1.7) / a).toFixed(4));
  // the note itself carries most of the sound: correlate with 440 Hz against 880 Hz and 1760 Hz over the first 0.3 s
  function amp(fq) { var c = 0, s = 0, n = 0; for (var k = Math.floor(0.12 * SR); k < Math.floor(0.42 * SR); k++) { var ph = 2 * Math.PI * fq * k / SR; c += x[k] * Math.cos(ph); s += x[k] * Math.sin(ph); n++; } return 2 * Math.sqrt(c * c + s * s) / n; }
  var f1 = amp(440), f2 = amp(880), f4 = amp(1760), hi = amp(5000);
  check('the note (440 Hz) is the strongest part, its octave softer, the double octave softer still', f1 > f2 && f2 > f4, [f1, f2, f4].map(function (v) { return v.toFixed(3); }).join(' / '));
  check('little up high (5 kHz under 1 % of the note)', hi < f1 * 0.01, (hi / f1).toFixed(4));
  say('LOG done');
}, function (e) { say('FAIL render: ' + e); });
