# notation

## Tested
- `notation-probe.js` (pagecheck, stage.html): three candidate timings for "You could be my someone", SVG dump (heads, ties, texts, chips, `barTokens`).
- `notation-sweep.js`, `notation-sweep2.js` (pagecheck, 384 renders each): one syllable at every pos 0..15 x len 1..24 in 4/4: drawn heads vs `barTokens` pieces, ties vs piece pairs (VexFlow 3 draws a tie as a bare root `<path>` with two `Q` curves), tie widths by pair and by within-bar vs over-barline, dots, rests, empty bars (4/4, 3/4), 6/8 dotted rest, one-bar-per-system break (zoom 100000), chips over two systems, lyric x vs head x, the sample sheet.
- `notation-vfver.py`, `notation-cdnjs.py`, `notation-jsdelivr.py`: which VexFlow is inlined in stage.html and the desktop build, and what cdnjs serves.
- Screenshots (`shot.py` 2600x700, `notation-crop.py` x2-4): `notation-crop-B.png` (synthetic line), `notation-crop-worst.png`, `notation-crop-break1.png`, `notation-crop-break2.png`.

## Findings
1. HIGH. The page runs VexFlow 3.0.9, not 4.2.5. `cdnjs .../vexflow/4.2.5/vexflow-min.js` is the legacy build (its tail reads "YOU ARE LOOKING AT VEXFLOW LEGACY VERSION 3.0.9"; cdnjs 4.2.5 lists only `vexflow-min.js`, `vexflow-debug.js` and their `.min.min.js` copies, all legacy; `vexflow.js` is a 404). In the page `Vex.Flow.BUILD` is undefined, `Vex.Flow.Dot.buildAndAttach` undefined, `StaveNote.prototype.addDotToAll` is a function. Same 754,296-byte file is inlined in stage.html and `Dictation Sheet.html`.
2. HIGH. No dot is ever drawn: 245 of 384 sweep renders wanted a dot, 0 were drawn (every dotted 8th, quarter, half). A 3-slot syllable is a dotted 8th that looks like a plain 8th with no rest after it.
3. HIGH. A tie from a 16th piece to its continuation one slot later is 0.44 px wide: 69 of 591 ties (pos 3, 7, 11, every len 2..24). Heads sit at 217.3..229.2 and 229.7..241.6 (slot 12.4 px); tie path `M229.2 87 Q229.4 85 229.7 87 Q229.4 79 229.2 87 Z`, a hairline "^". The same pair over a barline is 17.4 px and visible. Heads always equalled pieces and ties always equalled pieces-1 in all 384 renders: nothing is missing, it is unreadable.
4. Issue 1 reproduced: You@2x3 could@5x3 be@8x3 my@11x3 some@14x4 one@18x3 in 4/4 gives 8 gray heads, 4 flags, ties 0.4 px and 29.8 px, 0 dots, head spacing 3:3:3:1:2 slots, no rests between: the user's picture exactly (`notation-crop-B.png`). "my" = 16th+8th with the invisible tie, "some" = 8th + 8th over the barline (tie visible), You/could/be/one = dotted 8ths without dots. 6 syllables, 8 heads.
5. MEDIUM. A note held over a system break has no outgoing tie on the first system: sys 0 ties 0, sys 1 ties 1 (w12, from the clef to the carry). `notation-crop-break1.png`.
6. MEDIUM. A hyphenated word crossing a system break has no chip on the second system: "someone," chip clipped at the end of system 1, system 2 chips: none, although "one," is drawn on the staff. Nothing to click, drag or highlight there.
7. LOW. Dotted rests lose the dot: a 6-slot gap in 6/8 is a dotted-quarter rest in tokens (`rq.x6`), drawn plain (0 dots).
8. LOW. Words, hyphens and extenders are centred on the head's left edge (text centre 81.2 = head left 81.2, head centre 87.1): every word sits 6 px left of its note. Visible in the user's picture too.
- OK as designed: 6 slots on a beat = dotted quarter; 3 slots on the beat, "e" or "&" = dotted 8th, on the "a" = 16th+8th tied; a 3-slot gap on beat 2 = 8th+16th rests; empty bars = whole rest in 4/4 and 3/4; carry pieces get no text, the hyphen sits between syllables and trails at a system end; one chip per word group, width = group slots x slot width - 3, clipped at the system's last cell (127 px); sample sheet 14 syllables = 14 heads, 0 ties; cells start at the slot-0 head (`nsx + pad` = head left edge 81.2).

## Root causes
- index.html:5 loads `vexflow/4.2.5/vexflow-min.js`, which is 3.0.9; `build_desktop.py` inlines it as is. `buildEventNotes` calls the 4.x-only `VF.Dot.buildAndAttach` (line 1296) inside try/catch, so the TypeError is swallowed on every dotted note; `Stave.formatBegModifiers` (1349) is skipped the same way.
- The linear slot grid (`tc.setX(n.slotStart * swx)`, 1373) puts a 16th piece and its continuation 12 px apart; VexFlow runs the tie from head 1's right edge (`getTieRightX`) to head 2's left edge (`getTieLeftX`), so it has no width. Every syllable of 2+ slots starting on the "a" of a beat hits this (`notePiecesAt` 845: `c % 2 !== 0` limits the first piece to one 16th).
- `renderSystem` draws carry ties only from `noteBySyl` of the same system (1413-1417); `ev.spill` is never used while drawing.
- `buildTimeline` makes a chip only in the bar of the group head (1598-1600).
- `pushRests` (1307-1310) drops `p.dots`; `texts.push({x: ax})` uses `getAbsoluteX()`, the head's left edge (1380, 1399, 1437).

## Overlaps
- Place words / quantizeSpans (timing): with bpm and time left at 100 and 4/4 (issue 3) the sung lengths round to 3-slot values on off-beats, exactly the shape that splits into 16th+8th and needs dots.
- Playhead and chips (playback): a word continuing on the next system has no chip to highlight (finding 6); `hits` exist only for first pieces (1318), so the second head of "my" has no click target.
- Build and the claude.ai artifact use the same cdnjs URL: 3.0.9 everywhere. MusicXML (`barTokens`) is right (dots, ties), so exports disagree with the screen.

## Fixes
1. Load a real 4.x build: cdnjs 4.2.5 only has the legacy files, so use `https://cdn.jsdelivr.net/npm/vexflow@4.2.5/build/cjs/vexflow.js` (allowed CDN; verified: 992,373 bytes, `BUILD.VERSION` "4.2.5", has `Dot.buildAndAttach` and `stavetie` groups) and check `Vex.Flow.BUILD.VERSION` at boot. Until then make dots work on both APIs: `if (VF.Dot && VF.Dot.buildAndAttach) VF.Dot.buildAndAttach([note], {all: true}); else if (note.addDotToAll) note.addDotToAll();` and log the catch once instead of swallowing it. Rebuild the desktop copy after deleting `vendor/`.
2. Ties between heads closer than about 16 px: set `tie.render_options.first_x_shift = -(headW/2 + 1)`, `last_x_shift = headW/2 + 1`, `y_shift = 9` so the arc runs centre to centre (about 14 px wide); or raise the minimum slot width (`barWidthFor` floor 150 -> 290 gives 18 px slots).
3. In `renderSystem`, when `ev.spill` is set and the bar is the last one drawn in this system, draw `new VF.StaveTie({first_note: note})` with no last note (VexFlow ends it at the stave's tie-end x).
4. In `buildTimeline`, also emit a chip for a group whose head lies in an earlier system: anchor it on the first member inside this system, label it with the remaining syllables.
5. `pushRests`: pass `dots: p.dots` and attach the dot as for notes.
6. Centre lyrics on `ax + headW/2` (`note.getGlyphWidth()` in 3.x, `note.getGlyphProps().getWidth()` in 4.x), same for hyphens, extenders and blue texts.

## Confidence
High on 1-4 and 8: measured in the page and the picture reproduced (spacing, flags, beams, rests, tie). High on 5-7 (measured). The Blurry timing itself is inferred from the picture's geometry (3:3:3:1:2 slots), not read from the user's saved sheet.
