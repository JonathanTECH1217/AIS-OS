# tap

## Tested
- `mk_tap_stage.py` -> `tap-stage.html` (stage.html + extra hook exports: growNote, cutAt, applyLength, shove, nudgeContact, addBarToSelected, setSel, clearMarks, dropAt, tapPause, tapSlot, selected, noteMenu, setSlots). stage.html == index.html in these regions (CRLF only).
- `tap-smoke.js` (geometry), `tap-test-1.js` (tap pass, tapEndSlots edges, keys, pause), `tap-test-1b.js` (real timer gaps, no voice, fewer bars), `tap-test-1c.js` (rest at landing, 0 past the end, Ctrl+Z mid-pass), `tap-test-2.js` (chip drag, group drag, grip), `tap-test-2b.js` (word integrity, tied extra, ties, nudge), `tap-test-3.js` (keys, menu, bars, marks, applyLength+undo, Place words after rest), `tap-shot2.js/png`.
- Setup: fake file track (`el.currentTime` set by hand, `player.on = true`, `state.audioOn = true`, offset 3.0 s, 100 bpm so slot G = 3.0 + 0.15 G + 0.07), synthetic voice curves; drags via `PointerEvent` (the code listens to pointer, not mouse, events) with `setPointerCapture`/`hasPointerCapture` stubbed per chip.
- Verified OK: tap timing (two taps in one sixteenth -> +1; new line resizes the line before; trims from the voice; 0 on line 2 is line-local; tapStop open vs stopped; pause/resume; Space/0/Enter/Esc/Backspace), all tapEndSlots edge cases, grip (preview clip, 20-slot note drawn tied across the barline, MAX 64 clamp, shrink to 1, Shift fine snap), applyLength push + undo, shove/nudge, +/- bar buttons, setSel/clearMarks, Cut in half on 3 slots, Dotted whole = 24, growNote/+ toasts.

## Findings
1. HIGH. Dragging a multi-note word (hy group) corrupts words. "beau-ti-ful star" (0,4,8,12) dragged to 8 -> `beau@8 star@12 ti@12 ful@16`, group reads "beau+star" (ti stacked on star); dragged to 6 -> `beau@6 ti@10 star@12 ful@16`, chip "beautistar" + "ful" (tap-test-2/2b, tap-shot2.png line 2). Two-note words landing exactly on a note start happen to work.
2. HIGH. Undo during a tap pass. Ctrl+Z is handled before the tap-key block (onKey 1989), `undo()` (1160) swaps in new syllable objects but `tapW` keeps the old ones: later taps move orphans (sheet unchanged, tap-test-1c). Undo past the words: Esc/`player.stop()` throw UNCAUGHT `TypeError ... 'bars'` in `tapStop` (2717 via lineBars 818), tap mode stays on, `player.stop` aborts before `el.pause()` -> track keeps playing with the button on Play.
3. MEDIUM. Drop into the middle of an earlier note stacks a chord. A@0 B@4 C@8 D@12, D dropped at 2 -> `B@4 D@4` (dropAt 1796-1798). Order-dependent: array A,C,B gives `C@4 B@8` (tap-test-2 LOGs).
4. MEDIUM. `+`/`-`/`'` and menu Longer/Shorter/Dotted drop the tied extra (xs). quarter+2 beats (12): `+` -> 8, `'` -> 6, `-` -> 2; whole+4 (20) Shorter -> 8; whole+48 (64) Dotted -> 24; 16th+4 (5) `-` -> "No shorter length" (tap-test-2b).
5. MEDIUM. Place words deletes a word toggled to rest: "Si lent night, ho ly night" with "ho" as rest -> "Si lent night, ly night" (tap-test-3; 3040 filters it out of the alignment, 3093 splices every rest syllable).
6. LOW. `/` key adds one sixteenth (2019) while the menu says "Hold a beat longer (/)" and adds a beat (1715); the `+` toast also says "/ holds the note longer".
7. LOW. Stale join marks after a cross-line drag: mark {li:0, si:2} points past the end once a chip left the line (1657-1658, no remap).
8. LOW. `attachChip` pointerdown calls `chip.setPointerCapture` bare (1637); grip (1685) and note (1813) wrap it in try/catch. A synthetic pointer throws NotFoundError; real pointers fine.
9. LOW. Tap cosmetics: 0 in the same sixteenth as the tap does nothing silently (2737, n<1); a rest syllable on the landing slot is never moved (2690/2806) -> stacked; while paused the outline is wiped by `laneClear` in player.stop (3459) until resume; nudge on a packed line toasts "Already at the start" for a note at slot 8 (1972).
10. LOW (latent). `applyLength` has no MAX_SLOTS clamp (w.+56 = 80 possible); `normalize` (1011) clamps on the next undo/load, and `growNote` then "shortens" it to 64 (1973). Only reachable once xs is kept (finding 4).

## Root causes
- 1: `finish()` 1656-1659 splices the tail out, drops only the head with `dropAt`, re-adds the tail at fixed offsets, then `dropAt`s only the last member; middle members never collide, and the last one's "inside an earlier note" rule shoves it past whatever now sits inside the word.
- 3: `dropAt` checks "same start" (1796) before the "inside an earlier note" shift (1798) moves `pos`; the chain loop (1801) only looks forward from `y`, and stable sort puts the older note first.
- 4: onKey 2060/2061 and noteMenu 1711/1713/1714 call `applyLength(line, y, len, dot)` with no xs; 791 does `y.xs = xs || 0`.
- 2: no `tapStop` in `undo`/`redo`; `tapStop` trusts `s.lines[p.li]`; `player.stop` calls `tapStop` before pausing the track (3453 vs 3455).
- 5: the comment at 3092 assumes rest syllables are empty gap markers.

## Overlaps
- Place words part (5; also `setSlotsRaw` there never pushes). Notation part: `notePiecesAt` (839) draws an off-beat note as tied pieces (my shot: beau@6x4 = two tied eighths), so head count > syllable count is normal notation and a likely reading of the user's report 1. Player/highlight part: `laneClear` in `player.stop` (9). State/undo part (2). Ties are drawn but VexFlow 3.0.9 emits no `vf-stavetie` class (do not test ties by class).

## Fixes
- 1: move a group as one block: compute all member targets, remove all members, run the push rules once with the group's total span (e.g. temporarily give the head `xs = span - lenSlots(head)` for the `dropAt` call, then restore and place the tail at its offsets), never `dropAt` a lone tail member.
- 3: in `dropAt` do the "inside an earlier note" shift first, then the "same start" push, then the chain; break ties at equal pos by array order explicitly.
- 4: pass `y.xs` through (`applyLength(c.line, y, LENS[ni], y.dot, y.xs)` at 2060/2061/1711/1713/1714), let `-` step below '16' when xs > 0, and clamp `lenSlots` to MAX_SLOTS inside `applyLength`.
- 2: `if (tapW.on) tapStop(true)` at the top of `undo`/`redo` (or ignore Ctrl+Z while `tapW.on`); in `tapStop` guard `line && line.kind === 'line'`; in `player.stop` pause the track before/regardless of `tapStop` (try/finally).
- 5: at 3093 only splice rest syllables with empty text; drop the `!y.rest` filter at 3040 (3099 already clears the flag).
- 6: make `/` = `growNote(slotsPerBeat)` and Ctrl+/ a sixteenth (or relabel the menu and the `+` toast). 7: `clearMarks()` after a cross-line move/delete. 8: try/catch like 1685. 9: toast on n<1, push rests in `later`, skip `laneClear` while `tapW.paused`, toast "No room before this note" when idx > 0.

## Confidence
High on 1-5 (deterministic, reproduced through the real UI paths and directly; 1c shows the uncaught trace). Medium on severities. The tap pass ran on a hand-set file clock with `player.on` faked, not a playing track, so the 60 ms reaction offset and real-time drift are untested; Spotify path untested.
