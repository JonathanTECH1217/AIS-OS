"""Monarc Edge ledger and record (2026-10-04): the money book and the four gate lights.

The ledger is append-only rows in edge.sqlite (kind: deposit, fill, fee, settlement, adjust), each with the balance
after it. Equity is the balance plus the cost of the contracts still held. The record reads settled cards into
bands of the model's chance, Brier scores, CLV by hours-before-kickoff band and the equity series; the gate turns
four of those into lights (count, calibration, profit, CLV) and auto mode stays locked until all four are green.
Paper cards (dry-run fills) count toward the gate like real ones (decided 2026-10-04). Shapes follow
projects/edge/API.md.

Calibration reads "hit" as the outcome happening (the market settled Yes), since model_p is the chance of the
outcome. The top-line hit_rate and the market bands read "hit" as our side paying.

  python scripts/edge_ledger.py          print the record and the gate for the current data folder
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edge_common as ec  # noqa: E402


# ---------------------------------------------------------------- ledger

def init_bankroll(cfg):
    """One deposit row of bankroll_usd when the ledger is empty. Returns True when it wrote it."""
    c = ec.db()
    if c.execute("SELECT COUNT(*) AS n FROM ledger").fetchone()["n"]:
        return False
    amt = float(cfg.get("bankroll_usd") or 0)
    add("deposit", amt, note="starting bankroll")
    ec.kv_set("bankroll.peak", amt)
    return True


def balance():
    r = ec.db().execute("SELECT balance_after FROM ledger ORDER BY id DESC LIMIT 1").fetchone()
    return round(float(r["balance_after"]), 2) if r else 0.0


def add(kind, amount, card_id=None, note=None, ts=None):
    """Append one row and return it. amount is signed: money in positive, money out negative."""
    c = ec.db()
    amount = round(float(amount), 2)
    bal = round(balance() + amount, 2)
    ts = ts or ec.iso(ec.now())
    cur = c.execute("INSERT INTO ledger (ts, kind, card_id, amount_usd, balance_after, note) VALUES (?,?,?,?,?,?)",
                    (ts, kind, card_id, amount, bal, note))
    c.commit()
    return {"id": cur.lastrowid, "ts": ts, "kind": kind, "card_id": card_id, "amount_usd": amount,
            "balance_after": bal, "note": note}


def open_cost():
    """Cost basis of the contracts still held (filled or partial cards not yet settled)."""
    r = ec.db().execute("SELECT COALESCE(SUM(fill_count * COALESCE(avg_fill, 0)), 0) AS c FROM cards "
                        "WHERE state IN ('filled', 'partial')").fetchone()
    return round(float(r["c"] or 0), 2)


def equity():
    return round(balance() + open_cost(), 2)


def peak():
    """The highest equity seen, kept in kv and raised whenever equity is read."""
    eq = equity()
    pk = float(ec.kv_get("bankroll.peak") or 0)
    if eq > pk:
        pk = eq
        ec.kv_set("bankroll.peak", pk)
    return round(pk, 2)


def drawdown_pct():
    pk = peak()
    if pk <= 0:
        return 0.0
    return round(100.0 * (pk - equity()) / pk, 2)


def drawdown_allows(cfg):
    """False once equity sits pct or more under its peak (and the stop is on). The auto pass asks this."""
    dd = cfg.get("drawdown") or {}
    if not dd.get("on", True):
        return True
    return drawdown_pct() < float(dd.get("pct", 25.0))


def drawdown_check(ctx):
    """After a settlement: halt on the drawdown stop. Only in auto mode when auto_only is set. Returns True on a halt."""
    cfg = ctx.cfg
    dd = cfg.get("drawdown") or {}
    if not dd.get("on", True):
        return False
    if dd.get("auto_only", True) and cfg.get("mode") != "auto":
        return False
    pct = drawdown_pct()
    if pct >= float(dd.get("pct", 25.0)):
        if not ec.kv_get("halted"):
            import edge_cards
            edge_cards.halt(ctx, "drawdown", f"equity ${equity():.2f} is {pct:.1f}% under the peak ${peak():.2f} "
                                             f"(stop at {float(dd.get('pct', 25.0)):g}%)")
        return True
    return False


def period_bankroll(date):
    """The balance at the start of the UTC day `date` (YYYY-MM-DD), cached in kv once that day has begun. A day not
    begun, or a day before the ledger started, gets the current balance (not cached)."""
    key = f"bankroll.{date}"
    v = ec.kv_get(key)
    if v is not None:
        return float(v)
    start = f"{date}T00:00:00Z"
    if ec.parse_iso(start) > ec.now():
        return balance()
    r = ec.db().execute("SELECT balance_after FROM ledger WHERE ts < ? ORDER BY id DESC LIMIT 1", (start,)).fetchone()
    if not r:
        return balance()
    ec.kv_set(key, float(r["balance_after"]))
    return float(r["balance_after"])


# ---------------------------------------------------------------- record

def settled_cards():
    return ec.rows(ec.db().execute("SELECT * FROM cards WHERE state='settled' AND result IS NOT NULL "
                                   "ORDER BY expires_at, id"))


def _mean(xs):
    xs = [float(x) for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _band_key(b):
    return int(str(b).split("-")[0])


def bands_of(cards, cfg):
    """Bands of model_p (width band_width_points): n, the model's mean chance, the share that happened, the Wilson
    interval, within the tolerance, and the light (grey when thin)."""
    g = cfg["gate"]
    width = int(g["band_width_points"])
    tol = float(g["band_tolerance_points"])
    min_n = int(g["min_band_n"])
    groups = {}
    for c in cards:
        if c.get("model_p") is None:
            continue
        groups.setdefault(ec.band_of(float(c["model_p"]) * 100, width), []).append(c)
    out = []
    for b in sorted(groups, key=_band_key):
        cs = groups[b]
        n = len(cs)
        hits = sum(1 for c in cs if c["result"] == "yes")
        mm = 100.0 * _mean([c["model_p"] for c in cs])
        hr = 100.0 * hits / n
        lo, hi = ec.wilson(hits, n)
        within = abs(hr - mm) <= tol
        out.append({"band": b, "n": n, "model_mean": round(mm, 1), "hit_rate": round(hr, 1),
                    "lo": round(100 * lo, 1), "hi": round(100 * hi, 1), "within": within,
                    "light": "grey" if n < min_n else ("green" if within else "red")})
    return out


def pooled_of(cards, cfg):
    tol = float(cfg["gate"]["pooled_tolerance_points"])
    cs = [c for c in cards if c.get("model_p") is not None]
    n = len(cs)
    if not n:
        return {"n": 0, "model_mean": None, "hit_rate": None, "within": False}
    mm = 100.0 * _mean([c["model_p"] for c in cs])
    hr = 100.0 * sum(1 for c in cs if c["result"] == "yes") / n
    return {"n": n, "model_mean": round(mm, 1), "hit_rate": round(hr, 1), "within": abs(hr - mm) <= tol}


def market_bands_of(cards, cfg):
    """Bands of the price we paid (the market's chance of our side), and how often our side paid."""
    width = int(cfg["gate"]["band_width_points"])
    groups = {}
    for c in cards:
        if c.get("market_price") is None:
            continue
        groups.setdefault(ec.band_of(float(c["market_price"]) * 100, width), []).append(c)
    out = []
    for b in sorted(groups, key=_band_key):
        cs = groups[b]
        out.append({"band": b, "n": len(cs), "market_mean": round(100.0 * _mean([c["market_price"] for c in cs]), 1),
                    "hit_rate": round(100.0 * sum(1 for c in cs if c["side"] == c["result"]) / len(cs), 1)})
    return out


def clv_of(cards):
    cs = [c for c in cards if c.get("clv_points") is not None]
    vals = [float(c["clv_points"]) for c in cs]
    by = {}
    for c in cs:
        by.setdefault(c.get("hours_band") or "?", []).append(float(c["clv_points"]))
    order = [b for _, b in ec.HOURS_BANDS]
    by_hours = [{"band": b, "n": len(v), "mean": round(_mean(v), 2)} for b, v in
                sorted(by.items(), key=lambda kv: order.index(kv[0]) if kv[0] in order else 99)]
    return {"mean": round(_mean(vals), 2) if vals else None, "n": len(vals),
            "positive_share": round(sum(1 for v in vals if v > 0) / len(vals), 3) if vals else None,
            "by_hours": by_hours}


def brier_of(cards):
    model, market = [], []
    for c in cards:
        y = 1.0 if c["result"] == "yes" else 0.0
        if c.get("model_p") is not None:
            model.append((float(c["model_p"]) - y) ** 2)
        if c.get("market_mid") is not None:
            market.append((float(c["market_mid"]) - y) ** 2)
    return {"model": round(_mean(model), 4) if model else None, "market": round(_mean(market), 4) if market else None,
            "n": len(model)}


def _group_pnl(cards, key):
    groups = {}
    for c in cards:
        groups.setdefault(c.get(key), []).append(float(c.get("pnl_usd") or 0))
    return [{key: k, "n": len(v), "pnl_usd": round(sum(v), 2)} for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))]


GAP_BANDS = ((10.0, "7 to 10"), (15.0, "10 to 15"), (float("inf"), "15 and up"))


def gap_band(gap):
    g = float(gap or 0)
    for top, label in GAP_BANDS:
        if g < top:
            return label
    return GAP_BANDS[-1][1]


def _group_gap(cards):
    """Settled bets by the size of the gap they were taken at: the review's question is whether big gaps lose."""
    groups = {label: [] for _, label in GAP_BANDS}
    for c in cards:
        groups[gap_band(c.get("gap_points"))].append(c)
    out = []
    for _, label in GAP_BANDS:
        v = groups[label]
        wins = sum(1 for x in v if x.get("side") == x.get("result"))
        out.append({"gap": label, "n": len(v), "pnl_usd": round(sum(float(x.get("pnl_usd") or 0) for x in v), 2),
                    "hit_rate": round(100.0 * wins / len(v), 1) if v else None})
    return out


def gate(cfg):
    """The four lights. passed only when all four are ok. Grey bands (under min_band_n) are ignored."""
    g = cfg["gate"]
    cards = settled_cards()
    n = len(cards)
    bands = bands_of(cards, cfg)
    pooled = pooled_of(cards, cfg)
    clv = clv_of(cards)
    pnl = round(sum(float(c.get("pnl_usd") or 0) for c in cards), 2)
    need_clv = float(g["min_clv_points"])
    lights = {
        "count": {"ok": n >= int(g["min_settled"]), "value": n, "need": int(g["min_settled"])},
        "calibration": {"ok": n > 0 and not any(b["light"] == "red" for b in bands) and bool(pooled["within"]),
                        "bands": bands, "pooled": pooled},
        "profit": {"ok": pnl > 0, "value": pnl},
        "clv": {"ok": clv["mean"] is not None and clv["mean"] >= need_clv, "value": clv["mean"], "need": need_clv,
                "n": clv["n"]},
    }
    reasons = []
    if not lights["count"]["ok"]:
        reasons.append(f"{n} settled cards, {int(g['min_settled'])} needed")
    if not lights["calibration"]["ok"]:
        red = [b["band"] for b in bands if b["light"] == "red"]
        if red:
            reasons.append("off by more than the tolerance in band " + ", ".join(red))
        elif not pooled["within"]:
            reasons.append("pooled hit rate outside the tolerance" if n else "nothing settled yet")
    if not lights["profit"]["ok"]:
        reasons.append(f"return after fees is ${pnl:.2f}")
    if not lights["clv"]["ok"]:
        reasons.append(f"mean CLV {clv['mean'] if clv['mean'] is not None else 'unknown'} points, {need_clv:g} needed")
    return {"settled": n, "lights": lights, "passed": all(l["ok"] for l in lights.values()), "reasons": reasons}


def record(cfg, full=True):
    """The record in API.md. full=False leaves out equity, ledger and market_bands (the state bundle's summary)."""
    c = ec.db()
    cards = settled_cards()
    n = len(cards)
    wins = sum(1 for x in cards if x["side"] == x["result"])
    pnl = round(sum(float(x.get("pnl_usd") or 0) for x in cards), 2)
    staked = round(sum(float(x.get("fill_count") or 0) * float(x.get("avg_fill") or 0) for x in cards), 2)
    bets = c.execute("SELECT COUNT(*) AS n FROM cards WHERE fill_count > 0").fetchone()["n"]
    first = c.execute("SELECT amount_usd FROM ledger WHERE kind='deposit' ORDER BY id LIMIT 1").fetchone()
    bal, eq, pk = balance(), equity(), peak()
    out = {"settled": n, "bets": bets, "hit_rate": round(100.0 * wins / n, 1) if n else None, "pnl_usd": pnl,
           "return_pct": round(100.0 * pnl / staked, 1) if staked else None, "staked_usd": staked,
           "bankroll": {"start": float(first["amount_usd"]) if first else float(cfg.get("bankroll_usd") or 0),
                        "balance": bal, "equity": eq, "peak": pk,
                        "drawdown_pct": round(100.0 * (pk - eq) / pk, 1) if pk else 0.0},
           "bands": bands_of(cards, cfg), "clv": clv_of(cards), "brier": brier_of(cards),
           "by_side": _group_pnl(cards, "side"), "by_outcome": _group_pnl(cards, "outcome"),
           "by_gap": _group_gap(cards)}
    if full:
        led = ec.rows(c.execute("SELECT * FROM ledger ORDER BY id"))
        # the line the page draws is equity (cash plus the open bets at cost), so a bet moves it only when it settles
        # or pays a fee, never the moment the stake leaves the cash pile
        open_by_card, series = {}, []
        for r in led:
            k, cid, amt = r["kind"], r["card_id"], float(r["amount_usd"] or 0)
            if k == "fill" and cid:
                open_by_card[cid] = open_by_card.get(cid, 0.0) - amt
            elif k == "settlement" and cid:
                open_by_card.pop(cid, None)
            held = sum(open_by_card.values())
            series.append({"ts": r["ts"], "balance": round(float(r["balance_after"]) + held, 2),
                           "cash": r["balance_after"]})
        out["equity"] = series
        out["ledger"] = led[-100:][::-1]
        out["market_bands"] = market_bands_of(cards, cfg)
    return out


if __name__ == "__main__":
    cfg_ = ec.load_config()
    print(json.dumps({"record": record(cfg_, full=False), "gate": gate(cfg_)}, indent=1, default=str))
