// Test 3 (playhead part): the locked grid. Beats with a tempo drift and jitter; the band alone (no song), frames by
// hand; the red line must be continuous across beat boundaries, system changes and the loop end. Also the file path
// with a quantised currentTime, and the gap between bar cells that the red line leaps at every bar line.
var d = window.__ds, player = d.player, editor = d.editor, state = d.state;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var seed = 99; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
var fakeNow = 1000; performance.now = function () { return fakeNow; };
window.requestAnimationFrame = function () { return 0; }; window.cancelAnimationFrame = function () {};
player.ensureAudio = function () {};
function mkSheet(counts) {
  var text = counts.map(function (n) { var w = []; for (var i = 0; i < n; i++) w.push('da'); return w.join(' '); }).join('\n');
  d.wordsToNotes(text, 'Test', { noUndo: true, quiet: true });
  var W = document.getElementById('sys').clientWidth; state.prefs.zoom = Math.ceil((W - 130) / 3.5); d.renderWork();
}
function run(ms, each) {
  var recs = [], end = fakeNow + ms;
  while (fakeNow < end && player.on) {
    fakeNow += 16; if (each) each(); player.frame(); if (!player.on) break;
    var g = player.position(), bi = Math.floor(g / player.spb), bar = player.bars[bi], sy = editor.systems[bar.sys];
    recs.push({ t: fakeNow, g: g, song: d.songOfSlot(g), left: parseFloat(sy.ph.style.left), sys: bar.sys, k: bar.k, slotSec: player.slotSec });
  }
  return recs;
}
try {
  mkSheet([8, 8, 8, 8, 8, 8]); var s = d.S(); s.bpm = 120; state.audioOn = false; s.spotify = null;
  // beats: 12 bars x 4 + 8 spare, interval 0.5 s drifting to 0.6 s, jitter +-10 ms
  var beats = [], t = 10, N = 12 * 4 + 8; for (var i = 0; i < N; i++) { beats.push(+(t + (rnd() - 0.5) * 0.02).toFixed(4)); t += 0.5 + 0.1 * i / N; }
  s.audio = { offsetSec: beats[0], lined: true, locked: true, beats: beats, lockFit: null, name: '', assetId: null };
  check('grid is on', !!d.songGrid() && d.songGrid().length === N);
  say('LOG sheet: ' + editor.systems.length + ' systems, ' + player.bars.length + ' bars; local slotSec at slot 0 ' + d.localSlotSec ? '' : '');
  // gaps between bar cells
  var gaps = []; editor.systems.forEach(function (sy) { if (sy.header || !sy.geo) return; var c = sy.geo.cells; for (var k = 1; k < c.length; k++) gaps.push(Math.round((c[k].x0 - c[k - 1].x1) * 10) / 10); var w = c.map(function (cc) { return Math.round(cc.x1 - cc.x0); }); gaps.push('|w ' + w.join('/')); });
  say('LOG cell gaps (px the red line leaps at each bar line inside a system) and cell widths: ' + gaps.join(' '));
  var firstCell = editor.systems[player.bars[0].sys].geo.cells[0];
  say('LOG per-frame red-line motion at 16 ms: ' + ((firstCell.x1 - firstCell.x0) / 16 * 16 / 500 * 4).toFixed(2) + ' px (bar ' + Math.round(firstCell.x1 - firstCell.x0) + ' px, 2 s per bar)');
  // A: band alone from slot 0 through the whole sheet
  player.startSlot = 0; player.start(); clearInterval(player.timer);
  check('band on with the grid', player.on && !player.spot, 'slotSec ' + player.slotSec.toFixed(4));
  var t0 = fakeNow, song0 = d.songOfSlot(player.position());
  var recs = run(30000);
  var maxErr = 0, maxDErr = 0, prev = null, worst = null, beatCross = 0, sysChanges = [], badSys = 0;
  recs.forEach(function (r) {
    var e = (r.song - song0) * 1000 - (r.t - t0); if (Math.abs(e) > Math.abs(maxErr)) maxErr = e;
    if (prev) { var de = e - ((prev.song - song0) * 1000 - (prev.t - t0)); if (Math.abs(de) > Math.abs(maxDErr)) { maxDErr = de; worst = r; } if (Math.floor(r.g / 4) !== Math.floor(prev.g / 4)) beatCross++; if (r.sys !== prev.sys) { var c0 = editor.systems[r.sys].geo.cells[0]; sysChanges.push('sys ' + prev.sys + '>' + r.sys + ' at slot ' + r.g.toFixed(2) + ' left ' + r.left.toFixed(1) + ' (cell x0 ' + c0.x0.toFixed(1) + ')'); if (Math.abs(r.left - c0.x0) > 3) badSys++; } }
    prev = r;
  });
  say('LOG A band alone, ' + recs.length + ' frames, ' + beatCross + ' beat boundaries: song-time error vs a straight clock max ' + maxErr.toFixed(2) + ' ms, largest per-frame error step ' + maxDErr.toFixed(3) + ' ms' + (worst ? ' at slot ' + worst.g.toFixed(2) : ''));
  check('the red line is continuous across beat boundaries (per-frame error step < 1 ms)', Math.abs(maxDErr) < 1, maxDErr.toFixed(3) + ' ms');
  check('accumulated drift over the sheet < 20 ms', Math.abs(maxErr) < 20, maxErr.toFixed(2) + ' ms');
  say('LOG   system changes: ' + sysChanges.join('; '));
  check('at each system change the line starts at the new system first cell', badSys === 0, badSys + ' off');
  check('the band stopped at the end of the sheet', !player.on, 'on ' + player.on);
  // B: the loop end (bars 4-6), 3 rounds
  d.cur().loop = { a: 4, b: 6 }; d.cur().loopOn = true; player.startSlot = 0; player.start(); clearInterval(player.timer);
  check('loop set', player.loopA === 4 && player.loopB === 6 && player.slot0 === 64, 'slot0 ' + player.slot0);
  recs = run(20000); var wraps = [];
  for (var i = 1; i < recs.length; i++) if (recs[i].g < recs[i - 1].g - 5) { var want = 16 / 1000 / player.slotSecAt(64); wraps.push('t+' + Math.round(recs[i].t - t0) + ' g ' + recs[i - 1].g.toFixed(2) + '>' + recs[i].g.toFixed(3) + ' slotSec used ' + recs[i].slotSec.toFixed(4) + ' wanted ' + player.slotSecAt(64).toFixed(4) + ' next-frame step ' + (recs[i + 1].g - recs[i].g).toFixed(4) + ' wanted ' + want.toFixed(4)); }
  say('LOG B loop 4-6: ' + wraps.join(' | '));
  check('every wrap lands on slot 64 (+ one frame)', wraps.length >= 3 && recs.every(function (r) { return r.g >= 64 - 0.001 && r.g < 112 + 0.2; }), wraps.length + ' wraps');
  player.stop(); d.cur().loop = null; d.cur().loopOn = false;
  // C: the file path with the grid: currentTime quantised to 250 ms (an old-Firefox media clock) and to 16 ms
  [250, 16].forEach(function (q) {
    var base = null, el = { paused: false, seeking: false, readyState: 4, duration: 300, playbackRate: 1, pause: function () { this.paused = true; }, play: function () { this.paused = false; return Promise.resolve(); } };
    Object.defineProperty(el, 'currentTime', { get: function () { var tt = base === null ? 0 : (fakeNow - base) / 1000 + this._start; return Math.floor(tt * 1000 / q) * q / 1000; }, set: function (v) { this._start = v; base = fakeNow; }, configurable: true });
    d.cur().audio = { el: el, url: '', name: 'test.wav', peaks: null, duration: 300, onset: null, voice: null, low: null, blob: false };
    state.audioOn = true; player.startSlot = 0; player.start(); clearInterval(player.timer);
    var r2 = run(20000), mx = 0, n01 = 0, exp = 0, p = null, snapN = 0;
    r2.forEach(function (r) { if (p && p.sys === r.sys) { var dj = (r.g - p.g) - 16 / 1000 / p.slotSec; if (Math.abs(dj) > Math.abs(mx)) mx = dj; if (Math.abs(dj) > 0.1) n01++; if (Math.abs(dj) > 1) snapN++; } p = r; });
    say('LOG C file clock quantised to ' + q + ' ms: ' + r2.length + ' frames, largest per-frame step error ' + mx.toFixed(3) + ' slots (' + Math.round(mx * 125) + ' ms), frames off by >0.1 slot ' + n01 + ', >1 slot ' + snapN);
    player.stop(); state.audioOn = false; d.cur().audio = null;
  });
  // D: start mid-grid where the tempo differs: slotSec follows slotSecAt
  player.startSlot = 100; player.start(); clearInterval(player.timer);
  check('start at slot 100 uses the local beat length', Math.abs(player.slotSec - d.localSlotSec ? player.slotSec - player.slotSecAt(100) : 0) < 1e-9, 'slotSec ' + player.slotSec.toFixed(4) + ' local ' + player.slotSecAt(100).toFixed(4) + ' nominal ' + player.nominal().toFixed(4));
  player.stop();
  say('DONE');
} catch (e) { say('FAIL ' + (e && e.stack || e)); }
