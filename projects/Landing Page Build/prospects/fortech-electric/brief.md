# For-Tech Electric: the "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom audit. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder, built from `spec.json` by `scripts/prospect_page.py` (their logo and three of their photos in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/fortech-electric" --port 8806`, then http://127.0.0.1:8806/
- Renders: `projects/Landing Page Build/renders/2026-10-06/fortech-electric-after-*.png` (1440, 390, the first screen at 1536).
- The page it replaces: https://fortechelectric.com/home-automation/ (they have no lighting control page, so this is the home automation page).
- The Loom: https://www.loom.com/share/4aaccade87a24ebbbc9cd6ee238fe5be (about 4 minutes 40 seconds). File and word-timed transcript in `media/looms/4aaccade-landing-page-redesign-for-smart-homes/` (not in git).

## What he said, and what the page does

| At | His words | On the page |
|---|---|---|
| 1:01 | "The copy's running a little bit long. It's leaning a little bit left... center the headline." | Hero centered. The page is about 600 words; theirs is about 1,550. |
| 1:08 | "Add a little bit of an eyebrow... Home automation for residential." | Eyebrow: "Home automation for residential" |
| 1:18 | "Home automation installation for New Jersey homes... stick that in the middle. Make it 20% bigger." | h1: "Home Automation Installation for New Jersey Homes", 72px, centered. |
| 1:24 | "This is residential targeting... a little bit more of an elegant... serif style font." | Headings in a light serif (Newsreader). Body in Poppins, buttons in Kumbh Sans (their own Google font). |
| 1:36 | "Transform your home into a smarter... I think you can cut everything after that." | Sub is their first sentence, word for word, cut before "from For-Tech Electric". The two paragraphs after it are gone. |
| 1:48 | "Change get a quote to book an appointment, book a consultation." | One button, "Book a consultation", everywhere on the page. It opens a four-step form: first name, email, phone, message. |
| 1:55 | "This image in the background feels a bit stock, so we would change that out." | Their own photo of a lit home at night, from their portfolio (New Construction), under a dark scrim. |
| 2:02 | "Smart home systems we install, these icons feel a little bit commercial... the parts of the home automation that you get... security, control of lighting, climate... AV media distribution... pick and choose." | Four red cards with icons under "Pick the parts of home automation you want": Added security, Lighting control, Climate, AV and media. |
| 2:49 | "Explore more low voltage services... you know this is AI almost immediately." | That block and its AI-made pictures are off the page. |
| 3:06 | "The review section here, I'd push this closer to the call to action." | Reviews sit right under the cards, second band down. |
| 3:21 | "This more services we offer is fine... a simple card with a small icon that hyperlinks to another landing page." | "More we install in New Jersey homes": five plain cards with small icons, each linked to its page on their site. |
| 3:30 | "Add an about section that tells somebody a little bit about this company." | About band with the founder's photo and two sentences from their About page. |
| 3:35 | "The hero, a small reviews banner right below that... the reviews... trade partners... about us... more services... FAQ... secondary CTA." | Order: hero, cards, reviews, our process (for architects, designers, and contractors), about, more services, FAQ, closing ask. The small reviews banner is missing: see below. |

## Where every fact came from

- Logo (their SVG, drawn to PNG), red `#EB1D44` (darkened to `#C8143A` so white words read on it), phone 732-FORTECH, address, counties, the service page links, and the FAQ answers (shortened): their public site, read 2026-10-06 (`projects/research/fortech-electric*/site.json`).
- "Since 2009" and the founder's name: the founder's message on their About page. The photo sits beside that message and is read as him.
- The three reviews (E. B., Joey C., Carol P.): Google reviews shown on their site through Trustindex. Lines cut for length; a typo and run-on punctuation tidied.
- "Lutron Gold Dealer" in the footer: the dealer badge image on their site. "Licensed and insured": their home page description.
- The four card lines and the four process steps: written from their own page (scenes, low-voltage wiring, one app or wall panel, new and existing homes). No brand claim beyond theirs.
- Their hero picture and the five 2026-01 pictures on the page are AI-made; none is used.
- No rating is stated on their site, so there is no rating line and no reviews banner under the hero button. Pull the Google rating before this goes to them.
- The form sends nothing. It is a render.

## Big misses the AIOS would raise (his to take or leave)

1. **No reviews about home automation.** Every review on their site is a generator job or general service. For a buyer of a whole-home system, two reviews that name lighting, AV, or a smart home would carry more than all nine.
2. **No rating in the hero.** He asked for a small reviews banner under the button. Their site never states their Google rating or count; until it does, the first screen has no proof next to the ask.
3. **No photos of finished automation work.** Their portfolio's Low Voltage photos are racks and panels, and the homes shown are exteriors. Rooms with keypads, screens, and lighting scenes they built would sell the service; ask them for five.
