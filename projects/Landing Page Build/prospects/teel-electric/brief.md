# Teel Electric Company: the "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom review. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder, built by `scripts/prospect_page.py` from `spec.json` (their logo lockup and two photos in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/teel-electric" --port 8803`, then http://127.0.0.1:8803/
- Renders: `projects/Landing Page Build/renders/2026-10-06/teel-electric-after-1440.png`, `-fold-1536.png`, `-390.png`.
- The page it replaces: https://www.teelelectricco.com/home-automation (he took it as the template for a lighting control page).
- The Loom: https://www.loom.com/share/c8b55c6b28a242fbad943c322ba0393e (3 minutes 48 seconds). Its file and word-timed transcript are in `media/looms/c8b55c6b-rebuild-service-landing-pages-to-convert/` (not in git).
- Their site: four Wix pages (Home, Services, Home Automation, Projects). Jupiter, FL; "serving South Florida"; a Lutron dealer and installer. No about page, no reviews, no owner name.

## What he said, and what the page does

Times are from the Loom. His words are from the laptop's transcript.

| At | His words | On the page |
|---|---|---|
| 0:30 | "It's really good to have a landing page per service, so let's just start with the lighting control." | One service: lighting control. Their page's Lutron and Sonos product blocks are gone; audio and shades sit in the secondary services. |
| 0:58 | "Change the stock image out to be something like a home... right in front of that, it would be high contrast white text." | Their own Projects photo of a lit custom home at dusk, under the engine's dark scrim. White words. |
| 1:10 | "A headline that says something along the lines of lighting control installation in the area you're trying to target." | h1: "Lighting Control Installation in Jupiter" (their address; their site says "serving South Florida"). |
| 1:19 | "Above that would be a small eyebrow that just says who you're targeting." | Eyebrow: "For South Florida homeowners". |
| 1:20 | "One or two sentences that would just talk about the control, automation and security benefits." | Two sentences: keypad, phone, or voice; evening scenes, travel schedules, a lit entry. |
| 1:36 | "A big call to action that would say book an appointment... a four-step form that would be first name, email, phone number, and a message that would link directly to a calendar." | One button, "Book an appointment", three times down the page plus the header. It opens a four-step form in that order. The last screen has a "Pick a time" slot; they have no calendar to link yet. |
| 1:50 | "Automation, security, keypads, and voice control would all be cards that would have little brief amounts of text on them, maybe icons." | Four blue cards with icons: Automation, Security, Keypads, Voice control. |
| 2:05 | "Below that would be an about us, and that would just be a picture of either you or your team, and then a brief description of the company." | About us: two sentences cut from their "Who We Are" copy. The photo box is marked empty; their site shows no one. |
| 2:17 | "A Google review banner right below the hero section, or maybe put it into hero section." | Not drawn. Their site states no rating, and the engine draws the banner only from a stated rating. |
| 2:25 | "Below the about us section would be the reviews... relevant reviews to lighting control if you have them. If not, just the best reviews about your team. Just three." | A reviews band with three marked empty boxes: their site shows no reviews. |
| 2:36 | "If you're targeting architects, builders and designers, you would have an our process that just goes through the timeline of design consultation all the way to the installation. And then ongoing service after that." | Eyebrow "For architects, builders, and designers"; four numbered steps: design consultation, lighting plan, installation and programming, ongoing service. Their pool-house photo behind it. |
| 2:50 | "Below that, you could have an FAQ. This does SEO work." | Five plain questions on lighting control, one-line answers. |
| 3:03 | "A secondary services landing page that would direct people to home automation, any other high-ticket items like James Loudspeaker installation, whole home audio, media distribution." | Three cards linked to their real pages: Home automation, Whole home audio (Sonos is on their automation page), Motorized shades (Lutron shades on their Projects page). James Loudspeaker and media distribution are not on their site, so they are not claimed. |
| 3:21 | "Below that is secondary call to action. That would just take people through your booking form more often." | The closing band, same button, same form. |

## Where every fact came from

- Name, phone, address, "serving South Florida", "Lutron dealer and installer", "licensed experts", "free estimate", the Lutron HomeWorks QS, RadioRA 2, Sonos, and shades lines, the Projects page words: their public site, read 2026-10-06 (`projects/research/teel-electric*/site.json`).
- Brand blue `#26529C`: sampled from their home page's Contact band. Poppins: their site's face. The light serif for headings: his rule for high-end residential (Taste Log, 2026-10-05).
- The logo: their site's header is plain text; the lockup in `assets/logo.png` is their T-sphere mark (the only mark on the site) beside the name in Poppins SemiBold.
- `assets/hero.jpg`: their Projects photo `DMD_1776PS` (a custom home at dusk). `assets/process.jpg`: their home page photo `DMD_1802` (the pool house), cropped to landscape. Both are their own uploads, not Wix stock.
- Voice control, and "RadioRA 2 is wireless" in the FAQ: Lutron product facts, not claims from their site.
- Top menu removed on purpose: one page, one service, one thing to do.
- The form sends nothing. It is a render.

## Big misses the AIOS would raise (his to take or leave)

1. **No reviews anywhere.** Their site has none and states no rating, so the proof band under the ask is three empty boxes and the Google banner he asked for cannot be drawn. Three Google reviews, two of them about a Lutron job, would fill the strongest band on the page.
2. **No one on the page.** No owner or team photo and no owner name on their site. The about box is empty. One photo of the crew beside a Lutron panel is enough.
3. **The form ends at nothing.** He asked for the booking to land on their calendar. Until they have a booking link, a lead that fills the form waits for a call back.

## Not done

- Their calendar link in the form's last step.
- The Loom B and A cut and the email to the owner.
