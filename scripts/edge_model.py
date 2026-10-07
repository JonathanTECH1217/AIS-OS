"""Monarc Edge model (2026-10-04): the Dixon-Coles goals model that gives each Premier League match three chances.

Plain words: each team gets an attack number and a defence number. The league has a base scoring rate and a home
advantage. A team's expected goals = base x its attack x the other side's defence (x the home advantage at home).
Goals follow a Poisson count (the count you get when chances arrive at a steady rate). One extra number, rho,
fixes the known shortfall of 0-0 and 1-1 draws in a plain Poisson. Older matches count less: weight
exp(-xi * days_ago), xi about 0.002 a day, so a match a year old counts about half. The numbers are found by
maximising the weighted log likelihood (how well the model explains the scores) with L-BFGS-B, with the attack
numbers held to average zero (and the defence numbers too, so the base rate is one clear number).

Upgrade 1 (sot_blend): the strengths are fitted on a weighted sum of two likelihoods, one on real goals and one on
"shots on target x the league's conversion rate" (about 0.3, computed from the training rows). Shots on target
are the less noisy signal; with sot_blend 0.5 each counts half. The rho term applies to real goals only.

Calibration: one temperature T, fitted on earlier out-of-sample predictions only (the previous season's
walk-forward predictions), never on the season being scored. Applied as p to the power 1/T, then renormalised
(T above 1 softens an over-confident model, T under 1 sharpens a timid one).

Promoted teams: a team with no matches in the training window starts at the average fitted strength of the teams
promoted in the previous three seasons (computed inside the fit from the training rows). A team with only a few
matches is pulled toward that same value by a weak ridge penalty (weight 1 on the squared distance; 38 matches
already outweigh it about 25 to 1). Teams present from the start of the window are pulled toward the league
average instead.

  python scripts/edge_model.py fit            fit from the last three season CSVs in data/fd and save the weights
  python scripts/edge_model.py predict "Arsenal" "Chelsea" 2026-10-10T14:00:00Z
  python scripts/edge_model.py show           print the current weights as a table

Weights live in projects/edge/model/weights-<version>.json; latest.json points at the current version.
The CSV loader is scripts/edge_backtest.py (load_fd); this module imports it only when it needs to fit.
"""
import hashlib
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize, minimize_scalar
from scipy.special import gammaln

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import edge_common as ec  # noqa: E402

MAX_GOALS = 10                    # the score grid runs 0..10 goals a side (11 x 11), then is renormalised
RHO_BOUND = 0.25                  # rho is searched inside [-0.25, 0.25]; real values sit near -0.05 to -0.13
RIDGE = 1.0                       # weight on (strength - its centre)^2; weak, keeps a team with no data at its centre
DEFAULT_PRIOR = (-0.25, 0.20)     # a promoted team before any are measured: scores ~22% fewer, concedes ~22% more
TRAIN_DAYS = 1460                 # four years back; a row that old weighs under 0.25 even at xi 0.001
FEATURES = ["goals", "shots_on_target_x_conversion", "home_advantage", "time_decay", "dixon_coles_rho"]
PLAIN = {
    "attack": "Attack (goals scored, home minus away)",
    "defence": "Defence (goals allowed, away minus home)",
    "home_edge": "Home edge",
    "sot_last10": "Shots on target, last 10 (home minus away)",
    "rest_days": "Rest days (home minus away)",
    "matches_14d": "Matches in the last 14 days (home minus away)",
}
# Common names for the football-data.co.uk spellings, after edge_common.norm. Used when teams.json is missing.
ALIASES = {
    "manchester united": "man united", "man utd": "man united", "manchester city": "man city",
    "newcastle united": "newcastle", "tottenham hotspur": "tottenham", "spurs": "tottenham",
    "wolverhampton wanderers": "wolves", "wolverhampton": "wolves", "nottingham forest": "nottm forest",
    "forest": "nottm forest", "brighton hove albion": "brighton", "brighton and hove albion": "brighton",
    "west ham united": "west ham", "leicester city": "leicester", "leeds united": "leeds",
    "luton town": "luton", "ipswich town": "ipswich", "norwich city": "norwich", "coventry city": "coventry",
    "west bromwich albion": "west brom", "west bromwich": "west brom", "huddersfield town": "huddersfield",
    "cardiff city": "cardiff", "swansea city": "swansea", "stoke city": "stoke", "hull city": "hull",
    "sheffield utd": "sheffield united", "sheff utd": "sheffield united", "sheffield wednesday": "sheffield weds",
    "birmingham city": "birmingham", "blackburn rovers": "blackburn", "bolton wanderers": "bolton",
    "charlton athletic": "charlton", "derby county": "derby", "wigan athletic": "wigan",
    "queens park rangers": "qpr", "reading fc": "reading",
}


def _ts(t):
    """Anything date-like to a tz-aware UTC pandas Timestamp."""
    if isinstance(t, pd.Timestamp):
        ts = t
    elif isinstance(t, str):
        ts = pd.Timestamp(ec.parse_iso(t))
    else:
        ts = pd.Timestamp(t)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


# ---------------------------------------------------------------- parameters

@dataclass
class Params:
    """One fitted model. attack[i] and defence[i] go with teams[i] (keys are edge_common.norm of the
    football-data name). prior is (attack, defence) for a team the fit has not seen (a newly promoted side)."""
    teams: list
    attack: np.ndarray
    defence: np.ndarray
    mu: float
    home: float
    rho: float
    xi: float
    sot_blend: float
    conv: float
    prior: tuple
    as_of: str
    n_rows: int
    loglik: float
    seasons: list = field(default_factory=list)
    temperature: float = 1.0
    centres: dict = field(default_factory=dict)   # team -> "prior" | "average" (which centre the ridge used)

    def index(self):
        return {t: i for i, t in enumerate(self.teams)}

    def strength(self, team):
        """(attack, defence) for a team key; the promoted prior when the fit never saw it."""
        i = self.index().get(team)
        if i is None:
            return float(self.prior[0]), float(self.prior[1])
        return float(self.attack[i]), float(self.defence[i])

    def knows(self, team):
        return team in self.index()

    def to_dict(self):
        return {
            "teams": {t: {"attack": round(float(a), 6), "defence": round(float(d), 6)}
                      for t, a, d in zip(self.teams, self.attack, self.defence)},
            "mu": self.mu, "home": self.home, "rho": self.rho, "xi": self.xi, "sot_blend": self.sot_blend,
            "conv": self.conv, "prior": [float(self.prior[0]), float(self.prior[1])], "as_of": self.as_of,
            "n_rows": self.n_rows, "loglik": self.loglik, "seasons": list(self.seasons),
            "temperature": self.temperature, "centres": self.centres,
        }

    @classmethod
    def from_dict(cls, d):
        teams = sorted(d["teams"])
        return cls(teams=teams,
                   attack=np.array([d["teams"][t]["attack"] for t in teams], float),
                   defence=np.array([d["teams"][t]["defence"] for t in teams], float),
                   mu=float(d["mu"]), home=float(d["home"]), rho=float(d["rho"]), xi=float(d["xi"]),
                   sot_blend=float(d["sot_blend"]), conv=float(d["conv"]), prior=tuple(d["prior"]),
                   as_of=d.get("as_of", ""), n_rows=int(d.get("n_rows", 0)), loglik=float(d.get("loglik", 0.0)),
                   seasons=list(d.get("seasons", [])), temperature=float(d.get("temperature", 1.0)),
                   centres=dict(d.get("centres", {})))


# ---------------------------------------------------------------- the fit

def _training_rows(df, as_of, max_days):
    rows = df[df["date"] < as_of]
    if max_days:
        rows = rows[rows["date"] >= as_of - pd.Timedelta(days=max_days)]
    rows = rows.dropna(subset=["hg", "ag"])
    if len(rows) == 0:
        raise ValueError(f"no training rows before {as_of}")
    assert bool((rows["date"] < as_of).all()), "a training row is dated on or after as_of"
    return rows


def _centres(rows, teams, prior):
    """Which centre the ridge pulls each team toward: the promoted prior for a team whose first season in the
    window is not the window's first season, the league average (0, 0) otherwise."""
    seasons = sorted(rows["season"].unique())
    first = {}
    for s in seasons:
        for t in set(rows.loc[rows["season"] == s, "home"]) | set(rows.loc[rows["season"] == s, "away"]):
            first.setdefault(t, s)
    a0 = np.zeros(len(teams))
    d0 = np.zeros(len(teams))
    kind = {}
    for i, t in enumerate(teams):
        if seasons and first.get(t) != seasons[0]:
            a0[i], d0[i] = prior
            kind[t] = "prior"
        else:
            kind[t] = "average"
    return a0, d0, kind


def promoted_prior(rows, params, fallback=DEFAULT_PRIOR, last=3):
    """Average fitted strength of the teams promoted in the last `last` seasons of the training rows. A team is
    promoted into season s when it played in s but not in s-1 (both seasons must be in the rows)."""
    codes = sorted(rows["season"].unique())
    by_season = {s: set(rows.loc[rows["season"] == s, "home"]) | set(rows.loc[rows["season"] == s, "away"])
                 for s in codes}
    found = []
    for prev, cur in list(zip(codes[:-1], codes[1:]))[-last:]:
        for t in sorted(by_season[cur] - by_season[prev]):
            if params.knows(t):
                found.append(params.strength(t))
    if not found:
        return tuple(fallback)
    arr = np.array(found)
    return float(arr[:, 0].mean()), float(arr[:, 1].mean())


def _prepare(rows, teams, as_of, xi, sot_blend):
    idx = {t: i for i, t in enumerate(teams)}
    hi = rows["home"].map(idx).to_numpy(int)
    ai = rows["away"].map(idx).to_numpy(int)
    x = rows["hg"].to_numpy(float)
    y = rows["ag"].to_numpy(float)
    days = (as_of - rows["date"]).dt.total_seconds().to_numpy() / 86400.0
    w = np.exp(-xi * days)
    hst = rows["hst"].to_numpy(float) if "hst" in rows else np.full(len(rows), np.nan)
    ast = rows["ast"].to_numpy(float) if "ast" in rows else np.full(len(rows), np.nan)
    ok = np.isfinite(hst) & np.isfinite(ast) & (sot_blend > 0)
    if ok.any():
        conv = float((w[ok] * (x[ok] + y[ok])).sum() / max(1e-9, (w[ok] * (hst[ok] + ast[ok])).sum()))
    else:
        conv = 0.3
    xs = np.where(ok, hst * conv, 0.0)
    ys = np.where(ok, ast * conv, 0.0)
    beta = np.where(ok, float(sot_blend), 0.0)
    cell = np.zeros(len(rows), int)
    cell[(x == 0) & (y == 0)] = 1
    cell[(x == 0) & (y == 1)] = 2
    cell[(x == 1) & (y == 0)] = 3
    cell[(x == 1) & (y == 1)] = 4
    return dict(hi=hi, ai=ai, x=x, y=y, w=w, xs=xs, ys=ys, beta=beta, cell=cell, conv=conv, n=len(teams))


def _objective(theta, P, a0, d0, ridge):
    """Negative weighted log likelihood (goals part with the rho term, plus the shots-on-target part) and its
    gradient. theta = [attack (n), defence (n), mu, home, rho]; attack and defence are centred inside."""
    n = P["n"]
    a = theta[:n]
    d = theta[n:2 * n]
    mu, h, rho = theta[2 * n], theta[2 * n + 1], theta[2 * n + 2]
    ac = a - a.mean()
    dc = d - d.mean()
    hi, ai, x, y, w, xs, ys, beta, cell = (P[k] for k in ("hi", "ai", "x", "y", "w", "xs", "ys", "beta", "cell"))
    llh = mu + h + ac[hi] + dc[ai]
    lla = mu + ac[ai] + dc[hi]
    lam = np.exp(llh)
    m = np.exp(lla)
    # the rho (Dixon-Coles) correction on the four low-score cells
    tau = np.ones_like(lam)
    dtl = np.zeros_like(lam)   # d tau / d log lambda
    dtm = np.zeros_like(lam)   # d tau / d log mu
    dtr = np.zeros_like(lam)   # d tau / d rho
    c = cell == 1
    tau[c] = 1.0 - lam[c] * m[c] * rho
    dtl[c] = -lam[c] * m[c] * rho
    dtm[c] = -lam[c] * m[c] * rho
    dtr[c] = -lam[c] * m[c]
    c = cell == 2
    tau[c] = 1.0 + lam[c] * rho
    dtl[c] = lam[c] * rho
    dtr[c] = lam[c]
    c = cell == 3
    tau[c] = 1.0 + m[c] * rho
    dtm[c] = m[c] * rho
    dtr[c] = m[c]
    c = cell == 4
    tau[c] = 1.0 - rho
    dtr[c] = -1.0
    low = tau < 1e-6
    tau = np.where(low, 1e-6, tau)
    dtl[low] = dtm[low] = dtr[low] = 0.0
    goals = x * llh - lam + y * lla - m + np.log(tau)
    shots = xs * llh - lam + ys * lla - m
    ll = float((w * ((1.0 - beta) * goals + beta * shots)).sum())
    pen = ridge * float(((ac - a0) ** 2).sum() + ((dc - d0) ** 2).sum())
    gl = w * ((1.0 - beta) * (x - lam + dtl / tau) + beta * (xs - lam))
    gm = w * ((1.0 - beta) * (y - m + dtm / tau) + beta * (ys - m))
    ga = np.bincount(hi, gl, n) + np.bincount(ai, gm, n) - 2.0 * ridge * (ac - a0)
    gd = np.bincount(ai, gl, n) + np.bincount(hi, gm, n) - 2.0 * ridge * (dc - d0)
    ga -= ga.mean()      # centring: the gradient has no component along "add a constant to every team"
    gd -= gd.mean()
    gmu = gl.sum() + gm.sum()
    gh = gl.sum()
    grho = float((w * (1.0 - beta) * dtr / tau).sum())
    grad = np.concatenate([ga, gd, [gmu, gh, grho]])
    return -(ll - pen), -grad


def _fit_once(rows, teams, as_of, xi, sot_blend, prior, init, ridge):
    P = _prepare(rows, teams, as_of, xi, sot_blend)
    a0, d0, kind = _centres(rows, teams, prior)
    n = len(teams)
    theta = np.concatenate([a0, d0, [math.log(max(0.5, (P["x"].mean() + P["y"].mean()) / 2.0)), 0.25, -0.05]])
    if init is not None:
        idx = init.index()
        for i, t in enumerate(teams):
            j = idx.get(t)
            if j is not None:
                theta[i] = init.attack[j]
                theta[n + i] = init.defence[j]
        theta[2 * n:] = [init.mu, init.home, init.rho]
    bounds = [(-4.0, 4.0)] * (2 * n) + [(-3.0, 3.0), (-1.5, 1.5), (-RHO_BOUND, RHO_BOUND)]
    res = minimize(_objective, theta, args=(P, a0, d0, ridge), jac=True, method="L-BFGS-B", bounds=bounds,
                   options={"maxiter": 2000, "ftol": 1e-12, "gtol": 1e-7})
    th = res.x
    a = th[:n] - th[:n].mean()
    d = th[n:2 * n] - th[n:2 * n].mean()
    seasons = sorted(rows["season"].unique().tolist())
    return Params(teams=list(teams), attack=a, defence=d, mu=float(th[2 * n]), home=float(th[2 * n + 1]),
                  rho=float(th[2 * n + 2]), xi=float(xi), sot_blend=float(sot_blend), conv=float(P["conv"]),
                  prior=tuple(prior), as_of=ec.iso(as_of.to_pydatetime()), n_rows=int(len(rows)),
                  loglik=float(-res.fun), seasons=seasons, centres=kind)


def fit_dixon_coles(df, as_of, xi=0.002, sot_blend=0.5, init=None, max_days=TRAIN_DAYS, ridge=RIDGE):
    """Fit on the rows of `df` dated strictly before `as_of` (and within max_days of it). `init` is an earlier
    Params for a warm start and the promoted prior; without one the fit runs twice, the second pass centred on the
    promoted prior the first pass measured. Returns Params."""
    as_of = _ts(as_of)
    rows = _training_rows(df, as_of, max_days)
    teams = sorted(set(rows["home"]) | set(rows["away"]))
    prior = tuple(init.prior) if init is not None else DEFAULT_PRIOR
    params = _fit_once(rows, teams, as_of, xi, sot_blend, prior, init, ridge)
    new_prior = promoted_prior(rows, params, fallback=prior)
    if init is None:
        params = _fit_once(rows, teams, as_of, xi, sot_blend, new_prior, params, ridge)
        new_prior = promoted_prior(rows, params, fallback=new_prior)
    params.prior = new_prior
    return params


# ---------------------------------------------------------------- predictions

def rates(params, home, away):
    """Expected goals (home, away) for one match."""
    ah, dh = params.strength(home)
    aa, da = params.strength(away)
    lam = math.exp(params.mu + params.home + ah + da)
    m = math.exp(params.mu + aa + dh)
    return lam, m


def poisson_grid(lam, m, max_goals=MAX_GOALS):
    """P(home goals = i, away goals = j) for i, j in 0..max_goals, renormalised to sum to 1."""
    k = np.arange(max_goals + 1)
    ph = np.exp(k * math.log(lam) - lam - gammaln(k + 1))
    pa = np.exp(k * math.log(m) - m - gammaln(k + 1))
    g = np.outer(ph, pa)
    return g / g.sum()


def apply_rho(grid, lam, m, rho):
    """The Dixon-Coles correction on the four low-score cells. The four changes cancel, so the sum stays 1."""
    g = grid.copy()
    g[0, 0] *= 1.0 - lam * m * rho
    g[0, 1] *= 1.0 + lam * rho
    g[1, 0] *= 1.0 + m * rho
    g[1, 1] *= 1.0 - rho
    return g


def grid_to_three(grid):
    ph = float(np.tril(grid, -1).sum())
    pd_ = float(np.trace(grid))
    pa = float(np.triu(grid, 1).sum())
    s = ph + pd_ + pa
    return ph / s, pd_ / s, pa / s


def three_way(params, home, away):
    """(P home win, P draw, P away win) from the score grid, before the temperature."""
    lam, m = rates(params, home, away)
    g = apply_rho(poisson_grid(lam, m), lam, m, params.rho)
    return grid_to_three(g)


def apply_temperature(p3, t):
    """Divide the log-chances by t and renormalise. t = 1 leaves them alone."""
    if not t or abs(t - 1.0) < 1e-12:
        s = sum(p3)
        return tuple(float(p) / s for p in p3)
    lp = np.log(np.clip(np.asarray(p3, float), 1e-12, 1.0)) / t
    lp -= lp.max()
    e = np.exp(lp)
    e /= e.sum()
    return tuple(float(v) for v in e)


def fit_temperature(P, y, lo=0.3, hi=3.0):
    """The t that gives the lowest log loss on raw chances P (n x 3) and results y (0 home, 1 draw, 2 away).
    Only ever call this on out-of-sample predictions."""
    P = np.clip(np.asarray(P, float), 1e-12, 1.0)
    y = np.asarray(y, int)
    lp = np.log(P)

    def loss(t):
        z = lp / t
        z -= z.max(axis=1, keepdims=True)
        q = np.exp(z)
        q /= q.sum(axis=1, keepdims=True)
        return -np.log(np.clip(q[np.arange(len(y)), y], 1e-12, 1.0)).mean()

    res = minimize_scalar(loss, bounds=(lo, hi), method="bounded", options={"xatol": 1e-5})
    return float(res.x)


def rating(attack, defence):
    """0 to 100 strength: 50 + 20 x (attack - defence), clipped to 1..99. Ten points of rating = a team that
    outscores the other by e^0.5 (about 1.65 to 1) on neutral ground; twenty points = e^1 (about 2.7 to 1)."""
    return int(min(99, max(1, round(50.0 + 20.0 * (attack - defence)))))


# ---------------------------------------------------------------- the service

def _version_of(features, seasons, fit_date):
    raw = json.dumps({"features": features, "seasons": list(seasons), "fit_date": fit_date}, sort_keys=True)
    return hashlib.sha1(raw.encode()).hexdigest()[:8]


def season_label(code):
    """'1920' -> '2019/20'."""
    code = str(code)
    return f"20{code[:2]}/{code[2:]}"


class ModelService:
    """The live model behind the server. Loads the latest weights from projects/edge/model, or fits from the last
    three season CSVs in data/fd and saves them. Cheap: a load is instant, a fit is well under 5 s."""

    def __init__(self, cfg=None, fit_if_missing=True):
        self.cfg = cfg or ec.load_config()
        self.params = None
        self.version = ""
        self.sources = []
        self.df = None
        self._teams_cache = None
        ec.ensure_dirs()
        latest = ec.read_json(ec.MODEL_DIR / "latest.json", {}) or {}
        path = ec.MODEL_DIR / f"weights-{latest.get('version', '')}.json" if latest.get("version") else None
        if path is not None and path.exists():
            data = ec.read_json(path, {})
            self.params = Params.from_dict(data["params"])
            self.version = data.get("version", latest["version"])
            self.sources = data.get("sources", [])
        elif fit_if_missing:
            self.refresh(download=False)

    # ---- fitting
    def _codes(self, k=3):
        files = sorted(ec.FD_DIR.glob("E0-*.csv"))
        return [p.stem.split("-", 1)[1] for p in files][-k:]

    def _settings(self):
        """xi, sot_blend and temperature: the backtest's live pick when a report exists, else the config."""
        mcfg = self.cfg.get("model", {})
        xi, blend, temp = 0.002, float(mcfg.get("sot_blend", 0.5)), 1.0
        reports = sorted(ec.BACKTEST_DIR.glob("*.json"))
        if reports:
            live = (ec.read_json(reports[-1], {}) or {}).get("live") or {}
            xi = float(live.get("xi", xi))
            blend = float(live.get("sot_blend", blend))
            temp = float(live.get("temperature", temp))
        return xi, blend, temp

    def refresh(self, download=True):
        """Refit from the latest CSVs (the loop calls this weekly). Returns the version."""
        import edge_backtest as bt
        if download:
            try:
                bt.fetch(bt.SEASON_CODES[-2:], quiet=True)
            except Exception as e:  # the fit still runs on what is on disk
                ec.log("edge_model: download skipped:", str(e)[:120])
        codes = self._codes()
        if not codes:
            raise FileNotFoundError(f"no E0-*.csv in {ec.FD_DIR}; run: python scripts/edge_backtest.py fetch")
        self.df = bt.load_fd(codes)
        xi, blend, temp = self._settings()
        params = fit_dixon_coles(self.df, _ts(ec.now()), xi=xi, sot_blend=blend)
        params.temperature = temp
        fit_date = ec.iso(ec.now())
        self.version = _version_of(FEATURES, codes, fit_date)
        self.params = params
        self.sources = [f"football-data.co.uk E0 {season_label(codes[0])} to {season_label(codes[-1])}"]
        data = {"version": self.version, "fit_date": fit_date, "features": FEATURES, "training_seasons": codes,
                "sources": self.sources, "params": params.to_dict()}
        ec.write_json_atomic(ec.MODEL_DIR / f"weights-{self.version}.json", data, indent=1)
        ec.write_json_atomic(ec.MODEL_DIR / "latest.json", {"version": self.version, "fit_date": fit_date}, indent=1)
        return self.version

    # ---- names
    def resolve(self, name):
        """A team name from Kalshi, API-Football or a person -> the model's key (the normalised football-data
        name), or None. teams.json first when it exists, then the alias map, then the known team list."""
        if name is None:
            return None
        key = ec.norm(name)
        if self._teams_cache is None:
            self._teams_cache = ec.load_teams() if ec.TEAMS.exists() else []
        if self._teams_cache:
            row = ec.resolve_team(name, self._teams_cache)
            if row:
                key = ec.norm(row.get("fd") or row.get("name"))
        key = ALIASES.get(key, key)
        known = set(self.params.teams) if self.params else set()
        if self.df is not None:
            known |= set(self.df["home"]) | set(self.df["away"])
        if key in known:
            return key
        for k in sorted(known, key=len, reverse=True):
            if key.startswith(k + " ") or k.startswith(key + " "):
                return k
        if self._teams_cache and any(ec.norm(t.get("fd") or t.get("name")) == key for t in self._teams_cache):
            return key        # named in teams.json but no match yet: the promoted prior answers
        return None

    # ---- predictions
    def predict_three_way(self, home_key, away_key, as_of=None):
        """The three chances for two resolved keys, after the temperature. as_of only guards against asking the
        model about a match older than its fit (it has no older weights to answer with)."""
        if self.params is None:
            raise RuntimeError("no weights loaded")
        if as_of is not None and self.params.as_of:
            if _ts(as_of) < _ts(self.params.as_of) - pd.Timedelta(days=14):
                ec.log("edge_model: predict_three_way asked about a date before the fit; answering with current weights")
        return apply_temperature(three_way(self.params, home_key, away_key), self.params.temperature)

    def _frame(self):
        if self.df is None:
            try:
                import edge_backtest as bt
                codes = self._codes()
                self.df = bt.load_fd(codes) if codes else None
            except Exception:
                self.df = None
        return self.df

    def predict_fixture(self, home_name, away_name, kickoff_utc, lineups=None):
        """Chances plus the reasons, or None when a team name does not resolve.
        contributions: the home-minus-away differences that drove the number, each with a signed effect in
        points of the home-win chance (what that factor adds, the others held at neutral). The form rows
        (shots on target last 10, rest days, matches in 14 days) are context from edge_features: they are not a
        separate term in today's model (its decayed fit already leans on recent matches), so their effect is 0.
        ratings: 0 to 100 per team, see rating()."""
        home = self.resolve(home_name)
        away = self.resolve(away_name)
        if home is None or away is None or home == away:
            return None
        p = self.params
        ph, pd_, pa = self.predict_three_way(home, away, kickoff_utc)
        ah, dh = p.strength(home)
        aa, da = p.strength(away)
        base = {"mu": p.mu, "home": p.home, "rho": p.rho, "t": p.temperature}

        def p_home_with(ah_, dh_, aa_, da_, h_):
            lam = math.exp(p.mu + h_ + ah_ + da_)
            m = math.exp(p.mu + aa_ + dh_)
            g = apply_rho(poisson_grid(lam, m), lam, m, p.rho)
            return apply_temperature(grid_to_three(g), p.temperature)[0]

        full = p_home_with(ah, dh, aa, da, p.home)
        ma, md = (ah + aa) / 2.0, (dh + da) / 2.0
        contributions = [
            {"name": PLAIN["attack"], "key": "attack", "value": round(ah - aa, 3),
             "effect": round(100.0 * (full - p_home_with(ma, dh, ma, da, p.home)), 1)},
            {"name": PLAIN["defence"], "key": "defence", "value": round(da - dh, 3),
             "effect": round(100.0 * (full - p_home_with(ah, md, aa, md, p.home)), 1)},
            {"name": PLAIN["home_edge"], "key": "home_edge", "value": round(p.home, 3),
             "effect": round(100.0 * (full - p_home_with(ah, dh, aa, da, 0.0)), 1)},
        ]
        df = self._frame()
        if df is not None:
            try:
                import edge_features as ef
                mcfg = self.cfg.get("model", {})
                f = ef.build(df, home, away, kickoff_utc, n=int(mcfg.get("window_matches", 10)),
                             venue_weight=float(mcfg.get("venue_weight", 0.6)))
                for key, fk in (("sot_last10", "shots_on_target"), ("rest_days", "rest_days"),
                                ("matches_14d", "matches_14d")):
                    v = f.get(fk)
                    contributions.append({"name": PLAIN[key], "key": key, "value": None if v is None else round(v, 2),
                                          "effect": 0.0, "in_model": False})
            except Exception as e:
                ec.log("edge_model: features skipped:", str(e)[:120])
        return {
            "p_home": ph, "p_draw": pd_, "p_away": pa, "version": self.version,
            "contributions": contributions, "sources": list(self.sources),
            "ratings": {"home": rating(ah, dh), "away": rating(aa, da)},
            "expected_goals": {"home": round(rates(p, home, away)[0], 2), "away": round(rates(p, home, away)[1], 2)},
            "keys": {"home": home, "away": away}, "base": base,
        }


# ---------------------------------------------------------------- CLI

def main(argv):
    cmd = argv[0] if argv else "show"
    if cmd == "fit":
        svc = ModelService(fit_if_missing=False)
        v = svc.refresh(download=False)
        print("version", v, "teams", len(svc.params.teams), "home", round(svc.params.home, 3),
              "rho", round(svc.params.rho, 3), "conv", round(svc.params.conv, 3), "prior", svc.params.prior)
        return 0
    svc = ModelService()
    if cmd == "predict" and len(argv) >= 3:
        out = svc.predict_fixture(argv[1], argv[2], argv[3] if len(argv) > 3 else ec.iso(ec.now()))
        print(json.dumps(out, indent=1))
        return 0
    p = svc.params
    print(f"version {svc.version}  as_of {p.as_of}  rows {p.n_rows}  seasons {p.seasons}")
    print(f"mu {p.mu:.3f} (base {math.exp(p.mu):.2f} goals)  home {p.home:.3f}  rho {p.rho:.3f}  xi {p.xi}  "
          f"sot_blend {p.sot_blend}  conv {p.conv:.3f}  T {p.temperature:.3f}  prior {tuple(round(v, 3) for v in p.prior)}")
    order = sorted(range(len(p.teams)), key=lambda i: -(p.attack[i] - p.defence[i]))
    for i in order:
        print(f"  {p.teams[i]:22} attack {p.attack[i]:+.3f}  defence {p.defence[i]:+.3f}  rating {rating(p.attack[i], p.defence[i]):3}  ({p.centres.get(p.teams[i], '')})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
