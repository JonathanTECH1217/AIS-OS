# Innovative Outdoor Lighting and Audio: the "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom audit. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder, built by `scripts/prospect_page.py` from `spec.json` (their logo and two photos in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/io-lighting" --port 8802`, then http://127.0.0.1:8802/
- Rebuild after a spec edit: `python scripts/prospect_page.py all io-lighting`
- Renders: `projects/Landing Page Build/renders/2026-10-06/io-lighting-after-1440.png`, `-fold-1536.png`, `-390.png`.
- The page it replaces: https://io-lightingandaudio.com/copy-of-holiday-event-lifghting (their "Custom Lighting Design" page).
- The Loom: https://www.loom.com/share/6b2cdd19f09945af8381b03f1445d8ee (3 minutes 20 seconds; the first seconds are cut off). Its file and word-timed transcript are in `media/looms/6b2cdd19-rebuild-your-outdoor-lighting-landing-page/` (not in git).
- The company: Palm Desert, CA (74170 CA-111, Suite 3), (760) 880-2722. The owner is Sabrina (their Our Story page; sabrina@io-lightingandaudio.com is on their home page). Wix site.

## What he said, and what the page does

Times are from the Loom. His words are from the laptop's transcript.

| At | His words | On the page |
|---|---|---|
| 0:22 | "The headline's running a little bit large up to the top fold in terms of a ratio. So we'd make that about 70 pixels." | h1 at 72px (the engine's serif size), two lines, centered, the button above the fold at 1536x780. |
| 0:31 | "Change the headline from custom lighting design to... outdoor lighting design... in the area you're trying to target." | h1: "Outdoor Lighting Design in Palm Desert" |
| 0:44 | "Right above that, you'd put an eyebrow that would target the person if it's residential or commercial... I'm gonna guess you're trying to target residential here." | Eyebrow: "For homeowners across the Coachella Valley" (their Our Story page names the valley). |
| 0:59 | "One or two sentences of copy talking about what you have available as far as color temperature, form factors, and the process that your team does to get this design to happen." | Two sentences under the headline: the fixture types, warm white, cool white, or full color, then design, night-time demo, installation. |
| 1:11 | "A call to action button that would say something like book a meeting, book an appointment." | One button, "Book a meeting", in the top bar, the hero, and the close. It opens the four-step form: first name, email, phone, message. |
| 1:23 | "This blue theme here you're trying to do might be a good primary color, can be professional." | Their blue (#116DFF) on the button, the cards, the icons, and the form. |
| 1:30 | "Increase the contrast between the text and the background. This light's running a little bit bright here." | White words on a dark photo of their own work under a dark scrim; black words on white and pale blue below. |
| 1:36 | "A breakdown of the services section... the different form factors, the different color temperatures... step lights, pathways, driveways." | Four cards with icons: Pathways, Steps and decks, Driveways and entries, Color temperature. Each names the fixtures it uses. |
| 1:57 | "An about section... a picture of you or the team, and then a bit of copy." | About, cut from their Our Story page to two sentences. The photo box is marked empty: their site has no photo of Sabrina or the team. |
| 2:18 | "A reviews section to increase trust." | The reviews band, three boxes marked empty: their site shows no reviews and states no rating. |
| 2:22 | "A section that speaks directly to the commercial partners: your architect, builder, and designer, showing the process from design to installation." | "Our process, design to installation", eyebrow "For architects, builders, and designers", four numbered steps from their Why Choose Us page, on the photo from the audited page. No button in it. |
| 2:33 | "An FAQ just for SEO purposes when people are asking questions." | Five questions on outdoor lighting design, one-line answers. |
| 2:40 | "Secondary services below that, your network, your outdoor audio, distributed media... indoor residential lighting control... three to six... all hyperlinked to individual landing pages." | Six cards, each linked to the page their own menu links to: outdoor audio and entertainment, security lighting, holiday and event lighting, professional installation, maintenance program, repairs. Networking, distributed media, and indoor lighting control are not on their site, so they are not on the page. |
| 3:04 | "A secondary call to action below that would be a great idea." | The close: "Book a meeting with our design team", the same button. |

## Where every fact came from

- Name, logo, blue, phone, address, "Coachella Valley", "Southern California", Sabrina's story, the process (site visit, custom layout, complimentary night-time demo, installation), "replace a few fixtures", LED, "made in the USA", "resale wholesale design center": their public site, read 2026-10-06 (`projects/research/io-lighting*/site.json`).
- The hero photo: their gallery (a lit home with uplit palms). The process band photo: the picture on the audited page. The logo: the site's own PNG. Nothing AI-made, nothing stock (the one stock image on their home page was left alone).
- The fixture types on the cards (path lights, step lights, strip lighting, well lights, wall washers, up lights): their Landscape Lighting menu.
- Color temperature lines and the FAQ answers are plain facts about outdoor lighting, not claims about the company. No Kelvin numbers: their site lists none.
- The six secondary hrefs: their Wix menu's own links. The slugs do not match the names (the audio page lives at `/copy-of-security-lighting`); each href here is the one the menu uses, checked by reading the audio page.
- Fonts: their faces (Avenir, DIN Next, Proxima Nova) are not Google fonts, so Manrope and Poppins stand in, with the engine's light serif for headings (high-end residential).
- No rating, no year founded, no job count, no awards: none are on their site. The form sends nothing. It is a render.

## Big misses the AIOS would raise (his to take or leave)

1. **No reviews anywhere on their site, and no rating line.** The reviews band is three empty boxes right where trust is needed. Pull their Google reviews (first name, last initial) before anyone outside sees the page; a Google profile pull is about 4 cents.
2. **No photo of Sabrina or the team.** The about box is empty. Their story is the best thing on their site and a face would carry it. Ask for one photo of her, or of the crew with a van.
3. **The secondary services he named are not what they sell.** He guessed networking, distributed media, and indoor lighting control from the picture. Their site is outdoor lighting, outdoor audio, holiday lighting, and a fixture store. The page uses their six real pages; if they do offer the other three, each needs its own page first.

## Not done

- The second Loom (him going through the page) and the cut.
- The email to Sabrina.
- The 390 render was made but not checked by eye.
