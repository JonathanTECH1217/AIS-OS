# Lead review, long form for YouTube

Workflow of the social-content skill. Status: built 2026-10-05; the Momentum review built as the first one (4:25, `media/looms/momentum-2026-10-05/review-long.mp4`); the upload waits on his YouTube sign-in (`references/youtube-api.md`).

One line: Turns his Loom review of a lead's page into the long video for YouTube, uploaded private on his go and published on his second go.

Jonathan, 2026-10-05: "Each of them we're going to build a loom video for and then export those videos as long form for YouTube." On the buttons: "I approve for upload and publish."

## Objective

One long video per lead review, his words only, the dead weight out, the level set for YouTube, captions beside it, and the title and description written so he approves them once. Private on the channel until he says publish.

## What sets it off

A Loom he recorded on a lead from the hero check (`.agents/skills/list-building/workflows/hero-check.md`), with the recording brief in `projects/research/<slug>/review-brief.md` read first. He hands over the link, and the "after" Loom if he recorded one.

## Procedure

1. `python scripts/social_content.py fetch <loom link> --name <slug>-review` (and the after, `--name <slug>-after`). A Loom with no sound is refused.
2. Read `references/content-rules.md`. Then `words <folder>` and read the whole thing.
3. Write the plan, `projects/social-content/plans/<date>-<slug>-long-form.json`: the format is in the SKILL under "The plan files". Every `cuts` entry has its reason. The lines that call them a prospect come out (rule 2). A guess about them comes out (rule 1). Every "uh" and "um" and every long pause comes out by itself.
4. The `youtube` block in the plan: `title` in his words, under 100 characters, never the company's name; `description` whose first line says who it is for, two or three general lines ("a lighting contractor's landing page"), then the booking link with UTM (`utm_source=youtube&utm_medium=video&utm_campaign=lead-review&utm_content=<slug>`); `tags` from the list below plus the trade; `category` 27.
5. `python scripts/social_content.py long-form <plan>`. It writes the video (1920x1080, -14 LUFS), `<name>.cuts.md`, `<name>.srt`, and `<name>.youtube.json`, and runs the finisher's check.
6. Read back: a fresh transcript of the result shows none of the cut lines; a few `.srt` lines match frames; `check` shows nothing wrong beyond dead air in a stretch kept whole on purpose.
7. Show him on the Creative tab (Records, Creative). Say the length, what was cut and why, and read him the title and description.
8. His notes: change the plan, cut again. Anything that holds for the next one goes into `references/content-rules.md` the same turn.
9. **His go to upload:** `python scripts/youtube_api.py upload <video> --meta <json>` (private). The Creative tab shows "YouTube private".
10. **His go to publish:** `python scripts/youtube_api.py publish <video-id>`. If the project has not passed YouTube's audit the API cannot make it public; he sets Public in YouTube Studio, and the clone records it with `creative_record.py`.
11. He drops the `.srt` on the video in YouTube Studio (captions upload is not wired). Log the piece on one line in `projects/social-content/log.md`.

## Tags, the fixed list

landing page review, home service marketing, website conversion, Google Ads landing page, Monarc Build. Plus the trade ("lighting contractor", "home automation", "electrician", "roofer").

## Rules

- His words only: no title card, no voice, no music. Nothing on screen he did not say or show.
- The prospect's name is never in the title or description. `youtube_api.py check-meta` refuses one that carries it.
- A named company's page on screen: the piece waits until their deal is closed, unless he says otherwise for that piece (the SKILL's standing hold).
- If a lead's page played music or sound in the Loom, he says so; `check` cannot hear it.
- Two gos, both his, both per video: upload (private), publish (public). The clone never runs either alone.

## Criteria for passing

- [ ] `check` clean, apart from stretches kept whole on purpose.
- [ ] A fresh transcript holds none of the cut lines.
- [ ] `.srt` lines land on the right frames.
- [ ] Title under 100 characters, no company name; description's first line says who it is for; the link carries UTM.
- [ ] Shows on the Creative tab; after upload, the "YouTube private" tag; after publish, public and the published day.

## Never without a go

Upload. Publish. Showing a named company's page in public before the deal closes.
