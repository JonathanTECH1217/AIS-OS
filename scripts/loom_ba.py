"""Loom B and A: the hands under the /loom-b-and-a skill (Jonathan, 2026-10-06: "We're going to make a skill called Loom B and A").

He records one Loom talking over a company's page and names the changes ("the hero should get centered", "cut the copy by
around twenty percent", "change the CTA from get a quote to book a meeting", "swap this stock background image"). The clone
reads the words with their times and writes a plan: each change, the second he names it, and what it does to the page.
This script makes the pictures and the video from that plan, on this laptop, with what is already here (Playwright on
headless Edge, ffmpeg, Parakeet through social_content.py). Nothing is uploaded, posted, or sent.

  python scripts/loom_ba.py states <plan.json>
        the page as it is, then the page after each change in turn: one JPEG a state (1440 x 900, the first screen),
        and a full-page JPEG of the finished page for the trailer scroll. Tracking hosts are blocked; nothing is typed
        into or sent from the page; the live site is never touched, only the copy in the browser. Writes states.json.
  python scripts/loom_ba.py cut <plan.json>
        the video, 1920 x 1080: his words tight (fillers, long pauses, and the plan's cuts out), and on screen the page
        state that matches what he is saying, each change fading in the second he names it (variation A). Variation B
        opens on a scroll of the finished page under his first words and closes on it under his last. Captions in
        Monarc Studio's style, the level at -14 LUFS. Over 5 minutes it refuses; over 3 it says so.
  python scripts/loom_ba.py check <video>
        the finisher's look (social_content.check)
  python scripts/loom_ba.py record --company <key> --loom <url> --cut A --subject S1 --body B1 [--watched yes|no] [--replied yes|no]
        one line in projects/loom-b-and-a/sends.json per video emailed: which subject line and body went with it, and
        later whether they watched and whether they wrote back. The subject-line test reads from this file.

The plan (projects/loom-b-and-a/plans/<date>-<company>-<A|B>.json):

  {"out": "media/looms/<set>/<name>.mp4", "kind": "loom-ba", "variation": "A",
   "company_key": "pha.systems", "url": "https://www.pha.systems/smart-lighting-control",
   "folder": "media/looms/<id>-<slug>",            the fetched Loom (social_content.py fetch)
   "start_at": 18.5, "end_at": 212.6,             his words before and after these are out
   "cuts": [[s, e, "why"]], "keep_whole": [], "pause": 0.5, "fixes": {},
   "changes": [{"at": 39.7, "kind": "headline", "text": "Lighting control installation in Annapolis"},
               {"at": 48.0, "kind": "center"}, {"at": 48.0, "kind": "bigger", "percent": 20}, ...],
   "render": "projects/Landing Page Build/prospects/<slug>/index.html",   the rebuilt page: its sizes are matched by every
                                                  live change (his rule 11), and section/form steps show it
   "match": true,                                 false keeps their page's own sizes
   "face": {"crop": "244:244:31:743", "size": 260, "pos": [48, 772]},     his bubble in the Loom frame, cut with his voice
   "finish": [{"kind": "sections", "pattern": "ABACABA", "colors": {"A": "...", "B": "...", "C": "..."}}],
                                                  his standing rules for the finished page that the Loom does not name;
                                                  applied after the last change, not a step in the video
   "trailer": {"under": [18.5, 27.7], "screens": 4},   B only: the finished page scrolls while these words play; "screens"
   "final": {"under": [185.8, 191.7]}}                 caps how far down it goes (0 or missing: the whole page)

Kinds of change `states` knows: headline {text}, eyebrow {text}, center, bigger {percent}, colors {text, background},
cta {text, href, background}, copy {keep: "first-sentence" | <percent> | "<the words to keep>"}, image {file},
sections {pattern, colors {A,B,C}, text {A,B,C}, photos: false to drop a section's photo; his A B A C A B A, 2026-10-06},
header (the render's own header laid over theirs, at the second he names the header; needs the plan's render),
font {family, weight} (a Google font on the headline), eyebrow {reuse: true} restyles the line already above the headline,
section {band} and form {step: 1 to 4, or "sent" for the thank-you screen with the calendar box}: a shot of the rebuilt page (the plan's "render", its index.html) at that section or form
step, for everything past what their live page can show,
hide {selector}, text {selector, text}, css {selector, style}, note (a change the page cannot show; the picture holds).
Any kind takes "selector" to aim at one element and "view" (a y in px) to scroll the shot to a change below the first screen.
"""
import argparse
import asyncio
import base64
import json
import math
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import social_content as scn  # noqa: E402
import studio_captions as caps_style  # noqa: E402
from page_shot import BLOCK  # noqa: E402

ROOT = scn.ROOT
PROJECT = ROOT / "projects" / "loom-b-and-a"
SENDS = PROJECT / "sends.json"
VIEW_W, VIEW_H = 1440, 900
PAGE_W, PAGE_H = 1728, 1080            # the 1440 x 900 state at frame height; 96 px of dark ground each side
GROUND = "0x0E1116"
FADE = 0.35                            # a change fades in over this many seconds after he names it
CAP_Y, CAP_SIZE = 985, 56              # captions over the lower band of the page on a 1920 x 1080 frame
MAX_S, GOOD_S = 300.0, 180.0           # his limits: under five minutes, three is "really really good"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0")

REF_JS = r"""
() => {
  // the finished render's own sizes for each hero part, so a live change lands at the size the render shows
  // (Jonathan, 2026-10-06: "all of the changes should match render frame 10 as they are changed")
  const props = ['fontFamily','fontSize','fontWeight','lineHeight','letterSpacing','textTransform','color','maxWidth',
                 'minHeight','paddingTop','paddingBottom','paddingLeft','paddingRight','borderRadius','backgroundColor',
                 'objectPosition','transform','transformOrigin','marginTop','textWrap'];
  const read = s => { const e = document.querySelector(s); if (!e) return null; const cs = getComputedStyle(e); const o = {};
    for (const p of props) o[p] = cs[p]; o._top = e.getBoundingClientRect().top; return o; };
  return {h1: read('.hero h1'), eyebrow: read('.hero .eyebrow'), sub: read('.hero .sub'), btn: read('.hero .btn'), img: read('.hero-bg img')};
}
"""

ALIGN_JS = r"""
(top) => {
  // once the hero is centered, its words sit at the render's height on the screen: the headline's top is moved to the
  // render's headline top (the block moves as one), measured fresh after every change so it never drifts
  const head = document.querySelector('[data-mb-head]'); if (!head) return 'no headline';
  let grid = head.parentElement;
  while (grid && grid !== document.body && getComputedStyle(grid).flexDirection !== 'column' && grid.getBoundingClientRect().width < innerWidth * 0.9) grid = grid.parentElement;
  if (!grid || grid === document.body) return 'no column to move';
  grid.style.transform = 'none';
  const d = Math.round(top - head.getBoundingClientRect().top);
  grid.style.transform = 'translateY(' + d + 'px)';
  return 'moved ' + d + 'px';
}
"""

EDIT_JS = r"""
(c) => {
  const R = c.ref || {};
  const fontsWanted = [];
  const match = (el, key, props) => {
    const r = R[key]; if (!el || !r) return;
    for (const p of props) if (r[p]) el.style.setProperty(p.replace(/[A-Z]/g, m => '-' + m.toLowerCase()), r[p], 'important');
    if (props.includes('fontFamily') && r.fontFamily) fontsWanted.push([r.fontFamily.split(',')[0].replace(/["']/g, '').trim(), r.fontWeight || '400']);
  };
  const withFonts = (msg) => {
    // a face the render uses but their page does not load (Manrope on the button): fetched before the shot
    if (!fontsWanted.length) return msg;
    return Promise.all(fontsWanted.map(([fam, wt]) => new Promise(res => {
      if (document.fonts.check(wt + ' 20px "' + fam + '"')) return res();
      const l = document.createElement('link'); l.rel = 'stylesheet';
      l.href = 'https://fonts.googleapis.com/css2?family=' + fam.replace(/ /g, '+') + ':wght@' + wt + '&display=block';
      l.onload = () => document.fonts.load(wt + ' 20px "' + fam + '"').then(res, res); l.onerror = res; document.head.appendChild(l);
      setTimeout(res, 5000);
    }))).then(() => msg);
  };
  const q = s => { try { return s ? document.querySelector(s) : null; } catch (e) { return null; } };
  const qa = s => { try { return s ? [...document.querySelectorAll(s)] : []; } catch (e) { return []; } };
  const rect = e => e.getBoundingClientRect();
  const vw = innerWidth, vh = innerHeight;
  const head = document.querySelector('[data-mb-head]');
  const cta = document.querySelector('[data-mb-cta]');
  const heroOf = e => {
    let n = e;
    while (n && n !== document.body) {
      const r = rect(n), cs = getComputedStyle(n);
      const bg = (cs.backgroundImage && cs.backgroundImage !== 'none') || (cs.backgroundColor && cs.backgroundColor !== 'rgba(0, 0, 0, 0)');
      if (r.width >= vw * 0.9 && (r.height >= vh * 0.45 || bg)) return n;
      n = n.parentElement;
    }
    return e ? e.parentElement : document.body;
  };
  const setText = (e, text) => {
    let best = null;
    const walk = document.createTreeWalker(e, NodeFilter.SHOW_TEXT);
    for (let n = walk.nextNode(); n; n = walk.nextNode()) if (n.textContent.trim().length > ((best && best.textContent.trim().length) || 0)) best = n;
    if (best) best.textContent = text;
    else { e.textContent = text; return; }   // an empty element (a button the engine just made): its one text node is the new words
    // any other text node in the element (a second line, a span) goes quiet so the new words stand alone
    const w2 = document.createTreeWalker(e, NodeFilter.SHOW_TEXT);
    for (let n = w2.nextNode(); n; n = w2.nextNode()) if (n !== best && n.textContent.trim()) n.textContent = ' ';
  };
  const subOf = () => {
    if (!head) return null;
    const hero = heroOf(head), hr = rect(head);
    let best = null, gap = 1e9;
    for (const e of hero.querySelectorAll('p,div,span,h2,h3')) {
      if (e === head || head.contains(e) || e.contains(head) || e.closest('a,button,nav')) continue;
      if (e.children.length > 1 && e.tagName !== 'P') continue;      // a paragraph with bold words inside still counts
      const t = (e.textContent || '').replace(/\s+/g, ' ').trim(); if (t.length < 20 || t.length > 900) continue;   // their copy runs long; that is the point
      const g = rect(e).top - hr.bottom; if (g >= -4 && g <= 240 && g < gap) { best = e; gap = g; }
    }
    return best;
  };
  const target = q(c.selector) || head;
  // a piece reused from inside a header the 'header' step put away (Holm's hero words were built from header items)
  // only the pieces that become the new hero (a headline, a button, words); a style on the rest of their header leaves it unseen
  const reuseKinds = ['headline', 'eyebrow', 'cta', 'copy', 'text', 'image', 'font', 'center', 'bigger'];
  const showing = e => e && e.closest && e.closest('[data-mb-hid]') && (reuseKinds.includes(c.kind) || e.matches('[data-mb-head], [data-mb-cta], [data-mb-eyebrow], [data-mb-show]'));
  if (c.kind !== 'header') [target, ...(c.selector ? qa(c.selector) : [])].forEach(e => { if (showing(e)) e.setAttribute('data-mb-show', '1'); });
  switch (c.kind) {
    case 'headline': {
      if (!target) return 'no headline on the page to change';
      setText(target, c.text); target.style.textTransform = 'none';
      match(target, 'h1', ['fontSize', 'lineHeight', 'maxWidth', 'textWrap']);
      return 'headline: ' + c.text;
    }
    case 'eyebrow': {
      if (!head) return 'no headline to sit under';
      if (c.reuse) {
        // their page already has a line above the headline: restyle that one instead of adding a second
        const hr = rect(head); let best = null, gap = 1e9;
        for (const e of heroOf(head).querySelectorAll('p,span,div,h2,h3,h4,h5,h6,em,strong')) {
          if (e === head || e.contains(head) || head.contains(e) || e.children.length > 2) continue;
          const t = (e.textContent || '').replace(/\s+/g, ' ').trim(); if (t.length < 3 || t.length > 160) continue;
          const g = hr.top - rect(e).bottom; if (g >= -4 && g <= 160 && g < gap) { best = e; gap = g; }
        }
        if (best) {
          if (c.text) setText(best, c.text);
          best.setAttribute('data-mb-eyebrow', '1');
          const col = c.color || (R.eyebrow && R.eyebrow.color) || '';
          for (const e of [best, ...best.querySelectorAll('*')]) { e.style.setProperty('color', col, 'important'); e.style.setProperty('font-style', 'normal', 'important'); }
          if (R.eyebrow) match(best, 'eyebrow', ['fontFamily', 'fontSize', 'fontWeight', 'letterSpacing', 'textTransform', 'lineHeight']);
          else Object.assign(best.style, {textTransform: 'uppercase', letterSpacing: '0.12em', fontWeight: '600', fontSize: c.size || '14px'});
          for (const e of best.querySelectorAll('*')) { e.style.setProperty('font-size', 'inherit', 'important'); e.style.setProperty('font-weight', 'inherit', 'important'); e.style.setProperty('letter-spacing', 'inherit', 'important'); e.style.setProperty('font-family', 'inherit', 'important'); }
          return withFonts('eyebrow restyled: ' + best.textContent.trim().slice(0, 60));
        }
      }
      let eb = document.querySelector('[data-mb-eyebrow]');
      if (!eb) { eb = document.createElement('p'); eb.setAttribute('data-mb-eyebrow', '1'); head.parentElement.insertBefore(eb, head); }
      eb.textContent = c.text;
      const cs = getComputedStyle(head);
      Object.assign(eb.style, {margin: '0 0 12px', fontSize: Math.max(14, Math.round(parseFloat(cs.fontSize) * 0.3)) + 'px', letterSpacing: '0.12em',
        textTransform: 'uppercase', fontWeight: '600', color: c.color || cs.color, textAlign: cs.textAlign, lineHeight: '1.3', fontFamily: cs.fontFamily});
      return 'eyebrow: ' + c.text;
    }
    case 'center': {
      if (!head) return 'no headline to center on';
      const hero = q(c.selector) || heroOf(head);
      const fix = e => {
        const cs = getComputedStyle(e);
        if (cs.display.includes('flex')) { if (cs.flexDirection.startsWith('column')) e.style.alignItems = 'center'; else e.style.justifyContent = 'center'; }
        else if (cs.display.includes('grid')) e.style.justifyItems = 'center';
        e.style.textAlign = 'center';
      };
      // a page builder grid (Squarespace's fluid engine, Wix, Elementor) pins each block to fixed rows, so a bigger
      // headline would overlap its neighbors: the hero's blocks become one centered column in their screen order, the
      // way the render stacks them, keeping the hero's height so the photo stays the same size
      let grid = head.parentElement;
      while (grid && grid !== document.body && !(getComputedStyle(grid).display.includes('grid') && rect(grid).width >= vw * 0.9)) grid = grid.parentElement;
      if (grid && grid !== document.body && c.restack !== false) {
        const kids = [...grid.children].filter(k => rect(k).height > 2 && rect(k).top < vh);
        kids.sort((a, b) => rect(a).top - rect(b).top).forEach((k, i) => { k.style.order = String(i); });
        const h0 = rect(grid).height;
        Object.assign(grid.style, {display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-start',
          gap: (R.h1 ? '26px' : '20px'), minHeight: h0 + 'px', paddingTop: '0px'});
        for (const k of grid.children) {
          Object.assign(k.style, {gridArea: 'auto', position: 'relative', width: 'min(960px, 92vw)', maxWidth: '960px', height: 'auto',
            margin: '0', left: 'auto', top: 'auto', transform: 'none'});
          for (const e of [k, ...k.querySelectorAll('*')]) {
            const cs = getComputedStyle(e);
            if (cs.textAlign === 'left' || cs.textAlign === 'start') e.style.textAlign = 'center';
            if (cs.display.includes('flex')) { e.style.justifyContent = 'center'; e.style.alignItems = 'center'; }
            if (cs.position === 'absolute' && e.tagName !== 'IMG') e.style.position = 'relative';
          }
          k.querySelectorAll('h1,h2,h3,p').forEach(e => { e.style.marginLeft = 'auto'; e.style.marginRight = 'auto'; });
        }
        return 'hero centered: ' + kids.length + ' blocks stacked in one column';
      }
      fix(hero);
      const hw = rect(hero).width, hl = rect(hero).left;
      // a two-column hero (words left, picture right): the words take the whole width
      let col = head; while (col && col.parentElement && col.parentElement !== hero) col = col.parentElement;
      if (col && col !== hero && rect(col).width < hw * 0.65) { Object.assign(col.style, {width: '100%', maxWidth: '100%', flex: '1 1 100%', gridColumn: '1 / -1'}); }
      const boxy = /^(a|button|img|picture|div|p|h1|h2|h3|h4|h5|h6|ul|form|section|span)$/i;
      for (const e of hero.querySelectorAll('*')) {
        const r = rect(e); if (r.width < 40 || r.height < 4) continue;
        const cs = getComputedStyle(e);
        if (cs.textAlign === 'left' || cs.textAlign === 'start') e.style.textAlign = 'center';
        if (cs.display.includes('flex') || cs.display.includes('grid')) fix(e);
        if (cs.position === 'absolute' || cs.position === 'fixed') continue;
        const offMiddle = Math.abs((r.left + r.right) / 2 - (hl + hw / 2)) > hw * 0.05;
        const parentGrid = e.parentElement && getComputedStyle(e.parentElement).display.includes('grid');
        if (parentGrid && r.width < hw * 0.9 && offMiddle) {
          // a grid block placed in columns (Squarespace's fluid engine, Wix, Elementor): the block keeps its row and takes the whole width, centered
          e.style.gridColumnStart = '1'; e.style.gridColumnEnd = '-1'; e.style.justifySelf = 'center'; e.style.maxWidth = '100%';
          if (!e.querySelector('p,h1,h2,h3,h4,h5,h6,li')) e.style.width = 'fit-content';
          continue;
        }
        if (r.width < hw * 0.9 && offMiddle) {
          // every box narrower than the hero that does not sit at its middle: auto margins (a block), or made a block first (an inline box)
          if (/^(inline-block|inline-flex|inline-grid)$/.test(cs.display) && boxy.test(e.tagName) && !(e.parentElement && e.parentElement.closest('p,h1,h2,h3'))) {
            e.style.display = 'block'; e.style.width = 'fit-content';
          }
          if (/^(block|flex|grid|table|list-item)$/.test(getComputedStyle(e).display)) { e.style.marginLeft = 'auto'; e.style.marginRight = 'auto'; }
        }
      }
      return 'hero centered';
    }
    case 'bigger': {
      if (!target) return 'nothing to make bigger';
      const f = parseFloat(getComputedStyle(target).fontSize);
      target.style.fontSize = Math.round(f * (1 + (c.percent || 20) / 100)) + 'px'; target.style.lineHeight = '1.1';
      return 'headline ' + (c.percent || 20) + '% bigger';
    }
    case 'colors': {
      if (!head) return 'no headline';
      const hero = q(c.selector) || heroOf(head);
      if (c.background) { hero.style.backgroundColor = c.background; if (c.background_image === false) hero.style.backgroundImage = 'none'; }
      if (c.text) for (const e of [head, document.querySelector('[data-mb-eyebrow]'), ...hero.querySelectorAll('p,h2,h3,span,li')]) if (e && !e.closest('a,button')) e.style.color = c.text;
      return 'colors: ' + [c.text && ('text ' + c.text), c.background && ('ground ' + c.background)].filter(Boolean).join(', ');
    }
    case 'cta': {
      let b = q(c.selector) || cta;
      if (!b) {
        b = document.createElement('a'); b.href = c.href || '#book'; b.setAttribute('data-mb-cta', '1');
        Object.assign(b.style, {display: 'inline-block', padding: '16px 34px', background: c.background || '#1E8E3E', color: c.color || '#fff', fontWeight: '700',
          borderRadius: '8px', textDecoration: 'none', marginTop: '24px', fontSize: '18px'});
        (subOf() || head).insertAdjacentElement('afterend', b);
      }
      setText(b, c.text);
      b.style.whiteSpace = 'nowrap'; b.style.width = 'auto'; b.style.minWidth = '0';
      if (c.background) b.style.background = c.background; if (c.color) b.style.color = c.color; if (c.href) b.setAttribute('href', c.href);
      if (R.btn) { Object.assign(b.style, {display: 'inline-flex', alignItems: 'center', justifyContent: 'center', boxSizing: 'border-box', height: 'auto'});
        match(b, 'btn', ['fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'minHeight', 'paddingLeft', 'paddingRight', 'paddingTop', 'paddingBottom', 'borderRadius']);
        for (const e of b.querySelectorAll('*')) { e.style.setProperty('font', 'inherit', 'important'); e.style.setProperty('color', 'inherit', 'important'); } }
      return withFonts('button: ' + c.text);
    }
    case 'copy': {
      const e = q(c.selector) || subOf();
      if (!e) return 'no copy under the headline to cut';
      const t = e.textContent.replace(/\s+/g, ' ').trim();
      let keep;
      if (typeof c.keep === 'number') { const ws = t.split(' '); keep = ws.slice(0, Math.max(3, Math.round(ws.length * (100 - c.keep) / 100))).join(' ').replace(/[,;:]$/, '') ; }
      else if (!c.keep || c.keep === 'first-sentence') keep = (t.match(/^.*?[.!?](\s|$)/) || [t])[0].trim();
      else keep = c.keep;
      setText(e, keep);
      if (R.sub) { match(e, 'sub', ['fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'maxWidth']); e.style.marginLeft = 'auto'; e.style.marginRight = 'auto';
        for (const x of e.querySelectorAll('*')) { x.style.setProperty('font-size', 'inherit', 'important'); x.style.setProperty('line-height', 'inherit', 'important'); } }
      return 'copy: ' + t.split(' ').length + ' words to ' + keep.split(' ').length;
    }
    case 'image': {
      // the largest picture in the first screen, anywhere on the page (a Squarespace hero keeps its photo outside the text grid)
      let best = null, area = 0;
      for (const e of document.querySelectorAll('body *')) {
        const r = rect(e), a = r.width * r.height; if (a < vw * vh * 0.15 || a <= area || r.top > vh * 0.5) continue;
        if (e.closest('header,nav,footer')) continue;
        const cs = getComputedStyle(e);
        if (e.tagName === 'IMG' || e.tagName === 'VIDEO' || (cs.backgroundImage && cs.backgroundImage.includes('url('))) { best = e; area = a; }
      }
      const e = q(c.selector) || best;
      if (!e) return 'no big picture in the first screen to swap';
      if (e.tagName === 'IMG') { e.removeAttribute('srcset'); e.removeAttribute('sizes'); e.src = c.data; e.style.objectFit = 'cover';
        match(e, 'img', ['objectPosition', 'transform', 'transformOrigin']); }
      else if (e.tagName === 'VIDEO') {
        const img = document.createElement('img'); img.src = c.data; img.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;';
        e.pause(); e.style.visibility = 'hidden'; e.parentElement.insertBefore(img, e);
      } else { e.style.backgroundImage = 'url(' + c.data + ')'; e.style.backgroundSize = 'cover'; e.style.backgroundPosition = 'center'; }
      return 'picture swapped for ' + (c.file || 'the file');
    }
    case 'sections': {
      // his pattern (2026-10-06): "Background should be in this pattern. A B A C A B A. Hero, Services, About, Our process, Portfolio,
      // Secondary Services, FAQ, and then secondary CTA." Three grounds; the sections take them in that order, top to bottom.
      const sel = c.selector || 'main section, body > section, .page-section, section.region, [data-section-id], main > div > section, .elementor-section, .elementor-top-section';
      let secs = qa(sel).filter(e => { const r = rect(e); return r.height >= 160 && r.width >= vw * 0.85 && !e.closest('header,footer,nav'); });
      // the page's bands are the biggest set of matches that share one parent (Squarespace wraps every section in one
      // region, so "outermost only" would find one); failing that, the outermost ones
      const byParent = new Map();
      for (const e of secs) { const k = e.parentElement; byParent.set(k, (byParent.get(k) || []).concat([e])); }
      const best = [...byParent.values()].sort((a, b) => b.length - a.length)[0] || [];
      secs = best.length >= 2 ? best : secs.filter(e => !secs.some(o => o !== e && o.contains(e)));
      secs.sort((a, b) => rect(a).top - rect(b).top);
      const pattern = (c.pattern || 'ABACABA').toUpperCase(), colors = c.colors || {}, text = c.text || {}, used = [];
      const n = Math.min(secs.length, c.limit || pattern.length);
      for (let i = 0; i < n; i++) {
        const e = secs[i], k = pattern[i % pattern.length];
        if (colors[k]) {
          e.style.setProperty('background-color', colors[k], 'important');
          if (c.photos === false) e.style.setProperty('background-image', 'none', 'important');   // a section's photo stays unless told otherwise
        }
        if (text[k]) for (const t of e.querySelectorAll('h1,h2,h3,h4,h5,p,li,span,div,em,strong'))
          if (t.children.length === 0 && !t.closest('a,button,[data-mb-cta],input,select,textarea')) t.style.setProperty('color', text[k], 'important');
        used.push(k);
      }
      return n ? 'sections ' + used.join(' ') + ' on the first ' + n + ' of ' + secs.length : 'no sections found; give a selector';
    }
    case 'font': {
      // a Google font on the headline (his "make the font style a serif style font"), waited for so the shot shows it
      if (!target) return 'no headline for the font';
      const fam = c.family || 'Newsreader', wt = c.weight || 300;
      const link = document.createElement('link'); link.rel = 'stylesheet';
      // Newsreader is loaded with its optical-size axis, the way the render loads it, so the live headline sets at the same width
      const axes = c.axes || (fam === 'Newsreader' ? 'opsz,wght@6..72,' + wt : 'wght@' + wt);
      link.href = 'https://fonts.googleapis.com/css2?family=' + fam.replace(/ /g, '+') + ':' + axes + '&display=block';
      document.head.appendChild(link);
      return new Promise(res => {
        let ran = false;   // the load event and the 5 s fallback both call this; only the first may apply, or later steps get undone
        const done = () => { if (ran) return; ran = true; target.style.fontFamily = '"' + fam + '", Georgia, serif'; target.style.fontWeight = String(wt); target.style.letterSpacing = '-0.01em';
          match(target, 'h1', ['fontWeight', 'letterSpacing']);
          document.fonts.load(wt + ' 40px "' + fam + '"').then(() => res('font: ' + fam + ' ' + wt), () => res('font: ' + fam + ' (not loaded)')); };
        link.onload = done; link.onerror = () => res('font: could not load ' + fam); setTimeout(done, 5000);
      });
    }
    case 'header': {
      // the rebuilt page's own header, laid over theirs the second he names the header (Jonathan, 2026-10-07: at the swap
      // "it turned the header section white"): their header goes, the render's header (logo, menu, phone, button) takes
      // its place at the render's height, so nothing about the header changes at the swap
      if (!c.data) return 'no render header to lay in (the plan needs its render)';
      // their header, and a phone or promo strip above it (Hatch's Divi #top-header, 2026-10-07): anything pinned or
      // banner-like across the top that does not hold the headline
      const named = qa(c.selector || 'header, [role=banner], #header, .header, .site-header, #website-header, #masthead, .elementor-location-header, #top-header, .top-bar, .topbar, #topbar, .announcement-bar, .header-announcement-bar-wrapper');
      const pinned = qa('body *').filter(e => { const p = getComputedStyle(e).position; return p === 'fixed' || p === 'sticky'; });
      // a header can hold what the hero read took for the headline (Holm's "Residential" menu button, 2026-10-07): the
      // headline that protects a box is one below the header band, and a box that holds it is a hero, not a header
      const heads = [q('[data-mb-head]'), ...qa('h1')].filter(Boolean);
      const h1 = heads.find(e => rect(e).top > 60 && rect(e).height > 0) || null;
      const tops = [...new Set([...named, ...pinned])]
        .filter(e => { const r = rect(e); return r.top < 60 && r.width > vw * 0.6 && r.height > 0 && r.height < vh * (named.includes(e) ? 0.45 : 0.3) && !(h1 && e.contains(h1)) && !e.closest('[data-mb-header]'); });   // GSI's Wix header is 314 px
      // the empty box some sites put under a pinned header to hold its place (Holm's .header-desktop-empty-space)
      qa('body *').forEach(e => { const r = rect(e); if (r.top < 10 && r.height > 30 && r.height < vh * 0.3 && r.width > vw * 0.8 && !(e.innerText || '').trim() && !e.querySelector('img, video, iframe, svg, picture') && !getComputedStyle(e).backgroundImage.includes('url') && !e.closest('[data-mb-header]') && !(h1 && e.contains(h1))) tops.push(e); });
      // a thin full-width strip just under it (Liberty Bell's showroom line, 2026-10-07) is part of their header too.
      // Measured before anything is hidden; never in the headline's own section, so a hero eyebrow stays.
      const hb = Math.max(0, ...tops.map(e => rect(e).bottom));
      const h1Top = h1 ? rect(h1).top : vh;
      const h1Sec = h1 ? (h1.closest('section, [class*=hero], [class*=banner], [id*=hero]') || h1.parentElement) : null;
      const strips = hb ? qa('body *').filter(e => {
        const r = rect(e);
        return r.top >= -4 && r.top <= hb + 24 && r.bottom < h1Top - 30 && r.height > 12 && r.height < 64 && r.width > vw * 0.6   // IO's Wix menu row is 980 of 1440
          && !(h1Sec && (h1Sec.contains(e) || e.contains(h1Sec))) && !e.closest('[data-mb-header]') && !tops.some(t => t.contains(e));
      }) : [];
      const outer = strips.filter(e => !strips.some(o => o !== e && o.contains(e)));
      // a box that holds a tagged piece the plan reuses later stays in place but unseen; the rest go
      const reused = e => (c.reuse || []).some(s => { try { return e.querySelector(s) || e.matches(s); } catch (x) { return false; } })
        || (c.reuse_head && e.querySelector('[data-mb-head]')) || (c.reuse_cta && e.querySelector('[data-mb-cta]'));
      tops.forEach(e => {
        if (reused(e)) { e.setAttribute('data-mb-hid', '1'); e.style.setProperty('visibility', 'hidden', 'important'); }
        else { e.style.setProperty('display', 'none', 'important'); e.setAttribute('data-mb-gone', '1'); }
      });
      if (!document.querySelector('style[data-mb-hidrule]')) {
        const st = document.createElement('style'); st.setAttribute('data-mb-hidrule', '1');
        st.textContent = '[data-mb-hid] [data-mb-show], [data-mb-hid] [data-mb-show] *, [data-mb-hid] [data-mb-eyebrow], [data-mb-hid] [data-mb-eyebrow] * {visibility:visible !important}';
        document.head.appendChild(st);
      }
      outer.forEach(e => { e.style.setProperty('display', 'none', 'important'); e.setAttribute('data-mb-gone', '1'); tops.push(e); });
      let ov = document.querySelector('[data-mb-header]');
      if (!ov) { ov = document.createElement('img'); ov.setAttribute('data-mb-header', '1'); document.body.appendChild(ov); }
      ov.src = c.data;
      Object.assign(ov.style, {position: 'fixed', top: '0', left: '0', width: '100%', height: c.h + 'px', zIndex: '2147483646', display: 'block'});
      document.body.style.setProperty('padding-top', c.h + 'px', 'important');
      // an empty band left where their tall header sat (IO's Wix grid keeps the row): the page moves up to meet the header
      let gapNote = '';
      // Scanned down from the header: the first row where anything is painted (a picture, words, a background picture, or
      // a ground of another color) is where their page starts.
      const painted = (e) => {
        if (!e || e === document.documentElement || e === document.body) return false;
        if (['IMG', 'VIDEO', 'CANVAS', 'SVG', 'PICTURE', 'IFRAME'].includes(e.tagName.toUpperCase())) return 'thing';
        if ([...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return 'words';
        return false;
      };
      const groundAt = (x, y) => {   // the color and picture under a point, from the topmost box that paints one
        for (const e of document.elementsFromPoint(x, y)) {
          if (e.closest('[data-mb-header]')) continue;
          const cs = getComputedStyle(e);
          if (cs.backgroundImage && cs.backgroundImage.includes('url(')) return 'picture';
          const p = painted(e); if (p) return p;
          if (cs.backgroundColor && cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.backgroundColor !== 'transparent') return cs.backgroundColor;
        }
        return getComputedStyle(document.body).backgroundColor;
      };
      const xs = [0.08, 0.3, 0.5, 0.7, 0.92].map(f => Math.round(vw * f));
      const band = groundAt(xs[2], c.h + 2);
      let gap = 0;
      if (!['picture', 'thing', 'words'].includes(band)) {
        for (let y = c.h + 2; y < c.h + vh * 0.4; y += 3) {
          const seen = xs.map(x => groundAt(x, y));
          if (seen.some(g => g !== band)) { if (!seen.includes('words')) gap = y - c.h - 2; break; }   // words first: their own white hero, kept
        }
      }
      if (gap > 8) { document.body.style.setProperty('margin-top', -gap + 'px', 'important'); gapNote = ', an empty band of ' + gap + ' px closed'; }
      return 'header: the rebuilt page\'s header (' + tops.length + ' of theirs hidden' + gapNote + ')';
    }
    case 'hide': { const es = qa(c.selector); es.forEach(e => e.style.display = 'none'); return es.length + ' hidden'; }
    case 'text': { const e = q(c.selector); if (!e) return 'selector matched nothing'; setText(e, c.text); return 'text: ' + c.text; }
    case 'css': {
      const es = c.selector ? qa(c.selector) : (target ? [target] : []);
      // a part of their header the 'header' step put away stays away: a later style on it would bring it back (VME)
      const live = es.filter(e => !e.closest('[data-mb-gone]'));
      live.forEach(e => e.style.cssText += ';' + c.style);
      return live.length + ' styled' + (live.length < es.length ? ' (' + (es.length - live.length) + ' under the new header, left alone)' : '');
    }
    case 'click': {
      // their own control pressed, as he did on the call: a carousel's next arrow when he talks about the next photo over
      // (VME, 2026-10-07: "it didn't follow to the next photo over")
      const e = q(c.selector); if (!e) return 'selector matched nothing';
      for (let i = 0; i < (c.times || 1); i++) e.click();
      return 'clicked ' + (c.times || 1) + 'x: ' + c.selector;
    }
    case 'note': return 'no change on screen';
  }
  return 'unknown kind ' + c.kind;
}
"""


HIDE_OVERLAYS_JS = r"""
() => {
  // a promotional popup, a chat bubble, or a cookie bar that opened while the page was scrolled through: hidden for the
  // full-page shot. Fixed boxes that cover a quarter of the screen or more, or sit at the bottom, except a top header.
  const vw = innerWidth, vh = innerHeight, out = [];
  for (const e of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(e);
    if (cs.position !== 'fixed' || cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05) continue;
    const r = e.getBoundingClientRect(); if (r.width < 2 || r.height < 2) continue;
    const header = r.top < 10 && r.height < vh * 0.25;
    const big = r.width * r.height >= vw * vh * 0.25;
    const bottomBar = r.bottom > vh - 10 && r.height < vh * 0.4 && r.width > vw * 0.5;
    if (!header && (big || bottomBar)) { e.style.setProperty('display', 'none', 'important'); out.push((e.className || e.tagName).toString().slice(0, 40)); }
  }
  return out.join(', ');
}
"""


def rel(p):
    """A path as the repo writes it, or as given when it lies outside the repo (a scratch plan)."""
    try:
        return Path(p).relative_to(ROOT).as_posix()
    except ValueError:
        return Path(p).as_posix()


def load_plan(path):
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    for k in ("out", "url", "folder", "changes"):
        if k not in plan:
            sys.exit(f"The plan needs '{k}'.")
    plan["changes"] = sorted(plan["changes"], key=lambda c: float(c["at"]))
    return plan


def states_dir(plan):
    d = scn.folder(plan.get("states_dir") or (Path(plan["out"]).parent / "states"))
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------- states

async def _states(plan, out_dir):
    from playwright.async_api import async_playwright
    from hero_check import COOKIE_JS, HERO_JS  # the same read the hero check does, so the headline and the button are tagged

    block = [b.replace("*.", "") for b in BLOCK]
    rows = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(viewport={"width": VIEW_W, "height": VIEW_H}, user_agent=UA, locale="en-US", ignore_https_errors=True)

        async def route(r):
            host = urlparse(r.request.url).netloc.lower()
            if any(host == b or host.endswith("." + b) for b in block):
                await r.abort()
            else:
                await r.continue_()
        await context.route("**/*", route)
        page = await context.new_page()
        await page.goto(plan["url"], timeout=30000, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        if await page.evaluate(COOKIE_JS):
            try:
                await page.locator('[data-mb-cookie="1"]').first.click(timeout=1500)
                await page.wait_for_timeout(500)
            except Exception:  # noqa: BLE001
                pass
        # the page's own motion rests: a headline sliding in or a slider changing words would make two states differ for no reason
        await page.add_style_tag(content="*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}")
        await page.evaluate(HIDE_OVERLAYS_JS)   # a cookie bar's OK button or a chat pop-up is never read as the page's main button
        info = await page.evaluate(HERO_JS, VIEW_H)
        head = (info.get("headline") or {}).get("text")
        if not head:
            print("No headline found in the first screen; 'headline', 'center', 'eyebrow' and 'copy' changes will need a selector.")

        async def shot(name, view=0):
            await page.bring_to_front()              # with the render's tab open, a background tab's screenshot can stall (Sierra, 2026-10-06)
            await page.evaluate(HIDE_OVERLAYS_JS)   # a cookie bar or a timed popup never sits over a step
            await page.evaluate(f"window.scrollTo(0, {int(view)})")
            await page.wait_for_timeout(350)
            await page.screenshot(path=str(out_dir / name), type="jpeg", quality=88, clip={"x": 0, "y": 0, "width": VIEW_W, "height": VIEW_H})
            await page.evaluate("window.scrollTo(0, 0)")

        refbox = {}

        async def apply(c, what):
            c = dict(c)
            if refbox.get("ref") and plan.get("match", True):
                c["ref"] = refbox["ref"]
            if c["kind"] == "header":
                c["data"], c["h"] = refbox.get("header"), refbox.get("header_h", 80)
                # what later steps take from inside their header (Holm built its hero from header items; VME did not)
                later = [x for x in plan["changes"] if float(x["at"]) >= float(c["at"]) and x["kind"] not in ("header", "section", "form")]
                c["reuse"] = [x["selector"] for x in later if x.get("selector") and x["kind"] in ("headline", "eyebrow", "cta", "copy", "text", "image", "font", "center", "bigger")]
                c["reuse_head"] = any(not x.get("selector") and x["kind"] in ("headline", "eyebrow", "copy", "font", "css", "bigger", "center") for x in later)
                c["reuse_cta"] = any(not x.get("selector") and x["kind"] == "cta" for x in later)
            if c["kind"] == "image":
                f = scn.folder(c["file"])
                if not f.exists():
                    sys.exit(f"The picture for {what} is not there: {f}")
                mime = "image/png" if f.suffix.lower() == ".png" else "image/jpeg"
                c["data"] = f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode()
            try:
                note = await page.evaluate(EDIT_JS, c)
            except Exception as e:  # noqa: BLE001
                note = f"failed: {type(e).__name__}: {str(e)[:120]}"
            if c["kind"] == "center":
                refbox["centered"] = True
            ref = refbox.get("ref") or {}
            if refbox.get("centered") and (ref.get("h1") or {}).get("_top") is not None and plan.get("match", True):
                await page.evaluate(ALIGN_JS, ref["h1"]["_top"])
            await page.wait_for_timeout(1200 if c["kind"] == "click" else 250)   # a slide's picture loads after the click
            return note

        # the finished render (plan "render": its index.html), for the steps past what their live page can show: the
        # sections below the first screen and the form, shown as he names each one (2026-10-06, the third PHA audit)
        rpage = None
        render_url = scn.folder(plan["render"]).resolve().as_uri() if plan.get("render") else None

        async def render_shot(name, c):
            nonlocal rpage
            if not render_url:
                sys.exit("A 'section' or 'form' step needs the plan's 'render' (the rebuilt page's index.html).")
            if rpage is None:
                rpage = await context.new_page()
            if c["kind"] == "form":
                step = c.get("step", 1)
                if str(step) == "sent":      # the thank-you screen with the calendar box, for "it goes to your calendar"
                    await rpage.goto(f"{render_url}?sent=1", wait_until="load")
                    await rpage.wait_for_timeout(700)
                    await rpage.evaluate("() => { const b = document.getElementById('pick'); if (b) b.click(); }")
                    note = "the form, sent, with the calendar box"
                else:
                    await rpage.goto(f"{render_url}?step={int(step)}", wait_until="load")
                    note = f"the form, step {int(step)}"
                await rpage.wait_for_timeout(900)
                y = 0
            else:
                if not rpage.url.startswith(render_url) or "?" in rpage.url:
                    await rpage.goto(render_url, wait_until="load")
                    await rpage.wait_for_timeout(1200)
                band = c.get("band", "hero")
                y = await rpage.evaluate("(b) => { const e = document.querySelector('[data-band=\"' + b + '\"]'); if (!e) return -1;"
                                         " return Math.max(0, e.getBoundingClientRect().top + scrollY - 80); }", band)
                if y < 0:
                    return f"no '{band}' section on the render"
                y += int(c.get("offset", 0))
                note = f"the rebuilt page: {band}"
            await rpage.evaluate(f"window.scrollTo(0, {int(y)})")
            await rpage.wait_for_timeout(400)
            await rpage.bring_to_front()
            await rpage.screenshot(path=str(out_dir / name), type="jpeg", quality=88, clip={"x": 0, "y": 0, "width": VIEW_W, "height": VIEW_H})
            return note

        if render_url:
            # the render's own sizes, read once, so each live change lands at the size the finished page shows
            rpage = await context.new_page()
            await rpage.goto(render_url, wait_until="load")
            await rpage.wait_for_timeout(1200)
            refbox["ref"] = await rpage.evaluate(REF_JS)
            # the render's header as a picture, for the 'header' step
            hh = await rpage.evaluate("() => { const t = document.querySelector('.top'); return t ? Math.round(t.getBoundingClientRect().height) : 0; }")
            if hh:
                await rpage.bring_to_front()
                png = await rpage.screenshot(type="png", clip={"x": 0, "y": 0, "width": VIEW_W, "height": hh})
                refbox["header"], refbox["header_h"] = "data:image/png;base64," + base64.b64encode(png).decode(), hh

        await shot("00-before.jpg")
        rows.append({"i": 0, "kind": "before", "at": None, "file": "00-before.jpg", "note": f"the page as it is; headline: {head!r}"})
        for i, c in enumerate(plan["changes"], 1):
            name = f"{i:02d}-{c['kind']}{'-' + c['band'] if c.get('band') else ''}.jpg"
            if c["kind"] in ("section", "form"):
                note = await render_shot(name, c)
                rows.append({"i": i, "kind": c["kind"], "at": float(c["at"]), "file": name, "note": note})
                print(f"  {name} | at {scn.mmss(float(c['at']))} | {note}")
                continue
            note = await apply(c, f"change {i}")
            await shot(name, c.get("view", 0))
            rows.append({"i": i, "kind": c["kind"], "at": float(c["at"]), "file": name, "note": note})
            print(f"  {name} | at {scn.mmss(float(c['at']))} | {note}")
        # the finish: his standing rules for the rebuilt page that the Loom does not name (the background pattern). They are
        # not steps in the video; they show in the finished page's scroll.
        finish = []
        for j, c in enumerate(plan.get("finish", []), 1):
            note = await apply(c, f"finish {j}")
            finish.append({"kind": c["kind"], "note": note})
            print(f"  finish {j}: {c['kind']} | {note}")
        # the whole finished page: scroll through it first so every section reveals and every lazy picture loads
        y, steps = 0, 0
        while steps < 80:
            height = await page.evaluate("document.documentElement.scrollHeight")
            if y >= height:
                break
            await page.evaluate(f"window.scrollTo(0, {y})")
            await page.wait_for_timeout(180)
            y += 600
            steps += 1
        # what the scroll revealed stays shown; a popup the site keeps hidden is not forced open (visibility is left alone)
        await page.add_style_tag(content=".preFade.fadeIn,.preSlide.slideIn,.preScale.scaleIn,[data-aos],.wow,.elementor-invisible{opacity:1!important;transform:none!important}")
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(700)
        hidden = await page.evaluate(HIDE_OVERLAYS_JS)
        if hidden:
            print(f"  hid before the full-page shot: {hidden}")
        await page.screenshot(path=str(out_dir / "final-full.jpg"), type="jpeg", quality=85, full_page=True)
        await browser.close()
    return rows, finish, {"headline": head, "ctas": [x.get("label") for x in (info.get("ctas") or [])][:3], "centered": info.get("centered")}


def cmd_states(a):
    plan = load_plan(a.plan)
    out_dir = states_dir(plan)
    rows, finish, read = asyncio.run(_states(plan, out_dir))
    (out_dir / "states.json").write_text(json.dumps({"url": plan["url"], "made": date.today().isoformat(), "view": [VIEW_W, VIEW_H], "read": read,
                                                     "states": rows, "finish": finish, "final_full": "final-full.jpg"}, indent=1), encoding="utf-8")
    print(f"{rel(out_dir)} | {len(rows)} states + final-full.jpg | headline read: {read['headline']!r} | buttons: {read['ctas']}")


# ---------------------------------------------------------------- the cut

def source_to_out(ranges):
    """A map from a second in the Loom to a second on the cut's own timeline (a second inside a cut lands where the next kept stretch starts)."""
    def f(src):
        acc = 0.0
        for s, e in ranges:
            if src < s:
                return acc
            if src < e:
                return acc + src - s
            acc += e - s
        return acc
    return f


def pieces_for(plan, ranges, total):
    """The picture over the cut's timeline: [(kind, index, start, end)] with kind 'state' (the state's index) or 'scroll'
    (the index of the window in `windows`: [(start, end, screens)], screens being how many first screens the scroll covers,
    0 for the whole page)."""
    to_out = source_to_out(ranges)
    marks = [(to_out(float(c["at"])), i + 1) for i, c in enumerate(plan["changes"])]
    windows = []
    if plan.get("variation", "A").upper() == "B":
        for key in ("trailer", "final"):
            w = plan.get(key) or {}
            if w.get("under"):
                windows.append((to_out(float(w["under"][0])), to_out(float(w["under"][1])), int(w.get("screens", 0))))
    bounds = sorted({0.0, total, *[m[0] for m in marks], *[b for w in windows for b in w[:2]]})
    pieces = []
    for b0, b1 in zip(bounds, bounds[1:]):
        if b1 - b0 < 0.04:
            continue
        win = next((k for k, (w0, w1, _) in enumerate(windows) if w0 <= b0 < w1), None)
        if win is not None:
            pic = ("scroll", win)
        else:
            pic = ("state", max([i for t, i in marks if t <= b0 + 1e-6], default=0))
        if pieces and pieces[-1][0] == pic[0] and pieces[-1][1] == pic[1]:
            pieces[-1] = (pic[0], pic[1], pieces[-1][2], b1)
        else:
            pieces.append((pic[0], pic[1], b0, b1))
    return pieces, windows


def cmd_cut(a):
    plan = load_plan(a.plan)
    out = scn.folder(plan["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    sdir = states_dir(plan)
    sj = sdir / "states.json"
    if not sj.exists():
        sys.exit(f"No states yet. Run: python scripts/loom_ba.py states {a.plan}")
    sdata = json.loads(sj.read_text(encoding="utf-8"))
    states, finish = sdata["states"], sdata.get("finish") or []
    if len(states) != len(plan["changes"]) + 1:
        sys.exit(f"states.json has {len(states)} states and the plan {len(plan['changes'])} changes. Run states again.")
    words = scn.transcript(plan["folder"])["words"]
    src = scn.folder(plan["folder"]) / "source.mp4"
    start, end = float(plan.get("start_at", 0.0)), float(plan.get("end_at", words[-1][1]))
    cuts = ([(0.0, start, "before he starts")] if start > 0 else []) + [(float(c[0]), float(c[1]), c[2]) for c in plan.get("cuts", [])] + [(end, 1e9, "after the end")]
    ranges = scn.keep_ranges(words, cuts, [(float(k[0]), float(k[1])) for k in plan.get("keep_whole", [])], float(plan.get("pause", 0.5)))
    ranges = [[s, min(e, end)] for s, e in ranges if s < end]
    total = sum(e - s for s, e in ranges)
    if total > MAX_S:
        sys.exit(f"The cut would run {scn.mmss(total)}; his limit is five minutes. Cut more.")
    pieces, windows = pieces_for(plan, ranges, total)
    said = scn.remap([(words, ranges)], plan.get("fixes"))
    pal = caps_style.load_palette()
    blue, white = caps_style.ass_color(pal["you"]), caps_style.ass_color(pal["youWord"])
    fit = f"scale={PAGE_W}:{PAGE_H}:flags=lanczos,pad=1920:1080:(ow-iw)/2:0:color={GROUND}"
    norm = "fps=30,format=yuv420p,setsar=1,settb=AVTB"
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "fonts").mkdir()
        shutil.copy(scn.FONT, work / "fonts" / scn.FONT.name)
        inputs, graph = [], []
        n = len(pieces)
        for k, (kind, idx, b0, b1) in enumerate(pieces):
            d = (b1 - b0) + (FADE if k < n - 1 else 0.0)      # every picture but the last carries the fade into the next
            if kind == "state":
                inputs += ["-loop", "1", "-framerate", "30", "-t", f"{d:.3f}", "-i", str(sdir / states[idx]["file"])]
                graph.append(f"[{k}:v]{fit},{norm}[p{k}]")
            else:
                D = max(0.5, b1 - b0)
                screens = windows[idx][2]
                reach = f"min(ih-oh\\,{screens * PAGE_H})" if screens else "(ih-oh)"   # how far down the scroll goes
                inputs += ["-loop", "1", "-framerate", "30", "-t", f"{d:.3f}", "-i", str(sdir / "final-full.jpg")]
                graph.append(f"[{k}:v]scale={PAGE_W}:-2:flags=lanczos,pad={PAGE_W}:'max(ih\\,{PAGE_H})':0:0:color={GROUND},"
                             f"crop={PAGE_W}:{PAGE_H}:0:'{reach}*(1-cos(PI*min(t\\,{D:.3f})/{D:.3f}))/2',"
                             f"pad=1920:1080:(ow-iw)/2:0:color={GROUND},{norm}[p{k}]")
        if n == 1:
            graph.append("[p0]copy[v]")
        else:
            prev = "p0"
            for k in range(1, n):
                offset = pieces[k][2]                             # the fade starts the second he names the change
                lab = "v" if k == n - 1 else f"x{k}"
                graph.append(f"[{prev}][p{k}]xfade=transition=fade:duration={FADE}:offset={offset:.3f}[{lab}]")
                prev = lab
        (work / "picture.txt").write_text(";".join(graph), encoding="utf-8")
        scn.ff(["-y", "-loglevel", "error", *inputs, "-filter_complex_script", "picture.txt", "-map", "[v]", "-t", f"{total:.3f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30", "picture.mp4"], cwd=work)
        (work / "captions.ass").write_text(scn.ass(said, blue, white, cap_y=CAP_Y, res=(1920, 1080), size=CAP_SIZE, max_chars=22), encoding="utf-8")
        sel = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in ranges)
        face = plan.get("face")
        if face:
            # his face bubble from the Loom (Jonathan, 2026-10-06: "This should include my face with the same cuts as well"):
            # the same kept stretches as his voice, so lips and words stay together; made constant 30 fps first, since a
            # Loom is variable frame rate; cut round, set bottom left, under the captions
            size = int(face.get("size", 260))
            fx, fy = face.get("pos", [48, 1080 - size - 48])
            ring = int(face.get("ring", 4))
            pic = (f"[1:v]fps=30,select='{sel}',setpts=N/30/TB,crop={face['crop']},scale={size}:{size},format=rgba,"
                   f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lte(hypot(X-W/2,Y-H/2),W/2-1),255,0)'[f];"
                   f"color=c=white@0.95:s={size + 2 * ring}x{size + 2 * ring}:r=30,format=rgba,"
                   f"geq=r='255':g='255':b='255':a='if(lte(hypot(X-W/2,Y-H/2),W/2-1),235,0)'[ring];"
                   f"[0:v][ring]overlay={fx - ring}:{fy - ring}:shortest=1[p1];[p1][f]overlay={fx}:{fy}:eof_action=pass[p2];"
                   f"[p2]ass=captions.ass:fontsdir=fonts[v]")
        else:
            pic = "[0:v]ass=captions.ass:fontsdir=fonts[v]"
        (work / "final.txt").write_text(f"{pic};[1:a]aselect='{sel}',asetpts=N/SR/TB,aresample=48000,"
                                        f"aformat=channel_layouts=mono,{scn.LOUD}[a]", encoding="utf-8")
        scn.ff(["-y", "-loglevel", "error", "-i", "picture.mp4", "-i", str(src), "-filter_complex_script", "final.txt", "-map", "[v]", "-map", "[a]",
                "-t", f"{total:.3f}", *scn.ENC, "-crf", "20", "-b:a", "160k", "-movflags", "+faststart", str(out)], cwd=work)
    to_out = source_to_out(ranges)
    rows = "".join(f"| {scn.mmss(float(c['at']))} | {scn.mmss(to_out(float(c['at'])))} | {c['kind']} | {states[i + 1]['note']} |\n"
                   for i, c in enumerate(plan["changes"]))
    cut_rows = "".join(f"| {scn.mmss(s)} | {scn.mmss(min(e, words[-1][1]))} | {why} | {' '.join(w[2] for w in words if s <= w[0] < e)[:200] or '(silence)'} |\n"
                       for s, e, why in cuts)
    pic_rows = "".join(f"| {scn.mmss(b0)} | {scn.mmss(b1)} | {('the finished page, scrolling ' + (f'the first {windows[idx][2]} screens' if windows[idx][2] else 'top to bottom')) if kind == 'scroll' else states[idx]['file']} |\n"
                       for kind, idx, b0, b1 in pieces)
    out.with_suffix(".cuts.md").write_text(
        f"# {out.name}\n\nLoom B and A, variation {plan.get('variation', 'A')}. {scn.mmss(total)} of {scn.mmss(words[-1][1])}. The page on screen is the "
        "state that matches his words; each change fades in the second he names it. His voice, his words, Monarc Studio captions; no music, "
        + ("his face bubble on the same cuts as his voice" if plan.get("face") else "no face bubble") + ", no line he did not say. "
        "Fillers and long pauses are out.\n\n"
        + ("" if total <= GOOD_S else f"Over three minutes ({scn.mmss(total)}); three is the mark he set.\n\n")
        + f"## The changes\n\n| Said at (Loom) | Shows at (video) | Kind | What the page did |\n|---|---|---|---|\n{rows}\n"
        + (("## The finish (his standing rules, not named in the Loom; in the finished page only)\n\n" + "".join(f"- {f['kind']}: {f['note']}\n" for f in finish) + "\n") if finish else "")
        + f"## What is on screen\n\n| From | To | Picture |\n|---|---|---|\n{pic_rows}\n"
        f"## What was cut\n\n| From | To | Why | What he said |\n|---|---|---|---|\n{cut_rows}\n## The words\n\n" + " ".join(x[2] for x in said) + "\n",
        encoding="utf-8")
    flag = "" if total <= GOOD_S else f" | over three minutes"
    print(f"{rel(out)} | {scn.mmss(total)} | {len(plan['changes'])} changes | {len(pieces)} pictures | {len(said)} words{flag}")
    scn.check(out)


# ---------------------------------------------------------------- the record of what was sent

def cmd_record(a):
    PROJECT.mkdir(parents=True, exist_ok=True)
    data = json.loads(SENDS.read_text(encoding="utf-8")) if SENDS.exists() else {"_about": "One row per Loom B and A video emailed: the subject line and body "
                                                                                     "that carried it (keys from templates/loom-ba-email.md), then whether they "
                                                                                     "watched (Loom's view email, his to mark) and wrote back. The subject-line "
                                                                                     "test reads this file.", "sends": []}
    row = next((r for r in data["sends"] if r["loom"] == a.loom and r["company"] == a.company), None)
    if not row:
        row = {"date": date.today().isoformat(), "company": a.company, "loom": a.loom, "cut": a.cut, "subject": a.subject, "body": a.body, "watched": "", "replied": ""}
        data["sends"].append(row)
    for k in ("cut", "subject", "body", "watched", "replied"):
        v = getattr(a, k)
        if v:
            row[k] = v
    SENDS.write_text(json.dumps(data, indent=1), encoding="utf-8")
    by = {}
    for r in data["sends"]:
        b = by.setdefault(r["subject"], {"sent": 0, "watched": 0, "replied": 0})
        b["sent"] += 1
        b["watched"] += r.get("watched") == "yes"
        b["replied"] += r.get("replied") == "yes"
    print(f"{SENDS.relative_to(ROOT).as_posix()} | {len(data['sends'])} sends | " + "; ".join(f"{k}: {v['sent']} sent, {v['watched']} watched, {v['replied']} replied" for k, v in sorted(by.items())))


def cmd_find(a):
    """The second each phrase starts in a Loom's transcript ("phrase@120" finds the first match after 2:00). The beats in a
    director's script come from here, never by ear."""
    import re as _re
    words = scn.transcript(a.folder)["words"]
    norm = lambda s: _re.sub(r"[^a-z0-9']", "", s.lower())
    toks = [norm(w[2]) for w in words]
    for phrase in a.phrases:
        after = 0.0
        if "@" in phrase:
            phrase, at = phrase.rsplit("@", 1)
            after = float(at)
        p = [norm(x) for x in phrase.split()]
        hit = next((i for i in range(len(toks) - len(p) + 1) if words[i][0] >= after and toks[i:i + len(p)] == p), None)
        print(f"{phrase!r}: " + (f"{words[hit][0]:.2f}" if hit is not None else "not found"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    fd = sub.add_parser("find")
    fd.add_argument("folder")
    fd.add_argument("phrases", nargs="+")
    sub.add_parser("states").add_argument("plan")
    sub.add_parser("cut").add_argument("plan")
    sub.add_parser("check").add_argument("video")
    r = sub.add_parser("record")
    r.add_argument("--company", required=True)
    r.add_argument("--loom", required=True)
    r.add_argument("--cut", default="", help="A or B")
    r.add_argument("--subject", default="", help="S1, S2, S3 from templates/loom-ba-email.md")
    r.add_argument("--body", default="", help="B1 or B2")
    r.add_argument("--watched", default="", choices=["", "yes", "no"])
    r.add_argument("--replied", default="", choices=["", "yes", "no"])
    a = ap.parse_args()
    {"states": cmd_states, "cut": cmd_cut, "record": cmd_record, "find": cmd_find, "check": lambda x: scn.check(scn.folder(x.video))}[a.cmd](a)


if __name__ == "__main__":
    main()
