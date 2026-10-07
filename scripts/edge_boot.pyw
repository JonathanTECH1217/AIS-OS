"""Monarc Edge boot, run by the Desktop shortcut "Monarc Edge" (2026-10-04).

One click: if Edge already answers, open it in its own Edge app window. If not, start scripts/edge_server.py with no
console window, wait until it answers, then open it. If a server file changed since the running copy started, stop
that copy and start a fresh one, unless it is busy (placing an order, running a backtest): then the running copy is
left alone and the window opens on it. Page files are read from disk on every request.

Server output: ~/.monarc/edge-server.log. Started copy: ~/.monarc/edge-server.json.

  pythonw scripts/edge_boot.pyw             boot (what the shortcut runs)
  pythonw scripts/edge_boot.pyw --no-open   start or refresh the server, no window (the Startup entry)
  python scripts/edge_boot.pyw --install    write the icon, the Desktop shortcut "Monarc Edge" and the Startup
                                            entry "Monarc Edge (background)"
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
from studio_common import open_app  # noqa: E402  (its own Edge app window, shared with Studio)

SERVER = SCRIPTS / "edge_server.py"
ICO = ROOT / "projects" / "edge" / "monarc-edge.ico"
HOME = Path.home() / ".monarc"
LOG = HOME / "edge-server.log"
STATE = HOME / "edge-server.json"
PORT = 8800
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def watch_files():
    """Every scripts/edge_*.py plus the three client modules: a change in any restarts an idle server."""
    files = sorted(SCRIPTS.glob("edge_*.py")) + [SCRIPTS / f for f in ("kalshi_api.py", "api_football.py", "polymarket_read.py")]
    return tuple(p for p in files if p.exists())


def answers(url):
    """True when url serves the Monarc Edge page (not some other app on the port)."""
    try:
        with urllib.request.urlopen(url, timeout=1.5) as r:
            return b"Monarc Edge" in r.read(4000)
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
    ctypes.windll.user32.MessageBoxW(None, text, "Monarc Edge", 0x10)


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
        m = re.search(r"Monarc Edge at (http://\S+)", LOG.read_text(encoding="utf-8", errors="replace"))
        if m and answers(m.group(1)):
            STATE.write_text(json.dumps({"pid": proc.pid, "url": m.group(1), "started": time.time()}), encoding="utf-8")
            return m.group(1)
        time.sleep(0.4)
    tail = "\n".join(LOG.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-12:])
    alert(f"The Edge server did not start.\n\n{tail or '(no output)'}\n\nFull log: {LOG}")
    return None


def boot(open_window=True):
    st = {}
    try:
        st = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    url = st.get("url") or f"http://127.0.0.1:{PORT}/"
    if answers(url):
        watch = watch_files()
        changed = st.get("started") and watch and max(p.stat().st_mtime for p in watch) > st["started"]
        busy = health(url).get("busy")       # an order being placed or a backtest: never restarted in the middle
        if not (changed and not busy and st.get("pid") and is_python(st["pid"])):
            if open_window:
                open_app(url, size="1536,860")
            return
        subprocess.run(["taskkill", "/PID", str(st["pid"]), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)
        for _ in range(25):
            if not answers(url):
                break
            time.sleep(0.2)
    url = start()
    if url and open_window:
        open_app(url, size="1536,860")


def make_icon(letter="E", rgb=(16, 122, 68), path=ICO):
    """A white letter on a color in a rounded square: E on dark green for Monarc Edge."""
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
    img.resize((64, 64)).save(path.with_name("favicon.png"))


def shortcut(folder, name, args, ico, description):
    pyw = Path(sys.executable).with_name("pythonw.exe")
    lnk = Path(folder) / f"{name}.lnk"
    ps = (f"$l = (New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}'); "
          f"$l.TargetPath = '{pyw if pyw.exists() else sys.executable}'; "
          f"$l.Arguments = '\"{Path(__file__).resolve()}\"{args}'; "
          f"$l.WorkingDirectory = '{ROOT}'; "
          f"$l.IconLocation = '{ico},0'; "
          f"$l.Description = '{description}'; "
          "$l.Save()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    return lnk


def special_folder(name):
    return subprocess.run(["powershell", "-NoProfile", "-Command", f"[Environment]::GetFolderPath('{name}')"],
                          capture_output=True, text=True).stdout.strip()


def install():
    make_icon()
    desktop = special_folder("Desktop") or str(Path.home() / "Desktop")
    startup = special_folder("Startup") or str(Path.home() / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup")
    a = shortcut(desktop, "Monarc Edge", "", ICO, "Monarc Edge: the Kalshi Premier League betting agent (starts the local server if needed)")
    b = shortcut(startup, "Monarc Edge (background)", " --no-open", ICO, "Monarc Edge: start the server with Windows, no window")
    print(f"icon      {ICO}\nshortcuts {a}\n          {b}")


if __name__ == "__main__":
    if "--install" in sys.argv:
        install()
    else:
        boot(open_window="--no-open" not in sys.argv)
