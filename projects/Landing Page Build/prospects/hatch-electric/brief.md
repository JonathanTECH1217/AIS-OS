# Hatch Electric: the "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom audit of hatchelectric.com. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder, built by `scripts/prospect_page.py` from `spec.json` (their logo and five photos in `assets/`; the raw downloads in `assets/_raw/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/hatch-electric" --port 8795`, then http://127.0.0.1:8795/
- Renders: `projects/Landing Page Build/renders/2026-10-06/hatch-electric-after-1440.png`, `-fold-1536.png`, `-390.png`.
- The site it rebuilds: https://www.hatchelectric.com/ (a six-slide home page; the slides are the only lighting photos on the site).
- The Loom: https://www.loom.com/share/d7c4866a24bc46df874651dba6744721 (3 minutes 48 seconds). Its file and word-timed transcript are in `media/looms/d7c4866a-increase-landing-page-conversions-for-lighting-c/` (not in git).
- The company: 921 Eloise Ave, South Lake Tahoe, CA 96150. 530-541-3035. office@hatchelectric.com and chip@hatchelectric.com are on their contact page. Chip Henderson is the president (their about page: apprentice in 1976, president since 2002).

## What he said, and what the page does

Times are from the Loom. His words are from the laptop's transcript.

| At | His words | On the page |
|---|---|---|
| 0:23 | "I'm just gonna do one landing page and it's gonna be for lighting control." | One service: lighting control. Nothing about remodels, maintenance, or commercial work on the page except as links at the foot. |
| 0:41 | "We're going to take this gold color and we're going to say this is the primary." | Their gold (`#C19C36`, the nav links and the foot band) is the eyebrow, the stars, and the step numbers. Their darker gold from the same stylesheet (`#B78C00`, the fixed header) fills the buttons and the cards, because white words read better on it. |
| 0:45 | "As far as the header, reduce the size of that a little bit and make it high contrast on white background." | An 80px white bar: their mark in ink, the phone, one gold button. Their site's header is black with a grey logo about 90px tall. |
| 0:53 | "The hero section is going to be a black overlay on top of, let's just keep this photo. I like this photo." | Slide 1 of their home page (the bedroom with the fire), the one on his screen as he said it, under a dark scrim. |
| 0:58 | "White text on there that says something like lighting control installation in California. If you're in the San Francisco Bay Area, we could say like San Francisco or Oakland or wherever your offering is." | h1: "Lighting Control Installation in South Lake Tahoe". Their city is on the contact page and the about page; they are not in the Bay Area. |
| 1:10 | "Right above that, put an eyebrow that says directly who you're targeting. Is it for residential homeowners... or B to B being the architect, builder, or designer?" | Eyebrow: "For Lake Tahoe homeowners". The trade partners get their own band lower down. |
| 1:21 | "A few lines of copy right below the headline that are going to talk about the offering a little bit in terms of outcome for the prospect." | Two sentences: every light and shade from one keypad, a remote, or a phone; scenes set once and there every day. Built from their own planning page (keypad, remote, tabletop, phone). |
| 1:30 | "Big call to action button that says book a meeting or book an appointment. This takes you to a four-stage booking form: first name, email, phone number, and brief message that disqualifies anybody just contacting your company for TV mounts." | "Book a meeting", three times down the page (header, hero, close). It opens the four-step form: first name, phone, email, message. The message hint asks for the rooms and whether it is a new build. |
| 1:43 | "Right below that would be a little banner for Google Reviews." | A reviews band straight under the hero. Their site shows no reviews and no rating, so it is three marked empty boxes and no rating line under the hero button. |
| 1:48 | "The services that get included as far as outcomes the prospect feels... the keypad customizability where you can control the lighting scenes, the engravings on the keypads, the finishes on the keypads, what apertures do they want... the controlled color temperatures benefiting their circadian rhythm and reducing stress." | Four gold cards with icons: Keypads built for your rooms; Engravings and finishes; Apertures and trims; Light that follows the day ("tuned to your body clock"). |
| 2:28 | "An about section, a shot of you, the owner, or just a shot of the team, and then a little bit of a description about what the company is, what they stand for." | "Serving South Lake Tahoe since 1962" with three sentences cut from their about page. The photo is a marked empty box: their site has no owner or team photo. |
| 2:42 | "Our process, this speaks directly to the trade partners, architect, builder and designer, just showing that you understand everything from design consultation to the installation, ongoing service management." | A dark band, eyebrow "For architects, builders, and designers", four numbered steps: design consultation, lighting plan, installation and programming, ongoing service. Their shaded-room slide sits behind it. No button in this band. |
| 2:59 | "Portfolio, so like a few photos of really good work that you install relative to the trade per landing page." | Three photos from their home page slider, cut to the grid: the kitchen, the living room, the bathroom. See miss 1. |
| 3:07 | "An FAQ, and this just helps when people are searching for your stuff... a few things about that specific service." | Five questions on lighting control, one line each, built from their home controls, remodel, and planning pages. |
| 3:22 | "Internal linking to other high-ticket services like your whole home audio, your dedicated home theater, and that sort of stuff." | Three link cards to the pages they have: motorized shades (home controls), remodels and retrofits, planning and consulting. Their site has no audio or theater page. |
| 3:28 | "Below that would just be a secondary call to action that links directly back to the booking form." | The close band: "Start with a conversation about your home", one button, same form. |

## Where every fact came from

- Logo, gold (`#C19C36`, `#B78C00`), phone, address, email addresses, hours: their public site, read 2026-10-06 (`projects/research/hatch-electric*/site.json`, seven pages).
- The logo on the page is their grey mark with the grey refilled in ink and the strokes thickened one pixel. Same shape, same lockup, same alpha. The grey original would not read on the white header he asked for.
- 1951, Guerneville, 1962, Chip Henderson's dates, "clients originally established by Leonard Hatch": their about page, word for word where it counts.
- "Factory certified Lutron designer and installer, HomeWorks QS, RadioRA 2": their services page. In the footer only (his rule: credentials nowhere else). "A California corporation" is in their logo.
- The hero photo and the three work photos: the home page slider (`1-BEDROOM.jpg`, `2-KITCHEN.jpg`, `4-LOBBY.jpg`, `3-BATHROOM.jpg`, found in their Divi stylesheet). The process band photo is slide 6 (`6-SHADES-2.jpg`).
- The sub line, the FAQ answers, and the card lines: his words for the outcomes, with the facts (keypad, remote, tabletop, phone; wireless retrofit; occupancy sensors; shades and temperature control) from their home controls, remodel, and planning pages. Nothing on the page names a brand, a price, a year founded beyond their own, a rating, or a number of jobs.
- Fonts: their site sets none (Divi's default), so Newsreader for the headings (his light serif rule for high-end residential), Manrope and Poppins for the rest.
- The city: South Lake Tahoe, from their contact page. 530 is the area code.
- The form sends nothing. It is a render. The "Pick a time" step shows a marked box where their calendar would open.

## Big misses the AIOS would raise (his to take or leave)

1. **No photos of their own work.** Every lighting photo on their site is a slider image; the file names on their inner pages (`Kit_Cell_Preset_hi`, `DinRmLV_Dim-Hi`, `Bath_Modern_Dim-Hi`) read like Lutron's library, not Tahoe homes. The three in "Our work" are those slides. For a high-ticket home job in a lake town, three real rooms they lit would carry more than any copy. Ask them for five photos before this page meets a buyer.
2. **No reviews and no rating anywhere on their site.** The band he asked for under the hero is empty boxes. Sixty years in one town and nothing a buyer can read. Their Google profile was not pulled (no spend on this render); if it holds reviews, three with a first name and a last initial go straight in, and the rating line under the hero button with them.
3. **No face.** The about band has no owner or team photo; the site has only the office sign and the building. Chip Henderson has been there since 1976. One photo of him, or the crew by the vans, fills the box that does the most work on the page.

## Not done

- Their Google profile pull (`research.py google`, about 4 cents) for the rating and the reviews.
- The second Loom (him going through the page and the form) and the email to Chip.
- The engine fixes the header logo at 46px tall, which makes a wide lockup's wordmark about 9px high; a logo height setting in the spec would let their mark sit larger on the white bar.
