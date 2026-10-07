"""Monarc CRM boot, run by the Desktop shortcut "Monarc CRM" (2026-09-26).

One click: if the CRM already answers, open it in the browser. If not, start scripts/crm_server.py with no window,
wait until it answers, then open it. If crm_server.py or projects/crm/config.json changed since the running copy
started, stop that copy and start a fresh one, so an update never needs a restart by hand. Page files (html, css, js)
are read from disk on every request and need no restart.

Server output: ~/.monarc/crm-server.log (not AppData: the Store Python hides writes there). Started copy: ~/.monarc/crm-server.json.

  pythonw scripts/crm_boot.pyw             boot (what the shortcut runs)
  pythonw scripts/crm_boot.pyw --no-open   start or refresh the server, no browser tab (for the AIOS after a server edit)
  python scripts/crm_boot.pyw --install    write projects/crm/monarc-crm.ico and the Desktop shortcut

On a Mac (2026-10-07) the same script runs under python3; --install makes ~/Applications/Monarc CRM.app instead of the
shortcut (scripts/mac_app.py). The install script for a Mac is install/mac/install.sh.
"""
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "scripts" / "crm_server.py"
# The server and the scripts it imports: an edit to any of them restarts it (ads_publish.py added 2026-10-01, when a
# keyword-editor change there would otherwise have waited for the next crm_server.py edit).
WATCH = (SERVER, ROOT / "projects" / "crm" / "config.json",
         *(ROOT / "scripts" / f"{m}.py" for m in ("outreach_common", "ads_publish", "ads_lint", "ads_negative_check",
                                                  "google_ads_api", "ads_pull", "page_shot", "proton_mail",
                                                  "crm_butterfly", "google_calendar_api", "crm_chat")))
ICO = ROOT / "projects" / "crm" / "monarc-crm.ico"
HOME = Path.home() / ".monarc"
LOG = HOME / "crm-server.log"
STATE = HOME / "crm-server.json"
PORT = 8770
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
WINDOWS = sys.platform == "win32"
# hidden and on its own: a Windows process group, or a new session elsewhere (so closing the app leaves the server up)
DETACH = ({"creationflags": NO_WINDOW | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)} if WINDOWS
          else {"start_new_session": True})


def answers(url):
    """True when url serves the Monarc CRM page (not some other app on the port)."""
    try:
        with urllib.request.urlopen(url, timeout=1.5) as r:
            return b"Monarc CRM" in r.read(4000)
    except OSError:
        return False


def is_python(pid):
    if WINDOWS:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True,
                             creationflags=NO_WINDOW).stdout.lower()
    else:
        out = subprocess.run(["ps", "-p", str(pid), "-o", "comm="], capture_output=True, text=True).stdout.lower()
    return "python" in out


def kill(pid):
    if WINDOWS:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, creationflags=NO_WINDOW)
    else:
        try:
            os.kill(int(pid), signal.SIGTERM)
        except OSError:
            pass


def alert(text):
    if WINDOWS:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, "Monarc CRM", 0x10)
    else:
        import mac_app
        mac_app.alert("Monarc CRM", text)


def start():
    """Start the server hidden, return its url once it answers."""
    HOME.mkdir(exist_ok=True)
    py = Path(sys.executable).with_name("python.exe") if WINDOWS else Path(sys.executable)
    log = open(LOG, "w", encoding="utf-8")
    proc = subprocess.Popen([str(py if py.exists() else sys.executable), "-u", str(SERVER), "--no-open", "--port", str(PORT)],
                            cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **DETACH)
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            break
        m = re.search(r"Monarc CRM at (http://\S+)", LOG.read_text(encoding="utf-8", errors="replace"))
        if m and answers(m.group(1)):
            STATE.write_text(json.dumps({"pid": proc.pid, "url": m.group(1), "started": time.time()}), encoding="utf-8")
            return m.group(1)
        time.sleep(0.4)
    tail = "\n".join(LOG.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-12:])
    alert(f"The CRM server did not start.\n\n{tail or '(no output)'}\n\nFull log: {LOG}")
    return None


def boot(open_browser=True):
    if not open_browser:
        webbrowser.open = lambda url: None
    st = {}
    try:
        st = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    url = st.get("url") or f"http://127.0.0.1:{PORT}/"
    if answers(url):
        changed = st.get("started") and max(p.stat().st_mtime for p in WATCH if p.exists()) > st["started"]
        if not (changed and st.get("pid") and is_python(st["pid"])):
            webbrowser.open(url)  # running and current, or started by hand in a terminal: leave it alone
            return
        kill(st["pid"])
        for _ in range(25):
            if not answers(url):
                break
            time.sleep(0.2)
    url = start()
    if url:
        webbrowser.open(url)


def make_icon(png=None):
    """The CRM's mark: a white M on Google blue in a rounded square, the same as the top bar."""
    from PIL import Image, ImageDraw, ImageFont
    size = 512 if png else 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((size * 0.03, size * 0.03, size * 0.97, size * 0.97), radius=size * 0.23, fill=(11, 87, 208, 255))
    font = None
    for f in ("C:/Windows/Fonts/seguisb.ttf", "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf"):
        try:
            font = ImageFont.truetype(f, int(size * 0.59))
            break
        except OSError:
            continue
    d.text((size / 2, size / 2 + 4), "M", font=font, fill="white", anchor="mm")
    if png:
        img.save(png)
    else:
        img.save(ICO, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def install():
    if not WINDOWS:
        import mac_app
        png = ROOT / "projects" / "crm" / "monarc-crm.png"
        make_icon(png)
        app = mac_app.make_app("Monarc CRM", __file__, png=png)
        print(f"app       {app}\nOpen it from ~/Applications, Spotlight, or drag it to the Dock.")
        return
    make_icon()
    pyw = Path(sys.executable).with_name("pythonw.exe")
    desktop = subprocess.run(["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"],
                             capture_output=True, text=True).stdout.strip() or str(Path.home() / "Desktop")
    lnk = Path(desktop) / "Monarc CRM.lnk"
    ps = (f"$l = (New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}'); "
          f"$l.TargetPath = '{pyw if pyw.exists() else sys.executable}'; "
          f"$l.Arguments = '\"{Path(__file__).resolve()}\"'; "
          f"$l.WorkingDirectory = '{ROOT}'; "
          f"$l.IconLocation = '{ICO},0'; "
          "$l.Description = 'Monarc CRM: starts the local server if needed and opens Today'; "
          "$l.Save()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    print(f"icon      {ICO}\nshortcut  {lnk}")


if __name__ == "__main__":
    install() if "--install" in sys.argv else boot(open_browser="--no-open" not in sys.argv)
