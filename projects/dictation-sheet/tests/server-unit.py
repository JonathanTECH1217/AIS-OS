"""Unit tests of the built serve.py imported as a module: fetch_lyrics retry and fallback, listener_pid, running_version,
and the version-check logic of the shortcut flow (no server is started; the module's __main__ block does not run)."""
import email.message
import hashlib
import importlib.util
import json
import sys
import urllib.error

SERVE = r"C:\Users\sumre\Documents\Applications\Dictation Sheet\serve.py"
BUILD = r"C:\Users\sumre\Documents\GitHub\AIS-OS\projects\dictation-sheet\build_desktop.py"
sys.argv = ["serve.py", "--no-open"]

spec = importlib.util.spec_from_file_location("serve", SERVE)
serve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(serve)
print(f"imported serve: VERSION={serve.VERSION} PORT={serve.PORT} pyaudio={'yes' if serve.pyaudio else 'no'} np={'yes' if serve.np else 'no'} CAPTURE_WHY={serve.CAPTURE_WHY!r}")
print(f"LISTENER on import: running={serve.LISTENER.running} frames={len(serve.LISTENER.frames)} (a second Listener object, not the live one)")

# ---------- fetch_lyrics with a scripted urlopen ----------
import urllib.request

sleeps = []
real_sleep = serve.time.sleep
serve.time.sleep = lambda s: sleeps.append(s)
real_urlopen = urllib.request.urlopen


class FakeResp:
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def scripted(script):
    calls = []

    def urlopen(req, timeout=None):
        url = req.full_url
        calls.append((url.split("?")[0].rsplit("/", 1)[-1], url))
        step = script.pop(0)
        if isinstance(step, int):
            raise urllib.error.HTTPError(url, step, f"status {step}", email.message.Message(), None)
        if isinstance(step, Exception):
            raise step
        return FakeResp(step)

    urllib.request.urlopen = urlopen
    return calls


HIT = {"syncedLyrics": "[00:01.00] la", "plainLyrics": "la", "duration": 304.0, "trackName": "Blurry", "artistName": "Puddle of Mudd"}
NOSYNC = {"syncedLyrics": None, "plainLyrics": "la", "duration": 304.0, "trackName": "Blurry", "artistName": "Puddle of Mudd"}
Q = {"track": ["Blurry"], "artist": ["Puddle of Mudd"], "duration": ["304"]}


def case(name, script, q=Q, expect_ok=None):
    del sleeps[:]
    calls = scripted(list(script))
    out = serve.fetch_lyrics(dict(q))
    ok = out.get("ok")
    verdict = "" if expect_ok is None else ("PASS" if ok == expect_ok else "FAIL")
    print(f"{verdict:4} {name}: ok={ok} why={out.get('why', '')!r} calls={[c[0] for c in calls]} sleeps={sleeps} track={out.get('track')}")
    return out, calls


case("get 503 once then 200 (retry)", [503, HIT], expect_ok=True)
case("get 503 twice (retry then give up)", [503, 503], expect_ok=False)
case("get 404 then search 200 (fallback)", [404, [NOSYNC, HIT]], expect_ok=True)
case("get 404, search 503 once then 200", [404, 503, [HIT]], expect_ok=True)
case("get 200 without syncedLyrics -> search", [NOSYNC, [HIT]], expect_ok=True)
case("get 404, search empty list", [404, []], expect_ok=False)
case("get 429 (not retried)", [429, HIT], expect_ok=False)
case("get 500 then 200", [500, HIT], expect_ok=True)
case("URLError (network) not retried", [urllib.error.URLError("net down"), HIT], expect_ok=False)
case("TimeoutError not retried", [TimeoutError("timed out"), HIT], expect_ok=False)
case("search result with null duration", [404, [{"syncedLyrics": "[00:01.00] x", "duration": None, "trackName": "T", "artistName": "A"}]], expect_ok=True)
out, calls = case("search picks nearest duration", [404, [dict(HIT, duration=100.0, trackName="far"), dict(HIT, duration=300.0, trackName="near")]], expect_ok=True)
print("      picked:", out.get("track"), "(expect near)")
case("empty track: no call", [HIT], q={"track": [""], "artist": ["x"]}, expect_ok=False)
case("duration=abc -> 0, no duration param", [HIT], q={"track": ["Blurry"], "artist": ["x"], "duration": ["abc"]}, expect_ok=True)
out, calls = case("get 200 but body is null (hit None) -> search", [None, [HIT]], expect_ok=True)
out, calls = case("album passed through", [HIT], q={"track": ["Blurry"], "artist": ["x"], "album": ["Come Clean"], "duration": ["304.6"]}, expect_ok=True)
print("      get url:", calls[0][1])
urllib.request.urlopen = real_urlopen
serve.time.sleep = real_sleep

# ---------- listener_pid, running_version ----------
pid = serve.listener_pid()
print(f"\nlistener_pid() = {pid}")
ver = serve.running_version()
print(f"running_version() = {ver!r} (module VERSION {serve.VERSION!r}) match={ver == serve.VERSION}")

# ---------- is the built serve.py the same as build_desktop.py's SERVE_SRC? ----------
spec2 = importlib.util.spec_from_file_location("build_desktop", BUILD)
bd = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(bd)
src_ver = bd.server_version()
built = open(SERVE, encoding="utf-8").read()
expected = bd.SERVE_SRC.replace("__PORT__", str(bd.PORT)).replace("__VERSION__", src_ver)
print(f"build_desktop SERVE_SRC hash = {src_ver}; built file VERSION = {serve.VERSION}; running = {ver}; built text == SERVE_SRC render: {built == expected}")

# ---------- the shortcut's decision, replayed for a NEXT build with a different hash ----------
new_version = "0123456789"
ver_seen = serve.running_version()
decision = "launch only" if ver_seen == new_version else ("replace old server" if ver_seen == "old" else "MessageBox 'port in use by another program', exit 1")
print(f"next build (VERSION={new_version}) on top of running {ver_seen!r}: {decision}")

# ---------- netstat parsing on this machine ----------
import subprocess
out = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True, timeout=10).stdout
lines = [ln for ln in out.splitlines() if ":8765" in ln]
print("netstat lines with :8765:")
for ln in lines[:8]:
    print("   ", ln.strip())
print("netstat header:", [ln for ln in out.splitlines() if "Proto" in ln][:1])
if pid:
    ps = subprocess.run(["powershell", "-NoProfile", "-Command", f"(Get-Process -Id {pid}).ProcessName + ' ' + (Get-Process -Id {pid}).Path"], capture_output=True, text=True).stdout.strip()
    print("pid owner:", ps)
