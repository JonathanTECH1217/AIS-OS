"""Monarc Edge install and reachability check (2026-10-04).

  python scripts/edge_check.py        every check, OK / FAIL per line; exit 1 on a hard failure

Keys (source labels only, never values), Kalshi demo and prod public reachability and exchange status, the open
KXEPLGAME market count, the API-Football quota (or "no key"), Polymarket reachability, the imports the loop needs,
port 8800, teams.json (present, every row with kalshi and fd), and a writable data folder. A missing paid key is a
note, not a failure: the loop runs without it. Run it from his IP before the rehearsal (Polymarket geoblocks).
"""
import importlib
import json
import socket
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edge_common as ec  # noqa: E402

KALSHI_BASES = {"demo": "https://demo-api.kalshi.co/trade-api/v2", "prod": "https://api.elections.kalshi.com/trade-api/v2"}
UA = "MonarcEdge/1.0 (edge_check)"
FAILS = []


def line(ok, name, detail="", hard=True):
    print(f"{'OK  ' if ok else ('FAIL' if hard else 'note')}  {name}{('  ' + detail) if detail else ''}")
    if not ok and hard:
        FAILS.append(name)


def get_json(url, headers=None, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def kalshi_base(env):
    try:
        from kalshi_api import Kalshi
        return Kalshi(env=env, dry_run=True).base
    except Exception:  # noqa: BLE001
        return KALSHI_BASES[env]


def checks():
    cfg = ec.load_config()
    src = ec.key_sources()
    for label, names in src.items():
        have = {n: s for n, s in names.items() if s}
        ok = len(have) == len(names)
        line(ok, f"key {label}", ", ".join(f"{n} from {s}" for n, s in have.items()) or "not set", hard=False)
    # the account itself: a key that the exchange accepts, demo or prod (orders stay dry-run either way)
    accounts = 0
    try:
        from kalshi_api import Kalshi, KalshiError
        for env in ("demo", "prod"):
            k = Kalshi(env=env, dry_run=True)
            if not k.has_key:
                line(False, f"kalshi {env} account", k.key_error or "no key", hard=False)
                continue
            try:
                b = k.balance()
                line(True, f"kalshi {env} account", f"key accepted, balance ${float(b.get('usd') or 0):,.2f}")
                accounts += 1
            except KalshiError as e:
                line(False, f"kalshi {env} account", f"key refused: {e.status} {str(e.message)[:80]}", hard=False)
    except Exception as e:  # noqa: BLE001
        line(False, "kalshi account", f"{type(e).__name__}: {e}", hard=False)
    line(accounts > 0, "kalshi account key (demo or prod)", f"{accounts} exchange(s) accept a key" if accounts else
         "no exchange accepts a key: paper cards still run, settlements read from the markets, no orders possible")
    for env in ("demo", "prod"):
        base = kalshi_base(env)
        try:
            st = get_json(base + "/exchange/status")
            line(True, f"kalshi {env} reachable", f"exchange_active={st.get('exchange_active')} trading_active={st.get('trading_active')}")
        except Exception as e:  # noqa: BLE001
            line(False, f"kalshi {env} reachable", f"{type(e).__name__}: {e}", hard=(env == "demo"))
    try:
        base = kalshi_base("prod")
        data = get_json(f"{base}/markets?series_ticker={cfg['kalshi_series']}&status=open&limit=200")
        n = len(data.get("markets") or [])
        line(True, f"open {cfg['kalshi_series']} markets (prod, public)", str(n))
    except Exception as e:  # noqa: BLE001
        line(False, f"open {cfg['kalshi_series']} markets (prod, public)", f"{type(e).__name__}: {e}", hard=False)
    from outreach_common import load_env
    env, _ = load_env()
    fkey = env.get("API_FOOTBALL_KEY")
    if fkey:
        try:
            st = get_json("https://v3.football.api-sports.io/status", headers={"x-apisports-key": fkey})
            req = (st.get("response") or {}).get("requests") or {}
            line(True, "api-football quota", f"{req.get('current')} of {req.get('limit_day')} today")
        except Exception as e:  # noqa: BLE001
            line(False, "api-football quota", f"{type(e).__name__}: {e}", hard=False)
    else:
        line(False, "api-football quota", "no key (the loop runs from the Kalshi events alone)", hard=False)
    try:
        import polymarket_read
        ok = bool(polymarket_read.reachable())
        line(ok, "polymarket reachable", "" if ok else str(getattr(polymarket_read, "LAST_ERROR", "")), hard=False)
    except Exception:  # noqa: BLE001
        try:
            get_json("https://gamma-api.polymarket.com/events?limit=1")
            line(True, "polymarket reachable", "gamma-api answers (polymarket_read.py not present)")
        except Exception as e:  # noqa: BLE001
            line(False, "polymarket reachable", f"{type(e).__name__}: {e}", hard=False)
    for mod in ("requests", "numpy", "anthropic", "playwright", "PIL"):
        try:
            m = importlib.import_module(mod)
            line(True, f"import {mod}", getattr(m, "__version__", ""))
        except Exception as e:  # noqa: BLE001
            line(False, f"import {mod}", str(e))
    for mod in ("edge_common", "edge_cards", "edge_ledger", "edge_reason", "edge_server", "kalshi_api", "api_football",
                "polymarket_read", "edge_model", "edge_backtest"):
        try:
            importlib.import_module(mod)
            line(True, f"import {mod}")
        except Exception as e:  # noqa: BLE001
            line(False, f"import {mod}", f"{type(e).__name__}: {e}")
    s = socket.socket()
    try:
        s.settimeout(0.5)
        busy = s.connect_ex(("127.0.0.1", ec.PORT)) == 0
    finally:
        s.close()
    line(True, f"port {ec.PORT}", "in use (Edge running?)" if busy else "free")
    teams = ec.load_teams()
    if not ec.TEAMS.exists():
        line(False, "teams.json", f"missing: {ec.TEAMS}")
    else:
        bad = [t.get("name") for t in teams if not (t.get("kalshi") and t.get("fd"))]
        line(bool(teams) and not bad, "teams.json rows have kalshi and fd", f"{len(teams)} teams" + (f", missing on: {bad}" if bad else ""))
    try:
        ec.ensure_dirs()
        probe = ec.DATA / ".write-check"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        line(True, "data folder writable", str(ec.DATA))
    except OSError as e:
        line(False, "data folder writable", f"{ec.DATA}: {e}")
    print(f"\n{'All checks passed.' if not FAILS else str(len(FAILS)) + ' failed: ' + ', '.join(FAILS)}")


if __name__ == "__main__":
    checks()
    sys.exit(1 if FAILS else 0)
