# quantizer

## Tested
- `quantizer-prop.js`: 500 random lines (2-12 syllables, gaps 0.05-2 s, 20% unknown releases, 30% hy, next-line onset or null, random floorSlot) at 120 bpm, then 500 each at 76 and 160: invariants, rest histogram, hy-flip probe.
- `quantizer-tempo.js`: collisions and mean |placement error| at 76/100/120/160 bpm for 3-6 syl/s (8 syllables, 200 lines each) and on the random spans; against plain rounding (the 16th-grid floor), an optimal monotone DP, a 1-step backtrack, a 32nd grid.
- `quantizer-bars.js`: the real `autoPlaceWords` (fake /lyrics, fake track with a voice band and no onset curve, straight grid from offsetSec 10), 11 scenarios: barline overlap, held last word (2), pickup squeeze, 3-bar silence, 3/4, 6/8 at 240, marker line, note on slot 63, 64- and 66-slot holds. After each: int pos, len 1..64, no overlap, bars >= minBars, barOrdinal = sum of lineBars, no NaN, undo then fill again.
- `quantizer-edges.js`: MAX_SLOTS edges, setSlotsRaw/lenSlots round trip 1..64 and out of range, trimAtBar/minBars/lineBars/barOrdinal.
- `quantizer-marker.js`: the "♪" case on the heard-song path (e2e2 song, beats locked). `quantizer-probe.js`: why a long hold loses its onset.

## Findings
1. HIGH. A symbol-only LRC line ("♪", common on LRCLIB) before the first sung line puts that line a whole bar late and crushes its first syllables to consecutive sixteenths; "♪" itself draws as a quarter note in bar 1. Heard-song path: sung slots [9,11,15,21,23,27] -> sheet [16,17,18,21,23,27] (875/750/375 ms late); the toast blames "a line the line before still uses". Straight-grid path (bars G): [16,13,10] slots late.
2. MEDIUM. Pickups: when the previous line's last note starts in the bar the next line begins in, the next line "waits for the barline" and its early syllables fold to pos 0,1,2 with length 1 (bars C): song slots [28,30,32,36] -> sheet [32,33,34,36], 500/375/250/0 ms late, rhythm lost. By design (toast says so), but it is the most common phrase shape in vocal music and the sheet then disagrees with the song for that line.
3. MEDIUM. Rule FILL's hy branch is dead code: its guard `nextSlot - end <= 1` is exactly ABSORB's case. Flipping every hy flag changed none of 500 outputs; a hy pair with a 2-slot rounded gap gets a rest inside the word (edges: [[0,2],[4,1]]).
4. LOW. A 1-slot rest survives after a 64-slot hold when the next onset is at +65 (ABSORB needs nextSlot <= cap): [[0,64],[65,1]]. Otherwise 0 one-slot rests in 1500 random lines (rest histogram at 120: 0:1442 2:300 3:288 4:202 5:148 6:157 7:134 8:115 ... 15:7).
5. LOW. `setSlotsRaw(NaN|undefined)` leaves `xs = NaN` (lenSlots masks it with `xs || 0`, normalize zeroes it on reload). No NaN reached it in any fill.
6. INFO, rounding. Collisions: 0% up to 6 syl/s at 120+ bpm, 1.8% at 100 bpm/6 syl/s, 6.3% at 76/5, 49.5% at 76/6 (185 of 200 lines). Mean |error| equals the 16th-grid floor within 3 ms everywhere except 76 bpm at 6 syl/s: 116 vs 49 ms, 296/1600 syllables a full slot (197 ms) or more late; worst line sung [0.52,1.36,2.05,2.87,3.54,4.45,5.2,5.91] slots -> [1..8], errors 95..413 ms. At 76/5: sung [0.54,...,5.92,7.12] -> [1..8], syllable 7 lands 213 ms late because 0.54 rounded up and pushed the chain (DP: [0..7], max 107 ms). DP gains <= 1.3 ms mean on random spans and still leaves 48 late at 76/6 (6 syl/s > 5.07 slots/s cannot fit). A 32nd grid halves the error (25/19/15/12 ms) but LENS has no 32nd. Random spans mean |error|: 52/39/32/23 ms at 76/100/120/160.
7. PASS: invariants over 1500 random lines (strictly increasing, len 1..64, no overlap, floor, last <= lineEnd); hy pairs with a sung gap under a slot never split (0/151); held last word trimmed at the barline (25 -> 20 slots); 3 bars of silence become bars=4 on the previous line, no +bar needed; 3/4 and 6/8 (spb 12, spBeat 4 and 2) place identically; note on slot 63 held over the barline trimmed to 1, minBars 4; 64-slot hold kept, 65/200 capped at 64; setSlotsRaw/lenSlots round trip exact 1..64; barOrdinal = sum of lineBars in every scenario; undo then fill again gives the identical sheet in all 11 scenarios.

## Root causes
- 1: index.html 3062-3063 take the `lead` bars off bar 1 only when `!sa.lined`; gridFromSong (2383-2390) has already put bar 1 on the first sung word's downbeat and set `lined`, so the unplaced line's bar (`between`, 3083) has nowhere to go: `ord = between > startBar` (3084-3091) and `pos = max(c, slot - base)` (3095) folds to 0,1,2. Line 3026 keeps "♪" as a sheet line (syllableTexts gives it a syllable) while alignLines (wordsOf strips symbols, sim 0) can never match it.
- 2: 3086-3091: trimAtBar cuts only a note that straddles `want*spb`; a note starting at or after it lifts minBars(prev) above `want`, so `ord > startBar`, and 3095 folds the negative offsets.
- 3: 2972 `nextSlot - end <= 1 && (hy || legato)`; 2974 already fills a gap of 1 for everyone.
- 4: 2974 `nextSlot <= cap` while `end == cap`.

## Overlaps
- Onsets (sungSpansIn, lineLevels 2857): the floor is the 10th percentile of the window, so a window >90% one held note (probe: 8.2 s hold in an 8.6 s window) gets floor 2.25, the gate rises above the note's own wiggle, no onset, evenSpans fallback (bars L: "one" became a whole note, voice used on 1 of 2 lines).
- Notation (notePiecesAt): notes starting on odd sixteenths across beats split into tied heads; likely the 6-syllable/8-head report.
- Tempo (tempoOf/gridFromSong): the one bad grid case (76 bpm at 6 syl/s) is a half-tempo read, not a rounding problem.
- Playhead: findings 1 and 2 put one line's sheet slots up to a bar off the song; a candidate for "the highlight skips".

## Fixes (none made)
- 1: in step 1 drop lines with no letter or digit from `text` (keep them in `lrc` for the windows): `.filter(function (l) { return /[\p{L}\p{N}]/u.test(l); })`; and when the first placed line has `startBar < between`, move bar 1 back by `between - startBar` bars (offsetSec, or the beats index when locked) instead of squeezing, i.e. give gridFromSong the same `lead` the unheard path takes at 3062.
- 2: before squeezing, pull the previous line's notes that start at or after `cut` back to end at `cut` (pos = cut - k, len 1, chained backwards) when the overhang is <= a beat; when a squeeze is unavoidable keep the rhythm (`pos_i = e.slot - q[0].slot + firstPos`) instead of folding to 0,1,2, and say in the toast that the line plays late.
- 3: `if (nextSlot <= cap && sp.y && sp.y.hy) end = nextSlot; else if (nextSlot - end <= 1 && legato) end = nextSlot;`, or drop the hy clause and its comment.
- 4: accept, or `if (nextSlot - end === 1 && nextSlot > cap) end--` so the rest is 2 slots.
- 5: `if (!isFinite(+n)) n = 1;` at the top of setSlotsRaw.
- 6: keep the 16th grid and Math.round; a DP assignment is not worth it. Add a half-tempo guard instead: when the median sung inter-onset interval on a line is under ~1.2 slots, warn or double the bpm.

## Confidence
High on 1-5 and 7 (reproduced in the real functions, numbers above). Medium on the DP and 32nd-grid figures (synthetic onsets, uniform jitter). Medium on the overlaps (code read, not tested beyond the probe).
