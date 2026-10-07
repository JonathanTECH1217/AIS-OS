# Google Places API (New): national integrator seed list

Domain 5 and 11, `connections.md`. Started 2026-09-13. Goal: a national list of home integrators, AV companies,
and home theater builders as the LinkedIn company-list seed and a superset of the dial list.

## The short version

One endpoint does the work: **Text Search (New)**, `POST https://places.googleapis.com/v1/places:searchText`.
Send `{"textQuery": "home automation installer in Naples, FL", "regionCode": "US", "pageSize": 20}` with headers
`X-Goog-Api-Key` and `X-Goog-FieldMask`. Each response has up to 20 places and a `nextPageToken`; a query caps at
60 results across three pages. `scripts/places_seed.py` runs the grid in `scripts/places_grid.py`, caches every page,
dedupes on Place ID against the lists we already own, and writes `projects/outreach/places-seed-<DATE>.xlsx` in the
`Integrator_List` layout so `scripts/qualify_list.py` works on it unchanged.

Monarc OS has the same call in `monarc-os\Agents\Voyager\Prospect_Mapping\tools\places_search.py`; this script
ports it rather than importing across repos.

## Billing (verified against the pricing page 2026-09-13)

The SKU is set by the field mask. Our mask includes `websiteUri`, `nationalPhoneNumber`, `rating`, `userRatingCount`,
so every page is **Text Search Enterprise**: $35.00 per 1,000 requests, first 1,000 per month free at the project
level. Each `pageToken` call is a separate request. Field tiers:

| SKU | Fields | $/1,000 | Free/month |
|---|---|---|---|
| Essentials | `id`, `name`, `attributions`, `nextPageToken` | 2.00 | 10,000 |
| Pro | `displayName`, `formattedAddress`, `addressComponents`, `types`, `primaryType`, `googleMapsUri`, `location` | 32.00 | 5,000 |
| Enterprise | + `websiteUri`, `nationalPhoneNumber`, `rating`, `userRatingCount`, `businessStatus` | 35.00 | 1,000 |
| Enterprise + Atmosphere | + reviews, amenities | 40.00 | 1,000 |

Grid cost: 213 locations, 6 queries per metro, 4 per enclave, 1,102 text searches, 1,102 to 3,306 requests,
$39 to $116 before the free tier. Early stop (a page adds fewer than 5 new places or under 20% new) keeps it near
the low end. `--dry-run` prints the exact numbers; `--max-cost` defaults to 45% of `SEED_BUDGET_USD`.

## Setup, in order

1. **Key.** `GOOGLE_MAPS_API_KEY` in `%USERPROFILE%\.monarc\secrets.env` (see `references/credentials.md`). The
   Cloud project must have "Places API (New)" enabled and billing on. Restrict the key to that API.
2. **Check, no spend:** `python scripts/places_seed.py --check-keys` then `python scripts/places_seed.py --dry-run`.
3. **Smoke test:** `python scripts/places_seed.py --limit-locations 3` (18 to 54 requests, under $2). Open the
   workbook, confirm `Extras` has Place IDs and the query text.
4. **Full run:** `python scripts/places_seed.py`. Resumable: finished queries are skipped on rerun. Rebuild the
   workbook without spending: `--build-only`.
5. **Then qualify:** `python scripts/qualify_sites.py` (see `references/anthropic-api.md`).

## Request shape

```
POST https://places.googleapis.com/v1/places:searchText
X-Goog-Api-Key: <key>
X-Goog-FieldMask: places.id,places.displayName,places.formattedAddress,places.addressComponents,
  places.nationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount,places.businessStatus,
  places.primaryType,places.types,places.googleMapsUri,nextPageToken
{"textQuery": "<template> in <City, ST>", "regionCode": "US", "languageCode": "en", "pageSize": 20,
 "pageToken": "<from previous page, optional>"}
```

`addressComponents` gives `locality` (city), `administrative_area_level_1` (state), `administrative_area_level_2`
(county), `postal_code`. Errors come back as `{"error": {"code", "message", "status"}}`; the script stops on any
4xx (bad key, API not enabled, quota) and retries 429/5xx three times.

## Fallbacks

- Dealer locators (Crestron, Control4, Savant, Lutron, Josh.ai, Sonos, Kaleidescape) through the browser driver,
  `scripts/browser_driver.py`. Free, slower, higher-tier prospects. Not built yet.
- The existing 2,000-row `Integrator_List_2026-09-05.xlsx` already covers 29 metros; the seed script merges it.

## Rules (Intern Rule)

- Read-only against Google; nothing is written back anywhere but `projects/outreach/`.
- The key stays in `secrets.env`. Never in chat, never in the repo.
- Cost estimate before every run; the meter refuses a page that would cross the cap.

## Status

- [x] Script and grid written, dry-run and build-only verified on the 2026-09-05 list (2026-09-13)
- [x] Key in `secrets.env` (2026-09-13)
- [x] Smoke test: 3 locations, 24 pages, $0.84, 106 new places (2026-09-13)
- [x] Full national run: 1,084 queries, 1,516 pages, 8,091 new places, $53.90, no errors, about 45 minutes (2026-09-13). Actual pages per query averaged 1.4, so the low estimate is the one to plan on.
- [ ] Confirm the billed amount in Cloud Console matches $53.90 minus the free tier
