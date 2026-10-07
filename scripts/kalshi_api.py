"""Kalshi: the Premier League match-winner markets and the account that trades them (Monarc Edge, 2026-10-04).

A thin client over Kalshi's trade API v2. Public reads (markets, events, order books, exchange status) need no
key. Account calls (balance, positions, fills, settlements, orders) sign every request with the RSA key Kalshi
gives once: the three headers are KALSHI-ACCESS-KEY (the key id), KALSHI-ACCESS-TIMESTAMP (Unix ms as a string)
and KALSHI-ACCESS-SIGNATURE (RSA-PSS SHA-256 over timestamp + METHOD + path, base64). The path signed is the
full path from the host root, /trade-api/v2/..., without the query string.

Two environments with separate keys. Demo: demo-api.kalshi.co, play money; prod: api.elections.kalshi.com, real
money. Key names (values in ~/.monarc/secrets.env or the repo .env, PEM files beside secrets.env, never inside it;
references/credentials.md):
  demo  KALSHI_DEMO_API_KEY_ID (or KALSHI_DEMO_API_KEY), KALSHI_DEMO_PRIVATE_KEY_PATH (default ~/.monarc/kalshi-demo.pem)
  prod  KALSHI_API_KEY_ID (or KALSHI_API_KEY), KALSHI_PRIVATE_KEY_PATH (default ~/.monarc/kalshi-prod.pem or kalshi.pem)
The key Kalshi hands out may be RSA or Ed25519; both sign the same message (Ed25519 signs it raw).

Dry run (the default): create_order and cancel never touch the network. They append one line to
projects/edge/data/dry-run.jsonl and answer like a resting order with a "dry-" id. Every read still goes live.
Prod with dry_run off is refused unless allow_prod=True is passed, which the server does only when the config
says rehearsal_passed. The AIOS never flips that itself.

Orders use the V2 route only (POST /portfolio/events/orders). Kalshi's V2 speaks in YES terms: side "bid" buys
YES at the price, side "ask" sells YES, which opens a NO position. create_order takes the side you want to BUY
("yes" or "no") and the price of that side, and maps: buy No at 0.77 becomes side "ask" at price "0.2300".

  python scripts/kalshi_api.py check [--prod]              env, key sources, exchange status, balance if a key
  python scripts/kalshi_api.py markets [SERIES]            every open market in the series (default KXEPLGAME)
  python scripts/kalshi_api.py events [SERIES]             every open event with its three markets
  python scripts/kalshi_api.py event TICKER                one event
  python scripts/kalshi_api.py book TICKER                 the order book, five levels a side
  python scripts/kalshi_api.py order TICKER yes|no PRICE COUNT [--prod] --really
                                                           place an order; without --really it dry-runs
  python scripts/kalshi_api.py cancel ORDER_ID TICKER --really
  python scripts/kalshi_api.py fills
  python scripts/kalshi_api.py settlements [--since YYYY-MM-DD]
Default env is demo. Guide: references/kalshi-api.md.
"""
import argparse
import base64
import json
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edge_common  # noqa: E402
from edge_common import KEY_NAMES, get_secret, iso, now, parse_iso  # noqa: E402

PREFIX = "/trade-api/v2"
BASES = {
    "demo": ["https://demo-api.kalshi.co" + PREFIX, "https://external-api.demo.kalshi.co" + PREFIX],
    "prod": ["https://api.elections.kalshi.com" + PREFIX, "https://external-api.kalshi.com" + PREFIX],
}
UA = "MonarcEdge/1.0 (+kalshi_api.py)"
TIMEOUT = (5, 20)
PAGE = 200
WAITS_429 = (0.5, 1.0, 2.0)
TIFS = ("good_till_canceled", "fill_or_kill", "immediate_or_cancel")
_STRIKE = re.compile(r"-(\d{2})([A-Z]{3})(\d{2})([A-Z]+)$")
_MONTHS = {m: i for i, m in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"), 1)}


class KalshiError(Exception):
    """Anything Kalshi refused or we could not reach. .status is the HTTP code or None, .body the raw text."""

    def __init__(self, status, message, body=""):
        super().__init__(message)
        self.status = status
        self.message = message
        self.body = body or ""


# ---------------------------------------------------------------- number helpers

def _dollars(obj, name):
    """The `<name>_dollars` string as a float, else the old cents field `<name>` over 100, else None."""
    v = obj.get(name + "_dollars")
    if v not in (None, ""):
        return float(v)
    v = obj.get(name)
    if v in (None, ""):
        return None
    return float(v) / 100.0 if not isinstance(v, str) else float(v)


def _fp(obj, name):
    """The `<name>_fp` string as a float, else the old integer field `<name>`, else None."""
    v = obj.get(name + "_fp")
    if v not in (None, ""):
        return float(v)
    v = obj.get(name)
    return None if v in (None, "") else float(v)


def _count(v):
    """A fixed-point count string ("26.00") or an integer as a whole number. None and "" are 0."""
    if v in (None, ""):
        return 0
    return int(round(float(v)))


def _money(v):
    """A FixedPointDollars string as a float; an integer is cents. None stays None."""
    if v in (None, ""):
        return None
    if isinstance(v, str):
        return float(v)
    return float(v) / 100.0


def _unix(ts):
    """ISO string, datetime, or a number to Unix seconds. None stays None."""
    if ts is None or ts == "":
        return None
    if isinstance(ts, (int, float)):
        return int(ts)
    return int(parse_iso(ts).timestamp())


# ---------------------------------------------------------------- normalizers (pure, used by the tests)

def normalize_market(m):
    """One market as the agent reads it: floats in dollars (0..1) and contracts, None when a field is missing."""
    return {
        "ticker": m.get("ticker"), "event_ticker": m.get("event_ticker"), "title": m.get("title"),
        "yes_sub_title": m.get("yes_sub_title"), "status": m.get("status"),
        "yes_bid": _dollars(m, "yes_bid"), "yes_ask": _dollars(m, "yes_ask"),
        "no_bid": _dollars(m, "no_bid"), "no_ask": _dollars(m, "no_ask"),
        "last_price": _dollars(m, "last_price"),
        "yes_ask_size": _fp(m, "yes_ask_size"), "yes_bid_size": _fp(m, "yes_bid_size"),
        "volume": _fp(m, "volume"), "volume_24h": _fp(m, "volume_24h"), "open_interest": _fp(m, "open_interest"),
        "close_time": m.get("close_time"), "expected_expiration_time": m.get("expected_expiration_time"),
        "rules_primary": m.get("rules_primary"), "raw": m,
    }


def strike_date_of(event_ticker):
    """KXEPLGAME-26OCT18NFOARS -> '2026-10-18'. None when the ticker does not carry a date."""
    mt = _STRIKE.search(event_ticker or "")
    if not mt:
        return None
    yy, mon, dd = mt.group(1), mt.group(2), mt.group(3)
    if mon not in _MONTHS:
        return None
    return f"20{yy}-{_MONTHS[mon]:02d}-{dd}"


def codes_of(event_ticker, markets):
    """(home code, away code) from the event's markets: the two tickers that are not -TIE, in title order."""
    codes = [m.get("ticker", "").rsplit("-", 1)[-1] for m in markets]
    codes = [c for c in codes if c and c != "TIE"]
    if len(codes) == 2:
        return codes[0], codes[1]
    return None, None


def normalize_event(e, markets=None):
    """One event with its markets. home and away come from the title ('Nottingham Forest vs Arsenal', home first)."""
    raw_markets = markets if markets is not None else (e.get("markets") or [])
    title = e.get("title") or ""
    home = away = None
    if " vs " in title:
        home, away = [p.strip() for p in title.split(" vs ", 1)]
    home_code, away_code = codes_of(e.get("event_ticker"), raw_markets)
    return {
        "event_ticker": e.get("event_ticker"), "series_ticker": e.get("series_ticker"), "title": title,
        "sub_title": e.get("sub_title"), "strike_date": e.get("strike_date") or strike_date_of(e.get("event_ticker")),
        "home": home, "away": away, "home_code": home_code, "away_code": away_code,
        "markets": [normalize_market(m) for m in raw_markets], "raw": {k: v for k, v in e.items() if k != "markets"},
    }


def parse_orderbook(body):
    """The book as bids on each side, best first, plus the asks they imply: the yes ask is 1 minus the best no bid.
    A yes buy fills against the no bidders, so yes_ask_size is the size at the best no bid."""
    ob = body.get("orderbook_fp")
    cents = False
    if ob is None:
        ob = body.get("orderbook") or {}
        cents = True
    yes = ob.get("yes_dollars") if not cents else ob.get("yes")
    no = ob.get("no_dollars") if not cents else ob.get("no")

    def levels(side):
        out = []
        for lvl in side or []:
            p, n = float(lvl[0]), float(lvl[1])
            if cents:
                p = p / 100.0
            out.append([round(p, 4), n])
        out.sort(key=lambda x: -x[0])
        return out

    yes, no = levels(yes), levels(no)
    yes_bid = yes[0][0] if yes else None
    no_bid = no[0][0] if no else None
    return {
        "yes_bid": yes_bid, "yes_ask": round(1.0 - no_bid, 4) if no_bid is not None else None,
        "yes_bid_size": yes[0][1] if yes else None, "yes_ask_size": no[0][1] if no else None,
        "no_bid": no_bid, "no_ask": round(1.0 - yes_bid, 4) if yes_bid is not None else None,
        "yes": yes, "no": no,
    }


def normalize_order(o, tif=None):
    """The order shape the backend stores. status is resting | canceled | executed (| dry)."""
    fill = _count(o.get("fill_count_fp", o.get("fill_count")))
    remaining = _count(o.get("remaining_count_fp", o.get("remaining_count")))
    status = o.get("status")
    if not status:
        if remaining == 0:
            status = "executed"
        elif tif in ("fill_or_kill", "immediate_or_cancel"):
            status = "canceled"
        else:
            status = "resting"
    avg = _money(o.get("average_fill_price"))
    if avg is None and fill:
        cost = (_money(o.get("taker_fill_cost_dollars")) or 0.0) + (_money(o.get("maker_fill_cost_dollars")) or 0.0)
        if cost:
            avg = round(cost / fill, 4)
    fees = _money(o.get("average_fee_paid"))
    if fees is not None and fill:
        fees = round(fees * fill, 2)
    else:
        fees = (_money(o.get("taker_fees_dollars", o.get("taker_fees"))) or 0.0) + \
               (_money(o.get("maker_fees_dollars", o.get("maker_fees"))) or 0.0)
    return {"order_id": o.get("order_id"), "client_order_id": o.get("client_order_id"), "status": status,
            "fill_count": fill, "remaining_count": remaining, "avg_fill": avg, "fees_usd": round(fees or 0.0, 2),
            "raw": o}


# ---------------------------------------------------------------- the client

ALIAS_ID = {"prod": "KALSHI_API_KEY", "demo": "KALSHI_DEMO_API_KEY"}   # the name Jonathan saved the key id under (2026-10-04)
DEFAULT_PEMS = {"prod": ("kalshi-prod.pem", "kalshi.pem"), "demo": ("kalshi-demo.pem",)}


def _default_pem(env):
    """The PEM beside secrets.env when no *_PRIVATE_KEY_PATH is set: ~/.monarc/kalshi-prod.pem or kalshi.pem for
    prod, kalshi-demo.pem for demo. None when none exists."""
    home = Path.home() / ".monarc"
    for name in DEFAULT_PEMS.get(env, ()):
        if (home / name).exists():
            return str(home / name)
    return None


class Kalshi:
    def __init__(self, env="demo", dry_run=True, key_id=None, key_path=None, session=None, allow_prod=False):
        if env not in BASES:
            raise KalshiError(None, f"env must be demo or prod, not {env!r}")
        if env == "prod" and not dry_run and not allow_prod:
            raise KalshiError(None, "prod with dry_run off needs allow_prod=True (the server passes it only once "
                                    "rehearsal_passed is true)")
        self.env = env
        self.dry_run = bool(dry_run)
        self._bases = list(BASES[env])
        self.base = self._bases[0]
        self.s = session or requests.Session()
        self.id_name, self.path_name = KEY_NAMES["kalshi_demo" if env == "demo" else "kalshi"]
        self.key_id = key_id or get_secret(self.id_name) or get_secret(ALIAS_ID[env])
        self.key_path = key_path or get_secret(self.path_name) or _default_pem(env)
        self._key = None
        self.key_error = None
        self._last_msg = None
        self._load_key()

    # ---- keys and signing

    def _load_key(self):
        if not self.key_id:
            self.key_error = f"{self.id_name} not set"
            return
        if not self.key_path:
            self.key_error = f"{self.path_name} not set"
            return
        p = Path(str(self.key_path)).expanduser()
        if not p.exists():
            self.key_error = f"PEM file not found at {p}"
            return
        try:
            from cryptography.hazmat.primitives import serialization
            self._key = serialization.load_pem_private_key(p.read_bytes(), password=None)
        except Exception as e:  # noqa: BLE001
            self.key_error = f"could not read the PEM at {p}: {type(e).__name__}"

    @property
    def has_key(self):
        return self._key is not None and bool(self.key_id)

    def sign(self, method, path):
        """The three auth headers for one request. `path` is the full path (/trade-api/v2/...); any query string is
        dropped before signing, as Kalshi requires."""
        if not self.has_key:
            raise KalshiError(None, f"Kalshi {self.env} account call needs a key: {self.key_error}")
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ed25519, padding
        ts = str(int(time.time() * 1000))
        clean = path.split("?", 1)[0]
        msg = ts + method.upper() + clean
        self._last_msg = msg
        if isinstance(self._key, ed25519.Ed25519PrivateKey):      # Kalshi also issues Ed25519 keys (Jonathan's is one)
            sig = self._key.sign(msg.encode("utf-8"))
        else:
            sig = self._key.sign(msg.encode("utf-8"),
                                 padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=hashes.SHA256().digest_size),
                                 hashes.SHA256())
        return {"KALSHI-ACCESS-KEY": self.key_id, "KALSHI-ACCESS-TIMESTAMP": ts,
                "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode("ascii")}

    # ---- transport

    def _request(self, method, route, params=None, body=None, auth=False, ok404=False):
        """One call with the retry rules: 429 waits 0.5, 1, 2 s (three retries); a 5xx retries once; a connection
        error tries the other host for this env once. Raises KalshiError on anything else above 399."""
        path = PREFIX + route
        if auth and not self.has_key:
            raise KalshiError(None, f"Kalshi {self.env} account call needs a key: {self.key_error}")
        n429 = n5xx = 0
        hosts_left = [b for b in self._bases if b != self.base]
        while True:
            headers = {"Accept": "application/json", "User-Agent": UA}
            if body is not None:
                headers["Content-Type"] = "application/json"
            if self.has_key:
                headers.update(self.sign(method, path))
            try:
                r = self.s.request(method, self.base + route, params=params, json=body, headers=headers, timeout=TIMEOUT)
            except (requests.ConnectionError, requests.Timeout) as e:
                if hosts_left:
                    self.base = hosts_left.pop(0)
                    continue
                raise KalshiError(None, f"could not reach Kalshi {self.env}: {type(e).__name__}") from None
            if r.status_code == 429 and n429 < len(WAITS_429):
                time.sleep(WAITS_429[n429])
                n429 += 1
                continue
            if 500 <= r.status_code < 600 and n5xx < 1:
                n5xx += 1
                time.sleep(1.0)
                continue
            if r.status_code == 404 and ok404:
                return None
            if r.status_code >= 400:
                raise KalshiError(r.status_code, self._message(r), r.text)
            if not r.text:
                return {}
            try:
                return r.json()
            except ValueError:
                raise KalshiError(r.status_code, "Kalshi answered something that is not JSON", r.text[:500]) from None

    @staticmethod
    def _message(r):
        try:
            b = r.json()
            if isinstance(b, dict):
                err = b.get("error")
                if isinstance(err, dict):
                    return f"HTTP {r.status_code}: {err.get('message') or err.get('code') or err}"
                return f"HTTP {r.status_code}: {b.get('message') or err or r.text[:200]}"
        except ValueError:
            pass
        return f"HTTP {r.status_code}: {r.text[:200]}"

    def _pages(self, route, key, params, auth=False):
        """Every page of a cursor-paginated list. An empty or missing cursor is the last page."""
        out, cursor, params = [], None, dict(params or {})
        params.setdefault("limit", PAGE)
        for _ in range(50):
            if cursor:
                params["cursor"] = cursor
            body = self._request("GET", route, params=params, auth=auth) or {}
            out.extend(body.get(key) or [])
            cursor = body.get("cursor")
            if not cursor:
                break
        return out

    # ---- public reads

    def markets(self, series_ticker, status="open"):
        params = {"series_ticker": series_ticker}
        if status:
            params["status"] = status
        return [normalize_market(m) for m in self._pages("/markets", "markets", params)]

    def market(self, ticker):
        body = self._request("GET", f"/markets/{ticker}", ok404=True)
        if not body:
            return None
        m = body.get("market") or body
        return normalize_market(m) if m.get("ticker") else None

    def events(self, series_ticker, status="open"):
        params = {"series_ticker": series_ticker, "with_nested_markets": "true"}
        if status:
            params["status"] = status
        return [normalize_event(e) for e in self._pages("/events", "events", params)]

    def event(self, event_ticker):
        body = self._request("GET", f"/events/{event_ticker}", params={"with_nested_markets": "true"}, ok404=True)
        if not body:
            return None
        e = body.get("event") or {}
        if not e.get("event_ticker"):
            return None
        markets = e.get("markets") or body.get("markets") or []
        return normalize_event(e, markets)

    def orderbook(self, ticker, depth=5):
        body = self._request("GET", f"/markets/{ticker}/orderbook", params={"depth": int(depth)}) or {}
        return parse_orderbook(body)

    def exchange_status(self):
        body = self._request("GET", "/exchange/status") or {}
        trading = body.get("trading_active")
        if trading is None:
            for st in body.get("exchange_index_statuses") or []:
                if st.get("exchange_index") in (0, None):
                    trading = st.get("trading_active")
                    break
        return {"exchange_active": bool(body.get("exchange_active")), "trading_active": bool(trading)}

    # ---- account reads

    def balance(self):
        body = self._request("GET", "/portfolio/balance", auth=True) or {}
        usd = _money(body.get("balance_dollars"))
        if usd is None:
            usd = _money(body.get("balance"))
        return {"usd": round(usd or 0.0, 2), "raw": body}

    def positions(self):
        """Open market positions: position > 0 is yes contracts held, < 0 is no contracts."""
        rows = self._pages("/portfolio/positions", "market_positions", {"settlement_status": "unsettled"}, auth=True)
        out = []
        for p in rows:
            pos = _fp(p, "position")
            out.append({"ticker": p.get("ticker"), "position": pos or 0.0,
                        "exposure_usd": _money(p.get("market_exposure_dollars", p.get("market_exposure"))),
                        "realized_pnl_usd": _money(p.get("realized_pnl_dollars", p.get("realized_pnl"))),
                        "fees_paid_usd": _money(p.get("fees_paid_dollars", p.get("fees_paid"))),
                        "total_traded_usd": _money(p.get("total_traded_dollars", p.get("total_traded"))),
                        "raw": p})
        return out

    def fills(self, ticker=None, min_ts=None):
        params = {}
        if ticker:
            params["ticker"] = ticker
        if min_ts is not None:
            params["min_ts"] = _unix(min_ts)
        out = []
        for f in self._pages("/portfolio/fills", "fills", params, auth=True):
            out.append({"fill_id": f.get("fill_id") or f.get("trade_id"), "order_id": f.get("order_id"),
                        "ticker": f.get("ticker") or f.get("market_ticker"),
                        "side": (f.get("outcome_side") or f.get("side") or "").lower() or None,
                        "count": _count(f.get("count_fp", f.get("count"))),
                        "yes_price": _dollars(f, "yes_price"), "is_taker": bool(f.get("is_taker")),
                        "fee_usd": _money(f.get("fee_cost_dollars", f.get("fee_cost"))) or 0.0,
                        "created": f.get("created_time"), "raw": f})
        return out

    def settlements(self, ticker=None, min_ts=None):
        params = {}
        if ticker:
            params["ticker"] = ticker
        if min_ts is not None:
            params["min_ts"] = _unix(min_ts)
        out = []
        for s_ in self._pages("/portfolio/settlements", "settlements", params, auth=True):
            revenue = _money(s_.get("revenue_dollars"))
            if revenue is None:
                revenue = _money(s_.get("revenue"))
            out.append({"ticker": s_.get("ticker"), "market_result": (s_.get("market_result") or "").lower() or None,
                        "yes_count": _count(s_.get("yes_count_fp", s_.get("yes_count"))),
                        "no_count": _count(s_.get("no_count_fp", s_.get("no_count"))),
                        "revenue_usd": revenue or 0.0,
                        "fee_usd": _money(s_.get("fee_cost_dollars", s_.get("fee_cost"))) or 0.0,
                        "settled_time": s_.get("settled_time"), "raw": s_})
        return out

    def order(self, order_id):
        if str(order_id).startswith("dry-"):
            return {"order_id": order_id, "client_order_id": None, "status": "dry", "fill_count": 0,
                    "remaining_count": 0, "avg_fill": None, "fees_usd": 0.0, "raw": {}}
        body = self._request("GET", f"/portfolio/orders/{order_id}", auth=True) or {}
        return normalize_order(body.get("order") or body)

    # ---- orders (V2)

    @staticmethod
    def v2_body(ticker, side, price, count, client_order_id, expires_at=None, tif="good_till_canceled"):
        """The V2 order body. side is the side you BUY and price its dollars; a No buy becomes an ask at 1 - price."""
        side = str(side).lower()
        if side not in ("yes", "no"):
            raise KalshiError(None, f"side must be yes or no, not {side!r}")
        if tif not in TIFS:
            raise KalshiError(None, f"time_in_force must be one of {TIFS}, not {tif!r}")
        price = float(price)
        if not 0.01 <= price <= 0.99:
            raise KalshiError(None, f"price must be between 0.01 and 0.99 dollars, not {price}")
        count = int(count)
        if count < 1:
            raise KalshiError(None, f"count must be at least 1, not {count}")
        yes_price = price if side == "yes" else 1.0 - price
        body = {"ticker": ticker, "side": "bid" if side == "yes" else "ask", "count": str(count),
                "price": f"{round(yes_price + 1e-9, 2):.4f}", "time_in_force": tif,
                "self_trade_prevention_type": "taker_at_cross", "client_order_id": str(client_order_id),
                "post_only": False}
        exp = _unix(expires_at)
        if exp:
            body["expiration_time"] = exp
        return body

    def _dry_log(self, method, path, body):
        line = {"ts": iso(now()), "env": self.env, "method": method, "path": path, "body": body,
                "headers": {"KALSHI-ACCESS-KEY": "<key id>" if self.key_id else "<no key>",
                            "KALSHI-ACCESS-TIMESTAMP": str(int(time.time() * 1000)),
                            "KALSHI-ACCESS-SIGNATURE": "<signed>"}}
        p = Path(edge_common.DRY_RUN_LOG)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")
        return line

    def create_order(self, ticker, side, price, count, client_order_id, expires_at=None, tif="good_till_canceled"):
        body = self.v2_body(ticker, side, price, count, client_order_id, expires_at, tif)
        route = "/portfolio/events/orders"
        if self.dry_run:
            self._dry_log("POST", PREFIX + route, body)
            return {"order_id": "dry-" + uuid.uuid4().hex[:12], "client_order_id": str(client_order_id),
                    "status": "dry", "fill_count": 0, "remaining_count": int(count), "avg_fill": None,
                    "fees_usd": 0.0, "raw": body}
        resp = self._request("POST", route, body=body, auth=True) or {}
        o = resp.get("order") or resp
        out = normalize_order(o, tif)
        out["client_order_id"] = out.get("client_order_id") or str(client_order_id)
        if not out.get("remaining_count") and not out.get("fill_count"):
            out["remaining_count"] = int(count)
        return out

    def cancel(self, order_id, ticker):
        route = f"/portfolio/events/orders/{order_id}"
        if self.dry_run or str(order_id).startswith("dry-"):
            self._dry_log("DELETE", PREFIX + route, {"market_ticker": ticker})
            return {"order_id": order_id, "status": "dry"}
        resp = self._request("DELETE", route, params={"market_ticker": ticker}, auth=True) or {}
        return {"order_id": resp.get("order_id") or order_id, "status": "canceled",
                "reduced_by": _count(resp.get("reduced_by")), "raw": resp}


# ---------------------------------------------------------------- CLI

def _fmt(v, nd=2):
    return "-" if v is None else f"{v:.{nd}f}"


def _print_event(e):
    print(f"{e['event_ticker']}  {e['title']}  ({e.get('strike_date') or ''})")
    for m in e["markets"]:
        code = (m["ticker"] or "").rsplit("-", 1)[-1]
        print(f"   {code:<4} {m['yes_sub_title']:<20} yes {_fmt(m['yes_bid'])}/{_fmt(m['yes_ask'])}  "
              f"no {_fmt(m['no_bid'])}/{_fmt(m['no_ask'])}  vol {int(m['volume'] or 0):,}  oi {int(m['open_interest'] or 0):,}  {m['status']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--prod", action="store_true", help="production instead of demo")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("check", help="env, key sources, exchange status, balance if a key")
    p = sub.add_parser("markets", help="every open market in a series"); p.add_argument("series", nargs="?")
    p = sub.add_parser("events", help="every open event with its markets"); p.add_argument("series", nargs="?")
    p = sub.add_parser("event", help="one event"); p.add_argument("ticker")
    p = sub.add_parser("book", help="the order book"); p.add_argument("ticker"); p.add_argument("--depth", type=int, default=5)
    p = sub.add_parser("order", help="place an order (dry run without --really)")
    p.add_argument("ticker"); p.add_argument("side", choices=("yes", "no")); p.add_argument("price", type=float)
    p.add_argument("count", type=int); p.add_argument("--tif", default="good_till_canceled", choices=TIFS)
    p.add_argument("--really", action="store_true", help="send it for real")
    p = sub.add_parser("cancel", help="cancel a resting order"); p.add_argument("order_id"); p.add_argument("ticker")
    p.add_argument("--really", action="store_true")
    sub.add_parser("fills", help="the account's fills")
    p = sub.add_parser("settlements", help="the account's settlements"); p.add_argument("--since")
    argv = list(sys.argv[1:] if argv is None else argv)
    prod = "--prod" in argv                      # accepted before or after the subcommand
    a = ap.parse_args([x for x in argv if x != "--prod"])
    if not a.cmd:
        ap.print_help()
        return
    env = "prod" if prod else "demo"
    cfg = edge_common.load_config()
    series = getattr(a, "series", None) or cfg.get("kalshi_series") or "KXEPLGAME"
    really = bool(getattr(a, "really", False))
    if really and env == "prod" and not cfg.get("rehearsal_passed"):
        sys.exit("prod orders are locked until rehearsal_passed is true in projects/edge/config.json")
    try:
        k = Kalshi(env=env, dry_run=not really, allow_prod=really)
    except KalshiError as e:
        sys.exit(str(e))
    try:
        if a.cmd == "check":
            src = edge_common.key_sources()["kalshi_demo" if env == "demo" else "kalshi"]
            print(f"env: {env}   base: {k.base}   dry_run: {k.dry_run}")
            for name, where in src.items():
                print(f"  {name}: {'found in ' + where if where else 'MISSING'}")
            print(f"  key usable: {k.has_key}" + (f"  ({k.key_error})" if not k.has_key else ""))
            st = k.exchange_status()
            print(f"exchange_active: {st['exchange_active']}   trading_active: {st['trading_active']}")
            if k.has_key:
                print(f"balance: ${k.balance()['usd']:.2f}")
        elif a.cmd == "markets":
            ms = k.markets(series)
            print(f"{len(ms)} open markets in {series} ({env})")
            for m in ms:
                print(f"  {m['ticker']:<32} {str(m['yes_sub_title']):<20} yes {_fmt(m['yes_bid'])}/{_fmt(m['yes_ask'])}  "
                      f"vol {int(m['volume'] or 0):,}")
        elif a.cmd == "events":
            evs = k.events(series)
            print(f"{len(evs)} open events in {series} ({env}, {k.base})")
            for e in evs:
                _print_event(e)
        elif a.cmd == "event":
            e = k.event(a.ticker)
            if not e:
                sys.exit(f"no event {a.ticker}")
            _print_event(e)
        elif a.cmd == "book":
            b = k.orderbook(a.ticker, a.depth)
            print(f"{a.ticker} ({env})  yes {_fmt(b['yes_bid'])}/{_fmt(b['yes_ask'])}  no {_fmt(b['no_bid'])}/{_fmt(b['no_ask'])}  "
                  f"yes bid size {_fmt(b['yes_bid_size'], 0)}  yes ask size {_fmt(b['yes_ask_size'], 0)}")
            print("  yes bids:", ", ".join(f"{p:.2f} x {n:,.0f}" for p, n in b["yes"]) or "none")
            print("  no bids: ", ", ".join(f"{p:.2f} x {n:,.0f}" for p, n in b["no"]) or "none")
        elif a.cmd == "order":
            cid = "cli-" + uuid.uuid4().hex[:12]
            o = k.create_order(a.ticker, a.side, a.price, a.count, cid, tif=a.tif)
            print(("DRY RUN: " if o["status"] == "dry" else "") + json.dumps({x: o[x] for x in o if x != "raw"}, indent=1))
            if o["status"] == "dry":
                print(f"written to {edge_common.DRY_RUN_LOG}")
        elif a.cmd == "cancel":
            print(json.dumps(k.cancel(a.order_id, a.ticker), indent=1, default=str))
        elif a.cmd == "fills":
            fs = k.fills()
            print(f"{len(fs)} fills")
            for f in fs:
                print(f"  {f['created']}  {f['ticker']:<32} {f['side']:<3} x{f['count']:<4} yes {_fmt(f['yes_price'])}  "
                      f"fee ${f['fee_usd']:.2f}  {'taker' if f['is_taker'] else 'maker'}")
        elif a.cmd == "settlements":
            ss = k.settlements(min_ts=parse_iso(a.since + "T00:00:00Z") if a.since else None)
            print(f"{len(ss)} settlements")
            for s_ in ss:
                print(f"  {s_['settled_time']}  {s_['ticker']:<32} {s_['market_result']:<3} yes {s_['yes_count']} no {s_['no_count']}  "
                      f"revenue ${s_['revenue_usd']:.2f}  fee ${s_['fee_usd']:.2f}")
    except KalshiError as e:
        sys.exit(f"Kalshi: {e.message}")


if __name__ == "__main__":
    main()
