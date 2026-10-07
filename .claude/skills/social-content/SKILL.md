---
name: social-content
description: Use when Jonathan says "social content", "make a short", "cut this video", "edit this Loom", "before and after short", "owner's version", "content repurposer", "clip this", or hands over a Loom or a recording to be turned into something to post or send. The editor's role as one skill: Jonathan records and gives notes, the clone picks what stays, cuts it on this laptop, captions it, checks it, and shows it to him. His notes become rules it reads the next time. Its workflows live under it (the before-and-after short, the owner's walkthrough). Nothing is posted or sent without his go on that piece.
argument-hint: "<before-after-short | owner-walkthrough> [loom link ...] | notes <video> | learn | check <video>"
---

# Social content

One skill for the role a video editor fills. Jonathan, 2026-10-05: "use this video link transcript to build your Social content skill." The video is Christian Peverelli's walkthrough "I Fully Automated My Video Editing Using Claude Code" (https://www.youtube.com/watch?v=HzXD4GVqXwM, 17 minutes). Its method is kept here; its tools are swapped for the ones on this laptop.

The split of work, in the video's words: "I'm the director, Claude's the editor." Jonathan has two jobs: record, and give notes. Every other job is the clone's.

It runs inside Monarc first. It is the Content Repurposer on his list of 50 (`references/agent-catalog.md`, group 7), and ships into a client's business by the same steps once it has passed here.

## The jobs, and what does each one here

The video names seven jobs and one file of rules. This is who does each on this laptop.

| Job | In the video | Here | State |
|---|---|---|---|
| The editor: watches every clip, picks what stays, decides every cut | Claude Code | The clone. It reads the words with their times and writes the edit down as a plan | works |
| The transcriber: types out what was said, with a time on every word | Parakeet | Parakeet, already on this laptop (`scripts/studio_transcribe.py`) | works |
| The finisher: joins the pieces and checks for mistakes before he sees it | ffmpeg | ffmpeg, already here. `scripts/social_content.py check`: picture and sound present, black frames, dead air, level | works |
| The screen editor: frames a screen recording, the zooms, the layout | Tella, through its connector | He records in Loom. The laptop crops to the page and builds the panels. No zoom that follows what he points at | part. Tella is the step up; not bought |
| The animator: titles, logos popping in, motion graphics | HyperFrames (free, from HeyGen) | Only what ffmpeg draws: the panels, the BEFORE and AFTER tags, the captions. HyperFrames is not installed; it needs Node, which this laptop does not have | not there |
| The researcher: puts the real page, post, or paper on screen as proof | A browser | `scripts/page_shot.py` takes a full copy of a live page; the Loom itself shows the page. Only the real thing, never a mock | part |
| The sound designer: music and sound effects, on brand | Epidemic Sound, paid | Four sounds in `media/sfx`. No music library. No sound is added until he sets sound rules | not there |
| The rules: what good looks like | One skill file, about 1,400 lines, 36 rules | `references/content-rules.md`, in his words, 7 rules so far | started 2026-10-05 |

A job marked "not there" is left out of an edit, never faked. Adding one (Node and HyperFrames, Tella, a sound library) is a spend or an install and waits for his go.

## The loop

The video's main point: setting up is quick, and what takes time is teaching it his eye. This is the loop every edit runs.

1. **Start small.** A first try at a new kind of piece is one short or one hook, never a whole batch.
2. **Fetch and read.** `python scripts/social_content.py fetch <loom link> --name <slug>` brings the file and the transcript. A Loom with no sound is refused. `words <folder>` prints what he said, with times.
3. **Read the rules** in `references/content-rules.md` before picking anything.
4. **Write the plan**: a small file in `projects/social-content/plans/` that says what stays, what goes, and why. The plan is the edit. The script only carries it out.
5. **Cut.** `cut <plan>` or `before-after <plan>`. The video and a log land in `media/looms/<set>/`; the log lists every cut with its reason and the words that went.
6. **Check before he sees it.** The script runs the finisher's check after every cut. The clone also looks at frames across the piece and reads the words back from a fresh transcript. Say what was checked and what was not: the clone cannot listen.
7. **Show him.** The piece shows on the CRM's Creative tab (Records, Creative). Tell him what it is, how long, and what was chosen for him.
8. **Take his notes**, with times where he gives them ("at second 22 you did this, I want that"). Change the plan, cut again.
9. **Learn.** Every note that would hold for the next piece goes into `references/content-rules.md` in his words, the same turn. A new chat reads the rules first, so the same miss does not happen twice. The edit and his verdict go on one line in `projects/social-content/log.md`.

## Its workflows

Each is one file in `workflows/`. Read the one you are running before you start.

| Workflow | What sets it off | What comes out | File |
|---|---|---|---|
| Before-and-after short | Two recordings of the same page: the review, then the rebuilt page | A vertical short, one idea, old page on top and new below | `workflows/before-after-short.md` |
| Owner's walkthrough | A review he wants the company's owner to watch | One wide video with the prospect talk and the dead weight out | `workflows/owner-walkthrough.md` |
| Lead review, long form | His Loom review of a lead from the hero check (`/list-building hero-check`) | The long video for YouTube: the cut, the level, a `.srt`, the title and description; uploaded private on his go, published on his second go (`scripts/youtube_api.py`) | `workflows/lead-review-long-form.md` |
| Lead review, the short | The same Loom | A 30 to 60 second vertical short, one idea, the page in one tall panel, the caption to paste; he posts it himself (Jonathan, 2026-10-05: "I dont need metas API") | `workflows/lead-review-short.md` |

A new kind of piece gets its own file once it has been made once and he has seen it.

## The plan files

`cut` (one video from one or more recordings):

```json
{"out": "media/looms/<set>/<name>.mp4",
 "why": "what this piece is for, and his words for the rule behind it",
 "pause": 0.5,
 "parts": [{"folder": "media/looms/<id>-<slug>",
            "cuts": [[0.0, 21.85, "why this goes"]],
            "keep_whole": [[87.0, 117.9]]}]}
```

Every "uh" and "um" and every pause over `pause` seconds comes out by itself. `cuts` are the judgment calls, each with its reason. `keep_whole` is a stretch where the screen is the point, such as a form being filled in.

`before-after` (the short):

```json
{"out": "media/looms/<set>/<name>.mp4",
 "idea": "the one idea, and who it is said to",
 "before": {"folder": "...", "still_at": 25.0},
 "after": {"folder": "...", "still_at": 62.0},
 "segments": [["before", 0.5, 4.75], ["after", 54.8, 61.1]],
 "close": [["after", 86.9, 135.0]],
 "fixes": {"homeloading": "Home lighting"}}
```

`segments` are his own words in the order the short says them. `still_at` is the moment each page's first screen is in view, used for the dimmed panel. `close` moves in on the middle of the page for a stretch (a form or a popup). `fixes` corrects a word the transcript got wrong, for the captions only.

`long-form` (the YouTube version, 2026-10-05): the `cut` plan plus `"kind": "long-form"`, `"company_key": "<domain>"`, `"fixes"`, and a `youtube` block: `title` (his words, under 100 characters, never the company's name), `description` (first line who it is for; the booking link with `utm_source=youtube&utm_medium=video&utm_campaign=lead-review&utm_content=<piece>`), `tags`, `category` (27), `privacy` (`private`). Writes `<name>.srt` and `<name>.youtube.json` beside the video.

`review-short` (one recording, 2026-10-05):

```json
{"out": "media/looms/<set>/<name>.mp4",
 "kind": "review-short",
 "company_key": "<domain>",
 "idea": "the one idea, and who it is said to",
 "folder": "media/looms/<id>-<slug>",
 "segments": [[0.7, 10.6], [21.9, 29.5]],
 "close": [[81.0, 89.4]],
 "fixes": {},
 "face": false,
 "post": {"caption": "first line: who it is for..."}}
```

Refused under 25 or over 65 seconds. The page in one tall panel (`TALL_CROP`), captions under it (`cap_y` to move them). `face` is a hook only. `post.caption` is what he pastes when he posts; `<name>.cuts.md` carries it.

## Rules every edit follows

- **His rules first.** `references/content-rules.md`. Today: cut what does no work and what is not accurate; the owner's version never calls them a prospect; no ums or pauses; no icons dropped on the picture; one idea a short; say who it is for; before and after is a format he wants.
- **His words only.** The clone cuts and orders what he said. It never rewrites, dubs, or adds a voice. A caption may fix a word the transcript misheard; it may not change what he said.
- **Captions** are Monarc Studio's: Montserrat Black, his words in his blue, the word being said in white, two or three words at a time (`projects/studio/config.json`).
- **A named company on screen.** A prospect's site may be shown without asking (Jonathan, 2026-10-05). The piece is held until their deal is closed either way, unless he says otherwise for that piece (the AIOS's caution, `references/opusclip.md`).
- **Never without a go:** posting or scheduling anything, sending a video to anyone, paying for a tool, installing one.
- **OpusClip is not the editor.** His verdict, 2026-10-05: "The opus clip edits suck really bad... they make no sense." It picked moments well and could not hold one idea, a before and after, or his look. It stays wired for posting on a schedule, his to decide (`references/opusclip.md`).
- **Monarc Studio is not this skill.** Studio is where he cuts by hand; its rule that every edit is manual stands for what he makes there.

## Modes

- `<workflow> <loom link ...>`: run that workflow from the links to a first cut.
- `long-form <plan>` and `review-short <plan>`: the two lead-review cuts (`scripts/social_content.py`).
- `upload <video>` and `publish <video-id>`: the two YouTube steps, each only on his go (`scripts/youtube_api.py`).
- `notes <video>`: take his notes on a piece, change its plan, cut again.
- `learn`: write what the last round of notes taught into `references/content-rules.md`, and say which lines were added.
- `check <video>`: the finisher's check on any video.

## The record

`projects/social-content/log.md`: one line an edit, with the plan, the file, and his verdict. `projects/social-content/plans/`: every plan, so any piece can be cut again or changed.

## What the video costs him, for scale

About $27 a video in the video's own count (a share of his Claude plan, Tella at $13 a month, Epidemic Sound at $9.99 a month), against $250 to $1,000 for an editor. Here the tools in use cost nothing beyond the Claude plan.
