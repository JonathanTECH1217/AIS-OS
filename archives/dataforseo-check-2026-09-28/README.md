# DataForSEO keyword check (archived 2026-09-28, never run)

Built the same day it was dropped. Jonathan: "we're going to skip using data for SEO and just go based on transactional assumptions for high-intent buyers." The five keywords per campaign are now picked by the rule in `projects/google-ads/keywords/method.md` ("The five per campaign").

What is here: `ads_keyword_check.py` (DataForSEO volume plus the live Google top 10, a Claude read of each page, the pass rule of 10+ searches and 6+ agency results) and `dataforseo-api.md` (endpoints, prices, keys). Tested dry and on made-up data; one 1-cent live Claude call; no DataForSEO account was ever opened. To bring it back: move both files back to `scripts/` and `references/`, and add `DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD` to `secrets.env`.
