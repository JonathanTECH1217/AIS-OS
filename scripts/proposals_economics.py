"""Economics on the Portal proposal dataset: revenue at N wins, LTV by client, offering show rate,
offering share of a package, and an install-hours model.

Reads the raw exports through scripts/proposals_analyze.py helpers. Prints JSON.
Usage: python scripts/proposals_economics.py [wins_per_year=100] [margin=0.30]
"""
import json, re, statistics, sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import proposals_analyze as pa  # noqa: E402

WINS = int(sys.argv[1]) if len(sys.argv) > 1 else 100
MARGIN = float(sys.argv[2]) if len(sys.argv) > 2 else 0.30

# client keys seen in titles (former employer's clients; keys stay inside this folder)
CLIENT_KEYS = [
    "danny diaz", "frampton", "kettler", "westin", "alta", "nova", "abners", "kinney", "patrick fletcher", "waldron",
    "monet", "chislom", "chisholm", "baldwin homes", "hepburn", "gibbons-neff", "feldman", "kemira", "ledo", "juniper",
    "marlow", "berger", "chuck r", "kiddie academy", "chadwick", "jeff barnett", "mark emmons", "stournaras", "gyc",
    "evergreen", "atik rees", "oneill", "dibiagio", "hein", "morris", "chen", "hkn", "ash halim", "riewerts", "faulconer",
    "festival wine", "licht", "back nine", "john heller", "hammer and nails", "snow hill", "joseph", "mezzitti",
    "pinehurst", "cummings", "mcconnell", "brad davis", "amos", "mooney", "pumphrey", "bragg", "penzell",
    "calkins-hepting", "larkin", "hci", "kenny", "nichols", "carrion", "cyrus", "gate one", "carter", "annapolis harbor",
    "ford seafood", "bayview", "1150 chain bridge", "5621 jordan", "fernandez", "kell ", "aagaming", "the yards",
    "thomas", "crossroads", "carrollton", "gate one", "muse", "villamater", "golfzon",
]
LABOR_TYPES = {"lead technician": "tech", "helper": "helper", "programming": "programming",
               "project management": "pm", "design": "design"}
CABLE_RE = re.compile(r"per foot|cat ?6|cat ?5|14/2|16/4|16-4|14-2|spool|\bft\b|feet", re.I)
NON_DEVICE_RE = re.compile(r"misc|cable|wire|per foot|spool|bracket|plate|jack|mount|conduit|connector|accessor|"
                           r"enclosure back box|flex bracket|license|subscription|fee|tax|shipping|electrical project", re.I)


def client_key(title):
    t = title.lower()
    for k in CLIENT_KEYS:
        if k in t:
            return k.strip()
    return None


def main():
    files = sorted({p.resolve() for p in list(pa.RAW.glob("*.CSV")) + list(pa.RAW.glob("*.csv"))})
    by_num = {}
    for f in files:
        m = re.match(r"Proposal #(\d+)\s*-\s*(.*)\.csv$", f.name, re.I)
        if not m:
            continue
        num, title = int(m.group(1)), re.sub(r"\s*\(\d+\)\s*$", "", m.group(2).strip())
        if num not in by_num or f.stat().st_size > by_num[num][1].stat().st_size:
            by_num[num] = (title, f)
    props = []
    for num in sorted(by_num):
        title, f = by_num[num]
        loaded = pa.load_file(f)
        if not loaded:
            continue
        summary, items = loaded
        cats = Counter()
        area_cat = {}
        hours = Counter()
        parts = 0.0
        devices = 0
        cable_ft = 0.0
        areas = set()
        elec_pass = 0.0
        for r in items:
            it = (r.get("ItemType") or "").strip()
            sell = pa.fnum(r.get("SellTotal")) or 0.0
            qty = pa.fnum(r.get("AreaQty")) or 0.0
            area = (r.get("Area") or "").strip()
            if area:
                areas.add(area.lower())
            text = " ".join([r.get("Brand") or "", r.get("Model or Labor/Fee Name") or "", r.get("ShortDescription") or ""])
            if it == "Labor":
                name = (r.get("Model or Labor/Fee Name") or "").strip().lower()
                for k, v in LABOR_TYPES.items():
                    if name.startswith(k):
                        hours[v] += qty
                        break
                continue
            if it == "Fee":
                continue
            parts += sell
            if "electrical project" in text.lower():
                elec_pass += sell
            if CABLE_RE.search(text) and qty >= 25:
                cable_ft += qty
            elif not NON_DEVICE_RE.search(text) and 0 < qty <= 60:
                devices += int(qty)
            cat = pa.classify_item(r, title)
            if cat:
                cats[cat] += sell
                area_cat.setdefault(area, Counter())[cat] += sell
        for r in items:
            if (r.get("ItemType") or "").strip() == "Labor":
                area = (r.get("Area") or "").strip()
                sell = pa.fnum(r.get("SellTotal")) or 0.0
                ac = area_cat.get(area)
                if ac:
                    cats[ac.most_common(1)[0][0]] += sell
                elif cats:
                    cats[cats.most_common(1)[0][0]] += sell
        grand = pa.fnum(summary.get("GrandTotal")) if summary else None
        if grand is None:
            grand = sum(pa.fnum(r.get("SellTotal")) or 0 for r in items)
        text_all = title + " " + " ".join(areas)
        commercial = bool(re.search(r"westin|ledo|\balta\b|\bnova\b|abners|gaming|kiddie|library|kemira|marina|boat yard|showroom|festival|the yards|juniper|marlow|conference|parking|menu board|bulletin|division 28", text_all, re.I))
        props.append({
            "num": num, "title": title, "key": pa.norm_title(title), "client": client_key(title), "grand": grand,
            "cats": dict(cats), "primary": cats.most_common(1)[0][0] if cats else "", "hours": dict(hours),
            "tech_hours": hours["tech"] + hours["helper"], "all_hours": sum(hours.values()), "parts": parts,
            "elec_pass": elec_pass, "devices": devices, "cable_ft": cable_ft, "areas": len(areas),
            "commercial": commercial, "builder": bool(pa.BUILDER_RE.search(title)) and not commercial,
        })
    groups = defaultdict(list)
    for p in props:
        groups[p["key"] or f"#{p['num']}"].append(p)
    for ps in groups.values():
        ps.sort(key=lambda x: x["num"])
        for i, p in enumerate(ps):
            p["latest"] = i == len(ps) - 1
    live = [p for p in props if p["latest"] and p["grand"] > 0]
    res = [p for p in live if not p["commercial"]]
    months = 23.3  # 2024-09-10 to 2026-08-19
    per_year = len(live) / months * 12

    # ---- A. revenue at N wins
    def scen(pool, label):
        vals = sorted((p["grand"] for p in pool), reverse=True)
        mean = statistics.mean(vals)
        med = statistics.median(vals)
        top = sum(vals[:WINS])
        bottom = sum(vals[-WINS:])
        return {"pool": label, "pool_size": len(vals), "mean_ticket": round(mean), "median_ticket": round(med),
                "revenue_at_mean": round(WINS * mean), "gross_profit_at_mean": round(WINS * mean * MARGIN),
                "revenue_if_wins_are_median_jobs": round(WINS * med),
                "revenue_if_wins_are_the_largest": round(top), "revenue_if_wins_are_the_smallest": round(bottom),
                "revenue_without_top_10pct": round(WINS * statistics.mean(vals[len(vals) // 10:]))}
    A = {"wins_per_year": WINS, "margin": MARGIN, "live_proposals": len(live), "live_per_year": round(per_year),
         "implied_win_rate": round(WINS / per_year, 2),
         "scenarios": [scen(live, "all live proposals"), scen(res, "residential only"),
                       scen([p for p in res if p["grand"] >= 25000], "residential $25k and up"),
                       scen([p for p in res if p["grand"] >= 5000], "residential $5k and up")]}

    # ---- B. LTV by named client
    clients = defaultdict(lambda: {"proposals": 0, "live": 0, "dollars": 0.0, "nums": [], "cats": Counter()})
    for p in props:
        if p["client"]:
            c = clients[p["client"]]
            c["proposals"] += 1
            c["nums"].append(p["num"])
            if p["latest"] and p["grand"] > 0:
                c["live"] += 1
                c["dollars"] += p["grand"]
                for k, v in p["cats"].items():
                    c["cats"][k] += v
    named = [(k, v) for k, v in clients.items() if v["live"] > 0]
    res_named = [(k, v) for k, v in named if not any(p["commercial"] for p in props if p["client"] == k)]
    dollars = sorted(v["dollars"] for k, v in named)
    res_dollars = sorted(v["dollars"] for k, v in res_named)
    repeat = sum(1 for k, v in named if v["live"] >= 2)
    B = {"named_clients": len(named), "residential_named": len(res_named),
         "share_of_live_dollars_with_a_name": round(sum(dollars) / sum(p["grand"] for p in live), 2),
         "client_dollars_mean": round(statistics.mean(dollars)), "client_dollars_median": round(statistics.median(dollars)),
         "residential_client_dollars_mean": round(statistics.mean(res_dollars)),
         "residential_client_dollars_median": round(statistics.median(res_dollars)),
         "clients_with_2plus_live_jobs": repeat, "repeat_share": round(repeat / len(named), 2),
         "live_jobs_per_client_mean": round(statistics.mean(v["live"] for k, v in named), 2),
         "gross_ltv_mean_at_margin": round(statistics.mean(res_dollars) * MARGIN),
         "gross_ltv_median_at_margin": round(statistics.median(res_dollars) * MARGIN),
         "top_clients": [{"client": k[:3] + "***", "live_jobs": v["live"], "proposals": v["proposals"], "dollars": round(v["dollars"]),
                          "systems": [c for c, _ in v["cats"].most_common(3)]}
                         for k, v in sorted(named, key=lambda kv: -kv[1]["dollars"])[:12]]}
    # CAC scenarios for an integrator on Monarc Level 1 ($2,500/mo + $1,000/mo ads = $42,000/yr)
    monarc_year = 42000
    cac_rows = []
    for wins in (4, 6, 12, 24, 36):
        cac = monarc_year / wins
        cac_rows.append({"wins_from_monarc_per_year": wins, "cac": round(cac),
                         "ltv_cac_first_job_median_res": round(statistics.median(p["grand"] for p in res) * MARGIN / cac, 1),
                         "ltv_cac_first_job_25k_plus": round(statistics.median(p["grand"] for p in res if p["grand"] >= 25000) * MARGIN / cac, 1),
                         "ltv_cac_client_lifetime_median": round(statistics.median(res_dollars) * MARGIN / cac, 1),
                         "ltv_cac_client_lifetime_mean": round(statistics.mean(res_dollars) * MARGIN / cac, 1)})
    B["monarc_level1_per_year"] = monarc_year
    B["cac_scenarios"] = cac_rows

    # ---- C. show rate per offering
    cat_names = sorted({c for p in live for c in p["cats"]})
    C = []
    for c in cat_names:
        in_any = sum(1 for p in live if p["cats"].get(c, 0) >= 500)
        in_res = sum(1 for p in res if p["cats"].get(c, 0) >= 500)
        head = sum(1 for p in live if p["primary"] == c)
        C.append({"offering": c, "show_rate_all": round(in_any / len(live), 2), "show_rate_residential": round(in_res / len(res), 2),
                  "headline_rate": round(head / len(live), 2), "dollars": round(sum(p["cats"].get(c, 0) for p in live))})
    C.sort(key=lambda r: -r["show_rate_all"])

    # ---- D. share of a package
    def pkg(min_sys):
        rows = []
        pool = [p for p in res if sum(1 for v in p["cats"].values() if v >= 2000) >= min_sys]
        for c in cat_names:
            shares = [p["cats"][c] / sum(p["cats"].values()) for p in pool if p["cats"].get(c, 0) >= 2000 and sum(p["cats"].values()) > 0]
            if shares:
                rows.append({"offering": c, "in_packages": len(shares), "mean_share": round(100 * statistics.mean(shares), 1),
                             "median_share": round(100 * statistics.median(shares), 1)})
        rows.sort(key=lambda r: -r["mean_share"])
        return {"packages": len(pool), "rows": rows}
    D = {"3plus_systems": pkg(3), "2plus_systems": pkg(2)}

    # ---- E. install hours model (residential, live, with labor and parts, electrical pass-through removed)
    pool = [p for p in res if p["tech_hours"] >= 4 and p["parts"] - p["elec_pass"] >= 1000]
    y = np.array([p["tech_hours"] for p in pool])
    parts_k = np.array([(p["parts"] - p["elec_pass"]) / 1000 for p in pool])
    dev = np.array([p["devices"] for p in pool], dtype=float)
    ar = np.array([p["areas"] for p in pool], dtype=float)
    cab = np.array([p["cable_ft"] / 100 for p in pool])

    def fit(X, names):
        X1 = np.column_stack([np.ones(len(y))] + X)
        beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
        pred = X1 @ beta
        ss_res = float(((y - pred) ** 2).sum())
        ss_tot = float(((y - y.mean()) ** 2).sum())
        return {"intercept_hours": round(float(beta[0]), 1), **{f"hours_per_{n}": round(float(b), 2) for n, b in zip(names, beta[1:])},
                "r2": round(1 - ss_res / ss_tot, 2), "n": len(y)}
    E = {"pool": len(pool),
         "ratios": {"tech_hours_per_1k_parts_median": round(float(np.median(y / parts_k)), 2),
                    "tech_hours_per_device_median": round(float(np.median(y[dev > 0] / dev[dev > 0])), 2),
                    "tech_hours_per_area_median": round(float(np.median(y / np.maximum(ar, 1))), 1),
                    "labor_share_of_ticket_median": round(float(np.median([sum(p["hours"].values()) and (p["grand"] and 1) and 0 or 0 for p in pool])), 2)},
         "fit_parts": fit([parts_k], ["1k_parts"]),
         "fit_devices_areas": fit([dev, ar], ["device", "area"]),
         "fit_full": fit([parts_k, dev, ar, cab], ["1k_parts", "device", "area", "100ft_cable"]),
         "hours_mix": {k: round(sum(p["hours"].get(k, 0) for p in pool)) for k in ("tech", "helper", "programming", "pm", "design")},
         "examples": [{"num": p["num"], "grand": round(p["grand"]), "parts": round(p["parts"] - p["elec_pass"]), "devices": p["devices"],
                       "areas": p["areas"], "cable_ft": round(p["cable_ft"]), "tech_hours": round(p["tech_hours"]),
                       "prog_hours": round(p["hours"].get("programming", 0))}
                      for p in sorted(pool, key=lambda p: -p["grand"])[:10]],
         "with_address_in_title": [p["title"] for p in live if re.search(r"\d{3,5}\s+\w+\s+(rd|road|st|street|ave|dr|drive|ln|lane|ct|bridge)", p["title"], re.I)]}
    # labor share of ticket, properly
    E["ratios"]["labor_dollars_share_of_ticket_median"] = round(float(np.median([
        (sum(pa.fnum(r.get("SellTotal")) or 0 for r in pa.load_file(by_num[p["num"]][1])[1] if (r.get("ItemType") or "").strip() == "Labor") / p["grand"])
        for p in pool if p["grand"] > 0])), 2)
    print(json.dumps({"A_revenue": A, "B_ltv": B, "C_show_rate": C, "D_package_share": D, "E_install_model": E}, indent=1))


if __name__ == "__main__":
    main()
