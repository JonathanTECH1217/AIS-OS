---
name: list-building
description: Use when Jonathan says "build a list", "list building", "pull a list", "qualify the list", or when the SDR skill's cold outreach needs its list. A big pull from the Google Maps API, a Clay hookup for email, owner name, and LinkedIn URL, then a few qualifications from reviews and the website that show which of five things a company could use: a new site, a receptionist, email follow-up, an appointment setter, a proposal builder. Quotes the cost before any pull; never buys without a go.
argument-hint: "<company slug> [quote | pull | enrich | qualify | handover]"
---

# List building

A skill the SDR's cold outreach gets its list from (`.agents/skills/sdr/workflows/cold-outreach.md`). Not sold by itself. The same steps for Monarc's own list and for a client's.

Jonathan, 2026-10-05: "The list is just a big pull from google maps api with a clay hookup for email, owner name, and linkedin url, and the few qualifications like reviews and website signals that they could use a new site, receptionist, email follow up, an appointment setter, and a proposal builder come next."

## Primary objective

Every row is a real company with its owner's name and a way to reach them that works, and beside it which of the five things it could use and why.

## Its workflows

Each is one file in `workflows/`. Read the one you are running before you start.

| Workflow | What sets it off | What comes out | File |
|---|---|---|---|
| Hero check | A qualified list, or "filter the seed list", "which ones have no booking form" | The residential integrators whose first screen misses the ask, the centering, or the buyer's words, each with its reason and a picture of the first screen; `scripts/hero_check.py` | `workflows/hero-check.md` |

## Read first

1. The install record that asked for the list (`projects/clients/<slug>/sdr.md`): who, where, the row count, the review band, the do-not-contact list.
2. `references/google-places-api.md` and `references/credentials.md` (keys through `scripts/outreach_common.py`).
3. `references/airtable-api.md` before any row is written to a base.

## Procedure

Pick the mode from `$ARGUMENTS` or the request. Default is the next step that has not run for this list.

### quote

1. From the intake: the kinds of business (these become the Maps search words), the cities, the rows wanted.
2. The cost: Maps requests at $35 per 1,000 (20 companies a request), plus Clay's price per row for the three fields.
3. The owner approves the number. Nothing is pulled before that.

### pull

1. The Google Maps pull: `python scripts/places_seed.py --queries "<kind> in {loc}" --max-cost <approved>`. It caches every page, so a rerun never buys the same search twice.
2. One row per company: doubles out by Place ID and by website domain.
3. Each row has, from Maps: name, address, phone, website, rating, review count.

### enrich (the Clay hookup)

1. Each row goes to Clay with its name, website, and city.
2. It comes back with three fields: the owner's name, an email, the owner's LinkedIn URL.
3. Every email is verified. One that fails is dropped from the row; the row stays if it still has a LinkedIn URL or a phone.
4. Until the Clay hookup is built: `scripts/meta_seed.py` reads each site's contact and about pages for owner names and emails. It finds an owner name on about one company in four and no LinkedIn profile for the owner.

### qualify

A few checks, each read from the Maps row or the company's own website. Each of the five gets a yes or a no and one line of proof.

| Could use | The signal | Read from |
|---|---|---|
| (all) | Reviews: the count and the rating, inside the band set at intake | the Maps row |
| A new site | No website on the listing; or the site is on a template builder (Wix, GoDaddy, Squarespace, Weebly, Duda); or it does not load over https | the Maps row, the site |
| A receptionist | No chat on the site, and no sign the phone is answered after hours | the site |
| Email follow-up | A contact form, and no email tool behind the site | the site |
| An appointment setter | No way to book from the first screen: the hero's button goes to a contact page, a phone number, or nothing (built 2026-10-05: `workflows/hero-check.md`, which also checks the centered headline and the buyer's words) | the site, rendered |
| A proposal builder | The site offers a free estimate or quote and takes it by phone or a plain form | the site |

The signals are the AIOS's first cut of his line. Each is one he can add to, change, or strike.

Then each row is sorted:

- **Kept:** inside the review band, and at least one of the five is a yes.
- **Held:** the site could not be read. A person looks.
- **Dropped:** outside the band, none of the five, a double, or on the do-not-contact list. The reason is written on the row.

Built today: the template-builder fingerprints (`PLATFORM_RULES` in `scripts/qualify_sites.py`), the https check (`scripts/free_campaign.py`, the site read), and the booking check (`scripts/hero_check.py`, 2026-10-05). Not built: the chat, email tool, and estimate checks.

### handover

1. The list, one row per company, to where the install record says (at Monarc: a workbook in `projects/outreach/` and the Prospects base).
2. A method page: rows pulled, enriched, kept, held, dropped by reason, and the cost against the approved number.
3. Twenty rows picked at random go to the owner to check.

## Criteria for passing

- [ ] The cost came in at or under the approved number.
- [ ] Every kept row has the company, the phone, the website or "none", the review count and rating, the owner's name, and a verified email or a LinkedIn URL.
- [ ] Every kept row has a yes or no for each of the five, with one line of proof for each yes.
- [ ] No email that failed the check is on the list.
- [ ] No doubles. No row from the do-not-contact list.
- [ ] Of the 20 rows the owner checked, 18 or more are right: the owner is real, is at that company, and each yes is true.
- [ ] The method page adds up: pulled = kept + held + dropped.

## Never without a go

- A Maps pull or a Clay run. Each is quoted first.
- A second pull for the same list.
- Passing a list to a sending tool before the owner's 20-row check.

## What is not built yet

- The Clay hookup: no Clay account or key is on file, and there is no `references/clay-api.md`.
- The chat, email tool, and estimate checks named above.
- `scripts/places_seed.py` writes the integrator workbook layout; a pull for any kind of business works through `--queries`, and the sheet names stay as they are until that is changed.
