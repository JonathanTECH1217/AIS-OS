# Free campaign for a review

Campaign "Free campaign for a review" (Airtable Campaigns, channel `cold`, Platform id `free-campaign`). Planned 2026-10-03 from a 13-question interview (`brainstorms/2026-10-03-free-campaign-for-reviews.md`). Status: Planned until the first delivery goes out.

## The idea, in one line

On a second call window, Jonathan offers a prospect a free search check of their area and a free Google Ads campaign they load themselves, says plainly that he will ask for a Google review after, and then tries to sell the retainer. The AIOS builds the whole thing from the domain, phone, and city on the call list. Cost per company about $0.10; his time per delivery none.

## The funnel

1. **The call.** The dial hour keeps the meeting ask (Trade Call List). The second window runs this script: `references/free-campaign-call-script.md`. Calls are logged in the Prospects base, table "Free campaign calls" (pick the company, type the outcome in Status (typed) as on Contacts, the email in Email). A yes ("yes", "send it", "build it") is the trigger.
2. **The build.** `python scripts/free_campaign.py queue` builds every yes with no folder yet (or `build --mb MB-00258` for one). Folder `projects/free-campaign/<MB-ID>-<domain>/`: `audit.pdf` (the three searches and who shows up on the real Google page, their reviews against the market, the page the campaign lands on and its three fixes, what is in the file), `ads-editor.csv` (one paused Search campaign, one ad group, 12 keywords in exact and phrase, the negatives, three responsive search ads, the budget line, their own page as the final URL), `campaign.json`, `data.json`, the raw replies, and the two email drafts as text.
3. **The delivery.** `deliver --mb MB-00258` drafts the delivery email in Jonathan's copy into Proton Drafts with the PDF and the CSV attached (`templates/free-campaign-delivery-email.md`). He sends it from Proton. The first three need the row's Stage set to Approved in the CRM; after that Built suffices. `readback` reads the Sent folder and moves the row to Delivered, with the ask due two days on.
4. **The review ask.** `asks` drafts the review-ask email (`templates/free-campaign-review-ask.md`) for every delivery two days old, oldest first, three a day, only once `config.json` carries the review link and the Google Business Profile listing is Live. Jonathan sends; `readback` moves the row to Ask sent; he ticks Review left in the CRM.
5. **The retainer.** Said on the call and once more in the delivery email's last line. Nothing else is sold in writing.

The review is asked after delivery and never as the price of the free thing. The free thing is theirs whether they review or not.

## Data, and what each costs

| Step | Source | Cost |
|---|---|---|
| The site | `projects/outreach/site-cache-*.jsonl` (the 2026-09-13 reads cover the integrators), else one fetch | $0; an Opus read ($0.02) only for an integrator with no cached read |
| Their Google listing and the market top 20 | `places-cache-*.jsonl` by domain, else Google Places Text Search | $0.035 a query |
| The real results page, three searches, by city | DataForSEO `serp/google/organic/live/advanced` (`scripts/dataforseo.py`) | $0.002 a page |
| Bids for the budget line | DataForSEO `search_volume/live`, one call | $0.09 |
| Owner name and email | the Contacts row, else `contact-cache-*.jsonl`, else a crawl | $0 |

Without the DataForSEO keys the audit falls back to the map results from Places and says so on the page (`--no-serp` forces it). A dry run (`--dry-run`) touches nothing and prints the estimate and which keys are present.

## Rules the build follows

- Every sentence in the audit comes from data: the live page, their listing, their site. `check --mb` asserts every number in the audit is in `data.json`.
- One service, one city. Integrators: the first offering the Opus read found, in the order theater, automation, lighting, shades, audio, networking. Other trades: the service the site names most.
- Keywords by `projects/google-ads/keywords/method.md`: a buyer's words, the city, "near me", a brand-dealer term when the brand is on their site; nothing with how, best, cost, free, diy.
- Negatives: the shared lists that fit a homeowner-facing campaign (Jobs and careers, Learn and do it yourself, Lead buyers, Labor shoppers, Wrong country or language, Account and support) plus `negatives/<trade>.md`; a term that blocks one of the 12 keywords is dropped for that campaign and named in `data.json`.
- Ads by the slot rule (`projects/google-ads/README.md`, Writing a new ad): slot 1 the callout, slot 2 the outcome, slot 3 the call to action; sixth-grade descriptions (`ads_lint.py`); a star rating only when their listing shows 4.5 or more on 10 or more reviews.
- Budget: the median top-of-page bid times three clicks a day, rounded up to $5, $10 floor. Jonathan's rule to confirm.
- No person's name on the audit. "Monarc Build" in the footer. No PHA. No em dashes.

## The CRM

- Campaign row "Free campaign for a review" on the Cold call channel: dials, connects, and the yes rate from the second window's table (Config `call_sheets`), and the deliveries and reviews from the Monarc CRM table "Free campaigns" (one row per company: Built, Approved, Delivery drafted, Delivered, Ask drafted, Ask sent, Review left, Declined). Click a row to set its stage.
- The Today panel shows his boxes from `tasks.md`.

## Not verified yet

Google Ads Editor's import headers for responsive search ads and negatives (export campaign 07 from Editor and match the header row); the DataForSEO city codes for small towns (the script falls back to the listing's coordinates, then prints a warning); Edge's `--print-to-pdf` flags were checked on this laptop 2026-10-03.
