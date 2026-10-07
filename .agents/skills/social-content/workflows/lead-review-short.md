# Lead review, the short

Workflow of the social-content skill. Status: built 2026-10-05; the Momentum first-screen short built as the first one (`media/looms/momentum-2026-10-05/short-first-screen.mp4`). He posts it himself.

One line: Cuts one idea out of his Loom review of a lead's page into a vertical short for Instagram and Facebook, which he posts.

Jonathan, 2026-10-05: "Cut them in the short form for Instagram and Facebook." And: "I dont need metas API." So the clone makes the short and writes the caption; he posts it by hand or through OpusClip's connected accounts (`references/opusclip.md`). Nothing posts from here.

## Objective

A 30 to 60 second vertical short from one Loom: one idea, the page in one tall panel, captions under it, the first line saying who it is for, and the caption text ready to paste.

## What sets it off

The same Loom as the long form, once the long form's plan exists (the cuts are already judged). Or a review Loom on its own.

## Procedure

1. Fetch and read as in the long form (steps 1 and 2 there).
2. Pick the one idea (rule 5). The first words of the short must say who it is for (rule 6): find the stretch where he names the audience, or open with the stretch that does.
3. Write the plan, `projects/social-content/plans/<date>-<slug>-review-short.json` (the format is in the SKILL): `segments` in the order the short says them, `close` for a stretch where the middle of the page matters (a form, a popup), `fixes` for misheard words, `post.caption`.
4. `python scripts/social_content.py review-short <plan>`. It refuses a short under 25 or over 65 seconds. It prints the first words; read them: do they say who it is for.
5. Look at frames across the piece: the page panel shows the page, no browser bar, no face bubble, no task bar. Captions sit under the panel.
6. The caption to paste (in `<name>.cuts.md`): first line who it is for; the idea in one or two lines; on Instagram no link ("link in bio"); on Facebook the booking link with `utm_source=facebook&utm_medium=social&utm_campaign=lead-review&utm_content=<slug>`.
7. Show him on the Creative tab. His notes: change the plan, cut again; what holds goes into `references/content-rules.md`.
8. He posts it. When he says it went out, mark it published on the Creative tab (or he does). Log one line in `projects/social-content/log.md`.

## Layout

1080x1920 on the dark ground. One page panel, the whole page width and more of its height than the two-panel short (`TALL_CROP`, 1420x650 of the Loom, stopping above the face bubble), set in the phone's safe band (panel at y 420, captions at 1180; `panel_y` and `cap_y` in the plan move them). Captions in Monarc Studio's style under it. No BEFORE/AFTER tag, no icons. His face is off (`"face": false`); turning it on is his call and is not built yet.

## Rules

- One idea a short (rule 5). The first line says who it is for (rule 6). No icons, no emoji (rule 4).
- His words only. A caption may fix a misheard word; it may not change what he said.
- A named company's page on screen waits for the deal to close unless he says otherwise for that piece.
- Nothing is posted from the laptop. The Meta API is not wired and he does not want it (2026-10-05).

## Criteria for passing

- [ ] 30 to 60 seconds, one idea.
- [ ] The first words say who it is for.
- [ ] `check` clean; frames show the page only.
- [ ] The caption is written, with the right link rule per platform.
- [ ] On the Creative tab, marked published once he posts it.
