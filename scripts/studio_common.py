"""Shared helpers for Monarc Studio (the short-form video editor, 2026-09-29).

Paths, the ffmpeg locator, asset ids, atomic JSON writes, a hidden subprocess runner that reads ffmpeg's
-progress output, and a media probe that parses `ffmpeg -i` (the bundled ffmpeg has no ffprobe).

Folders (media/ is git-ignored except its README):
  media/inbox     recordings; new files are prepared automatically
  media/sfx       sound effects (the Sounds bin)
  media/assets    images, logos, B-roll for overlays
  media/projects  one JSON per short, plus .versions/ and .trash/
  media/ready     finished exports the scheduler picks up
  media/sessions  Monarc Calls session logs, one JSON line per click and write (original data, not cache)
  media/.studio   cache: remux, proxy, peaks, thumbnails, transcript, moments, render jobs

STUDIO_MEDIA overrides the media folder (the tests point it at a seeded copy).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDIO_DIR = ROOT / "projects" / "studio"
MEDIA = Path(os.environ.get("STUDIO_MEDIA") or (ROOT / "media")).resolve()
INBOX = MEDIA / "inbox"
SFX = MEDIA / "sfx"
ASSETS = MEDIA / "assets"
PROJECTS = MEDIA / "projects"
READY = MEDIA / "ready"
SESSIONS = MEDIA / "sessions"
CACHE = MEDIA / ".studio"
HOME = Path.home() / ".monarc"          # not AppData: the Store Python hides writes there
MODELS = HOME / "models"
FPS = 30

VIDEO_EXT = {".mp4", ".mov", ".mkv", ".m4v", ".webm", ".avi"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
BELOW_NORMAL = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)

PARAKEET_DIR = MODELS / "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"
SILERO_VAD = MODELS / "silero_vad.onnx"
# the voice split (2026-09-30): pyannote segmentation 3.0 finds who speaks when, WeSpeaker ResNet34-LM voiceprints
SPK_SEG = MODELS / "sherpa-onnx-pyannote-segmentation-3-0" / "model.onnx"
SPK_EMB = MODELS / "wespeaker_en_voxceleb_resnet34_LM.onnx"
# Jonathan's saved voiceprint (outside the cache, which is safe to delete) and the Studio settings (caption palette).
# A run pointed at another media folder (the tests) keeps both inside that folder unless told otherwise, so it can
# never overwrite the real ones.
_TEST_MEDIA = bool(os.environ.get("STUDIO_MEDIA"))
VOICEPRINT = Path(os.environ.get("STUDIO_VOICEPRINT") or
                  (MEDIA / ".studio" / "voiceprint.json" if _TEST_MEDIA else HOME / "studio-voiceprint.json"))
CONFIG = Path(os.environ.get("STUDIO_CONFIG") or
              (MEDIA / "studio-config.json" if _TEST_MEDIA else STUDIO_DIR / "config.json"))
# Monarc Calls' docs, one folder per company (2026-10-03); the tests keep theirs in the throwaway media folder
PROSPECTS = Path(os.environ.get("STUDIO_PROSPECTS") or
                 (MEDIA / "prospects" if _TEST_MEDIA else ROOT / "projects" / "prospects"))


def ensure_dirs():
    for d in (INBOX, SFX, ASSETS, PROJECTS, READY, SESSIONS, CACHE, HOME):
        d.mkdir(parents=True, exist_ok=True)


BROWSERS = [Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
           Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),      # a Mac (2026-10-07)
           Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")]


def open_app(url, maximized=False, size=None):
    """Its own window: Edge --app (no tabs, no address bar), autoplay allowed so preview audio starts on Space.
    Shared by the boot script and the server."""
    import webbrowser
    for b in BROWSERS:
        if b.exists():
            subprocess.Popen([str(b), f"--app={url}", "--autoplay-policy=no-user-gesture-required",
                              "--start-maximized" if maximized else f"--window-size={size or '1600,960'}"])
            return
    webbrowser.open(url)


def _windows_titled(*needles):
    """{needle: hwnd} for visible top-level windows whose title holds the needle (first match each)."""
    import ctypes
    import ctypes.wintypes as w
    user32 = ctypes.windll.user32
    found = {}

    @ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    def each(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        if n:
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            title = buf.value.lower()
            if "edge" in title:          # an ordinary browser window ("... - Microsoft Edge"), never an app window
                return True
            for needle in needles:
                if needle not in found and needle.lower() in title:
                    found[needle] = hwnd
        return True

    user32.EnumWindows(each, 0)
    return found


def open_side_by_side(left_url, right_url, split=2 / 3, left_title="Airtable", right_title="Monarc Calls",
                      wait=12.0):
    """Monarc Calls (2026-10-03, Q41): Airtable's grid on the left two-thirds of the screen, the notes window on the
    right third. A window already open is reused, not opened twice. Placed with SetWindowPos in physical pixels on
    the work area (the screen minus the taskbar), retrying while Edge opens them."""
    import ctypes
    import ctypes.wintypes as w
    user32 = ctypes.windll.user32
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)     # physical pixels at 125 % scaling
    except Exception:  # noqa: BLE001
        pass
    have = _windows_titled(left_title, right_title)
    if left_title not in have:
        open_app(left_url, size="1020,780")
    if right_title not in have:
        open_app(right_url, size="510,780")
    area = w.RECT()
    user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(area), 0)          # SPI_GETWORKAREA
    width, height = area.right - area.left, area.bottom - area.top
    cut = int(width * split)
    spots = {left_title: (area.left, area.top, cut, height), right_title: (area.left + cut, area.top, width - cut, height)}
    placed, deadline = {}, time.time() + wait        # title -> [first placed at, times placed]
    while time.time() < deadline and not (len(placed) == 2 and all(p[1] >= 2 for p in placed.values())):
        for title, hwnd in _windows_titled(left_title, right_title).items():
            p = placed.get(title)
            if p and (p[1] >= 2 or time.time() - p[0] < 1.5):    # placed once more after Edge settles, then left be
                continue
            x, y, cx, cy = spots[title]
            user32.ShowWindow(hwnd, 9)                                       # SW_RESTORE (out of maximized)
            user32.SetWindowPos(hwnd, None, x, y, cx, cy, 0x0004 | 0x0040)   # SWP_NOZORDER | SWP_SHOWWINDOW
            placed[title] = [p[0] if p else time.time(), (p[1] if p else 0) + 1]
        time.sleep(0.3)
    return sorted(placed)


def kind_of(path):
    ext = Path(path).suffix.lower()
    if ext in VIDEO_EXT:
        return "video"
    if ext in AUDIO_EXT:
        return "audio"
    if ext in IMAGE_EXT:
        return "image"
    return None


# ---------------------------------------------------------------- ffmpeg

_FFMPEG = None


def ffmpeg_exe():
    """STUDIO_FFMPEG, then PATH, then winget's Links folder, then the copy bundled with imageio-ffmpeg."""
    global _FFMPEG
    if _FFMPEG:
        return _FFMPEG
    cands = [os.environ.get("STUDIO_FFMPEG"), shutil.which("ffmpeg"),
             str(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe")]
    for c in cands:
        if c and Path(c).is_file():
            _FFMPEG = c
            return c
    try:
        import imageio_ffmpeg
        _FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
        return _FFMPEG
    except Exception as e:  # pragma: no cover - reported by studio_check
        raise RuntimeError("ffmpeg not found: pip install imageio-ffmpeg, or set STUDIO_FFMPEG") from e


def probe(path):
    """Duration, video and audio stream facts from `ffmpeg -i` (no ffprobe in the bundled build)."""
    out = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", str(path)], capture_output=True, text=True,
                         encoding="utf-8", errors="replace", creationflags=NO_WINDOW).stderr
    info = {"duration": None, "video": None, "audio": None}
    m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", out)
    if m:
        info["duration"] = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    for line in out.splitlines():
        if "Stream #" not in line:
            continue
        if "Video:" in line and not info["video"]:
            v = {"codec": re.search(r"Video: (\w+)", line).group(1)}
            wh = re.search(r", (\d{2,5})x(\d{2,5})", line)
            if wh:
                v["w"], v["h"] = int(wh.group(1)), int(wh.group(2))
            fps = re.search(r"([\d.]+) fps", line) or re.search(r"([\d.]+) tbr", line)
            if fps:
                v["fps"] = float(fps.group(1))
            info["video"] = v
            if "attached pic" in line:
                info["video"]["still"] = True
        elif "Audio:" in line and not info["audio"]:
            a = {"codec": re.search(r"Audio: (\w+)", line).group(1)}
            sr = re.search(r"(\d+) Hz", line)
            if sr:
                a["sr"] = int(sr.group(1))
            a["channels"] = 1 if "mono" in line else 2
            info["audio"] = a
    return info


class Cancelled(Exception):
    pass


JOBS_DIR = HOME / "studio-jobs"          # one file per Studio process: <pid>.json lists its children
_children = set()
_children_lock = threading.Lock()


def _jobs_file():
    return JOBS_DIR / f"{os.getpid()}.json"


def track(proc):
    """Remember a child's pid on disk, so a restarted server can stop what a crashed one left running."""
    with _children_lock:
        _children.add(proc.pid)
        _write_children()


def untrack(proc):
    with _children_lock:
        _children.discard(proc.pid)
        _write_children()


def _write_children():
    try:
        JOBS_DIR.mkdir(parents=True, exist_ok=True)
        f = _jobs_file()
        if _children:
            f.write_text(json.dumps(sorted(_children)), encoding="utf-8")
        else:
            f.unlink(missing_ok=True)
    except OSError:
        pass


def _alive(pid):
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True,
                         creationflags=NO_WINDOW).stdout.lower()
    return out if str(pid) in out else ""


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)


def kill_orphans():
    """Stop the children of Studio processes that died (a crashed server, a killed export). A living process's
    children are left alone, so a test server never touches the real server's jobs."""
    if not JOBS_DIR.exists():
        return
    for f in JOBS_DIR.glob("*.json"):
        try:
            owner = int(f.stem)
        except ValueError:
            continue
        if owner == os.getpid() or _alive(owner):
            continue
        for pid in read_json(f, []) or []:
            info = _alive(pid)
            if "ffmpeg" in info or "python" in info:
                kill_tree(pid)
        f.unlink(missing_ok=True)


def popen(args, **kw):
    """Popen hidden, below normal priority, tracked. Caller must call untrack(proc) (or use run_proc)."""
    kw.setdefault("creationflags", NO_WINDOW | BELOW_NORMAL)
    kw.setdefault("stdin", subprocess.DEVNULL)
    proc = subprocess.Popen([str(a) for a in args], **kw)
    track(proc)
    return proc


def run_proc(args, on_progress=None, cancel=None, cwd=None, stdin=None, total=None):
    """Run a child hidden and at below-normal priority. For ffmpeg, pass `-progress pipe:1 -nostats` in args and
    on_progress(fraction) is called from out_time. cancel is a threading.Event. Returns (code, stderr_tail)."""
    proc = popen(args, cwd=cwd, stdin=stdin or subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        return _run_tracked(proc, on_progress, cancel, total)
    finally:
        untrack(proc)


def _run_tracked(proc, on_progress, cancel, total):
    tail = []

    def read_err():
        for raw in proc.stderr:
            tail.append(raw.decode("utf-8", "replace").rstrip())
            del tail[:-40]

    t = threading.Thread(target=read_err, daemon=True)
    t.start()
    for raw in proc.stdout:
        if cancel is not None and cancel.is_set():
            proc.kill()
            proc.wait()
            raise Cancelled()
        line = raw.decode("utf-8", "replace").strip()
        if on_progress and total and line.startswith("out_time_us="):
            try:
                us = int(line.split("=", 1)[1])
                on_progress(max(0.0, min(1.0, us / 1e6 / total)))
            except ValueError:
                pass
    proc.wait()
    t.join(timeout=2)
    return proc.returncode, "\n".join(tail)


# ---------------------------------------------------------------- ids and json

def asset_id(path):
    """a_ + sha1(size, first MiB, last MiB)[:12]. Survives renames and moves; cheap on a 4.5 GB file."""
    p = Path(path)
    size = p.stat().st_size
    h = hashlib.sha1(str(size).encode())
    with open(p, "rb") as f:
        h.update(f.read(1 << 20))
        if size > 2 << 20:
            f.seek(-(1 << 20), os.SEEK_END)
            h.update(f.read(1 << 20))
    return "a_" + h.hexdigest()[:12]


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json_atomic(path, obj, indent=None):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + f".{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(obj, indent=indent, ensure_ascii=False), encoding="utf-8")
    for i in range(20):  # Windows: a reader holding the file makes replace fail for a moment
        try:
            os.replace(tmp, p)
            return
        except PermissionError:
            time.sleep(0.05 * (i + 1))
    os.replace(tmp, p)


def rel_media(path):
    """media-relative path with forward slashes, the form the front end and the project files use."""
    return Path(path).resolve().relative_to(MEDIA).as_posix()


def media_path(rel):
    """Resolve a media-relative path and refuse anything outside media/."""
    p = (MEDIA / rel).resolve()
    if not p.is_relative_to(MEDIA):
        raise ValueError("outside media")
    return p


def slugify(text, fallback="short"):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (s[:48].strip("-") or fallback)


def python_exe():
    """python.exe beside the running interpreter (pythonw runs the boot; children need a console-less python)."""
    py = Path(sys.executable).with_name("python.exe")
    return str(py if py.exists() else sys.executable)
