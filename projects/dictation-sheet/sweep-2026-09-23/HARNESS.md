# Dictation Sheet test harness (for the test agents)

Everything lives in this folder (call it SP):
`C:\Users\sumre\AppData\Local\Temp\claude\c--Users-sumre-Documents-GitHub-AIS-OS-projects-dictation-sheet\e53776e8-9cfa-42a9-96ed-0d783532b8cb\scratchpad`

The program under test: `C:\Users\sumre\Documents\GitHub\AIS-OS\projects\dictation-sheet\index.html` (one ~360 KB page, ES5 JS in one IIFE) and `build_desktop.py` (the local server is the `SERVE_SRC` string inside it; the built copy is `C:\Users\sumre\Documents\Applications\Dictation Sheet\serve.py`, running now on http://127.0.0.1:8765/ with `/version`, `/listen/status`, `/listen/frames?since=N`, `/lyrics?track=..&artist=..&duration=..`).

RULES
- Do NOT edit `index.html`, `build_desktop.py`, `stage.html`, or anything outside SP. You test and report. Write your scripts and your TL;DR into SP only.
- If you need a modified page for an experiment, copy `SP\stage.html` to `SP\<yourpart>-stage.html` and edit the copy.
- Use your own browser profile: set the env var `PROFILE` to a unique name (e.g. `prof-<yourpart>`) before every run, otherwise parallel runs collide. Keep runs sequential within your own work.
- No git and no Node on this machine. Python 3.13 works (with `esprima` for JS parsing, `requests`, `PIL`).

TOOLS (run with `python`)
- `SP\stage.html`: an offline build of the current page (fonts, VexFlow, Hyphenator inlined). Do not rebuild it.
- `SP\pagecheck.py <page.html> [extra.js]`: loads the page in headless Edge with an error trap; `extra.js` runs 1.5 s after boot inside the page; it prints console.log/error/warn, uncaught errors, and anything you append to the `#__out` element. Env: `BUDGET` = virtual time budget in ms (default 6000; use 12000-20000 for longer tests), `PROFILE` as above. Async work: write results into `#__out` when done (see `e2e2-test.js` for the `say()` helper that also works before `#__out` exists). OfflineAudioContext renders do NOT finish under the virtual clock: for those use `runjs.py`.
- `SP\runjs.py <script.js>`: runs a standalone JS file in headless Edge (no page); env `TIMEOUT` = ms to wait for async work (real clock). Prints console.log lines and the `#out` element. Use it for pure functions (paste the function source in) and for Web Audio renders.
- `SP\shot.py <page.html> <out.png> [extra.js]`: screenshot after running extra.js; env `SIZE` (e.g. `2600,700`), `BUDGET`, `PROFILE`. Read the PNG with the Read tool to look at the notation.
- `SP\jscheck.py <index.html>`: esprima parse of the page's inline script (only if you make an experimental copy).

THE DEBUG HOOK `window.__ds` (available in the page after boot) exposes, among others:
`S()` the current sheet, `cur()` the current tab (`cur().audio` is the attached-track record: `{el, onset, voice, low, duration, name}`), `sheetAudio()`, `songGrid()`, `state`, `player`, `editor` (`editor.systems[i].chips`, `.geo`, `.bars`), `sp`, `listen`, `tapW`,
words: `parseLyrics`, `syllableTexts`, `splitWord`, `vowelSplit`, `joinVowelless`, `hyphSplit`, `wordsToNotes(text, title, {noUndo, quiet})`, `sortedSyls`, `groupOf`, `groupEnd`,
timing: `lenSlots`, `setSlotsRaw`, `lenFromSlots`, `pieceSlots`, `slotsPerBar`, `slotsPerBeat`, `timeParts`, `barOrdinal`, `lineBars`, `minBars`, `MAX_SLOTS`, `quantizeSpans(spans, nextLineOnsetSec, floorSlot)`, `slotOfSong`, `songOfSlot`, `audioNominalSlotSec`,
notation: `barEvents(line, b, spb)`, `notePiecesAt(c, n, spb, time)`, `restPieces`, `barTokens`, `layoutSystems`, `drawSystems`, `renderAll`, `renderWork`, `asText`, `musicXML`, `midiBytes`,
audio: `risesOf`, `voiceOf(ab)`, `voiceIR`, `voiceCurve()`, `beatCurve()`, `pctl`, `lineLevels`, `sungEndAfter(vc, tOn, tLimit, floor)`, `onsetCandidatesIn(vc, t0, t1, K)`, `assignVirtual`, `sungSpansIn(vc, t0, t1, K, hy)`,
tempo and meter: `tempoOf(on, fps)`, `trackBeats(on, fps, bpm)`, `meterOf(on, low, fps, beats, tau, starts)`, `timeFromMeter`, `gridFromSong(firstOn, starts)`, `lockToSong(quiet, final, noUndo, bpmHint)`, `unlockSong`, `setBpm`, `applyTime`, `bpmText`,
place words: `autoPlaceWords()` (async), `songMeta`, `songKey`, `parseLrc`, `alignLines`, `lrcWindows`, `evenSpans`, `trimAtBar`,
playback: `spOffsetSample`, `spPosition`, `spPoll`, `highlightSlot`, `highlightClear`, `followSong`, `followFrame`, `trackSrc`,
tap words: `tapStart`, `tapHit`, `tapStop`, `tapRest`, `tapEndSlots`,
state: `normalize`, `plain`, `pushUndo`, `undo`, `redo`, `touch`, `listenSongStart`, `tabAudio`.

STUBS that existing tests use (copy from `SP\e2e2-test.js` and `SP\meter-test.js`):
- a fake `/lyrics` answer: replace `window.fetch` for URLs starting with `/lyrics`, returning `{ ok: true, headers: new Headers({'content-type':'application/json'}), json: () => Promise.resolve({ ok: true, synced: lrcText, plain: '', duration, track, artist }) }`.
- a fake attached track: `cur().audio = { el: {paused: true, currentTime: 0, duration, playbackRate: 1, pause(){}, play(){ return Promise.resolve(); }}, url: '', name: 'test.wav', peaks: null, duration, onset: risesOf(fullBandEnvelope), voice: voiceEnvelope, low: lowBandEnvelope, blob: false }`; envelopes are Float32Array at 100 frames a second in log1p(100*RMS) units, floor ~0.4, sung/hit peaks ~2.3.
- a fake Spotify link: `S().spotify = { trackId: 'x', name: 'Title · Artist', durationMs, title, artist, album: '' }`.
- the real lyrics server is running: `fetch('/lyrics?track=Blurry&artist=Puddle%20of%20Mudd&duration=304')` works from the desktop copy only (a file:// page cannot reach it; from Python use `requests.get('http://127.0.0.1:8765/lyrics', params=...)`).

REPORTED BY THE USER (2026-09-23), to be explained:
1. On a real song (Blurry, Puddle of Mudd) the line "You could be my someone" (6 syllables) shows 8 note heads in the notation; screenshot: `C:\Users\sumre\AppData\Local\Temp\claude\c--Users-sumre-Documents-GitHub-AIS-OS-projects-dictation-sheet\e53776e8-9cfa-42a9-96ed-0d783532b8cb\images\1.png` (the chip strip under it shows 5 chips: Y.., c.., b.., m.., someone,).
2. The playhead (red line / chip highlight) sometimes skips while playing (Spotify path, most likely).
3. After Place words, the bpm and time signature did not change.

YOUR TL;DR: write `SP\tldr-<yourpart>.md` with exactly these sections: `# <part>`, `## Tested` (what you ran, script names), `## Findings` (each: severity high/medium/low, what, evidence with numbers or line numbers), `## Root causes` (what in the code explains it), `## Overlaps` (other parts you suspect are involved), `## Fixes` (concrete, no edits made), `## Confidence`. Keep it under 60 lines. Report the same TL;DR back as your final message.
