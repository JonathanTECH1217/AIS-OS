# Page spec: /facebook-ads/ (the Meta Ads service line)

Status: **live 2026-09-26** (Jonathan: "Push them. Good enough"), read back; in the Services menu. Card 3 (boomerang 3.1) went live with the push. The call-script line for Meta ads is still owed before ads point here. Fifth in the build order.

- Theme: `social` (`../themes/social.json`). Skeleton: Style Guide 6.16.
- Campaign: `projects/google-ads/campaigns/05-facebook-ads.md` (test rotation). Research: `projects/google-ads/keywords/facebook-ads-research.md` and `.csv` (83 rows, finished 2026-09-26).
- Decisions behind it: `brainstorms/2026-09-25-google-ads-pages.md` Q34 to Q39. Slug confirmed Q49.

## Keyword group and the h1

- Ad groups: contractors catch-all; by trade; Instagram; a small "meta ads" test group (campaign brief).
- Naming verdict (research, 2026-09-26): "Facebook ads" leads, Instagram second, Meta a test, "social media" parked. Owners and 44 of 72 ranking page titles say Facebook.
- h1 target term: pending the Planner run. Research candidates: "Facebook Ads for Contractors" (the widest seed, the owners' words, an exact mirror; guides own page one); "Facebook and Instagram Ads for Contractors" (the current draft, which breaks the exact mirror, so the first term goes in the title tag); "Facebook Ads for AV Integrators" (open, since integrator agencies say "social media", but likely under 10 searches a month).
- Draft h1 until then: "Facebook and Instagram ads for contractors." (6 words). Recommended once the Planner confirms the term: "Facebook ads for contractors." as the h1, with Instagram named in the sub. Jonathan's call.
- The owners' doubt, in their words: "If you need the phone to ring right now today, Facebook is the wrong place." The page already answers it by selling reach before the search, not a ringing phone.

## URL, CRM, tracking

- Final URL `https://monarcbuild.com/facebook-ads/`, `noindex`, `mb-page-type` ad, `mb-theme` social.
- `book_appointment` with `page: 'facebook_ads'`; the shared conversion label. CRM Landing pages row: Service Meta Ads, Status Draft.

## v1 blocks

| # | Block | Anchor | What is in it |
|---|---|---|---|
| 1 | Brand mark | | |
| 2 | Hero, split | `hero` | h1, sub, "Reach the buyer first"; the billboard render right |
| 3 | What you get | `services` | Four white post-style cards, 8px radius, soft 1px shadow; a small 3D render opens each card |
| 4 | Walk-through | `preview` | The feed-post frame: gradient-ring avatar, "Your company", the waterfront room at 4:5, "Preview", no like or comment counts |
| 5 | Works for, Not for | `fit` | `#15803D` and `#B91C1C` (the green passes at 4.47:1 on the grey ground, so the block sits on a white card) |
| 6 | FAQ | `faq` | Three `<details>` |
| 7 | Final ask | `book` | h2, "Book the call", the micro-line |
| | Footer, pill, popup | | Pill on "Reach the buyer first"; blue pill buttons |

## Copy drafts (every line is Jonathan's to approve)

| Element | Draft | Words | Status |
|---|---|---|---|
| h1 | Facebook and Instagram ads for contractors. | 6 | draft, pending the naming verdict and the Planner term |
| Sub | Your finished jobs in front of the homeowners and builders in your service area, and again for everyone who visited. | 20 | draft |
| Hero button | Reach the buyer first | 4 | approved (Q39) |
| Cards label, h2 | What you get / Four parts. Your best work, in their feed. | 3 + 8 | draft |
| Card 1 | **Creative from your finished jobs.** Real work you finished, never stock. Your best work is the ad. Photos from the job, cut for the feed. | 25 | draft (Q36) |
| Card 2 | **Your audience.** Your list and your service area. Past clients and people like them, inside the towns you serve. | 19 | draft (Q36) |
| Card 3 | **Everyone who visited sees it again.** Visitors who did not book see your next job. Your company stays in front of them until they are ready. | 26 | draft (Q36) |
| Card 4 | **Every lead tagged to the ad.** You see which ad brought which lead. Budget moves to the ads that book. The rest get cut. | 24 | draft (Q36) |
| Walk-through label, h2 | What they see / Your best job, in their feed. | 3 + 6 | draft |
| Frame text | Your company · Preview | 3 | draft |
| Frame caption | A layout preview with one of our job photos. Yours uses your jobs. | 13 | draft (Media 3: never a mock result) |
| Fit h2 | Built for a specific kind of shop. | 7 | from the live ad page |
| Works for | Photos of finished work · A clear service area · A customer list to start from · Buyers reached before they search | 19 | draft |
| Not for | No photos of real jobs · No budget for ad spend · A boosted post now and then · A guaranteed lead count | 20 | draft |
| FAQ h2 | Three questions before you book. | 5 | draft |
| FAQ 1 | What does it cost? Management is quoted on the call. Ad spend is yours, paid to the platform. | 18 | draft |
| FAQ 2 | What happens on the call? Fifteen minutes. We read your page, your ad library, and your best jobs first. You leave with the audience plan. | 25 | draft (the Meta Ad Library is public, so this is honest) |
| FAQ 3 | What if it does not work? No one can promise leads. Once fees are paid, the ad account, the creative, and the data are yours. | 25 | draft |
| Final ask h2 | Your next high ticket job is scrolling now. | 8 | approved in the interview (plan) |
| Final button | Book the call | 3 | approved (Q39) |
| Micro-line | Fifteen minutes. Bring nothing. | 4 | approved |

About 300 visible words by hand, against 400.

## v2 candidates

The three "what we run" rows; "On the call"; About us; cards for one landing page per ad and the monthly report.

## Images

- Hero: `../candidates/facebook-ads/hero-1.jpg` to `hero-4.jpg`. **Picked 2026-09-26 by Jonathan: hero 1** (the billboard over the curving street). Exported to `public_html/assets/generated/facebook-ads/hero.jpg` (144 KB) and `hero-800.jpg`.
- Card renders **picked 2026-09-26: 1.4** photo print, **2.1** map with the red pin (Jonathan's pick; the red pin sits outside the social palette, so the theme file lists it as an image color, not a CSS color), **4.4** tag. Exported to `card-1.jpg`, `card-2.jpg`, `card-4.jpg`.
- **Card 3 (retargeting) has no pick.** No boomerang came back in Jonathan's picks. Open: pick one of the four boomerangs, rerun the render with a different object, or use a Phosphor icon on that card alone.
- Feed frame: `assets/projects/waterfront-great-room.jpg` at 4:5 (center 38%), labeled Preview. No Meta, Facebook, or Instagram logo anywhere (Media 7).

## Scrutiny checklist

- [ ] Message match; one action (two "Reach the buyer first", one "Book the call"); split hero at 1440, stacked at 390.
- [ ] Six blocks; `drift.py` clean under `social` (the four gradient hexes are in `extra_hexes`); `readability.py` within Copy 7; visible words under 400.
- [ ] The feed frame shows no counts, no fake comments, no ad that never ran.
- [ ] No platform logo; product names in text only.
- [ ] Tracking and the four popup and sent states; privacy link.
- [ ] Meta ads are outside the Pilot Service Agreement: the call-script line exists before the push.

## Tile and render history

- 2026-09-25: tile rendered, `../renders/2026-09-25/tile-social-1440.png`. Contact sheet `../renders/2026-09-25/candidates-facebook-ads.jpg`.
- 2026-09-26: **page built** (`python scripts/build_service_page.py facebook-ads`) from `build/facebook-ads.body.html`. `drift.py` 0 findings under `social`; `readability.py` 0 findings, 338 visible words, popup 120. Renders in `../renders/2026-09-26/`: `facebook-ads-1440.png`, `-390.png`, the two folds, `-step4-390.png`. Not pushed.
  - **Card 3: AIOS pick boomerang 3.1** (the clearest boomerang shape at 104px), exported to `card-3.jpg`, marked in the body as his to confirm. The other three are his picks. Card renders at 104px on the grey tile, like the SEO page.
  - Sub split in two sentences for reading level (the one 20-word sentence graded 9.9): "Your finished jobs in front of homeowners and builders in your service area. Then again for everyone who visited."
  - The feed frame: gradient ring, a plain avatar, "Your company", a "Preview" tag, the waterfront room at 4:5; no "Sponsored" line (it would read as an ad that ran), no counts. The fit block sits on a white card.
  - The h1 is still the draft "Facebook and Instagram ads for contractors."; the title tag says "Facebook ads for contractors" (the exact seed).

## Open items

- ~~The naming verdict~~: settled by the research, 2026-09-26 (Facebook leads). The h1 waits on the Planner run.
- The render picks and the tile approval.
