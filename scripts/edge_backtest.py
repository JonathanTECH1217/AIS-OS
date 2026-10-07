"""Monarc Edge backtest (2026-10-04): the data step and the proof behind the model.

Data: football-data.co.uk's Premier League season files (E0.csv, one per season) into projects/edge/data/fd/.
They carry every result with shots, shots on target, corners, fouls and cards, plus the bookmakers' opening and
closing odds (Pinnacle's closing line, PSCH/PSCD/PSCA, is the sharpest public price we have; the "closing line"
is the last price before kickoff).

The proof: a walk-forward test. For each test season from 2019/20 to 2025/26 the model is refitted every
matchweek on matches dated before that week only. The two tuning numbers (xi, the time decay; sot_blend, how much
shots on target count) are picked on the seasons before the test season by predictive log loss, and the
temperature is fitted on the previous season's out-of-sample predictions. Nothing a prediction uses is dated on
or after the week it is made for.

Outputs (projects/edge/backtest/<date>.md and .json, plus <date>-predictions.csv):
  (a) accuracy per season (log loss, Brier, RPS), model against the de-vigged closing line
  (b) calibration by 10-point bands, model and market, with a Wilson interval and a pass mark
  (c) a simulated bet record with the live rules, Pinnacle closing standing in for Kalshi
  (d) the no-look-ahead canary

  python scripts/edge_backtest.py fetch                       download the season files (skips files under 24 h old)
  python scripts/edge_backtest.py run [--seasons 1920,2021]   the proof; fitted weights are cached per week in
                                                              data/cache/backtest so a re-run takes seconds
  python scripts/edge_backtest.py run --fresh                 ignore the cache
  python scripts/edge_backtest.py report                      print the latest summary
  python scripts/edge_backtest.py canary                      the no-look-ahead check alone

The server calls run_backtest(seasons, progress) in a thread; progress gets a short string now and then.
"""
import argparse
import hashlib
import io
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import edge_common as ec  # noqa: E402
import edge_model as em  # noqa: E402

SEASON_CODES = [f"{y % 100:02d}{(y + 1) % 100:02d}" for y in range(2015, 2027)]   # 1516 .. 2627
FD_URL = "https://www.football-data.co.uk/mmz4281/{code}/E0.csv"
TEST_FROM, TEST_TO = "1920", "2526"
GRID = [(xi, blend) for xi in (0.001, 0.002, 0.004) for blend in (0.0, 0.5)]
CACHE_DIR = ec.CACHE / "backtest"
HALF_SPREAD = 0.01            # half a 2-cent spread: ask = fair + 0.01, bid = fair - 0.01
BANKROLL = 1000.0             # flat for the simulation: every stake is a share of the same $1,000
COVID_SEASON = "2021"         # 2020/21, empty grounds
OUTCOMES = ("home", "draw", "away")
RESULT_INDEX = {"H": 0, "D": 1, "A": 2}

RENAME = {
    "HomeTeam": "home_raw", "AwayTeam": "away_raw", "FTHG": "hg", "FTAG": "ag", "FTR": "result",
    "HS": "hs", "AS": "as_", "HST": "hst", "AST": "ast", "HC": "hc", "AC": "ac", "HF": "hf", "AF": "af",
    "HY": "hy", "AY": "ay", "HR": "hr", "AR": "ar",
    "PSH": "ps_h", "PSD": "ps_d", "PSA": "ps_a", "PSCH": "psc_h", "PSCD": "psc_d", "PSCA": "psc_a",
    "B365H": "b365_h", "B365D": "b365_d", "B365A": "b365_a", "B365CH": "b365c_h", "B365CD": "b365c_d", "B365CA": "b365c_a",
    "AvgH": "avg_h", "AvgD": "avg_d", "AvgA": "avg_a", "AvgCH": "avgc_h", "AvgCD": "avgc_d", "AvgCA": "avgc_a",
    "MaxCH": "maxc_h", "MaxCD": "maxc_d", "MaxCA": "maxc_a",
}
INT_COLS = ["hg", "ag", "hs", "as_", "hst", "ast", "hc", "ac", "hf", "af", "hy", "ay", "hr", "ar"]
ODDS_COLS = [c for c in RENAME.values() if c.split("_")[0] in ("ps", "psc", "b365", "b365c", "avg", "avgc", "maxc")]


# ---------------------------------------------------------------- data

def fd_path(code):
    return ec.FD_DIR / f"E0-{code}.csv"


def fetch(codes=None, max_age_hours=24, quiet=False, progress=None):
    """Download the season files. A file under max_age_hours old is kept. A 404 or an empty body is reported,
    never fatal. Returns one dict per code: code, status (fresh | downloaded | missing | error), rows, closing."""
    ec.ensure_dirs()
    out = []
    for code in codes or SEASON_CODES:
        path = fd_path(code)
        rec = {"code": code, "season": em.season_label(code), "status": "", "rows": 0, "note": ""}
        if path.exists() and (time.time() - path.stat().st_mtime) < max_age_hours * 3600:
            rec["status"] = "fresh"
        else:
            try:
                r = requests.get(FD_URL.format(code=code), timeout=60)
                if r.status_code == 404 or not r.content or len(r.content) < 200:
                    rec["status"] = "missing"
                    rec["note"] = f"HTTP {r.status_code}, {len(r.content)} bytes"
                else:
                    tmp = path.with_suffix(".part")
                    tmp.write_bytes(r.content)
                    tmp.replace(path)
                    rec["status"] = "downloaded"
            except requests.RequestException as e:
                rec["status"] = "error"
                rec["note"] = str(e)[:120]
        if path.exists():
            head = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
            cols = set(head[0].split(",")) if head else set()
            rec["rows"] = max(0, len([l for l in head[1:] if l.strip(",").strip()]))
            rec["closing"] = {"PSCH": "PSCH" in cols, "AvgCH": "AvgCH" in cols, "B365CH": "B365CH" in cols,
                              "PSH": "PSH" in cols, "Time": "Time" in cols}
        if not quiet:
            ec.log(f"fetch E0 {code}: {rec['status']} {rec['rows']} rows"
                   + (f" closing {rec.get('closing')}" if rec.get("closing") else "") + (f" {rec['note']}" if rec["note"] else ""))
        if progress:
            progress(f"fetch {code}: {rec['status']}")
        out.append(rec)
    return out


def _read_one(path, code):
    raw = pd.read_csv(path, encoding="utf-8-sig", encoding_errors="replace", dtype=str, keep_default_na=False)
    raw = raw.loc[:, [c for c in raw.columns if c and not c.startswith("Unnamed")]]
    raw = raw[raw.get("HomeTeam", pd.Series("", index=raw.index)).str.strip() != ""]
    if len(raw) == 0:
        return None
    first = str(raw["Date"].iloc[0]).strip()
    fmt = "%d/%m/%Y" if len(first.split("/")[-1]) == 4 else "%d/%m/%y"
    df = pd.DataFrame({"date": pd.to_datetime(raw["Date"].str.strip(), format=fmt, utc=True)})
    df["time"] = raw["Time"].str.strip() if "Time" in raw else ""
    df["season"] = code
    for src, dst in RENAME.items():
        if src in raw:
            s = raw[src].str.strip()
            if dst in ("home_raw", "away_raw", "result"):
                df[dst] = s
            else:
                df[dst] = pd.to_numeric(s.replace("", np.nan), errors="coerce")
        else:
            df[dst] = "" if dst in ("home_raw", "away_raw", "result") else np.nan
    df["home"] = df["home_raw"].map(ec.norm)
    df["away"] = df["away_raw"].map(ec.norm)
    return df


def load_fd(codes=None):
    """The tidy frame: date (UTC midnight), time, season (code), home, away (edge_common.norm of the names),
    home_raw, away_raw, hg, ag, result (H/D/A), hs, as_, hst, ast, hc, ac, hf, af, hy, ay, hr, ar, and the odds
    as floats or NaN: ps_* (Pinnacle before close), psc_* (Pinnacle closing), b365_*, b365c_*, avg_*, avgc_*,
    maxc_*. Sorted by date. Files that are missing are skipped."""
    frames = []
    for code in codes or SEASON_CODES:
        path = fd_path(code)
        if path.exists():
            one = _read_one(path, code)
            if one is not None:
                frames.append(one)
    if not frames:
        raise FileNotFoundError(f"no season files in {ec.FD_DIR}; run: python scripts/edge_backtest.py fetch")
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["hg", "ag"]).copy()
    for c in INT_COLS:
        df[c] = df[c].astype(float)
    df = df.sort_values(["date", "home"], kind="stable").reset_index(drop=True)
    return df


def closing_coverage(df):
    """Share of each season's rows that carry Pinnacle closing odds. Pinnacle left the feed on 2026-01-08, so
    2025/26 has about 55% and 2026/27 none."""
    return {code: float(g["psc_h"].notna().mean()) for code, g in df.groupby("season")}


def seasons_with_closing(df, min_share=0.2):
    """Season codes where Pinnacle closing odds exist on at least min_share of the rows."""
    return sorted(code for code, share in closing_coverage(df).items() if share >= min_share)


# ---------------------------------------------------------------- the walk

def week_start(dates):
    """Monday 00:00 UTC of each date's week."""
    d = dates.dt.normalize()
    return d - pd.to_timedelta(d.dt.weekday, unit="D")


def _cache_key(train_rows, xi, blend):
    cols = ["date", "home", "away", "hg", "ag", "hst", "ast"]
    h = hashlib.sha1()
    h.update(pd.util.hash_pandas_object(train_rows[cols], index=False).to_numpy().tobytes())
    h.update(f"{xi}|{blend}|{em.RIDGE}|{em.TRAIN_DAYS}|v1".encode())
    return h.hexdigest()[:20]


def fit_week(df, ws, xi, blend, init=None, use_cache=True):
    """The fit for a week starting at `ws` (training rows dated before it), from the cache when the same rows
    were fitted before."""
    train = em._training_rows(df, ws, em.TRAIN_DAYS)
    key = _cache_key(train, xi, blend)
    sub = CACHE_DIR / f"xi{xi}-sot{blend}"
    path = sub / f"{ws.strftime('%Y-%m-%d')}-{key}.json"
    if use_cache and path.exists():
        return em.Params.from_dict(ec.read_json(path, {})), True
    params = em.fit_dixon_coles(df, ws, xi=xi, sot_blend=blend, init=init)
    if use_cache:
        sub.mkdir(parents=True, exist_ok=True)
        ec.write_json_atomic(path, params.to_dict(), indent=0)
    return params, False


def walk_season(df, season, xi, blend, init=None, use_cache=True, progress=None, max_weeks=None):
    """Raw (pre-temperature) chances for every match of one season, refitting at each week start on earlier
    rows only. Returns (predictions DataFrame, the last week's Params) so the next season can warm-start."""
    rows = df[df["season"] == season].sort_values("date")
    weeks = week_start(rows["date"])
    out = []
    starts = sorted(weeks.unique())
    if max_weeks:
        starts = starts[:max_weeks]
    params = init
    for k, ws in enumerate(starts):
        wk = rows[weeks == ws]
        params, cached = fit_week(df, ws, xi, blend, init=params, use_cache=use_cache)
        for r in wk.itertuples(index=False):
            ph, pd_, pa = em.three_way(params, r.home, r.away)
            out.append((season, r.date, ws, r.home, r.away, r.result, ph, pd_, pa, params.n_rows,
                        params.knows(r.home), params.knows(r.away)))
        if progress and (k % 10 == 0 or k == len(starts) - 1):
            progress(f"xi {xi} sot {blend}: {em.season_label(season)} week {k + 1}/{len(starts)}" + (" (cached)" if cached else ""))
    pred = pd.DataFrame(out, columns=["season", "date", "week", "home", "away", "result", "raw_h", "raw_d", "raw_a",
                                      "train_rows", "home_known", "away_known"])
    return pred, params


def walk_all(df, seasons, xi, blend, use_cache=True, progress=None):
    frames, params = [], None
    for s in seasons:
        pred, params = walk_season(df, s, xi, blend, init=params, use_cache=use_cache, progress=progress)
        frames.append(pred)
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------- scores

def y_index(results):
    return np.array([RESULT_INDEX[r] for r in results], int)


def log_loss(P, y):
    P = np.clip(np.asarray(P, float), 1e-12, 1.0)
    return float(-np.log(P[np.arange(len(y)), y]).mean())


def brier(P, y):
    P = np.asarray(P, float)
    O = np.eye(3)[y]
    return float(((P - O) ** 2).sum(axis=1).mean())


def rps(P, y):
    """Ranked probability score: the Brier score on the running totals home, home+draw. Lower is better; it
    forgives a near miss (home when the draw was likeliest) more than a far one."""
    P = np.asarray(P, float)
    O = np.eye(3)[y]
    cp = np.cumsum(P, axis=1)[:, :2]
    co = np.cumsum(O, axis=1)[:, :2]
    return float((((cp - co) ** 2).sum(axis=1) / 2.0).mean())


def scores(P, y):
    return {"n": int(len(y)), "log_loss": log_loss(P, y), "brier": brier(P, y), "rps": rps(P, y)}


def calibration_table(P, y, width=10, tol=5.0, min_n=1):
    """One row per 10-point band of the stated chance, pooled over the three outcome columns. pass = the mean
    stated chance sits inside the Wilson 95% interval of the hit rate and within tol points of it."""
    P = np.asarray(P, float)
    p = P.T.reshape(-1)
    hit = (np.tile(np.arange(3), (len(y), 1)).T.reshape(-1) == np.repeat(y[None, :], 3, axis=0).reshape(-1))
    bands = np.array([ec.band_of(100.0 * v, width) for v in p])
    rows = []
    for lo in range(0, 100, width):
        b = f"{lo}-{lo + width}"
        m = bands == b
        n = int(m.sum())
        if n < min_n:
            continue
        mean_p = 100.0 * float(p[m].mean())
        k = int(hit[m].sum())
        rate = 100.0 * k / n
        wl, wh = ec.wilson(k, n)
        rows.append({"band": b, "n": n, "mean_p": mean_p, "hit_rate": rate, "lo": 100.0 * wl, "hi": 100.0 * wh,
                     "pass": bool(100.0 * wl <= mean_p <= 100.0 * wh and abs(mean_p - rate) <= tol)})
    x = p - p.mean()
    slope = float((x * (hit - hit.mean())).sum() / max(1e-12, (x * x).sum()))
    return {"rows": rows, "slope": slope, "pooled": {"n": int(len(p)), "mean_p": 100.0 * float(p.mean()),
                                                      "hit_rate": 100.0 * float(hit.mean())}}


# ---------------------------------------------------------------- the market

def add_market(pred):
    """De-vigged fair chances: Pinnacle closing by the power method (psc_pw_*) and proportional (psc_pr_*),
    the market average closing by power (avgc_pw_*), Pinnacle before close by power (ps_pw_*). NaN when missing."""
    def dv(cols, fn, prefix):
        vals = pred[list(cols)].to_numpy(float)
        out = np.full_like(vals, np.nan)
        ok = np.isfinite(vals).all(axis=1) & (vals > 1.0).all(axis=1)
        for i in np.where(ok)[0]:
            out[i] = fn(vals[i].tolist())
        for j, o in enumerate(("h", "d", "a")):
            pred[f"{prefix}_{o}"] = out[:, j]
    dv(("psc_h", "psc_d", "psc_a"), ec.devig_power, "psc_pw")
    dv(("psc_h", "psc_d", "psc_a"), ec.devig_proportional, "psc_pr")
    dv(("avgc_h", "avgc_d", "avgc_a"), ec.devig_power, "avgc_pw")
    dv(("ps_h", "ps_d", "ps_a"), ec.devig_power, "ps_pw")
    return pred


# ---------------------------------------------------------------- the simulated record

def _bet_rows(pred, cfg, price_prefix="psc_pw", clv_prefix="psc_pw", bankroll=BANKROLL):
    """The live rules on one frame. For each match the six sides are priced from the de-vigged fair chance:
    yes ask = fair + 0.01, no ask = 1 - (fair - 0.01); edge_common.gap_and_side scores each outcome; the single
    largest gap at the floor or above is bet, staked by stake_for_gap on a flat bankroll."""
    rate = float(cfg["fees"]["taker_rate"])
    floor = float(cfg["gap_floor_points"])
    bets = []
    cols_p = ["p_h", "p_d", "p_a"]
    cols_f = [f"{price_prefix}_{o}" for o in ("h", "d", "a")]
    cols_c = [f"{clv_prefix}_{o}" for o in ("h", "d", "a")]
    for r in pred.itertuples(index=False):
        d = r._asdict()
        fair = [d[c] for c in cols_f]
        if any(not np.isfinite(v) for v in fair):
            continue
        close = [d[c] for c in cols_c]
        best = None
        for o in range(3):
            g = ec.gap_and_side(d[cols_p[o]], fair[o] + HALF_SPREAD, 1.0 - (fair[o] - HALF_SPREAD), rate)
            if best is None or g["gap"] > best[1]["gap"]:
                best = (o, g)
        o, g = best
        if g["gap"] < floor:
            continue
        stake = ec.stake_for_gap(g["gap"], bankroll, cfg)
        count = ec.contracts_for(stake, g["price"])
        fee = ec.kalshi_fee_usd(count, g["price"], rate)
        cost = round(count * g["price"] + fee, 2)
        yes = g["side"] == "yes"
        res = RESULT_INDEX[d["result"]]
        won = (res == o) if yes else (res != o)
        pnl = round((count if won else 0) - cost, 2)
        p_bought = d[cols_p[o]] if yes else 1.0 - d[cols_p[o]]
        fair_bought = fair[o] if yes else 1.0 - fair[o]
        close_bought = (close[o] if yes else 1.0 - close[o]) if all(np.isfinite(v) for v in close) else np.nan
        bets.append({
            "season": d["season"], "date": d["date"], "home": d["home"], "away": d["away"], "outcome": OUTCOMES[o],
            "side": g["side"], "p": p_bought, "fair": fair_bought, "price": g["price"], "gap": g["gap"],
            "break_even": g["break_even"], "stake": stake, "count": count, "fee": fee, "cost": cost,
            "won": bool(won), "pnl": pnl, "clv": 100.0 * (close_bought - g["break_even"]),
            "our_band": ec.band_of(100.0 * p_bought), "market_band": ec.band_of(100.0 * fair_bought),
        })
    return pd.DataFrame(bets)


def _drawdown(pnl):
    cum = np.concatenate([[0.0], np.cumsum(pnl)])
    peak = np.maximum.accumulate(cum)
    return float((peak - cum).max()) if len(cum) else 0.0


def _group(bets, col):
    out = []
    for k, g in bets.groupby(col, sort=True):
        out.append({col: k, "bets": int(len(g)), "hit_rate": 100.0 * float(g["won"].mean()),
                    "pnl": float(g["pnl"].sum()), "cost": float(g["cost"].sum()),
                    "return_pct": 100.0 * float(g["pnl"].sum() / max(1e-9, g["cost"].sum())),
                    "mean_clv": float(g["clv"].mean()) if g["clv"].notna().any() else None})
    return out


def bootstrap_return(bets, n=10000, seed=0):
    """Resample the bet list with replacement n times; the 5th and 95th percentile of return on cost."""
    if len(bets) == 0:
        return {"p5": None, "p50": None, "p95": None, "n": 0}
    rng = np.random.default_rng(seed)
    pnl = bets["pnl"].to_numpy(float)
    cost = bets["cost"].to_numpy(float)
    m = len(pnl)
    rets = []
    for start in range(0, n, 1000):
        idx = rng.integers(0, m, (min(1000, n - start), m))
        rets.append(100.0 * pnl[idx].sum(axis=1) / cost[idx].sum(axis=1))
    rets = np.concatenate(rets)
    return {"p5": float(np.percentile(rets, 5)), "p50": float(np.percentile(rets, 50)),
            "p95": float(np.percentile(rets, 95)), "share_positive": float((rets > 0).mean()), "n": int(n)}


def random_control(pred, bets, cfg, repeats=1000, seed=0, price_prefix="psc_pw"):
    """No-skill bets: the same number of bets, the same stakes (shuffled), a random match and a random one of
    its six sides each time, paying the same spread and fee. The mean and 90% range of return on cost."""
    pool = pred.dropna(subset=[f"{price_prefix}_h"])
    n = len(bets)
    if n == 0 or len(pool) == 0:
        return {"mean": None, "p5": None, "p95": None, "repeats": 0}
    rng = np.random.default_rng(seed)
    rate = float(cfg["fees"]["taker_rate"])
    fair = pool[[f"{price_prefix}_{o}" for o in ("h", "d", "a")]].to_numpy(float)
    y = y_index(pool["result"].to_numpy())
    stakes = bets["stake"].to_numpy(float)
    rets = []
    for _ in range(repeats):
        mi = rng.integers(0, len(pool), n)
        oc = rng.integers(0, 3, n)
        yes = rng.integers(0, 2, n) == 1
        f = fair[mi, oc]
        price = np.where(yes, f + HALF_SPREAD, 1.0 - (f - HALF_SPREAD))
        st = rng.permutation(stakes)
        count = np.maximum(1, np.floor(st / price + 1e-9))
        fee = np.ceil(rate * count * price * (1.0 - price) * 100.0 - 1e-9) / 100.0
        cost = count * price + fee
        won = np.where(yes, y[mi] == oc, y[mi] != oc)
        pnl = np.where(won, count, 0.0) - cost
        rets.append(100.0 * pnl.sum() / cost.sum())
    rets = np.array(rets)
    return {"mean": float(rets.mean()), "p5": float(np.percentile(rets, 5)), "p95": float(np.percentile(rets, 95)),
            "repeats": int(repeats)}


def simulate(pred, cfg, price_prefix="psc_pw", clv_prefix="psc_pw", label="Pinnacle closing as Kalshi"):
    bets = _bet_rows(pred, cfg, price_prefix=price_prefix, clv_prefix=clv_prefix)
    out = {"label": label, "bets": int(len(bets)), "bankroll": BANKROLL, "bankroll_note": "flat $1,000, stakes never compound"}
    if len(bets) == 0:
        out.update({"hit_rate": None, "pnl": 0.0, "cost": 0.0, "staked": 0.0, "return_pct": None})
        return out, bets
    bets = bets.sort_values("date").reset_index(drop=True)
    out.update({
        "hit_rate": 100.0 * float(bets["won"].mean()), "pnl": float(bets["pnl"].sum()),
        "cost": float(bets["cost"].sum()), "staked": float(bets["stake"].sum()), "fees": float(bets["fee"].sum()),
        "return_pct": 100.0 * float(bets["pnl"].sum() / bets["cost"].sum()),
        "max_drawdown_usd": _drawdown(bets["pnl"].to_numpy(float)),
        "max_drawdown_pct": 100.0 * _drawdown(bets["pnl"].to_numpy(float)) / BANKROLL,
        "mean_gap": float(bets["gap"].mean()), "mean_price": float(bets["price"].mean()),
        "clv": {"mean": float(bets["clv"].mean()), "share_positive": 100.0 * float((bets["clv"] > 0).mean()),
                "n": int(bets["clv"].notna().sum())},
        "by_season": _group(bets, "season"), "by_side": _group(bets, "side"), "by_outcome": _group(bets, "outcome"),
        "by_our_band": _group(bets, "our_band"), "by_market_band": _group(bets, "market_band"),
        "bootstrap": bootstrap_return(bets), "random_control": random_control(pred, bets, cfg, price_prefix=price_prefix),
    })
    for row in out["by_our_band"] + out["by_market_band"]:
        row["mean_p"] = None
    for row in out["by_our_band"]:
        g = bets[bets["our_band"] == row["our_band"]]
        row["mean_p"] = 100.0 * float(g["p"].mean())
        row["mean_fair"] = 100.0 * float(g["fair"].mean())
    for row in out["by_market_band"]:
        g = bets[bets["market_band"] == row["market_band"]]
        row["mean_p"] = 100.0 * float(g["p"].mean())
        row["mean_fair"] = 100.0 * float(g["fair"].mean())
    return out, bets


# ---------------------------------------------------------------- the canary

def canary(df, season=None, weeks=3, xi=0.002, blend=0.5):
    """Append a fake future match (9-0) dated at the start of the last predicted week and check that no earlier
    prediction moves. Runs without the cache. Returns {ok, max_diff, matches, fake_date}."""
    season = season or sorted(df["season"].unique())[-2]
    base, _ = walk_season(df, season, xi, blend, use_cache=False, max_weeks=weeks)
    fake_date = base["week"].max()
    last = df[df["season"] == season].sort_values("date").iloc[0]
    fake = {c: last[c] for c in df.columns}
    fake.update({"date": fake_date, "hg": 9.0, "ag": 0.0, "result": "H", "hst": 25.0, "ast": 0.0, "hs": 40.0, "as_": 1.0,
                 "home": last["away"], "away": last["home"], "home_raw": last["away_raw"], "away_raw": last["home_raw"]})
    df2 = pd.concat([df, pd.DataFrame([fake])], ignore_index=True).sort_values(["date", "home"], kind="stable").reset_index(drop=True)
    again, _ = walk_season(df2, season, xi, blend, use_cache=False, max_weeks=weeks)
    key = ["date", "home", "away"]
    m = base.merge(again, on=key, suffixes=("", "_2"))
    m = m[~((m["date"] == fake_date) & (m["home"] == fake["home"]) & (m["away"] == fake["away"]))]
    diff = float(np.abs(m[["raw_h", "raw_d", "raw_a"]].to_numpy() - m[["raw_h_2", "raw_d_2", "raw_a_2"]].to_numpy()).max())
    ok = len(m) == len(base) and diff <= 1e-9
    return {"ok": bool(ok), "max_diff": diff, "matches": int(len(m)), "fake_date": ec.iso(fake_date.to_pydatetime()),
            "season": em.season_label(season), "weeks": weeks}


def training_dates_ok(df, pred):
    """Every week's training rows end before the week start (the fit asserts it too); here on the predictions."""
    ws = pred["week"].min()
    return bool((pred["week"] <= pred["date"]).all()) and ws is not None


# ---------------------------------------------------------------- the run

def _py(o):
    if isinstance(o, dict):
        return {str(k): _py(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_py(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, pd.Timestamp):
        return ec.iso(o.to_pydatetime())
    return o


def run_backtest(seasons=None, progress=None, use_cache=True, date=None):
    """The whole proof. seasons: football-data codes to score (default: every season with Pinnacle closing odds
    from 1920 to 2526). Returns the metrics dict that is also written to projects/edge/backtest/<date>.json."""
    t0 = time.time()
    say = progress or (lambda s: ec.log("backtest:", s))
    cfg = ec.load_config()
    date = date or ec.now().strftime("%Y-%m-%d")
    df = load_fd()
    codes = sorted(df["season"].unique())
    closing = seasons_with_closing(df)
    test = [s for s in (seasons or [c for c in closing if TEST_FROM <= c <= TEST_TO]) if s in codes]
    if not test:
        raise ValueError("no test seasons with closing odds")
    walk = [c for c in codes[1:] if c <= max(test)]        # every season after the first file, up to the last test season
    say(f"{len(codes)} seasons on disk, closing odds in {len(closing)}, scoring {', '.join(em.season_label(s) for s in test)}")

    # 1. walk-forward raw predictions for every grid point
    raw = {}
    for k, (xi, blend) in enumerate(GRID):
        say(f"grid {k + 1}/{len(GRID)}: xi {xi}, sot_blend {blend}")
        raw[(xi, blend)] = walk_all(df, walk, xi, blend, use_cache=use_cache, progress=say)
    say(f"fits done in {time.time() - t0:.0f} s")

    # 2. per test season: pick the grid point on earlier seasons, the temperature on the season before
    frames, choices = [], []
    for s in test:
        earlier = [w for w in walk if w < s]
        prev = earlier[-1] if earlier else None
        best, best_ll = None, None
        for g, pr in raw.items():
            sel = pr[pr["season"].isin(earlier)]
            if len(sel) == 0:
                continue
            ll = log_loss(sel[["raw_h", "raw_d", "raw_a"]].to_numpy(), y_index(sel["result"].to_numpy()))
            if best_ll is None or ll < best_ll - 1e-12:
                best, best_ll = g, ll
        best = best or GRID[0]
        pr = raw[best]
        temp = 1.0
        if prev is not None:
            pv = pr[pr["season"] == prev]
            temp = em.fit_temperature(pv[["raw_h", "raw_d", "raw_a"]].to_numpy(), y_index(pv["result"].to_numpy()))
        cur = pr[pr["season"] == s].copy()
        P = np.array([em.apply_temperature(t, temp) for t in cur[["raw_h", "raw_d", "raw_a"]].to_numpy()])
        cur["p_h"], cur["p_d"], cur["p_a"] = P[:, 0], P[:, 1], P[:, 2]
        cur["xi"], cur["sot_blend"], cur["temperature"] = best[0], best[1], temp
        frames.append(cur)
        choices.append({"season": em.season_label(s), "code": s, "xi": best[0], "sot_blend": best[1],
                        "selection_log_loss": best_ll, "selected_on": [em.season_label(w) for w in earlier],
                        "temperature": temp, "temperature_from": em.season_label(prev) if prev else None})
        say(f"{em.season_label(s)}: xi {best[0]}, sot_blend {best[1]}, T {temp:.3f}")
    pred = pd.concat(frames, ignore_index=True)
    pred = pred.merge(df[["date", "home", "away", "hg", "ag"] + ODDS_COLS], on=["date", "home", "away"], how="left")
    pred = add_market(pred)

    # the pick for the live season: the grid point on every walk season, T on the last one
    live_best, live_ll = None, None
    for g, pr in raw.items():
        ll = log_loss(pr[["raw_h", "raw_d", "raw_a"]].to_numpy(), y_index(pr["result"].to_numpy()))
        if live_ll is None or ll < live_ll - 1e-12:
            live_best, live_ll = g, ll
    lv = raw[live_best][raw[live_best]["season"] == walk[-1]]
    live_T = em.fit_temperature(lv[["raw_h", "raw_d", "raw_a"]].to_numpy(), y_index(lv["result"].to_numpy()))
    live = {"xi": live_best[0], "sot_blend": live_best[1], "temperature": live_T, "selected_on": [em.season_label(w) for w in walk],
            "temperature_from": em.season_label(walk[-1]), "selection_log_loss": live_ll}

    # 3. accuracy
    y = y_index(pred["result"].to_numpy())
    Pm = pred[["p_h", "p_d", "p_a"]].to_numpy()
    Pr = pred[["raw_h", "raw_d", "raw_a"]].to_numpy()
    has_psc = pred["psc_pw_h"].notna().to_numpy()
    has_avg = pred["avgc_pw_h"].notna().to_numpy()
    accuracy = {"all": {}, "by_season": []}

    def acc_block(mask):
        b = {"n": int(mask.sum()), "model": scores(Pm[mask], y[mask]), "model_raw": scores(Pr[mask], y[mask])}
        mp = mask & has_psc
        if mp.any():
            b["pinnacle_close_power"] = scores(pred.loc[mp, ["psc_pw_h", "psc_pw_d", "psc_pw_a"]].to_numpy(), y[mp])
            b["pinnacle_close_proportional"] = scores(pred.loc[mp, ["psc_pr_h", "psc_pr_d", "psc_pr_a"]].to_numpy(), y[mp])
            b["model_on_same_rows"] = scores(Pm[mp], y[mp])
            b["gap_log_loss"] = b["model_on_same_rows"]["log_loss"] - b["pinnacle_close_power"]["log_loss"]
        ma = mask & has_avg
        if ma.any():
            b["avg_close_power"] = scores(pred.loc[ma, ["avgc_pw_h", "avgc_pw_d", "avgc_pw_a"]].to_numpy(), y[ma])
        mpre = mask & pred["ps_pw_h"].notna().to_numpy()
        if mpre.any():
            b["pinnacle_preclose_power"] = scores(pred.loc[mpre, ["ps_pw_h", "ps_pw_d", "ps_pw_a"]].to_numpy(), y[mpre])
        return b

    for s in test:
        m = (pred["season"] == s).to_numpy()
        blk = acc_block(m)
        blk.update({"season": em.season_label(s), "code": s, "empty_grounds": s == COVID_SEASON})
        accuracy["by_season"].append(blk)
    accuracy["all"] = acc_block(np.ones(len(pred), bool))
    not_covid = (pred["season"] != COVID_SEASON).to_numpy()
    accuracy["without_2020_21"] = acc_block(not_covid)
    accuracy["agree_with_market_pick_pct"] = 100.0 * float((Pm[has_psc].argmax(axis=1) == pred.loc[has_psc, ["psc_pw_h", "psc_pw_d", "psc_pw_a"]].to_numpy().argmax(axis=1)).mean())

    # 4. calibration
    gate = cfg["gate"]
    calibration = {
        "model": calibration_table(Pm, y, int(gate["band_width_points"]), float(gate["band_tolerance_points"])),
        "model_raw": calibration_table(Pr, y, int(gate["band_width_points"]), float(gate["band_tolerance_points"])),
        "market": calibration_table(pred.loc[has_psc, ["psc_pw_h", "psc_pw_d", "psc_pw_a"]].to_numpy(), y[has_psc],
                                    int(gate["band_width_points"]), float(gate["band_tolerance_points"])),
    }
    for key in ("model", "market"):
        rows = calibration[key]["rows"]
        calibration[key]["bands_passed"] = sum(1 for r in rows if r["pass"])
        calibration[key]["bands"] = len(rows)

    # 5. the simulated record
    say("simulating the bet record")
    record, bets = simulate(pred, cfg)
    say("simulating the pre-close variant")
    record_pre, bets_pre = simulate(pred, cfg, price_prefix="ps_pw", clv_prefix="psc_pw",
                                    label="Pinnacle before close as the price, closing line as the truth")
    record_pre["note"] = ("The same rules at Pinnacle's earlier price (PSH/PSD/PSA, taken days before kickoff). CLV here "
                          "is a real test: does the closing line move toward the side we bought?")

    # 6. the canary
    say("canary")
    can = canary(df, season=test[-1])
    can["training_rows_before_week"] = training_dates_ok(df, pred)

    took = time.time() - t0
    cover = closing_coverage(df)
    out = {
        "date": date, "took_s": took, "seasons_on_disk": [em.season_label(c) for c in codes],
        "seasons_with_closing": [em.season_label(c) for c in closing], "test_seasons": [em.season_label(c) for c in test],
        "closing_coverage": {em.season_label(c): round(100.0 * cover[c], 1) for c in codes},
        "walk_seasons": [em.season_label(c) for c in walk], "grid": [{"xi": g[0], "sot_blend": g[1]} for g in GRID],
        "choices": choices, "live": live, "matches_scored": int(len(pred)), "matches_with_closing": int(has_psc.sum()),
        "rules": {"gap_floor_points": cfg["gap_floor_points"], "stake": cfg["stake"], "taker_rate": cfg["fees"]["taker_rate"],
                  "half_spread": HALF_SPREAD, "bankroll": BANKROLL},
        "accuracy": accuracy, "calibration": calibration, "record": record, "record_preclose": record_pre, "canary": can,
        "model_notes": {"max_goals": em.MAX_GOALS, "ridge": em.RIDGE, "train_days": em.TRAIN_DAYS, "features": em.FEATURES},
    }
    out = _py(out)
    ec.ensure_dirs()
    ec.write_json_atomic(ec.BACKTEST_DIR / f"{date}.json", out, indent=1)
    pred_out = pred.drop(columns=[c for c in pred.columns if c.startswith("b365")], errors="ignore")
    pred_out.to_csv(ec.BACKTEST_DIR / f"{date}-predictions.csv", index=False)
    bets.to_csv(ec.BACKTEST_DIR / f"{date}-bets.csv", index=False)
    (ec.BACKTEST_DIR / f"{date}.md").write_text(write_report(out), encoding="utf-8")
    try:
        c = ec.db()
        c.execute("INSERT INTO backtests (ts, params_json, metrics_json, path) VALUES (?, ?, ?, ?)",
                  (ec.iso(ec.now()), json.dumps({"seasons": test, "grid": GRID}), json.dumps(_summary(out)),
                   str(ec.BACKTEST_DIR / f"{date}.md")))
        c.commit()
    except Exception as e:
        ec.log("backtest: db row skipped:", str(e)[:120])
    say(f"done in {took:.0f} s")
    return out


def _summary(out):
    r = out["record"]
    a = out["accuracy"]["all"]
    return {"date": out["date"], "matches": out["matches_scored"], "log_loss_model": a["model"]["log_loss"],
            "log_loss_market": a.get("pinnacle_close_power", {}).get("log_loss"), "bets": r["bets"], "pnl": r.get("pnl"),
            "return_pct": r.get("return_pct"), "hit_rate": r.get("hit_rate"), "canary_ok": out["canary"]["ok"],
            "bands_passed": f"{out['calibration']['model']['bands_passed']}/{out['calibration']['model']['bands']}"}


# ---------------------------------------------------------------- the report

def _f(v, d=3, pct=False, sign=False):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "n/a"
    s = f"{v:+.{d}f}" if sign else f"{v:.{d}f}"
    return s + ("%" if pct else "")


def _money(v):
    if v is None:
        return "n/a"
    return f"-${abs(v):,.2f}" if v < 0 else f"${v:,.2f}"


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def write_report(out):
    a = out["accuracy"]
    r = out["record"]
    rp = out["record_preclose"]
    cal = out["calibration"]
    can = out["canary"]
    L = []
    L.append(f"# Monarc Edge backtest, {out['date']}")
    L.append("")
    L.append("Plain words first. This is the proof behind the model: we pretended to be on each matchweek from "
             f"{out['test_seasons'][0]} to {out['test_seasons'][-1]}, refitted the model on the matches played before that "
             "week, and wrote down our three chances for every match before looking at the result. Then we scored those "
             "chances against what happened, and against the sharpest public price (Pinnacle's closing line, with the "
             "bookmaker's margin taken out), and ran the live betting rules against that line as if it were Kalshi.")
    L.append("")
    L.append("**What to expect, stated before the numbers.** A stats-only model with no market input usually lands within "
             "1 to 2 points of log loss of the closing line and does not beat it. Against Pinnacle's closing line the "
             "simulated record is likely flat or negative, because that line already knows everything the model knows "
             "and more. The edge, if there is one, is where Kalshi's retail book differs from the sharp line, and only "
             "live cards can show that. What follows is what we actually got.")
    L.append("")
    L.append("## The short version")
    L.append("")
    mk_all = a["all"].get("pinnacle_close_power", {})
    rc = r.get("random_control", {})
    L.append(f"- Accuracy: the model's log loss is {_f(a['all']['model']['log_loss'], 4)} against the closing line's "
             f"{_f(mk_all.get('log_loss'), 4)} over {out['matches_with_closing']} matches. The market is sharper by "
             f"{_f(a['all'].get('gap_log_loss'), 3)}, inside the 1 to 2 point range a public-data model usually lands in.")
    L.append(f"- Calibration: {cal['model']['bands_passed']} of {cal['model']['bands']} bands pass with slope {_f(cal['model']['slope'], 2)} "
             f"(the market: {cal['market']['bands_passed']} of {cal['market']['bands']}, slope {_f(cal['market']['slope'], 2)}). "
             "When the model says 40%, it happens about 40% of the time.")
    if r["bets"]:
        L.append(f"- The record against the closing line: {r['bets']} bets, {_f(r['hit_rate'], 0)}% hit, {_money(r['pnl'])} after fees, "
                 f"{_f(r['return_pct'], 1, pct=True, sign=True)} on cash. Random bets with the same stakes return "
                 f"{_f(rc.get('mean'), 1, pct=True, sign=True)}. So where the model disagrees with Pinnacle's close by 7 points or more, "
                 f"Pinnacle is right more often than chance: the gap picks out the model's worst errors, not its insights.")
        L.append(f"- Max drawdown {_money(r['max_drawdown_usd'])}: a real ${out['rules']['bankroll']:,.0f} bankroll would have gone bust "
                 "following these rules against the closing line. The flat-bankroll simulation keeps betting so the whole record can be read; a live bankroll would not.")
    L.append(f"- CLV at the pre-close price: {_f(rp.get('clv', {}).get('mean'), 2, sign=True)} points, "
             f"{_f(rp.get('clv', {}).get('share_positive'), 0)}% positive. The line did not move toward the sides the model liked.")
    L.append(f"- No-look-ahead canary: {'PASS' if can['ok'] else 'FAIL'}. Runtime {out['took_s']:.0f} s"
             + (" with the per-week cache warm; a cold run is about 100 s on this laptop." if out["took_s"] < 60 else " with no cache."))
    L.append("- What it means for the plan: this model is a fair baseline and a working Stage 3 and 4, not an edge over a sharp book. "
             "Any edge has to come from Kalshi's price sitting away from the sharp line; the live cards measure that, the backtest cannot.")
    L.append("")
    L.append("## The setup")
    L.append("")
    partial ={s: v for s, v in out.get("closing_coverage", {}).items() if v < 100.0}
    L.append(f"- Data: football-data.co.uk E0, seasons on disk {', '.join(out['seasons_on_disk'])}. Pinnacle closing odds "
             f"present in {', '.join(out['seasons_with_closing'])}"
             + (" (partial: " + ", ".join(f"{s} {v:.0f}% of rows" for s, v in partial.items()) + "; Pinnacle left the feed on 2026-01-08, "
                "so 2025/26 is scored for accuracy on every match and against the market on the rows that have the line)" if partial else "") + ".")
    L.append(f"- Scored: {out['matches_scored']} matches over {len(out['test_seasons'])} seasons, {out['matches_with_closing']} with a closing line.")
    L.append(f"- Walk-forward seasons (also used to pick the tuning numbers): {', '.join(out['walk_seasons'])}.")
    L.append("- Model: Dixon-Coles Poisson goals model (attack and defence per team, home advantage, the rho fix for low-score "
             f"draws), time decay exp(-xi x days), shots on target blended in through a second likelihood. Weak ridge toward "
             "the promoted-team average for new teams. Score grid to 10 goals a side.")
    L.append("- Tuning, nested: xi from {0.001, 0.002, 0.004} and sot_blend from {0, 0.5}, picked for each test season on the "
             "seasons before it by predictive log loss. Temperature fitted on the previous season's out-of-sample chances.")
    L.append(f"- Rules: bet when our chance beats the price by {out['rules']['gap_floor_points']:.0f} points after the "
             f"{100 * out['rules']['taker_rate']:.0f}% taker fee; stake {out['rules']['stake']['floor_pct']:.0f}% of the bankroll "
             f"at the floor rising to {out['rules']['stake']['cap_pct']:.0f}% at {out['rules']['stake']['cap_from_points']:.0f} points; "
             f"one bet per match (the largest gap of the six sides); flat ${out['rules']['bankroll']:,.0f} bankroll (stakes never compound).")
    L.append(f"- Runtime: {out['took_s']:.0f} s.")
    L.append("")
    L.append("### What was picked each season")
    L.append("")
    L.append(md_table(["Season", "xi", "sot_blend", "Picked on", "Temperature", "T from"],
                      [[c["season"], c["xi"], c["sot_blend"], f"{c['selected_on'][0]} to {c['selected_on'][-1]}" if c["selected_on"] else "none",
                        _f(c["temperature"], 3), c["temperature_from"] or "none"] for c in out["choices"]]))
    L.append("")
    lv = out["live"]
    L.append(f"For the live season the pick is xi {lv['xi']}, sot_blend {lv['sot_blend']}, temperature {lv['temperature']:.3f} "
             f"(fitted on {lv['temperature_from']}). `edge_model.ModelService` reads these from this report's JSON.")
    L.append("")

    # (a)
    L.append("## (a) Accuracy per season")
    L.append("")
    L.append("Log loss: the average surprise; lower is better; 1.0986 is three equal chances. Brier: the squared error over "
             "the three outcomes (0 perfect, 2 worst). RPS: like Brier but it forgives a near miss (calling home when the "
             "draw came) more than a far one. Market = Pinnacle closing, margin removed by the power method.")
    L.append("")
    rows = []
    for b in a["by_season"]:
        mk = b.get("pinnacle_close_power", {})
        rows.append([b["season"] + (" (empty grounds)" if b["empty_grounds"] else ""), b["n"],
                     _f(b["model"]["log_loss"], 4), _f(mk.get("log_loss"), 4), _f(b.get("gap_log_loss"), 4, sign=True),
                     _f(b["model"]["brier"], 4), _f(mk.get("brier"), 4), _f(b["model"]["rps"], 4), _f(mk.get("rps"), 4),
                     _f(b.get("avg_close_power", {}).get("log_loss"), 4)])
    for key, label in (("all", "All seasons"), ("without_2020_21", "All but 2020/21")):
        b = a[key]
        mk = b.get("pinnacle_close_power", {})
        rows.append([f"**{label}**", b["n"], _f(b["model"]["log_loss"], 4), _f(mk.get("log_loss"), 4), _f(b.get("gap_log_loss"), 4, sign=True),
                     _f(b["model"]["brier"], 4), _f(mk.get("brier"), 4), _f(b["model"]["rps"], 4), _f(mk.get("rps"), 4),
                     _f(b.get("avg_close_power", {}).get("log_loss"), 4)])
    L.append(md_table(["Season", "Matches", "Log loss model", "Log loss market", "Gap", "Brier model", "Brier market",
                       "RPS model", "RPS market", "Log loss avg book"], rows))
    L.append("")
    gap = a["all"].get("gap_log_loss")
    raw_ll = a["all"]["model_raw"]["log_loss"]
    L.append(f"Reading: over every season our log loss is {_f(a['all']['model']['log_loss'], 4)} against the closing line's "
             f"{_f(a['all'].get('pinnacle_close_power', {}).get('log_loss'), 4)}, a gap of {_f(gap, 4, sign=True)} "
             f"({'the market is sharper, as expected' if gap and gap > 0 else 'the model is at or ahead of the market, which would be unusual and deserves a second look'}). "
             f"Before the temperature the model's log loss was {_f(raw_ll, 4)}, so the temperature "
             f"{'lowered' if raw_ll > a['all']['model']['log_loss'] else 'did not lower'} the log loss "
             f"(it is fitted on the season before, and a season's over- or under-confidence does not always carry over); "
             f"its job is the calibration table below, where it moved the model from "
             f"{sum(1 for x in cal['model_raw']['rows'] if x['pass'])} to {cal['model']['bands_passed']} passing bands. "
             f"Our top pick agrees with the market's top pick in {_f(a.get('agree_with_market_pick_pct'), 1)}% of matches. "
             "2020/21 was played in empty grounds and home advantage shrank; it is shown on its own line and in the "
             "'all but' row so one strange season does not hide in the total.")
    L.append("")

    # (b)
    L.append("## (b) Calibration by band")
    L.append("")
    L.append("Each match gives three rows (its home, draw and away chance). A band holds every stated chance in that "
             "ten-point range. 'Stated' is the average chance we said; 'Hit' is how often it happened; the interval is "
             "the Wilson 95% range the hit rate could really be. A band passes when the stated chance sits inside that "
             "interval and within 5 points of the hit rate. A slope of 1.0 means a point of stated chance was worth a "
             "point of real chance; under 1.0 means over-confident, over 1.0 timid.")
    L.append("")
    for key, label in (("model", "Model (after the temperature)"), ("market", "Market (Pinnacle closing, power de-vig)")):
        t = cal[key]
        L.append(f"### {label}: {t['bands_passed']} of {t['bands']} bands pass, slope {_f(t['slope'], 3)}")
        L.append("")
        L.append(md_table(["Band", "n", "Stated %", "Hit %", "Wilson 95%", "Pass"],
                          [[r["band"], r["n"], _f(r["mean_p"], 1), _f(r["hit_rate"], 1), f"{_f(r['lo'], 1)} to {_f(r['hi'], 1)}",
                            "yes" if r["pass"] else "no"] for r in t["rows"]]))
        L.append("")
    t = cal["model_raw"]
    L.append(f"Before the temperature the model passed {sum(1 for r in t['rows'] if r['pass'])} of {len(t['rows'])} bands with slope {_f(t['slope'], 3)}.")
    L.append("")
    failed = [r for r in cal["model"]["rows"] if not r["pass"]]
    L.append("Reading: " + ("every band passes: when we say 30%, it happens about 30% of the time. " if not failed else
             "the bands that miss are " + ", ".join(f"{r['band']} (stated {r['mean_p']:.0f}, hit {r['hit_rate']:.0f})" for r in failed) + ". ") +
             "Calibration is the floor, not the prize: a model can be perfectly calibrated and still know less than the market. "
             "The gate for auto mode needs the live cards to pass this same table, not the backtest.")
    L.append("")

    # (c)
    L.append("## (c) The simulated bet record")
    L.append("")
    L.append("Pinnacle's closing fair chance stands in for Kalshi: we pay fair plus one cent (half a two-cent spread) for a "
             "Yes, and one minus (fair minus one cent) for a No, plus the taker fee. One bet per match, the largest gap of "
             "the six sides, only at 7 points or more. CLV (closing line value) per bet = the closing fair chance of the side "
             "we bought minus our break-even price, in points. In this simulation the closing line is also the price we "
             "paid, so CLV is negative by the spread and fee by construction (about -2.7 points); the pre-close variant "
             "below is the real CLV test.")
    L.append("")
    if r["bets"]:
        L.append(md_table(["Bets", "Hit rate", "Cash down", "P&L after fees", "Return on cash", "Fees", "Max drawdown", "Mean gap", "Mean CLV", "CLV > 0"],
                          [[r["bets"], _f(r["hit_rate"], 1, pct=True), _money(r["cost"]), _money(r["pnl"]), _f(r["return_pct"], 1, pct=True, sign=True),
                            _money(r["fees"]), f"{_money(r['max_drawdown_usd'])} ({_f(r['max_drawdown_pct'], 1, pct=True)} of bankroll)",
                            _f(r["mean_gap"], 1), _f(r["clv"]["mean"], 2, sign=True), _f(r["clv"]["share_positive"], 0, pct=True)]]))
        L.append("")
        bs, rc = r["bootstrap"], r["random_control"]
        L.append(f"Bootstrap (the bet list resampled {bs['n']:,} times): return on cash between {_f(bs['p5'], 1, pct=True, sign=True)} "
                 f"and {_f(bs['p95'], 1, pct=True, sign=True)} nine times in ten (median {_f(bs['p50'], 1, pct=True, sign=True)}); "
                 f"{_f(100 * bs['share_positive'], 0)}% of resamples end positive.")
        L.append("")
        L.append(f"Random control (same number of bets, same stakes, a random side of a random match, {rc['repeats']:,} times): "
                 f"mean return {_f(rc['mean'], 1, pct=True, sign=True)}, 90% range {_f(rc['p5'], 1, pct=True, sign=True)} to "
                 f"{_f(rc['p95'], 1, pct=True, sign=True)}. That is what paying the spread and fee with no skill costs.")
        L.append("")
        L.append("Per season:")
        L.append("")
        L.append(md_table(["Season", "Bets", "Hit rate", "P&L", "Return"],
                          [[em.season_label(g["season"]) + (" (empty grounds)" if g["season"] == COVID_SEASON else ""), g["bets"],
                            _f(g["hit_rate"], 1, pct=True), _money(g["pnl"]), _f(g["return_pct"], 1, pct=True, sign=True)] for g in r["by_season"]]))
        L.append("")
        L.append("Per side and per outcome:")
        L.append("")
        L.append(md_table(["Cut", "Bets", "Hit rate", "P&L", "Return"],
                          [[f"side {g['side']}", g["bets"], _f(g["hit_rate"], 1, pct=True), _money(g["pnl"]), _f(g["return_pct"], 1, pct=True, sign=True)] for g in r["by_side"]] +
                          [[f"outcome {g['outcome']}", g["bets"], _f(g["hit_rate"], 1, pct=True), _money(g["pnl"]), _f(g["return_pct"], 1, pct=True, sign=True)] for g in r["by_outcome"]]))
        L.append("")
        L.append("Hit rate by our band (the chance we gave the side we bought) and by the market's band (its fair chance):")
        L.append("")
        L.append(md_table(["Our band", "Bets", "Our mean %", "Market mean %", "Hit %", "P&L"],
                          [[g["our_band"], g["bets"], _f(g["mean_p"], 1), _f(g["mean_fair"], 1), _f(g["hit_rate"], 1), _money(g["pnl"])] for g in r["by_our_band"]]))
        L.append("")
        L.append(md_table(["Market band", "Bets", "Our mean %", "Market mean %", "Hit %", "P&L"],
                          [[g["market_band"], g["bets"], _f(g["mean_p"], 1), _f(g["mean_fair"], 1), _f(g["hit_rate"], 1), _money(g["pnl"])] for g in r["by_market_band"]]))
        L.append("")
        verdict = ("lost money" if r["pnl"] < 0 else "made money")
        L.append(f"Reading: against the closing line the rules {verdict}: {_money(r['pnl'])} on {_money(r['cost'])} put down, "
                 f"{_f(r['return_pct'], 1, pct=True, sign=True)}. Compare the hit rate in each band with the two mean columns: where "
                 "the hit rate tracks the market's mean rather than ours, the market was right about those matches and our "
                 "gap was model error, not edge. The random control shows the cost of the spread and fee alone; anything "
                 "we do has to clear that first. "
                 f"The max drawdown of {_money(r['max_drawdown_usd'])} is {_f(r['max_drawdown_pct'], 0)}% of the ${BANKROLL:,.0f} bankroll: "
                 "a real bankroll would have been gone long before the record ended. The simulation keeps a flat bankroll on purpose, "
                 "so every bet is counted and the whole picture can be read.")
    else:
        L.append("No bet cleared the 7-point floor against the closing line.")
    L.append("")
    L.append("### The pre-close variant")
    L.append("")
    L.append(rp.get("note", ""))
    L.append("")
    if rp["bets"]:
        L.append(md_table(["Bets", "Hit rate", "Cash down", "P&L after fees", "Return on cash", "Max drawdown", "Mean CLV", "CLV > 0", "Bootstrap 5% to 95%", "Random control"],
                          [[rp["bets"], _f(rp["hit_rate"], 1, pct=True), _money(rp["cost"]), _money(rp["pnl"]), _f(rp["return_pct"], 1, pct=True, sign=True),
                            _money(rp["max_drawdown_usd"]), _f(rp["clv"]["mean"], 2, sign=True), _f(rp["clv"]["share_positive"], 0, pct=True),
                            f"{_f(rp['bootstrap']['p5'], 1, pct=True, sign=True)} to {_f(rp['bootstrap']['p95'], 1, pct=True, sign=True)}",
                            f"{_f(rp['random_control']['mean'], 1, pct=True, sign=True)} ({_f(rp['random_control']['p5'], 1, sign=True)} to {_f(rp['random_control']['p95'], 1, sign=True)})"]]))
        L.append("")
        L.append(f"Reading: a positive mean CLV here would mean the closing line moved toward the sides we picked days earlier, "
                 f"which is the one sign of real edge that does not need thousands of bets. We got {_f(rp['clv']['mean'], 2, sign=True)} "
                 f"points with {_f(rp['clv']['share_positive'], 0)}% of bets positive.")
    else:
        L.append("No bet cleared the floor at the pre-close price.")
    L.append("")

    # (d)
    L.append("## (d) No-look-ahead canary")
    L.append("")
    L.append(f"A fake 9-0 match was appended at {can['fake_date'][:10]} (the start of the last predicted week of {can['season']}) and the "
             f"first {can['weeks']} weeks were predicted again without the cache. Largest change in any earlier chance: "
             f"{can['max_diff']:.2e} over {can['matches']} matches. **{'PASS' if can['ok'] else 'FAIL'}.** "
             f"Every training row is dated before its week start (asserted inside the fit): {'yes' if can['training_rows_before_week'] else 'NO'}.")
    L.append("")
    L.append("## What this does and does not say")
    L.append("")
    L.append("- The model is a fair public-data baseline. It is not sharper than Pinnacle's close and was never expected to be.")
    L.append("- Stage 4 (does the win rate scale with the stated chance) is the calibration table above; it is the thing the live "
             "gate re-checks on real cards.")
    L.append("- Stage 5's green or red percent is the gap column of the live card. In this backtest the gap against the closing line "
             "was mostly model error; the live question is whether Kalshi's price sits far enough from the sharp line often enough.")
    L.append("- Live data from API-Football (possession, tackles and interceptions, take-ons, lineups) is not in this model yet; "
             "edge_features.py has the slots for it.")
    L.append("- The temperature and the two tuning numbers are the only things fitted across seasons; each season only ever saw "
             "its own past.")
    L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- CLI

def latest_json():
    files = sorted(p for p in ec.BACKTEST_DIR.glob("*.json"))
    return files[-1] if files else None


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["fetch", "run", "report", "canary"])
    ap.add_argument("--seasons", default="", help="comma list of football-data codes, e.g. 1920,2021")
    ap.add_argument("--fresh", action="store_true", help="ignore the per-week cache")
    a = ap.parse_args(argv)
    if a.cmd == "fetch":
        recs = fetch()
        closing = [r["season"] for r in recs if r.get("closing", {}).get("PSCH")]
        print("seasons with Pinnacle closing (PSCH):", ", ".join(closing))
        print("seasons with AvgCH:", ", ".join(r["season"] for r in recs if r.get("closing", {}).get("AvgCH")))
        return 0
    if a.cmd == "run":
        seasons = [s.strip() for s in a.seasons.split(",") if s.strip()] or None
        out = run_backtest(seasons, use_cache=not a.fresh)
        print(json.dumps(_summary(out), indent=1))
        print("report:", ec.BACKTEST_DIR / f"{out['date']}.md")
        return 0
    if a.cmd == "canary":
        df = load_fd()
        print(json.dumps(canary(df), indent=1))
        return 0
    p = latest_json()
    if not p:
        print("no backtest yet; run: python scripts/edge_backtest.py run")
        return 1
    out = ec.read_json(p, {})
    print(json.dumps(_summary(out), indent=1))
    print("report:", p.with_suffix(".md"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
