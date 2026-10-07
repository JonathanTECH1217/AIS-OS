# Before-and-after short

Workflow of the social content skill. Status: first cut made 2026-10-05 (Momentum, 44 seconds), not approved; he has not given notes on it yet.

One line: Turns a page review and its rebuild into one vertical short that shows the old page and the new one.

Jonathan, 2026-10-05: "it's supposed to be speaking to home service companies and also giving them like a before and after of the website would be a good one."

## Objective

One short a review, 30 to 60 seconds, that a home service owner can follow with the sound off: who it is for, what was wrong, what it became.

## What sets it off

Two Loom recordings of the same page: the review (he talks through the changes) and the after (he walks the rebuilt page). Both with sound.

## What he gives

The two Loom links. Nothing else.

## Procedure

1. Fetch both: `python scripts/social_content.py fetch <link> --name <company>-review` and `--name <company>-after`.
2. Read both transcripts (`words <folder>`) and the rules (`references/content-rules.md`).
3. Pick one idea. Not a tour of every change: the one change a stranger would understand in a glance. The first screen of the page is the default, since both recordings open on it.
4. Pick his words, in this order:
   - one line that says who it is for (rule 6). If he did not say one, there is no short yet: ask him for a line, do not write one.
   - two to four lines from the review that name what is wrong or what will change
   - two to four lines from the after that show it done
   - a last line that lands the point, if he said one
5. Find `still_at` for each recording: a moment when that page's first screen is in view.
6. Mark any stretch where a form or popup is open as `close`.
7. Write the plan in `projects/social-content/plans/<date>-<company>-before-after.json` and run `before-after <plan>`.
8. Look at frames across the result: both tags show, nothing is cut off at the sides, the captions sit between the panels, his face bubble and the browser bar are out. Read the caption text for a misheard word and add it to `fixes`.
9. Tell him it is on the Creative tab, with its length, the idea, and the lines used.

## What it looks like

- 1080 by 1920. A dark ground.
- Top panel: the old page, a red BEFORE tag above it. Bottom panel: the rebuilt page, a green AFTER tag above it.
- The panel he is talking about plays. The other shows its first screen, dimmed.
- Captions between the two panels.
- No emoji, no stickers, no music, no sound effects.

## Criteria for passing

Before he sees it:
- [ ] The first line names who it is for.
- [ ] One idea. Every line kept serves it.
- [ ] Every line is his, in words he said.
- [ ] Nothing said is untrue of what is on screen.
- [ ] 30 to 60 seconds. The finisher's check finds nothing wrong.

After his first watch:
- [ ] His notes are in the plan and the piece is cut again.
- [ ] Any note that holds for the next short is in `references/content-rules.md`.

Before it is posted:
- [ ] He approved this piece.
- [ ] The company on screen has a closed deal, or he said to post anyway.

## What it never does without a go

Post it, schedule it, or send it to anyone. Add a line he did not say.

## Open, his to answer

- Whether the opening line should be on screen as a headline as well as said.
- Which platforms, and whether each gets the same cut.
- Whether his face should show at all.
