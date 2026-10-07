"""Monarc Studio boot, run by the Desktop shortcut "Monarc Studio" (2026-09-29).

One click: if Studio already answers, open it in its own Edge app window. If not, start scripts/studio_server.py
with no console window, wait until it answers, then open it. If a server file changed since the running copy
started, stop that copy and start a fresh one, unless it is busy (preparing, finding moments, exporting): then the
running copy is left alone and the window opens on it. Page files are read from disk on every request.

Server output: ~/.monarc/studio-server.log. Started copy: ~/.monarc/studio-server.json.

  pythonw scripts/studio_boot.pyw             boot (what the shortcut runs)
  pythonw scripts/studio_boot.pyw --calls     boot, then Monarc Calls: Airtable's grid (left 2/3) beside the notes (right 1/3)
  pythonw scripts/studio_boot.pyw --no-open   start or refresh the server, no window
  python scripts/studio_boot.pyw --install    write the icons and both Desktop shortcuts (Monarc Studio, Monarc Calls)
"""
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from studio_common import open_app, open_side_by_side  # noqa: E402  (shared with the server's Calls button)

SERVER = SCRIPTS / "studio_server.py"
WATCH = tuple(SCRIPTS / f for f in ("studio_server.py", "studio_common.py", "studio_prep.py", "studio_moments.py",
                                    "studio_speakers.py", "studio_captions.py", "studio_calls.py", "studio_session.py",
                                    "studio_prospects.py", "calls_mic.py", "calls_notes.py", "studio_gencaps.py",
                                    "studio_listen.py", "studio_transcribe.py"))
AIRTABLE_GRID = "https://airtable.com/appPM1HmRfFlgA484/tblGdourIuqa9onmp/viwIqkvcY7jm27SY0"   # his Grid view
ICO = ROOT / "projects" / "studio" / "monarc-studio.ico"
CALLS_ICO = ROOT / "projects" / "studio" / "monarc-calls.ico"
HOME = Path.home() / ".monarc"
LOG = HOME / "studio-server.log"
STATE = HOME / "studio-server.json"
PORT = 8780
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def answers(url):
    """True when url serves the Monarc Studio page (not some other app on the port)."""
    try:
        with urllib.request.urlopen(url, timeout=1.5) as r:
            return b"Monarc Studio" in r.read(4000)
    except OSError:
        return False


def health(url):
    try:
        with urllib.request.urlopen(url + "api/health", timeout=2) as r:
            return json.loads(r.read())
    except (OSError, ValueError):
        return {}


def is_python(pid):
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True,
                         creationflags=NO_WINDOW).stdout.lower()
    return "python" in out


def alert(text):
    import ctypes
    ctypes.windll.user32.MessageBoxW(None, text, "Monarc Studio", 0x10)


def start():
    HOME.mkdir(exist_ok=True)
    py = Path(sys.executable).with_name("python.exe")
    log = open(LOG, "w", encoding="utf-8")
    proc = subprocess.Popen([str(py if py.exists() else sys.executable), "-u", str(SERVER), "--no-open",
                             "--port", str(PORT)], cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, creationflags=NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            break
        m = re.search(r"Monarc Studio at (http://\S+)", LOG.read_text(encoding="utf-8", errors="replace"))
        if m and answers(m.group(1)):
            STATE.write_text(json.dumps({"pid": proc.pid, "url": m.group(1), "started": time.time()}), encoding="utf-8")
            return m.group(1)
        time.sleep(0.4)
    tail = "\n".join(LOG.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-12:])
    alert(f"The Studio server did not start.\n\n{tail or '(no output)'}\n\nFull log: {LOG}")
    return None


def show(url, page):
    """The editor in its own window; Monarc Calls as two windows side by side (Q41), Airtable left, notes right."""
    if page == "calls.html":
        open_side_by_side(AIRTABLE_GRID, url + page)
    else:
        open_app(url + page)


def boot(open_window=True, page=""):
    """page: "" for the editor, "calls.html" for Monarc Calls."""
    st = {}
    try:
        st = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    url = st.get("url") or f"http://127.0.0.1:{PORT}/"
    if answers(url):
        changed = st.get("started") and max(p.stat().st_mtime for p in WATCH if p.exists()) > st["started"]
        busy = health(url).get("busy")       # busy includes a Monarc Calls session: never restarted mid-session
        if not (changed and not busy and st.get("pid") and is_python(st["pid"])):
            if open_window:
                show(url, page)
            return
        subprocess.run(["taskkill", "/PID", str(st["pid"]), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)
        for _ in range(25):
            if not answers(url):
                break
            time.sleep(0.2)
    url = start()
    if url and open_window:
        show(url, page)


def make_icon(letter="S", rgb=(11, 87, 208), path=ICO):
    """A white letter on a color in a rounded square: S on the CRM blue for Studio (the top bar's mark), C on red for
    Monarc Calls (the record light)."""
    from PIL import Image, ImageDraw, ImageFont
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((8, 8, size - 8, size - 8), radius=60, fill=(*rgb, 255))
    font = None
    for f in ("seguisb.ttf", "segoeuib.ttf", "arialbd.ttf"):
        try:
            font = ImageFont.truetype(str(Path("C:/Windows/Fonts") / f), 150)
            break
        except OSError:
            continue
    d.text((size / 2, size / 2 + 4), letter, font=font, fill="white", anchor="mm")
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    img.resize((64, 64)).save(path.with_name("favicon.png" if path == ICO else path.stem + ".png"))


def shortcut(desktop, name, args, ico, description):
    pyw = Path(sys.executable).with_name("pythonw.exe")
    lnk = Path(desktop) / f"{name}.lnk"
    ps = (f"$l = (New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}'); "
          f"$l.TargetPath = '{pyw if pyw.exists() else sys.executable}'; "
          f"$l.Arguments = '\"{Path(__file__).resolve()}\"{args}'; "
          f"$l.WorkingDirectory = '{ROOT}'; "
          f"$l.IconLocation = '{ico},0'; "
          f"$l.Description = '{description}'; "
          "$l.Save()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    return lnk


def install():
    make_icon()
    make_icon("C", (197, 34, 31), CALLS_ICO)
    desktop = subprocess.run(["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"],
                             capture_output=True, text=True).stdout.strip() or str(Path.home() / "Desktop")
    a = shortcut(desktop, "Monarc Studio", "", ICO,
                 "Monarc Studio: short-form video editor (starts the local server if needed)")
    b = shortcut(desktop, "Monarc Calls", " --calls", CALLS_ICO,
                 "Monarc Calls: Airtable beside live key notes from your calls")
    print(f"icons     {ICO}, {CALLS_ICO}\nshortcuts {a}\n          {b}")


if __name__ == "__main__":
    if "--install" in sys.argv:
        install()
    else:
        boot(open_window="--no-open" not in sys.argv, page="calls.html" if "--calls" in sys.argv else "")
