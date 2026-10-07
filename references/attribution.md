# Attribution: how a lead carries its source, campaign, keyword, and page

Written 2026-09-15 when the CRM got its Home of channel cards. The fifth CRM job in Jonathan's words: source on every lead, revenue by source on every report, so "we spent $2,000" becomes "that keyword produced that job."

## Yes, UTMs are required

Without them a form fill says only "someone filled the form." With them it says which channel, which campaign, which keyword, which ad, which page. Every paid link and every link Monarc controls carries these five parameters plus the platform click id:

| Parameter | Google Ads | Meta Ads | LinkedIn | Email | Organic |
|---|---|---|---|---|---|
| `utm_source` | `google` | `facebook` or `instagram` | `linkedin` | `email` | none (referrer) |
| `utm_medium` | `cpc` | `paid-social` | `paid-social` | `email` | `organic` |
| `utm_campaign` | `{campaignid}` | `{{campaign.id}}`, the campaign id (corrected 2026-10-03; was "ad set id", which clashed with `channel-connections.md` and with Platform id) | `{{AD_SET_ID}}` (already on /avmarketing) | campaign slug | none |
| `utm_term` | `{keyword}` | none | none | none | none |
| `utm_content` | `{creative}` | ad id | creative id | link name | none |
| click id | `gclid={gclid}` | `fbclid` (auto) | none | none | none |

**Google Ads final URL suffix** (account level: Admin, Account settings, Tracking, "Final URL suffix"), one line:

```
utm_source=google&utm_medium=cpc&utm_campaign={campaignid}&utm_term={keyword}&utm_content={creative}
```

Google fills the braces per click and adds the line to every ad's address. `{campaignid}` is what the Campaigns table stores in `Platform id`, so a lead matches its campaign row without typing. `{keyword}` matches the Keywords table. The page URL matches Landing pages. The click id (`gclid`) comes from auto-tagging (Admin, Account settings, Auto-tagging, tick the box), not from the suffix; `{gclid}` is not a value Google fills. Corrected 2026-09-24: the earlier note called for a tracking template with `{lpurl}`; the suffix does the same job with less to break, since the template is meant for click-tracking redirects.

## What the page does

Every landing page form reads the query string into hidden fields on load and posts them with the lead. `/av_marketing/` already does this for the LinkedIn parameters (Section Spec, Tracking). The homepage `/book` form does not yet; that is a one-line addition per field. The form email then carries `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `gclid`, and the page path.

## What the CRM does with it

`Leads` table: Name, When, Email, Phone, Status (New, Called, Qualified, Booked, Sold, Dead), First call at, UTM (the raw query string), gclid, Message, and links to Company, Source, Campaign, Keyword, Landing page, Deal. `External id` = the form email's Message-ID, so the inbox pass never creates a lead twice.

When a lead is saved with a UTM string the server:
1. Sets Source from `utm_source` and `utm_medium` (google + cpc = Google Ads; facebook or instagram = Meta Ads; linkedin = LinkedIn; email = Email; organic or empty with a monarcbuild.com referrer = Google Organic).
2. Matches Campaign by `Platform id` = `utm_campaign`, then by name.
3. Matches Keyword by `utm_term` within that campaign.
4. Matches Landing page by URL path.
5. Links the Company by email domain or phone when one exists, and creates one otherwise.

The Google Ads workspace then shows, per campaign, keyword, and page: leads, booked, sold, and the deal value they produced. Cost per lead and cost per booked use `Spend to date` on the campaign (typed from the platform for now; the Google Ads API is a later connection).

## The Lead loop (roadmap step 15)

Time in, time called, qualified, booked, showed, sold. `When` and `First call at` give minutes to first call; Status gives the rest. The five-minute promise is measured here.

## Status

The full per-channel wiring list (tags, link labels, Airtable rows, what is live) is `references/channel-connections.md` (2026-09-23).

- [x] Tables and links created 2026-09-15.
- [ ] Google Ads tracking template set in the account (Jonathan).
- [ ] `/book` form reads the six parameters into hidden fields and posts them (AIOS, on Jonathan's go; `/av_marketing/` already does for LinkedIn).
- [ ] Booker journey (2026-09-28, Jonathan: "a booker's full attribution and journey in a single view"): `public_html/assets/journey.js` on every page keeps the click that brought someone (tags, `li_fat_id`, `gclid`, the outside referrer) and each page and booking step with its time, in the visitor's own browser (`localStorage mb_journey`) for 30 days; the booking sends it (`payload.journey`, one line added by `scripts/build_service_page.py`, by hand on `/about/` and the `/av_marketing/` staging copy). The booking script saves it on Leads "Journey" and, on a return visit with no tags, credits the journey's first click (`withFirstTouch`). The CRM's lead page (`#/lead/<id>`) draws it; the LinkedIn page splits bookings into Ads (li_fat_id or a paid medium), Posts, and DMs (`utm_medium=dm`) with a booking rate each (ads and posts per click typed on their campaign rows, DMs per reply). Live once the pages are pushed and the script republished. Privacy page lines added, pending Jonathan's approval.
- [ ] Referrer rule in the booking script (2026-09-28): with no `utm_source`, a linkedin.com or lnkd.in referrer is LinkedIn and a Google search referrer is Google Organic (was: inbound). Edited in `scripts/avmarketing-booking.gs`; live once Jonathan pastes the file into the Apps Script project and publishes a new version (the same republish the `agenda` action is waiting on). Post links should still carry the tags: `?utm_source=linkedin&utm_medium=social&utm_campaign=linkedin-posts&utm_content=<post date>` (Campaigns row "LinkedIn posts").
- [x] `/av_marketing/` bookings post straight to Leads from the Apps Script backend with the UTM string, Status Booked, and links by name (2026-09-23, `references/apps-script-booking.md`; live once `AIRTABLE_TOKEN` is set). The channel is read the same way as the list above; a LinkedIn click id or a paid-social medium off a LinkedIn referrer still counts as LinkedIn when `utm_source` carries an id instead of the word.
- [ ] LinkedIn template checked in Campaign Manager: LinkedIn substitutes `{{CAMPAIGN_ID}}`, `{{CAMPAIGN_NAME}}`, `{{CAMPAIGN_GROUP_ID}}`, `{{CREATIVE_ID}}`, `{{ACCOUNT_ID}}`; `{{AD_SET_ID}}` is the Meta name and arrives as literal text if LinkedIn does not know it (Section Spec, Tracking). Keep `utm_source=linkedin` so the channel maps.
- [ ] Inbox pass parses "New Monarc Build lead" emails from formsubmit.co into Leads rows (`/level-up` candidate).
- [ ] Meta (2026-10-03, `projects/meta-ads/README.md`): the ad link is `/builder-check/?utm_source=facebook&utm_medium=paid-social&utm_campaign={{campaign.id}}&utm_content={{ad.id}}`; the campaign id goes in the Campaigns row's Platform id before the ad runs. `fbclid` is captured by the popup's hidden fields and the booking script (`scripts/meta_pixel_update.py` added it to every mirror page; live with the pending push and republish). The check's four answers ride on the Leads row as Installs, Technicians, Last five, Ads today.
