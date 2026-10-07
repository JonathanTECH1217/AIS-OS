# Holm Electric: the "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom audit, by `scripts/prospect_page.py` from `spec.json`. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder (one file; their logo and five photos in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/holm-electric" --port 8799`, then http://127.0.0.1:8799/
- Rebuild after a spec change: `python scripts/prospect_page.py all holm-electric`
- Renders: `projects/Landing Page Build/renders/2026-10-06/holm-electric-after-1440.png`, `-fold-1536.png`, `-390.png`.
- The page it replaces: https://holmelectric.com/residential/ (one page for every residential service, an interactive map in the hero).
- The Loom: https://www.loom.com/share/56cfa2fd6f6644148769298a61285b5e (4 minutes 40 seconds). Its file and word-timed transcript are in `media/looms/56cfa2fd-boost-conversions-with-high-ticket-service-pages/` (not in git).
- The company: Holm Electric, Inc. Two offices: 919 Incline Way, Ste. 21, Incline Village, NV 89450 (775-831-3781, info@holmelectric.com) and 5045 S Rogers St, Ste. 3, Las Vegas, NV 89118 (702-818-3781). The owner's name is not on the site. CRM row not looked up for this render.

## What he said, and what the page does

Times are from the Loom. His words are from the laptop's transcript.

| At | His words | On the page |
|---|---|---|
| 0:28 | "You guys don't have a landing page per service that you offer. So let's start with a really high-ticket item like lighting control." | One service: lighting control. Everything else on their residential page is off this one. |
| 0:33, 4:08 | "I notice you have this interactive map here, I think this is pretty cool... it's probably not doing a lot for your conversion rate... I wouldn't put this at the top of the hero section." | The map is left off on purpose. |
| 0:46 | "The header section up at the top should be reduced to around 40% of its current height." | One 80 px bar: logo, phone, one button. Their menu is gone. |
| 0:53 | "Hero section is just going to be a high contrast, dark background... interior of a house, a normal architectural looking scene, preferably high end." | Their own photo of a bar with pendant lights (from their home page) under a dark scrim, white words, centered. |
| 1:17 | "A headline would be something like lighting control installation in the area you're currently trying to target." | h1: "Lighting Control Installation in Lake Tahoe". Their first office is Incline Village and the residential page lists Lake Tahoe first; Las Vegas is in the footer. |
| 1:23 | "Above that would be the eyebrow with a direct call out to the person that you're trying to target, or maybe a credential." | Eyebrow: "Lake Tahoe homeowners, architects, and builders". |
| 1:35 | "The primary color we're going to be working with right here, it looks like this blue. We're gonna make that blue the call to action button as well as like card background colors." | Button and cards in their blue. Their site's blue is #799EC8; white on it reads at 2.79:1, so the button and cards use the same hue one step darker (#4A78B0, 4.56:1) and #799EC8 is the accent on the process step rules. |
| 1:40 | "Big button saying something like a book a meeting." | "Book a meeting", three times: the bar, the hero, the foot. |
| 1:43 | "Linked to a four-stage booking form, first name, email, phone number, and a brief message that disqualifies any low-ticket guy." | The button opens a four-step form, one question a screen. The message hint asks for the home, the rooms, new build or a remodel. No floor is printed; that is theirs to set. |
| 1:53 | "Right below that would be Google Reviews." | No rating or review is on their site, so there is no trust line under the hero button. The review band sits where he put it at 3:17. |
| 2:00 | "An about us section, just talking briefly about who you are... accompanied by a picture of either you or the team." | About band, two sentences cut from their About page. The photo is a marked empty box: no team or owner photo on their site. |
| 2:17 | "Hero, services, then about us. So the services section... the keypads, control, automation, voice, Kelvin color control. All of the benefits... as far as outcomes go for the buyer." | Four cards with icons: Keypads, Control from anywhere (app and voice), Automation, Kelvin color control. Each line is an outcome, in plain words. |
| 2:40 | "Below that would be a portfolio of your work relevant to the offering." | Three of their own photos: vanity lights, theater sconces, a media wall under ceiling spots. |
| 2:52 | "Our process, and that talks to the B2B buyer. So your architect, builder, designer... the design consultation all the way to the installation and ongoing service." | Four numbered steps on a dark band with their lakefront home behind: design consultation, engineering and drawings, installation and programming, documentation and ongoing service. The words come from their About page. No button on this band. |
| 3:17 | "The reviews section... three cards of the top relevant reviews to this section alone." | Three marked empty boxes. Their site shows no reviews. |
| 3:35 | "Internal linking towards other high ticket services... whole home audio, your dedicated home theater... keep it at three." | Three cards: Whole home audio, Dedicated home theater, Motorized shades. All three link to /residential/ because no page per service exists yet. |
| 3:53 | "Secondary call to action... the booking form, same four steps." | The closing band, same button, same form. |
| 3:57 | "All of the cards using the same primary color. This could be a high contrast white text or black text." | White on the blue. |

## Where every fact came from

- Logo, the two blues (#9DBCE1 and #799EC8 in their CSS), Poppins, both phones and addresses, the residential service list, "Since 1998", the engineering and documentation words, the brands they integrate (Lutron, Ketra, Savant, RTI): their public site, read 2026-10-06 (`projects/research/holm-electric*/site.json`).
- Photos: their home page and their public WordPress media list. None is marked AI-made. The 3D-rendered partners banner, the stock hard-hat contact banner, the camera photo, and the commercial lobby banners were skipped. The vanity photo is cropped to its right side so the bulbs stay in the 4:5 cell.
- The serif titles are the engine's rule for high-end residential; Poppins stays for the rest, as on their site.
- The card lines and the process steps are written from the outcomes he named and their About page. No brand, no price, no number of jobs, no rating.
- Top menu removed on purpose: one page, one service, one thing to do.
- The form sends nothing. It is a render.

## Big misses the AIOS would raise (his to take or leave)

1. **No reviews and no rating anywhere on their site.** The proof under the ask is empty, in the hero and in the three cards. Their Google Business Profile reviews would fill both; the Google profile pull (about 4 cents) needs his go.
2. **No photo of the owner or the team, and the only lighting interiors are 960 px wide.** The about box is empty and the hero is soft on a wide screen. Ask them for a team photo and the full-size files of five lighting jobs. The sharper lakefront home at dusk (1920 px) is the swap for the hero if he wants it crisp now; it sits behind the process band today.
3. **No page per service and no booking calendar.** The three service cards all land on the same /residential/ page, and the form ends on a promise to call. A page each for audio, theater, and shades, and a calendar link at the form's end, are the next build.

## Not done

- The Loom B and A cut and the email to the owner (the owner's name is not on the site).
- Which city carries the headline, Lake Tahoe or Las Vegas: his call. The spec takes one line to change.
- The header's "40%": their bar could not be measured here; the render's is 80 px.
