# TruDefinition: the "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom audit. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder, built by `scripts/prospect_page.py` from `spec.json` (their logo in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/tru-definition" --port 8796`, then http://127.0.0.1:8796/
- Rebuild and re-render: `python scripts/prospect_page.py all tru-definition`
- Renders: `projects/Landing Page Build/renders/2026-10-06/tru-definition-after-1440.png`, `-fold-1536.png`, `-390.png`.
- The page it replaces: https://www.trudefinition.com/services/lighting-control
- The Loom: https://www.loom.com/share/86afd9c475584fe6a1fe40d59a7f6932 (6 minutes 23 seconds). Its file and word-timed transcript are in `media/looms/86afd9c4-boost-your-low-voltage-landing-page-conversions/` (not in git).
- The people: he opens "Hey Tommy" and closes with "Tommy or Chris or Ben". None of the three is named on the site, so no name is on the page.

## What he said, and what the page does

Times are from the Loom. His words are from the laptop's transcript.

| At | His words | On the page |
|---|---|---|
| 0:36 | "You guys have segmented your offerings by a service for a landing page. So let's start with lighting control here." | One service: lighting control. Everything else they do is a card near the foot. |
| 1:16 | "I like the choice of the Serif Style font." | Serif headings. The engine draws Newsreader (light); their Playfair Display is not an option in it (see Not done). |
| 1:19 | "Your primary color being the gold kind of goes against your branding. So I'm going to stay true to your branding being that darker blue, and putting high contrast white text on those cards." | Their navy (`#0C1A2E`, from their site CSS) is the one page color: both buttons, the four cards, the icons, the close band. White words on the cards. The gold is off the page. |
| 1:36 | "Lighting control in Dallas Fort Worth. Great headline. I want all of this text to be centered." | h1: "Lighting Control in Dallas Fort Worth", centered, with the sub and the button under it. |
| 1:41 | "An eyebrow right above that headline that targets directly to your prospect... lighting design for residential." | Eyebrow: "Lighting design for residential". |
| 1:57 | "High contrast text to a white background with dark text... the overlay on the background... that white overlay, black text." | `"light": true` in the hero: the engine draws a pale scrim and dark words. With no photo under it (next row), the hero is plain white with black words. |
| 2:11 | "It shouldn't be a stock image, it should be a really good photo from you guys, architectural shot." | No photo. Every picture on their site is AI-made or a vendor's stock (below), so none went on. The hero waits for one of theirs. |
| 2:15 | "A big dark blue primary color call to action saying book a meeting that takes you directly to a four-stage booking form. First name, email, phone number, and a brief message." | One navy "Book a meeting" button, three times (top bar, hero, close). It opens the engine's four-step form: first name, phone, email, message (his order here was first name, email, phone, message; the engine's order is fixed). The form sends nothing. |
| 2:41 | "Right below that, a services part... keypad customization with your lighting scenes, the control automation, security benefits, tunability with your Kelvin temperature... cards in your primary color... brief descriptions of each." | Four navy cards with icons: Keypads and scenes, Control and automation, Security lighting, Tunable color temperature. Each line is cut from their lighting page. |
| 3:06 | "A section that says a little bit about your company, accompanied by a photo of either the owner or the team. You could do leadership as well." | About: "A small team. Real names." and two sentences from their about and home pages. The photo is a marked empty box: the site has no photo of the owner, the team, or leadership. |
| 3:22 | "Right below the call to action... Google reviews. So a star banner with the number of reviews and the star rating." | Not drawn. Their site states no rating ("no public star-rating total is claimed without a corresponding public source"). Nothing is invented. |
| 3:33 | "Right below the About Us section, our process. This speaks directly to the builder, architect, and designer... from design consultation to the installation and then ongoing service." | "Our process" under the eyebrow "For builders, architects, and designers": four numbered steps, folded from the six on their /our-process page. No button in this band (his PHA rule). |
| 3:58 | "A portfolio section. You should have three shots of architectural stuff... a three-quarter shot of a keypad... recessed small aperture lights running down a great room... a decorative fixture, wall sconce or pendant." | "Our work": three marked empty boxes. His three shots are the ask list (Big misses, 1). |
| 4:26 | "Another three card review slot. The best reviews you guys have that relate to this offering or your team." | Three reviews from their /reviews page: lighting control (Plano), a new build with the builder (Prosper), the whole house and the team (Highland Park). The site withholds names, so each carries the label the site shows (buyer and community). |
| 4:37 | "A secondary services page... your distributed audio, your dedicated home theater... the talent of your team... a brief description of the talent." | "Everything else we install": six cards that link to their real pages (whole-home audio, home theaters, motorized shades, home automation, home networking) and "The team" with their own talent line. |
| 4:56 | "Below that would just be a secondary call to action." | The close: "Let's talk about your home." with the button. |
| 5:06 | "A lot of this looks like stock media. A lot of it looks like it was generated using AI." | None of their pictures is on the page. |
| 5:21 | "These text chats... adds to the confusion. The dark and light mode is just not doing anything for conversion." | No chat widget, no theme switch, no top menu. One page, one thing to do. |
| 5:36 | "These websites have one job and it's just to get consultations on your calendar." | One button, one form. There is no calendar of theirs to end on yet (Big misses, 3). |

## Where every fact came from

- Their public site, read free on 2026-10-06 (`projects/research/tru-definition*/site.json`, nine pages: the lighting page, home, about, our-process, contact, services, areas-served, reviews, builder-partnerships).
- Logo: `logo-dark.png` from their site, trimmed. Navy `#0C1A2E` and slate `#2A3547`: their CSS. Fonts: their Google Fonts link loads Montserrat (used), Playfair Display, Cormorant Garamond, and Allura.
- Phone (817) 965-1042 and "Dallas-Fort Worth Metroplex": the contact page. No street address is anywhere on the site, so none is on the page.
- Areas: their area pages (Fort Worth, Southlake, Westlake, Highland Park) and the services page ("Fort Worth and Southlake to the Park Cities and Frisco").
- The four card lines: the lighting page ("engraved scenes", "Security Lighting Automation", "Landscape & Exterior Lighting", "You pull into the drive. The house knows you're home.", "Morning light at breakfast. Candleglow at dinner. The same fixture, all day long.", "Light that wakes you gently and lets you sleep when the day is done.", "manual, scheduled or daylight-driven", "app access and useful manual controls") and the about page ("Keypads land where the eye expects them").
- About: the home page ("designs and installs integrated technology for new construction, renovations, and existing homes") and the about page ("Small Team. Real Names.", "You work directly with the people who design and install your system", "Forty-plus years of combined experience informs the questions we ask").
- Process: their /our-process page, six stages folded into four in their words.
- Reviews: their /reviews page, word for word, except two em dashes inside the quotes became a colon and commas.
- Service card lines: the one-liners on their /services page. The team card: "Design, engineering, and support under one roof." (/services) and the forty-plus years (/about).
- The close: "A real person replies within one business day." (/contact); "Let's Talk About Your Home." (/about).
- Footer credentials: the about page (Savant Authorized Dealer, CEDIA Member, 40+ Years Combined).
- Their Google listing, for the reviews pull later: https://g.page/TruDefAV?share (linked from their contact page). Not pulled; no money spent.
- The pictures looked at and left off: `luxury-dfw-living-room-hero.png` and `hero-light.png` (the same AI living room twice), `philosophy-light.png` (AI exterior), `system-light.png` (AI theater), `how-we-work-light.png` (Savant's own tablet marketing shot), `About us cant be done image.png` (stock couple over blueprints), `About us CTA.png` (empty AI wall), `savant-lighting-systems-light.png` and `circadian-rhythm-lighting-light.png` (one vendor room shot twice), `tunable-led-lighting-light.png` (vendor stock), `services-cta-light.png` (a Texas dot map), `service-areas-dallas-skyline-light.png` (AI by its name).

## Big misses the AIOS would raise (his to take or leave)

1. **No photo of their own work anywhere on their site.** The hero is white, the about box is empty, and the three portfolio boxes are empty, because every picture they publish is AI-made or a vendor's stock. For a high-ticket home job that is the proof a buyer looks for. Ask for five: one architectural shot of a finished room for the hero, a keypad three-quarter, small-aperture recessed lights down a great room, a sconce or pendant, and the team. Their Instagram (instagram.com/trudefinition) may already hold them; the Instagram pull is not wired.
2. **No Google rating, review count, or named reviewer.** The star banner he wants under the button cannot be drawn: the site states no rating. The three reviews shown carry no names because the site withholds them, so his first-name-and-last-initial rule is not met. Pull the Google listing (g.page/TruDefAV) once a pull is approved; about 4 cents.
3. **No calendar behind the form.** The button opens the form and ends on a promise of a reply, not a booking. Their own contact page promises a reply within one business day; he wants the meeting on the calendar. Until they have a booking link, a lead that waits goes cold.

## Not done

- The serif he liked is their Playfair Display; the engine's serif setting draws Newsreader (a lighter serif) and has no face switch for titles. Changing that means a script edit, which this build did not touch.
- The form's step order in the engine is first name, phone, email, message. He said first name, email, phone, message on this Loom.
- No `pattern` block: his A B A C A B A background colors are not settled, so the page keeps the PHA look (white, grey, black bands).
- The engine's HTML comment on line 8 of `index.html` names `scripts/prospect_page.py`, so the word "prospect" is in the source; nothing on the page says it.
- The second Loom (him going through this page and the form) and the email to Tommy, Chris, or Ben.
