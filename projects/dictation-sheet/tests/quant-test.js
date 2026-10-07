// runs inside the staged page 1.5 s after boot: checks quantizeSpans on a made-up sheet and voiceOf on a synthetic signal
var d = window.__ds, s = d.S();
function eq(name, got, want) { var g = JSON.stringify(got), w = JSON.stringify(want); console.log((g === w ? 'PASS ' : 'FAIL ') + name + ': ' + g + (g === w ? '' : ' (want ' + w + ')')); }
s.bpm = 120; s.time = '4/4';
s.audio = { offsetSec: 10, lined: true, name: '', assetId: null, forTrack: null, beats: null, locked: false, lockFit: null };
var y = function (hy) { return { hy: !!hy }; };
// slots are 0.125 s: Si on 10.0 off 10.3 (hy), lent on 10.375 off 10.63, night on 10.82 off 11.23, peace on 11.57 off 12.35
var spans = [{ y: y(true), on: 10.0, off: 10.3 }, { y: y(false), on: 10.375, off: 10.63 }, { y: y(false), on: 10.82, off: 11.23 }, { y: y(false), on: 11.57, off: 12.35 }];
eq('last line, hy fill, rests kept', d.quantizeSpans(spans, null, 0), [{ slot: 0, lenSlots: 3 }, { slot: 3, lenSlots: 2 }, { slot: 7, lenSlots: 3 }, { slot: 13, lenSlots: 6 }]);
eq('next line onset caps the last word', d.quantizeSpans(spans, 12.0, 0), [{ slot: 0, lenSlots: 3 }, { slot: 3, lenSlots: 2 }, { slot: 7, lenSlots: 3 }, { slot: 13, lenSlots: 3 }]);
eq('floorSlot pushes the line', d.quantizeSpans(spans, null, 2), [{ slot: 2, lenSlots: 1 }, { slot: 3, lenSlots: 2 }, { slot: 7, lenSlots: 3 }, { slot: 13, lenSlots: 6 }]);
eq('unknown release holds to the next onset', d.quantizeSpans([{ y: y(false), on: 10.0, off: null }, { y: y(false), on: 10.5, off: 10.6 }], null, 0), [{ slot: 0, lenSlots: 4 }, { slot: 4, lenSlots: 1 }]);
eq('legato under 60 ms fills a one-slot gap', d.quantizeSpans([{ y: y(false), on: 10.0, off: 10.22 }, { y: y(false), on: 10.27, off: 10.6 }], null, 0), [{ slot: 0, lenSlots: 2 }, { slot: 2, lenSlots: 3 }]);
eq('two-slot gap stays a rest', d.quantizeSpans([{ y: y(false), on: 10.0, off: 10.25 }, { y: y(false), on: 10.5, off: 10.75 }], null, 0), [{ slot: 0, lenSlots: 2 }, { slot: 4, lenSlots: 2 }]);
eq('MAX_SLOTS caps a very long hold', d.quantizeSpans([{ y: y(false), on: 10.0, off: 40.0 }], null, 0), [{ slot: 0, lenSlots: d.MAX_SLOTS }]);
eq('collision pushes forward by one', d.quantizeSpans([{ y: y(false), on: 10.0, off: 10.05 }, { y: y(false), on: 10.03, off: 10.3 }], null, 0), [{ slot: 0, lenSlots: 1 }, { slot: 1, lenSlots: 1 }]);
eq('before bar 1 clamps to slot 0', d.quantizeSpans([{ y: y(false), on: 9.0, off: 9.2 }, { y: y(false), on: 9.5, off: 10.2 }], null, 0), [{ slot: 0, lenSlots: 1 }, { slot: 1, lenSlots: 1 }]);
// voiceOf: 3 s mono at 48 kHz, a 60 Hz hum throughout (out of band) and a 1 kHz tone from 1.0 to 2.0 s (in band)
try {
  var sr = 48000, n = sr * 3, oc = new OfflineAudioContext(1, n, sr), buf = oc.createBuffer(1, n, sr), ch = buf.getChannelData(0), i;
  for (i = 0; i < n; i++) { var t = i / sr; ch[i] = 0.02 * Math.sin(2 * Math.PI * 60 * t) + (t >= 1 && t < 2 ? 0.3 * Math.sin(2 * Math.PI * 1000 * t) : 0); }
  d.voiceOf(buf).then(function (env) {
    var out = document.getElementById('__out');
    if (!env) { out.textContent += '\nFAIL voiceOf returned null'; return; }
    var q = [env[50], env[150], env[250]].map(function (v) { return Math.round(v * 100) / 100; });
    var ok = env.length === 300 && q[0] < 0.3 && q[1] > 1.5 && q[2] < 0.3;
    out.textContent += '\n' + (ok ? 'PASS' : 'FAIL') + ' voiceOf: length ' + env.length + ' hum-only ' + q[0] + ' tone ' + q[1] + ' hum-only ' + q[2];
  });
} catch (e) { console.log('FAIL voiceOf threw ' + (e && e.message)); }
