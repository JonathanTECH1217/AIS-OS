// meterOf on synthetic songs: rock 4/4, a waltz, random accents, a 6/8, and a waltz read at double tempo
var d = window.__ds, fps = 100, N = fps * 60;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function bump(env, t, amp, decay) { var k0 = Math.round(t * fps), k; for (k = 0; k < decay && k0 + k < env.length; k++) { var v = (k < 2 ? amp * (k + 1) / 2 : amp * (1 - (k - 2) / (decay - 2))); if (v > env[k0 + k]) env[k0 + k] = v; } }
function fresh() { var e = new Float32Array(N); for (var i = 0; i < N; i++) e[i] = 0.4; return e; }
function brief(m) { return m ? 'per ' + m.per + ' bar ' + m.bar + ' time ' + m.time + ' phase ' + m.phase + ' sure ' + m.sure.toFixed(2) + ' phaseSure ' + m.phaseSure.toFixed(2) + ' compound ' + m.compound + ' subSure ' + m.subSure.toFixed(2) + ' half ' + m.half : 'null'; }
// (a) rock 4/4 at 120: kick on 1 (loud) and 3, snare on 2 and 4 louder in the full band, hi-hat eighths
var full = fresh(), low = fresh(), beats = [], t, k = 0;
for (t = 1.0; t < 59; t += 0.5, k++) { beats.push(t); var pos = k % 4; if (pos === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else if (pos === 2) { bump(low, t, 1.7, 12); bump(full, t, 1.9, 10); } else { bump(full, t, 2.5, 8); bump(low, t, 0.8, 6); } bump(full, t + 0.25, 1.0, 4); }
var m = d.meterOf(d.risesOf(full), low, fps, beats, 0.5, null); say('LOG rock: ' + brief(m));
check('rock is 4/4, beat 1 on the loud kick, sure', m && m.time === '4/4' && m.phase === 0 && m.sure >= 0.5 && m.phaseSure >= 0.5 && !m.compound);
// (b) waltz: bass on 1 of every 3
full = fresh(); low = fresh(); beats = []; k = 0;
for (t = 1.0; t < 59; t += 0.5, k++) { beats.push(t); if (k % 3 === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.3, 10); } else { bump(full, t, 1.6, 8); bump(low, t, 0.7, 6); } }
m = d.meterOf(d.risesOf(full), low, fps, beats, 0.5, null); say('LOG waltz: ' + brief(m));
check('waltz is 3/4 with beat 1 on the bass', m && m.time === '3/4' && m.phase === 0 && m.sure >= 0.5 && m.phaseSure >= 0.5);
// (c) random accents over 30 seeds: how often do they come out "sure"?
var seed = 7; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
var sures = [], passes = 0;
for (var si = 0; si < 30; si++) {
  full = fresh(); low = fresh(); beats = []; seed = 1000 + si * 7919;
  for (t = 1.0; t < 59; t += 0.5) { beats.push(t); bump(full, t, 0.8 + 2 * rnd(), 8); bump(low, t, 0.5 + 2 * rnd(), 8); }
  m = d.meterOf(d.risesOf(full), low, fps, beats, 0.5, null); sures.push(m ? +m.sure.toFixed(2) : -1); if (m && m.sure >= 0.5) passes++;
}
say('LOG random sure over 30 seeds: ' + sures.join(' ') + ' -> ' + passes + ' would set the time signature');
check('random accents rarely pass (at most 2 of 30)', passes <= 2, passes + ' of 30');
// (d) 6/8 at a dotted-quarter pulse of 80 (tau 0.75): strong, weak; eighths between (thirds of the beat)
full = fresh(); low = fresh(); beats = []; k = 0;
for (t = 1.0; t < 59; t += 0.75, k++) { beats.push(t); if (k % 2 === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.3, 10); } else { bump(full, t, 1.6, 8); bump(low, t, 0.9, 6); } bump(full, t + 0.25, 1.1, 4); bump(full, t + 0.5, 1.1, 4); }
m = d.meterOf(d.risesOf(full), low, fps, beats, 0.75, null); say('LOG 6/8: ' + brief(m));
check('6/8 is read as compound with two beats to the bar', m && m.compound && m.time === '6/8' && m.bar === 2 && m.phase === 0);
// (e) a waltz whose tempo came out doubled (beats every 0.25 s, accents every 6)
full = fresh(); low = fresh(); beats = []; k = 0;
for (t = 1.0; t < 59; t += 0.25, k++) { beats.push(t); if (k % 6 === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.3, 10); } else if (k % 2 === 0) { bump(full, t, 1.6, 8); bump(low, t, 0.7, 6); } }
m = d.meterOf(d.risesOf(full), low, fps, beats, 0.25, null); say('LOG doubled waltz: ' + brief(m) + ' r ' + JSON.stringify(m && m.r));
check('a waltz read at double tempo is flagged half', m && m.half && m.sure === 0);
// (e2) the same with hi-hat on every eighth, the way a real band plays it
full = fresh(); low = fresh(); beats = []; k = 0;
for (t = 1.0; t < 59; t += 0.25, k++) { beats.push(t); if (k % 6 === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.3, 10); } else if (k % 2 === 0) { bump(full, t, 1.6, 8); bump(low, t, 0.7, 6); } else bump(full, t, 1.0, 4); }
m = d.meterOf(d.risesOf(full), low, fps, beats, 0.25, null); say('LOG doubled waltz with hats: ' + brief(m) + ' r ' + JSON.stringify(m && m.r));
// (e3) a 4/4 read at double tempo, for contrast: must NOT be flagged half
full = fresh(); low = fresh(); beats = []; k = 0;
for (t = 1.0; t < 59; t += 0.25, k++) { beats.push(t); var p8 = k % 8; if (p8 === 0) { bump(low, t, 2.2, 12); bump(full, t, 2.0, 10); } else if (p8 === 4) { bump(low, t, 1.7, 12); bump(full, t, 1.9, 10); } else if (p8 === 2 || p8 === 6) { bump(full, t, 2.5, 8); bump(low, t, 0.8, 6); } else bump(full, t, 1.0, 4); }
m = d.meterOf(d.risesOf(full), low, fps, beats, 0.25, null); say('LOG doubled 4/4: ' + brief(m) + ' r ' + JSON.stringify(m && m.r));
check('a 4/4 read at double tempo is not flagged half', m && !m.half);
// (f) the phrase-start vote: rock with kicks equal on 1 and 3, lines starting on beat 1
full = fresh(); low = fresh(); beats = []; k = 0; var starts = [];
for (t = 1.0; t < 59; t += 0.5, k++) { beats.push(t); var p2 = k % 4; if (p2 === 0 || p2 === 2) { bump(low, t, 2.0, 12); bump(full, t, 1.9, 10); } else { bump(full, t, 2.5, 8); bump(low, t, 0.8, 6); } if (k % 16 === 0 && t > 4) starts.push(t + 0.03); }
m = d.meterOf(d.risesOf(full), low, fps, beats, 0.5, starts); say('LOG equal kicks with phrase starts: ' + brief(m) + ' (' + starts.length + ' starts)');
check('equal kicks: the phrase starts choose beat 1', m && m.time === '4/4' && m.phase === 0 && m.phaseSure >= 0.5);
say('LOG splitter: ' + JSON.stringify(d.syllableTexts('Silent night, holy night All is calm wonderful beautiful away very little people every').map(function (x) { return x.text + (x.hy ? '-' : ''); })));
