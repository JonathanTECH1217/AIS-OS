# Trailer cut (variation B)

Workflow of the Loom B and A skill. Status: first cut made 2026-10-06 on the PHA review Loom (`media/looms/pha-2026-10-06/loom-ba-B.mp4`, 1:04), not watched, not approved. That Loom has no "who I am" part, so the trailer leads straight into the changes.

One line: The finished page first, then who he is, then the changes one by one, then the finished page again.

Jonathan, 2026-10-06: "a trailer preview of their new homepage. Leading into my introduction, talking about who I am. And then talking about the editing step by step, and then they see the whole entire final product."

## Objective

The same piece as the steps cut, opened with the result so the owner knows in ten seconds what the video is, and closed on the whole finished page.

## What sets it off

The same Loom as the steps cut. For the "who I am" beat, the Loom needs a line where he says who he is; if he did not record one, the trailer leads into the changes and the log says so.

## Procedure

1. Steps 1 to 4 of `workflows/steps-cut.md`. The plan is `<date>-<company>-B.json` with `"variation": "B"`; it may point at the A plan's `states_dir` so the states are rendered once.
2. Add `trailer.under`: the stretch of his words the finished page scrolls under at the start. His first kept words, as long as they say what the video is.
3. Add `final.under`: the stretch the finished page scrolls under at the end. His last kept words.
4. `states` (if not rendered for A), then `cut`, then the frames and the captions as in the steps cut.
5. Tell him, and say whether the "who I am" beat is in it.

## What it looks like

- The steps cut's look, plus: the whole finished page scrolling top to bottom, eased, under his first words; the same at the end.
- The scroll takes exactly as long as the words under it, so the page's length sets the speed. `screens` in the plan caps how far down the trailer goes (PHA's page is fifteen screens; the trailer takes the first four in nine seconds); the final scroll runs the whole page, so a long page wants longer `under` words at the end.

## Criteria for passing

The steps cut's, plus:
- [ ] The opening scroll shows the finished page with every section loaded (no blank sections).
- [ ] The "who I am" beat is his line, or the log says there was none.

## What it never does without a go

Send it, post it, or add a line he did not say.
