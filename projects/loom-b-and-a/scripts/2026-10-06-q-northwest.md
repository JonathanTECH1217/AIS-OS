# Director's script: Qnorthwest, lighting control

Jonathan, 2026-10-06: "I want you to make a director's script prior to sending this into the editing engine. Because this should be step by step making the adjustments that the prospect sees based on what I'm saying, one by one."

- **Loom:** https://www.loom.com/share/62f8953c51b949cfbdcabc6ea163c362 (3:44, his screen held on qnorthwest.com/residential the whole time)
- **Live page edited:** https://www.qnorthwest.com/residential
- **Render:** `projects/Landing Page Build/prospects/q-northwest/` (lighting control, Seattle, built in this Loom's section order)
- **Edit plan:** `projects/loom-b-and-a/plans/2026-10-06-q-northwest-A.json`
- **Cut:** `media/loom-ba/2026-10-06/q-northwest/q-northwest-loom-ba.mp4`, 2:50, variation A (the steps). Under the three-minute mark.
- **Face:** his Loom bubble, crop `244:244:32:745` from a full 1920 x 1080 frame, same cuts as his voice. The Loom is about 30 frames a second, so the bubble moves smoothly.

## The shape

**Act one, their page changes as he talks (0:00 to 1:23 of the cut).** Their live residential page, edited in the browser one change at a time. Each change fades in over a third of a second on the first word that names it, at the render's own size, font, and spacing (rule 11).

**Act two, the rebuilt page (1:23 to the end).** When he says "below that section", the picture becomes the finished lighting control page, and it moves to each section the second he names it.

## The beats

| # | His words (Loom) | Video | What the viewer sees |
|---|---|---|---|
| 0 | 0:04 "Hey, this is Jonathan" | 0:00 | Their page as it is: the dark header, the carousel on the kitchen slide, "Residential" and the long paragraph below it |
| 1 | 1:00 "starting off with this carousel" | 0:50 | The carousel turns to their own outdoor room slide (the fireplace and the lit porch), the one the render uses |
| 2 | 1:04 "make that a little bit bigger to cover the top of the fold" | 0:53 | The photo grows from 450 to 605 px tall and fills the screen down to the render's hero line |
| 3 | 1:11 "lighting control installation in your area" | 0:59 | The headline moves onto the photo: Lighting Control Installation in Seattle, white, the render's light serif at 72 px, centered, the photo darkened behind it |
| 4 | 1:19 "for residential" | 1:06 | An eyebrow above the headline: FOR RESIDENTIAL, small light blue capitals |
| 5 | 1:22 "lighting control for homeowners" | 1:07 | The eyebrow becomes LIGHTING CONTROL FOR HOMEOWNERS |
| 6 | 1:26 "a little bit of text... one to two sentences" | 1:10 | Their 39-word paragraph drops to the render's 21 words: keypads, scenes, and schedules; new construction and remodels |
| 7 | 1:37 "big call to action that says book a meeting" | 1:19 | A slate Book a meeting button under the copy |
| 8 | 1:43 "below that section" | 1:23 | The finished first screen (the swap). He talks about the review bar here; see "Left for you" |
| 9 | 1:53 "break down the next section into the services" | 1:31 | What lighting control gives you: Keypads, Automation, Voice and app, Customizable |
| 10 | 2:12 "an about us section" | 1:47 | About us: the team photo, since 2011, more than 30 people who know Lutron |
| 11 | 2:46 "a reviews section" | 2:04 | What our clients say: three boxes marked empty |
| 12 | 2:48 "if you're targeting architects, designers, and builders" | 2:06 | How we work with your project: the four steps for architects, designers, and builders |
| 13 | 2:56 "then below that an FAQ" | 2:12 | Questions we get asked |
| 14 | 3:00 "your secondary services" | 2:16 | Everything else we install: six linked cards |
| 15 | 3:11 "the Lutron diamond dealer credential... the footer" | 2:25 | The closing band and the footer: "Lutron Diamond Dealer." |
| 16 | 3:19 "new construction and remodel... baked into the copy" | 2:30 | Back to the first screen, where the line under the headline says new construction and remodels |
| 17 | 3:26 "if this is an actual project here... monochrome" | 2:36 | The process band with that dark modern home behind it |
| 18 | 3:35 "But besides that... make a lot more money through Google" | 2:43 | The finished first screen again, to the end |

Act one: 7 beats (24 engine steps; the extra steps lay the words over the photo, darken it, load the render's fonts, and set the button under the copy, so the live page lands at the render's sizes). Act two: 11 beats.

## What was cut, and why

| Loom | Why |
|---|---|
| 0:00 to 0:04 | Silence before he starts |
| 0:43 to 0:45 | "So starting off": a lead-in said again a few lines later |
| 2:15 to 2:30 | "So like they go from here a section to exactly what it is to offer, to broken down how the service kind of operates in their home... and then right below that": a recap of the order that comes out garbled; not accurate as said |
| 3:16 to 3:19 | A pause and a "mm" with nothing in it |
| 3:42 to the end | "Talk to you later": the sign-off; the piece ends on "make a lot more money through Google as a channel" |

Every "uh" and "um" and every pause over half a second is out besides. Captions fix three misheard words: "yet?" to "yet.", "Loud Speaker" to "Loudspeaker" (James Loudspeaker), "monogrome" to "monochrome".

## Every live change lands at the render's size

The last live state (the button) against the first render state: the eyebrow at 222 px from the top, the headline at 268 px on two lines, the copy at 445 px on three lines, the button at 576 px, each at the render's size and font. What changes at the swap is the header bar (their tall dark bar, the render's white one with the phone and a second button), the photo's top edge, and the grey band under the hero, which is the page itself changing. To get there the plan lays their "Residential" block over the carousel, takes its white ground off, darkens the photo the way the render does, and moves the button under the copy.

## His notes (2026-10-07)

| His note | Loom second | Change | Where |
|---|---|---|---|
| "I did two adjustments for the eyebrow. It should only be the final adjustment that gets shown." | 79.0 | One eyebrow step, "Lighting control for homeowners", at his first eyebrow word | plan; `scripts/loom_ba_rules.py`; rule 12 |
| "Never got the render adjustment for the gold stars below the book a meeting button." | 110.6 | The render's hero now has the Google stars and "4.9 on Google from 25 reviews" under the button; the hero step at 1:42.6 shows it | engine (`review_banner`); spec (`google`); rule 18 |
| "The header section white" (said on VME) | | Dark header kept, with a white logo | spec (`header.dark`); rule 14 |

## Left for you

- **The review bar is not on screen.** At 1:44 he asks for "a little bar... your review count... the gold stars". Their site shows no rating, so the render left it out; the finished first screen holds while he says it. Needs their Google count.
- **Two things he does not name, done with the headline:** the centering and the darker photo. The render has both, and without them the swap would jump (rule 11). Say if either should wait for its own words.
- **The photo:** at "this carousel" the picture turns to their own outdoor slide, the one the render uses. All three slides are iStock photos (the file names say so). Ask for real project photos before this goes out.
- **The reviews section shows three empty boxes.** Their site has no reviews. Pull three from their Google profile before this goes out.
- **No form count and no ask in this Loom.** He never counts the form fields, so there are no form steps. There is no "fifteen minutes": the ask goes in the email.
- **"Talk to you later" is out** (about one second). Say if it goes back in.
- **Engine notes, not fixed (`scripts/loom_ba.py` is off limits):** the `font` kind sets its styles a second time five seconds later, which once undid the eyebrow's size; the plan loads the fonts on the page title instead. The `cta` kind put the new button straight under the headline, because their copy sits in another block; a `css` step moves it under the copy.
- **Not built:** the trailer version (B).
