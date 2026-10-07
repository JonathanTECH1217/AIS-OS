// Part: words. Test 5: timing on the real clock (run with words_pagereal.py): the splitter over the 55 Blurry lines,
// parseLyrics, wordsToNotes with its render, alignLines, and a 10x song for scaling.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
var LRC = __LRC__;
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
