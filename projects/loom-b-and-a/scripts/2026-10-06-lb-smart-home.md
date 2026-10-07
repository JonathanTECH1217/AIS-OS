# Director's script: Liberty Bell Smart Home, the cold audit

- **Loom:** https://www.loom.com/share/0fd362d61f2942178544367a6491544a (4:29, his screen held on lbsmarthome.com/residential-solutions#lighting-and-shades the whole time)
- **Render:** `projects/Landing Page Build/prospects/lb-smart-home/` (one lighting control page, built in this Loom's section order)
- **Edit plan:** `projects/loom-b-and-a/plans/2026-10-06-lb-smart-home-A.json`
- **Cut:** `media/loom-ba/2026-10-06/lb-smart-home/lb-smart-home-loom-ba.mp4`, 3:23, variation A (the steps). Under five; over the three-minute mark.

## The shape

**Act one, their page changes as he talks (0:00 to 1:25 of the cut).** Their Residential Services page, edited one change at a time. Each change fades in over a third of a second on the first word that names it.

**Act two, the rebuilt page (1:25 to the end).** When he finishes the eyebrow line, the picture becomes the finished first screen; from "below that, a services section" it moves to each section the second he names it, and ends on the first screen.

## The beats

| # | His words (Loom) | Video | What the viewer sees |
|---|---|---|---|
| 0 | 0:00 "Hey, this is Jonathan... I used to work for architects, builders, and designers" | 0:00 | Their page as it is: "Residential Services" over a bright living room, twelve service icons under it, no button |
| 1 | 1:09 "Background would be something like... high end home" | 0:51 | The living room becomes their own home theater: dark wood, lit sconces, star ceiling |
| 2 | 1:40 "the blue would be a good color for the call to action button" | 1:10 | A logo-navy Book a meeting button appears under the headline, at the render's size and face |
| 3 | 1:44 "the headline would be something like lighting control installation in downtown historic Auburn" | 1:14 | The headline becomes Lighting Control Installation in Downtown Historic Auburn: the render's light serif, 72 px, three lines, at the render's height; the button drops to the render's spot |
| 4 | 1:52 "the eyebrow right above that being something like for luxury homeowners" | 1:21 | FOR LUXURY HOMEOWNERS in their bright blue above the headline |
| 5 | 2:02 (end of "homeowners") | 1:25 | The finished first screen: the same headline, eyebrow, and button in the same places, plus the line of copy, the short header with the phone, and the darker photo |
| 6 | 2:03 "a services section... the outcomes" | 1:26 | Four navy cards: custom keypads, voice control, adjustable color temperature, any fixture you want |
| 7 | 2:32 "an about section... your team" | 1:49 | The crew outside the office, "A family company since 1981" |
| 8 | 2:44 "our process... design consultation all the way up to the installation" | 1:59 | Four steps for architects, builders, and designers, their truck behind |
| 9 | 3:08 "your reviews, three reviews" | 2:21 | Three quotes from their home page |
| 10 | 3:31 "a secondary link that goes to some other high-ticket services" | 2:36 | Three linked cards: whole home audio and video, dedicated home theater, home networks |
| 11 | 3:43 "A portfolio... a few pictures that show your best work, just three" | 2:47 | Our work: the kitchen, the upstairs lounge, the patio |
| 12 | 3:53 "a secondary call to action" | 2:52 | The closing band: Free lighting consultation |
| 13 to 16 | 3:56 "first name, email, phone number, and brief message" | 2:56 to 2:57 | The form opens and steps through its four questions on his count |
| 17 | 4:16 "I have 15 minutes available sometime this week" | 3:15 | The finished first screen again, to the end |

## What was cut, and why

| Loom | Why |
|---|---|
| 0:00 to 0:01 | Before he starts |
| 0:02 to 0:03 | "Uh, you don't know me yet?": a question that does no work |
| 0:13 to 0:16 | "Over the course of three minutes, if you want to tune in": the cut runs 3:23, so the line is not accurate |
| 0:57 to 1:06 | Talk about the making of the video: "I'm going to make a few suggestions, let's just say this one" |
| 1:30 to 1:39 | The background said a second time, "the header would be the same", and "with this" trailing off |
| 1:55 to 2:00 | "Featured in X Magazine or": their site names no magazine; the page shows the line he lands on |
| 2:18 to 2:20 | "Just all of this sort of good stuff you guys have" |
| 2:30 to 2:31 | "All of that sort" trails off |
| 3:21 to 3:29 | "So that just peace up the conversion rate for that offering there": a line that does not land |
| 3:44 to 3:46 | "Does work. Good work.": a false start; the next line says it plainly |
| 3:49 to 3:52 | "Just three of your best pictures is all you need": just three said a second time |
| 4:26 to the end | The sign-off: "So, Mike, you know, this is Jonathan" (the ask ends on "go over this briefly with you guys") |

Every "uh" and "um" and every pause over half a second is out besides. Captions fix "hour" to "our" and drop the false start "bre".

## Rule 11, the swap

The last live frame (1:21) against the first render frame (1:25), both at 1440 x 900: the headline is 72 px Newsreader Light, the same three line breaks, its top at 246 px on both; the eyebrow sits at 200 px on both; the button is 260 x 64 at 598 px on both, in the render's Montserrat. What changes at the swap is the page itself: their header and showroom bar give way to the short header with the phone, the line of copy fills the gap above the button, and the photo darkens and grows to the render's frame.

Two of the act-one steps are sizing only, landing with his headline at 1:14, not changes of his: the headline held to the render's width (so it breaks in three lines, not two) and the block set at the render's height. Their headline was already centered, so "center" changes nothing he did not name.

## Left for you

- **Their live page shows a robot check.** lbsmarthome.com answers the headless browser with "Press & Hold to confirm you are a human". The clone does not get around it. Act one runs on a still copy of the same page from today's research read (`projects/research/lb-smart-home/site.html`), saved at `media/looms/lb-smart-home-ba-2026-10-06/live/residential-solutions.html`: scripts out, their styles and photos loaded from their site. It matches your Loom frame for frame. Two working additions show nothing until your words: an empty link under the headline where the button is built (their hero has none), and the render's Montserrat under a name of its own.
- **The Google review banner is not drawn.** At 3:17 you ask for it right under the button; their site states no Google rating, so the render has none and the picture holds on the reviews. A Google profile pull (about 4 cents, your go) adds the line and the stars.
- **"Links directly to your calendar" holds on the form's last step.** The render's calendar box shows only after a send, and the engine steps the form 1 to 4 only. The drip sequence you name is not a page thing; the picture holds there too.
- **The four form beats run under a second apart**, because you count them fast. They read as a flick through the form.
- **The sign-off says "Mike".** It is cut. Their site names Mark Buzzard as President and CEO; check who Mike is before the email goes out.
- **Engine notes, nothing changed in the scripts:** on their live page a tracker frame breaks the hero read (it hands back no box); a `cta` aimed at an empty element blanks its own words; and a face their CSS names but never loads is skipped by the font check, so the button fell back to Arial until the face was loaded under its own name.
- **Not built:** the trailer version (B), and the email draft.
