"""Hero check: which residential integrators' first screen misses the ask, the centering, or the buyer's words.

The workflow of /list-building (Jonathan, 2026-10-05: "monitoring for a call to action in a booking form in the hero
section, centered text, a headline that matches buyer intent. And if it doesn't have that, that's our leads").

Three stages, every result appended to projects/outreach/hero-cache-<DATE>.jsonl so a crash resumes:
  A. Niche signals, free, from every site-cache-*.jsonl merged by domain: Lutron named, residential or commercial,
     integrator or not. Commercial-led, not-an-integrator, and One Firefly sites are dropped here, no browser, no model.
  B. The rendered hero, free: Playwright on headless Edge, 1440 x 900, tracking hosts blocked. The headline, the
     eyebrow, the sub line, the first-screen button, whether that button opens a form (static hooks, then one click),
     whether the headline is centered, and a JPEG of the first screen in projects/crm/shots/hero/.
     The rendered text of domains the 2026-09-13 static read missed goes through qualify_sites' own Opus read
     (the gap-fill), into site-cache-<DATE>.jsonl, so Residential and Lutron stop being unknown.
  C. Headline intent, a small Claude read (claude-opus-5, JSON schema, Batches API at half price): does the headline
     name the service, the place, and speak to the homeowner. A headline baked into a picture is read from the JPEG.

Verdict: lead = residential integrator with one or more of the three missing; not a lead = passes all three or
dropped in A; held = could not be read, with the reason.

Usage:
  python scripts/hero_check.py --dry-run                      # the quote: counts and the model estimate, no spend
  python scripts/hero_check.py --urls <url> [<url> ...] --no-batch   # fixtures, sync, instant
  python scripts/hero_check.py --limit 25 --no-batch         # the first 25 rows, sync, about $0.60
  python scripts/hero_check.py                               # the full list, batch
  python scripts/hero_check.py --build-only [--write-list]   # rebuild the xlsx (and the CRM's CSV) from the cache
Flags: --input <csv> (default: the newest projects/outreach/qualified-list-*.csv without hero columns),
  --require-lutron (Lutron becomes a gate, not a sort key), --all-rows (the CSV gets every row, not leads only),
  --write-list (write qualified-list-<DATE>.csv, which the CRM dials from; off until his 20-row check),
  --max-cost USD (default 20), --date YYYY-MM-DD, --no-wait, --concurrency N (default 5).
Keys: ANTHROPIC_API_KEY through scripts/outreach_common.load_env. Never types into or submits any form.
"""
import argparse
import asyncio
import base64
import csv
import json
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import openpyxl
from openpyxl.styles import Font

sys.path.insert(0, str(Path(__file__).resolve().parent))
from outreach_common import (  # noqa: E402
    OUTREACH, ROOT, UA, BudgetExceeded, CostMeter, budget_cap, get_secret, norm_domain,
)
import qualify_sites as qs  # noqa: E402
from page_shot import BLOCK  # noqa: E402
from seed_to_list import COLS  # noqa: E402

SHOTS = ROOT / "projects" / "crm" / "shots" / "hero"
VIEW_W, VIEW_H = 1440, 900
GOTO_TIMEOUT_MS = 25000
SETTLE_S = 1.5
CLICK_WAIT_S = 2.0
DOM_TEXT_CAP = 6000
EST_OUTPUT_TOKENS = 600          # the intent answer plus thinking at effort low
DEFAULT_MAX_COST = 20.0
HERO_COLS = ["Hero CTA", "Hero form", "Centered", "Intent headline", "Lutron", "Residential", "Verdict", "Reason",
             "Checked", "Headline", "Button label", "Shot"]

BOOKING_HOSTS = ("calendar.google.com/calendar/appointments", "calendar.app.google", "calendly.com", "acuityscheduling.com", "as.me", "meetings.hubspot.com", "hsforms.com",
                 "hsforms.net", "leadconnectorhq.com", "msgsndr.com", "housecallpro.com", "clienthub.app",
                 "servicetitan.com", "squareup.com/appointments", "square.site", "setmore.com", "youcanbook.me",
                 "cal.com", "zcal.co", "tidycal.com", "oncehub.com", "zohobookings.com", "bookings.zoho",
                 "jotform.com", "typeform.com", "vcita.com", "thryv.com", "workiz.com", "schedulicity.com",
                 "appointlet.com", "simplybook", "picktime.com", "bookafy.com", "zencal", "savvycal.com")
CONTACT_PATH_RE = re.compile(r"/(contact|book|booking|schedule|scheduling|consult|consultation|quote|estimate|"
                             r"get-started|getstarted|appointment|request)", re.I)
MODAL_ATTR_RE = re.compile(r"data-(bs-)?toggle|data-target|data-popup|data-modal|data-open|data-elementor-open-"
                           r"lightbox|elementor-popup|popmake|data-remodal|data-fancybox|data-lity|data-micromodal|"
                           r"data-featherlight|data-magnific|data-izimodal", re.I)
COOKIE_RE = re.compile(r"^(accept( all)?( cookies)?|i accept|agree|i agree|got it|ok(ay)?|allow( all)?|close|"
                       r"dismiss|continue|understood|yes)\W*$", re.I)
BOT_WALL_RE = re.compile(r"just a moment|access denied|attention required|verify you are|are you a robot|"
                         r"captcha|forbidden", re.I)
LUTRON_RE = re.compile(r"\blutron\b", re.I)

# Buyer words for the integrator trade, the same list the free campaign builds its searches from.
try:
    from free_campaign import TRADES as _TRADES  # noqa: E402
    BUYER_WORDS = sorted({w for s in _TRADES["integrator"]["services"] for w in s["words"]})
except Exception:  # noqa: BLE001
    BUYER_WORDS = ["lighting control", "lutron", "home theater", "smart home", "automation", "motorized shades",
                   "whole home audio", "media room"]

INTENT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["names_service", "names_place", "names_buyer", "speaks_to_homeowner", "service_named",
                 "place_named", "confidence", "reason"],
    "properties": {
        "names_service": {"type": "boolean",
                          "description": "The headline (with its eyebrow and sub line) says what is offered: a "
                                         "service a homeowner would search for. A company name alone is false "
                                         "unless the name itself is a plain service description."},
        "names_place": {"type": "boolean", "description": "A city, county, region, or state is named."},
        "names_buyer": {"type": "boolean", "description": "It says who it is for: homeowners, a kind of home, "
                                                          "builders and designers, or the like."},
        "speaks_to_homeowner": {"type": "boolean",
                                "description": "The words are a homeowner's words (home, house, family, living, "
                                               "estate, room), not trade or commercial words (enterprise, pro AV, "
                                               "solutions, systems integration, commercial)."},
        "service_named": {"type": "string", "description": "The service, in the page's words, or empty."},
        "place_named": {"type": "string", "description": "The place, in the page's words, or empty."},
        "confidence": {"type": "number", "description": "0 to 1."},
        "reason": {"type": "string", "description": "One sentence, under 200 characters, plain facts."},
    },
}
PICTURE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["headline_text", "eyebrow_text", "sub_text", "looks_centered", "cta_label", "reason"],
    "properties": {
        "headline_text": {"type": "string", "description": "The largest line of words in the picture, or empty."},
        "eyebrow_text": {"type": "string", "description": "The short line right above the headline, or empty."},
        "sub_text": {"type": "string", "description": "The line right under the headline, or empty."},
        "looks_centered": {"type": "boolean", "description": "The headline block sits centered across the width."},
        "cta_label": {"type": "string", "description": "The label on the main button in the picture, or empty."},
        "reason": {"type": "string", "description": "One sentence, under 200 characters."},
    },
}


def intent_system_prompt():
    return (
        "You read the first screen of a home technology integrator's website for Monarc Build, a marketing agency "
        "that sells managed Google Ads, SEO, and web management to integrators doing residential work (lighting "
        "control, home automation, home theater, shades, whole-home audio) in high-end homes. You are given the "
        "eyebrow, the headline, the sub line, and the main button label of the hero, plus where the company is. "
        "Return one JSON object matching the schema. Judge only from the words given. A headline that is only the "
        "company name does not name the service. The place can be in the eyebrow or the sub line. "
        "Buyer words a homeowner types: " + ", ".join(BUYER_WORDS) + "."
    )


PICTURE_SYSTEM = ("You read a screenshot of the first screen of a website. Return one JSON object with the words you "
                  "can read in the hero, whether the headline block is centered across the width, and the main "
                  "button's label. Do not invent words you cannot read.")


# ---------------------------------------------------------------- input

def default_input():
    files = sorted(OUTREACH.glob("qualified-list-*.csv"))
    for p in reversed(files):
        with p.open(encoding="utf-8", newline="") as fh:
            hdr = next(csv.reader(fh), [])
        if "Verdict" not in hdr:
            return p
    return None


def load_rows(path):
    with Path(path).open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        site = (r.get("Website") or "").strip()
        dom = norm_domain(site)
        if not dom:
            continue
        r = dict(r)
        r["_key"], r["_url"] = dom, site
        out.append(r)
    return out


def rows_from_urls(urls):
    out = []
    for u in urls:
        if not re.match(r"^https?://", u, re.I):
            u = "https://" + u
        p = urlparse(u)
        key = norm_domain(u)
        slug = re.sub(r"[^a-z0-9]+", "-", p.path.lower()).strip("-")
        if slug:
            key = f"{key}/{slug}"
        row = {c: "" for c in COLS}
        row.update({"Name": key, "Website": u, "Source": "fixture", "_key": key, "_url": u})
        out.append(row)
    return out


def shot_name(key):
    return re.sub(r"[^a-z0-9.]+", "-", key.lower()).strip("-") + "-1440.jpg"


# ---------------------------------------------------------------- caches

def hero_cache_path(run_date):
    return OUTREACH / f"hero-cache-{run_date}.jsonl"


def hero_batches_path(run_date):
    return OUTREACH / f"hero-batches-{run_date}.json"


def load_hero_cache(path):
    """{kind: {key: record}} for kinds hero, intent, picture."""
    out = {"hero": {}, "intent": {}, "picture": {}}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").split("\n"):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        out.setdefault(row.get("kind", "hero"), {})[row["domain"]] = row
    return out


def append_hero(run_date, rec):
    with hero_cache_path(run_date).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_all_site_caches():
    """Every site-cache-*.jsonl, oldest to newest, merged by domain. Newer rows win."""
    sites, llms = {}, {}
    for p in sorted(OUTREACH.glob("site-cache-*.jsonl")):
        s, l = qs.load_site_cache(p)
        sites.update(s)
        llms.update(l)
    return sites, llms


# ---------------------------------------------------------------- stage A: niche signals

def niche(site, llm):
    """Returns dict(lutron, residential, integrator, drop) with yes/no/unknown and a drop reason or ''."""
    d = (llm or {}).get("data") if (llm or {}).get("ok") else None
    text = " ".join([(site or {}).get("text") or "", (site or {}).get("title") or ""] +
                    [sp.get("text") or "" for sp in (site or {}).get("subpages") or []])
    lutron = "unknown"
    if d is not None or text.strip():
        named = any(LUTRON_RE.search(b or "") for b in ((d or {}).get("brands") or []) +
                    ((d or {}).get("high_end_signals") or []))
        lutron = "yes" if (named or LUTRON_RE.search(text)) else "no"
    if d is None:
        residential, integrator = "unknown", "unknown"
    else:
        mf = d.get("market_focus")
        residential = ("yes" if mf in ("residential", "mixed_residential_lead")
                       else "no" if mf in ("commercial", "mixed_commercial_lead") else "unknown")
        integrator = "yes" if d.get("is_integrator") else "no"
    drop = ""
    if (site or {}).get("agency") == "one_firefly":
        drop = "One Firefly site (already agencied)"
    elif integrator == "no":
        drop = "not an integrator: " + (d.get("reason") or "")[:120]
    elif residential == "no":
        drop = f"commercial-focused ({d.get('market_focus', '').replace('_', ' ')})"
    return {"lutron": lutron, "residential": residential, "integrator": integrator, "drop": drop}


# ---------------------------------------------------------------- stage B: the rendered hero

HERO_JS = r"""
(vh) => {
  const vw = innerWidth;
  const rect = e => e.getBoundingClientRect();
  const txt = e => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
  const vis = e => {
    const r = rect(e); if (r.width < 2 || r.height < 2) return false;
    const cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) < 0.05) return false;
    if (!(r.top < vh && r.bottom > 0 && r.left < vw && r.right > 0)) return false;
    // a slider's cloned slide sits mostly off-screen: at least half of the element must be in view
    return (Math.min(r.right, vw) - Math.max(r.left, 0)) >= 0.5 * r.width;
  };
  // a short header is chrome; a tall one is the hero itself (many themes wrap the hero in <header>)
  const inChrome = e => {
    const h = e.closest('header, [role=banner]');
    if (h && rect(h).height < 200) return true;
    return !!e.closest('nav, [role=navigation], footer, [class*="cookie" i], [id*="cookie" i]');
  };
  const box = r => ({x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height)});

  // headline: first visible h1 in the first screen, else the largest visible text block
  let head = null;
  const h1s = [...document.querySelectorAll('h1')].filter(e => vis(e) && txt(e).length >= 3 && !inChrome(e));
  const fontOf = e => parseFloat(getComputedStyle(e).fontSize) || 0;
  document.querySelectorAll('[data-mb-cta],[data-mb-head]').forEach(e => { e.removeAttribute('data-mb-cta'); e.removeAttribute('data-mb-head'); });
  const cands = [...document.querySelectorAll('h1,h2,h3,[role=heading],p,div,span,strong,a')].filter(e => {
    if (!vis(e) || inChrome(e)) return false;
    if (e.children.length > 3) return false;
    if (fontOf(e) < 16) return false;               // an address bar or a caption is not a headline
    const t = txt(e); if (t.length < 3 || t.length > 120) return false;
    return rect(e).top < vh * 0.9;
  });
  cands.sort((a, b) => fontOf(b) - fontOf(a));
  const largest = cands[0] || null;
  // the first h1 is the headline unless it is small type and something much larger carries the hero
  if (h1s.length && (!largest || fontOf(h1s[0]) >= 0.6 * fontOf(largest) || fontOf(h1s[0]) >= 28)) head = h1s[0];
  else head = largest;
  const tag = head ? head.tagName.toLowerCase() : '';

  let headline = null, centered = 'unknown', centered_why = 'no headline text';
  if (head) {
    const r = rect(head); const cs = getComputedStyle(head);
    // line boxes
    const range = document.createRange(); range.selectNodeContents(head);
    const lines = {};
    for (const cr of range.getClientRects()) {
      if (cr.width < 4 || cr.height < 4) continue;
      const k = Math.round(cr.top / 6);
      const L = lines[k] || (lines[k] = {l: cr.left, r: cr.right});
      L.l = Math.min(L.l, cr.left); L.r = Math.max(L.r, cr.right);
    }
    const mids = Object.values(lines).map(L => (L.l + L.r) / 2);
    const mean = mids.length ? mids.reduce((a, b) => a + b, 0) / mids.length : (r.left + r.right) / 2;
    const nearMiddle = Math.abs(mean - vw / 2) <= vw * 0.10;
    const linesAgree = mids.length >= 2 && Math.max(...mids) - Math.min(...mids) <= vw * 0.03;
    const blockMid = Math.abs((r.left + r.right) / 2 - vw / 2) <= vw * 0.10;
    // the eye reads the words, not the box: the line boxes decide where the headline sits
    if (cs.textAlign === 'center' && nearMiddle) { centered = 'yes'; centered_why = 'text-align center, words at the middle'; }
    else if (linesAgree && nearMiddle) { centered = 'yes'; centered_why = 'line boxes agree at the middle'; }
    else if (cs.textAlign === 'center') { centered = 'no'; centered_why = `text-align center but the words sit at ${Math.round(100 * mean / vw)}% of the width (a half column)`; }
    else if (mids.length === 1 && nearMiddle && r.width < vw * 0.8) { centered = 'yes'; centered_why = 'one line at the middle'; }
    else { centered = 'no'; centered_why = `text-align ${cs.textAlign}, block middle at ${Math.round(100 * mean / vw)}% of the width`; }
    headline = {text: txt(head).slice(0, 200), tag, font: Math.round(parseFloat(cs.fontSize)), rect: box(r),
                align: cs.textAlign, lines: mids.length, h1_count: h1s.length};
    head.setAttribute('data-mb-head', '1');
  }

  // eyebrow and sub line
  let eyebrow = '', sub = '';
  if (head) {
    const hr = rect(head);
    const blocks = [...document.querySelectorAll('p,span,div,h2,h3,h4,h5,h6,small,em,strong')].filter(e =>
      vis(e) && !inChrome(e) && e !== head && !head.contains(e) && !e.contains(head) && e.children.length <= 2);
    let best = null, bestGap = 1e9;
    for (const e of blocks) {
      const t = txt(e); const r = rect(e);
      if (t.length < 2 || t.length > 60) continue;
      const gap = hr.top - r.bottom;
      if (gap >= -4 && gap <= 80 && gap < bestGap) { best = e; bestGap = gap; }
    }
    if (best) eyebrow = txt(best);
    best = null; bestGap = 1e9;
    for (const e of blocks) {
      const t = txt(e); const r = rect(e);
      if (t.length < 20 || t.length > 300) continue;
      if (e.matches('a,button') || e.closest('a,button')) continue;
      const gap = r.top - hr.bottom;
      if (gap >= -4 && gap <= 200 && gap < bestGap) { best = e; bestGap = gap; }
    }
    if (best) sub = txt(best).slice(0, 300);
  }

  // first-screen buttons outside header and nav
  const ctas = [];
  for (const e of document.querySelectorAll('a,button,[role=button],input[type=submit],input[type=button]')) {
    if (!vis(e) || inChrome(e)) continue;
    const label = (e.tagName === 'INPUT' ? (e.value || '') : txt(e)).trim();
    if (label.length < 2 || label.length > 40) continue;
    const r = rect(e);
    if (r.top > vh) continue;
    const cs = getComputedStyle(e);
    const looksButton = e.tagName !== 'A' || cs.backgroundColor !== 'rgba(0, 0, 0, 0)' || (cs.borderStyle !== 'none' && parseFloat(cs.borderWidth) > 0) || e.className.toString().match(/btn|button|cta/i);
    const attrs = [...e.attributes].filter(a => a.name.startsWith('data-') || a.name === 'onclick' || a.name === 'class' || a.name === 'id' || a.name === 'target')
      .map(a => `${a.name}=${String(a.value).slice(0, 80)}`).join(' ');
    let href = e.getAttribute('href') || '';
    let hash_has_form = null;
    if (href.startsWith('#') && href.length > 1) {
      try { const t = document.querySelector(href); if (t) hash_has_form = !!(t.querySelector('form') || t.querySelectorAll('input,textarea,select').length >= 2 || t.querySelector('iframe')); } catch (err) {}
    }
    const form = e.closest('form');
    const in_form = !!(form && form.querySelectorAll('input:not([type=hidden]),textarea,select').length >= 1);
    ctas.push({label: label.slice(0, 60), tag: e.tagName.toLowerCase(), href: href.slice(0, 300), attrs: attrs.slice(0, 400),
               rect: box(r), area: Math.round(r.width * r.height), looksButton: !!looksButton, hash_has_form, in_form});
  }
  ctas.sort((a, b) => (b.looksButton - a.looksButton) || (b.area - a.area));
  if (ctas.length) {
    const i = [...document.querySelectorAll('a,button,[role=button],input[type=submit],input[type=button]')]
      .filter(e => vis(e) && !inChrome(e)).find(e => {
        const label = (e.tagName === 'INPUT' ? (e.value || '') : txt(e)).trim().slice(0, 60);
        return label === ctas[0].label && Math.round(rect(e).top) === ctas[0].rect.y; });
    if (i) i.setAttribute('data-mb-cta', '1');
  }

  // a visible form with fields in the first screen
  const fields = [...document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=checkbox]),textarea,select')]
    .filter(e => vis(e) && !inChrome(e) && rect(e).top < vh);
  const named = fields.filter(e => /name|email|phone|tel|mail|first|last|address|zip/i.test((e.name || '') + ' ' + (e.id || '') + ' ' + (e.placeholder || '') + ' ' + (e.type || '')));
  const search = fields.filter(e => /search/i.test((e.name || '') + ' ' + (e.id || '') + ' ' + (e.placeholder || '') + ' ' + (e.type || '')));
  const iframes = [...document.querySelectorAll('iframe')].filter(e => vis(e)).map(e => (e.src || '').slice(0, 200));

  // a big picture or video in the first screen
  let bigImage = false;
  for (const e of document.querySelectorAll('body *')) {
    if (!vis(e)) continue;
    const r = rect(e); if (r.width * r.height < vw * vh * 0.25) continue;
    if (e.tagName === 'IMG' || e.tagName === 'VIDEO' || e.tagName === 'PICTURE') { bigImage = true; break; }
    const bg = getComputedStyle(e).backgroundImage;
    if (bg && bg !== 'none' && bg.includes('url(')) { bigImage = true; break; }
  }

  return {headline, centered, centered_why, eyebrow, sub, ctas: ctas.slice(0, 8), fields: fields.length - search.length,
          named_fields: named.length, iframes, bigImage, title: document.title.slice(0, 200),
          text: (document.body ? document.body.innerText : '').replace(/\s+/g, ' ').trim().slice(0, %DOM_CAP%)};
}
""".replace("%DOM_CAP%", str(DOM_TEXT_CAP))

AFTER_CLICK_JS = r"""
() => {
  const vis = e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 2 && r.height > 2 && cs.visibility !== 'hidden' && cs.display !== 'none' && parseFloat(cs.opacity) > 0.05; };
  const fields = [...document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=checkbox]),textarea,select')].filter(vis);
  const named = fields.filter(e => /name|email|phone|tel|mail|first|last|address|zip/i.test((e.name || '') + ' ' + (e.id || '') + ' ' + (e.placeholder || '') + ' ' + (e.type || '')));
  const forms = [...document.querySelectorAll('form')].filter(vis).length;
  const iframes = [...document.querySelectorAll('iframe')].filter(vis).map(e => (e.src || '').slice(0, 200));
  return {fields: fields.length, named_fields: named.length, forms, iframes, url: location.href};
}
"""

COOKIE_JS = r"""
() => {
  const txt = e => (e.innerText || e.textContent || e.value || '').replace(/\s+/g, ' ').trim();
  const vis = e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 2 && r.height > 2 && cs.visibility !== 'hidden' && cs.display !== 'none' && r.top < innerHeight && r.bottom > 0; };
  const re = /^(accept( all)?( cookies)?|i accept|agree|i agree|got it|ok(ay)?|allow( all)?|close|dismiss|continue|understood|yes)\W*$/i;
  for (const e of document.querySelectorAll('button,a,[role=button],input[type=button]')) {
    if (!vis(e)) continue;
    const wrap = e.closest('[class*="cookie" i],[id*="cookie" i],[class*="consent" i],[id*="consent" i],[class*="gdpr" i],[aria-label*="cookie" i],[class*="banner" i]');
    const label = txt(e); const aria = (e.getAttribute('aria-label') || '');
    if ((wrap && re.test(label)) || (/^(accept|agree)/i.test(label) && /cookie|consent/i.test(document.body.innerText.slice(0, 20000)) && wrap)) {
      e.setAttribute('data-mb-cookie', '1'); return label || aria;
    }
  }
  return '';
}
"""


def booking_host(url):
    u = (url or "").lower()
    return any(h in u for h in BOOKING_HOSTS)


def classify_static(cta, final_url):
    """Returns (form, evidence) or (None, why) when a click must decide."""
    href = cta.get("href") or ""
    attrs = cta.get("attrs") or ""
    if cta.get("in_form"):
        return "inline form", "the button sits in a form with fields"
    if href.startswith("tel:") or href.startswith("mailto:") or href.startswith("sms:"):
        return "phone", f"href {href[:40]}"
    if booking_host(href) or booking_host(attrs):
        return "booking widget", f"link to {urlparse(href).netloc or 'a booking host'}"
    if href.startswith("#") and len(href) > 1:
        if cta.get("hash_has_form") is True:
            return "modal form", f"anchor {href[:40]} holds a form"
        if cta.get("hash_has_form") is False:
            return None, f"anchor {href[:40]} holds no form; click decides"
    if MODAL_ATTR_RE.search(attrs) or href in ("", "#", "javascript:void(0)", "javascript:;"):
        return None, "popup hook; click decides"
    if re.match(r"^https?://", href, re.I):
        host = urlparse(href).netloc.lower().replace("www.", "")
        page_host = urlparse(final_url).netloc.lower().replace("www.", "")
        if host != page_host:
            return None, f"link off the site to {host}; click decides"
    path = urlparse(href).path if href else ""
    if CONTACT_PATH_RE.search(path or ""):
        return "contact page", f"link to {path}"
    if href and not href.startswith("#"):
        return "contact page", f"link to another page {path or href[:40]}"
    return None, "click decides"


async def render_one(context, row, run_date, sem, out):
    key, url = row["_key"], row["_url"]
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    rec = {"kind": "hero", "domain": key, "url": url, "ts": time.strftime("%Y-%m-%d %H:%M"), "ok": False}
    async with sem:
        page = await context.new_page()
        popups = []
        page.on("popup", lambda p: popups.append(p))
        try:
            try:
                resp = await page.goto(url, timeout=GOTO_TIMEOUT_MS, wait_until="domcontentloaded")
            except Exception as e:  # noqa: BLE001
                if url.startswith("https://"):
                    try:
                        resp = await page.goto("http://" + url[8:], timeout=GOTO_TIMEOUT_MS, wait_until="domcontentloaded")
                    except Exception as e2:  # noqa: BLE001
                        rec["error"] = "goto:" + type(e2).__name__
                        return rec
                else:
                    rec["error"] = "goto:" + type(e).__name__
                    return rec
            status = resp.status if resp else 0
            await page.wait_for_timeout(int(SETTLE_S * 1000))
            title = await page.title()
            rec.update({"final_url": page.url, "status": status, "title": title[:200]})
            if status >= 400 or BOT_WALL_RE.search(title or ""):
                rec["error"] = f"HTTP {status}" if status >= 400 else "bot wall: " + title[:60]
                return rec
            cookie = await page.evaluate(COOKIE_JS)
            if cookie:
                try:
                    await page.locator('[data-mb-cookie="1"]').first.click(timeout=1500)
                    await page.wait_for_timeout(500)
                    rec["cookie_dismissed"] = cookie
                except Exception:  # noqa: BLE001
                    pass
            SHOTS.mkdir(parents=True, exist_ok=True)
            shot = SHOTS / shot_name(key)
            await page.screenshot(path=str(shot), type="jpeg", quality=72,
                                  clip={"x": 0, "y": 0, "width": VIEW_W, "height": VIEW_H})
            rec["shot"] = str(shot.relative_to(ROOT)).replace("\\", "/")
            info = await page.evaluate(HERO_JS, VIEW_H)
            # a headline still sliding in, or a slider that changed its words: measure again after a moment
            for _ in range(2):
                h = info.get("headline") or {}
                r_ = h.get("rect") or {}
                moving = h and (r_.get("x", 0) < 0 or r_.get("x", 0) + r_.get("w", 0) > VIEW_W)
                await page.wait_for_timeout(1200)
                again = await page.evaluate(HERO_JS, VIEW_H)
                h2 = again.get("headline") or {}
                if h2.get("text") != h.get("text"):
                    rec["slider"] = True
                if moving or h2.get("text") != h.get("text") or (not h and h2):
                    info = again
                    continue
                break
            rec.update({"headline": info["headline"], "centered": info["centered"], "centered_why": info["centered_why"],
                        "eyebrow": info["eyebrow"], "sub": info["sub"], "ctas": info["ctas"], "fields": info["fields"],
                        "named_fields": info["named_fields"], "iframes": info["iframes"], "big_image": info["bigImage"],
                        "text": info["text"]})
            if BOT_WALL_RE.search(info["text"][:400] or "") and not info["headline"]:
                rec["error"] = "bot wall"
                return rec
            # the ask: static first
            cta = info["ctas"][0] if info["ctas"] else None
            if info["named_fields"] >= 2 and (not cta or cta.get("in_form")):
                rec.update({"cta": cta, "form": "inline form", "form_evidence": f"{info['named_fields']} fields in the first screen"})
            elif any(booking_host(s) for s in info["iframes"]):
                rec.update({"cta": cta, "form": "booking widget", "form_evidence": "booking iframe in the first screen"})
            elif not cta:
                rec.update({"cta": None, "form": "none", "form_evidence": "no button in the first screen outside the header"})
            else:
                form, why = classify_static(cta, page.url)
                if form:
                    rec.update({"cta": cta, "form": form, "form_evidence": why})
                else:
                    # one click, then look
                    before = {"fields": info["fields"], "named": info["named_fields"], "url": page.url}
                    try:
                        await page.locator('[data-mb-cta="1"]').first.click(timeout=3000, no_wait_after=True)
                    except Exception as e:  # noqa: BLE001
                        rec.update({"cta": cta, "form": "none", "form_evidence": f"click failed ({type(e).__name__}); {why}"})
                        return _finish(rec)
                    await page.wait_for_timeout(int(CLICK_WAIT_S * 1000))
                    popup_url = ""
                    for p in popups:
                        try:
                            popup_url = p.url
                            await p.close()
                        except Exception:  # noqa: BLE001
                            pass
                    try:
                        after = await page.evaluate(AFTER_CLICK_JS)
                    except Exception:  # noqa: BLE001
                        after = {"fields": 0, "named_fields": 0, "forms": 0, "iframes": [], "url": page.url}
                    if popup_url and booking_host(popup_url):
                        form, ev = "booking widget", f"opened {urlparse(popup_url).netloc}"
                    elif after["url"] != before["url"] and booking_host(after["url"]):
                        form, ev = "booking widget", f"went to {urlparse(after['url']).netloc}"
                    elif any(booking_host(s) for s in after["iframes"]):
                        form, ev = "booking widget", "a booking iframe appeared"
                    elif after["named_fields"] >= 2 or after["fields"] - before["fields"] >= 2:
                        form, ev = "modal form", f"{after['named_fields']} fields appeared after the click"
                    elif after["url"] != before["url"] and urlparse(after["url"]).netloc.replace("www.", "") == urlparse(before["url"]).netloc.replace("www.", ""):
                        p = urlparse(after["url"]).path
                        if CONTACT_PATH_RE.search(p or ""):
                            form, ev = "contact page", f"went to {p}"
                        else:
                            form, ev = "contact page", f"went to another page {p}"
                    elif popup_url:
                        form, ev = "none", f"opened {urlparse(popup_url).netloc}, not a booking host"
                    elif after["url"] != before["url"]:
                        form, ev = "none", f"went off the site to {urlparse(after['url']).netloc}, not a booking host"
                    else:
                        form, ev = "none", "nothing opened after the click"
                    rec.update({"cta": cta, "form": form, "form_evidence": ev + "; " + why})
            return _finish(rec)
        except Exception as e:  # noqa: BLE001
            rec["error"] = "render:" + type(e).__name__ + ":" + str(e)[:120]
            return rec
        finally:
            try:
                await page.close()
            except Exception:  # noqa: BLE001
                pass
            out.append(rec)


def _finish(rec):
    rec["ok"] = True
    # a blank first screen is held; one with a picture or words but no headline text goes to the picture read
    if not rec.get("headline") and not rec.get("big_image") and len(rec.get("text") or "") < 200:
        rec["ok"] = False
        rec["error"] = "blank first screen: no headline text, no big picture, under 200 characters"
    return rec


async def render_all(rows, run_date, concurrency):
    from playwright.async_api import async_playwright
    out = []
    sem = asyncio.Semaphore(concurrency)
    block = [b.replace("*.", "") for b in BLOCK]
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True,
                                          args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(viewport={"width": VIEW_W, "height": VIEW_H}, user_agent=UA,
                                            locale="en-US", ignore_https_errors=True)

        async def route(r):
            host = urlparse(r.request.url).netloc.lower()
            if any(host == b or host.endswith("." + b) for b in block):
                await r.abort()
            else:
                await r.continue_()
        await context.route("**/*", route)
        tasks = [render_one(context, r, run_date, sem, out) for r in rows]
        done = 0
        for fut in asyncio.as_completed(tasks):
            rec = await fut
            append_hero(run_date, rec)
            done += 1
            if done % 25 == 0 or done == len(rows):
                print(f"  rendered {done}/{len(rows)}", flush=True)
        await browser.close()
    return out


def render_missing(rows, run_date, concurrency, again=False):
    cache = load_hero_cache(hero_cache_path(run_date))
    todo = [r for r in rows if again or r["_key"] not in cache["hero"]]
    print(f"{len(rows)} rows, {len(cache['hero'])} rendered before, {len(todo)} to render", flush=True)
    if todo:
        asyncio.run(render_all(todo, run_date, concurrency))
    return load_hero_cache(hero_cache_path(run_date))


# ---------------------------------------------------------------- stage C: the reads

def intent_content(row, hero, pic=None):
    h = hero.get("headline") or {}
    eyebrow, headline, sub = hero.get("eyebrow", ""), h.get("text", ""), hero.get("sub", "")
    if pic:
        eyebrow = eyebrow or pic.get("eyebrow_text", "")
        headline = headline or pic.get("headline_text", "")
        sub = sub or pic.get("sub_text", "")
    button = (hero.get("cta") or {}).get("label", "") or (pic or {}).get("cta_label", "")
    return "\n".join([
        f"Company: {row.get('Name', '')}. Where: {row.get('City', '')}, {row.get('State', '')}.",
        f"Eyebrow: {eyebrow or '(none)'}",
        f"Headline: {headline or '(none)'}",
        f"Sub line: {sub or '(none)'}",
        f"Button: {button or '(none)'}",
        "Return the JSON object now.",
    ])


def intent_params(system_prompt, content):
    return {
        "model": qs.MODEL, "max_tokens": 1500,
        "system": [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": content}],
        "output_config": {"effort": "low", "format": {"type": "json_schema", "schema": INTENT_SCHEMA}},
    }


def picture_params(shot_path):
    data = base64.b64encode(Path(shot_path).read_bytes()).decode("ascii")
    return {
        "model": qs.MODEL, "max_tokens": 1500,
        "system": [{"type": "text", "text": PICTURE_SYSTEM}],
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}},
            {"type": "text", "text": "Return the JSON object now."}]}],
        "output_config": {"effort": "low", "format": {"type": "json_schema", "schema": PICTURE_SCHEMA}},
    }


def gap_site_record(row, hero):
    """A site record for site-cache-<DATE>.jsonl from the rendered page, so qualify_sites' read can run on it."""
    text = hero.get("text") or ""
    return {"kind": "site", "domain": row["_key"], "listed_url": row["_url"], "fetched": hero.get("ts"), "ok": True,
            "final_url": hero.get("final_url"), "https_ok": (hero.get("final_url") or "").startswith("https://"),
            "platform": "custom", "platform_evidence": ["rendered by hero_check"], "agency": "none",
            "title": hero.get("title", ""), "desc": "", "headings": [x for x in [(hero.get("headline") or {}).get("text")] if x],
            "nav": [], "text": text[:qs.HOME_TEXT_CAP], "text_len": len(text), "subpages": [], "rendered": True}


def estimate(system_prompt, contents, n_pictures, batch):
    in_rate, out_rate = (qs.BATCH_IN_PER_M, qs.BATCH_OUT_PER_M) if batch else (qs.SYNC_IN_PER_M, qs.SYNC_OUT_PER_M)
    in_tokens = sum(len(c) for c in contents) / 4 + len(system_prompt) / 4 + n_pictures * 1800
    out_tokens = EST_OUTPUT_TOKENS * (len(contents) + n_pictures)
    return round((in_tokens * in_rate + out_tokens * out_rate) / 1e6, 2)


def run_reads(client, jobs, run_date, meter, batch, wait):
    """jobs: [(custom_key, params, kind)] with custom_key 'i:<key>', 'p:<key>', or 'g:<key>'. Records every answer:
    intent and picture into the hero cache, gap-fill into site-cache-<DATE>.jsonl as qualify_sites' own llm record."""
    if not jobs:
        return
    params_by_key = {k: p for k, p, _ in jobs}
    kind_by_key = {k: kd for k, _, kd in jobs}
    site_cache = qs.cache_path(run_date)

    def on_result(ckey, msg, err):
        kind = kind_by_key.get(ckey, "intent")
        dom = ckey.split(":", 1)[1]
        if msg is not None:
            data, perr = qs.parse_message(msg)
            rec = qs.llm_record(dom, data, perr, msg, batch=batch, kind=kind)
        else:
            rec = qs.llm_record(dom, None, err, kind=kind)
        if kind == "llm":
            with site_cache.open("a", encoding="utf-8") as fh:
                qs.append_cache(fh, rec)
        else:
            append_hero(run_date, rec)
        return rec

    if batch:
        state_path = hero_batches_path(run_date)
        pending = state_path.exists() and any(not b.get("collected")
                                              for b in json.loads(state_path.read_text(encoding="utf-8"))["batches"])
        if not pending:
            qs.submit_batches(client, [(k, "") for k in params_by_key], "", run_date,
                              params_fn=lambda k, _c: params_by_key[k], state_path=state_path)
        else:
            print("Pending hero batch found; collecting it before submitting anything new.", flush=True)
        qs.collect_batches(client, run_date, meter, wait=wait, state_path=state_path, on_result=on_result)
        return
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def one(ckey):
        try:
            msg = client.messages.create(**params_by_key[ckey])
        except Exception as e:  # noqa: BLE001
            return on_result(ckey, None, "api:" + type(e).__name__ + ":" + str(e)[:160])
        return on_result(ckey, msg, None)

    with ThreadPoolExecutor(max_workers=4) as ex:
        for fut in as_completed([ex.submit(one, k) for k in params_by_key]):
            rec = fut.result()
            meter.add("opus_sync", (rec or {}).get("cost_usd", 0))


def plan_reads(rows, sites, llms, hero_cache, system_prompt, run_date):
    """Which reads are still due: gap-fill (g), picture (p), intent (i). Returns [(ckey, params, kind)]."""
    jobs = []
    for r in rows:
        key = r["_key"]
        hero = hero_cache["hero"].get(key)
        if not hero or not hero.get("ok"):
            continue
        site, llm = sites.get(key), llms.get(key)
        n = niche(site, llm)
        if n["drop"]:
            continue
        if n["residential"] == "unknown" and not (llm or {}).get("ok") and hero.get("text") and len(hero["text"]) >= qs.THIN_TEXT:
            srec = gap_site_record(r, hero)
            if not (site or {}).get("ok") or qs.is_thin(site):
                with qs.cache_path(run_date).open("a", encoding="utf-8") as fh:
                    qs.append_cache(fh, srec)      # the rendered text stands in for the static read
            company = {"Name": r.get("Name", ""), "City": r.get("City", ""), "State": r.get("State", ""),
                       "Website": r["_url"], "Primary type": "", "Rating": r.get("Rating", ""),
                       "Review count": r.get("Review count", "")}
            jobs.append((f"g:{key}", qs.request_params(qs.build_system_prompt(), qs.user_message(company, srec)), "llm"))
        has_text = bool((hero.get("headline") or {}).get("text"))
        pic = hero_cache["picture"].get(key)
        if not has_text and hero.get("shot") and not pic:
            jobs.append((f"p:{key}", picture_params(ROOT / hero["shot"]), "picture"))
            continue                       # the intent read waits for the picture's words
        if key in hero_cache["intent"] and hero_cache["intent"][key].get("ok"):
            continue
        pdata = (pic or {}).get("data") if (pic or {}).get("ok") else None
        if not has_text and not (pdata or {}).get("headline_text"):
            continue                       # nothing to read
        jobs.append((f"i:{key}", intent_params(system_prompt, intent_content(r, hero, pdata)), "intent"))
    return jobs


# ---------------------------------------------------------------- verdict and outputs

PASSING_FORMS = {"modal form", "booking widget", "inline form"}


def judge(row, site, llm, hero, intent, pic, require_lutron):
    n = niche(site, llm)
    out = {"Lutron": n["lutron"], "Residential": n["residential"], "Hero CTA": "", "Hero form": "", "Centered": "",
           "Intent headline": "", "Headline": "", "Button label": "", "Shot": (hero or {}).get("shot", "") or ""}
    pdata = (pic or {}).get("data") if (pic or {}).get("ok") else {}
    centered = "unknown"
    if hero and hero.get("ok"):
        # the facts seen on the first screen, shown even when the row is dropped for its niche
        h = hero.get("headline") or {}
        out["Headline"] = h.get("text") or pdata.get("headline_text", "")
        out["Button label"] = (hero.get("cta") or {}).get("label", "") or pdata.get("cta_label", "")
        out["Hero CTA"] = "yes" if (hero.get("cta") or out["Button label"]) else "no"
        out["Hero form"] = hero.get("form") or "none"
        centered = hero.get("centered") or "unknown"
        if centered == "unknown" and pdata:
            centered = "yes (visual)" if pdata.get("looks_centered") else "no (visual)"
        out["Centered"] = centered
    if n["drop"]:
        out.update({"Verdict": "not a lead", "Reason": n["drop"]})
        return out
    if not hero or not hero.get("ok"):
        out.update({"Verdict": "held", "Reason": "not rendered: " + ((hero or {}).get("error") or "not run")})
        return out
    idata = (intent or {}).get("data") if (intent or {}).get("ok") else None
    if idata is None:
        if not out["Headline"]:
            out.update({"Verdict": "held", "Reason": "no headline words found on the first screen"})
            return out
        out.update({"Verdict": "held", "Reason": "headline read not done: " + ((intent or {}).get("error") or "not run")})
        return out
    out["Intent headline"] = "yes" if (idata["names_service"] and idata["names_place"] and idata["speaks_to_homeowner"]) else "no"
    if n["residential"] == "unknown":
        out.update({"Verdict": "held", "Reason": "residential or commercial still unknown (no page read)"})
        return out
    if require_lutron and n["lutron"] != "yes":
        out.update({"Verdict": "not a lead", "Reason": "Lutron not named (gate on)"})
        return out
    fails = []
    if out["Hero form"] not in PASSING_FORMS:
        fails.append("no booking form from the first screen" if out["Hero CTA"] == "yes" else "no ask on the first screen")
    if not centered.startswith("yes"):
        fails.append("headline not centered")
    if out["Intent headline"] == "no":
        missing = [w for w, ok in (("service", idata["names_service"]), ("place", idata["names_place"]),
                                   ("homeowner words", idata["speaks_to_homeowner"])) if not ok]
        fails.append("headline misses " + ", ".join(missing))
    evidence = f" ({hero.get('form_evidence', '')}; {hero.get('centered_why', '')}; {idata.get('reason', '')})"
    if pdata:
        evidence = evidence[:-1] + "; read from the picture)"
    if fails:
        out.update({"Verdict": "lead", "Reason": "; ".join(fails) + evidence, "_fails": len(fails)})
    else:
        out.update({"Verdict": "not a lead", "Reason": "the first screen passes all three" + evidence})
    return out


def build_rows(rows, sites, llms, hero_cache, run_date, require_lutron):
    out = []
    for r in rows:
        key = r["_key"]
        j = judge(r, sites.get(key), llms.get(key), hero_cache["hero"].get(key), hero_cache["intent"].get(key),
                  hero_cache["picture"].get(key), require_lutron)
        rec = {c: r.get(c, "") for c in COLS}
        rec["Status"] = ""
        rec.update({c: j.get(c, "") for c in HERO_COLS})
        rec["Checked"] = run_date
        rec["_fails"] = j.get("_fails", 0)
        rec["_key"] = key
        out.append(rec)
    order = {"lead": 0, "held": 1, "not a lead": 2}

    def rc(r):
        try:
            return int(float(r.get("Review count") or 0))
        except ValueError:
            return 0
    out.sort(key=lambda r: (order[r["Verdict"]], 0 if r["Lutron"] == "yes" else 1, -r["_fails"], -rc(r), r["Name"]))
    return out


def method_lines(rows, built, hero_cache, meter, run_date, src, require_lutron):
    def count(key, subset=None):
        c = {}
        for r in (subset if subset is not None else built):
            c[r[key] or "?"] = c.get(r[key] or "?", 0) + 1
        return dict(sorted(c.items(), key=lambda kv: -kv[1]))
    leads = [r for r in built if r["Verdict"] == "lead"]
    held = [r for r in built if r["Verdict"] == "held"]
    nots = [r for r in built if r["Verdict"] == "not a lead"]
    dropped = [r for r in nots if not r["Hero form"]]
    rendered = sum(1 for r in built if (hero_cache["hero"].get(r["_key"]) or {}).get("ok"))
    return [
        f"Built {run_date} by scripts/hero_check.py from {src}. Model: {qs.MODEL}, structured JSON, effort low.",
        f"Rows in: {len(built)} = leads {len(leads)} + not a lead {len(nots)} + held {len(held)}.",
        f"Dropped before the browser (Stage A): {len(dropped)}: {json.dumps(count('Reason', [dict(r, Reason=r['Reason'].split(':')[0].split(' (')[0]) for r in dropped]))}",
        f"Rendered first screens: {rendered}. Held by reason: {json.dumps(count('Reason', [dict(r, Reason=r['Reason'].split(':')[0]) for r in held]))}",
        f"Leads by what fails: no form from the first screen {sum(1 for r in leads if r['Hero form'] not in PASSING_FORMS)}, "
        f"not centered {sum(1 for r in leads if not r['Centered'].startswith('yes'))}, "
        f"headline misses the buyer's words {sum(1 for r in leads if r['Intent headline'] == 'no')}.",
        f"Hero form across rendered rows: {json.dumps(count('Hero form', [r for r in built if r['Hero form']]))}",
        f"Lutron: {json.dumps(count('Lutron'))}. Residential: {json.dumps(count('Residential'))}. "
        f"Lutron gate: {'on' if require_lutron else 'off (a sort key)'}.",
        "A lead is a residential integrator whose first screen misses one or more of: a button that opens a form "
        "(modal form, booking widget, or inline form); a centered headline; a headline that names the service, the "
        "place, and speaks to the homeowner. Rules: projects/Landing Page Build/Taste Log.md and Style Guide Copy 11.",
        "Held rows are never leads. A held row was not rendered, had no headline words, or its page read is missing.",
        f"Spend this run: {json.dumps(meter.summary())}",
        "Nothing was typed into or submitted on any site. One click at most per site, on the first-screen button.",
    ]


def write_xlsx(built, lines, run_date):
    out = OUTREACH / f"hero-check-{run_date}.xlsx"
    cols = COLS + HERO_COLS
    wb = openpyxl.Workbook()
    first = True
    for title, subset in [("Leads", [r for r in built if r["Verdict"] == "lead"]),
                          ("Not a lead", [r for r in built if r["Verdict"] == "not a lead"]),
                          ("Held", [r for r in built if r["Verdict"] == "held"]), ("All", built)]:
        ws = wb.active if first else wb.create_sheet(title)
        ws.title = title
        first = False
        ws.append(cols)
        for r in subset:
            ws.append([r.get(c, "") if r.get(c) is not None else "" for c in cols])
        for c in ws[1]:
            c.font = Font(bold=True)
        ws.freeze_panes = "A2"
    ws = wb.create_sheet("Method")
    for line in lines:
        ws.append([line])
    wb.save(out)
    return out


def write_list(built, run_date, all_rows):
    out = OUTREACH / f"qualified-list-{run_date}.csv"
    rows = built if all_rows else [r for r in built if r["Verdict"] == "lead"]
    cols = COLS + HERO_COLS
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return out, len(rows)


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--input", default=None, help="the call list CSV (default: newest qualified-list-*.csv without hero columns)")
    ap.add_argument("--urls", nargs="*", default=None, help="fixture URLs instead of the CSV")
    ap.add_argument("--limit", type=int, default=0, help="only the first N rows")
    ap.add_argument("--dry-run", action="store_true", help="counts and the model estimate; no browser, no spend")
    ap.add_argument("--no-batch", action="store_true", help="synchronous reads at full price (small runs)")
    ap.add_argument("--no-wait", action="store_true", help="submit the batch and exit; rerun to collect")
    ap.add_argument("--build-only", action="store_true", help="rebuild outputs from the caches only")
    ap.add_argument("--require-lutron", action="store_true", help="Lutron named becomes a gate")
    ap.add_argument("--all-rows", action="store_true", help="the CSV gets every row, not leads only")
    ap.add_argument("--write-list", action="store_true", help="write qualified-list-<DATE>.csv (the CRM dials from it)")
    ap.add_argument("--again", action="store_true", help="render the given rows again even when cached (fixtures)")
    ap.add_argument("--max-cost", type=float, default=DEFAULT_MAX_COST)
    ap.add_argument("--concurrency", type=int, default=5)
    ap.add_argument("--date", default=date.today().isoformat())
    a = ap.parse_args(argv)

    if a.urls:
        rows, src = rows_from_urls(a.urls), "fixtures"
    else:
        src_path = Path(a.input) if a.input else default_input()
        if not src_path or not src_path.exists():
            sys.exit("No call list CSV. Pass --input or --urls.")
        rows, src = load_rows(src_path), src_path.name
    if a.limit:
        rows = rows[:a.limit]
    sites, llms = load_all_site_caches()
    hero_cache = load_hero_cache(hero_cache_path(a.date))
    already = {}
    for kind in ("intent", "picture"):
        for rec in hero_cache[kind].values():
            already["opus_prior"] = round(already.get("opus_prior", 0) + rec.get("cost_usd", 0), 4)
    meter = CostMeter(budget_cap(override=a.max_cost), already)
    system_prompt = intent_system_prompt()

    n = {r["_key"]: niche(sites.get(r["_key"]), llms.get(r["_key"])) for r in rows}
    dropped = [k for k, v in n.items() if v["drop"]]
    # fixtures are rendered whatever their niche, so a control page's hero read can be checked
    to_render = [r for r in rows if (a.urls or not n[r["_key"]]["drop"]) and (a.again or r["_key"] not in hero_cache["hero"])]
    print(f"{src}: {len(rows)} rows; dropped before the browser {len(dropped)}; "
          f"rendered before {sum(1 for r in rows if r['_key'] in hero_cache['hero'])}; to render {len(to_render)}", flush=True)

    if a.dry_run:
        unknown = sum(1 for v in n.values() if not v["drop"] and v["residential"] == "unknown")
        due = len(rows) - len(dropped)
        est = estimate(system_prompt, ["x" * 350] * due, int(due * 0.08), batch=not a.no_batch) + \
            qs.estimate_cost(qs.build_system_prompt(), ["x" * 4000] * unknown, batch=not a.no_batch)
        print(json.dumps({"rows": len(rows), "dropped_stage_a": len(dropped), "render_due": len(to_render),
                          "residential_unknown_gap_fill": unknown, "render_minutes_est": round(len(to_render) * 8 / a.concurrency / 60, 1),
                          "opus_estimate_usd": est, "lutron_named": sum(1 for v in n.values() if v["lutron"] == "yes"),
                          "cost": meter.summary()}, indent=2))
        return 0

    if not a.build_only:
        if to_render:
            hero_cache = render_missing([r for r in rows if a.urls or not n[r["_key"]]["drop"]], a.date, a.concurrency,
                                        again=a.again)
            if a.again:
                for r in rows:                     # the words may have changed; read them again
                    hero_cache["intent"].pop(r["_key"], None)
                    hero_cache["picture"].pop(r["_key"], None)
        jobs = plan_reads(rows, sites, llms, hero_cache, system_prompt, a.date)
        if jobs or hero_batches_path(a.date).exists():
            n_pic = sum(1 for _, _, k in jobs if k == "picture")
            est = estimate(system_prompt, [j[1]["messages"][0]["content"] for j in jobs if j[2] == "intent"], n_pic, batch=not a.no_batch) \
                + qs.estimate_cost(qs.build_system_prompt(), [j[1]["messages"][0]["content"] for j in jobs if j[2] == "llm"], batch=not a.no_batch)
            print(f"{len(jobs)} reads ({'sync' if a.no_batch else 'batch'}): "
                  f"{sum(1 for j in jobs if j[2] == 'intent')} headline, {n_pic} picture, "
                  f"{sum(1 for j in jobs if j[2] == 'llm')} gap-fill; estimated ${est:.2f}; "
                  f"spent so far ${meter.total:.2f} of ${meter.cap:.2f}", flush=True)
            try:
                meter.assert_affordable(est, "hero reads")
            except BudgetExceeded as e:
                sys.exit(f"STOPPED: {e}")
            import anthropic
            client = anthropic.Anthropic(api_key=get_secret(
                "ANTHROPIC_API_KEY", required=True,
                hint="Copy it from the Monarc OS main machine into %USERPROFILE%\\.monarc\\secrets.env."))
            run_reads(client, jobs, a.date, meter, batch=not a.no_batch, wait=not a.no_wait)
            hero_cache = load_hero_cache(hero_cache_path(a.date))
            sites, llms = load_all_site_caches()
            # pictures read: the intent read on their words is a second pass
            second = [j for j in plan_reads(rows, sites, llms, hero_cache, system_prompt, a.date) if j[2] == "intent"]
            if second and not (a.no_wait and not a.no_batch):
                print(f"{len(second)} headline reads from the pictures' words", flush=True)
                run_reads(client, second, a.date, meter, batch=False, wait=True)
                hero_cache = load_hero_cache(hero_cache_path(a.date))

    built = build_rows(rows, sites, llms, hero_cache, a.date, a.require_lutron)
    lines = method_lines(rows, built, hero_cache, meter, a.date, src, a.require_lutron)
    xlsx = write_xlsx(built, lines, a.date)
    summary = {"rows": len(built), "leads": sum(1 for r in built if r["Verdict"] == "lead"),
               "not_a_lead": sum(1 for r in built if r["Verdict"] == "not a lead"),
               "held": sum(1 for r in built if r["Verdict"] == "held"),
               "cost": meter.summary(), "xlsx": str(xlsx)}
    if a.write_list:
        out, k = write_list(built, a.date, a.all_rows)
        summary.update({"csv": str(out), "csv_rows": k})
    if a.urls:
        for r in built:
            print(f"- {r['_key']}: {r['Verdict']} | CTA {r['Hero CTA']} | form {r['Hero form']} | centered {r['Centered']} | "
                  f"intent {r['Intent headline']} | {r['Headline'][:70]!r} | {r['Reason'][:220]}")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
