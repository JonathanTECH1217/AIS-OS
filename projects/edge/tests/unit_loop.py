"""Monarc Edge loop checks (2026-10-04): the gate, the mode lock, the window, orders, delisting, settlement, halts.

Run through projects/edge/tests/run.py (it imports this module and calls tests(check)), or alone:

  python projects/edge/tests/unit_loop.py

Every test gets its own SQLite file and config copy in a temp folder and a frozen clock; the clients are the fakes
in fakes.py, so nothing here touches the network, the real data folder or the real config.
"""
import json
import os
import shutil
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPTS = ROOT / "scripts"
_TMP = Path(tempfile.mkdtemp(prefix="edge-unit-"))
os.environ.setdefault("EDGE_DATA", str(_TMP / "data"))
os.environ.setdefault("EDGE_CONFIG", str(_TMP / "config.json"))
os.environ["EDGE_NO_CLAUDE"] = "1"
for p in (str(SCRIPTS), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)
import edge_common as ec  # noqa: E402
import edge_cards as cards  # noqa: E402
import edge_ledger as ledger  # noqa: E402
import edge_reason  # noqa: E402
import edge_server as server  # noqa: E402
import fakes  # noqa: E402

T0 = ec.parse_iso("2026-10-16T12:00:00Z")      # a Friday noon UTC


# ---------------------------------------------------------------- harness

def fresh(name, now=T0, cfg_over=None):
    """A new db file, a new config file (repo config with overrides), the clock at `now`. Returns the config."""
    ec.DB_PATH = _TMP / f"{name}.sqlite"
    ec.CONFIG = _TMP / f"{name}-config.json"
    base = ec.deep_merge(ec.DEFAULTS, ec.read_json(ec.EDGE_DIR / "config.json", {}) or {})
    base.pop("_about", None)
    ec.save_config(ec.deep_merge(base, cfg_over or {}))
    ec.set_clock(ec.iso(now))
    return ec.load_config()


def ctx_for(cfg, script, reasoner=None, football=None):
    return cards.Ctx(cfg, fakes.FakeKalshi(script["kalshi"]), football if football is not None else fakes.FakeFootball(script["football"]),
                     fakes.FakePoly(script["poly"]), fakes.FakeModel(script["model"]),
                     reasoner if reasoner is not None else fakes.FakeReasoner())


def one_fixture(now, hours, listed_at=None, fill_after=1):
    """Nottingham Forest v Arsenal with the weekend's prices: Arsenal green (8.3 points), the other two amber."""
    ev, fx, pm = fakes.fixture_script(now, hours, "Nottingham Forest", "Arsenal", "NFO", "ARS",
                                      {"home": (0.24, 0.25, 20000), "away": (0.44, 0.45, 25000), "draw": (0.29, 0.30, 15000)},
                                      2001, listed_at=listed_at, poly={"home": 0.21, "draw": 0.26, "away": 0.53})
    return {"kalshi": {"events": [ev], "fill_after_polls": fill_after}, "football": {"fixtures": [fx], "lineups": {}},
            "poly": {"matches": [pm]}, "model": {"Nottingham Forest|Arsenal": {"p_home": 0.20, "p_draw": 0.25, "p_away": 0.55}}}


def by_outcome(fid):
    return {c["outcome"]: c for c in cards.cards_of_fixture(fid)}


def seed_settled(groups, paper=0, fixture_id=9000, start_n=0):
    """groups: [(n, model_p, yes_count, pnl_each, clv_each)]. Writes settled Yes cards with those numbers."""
    c = ec.db()
    c.execute("INSERT OR REPLACE INTO fixtures (id, home, away, kickoff_utc, kalshi_event) VALUES (?,?,?,?,?)",
              (fixture_id, "Seed Home", "Seed Away", "2026-09-01T14:00:00Z", "KXEPLGAME-SEED"))
    k = start_n
    for n, p, yes, pnl, clv in groups:
        for i in range(n):
            result = "yes" if i < yes else "no"
            c.execute("INSERT INTO cards (id, fixture_id, event_ticker, ticker, outcome, side, created, expires_at, model_p, "
                      "market_price, market_mid, break_even, state, fill_count, avg_fill, result, pnl_usd, clv_points, band, "
                      "hours_band, paper, flags_json, sources_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'[]','[]')",
                      (f"SEED-{k}", fixture_id, "KXEPLGAME-SEED", f"KXEPLGAME-SEED-{k}", "home", "yes",
                       "2026-09-01T10:00:00Z", "2026-09-01T14:00:00Z", p, p - 0.08, p - 0.07, p - 0.06, "settled", 10,
                       p - 0.08, result, pnl, clv, ec.band_of(p * 100), "1-3h", paper))
            k += 1
    c.commit()
    return k


GOOD = [(200, 0.45, 90, 1.0, 6.0)]        # one band, 45% said, 45% happened, profit, CLV 6


# ---------------------------------------------------------------- tests

def test_gate(check):
    cfg = fresh("gate")
    seed_settled([(199, 0.45, 90, 1.0, 6.0)])
    g = ledger.gate(cfg)
    check("gate: 199 settled fails the count light", not g["lights"]["count"]["ok"] and not g["passed"], str(g["reasons"]))

    fresh("gate2")
    seed_settled([(160, 0.45, 72, 1.0, 6.0), (40, 0.65, 29, 1.0, 6.0)])     # 72.5% in the 60-70 band: 7.5 off
    g = ledger.gate(cfg)
    band = next(b for b in g["lights"]["calibration"]["bands"] if b["band"] == "60-70")
    check("gate: a band 7 points off is red and fails calibration", band["light"] == "red" and not g["lights"]["calibration"]["ok"]
          and g["lights"]["count"]["ok"], json.dumps(band))

    fresh("gate3")
    seed_settled([(200, 0.45, 90, -0.5, 6.0)])
    g = ledger.gate(cfg)
    check("gate: negative pnl fails profit", not g["lights"]["profit"]["ok"] and g["lights"]["calibration"]["ok"],
          str(g["lights"]["profit"]))

    fresh("gate4")
    seed_settled([(200, 0.45, 90, 1.0, 4.9)])
    g = ledger.gate(cfg)
    check("gate: CLV 4.9 fails", not g["lights"]["clv"]["ok"] and g["lights"]["clv"]["value"] == 4.9, str(g["lights"]["clv"]))

    fresh("gate5")
    seed_settled(GOOD)
    g = ledger.gate(cfg)
    check("gate: all good passes", g["passed"], str(g["reasons"]))

    fresh("gate6")
    seed_settled([(171, 0.45, 77, 1.0, 6.0), (29, 0.65, 22, 1.0, 6.0)])     # 29 cards 10.9 off: grey, ignored
    g = ledger.gate(cfg)
    band = next(b for b in g["lights"]["calibration"]["bands"] if b["band"] == "60-70")
    check("gate: a band with 29 cards is grey and ignored", band["light"] == "grey" and g["passed"],
          f"{band['light']} {g['reasons']}")
    rec = ledger.record(cfg)
    check("gate: record has the API shape", all(k in rec for k in ("settled", "bets", "hit_rate", "pnl_usd", "bankroll", "equity",
                                                                     "ledger", "bands", "market_bands", "clv", "brier", "by_side",
                                                                     "by_outcome")) and rec["settled"] == 200, str(sorted(rec)))


def test_mode_lock(check):
    cfg = fresh("mode_lock", cfg_over={"env": "demo"})     # the live config may say prod; the lock test starts from demo
    script = one_fixture(T0, 20)
    ctx = ctx_for(cfg, script)
    server.CTX = ctx
    status, payload = server.put_config({"mode": "auto"}, ctx)
    check("mode_lock: PUT auto is 409 with the gate while nothing is settled", status == 409 and "gate" in payload
          and payload["gate"]["passed"] is False, f"{status} {list(payload)}")
    status, payload = server.put_config({"nonsense": 1}, ctx)
    check("mode_lock: an unknown key is 400", status == 400, f"{status} {payload}")
    status, payload = server.put_config({"gap_floor_points": "seven"}, ctx)
    check("mode_lock: a wrong type is 400", status == 400, f"{status} {payload}")
    status, payload = server.put_config({"env": "prod", "dry_run": False}, ctx)
    check("mode_lock: prod with dry_run false is 409 without rehearsal_passed", status == 409, f"{status} {payload}")
    check("mode_lock: config untouched after the refusals", ec.load_config()["mode"] == "approve" and ec.load_config()["env"] == "demo")
    seed_settled(GOOD)
    status, payload = server.put_config({"mode": "auto"}, ctx)
    check("mode_lock: PUT auto is 200 once the gate passes", status == 200 and payload["mode"] == "auto"
          and ec.load_config()["mode"] == "auto" and ctx.cfg["mode"] == "auto", f"{status}")
    cards.halt(ctx, "test", "a test halt")
    check("mode_lock: a halt flips the mode back to approve, in memory and on disk",
          ctx.cfg["mode"] == "approve" and ec.load_config()["mode"] == "approve" and ec.kv_get("halted") is True)
    status, payload = server.put_config({"mode": "auto"}, ctx)
    check("mode_lock: PUT auto is 409 while halted", status == 409, f"{status}")
    cards.clear_halt(ctx)
    check("mode_lock: clear_halt lifts it", ec.kv_get("halted") is False and all(h["cleared_at"] for h in cards.halts()))


def test_window(check):
    K = T0 + timedelta(hours=30)
    cfg = fresh("window", now=K - timedelta(hours=26))
    x = one_fixture(K, 0, listed_at=K - timedelta(hours=24), fill_after=None)
    ev, fx, pm = fakes.fixture_script(K, 0, "Chelsea", "Tottenham", "CHE", "TOT",
                                      {"home": (0.39, 0.40, 30000), "away": (0.20, 0.21, 20000), "draw": (0.26, 0.27, 12000)},
                                      2002, listed_at=K - timedelta(hours=24), poly={"home": 0.40, "draw": 0.265, "away": 0.21})
    x["kalshi"]["events"].append(ev)
    x["football"]["fixtures"].append(fx)
    x["poly"]["matches"].append(pm)
    x["model"]["Chelsea|Tottenham"] = {"p_home": 0.50, "p_draw": 0.20, "p_away": 0.30}
    ctx = ctx_for(cfg, x)

    r = cards.tick(ctx, force_sync=True)
    check("window: T-26 h, nothing listed yet, no fixture and no card",
          not cards.cards_where() and not cards.fixtures_between(T0, K + timedelta(days=1)), str(r["did"]))

    ec.set_clock(ec.iso(K - timedelta(hours=23)))
    r = cards.tick(ctx, force_sync=True)
    a, b = by_outcome(2001), by_outcome(2002)
    check("window: T-23 h, three cards per fixture", len(a) == 3 and len(b) == 3, str(r["did"]))
    check("window: Arsenal ready, Forest and Tie no_edge (amber)",
          a["away"]["state"] == "ready" and a["home"]["state"] == "no_edge" and a["draw"]["state"] == "no_edge",
          {k: (v["state"], v["color"], round(v["gap_points"] or 0, 1)) for k, v in a.items()})
    check("window: Chelsea ready, Tottenham watching (smaller green), Tie no_edge",
          b["home"]["state"] == "ready" and b["away"]["state"] == "watching" and b["draw"]["state"] == "no_edge"
          and "larger edge on home" in json.loads(b["away"]["flags_json"]),
          {k: (v["state"], v["color"], round(v["gap_points"] or 0, 1), v["flags_json"]) for k, v in b.items()})
    js = {c["id"]: cards.card_json(c) for c in cards.cards_where()}
    check("window: can_approve only on ready cards",
          all((v["can_approve"] is True) == (v["state"] == "ready") for v in js.values()) and sum(v["can_approve"] for v in js.values()) == 2)
    check("window: hours band 12-24h and band of the model chance", a["away"]["hours_band"] == "12-24h" and a["away"]["band"] == "50-60")
    check("window: the Arsenal card carries 'second witness disagrees' (Polymarket 53 against Kalshi 44.5)",
          "second witness disagrees" in json.loads(a["away"]["flags_json"]), a["away"]["flags_json"])
    check("window: stake and count from the gap (6.25% of $1,000 at 0.45)",
          a["away"]["stake_usd"] == 62.54 and a["away"]["count"] == 138, f"{a['away']['stake_usd']} {a['away']['count']}")

    ec.set_clock(ec.iso(K - timedelta(minutes=70)))
    ctx.football.post_lineups(2001)
    r = cards.tick(ctx)
    a = by_outcome(2001)
    check("window: T-70 min with lineups posted, re-priced with lineups_seen 1 and the flag",
          a["away"]["lineups_seen"] == 1 and "lineups posted" in json.loads(a["away"]["flags_json"]) and a["away"]["state"] == "ready",
          f"{a['away']['lineups_seen']} {a['away']['flags_json']} {r['did']}")
    placed, errors = cards.approve(ctx, a["away"]["id"])
    check("window: Arsenal approved at T-70 rests as placed", placed and placed["state"] == "placed", str(errors))

    ec.set_clock(ec.iso(K - timedelta(minutes=19)))
    r = cards.tick(ctx)
    a, b = by_outcome(2001), by_outcome(2002)
    check("window: T-19 min, Chelsea without lineups is no_edge with 'no lineups'",
          all(c["state"] == "no_edge" and "no lineups" in json.loads(c["flags_json"]) for c in b.values()),
          {k: (v["state"], v["flags_json"]) for k, v in b.items()})
    check("window: the fixture with lineups is untouched by the no-lineups rule", a["away"]["state"] == "placed"
          and a["home"]["state"] == "no_edge" and "no lineups" not in json.loads(a["home"]["flags_json"]))

    ec.set_clock(ec.iso(K - timedelta(minutes=1)))
    r = cards.tick(ctx)
    a, b = by_outcome(2001), by_outcome(2002)
    check("window: T-1 min, the resting order is cancelled and the card is unfilled",
          a["away"]["state"] == "unfilled" and ctx.kalshi.canceled == [a["away"]["order_id"]], f"{a['away']['state']} {ctx.kalshi.canceled}")
    check("window: untouched cards expired", all(c["state"] == "expired" for c in list(b.values()) + [a["home"], a["draw"]]),
          {k: v["state"] for k, v in {**a, **b}.items()})
    snaps = ec.rows(ec.db().execute("SELECT as_of FROM snapshots WHERE ticker=? ORDER BY as_of", (a["away"]["ticker"],)))
    check("window: snapshots at each due step (4)", len(snaps) == 4, str([s["as_of"] for s in snaps]))


def test_approve_flow(check):
    cfg = fresh("approve")
    script = one_fixture(T0, 20)
    ctx = ctx_for(cfg, script)
    cards.tick(ctx, force_sync=True)
    card = by_outcome(2001)["away"]
    placed, errors = cards.approve(ctx, card["id"])
    o = ctx.kalshi.calls[-1]
    check("approve: the order reached the fake with side, price, count and client_order_id",
          o[0] == "create_order" and o[2] == "yes" and o[3] == 0.45 and o[4] == 138 and o[5] == f"edge-{card['id']}-1", str(o))
    check("approve: the card is placed with the order id and approved_at", placed and placed["state"] == "placed"
          and placed["order_id"] == "fake-order-1" and placed["approved_at"] and placed["mode"] == "approve", str(errors))
    row = ec.db().execute("SELECT * FROM orders WHERE card_id=?", (card["id"],)).fetchone()
    check("approve: an orders row with the expiry two minutes before kickoff", row and row["expires_at"] == ec.iso(T0 + timedelta(hours=20, minutes=-2)),
          dict(row) if row else "none")
    n = cards.check_fills(ctx)
    c2 = cards.get_card(card["id"])
    check("approve: the fake fills on the first poll and the card is filled", n == 1 and c2["state"] == "filled"
          and c2["fill_count"] == 138 and c2["avg_fill"] == 0.45, f"{c2['state']} {c2['fill_count']}")
    led = ec.rows(ec.db().execute("SELECT kind, amount_usd, balance_after FROM ledger ORDER BY id"))
    check("approve: ledger fill and fee rows (138 x 0.45 = 62.10, fee 2.40)",
          [(r["kind"], r["amount_usd"]) for r in led] == [("deposit", 1000.0), ("fill", -62.1), ("fee", -2.4)]
          and led[-1]["balance_after"] == 935.5, str(led))
    check("approve: fees_paid matches kalshi_fee_usd", c2["fees_paid"] == ec.kalshi_fee_usd(138, 0.45) == 2.4, str(c2["fees_paid"]))
    again, errors = cards.approve(ctx, card["id"])
    check("approve: a second approve is refused", again is None and errors and "filled" in errors[0], str(errors))
    check("approve: equity counts the open position", ledger.equity() == 935.5 + 62.1, str(ledger.equity()))
    other = by_outcome(2001)["home"]
    cards.update_card(other["id"], state="ready")
    blocked, errors = cards.approve(ctx, other["id"])
    check("approve: a second position on the same match is refused (Q18)", blocked is None and "already" in errors[0], str(errors))


def test_approve_repriced(check):
    cfg = fresh("repriced")
    script = one_fixture(T0, 20)
    ctx = ctx_for(cfg, script)
    server.CTX = ctx
    cards.tick(ctx, force_sync=True)
    card = by_outcome(2001)["away"]
    ctx.kalshi.set_price(card["ticker"], yes_bid=0.50, yes_ask=0.51)
    status, payload = server.do_approve(card["id"])
    check("repriced: 409 with errors and the card", status == 409 and payload["errors"] and payload["card"]["id"] == card["id"],
          f"{status} {payload.get('errors')}")
    check("repriced: the card is no_edge with the new numbers", payload["card"]["state"] == "no_edge"
          and payload["card"]["market_yes_ask"] == 0.51 and payload["card"]["color"] == "amber" and not ctx.kalshi.orders,
          f"{payload['card']['state']} {payload['card']['gap_points']}")


def test_busy_fail(check):
    cfg = fresh("busy")
    script = fakes.make_script(T0)
    ctx = ctx_for(cfg, script)
    cards.tick(ctx, force_sync=True)
    b = by_outcome(1002)
    check("busy: the thin Tie market is green on price but no_edge on the busy floor",
          b["draw"]["color"] == "green" and b["draw"]["state"] == "no_edge" and b["draw"]["busy_ok"] == 0
          and "3,000" in (b["draw"]["busy_reason"] or ""), f"{b['draw']['state']} {b['draw']['busy_reason']}")
    a, c = by_outcome(1001), by_outcome(1003)
    check("busy: the weekend's shape (green, amber, red, busy)",
          a["away"]["state"] == "ready" and c["home"]["state"] == "ready" and b["away"]["color"] == "red"
          and b["home"]["color"] == "amber" and c["draw"]["color"] == "red",
          {f"{k}-{o}": (v["state"], v["color"]) for k, d in (("A", a), ("B", b), ("C", c)) for o, v in d.items()})
    check("busy: depth check uses the chosen side", ec.busy_check({"volume": 20000, "yes_bid": 0.44, "yes_ask": 0.45,
                                                                   "yes_ask_size": 10, "yes_bid_size": 500}, 100, "yes", cfg["busy"])[0] is False)


def test_delisting(check):
    cfg = fresh("delist")
    script = one_fixture(T0, 20, fill_after=None)
    ctx = ctx_for(cfg, script)
    cards.tick(ctx, force_sync=True)
    card = by_outcome(2001)["away"]
    placed, _ = cards.approve(ctx, card["id"])
    ctx.kalshi.delist(card["ticker"])
    n = cards.check_listing(ctx)
    c2 = cards.get_card(card["id"])
    check("delisting: a 404 market makes the card delisted and cancels the resting order",
          n == 1 and c2["state"] == "delisted" and ctx.kalshi.canceled == [placed["order_id"]]
          and "delisted by Kalshi" in json.loads(c2["flags_json"]), f"{c2['state']} {ctx.kalshi.canceled}")

    cfg = fresh("gone")
    ctx = ctx_for(cfg, one_fixture(T0, 20))
    cards.tick(ctx, force_sync=True)
    ctx.kalshi.clear_events()
    cards.sync_fixtures(ctx)
    check("delisting: one empty sync is not a halt", not ec.kv_get("halted") and ec.kv_get("sync.empty_syncs") == 1)
    cards.sync_fixtures(ctx)
    hs = cards.halts()
    check("delisting: two empty syncs halt sports_gone and park the ready card",
          ec.kv_get("halted") is True and hs and hs[0]["reason"] == "sports_gone"
          and by_outcome(2001)["away"]["state"] == "halted", str(hs))

    cfg = fresh("stateblock", cfg_over={"mode": "approve"})
    ctx = ctx_for(cfg, one_fixture(T0, 20))
    cards.tick(ctx, force_sync=True)
    card = by_outcome(2001)["away"]
    ctx.kalshi.reject_next_order("Trading is not available in your state", status=403)
    placed, errors = cards.approve(ctx, card["id"])
    hs = cards.halts()
    check("delisting: a state rejection halts state_block with the body kept",
          placed is None and ec.kv_get("halted") is True and hs and hs[0]["reason"] == "state_block"
          and "state" in hs[0]["detail"].lower() and "forbidden" in hs[0]["detail"], str(hs[:1]) + str(errors))
    check("delisting: the card is parked as halted", cards.get_card(card["id"])["state"] == "halted")
    check("delisting: an ordinary rejection is not a state block",
          not cards.looks_like_state_block(fakes.KalshiError(400, "insufficient balance", "{}"))
          and cards.looks_like_state_block(fakes.KalshiError(403, "geoblocked", "")))


def _filled_card(name, revenue=None, result="yes"):
    cfg = fresh(name)
    script = one_fixture(T0, 20)
    ctx = ctx_for(cfg, script)
    cards.tick(ctx, force_sync=True)
    card = by_outcome(2001)["away"]
    cards.approve(ctx, card["id"])
    cards.check_fills(ctx)
    K = T0 + timedelta(hours=20)
    ec.set_clock(ec.iso(K - timedelta(minutes=3)))
    cards.tick(ctx)                                     # a snapshot inside the last 5 minutes: the closing fair
    ec.set_clock(ec.iso(K + timedelta(hours=3)))
    ctx.kalshi.settle(card["ticker"], result, revenue_usd=revenue)
    n = cards.settle(ctx)
    return ctx, cards.get_card(card["id"]), n


def test_settle_ledger(check):
    ctx, c, n = _filled_card("settle")
    check("settle: a filled Yes card settled yes is settled with the result", n == 1 and c["state"] == "settled" and c["result"] == "yes")
    check("settle: pnl = 138 x 0.55 - 2.40 = 73.50", c["pnl_usd"] == 73.5, str(c["pnl_usd"]))
    check("settle: closing fair is the last mid (0.445) and clv = 100 x (0.445 - 0.4673) = -2.23",
          c["closing_fair"] == 0.445 and abs(c["clv_points"] + 2.23) < 0.02, f"{c['closing_fair']} {c['clv_points']}")
    led = ec.rows(ec.db().execute("SELECT kind, amount_usd, balance_after FROM ledger ORDER BY id"))
    check("settle: ledger settlement row +138 and the balance 1073.50",
          [(r["kind"], r["amount_usd"]) for r in led] == [("deposit", 1000.0), ("fill", -62.1), ("fee", -2.4), ("settlement", 138.0)]
          and led[-1]["balance_after"] == 1073.5, str(led))
    s = ec.db().execute("SELECT * FROM settlements WHERE card_id=?", (c["id"],)).fetchone()
    check("settle: a settlements row", s and s["market_result"] == "yes" and s["revenue_usd"] == 138.0)
    rec = ledger.record(ctx.cfg)
    check("settle: the record counts it", rec["settled"] == 1 and rec["pnl_usd"] == 73.5 and rec["hit_rate"] == 100.0
          and rec["clv"]["n"] == 1 and rec["by_side"][0]["side"] == "yes", json.dumps({k: rec[k] for k in ("settled", "pnl_usd", "clv")}))

    ctx, c, n = _filled_card("settle2", revenue=137.0)
    led = ec.rows(ec.db().execute("SELECT kind, amount_usd, note FROM ledger ORDER BY id"))
    adj = [r for r in led if r["kind"] == "adjust"]
    check("settle: a revenue one dollar off writes an adjust row and the pnl follows the money",
          len(adj) == 1 and adj[0]["amount_usd"] == -1.0 and c["pnl_usd"] == 72.5, str(adj) + str(c["pnl_usd"]))

    ctx, c, n = _filled_card("settle3", result="no")
    check("settle: a loss: pnl = -62.10 - 2.40 = -64.50 and no payout", c["pnl_usd"] == -64.5 and c["result"] == "no"
          and ledger.balance() == 935.5, f"{c['pnl_usd']} {ledger.balance()}")


def test_drawdown(check):
    cfg = fresh("drawdown", cfg_over={"mode": "auto"})
    ctx = ctx_for(cfg, one_fixture(T0, 20))
    ledger.init_bankroll(cfg)
    ledger.add("settlement", -251.0, "x", "a bad weekend")
    check("drawdown: equity 749 is 25.1% under the 1000 peak", ledger.drawdown_pct() == 25.1 and not ledger.drawdown_allows(cfg))
    hit = ledger.drawdown_check(ctx)
    check("drawdown: in auto mode it halts and the mode goes back to approve",
          hit and ec.kv_get("halted") is True and cards.halts()[0]["reason"] == "drawdown" and ctx.cfg["mode"] == "approve"
          and ec.load_config()["mode"] == "approve", str(cards.halts()[:1]))

    cfg = fresh("drawdown2", cfg_over={"mode": "approve"})
    ctx = ctx_for(cfg, one_fixture(T0, 20))
    ledger.init_bankroll(cfg)
    ledger.add("settlement", -251.0, "x", "a bad weekend")
    hit = ledger.drawdown_check(ctx)
    check("drawdown: in approve mode with auto_only nothing happens", not hit and not ec.kv_get("halted") and not cards.halts())
    cfg = fresh("drawdown3", cfg_over={"mode": "approve", "drawdown": {"auto_only": False}})
    ctx = ctx_for(cfg, one_fixture(T0, 20))
    ledger.init_bankroll(cfg)
    ledger.add("settlement", -251.0, "x", "a bad weekend")
    check("drawdown: with auto_only off approve mode halts too", ledger.drawdown_check(ctx) and ec.kv_get("halted") is True)


def test_reasoning_guard(check):
    cfg = fresh("reason")
    script = one_fixture(T0, 20)
    fr = fakes.FakeReasoner()
    ctx = ctx_for(cfg, script, reasoner=fr)
    cards.tick(ctx, force_sync=True)
    c = by_outcome(2001)["away"]
    check("reasoning: the fake's stray 63% and model_p key never move model_p", c["model_p"] == 0.55 and c["p_away"] == 0.55
          and "63%" in c["reasoning"], f"{c['model_p']} {c['reasoning'][:60]}")
    check("reasoning: its flags are appended, nothing else", "fake reasoning" in json.loads(c["flags_json"]))
    check("reasoning: written once for the ready card only", len(fr.calls) == 1 and fr.calls[0][0] == c["id"], str(fr.calls))
    cards.tick(ctx)                                        # nothing due: no second call
    ec.set_clock(ec.iso(T0 + timedelta(hours=1)))
    cards.tick(ctx)                                        # a new snapshot, same side and gap band: still no call
    check("reasoning: a re-price with the same side and gap band does not call again", len(fr.calls) == 1, str(fr.calls))
    ctx.kalshi.set_price(c["ticker"], yes_bid=0.39, yes_ask=0.40)          # gap 13.3: the next band
    ec.set_clock(ec.iso(T0 + timedelta(hours=2)))
    cards.tick(ctx)
    check("reasoning: a gap band change calls again", len(fr.calls) == 2, str(fr.calls))

    cfg = fresh("reason2")
    ctx = ctx_for(cfg, one_fixture(T0, 20), reasoner=edge_reason.Reasoner(cfg))
    cards.tick(ctx, force_sync=True)
    c = by_outcome(2001)["away"]
    check("reasoning: with EDGE_NO_CLAUDE the card still has the template text, in sixth-grade words",
          c["reasoning"].startswith("We think Arsenal wins about 55 times out of 100. Kalshi's price says Arsenal wins 45 times out of 100.")
          and "points in our favor, so this is a green card: " in c["reasoning"] and "risk $" in c["reasoning"]
          and " to win $" in c["reasoning"] and "break-even" not in c["reasoning"] and "+0 points" not in c["reasoning"],
          c["reasoning"])
    check("reasoning: no Claude spend recorded", edge_reason.Reasoner(cfg).spent_today() == 0.0)


def test_paper_counts(check):
    cfg = fresh("paper")
    seed_settled(GOOD, paper=1)
    g = ledger.gate(cfg)
    check("paper: 200 paper cards count toward the gate", g["lights"]["count"]["value"] == 200 and g["passed"], str(g["reasons"]))
    cfg = fresh("paper2", cfg_over={"paper_auto": False})     # the click path; paper_auto is tested below
    ctx = cards.Ctx(cfg, fakes.FakeKalshi(one_fixture(T0, 20)["kalshi"], dry_run=True), fakes.FakeFootball(one_fixture(T0, 20)["football"]),
                    fakes.FakePoly(one_fixture(T0, 20)["poly"]), fakes.FakeModel(one_fixture(T0, 20)["model"]), fakes.FakeReasoner())
    cards.tick(ctx, force_sync=True)
    c = by_outcome(2001)["away"]
    check("paper: cards from a dry-run client are paper", c["paper"] == 1)
    placed, errors = cards.approve(ctx, c["id"])
    check("paper: a dry order fills at the ask at once (paper fill)", placed and placed["state"] == "filled" and placed["fill_count"] == 138
          and "paper fill at the ask" in json.loads(placed["flags_json"]), str(errors))
    # a paper fill never reaches the account's settlement list: the card settles from the market's own result
    ec.set_clock(ec.iso(T0 + timedelta(hours=22, minutes=1)))
    ctx.kalshi.settle(placed["ticker"], placed["side"])          # the market decides in our favour
    n = cards.settle(ctx)
    done = next((r for r in cards.cards_of_fixture(2001) if r["id"] == placed["id"]), None)
    led = ec.db().execute("SELECT kind, amount_usd FROM ledger WHERE card_id=? AND kind='settlement'", (placed["id"],)).fetchone()
    check("paper: the paper card settles from the market result, with a ledger payout",
          n == 1 and done is not None and done["state"] == "settled" and done["result"] == placed["side"]
          and done["pnl_usd"] is not None and done["pnl_usd"] > 0 and led is not None and float(led["amount_usd"]) == 138.0,
          f"{n} {done and done['state']} pnl={done and done['pnl_usd']} ledger={dict(led) if led else None}")
    # paper_auto: with dry_run on, a tick paper-fills the ready card by itself (no click); off, it waits
    cfg3 = fresh("paper3")
    ctx3 = cards.Ctx(cfg3, fakes.FakeKalshi(one_fixture(T0, 20)["kalshi"], dry_run=True), fakes.FakeFootball(one_fixture(T0, 20)["football"]),
                     fakes.FakePoly(one_fixture(T0, 20)["poly"]), fakes.FakeModel(one_fixture(T0, 20)["model"]), fakes.FakeReasoner())
    r3 = cards.tick(ctx3, force_sync=True)
    c3 = by_outcome(2001)["away"]
    acct = ec.kv_get("account") or {}
    check("paper_auto: a tick paper-fills the ready card by itself, mode paper",
          c3["state"] == "filled" and c3["mode"] == "paper" and c3["paper"] == 1 and any(d.startswith("paper:") for d in r3["did"]),
          f"{c3['state']} {c3['mode']} {r3['did']}")
    check("paper_auto: the account read lands in the bundle (balance from the fake; a paper fill is not a real position)",
          acct.get("balance_usd") is not None and acct.get("error") is None and acct.get("positions") == 0, str(acct))
    cfg4 = fresh("paper4", cfg_over={"paper_auto": False})
    ctx4 = cards.Ctx(cfg4, fakes.FakeKalshi(one_fixture(T0, 20)["kalshi"], dry_run=True), fakes.FakeFootball(one_fixture(T0, 20)["football"]),
                     fakes.FakePoly(one_fixture(T0, 20)["poly"]), fakes.FakeModel(one_fixture(T0, 20)["model"]), fakes.FakeReasoner())
    cards.tick(ctx4, force_sync=True)
    c4 = by_outcome(2001)["away"]
    check("paper_auto off: the ready card waits for the click", c4["state"] == "ready", c4["state"])
    # yellow: a gap past big_gap_points is a warning (review of the first card, 2026-10-04). Paper mode still logs it;
    # live auto mode never takes it; Jonathan may still click it.
    check("color_of: 9.9 green, 10 yellow, 6.9 amber, no big line means green",
          ec.color_of(9.9, 7, 10) == "green" and ec.color_of(10, 7, 10) == "yellow" and ec.color_of(6.9, 7, 10) == "amber"
          and ec.color_of(12, 7, None) == "green")
    cfg5 = fresh("yellow", cfg_over={"paper_auto": False})
    s5 = one_fixture(T0, 20)
    ctx5 = cards.Ctx(cfg5, fakes.FakeKalshi(s5["kalshi"], dry_run=True), fakes.FakeFootball(s5["football"]),
                     fakes.FakePoly(s5["poly"]), fakes.FakeModel(s5["model"]), fakes.FakeReasoner())
    cards.tick(ctx5, force_sync=True)
    c5 = by_outcome(2001)["away"]
    ctx5.kalshi.set_price(c5["ticker"], yes_bid=0.40, yes_ask=0.41)      # 55 against 41: about 12 points, past the 10 line
    ec.set_clock(ec.iso(T0 + timedelta(minutes=61)))
    cards.tick(ctx5)
    c5 = by_outcome(2001)["away"]
    check("yellow: a gap past big_gap_points is yellow, still ready, and flagged",
          c5["color"] == "yellow" and c5["state"] == "ready" and any(f.startswith("big gap") for f in json.loads(c5["flags_json"])),
          f"{c5['color']} {c5['state']} {c5['gap_points']} {c5['flags_json']}")
    cfg5["paper_auto"] = True
    n5 = cards.paper_pass(ctx5)
    c5 = by_outcome(2001)["away"]
    check("yellow: paper mode still logs it as a paper bet", n5 == 1 and c5["state"] == "filled" and c5["color"] == "yellow",
          f"{n5} {c5['state']} {c5['color']}")
    rec5 = ledger.record(cfg5, full=False)
    check("record: by_gap has the three gap bands", [g["gap"] for g in rec5.get("by_gap", [])] == ["7 to 10", "10 to 15", "15 and up"], str(rec5.get("by_gap")))
    cfg6 = fresh("yellow_auto", cfg_over={"paper_auto": False, "mode": "auto"})
    seed_settled(GOOD)
    s6 = one_fixture(T0, 20)
    ctx6 = cards.Ctx(cfg6, fakes.FakeKalshi(s6["kalshi"], dry_run=True), fakes.FakeFootball(s6["football"]),
                     fakes.FakePoly(s6["poly"]), fakes.FakeModel(s6["model"]), fakes.FakeReasoner())
    cards.tick(ctx6, force_sync=True)
    c6 = by_outcome(2001)["away"]
    ctx6.kalshi.set_price(c6["ticker"], yes_bid=0.40, yes_ask=0.41)
    ec.set_clock(ec.iso(T0 + timedelta(minutes=61)))
    cards.tick(ctx6)
    c6 = by_outcome(2001)["away"]
    check("yellow: live auto mode never takes a yellow card (it stays ready for his click)",
          c6["color"] == "yellow" and c6["state"] == "ready", f"{c6['color']} {c6['state']}")


def test_no_football(check):
    cfg = fresh("nofootball")
    script = one_fixture(T0, 20)
    ctx = ctx_for(cfg, script, football=fakes.FakeFootball({"raise": True}))
    r = cards.tick(ctx, force_sync=True)
    fx = cards.fixtures_between(T0, T0 + timedelta(days=2))
    check("no_football: the fixture comes from the Kalshi event alone (hashed id, names from the title), kickoff from Polymarket",
          len(fx) == 1 and fx[0]["id"] < 0 and fx[0]["home"] == "Nottingham Forest" and fx[0]["away"] == "Arsenal"
          and fx[0]["kickoff_utc"] == ec.iso(T0 + timedelta(hours=20)) and bool(fx[0]["poly_slug"]), str(fx))
    fj = cards.fixture_json(fx[0])
    check("no_football: kickoff_source polymarket when it links", fj["kickoff_source"] == "polymarket", str(fj))
    a = by_outcome(fx[0]["id"])
    check("no_football: cards priced with 'no lineup feed' and no 'kickoff from Kalshi' flag",
          a["away"]["state"] == "ready" and "no lineup feed" in json.loads(a["away"]["flags_json"])
          and "kickoff from Kalshi" not in json.loads(a["away"]["flags_json"]), a["away"]["flags_json"])
    ec.set_clock(ec.iso(T0 + timedelta(hours=20, minutes=-19)))
    cards.tick(ctx)
    a = by_outcome(fx[0]["id"])
    check("no_football: at T-19 the card stays ready (decide_without_lineups treated as true)",
          a["away"]["state"] == "ready" and "no lineups" not in json.loads(a["away"]["flags_json"]), f"{a['away']['state']} {a['away']['flags_json']}")
    check("no_football: the error is noted, not raised", "football" in (ec.kv_get("sync.last_error") or "").lower()
          or ec.kv_get("football.no_feed") is True, str(ec.kv_get("sync.last_error")))

    # the same weekend with no Polymarket match: the kickoff is Kalshi's expected expiration minus 3 h, flagged
    cfg2 = fresh("nofootball2")
    script2 = one_fixture(T0, 20)
    ctx2 = cards.Ctx(cfg2, fakes.FakeKalshi(script2["kalshi"]), fakes.FakeFootball({"raise": True}),
                     fakes.FakePoly({"reachable": True, "matches": []}), fakes.FakeModel(script2["model"]), fakes.FakeReasoner())
    cards.tick(ctx2, force_sync=True)
    fx2 = cards.fixtures_between(T0, T0 + timedelta(days=2))
    fj2 = cards.fixture_json(fx2[0]) if fx2 else {}
    a2 = by_outcome(fx2[0]["id"]) if fx2 else {}
    check("no_football: without Polymarket the kickoff is the expiration minus 3 h, source kalshi, flagged",
          bool(fx2) and fx2[0]["kickoff_utc"] == ec.iso(T0 + timedelta(hours=20)) and fj2.get("kickoff_source") == "kalshi"
          and "kickoff from Kalshi" in json.loads(a2["away"]["flags_json"]), f"{fx2} {fj2}")

    # the kickoff fallback when there is no strike_date: expiration minus the match length
    ev = {"event_ticker": "KXEPLGAME-26OCT18NFOARS", "title": "Nottingham Forest vs Arsenal",
          "markets": [{"ticker": "KXEPLGAME-26OCT18NFOARS-NFO", "yes_sub_title": "Nottingham Forest",
                       "expected_expiration_time": "2026-10-18T16:00:00Z", "close_time": "2026-10-18T16:30:00Z"},
                      {"ticker": "KXEPLGAME-26OCT18NFOARS-ARS", "yes_sub_title": "Arsenal", "close_time": "2026-10-18T16:00:00Z"},
                      {"ticker": "KXEPLGAME-26OCT18NFOARS-TIE", "yes_sub_title": "Tie"}]}
    p = cards.parse_event(ev)
    check("no_football: event parsing (codes, outcomes, kickoff = expected expiration minus Kalshi's 3 h margin)",
          p["tickers"] == {"home": "KXEPLGAME-26OCT18NFOARS-NFO", "away": "KXEPLGAME-26OCT18NFOARS-ARS", "draw": "KXEPLGAME-26OCT18NFOARS-TIE"}
          and p["kickoff_utc"] == "2026-10-18T13:00:00Z" and p["home_code"] == "NFO" and p["away_code"] == "ARS", str(p))
    ev2 = {"event_ticker": "KXEPLGAME-26OCT18NFOARS", "title": "Nottingham Forest vs Arsenal", "strike_date": "2026-10-18",
           "markets": [{"ticker": "KXEPLGAME-26OCT18NFOARS-NFO", "yes_sub_title": "Nottingham Forest"},
                       {"ticker": "KXEPLGAME-26OCT18NFOARS-ARS", "yes_sub_title": "Arsenal"},
                       {"ticker": "KXEPLGAME-26OCT18NFOARS-TIE", "yes_sub_title": "Tie"}]}
    p2 = cards.parse_event(ev2)
    check("no_football: with no expiration the strike date gives midnight UTC (Polymarket replaces it when it links)",
          p2["kickoff_utc"] == "2026-10-18T00:00:00Z" and p2["kickoff_source"] == "kalshi", str(p2))


def test_state_bundle(check):
    """The server's read shapes over the fakes, without a socket."""
    cfg = fresh("bundle")
    ctx = ctx_for(cfg, fakes.make_script(T0))
    server.CTX = ctx
    cards.tick(ctx, force_sync=True)
    b = server.state_bundle()
    check("bundle: the state bundle keys", all(k in b for k in ("rev", "now", "config", "halted", "halts", "cards", "record", "gate",
                                                                 "sync", "unlinked", "version")), str(sorted(b)))
    check("bundle: default cards window is now-3h to the listing lookahead (the 48 h fixture is on the page too)",
          {c["fixture_id"] for c in b["cards"]} == {1001, 1002, 1003}, str({c["fixture_id"] for c in b["cards"]}))
    check("bundle: the record summary has no ledger", "ledger" not in b["record"] and "bands" in b["record"])
    lst = server.cards_list({"day": ec.iso(T0 + timedelta(hours=48))[:10]})
    check("bundle: cards?day= filters by kickoff day", lst and all(c["fixture_id"] == 1001 for c in lst), str(len(lst)))
    lst = server.cards_list({"state": "ready"})
    check("bundle: cards?state= filters", lst and all(c["state"] == "ready" for c in lst) and len(lst) == 2, str(len(lst)))
    d = server.card_detail(lst[0]["id"])
    check("bundle: a card detail has snapshots and order", d and "snapshots" in d and "order" in d and d["snapshots"])
    h = server.health()
    check("bundle: health never carries key values", all(v is None or isinstance(v, str) and len(v) < 40 for v in h["keys"].values())
          and h["app"] == "Monarc Edge" and h["dry_run"] is True, str(h["keys"]))
    fx = [cards.fixture_json(f) for f in cards.fixtures_between(T0, T0 + timedelta(days=16))]
    check("bundle: fixtures carry kalshi_event, poly_slug and linked", len(fx) == 3 and all(f["kalshi_event"] and f["poly_slug"] and f["linked"] for f in fx), str(fx[:1]))
    status, payload = server.do_pass(lst[0]["id"])
    check("bundle: pass makes the card passed", status == 200 and payload["state"] == "passed" and payload["passed_at"])


TESTS = {"gate": test_gate, "mode_lock": test_mode_lock, "window": test_window, "approve_flow": test_approve_flow,
         "approve_repriced": test_approve_repriced, "busy_fail": test_busy_fail, "delisting": test_delisting,
         "settle_ledger": test_settle_ledger, "drawdown": test_drawdown, "reasoning_guard": test_reasoning_guard,
         "paper_counts": test_paper_counts, "no_football": test_no_football, "state_bundle": test_state_bundle}


def tests(check, names=None):
    for name, fn in TESTS.items():
        if names and name not in names:
            continue
        try:
            fn(check)
        except Exception as e:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(f"{name}: raised", False, f"{type(e).__name__}: {e}")
    ec.set_clock(None)


def cleanup():
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    fails, passes = [], [0]

    def check(name, ok, detail=""):
        if ok:
            passes[0] += 1
            print(f"ok   {name}")
        else:
            fails.append(name)
            print(f"FAIL {name}  {detail}")

    tests(check, sys.argv[1:] or None)
    print(f"\n{passes[0]} passed, {len(fails)} failed")
    sys.exit(1 if fails else 0)
