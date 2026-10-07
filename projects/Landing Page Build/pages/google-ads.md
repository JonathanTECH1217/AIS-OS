# Page spec: /google-ads/ (Managed Google Ads)

Status: **live 2026-09-26**; round 2 (the new h1, the colored Google letters, the salmon hero, centered on phones) **pushed the same day** on Jonathan's go and read back. The yellow letter stays `#FBBC04`. First in the build order (brainstorm Q50).

- Theme: `google` (`../themes/google.json`; Style Guide section 8). Skeleton: Style Guide 6.16.
- Campaign: `projects/google-ads/campaigns/01-google-ads.md`. Keyword research: `projects/google-ads/keywords/google-ads-research.md` and `.csv`.
- Decisions behind it: `brainstorms/2026-09-25-google-ads-pages.md` Q1 to Q15.

## Keyword group and the h1

- Ad groups: integrators; electricians; home services (HVAC, plumbing, roofing merged); outcome.
- h1 target term: pending Jonathan's Keyword Planner run (method step 4). Research candidates, each 6 words: "Google Ads for Home Automation Companies" (the exact seed, one generic agency on it); "Google Ads Management for AV Integrators" (One Firefly says "SEM", which leaves this phrasing open); "Google Ads for Low Voltage Contractors" (how the ICP names itself; the results bleed to electricians).
- h1 (Jonathan, 2026-09-26): "Managed Google Ads for contractors." (5 words; his words from the brief, "Managed Google Ads"). Supersedes the draft "Google Ads management for contractors." The Planner run can still move the trade word, not the "Managed Google Ads" lead.
- Open, recommended: one page serves three trade ad groups, so one h1 cannot mirror all of them. Each ad group's final URL carries a trade word (`/google-ads/?t=electricians`) and the page swaps it into the h1 from a fixed list of five trade words, falling back to "contractors". Nothing else on the page changes. Jonathan's call before the build.

## URL, CRM, tracking

- Final URL `https://monarcbuild.com/google-ads/`, `noindex`, `mb-page-type` ad, `mb-theme` google, `<html data-theme="google">`.
- Sent state `?sent=1`; `book_appointment` with `page: 'google_ads'`; conversion `AW-18358744393/9mMKCIaR1uEcEMnqkLJE`.
- Hidden fields: the five UTMs, `gclid`, `landing_url`, `referrer`, `page`. `_next` back to `/google-ads/?sent=1`.
- CRM Landing pages row: URL above, Service Google Ads, Status Draft until the push.

## v1 blocks (Style Guide 6.16)

| # | Block | Anchor | What is in it |
|---|---|---|---|
| 1 | Brand mark | | Monarc Build, the theme's ink |
| 2 | Hero, split | `hero` | h1, sub, the search bar cycling five buyer searches, "Book the audit"; the angler render right |
| 3 | What you get | `services` | Four static Material cards (search, web, sell, analytics icons in the four colors) |
| 4 | Proof | `proof` | Three static Material cards on the grey band, waterfront first |
| 5 | Works for, Not for | `fit` | Two columns, Google green and red on the 24px headings and marks only |
| 6 | FAQ | `faq` | Three `<details>`, the first open |
| 7 | Final ask | `book` | h2, "Book your fifteen minutes", the micro-line |
| | Footer, pill, popup | | Pill on "Book the audit"; popup and sent state in the theme |

## Copy drafts (every line is Jonathan's to approve)

| Element | Draft | Words | Status |
|---|---|---|---|
| h1 | Managed Google Ads for contractors. ("Google" in the four colors, letter by letter) | 5 | Jonathan's, 2026-09-26 |
| Sub | More exposure across every service you sell. One page per search, every lead tagged to the keyword that paid. | 19 | draft (Jonathan's "Increase exposure across your core offerings") |
| Search bar | lighting control installer near me / standby generator installer / slate roof repair / ductless mini split installer / tankless water heater install | 4 to 5 each | draft |
| Hero button | Book the audit | 3 | approved (Q14) |
| Cards label, h2 | What you get / Four parts. One account you own. | 3 + 6 | draft |
| Card 1 | **Campaigns built on buyer searches.** Rebuilt around the searches your buyers type. Broad terms and wasted clicks come out first. Budget goes where jobs come from. | 26 | draft (offer bullet 1) |
| Card 2 | **One page per keyword group.** Each ad lands on a page written for its search. The headline says what they typed. Three fields, above the fold. | 26 | draft (offer bullets 2 and 3) |
| Card 3 | **Every lead tagged.** Each form fill and booking carries its keyword and campaign. You see which search brought which job. Spend follows what books. | 24 | draft (offer bullet 4) |
| Card 4 | **A monthly report you can read.** Spend, leads by source, and cost per lead. Plus whether budget or ad rank is the limit. | 23 | draft (offer bullets 5 and 6) |
| Proof label, h2 | Proof / $2.5k in ads. A $91k great room. | 1 + 7 | draft |
| Proof sub | The waterfront came from $2.5k of ads. The Georgian came from a page that ranked first. | 16 | draft (`context/about-business.md`) |
| Proof card 1 | $91k · Waterfront great room · $2.5k of Google Ads on lighting control searches pulled the lead. | 15 | from the live ad page card |
| Proof card 2 | $51k · Baltimore penthouse · Control4 and Lutron retrofit. From the same ranked page and ad account. | 15 | from the live ad page card |
| Proof card 3 | $69k · Georgian Colonial restoration · Whole home audio. The contractor found the #1 page for whole home audio in Annapolis. | 19 | from the live ad page card |
| Fit h2 | Built for a specific kind of shop. | 7 | from the live ad page |
| Works for | Owners who want their own account · A service area where buyers search · Installs, not only service calls · Someone to call every lead back | 23 | draft |
| Not for | A promised number of leads · No budget for ad spend · Leads nobody calls back · Repair calls as the whole business | 20 | draft |
| FAQ h2 | Three questions before you book. | 5 | draft |
| FAQ 1 | What does it cost? Management is quoted on the call, after we see your account. Ad spend is yours, paid to Google. | 22 | draft (no figure, Copy 4) |
| FAQ 2 | What happens on the call? Fifteen minutes. We pull your search terms, your ad account, and your pages first. You leave with the audit. | 24 | draft |
| FAQ 3 | What if it does not work? No one can promise leads. Once fees are paid, the account, the pages, and the data are yours. | 24 | draft (`context/offer.md` ownership clause) |
| Final ask h2 | Your next high ticket job is searching now. | 8 | from the live ad page |
| Final button | Book your fifteen minutes | 4 | approved (Q14) |
| Micro-line | Fifteen minutes. Bring nothing. | 4 | approved (Q1 skeleton) |

Visible words outside the popup, counted by hand: about 360 against the 400 budget. `readability.py` gives the real count on the build.

## v2 candidates (only when day 30 asks)

The searches ticker; the pin map of the metro seed; the math block; About us; cards five and six (impression share, the three-field form on its own).

## Images

- Hero: four candidates in `../candidates/google-ads/hero-1.jpg` to `hero-4.jpg` (prompt in `../candidates/jobs-2026-09-25.json`). **Picked 2026-09-26 by Jonathan: hero 2** (the river through the middle, the angler in the red cap mid-cast). Exported to `public_html/assets/generated/google-ads/hero.jpg` (102 KB) and `hero-800.jpg`.
- Hero, round 2 (Jonathan, 2026-09-26: "Fix the fishing line naturally fall into the water and have a salmon jumping out of the water"): four image edits of hero 2, `../candidates/google-ads/hero-5.jpg` to `hero-8.jpg` (`../candidates/jobs-2026-09-26c.json`, 8 credits, came back as nano_banana_2). Side by side: `../renders/2026-09-26/candidates-google-ads-salmon.jpg`. **AIOS pick: hero 8** (one arch from the rod tip, the fly on the water with rings, the salmon jumping past it). In all four the line still rises before it lands; a flatter line is one more edit round. Exported over `hero.jpg` and `hero-800.jpg`; the hero 2 files are in the live copy until the push. Alt: "Illustration: a fly fisherman on a grassy riverbank, his line resting on the river and a salmon jumping beyond it".
- Proof cards: camera photos only. Waterfront `assets/projects/waterfront-great-room.jpg` (center 38%); penthouse `assets/projects/baltimore-penthouse.jpg`; Georgian `assets/georgian/rough-in-01.jpg` (center 20%, the PHA shirt out of frame). Compressed copies before the build.
- No Google wordmark anywhere. The Google Ads product logo only inside card 1 if Jonathan wants it ("we run this"); the draft has none.
- **Exception (Jonathan, 2026-09-26):** the word "Google" in the h1 is set letter by letter in the four colors (blue, red, yellow, blue, green, red), Roboto, not the Google logo face. `.g-word` spans in the body, colors in `site.css` under `html[data-theme="google"]`. Style Guide Media 7, dated exception. Yellow `#FBBC04` measures 1.71:1 on white and fails the 3:1 heading floor; the question is in the Style Guide note.

## Scrutiny checklist (run before the render goes to Jonathan)

- [ ] Message match: the keyword's noun in the h1; the outcome in the sub; nothing above the fold names a service this page does not sell.
- [ ] One action: two "Book the audit", one "Book your fifteen minutes", mailto, `/privacy/`, the calendar fallback; nothing else.
- [ ] Split hero at 1440, stacked at 390 with the hero button inside the first 844px.
- [ ] Six blocks, nothing from the v2 list.
- [ ] `drift.py` clean under `google`; `readability.py` within Copy 7; visible words under 400.
- [ ] Renders labeled as illustrations; camera photos on proof only; hero file at or under 300 KB; alt on every image.
- [ ] Fit colors on the 24px headings and marks only (`#34A853` passes at 3.06:1, `#EA4335` at 3.92:1).
- [ ] Tracking head and hidden fields as above; `?step=4`, `?step=5`, `?sent=1`, `?sent=1&at=<ISO>&booked=1` render in the theme.
- [ ] Privacy link; business name and contact in the footer; no third-party mark as the brand.
- [ ] Every card is an offer bullet (`context/offer.md`).

## Tile and render history

- 2026-09-25: tile rendered, `../renders/2026-09-25/tile-google-1440.png`, with the four hero candidates. Contact sheet `../renders/2026-09-25/candidates-google-ads.jpg`. Waiting on the pick.

- 2026-09-26: **page built** (Jonathan's go), `projects/monarcbuild-site/public_html/google-ads/index.html`, assembled by `python scripts/build_service_page.py google-ads` from `build/google-ads.body.html`, `build/service-page.css`, and the tracking head, popup, and booking script of `/website-build/`. `drift.py` 0 findings under `google`; `readability.py` 0 findings, 399 visible words (budget 400), popup 119. Renders in `../renders/2026-09-26/`: `google-ads-1440.png`, `google-ads-390.png`, the folds at 1440x900 and 390x844, `google-ads-step4-390.png`, `google-ads-sent-1440.png`. Fixed on the first render: the search bar forced the hero wider than a phone (`site.css`, `min-width:0` on the hero column). Not pushed. **Render approved by Jonathan 2026-09-26** ("I approve the ads management render"); the push waits on his go. The trade-word swap in the h1 is not built (undecided).

- 2026-09-26: **pushed live** on Jonathan's go ("push the google ads page"); read back 200, `noindex`, labels 2 and 1, the conversion guard.

- 2026-09-26, round 2 (Jonathan): "Mobile headers and copy and the CTA should be centered. And make the google letters in the google colors. Fix the fishing line naturally fall into the water and have a salmon jumping out of the water." and "Have it be managed google ads". Built:
  - Phones (under 768px): the hero text, the search bar, the hero button, every section head, the sent state, the final ask, and the SEO page's "Page 1" row centered (`build/service-page.css`, so every service page gets it). Cards, proof captions, fit lists, and FAQ answers stay left: short centered lines are fine, centered lists and paragraphs are hard to read.
  - h1 "Managed Google Ads for contractors." with the colored letters (above); title and description in `scripts/build_service_page.py` to match.
  - Hero 8 (above).
  - `readability.py` now keeps a heading with spans in it as one line (the six colored letters had counted as six words).
  - `drift.py` 0 findings under `google`; `readability.py` 0 findings, 399 visible words, popup 119, h1 5 words.
  - Renders: `../renders/2026-09-26/google-ads-1440.png`, `google-ads-fold-1440.png`, `google-ads-390.png`, `google-ads-fold-390.png`.
  - Not pushed. Files for the push: `google-ads/index.html`, `assets/site.css`, `assets/generated/google-ads/hero.jpg`, `hero-800.jpg`.

- 2026-09-27: the job figures came off (Jonathan: "remove the figures and keep scope"; Style Guide Copy 4). Proof h2 now "One ad account. A waterfront great room." (was "$2.5k in ads. A $91k great room."); sub "The waterfront came from Google Ads. The Georgian came from a page that ranked first."; the three cards carry no figure, the waterfront line reads "Lutron Ketra lighting. Google Ads on lighting control searches pulled the lead." The butterfly lockup replaced the text mark the same weekend. **Pushed 2026-09-27** on Jonathan's "push the updates" with the "Other services" row above the footer (405 visible words, 5 over the 6.16 budget), read back.

- 2026-09-27: the four Google-colored dots before each of the six section labels came off (Jonathan: "the few color icons should go from my page", then his pick); the labels are plain tracked caps (`themes/google.json`). The colored Google letters and the card icons stay. drift 0, readability 0. Renders `../renders/2026-09-27/google-ads-nodots-*.png`. **Pushed the same day**, read back identical.

## Open items

- ~~The round 2 push (Jonathan's go).~~ Pushed 2026-09-26.
- The ad drafts in `projects/google-ads/campaigns/01-google-ads.md` still carry "$2.5k in Ads. A $91k Install." (headline 5) and "$2.5k in ads pulled a $91k Ketra great room." (description 2); the page no longer shows either figure, so the ad would claim what the page does not.
- The yellow letter: keep `#FBBC04` or darken (Style Guide Media 7 note).
- The trade-word swap (above).
- The `/website-build/` portfolio screenshot of this page is the old hero; retake it after the round 2 push.
