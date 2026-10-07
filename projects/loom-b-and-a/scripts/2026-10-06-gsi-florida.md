# Director's script: Gold Standard Integration (GSI, Jupiter, FL)

- **Loom:** https://www.loom.com/share/65e163700465418b8f6705154b8fe34d (7:06, his screen on gsi-fl.com, the home page, the whole time; silent from 1:53 to 3:51)
- **Render:** `projects/Landing Page Build/prospects/gsi-florida/` (words in `spec.json`)
- **Edit plan:** `projects/loom-b-and-a/plans/2026-10-06-gsi-florida-A.json`
- **Cut:** `media/loom-ba/2026-10-06/gsi-florida/gsi-florida-loom-ba.mp4`, 4:12, variation A. Under five; over the three-minute mark.

## The shape

**Act one, their page changes as he talks (0:00 to 1:33 of the cut).** Their live home page, edited in the browser one change at a time. Each change fades in over a third of a second on the first word that names it. Their hero is a drone photo with no headline, no words, and no button, so each new part lands where the render puts it, at the render's size and font.

**Act two, the rebuilt page (1:33 to the end).** At "now that we have the hero section" the picture becomes the finished page, and it moves to each section the second he names it.

## The beats

| # | His words (Loom) | Video | What the viewer sees |
|---|---|---|---|
| 0 | 0:00 "Hey, this is Jonathan... architects, builders and designers" | 0:00 | Their page as it is: the plan-room drawing across the top, the nav, the drone shot of a lit plaza at night, nothing on it |
| 1 | 1:04 "your header up at the top, about seventy pixels... black text" | 0:49 | The drawing goes; the header becomes a white 80 px bar, the nav in black |
| 2 | 1:15 "high contrast dark background" | 0:58 | The photo darkens and takes the render's height and crop |
| 3 | 1:24 "we'll just work with this blue" | 1:07 | A button in their blue, `#008AFC`, with their own words: Book Now |
| 4 | 1:27 "book a meeting button" | 1:09 | Book Now becomes Book a meeting |
| 5 | 1:30 "lighting control installation in the area" | 1:12 | The headline: Lighting Control Installation in Palm Beach County, in the light serif |
| 6 | 1:33 "put an eyebrow section above that" | 1:15 | FOR PALM BEACH COUNTY HOMEOWNERS in light blue capitals |
| 7 | 1:45 "a couple lines of copy right below that headline" | 1:26 | Keypad scenes, phone and voice, light that warms and cools with your day |
| 8 | 3:51 "now that we have the hero section" | 1:33 | The finished first screen: the white header with their name and phone, the same hero |
| 9 | 3:59 "the services offered with lighting controls" | 1:37 | Three cards: keypads with your scenes, your phone and your voice, light that follows your day |
| 10 | 4:31 "an about section, a picture of you or your team" | 2:09 | About: a family business in Jupiter, the marked box for the team photo |
| 11 to 14 | 4:53 "four stage booking form... first name, email, phone number, a brief message" | 2:20 to 2:24 | The form opens and steps through its four questions on his count |
| 15 | 5:22 "our process" | 2:47 | The four stages for architects, builders, and designers |
| 16 | 5:47 "actual photos of the team members" | 3:05 | Back to the about band and its empty photo box |
| 17 | 5:56 "portfolio as far as the work" | 3:13 | Our work, three marked boxes |
| 18 | 6:00 "reviews alone would be a good section" | 3:17 | What our clients say, three marked boxes |
| 19 | 6:09 "another services page" | 3:24 | Four linked cards: EV charging, panel upgrades, generator inspection, electrical wiring |
| 20 | 6:30 "a secondary call to action" | 3:43 | The closing band: Start with a design consultation |
| 21 | 6:36 "if you did this and put a little bit of ad spend behind it" | 3:45 | The finished first screen again, to the end, under his ask |

## What was cut, and why

| Loom | Why |
|---|---|
| 0:24 to 0:33 | Words missing in the recording ("I just want to provide. For you as I can right now"), and "about three minutes" and the guarantee are not true of this cut |
| 1:02 to 1:04 | A false start ("you would want your headline"); the headline comes at 1:30 |
| 1:51 to 3:51 | The line trails off ("and then right below that, you would have"), then "yeah" and the silent gap |
| 3:53 to 3:55 | A lead-in with nothing in it ("talking about lighting control") |
| 4:43 to 4:53 | A Google review line under the button: the render has none, since their site states no rating; reviews come again at 6:00 |
| 5:39 to 5:45 | Trails off, then "here's the impressive portfolio, I like this": their portfolio is four placeholder client logos, so not accurate |
| 6:31 to 6:36 | Trails off ("besides that, I would say, that's about it for this") |
| 6:53 to 6:54 | "This is Jonathan checking out" said before the ask; the ask is the close |

Every "uh" and "um" and every pause over half a second is out besides. Captions fix three words: "flighting" to "lighting", "heroes" to "hero", and "thin" dropped. His offer stays: "If you don't want to do it, I'd be happy to do it" at the top, and "I have availability this week. Shoot me an email" at the end.

## How act one was made

- Their hero has no headline, words, or button, so the engine's headline, eyebrow, and copy steps had nothing to aim at. Each new part is a text block from lower on their page ("What We Offer", "Electrical Solutions", a card line, a Learn More button), rewritten with the render's words and set at the render's spot by `css` steps.
- One `font` step at 1:04 loads the render's own three faces (Newsreader with its optical sizes, Manrope, Poppins) on a block below the first screen. Its line in the `.cuts.md` reads like a web address; it changes nothing on screen.
- The swap checks out (rule 11): in the last live frame and the first render frame the headline spans the same 297 to 1144 px, the button sits on the same line, and the eyebrow and copy are within 2 px. What changes at the swap is the header bar (their nav and cart become our name, phone, and button), which is the page itself changing.

## Left for you

- **Their yellow Shopping Cart stays yellow** in act one. It does not take the black text; it is likely Wix's own frame.
- **The services you named** (whole home audio, media distribution, networking) are not on their site, so the services band shows the four they do list while you say yours. Say if those lines go.
- **The form steps 2 to 4 run under half a second apart**, because you count them fast. They read as a flick through the form.
- **The face bubble is about six frames a second**, the same as PHA: Loom stores the recording at a variable rate.
- **Not built:** the trailer version (B).
- **For the engine, not changed here:** a `text` or `headline` step on an empty block leaves it blank, and a `font` step runs itself again five seconds later and undoes the letter spacing set after it. Both were gone around in the plan.
