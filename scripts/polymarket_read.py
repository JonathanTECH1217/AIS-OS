"""Polymarket, read-only: the second witness on every Premier League match price (Monarc Edge, 2026-10-04).

No account, no key, nothing is ever sent. Gamma (gamma-api.polymarket.com) lists the match events under the tag
epl: one event a match, slug like epl-cry-not-2026-10-11, title "Crystal Palace FC vs. Nottingham Forest FC",
three moneyline markets whose slugs end in the home code, -draw, and the away code. Each market is a Yes/No
market with its own CLOB token; the CLOB (clob.polymarket.com) gives the midpoint per token. The agent shows the
Polymarket mid beside the Kalshi price and flags a disagreement over config polymarket.disagree_points. It never
trades here.

Listings are cached 5 minutes and midpoints 2 minutes under projects/edge/data/cache/polymarket/. Any network
error answers None or an empty list and leaves the reason in LAST_ERROR so the server can show it. Polymarket
blocks some US states; if Gamma or the CLOB refuses from this machine the agent runs with no witness.

Gamma's start_date_min filters on the day the event was listed, not the kickoff, so the listing asks by
end_date_min and end_date_max instead (a match event's endDate is its kickoff) and then keeps only the events
whose gameStartTime falls in the window.

  python scripts/polymarket_read.py check
  python scripts/polymarket_read.py list
  python scripts/polymarket_read.py match "Arsenal" "Chelsea" 2026-10-18T15:30:00Z
Guide: the Polymarket section at the end of references/kalshi-api.md.
"""
import argparse
import json
import re
import sys
import time
from datetime import timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edge_common  # noqa: E402
from edge_common import OUTCOMES, iso, now, parse_iso, read_json, resolve_team, write_json_atomic  # noqa: E402

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
UA = "MonarcEdge/1.0 (+polymarket_read.py, read only)"
TIMEOUT = (5, 25)
LIST_TTL_S = 300
MID_TTL_S = 120
PAGE = 100
MAX_PAGES = 5
LAST_ERROR = None
_SLUG = re.compile(r"^epl-([a-z0-9]{2,5})-([a-z0-9]{2,5})-(\d{4}-\d{2}-\d{2})$")
_session = None


def _s():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers["User-Agent"] = UA
    return _session


def _f(v):
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _jl(v):
    """Gamma stores some lists as JSON strings ('["Yes","No"]')."""
    if isinstance(v, list):
        return v
    try:
        out = json.loads(v) if v else []
    except (TypeError, ValueError):
        return []
    return out if isinstance(out, list) else []


# ---------------------------------------------------------------- cache and transport

def _cache_path(name):
    d = Path(edge_common.CACHE) / "polymarket"
    d.mkdir(parents=True, exist_ok=True)
    return d / name


def _cache_read(name, ttl_s):
    obj = read_json(_cache_path(name))
    if obj and time.time() - float(obj.get("t") or 0) < ttl_s:
        return obj.get("body")
    return None


def _cache_write(name, body):
    write_json_atomic(_cache_path(name), {"t": time.time(), "body": body})


def _fail(msg):
    global LAST_ERROR
    LAST_ERROR = msg
    return None


def _get(url, params=None, timeout=TIMEOUT):
    """GET and parse. None on any trouble, with the reason in LAST_ERROR. 403 and 451 read as a geoblock."""
    host = url.split("/")[2]
    try:
        r = _s().get(url, params=params, timeout=timeout)
    except requests.RequestException as e:
        return _fail(f"{type(e).__name__} reaching {host}")
    if r.status_code in (403, 451):
        return _fail(f"HTTP {r.status_code} from {host}: Polymarket may be blocked where this machine sits")
    if r.status_code >= 400:
        return _fail(f"HTTP {r.status_code} from {host}")
    try:
        return r.json()
    except ValueError:
        return _fail(f"{host} answered something that is not JSON")


def reachable(timeout=4):
    """One cheap Gamma call. False on a geoblock or no network (LAST_ERROR says which)."""
    global LAST_ERROR
    body = _get(GAMMA + "/events", {"limit": 1}, timeout=(timeout, timeout))
    if body is None:
        return False
    LAST_ERROR = None
    return True


# ---------------------------------------------------------------- parsing (pure, used by the tests)

def _kickoff(m, e):
    """gameStartTime ('2026-10-17 11:30:00+00') first, then the event's startTime, then its endDate. ISO Z or None."""
    for v in (m.get("gameStartTime"), e.get("startTime"), e.get("endDate")):
        if not v:
            continue
        s = str(v).strip().replace(" ", "T")
        if re.search(r"[+-]\d{2}$", s):
            s += ":00"
        try:
            return iso(parse_iso(s))
        except ValueError:
            continue
    return None


def _market(m):
    outcomes = _jl(m.get("outcomes"))
    prices = _jl(m.get("outcomePrices"))
    tokens = _jl(m.get("clobTokenIds"))
    yes_i = outcomes.index("Yes") if "Yes" in outcomes else 0
    return {"slug": m.get("slug"), "question": m.get("question"),
            "token_yes": str(tokens[yes_i]) if len(tokens) > yes_i else None,
            "best_bid": _f(m.get("bestBid")), "best_ask": _f(m.get("bestAsk")),
            "yes_price": _f(prices[yes_i]) if len(prices) > yes_i else None,
            "last_price": _f(m.get("lastTradePrice")), "liquidity": _f(m.get("liquidity")), "volume": _f(m.get("volume")),
            "type": m.get("sportsMarketType"), "active": m.get("active"), "closed": m.get("closed")}


def parse_event(e):
    """One Gamma event to a match, or None when it is not a match event (futures, props)."""
    slug = e.get("slug") or ""
    mt = _SLUG.match(slug)
    if not mt:
        return None
    home_code, away_code, _day = mt.groups()
    title = e.get("title") or ""
    sep = " vs. " if " vs. " in title else (" vs " if " vs " in title else None)
    if not sep:
        return None
    home_name, away_name = [p.strip() for p in title.split(sep, 1)]
    markets, kick = {}, None
    for m in e.get("markets") or []:
        ms = m.get("slug") or ""
        suffix = ms[len(slug) + 1:] if ms.startswith(slug + "-") else ms.rsplit("-", 1)[-1]
        if suffix == "draw":
            key = "draw"
        elif suffix == home_code:
            key = "home"
        elif suffix == away_code:
            key = "away"
        else:
            continue
        markets[key] = _market(m)
        kick = kick or _kickoff(m, e)
    if "home" not in markets or "away" not in markets:
        return None
    return {"slug": slug, "title": title, "home_name": home_name, "away_name": away_name,
            "home_code": home_code, "away_code": away_code, "kickoff_utc": kick or _kickoff({}, e),
            "markets": markets}


def parse_events(raw):
    return [x for x in (parse_event(e) for e in raw or []) if x]


# ---------------------------------------------------------------- the three reads

def list_matches(days=16):
    """Every EPL match event kicking off from 3 hours ago to `days` ahead, soonest first. [] on trouble."""
    global LAST_ERROR
    name = f"list-{int(days)}.json"
    cached = _cache_read(name, LIST_TTL_S)
    if cached is not None:
        return cached
    t0 = now()
    lo, hi = t0 - timedelta(hours=3), t0 + timedelta(days=days)
    raw = []
    for page in range(MAX_PAGES):
        body = _get(GAMMA + "/events", {"tag_slug": "epl", "active": "true", "closed": "false", "limit": PAGE,
                                        "offset": page * PAGE, "end_date_min": iso(lo), "end_date_max": iso(hi)})
        if body is None:
            return [] if page == 0 else _finish(name, raw, lo, hi)
        if not isinstance(body, list):
            _fail("Gamma answered an unexpected shape")
            return []
        raw.extend(body)
        if len(body) < PAGE:
            break
    LAST_ERROR = None
    return _finish(name, raw, lo, hi)


def _finish(name, raw, lo, hi):
    out = []
    for m in parse_events(raw):
        k = m.get("kickoff_utc")
        if k and lo <= parse_iso(k) <= hi:
            out.append(m)
    out.sort(key=lambda m: m["kickoff_utc"] or "")
    _cache_write(name, out)
    return out


def find_match(home_name, away_name, kickoff_utc, matches=None, tolerance_s=600):
    """The match whose kickoff is within `tolerance_s` (10 minutes by default) and whose two names resolve to the
    same clubs through edge_common.resolve_team (names and aliases, never the slug codes). None when there is no
    such match. With no football feed the agent only knows the day, so it passes a 36-hour tolerance and takes
    this match's kickoff as the real one."""
    teams = edge_common.load_teams()
    th, ta = resolve_team(home_name, teams), resolve_team(away_name, teams)
    if th is None or ta is None or not kickoff_utc:
        return None
    want = parse_iso(kickoff_utc)
    for m in (matches if matches is not None else list_matches()):
        k = m.get("kickoff_utc")
        if not k or abs((parse_iso(k) - want).total_seconds()) > tolerance_s:
            continue
        if resolve_team(m.get("home_name"), teams) is th and resolve_team(m.get("away_name"), teams) is ta:
            return m
    return None


def _midpoint(token):
    name = f"mid-{token}.json"
    cached = _cache_read(name, MID_TTL_S)
    if cached is not None:
        return cached
    body = _get(CLOB + "/midpoint", {"token_id": token})
    mid = _f(body.get("mid")) if isinstance(body, dict) else None
    if mid is not None:
        _cache_write(name, mid)
    return mid


def mids(match):
    """The Yes mid for home, draw, away: the CLOB midpoint per market, else Gamma's (bestBid + bestAsk) / 2,
    else Gamma's outcome price. source is "clob" only when all three came from the CLOB."""
    out = {"home": None, "draw": None, "away": None, "source": "clob"}
    all_clob = True
    for key in OUTCOMES:
        m = (match or {}).get("markets", {}).get(key)
        if not m:
            all_clob = False
            continue
        mid = _midpoint(m["token_yes"]) if m.get("token_yes") else None
        if mid is None:
            all_clob = False
            if m.get("best_bid") is not None and m.get("best_ask") is not None:
                mid = round((m["best_bid"] + m["best_ask"]) / 2.0, 4)
            elif m.get("yes_price") is not None:
                mid = m["yes_price"]
        out[key] = mid
    out["source"] = "clob" if all_clob else "gamma"
    return out


# ---------------------------------------------------------------- CLI

def _p(v):
    return "-" if v is None else f"{v:.3f}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("check", help="can we reach Gamma and the CLOB from here")
    p = sub.add_parser("list", help="the EPL match events in the window"); p.add_argument("--days", type=int, default=16)
    p = sub.add_parser("match", help="find one match by names and kickoff, print its mids")
    p.add_argument("home"); p.add_argument("away"); p.add_argument("kickoff_utc")
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return
    if a.cmd == "check":
        ok = reachable()
        print(f"Gamma: {'reachable' if ok else 'NOT reachable'}" + (f" ({LAST_ERROR})" if LAST_ERROR else ""))
        if ok:
            ms = list_matches()
            print(f"match events in the next 16 days: {len(ms)}" + (f" ({LAST_ERROR})" if LAST_ERROR else ""))
            if ms:
                mid = mids(ms[0])
                print(f"CLOB: {'answers' if mid['source'] == 'clob' else 'no answer, Gamma mids used'}"
                      + (f" ({LAST_ERROR})" if LAST_ERROR else ""))
        return
    if a.cmd == "list":
        ms = list_matches(a.days)
        print(f"{len(ms)} EPL match events" + (f"   ({LAST_ERROR})" if LAST_ERROR else ""))
        for m in ms:
            mk = m["markets"]
            print(f"  {m['kickoff_utc']}  {m['slug']:<26} {m['title']}")
            print("      " + "  ".join(f"{k} {_p(mk.get(k, {}).get('best_bid'))}/{_p(mk.get(k, {}).get('best_ask'))}" for k in OUTCOMES)
                  + f"   liq {int(sum((mk.get(k) or {}).get('liquidity') or 0 for k in OUTCOMES)):,}")
        return
    m = find_match(a.home, a.away, a.kickoff_utc)
    if not m:
        sys.exit(f"no Polymarket match for {a.home} v {a.away} at {a.kickoff_utc}" + (f" ({LAST_ERROR})" if LAST_ERROR else ""))
    print(f"{m['slug']}  {m['title']}  {m['kickoff_utc']}")
    mid = mids(m)
    print(f"  mids ({mid['source']}): home {_p(mid['home'])}  draw {_p(mid['draw'])}  away {_p(mid['away'])}")


if __name__ == "__main__":
    main()
