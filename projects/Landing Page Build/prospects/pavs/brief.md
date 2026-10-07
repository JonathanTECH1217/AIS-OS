# PAVS Smart Home Tech: the "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom audit. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder, built by `scripts/prospect_page.py` from `spec.json` (their logo in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/pavs" --port 8804`, then http://127.0.0.1:8804/
- Rebuild after a spec change: `python scripts/prospect_page.py all pavs`
- Renders: `projects/Landing Page Build/renders/2026-10-06/pavs-after-1440.png`, `pavs-after-fold-1536.png`, `pavs-after-390.png`.
- The page it replaces: https://pavs.tech (their home page; they have no service pages).
- The Loom: https://www.loom.com/share/43385752eb5640fda728044d9cf90829 (3 minutes 24 seconds). Its file and word-timed transcript are in `media/looms/43385752-increase-leads-with-better-landing-pages/` (not in git).
- The company: Ponderosa Audio Video Systems, "PAVS Smart Home Tech", 2550 Copper Ridge Dr Unit A, Steamboat Springs, CO 80487, (970) 879-2217. The owner is Ross (named in five of their Google reviews, never on the site; last name not on file).

## What he said, and what the page does

Times are from the Loom. His words are from the laptop's transcript.

| At | His words | On the page |
|---|---|---|
| 0:36 | "You don't have individual service pages... let's just start off with lighting control. It's a really high-ticket item." | One service: lighting control. Everything else they install is six linked cards near the foot. |
| 0:48 | "Your header section is running a little bit big. I'd shrink that... about 60 pixels from top." | The engine's header is 80 px with a 56 px logo. The engine sets the header height, so 60 px is not reachable from the spec (see "Not done"). |
| 0:57 | "Increase the contrast of this background image... change that stock background out to be something like a picture of a home with a lighting system inside of it." | No photo: every picture on their site is stock or a Savant marketing render. The hero is plain black with white words (the taste-log fallback). A real photo of a home they lit is miss 1 below. |
| 1:09 | "Headline would be something like lighting control installation in whatever area is the primary area you're trying to target." | h1: "Lighting Control Installation in Steamboat Springs". Their site names only Steamboat Springs and "the greater Steamboat Springs area". |
| 1:16 | "An eyebrow... would target to the person you're trying to speak to, or maybe it could be a credential." | Eyebrow: "Serving Steamboat Springs homes since 1997" (their site: founded in 1997, serving the area). |
| 1:25 | "One or two sentences... what lighting control has to offer with the keypads, control, talk to it by voice and automation." | Two sentences: keypads that set a room with one press; lights by voice, app, or schedule. |
| 1:34 | "Big green button that just says something like book an appointment, book a meeting." | Their green (#6CC24A), "Book a meeting", in the header, the hero, and the closing band. |
| 1:44 | "A four-step form: first name, email, phone number, and message that would link directly to your calendar and then send an email push notification to your inbox." | The button opens the four-step form in that order. It ends on a "Pick a time" step with a marked box where their calendar would go. The form sends nothing; it is a render. |
| 2:04 | "A little review banner there... the trust that a customer has with your company when they're taking that big action." | Five stars and "Rated 5 out of 5 on Google" sit under the hero button (their site's own words). |
| 2:14 | "The process of the service is broken down here in this section." | Their four steps kept, numbered: Home consultation (free), Customized plan, Skilled installation, Guided tutorial (with 24/7 support). Eyebrow "How the work goes". |
| 2:19 | "An about us... a picture of the team... you, the owner, and then a little bit of copy and a call to action." | About block with their words cut to two sentences. The photo is a marked empty box (no owner or team photo on their site). The engine's about block has no button; the header and the band after the reviews carry it. |
| 2:36 | "Three reviews... card style, kind of friendly." | Three Google reviews from their home page in cards: Doug S., Ross D., Mary Jo W. First name and last initial only. |
| 2:51 | "Our services could be a section... hyperlinked to individual service landing pages." | Six cards with icons: whole home automation, home theatre, sound systems, security cameras, thermostats and HVAC, locks and doorbells. Each links to https://pavs.tech/services/ because no service page exists yet. |
| 3:00 | "An FAQ down here and then maybe a secondary call to action... book a free consultation for a lighting design." | Five plain questions on lighting control, then "Book a free consultation" with the same button. |

## Where every fact came from

- Logo, green (`#6CC24A` and the darker `#3A9018`), phone, address, "founded in 1997", "over 15 years", "serving the greater Steamboat Springs area", the four process steps and their captions (FREE, FOR YOUR HOME, PROJECTS LARGE & SMALL, + 24/7 SUPPORT), the services list, and "Rated 5 out of 5": their public site, read 2026-10-06 (`projects/research/pavs/`, `pavs-about/`, `pavs-services/`, `pavs-contact/`).
- The reviews: ten Google review screenshots on their home page, read by eye. Names cut to first name and last initial. One of the ten is four stars (Ronda F.); not used.
- The hero sub line, the FAQ answers, and the service card lines: plain descriptions of lighting control and of the services their site lists. No brand of gear is named; their site names Savant only as a logo.
- Fonts: their site loads Roboto, Roboto Slab, and Lato. Headings use the engine's light serif (the high-end residential rule); Lato for the eyebrows and buttons, Roboto for the body.
- Band colors: the AIOS's choice, not his. With no hero photo the hero and the default black process band ran together, so the process took their dark green and the rest alternate mist and white. His A B A C A B A colors are his to settle.
- No footer credentials: the site states no license number or award.
- Top menu removed on purpose: one page, one service, one thing to do.
- The form sends nothing. It is a render.

## Big misses the AIOS would raise (his to take or leave)

1. **Not one real photo.** Their hero, their service pictures, and their "smart home" images are stock or Savant marketing renders; the only real photo is a street in downtown Steamboat Springs. The hero is black and the about box is empty because of it. Five photos of rooms they lit and one of Ross and the crew would change the page more than any copy.
2. **No review names lighting.** The ten reviews are about TVs, sound, and service after the sale. Two reviews from lighting clients would carry more than all ten. The site also claims "Rated 5 out of 5" while one shown review is four stars; check the live Google profile before anyone outside sees the page.
3. **No calendar and no service pages.** The form ends on a marked box where their calendar goes, and all six service cards point at one services page. Until they have a booking link, a lead waits for a call back; until they have service pages, the cards have nowhere to send a buyer.

## Not done

- The header at 60 px (he asked at 0:48): the engine fixes the header at 80 px and the spec has no key for it.
- A button inside the about block (he asked at 2:19): the engine's about block takes no button.
- A hero photo of a home with a lighting system: none exists on their site.
- The second Loom and the email to Ross.
