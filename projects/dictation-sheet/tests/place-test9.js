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
  var s1 = d.S(), sa = d.sheetAudio(), spb = d.slotsPerBar(s1.time);
  say('LOG result: bpm ' + s1.bpm + ' time ' + s1.time + ' offsetSec ' + sa.offsetSec + ' lined ' + sa.lined + '/' + sa.linedBy + ' locked ' + sa.locked + '/' + sa.lockedBy + ' beats ' + (sa.beats ? sa.beats.length : 0) + ' fit ' + JSON.stringify(sa.lockFit) + ' filled ' + JSON.stringify(s1.filled));
  var flatOns = [], flatOffs = []; sung.forEach(function (sg) { sg.ons.forEach(function (o, q) { flatOns.push(o); flatOffs.push(sg.offs[q]); }); });
  var got = []; s1.lines.forEach(function (l, li) { if (l.kind !== 'line') return; var base = d.barOrdinal(s1, li, 0) * spb; d.sortedSyls(l).forEach(function (y) { got.push({ t: y.text, g: base + y.pos, len: d.lenSlots(y), li: li, rest: y.rest }); }); });
  check('syllable count on the sheet equals the sung count', got.length === flatOns.length, got.length + ' vs ' + flatOns.length);
  var errs = [], lenErrs = [], bad = [], notInc = 0, rests = 0;
  got.forEach(function (o, q) { if (o.rest) rests++; if (q >= flatOns.length) return; if (q > 0 && o.g <= got[q - 1].g) notInc++; var e = d.songOfSlot(o.g) - flatOns[q]; errs.push(e); lenErrs.push(d.songOfSlot(o.g + o.len) - flatOffs[q]); if (Math.abs(e) > SIXTEENTH) bad.push(o.t + '(line ' + o.li + ') ' + (e > 0 ? '+' : '') + r2(e)); });
  var abs = errs.map(Math.abs), within1 = abs.filter(function (e) { return e <= SIXTEENTH; }).length, withinHalf = abs.filter(function (e) { return e <= SIXTEENTH / 2; }).length, maxE = Math.max.apply(null, abs), mean = errs.reduce(function (a, b) { return a + b; }, 0) / errs.length;
  check('every syllable within one sixteenth (' + r3(SIXTEENTH) + ' s) of where it was sung, in sheet order', within1 === errs.length, within1 + ' of ' + errs.length + ' within one sixteenth, ' + withinHalf + ' within half; max |err| ' + r3(maxE) + ' s, mean ' + r3(mean) + ' s');
  if (bad.length) say('LOG off by more than a sixteenth (' + bad.length + '): ' + bad.slice(0, 40).join(', '));
  var lenAbs = lenErrs.map(Math.abs); say('LOG note ends vs sung ends: mean ' + r3(lenErrs.reduce(function (a, b) { return a + b; }, 0) / lenErrs.length) + ' s, within a sixteenth ' + lenAbs.filter(function (e) { return e <= SIXTEENTH; }).length + ' of ' + lenAbs.length);
  check('onsets strictly increasing across the sheet', notInc === 0, notInc + ' not increasing');
  check('no rest syllables left', rests === 0, rests);
  var lines = s1.lines.filter(function (l) { return l.kind === 'line'; }); say('LOG sheet lines ' + lines.length + ' of 55 timed lines (' + (55 - lines.length) + ' joined); bars per line: ' + lines.map(function (l) { return l.bars; }).join(' ') + '; syllables per line: ' + lines.map(function (l) { return l.syllables.length; }).join(' '));
  // heads drawn per record: pieces from notePiecesAt + carries from barEvents, as the drawing does
  var heads = 0; s1.lines.forEach(function (l) { if (l.kind !== 'line') return; for (var b = 0; b < d.lineBars(l, spb); b++) d.barEvents(l, b, spb).forEach(function (ev) { heads += d.notePiecesAt(ev.s, ev.len, spb, s1.time).length; }); });
  say('LOG drawn heads ' + heads + ' for ' + got.length + ' records');
  var svg = document.querySelectorAll('#work svg'); var dots = 0; svg.forEach(function (g) { dots += g.querySelectorAll('.vf-dot, [class*="dot"]').length; }); say('LOG svg systems ' + svg.length + ', elements with a dot class ' + dots);
  say('LOG status hint: ' + document.getElementById('stHint').textContent);
  say('LOG lyrics panel lines: ' + s1.lyrics.split('\n').length + '; line 9 text: ' + s1.lyrics.split('\n')[8]);
  var last = toasts[toasts.length - 1] || ''; say('LOG last toast (' + last.length + ' chars): ' + last);
  var ax = 0; s1.lines.forEach(function (l, li) { if (l.kind === 'line' && l.syllables.length > 40 && !ax) { ax = 1; var base = d.barOrdinal(s1, li, 0) * spb; say('LOG a long joined line (' + l.syllables.length + ' syllables, bars ' + l.bars + '): ' + d.sortedSyls(l).slice(0, 16).map(function (y) { return y.text + '@' + (base + y.pos) + 'x' + d.lenSlots(y); }).join(' ') + ' ...'); } });
  check('one undo step for the whole fill', d.cur().undo.length === 1, d.cur().undo.length + ' undo steps');
  d.undo(); var s3 = d.S();
  check('undo: lines gone, filled cleared, tempo and lock back', s3.lines.length === 0 && !s3.filled && s3.bpm === 100 && s3.time === '4/4' && !(s3.audio && s3.audio.locked), 'lines ' + s3.lines.length + ' bpm ' + s3.bpm + ' locked ' + (s3.audio && s3.audio.locked));
  window.fetch = realFetch;
}, function (e) { say('FAIL rejected: ' + (e && e.stack || e)); window.fetch = realFetch; });
