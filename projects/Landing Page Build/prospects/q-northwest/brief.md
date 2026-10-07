# Qnorthwest: the "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom audit. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder, built from `spec.json` by `scripts/prospect_page.py` (logo and three photos in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/q-northwest" --port 8805`, then http://127.0.0.1:8805/
- Renders: `projects/Landing Page Build/renders/2026-10-06/q-northwest-after-*.png` (1440, the first screen at 1536, 390).
- The page it replaces: https://www.qnorthwest.com/residential
- The Loom: https://www.loom.com/share/62f8953c51b949cfbdcabc6ea163c362 (about 3 minutes 43 seconds). Its file and word-timed transcript are in `media/looms/62f8953c-turn-google-landing-pages-into-phone-calls/` (not in git).
- Site reads: `projects/research/q-northwest/` (residential), `q-northwest-home`, `-about`, `-meet`, `-faqs`, `-contact`.

## What he said, and what the page does

| At | His words | On the page |
|---|---|---|
| 0:44 | "The residential section doesn't have the service segmented into individual landing pages." | One service: lighting control. The other six are cards near the foot. |
| 0:59 | "This carousel going on in the hero section... make that a little bit bigger to cover the top of the fold." | The strongest of their three slides (the covered outdoor room with the lit fireplace) fills the hero under a dark scrim. The engine draws one photo, so no carousel. |
| 1:07 | "Lighting control installation in your area." | h1: "Lighting Control Installation in Seattle" (their headquarters, per their About and FAQ pages). |
| 1:14 | "An eyebrow... for residential, or lighting control for homeowners." | Eyebrow: "Lighting control for homeowners". |
| 1:26 | "A little bit of text... one to two sentences." | Two sentences: keypads, scenes, schedules; new construction and remodels. |
| 1:37 | "Big call to action that says book a meeting." | "Book a meeting", one label down the page, opens the four-step form (first name, email, phone, message). |
| 1:43 | "A little bar... your review count... the gold stars." | Left out: their site shows no rating. Needs their Google count. |
| 1:53 | "Services specific to lighting controls... keypads, automation, control it with your voice, very customizable." | Four cards with icons: Keypads, Automation, Voice and app, Customizable. |
| 2:11 | "About us... picture of the owner, picture of the team... how long they've been in service, what they specialize in." | Team photo from their About page; "since 2011" and "more than 30 of our people know Lutron's systems", both their words. |
| 2:45 | "Below that, I'd have a reviews section." | Three marked empty boxes: no reviews on their site. |
| 2:47 | "If you're targeting architects, designers, and builders... a section that speaks directly to that ICP." | Process band, eyebrow "For architects, designers, and builders", four numbered stages from their own new-construction and FAQ copy. No button. |
| 2:55 | "Then below that an FAQ, just stuff for like kinda SEO." | Five questions on lighting control, answered from their FAQ and residential page. |
| 2:59 | "Your secondary services... a landing page for [each] and then you could hyperlink those." | Six cards: home control, audio, shades, media rooms and theater, security, network. Each links to /residential, as no page of their own exists yet. |
| 3:11 | "The Lutron diamond dealer credential... the footer of the page." | Footer only: "Lutron Diamond Dealer." Nowhere else. |
| 3:18 | "New construction and remodel that can be baked into the copy." | In the hero line, the first two FAQ answers, and the process stages. |
| 3:24 | "If this is an actual project here, this is a very nice looking monochrome... speaks directly to the architect and designer." | That photo (the dark modern home at dusk behind their contact band) sits behind the process band. |

A closing band, "Tell us about your home", ends the page with the same button.

## Where every fact came from

- Logo, phone (866.444.1224), faces (Montserrat, Poppins), header slate `#2F4858`: their site, read 2026-10-06. The logo is their white lockup recolored to that slate, because the engine's header is white.
- Seattle, the Pacific Northwest, and the Bay Area: their About page ("Residential: Serving the larger Pacific Northwest and San Francisco Bay areas") and FAQ ("We are based in Seattle, Washington").
- "Since 2011": the Meet the Team page (Peter Schuldt: "In 2011, I became the first Qnorthwest employee"). No founding year is printed on their site.
- "More than 30 of our people": their FAQ. Lutron systems named (HomeWorks QSX, RadioRA 3, Ketra), Vantage, Crestron, Control4, LiteTouch: the residential page.
- Line voltage and low voltage electricians: their FAQ. No license number is on their site.
- The process photo: file `image-asset.jpeg`, not marked stock. Not confirmed as their own project.
- The form sends nothing. It is a render.

## Big misses the page cannot fix without them

1. **No real project photos in the hero.** All three carousel slides are iStock photos (the file names say so). The hero uses the strongest one for now. Five photos of their own lit rooms would carry the page.
2. **No reviews and no rating anywhere on their site.** The bar under the button and the three review boxes stay empty until we have their Google profile.
3. **No page per service.** The six secondary cards all point at one long page. Each needs its own page, built like this one, to be worth a Google click.
