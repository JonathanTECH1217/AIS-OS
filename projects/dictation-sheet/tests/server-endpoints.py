"""Live checks of the running Dictation Sheet server on 127.0.0.1:8765 (read-only except a <2 s listener start/stop)."""
import json
import time

import requests

B = "http://127.0.0.1:8765"


def get(path, **params):
    t = time.time()
    try:
        r = requests.get(B + path, params=params or None, timeout=90)
    except Exception as exc:
        print(f"{path} {params}: EXCEPTION {type(exc).__name__}: {exc}  ({round((time.time() - t) * 1000)} ms)")
        return None, time.time() - t
    return r, time.time() - t


def post(path):
    t = time.time()
    r = requests.post(B + path, timeout=30)
    return r, time.time() - t


def show(label, r, dt):
    if r is None:
        return None
    try:
        j = r.json()
    except Exception:
        j = None
    keys = sorted(j.keys()) if isinstance(j, dict) else type(j).__name__
    print(f"{label}: {r.status_code} {round(dt * 1000)} ms ct={r.headers.get('content-type')} cc={r.headers.get('cache-control')} len={r.headers.get('content-length')} keys={keys}")
    if isinstance(j, dict):
        for k, v in j.items():
            s = repr(v)
            if len(s) > 110:
                s = s[:110] + f"... (len {len(v) if hasattr(v, '__len__') else '?'})"
            print(f"   {k} = {s}")
    return j


print("== plain endpoints ==")
show("/version", *get("/version"))
st = show("/listen/status", *get("/listen/status"))
f0 = show("/listen/frames?since=0", *get("/listen/frames", since=0))
show("/listen/frames?since=-5", *get("/listen/frames", since=-5))
show("/listen/frames?since=", *get("/listen/frames", since=""))
show("/listen/frames?since=abc (int() ValueError -> ?)", *get("/listen/frames", since="abc"))
show("/listen/frames?since=1e3", *get("/listen/frames", since="1e3"))
show("/listen/frames?since=99999999", *get("/listen/frames", since=99999999))
r, dt = post("/listen/nothing")
print(f"POST /listen/nothing: {r.status_code} cc={r.headers.get('cache-control')} body={r.text[:60]!r}")

print("\n== page routes and headers ==")
for p in ("/", "/callback?code=abc&state=x", "/nothing-here", "/Dictation%20Sheet.html", "/serve.py", "/README.txt", "/version?x=1"):
    r, dt = get(p)
    if r is not None:
        print(f"GET {p}: {r.status_code} {round(dt * 1000)} ms ct={r.headers.get('content-type')} cc={r.headers.get('cache-control')} len={len(r.content)} head={r.text[:40]!r}")

print("\n== /lyrics ==")
j = show("Blurry / Puddle of Mudd / 304", *get("/lyrics", track="Blurry", artist="Puddle of Mudd", duration=304))
if j and j.get("synced"):
    lines = [ln for ln in j["synced"].splitlines() if ln.strip()]
    print(f"   synced lines: {len(lines)}; first: {lines[0]!r}; has 'someone': {'someone' in j['synced']}")
    for ln in lines:
        if "someone" in ln:
            print(f"   line: {ln!r}")
show("Blurry / Puddle of Mudd / 100 (duration off -> /get 404 then /search)", *get("/lyrics", track="Blurry", artist="Puddle of Mudd", duration=100))
show("Blurry / no artist / no duration", *get("/lyrics", track="Blurry"))
show("Blurry / duration=abc", *get("/lyrics", track="Blurry", artist="Puddle of Mudd", duration="abc"))
show("nonsense song", *get("/lyrics", track="qzxv ploomp nothing", artist="nobody at all", duration=200))
show("instrumental (Eruption / Van Halen)", *get("/lyrics", track="Eruption", artist="Van Halen", duration=102))
show("empty track", *get("/lyrics", track="", artist="Puddle of Mudd", duration=304))
show("no params", *get("/lyrics"))
show("track with & and unicode", *get("/lyrics", track="Blurry & co ñ", artist="Puddle of Mudd"))

print("\n== listener: start, 1.5 s, frames, stop ==")
if st and st.get("ok"):
    r, dt = post("/listen/start")
    j1 = show("POST /listen/start", r, dt)
    time.sleep(1.5)
    r, dt = get("/listen/frames", since=0)
    fr = r.json()
    n, m = len(fr["frames"]), len(fr["mid"])
    now = time.time()
    print(f"   after 1.5 s: running={fr['running']} t0={fr['t0']} frames={n} mid={m} equal={n == m} err={fr['err']!r}")
    if fr["t0"]:
        print(f"   wall since t0: {now - fr['t0']:.3f} s -> expected ~{(now - fr['t0']) * 100:.0f} frames at 100 fps; got {n} (ratio {n / max(1e-9, (now - fr['t0']) * 100):.2f})")
        vals = fr["frames"]
        mids = fr["mid"]
        print(f"   low band: min {min(vals):.3f} max {max(vals):.3f}; mid band: min {min(mids):.3f} max {max(mids):.3f}; NaN? {any(v != v for v in vals + mids)}")
    r, dt = get("/listen/frames", since=n)
    fr2 = r.json()
    print(f"   since={n}: echoed since={fr2['since']} new frames={len(fr2['frames'])} mid={len(fr2['mid'])}")
    r, dt = post("/listen/stop")
    print(f"POST /listen/stop: {r.status_code} {r.text}")
    time.sleep(0.6)
    st2 = show("/listen/status after stop", *get("/listen/status"))
    print("\n== race: stop then start at once ==")
    r, dt = post("/listen/start")
    print(f"start: running={r.json()['running']}")
    time.sleep(0.8)
    r, dt = post("/listen/stop")
    r, dt = post("/listen/start")
    j3 = r.json()
    print(f"stop then start at once -> start answered running={j3['running']} count={j3['count']} err={j3['err']!r} ({round(dt * 1000)} ms)")
    time.sleep(0.6)
    st3 = get("/listen/status")[0].json()
    print(f"0.6 s later: running={st3['running']} count={st3['count']} t0={st3['t0']} err={st3['err']!r}")
    if st3["running"]:
        post("/listen/stop")
        time.sleep(0.5)
    st4 = get("/listen/status")[0].json()
    print(f"cleanup: running={st4['running']}")
else:
    print("listener not available:", st)
