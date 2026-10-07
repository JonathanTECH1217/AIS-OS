// place-test4: how long the whole flow takes on the REAL clock (run with pagecheck-rt.py): the 55 Blurry lines on a
// 5-minute synthetic 76 bpm track with a synthetic voice. Runs synchronously at the end of the body; the fetch stub
// resolves in microtasks, so everything is done before the load event.
/*BLURRY_LRC*/
var d = window.__ds, out = document.getElementById('__out');
function say(t) { out.textContent += '\n' + t; }
function r0(x) { return Math.round(x); }
if (!d || !d.S()) { say('FAIL no sheet at end of body: __ds ' + !!d + ' S ' + !!(d && d.S())); }
else {
  var fps = 100, DUR = 300, N = fps * DUR, BPM = 76, BEAT = 60 / BPM, T0 = 1.0;
  function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
  function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), f; if (k0 < env.length && env[k0] < 1.4) env[k0] = 1.4; for (f = k0 + 1; f < k1 && f < env.length; f++) if (env[f] < 2.3) env[f] = 2.3; }
  var tb0 = performance.now();
  var full = new Float32Array(N), low = new Float32Array(N), voice = new Float32Array(N), i, k = 0, t;
  for (i = 0; i < N; i++) { full[i] = 0.5; low[i] = 0.4; voice[i] = 0.4; }
  for (t = T0; t < DUR - 1; t += BEAT, k++) { var pos = k % 4; if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else if (pos === 2) { bump(low, t, 1.8, 12); bump(full, t, 1.9, 10); } else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); } bump(full, t + BEAT / 2, 1.0, 4); }
  var lrc = d.parseLrc(BLURRY_LRC);
  lrc.forEach(function (l) { if (!l.text) return; var K = d.syllableTexts(l.text).length; for (var q = 0; q < K; q++) sing(voice, l.t + 0.2 + q * 0.25, l.t + 0.4 + q * 0.25); });
  say('LOG clock probe: building the synthetic track took ' + r0(performance.now() - tb0) + ' ms (a real number means the clock runs)');
  var s = d.S(); s.time = '4/4'; s.bpm = 100; s.audio = null; s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null; s.spotify = null; d.cur().undo = []; d.cur().redo = [];
  d.cur().audio = { el: { paused: true, currentTime: 0, duration: DUR, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'Puddle of Mudd - Blurry.wav', peaks: null, duration: DUR, onset: d.risesOf(full), voice: voice, low: low, blob: false };
  var realFetch = window.fetch, jsonAt = 0, fetchAt = 0;
  window.fetch = function (url) { if (String(url).indexOf('/lyrics') === 0) { fetchAt = performance.now(); return Promise.resolve({ ok: true, status: 200, headers: new Headers({ 'content-type': 'application/json' }), json: function () { jsonAt = performance.now(); return Promise.resolve({ ok: true, synced: BLURRY_LRC, plain: '', duration: DUR, track: 'Blurry', artist: 'Puddle of Mudd' }); } }); } return realFetch.apply(this, arguments); };
  function time(label, fn) { var a = performance.now(), r = fn(); say('LOG   ' + label + ': ' + r0(performance.now() - a) + ' ms'); return r; }
  var t0 = performance.now();
  d.autoPlaceWords().then(function () {
    var t1 = performance.now(), s1 = d.S();
    say('LOG WHOLE FLOW ' + r0(t1 - t0) + ' ms: before the fetch ' + r0(fetchAt - t0) + ' ms, after the lyrics arrived one synchronous block of ' + r0(t1 - jsonAt) + ' ms (the UI thread is blocked for it); result bpm ' + s1.bpm + ' lines ' + s1.lines.length + ' locked ' + (s1.audio && s1.audio.locked));
    // second run of the same flow on the same page (a fresh sheet), to see the warm number
    s1.lines = []; s1.lyrics = ''; s1.title = ''; s1.filled = null; s1.audio = null; s1.bpm = 100; d.cur().undo = [];
    var t2 = performance.now();
    return d.autoPlaceWords().then(function () {
      var t3 = performance.now(); say('LOG WHOLE FLOW again (warm): ' + r0(t3 - t2) + ' ms, sync block ' + r0(t3 - jsonAt) + ' ms');
      say('LOG the parts by hand on the same data:');
      var on = d.risesOf(full), s2 = d.S();
      time('risesOf (30000 frames)', function () { return d.risesOf(full); });
      var bpm = time('tempoOf', function () { return d.tempoOf(on, fps); });
      var beats = time('trackBeats', function () { return d.trackBeats(on, fps, bpm); });
      time('meterOf', function () { return d.meterOf(on, low, fps, beats, 60 / bpm, null); });
      time('lockToSong(quiet, final, noUndo, bpm): trackBeats again, 2 x beatFit (a full sort of 30000 onsets), 2 renders', function () { d.lockToSong(true, true, true, bpm); });
      var vc = d.voiceCurve(); vc.rises = d.risesOf(vc.env);
      var sheetLines = []; s2.lines.forEach(function (l, li) { if (l.kind === 'line' && l.syllables.length) sheetLines.push({ li: li, text: d.sortedSyls(l).map(function (y) { return y.text + (y.hy ? '' : ' '); }).join('').trim() }); });
      var pairs = time('alignLines (55 x 60)', function () { return d.alignLines(sheetLines, lrc); });
      var windows = time('lrcWindows', function () { return d.lrcWindows(pairs, lrc, 12); });
      time('sungSpansIn over all ' + windows.length + ' windows', function () { windows.forEach(function (w) { var K = 0, hy = []; w.lis.forEach(function (li) { d.sortedSyls(s2.lines[li]).forEach(function (y) { if (!y.rest) { K++; hy.push(!!y.hy); } }); }); d.sungSpansIn(vc, w.t0 - 0.12, w.t1 - 0.05, K, hy); }); });
      time('pushUndo (plain copy of the 55-line sheet)', function () { d.pushUndo(); });
      time('renderWork (55 lines, VexFlow)', function () { d.renderWork(); });
      time('renderAll (chrome + tabs + work + inspector + tones)', function () { d.renderAll(); });
      time('wordsToNotes (parse + renderAll)', function () { d.wordsToNotes(s2.lyrics, s2.title, { noUndo: true, quiet: true }); });
      time('applyTime (renderWork + inspector + status)', function () { d.applyTime('4/4'); });
      var tot = 0; time('slotOfSong x 10000 (locked grid, binary search)', function () { for (var q = 0; q < 10000; q++) tot += d.slotOfSong(q * 0.03); });
      say('LOG done');
      out.textContent += '\n' + __lines.join('\n');
      window.fetch = realFetch;
    });
  }).catch(function (e) { say('FAIL ' + (e && e.stack || e)); out.textContent += '\n' + __lines.join('\n'); window.fetch = realFetch; });
}
