"""Mac helpers for the AIOS apps (2026-10-07, Jonathan: "ship Monarc's CRM and Monarc Flow ... for installation on a Mac").

make_app() writes a double-click app into ~/Applications (an .app folder whose program is a two-line shell script that
runs a repo script with the repo's Python). login_item() writes a LaunchAgent so a script starts when he logs in.
Both use only what ships with macOS (sips and iconutil for the icon, launchctl for the log-in item).
"""
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPS = Path.home() / "Applications"
AGENTS = Path.home() / "Library" / "LaunchAgents"
IS_MAC = sys.platform == "darwin"


def python():
    """The Python the install made (.venv in the repo), else the one running now."""
    v = ROOT / ".venv" / "bin" / "python3"
    return str(v if v.exists() else Path(sys.executable))


def _icns(png, dest):
    """An .icns from a square PNG, with macOS's own sips and iconutil. Skipped quietly when either is missing."""
    if not (png and Path(png).exists() and shutil.which("sips") and shutil.which("iconutil")):
        return False
    with tempfile.TemporaryDirectory() as t:
        iconset = Path(t) / "icon.iconset"
        iconset.mkdir()
        for s in (16, 32, 64, 128, 256, 512):
            for scale, suffix in ((1, ""), (2, "@2x")):
                px = s * scale
                if px > 1024:
                    continue
                subprocess.run(["sips", "-z", str(px), str(px), str(png), "--out", str(iconset / f"icon_{s}x{s}{suffix}.png")],
                               capture_output=True)
        r = subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(dest)], capture_output=True)
        return r.returncode == 0


def make_app(name, script, args=(), png=None, bundle_id=None, background=True):
    """~/Applications/<name>.app that runs `python <script> <args>` from the repo. Returns its path."""
    app = APPS / f"{name}.app"
    if app.exists():
        shutil.rmtree(app)
    (app / "Contents" / "MacOS").mkdir(parents=True)
    (app / "Contents" / "Resources").mkdir()
    exe = app / "Contents" / "MacOS" / "run"
    quoted = " ".join(f'"{a}"' for a in (python(), str(Path(script).resolve()), *args))
    exe.write_text(f'#!/bin/bash\ncd "{ROOT}"\nexec {quoted} >> "$HOME/.monarc/{name.lower().replace(" ", "-")}-app.log" 2>&1\n',
                   encoding="utf-8")
    os.chmod(exe, 0o755)
    info = {"CFBundleName": name, "CFBundleDisplayName": name, "CFBundleExecutable": "run",
            "CFBundleIdentifier": bundle_id or f"com.monarcbuild.{name.lower().replace(' ', '')}",
            "CFBundlePackageType": "APPL", "CFBundleShortVersionString": "1.0", "LSMinimumSystemVersion": "12.0",
            "NSMicrophoneUsageDescription": "Monarc Flow listens only while you hold the keys.",
            "NSHighResolutionCapable": True}
    if background:
        info["LSUIElement"] = True          # no Dock icon: the CRM opens a browser tab, Flow lives in the menu bar
    if _icns(png, app / "Contents" / "Resources" / "icon.icns"):
        info["CFBundleIconFile"] = "icon"
    with open(app / "Contents" / "Info.plist", "wb") as f:
        plistlib.dump(info, f)
    (Path.home() / ".monarc").mkdir(exist_ok=True)
    return app


def login_item(label, script, args=(), on=True, keep_alive=False):
    """A LaunchAgent that runs the script at log-in (on=False removes it). Returns the plist path."""
    plist = AGENTS / f"{label}.plist"
    if IS_MAC and plist.exists():
        subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
    if not on:
        plist.unlink(missing_ok=True)
        return plist
    AGENTS.mkdir(parents=True, exist_ok=True)
    log = str(Path.home() / ".monarc" / f"{label.split('.')[-1]}-agent.log")
    with open(plist, "wb") as f:
        plistlib.dump({"Label": label, "ProgramArguments": [python(), str(Path(script).resolve()), *args],
                       "WorkingDirectory": str(ROOT), "RunAtLoad": True, "KeepAlive": keep_alive,
                       "StandardOutPath": log, "StandardErrorPath": log, "ProcessType": "Interactive"}, f)
    if IS_MAC:
        subprocess.run(["launchctl", "load", str(plist)], capture_output=True)
    return plist


def login_item_on(label):
    return (AGENTS / f"{label}.plist").exists()


def alert(title, text):
    """A dialog on the Mac; printed elsewhere."""
    if IS_MAC:
        esc = text.replace("\\", "\\\\").replace('"', '\\"')
        subprocess.run(["osascript", "-e", f'display alert "{title}" message "{esc}" as critical'], capture_output=True)
    else:
        print(f"{title}: {text}", file=sys.stderr)
