# OpusClip

The engine of the Content Repurposer (CRMA, `references/agent-catalog.md`, group 7). Jonathan, 2026-10-05: "We want to do testing first, I guess, but let's just get the tool put in place. Let's use OpusClip." It takes a long video, picks the moments, cuts them vertical, captions them, and posts them on a schedule.

Facts below were read from OpusClip's own pages on 2026-10-05. Nothing has been run yet: no account on file, no clip made.

## Status

- [x] Server added to `.mcp.json` as `opusclip` (2026-10-05)
- [x] OpusClip account made (Jonathan, 2026-10-05). On the free trial: the API calls it tier `TRIAL`, and trial clips carry OpusClip's watermark.
- [x] `OPUSCLIP_API_KEY` in `%USERPROFILE%\.monarc\secrets.env` (Jonathan, 2026-10-05). Read-only call answered: one brand template, vertical, captions on, layout on auto, screen layout off.
- [ ] Signed in from Claude Code: `/mcp`, pick `opusclip`, approve in the browser (Jonathan). Not needed while the key route works.
- [ ] Social accounts connected inside OpusClip (Jonathan; only the ones he picks)
- [ ] Test run: one Loom review, clips looked at, nothing posted. Sent 2026-10-05 through the REST API: project `P3100519EN55`, the Momentum review by its Loom link, model ClipAnything, clips of 30 to 90 seconds, vertical, the pick line "Pick the moments where one specific change to the page is named and shown on screen" (the AIOS's words for the test, not his rule). Not shared, not posted. OpusClip keeps a trial project's files until 2026-10-12.
- [ ] His call after the test: keep it, or add a zoom step

### The first test, 2026-10-05 (project `P3100519EN55`)

15 clips in about 12 minutes, 23 to 89 seconds each, 1080x1920, captions on. The AIOS looked at four frames from two of them ("Stop Using Stock Photos", "Better Headlines"); Jonathan has not looked yet.

- The page text is big enough to read. OpusClip crops into the screen and does not shrink it.
- The crop is fixed and does not follow what he is talking about: a headline is cut off at both sides ("ome Lighting and A"), the logo is cut ("omentum"), and the part he names is often outside the frame.
- The face bubble and the captions sit on top of the page text. The browser's tab bar and the Windows task bar show.
- One frame used the other layout: the whole page across the width, small, with a blurred fill above and below.
- The titles and captions are OpusClip's own style ("Website Secrets Revealed for Electricians!", capitals, green highlight), not his voice. One title names Momentum.
- Trial watermark on every clip.

Read: it finds the right moments and the words can be read, but the framing is the gap, as the comparison said it would be. Fixes to try before a second tool: record with the browser full screen (no tabs, no task bar) and the face bubble in a corner the crop drops; a brand template with his caption style; titles rewritten by the clone in his voice.

Last checked: 2026-10-05.

### The second run, 2026-10-05: the Momentum review joined to the "after"

Jonathan sent two Looms: the review (`ba7df3a7...`, 3:15) and the after, him walking the rebuilt page and its form (`44a700d9...`, 3:41). His words: "The cuts happen in OPUS clip not in loom" and "The stitches also happen in opus clip after a second loom gets sent."

- The key has no way to stitch two videos (that is by hand in OpusClip's editor), so the two were joined on the laptop with ffmpeg and the joined files uploaded. The upload route works: `POST /api/upload-links` with `{"video": {"usecase": "LocalUpload"}}`, start a resumable session on the address it returns (`x-goog-resumable: start`), `PUT` the file to the session's `Location`, then make the project with `videoUrl` set to the `uploadId`.
- Shorts: project `P3100520NmUy`, the whole review plus the after (6:33), vertical, ClipAnything, filler words out (`renderPref.quickstartConfig.enableRemoveFillerWords`, accepted).
- Owner's version: project `P3100520O21H`, the cut with the "master class" opener and "one of my prospects" gone (6:05), wide, `curationPref.skipCurate` true so nothing is picked, filler words out. First use of `skipCurate`; what it returns is not known yet.
- What came back (owner in about 4 minutes, shorts in about 5; the AIOS looked at one frame of each):
  - Owner's version: one clip, wide, 6:02. The filler-word switch took out about 2 seconds of 6:05, so most ums and pauses are still there. OpusClip's mark sits on top of their logo, and the picture is softer than the source (about 1,000 kb/s). The laptop's `owner-cut.mp4` is the better file to send.
  - Shorts: 8 clips, 31 to 68 seconds. This time the layout is split: the screen on top and his face large below, so the page and the form can be read. The captions are OpusClip's style with emoji on top (a pickaxe over his chest in one frame). Titles are OpusClip's ("Website Hacks for More Clients").
- **His verdict, 2026-10-05:** "The opus clip edits suck really bad. I mean they make no sense. It's adding like really weird icons in wrong places like hammers and trophies and ideas aren't centralized." The edit moved to the laptop the same day (`references/content-rules.md`, the before-and-after short). What is left for OpusClip, if anything, is posting on a schedule; his to decide before the trial ends.
- Both on the trial (watermark). Not shared, not posted. All of it shows on the CRM's Creative tab (`projects/crm/creative.json`). The joined files are in `media/looms/momentum-2026-10-05/` (not in git): `owner-cut.mp4` is a clean copy of the owner's version with no watermark, checked by transcript.

## How the AIOS reaches it

Mechanism: `mcp`. Server `https://mcp.opus.pro/mcp`, signed in through `/mcp` with the OpusClip account (OAuth, no key in any file). Any account can sign in and see the tools; calling one needs Pro, Max, or Business.

A second route exists if the first falls short: the REST API (`POST https://api.opus.pro/api/clip-projects`, `Authorization: Bearer <key>`, the key from the lower left of the OpusClip dashboard). It would go in `%USERPROFILE%\.monarc\secrets.env` as `OPUSCLIP_API_KEY`. No script is written; write one only if the MCP cannot do the job.

## What it costs

- Pro: $29 a month, with a free trial. Includes the API, the scheduler API, the MCP connector, the scheduler for six platforms, up to 4 brand templates.
- 1 credit is 1 minute of source video. A project costs at least 10 credits. The cap through the API is 15 hours (900 credits) a month, 4 projects at once, 30 requests a minute.
- An 11-minute Loom review is about 11 credits a run.

## What it can do, by tool

- Take a video: `opusclip_submit_project` (a YouTube or Vimeo link) or `opusclip_create_upload_link` (a file from this laptop). The REST API also takes a Loom link directly; the MCP page does not list Loom.
- Look at a video: `opusclip_analyze_video` (faces, positions, documents on screen), `opusclip_get_transcript`.
- Read the clips: `opusclip_list_projects`, `opusclip_list_clips`, `opusclip_describe_clip`.
- Change a clip: `opusclip_edit_clip` (captions and their color, place, and case; emoji; keyword highlights; filler words and pauses out; trim, split, drop, or reorder sections; cut a phrase; dubbing). `opusclip_create_censor_job` bleeps or masks.
- Get the file: `opusclip_export_clip`, `opusclip_export_collection`.
- Post: `opusclip_create_social_copy_job` (the caption text per platform), `opusclip_create_post_task` (post now), `opusclip_schedule_publish`, `opusclip_unschedule_publish`. Platforms on Pro: YouTube Shorts, TikTok, Instagram, LinkedIn, Facebook, X.
- Brand: `opusclip_list_brand_templates` (made in the OpusClip dashboard, not here).

## Where his rules can go

- What gets picked: the REST API's `curationPref.customPrompt` (the "ClipAnything" model) takes plain words on what to pick, and `clipDurations` sets the length. Whether the MCP tool takes the same words is not on its page; the test finds out. Either way the clone reads the clips against his rules before he sees them.
- How it looks: one brand template (fonts, caption style, layout). There is a screenshare layout.
- Keyframes: not his to set here. OpusClip frames each clip itself. No tool takes a zoom point, a zoom amount, or a time. If the test shows the page cannot be read in the shorts, the zoom step is a second tool (Tella was the pick in the comparison of 2026-10-05).

## Rules for the clone

- Nothing posts without Jonathan's go on each short. `opusclip_create_post_task` and `opusclip_schedule_publish` are never called on a guess.
- A run spends credits. Say the credits before a run; one run at a time while testing.
- A prospect's site and name in a short: allowed without asking them (Jonathan, 2026-10-05: "There is no, like, privacy law on me posting an audit of their website without getting their permission."). Only what is on their public site. The AIOS's cautions, his to take or leave, not yet rules: say opinions and what the page shows, never a claim about their business that cannot be shown; never suggest they are a client; keep a person's name, face, and phone out unless it is on the public page; nothing they said or shared on a call; hold a prospect's short until their deal is closed either way. Not legal advice; no lawyer has read this. A test clip still stays private: no `opusclip_share_project`, no post, until he approves the short.
- Never his sumreat17 account. The OpusClip account and every connected social account are Monarc's.

## The test

1. One Loom review in (the Momentum one is the only one on file, `projects/crm/looms.json`, 11 minutes 23 seconds, about 11 credits).
2. Vertical, with captions, the screenshare layout.
3. He looks at the clips. The one question: can the page be read?
4. Yes: write his content rules, pick a brand template, connect the platforms. No: add the zoom step, then the same.
