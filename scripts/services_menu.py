"""The Services dropdown on monarcbuild.com's site pages (Jonathan, 2026-09-26: "a menu dropdown for services should hold
all of these individual landing pages").

Usage: python scripts/services_menu.py

Rewrites the menu on /about/ and /book/ from the LIVE list below. The six service pages carry no menu (Style Guide 6.1;
Jonathan's choice the same day). The homepage left this list on 2026-09-26: the new homepage carries the six services as
cards (build/home.body.html), so a new service goes there too. Only pages that are live go in the
list; add a service the day its page is pushed, rerun this, and push the two pages:

  python scripts/site_sync.py push about/index.html book/index.html

The menu sits between <!-- services-menu --> markers, with its style and script between <!-- services-menu-assets -->
markers in the head, so a rerun replaces them in place. Add ?menu=1 to a page's address to render it open.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "projects" / "monarcbuild-site"
PAGES = [SITE / "public_html" / "book" / "index.html"]  # the homepage left 2026-09-26 and /about/ 2026-09-27 (both carry the six service cards)

# (label, path). In the order Jonathan's build order ships them; only live pages.
LIVE = [
    ("Google Ads management", "/google-ads/"),
    ("Website design", "/website-build/"),
    ("SEO", "/seo/"),
    ("Email marketing", "/email-marketing/"),
    ("Facebook ads", "/facebook-ads/"),
    ("AI automation", "/ai-automation/"),
]

ASSETS = """<!-- services-menu-assets -->
<style>
.mb-svc{position:relative}
.mb-svc summary{list-style:none;cursor:pointer;display:inline-flex;align-items:center;gap:8px}
.mb-svc summary::-webkit-details-marker{display:none}
.mb-svc summary:focus-visible{outline:2px solid var(--mb-cobalt);outline-offset:4px}
.mb-svc-caret{width:7px;height:7px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:translateY(-2px) rotate(45deg);transition:transform .15s ease}
.mb-svc[open] .mb-svc-caret{transform:translateY(1px) rotate(-135deg)}
.mb-svc-menu{position:absolute;top:calc(100% + 18px);left:-14px;min-width:250px;display:grid;padding:8px;background:var(--mb-paper);border:1px solid var(--mb-line);box-shadow:0 12px 32px rgba(0,0,0,.08);z-index:50}
.mb-svc-menu a{display:block;padding:10px 12px;font-size:14px;color:var(--mb-ink-2);white-space:nowrap}
.mb-svc-menu a:hover,.mb-svc-menu a:focus-visible{color:var(--mb-cobalt);outline:none}
</style>
<script>
document.addEventListener('click',function(e){document.querySelectorAll('details.mb-svc[open]').forEach(function(d){if(!d.contains(e.target))d.removeAttribute('open');});});
document.addEventListener('keydown',function(e){if(e.key==='Escape')document.querySelectorAll('details.mb-svc[open]').forEach(function(d){d.removeAttribute('open');});});
document.addEventListener('DOMContentLoaded',function(){if(/[?&]menu=1/.test(location.search))document.querySelectorAll('details.mb-svc').forEach(function(d){d.setAttribute('open','');});});
</script>
<!-- /services-menu-assets -->"""

SUMMARY_CLASS = "text-sm font-medium text-[var(--mb-ink-2)] transition-colors hover:text-[var(--mb-cobalt)]"


def menu():
    links = "".join(f'<a href="{path}">{label}</a>' for label, path in LIVE)
    return (f'<!-- services-menu --><details class="mb-svc"><summary class="{SUMMARY_CLASS}">Services'
            f'<span class="mb-svc-caret" aria-hidden="true"></span></summary><div class="mb-svc-menu">{links}</div>'
            f'</details><!-- /services-menu -->')


def apply(text):
    # assets in the head
    if "<!-- services-menu-assets -->" in text:
        text = re.sub(r"<!-- services-menu-assets -->.*?<!-- /services-menu-assets -->", lambda m: ASSETS, text, flags=re.S)
    else:
        text = text.replace("</head>", ASSETS + "\n</head>", 1)
    # the menu as the first item of the header nav
    if "<!-- services-menu -->" in text:
        text = re.sub(r"<!-- services-menu -->.*?<!-- /services-menu -->", lambda m: menu(), text, flags=re.S)
    else:
        m = re.search(r'(<header\b.*?<nav\b[^>]*>)', text, flags=re.S)
        if not m:
            raise SystemExit("no <nav> inside the <header>")
        text = text[:m.end()] + menu() + text[m.end():]
    return text


def main():
    for p in PAGES:
        if not p.exists():
            raise SystemExit(f"missing {p}")
        before = p.read_text(encoding="utf-8")
        after = apply(before)
        p.write_text(after, encoding="utf-8")
        print(f"{p.relative_to(ROOT)}: menu with {len(LIVE)} service(s){' (changed)' if after != before else ' (no change)'}")


if __name__ == "__main__":
    main()
