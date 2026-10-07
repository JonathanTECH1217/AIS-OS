"""Monarc Edge local server (2026-10-04): the Kalshi Premier League betting agent behind the Desktop shortcut.

  python scripts/edge_server.py [--port 8800] [--no-open]

Serves the page (projects/edge/) and the JSON API in projects/edge/API.md. A loop thread runs one pass of
scripts/edge_cards.tick every EDGE_TICK_SECONDS (60). Clients are built from projects/edge/config.json at start:
Kalshi (env and dry_run from config; prod orders only once rehearsal_passed), API-Football, the Polymarket reader,
the model service (a missing CSV does not stop the server, it lands in sync.last_error) and the reasoning writer.
The Kalshi client is rebuilt when a config PUT changes env or dry_run. Opened hidden by scripts/edge_boot.pyw; log
in ~/.monarc/edge-server.log.

Test hooks: EDGE_TEST=1 adds the clock and fake routes; EDGE_DATA, EDGE_CONFIG, EDGE_CLOCK, EDGE_NO_CLAUDE,
EDGE_TICK_SECONDS; EDGE_FAKE_KALSHI, EDGE_FAKE_FOOTBALL, EDGE_FAKE_POLY, EDGE_FAKE_MODEL name JSON scripts and the
server builds the fakes from projects/edge/tests/fakes.py instead of the real clients. The config handler
(put_config) is a plain function so the tests can call it without a socket.
"""
import argparse
import gzip
import hashlib
import json
import mimetypes
import os
import socketserver
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edge_cards as cards  # noqa: E402
import edge_common as ec  # noqa: E402
import edge_ledger as ledger  # noqa: E402
import edge_reason  # noqa: E402
from studio_common import open_app, read_json  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent
TESTS_DIR = ec.EDGE_DIR / "tests"
CTYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
          ".mjs": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml",
          ".png": "image/png", ".jpg": "image/jpeg", ".ico": "image/x-icon", ".woff2": "font/woff2", ".ttf": "font/ttf",
          ".txt": "text/plain; charset=utf-8", ".md": "text/plain; charset=utf-8"}
VERSION_FILES = ("edge_server.py", "edge_common.py", "edge_cards.py", "edge_ledger.py", "edge_reason.py",
                 "edge_model.py", "edge_backtest.py", "kalshi_api.py", "api_football.py", "polymarket_read.py")
VERSION = hashlib.md5(b"".join((SCRIPTS / f).read_bytes() for f in VERSION_FILES if (SCRIPTS / f).exists())).hexdigest()[:10]
TICK_SECONDS = float(os.environ.get("EDGE_TICK_SECONDS") or 60)
PLACEHOLDER = ("<!doctype html><title>Monarc Edge</title><body style='font:16px system-ui;padding:32px;background:#0b1a12;"
               "color:#e6efe9'><h1>Monarc Edge</h1><p>The page files are not built yet. The API answers at "
               "<code>/api/health</code>.</p></body>")


# ---------------------------------------------------------------- change feed

class Feed:
    """A revision number the page long-polls; anything that changes the state bumps it."""

    def __init__(self):
        self.rev = 1
        self.cv = threading.Condition()
        self._last = 0
        self._pending = None

    def bump(self, throttle=0.0):
        now = time.time()
        if throttle and now - self._last < throttle:
            if self._pending is None:
                self._pending = threading.Timer(throttle - (now - self._last), self._fire)
                self._pending.daemon = True
                self._pending.start()
            return
        self._fire()

    def _fire(self):
        self._pending = None
        self._last = time.time()
        with self.cv:
            self.rev += 1
            self.cv.notify_all()

    def wait(self, since, timeout=25):
        with self.cv:
            if self.rev <= since:
                self.cv.wait(timeout)
            return self.rev


FEED = Feed()
CTX = None
BACKTEST = {"status": "idle", "started": None, "finished": None, "report_md": None, "report_path": None,
            "metrics": None, "error": None, "seasons": None}
_bt_lock = threading.Lock()


# ---------------------------------------------------------------- clients

def _fake(name):
    path = os.environ.get(f"EDGE_FAKE_{name.upper()}")
    if not path:
        return None
    sys.path.insert(0, str(TESTS_DIR))
    import fakes
    script = read_json(path, {}) or {}
    cls = {"kalshi": fakes.FakeKalshi, "football": fakes.FakeFootball, "poly": fakes.FakePoly, "model": fakes.FakeModel}[name]
    return cls(script)


def build_kalshi(cfg):
    fk = _fake("kalshi")
    if fk is not None:
        return fk
    try:
        from kalshi_api import Kalshi
        return Kalshi(env=cfg["env"], dry_run=bool(cfg["dry_run"]), allow_prod=bool(cfg.get("rehearsal_passed")))
    except Exception as e:  # noqa: BLE001
        cards.set_error(f"kalshi client: {type(e).__name__}: {e}")
        return None


def build_quotes(cfg):
    """Public market reads (events, markets, books) always come from the production exchange: the demo exchange's
    Premier League books are empty, so a card priced from demo would show 0 and 1. Orders still go to cfg env.
    With a fake Kalshi the fake answers both, so this returns None."""
    if _fake("kalshi") is not None:
        return None
    try:
        from kalshi_api import Kalshi
        return Kalshi(env="prod", dry_run=True)
    except Exception as e:  # noqa: BLE001
        cards.set_error(f"kalshi quotes client: {type(e).__name__}: {e}")
        return None


def build_ctx(cfg):
    kalshi = build_kalshi(cfg)
    football = _fake("football")
    if football is None:
        try:
            from api_football import Football
            football = Football()
        except Exception as e:  # noqa: BLE001
            cards.set_error(f"football client: {type(e).__name__}: {e}")
    poly = _fake("poly")
    if poly is None:
        try:
            import polymarket_read
            poly = polymarket_read
        except Exception as e:  # noqa: BLE001
            cards.set_error(f"polymarket reader: {type(e).__name__}: {e}")
    model = _fake("model")
    if model is None:
        try:
            from edge_model import ModelService
            model = ModelService(cfg)
        except Exception as e:  # noqa: BLE001
            cards.set_error(f"model service: {type(e).__name__}: {e}")
    return cards.Ctx(cfg, kalshi, football, poly, model, edge_reason.Reasoner(cfg), on_change=FEED.bump,
                     quotes=build_quotes(cfg))


# ---------------------------------------------------------------- config

def validate_patch(patch, base=None, path=""):
    """Unknown keys and wrong types against DEFAULTS. Keys starting with _ (the _about note) pass."""
    base = ec.DEFAULTS if base is None else base
    errors = []
    for k, v in patch.items():
        if str(k).startswith("_"):
            continue
        if k not in base:
            errors.append(f"Unknown key: {path}{k}")
            continue
        cur = base[k]
        if isinstance(cur, dict):
            if not isinstance(v, dict):
                errors.append(f"{path}{k} must be an object")
            else:
                errors += validate_patch(v, cur, f"{path}{k}.")
        elif isinstance(cur, bool):
            if not isinstance(v, bool):
                errors.append(f"{path}{k} must be true or false")
        elif isinstance(cur, (int, float)):
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                errors.append(f"{path}{k} must be a number")
        elif isinstance(cur, str):
            if not isinstance(v, str):
                errors.append(f"{path}{k} must be text")
    return errors


def put_config(body, ctx=None):
    """(status, payload) for PUT /api/config. Deep-merged, validated, locked as API.md says, saved."""
    ctx = ctx or CTX
    if not isinstance(body, dict):
        return 400, {"errors": ["Send a JSON object."]}
    errors = validate_patch(body)
    if errors:
        return 400, {"errors": errors}
    cur = ec.load_config()
    new = ec.deep_merge(cur, body)
    if new.get("env") not in ("demo", "prod"):
        return 400, {"errors": ["env must be demo or prod."]}
    if new.get("mode") not in ("approve", "auto"):
        return 400, {"errors": ["mode must be approve or auto."]}
    if body.get("mode") == "auto":
        g = ledger.gate(new)
        if not g["passed"]:
            return 409, {"errors": ["Auto mode is locked until the gate passes: " + "; ".join(g["reasons"])], "gate": g}
        if ec.kv_get("halted"):
            return 409, {"errors": ["Auto mode is locked while a halt is on."], "gate": g}
    if new.get("env") == "prod" and not new.get("dry_run") and not new.get("rehearsal_passed"):
        return 409, {"errors": ["Live orders on prod need rehearsal_passed (the seven-line checklist in the README)."]}
    ec.save_config(new)
    if ctx is not None:
        rebuild = (cur.get("env"), cur.get("dry_run")) != (new.get("env"), new.get("dry_run"))
        ctx.cfg.clear()
        ctx.cfg.update(new)
        if rebuild:
            ctx.kalshi = build_kalshi(new)
    FEED.bump()
    return 200, new


# ---------------------------------------------------------------- state

def key_labels():
    src = ec.key_sources()
    out = {}
    for label, names in src.items():
        out[label] = next((v for v in names.values() if v), None)
    return out


def football_remaining():
    f = CTX.football if CTX else None
    try:
        return getattr(f, "remaining", None) if f is not None else None
    except Exception:  # noqa: BLE001
        return None


def health():
    cfg = CTX.cfg if CTX else ec.load_config()
    return {"app": ec.APP, "version": VERSION, "env": cfg.get("env"), "mode": cfg.get("mode"),
            "dry_run": bool(cfg.get("dry_run")), "halted": bool(ec.kv_get("halted")), "keys": key_labels(),
            "football_remaining": football_remaining(),
            "busy": bool((CTX and CTX.busy) or BACKTEST["status"] == "running"), "rev": FEED.rev,
            "clock": ec.iso(ec.now())}


def sync_info():
    return {"fixtures_at": ec.kv_get("sync.fixtures_at"), "markets_at": ec.kv_get("sync.markets_at"),
            "open_markets": ec.kv_get("sync.open_markets"), "football_remaining": football_remaining(),
            "poly_ok": ec.kv_get("sync.poly_ok"), "last_error": ec.kv_get("sync.last_error")}


def state_bundle():
    cfg = CTX.cfg if CTX else ec.load_config()
    halted = bool(ec.kv_get("halted"))
    return {"rev": FEED.rev, "now": ec.iso(ec.now()), "config": cfg, "halted": halted, "halts": cards.halts(),
            "cards": [cards.card_json(r, halted) for r in cards.default_cards()],
            "record": ledger.record(cfg, full=False), "gate": ledger.gate(cfg), "sync": sync_info(),
            "account": ec.kv_get("account"),
            "unlinked": ec.kv_get("sync.unlinked") or [], "version": VERSION}


def cards_list(q):
    halted = bool(ec.kv_get("halted"))
    day, states = q.get("day"), q.get("state")
    if not day and not states:
        rows = cards.default_cards()
    else:
        where, params = [], []
        if day:
            where.append("substr(f.kickoff_utc, 1, 10) = ?")
            params.append(day)
        if states:
            names = [s.strip() for s in states.split(",") if s.strip()]
            where.append(f"c.state IN ({', '.join('?' * len(names))})")
            params += names
        rows = cards.cards_where(" AND ".join(where), tuple(params))
    return [cards.card_json(r, halted) for r in rows]


def card_detail(card_id):
    r = cards.get_card(card_id)
    if not r:
        return None
    out = cards.card_json(r)
    out["snapshots"] = ec.rows(ec.db().execute("SELECT * FROM snapshots WHERE ticker=? ORDER BY as_of DESC LIMIT 24",
                                               (r["ticker"],)))
    o = ec.db().execute("SELECT * FROM orders WHERE card_id=? ORDER BY created DESC LIMIT 1", (card_id,)).fetchone()
    out["order"] = dict(o) if o else None
    return out


def do_pass(card_id):
    r = cards.get_card(card_id)
    if not r:
        return 404, {"errors": ["No such card."]}
    if r["state"] not in ec.OPEN_STATES:
        return 409, {"errors": [f"This card is {r['state']}; only an open card can be passed."], "card": cards.card_json(r)}
    cards.update_card(card_id, state="passed", passed_at=ec.iso(ec.now()), decided_at=ec.iso(ec.now()))
    FEED.bump()
    return 200, cards.card_json(cards.get_card(card_id))


def do_cancel(card_id):
    r = cards.get_card(card_id)
    if not r:
        return 404, {"errors": ["No such card."]}
    if r["state"] not in ("placed", "partial") or not r.get("order_id"):
        return 409, {"errors": [f"This card is {r['state']}; there is no resting order."], "card": cards.card_json(r)}
    with CTX.lock:
        cards.cancel_order(CTX, r)
    FEED.bump()
    return 200, cards.card_json(cards.get_card(card_id))


def do_approve(card_id):
    card, errors = cards.approve(CTX, card_id, by="click")
    FEED.bump()
    if card:
        return 200, cards.card_json(card)
    r = cards.get_card(card_id)
    return (404 if not r else 409), {"errors": errors, "card": cards.card_json(r) if r else None}


def start_backtest(seasons):
    with _bt_lock:
        if BACKTEST["status"] == "running":
            return 409, {"errors": ["A backtest is already running."], **BACKTEST}
        BACKTEST.update({"status": "running", "started": ec.iso(ec.now()), "finished": None, "error": None,
                         "report_md": None, "report_path": None, "metrics": None, "seasons": seasons})

    def work():
        try:
            from edge_backtest import run_backtest
            r = run_backtest(seasons, progress=lambda *a: FEED.bump(1.0)) or {}
            BACKTEST.update({"status": "done", "report_md": r.get("report_md"), "report_path": str(r.get("report_path") or ""),
                             "metrics": {k: v for k, v in r.items() if k not in ("report_md", "report_path")}})
            try:
                c = ec.db()
                c.execute("INSERT INTO backtests (ts, params_json, metrics_json, path) VALUES (?,?,?,?)",
                          (ec.iso(ec.now()), json.dumps({"seasons": seasons}), ec.json_dumps(BACKTEST["metrics"]),
                           BACKTEST["report_path"]))
                c.commit()
            except Exception:  # noqa: BLE001
                traceback.print_exc()
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            BACKTEST.update({"status": "error", "error": f"{type(e).__name__}: {e}"[:600]})
        BACKTEST["finished"] = ec.iso(ec.now())
        FEED.bump()

    threading.Thread(target=work, daemon=True).start()
    FEED.bump()
    return 200, dict(BACKTEST)


# ---------------------------------------------------------------- http

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        status = str(args[1]) if len(args) > 1 else ""
        if not status.isdigit() or int(status) < 400:
            return
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def handle(self):
        try:
            super().handle()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def _send(self, status, data, ctype, extra=None):
        try:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            self.close_connection = True

    def _json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        if len(data) > 4096 and "gzip" in (self.headers.get("Accept-Encoding") or ""):
            return self._send(status, gzip.compress(data, 5), "application/json; charset=utf-8", {"Content-Encoding": "gzip"})
        self._send(status, data, "application/json; charset=utf-8")

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except ValueError:
            return {}

    def _file(self, file):
        data = file.read_bytes()
        ctype = CTYPES.get(file.suffix.lower()) or mimetypes.guess_type(str(file))[0] or "application/octet-stream"
        self._send(200, data, ctype, {"Cache-Control": "no-cache"})

    def _static(self, path):
        rel = "index.html" if path in ("", "/") else unquote(path.lstrip("/"))
        if rel == "favicon.ico":                      # the browser asks by itself; the boot script's icon, else nothing
            ico = ec.EDGE_DIR / "monarc-edge.ico"
            return self._file(ico) if ico.is_file() else self._send(204, b"", "image/x-icon")
        file = (ec.EDGE_DIR / rel).resolve()
        if rel == "index.html" and not file.is_file():
            return self._send(200, PLACEHOLDER.encode("utf-8"), "text/html; charset=utf-8")
        if not file.is_relative_to(ec.EDGE_DIR.resolve()) or not file.is_file() or "data" in file.relative_to(ec.EDGE_DIR.resolve()).parts[:1]:
            return self._send(404, b"not found", "text/plain")
        return self._file(file)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if not u.path.startswith("/api/"):
            return self._static(u.path)
        p = u.path[len("/api/"):].strip("/")
        try:
            if p == "health":
                return self._json(200, health())
            if p == "state":
                since = int(q.get("since", 0) or 0)
                if since:
                    FEED.wait(since, timeout=min(25, float(q.get("wait", 25))))
                return self._json(200, state_bundle())
            if p == "config":
                return self._json(200, CTX.cfg if CTX else ec.load_config())
            if p == "cards":
                return self._json(200, cards_list(q))
            if p.startswith("cards/"):
                d = card_detail(unquote(p[len("cards/"):]))
                return self._json(200, d) if d else self._json(404, {"errors": ["No such card."]})
            if p == "record":
                return self._json(200, ledger.record(CTX.cfg, full=True))
            if p == "gate":
                return self._json(200, ledger.gate(CTX.cfg))
            if p == "backtest":
                return self._json(200, dict(BACKTEST))
            if p == "fixtures":
                now = ec.now()
                look = int(CTX.cfg["window"]["listing_lookahead_days"])
                from datetime import timedelta
                rows = cards.fixtures_between(now - timedelta(hours=3), now + timedelta(days=look))
                return self._json(200, [cards.fixture_json(f) for f in rows])
            if p == "clock" and ec.TEST_MODE:
                return self._json(200, {"clock": ec.iso(ec.now()), "fixed": ec._clock["fixed"] is not None})
            return self._json(404, {"errors": ["Unknown endpoint."]})
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            return self._json(500, {"errors": [f"{type(e).__name__}: {e}"]})

    def do_PUT(self):
        u = urlparse(self.path)
        p = u.path[len("/api/"):].strip("/") if u.path.startswith("/api/") else ""
        try:
            if p == "config":
                status, payload = put_config(self._body())
                return self._json(status, payload)
            return self._json(404, {"errors": ["Unknown endpoint."]})
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            return self._json(500, {"errors": [f"{type(e).__name__}: {e}"]})

    def do_POST(self):
        u = urlparse(self.path)
        p = u.path[len("/api/"):].strip("/") if u.path.startswith("/api/") else ""
        try:
            body = self._body()
            if p.startswith("cards/"):
                parts = p.split("/")
                if len(parts) == 3:
                    cid, action = unquote(parts[1]), parts[2]
                    if action == "approve":
                        return self._json(*do_approve(cid))
                    if action == "pass":
                        return self._json(*do_pass(cid))
                    if action == "cancel":
                        return self._json(*do_cancel(cid))
            if p == "backtest":
                seasons = body.get("seasons") if isinstance(body, dict) else None
                if not seasons or not isinstance(seasons, list):
                    return self._json(400, {"errors": ["Send {seasons: [\"2122\", ...]}."]})
                return self._json(*start_backtest([str(s) for s in seasons]))
            if p == "tick":
                r = cards.tick(CTX, force_sync=bool(isinstance(body, dict) and body.get("sync")))
                FEED.bump()
                return self._json(200, {"ran": True, **r})
            if p == "halt/clear":
                cards.clear_halt(CTX)
                FEED.bump()
                return self._json(200, {"halted": False})
            if p == "halt" and ec.TEST_MODE:
                cards.halt(CTX, body.get("reason") or "manual", body.get("detail") or "")
                return self._json(200, {"halted": True})
            if p == "clock" and ec.TEST_MODE:
                iso_ = body.get("iso") if isinstance(body, dict) else None
                ec.set_clock(iso_)
                FEED.bump()
                return self._json(200, {"clock": ec.iso(ec.now()), "fixed": iso_ is not None})
            if p.startswith("fake/") and ec.TEST_MODE:
                name = p[len("fake/"):]
                client = {"kalshi": CTX.kalshi, "football": CTX.football, "poly": CTX.poly, "model": CTX.model}.get(name)
                if client is None or not hasattr(client, "load"):
                    return self._json(400, {"errors": [f"{name} is not a fake in this server."]})
                client.load(body)
                FEED.bump()
                return self._json(200, {"ok": True, "name": name})
            return self._json(404, {"errors": ["Unknown endpoint."]})
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            return self._json(500, {"errors": [f"{type(e).__name__}: {e}"]})


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False


def loop():
    """One pass at start, then one every TICK_SECONDS."""
    while True:
        try:
            cards.tick(CTX)
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        FEED.bump()
        time.sleep(TICK_SECONDS)


def main():
    global CTX
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=ec.PORT)
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--no-loop", action="store_true", help="tests: no loop thread, ticks only on POST /api/tick")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    ec.ensure_dirs()
    if os.environ.get("EDGE_CLOCK"):
        ec.set_clock(os.environ["EDGE_CLOCK"])
    cfg = ec.load_config()
    CTX = build_ctx(cfg)
    ledger.init_bankroll(cfg)
    socketserver.TCPServer.allow_reuse_address = False
    try:
        httpd = Server(("127.0.0.1", args.port), Handler)
    except OSError as e:
        sys.exit(f"Port {args.port} is busy ({e}).")
    if not args.no_loop:
        threading.Thread(target=loop, daemon=True).start()
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Monarc Edge at {url}  (data {ec.DATA}, version {VERSION})", flush=True)
    if not args.no_open:
        threading.Timer(0.6, lambda: open_app(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
