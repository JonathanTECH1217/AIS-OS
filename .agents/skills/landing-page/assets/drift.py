"""Drift check: compare a monarcbuild.com page against the checkable rules in
projects/Landing Page Build/Style Guide.md.

Usage: python drift.py <page.html> [--type home|ad|legal] [--theme <name>] [--themes-dir <dir>]

Prints one line per finding, tagged with the Style Guide rule it breaks, then a
summary. Exit code 1 if anything was found. The rules the script cannot test
(two faces, real photos only, placeholder labels) are listed at the end for a
human pass.

Page type: "home" (default) checks the homepage anchors in order (round 3, 2026-09-27: hero, services, proof, fit, about,
questions, book). "ad" (Style Guide
section 6) skips the anchor check, allows form step buttons labeled exactly OK,
Back, Send, or Confirm appointment that carry a data-step-btn attribute, and requires
exactly three button instances (hero, final ask, floating pill). Auto-detected from
<meta name="mb-page-type" content="ad"> when --type is not given.

Theme (added 2026-09-25, Style Guide section 8): the palette, the button color, the
allowed font weights, and the button labels come from the page's theme file,
projects/Landing Page Build/themes/<name>.json, named by <meta name="mb-theme">
(default "house", the homepage and /av_marketing/ rules as they were). A service
page carries two labels: the hero label on the hero button and the floating pill
(two instances), the final-ask label on the final ask (one instance). When both
labels are the same word, three instances of it are expected, as before.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# The house theme, used when no theme file can be read (the constants before 2026-09-25).
HOUSE = {
    "name": "house",
    "palette": {"button": "#61534E", "ink": "#2F334D", "body": "#4B4C5C", "muted": "#6E6E78", "band": "#C2B3A9", "ground": "#F6F3EF", "white": "#FFFFFF"},
    "extra_hexes": [],
    "weights": [400],
    "labels": {"hero": "Book an appointment", "final": "Book an appointment", "legacy": "Book a 15 minute call"},
    "faces": {"heading": "Cormorant Garamond", "body": "Inter"},
}
ALWAYS_ALLOWED_HEXES = {"#fff", "#ffffff", "#000", "#000000"}  # pure white and the popup scrim black
STEP_LABELS = {"OK", "Back", "Send", "Confirm appointment"}  # Copy 6 exception; "Confirm appointment" added 2026-09-23 for the calendar step
AD_BUTTONS = 3  # Style Guide 6.2: hero, final ask, floating pill (2026-09-23 round 2)
ANCHORS = ["hero", "services", "proof", "fit", "about", "questions", "book"]  # the homepage, round 3 (2026-09-27; the 2026-09-13 list was hero, about, how, results, portfolio, offer, book)
HEADLINE_CAP = 8
SUB_CAP = 25
THEMES_DIR = Path(__file__).resolve().parents[4] / "projects" / "Landing Page Build" / "themes"


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.seq = []          # (tag, text, attrs) for h1, h2, h3, p, a, button
        self.ids = []
        self.imgs = []         # attrs dicts
        self.styles = []       # inline <style> text
        self.text_all = []
        self._open = []        # stack of [tag, attrs, buf]
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.append(a["id"])
        if tag == "img":
            self.imgs.append(a)
        if tag == "style":
            self._in_style = True
            self.styles.append("")
        if tag in ("h1", "h2", "h3", "p", "a", "button"):
            self._open.append([tag, a, []])

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False
        for i in range(len(self._open) - 1, -1, -1):
            if self._open[i][0] == tag:
                t, a, buf = self._open.pop(i)
                self.seq.append((t, " ".join("".join(buf).split()), a))
                break

    def handle_data(self, data):
        if self._in_style:
            self.styles[-1] += data
            return
        self.text_all.append(data)
        for o in self._open:
            o[2].append(data)


def words(s):
    return len([w for w in s.split() if w.strip()])


def flag_value(flags, name):
    if name in flags and flags.index(name) + 1 < len(flags):
        return flags[flags.index(name) + 1]
    return None


def load_theme(name, themes_dir):
    """Return (theme dict, note). Falls back to the built-in house constants."""
    path = Path(themes_dir) / f"{name}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f), f"theme {name} from {path.name}"
    if name == "house":
        return HOUSE, "theme house (built-in constants; themes/house.json not found)"
    return HOUSE, f"theme {name} not found in {themes_dir}; checked against house"


def theme_hexes(theme):
    """Every hex value the theme allows in page CSS, lowercased."""
    found = set()

    def walk(v):
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str):
            for h in re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", v):
                found.add(h.lower())

    walk(theme.get("palette", {}))
    walk(theme.get("extra_hexes", []))
    walk(theme.get("cards", {}))
    return found | ALWAYS_ALLOWED_HEXES


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    flags = sys.argv[1:]
    page_type = flag_value(flags, "--type")
    theme_name = flag_value(flags, "--theme")
    themes_dir = flag_value(flags, "--themes-dir") or THEMES_DIR
    # a flag's value is not a positional argument
    for name in ("--type", "--theme", "--themes-dir"):
        v = flag_value(flags, name)
        if v in args:
            args.remove(v)
    html = open(args[0], encoding="utf-8", errors="replace").read()
    if page_type is None:
        m = re.search(r'<meta\s+name="mb-page-type"\s+content="([^"]+)"', html)
        page_type = m.group(1) if m else "home"
    if theme_name is None:
        m = re.search(r'<meta\s+name="mb-theme"\s+content="([^"]+)"', html)
        theme_name = m.group(1) if m else "house"
    theme, theme_note = load_theme(theme_name, themes_dir)
    ad = page_type == "ad"
    palette = theme_hexes(theme)
    accent = (theme.get("palette", {}).get("button") or "#61534E").lower()
    weights_allowed = set(int(w) for w in theme.get("weights", [400]))
    labels = theme.get("labels", {})
    hero_label = labels.get("hero", "Book an appointment")
    final_label = labels.get("final", hero_label)
    legacy_label = labels.get("legacy")
    allowed_labels = {hero_label, final_label} | ({legacy_label} if legacy_label else set())

    p = Page()
    p.feed(html)
    findings = []

    # Copy 1: one h1, headline and sub caps
    h1s = [s for s in p.seq if s[0] == "h1"]
    if len(h1s) != 1:
        findings.append(f"Copy 1: {len(h1s)} h1 elements (need exactly 1)")
    for i, (tag, text, attrs) in enumerate(p.seq):
        if tag in ("h1", "h2"):
            n = words(text)
            if n > HEADLINE_CAP:
                findings.append(f"Copy 1: {tag} is {n} words (cap {HEADLINE_CAP}): \"{text}\"")
            for t2, tx2, a2 in p.seq[i + 1:]:
                if t2 in ("h1", "h2"):
                    break
                if t2 == "p" and tx2:
                    n2 = words(tx2)
                    if n2 > SUB_CAP:
                        findings.append(f"Copy 1: sub after \"{text[:40]}\" is {n2} words (cap {SUB_CAP})")
                    break

    # Copy 2: em and en dashes (page text, alt, meta)
    if "—" in html or "–" in html:
        count = html.count("—") + html.count("–")
        findings.append(f"Copy 2: {count} em/en dash characters in the file")

    text = " ".join(" ".join(p.text_all).split())
    alts = " ".join(a.get("alt", "") for a in p.imgs)
    metas = " ".join(re.findall(r'content="([^"]*)"', html))
    corpus = f"{text} {alts} {metas}"

    # Copy 3: tenure
    for m in re.finditer(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+years?\b|\bsince\s+(19|20)\d\d\b|\bdecades?\b", corpus, re.I):
        ctx = corpus[max(0, m.start() - 30): m.end() + 30]
        findings.append(f"Copy 3: tenure claim: \"...{ctx}...\"")

    # Copy 9: no callback-time promise (Jonathan, 2026-09-23)
    for m in re.finditer(r"\b(calls?|called|calling|callback|call back|respond|responds|response|repl(?:y|ies)|text|texts|texted|answer|answers|answered)\b[^.]{0,40}?\b(within|inside|under)\s+(a\s+|an\s+)?(\d+|one|two|three|five|ten|fifteen|thirty|sixty)\s*(minutes?|hours?|seconds?)\b|\b(\d+|one|two|five|ten|fifteen|thirty)[\s-]*(minute|second)\s+(callback|call back|response|reply|text back)\b|\bsame[\s-]day\s+(callback|call back|response|reply)\b", corpus, re.I):
        ctx = corpus[max(0, m.start() - 30): m.end() + 30]
        findings.append(f"Copy 9: callback-time promise: \"...{ctx}...\"")

    # Copy 4: tier prices
    for m in re.finditer(r"\$\s?(2,?500|4,?500)\b", corpus):
        findings.append(f"Copy 4: tier price on page: {m.group(0)}")

    # Copy 5: PHA
    for m in re.finditer(r"\bPHA\b|pha\.systems|Performance Home Automation", corpus):
        findings.append(f"Copy 5: names the integrator: {m.group(0)}")

    # Copy 6: button labels, from the theme (two labels per service page, 2026-09-25)
    ctas = [(t, tx, a) for t, tx, a in p.seq if t in ("a", "button") and tx]
    wrong = set()
    for t, tx, a in ctas:
        if tx in STEP_LABELS and "data-step-btn" in a:
            continue  # Copy 6: step buttons inside a booking popup, any page (2026-09-19)
        cls = a.get("class", "")
        # whole words only: "Facebook and Instagram" is a link, not a "book a" button (2026-09-26, the homepage results)
        looks_like_button = "btn" in cls or "button" in cls or re.search(r"\bapply now\b|\bbook (?:a|an|the)\b|\bschedule\b|\bget started\b|\bget found\b|\bget your\b", tx, re.I)
        if looks_like_button and tx not in allowed_labels:
            wrong.add(tx)
    for w in sorted(wrong):
        findings.append(f"Copy 6: button label \"{w}\" (theme {theme.get('name', theme_name)} allows \"{hero_label}\" and \"{final_label}\")")
    if ad:
        if hero_label == final_label:
            n_main = sum(1 for t, tx, a in ctas if tx == hero_label)
            if n_main != AD_BUTTONS:
                findings.append(f"Copy 6 (ad): {n_main} \"{hero_label}\" buttons (an ad page needs exactly {AD_BUTTONS}: hero, final ask, pill)")
        else:
            n_hero = sum(1 for t, tx, a in ctas if tx == hero_label)
            n_final = sum(1 for t, tx, a in ctas if tx == final_label)
            if n_hero != 2:
                findings.append(f"Copy 6 (service page): {n_hero} \"{hero_label}\" buttons (need exactly 2: hero and the floating pill)")
            if n_final != 1:
                findings.append(f"Copy 6 (service page): {n_final} \"{final_label}\" buttons (need exactly 1: the final ask)")
        if legacy_label:
            n_legacy = sum(1 for t, tx, a in ctas if tx == legacy_label)
            if n_legacy:
                findings.append(f"Copy 6 (ad): {n_legacy} \"{legacy_label}\" buttons (old label; ad pages use the theme's labels)")

    # Layout: anchors in order (homepage only)
    if page_type == "home":  # "legal" pages (privacy, 2026-09-24) carry no homepage anchors and no buttons
        present = [i for i in ANCHORS if i in p.ids]
        missing = [i for i in ANCHORS if i not in p.ids]
        if missing:
            findings.append(f"Section Spec: missing anchors: {', '.join(missing)}")
        order = [i for i in p.ids if i in ANCHORS]
        if order != present:
            findings.append(f"Section Spec: anchors out of order: {order}")

    # Color 2: hex values outside the theme; Color 1: the button color present
    css = "\n".join(p.styles) + " " + " ".join(re.findall(r'style="([^"]*)"', html))
    hexes = {h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", css)}
    outside = sorted(h for h in hexes if h not in palette)
    if outside:
        findings.append(f"Color 2: colors outside the theme in CSS: {', '.join(outside)}")
    if accent not in hexes and "var(--accent" not in css and "var(--oak" not in css and "var(--button" not in css:
        findings.append(f"Color 1: button color {accent} not found in CSS")

    # Type 2: weights outside the theme
    bad_weights = []
    for m in re.finditer(r"font-weight\s*:\s*(bold|normal|[1-9]00)", css):
        v = m.group(1)
        w = 700 if v == "bold" else 400 if v == "normal" else int(v)
        if w not in weights_allowed:
            bad_weights.append(str(w))
    for m in re.finditer(r"font\s*:\s*(bold|[1-9]00)\s", css):
        v = m.group(1)
        w = 700 if v == "bold" else int(v)
        if w not in weights_allowed:
            bad_weights.append(str(w))
    if 700 not in weights_allowed:
        bad_weights += re.findall(r"\bfont-(?:bold|black|semibold|extrabold)\b", html)
    if bad_weights:
        findings.append(f"Type 2: {len(bad_weights)} weight declarations outside the theme (allowed: {sorted(weights_allowed)}): {sorted(set(bad_weights))[:6]}")

    # Media 5: alt text. A tracking pixel (1x1, hidden, alt="") is not a picture; skip it (LinkedIn Insight Tag, 2026-09-24).
    def pixel(a):
        return a.get("width") == "1" and a.get("height") == "1"
    noalt = [a.get("src", "?") for a in p.imgs if not a.get("alt", "").strip() and not pixel(a)]
    if noalt:
        findings.append(f"Media 5: {len(noalt)} images without alt text: {noalt[:3]}")

    for f in findings:
        print("-", f)
    print()
    print(f"{len(findings)} findings in {args[0]} (page type: {page_type}; {theme_note})")
    faces = theme.get("faces", {})
    print(f"Human pass still needed for: Type 1 (the theme's faces: {faces.get('heading')} for headings, {faces.get('body')} for body), Color 4 (one accent, no second saturated color beyond the theme), Media 1 to 3 (real photos on proof, renders as illustrations only, placeholders where a rule is pending), the fit block colors on headings and marks only, pending-rule labels present.")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
