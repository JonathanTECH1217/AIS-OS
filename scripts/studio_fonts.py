"""Fetch Monarc Studio's fonts into projects/studio/fonts/ (2026-09-29).

The CRM's Google look (Google Sans, Google Sans Text, a Material Symbols subset, through crm_fonts.build) plus the
caption font: Montserrat Black as a static TTF (SIL OFL 1.1, JulietaUla/Montserrat). libass burns captions with the
same TTF the page draws them with, so preview and export match. To use a new icon, add its name to ICONS
(https://fonts.google.com/icons) and run:

  python scripts/studio_fonts.py
"""
import urllib.error
import urllib.request
from pathlib import Path

import crm_fonts

OUT = Path(__file__).resolve().parent.parent / "projects" / "studio" / "fonts"
MONTSERRAT = "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-Black.ttf"
MONTSERRAT_OFL = "https://raw.githubusercontent.com/JulietaUla/Montserrat/master/OFL.txt"

ICONS = sorted(set("""
arrow_selector_tool content_cut pan_tool zoom_in zoom_out start sync_alt swap_horiz width ink_pen title
undo redo file_export play_arrow pause first_page last_page chevron_left chevron_right fast_rewind fast_forward
crop_free link link_off bookmark bookmark_add visibility visibility_off lock lock_open volume_up volume_off
headphones add remove movie graphic_eq subtitles folder folder_open video_file audio_file image music_note
auto_awesome upload_file progress_activity check_circle task_alt radio_button_unchecked play_circle more_vert
expand_more expand_less refresh search handshake event_available sentiment_very_satisfied format_quote timer
restart_alt diamond keyboard_arrow_left keyboard_arrow_right keyboard_arrow_down palette edit history restore close
check warning info delete content_copy content_paste keyboard rectangle circle arrow_right_alt text_fields
opacity rotate_right open_with aspect_ratio star download cancel drag_indicator settings help phone_in_talk
vertical_align_center fit_screen blur_on skip_previous skip_next stop error schedule arrow_back
""".split()))


def valid_icons(names):
    """Drop names the Material Symbols API does not know (one bad name fails the whole request)."""
    base = ("https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,300..500,"
            "0..1,0&icon_names=")
    try:
        crm_fonts.get(base + ",".join(names))
        return names
    except urllib.error.HTTPError:
        pass
    good = []
    for n in names:
        try:
            crm_fonts.get(base + n)
            good.append(n)
        except urllib.error.HTTPError:
            print(f"  skipped unknown icon: {n}")
    return good


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    icons = valid_icons(ICONS)
    css = crm_fonts.build(OUT, icons, writer="scripts/studio_fonts.py")
    (OUT / "Montserrat-Black.ttf").write_bytes(crm_fonts.get(MONTSERRAT))
    (OUT / "Montserrat-OFL.txt").write_bytes(crm_fonts.get(MONTSERRAT_OFL))
    css.append("/* caption font: Montserrat Black, SIL OFL 1.1 (Montserrat-OFL.txt) */")
    css.append("@font-face {font-family: 'Montserrat Black'; font-style: normal; font-weight: 400; "
               "font-display: block; src: url(Montserrat-Black.ttf) format('truetype');}")
    (OUT / "fonts.css").write_text("\n".join(css) + "\n", encoding="utf-8")
    for p in sorted(OUT.iterdir()):
        print(f"  {p.name} {p.stat().st_size}")


if __name__ == "__main__":
    main()
