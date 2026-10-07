// Test 2 (playhead part): the band with Spotify on. A real sheet, player.start() with a faked Spotify (fetch stub,
// fake clock, rAF stubbed), frames driven by hand every 16 ms. Measures red-line jumps in slots and px per frame,
// the snaps in reportSong, the loop-wrap snap, and the stop-with-a-poll-in-flight race.
var d = window.__ds, sp = d.sp, player = d.player, editor = d.editor, state = d.state;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var seed = 4321; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
var fakeNow = 1000; performance.now = function () { return fakeNow; };
window.requestAnimationFrame = function () { return 0; }; window.cancelAnimationFrame = function () {};
player.ensureAudio = function () {};
var realFetch = window.fetch;
var song = { playing: false, pos: 0, at: 0, next: null };
function truth(t) { if (song.next && t >= song.next.at) return song.next.pos + (t - song.next.at); return song.playing ? song.pos + Math.max(0, t - song.at) : song.pos; }
function songTick() { if (song.next && fakeNow >= song.next.at) { song.pos = song.next.pos; song.at = song.next.at; song.next = null; } }
var model = { spike: 0.05, spikeMs: 800, stale: 0, staleMs: 1000, inject: [], startLat: 350, seekLat: 300 }, pending = [], log = [];
window.fetch = function (url, opts) {
  url = String(url);
  var ok204 = { status: 204, ok: true, headers: { get: function () { return null; } }, text: function () { return Promise.resolve(''); } };
  if (/\/me\/player\/play/.test(url)) { var body = JSON.parse(opts.body); song.next = { at: fakeNow + model.startLat, pos: body.position_ms }; song.playing = true; song.pos = body.position_ms; song.at = fakeNow + model.startLat; log.push('play ' + body.position_ms + ' at ' + fakeNow); return Promise.resolve(ok204); }
  if (/\/me\/player\/seek/.test(url)) { var ms = +/position_ms=(\d+)/.exec(url)[1]; song.next = { at: fakeNow + model.seekLat, pos: ms }; log.push('seek ' + ms + ' at ' + fakeNow); return Promise.resolve(ok204); }
  if (/\/me\/player\/pause/.test(url)) { song.next = null; song.playing = false; song.pos = truth(fakeNow); return Promise.resolve(ok204); }
  if (url.indexOf('/me/player') >= 0) {
    var rtt = rnd() < model.spike ? model.spikeMs : rnd() * 300, u = rnd(), tServer = fakeNow + u * rtt;
    var stale = model.inject.length ? model.inject.shift() : ((model.stale && rnd() < model.stale) ? rnd() * model.staleMs : 0);
    var progress = Math.round(truth(tServer - stale));
    return new Promise(function (res) { pending.push({ due: fakeNow + rtt, progress: progress, res: res, playing: song.playing }); });
  }
  return realFetch(url, opts);
};
function flushDue(forcePlaying) {
  var fired = []; pending = pending.filter(function (p) { if (p.due <= fakeNow) { fired.push(p); return false; } return true; });
  fired.forEach(function (p) { p.res({ status: 200, ok: true, headers: { get: function () { return null; } }, text: function () { return Promise.resolve(JSON.stringify({ is_playing: forcePlaying !== undefined ? forcePlaying : p.playing, progress_ms: p.progress, item: { id: 'x' } })); } }); });
  return fired.length;
}
function tick0() { return new Promise(function (r) { setTimeout(r, 0); }); }
async function micro() { for (var k = 0; k < 12; k++) await Promise.resolve(); }
function stateLine(tag) { var s = d.S(); return tag + ': bpm ' + s.bpm + ' time ' + s.time + ' pct ' + player.pct + ' speed ' + state.speed + ' offsetSec ' + d.sheetAudio().offsetSec + ' locked ' + !!d.songGrid() + ' slotSec ' + player.slotSec.toFixed(4) + ' lineUp ' + (document.getElementById('audLineUp') && document.getElementById('audLineUp').classList.contains('on')); }
function mkSheet(counts) {
  var text = counts.map(function (n) { var w = []; for (var i = 0; i < n; i++) w.push('da'); return w.join(' '); }).join('\n');
  d.wordsToNotes(text, 'Test', { noUndo: true, quiet: true });
  var W = document.getElementById('sys').clientWidth; state.prefs.zoom = Math.ceil((W - 130) / 3.5); d.renderWork();
}
var snaps = [], origReport = player.reportSong;
player.reportSong = function (songSec, dead) { var before = this.position(), ns = this.needSnap; origReport.call(this, songSec, dead); var after = this.position(); if (Math.abs(after - before) > 1e-9) snaps.push({ t: Math.round((fakeNow - T0) / 100) / 10, slots: Math.round((after - before) * 100) / 100, ms: Math.round((after - before) * this.slotSec * 1000), first: ns }); };
var T0 = 0;
async function startBand(fromSlot) {
  sp.refresh = 'r'; sp.access = 'a'; sp.exp = Date.now() + 1e9; sp.connected = true; sp.polling = false; sp.pollBusy = false; sp.backoffUntil = 0; sp.seekAt = 0; sp.offs = []; sp.odd = null; sp.playing = false;
  state.audioOn = true; d.sheetAudio().lined = true; player.startSlot = fromSlot || 0; pending = []; snaps = []; log = []; model.inject = []; song.next = null; song.playing = false;
  say('LOG   ' + stateLine('before start'));
  player.start(); T0 = fakeNow;
  for (var i = 0; i < 4; i++) await tick0();
  sp.polling = false; clearTimeout(sp.pollTimer); sp.pollTimer = null; clearInterval(player.timer); player.timer = null;
  say('LOG   ' + stateLine('after start'));
  return player.on && player.spot && sp.playing;
}
// run the band for `ms` of fake time; returns per-frame records
async function runFrames(ms, opts) {
  opts = opts || {};
  var recs = [], inFlight = false, nextPoll = fakeNow + 500, end = fakeNow + ms;
  while (fakeNow < end && player.on) {
    fakeNow += 16; songTick();
    if (!inFlight && fakeNow >= nextPoll) { inFlight = true; d.spPoll(); await micro(); if (!pending.length) { say('FAIL poll did not reach fetch'); return recs; } }
    if (inFlight && flushDue()) { await micro(); inFlight = false; nextPoll = fakeNow + (fakeNow - (sp.seekAt || 0) < 3000 ? 500 : 1000); }
    if (opts.each) opts.each();
    player.frame(); await micro();
    if (!player.on) break;
    var g = player.position(), bi = Math.floor(g / player.spb), bar = player.bars[bi], sy = bar && editor.systems[bar.sys];
    recs.push({ t: fakeNow - T0, g: g, left: sy && sy.ph ? parseFloat(sy.ph.style.left) : NaN, sys: bar ? bar.sys : -1, err: d.songOfSlot(g) * 1000 - truth(fakeNow), corr: player.corr, est: d.spPosition() - truth(fakeNow) });
  }
  return recs;
}
function analyse(recs, label, from) {
  var exp = 16 / (player.slotSec * 1000), maxJ = 0, nJ = 0, n02 = 0, prev = null, maxPx = 0, se = 0, n = 0, maxErr = 0, pxPerSlot = 0;
  recs.forEach(function (r) {
    if (r.t < (from || 0)) { prev = r; return; }
    if (prev && prev.sys === r.sys) { var dj = r.g - prev.g - exp; if (Math.abs(dj) > Math.abs(maxJ)) maxJ = dj; if (Math.abs(dj) > 0.05) nJ++; if (Math.abs(dj) > 0.2) n02++; var dpx = r.left - prev.left; if (Math.abs(dpx) > maxPx && Math.abs(r.g - prev.g) > 0.2) maxPx = Math.abs(dpx); }
    se += r.err * r.err; n++; if (Math.abs(r.err) > maxErr) maxErr = Math.abs(r.err); prev = r;
  });
  var cell = editor.systems[player.bars[0].sys].geo.cells[0]; pxPerSlot = (cell.x1 - cell.x0) / player.spb;
  say('LOG   ' + label + ': expected ' + exp.toFixed(3) + ' slots/frame (' + (pxPerSlot * exp).toFixed(1) + ' px); largest per-frame jump ' + maxJ.toFixed(2) + ' slots (' + Math.round(maxJ * player.slotSec * 1000) + ' ms, ' + Math.round(Math.abs(maxJ) * pxPerSlot) + ' px); frames off by >0.05 slot: ' + nJ + ', >0.2 slot: ' + n02 + '; band vs song rms ' + Math.round(Math.sqrt(se / n)) + ' ms max ' + Math.round(maxErr) + ' ms');
}
function snapText() { return snaps.length ? snaps.map(function (s) { return s.t + 's:' + (s.ms > 0 ? '+' : '') + s.ms + 'ms(' + s.slots + ' sl' + (s.first ? ',first' : '') + ')'; }).join(' ') : 'none'; }
(async function () {
  try {
    mkSheet([8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8]); var s = d.S(); s.bpm = 120;
    say('LOG staged sheet came with audio ' + JSON.stringify(s.audio && { locked: s.audio.locked, beats: s.audio.beats && s.audio.beats.length, offsetSec: s.audio.offsetSec, name: s.audio.name }));
    s.audio = { offsetSec: 60, lined: true, name: '', assetId: null, beats: null, locked: false, lockFit: null };
    s.spotify = { trackId: 'x', name: 'Test · Tester', durationMs: 240000, title: 'Test', artist: 'Tester', album: '' };
    d.sheetAudio().offsetSec = 60; d.sheetAudio().lined = true;
    say('LOG sheet: ' + editor.systems.length + ' systems, ' + document.querySelectorAll('.syl-chip').length + ' chips, ' + player.bars.length + ' bars');
    // A: plain M1 noise, 20 s
    var ok = await startBand(0); check('band started on Spotify', ok, 'on ' + player.on + ' spot ' + player.spot + ' playing ' + sp.playing);
    var recs = await runFrames(11000);
    say('LOG A (M1 noise, start lat 350 ms): snaps ' + snapText());
    analyse(recs, 'A first 4 s', 0); analyse(recs, 'A after 4 s', 4000); say('LOG   ' + stateLine('after A'));
    // B: one stale reading of 400 ms
    snaps = []; model.inject = [400]; recs = await runFrames(4000); say('LOG B one 400 ms stale reading: snaps ' + snapText() + ' corr now ' + Math.round(player.corr * 1000) + ' ms'); analyse(recs, 'B', 0);
    // C: two stale readings in a row (400 and 420 ms)
    snaps = []; model.inject = [400, 420]; recs = await runFrames(6000); say('LOG C two stale readings 400/420 ms: snaps ' + snapText()); analyse(recs, 'C', 0);
    // D: the threshold: a pair at 330 ms (under 0.35) then a pair at 370 ms
    snaps = []; model.inject = [330, 335]; recs = await runFrames(5000); say('LOG D pair at 330 ms: snaps ' + snapText() + '; corr after ' + Math.round(player.corr * 1000) + ' ms'); analyse(recs, 'D 330', 0);
    snaps = []; model.inject = [370, 375]; recs = await runFrames(5000); say('LOG D pair at 370 ms: snaps ' + snapText()); analyse(recs, 'D 370', 0);
    check('band still on after A-D (31 s of a 48 s sheet)', player.on, 'position ' + player.position().toFixed(1) + ' of ' + player.bars.length * player.spb);
    player.stop(); await tick0();
    // H: the absorb gap, band alone (no reports): corr absorbed to 0, a quiet spell, then a 200 ms correction lands in one frame
    state.audioOn = false; var spot0 = s.spotify; s.spotify = null; player.startSlot = 0; player.start(); clearInterval(player.timer);
    check('band alone for H', player.on && !player.spot);
    function plain(ms) { var end = fakeNow + ms; while (fakeNow < end && player.on) { fakeNow += 16; player.frame(); } }
    plain(1000); player.corr = 0.05; plain(2000);
    check('a 50 ms correction is absorbed to 0 within 2 s', player.corr === 0, 'corr ' + player.corr);
    var lastAbs = player.lastAbsorb; plain(5000); var gap = player.now() - player.lastAbsorb;
    var gBefore = player.position(); player.corr = 0.2; fakeNow += 16; player.frame(); var step = player.position() - gBefore - 16 / (player.slotSec * 1000);
    say('LOG H absorb after a ' + gap.toFixed(1) + ' s quiet spell (lastAbsorb unchanged since the last absorb: ' + (lastAbs === player.lastAbsorb) + '): a 200 ms correction moved the line ' + Math.round(step * player.slotSec * 1000) + ' ms (' + step.toFixed(2) + ' slots) in ONE frame; the 4 %/s rate would allow 0.64 ms');
    check('absorb is rate limited after a quiet spell', Math.abs(step * player.slotSec * 1000) < 2, Math.round(step * player.slotSec * 1000) + ' ms in one frame');
    // the same right after a 1 s poll gap: 60 ms diff, corr was 0 for 1.2 s
    player.corr = 0; plain(1200); gBefore = player.position(); player.corr = 0.06; fakeNow += 16; player.frame(); step = player.position() - gBefore - 16 / (player.slotSec * 1000);
    say('LOG H after 1.2 s with corr 0 (a normal poll gap): a 60 ms diff moved the line ' + Math.round(step * player.slotSec * 1000) + ' ms in one frame');
    player.stop(); s.spotify = spot0; state.audioOn = true; await tick0();
    // E: the loop wrap on Spotify: loop bars 2-3
    d.cur().loop = { a: 2, b: 3 }; d.cur().loopOn = true;
    ok = await startBand(0); check('band started in the loop', ok && player.loopA === 2, 'loopA ' + player.loopA + ' slot0 ' + player.slot0);
    recs = await runFrames(14000);
    var wraps = []; for (var i = 1; i < recs.length; i++) if (recs[i].g < recs[i - 1].g - 5) wraps.push(Math.round(recs[i].t / 100) / 10);
    say('LOG E loop bars 2-3 (4 s round): wraps at ' + wraps.join(', ') + ' s; snaps ' + snapText());
    say('LOG   log: ' + log.join(' | '));
    d.cur().loop = null; d.cur().loopOn = false; player.stop(); await tick0();
    // F: stop while a poll is in flight, the answer says still playing
    ok = await startBand(0); await runFrames(5000);
    d.spPoll(); await tick0(); check('a poll is in flight', pending.length === 1);
    player.stop(); await tick0(); var wasPlaying = sp.playing;
    fakeNow += 400; flushDue(true); await tick0(); await tick0();
    check('sp.playing stays false after stop when the in-flight poll answers "playing"', sp.playing === false, 'right after stop ' + wasPlaying + ', after the late answer ' + sp.playing + ', polling ' + sp.polling + ', trackSrc().playing ' + (d.trackSrc() && d.trackSrc().playing));
    var lit0 = document.querySelectorAll('.syl-chip.playing').length; d.followFrame(); var lit1 = document.querySelectorAll('.syl-chip.playing').length;
    check('followFrame after stop lights nothing', lit1 === 0, 'chips lit before ' + lit0 + ' after ' + lit1 + ' (the 200 ms strip ticker calls followSong/followStart on its own whenever trackSrc().playing is true)');
    fakeNow += 3000; say('LOG   spPosition keeps running after stop? ' + (d.spPosition() - sp.pos > 1000 ? 'yes, +' + Math.round(d.spPosition() - sp.pos) + ' ms' : 'no'));
    // G: the M2 model (stale device reports) under the band, 30 s
    sp.playing = false; model.stale = 0.3; model.staleMs = 1000; ok = await startBand(0); recs = await runFrames(23000);
    say('LOG G 30% stale device reports up to 1 s: snaps ' + snapText()); analyse(recs, 'G after 4 s', 4000);
    player.stop();
    say('DONE');
  } catch (e) { say('FAIL ' + (e && e.stack || e)); }
})();
