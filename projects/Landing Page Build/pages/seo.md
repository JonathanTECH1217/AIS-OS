# Page spec: /seo/ (SEO)

Status: **live 2026-09-26** on Jonathan's go ("go with posting the pages"), read back; in the Services menu. Third in the build order. The call-script line for SEO is still owed before ads point here.

- Theme: `saas` (`../themes/saas.json`). Skeleton: Style Guide 6.16.
- Campaign: `projects/google-ads/campaigns/03-seo.md` (first 30-day test slot). Research: `projects/google-ads/keywords/seo-research.md` and `.csv`.
- Decisions behind it: `brainstorms/2026-09-25-google-ads-pages.md` Q22 to Q27; Jonathan: "GMBP, Organic Search, AEO, Copywriting. This page can be more of a SAAS style page with modern design and minimal."

## Keyword group and the h1

- Ad groups: integrators; electricians; home services; profile; contractors catch-all.
- h1 target term: pending the Planner run. Research candidates: "Local SEO for Contractors" (two buy terms, "local" filters national SEO shoppers; Blue Corona owns the exact page); "SEO for Home Service Companies" (covers all five trades, no trade hook); "Google Business Profile Management for Contractors" (the map listing is the pain in every review quote; narrows the page to one of the four parts).
- AEO: owners type the outcome ("how to get my business to show up in chatgpt"), not the acronym. Keep AEO terms in the compare tier until the Planner shows volume; the card glosses the word.
- Draft h1 until then: "SEO for contractors. Found first, everywhere." (6 words).

## URL, CRM, tracking

- Final URL `https://monarcbuild.com/seo/`, `noindex`, `mb-page-type` ad, `mb-theme` saas.
- `book_appointment` with `page: 'seo'`; the shared conversion label. CRM Landing pages row: Service SEO, Status Draft.

## v1 blocks

| # | Block | Anchor | What is in it |
|---|---|---|---|
| 1 | Brand mark | | |
| 2 | Hero, split | `hero` | h1, sub, "Get found first" with an arrow; the mid-build house render right |
| 3 | The four parts | `services` | Four cards, 16px radius, hairline border; a small 3D render opens each card |
| 4 | Proof | `proof` | A "Page 1" row beside the ranking line, then the one Georgian card |
| 5 | Works for, Not for | `fit` | `#15803D` and `#B91C1C` |
| 6 | FAQ | `faq` | Three `<details>` |
| 7 | Final ask | `book` | h2, "Book the rank check", the micro-line |
| | Footer, pill, popup | | Pill on "Get found first"; indigo buttons |

## Copy drafts (every line is Jonathan's to approve)

| Element | Draft | Words | Status |
|---|---|---|---|
| h1 | SEO for home services. Found first, everywhere. | 7 | **changed by Jonathan 2026-09-26** (was "SEO for contractors. Found first, everywhere."); matches the research candidate "SEO for Home Service Companies" |
| Sub | Your map listing, your pages, and AI answers, all pointing at your company. Written in your trade's words. | 18 | draft |
| Hero button | Get found first | 3 | approved (Q26) |
| Cards label, h2 | The four parts / Four parts, one goal: found first. | 3 + 6 | draft |
| Card 1 | **Google Business Profile.** The map listing, the first thing buyers see. Built out by service and photo. Reviews asked for after every job. | 23 | draft (Q23 gloss) |
| Card 2 | **Organic search.** The pages that rank. One page per service and per town, written for the search that brings the buyer. | 21 | draft |
| Card 3 | **AEO.** Showing up in AI answers. ChatGPT and Google's AI answers quote pages that answer plainly. We write yours that way. | 21 | draft (describes the method, claims no result) |
| Card 4 | **Copywriting.** The words on every page. Plain, specific, in your trade's words. Every page asks for the call. | 18 | draft |
| Proof h2 | One page ranked first. The job followed. (was "A $69k job followed.", figures off 2026-09-27, Style Guide Copy 4) | 7 | changed by Jonathan's rule |
| Page 1 row | Page 1 · First for whole home audio in Annapolis. A contractor restoring a Georgian Colonial found that page. | 19 | from the live ad page and `context/about-business.md` |
| Georgian card | Georgian Colonial restoration · Whole home audio, James Loudspeaker indoors and out, wired from rough-in. (the $69k came off 2026-09-27) | 14 | from the live ad page card |
| Fit h2 | Built for a specific kind of shop. | 7 | from the live ad page |
| Works for | Missing from the map in your own town · Real jobs and reviews to show · Patience measured in months · Pages you want to keep | 23 | draft |
| Not for | Page one next week · A one-time listing fix · A guaranteed ranking · No service area to rank in | 17 | draft (the research's $50 profile-fix shoppers) |
| FAQ h2 | Three questions before you book. | 5 | draft |
| FAQ 1 | What does it cost? Quoted on the call, by how many services and towns need pages. | 16 | draft |
| FAQ 2 | What happens on the call? Fifteen minutes. We check where you show up for your services in your towns. You leave with the rank check. | 25 | draft |
| FAQ 3 | What if it does not work? Rankings take months and no one can promise one. Once fees are paid, the pages and the profile work are yours. | 27 | draft; trim if the build runs long |
| Final ask h2 | Be the company they find first. | 6 | draft |
| Final button | Book the rank check | 4 | approved (Q26) |
| Micro-line | Fifteen minutes. Bring nothing. | 4 | approved |

About 300 visible words by hand, against 400.

## v2 candidates

The citations strip; "On the call"; the map-pack card with "Your company" as the name; About us.

## Images

- Hero: `../candidates/seo/hero-1.jpg` to `hero-4.jpg`. ~~**Picked 2026-09-26 by Jonathan: hero 4** (the framed house on its slab, roof going on, a builder at the corner). Exported to `public_html/assets/generated/seo/hero.jpg` (102 KB) and `hero-800.jpg`.~~
- **Hero redone 2026-09-26 (Jonathan: "a map, pin icon, five star reviews, and jumbled up being lassoed by who looks like a contractor in the same cartoon style"; interview Q59 to Q67 in `brainstorms/2026-09-25-google-ads-pages.md`).** A contractor in a white hard hat, indigo shirt, and tool belt stands on a clay town map and hauls in, on a tight rope, a big indigo pin (the card 1 pin, house inside) tangled with a white review card with five gold stars. Four candidates, `../candidates/seo/hero-5.jpg` to `hero-8.jpg`, hero 4 and card 1.12 as references, `../candidates/jobs-2026-09-26d.json`, 8 credits (all four came back labeled nano_banana_2). Sheet: `../renders/2026-09-26/candidates-seo-lasso.jpg`. All four have the white hard hat, tool belt, town map, the house pin, five gold stars, no letters. 5 and 7: the rope holds the pin only, the card hangs beside it (7 has the largest contractor). 8: an open loop floats above the pin, closer to mid-throw than caught. 6: the rope wraps the pin and the card together, pulled tight, the Q65 moment. ~~AIOS pick: hero 6.~~ **Jonathan picked hero 7** (sent it back; matched by pixels, 5.2 against 18.9 and up for the rest). Exported to `hero.jpg` (90 KB) and `hero-800.jpg`; the house is still `../candidates/seo/hero-4.jpg`.
- Card renders **picked 2026-09-26: 1.1** map pin, **2.3** magnifier, **3.3** speech bubble, **4.1** fountain pen. Exported to `public_html/assets/generated/seo/card-1.jpg` to `card-4.jpg`.
- **Card 1 redone the same day (Jonathan: "The home service icon needs to be better"; direction "Show the trades").** Four new candidates, a map pin with a house and the trade tools (wrench, lightning bolt, roof shingles, fan), 8 credits, job ids in `../candidates/jobs-2026-09-26.json`, files `card-1-5.jpg` to `card-1-8.jpg`. ~~In use: 1.5, the house in a white pin head with the tools at its base.~~ **Second redo, same day (Jonathan: "just a map icon with a house should do it. But scale the house up slightly").** Candidate 1.5 was given back to the generator as the reference with the tools removed and the house enlarged, four variations, 8 credits, `../candidates/jobs-2026-09-26b.json`, files `card-1-9.jpg` to `card-1-12.jpg`. In use: **1.12**, a full indigo pin with a large white house on a white disc, the largest house of the set and the closest match to the other three card icons (sheet `../renders/2026-09-26/seo-card1-house-only.png`). 1.10 and 1.11 keep the white pin head of the first version.
- Every card render is now cropped tight to its object before export (`scripts/ads_images.py`, `tight()`), and the SEO tiles grew from 88px to 104px, so the objects fill the tile. The Facebook card renders were re-exported the same way.
- Proof: the Georgian card uses `assets/georgian/rough-in-01.jpg` (center 20%).

## Scrutiny checklist

- [ ] Message match; one action (two "Get found first", one "Book the rank check"); split hero at 1440, stacked at 390.
- [ ] Six blocks; `drift.py` clean under `saas`; `readability.py` within Copy 7 (AEO and ChatGPT in the exempt list); visible words under 400.
- [ ] AEO and the Business Profile claim nothing; the only result on the page is the Annapolis ranking.
- [ ] Card renders under 60 KB each; hero at or under 300 KB; renders labeled as illustrations.
- [ ] Tracking and the four popup and sent states; privacy link.
- [ ] SEO is outside the Pilot Service Agreement: the call-script line exists before the push.

## Tile and render history

- 2026-09-25: tile rendered, `../renders/2026-09-25/tile-saas-1440.png`. Contact sheet `../renders/2026-09-25/candidates-seo.jpg`.
- 2026-09-26: **page built** (`python scripts/build_service_page.py seo`), `projects/monarcbuild-site/public_html/seo/index.html`. `drift.py` 0 findings under `saas`; `readability.py` 0 findings, 338 visible words, popup 119. Card renders shown at 88px on the indigo tint. Fixed on the first render: "Page 1" wrapped to two lines (the figure column is now as wide as the figure) and the section labels on the tinted bands lost the indigo (a shared `site.css` rule; labels now keep the theme color on bands, which also touches the live Google Ads page once `site.css` is pushed again). Renders in `../renders/2026-09-26/seo-*.png`. Not pushed; waiting on Jonathan's render approval.
- 2026-09-26, the lasso hero (Q59 to Q67): hero 6 in the page, then hero 7 on Jonathan's pick (same checks, 0 and 0, 340 words), pushed live the same day; alt "Illustration: a contractor in a hard hat on a clay town map, pulling in a map pin and a five-star review card with a rope". Rebuilt; `drift.py` 0 findings under `saas`; `readability.py` 0 findings, 340 visible words, popup 119. Renders `seo-fold-1440.png`, `seo-fold-390.png`, `seo-1440.png`, `seo-390.png`. Phone heads and hero centered (the shared change of the Google Ads round 2). Not pushed.
- 2026-09-27: the job figures off (above) and the "Other services" row above the footer; **pushed the same day** on Jonathan's "push the updates", read back.
