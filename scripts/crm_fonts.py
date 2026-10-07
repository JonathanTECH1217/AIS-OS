"""Fetch the Monarc CRM's Google look into projects/crm/fonts/ and write fonts.css (2026-09-26).

Google Sans and Google Sans Text (latin, 400 and 500), plus a Material Symbols Outlined file that holds only the icons
named in ICONS. The CRM serves these itself, so the look holds offline. To use a new icon in the CRM, add its name
to ICONS (names at https://fonts.google.com/icons) and run:

  python scripts/crm_fonts.py
"""
import re
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "projects" / "crm" / "fonts"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
ICONS = sorted(["ads_click", "bar_chart", "calendar_today", "campaign", "check", "domain", "folder_open", "history", "movie",
                "payments", "refresh", "search", "settings", "view_kanban"])  # folder_open: Records, Artifacts (2026-10-02); movie: Records, Creative (2026-10-05)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def faces(family_q, slug, css_out, out=None):
    out = out or OUT
    css = get(f"https://fonts.googleapis.com/css2?family={family_q}&display=swap").decode()
    n = 0
    for subset, body in re.findall(r"/\*\s*([\w-]+)\s*\*/\s*@font-face\s*{([^}]*)}", css):
        if subset != "latin":
            continue
        url = re.search(r"url\((https://[^)]+)\)", body).group(1)
        weight = re.search(r"font-weight:\s*([\d ]+);", body).group(1).strip().replace(" ", "-")
        fname = f"{slug}-{weight}.woff2"
        (out / fname).write_bytes(get(url))
        css_out.append("@font-face {" + body.replace(url, fname) + "}")
        n += 1
    print(f"{family_q}: {n} faces")


def build(out, icons, writer="scripts/crm_fonts.py"):
    """Google Sans, Google Sans Text and a Material Symbols subset into out/, plus out/fonts.css.
    scripts/studio_fonts.py calls this with Monarc Studio's folder and icon list (2026-09-29)."""
    out.mkdir(parents=True, exist_ok=True)
    css_out = [f"/* Written by {writer} from Google Fonts (Google Sans, Google Sans Text: SIL OFL 1.1;\n"
               "   Material Symbols: Apache 2.0). Latin only. The symbols file holds only the icons listed below. */"]
    faces("Google+Sans:wght@400;500", "google-sans", css_out, out)
    faces("Google+Sans+Text:wght@400;500", "google-sans-text", css_out, out)
    sym = get("https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,300..500,0..1,0"
              "&icon_names=" + ",".join(icons) + "&display=block").decode()
    url = re.search(r"url\((https://[^)]+)\)", sym).group(1)
    (out / "material-symbols.woff2").write_bytes(get(url))
    css_out.append("/* icons: " + ", ".join(icons) + " */")
    css_out.append("@font-face {" + re.search(r"@font-face\s*{([^}]*)}", sym).group(1).replace(url, "material-symbols.woff2") + "}")
    (out / "fonts.css").write_text("\n".join(css_out) + "\n", encoding="utf-8")
    return css_out


def main():
    build(OUT, ICONS)
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name} {p.stat().st_size}")


if __name__ == "__main__":
    main()
