# server

## Tested
- `server-endpoints.py`: live GET/POST on 8765 (version, status, frames since=0/-5/""/abc/1e3/huge, page routes, 9 lyrics cases, listener start/stop, stop-then-start race). `server-listener-live.py`: same capture with the audio engine kept awake by a looped quiet WAV.
- `server-unit.py`: built serve.py imported as a module; 16 scripted `urlopen` cases for `fetch_lyrics`; `listener_pid()`; `running_version()`; build hash vs built file; the shortcut's decision replayed for a next build. `python -c` netstat simulation (English, German, IPv6, 0.0.0.0, ESTABLISHED, :18765).
- `server-poll-test.js` on `server-stage.html` (stage.html + `serverListenPoll/listenStop/liveLock/...` added to `__ds`) via pagecheck: T1-T11, 36 checks. `server-merger-test.js` via runjs: offline render of the `listenStart` graph.
- Shapes/timings: `/version` {ok,version,app} 2-4 ms; `/listen/status` {ok,why,running,t0,fps,count,err,device}; `/listen/frames` {ok,running,t0,fps,since,frames,mid,err} 14 ms; `/lyrics` ok {ok,synced,plain,duration,track,artist} 210-280 ms, fail {ok:false,why}. `Cache-Control: no-store` on every answer, page included. Blurry: 60 synced lines, `[00:47.21] You could be my someone, you could be my scene`, next line 00:53.37. Running server = build_desktop hash 7f8031faa5, pid 44448 pythonw, shortcut = WindowsApps pythonw.exe "serve.py".

## Findings
1. HIGH The shortcut cannot replace the server after the next rebuild. Replayed: running "7f8031faa5" vs a new VERSION -> "MessageBox: port in use by another program", exit 1. `running_version()` returns the JSON hash; `__main__` only replaces `ver == "old"` (an HTML answer). Every build that has `/version` is "not old", so the stale server (old routes) keeps the port and the user gets a wrong message.
2. HIGH Loopback frames only flow while some app renders audio. Live: start with nothing playing -> 0 frames in 1.5 s, t0 null, `/listen/stop` ignored (running stayed true until a system sound delivered one 40 ms chunk, count 4); with a quiet loop playing -> 152 frames in 1.53 s, stop in 75 ms. The page clock `t0 + i/fps` assumes no holes. Edge's AudioContext masks this while the page is open; close the window while listening and the thread stalls with running=true forever; the next `start()` is a no-op and the new page inherits the stale capture (since=0 -> old t0 + a hole) -> `listenSongStart` and the lock land at the wrong song time.
3. MEDIUM stop-then-start race, live with audio rendering: start right after stop answered running=false, count=56 (old frames kept); the page then sees `!j.running` and `listenStop()`s silently, no toast.
4. MEDIUM `liveLock` every 5 s moves the playhead (Spotify auto-listen): T11 after one re-lock `slotOfSong(45 s)` 192.00 -> 190.46 (-0.38 beat), 48 s -2.46 slots, bpm 120 -> 119.84. `lockToSong(true)` rebuilds offsetSec/beats/bpm; `followSong`/`highlightSlot` map the live song time through the new grid. Fits user report 2.
5. MEDIUM `listen.pairs` is never cleared: T10 a 30 s pause makes `listenSongStart` jump by 30 s once post-pause pairs outnumber the old; same after a seek. `spUseTrack` (l.3200) resets env/mid but not pairs/t0.
6. MEDIUM `serverListenPoll` takes `j.t0` before the skip check (l.2474 vs 2477): T5 a stale in-flight answer after a reset sets t0=1000 while the server is at 3000; T4 a server restart is never noticed (old t0 kept, new frames appended once the server passes the old count). The since/skip itself is right: T2/T2b overlapping polls with the same since give no duplicates; env.length === mid.length held in every step.
7. MEDIUM `/lyrics`: lrclib `/search` answered 503 twice in a row in one run (2413 ms, "HTTP Error 503" returned); only one retry after 1.5 s, and URLError/timeouts are never retried (unit: PASS as coded). `/get` with an empty artist -> 400 "artist_name: cannot be empty", not caught (only 404 falls back) although `/search` works with an empty artist (a pasted link before `spEnsureMeta`). Eruption passes as ok with synced "[00:00.00]".
8. LOW mid padding: T3 an answer without `mid` pads with 0/last and midOk stays false, `voiceCurve()` null (good); T3b once any answer carries mid, midOk flips and the zero-padded head is offered as the voice curve.
9. LOW `launch()` always opens a new Edge `--app` window: a second shortcut click, or a replace (the old window stays open on the old page), gives two windows. No path serves a cached page (no-store confirmed on `/`, `/callback`, static files).
10. LOW `/listen/frames?since=abc` or `1e3` -> unhandled ValueError, connection dropped (live). `listener_pid`: German netstat (ABHÖREN) -> None -> the "another program" box; `[::1]:8765` and `0.0.0.0:8765` match; `taskkill` denied -> 4 s wait -> same wrong box, no window opened. `time` is imported. pythonw shows `MessageBoxW` fine (GUI call, no console needed).
11. LOW Browser capture: ChannelMerger(2) -> ScriptProcessor(1024,2,1) verified (channel0 = input 0 = lp, channel1 = input 1 = conv); voiceIR gain 0.866 @1 kHz, 0.242 @100 Hz as the box-difference theory; conv and mix are in `listen.nodes` and disconnected in `listenStop`, tracks stopped, nothing left connected. But `listen.t0 = e.playbackTime` is 40 ms after the first input sample (measured) with `latency = 0`, and `lowIR()` (l.2138) is unused: `lp` is a 500 Hz biquad, so the 800/1000 Hz clicks are only ~12 dB down, not nulled as on the server.

## Root causes
- serve.py `__main__`: `if ver != "old" or not replace_old_server()`; `running_version()` never maps a foreign hash to "old".
- `Listener.run`: blocking `stream.read` on a WASAPI loopback with no keep-alive render stream; `start()` early-returns while `running`.
- `serverListenPoll`: t0 taken before skip; no session/t0 change detection; pairs only ever pushed (l.2454/2465).
- `liveLock` -> `lockToSong(true)` replaces the grid while `followSong` maps song time through it (no anchor for the band-off preview).
- `fetch_lyrics.get`: retries HTTPError >= 500 once; the outer fallback triggers on 404 only; `instrumental` flag ignored.

## Overlaps
- playback part: finding 4 (grid moves under the playhead); also Spotify's progress_ms lag, which the blip calibration cannot see (it measures loopback vs the page's own output only).
- words part: the LRC line at 47.21 holds two half-lines (12 syllables) with the next timestamp 6.16 s later; the user's 6-syllable line is half of it. Instrumental synced "[00:00.00]".
- lock/meter part: `beatCurve().start` depends on `listenSongStart` (findings 2, 5, 6); `calibrateLatency` picks the biggest rise in a 0.55 s window, so a manual Listen mid-song can lock a wrong latency for the session.

## Fixes
- `__main__`: replace when the JSON answer has `app == "Dictation Sheet"` and `version != VERSION` (or return "old" for it in `running_version`).
- Listener: open a silent WASAPI output stream while capturing (keeps the loopback fed, makes stop reliable); `start()`: if running, set stop_flag, join with a timeout, then start fresh; give each capture a session id (its t0) and return it from `/listen/start`.
- Page: reset env/mid/t0/pairs when `j.t0` differs from `listen.t0`, set t0 only when `skip >= 0`; clear pairs on seek/pause/track change or keep the last 20; `listenStop` on `pagehide`; on `!j.running` after a start, toast and retry once.
- `liveLock`: re-lock only when the new grid differs beyond a threshold, or hold the highlighted slot for the current song time across the swap (re-anchor `followSong`).
- `fetch_lyrics`: 3 tries with 1.5/3 s backoff, retry URLError/timeouts; fall back to `/search` on any 4xx or when artist is empty; treat `instrumental` or letterless synced text as "no timed lyrics".
- `do_GET`: `try/except ValueError` around `int(since)` -> 400. `listener_pid`: read the state column by position, not the word. `launch()`: skip when a Dictation Sheet window is already open (`--app` never dedupes).

## Confidence
High on 1, 2, 3, 6, 7, 10 (live or replayed evidence). Medium-high on 4 (mechanism shown on a synthetic song, not on a real Spotify run). Medium on 5, 8, 9, 11 (static reading plus partial tests; 9 rests on Edge's `--app` behaviour).
