# Channel connections checklist

Written 2026-09-23 when Jonathan asked "Is Google Analytics hooked up?" (no) and for one list of every wire each channel needs before its numbers are real in the CRM. Tick here as each lands; `connections.md` stays the registry, `references/attribution.md` holds the label rules.

Three kinds of wire:

- **Tag on the site.** A small script on every page that tells a platform "this person came, this person booked." Google Ads has one. Google Analytics, LinkedIn, and Meta do not.
- **Labels on the link.** The extra words on the end of an ad link (UTM labels) that name the channel, campaign, keyword, and ad. The ad page reads them and sends them into the CRM with the booking. The homepage form does not read them yet.
- **Rows in Airtable.** A campaign row whose Platform id matches the id the platform puts in the label, the source ticked Active, and spend, impressions, and clicks typed on the row until an API fills them.

## Google Analytics (GA4)

Not hooked up. Every page carries the Google Ads conversion tag only (`AW-18358744393`); no `G-` measurement id, no Tag Manager. Without it a click that leaves without booking is invisible to Monarc except inside the ad platform.

- [x] GA4 property created, measurement id `G-JQ977C0MY7` (Jonathan, 2026-09-23).
- [x] Config line next to the Google Ads tag on every page (AIOS, 2026-09-23). Pushed on Jonathan's go 2026-09-24, read back live on all eight pages.
- [x] `book_appointment` event on the sent state of the ad page, the homepage popup, and `/book/` (AIOS, 2026-09-23).
- [ ] Mark `book_appointment` as a key event: GA4, Admin, Events, toggle "Mark as key event" once the first one has fired. Jonathan.
- [ ] Link GA4 to the Google Ads account (Admin, Product links) so ad clicks and bookings show in both. Jonathan.
- [ ] Link Search Console to GA4 so free-search terms show. Jonathan (needs the Search Console item below).

## Google Ads

- [x] Conversion tag on every page; the booking fires it on the sent state, one label for the homepage popup and one for the ad page (2026-09-23).
- [ ] Final URL suffix at account level (Admin, Account settings, Tracking), one line: `utm_source=google&utm_medium=cpc&utm_campaign={campaignid}&utm_term={keyword}&utm_content={creative}`. Jonathan. (Corrected 2026-09-24 from a tracking template; `references/attribution.md`.)
- [ ] Auto-tagging on (Admin, Account settings, Auto-tagging, tick the box). Adds the click id to every ad link. Jonathan.
- [ ] One row per campaign in Airtable Campaigns with Platform id set to the campaign id from Google Ads; one row per keyword in Keywords, linked to its campaign. Jonathan or AIOS.
- [ ] The page the ads land on reads the labels. The ad page does; the homepage `/book` form does not yet (hidden fields plus the CRM post, AIOS, on Jonathan's go).
- [ ] Spend, impressions, clicks typed on each campaign row weekly until the Google Ads API is wired (below).
- [ ] Source "google-ads" ticked Active in Sources.
- [x] Privacy policy reachable from every page that takes a name, email, or phone (Google Ads destination rule). `/privacy/` live 2026-09-24 with footer links on the ad page, book, about, and the homepage.
- [x] One address per page: www and /index.html now 301 to the bare folder address with the labels kept (`.htaccess`, live 2026-09-24, read back). The old Higgsfield copy of the site was taken off its address 2026-09-24 (Jonathan: "unpublish the higgsfield copy"): the connector has no unpublish, so the AIOS renamed the site's subdomain to `monarc-build-old`, which kills `monarc-build.higgsfield.app` at once; the copy still exists at the new address for reference and can be deleted or unpublished in the Higgsfield dashboard.
- [ ] **Monarc's own campaigns (plan approved 2026-09-25, `projects/google-ads/`).** Before a dollar is spent, in this order: billing fixed (a payment was declined 2026-09-01); the existing conversion actions read and "Submit lead form (6)" made the one Primary action with "Page view (9)" Secondary or removed; the homepage page-view snippet removed or guarded; the suffix and auto-tagging above; GA4 linked with `book_appointment` imported as Secondary; a Manager account created; IP exclusions; `geo-targets.txt` (the 213-location seed) loaded with "Presence" only; the shared negative lists; one Campaigns row per campaign by id; a test click that lands in Airtable with the UTM string filled. The full list with dates: `projects/google-ads/tracking-checklist.md`.
- [ ] **Google Ads API: built 2026-09-28, waiting on Jonathan's login.** The Ads screen (`#/ads`) approves, publishes (paused), goes live, pauses, sets budgets, blocks searches, and swaps keywords. `scripts/ads_pull.py` reads the numbers back every morning. Google dropped the developer token and the manager-account requirement on 2026-09-09: all it needs is a Google Cloud project with Explorer access and a Desktop OAuth client (`references/google-ads-api.md`). The paragraph below is the 2026-09-24 plan, kept for history.
- [ ] **Google Ads API (asked 2026-09-24: "control ads through the CRM").** Two halves. Read: a script pulls spend, impressions, clicks, and conversions per campaign and keyword every morning into the Campaigns and Keywords rows, so the Channels page stops depending on typed numbers. Control: pause or enable a campaign and change a daily budget from the campaign table, each behind a confirm step and logged as an Activity. Needs from Jonathan: a Google Ads Manager account (the developer token lives there), the developer token with Basic access (Google reviews the application; test access is instant but only works on test accounts), and an OAuth client from the same Google account; token and client secret go in `secrets.env`, never in a tracked file. Build order: read first, control after a week of clean reads.

## LinkedIn Ads

- [x] Ad page reads the labels and holds them through the popup (2026-09-13, live 2026-09-23).
- [x] Booking posts the lead to the CRM with the labels, Source LinkedIn, campaign by id (`AIRTABLE_TOKEN` set 2026-09-23, 9:56 pm).
- [ ] Ad destination in Campaign Manager: `https://monarcbuild.com/av_marketing/?utm_source=linkedin&utm_medium=paid-social&utm_campaign={{CAMPAIGN_ID}}&utm_content={{CREATIVE_ID}}`. Replaces the old `utm_id={{AD_SET_ID}}` template, which is a Meta name LinkedIn does not fill. Test with one click from the ad preview and check the labels arrive filled, not as braces. Jonathan.
- [ ] One row in Campaigns with Platform id set to the LinkedIn campaign id. Jonathan or AIOS.
- [ ] Source "linkedin" ticked Active in Sources.
- [ ] Spend, impressions, clicks typed weekly from Campaign Manager.
- [x] Insight Tag on every page that takes data (LinkedIn's own tag, partner id 9685362). Jonathan placed it on the old pages on the server; the AIOS added the same snippet to the homepage and the ad page, pushed on his go 2026-09-24 and read back. The privacy page carries no LinkedIn tag.
- [ ] After the tag: a conversion in Campaign Manager keyed to the booked page state (`?sent=1` in the URL). Jonathan.

## Meta Ads

Plan 2026-10-03: `projects/meta-ads/README.md` (the campaign "Meta: builder search check", one Campaigns row, Planned). Nothing existed on Meta for Monarc Build as of 2026-10-03 (no Business Manager, ad account, Page, Instagram, or Pixel).

- [ ] Business Manager, ad account with a payment method, the Page "Monarc Build", a linked Instagram, the Pixel. Jonathan supplies the Pixel id and the ad account id.
- [ ] Pixel base code on every page: `python scripts/meta_pixel_update.py --pixel <id>` writes it into the mirror next to `journey.js` (the `fbclid` key was added to every popup 2026-10-03 by the same script). Pushed on his go with the journey and popup changes.
- [ ] Events on `/builder-check/` only: `CheckStarted` (custom) at the first tile, `Lead` at the result screen (the ad set's conversion event), `Schedule` on the booked state (`projects/meta-ads/check.md`).
- [ ] Ad link labels: `utm_source=facebook&utm_medium=paid-social&utm_campaign={{campaign.id}}&utm_content={{ad.id}}`. Meta fills the braces. Put the same campaign id in the campaign row's Platform id before the ad runs. Jonathan.
- [ ] The two privacy lines naming the Pixel (in the mirror 2026-10-03, with the journey lines, pending approval).
- [ ] A test booking on `/builder-check/` from a non-self address with the labels lands in Leads with Source meta-ads and the campaign linked; Events Manager's Test Events shows Lead and Schedule.
- [ ] Source "meta-ads" ticked Active the day the ad goes live; spend, impressions, clicks typed on the row each Friday until an API reads them.
- [ ] Round two only: upload `meta-customer-list-2026-09-24-integrators-strong.csv` as a customer list for the matched-list ad set (already on `tasks.md`). Jonathan.

## Cold call

- [x] The 22 a day on Today, one-tap dial log, company and deal carry Source "cold" (2026-09-15).
- [ ] Optional: a VoIP number so calls log themselves. Today the phone is not connected and each dial is tapped by hand.
- [ ] Optional: the statuses Jonathan set by hand in the "Call List" base under jonathan@monarcbuild.com. A read token from that account (`AIRTABLE_PAT_CALLLIST`) or share the base with the token's account.

## Email

- [x] Booking confirmation and one-hour reminder from the script (2026-09-23).
- [ ] Every link in an email Monarc sends carries `utm_source=email&utm_medium=email&utm_campaign=<drip name>`. AIOS, when a drip is written.
- [ ] Proton Bridge signed in so `/inbox` runs (signed out on 2026-09-14 and 2026-09-15).
- [ ] Inbox pass turns "New Monarc Build lead" emails from the homepage form into Leads rows (`/level-up` candidate). Until then homepage leads live only in Proton.

## Google organic (free search)

- [x] A lead with no labels counts as Google organic in the CRM (2026-09-15).
- [ ] Search Console property for monarcbuild.com verified in the jonathan@monarcbuild.com account. Gives the search terms, indexing, and the link into GA4. Jonathan.
- [ ] Homepage form posts to the CRM (same item as Google Ads and Email above).

## Referral, warm, rep, content

- [x] Picked by hand in the deal form. Nothing to wire.

## Shared by every web channel

- [x] Ad page `/av_marketing/` live with the calendar step, the labels, and the CRM post (2026-09-23).
- [ ] Booking script published as a new version so the CRM's Today can read the calendar (`agenda` action; `references/apps-script-booking.md`). No longer needed for Today since 2026-10-05: the CRM reads the calendar with the Monarc login.
- [ ] Booking script moved to the jonathan@monarcbuild.com account, so invites read as him (his step, same guide).
- [ ] Homepage `/book` form: hidden label fields and the CRM post (AIOS, on Jonathan's go).
- [ ] Google Analytics on every page (above).
