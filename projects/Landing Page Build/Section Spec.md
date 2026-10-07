# Section spec: monarcbuild.com homepage

Second file `/landing-page` reads, after `Style Guide.md`. Every block names its copy source so the build pulls facts from canonical pages, never from memory. Jonathan approves copy on the render.

## Homepage (Jonathan, 2026-09-27, round 3): a Google product site in the Google type, the butterfly's colors. Live 2026-09-27

"It should use the google type and copy but not look like a google search results page." Interview: `brainstorms/2026-09-26-homepage-google-rebuild.md` (Q1 to Q31; round 3 is Q29 to Q31). Theme `monarc` (`themes/monarc.json`, Style Guide section 8: white, Roboto, the butterfly's four hues). Rounds 1 (a Google results page) and 2 (the same layout in a warm theme) were retired unshipped. Built by `python scripts/build_service_page.py home` from `build/home.body.html`, `build/home.css`, `build/home.js`, and the tested tracking head, popup, and booking script; writes `public_html/index.html`. Indexed (no `noindex`), canonical `https://monarcbuild.com/`, the link preview `assets/og/home.jpg`, organization data (no ratings). No page-view conversion: the shared conversion fires on `?sent=1` only.

| # | Block | Anchor | What is in it |
|---|---|---|---|
| | Header | | The lockup (links home); Services, Results, Questions (anchors) and About (`/about/`), hidden on phones; "Book an appointment" |
| 1 | Hero | `hero` | Centered: the eyebrow "For the trades"; h1 "Marketing for contractors. Built by installers."; the sub (24 words); the search bar typing "marketing for contractors" once (Q31); "Book an appointment" (`open-hero`); the sent state under it |
| 1b | National citations | `citations` | Jonathan, 2026-09-27: "Add the rolling citation banner with big brand names to the section right below the fold". The logo banner template (below), full color, the marks about half again as tall as the template's (40 to 58px on desktop), the label "We list your business on" (2026-09-28; was "National citations we work with"), filled by the build script like the service pages'. The banner never stops under the pointer and runs 45 seconds a loop (the template, below) |
| 2 | Services | `services` | h2 "Six services. One fifteen minute call."; six cards in the build order, each linking to its page: the page's render (`assets/generated/<slug>/tile.jpg`, `scripts/ads_images.py thumbs`), the service name with a hue dot, the page's h1, the page's sub. Compact rows on phones. A new service page adds a card here |
| 3 | Results | `proof` | h2 "Three jobs our marketing brought in."; the Georgian, the waterfront, the penthouse as photo cards (`assets/projects/cards/`), a title and one line each. No dollar figures on the cards (Jonathan, 2026-09-27: "Take the number figures out of the jobs"); the Georgian card shows the interior rough-in, cropped high (center 20%) so the PHA shirt stays out. Source: `context/about-business.md` Proof jobs |
| 4 | Fit | `fit` | h2 "Built for a specific kind of shop."; "Who it is for" and "Who it is not for" (Q29, his words), teal and coral on the headings and marks only |
| 5 | About | `about` | The butterfly; h2 "Sold and installed before we marketed."; the credentials as chips (Lutron certified, AIA presentations, CEDIA workshops); the trades. No years (Copy 3) |
| 6 | Questions | `questions` | "Questions contractors ask": cost, the call, which trades, what if it does not work |
| 7 | Closing ask | `book` | "Your next high ticket job is searching now.", "Book an appointment" (`open-final`), "Fifteen minutes. Bring nothing." |
| | Footer | | "Monarc Build, LLC · Annapolis, Maryland"; About, Privacy, the email. The floating pill and the popup in the theme |

Section labels are plain tracked caps: the four hue dots before every label on the homepage and `/about/` came off (Jonathan, 2026-09-27: "remove this icon from these sections"). The single hue dot beside each service card's name stays. Live the same day, with the Google-colored dots off `/google-ads/` (`pages/google-ads.md`).

The seven-block homepage below (2026-09-13 to 2026-09-26) is history; its draft is archived at `archives/homepage-draft-2026-09-13/`.

## About page /about/ (Jonathan, 2026-09-27): rebuilt in the homepage's theme. Live 2026-09-27

"Rebuild the about page with a more aligned offering and new style as used in the home page." Interview: `brainstorms/2026-09-27-about-page-rebuild.md` (Q1 to Q6). Theme `monarc`. Built by `python scripts/build_service_page.py about` from `build/about.body.html` and `build/about.css` (with `home.css` and `service-page.css`); page type `site`, indexed, canonical `https://monarcbuild.com/about/`, link preview `assets/og/about.jpg`, the booking popup. His first person in the story, his name only, no years (Copy 3), no prices, never PHA.

| # | Block | Anchor | What is in it |
|---|---|---|---|
| | Header | | The homepage's: the lockup, Services (this page), Results and Questions (the homepage), About (this page), the button |
| 1 | Hero | `hero` | The eyebrow "About"; h1 "I sold these systems before I marketed them."; the story in one sentence; "Book an appointment"; the butterfly large on the right (above the text on phones); the sent state under it |
| 2 | The story | `story` | "Why Monarc Build exists.": the shops did exceptional work on luck-based pipelines; their buyers were already searching; Monarc Build is that work, run by someone who pulled the wire and sold the job |
| 3 | Credentials | `credentials` | Lutron certified; AIA presentations; CEDIA workshops; Rankings that win work (a hue dot each) |
| 4 | How we work | `how` | Four steps: the fifteen minute call; the plan; the build; the monthly report |
| 5 | Services | `services` | The homepage's six cards, each linking to its page |
| 6 | Closing ask | `book` | "Talk to the person who built it.", the button, "Fifteen minutes. Bring nothing." |
| | Footer | | Entity and city; Home, Privacy, the email |

Every page links to the six service pages (Jonathan, 2026-09-27: "Each page should also link internally to the other service pages"): the homepage and `/about/` through their six cards, `/book/` through its Services dropdown, and each service page through a quiet "Other services" row above its footer (Style Guide 6.1, dated exception).

## History: the seven-block homepage (2026-09-13, never shipped)

Decided 2026-09-13 (`brainstorms/2026-09-13-landing-page-sop.md`, `decisions/log.md` same date). Alignment per block was pending render approval (variations A, B, C in `renders/`).

## Block order and anchors

| # | Block | Anchor id | Purpose | Alignment |
|---|---|---|---|---|
| 1 | Hero | `hero` | Promise plus the pain, VSL, first ask | Centered (confirmed) |
| 2 | About | `about` | Founder credibility, so the rest reads as an insider's | Pending |
| 3 | How it Works | `how` | The 7 step process with the step-7 loop | Pending |
| 4 | Similar Results | `results` | Three case tiles, numbers only | Pending |
| 5 | Portfolio | `portfolio` | Monarc's work product | Pending |
| 6 | Upsell | `offer` | Level 1, Level 2, the pilot. No dollar amounts | Pending |
| 7 | Final ask | `book` | Same button, same label | Centered (mirrors the hero) |
| | Footer | | Entity, email, phone (pending), anchor links | |

Nav: brand mark left, anchor links (About, How it works, Results, Portfolio, The offer), button right. Mobile: brand and button only.

## 1. Hero

- h1 (8 words max). Draft: **"Booked appointments with high ticket prospects."** Source: `context/offer.md` headline.
- Sub (25 max). Carries the problem statement (Q20). Draft: "You run the marketing, the sales calls, the appointments, and the installs. Monarc runs top of funnel so high ticket work keeps coming." Source: the 2026-09-08 problem section, `context/website.md`.
- Button: "Book a 15 minute call". **Jonathan, 2026-09-19: the button opens a popup (Style Guide 6.11 pattern), four steps, one question each: first name, email, phone, then open afternoon times from the business calendar (Style Guide 6.10 rules, Apps Script backend `references/apps-script-booking.md`). Send books the slot with a Google Meet invite and emails Jonathan through formsubmit.co. The sent state shows in the popup: "Booked." with the time, "Requested." when the booking failed, "Received." with the calendar link button when no time was picked or the backend is offline.** Without JavaScript the button goes straight to the appointment schedule link. Set by Jonathan 2026-09-19: `CALENDAR_LINK = https://calendar.google.com/calendar/appointments/schedules/AcZssZ3L5Jkwx6J345Nhh80VcpdcJJ4ecY1B5-EwKup0DJLadI9ccKviFeXwYMStSeViy-R2P3v_ieO2` (the booking page; drop `?gv=true`, which is only for Google's embed popup). Use it as a plain link on Monarc's own Dark Oak button, `target="_blank"`. Never paste Google's scheduling-button snippet: it adds a `#039BE5` button labeled "Book an appointment" and an external stylesheet, breaking Color 2, Color 4, and Copy 6.
- Media: VSL, 16:9, centered under the sub. **Pending**: Jonathan records it (Q7). Script: `templates/vsl-draft.md`, Monarc worked example, v1 awaiting approval. Placeholder: the three hero stills in a row with the caption "Video coming."
- No trust strip, no second button, no feature cards under the hero.

## 2. About

- h2 draft: **"Sold and installed before we marketed."**
- Sub draft: "Lutron certified. AIA presentations to architects. CEDIA workshops. Monarc was built by someone who has wired the rough-in and closed the six figure proposal."
- Body: three to five short lines. Credentials only as stated in `context/about-me.md` and the old founder line in `context/website.md`: Lutron certified, AIA presentations, CEDIA workshops. **No years, no start date** (Q19).
- Media: founder photo, 4:5. **Pending**: none in the AIOS. Placeholder box labeled "Founder photo."
- Why second: integrators buy from someone who has done the work (Q18).

## 3. How it Works

- h2 draft: **"How it works. Seven steps, one loop."**
- Sub draft: "One kickoff meeting, then the pages, the ads, and the phone. Step seven runs every month."
- Steps (Jonathan, Q16, his order). Step titles 8 words max, one line of body each:
  1. **Onboarding.** New landing pages mapped to your service area and the brands you spec.
  2. **Targeting and offering.** Body copy **pending** (Q16 flag): which searches, which offer per page.
  3. **Managed Google Ads on every page.** Each landing page gets its own campaign pointing at it.
  4. **The phone starts ringing.** Buyers already searching land on the page built for that search.
  5. **5 minute response, meeting booked (Level 2).** A person calls the lead and books your calendar. The "(Level 2)" label is required (Q17).
  6. **You close the meetings.** You show up to the appointment. That is the whole job.
  7. **The loop.** Optimize the pages and the messaging. More revenue, more ad spend, repeat. Drawn with one loop mark back to step 1, in Charcoal Blue or Stone, never Dark Oak.
- Layout of seven steps: **pending** (numbered list, two rows, or a horizontal track). Decide after the alignment render.
- Source: `context/offer.md` (Level 1 and Level 2 contents), `context/roadmap.md` step 14 (14 day build).

## 4. Similar Results

- h2 draft: **"One search term. $500k and counting."**
- Sub draft: "Three jobs from one ranked page and $2.5k of ads. Numbers from the winning proposals."
- Three tiles, each: photo 4:3, one outcome line, the number. Numbers only; no quotes until a named testimonial exists (Q12). Source of truth for every figure: `context/about-business.md`, Proof jobs table.
  1. Georgian Colonial restoration. $70k. Whole home audio, James Loudspeaker indoors and out, wired from rough-in. Found the #1 page for "whole home audio in Annapolis." Photo `assets/hero/hero-rough-in.jpg`.
  2. Waterfront great room. $91k. Lutron Ketra lighting, from $2.5k of Google Ads. Photo `assets/hero/hero-waterfront.jpg`.
  3. Baltimore penthouse. $50k. Control4 and Lutron retrofit. Photo `assets/projects/baltimore-penthouse-frame-01.jpg` (check the PHA polo exposure first).
- One line under the tiles: "That one contractor is now over $500k in lifetime value."
- Never name the integrator or link pha.systems.
- Open inconsistency in `context/about-business.md` ($70k vs "$90k+ James Loudspeaker"): the tiles use the table values ($70k Georgian, $91k Ketra). Jonathan confirms on the render.

## 5. Portfolio

- h2 draft: **"What we build."**
- Sub draft: "Sites, landing pages per service and area, and the ads behind them."
- Media: screenshots of Monarc work product, 16:10. **Pending** (Q13): which built sites or ads can be shown and with whose consent. Until then, three labeled placeholder boxes. Never room photos here.

## 6. Upsell

- h2 draft: **"Two tiers. Both start with a pilot."**
- Sub draft: "Start on Level 1 for 60 days, no setup fee, $1,000 of ad spend matched. Day 60: continue or walk and keep the site."
- Two cards, contents from `context/offer.md`, no dollar amounts for the retainers:
  - **Level 1.** Website (new build or takeover). One landing page per service and per area. Managed Google Ads. SEO: local, Google Business Profile, content, technical. Weekly PDF report, one 15 minute meeting a month. Ad spend paid on top, $1,000 a month minimum recommended.
  - **Level 2.** Everything in Level 1 plus First Responder: a person calls every lead within 5 minutes, 9am to 7pm Eastern, Monday to Friday. Qualified on your pricing floor and service area. Booked into your calendar, email follow-up after. Month to month.
- Pilot line under the cards: 60 days, no setup fee, $1,000 matched, day 60 continue on a 6 month term or walk with the site, pages, and data.

## 7. Final ask

- h2 draft: **"Your next high ticket job is searching now."**
- Sub draft: "Fifteen minutes. Bring nothing."
- Button: "Book a 15 minute call" to `CALENDAR_LINK`. Same label as the hero. The only two buttons on the page.

## Footer

- "Monarc Build, LLC · Annapolis, Maryland" (the middle dot is allowed; em dashes are not).
- jonathan@monarcbuild.com. Phone **pending**.
- Anchor links repeating the nav. No link to any old subpage.

## Ad page /av_marketing/ (rebuilt 2026-09-23, live the same day)

**2026-09-30, restyled, live the same day (Jonathan: "push"; the journey tag held back) (Jonathan: "update the creative style to match the Google-esque style"; interview `brainstorms/2026-09-30-av-marketing-google-look.md`).** Look only: every block and word below stays, in the homepage's `monarc` theme (white, Roboto, the butterfly's four hues, butterfly blue buttons). The hero keeps the full-bleed colonial photo under a `#202124` wash and gains the eyebrow "Marketing for AV integrators" above the h1 (it also echoes Google Ads campaign 07, which lands here); the services sit on the light band as white flip cards with the hues on their icons; "Page 1" is butterfly blue. Built by `scripts/avm_restyle.py` into `staging/av_marketing/`; renders `renders/2026-09-30/av_marketing-google-*.png`. The block table below still holds for the blocks and the copy; where it names house colors or faces (Charcoal Blue, Dark Oak, Sand, serif), read the `monarc` theme.

Style Guide section 6 governs (rules 12 to 15 carry the block order, the team, the pill, the services). Source: `projects/monarcbuild-site/public_html/av_marketing/index.html`, live at https://monarcbuild.com/av_marketing/ since 2026-09-23; this is the LinkedIn destination. The 2026-09-14 funnel at `/avmarketing/` was deleted from the server the same day; `.htaccess` 301s that address to `/av_marketing/` with the query string kept (so `utm_id`, `utm_source`, and the rest survive the hop). Last copy: `archives/site-avmarketing-2026-09-23/`. Jonathan's brief, the brainstorm, and the decisions: `brainstorms/2026-09-23-avmarketing-conversion.md`, `decisions/log.md` 2026-09-23 (two entries).

| # | Block | Anchor id | Copy and source |
|---|---|---|---|
| 1 | Hero | `hero` | h1 **"Book more quality leads as an AV contractor."** (Jonathan's line, 8 words). Sub **"Booked appointments with high ticket prospects in your service area."** (2026-10-01, outcome first; was "Schedule an appointment with our team.") Button "Book an appointment". The colonial house full bleed behind it under a Charcoal Blue scrim, text in White (Style Guide 6.8). |
| 2 | The audit | `audit` | Label "On the call". h2 **"Fifteen minutes. You leave with the audit."** One line: what is pulled before the call. Source: the cold call script's free-value move, `references/voice.md`. |
| 3 | Brands ticker | `brands` | Label "The systems your buyers search for", then a scrolling bar of the names: Lutron, Ketra, Control4, Crestron, Savant, Josh.ai, James Loudspeaker, Sonance, Kaleidescape, from `context/icp-brands.md`. |
| 4 | Proof | `proof` | Label "Proof". h2 **"First page rankings. Three jobs and counting."** One row (the first-page line, written to the outcome), three flip cards (the Georgian, the waterfront, the penthouse; photo and title in front, the install and the marketing on the back; the dollar figures and "$2.5k of ads" came off 2026-09-27, Style Guide Copy 4), and the closing line "From one page and one ad account." Sources: `context/about-business.md` Proof jobs and Ranking claim. |
| 5 | Services | `services` | **2026-10-01, outcome first** (Jonathan: "get rid of the seventh service... make the copy about being outcome-based"; `brainstorms/2026-10-01-av-marketing-outcome-copy.md`). Label "What you get back". h2 **"Six services. One return: booked installs."** Sub "Each one built to put high ticket buyers from your service area on your calendar." Six static cards on the light band, from his reference: the icon in a butterfly hue, the bold service name, one or two sentences on what the buyer gets back, no number promised. In order: Website build and design; Local SEO and Google Business Profile; Google Ads (ends on the lead tagging and the monthly report, the Pilot's promise); Meta Ads; Email follow-up (was "Email drip sequences"); Appointment setting (kept, Q7). Monitored analytics came off. No flip, no counter, no hint. Drafts for his approval on `renders/2026-10-01/av_marketing-outcome-*.png`. ~~2026-09-23: "What we run", "Seven services. One team on your pipeline.", seven flip cards with the strategy on the back.~~ |
| 5b | The logo banner | `citations` | **Approved 2026-09-28** (Jonathan: "add the "We Work With" banner to each of the landing pages"; `brainstorms/2026-09-28-landing-pages-banner.md` Q1, Q4). The logo banner template (below): the label "We list your business on" with the house hairlines, then the big marks (`logos-lg`) of Yelp, Google, Apple, Facebook, Bing, Angi, Tripadvisor in full color. Paper ground between the Charcoal Blue services block and the Sand fit band, apart from the brand-name bar at block 3. Built 2026-09-25 with the label "National citations we work with"; renders `renders/2026-09-28/av_marketing-banner-1440.png`. The page links `../assets/site.css` for it. |
| 6 | Fit | `fit` | h2 **"Built for a specific kind of shop."** "For" and "Not for" columns. Brands from `context/icp-brands.md`; the no-guarantee line from `context/offer.md`. |
| 7 | The math | `math` | h2 **"One closed install covers the month."** Three lines from the call math in `context/offer.md`. No ad spend figure. |
| 8 | About us | `team` | Label "About us", h2 **"Sold and installed before we marketed."**, the credentials sub (round-1 About sub). No tiles: Jonathan will not have team photos (2026-09-23). |
| 9 | FAQ | `faq` | h2 **"Four questions before you book."** Cost (on the call), speed (fourteen days, `context/roadmap.md` step 14), ownership (yours, `context/offer.md`), what if it does not work (no guarantee, you keep the site, the pages, the data). |
| 10 | Final ask | `book` | Same h2 and sub as homepage block 7. Second "Book an appointment" button and the caption line. |
| | Footer | | Entity, mailto, phone pending. |
| | Floating pill | | Third "Book an appointment", Style Guide 6.14. |

All three buttons open the five-step popup (first name, email, phone, technicians on the team, then the calendar; Style Guide 6.10) and fall back to the Google Calendar booking page without JavaScript. Sent state renders under the hero. `noindex` stays until Jonathan says otherwise. No timer bar, no scarcity claim, no terms, no prices. The drip that follows a booking: `templates/booking-drip.md`.

## Website build page /website-build/

Moved 2026-09-25 to `pages/website-build.md`. The house-style build of 2026-09-25 (ten blocks, seven flip cards, never pushed) is kept there under "History"; the page is rebuilt in the editorial theme as one of the six service pages below.

## Service pages (added 2026-09-25, the Google Ads plan)

Six pages, one per service line, each the destination of one of Monarc's own search campaigns (`projects/google-ads/`). Each page is built in its own theme (Style Guide section 8; one JSON per theme in `themes/`) on the shared skeleton of Style Guide 6.16. The full spec of each page lives in its own file under `pages/`; this table is the index. Jonathan's two interviews behind them: `brainstorms/2026-09-25-google-ads-campaign.md` and `brainstorms/2026-09-25-google-ads-pages.md`.

| Page | URL | Theme | Hero render | Status | Spec |
|---|---|---|---|---|---|
| Managed Google Ads | `/google-ads/` | google | The cast: an angler on the bank, mid-cast over a river | Live 2026-09-26 | `pages/google-ads.md` |
| Website design | `/website-build/` | editorial | A shopfront at dusk, lights on, door open | Live 2026-09-26 | `pages/website-build.md` |
| SEO | `/seo/` | saas | ~~A house mid-build~~ A contractor on a clay town map roping in the map pin and a five-star review card (Jonathan, 2026-09-26) | Live 2026-09-26 | `pages/seo.md` |
| Email marketing | `/email-marketing/` | commercial | The ball on the lip of the cup, flag in red | Live 2026-09-26 | `pages/email-marketing.md` |
| Facebook ads (the Meta Ads service line) | `/facebook-ads/` | social | A billboard over a neighborhood at dusk | Live 2026-09-26 | `pages/facebook-ads.md` |
| AI automation | `/ai-automation/` | time | An evening porch, lights on, the work truck in the drive | Live 2026-09-26; tools unnamed | `pages/ai-automation.md` |

Order of work: all six style tiles (`tiles/tile.html?theme=<name>`, rendered to `renders/2026-09-25/tile-<theme>-1440.png`, each with its render candidates from `candidates/<slug>/`) approved by Jonathan before any page is built; then the pages in the order he confirmed on 2026-09-25: Google Ads, Website, SEO, Email, Facebook, Automation. Slugs confirmed the same day: `/seo/`, `/facebook-ads/`, `/ai-automation/`. `/av_marketing/` stays the LinkedIn destination in the house theme.

**Services menu (Jonathan, 2026-09-26: "a menu dropdown for services should hold all of these individual landing pages").** A "Services" dropdown is the first item of the header menu on the live homepage, `/about/`, and `/book/`, listing only service pages that are live, in the build order. The six service pages carry no menu (Style Guide 6.1 holds; Jonathan chose site pages only). `scripts/services_menu.py` owns the list and rewrites the menu on the three pages; when a service page is pushed, add it to `LIVE`, rerun, and push the three pages. **From 2026-09-27 the menu is on `/about/` and `/book/` only:** the new homepage lists the six services as cards (Section Spec, "Homepage"), and the old `live/index.html` copy and its `push-as` retired with it. The old site's header menu shows only at 1024px and up, so phones do not see it; that is the old build's behavior, unchanged. The homepage draft carries the same menu when it ships. **Idea, not built (Jonathan, 2026-10-01: "add this as an idea for the service dropdown. I like this visual."):** the dropdown as a row of picture cards, one per service page with its render tile (`assets/generated/<slug>/tile.jpg`) and the service name under it, after Arctic Electricians' Services menu (`references/design-references.md` entry 2).

**Decided (Jonathan, 2026-10-01): "headline swaps in the trade from the ad link".** One page serves several trade ad groups, so one h1 cannot mirror every trade's search: each ad group's final URL carries a trade word (`?t=electricians`) that the page swaps into the h1 from a fixed list of five trade words, falling back to "contractors"; nothing else on the page changes. Not built yet.

What every service page shares, in order (Style Guide 6.16): brand mark; the split hero (h1, sub, one line where the page needs it, the hero button; the render beside them); the logo banner right under the hero (Jonathan, 2026-09-28, a dated exception to the 6.16 v2 list: "We list your business on", no Google logo on `/google-ads/`, no Facebook logo on `/facebook-ads/`; the template below); four static cards; one proof or walk-through block; Works for and Not for in the theme's green and red; three FAQs (cost, the call, what if); the final ask with the final-ask button and "Fifteen minutes. Bring nothing."; footer, the pill on the hero label, the popup and sent state in the theme. Every page carries the `/website-build/` head: both gtag configs, the `?sent=1` guard, `book_appointment` with its page label, the shared conversion label, the hidden UTM and `gclid` fields, `_next` to its own `?sent=1`, the privacy link, `noindex`, `mb-page-type` ad, and `mb-theme`.

## Section templates

Reusable blocks any monarcbuild.com page can carry. Markup lives in `templates/` (this folder); CSS in `public_html/assets/site.css`, which the page must link (`../assets/site.css` one folder down, `/assets/site.css` on the homepage).

### Logo banner (added 2026-09-25, from Jonathan's screenshot "National Citations We Work With")

- Markup: `templates/logo-banner.html`. Section class `logos`, anchor of the page's choosing (`citations` on the ad page).
- A centered label with the 40px hairlines (Style Guide Typography 6), then a full-width bar between two Sand hairlines where the logos scroll left, 45 seconds a loop and never paused on hover (Jonathan, 2026-09-27: "dont make the banner stop on hover but decrease speed by 20%"; it was 36 seconds, paused on hover), faded at both edges, still under reduced motion: otherwise the brands ticker's mechanics (Style Guide 6.12) with images instead of names. On phones the label drops its hairlines so it does not wrap around them.
- Logos: `public_html/assets/logos/*.svg`, seven files pulled from Wikimedia Commons on 2026-09-25 (Yelp, Google, Apple, Facebook, Bing, Angi, Tripadvisor; the current marks, Tripadvisor 2025 and the Bing fluent wordmark). Every `<img>` carries its name as alt text; the second set exists for the seamless loop and is hidden from screen readers. No links on the logos on an ad page (Style Guide 6.1).
- **Decided 2026-09-26 (Jonathan): full color.** The template carries `logos-color`; Style Guide Media 6 records the exception to Color 4.
- Heights per mark are tuned in `site.css` so the seven read at one weight (22px to 38px at desktop, 18px to 30px on phones); a new logo gets its own `.logo-<name>` line there.
- **On every ad landing page and the homepage (Jonathan, 2026-09-28, `brainstorms/2026-09-28-landing-pages-banner.md`):**
  - Where: right under the hero on the homepage and the six service pages; after the services (5b) on `/av_marketing/`.
  - The label reads **"We list your business on"** (was "National citations we work with"). It says what Monarc does on those sites and claims no partnership. Never "We work with": Google suspends accounts without warning for ads that "make it seem like you're supported by another brand" (Style Guide Media 7).
  - The big marks everywhere (class `logos-lg`, 34px to 58px on desktop); `logos-top` seats the banner under a hero. Both are in `site.css`.
  - The page that sells a platform's ads leaves that platform's logo out: no Google logo on `/google-ads/`, no Facebook logo on `/facebook-ads/`.
  - Full color on every page, the dark `/ai-automation/` included (his call; the Apple and Tripadvisor marks read faintly there).
  - Built pages take it from `scripts/build_service_page.py` (`logo_banner()`, the `<!-- logo-banner -->` marker, `LOGOS_LEFT_OUT`); `/av_marketing/` carries it by hand.

## Redirects (build step, after approval)

In `public_html/.htaccess`, 301s: `/about` to `/#about`, `/how-it-works` to `/#how`, `/results` to `/#results`, `/book` to `CALENDAR_LINK`, `/territories` and `/permit-intelligence` to `/`. Old pages move to `archives/`. **Check first**: the live homepage fires a Google Ads conversion event on page view (`AW-18358744393/xvGlCMOiweMcEMnqkLJE`); confirm what the Ads account counts as a conversion before redirecting `/book` (Q22 flag).

## Tracking (added 2026-09-13)

- LinkedIn ad set UTM template, Jonathan's words: `utm_id={{AD_SET_ID}}&utm_source=linkedin&utm_medium=paid-social`. Every ad destination on monarcbuild.com must accept these parameters without redirecting them away (a 301 from an old URL must carry the query string through).
- **Closed 2026-09-24:** GA4 `G-JQ977C0MY7` is live on every page next to the Google Ads tag (`AW-18358744393`), with a `book_appointment` event on each sent state. The LinkedIn Insight Tag (partner id 9685362) was placed by Jonathan on five pages on the server; the same snippet goes on the homepage, results, and `/av_marketing/` on his go. Tag status lives in `references/channel-connections.md`. Every page keeps both tags; a rebuild must carry them over.
- **Gap, pending Jonathan:** the primary button goes to a Google Calendar appointment schedule, which drops the UTMs. To attribute a booked call to an ad set, either pass the UTMs into a Monarc-hosted booking page that holds them in a hidden field, or read the ad set out of GA4's session data by time and match to the calendar booking by hand.
- **Check the macro:** `{{AD_SET_ID}}` is the Meta-style name. LinkedIn Campaign Manager's dynamic UTM macros are `{{CAMPAIGN_ID}}`, `{{CAMPAIGN_NAME}}`, `{{CAMPAIGN_GROUP_ID}}`, `{{CREATIVE_ID}}`, `{{ACCOUNT_ID}}` (LinkedIn calls the ad set a campaign). If Campaign Manager does not substitute `{{AD_SET_ID}}`, the literal text arrives in `utm_id`. Verify on the first click in the ad preview before spend starts.
- Assistant suggestion, not decided: add `utm_campaign={{CAMPAIGN_NAME}}` and `utm_content={{CREATIVE_ID}}` so a report reads as words, not ids.
- **Built 2026-09-13, not pushed:** the LinkedIn destination `/avmarketing/` (Style Guide section 6) reads `utm_id`, `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`, `li_fat_id`, the landing URL, and the referrer into hidden form fields, so every application email carries its ad set. The Google Ads "Submit lead form" snippet on that page fires only on `?sent=1`. Live at `/av_marketing/` since 2026-09-23 with the calendar step; tags per the line above.

## Sources the build must read

`Style Guide.md` (this folder), this file, `references/voice.md`, `references/design-references.md`, `context/offer.md`, `context/about-business.md` (Proof jobs, PHA rule), `context/about-me.md`, `context/website.md` (pipeline, charset rule, live state).
