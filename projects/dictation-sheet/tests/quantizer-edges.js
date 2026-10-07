// quantizer-edges.js: MAX_SLOTS edges of quantizeSpans, setSlotsRaw/lenSlots/lenFromSlots round trips, trimAtBar and
// minBars on a note at slot 63. Run: PROFILE=prof-quantizer python pagecheck.py stage.html quantizer-edges.js
var d = window.__ds, s = d.S();
function say(t) { var o = document.getElementById('__out'); if (o) o.textContent += '\n' + t; else __lines.push(t); }
function check(name, ok, detail) { say((ok ? 'PASS ' : 'FAIL ') + name + (detail ? ': ' + detail : '')); }
function eq(name, got, want) { var g = JSON.stringify(got), w = JSON.stringify(want); check(name, g === w, g + (g === w ? '' : ' (want ' + w + ')')); }
var OFF = 10; s.bpm = 120; s.time = '4/4'; s.audio = { offsetSec: OFF, lined: true, name: '', assetId: null, beats: null, locked: false, lockFit: null };
var sl = d.audioNominalSlotSec(); // 0.125
function sp(on, off, hy) { return { y: { hy: !!hy }, on: OFF + on * sl, off: off === null ? null : OFF + off * sl }; }
function q(spans, next, floor) { return d.quantizeSpans(spans, next === null ? null : OFF + next * sl, floor).map(function (e) { return [e.slot, e.lenSlots]; }); }
eq('a 64-slot note', q([sp(0, 64)], null, 0), [[0, 64]]);
eq('a 65-slot span is capped at 64', q([sp(0, 65)], null, 0), [[0, 64]]);
eq('a 200-slot span is capped at 64', q([sp(0, 200)], null, 0), [[0, 64]]);
eq('a 64-slot hold then the next onset at 65: a 1-slot rest survives (ABSORB skipped because nextSlot > cap)', q([sp(0, 64.4), sp(65, 66)], null, 0), [[0, 64], [65, 1]]);
eq('a 64-slot hold then the next onset at 66: a 2-slot rest', q([sp(0, 64.4), sp(66, 67)], null, 0), [[0, 64], [66, 1]]);
eq('a 63-slot hold then the next onset at 64: filled to 64 (ABSORB, nextSlot == cap)', q([sp(0, 63), sp(64, 65)], null, 0), [[0, 64], [64, 1]]);
eq('unknown release, next line 65 slots later: held to the cap? (last word with off null is one sixteenth)', q([sp(0, null)], 65, 0), [[0, 1]]);
eq('unknown release, not last, next onset 65 slots later: held to the cap 64, then a 1-slot rest', q([sp(0, null), sp(65, 66)], null, 0), [[0, 64], [65, 1]]);
eq('last word ends at the next line onset (open release just before it)', q([sp(0, 7.4)], 8, 0), [[0, 8]]);
eq('last word release rounds past the next line onset: capped at it', q([sp(0, 9.4)], 8, 0), [[0, 8]]);
eq('next line onset before the last onset: line end = last + 1', q([sp(0, 2), sp(6, 7)], 3, 0), [[0, 2], [6, 1]]);
eq('floorSlot above every onset: consecutive from the floor', q([sp(0, 1), sp(1, 2), sp(2, 3)], null, 10), [[10, 1], [11, 1], [12, 1]]);
eq('floorSlot NaN treated as 0', q([sp(2, 3)], null, NaN), [[2, 1]]);
eq('onsets before bar 1 clamp to 0 and chain', q([sp(-5, -4), sp(-3, -2), sp(-1, 0.4)], null, 0), [[0, 1], [1, 1], [2, 1]]);
eq('empty spans', q([], null, 0), []);
eq('hy pair with a 2-slot gap is NOT filled (hy FILL needs gap <= 1, same as ABSORB)', q([sp(0, 2, true), sp(4, 5)], null, 0), [[0, 2], [4, 1]]);
eq('hy pair with a 1-slot gap is filled', q([sp(0, 3, true), sp(4, 5)], null, 0), [[0, 4], [4, 1]]);
eq('non-hy pair with a 1-slot gap is filled too (ABSORB)', q([sp(0, 3), sp(4, 5)], null, 0), [[0, 4], [4, 1]]);
eq('legato under 60 ms with a 1-slot rounded gap filled', q([sp(0, 1.4), sp(2.6, 3.6)], null, 0), [[0, 3], [3, 1]]);
// setSlotsRaw / lenSlots / lenFromSlots round trip
var bad = [], y = { len: 'q', dot: false, xs: 0 }, n;
for (n = 1; n <= 64; n++) { d.setSlotsRaw(y, n); var back = d.lenSlots(y); if (back !== n || y.xs < 0) bad.push(n + '->' + back + '(' + y.len + (y.dot ? '.' : '') + '+' + y.xs + ')'); }
check('setSlotsRaw then lenSlots gives back every n in 1..64 with xs >= 0', bad.length === 0, bad.join(' '));
var pieces = []; [1, 2, 3, 4, 5, 6, 7, 8, 12, 13, 15, 16, 17, 24, 32, 48, 63, 64].forEach(function (k) { d.setSlotsRaw(y, k); pieces.push(k + ':' + y.len + (y.dot ? '.' : '') + '+' + y.xs); }); say('LOG setSlotsRaw pieces: ' + pieces.join(' '));
[[0, 1], [65, 64], [100, 64], [-3, 1], [2.5, 3], [2.4, 2], [Infinity, 64], [-Infinity, 1]].forEach(function (c) { d.setSlotsRaw(y, c[0]); check('setSlotsRaw(' + c[0] + ') -> ' + c[1], d.lenSlots(y) === c[1], 'got ' + d.lenSlots(y)); });
d.setSlotsRaw(y, NaN); check('setSlotsRaw(NaN) leaves a finite length (it does not: NaN passes Math.max(1, Math.min(64, NaN)))', isFinite(d.lenSlots(y)), 'lenSlots ' + d.lenSlots(y) + ' len ' + y.len + ' xs ' + y.xs);
d.setSlotsRaw(y, undefined); check('setSlotsRaw(undefined) leaves a finite length', isFinite(d.lenSlots(y)), 'lenSlots ' + d.lenSlots(y) + ' xs ' + y.xs);
eq('lenFromSlots 0 and NaN fall to a sixteenth', [d.lenFromSlots(0), d.lenFromSlots(NaN)], [{ len: '16', dot: false }, { len: '16', dot: false }]);
// trimAtBar and minBars on a note at slot 63 of a 4-bar line
function line(pos, len) { var yy = { text: 'x', pos: pos, len: 'q', dot: false, xs: 0, rest: false, hy: false }; d.setSlotsRaw(yy, len); return { kind: 'line', bars: 1, syllables: [yy] }; }
var l1 = line(63, 64); check('note at 63 held 64: minBars 8', d.minBars(l1, 16) === 8, 'got ' + d.minBars(l1, 16));
d.trimAtBar(l1, 64); check('trimAtBar at 64 cuts it to 1 slot, minBars 4', d.lenSlots(l1.syllables[0]) === 1 && d.minBars(l1, 16) === 4, 'len ' + d.lenSlots(l1.syllables[0]) + ' minBars ' + d.minBars(l1, 16));
var l2 = line(63, 1); d.trimAtBar(l2, 64); check('note at 63 of 1 slot is left alone by trimAtBar(64)', d.lenSlots(l2.syllables[0]) === 1 && d.minBars(l2, 16) === 4);
var l3 = line(64, 4); d.trimAtBar(l3, 64); check('note starting AT the cut is not trimmed (starts in the next bar): minBars 5', d.lenSlots(l3.syllables[0]) === 4 && d.minBars(l3, 16) === 5, 'len ' + d.lenSlots(l3.syllables[0]) + ' minBars ' + d.minBars(l3, 16));
var l4 = { kind: 'line', bars: 1, syllables: [] }; check('empty line: minBars 1, lineBars 1', d.minBars(l4, 16) === 1 && d.lineBars(l4, 16) === 1);
var l5 = line(0, 16); l5.bars = 3; check('lineBars keeps a larger bars setting (3) over minBars (1)', d.lineBars(l5, 16) === 3 && d.minBars(l5, 16) === 1);
var l6 = line(0, 16); l6.bars = 0; check('lineBars with bars 0 falls to minBars', d.lineBars(l6, 16) === 1);
// barOrdinal: headers skipped, sum of lineBars
var sheet = { time: '4/4', lines: [line(0, 16), { kind: 'header', text: 'x' }, line(20, 4), line(0, 4)] }; sheet.lines[0].bars = 2;
check('barOrdinal: line0 bars 2, header skipped, line2 (pos 20 -> minBars 2) -> ordinals 0, -, 2, 4', d.barOrdinal(sheet, 0, 0) === 0 && d.barOrdinal(sheet, 2, 0) === 2 && d.barOrdinal(sheet, 3, 0) === 4 && d.barOrdinal(sheet, 1, 0) === -1 && d.barOrdinal(sheet, 2, 1) === 3, [d.barOrdinal(sheet, 0, 0), d.barOrdinal(sheet, 1, 0), d.barOrdinal(sheet, 2, 0), d.barOrdinal(sheet, 3, 0)].join(','));
// 6/8 and 3/4 slot math on the straight grid
s.time = '6/8'; s.bpm = 240; check('6/8 at 240: a sixteenth is 125 ms, a bar 1.5 s (12 slots)', Math.abs(d.audioNominalSlotSec() - 0.125) < 1e-9 && Math.abs(d.slotOfSong(11.5) - 12) < 1e-9, d.audioNominalSlotSec() + ' ' + d.slotOfSong(11.5));
s.time = '3/4'; s.bpm = 120; check('3/4 at 120: a sixteenth is 125 ms, a bar 1.5 s (12 slots)', Math.abs(d.audioNominalSlotSec() - 0.125) < 1e-9 && Math.abs(d.slotOfSong(11.5) - 12) < 1e-9, d.audioNominalSlotSec() + ' ' + d.slotOfSong(11.5));
s.time = '4/4';
