# playhead

## Tested
All against `stage.html`, PROFILE=prof-playhead, fake `performance.now`, rAF stubbed, frames driven by hand every 16 ms; the real `spPoll` fed through a stubbed `fetch` (progress_ms = true position sampled inside the round trip, rtt U(0,300) with 5-20 % 800 ms spikes, optional stale device reports), OLD fixed-80 ms rule run on the same readings.
- `ph-spclock.js`: Spotify clock alone, 60 s x5 models + 600 s, play at 350 ms start latency, seek at 30 s with 300 ms latency.
- `ph-band.js`: real sheet (24 bars, 96 chips), `player.start()` on faked Spotify; stray readings injected; loop wrap; stop with a poll in flight; absorb gap with the band alone.
- `ph-grid.js`: locked grid (56 beats, 0.5 to 0.6 s with +-10 ms jitter), band alone, loop 4-6, file clock quantised to 250/16 ms, cell gaps.
- `ph-highlight.js`: 4 systems / 40 chips, sweep 0..160 in 0.1 steps, DOM toggle count, followFrame + frame, stop.
- `ph-cost.js` via `realcheck.py` (real clock, load event held by an unroutable image): frame(), drawWave-on-the-second, highlightSlot.
- `ph-scroll.js`: 8 systems in a 420 px #work, system changes, loop wrap upward, scrollbar drag, wheel.
Caveat: the profile's localStorage kept the grid test's locked sheet into two later runs; the final band/scroll runs unlock explicitly.

## Findings
1. HIGH. Every Play, every seek/jump and every loop wrap on Spotify makes the red line run ahead, then jump BACK 280-460 ms about 1.5-2.1 s later (2.3-3.7 slots, 50-77 px at 21 px/slot). ph-band A: snap -456 ms at 2.1 s; E: -281 and -332 ms after each 4 s loop round (wraps at 4.1/8.4/12.8 s, every round). ph-spclock: after a seek the estimate settles under 100 ms only after 1.9-2.1 s (old rule: 8.7-10 s).
2. HIGH. `absorb()` is not rate limited after `corr` has been 0: a 60 ms correction after a normal 1.2 s poll gap moves the line 49 ms in ONE frame, a 200 ms correction after 5.8 s idle moves it 200 ms in one frame (allowed at 4 %/s: 0.64 ms). Seen in the normal path: ph-band A "after 4 s": a 0.40-slot (51 ms, 9 px) one-frame jump.
3. HIGH. Two stale readings in a row (a Spotify Connect device reporting late) move the clock by their staleness and the band snaps twice: ph-band C: -421 ms at 16.9 s then +448 ms at 20.2 s (76 px each). One stale reading is filtered (B: 0 px). ph-spclock M2 (30 % stale up to 1 s): NEW back 726 / fwd 711 ms, 3 jumps >350 ms in 26 s, rms 429 ms; band G: 4 snaps in 23 s. In steady state without staleness the median filter is good: NEW back 43-77 ms, rms 24 ms vs OLD back 554-657 ms, 7-9 jumps >100 ms per minute, 18 jumps >350 ms in 10 min.
4. MEDIUM. Stop while a poll is in flight: the late answer ("is_playing": true) sets `sp.playing` back to true; `trackSrc().playing` is true, `spPosition()` keeps running (+3000 ms after 3 s), `followFrame` relights a chip and the 200 ms strip ticker keeps moving the red line after Stop. Reproduced 3/3 (ph-band F). Probability per stop: rtt/poll interval, roughly 15-30 %.
5. MEDIUM. Auto-scroll only moves down: after a loop wrap two systems up the red line sits 428 px above the viewport for 6.0 s (375 frames). A scrollbar drag (no wheel/touch/key) is pulled back 151 px every frame; a wheel event pauses it 2 s. Forward play: converges in 20-23 frames, no oscillation, 3 frames per system change with the line below the viewport. `scrollTop` truncates (100.4 reads 100): dead zone 4-6.7 px, harmless.
6. LOW. The red line hops 17 px at every bar line inside a system (cell x0 = note start + pad; bar 338 px, normal motion 2.7 px/frame): a small regular tick, not the reported skip.
7. OK. Locked grid: song-time error vs a straight clock max 2.2 ms over 47 beat boundaries, per-frame step 0.53 ms, system changes land on cell x0 (+-1 px), loop wraps land on slot 64 (slotSec one frame late, 0.6 ms), 250 ms-quantised file clock absorbed (1 ms). Highlight: 1600 steps, 0 mismatches, held-over chip lit 40/40, toggles = transitions (79), no double highlight, all dark after stop. Cost: frame() 0.19 ms mean / 0.6 max; with drawWave (800 peaks) 0.95 mean / 2.8 max; highlightSlot ~0; no stutter from CPU.

## Root causes
- 1: `spPlayAt`/`spSeek` set `sp.posAt = now` as if the device moved at once; `spPoll` line 3320 ignores readings for a fixed 1500 ms, the first accepted one (a 1-sample "median") then `needSnap`s the band (3481). The seek in the loop wrap (3543 -> `syncAudio(true)` 3507) repeats this every round.
- 2: `absorb` 3485 returns before `this.lastAbsorb = nowT` (3486), so `dt` spans the whole idle time.
- 3: `spOffsetSample` 3298-3300: two agreeing strays replace the buffer with 2 samples; late/stale progress_ms is one-sided (always too small) but the median treats it as symmetric noise; `reportSong` 3481 snaps on a single report >0.35 s, and the false shift lasts exactly 2 reports.
- 4: `spPoll` 3322 writes `sp.playing` from a response that was requested before `spPause` (3291) and never checks `sp.polling` after the await; nothing polls again to correct it.
- 5: frame() 3559 `if (mid > center + 4)` only; 4221 sets `lastUserScroll` on wheel/touchmove/keydown, never on `scroll`.
- 6: renderSystem 1407 `x0: nsx + pad`, cells are not contiguous.

## Overlaps
Spotify connect/poll (spApi, spToken, backoff) and the strip (drawWave, stripTick, wave drag) share `sp` state; lineUp and lock-to-song write offsetSec/beats the band reads; the loop lane (laneReset) runs on the same wrap. Issue 1 (8 note heads) and 3 (bpm/time after Place words) are not in this part.

## Fixes
- absorb: `var dt = ...; this.lastAbsorb = nowT; if (!this.corr) return;` (or reset lastAbsorb when corr goes 0 -> nonzero). Consider 0.1 s/s instead of 0.04.
- spPoll: after the await, `if (!sp.polling || tSend < sp.seekAt) return;` (stamp pause time into seekAt too). Also reschedule on the `pollBusy` early return (3308).
- spOffsetSample: readings can only be late, so use the max (or 80th percentile) of the last 5 offsets instead of the median, and need 3 agreeing strays before moving the clock; never rebuild the buffer from 2 samples.
- reportSong hysteresis: snap only when two consecutive reports agree (>0.35 s, same sign, within 0.2 s), except the needSnap one; otherwise cap corr at +-0.35 and absorb.
- Start/seek: hold the band at slot0 until the first accepted reading (like the count-in) or set posAt = command response time + ~250 ms; end settling as soon as progress_ms is within 300 ms of the requested spot instead of a fixed 1.5 s; keep 500 ms polls until the buffer has 3 samples.
- Auto-scroll: also scroll up when the line is above center (`Math.abs(mid - center) > 4`), and treat a `scroll` event whose scrollTop differs from the frame's own write as user scroll.
- Bar-line hop: cosmetic; map frac 0 to the previous cell's x1 or leave.

## Confidence
High for 2, 4, 5, 6, 7 and for the start/seek/loop snap (1): reproduced deterministically with the real code paths. Medium for 3 as the user's actual skip: the stale-pair mechanism is proven in code and simulation, but the real Spotify feed was not sampled here; the start/loop snaps and the absorb gap already produce 50-460 ms jumps in the normal path and are the most likely thing he sees.
