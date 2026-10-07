"""Monarc Edge loop (2026-10-04): fixtures, snapshots, cards, orders, fills, settlement, halts.

Plain functions over the SQLite db and the clients handed in on a Ctx; the server and the tests call them with the
real clients or the fakes in projects/edge/tests/fakes.py. One pass is tick(ctx): sync the Kalshi listing when due
(every 6 h), do each fixture's window work (snapshot, lineups, price, decide, cancel), then fills, listing checks,
settlement and the auto pass. Nothing raises out of tick; errors land in kv sync.last_error and the log.

The rules it keeps (brainstorms/2026-10-03-betting-market-agent.md): the gap is measured against the ask after the
taker fee; green at 7 points; the stake is 6% of the match day's opening bankroll at the floor rising to 8% at 17;
a market must be busy (10,000 contracts, 2-cent spread, depth for our count); one position a match, the largest green
side (Q18), the other green sides wait as `watching`; every card waits for a click in approve mode; Claude writes
words only after the numbers are set, and only when a card first turns ready or its side or gap band moves.

Without API-Football (no key) fixtures come from the Kalshi events alone: names from the event title, kickoff from
the event's strike_date or its markets' expiration minus the match length, flagged "kickoff from Kalshi"; lineups
are "not available", so decide_without_lineups is treated as true and the card carries "no lineup feed".

A dry-run Kalshi order (status "dry") is treated as a paper fill at the limit price with the taker fee, so paper
cards settle and count toward the gate.

  python scripts/edge_cards.py tick       one pass with the real clients from config
  python scripts/edge_cards.py sync       just the listing sync
"""
import hashlib
import json
import re
import sys
import threading
import time
import traceback
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edge_common as ec  # noqa: E402
import edge_ledger  # noqa: E402

MATCH_LENGTH = timedelta(hours=3)          # kickoff to the market's expected expiration (checked 2026-10-04 on 19
                                           # events against Polymarket's kickoffs: Kalshi expects to settle 3 h after)
SETTLE_AFTER = timedelta(hours=2)          # look for a settlement this long after kickoff
SYNC_EVERY = 6 * 3600
LISTING_EVERY = 600                        # seconds between delisting sweeps inside tick
GONE_STATES = ("closed", "settled", "determined", "paused", "finalized")
STICKY_FLAGS = ("lineups posted", "no lineups", "no lineup feed", "kickoff from Kalshi")
STATE_BLOCK = re.compile(r"\b(location|state|jurisdiction|restricted|eligible|geo\w*)\b", re.I)
_VS = re.compile(r"\s+(?:vs\.?|v\.?|at|@|-)\s+", re.I)


class Ctx:
    """Everything a pass needs. Any client may be None (then that part is skipped) or a fake."""

    def __init__(self, cfg, kalshi=None, football=None, poly=None, model=None, reason=None, on_change=None,
                 quotes=None):
        self.cfg = cfg
        self.kalshi = kalshi          # orders and the account: the configured exchange (demo until the rehearsal)
        self.quotes = quotes          # public prices: always the production exchange (demo's books are empty)
        self.football = football
        self.poly = poly
        self.model = model
        self.reason = reason
        self.on_change = on_change
        self.lock = threading.RLock()
        self.busy = False

    @property
    def reads(self):
        """The client market data comes from: the production quotes client when there is one, else the order client
        (the fakes answer both)."""
        return self.quotes if self.quotes is not None else self.kalshi

    def changed(self):
        if self.on_change:
            try:
                self.on_change()
            except Exception:  # noqa: BLE001
                pass


# ---------------------------------------------------------------- small helpers

def halted():
    return bool(ec.kv_get("halted"))


def set_error(text):
    ec.kv_set("sync.last_error", str(text)[:400] if text else None)
    if text:
        ec.log("edge:", str(text)[:400])


def _priced(x):
    """A usable ask: present and strictly between 0 and 1. An empty book shows 0 or 1, which is no price."""
    try:
        return x is not None and 0.0 < float(x) < 1.0
    except (TypeError, ValueError):
        return False


def is_kalshi_error(e):
    return type(e).__name__ == "KalshiError" or (hasattr(e, "status") and hasattr(e, "body"))


def looks_like_state_block(e):
    text = " ".join(str(getattr(e, k, "") or "") for k in ("message", "body")) + " " + str(e)
    return bool(STATE_BLOCK.search(text))


def no_football_feed(ctx):
    """True when lineups cannot come from anywhere: no client, or the client raises for want of a key."""
    if ctx.football is None:
        return True
    return bool(ec.kv_get("football.no_feed"))


def _flags(row):
    try:
        return list(json.loads(row.get("flags_json") or "[]"))
    except (ValueError, TypeError):
        return []


def _with_flag(flags, flag):
    if flag and flag not in flags:
        flags.append(flag)
    return flags


def mins_until(kickoff, at):
    return (ec.parse_iso(kickoff) - at).total_seconds() / 60.0


# ---------------------------------------------------------------- fixtures

def get_fixture(fid):
    r = ec.db().execute("SELECT * FROM fixtures WHERE id=?", (fid,)).fetchone()
    return dict(r) if r else None


def fixture_by_event(event_ticker):
    r = ec.db().execute("SELECT * FROM fixtures WHERE kalshi_event=?", (event_ticker,)).fetchone()
    return dict(r) if r else None


def fixtures_between(frm, to):
    return ec.rows(ec.db().execute("SELECT * FROM fixtures WHERE kickoff_utc >= ? AND kickoff_utc <= ? "
                                   "ORDER BY kickoff_utc, id", (ec.iso(frm), ec.iso(to))))


def upsert_fixture(f):
    c = ec.db()
    cols = ("id", "season", "round", "kickoff_utc", "home_id", "home", "away_id", "away", "status", "home_goals",
            "away_goals", "result", "kalshi_event", "poly_slug", "linked", "updated")
    vals = [f.get(k) for k in cols]
    sets = ", ".join(f"{k}=excluded.{k}" for k in cols if k != "id")
    c.execute(f"INSERT INTO fixtures ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))}) "
              f"ON CONFLICT(id) DO UPDATE SET {sets}", vals)
    c.commit()


def fixture_json(f):
    meta = ec.kv_get(f"fixture_meta.{f['id']}") or {}
    return {"id": f["id"], "home": f["home"], "away": f["away"], "kickoff_utc": f["kickoff_utc"],
            "kalshi_event": f["kalshi_event"], "poly_slug": f["poly_slug"], "linked": bool(f.get("linked")),
            "status": f.get("status"), "unlinked_names": meta.get("unlinked") or [],
            "kickoff_source": meta.get("kickoff_source")}


def split_title(title):
    """'Nottingham Forest vs Arsenal' -> ('Nottingham Forest', 'Arsenal'); None when the shape is unknown."""
    parts = _VS.split(str(title or "").strip(), maxsplit=1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return parts[0].strip(), parts[1].strip()


def event_codes(event_ticker):
    """'KXEPLGAME-26OCT18NFOARS' -> 'NFOARS' (the part after the 7-character date)."""
    tail = str(event_ticker or "").split("-", 1)[-1]
    return tail[7:] if len(tail) > 7 else ""


def _slim(market):
    return {k: v for k, v in (market or {}).items() if k != "raw"}


def parse_event(ev):
    """The three markets by outcome, the names and the kickoff from one Kalshi event. None when unusable."""
    ticker = ev.get("event_ticker") or ""
    names = split_title(ev.get("title"))
    if not ticker or not names:
        return None
    home_name, away_name = names
    codes = event_codes(ticker)
    markets, tickers = {}, {}
    for m in ev.get("markets") or []:
        mt = m.get("ticker") or ""
        suffix = mt.rsplit("-", 1)[-1].upper()
        sub = str(m.get("yes_sub_title") or "").strip()
        out = None
        if suffix == "TIE" or sub.lower() in ("tie", "draw"):
            out = "draw"
        elif sub and ec.norm(sub) == ec.norm(home_name):
            out = "home"
        elif sub and ec.norm(sub) == ec.norm(away_name):
            out = "away"
        elif codes and suffix and codes.startswith(suffix):
            out = "home"
        elif codes and suffix and codes.endswith(suffix):
            out = "away"
        if out and out not in markets:
            markets[out] = _slim(m)
            tickers[out] = mt
    kickoff, source = None, "kalshi"
    ends = []
    for m in markets.values():
        if m.get("expected_expiration_time"):
            try:
                ends.append(ec.parse_iso(m["expected_expiration_time"]))
            except ValueError:
                pass
    if ends:
        kickoff = min(ends) - MATCH_LENGTH        # Kalshi expects to settle 3 h after kickoff
    if kickoff is None and ev.get("strike_date"):
        try:
            kickoff = ec.parse_iso(ev["strike_date"])   # a date only: midnight UTC, replaced when Polymarket links
        except ValueError:
            kickoff = None
    if kickoff is None:
        for m in markets.values():
            if m.get("close_time"):
                try:
                    kickoff = ec.parse_iso(m["close_time"]) - MATCH_LENGTH
                    break
                except ValueError:
                    pass
    rules = next((m.get("rules_primary") for m in markets.values() if m.get("rules_primary")), None)
    return {"event_ticker": ticker, "home_name": home_name, "away_name": away_name,
            "kickoff_utc": ec.iso(kickoff) if kickoff else None, "kickoff_source": source,
            "markets": markets, "tickers": tickers, "rules": rules,
            "home_code": codes[:3] if codes else None, "away_code": codes[3:] if codes else None}


def football_fixtures(ctx, now, look_days):
    """Upcoming league fixtures from API-Football, or None when there is no feed (then kv football.no_feed is set)."""
    if ctx.football is None:
        return None
    cfg = ctx.cfg
    try:
        rows = ctx.football.fixtures(league=int(cfg["league_id"]), season=int(cfg["season"]),
                                     frm=ec.iso(now - timedelta(days=1))[:10],
                                     to=ec.iso(now + timedelta(days=look_days))[:10]) or []
        ec.kv_set("football.no_feed", False)
        return rows
    except Exception as e:  # noqa: BLE001
        name = type(e).__name__
        ec.kv_set("football.no_feed", True)
        if "key" in str(e).lower():
            set_error("API-Football: no key yet. Kickoffs come from Kalshi and Polymarket; lineups are not read.")
        else:
            set_error(f"football fixtures: {name}: {e}")
        return None


def match_football(rows, home, away, home_raw, away_raw, kickoff, teams):
    """The API-Football fixture for a Kalshi event: same two teams (canonical, raw or api id), kickoff within 36 h."""
    want_h = {ec.norm(home), ec.norm(home_raw)}
    want_a = {ec.norm(away), ec.norm(away_raw)}
    k0 = ec.parse_iso(kickoff) if kickoff else None
    best = None
    for r in rows:
        th = ec.team_by_api_id(r.get("home_id"), teams) or ec.resolve_team(r.get("home"), teams)
        ta = ec.team_by_api_id(r.get("away_id"), teams) or ec.resolve_team(r.get("away"), teams)
        names_h = {ec.norm(r.get("home"))} | ({ec.norm(th["name"])} if th else set())
        names_a = {ec.norm(r.get("away"))} | ({ec.norm(ta["name"])} if ta else set())
        if not (names_h & want_h and names_a & want_a):
            continue
        if k0 and r.get("kickoff_utc"):
            gap = abs((ec.parse_iso(r["kickoff_utc"]) - k0).total_seconds())
            if gap > 36 * 3600:
                continue
            if best is None or gap < best[0]:
                best = (gap, r)
        elif best is None:
            best = (0, r)
    return best[1] if best else None


def poly_matches(ctx, look_days):
    if ctx.poly is None or not (ctx.cfg.get("polymarket") or {}).get("on", True):
        return None
    try:
        if not ctx.poly.reachable():
            ec.kv_set("sync.poly_ok", False)
            return None
        rows = ctx.poly.list_matches(days=look_days) or []
        ec.kv_set("sync.poly_ok", True)
        return rows
    except Exception as e:  # noqa: BLE001
        ec.kv_set("sync.poly_ok", False)
        set_error(f"polymarket: {type(e).__name__}: {e}")
        return None


def stable_id(event_ticker):
    return -(int(hashlib.sha1(event_ticker.encode()).hexdigest()[:8], 16) or 1)


def sync_fixtures(ctx):
    """Kalshi's open events for the series -> fixtures (ids from API-Football when it answers), the three market
    tickers per event in kv, the Polymarket link, and the sync stamps. Two syncs in a row with no open market while
    fixtures sit in the next 7 days -> halt sports_gone."""
    cfg = ctx.cfg
    now = ec.now()
    look = int(cfg["window"]["listing_lookahead_days"])
    did = {"events": 0, "open_markets": 0, "fixtures": 0}
    if ctx.reads is None:
        set_error("no Kalshi client")
        return did
    try:
        events = ctx.reads.events(cfg["kalshi_series"], status="open") or []
    except Exception as e:  # noqa: BLE001
        set_error(f"kalshi events: {type(e).__name__}: {e}")
        return did
    teams = ec.load_teams()
    fb = football_fixtures(ctx, now, look)
    pm = poly_matches(ctx, look)
    open_markets, unlinked = 0, []
    for ev in events:
        p = parse_event(ev)
        if not p or not p["kickoff_utc"]:
            continue
        did["events"] += 1
        open_markets += sum(1 for m in p["markets"].values() if str(m.get("status") or "open").lower() in ("open", "active"))
        th, ta = ec.resolve_team(p["home_name"], teams), ec.resolve_team(p["away_name"], teams)
        home = th["name"] if th else p["home_name"]
        away = ta["name"] if ta else p["away_name"]
        names = [n for n, t in ((p["home_name"], th), (p["away_name"], ta)) if not t]
        kickoff, source = p["kickoff_utc"], "kalshi"
        existing = fixture_by_event(p["event_ticker"])
        fid = existing["id"] if existing else None
        fbrow = match_football(fb, home, away, p["home_name"], p["away_name"], kickoff, teams) if fb else None
        if fbrow:
            if fid is None or fid < 0:
                fid = int(fbrow["id"])
            kickoff, source = fbrow.get("kickoff_utc") or kickoff, "api-football"
        if fid is None:
            fid = stable_id(p["event_ticker"])
        if existing and existing["id"] != fid:          # the football id arrived after a hashed one: move the rows
            c = ec.db()
            for t in ("cards", "snapshots", "model_runs", "features"):
                c.execute(f"UPDATE {t} SET fixture_id=? WHERE fixture_id=?", (fid, existing["id"]))
            c.execute("DELETE FROM fixtures WHERE id=?", (existing["id"],))
            c.commit()
        slug = None
        if pm is not None:
            try:
                if source == "kalshi":       # no football feed: Kalshi gives the day and a 3 h margin, Polymarket the kickoff
                    try:
                        m = ctx.poly.find_match(home, away, kickoff, pm, tolerance_s=36 * 3600)
                    except TypeError:
                        m = ctx.poly.find_match(home, away, kickoff, pm)
                    if m and m.get("kickoff_utc"):
                        kickoff, source = m["kickoff_utc"], "polymarket"
                else:
                    m = ctx.poly.find_match(home, away, kickoff, pm)
                if m:
                    slug = m.get("slug")
                    ec.kv_set(f"poly_match.{slug}", m)
            except Exception as e:  # noqa: BLE001
                set_error(f"polymarket match: {type(e).__name__}: {e}")
        upsert_fixture({"id": fid, "season": int(cfg["season"]), "round": (fbrow or {}).get("round"),
                        "kickoff_utc": kickoff, "home_id": (fbrow or {}).get("home_id") or (th or {}).get("api_id"),
                        "home": home, "away_id": (fbrow or {}).get("away_id") or (ta or {}).get("api_id"), "away": away,
                        "status": (fbrow or {}).get("status") or "NS", "home_goals": (fbrow or {}).get("home_goals"),
                        "away_goals": (fbrow or {}).get("away_goals"), "result": None,
                        "kalshi_event": p["event_ticker"], "poly_slug": slug,
                        "linked": 1 if (fid > 0 and slug) else 0, "updated": ec.iso(now)})
        ec.kv_set(f"event.{p['event_ticker']}", {"fixture_id": fid, "tickers": p["tickers"], "markets": p["markets"],
                                                 "rules": p["rules"], "home_code": p["home_code"],
                                                 "away_code": p["away_code"], "synced": ec.iso(now)})
        ec.kv_set(f"fixture_meta.{fid}", {"kickoff_source": source, "unlinked": names, "event": p["event_ticker"]})
        if names:
            unlinked.append({"fixture_id": fid, "kalshi_event": p["event_ticker"], "poly_slug": slug, "names": names})
        did["fixtures"] += 1
    did["open_markets"] = open_markets
    ec.kv_set("sync.fixtures_at", ec.iso(now))
    ec.kv_set("sync.markets_at", ec.iso(now))
    ec.kv_set("sync.open_markets", open_markets)
    ec.kv_set("sync.unlinked", unlinked)
    if pm is None and ctx.poly is None:
        ec.kv_set("sync.poly_ok", None)
    upcoming = len(fixtures_between(now, now + timedelta(days=7)))
    if open_markets == 0 and upcoming > 0:
        n = int(ec.kv_get("sync.empty_syncs") or 0) + 1
        ec.kv_set("sync.empty_syncs", n)
        if n >= 2 and not halted():
            halt(ctx, "sports_gone", f"{n} syncs in a row with no open {cfg['kalshi_series']} market while "
                                     f"{upcoming} fixtures sit in the next 7 days")
    else:
        ec.kv_set("sync.empty_syncs", 0)
    ctx.changed()
    return did


# ---------------------------------------------------------------- snapshots

def poly_mids_for(ctx, fixture):
    slug = fixture.get("poly_slug")
    if not slug or ctx.poly is None or not (ctx.cfg.get("polymarket") or {}).get("on", True):
        return {}
    m = ec.kv_get(f"poly_match.{slug}")
    if not m:
        return {}
    try:
        mids = ctx.poly.mids(m) or {}
        ec.kv_set("sync.poly_ok", True)
        return {k: mids.get(k) for k in ec.OUTCOMES}
    except Exception as e:  # noqa: BLE001
        ec.kv_set("sync.poly_ok", False)
        set_error(f"polymarket mids: {type(e).__name__}: {e}")
        return {}


def snapshot(ctx, fixture):
    """One snapshots row per market: the fresh market fields, the top of the book, the Polymarket mid."""
    ev = ec.kv_get(f"event.{fixture.get('kalshi_event')}") or {}
    tickers, cached = ev.get("tickers") or {}, ev.get("markets") or {}
    poly = poly_mids_for(ctx, fixture)
    now = ec.now()
    out = []
    c = ec.db()
    for outcome in ec.OUTCOMES:
        t = tickers.get(outcome)
        if not t:
            continue
        m = dict(cached.get(outcome) or {})
        if ctx.reads is not None:
            try:
                fresh = ctx.reads.market(t)
                if fresh:
                    m.update(_slim(fresh))
                else:
                    m["status"] = "gone"
            except Exception as e:  # noqa: BLE001
                set_error(f"kalshi market {t}: {type(e).__name__}: {e}")
            try:
                ob = ctx.reads.orderbook(t) or {}
            except Exception as e:  # noqa: BLE001
                ob = {}
                set_error(f"kalshi orderbook {t}: {type(e).__name__}: {e}")
            for k in ("yes_bid", "yes_ask", "no_bid", "no_ask", "yes_ask_size", "yes_bid_size"):
                if ob.get(k) is not None:
                    m[k] = ob[k]
        snap = {"fixture_id": fixture["id"], "ticker": t, "outcome": outcome, "as_of": ec.iso(now),
                "yes_bid": m.get("yes_bid"), "yes_ask": m.get("yes_ask"), "no_bid": m.get("no_bid"),
                "no_ask": m.get("no_ask"), "yes_ask_size": m.get("yes_ask_size"), "yes_bid_size": m.get("yes_bid_size"),
                "volume": m.get("volume"), "oi": m.get("open_interest"), "status": m.get("status"),
                "poly_mid": poly.get(outcome), "poly_bid": None, "poly_ask": None}
        c.execute("INSERT INTO snapshots (fixture_id, ticker, outcome, as_of, yes_bid, yes_ask, no_bid, no_ask, "
                  "yes_ask_size, yes_bid_size, volume, oi, status, poly_mid, poly_bid, poly_ask) "
                  "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (snap["fixture_id"], t, outcome, snap["as_of"], snap["yes_bid"], snap["yes_ask"], snap["no_bid"],
                   snap["no_ask"], snap["yes_ask_size"], snap["yes_bid_size"], snap["volume"], snap["oi"],
                   snap["status"], snap["poly_mid"], None, None))
        out.append(snap)
    c.commit()
    return out


def closing_fair(ticker, kickoff):
    """The Yes mid of the last snapshot within 5 minutes before kickoff, else the last one before kickoff."""
    k = ec.parse_iso(kickoff)
    c = ec.db()
    r = c.execute("SELECT yes_bid, yes_ask FROM snapshots WHERE ticker=? AND as_of >= ? AND as_of <= ? "
                  "ORDER BY as_of DESC LIMIT 1", (ticker, ec.iso(k - timedelta(minutes=5)), ec.iso(k))).fetchone()
    if not r:
        r = c.execute("SELECT yes_bid, yes_ask FROM snapshots WHERE ticker=? AND as_of <= ? "
                      "ORDER BY as_of DESC LIMIT 1", (ticker, ec.iso(k))).fetchone()
    if not r:
        return None
    yb, ya = r["yes_bid"], r["yes_ask"]
    if yb is not None and ya is not None:
        return (float(yb) + float(ya)) / 2
    return float(ya) if ya is not None else (float(yb) if yb is not None else None)


# ---------------------------------------------------------------- cards

CARD_COLS = ("id", "fixture_id", "event_ticker", "ticker", "outcome", "side", "created", "decided_at", "expires_at",
             "model_version", "model_p", "p_home", "p_draw", "p_away", "market_yes_bid", "market_yes_ask",
             "market_price", "market_mid", "poly_mid", "fee_points", "break_even", "gap_points", "color", "stake_usd",
             "count", "limit_price", "band", "hours_band", "mode", "state", "approved_at", "passed_at", "order_id",
             "client_order_id", "fill_count", "avg_fill", "fees_paid", "result", "pnl_usd", "clv_points",
             "closing_fair", "reasoning", "flags_json", "lineups_seen", "busy_ok", "busy_reason", "sources_json",
             "paper", "updated")
CARD_SQL = ("SELECT c.*, f.home, f.away, f.kickoff_utc FROM cards c LEFT JOIN fixtures f ON f.id = c.fixture_id")


def get_card(card_id):
    r = ec.db().execute(CARD_SQL + " WHERE c.id=?", (card_id,)).fetchone()
    return dict(r) if r else None


def cards_where(where="1=1", params=()):
    return ec.rows(ec.db().execute(CARD_SQL + f" WHERE {where} ORDER BY f.kickoff_utc, c.fixture_id, c.outcome", params))


def cards_of_fixture(fid):
    return cards_where("c.fixture_id=?", (fid,))


def insert_card(d):
    c = ec.db()
    cols = [k for k in CARD_COLS if k in d]
    c.execute(f"INSERT INTO cards ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", [d[k] for k in cols])
    c.commit()


def update_card(card_id, **fields):
    fields["updated"] = ec.iso(ec.now())
    c = ec.db()
    c.execute(f"UPDATE cards SET {', '.join(k + '=?' for k in fields)} WHERE id=?", [*fields.values(), card_id])
    c.commit()


def card_json(r, halted_now=None):
    """The Card shape in API.md."""
    if halted_now is None:
        halted_now = halted()
    kickoff = r.get("kickoff_utc") or r.get("expires_at")
    future = bool(kickoff) and ec.parse_iso(kickoff) > ec.now()
    outcome = r.get("outcome")
    name = r.get("home") if outcome == "home" else r.get("away") if outcome == "away" else "Tie"
    out = {k: r.get(k) for k in CARD_COLS if k not in ("flags_json", "sources_json")}
    out.update({"outcome_name": name, "home": r.get("home"), "away": r.get("away"), "kickoff_utc": kickoff,
                "flags": _flags(r), "sources": json.loads(r.get("sources_json") or "[]"),
                "can_approve": r.get("state") == "ready" and not halted_now and future,
                "lineups_seen": int(r.get("lineups_seen") or 0), "busy_ok": int(r.get("busy_ok") or 0),
                "paper": int(r.get("paper") or 0), "fill_count": int(r.get("fill_count") or 0),
                "fees_paid": float(r.get("fees_paid") or 0)})
    return out


def gap_band(gap):
    return None if gap is None else int(gap // 5) * 5


def poly_reading(poly_mid, model_p, market_mid, side):
    if poly_mid is None:
        return None, "no Polymarket price"
    ours = model_p if side == "yes" else 1 - model_p
    theirs = poly_mid if side == "yes" else 1 - poly_mid
    cents = round(100 * poly_mid)
    if abs(theirs - ours) <= 0.02:
        return "agrees", f"Polymarket mid {cents} cents sides with us"
    if market_mid is not None and abs(poly_mid - market_mid) <= 0.02:
        return "disagrees", f"Polymarket mid {cents} cents sides with Kalshi"
    return "neutral", f"Polymarket mid {cents} cents sits between us and Kalshi"


def reason_context(ctx, fixture, card, pred, snap, poly_text, lineups, no_feed):
    ev = ec.kv_get(f"event.{fixture.get('kalshi_event')}") or {}
    if lineups:
        lu = "lineups posted"
    elif no_feed:
        lu = "no lineup feed"
    else:
        lu = "lineups not posted yet"
    # the bet in a sixth grader's words, and the money as risk and win (Jonathan, 2026-10-04: "a 6th grader view")
    name, side, draw = card["outcome_name"], card["side"], card["outcome"] == "draw"
    p = float(card["model_p"]) if card.get("model_p") is not None else None
    if side == "no":
        bet_words = "it does not end in a draw" if draw else f"{name} does not win"
        p_side = None if p is None else 1.0 - p
    else:
        bet_words = "it ends in a draw" if draw else f"{name} wins"
        p_side = p
    count = int(card.get("count") or 0)
    price = float(card.get("market_price") or 0)
    rate = float((ctx.cfg.get("fees") or {}).get("taker_rate", 0.07))
    fee = ec.kalshi_fee_usd(count, price, rate) if count and 0 < price < 1 else 0.0
    return {"home": fixture["home"], "away": fixture["away"], "kickoff_utc": fixture["kickoff_utc"],
            "outcome_name": card["outcome_name"], "side": card["side"],
            "bet_words": bet_words, "p_side": p_side, "price_side": price if count else card.get("market_price"),
            "risk_usd": round(count * price + fee, 2) if count else 0.0,
            "win_usd": round(count * (1.0 - price) - fee, 2) if count else 0.0,
            "paper": bool(getattr(ctx.kalshi, "dry_run", False)),
            "p_home": pred.get("p_home"), "p_draw": pred.get("p_draw"), "p_away": pred.get("p_away"),
            "ratings": pred.get("ratings"), "contributions": (pred.get("contributions") or [])[:5],
            "yes_ask": snap.get("yes_ask"), "no_ask": snap.get("no_ask"), "fee_points": card["fee_points"],
            "break_even": card["break_even"], "gap_points": card["gap_points"], "stake_usd": card["stake_usd"],
            "count": card["count"], "poly_mid": card["poly_mid"], "poly_reading": poly_text, "lineups": lu,
            "missing_regulars": (lineups or {}).get("missing_regulars") if isinstance(lineups, dict) else None,
            "rule": ev.get("rules")}


def price_cards(ctx, fixture, snaps, lineups=None, lineups_seen=False, no_feed=False):
    """The model once, then one card per market. Cards in watching/ready/no_edge are updated in place; a card past
    its decision (or a fixture past kickoff) is never re-priced. Returns the fixture's cards."""
    cfg = ctx.cfg
    now = ec.now()
    kickoff = ec.parse_iso(fixture["kickoff_utc"])
    if kickoff <= now or not snaps:
        return cards_of_fixture(fixture["id"])
    if ctx.model is None:
        set_error("no model service: cards not priced")
        return cards_of_fixture(fixture["id"])
    try:
        pred = ctx.model.predict_fixture(fixture["home"], fixture["away"], fixture["kickoff_utc"], lineups=lineups)
    except Exception as e:  # noqa: BLE001
        set_error(f"model {fixture['home']} v {fixture['away']}: {type(e).__name__}: {e}")
        return cards_of_fixture(fixture["id"])
    if not pred:
        return cards_of_fixture(fixture["id"])
    c = ec.db()
    c.execute("INSERT INTO model_runs (fixture_id, feature_id, as_of, model_version, p_home, p_draw, p_away, contrib_json) "
              "VALUES (?,?,?,?,?,?,?,?)", (fixture["id"], None, ec.iso(now), pred.get("version"), pred["p_home"],
                                           pred["p_draw"], pred["p_away"], ec.json_dumps(pred.get("contributions") or [])))
    c.commit()
    probs = {"home": float(pred["p_home"]), "draw": float(pred["p_draw"]), "away": float(pred["p_away"])}
    bankroll = edge_ledger.period_bankroll(fixture["kickoff_utc"][:10])
    meta = ec.kv_get(f"fixture_meta.{fixture['id']}") or {}
    existing = {r["outcome"]: r for r in cards_of_fixture(fixture["id"])}
    taken = next((r["outcome"] for r in existing.values()
                  if r["state"] in ec.LIVE_ORDER_STATES + ec.POSITION_STATES + ("settled",)), None)
    is_halted = halted()
    hrs = ec.hours_until(kickoff, now)
    rate = float(cfg["fees"]["taker_rate"])
    floor = float(cfg["gap_floor_points"])
    pm = cfg.get("polymarket") or {}
    paper = 1 if getattr(ctx.kalshi, "dry_run", False) else 0
    sources = list(pred.get("sources") or []) + ["kalshi"]
    if lineups:
        sources.append("api-football lineups")
    computed = []
    for snap in snaps:
        o = snap["outcome"]
        old = existing.get(o)
        if old and old["state"] not in ec.OPEN_STATES:
            continue
        p = probs[o]
        flags = [f for f in _flags(old or {}) if f in STICKY_FLAGS]
        if meta.get("kickoff_source") == "kalshi":
            _with_flag(flags, "kickoff from Kalshi")
        if no_feed:
            _with_flag(flags, "no lineup feed")
        if lineups_seen:
            _with_flag(flags, "lineups posted")
        yb, ya, na = snap.get("yes_bid"), snap.get("yes_ask"), snap.get("no_ask")
        mid = (float(yb) + float(ya)) / 2 if (yb is not None and ya is not None) else None
        d = {"id": f"{fixture['kalshi_event']}-{snap['ticker'].rsplit('-', 1)[-1].upper()}",
             "fixture_id": fixture["id"], "event_ticker": fixture["kalshi_event"], "ticker": snap["ticker"],
             "outcome": o, "expires_at": fixture["kickoff_utc"], "model_version": pred.get("version"),
             "model_p": p, "p_home": probs["home"], "p_draw": probs["draw"], "p_away": probs["away"],
             "market_yes_bid": yb, "market_yes_ask": ya, "market_mid": mid, "poly_mid": snap.get("poly_mid"),
             "band": ec.band_of(p * 100, int(cfg["gate"]["band_width_points"])), "hours_band": ec.hours_band(hrs),
             "lineups_seen": 1 if lineups_seen else 0, "paper": paper, "sources_json": ec.json_dumps(sources),
             "outcome_name": fixture["home"] if o == "home" else fixture["away"] if o == "away" else "Tie"}
        if not _priced(ya) or not _priced(na):
            d.update({"side": None, "market_price": None, "fee_points": None, "break_even": None, "gap_points": None,
                      "color": None, "stake_usd": 0.0, "count": 0, "limit_price": None, "busy_ok": 0,
                      "busy_reason": "no two-sided book", "green_ok": False})
            _with_flag(flags, "no price")
        else:
            gs = ec.gap_and_side(p, float(ya), float(na), rate)
            color = ec.color_of(gs["gap"], floor, float(cfg.get("big_gap_points") or 0) or None)
            if color == "yellow":
                _with_flag(flags, "big gap: the model may be wrong, check the news")
            stake = ec.stake_for_gap(gs["gap"], bankroll, cfg)
            count = ec.contracts_for(stake, gs["price"])
            busy_ok, busy_reason = ec.busy_check(snap, count, gs["side"], cfg["busy"])
            disagree = (snap.get("poly_mid") is not None and mid is not None
                        and abs(float(snap["poly_mid"]) - mid) > float(pm.get("disagree_points", 5.0)) / 100.0)
            if disagree:
                _with_flag(flags, "second witness disagrees")
            d.update({"side": gs["side"], "market_price": gs["price"], "limit_price": gs["price"],
                      "fee_points": round(ec.fee_points_per_contract(gs["price"], rate), 3),
                      "break_even": round(gs["break_even"], 4), "gap_points": round(gs["gap"], 3), "color": color,
                      "stake_usd": stake, "count": count, "busy_ok": 1 if busy_ok else 0, "busy_reason": busy_reason,
                      "green_ok": color in ("green", "yellow") and busy_ok and not (disagree and pm.get("block_when_disagree"))})
        d["_flags"], d["_old"], d["_snap"] = flags, old, snap
        computed.append(d)
    cands = [d for d in computed if d["green_ok"]]
    best = max(cands, key=lambda d: d["gap_points"]) if cands else None
    for d in computed:
        flags, old, snap = d.pop("_flags"), d.pop("_old"), d.pop("_snap")
        green_ok = d.pop("green_ok")
        if green_ok and d is best and not taken and not is_halted:
            state = "ready"
        elif green_ok:
            state = "watching"
            if is_halted:
                _with_flag(flags, "halted")
            elif taken:
                _with_flag(flags, f"position already on {taken}")
            else:
                _with_flag(flags, f"larger edge on {best['outcome']}")
        elif d["color"] in ("amber", "red") or (d["color"] in ("green", "yellow") and not d["busy_ok"]) or (
                d["color"] in ("green", "yellow") and "second witness disagrees" in flags):
            state = "no_edge"
        else:
            state = "watching"
        d["state"] = state
        d["flags_json"] = json.dumps(flags)
        d["updated"] = ec.iso(now)
        reasoning = old.get("reasoning") if old else None
        if state == "ready":
            key = f"reason.{d['id']}"
            last = ec.kv_get(key) or {}
            if ctx.reason is not None and (last.get("side") != d["side"] or last.get("gap_band") != gap_band(d["gap_points"])
                                           or not reasoning):
                _, poly_text = poly_reading(d["poly_mid"], d["model_p"], d["market_mid"], d["side"])
                model_p_before = d["model_p"]
                try:
                    r = ctx.reason.write(dict(d), reason_context(ctx, fixture, d, pred, snap, poly_text, lineups, no_feed)) or {}
                except Exception as e:  # noqa: BLE001
                    r = {"reasoning": None, "flags": [f"reasoning failed: {type(e).__name__}"]}
                d["model_p"] = model_p_before                      # the words never move the number
                reasoning = str(r.get("reasoning") or reasoning or "")
                for f in (r.get("flags") or [])[:3]:
                    _with_flag(flags, str(f)[:80])
                d["flags_json"] = json.dumps(flags)
                ec.kv_set(key, {"side": d["side"], "gap_band": gap_band(d["gap_points"]), "at": ec.iso(now)})
        d["reasoning"] = reasoning
        d.pop("outcome_name", None)
        if old:
            if old["state"] in ec.OPEN_STATES and state not in ec.OPEN_STATES:
                d["decided_at"] = ec.iso(now)
            update_card(d["id"], **{k: v for k, v in d.items() if k not in ("id", "created", "fixture_id", "event_ticker",
                                                                          "ticker", "outcome", "updated")})
        else:
            d["created"] = ec.iso(now)
            d["mode"] = cfg.get("mode", "approve")
            d["fill_count"], d["fees_paid"] = 0, 0.0
            insert_card(d)
    ctx.changed()
    return cards_of_fixture(fixture["id"])


# ---------------------------------------------------------------- the window

def _both_xis(lu):
    if not isinstance(lu, dict):
        return False
    return all(((lu.get(k) or {}).get("start_xi") or []) for k in ("home", "away"))


def close_window(ctx, fixture):
    """At cancel_before_kickoff_minutes: resting orders cancelled (unfilled, or partial when some filled), untouched
    open cards expired."""
    n = 0
    for card in cards_of_fixture(fixture["id"]):
        st = card["state"]
        if st in ("placed", "partial") and card.get("order_id"):
            cancel_order(ctx, card)
            n += 1
        elif st in ec.OPEN_STATES or st == "halted":
            flags = _with_flag(_flags(card), "expired at kickoff")
            update_card(card["id"], state="expired", decided_at=ec.iso(ec.now()), flags_json=json.dumps(flags))
            n += 1
    return n


def cancel_order(ctx, card):
    """Cancel a resting order. Returns the card's new state."""
    try:
        if ctx.kalshi is not None:
            ctx.kalshi.cancel(card["order_id"], card["ticker"])
    except Exception as e:  # noqa: BLE001
        set_error(f"cancel {card['order_id']}: {type(e).__name__}: {e}")
    c = ec.db()
    c.execute("UPDATE orders SET status='canceled', updated=? WHERE order_id=?", (ec.iso(ec.now()), card["order_id"]))
    c.commit()
    state = "partial" if int(card.get("fill_count") or 0) > 0 else "unfilled"
    update_card(card["id"], state=state, decided_at=card.get("decided_at") or ec.iso(ec.now()))
    ctx.changed()
    return state


def decide_window(ctx, fixture, at=None):
    """The schedule from config for one fixture at time `at`: a snapshot every snapshot_minutes until
    lineup_from_minutes before kickoff and every lineup_poll_minutes after; lineups polled in that window and the
    cards re-priced when both XIs post; no_edge "no lineups" at decide_by_minutes without them; everything closed at
    cancel_before_kickoff_minutes. Snapshots keep going to kickoff so the closing fair exists for CLV."""
    at = at or ec.now()
    w = ctx.cfg["window"]
    fid = fixture["id"]
    key = f"window.{fid}"
    st = ec.kv_get(key) or {}
    mins = mins_until(fixture["kickoff_utc"], at)
    did = []
    if mins <= float(w["cancel_before_kickoff_minutes"]):
        if not st.get("closed"):
            if mins > 0:
                snapshot(ctx, fixture)            # the last price before kickoff: the CLV closing fair
                st["last_snapshot"] = ec.iso(at)
            n = close_window(ctx, fixture)
            st["closed"] = True
            ec.kv_set(key, st)
            did.append(f"closed {fid} ({n} cards)")
        return did
    in_lineup = mins <= float(w["lineup_from_minutes"])
    cadence = float(w["lineup_poll_minutes"] if in_lineup else w["snapshot_minutes"])
    last = ec.parse_iso(st["last_snapshot"]) if st.get("last_snapshot") else None
    if last is not None and (at - last).total_seconds() < cadence * 60 - 1:
        return did
    no_feed = no_football_feed(ctx) or fid < 0
    lineups = st.get("lineups") if st.get("lineups_seen") else None
    if in_lineup and not st.get("lineups_seen") and not no_feed:
        try:
            lu = ctx.football.lineups(fid)
            if _both_xis(lu):
                st["lineups_seen"] = True
                st["lineups"] = lineups = lu
                did.append(f"lineups {fid}")
        except Exception as e:  # noqa: BLE001
            st["lineup_error"] = f"{type(e).__name__}: {e}"[:200]
            if type(e).__name__ == "FootballError" and "key" in str(e).lower():
                ec.kv_set("football.no_feed", True)
                no_feed = True
    snaps = snapshot(ctx, fixture)
    st["last_snapshot"] = ec.iso(at)
    did.append(f"snapshot {fid}")
    decide_without = bool(w["decide_without_lineups"]) or no_feed
    if mins <= float(w["decide_by_minutes"]) and not st.get("lineups_seen") and not decide_without:
        if not st.get("decided"):
            for card in cards_of_fixture(fid):
                if card["state"] in ec.OPEN_STATES:
                    flags = _with_flag(_flags(card), "no lineups")
                    update_card(card["id"], state="no_edge", decided_at=ec.iso(at), flags_json=json.dumps(flags))
            st["decided"] = True
            did.append(f"no lineups {fid}")
            ctx.changed()
    elif not st.get("decided"):
        price_cards(ctx, fixture, snaps, lineups=lineups, lineups_seen=bool(st.get("lineups_seen")), no_feed=no_feed)
        did.append(f"priced {fid}")
    ec.kv_set(key, st)
    return did


# ---------------------------------------------------------------- orders and fills

def _record_fills(card, order_id, fill_count, avg_fill, fees_usd, is_taker=1):
    """Fills, ledger rows (fill = minus count x price, fee = minus fee) and the card's running totals, from the
    order's totals. Returns the new fill_count."""
    old_n = int(card.get("fill_count") or 0)
    new_n = int(fill_count or 0)
    if new_n <= old_n:
        return old_n
    old_avg = float(card.get("avg_fill") or 0)
    avg = float(avg_fill if avg_fill is not None else (card.get("limit_price") or 0))
    delta = new_n - old_n
    price = (new_n * avg - old_n * old_avg) / delta
    paid = float(card.get("fees_paid") or 0)
    total_fee = float(fees_usd) if fees_usd is not None else paid + ec.kalshi_fee_usd(delta, price)
    fee = round(max(0.0, total_fee - paid), 2)
    now = ec.iso(ec.now())
    c = ec.db()
    c.execute("INSERT OR REPLACE INTO fills (id, order_id, card_id, ticker, count, yes_price, is_taker, fee_usd, created) "
              "VALUES (?,?,?,?,?,?,?,?,?)",
              (f"{order_id}-{new_n}", order_id, card["id"], card["ticker"], delta,
               price if card.get("side") == "yes" else round(1 - price, 4), is_taker, fee, now))
    c.commit()
    edge_ledger.add("fill", -round(delta * price, 2), card["id"], f"{delta} x {card['side']} at {price:.2f}")
    if fee:
        edge_ledger.add("fee", -fee, card["id"], "taker fee")
    update_card(card["id"], fill_count=new_n, avg_fill=round(avg, 4), fees_paid=round(paid + fee, 2))
    card["fill_count"], card["avg_fill"], card["fees_paid"] = new_n, round(avg, 4), round(paid + fee, 2)
    return new_n


def apply_order(ctx, card, o):
    """The card's state from an order reply (placed, partial, filled, unfilled). A dry-run order fills at once."""
    status = str(o.get("status") or "")
    count = int(card.get("count") or 0)
    fc = int(o.get("fill_count") or 0)
    avg, fees = o.get("avg_fill"), o.get("fees_usd")
    flags = _flags(card)
    if status == "dry":
        fc, avg, fees = count, float(card["limit_price"]), ec.kalshi_fee_usd(count, float(card["limit_price"]))
        _with_flag(flags, "paper fill at the ask")
    _record_fills(card, o.get("order_id") or card.get("order_id"), fc, avg, fees)
    if fc >= count and count:
        state = "filled"
    elif fc > 0:
        state = "partial"
    elif status == "canceled":
        state = "unfilled"
    else:
        state = "placed"
    c = ec.db()
    c.execute("UPDATE orders SET status=?, updated=?, raw_json=? WHERE order_id=?",
              (status or state, ec.iso(ec.now()), ec.json_dumps(o.get("raw") or o), card.get("order_id")))
    c.commit()
    update_card(card["id"], state=state, flags_json=json.dumps(flags),
                decided_at=card.get("decided_at") or ec.iso(ec.now()))
    ctx.changed()
    return state


def approve(ctx, card_id, by="click"):
    """Re-price from a fresh book, then place (or dry-run) the order. Returns (card, []) or (None, errors)."""
    with ctx.lock:
        cfg = ctx.cfg
        card = get_card(card_id)
        if not card:
            return None, ["No such card."]
        if halted():
            return None, ["A halt is on. Clear it first."]
        if card["state"] != "ready":
            return None, [f"This card is {card['state']}, not ready."]
        now = ec.now()
        kickoff = ec.parse_iso(card["kickoff_utc"] or card["expires_at"])
        if kickoff <= now:
            return None, ["Kickoff has passed."]
        other = next((r for r in cards_of_fixture(card["fixture_id"])
                      if r["id"] != card_id and r["state"] in ec.LIVE_ORDER_STATES + ec.POSITION_STATES), None)
        if other:
            return None, [f"A position is already on {other['outcome']} for this match."]
        if ctx.kalshi is None or ctx.reads is None:
            return None, ["No Kalshi client."]
        try:
            m = ctx.reads.market(card["ticker"]) or {}
            ob = ctx.reads.orderbook(card["ticker"]) or {}
        except Exception as e:  # noqa: BLE001
            return None, [f"Kalshi did not answer: {type(e).__name__}: {e}"]
        snap = {**_slim(m), **{k: v for k, v in ob.items() if v is not None and not isinstance(v, list)}}
        ya, na = snap.get("yes_ask"), snap.get("no_ask")
        if not _priced(ya) or not _priced(na):
            update_card(card_id, state="no_edge", busy_ok=0, busy_reason="no two-sided book", decided_at=ec.iso(now))
            ctx.changed()
            return None, ["No two-sided book right now."]
        rate = float(cfg["fees"]["taker_rate"])
        gs = ec.gap_and_side(float(card["model_p"]), float(ya), float(na), rate)
        color = ec.color_of(gs["gap"], float(cfg["gap_floor_points"]), float(cfg.get("big_gap_points") or 0) or None)
        bankroll = edge_ledger.period_bankroll((card["kickoff_utc"] or card["expires_at"])[:10])
        stake = ec.stake_for_gap(gs["gap"], bankroll, cfg)
        count = ec.contracts_for(stake, gs["price"])
        busy_ok, busy_reason = ec.busy_check(snap, count, gs["side"], cfg["busy"])
        yb = snap.get("yes_bid")
        fields = dict(side=gs["side"], market_yes_bid=yb, market_yes_ask=ya, market_price=gs["price"],
                      market_mid=(float(yb) + float(ya)) / 2 if yb is not None else None, limit_price=gs["price"],
                      fee_points=round(ec.fee_points_per_contract(gs["price"], rate), 3),
                      break_even=round(gs["break_even"], 4), gap_points=round(gs["gap"], 3), color=color,
                      stake_usd=stake, count=count, busy_ok=1 if busy_ok else 0, busy_reason=busy_reason)
        if color not in ("green", "yellow") or not busy_ok:
            errors = []
            if color not in ("green", "yellow"):
                errors.append(f"The gap is now {gs['gap']:.1f} points at {round(100 * gs['price'])} cents "
                              f"(floor {float(cfg['gap_floor_points']):g}).")
            if not busy_ok:
                errors.append(f"Busy check failed: {busy_reason}.")
            update_card(card_id, state="no_edge", decided_at=ec.iso(now), **fields)
            ctx.changed()
            return None, errors
        attempt = ec.db().execute("SELECT COUNT(*) AS n FROM orders WHERE card_id=?", (card_id,)).fetchone()["n"] + 1
        coid = f"edge-{card_id}-{attempt}"
        expires = kickoff - timedelta(minutes=float(cfg["window"]["cancel_before_kickoff_minutes"]))
        paper = 1 if getattr(ctx.kalshi, "dry_run", False) else 0
        update_card(card_id, state="approved", approved_at=ec.iso(now), mode=by if by in ("auto", "paper") else "approve",
                    paper=paper, client_order_id=coid, **fields)
        ctx.busy = True
        try:
            o = ctx.kalshi.create_order(card["ticker"], gs["side"], gs["price"], count, coid, expires_at=ec.iso(expires))
        except Exception as e:  # noqa: BLE001
            body = str(getattr(e, "body", "") or "")
            msg = f"{type(e).__name__}: {getattr(e, 'message', None) or e}"
            if is_kalshi_error(e) and looks_like_state_block(e):
                update_card(card_id, state="halted", flags_json=json.dumps(_with_flag(_flags(card), "order refused: state block")))
                halt(ctx, "state_block", (body or msg)[:2000])
                return None, [f"Kalshi refused the order: {msg}. Halted."]
            update_card(card_id, state="error", decided_at=ec.iso(now),
                        flags_json=json.dumps(_with_flag(_flags(card), f"order refused: {msg}"[:120])))
            ctx.changed()
            return None, [f"Order refused: {msg}"]
        finally:
            ctx.busy = False
        o = dict(o or {})
        oid = str(o.get("order_id") or coid)
        c = ec.db()
        c.execute("INSERT OR REPLACE INTO orders (order_id, card_id, client_order_id, ticker, side, price, count, tif, "
                  "expires_at, status, created, updated, raw_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (oid, card_id, coid, card["ticker"], gs["side"], gs["price"], count, "good_till_canceled",
                   ec.iso(expires), o.get("status"), ec.iso(now), ec.iso(now), ec.json_dumps(o.get("raw") or o)))
        c.commit()
        update_card(card_id, order_id=oid, state="placed")
        card = get_card(card_id)
        apply_order(ctx, card, o)
        return get_card(card_id), []


def check_fills(ctx):
    """Poll resting orders; new fills become fills and ledger rows."""
    n = 0
    if ctx.kalshi is None:
        return n
    for card in cards_where("c.state IN ('placed', 'partial') AND c.order_id IS NOT NULL"):
        try:
            o = ctx.kalshi.order(card["order_id"])
        except Exception as e:  # noqa: BLE001
            set_error(f"order {card['order_id']}: {type(e).__name__}: {e}")
            continue
        if not o:
            continue
        before = (card["state"], int(card.get("fill_count") or 0))
        apply_order(ctx, card, dict(o))
        after = get_card(card["id"])
        if (after["state"], int(after.get("fill_count") or 0)) != before:
            n += 1
    return n


def check_listing(ctx, force=True):
    """A market gone (404) or closed, settled, determined or paused before kickoff: cancel any resting order and
    mark the card delisted. Inside tick this runs every LISTING_EVERY seconds."""
    if ctx.reads is None:
        return 0
    now = ec.now()
    last = ec.kv_get("listing.checked_at")
    if not force and last and (now - ec.parse_iso(last)).total_seconds() < LISTING_EVERY:
        return 0
    ec.kv_set("listing.checked_at", ec.iso(now))
    cards = [c for c in cards_where("c.state IN ('watching', 'ready', 'no_edge', 'placed', 'partial')")
             if ec.parse_iso(c["kickoff_utc"] or c["expires_at"]) > now]
    gone_tickers, seen = set(), {}
    for card in cards:
        t = card["ticker"]
        if t not in seen:
            try:
                m = ctx.reads.market(t)
                seen[t] = (m or {}).get("status") if m else None
                if m is None or str(seen[t] or "").lower() in GONE_STATES:
                    gone_tickers.add(t)
            except Exception as e:  # noqa: BLE001
                set_error(f"listing {t}: {type(e).__name__}: {e}")
                seen[t] = "error"
    n = 0
    for card in cards:
        if card["ticker"] not in gone_tickers:
            continue
        if card["state"] in ("placed", "partial") and card.get("order_id"):
            cancel_order(ctx, card)
        status = seen.get(card["ticker"])
        flags = _with_flag(_flags(card), "delisted by Kalshi" if status is None else f"market {status} before kickoff")
        update_card(card["id"], state="delisted", decided_at=ec.iso(now), flags_json=json.dumps(flags))
        n += 1
    if n:
        ctx.changed()
    return n


def market_settlement(ctx, ticker):
    """A settlement read from the market itself once Kalshi has decided it: {"market_result": "yes"|"no", ...}.
    Paper cards (dry-run fills) never reach the account's settlement list, so this is how they settle; a real card
    falls back to it when the account list has no row yet. None while the market is still open."""
    if ctx.reads is None:
        return None
    try:
        m = ctx.reads.market(ticker)
    except Exception as e:  # noqa: BLE001
        set_error(f"market {ticker}: {type(e).__name__}: {e}")
        return None
    if not m:
        return None
    raw = m.get("raw") or {}
    res = str(m.get("result") or raw.get("result") or "").lower()
    if res not in ("yes", "no"):
        return None
    return {"ticker": ticker, "market_result": res, "yes_count": None, "no_count": None, "revenue_usd": None,
            "fee_usd": None, "settled_time": raw.get("settlement_ts") or raw.get("expiration_time") or m.get("close_time"),
            "source": "market"}


def settle(ctx):
    """Cards holding contracts, 2 h past kickoff: the Kalshi settlement (the account's row for a real fill, the
    market's own result for a paper fill), the pnl, the ledger rows, the CLV."""
    if ctx.kalshi is None and ctx.reads is None:
        return 0
    now = ec.now()
    done = 0
    for card in cards_where("c.state IN ('filled', 'partial') AND c.fill_count > 0"):
        kickoff = ec.parse_iso(card["kickoff_utc"] or card["expires_at"])
        if now < kickoff + SETTLE_AFTER:
            continue
        paper = int(card.get("paper") or 0) == 1 or str(card.get("order_id") or "").startswith("dry-")
        s = None
        if not paper and ctx.kalshi is not None and getattr(ctx.kalshi, "has_key", True):
            try:
                rows = ctx.kalshi.settlements(ticker=card["ticker"]) or []
            except Exception as e:  # noqa: BLE001
                set_error(f"settlements {card['ticker']}: {type(e).__name__}: {e}")
                rows = []
            s = next((r for r in rows if r.get("ticker") == card["ticker"]), None)
        if not s or s.get("market_result") not in ("yes", "no"):
            s = market_settlement(ctx, card["ticker"])
        if not s or s.get("market_result") not in ("yes", "no"):
            continue
        result = s["market_result"]
        n, a, f = int(card["fill_count"]), float(card["avg_fill"] or 0), float(card.get("fees_paid") or 0)
        win = card["side"] == result
        pnl = n * (1 - a) - f if win else -n * a - f
        payout = float(n) if win else 0.0
        adjust = 0.0
        rev = s.get("revenue_usd")
        if rev is not None and abs(float(rev) - payout) > 0.01:
            diff = round(float(rev) - payout, 2)
            edge_ledger.add("adjust", diff, card["id"], f"Kalshi revenue ${float(rev):.2f} against expected ${payout:.2f}")
            adjust += diff
        sfee = float(s.get("fee_usd") or 0)
        if abs(sfee) > 0.01:
            edge_ledger.add("adjust", -sfee, card["id"], f"settlement fee ${sfee:.2f} not in the model")
            adjust -= sfee
        edge_ledger.add("settlement", payout, card["id"], f"settled {result}, {'won' if win else 'lost'}")
        fair_yes = closing_fair(card["ticker"], card["kickoff_utc"] or card["expires_at"])
        fair = None if fair_yes is None else (fair_yes if card["side"] == "yes" else 1 - fair_yes)
        clv = None if fair is None or card.get("break_even") is None else round(100 * (fair - float(card["break_even"])), 3)
        c = ec.db()
        c.execute("INSERT OR REPLACE INTO settlements (ticker, card_id, market_result, yes_count, no_count, revenue_usd, "
                  "fee_usd, settled_time, raw_json) VALUES (?,?,?,?,?,?,?,?,?)",
                  (card["ticker"], card["id"], result, s.get("yes_count"), s.get("no_count"), rev, s.get("fee_usd"),
                   s.get("settled_time") or ec.iso(now), ec.json_dumps(s)))
        c.commit()
        update_card(card["id"], state="settled", result=result, pnl_usd=round(pnl + adjust, 2), clv_points=clv,
                    closing_fair=None if fair is None else round(fair, 4))
        done += 1
    if done:
        ctx.changed()
        edge_ledger.drawdown_check(ctx)
    return done


def auto_pass(ctx):
    """Auto mode: approve every ready card whose band is green in the gate and whose window is allowed."""
    cfg = ctx.cfg
    if cfg.get("mode") != "auto" or halted() or not edge_ledger.drawdown_allows(cfg):
        return 0
    g = edge_ledger.gate(cfg)
    if not g["passed"]:
        return 0
    lights = {b["band"]: b["light"] for b in g["lights"]["calibration"]["bands"]}
    aw = cfg.get("auto_windows") or {}
    clv = edge_ledger.clv_of(edge_ledger.settled_cards())
    by_hours = {b["band"]: b for b in clv["by_hours"]}
    lineup_from_h = float(cfg["window"]["lineup_from_minutes"]) / 60.0
    n = 0
    now = ec.now()
    for card in cards_where("c.state='ready'"):
        if card.get("color") == "yellow":          # a big gap is a warning: live auto never takes it, Jonathan may
            continue
        if lights.get(card["band"]) != "green":
            continue
        hrs = ec.hours_until(card["kickoff_utc"] or card["expires_at"], now)
        ok = False
        if aw.get("lineup_hour", True) and (int(card.get("lineups_seen") or 0) or hrs < lineup_from_h):
            ok = True
        if not ok and aw.get("clv_proven_bands", True):
            b = by_hours.get(card["hours_band"])
            if b and b["n"] >= int(aw.get("min_band_cards", 30)) and b["mean"] > 0:
                ok = True
        if not ok:
            continue
        placed, errors = approve(ctx, card["id"], by="auto")
        if placed:
            n += 1
        elif errors:
            ec.log("auto:", card["id"], "; ".join(errors))
        if halted():
            break
    return n


# ---------------------------------------------------------------- halts

def halt(ctx, reason, detail):
    """A halts row, mode forced to approve (saved), every ready card -> halted, kv halted."""
    now = ec.iso(ec.now())
    c = ec.db()
    c.execute("INSERT INTO halts (ts, reason, detail) VALUES (?,?,?)", (now, reason, str(detail or "")[:2000]))
    c.execute("UPDATE cards SET state='halted', updated=? WHERE state='ready'", (now,))
    c.commit()
    ec.kv_set("halted", True)
    if ctx.cfg.get("mode") != "approve":
        ctx.cfg["mode"] = "approve"
        try:
            ec.save_config(ctx.cfg)
        except Exception as e:  # noqa: BLE001
            set_error(f"save config after halt: {e}")
    ec.log("HALT", reason, str(detail)[:200])
    ctx.changed()


def clear_halt(ctx):
    now = ec.iso(ec.now())
    c = ec.db()
    c.execute("UPDATE halts SET cleared_at=? WHERE cleared_at IS NULL", (now,))
    c.execute("UPDATE cards SET state='watching', updated=? WHERE state='halted' AND expires_at > ?", (now, now))
    c.commit()
    ec.kv_set("halted", False)
    ec.kv_set("sync.empty_syncs", 0)
    ctx.changed()


def halts():
    return ec.rows(ec.db().execute("SELECT * FROM halts ORDER BY id DESC LIMIT 50"))


def paper_pass(ctx):
    """Paper mode (dry_run on and paper_auto on): every ready card is paper-filled at the ask by itself, so the record
    builds without a click (Jonathan, 2026-10-04: "run paper on an account"). Nothing leaves the machine. Once dry_run
    is off this does nothing and approve mode means his click."""
    cfg = ctx.cfg
    if not cfg.get("dry_run") or not cfg.get("paper_auto", True) or halted():
        return 0
    if not getattr(ctx.kalshi, "dry_run", False):
        return 0
    n = 0
    for card in cards_where("c.state='ready'"):
        placed, _errors = approve(ctx, card["id"], by="paper")
        if placed:
            n += 1
    return n


def context_from_card(ctx, card):
    """The note's context rebuilt from a stored card (for a bet that has no note yet)."""
    fixture = {"home": card.get("home"), "away": card.get("away"), "kickoff_utc": card.get("kickoff_utc"),
               "kalshi_event": card.get("event_ticker")}
    contribs = []
    try:
        r = ec.db().execute("SELECT contrib_json FROM model_runs WHERE fixture_id=? ORDER BY id DESC LIMIT 1",
                            (card.get("fixture_id"),)).fetchone()
        if r and r["contrib_json"]:
            contribs = json.loads(r["contrib_json"]) or []
    except Exception:  # noqa: BLE001
        contribs = []
    pred = {"p_home": card.get("p_home"), "p_draw": card.get("p_draw"), "p_away": card.get("p_away"),
            "contributions": contribs}
    yb = card.get("market_yes_bid")
    snap = {"yes_ask": card.get("market_yes_ask"), "no_ask": None if yb is None else round(1.0 - float(yb), 4)}
    _, poly_text = poly_reading(card.get("poly_mid"), card.get("model_p"), card.get("market_mid"), card.get("side"))
    flags = _flags(card)
    lineups = {"missing_regulars": []} if "lineups posted" in flags else None
    return reason_context(ctx, fixture, card, pred, snap, poly_text, lineups, "no lineup feed" in flags)


def backfill_notes(ctx):
    """A card holding a bet with no note (filled before the note was written, or the notes were cleared for a rewrite)
    gets one, once. The number is never touched."""
    if ctx.reason is None:
        return 0
    n = 0
    for card in cards_where("c.state IN ('approved', 'placed', 'partial', 'filled') AND (c.reasoning IS NULL OR c.reasoning = '')"):
        card = dict(card)
        card["outcome_name"] = card["home"] if card["outcome"] == "home" else card["away"] if card["outcome"] == "away" else "Tie"
        try:
            r = ctx.reason.write(card, context_from_card(ctx, card)) or {}
        except Exception as e:  # noqa: BLE001
            set_error(f"note for {card['id']}: {type(e).__name__}: {e}")
            r = {}
        text = str(r.get("reasoning") or "")
        if text:
            update_card(card["id"], reasoning=text)
            n += 1
    if n:
        ctx.changed()
    return n


ACCOUNT_EVERY = 300        # seconds between reads of the Kalshi account (balance, positions)


def read_account(ctx):
    """The account behind the configured exchange, for the page: balance and open positions, every 5 minutes when a
    key is accepted. kv "account" is None with no key."""
    k = ctx.kalshi
    if k is None or not getattr(k, "has_key", False):
        if ec.kv_get("account") is not None:
            ec.kv_set("account", None)
        return 0
    env = getattr(k, "env", None)
    last = ec.kv_get("account") or {}
    now = ec.now()
    if (last.get("read_at") and last.get("env") == env
            and (now - ec.parse_iso(last["read_at"])).total_seconds() < ACCOUNT_EVERY):
        return 0
    try:
        b = k.balance()
        pos = k.positions()
        ec.kv_set("account", {"env": env, "balance_usd": float(b.get("usd") or 0), "positions": len(pos or []),
                              "read_at": ec.iso(now), "error": None})
    except Exception as e:  # noqa: BLE001
        ec.kv_set("account", {"env": env, "balance_usd": None, "positions": None, "read_at": ec.iso(now),
                              "error": f"{type(e).__name__}: {str(e)[:80]}"})
    return 1


# ---------------------------------------------------------------- the pass

def tick(ctx, force_sync=False):
    """One pass. Never raises."""
    t0 = time.time()
    did = []
    with ctx.lock:
        try:
            edge_ledger.init_bankroll(ctx.cfg)
            now = ec.now()
            last = ec.kv_get("sync.fixtures_at")
            if force_sync or not last or (now - ec.parse_iso(last)).total_seconds() >= SYNC_EVERY:
                r = sync_fixtures(ctx)
                did.append(f"sync: {r['events']} events, {r['open_markets']} open markets")
            look = int(ctx.cfg["window"]["listing_lookahead_days"])
            for f in fixtures_between(now - timedelta(hours=3), now + timedelta(days=look)):
                try:
                    did += decide_window(ctx, f, now)
                except Exception as e:  # noqa: BLE001
                    traceback.print_exc()
                    set_error(f"window {f['id']}: {type(e).__name__}: {e}")
            for name, fn in (("fills", check_fills), ("listing", lambda c: check_listing(c, force=False)),
                             ("settle", settle), ("auto", auto_pass), ("paper", paper_pass), ("notes", backfill_notes),
                             ("account", read_account)):
                try:
                    n = fn(ctx)
                    if n:
                        did.append(f"{name}: {n}")
                except Exception as e:  # noqa: BLE001
                    traceback.print_exc()
                    set_error(f"{name}: {type(e).__name__}: {e}")
            ec.kv_set("tick.last", ec.iso(now))
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            set_error(f"tick: {type(e).__name__}: {e}")
    return {"did": did, "took_ms": int((time.time() - t0) * 1000)}


def default_cards(now=None, look_days=None):
    """GET /api/cards with no filter: every listed fixture from 3 h ago to the listing lookahead (16 days, so the
    early market is on the page too: Jonathan bets "when the market is the least sharp"), plus live-order and
    position cards."""
    now = now or ec.now()
    look = int(look_days or ec.DEFAULTS["window"]["listing_lookahead_days"])
    return cards_where("(f.kickoff_utc >= ? AND f.kickoff_utc <= ?) OR c.state IN ('approved', 'placed', 'partial', 'filled')",
                       (ec.iso(now - timedelta(hours=3)), ec.iso(now + timedelta(days=look))))


def real_ctx(cfg=None):
    """A Ctx with the real clients from config (the command line and edge_check use it)."""
    import edge_reason
    cfg = cfg or ec.load_config()
    kalshi = quotes = football = poly = model = None
    try:
        from kalshi_api import Kalshi
        kalshi = Kalshi(env=cfg["env"], dry_run=bool(cfg["dry_run"]), allow_prod=bool(cfg.get("rehearsal_passed")))
        quotes = Kalshi(env="prod", dry_run=True)      # public prices always from the production exchange
    except Exception as e:  # noqa: BLE001
        set_error(f"kalshi client: {type(e).__name__}: {e}")
    try:
        from api_football import Football
        football = Football()
    except Exception as e:  # noqa: BLE001
        set_error(f"football client: {type(e).__name__}: {e}")
    try:
        import polymarket_read
        poly = polymarket_read
    except Exception as e:  # noqa: BLE001
        set_error(f"polymarket reader: {type(e).__name__}: {e}")
    try:
        from edge_model import ModelService
        model = ModelService(cfg)
    except Exception as e:  # noqa: BLE001
        set_error(f"model service: {type(e).__name__}: {e}")
    return Ctx(cfg, kalshi, football, poly, model, edge_reason.Reasoner(cfg), quotes=quotes)


if __name__ == "__main__":
    ec.ensure_dirs()
    ctx_ = real_ctx()
    if "sync" in sys.argv:
        print(json.dumps(sync_fixtures(ctx_), indent=1))
    else:
        print(json.dumps(tick(ctx_, force_sync="sync" in sys.argv or "--sync" in sys.argv), indent=1))
