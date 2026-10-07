// voice-band.js (body; voice-extract.py glues voiceIR/lowIR/bandOf/voiceOf/lowOf in front -> voice-band.full.js)
// runjs.py dumps the DOM right after load, and a render needs the main thread free, so the load event is held back by an
// image that slowserver.py (port 8799) answers after WAIT ms; every render is started at once and reports as it finishes.
// Tones at 60, 300, 1000, 1500, 2000, 3000, 5000 Hz in 1.5 s slots from 1.0, 3.0, ... 13.0 s of a 15 s buffer, at 44.1k and 48k,
// through voiceOf and lowOf: gain per tone (dB re the input RMS), the frame the 300 Hz (3.000 s) and 60 Hz (1.000 s) tones show at,
// the frame count, and stereo averaging.
var WAIT = 12000;
var hold = new Image(); hold.src = 'http://127.0.0.1:8799/slow?ms=' + WAIT; document.body.appendChild(hold);
function say(t) { __lines.push('LOG ' + t); var o = document.getElementById('out'); if (o) o.textContent += '\n' + t; }
// the box filters on paper: -3 dB edges and the worst sidelobe above 3 kHz of the voice band, the worst leak above 1 kHz of the low band
[44100, 48000].forEach(function (sr) {
  var lo3 = null, hi3 = null, worstV = -Infinity, worstVf = 0, worstL = -Infinity, worstLf = 0, f, g;
  for (f = 20; f <= 10000; f += 5) { g = theory(sr, 'voice', f); if (g >= -3 && lo3 === null) lo3 = f; if (g >= -3) hi3 = f; if (f >= 3000 && g > worstV) { worstV = g; worstVf = f; } g = theory(sr, 'low', f); if (f >= 1000 && g > worstL) { worstL = g; worstLf = f; } }
  say('THEORY @' + sr + ': voice band -3 dB from ' + lo3 + ' to ' + hi3 + ' Hz, worst leak above 3 kHz ' + worstV + ' dB at ' + worstVf + ' Hz; low band worst leak above 1 kHz ' + worstL + ' dB at ' + worstLf + ' Hz');
});
var TONES = [60, 300, 1000, 1500, 2000, 3000, 5000], AMP = 0.1, RMS = AMP / Math.SQRT2, DUR = 15;
function db(env) { var g = Math.expm1(env) / 100 / RMS; return g > 0 ? Math.round(20 * Math.log10(g) * 10) / 10 : -Infinity; }
function r2(x) { return Math.round(x * 100) / 100; }
function toneBuf(sr, chans, mode) {
  var n = Math.round(DUR * sr), oc = new OfflineAudioContext(1, 16, sr), buf = oc.createBuffer(chans, n, sr), c, i, ti;
  for (c = 0; c < chans; c++) {
    var d = buf.getChannelData(c), a = mode === 'left' && c === 1 ? 0 : AMP;
    for (ti = 0; ti < TONES.length; ti++) { var f = TONES[ti], s0 = Math.round((1 + 2 * ti) * sr), s1 = Math.round((2.5 + 2 * ti) * sr); for (i = s0; i < s1; i++) d[i] = a * Math.sin(2 * Math.PI * f * (i - s0) / sr); }
  }
  return buf;
}
function silentBuf(sr, n) { var oc = new OfflineAudioContext(1, 16, sr); return oc.createBuffer(1, n, sr); }
function theory(sr, kind, f) {
  // the box filters' own response: a box of m taps has |sin(pi f m / sr) / (m sin(pi f / sr))|
  function box(m) { var x = Math.PI * f / sr; return Math.sin(x * m) / (m * Math.sin(x)); }
  var g;
  if (kind === 'voice') g = box(Math.max(1, Math.round(sr / 3500))) - box(Math.max(1, Math.round(sr / 250)));
  else g = box(Math.max(1, Math.round(sr / 1000))) * box(Math.max(1, Math.round(sr / 800)));
  g = Math.abs(g); return g > 1e-9 ? Math.round(20 * Math.log10(g) * 10) / 10 : -Infinity;
}
var pending = 0, done = 0, lines = [];
function track(p, label, fn) { pending++; p.then(function (v) { done++; try { fn(v); } catch (e) { lines.push('FAIL ' + label + ': ' + (e && e.stack || e)); } }, function (e) { done++; lines.push('FAIL ' + label + ' rejected: ' + e); }); }
var t00 = performance.now(), envs = {};
[44100, 48000].forEach(function (sr) {
  [['voice', voiceOf], ['low', lowOf]].forEach(function (b) {
    var kind = b[0], fn = b[1];
    track(fn(toneBuf(sr, 1, 'mono')), kind + sr, function (env) {
      if (!env) { lines.push('FAIL ' + kind + 'Of null at ' + sr); return; }
      envs[kind + sr] = env;
      var rows = [];
      for (var ti = 0; ti < TONES.length; ti++) { var k = Math.round((1 + 2 * ti + 0.75) * 100); rows.push(TONES[ti] + 'Hz ' + db(env[k]) + 'dB (theory ' + theory(sr, kind, TONES[ti]) + ')'); }
      lines.push('BAND ' + kind + ' @' + sr + ': length ' + env.length + ' (want ' + Math.floor(DUR * 100) + ') done at ' + Math.round(performance.now() - t00) + ' ms | ' + rows.join(', '));
      var seq = function (k) { var s = []; for (var q = k - 2; q <= k + 2; q++) s.push(q + ':' + r2(env[q])); return s.join(' '); };
      lines.push('ALIGN ' + kind + ' @' + sr + ': 300 Hz starts at 3.000 s -> frames ' + seq(300) + ' | 60 Hz starts at 1.000 s -> frames ' + seq(100) + ' | 1 kHz starts at 5.000 s -> ' + seq(500) + ' | quiet frame 50: ' + r2(env[50]));
    });
  });
  track(voiceOf(toneBuf(sr, 2, 'both')), 'both' + sr, function (env) { envs['both' + sr] = env; });
  track(voiceOf(toneBuf(sr, 2, 'left')), 'left' + sr, function (env) { envs['left' + sr] = env; });
});
[[44100, 441000], [44100, 441163], [48000, 480000], [48000, 480178], [22050, 220500], [22050, 220600]].forEach(function (p) {
  var sr = p[0], n = p[1];
  track(voiceOf(silentBuf(sr, n)), 'len' + sr + '/' + n, function (env) { lines.push('LENGTH voice @' + sr + ' samples ' + n + ' duration ' + (n / sr).toFixed(4) + ' s: env ' + (env ? env.length : 'null') + ' frames, floor(duration*100) ' + Math.floor(n / sr * 100) + ', hop ' + Math.round(sr / 100) + ' -> ' + (sr / Math.round(sr / 100)).toFixed(3) + ' fps' + (Math.abs(sr / Math.round(sr / 100) - 100) > 1e-9 ? ' (NOT 100: frames drift ' + ((100 / (sr / Math.round(sr / 100)) - 1) * 300).toFixed(2) + ' s over 5 min)' : '')); });
});
track(voiceOf(silentBuf(8000, 8000 * 20 * 60 + 8000)), 'guard', function (env) { lines.push('GUARD 20 min + 1 s at 8 kHz -> ' + (env === null ? 'null (as documented)' : env.length + ' frames')); });
track(voiceOf({ length: 0, duration: 0, sampleRate: 48000, numberOfChannels: 1 }), 'empty', function (env) { lines.push('GUARD empty -> ' + (env === null ? 'null' : env.length)); });
say('RENDERS started ' + pending + '; the load event is held ' + WAIT + ' ms');
function report() {
  say('RENDERS done ' + done + ' of ' + pending + ' at ' + Math.round(performance.now() - t00) + ' ms');
  lines.forEach(say);
  [44100, 48000].forEach(function (sr) {
    var mono = envs['voice' + sr], both = envs['both' + sr], left = envs['left' + sr], k = 575;
    if (!mono || !both || !left) { say('STEREO @' + sr + ': missing renders'); return; }
    say('STEREO voice @' + sr + ' 1 kHz slot frame ' + k + ': mono ' + r2(mono[k]) + ' (' + db(mono[k]) + ' dB), same tone both channels ' + r2(both[k]) + ' (' + db(both[k]) + ' dB), left only ' + r2(left[k]) + ' (' + db(left[k]) + ' dB) -> ' + (Math.abs(both[k] - mono[k]) < 0.01 ? 'AVERAGED' : 'NOT averaged (summed would be +6 dB)') + '; left-only is ' + (db(left[k]) - db(mono[k])).toFixed(1) + ' dB re mono (averaged: -6.0)');
  });
}
// report once every render is in, or when the hold is about to end
var poll = setInterval(function () { if (done >= pending || performance.now() - t00 > WAIT - 800) { clearInterval(poll); report(); } }, 100);
