"""API-Football: fixtures, lineups, match statistics, injuries, players, and bookmaker odds (Monarc Edge, 2026-10-04).

The facts the model is built from. Base https://v3.football.api-sports.io, header x-apisports-key, key
API_FOOTBALL_KEY in ~/.monarc/secrets.env (references/credentials.md). Premier League is league 39; season 2026
means 2026-27. Pro plan: 7,500 calls a day, 300 a minute. The day quota comes back in the header
x-ratelimit-requests-remaining and the minute quota in X-RateLimit-Remaining.

Every answer is kept on disk under projects/edge/data/cache/football/<sha1>.json as {"t", "path", "params",
"body"}. A cache hit costs nothing. Live calls count against a daily budget (config api_football.daily_budget,
6,000 of the 7,500) kept in projects/edge/data/football-budget.json; past it the client raises FootballBudget
instead of spending the rest. Without a key every live call raises FootballError, but cached data still serves.

Timing: lineups post 20 to 40 minutes before kickoff (the agent polls from 75 minutes out, every 5), statistics
fill during the match and stay, odds are kept 7 days only. The shapes here follow the public v3 docs; the docs
site refused automated reads on 2026-10-04, so the first live read with a key should be checked against
references/api-football.md.

  python scripts/api_football.py check
  python scripts/api_football.py fixtures --from 2026-10-10 --to 2026-10-12
  python scripts/api_football.py lineups FIXTURE
  python scripts/api_football.py stats FIXTURE
  python scripts/api_football.py teams
"""
import argparse
import hashlib
import json
import sys
import time
from datetime import timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edge_common  # noqa: E402
from edge_common import get_secret, iso, now, parse_iso, read_json, write_json_atomic  # noqa: E402
from outreach_common import report_key_sources  # noqa: E402

BASE = "https://v3.football.api-sports.io"
KEY_NAME = "API_FOOTBALL_KEY"
TIMEOUT = (5, 30)
FLOOR_S = 0.25
FOREVER = None
STAT_NAMES = {
    "Shots on Goal": "shots_on_target", "Shots off Goal": "shots_off_target", "Total Shots": "shots",
    "Blocked Shots": "shots_blocked", "Shots insidebox": "shots_inside_box", "Shots outsidebox": "shots_outside_box",
    "Fouls": "fouls", "Corner Kicks": "corners", "Offsides": "offsides", "Ball Possession": "possession",
    "Yellow Cards": "yellow", "Red Cards": "red", "Goalkeeper Saves": "saves", "Total passes": "passes",
    "Passes accurate": "passes_accurate", "Passes %": "pass_pct", "expected_goals": "xg",
    "goals_prevented": "goals_prevented",
}
FLOAT_STATS = {"possession", "pass_pct", "xg", "goals_prevented"}


class FootballError(Exception):
    pass


class FootballBudget(FootballError):
    """The day's budget is spent. Cached data still serves."""


# ---------------------------------------------------------------- parsers (pure, used by the tests)

def _num(v):
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().rstrip("%")
    try:
        return float(s)
    except ValueError:
        return None


def _int(v):
    n = _num(v)
    return None if n is None else int(round(n))


def normalize_fixture(x):
    fx, lg, tm, gl = x.get("fixture") or {}, x.get("league") or {}, x.get("teams") or {}, x.get("goals") or {}
    home, away = tm.get("home") or {}, tm.get("away") or {}
    date = fx.get("date")
    try:
        kick = iso(parse_iso(date)) if date else None
    except ValueError:
        kick = None
    return {"id": fx.get("id"), "kickoff_utc": kick, "status": (fx.get("status") or {}).get("short"),
            "elapsed": (fx.get("status") or {}).get("elapsed"), "round": lg.get("round"), "season": lg.get("season"),
            "home_id": home.get("id"), "home": home.get("name"), "away_id": away.get("id"), "away": away.get("name"),
            "home_goals": gl.get("home"), "away_goals": gl.get("away"), "venue": (fx.get("venue") or {}).get("name")}


def parse_stats(body):
    """{team_id: {shots, shots_on_target, possession (0..100 float), corners, fouls, yellow, red, saves, passes,
    passes_accurate, xg (float|None), ...}}. A null count reads as 0; a null float stays None."""
    out = {}
    for item in body.get("response") or []:
        tid = (item.get("team") or {}).get("id")
        if tid is None:
            continue
        row = {"team": (item.get("team") or {}).get("name")}
        for st in item.get("statistics") or []:
            key = STAT_NAMES.get(st.get("type"))
            if not key:
                continue
            if key in FLOAT_STATS:
                row[key] = _num(st.get("value"))
            else:
                row[key] = _int(st.get("value")) or 0
        out[tid] = row
    return out


def parse_players(body):
    out = {}
    for item in body.get("response") or []:
        tid = (item.get("team") or {}).get("id")
        rows = []
        for p in item.get("players") or []:
            pl, st = p.get("player") or {}, (p.get("statistics") or [{}])[0]
            g, tk, dr, du, sh, go, pa, fo, ca = (st.get(k) or {} for k in
                                                 ("games", "tackles", "dribbles", "duels", "shots", "goals", "passes", "fouls", "cards"))
            rows.append({"id": pl.get("id"), "name": pl.get("name"), "minutes": _int(g.get("minutes")) or 0,
                         "rating": _num(g.get("rating")), "position": g.get("position"), "number": g.get("number"),
                         "substitute": bool(g.get("substitute")),
                         "tackles": _int(tk.get("total")) or 0, "interceptions": _int(tk.get("interceptions")) or 0,
                         "blocks": _int(tk.get("blocks")) or 0,
                         "dribbles_attempts": _int(dr.get("attempts")) or 0, "dribbles_success": _int(dr.get("success")) or 0,
                         "duels_total": _int(du.get("total")) or 0, "duels_won": _int(du.get("won")) or 0,
                         "shots": _int(sh.get("total")) or 0, "shots_on": _int(sh.get("on")) or 0,
                         "goals": _int(go.get("total")) or 0, "assists": _int(go.get("assists")) or 0,
                         "passes": _int(pa.get("total")) or 0, "key_passes": _int(pa.get("key")) or 0,
                         "fouls_committed": _int(fo.get("committed")) or 0, "fouls_drawn": _int(fo.get("drawn")) or 0,
                         "yellow": _int(ca.get("yellow")) or 0, "red": _int(ca.get("red")) or 0})
        if tid is not None:
            out[tid] = rows
    return out


def _lineup(t):
    def players(key):
        return [{"id": (p.get("player") or {}).get("id"), "name": (p.get("player") or {}).get("name"),
                 "pos": (p.get("player") or {}).get("pos"), "number": (p.get("player") or {}).get("number"),
                 "grid": (p.get("player") or {}).get("grid")} for p in t.get(key) or []]
    return {"team_id": (t.get("team") or {}).get("id"), "team": (t.get("team") or {}).get("name"),
            "formation": t.get("formation"), "coach": (t.get("coach") or {}).get("name"),
            "start_xi": players("startXI"), "subs": players("substitutes")}


def lineups_complete(body):
    items = body.get("response") or []
    return len(items) == 2 and all(len(t.get("startXI") or []) == 11 for t in items)


# ---------------------------------------------------------------- the client

class Football:
    def __init__(self, key=None, cache=None, budget=None, session=None, budget_file=None):
        self.key = key if key is not None else get_secret(KEY_NAME)
        self.cache_dir = Path(cache) if cache else Path(edge_common.CACHE) / "football"
        cfg = edge_common.load_config().get("api_football") or {}
        self.budget = int(budget if budget is not None else cfg.get("daily_budget", 6000))
        self.ttl = dict(cfg.get("cache_hours") or {})
        self.budget_file = Path(budget_file) if budget_file else Path(edge_common.DATA) / "football-budget.json"
        self.s = session or requests.Session()
        self.remaining = None
        self.minute_remaining = None
        self.calls = 0
        self._last_call = 0.0

    # ---- cache

    def _cache_file(self, path, params):
        key = path + "?" + "&".join(f"{k}={params[k]}" for k in sorted(params))
        return self.cache_dir / (hashlib.sha1(key.encode("utf-8")).hexdigest() + ".json")

    def _read_cache(self, path, params):
        obj = read_json(self._cache_file(path, params))
        if not obj or "body" not in obj:
            return None
        return obj["body"], time.time() - float(obj.get("t") or 0)

    def _write_cache(self, path, params, body):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        write_json_atomic(self._cache_file(path, params), {"t": time.time(), "path": path, "params": params, "body": body})

    def peek(self, path, **params):
        """The cached body whatever its age, or None."""
        params = {k: v for k, v in params.items() if v is not None}
        hit = self._read_cache(path, params)
        return hit[0] if hit else None

    # ---- budget

    def _today(self):
        return now().strftime("%Y-%m-%d")

    def budget_used(self):
        b = read_json(self.budget_file, {}) or {}
        return int(b.get("used") or 0) if b.get("day") == self._today() else 0

    def _budget_add(self, n=1):
        b = read_json(self.budget_file, {}) or {}
        used = int(b.get("used") or 0) if b.get("day") == self._today() else 0
        write_json_atomic(self.budget_file, {"day": self._today(), "used": used + n})

    def _read_quota(self, headers):
        day = headers.get("x-ratelimit-requests-remaining")
        minute = headers.get("X-RateLimit-Remaining")
        if day is not None and str(day).isdigit():
            self.remaining = int(day)
        if minute is not None and str(minute).isdigit():
            self.minute_remaining = int(minute)

    # ---- transport

    def get(self, path, ttl_hours, **params):
        """The raw body. A cache entry younger than ttl_hours serves (None means for good, 0 means never);
        otherwise one live call, counted against the day's budget."""
        params = {k: v for k, v in params.items() if v is not None}
        hit = self._read_cache(path, params)
        if hit is not None:
            body, age = hit
            if ttl_hours is None or (ttl_hours > 0 and age < float(ttl_hours) * 3600):
                return body
        return self._live(path, params)

    def _live(self, path, params):
        if not self.key:
            raise FootballError(f"{KEY_NAME} not set")
        used = self.budget_used()
        if used >= self.budget:
            raise FootballBudget(f"API-Football daily budget spent: {used} of {self.budget} calls today")
        wait = FLOOR_S - (time.time() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        for attempt in range(2):
            self._last_call = time.time()
            try:
                r = self.s.request("GET", BASE + path, params=params,
                                   headers={"x-apisports-key": self.key, "Accept": "application/json"}, timeout=TIMEOUT)
            except requests.RequestException as e:
                raise FootballError(f"could not reach API-Football: {type(e).__name__}") from None
            self._budget_add(1)
            self.calls += 1
            self._read_quota(getattr(r, "headers", {}) or {})
            if r.status_code == 429 and attempt == 0:
                time.sleep(2.0)
                continue
            if r.status_code >= 400:
                raise FootballError(f"HTTP {r.status_code} from API-Football on {path}: {str(r.text)[:200]}")
            try:
                body = r.json()
            except ValueError:
                raise FootballError(f"API-Football answered something that is not JSON on {path}") from None
            errs = body.get("errors") if isinstance(body, dict) else None
            if errs:
                if isinstance(errs, dict):
                    if "rateLimit" in errs and attempt == 0:
                        time.sleep(2.0)
                        continue
                    if "requests" in errs:
                        raise FootballBudget(f"API-Football: {errs['requests']}")
                    msg = "; ".join(f"{k}: {v}" for k, v in errs.items())
                else:
                    msg = str(errs)
                raise FootballError(f"API-Football error on {path}: {msg}")
            self._write_cache(path, params, body)
            return body
        raise FootballError(f"API-Football rate limit held on {path} after one retry")

    def _ttl(self, name, default):
        return self.ttl.get(name, default)

    # ---- fixtures

    def fixtures(self, league=39, season=2026, frm=None, to=None, ids=None, team=None, last=None, next=None):
        if ids:
            params = {"ids": "-".join(str(i) for i in ids)}
        else:
            params = {"league": league, "season": season, "team": team, "last": last, "next": next}
            params["from"] = frm
            params["to"] = to
        body = self.get("/fixtures", self._ttl("fixtures", 6), **params)
        return [normalize_fixture(x) for x in body.get("response") or []]

    def _home_id(self, fixture_id):
        try:
            rows = self.fixtures(ids=[fixture_id])
        except FootballError:
            return None
        return rows[0]["home_id"] if rows else None

    def lineups(self, fixture_id, home_id=None):
        """Both lineups or None until both teams have posted (nothing cached until then; then kept for good).
        home_id skips the one fixture lookup that tells which team is home."""
        body = self.peek("/fixtures/lineups", fixture=fixture_id)
        if not body or not lineups_complete(body):
            body = self.get("/fixtures/lineups", 0, fixture=fixture_id)
        if not lineups_complete(body):
            return None
        teams = [_lineup(t) for t in body["response"]]
        if home_id is None:
            home_id = self._home_id(fixture_id)
        if home_id is not None and teams[1]["team_id"] == home_id:
            teams.reverse()
        return {"home": teams[0], "away": teams[1]}

    def fixture_stats(self, fixture_id):
        """Call it after full time: the first non-empty answer is kept for good."""
        body = self.peek("/fixtures/statistics", fixture=fixture_id)
        if not body or not body.get("response"):
            body = self.get("/fixtures/statistics", 0, fixture=fixture_id)
        return parse_stats(body)

    def fixture_players(self, fixture_id):
        body = self.peek("/fixtures/players", fixture=fixture_id)
        if not body or not body.get("response"):
            body = self.get("/fixtures/players", 0, fixture=fixture_id)
        return parse_players(body)

    def injuries(self, league=39, season=2026, fixture_id=None):
        params = {"fixture": fixture_id} if fixture_id else {"league": league, "season": season}
        body = self.get("/injuries", self._ttl("injuries", 6), **params)
        out = []
        for x in body.get("response") or []:
            pl, tm, fx = x.get("player") or {}, x.get("team") or {}, x.get("fixture") or {}
            out.append({"player_id": pl.get("id"), "name": pl.get("name"), "team_id": tm.get("id"), "team": tm.get("name"),
                        "type": pl.get("type"), "reason": pl.get("reason"), "fixture_id": fx.get("id"), "date": fx.get("date")})
        return out

    def players(self, team_id, league=39, season=2026):
        """Every page. {id, name, minutes, appearances, lineups, rating, position} for this league's statistics."""
        out, page, total = [], 1, 1
        while page <= total and page <= 20:
            body = self.get("/players", self._ttl("players", 24), team=team_id, league=league, season=season, page=page)
            total = int((body.get("paging") or {}).get("total") or 1)
            for x in body.get("response") or []:
                pl = x.get("player") or {}
                stats = x.get("statistics") or []
                mine = [s for s in stats if ((s.get("league") or {}).get("id") == league)] or stats
                g = (mine[0].get("games") if mine else {}) or {}
                out.append({"id": pl.get("id"), "name": pl.get("name"), "minutes": _int(g.get("minutes")) or 0,
                            "appearances": _int(g.get("appearences", g.get("appearances"))) or 0,
                            "lineups": _int(g.get("lineups")) or 0, "rating": _num(g.get("rating")),
                            "position": g.get("position"), "injured": pl.get("injured")})
            page += 1
        return out

    def odds(self, fixture_id, bet=1):
        """Decimal Match Winner odds per bookmaker: [{bookmaker, home, draw, away}]. Empty past the 7-day window."""
        body = self.get("/odds", self._ttl("odds", 3), fixture=fixture_id, bet=bet)
        out = []
        for item in body.get("response") or []:
            for bk in item.get("bookmakers") or []:
                for b in bk.get("bets") or []:
                    if b.get("id") != bet and (b.get("name") or "").lower() != "match winner":
                        continue
                    vals = {str(v.get("value")).lower(): _num(v.get("odd")) for v in b.get("values") or []}
                    if all(vals.get(k) for k in ("home", "draw", "away")):
                        out.append({"bookmaker": bk.get("name"), "home": vals["home"], "draw": vals["draw"], "away": vals["away"]})
        return out

    def h2h(self, team_a, team_b, last=10):
        body = self.get("/fixtures/headtohead", self._ttl("h2h", 168), h2h=f"{team_a}-{team_b}", last=last)
        return [normalize_fixture(x) for x in body.get("response") or []]

    def teams(self, league=39, season=2026):
        body = self.get("/teams", self._ttl("h2h", 168), league=league, season=season)
        out = []
        for x in body.get("response") or []:
            t = x.get("team") or {}
            out.append({"id": t.get("id"), "name": t.get("name"), "code": t.get("code"), "country": t.get("country"),
                        "venue": (x.get("venue") or {}).get("name")})
        return out


# ---------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("check", help="key source and the day quota left")
    p = sub.add_parser("fixtures", help="Premier League fixtures in a date window")
    p.add_argument("--from", dest="frm"); p.add_argument("--to"); p.add_argument("--season", type=int)
    p = sub.add_parser("lineups", help="both lineups for a fixture"); p.add_argument("fixture", type=int)
    p = sub.add_parser("stats", help="match statistics for a fixture"); p.add_argument("fixture", type=int)
    p = sub.add_parser("teams", help="this season's clubs with their API ids"); p.add_argument("--season", type=int)
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return
    cfg = edge_common.load_config()
    season = getattr(a, "season", None) or cfg.get("season", 2026)
    league = cfg.get("league_id", 39)
    f = Football()
    try:
        if a.cmd == "check":
            report_key_sources([KEY_NAME])
            print(f"budget: {f.budget_used()} of {f.budget} calls used today ({f.budget_file})")
            if not f.key:
                print("no key: live calls will raise, cached data still serves")
                return
            body = f.get("/status", 0)
            req = ((body.get("response") or {}).get("requests") or {})
            sub_ = ((body.get("response") or {}).get("subscription") or {})
            print(f"plan: {sub_.get('plan')}   used today: {req.get('current')} of {req.get('limit_day')}   "
                  f"header says remaining: {f.remaining}")
        elif a.cmd == "fixtures":
            frm = a.frm or now().strftime("%Y-%m-%d")
            to = a.to or (now() + timedelta(days=7)).strftime("%Y-%m-%d")
            rows = f.fixtures(league=league, season=season, frm=frm, to=to)
            print(f"{len(rows)} fixtures {frm} to {to} (league {league}, season {season}); quota left {f.remaining}")
            for r in rows:
                score = f"{r['home_goals']}-{r['away_goals']}" if r["home_goals"] is not None else ""
                print(f"  {r['id']}  {r['kickoff_utc']}  {r['home']} v {r['away']}  {r['status']} {score}  {r['round']}")
        elif a.cmd == "lineups":
            lu = f.lineups(a.fixture)
            if not lu:
                print("not posted yet (both teams are needed)")
                return
            for side in ("home", "away"):
                t = lu[side]
                print(f"{side}: {t['team']} ({t['formation']}, {t['coach']})")
                print("   " + ", ".join(f"{p['number']} {p['name']}" for p in t["start_xi"]))
        elif a.cmd == "stats":
            print(json.dumps(f.fixture_stats(a.fixture), indent=1))
        elif a.cmd == "teams":
            for t in f.teams(league=league, season=season):
                print(f"  {t['id']:>5}  {t['code'] or '':<4} {t['name']}")
    except FootballError as e:
        sys.exit(f"API-Football: {e}")


if __name__ == "__main__":
    main()
