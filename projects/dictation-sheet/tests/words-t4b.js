// Part: words. Test 4b: can the Float32 dp drop fire in today's Place words flow? A typed hyphen in the LRC text
// ("oh-oh-oh") makes lineText give "ohohoh" (hy pieces join without a space) while wordsOf(lrc) gives "oh oh oh":
// an inexact sim early in a long song. Then the same dp in Float64 as the fix.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function lineTextOf(line) { var t = ''; d.sortedSyls(line).forEach(function (y) { t += (y.text || '') + (y.hy ? '' : ' '); }); return t.trim(); }
function flow(lrcLines) {
  // exactly what autoPlaceWords does: wordsToNotes on the joined text, then lineText per sheet line, then alignLines
  var lrc = lrcLines.map(function (t, i) { return { t: 10 + i * 3, text: t }; });
  var text = lrc.map(function (l) { return String(l.text || '').trim(); }).filter(Boolean).join('\n');
  var s = d.S(); s.lines = []; s.audio = null;
  d.wordsToNotes(text, 'T', { noUndo: true, quiet: true });
  var sheetLines = []; d.S().lines.forEach(function (l, li) { if (l.kind === 'line' && l.syllables.length) sheetLines.push({ li: li, text: lineTextOf(l) }); });
  var pairs = d.alignLines(sheetLines, lrc), lost = [];
  sheetLines.forEach(function (sl) { if (!pairs.some(function (p) { return p.li === sl.li; })) lost.push(sl.li + ' "' + sl.text + '"'); });
  return { sheet: sheetLines, pairs: pairs, lost: lost };
}
var N = 70, lines = [], i, k;
for (i = 0; i < N; i++) { var ws = []; for (k = 0; k < 7; k++) ws.push('w' + i + 'x' + k); lines.push(ws.join(' ')); }
lines[0] = 'Oh-oh-oh w0x1 w0x2 w0x3 w0x4 w0x5 w0x6';
var r = flow(lines);
say('LOG first pair: ' + JSON.stringify(r.pairs[0]) + ' sheet text "' + r.sheet[0].text + '" vs lrc "' + lines[0] + '"');
check('a hyphenated word in line 1 of a 70-line song: every line still pairs', r.lost.length === 0, r.pairs.length + ' of ' + r.sheet.length + ' pairs, lost: ' + r.lost.join(', '));
// a second shape: "oh-oh" late in the song is harmless, early in a song of 40 lines?
var lines2 = lines.slice(0, 40); lines2[1] = 'Oh-oh w1x1 w1x2 w1x3 w1x4 w1x5 w1x6';
lines2[0] = 'w0x0 w0x1 w0x2 w0x3 w0x4 w0x5 w0x6';
var r2 = flow(lines2);
check('"Oh-oh" in line 2 of a 40-line song: every line still pairs', r2.lost.length === 0, r2.pairs.length + ' of ' + r2.sheet.length + ' pairs, lost: ' + r2.lost.join(', '));
// the Blurry-shaped case: "Nobo-," gives "Nobo," (the piece after the hyphen is only a comma) so the sim stays 1
var l3 = lines.slice(); l3[0] = 'Nobo-, nobody told me what you thought';
var r3 = flow(l3);
check('"Nobo-," keeps sim 1 (the hyphen piece is only punctuation)', r3.pairs[0] && r3.pairs[0].sim === 1 && r3.lost.length === 0, JSON.stringify(r3.pairs[0]) + ' lost ' + r3.lost.length);
// the fix, mirrored here: the same dp with Float64 rows (and the traceback the same)
function wordsOf(text) { return String(text || '').toLowerCase().replace(/[^a-z0-9' ]+/g, ' ').split(/\s+/).filter(Boolean); }
function textSim(a, b) { var A = wordsOf(a), B = wordsOf(b); if (!A.length || !B.length) return 0; var set = {}; A.forEach(function (w) { set[w] = (set[w] || 0) + 1; }); var hit = 0; B.forEach(function (w) { if (set[w]) { hit++; set[w]--; } }); return hit / Math.max(A.length, B.length); }
function align64(sheetLines, lrc) {
  var n = sheetLines.length, m = lrc.length, thr = 0.45, dp = [], i, j;
  for (i = 0; i <= n; i++) { dp.push(new Float64Array(m + 1)); }
  for (i = 1; i <= n; i++) for (j = 1; j <= m; j++) { var sim = textSim(sheetLines[i - 1].text, lrc[j - 1].text), best = Math.max(dp[i - 1][j], dp[i][j - 1]); if (sim >= thr && dp[i - 1][j - 1] + sim > best) best = dp[i - 1][j - 1] + sim; dp[i][j] = best; }
  var pairs = []; i = n; j = m;
  while (i > 0 && j > 0) { var sim2 = textSim(sheetLines[i - 1].text, lrc[j - 1].text); if (sim2 >= thr && Math.abs(dp[i][j] - (dp[i - 1][j - 1] + sim2)) < 1e-6) { pairs.push({ li: sheetLines[i - 1].li, lrcIdx: j - 1, sim: sim2 }); i--; j--; } else if (dp[i - 1][j] >= dp[i][j - 1]) i--; else j--; }
  pairs.reverse(); return pairs;
}
var lrcA = lines.map(function (t, i) { return { t: 10 + i * 3, text: t }; });
var p64 = align64(r.sheet, lrcA);
check('the same dp in Float64 pairs all 70', p64.length === 70, p64.length + ' pairs');
// how far off the Float32 check is at the crossing
var sl = r.sheet, lr = lrcA, n = sl.length, m = lr.length, dp32 = [], worst = 0, where = -1;
for (i = 0; i <= n; i++) dp32.push(new Float32Array(m + 1));
for (i = 1; i <= n; i++) for (j = 1; j <= m; j++) { var sim = textSim(sl[i - 1].text, lr[j - 1].text), best = Math.max(dp32[i - 1][j], dp32[i][j - 1]); if (sim >= 0.45 && dp32[i - 1][j - 1] + sim > best) best = dp32[i - 1][j - 1] + sim; dp32[i][j] = best; if (i === j) { var err = Math.abs(dp32[i][j] - (dp32[i - 1][j - 1] + sim)); if (err > worst) { worst = err; where = i; } } }
say('LOG largest Float32 rounding gap on the diagonal: ' + worst.toExponential(2) + ' at line ' + where + ' (tolerance 1e-6; Float32 ulp at 32..64 is 3.8e-6, at 64..128 7.6e-6)');
