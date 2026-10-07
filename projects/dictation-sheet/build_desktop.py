"""Build the desktop copy of Dictation Sheet.

Run from anywhere:
    python projects/dictation-sheet/build_desktop.py

What it does
- Reads index.html (the one source of truth, also published to claude.ai).
- Inlines VexFlow, Hyphenator and its English patterns, and the Google Fonts
  files, so the desktop copy works with no internet. Downloads are cached in
  vendor/ (gitignored); delete that folder to refetch.
- Wraps the page fragment in a full HTML document.
- Writes Documents\\Applications\\Dictation Sheet\\ (page, icon, README).
- Rebuilds the desktop shortcut so Edge opens the page in app mode
  (own window, no address bar).
"""

import base64
import re
import subprocess
import sys
from pathlib import Path

import requests
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SRC = HERE / "index.html"
VENDOR = HERE / "vendor"
OUT_DIR = Path.home() / "Documents" / "Applications" / "Dictation Sheet"
OUT_HTML = OUT_DIR / "Dictation Sheet.html"
ICO = OUT_DIR / "Dictation Sheet.ico"
README = OUT_DIR / "README.txt"
SERVE = OUT_DIR / "serve.py"
PORT = 8765
DESKTOP_LNK = Path.home() / "Desktop" / "Dictation Sheet.lnk"
SHEET_DIR = Path.home() / "Documents" / "Sheet Music"
BROWSERS = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
ARTIFACT_URL = "https://claude.ai/artifact/Lx7YY58MDePpDa6hJ4vi1v"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>:root{color-scheme:light dark}body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>
"""
TAIL = "\n</body>\n</html>\n"

README_TEXT = f"""Dictation Sheet
===============

Open it from the desktop shortcut (Edge, own window) or double-click
"Dictation Sheet.html" to open it in any browser.

What it does
- Paste lyrics, press "Split into syllables".
- Fill in length, drum hits, solfege, note in key, and the guitar / piano /
  bass position for every syllable.
- Real notation draws under every line. Copy as text or print.

Saving
- The sheet you are working on stays in the browser between openings.
- Ctrl+S saves the sheet as a .json file in Documents\\Sheet Music. The first
  time, Edge asks you to pick that folder once; after that it saves silently.
  File, Save as picks a different file. File, Open file opens from the folder.
- For sheets that save to the cloud and can be edited by others, use the
  online copy: {ARTIFACT_URL}

Spotify
- The shortcut starts a tiny local server (serve.py) and opens the app at
  http://127.0.0.1:{PORT}/ so Spotify's login can come back to it. An older
  copy of the server left running from before a rebuild is replaced by the
  shortcut, so the lyrics lookup and the listener's voice band are always
  the current ones.
- Make a free app at developer.spotify.com, add the redirect URI
  http://127.0.0.1:{PORT}/callback, and paste its Client ID under Play.
- Spotify Premium is needed for remote control. Spotify plays at full speed.

- Lock to the song: while a Spotify song plays through the app, the local
  server reads the computer's own sound output (the sound card's loopback),
  keeps only a loudness curve, finds the beats, and the metronome follows
  them. Needs two Python packages once:  pip install pyaudiowpatch numpy
  Without them the app offers Listen, which asks to share the screen's audio.
- Place words: fetches the song's words from lrclib.net (a free, open lyrics
  database) through the local server, then fits them to the song's sound with
  a speech model (align.py, next to serve.py): every word cut into syllables
  from the CMU pronouncing dictionary, every syllable given the moment it is
  sung and the moment it stops, the beats read for the tempo and bar 1. With
  an attached file this runs at once; with a Spotify song the song plays
  through first while the server records the sound card (kept in memory for
  that run only). Needs, once:
      pip install torch torchaudio librosa soundfile cmudict pyphen
  The first run also fetches the speech model (about 360 MB). Without these
  the app falls back to reading the song's loudness, which is far rougher.
  Gaps draw as rests; a held note can run up to four bars, tied over the bar
  lines. Ctrl+Z undoes the whole fill in one step; Place words can be pressed
  again any time.

Works offline for everything except Spotify. Fonts, the notation drawer
(VexFlow) and the syllable splitter (Hyphenator) are built into the file.

Source of truth and rebuild:
  Documents\\GitHub\\AIS-OS\\projects\\dictation-sheet\\index.html
  python projects/dictation-sheet/build_desktop.py
"""


def fetch(url: str, cache_name: str) -> bytes:
    p = VENDOR / cache_name
    if p.exists():
        return p.read_bytes()
    r = requests.get(url, headers={"User-Agent": UA}, timeout=90)
    r.raise_for_status()
    VENDOR.mkdir(exist_ok=True)
    p.write_bytes(r.content)
    return r.content


def cache_name(url: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", url.split("://", 1)[1])


def inline_scripts(html: str) -> tuple[str, int]:
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        url = m.group(1)
        js = fetch(url, cache_name(url)).decode("utf-8")
        js = js.replace("</script", "<\\/script")
        count += 1
        return f"<script>/* inlined from {url} */\n{js}\n</script>"

    html = re.sub(r'<script src="(https://[^"]+)"></script>', repl, html)
    return html, count


def inline_fonts(html: str) -> tuple[str, int]:
    m = re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com/[^"]+)">', html)
    if not m:
        return html, 0
    css_url = m.group(1).replace("&amp;", "&")
    css = fetch(css_url, "google-fonts.css").decode("utf-8")
    count = 0

    def repl(u: re.Match) -> str:
        nonlocal count
        url = u.group(1)
        data = fetch(url, cache_name(url))
        count += 1
        ext = url.rsplit(".", 1)[-1].lower()
        mime = {"woff2": "font/woff2", "woff": "font/woff", "ttf": "font/ttf"}.get(ext, "application/octet-stream")
        return f"url(data:{mime};base64,{base64.b64encode(data).decode('ascii')})"

    css = re.sub(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", repl, css)
    html = html.replace(m.group(0), f"<style>/* Google Fonts, inlined */\n{css}\n</style>")
    html = re.sub(r'<link rel="preconnect"[^>]*>\n?', "", html)
    return html, count


def wrap(fragment: str) -> str:
    i = fragment.index("</style>") + len("</style>")
    return HEAD + fragment[:i] + "\n</head>\n<body>" + fragment[i:] + TAIL


def draw_icon(path: Path) -> None:
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    paper, ink, accent = (243, 244, 239, 255), (27, 31, 26, 255), (44, 95, 134, 255)
    d.rounded_rectangle((8, 8, size - 8, size - 8), radius=44, fill=paper)
    # five staff lines
    for k in range(5):
        y = 78 + k * 22
        d.line((40, y, size - 40, y), fill=ink, width=4)
    # a quarter note: head on the third space, stem up
    d.ellipse((92, 130, 140, 166), fill=accent)
    d.rectangle((134, 64, 142, 148), fill=accent)
    img.save(path, format="ICO", sizes=[(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)])


SERVE_SRC = '''"""Local server for Dictation Sheet.

Serves the app folder at http://127.0.0.1:PORT/ so Spotify's login can return
to the page, then opens the app in Edge's app mode. If the server is already
running it only opens the window. Started by the desktop shortcut.
"""
import http.server
import json
import os
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path

PORT = __PORT__
VERSION = "__VERSION__"
HERE = Path(__file__).resolve().parent
PAGE = "/" + urllib.parse.quote("Dictation Sheet.html")
URL = f"http://127.0.0.1:{PORT}/"
BROWSERS = [
    Path(r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"),
    Path(r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"),
    Path(r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"),
]

try:
    import numpy as np
    import pyaudiowpatch as pyaudio
    CAPTURE_WHY = ""
except Exception as exc:  # the app falls back to the browser's own capture
    np = None
    pyaudio = None
    CAPTURE_WHY = str(exc)


class Listener:
    """Reads what the computer is playing (the sound card's loopback) and keeps a loudness curve of the low band,
    100 frames a second, so the app can find the beats of whatever is on. No audio is stored or written anywhere."""

    FPS = 100

    def __init__(self):
        self.lock = threading.Lock()
        self.frames = []
        self.mid = []
        self.t0 = None
        self.running = False
        self.err = ""
        self.stop_flag = False
        self.device = ""
        # the sound itself is kept only when Place words asks for it (record), in memory, for the fit; never written
        self.record = False
        self.rec = []
        self.rec_rate = 0

    def start(self, record=False):
        with self.lock:
            if self.running:
                return
            self.frames = []
            self.mid = []
            self.t0 = None
            self.err = ""
            self.stop_flag = False
            self.running = True
            self.record = bool(record)
            self.rec = []
            self.rec_rate = 0
        threading.Thread(target=self.run, daemon=True).start()

    def recording(self):
        """The captured mono samples so far (device rate) and the wall-clock time of the first, or None."""
        with self.lock:
            if not self.rec:
                return None
            return np.concatenate(self.rec), self.rec_rate, self.t0

    def stop(self):
        self.stop_flag = True

    def run(self):
        try:
            p = pyaudio.PyAudio()
            dev = p.get_default_wasapi_loopback()
            self.device = dev["name"]
            rate = int(dev["defaultSampleRate"])
            ch = max(1, int(dev["maxInputChannels"]))
            hop = rate // self.FPS
            chunk = hop * 4
            # two box filters whose first nulls sit on the app's own click tones (1000 and 800 Hz), so the metronome
            # never counts as a drum hit; kick and snare live far below
            n1, n2 = max(1, round(rate / 1000)), max(1, round(rate / 800))
            k1 = np.ones(n1, dtype=np.float32) / n1
            k2 = np.ones(n2, dtype=np.float32) / n2
            # the voice band, roughly 250 to 3500 Hz, for where the syllables start
            nh, nl = max(1, round(rate / 3500)), max(1, round(rate / 250))
            kh = np.ones(nh, dtype=np.float32) / nh
            kl = np.ones(nl, dtype=np.float32) / nl
            pad = n1 + n2 + nl
            tail = np.zeros(pad, dtype=np.float32)
            stream = p.open(format=pyaudio.paFloat32, channels=ch, rate=rate, input=True, input_device_index=dev["index"], frames_per_buffer=chunk)
            while not self.stop_flag:
                data = stream.read(chunk, exception_on_overflow=False)
                now = time.time()
                x = np.frombuffer(data, dtype=np.float32)
                if ch > 1:
                    x = x.reshape(-1, ch).mean(axis=1)
                if self.t0 is None:
                    self.t0 = now - len(x) / rate
                if self.record:
                    with self.lock:
                        self.rec.append(x.copy())
                        self.rec_rate = rate
                buf = np.concatenate([tail, x])
                low = np.convolve(np.convolve(buf, k1, mode="same"), k2, mode="same")[pad:]
                voice = (np.convolve(buf, kh, mode="same") - np.convolve(buf, kl, mode="same"))[pad:]
                vals = []
                mids = []
                for i in range(len(x) // hop):
                    seg = low[i * hop:(i + 1) * hop]
                    vals.append(float(np.log1p(100.0 * float(np.sqrt(np.mean(seg * seg))))))
                    seg2 = voice[i * hop:(i + 1) * hop]
                    mids.append(float(np.log1p(100.0 * float(np.sqrt(np.mean(seg2 * seg2))))))
                tail = x[-pad:]
                with self.lock:
                    self.frames.extend(vals)
                    self.mid.extend(mids)
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as exc:
            self.err = str(exc)
        with self.lock:
            self.running = False

    def status(self):
        with self.lock:
            return {"ok": pyaudio is not None, "why": CAPTURE_WHY, "running": self.running, "t0": self.t0, "fps": self.FPS, "count": len(self.frames), "err": self.err, "device": self.device, "record": self.record, "recorded": (sum(len(r) for r in self.rec) / self.rec_rate) if self.rec_rate else 0}

    def frames_since(self, since):
        with self.lock:
            return {"ok": True, "running": self.running, "t0": self.t0, "fps": self.FPS, "since": since, "frames": self.frames[since:], "mid": self.mid[since:], "err": self.err}


LISTENER = Listener()

# ---------- the fit: the words placed in the song by the speech model (align.py, next to this file) ----------
sys.path.insert(0, str(HERE))
ALIGN = None
ALIGN_WHY = ""
ALIGN_JOB = None
UPLOAD = HERE / ".place-words-upload"


def get_align():
    """The fitting module, imported once; None with the reason when its tools are missing."""
    global ALIGN, ALIGN_WHY, ALIGN_JOB
    if ALIGN is None and not ALIGN_WHY:
        try:
            import align as mod
            ok, why = mod.available()
            if not ok:
                ALIGN_WHY = why
            else:
                ALIGN = mod
                ALIGN_JOB = mod.Job()
        except Exception as exc:
            ALIGN_WHY = str(exc)
    return ALIGN


def align_status():
    mod = get_align()
    return {"ok": True, "available": mod is not None, "why": ALIGN_WHY, "job": ALIGN_JOB.status() if ALIGN_JOB else None, "recorded": LISTENER.status().get("recorded", 0)}


def align_run(req):
    """Start the fit as a background job. req: {lines: [...], source: 'upload' | 'capture'}. Returns at once."""
    mod = get_align()
    if mod is None:
        return {"ok": False, "why": ALIGN_WHY or "the fitting tools are not installed"}
    lines = [str(x) for x in (req.get("lines") or [])]
    if not lines:
        return {"ok": False, "why": "no lines of words"}
    src = req.get("source") or "upload"
    # each line's start from the timed lyrics, in seconds of the recording (start = the song second of its first sample)
    try:
        start = float(req.get("start") or 0)
        stamps = [float(t) - start for t in (req.get("stamps") or [])]
    except (TypeError, ValueError):
        stamps = []
    if len(stamps) != len(lines):
        stamps = None
    try:
        if src == "capture":
            got = LISTENER.recording()
            if got is None:
                return {"ok": False, "why": "nothing has been recorded: play the song through with Place words listening first"}
            samples, rate, t0 = got
            wave = mod.from_pcm(samples, rate)
        else:
            if not UPLOAD.is_file():
                return {"ok": False, "why": "no song file was uploaded"}
            wave = mod.load_audio(str(UPLOAD))
    except Exception as exc:
        return {"ok": False, "why": "could not read the sound: %s" % exc}
    if len(wave) < mod.SR * 2:
        return {"ok": False, "why": "the sound is too short to fit words to"}
    if not ALIGN_JOB.start(wave, lines, stamps):
        return {"ok": False, "why": "a fit is already running"}
    return {"ok": True, "seconds": len(wave) / mod.SR, "stamps": stamps is not None}


def capture_wav():
    """The sound the listener recorded, as a 16 kHz mono WAV in memory (for looking into a fit that went wrong), or None."""
    got = LISTENER.recording()
    mod = get_align()
    if got is None or mod is None:
        return None
    import io
    import wave as wavmod
    samples, rate, _ = got
    x = mod.from_pcm(samples, rate)
    pcm = np.clip(x * 32767.0, -32768, 32767).astype("<i2").tobytes()
    buf = io.BytesIO()
    with wavmod.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(mod.SR)
        w.writeframes(pcm)
    return buf.getvalue()


def fetch_lyrics(q):
    """Timed lyrics for a song from LRCLIB (a free, open lyrics database), fetched here because the page cannot reach it itself."""
    import urllib.request
    import urllib.error
    artist = (q.get("artist", [""])[0] or "").strip()
    track = (q.get("track", [""])[0] or "").strip()
    album = (q.get("album", [""])[0] or "").strip()
    try:
        duration = float(q.get("duration", ["0"])[0] or 0)
    except ValueError:
        duration = 0
    if not track:
        return {"ok": False, "why": "no song name"}
    headers = {"User-Agent": "DictationSheet/1.0 (personal transcription tool)"}

    def get(url):
        req = urllib.request.Request(url, headers=headers)
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=15) as r:
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                # the site answers 503 for a moment now and then; one more try after a short wait
                if exc.code < 500 or attempt:
                    raise
                time.sleep(1.5)

    try:
        params = {"track_name": track, "artist_name": artist}
        if album:
            params["album_name"] = album
        if duration:
            params["duration"] = str(int(round(duration)))
        try:
            hit = get("https://lrclib.net/api/get?" + urllib.parse.urlencode(params))
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            hit = None
        if not hit or not hit.get("syncedLyrics"):
            found = get("https://lrclib.net/api/search?" + urllib.parse.urlencode({"track_name": track, "artist_name": artist}))
            found = [f for f in found if f.get("syncedLyrics")]
            if duration:
                found.sort(key=lambda f: abs(float(f.get("duration") or 0) - duration))
            hit = found[0] if found else None
        if not hit:
            return {"ok": False, "why": "no timed lyrics found for this song"}
        return {"ok": True, "synced": hit.get("syncedLyrics") or "", "plain": hit.get("plainLyrics") or "", "duration": hit.get("duration"), "track": hit.get("trackName"), "artist": hit.get("artistName")}
    except Exception as exc:
        return {"ok": False, "why": str(exc)}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE), **kwargs)

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path == "/version":
            return self.send_json({"ok": True, "version": VERSION, "app": "Dictation Sheet"})
        if path == "/listen/status":
            return self.send_json(LISTENER.status())
        if path == "/listen/frames":
            q = urllib.parse.parse_qs(query)
            try:
                since = int(q.get("since", ["0"])[0] or 0)
            except ValueError:
                return self.send_json({"ok": False, "why": "since must be a whole number"}, 400)
            return self.send_json(LISTENER.frames_since(max(0, since)))
        if path == "/lyrics":
            return self.send_json(fetch_lyrics(urllib.parse.parse_qs(query)))
        if path == "/align/status":
            return self.send_json(align_status())
        if path == "/align/result":
            job = ALIGN_JOB
            if job is None or job.result is None:
                return self.send_json({"ok": False, "why": "no fit has finished"})
            return self.send_json(job.result)
        if path == "/align/capture.wav":
            data = capture_wav()
            if data is None:
                return self.send_json({"ok": False, "why": "nothing recorded"}, 404)
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return None
        target = HERE / urllib.parse.unquote(path.lstrip("/"))
        if path in ("/", "/callback") or not target.is_file():
            self.path = PAGE + ("?" + query if query else "")
        return super().do_GET()

    def body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        return self.rfile.read(n) if n > 0 else b""

    def do_POST(self):
        path, _, query = self.path.partition("?")
        if path == "/listen/start":
            if pyaudio is None or np is None:
                return self.send_json({"ok": False, "why": CAPTURE_WHY or "capture libraries missing"})
            q = urllib.parse.parse_qs(query)
            LISTENER.start(record=q.get("record", ["0"])[0] == "1")
            time.sleep(0.15)
            return self.send_json(LISTENER.status())
        if path == "/listen/stop":
            LISTENER.stop()
            return self.send_json({"ok": True})
        if path == "/align/audio":
            data = self.body()
            if len(data) < 1000:
                return self.send_json({"ok": False, "why": "no sound in the upload"}, 400)
            if len(data) > 40 * 1024 * 1024:
                return self.send_json({"ok": False, "why": "the song file is too big (40 MB at most)"}, 400)
            UPLOAD.write_bytes(data)
            return self.send_json({"ok": True, "bytes": len(data)})
        if path == "/align/run":
            try:
                req = json.loads(self.body().decode("utf-8") or "{}")
            except ValueError:
                return self.send_json({"ok": False, "why": "bad request body"}, 400)
            return self.send_json(align_run(req))
        self.send_response(404)
        self.end_headers()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


def port_busy() -> bool:
    s = socket.socket()
    try:
        s.settimeout(0.3)
        s.connect(("127.0.0.1", PORT))
        return True
    except OSError:
        return False
    finally:
        s.close()


def launch() -> None:
    if "--no-open" in sys.argv:
        return
    for b in BROWSERS:
        if b.exists():
            subprocess.Popen([str(b), f"--app={URL}"])
            return
    webbrowser.open(URL)


def running_version():
    """The version of whatever answers on the port: this build's, an older Dictation Sheet server's ("old"), or
    None when it is some other program (or nothing answers)."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"{URL}version", timeout=2) as r:
            body = r.read().decode("utf-8", "replace")
            if r.headers.get_content_type() == "application/json":
                data = json.loads(body)
                # any other Dictation Sheet build on the port is "old" to this one, whatever its hash: it is replaced
                if data.get("app") == "Dictation Sheet" and data.get("version") != VERSION:
                    return "old"
                return data.get("version")
            return "old" if "Dictation Sheet" in body else None
    except Exception:
        return None


def listener_pids():
    """Every process listening on the port, from netstat (Windows lets more than one bind it); [] when it cannot be told."""
    try:
        out = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return []
    pids = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0] == "TCP" and parts[1].endswith(f":{PORT}") and parts[3] == "LISTENING":
            try:
                pid = int(parts[4])
            except ValueError:
                continue
            if pid not in pids:
                pids.append(pid)
    return pids


def listener_pid():
    pids = listener_pids()
    return pids[0] if pids else None


def replace_old_server() -> bool:
    """An older Dictation Sheet server left running keeps the port and lacks the newer routes. Every one of them is
    stopped so this build can serve. Another program on the port is left alone (it never answers /version as ours)."""
    pids = [p for p in listener_pids() if p != os.getpid()]
    if not pids:
        return False
    for pid in pids:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    for _ in range(40):
        if not port_busy():
            return True
        time.sleep(0.1)
    return False


if __name__ == "__main__":
    if port_busy():
        ver = running_version()
        if ver == VERSION:
            launch()
            sys.exit(0)
        if ver != "old" or not replace_old_server():
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, f"Port {PORT} is in use by another program, so Dictation Sheet cannot start its local server. Close that program and open the shortcut again.", "Dictation Sheet", 0x10)
            except Exception:
                pass
            sys.exit(1)
    # never two servers on the port: on Windows, address reuse lets a second one bind beside the first, and then the
    # browser reaches whichever it happens to hit (two were found listening on 2026-09-24)
    socketserver.ThreadingTCPServer.allow_reuse_address = False
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as srv:
        threading.Timer(0.5, launch).start()
        srv.serve_forever()
'''


def server_version() -> str:
    """Changes whenever the server's own code changes, so a running older copy is replaced by the shortcut; the page is
    read from disk on every request, so a page-only rebuild needs no restart."""
    import hashlib
    align_src = SRC.parent / "align.py"
    extra = align_src.read_text("utf-8") if align_src.is_file() else ""
    return hashlib.md5((SERVE_SRC + extra).encode("utf-8")).hexdigest()[:10]


def write_server() -> None:
    SERVE.write_text(SERVE_SRC.replace("__PORT__", str(PORT)).replace("__VERSION__", server_version()), "utf-8")
    # the fitting module rides along; the server imports it from its own folder
    align_src = SRC.parent / "align.py"
    if align_src.is_file():
        (OUT_DIR / "align.py").write_text(align_src.read_text("utf-8"), "utf-8")


def make_shortcut(browser: Path) -> None:
    pyw = Path(sys.executable).with_name("pythonw.exe")
    if not pyw.exists():
        pyw = Path(sys.executable)
    script = f"""
$ws = New-Object -ComObject WScript.Shell
$l = $ws.CreateShortcut('{DESKTOP_LNK}')
$l.TargetPath = '{pyw}'
$l.Arguments = '"{SERVE}"'
$l.WorkingDirectory = '{OUT_DIR}'
$l.IconLocation = '{ICO},0'
$l.Description = 'Dictation Sheet: lyrics to solfege, drums and notation'
$l.Save()
"""
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], check=True)
    del browser


def main() -> int:
    fragment = SRC.read_text("utf-8")
    fragment, n_js = inline_scripts(fragment)
    fragment, n_fonts = inline_fonts(fragment)
    html = wrap(fragment)
    leftovers = re.findall(r'(?:src|href)="https://[^"]+"', html)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SHEET_DIR.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, "utf-8")
    README.write_text(README_TEXT.replace("{PORT}", str(PORT)), "utf-8")
    write_server()
    draw_icon(ICO)

    browser = next((b for b in BROWSERS if b.exists()), None)
    if browser:
        make_shortcut(browser)

    print(f"page      {OUT_HTML}  ({OUT_HTML.stat().st_size / 1024:.0f} KB)")
    print(f"scripts   {n_js} inlined, fonts {n_fonts} inlined")
    print(f"icon      {ICO}")
    print(f"server    {SERVE} on http://127.0.0.1:{PORT}/")
    print(f"shortcut  {DESKTOP_LNK} -> pythonw serve.py (opens {browser.name if browser else 'the default browser'})")
    if leftovers:
        print("still loads from the web:", *leftovers, sep="\n  ")
        return 1
    print("no web loads left")
    return 0


if __name__ == "__main__":
    sys.exit(main())
