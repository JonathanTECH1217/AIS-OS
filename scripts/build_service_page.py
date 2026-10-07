"""Assemble a service page (Style Guide 6.16), or the homepage, from the shared parts.

Usage: python scripts/build_service_page.py <slug> [--force]
Example: python scripts/build_service_page.py google-ads
         python scripts/build_service_page.py home        (the search-page homepage, 2026-09-26)

Takes the tracking head, the booking popup, and the booking script from the built /website-build/ page (the tested
code, copied as is), swaps in the page's address, the page label, the theme, the two button labels, the title, and the
description, and wraps the page body from projects/Landing Page Build/build/<slug>.body.html with the shared
stylesheet build/service-page.css (and any page stylesheet named in PAGES). Every page gets the favicon links; the
marker <!-- brand-lockup --> in a body is replaced by the Monarc Build lockup (build/brand-lockup.html, made by
brand/make_brand.py), <!-- other-services --> by the row of links to the other service pages, and <!-- logo-banner -->
by the logo banner ("We list your business on", 2026-09-28). Writes projects/monarcbuild-site/public_html/<slug>/index.html (the homepage: index.html, kept
indexed, with its canonical, link preview, and organization data). Refuses to overwrite an existing page unless
--force is given. Pushes nothing.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LPB = ROOT / "projects" / "Landing Page Build"
SITE = ROOT / "projects" / "monarcbuild-site" / "public_html"
# The house-style /website-build/ build of 2026-09-25, archived before its editorial rebuild: the source of the shared
# tracking head, booking popup, and booking script for every service page.
SOURCE = ROOT / "archives" / "site-website-build-house-2026-09-25" / "index.html"

PAGES = {
    "google-ads": {
        "theme": "google",
        "label": "google_ads",
        "title": "Managed Google Ads for contractors: Monarc Build",
        "description": "Managed Google Ads for contractors: campaigns rebuilt around the searches your buyers type, one page per keyword group, every lead tagged to the keyword that paid, and a monthly report you can read.",
        "queries": ["lighting control installer near me", "standby generator installer", "slate roof repair", "ductless mini split installer", "tankless water heater install"],
    },
    "seo": {
        "theme": "saas",
        "label": "seo",
        "title": "SEO for home services: Monarc Build",
        "description": "SEO for home service companies in four parts: your Google Business Profile, pages that rank, showing up in AI answers, and copy written in your trade's words.",
    },
    "website-build": {
        "theme": "editorial",
        "label": "website_build",
        "title": "Contractor website design that books the job: Monarc Build",
        "description": "Contractor website design built to book the job: one page per service and per area, a three field form above the fold, and copy matched to the search that brought the buyer.",
    },
    "email-marketing": {
        "theme": "commercial",
        "label": "email_marketing",
        "title": "Email marketing for contractors: Monarc Build",
        "description": "Email marketing for contractors: four sequences in your voice for past clients, new leads, open proposals, and finished installs, sent without anyone typing.",
    },
    "facebook-ads": {
        "theme": "social",
        "label": "facebook_ads",
        "title": "Facebook ads for contractors: Monarc Build",
        "description": "Facebook and Instagram ads for contractors: your finished jobs in front of the homeowners and builders in your service area, and again for everyone who visited.",
    },
    "ai-automation": {
        "theme": "time",
        "label": "ai_automation",
        "title": "AI automation for contractors: Monarc Build",
        "description": "AI automation for contractors: proposals, lead follow-up, invoices, and the books run without you typing, and a missed call gets a text back.",
    },
    # The homepage as a results page (Jonathan, 2026-09-26; brainstorms/2026-09-26-homepage-google-rebuild.md), in
    # Monarc's own theme since round 2 (2026-09-27: the Google look read as a copy). Indexed, page type home, no
    # page-view conversion (the shared conversion fires on ?sent=1 only, tracking checklist item 4).
    "home": {
        "theme": "monarc",
        "label": "home",
        "path": "/",
        "out": "index.html",
        "page_type": "home",
        "index": True,
        "asset_prefix": "",
        "css": ["service-page.css", "home.css"],
        "script": "home.js",
        "title": "Marketing for contractors: Monarc Build",
        "description": "Marketing for contractors, built by installers: Google Ads, websites, SEO, email, Facebook ads, and AI automation for home service companies.",
        "og_image": "https://monarcbuild.com/assets/og/home.jpg",
    },
    # /about/, rebuilt in the homepage's theme (Jonathan, 2026-09-27; brainstorms/2026-09-27-about-page-rebuild.md).
    # A site page (page type site: no homepage anchors, no ad-page counts), indexed.
    "about": {
        "theme": "monarc",
        "label": "about",
        "path": "/about/",
        "page_type": "site",
        "index": True,
        "css": ["service-page.css", "home.css", "about.css"],
        "title": "About Monarc Build: marketing built by installers",
        "description": "Jonathan Beach sold and installed control systems in high end homes before he marketed them. Monarc Build runs the marketing for the trades.",
        "og_image": "https://monarcbuild.com/assets/og/about.jpg",
    },
}

PAYLOAD_LINE = 'KEYS.concat(["landing_url","referrer"]).forEach(function(k){ if (store[k]) payload[k] = store[k]; });'
JOURNEY_LINE = "\n    if (window.mbJourney) payload.journey = window.mbJourney();"
JOURNEY_TAG = '<script src="/assets/journey.js" defer></script>\n'

FAVICONS = ('<link rel="icon" href="/favicon.ico" sizes="any">\n<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
            '<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n')

# The six service pages, for the "Other services" row above each one's footer (Jonathan, 2026-09-27: "Each page should
# also link internally to the other service pages"; a quiet row, Style Guide 6.1 dated exception). A body file marks the
# spot with <!-- other-services -->.
SERVICES = [("google-ads", "Google Ads management"), ("website-build", "Website design"), ("seo", "SEO"),
            ("email-marketing", "Email marketing"), ("facebook-ads", "Facebook ads"), ("ai-automation", "AI automation")]


def others_row(slug):
    links = "".join(f'<a href="/{s}/">{label}</a>' for s, label in SERVICES if s != slug)
    return (f'<nav class="svc-others" aria-label="Other services"><div class="col"><span class="label">Other services</span>'
            f'{links}</div></nav>')


# The logo banner right under the hero, on the homepage and the six service pages (Jonathan, 2026-09-28,
# brainstorms/2026-09-28-landing-pages-banner.md). A body file marks the spot with <!-- logo-banner -->. The label claims
# no partnership (Google's Misrepresentation policy, Q5b), and a page that sells a platform's ads leaves that
# platform's logo out (Q6). CSS: the template in assets/site.css (.logos, .logos-lg, .logos-top).
LOGOS = [("yelp", "Yelp"), ("google", "Google"), ("apple", "Apple"), ("facebook", "Facebook"), ("bing", "Bing"),
         ("angi", "Angi"), ("tripadvisor", "Tripadvisor")]
LOGOS_LEFT_OUT = {"google-ads": {"google"}, "facebook-ads": {"facebook"}}


def logo_banner(slug, prefix):
    logos = [(key, name) for key, name in LOGOS if key not in LOGOS_LEFT_OUT.get(slug, set())]
    imgs = "\n".join(f'<img class="logo-{key}" src="{prefix}assets/logos/{key}.svg" alt="{name}">' for key, name in logos)
    names = ", ".join(name for _, name in logos)
    return ('<section id="citations" class="logos logos-color logos-lg logos-top"><div class="col reveal">\n'
            '<span class="label">We list your business on</span>\n</div>\n'
            f'<div class="logo-ticker" aria-label="{names}"><div class="logo-track">\n'
            f'<span class="logo-set">\n{imgs}\n</span>\n<span class="logo-set" aria-hidden="true">\n{imgs}\n</span>\n'
            '</div></div>\n</section>')


def site_head(cfg, page_type):
    """An indexed page's extra head lines: canonical and the link preview; on the homepage, the organization too
    (no ratings, no reviews)."""
    url = "https://monarcbuild.com" + cfg["path"]
    lines = (f'<link rel="canonical" href="{url}">\n'
             f'<meta property="og:type" content="website">\n<meta property="og:url" content="{url}">\n'
             f'<meta property="og:title" content="{cfg["title"]}">\n<meta property="og:description" content="{cfg["description"]}">\n'
             f'<meta property="og:image" content="{cfg["og_image"]}">\n<meta name="twitter:card" content="summary_large_image">\n'
             f'<meta name="twitter:image" content="{cfg["og_image"]}">\n')
    if page_type == "home":
        org = {
            "@context": "https://schema.org", "@type": "ProfessionalService", "name": "Monarc Build", "legalName": "Monarc Build, LLC",
            "url": url, "logo": "https://monarcbuild.com/assets/brand/butterfly-512.png", "image": cfg["og_image"],
            "email": "jonathan@monarcbuild.com", "description": cfg["description"], "areaServed": "US",
            "address": {"@type": "PostalAddress", "addressLocality": "Annapolis", "addressRegion": "MD", "addressCountry": "US"},
        }
        lines += f'<script type="application/ld+json">{json.dumps(org)}</script>\n'
    return lines


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args or args[0] not in PAGES:
        sys.exit(__doc__ + f"\nKnown slugs: {', '.join(PAGES)}")
    slug = args[0]
    cfg = PAGES[slug]
    theme = json.loads((LPB / "themes" / f"{cfg['theme']}.json").read_text(encoding="utf-8"))
    hero_label, final_label = theme["labels"]["hero"], theme["labels"]["final"]
    path = cfg.get("path", f"/{slug}/")
    out = SITE / cfg.get("out", f"{slug}/index.html")
    if out.exists() and "--force" not in sys.argv:
        sys.exit(f"{out} exists; pass --force to overwrite")

    src = SOURCE.read_text(encoding="utf-8")
    head = src[: src.index("<link rel=\"preconnect\"")]
    page_type = cfg.get("page_type", "ad")
    head = head.replace("<meta name=\"mb-page-type\" content=\"ad\">", f"<meta name=\"mb-page-type\" content=\"{page_type}\">\n<meta name=\"mb-theme\" content=\"{cfg['theme']}\">")
    if cfg.get("index"):
        head = head.replace('<meta name="robots" content="noindex">\n', "")
    head = re.sub(r"<title>.*?</title>", f"<title>{cfg['title']}</title>", head)
    head = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{cfg["description"]}">', head)
    if cfg.get("index"):
        head = head.replace(f'<meta name="description" content="{cfg["description"]}">', f'<meta name="description" content="{cfg["description"]}">\n' + site_head(cfg, page_type).rstrip("\n"))
    head = head.replace("'page': 'website_build'", f"'page': '{cfg['label']}'")
    head = head.replace("<!DOCTYPE html><html lang=\"en\">", f"<!DOCTYPE html><html lang=\"en\" data-theme=\"{cfg['theme']}\">")
    prefix = cfg.get("asset_prefix", "../")
    fonts = (FAVICONS + f'<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
             f'<link href="{theme["google_fonts"]}" rel="stylesheet">\n<link rel="stylesheet" href="{prefix}assets/site.css">\n')
    css = "\n".join((LPB / "build" / name).read_text(encoding="utf-8") for name in cfg.get("css", ["service-page.css"]))

    tail = src[src.index("<a class=\"btn pill\""):]
    # the page's own address in the form's return link, its email subject, and the sent-state link
    tail = tail.replace("monarcbuild.com/website-build/", "monarcbuild.com" + path).replace("monarcbuild.com/website-build", "monarcbuild.com" + path.rstrip("/"))
    tail = tail.replace("website-build", slug).replace("website_build", cfg["label"])
    tail = tail.replace(">Book an appointment</a>\n\n<div class=\"modal\"", f">{hero_label}</a>\n\n<div class=\"modal\"", 1)
    tail = tail.replace('<span class="label" id="dialog-title">Book an appointment</span>', f'<span class="label" id="dialog-title">{hero_label}</span>')
    tail = tail.replace('a.textContent = "Book an appointment";', f'a.textContent = "{hero_label}";')
    # the search bar in the hero cycles the buyer queries; one static line on renders and under reduced motion
    queries = json.dumps(cfg.get("queries", []))
    cycler = ("<script>\n(function(){\n  var q = document.getElementById('q'); if (!q) return;\n"
              f"  var list = {queries};\n"
              "  var still = location.protocol === 'file:' || /[?&]static=1/.test(location.search) || !(window.matchMedia && matchMedia('(prefers-reduced-motion: no-preference)').matches);\n"
              "  if (still || !list.length) return;\n"
              "  var i = 0, n = 0, del = false;\n"
              "  function tick(){ var w = list[i]; if (!del) { n++; q.textContent = w.slice(0, n); if (n === w.length) { del = true; return setTimeout(tick, 1600); } }\n"
              "    else { n--; q.textContent = w.slice(0, n); if (n === 0) { del = false; i = (i + 1) % list.length; } }\n"
              "    setTimeout(tick, del ? 28 : 60); }\n"
              "  q.textContent = ''; setTimeout(tick, 400);\n})();\n</script>\n")
    # The visitor's journey (2026-09-28): assets/journey.js keeps the click that brought them and each page in their
    # browser, and the booking sends it with the rest, so the CRM can show a booker's whole trail.
    if PAYLOAD_LINE not in tail:
        sys.exit("The booking script no longer has the payload line the journey hooks onto; update PAYLOAD_LINE.")
    tail = tail.replace(PAYLOAD_LINE, PAYLOAD_LINE + JOURNEY_LINE)
    head = head.rstrip("\n") + "\n" + JOURNEY_TAG
    if cfg.get("script"):  # a page's own script (the homepage load-in) instead of the search-bar cycler
        cycler = "<script>\n" + (LPB / "build" / cfg["script"]).read_text(encoding="utf-8") + "</script>\n"
    body = (LPB / "build" / f"{slug}.body.html").read_text(encoding="utf-8")
    if "<!-- brand-lockup -->" in body:
        lockup = (LPB / "build" / "brand-lockup.html").read_text(encoding="utf-8")
        lockup = re.sub(r"<!--.*?-->\s*", "", lockup, flags=re.S).strip()
        body = body.replace("<!-- brand-lockup -->", lockup)
    if "<!-- other-services -->" in body:
        body = body.replace("<!-- other-services -->", others_row(slug))
    if "<!-- logo-banner -->" in body:
        body = body.replace("<!-- logo-banner -->", logo_banner(slug, prefix))
    page = (head + fonts + "<style>\n" + css + "</style>\n</head><body>\n<script>document.documentElement.className='js'</script>\n"
            + body + "\n" + tail.rstrip() + "\n" + cycler + "</body></html>\n")
    if "</body></html>" in tail:  # the source tail already closes the document; drop the duplicate close
        page = page.replace("</body></html>\n" + cycler + "</body></html>\n", cycler + "</body></html>\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"{out} written ({len(page) // 1024} KB); labels: {hero_label} / {final_label}")


if __name__ == "__main__":
    main()
