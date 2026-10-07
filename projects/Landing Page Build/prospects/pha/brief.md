# Performance Home Automation (PHA): the "after" page

A render of one landing page, built 2026-10-05 from Jonathan's Loom review. Not their live site and not pushed anywhere.

**The standing rule still holds:** this company is never named in Monarc's own pages, emails, or posts, and pha.systems is never linked (`CLAUDE.md`, the landing page skill's house rules, `references/mycopy.md`). This render carries their name because it is their own page. It stays on this laptop. No short, template, or post has been made from it.

- The page: `index.html` in this folder (their logo and photos in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/pha" --port 8791`, then http://127.0.0.1:8791/
- Renders: `projects/Landing Page Build/renders/2026-10-05/pha-after-*.png` (1440, 390, the form's sent screen).
- The page it replaces: `pha.systems/smart-lighting-control` (about 1,830 words on it, menus included; 272 here).
- The Loom: https://www.loom.com/share/46e5021a96ec4847b92cc3997b8dca31 (3 minutes 34 seconds, "Revamping Annapolis Home Automation Landing Page"). File, frames, and transcript in `media/looms/46e5021a-review/` (not in git).

## What he said, and what the page does

Times are from the Loom. His words are from the laptop's transcript.

| At | His words | On the page |
|---|---|---|
| 0:39 | "Take this headline smart lighting and home automation lighting control and make it into a single service... Lighting control installation in Annapolis." | h1: "Lighting Control Installation in Annapolis". One service. |
| 0:48 | "Center that, make it about 20% bigger, make this white text on a black background." | Centered, 68px (the Momentum render's was 56), white text. First built on plain black; changed the same evening on his note: "Throw the Georgian colonial photo, the one big estate shot from outside of the house, as the background to this landing page." The photo is from their About page (`assets/hero.jpg`), under a dark scrim so the white words can be read. |
| 0:56 | "An eyebrow... that speaks directly to the target audience saying Annapolis homeowner." | Eyebrow: "Annapolis homeowners", in their logo's green. |
| 1:02 | "A big call to action that just says book a meeting. That takes you directly through four step form that's first name, phone number, email, and a brief message." | One button, "Book a meeting", five times down the page. The form asks in his order: first name, phone, email, message. |
| 1:17 | "And that links directly to the owner calendar." | The sent screen has a "Pick a time" button. It opens a marked empty box: they have no calendar link on file. |
| 1:20 | "A review section right at the bottom because adding reviews right below the call to action increases conversion rate." | Reviews sit straight under the hero. Three marked empty cards: their page has no reviews. |
| 1:29 | "This solutions section... move it a little bit further down into a few of the services that are offered within lighting control... keypads, automation, and security... small icons with a brief card description." | Three green cards with white icons: Keypads, Automation, Security. Each line is cut from their own copy. |
| 1:51 | "And then maybe a little call to action below that." | A button under the cards. |
| 1:54 | "This call to action booking form here is getting replaced by the call to action up top." | Their on-page form is gone. |
| 1:58 | "A brief about us section, maybe a photo of the owner or the company, and then just a brief description." | About section: a marked empty photo box, two sentences from their About page, the Lutron Gold badge. |
| 2:08 | "A little bit of a portfolio grid. Let's just say three photos split into thirds, and then it says something like our work... lighting control photos installed in homes... This is a good photo. It looks a little bit stock, but you could definitely use this one photo across three of them." | "Our work", three photos in thirds. The first is the one he pointed at. The other two are real job photos from their About page, in place of the same photo three times. |
| 2:31 | "Why we work with lighting designers. So this could be a good thing to target would be your B2B partners... talk about our process in stages from design consultation to the plan drawings that we do to the wire scheduling... and then adjustments and installation." | A black band, "For architects, builders, and designers", "Our process" in four numbered steps, and a button. |
| 3:01 | "This kind of stuff doesn't really matter for a landing page, it should just be a secondary call to action down here." | Light layering, color temperature, shades, and the questions are gone. A closing "Free lighting consultation" band. |
| 3:13 | "The primary text is not really following any sort of brand design. The green in the PHA should be distributed as the primary color... the call to action button, the icon colors, and the card backgrounds. White text should be used on the green card backgrounds." | Green is the one color: the button, the cards, the icons, the eyebrows, the step numbers. See the first big miss for the shade. |

## His second round of notes, the same evening

| His words | On the page |
|---|---|
| "Companies targeting residential high-end should have a serif style font but it should be a light serif not too sharp and Victorian looking." | Headings are Newsreader Light. Their own sans (Manrope) stays on buttons, eyebrows, and labels. Three candidates are on one sheet for him to pick from: `renders/2026-10-05/pha-serif-samples.png`. |
| "Reviews from the Google My Business profile and post them to the reviews section." | Their Google profile read once through the Places API: 4.8 from 19 reviews, five reviews handed out. Three are on the page, the lighting one first. The rating also sits under the hero button. The one about pizza restaurants is left off a page for homeowners. |
| "Do not include last names in the reviews that are shown." | First name and last initial: Barbara N., Gene H., Michael M. |
| "Remove the Lutron gold star dealer badge. High-profile companies don't need to post their credentials anywhere besides in the footer." | The badge is gone. "Lutron Gold Star Dealer" and the "featured in" line are in the footer only. |
| "Stick that photo in the background of the [for builders, architects, and designers] section and stick the photo of all of their vans... into the background of the hero section." | Hero: their vans outside the shop, from their Google profile (`assets/hero.jpg`). Partners section: the front of the Georgian Colonial, the photo behind the hero of his own /av_marketing/ page (`assets/partners.jpg`), under a dark scrim. |

## His third round of notes, the same evening

| His words | On the page |
|---|---|
| "Remove the book a meeting from the Our Process section." | That button and its line are gone. Four buttons are left: the top bar, the hero, under the cards, the close. |
| "The Our Work section should pull from their Instagram. And be number four, pushing Google Reviews below it." | Order now: hero, the three cards, About us, Our work, the reviews, Our process, the close. **Not done: the Instagram photos.** Their public Instagram page hands no post or photo to a visitor who is not signed in (checked twice), and Instagram's terms forbid collecting it by machine. The three photos already there stay until he gives post links, the photo files, or their sign-in. |
| "The photo for the About Us section is currently sitting in my drafts. It has no recipient, and it is the attachment." | **Not found.** Proton Drafts through Bridge shows 26 drafts, the newest from 6:56 pm; none is without a recipient and none carries a picture. The marked empty box stays. |
| "Flip the hero and our process background photos." | Hero: the Georgian Colonial (`assets/georgian.jpg`). Our process: their vans (`assets/vans.jpg`). |
| "[Center] the portico columns in the background to pull the eye toward the book a meeting button... increase the scale of the photo slightly to increase the size of the home's ratio to the background." | The photo is 16 percent larger and slid so the portico's middle sits on the page's centre line. At 1536 wide the button sits between the columns, above the front door. Checked at 1440 and 1536; not tuned for a phone. |

**Fourth round:** "Move the our process section to number three. The our work section to number four, the about us section to number five." Order now: hero, the three cards, Our process, Our work, About us, the reviews, the close. On the About photo: "It is the draft from 6:56 with no recipient." The only draft from 6:56 pm in Proton is "Outreach: the proposal and the first invoice", addressed to jonathan@monarcbuild.com, with two PDFs and no picture. The photo box was still empty until he said "It is saved to downloads": the team photo (`Resized_20250904_160117.jpeg`, seven of them in company shirts at a trade show) is now in the About section as `assets/team.jpg`, in a wide box so nobody is cut off.

**Fifth round:** "In the green text at the top, have featured in Architectural Digest and Annapolis Home Magazine in the dark green text." Then: "Also say projects featured." The line at the top of the hero now reads "Projects featured in Architectural Digest and Annapolis Home Magazine" in the dark green, on a pale chip (dark green straight on the dark photo measures about 3 to 1). It replaced "Annapolis homeowners"; the footer keeps only "Lutron Gold Star Dealer." Later the same evening: "Take out the white background behind the text for the eyebrow." The chip is gone; the line is `#5E9A1F`, the deepest green of their hue that still reads on the dark photo (about 4.9 to 1; the button's green would be about 3 to 1).

**Sixth round:** "Pull a couple photos from his website real quick. Or a couple photos from his Instagram that are architectural." From their website, since Instagram gives nothing without a sign-in. Twenty photos read off their gallery, Lutron, lighting, and outdoor lighting pages: most are a maker's own marketing pictures (five carry Lutron's mark), product shots, or AI-made. "Our work" now shows three from their site: the living room he picked, the stairwell of hanging lights (About page), and a double-height lounge with long hanging lights (gallery page, `assets/work-lounge.jpg`), which replaced the small, soft kitchen photo.

**Seventh round:** "Remove the book a meeting button from the second section." The button under the three cards is gone. Three are left: the top bar, the hero, the close.

The first big miss below (no reviews) is closed by the second round. The second (white on the logo's green) and the third (AI-made pictures) stand. Their Google profile has ten real job photos, among them a room of hanging lights with shades down; any of them could replace the three in "Our work".

## Taste log lines that shaped it

From `Taste Log.md`, the 2026-10-05 Momentum line: one service a page; an eyebrow to the buyer, then the headline with the service and the place, centered; one button label down the whole page; the button opens a short form, one question a screen; the offering as three cards with icons; about and real work near the end; the ask again at the foot. Strike any that was meant for Momentum only.

## Where every fact came from

- Logo, faces (Manrope, Poppins), phone, address, "Lutron Gold Star Dealer", "Projects featured in Annapolis Home Magazine and Architectural Digest", the service areas, "since 2001": their public site, read 2026-10-05.
- Card lines and the four step lines: shortened from their page. "Wire schedule" is his term; its line is the AIOS's plain reading of it, his to correct.
- No review, rating, or owner's name is on the page because none is on their site or on file.

## Big misses the AIOS would raise (his to take or leave)

1. **White on their logo's green cannot be read.** It measures 2.1 to 1; body text needs 4.5. The button and cards use a deeper green of the same hue (`#3F7A17`, 5.2 to 1 with white). The logo's own green (`#8CC440`) is used only where it sits on black. If he wants the exact logo green on the button, the words on it would have to be black.
2. **There is no proof where he wants proof.** Their page has no reviews, so the three cards under the hero are empty. That is the spot he says lifts the rate most. Three real reviews from lighting clients are the first thing to ask them for.
3. **Many pictures on their live page are AI-made.** The file names say so ("ChatGPT Image ..."). For high-ticket work in real homes, a buyer who spots that stops trusting the rest. Two real job photos from their About page are used here; a lighting page should be all real jobs, plus the owner or the team.

## Not done

- A second Loom of him walking this page and the form.
- Anything for social content. Held because of the naming rule above.
- A template copy with a different logo and media.
