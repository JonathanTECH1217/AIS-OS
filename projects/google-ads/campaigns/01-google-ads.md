# Campaign 01: Google Ads management

## Status

Planned 2026-09-25. Funded: $50 a day. Google campaign id: pending. Airtable Campaigns record: pending. Offer gate: the Pilot Service Agreement covers this service (`context/offer.md`), so the call needs no extra line.

## Who is searching

The owner of a contractor business (integrator, electrician, HVAC, roofing, plumbing) who runs Google Ads badly or has just been burned by an agency, typing the service plus their trade. The moment: a slow month, an agency report that shows spend and no jobs, or a competitor's ad above theirs.

## Page

Final URL `https://monarcbuild.com/google-ads/`. Theme google (`projects/Landing Page Build/themes/google.json`); spec `projects/Landing Page Build/pages/google-ads.md`. h1 draft "Google Ads management for contractors." (replaced by the Phase 1 target term). Sent-state label `page: 'google_ads'`. The block that differs from the other pages: the search bar under the sub cycling the five trades' buyer queries. Media: the angler render in the hero, the three camera photos on the proof cards (waterfront first).

## Target term and ad groups

**Current (2026-09-28):** 12 keywords locked by Jonathan, picked on buying intent (`../keywords/method.md`), in one ad group, each keyword exact and phrase, plus the ad: `01-google-ads.json`, the file the Ads screen publishes from. The table below is the earlier plan, kept for history.

Keyword list `../keywords/google-ads.csv` (seeds, the modifier matrix, and 80 researched rows merged 2026-09-26 by `python scripts/ads_keyword_matrix.py --merge`); findings `../keywords/google-ads-research.md`; Planner paste files `../keywords/paste/google-ads-*.txt`. The h1 target term is picked after Jonathan's Keyword Planner run; the research's three candidates are in `projects/Landing Page Build/pages/google-ads.md`. The research's warning: nobody ranks for the integrator phrasings, so expect them under 10 searches a month, and "lighting control leads" returns cable suppliers (a dead seed).

| Ad group | Theme | Top terms (to confirm against the Planner) | Match | Page |
|---|---|---|---|---|
| Integrators | by trade | google ads for av integrators; google ads for home automation companies; ppc for smart home installers; google ads for low voltage contractors | exact, phrase | `/google-ads/` |
| Electricians | by trade | google ads for electricians; google ads management for electrical contractors; ppc for electricians | exact, phrase | `/google-ads/` |
| Home services | by trade (HVAC, plumbing, roofing merged until volume splits them) | google ads for hvac companies; google ads for plumbers; ppc for roofing companies | exact, phrase | `/google-ads/` |
| Outcome | by outcome | more high ticket installs; lighting control leads; control4 dealer marketing; lutron dealer leads | phrase | `/google-ads/` |

A "compare" ad group (best google ads agency for contractors; google ads management pricing) opens once this campaign has 15 conversions.

## Budget and bidding

$50 a day. Phase 1 Maximize clicks with a $12 max CPC (the Planner's top-of-page low range for the approved terms replaces it), 14 to 21 days. Phase 2 Maximize conversions at 15 conversions in 30 days. Phase 3 Target CPA at 30 conversions in 30 days, set at observed cost per booked times 1.1. Broad match only in phase 3, this campaign only. Target cost per booked call $200, tolerated to $400 for 30 days.

## Geo, schedule, device, audience signals

`../geo-targets.txt` (213 locations), "Presence" only, +20% on DMV, DFW, Naples, Bay Area; AK, HI, PR excluded. All hours for 14 days, then trim. No device exclusions. Observation only: in-market "Advertising and Marketing Services", a custom segment from the approved keywords, site visitors 30 days.

## Negatives

Every shared list in `../negatives/shared-lists.md` whose "Applies to" covers 01, plus `../negatives/google-ads.md` (head terms as exact, Google's own products, the research negatives; no routing, because 01 takes the combined searches). Rebuilt 2026-09-28; `python scripts/ads_negative_check.py` proves none blocks a keyword. The search-terms loop adds more.

## Ads

One RSA per ad group, drafted in Phase 6 after the target term is set, checked by `scripts/ads_lint.py`. Worked example for the Integrators ad group, term `google ads for av integrators`, paths `Google-Ads` / `Integrators` (draft, Jonathan's to approve):

| # | Headline | Pin |
|---|---|---|
| 1 | Google Ads for AV Integrators | 1 |
| 2 | Google Ads for Home Automation | 1 |
| 3 | Google Ads for Integrators | 1 |
| 4 | More High Ticket Installs | |
| 5 | $2.5k in Ads. A $91k Install. | |
| 6 | Page 1 for Whole Home Audio | |
| 7 | Built by a Low Voltage Guy | |
| 8 | Book the Audit | 3 |
| 9 | Fifteen Minutes, Bring Nothing | 3 |
| 10 | Keywords Your Buyers Type | |
| 11 | Every Lead Tagged by Keyword | |
| 12 | Win the $47k Lighting Jobs | |
| 13 | You Own the Account and Data | |
| 14 | Monthly Report: Cost per Lead | |
| 15 | Control4 and Lutron Dealers | |

Descriptions: "Campaigns rebuilt around the searches your buyers type. Every lead tagged to its keyword." / "$2.5k in ads pulled a $91k Ketra great room. Fifteen minutes. You leave with the audit." / "Wired the rough-in, closed the six figure proposal, then ran the ads. Lutron certified." / "You own the account and the data. Monthly report: spend, leads by source, cost per lead."

Flags: headline 12 uses the $47k lighting-control median from the proposal dataset (allowed in ad copy, never the client name); headline 7 is hook 33 from the Facebook brainstorm, his to keep or cut.

## Assets

Sitelinks to the other service pages as each goes live (same-page anchors get disapproved). Callouts: Lutron certified; AIA presenter; You own the account; Monthly report by source; Every lead tagged; Fifteen minute call; Built in Annapolis; Runs nationwide. Structured snippets: "Service catalog" (Google Ads, Landing pages, Local SEO, Google Business Profile, Monthly reporting); "Types" with the trades that have live ad groups. Image assets from Jonathan's own photos only (not the penthouse listing photo). Business name and logo. No call asset until a number exists; no lead form asset.

## Tracking

Conversion label `AW-18358744393/9mMKCIaR1uEcEMnqkLJE` on `?sent=1`; GA4 `book_appointment` with `page: google_ads`. Airtable: Campaigns row (Platform id = the campaign id), Keywords rows for every approved term, Landing pages row for the URL. All pending until `../tracking-checklist.md` item 11.

## Numbers that decide

Booking rate floor 1.5% after 200 clicks; keyword pause at 2x target with zero booked or CTR under 1% at 200 impressions; ad group pause at 3x; scale at under target for 14 days with budget loss over 20%. Kill date: day 60 at over 3x target with under 3 booked.

## Log

- 2026-09-25: brief created from the approved plan. Seeds in the CSV; research running.
