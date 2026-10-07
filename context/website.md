# monarcbuild.com

Update this page when the site changes.

## Live: /av_marketing/ in the homepage look (pushed 2026-09-30)

Jonathan: "update the creative style to match the Google-esque style", then "push". Interview: `brainstorms/2026-09-30-av-marketing-google-look.md` (Q1 to Q7).

- `/av_marketing/` now wears the `monarc` theme of the homepage and `/about/`: Roboto, white and light grey bands, butterfly blue buttons, plain grey section labels. Look only: every block and word stayed. The colonial photo stays full bleed under a near-black wash; a new eyebrow "Marketing for AV integrators" sits above the h1 (it also serves Google Ads campaign 07, drafted to land here); the seven services are white flip cards on the light band with the butterfly's hues on their icons; "Page 1" is butterfly blue; the popup, calendar, and form match.
- The logo banner ("We list your business on", approved 2026-09-28) went live on the page with it, and `assets/site.css` went up with its large-logo rules (`logos-lg`), which the live stylesheet lacked; every page carrying the banner now shows the big marks.
- Not pushed: the visitor-journey tag (`/assets/journey.js`), which waits on Jonathan's privacy-page lines. The live page is `staging/av_marketing/index-push.html`; `staging/av_marketing/index.html` and the mirror carry the tag for later.
- Pushed with `site_sync.py push-as` (page) and `push assets/site.css`. Old live copies: `archives/site-av_marketing-2026-09-30/` (`live-index-prepush.html`, `live-site.css`). Read back: both identical to the pushed files; the Google Ads tag, GA4, the LinkedIn tag, and `noindex` all still on the page.

## Live: the label dots off, the citations banner slower (pushed 2026-09-27)

Jonathan: "remove this icon from these sections. also dont make the banner stop on hover but decrease speed by 20%", then "push and the few color icons should go from my page" (his pick: the Google-colored dots on `/google-ads/`).

- The four colored dots before the section labels are gone: the butterfly-color ones on the homepage and `/about/`, the Google-color ones on `/google-ads/`. The labels are plain grey caps. The small dot beside each service card's name, the `/about/` credential dots and step rings, and the fit checks and crosses stay.
- The citations banner on the homepage runs 45 seconds a loop (was 36, 20% slower) and keeps moving under the mouse; it still stands still for anyone who turns motion off on their device.
- Pushed `assets/site.css`, `/`, `/about/`, `/google-ads/`. Old live copies: `archives/site-updates-2026-09-27c/`. Read back: all four 200 and identical to the pushed files; no dots markup, no dots rules, `45s` and no hover pause in the live stylesheet.

## Live: the job figures off, the citations strip, the new /about/, and the Other services rows (pushed 2026-09-27)

On Jonathan's "push the updates". Specs: `projects/Landing Page Build/Section Spec.md` (Homepage and About page sections); the about interview: `brainstorms/2026-09-27-about-page-rebuild.md`.

- **No job figures on any page** (Style Guide Copy 4, amended; Jonathan: "remove the figures and keep scope"): the homepage, `/google-ads/`, `/seo/`, and `/av_marketing/` show each job's scope and where the lead came from, not its dollar value or the ad spend. The "Page 1" and "#1 page" claims stay, and so does the margin math on `/av_marketing/` ("a $10k to $15k ticket... $3k to $4.5k in gross profit").
- **Homepage:** the Georgian card shows the interior rough-in (`assets/projects/cards/georgian.jpg`, cropped high), and the rolling "National citations we work with" strip sits right under the hero (seven logos in `assets/logos/`).
- **`/about/`** rebuilt in the homepage's theme (built by `python scripts/build_service_page.py about`): his first-person story with the butterfly large, the four credentials, how we work in four steps, the six service cards, "Talk to the person who built it." Indexed, canonical `https://monarcbuild.com/about/`, link preview `assets/og/about.jpg`, the booking popup. The "Three years" tenure line and the permit-intelligence story are gone. The old page: `archives/about-2026-09-27-before-rebuild/`.
- **Other services:** each of the six service pages has a quiet row of links to the other five above its footer (Style Guide 6.1, dated exception). The homepage and `/about/` link to all six through their cards; `/book/` through the Services menu. `/av_marketing/` and `/privacy/` have no row.
- `/av_marketing/` went up from `staging/` again: the live page plus the figure lines only. The logo strip in the mirror's copy stays off the site.
- Old live copies: `archives/site-updates-2026-09-27b/`. Read back: all nine pages 200 and identical to the pushed files; no job figures on the homepage, `/about/`, or the six service pages; the seven logos identical; the two new pictures pixel-matched (the server re-saves JPEGs).
- Still open: `llms.txt` still describes the old permit-intelligence offer. `/google-ads/` is at 405 visible words with the row, 5 over the 400 budget.

## Live: the new homepage and the butterfly mark on every page (pushed 2026-09-27)

On Jonathan's "go and make the favicon the butterfly". Interview and three rounds: `brainstorms/2026-09-26-homepage-google-rebuild.md`; spec: `projects/Landing Page Build/Section Spec.md` (top section) and `themes/monarc.json`.

- **Homepage** (`/`, from `public_html/index.html`, built by `python scripts/build_service_page.py home`): a Google product-site layout in Roboto on white with the butterfly's four hues. A centered hero ("Marketing for contractors. Built by installers.", the sub, a search bar typing "marketing for contractors", "Book an appointment"), the six service pages as render cards, the three jobs, Who it is for and Who it is not for, about, four questions, the closing ask; every button opens the five-step booking popup. Indexed, canonical `https://monarcbuild.com/`, a new link preview (`assets/og/home.jpg`), organization data with no ratings. **The page-view conversion is gone** (tracking checklist item 4 ticked); the shared conversion fires on bookings only. The LinkedIn tag and both gtag configs carried over.
- **The mark:** the butterfly (`projects/Landing Page Build/brand/`, candidate A) is the favicon (`/favicon.svg`, `/favicon.ico` at 16, 32, 48, `/apple-touch-icon.png`) and the header lockup on all eleven pages: the homepage, the six service pages, `/about/`, `/book/`, `/privacy/`, `/av_marketing/` (white name over the hero photo). Browsers hold old favicons; a hard refresh shows it at once, Google's results pick it up on the next crawl.
- **`/av_marketing/`** was pushed from `projects/monarcbuild-site/staging/av_marketing/index.html`: the live page plus the butterfly only. The mirror's copy also carries the "National citations" logo strip, built 2026-09-25 and never approved to go live; it stays unpushed until Jonathan says so.
- The old homepage (the 2026-09-08 export) and its working copy `projects/monarcbuild-site/live/` are retired to `archives/site-homepage-brand-2026-09-27/` with every other replaced live file; `push-as` for the homepage retires with it. The 2026-09-13 seven-block draft is at `archives/homepage-draft-2026-09-13/`.
- Read back: all eleven pages 200 and identical to the pushed files; the favicon files identical; the pictures pixel-identical (the server re-saves JPEGs and PNGs).
- Still open: `/about/` says "Three years inside custom home integration" (a tenure claim, Style Guide Copy 3), left for Jonathan (gone with the `/about/` rebuild, pushed later the same day). `llms.txt` still describes the old permit-intelligence offer.

## Live: /email-marketing/, /facebook-ads/, /ai-automation/, and all six in the Services menu (pushed 2026-09-26)

On Jonathan's go ("Push them. Good enough"): the last three service pages (themes `commercial`, `social`, `time`) with their images; `/website-build/` again with all four portfolio frames filled; `assets/site.css` with the three new themes' rules (scoped to those themes, so the live pages did not change); the homepage, `/about/`, and `/book/` with the menu now listing all six service pages. Before the push the three menu pages differed from live only by the three new links; old live copies in `archives/site-service-pages-2026-09-26b/`. Read back: every page 200 and identical to the local file, `noindex`, the conversion label, the booking return to its own `?sent=1`; images pixel-identical; the server resized the automation sticker to 1600 wide and kept its transparency. Specs and open points: `projects/Landing Page Build/pages/<slug>.md`. No ads point at any service page yet; each still needs its call-script line and the tracking checklist.

## Live: /website-build/ and /seo/, the Services menu, /google-ads/ round 2 (pushed 2026-09-26)

On Jonathan's go ("go with posting the pages and sticking them under the services tab"): `/website-build/` (editorial theme) and `/seo/` (saas theme, the lasso hero) went live with their images; `/google-ads/` got round 2 (h1 "Managed Google Ads for contractors." with "Google" in the four colors, the salmon hero, phone centering); `assets/site.css` again (every change scoped to themed pages; `/av_marketing/` has no theme and is unchanged). Then the homepage (from `projects/monarcbuild-site/live/index.html`), `/about/`, and `/book/` with a Services dropdown in the header nav: Google Ads management, Website design, SEO (`scripts/services_menu.py`, live pages only). The three pages were checked against live first; they differed only by the menu. Old live copies in `archives/site-service-pages-2026-09-26/`. Read back: every page 200 and identical to the local file, `noindex` on the service pages, the conversion only on `?sent=1`, images pixel-identical (the server re-saves JPEGs, so the bytes differ). On phones the site hides the whole header nav, so the menu shows on desktop only. The job photos under `assets/georgian/` and `assets/projects/` were not pushed: the local copies are larger than the server's re-saved ones and show the same picture.

## Live: /google-ads/ Google Ads management page (pushed 2026-09-26)

The first of the six service pages of Monarc's own Google Ads plan (`projects/google-ads/`), in the `google` theme; spec `projects/Landing Page Build/pages/google-ads.md`. Pushed on Jonathan's go with its two hero images and the shared `assets/site.css` (the theme layer only touches pages that declare `data-theme`, so `/av_marketing/` is unchanged). Read back live: 200, `noindex`, two "Book the audit" and one "Book your fifteen minutes", the conversion fires only on `?sent=1`, the no-slash address 301s with the query string kept. No ads point at it yet; the tracking checklist in `projects/google-ads/` comes first. `scripts/site_sync.py` push now creates every missing remote folder level (it failed on `assets/generated/google-ads/` the first time; the page and stylesheet had already gone up).

## Live: /av_marketing/ AV contractor booking page (pushed 2026-09-23)

Pushed 2026-09-23 on Jonathan's "upload this to the public html with the url slug av_marketing": `av_marketing/index.html`, one file, through `scripts/site_sync.py`. Verified live: 200, `Content-Type: text/html; charset=UTF-8`, charset meta first, `noindex`, ad-mode meta, h1 "Book more quality leads as an AV contractor.", three "Book an appointment" buttons (hero, final ask, floating pill), the calendar step with "Confirm appointment", the sent-state redirect on the new slug, and the three hero images at 200 (live since 2026-09-14). Source of truth: `projects/monarcbuild-site/public_html/av_marketing/index.html`.

What is on it (second push, later on 2026-09-23, on Jonathan's "update this on the website"; verified live the same way): the real camera photo of the colonial house full bleed behind the hero under a Charcoal Blue scrim; the audit block, one line; the brands ticker; proof (the "Page 1" outcome line, three flip cards at $69k, $91k, $51k on real photos, the penthouse from the listing photo Jonathan supplied, `assets/projects/baltimore-penthouse.jpg`, pushed with the page); seven services as White flip cards on a Charcoal Blue band, Dark Oak icons and text, a channel-purpose label and a strategy paragraph on each back, no callback-time promise; fit; the math; About us (label, h2, credentials line, no team tiles); FAQ accordions; final ask; footer; the popup with first name, email, phone, then a calendar. Style Guide section 6, Section Spec "Ad page /av_marketing/", brainstorm `brainstorms/2026-09-23-avmarketing-conversion.md`, decisions 2026-09-23.

**Third push, 2026-09-23 about 5:05 pm: the calendar is live.** Jonathan deployed the Apps Script from `sumreat17@gmail.com` (selfTest and dripSelfTest passed in his logs); the web app URL is in `BOOKING_URL` on the page, with the shared token. The popup is five steps (first name, email, phone, technicians on the team, then the calendar), and the last step now shows real open times from the "Monarc Build" calendar, two weeks out; Confirm books the event with a Meet link, emails the prospect a confirmation, writes the bookings sheet, and emails Jonathan. The bridge that sent the buttons to Google's booking page is inactive now that the URL is set. Also in this push: the three case photos pinned to equal boxes. Fourth push, about 5:40 pm: the page points at a second deployment of the script (the three-email flow: confirmation with the Meet link, the time, and who they speak with; a reminder one hour before; Jonathan's notification; queue every five minutes), verified live.

**Still open:** `setup` and `installQueue` not confirmed in Jonathan's logs (the sheet is created on the first booking either way; without the trigger no follow-up or reminder goes out); no `AIRTABLE_TOKEN`, so nothing reaches the CRM yet; the drip wording awaits Jonathan's read; formsubmit.co's one-time activation is still unconfirmed; the homepage draft carries the same URL but is not pushed.

**Site cut to four pages (2026-09-24, Jonathan: "results can go, how it works can go, territories can go, permit intelligence can go and the 301 can go"):** live now: `/` (old build homepage, button to `/book`), `/about/`, `/book/` (email form), `/av_marketing/` (the ad page with the calendar). Removed from the server and the mirror: `/results/`, `/how-it-works/`, `/territories/`, `/permit-intelligence/` (copies in `archives/site-pages-removed-2026-09-24/`). The `/avmarketing` 301 is gone, so that address 404s; any ad still pointing there must move to `/av_marketing/`. Dead links taken out of the homepage (nav, footer, "More from the field record"), about, and book; `llms.txt` lists the four pages on monarcbuild.com (its prose still describes the old permit-intelligence offer; not rewritten). Read back: four pages 200 with no dead links, five old addresses 404.

**Privacy page, LinkedIn tag, one address (2026-09-24, pushed on Jonathan's go):** `/privacy/` is live (Style Guide section 7; `noindex`; Google Ads requires it on any page that takes a name, email, or phone), with a Privacy link in the footer of the homepage, about, book, and the ad page (ad page rule 6.1 amended for that one link). The LinkedIn Insight Tag now sits on the homepage and the ad page too, so every page that takes data carries the Google Ads tag, GA4, and LinkedIn. `.htaccess` sends `www.` and any `/index.html` address to the bare folder address with a 301 that keeps the query string, so the ad platforms count each page once. Read back: five pages 200 with both tags and the link; four redirect addresses 301 to the right place with labels intact. The old Higgsfield copy at monarc-build.higgsfield.app was taken off that address the same night by renaming its subdomain to `monarc-build-old` (the connector has no unpublish); the old address no longer answers.

**Tags (2026-09-23, evening):** Google Analytics property created by Jonathan, measurement id `G-JQ977C0MY7`; the config line sits next to the Google Ads tag on every page, and a `book_appointment` event fires on the sent state of the ad page, the homepage popup, and `/book/` (whose Google Ads conversion used to fire on every view of the page; now only on the sent state). Pushed on Jonathan's go 2026-09-24 (just after midnight): eight pages, each read back over HTTPS with the GA4 id present and the LinkedIn tag count unchanged; the homepage got the tag on its live version, the local draft stayed local. **The LinkedIn Insight Tag (partner id 9685362) is already live** on about, book, how-it-works, permit-intelligence, and territories: Jonathan put it on the server directly, so the local mirror did not have it. Not on the homepage, results, or the ad page yet. The mirror copies of those six old pages were stale (they carried a `/assets/site.css` link that was never pushed; the file 404s live) and were refreshed from live on 2026-09-23; the old copies sit in `archives/site-mirror-2026-09-23/`. Live is the source of truth.

**The old funnel at `/avmarketing/` is gone (Jonathan, 2026-09-23, about 5:30 pm: "get rid of the old avmarketing url").** `.htaccess` now carries a 301 from `/avmarketing/` (and `/avmarketing/index.html`) to `/av_marketing/` with the query string kept, so old links and any ad still pointing there land on the new page with their UTMs; then the folder was deleted from the server. The last live copy of the 2026-09-14 page is at `archives/site-avmarketing-2026-09-23/index.html`; the mirror no longer has an `avmarketing/` folder.

## Live: /avmarketing/ LinkedIn ad page (pushed 2026-09-14, revised same day)

Revision pushed 2026-09-14 on Jonathan's four changes: the step 3 email hint ("The calendar invite with the Google Meet link goes here") removed; the form is a popup opened by a "Book a 15 minute call" button in the hero (dark ground, Paper panel, Close control, Escape closes; inline without JavaScript); the VSL slot is one 16:9 image, `hero-waterfront.jpg` (the rough-in still shows the PHA shirt logo at that size); the terms block is gone and "Our client results." lists the proof jobs as text ($70k Georgian, $91k waterfront Ketra, $50k penthouse, $500k lifetime). The sent state no longer has a calendar button; `CALENDAR_LINK` is removed from the script. Renders: `projects/Landing Page Build/renders/2026-09-14/avmarketing-popup-*.png`.

Pushed 2026-09-14 on Jonathan's "publish": `avmarketing/index.html` plus `assets/hero/hero-rough-in.jpg`, `hero-waterfront.jpg`, `hero-exterior.jpg`. Verified live: page 200 with the UTM query intact, three images 200, charset first, `noindex`, ad-mode meta present. **Live with placeholders:** `BOOKING_URL` and `BOOKING_TOKEN` empty (slot step shows "Live times are offline," sent state falls back to the calendar button), `CALENDAR_LINK` empty (button is a dead `#` with the "Calendar link pending" note showing; mailto fallback is on screen), `DEADLINE` at the placeholder 2026-10-01 Eastern, "Takes about a minute" unmeasured. Each fix is a one-line edit and a re-push of `avmarketing/index.html`.

`projects/monarcbuild-site/public_html/avmarketing/index.html`. Timer bar to a fixed deadline, brand mark, h1 "Booked appointments with high ticket prospects.", sub with "One integrator per metro," instruction line, three hero stills in the VSL slot ("Video coming."), application form to formsubmit.co with the LinkedIn UTMs in hidden fields, sent state, terms, footer. `noindex`. Google Ads base tag kept; the "Submit lead form" conversion fires only on `?sent=1`. Style Guide section 6, decision 2026-09-13.

Rebuilt 2026-09-14 to Jonathan's funnel (Style Guide 6.10): five steps, metro ("Check your metro's availability."), name, email, team size (Just me, 2-5, 6-10, 11+), then open afternoon times, one per hour, from the business calendar. Times show in the applicant's own time zone. Send books the slot through a Google Apps Script web app (`scripts/avmarketing-booking.gs`, setup in `references/apps-script-booking.md`): event on the business calendar with a Google Meet link, invite emailed to the applicant. Then formsubmit.co emails Jonathan with the UTMs, the booking status, and the Meet link, reply-to set to the applicant, one-line auto-reply to the applicant. Sent state says booked, requested, or shows the "Book a 15 minute call" button when no time was picked. Dropped from the 2026-09-13 form: business type, project size, brands, company, phone. Renders in `projects/Landing Page Build/renders/2026-09-14/avmarketing-*.png` (step 1, step 4, step 5 with sample times, sent booked, sent no slot, 1440 and 390).

Push list when Jonathan says go: `avmarketing/index.html` plus `assets/hero/hero-rough-in.jpg`, `hero-waterfront.jpg`, `hero-exterior.jpg` (the stills are local only). Before push: deploy the Apps Script and set `BOOKING_URL` and `BOOKING_TOKEN`, set `DEADLINE` and `CALENDAR_LINK` in the page script, replace "Takes about a minute" with the measured time, confirm the LinkedIn destination is `https://monarcbuild.com/avmarketing/` with the trailing slash.

## Live now (pushed 2026-09-08)

Homepage rebuilt around the two-tier offer. Nine sections: hero ("Predictable high ticket work. Without running top of funnel yourself."), problem ("Being a home integrator is hard."), solution in four steps, benefits, proof (Annapolis: #1, $90K+, $500K+), six-question FAQ, the offer (Level 1 and Level 2 contents, **no dollar amounts by decision**, pilot terms), final CTA, footer with email. Primary CTA "Apply now" to /book. Nav: How it works, The offer, FAQ, Results, About. Title and link-preview text updated; @Higgsfield tag removed. Source: `projects/monarcbuild-site/public_html/index.html`, pushed with `scripts/site_sync.py`.

Not yet changed: /book, /results, /about, /how-it-works, /territories, /permit-intelligence. Footer has no phone yet. `cover.png` (link-preview image) is the old design.

2026-09-09: proof values corrected to Jonathan's figures (see `context/about-business.md`, Proof jobs). Homepage proof paragraph rewritten; tiles now #1 ranking, $70K one search term (Georgian, James Loudspeaker), $91K from $2.5K of ads (waterfront Ketra), $500K+ lifetime. Results page: $110K changed to $70K, $135K changed to $91K; its other three figures ($300K, $250K+, $120K) are unverified and untouched.

2026-09-09: encoding fix. Arrows, middle dots, and the copyright sign were rendering as `â†'`, `Â·`, `Â©` because the server sent no charset and the charset meta sat after the Google tag scripts. Fixed by moving `<meta charset="utf-8">` to the first line of the head and adding `public_html/.htaccess` with `AddDefaultCharset UTF-8`. Every page now serves `Content-Type: text/html; charset=UTF-8`. Keep the charset tag first in any page's head.

Same day, 2026-09-08, home price removed from the proof paragraph (scope only). Requested next (Jonathan's words): turn the project's camera shots into proper hero shots with Higgsfield ("aligned with proper ratios of subject to background by using color contrast, lightness/shading, and sizing proportions"), and put one line under each of three images: "get more wires set during rough-in", "specify more high ticket services", "close more appointments". The camera shots are in the Proton mailbox; see `references/proton-mail-api.md`. First source photo staged at `/assets/georgian/rough-in-01.jpg` (live, unlinked).

Hero candidates rendered with Higgsfield 2026-09-08 from that photo (16:9, ~2.7k wide), saved locally in `assets/georgian/`, not pushed:
- `hero-rough-in-candidate-a.jpg` (gpt_image_2, job 461f8cf8): warm, cinematic, faithful.
- `hero-rough-in-candidate-b.jpg` (gpt_image_2, job e13b0268): moodiest, strongest subject separation, moved a few floor items.
- `hero-rough-in-candidate-nano.jpg` (nano_banana, job 9d8a3f72): most literal, flatter light.
Cost: about 15 credits total. Caption intended under this image: "Get more wires set during rough-in."

Source photos recovered from the Proton inbox 2026-09-08 (self-sent, July 29 and 30), web-sized into the mirror:
- `assets/georgian/exterior-01.jpg`: the Georgian's front elevation, columned portico, brick wings, gravel drive, a man walking to the door, fall light. Proposed line: "Close more appointments."
- `assets/georgian/rough-in-02-original.jpg`: full-resolution original of the rough-in interior. Line: "Get more wires set during rough-in."
- `assets/projects/waterfront-great-room.jpg`: waterfront great room at sunset, wood ceiling with recessed lighting and in-ceiling speakers, glass wall to the dock (matches the "riverside build" on /results). Proposed line: "Specify more high ticket services."
- `assets/projects/farmhouse-build.jpg`: modern farmhouse under construction, cedar siding, standing-seam roof. Spare.
- Also in the inbox: `build-hero_1.zip`, a code project (Python + a React scrub component) that renders a CG Georgian house at night for a scroll-driven hero film. Not photos. Parked.
Library of this home (the Georgian) = exterior plus rough-in, two shots so far.

Added by Jonathan to `projects/outreach/` 2026-09-09 and filed into the mirror (local only): `assets/projects/colonial-rear-deck-01.jpg` (gray stucco rear deck with French doors, "colonial 1", identity unconfirmed), two frames from the Baltimore penthouse night walkthrough video in `assets/projects/` (the $50k Control4 and Lutron retrofit; the video is handheld and vertical, reference only). "colonial 2" was a duplicate of the rough-in shot. Proof values per job are in `context/about-business.md`.

Hero set rendered 2026-09-08 (Higgsfield, gpt_image_2, 16:9, ~2.7k wide), web-sized to 1600px in `assets/hero/`, NOT yet on the live page:
- `hero-rough-in.jpg` (candidate B) → "Get more wires set during rough-in"
- `hero-waterfront.jpg` (variant A; `alt-waterfront-b.jpg` alternate) → "Specify more high ticket services"
- `hero-exterior.jpg` (variant A; `alt-exterior-b.jpg` alternate) → "Close more appointments"
The three-image strip replaces the Searched / Called in 5 minutes / Booked strip under the hero. Built into `_wireframe/page.html` (local only, never pushed) for the handoff render.

Client site wireframe (2026-09-10): the template Monarc builds for an integrator client. Home, one landing page per priority offering (lighting, audio, shades) plus theater and builders, a booking page, and a spec page with the rules (h1/h2/h3 hierarchy, 7th grade outcome copy, recognition only as a risk reducer, 50/50 and thirds ratios, one accent color, 96px section rhythm). Live: https://claude.ai/code/artifact/8861a1b7-b438-49d3-8a5f-7b4627b540b9. Source copy: `projects/wireframes/monarc-integrator-wireframe-2026-09-10.html`. Body copy is lorem ipsum by design; headlines are real.

Design references Jonathan wants the site to learn from: `references/design-references.md` (first entry 2026-09-09, Purple Cherry's profile page for spacing and contrast). Hand it to the designer with the handoff PDF.

Handoff for a designer and an SEO, 2026-09-08: `projects/monarcbuild-site/handoff/2026-09-08-homepage-handoff.pdf` (single page, 1840x4822px: full homepage at 1440px on the left, annotation column on the right with page facts, section map, designer notes, SEO notes). Also `...-handoff.png` and `...-fullpage-1440.png`. Regenerate with the scripts in the session scratchpad (`build_wireframe_page.py`, `build_board.py`, headless Chrome), or ask the AIOS.

## State before the rebuild (read live 2026-09-08, kept as history)

## How the site is built (raw HTML, 2026-09-08)

- Built with **Higgsfield's website builder** (`<meta name="author" content="Higgsfield">`, `<meta name="twitter:site" content="@Higgsfield">`). Served from Hostinger (`platform: hostinger`, `Server: hcdn`).
- Compiled front end: one stylesheet `/assets/styles-Bf3p8a1Y.css` (hashed, Vite-style build), one script `/monarc.js`, React-style markup (`charSet`, `data-precedence`). `public_html` holds build output, not editable source.
- Google Ads tag present: `AW-18358744393`.
- Open Graph title: "Monarc Build: Permit Intelligence for Custom Home Integrators." Description: "One integrator per metro..." These are what a link preview shows in email or LinkedIn.
- Leak to fix: `twitter:site` points at @Higgsfield, not Monarc.
- The /book form has no plain `action`; it submits from the script. Endpoint unknown.

### Corrected after reading the source and the live script (same day)

- Higgsfield project `monarc-build` (id `5df87ff8-e909-49a3-9c5c-41ed10a53c4c`, live at monarc-build.higgsfield.app) is a React / TanStack Start app with a server-side lead function. The AIOS cloned it to `projects/monarcbuild-site/` (gitignored) for reference.
- The site on Hostinger is a **static HTML export** of that app, hand-adapted: the `/book` form posts to `https://formsubmit.co/jonathan@monarcbuild.com` (CC `patrick@monarcbuild.com`, subject "New Monarc Build lead", redirect to `/book/?sent=1`), and `/monarc.js` is a 2KB vanilla scroll script. No React on the live site.
- The two have diverged. **The HTML in Hostinger `public_html` is the live source of truth.** Edit it directly. The Higgsfield repo is history and a parts bin (components, copy), not the deploy path. No Node is needed.
- Pipeline: pull `public_html` to the local mirror, edit, Jonathan approves, push. `scripts/site_sync.py`, credentials per `references/hostinger-api.md`.
- Open: formsubmit.co needs a one-time activation click on the first submission. Whether that happened is unconfirmed. Who patrick@monarcbuild.com is: unconfirmed.

## What the site sells today

- Headline: "We run the pipeline. You run the installs."
- Subhead: "A marketing agency built only for custom home integrators: permits surfaced before the bid, past clients reactivated, builders who keep calling back."
- Model: "The full agency, one retainer," month to month. No prices anywhere.
- Scope: Demand Capture (search, local ads, website), Demand Activation (reengagement, upgrades, service plans), Demand Creation (permit-driven outreach, lunch-and-learns, designer outreach).
- Territories page: "One integrator per metro. That's the product." County-level permit monitoring weekly, EnerGov, reactivation engine, competitors waitlisted. Decorative US map, no availability shown.
- Homepage "signal feed": four permits with builder names (Meridian Custom Homes, Caldwell Homes, Stonebridge Builders, Harlan Estate Group) and values $3.8M to $5.1M. Real or illustrative: unconfirmed.
- Founder line: "Three years inside the industry: selling systems, closing six-figure installs." Credentials: Lutron certified, AIA presentations, CEDIA workshops.
- Nav: How it works, Permit intelligence, Territories, About, Results.

## Mismatches with the current offer (`context/offer.md`, decided 2026-09-07)

| On the site | In the offer |
|---|---|
| Permit intelligence, territory exclusivity, B2B outreach as the product | B2B and permit monitoring scratched (hidden $10k custom engagement only) |
| One retainer, month to month, no price | Level 1 $2,500/mo, Level 2 $4,500/mo, prices printed |
| No pilot | 60 day pilot, no setup fee, $1,000 ad spend match, then 6 month term |
| No First Responder | First Responder is the Level 2 headline feature (5 minute lead response) |
| "Three years inside the industry" | Cold call script says four years |
| Results: $110K Georgian Colonial with James Loudspeaker, no names, no dates | Offer proof: #1 for "whole home audio in Annapolis," $90k+ James Loudspeaker, $8M colonial restoration, $500k+ LTV |
| Results header promises "named and dated" case studies | None are named or dated |
| No phone or email anywhere on the site | Offer page CTA has email, phone, booking link placeholders |

## Booking flow (/book)

- Headline: "Fifteen minutes. Bring nothing."
- A form (Name, Company, Metro, Email, Phone optional, notes), no calendar widget. Promise: "We'll come back within one business day with times." Confirmation: "You'll hear from Jonathan within one business day."
- Where the form submits, and whether submissions arrive, is unconfirmed.
- Gap: a one business day response on the agency's own CTA sits next to a five minute First Responder promise for clients. Google Calendar is connected to the AIOS; a Google Calendar appointment schedule link would make the CTA book instantly.

## Results page (/results)

Five results, all unnamed and undated: The Follow-Up $110K (Georgian Colonial, James Loudspeaker); D2C Pipeline $135K (Ketra and Lutron shading); Lunch-and-Learn $300K (shore project); Cold Call $250K+ (architecture firm LTV); Referral Ask $120K (builder referral). No testimonials.

## Flagship hero, draft from Jonathan (2026-09-08, his words, needs tightening)

> Being a home integrator is hard. The owner is trying to idea generate for marketing, take the sales calls, attend the appointments, and do the installs. Monarc applies pressure to your pipeline.
>
> Apply Now. (CTA)

Note: the CTA is "Apply Now," not "Book a call." That's an application frame (they apply to work with Monarc), which fits the one-integrator-per-metro positioning more than the two-tier offer. Reconcile when the site decision is made.

## Decision (2026-09-08)

The site moves to the two-tier offer. Logged in `decisions/log.md`. New homepage drafted in `projects/monarcbuild-site/public_html/index.html` (nine sections, "Apply now" CTA, prices printed); original archived at `archives/site-2026-09-08-original/`. Not pushed until Jonathan approves.

Still on the old story after the homepage ships: `/territories`, `/permit-intelligence`, `/how-it-works`, `/about`, `/results`. The new homepage nav no longer links to territories or permit intelligence, but the pages remain reachable. `cover.png` (the link-preview image) was made for the old messaging.
