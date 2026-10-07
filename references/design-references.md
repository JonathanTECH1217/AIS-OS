# Design references

Sites Jonathan flags for what they get right visually. Each entry says what to copy and why, with measured values so a designer or the AIOS can reproduce the effect on monarcbuild.com without guessing. Add an entry when Jonathan sends a screenshot and says "add this." Keep the screenshot description; screenshots pasted in chat are not saved.

Use this when: briefing a designer (pair with `projects/monarcbuild-site/handoff/`), drafting any page or landing page, rendering hero images, or building an ad creative.

---

## 1. Purple Cherry Architecture & Interiors, profile page

- URL: https://purplecherry.com/profile/
- Added 2026-09-09 from a desktop screenshot (about 1830px wide). Jonathan's words: "This spacing and contrast is thought out well."
- What it is: a residential architecture firm's "Profile" page. Header, sub-nav, one watercolor sketch, one italic line, then the philosophy section. Same customer as Monarc's clients sell to, so the register is the target register.
- Stack: WordPress. Type served from Adobe Fonts (kit vti1vqk).

### Type

| Role | Face | How it's set |
|---|---|---|
| Logo "PURPLE CHERRY" | LTC Goudy Oldstyle Pro, regular | All caps, wide tracking (about 0.2em), deep purple |
| Logo line 2 "ARCHITECTURE & INTERIORS" | Freight Sans Pro | Small caps size, tracking wider still, gray |
| Nav and sub-nav | Freight Sans Pro | 14 to 15px caps, tracked, thin pipe separators, active item darker |
| Quote "When we're designing a house, we talk about romance." | LTC Goudy Oldstyle Pro, italic 400 | About 64px, two lines, centered, line height near 1.2, gray-brown not black |
| Section label "PHILOSOPHY" | Freight Sans Pro | About 13px caps, tracked, bracketed by short rules |
| Section subhead "ROMANCE, PASSION, & VISION" | Freight Sans Pro | About 15px caps, tracked |
| CTA "Schedule a Consultation" | Goudy Oldstyle (serif, title case) | White on purple |

Only two faces, two weights total (regular and italic). Hierarchy comes from size and letterspacing, never from bold.

### Color

| Use | Value |
|---|---|
| Brand purple: logo, CTA button | `#281b54` (variant `#332164`) |
| Body and quote text | `#5f5852` warm gray-brown, never pure black |
| Section ground | warm light gray, about `#e6e3df` (sampled from the screenshot, not from CSS) |
| Header ground | `#ffffff` |
| Top strip | thin dark slate line above the header |

One saturated color on the whole page, used exactly twice: the logo and the CTA. Everything else is two grays on a warm ground. That's why the CTA reads without shouting.

### Spacing (measured on the screenshot)

- Header about 120px tall, logo centered, nav split three left and three right.
- Sub-nav sits about 80px below the header.
- Sketch about 950px wide, centered, about 100px below the sub-nav. No frame, no box, no drop shadow. A hand drawing where most firms put a photo.
- Quote about 60px below the sketch.
- About 100px of air before the section label.
- Floating CTA pill bottom right, about 265x65px, full radius, about 40px from the edges. It's the only element not on the center axis.
- Nothing touches an edge. One idea per screen height.

### What to take for monarcbuild.com

1. Warm gray section ground with `#5f5852`-style off-black text for the proof section, so the numbers sit on something quieter than white.
2. One accent color, reserved for the logo and the "Apply now" button. Nothing else gets it.
3. A single italic serif line as a section opener. Monarc's equivalent already exists: "Being a home integrator is hard."
4. Tracked small-caps section labels with a short rule on each side. Treat the rules as graphic lines, not text (Jonathan's copy rule: no em dashes in prose).
5. Two typefaces, regular and italic only. Size and tracking do the hierarchy.
6. Floating CTA pill, bottom right, brand color, serif label.
7. 80 to 120px between blocks. When in doubt, add air.

Not to take: the watercolor sketch. Monarc's proof is real photos of real jobs (`projects/outreach/proof-pack/`). A drawing would undercut that.

### Note

The firm is a residential architecture practice with 30+ years of high end work. Architects are a referral channel Jonathan already knows (AIA presentations). If the site's address puts them in the Annapolis area, they're a warm-intro candidate; check the contact page before using that angle.

---

## 2. Arctic Electricians, the Services menu

- URL: https://arcticelectricians.com/ (the row opens under "Services" in the header)
- Added 2026-10-01 from a desktop screenshot (about 1860px wide), saved as `design-references/2-arctic-electricians-services-menu.png`. Jonathan's words: "add this as an idea for the service dropdown. I like this visual."
- What it is: an electrician and smart home integrator in Stateline, Nevada (South Lake Tahoe): generators, ice melt, lighting, security, theaters, Savant, Control4, Crestron, Josh.ai. Their header's Services item opens a row of photo cards, one per service.
- Status: an idea for monarcbuild.com's Services dropdown, not built.

### The menu, as the screenshot shows it

- Header in one row on a light ground: "We Work With" (a dropdown), "Services" (open, a light grey pill behind it and a chevron), About, Careers, "Cinergy Certified"; the logo centered; then the phone number, "Recent Projects", and an outlined "Contact Us >" button at the right.
- Under it, eight cards in one row across the full width (about 30px side margins): Smart Home, Build Consultation, Lighting, Generators, Ice Melt, Security, Home Theater & AV, Design Consultation.
- Each card: a real job photo about 208 x 138px (about 3:2), corners rounded about 8px, no border, no shadow; the service name under it, about 20px, medium weight, dark grey, left aligned, about 12px below the photo. About 20px between cards.
- The photos are their own installs, all bright and warm: a remote in a hand, plans on a table, a theater with a starlit ceiling, a Generac unit beside a house, a roof edge with heat cable, a tech at a keypad, a lounge with a fireplace TV, a designer at a table. They read as one set.

### What to take for monarcbuild.com

1. A Services mega menu: one card per service page, the picture on top and the service name under it, opening under "Services" on the site pages (`/`, `/about/`, `/book/`). The six service pages keep no menu (Style Guide 6.1).
2. The pictures already exist: each service's render tile, `assets/generated/<slug>/tile.jpg` (600 x 450, 4:3, `scripts/ads_images.py thumbs`), the same tiles the homepage's six service cards use. They are renders, so their alt text names them as illustrations (Style Guide Media 1).
3. The panel runs the full width under the header, wider than the 960px column (it is navigation, not page content): six cards about 200px wide with 20px gaps fit one row at 1440. On phones, a list: the picture left, the name right, like the homepage's compact rows.
4. The name only under each card, in the page's label style; no description line. One glance per card.
5. Opens on hover and on click or tap; Escape closes; every card reachable by keyboard.

### Not to take

- The two consultation cards: Monarc has one booking, the fifteen minute call, and it stays the button, not a menu card.
- The outlined "Contact Us" button: Monarc's button is the theme's solid pill.

### Note

Arctic Electricians is also Monarc's buyer: an electrician that installs Savant, Control4, and Crestron in high end Tahoe homes. They are in the Prospects call list as MB-03798 (electrician list, labeled AV integrator on 2026-10-01 from the 2026-09-13 site read), not yet called.

---

## Entry template

```
## N. Site name, page

- URL:
- Added YYYY-MM-DD from (screenshot / live). Jonathan's words: ""
- What it is:
- Stack:

### Type
### Color
### Spacing
### What to take for monarcbuild.com
### Not to take
```
