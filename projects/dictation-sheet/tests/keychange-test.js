// A key change keeps every note sounding as it was (C# minor to E major through the key box, both orders, la-based
// minor on and off); only the syllables, degrees and spellings follow the new key.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function mk(pos, text) { return d.normalize({ lines: [{ kind: 'line', syllables: [{ text: text, pos: pos, len: 'q' }] }] }).lines[0].syllables[0]; }
function midis() { var s1 = d.S(), inst = d.instFor(s1); return d.sortedSyls(s1.lines[0]).map(function (y) { return d.sylMidiFor(y, inst); }).join(','); }
function sols() { return d.sortedSyls(d.S().lines[0]).map(function (y) { return y.sol; }).join(' '); }
function notes() { return d.sortedSyls(d.S().lines[0]).map(function (y) { return y.note + y.oct; }).join(' '); }
function setup(la) {
  s = d.S(); s.view = 'vocals'; s.key = { tonic: 'C#', mode: 'minor', laMinor: la };
  var y = mk(0, 'a'); y.sol = la ? 'la' : 'do'; y.noteAuto = true; y.note = 'C#'; y.oct = 4; var list = [y];
  for (var i = 1; i < 8; i++) { var z = mk(i * 4, 'n' + i); z.sol = y.sol; z.note = y.note; z.oct = 4; z.noteAuto = true; d.stepDiatonic(z, s.key, i, 4); list.push(z); }
  s.lines = [{ kind: 'line', bars: 2, syllables: list }]; d.renderAll();
}
function pick(id, v) { var e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('change', { bubbles: true })); }
[true, false].forEach(function (la) {
  setup(la); var want = midis();
  check('la-based ' + la + ': C# minor, eight notes up the scale from C#4', want.split(',')[0] === '61' && want.split(',').length === 8, want);
  pick('mode', 'major');
  if (la) check('  mode to major first: the pitches stay, the tonic goes to E (same do), syllables unchanged', midis() === want && d.S().key.tonic === 'E' && sols() === 'la ti do re mi fa sol la', midis() + ' ' + d.S().key.tonic + ' | ' + sols());
  else check('  mode to major first: the pitches stay, the tonic goes to Db (not C)', midis() === want && d.S().key.tonic === 'Db', midis() + ' ' + d.S().key.tonic);
  pick('tonic', 'E');
  check('  then E major: the pitches stay', midis() === want, midis());
  if (la) check('  spelled in E major, syllables from do = E', notes() === 'C#4 D#4 E4 F#4 G#4 A4 B4 C#5' && sols() === 'la ti do re mi fa sol la', notes() + ' | ' + sols());
  else check('  every note has a syllable in E major; C#, D#, F#, G# are la, ti, re, mi', sols().split(' ').every(function (x) { return !!x; }) && [0, 1, 3, 4].every(function (i, k) { return sols().split(' ')[i] === ['la', 'ti', 're', 'mi'][k]; }), notes() + ' | ' + sols());
  setup(la); pick('tonic', 'E'); pick('mode', 'major');
  check('  the other order (tonic first, then major): the pitches stay', midis() === want, midis());
  if (la) check('  (la-based: E minor then major is G major, the key sharing E minor\'s do)', d.S().key.tonic === 'G', d.S().key.tonic);
});
// do-based C# minor labels C# as do; in E major the same pitch is la
setup(false);
check('do-based C# minor: C#4 is do', d.sortedSyls(d.S().lines[0])[0].sol === 'do');
// a note off the new scale keeps its pitch and gets a raised or lowered syllable: C natural in E major is le
s = d.S(); s.key = { tonic: 'E', mode: 'major', laMinor: true }; var c = mk(0, 'c'); c.note = 'C'; c.oct = 4; c.sol = ''; c.noteAuto = false; s.lines = [{ kind: 'line', bars: 1, syllables: [c] }]; d.renderAll();
pick('tonic', 'A');
check('a note off the new scale keeps its pitch (C4 in A major) with a lowered syllable', d.sylMidiFor(c, d.instFor(d.S())) === 60 && /^(me|ra|le|te|se)$/.test(c.sol), c.note + c.oct + ' ' + c.sol);
d.undo(); d.undo();
// C minor (la-based) to Eb major through the mode box: one step, the syllables stay, the degrees move (la 1 to la 6),
// and back to C minor
s = d.S(); s.view = 'vocals'; s.key = { tonic: 'C', mode: 'minor', laMinor: true };
var cm = ['la', 'ti', 'do', 're', 'mi'].map(function (sy, i) { var y = mk(i * 4, sy); y.sol = sy; y.noteAuto = true; y.note = ({ la: 'C', ti: 'D', do: 'Eb', re: 'F', mi: 'G' })[sy]; y.oct = 4; return y; });
s.lines = [{ kind: 'line', bars: 2, syllables: cm }]; d.renderAll();
function degs() { var k = d.S().key; return d.sortedSyls(d.S().lines[0]).map(function (y) { return d.scaleDegreeOf(y, k) + 1; }).join(' '); }
var w2 = midis(), g0 = degs();
pick('mode', 'major');
check('C minor to Eb major in one step: key Eb major', d.S().key.tonic === 'Eb' && d.S().key.mode === 'major', JSON.stringify(d.S().key));
check('  syllables stay, pitches stay', sols() === 'la ti do re mi' && midis() === w2, sols() + ' | ' + midis());
check('  degrees change (1 2 3 4 5 to 6 7 1 2 3)', g0 === '1 2 3 4 5' && degs() === '6 7 1 2 3', g0 + ' -> ' + degs());
pick('mode', 'minor');
check('  and back to C minor, degrees 1 2 3 4 5', d.S().key.tonic === 'C' && degs() === '1 2 3 4 5' && sols() === 'la ti do re mi', d.S().key.tonic + ' ' + degs());
say('LOG done');
