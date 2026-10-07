"""Unit tests for the three Monarc Edge API clients (2026-10-04): kalshi_api, polymarket_read, api_football, plus
teams.json. No network: every HTTP call goes through a fake session, and the data comes from tests/fixtures/
(kalshi-event.json and kalshi-book.json are live reads from 2026-10-04, poly-event.json a live Gamma read,
football-stats.json hand-built from the documented shape).

The runner calls tests(check) with check(name, ok, detail=""). During the run edge_common.DRY_RUN_LOG, CACHE and
DATA point at a temp folder, so nothing here touches projects/edge/data.
"""
import base64
import copy
import json
import sys
import tempfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import edge_common  # noqa: E402
import kalshi_api  # noqa: E402
import polymarket_read  # noqa: E402
import api_football  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"


class FakeResponse:
    def __init__(self, status, body, headers=None):
        self.status_code = status
        self._body = body
        self.headers = headers or {}
        self.text = json.dumps(body) if body is not None else ""

    def json(self):
        if self._body is None:
            raise ValueError("no body")
        return self._body


class FakeSession:
    """Answers by the first key found in the URL; raises when told to (as a connection error)."""

    def __init__(self, answers=None, fail=False, headers=None):
        self.answers = dict(answers or {})
        self.fail = fail
        self.headers = headers or {}
        self.calls = []

    def request(self, method, url, **kw):
        self.calls.append((method, url, kw))
        if self.fail:
            raise requests.ConnectionError("fake: no network")
        for key, body in self.answers.items():
            if key in url:
                if isinstance(body, tuple):
                    return FakeResponse(body[0], body[1], self.headers)
                return FakeResponse(200, body, self.headers)
        return FakeResponse(404, {"error": {"code": "not_found", "message": f"no fake answer for {url}"}}, self.headers)

    def get(self, url, **kw):
        return self.request("GET", url, **kw)


def tests(check):
    tmp = Path(tempfile.mkdtemp(prefix="edge-clients-"))
    saved = (edge_common.DRY_RUN_LOG, edge_common.CACHE, edge_common.DATA, polymarket_read._session)
    edge_common.DRY_RUN_LOG = tmp / "dry-run.jsonl"
    edge_common.CACHE = tmp / "cache"
    edge_common.DATA = tmp
    try:
        _kalshi(check, tmp)
        _teams(check)
        _poly(check, tmp)
        _football(check, tmp)
    finally:
        edge_common.DRY_RUN_LOG, edge_common.CACHE, edge_common.DATA, polymarket_read._session = saved
        edge_common.set_clock(None)


# ---------------------------------------------------------------- kalshi

def _kalshi(check, tmp):
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = tmp / "test-key.pem"
    pem.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                      serialization.NoEncryption()))
    fake = FakeSession(fail=True)
    k = kalshi_api.Kalshi(env="demo", dry_run=True, key_id="test-key-id", key_path=str(pem), session=fake)
    check("kalshi: PEM loads, has_key", k.has_key, k.key_error or "")
    check("kalshi: base is the demo host", k.base.startswith("https://demo-api.kalshi.co/trade-api/v2"), k.base)

    h = k.sign("GET", "/trade-api/v2/markets?limit=5")
    msg = (h["KALSHI-ACCESS-TIMESTAMP"] + "GET" + "/trade-api/v2/markets").encode("utf-8")
    try:
        key.public_key().verify(base64.b64decode(h["KALSHI-ACCESS-SIGNATURE"]), msg,
                                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=hashes.SHA256().digest_size),
                                hashes.SHA256())
        verified = True
    except InvalidSignature:
        verified = False
    check("kalshi: signature verifies with the public half", verified)
    check("kalshi: the three header names", set(h) == {"KALSHI-ACCESS-KEY", "KALSHI-ACCESS-TIMESTAMP", "KALSHI-ACCESS-SIGNATURE"})
    check("kalshi: timestamp is Unix ms as a string", h["KALSHI-ACCESS-TIMESTAMP"].isdigit() and len(h["KALSHI-ACCESS-TIMESTAMP"]) == 13)
    check("kalshi: signed string has /trade-api/v2 and no query",
          k._last_msg.endswith("/trade-api/v2/markets") and "?" not in k._last_msg, k._last_msg)

    o = k.create_order("KXEPLGAME-26OCT18NFOARS-NFO", "no", 0.77, 26, "cid-1")
    lines = edge_common.DRY_RUN_LOG.read_text(encoding="utf-8").splitlines()
    check("kalshi: dry run writes one line", len(lines) == 1, str(len(lines)))
    check("kalshi: dry run makes zero HTTP calls", not fake.calls, str(len(fake.calls)))
    line = json.loads(lines[0]) if lines else {}
    body = line.get("body") or {}
    check("kalshi: buy No at 0.77 -> side ask, price 0.2300, count 26",
          body.get("side") == "ask" and body.get("price") == "0.2300" and body.get("count") == "26", json.dumps(body))
    check("kalshi: V2 body fields", body.get("time_in_force") == "good_till_canceled"
          and body.get("self_trade_prevention_type") == "taker_at_cross" and body.get("client_order_id") == "cid-1"
          and body.get("post_only") is False and line.get("path") == "/trade-api/v2/portfolio/events/orders")
    check("kalshi: dry log hides the key id and the signature",
          line.get("headers", {}).get("KALSHI-ACCESS-SIGNATURE") == "<signed>" and "test-key-id" not in lines[0])
    check("kalshi: dry order shape", o["status"] == "dry" and o["order_id"].startswith("dry-") and len(o["order_id"]) == 16
          and o["fill_count"] == 0 and o["remaining_count"] == 26 and o["avg_fill"] is None and o["fees_usd"] == 0.0
          and o["client_order_id"] == "cid-1" and o["raw"] == body)
    o2 = k.create_order("KXEPLGAME-26OCT18NFOARS-ARS", "yes", 0.26, 20, "cid-2", expires_at="2026-10-18T18:28:00Z")
    check("kalshi: buy Yes at 0.26 -> side bid, price 0.2600",
          o2["raw"]["side"] == "bid" and o2["raw"]["price"] == "0.2600" and o2["raw"]["count"] == "20")
    check("kalshi: expires_at becomes Unix seconds", o2["raw"].get("expiration_time") == 1792348080, str(o2["raw"].get("expiration_time")))
    c = k.cancel(o["order_id"], "KXEPLGAME-26OCT18NFOARS-NFO")
    check("kalshi: dry cancel logs and makes no call", c["status"] == "dry" and not fake.calls
          and len(edge_common.DRY_RUN_LOG.read_text(encoding="utf-8").splitlines()) == 3)
    for bad in (("maybe", 0.5, 1), ("yes", 1.5, 1), ("yes", 0.5, 0)):
        try:
            kalshi_api.Kalshi.v2_body("T", bad[0], bad[1], bad[2], "x")
            raised = False
        except kalshi_api.KalshiError:
            raised = True
        check(f"kalshi: v2_body refuses {bad}", raised)

    book = json.loads((FIX / "kalshi-book.json").read_text(encoding="utf-8"))
    b = kalshi_api.parse_orderbook(book)
    check("kalshi: book: yes ask = 1 - best no bid", b["yes_ask"] == 0.72 and b["no_ask"] == 0.29
          and b["yes_bid"] == 0.71 and b["no_bid"] == 0.28, json.dumps({x: b[x] for x in b if x not in ("yes", "no")}))
    check("kalshi: book: sizes at the touch (yes ask size = best no bid size)",
          b["yes_bid_size"] == 23.34 and b["yes_ask_size"] == 21179.74)
    check("kalshi: book: levels best first", b["yes"][0][0] == 0.71 and b["yes"][-1][0] == 0.67 and len(b["no"]) == 5)
    e1 = kalshi_api.parse_orderbook({"orderbook_fp": {"yes_dollars": [], "no_dollars": [["0.3000", "10.00"]]}})
    check("kalshi: book: an empty side is None", e1["yes_bid"] is None and e1["no_ask"] is None and e1["yes_ask"] == 0.7)
    e2 = kalshi_api.parse_orderbook({"orderbook": {"yes": [[71, 5]], "no": [[28, 7]]}})
    check("kalshi: book: cents fallback", e2["yes_bid"] == 0.71 and e2["yes_ask"] == 0.72)

    ev = json.loads((FIX / "kalshi-event.json").read_text(encoding="utf-8"))["event"]
    e = kalshi_api.normalize_event(ev)
    check("kalshi: event: three markets, strike date, home and away from the title",
          len(e["markets"]) == 3 and e["strike_date"] == "2026-10-18" and e["home"] == "Nottingham Forest"
          and e["away"] == "Arsenal" and e["home_code"] == "NFO" and e["away_code"] == "ARS", json.dumps({x: e[x] for x in e if x not in ("markets", "raw")}))
    m = [x for x in e["markets"] if x["ticker"].endswith("-ARS")][0]
    check("kalshi: market: dollar strings become floats", m["yes_bid"] == 0.58 and m["yes_ask"] == 0.60
          and m["no_bid"] == 0.40 and m["no_ask"] == 0.42 and m["yes_sub_title"] == "Arsenal" and m["status"] == "active"
          and isinstance(m["volume"], float) and isinstance(m["open_interest"], float) and m["raw"] is ev["markets"][1],
          json.dumps({x: m[x] for x in m if x != "raw"}))
    cm = kalshi_api.normalize_market({"ticker": "X", "yes_bid": 71, "yes_ask": 72, "volume": 5})
    check("kalshi: market: cents fallback", cm["yes_bid"] == 0.71 and cm["yes_ask"] == 0.72 and cm["volume"] == 5.0 and cm["no_bid"] is None)
    check("kalshi: strike_date_of", kalshi_api.strike_date_of("KXEPLGAME-26OCT10ARSLEE") == "2026-10-10"
          and kalshi_api.strike_date_of("NOPE") is None)

    fake3 = FakeSession({"/events": {"events": [ev], "cursor": ""}, "/exchange/status": {"exchange_active": True, "trading_active": False}})
    k3 = kalshi_api.Kalshi(env="demo", dry_run=True, key_id="test-key-id", key_path=str(pem), session=fake3)
    evs = k3.events("KXEPLGAME")
    check("kalshi: events() normalises and stops at an empty cursor", len(evs) == 1 and len(fake3.calls) == 1
          and evs[0]["markets"][0]["ticker"] == "KXEPLGAME-26OCT18NFOARS-NFO")
    sent = fake3.calls[0][2]
    check("kalshi: events() asks for open with nested markets",
          sent["params"].get("series_ticker") == "KXEPLGAME" and sent["params"].get("status") == "open"
          and sent["params"].get("with_nested_markets") == "true" and "KALSHI-ACCESS-SIGNATURE" in sent["headers"])
    st = k3.exchange_status()
    check("kalshi: exchange_status shape", st == {"exchange_active": True, "trading_active": False})

    real_get_secret = kalshi_api.get_secret
    kalshi_api.get_secret = lambda *a, **kw: None
    try:
        fake4 = FakeSession({"/exchange/status": {"exchange_active": True, "exchange_index_statuses": [{"exchange_index": 0, "trading_active": True}]}})
        k4 = kalshi_api.Kalshi(env="demo", session=fake4)
    finally:
        kalshi_api.get_secret = real_get_secret
    check("kalshi: no key: public read works and sends no auth headers",
          not k4.has_key and k4.exchange_status()["trading_active"] is True and "KALSHI-ACCESS-KEY" not in fake4.calls[0][2]["headers"])
    try:
        k4.balance()
        raised = ""
    except kalshi_api.KalshiError as ex:
        raised = ex.message
    check("kalshi: no key: account call raises a clear KalshiError", "KALSHI_DEMO_API_KEY_ID" in raised, raised)

    try:
        kalshi_api.Kalshi(env="prod", dry_run=False, session=fake)
        raised = False
    except kalshi_api.KalshiError:
        raised = True
    check("kalshi: prod + dry_run False without allow_prod raises", raised)
    try:
        kp = kalshi_api.Kalshi(env="prod", dry_run=False, allow_prod=True, key_id="test-key-id", key_path=str(pem), session=fake)
        ok = kp.base.startswith("https://api.elections.kalshi.com/trade-api/v2")
    except kalshi_api.KalshiError:
        ok = False
    check("kalshi: prod with allow_prod builds on the elections host", ok)
    try:
        kalshi_api.Kalshi(env="staging", session=fake)
        raised = False
    except kalshi_api.KalshiError:
        raised = True
    check("kalshi: unknown env raises", raised)

    no = kalshi_api.normalize_order({"order_id": "o1", "client_order_id": "c1", "status": "executed", "fill_count_fp": "26.00",
                                      "remaining_count_fp": "0.00", "taker_fees_dollars": "0.33", "maker_fees_dollars": "0.0000",
                                      "taker_fill_cost_dollars": "5.98"})
    check("kalshi: order normaliser", no["status"] == "executed" and no["fill_count"] == 26 and no["remaining_count"] == 0
          and no["fees_usd"] == 0.33 and no["avg_fill"] == 0.23, json.dumps({x: no[x] for x in no if x != "raw"}))
    cr = kalshi_api.normalize_order({"order_id": "o2", "fill_count": "0", "remaining_count": "20"}, tif="good_till_canceled")
    check("kalshi: create answer without status reads as resting", cr["status"] == "resting" and cr["remaining_count"] == 20)
    fk = kalshi_api.normalize_order({"order_id": "o3", "fill_count": "0", "remaining_count": "20"}, tif="fill_or_kill")
    check("kalshi: unfilled fill_or_kill reads as canceled", fk["status"] == "canceled")

    retry = FakeSession({"/markets/X/orderbook": (429, {"error": "too many requests"})})
    saved_waits = kalshi_api.WAITS_429
    kalshi_api.WAITS_429 = (0.0, 0.0, 0.0)
    try:
        k5 = kalshi_api.Kalshi(env="demo", key_id="test-key-id", key_path=str(pem), session=retry)
        try:
            k5.orderbook("X")
            status = None
        except kalshi_api.KalshiError as ex:
            status = ex.status
    finally:
        kalshi_api.WAITS_429 = saved_waits
    check("kalshi: 429 retried three times then raised", status == 429 and len(retry.calls) == 4, str(len(retry.calls)))


# ---------------------------------------------------------------- teams

def _teams(check):
    teams = edge_common.load_teams()
    check("teams: 20 clubs", len(teams) == 20, str(len(teams)))
    rows = [edge_common.resolve_team(x, teams) for x in ("Nott'm Forest", "NFO", "not", "Nottingham Forest FC")]
    check("teams: Forest's four spellings hit one row", all(r is not None and r is rows[0] for r in rows)
          and rows[0]["name"] == "Nottingham Forest")
    bad = []
    for t in teams:
        for f in ("name", "fd", "kalshi", "poly"):
            if not t.get(f):
                bad.append(f"{t['name']}:{f} empty")
            elif edge_common.resolve_team(t[f], teams) is not t:
                bad.append(f"{t['name']}:{f}={t[f]}")
        for a in t.get("aliases", []):
            if edge_common.resolve_team(a, teams) is not t:
                bad.append(f"{t['name']}:alias={a}")
    check("teams: every name, fd, kalshi, poly and alias resolves to its own row", not bad, ", ".join(bad))
    kalshi_names = ["Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton", "Chelsea", "Coventry", "Crystal Palace",
                    "Everton", "Fulham", "Hull City", "Ipswich Town", "Leeds United", "Liverpool", "Manchester City",
                    "Manchester United", "Newcastle", "Nottingham Forest", "Sunderland", "Tottenham"]
    poly_names = ["Arsenal FC", "Leeds United FC", "Sunderland AFC", "Brighton & Hove Albion FC", "Ipswich Town FC", "Fulham FC",
                  "Aston Villa FC", "Brentford FC", "Chelsea FC", "AFC Bournemouth", "Manchester United FC", "Tottenham Hotspur FC",
                  "Hull City AFC", "Everton FC", "Crystal Palace FC", "Nottingham Forest FC", "Liverpool FC", "Manchester City FC",
                  "Coventry City FC", "Newcastle United FC"]
    fd_names = ["Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton", "Chelsea", "Coventry", "Crystal Palace", "Everton",
                "Fulham", "Hull", "Ipswich", "Leeds", "Liverpool", "Man City", "Man United", "Newcastle", "Nott'm Forest",
                "Sunderland", "Tottenham"]
    for label, names in (("Kalshi yes_sub_title", kalshi_names), ("Polymarket title", poly_names), ("football-data", fd_names)):
        hit = [edge_common.resolve_team(n, teams) for n in names]
        missing = [n for n, r in zip(names, hit) if r is None]
        distinct = len({id(r) for r in hit if r is not None})
        check(f"teams: all 20 {label} names resolve to 20 rows", not missing and distinct == 20, f"missing {missing}, distinct {distinct}")
    check("teams: a stranger resolves to None", edge_common.resolve_team("Wolves", teams) is None
          and edge_common.resolve_team("Tie", teams) is None)
    check("teams: api_id is null until the key is in", all(t.get("api_id") is None for t in teams))


# ---------------------------------------------------------------- polymarket

def _poly(check, tmp):
    raw = json.loads((FIX / "poly-event.json").read_text(encoding="utf-8"))
    matches = polymarket_read.parse_events(raw)
    check("poly: the fixture parses to one match", len(matches) == 1, str(len(matches)))
    if not matches:
        return
    m = matches[0]
    check("poly: names from the title, kickoff from gameStartTime, three markets",
          m["home_name"] == "Everton FC" and m["away_name"] == "Chelsea FC" and m["kickoff_utc"] == "2026-10-17T11:30:00Z"
          and set(m["markets"]) == {"home", "draw", "away"} and m["home_code"] == "eve" and m["away_code"] == "che",
          json.dumps({x: m[x] for x in m if x != "markets"}))
    hm = m["markets"]["home"]
    check("poly: market fields (Yes token, bid, ask, outcome price)", str(hm["token_yes"]).startswith("76319988911719522648949279345019991557414811097934439811060510192358886688263"[:12])
          and hm["best_bid"] == 0.33 and hm["best_ask"] == 0.36 and hm["yes_price"] == 0.345 and hm["type"] == "moneyline",
          json.dumps(hm))
    check("poly: draw market is the -draw slug", m["markets"]["draw"]["slug"].endswith("-draw") and m["markets"]["away"]["slug"].endswith("-che"))
    check("poly: futures and props are not matches",
          polymarket_read.parse_event({"slug": "epl-2027-champion-20260701200428749", "title": "EPL: 2027 Champion", "markets": []}) is None)

    hit = polymarket_read.find_match("Everton", "Chelsea", "2026-10-17T11:30:00Z", matches)
    check("poly: find_match by names and kickoff", hit is m)
    check("poly: find_match accepts fd and Kalshi spellings",
          polymarket_read.find_match("Everton", "CFC", "2026-10-17T11:30:00Z", matches) is m
          and polymarket_read.find_match("Everton FC", "Chelsea FC", "2026-10-17T11:30:00Z", matches) is m)
    check("poly: find_match 5 minutes off still matches", polymarket_read.find_match("Everton", "Chelsea", "2026-10-17T11:35:00Z", matches) is m)
    check("poly: find_match 2 hours off is None", polymarket_read.find_match("Everton", "Chelsea", "2026-10-17T13:30:00Z", matches) is None)
    check("poly: find_match with the sides swapped is None", polymarket_read.find_match("Chelsea", "Everton", "2026-10-17T11:30:00Z", matches) is None)
    check("poly: find_match with a stranger is None", polymarket_read.find_match("Wolves", "Chelsea", "2026-10-17T11:30:00Z", matches) is None)

    clob = FakeSession({"/midpoint": {"mid": "0.5"}})
    polymarket_read._session = clob
    mids = polymarket_read.mids(m)
    check("poly: mids from the CLOB", mids == {"home": 0.5, "draw": 0.5, "away": 0.5, "source": "clob"} and len(clob.calls) == 3, json.dumps(mids))
    polymarket_read.mids(m)
    check("poly: midpoints cached (no second call)", len(clob.calls) == 3, str(len(clob.calls)))
    m2 = copy.deepcopy(m)
    for i, key in enumerate(("home", "draw", "away")):
        m2["markets"][key]["token_yes"] = f"nocache{i}"
    polymarket_read._session = FakeSession(fail=True)
    mids2 = polymarket_read.mids(m2)
    check("poly: CLOB down -> Gamma (bid+ask)/2 and source gamma",
          mids2["source"] == "gamma" and mids2["home"] == 0.345 and mids2["draw"] == 0.255 and mids2["away"] == 0.405
          and polymarket_read.LAST_ERROR, json.dumps(mids2))

    edge_common.set_clock("2026-10-10T12:00:00Z")
    try:
        polymarket_read._session = FakeSession(fail=True)
        out = polymarket_read.list_matches(days=16)
        check("poly: no network -> [] and LAST_ERROR set", out == [] and "ConnectionError" in (polymarket_read.LAST_ERROR or ""), str(polymarket_read.LAST_ERROR))
        check("poly: reachable() is False with no network", polymarket_read.reachable() is False)
        gamma = FakeSession({"/events": raw})
        polymarket_read._session = gamma
        out = polymarket_read.list_matches(days=16)
        check("poly: list_matches parses, filters by kickoff window, asks Gamma by end date",
              len(out) == 1 and out[0]["slug"] == "epl-eve-che-2026-10-17" and polymarket_read.LAST_ERROR is None
              and gamma.calls[0][2]["params"].get("tag_slug") == "epl" and "end_date_min" in gamma.calls[0][2]["params"],
              json.dumps(gamma.calls[0][2]["params"] if gamma.calls else {}))
        polymarket_read.list_matches(days=16)
        check("poly: listing cached 5 minutes (one Gamma call)", len(gamma.calls) == 1, str(len(gamma.calls)))
        check("poly: a listing outside the window is dropped", polymarket_read.list_matches(days=3) == [] and len(gamma.calls) == 2)
        check("poly: reachable() is True", polymarket_read.reachable() is True)
    finally:
        edge_common.set_clock(None)
        polymarket_read._session = None


# ---------------------------------------------------------------- api-football

def _football(check, tmp):
    stats = json.loads((FIX / "football-stats.json").read_text(encoding="utf-8"))
    fake = FakeSession({"/fixtures/statistics": stats, "/teams": {"get": "teams", "errors": [], "results": 0, "paging": {"current": 1, "total": 1}, "response": []}},
                       headers={"x-ratelimit-requests-remaining": "7498", "X-RateLimit-Remaining": "299"})
    f = api_football.Football(key="test", cache=tmp / "fb", budget=2, session=fake, budget_file=tmp / "budget.json")
    st = f.fixture_stats(1)
    check("football: 'Ball Possession': '55%' -> 55.0", st.get(40, {}).get("possession") == 55.0 and st.get(50, {}).get("possession") == 45.0,
          json.dumps(st.get(40)))
    check("football: counts, xg, null red cards -> 0", st[40]["shots_on_target"] == 6 and st[40]["shots"] == 14 and st[40]["corners"] == 7
          and st[40]["xg"] == 1.87 and st[40]["red"] == 0 and st[40]["saves"] == 2 and st[40]["passes"] == 512
          and st[40]["passes_accurate"] == 440 and st[40]["goals_prevented"] is None and st[40]["team"] == "Liverpool")
    check("football: one live call, key header sent, quota read", f.calls == 1 and len(fake.calls) == 1
          and fake.calls[0][2]["headers"].get("x-apisports-key") == "test" and f.remaining == 7498 and f.minute_remaining == 299)
    f.fixture_stats(1)
    check("football: cache hit makes no call", len(fake.calls) == 1, str(len(fake.calls)))
    check("football: budget file counts the day", json.loads((tmp / "budget.json").read_text())["used"] == 1)
    f.get("/teams", 1, league=39, season=2026)
    try:
        f.get("/teams", 1, league=39, season=2025)
        raised = False
    except api_football.FootballBudget:
        raised = True
    check("football: a live call past the budget raises FootballBudget", raised and len(fake.calls) == 2, str(len(fake.calls)))
    check("football: cached data still serves past the budget", f.fixture_stats(1) == st and f.get("/teams", 1, league=39, season=2026)["response"] == [])
    check("football: FootballBudget is a FootballError", issubclass(api_football.FootballBudget, api_football.FootballError))

    g = api_football.Football(key="", cache=tmp / "fb", budget=5, session=fake, budget_file=tmp / "b2.json")
    try:
        g.get("/injuries", 6, league=39, season=2026)
        msg = ""
    except api_football.FootballBudget:
        msg = "budget?"
    except api_football.FootballError as ex:
        msg = str(ex)
    check("football: no key -> FootballError('API_FOOTBALL_KEY not set')", msg == "API_FOOTBALL_KEY not set", msg)
    check("football: no key but cached -> serves", g.fixture_stats(1) == st)

    # lineups: nothing until both teams are in, then kept for good
    def team(tid, n):
        return {"team": {"id": tid, "name": f"T{tid}"}, "formation": "4-3-3", "coach": {"name": "C"},
                "startXI": [{"player": {"id": tid * 100 + i, "name": f"P{i}", "number": i, "pos": "M", "grid": "1:1"}} for i in range(n)],
                "substitutes": [{"player": {"id": tid * 100 + 50, "name": "S", "number": 50, "pos": "D", "grid": None}}]}
    lu_fake = FakeSession({"/fixtures/lineups": {"errors": [], "response": [team(50, 11)]}})
    h = api_football.Football(key="test", cache=tmp / "fb3", budget=10, session=lu_fake, budget_file=tmp / "b3.json")
    check("football: lineups None with one team", h.lineups(7, home_id=40) is None and len(lu_fake.calls) == 1)
    check("football: incomplete lineups are not served from cache", h.lineups(7, home_id=40) is None and len(lu_fake.calls) == 2)
    lu_fake.answers["/fixtures/lineups"] = {"errors": [], "response": [team(50, 11), team(40, 11)]}
    lu = h.lineups(7, home_id=40)
    check("football: complete lineups, home picked by home_id", lu and lu["home"]["team_id"] == 40 and lu["away"]["team_id"] == 50
          and len(lu["home"]["start_xi"]) == 11 and lu["home"]["start_xi"][0]["name"] == "P0" and lu["home"]["subs"][0]["name"] == "S"
          and lu["home"]["formation"] == "4-3-3", json.dumps(lu)[:200])
    h.lineups(7, home_id=40)
    check("football: complete lineups served from cache", len(lu_fake.calls) == 3, str(len(lu_fake.calls)))

    fx = api_football.normalize_fixture({"fixture": {"id": 1, "date": "2026-10-18T15:30:00+00:00", "status": {"short": "NS", "elapsed": None},
                                                     "venue": {"id": 1, "name": "City Ground", "city": "Nottingham"}},
                                         "league": {"id": 39, "season": 2026, "round": "Regular Season - 8"},
                                         "teams": {"home": {"id": 65, "name": "Nottingham Forest"}, "away": {"id": 42, "name": "Arsenal"}},
                                         "goals": {"home": None, "away": None}})
    check("football: fixture normaliser", fx == {"id": 1, "kickoff_utc": "2026-10-18T15:30:00Z", "status": "NS", "elapsed": None,
                                                  "round": "Regular Season - 8", "season": 2026, "home_id": 65, "home": "Nottingham Forest",
                                                  "away_id": 42, "away": "Arsenal", "home_goals": None, "away_goals": None, "venue": "City Ground"}, json.dumps(fx))
    err_fake = FakeSession({"/odds": {"get": "odds", "errors": {"token": "Error/Missing application key."}, "response": []}})
    e = api_football.Football(key="bad", cache=tmp / "fb4", budget=10, session=err_fake, budget_file=tmp / "b4.json")
    try:
        e.odds(1)
        msg = ""
    except api_football.FootballError as ex:
        msg = str(ex)
    check("football: an errors dict in a 200 body raises FootballError", "token" in msg and not list((tmp / "fb4").glob("*.json")) if (tmp / "fb4").exists() else "token" in msg, msg)
    odds_fake = FakeSession({"/odds": {"errors": [], "response": [{"fixture": {"id": 1}, "bookmakers": [
        {"id": 8, "name": "Bet365", "bets": [{"id": 1, "name": "Match Winner", "values": [{"value": "Home", "odd": "2.10"}, {"value": "Draw", "odd": "3.40"}, {"value": "Away", "odd": "3.60"}]}]},
        {"id": 9, "name": "Half", "bets": [{"id": 1, "name": "Match Winner", "values": [{"value": "Home", "odd": "2.00"}]}]}]}]}})
    o = api_football.Football(key="test", cache=tmp / "fb5", budget=10, session=odds_fake, budget_file=tmp / "b5.json").odds(1)
    check("football: odds parser keeps complete Match Winner lines", o == [{"bookmaker": "Bet365", "home": 2.1, "draw": 3.4, "away": 3.6}], json.dumps(o))
