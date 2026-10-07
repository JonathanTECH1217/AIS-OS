"""Prospect page: one rebuilt landing page from one spec, the way the PHA and Momentum renders were built by hand (2026-10-06).

Jonathan handed 15 Loom audits the same day ("Use these links to build the renders"). Each render is the page the
audit describes, built to his rules (`projects/Landing Page Build/Taste Log.md`): one service a page; an eyebrow to the
buyer, then the headline with the service and the place, centered, white on a dark real photo (plain black when there is
no photo); one "Book a meeting" button down the whole page that opens a four-step form (first name, phone, email, a
message); the offering as three or four cards with icons; reviews from Google, first name and last initial; about and
real work near the end; a process in numbered stages when he asks for it; the ask again at the foot; credentials in the
footer only; a light serif for headings when the buyer is high-end residential.

  python scripts/prospect_page.py build <slug>      projects/Landing Page Build/prospects/<slug>/spec.json -> index.html
  python scripts/prospect_page.py render <slug>     index.html -> renders/<date>/<slug>-after-1440.png, -fold-1536.png, -390.png
  python scripts/prospect_page.py all <slug> ...    build then render, each
  python scripts/prospect_page.py check <slug>      what the spec leaves marked empty, and the words count

The spec (one JSON a company; a missing block leaves that section out; a missing photo or review draws a marked empty box):

  {"company": "Performance Home Automation", "short": "PHA", "page": "https://...", "loom": "https://www.loom.com/share/...",
   "phone": "410-956-9676", "address": "2014 Renard Ct, Annapolis, MD 21401", "areas": "Annapolis, Baltimore, ...",
   "brand": {"color": "#3F7A17", "dark": "#356B12", "accent": "#8CC440", "serif": true, "head": "Manrope", "body": "Poppins"},
   "logo": "assets/logo.png",
   "hero": {"eyebrow": "Annapolis homeowners", "h1": "Lighting Control Installation in Annapolis", "sub": "...", "photo": "assets/hero.jpg", "trust": "4.8 on Google from 19 reviews"},
   "cards": {"h2": "What lighting control gives you", "items": [{"icon": "keypad", "h3": "Keypads", "p": "..."}]},
   "process": {"eyebrow": "For architects, builders, and designers", "h2": "Our process", "photo": "assets/vans.jpg", "steps": [{"h3": "...", "p": "..."}]},
   "work": {"h2": "Our work", "photos": [{"src": "assets/a.jpg", "alt": "..."}]},
   "about": {"eyebrow": "About us", "h2": "...", "p": "...", "photo": "assets/team.jpg"},
   "reviews": {"h2": "What our clients say", "rating": "4.8 on Google from 19 reviews", "items": [{"p": "...", "who": "Barbara N."}]},
   "final": {"h2": "Free lighting consultation", "p": "Tell us about your home and pick a time."},
   "services": {"h2": "Everything else we install", "items": [{"icon": "speaker", "h3": "Whole home audio", "p": "...", "href": "https://..."}]},
   "faq": {"h2": "Questions we get asked", "items": [{"q": "...", "a": "..."}]},
   "footer": {"creds": "Lutron Gold Star Dealer."},
   "form": {"hint": "A line or two is plenty: the rooms, new build or a retrofit.", "order": ["first_name", "email", "phone", "message"]},
   "order": ["hero", "cards", "about", "process", "work", "reviews", "services", "faq", "final"],
   "pattern": {"letters": "ABACABA", "A": "#FFFFFF", "B": "#F3F6F0", "C": "#000000"},
   "notes": "anything the builder should know; not rendered"}

Also: "button" (the one label down the page, default "Book a meeting"); "logo_height" (px, default 46, for a wide
lockup); "hero.light" (a pale scrim with dark words); "cards.text": "dark" (black words on a light brand color);
"brand.title" (a Google serif in place of Newsreader); "header": {"dark": true, "logo": "assets/logo-light.png"} keeps
a dark header when theirs is dark (VME, 2026-10-07: "it turned the header section white"), with a logo made for a dark
ground; "bg" sets their own header color (Q Northwest's slate). Icons: keypad, clock, shield, bulb, speaker, camera, tv, shade,
wifi, home, lock, thermostat, bolt, wrench, plug, sun, network, phone, lamp, star, gate, drop, cog.

`pattern` is his background rule of 2026-10-06 ("A B A C A B A ... the change in the background color to show the
different sections"); which color is A, B, and C is his to say, so a spec without it keeps the PHA look. A section with
its own photo keeps the photo. The form sends nothing: it is a render. The page is never pushed anywhere by this script.
"""
import argparse
import html
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LPB = ROOT / "projects" / "Landing Page Build"
PROSPECTS = LPB / "prospects"
RENDERS = LPB / "renders"
RENDER_PY = ROOT / ".claude" / "skills" / "landing-page" / "assets" / "render.py"

ICONS = {
    "keypad": '<rect x="13" y="5" width="22" height="38" rx="4"/><path d="M19 14h10M19 22h10M19 30h10"/>',
    "clock": '<circle cx="24" cy="24" r="17"/><path d="M24 14v10l7 5"/>',
    "shield": '<path d="M24 5l15 6v11c0 10-6.5 17-15 21-8.5-4-15-11-15-21V11z"/><path d="M17.5 24l4.5 4.5 8.5-9"/>',
    "bulb": '<path d="M17 33a11 11 0 1 1 14 0v4H17z"/><path d="M19 42h10M24 5v3"/>',
    "speaker": '<rect x="13" y="5" width="22" height="38" rx="4"/><circle cx="24" cy="30" r="6"/><circle cx="24" cy="15" r="2.5"/>',
    "camera": '<rect x="6" y="14" width="26" height="20" rx="4"/><path d="M32 20l10-5v18l-10-5z"/>',
    "tv": '<rect x="6" y="9" width="36" height="24" rx="3"/><path d="M17 40h14M24 33v7"/>',
    "shade": '<rect x="8" y="6" width="32" height="8" rx="2"/><path d="M12 14v22M36 14v22M12 36h24M24 36v6"/>',
    "wifi": '<path d="M7 19a24 24 0 0 1 34 0M13 26a15 15 0 0 1 22 0M19 33a6 6 0 0 1 10 0"/><circle cx="24" cy="39" r="1.5"/>',
    "home": '<path d="M8 23L24 9l16 14"/><path d="M12 20v20h24V20"/><path d="M20 40V29h8v11"/>',
    "lock": '<rect x="11" y="21" width="26" height="21" rx="4"/><path d="M16 21v-6a8 8 0 0 1 16 0v6"/><circle cx="24" cy="32" r="2.5"/>',
    "thermostat": '<circle cx="24" cy="24" r="17"/><circle cx="24" cy="24" r="8"/><path d="M24 12v4M24 32v4"/>',
    "bolt": '<path d="M27 5L12 27h10l-2 16 16-23H26z"/>',
    "wrench": '<path d="M34 8a9 9 0 0 1 2 14l-19 19a4 4 0 0 1-6-6l19-19a9 9 0 0 1 4-8z"/><path d="M28 14l6 6"/>',
    "plug": '<path d="M16 6v10M32 6v10"/><rect x="11" y="16" width="26" height="12" rx="3"/><path d="M24 28v8a6 6 0 0 1-6 6"/>',
    "sun": '<circle cx="24" cy="24" r="9"/><path d="M24 4v6M24 38v6M4 24h6M38 24h6M9.9 9.9l4.2 4.2M33.9 33.9l4.2 4.2M9.9 38.1l4.2-4.2M33.9 14.1l4.2-4.2"/>',
    "network": '<circle cx="24" cy="10" r="5"/><circle cx="10" cy="36" r="5"/><circle cx="38" cy="36" r="5"/><path d="M21 14l-8 17M27 14l8 17M15 36h18"/>',
    "phone": '<rect x="14" y="4" width="20" height="40" rx="4"/><path d="M21 38h6"/>',
    "lamp": '<path d="M16 6h16l6 18H10z"/><path d="M24 24v14M16 42h16"/>',
    "star": '<path d="M24 6l5.5 11.5L42 19l-9 8.8 2.1 12.4L24 34.3 12.9 40.2 15 27.8 6 19l12.5-1.5z"/>',
    "gate": '<path d="M6 42V18l18-10 18 10v24"/><path d="M14 42V26h20v16M24 26v16"/>',
    "drop": '<path d="M24 5s13 14 13 24a13 13 0 0 1-26 0C11 19 24 5 24 5z"/>',
    "cog": '<circle cx="24" cy="24" r="7"/><path d="M24 4v6M24 38v6M4 24h6M38 24h6M9.9 9.9l4.2 4.2M33.9 33.9l4.2 4.2M9.9 38.1l4.2-4.2M33.9 14.1l4.2-4.2"/>',
}


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def icon(name):
    body = ICONS.get(name) or ICONS["bulb"]
    return ('<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{body}</svg>')


def empty_box(what, cls="shot"):
    return f'<div class="{cls} empty"><span>{esc(what)}</span></div>'


# ---------------------------------------------------------------- the sections

# Google's "G", beside every rating and every review (Jonathan, 2026-10-07: "The review sections should have the Google logo
# every time. Google reviews carry more trust and authority than just any review.")
GOOGLE_G = ('<svg class="g-mark" viewBox="0 0 48 48" aria-label="Google" role="img">'
            '<path fill="#FFC107" d="M43.6 20.1H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.6-.4-3.9z"/>'
            '<path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/>'
            '<path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z"/>'
            '<path fill="#1976D2" d="M43.6 20.1H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.6-.4-3.9z"/></svg>')


def rating_of(s):
    """(rating, count) from the Google profile on the spec, else parsed from a written line like '4.8 on Google from 19 reviews'."""
    g = s.get("google") or {}
    if g.get("rating"):
        return float(g["rating"]), int(g.get("count") or 0)
    for line in ((s.get("hero") or {}).get("trust"), (s.get("reviews") or {}).get("rating")):
        m = re.search(r"(\d(?:\.\d)?)\D+?(\d+)\s+reviews", line or "")
        if m:
            return float(m.group(1)), int(m.group(2))
    return None, 0


def stars(rating):
    n = max(0, min(5, int(round(rating or 0))))
    return "★" * n + '<span class="star-off">' + "★" * (5 - n) + "</span>"


def review_banner(s, cls="trust"):
    """The review banner (his word, 2026-10-07): the stars and the Google rating from however many reviews, right below the
    call to action, on every page. With no profile on file it is a marked empty slot, never an invented number."""
    r, n = rating_of(s)
    if not r:
        return f'<div class="{cls} banner empty-banner">{GOOGLE_G}<span>Their Google rating goes here</span></div>'
    return (f'<div class="{cls} banner">{GOOGLE_G}<span class="stars" aria-label="{r} stars">{stars(r)}</span>'
            f'<span>{r:g} on Google from {n} review{"s" if n != 1 else ""}</span></div>')


def sec_hero(s, b):
    h = s["hero"]
    # photo_style: a crop for one photo, such as PHA's portico slid onto the button (his note of 2026-10-05)
    pstyle = f' style="{esc(h["photo_style"])}"' if h.get("photo_style") else ""
    photo = f'<div class="hero-bg"><img src="{esc(h["photo"])}" alt=""{pstyle}></div>' if h.get("photo") else ""
    trust = review_banner(s)
    sub = f'<p class="sub">{esc(h["sub"])}</p>' if h.get("sub") else ""
    # white words on a dark ground, always (Jonathan, 2026-10-07: "white text on a dark background definitely carries");
    # the pale scrim tried once on TruDefinition is retired
    light = ""
    return (f'<section class="hero{light}" id="top" data-band="hero">{photo}<div class="col">'
            f'<div class="eyebrow">{esc(h.get("eyebrow", ""))}</div><h1>{esc(h["h1"])}</h1>{sub}'
            f'<button class="btn" type="button" data-book>{esc(b)}</button>{trust}</div></section>')


def sec_cards(s, b):
    c = s["cards"]
    dark = " dark" if c.get("text") == "dark" else ""     # black words on the brand color (his Lighthouse audit: "black text would probably look better")
    # the benefits of the offering, three cards, always: the three outcomes the owner of the house raves about, first in
    # the spec (Jonathan, 2026-10-07: "should just be three cards universally, and probably the strongest three")
    three = c["items"][:3]
    items = "".join(f'<div class="card{dark}">{icon(i.get("icon", "bulb"))}<h3>{esc(i["h3"])}</h3><p>{esc(i["p"])}</p></div>' for i in three)
    n = len(three)
    ask = f'<div class="ask"><button class="btn" type="button" data-book>{esc(b)}</button></div>' if c.get("button") else ""
    return (f'<section id="what" data-band="cards"><div class="col"><div class="center"><h2>{esc(c["h2"])}</h2></div>'
            f'<div class="cards lead" style="grid-template-columns:repeat({min(max(n, 1), 4)},minmax(0,1fr))">{items}</div>{ask}</div></section>')


def sec_process(s, b):
    p = s["process"]
    steps = "".join(f'<div class="step-card"><h3>{esc(x["h3"])}</h3><p>{esc(x["p"])}</p></div>' for x in p["steps"])
    # the photo rides in a CSS variable, so the band color (his A B A C pattern) can be laid over it as the scrim
    style = (f' style="--photo:url(\'{esc(p["photo"])}\');background:linear-gradient(180deg,rgba(8,9,11,.84),rgba(8,9,11,.88)),#000 var(--photo) center 55%/cover no-repeat"'
             if p.get("photo") else "")
    eyebrow = f'<div class="eyebrow">{esc(p["eyebrow"])}</div>' if p.get("eyebrow") else ""
    return (f'<section class="process" id="process" data-band="process"{style}><div class="col"><div class="center">{eyebrow}'
            f'<h2 style="margin-top:16px">{esc(p.get("h2", "Our process"))}</h2></div>'
            f'<div class="steps lead" style="grid-template-columns:repeat({min(max(len(p["steps"]), 1), 4)},minmax(0,1fr))">{steps}</div></div></section>')


def sec_work(s, b):
    w = s["work"]
    photos = list(w.get("photos") or [])
    cells = [f'<div class="shot"><img src="{esc(x["src"])}" alt="{esc(x.get("alt", ""))}"></div>' for x in photos]
    while len(cells) < 3:
        cells.append(empty_box("A photo of their work goes here"))
    return (f'<section id="work" data-band="work"><div class="col"><div class="center"><h2>{esc(w.get("h2", "Our work"))}</h2></div>'
            f'<div class="work lead">{"".join(cells[:3])}</div></div></section>')


def sec_about(s, b):
    a = s["about"]
    photo = (f'<div class="team"><img src="{esc(a["photo"])}" alt="{esc(a.get("alt", ""))}"></div>' if a.get("photo")
             else empty_box("A photo of the owner or the team goes here", "team"))
    return (f'<section class="about" id="about" data-band="about"><div class="col">{photo}<div>'
            f'<div class="eyebrow">{esc(a.get("eyebrow", "About us"))}</div><h2 style="margin-top:16px">{esc(a["h2"])}</h2>'
            f'<p>{esc(a["p"])}</p></div></div></section>')


def sec_reviews(s, b):
    r = s["reviews"]
    items = list(r.get("items") or [])
    cells = [f'<div class="quote"><div class="quote-top"><span class="stars" aria-label="{x.get("stars", 5)} stars">{stars(x.get("stars", 5))}</span>{GOOGLE_G}</div>'
             f'<p>{esc(x["p"])}</p><div class="who">{esc(x["who"])}<span class="muted"> on Google</span></div></div>'
             for x in items]
    while len(cells) < 3:
        cells.append(empty_box("A Google review goes here", "quote"))
    rating = review_banner(s, "rating")
    return (f'<section id="reviews" data-band="reviews"><div class="col"><div class="center"><h2>{esc(r.get("h2", "What our clients say"))}</h2></div>'
            f'{rating}<div class="quotes lead">{"".join(cells[:3])}</div></div></section>')


def sec_final(s, b):
    f = s["final"]
    p = f'<p>{esc(f["p"])}</p>' if f.get("p") else ""
    # the secondary call to action reads "Start your project" (Jonathan, 2026-10-07); a spec can say "h2_keep": true to keep its own
    h2 = f["h2"] if f.get("h2_keep") else "Start your project"
    return (f'<section class="final" id="book" data-band="final"><div class="col"><h2>{esc(h2)}</h2>{p}'
            f'<button class="btn" type="button" data-book>{esc(b)}</button></div></section>')


def sec_services(s, b):
    """Secondary services (his audits, 2026-10-06): three to six cards that link to the company's other high-ticket pages."""
    v = s["services"]
    items = v.get("items") or []
    cells = "".join(f'<a class="svc" href="{esc(i.get("href", "#"))}">{icon(i.get("icon", "bulb"))}<h3>{esc(i["h3"])}</h3>'
                    + (f'<p>{esc(i["p"])}</p>' if i.get("p") else "") + "</a>" for i in items)
    cols = 3 if len(items) in (3, 5, 6) else min(max(len(items), 1), 4)
    return (f'<section class="services" id="services" data-band="services"><div class="col"><div class="center"><h2>{esc(v.get("h2", "Everything else we install"))}</h2>'
            + (f'<p class="under">{esc(v["p"])}</p>' if v.get("p") else "")
            + f'</div><div class="svcs lead" style="grid-template-columns:repeat({cols},minmax(0,1fr))">{cells}</div></div></section>')


def sec_faq(s, b):
    v = s["faq"]
    items = "".join(f'<div class="qa"><h3>{esc(i["q"])}</h3><p>{esc(i["a"])}</p></div>' for i in v.get("items") or [])
    return (f'<section class="faq" id="faq" data-band="faq"><div class="col narrow"><div class="center"><h2>{esc(v.get("h2", "Questions we get asked"))}</h2></div>'
            f'<div class="qas lead">{items}</div></div></section>')


SECTIONS = {"hero": sec_hero, "cards": sec_cards, "process": sec_process, "work": sec_work, "about": sec_about, "reviews": sec_reviews,
            "services": sec_services, "faq": sec_faq, "final": sec_final}
DEFAULT_ORDER = ["hero", "cards", "about", "process", "work", "services", "faq", "reviews", "final"]


# ---------------------------------------------------------------- the page

def fonts_link(brand):
    fams = []
    if brand.get("serif", True):
        fams.append(f"{brand['title'].replace(' ', '+')}:wght@300;400" if brand.get("title") else "Newsreader:opsz,wght@6..72,300;6..72,400")
    fams.append(f"{brand.get('head', 'Manrope').replace(' ', '+')}:wght@500;600;700")
    fams.append(f"{brand.get('body', 'Poppins').replace(' ', '+')}:wght@400;500;600")
    return "https://fonts.googleapis.com/css2?" + "&".join("family=" + f for f in fams) + "&display=swap"


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(v))):02X}" for v in rgb)


def _mix(a, b, t):
    """a moved toward b by t (0 keeps a, 1 is b)."""
    ra, rb = _rgb(a), _rgb(b)
    return _hex([x + (y - x) * t for x, y in zip(ra, rb)])


def _dark(h):
    r, g, b = _rgb(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b < 128


def _lum(h):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = _rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def _contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def eyebrow_color(spec):
    """The eyebrow is always a shade of the brand color (Jonathan, 2026-10-07: "The eyebrow should always be a variant of the
    primary color"): the brand color, lightened just enough to read on the dark hero (4.5 to 1)."""
    base = spec["brand"]["color"]
    ground = "#1A1B1E"
    for t in [i / 20 for i in range(0, 20)]:
        c = _mix(base, "#FFFFFF", t)
        if _contrast(c, ground) >= 4.5:
            return c
    return "#FFFFFF"


def band_colors(spec):
    """His background rule (Jonathan, 2026-10-06): "A is the color of whatever the background is on the first one. B is just
    the opposite of that... C is the secondary color... a lighter version or a darker version of whatever the primary is
    relative to A." So A is the hero's ground (black under a dark hero, white under a light one), B its opposite, and C the
    brand color pushed toward A: a deep shade on a dark page, a pale tint on a light one. A spec may set any of the three."""
    p = spec.get("pattern") or {}
    hero_light = bool((spec.get("hero") or {}).get("light"))
    a = p.get("A") or ("#FFFFFF" if hero_light else "#0E0F11")
    b = p.get("B") or ("#0E0F11" if not _dark(a) else "#FFFFFF")
    c = p.get("C") or (_mix(spec["brand"]["color"], a, 0.55) if _dark(a) else _mix(spec["brand"]["color"], a, 0.86))
    return {"A": a, "B": b, "C": c}


def band_css(spec):
    """The sections take A B A C A B A down the page ("Hero, Services, About, Our process, Portfolio, Secondary Services,
    FAQ, and then secondary CTA"); past seven the cycle A B A C runs on, so no two bands side by side share a color. The
    hero keeps its photo and only sets A. A band with a photo (the process) keeps it under a scrim of its band's color."""
    p = spec.get("pattern") or {}
    if p.get("off"):
        return ""
    cols = band_colors(spec)
    letters = (p.get("letters") or "ABAC").upper()
    order = [k for k in (spec.get("order") or DEFAULT_ORDER) if k == "hero" or k in spec]
    rules = [f"\n/* his background pattern (2026-10-06): A {cols['A']}, B {cols['B']}, C {cols['C']} */"]
    for i, name in enumerate(order):
        k = letters[i % len(letters)]
        if name == "hero":
            continue
        col = cols[k]
        sel = f'[data-band="{name}"]'
        r, g, b = _rgb(col)
        if name == "process" and (spec.get("process") or {}).get("photo"):
            rules.append(f"{sel}{{background:linear-gradient(180deg,rgba({r},{g},{b},.86),rgba({r},{g},{b},.9)),{col} var(--photo) center 55%/cover no-repeat !important}}")
        else:
            rules.append(f"{sel}{{background:{col} !important}}")
        texts = f"{sel} .col>div>p,{sel} .col>p,{sel} .center p,{sel} .qa p,{sel} .step-card p"
        heads = f"{sel} h2,{sel} .qa h3,{sel} .step-card h3,{sel} .rating"
        if _dark(col):
            rules.append(f"{heads}{{color:#FFFFFF}}{texts}{{color:rgba(255,255,255,.8)}}{sel} .qa{{border-color:rgba(255,255,255,.18)}}"
                         f"{sel} .eyebrow{{color:var(--eyebrow)}}")
        else:
            rules.append(f"{heads}{{color:var(--ink)}}{texts}{{color:var(--grey)}}{sel} .qa{{border-color:var(--line)}}"
                         f"{sel} .eyebrow{{color:var(--brand)}}{sel} .step-card{{border-top-color:var(--brand)}}{sel} .step-card::before{{color:var(--brand)}}")
    return "\n".join(rules)


def css(spec):
    b = spec["brand"]
    serif = b.get("serif", True)
    head_face = f'"{b.get("head", "Manrope")}",Arial,sans-serif'
    body_face = f'"{b.get("body", "Poppins")}",Arial,sans-serif'
    title_face = (f'"{b["title"]}",Georgia,"Times New Roman",serif' if b.get("title") else '"Newsreader",Georgia,"Times New Roman",serif') if serif else head_face
    h1 = "font-size:72px;line-height:1.05;font-weight:300;letter-spacing:-.01em" if serif else "font-size:60px;line-height:1.06;font-weight:700;letter-spacing:-.015em"
    h2 = "font-size:44px;line-height:1.12;font-weight:300;letter-spacing:-.005em" if serif else "font-size:38px;line-height:1.14;font-weight:700;letter-spacing:-.01em"
    h3 = "font-size:25px;line-height:1.22;font-weight:400" if serif else "font-size:22px;line-height:1.24;font-weight:700"
    bands = band_css(spec)
    return f"""
:root{{--eyebrow:{eyebrow_color(spec)};--brand:{b["color"]};--brand-dark:{b.get("dark", b["color"])};--accent:{b.get("accent", b["color"])};--black:#000000;--ink:#111111;--grey:#3A3A3A;--mist:{b.get("mist", "#F3F4F2")};--line:#E3E5E1;--white:#FFFFFF;
  --title:{title_face};--head:{head_face};--body:{body_face}}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font:400 17px/1.65 var(--body);color:var(--grey);background:var(--white);-webkit-font-smoothing:antialiased}}
img{{max-width:100%;display:block}}
a{{color:inherit;text-decoration:none}}
button{{font:inherit;cursor:pointer}}
.col{{width:100%;max-width:960px;margin:0 auto;padding:0 24px}}
h1,h2,h3{{font-family:var(--title);color:var(--ink);text-wrap:balance}}
h1{{{h1}}}
h2{{{h2}}}
h3{{{h3}}}
.eyebrow{{font:600 14px/1 var(--head);letter-spacing:.16em;text-transform:uppercase}}
.center{{text-align:center}}
section{{padding:96px 0}}
.lead{{margin-top:56px}}
.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:64px;padding:0 46px;border:0;border-radius:8px;background:var(--brand);color:var(--white);font:700 20px/1 var(--head);transition:background .15s ease,transform .15s ease}}
.btn:hover{{background:var(--brand-dark);transform:translateY(-1px)}}
.btn:focus-visible,.ghost:focus-visible{{outline:3px solid var(--accent);outline-offset:3px}}
.btn.small{{min-height:46px;padding:0 22px;font-size:16px}}
.top{{position:sticky;top:0;z-index:5;background:var(--white);border-bottom:1px solid var(--line)}}
.top .col{{display:flex;align-items:center;gap:24px;height:80px;max-width:1120px}}
.top img{{height:46px;width:auto}}
.top .name{{font:700 20px/1 var(--head);color:var(--ink)}}
.top .phone{{margin-left:auto;font:600 15px/1 var(--head);color:var(--ink);white-space:nowrap}}
.top .btn.small{{white-space:nowrap}}
.hero{{position:relative;display:grid;place-items:center;min-height:min(84vh,700px);padding:96px 0;color:var(--white);text-align:center;background:var(--black);overflow:hidden}}
.hero-bg{{position:absolute;inset:0}}
.hero-bg img{{width:100%;height:100%;object-fit:cover;object-position:50% 45%}}
.hero-bg::after{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(18,19,22,.80),rgba(18,19,22,.62))}}
.hero .col{{position:relative;display:grid;justify-items:center;gap:26px}}
.hero .eyebrow{{color:var(--eyebrow);line-height:1.4;max-width:92%}}
.hero h1{{color:var(--white);max-width:900px}}
.hero .sub{{font-size:21px;line-height:1.5;max-width:640px;color:rgba(255,255,255,.9)}}
.hero .btn{{margin-top:10px}}
.trust{{font:500 14px/1.5 var(--head);letter-spacing:.02em;color:rgba(255,255,255,.85);max-width:620px}}
.banner{{display:inline-flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:center}}
.banner .g-mark{{width:18px;height:18px;flex:none}}
.banner .stars{{font-size:17px;letter-spacing:2px}}
.star-off{{opacity:.28}}
.empty-banner{{border:1px dashed rgba(255,255,255,.5);border-radius:6px;padding:4px 10px;color:rgba(255,255,255,.75)}}
.rating.empty-banner{{border-color:#B9BFB4;color:#6B7265}}
.quote-top{{display:flex;align-items:center;justify-content:space-between}}
.quote-top .g-mark{{width:20px;height:20px}}
.quote .who .muted{{font-weight:400;color:var(--grey)}}
.top nav{{display:flex;gap:18px;margin-left:24px;white-space:nowrap}}
.top nav a{{font:500 14px/1 var(--head);color:var(--ink);white-space:nowrap}}
.top nav a:hover{{color:var(--brand)}}
.top.dark{{background:#1A1B1E;border-bottom-color:#2A2B2F}}
.top.dark nav a,.top.dark .phone,.top.dark .name{{color:#FFFFFF}}
.top.dark nav a:hover{{color:var(--eyebrow)}}
/* hero.light (his Tru Definition audit, 2026-10-06: "that white overlay on the background with black text"): a pale scrim over the photo, dark words */
.hero.light{{color:var(--ink);background:var(--white)}}
.hero.light .hero-bg::after{{background:linear-gradient(180deg,rgba(255,255,255,.86),rgba(255,255,255,.74))}}
.hero.light h1{{color:var(--ink)}}
.hero.light .sub{{color:var(--grey)}}
.hero.light .eyebrow{{color:var(--brand)}}
.hero.light .trust{{color:var(--grey)}}
.quotes{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px}}
.quote{{border-radius:12px;padding:28px;display:grid;gap:12px;align-content:start;background:var(--mist)}}
.quote p{{font-size:16px;line-height:1.6;color:var(--ink)}}
.quote .who{{font:600 14px/1.3 var(--head);color:var(--grey)}}
.rating{{margin-top:14px;display:flex;justify-content:center;font:600 15px/1.4 var(--head);color:var(--ink)}}
.rating .stars{{margin-right:6px}}
.stars{{color:#F2B01E;font-size:19px;letter-spacing:3px}}
.cards{{display:grid;gap:24px}}
.card{{background:var(--brand);color:var(--white);border-radius:12px;padding:32px 28px;display:grid;gap:14px;align-content:start}}
.card h3{{color:var(--white)}}
.card svg{{width:44px;height:44px;color:var(--white)}}
.card p{{font-size:16px;line-height:1.6;color:rgba(255,255,255,.95)}}
.card.dark,.card.dark h3,.card.dark svg{{color:var(--ink)}}
.card.dark p{{color:rgba(0,0,0,.82)}}
.ask{{display:grid;justify-items:center;gap:14px;margin-top:56px}}
.about{{background:var(--mist)}}
.about .col{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:56px;align-items:center}}
.about .eyebrow{{color:var(--brand)}}
.about p{{margin-top:20px}}
.team{{aspect-ratio:5/4;border-radius:12px;overflow:hidden;background:var(--white)}}
.team img{{width:100%;height:100%;object-fit:cover;object-position:50% 40%}}
.work{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px}}
.shot{{aspect-ratio:4/5;border-radius:12px;overflow:hidden;background:var(--mist)}}
.shot img{{width:100%;height:100%;object-fit:cover}}
.empty{{display:grid;place-items:center;border:2px dashed #B9BFB4;padding:20px;text-align:center;font:600 14px/1.45 var(--head);color:#6B7265;background:var(--mist)}}
.process{{color:var(--white);background:var(--black)}}
.process h2{{color:var(--white)}}
.process .eyebrow{{color:var(--eyebrow)}}
.steps{{display:grid;gap:24px;counter-reset:step}}
.step-card{{border-top:3px solid var(--accent);padding-top:20px;display:grid;gap:10px;align-content:start;counter-increment:step}}
.step-card::before{{content:counter(step);font:700 34px/1 var(--head);color:var(--accent)}}
.step-card h3{{color:var(--white);font-size:20px}}
.step-card p{{font-size:15px;line-height:1.6;color:rgba(255,255,255,.82)}}
.services .under{{margin-top:16px;font-size:18px;color:var(--grey)}}
.svcs{{display:grid;gap:20px}}
.svc{{display:grid;gap:10px;align-content:start;padding:26px 24px;border:1px solid var(--line);border-radius:12px;background:var(--white);transition:border-color .15s ease,transform .15s ease}}
.svc:hover{{border-color:var(--brand);transform:translateY(-2px)}}
.svc svg{{width:36px;height:36px;color:var(--brand)}}
.svc h3{{font-size:20px}}
.svc p{{font-size:15px;line-height:1.55}}
.col.narrow{{max-width:760px}}
.qas{{display:grid;gap:28px}}
.qa{{display:grid;gap:8px;padding-bottom:24px;border-bottom:1px solid var(--line)}}
.qa h3{{font-size:21px}}
.qa p{{font-size:16px;line-height:1.6}}
.final{{text-align:center}}
.final p{{margin-top:16px;font-size:19px}}
.final .btn{{margin-top:40px}}
footer{{background:var(--black);color:rgba(255,255,255,.78);padding:36px 0;font-size:14px}}
footer .col{{display:flex;flex-wrap:wrap;align-items:center;gap:12px 36px;max-width:1120px}}
footer strong{{font:600 15px/1 var(--head);color:var(--white)}}
footer .right{{margin-left:auto}}
footer .creds{{flex-basis:100%;padding-top:12px;border-top:1px solid rgba(255,255,255,.16);font-size:13px;color:rgba(255,255,255,.6)}}
.veil{{position:fixed;inset:0;z-index:20;display:none;place-items:center;padding:24px;background:rgba(0,0,0,.66)}}
.veil.open{{display:grid}}
.sheet{{position:relative;width:100%;max-width:520px;background:var(--white);border-radius:14px;padding:40px 36px 32px;display:grid;gap:24px}}
.sheet .x{{position:absolute;top:10px;right:12px;width:40px;height:40px;border:0;background:none;font-size:26px;line-height:1;color:var(--grey);border-radius:50%}}
.sheet .x:hover{{background:var(--mist)}}
.bar{{height:6px;border-radius:3px;background:var(--mist);overflow:hidden}}
.bar b{{display:block;height:100%;width:25%;background:var(--brand);transition:width .2s ease}}
.count{{font:600 13px/1 var(--head);letter-spacing:.12em;text-transform:uppercase;color:var(--grey)}}
.step{{display:none;gap:14px}}
.step.on{{display:grid}}
.step label{{font:700 26px/1.2 var(--head);color:var(--ink)}}
.step .hint{{font-size:15px;color:var(--grey)}}
.step input,.step textarea{{width:100%;border:2px solid #C8CCC4;border-radius:8px;padding:14px 16px;font:400 18px/1.4 var(--body);color:var(--ink)}}
.step textarea{{min-height:120px;resize:vertical}}
.step input:focus,.step textarea:focus{{border-color:var(--brand);outline:4px solid color-mix(in srgb,var(--brand) 22%,transparent)}}
.err{{min-height:20px;font-size:14px;color:#B3261E}}
.nav{{display:flex;align-items:center;gap:16px}}
.ghost{{border:0;background:none;font:600 16px/1 var(--head);color:var(--grey);padding:12px 8px;border-radius:6px}}
.ghost:hover{{color:var(--ink)}}
.nav .btn{{margin-left:auto;min-height:54px;padding:0 34px;font-size:18px}}
.sent{{display:none;gap:16px;text-align:center;justify-items:center}}
.sent.on{{display:grid}}
.sent .tick{{display:grid;place-items:center;width:64px;height:64px;border-radius:50%;background:var(--brand);color:var(--white)}}
.sent .tick svg{{width:32px;height:32px}}
.sent h3{{font-size:28px}}
.gcal{{width:100%;border:1px solid #DADCE0;border-radius:10px;background:#fff;text-align:left;font:400 12px/1.3 Arial,var(--body);color:#3C4043;overflow:hidden}}
.gc-top{{display:flex;align-items:center;gap:8px;padding:10px 12px;border-bottom:1px solid #DADCE0;font-size:13px}}
.gc-icon{{width:22px;height:22px}}
.gc-grid{{display:grid;grid-template-columns:44px repeat(5,minmax(0,1fr))}}
.gc-day{{padding:6px 4px;text-align:center;font-weight:700;border-bottom:1px solid #DADCE0;font-size:11px;color:#70757A}}
.gc-hour{{padding:4px;font-size:10px;color:#70757A;border-top:1px solid #F1F3F4;text-align:right}}
.gc-cell{{height:38px;border-top:1px solid #F1F3F4;border-left:1px solid #F1F3F4;padding:2px}}
.gc-ev{{height:100%;border-radius:4px;background:#E8EAED;color:#5F6368;padding:3px 5px;font-size:10px;overflow:hidden}}
.gc-ev.new{{background:var(--brand);color:#fff;display:grid;align-content:start;box-shadow:0 2px 6px rgba(0,0,0,.25);animation:gcin .6s ease both}}
.gc-ev.new b{{font-size:11px}}
@keyframes gcin{{from{{transform:translateY(-14px);opacity:0}}to{{transform:none;opacity:1}}}}
.gc-note{{padding:8px 12px;border-top:1px solid #DADCE0;font-size:11px;color:#5F6368}}
{bands}
@media (max-width:860px){{
  h1{{font-size:42px}}h2{{font-size:32px}}body{{font-size:16px}}
  section{{padding:72px 0}}
  .cards,.quotes,.work,.svcs{{grid-template-columns:1fr !important}}
  .steps{{grid-template-columns:1fr 1fr !important;gap:32px 20px}}
  .about .col{{grid-template-columns:1fr;gap:32px}}
  .hero .sub{{font-size:18px}}
  .hero .eyebrow{{font-size:12px}}
  .top .phone{{display:none}}
  .top nav{{display:none}}
  .top .btn{{margin-left:auto}}
  .btn{{width:100%;max-width:360px}}
  .top .btn{{width:auto;white-space:nowrap;padding:0 16px}}
  .top img{{max-width:52vw;height:auto !important;max-height:46px}}
  .sheet{{padding:36px 22px 24px}}
}}
@media (prefers-reduced-motion:reduce){{*{{transition:none !important;scroll-behavior:auto !important}}}}
"""


FORM_JS = r"""
(function () {
  var veil = document.getElementById("veil"), form = document.getElementById("form");
  var steps = [].slice.call(form.querySelectorAll(".step")), wrap = document.getElementById("steps-wrap");
  var bar = document.getElementById("bar"), count = document.getElementById("count"), err = document.getElementById("err");
  var back = document.getElementById("back"), next = document.getElementById("next"), sent = document.getElementById("sent");
  var cal = document.getElementById("cal"), at = 0, opener = null;
  function field(i) { return steps[i].querySelector("input, textarea"); }
  function show(i) {
    at = i;
    steps.forEach(function (s, n) { s.classList.toggle("on", n === i); });
    bar.style.width = ((i + 1) / steps.length * 100) + "%";
    count.textContent = "Step " + (i + 1) + " of " + steps.length;
    back.hidden = i === 0;
    next.textContent = i === steps.length - 1 ? "Send" : "OK";
    err.textContent = "";
    field(i).focus();
  }
  function problem(i) {
    var f = field(i), v = f.value.trim();
    if (!v) return "Please fill this in.";
    if (f.type === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) return "That email does not look right.";
    if (f.type === "tel" && v.replace(/\D/g, "").length < 10) return "Please enter a 10 digit number.";
    return "";
  }
  function open(from) {
    opener = from || null;
    wrap.style.display = "grid";
    sent.classList.remove("on");
    cal.classList.remove("on");
    veil.classList.add("open");
    document.body.style.overflow = "hidden";
    show(0);
  }
  function close() {
    veil.classList.remove("open");
    document.body.style.overflow = "";
    if (opener) opener.focus();
  }
  [].forEach.call(document.querySelectorAll("[data-book]"), function (b) { b.addEventListener("click", function () { open(b); }); });
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var p = problem(at);
    if (p) { err.textContent = p; field(at).focus(); return; }
    if (at < steps.length - 1) { show(at + 1); return; }
    var first = field(0).value.trim().split(/\s+/)[0];
    document.getElementById("sent-title").textContent = "Thank you, " + first + ".";
    var who = document.getElementById("cal-who"); if (who) who.textContent = "Consultation: " + first;
    wrap.style.display = "none";
    sent.classList.add("on");
    form.reset();
  });
  form.addEventListener("keydown", function (e) { if (e.key === "Enter" && e.target.tagName === "INPUT") { e.preventDefault(); next.click(); } });
  back.addEventListener("click", function () { if (at > 0) show(at - 1); });
  document.getElementById("close").addEventListener("click", close);
  document.getElementById("done").addEventListener("click", close);
  veil.addEventListener("mousedown", function (e) { if (e.target === veil) close(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && veil.classList.contains("open")) close(); });
  var q = new URLSearchParams(location.search);
  if (q.get("step")) { open(); show(Math.max(0, Math.min(steps.length - 1, parseInt(q.get("step"), 10) - 1))); }
  if (q.get("sent")) { open(); wrap.style.display = "none"; sent.classList.add("on"); }
})();
"""


FORM_STEPS = {
    "first_name": '<label for="f-name" id="form-title">What is your first name?</label><input id="f-name" name="first_name" type="text" autocomplete="given-name" required>',
    "phone": '<label for="f-phone">What is the best number to call?</label><input id="f-phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" required>',
    "email": '<label for="f-email">What is your email?</label><input id="f-email" name="email" type="email" autocomplete="email" inputmode="email" required>',
    "message": '<label for="f-msg">What would you like done?</label><div class="hint">{hint}</div><textarea id="f-msg" name="message" required></textarea>',
}


def form_html(spec, b):
    f = spec.get("form") or {}
    hint = f.get("hint", "A line or two is plenty.")
    # the order he said in that Loom: PHA's was first name, phone, email, message; the cold audits say first name, email, phone, message
    order = [k for k in (f.get("order") or ["first_name", "email", "phone", "message"]) if k in FORM_STEPS]
    if "first_name" not in order:
        order = ["first_name"] + order
    steps = "".join(f'<div class="step{" on" if i == 0 else ""}" data-step="{i + 1}">{FORM_STEPS[k].replace("{hint}", esc(hint))}</div>' for i, k in enumerate(order))
    return f"""
<div class="veil" id="veil" role="dialog" aria-modal="true" aria-labelledby="form-title">
  <form class="sheet" id="form" novalidate>
    <button class="x" type="button" id="close" aria-label="Close">&times;</button>
    <div id="steps-wrap" style="display:grid;gap:24px">
      <div style="display:grid;gap:12px"><div class="count" id="count">Step 1 of {len(order)}</div><div class="bar"><b id="bar"></b></div></div>
      {steps}
      <div class="err" id="err" role="alert"></div>
      <div class="nav"><button class="ghost" type="button" id="back" hidden>Back</button><button class="btn" type="submit" id="next">OK</button></div>
    </div>
    <div class="sent" id="sent">
      <div class="tick"><svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17l6 6 12-13"/></svg></div>
      <h3 id="sent-title">Thank you.</h3>
      <p id="sent-line">Your consultation is booked. It goes straight onto our calendar, and we confirm the time by email.</p>
      {calendar_html(spec)}
      <button class="ghost" type="button" id="done">Close</button>
    </div>
  </form>
</div>"""


def nav_html(spec, order):
    """The basic menu in the header (Jonathan, 2026-10-07: "The header should also have like the basic menu elements like
    home, services and the other basic stuff"), each link to a section the page has."""
    links = [("Home", "#top", True), ("Services", "#what", "cards" in order), ("About", "#about", "about" in order),
             ("Our work", "#work", "work" in order), ("Reviews", "#reviews", "reviews" in order), ("Contact", "#book", "final" in order)]
    return "<nav>" + "".join(f'<a href="{h}">{t}</a>' for t, h, ok in links if ok) + "</nav>"


def calendar_html(spec):
    """What happens after Send (Jonathan, 2026-10-07: "when booking happens [it] goes straight to Google Calendar for the
    owner to adjust for their consultation time"): the owner's week in a calendar, the new consultation landing in it. A
    picture of the hand-off, not a live calendar; the event's name fills in from the form's first answer."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    busy = {(0, 0): "Site visit", (2, 2): "Install", (3, 1): "Walkthrough", (4, 0): "Programming"}
    cells = []
    for h, hour in enumerate(["9 AM", "10 AM", "11 AM", "12 PM"]):
        cells.append(f'<div class="gc-hour">{hour}</div>')
        for d in range(5):
            if (d, h) == (1, 1):
                cells.append('<div class="gc-cell"><div class="gc-ev new"><b id="cal-who">Consultation</b><span>New booking</span></div></div>')
            elif (d, h) in busy:
                cells.append(f'<div class="gc-cell"><div class="gc-ev">{busy[(d, h)]}</div></div>')
            else:
                cells.append('<div class="gc-cell"></div>')
    head = "".join(f'<div class="gc-day">{x}</div>' for x in days)
    return (f'<div class="gcal" id="cal" aria-label="The owner\'s calendar">'
            f'<div class="gc-top"><svg viewBox="0 0 24 24" aria-hidden="true" class="gc-icon"><rect x="3" y="4" width="18" height="17" rx="3" fill="#fff" stroke="#1A73E8" stroke-width="1.6"/>'
            f'<rect x="3" y="4" width="18" height="5" rx="2" fill="#1A73E8"/><text x="12" y="18" text-anchor="middle" font-size="8" font-weight="700" fill="#1A73E8" font-family="Arial">31</text></svg>'
            f'<span><b>Google Calendar</b> · {esc(spec["company"])}</span></div>'
            f'<div class="gc-grid"><div></div>{head}{"".join(cells)}</div>'
            f'<div class="gc-note">Goes straight to the owner\'s calendar, who can move it to fit the consultation.</div></div>')


def build_html(spec):
    b = spec.get("button", "Book a meeting")
    order = [k for k in (spec.get("order") or DEFAULT_ORDER) if k == "hero" or k in spec]
    body = "".join(SECTIONS[k](spec, b) for k in order)
    tel = re.sub(r"\D", "", spec.get("phone", ""))
    tel_href = f"tel:+1{tel}" if len(tel) == 10 else f"tel:{tel}"
    lh = int(spec.get("logo_height") or 46)   # a wide lockup wants more than the 46 px default (Hatch Electric, 2026-10-06)
    hd = spec.get("header") or {}
    logo_src = (hd.get("logo") if hd.get("dark") else None) or spec.get("logo")
    logo = (f'<img src="{esc(logo_src)}" alt="{esc(spec["company"])}" style="height:{lh}px">' if spec.get("logo") else f'<span class="name">{esc(spec["company"])}</span>')
    phone_top = f'<a class="phone" href="{tel_href}">{esc(spec["phone"])}</a>' if spec.get("phone") else ""
    phone_foot = f'<a href="{tel_href}">{esc(spec["phone"])}</a>' if spec.get("phone") else ""
    foot = spec.get("footer") or {}
    creds = f'<span class="creds">{esc(foot["creds"])}</span>' if foot.get("creds") else ""
    areas = f'<span class="right">{esc(spec["areas"])}</span>' if spec.get("areas") else ""
    address = f'<span>{esc(spec["address"])}</span>' if spec.get("address") else ""
    title = spec.get("title") or f'{spec["hero"]["h1"]} | {spec["company"]}'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{esc(title)}</title>
<!-- A render, not their live page ({date.today().isoformat()}). Built by the page engine from spec.json beside this file,
     which carries Jonathan's Loom review of {esc(spec.get("page", "their page"))}. Their logo, faces, photos, and words come
     from their public site. The form sends nothing anywhere. Local only. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{fonts_link(spec["brand"])}" rel="stylesheet">
<style>{css(spec)}</style>
</head>
<body>
<header class="top{' dark' if hd.get('dark') else ''}"{f' style="background:{esc(hd["bg"])}"' if hd.get('dark') and hd.get('bg') else ''}><div class="col">{logo}{nav_html(spec, order)}{phone_top}<button class="btn small" type="button" data-book>{esc(b)}</button></div></header>
<main>
{body}
</main>
<footer><div class="col"><strong>{esc(spec["company"])}</strong>{address}{phone_foot}{areas}{creds}</div></footer>
{form_html(spec, b)}
<script>{FORM_JS}</script>
</body>
</html>
"""


# ---------------------------------------------------------------- commands

def spec_path(slug):
    return PROSPECTS / slug / "spec.json"


def load(slug):
    p = spec_path(slug)
    if not p.exists():
        sys.exit(f"No spec: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def cmd_build(slug):
    spec = load(slug)
    out = PROSPECTS / slug / "index.html"
    out.write_text(build_html(spec), encoding="utf-8")
    words = len(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[\s\S]*?</\1>", " ", build_html(spec))).split())
    print(f"{out.relative_to(ROOT).as_posix()} | {words} words | sections: {', '.join(k for k in (spec.get('order') or DEFAULT_ORDER) if k == 'hero' or k in spec)}")
    return out


def cmd_render(slug, day=None):
    page = PROSPECTS / slug / "index.html"
    if not page.exists():
        sys.exit(f"No page yet: run build {slug}")
    day = day or date.today().isoformat()
    out_dir = RENDERS / day
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [("after-1440", ["1440"]), ("after-fold-1536", ["1536", "780"]), ("after-390", ["390"])]
    made = []
    for name, args in jobs:
        png = out_dir / f"{slug}-{name}.png"
        p = subprocess.run([sys.executable, str(RENDER_PY), str(page), str(png), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if p.returncode:
            print(f"render failed for {name}: {p.stderr[-300:]}")
        else:
            made.append(png.relative_to(ROOT).as_posix())
    print(" | ".join(made) if made else "nothing rendered")
    return made


def cmd_check(slug):
    spec = load(slug)
    gaps = []
    if not (spec.get("hero") or {}).get("photo"):
        gaps.append("hero: no photo (plain black)")
    if not (spec.get("hero") or {}).get("trust"):
        gaps.append("hero: no rating line")
    if "work" in spec and len((spec["work"].get("photos") or [])) < 3:
        gaps.append(f"work: {len(spec['work'].get('photos') or [])} of 3 photos")
    if "about" in spec and not spec["about"].get("photo"):
        gaps.append("about: no photo")
    if "reviews" in spec and len((spec["reviews"].get("items") or [])) < 3:
        gaps.append(f"reviews: {len(spec['reviews'].get('items') or [])} of 3")
    if not spec.get("logo"):
        gaps.append("no logo (the name is set in type)")
    folder = PROSPECTS / slug
    for key in ("logo",):
        if spec.get(key) and not (folder / spec[key]).exists():
            gaps.append(f"{key} file missing: {spec[key]}")
    for k in ("hero", "about", "process"):
        ph = (spec.get(k) or {}).get("photo")
        if ph and not (folder / ph).exists():
            gaps.append(f"{k} photo file missing: {ph}")
    for x in (spec.get("work") or {}).get("photos") or []:
        if not (folder / x["src"]).exists():
            gaps.append(f"work photo file missing: {x['src']}")
    print(f"{slug}: " + ("; ".join(gaps) if gaps else "nothing marked empty"))
    return gaps


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("build", "render", "check", "all"):
        s = sub.add_parser(name)
        s.add_argument("slugs", nargs="+")
        s.add_argument("--date", default=None)
    a = ap.parse_args()
    for slug in a.slugs:
        if a.cmd == "build":
            cmd_build(slug)
        elif a.cmd == "render":
            cmd_render(slug, a.date)
        elif a.cmd == "check":
            cmd_check(slug)
        else:
            cmd_build(slug)
            cmd_check(slug)
            cmd_render(slug, a.date)


if __name__ == "__main__":
    main()
