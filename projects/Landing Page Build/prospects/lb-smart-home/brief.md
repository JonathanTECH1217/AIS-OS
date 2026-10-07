# Liberty Bell Smart Home: the "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom audit. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder, built from `spec.json` by `scripts/prospect_page.py` (their logo and six photos in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/lb-smart-home" --port 8798`, then http://127.0.0.1:8798/
- Rebuild: `python scripts/prospect_page.py all lb-smart-home`
- Renders: `projects/Landing Page Build/renders/2026-10-06/lb-smart-home-after-1440.png`, `-fold-1536.png`, `-390.png`
- The page it replaces: https://lbsmarthome.com/residential-solutions#lighting-and-shades (every residential service on one page; lighting and shades is one block of it; they also have https://www.lbsmarthome.com/residential-solutions/lighting-and-shades)
- The Loom: https://www.loom.com/share/0fd362d61f2942178544367a6491544a (4 minutes 28 seconds). Its file and word-timed transcript are in `media/looms/0fd362d6-boost-landing-page-conversions-for-services/` (not in git).
- The company: Liberty Bell Smart Home (lbsmarthome.com). Two stores: 1522 Lincoln Way, Auburn, CA 95603 (916-386-9696) and 10072 Donner Pass Rd, Truckee, CA 96161 (530-927-8117). Jonathan signs off to "Mike". Their site names Mark Buzzard as President and CEO; check who Mike is before the email goes out.

## What he said, and what the page does

Times are from the Loom. His words are from the laptop's transcript.

| At | His words | On the page |
|---|---|---|
| 0:31 | "I see that you guys have this split up across all of the services here... [a] landing page should be an individual service. So when somebody looks up something like lighting control installation in... Downtown Historic Auburn, you want your result to show up and then the landing page have the exact offering." | One service: lighting control. Shades, audio, theater, networks, security are off the page; three of them are links near the foot. |
| 1:09 | "Background would be something like home, high end home, 'cause you wanna segment the market into the luxury tier." | Their own home theater photo (dark wood, lit sconces, star ceiling) under a dark scrim, white words on it. |
| 1:39 | "It seems that the blue would be a good color for the call to action button." | The logo navy (`#003865`) on every "Book a meeting" button, the card grounds, and the service icons. Their bright blue (`#009CDE`) is the eyebrow and the step numbers. Both are theirs; swapping them is two values in `spec.json`. |
| 1:43 | "The headline would be something like lighting control installation in downtown historic Auburn." | h1: "Lighting Control Installation in Downtown Historic Auburn". Centered, light serif, white. Their site confirms Auburn (the Lincoln Way store, "New Auburn Location"). |
| 1:50 | "The eyebrow right above that being something like featured in X Magazine or for luxury homeowners." | Eyebrow: "For luxury homeowners". Their site names no magazine. |
| 2:02 | "A services section that breaks down the outcomes to the customer... key pads being customized, controlling lighting scenes... controlled through voice, has adjustable color temperature... down lights, small aperture, pendants, fixtures, sconces." | Four navy cards with icons: Custom keypads (Entertain, Dine, Evening, All Off, from their own keypad photo), Voice control, Adjustable color temperature, Any fixture you want (downlights, small aperture, pendants, sconces). |
| 2:29 | "An about section being a picture of you... or your team and then a brief description about what your company stands for." | About band: the crew outside the office, "A family company since 1981", two sentences from their about page (the 1981 break-in, peace of mind and comfort, ALA-certified designers, Alpine Electric). No photo of the owner on their site. |
| 2:41 | "Our process that walks them through design consultation all the way up to the installation... talks directly to the designer builder and the architect." | Eyebrow "For architects, builders, and designers", four numbered steps: Design consultation, Lighting plan, Rough-in and wiring, Installation and programming. Their truck behind it. No button in this band. |
| 3:04 | "Three reviews that are relevant to the offering, or just kind of talk your company up... putting that little Google review banner right below the call to action." | Three quotes from their home page, first name and last initial. The banner under the button is not drawn: their site states no Google rating, and the page invents nothing (see the misses). |
| 3:27 | "A secondary link that goes to some other high-ticket services... distributed audio, your whole home audio... dedicated home theater, networking." | Three linked cards: Whole home audio and video, Dedicated home theater, Home networks, each to its real page on their site. |
| 3:43 | "A portfolio... just three of your best pictures is all you need." | Three of their gallery photos: the open kitchen with pendants, the upstairs lounge, the covered patio. |
| 3:51 | "A secondary call to action that leads to the same four-stage booking link: first name, email, phone number, and brief message. And that links directly to your calendar." | Closing band "Free lighting consultation" with the same button. The form is four steps (first name, phone, email, message) and ends on a marked box where their calendar goes. The drip he names is not a page thing. |

## Where every fact came from

- Name, logo, the two blues, Montserrat, phones, both addresses, service areas, the about words, the ALA-certified designers, Alpine Electric, CEDIA, the Control4 showroom, Lutron: their public site (home, `/about-us`, `/residential-solutions`, `/residential-solutions/lighting-and-shades`), read 2026-10-06 and saved under `projects/research/lb-smart-home*/`.
- "Downtown Historic Auburn": his words. Their site names Auburn and Lincoln Way; it does not say "downtown" or "historic". His to keep or trim.
- The reviews: the four quotes on their home page. The reviewer names are in that page's source, commented out beside each quote (Jeanine Garnet, Yaser Alex, Estrella Sabahudin, Sung-Ho Hammond); the page shows first name and last initial. Check them against the Google profile before anyone outside sees the page.
- The card words: his outcomes, plus their lighting page (ambient, task, and accent light; ceilings and finishes) and their Palladiom keypad photo (the four engraved scenes).
- The process words: his four stages and their lighting page (design first, fixture specification, Alpine Electric as the electrical crew).
- Photos, all from their site: hero `home-theater-with-brown-leather-couches.jpg`; work `living-room-and-kitchen-with-orange-accent-furniture.jpg`, `upstairs-lounge-with-guitar.jpg`, `gazebo-with-projector-screen.jpg`; about `DSC_5028.jpg`; process `about-us-5.jpg` (their truck in downtown Truckee). The Lutron and Ketra vendor photos on their lighting page were skipped: not their work.
- Body face: Helvetica on their site, which is not a Google font, so Poppins stands in. Headings are Newsreader (the light serif rule for high-end residential).
- No `pattern` block: his A B A C A B A background colors are not settled, so the page keeps the PHA look (white, mist, dark photo, white, navy close).
- Top menu removed on purpose: one page, one service, one thing to do. The form sends nothing. It is a render.

## Big misses the AIOS would raise (his to take or leave)

1. **No Google rating anywhere on their site.** He asked for the review banner right under the button; it cannot be drawn without the number. One Google profile pull (`python scripts/research.py google "Liberty Bell Smart Home 1522 Lincoln Way Auburn"`, about 4 cents, his go) fills `hero.trust` and `reviews.rating`.
2. **None of their reviews is about lighting.** The three used are alarm, stereo, and safety. Two reviews from lighting clients, pulled from the Google profile, would carry more than all four on their site.
3. **No photos of a lighting job and no photo of the owner.** The hero is their theater, the portfolio is three rooms, the about photo is the crew. Three lit rooms they did (a kitchen at dusk, a keypad on the wall, a lit exterior) and one photo of Mike would make the page theirs.

Also open: the form ends on a marked box, not their calendar; the page phone is the Auburn store, and their truck photo in the process band shows the Truckee number faintly.

## Not done

- The Loom B and A cut and the email to Mike.
- The Google profile pull (costs money; waits on his go).
- The calendar behind the form.
