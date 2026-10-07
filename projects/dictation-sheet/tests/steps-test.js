// A step up or down the scale goes to the next scale note by pitch, in every key, with no octave jumps; the readout
// names the degree, syllable and note.
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
var keys = [['C', 'major'], ['G', 'major'], ['F', 'major'], ['B', 'major'], ['Eb', 'major'], ['A', 'minor'], ['E', 'minor'], ['F#', 'minor']];
s.view = 'vocals';
keys.forEach(function (k) {
  s.key = { tonic: k[0], mode: k[1], laMinor: true };
  var y = d.normalize({ lines: [{ kind: 'line', syllables: [{ text: 'x', pos: 0 }] }] }).lines[0].syllables[0];
  y.sol = 'do'; y.noteAuto = true; y.note = ''; y.oct = 3; d.stepDiatonic(y, s.key, 0, 3); // puts it on do
  y.oct = 3;
  var inst = d.instFor(s), path = [d.sylMidiFor(y, inst)], bad = [];
  for (var i = 0; i < 16; i++) { d.stepDiatonic(y, s.key, 1, 3); path.push(d.sylMidiFor(y, inst)); }
  for (i = 0; i < 16; i++) { d.stepDiatonic(y, s.key, -1, 3); path.push(d.sylMidiFor(y, inst)); }
  for (i = 1; i < path.length; i++) { var st = path[i] - path[i - 1], up = i <= 16; if (up ? !(st === 1 || st === 2) : !(st === -1 || st === -2)) bad.push(i + ':' + st); }
  check(k[0] + ' ' + k[1] + ': 16 steps up and 16 down, each a scale step (1 or 2 half steps), back where it began', bad.length === 0 && path[0] === path[path.length - 1] && path[16] - path[0] >= 26 && path[16] - path[0] <= 28, bad.join(' ') + ' | ' + path.join(','));
});
// G major: ti (B4) up one is do (G? no: C5), never C4
s.key = { tonic: 'G', mode: 'major', laMinor: true };
var y2 = d.normalize({ lines: [{ kind: 'line', syllables: [{ text: 'x', pos: 0 }] }] }).lines[0].syllables[0];
y2.note = 'B'; y2.sol = 'mi'; y2.noteAuto = true; y2.oct = 4;
d.stepDiatonic(y2, s.key, 1, 4);
check('G major: B4 (mi) up one step is C5 (fa), not C4', y2.note === 'C' && y2.oct === 5 && y2.sol === 'fa', y2.note + y2.oct + ' ' + y2.sol);
check('the readout: "4 · fa · C5"', d.pitchLabel(y2, s) === '4 · fa · C5', d.pitchLabel(y2, s));
s.view = 'guitar'; s.key = { tonic: 'A', mode: 'minor', laMinor: true };
y2.note = 'C'; y2.sol = 'do'; y2.oct = 5;
check('A minor, Guitar: C5 reads as degree 3 from the tonic A', d.pitchLabel(y2, s) === '3 · do · C5', d.pitchLabel(y2, s));
s.view = 'vocals'; s.key = { tonic: 'C', mode: 'major', laMinor: true };
say('LOG done');
