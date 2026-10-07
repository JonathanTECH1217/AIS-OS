"""Monarc Edge checks (2026-10-04).

  python projects/edge/tests/run.py                 everything: the unit modules, demo, page
  python projects/edge/tests/run.py loop clients    just those unit modules (unit_loop.py, unit_clients.py)
  python projects/edge/tests/run.py unit            every unit_*.py
  python projects/edge/tests/run.py demo            the real Kalshi demo exchange (skipped without KALSHI_DEMO_API_KEY_ID)
  python projects/edge/tests/run.py page            the page tests (t-*.js) in headless Edge against a test server

unit    imports every projects/edge/tests/unit_*.py and calls its tests(check); a missing module is noted, not failed.
        The temp data folder and config are set before edge_common is imported, so nothing touches the real ones.
demo    balance, exchange status, open markets, a 1-contract resting order far from the ask then its cancel, then a
        1-contract crossing order and its fill, whose fee must match edge_common.kalshi_fee_usd. Real demo money
        (play dollars), real network.
page    starts scripts/edge_server.py on port 8801 with EDGE_TEST=1, a temp EDGE_DATA, a temp copy of config, the
        fakes (fakes.make_script, the clock frozen at the script's base time) and EDGE_NO_CLAUDE=1, polls api/health,
        then loads http://127.0.0.1:8801/?test=<name> for each t-*.js in headless Edge, reads PASS / FAIL / DONE from
        <pre id="__out">, saves tests/shots/<name>.png at 1536x780 and writes tests/out/report.json. With no t-*.js
        yet it reports "no page tests found" and passes. The server is killed with its tree in finally.
"""
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPTS = ROOT / "scripts"
PORT = 8801
URL = f"http://127.0.0.1:{PORT}/"
VIEWPORT = (1536, 780)          # his screen: 1920x1080 at 125 %

TMP = Path(tempfile.mkdtemp(prefix="edge-tests-"))
os.environ.setdefault("EDGE_DATA", str(TMP / "data"))
os.environ.setdefault("EDGE_CONFIG", str(TMP / "config.json"))
os.environ["EDGE_NO_CLAUDE"] = "1"
for p in (str(SCRIPTS), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

FAILS, PASSES = [], [0]


def check(name, ok, detail=""):
    if ok:
        PASSES[0] += 1
        print(f"ok   {name}" + (f"  ({detail})" if detail and len(str(detail)) < 80 else ""))
    else:
        FAILS.append(name)
        print(f"FAIL {name}  {detail}")


# ---------------------------------------------------------------- unit modules

def unit_modules():
    return sorted(p.stem for p in HERE.glob("unit_*.py"))


def run_unit(name):
    """One unit module by its short name ("loop") or full name ("unit_loop")."""
    mod_name = name if name.startswith("unit_") else f"unit_{name}"
    if not (HERE / f"{mod_name}.py").exists():
        print(f"note {mod_name}.py is not written yet, skipped")
        return
    print(f"--- {mod_name}")
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        check(f"{mod_name}: imports", False, f"{type(e).__name__}: {e}")
        return
    if not hasattr(mod, "tests"):
        check(f"{mod_name}: has tests(check)", False)
        return
    mod.tests(check)


def run_units():
    mods = unit_modules()
    for expected in ("unit_loop", "unit_clients", "unit_model"):
        if expected not in mods:
            print(f"note {expected}.py is not written yet, skipped")
    for m in mods:
        run_unit(m)


# ---------------------------------------------------------------- the demo exchange

def run_demo():
    print("--- demo")
    from outreach_common import load_env
    env, _ = load_env()
    if not env.get("KALSHI_DEMO_API_KEY_ID"):
        print("note KALSHI_DEMO_API_KEY_ID is not set, the demo exchange test is skipped")
        return
    try:
        from kalshi_api import Kalshi, KalshiError
    except Exception as e:  # noqa: BLE001
        check("demo: scripts/kalshi_api.py imports", False, f"{type(e).__name__}: {e}")
        return
    import edge_common as ec
    cfg = ec.load_config()
    k = Kalshi(env="demo", dry_run=False)
    check("demo: the demo client has a key", k.has_key)
    st = k.exchange_status()
    check("demo: exchange status answers", isinstance(st, dict) and "exchange_active" in st, str(st))
    bal = k.balance()
    check("demo: balance answers in dollars", isinstance(bal.get("usd"), (int, float)), str(bal))
    markets = k.markets(cfg["kalshi_series"], status="open")
    check("demo: open markets listed", isinstance(markets, list), f"{len(markets)} open")
    if not markets:
        print("note no open KXEPLGAME market on the demo exchange right now; the order checks are skipped")
        return
    m = max((x for x in markets if x.get("yes_ask") and x.get("yes_bid")), key=lambda x: x.get("volume") or 0, default=None)
    if not m:
        check("demo: a two-sided market to trade", False)
        return
    far = max(0.01, round(float(m["yes_bid"]) - 0.20, 2))
    coid = f"edge-test-rest-{int(time.time())}"
    o = k.create_order(m["ticker"], "yes", far, 1, coid)
    check("demo: a 1-contract order far from the ask rests", o.get("status") in ("resting", "pending") and o.get("fill_count", 0) == 0, str(o))
    time.sleep(1.0)
    c = k.cancel(o["order_id"], m["ticker"])
    o2 = k.order(o["order_id"])
    check("demo: the resting order cancels", o2.get("status") == "canceled" or c.get("status") == "canceled", str(o2))
    ask = float(m["yes_ask"])
    coid = f"edge-test-cross-{int(time.time())}"
    o = k.create_order(m["ticker"], "yes", ask, 1, coid, tif="immediate_or_cancel")
    deadline = time.time() + 20
    while time.time() < deadline and int(o.get("fill_count") or 0) < 1 and o.get("status") in ("resting", "pending"):
        time.sleep(1.0)
        o = k.order(o["order_id"])
    filled = int(o.get("fill_count") or 0) == 1
    check("demo: a 1-contract crossing order fills", filled, str(o))
    if filled:
        fills = k.fills(ticker=m["ticker"])
        f = next((x for x in fills if x.get("order_id") == o["order_id"]), None)
        if f:
            want = ec.kalshi_fee_usd(1, float(f["yes_price"]), float(cfg["fees"]["taker_rate"]))
            check("demo: the fee matches kalshi_fee_usd", abs(float(f.get("fee_usd") or 0) - want) < 0.005,
                  f"kalshi {f.get('fee_usd')} ours {want} at {f['yes_price']}")
        else:
            check("demo: the fill is listed", False, str(fills[:2]))
        try:
            k.create_order(m["ticker"], "no", float(m["no_ask"]), 1, f"edge-test-flat-{int(time.time())}",
                           tif="immediate_or_cancel")     # flatten: a No at the ask against our Yes
        except KalshiError as e:
            print(f"note could not flatten the demo position: {e}")


# ---------------------------------------------------------------- the page

def get(path, timeout=5):
    with urllib.request.urlopen(URL + path, timeout=timeout) as r:
        return json.loads(r.read())


def run_page():
    print("--- page")
    names = sorted(p.stem[2:] for p in HERE.glob("t-*.js"))
    if not names:
        print("note no page tests found (projects/edge/tests/t-*.js); only the server smoke checks run")
    import fakes
    from datetime import datetime, timezone
    base = datetime.now(timezone.utc).replace(microsecond=0)
    folder = TMP / "page"
    folder.mkdir(parents=True, exist_ok=True)
    scripts = fakes.write_scripts(folder, base)
    cfg_path = folder / "config.json"
    shutil.copy(ROOT / "projects" / "edge" / "config.json", cfg_path)
    env = dict(os.environ, EDGE_TEST="1", EDGE_DATA=str(folder / "data"), EDGE_CONFIG=str(cfg_path),
               EDGE_CLOCK=fakes._iso(base), EDGE_NO_CLAUDE="1", EDGE_TICK_SECONDS="3600",
               EDGE_FAKE_KALSHI=str(scripts["kalshi"]), EDGE_FAKE_FOOTBALL=str(scripts["football"]),
               EDGE_FAKE_POLY=str(scripts["poly"]), EDGE_FAKE_MODEL=str(scripts["model"]))
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "shots").mkdir(exist_ok=True)
    srv_log = open(HERE / "out" / "server.log", "w", encoding="utf-8")
    srv = subprocess.Popen([sys.executable, "-u", str(SCRIPTS / "edge_server.py"), "--port", str(PORT), "--no-open"],
                           env=env, stdout=srv_log, stderr=subprocess.STDOUT, cwd=str(ROOT))
    results, total_fail = {}, 0
    try:
        up = False
        for _ in range(60):
            try:
                get("api/health")
                up = True
                break
            except OSError:
                time.sleep(0.5)
        check("page: the test server answers api/health", up)
        if not up:
            return
        try:
            req = urllib.request.Request(URL + "api/tick", data=b"{}", method="POST", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                t = json.loads(r.read())
            check("page: one tick over the fakes ran", t.get("ran") is True, str(t.get("did"))[:120])
            st = get("api/state")
            check("page: the state bundle has cards from the fakes", len(st.get("cards") or []) >= 3 and st.get("gate") is not None,
                  f"{len(st.get('cards') or [])} cards")
            check("page: the clock is frozen at the script's base time (EDGE_TEST)", get("api/clock").get("fixed") is True)
        except OSError as e:
            check("page: the server smoke checks", False, str(e))
        if not names:
            return
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            for name in names:
                ctx = browser.new_context(viewport={"width": VIEWPORT[0], "height": VIEWPORT[1]})
                page = ctx.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "favicon" not in m.text
                        and "status of 409" not in m.text else None)
                page.goto(URL + f"?test={name}")
                text = ""
                deadline = time.time() + 90
                while time.time() < deadline:
                    try:
                        text = page.eval_on_selector("#__out", "e => e.textContent") or ""
                    except Exception:  # noqa: BLE001
                        text = ""
                    if "DONE" in text:
                        break
                    time.sleep(0.25)
                page.screenshot(path=str(HERE / "shots" / f"{name}.png"))
                lines = [l for l in text.splitlines() if l.strip()]
                fails = [l for l in lines if l.startswith("FAIL")]
                if "DONE" not in text:
                    fails.append("FAIL timeout (no DONE line)")
                for e in errors:
                    fails.append(f"FAIL page error: {e[:300]}")
                passes = [l for l in lines if l.startswith("PASS")]
                results[name] = {"pass": len(passes), "fail": fails}
                total_fail += len(fails)
                print(f"{'ok  ' if not fails else 'FAIL'} {name:14} {len(passes):3} passed" + (f", {len(fails)} failed" if fails else ""))
                for f in fails:
                    print("       " + f)
                    FAILS.append(f"page {name}: {f}")
                PASSES[0] += len(passes)
                ctx.close()
            browser.close()
        (HERE / "out" / "report.json").write_text(json.dumps(results, indent=1))
        print(f"page: {len(results)} tests, {total_fail} failed. Shots in {HERE / 'shots'}")
    finally:
        subprocess.run(["taskkill", "/PID", str(srv.pid), "/T", "/F"], capture_output=True)
        srv.wait()
        srv_log.close()


# ---------------------------------------------------------------- main

TESTS = {"unit": run_units, "demo": run_demo, "page": run_page}


def main():
    names = sys.argv[1:] or ["unit", "demo", "page"]
    for name in names:
        if name in TESTS:
            TESTS[name]()
        elif (HERE / f"unit_{name}.py").exists() or name.startswith("unit_"):
            run_unit(name)
        else:
            print(f"note no test named {name} (unit, demo, page, or a unit module: {', '.join(m[5:] for m in unit_modules())})")
    print(f"\n{PASSES[0]} passed, {len(FAILS)} failed")
    shutil.rmtree(TMP, ignore_errors=True)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
