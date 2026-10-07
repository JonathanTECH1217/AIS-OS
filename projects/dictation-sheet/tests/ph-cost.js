// Test 5 (playhead part): cost of frame() per call with 40 chips, of the once-a-second drawWave() inside it, and of
// highlightSlot alone. Run with realcheck.py (real clock), TIMEOUT 15000.
var d = window.__ds, player = d.player, editor = d.editor, state = d.state;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
window.requestAnimationFrame = function () { return 0; }; window.cancelAnimationFrame = function () {};
player.ensureAudio = function () {};
function mkSheet(counts) {
  var text = counts.map(function (n) { var w = []; for (var i = 0; i < n; i++) w.push('da'); return w.join(' '); }).join('\n');
  d.wordsToNotes(text, 'Test', { noUndo: true, quiet: true });
  var W = document.getElementById('sys').clientWidth; state.prefs.zoom = Math.ceil((W - 130) / 3.5); d.renderWork();
}
function pct(a, p) { var b = a.slice().sort(function (x, y) { return x - y; }); return b[Math.min(b.length - 1, Math.floor(b.length * p))]; }
function fmt(a) { var s = 0; a.forEach(function (v) { s += v; }); return 'n ' + a.length + ' mean ' + (s / a.length).toFixed(3) + ' p50 ' + pct(a, 0.5).toFixed(3) + ' p95 ' + pct(a, 0.95).toFixed(3) + ' max ' + pct(a, 1).toFixed(3) + ' ms'; }
try {
  mkSheet([12, 20, 8]); var s = d.S(); s.bpm = 120;
  var peaks = new Float32Array(800); for (var i = 0; i < 800; i++) peaks[i] = 0.2 + 0.8 * Math.abs(Math.sin(i * 0.37));
  var base = performance.now(), el = { paused: false, seeking: false, readyState: 4, duration: 240, playbackRate: 1, pause: function () { this.paused = true; }, play: function () { this.paused = false; return Promise.resolve(); } };
  Object.defineProperty(el, 'currentTime', { get: function () { return (performance.now() - base) / 1000 + (this._start || 0); }, set: function (v) { this._start = v; base = performance.now(); } });
  d.cur().audio = { el: el, url: '', name: 'test.wav', peaks: peaks, duration: 240, onset: null, voice: null, low: null, blob: false };
  d.sheetAudio().offsetSec = 5; d.sheetAudio().lined = true; state.audioOn = true;
  say('LOG sheet: ' + editor.systems.length + ' systems, ' + document.querySelectorAll('.syl-chip').length + ' chips');
  player.startSlot = 0; player.start(); clearInterval(player.timer);
  var plain = [], withWave = [], t0 = performance.now();
  while (performance.now() - t0 < 6000 && player.on) {
    var ld = player.lastDrift, a = performance.now(); player.frame(); var b = performance.now();
    (player.lastDrift !== ld ? withWave : plain).push(b - a);
    // wait ~16 ms of real time between frames the cheap way
    var w = performance.now(); while (performance.now() - w < 16) { /* spin */ }
  }
  say('LOG frame() without drawWave: ' + fmt(plain));
  say('LOG frame() on the seconds (with syncAudio(false) + drawWave, 800 peaks): ' + fmt(withWave));
  // highlightSlot alone, 2000 calls sweeping the sheet
  var bars = player.bars, spb = player.spb, hs = [];
  for (var k = 0; k < 2000; k++) { var g = (k * 0.08) % (bars.length * spb), bi = Math.floor(g / spb), bar = bars[bi]; var a2 = performance.now(); d.highlightSlot(bar, bar.b * spb + (g - bi * spb)); hs.push(performance.now() - a2); }
  say('LOG highlightSlot alone: ' + fmt(hs));
  // the layout read in frame(): style.left write then getBoundingClientRect on the playhead and on #work
  var sy = editor.systems[bars[0].sys], work = document.getElementById('work'), gb = [];
  for (k = 0; k < 500; k++) { sy.ph.style.left = (100 + (k % 50)) + 'px'; var a3 = performance.now(); work.getBoundingClientRect(); sy.ph.getBoundingClientRect(); gb.push(performance.now() - a3); }
  say('LOG style.left write + 2 getBoundingClientRect (forced layout) : ' + fmt(gb));
  player.stop();
  // and the strip ticker while the song plays on its own: drawWave + renderPlayUI + followSong every 200 ms
  var st = []; for (k = 0; k < 50; k++) { var a4 = performance.now(); d.followSong(d.trackSrc()); st.push(performance.now() - a4); }
  say('LOG followSong alone: ' + fmt(st));
  d.cur().audio = null; state.audioOn = false;
  say('DONE');
} catch (e) { say('FAIL ' + (e && e.stack || e)); }
