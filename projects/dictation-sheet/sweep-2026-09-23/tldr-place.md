# place (autoPlaceWords flow)

## Tested
- `place-test1.js` (pagecheck, stage.html): real Blurry LRC (60 stamps, 55 with words, 480 syllables), synthetic 76 bpm 4/4 drums (kick 1/3, snare 2/4, hats) + voice band (0.2 s after each stamp, 4 syl/s). Grid, per-syllable error vs sung onset, toasts, state after fill, undo.
- `place-test2.js`: conditions (a) Spotify not heard, (b) then heard via `listen.*`, (b') fresh sheet heard, (c) same song again, (d) undo, (e) already locked, (f) HTML answer, (g) 503 `ok:false`, (h) 1-line LRC, (i) headers/blank/two-stamp lines, (j) typed words replace+merge, (k) attached file before its bands are read.
- `place-test4.js` with `pagecheck-rt.py` (my real-clock variant; the virtual clock stands still during busy JS, so timings there read 0 ms).
- `make_place_stage.py` + `place-test1m.js`: experiment copy `place-stage.html` with step 6 changed (merge instead of squeeze), run on both pages.
- Live server: `/version` 7f8031faa5, `/listen/status` ok (Realtek loopback), `/lyrics` Blurry answers JSON.

## Findings
- HIGH. Placement "does not align" because of step 6 (index.html 3079-3103). Grid was right (bpm 76, 4/4, bar 1 = downbeat 23.11 s, 100% on hit) yet 166/480 syllables land more than a sixteenth (0.197 s) late, max 2.72 s, mean +0.46 s. 25 of 55 lines were "squeezed": a line whose first onset falls in a bar the previous line still uses is pushed to the next barline and packed as consecutive sixteenths (`Can@272x1 you@273x1 ...`), losing its timing. It cascades: chorus 1 drifts +0.65, +0.74, +0.66, +0.88, +0.99, +1.22 s; bridge lines 33-47 drift +0.95 to +2.72 s, until a long gap resets it. Blurry's chorus lines are ~3.0 s apart on a 3.16 s bar and start on beat 4 (pickup), the common case, not an edge case. Blind fills squeeze too (4 of 8 lines in test 2a, 1 of 5 in 2i).
- MEDIUM (Issue 3). Tempo/time only change when a grid is read. Three paths keep them: (1) Spotify with nothing heard (no Listen while playing through the app) -> blind fill, `filled` null, toast "has not been heard yet... Tempo and time signature kept as set" (test 2a, 2k for a file whose bands are not read yet); (2) sheet already locked (auto-lock while playing, or a lock from another song: `forTrack` is written at 2339 and never compared) -> `gridFromSong` 2366-2372 "Kept the lock at 120 bpm" even on a 76 bpm track (test 2e); (3) the time box stays 4/4 legitimately when the song is 4/4. The explanation is in a 216-409 char toast shown 1.8 s (`toast()` 1170), unreadable, so the user sees "nothing changed".
- MEDIUM. A blind fill sets `sa.lined = true` (3063). The recommended second press then skips the downbeat search (`if (!sa.lined ...)` 2383) and `lockToSong` snaps bar 1 to the beat nearest the first LRC stamp: test 2b gives offsetSec 23.25 = beat 2, toast lacks "bar 1 on its downbeat". Every bar is then offset by a beat.
- MEDIUM. UI freeze: after the lyrics arrive the flow is one synchronous block of 815-1134 ms (55 lines): renderAll in `wordsToNotes` 424 ms + final `renderWork` 373 ms (+ `applyTime` 474 ms when the time changes); analysis is small (trackBeats 70, tempoOf 21, lockToSong 83, sungSpansIn 15, alignLines 11 ms). "Looking up" toast cannot even paint.
- LOW. Listener path: `beatCurve` (2419) passes the full-band loudness as `low`, so `meterOf`'s no-low guard (2309) never applies; snare beats 2 and 4 tie, phaseSure 0, the downbeat rests on the phrase-start vote from crowd-sourced stamps (test 2b': bar 1 on beat 2 of my synthetic grid).
- LOW. `parseLrc` drops `[Verse]`-style section text (2827) so no headers reach the sheet; a 1-line LRC is refused as "empty" (`lrc.length < 2`, 3021) while 1 line + a blank stamp passes.
- OK: toasts for stale HTML server, 503 with why, refusal on same song, undo (one step per press: after blind+heard, two undos), `S().lyrics` = joined text, Words panel closed, `$('time')`/`$('bpm')` updated, `player.bars` 81 relaid, no `.playing` chips, no NaN, replace+merge keeps notes on matching lines (2j; my regex check was wrong, "emp ty" is split).

## Root causes
- Sheet model: a line owns whole bars from a barline; two lines cannot share a bar. Step 6 resolves the conflict by delaying the line (`ord > startBar`) and `pos = Math.max(c, e.slot - base)` packs it. The next line's `want` is then 0 or negative, so the squeeze repeats down the section.
- `lined` means "bar 1 chosen" for both hand line-ups and blind fills; `gridFromSong` cannot tell them apart. `songGrid()` present means "keep" regardless of which song made it.
- One fixed 1800 ms toast timer for any message length; all heavy work is synchronous with two full VexFlow renders.

## Overlaps
- meter/lock agents: listener low band = full band; downbeat by phrase starts; auto-lock feeding the "kept" path. words agent: syllable counts matched the splitter on all 55 lines here. listen agent: `listen.env`/`mid` shape and `listenSongStart`. playback: none seen.

## Fixes
- Step 6: when `ord > startBar`, append the line's syllables to the previous line at their true slots (validated in `place-stage.html`: 479/480 within a sixteenth, max 0.23 s, mean 0.00, 18 merges) or add a per-line pickup/start offset; never pack a line as sixteenths.
- Blind fill: do not set `sa.lined` (or set `sa.linedBy = 'blind'` and let `gridFromSong` re-line unless by hand).
- `gridFromSong`: re-read the tempo when `sa.forTrack`/stored key differs from `songKey()`, or when `tempoOf` disagrees with the lock by >3%; say so in the toast.
- Toast: duration scaled by length (e.g. 1.8 s + 40 ms/char) or a persistent status line for the Place words report.
- Freeze: skip the render inside `wordsToNotes` (noRender option) and render once at the end; yield once (rAF/setTimeout 0) after the "Looking up" toast; optionally move `trackBeats`/`tempoOf` to a Worker.
- `beatCurve`: `low: null` on the listener path (or capture a real low band); `parseLrc`: keep bracketed section text as headers, accept one timed line.

## Confidence
High on the squeeze cascade and its fix (reproduced, patched, measured), high on the blind-`lined` and kept-lock mechanics (code + tests). Medium on which Issue-3 path the user actually hit (session not seen) and on the listener downbeat (synthetic stamps unrelated to my drum grid). Numbers from synthetic envelopes; real Blurry audio was not analysed.
