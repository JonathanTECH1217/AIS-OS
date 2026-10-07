// Round trip: a full sheet through plain -> JSON (file format) -> normalize, every field compared; then an OLD sheet
// (no filled, xs 15, pos missing, odd values) through normalize. Leaves the old sheet in ds-tabs for persist-boot.js.
var d = window.__ds;
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function diff(a, b, path, out) {
  path = path || '$'; out = out || [];
  if (a === b) return out;
  var ta = a === null ? 'null' : Array.isArray(a) ? 'array' : typeof a, tb = b === null ? 'null' : Array.isArray(b) ? 'array' : typeof b;
  if (ta !== tb) { out.push(path + ': ' + JSON.stringify(a) + ' -> ' + JSON.stringify(b)); return out; }
  if (ta === 'array') { var n = Math.max(a.length, b.length); for (var i = 0; i < n; i++) diff(a[i], b[i], path + '[' + i + ']', out); return out; }
  if (ta === 'object') { var keys = {}; Object.keys(a).forEach(function (k) { keys[k] = 1; }); Object.keys(b).forEach(function (k) { keys[k] = 1; }); Object.keys(keys).forEach(function (k) { if (!(k in a)) out.push(path + '.' + k + ': (absent) -> ' + JSON.stringify(b[k])); else if (!(k in b)) out.push(path + '.' + k + ': ' + JSON.stringify(a[k]) + ' -> (absent)'); else diff(a[k], b[k], path + '.' + k, out); }); return out; }
  out.push(path + ': ' + JSON.stringify(a) + ' -> ' + JSON.stringify(b)); return out;
}
try { localStorage.clear(); } catch (e) { /* ignore */ }

// ---- 1. a full sheet
var s = d.S();
s.title = 'Round trip'; s.lyrics = '[Verse]\nTwin-kle star\nHo-ly night\n'; s.time = '4/4'; s.bpm = 110.37;
s.key = { tonic: 'Eb', mode: 'minor', laMinor: false }; s.view = 'piano'; s.instrument = 'piano'; s.tuning = 442;
s.lines = d.parseLyrics(s.lyrics);
var L1 = s.lines[1], L2 = s.lines[2];
say('LOG parsed line 1: ' + L1.syllables.map(function (y) { return y.text + (y.hy ? '-' : ''); }).join(' ') + ' | line 2: ' + L2.syllables.map(function (y) { return y.text + (y.hy ? '-' : ''); }).join(' '));
var a = L1.syllables[0], b = L1.syllables[1], c = L1.syllables[2];
d.setSlotsRaw(a, 40); b.pos = 40; c.pos = 44; d.setSlotsRaw(c, 64);
a.note = 'C'; a.oct = 5; a.sol = 'do'; a.noteAuto = false; a.drum = ['kick', 'hh']; a.guitar = { s: 2, f: 5, auto: false };
b.note = 'F#'; b.oct = 3; b.sol = 'sol'; b.drum = ['snare']; b.piano.hand = 'L'; b.bass = { s: 1, f: 3, auto: false };
c.note = 'Bb'; c.oct = null; c.tie = true; c.drum = ['hh', 'crash', 'tom1', 'ftom'];
L1.bars = 7;
var r = d.plain(L2.syllables[0]); r.text = ''; r.rest = true; r.pos = 8; r.len = '8'; r.dot = true; r.xs = 0; r.hy = false; L2.syllables.push(r);
L2.syllables[0].note = 'G'; L2.syllables[0].oct = 4; L2.syllables[1].pos = 11; L2.syllables[1].tie = true; L2.syllables[1].note = 'G'; L2.syllables[1].oct = 4;
if (L2.syllables[2] && L2.syllables[2] !== r) L2.syllables[2].pos = 12;
L2.bars = 2;
var beats = []; for (var i = 0; i < 300; i++) beats.push(Math.round((19.123 + i * 0.5 + Math.sin(i) * 0.01) * 1000) / 1000);
s.audio = { offsetSec: 19.123, lined: true, name: 'song.mp3', assetId: null, forTrack: 'trk1', beats: beats, locked: true, lockFit: { onHit: 91, avgMs: 12 } };
s.spotify = { trackId: 'x1', name: 'T · A', durationMs: 304000, title: 'T', artist: 'A', album: 'B' };
s.filled = { key: 'spotify:x1', title: 'T' };
s.attempts = [{ when: 1, hidden: ['sol'], score: 80 }]; s.createdBy = 'me'; s.updatedAt = 1700000000000;

var p0 = d.plain(s);
var text = JSON.stringify(Object.assign(d.plain(s), { format: 'dictation-sheet/2' }), null, 2);
var back = d.normalize(JSON.parse(text));
var df = diff(p0, d.plain(back));
check('round trip plain -> JSON -> normalize keeps every field', df.length === 0, df.length ? df.join(' | ') : '');
check('file text carries format dictation-sheet/2 and it is dropped on load', /"format": "dictation-sheet\/2"/.test(text) && back.format === undefined);
var back2 = d.normalize(d.plain(back)); var df2 = diff(d.plain(back), d.plain(back2));
check('normalize is idempotent', df2.length === 0, df2.join(' | '));
check('40-slot note kept (w + 24)', back.lines[1].syllables[0].len === 'w' && back.lines[1].syllables[0].xs === 24 && d.lenSlots(back.lines[1].syllables[0]) === 40, JSON.stringify({ len: back.lines[1].syllables[0].len, xs: back.lines[1].syllables[0].xs }));
check('64-slot note kept (w + 48)', d.lenSlots(back.lines[1].syllables[2]) === 64, String(d.lenSlots(back.lines[1].syllables[2])));
check('audio: 300 beats, locked, offset 19.123, forTrack', back.audio.beats.length === 300 && back.audio.locked === true && back.audio.offsetSec === 19.123 && back.audio.forTrack === 'trk1');
check('spotify + filled kept', back.spotify.trackId === 'x1' && back.spotify.durationMs === 304000 && back.filled.key === 'spotify:x1');
check('rest, tie, hy, drum, oct, fixed fret kept', back.lines[2].syllables[back.lines[2].syllables.length - 1].rest === true && back.lines[2].syllables[1].tie === true && back.lines[1].syllables[0].hy === true && back.lines[1].syllables[2].drum.length === 4 && back.lines[1].syllables[0].oct === 5 && back.lines[1].syllables[0].guitar.auto === false && back.lines[1].syllables[0].guitar.f === 5);
check('header line kept', back.lines[0].kind === 'header' && back.lines[0].text === 'Verse');
say('LOG sheet JSON (pretty, with 300 beats): ' + text.length + ' chars');

// what sheetAudio()'s own default shape becomes after a save/load
var defAudio = { offsetSec: 0, lined: false, name: '', assetId: null, beats: null, locked: false, lockFit: null };
var s2 = d.normalize({ lines: [], audio: defAudio });
var df3 = diff(defAudio, s2.audio);
say('LOG sheetAudio() default shape through normalize: ' + (df3.length ? df3.join(' | ') : 'identical'));
// a sheet whose song was switched: lined false but the old offset still there
var s3 = d.normalize({ lines: [], audio: { offsetSec: 12.5, lined: false, beats: null, locked: false } });
check('lined:false with offsetSec>0 (song switched, spUseTrack) stays false after a load', s3.audio.lined === false, 'lined -> ' + s3.audio.lined);
// an audio record with locked:true but no beats
var s4 = d.normalize({ lines: [], audio: { offsetSec: 1, lined: true, beats: [1.0], locked: true } });
check('locked with one beat is unlocked on load', s4.audio.locked === false);
// syllable text as a number, bpm as a string
var s5 = d.normalize({ bpm: '95', lines: [{ kind: 'line', syllables: [{ text: 5, pos: 0 }] }] });
check('bpm "95" (string) becomes a number on load', typeof s5.bpm === 'number', 'bpm is ' + typeof s5.bpm + ' ' + JSON.stringify(s5.bpm));
check('text 5 (number) becomes a string on load', typeof s5.lines[0].syllables[0].text === 'string', 'text is ' + typeof s5.lines[0].syllables[0].text);

// ---- 2. an old sheet
var old = { title: 'Old', lyrics: 'a b', bpm: 95, time: '3/4', lines: [
  { kind: 'line', syllables: [{ text: 'a', len: 'q', xs: 15 }, { text: 'b', len: 'w', xs: 15, dot: true }, { text: 'c', len: 'x', xs: 200, pos: '7' }, { text: 'd', xs: -3 }, { text: 'e', xs: 'abc' }, { text: 'f', pos: 3.6, len: '8' }, { text: 'g', pos: null }] },
  { kind: 'header', text: 'Chorus' },
  { kind: 'line', bars: 0, syllables: [{ text: 'h' }] },
  { kind: 'line' }, { kind: 'weird', syllables: [{ text: 'z', drum: 'kick', guitar: null }] }
], audio: { offsetSec: 3.5 }, spotify: { name: 'no id' }, key: { tonic: 'G' }, instrument: 'ukulele', view: 'banjo', tuning: 999 };
// corrupt shapes, each on its own
[['lines: [null]', { lines: [null] }], ['lines: ["x"]', { lines: ['x'] }], ['lines: [{syllables: null}]', { lines: [{ kind: 'line', syllables: null }] }], ['syllables: [null]', { lines: [{ kind: 'line', syllables: [null] }] }], ['syllables: ["x"]', { lines: [{ kind: 'line', syllables: ['x'] }] }], ['lines: "x"', { lines: 'x' }], ['key: "C"', { lines: [], key: 'C' }], ['audio: "x"', { lines: [], audio: 'x' }], ['spotify: 5', { lines: [], spotify: 5 }], ['filled: "k"', { lines: [], filled: 'k' }], ['attempts: {}', { lines: [], attempts: {} }], ['lines: [{kind:"header", text: null}]', { lines: [{ kind: 'header', text: null }] }], ['syllable guitar: "x"', { lines: [{ kind: 'line', syllables: [{ text: 'a', guitar: 'x', piano: 3, bass: [] }] }] }]].forEach(function (c2) {
  var e2 = null; try { d.normalize(c2[1]); } catch (e) { e2 = e; }
  check('normalize survives ' + c2[0], !e2, e2 && String(e2.message));
});
var o = null, err = null; try { o = d.normalize(JSON.parse(JSON.stringify(old))); } catch (e) { err = e; }
check('old sheet normalizes without error', !err, err && err.stack);
if (o) {
  var ys = o.lines[0].syllables;
  say('LOG old line 0: ' + ys.map(function (y) { return y.text + ' pos ' + y.pos + ' len ' + y.len + (y.dot ? '.' : '') + ' xs ' + y.xs + ' =' + d.lenSlots(y); }).join(' | '));
  check('filled defaults to null', o.filled === null);
  check('xs 15 kept on a quarter (19 slots)', ys[0].xs === 15 && d.lenSlots(ys[0]) === 19);
  check('xs 200 clamped so the note is 64 slots', d.lenSlots(ys[2]) === 64, 'xs ' + ys[2].xs + ' len ' + ys[2].len);
  check('bad len falls back to q', ys[2].len === 'q');
  check('negative / non-numeric xs -> 0', ys[3].xs === 0 && ys[4].xs === 0);
  check('pos missing / string / null -> after the note before', typeof ys[2].pos === 'number' && ys[2].pos === ys[1].pos + d.lenSlots(ys[1]) && typeof ys[6].pos === 'number' && ys[6].pos === ys[5].pos + d.lenSlots(ys[5]), JSON.stringify(ys.map(function (y) { return y.pos; })));
  check('pos 3.6 rounds to 4', ys[5].pos === 4);
  check('bars 0 -> 1', o.lines[2].bars === 1);
  check('line without syllables and unknown kind survive as lines', o.lines[3].syllables.length === 0 && o.lines[4].kind === 'line');
  check('drum "kick" (string) -> []', Array.isArray(o.lines[4].syllables[0].drum) && o.lines[4].syllables[0].drum.length === 0);
  check('guitar null -> default', !!o.lines[4].syllables[0].guitar && o.lines[4].syllables[0].guitar.auto === true);
  check('audio {offsetSec:3.5} -> lined true, beats null, locked false', o.audio.lined === true && o.audio.beats === null && o.audio.locked === false, JSON.stringify(o.audio));
  check('spotify without trackId -> null', o.spotify === null);
  check('key {tonic:G} -> major, laMinor', o.key.mode === 'major' && o.key.laMinor === true);
  check('unknown instrument/view -> guitar', o.instrument === 'guitar' && o.view === 'guitar');
  check('tuning 999 -> 440', o.tuning === 440);
  d.cur().sheet = o; d.renderAll();
  check('renders the old sheet without NaN or draw errors', document.querySelectorAll('[style*="NaN"]').length === 0 && !document.querySelector('.noteshint'), (document.querySelector('.noteshint') || {}).textContent);
  var xo = null, xe = null; try { xo = d.musicXML(o); d.midiBytes(o); d.asText(); } catch (e) { xe = e; }
  check('old sheet exports (xml, midi, text) without error', !xe, xe && xe.message);
}
// leave the raw old sheet for the boot check
localStorage.setItem('ds-tabs', JSON.stringify({ tabs: [{ id: 'oldsheet1', sheet: old }], active: 0 }));
localStorage.setItem('ds-store', JSON.stringify({ oldsheet1: old }));
say('LOG wrote raw old sheet into ds-tabs/ds-store for persist-boot.js');
