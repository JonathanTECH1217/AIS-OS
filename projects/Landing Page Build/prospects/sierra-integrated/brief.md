# Sierra Integrated Systems: the "after" page

A render of one landing page, built 2026-10-06 from Jonathan's Loom review. Not their live site and not pushed anywhere.

- The page: `index.html` in this folder, built by `scripts/prospect_page.py` from `spec.json` (their logo and six photos in `assets/`).
- See it: `python scripts/site_preview.py --root "projects/Landing Page Build/prospects/sierra-integrated" --port 8797`, then http://127.0.0.1:8797/
- Rebuild after a spec change: `python scripts/prospect_page.py all sierra-integrated`
- Renders: `projects/Landing Page Build/renders/2026-10-06/sierra-integrated-after-*.png` (1440, the 1536 fold, 390).
- The page it replaces: https://sierraintegratedsystems.com/solutions/lighting-design
- The Loom: https://www.loom.com/share/8c241718d7e543b0a3531d6d49266967 (4 minutes 36 seconds). Its file and word-timed transcript are in `media/looms/8c241718-increase-landing-page-conversions-for-lighting/` (not in git).
- Who: Reno, NV. Founder and Managing Member Keith Burrowes (their about page). The reviews name a Ryan who runs jobs. On the 2026-09-24 sweep (`projects/outreach/electrician-list-2026-09-24.csv`, row 5173, and the integrator LinkedIn list); no CRM id on file in the CSVs.

## What he said, and what the page does

Times are from the Loom. His words are from the laptop's transcript.

| At | His words | On the page |
|---|---|---|
| 0:17 | "Every single integrator website run by [the agency] looks exactly like yours. You have no differentiation." | One page, one service, their own founder, their own jobs, their amber. No template blocks. |
| 0:43 | "Your landing pages being segmented by service offering is a good thing. So we're going to go to your lighting design." | One service: lighting design. Everything else is a card at the foot. |
| 0:55 | "Decrease your header section in height by about 20%." | The hero is capped at 700 px (655 px on his 780 px screen); theirs fills the first screen. |
| 1:05 | "Center your headline, copy, and call to action text." | Eyebrow, headline, line, and button centered. |
| 1:14 | "A dark overlay with white text on it. This lightness on the right side is currently bringing my eye toward that." | Their own hero photo under one even dark scrim, white words. The bright kitchen on the right is darkened with the rest. |
| 1:21 | "It should be something like lighting design for your Nevada home. The dedicated being at the beginning of the headline is just hurting your intent alignment." | h1: "Lighting Design for Your Nevada Home". |
| 1:35 | "An eyebrow talking about who you're targeting... For homeowners, or we work with architects, builders, and designers." | Eyebrow: "For homeowners in Reno, Tahoe, and Truckee". The trade line sits over Our process. |
| 1:48 | "Keeping this line right here, lighting has the power to shape how your home looks and feels..." | Their line, word for word, under the headline. Their page has "intention, comfort, and performance"; his read skipped "intention". |
| 2:00 | "This copy is running way too long. This should be a services section that has a few cards... the keypad customized lighting scenes, the automation voice control, controlled color temperature as well as circadian rhythm benefits... each of those cards should be this primary color... this sort of orange." | Three cards in their amber (#EBA900): Keypad lighting scenes, Automation and voice control, Color temperature and circadian rhythm. Their 1,600-word page is about 800 words here, headline to footer. |
| 2:27 | "Right below the call to action, adding reviews right there... just having like stars right there with whatever the number is." | Not done. Their site states no Google rating or count. The 2026-09-24 sweep lists 3.9 from 14 reviews; see the misses. One line in `hero.trust` draws it once he says so. |
| 2:42 | "An about us... a picture of either you, the owner, the team, leadership, and then just a brief description about what the company stands for." | About: the founder, Keith Burrowes, in their own photo. Two sentences from their about page: founded 2002, built on performance and integrity, works with your architect, builder, and designer. |
| 2:56 | "Just three good reviews would do a lot of heavy lifting." | Three of the six on their home page: Ronald D. (design and install), Meredith M. (kitchen lighting), Alyssa R. and Aaron D. First name and last initial, as their site already shows them. |
| 3:03 | "A portfolio of your works, like three shots of the relevant offerings." | Three of their gallery photos: the Greybull living room with the lit ceiling, the lake kitchen with its chandeliers, the great room with cove lighting. |
| 3:10 | "An our process that just talks through. Oh, you got that right here... consultation, design." | Their four steps from the page, their words, numbered: Discovery and consultation, Conceptual design, Detailed lighting plan, Installation support and final tuning. Their Greybull house behind it. |
| 3:17 | "The FAQ, that's good." | Six of their seven questions with their answers. Dropped: remote design. |
| 3:24 | "Already feeling high resistance here. It should just be a single button that takes you to a four-stage multi-step form: first name, email, phone number, and then brief message, directly linked to your calendar." | One "Book a meeting" button (top bar, hero, foot) opens the four-step form, one question a screen. The engine's order is first name, phone, email, message (his PHA order of 2026-10-05). The last screen shows a marked calendar slot: they have no booking link. |
| 3:40 | "A secondary services section. So you have your high-ticket items like your whole home audio." | Six cards to their own pages: whole-home audio and video, home theater, motorized shading, smart home automation, lighting control, electrical services. |
| 3:46 | "A secondary call to action right below that." | "Start with a private consultation" and the button. Their site says "private consultation", never "free", so the page does not either. |

## Where every fact came from

Their public site, read 2026-10-06 with `scripts/research.py site` (`projects/research/sierra-integrated*/`):

- Lighting design page: the hero line, the hero photo (`room_task_light_i1`, the only non-AI picture on the page; the three "lighting-design-0N-ai" pictures were skipped), the four process steps, the seven FAQ, the Ketra tunable white line, the amber (#eba900) and faces (Roboto, Roboto Condensed).
- Home page: the six reviews, the "Explore Our Solutions" one-liners used on the service cards, the service areas.
- /about-us/company: founded 2002, Keith Burrowes as founder and Managing Member, "built on performance and integrity", "collaborate with you, your architect, builder, and designer", his photo (`/images/clientimages/Burrowes_2809_w.jpg`), the credentials (Control4, Crestron, Lutron, Sonance, Sony direct dealer; CEDIA and HTSA member; licensed in Nevada and California).
- /gallery originals under `/images/clientimages/`: 30Greybull07 (living room), Kitchen-0952_RGB, Great Room-1317-Blinds Half Closed_WEB, and 30Greybull22 (the house, behind the process band).
- /contact: 8060 Double R Boulevard #500, Reno, NV 89511; (775) 853-4800.
- Lutron Black Diamond Dealer 2025: the badge on every page. Credentials sit in the footer only.
- The three cards are his three outcomes. The scene names (Welcome Home, Movie Night, Goodnight) are their lighting control copy; tunable white is their Ketra line. "Answer a voice command" and "helps you wind down" are his outcomes in plain words, not claims their site makes; cut them if they object.
- The reviews are cut, not rewritten; a cut is marked with three periods.
- Two assets were changed, not invented: their white horizontal logo is painted their dark grey (#292929) for the white header bar; the founder's portrait is cropped to 5:4 so his head stays in the box.
- No rating anywhere on the page: their site states none.
- No background pattern set: his A B A C A B A colors are his to settle (Taste Log 2026-10-06). The page keeps the PHA look.
- The form sends nothing. It is a render.

## Big misses the AIOS would raise (his to take or leave)

1. **No proof under the button.** He asked for stars and the count right under the call to action. Their site never states a rating, and the sweep of 2026-09-24 lists 3.9 from 14 reviews: a thin, middling number for a 24-year-old company that sells to high-end homes. Five full stars over "3.9" would misread, so the line is off. A review campaign (the free one, or asking the six people quoted on their site) is worth more than any line of copy here.
2. **The hero is not their work.** Their page's hero is a rendered room, not a photo of a job. Their gallery has the Greybull house and the lake homes. Swap `hero.photo` to `assets/work-greybull-exterior.jpg` and the first screen is a Nevada home they wired. One line in the spec; his call.
3. **No calendar.** "Directly linked to your calendar" needs a booking link they do not have; their site ends at a form. Until they give one, the form's last screen is a marked slot and a lead waits for a call back.

Also: only one of the six reviews on their site is about lighting (a repair), and none are from Google. Two reviews from lighting design clients would carry the reviews section.

## Not done

- The B and A Loom cut and the email to Keith.
- A team photo: the only picture of a person on their site is the founder's formal headshot.
- The Google profile pull (about 4 cents) for the real rating, count, and five reviews; waits on his go.
