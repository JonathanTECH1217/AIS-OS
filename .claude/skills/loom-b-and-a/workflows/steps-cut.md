# Steps cut (variation A)

Workflow of the Loom B and A skill. Status: first cut made 2026-10-06 on the PHA review Loom (`media/looms/pha-2026-10-06/loom-ba-A.mp4`, 1:04, six changes shown), not watched, not approved.

One line: The page as it is, then each change he names fading in the second he names it.

Jonathan, 2026-10-06: "as I'm saying these things, they change one by one. So that would be variation A."

## Objective

A video under five minutes (three is the mark) that a company owner can watch and see their own first screen become the rebuilt one, change by change, in his voice.

## What sets it off

A Loom link in which he talks over a company's page and names the changes.

## Procedure

1. `python scripts/social_content.py fetch <link> --name <company>-ba`, then `words <folder>`.
2. Read `references/content-rules.md`.
3. Find the page's URL (the one on screen in the Loom; the company's research folder or the hero-check row has it).
4. Write the plan, `projects/loom-b-and-a/plans/<date>-<company>-A.json`:
   - `start_at`: his first word that belongs in the piece. Talk about them being a prospect and the setup go (rule 2).
   - `end_at`: his last word that belongs.
   - `cuts`: every stretch that does no work or is not accurate, each with its reason (rule 1).
   - `changes`: one entry a change, `at` the first word of it. The kind and its words from what he said: the headline he reads out, the button label, the eyebrow, the percent, the colors. A change below the first screen or one the page cannot show is `note`.
   - `fixes`: words the transcript got wrong, for the captions.
   - `finish`: his standing rules for the finished page that the Loom does not name, from `projects/Landing Page Build/Taste Log.md` (the A B A C A B A background pattern first). Not steps in the video; they show in the finished page's scroll.
5. `python scripts/loom_ba.py states <plan>`. Look at every JPEG. Fix a change that did not land with `selector` or a `css` change; run `states` again.
6. `python scripts/loom_ba.py cut <plan>`. Read the `.cuts.md`: each change's second in the Loom and in the video.
7. Pull four frames across the video and look. Read the caption words.
8. Tell him: the file, the length, the changes shown, what was cut and why. It is on the Creative tab.

## What it looks like

- 1920 by 1080. The page state at frame height on a dark ground, 96 px of ground each side.
- Each change fades in over 0.35 seconds, starting the second he names it.
- Captions over the lower band of the page in Monarc Studio's style, three words at a time.
- His voice, his words, the level at -14 LUFS. No music, no title, no face bubble (not built).

## Criteria for passing

Before he sees it:
- [ ] Every change he names is in the plan, as a change or a note.
- [ ] Every state JPEG shows the change it claims. None is faked.
- [ ] Under five minutes. The finisher's check finds nothing wrong.
- [ ] Every line kept is his, in his words.

After his first watch:
- [ ] His notes are in the plan and the piece is cut again.
- [ ] Any note that holds for the next piece is in `references/content-rules.md`.

Before it goes to the company:
- [ ] He approved this piece.
- [ ] The email draft is his to send (`workflows/send-email.md`).

## What it never does without a go

Send it, post it, or add a line he did not say.
