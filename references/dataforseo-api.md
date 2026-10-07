# DataForSEO API

Added 2026-09-28 for the keyword check behind the Google Ads publish plan (dropped before it ran, `archives/dataforseo-check-2026-09-28/`); brought back 2026-10-03 for the free-campaign audit (`scripts/free_campaign.py`), which asks what a buyer in one city sees. Client: `scripts/dataforseo.py`.

## What it gives us

- **The Google results page**: the live top 10 for a keyword in a city, with the ads (`paid`), the map pack (`local_pack`, with each shop's rating and review count), and the organic results.
- **Search volume**: Google Keyword Planner numbers, resold. Average monthly searches, competition, and the low and high top-of-page bid, by location. The free-campaign budget line reads the bids.

No open-source tool has its own search volume or a legal live results page; they all read Google's data through Google's API or a reseller like this one.

## Account and keys

- Sign up at dataforseo.com. Minimum payment $50, pay as you go after that. Set a spend limit in the dashboard as the backstop.
- The API login and password are on app.dataforseo.com/api-access (not the website login). Put them in `%USERPROFILE%\.monarc\secrets.env` as `DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD` (`references/credentials.md`).
- Every script caps its run (`--max-cost`; the free-campaign build defaults to $0.50 a company).

## Endpoints used

Base `https://api.dataforseo.com/v3`, HTTP Basic auth, JSON body is a list of tasks. Live endpoints take one task per call.

| Job | Endpoint | Body | Price (2026-09-28, recheck) |
|---|---|---|---|
| Results page | `POST serp/google/organic/live/advanced` | `{"keyword": "...", "location_code": <city code>, "language_code": "en", "device": "desktop", "depth": 10}`; or `"location_coordinate": "lat,lon,radius"` for a town with no code | $0.002 per page of 10 |
| Volume | `POST keywords_data/google_ads/search_volume/live` | `{"keywords": [...], "location_code": <code>, "language_code": "en"}`. Up to 1,000 keywords | $0.09 per request |
| Locations | `GET serp/google/locations/us` | none | free; cached to `projects/free-campaign/dataforseo-locations.json` |

Reply shape: top level `status_code` 20000 means OK. Each task has its own `status_code`, `cost`, and `result`.
- Results page: `result[0].items[]`, with `type` "organic", "paid", "local_pack", and others (`people_also_ask`, `video`); each item carries `rank_group`, `rank_absolute`, `domain`, `title`, `url`, `description`. A `local_pack` item also carries `phone`, `rating.value`, `rating.votes_count`, `is_paid`. `result[0].item_types` lists which kinds appeared; `check_url` is the Google page it read.
- Volume: `result[]` holds `keyword`, `search_volume` (null when Google has no data), `competition`, `cpc`, `low_top_of_page_bid`, `high_top_of_page_bid`, `monthly_searches[]`.
- Locations: `location_code`, `location_name` ("Naples,Florida,United States"), `location_type` (City, County, State, Neighborhood, ...). `DataForSEO.city_code(city, state)` matches the City entry first, then any location in that state whose name starts with the city.

Errors: 401 is a wrong login; a task code starting 402 means the balance is out.

Pricing pages: [organic results](https://dataforseo.com/pricing/google-serp/google-organic-serp-api), [keywords data](https://dataforseo.com/pricing/keywords-data/google-ads).

## The scripts

- `python scripts/dataforseo.py locations Naples FL` prints the matching codes (one free download of the US list, then cached).
- `python scripts/dataforseo.py serp "home theater installation naples" --city Naples --state FL` prints one live page.
- `scripts/free_campaign.py` pulls three pages and one volume call per company, about $0.10 with Places, and keeps every reply in the company's folder so a rerun pays nothing.
