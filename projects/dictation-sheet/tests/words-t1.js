// Part: words. Test 1 (+5): the real Blurry LRC through parseLrc, syllableTexts, parseLyrics and wordsToNotes; the
// splitter timed over the 60 lines; then a blind Place words (fake Spotify link, fake /lyrics answer carrying the real
// LRC, no track heard) to see the syllable records per line against the note heads the notation would draw; then
// alignLines over the whole song.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var LRC = "[00:23.09] Everything's so blurry and everyone's so fake\n[00:28.96] And everybody's empty and everything is so messed up\n[00:34.96] Preoccupied without you, I cannot live at all\n[00:41.24] My whole world surrounds you, I stumble and I crawl\n[00:47.21] You could be my someone, you could be my scene\n[00:53.37] You know that I'll protect you from all of the obscene\n[00:59.31] I wonder what you're doing, imagine where you are\n[01:05.42] There's oceans in between us, but that's not very far\n[01:12.94] Can you take it all away?\n[01:15.94] Can you take it all away?\n[01:19.01] Well, you shoved it in my face\n[01:22.25] This pain you gave to me\n[01:25.18] Can you take it all away?\n[01:28.23] Can you take it all away?\n[01:31.16] Well, you shoved it in my face\n[01:36.25] Everyone is changing, there's no one left that's real\n[01:42.19] So make up your own ending and let me know just how you feel\n[01:48.22] 'Cause I am lost without you, I cannot live at all\n[01:54.46] My whole world surrounds you, I stumble then I crawl\n[02:00.67] You could be my someone, you could be my scene\n[02:06.55] You know that I will save you from all of the unclean\n[02:12.76] I wonder what you're doing, I wonder where you are\n[02:18.70] There's oceans in between us, but that's not very far\n[02:26.18] Can you take it all away?\n[02:29.33] Can you take it all away?\n[02:32.30] Well, you shoved it in my face\n[02:35.57] This pain you gave to me\n[02:38.45] Can you take it all away?\n[02:41.52] Can you take it all away?\n[02:44.40] Well, you shoved it in my face\n[02:47.95] This pain you gave to me\n[02:51.16] \n[03:01.91] Nobo-, nobody told me what you thought\n[03:06.17] Nobody told me what to say\n[03:09.11] Everyone showed you where to turn\n[03:12.36] Told you when to run away\n[03:15.48] Nobody told you where to hide\n[03:18.49] Nobody told you what to say\n[03:21.57] Everyone showed you where to turn\n[03:24.30] Showed you when to run away\n[03:27.13] Can you take it all away?\n[03:30.21] Can you take it all away?\n[03:33.21] Well, you shoved it in my face\n[03:36.48] This pain you gave to me\n[03:39.30] Can you take it all away?\n[03:42.35] Can you take it all away?\n[03:45.45] Well, you shoved it in my face\n[03:48.85] This pain you gave to me, no\n[03:53.59] \n[03:56.55] This pain you gave to me\n[03:59.80] \n[04:08.78] This pain you gave to me\n[04:12.54] \n[04:19.52] Can you take it all, take it all away?\n[04:24.32] This pain you gave to me\n[04:27.03] Can you take it all away?\n[04:30.29] This pain you gave to me\n[04:32.93] Can you take it all away?\n[04:36.10] This pain you gave to me\n[04:37.40] ";
function lineTextOf(line) { var t = ''; d.sortedSyls(line).forEach(function (y) { t += (y.text || '') + (y.hy ? '' : ' '); }); return t.trim(); }
function splitStr(text) { return d.syllableTexts(text).map(function (x) { return x.text + (x.hy ? '-' : ' '); }).join('').trim(); }
function drawnHeads(line) {
  var s = d.S(), spb = d.slotsPerBar(s.time), bars = d.lineBars(line, spb), n = 0, b;
  for (b = 0; b < bars; b++) d.barEvents(line, b, spb).forEach(function (ev) { n += d.notePiecesAt(ev.s, ev.len, spb, s.time).length; });
  return n;
}
say('LOG hyphenator: ' + typeof window.Hyphenator + ', en-us patterns: ' + !!(window.Hyphenator && Hyphenator.languages && Hyphenator.languages['en-us']));
// (5) timing first, before anything else here warms the splitter (boot may already have: the sample sheet)
var lrc = d.parseLrc(LRC), texts = lrc.map(function (e) { return e.text; }).filter(Boolean);
var t0 = performance.now(); texts.forEach(function (t) { d.syllableTexts(t); }); var t1 = performance.now();
texts.forEach(function (t) { d.syllableTexts(t); }); var t2 = performance.now();
var joined = texts.join('\n');
var t3 = performance.now(); var parsed = d.parseLyrics(joined); var t4 = performance.now();
say('LOG perf: syllableTexts x' + texts.length + ' lines: pass 1 ' + (t1 - t0).toFixed(1) + ' ms, pass 2 ' + (t2 - t1).toFixed(1) + ' ms; parseLyrics ' + (t4 - t3).toFixed(1) + ' ms');
say('LOG parseLrc entries ' + lrc.length + ', with text ' + texts.length + ', parseLyrics lines ' + parsed.length);
// (1) every timed line through the splitter
lrc.forEach(function (e, i) { var syl = d.syllableTexts(e.text); say('LINE|' + i + '|' + e.t.toFixed(2) + '|' + e.text + '|' + (e.text ? syl.length : 0) + '|' + splitStr(e.text)); });
say('LOG syllableTexts on an empty string gives ' + JSON.stringify(d.syllableTexts('')) + ' (parseLyrics skips blank lines)');
// parseLyrics agrees with syllableTexts line by line
var mism = 0; parsed.forEach(function (l, i) { if (l.syllables.length !== d.syllableTexts(texts[i]).length) mism++; });
check('parseLyrics line counts equal syllableTexts counts', mism === 0, mism + ' differ');
// wordsToNotes on the joined text: sheet lines as the timed lines
var s = d.S(); s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null; s.audio = null; s.spotify = null; s.bpm = 100; s.time = '4/4';
var t5 = performance.now(); d.wordsToNotes(joined, 'Puddle of Mudd - Blurry', { quiet: true }); var t6 = performance.now();
say('LOG perf: wordsToNotes (parse + render) ' + (t6 - t5).toFixed(1) + ' ms');
s = d.S();
var counts = s.lines.map(function (l) { return l.kind === 'line' ? l.syllables.length : 'H'; });
check('wordsToNotes made ' + texts.length + ' lines', s.lines.length === texts.length, String(s.lines.length));
check('line 5 (You could be my someone, you could be my scene) holds 11 syllable records', counts[4] === 11, 'records ' + counts[4] + ' text "' + lineTextOf(s.lines[4]) + '"');
say('LOG records per line after wordsToNotes: ' + counts.join(' '));
// (1b) the blind fill on the same sheet: fake link, fake lookup with the real LRC, no track heard
var realFetch = window.fetch;
window.fetch = function (url, opts) { if (String(url).indexOf('/lyrics') === 0) return Promise.resolve({ ok: true, headers: new Headers({ 'content-type': 'application/json' }), json: function () { return Promise.resolve({ ok: true, synced: LRC, plain: '', duration: 304, track: 'Blurry', artist: 'Puddle of Mudd' }); } }); return realFetch(url, opts); };
s.spotify = { trackId: 'blurry', name: 'Blurry · Puddle of Mudd', durationMs: 304000, title: 'Blurry', artist: 'Puddle of Mudd', album: '' };
d.cur().audio = null;
var t7 = performance.now();
d.autoPlaceWords().then(function () {
  var t8 = performance.now(), s2 = d.S(), spb = d.slotsPerBar(s2.time), sa = d.sheetAudio();
  say('LOG perf: autoPlaceWords (blind) ' + (t8 - t7).toFixed(1) + ' ms; bpm ' + s2.bpm + ' time ' + s2.time + ' offsetSec ' + sa.offsetSec + ' filled ' + JSON.stringify(s2.filled));
  var after = s2.lines.map(function (l) { return l.kind === 'line' ? l.syllables.length : 'H'; });
  check('syllable records per line unchanged by the fill', after.join(' ') === counts.join(' '), after.join(' '));
  var rows = [];
  s2.lines.forEach(function (l, li) { if (l.kind !== 'line') return; var heads = drawnHeads(l); rows.push(li + ':' + l.syllables.length + '/' + heads); });
  say('LOG line:records/drawnHeads after the blind fill: ' + rows.join(' '));
  var l5 = s2.lines[4];
  say('LOG line 5 after the fill: ' + d.sortedSyls(l5).map(function (y) { return y.text + '@' + y.pos + 'x' + d.lenSlots(y); }).join(' ') + ' bars ' + d.lineBars(l5, spb) + ' drawn heads ' + drawnHeads(l5));
  // alignLines with the sheet's own lines against the same LRC
  var sheetLines = []; s2.lines.forEach(function (l, li) { if (l.kind === 'line' && l.syllables.length) sheetLines.push({ li: li, text: lineTextOf(l) }); });
  var t9 = performance.now(); var pairs = d.alignLines(sheetLines, lrc); var t10 = performance.now();
  say('LOG perf: alignLines ' + sheetLines.length + 'x' + lrc.length + ' ' + (t10 - t9).toFixed(1) + ' ms');
  var bad = pairs.filter(function (p) { return p.sim !== 1; }), mono = true, k;
  for (k = 1; k < pairs.length; k++) if (pairs[k].lrcIdx <= pairs[k - 1].lrcIdx || pairs[k].li <= pairs[k - 1].li) mono = false;
  check('every sheet line pairs (' + sheetLines.length + ')', pairs.length === sheetLines.length, pairs.length + ' pairs');
  check('every pair sim 1', bad.length === 0, bad.map(function (p) { return p.li + '->' + p.lrcIdx + ' ' + p.sim.toFixed(3); }).join(', '));
  check('pairs in order', mono);
  var unpaired = []; lrc.forEach(function (e, i) { if (!pairs.some(function (p) { return p.lrcIdx === i; })) unpaired.push(i + (e.text ? '(' + e.text + ')' : '(blank)')); });
  say('LOG unpaired LRC entries: ' + unpaired.join(' '));
  // a crafted placing of the 6 syllables from the screenshot: a note off the beat and one over the barline
  var line = d.parseLyrics('You could be my someone,')[0], ys = d.sortedSyls(line), plan = [[0, 2], [2, 2], [4, 2], [7, 3], [14, 4], [18, 2]];
  ys.forEach(function (y, i) { y.pos = plan[i][0]; d.setSlotsRaw(y, plan[i][1]); });
  var pieces = []; for (var b = 0; b < d.lineBars(line, spb); b++) d.barEvents(line, b, spb).forEach(function (ev) { pieces.push(ev.items[0].y.text + (ev.items[0].carry ? '(carry)' : '') + ':' + d.notePiecesAt(ev.s, ev.len, spb, s2.time).map(function (p) { return p.dur + (p.dots ? '.' : ''); }).join('+')); });
  say('LOG crafted line: ' + ys.length + ' records, ' + drawnHeads(line) + ' drawn heads: ' + pieces.join(' '));
  window.fetch = realFetch;
  say('DONE');
}, function (e) { say('FAIL autoPlaceWords rejected: ' + (e && e.stack || e)); window.fetch = realFetch; say('DONE'); });
