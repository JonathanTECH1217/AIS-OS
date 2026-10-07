# Lighthouse Outdoor Lighting of Vail: the "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom review of their Vail office page. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder, built from `spec.json` by `scripts/prospect_page.py` (their logo and six photos in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/lighthouse-vail" --port 8793`, then http://127.0.0.1:8793/
- Rebuild: `python scripts/prospect_page.py all lighthouse-vail`
- Renders: `projects/Landing Page Build/renders/2026-10-06/lighthouse-vail-after-1440.png`, `-fold-1536.png`, `-390.png`.
- The page it replaces: https://lighthouse-lights.com/office-colorado-vail/ (he also opened their SERVICES and PROJECTS pages).
- The Loom: https://www.loom.com/share/0257f9eee6ff464aa8911e2ee4d9b105 (4 minutes 33 seconds). Its file and word-timed transcript are in `media/looms/0257f9ee-improving-service-page-conversions-with-trust/` (not in git).
- The company: a Vail Valley office of The Lighthouse Group (a national outdoor lighting brand). The partner is Mark Nall. Phone 970.236.1567, mail address 105 Edwards Village Blvd Unit# 4957, Edwards, CO.

## What he said, and what the page does

Times are from the Loom. His words are from the laptop's transcript.

| At | His words | On the page |
|---|---|---|
| 0:57 | "Let's just say lighting control installation being one of the services you guys offer in this area... per offering you guys have." | One service a page. "Lighting control" was his stand-in; this company sells landscape lighting, so the page is their installation service. His to swap. |
| 1:13 | "Lighting control installation in X area, the area you're currently trying to target the most." | h1: "Landscape Lighting Installation in Vail" |
| 1:13 | "Above that would be an eyebrow speaking directly to the prospect you want to sell... residential or B2B targeting in that eyebrow." | Eyebrow: "For homeowners in the Vail Valley". He did not pick; the page on screen speaks to homeowners, and the trade gets the process section. His call. |
| 1:36 | "A few lines of copy right below that, speaking directly to the outcomes... one or two sentences." | Two sentences under the headline: paths, trees, and stonework lit; safe, warm, longer evenings; brass and copper for Vail winters. |
| 1:48 | "A call to action saying book a meeting, and this would be a four-stage form in the primary color... this kind of muted desaturated olive kind of gold. I like that." | One "Book a meeting" button, olive gold `#A3A786` from their site, opens the four-step form (first name, phone, email, message). |
| 2:02 | "The serif style font is also nice. This should be centered and kind of pushed up a little bit. Also, the header section's a little bit big, reducing the size of that." | Serif headings, centered, white on their own lit home at dusk. The hero is capped at 700 px. |
| 2:06 | "Right below that call to action, just putting a little review badge there that just shows five stars and then the amount of reviews you guys have had." | Not on the page. Their site states no rating and no count. It goes in once the Google number is checked. |
| 2:27 | "Below that would be your services... speaking directly to the outcomes... on cards in the primary color with either black or white text. I think black text would probably look better on this kind of olivish gold." | Four olive cards with icons: a home that glows, safe steps and entries, evenings that run longer, built for Vail winters. The engine draws white text on them; black is what he wants and needs an engine switch. |
| 2:48 | "An about us. I saw on the home page that I think was Mark... one of those photos with a little bit of a description about the company." | "Meet Mark Nall", his photo from the Vail page, two sentences cut from his own words. |
| 3:09 | "The portfolio section... your highest quality three photos... split into thirds." | Three of their portfolio photos from the Vail page: the timber entry, the Bear Dance log home, the stone arches. |
| 3:18 | "Our process. This speaks directly to the builder, architect and designer... design consultation, installation, then ongoing support." | Four numbered steps under "For builders, architects, and designers": design consultation, the plan, installation, ongoing service. Their bollard row sits behind it, darkened. |
| 3:30 | "Reviews... the prospect can click through and they go, okay, this is a good company." | Three marked empty boxes. No reviews on their site. |
| 3:40 | "A brief FAQ just for SEO stuff." | Five questions, one-line answers, cut from the FAQ on their Vail page. |
| 3:44 | "Secondary services that are hyperlinked internally. Your high ticket items like your whole home audio..." | Three cards linked to their own pages: outdoor audio, Legacy Care, holiday and event lighting. He named integrator items; these are theirs. |
| (rule) | The ask again at the foot (his words on Momentum, 2026-10-05: "so they don't have to scroll back up"). Not said in this Loom. | "Start your project" with the button, as the closing band. |

Order on the page, his order in the Loom: hero, cards, about, work, process, reviews, FAQ, secondary services, close.

## Where every fact came from

- Logo, olive gold (`#a3a786` and `#a3a585` in their CSS), faces (Cormorant Garamond, Figtree, Open Sans), phone, address, Mark's words and degrees, the five services and their links, the FAQ: their public site, read 2026-10-06 (`projects/research/lighthouse-vail/`, `lighthouse-vail-services/`, `lighthouse-vail-projects/`).
- Photos, all theirs, from the Vail office page: `Vail-Slider-1` (the hero), `Director_MainImg_Mark-Nall` (about), `Koenig-timber-entry-from-left`, `Bear-Dance-Bollard-on-Driveway1`, `Prioletti-arches` (the work), `Vail-Slider-4` (behind the process). Their page calls these "recent landscape lighting design projects in the Vail, Colorado, area"; the stone-arches house may be another office's job.
- The four card lines and the process steps: shortened from their FAQ and services copy (brass and copper, snow and wind and wildlife, low voltage LED, the 20 point inspection, night aiming, Legacy Care).
- The serif is the engine's Newsreader, not their Cormorant Garamond; the sans is their Figtree.
- No rating, no review, no award, no year, no job count is printed: none is on the pages read (their Awards page was not read).
- Top menu removed on purpose: one page, one service, one thing to do.
- No background pattern set: his A B A C A B A rule (2026-10-06) names no colors yet, so the PHA look holds.
- The form sends nothing. It is a render.

## Big misses the AIOS would raise (his to take or leave)

1. **No reviews and no Google count anywhere on their site.** The badge he wanted under the button and the three review boxes are empty, and that is the trust he said sells the click. Pull their Google profile (`research.py google`, about 4 cents, his go first) or ask Mark for the count and three reviews.
2. **No photo of the Vail crew, trucks, or a named Vail job.** The only face is Mark's hiking photo, and the portfolio may mix in other offices' work. Three jobs by Vail Valley address and one crew photo would carry more than the whole site does now.
3. **No calendar.** The form ends on a marked box and the page promises a call back. Until they link a booking calendar, a lead that waits goes cold.

## Not done

- Black text on the olive cards (his words at 2:27): the engine has no switch for it.
- The review badge and the reviews: wait on the Google number.
- The Loom B and A cut and the email to Mark.
