# Page spec: /email-marketing/ (Email marketing)

Status: **live 2026-09-26** (Jonathan: "Push them. Good enough"), read back; in the Services menu. The open points below carry into the next round. The call-script line for email is still owed before ads point here. Fourth in the build order.

- Theme: `commercial` (`../themes/commercial.json`). Skeleton: Style Guide 6.16. Bold allowed in this theme.
- Campaign: `projects/google-ads/campaigns/04-email-marketing.md` (test rotation). Research: `projects/google-ads/keywords/email-marketing-research.md` and `.csv`.
- Decisions behind it: `brainstorms/2026-09-25-google-ads-pages.md` Q28 to Q33; Jonathan: "a commercial feel with more slab style font a golf put hole to indicate that email marketing works to close the proposal more frequently. It also shows breadth in trades."

## Keyword group and the h1

- Ad groups: contractors catch-all; follow-up (by pain); by trade.
- h1 target term: pending the Planner run. Research candidates: "Email Marketing for Home Integrators" (One Firefly's term with Jonathan's ICP word; nobody ranks on it); "Email Marketing for Contractors That Follows Up" (the widest buy term plus the sequence angle); "Follow-Up Emails for Quotes That Went Quiet" (pain first, in forum words; low volume).
- The research warns: "email marketing contractor" means freelancer jobs, so "contractor" stays tied to "for"; the trade SERPs belong to software, so software words and brand names are negatives.
- Draft h1 until then: "Email marketing for contractors with open proposals." (7 words).

## URL, CRM, tracking

- Final URL `https://monarcbuild.com/email-marketing/`, `noindex`, `mb-page-type` ad, `mb-theme` commercial.
- `book_appointment` with `page: 'email_marketing'`; the shared conversion label. CRM Landing pages row: Service Email, Status Draft.

## v1 blocks

| # | Block | Anchor | What is in it |
|---|---|---|---|
| 1 | Brand mark | | |
| 2 | Hero, split | `hero` | h1, sub, "Close the open proposals" (square, course green); the putt render right in a 2px ink frame |
| 3 | What you get | `services` | Four square cards, 2px ink border, hard offset shadow; Phosphor Bold envelopes (plain, bell, check, house) |
| 4 | Walk-through | `trades` | "One sequence, five trades": five columns, a trade icon (speaker, bolt, roof, fan, drop) and one draft subject line each |
| 5 | Works for, Not for | `fit` | Course green and flag red |
| 6 | FAQ | `faq` | Three `<details>` |
| 7 | Final ask | `book` | h2, "Book the call", the micro-line |
| | Footer, pill, popup | | Pill on "Close the open proposals"; square buttons |

## Copy drafts (every line is Jonathan's to approve)

| Element | Draft | Words | Status |
|---|---|---|---|
| h1 | Email marketing for contractors with open proposals. | 7 | draft, pending the Planner term |
| Sub | Four sequences in your voice: past clients, new leads, open proposals, finished installs. Sent without anyone typing. | 17 | draft |
| Hero button | Close the open proposals | 4 | approved (Q32) |
| Cards label, h2 | What you get / Four sequences. Written once, sent every time. | 3 + 7 | draft |
| Card 1 | **Your existing base.** Past clients hear from you again. Service reminders and the next upgrade. Referrals come from the list you already have. | 23 | draft (Q30) |
| Card 2 | **After a lead comes in.** Every new lead gets a sequence. A job like theirs, then the ask to book. Nobody has to remember to send it. | 27 | draft (Q30) |
| Card 3 | **After the consultation.** The proposal that went quiet gets followed up. Answers to the questions that stall a yes, one email at a time. | 23 | draft (Q30; the forum pain "estimates going cold") |
| Card 4 | **After the install.** Finished jobs turn into reviews and referrals. A thank you, a review request, and a check-in next season. | 21 | draft (Q30) |
| Walk-through label, h2 | One sequence, five trades / Written for the trade you run. | 4 + 6 | draft |
| Subject lines | Integrators: Still thinking about the theater? · Electricians: The generator quote, one question · Roofers: Before the next storm · HVAC: Your system quote is still open · Plumbers: The water heater we quoted | 30 | drafts in Jonathan's register |
| Walk-through caption | Draft first subject lines. Yours are written in your voice. | 10 | draft |
| Fit h2 | Built for a specific kind of shop. | 7 | from the live ad page |
| Works for | Proposals out, no follow-up · A customer list nobody emails · Copy approved once, then left to run · Emails in your own voice | 21 | draft |
| Not for | Buying a list · Newsletters for their own sake · No past clients yet · A guaranteed reply rate | 16 | draft (the forum quote "Newsletters don't really work if you just send them out") |
| FAQ h2 | Three questions before you book. | 5 | draft |
| FAQ 1 | What does it cost? Quoted on the call, by how many sequences you need and how big the list is. | 20 | draft |
| FAQ 2 | What happens on the call? Fifteen minutes. Bring the count of proposals waiting on a yes. You leave with the sequence plan. | 22 | draft |
| FAQ 3 | What if it does not work? No one can promise replies. Once fees are paid, the sequences and the list stay yours. | 22 | draft |
| Final ask h2 | The proposals you sent are still open. | 7 | approved in the interview (plan) |
| Final button | Book the call | 3 | approved (Q32) |
| Micro-line | Fifteen minutes. Bring nothing. | 4 | approved |

About 310 visible words by hand, against 400.

## v2 candidates

"On the call"; About us; a sequence timeline if the call keeps asking how often the emails go out.

## Images

- Hero: `../candidates/email-marketing/hero-1.jpg` to `hero-4.jpg`. **Picked 2026-09-26 by Jonathan: hero 3** (the ball at the cup, the red flag, a golfer walking up in the distance, clouds in a beige sky). Exported to `public_html/assets/generated/email-marketing/hero.jpg` (78 KB) and `hero-800.jpg`. No stock image (the licensed putt photo was superseded, Q28).
- **Hero layout changed (Jonathan, 2026-09-26): "The golf photo should have the headline overlaying the beige sky."** This page drops the split hero: the render runs the full column width, and the h1, the sub, and "Close the open proposals" sit over the beige sky in the top of the image, left of the flag, in ink `#1A1A1A` (about 15:1 on the cream sky). On phones the image crops to keep the sky band behind the text; if the sub cannot fit over the sky at 390, it drops below the image. Style Guide Layout 2 records the exception. The 2px ink frame stays.
- Icons: Phosphor Bold, inline SVG, in ink. No images in the trade row.

## Scrutiny checklist

- [ ] Message match; one action (two "Close the open proposals", one "Book the call"); split hero at 1440, stacked at 390.
- [ ] Six blocks; `drift.py` clean under `commercial` (weights 400, 600, 700 allowed); `readability.py` within Copy 7; visible words under 400.
- [ ] No open rates, reply rates, or results printed (none exist for email).
- [ ] Subject lines read as drafts for the reader's trade, never as sent emails with results.
- [ ] Tracking and the four popup and sent states in the theme; privacy link.
- [ ] Email is outside the Pilot Service Agreement: the call-script line exists before the push.

## Tile and render history

- 2026-09-25: tile rendered, `../renders/2026-09-25/tile-commercial-1440.png`. Contact sheet `../renders/2026-09-25/candidates-email-marketing.jpg`.
- 2026-09-26: **page built** (`python scripts/build_service_page.py email-marketing`) from `build/email-marketing.body.html`, every copy line the draft above. `drift.py` 0 findings under `commercial`; `readability.py` 0 findings, 355 visible words, popup 120. Renders in `../renders/2026-09-26/`: `email-marketing-1440.png`, `-390.png`, the two folds, `-step4-390.png` (and `popups-step4-390.png`, all three new pages side by side). Not pushed.
  - Hero over the sky, as Jonathan asked: on desktop the h1 (40px, not the 64px split-hero size, so it fits left of the flag), the sub, and the button sit over the sky; the button clears the golfer. **Under 1024px the strip of sky left of the flag is too narrow for the h1, so on tablets and phones the text stacks above the render.** Jonathan's call if he wants another answer there (a taller crop, or the h1 alone over the sky).
  - Icons: Phosphor Bold (MIT) files from jsdelivr, inline. Cards: the envelope, then the envelope with a bell, a check, and a house badge (Phosphor has no such envelopes, so each is the envelope plus a small badge icon), 40px so the badge reads (the theme said 32px). Trade row: speaker-hifi, lightning, house-line (no roof icon exists in the set), fan, drop.
  - Card titles and trade names in the bold slab; popup answer boxes square to match the theme.
  - Walk-through on the white band, the five subject lines in a bordered strip with the hard shadow; stacked rows on phones.
  - To settle: the FAQ says "Bring the count of proposals waiting on a yes" while the micro-line says "Bring nothing".
