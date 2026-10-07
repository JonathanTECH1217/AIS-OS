# Dictation Sheet sweep: analysis of 10 TL;DRs against the 3 user reports

Session assumed: Blurry (Puddle of Mudd, ~76 bpm, 4/4) on the desktop copy, Spotify with the auto-listener, local server stale (old serve.py: `/listen/frames` without `mid`) until 10:30 today. Line numbers are index.html unless a file is named. Re-checked in index.html: beatCurve 2419, gridFromSong 2366-2392, Place words 3060-3106, absorb 3485-3486, toast 1170, normalize 994, storeWrite/localSave 1033/1061, alignLines 2839/2844, dots 1296, applyLength 791.

## The three user reports, explained

### 1. "You could be my someone" (6 syllables) draws 8 heads
The words are right; the extra heads are pieces of the same 6 notes. LRC 47.21 is one 12-syllable line ("..., you could be my scene", next stamp 53.37; server), 11 records, 6 for the phrase, 5 chips = 5 word groups (words). In 384 sweep renders heads always equalled `barTokens` pieces (notation 3), so nothing phantom is drawn. Chain, ranked for his session:
1. The timing came from the blind spread, not the voice. The old server sends no `mid` -> `listen.midOk` false -> `voiceCurve()` 2410 null -> every line falls to `evenSpans` 2983 (voice 7, server 1), which spreads the 12 syllables over 0.85 x 6.16 s = 0.48 s steps, ~3 slots at the sheet's 100 bpm (words: You@1 could@4 be@7 my@10 some@13; that line draws 15 heads for 11 records, ~600 heads for 480 over the song). Report 3 (tempo kept) says the grid was null, so the spread ran at 100 bpm 4/4 (tempo path 1, place 2a).
2. 3-slot notes are the worst shape for this renderer: starting on the "a" of a beat, `notePiecesAt` 845 (`c % 2 !== 0`) cuts 16th+8th (two heads; the tie between them is a 0.44 px hairline, notation 3); crossing the barline, `barEvents` 860 adds a tied carry head; on the beat or "&" it is a dotted 8th whose dot is never drawn because the page runs VexFlow 3.0.9 and `VF.Dot.buildAndAttach` 1296 throws into an empty catch (notation 1-2). You@2x3 could@5x3 be@8x3 my@11x3 some@14x4 one@18x3 reproduces the screenshot head for head, 3:3:3:1:2 spacing, 0 dots (notation 4; the words agent's crafted line gives the same 8: my = 16th+8th, some = 8th + carry).
3. The heard path would not have saved it: with the grid read (76 bpm, slot 0.197 s) step 6 packs 25 of 55 lines into consecutive sixteenths and lands 166/480 syllables a slot or more late (place HIGH); pickups fold to pos 0,1,2 (quantizer 2); syllables under 170 ms are dropped so N<K and the DP names wrong owners on 48 % of those lines (voice 1-2). All put onsets on odd sixteenths, the same tied-heads shape.
Verdict: a display defect (no dots, invisible tie) on top of a placement defect (blind 3-slot spread, squeeze). Fixing the renderer alone still shows "my" as two tied heads; fixing placement alone still shows dotted 8ths as plain 8ths.

### 2. The playhead skips (Spotify)
1. Every Play, seek and loop wrap: `spPlayAt`/`spSeek` set `sp.posAt = now`, `spPoll` 3320 ignores readings for 1500 ms, the first accepted reading is a 1-sample "median" and `reportSong` 3481 `needSnap`s the band: the red line runs ahead, then jumps back 280-460 ms (2.3-3.7 slots, 50-77 px) 1.5-2.1 s after each start, every loop round (playhead 1, deterministic on the real code). Most likely what he sees.
2. `absorb` 3485 returns before `lastAbsorb = nowT` 3486, so after any spell with corr 0 the first correction uses the whole idle time as dt: 49-200 ms moves in one frame instead of 0.64 ms (playhead 2, normal path).
3. Auto-listener `liveLock` every 5 s -> `lockToSong(true)` rebuilds offsetSec/beats/bpm while `followSong`/`highlightSlot` map live song time through the new grid: `slotOfSong(45 s)` 192.00 -> 190.46, 48 s -2.46 slots (server 4). Each re-lock gets a different `listenSongStart` because `listen.pairs` is never cleared (a 30 s pause shifts it 30 s, server 5), `t0` is taken before the skip check (server 6) and loopback frames stop when nothing renders audio (server 2). Needs env > 15 s and pairs (2419): possible on the old server, certain on the new one once the sheet is `lined`, which the blind fill did (3063).
4. Two stale Connect reports -> +-420-450 ms snaps (playhead 3); Stop with a poll in flight leaves `sp.playing` true and the line moving after Stop, ~15-30 % of stops (playhead 4).
5. Not skips but "does not line up": sheet slots up to a bar off the song after a "♪" line or a pickup (quantizer 1-2), the squeeze cascade +0.65..+2.72 s (place); the 17 px hop at each bar line (playhead 6).

### 3. bpm and time signature unchanged after Place words
Only `gridFromSong` changes them, and it returns early on three paths (tempo i1-i5, place 2a/2e/2k), each explained in a 216-409 char toast shown 1800 ms (`toast` 1170), which is why it reads as "nothing happened":
1. Not heard (most likely): `beatCurve()` 2419 needs `listen.env` > 15 s AND `listen.pairs` (pairs need `sp.playing` polls); `gridFromSong` 2362 returns null, words are spread blind at 100 bpm 4/4, `filled` stays null (3105-3106) but `sa.lined` is set (3063). Pressing Place words inside the first 15 s of play, or with the old server's listener not pairing, lands here (tempo h6/h7, voice 7).
2. Kept lock (likely on a second press): `if (songGrid())` 2366 keeps bpm, beats and bar 1 blindly and re-reads only the meter on the OLD beats ("Kept the lock at N bpm"). A lock gets there silently by `liveLock` once the blind fill set `lined` (tempo, server 4), by reload/undo/redo/History (`normalize` 994 keeps `locked` whenever beats exist and `lined` whenever offsetSec > 0: persist 4), or from another song (`forTrack` written at 2339, never compared: place). Nothing checks `lockFit` or who made the lock: a 100-bpm lock stayed on the 76 song and the time flipped to 12/8 with sure 1.00 (tempo HIGH).
3. `tempoOf` = 0 on a low band with one hit a bar (tempo path 2): unlikely on this record.
Side effect of 1: the blind `lined` makes the next heard press skip the downbeat search (2383), and `lockToSong` snaps bar 1 to the beat nearest the stamp-based offset (offsetSec 23.25 = beat 2, place 3), so every bar is a beat off and the toast never says "bar 1 on its downbeat".

## Overlapping findings
- A. Kept lock -> tempo unchanged. persist 4 + overlaps, tempo path 3 + HIGH, place path 2, server 4 (liveLock makes the lock). Root: `songGrid()` truthy means "keep" at 2366, with no author flag, no fit check, no song-key compare.
- B. Auto liveLock -> grid moves -> playhead jumps. server 4 (mechanism), tempo overlaps, server 5/6/2 (pairs, t0, holes feed each re-lock a new start); playhead 7 shows the band is exact on a fixed grid (2.2 ms), so a jump on a locked sheet is the grid moving or the Spotify clock. Root: `lockToSong(true)` swaps offsetSec/beats under `followSong`, no re-anchor, no change threshold.
- C. Squeeze cascade -> late syllables -> odd sixteenths -> tied heads. place HIGH, quantizer 1-2, words (3-slot blind spacing), notation (845 split, 860 carry), voice (any sixteenth count; shifted onsets change which note straddles the barline), tap (off-beat note = tied pieces). Root: one line owns whole bars from a barline; step 6 delays (`ord > startBar` 3091) and packs (`pos = max(c, slot - base)` 3095), and the next line's `want` (3086) drops to 0 so it repeats down the section.
- D. VexFlow 3.0.9 -> no dots -> dotted 8th reads as 8th plus an extra note. notation 1-3, 7 (dotted rests), tap overlaps (no vf-stavetie class), persist (tokens == renderer; XML/MIDI carry the dots and ties the screen lacks). Root: index.html:5 loads cdnjs `vexflow/4.2.5/vexflow-min.js`, which is the legacy 3.0.9; 1296 and 1349 call 4.x APIs inside empty catches.
- E. Blind fill sets lined -> second press skips the downbeat. place 3 (3063 -> 2383 -> nearest beat), persist 4 (normalize re-derives lined; spUseTrack 3200 clears lined but keeps offsetSec), tempo MEDIUM (a hand-lined bar 1 is snapped to the nearest beat anyway, 2332-2338), quantizer 1 (lead bars taken off only when !lined, 3062-3063). Root: one `lined` flag for "chosen by hand", "guessed blind" and "derived from an old offset".
- F. Reason hidden. tempo (322-char toast), place (216-409), voice 4 (evenSpans lines not named), quantizer 1 (toast blames the wrong line), server 3 (silent listenStop). Root: `toast()` 1170 fixed 1800 ms, no status line for Place words.
- G. Stale server chain. server 1 (shortcut cannot replace any server that answers `/version`), voice 7 (no mid -> evenSpans forever), server 8 (zero-padded head offered as voice once mid appears), tempo overlaps (mid ignored by the grid). Root: serve.py `__main__` replaces only `ver == "old"`; the page never compares server and page versions.
- H. Fast syllables lost before the grid. voice 1-2 (under 170 ms: 0-1 onsets, N<K on 58 % of lines), quantizer 6 (collisions only at 76/6 syl/s, a half-tempo read), tempo (76 -> 151 when eighths are loud). Root: `onsetCandidatesIn` 2887-2903 look-ahead swallows the next syllable; the K cut plus `assignVirtual` 2915-2927 has no skip move.
- I. Tied extra (xs) dropped. tap 4 (`+`/`-`/menu call applyLength without xs, 791 `xs || 0`), tap 10 (no MAX_SLOTS clamp), quantizer 5 (setSlotsRaw NaN), persist (normalize clamps). Root: `applyLength` signature vs its 5 callers.
- J. Rest syllables. tap 5 (Place words deletes a word toggled to rest: 3040 filter, 3093 splice), words (old rest record kept on merge). Root: 3092 assumes rest syllables are empty gap markers.
- K. Word across a system break. notation 5-6 (no outgoing tie, no chip on system 2) + playhead (nothing to highlight or click there). Root: renderSystem 1413-1417 ties only within a system; buildTimeline 1598-1600 chips only the head's bar.

## Ranked fix list (most valuable first; groups ship together)
Group I, Place words honesty (report 3, clusters A/E/F):
1. gridFromSong 2366: keep the lock only when `sa.lockedBy === 'user'` (set in lockToSong when !quiet) and `sa.forTrack === songKey()`; else re-read tempo and keep the old lock only if `lockFit.onHit` >= the new fit; never applyTime from a kept lock without that. tempo/place/persist. M, medium risk (Lock semantics; re-run tempo-t45 5a-d/i1-i5, place-test2 e). Closes tempo HIGH, place path 2, persist overlap.
2. Blind fill 3063: do not set `sa.lined` (or `linedBy = 'blind'` so 2383 re-lines unless by hand). place. S, low. Closes place 3, half of quantizer 1.
3. normalize 994: `lined: !!d.audio.lined` (one-time migration when the key is absent), or spUseTrack 3200 zeroes offsetSec. persist. S, low. Closes persist 4.
4. toast 1170: `Math.max(1800, 25 * msg.length)` plus a status-line note ("Tempo kept: song not heard"); name the evenSpans lines (voice 5). S, none. Closes cluster F.
5. Place words when not heard: start the listener itself and say "N s heard, press again after 15 s" (tempo 2). M, low.
Group II, notation (report 1 display half, cluster D):
6. 1296: `if (VF.Dot && VF.Dot.buildAndAttach) VF.Dot.buildAndAttach([note], {all: true}); else if (note.addDotToAll) note.addDotToAll();`, log the catch once; pushRests 1307 pass `dots: p.dots`. S, none. Closes notation 2, 7.
7. Tie width: `tie.render_options.first_x_shift = -(headW/2 + 1)`, `last_x_shift = headW/2 + 1`, `y_shift = 9` (or barWidthFor floor 150 -> 290). S, low. Closes notation 3.
8. Load real 4.2.5 (`cdn.jsdelivr.net/npm/vexflow@4.2.5/build/cjs/vexflow.js`), assert `Vex.Flow.BUILD.VERSION` at boot, delete vendor/ and rebuild. M, medium (API drift; artifact and desktop both). Closes notation 1; makes 6-7 permanent.
Group III, placement (report 1 timing half, cluster C):
9. Step 6 3084-3095: when `ord > startBar` append the line's syllables to the previous line at their true slots (place-stage: 479/480 within a sixteenth, mean 0.00 s, 18 merges); never pack to sixteenths; toast "line plays late" if a squeeze is unavoidable. place/quantizer. M, medium (bar ownership; re-run quantizer-bars 11 scenarios, persist round trip, undo). Closes place HIGH, quantizer 2.
10. quantizer 1: at 3026 drop lines with no letter or digit from `text` (keep them in `lrc`); when the first placed line has `startBar < between`, move bar 1 back by the difference instead of squeezing. S, low.
11. evenSpans 2983: start at stamp+0.15, step <= 0.45 s (last line K x 0.45 s, not 12 s), mark `rec.even`; snap blind onsets to the 8th grid (words). S, low. Halves the tied heads on blind fills.
Group IV, playhead (report 2):
12. absorb 3485: `var dt = ...; this.lastAbsorb = nowT; if (!this.corr) return;` (consider 0.1 s/s). S, none. Closes playhead 2.
13. spPoll 3322: after the await `if (!sp.polling || tSend < sp.seekAt) return;`, stamp pause time into seekAt, reschedule on the pollBusy return 3308. S, low. Closes playhead 4.
14. Start/seek/loop: hold the band at slot0 until the first accepted reading (as the count-in does), end settling when progress_ms is within 300 ms of the request, 500 ms polls until 3 samples. M, low. Closes playhead 1.
15. spOffsetSample 3298: one-sided (max or 80th pct of the last 5), 3 agreeing strays before moving, never rebuild from 2; reportSong 3481 snap only on two agreeing reports except needSnap, else cap corr at +-0.35. S/M, low. Closes playhead 3.
16. liveLock: re-lock only past a threshold, or re-anchor followSong across the swap; clear `listen.pairs` on seek/pause/track change; take `j.t0` after the skip check and reset env/mid/t0/pairs when t0 changes. M, low. Closes cluster B (server 4-6).
17. frame 3559: `Math.abs(mid - center) > 4`; a `scroll` whose scrollTop differs from the frame's own write counts as user scroll. S, none. Closes playhead 5.
Group V, server:
18. serve.py `__main__`: replace when the JSON answer has `app == "Dictation Sheet"` and `version != VERSION`. S, low. Closes server 1; stops cluster G from recurring.
19. Listener: silent WASAPI output stream while capturing, `start()` restarts a running capture, session id = t0 returned by `/listen/start`; page `listenStop` on pagehide. M, medium. Closes server 2-3.
20. fetch_lyrics: 3 tries with 1.5/3 s backoff, retry URLError, `/search` fallback on any 4xx or empty artist, `instrumental`/letterless synced = none; `int(since)` in try -> 400. S, none. Closes server 7, 10.
Group VI, data safety and editing:
21. storeWrite 1033 / persistTabs 1042 return false; localSave 1061 keeps dirty, status "Could not save, storage is full", toast once; on quota drop ds-versions and retry; ids only in ds-tabs. S (return false) / M (rest), low. Closes persist 1.
22. normalize: filter null lines/syllables; boot 4239 try/catch per tab with fallback to ds-store or the sample. S, none. Closes persist 2.
23. `if (tapW.on) tapStop(true)` at the top of undo/redo, guard `line.kind` in tapStop 2717, pause the track before tapStop in player.stop 3453 (try/finally). S, low. Closes tap 2 (uncaught TypeError, track keeps playing).
24. applyLength callers 2060/2061/1711/1713/1714 pass `y.xs`; clamp to MAX_SLOTS inside applyLength. S, none. Closes tap 4, 10.
25. Group drag as one block in finish() 1656-1659; dropAt 1796-1801 shift-then-push order. M/S, low. Closes tap 1, 3.
26. 3093 splice only rest syllables with empty text; drop the `!y.rest` filter at 3040. S, none. Closes tap 5.
Group VII, analysis quality (measure before/after with voice-diag, tempo-t123):
27. onsetCandidatesIn: look-ahead bounded by the next rise, score from the jump, gate 0.25; keep candidates > 0.2 max and add a "skip candidate" move to assignVirtual; windows stamp-0.35..next-0.05; sungEndAfter local floor. voice. L, medium. Closes voice 1-3.
28. tempoOf 2172: score lags by max(a[L-1..L+1]), L/3 guard, prefer the lag nearest 100 on ties; listener `on` = risesOf(env) + risesOf(mid); half-tempo guard when the sung inter-onset median < 1.2 slots (quantizer 6). M, medium. Closes tempo aliasing and half/double.
29. alignLines 2839 Float64Array; parseLrc 2827 strip `<mm:ss.xx>`, accept `[mm:ss:xx]`; syllableTexts glue letterless pieces; vowelSplit -ed/-es rule; splitWord re-split pieces with 2+ vowel groups. words. S each, none. Closes words mediums.
30. wordsToNotes noRender + one render at the end, yield once after "Looking up" (815-1134 ms freeze). place. S, low.
31. barTokens 3904: whole-bar rest = spb (12/8 export). persist. S, none. Closes persist 3.
32. voiceIR nh = round(sr/7000), mirrored in build_desktop.py; bandOf exact 100 fps. voice. S, low-medium (gates were tuned on the old band).

## Contradictions and doubts
- Listener `low`: place says `beatCurve` 2419 passes the full band as `low` (no-low guard never fires, snare 2/4 tie, phaseSure 0); tempo says the listener curve is the low band only (no snare bleed -> tempoOf 0, halving at >= 120). Code: 2419 passes `listen.env` as both the `on` source and `low`. Server 11 and voice 6 say the server's frames go through lowIR (nulls at 800/1000 Hz), so in real use tempo is right and place's synthetic drums fed straight into listen.env are not what the server sends. Settle: read the Listener in build_desktop.py (which filter feeds `frames`) and dump `listen.env` vs `listen.mid` on a tone sweep through the loopback. Either way fix 28 is needed.
- Fast-syllable collisions: quantizer says only 76 bpm at 6 syl/s collides and that is a half-tempo read (keep the 16th grid, no DP); voice says syllables under 170 ms are lost in `onsetCandidatesIn` before any grid; words says the blind 3-slot spacing is what doubles heads. Blurry runs ~4 syl/s = 1.3 slots per syllable at 76 bpm, so rounding is not the driver. Settle: on the real song with the new server, log per line `usedVoice`, N vs K and `rec.q`.
- Which path report 3 took: tempo bets 1 or 3, place lists 1-3, persist points at the reload lock. Settle: read `audio.locked`, `beats.length`, `lockFit`, `lined` and `filled` from the desktop copy's ds-store, and ask which toast text he saw.
- Report 1 slots: notation infers 2,5,8,11,14,18 from the picture, words computes the blind fill as 1,4,7,10,13. Same mechanism, different slots; settle from the saved sheet. Words doubted the "my" tie is drawn; notation's sweep shows ties = pieces-1 always, just 0.44 px wide.
- liveLock vs the Spotify clock as the skip: server shows the grid shift on a synthetic song; playhead shows the Spotify snaps on the real code and measures the locked band exact to 2.2 ms. Compatible, different triggers. Settle: log `lockToSong(true)` calls (offsetSec/bpm delta) during a real play and see whether jumps sit on the 5 s cadence or 1.5-2.1 s after Play.
- All timing numbers (voice, tempo, place, quantizer) come from synthetic envelopes: no audio file on this machine. Voice says real singing is dirtier than its 30/60 ms ramps, so real error is worse, not better.

## Not worth fixing now
- playhead 6, 17 px hop at bar lines: small and regular; cosmetic.
- notation 8, lyrics 6 px left of the head: cosmetic; fold into the VexFlow upgrade.
- persist 5-9 (asText widths, XML tie-first throw, overlap MIDI, Ctrl+S status, raw types): file-only shapes or harmless.
- tap 6-9 (`/` key label, stale join marks, bare setPointerCapture, tap cosmetics): rare, no data loss.
- quantizer 3-5 (dead hy branch, 1-slot rest after a 64-slot hold, NaN masked by lenSlots): no visible effect today.
- tempo LOW (x/8 clamp 300, swing reads 6/8, a.low-null vote): rare meters.
- voice 6 hop drift at 22050 Hz: only if the AudioContext itself runs at 22.05k.
- server 9-10 (two windows, German netstat, taskkill denied): cosmetic or locale.
- place LOW parseLrc drops `[Verse]` headers and refuses a 1-line LRC; words LOW (`lineText` not on `__ds`, `syllableTexts('')`): harmless.
