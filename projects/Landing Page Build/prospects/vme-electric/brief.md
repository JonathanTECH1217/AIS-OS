# VME Electrical Contractor Inc.: the "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom review. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder, built by `scripts/prospect_page.py` from `spec.json` (their logo and six of their photos in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/vme-electric" --port 8792`, then http://127.0.0.1:8792/
- Rebuild after a spec edit: `python scripts/prospect_page.py all vme-electric`
- Renders: `projects/Landing Page Build/renders/2026-10-06/vme-electric-after-*.png` (1440, the first screen at 1536, 390).
- The page it replaces: https://vmeelectric.com/light-installations---vme-electrical-contractor-inc (a photo carousel under the words "Light Installations", nothing else).
- The Loom: https://www.loom.com/share/eab52faaef804c438e0858c2c315569d (5 minutes 52 seconds). Its file and word-timed transcript are in `media/looms/eab52faa-landing-page-redesign-for-lighting-installation/` (not in git).
- The company: Victor Mendoza runs it (their footer: Victor@vmeelectric.com). Office 631-953-5293, Office@vmeelectric.com; an emergency line, 631-316-2071. Shop at 1 Liano Drive, Wainscott, NY 11975; mail to PO Box 4164, East Hampton, NY 11937. Instagram vme_electrical_contractor_inc. The CRM row was not looked up for this render.

## What he said, and what the page does

Times are from the Loom. His words are from the laptop's transcript.

| At | His words | On the page |
|---|---|---|
| 0:31 | "Segmenting your services by landing page... you have a service landing page for lighting installation." | One service: lighting control. This page replaces their Light Installations page. |
| 0:44 | "Putting your logo over on the left side and then having just a menu of options... And then CTA on the right side is fine. We're gonna reduce the size of this header to about 70 pixels." | Logo left, phone and one "Book a meeting" button right. No menu: one page, one thing to do. The bar is the engine's 80 px. |
| 1:08 | "These photo carousels... I like this one with the cove lighting and the pendants and that's just a very unique photo. So we're going to make this the background photo... with a dark overlay with white text." | The photo on his screen at that second (carousel photo 2: the dark ceiling tray, the pendant cluster, the cove on the wall) under a dark scrim, white words. |
| 1:29 | "Using this orange that just pops as the primary call to action." | Their own button orange, #E37235, on every button, the four card grounds, and the icons. |
| 1:40 | "Transform it from something weak like lighting installations to something strong that targets the transactional offering... and the service area... Lighting control installation in X area." | h1: "Lighting Control Installation in the Hamptons". Their own line is "from Montauk to Southampton"; "the Hamptons" is the buyer's word for it. His to change to "East Hampton". |
| 1:57 | "An eyebrow right above that that speaks directly to the prospect you're trying to sell to." | Eyebrow: "For homeowners from Montauk to Southampton". |
| 2:05 | "A few lines of copy right below that that are going to say, in simple words, exactly the outcome that the prospect currently wants." | Two sentences: every light from one keypad, a schedule, or a phone; designed, wired, and programmed by their own electricians, new build or finished home. |
| 2:15 | "The book a meeting or book an appointment button right below that in that high contrast orange." | One orange "Book a meeting" button: top bar, hero, and the close. |
| 2:18 | "A four-stage booking form first name, email, phone number, and a brief message that when it gets submitted takes them to a booking calendar link." | The button opens the engine's four-step form (first name, phone, email, message; he said email before phone, see Not done). It ends on "Pick a time" with no calendar behind it: they have none to link to yet. |
| 2:31 | "This would disqualify people that are just looking for things like TV mounts." | Nothing but lighting control on the page. TV installation is left off the secondary services on purpose. |
| 2:47 | "The services section speaking about the outcomes directly related to the offering... keypad customizations, the engravings, the controlled color temperature, as well as form factor. If you wanted to do recessed, pendants and sconces, there's retrofit applications." | Four orange cards with icons: Engraved keypads, Color temperature, Recessed, pendants, sconces, Retrofit. His four points, one card each. |
| 3:09 | "An about section right there that has a photo of you or your team just with a little bit of stuff about the company." | About: two of their own crew on a scaffold hanging a pendant cluster (carousel photo 4), two sentences cut from their home page. |
| 3:21 | "Right below that call to action, just sticking a Google reviews icon there." | Not on the page. Their site shows no Google rating and the Google pull waits on his go. The engine draws the stars line under the hero button once `hero.trust` holds a real number. |
| 3:34 | "A portfolio section right there and this is gonna be like three shots of just your best work." | Three of their carousel photos: the dining room chandelier, the stair with the lit edge, the game room pendant. |
| 3:40 | "Our process showing everything from design consultation to the installation and ongoing service... helps the B2B prospect understand." | "For architects, builders, and designers": four numbered stages, design consultation, lighting plan, installation, ongoing service. The octagon cove room (carousel photo 1) behind it. |
| 3:58 | "A review section with three cards that just say in the best words that people who have had your service repeat back... get rid of any fears about timelines or quality of the installation." | The three reviews from their home page, last names cut: William M., David, Robert C. All three speak to timing and the crew. None names lighting (see the misses). |
| 4:28 | "A secondary services offering, hyperlink map... a grid of three to six cards that hyperlink to high-ticket offerings, your dedicated media, your distributed media." | Six cards, each a link to one of their own pages: landscape lighting, outdoor audio (Coastal Source), whole-home control (AVA), new construction, renovations, pool electrical. |
| 5:11 | "A secondary call to action right below that... say this in different wording as well, just to hit a different part of their head." | The close: "Tell us about the house", a different ask in different words, the same button. |
| 5:24 | "Here is the finished product... Use this as inspiration if you want to." | This render. |

He named no FAQ in this Loom. A five-question FAQ is written in `spec.json` and left off the page; put `"faq"` before `"final"` in `order` to show it. No background pattern is set (he has not said which color is A, B, or C), so the page keeps the PHA look.

## Where every fact came from

- Company name, phones, both addresses, Victor's name and email, the Instagram handle, the about words, the three reviews, the secondary service pages and their one-liners, the fonts (Roboto Slab and Roboto, both Google), the orange (#E37235, the header and footer "Book Online" button), and the credentials in the footer (licensed and insured, Lutron Pro Installer, Coastal Source dealer and installer, AVA Remote Pro Installer): their public site, read 2026-10-06 (`projects/research/vme-electric/` and `vme-electric-home/`). The site is built on Durable and renders from a `__NEXT_DATA__` JSON, so `site.json` shows 7 words for the service page; the JSON in `site.html` was read by hand.
- The six photos: their Light Installations carousel, their own uploads on cdn.durable.co. None is marked AI-made. The Unsplash and Shutterstock pictures on their home page were skipped.
- The logo in the top bar: their own PNG (`assets/logo-original.png`) is made for a dark site, an orange mark with the name in white inside it, and at 46 px the name is 5 px tall. The bar shows the name alone, cut from that PNG, recolored from white to their ink (#131313) and set on two lines (`assets/logo.png`, `logo_height` 38 in the spec). The mark alone is `assets/logo-mark.png`. Nothing was redrawn. A mark-and-name lockup overflows the engine's phone bar, so the mark is off the page for now.
- Headings use the engine's light serif (the buyer is a high-end Hamptons homeowner); the eyebrow, buttons, and names use their Roboto Slab.
- The card lines, the process steps, the sub, and the FAQ answers: his words in the Loom and plain facts about lighting control. Nothing claims a brand of gear, a year founded, a job count, or a rating.
- "The Hamptons" in the headline is the AIOS's reading of "from Montauk to Southampton". The site never uses the word.
- Their "Electrical Emergency" phone button and the top menu are off on purpose: not about the one service.
- The form sends nothing. It is a render.

## Big misses the AIOS would raise (his to take or leave)

1. **No Google rating and no lighting review.** Their site shows three reviews with no star count, and none is about lighting. He asked for a Google reviews icon under the hero button; it needs a real rating (the Google profile pull, about 4 cents, waits on his go) and two reviews from lighting clients to carry the page.
2. **No photo of a Hamptons home.** The hero and the process band are a restaurant and a sunroom; the portfolio is three interiors with no house around them. For a luxury homeowner, one of their houses lit at dusk from the street would carry more than all three. Ask Victor for five photos of residential jobs, outside at dusk and in.
3. **No calendar.** The form ends on "Pick a time" with nowhere to go. Until they share a booking link, a lead waits for a call, and a lead that waits goes cold.

## Not done

- The form's steps come in the engine's order (first name, phone, email, message). He said email before phone in this Loom; that is a change to `scripts/prospect_page.py`, not to the spec.
- The header is the engine's 80 px; he said about 70.
- The Google reviews icon as a mark (a "G"): the engine draws stars and words, no logo.
- The Loom B and A cut and the email to Victor.
- The CRM row match.
