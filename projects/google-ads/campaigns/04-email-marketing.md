# Campaign 04: Email marketing

## Status

Planned 2026-09-25. Second in the 30-day test rotation at $20 a day. Google campaign id: pending. Offer gate: email is not in the Pilot Service Agreement; call-script line pending Jonathan.

## Who is searching

A contractor owner with a stack of proposals that went quiet and a customer list nobody has emailed in a year. The moment: a slow month, a competitor's newsletter in their own inbox, or a quote they lost to silence.

## Page

Final URL `https://monarcbuild.com/email-marketing/`. Theme commercial (`projects/Landing Page Build/themes/commercial.json`); spec `projects/Landing Page Build/pages/email-marketing.md`. h1 draft "Email marketing for contractors with open proposals." Sent-state label `page: 'email_marketing'`. Media: the ball-on-the-lip render in the hero; the five-trade row as the walk-through; no proof numbers (none exist for email).

## Target term and ad groups

**Current (2026-09-28):** 12 keywords locked by Jonathan, picked on buying intent (`../keywords/method.md`), in one ad group, each keyword exact and phrase, plus the ad: `04-email-marketing.json`, the file the Ads screen publishes from. The table below is the earlier plan, kept for history.

Keyword list `../keywords/email-marketing.csv` (75 researched rows merged 2026-09-26); findings `../keywords/email-marketing-research.md`; paste files `../keywords/paste/email-marketing-*.txt`. The research's warnings: "email marketing contractor" means freelancer jobs, so "contractor" stays tied to "for"; quote-follow-up automation terms belong to software and are parked. The four cards are the four triggered sequences (existing base, after a lead submits, after the consultation, after the install), so terms about follow-up and past customers are the buy terms; software-seeker terms are parked or negative.

| Ad group | Theme | Top terms (to confirm) | Match | Page |
|---|---|---|---|---|
| Contractors | catch-all | email marketing for contractors; email marketing agency for home services; lead nurture for contractors | exact, phrase | `/email-marketing/` |
| Follow-up | by pain | quote follow up email automation; proposal follow up email contractor; past customer email campaign contractor | phrase | `/email-marketing/` |
| By trade | by trade | email marketing for electricians; email marketing for av companies; drip campaign for hvac company | phrase | `/email-marketing/` |

## Budget and bidding

$20 a day in the test slot; the bidding phases of `../review-cadence.md`. Target cost per booked call $200.

## Geo, schedule, device, audience signals

As campaign 01.

## Negatives

Every shared list in `../negatives/shared-lists.md` whose "Applies to" covers 04, plus `../negatives/email-marketing.md` (mail logins, list buying, cold email, texting, the research negatives, and routing to 01 to 03). Rebuilt 2026-09-28; `python scripts/ads_negative_check.py` proves none blocks a keyword.

## Ads

One RSA per ad group, drafted in Phase 6. No proof numbers. Outcome headlines from the four sequences ("Close the Open Proposals", "Your Past Clients, Emailed", "Every Lead Gets a Sequence"). CTAs pinned 3: "Close the Open Proposals", "Book the Call".

## Assets

As campaign 01.

## Tracking

Conversion label `AW-18358744393/9mMKCIaR1uEcEMnqkLJE`; GA4 `book_appointment` with `page: email_marketing`. Airtable rows pending.

## Numbers that decide

As campaign 01; rotation rule as campaign 03.

## Log

- 2026-09-25: brief created from the approved plan.
