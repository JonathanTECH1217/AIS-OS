"""Stage an offline build of index.html into the scratchpad (same inlining as build_desktop.py, nothing else touched).

Usage: python stage_build.py  -> writes stage.html next to this script
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = Path(r"C:\Users\sumre\Documents\GitHub\AIS-OS\projects\dictation-sheet")
sys.path.insert(0, str(PROJ))
import build_desktop as bd  # noqa: E402

fragment = bd.SRC.read_text("utf-8")
fragment, n_js = bd.inline_scripts(fragment)
fragment, n_fonts = bd.inline_fonts(fragment)
html = bd.wrap(fragment)
out = HERE / "stage.html"
out.write_text(html, "utf-8")
print(f"staged {out} ({out.stat().st_size // 1024} KB), scripts {n_js}, fonts {n_fonts}")
