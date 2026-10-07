# Dictation Sheet tests

Headless tests for `../index.html`, written during the 2026-09-23 sweep and the fixes after it. No Node and no git on this machine: Python 3.13 (with `esprima`, `requests`, `PIL`) and headless Edge do the work.

## Tools

- `stage_build.py`: writes `stage.html` next to itself, an offline build of `index.html` (scripts and fonts inlined the way `build_desktop.py` does it). Rebuild it after every edit to the page.
- `jscheck.py <index.html>`: esprima parse of the inline script, with file line numbers.
- `pagecheck.py <page.html> [test.js]`: boots the page in headless Edge with an error trap; `test.js` runs 1.5 s after boot; prints console output, uncaught errors and what the test appends to `#__out`. Env: `BUDGET` (virtual time in ms, default 6000), `PROFILE` (a unique browser profile name per run; parallel runs must differ), `SIZE` (the window, default `1400,900`; `narrow-test.js` wants a narrow one such as `600,700`).
- `pagecheck-rt.py`: the same on the real clock (for timings; the virtual clock stands still during busy JS).
- `runjs.py <script.js>`: a standalone script in headless Edge, real clock (`TIMEOUT` ms); for Web Audio renders.
- `shot.py <page.html> <out.png> [test.js]`: a screenshot after running the test (`SIZE`, `BUDGET`, `PROFILE`).
- `build_place_tests.py`: injects `blurry.lrc.json` into every `place-test*.src.js` to make the runnable `place-test*.js`.
- `mk_tap_stage.py`: `tap-stage.html`, the stage with extra functions on `window.__ds` for the tap tests.

The page exposes `window.__ds` after boot (sheet, timing, notation, audio, tempo, Place words, playback, tap and state helpers); `HARNESS.md` in `../sweep-2026-09-23/` lists them.

## Tests worth re-running after a change

- `place-test9.js`: the whole Place words flow on the real Blurry lyrics with a synthetic 76 bpm track and voice; every syllable against where it was sung, in sheet order (479 of 480 within a sixteenth on 2026-09-23).
- `place-test2.js`: the condition matrix (not heard, heard, same song again, undo, an old lock, HTML answer, 503, one-line LRC, headers, typed words). Some checks assert the pre-fix behaviour.
- `quantizer-bars.js`: bars and pickups on synthetic lines (its A, B2, J and L expectations were stale before the fixes).
- `ph-band.js`: the playhead band on a faked Spotify feed (start, stale readings, loop wrap, stop with a poll in flight, absorb).
- `notation-sweep.js`: 384 renders, heads vs pieces, tie widths, dots. `notation-shot-B.js` with `shot.py` draws the six-syllable line from the user's report.
- `words-t1.js`: the splitter and the blind fill on the real lyrics; heads drawn per record.
- `persist-rt.js`, `persist-undo.js`, `persist-brick.js` then `persist-boot2.js` then `persist-clear.js`: saving, undo, a corrupt store.
- `tap-test-1c.js`, `tap-test-2b.js` on `tap-stage.html`: undo during a tap pass, the tied extra through the keys.
- `tempo-t45.js`: gridFromSong, lockToSong and the Place words toasts.

Example: `set PROFILE=prof-x && set BUDGET=20000 && python pagecheck.py stage.html place-test9.js`

A profile keeps the page's saved preferences (localStorage) between runs, so a test that changes them leaves them for the next test in the same profile: `cursor-test.js` leaves the snap step at a sixteenth, which makes `focus-test.js` fail after it. Give a test its own `PROFILE` when the result matters. Undo swaps the sheet object out: a test that holds `d.S()` in a variable must fetch it again after `d.undo()`.

## The rail and the green line (2026-09-25)

- `rail-test.js`: the tools rail (one symbol per button, names in the tips, a group's fields in a flyout that opens beside the rail from its last icon; Escape, a click elsewhere and a ribbon change close it; the words panel sits after the rail, the handles after both). `rail-shot-edit.js`, `rail-shot-play.js`, `rail-shot-view.js`, `rail-shot-song.js` with `shot.py` draw the sets and the green line.
- `songline-test.js`: the green line (where the song comes in on the sheet): `shiftSong` on a beat grid and off it with every note keeping its song time, the refusal when a note would end up before bar 1, undo, a sheet that starts before the song (bar 1 at a negative song time), the drag of the line to bar 2, an empty line before the notes, the box re-anchoring a beat grid, and Play running the empty bars and starting the song at the line (BUDGET 9000: the last check runs 3.3 s in).
- `pad-test.js`: the note pad (Pad in the top row, or P): eight keys 1 to 8 with syllables and note names (8 the octave above 1), 1 is do in Vocals and the key's tonic elsewhere, rising, the − and + octave buttons, the number keys sounding it (1 to 7 also setting a selected note's degree, 8 sounding only), following the key (C major, A minor la-based, G, Eb), P and ✕ closing it, P in the words box ignored. `rail-shot-pad.js` draws it.
- `park-test.js`: the red line parks half a bar before the selected word (a click on its chip in Move, on its note in Edit, the arrows between words, a word on a later line counting the bars before it, never before the sheet), Play from a selection starts there, a click on a bar afterwards wins, the Add tool keeps its cursor.
- `sound-test.js`: Notes only under Play: one press turns the notes on and the song off (the top-row Notes and Audio agree), a second brings the song back, while the band runs it pauses the song, with no song it just turns the notes on.
- `chips-test.js`: one chip per syllable on the strip (a hyphenated word's syllables chained by their hyphens, `hy` and `cont` classes, own widths and ends), the red line lighting one chip at a time, a tied note staying inside its syllable's chip, a chip dragged on its own in Move (the other syllables stay, undo), a click on a rest putting the red line at its start in Move, Edit and Cut and a note there with Add, a click on an empty spot of a bar. `rail-shot-chips.js` draws two hyphenated lines.
- `downbeat-test.py` with `mksong.py`: which beat is beat 1, read by `align.downbeat_of` on synthetic 4/4 songs (kick, snare, hats, a bass root per bar, a chord every two bars) at three lead-ins: lines on the downbeat, as pickups, on beat 3 (a misleading vote must not win with confidence), no lines, no chords, 120 bpm. Runs without the speech model.

## The fit (2026-09-24)

- `fit-test.js`: Place words with the fit on the page, against a faked local server that answers with `spoken.json`, the real result of `align.py` on `spoken.wav` (the Windows voice reading four Blurry lines from `spoken.txt`).
- `server-fit-test.py spoken.wav spoken.txt`: the running server's `/align/*` endpoints on an uploaded file. `capture-test.py spoken.wav spoken.txt`: the same on a recording of the sound card while the file plays.
- `python ..\align.py spoken.wav spoken.txt out.json`: the fit by hand, printing every word's syllables and times.
- `readsheet.py`: a sheet saved with File, Save as, read against the lyric stamps in `blurry.lrc.json`.
- `mkmix.py` makes `mix.wav`: the spoken lines under loud synthetic drums, hats and bass at 78 bpm, with `mix.stamps.json` (each line's start). `python ..\align.py mix.wav spoken.txt out.json mix.stamps.json` fits it with the singer pulled out; add `--no-separate` to skip that.
- `readfit.py` reads a fit result saved from `/align/result` (`real-result.json`) against the lyric stamps: line starts, scores, the beat grid.
