# Reliant Electrical and Automation: the home theater "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom audit. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder, built by `scripts/prospect_page.py` from `spec.json` (their logo and two photos in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/reliant-theater" --port 8801`, then http://127.0.0.1:8801/
- Renders: `projects/Landing Page Build/renders/2026-10-06/reliant-theater-after-1440.png`, `-fold-1536.png`, `-390.png`.
- The page it replaces: https://reliant.services/home-theater-automation/ (one page for two services; this render is the home theater half, automation is a card at the foot).
- The Loom: https://www.loom.com/share/6c3519b9bb5e48558e7e9846d1da1289 (5 minutes 4 seconds). Its file and word-timed transcript are in `media/looms/6c3519b9-increase-home-theater-landing-page-conversions/` (not in git).
- Company: Reliant Electrical and Automation Inc., 144 E Weldon Ave, Fresno, CA 93704, (559) 338-4458, info@reliant.services, CSLB License #1128802. The reviews name Marshal (and Evan) on the jobs; the site does not say who owns it.

## What he said, and what the page does

Times are from the Loom. His words are from the laptop's transcript.

| At | His words | On the page |
|---|---|---|
| 0:29 | "We'll just start off with one, home theater and automation... super important to segment your landing pages... If somebody wants a home theater... they land on your home theater page. If it's automation, they land on your automation page." | One service: home theater. Automation is one card under "Everything else we install", linked to their Smart Home Evolution Plan page. |
| 0:51 | "Your header section being high contrast to the hero section. So that would be like a white banner with black text that has the dropdowns with your logo." | White top bar, their logo, the phone in black, one orange button. No dropdowns: one page, one thing to do. |
| 1:01 | "The primary color being this orange. I love that it pops out. So we're going to make that into the primary call to action button." | Their orange (#F76A0C, from their CSS) is the button, the eyebrow, the cards, and the icons. |
| 1:08 | "[Home] theater installation in the area you're currently trying to target would be the headline." | h1: "Home Theater Installation in Fresno". Their page targets Fresno, Clovis, and Madera; Fresno is the address and the search city. Clovis and Madera are in the FAQ and the footer. |
| 1:12 | "Above that the eyebrow saying the kind of person you're targeting. So for luxury homeowners or high-end homes or custom home audio... The orange is going to be that eyebrow color." | Eyebrow: "For luxury homeowners", in orange, centered above the headline. |
| 1:29 | "One to two copy lines... acoustic tuning, high-resolution media, and low latency streaming." | Sub: "Acoustic tuning, high-resolution picture and sound, and streaming with no lag. One licensed team handles the design, the wiring, and the installation." |
| 1:42 | "A big call to action that says something like book a meeting... link to a four-step form, first name, email, phone number, and message." | "Book a meeting" opens the four-step form in that order. It sends nothing; it is a render. |
| 2:01 | "Right below that, it would be a Google review banner." | "5.0 on Google from 17 reviews" with stars under the hero button. The number is the Google widget on their home page. |
| 2:16 | "The services offered within home theater... a 7.1, a 7.2, a 15.1. How's audio being steered? What kind of mixing... XLRs... the audio quality matters... in wall, in ceiling... cards, three to six, high contrast orange with either white or black text." | Four orange cards, black text (black reads better on this orange): speaker layouts, steering and mixing, in-wall and in-ceiling speakers, the gear that keeps the quality. |
| 3:00 | "An about us section... a picture of you or a picture of the team... a brief description of who your company is and what they stand for." | About: "From tugboats to smart homes", two sentences cut from their About page. The photo box is marked empty: no owner or team photo on their site. |
| 3:18 | "A review section, just three cards of relevant reviews if you have things for just home audio or home theater, or the quality of the theater." | Three Google reviews from their site, first name and last initial: Mason D. (audio quality and clean installation), Sol R., Peter T. Only Mason's is about audio. |
| 3:34 | "Three to four images of installations that you've done. Maybe the card on hover... white text on a black background... two to three sentences about that project." | Two real photos (their theater, their backlit onyx game-room bar) and one marked empty box. The engine has no hover text, so the project line sits in each photo's `alt`. |
| 3:54 | "An FAQ, this is just for Google SEO." | Five plain questions on home theater, answers cut from their own FAQ and service copy, plus one on Clovis and Madera. |
| 4:03 | "[Our process from] consultation all the way into the installation, and on the eyebrow of that section... the architects, builders and designers." | Four numbered steps on a black band: consultation, design and wiring plan, equipment, installation and tuning. Eyebrow: "For architects, builders, and designers". |
| 4:16 | "Secondary call to action." | "Book your theater consultation" with the same button, above the services links. |
| 4:19 | "A section linked to other services, so like your network, your lighting control, your outdoor entertainment... three to six hyperlinks." | Four cards with real links: Networking, Lighting control, Whole-home automation, Backup power. Outdoor entertainment has no page on their site, so it is not linked. |

## Where every fact came from

- Logo (the wide lockup, `Reliant_Electrical_and_Automation_PNG_File-01.png`), orange `#F76A0C`, faces Montserrat and Inter, phone, address, areas, and the license: their public site, read 2026-10-06 (`projects/research/reliant-theater/`, `reliant-home/`, `reliant-about/`, `reliant-lighting/`, `reliant-residential/`).
- "5.0 on Google from 17 reviews" and the three reviews: the Google review widget on their home page (business-reviews-bundle). Their schema says 15; the widget on screen says 17. Check the profile before anyone outside sees the page.
- The hero and first work photo: `Theater-scaled.webp` from their theater and residential pages, a phone shot of a real room. The second work photo: `PXL_20250702_230652000.webp` from their lighting page, a Pixel shot of a backlit onyx bar in a wood-paneled game room.
- Not used: the Control4 and Snap One marketing images on their pages (Avalon Beach, AU_2G_Dine keypad, EMEA_C4 theater render, the C4 drip image, the Araknis rack), the lighting header (a city kitchen, not Fresno), and the stock solar and electrician photos. None is their work.
- Card lines, FAQ answers, and process steps: shortened from their theater page ("What to Expect with Installation", "Immersive Audio Systems", their automation FAQ) and their About page. Speaker counts (5.1 to 15.1), steering and mixing, in-wall and in-ceiling, and the gear line are from his Loom; the balanced runs, dedicated circuits, grounding, and surge protection are on their page.
- The light serif for headings: his rule for high-end residential buyers (Taste Log, 2026-10-05).
- Top menu removed on purpose. The form sends nothing.

## Big misses the AIOS would raise (his to take or leave)

1. **One theater photo on the whole site.** Everything else is manufacturer imagery. The hero and the work grid share the same room, and one work box is empty. For a high-ticket room, three finished theaters from their own jobs are the proof a buyer looks for. Ask them for five.
2. **No face.** No owner or team photo anywhere on the site, and the site never says who runs the company; the reviews are the only place "Marshal" appears. The about box is empty until they send one photo and one name.
3. **The reviews are about electrical work.** Of 17 Google reviews, one names audio. Two reviews from theater clients, asked for after the next two jobs, would carry more than all 17.

## Not done

- The second Loom (him going through the rebuilt page and the form).
- The email to the company.
- The automation page he said to split off (this render is the theater half only).
