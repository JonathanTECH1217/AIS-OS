# Fusion Tech Companies: the "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom review of their home page. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder, built by `scripts/prospect_page.py` from `spec.json` (their logo and four photos in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/fusion-tech" --port 8794`, then http://127.0.0.1:8794/
- Renders: `projects/Landing Page Build/renders/2026-10-06/fusion-tech-after-1440.png`, `-fold-1536.png`, `-390.png`.
- The site he reviewed: https://fusiontechcompanies.com (the home page; they have no lighting control page). Brentwood, MO, 314-395-8888.
- The Loom: https://www.loom.com/share/ea3b44a355c742e8ad842211b82ee3e4 (4 minutes 18 seconds). Its file and word-timed transcript are in `media/looms/ea3b44a3-boost-conversions-with-service-landing-pages/` (not in git).
- The owners on their About page: Kevin Boone (electrical), Joe Mclafferty (media), Cindy Willhoyt (operations). No pictures of them on the site. CRM row not looked up.

## What he said, and what the page does

Times are from the Loom. His words are from the laptop's transcript.

| At | His words | On the page |
|---|---|---|
| 0:29 | "Have a page, landing page per offering that you guys have. So your distributed audio, your lighting control and your dedicated home theaters." | One page, one service: lighting control. The other offerings are link cards near the foot. |
| 0:51 | "Let's just say lighting control. It's one of the highest ticket items that you have to offer." | The service on the page. |
| 0:58 | "A shot of an inside space or outside space that shows a high-end home, and then make that a dark overlay on that stock photo. Add a big headline right in the center of the page that says something like lighting control installation in the area you're trying to target." | Hero: the staircase and chandelier photo their About page shows as previous work, under a dark scrim. h1 "Lighting Control Installation in St. Louis", centered, white, light serif. |
| 1:22 | "The eyebrow is just going to be something that speaks directly to the prospect... lighting control for residential... lighting control for homeowners also works." | Eyebrow: "Lighting control for homeowners", in the logo's cyan. |
| 1:31 | "A few lines of copy right below the headline that speak directly to the outcomes, like circadian rhythm, reducing stress, customized engravings on keypads, controlled color temperature." | Two sentences: light that follows the sun, engraved keypads, a color temperature set once, less to think about. |
| 1:48 | "Big book a meeting button that gets a four-stage form, which is first name, email, phone number, and brief message. This is just going to help you disqualify the people that are doing TV mounts." | One "Book a meeting" button, top bar, hero, and the close. It opens the four-step form, one question a screen. The engine's order is first name, phone, email, message; he said email before phone here. |
| 2:00 | "Link directly to your Google Calendar, and this is going to notify you by email exactly when somebody submits a form." | The form ends on a marked calendar box. They have no booking calendar to link to yet. The form sends nothing; it is a render. |
| 2:12 | "The services that are included speaking directly to the outcomes the prospect wants to feel... reduced stress, the customizability, the ability to change the color temperature. Keep it between three to six per offering." | Four cards with icons on the logo's dark blue: Follows the sun, Engraved keypads, Color temperature, Less to think about. |
| 2:41 | "An about section, that's going to just have a photo of either you or your team, and then a little bit about you and your company and what you stand for." | About: their own About page words cut to two sentences. The photo box is marked empty; the site has no owner or team photo. |
| 2:46 | "Portfolio section. This is just a few things that you guys have installed, taken a photo of. Ideally the best photos you have." | Three photos in a three-across grid: the theater, the kitchen, the bedroom, all from their site. |
| 3:03 | "Our process. This speaks directly to the B2B partners, the trade guys, your builders, architects, and designers... everything from design consultation all the way to installation and ongoing service." | Four numbered stages on black, no button: Design consultation, System design and drawings, Installation, Ongoing service. Cut from the five phases on their About page. |
| 3:17 | "Internal linking to other offerings you guys have because somebody that wants lighting control might want distributed audio." | Six link cards: Distributed audio, Dedicated home theater, Motorized shades, Smart home control, Security and cameras, Whole home generators. All six link to their Home Spaces page, the only page that holds them. |
| 3:31 | "FAQ, this just helps with SEO. Not overly complicated stuff." | Five plain questions on lighting control, one-line answers. Nothing company-specific in them. |
| 3:35 | "A secondary call to action that just goes straight back to that four-stage booking form." | The closing band: "Ready to plan the lighting?" and the same button, the same form. |
| 3:46 | "Maybe a small review section, just three cards. Right around in one of those areas." | Three reviews from their home page, first name and last initial, placed just before the closing ask. |

## Where every fact came from

- Logo, cyan (`#0EB9DF`) and dark blue (`#025399`), faces (Barlow Semi Condensed, Montserrat), phone, address, "Serving the Greater St. Louis area", "over 25 years of combined experience", "Union Local 1" technicians, the five-phase process, the list of offerings, the six testimonials, and the footer logos (BBB Accredited Business, IBEW, Lutron, CEDIA, CE Pro): their public site, read 2026-10-06 (`projects/research/fusion-tech*/site.json`).
- The dark blue carries the buttons, icons, and card grounds because white words on the cyan fail contrast. The cyan is the accent (hero eyebrow, process numbers). His call if he wants it the other way.
- Headings are the engine's light serif (Newsreader): his rule for high-end residential.
- The photos: the hero and the three work photos are pictures their site shows ("Get inspired by some of our previous work in these beautiful homes"). The kitchen is the right side of their home hero, cropped past the logo overlay. Two pictures on their site are named as ChatGPT images and one is an Unsplash stock photo; none of those were used.
- The reviews: Renee and Andrew B. (names lighting control), Jeff B. (St. Louis, two decades), Ashley F. (motorized shades). Cut to whole sentences. Their site shows full names; the page does not.
- The card lines and the FAQ: plain lighting control facts, nothing tied to the company.
- Not used: the "20+ years" counter on their home page (the About page's "25 years combined" is the line kept), the "922 completed media jobs" counter, and any Google rating (none on the site). No price anywhere.
- The form sends nothing. It is a render.

## Big misses the AIOS would raise (his to take or leave)

1. **No photos of their own work.** The four photos are their site's header pictures and read as stock. No owner or team photo. For a high-ticket lighting job the proof is real rooms they lit. Ask for five job photos and one team photo before anyone outside sees the page.
2. **No page per offering.** All six "everything else" cards land on one Home Spaces page, and their own site still links lighting and audio to another domain (fusion-companies.com). His first point in the Loom was a page per offering; the links need somewhere to go.
3. **No calendar and no Google proof.** The form ends on an empty calendar box, so a lead waits for a call back. The site has no Google rating or reviews, so the hero has no trust line and the three reviews are the site's own testimonials.

## Not done

- The Loom B and A cut and the email to the owners.
- The CRM link (company row not looked up).
- Their own photos in place of the header pictures, once they send them.
