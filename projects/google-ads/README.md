# Monarc's own Google Ads

Started 2026-09-25 from the approved plan (`brainstorms/2026-09-25-google-ads-campaign.md` and `brainstorms/2026-09-25-google-ads-pages.md` hold the interviews behind it). This folder is Monarc buying leads for itself. Client campaigns live in `projects/clients/<slug>/`.

Six search campaigns, one landing page each, every page booking the same 15-minute call:

| # | Campaign | Page | Theme | Status |
|---|---|---|---|---|
| 01 | Google Ads management | `/google-ads/` | google | **Live 2026-09-26** (read back); round 2 (new h1, colored Google letters, salmon hero, phone centering) pushed the same day; no ads until the tracking checklist is done |
| 02 | Website build | `/website-build/` | editorial | **Live 2026-09-26** (read back); portfolio frames show the Google Ads and SEO pages |
| 03 | SEO | `/seo/` | saas | **Live 2026-09-26** (read back), the lasso hero; first 30-day test slot; call-script line still owed before ads point here |
| 04 | Email marketing | `/email-marketing/` | commercial | **Live 2026-09-26** (read back); test slot; call-script line owed before ads |
| 05 | Facebook ads | `/facebook-ads/` | social | Research done 2026-09-26 (say "Facebook ads"; Instagram second; Meta a small test); **live 2026-09-26** (read back); test slot; call-script line owed before ads |
| 06 | AI automation | `/ai-automation/` | time | Research done 2026-09-26 (ad groups revised: back office, follow-up, by trade; software-owned seeds parked); **live 2026-09-26** (read back); test slot; tools unnamed; call-script line owed before ads |

Where each step stands (2026-09-26): keyword lists merged with the web research in `keywords/<service>.csv`; Planner paste files in `keywords/paste/`; page specs in `projects/Landing Page Build/pages/`; tiles in `projects/Landing Page Build/renders/2026-09-25/`; all six pages live and listed in the site's Services menu; nothing is spending.

## Publish from the CRM (Jonathan, 2026-09-28)

The Google Ads channel page in the CRM (Channels, the Google Ads card, `#/channel/google-ads`) is where campaigns go out. It was a separate Ads screen (`#/ads`) until 2026-09-29, when it folded into the channel page; "the Ads screen" in older notes means these controls, which now open inside each campaign's row. Each campaign has one file, `campaigns/NN-<service>.json`. On that page each campaign row shows five numbers (impressions, clicks, bookings, CPL, conversion rate) and opens into two cards, the ad and a copy of its landing page (2026-09-29). Per campaign, in the ad's card, Jonathan gives four approvals, and can take any of them back:
- **Spend:** budget, bidding, and where it runs.
- **Keywords:** 12 to start, picked on buying intent (`keywords/method.md`); his to change after that.
- **Negatives:** `negatives/shared-lists.md` plus `negatives/<service>.md`, approved by list.
- **The ad:** checked by `scripts/ads_lint.py`.

Any edit clears the approval it touches. The ad can be edited in place (2026-09-29): an X on a headline or description takes it out (it goes to `ad_bench` in the campaign file, shown as "Taken out", and can be put back), a slot badge cycles any slot, 1, 2, 3, a line can be dragged to a new place, a box adds his own, and (2026-10-02, Jonathan: "I should be able to edit my descriptions as well") a click on any headline or description turns it into a box to change its words (Enter keeps it, Escape drops it; the old wording joins "Taken out" when the set is saved). Edits collect on the screen and go to the file in one Save changes (`ads_publish.set_ad_lines`), which checks the whole set: length (30 and 90 characters), the copy rules in `ads_lint.py`, no line twice, and Google's 3 to 15 headlines and 2 to 4 descriptions. The ads were built at 15 headlines, so adding one to a full ad means taking one out first.

The keywords work the same way (Jonathan, 2026-10-01: "I should be able to delete and add keywords to the google ads campaigns as well"): an X takes one out (it joins the campaign's `bench`, shown as "Taken out", and can be put back), a box adds his own, and one Save changes sends the list to the file (`ads_publish.set_keywords`). Each keyword goes in exact and phrase. The save is refused outright for: no keywords, more than 50, one over 80 characters or 10 words, a character Google refuses, or any negative that blocks a keyword, since a blocked keyword never shows (example: on campaign 07 the Routing list blocks "google ads", which belongs to campaign 01). A new keyword that misses the buying-intent test (it must name a trade and this campaign's service, with no learner or bargain words) is not refused: the screen names the reason and offers **Save anyway**, because the keywords are his call. A saved change needs the keywords approved again; on a published campaign, Publish changes adds the new ones in Google and removes the ones taken out.

**Publish** builds the campaign in Google Ads **paused**. Google rehearses every step first; publishing again sends only what changed. **Go live** stays locked until the five gates below are done (the screen reads them, and can fix the two account switches). It is also held to $100 a day in total, with one test-slot campaign at a time.

Every change is logged in `ads-log.jsonl` and as an Airtable Activity. After a publish, the Campaigns row and the Keywords rows are written for attribution. Each morning after 6 am, `scripts/ads_pull.py` brings back spend, clicks, conversions, and the searches that cost money; the screen lists the searches with a Block button.

- **Command line:** `python scripts/ads_publish.py status | plan 01 | publish 01 --validate-only`.
- **Checks:** `python scripts/ads_negative_check.py` must say OK.
- **Setup:** `references/google-ads-api.md`. It needs a Google Cloud project with Explorer access and a Desktop OAuth client. There is no developer token and no manager account since 2026-09-09.

## The decisions (Jonathan, 2026-09-25)

Audience all five trades; $3,000 a month (two funded campaigns plus one rotating test); the 213-location metro seed, "Presence" only; AIOS drafts keywords and Jonathan validates in Keyword Planner; every page funnels to the same call and the service is scoped there; grade 8 reading level with brand names exempt; each page in its own theme with the spacing rules unchanged; a 3D cartoonish hero render per page; all six style tiles approved before any page is built. The full plan, phases, and the page-by-page settled table: `projects/Landing Page Build/Section Spec.md` (service pages) and the plan file named in the brainstorm captures.

## Writing a new ad (Jonathan, 2026-10-01)

A rule for every ad written from here on. The ads already built stay as they are until he edits them.

- **Headline slots:** slot 1 is the callout to the person (who it is for: "Marketing for AV Integrators"); slot 2 is the outcome they want (what they get); slot 3 is the call to action (what to do: "Book the Audit"). Each headline written for a slot is pinned to it.
- **Descriptions:** sixth-grade words, short sentences, and each one matches an outcome the campaign promises (its brief's "Outcomes we want"). `ads_lint.py` reports each description's grade and flags any above 6. Brand names and trade terms count as easy words.

## Five gates before a dollar is spent

1. Billing works on the Ads account (a payment was declined 2026-09-01).
2. One Primary conversion action; the homepage page-view label retired.
3. Final URL suffix and auto-tagging on.
4. Each page's h1 mirrors its ad group's target term.
5. A test booking reached Airtable with the UTM string filled.

Ticked in `tracking-checklist.md`; the launch gate in `launch-checklist.md`.

## Files

- `account.md`: customer id, admins, billing owner, MCC status, the settings that must hold.
- `tracking-checklist.md` and `launch-checklist.md`: tickable, dated as each item lands.
- `review-cadence.md`: day 3, 7, 14, 30, 60 checks; the pause and scale numbers; the search-terms loop.
- `search-terms-log.md`: one dated table.
- `geo-targets.txt`: the 213 locations, written by `scripts/ads_geo_export.py`.
- `negatives/shared-lists.md`: the account-level lists.
- `keywords/`: `method.md`, one CSV per service line, Jonathan's raw Planner exports under `keyword-planner/`, SERP screenshots under `serps/`.
- `campaigns/`: one brief per campaign, RSAs inside.
- `reports/`: the dated reviews; numbers typed into Airtable the same day.

## CRM view (to build, Jonathan 2026-09-26)

A Website card in the CRM opens to one card per landing page. Each card shows impressions, clicks, average time on page, and the campaign's spend, each against the previous period. Time on page comes from GA4 by page path. Impressions, clicks, and spend come from Google Ads: the typed Friday numbers first, then the API. The task and its order are in `tasks.md`, Google Ads section.

## How the loop runs

Friday is the standing day, matching the dial tally: search terms read, negatives added, spend and clicks typed into the Airtable Campaigns and Keywords rows, the report written. The Google Ads API read (`references/channel-connections.md`) replaces the typing when it lands.
