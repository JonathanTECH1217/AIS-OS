"""Build the style tiles for the service-page themes (Style Guide section 8; landing-page skill, "tile" mode).

Usage: python scripts/ads_tiles.py [--render] [--theme <name>] [--width 1440]

Reads every projects/Landing Page Build/themes/*.json and writes projects/Landing Page Build/tiles/themes.js
(window.MB_THEMES), which tiles/tile.html reads through ?theme=<name>. With --render it also renders each tile
(or the one named) through .claude/skills/landing-page/assets/render.py at the given width into
projects/Landing Page Build/renders/<today>/tile-<theme>-<width>.png and prints the paths.
"""
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES = ROOT / "projects" / "Landing Page Build" / "themes"
TILES = ROOT / "projects" / "Landing Page Build" / "tiles"
RENDERS = ROOT / "projects" / "Landing Page Build" / "renders"
RENDER_PY = ROOT / ".claude" / "skills" / "landing-page" / "assets" / "render.py"


def flag_value(flags, name, default=None):
    if name in flags and flags.index(name) + 1 < len(flags):
        return flags[flags.index(name) + 1]
    return default


def main():
    flags = sys.argv[1:]
    only = flag_value(flags, "--theme")
    width = int(flag_value(flags, "--width", 1440))
    themes = {}
    for path in sorted(THEMES.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        themes[data.get("name", path.stem)] = data
    TILES.mkdir(parents=True, exist_ok=True)
    out = TILES / "themes.js"
    out.write_text("// Written by scripts/ads_tiles.py from projects/Landing Page Build/themes/*.json. Do not edit by hand.\n"
                   "window.MB_THEMES = " + json.dumps(themes, indent=2) + ";\n", encoding="utf-8")
    print(f"{len(themes)} themes -> {out}")
    if "--render" not in flags:
        return
    day = dt.date.today().isoformat()
    outdir = RENDERS / day
    outdir.mkdir(parents=True, exist_ok=True)
    tile = TILES / "tile.html"
    for name in themes:
        if only and name != only:
            continue
        uri = tile.resolve().as_uri() + f"?theme={name}&static=1"
        png = outdir / f"tile-{name}-{width}.png"
        r = subprocess.run([sys.executable, str(RENDER_PY), uri, str(png), str(width)], capture_output=True, text=True)
        status = "ok" if r.returncode == 0 and png.exists() else "failed"
        print(f"{name}: {status} {png}")
        if r.returncode != 0:
            print(r.stdout[-400:], r.stderr[-400:])


if __name__ == "__main__":
    main()
