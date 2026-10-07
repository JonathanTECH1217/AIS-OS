# Page spec: /website-build/ (Website design)

Status: **live 2026-09-26** in the editorial theme on Jonathan's go ("go with posting the pages"), read back; in the Services menu. The portfolio frames now show the Google Ads page (round 2) and the SEO page (`assets/generated/website-build/portfolio-google-ads.jpg`, `portfolio-seo.jpg`, 800x500 from the 1440x900 fold renders); ~~Email and Facebook stay placeholders until they ship.~~ Email and Facebook screenshots added and pushed the same day (`portfolio-email-marketing.jpg`, `portfolio-facebook-ads.jpg`); all four frames are real now. The call-script line for the website build is still owed before ads point here. Second in the build order (brainstorm Q50).

- Theme: `editorial` (`../themes/editorial.json`). Skeleton: Style Guide 6.16.
- Campaign: `projects/google-ads/campaigns/02-website-build.md`. Research: `projects/google-ads/keywords/website-build-research.md` and `.csv`.
- Decisions behind it: `brainstorms/2026-09-25-google-ads-pages.md` Q16 to Q21; Jonathan's look: "The editorial style but the background being white so the rounded portfolio cards have a good contrast."

## Keyword group and the h1

- Ad groups: integrators; electricians; home services; contractors catch-all.
- h1 target term: pending the Planner run. Research candidates: "website design for contractors" (widest, agency results, all five trades on one page); "contractor website design company" (all-agency results, "company" is a buy word); "av integrator website design" (One Firefly the only entrenched name; may sit under 10 searches a month). Note from the research: "av company website design" means Antelope Valley to Google; never bid it.
- Draft h1 until then: "Contractor website design that books the job." (7 words).
- The trade-word swap in the h1 is the same open question as on `/google-ads/`.

## URL, CRM, tracking

- Final URL `https://monarcbuild.com/website-build/`, `noindex`, `mb-page-type` ad, `mb-theme` editorial.
- Sent state `?sent=1`; `book_appointment` with `page: 'website_build'` (already in the built page); the shared conversion label.
- CRM Landing pages row: Service Website, Status Draft.

## v1 blocks

| # | Block | Anchor | What is in it |
|---|---|---|---|
| 1 | Brand mark | | |
| 2 | Hero, split | `hero` | h1, sub, the brand line, "Book the page plan"; the shopfront render right |
| 3 | What you get | `services` | Four rounded cards on `#F4F4F2`, serif numerals 01 to 04, no icons |
| 4 | Proof: our work | `proof` | "Six pages, six styles": browser frames at 16:10 of the other five service pages, labeled placeholders until each ships |
| 5 | Works for, Not for | `fit` | Two columns, `#15803D` and `#B91C1C` |
| 6 | FAQ | `faq` | Three `<details>` |
| 7 | Final ask | `book` | h2, "Book your fifteen minutes", the micro-line |
| | Footer, pill, popup | | Pill on "Book the page plan"; black buttons, pill shape |

## Copy drafts (every line is Jonathan's to approve)

| Element | Draft | Words | Status |
|---|---|---|---|
| h1 | Contractor website design that books the job. | 7 | draft, pending the Planner term |
| Sub | One page per service and per area, a three field form above the fold, copy matched to the search. | 19 | draft |
| Brand line | Bring the brand you want. We bring the pages your site is missing. | 13 | draft (Jonathan's "Consult a designer about your brand vision") |
| Hero button | Book the page plan | 4 | approved (Q20) |
| Cards label, h2 | What you get / Four parts. One site that books. | 3 + 6 | draft |
| 01 | **One page per service.** Every service you sell gets its own page. Each page answers one search. That is the page Google sends that buyer to. | 26 | draft |
| 02 | **One page per area.** The towns you drive to, each with a page. Your jobs in that town go on it. That is what ranks there. | 26 | draft |
| 03 | **Three fields above the fold.** Short enough to fill on a phone. The form sits where the visitor lands. No scrolling to find it. | 24 | draft |
| 04 | **Copy matched to the search.** The headline says what they typed. A buyer sees their own words first. Fewer back buttons, more calls. | 23 | draft |
| Proof label, h2 | Our work / Six pages, six styles. | 2 + 4 | draft |
| Proof sub | Every service page on this site is its own design. Yours gets the same care. | 15 | draft |
| Frame captions | Google Ads · SEO · Email marketing · Facebook ads · AI automation | 9 | draft |
| Fit h2 | Built for a specific kind of shop. | 7 | from the live ad page |
| Works for | One page for everything today · Selling in more than one town · Twenty photos of real jobs · Owning the site outright | 20 | draft (asset email item 1) |
| Not for | A template by Friday · No photos and no time to shoot · Shopping on price alone · Locked to a builder you cannot leave | 22 | draft |
| FAQ h2 | Three questions before you book. | 5 | draft |
| FAQ 1 | What does it cost? The build is quoted on the call, once we know how many services and towns need pages. | 21 | draft |
| FAQ 2 | What happens on the call? Fifteen minutes. We pull your site, your searches, and where you show up. You leave with the page plan. | 24 | draft |
| FAQ 3 | What if it does not work? No one can promise leads. Once fees are paid, the site, the pages, and the data are yours. | 24 | draft |
| Final ask h2 | Your next high ticket job is searching now. | 8 | from the live ad page |
| Final button | Book your fifteen minutes | 4 | approved (Q20) |
| Micro-line | Fifteen minutes. Bring nothing. | 4 | approved |

About 330 visible words by hand, against 400.

## v2 candidates

The three proof job cards; the citations strip; "Kickoff to live in fourteen days"; About us; cards for the Business Profile and citations and for lead tagging.

## Images

- Hero: `../candidates/website-build/hero-1.jpg` to `hero-4.jpg`. **Picked 2026-09-26 by Jonathan: hero 4** (arched windows, a customer walking in the open door). Exported to `public_html/assets/generated/website-build/hero.jpg` (125 KB) and `hero-800.jpg`.
- Proof: screenshots of the sibling pages in browser frames once each is built, 16:10; labeled placeholders until then (Media 3 extension).

## Scrutiny checklist

- [ ] Message match; one action (two "Book the page plan", one "Book your fifteen minutes"); split hero at 1440, stacked at 390.
- [ ] Six blocks; `drift.py` clean under `editorial`; `readability.py` within Copy 7; visible words under 400.
- [ ] No accent anywhere but the fit block; black button with white text (18.9:1).
- [ ] Portfolio frames show only Monarc's own pages; placeholders labeled.
- [ ] Tracking and the four popup and sent states; privacy link.
- [ ] The website build is outside the Pilot Service Agreement: the call-script line exists before the push.

## Tile and render history

- 2026-09-25: tile rendered, `../renders/2026-09-25/tile-editorial-1440.png`. Contact sheet `../renders/2026-09-25/candidates-website-build.jpg`.

- 2026-09-26: **rebuilt in the editorial theme** (Jonathan's go), `python scripts/build_service_page.py website-build`. The house-style page is archived at `archives/site-website-build-house-2026-09-25/index.html`, which is now the source of the shared head, popup, and booking script. `drift.py` 0 findings under `editorial`; `readability.py` 0 findings, 381 visible words, popup 120. The portfolio shows four frames: a real screenshot of `/google-ads/` (cut from its approved render) and labeled placeholders for SEO, Email, and Facebook; AI automation is left out so the grid stays two by two, and joins when it ships. Renders in `../renders/2026-09-26/website-build-*.png`. Not pushed. Jonathan, the same day: "lets move to the next render"; no changes asked, no push go given.

## History: the house-style build (2026-09-25, never pushed)

Moved here from the Section Spec on 2026-09-25 when this spec was written. Jonathan, 2026-09-25: "Add a website build landing page as a LP." Built from the ad page's bones in the house theme, marked `mb-page-type` ad and `noindex`. Source: `projects/monarcbuild-site/public_html/website-build/index.html` (the rebuild replaces it; the old copy moves to `archives/` first).

| # | Block | Anchor id | Copy and source |
|---|---|---|---|
| 1 | Hero | `hero` | h1 "A contractor website that books the job." (7 words). Sub "One page per service and per area, a three field form above the fold, and copy matched to the search that brought them." Button "Book an appointment". The colonial house under the scrim (6.8). |
| 2 | On the call | `audit` | h2 "Fifteen minutes. You leave with the page plan." One line: the searches, where the site shows up, the pages it is missing. |
| 3 | National citations | `citations` | The logo banner template. |
| 4 | Proof | `proof` | Unchanged from the ad page (rule 6.7). |
| 5 | What you get | `services` | Label "What you get". h2 "Seven parts. One site built to convert." Seven flip cards: 01 One page per service; 02 One page per area; 03 Three field form above the fold; 04 Copy matched to the search; 05 Google Business Profile and citations; 06 Fast on a phone; 07 Every lead tagged. |
| 6 | Fit | `fit` | h2 unchanged. "For" rewritten for every trade, plus "Twenty photos of your best jobs, or a week to shoot them". |
| 7 | The build | `build` | h2 "Kickoff to live in fourteen days." Three lines: kickoff and asset list; pages, copy, form, tracking, Business Profile; live with Google Ads. |
| 8 | About us | `team` | Unchanged. |
| 9 | FAQ | `faq` | Cost; speed (fourteen days once the photos and the logo are in); ownership; takeover. |
| 10 | Final ask | `book` | Unchanged. |

Measured 2026-09-25 by `readability.py`: 1,112 words on the page, grade 3.3 whitelisted.
