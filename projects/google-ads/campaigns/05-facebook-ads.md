# Campaign 05: Facebook ads

## Status

Planned 2026-09-25. Third in the 30-day test rotation at $20 a day. Google campaign id: pending. Offer gate: Meta ads are not in the Pilot Service Agreement; call-script line pending Jonathan. The service line is "Meta Ads"; the page and the ads say Facebook because that is what searchers type (the research confirms or corrects this).

## Who is searching

A contractor owner who has boosted a post or two, seen nothing, and wants someone to run it. The moment: a competitor's finished-job ad in their own feed, or a slow season they want to fill before it starts.

## Page

Final URL `https://monarcbuild.com/facebook-ads/`. Theme social (`projects/Landing Page Build/themes/social.json`); spec `projects/Landing Page Build/pages/facebook-ads.md`. h1 draft "Facebook and Instagram ads for contractors." Sent-state label `page: 'facebook_ads'`. Media: the billboard render in the hero; four small renders on the cards; the feed-post frame (labeled Preview, a real job photo, no counts) as the walk-through.

## Target term and ad groups

**Current (2026-09-28):** 12 keywords locked by Jonathan, picked on buying intent (`../keywords/method.md`), in one ad group, each keyword exact and phrase, plus the ad: `05-facebook-ads.json`, the file the Ads screen publishes from. The table below is the earlier plan, kept for history.

Keyword list `../keywords/facebook-ads.csv` (83 researched rows merged 2026-09-26); findings `../keywords/facebook-ads-research.md`; paste files `../keywords/paste/facebook-ads-*.txt`.

Naming verdict from the research (2026-09-26): say "Facebook ads". Across the nine seeds, 72 unique ranking pages: 44 titles say Facebook, 11 social media, 7 Meta (all agencies), 4 Instagram. No contractor forum thread found by searching "meta ads" or "instagram ads" is titled either way; a 2025 ContractorTalk thread is titled "Facebook ads". Agencies put Facebook in the title and call the product Meta on the page (Hook, Contractor Dynamics). So Facebook leads, Instagram comes second, "meta ads" runs as a small test group, and "social media" is parked (five of six such titles mean posting, not ads).

| Ad group | Theme | Top terms (to confirm) | Match | Page |
|---|---|---|---|---|
| Contractors | catch-all | facebook ads for contractors; facebook ads management for contractors; facebook ads agency for home services | exact, phrase | `/facebook-ads/` |
| By trade | by trade | facebook ads for roofing companies; facebook lead ads for hvac; instagram ads for electricians; facebook ads for home automation; facebook ads for smart home installers | phrase | `/facebook-ads/` |
| Instagram | channel | instagram ads for contractors | phrase | `/facebook-ads/` |
| Meta test | naming test | meta ads agency for contractors | phrase | `/facebook-ads/` |

Parked: social media ads for contractors, social media management for contractors (posting services, not ads).

## Budget and bidding

$20 a day in the test slot; the bidding phases of `../review-cadence.md`. Target cost per booked call $200. Note the head-term risk: "facebook ads agency" is national-agency territory; the trade terms carry this campaign. Prices the searcher has seen sit at both ends: $100 to $249 packages beside $3,000 a month from Hook and Contractor Dynamics. The channel doubt owners voice ("If you need the phone to ring right now today, Facebook is the wrong place") is why the page sells reaching the buyer before they search, not the phone ringing today.

## Geo, schedule, device, audience signals

As campaign 01.

## Negatives

Every shared list in `../negatives/shared-lists.md` whose "Applies to" covers 05, plus `../negatives/facebook-ads.md` (logins, Marketplace, groups and pages, boosting, followers, Meta's other products, posting plans, the research negatives, and routing to 01 to 04). Live on day one because how-to guides fill page one for every seed. Rebuilt 2026-09-28; `python scripts/ads_negative_check.py` proves none blocks a keyword.

## Ads

One RSA per ad group, drafted in Phase 6. No proof numbers (none exist for Meta). Outcome headlines ("Your Best Job on Their Feed", "Reach the Buyer Before They Search"). CTAs pinned 3: "Reach the Buyer First", "Book the Call". No Meta, Facebook, or Instagram logo in image assets.

## Assets

As campaign 01.

## Tracking

Conversion label `AW-18358744393/9mMKCIaR1uEcEMnqkLJE`; GA4 `book_appointment` with `page: facebook_ads`. Airtable rows pending.

## Numbers that decide

As campaign 01; rotation rule as campaign 03.

## Log

- 2026-09-25: brief created from the approved plan.
