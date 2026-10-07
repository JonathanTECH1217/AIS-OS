---
name: loom-b-and-a
description: Use when Jonathan says "Loom B and A", "B and A", "before and after of the rebuild", "the step-by-step cut", "the trailer cut", "cut this Loom into the changes", pastes a Loom link in which he talks over a company's page and names the changes, or asks for the email that carries that video. One Loom becomes a video where each change he names shows on their page the second he says it (variation A), or the finished page first, then the changes, then the finished page (variation B), under five minutes; then an email draft with subject lines to test. Nothing is sent without his go.
argument-hint: "<steps-cut | trailer-cut | send-email> <loom link | plan | company> | notes <video> | record --company <key> --loom <url> --subject S1 --body B1"
---

# Loom B and A

One skill for one kind of piece: the before and after of a website rebuild that he talks over. Jonathan, 2026-10-06: "We're going to make a skill called Loom B and A."

His words for how it works: "me recording a video in Loom, pasting the link into the chat, and then what you're going to do is take that video and we're going to use the latest and greatest tools for cutting and editing frames and moving cut clips in a relevant way that shows either step by step, so every time I say something that changes, we see that change happen to their website."

It is the editor's role (`/social-content`) on one piece, with its own hands: `scripts/loom_ba.py` renders the page states and makes the video; the social content script does the fetch, the words, the captions, and the check; its rules (`references/content-rules.md`) hold here.

## What he gives

One Loom link. In it he talks over the company's page and names the changes one at a time ("headline", "the hero should get centered", "cut the copy by around twenty percent, just keeping the first sentence", "change the CTA from get a quote to book a meeting", "swap this stock background image"). The page is the one on screen in the Loom.

## The two variations

| Variation | What it is | Workflow |
|---|---|---|
| A, the steps | The page as it is, then each change fading in the second he names it, in his order | `workflows/steps-cut.md` |
| B, the trailer | The finished page scrolls under his first words, then who he is, then the changes one by one, then the finished page again | `workflows/trailer-cut.md` |
| The email | The Proton draft that carries the link: one of three subject lines, one of two bodies, recorded so the test can be read | `workflows/send-email.md` |
| The batch | A day's audits: each cut saved in `media/loom-ba/<date>/<slug>/`, a page a video built for monarcbuild.com (pushed on his go), an email draft a company with the link, and "Batch looms done" in his inbox (Jonathan, 2026-10-06: "this is part of the SOP"). The cold email channel's campaign is "Loom B and A: cold audits" (Airtable Campaigns `recSBUxwNpumAhvYO`) | `workflows/batch.md`, `scripts/loom_ba_batch.py` |

Both under five minutes. Jonathan: "we keep these videos under five minutes for retention. Three minutes is really really good." `cut` refuses over five and says so over three.

## The loop

1. **Fetch.** `python scripts/social_content.py fetch <loom link> --name <company>-ba`. A Loom with no sound is refused.
2. **Read the words.** `python scripts/social_content.py words <folder>`. Then read `references/content-rules.md`.
3. **Write the plan** in `projects/loom-b-and-a/plans/<date>-<company>-<A|B>.json`: the page's URL, `start_at` and `end_at`, the cuts with their reasons, and every change with the second he names it (`at`), its kind, and its words (the fields are in the script's head). A change the page cannot show (a review section below the fold, a line about response time) is kind `note`: the picture holds. One plan a variation; B adds `trailer.under` and `final.under`, the words the finished page scrolls under.
3b. **Write the director's script** (Jonathan, 2026-10-06: "make a director's script prior to sending this into the editing engine... step by step making the adjustments that the prospect sees based on what I'm saying, one by one") in `projects/loom-b-and-a/scripts/<date>-<company>.md`: every beat with his words and their time, its time in the cut, and what the viewer sees; then every cut with its reason; then what is left for him. Act one is their live page changed in the browser; act two, once he moves to the section order, is the rebuilt page (`render` in the plan, `section` and `form` steps) moving to each section as he names it. Find word times with the transcript, never by ear.
4. **Render the states.** `python scripts/loom_ba.py states <plan>`: the page as it is, then after each change, one JPEG each, plus the whole finished page. Look at every JPEG. A change that did not land (the wrong element, a box still left) gets a `selector` or a `css` change in the plan, then `states` again.
5. **Cut.** `python scripts/loom_ba.py cut <plan>`. The video and its `.cuts.md` land in `media/looms/<set>/`, which the CRM's Creative tab lists.
6. **Check.** The finisher's check runs after the cut. Pull four frames across the piece and look: the right state at the right words, the captions readable, nothing cut off. Read the caption words for a misheard one and add it to `fixes`.
7. **Show him.** Say what it is, how long, which changes show, and what was cut.
8. **Notes, then cut again.** His notes with times go into the plan. Any note that holds for the next piece goes into `references/content-rules.md` in his words, the same turn. One line in `projects/loom-b-and-a/log.md`.
9. **The email**, on his go on the piece: `workflows/send-email.md`.

## The kinds of change the page can show

headline, eyebrow, center, bigger, colors, cta, copy, image, sections, hide, text, css, note. What each takes is in `scripts/loom_ba.py`. The page is changed only in the browser's copy, with inline styles; the live site is never touched; nothing is typed into a form or sent. Squarespace, Wix, and Elementor grids are centered block by block (checked on PHA's Squarespace page, 2026-10-06).

**The finish.** His standing rules for a rebuilt page that the Loom does not name go in the plan's `finish` list: applied after the last change, not a step in the video, shown in the finished page's scroll. The first is the background pattern (Jonathan, 2026-10-06: "Background should be in this pattern. A B A C A B A. Hero, Services, About, Our process, Portfolio, Secondary Services, FAQ, and then secondary CTA. The pattern just goes for the change in the background color to show the different sections."): `{"kind": "sections", "pattern": "ABACABA", "colors": {"A": ..., "B": ..., "C": ...}}`, the three colors per page by his rule: A is the first section's ground, B its opposite, C the brand color pushed toward A (`projects/Landing Page Build/Taste Log.md`, 2026-10-06). The landing page skill's taste log is where rebuilt-page rules live; this skill reads it before writing a finish.

## The jobs, and who does each here

| Job | Here | State |
|---|---|---|
| The editor: reads the words, writes the plan | The clone | works |
| The words with times | Parakeet (`scripts/studio_transcribe.py`, through `social_content.py fetch`) | works |
| The page states | Playwright on headless Edge, 1440 x 900, tracking hosts blocked | works |
| The cut, the fades, the scroll, the captions, the level | ffmpeg (`loom_ba.py cut`) | works |
| The animator: the headline sliding to the middle, the button's words changing in place, lower thirds | HyperFrames (HeyGen, free, Apache-2.0): the "latest and greatest" he asked for. Needs Node, which this laptop does not have; `winget install OpenJS.NodeJS.LTS` is the one line. `references/hyperframes.md` | waits on his go to install |
| His face bubble on the picture | Cut from the Loom with the same stretches as his voice, round with a white ring, bottom left, under the captions (plan `face`: the bubble's crop in the Loom frame, its size, its spot). His rule 10 | works (2026-10-06) |
| Live edits at the render's size | With a `render` in the plan, each live change takes the render's own size, font, and spacing as it lands, a page builder grid is restacked into one column at the center step, and the words are held at the render's height. His rule 11 | works (2026-10-06) |
| Sound | None added, as in every cut (no sound rules yet) | not there |

## Rules every piece follows

- **His rules first.** `references/content-rules.md`, rules 1 to 9.
- **His words only.** The clone cuts and orders what he said; a caption may fix a misheard word. No line he did not say, on screen or in sound.
- **A change shows the second he names it.** The `at` time is the first word of the change in the transcript.
- **Nothing is faked.** A change the page cannot show is a `note`, and the log says so. A state that landed wrong is fixed or marked, never papered over.
- **A named company.** Their public page may be shown (Jonathan, 2026-10-05). The video is for that company; it is not posted anywhere.
- **Never without a go:** sending the email, posting the video anywhere, installing a tool.

## Modes

- `steps-cut <loom link | plan>`: variation A from a link (fetch, words, plan, states, cut) or from a written plan.
- `trailer-cut <loom link | plan>`: variation B the same way.
- `send-email <company>`: the draft into Proton Drafts from `templates/loom-ba-email.md`, and the record line.
- `notes <video>`: his notes into the plan, cut again.
- `notes <date>`: the batch's notes pass (`workflows/batch.md`, "His notes"): his notes from the CRM (`projects/loom-b-and-a/notes/<date>.json`) become plan fixes for one video, or rules, steps, and engine fixes for every video; the changed videos are cut again.
- `record ...`: `python scripts/loom_ba.py record` marks watched or replied on a send.

## The record

`projects/loom-b-and-a/log.md`: one line a piece. `projects/loom-b-and-a/plans/`: every plan. `projects/loom-b-and-a/sends.json`: every email that carried one, with its subject line and body, watched, replied.

## Open, his to answer

- Whether his face bubble belongs on the picture, and where.
- Where the email sits: the cold sequence's Email 1 (his word 2026-10-06: Email 1 carries the rebuilt page's link) or a touch of its own.
- Node, so HyperFrames can be tried against the ffmpeg cut on one piece.
