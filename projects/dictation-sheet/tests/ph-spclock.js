// Test 1 (playhead part): the Spotify clock. The real spPoll is driven through a stubbed fetch whose readings come
// from a modeled song clock: progress_ms is the true position sampled somewhere inside the round trip (rtt uniform
// 0-300 ms, sometimes 800 ms), optionally stale (a Connect device that reported a while ago). spPosition() is
// sampled every 16 ms of fake time. The OLD rule (pos = progress, posAt = tRecv - 80) runs on the same readings.
var d = window.__ds, sp = d.sp;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
var seed = 12345; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
var fakeNow = 1000; performance.now = function () { return fakeNow; };
var realFetch = window.fetch;
var song = { playing: false, pos: 0, at: 0, next: null };   // next: a pending jump {at, pos}
function truth(t) { if (song.next && t >= song.next.at) return song.next.pos + (t - song.next.at); return song.playing ? song.pos + Math.max(0, t - song.at) : song.pos; }
function songTick() { if (song.next && fakeNow >= song.next.at) { song.pos = song.next.pos; song.at = song.next.at; song.next = null; } }
var model = { spike: 0.05, spikeMs: 800, stale: 0, staleMs: 1000 }, pending = [], readings = 0;
window.fetch = function (url, opts) {
  url = String(url);
  var ok204 = { status: 204, ok: true, headers: { get: function () { return null; } }, text: function () { return Promise.resolve(''); } };
  if (/\/me\/player\/(play|seek|pause)/.test(url)) return Promise.resolve(ok204);
  if (url.indexOf('/me/player') >= 0) {
    var rtt = rnd() < model.spike ? model.spikeMs : rnd() * 300, u = rnd(), tServer = fakeNow + u * rtt;
    var stale = (model.stale && rnd() < model.stale) ? rnd() * model.staleMs : 0;
    var progress = Math.round(truth(tServer - stale));
    return new Promise(function (res) { pending.push({ due: fakeNow + rtt, progress: progress, res: res, rtt: rtt, stale: stale }); });
  }
  return realFetch(url, opts);
};
var old = { pos: 0, posAt: 0 };
function flushDue() {
  var fired = []; pending = pending.filter(function (p) { if (p.due <= fakeNow) { fired.push(p); return false; } return true; });
  fired.forEach(function (p) {
    readings++;
    // the OLD rule on the same reading (same 1.5 s settling window)
    if (fakeNow - (sp.seekAt || 0) >= 1500) { old.pos = p.progress; old.posAt = fakeNow - 80; }
    p.res({ status: 200, ok: true, headers: { get: function () { return null; } }, text: function () { return Promise.resolve(JSON.stringify({ is_playing: true, progress_ms: p.progress, item: { id: 'x' } })); } });
  });
  return fired.length;
}
function tick0() { return new Promise(function (r) { setTimeout(r, 0); }); }
function stats(samples, from, to, key) {
  var back = 0, fwd = 0, n50 = 0, n100 = 0, n350 = 0, se = 0, n = 0, maxErr = 0, prev = null;
  samples.forEach(function (s) {
    if (s.t < from || s.t > to) { prev = null; return; }
    if (prev) { var dl = s[key] - prev[key] - 16; if (dl < 0 && -dl > back) back = -dl; if (dl > 0.8 && dl - 0.8 > fwd) fwd = dl - 0.8; if (Math.abs(dl) > 50) n50++; if (Math.abs(dl) > 100) n100++; if (Math.abs(dl) > 350) n350++; }
    var e = s[key] - s.tr; se += e * e; n++; if (Math.abs(e) > maxErr) maxErr = Math.abs(e); prev = s;
  });
  return { back: Math.round(back), fwd: Math.round(fwd), n50: n50, n100: n100, n350: n350, rms: n ? Math.round(Math.sqrt(se / n)) : 0, maxErr: Math.round(maxErr) };
}
function settle(samples, tSeek, key, tol) {
  // time after the seek from which |err| stays within tol until the window ends (10 s)
  var end = tSeek + 10000, last = null;
  samples.forEach(function (s) { if (s.t >= tSeek && s.t <= end && Math.abs(s[key] - s.tr) > tol) last = s.t; });
  return last === null ? 0 : Math.round(last - tSeek);
}
async function run(label, opts) {
  sp.refresh = 'r'; sp.access = 'a'; sp.exp = Date.now() + 1e9; sp.connected = true; sp.trackId = 'x'; sp.polling = false; sp.pollBusy = false; sp.backoffUntil = 0;
  fakeNow += 5000; pending = []; readings = 0; seed = opts.seed || 12345;
  var P0 = 60000;
  song.playing = false; song.pos = P0; song.at = fakeNow; song.next = { at: fakeNow + opts.startLat, pos: P0 }; song.playing = true; song.pos = P0; song.at = fakeNow + opts.startLat;
  // what spPlayAt does
  sp.pos = P0; sp.posAt = fakeNow; sp.seekAt = fakeNow; sp.playing = true; sp.offs = []; sp.odd = null;
  old.pos = P0; old.posAt = fakeNow;
  var t0 = fakeNow, T = fakeNow + opts.dur, nextPoll = fakeNow + 500, samples = [], seekT = t0 + opts.seekAt, seeked = false, inFlight = false, jumps = [];
  var prevEst = null, prevT = 0;
  while (fakeNow < T) {
    fakeNow += 16; songTick();
    if (!seeked && fakeNow >= seekT) {
      seeked = true; seekT = fakeNow;
      // what spSeek does to the state (the PUT itself changes nothing here); the song lands on the new spot a little later
      sp.pos = opts.seekTo; sp.posAt = fakeNow; sp.seekAt = fakeNow; sp.offs = []; sp.odd = null;
      old.pos = opts.seekTo; old.posAt = fakeNow;
      song.next = { at: fakeNow + opts.seekLat, pos: opts.seekTo };
    }
    if (!inFlight && fakeNow >= nextPoll) { inFlight = true; d.spPoll(); await tick0(); if (!pending.length) { say('FAIL poll did not reach fetch'); return; } }
    if (inFlight && flushDue()) { await tick0(); inFlight = false; nextPoll = fakeNow + (fakeNow - (sp.seekAt || 0) < 3000 ? 500 : 1000); }
    var est = d.spPosition(), oe = old.pos + (fakeNow - old.posAt), tr = truth(fakeNow);
    if (prevEst !== null && fakeNow !== seekT && Math.abs(est - prevEst - 16) > 100) jumps.push({ t: Math.round((fakeNow - t0) / 100) / 10, jump: Math.round(est - prevEst - 16), offs: sp.offs.length, odd: sp.odd !== null });
    prevEst = est;
    samples.push({ t: fakeNow, est: est, old: oe, tr: tr });
  }
  var steadyNew = stats(samples, t0 + 4000, seekT - 16, 'est'), steadyOld = stats(samples, t0 + 4000, seekT - 16, 'old');
  var afterNew = stats(samples, seekT, seekT + 10000, 'est'), afterOld = stats(samples, seekT, seekT + 10000, 'old');
  var startNew = stats(samples, t0, t0 + 4000, 'est'), startOld = stats(samples, t0, t0 + 4000, 'old');
  say('LOG == ' + label + ' (' + readings + ' readings over ' + (opts.dur / 1000) + ' s) ==');
  say('LOG   after play (0-4 s)  NEW back ' + startNew.back + ' fwd ' + startNew.fwd + ' maxErr ' + startNew.maxErr + ' | OLD back ' + startOld.back + ' fwd ' + startOld.fwd + ' maxErr ' + startOld.maxErr);
  say('LOG   steady (4 s-seek)   NEW back ' + steadyNew.back + ' fwd ' + steadyNew.fwd + ' jumps>50 ' + steadyNew.n50 + ' >100 ' + steadyNew.n100 + ' >350 ' + steadyNew.n350 + ' rms ' + steadyNew.rms + ' maxErr ' + steadyNew.maxErr);
  say('LOG                       OLD back ' + steadyOld.back + ' fwd ' + steadyOld.fwd + ' jumps>50 ' + steadyOld.n50 + ' >100 ' + steadyOld.n100 + ' >350 ' + steadyOld.n350 + ' rms ' + steadyOld.rms + ' maxErr ' + steadyOld.maxErr);
  say('LOG   after seek (10 s)   NEW back ' + afterNew.back + ' fwd ' + afterNew.fwd + ' jumps>50 ' + afterNew.n50 + ' settle(<100ms) ' + settle(samples, seekT, 'est', 100) + ' ms settle(<50ms) ' + settle(samples, seekT, 'est', 50) + ' ms | OLD back ' + afterOld.back + ' settle(<100ms) ' + settle(samples, seekT, 'old', 100) + ' ms');
  say('LOG   NEW jumps >100 ms (t s: ms, buffer size, odd held): ' + (jumps.length ? jumps.map(function (j) { return j.t + ':' + (j.jump > 0 ? '+' : '') + j.jump + '/' + j.offs + (j.odd ? '*' : ''); }).join(' ') : 'none'));
  return { steadyNew: steadyNew, steadyOld: steadyOld, jumps: jumps };
}
(async function () {
  try {
    await run('M1 rtt U(0,300) 5% spikes 800, start lat 350, seek at 30 s lat 300', { startLat: 350, seekAt: 30000, seekTo: 20000, seekLat: 300, dur: 60000, seed: 12345 });
    model.spike = 0.2; await run('M1b 20% spikes', { startLat: 350, seekAt: 30000, seekTo: 20000, seekLat: 300, dur: 60000, seed: 777 });
    model.spike = 0.05; model.stale = 0.3; await run('M2 as M1 + 30% stale device reports (0-1000 ms)', { startLat: 350, seekAt: 30000, seekTo: 20000, seekLat: 300, dur: 60000, seed: 999 });
    model.stale = 0.15; model.staleMs = 600; await run('M2b 15% stale up to 600 ms', { startLat: 350, seekAt: 30000, seekTo: 20000, seekLat: 300, dur: 60000, seed: 4242 });
    model.stale = 0; model.spike = 0; await run('M0 rtt U(0,300) no spikes (best case)', { startLat: 350, seekAt: 30000, seekTo: 20000, seekLat: 300, dur: 60000, seed: 31337 });
    // long steady run for rare events: 10 minutes of M1
    model.spike = 0.05; var r = await run('M1 long, 600 s', { startLat: 350, seekAt: 590000, seekTo: 20000, seekLat: 300, dur: 600000, seed: 2024 });
    // the two-odd rule by hand: a clean buffer, then two stale readings in a row, then clean again
    sp.offs = [100, 105, 98, 102, 101]; sp.odd = null; var seq = [500, 505, 100, 103, 99], outs = seq.map(function (o) { return d.spOffsetSample(o); });
    say('LOG   spOffsetSample with buffer ~100 fed 500,505,100,103,99 -> ' + outs.join(', ') + ' (two agreeing strays move the clock by ' + Math.round(outs[1] - 100) + ' ms, then it takes two clean readings to come back)');
    say('DONE');
  } catch (e) { say('FAIL ' + (e && e.stack || e)); }
})();
