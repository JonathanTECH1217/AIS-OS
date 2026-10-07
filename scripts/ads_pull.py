"""The morning read-back: pull spend, clicks, and conversions for every published campaign and keyword, and the last
7 days of real search terms, from Google Ads.

Usage:
  python scripts/ads_pull.py            pull now; print what came back (no Airtable writes from the command line)

What it writes:
- each campaign file's "google.live" (spend, impressions, clicks, conversions, all time; read time) and "google.status"
  as Google reports it, so a pause made inside Google Ads shows on the Ads screen too;
- projects/google-ads/search-terms/<date>.json: the searches that cost money in the last 7 days, most expensive first,
  minus any a current negative already blocks. The Ads screen lists them with a Block button (the Friday list).
The CRM server (scripts/crm_server.py) runs this once a day, the first time it is up after 6 am, in the background, and
from the Pull now button; it then writes the numbers into the Airtable Campaigns and Keywords rows, only the rows
whose numbers changed, ten to a call (Airtable Free allows about 1,000 calls a month).
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ads_negative_check as negcheck  # noqa: E402
import ads_publish as ap  # noqa: E402

STATE = ap.ADS / "ads-pull.json"
TERMS_DIR = ap.ADS / "search-terms"


def _cid(rn):
    return (rn or "").rsplit("/", 1)[-1]


def pull(g=None):
    docs = [d for d in ap.all_campaigns() if (d.get("google") or {}).get("campaign")]
    if not docs:
        return {"campaigns": [], "keywords": [], "terms": [], "note": "Nothing published yet."}
    g = g or ap._google()
    by_id = {_cid(d["google"]["campaign"]): d for d in docs}
    ids = ", ".join(by_id)
    camps = g.search("SELECT campaign.id, campaign.status, metrics.cost_micros, metrics.impressions, metrics.clicks, "
                     f"metrics.conversions FROM campaign WHERE campaign.id IN ({ids})")
    kws = g.search("SELECT campaign.id, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, "
                   "metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.conversions FROM keyword_view "
                   f"WHERE campaign.id IN ({ids})")
    terms = g.search("SELECT campaign.id, search_term_view.search_term, metrics.impressions, metrics.clicks, "
                     "metrics.cost_micros, metrics.conversions FROM search_term_view "
                     f"WHERE segments.date DURING LAST_7_DAYS AND campaign.id IN ({ids})")
    stamp = ap.now()

    def m(r):
        x = r.get("metrics", {})
        return {"cost": round(int(x.get("costMicros", 0) or 0) / 1e6, 2), "impressions": int(x.get("impressions", 0) or 0),
                "clicks": int(x.get("clicks", 0) or 0), "conversions": round(float(x.get("conversions", 0) or 0), 1)}

    out_c = []
    for r in camps:
        cid = str(r["campaign"]["id"])
        d = ap.load(by_id[cid]["nn"])
        live = {**m(r), "at": stamp}
        d["google"]["live"] = live
        d["google"]["status"] = r["campaign"].get("status", d["google"].get("status"))
        ap.save(d)
        out_c.append({"nn": d["nn"], "name": d["name"], "platform_id": cid, "status": d["google"]["status"], **live})

    out_k = {}
    for r in kws:
        nn = by_id[str(r["campaign"]["id"])]["nn"]
        text = r["adGroupCriterion"]["keyword"]["text"]
        k = out_k.setdefault((nn, text), {"nn": nn, "keyword": text, "cost": 0.0, "impressions": 0, "clicks": 0, "conversions": 0.0})
        for f, v in m(r).items():
            k[f] = round(k[f] + v, 2)

    out_t = []
    for r in terms:
        d = by_id[str(r["campaign"]["id"])]
        term = r["searchTermView"]["searchTerm"]
        x = m(r)
        if not x["clicks"] and not x["cost"]:
            continue
        q = negcheck.words(term)
        if any(negcheck.blocks(t, q) for grp in ap.negative_groups(d) for t in grp["terms"]):
            continue                                   # already blocked since it ran
        out_t.append({"nn": d["nn"], "term": term, **x})
    out_t.sort(key=lambda t: (-t["cost"], -t["clicks"]))
    TERMS_DIR.mkdir(parents=True, exist_ok=True)
    (TERMS_DIR / f"{date.today().isoformat()}.json").write_text(
        json.dumps({"at": stamp, "days": 7, "terms": out_t}, indent=1) + "\n", encoding="utf-8")
    ap._write_json(STATE, {"last_run": stamp, "campaigns": len(out_c), "terms": len(out_t)})
    ap.log("--", "pull", f"{len(out_c)} campaigns, {len(out_k)} keywords, {len(out_t)} search terms", by="AIOS")
    return {"campaigns": out_c, "keywords": list(out_k.values()), "terms": out_t}


def due(now=None):
    """True once a day, the first time after 6 am local."""
    now = now or datetime.now()
    if now.hour < 6:
        return False
    last = (ap._read_json(STATE, {}) or {}).get("last_run", "")
    return not last.startswith(now.date().isoformat())


def main():
    try:
        r = pull()
    except ap.Refused as e:
        sys.exit(f"Refused: {e}")
    except Exception as e:  # noqa: BLE001
        lines = getattr(e, "lines", None)
        sys.exit("Google refused:\n  " + "\n  ".join(lines) if lines else f"{type(e).__name__}: {e}")
    if r.get("note"):
        print(r["note"])
        return
    for c in r["campaigns"]:
        print(f"{c['nn']} {c['name']:<28} {c['status']:<8} ${c['cost']:>8.2f}  {c['impressions']:>6} impr  "
              f"{c['clicks']:>4} clicks  {c['conversions']} conv")
    print(f"{len(r['keywords'])} keyword rows; {len(r['terms'])} search terms that cost money and are not blocked yet.")
    for t in r["terms"][:15]:
        print(f"  {t['nn']}  ${t['cost']:>6.2f}  {t['clicks']:>3} clicks  {t['term']}")


if __name__ == "__main__":
    main()
