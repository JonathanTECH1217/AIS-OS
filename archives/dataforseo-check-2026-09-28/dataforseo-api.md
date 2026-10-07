# DataForSEO API

Added 2026-09-28 for the keyword check behind the Google Ads publish plan. Jonathan's choice over waiting for Google's own Keyword Planner API, which needs Basic access (brand verification and about 10 business days); Explorer access, enough to publish campaigns, blocks Keyword Planner.

## What it gives us

- **Search volume**: Google Keyword Planner numbers, resold. Average monthly searches over the last 12 months, the monthly trend, competition, and the low and high top-of-page bid.
- **The Google results page**: the live top 10 for a keyword, with the ads on it as `paid` items.

No open-source tool has its own search volume; they all read Google's data through Google's API or a reseller like this one.

## Account and keys

- Sign up at dataforseo.com. Minimum payment $50, pay as you go after that.
- The API login and password are on app.dataforseo.com/api-access (not the website login). Put them in `%USERPROFILE%\.monarc\secrets.env` as `DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD` (`references/credentials.md`).
- Set a spend limit in the dashboard as the backstop. The script also caps each run (`--max-cost`, default $3).

## Endpoints used

Base `https://api.dataforseo.com/v3`, HTTP Basic auth, JSON body is a list of tasks. Live endpoints take one task per call.

| Job | Endpoint | Body | Price (2026-09-28) |
|---|---|---|---|
| Volume | `POST keywords_data/google_ads/search_volume/live` | `{"keywords": [...], "location_code": 2840, "language_code": "en"}`. Up to 1,000 keywords, 80 characters and 10 words each. 12 requests a minute | $0.09 per request, any number of keywords up to 1,000 |
| Results page | `POST serp/google/organic/live/advanced` | `{"keyword": "...", "location_code": 2840, "language_code": "en", "device": "desktop", "depth": 10}` | $0.002 per page of 10 |

Reply shape: top level `status_code` 20000 means OK. Each task has its own `status_code` and `cost`, and `result`.
- Volume: `result[]` holds `keyword`, `search_volume`, `competition`, `competition_index`, `cpc`, `low_top_of_page_bid`, `high_top_of_page_bid`, `monthly_searches[]`. `search_volume` is null when Google has no data, which the check treats as zero.
- Results page: `result[0].items[]`, with `type` "organic" or "paid" (and others such as `local_pack`, `people_also_ask`), each with `domain`, `title`, `description`, `url`. `result[0].item_types` lists which kinds appeared.

Errors: 401 is a wrong login; a task code starting 402 means the balance is out.

Pricing pages: [keywords data](https://dataforseo.com/pricing/keywords-data/google-ads), [organic results](https://dataforseo.com/pricing/google-serp/google-organic-serp-api).

## The script

`python scripts/ads_keyword_check.py --dry-run` prints what would be fetched and what it costs, and which keys are present. Without `--dry-run` it fetches, has Claude read each campaign's pages in one call, applies the pass rule, fills the `planner_*` and `serp_*` columns of `projects/google-ads/keywords/<service>.csv`, and writes `keywords/check-<date>.md`. Raw replies are cached in `projects/google-ads/keywords/dataforseo/cache.json` for 30 days. The whole 60-keyword check estimates at about $1.75, most of it the Claude read.
