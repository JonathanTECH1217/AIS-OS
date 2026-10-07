// Page side of the listener, against a fake /listen server: serverListenPoll (since/skip, mid padding, midOk, restart,
// reset race), listenSongStart, voiceCurve/beatCurve gates, listenStop's final liveLock, liveLock's gates.
// PASS on a line marked BUG means the suspected bug was reproduced.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var L = d.listen;
var FS = { t0: 1000, frames: [], mid: [], running: true, sendMid: true };
function grow(n, base) { for (var i = 0; i < n; i++) { var k = FS.frames.length; FS.frames.push(+(base + k * 0.001).toFixed(3)); FS.mid.push(+(base + 0.5 + k * 0.001).toFixed(3)); } }
function answer(since, snap) { snap = snap || FS; var o = { ok: true, running: snap.running, t0: snap.t0, fps: 100, since: since, frames: snap.frames.slice(since), err: '' }; if (snap.sendMid) o.mid = snap.mid.slice(since); return o; }
var pending = [], log = [];
var realFetch = window.fetch;
window.fetch = function (url, opts) {
  url = String(url);
  if (url.indexOf('/listen/frames') === 0) {
    var since = +url.split('since=')[1]; log.push(since);
    return new Promise(function (res) { pending.push({ since: since, res: function (obj) { res({ ok: true, json: function () { return Promise.resolve(obj); } }); } }); });
  }
  if (url.indexOf('/listen/') === 0) return Promise.resolve({ ok: true, json: function () { return Promise.resolve({ ok: true }); } });
  return realFetch(url, opts);
};
function flush() { var p = pending.splice(0); p.forEach(function (q) { q.res(answer(q.since)); }); }
function sameArr(a, b) { if (a.length !== b.length) return false; for (var i = 0; i < a.length; i++) if (a[i] !== b[i]) return false; return true; }
function eq() { return L.env.length === L.mid.length; }
function reset() { L.env = []; L.mid = []; L.midOk = false; L.t0 = null; L.pairs = []; L.on = true; L.mode = 'server'; L.latency = 0.05; L.timer = null; L.live = null; L.poll = null; L.auto = false; }
function song(n) { reset(); FS = { t0: 1000, frames: [], mid: [], running: true, sendMid: true }; var env = []; for (var i = 0; i < n; i++) env.push(0.4); function bump(t, amp, decay) { var k0 = Math.round(t * 100); for (var k = 0; k < decay && k0 + k < n; k++) { var v = k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2)); if (v > env[k0 + k]) env[k0 + k] = v; } } for (var t = 1.0; t < n / 100 - 0.5; t += 0.5) bump(t, 2.2, 12); FS.frames = env; FS.mid = env.slice(); }
(async function () {
  try {
    check('hook has serverListenPoll/listenStop/liveLock', typeof d.serverListenPoll === 'function' && typeof d.listenStop === 'function' && typeof d.liveLock === 'function');
    reset(); d.cur().audio = null;
    var p;
    // T1 basic
    grow(100, 0.4); p = d.serverListenPoll(); flush(); await p;
    check('T1 basic poll: 100 env, 100 mid, t0 1000, midOk true', L.env.length === 100 && L.mid.length === 100 && L.t0 === 1000 && L.midOk === true, L.env.length + '/' + L.mid.length + ' t0 ' + L.t0 + ' midOk ' + L.midOk);
    // T2 overlapping polls with the same since
    grow(50, 0.4);
    var p1 = d.serverListenPoll(), p2 = d.serverListenPoll();
    check('T2 both polls asked since=100', log.slice(-2).join(',') === '100,100', log.slice(-2).join(','));
    var q1 = pending.shift(); q1.res(answer(q1.since)); await p1;
    grow(10, 0.4);
    var q2 = pending.shift(); q2.res(answer(q2.since)); await p2;
    check('T2 overlap same since: no duplicates, env and mid == server (160)', sameArr(L.env, FS.frames) && sameArr(L.mid, FS.mid), L.env.length + ' env vs ' + FS.frames.length + ' server; mid ' + L.mid.length);
    var p3 = d.serverListenPoll(), p4 = d.serverListenPoll();
    grow(20, 0.4);
    var q4 = pending.pop(); q4.res(answer(q4.since)); await p4;
    var q3 = pending.pop(); q3.res(answer(q3.since, { t0: FS.t0, running: true, sendMid: true, frames: FS.frames.slice(0, 165), mid: FS.mid.slice(0, 165) })); await p3;
    check('T2b a stale shorter answer after a fuller one: still == server (180)', sameArr(L.env, FS.frames) && sameArr(L.mid, FS.mid) && L.env.length === 180, L.env.length + ' ' + L.mid.length);
    // T3 answer without mid (older serve.py)
    reset(); FS = { t0: 1000, frames: [], mid: [], running: true, sendMid: false }; grow(600, 0.4); L.pairs = [-980];
    p = d.serverListenPoll(); flush(); await p;
    check('T3 no mid: env 600, mid 600 (padded), midOk false', L.env.length === 600 && L.mid.length === 600 && L.midOk === false, L.env.length + '/' + L.mid.length + ' midOk ' + L.midOk);
    check('T3 padded mid is all zeros', L.mid.every(function (v) { return v === 0; }));
    check('T3 voiceCurve() refuses (null) while midOk is false', d.voiceCurve() === null, String(d.voiceCurve()));
    check('T3 beatCurve() null under 15 s', d.beatCurve() === null);
    FS.sendMid = true; grow(1000, 0.4); p = d.serverListenPoll(); flush(); await p;
    var vc = d.voiceCurve();
    check('T3b mid arrives later: midOk true, env==mid length 1600', L.midOk === true && L.env.length === 1600 && L.mid.length === 1600, L.env.length + '/' + L.mid.length);
    check('T3b BUG: voiceCurve() now offers a curve whose first 600 frames are padded zeros', !!(vc && vc.env.length === 1600 && vc.env[0] === 0 && vc.env[599] === 0 && vc.env[600] > 0), vc ? ('len ' + vc.env.length + ' start ' + vc.start + ' [0]=' + vc.env[0] + ' [600]=' + vc.env[600]) : 'null');
    var bc = d.beatCurve();
    check('T3b beatCurve() offered at 1600 frames, start = listenSongStart()', !!(bc && Math.abs(bc.start - d.listenSongStart()) < 1e-9 && bc.on.length === 1600), JSON.stringify(bc && { start: bc.start, n: bc.on.length, st: d.listenSongStart() }));
    // T4 server restarted (since ahead of the server's count)
    var oldT0 = L.t0; FS = { t0: 2000, frames: [], mid: [], running: true, sendMid: true }; grow(50, 0.9);
    p = d.serverListenPoll(); flush(); await p;
    check('T4 after a server restart: nothing appended, t0 kept stale (' + oldT0 + ', server says 2000)', L.env.length === 1600 && L.t0 === oldT0, 'env ' + L.env.length + ' t0 ' + L.t0);
    grow(1600, 0.9); p = d.serverListenPoll(); flush(); await p;
    check('T4 BUG: the new capture is appended to the old env under the old t0 once the server passes the old count', L.env.length === 1650 && L.t0 === oldT0 && L.env[1600] === FS.frames[1600], 'env ' + L.env.length + ' t0 ' + L.t0 + ' env[1600]=' + L.env[1600] + ' server[1600]=' + FS.frames[1600]);
    check('T4 invariant env.length === mid.length', eq());
    // T5 reset race: an answer in flight from before a reset
    var pOld = d.serverListenPoll(); var qOld = pending.shift();
    L.env = []; L.mid = []; L.midOk = false; L.t0 = null; L.pairs = [];
    FS = { t0: 3000, frames: [], mid: [], running: true, sendMid: true };
    qOld.res({ ok: true, running: true, t0: 1000, fps: 100, since: 1650, frames: [0.5, 0.5], mid: [0.1, 0.1], err: '' }); await pOld;
    check('T5 stale answer after a reset: its frames are dropped', L.env.length === 0 && L.mid.length === 0, L.env.length + '/' + L.mid.length);
    check('T5 BUG: but its old t0 (1000) was taken before the skip check', L.t0 === 1000, 't0 = ' + L.t0);
    grow(30, 0.4); p = d.serverListenPoll(); flush(); await p;
    check('T5 BUG: the new capture (server t0 3000) then runs under t0 1000', L.t0 === 1000 && L.env.length === 30, 't0 ' + L.t0 + ' env ' + L.env.length);
    // T6 listenSongStart
    L.t0 = 1000; L.pairs = [30.5, 30.4, 30.6, 45.0]; L.latency = 0.12;
    check('T6 listenSongStart = t0 + median(pairs) - latency = 1030.48 (upper median of 4; outlier 45 ignored)', Math.abs(d.listenSongStart() - 1030.48) < 1e-6, String(d.listenSongStart()));
    L.pairs = []; check('T6 no pairs -> null', d.listenSongStart() === null);
    L.pairs = [1]; L.t0 = null; check('T6 no t0 -> null', d.listenSongStart() === null);
    L.latency = null; L.t0 = 1000; check('T6 latency null counts as 0', d.listenSongStart() === 1001);
    // T7 running=false in an answer stops listening
    reset(); FS = { t0: 4000, frames: [], mid: [], running: false, sendMid: true }; grow(10, 0.4);
    p = d.serverListenPoll(); flush(); await p;
    check('T7 running=false -> listenStop (on false)', L.on === false, 'on ' + L.on);
    // T8 listenStop: final liveLock only when lined (synthetic 20 s song, kicks every 0.5 s from 1.0 s)
    var s = d.S(); s.audio = null; s.time = '4/4'; s.bpm = 100; s.spotify = null;
    song(2000); L.pairs = [-980]; L.latency = 0; p = d.serverListenPoll(); flush(); await p;
    var sa = d.sheetAudio(); sa.lined = false; sa.locked = false; sa.beats = null; sa.offsetSec = 21.0;
    d.listenStop(); sa = d.sheetAudio();
    check('T8 listenStop, not lined: no lock; on=false; timers null', !sa.locked && L.on === false && L.timer === null && L.poll === null && L.live === null, 'locked ' + sa.locked + ' on ' + L.on);
    song(2000); L.pairs = [-980]; L.latency = 0; p = d.serverListenPoll(); flush(); await p;
    sa = d.sheetAudio(); sa.lined = true; sa.locked = false; sa.beats = null; sa.offsetSec = 21.0;
    d.listenStop(); sa = d.sheetAudio(); s = d.S();
    check('T8 listenStop, lined: final liveLock locks to the listener beats', !!(sa.locked && sa.beats && sa.beats.length > 10), 'locked ' + sa.locked + ' beats ' + (sa.beats && sa.beats.length) + ' first ' + (sa.beats && sa.beats[0]) + ' bpm ' + s.bpm + ' fit ' + JSON.stringify(sa.lockFit));
    check('T8 first beat at 21.0 s (frame 100 under t0 + median(pairs))', !!(sa.beats && Math.abs(sa.beats[0] - 21.0) < 0.03), String(sa.beats && sa.beats[0]));
    check('T8 bpm read as 120', Math.abs(s.bpm - 120) <= 1, String(s.bpm));
    // T9 liveLock gates
    song(1400); L.pairs = [-980]; L.latency = 0; p = d.serverListenPoll(); flush(); await p; sa = d.sheetAudio(); sa.locked = false; sa.beats = null; sa.lined = true;
    d.liveLock(); check('T9 liveLock under 15 s: nothing', !d.sheetAudio().locked);
    song(2000); L.pairs = []; p = d.serverListenPoll(); flush(); await p; sa = d.sheetAudio(); sa.locked = false; sa.beats = null;
    d.liveLock(); check('T9 liveLock without pairs: nothing', !d.sheetAudio().locked);
    L.pairs = [-980]; L.latency = 0; d.cur().audio = { onset: new Float32Array(3000), voice: null, low: null, el: null, duration: 30, name: 'f' };
    d.liveLock(); check('T9 liveLock with an attached file: nothing', !d.sheetAudio().locked);
    d.cur().audio = null; d.liveLock(); check('T9 liveLock otherwise locks (quiet, not final)', !!d.sheetAudio().locked, 'beats ' + (d.sheetAudio().beats && d.sheetAudio().beats.length));
    // T10 pairs across a pause: env keeps growing, the song's clock does not; the two halves disagree
    L.t0 = 1000; L.latency = 0; L.pairs = [];
    for (var i = 0; i < 10; i++) L.pairs.push(20 - 1000);          // 5 s playing: song clock = wall - 980
    for (i = 0; i < 12; i++) L.pairs.push(20 - 1000 - 30);         // after a 30 s pause: song clock = wall - 1010
    check('T10 pairs across a pause: median takes the bigger half (start 20 -> -10), first half misplaced by 30 s', d.listenSongStart() === -10, String(d.listenSongStart()));
    // T11 liveLock every 5 s while the song plays: the grid is rebuilt each time, so the song-time -> slot map moves
    song(2000); L.pairs = [-980]; L.latency = 0; p = d.serverListenPoll(); flush(); await p;
    sa = d.sheetAudio(); sa.lined = true; sa.locked = false; sa.beats = null; sa.offsetSec = 21.0;
    d.liveLock(); var g1 = d.slotOfSong(45.0), g1b = d.slotOfSong(48.0), g1c = d.slotOfSong(30.0), b1 = d.sheetAudio().beats.slice(0, 2), bpm1 = d.S().bpm, n1 = d.sheetAudio().beats.length;
    var env = FS.frames, n = 3000; while (env.length < n) env.push(0.4);
    (function () { function bump(t, amp, decay) { var k0 = Math.round(t * 100); for (var k = 0; k < decay && k0 + k < n; k++) { var v = k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2)); if (v > env[k0 + k]) env[k0 + k] = v; } } for (var t = 20.0; t < 29.5; t += 0.52) bump(t, 2.2, 12); })();
    FS.mid = env.slice(); p = d.serverListenPoll(); flush(); await p;
    d.liveLock(); var g2 = d.slotOfSong(45.0), g2b = d.slotOfSong(48.0), g2c = d.slotOfSong(30.0), b2 = d.sheetAudio().beats.slice(0, 2), bpm2 = d.S().bpm, n2 = d.sheetAudio().beats.length;
    say('LOG T11 liveLock again after 10 s more (band drifts to 0.52 s beats from song 40 s): slotOfSong(45 s) ' + g1.toFixed(2) + ' -> ' + g2.toFixed(2) + ' (' + ((g2 - g1) / d.slotsPerBeat('4/4')).toFixed(2) + ' beats); slotOfSong(48 s) ' + g1b.toFixed(2) + ' -> ' + g2b.toFixed(2) + '; slotOfSong(30 s) ' + g1c.toFixed(2) + ' -> ' + g2c.toFixed(2) + '; bpm ' + bpm1 + ' -> ' + bpm2 + '; beats ' + n1 + ' -> ' + n2 + '; bar 1 ' + b1[0] + ' -> ' + b2[0]);
    check('T11 BUG: a re-lock moves the playhead slot for the same song time (the part heard since the last lock)', Math.abs(g2 - g1) > 0.5 || Math.abs(g2b - g1b) > 0.5, 'd45 ' + (g2 - g1).toFixed(2) + ' d48 ' + (g2b - g1b).toFixed(2) + ' d30 ' + (g2c - g1c).toFixed(2));
    check('T-final invariant env.length === mid.length', eq());
  } catch (e) { say('FAIL exception: ' + (e && e.stack || e)); }
  window.fetch = realFetch;
})();
