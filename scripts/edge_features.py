"""Monarc Edge features (2026-10-04): Stage 2, the variables that influence the result, as home-minus-away numbers.

Each team's last N league matches (config model.window_matches, 10) strictly before the match date: goals for and
against, shots, shots on target, corners, points a match, rest days (days since the last match, from the fixture
list) and matches in the last 14 days. Venue-weighted: a match at the venue in question (the home side's home
matches, the away side's away matches) carries weight venue_weight (0.6) and a match at the other venue carries
1 - venue_weight, then a weighted mean. The output is home value minus away value for each, with both teams'
raw values kept for display.

Today the frame comes from football-data.co.uk (edge_backtest.load_fd). API-Football stats slot in later as extra
columns on the same frame, one home and one away column each, and come out as the same kind of differential or
None when the column is missing:
  possession  from columns h_possession, a_possession   (percent of the ball)
  steals      from columns h_steals, a_steals           (tackles won plus interceptions)
  jukes       from columns h_jukes, a_jukes             (take-ons completed: dribbles past a defender)

Nothing here reads a match dated on or after as_of. The date is floored to midnight UTC first, so a match on the
same day never counts, whatever its kickoff time.

  python scripts/edge_features.py "Arsenal" "Chelsea" 2026-10-10      print the features for one fixture
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import edge_common as ec  # noqa: E402

# feature -> (home column, away column); "for" stats read the team's own column, "against" the other side's
STATS = {
    "goals_for": ("hg", "ag"),
    "goals_against": ("ag", "hg"),
    "shots": ("hs", "as_"),
    "shots_on_target": ("hst", "ast"),
    "corners": ("hc", "ac"),
}
EXTRA = {                       # API-Football, later; None until the columns exist
    "possession": ("h_possession", "a_possession"),
    "steals": ("h_steals", "a_steals"),
    "jukes": ("h_jukes", "a_jukes"),
}
FEATURE_NAMES = list(STATS) + ["points_per_match", "rest_days", "matches_14d"] + list(EXTRA)


def _day(as_of):
    """as_of as a tz-aware UTC Timestamp floored to midnight."""
    if isinstance(as_of, str):
        ts = pd.Timestamp(ec.parse_iso(as_of))
    else:
        ts = pd.Timestamp(as_of)
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    return ts.normalize()


def _points(for_goals, against_goals):
    return np.where(for_goals > against_goals, 3.0, np.where(for_goals == against_goals, 1.0, 0.0))


def team_window(df, team, as_of, n=10, venue="home", venue_weight=0.6):
    """The team's last n matches before as_of, oldest first, with per-row weight and its own-side columns."""
    day = _day(as_of)
    past = df[((df["home"] == team) | (df["away"] == team)) & (df["date"] < day)]
    past = past.dropna(subset=["hg", "ag"]).sort_values("date").tail(n)
    assert len(past) == 0 or bool((past["date"] < day).all()), "feature window reached a match on or after as_of"
    at_home = (past["home"] == team).to_numpy()
    at_venue = at_home if venue == "home" else ~at_home
    w = np.where(at_venue, float(venue_weight), 1.0 - float(venue_weight))
    out = {"n": int(len(past)), "weights": w, "dates": past["date"].to_numpy(), "at_home": at_home}
    for name, (hcol, acol) in {**STATS, **EXTRA}.items():
        if hcol in past and acol in past:
            own = np.where(at_home, past[hcol].to_numpy(float), past[acol].to_numpy(float))
            out[name] = own
        else:
            out[name] = None
    gf, ga = out["goals_for"], out["goals_against"]
    out["points_per_match"] = _points(gf, ga) if gf is not None and len(past) else None
    last = past["date"].max() if len(past) else None
    out["rest_days"] = float((day - last).total_seconds() / 86400.0) if last is not None else None
    since = day - pd.Timedelta(days=14)
    out["matches_14d"] = float(((past["date"] >= since) & (past["date"] < day)).sum()) if len(past) else None
    return out


def _wmean(values, w):
    if values is None or len(values) == 0:
        return None
    v = np.asarray(values, float)
    ok = np.isfinite(v)
    if not ok.any():
        return None
    return float((v[ok] * w[ok]).sum() / w[ok].sum())


def build(fixtures_df, home, away, as_of, n=10, venue_weight=0.6):
    """Home-minus-away differentials for one fixture, plus each side's own numbers under "home" and "away".
    Keys: goals_for, goals_against, shots, shots_on_target, corners, points_per_match, rest_days, matches_14d,
    possession, steals, jukes (the last three None until API-Football columns exist). n_home and n_away say how
    many matches each window found; window_end is the last date either window used."""
    hw = team_window(fixtures_df, home, as_of, n=n, venue="home", venue_weight=venue_weight)
    aw = team_window(fixtures_df, away, as_of, n=n, venue="away", venue_weight=venue_weight)
    out = {"home": {}, "away": {}, "n_home": hw["n"], "n_away": aw["n"], "as_of": ec.iso(_day(as_of).to_pydatetime())}
    ends = [d for d in (hw["dates"].max() if hw["n"] else None, aw["dates"].max() if aw["n"] else None) if d is not None]
    out["window_end"] = ec.iso(pd.Timestamp(max(ends)).to_pydatetime()) if ends else None
    for name in FEATURE_NAMES:
        if name in ("rest_days", "matches_14d"):
            hv, av = hw[name], aw[name]
        else:
            hv, av = _wmean(hw[name], hw["weights"]), _wmean(aw[name], aw["weights"])
        out["home"][name] = hv
        out["away"][name] = av
        out[name] = (hv - av) if hv is not None and av is not None else None
    return out


# ---------------------------------------------------------------- lineups (pure, for API-Football later)

def lineup_share(start_xi, season_minutes_by_player):
    """How much of the usual team starts: the season minutes of the eleven named, over the minutes of the
    club's eleven biggest minute-getters. 1.0 is the full-strength side, 0.0 eleven players nobody has seen.
    Players missing from the minutes table count as zero."""
    mins = {str(k): float(v or 0.0) for k, v in (season_minutes_by_player or {}).items()}
    if not mins:
        return 0.0
    top = sorted(mins.values(), reverse=True)[:11]
    denom = sum(top)
    if denom <= 0:
        return 0.0
    got = sum(mins.get(str(p), 0.0) for p in (start_xi or []))
    return float(min(1.0, max(0.0, got / denom)))


def missing_regulars(start_xi, regulars):
    """The regulars (names or ids) not in the starting eleven, in the order given."""
    on = {str(p) for p in (start_xi or [])}
    return [r for r in (regulars or []) if str(r) not in on]


# ---------------------------------------------------------------- CLI

def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    import edge_backtest as bt
    df = bt.load_fd()
    cfg = ec.load_config().get("model", {})
    out = build(df, ec.norm(argv[0]), ec.norm(argv[1]), argv[2], n=int(cfg.get("window_matches", 10)),
                venue_weight=float(cfg.get("venue_weight", 0.6)))
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
