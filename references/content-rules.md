# Content rules: what stays in a cut and what goes

Jonathan's rules for any video the clone cuts. The social content skill (`.claude/skills/social-content/SKILL.md`) reads this before it cuts or picks anything, and adds a rule in his words the day he says it. His to edit.

## The rules

1. **Cut what does no work, and cut what is not accurate** (Jonathan, 2026-10-05): "When the things I'm saying don't do a lot of work as far as keeping people engaged or the information that I'm saying is kind of inaccurate, it should just be cut."
2. **The owner's version never calls them a prospect** (Jonathan, 2026-10-05): "take out the part where it talks about them being my prospect and just talk about the changes that I'm going to make to the website."
3. **No ums, erms, or pauses** (Jonathan, 2026-10-05): "cuts between ums and erms, pauses."

4. **No icons dropped on the picture** (Jonathan, 2026-10-05, on OpusClip's shorts): "It's adding like really weird icons in wrong places like hammers and trophies." No emoji, no stickers.
5. **One idea a short** (same day): "ideas aren't centralized." A short holds one point and nothing beside it.
6. **Say who it is for** (same day): "it's supposed to be speaking to home service companies." The first line names them.
7. **Before and after is a format he wants** (same day): "giving them like a before and after of the website would be a good one."
8. **Under five minutes; three is the mark** (Jonathan, 2026-10-06, for Loom B and A): "we keep these videos under five minutes for retention. Three minutes is really really good." `scripts/loom_ba.py cut` refuses over five and says so over three.
9. **A change shows the second he names it** (same day): "every time I say something that changes, we see that change happen to their website." The change's time in the plan is the first word of it.
10. **His face is in the piece, on the same cuts** (same day): "This should include my face with the same cuts as well." The Loom's face bubble is cut with his voice, round, bottom left, under the captions (`face` in a Loom B and A plan).
11. **The live edits land at the render's size** (same day): "all of the changes should match render frame 10 as they are changed so the 9 to 10 jump does not feel fabricated for the size adjustments." Each change on their live page takes the finished render's own size, font, and spacing as it lands, and the words sit at the render's height, so the swap to the render changes the page, not the sizes.
12. **Only the final version of a change shows** (Jonathan, 2026-10-07): "It should only be the final adjustment that gets shown in the final cut this goes for any change." He tried two eyebrows on Q Northwest; the cut shows the last one, at the time he first names it (`scripts/loom_ba_rules.py`).
13. **The picture follows his hand** (same day): "when I talked about the pendant picture that was in the carousel, it didn't follow to the next photo over." When he clicks to another photo, slide, or tab on their page, the cut does too (a `click` step).
14. **Their header stays theirs until the swap, then the render's matches it** (same day): "When I said something about the four stage booking form, it turned the header section white." A dark header stays dark in the render (`header.dark` in the spec), and the render's header is laid on their page the first time he names the header.
15. **The header has a menu** (same day): "The header should also have like the basic menu elements like home, services and the other basic stuff."
16. **Real work photos before export** (same day): "I like when the our work section has actual photos before export." Their own photos (site or Google profile), never a stock or blank card.
17. **Google on every review** (same day): "The review sections should have the Google logo every time. Google reviews carry more trust and authority than just any review."
18. **The review banner sits under the button on every page** (same day): "Right below the call to action, just like on the PHA page, should be the Google Review stars and the rating."
19. **Review section and review banner are two things** (same day): "when I say review section, that's the review section. And when I say review banner, it's just that little five star ... and then the star rating from however many reviews right below the call to action."
20. **The second call to action says "Start your project"** (same day).
21. **The hero is white words on a dark ground** (same day): "for the hero, I feel like white text on a dark background definitely carries."
22. **The eyebrow is a shade of the main brand color** (same day): "The eyebrow should always be a variant of the primary color as well." Lightened until it reads on dark.
23. **Three benefit cards, the strongest three** (same day): "should just be three cards universally, and probably the strongest three in terms of the outcome that the end user probably raves about."
24. **The booking lands on the owner's calendar** (same day): "when I say something about the booking form that goes into the calendar, there should be a visualization that when booking happens goes straight to Google Calendar for the owner." His first "calendar" after the form shows the sent screen with the booking dropping into a week view.

## How the clone applies them

- It works from the word-timed transcript (`scripts/studio_transcribe.py`), so every cut is a time and a reason.
- "Does no work": a repeat of something just said, a false start, a line that trails off, talk about the making of the video. "Not accurate": anything that is not true of what is on screen or on file, and any guess about the other company stated as fact.
- A stretch where the screen is the point (a form being filled in) stays whole even when little is said.
- Every cut is written to a log beside the video (`<name>.cuts.md`): from, to, why, and the words that went. He reads the log, not the timeline. A cut he disagrees with goes back in on his word.
- When unsure whether a line is accurate, the clone cuts it and says so in the log; it never rewrites or dubs his words.

## The before-and-after short (first made 2026-10-05)

`media/looms/momentum-2026-10-05/short-before-after.mp4`, 44 seconds, 1080x1920, made on the laptop with ffmpeg from the two Momentum Looms. Its shape, his to change:

- Two panels. The old page on top with a red BEFORE tag, the rebuilt page below with a green AFTER tag. The panel he is talking about plays; the other is a dimmed still.
- The page only: the browser bar, the task bar, and his face bubble are cropped out. While the form is open the lower panel moves in closer so the whole form shows.
- Captions between the two panels, in Monarc Studio's caption style (Montserrat Black, his words blue, the spoken word white), two or three words at a time.
- His own words, in his order: the line to home service companies, then the before points, then the after points. The log beside the file lists each stretch and its time in the Looms.

## First use

2026-10-05, the Momentum owner's version: `media/looms/momentum-2026-10-05/owner-cut-tight.mp4`, 4:25 from 6:05, with `owner-cut-tight.cuts.md`. Made on the laptop; OpusClip's filler-word switch had taken out only about 2 seconds of the same video (`references/opusclip.md`).
