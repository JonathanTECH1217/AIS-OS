# Batch

Workflow of the Loom B and A skill. Status: written 2026-10-06; first run the same day on the fifteen cold audits of 2026-10-06 plus PHA.

One line: A day's audits become step-by-step cuts with his face, saved by date, each linked in an email draft, and one email to him when the batch is done.

Jonathan, 2026-10-06: "In the media folder can you save all of these by date folders in a Loom B&A folder with the final stitches that get attached as links to the email drafts. When a batch is done I should get an email notification saying batch looms done and this is part of the SOP."

## Where things go

- **The cut:** `media/loom-ba/<date>/<slug>/<slug>-loom-ba.mp4`, with its `.cuts.md` beside it and a copy of the director's script.
- **The plan:** `projects/loom-b-and-a/plans/<date>-<slug>-A.json`. **The director's script:** `projects/loom-b-and-a/scripts/<date>-<slug>.md`. **The page states (working files):** `media/looms/<slug>-ba-<date>/states/`.
- **The render it shows:** `projects/Landing Page Build/prospects/<slug>/index.html` (built first by `scripts/prospect_page.py`).

## One company, in order

1. **Read his words.** `python scripts/social_content.py words <loom folder>`. Read `references/content-rules.md` (rules 1 to 24).
2. **Find the page on screen.** Grab frames (ffmpeg through `scripts/studio_common.ffmpeg_exe()`, `-ss <sec> -frames:v 1 -vf "crop=1920:56:0:62"` for the address bar) at the times he talks about the hero. That URL is the plan's `url`. If he changes pages mid-Loom, the hero page he reviews is the one.
3. **Find his face bubble.** One full frame at 1920x1080; the bubble is usually bottom left. The plan's `face.crop` is a square `w:h:x:y` just inside the circle (PHA's: `244:244:31:743`). If there is no bubble, leave `face` out and say so.
4. **Write the director's script first** (`projects/loom-b-and-a/scripts/2026-10-06-pha-v2.md` is the model; copy its shape): the beats, each with his words, the Loom second (from `python scripts/loom_ba.py find <folder> "phrase" "phrase@after"`), the second in the cut, and what the viewer sees; the cuts with reasons; what is left for him.
   - **Act one, their live page:** each change he names about their first screen, as a live edit on their page (kinds: `cta`, `image`, `headline`, `eyebrow` with `reuse: true` when a line already sits above the headline, `center`, `font`, `colors`, `copy`, `bigger`, `header`, `click`, `note`). Use the words the render uses (`spec.json` in the render folder), so the live page lands on the render.
   - **Act two, the rebuilt page:** from the moment he moves past the first screen ("below that", the section order), `section` steps (`band`: hero, cards, about, process, work, reviews, services, faq, final, only bands the render has) as he names each one, and `form` steps 1 to 4 when he counts the form fields. End on `section` `hero`.
   - **His words, what they mean** (2026-10-07): "review section" is the `reviews` band; "review banner" (the stars, the rating, "below the call to action") is the `hero` band. "Header" is the top bar: a `header` step lays the render's header on their page. "The calendar" after the form is `form` step `sent`. When he clicks to the next photo or slide on their page, a `click` step on that control.
   - **The spec, before the render** (rules 15 to 23): the header menu and a dark header when theirs is dark (`header: {dark, logo}` with a `logo-light.png`); three benefit cards; their own work photos; `google` rating and reviews from `python scripts/research.py google "<name and city>" --name <slug> --photos`. The hero photo is the one on their live page unless he names another, so the swap does not change the picture (Lighthouse, 2026-10-07); a brand's stock shot is never used (Reliant's Control4 photo).
   - **When a standing note makes his spoken words wrong** (TruDefinition's "white overlay", 2026-10-07): cut those words (rule 1) and show the page the note asks for.
5. **Write the plan** (`projects/loom-b-and-a/plans/2026-10-06-pha-v2-A.json` is the model): `out` `media/loom-ba/<date>/<slug>/<slug>-loom-ba.mp4`, `states_dir` `media/looms/<slug>-ba-<date>/states`, `render`, `url`, `folder`, `face`, `start_at` (his first useful word), `end_at` (after his ask, before the sign-off ramble), `cuts` with a reason each, `fixes` for misheard words, `changes`.
6. **His standing notes:** `python scripts/loom_ba_rules.py <plan>` (a dry run), then `--write`. It keeps only the final version of a change, moves a "review banner" step to the hero, adds the calendar step, and adds the header step.
7. **States:** `python scripts/loom_ba.py states <plan>`. Every line must say what it did; "no ..." or "failed" means a change missed. Look at frames 01 to the last act-one frame and the first act-two frame side by side: the last live frame should match the render's first screen in size (rule 11). Fix with a `selector` or a `css` step, then run again.
8. **Cut:** `python scripts/loom_ba.py cut <plan>`. It refuses over 5:00. Trim with reasons until it fits, never his offer or a change.
9. **Check:** three frames from the cut (one in act one, the swap, one in act two): the change is on screen at its words, the face is in, the captions read.
10. **Copy the director's script** into the cut's folder. Add a line to `projects/loom-b-and-a/log.md`.

## The batch's end (`scripts/loom_ba_batch.py`)

- `python scripts/loom_ba_batch.py index <date>`: lists every cut in `media/loom-ba/<date>/` with its length and check, into `index.json` and `index.md`.
- `python scripts/loom_ba_batch.py drafts <date>`: one Proton draft per company from `templates/loom-ba-email.md` (subject lines in rotation, body B1), the link to its video, to the address on its row; a company with no address gets no draft and is listed.
- `python scripts/loom_ba_batch.py notify <date>`: the "Batch looms done" email in his inbox: each company, its length, its link, its draft or why none.

Nothing is sent. The drafts wait for him.

## His notes, and the SOP they change

Jonathan, 2026-10-07: "I will leave notes on each video for where it went wrong so the SOP can be adjusted." He leaves them in the CRM under the player (Today, a draft's reader; or Records, Creative, the batch's group). Each note keeps the second the video was on. They are saved in `projects/loom-b-and-a/notes/<date>.json` as `{slug: [{at, text, on}]}`.

The notes pass, run when he says the notes are in (or at the start of the next batch):

1. Read every note in the batch's file, grouped by kind: the picture (a change at the wrong time, a size off, a section shown wrong), the words (a cut that should stay, a line that should go, a caption), the face, the email.
2. For each, decide where the fix lives and write it there the same turn:
   - **One video only:** that plan (`plans/<date>-<slug>-A.json`), then `states` and `cut` again.
   - **Every video:** a rule in `references/content-rules.md` in his words; a step in this file; or the engine (`scripts/loom_ba.py`, `scripts/prospect_page.py`), so the next batch does not make the same miss.
3. Recut the videos whose plans changed. Rerun `python scripts/loom_ba_batch.py index <date>` and `pages <date>`; the drafts keep their links.
4. Under each note's company, the director's script gets a "His notes" table: his note, its second, the change made, and where (plan, rule, step, or engine).
5. Tell him, in one line a note: what changed and where. A note that cannot be met says why.
