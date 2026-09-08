# monarcbuild.com

Update this page when the site changes.

## Live now (pushed 2026-09-08)

Homepage rebuilt around the two-tier offer. Nine sections: hero ("Predictable high ticket work. Without running top of funnel yourself."), problem ("Being a home integrator is hard."), solution in four steps, benefits, proof (Annapolis: #1, $90K+, $500K+), six-question FAQ, the offer (Level 1 and Level 2 contents, **no dollar amounts by decision**, pilot terms), final CTA, footer with email. Primary CTA "Apply now" to /book. Nav: How it works, The offer, FAQ, Results, About. Title and link-preview text updated; @Higgsfield tag removed. Source: `projects/monarcbuild-site/public_html/index.html`, pushed with `scripts/site_sync.py`.

Not yet changed: /book, /results, /about, /how-it-works, /territories, /permit-intelligence. Footer has no phone yet. `cover.png` (link-preview image) is the old design.

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

Hero set rendered 2026-09-08 (Higgsfield, gpt_image_2, 16:9, ~2.7k wide), web-sized to 1600px in `assets/hero/`, NOT yet on the live page:
- `hero-rough-in.jpg` (candidate B) → "Get more wires set during rough-in"
- `hero-waterfront.jpg` (variant A; `alt-waterfront-b.jpg` alternate) → "Specify more high ticket services"
- `hero-exterior.jpg` (variant A; `alt-exterior-b.jpg` alternate) → "Close more appointments"
The three-image strip replaces the Searched / Called in 5 minutes / Booked strip under the hero. Built into `_wireframe/page.html` (local only, never pushed) for the handoff render.

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
