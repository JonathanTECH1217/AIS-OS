# Page spec: /ai-automation/ (AI Business Automation)

Status: **live 2026-09-26** (Jonathan: "Push them. Good enough"), read back; in the Services menu. Last in the build order. The tool behind each card is still unnamed: the plan said nothing prints before it runs on Monarc's own line, and the cards name jobs, not tools, so that holds; name the tools before ads point here, with the call-script line.

- Theme: `time` (`../themes/time.json`), dark. Skeleton: Style Guide 6.16.
- Campaign: `projects/google-ads/campaigns/06-ai-automation.md` (test rotation). Research: `projects/google-ads/keywords/ai-automation-research.md` and `.csv` (85 rows, finished 2026-09-26).
- Decisions behind it: `brainstorms/2026-09-25-google-ads-pages.md` Q40 to Q45; Jonathan: "The AI automation page should show centralize around saving the business owner time. This is in the proposal building, email automation, lead follow up, invoicing and book keeping."

## Keyword group and the h1

- Ad groups (revised 2026-09-26 from the research): back office; follow-up; by trade. The software-owned seeds (invoicing, bookkeeping, the AI receptionist, the answering services) are parked; see the campaign brief.
- h1 target term: pending the Planner run. Research candidates: "AI Automation for Contractors" (the first seed and the start of the draft h1; three done-for-you builders rank); "Back Office Automation for Contractors" (the results page with the most done-for-you sellers; covers proposals, invoices, and books); "AI Automation for Home Service Contractors" (drops the wrong readers, though integrators may not see themselves in it).
- Two wrong searchers to exclude: "ai contractor" (a freelance AI engineer or a job) and "automation contractor" (factory controls).
- Draft h1 until then: "AI automation for contractors. Your hours back." (7 words), which keeps the first candidate as typed.
- What the searcher expects: software pages show a monthly price and builders a setup fee; this page shows neither, so the FAQ's cost answer carries the weight, and the call-script line must name how the price is set.

## URL, CRM, tracking

- Final URL `https://monarcbuild.com/ai-automation/`, `noindex`, `mb-page-type` ad, `mb-theme` time.
- `book_appointment` with `page: 'ai_automation'`; the shared conversion label. CRM Landing pages row: Service AI automation, Status Draft.

## v1 blocks

| # | Block | Anchor | What is in it |
|---|---|---|---|
| 1 | Brand mark | | |
| 2 | Hero, split | `hero` | h1, sub, Jonathan's line, "Get your hours back" (mint pill, dark text); the evening-porch render right |
| 3 | What you get | `services` | Four panel cards, 12px radius, hairline border; Lucide icons in mint (file-text, mail, receipt, book-open) |
| 4 | Walk-through | `week` | "A week, before and after": two five-day CSS grids, mono labels, no hours figure |
| 5 | Works for, Not for | `fit` | `#4ADE80` and `#F87171` on the dark ground |
| 6 | FAQ | `faq` | Three `<details>` |
| 7 | Final ask | `book` | h2, "Book the call", the micro-line |
| | Footer, pill, popup | | Pill on "Get your hours back"; the popup on the dark ground |

## Copy drafts (every line is Jonathan's to approve)

| Element | Draft | Words | Status |
|---|---|---|---|
| h1 | AI automation for contractors. Your hours back. | 7 | draft, pending the Planner term |
| Sub | Proposals, follow-up, invoices, and the books run without you typing. A missed call gets a text back. | 17 | draft (no clock, Copy 9) |
| Hero line | Stay in the field without missing a call. | 8 | draft (Jonathan's "Don't miss a call while you're in the field") |
| Hero button | Get your hours back | 4 | approved (Q44) |
| Cards label, h2 | What you get / Four jobs off your evenings. | 3 + 5 | draft |
| Card 1 | **Proposals from the call notes.** Your notes become a proposal draft. You review it and send it. The typing is gone. | 21 | draft (Q41) |
| Card 2 | **Lead follow-up.** Every lead gets a reply and a sequence. A missed call gets a text back. The follow-up goes out without you. | 23 | draft (Q41: the drip, email automation, and the missed-call text-back in one card) |
| Card 3 | **Invoices at the milestone.** Stage done, invoice sent. Invoices go out when the job moves. No chasing paperwork at night. | 20 | draft (Q41) |
| Card 4 | **The books, closed.** Transactions sorted as they come in. The month closes without a weekend lost to receipts. | 18 | draft (Q41) |
| Walk-through label, h2 | A week, before and after / Where your evenings go. | 5 + 4 | draft |
| Grid labels | Before · After · Mon to Fri · Proposals · Follow-up · Invoices · Books · Missed calls · On site · Home | about 20 | draft (mono face) |
| Fit h2 | Built for a specific kind of shop. | 7 | from the live ad page |
| Works for | Paperwork after dinner · Calls missed from the job site · The same admin every week · Willing to review drafts | 18 | draft |
| Not for | No written process at all · Wanting a promised number of hours · No calls to miss · Nobody to review the drafts | 20 | draft |
| FAQ h2 | Three questions before you book. | 5 | draft |
| FAQ 1 | What does it cost? Quoted on the call, by which of the four parts you need and the tools you already run. | 22 | draft |
| FAQ 2 | What happens on the call? Fifteen minutes. Bring last month's admin hours. You leave with the list of what goes first. | 21 | draft |
| FAQ 3 | What if it does not work? No one can promise hours saved. Once fees are paid, the automations and the data are yours. | 23 | draft |
| Final ask h2 | Get the admin off your evenings. | 6 | draft |
| Final button | Book the call | 3 | approved (Q44) |
| Micro-line | Fifteen minutes. Bring nothing. | 4 | approved |

About 290 visible words by hand, against 400.

## v2 candidates

"On the call" ("the hours plan"); About us; a dashboard card.

## Images

- Hero: `../candidates/ai-automation/hero-1.jpg` to `hero-4.jpg`. **Picked 2026-09-26 by Jonathan: hero 4, the warm home** ("for the house use the warm home photo but make slab/home into a sticker"). The background was removed on the connected generator (1 credit), then the house and its slab got a white sticker border and a soft shadow on a transparent ground: `public_html/assets/generated/ai-automation/hero-sticker.png` (171 KB) and `hero-sticker-800.png`. The plain export `hero.jpg` stays as a fallback. Preview on the page ground: `../candidates/ai-automation/hero-4-sticker-preview.jpg`. The warm window light sits outside the mint palette; Jonathan chose it over the mint candidates.
- Icons: Lucide, inline SVG, in mint. No other images.

## Scrutiny checklist

- [ ] Message match; one action (two "Get your hours back", one "Book the call"); split hero at 1440, stacked at 390.
- [ ] Six blocks; `drift.py` clean under `time`; `readability.py` within Copy 7; visible words under 400.
- [ ] No hours-saved figure and no answer-time promise anywhere; `drift.py`'s Copy 9 check covers "text back within N minutes".
- [ ] Every card names a job a real tool does, and each tool has run on Monarc's own line (Jonathan names them first).
- [ ] Mint on the dark ground passes (14:1); the popup, footer, and pill read on `#0B1220`.
- [ ] Tracking and the four popup and sent states; privacy link.
- [ ] Automation is outside the Pilot Service Agreement: the call-script line exists before the push.

## Tile and render history

- 2026-09-25: tile rendered, `../renders/2026-09-25/tile-time-1440.png`. Contact sheet `../renders/2026-09-25/candidates-ai-automation.jpg`.
- 2026-09-26: **page built** (`python scripts/build_service_page.py ai-automation`) from `build/ai-automation.body.html`. `drift.py` 0 findings under `time`; `readability.py` 0 findings, 358 visible words, popup 120. Renders in `../renders/2026-09-26/`: `ai-automation-1440.png`, `-390.png`, the two folds, `-step4-390.png`. Not pushed.
  - The sticker sits straight on the dark ground, no frame. Its clear pixels were alpha 1, not 0, one shade off the ground; set to 0 (same file size).
  - Icons: Lucide (ISC) files, inline, 1.5 stroke in mint. The hero line in the mono face, mint.
  - The week: two five-day grids. Before: "On site", then two admin blocks each evening (proposals, follow-up, invoices, books, missed calls). After: "On site", then "Home" outlined in mint. No hours figure.
  - To settle: at 1440 the h1 breaks into five lines with "for" alone ("AI automation / for / contractors. / Your hours / back."): the words are too wide for the hero column at 64px. A shorter h1 or a smaller size on this page fixes it. The FAQ says "Bring last month's admin hours" while the micro-line says "Bring nothing".

## Open items

- The tool behind each card (proposals, follow-up and text-back, invoicing, bookkeeping), run on Monarc's own line first.
