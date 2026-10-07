// Part: words. Test 4: alignLines in isolation: same text, an extra typed line, headers, repeated lines, and the
// Float32 dp table against the 1e-6 traceback tolerance on long songs with one inexact pair.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function lineTextOf(line) { var t = ''; d.sortedSyls(line).forEach(function (y) { t += (y.text || '') + (y.hy ? '' : ' '); }); return t.trim(); }
function sheetOf(text) { var out = []; d.parseLyrics(text).forEach(function (l, li) { if (l.kind === 'line' && l.syllables.length) out.push({ li: li, text: lineTextOf(l) }); }); return out; }
function lrcOf(lines) { return lines.map(function (t, i) { return { t: 10 + i * 3, text: t }; }); }
var song = ['Everything\'s so blurry and everyone\'s so fake', 'And everybody\'s empty and everything is so messed up', 'Preoccupied without you, I cannot live at all', 'My whole world surrounds you, I stumble and I crawl', 'You could be my someone, you could be my scene', 'Can you take it all away?', 'Can you take it all away?', 'Well, you shoved it in my face', 'This pain you gave to me', 'Nobo-, nobody told me what you thought'];
// (a) the same text
var pairs = d.alignLines(sheetOf(song.join('\n')), lrcOf(song));
check('(a) same text: 10 pairs, all sim 1, in order', pairs.length === 10 && pairs.every(function (p, i) { return p.sim === 1 && p.li === i && p.lrcIdx === i; }), JSON.stringify(pairs));
// (b) one extra typed line in the sheet
var extra = song.slice(0, 3).concat(['La la la la la'], song.slice(3));
pairs = d.alignLines(sheetOf(extra.join('\n')), lrcOf(song));
check('(b) one extra typed line: 10 pairs, the extra line (li 3) skipped, lrc order kept', pairs.length === 10 && !pairs.some(function (p) { return p.li === 3; }) && pairs.every(function (p) { return p.sim === 1; }), pairs.map(function (p) { return p.li + '>' + p.lrcIdx; }).join(' '));
// (c) headers in the sheet: li must point at the real line index
var withH = ['[Verse]'].concat(song.slice(0, 5), ['[Chorus]'], song.slice(5));
var sh = sheetOf(withH.join('\n')); pairs = d.alignLines(sh, lrcOf(song));
check('(c) headers: 10 pairs, li skips the header rows (1..5, 7..11)', pairs.length === 10 && pairs.map(function (p) { return p.li; }).join(',') === '1,2,3,4,5,7,8,9,10,11', pairs.map(function (p) { return p.li + '>' + p.lrcIdx; }).join(' '));
// (d) a sheet line the user edited a little (sim under 1) still pairs; a very different one does not
var edited = song.slice(); edited[2] = 'Preoccupied without you, I cannot breathe at all'; edited[7] = 'Something else entirely here';
pairs = d.alignLines(sheetOf(edited.join('\n')), lrcOf(song));
var p2 = pairs.filter(function (p) { return p.li === 2; })[0], p7 = pairs.filter(function (p) { return p.li === 7; })[0];
check('(d) a one-word edit pairs with sim 0.8; a rewritten line does not pair', p2 && Math.abs(p2.sim - 0.8) < 1e-6 && !p7, JSON.stringify([p2, p7]));
// (e) the repeated "Can you take it all away?" with one copy missing on the sheet: order kept, no cross pairing
var missing = song.slice(0, 6).concat(song.slice(7));
pairs = d.alignLines(sheetOf(missing.join('\n')), lrcOf(song));
check('(e) one of two repeated lines missing: 9 pairs, all sim 1', pairs.length === 9 && pairs.every(function (p) { return p.sim === 1; }), pairs.map(function (p) { return p.li + '>' + p.lrcIdx; }).join(' '));
// (f) blank LRC entries (stamps with no text) pair with nothing and do not break the order
var lrcB = lrcOf(song); lrcB.splice(4, 0, { t: 21.5, text: '' }); lrcB.push({ t: 99, text: '' });
pairs = d.alignLines(sheetOf(song.join('\n')), lrcB);
check('(f) blank stamped entries: 10 pairs, lrcIdx skips the blank', pairs.length === 10 && pairs.map(function (p) { return p.lrcIdx; }).join(',') === '0,1,2,3,5,6,7,8,9,10', pairs.map(function (p) { return p.li + '>' + p.lrcIdx; }).join(' '));
// (g) long songs: N identical lines but the first pair inexact (h of n words kept). dp is Float32; the traceback
// wants |dp[i][j] - (dp[i-1][j-1] + sim)| < 1e-6
function longCase(N, n, h) {
  var lrcL = [], sheetL = [], i, k;
  for (i = 0; i < N; i++) { var ws = []; for (k = 0; k < n; k++) ws.push('w' + i + 'x' + k); lrcL.push(ws.join(' ')); var ss = ws.slice(); if (i === 0) for (k = h; k < n; k++) ss[k] = 'zz' + k; sheetL.push(ss.join(' ')); }
  var sl = sheetL.map(function (t, li) { return { li: li, text: t }; }), pr = d.alignLines(sl, lrcOf(lrcL));
  var lost = []; for (i = 0; i < N; i++) if (!pr.some(function (p) { return p.li === i; })) lost.push(i);
  return { pairs: pr.length, lost: lost, sim0: pr.length && pr[0].li === 0 ? pr[0].sim : null };
}
var combos = [[70, 10, 7], [70, 10, 6], [70, 10, 9], [70, 7, 5], [70, 3, 2], [70, 9, 8], [70, 10, 5], [70, 10, 8], [130, 10, 7], [130, 7, 5], [130, 9, 8], [130, 6, 5]];
var lostAny = [];
combos.forEach(function (c) { var r = longCase(c[0], c[1], c[2]); say('LOG long N=' + c[0] + ' first pair sim ' + c[2] + '/' + c[1] + ': ' + r.pairs + ' pairs, lost lines ' + JSON.stringify(r.lost)); if (r.lost.length) lostAny.push(c[2] + '/' + c[1] + '@' + c[0] + ' lost ' + r.lost.join(',')); });
check('(g) long songs with one inexact pair keep every line', lostAny.length === 0, lostAny.join('; '));
// the same with exact sims only (all 1): must never lose a line
var r1 = longCase(200, 10, 10);
check('(g2) 200 exact lines all pair', r1.pairs === 200, r1.pairs + ' pairs, lost ' + JSON.stringify(r1.lost));
// (h) two-word lines: "Can you take it all away?" vs "Can you take it all, take it all away?" sim
say('LOG sim of the two "take it all" lines: ' + JSON.stringify(d.alignLines([{ li: 0, text: 'Can you take it all, take it all away?' }], [{ t: 1, text: 'Can you take it all away?' }])));
