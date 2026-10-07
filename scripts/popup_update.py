"""The booking popup changes of 2026-10-01, applied in place to every page that carries the shared popup.

Usage: python scripts/popup_update.py [--check]

Jonathan, 2026-10-01:
- "My name should not be used throughout this process that they're going through": the popup, the sent state, and
  the formsubmit auto-reply say "we" and "our calendar", never his name (the booking script's event, invite, and
  emails changed the same day in scripts/avmarketing-booking.gs and templates/booking-drip.md).
- "There should also be back arrows allowing me to go to the previous stage": a round back arrow top left of the
  popup, opposite the Close control, from step 2 on; the step's own Back button gets an arrow too (drawn in CSS in
  assets/site.css, so its label stays exactly "Back", Style Guide 6.2).
- "After picking a calendar date, does the time availability show up?": it does, under the calendar, but below the
  fold of a laptop screen; a day picked by hand now scrolls the times and the Confirm button into view.

Pages: every index.html under the site mirror with the popup, the /av_marketing/ staging copy (its push source), and
the archived /website-build/ build that scripts/build_service_page.py copies the popup from, so a rebuilt page keeps
the changes. Each change applies once; a second run reports "already done". --check changes nothing and lists what
would change. Pushes nothing.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "projects" / "monarcbuild-site"
PAGES = sorted(p for p in (SITE / "public_html").rglob("index.html") if "_wireframe" not in p.parts) + [
    SITE / "staging" / "av_marketing" / "index.html",
    ROOT / "archives" / "site-website-build-house-2026-09-25" / "index.html",
]

SMOOTH = '(window.matchMedia && matchMedia("(prefers-reduced-motion: no-preference)").matches ? "smooth" : "auto")'

# (old, new): each old string is the 2026-09-25 popup text, the same on every page
EDITS = [
    # the copy a booker reads
    ("from Jonathan's calendar. If not, Jonathan emails you two times. My Best, Jonathan",
     "from our calendar. If not, we email you two times. My Best, Monarc Build"),
    ('id="sent-sub">Jonathan emails you two times for a fifteen minute call.</p>',
     'id="sent-sub">We email you two times for a fifteen minute call.</p>'),
    ('<p class="hint">Jonathan calls it if the Meet link drops.</p>',
     '<p class="hint">We call it if the Meet link drops.</p>'),
    ("Fifteen minutes with Jonathan on Google Meet. Reading the calendar.",
     "Fifteen minutes on Google Meet. Reading the calendar."),
    ("Confirm books the time on Jonathan's calendar. The invite lands in your inbox.",
     "Confirm books the time on our calendar. The invite lands in your inbox."),
    ('" is requested. Jonathan confirms by email with the Google Meet link."',
     '" is requested. We confirm by email with the Google Meet link."'),
    ('". Jonathan\'s afternoon, Eastern"', '". Our afternoon, Eastern"'),
    ('textContent = "Jonathan emails you two times.";', 'textContent = "We email you two times.";'),
    ("Confirm and Jonathan replies with two times.", "Confirm and we reply with two times."),
    # the back arrow, opposite the Close control
    ('<button type="button" class="close" id="close" aria-label="Close">&times;</button>\n',
     '<button type="button" class="close" id="close" aria-label="Close">&times;</button>\n'
     '<button type="button" class="back-top" id="back-top" aria-label="Back" hidden>&larr;</button>\n'),
    ("    if (back) back.hidden = (i === 0);\n",
     "    if (back) back.hidden = (i === 0);\n"
     '    var backTop = document.getElementById("back-top");\n'
     "    if (backTop) backTop.hidden = (i === 0);\n"),
    ('  document.getElementById("close").addEventListener("click", closeModal);\n',
     '  document.getElementById("close").addEventListener("click", closeModal);\n'
     '  var backTopBtn = document.getElementById("back-top");\n'
     '  if (backTopBtn) backTopBtn.addEventListener("click", function(){ go("back"); });\n'),
    # a day picked by hand brings its times and the Confirm button into view (on a phone the buttons stick to the
    # bottom, so the times' label goes to the top instead)
    ('    if (c) pickDay(c.getAttribute("data-day"));\n',
     '    if (!c) return;\n'
     '    pickDay(c.getAttribute("data-day"));\n'
     '    var nav = c.closest(".step") && c.closest(".step").querySelector(".step-nav");\n'
     '    var stuck = nav && getComputedStyle(nav).position === "sticky";\n'
     f'    if (stuck || !nav) slotDay.scrollIntoView({{block: "start", behavior: {SMOOTH}}});\n'
     f'    else nav.scrollIntoView({{block: "nearest", behavior: {SMOOTH}}});\n'),
]
# the first version of the scroll (2026-10-01, earlier the same session), replaced by the one above where it landed
OLD_SCROLL = (
    '    var nav = c.closest(".step") && c.closest(".step").querySelector(".step-nav");\n'
    f'    (nav || box).scrollIntoView({{block: "nearest", behavior: {SMOOTH}}});\n')
NEW_SCROLL = (
    '    var nav = c.closest(".step") && c.closest(".step").querySelector(".step-nav");\n'
    '    var stuck = nav && getComputedStyle(nav).position === "sticky";\n'
    f'    if (stuck || !nav) slotDay.scrollIntoView({{block: "start", behavior: {SMOOTH}}});\n'
    f'    else nav.scrollIntoView({{block: "nearest", behavior: {SMOOTH}}});\n')


# the old /book/ page (its own form, no shared popup) names him once in its thank-you line
BOOK_EDITS = [("You&#39;ll hear from Jonathan within one business day.", "You&#39;ll hear from us within one business day.")]


def main():
    check = "--check" in sys.argv
    for p in PAGES:
        if not p.exists():
            print(f"missing: {p}")
            continue
        raw = p.read_bytes().decode("utf-8")
        crlf = "\r\n" in raw
        t = raw.replace("\r\n", "\n")
        if OLD_SCROLL in t:
            t = t.replace(OLD_SCROLL, NEW_SCROLL)
            if not check:
                p.write_bytes((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
            print(f"{p.relative_to(ROOT)}: scroll updated")
        edits = EDITS if 'id="book-form"' in t else BOOK_EDITS if p.parent.name == "book" else None
        if not edits:
            continue
        done, already, missing = 0, 0, []
        for old, new in edits:
            if new in t:
                already += 1
            elif old in t:
                t = t.replace(old, new)
                done += 1
            else:
                missing.append(old[:60])
        name = p.relative_to(ROOT)
        print(f"{name}: {done} changed, {already} already done" + (f", NOT FOUND: {missing}" if missing else ""))
        if done and not check:
            p.write_bytes((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))


if __name__ == "__main__":
    main()
