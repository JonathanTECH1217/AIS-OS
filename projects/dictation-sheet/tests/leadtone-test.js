// The playback voice is the note pad's keyboard (pagecheck-rt.py, TIMEOUT 8000): a sheet note rendered offline next to a
// pad key of the same pitch and length sounds the same (same level, same ring), a clean start and end; the tap on a
// word goes through it too.
var d = window.__ds, p = d.player, out = document.getElementById('__out');
function say(t) { out.textContent += '\n' + t; }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var SR = 22050, off = new OfflineAudioContext(2, Math.round(SR * 0.8), SR), keep = { ac: p.ac, ng: p.noteGain, ss: p.slotSec, ens: p.ensureAudio, kv: p.keyVoice };
// left channel: the sheet's note (A4, 4 slots of 0.1 s = 0.38 s); right channel: a pad key, A4, held 0.38 s
var merge = off.createChannelMerger(2); merge.connect(off.destination);
var left = off.createGain(), right = off.createGain(); left.connect(merge, 0, 0); right.connect(merge, 0, 1);
p.ac = off; p.ensureAudio = function () {}; p.slotSec = 0.1; p.keyVoice = null;
p.noteGain = left; p.tone(0.05, { midi: 69, len: 4 });
p.noteGain = right; p.keyTone(69, 0.38, 0.05);
p.ac = keep.ac; p.noteGain = keep.ng; p.slotSec = keep.ss; p.ensureAudio = keep.ens; p.keyVoice = keep.kv;
off.startRendering().then(function (buf) {
  var a = buf.getChannelData(0), b = buf.getChannelData(1), i, diff = 0, peakA = 0, peakB = 0;
  for (i = 0; i < a.length; i++) { diff = Math.max(diff, Math.abs(a[i] - b[i])); peakA = Math.max(peakA, Math.abs(a[i])); peakB = Math.max(peakB, Math.abs(b[i])); }
  check('the sheet\'s note and the pad\'s key are the same sound (sample for sample within 1 % of the peak)', diff < peakA * 0.01 && peakA > 0.05, 'largest difference ' + (diff / peakA).toFixed(4) + ' of the peak ' + peakA.toFixed(3));
  function rms(x, s0, s1) { var q = 0, n = 0; for (var k = Math.floor(s0 * SR); k < Math.floor(s1 * SR); k++) { q += x[k] * x[k]; n++; } return Math.sqrt(q / n); }
  check('it rings like a struck key while held and ends clean (silent 0.3 s after its length)', rms(a, 0.3, 0.4) < rms(a, 0.06, 0.12) && rms(a, 0.7, 0.78) < rms(a, 0.06, 0.12) * 0.01, [rms(a, 0.06, 0.12), rms(a, 0.3, 0.4), rms(a, 0.7, 0.78)].map(function (v) { return v.toFixed(4); }).join(' / '));
  check('the tap on a word goes through the same voice', /this\.tone\(/.test(String(p.playTone)) && /keyVoiceAt/.test(String(p.tone)));
  say('LOG done');
}, function (e) { say('FAIL render: ' + e); });
