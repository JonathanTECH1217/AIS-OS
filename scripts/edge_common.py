"""Shared helpers for Monarc Edge (2026-10-04): the Kalshi Premier League betting agent.

Paths, the config with its defaults, a clock the tests can freeze, the money math (Kalshi fee, gap and side,
stake line, contracts), bands, the busy-market check, de-vig, Wilson intervals, the SQLite schema, and team-name
resolution. Every number Jonathan set in the interview lives in projects/edge/config.json; the defaults here are
the same numbers so a missing key never changes a bet.

Folders (projects/edge/data is git-ignored except its README):
  projects/edge/data/edge.sqlite   fixtures, features, model runs, market snapshots, cards, orders, fills,
                                   settlements, the ledger, halts, backtests
  projects/edge/data/cache/        raw API responses (football, polymarket, kalshi)
  projects/edge/data/fd/           football-data.co.uk season CSVs
  projects/edge/model/             fitted weights, one JSON per version
  projects/edge/backtest/          dated reports

EDGE_DATA overrides the data folder, EDGE_CONFIG the config file, EDGE_CLOCK freezes the clock (ISO 8601 UTC),
EDGE_TEST=1 turns on the test-only routes. Same pattern as STUDIO_MEDIA / STUDIO_CONFIG.
"""
import json
import math
import os
import re
import sqlite3
import sys
import threading
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from studio_common import read_json, write_json_atomic  # noqa: E402  (atomic JSON writes, shared with Studio)
from outreach_common import get_secret, load_env  # noqa: E402  (keys from ~/.monarc/secrets.env, never values in logs)

APP = "Monarc Edge"
PORT = 8800
TEST_PORT = 8801
EDGE_DIR = ROOT / "projects" / "edge"
DATA = Path(os.environ.get("EDGE_DATA") or (EDGE_DIR / "data")).resolve()
CONFIG = Path(os.environ.get("EDGE_CONFIG") or (EDGE_DIR / "config.json"))
TEAMS = EDGE_DIR / "teams.json"
MODEL_DIR = EDGE_DIR / "model"
BACKTEST_DIR = EDGE_DIR / "backtest"
CACHE = DATA / "cache"
FD_DIR = DATA / "fd"
DB_PATH = DATA / "edge.sqlite"
DRY_RUN_LOG = DATA / "dry-run.jsonl"
HOME = Path.home() / ".monarc"          # not AppData: the Store Python hides writes there
TEST_MODE = os.environ.get("EDGE_TEST") == "1"

KEY_NAMES = {
    "kalshi_demo": ("KALSHI_DEMO_API_KEY_ID", "KALSHI_DEMO_PRIVATE_KEY_PATH"),
    "kalshi": ("KALSHI_API_KEY_ID", "KALSHI_PRIVATE_KEY_PATH"),
    "football": ("API_FOOTBALL_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY",),
}

# ---------------------------------------------------------------- config

DEFAULTS = {
    "env": "demo",                 # demo | prod. prod with dry_run false needs rehearsal_passed.
    "dry_run": True,               # orders are written to data/dry-run.jsonl instead of sent
    "paper_auto": True,            # while dry_run is on, every ready card is paper-filled at the ask by itself
    "rehearsal_passed": False,     # flipped by hand after the seven-line checklist in the README
    "mode": "approve",             # approve | auto. auto is refused until gate().passed.
    "port": PORT,
    "league_id": 39,
    "season": 2026,
    "kalshi_series": "KXEPLGAME",
    "gap_floor_points": 7.0,
    "big_gap_points": 10.0,        # a gap this big on a major league is a warning: yellow, "the model may be wrong"
    "stake": {"floor_pct": 6.0, "cap_pct": 8.0, "cap_from_points": 17.0},
    "fees": {"taker_rate": 0.07, "maker_rate": 0.0175, "assume_taker": True, "schedule_checked": ""},
    "busy": {"min_volume_contracts": 10000, "max_spread_cents": 2, "min_depth_multiple": 1.0},
    "bankroll_usd": 1000.0,
    "drawdown": {"on": True, "auto_only": True, "pct": 25.0},
    "window": {"snapshot_minutes": 60, "lineup_from_minutes": 75, "lineup_poll_minutes": 5,
               "decide_by_minutes": 20, "decide_without_lineups": False, "cancel_before_kickoff_minutes": 2,
               "listing_lookahead_days": 16},
    "auto_windows": {"lineup_hour": True, "clv_proven_bands": True, "min_band_cards": 30},
    "gate": {"min_settled": 200, "band_width_points": 10, "band_tolerance_points": 5.0, "min_band_n": 30,
             "pooled_tolerance_points": 3.0, "min_clv_points": 5.0},
    "model": {"version": "", "window_matches": 10, "venue_weight": 0.6, "sot_blend": 0.5},
    "polymarket": {"on": True, "disagree_points": 5.0, "block_when_disagree": False},
    "claude": {"on": True, "max_usd_per_day": 1.0, "model": ""},
    "api_football": {"daily_budget": 6000, "odds_witness": False,
                     "cache_hours": {"fixtures": 6, "team_stats": 24, "players": 24, "h2h": 168, "injuries": 6,
                                     "odds": 3, "lineups_pending": 0}},
    "legal_watch": {"note": "Maryland v. Kalshi, 4th Cir., argued 2026-05-07, enforcement paused pending ruling",
                    "checked": "2026-10-04"},
}

_cfg_lock = threading.Lock()


def deep_merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config():
    """Defaults under the file: a key missing from config.json never changes a bet."""
    with _cfg_lock:
        return deep_merge(DEFAULTS, read_json(CONFIG, {}) or {})


def save_config(cfg):
    with _cfg_lock:
        data = {k: v for k, v in cfg.items()}
        write_json_atomic(CONFIG, data, indent=1)


# ---------------------------------------------------------------- clock

_clock = {"fixed": None}


def set_clock(iso_or_none):
    """Freeze or release the clock (tests). EDGE_CLOCK in the environment freezes it at start."""
    _clock["fixed"] = parse_iso(iso_or_none) if iso_or_none else None


def now():
    if _clock["fixed"]:
        return _clock["fixed"]
    env = os.environ.get("EDGE_CLOCK")
    if env:
        return parse_iso(env)
    return datetime.now(timezone.utc)


def iso(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_iso(s):
    if s is None or s == "":
        return None
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    s = str(s).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def hours_until(kickoff, at=None):
    at = at or now()
    return (parse_iso(kickoff) - at).total_seconds() / 3600.0


# ---------------------------------------------------------------- money math

def fee_points_per_contract(price, rate=0.07):
    """Kalshi's taker fee for one contract at `price` (0..1), in points of a dollar. Worst at 50 cents (1.75)."""
    return 100.0 * rate * price * (1.0 - price)


def kalshi_fee_usd(count, price, rate=0.07):
    """Fee for a fill of `count` contracts at `price`, rounded UP to the cent (Kalshi's rule). 100 at 0.55 = 1.74."""
    raw = rate * count * price * (1.0 - price)
    return math.ceil(raw * 100 - 1e-9) / 100.0


def gap_and_side(p, yes_ask, no_ask, rate=0.07):
    """Our chance `p` that the outcome happens, against the price to BUY each side. Always the ask, never the mid.
    Returns gap_yes, gap_no (points, after the taker fee), the better side, its gap and its price."""
    gy = 100.0 * (p - yes_ask) - fee_points_per_contract(yes_ask, rate)
    gn = 100.0 * ((1.0 - p) - no_ask) - fee_points_per_contract(no_ask, rate)
    if gy >= gn:
        side, gap, price = "yes", gy, yes_ask
    else:
        side, gap, price = "no", gn, no_ask
    return {"gap_yes": gy, "gap_no": gn, "side": side, "gap": gap, "price": price,
            "break_even": price + fee_points_per_contract(price, rate) / 100.0}


def color_of(gap, floor_points, big_gap_points=None):
    """green at the floor or above, red below zero, amber between (shown, no trade). yellow when the gap is at or
    past big_gap_points: on a heavily traded league a gap that big usually means the model missed something, so it is
    a warning to check the news, never a bigger bet (review of the first card, 2026-10-04). Paper mode still logs it;
    live auto mode never takes it."""
    if big_gap_points and gap >= float(big_gap_points):
        return "yellow"
    if gap >= floor_points:
        return "green"
    if gap < 0:
        return "red"
    return "amber"


def stake_pct_for_gap(gap, cfg):
    """Jonathan's line (Q6 shape, Q17 amounts): 6% of the bankroll at the 7-point floor, a straight line to 8% at
    17 points or more. Zero under the floor."""
    g0 = float(cfg["gap_floor_points"])
    st = cfg["stake"]
    if gap < g0:
        return 0.0
    span = max(1e-9, float(st["cap_from_points"]) - g0)
    t = min(1.0, max(0.0, (gap - g0) / span))
    return float(st["floor_pct"]) + (float(st["cap_pct"]) - float(st["floor_pct"])) * t


def stake_for_gap(gap, bankroll_usd, cfg):
    pct = stake_pct_for_gap(gap, cfg)
    return round(bankroll_usd * pct / 100.0, 2) if pct > 0 else 0.0


def contracts_for(stake_usd, price):
    """Whole contracts the stake buys at `price`; never 0 once there is a stake."""
    if stake_usd <= 0 or price <= 0:
        return 0
    return max(1, int(math.floor(stake_usd / price + 1e-9)))


def order_cost_usd(count, price, rate=0.07):
    return round(count * price + kalshi_fee_usd(count, price, rate), 2)


# ---------------------------------------------------------------- bands

def band_of(p_pct, width=10):
    """'30-40' for 34.2; the top band is '90-100'."""
    width = int(width)
    lo = int(math.floor(p_pct / width)) * width
    lo = min(max(lo, 0), 100 - width)
    return f"{lo}-{lo + width}"


HOURS_BANDS = ((1, "0-1h"), (3, "1-3h"), (12, "3-12h"), (24, "12-24h"), (72, "1-3d"), (float("inf"), "3d+"))


def hours_band(hours):
    """Hours before kickoff, binned, so the record can say which hour the market is least sharp."""
    h = max(0.0, float(hours))
    for top, label in HOURS_BANDS:
        if h < top:
            return label
    return HOURS_BANDS[-1][1]


# ---------------------------------------------------------------- busy market

def busy_check(snap, count, side, cfg_busy):
    """(ok, reason). snap: volume, yes_bid, yes_ask, yes_ask_size, yes_bid_size (dollars 0..1, contracts).
    A No buy fills against the Yes bidders, so its depth is the yes bid size."""
    vol = float(snap.get("volume") or 0)
    if vol < float(cfg_busy["min_volume_contracts"]):
        return False, f"only {int(vol):,} contracts traded (floor {int(cfg_busy['min_volume_contracts']):,})"
    yb, ya = snap.get("yes_bid"), snap.get("yes_ask")
    if yb is None or ya is None:
        return False, "no two-sided book"
    spread_c = round((float(ya) - float(yb)) * 100)
    if spread_c > int(cfg_busy["max_spread_cents"]):
        return False, f"spread {spread_c} cents (max {int(cfg_busy['max_spread_cents'])})"
    depth = float(snap.get("yes_ask_size" if side == "yes" else "yes_bid_size") or 0)
    need = count * float(cfg_busy.get("min_depth_multiple", 1.0))
    if count and depth < need:
        return False, f"only {int(depth)} contracts at the touch (need {int(math.ceil(need))})"
    return True, ""


# ---------------------------------------------------------------- odds helpers

def devig_proportional(odds):
    """Decimal odds -> fair chances that sum to 1, each implied chance divided by their sum."""
    imp = [1.0 / o for o in odds]
    s = sum(imp)
    return [x / s for x in imp]


def devig_power(odds, tol=1e-10):
    """Power method: raise each implied chance to k and solve for k so they sum to 1. Gives the longshot a
    smaller share than the proportional method, which is where books pad most."""
    imp = [1.0 / o for o in odds]
    lo, hi = 0.5, 3.0
    for _ in range(200):
        k = (lo + hi) / 2
        s = sum(x ** k for x in imp)
        if abs(s - 1.0) < tol:
            break
        if s > 1.0:
            lo = k
        else:
            hi = k
    k = (lo + hi) / 2
    out = [x ** k for x in imp]
    s = sum(out)
    return [x / s for x in out]


def wilson(k, n, z=1.96):
    """Wilson score interval for k hits in n, as (lo, hi) in 0..1. (0, 1) when n is 0."""
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d


# ---------------------------------------------------------------- card states

CARD_STATES = ("watching", "ready", "no_edge", "approved", "placed", "filled", "partial", "unfilled", "passed",
               "expired", "delisted", "halted", "settled", "error")
OPEN_STATES = ("watching", "ready", "no_edge")          # still being re-priced
LIVE_ORDER_STATES = ("approved", "placed", "partial")   # money may be committed
POSITION_STATES = ("filled", "partial")                 # holding contracts until settlement
OUTCOMES = ("home", "draw", "away")

# ---------------------------------------------------------------- database

SCHEMA = """
CREATE TABLE IF NOT EXISTS fixtures (
  id INTEGER PRIMARY KEY, season INTEGER, round TEXT, kickoff_utc TEXT, home_id INTEGER, home TEXT,
  away_id INTEGER, away TEXT, status TEXT, home_goals INTEGER, away_goals INTEGER, result TEXT,
  kalshi_event TEXT, poly_slug TEXT, linked INTEGER DEFAULT 0, updated TEXT);
CREATE TABLE IF NOT EXISTS features (
  id INTEGER PRIMARY KEY AUTOINCREMENT, fixture_id INTEGER, as_of TEXT, kind TEXT, json TEXT);
CREATE TABLE IF NOT EXISTS model_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, fixture_id INTEGER, feature_id INTEGER, as_of TEXT, model_version TEXT,
  p_home REAL, p_draw REAL, p_away REAL, contrib_json TEXT);
CREATE TABLE IF NOT EXISTS snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT, fixture_id INTEGER, ticker TEXT, outcome TEXT, as_of TEXT,
  yes_bid REAL, yes_ask REAL, no_bid REAL, no_ask REAL, yes_ask_size REAL, yes_bid_size REAL,
  volume REAL, oi REAL, status TEXT, poly_mid REAL, poly_bid REAL, poly_ask REAL);
CREATE INDEX IF NOT EXISTS snapshots_ticker ON snapshots (ticker, as_of);
CREATE TABLE IF NOT EXISTS cards (
  id TEXT PRIMARY KEY, fixture_id INTEGER, event_ticker TEXT, ticker TEXT, outcome TEXT, side TEXT,
  created TEXT, decided_at TEXT, expires_at TEXT, model_version TEXT, model_p REAL,
  p_home REAL, p_draw REAL, p_away REAL,
  market_yes_bid REAL, market_yes_ask REAL, market_price REAL, market_mid REAL, poly_mid REAL,
  fee_points REAL, break_even REAL, gap_points REAL, color TEXT, stake_usd REAL, count INTEGER, limit_price REAL,
  band TEXT, hours_band TEXT, mode TEXT, state TEXT, approved_at TEXT, passed_at TEXT,
  order_id TEXT, client_order_id TEXT, fill_count INTEGER DEFAULT 0, avg_fill REAL, fees_paid REAL DEFAULT 0,
  result TEXT, pnl_usd REAL, clv_points REAL, closing_fair REAL, reasoning TEXT, flags_json TEXT DEFAULT '[]',
  lineups_seen INTEGER DEFAULT 0, busy_ok INTEGER DEFAULT 0, busy_reason TEXT, sources_json TEXT DEFAULT '[]',
  paper INTEGER DEFAULT 0, updated TEXT);
CREATE INDEX IF NOT EXISTS cards_fixture ON cards (fixture_id);
CREATE INDEX IF NOT EXISTS cards_state ON cards (state);
CREATE TABLE IF NOT EXISTS orders (
  order_id TEXT PRIMARY KEY, card_id TEXT, client_order_id TEXT, ticker TEXT, side TEXT, price REAL,
  count INTEGER, tif TEXT, expires_at TEXT, status TEXT, created TEXT, updated TEXT, raw_json TEXT);
CREATE TABLE IF NOT EXISTS fills (
  id TEXT PRIMARY KEY, order_id TEXT, card_id TEXT, ticker TEXT, count INTEGER, yes_price REAL,
  is_taker INTEGER, fee_usd REAL, created TEXT);
CREATE TABLE IF NOT EXISTS settlements (
  ticker TEXT PRIMARY KEY, card_id TEXT, market_result TEXT, yes_count INTEGER, no_count INTEGER,
  revenue_usd REAL, fee_usd REAL, settled_time TEXT, raw_json TEXT);
CREATE TABLE IF NOT EXISTS ledger (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, kind TEXT, card_id TEXT, amount_usd REAL,
  balance_after REAL, note TEXT);
CREATE TABLE IF NOT EXISTS halts (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, reason TEXT, detail TEXT, cleared_at TEXT);
CREATE TABLE IF NOT EXISTS backtests (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, params_json TEXT, metrics_json TEXT, path TEXT);
CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT);
"""

_db_local = threading.local()
_db_init = {"done": set()}


def ensure_dirs():
    for d in (DATA, CACHE, FD_DIR, MODEL_DIR, BACKTEST_DIR, HOME):
        d.mkdir(parents=True, exist_ok=True)


def db(path=None):
    """One SQLite connection per thread, WAL mode, rows as sqlite3.Row. The schema is applied once per path."""
    path = Path(path or DB_PATH)
    conn = getattr(_db_local, "conn", None)
    if conn is not None and getattr(_db_local, "path", None) == str(path):
        return conn
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    if str(path) not in _db_init["done"]:
        conn.executescript(SCHEMA)
        conn.commit()
        _db_init["done"].add(str(path))
    _db_local.conn = conn
    _db_local.path = str(path)
    return conn


def rows(cur):
    return [dict(r) for r in cur.fetchall()]


def kv_get(key, default=None):
    r = db().execute("SELECT v FROM kv WHERE k=?", (key,)).fetchone()
    return json.loads(r["v"]) if r else default


def kv_set(key, value):
    c = db()
    c.execute("INSERT INTO kv (k, v) VALUES (?, ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (key, json.dumps(value)))
    c.commit()


# ---------------------------------------------------------------- teams

_STRIP = re.compile(r"\b(fc|afc|cf|the)\b|[^a-z0-9 ]")


def norm(name):
    """'Nott'm Forest' -> 'nottm forest', 'Brighton & Hove Albion FC' -> 'brighton hove albion'."""
    s = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", " ").replace("'", "")
    s = _STRIP.sub(" ", s)
    return " ".join(s.split())


def load_teams():
    return read_json(TEAMS, {}).get("teams", [])


def save_teams(teams, note=None):
    data = read_json(TEAMS, {})
    data["teams"] = teams
    if note:
        data["_about"] = note
    write_json_atomic(TEAMS, data, indent=1)


def resolve_team(name, teams=None):
    """The team row whose name, football-data name, Kalshi code, Polymarket code or alias matches. None if not."""
    if name is None:
        return None
    teams = teams if teams is not None else load_teams()
    key = norm(name)
    code = str(name).strip().lower()
    for t in teams:
        if key and key == norm(t.get("name")):
            return t
        if key and key == norm(t.get("fd")):
            return t
        if code and code in (str(t.get("kalshi") or "").lower(), str(t.get("poly") or "").lower()):
            return t
        if key and any(key == norm(a) for a in t.get("aliases", [])):
            return t
    return None


def team_by_api_id(api_id, teams=None):
    for t in (teams if teams is not None else load_teams()):
        if t.get("api_id") == api_id:
            return t
    return None


# ---------------------------------------------------------------- misc

def log(*parts):
    print(time.strftime("%H:%M:%S"), *parts, flush=True)


def key_sources():
    """Which keys resolve and where from (source labels only, never values)."""
    _, src = load_env()
    out = {}
    for label, names in KEY_NAMES.items():
        out[label] = {n: src.get(n) for n in names}
    # Jonathan saved the production key id as KALSHI_API_KEY (2026-10-04) and the PEM sits at ~/.monarc/kalshi.pem;
    # kalshi_api.py reads both, so report them under the names the rest of the system expects.
    k = out["kalshi"]
    if not k.get("KALSHI_API_KEY_ID") and src.get("KALSHI_API_KEY"):
        k["KALSHI_API_KEY_ID"] = f"{src['KALSHI_API_KEY']} (as KALSHI_API_KEY)"
    if not k.get("KALSHI_PRIVATE_KEY_PATH"):
        for name in ("kalshi-prod.pem", "kalshi.pem"):
            if (HOME / name).exists():
                k["KALSHI_PRIVATE_KEY_PATH"] = f"default ~/.monarc/{name}"
                break
    d = out["kalshi_demo"]
    if not d.get("KALSHI_DEMO_PRIVATE_KEY_PATH") and (HOME / "kalshi-demo.pem").exists():
        d["KALSHI_DEMO_PRIVATE_KEY_PATH"] = "default ~/.monarc/kalshi-demo.pem"
    return out


def json_dumps(obj):
    return json.dumps(obj, ensure_ascii=False, default=str)
