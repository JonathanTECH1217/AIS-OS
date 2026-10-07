"""DataForSEO: the real Google results page and Keyword Planner numbers, by city.

Lifted 2026-10-03 from archives/dataforseo-check-2026-09-28/ads_keyword_check.py for the free-campaign audit
(scripts/free_campaign.py). The archive hard-wired the whole United States (2840); the audit asks what a buyer in one
city sees, so every call takes a location_code (a DataForSEO city code) or a location_coordinate ("lat,lon,radius").

Endpoints (base https://api.dataforseo.com/v3, HTTP Basic auth, one task per live call):
  serp/google/organic/live/advanced     the live page: organic, paid, local_pack items     $0.002 a page of 10
  keywords_data/google_ads/search_volume/live   Keyword Planner volume, cpc, top-of-page bids  $0.09 a request
  serp/google/locations/us              every US location with its code (free, cached to disk)
Keys: DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD in %USERPROFILE%\\.monarc\\secrets.env (references/dataforseo-api.md).

  python scripts/dataforseo.py locations "Naples" FL      print the matching location codes (one free download)
  python scripts/dataforseo.py serp "home theater installation naples" --city Naples --state FL
"""
import argparse
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import ROOT, STATE_NAMES, get_secret  # noqa: E402

DFS = "https://api.dataforseo.com/v3"
US, ENGLISH = 2840, "en"
VOLUME_TASK_USD = 0.09      # live, up to 1,000 keywords per task (dataforseo.com/pricing/keywords-data/google-ads)
SERP_USD = 0.002            # live, one page of 10 (dataforseo.com/pricing/google-serp/google-organic-serp-api)
LOCATIONS_CACHE = ROOT / "projects" / "free-campaign" / "dataforseo-locations.json"
HINT = "Sign up at dataforseo.com ($50 minimum), then put the API login and password from app.dataforseo.com/api-access in ~/.monarc/secrets.env."


class DataForSEO:
    def __init__(self, login, password):
        self.s = requests.Session()
        self.s.auth = (login, password)
        self._locations = None

    @classmethod
    def from_env(cls):
        return cls(get_secret("DATAFORSEO_LOGIN", True, HINT), get_secret("DATAFORSEO_PASSWORD", True, HINT))

    @staticmethod
    def keys_present():
        return bool(get_secret("DATAFORSEO_LOGIN") and get_secret("DATAFORSEO_PASSWORD"))

    # ---- transport

    def _check(self, r, path):
        if r.status_code == 401:
            sys.exit("DataForSEO refused the login. Check DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD (app.dataforseo.com/api-access).")
        r.raise_for_status()
        body = r.json()
        if body.get("status_code") != 20000:
            sys.exit(f"DataForSEO: {body.get('status_code')} {body.get('status_message')}")
        t = body["tasks"][0]
        if t.get("status_code") != 20000:
            msg = f"{t.get('status_code')} {t.get('status_message')}"
            if str(t.get("status_code")).startswith("402"):
                msg += " (top up the DataForSEO balance)"
            raise RuntimeError(f"DataForSEO task failed on {path}: {msg}")
        return t.get("result") or [], float(t.get("cost") or body.get("cost") or 0)

    def post(self, path, task):
        r = self.s.post(f"{DFS}/{path}", json=[task], timeout=(10, 120))
        return self._check(r, path)

    def get(self, path):
        r = self.s.get(f"{DFS}/{path}", timeout=(10, 120))
        return self._check(r, path)

    # ---- locations: "Naples,Florida,United States" -> 1015073 (the code DataForSEO gives that city)

    def locations(self, country="us"):
        if self._locations is not None:
            return self._locations
        if LOCATIONS_CACHE.exists():
            self._locations = json.loads(LOCATIONS_CACHE.read_text(encoding="utf-8"))
            return self._locations
        rows, _ = self.get(f"serp/google/locations/{country}")
        keep = [{"code": r.get("location_code"), "name": r.get("location_name"), "type": r.get("location_type")}
                for r in rows if r.get("location_code")]
        LOCATIONS_CACHE.parent.mkdir(parents=True, exist_ok=True)
        LOCATIONS_CACHE.write_text(json.dumps(keep, indent=0), encoding="utf-8")
        self._locations = keep
        return keep

    def city_code(self, city, state):
        """The location code for a city: the City entry "<City>,<State name>,United States" first, then any
        location whose name starts with the city in that state (a county or a neighborhood). (code, name) or (None, None)."""
        st = (state or "").upper()
        want = f"{(city or '').strip().lower()},{STATE_NAMES.get(st, st).lower()},united states"
        locs = self.locations()
        for pref in ("City", None):
            for l in locs:
                name = (l.get("name") or "").lower()
                if name == want and (pref is None or l.get("type") == pref):
                    return l["code"], l["name"]
        head = f"{(city or '').strip().lower()},"
        tail = f",{STATE_NAMES.get(st, st).lower()},united states"
        for l in locs:
            name = (l.get("name") or "").lower()
            if name.startswith(head) and name.endswith(tail):
                return l["code"], l["name"]
        return None, None

    # ---- the page

    def serp(self, keyword, location_code=None, location_coordinate=None, depth=10, device="desktop"):
        task = {"keyword": keyword, "language_code": ENGLISH, "device": device, "depth": depth}
        if location_coordinate:
            task["location_coordinate"] = location_coordinate
        else:
            task["location_code"] = location_code or US
        res, cost = self.post("serp/google/organic/live/advanced", task)
        page = res[0] if res else {}
        items = page.get("items") or []
        organic = [{"n": it.get("rank_group") or it.get("rank_absolute"), "domain": it.get("domain"), "title": it.get("title"),
                    "url": it.get("url"), "snippet": (it.get("description") or "")[:300]}
                   for it in items if it.get("type") == "organic"][:depth]
        for i, o in enumerate(organic, 1):
            o["n"] = i
        paid = [{"domain": it.get("domain"), "title": it.get("title"), "url": it.get("url")}
                for it in items if it.get("type") == "paid"]
        pack = []
        for it in items:
            if it.get("type") != "local_pack":
                continue
            rating = it.get("rating") or {}
            pack.append({"n": len(pack) + 1, "title": it.get("title"), "domain": it.get("domain"), "phone": it.get("phone"),
                         "url": it.get("url"), "rating": rating.get("value"), "reviews": rating.get("votes_count"),
                         "is_paid": bool(it.get("is_paid"))})
        return {"keyword": keyword, "location_code": task.get("location_code"), "location_coordinate": location_coordinate,
                "check_url": page.get("check_url"), "organic": organic, "paid": paid, "local_pack": pack,
                "item_types": page.get("item_types") or []}, cost

    # ---- Keyword Planner numbers

    def volume(self, keywords, location_code=None):
        rows, cost = self.post("keywords_data/google_ads/search_volume/live",
                               {"keywords": keywords, "location_code": location_code or US, "language_code": ENGLISH})
        out = {}
        for r in rows:
            out[(r.get("keyword") or "").lower()] = {
                "searches": r.get("search_volume"), "competition": r.get("competition"), "cpc": r.get("cpc"),
                "bid_low": r.get("low_top_of_page_bid"), "bid_high": r.get("high_top_of_page_bid"),
            }
        return out, cost


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("locations", help="print the location codes that match a city")
    p.add_argument("city")
    p.add_argument("state")
    p = sub.add_parser("serp", help="one live results page, printed")
    p.add_argument("keyword")
    p.add_argument("--city", required=True)
    p.add_argument("--state", required=True)
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return
    dfs = DataForSEO.from_env()
    if a.cmd == "locations":
        code, name = dfs.city_code(a.city, a.state)
        print(f"{a.city}, {a.state}: {code} ({name})" if code else f"{a.city}, {a.state}: no match")
        st = STATE_NAMES.get(a.state.upper(), a.state)
        near = [l for l in dfs.locations() if a.city.lower() in (l.get("name") or "").lower() and st.lower() in (l.get("name") or "").lower()]
        for l in near[:10]:
            print(f"  {l['code']}  {l['type']:<12} {l['name']}")
        return
    code, name = dfs.city_code(a.city, a.state)
    if not code:
        sys.exit(f"No DataForSEO location for {a.city}, {a.state}.")
    page, cost = dfs.serp(a.keyword, location_code=code)
    print(f"{a.keyword} in {name} (${cost:.3f}); items: {', '.join(page['item_types'])}")
    for ad in page["paid"]:
        print(f"  ad      {ad['domain']}  {ad['title']}")
    for p_ in page["local_pack"]:
        print(f"  map {p_['n']}   {p_['title']}  {p_['rating']} ({p_['reviews']})  {p_['domain'] or ''}")
    for o in page["organic"]:
        print(f"  {o['n']:>2}      {o['domain']}  {o['title']}")


if __name__ == "__main__":
    main()
