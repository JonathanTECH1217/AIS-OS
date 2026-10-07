// place-test2: Place words under each condition, what it wrote and what the toast said.
var BLURRY_LRC = "[00:23.09] Everything's so blurry and everyone's so fake\n[00:28.96] And everybody's empty and everything is so messed up\n[00:34.96] Preoccupied without you, I cannot live at all\n[00:41.24] My whole world surrounds you, I stumble and I crawl\n[00:47.21] You could be my someone, you could be my scene\n[00:53.37] You know that I'll protect you from all of the obscene\n[00:59.31] I wonder what you're doing, imagine where you are\n[01:05.42] There's oceans in between us, but that's not very far\n[01:12.94] Can you take it all away?\n[01:15.94] Can you take it all away?\n[01:19.01] Well, you shoved it in my face\n[01:22.25] This pain you gave to me\n[01:25.18] Can you take it all away?\n[01:28.23] Can you take it all away?\n[01:31.16] Well, you shoved it in my face\n[01:36.25] Everyone is changing, there's no one left that's real\n[01:42.19] So make up your own ending and let me know just how you feel\n[01:48.22] 'Cause I am lost without you, I cannot live at all\n[01:54.46] My whole world surrounds you, I stumble then I crawl\n[02:00.67] You could be my someone, you could be my scene\n[02:06.55] You know that I will save you from all of the unclean\n[02:12.76] I wonder what you're doing, I wonder where you are\n[02:18.70] There's oceans in between us, but that's not very far\n[02:26.18] Can you take it all away?\n[02:29.33] Can you take it all away?\n[02:32.30] Well, you shoved it in my face\n[02:35.57] This pain you gave to me\n[02:38.45] Can you take it all away?\n[02:41.52] Can you take it all away?\n[02:44.40] Well, you shoved it in my face\n[02:47.95] This pain you gave to me\n[02:51.16] \n[03:01.91] Nobo-, nobody told me what you thought\n[03:06.17] Nobody told me what to say\n[03:09.11] Everyone showed you where to turn\n[03:12.36] Told you when to run away\n[03:15.48] Nobody told you where to hide\n[03:18.49] Nobody told you what to say\n[03:21.57] Everyone showed you where to turn\n[03:24.30] Showed you when to run away\n[03:27.13] Can you take it all away?\n[03:30.21] Can you take it all away?\n[03:33.21] Well, you shoved it in my face\n[03:36.48] This pain you gave to me\n[03:39.30] Can you take it all away?\n[03:42.35] Can you take it all away?\n[03:45.45] Well, you shoved it in my face\n[03:48.85] This pain you gave to me, no\n[03:53.59] \n[03:56.55] This pain you gave to me\n[03:59.80] \n[04:08.78] This pain you gave to me\n[04:12.54] \n[04:19.52] Can you take it all, take it all away?\n[04:24.32] This pain you gave to me\n[04:27.03] Can you take it all away?\n[04:30.29] This pain you gave to me\n[04:32.93] Can you take it all away?\n[04:36.10] This pain you gave to me\n[04:37.40] ";
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function r2(x) { return Math.round(x * 100) / 100; }
function r3(x) { return Math.round(x * 1000) / 1000; }
var fps = 100;
var toasts = []; (function () { var t = document.getElementById('toast'); new MutationObserver(function () { toasts.push(t.textContent); }).observe(t, { childList: true, characterData: true, subtree: true }); })();
var realFetch = window.fetch, answer = null, fetchCount = 0;
window.fetch = function (url, opts) { if (String(url).indexOf('/lyrics') === 0) { fetchCount++; return Promise.resolve(answer()); } return realFetch(url, opts); };
function jsonAnswer(body, status) { return { ok: !status || status < 400, status: status || 200, headers: new Headers({ 'content-type': 'application/json' }), json: function () { return Promise.resolve(body); } }; }
function htmlAnswer() { return { ok: true, status: 200, headers: new Headers({ 'content-type': 'text/html; charset=utf-8' }), json: function () { return Promise.reject(new SyntaxError('Unexpected token <')); } }; }
var LRC8 = BLURRY_LRC.split('\n').slice(0, 8).join('\n') + '\n[01:12.94] \n';
function lookup(lrcText) { return function () { return jsonAnswer({ ok: true, synced: lrcText, plain: '', duration: 304, track: 'Blurry', artist: 'Puddle of Mudd' }); }; }
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), f; if (k0 < env.length && env[k0] < 1.4) env[k0] = 1.4; for (f = k0 + 1; f < k1 && f < env.length; f++) if (env[f] < 2.3) env[f] = 2.3; }
function fakeEl(dur) { return { paused: true, currentTime: 0, duration: dur, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }; }
function fresh(trackId, opts) { opts = opts || {}; var s = d.S(); s.time = '4/4'; s.bpm = 100; s.audio = null; s.lines = []; s.lyrics = ''; s.title = opts.title || ''; s.filled = null; s.spotify = trackId ? { trackId: trackId, name: 'Blurry · Puddle of Mudd', durationMs: 304000, title: 'Blurry', artist: 'Puddle of Mudd', album: '' } : null; d.cur().audio = null; d.cur().undo = []; d.cur().redo = []; var L = d.listen; L.env = []; L.mid = []; L.midOk = false; L.t0 = null; L.pairs = []; L.latency = null; return s; }
function nLines() { return d.S().lines.filter(function (l) { return l.kind === 'line'; }).length; }
function brief(label) { var s = d.S(), sa = s.audio || {}; return label + ': lines ' + nLines() + ' bpm ' + s.bpm + ' time ' + s.time + ' offsetSec ' + sa.offsetSec + ' lined ' + sa.lined + ' locked ' + sa.locked + ' beats ' + (sa.beats ? sa.beats.length : 0) + ' filled ' + JSON.stringify(s.filled) + ' undo ' + d.cur().undo.length + ' title "' + s.title + '"'; }
function lastToast() { return toasts[toasts.length - 1] || ''; }
function placements(n) { var s = d.S(), spb = d.slotsPerBar(s.time), out = [], c = 0; s.lines.forEach(function (l, li) { if (l.kind !== 'line' || c >= n) return; c++; var base = d.barOrdinal(s, li, 0) * spb; out.push('bar' + (base / spb + 1) + '/' + l.bars + ': ' + d.sortedSyls(l).map(function (y) { return y.text + '@' + (base + y.pos) + 'x' + d.lenSlots(y); }).join(' ')); }); return out.join(' || '); }
// the listener's data for the 8 lines: a rock beat at 120 from 0.75 s (kick 1 loud and 3, snare 2 and 4 louder in the
// full band, hats on the eighths; the listener has no low band), the voice sung as in test 1
var DUR2 = 80, N2 = fps * DUR2, T0b = 0.75, BEATb = 0.5;
function listenerData() { var full = new Float32Array(N2), mid = new Float32Array(N2), i, k = 0, t; for (i = 0; i < N2; i++) { full[i] = 0.5; mid[i] = 0.4; } for (t = T0b; t < DUR2 - 1; t += BEATb, k++) { var pos = k % 4; if (pos === 0) bump(full, t, 2.0, 10); else if (pos === 2) bump(full, t, 1.9, 10); else bump(full, t, 2.5, 8); bump(full, t + BEATb / 2, 1.0, 4); } var lrc = d.parseLrc(LRC8), sungOn = []; lrc.forEach(function (l) { if (!l.text) return; var K = d.syllableTexts(l.text).length; for (var q = 0; q < K; q++) { var on = l.t + 0.2 + q * 0.25; sing(mid, on, on + 0.2); sungOn.push(on); } }); return { full: full, mid: mid, sungOn: sungOn }; }
var LD = listenerData();
function hear() { var L = d.listen; L.env = Array.prototype.slice.call(LD.full); L.mid = Array.prototype.slice.call(LD.mid); L.midOk = true; L.t0 = 0; L.pairs = [0, 0, 0]; L.latency = 0; L.fps = 100; }
function beatPos(sec) { return r2((((sec - T0b) / BEATb) % 4 + 4) % 4); }
function sylErrors() { var s = d.S(), spb = d.slotsPerBar(s.time), errs = [], q = 0; s.lines.forEach(function (l, li) { if (l.kind !== 'line') return; var base = d.barOrdinal(s, li, 0) * spb; d.sortedSyls(l).forEach(function (y) { if (y.rest) return; errs.push(r2(d.songOfSlot(base + y.pos) - LD.sungOn[q++])); }); }); return errs; }
var seq = Promise.resolve();
function step(name, fn) { seq = seq.then(function () { say('LOG --- ' + name); var t0 = toasts.length; return Promise.resolve(fn()).then(function () { toasts.slice(t0).forEach(function (x, q) { say('LOG   toast ' + (q + 1) + ' (' + x.length + ' chars): ' + x); }); }); }).catch(function (e) { say('FAIL ' + name + ' threw: ' + (e && e.stack || e)); }); }

step('(a) Spotify link, nothing heard (no listener data)', function () {
  fresh('blurry-a'); answer = lookup(LRC8);
  return d.autoPlaceWords().then(function () {
    var s = d.S(), sa = s.audio; say('LOG ' + brief('after (a)'));
    check('(a) words written: 8 lines', nLines() === 8, nLines() + ' lines');
    check('(a) tempo and time kept (100, 4/4)', s.bpm === 100 && s.time === '4/4', s.bpm + ' ' + s.time);
    check('(a) filled is null (can be placed again once heard)', s.filled === null, JSON.stringify(s.filled));
    check('(a) toast says the song has not been heard', lastToast().indexOf('has not been heard yet') >= 0);
    check('(a) title from the lookup', s.title === 'Puddle of Mudd - Blurry', s.title);
    check('(a) a blind fill marks bar 1 as lined up (sa.lined) at the first stamp', sa.lined === true && Math.abs(sa.offsetSec - 23.09) < 0.01, 'lined ' + sa.lined + ' offsetSec ' + sa.offsetSec);
    say('LOG (a) placements: ' + placements(2));
  });
});
step('(b) then heard: listener data present, second press', function () {
  hear(); var bc = d.beatCurve(), vc = d.voiceCurve();
  check('(b) beatCurve and voiceCurve present', !!bc && !!vc, 'bc ' + !!bc + ' vc ' + !!vc);
  var bpm = d.tempoOf(bc.on, bc.fps), beats = d.trackBeats(bc.on, bc.fps, bpm), m = d.meterOf(bc.on, bc.low, bc.fps, beats, 60 / bpm, null);
  say('LOG (b) by hand: tempoOf ' + bpm + '; meterOf phase ' + m.phase + ' (0 = the kick on beat 1, 1 and 3 = the snare) phaseSure ' + r2(m.phaseSure) + ' sure ' + r2(m.sure) + ' time ' + m.time + '; the "low band" meterOf gets on the listener path is ' + (bc.low === null ? 'null' : (bc.low === bc.on ? 'the onset curve' : 'the full-band loudness itself')));
  var m2 = d.meterOf(bc.on, null, bc.fps, beats, 60 / bpm, null); say('LOG (b) meterOf with low = null instead: phase ' + m2.phase + ' phaseSure ' + r2(m2.phaseSure));
  return d.autoPlaceWords().then(function () {
    var s = d.S(), sa = s.audio; say('LOG ' + brief('after (b)'));
    check('(b) second press fills with the audio: filled set', !!(s.filled && s.filled.key === 'spotify:blurry-a'), JSON.stringify(s.filled));
    check('(b) tempo read (120)', Math.abs(s.bpm - 120) <= 1, String(s.bpm));
    check('(b) locked', !!sa.locked, 'fit ' + JSON.stringify(sa.lockFit));
    check('(b) bar 1 on a downbeat (0.75 + 2k s; the one before the first sung word is 22.75)', beatPos(sa.offsetSec) === 0, 'offsetSec ' + sa.offsetSec + ' = beat position ' + beatPos(sa.offsetSec) + ' in the bar (0 = beat 1)');
    check('(b) toast says the tempo was read', lastToast().indexOf('read from the song') >= 0, lastToast().slice(0, 120));
    check('(b) toast says the syllables are as long as sung', lastToast().indexOf('as long as it is sung') >= 0);
    var errs = sylErrors(), big = errs.filter(function (e) { return Math.abs(e) > 0.125; });
    check('(b) syllables within a sixteenth (0.125 s at 120) of the sung onset', big.length === 0, big.length + ' of ' + errs.length + ' off by more; errors ' + errs.slice(0, 20).join(' '));
    say('LOG (b) placements: ' + placements(2));
  });
});
step('(c) same song again', function () {
  var before = JSON.stringify(d.S().lines), undoN = d.cur().undo.length, fc = fetchCount;
  return d.autoPlaceWords().then(function () {
    check('(c) refused with the "already on the sheet" toast', lastToast().indexOf('already on the sheet') >= 0, lastToast());
    check('(c) nothing changed, no undo step, no lookup', JSON.stringify(d.S().lines) === before && d.cur().undo.length === undoN && fetchCount === fc, 'undo ' + d.cur().undo.length + ' vs ' + undoN + ', fetches ' + (fetchCount - fc));
  });
});
step('(d) undo after (a) then (b)', function () {
  d.undo(); var s = d.S(); say('LOG ' + brief('after one undo'));
  check('(d) one undo clears filled (back to the blind fill: words still there, tempo 100)', !s.filled && nLines() === 8 && s.bpm === 100 && !(s.audio && s.audio.locked), 'filled ' + JSON.stringify(s.filled) + ' lines ' + nLines() + ' bpm ' + s.bpm);
  d.undo(); var s2 = d.S(); say('LOG ' + brief('after two undos'));
  check('(d) the second undo takes the words away too', nLines() === 0 && !s2.filled, 'lines ' + nLines());
  check('(d) bpm box shows 100 again', document.getElementById('bpm').value === '100', document.getElementById('bpm').value);
});
step("(b') a fresh sheet, same listener data, no blind fill first", function () {
  fresh('blurry-b2'); hear();
  return d.autoPlaceWords().then(function () {
    var s = d.S(), sa = s.audio; say('LOG ' + brief("after (b')"));
    check("(b') bar 1 on a downbeat", beatPos(sa.offsetSec) === 0, 'offsetSec ' + sa.offsetSec + ' = beat position ' + beatPos(sa.offsetSec) + ' (0 = beat 1, 1 and 3 = the snare)');
    check("(b') tempo 120", Math.abs(s.bpm - 120) <= 1, String(s.bpm));
    var errs = sylErrors(), big = errs.filter(function (e) { return Math.abs(e) > 0.125; });
    check("(b') syllables within a sixteenth of the sung onset", big.length === 0, big.length + ' of ' + errs.length + ' off by more; errors ' + errs.slice(0, 20).join(' '));
    say("LOG (b') placements: " + placements(2));
  });
});
step('(e) sheet already locked (an earlier lock, for another song, at 120 on a 76 bpm track)', function () {
  var s = fresh('blurry-e'), full = new Float32Array(N2), low = new Float32Array(N2), voice = new Float32Array(N2), i, k = 0, t;
  for (i = 0; i < N2; i++) { full[i] = 0.5; low[i] = 0.4; voice[i] = 0.4; }
  for (t = 1.0; t < DUR2 - 1; t += 60 / 76, k++) { var pos = k % 4; if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else if (pos === 2) { bump(low, t, 1.8, 12); bump(full, t, 1.9, 10); } else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); } }
  d.parseLrc(LRC8).forEach(function (l) { if (!l.text) return; var K = d.syllableTexts(l.text).length; for (var q = 0; q < K; q++) sing(voice, l.t + 0.2 + q * 0.25, l.t + 0.4 + q * 0.25); });
  d.cur().audio = { el: fakeEl(DUR2), url: '', name: 'Puddle of Mudd - Blurry.wav', peaks: null, duration: DUR2, onset: d.risesOf(full), voice: voice, low: low, blob: false };
  var beats = []; for (t = 22.75; t < DUR2; t += 0.5) beats.push(r3(t));
  s.bpm = 120; s.audio = { offsetSec: 22.75, lined: true, name: '', assetId: null, forTrack: 'some-other-song', beats: beats, locked: true, lockFit: { onHit: 100, avgMs: 0 } };
  var beatsBefore = JSON.stringify(beats);
  return d.autoPlaceWords().then(function () {
    var s1 = d.S(), sa = s1.audio; say('LOG ' + brief('after (e)'));
    check('(e) "Kept the lock" path taken', lastToast().indexOf('Kept the lock at 120') >= 0, lastToast().slice(0, 140));
    check('(e) the old lock is kept as is (bpm 120, beats and bar 1 unchanged) although forTrack names another song and the track runs at 76', s1.bpm === 120 && JSON.stringify(sa.beats) === beatsBefore && sa.offsetSec === 22.75, 'bpm ' + s1.bpm + ' offsetSec ' + sa.offsetSec + ' beats same ' + (JSON.stringify(sa.beats) === beatsBefore));
    check('(e) filled set (the grid counts as heard)', !!s1.filled, JSON.stringify(s1.filled));
  });
});
step('(f) /lyrics answers HTML (an older local server)', function () {
  fresh('blurry-f'); answer = htmlAnswer; var undoN = d.cur().undo.length;
  return d.autoPlaceWords().then(function () { check('(f) stale-server toast', lastToast().indexOf('older Dictation Sheet server') >= 0, lastToast()); check('(f) nothing written, no undo step', nLines() === 0 && d.cur().undo.length === undoN); });
});
step('(g) /lyrics 503 with ok:false and why', function () {
  fresh('blurry-g'); answer = function () { return jsonAnswer({ ok: false, why: 'lyrics service unavailable' }, 503); };
  return d.autoPlaceWords().then(function () { check('(g) toast carries the why', lastToast() === 'No timed lyrics found (lyrics service unavailable). Tap words places them by hand.', lastToast()); check('(g) nothing written', nLines() === 0); });
});
step('(h) synced lyrics with only one line', function () {
  fresh('blurry-h'); answer = lookup('[00:10.00] Only one line is here\n');
  return d.autoPlaceWords().then(function () {
    check('(h) one timed line is refused as "empty"', lastToast().indexOf('timed lyrics are empty') >= 0, lastToast()); check('(h) nothing written', nLines() === 0);
    fresh('blurry-h2'); answer = lookup('[00:10.00] Only one line is here\n[00:14.00] \n');
    return d.autoPlaceWords().then(function () { check('(h2) one line plus a blank stamp goes through', nLines() === 1, 'lines ' + nLines() + '; ' + placements(1)); });
  });
});
step('(i) headers and blank lines in the LRC', function () {
  fresh('blurry-i'); var text = '[ar:Tester]\n[ti:Header Song]\n[00:05.00] [Verse 1]\n[00:05.50] First line of the verse\n\n[00:09.00] Second line of the verse\n[00:12.00]\n[00:15.00] [Chorus]\n[00:15.20] Third line is the chorus\n[00:20.00][00:30.00] Repeated line twice\n[00:35.00] \n';
  answer = lookup(text); say('LOG (i) parseLrc: ' + JSON.stringify(d.parseLrc(text).map(function (l) { return l.t + ':' + l.text; })));
  return d.autoPlaceWords().then(function () {
    var s = d.S(), texts = s.lines.map(function (l) { return l.kind === 'header' ? '[' + l.text + ']' : l.syllables.map(function (y) { return y.text; }).join('|'); });
    say('LOG (i) lines: ' + JSON.stringify(texts));
    check('(i) 5 lines of words, no headers on the sheet (section names in the LRC are dropped), blank stamps end windows', s.lines.length === 5 && s.lines.every(function (l) { return l.kind === 'line'; }), s.lines.length + ' lines, ' + s.lines.filter(function (l) { return l.kind === 'header'; }).length + ' headers');
    check('(i) the two-stamp line is placed twice, in order', texts[3] === texts[4], texts[3] + ' / ' + texts[4]);
    say('LOG (i) placements: ' + placements(5));
  });
});
step('(j) typed words that differ from the lookup (replace + merge)', function () {
  var s = fresh('blurry-j', { title: 'My Title' });
  d.wordsToNotes("Everything's so blurry and everyone's so fake\nLa la la\nPreoccupied without you, I cannot live at all\n", 'My Title', { noUndo: true, quiet: true });
  var y0 = d.sortedSyls(s.lines[0])[0]; y0.note = 'E4'; y0.sol = 'mi'; y0.len = 'h'; var y2 = d.sortedSyls(s.lines[2])[1]; y2.note = 'G4';
  var undoN = d.cur().undo.length; answer = lookup(LRC8);
  return d.autoPlaceWords().then(function () {
    var s1 = d.S(), lines = s1.lines.filter(function (l) { return l.kind === 'line'; });
    var texts = lines.map(function (l) { return d.sortedSyls(l).map(function (y) { return y.text; }).join(' '); });
    check('(j) the sheet now holds the 8 lookup lines', lines.length === 8, lines.length + ' lines');
    check('(j) "La la la" replaced by lookup line 2', /empty/.test(texts[1]), texts[1]);
    var k0 = d.sortedSyls(lines[0])[0], k2 = d.sortedSyls(lines[2])[1];
    check('(j) a line whose text matches keeps its notes (line 1 syllable 1: note E4, sol mi), its length re-placed', k0.note === 'E4' && k0.sol === 'mi', 'note ' + k0.note + ' sol ' + k0.sol + ' len ' + k0.len + ' = ' + d.lenSlots(k0) + ' slots');
    check('(j) line 3 keeps its note G4', k2.note === 'G4', 'note ' + k2.note);
    check('(j) the title typed by hand is kept', s1.title === 'My Title', s1.title);
    check('(j) one undo step for the whole fill', d.cur().undo.length === undoN + 1, d.cur().undo.length);
    say('LOG (j) placements: ' + placements(3));
  });
});
step('(k) an attached file, pressed before its bands are read', function () {
  fresh(null); d.cur().audio = { el: fakeEl(304), url: '', name: 'Puddle of Mudd - Blurry.mp3', peaks: null, duration: 304, onset: null, voice: null, low: null, blob: false }; answer = lookup(LRC8);
  say('LOG (k) songMeta ' + JSON.stringify(d.songMeta()) + ' songKey ' + d.songKey());
  return d.autoPlaceWords().then(function () { var s = d.S(); say('LOG ' + brief('after (k)')); check('(k) toast: wait for the track to be read; tempo kept', lastToast().indexOf('wait a moment for the attached track') >= 0 && s.bpm === 100, lastToast().slice(0, 160)); check('(k) filled null, so it can be placed again', s.filled === null); });
});
seq.then(function () { window.fetch = realFetch; say('LOG done, ' + fetchCount + ' lookups'); });
