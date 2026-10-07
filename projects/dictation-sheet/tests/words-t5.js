// Part: words. Test 5: timing on the real clock (run with words_pagereal.py): the splitter over the 55 Blurry lines,
// parseLyrics, wordsToNotes with its render, alignLines, and a 10x song for scaling.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
var LRC = "[00:23.09] Everything's so blurry and everyone's so fake\n[00:28.96] And everybody's empty and everything is so messed up\n[00:34.96] Preoccupied without you, I cannot live at all\n[00:41.24] My whole world surrounds you, I stumble and I crawl\n[00:47.21] You could be my someone, you could be my scene\n[00:53.37] You know that I'll protect you from all of the obscene\n[00:59.31] I wonder what you're doing, imagine where you are\n[01:05.42] There's oceans in between us, but that's not very far\n[01:12.94] Can you take it all away?\n[01:15.94] Can you take it all away?\n[01:19.01] Well, you shoved it in my face\n[01:22.25] This pain you gave to me\n[01:25.18] Can you take it all away?\n[01:28.23] Can you take it all away?\n[01:31.16] Well, you shoved it in my face\n[01:36.25] Everyone is changing, there's no one left that's real\n[01:42.19] So make up your own ending and let me know just how you feel\n[01:48.22] 'Cause I am lost without you, I cannot live at all\n[01:54.46] My whole world surrounds you, I stumble then I crawl\n[02:00.67] You could be my someone, you could be my scene\n[02:06.55] You know that I will save you from all of the unclean\n[02:12.76] I wonder what you're doing, I wonder where you are\n[02:18.70] There's oceans in between us, but that's not very far\n[02:26.18] Can you take it all away?\n[02:29.33] Can you take it all away?\n[02:32.30] Well, you shoved it in my face\n[02:35.57] This pain you gave to me\n[02:38.45] Can you take it all away?\n[02:41.52] Can you take it all away?\n[02:44.40] Well, you shoved it in my face\n[02:47.95] This pain you gave to me\n[02:51.16] \n[03:01.91] Nobo-, nobody told me what you thought\n[03:06.17] Nobody told me what to say\n[03:09.11] Everyone showed you where to turn\n[03:12.36] Told you when to run away\n[03:15.48] Nobody told you where to hide\n[03:18.49] Nobody told you what to say\n[03:21.57] Everyone showed you where to turn\n[03:24.30] Showed you when to run away\n[03:27.13] Can you take it all away?\n[03:30.21] Can you take it all away?\n[03:33.21] Well, you shoved it in my face\n[03:36.48] This pain you gave to me\n[03:39.30] Can you take it all away?\n[03:42.35] Can you take it all away?\n[03:45.45] Well, you shoved it in my face\n[03:48.85] This pain you gave to me, no\n[03:53.59] \n[03:56.55] This pain you gave to me\n[03:59.80] \n[04:08.78] This pain you gave to me\n[04:12.54] \n[04:19.52] Can you take it all, take it all away?\n[04:24.32] This pain you gave to me\n[04:27.03] Can you take it all away?\n[04:30.29] This pain you gave to me\n[04:32.93] Can you take it all away?\n[04:36.10] This pain you gave to me\n[04:37.40] ";
function lineTextOf(line) { var t = ''; d.sortedSyls(line).forEach(function (y) { t += (y.text || '') + (y.hy ? '' : ' '); }); return t.trim(); }
var now = function () { return performance.now(); }, i;
var lrc = d.parseLrc(LRC), texts = lrc.map(function (e) { return e.text; }).filter(Boolean);
var d0 = Date.now(), p0 = now();
var h0 = now(); for (i = 0; i < 100; i++) Hyphenator.hyphenate('preoccupied', 'en-us'); var h1 = now();
say('LOG Hyphenator.hyphenate("preoccupied") x100: ' + (h1 - h0).toFixed(2) + ' ms');
var t0 = now(); texts.forEach(function (t) { d.syllableTexts(t); }); var t1 = now();
texts.forEach(function (t) { d.syllableTexts(t); }); var t2 = now();
say('LOG syllableTexts x' + texts.length + ' lines (' + texts.join(' ').split(' ').length + ' words): pass 1 ' + (t1 - t0).toFixed(1) + ' ms, pass 2 ' + (t2 - t1).toFixed(1) + ' ms');
var joined = texts.join('\n'), t3 = now(); d.parseLyrics(joined); var t4 = now();
say('LOG parseLyrics 55 lines: ' + (t4 - t3).toFixed(1) + ' ms');
var big = []; for (i = 0; i < 10; i++) big = big.concat(texts);
var t5 = now(); d.parseLyrics(big.join('\n')); var t6 = now();
say('LOG parseLyrics 550 lines: ' + (t6 - t5).toFixed(1) + ' ms');
var s = d.S(); s.lines = []; s.lyrics = ''; s.title = ''; s.filled = null; s.audio = null; s.spotify = null; s.bpm = 100; s.time = '4/4';
var w0 = now(); d.wordsToNotes(joined, 'Puddle of Mudd - Blurry', { quiet: true }); var w1 = now();
say('LOG wordsToNotes 55 lines (parse + full render): ' + (w1 - w0).toFixed(1) + ' ms');
var w2 = now(); d.wordsToNotes(joined + '\nOne more line', 'Puddle of Mudd - Blurry', { quiet: true }); var w3 = now();
say('LOG wordsToNotes again, one line added (merge + render): ' + (w3 - w2).toFixed(1) + ' ms');
var sheetLines = []; d.S().lines.forEach(function (l, li) { if (l.kind === 'line' && l.syllables.length) sheetLines.push({ li: li, text: lineTextOf(l) }); });
var a0 = now(); var pairs = d.alignLines(sheetLines, lrc); var a1 = now();
say('LOG alignLines ' + sheetLines.length + 'x' + lrc.length + ': ' + (a1 - a0).toFixed(1) + ' ms, ' + pairs.length + ' pairs');
var lrcBig = big.map(function (t, k) { return { t: 10 + k * 3, text: t }; }), sheetBig = big.map(function (t, k) { return { li: k, text: t }; });
var a2 = now(); var pairsBig = d.alignLines(sheetBig, lrcBig); var a3 = now();
say('LOG alignLines 550x550: ' + (a3 - a2).toFixed(1) + ' ms, ' + pairsBig.length + ' pairs');
say('LOG wall check: performance.now advanced ' + (now() - p0).toFixed(0) + ' ms, Date.now advanced ' + (Date.now() - d0) + ' ms');
