"""Seed the six keyword CSVs for Monarc's own Google Ads (projects/google-ads/keywords/method.md, step 2).

Usage: python scripts/ads_keyword_matrix.py [--merge]

Writes projects/google-ads/keywords/<service>.csv with the seed rows and the modifier
matrix (channel word x trade word x pattern), status "candidate", planner columns blank.
With --merge, rows from <service>-research.csv (the web research, same schema) are merged:
a research row on a keyword the matrix also produced replaces its intent, searcher, match
type, and status and adds its source and note; a new research row is added. Jonathan's work
in the existing <service>.csv wins on a rerun: planner numbers, SERP counts, ad groups, an
approval, and a matrix row he parked or negated by hand.

Also writes projects/google-ads/keywords/paste/<service>-discover.txt (up to 10 seeds for
Keyword Planner's "Discover new keywords"), <service>-volume.txt (every row that is not a
negative, for "Get search volume and forecasts"), and <service>-negatives.txt.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYWORDS = ROOT / "projects" / "google-ads" / "keywords"
COLUMNS = ["keyword", "service", "trade", "intent", "searcher", "match_type", "source",
           "planner_avg_monthly", "planner_competition", "planner_bid_low", "planner_bid_high",
           "serp_ad_count", "serp_advertisers", "status", "ad_group", "landing_page", "notes"]

TRADES = {
    "integrator": ["av company", "av integrator", "home automation company", "smart home installer", "home theater company", "low voltage contractor", "integrator"],
    "electrician": ["electrician", "electrical contractor"],
    "hvac": ["hvac company", "heating and air company"],
    "roofing": ["roofing company", "roofer"],
    "plumbing": ["plumber", "plumbing company"],
    "contractor": ["contractor", "home services company"],
}
PLURAL = {"av company": "av companies", "av integrator": "av integrators", "home automation company": "home automation companies",
          "smart home installer": "smart home installers", "home theater company": "home theater companies",
          "low voltage contractor": "low voltage contractors", "integrator": "integrators", "electrician": "electricians",
          "electrical contractor": "electrical contractors", "hvac company": "hvac companies", "heating and air company": "heating and air companies",
          "roofing company": "roofing companies", "roofer": "roofers", "plumber": "plumbers", "plumbing company": "plumbing companies",
          "contractor": "contractors", "home services company": "home services companies"}

SERVICES = {
    "google-ads": {
        "landing_page": "/google-ads/",
        "channels": ["google ads", "ppc", "adwords", "paid search", "google ads management"],
        "seeds": ["google ads for home automation companies", "google ads management for av companies", "ppc for smart home installers",
                  "google ads for low voltage contractors", "google ads for electricians", "google ads for hvac companies",
                  "ppc for roofing companies", "google ads for plumbers", "marketing agency for home integrators",
                  "control4 dealer marketing", "cedia marketing agency", "lighting control leads"],
    },
    "website-build": {
        "landing_page": "/website-build/",
        "channels": ["website design", "web design", "website", "landing pages", "website redesign"],
        "seeds": ["website design for contractors", "contractor website design company", "website for electrical contractors",
                  "home automation website design", "hvac website design company", "roofing website design", "plumbing website design",
                  "website that generates leads for contractors", "redesign my contractor website", "av company website design",
                  "landing pages for contractors"],
    },
    "seo": {
        "landing_page": "/seo/",
        "channels": ["seo", "local seo", "google business profile", "search ranking", "aeo"],
        "seeds": ["seo for contractors", "local seo for electricians", "seo agency for hvac companies", "roofing seo company",
                  "plumber seo services", "seo for home automation companies", "seo for av integrators",
                  "google business profile optimization service", "google business profile management for contractors",
                  "answer engine optimization agency", "copywriting for contractor websites"],
    },
    "email-marketing": {
        "landing_page": "/email-marketing/",
        "channels": ["email marketing", "email automation", "drip campaign", "email sequence", "lead nurture"],
        "seeds": ["email marketing for contractors", "email marketing agency for home services", "drip campaign for hvac company",
                  "quote follow up email automation", "past customer email campaign contractor", "lead nurture for contractors",
                  "email marketing for electricians", "email marketing for av companies", "proposal follow up email contractor"],
    },
    "facebook-ads": {
        "landing_page": "/facebook-ads/",
        "channels": ["facebook ads", "instagram ads", "meta ads", "social media ads", "facebook advertising"],
        "seeds": ["facebook ads for contractors", "facebook ads for home automation", "facebook ads agency for home services",
                  "instagram ads for electricians", "facebook ads management for contractors", "facebook lead ads for hvac",
                  "facebook ads for roofing companies", "social media ads for contractors", "facebook ads for smart home installers"],
    },
    "ai-automation": {
        "landing_page": "/ai-automation/",
        "channels": ["ai automation", "automation", "ai receptionist", "missed call text back", "invoicing automation",
                     "bookkeeping automation", "proposal automation", "lead follow up automation"],
        "seeds": ["ai automation for contractors", "automate contractor proposals", "contractor invoicing automation",
                  "bookkeeping automation for contractors", "ai for small contractors", "contractor back office automation",
                  "missed call text back for contractors", "ai receptionist for contractors", "automated lead follow up for contractors",
                  "ai answering service for electricians", "ai phone answering for hvac"],
    },
}

PATTERNS = [
    "{channel} for {trades}",            # google ads for electricians
    "{channel} agency for {trades}",     # google ads agency for electricians
    "{trade} {channel} company",         # electrician google ads company
    "{channel} services for {trades}",   # google ads services for electricians
]


def trade_of(keyword):
    for trade, words in TRADES.items():
        for w in words:
            if w in keyword or PLURAL[w] in keyword:
                return trade
    return "contractor"


def row(keyword, service, source, landing_page, intent="buy", searcher="contractor", match_type="phrase", notes=""):
    return {
        "keyword": keyword, "service": service, "trade": trade_of(keyword), "intent": intent, "searcher": searcher,
        "match_type": match_type, "source": source, "planner_avg_monthly": "", "planner_competition": "",
        "planner_bid_low": "", "planner_bid_high": "", "serp_ad_count": "", "serp_advertisers": "",
        "status": "candidate", "ad_group": "", "landing_page": landing_page, "notes": notes,
    }


def read(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})


HUMAN_FIELDS = ("ad_group", "planner_avg_monthly", "planner_competition", "planner_bid_low", "planner_bid_high",
                "serp_ad_count", "serp_advertisers")
RESEARCH_FIELDS = ("trade", "intent", "searcher", "match_type", "status")


def paste_files(service, spec, rows):
    """Write the lists Jonathan pastes into Keyword Planner (method.md step 4) and the negatives for the campaign."""
    out = KEYWORDS / "paste"
    out.mkdir(parents=True, exist_ok=True)
    volume = [r["keyword"] for r in rows if r.get("status") != "negative"]
    negatives = [r["keyword"] for r in rows if r.get("status") == "negative"]
    parked = {r["keyword"].strip().lower() for r in rows if r.get("status") in ("negative", "parked")}
    discover = [s for s in spec["seeds"] if s.lower() not in parked]
    for r in rows:
        if len(discover) >= 10:
            break
        if r.get("source", "").startswith(("serp", "paa", "forum", "competitor")) and r.get("intent") == "buy" \
                and r.get("status") == "candidate" and r["keyword"] not in discover:
            discover.append(r["keyword"])
    (out / f"{service}-discover.txt").write_text("\n".join(discover[:10]) + "\n", encoding="utf-8")
    (out / f"{service}-volume.txt").write_text("\n".join(volume) + "\n", encoding="utf-8")
    (out / f"{service}-negatives.txt").write_text("\n".join(negatives) + "\n", encoding="utf-8")
    return len(discover[:10]), len(volume), len(negatives)


def main():
    merge = "--merge" in sys.argv
    KEYWORDS.mkdir(parents=True, exist_ok=True)
    for service, spec in SERVICES.items():
        path = KEYWORDS / f"{service}.csv"
        existing = {r["keyword"].strip().lower(): r for r in read(path)}
        rows = {}  # key -> row, in insertion order

        def put(r):
            k = r["keyword"].strip().lower()
            if k and k not in rows:
                rows[k] = r

        for s in spec["seeds"]:
            put(row(s, service, "seed", spec["landing_page"], notes="seed from the plan"))
        for channel in spec["channels"]:
            for trade, words in TRADES.items():
                for w in words:
                    for pat in PATTERNS:
                        put(row(pat.format(channel=channel, trade=w, trades=PLURAL[w]), service, "matrix", spec["landing_page"]))
        if merge:
            # the web research is evidence: on a keyword the matrix also produced, its intent, searcher, match type,
            # and status replace the matrix defaults, and its source and note are added
            for r in read(KEYWORDS / f"{service}-research.csv"):
                k = r.get("keyword", "").strip().lower()
                if not k:
                    continue
                r["landing_page"] = r.get("landing_page") or spec["landing_page"]
                r["service"] = r.get("service") or service
                r["trade"] = r.get("trade") or trade_of(k)
                r["status"] = r.get("status") or "candidate"
                if k in rows:
                    base = rows[k]
                    for c in RESEARCH_FIELDS:
                        if r.get(c):
                            base[c] = r[c]
                    base["source"] = f"{base.get('source', '')}+{r.get('source') or 'research'}".strip("+")
                    base["notes"] = " | ".join(x for x in (r.get("notes", ""), base.get("notes", "")) if x)
                else:
                    rows[k] = {c: r.get(c, "") for c in COLUMNS}
        # Jonathan's work in the existing file wins: planner numbers, SERP counts, ad groups, an approval, and a
        # matrix row he parked or negated by hand (the computed status would otherwise put it back to candidate)
        for k, old in existing.items():
            if k not in rows:
                rows[k] = old  # a term added by hand stays
                continue
            new = rows[k]
            for c in HUMAN_FIELDS:
                if old.get(c):
                    new[c] = old[c]
            if old.get("status") == "approved" or (old.get("status") not in ("", "candidate") and new.get("status") == "candidate"):
                new["status"] = old["status"]
        final = list(rows.values())
        write(path, final)
        d, v, n = paste_files(service, spec, final)
        counts = {}
        for r in final:
            counts[r.get("status", "")] = counts.get(r.get("status", ""), 0) + 1
        print(f"{service}: {len(final)} rows -> {path.name} {counts}; paste lists: {d} discover seeds, {v} for volume, {n} negatives")


if __name__ == "__main__":
    main()
