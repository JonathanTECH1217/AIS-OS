// Part: words. Test 3: the wordsToNotes merge rule, noUndo, the Words panel flag.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function brief(l) { return l.kind !== 'line' ? 'H' : 'bars ' + l.bars + ' ' + d.sortedSyls(l).map(function (y) { return y.text + '@' + y.pos + 'x' + d.lenSlots(y) + (y.note ? '=' + y.note : '') + (y.rest ? '(rest)' : ''); }).join(' '); }
function setup() {
  var s = d.S(); s.lines = d.parseLyrics('Twinkle twinkle little star\nHow I wonder what you are'); s.lyrics = 'Twinkle twinkle little star\nHow I wonder what you are'; s.title = 'T';
  s.lines.forEach(function (l) { var pos = 0; l.syllables.forEach(function (y) { y.note = 'E4'; y.noteAuto = false; y.sol = 'mi'; y.len = 'h'; y.pos = pos; pos += 8; }); l.bars = 4; });
  return s;
}
var s = setup();
say('LOG before: ' + s.lines.map(brief).join(' || '));
var l0 = s.lines[0].syllables, l1 = s.lines[1].syllables;
var undoBefore = d.cur().undo.length; d.state.prefs.side = true;
// (a) line 1 unchanged, line 2 with one word changed
d.wordsToNotes('Twinkle twinkle little star\nHow I wonder what YOU are', 'T', { quiet: true });
s = d.S();
say('LOG after (a): ' + s.lines.map(brief).join(' || '));
check('(a) unchanged line keeps its syllable objects and bars', s.lines[0].syllables === l0 && s.lines[0].bars === 4, 'same objects ' + (s.lines[0].syllables === l0) + ' bars ' + s.lines[0].bars);
var y1 = d.sortedSyls(s.lines[1]);
check('(a) changed line: matching syllables keep their notes', y1[0].note === 'E4' && y1[3].note === 'E4' && y1[6].note === 'E4', y1.map(function (y) { return y.text + '=' + (y.note || '-'); }).join(' '));
check('(a) changed line: the changed word is fresh (no note)', y1[5].text === 'YOU' && !y1[5].note, y1[5].text + '=' + y1[5].note);
check('(a) changed line: positions reset to one quarter per syllable', y1.every(function (y, i) { return y.pos === i * 4; }), y1.map(function (y) { return y.pos; }).join(','));
check('(a) changed line: bars reset to 1', s.lines[1].bars === 1, String(s.lines[1].bars));
var overlaps = 0; y1.forEach(function (y, i) { if (i + 1 < y1.length && y.pos + d.lenSlots(y) > y1[i + 1].pos) overlaps++; });
check('(a) kept notes do not overlap the next note (lengths kept while positions reset)', overlaps === 0, overlaps + ' of ' + y1.length + ' overlap: kept len h (8 slots) at quarter spacing');
check('(a) without noUndo the undo stack grew by one', d.cur().undo.length === undoBefore + 1, undoBefore + ' -> ' + d.cur().undo.length);
check('(a) the Words panel flag is closed by wordsToNotes', d.state.prefs.side === false, String(d.state.prefs.side));
// (b) a word added at the start of line 2 shifts every index
setup(); d.wordsToNotes('Twinkle twinkle little star\nOh how I wonder what you are', 'T', { quiet: true }); s = d.S();
var y2 = d.sortedSyls(s.lines[1]), kept = y2.filter(function (y) { return y.note === 'E4'; }).length;
say('LOG after (b): ' + brief(s.lines[1]));
check('(b) one word added at the start: notes on the same words are kept', kept === 6, kept + ' of 6 old words kept a note (matching is by index, not by word)');
// (c) a rest record in the old line shifts the indexes too
setup(); s = d.S(); var r = d.plain(s.lines[1].syllables[1]); r.rest = true; r.text = ''; r.note = ''; s.lines[1].syllables.splice(1, 0, r);
d.wordsToNotes('Twinkle twinkle little star\nHow I wonder what you are', 'T', { quiet: true }); s = d.S();
var y3 = d.sortedSyls(s.lines[1]), kept3 = y3.filter(function (y) { return y.note === 'E4'; }).length;
say('LOG after (c): ' + brief(s.lines[1]));
check('(c) same text with an old rest record in the line: all 7 notes kept', kept3 === 7, kept3 + ' of 7 kept');
// (d) noUndo leaves the undo stack alone; quiet
setup(); var u0 = d.cur().undo.length; d.state.prefs.side = true;
d.wordsToNotes('Twinkle twinkle little star\nHow I wonder what you are\nNew line here', 'T', { noUndo: true, quiet: true });
check('(d) noUndo: undo stack untouched', d.cur().undo.length === u0, u0 + ' -> ' + d.cur().undo.length);
check('(d) side flag closed even with noUndo + quiet (Place words path)', d.state.prefs.side === false, String(d.state.prefs.side));
check('(d) identical lines keep notes, the new line is fresh', d.S().lines[0].syllables[0].note === 'E4' && d.S().lines[1].syllables[0].note === 'E4' && !d.S().lines[2].syllables[0].note);
// (e) the same text again: nothing changes
setup(); var snap = JSON.stringify(d.S().lines); d.wordsToNotes('Twinkle twinkle little star\nHow I wonder what you are', 'T', { quiet: true });
check('(e) the same text keeps every line as it was', JSON.stringify(d.S().lines) === snap);
// (f) a header added above shifts line indexes: notes lost?
setup(); d.wordsToNotes('[Verse]\nTwinkle twinkle little star\nHow I wonder what you are', 'T', { quiet: true }); s = d.S();
var keptF = 0; s.lines.forEach(function (l) { if (l.kind === 'line') l.syllables.forEach(function (y) { if (y.note === 'E4') keptF++; }); });
check('(f) a header added above: the 14 notes are kept', keptF === 14, keptF + ' of 14 kept (lines are matched by index, a header shifts them)');
say('LOG sheet.lyrics after: ' + JSON.stringify(d.S().lyrics.slice(0, 40)) + ' title ' + JSON.stringify(d.S().title));
