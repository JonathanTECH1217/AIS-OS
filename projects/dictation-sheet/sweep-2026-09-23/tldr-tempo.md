# tempo

## Tested
- `tempo-t123.js` (pagecheck.py on stage.html, PROFILE=prof-tempo): tempoOf, trackBeats+beatFit, meterOf on 64 synthetic tracks (60 s, 100 fps): 8 bpm (60..180) x 8 views (straight, swing, no hats, fill every 8 bars, 2 % drift, listener low-only, half-time, half-time+low-only); plus 3/4, 6/8, 12/8, 2/4, equal kicks +/- starts, bass only, 20 random, waltz+eighths, short/flat. `beatFit` pasted verbatim (not on `__ds`).
- `tempo-t45.js`: gridFromSong end to end (a..g), lockToSong hints/refusals (5a..d), listener path (h1..h7), the REAL Place-words toasts via autoPlaceWords with a faked /lyrics (i1..i5).
- `tempo-t4loop.js`: gridFromSong per bpm x view (40 runs), double/half flip vs hat and bass loudness, random accents at 304 s, a 304 s file.
- `mk_tempo_pure.py` -> `tempo-pure.js` (runjs.py, real clock): timing at 60/304/600 s. Servers: `/listen/status` on 127.0.0.1:8765 answers `ok: true` here.

## Findings
Paths through gridFromSong that leave s.bpm/s.time unchanged, with the toast (all confirmed live, i1..i5):
1. `beatCurve()` null -> returns null -> "The song has not been heard yet: press Play so it plays through once with Listen on, then press Place words again. Tempo and time signature kept as set." (Spotify) / "...wait a moment for the attached track to be read..." (file). Needs >15 s heard AND a clock pair: h6 (14 s) null, h7 (30 s, no pairs) null. Words still placed (evenly, at 100 bpm), `filled` stays null.
2. `tempoOf` = 0 -> "No steady beat found, so the tempo and time signature stay as set." Hit by <15 s of curve, a flat curve, or a low band with one hit per bar (half-time kick only: 0 at 60/70/76, e2/h3).
3. `songGrid()` truthy (kept lock, line 2366) -> "Kept the lock at N bpm[ and T]." bpm/beats/bar 1 never re-read; time re-read on the OLD beats.
4. Before the grid: `s.filled` matches -> "This song is already on the sheet..." (i2); lyric lookup failures.
5. 4/4 -> 4/4 is never visible; the toast says "Tempo 76 bpm and 4/4 read from the song..." (a3).
- HIGH (issue 3, Spotify + desktop): path 1 is the likely one. The auto-listener (`autoListenBefore`, server ok here) only feeds the grid after 15 s of play with pairs; Place words pressed before that keeps 100/4/4 and the only sign is a 322-char toast shown 1800 ms (line 1170). Path 3 is the other candidate: a lock is saved with the sheet (`storeSave`) and `liveLock` makes quiet locks while a lined sheet plays. On a file track the bpm always moves (76 or 152), so "unchanged" cannot come from the file path (40/40 sweep runs set a bpm).
- HIGH: kept-lock path trusts a wrong lock and still applies the meter: a 100-bpm lock on the 76 song was kept (bpm 100, beats untouched) and the time signature flipped 4/4 -> 12/8 with sure 1.00 ("Kept the lock at 100 bpm and 12/8.", b/i3). A right-tempo lock with bar 1 on beat 3 is kept too, no "downbeat" (b2). Nothing checks `lockFit` (41 %) or who made the lock.
- MEDIUM: tempoOf coarse scan aliasing: 180 -> 60 (straight/swing/no-hats/fill), half-time 90 -> 60, waltz 90 + eighths -> 60: the integer lag 100 (= 3 tau or 1.5 tau exactly) beats the true lag that is 0.33 frame off (2 % drift fixes 180 -> 181.87). Downstream: meterOf reads the true beats as thirds -> 6/8 or 12/8 with sure 1.00, applyTime, lockToSong triples -> sheet "180 bpm 6/8", bar 1 off the true downbeat (sweep rows 180 and half-time 90).
- MEDIUM: half/double are decided by layer loudness, and beatFit cannot tell. Low band >= 120 bpm: 128/150/180 -> 64/75/90 (kick 1+3 only, bass only at 120 -> 60). Full band 76: hats 1.4 -> 76, hats 1.8+ -> 151.18 (kick 2.0/snare 2.5); low band 76: bass eighths 1.3 -> 76, 1.6 -> 151.18 (same at 304 s). Half-time 60/70 -> 120/140. beatFit on the 76 track: true beats 100 %/0 ms, eighths 100 %/5 ms, every other beat 100 %/0 ms; a 100-bpm hint still locks at 50 % and moves bar 1 to 20.15 (5c). 9 HALF + 2 DOUBLE + 4 x1/3 of 64 tracks.
- MEDIUM: a hand-lined bar 1 is not "kept": lockToSong snaps it to the nearest tracked beat whatever its place in the bar (20.5 -> 20.74 = beat 2, c), toast silent about it; comment at 2358 says kept.
- LOW: `a.low` null -> phaseSure capped 0.49 and the phrase-start vote cannot rescue it: it only chooses between `phase` and `alt` (the two snare classes on attack), never the kick class (d2: 18 starts on downbeats, phaseSure stays 0.33; bar 1 right only by luck of "beat at or before").
- LOW: x/8: dotted pulse 110 -> 330 -> bpmClamp 300 while the grid runs 316 eighths/min (g2; unlock -> straight 300). Swing 4/4 reads 6/8 at every bpm (never 12/8, r4-r2 < 0.25); 12/8 with medium beat 3 reads 6/8 (r2 0.79). Doubled waltz (70, loud eighths -> 140) reads 3/4 at double tempo, sure 0.52; `half` needs per === 4 so the half path (2377) never fired from tempoOf in any track.
- OK: 4/4 at 60..150 BEAT in every view but low-only (43/64 BEAT); 3/4, 6/8, 2/4 fold, equal-kick vote (>= 6 starts -> 0.50) right; random accents 0/20 sure at 60 s and 304 s (max 0.47), 2/20 phaseSure >= 0.5 at 304 s; bar 1 on the true downbeat 39/40; lockToSong never refuses a downbeat from its own tracking (bd = 0), refuses a 38-bpm hint silently (tracker takes the snares, 0.79 s = the window, 5a), x/8 re-track at 3x found bar 1 on a downbeat (g, 99 %); slotOfSong on the eighth grid 5.92/12.00 for +0.75/+1.5 s. Timing 304 s: tempoOf 53 ms, trackBeats 119 ms, meterOf 4.5 ms, beatFit 21 ms (600 s: 97/212/4/51).

## Root causes
- gridFromSong 2366-2371: `if (songGrid())` keeps tempo, beats and bar 1 blindly; no author flag on the lock, no fit check; meterOf's `sure` measures accent periodicity on whatever beats it is given, not whether the beats are right.
- tempoOf 2172-2175: integer lags in the coarse scan (interpolation only around the winner); `a[L]+.5a[2L]+.25a[3L]` ties L with 3L for a 2-periodic backbeat (both 1.25 A_odd + .5 A_even), so rounding decides; range 60..200 means < 120 cannot halve and <= 100 can double through the 0.75 h-check (2175): the eighth layer's loudness picks.
- beatCurve 2419: the listener's curve is the low band only (kick, bass, snare bleed); no snare bleed -> one hit a bar -> 0.
- Toast 1800 ms (1170); gridFromSong's reason reaches nothing else. lockToSong 2332-2338: offsetSec = nearest beat. meterOf 2312-2316: vote only between phase and alt.

## Overlaps
- words/placing: on path 1 syllables come from evenSpans at 100 bpm (i4 "spread evenly", "1 line waits for the barline"), which feeds the 8-heads-for-6 look. playhead/Spotify: liveLock quiet locks and `listen.pairs` (needs `sp.playing` polls). listen/server: mid band exists (`listen.mid`) but the grid ignores it.

## Fixes
1. Place words: always re-read tempo+meter; keep the old lock only if `sa.lockFit.onHit` >= the new fit (or only when `sa.lockedBy === 'user'`, a flag set in lockToSong when !quiet); never applyTime from a kept lock without that check.
2. Keep the reason visible: toast length ~ `Math.max(1800, 25 * msg.length)` and a status-line note "Tempo kept: song not heard"; Place words could start the listener itself and say so.
3. tempoOf: score each lag with max(a[L-1],a[L],a[L+1]) or interpolated ac at L, 2L, 3L; add an L/3 guard symmetric to the h-check; on a near tie prefer the lag nearest 100 bpm; for the listener use `risesOf(env) + risesOf(mid)` for `on`, keep `env` for `low`.
4. After a lock with a sure meter, move a hand-lined bar 1 to the downbeat of its bar and say "bar 1 moved to X s".
5. Vote over all bar classes (best vs runner-up), and wait up to 2 s for `a.low` before reading the meter. 6. bpmClamp to 360 (or clamp the felt pulse, not the eighths) in x/8.

## Confidence
High on the path list and toasts (real code path, real toasts) and the synthetic tables; medium on which path hit Blurry (no audio file on this machine; the listener server is live here, so path 1 or 3 is the bet; path 2 needs a snare-less low band, unlikely on the record).
