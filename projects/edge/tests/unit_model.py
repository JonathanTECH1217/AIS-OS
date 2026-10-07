"""Unit checks for the Monarc Edge model (scripts/edge_model.py, edge_features.py, edge_backtest.py, 2026-10-04).

Exposes tests(check): the runner passes check(name, ok, detail=""). On its own:
  python projects/edge/tests/unit_model.py

A synthetic league first: 20 teams with known attack and defence, home advantage 0.25, rho -0.1, six simulated
seasons; the fit has to recover them. Then the score grid sums, the de-vig helpers, the calibration table and the
temperature on simulated true chances, the no-look-ahead canary, the worked six-side example from the interview,
and ModelService on two real teams (needs the season CSVs in data/fd; reported as a skip when they are missing).
The synthetic parts stay under 60 s.
"""
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import edge_common as ec  # noqa: E402
import edge_model as em  # noqa: E402
import edge_features as ef  # noqa: E402
import edge_backtest as bt  # noqa: E402

N_TEAMS, SEASONS, HOME_ADV, RHO, MU = 20, 6, 0.25, -0.10, 0.18


def true_grid(lam, m, rho):
    return em.apply_rho(em.poisson_grid(lam, m), lam, m, rho)


def synthetic_league(seed=7):
    """Six double round-robin seasons from known numbers. Shots on target are drawn so that the conversion rate
    is 0.3 and the shots carry the same strengths as the goals."""
    rng = np.random.default_rng(seed)
    teams = [f"team{i:02d}" for i in range(N_TEAMS)]
    attack = rng.normal(0, 0.30, N_TEAMS)
    attack -= attack.mean()
    defence = rng.normal(0, 0.25, N_TEAMS)
    defence -= defence.mean()
    truth = {"attack": attack, "defence": defence}
    rows = []
    pairs = [(i, j) for i in range(N_TEAMS) for j in range(N_TEAMS) if i != j]
    cells = [(i, j) for i in range(em.MAX_GOALS + 1) for j in range(em.MAX_GOALS + 1)]
    for s in range(SEASONS):
        start = pd.Timestamp("2018-08-11", tz="UTC") + pd.Timedelta(days=365 * s)
        order = rng.permutation(len(pairs))
        for k, idx in enumerate(order):
            i, j = pairs[idx]
            lam = math.exp(MU + HOME_ADV + attack[i] + defence[j])
            m = math.exp(MU + attack[j] + defence[i])
            g = true_grid(lam, m, RHO).ravel()
            hg, ag = cells[rng.choice(len(cells), p=g / g.sum())]
            rows.append({"date": start + pd.Timedelta(days=7 * (k // 10)), "season": f"0{s + 1}", "home": teams[i],
                         "away": teams[j], "home_raw": teams[i], "away_raw": teams[j], "hg": float(hg), "ag": float(ag),
                         "result": "H" if hg > ag else ("D" if hg == ag else "A"),
                         "hst": float(rng.poisson(lam / 0.3)), "ast": float(rng.poisson(m / 0.3)),
                         "hs": np.nan, "as_": np.nan, "hc": np.nan, "ac": np.nan, "time": ""})
    df = pd.DataFrame(rows).sort_values(["date", "home"], kind="stable").reset_index(drop=True)
    return df, teams, truth, rng


def tests(check):
    t0 = time.time()
    df, teams, truth, rng = synthetic_league()
    as_of = df["date"].max() + pd.Timedelta(days=1)

    # ---- the fit recovers the league
    for blend in (0.0, 0.5):
        p = em.fit_dixon_coles(df, as_of, xi=0.0, sot_blend=blend, max_days=None)
        a = np.array([p.strength(t)[0] for t in teams])
        d = np.array([p.strength(t)[1] for t in teams])
        ca = float(np.corrcoef(a, truth["attack"])[0, 1])
        cd = float(np.corrcoef(d, truth["defence"])[0, 1])
        tag = f"sot_blend {blend}"
        check(f"synthetic: attack correlation above 0.95 ({tag})", ca > 0.95, f"{ca:.3f}")
        check(f"synthetic: defence correlation above 0.95 ({tag})", cd > 0.95, f"{cd:.3f}")
        check(f"synthetic: home advantage within 0.05 ({tag})", abs(p.home - HOME_ADV) < 0.05, f"{p.home:.3f} vs {HOME_ADV}")
        check(f"synthetic: rho within 0.05 ({tag})", abs(p.rho - RHO) < 0.05, f"{p.rho:.3f} vs {RHO}")
        if blend == 0.5:
            check("synthetic: conversion rate near 0.3", abs(p.conv - 0.3) < 0.03, f"{p.conv:.3f}")
        # 1,000 held-out matches against the true chances
        errs = []
        for _ in range(1000):
            i, j = rng.choice(N_TEAMS, 2, replace=False)
            lam = math.exp(MU + HOME_ADV + truth["attack"][i] + truth["defence"][j])
            m = math.exp(MU + truth["attack"][j] + truth["defence"][i])
            tp = em.grid_to_three(true_grid(lam, m, RHO))
            fp = em.three_way(p, teams[i], teams[j])
            errs.append(np.abs(np.array(tp) - np.array(fp)).mean())
        # six seasons of goals alone leave about 2 points of sampling noise in the strengths (1.75 to 2.45 over
        # seeds; a 30-season fit lands on the true numbers), so the 2-point bar is for the configured model with
        # shots blended in; goals alone is checked against its noise floor
        bar = 0.02 if blend > 0 else 0.025
        check(f"synthetic: three-way chances within {100 * bar:.1f} points on 1,000 held-out matches ({tag})", float(np.mean(errs)) < bar,
              f"mean abs diff {100 * np.mean(errs):.2f} points" + ("" if blend > 0 else ", the noise floor for goals alone"))

    # ---- grids and sums
    ok_before = ok_after = True
    for lam, m, rho in ((1.2, 0.9, -0.1), (2.6, 0.4, 0.05), (0.7, 1.9, -0.2)):
        g = em.poisson_grid(lam, m)
        ok_before &= abs(g.sum() - 1.0) < 1e-9
        ok_after &= abs(em.apply_rho(g, lam, m, rho).sum() - 1.0) < 1e-9
    check("score grid sums to 1 before rho", ok_before)
    check("score grid sums to 1 after rho", ok_after)
    p3 = em.three_way(p, teams[0], teams[1])
    check("P(home) + P(draw) + P(away) = 1", abs(sum(p3) - 1.0) < 1e-9, f"{sum(p3):.12f}")
    check("temperature keeps the sum at 1", abs(sum(em.apply_temperature(p3, 1.3)) - 1.0) < 1e-9)

    # ---- de-vig helpers
    odds = [1.5, 4.2, 6.5]
    pr = ec.devig_proportional(odds)
    pw = ec.devig_power(odds)
    check("de-vig proportional sums to 1", abs(sum(pr) - 1.0) < 1e-9)
    check("de-vig power sums to 1", abs(sum(pw) - 1.0) < 1e-9)
    check("power gives the longshot less than proportional", pw[2] < pr[2], f"power {pw[2]:.4f} proportional {pr[2]:.4f}")

    # ---- calibration table on true chances, and a shifted copy
    P = rng.dirichlet([2.0, 1.6, 1.6], 6000)
    y = np.array([rng.choice(3, p=row) for row in P])
    tab = bt.calibration_table(P, y, min_n=30)
    check("calibration: every band passes on true chances", all(r["pass"] for r in tab["rows"]),
          ", ".join(f"{r['band']} {'ok' if r['pass'] else 'FAIL'}" for r in tab["rows"]))
    check("calibration: slope near 1 on true chances", abs(tab["slope"] - 1.0) < 0.1, f"{tab['slope']:.3f}")
    Ps = P.copy()
    Ps[:, 0] += 0.08
    Ps[:, 2] -= 0.08
    Ps = np.clip(Ps, 0.005, 0.995)
    Ps /= Ps.sum(axis=1, keepdims=True)
    tab2 = bt.calibration_table(Ps, y, min_n=30)
    failed = [r["band"] for r in tab2["rows"] if not r["pass"]]
    check("calibration: a copy shifted by 8 points fails", len(failed) > 0, f"failed bands {failed}")

    # ---- temperature recovers a known over-confidence
    P2 = rng.dirichlet([2.0, 1.6, 1.6], 20000)
    y2 = np.array([rng.choice(3, p=row) for row in P2])
    sharp = np.array([em.apply_temperature(row, 0.7) for row in P2])
    t_hat = em.fit_temperature(sharp, y2)
    check("temperature fit recovers 1/0.7", abs(t_hat - 1 / 0.7) < 0.1, f"{t_hat:.3f} vs {1 / 0.7:.3f}")
    check("temperature fit on true chances is near 1", abs(em.fit_temperature(P2, y2) - 1.0) < 0.08)

    # ---- no look-ahead
    can = bt.canary(df, season="06", weeks=3, xi=0.002, blend=0.5)
    check("canary: a fake 9-0 in the future moves no earlier chance", can["ok"], f"max diff {can['max_diff']:.2e} over {can['matches']} matches")
    some = df[df["season"] == "04"].iloc[100]
    train = em._training_rows(df, some["date"], em.TRAIN_DAYS)
    check("every training row is dated before the match", bool((train["date"] < some["date"]).all()))
    f = ef.build(df, some["home"], some["away"], some["date"])
    check("every feature window row is dated before the match", f["window_end"] is not None and f["window_end"] < f["as_of"],
          f"window_end {f['window_end']} as_of {f['as_of']}")
    check("features: a same-day match never counts", bool(ef.team_window(df, some["home"], some["date"])["dates"].max() < some["date"]))
    check("features: API-Football slots are None until the columns exist", f["possession"] is None and f["steals"] is None and f["jukes"] is None)
    check("features: rest days and matches in 14 days present", f["rest_days"] is not None and f["matches_14d"] is not None)

    # ---- the worked six-side example (model 38/33/29; Kalshi home 44/46, tie 22/24, away 30/32)
    model = {"home": 0.38, "draw": 0.33, "away": 0.29}
    book = {"home": (0.44, 0.46), "draw": (0.22, 0.24), "away": (0.30, 0.32)}
    got = {}
    for o, p_ in model.items():
        bid, ask = book[o]
        g = ec.gap_and_side(p_, ask, 1.0 - bid)
        got[o] = g
    check("six sides: Tie Yes about +7.7 (green)", got["draw"]["side"] == "yes" and round(got["draw"]["gap"], 1) == 7.7
          and ec.color_of(got["draw"]["gap"], 7.0) == "green", f"{got['draw']['side']} {got['draw']['gap']:.2f}")
    check("six sides: Home No about +4.3 (amber)", got["home"]["side"] == "no" and round(got["home"]["gap"], 1) == 4.3
          and ec.color_of(got["home"]["gap"], 7.0) == "amber", f"{got['home']['side']} {got['home']['gap']:.2f}")
    check("six sides: the other four are red", got["home"]["gap_yes"] < 0 and got["draw"]["gap_no"] < 0
          and got["away"]["gap_yes"] < 0 and got["away"]["gap_no"] < 0,
          f"home yes {got['home']['gap_yes']:.1f} tie no {got['draw']['gap_no']:.1f} away yes {got['away']['gap_yes']:.1f} away no {got['away']['gap_no']:.1f}")
    best = max(got.items(), key=lambda kv: kv[1]["gap"])
    check("six sides: the single bet is Tie Yes", best[0] == "draw" and best[1]["side"] == "yes")

    # ---- the live service on two real teams
    if list(ec.FD_DIR.glob("E0-*.csv")):
        svc = em.ModelService()
        out = svc.predict_fixture("Arsenal", "Chelsea", "2026-10-10T14:00:00Z")
        ok = out is not None and abs(out["p_home"] + out["p_draw"] + out["p_away"] - 1.0) < 1e-9 and bool(out["version"])
        check("ModelService.predict_fixture: three chances summing to 1 and a version", ok,
              "" if not out else f"{out['p_home']:.3f}/{out['p_draw']:.3f}/{out['p_away']:.3f} v{out['version']}")
        check("ModelService: contributions and ratings present", bool(out) and len(out["contributions"]) >= 3 and 1 <= out["ratings"]["home"] <= 99)
        check("ModelService: 'Manchester United' resolves through the alias map", svc.resolve("Manchester United") == "man united")
        check("ModelService: an unknown name returns None", svc.predict_fixture("Arsenal", "Real Madrid", "2026-10-10T14:00:00Z") is None)
        check("ModelService: same team twice returns None", svc.predict_fixture("Arsenal", "Arsenal", "2026-10-10T14:00:00Z") is None)
    else:
        check("ModelService.predict_fixture (skipped: no CSVs in data/fd)", True, "run: python scripts/edge_backtest.py fetch")
    check("synthetic tests under 60 s", time.time() - t0 < 60, f"{time.time() - t0:.1f} s")


if __name__ == "__main__":
    fails = []

    def check(name, ok, detail=""):
        print(("ok   " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))
        if not ok:
            fails.append(name)

    tests(check)
    print(f"\n{len(fails)} failed")
    sys.exit(1 if fails else 0)
