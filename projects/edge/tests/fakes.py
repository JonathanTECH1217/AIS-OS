"""Stand-ins for Monarc Edge's clients (2026-10-04): no network, scripted from JSON.

FakeKalshi(script)    events, markets and books from the script; orders recorded; fills after `fill_after_polls`
                      polls of .order(); settlements scripted; delist(ticker), reject_next_order(message),
                      set_price(ticker, ...), clear_events(), settle(ticker, result, ...).
FakeFootball(script)  fixtures and lineups; post_lineups(fixture_id); script["raise"] makes every call raise
                      FootballError like the real client without API_FOOTBALL_KEY.
FakePoly(script)      reachable(), list_matches(), find_match(), mids(), LAST_ERROR, like scripts/polymarket_read.py.
FakeModel(probs)      predict_fixture returns the scripted chances per (home, away).
FakeReasoner()        a fixed text with a stray "63%" and a stray model_p key, to prove the number never moves.
make_script(now)      a realistic weekend: three fixtures 48 h, 20 h and 2 h out, with one green card, ambers, reds,
                      and one green side failing the busy floor.

The server builds these when EDGE_FAKE_KALSHI, EDGE_FAKE_FOOTBALL, EDGE_FAKE_POLY or EDGE_FAKE_MODEL name a JSON
file; POST /api/fake/{kalshi|football|poly} (EDGE_TEST=1) calls .load(script) to swap the data live.
"""
import copy
import json
import math
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

try:
    from kalshi_api import KalshiError          # the real class when the other agent's module is there
except Exception:  # noqa: BLE001
    class KalshiError(Exception):
        def __init__(self, status=None, message="", body=None):
            super().__init__(message)
            self.status, self.message, self.body = status, message, body

try:
    from api_football import FootballError
except Exception:  # noqa: BLE001
    class FootballError(Exception):
        pass


def _iso(dt):
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse(s):
    if isinstance(s, datetime):
        return s
    s = str(s)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    d = datetime.fromisoformat(s)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _now():
    import edge_common as ec
    return ec.now()


def fee_usd(count, price, rate=0.07):
    return math.ceil(rate * count * price * (1 - price) * 100 - 1e-9) / 100.0


def _norm(s):
    return re.sub(r"[^a-z0-9 ]", "", str(s or "").lower()).strip()


# ---------------------------------------------------------------- Kalshi

class FakeKalshi:
    def __init__(self, script=None, env="demo", dry_run=False):
        self.env = env
        self.dry_run = dry_run
        self.base = "fake://kalshi"
        self.has_key = True
        self.calls = []
        self.orders = {}
        self.order_n = 0
        self.canceled = []
        self.load(script or {})

    def load(self, script):
        """Replace the scripted data. Orders already placed are kept."""
        self.script = copy.deepcopy(script or {})
        self.events_ = self.script.get("events") or []
        self.fill_after = self.script.get("fill_after_polls", 1)
        self.settlements_ = {s["ticker"]: s for s in self.script.get("settlements") or []}
        self.gone = set(self.script.get("delisted") or [])
        self.reject = None
        self.balance_usd = float(self.script.get("balance", 1000.0))
        return self

    # ---- test controls
    def _market_ref(self, ticker):
        for ev in self.events_:
            for m in ev.get("markets") or []:
                if m.get("ticker") == ticker:
                    return m
        return None

    def set_price(self, ticker, **fields):
        m = self._market_ref(ticker)
        if m is None:
            raise KeyError(ticker)
        m.update(fields)
        if "yes_bid" in fields or "yes_ask" in fields:
            m["no_ask"] = round(1 - m["yes_bid"], 4)
            m["no_bid"] = round(1 - m["yes_ask"], 4)
        return m

    def delist(self, ticker):
        self.gone.add(ticker)

    def clear_events(self):
        self.events_ = []

    def reject_next_order(self, message, status=403, body=None):
        self.reject = (status, message, body if body is not None else json.dumps({"error": {"code": "forbidden", "message": message}}))

    def settle(self, ticker, result, revenue_usd=None, fee_usd_=0.0):
        self.settlements_[ticker] = {"ticker": ticker, "market_result": result, "revenue_usd": revenue_usd,
                                     "fee_usd": fee_usd_, "settled_time": _iso(_now())}
        m = self._market_ref(ticker)
        if m is not None:                       # like Kalshi: the market object carries the result once decided
            m["result"] = result
            m["status"] = "settled"

    # ---- the client surface
    def _listed(self, ev):
        la = ev.get("listed_at")
        return not la or _parse(la) <= _now()

    def _market(self, m, ev):
        if m.get("ticker") in self.gone:
            return None
        out = {"ticker": m["ticker"], "event_ticker": ev["event_ticker"], "title": ev.get("title"),
               "yes_sub_title": m.get("yes_sub_title"), "status": m.get("status", "open"),
               "yes_bid": m.get("yes_bid"), "yes_ask": m.get("yes_ask"), "no_bid": m.get("no_bid"), "no_ask": m.get("no_ask"),
               "last_price": m.get("last_price", m.get("yes_ask")), "yes_ask_size": m.get("yes_ask_size", 0),
               "yes_bid_size": m.get("yes_bid_size", 0), "volume": m.get("volume", 0), "volume_24h": m.get("volume_24h", 0),
               "open_interest": m.get("open_interest", 0), "close_time": m.get("close_time"),
               "expected_expiration_time": m.get("expected_expiration_time"),
               "rules_primary": m.get("rules_primary", ev.get("rules_primary")), "result": m.get("result"),
               "raw": dict(m)}
        return out

    def markets(self, series_ticker, status="open"):
        self.calls.append(("markets", series_ticker))
        out = []
        for ev in self.events_:
            if not self._listed(ev):
                continue
            for m in ev.get("markets") or []:
                mm = self._market(m, ev)
                if mm and (status in (None, "", mm["status"])):
                    out.append(mm)
        return out

    def market(self, ticker):
        self.calls.append(("market", ticker))
        for ev in self.events_:
            if not self._listed(ev):
                continue
            for m in ev.get("markets") or []:
                if m.get("ticker") == ticker:
                    return self._market(m, ev)
        return None

    def events(self, series_ticker, status="open"):
        self.calls.append(("events", series_ticker))
        out = []
        for ev in self.events_:
            if not self._listed(ev):
                continue
            ms = [x for x in (self._market(m, ev) for m in ev.get("markets") or []) if x]
            if not ms:
                continue
            out.append({"event_ticker": ev["event_ticker"], "series_ticker": series_ticker, "title": ev.get("title"),
                        "sub_title": ev.get("sub_title"), "strike_date": ev.get("strike_date"), "markets": ms, "raw": {}})
        return out

    def event(self, event_ticker):
        return next((e for e in self.events("KXEPLGAME") if e["event_ticker"] == event_ticker), None)

    def orderbook(self, ticker, depth=5):
        self.calls.append(("orderbook", ticker))
        m = self.market(ticker)
        if not m:
            raise KalshiError(404, "market not found", "")
        return {"yes_bid": m["yes_bid"], "yes_ask": m["yes_ask"], "yes_bid_size": m["yes_bid_size"],
                "yes_ask_size": m["yes_ask_size"], "no_bid": m["no_bid"], "no_ask": m["no_ask"],
                "yes": [[m["yes_bid"], m["yes_bid_size"]]], "no": [[m["no_bid"], m["yes_ask_size"]]]}

    def exchange_status(self):
        return {"exchange_active": True, "trading_active": True}

    def balance(self):
        return {"usd": self.balance_usd}

    def positions(self):
        return [{"ticker": o["ticker"], "side": o["side"], "count": o["fill_count"]} for o in self.orders.values()
                if o["fill_count"]]

    def fills(self, ticker=None, min_ts=None):
        out = []
        for o in self.orders.values():
            if o["fill_count"] and (ticker in (None, o["ticker"])):
                out.append({"fill_id": o["order_id"] + "-f", "order_id": o["order_id"], "ticker": o["ticker"],
                            "side": o["side"], "count": o["fill_count"], "yes_price": o["price"] if o["side"] == "yes" else 1 - o["price"],
                            "is_taker": True, "fee_usd": o["fees_usd"], "created": o["created"]})
        return out

    def settlements(self, ticker=None, min_ts=None):
        out = []
        for t, s in self.settlements_.items():
            if ticker not in (None, t):
                continue
            yes_count = sum(o["fill_count"] for o in self.orders.values() if o["ticker"] == t and o["side"] == "yes")
            no_count = sum(o["fill_count"] for o in self.orders.values() if o["ticker"] == t and o["side"] == "no")
            won = yes_count if s["market_result"] == "yes" else no_count
            rev = s.get("revenue_usd")
            out.append({"ticker": t, "market_result": s["market_result"], "yes_count": yes_count, "no_count": no_count,
                        "revenue_usd": float(won) if rev is None else float(rev), "fee_usd": float(s.get("fee_usd") or 0),
                        "settled_time": s.get("settled_time") or _iso(_now())})
        return out

    def _view(self, o):
        return {"order_id": o["order_id"], "client_order_id": o["client_order_id"], "status": o["status"],
                "fill_count": o["fill_count"], "remaining_count": o["count"] - o["fill_count"],
                "avg_fill": o["price"] if o["fill_count"] else None, "fees_usd": o["fees_usd"] if o["fill_count"] else None,
                "raw": {"fake": True}}

    def order(self, order_id):
        o = self.orders.get(order_id)
        if not o:
            raise KalshiError(404, "order not found", "")
        if o["status"] == "resting":
            o["polls"] += 1
            if self.fill_after is not None and o["polls"] >= int(self.fill_after):
                self._fill(o)
        return self._view(o)

    def _fill(self, o):
        o["fill_count"] = o["count"]
        o["fees_usd"] = fee_usd(o["count"], o["price"])
        o["status"] = "executed"

    def create_order(self, ticker, side, price, count, client_order_id, expires_at=None, tif="good_till_canceled"):
        listed = self.market(ticker) is not None
        self.calls.append(("create_order", ticker, side, price, count, client_order_id))
        if self.reject:
            status, message, body = self.reject
            self.reject = None
            raise KalshiError(status, message, body)
        if not listed:
            raise KalshiError(404, "market not found", "")
        self.order_n += 1
        o = {"order_id": f"fake-order-{self.order_n}", "client_order_id": client_order_id, "ticker": ticker,
             "side": side, "price": float(price), "count": int(count), "expires_at": expires_at, "tif": tif,
             "status": "dry" if self.dry_run else "resting", "fill_count": 0, "fees_usd": 0.0, "polls": 0,
             "created": _iso(_now())}
        self.orders[o["order_id"]] = o
        if self.fill_after == 0 and not self.dry_run:
            self._fill(o)
        return self._view(o)

    def cancel(self, order_id, ticker):
        self.canceled.append(order_id)
        o = self.orders.get(order_id)
        if o and o["status"] == "resting":
            o["status"] = "canceled"
        return {"order_id": order_id, "status": "canceled"}


# ---------------------------------------------------------------- football

class FakeFootball:
    def __init__(self, script=None):
        self.calls = []
        self.load(script or {})

    def load(self, script):
        self.script = copy.deepcopy(script or {})
        self.fixtures_ = self.script.get("fixtures") or []
        self.lineups_ = {int(k): v for k, v in (self.script.get("lineups") or {}).items()}
        self.raise_ = bool(self.script.get("raise"))
        self.remaining = int(self.script.get("remaining", 5990))
        return self

    def _guard(self, what):
        self.calls.append(what)
        if self.raise_:
            raise FootballError("API_FOOTBALL_KEY not found: no live calls")
        self.remaining -= 1

    def fixtures(self, league=39, season=2026, frm=None, to=None, ids=None, team=None, last=None, next=None):
        self._guard(("fixtures", frm, to))
        rows = self.fixtures_
        if ids:
            rows = [r for r in rows if r["id"] in ids]
        if frm:
            rows = [r for r in rows if r["kickoff_utc"][:10] >= str(frm)[:10]]
        if to:
            rows = [r for r in rows if r["kickoff_utc"][:10] <= str(to)[:10]]
        return copy.deepcopy(rows)

    def lineups(self, fixture_id):
        self._guard(("lineups", fixture_id))
        return copy.deepcopy(self.lineups_.get(int(fixture_id)))

    def post_lineups(self, fixture_id, home_formation="4-3-3", away_formation="4-2-3-1"):
        fx = next((r for r in self.fixtures_ if r["id"] == fixture_id), {})
        def xi(team_id, prefix):
            return {"team_id": team_id, "formation": home_formation,
                    "start_xi": [{"id": team_id * 100 + i, "name": f"{prefix} {i}", "pos": "M", "number": i} for i in range(1, 12)],
                    "subs": [{"id": team_id * 100 + i, "name": f"{prefix} sub {i}", "pos": "M", "number": i} for i in range(12, 19)]}
        self.lineups_[int(fixture_id)] = {"home": xi(fx.get("home_id", 1), fx.get("home", "Home")),
                                          "away": {**xi(fx.get("away_id", 2), fx.get("away", "Away")), "formation": away_formation}}
        return self.lineups_[int(fixture_id)]

    def fixture_stats(self, fixture_id):
        self._guard(("stats", fixture_id))
        return {}

    def fixture_players(self, fixture_id):
        self._guard(("players", fixture_id))
        return {}

    def injuries(self, *a, **k):
        self._guard(("injuries",))
        return []

    def players(self, team_id, *a, **k):
        self._guard(("players", team_id))
        return []

    def odds(self, fixture_id):
        self._guard(("odds", fixture_id))
        return []

    def teams(self, *a, **k):
        self._guard(("teams",))
        return []


# ---------------------------------------------------------------- Polymarket

class FakePoly:
    LAST_ERROR = None

    def __init__(self, script=None):
        self.load(script or {})

    def load(self, script):
        self.script = copy.deepcopy(script or {})
        self.matches_ = self.script.get("matches") or []
        self.reachable_ = bool(self.script.get("reachable", True))
        return self

    def reachable(self):
        return self.reachable_

    def list_matches(self, days=16):
        if not self.reachable_:
            raise OSError("polymarket unreachable")
        return copy.deepcopy(self.matches_)

    def find_match(self, home_name, away_name, kickoff_utc, matches=None, tolerance_s=600):
        """Same two names and a kickoff within tolerance_s (10 minutes by default, 36 h when the loop has no feed)."""
        want = None
        if kickoff_utc:
            s = str(kickoff_utc).replace("Z", "+00:00")
            want = datetime.fromisoformat(s)
            if want.tzinfo is None:
                want = want.replace(tzinfo=timezone.utc)
        for m in (matches if matches is not None else self.matches_):
            if _norm(m.get("home_name")) != _norm(home_name) or _norm(m.get("away_name")) != _norm(away_name):
                continue
            k = m.get("kickoff_utc")
            if want is not None and k:
                kd = datetime.fromisoformat(str(k).replace("Z", "+00:00"))
                if kd.tzinfo is None:
                    kd = kd.replace(tzinfo=timezone.utc)
                if abs((kd - want).total_seconds()) > tolerance_s:
                    continue
            return m
        return None

    def mids(self, match):
        mids = dict(match.get("mids") or {})
        mids.setdefault("source", "fake")
        return mids


# ---------------------------------------------------------------- model and reasoner

class FakeModel:
    def __init__(self, probs=None):
        self.version = "fake-1"
        self.load(probs or {})

    def load(self, probs):
        self.probs = {}
        for k, v in (probs or {}).items():
            key = tuple(k) if isinstance(k, (list, tuple)) else tuple(str(k).split("|", 1))
            self.probs[(_norm(key[0]), _norm(key[1]))] = v
        return self

    def refresh(self):
        return self.version

    def predict_fixture(self, home_name, away_name, kickoff_utc, lineups=None):
        v = self.probs.get((_norm(home_name), _norm(away_name)))
        if not v:
            return None
        p = {"p_home": float(v["p_home"]), "p_draw": float(v["p_draw"]), "p_away": float(v["p_away"])}
        return {**p, "version": self.version,
                "contributions": [{"name": "home form (10)", "value": 1.8, "effect": 0.04},
                                  {"name": "away form (10)", "value": 1.5, "effect": -0.02},
                                  {"name": "shots on target blend", "value": 0.5, "effect": 0.01},
                                  {"name": "lineups", "value": 1 if lineups else 0, "effect": 0.0}],
                "sources": ["fake model"], "ratings": {"home": 1.0, "away": 1.0}}


class FakeReasoner:
    def __init__(self, cfg=None):
        self.cfg = cfg
        self.calls = []

    def write(self, card, context):
        self.calls.append((card.get("id"), card.get("model_p")))
        return {"reasoning": f"Fixed fake note for {card.get('outcome_name') or card.get('outcome')}. "
                             "Our model gives it a 63% chance (this number is a stray and must change nothing).",
                "flags": ["fake reasoning"], "model_p": 0.63, "p_home": 0.63}


# ---------------------------------------------------------------- a realistic weekend

def _ticker_date(dt):
    return dt.strftime("%y%b%d").upper()


def market(ticker, sub, yes_bid, yes_ask, volume, size=400, close=None, expiration=None, status="open"):
    return {"ticker": ticker, "yes_sub_title": sub, "yes_bid": yes_bid, "yes_ask": yes_ask,
            "no_bid": round(1 - yes_ask, 4), "no_ask": round(1 - yes_bid, 4), "yes_ask_size": size, "yes_bid_size": size,
            "volume": volume, "open_interest": volume // 2, "close_time": close, "expected_expiration_time": expiration,
            "status": status, "rules_primary": "If the match ends in a win for the named team in regulation plus stoppage time, the market resolves Yes. A draw resolves the Tie market Yes."}


def fixture_script(now, hours, home, away, home_code, away_code, prices, fixture_id, listed_at=None, poly=None):
    """One fixture for all four fakes. prices: {outcome: (yes_bid, yes_ask, volume)}."""
    kickoff = now + timedelta(hours=hours)
    ev_ticker = f"KXEPLGAME-{_ticker_date(kickoff)}{home_code}{away_code}"
    exp = _iso(kickoff + timedelta(hours=3))      # Kalshi expects to settle 3 h after kickoff (checked 2026-10-04)
    ev = {"event_ticker": ev_ticker, "title": f"{home} vs {away}", "strike_date": _iso(kickoff),
          "markets": [market(f"{ev_ticker}-{home_code}", home, *prices["home"], close=exp, expiration=exp),
                      market(f"{ev_ticker}-{away_code}", away, *prices["away"], close=exp, expiration=exp),
                      market(f"{ev_ticker}-TIE", "Tie", *prices["draw"], close=exp, expiration=exp)]}
    if listed_at:
        ev["listed_at"] = _iso(listed_at)
    fx = {"id": fixture_id, "kickoff_utc": _iso(kickoff), "status": "NS", "round": "Regular Season - 8",
          "home_id": fixture_id * 10 + 1, "home": home, "away_id": fixture_id * 10 + 2, "away": away,
          "home_goals": None, "away_goals": None, "venue": f"{home} ground"}
    pm = {"slug": f"epl-{home_code.lower()}-{away_code.lower()}-{kickoff:%Y-%m-%d}", "title": f"{home} vs. {away}",
          "home_name": home, "away_name": away, "kickoff_utc": _iso(kickoff),
          "markets": {"home": f"pm-{home_code}", "draw": f"pm-TIE-{home_code}", "away": f"pm-{away_code}"},
          "mids": poly or {}}
    return ev, fx, pm


def make_script(now=None):
    """Three fixtures 48 h, 20 h and 2 h out. Returns {"kalshi", "football", "poly", "model"} scripts.

    Against the model's chances the prices make: Arsenal (48 h) green at 8.3 points; Chelsea (2 h) green at 8.3;
    Nottingham Forest, Tie (48 h), Liverpool, Tottenham amber; Manchester City, Tie (2 h) red; the 20 h Tie green on
    price but with only 3,000 contracts traded, so the busy floor fails. Polymarket agrees with us on Arsenal
    (53 cents against Kalshi's 44.5), so that card carries "second witness disagrees"."""
    now = now or datetime.now(timezone.utc).replace(microsecond=0)
    a = fixture_script(now, 48, "Nottingham Forest", "Arsenal", "NFO", "ARS",
                       {"home": (0.24, 0.25, 20000), "away": (0.44, 0.45, 25000), "draw": (0.29, 0.30, 15000)}, 1001,
                       poly={"home": 0.21, "draw": 0.26, "away": 0.53})
    b = fixture_script(now, 20, "Liverpool", "Manchester City", "LIV", "MCI",
                       {"home": (0.41, 0.42, 40000), "away": (0.35, 0.36, 30000), "draw": (0.19, 0.20, 3000)}, 1002,
                       poly={"home": 0.415, "draw": 0.20, "away": 0.355})
    c = fixture_script(now, 2, "Chelsea", "Tottenham", "CHE", "TOT",
                       {"home": (0.39, 0.40, 30000), "away": (0.29, 0.30, 20000), "draw": (0.26, 0.27, 12000)}, 1003,
                       poly={"home": 0.40, "draw": 0.265, "away": 0.30})
    model = {"Nottingham Forest|Arsenal": {"p_home": 0.20, "p_draw": 0.25, "p_away": 0.55},
             "Liverpool|Manchester City": {"p_home": 0.36, "p_draw": 0.30, "p_away": 0.34},
             "Chelsea|Tottenham": {"p_home": 0.50, "p_draw": 0.25, "p_away": 0.25}}
    return {"kalshi": {"events": [a[0], b[0], c[0]], "fill_after_polls": 1, "settlements": [], "balance": 1000.0},
            "football": {"fixtures": [a[1], b[1], c[1]], "lineups": {}},
            "poly": {"reachable": True, "matches": [a[2], b[2], c[2]]},
            "model": model}


def write_scripts(folder, now=None):
    """The four JSON files the server's EDGE_FAKE_* hooks read. Returns {name: path}."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    s = make_script(now)
    out = {}
    for name in ("kalshi", "football", "poly", "model"):
        p = folder / f"fake-{name}.json"
        p.write_text(json.dumps(s[name], indent=1), encoding="utf-8")
        out[name] = p
    return out


if __name__ == "__main__":
    print(json.dumps(make_script(), indent=1)[:3000])
