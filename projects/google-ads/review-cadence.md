# Review cadence

Reviews go to `reports/YYYY-MM-DD.md`; the numbers are typed into the Airtable Campaigns row (Spend to date, Impressions, Clicks) and the top ten Keywords rows the same day. Friday is the standing day, matching the dial tally. The Google Ads API read replaces the typing when it lands (`references/channel-connections.md`).

| When | Check | Action |
|---|---|---|
| Day 3 | Ads approved (no disapproved or limited status); impressions above zero; average CPC against the cap; first search-terms read; the page loads on a phone in under 3 seconds; the conversion action shows Recording after any booking | Add negatives found in search terms. Change no bids. |
| Day 7 | Search-terms loop; CTR per ad group (under 3% on exact and phrase means the mirror is off); impression share lost to rank vs to budget; conversions against the test rows | Negatives; promote converting or clearly buy-now terms to exact; if rank loss is over 60%, raise the CPC cap 20% |
| Day 14 | Cost per booked per ad group; spend without a booking; the asset report | Pause an ad group at 3x target cost per booked with zero booked; the first bidding switch if 15 conversions exist; install thatrebeccarae `wasted-spend-finder` for this review (`references/github-skills-shortlist.md`) |
| Day 30 | Bidding switch per the brief; booking rate (clicks to booked) against 3%; show rate on booked against 60%; cost per booked against target; schedule and device data; geo thinness (under 5 impressions a day per ad group means widen to national and keep the metro lifts, Jonathan's call); the v2 decision per page (a block ships only if booking rate is under 1.5% with clean search terms, or the call keeps hearing the same question) | Switch bidding if the condition is met; trim the schedule; +20% budget if under target with budget loss over 20%; rewrite the weakest headlines from the asset report; rotate campaign 03 to the next line |
| Day 60 | Kill or keep per campaign | Kill: cost per booked over 3x target and under 3 booked. Keep: add the next trade ad groups; a test line that hit target earns its own campaign (the split becomes 01 $40, 02 $25, that line $20, test $15) |

## The search-terms loop (weekly)

Every term with a click gets one of three actions in `search-terms-log.md`: add as exact (booked, or clearly buy-now), leave, or negative (and which list). Terms that convert get their own Keywords row in Airtable so the lead links.

Since 2026-09-28 the list comes to the Ads screen in the CRM: the morning pull (`scripts/ads_pull.py`) lists the last 7 days of searches that cost money and are not blocked yet. Block pushes a negative to Google after `scripts/ads_negative_check.py` proves it blocks no keyword. A swap moves a keyword out for a bench term. The screen also shows spend, clicks, and conversions per campaign, so the Friday typing stops once a campaign is published.

## The numbers that decide

- Booking rate under 1.5% after 200 clicks: intent or h1 mismatch. Search terms first, then the h1.
- Keyword pause: 2x target cost per booked with zero booked, or CTR under 1% at 200 impressions.
- Ad group pause: 3x target with zero booked.
- Scale: under target for 14 days with budget loss over 20%: +20% daily budget.
- Target cost per booked $200, tolerated to $400 for the first 30 days. The math: a booked call closes about one pilot in eight (50% show, 25% close), so $200 a booked call is $1,600 a signed pilot against $6,000 of pilot revenue.

## Bidding phases (every campaign)

1. Maximize clicks with a max CPC cap ($12 to start; the Planner's top-of-page low range for the approved terms replaces it), 14 to 21 days, to buy search-term data cheaply.
2. Maximize conversions, no target, at 15 conversions in 30 days, or at day 30 if the search terms are clean and conversions are at least 8.
3. Target CPA at 30 conversions in 30 days, set at observed cost per booked times 1.1, never lower on day one. Broad match enters here, campaign 01 only.
