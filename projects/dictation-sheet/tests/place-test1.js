// place-test1: the whole Place words flow on the real Blurry timed lyrics (60 stamps, 55 with words) on a synthetic
// 76 bpm 4/4 drum track (kick 1 loud and 3, snare 2 and 4 louder in the full band, hats on the eighths) with a synthetic
// voice band: each timed line's syllables sung from 0.2 s after its stamp, four a second (0.2 s long, 0.05 s apart).
// Then: state after the fill, the toasts, undo.
var BLURRY_LRC = "[00:23.09] Everything's so blurry and everyone's so fake\n[00:28.96] And everybody's empty and everything is so messed up\n[00:34.96] Preoccupied without you, I cannot live at all\n[00:41.24] My whole world surrounds you, I stumble and I crawl\n[00:47.21] You could be my someone, you could be my scene\n[00:53.37] You know that I'll protect you from all of the obscene\n[00:59.31] I wonder what you're doing, imagine where you are\n[01:05.42] There's oceans in between us, but that's not very far\n[01:12.94] Can you take it all away?\n[01:15.94] Can you take it all away?\n[01:19.01] Well, you shoved it in my face\n[01:22.25] This pain you gave to me\n[01:25.18] Can you take it all away?\n[01:28.23] Can you take it all away?\n[01:31.16] Well, you shoved it in my face\n[01:36.25] Everyone is changing, there's no one left that's real\n[01:42.19] So make up your own ending and let me know just how you feel\n[01:48.22] 'Cause I am lost without you, I cannot live at all\n[01:54.46] My whole world surrounds you, I stumble then I crawl\n[02:00.67] You could be my someone, you could be my scene\n[02:06.55] You know that I will save you from all of the unclean\n[02:12.76] I wonder what you're doing, I wonder where you are\n[02:18.70] There's oceans in between us, but that's not very far\n[02:26.18] Can you take it all away?\n[02:29.33] Can you take it all away?\n[02:32.30] Well, you shoved it in my face\n[02:35.57] This pain you gave to me\n[02:38.45] Can you take it all away?\n[02:41.52] Can you take it all away?\n[02:44.40] Well, you shoved it in my face\n[02:47.95] This pain you gave to me\n[02:51.16] \n[03:01.91] Nobo-, nobody told me what you thought\n[03:06.17] Nobody told me what to say\n[03:09.11] Everyone showed you where to turn\n[03:12.36] Told you when to run away\n[03:15.48] Nobody told you where to hide\n[03:18.49] Nobody told you what to say\n[03:21.57] Everyone showed you where to turn\n[03:24.30] Showed you when to run away\n[03:27.13] Can you take it all away?\n[03:30.21] Can you take it all away?\n[03:33.21] Well, you shoved it in my face\n[03:36.48] This pain you gave to me\n[03:39.30] Can you take it all away?\n[03:42.35] Can you take it all away?\n[03:45.45] Well, you shoved it in my face\n[03:48.85] This pain you gave to me, no\n[03:53.59] \n[03:56.55] This pain you gave to me\n[03:59.80] \n[04:08.78] This pain you gave to me\n[04:12.54] \n[04:19.52] Can you take it all, take it all away?\n[04:24.32] This pain you gave to me\n[04:27.03] Can you take it all away?\n[04:30.29] This pain you gave to me\n[04:32.93] Can you take it all away?\n[04:36.10] This pain you gave to me\n[04:37.40] ";
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function r2(x) { return Math.round(x * 100) / 100; }
function r3(x) { return Math.round(x * 1000) / 1000; }
var fps = 100, DUR = 304, N = fps * DUR, BPM = 76, BEAT = 60 / BPM, T0 = 1.0, SIXTEENTH = BEAT / 4;
var toasts = []; (function () { var t = document.getElementById('toast'); new MutationObserver(function () { toasts.push(t.textContent); }).observe(t, { childList: true, characterData: true, subtree: true }); })();
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
// a crisp sung syllable: attack over one frame, held at 2.3, released at once
function sing(env, on, off) { var k0 = Math.round(on * fps), k1 = Math.round(off * fps), f; if (k0 < env.length && env[k0] < 1.4) env[k0] = 1.4; for (f = k0 + 1; f < k1 && f < env.length; f++) if (env[f] < 2.3) env[f] = 2.3; }
var full = new Float32Array(N), low = new Float32Array(N), voice = new Float32Array(N), i, k = 0, t, downbeats = [];
for (i = 0; i < N; i++) { full[i] = 0.5; low[i] = 0.4; voice[i] = 0.4; }
for (t = T0; t < DUR - 1; t += BEAT, k++) { var pos = k % 4; if (pos === 0) { downbeats.push(t); bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else if (pos === 2) { bump(low, t, 1.8, 12); bump(full, t, 1.9, 10); } else { bump(full, t, 2.5, 8); bump(low, t, 0.9, 6); } bump(full, t + BEAT / 2, 1.0, 4); }
var lrc = d.parseLrc(BLURRY_LRC), sung = [], textExpected = lrc.map(function (l) { return String(l.text || '').trim(); }).filter(Boolean).join('\n');
lrc.forEach(function (l, j) { if (!l.text) return; var K = d.syllableTexts(l.text).length, ons = [], offs = [], q; for (q = 0; q < K; q++) { var on = l.t + 0.2 + q * 0.25; ons.push(on); offs.push(on + 0.2); sing(voice, on, on + 0.2); } sung.push({ j: j, t: l.t, text: l.text, ons: ons, offs: offs }); });
say('LOG lrc entries ' + lrc.length + ', with words ' + sung.length + ', syllables ' + sung.reduce(function (a, x) { return a + x.ons.length; }, 0));
var over = []; sung.forEach(function (sg, n) { var nx = null; for (var q = sg.j + 1; q < lrc.length; q++) if (lrc[q].t - sg.t > 0.05) { nx = lrc[q].t; break; } if (nx !== null && sg.offs[sg.offs.length - 1] > nx - 0.05) over.push('L' + n + ' (' + r2(sg.offs[sg.offs.length - 1] - nx) + ' s past the next stamp ' + r2(nx) + ')'); });
say('LOG lines whose singing at 4 syl/s runs past the next stamp (the window cannot hold them): ' + over.length + (over.length ? ' -> ' + over.join(', ') : ''));
var s = d.S(); s.time = '4/4'; s.bpm = 100; s.audio = null; s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null; s.spotify = null; d.cur().undo = []; d.cur().redo = []; d.state.prefs.side = true;
d.cur().audio = { el: { paused: true, currentTime: 0, duration: DUR, playbackRate: 1, pause: function () {}, play: function () { return Promise.resolve(); } }, url: '', name: 'Puddle of Mudd - Blurry.wav', peaks: null, duration: DUR, onset: d.risesOf(full), voice: voice, low: low, blob: false };
var realFetch = window.fetch, fetchUrls = [];
window.fetch = function (url, opts) { if (String(url).indexOf('/lyrics') === 0) { fetchUrls.push(String(url)); return Promise.resolve({ ok: true, status: 200, headers: new Headers({ 'content-type': 'application/json' }), json: function () { return Promise.resolve({ ok: true, synced: BLURRY_LRC, plain: '', duration: DUR, track: 'Blurry', artist: 'Puddle of Mudd' }); } }); } return realFetch(url, opts); };
// the readers by hand first, so the flow's result can be set against what they say about this track
var on = d.risesOf(full), bpmRead = d.tempoOf(on, fps);
var beatsRead = bpmRead ? d.trackBeats(on, fps, bpmRead) : [], m = bpmRead ? d.meterOf(on, low, fps, beatsRead, 60 / bpmRead, null) : null;
say('LOG by hand: tempoOf ' + bpmRead + ' (true 76); meterOf ' + (m ? 'per ' + m.per + ' bar ' + m.bar + ' phase ' + m.phase + ' phaseSure ' + r2(m.phaseSure) + ' sure ' + r2(m.sure) + ' time ' + m.time + ' half ' + m.half + ' compound ' + m.compound : 'null'));
var sp0 = performance.now(), acc = 0, z; for (z = 0; z < 2e7; z++) acc += z & 7; var sp1 = performance.now();
say('LOG virtual-clock probe: a 2e7-step spin measured ' + (sp1 - sp0).toFixed(1) + ' ms by performance.now (0 means the clock stands still while the thread is busy)');
say('LOG songMeta ' + JSON.stringify(d.songMeta()) + ' songKey ' + d.songKey());
var p0 = performance.now(), dd0 = Date.now(), tStart = toasts.length;
d.autoPlaceWords().then(function () {
  var ms = performance.now() - p0, dms = Date.now() - dd0;
  say('LOG autoPlaceWords took ' + ms.toFixed(0) + ' ms (performance.now) / ' + dms + ' ms (Date.now) under the virtual clock');
  say('LOG fetch url: ' + fetchUrls.join(' | '));
  var s1 = d.S(), sa = d.sheetAudio(), spb = d.slotsPerBar(s1.time);
  var lineIdx = []; s1.lines.forEach(function (l, li) { if (l.kind === 'line') lineIdx.push(li); });
  say('LOG result: bpm ' + s1.bpm + ' time ' + s1.time + ' offsetSec ' + sa.offsetSec + ' lined ' + sa.lined + ' locked ' + sa.locked + ' beats ' + (sa.beats ? sa.beats.length : 0) + ' fit ' + JSON.stringify(sa.lockFit) + ' filled ' + JSON.stringify(s1.filled) + ' title "' + s1.title + '"');
  check('every timed line with words became a sheet line (55 of 60 stamps)', lineIdx.length === sung.length && lineIdx.every(function (li) { return s1.lines[li].syllables.length > 0; }), lineIdx.length + ' lines');
  var which = Math.abs(s1.bpm - BPM) <= 1 ? 'the true tempo' : Math.abs(s1.bpm - 2 * BPM) <= 2 ? 'DOUBLE the true tempo' : Math.abs(s1.bpm - BPM / 2) <= 1 ? 'HALF the true tempo' : 'neither';
  check('bpm within 1 of 76', Math.abs(s1.bpm - BPM) <= 1, s1.bpm + ' = ' + which + ' (ratio ' + r2(s1.bpm / BPM) + ')');
  check('time signature 4/4', s1.time === '4/4', s1.time);
  var nearestDown = downbeats.reduce(function (b, x) { return Math.abs(x - sa.offsetSec) < Math.abs(b - sa.offsetSec) ? x : b; }, downbeats[0]);
  var beatNo = ((sa.offsetSec - T0) / BEAT) % 4;
  check('bar 1 (offsetSec) on a downbeat of the track', Math.abs(nearestDown - sa.offsetSec) < 0.03, 'offsetSec ' + sa.offsetSec + ', nearest downbeat ' + r3(nearestDown) + ', beat position in the bar ' + r2(beatNo) + ' (0 = beat 1)');
  check('locked to the beats', !!sa.locked && !!(sa.beats && sa.beats.length > 1), 'locked ' + sa.locked + ' fit ' + JSON.stringify(sa.lockFit));
  // where each syllable landed against where it was sung
  var errs = [], lenErrs = [], off1 = [], firstErr = [], countMismatch = 0, notIncreasing = 0, lastG = -1;
  lineIdx.forEach(function (li, n) {
    var line = s1.lines[li], sg = sung[n]; if (!sg) return;
    var base = d.barOrdinal(s1, li, 0) * spb, ys = d.sortedSyls(line).filter(function (y) { return !y.rest; });
    if (ys.length !== sg.ons.length) { countMismatch++; say('LOG line ' + n + ': ' + ys.length + ' syllables on the sheet vs ' + sg.ons.length + ' sung: "' + sg.text + '" -> ' + ys.map(function (y) { return y.text; }).join('|')); }
    ys.forEach(function (y, q) { if (q >= sg.ons.length) return; var g = base + y.pos; if (g <= lastG) notIncreasing++; lastG = g; var e = d.songOfSlot(g) - sg.ons[q]; errs.push(e); lenErrs.push(d.songOfSlot(g + d.lenSlots(y)) - sg.offs[q]); if (Math.abs(e) > SIXTEENTH) off1.push('L' + n + ' ' + y.text + ' ' + (e > 0 ? '+' : '') + r2(e)); if (q === 0) firstErr.push(r2(e)); });
  });
  var abs = errs.map(Math.abs), within1 = abs.filter(function (e) { return e <= SIXTEENTH; }).length, withinHalf = abs.filter(function (e) { return e <= SIXTEENTH / 2; }).length, maxE = Math.max.apply(null, abs), mean = errs.reduce(function (a, b) { return a + b; }, 0) / errs.length;
  check('every syllable within one sixteenth (' + r3(SIXTEENTH) + ' s at 76) of where it was sung', within1 === errs.length, within1 + ' of ' + errs.length + ' within one sixteenth, ' + withinHalf + ' within half; max |err| ' + r3(maxE) + ' s, mean err ' + r3(mean) + ' s (placed minus sung)');
  if (off1.length) say('LOG off by more than a sixteenth (' + off1.length + '): ' + off1.slice(0, 60).join(', ') + (off1.length > 60 ? ' ...' : ''));
  say('LOG first-syllable error per line (s): ' + firstErr.join(' '));
  var lenAbs = lenErrs.map(Math.abs), lenMean = lenErrs.reduce(function (a, b) { return a + b; }, 0) / lenErrs.length;
  say('LOG note ends vs sung ends: mean ' + r3(lenMean) + ' s, within a sixteenth ' + lenAbs.filter(function (e) { return e <= SIXTEENTH; }).length + ' of ' + lenAbs.length);
  check('syllable counts match the splitter on every line', countMismatch === 0, countMismatch + ' lines differ');
  check('onsets strictly increasing across the sheet', notIncreasing === 0, notIncreasing + ' not increasing');
  var last = toasts[toasts.length - 1] || '', sq = last.indexOf('in a bar the line before');
  check('no line squeezed (toast)', sq < 0, sq >= 0 ? last.slice(Math.max(0, sq - 40), sq + 60) : 'none reported');
  check('first word not "before bar 1"', last.indexOf('before bar 1') < 0);
  var barsList = []; lineIdx.forEach(function (li) { barsList.push(s1.lines[li].bars); }); say('LOG bars per line: ' + barsList.join(' '));
  lineIdx.slice(0, 3).forEach(function (li, n) { var line = s1.lines[li], base = d.barOrdinal(s1, li, 0) * spb; say('LOG line ' + (n + 1) + ' (starts bar ' + (base / spb + 1) + ', bars ' + line.bars + ', stamp ' + sung[n].t + '): ' + d.sortedSyls(line).map(function (y, q) { var g = base + y.pos; return y.text + '@' + g + 'x' + d.lenSlots(y) + '(' + r2(d.songOfSlot(g)) + 's/sung ' + r2(sung[n].ons[q]) + ')'; }).join(' ')); });
  say('LOG toasts during the flow (' + (toasts.length - tStart) + '):'); toasts.slice(tStart).forEach(function (x, q) { say('LOG   toast ' + (q + 1) + ' (' + x.length + ' chars, shown 1.8 s): ' + x); });
  // state after the fill
  check('S().lyrics equals the lookup text (the 55 lines with words, joined)', s1.lyrics === textExpected, s1.lyrics.length + ' chars vs ' + textExpected.length);
  check('Words panel closed', d.state.prefs.side === false && document.body.classList.contains('side-closed'), 'prefs.side ' + d.state.prefs.side + ' side-closed ' + document.body.classList.contains('side-closed'));
  check("$('time').value equals S().time", document.getElementById('time').value === s1.time, document.getElementById('time').value);
  check("$('bpm').value shows the bpm", document.getElementById('bpm').value === d.bpmText(s1.bpm), document.getElementById('bpm').value + ' vs ' + d.bpmText(s1.bpm) + ', face ' + document.getElementById('bpmFace').textContent + ', stage ' + document.getElementById('stageBpm').textContent);
  var tb = 0; s1.lines.forEach(function (l) { if (l.kind === 'line') tb += d.lineBars(l, spb); });
  check('player.bars relaid to the sheet (' + tb + ' bars)', d.player.bars.length === tb, d.player.bars.length + ' bars in player, ' + d.editor.systems.length + ' systems');
  check('no .playing chips lit', document.querySelectorAll('.playing').length === 0, document.querySelectorAll('.playing').length + ' lit');
  check('no NaN styles', document.querySelectorAll('[style*="NaN"]').length === 0);
  check('wave strip visible', !document.getElementById('wavebar').hidden);
  check('lyrics box shows the words', document.getElementById('lyrics').value === textExpected);
  check('one undo step for the whole fill', d.cur().undo.length === 1, d.cur().undo.length + ' undo steps');
  d.undo(); var s3 = d.S();
  check('undo: lines gone, filled cleared, tempo and lock back', s3.lines.length === 0 && !s3.filled && s3.bpm === 100 && s3.time === '4/4' && !(s3.audio && s3.audio.locked), 'lines ' + s3.lines.length + ' filled ' + JSON.stringify(s3.filled) + ' bpm ' + s3.bpm + ' locked ' + (s3.audio && s3.audio.locked));
  check("undo: bpm box back to 100", document.getElementById('bpm').value === '100', document.getElementById('bpm').value);
  window.fetch = realFetch;
}, function (e) { say('FAIL rejected: ' + (e && e.stack || e)); window.fetch = realFetch; });
