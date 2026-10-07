// voice-lrcwin.js: pagecheck.py extra script. lrcWindows edge cases and the window autoPlaceWords hands to sungSpansIn.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var s = d.S(); s.spotify = { trackId: 'w', name: 'T · A', durationMs: 60000, title: 'T', artist: 'A', album: '' }; d.cur().audio = null;
function W(lrc, pairs, lastLen) { return d.lrcWindows(pairs, lrc, lastLen).map(function (w) { return [Math.round(w.t0 * 100) / 100, Math.round(w.t1 * 100) / 100, w.lis.join('+')]; }); }
var lrc = [{ t: 10.0, text: 'a' }, { t: 10.03, text: 'b' }, { t: 14.0, text: 'c' }, { t: 22.0, text: 'unpaired' }, { t: 24.0, text: 'd' }, { t: 24.06, text: 'e' }, { t: 40.0, text: 'f' }, { t: 58.0, text: 'g' }, { t: 59.9, text: 'h' }];
var pairs = [{ li: 0, lrcIdx: 0 }, { li: 1, lrcIdx: 1 }, { li: 2, lrcIdx: 2 }, { li: 3, lrcIdx: 4 }, { li: 4, lrcIdx: 5 }, { li: 5, lrcIdx: 6 }, { li: 6, lrcIdx: 7 }, { li: 7, lrcIdx: 8 }];
var w = W(lrc, pairs, 12);
say('LOG lrcWindows (song 60 s, lastLen 12): ' + JSON.stringify(w));
check('stamps 30 ms apart share one window with both lines', w[0][2] === '0+1' && w[0][0] === 10 && w[0][1] === 14, JSON.stringify(w[0]));
check('an unpaired timed line still ends the window before it (14 -> 22)', w[1][0] === 14 && w[1][1] === 22, JSON.stringify(w[1]));
check('stamps 60 ms apart get separate windows, the first padded to 0.4 s', w[2][2] === '3' && Math.abs(w[2][1] - 24.4) < 1e-9 && w[3][2] === '4', JSON.stringify([w[2], w[3]]));
check('a 16 s gap to the next stamp is capped at 12 s (24.06 -> 36.06)', Math.abs(w[3][1] - 36.06) < 1e-9, JSON.stringify(w[3]));
check('a window never passes the end of the song (58 -> 60, not 70)', w[5][0] === 58 && w[5][1] === 60, JSON.stringify(w[5]));
check('...except a stamp near the end: 59.9 -> 60.3 passes the song end (0.4 s minimum applied after the clamp)', w[6][0] === 59.9 && Math.abs(w[6][1] - 60.3) < 1e-9, JSON.stringify(w[6]));
say('LOG the windows sungSpansIn gets (t0 - 0.12, t1 - 0.05): ' + JSON.stringify(w.map(function (x) { return [Math.round((x[0] - 0.12) * 100) / 100, Math.round((x[1] - 0.05) * 100) / 100]; })));
var w6 = W(lrc, pairs, 6); check('without a voice curve the last window is 6 s (58 -> 60 still clamped)', w6[5][1] === 60, JSON.stringify(w6[5]));
// no duration known (a file with duration 0): windows run to t0 + lastLen
s.spotify = { trackId: 'w', name: 'T · A', durationMs: 0, title: 'T', artist: 'A', album: '' };
var w0 = W(lrc, pairs, 12); check('duration unknown: the last window runs the full 12 s (59.9 -> 71.9)', Math.abs(w0[6][1] - 71.9) < 1e-9, JSON.stringify(w0[6]));
// alignLines: a repeated chorus line and a near-miss
var sheet = [{ li: 0, text: 'you could be my someone' }, { li: 1, text: 'you can be my scene' }, { li: 2, text: 'you could be my someone' }];
var lrc2 = [{ t: 1, text: 'You could be my someone' }, { t: 3, text: 'You can be my scene' }, { t: 5, text: 'Some other line' }, { t: 7, text: 'You could be my someone' }];
say('LOG alignLines repeated lines: ' + JSON.stringify(d.alignLines(sheet, lrc2)));
