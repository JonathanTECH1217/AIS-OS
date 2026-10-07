# Monarc Studio: the short-form video editor

Built 2026-09-29 from 44 grill answers (`brainstorms/2026-09-28-short-form-video-process.md`). Captions colored by
voice added 2026-09-30 from 14 more (`brainstorms/2026-09-30-caption-colors-by-speaker.md`; plan at
`C:\Users\sumre\.claude\plans\what-is-the-desktop-smooth-teapot.md`). Works like Premiere Pro, looks like the Monarc CRM
(Material 3, dark). Takes long recordings (cold-call sessions) and phone clips to finished vertical shorts in
`media/ready/`, which Jonathan's third-party scheduler posts. Every edit is manual; automation is limited to preparing
files (transcript, voice split) and Claude's suggestions (moments, voice labels).

## Open it

- **Desktop shortcut "Monarc Studio"** (white S on blue). It runs `scripts/studio_boot.pyw`: starts the hidden server if
  needed, restarts it when a server file changed (unless it is busy preparing or exporting), and opens its own Edge app
  window at http://127.0.0.1:8780/.
- By hand: `python scripts/studio_server.py` (add `--no-open` to skip the window). Log from the shortcut:
  `~/.monarc/studio-server.log`; started copy: `~/.monarc/studio-server.json`.
- **Desktop shortcut "Monarc Calls"** (white C on red; reworked 2026-10-03): the same boot with `--calls`, which opens
  Airtable's grid on the left two-thirds of the screen and the notes window (`calls.html`) on the right third. Studio's
  top bar has a Calls button that does the same. See "Monarc Calls" below.
- Rebuild both shortcuts and icons: `python scripts/studio_boot.pyw --install`. After a server edit the AIOS runs
  `pythonw scripts/studio_boot.pyw --no-open` (it never restarts the server while a Monarc Calls session is on).
- Install check: `python scripts/studio_check.py` (ffmpeg features, libass picks Montserrat, models, key source, disk,
  port). `--get-models` downloads the speech model; `--time-asr` and `--time-proxy` time 60 s of the newest recording.

## The screen

Top bar (Docs style): mark, short name, File / Edit / Clip / Sequence menus, save status, Undo / Redo, blue Export.
Left: 48 px tool strip (V select, C razor, H hand, Z zoom, B ripple, N rolling, Y slip, U slide, P pen, T type), then
the Media bin (a recording opens to its calls: "Recordings and calls" below). Middle: the 9:16 program monitor (Full,
1/2, 1/4; safe zones). Right: Effect Controls and Captions tabs.
Bottom: the timeline (Captions, V2, V1, A1, A2, "+" for more). Dividers drag and are remembered. `?` lists every
shortcut; they are Premiere's defaults (Space, J/K/L, Ctrl+K, Q/W, Shift+Delete, I/O, Ctrl+D, M, Ctrl+M...).

## Media folders (git-ignored except media/README.md)

| Folder | What |
|---|---|
| `media/inbox/` | recordings; a new file is prepared automatically once its size stops changing (15 s for big files) |
| `media/sfx/` | sound effects, the Sounds bin (click to hear, drag onto A2) |
| `media/assets/` | logos, screenshots, B-roll for overlays. Since 2026-10-03 (Jonathan: "save the logo under media and assets; this is where proof photos should live too"): `brand/` holds the logo set (butterfly, wordmark, white wordmark, SVG) and `proof/` the proof pack (waterfront great room, Georgian exterior and rough-in, the masked rough-in, the five penthouse stills, the penthouse walkthrough). The rough-in shows the PHA shirt logo; use `georgian-rough-in-masked.jpg`. The Assets bin lists subfolders too |
| `media/projects/<id>.json` | one per short; `.versions/<id>/` (a copy every 10 minutes, 100 kept), `.trash/` |
| `media/ready/` | finished exports for the scheduler |
| `media/sessions/` | Monarc Calls session logs, `<YYYY-MM-DD HH-MM-SS>.jsonl`: the words heard, each Status seen, cards, pushes and Airtable writes (original data, not cache) |
| `media/.studio/` | cache, rebuilt if deleted, except Jonathan's fixes and Claude's labels, which live here too: `index.json`, `<asset-id>/` (meta, status, orig.mp4 remux, proxy.mp4, peaks, thumbs, transcript.json, transcript-edits.json, speakers.json, speaker-labels.json, speaker-edits.json, moments.json, moments-log.jsonl, blocks/), `renders/<short>/` export jobs, `exports.json` |

Outside `media/`: Jonathan's voiceprint `~/.monarc/studio-voiceprint.json` (rebuilt from the labels) and the caption
palette `projects/studio/config.json` (tracked).

About 7 GB of cache per 4-hour recording (4.6 GB remux, ~1 GB proxy). Asset ids are a hash of size + first and last
MiB, so renaming or moving a file keeps its cache.

## Preparing a file (automatic)

1. **Remux** MKV to `orig.mp4` (stream copy, +faststart; Edge can't be trusted with MKV). MP4 sources play as they are.
2. **Peaks** for waveforms (int8 min/max at 100 and 10 per second).
3. **Proxy** 540x960 (source shape kept), libx264 ultrafast, exact 30 fps grid (fps filter, the same grid the exporter
   decodes on), a keyframe every 15 frames. Plus thumbnail sheets (72x128, one per 2 s, 10x10 per sheet). About 18 min
   for 4 hours. Quick Sync was tried and dropped on 2026-09-29: it duplicated frames (a 20 s clip came out 37 s long)
   and was no faster.
4. **Transcript** on the laptop, inbox videos only: Silero VAD + NVIDIA Parakeet TDT 0.6B v2 int8 via sherpa-onnx
   (`scripts/studio_transcribe.py`, model in `~/.monarc/models/`). Measured on the 4 h 03 m session: **16.8 minutes,
   14,110 words**, filler words kept. Word times from the model's own token durations. Resumable (`--resume`).

5. **Voices** (inbox videos, after the transcript): `scripts/studio_speakers.py` splits who speaks when, on the laptop:
   sherpa-onnx with pyannote segmentation 3.0 and WeSpeaker ResNet34-LM voiceprints, over ~10-minute windows cut at
   the transcript's longest pauses. Writes `speakers.json` (turns, and per voice group its seconds, pitch and
   voiceprint). About 7x real time: **~35-40 minutes for 4 hours**. A person usually lands in 2 or 3 groups; the labels
   join them. Resumable. Needs the transcript first.

Proxy and transcript run side by side; the voice split follows the transcript. The monitor plays `orig.mp4` until the
proxy exists. "Prepare again" in a file's menu leaves the transcript and the voices alone (they are slow and carry
fixes); a failed stage's Retry reruns just that stage.

Safety rules (2026-10-02, after shorts from the 3-hour recording played silent):
- **"Prepare again" deletes nothing at the click.** The stages wait in `redo.json`, and each old output is removed
  only when its stage starts again. Prep can wait a long time: Monarc Calls holds it while OBS records, and a restart
  drops the queue. The old way deleted `orig.mp4` at the click and lost the rebuild.
- **At start the server checks the outputs**, not only `status.json` (`studio_prep.missing_stages`): a stage marked
  done whose file is gone runs again, as does any waiting redo.
- **The sound never depends on the remux alone.** `studio_prep.orig_path` falls back to the OBS file while
  `orig.mp4` is missing, so sound blocks, loudness and the ring finder keep working. The summary's `copy` reads
  "missing" and the page gets no full-size address meanwhile, so it plays the preview copy.

## Playback (the monitor, `js/media/videopool.js`, 2026-09-30)

- 1/2 and 1/4 play the proxy (a keyframe every 0.5 s). Full plays `orig.mp4`, which keeps OBS's keyframe every 8.3 s,
  so one seek there can take a second.
- While playing, each video follows the audio clock by speed: up to 1.5x when behind, 0.9x or a short wait when ahead.
  It seeks only past 0.5 s behind or 1 s ahead, aimed ahead by what a seek takes in that file, and a seek in flight is
  never started over.
- A video that is seeking shows a copy of its last picture. A clip with no picture yet holds the whole last frame for
  up to 1.5 s. Cuts coming up are pre-seeked 1.5 s ahead (up to 4 s in a slow file). The file stays the same through a
  play; the automatic quality drop switches it at the next pause, and a canvas resize carries the picture over.
- Measured on the 4-hour recording, a 25 s play through 8 hard cuts: no black or frozen frames, 8 seeks (a 12 s play
  made 478 before the fix). The picture runs about 44 ms behind the audio clock, which the speaker delay mostly cancels.

## Voice tracks (2026-09-30, `brainstorms/2026-09-30-voice-tracks.md`)

- **A new short from a moment** starts with A1 "You" and A2 "Them" holding the same audio, plus A3 "Sounds". A1 plays
  only Jonathan's stretches and A2 only the other side's (everyone on their side shares it). The cut sits in the middle
  of the pause between speakers, with 2-frame ramps. The stretches come from the voice labels (`studio_speakers.voice_runs`),
  so a voice fix in the Captions tab moves the split too. The track that isn't playing is shaded on the timeline.
- **Older shorts:** Clip → "Split audio by voice" (one undo step). Anything on A2 moves to a new "Sounds" track first.
- **Normalize voices** (Clip menu, or right-click a voice track): each voice track's speech is measured on the server
  (`POST /api/loudness`, EBU R128 over the stretches it plays) and its clips set so both land at -20 LUFS; the export
  still masters the whole mix to -14 LUFS. One undo step. On the Caitlin clip: Jonathan -21.8 LUFS, Caitlin -30.0.
- Both voice clips stay linked to the video, so moving, trimming or cutting (Ctrl+K cuts both) keeps them in step.
  A sound dropped on a voice track goes on Sounds instead (it would cut a hole in that voice).

## Make trailer (2026-09-30, the Trailer archetype, grill T1-T4 in `brainstorms/2026-09-30-voice-tracks.md`)

Mark the peak with I and O (stop just before the reward), then Clip → Make trailer:
1. Claude drafts three headlines from the peak's words (`POST /api/asset/<id>/headlines`, effort low, about $0.004);
   pick one or type your own. Nothing goes on screen unseen.
2. The peak moves to the front (V1 and both voice tracks, linked to each other). The call reaches back to just before
   its last ring (`GET /api/asset/<id>/ring?t=`: 440 + 480 Hz ringback, searched after the previous call ends; on the
   Caitlin call, 4.9 s before she picks up).
3. The first "Riser" sound in `media/sfx` lands on Sounds at the hard cut.
4. The headline goes on the first free video track above V1. It is black Montserrat Black on a white box, at 84 px in
   the top third (y 480), and stays on through the peak. It fades in over 6 frames and never moves. Long headlines
   wrap into even lines.

One undo step. Text clips can now carry a box (`text.bg`, Effect Controls → Box), drawn the same in preview and export.

## Timeline scrolling (2026-09-30)

A two-finger swipe up or down moves the tracks (over the clips or the track names); a sideways swipe or Shift+wheel
moves through time; a pinch or Ctrl/Alt+wheel zooms at the pointer. A scrollbar on the right shows when the tracks
don't fit, and a "+" in the corner above the track names (always in view) adds a video or audio track.

Pulling a clip's start back with the Select tool past the room before it (the first clip, or one butted against
another) extends it into the earlier recording, like a ripple trim: it keeps its place and everything after moves
right. That is how to reach the dial tone before a moment (`ops.trimEdge`).

Marking a stretch: I at the playhead marks In, O marks Out (the frame at O is not included), Ctrl+Shift+X clears both.
Clicking a word in the Captions tab moves the playhead to it, so the marks land on word edges.

A window that was open while Studio was updated shows "Update ready · Reload" in the top bar (the short saves first).
A short made before the voice tracks splits itself the first time it opens (Ctrl+Z puts the old layout back).

**Volume on the timeline (2026-10-02):** a selected audio clip shows its volume as a yellow line. With the Select tool:
- Drag the line up (louder) or down: 0.2 dB a pixel, Ctrl for 0.05. It catches at 0 dB. The level shows beside the
  pointer, and the waveform grows or shrinks with it.
- Every selected audio clip moves by the same amount, so selecting both voice tracks turns the whole call up or down.
  Alt+click picks one side alone.
- One drag is one undo step. Volume keyframes all move together, so a fade keeps its shape.
- Double-click the line to put that clip back at 0 dB.
- The limits are -60 to +24 dB, the same in Effect Controls. "Normalize voices" can lift a quiet phone line past +12.
- A clip that isn't selected has no handle, so a click on it still selects and moves it.

## Words the transcript missed (2026-09-30, the Caitlin clip)

The voice detector in front of Parakeet can drop a quiet phone-line voice. On the Caitlin clip (moment m17) Parakeet
was rerun straight on the uncovered stretches and then on the whole clip in overlapping windows, no VAD: 70 of her words
were added and 6 misheard ones replaced ("They stay through me to now" was "I appreciate you reaching out"), marked
said by Caitlin, with every saved short's word ids shifted to match. Backups in
`media/.studio/a_40ad52a5455f/backup-*-caitlin-fill*`; `transcript.json` lists each fill under `filled`. A page that
has the recording open refetches the words when `transcriptRev` changes. Only this clip was redone.

## Captions colored by voice (2026-09-30)

- **Palette, one for every short** (`projects/studio/config.json`, Captions tab "Colors · every short", Reset colors):
  Jonathan `#4D80E6` with his spoken word `#FFFFFF`; women `#FF5FA2`; men `#FF3B30`; their spoken word `#FFFFFF`
  (white since 2026-09-30, Jonathan: "It looks better"; it was `#FFD400`).
  Words with no voice yet keep the old look (white, yellow spoken word).
- **Rule:** the other side's color comes from gender, not role; recorded voices (voicemail greetings, phone menus)
  follow the same rule. Captions sit in the same spot for everyone. A caption group breaks where the voice changes.
- **Who is who**, per voice group, first answer wins: Jonathan's fix, then Claude's label, then a local guess. The
  guess needs his saved voiceprint (built from groups Claude or he marked as him, never from guesses; the match
  threshold is set from those labels): a match is him, anyone else is a woman at 165 Hz and up, else a man. With no
  voiceprint yet a voice stays "unknown" (white), so he never shows up red before the labels land. Voiceprint scores
  between two people run close on these calls (0.65 to 0.85), so Claude reading the words is what decides.
- **Claude's labels** ride along with Find moments (below). "Label voices with Claude…" in a recording's menu labels
  them alone and leaves the moments as they are (for a recording whose moments came first, or after a new split).
- **Fixes** (Captions tab), saved on the recording so every short from that call follows (`speaker-edits.json`; on a
  short with generated captions a word's "Said by" is saved on that short instead, see Generate captions):
  - "Voices in this short": each voice's row menu has This is me, Woman, Man, Same person as, Reset to automatic.
    "You" has no menu: his voice can come in parts, fixed from its words.
  - The words, in their voice's color: click jumps, Shift+click selects a run, right-click has "Said by" (You, a voice,
    New voice woman/man, Reset to automatic) for the selected words, and "This whole voice is" for the word's whole
    group from the split.
  - The last action on a voice wins (labeling it detaches it from "same person as"; joining drops its own label).
    Fixes are not in a short's undo list, like spelling fixes; each can be set back from the same menu.
- **The export** looks each word's voice up again from the recording's current labels, so "Export all" colors right
  even for shorts not opened since a fix; if any word moved, the job notes "open the short once to regroup its
  captions" (the bin shows "Exported with a note"). An export job freezes the palette into its `project.json`.
- **A new split** (only if the voices are split again) sets Claude's labels and whole-voice fixes aside as
  `*.stale-<rev>.json`; word fixes to "you" or a new voice are kept.

## Generate captions (2026-10-02, `brainstorms/2026-10-02-captions-after-trim.md`)

Jonathan: "Captions should only be generated after I trim a video to its best parts. So the transcript is the only
thing that is weighed for contextual accuracy." (grill G1-G7)
- **A new short has no captions** while he trims it (`captions.mode = "generate"`). The Captions tab says "No captions
  yet" with **Generate captions**; the same button sits in the Captions row's head on the timeline (the sparkle) and in
  the Clip menu. The razor and trims still snap to the transcript's words.
- **Generate** (`scripts/studio_gencaps.py`, about 1 to 2 cents a short):
  1. The parts the speech clips keep (A1 and the voice tracks; parts under 4 s apart count as one) are heard again with
     2 s either side (`scripts/studio_listen.py`, a child process, one at a time): Parakeet on 20 s windows every
     15 s, no voice detector, so it hears whole sentences.
  2. The two listens are lined up word by word. Where they agree, the second listen's words go in. Where they differ,
     Claude (`claude-opus-5`, effort low) reads the short's words with each difference marked and picks A or B; it
     never writes words of its own. Without Claude (no key, no network) the second listen wins. A word he fixed by
     hand always stays, and so does the rest of that spot.
  3. Each word keeps a way to its voice: the first-transcript word it overlaps (so it follows every voice fix), or for
     a word only the second listen heard, the voice split's group at that time.
- **Saved in the short** (`captions.gen[asset]`: words `[start, end, text, donor id, group, fix]` in the recording's
  seconds; the stretches it covers, 1 s past each kept part; the transcript's rev; when; the cost). One undo step.
  Later cuts and moves keep the captions right. Footage pulled past what was generated has none: the tab says "Some
  footage was added after the captions were made" with Generate again, and the sparkle comes back on the timeline.
- **Fixes after Generate are saved on the short:** double-click a word for its spelling, right-click "Said by" for who
  said it. "This whole voice is" still fixes the whole voice on the recording.
- **Export** asks first when the short has none, or part of its footage has none: "Generate captions first?" with
  Generate and export / Export without captions. Export all queues every done short and names those that go out
  without captions.
- **Older shorts** (made before 2026-10-02) keep their captions from the transcript, with a note and Generate captions
  to replace them. The calls view's player keeps its rough captions from the transcript (G6).
- **Measured** on call c23 of the Sep 30 recording, best bit m13 (75 s): 216 words became 230, Claude read 11 spots,
  25 to 33 s, 1 to 1.9 cents. It filled the far side's "No, I do not, I do not have 15 minutes. All you gotta do is",
  and "And just set the line." became "Except what?". On a 22 s short: 11 s, half a cent.
- **Numbers:** Parakeet hands back a number's first token without its word-start mark, so "get 15" came out "get15"
  (59 times in the first two recordings). Since 2026-10-02 the transcriber splits them, except after a single letter
  ("C3") or "Control" (Control4); old transcripts are split the same way before the two listens are lined up.
- Each run is logged in `moments-log.jsonl` (`kind: "captions"`) with its cost.

## Recordings and calls (2026-10-01, `brainstorms/2026-10-01-clip-browser.md`)

A recording's clips are its calls, ring to hang-up. Clicking a recording turns the Media panel into its calls (a back
arrow returns). While one is open the panel runs full height beside the timeline and widens (`binBrowse`, default 800,
capped so the viewer keeps 260 px): the player on the left, the calls on the right.
- **The Recordings list:** each recording is titled by the date it was recorded ("Wed Sep 30, 10:27 AM"), newest first.
  The date comes from the name OBS gives the file; a name without one falls back to the file's modified time less its
  length (`studio_calls.recorded_at`; the summary's `recorded`, `recordedFrom`). The newest recording stays in view and
  the earlier ones fold under "Previous recordings", closed until opened (remembered). Files keep their names on disk.
- **Rows:** a dot until watched (3 s of play), the time in the recording, the title, the length, how it ended as a tag,
  and "Short" once a short covers most of it (worked out from the shorts list). Stretches Claude marked "not a call"
  are hidden behind "Show N hidden", except a stretch that holds a best bit: it shows as "Between calls" and plays
  from 2 s before its first bit. Tags filter by outcome; the search box matches titles and what was said (on the
  server; a click then plays from just before the first match).
- **Player:** one `<video>` on the preview copy, a keyframe every 0.5 s. A click plays from the ring; it stops at the
  hang-up (`requestVideoFrameCallback`). Speed 1x, 1.5x, 2x (remembered). The bar shows Claude's best bits as diamonds
  (a click marks the bit), I and O mark a part, Make short opens a short of the marked part or the whole call (named
  after the call, or the bit when the marks match it exactly; that bit is marked kept). Captions are drawn on the
  picture with the same colors as a short. Rows drag onto the timeline.
- **Keys** while the calls view has focus: Space, Up/Down (previous/next call shown), I, O. Every other key still acts
  on the open short.
- **Memory:** the page holds the titles (about 20 KB for 4 hours), one player and the playing call's words. Switching
  calls only moves the player inside the same file; stepping through 20 calls on the 4-hour session kept the browser at
  758 to 785 MB. Leaving empties the player.
- **Where a call plays** (`scripts/studio_calls.py`): from its ring (`studio_prep.find_ring`, found on the laptop, free;
  10 of 20 calls on the 4-hour session), else 1 s before the first word; to 1.5 s after the last word. Margins never cut
  a call (calls overlap: c20 runs into the Caitlin call) and never reach into the call before or past the next one.
  Kept in `calls.json`, rebuilt when `moments.json` changes; best bits belong to calls by time, not Claude's call field.
  Watched marks: `call-marks.json`, by time range, so they follow a rerun.
- **Disk:** a note under 15 GB free. A recording's menu: "Remove full-size copy" frees `orig.mp4` (`meta.orig =
  "removed"`; exports, sound blocks, loudness and the ring finder read the OBS file; the page plays the preview copy,
  even at Full), "Restore full-size copy" makes it again.

## Find calls (Claude's pass)

`scripts/studio_moments.py`: one `claude-opus-5` call over the transcript (numbered lines; Claude answers with line
numbers only, so times can't be made up). Returns the calls (label, outcome, summary) and the best bits ("moments")
tagged objection, booking, funny/awkward, best line, each the whole exchange with a reason and a strength 1 to 5.
Call labels (2026-10-01) are the first name and company when said ("Sean, C3 Electrical"), else who answered; the
outcome stays its own tag. The button counts tokens (free) and shows the cost before spending. First run: 42,567
tokens, **$0.355**, 62 s, 32 calls, 31 moments. Only transcript text is sent. Details: `references/anthropic-api.md`
(Studio section). Key: `ANTHROPIC_API_KEY`.

**By itself (B16):** when a new inbox recording finishes preparing (voices split), the server counts tokens and runs
the pass if the top of the estimate is under `autoFindMax` in `projects/studio/config.json` (3.00). The estimate's
top is $2.75 plus input at $5 per million, so the line falls at 50,000 input tokens: a 3-hour recording (about 40,000)
runs, the 4-hour session (about 59,000) waits for a click and its row says why. Decided once per recording
(`auto-find.json`, written after a good count), logged in `moments-log.jsonl`; checked at server start too; never
with `STUDIO_MEDIA` or `STUDIO_NO_CLAUDE` set.

Once the voices are split, the lines carry inline voice tags (`412|01:12:34|[S2] yeah we handle it [S1] okay…`, same
numbering) with a table of tags on top (seconds, pitch, voiceprint match), and the same call also returns which tags
are Jonathan and each other voice's gender, first name, role and "same person as". The button waits for the voice
split. The labels are the costly part: the labels-only run on the 4 h 03 m session (426 voice groups) cost **$1.72**
(58,416 tokens in, 57,068 out, nearly all thinking, 11 minutes), over its first estimate of $0.54 to $1.04; the
estimate now assumes 40,000 to 70,000 output tokens for the labels. Labels only: `python scripts/studio_moments.py
<asset> --speakers-only [--estimate]`, or "Label voices with Claude…" in the recording's menu.

Shorts come from the calls view's Make short (above). The old moments list under each recording went on 2026-10-01;
`POST /api/projects {asset, moment}` still makes a short from a best bit by id.

## Monarc Calls: Airtable beside live key notes (2026-10-03, `brainstorms/2026-10-01-live-call-notes.md`, Q32-Q45)

The first build (2026-10-01) drove OBS and split recordings by his clicks; on 2026-10-02 Jonathan scrapped the whole
recording part. Now: two windows side by side, his real Airtable grid (Grid view of Prospects, Contacts) on the left
two-thirds, where he types Status as always, and the notes window on the right third. Nothing is recorded.

- **Listening:** Start opens the mic child (`scripts/calls_mic.py`): whatever microphone Windows has as its default
  input (WASAPI via pyaudiowpatch; the C920 webcam mic), mono, 16 kHz (soxr), Silero VAD into stretches of speech,
  Parakeet words with wall-clock times, a stretch a second or two after it ends. The audio is dropped once its words
  are out. Pause (button, or F9 anywhere: a Windows-wide hotkey, `RegisterHotKey`) stops listening; nothing is kept
  while paused. A dot pulses while it hears speech. No mic plugged in: the check line says so in plain words.
  `python scripts/calls_mic.py --check` prints the device and 10 s of words.
- **Key notes** (`scripts/calls_notes.py`): plain rules, no model, the same words always give the same notes. Kinds:
  offering, constraint, objection (phrase lists in `references/call-note-phrases.md`, his to edit; a service or brand
  word counts as an offering only in a sentence with we / our / us; a sentence holding an "Ignore" phrase, his pitch
  like "you guys" or "landing page", never makes one of these), email (written, or spoken and put together, checked
  against the row's website; a doubt is flagged), name ("this is ...", "what was your name?" and the answer, "Hey
  Chase,", spelled out), phone (ten digits, spoken or written), meeting (the last day and time said in a call with a
  yes and a meeting word, not one that ends in a call back). Shown live under "This call", the phrase in bold.
- **The cut** (`scripts/studio_session.py`): every 5 s while listening it asks the Prospects base which rows' "Status
  changed" is newer than the last one seen (one call). An edit is acted on once it has sat 3 s (so a half-typed word
  isn't read). Typing Status ends the call: the stretches heard since the last cut, by their start, belong to that
  row, cut at Airtable's own timestamp. No cut for a blank Status, the words the CRM reads as judged-never-dialed
  (wrong vertical, unqualified, bad fit, commercial, no website, zip code), or a row already cut this session (a fix;
  its card shows the new words). Each cut queues the dial's Outreach Log row.
- **Cards:** a call with key notes becomes a card under "To file" (company, MB ID, his Status words, time). Each note is
  an editable line with its kind; email, name, phone and meeting notes are edited as the value, the line heard under
  it; X takes one out, "+ Add" adds one. Edits are kept in the page (and localStorage) until he pushes. Push writes the
  doc, fills the row's Email and Owner when blank (the first kept email and name), and puts the kept notes in the log
  row's Transcript. Discard files nothing. A call with no key notes files its words at once, no card; no speech at
  all, nothing filed. Cards wait across Stop and a restart (the last 3 days).
- **The doc:** `projects/prospects/<MB-ID> <Company>/<YYYY-MM-DD HH-MM> call.md`: company, MB ID, date, his Status words,
  the Airtable record ID and session; "## Key notes" (his kept lines); "## Words heard" (every stretch with its time).
- **The two windows** (`studio_common.open_side_by_side`): Edge app windows found by title ("Airtable", "Monarc
  Calls"; ordinary browser windows are never touched), placed on the work area at 2/3 and 1/3 with `SetWindowPos`; a
  window already open is reused. Airtable uses his default Edge profile.
- **The Prospects base** (`scripts/studio_prospects.py`): schema read at the start panel and at Start, every read and
  write by field id after that; a missing column ("Status changed" included) stops Start, named. Writes in order on a
  thread: retried after 2, 5, 15, 30, then every 60 s on a network error, 429 or 5xx; any other refusal is "stuck" and
  shown in the footer. A log note waits for its log row. `python scripts/studio_prospects.py --check` lists the
  columns and the last few Status changes (reads only).
- **The session file:** `media/sessions/<start>.jsonl`, flushed before anything goes over the network. Every click
  carries an id (a resend counts once); the page keeps clicks in localStorage while the server can't be reached. After
  a restart: an open session is closed (press Start), writes Airtable never confirmed go again (older than a day:
  stuck), open cards come back. While listening, Studio holds off preparing files, and `health().busy` keeps the boot
  script from restarting the server.
- **Stand-ins for tests:** `STUDIO_FAKE_MIC=1` (the mic child plays lines sent by `POST /api/session/fake {say}`),
  `STUDIO_FAKE_AIRTABLE=<json>` (`tests/fixtures/prospects.json`; `{status: {rec, words}}` plays him typing Status;
  `GET /api/session/fake` shows the base), `STUDIO_PHRASES` (`tests/fixtures/call-note-phrases.md`),
  `STUDIO_POLL_SECONDS` / `STUDIO_SETTLE_SECONDS`, `STUDIO_PROSPECTS`. F9 is never registered under the stand-ins.

## The short (project file)

Every time is a whole frame at 30 fps. Clips: `start` on the timeline, `in` / `out` on the source's own frames
(text, shape, image: in = 0). Keyframes (`fx.<prop>.k`: `{t, v, e}`) sit on source frames, so trims and slips carry
them. Props: posX, posY (pixels, clip center on 1080x1920), scale, opacity (percent), rot (degrees clockwise), volume
(dB). Easing: linear, in, out, both, hold; one formula in `js/model/keyframes.js` and `studio_render.py`, checked by
`tests/vectors.json`. Captions are built from the words under the speech clips (2 to 4 word groups, each word with its
center x), so they follow every cut: the short's own generated words (`captions.gen`, Generate captions above), or for
a short made before 2026-10-02 the transcript's, where a word fix is saved on the recording's transcript
(`transcript-edits.json`) so every short from that recording gets it.

## Export (Ctrl+M, or Export all for shorts marked Done)

`scripts/studio_render.py`, run from a queue in the server, one job at a time. A Python compositor (Pillow + numpy)
builds each frame with the page's rules; ffmpeg decodes sources on the 30 fps grid, burns captions with libass
(`studio_captions.py` writes the ASS: one event per word, the lit word changes color and pops 108 % over 110 ms), mixes
audio (volume keyframes as expressions, fades, sound effects), evens loudness to -14 LUFS (measured gain, peak limiter at
-1.5 dBFS, one correction pass; loudnorm's own second pass landed about 1 LU low on call audio), and encodes 1080x1920
30 fps H.264 High + AAC 48 kHz, +faststart. A short over 90 s gets a warning, never a block. Measured: a 58 s short with
no zoom renders in about 65 s; zooms and moves take the crop-and-resize path; a rotation all the way through runs about
5 fps.

## Tests (G39: every tool passes a checklist)

- `python projects/studio/tests/run.py [names]`: 38 headless Edge tests (Playwright) against a seeded media copy on port
  8781, screenshots in `projects/studio/tests/shots/`. Fixtures: `tests/fixtures/make.py` (a 20 s clip whose top band
  carries the frame number as a barcode, so tests read which frame the monitor shows; four stretches: a gatekeeper
  call, a booking, one hidden, one between calls; `listen-fake.json`, what the second listen "hears" under
  `STUDIO_FAKE_LISTEN`). `t-browse.js` runs at 1536x780, Jonathan's screen (1920x1080 at 125 %). Shorts made by
  `t.fresh()` take their captions from the transcript; `t-gencaptions.js` covers Generate captions.
- `python projects/studio/tests/gencaps-unit.py`: Generate captions without the model or Claude: stretches heard and
  kept, the two listens lined up, his fixes pinned, picks applied, voices, what an export counts as missing, numbers
  split, and one whole run through the child process.
- `python projects/studio/tests/calls-unit.py`: call bounds with the real overlaps and a made-up ringback, best bits by
  time, between-calls rows, watched marks, search, the words slice, the auto-run rule (nothing can spend).
- `python projects/studio/tests/prep-unit.py`: the remux fallback, the start-up check for missing outputs, and "Prepare
  again" removing an old output only when its stage runs (stand-in stages, nothing encoded).
- `python projects/studio/tests/session-unit.py` (Monarc Calls): the key-note rules (phrases, the we-cue, his pitch
  ignored, spoken and written emails and phones, names, meetings), the poll formula and times, the writer (log row,
  log note after it, blank-only, retry), a whole session against the stand-ins (live notes, the cut, skip words, fixes,
  no-notes and no-speech calls, Pause, F9's toggle, Push, Discard, Stop), and what a restart brings back.
  `t-calls.js` and `t-calls-layout.js` run the notes window at 510 x 780, last in `run.py`.
- `python projects/studio/tests/render-unit.py` (easing vectors, volume expressions, ASS with the voice colors,
  transforms, tokens to words, moment lines to times), `server-unit.py` (Range 206/416, path guard, uploads, 409 on a
  stale save, versions, voices, the palette), `speakers-unit.py` (pitch incl. phone-band audio, windows, words to
  turns, who wins, fixes, the voiceprint, the tagged Claude request; no network, no models), `render-smoke.py` (every
  feature exported, then format, constant 30 fps, faststart, loudness, still vs export frame). The runners set
  `STUDIO_MEDIA`, `STUDIO_CONFIG` and `STUDIO_VOICEPRINT` to throwaway copies; the seed is rebuilt when
  `fixtures/make.py`'s `SEED_VERSION` changes. The seed has three voices (Jonathan in two groups, "Dana", an "Owner").
- `t-parity.js`: the monitor's canvas vs the exporter's still of the same frame. Things sit within 2 px; brightness
  PSNR >= 32 dB without a title, >= 27 with one, >= 24 in the caption band (letter edges anti-alias differently in
  the browser, Pillow and libass; identical by eye).
- `python projects/studio/tests/make_vectors.py` rewrites `vectors.json` from the exporter.

## Server routes (127.0.0.1:8780)

`/` page files; `/media/<rel>` with HTTP Range; `/api/health`; `/api/bin?since=REV` (25 s long poll: media tree, prep
progress, shorts, moments jobs, export queue); `PUT /api/upload?dir=&name=`; `POST /api/import {path}`;
`/api/asset/<id>` (+ `/transcript` GET (with `voices`)/PATCH, `/voices` GET, `/speakers` PATCH (fixes: `groups`,
`merge`, `words`, `new_voice`), `/voices/estimate` POST, `/voices` POST (labels only), `/moments` GET,
`/moments/estimate` POST, `/moments` POST (both 409 while the voices split), `/moments/<mid>` PATCH, `/reprep` POST,
`/calls` GET (the calls view's rows, best bits, hidden count), `/calls/search?q=` GET, `/calls/<cid>` PATCH
`{watched: true}`, `/words?s=&e=` GET (one stretch's words and voices), `/orig` POST `{keep: false|true}` (remove or
restore the full-size copy), `/captions` POST `{ranges: [[s, e]]}` (Generate captions: starts a job; 409 without a
transcript));
`/api/captions/<job>` GET (the job: `state`, `msg`, `progress`, and `result` when done, which the page puts in the
short);
`/api/config` GET/PUT (`captionColors`, or `reset`); `POST /api/loudness {asset, ranges}` (Normalize voices);
`/api/asset/<id>/ring?t=` GET and `/api/asset/<id>/headlines` POST (Make trailer; `STUDIO_NO_CLAUDE` turns the
headline call off, as the test runner does);
`/api/audio_block?asset&i&sr` (30 s WAV blocks); `/api/projects` (GET list,
POST create), `/api/projects/<id>` (GET, PUT with baseRev, DELETE to trash), `/versions`, `/versions/<ts>`, `/restore`,
`/still?f=`; `POST /api/projects` also takes `{asset, call, bit, start, end, name}` (Make short; a bare asset is 400);
`/api/export`, `/api/export/all`, `/api/exports`, `/api/export/cancel`. The bin feed carries `diskFreeGb` and
`session {active, listening, calls}`; each recording's summary carries `calls {n, booked}`, `callsRev`, `copy` and
`auto`.
Monarc Calls: `/calls.html`; `/api/session?since=REV` (25 s long poll on its own feed: listening, live notes, cards,
filed, writes); `/api/session/check` (the mic, the phrase file, the base, in plain words; opens nothing);
`POST /api/session/<action>` with `{cid, at, ...}`: `start`, `pause`, `resume`, `toggle` (F9), `push {sid, n, notes}`,
`discard {sid, n}`, `stop`, `retry`, `window` (opens both windows); tests only: `GET/POST /api/session/fake`.

## Licenses and credits

Parakeet TDT 0.6B v2 (NVIDIA, CC-BY-4.0: credit NVIDIA), Silero VAD (MIT), pyannote segmentation 3.0 (MIT), WeSpeaker
ResNet34-LM speaker model trained on VoxCeleb (CC-BY-4.0, following its dataset: credit WeSpeaker and VoxCeleb;
checked 2026-09-30), sherpa-onnx (Apache-2.0), ffmpeg 7.1 from
imageio-ffmpeg (GPL), Montserrat (SIL OFL 1.1, `projects/studio/fonts/Montserrat-OFL.txt`), Google Sans / Google Sans
Text (OFL), Material Symbols (Apache-2.0), Pillow, numpy, Playwright (tests). No code copied from OpenShorts; its
approach (word-edge cuts, per-word caption events, crop-based zooms) informed the design.

## Troubleshooting

- **Window opens but says it can't reach the server:** check `~/.monarc/studio-server.log`; run
  `python scripts/studio_check.py`.
- **Shorts from one recording play silent:** look for `audio_block … 500` in the log and a missing
  `media/.studio/<asset>/orig.mp4`. Since 2026-10-02 the sound falls back to the OBS file and a restart rebuilds the copy
  (`pythonw scripts/studio_boot.pyw --no-open` when the server isn't busy).
- **A file sits at "Preview copy 0 %":** the prep queue works one file at a time; a 4-hour recording takes about 35
  minutes, then about 35-40 more for "Voices". "Prepare again" in the file's menu reruns the failed quick stages; a
  failed transcript or voice split has its own Retry.
- **A new short has no captions:** that's on purpose until Generate captions (above). If Generate fails, the Captions tab
  shows the reason under the button; a missing key or no network still gives captions (the second listen's words).
- **Captions are all white:** the recording's voices aren't split or labeled yet (the Captions tab's "Voices in this
  short" says which), or it isn't an inbox recording (only those get the split).
- **A voice has the wrong color:** fix it in the Captions tab (voice row menu, or right-click a word); the fix covers
  every short from that recording.
- **Find moments failed:** hover the red line for the reason (no key, no transcript yet, network). Nothing was spent if
  the estimate step failed.
- **Export failed:** hover "Export failed" in the bin; the job folder `media/.studio/renders/<short>/<job>/` holds the
  frozen project and captions.ass. Rerun by hand:
  `python scripts/studio_render.py <job>/project.json --out media/ready/x.mp4 --job <job>`.
- **Leftover ffmpeg after a crash:** each Studio process lists its children in `~/.monarc/studio-jobs/<pid>.json`; a
  restarted server stops the children of processes that died.
