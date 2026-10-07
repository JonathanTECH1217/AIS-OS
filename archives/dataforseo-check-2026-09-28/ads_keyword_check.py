"""Check the picked keywords for search volume and who is searching, before Jonathan locks them.

Usage:
  python scripts/ads_keyword_check.py --dry-run             what would be fetched and what it costs; no calls, no keys
  python scripts/ads_keyword_check.py [--only 01,03] [--max-cost 3] [--fresh] [--no-write]
  python scripts/ads_keyword_check.py --only 03 --add "roofing seo agency; hvac seo services"   check swap candidates

Reads projects/google-ads/keywords/picks.json (5 picks and a bench of 5 per campaign, Jonathan 2026-09-28).
For every keyword:
  1. Volume: DataForSEO keywords_data/google_ads/search_volume/live, which resells Google Keyword Planner numbers.
     US, English, average of the last 12 months. One request holds up to 1,000 keywords ($0.09).
  2. The Google results page: serp/google/organic/live/advanced, top 10, desktop, US ($0.002 each). Ads on the
     page come back as "paid" items.
  3. Claude reads each campaign's pages in one call and labels what each result is (an agency selling the service
     to contractors, a list of such agencies, a guide, software, a homeowner page, jobs, other).
Pass rule (Jonathan 2026-09-28): 10 or more US searches a month, and 6 or more of the top 10 results are agencies
selling to contractors (their service pages or lists ranking them). A pick that fails is replaced by the first
bench keyword that passed.

Writes: the planner_* and serp_* columns of keywords/<service>.csv (ads_keyword_matrix.py keeps them on reruns);
keywords/check-<date>.md, one table per campaign; raw replies in keywords/dataforseo/cache.json, reused for 30 days
so a rerun pays nothing (--fresh ignores it).
Keys: DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD, ANTHROPIC_API_KEY via scripts/outreach_common.load_env.
"""
import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import BudgetExceeded, CostMeter, ROOT, get_secret, report_key_sources  # noqa: E402

KEYWORDS = ROOT / "projects" / "google-ads" / "keywords"
PICKS = KEYWORDS / "picks.json"
CACHE = KEYWORDS / "dataforseo" / "cache.json"
CACHE_DAYS = 30

DFS = "https://api.dataforseo.com/v3"
US, ENGLISH = 2840, "en"
VOLUME_TASK_USD = 0.09      # live, up to 1,000 keywords per task (dataforseo.com/pricing/keywords-data/google-ads)
SERP_USD = 0.002            # live, one page of 10 (dataforseo.com/pricing/google-serp/google-organic-serp-api)

MODEL = "claude-opus-5"
IN_PER_M, OUT_PER_M, CACHE_READ_PER_M = 5.00, 25.00, 0.50
EST_IN_PER_PAGE, EST_OUT_PER_PAGE = 1500, 700    # tokens; thinking counts as output

MIN_SEARCHES = 10
MIN_AGENCY = 6              # of 10
BUYER_LABELS = ("agency_service", "agency_list")
LABELS = ["agency_service", "agency_list", "guide", "software", "homeowner", "jobs", "other"]
LABEL_WORDS = {"agency_service": ("agency page", "agency pages"), "agency_list": ("agency list", "agency lists"),
               "guide": ("guide", "guides"), "software": ("software", "software"),
               "homeowner": ("homeowner page", "homeowner pages"), "jobs": ("job listing", "job listings"),
               "other": ("other", "other")}

SYSTEM = """You sort Google search results for Monarc Build, a small agency that sells Google Ads management, \
website builds, SEO, email marketing, Facebook ads, and AI automation to contractors: home integrators (AV, smart \
home, low voltage), electricians, HVAC, roofing, and plumbing companies.

For each keyword you get the top organic results (number, site, title, snippet) and the ads shown on the page. Label \
every organic result with exactly one of:
- agency_service: a company page that offers to do this service for contractors or home service businesses (the \
reader would hire them). An agency's own service or pricing page counts.
- agency_list: a ranking, review page, or directory of agencies that do this service for contractors (a buyer \
comparing agencies).
- guide: teaches how to do it yourself: how-to posts, tips, examples, statistics, courses, templates to copy, forum \
threads. A guide on an agency's blog is still a guide.
- software: a software product, app, website builder, or tool the contractor would run themselves.
- homeowner: written for a homeowner hiring a trade or buying a product.
- jobs: job listings, careers, or freelance work.
- other: anything else, including a different meaning of the words.

Judge each result by what the page is for, from its title and snippet. Then give one short plain sentence per \
keyword on who is searching, naming the main mix (for example "Mostly agencies selling to HVAC companies, plus two \
how-to guides"). Return only the JSON object."""

SCHEMA = {
    "type": "object",
    "properties": {
        "keywords": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "labels": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"n": {"type": "integer"}, "label": {"type": "string", "enum": LABELS}},
                            "required": ["n", "label"],
                            "additionalProperties": False,
                        },
                    },
                    "who": {"type": "string"},
                },
                "required": ["keyword", "labels", "who"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["keywords"],
    "additionalProperties": False,
}


# ---------------------------------------------------------------- inputs and cache

def load_picks(only=None):
    data = json.loads(PICKS.read_text(encoding="utf-8"))
    camps = data["campaigns"]
    if only:
        camps = [c for c in camps if c["nn"] in only]
    return camps


def load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {"volume": {}, "serp": {}, "intent": {}}


def save_cache(cache):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True), encoding="utf-8")


def fresh_entry(cache, kind, kw, fresh):
    e = cache.get(kind, {}).get(kw)
    if not e or fresh:
        return None
    try:
        age = date.today() - date.fromisoformat(e["fetched"])
    except (KeyError, ValueError):
        return None
    return e if age <= timedelta(days=CACHE_DAYS) else None


# ---------------------------------------------------------------- DataForSEO

class DataForSEO:
    def __init__(self, login, password):
        self.s = requests.Session()
        self.s.auth = (login, password)

    def post(self, path, task):
        r = self.s.post(f"{DFS}/{path}", json=[task], timeout=(10, 120))
        if r.status_code == 401:
            sys.exit("DataForSEO refused the login. Check DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD "
                     "(app.dataforseo.com/api-access).")
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

    def volume(self, keywords):
        rows, cost = self.post("keywords_data/google_ads/search_volume/live",
                               {"keywords": keywords, "location_code": US, "language_code": ENGLISH})
        out = {}
        for r in rows:
            out[r["keyword"].lower()] = {
                "searches": r.get("search_volume"),
                "competition": r.get("competition"),
                "cpc": r.get("cpc"),
                "bid_low": r.get("low_top_of_page_bid"),
                "bid_high": r.get("high_top_of_page_bid"),
                "monthly": [[m.get("year"), m.get("month"), m.get("search_volume")] for m in r.get("monthly_searches") or []],
            }
        return out, cost

    def serp(self, keyword):
        res, cost = self.post("serp/google/organic/live/advanced",
                              {"keyword": keyword, "location_code": US, "language_code": ENGLISH,
                               "device": "desktop", "depth": 10})
        page = res[0] if res else {}
        items = page.get("items") or []
        organic = [{"n": i + 1, "domain": it.get("domain"), "title": it.get("title"),
                    "snippet": (it.get("description") or "")[:300], "url": it.get("url")}
                   for i, it in enumerate([x for x in items if x.get("type") == "organic"][:10])]
        paid = [{"domain": it.get("domain"), "title": it.get("title")} for it in items if it.get("type") == "paid"]
        return {"organic": organic, "paid": paid, "item_types": page.get("item_types") or []}, cost


# ---------------------------------------------------------------- Claude

def page_block(kw, serp):
    lines = [f"KEYWORD: {kw}"]
    for o in serp["organic"]:
        lines.append(f"{o['n']}. {o['domain']} | {o['title']} | {o['snippet']}")
    if not serp["organic"]:
        lines.append("(no organic results)")
    ads = "; ".join(f"{p['domain']} ({p['title']})" for p in serp["paid"]) or "none"
    lines.append(f"ADS ON THE PAGE: {ads}")
    return "\n".join(lines)


def estimate_claude(n_pages):
    return round((n_pages * EST_IN_PER_PAGE + 1200) * IN_PER_M / 1e6 + n_pages * EST_OUT_PER_PAGE * OUT_PER_M / 1e6, 4)


def usage_cost(u):
    cache_read = getattr(u, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(u, "cache_creation_input_tokens", 0) or 0
    return round((u.input_tokens * IN_PER_M + cache_write * IN_PER_M * 1.25 + cache_read * CACHE_READ_PER_M
                  + u.output_tokens * OUT_PER_M) / 1e6, 6)


def read_intent(client, pages):
    """pages: [(keyword, serp)]. One call. Returns ({keyword: {"labels": {n: label}, "who": str}}, cost)."""
    content = "\n\n".join(page_block(kw, s) for kw, s in pages) + "\n\nLabel every result now."
    msg = client.beta.messages.create(
        model=MODEL, max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"], fallbacks="default",
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        system=SYSTEM, messages=[{"role": "user", "content": content}],
    )
    cost = usage_cost(msg.usage)
    if msg.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined the read ({getattr(msg.stop_details, 'category', '')}).")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("Claude ran out of room on the read; check fewer keywords at a time (--only).")
    text = next((b.text for b in msg.content if b.type == "text"), "")
    data = json.loads(text)
    out = {}
    for k in data["keywords"]:
        out[k["keyword"].strip().lower()] = {"labels": {str(x["n"]): x["label"] for x in k["labels"]}, "who": k["who"]}
    return out, cost


# ---------------------------------------------------------------- verdict

def verdict(vol, serp, intent):
    searches = (vol or {}).get("searches")
    n_results = len(serp["organic"]) if serp else 0
    labels = list((intent or {}).get("labels", {}).values())
    agency = sum(1 for lb in labels if lb in BUYER_LABELS)
    need = MIN_AGENCY if n_results >= 10 else max(1, round(n_results * MIN_AGENCY / 10))
    reasons = []
    if not searches or searches < MIN_SEARCHES:
        reasons.append(f"{searches or 0} searches a month (under {MIN_SEARCHES})")
    if agency < need:
        reasons.append(f"{agency} of {n_results} results are agencies (need {need})")
    mix = {}
    for lb in labels:
        if lb not in BUYER_LABELS:
            mix[lb] = mix.get(lb, 0) + 1
    return {"pass": not reasons, "searches": searches, "agency": agency, "of": n_results,
            "others": ", ".join(f"{v} {LABEL_WORDS[k][v > 1]}" for k, v in sorted(mix.items(), key=lambda kv: -kv[1])),
            "why": "; ".join(reasons)}


# ---------------------------------------------------------------- writes

def write_csv(service, results):
    path = KEYWORDS / f"{service}.csv"
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        rows = list(reader)
    by_kw = {r["kw"]: r for r in results}
    touched = 0
    for row in rows:
        r = by_kw.get(row["keyword"].strip().lower())
        if not r:
            continue
        v, s = r.get("vol") or {}, r.get("serp") or {}
        row["planner_avg_monthly"] = "" if v.get("searches") is None else str(v["searches"])
        row["planner_competition"] = v.get("competition") or ""
        row["planner_bid_low"] = "" if v.get("bid_low") is None else f"{v['bid_low']:.2f}"
        row["planner_bid_high"] = "" if v.get("bid_high") is None else f"{v['bid_high']:.2f}"
        row["serp_ad_count"] = str(len(s.get("paid") or []))
        row["serp_advertisers"] = "; ".join(sorted({p["domain"] for p in s.get("paid") or [] if p.get("domain")}))
        touched += 1
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return touched


def money(x):
    return "" if x is None else f"${x:,.2f}"


def report(camps, results_by_nn, meter, extra):
    today = date.today().isoformat()
    out = [f"# Keyword check, {today}", "",
           "Searches a month and bids: Google Keyword Planner numbers through DataForSEO (US, English, average of the "
           "last 12 months). Results: the live Google page, top 10, desktop, US, read by Claude.",
           f"Pass rule (Jonathan 2026-09-28): {MIN_SEARCHES}+ searches a month and {MIN_AGENCY} or more of the top 10 "
           "results are agencies selling to contractors (their service pages or lists ranking them).",
           f"Cost of this run: ${meter.total:.2f} ({', '.join(f'{k} ${v:.2f}' for k, v in meter.items.items()) or 'all cached'}).",
           ""]
    head = ["Keyword", "Searches a month", "Top-of-page bid", "Ads on the page", "Agency results", "The rest", "Pass"]
    for c in camps:
        res = results_by_nn.get(c["nn"])
        if not res:
            continue
        by_kw = {r["kw"]: r for r in res}
        out += [f"## {c['nn']} {c['service']}", ""]
        for title, group in (("Picks", c["picks"]), ("Bench, in replacement order", c["bench"]),
                             ("Swap candidates", extra.get(c["nn"], []))):
            if not group:
                continue
            out += [f"**{title}**", "", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
            for kw in group:
                r = by_kw.get(kw.lower())
                if not r:
                    continue
                v, vd = r.get("vol") or {}, r["verdict"]
                bid = (f"{money(v.get('bid_low'))} to {money(v.get('bid_high'))}"
                       if v.get("bid_low") is not None or v.get("bid_high") is not None else "no data")
                searches = "no data" if v.get("searches") is None else f"{v['searches']:,}"
                out.append(f"| {kw} | {searches} | {bid} | {len((r.get('serp') or {}).get('paid') or [])} | "
                           f"{vd['agency']} of {vd['of']} | {vd['others'] or '-'} | "
                           f"{'yes' if vd['pass'] else 'no: ' + vd['why']} |")
            out.append("")
        for kw in c["picks"] + c["bench"] + extra.get(c["nn"], []):
            r = by_kw.get(kw.lower())
            if r and r.get("who"):
                out.append(f"- *{kw}*: {r['who']}")
        final = [k for k in c["picks"] if by_kw.get(k.lower(), {}).get("verdict", {}).get("pass")]
        for b in c["bench"]:
            if len(final) >= 5:
                break
            if by_kw.get(b.lower(), {}).get("verdict", {}).get("pass"):
                final.append(b)
        out += ["", f"**Proposed five:** {'; '.join(final) if final else 'none passed'}"
                + (f" (short by {5 - len(final)}; more candidates needed)" if len(final) < 5 else ""), ""]
    path = KEYWORDS / f"check-{today}.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="count, estimate, and stop; no calls, no keys needed")
    ap.add_argument("--only", default="", help="campaign numbers, comma separated (e.g. 01,03)")
    ap.add_argument("--add", default="", help='extra keywords to check for --only, separated by ";"')
    ap.add_argument("--max-cost", type=float, default=3.0, help="USD cap for the run (default 3)")
    ap.add_argument("--fresh", action="store_true", help=f"ignore cached replies younger than {CACHE_DAYS} days")
    ap.add_argument("--no-write", action="store_true", help="leave the keyword CSVs alone")
    a = ap.parse_args()

    only = [x.strip().zfill(2) for x in a.only.split(",") if x.strip()]
    camps = load_picks(only)
    if not camps:
        sys.exit("No campaign matched --only.")
    extra = {}
    if a.add:
        if len(camps) != 1:
            sys.exit("--add needs exactly one campaign in --only.")
        extra[camps[0]["nn"]] = [k.strip().lower() for k in a.add.split(";") if k.strip()]

    todo = {c["nn"]: [k.lower() for k in c["picks"] + c["bench"]] + extra.get(c["nn"], []) for c in camps}
    all_kws = sorted({k for ks in todo.values() for k in ks})
    cache = load_cache()
    need_vol = [k for k in all_kws if not fresh_entry(cache, "volume", k, a.fresh)]
    need_serp = [k for k in all_kws if not fresh_entry(cache, "serp", k, a.fresh)]
    need_read = {nn: [k for k in ks if k in need_serp or not fresh_entry(cache, "intent", k, a.fresh)]
                 for nn, ks in todo.items()}
    n_read = sum(len(v) for v in need_read.values())
    est = {"volume": VOLUME_TASK_USD if need_vol else 0.0, "serp": round(len(need_serp) * SERP_USD, 4),
           "claude": sum(estimate_claude(len(v)) for v in need_read.values() if v)}
    print(f"{len(all_kws)} keywords in {len(camps)} campaigns. To fetch: volume {len(need_vol)}, results pages "
          f"{len(need_serp)}, Claude reads {n_read}.")
    print(f"Estimate: ${sum(est.values()):.2f} ({', '.join(f'{k} ${v:.2f}' for k, v in est.items())}); cap ${a.max_cost:.2f}.")
    if a.dry_run:
        report_key_sources(["DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD", "ANTHROPIC_API_KEY"])
        return

    meter = CostMeter(a.max_cost)
    try:
        meter.assert_affordable(sum(est.values()), "this run")
    except BudgetExceeded as e:
        sys.exit(str(e))
    today = date.today().isoformat()

    if need_vol or need_serp:
        hint = "Sign up at dataforseo.com, then put both in ~/.monarc/secrets.env."
        dfs = DataForSEO(get_secret("DATAFORSEO_LOGIN", True, hint), get_secret("DATAFORSEO_PASSWORD", True, hint))
    if need_vol:
        got, cost = dfs.volume(need_vol)
        meter.add("volume", cost)
        for k in need_vol:
            cache["volume"][k] = {**(got.get(k) or {"searches": None}), "fetched": today}
        save_cache(cache)
        print(f"Volume: {len(got)} of {len(need_vol)} keywords had data (${cost:.3f}).")
    if need_serp:
        def one(k):
            return k, *dfs.serp(k)
        with ThreadPoolExecutor(max_workers=6) as ex:
            for k, page, cost in ex.map(one, need_serp):
                meter.add("serp", cost or SERP_USD)
                cache["serp"][k] = {**page, "fetched": today}
                cache["intent"].pop(k, None)     # a new page needs a new read
        save_cache(cache)
        print(f"Results pages: {len(need_serp)} fetched (${meter.items.get('serp', 0):.3f}).")
    if n_read:
        import anthropic
        client = anthropic.Anthropic(api_key=get_secret("ANTHROPIC_API_KEY", required=True))
        for nn, ks in need_read.items():
            if not ks:
                continue
            got, cost = read_intent(client, [(k, cache["serp"][k]) for k in ks])
            meter.add("claude", cost)
            for k in ks:
                if k in got:
                    cache["intent"][k] = {**got[k], "fetched": today}
            save_cache(cache)
            missing = [k for k in ks if k not in got]
            print(f"Claude read {nn}: {len(ks) - len(missing)} of {len(ks)} pages (${cost:.3f})"
                  + (f"; not returned: {', '.join(missing)}" if missing else ""))

    results_by_nn = {}
    for c in camps:
        res = []
        for k in todo[c["nn"]]:
            vol, serp, intent = cache["volume"].get(k), cache["serp"].get(k), cache["intent"].get(k)
            res.append({"kw": k, "vol": vol, "serp": serp, "who": (intent or {}).get("who", ""),
                        "verdict": verdict(vol, serp, intent)})
        results_by_nn[c["nn"]] = res
        if not a.no_write:
            n = write_csv(c["service"], res)
            print(f"{c['nn']} {c['service']}: {n} CSV rows updated.")
    path = report(camps, results_by_nn, meter, extra)
    print(f"Report: {path}. Spent ${meter.total:.2f} of ${a.max_cost:.2f}.")


if __name__ == "__main__":
    main()
