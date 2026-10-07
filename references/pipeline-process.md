# Pipeline process: the documents at every stage

One page that says, for each stage a prospect or client moves through, what happens, which documents and tools carry it, and what moves it to the next stage. Written 2026-09-24 when Jonathan filed the onboarding questionnaire and the asset-request email under Onboarding. The stages before Won are the CRM's deal stages (`projects/crm/config.json`, Config row `stages`); the stages after Won are the client steps in `context/roadmap.md` (13 to 19). Every document named here lives in this repo unless the line says otherwise. A document is listed at the stage where it is first used; a later stage points back rather than listing it again. When a template, script, or skill is added or moved, add or move its line here in the same edit. The check: every backticked path on this page exists on disk.

| Stage | Moves in when | Moves out when |
|---|---|---|
| Cold | A company is on a call list | A dial reaches a person, or an email, text, or DM goes out |
| Contacted | A connected call, an email, a text, or a DM (Phase ladder: Called, Second channel, Third channel) | A meeting lands on the calendar |
| Booked | A meeting is on the "Monarc Build" calendar, from a cold call yes or a booking on the site | The meeting is held, or the prospect no-shows |
| Held | The 15 minute meeting ran | Terms went out, or a close reason is logged |
| Proposed | The terms email and the signing link went out | The agreement is signed, or a close reason is logged |
| Won | The agreement is signed (close reason "Signed") | The invoice is out and the kickoff is booked |
| Onboarding | Signing day to the kickoff call | The kickoff ran and the recap went out |
| Build | Kickoff to go-live, 14 days | Site, landing pages, GBP, and Ads are live |
| Live | The Lead loop runs: First Responder, weekly PDF, monthly meeting | Day 60 |
| Day 60 | The pilot ends | The 6 month term is signed, or the client walks with the site, pages, and data |
| Lost | Any stage, with a close reason | Not reopened in place; a new deal if they come back |

## Cold

What happens: 22 dials in the dial hour (12:00 to 13:00 Eastern), Monday to Friday, from the Today view of the CRM. Every dial gets an outcome. A no-contact outcome logs the dial and drops the row; a contact outcome moves the deal.

- `projects/outreach/qualified-list-2026-09-11.csv` (integrators) and `projects/outreach/electrician-list-2026-09-24.csv`: the call lists the Today view reads, one per vertical (`verticals` in `projects/crm/config.json`).
- `scripts/places_seed.py`, `scripts/qualify_sites.py`, `scripts/seed_to_list.py`: how a list is built (Places sweep, Opus read, cut to the call list). `scripts/seed_to_linkedin.py` and `scripts/meta_seed.py` cut the same sweep for the LinkedIn and Meta audiences.
- `references/cold-call-principles.md`: the five rules and the script lines (DISARM to LOCK). The script itself is Sample 1 in `references/voice.md`. The line a call died on is logged per dial.
- `context/icp-brands.md` and `context/trades/`: who the ideal client is per trade; the PROVE and NAME lines draw from them.
- `.claude/skills/sdr/SKILL.md` (added 2026-10-05; mirror at `.agents/skills/sdr/SKILL.md`): the SDR skill, one role for the outbound, the follow-up, and the appointment setting. Its workflows are files under it: `.claude/skills/sdr/workflows/cold-outreach.md` (this stage), `.claude/skills/sdr/workflows/lead-form-follow-up.md` and `.claude/skills/sdr/workflows/appointment-booking.md` (Contacted and Booked), `.claude/skills/sdr/workflows/stale-proposal-follow-up.md` (Proposed). A workflow passes when Jonathan approves that its copy sounds like him. Monarc's own run is recorded in `projects/clients/monarc-build/sdr.md` (intake open; nothing built or sent).
- `.claude/skills/list-building/SKILL.md` (added 2026-10-05; mirror at `.agents/skills/list-building/SKILL.md`): a skill, how a list is built from here on: a Google Maps pull, a Clay hookup for email, owner name, and LinkedIn URL (not wired yet), then reviews and five website signals. The SDR's cold outreach gets its list from it.
- `projects/outreach/dial-log.jsonl`: every dial on disk. The CRM Reports view runs the Friday tally (`context/roadmap.md` step 10).
- `projects/google-ads/` (added 2026-09-25): Monarc's own search campaigns, one per service-line page. A click lands on a themed page (`projects/Landing Page Build/pages/<slug>.md`), and a booking arrives at Booked with Source Google Ads and its campaign and keyword through the UTMs (`references/attribution.md`). The tracking and launch checklists there gate any spend; the Friday review writes `projects/google-ads/reports/`.
- `projects/meta-ads/` (added 2026-10-03): Monarc's Meta campaign, a talking-head video to `/builder-check/` (`check.md`: four tiles, one true result line, then the booking calendar). A completed check is a booking that arrives at Booked with Source Meta Ads, its campaign by Platform id, and the four answers on the Leads row. `README.md` holds the six gates before a dollar spends, the $500 read, and the $1,000 stop; `scripts.md` the three video scripts.

## Contacted

What happens: a person answered, or a first email, text, or DM went out. A next action and a date are required on the deal.

- `references/mycopy.md`: the copy blocks for every email in Jonathan's register (opener, proof line, ranked page line, one-sentence offer, pilot terms, the terms email, the ask, rebook, declining). `/inbox` drafts replies from it into Proton Drafts; nothing sends itself.
- `projects/outreach/2026-09-09-criteria-of-naples.md`: the worked case email, version 6 approved, the pattern for a proof email.
- `scripts/proton_mail.py`: reads the mailbox and writes drafts (`references/proton-mail-api.md`).

## Booked

What happens: a meeting is on the calendar with a Meet link. Confirmation the same day, the Loom brief before the meeting, reminder the day before, show or no-show logged.

- `projects/crm/playbook.json` (added 2026-10-04): the steps each stage owes a company, the list the CRM's company file triages against. One list per stage from Contacted to Won; edit it there and the file follows. Ticks and Jonathan's own to-dos per company are kept in `projects/crm/triage.json`.
- The Loom brief (Jonathan, 2026-10-04): a short Loom recorded for the company and sent before the meeting, a brief on what Monarc will set up so their lead flow runs smooth. Script: `templates/loom-brief-script.md` (added 2026-10-05, variation A the full review, B the page reviewed and rebuilt); the CRM ticks the step when a sent email to the company carries a loom.com link. Each Loom is pasted on the company's file and kept in `projects/crm/looms.json` with its variation (A: the full page review, about 11 minutes, first sent to Momentum Electrical Contractors 2026-10-04); the CRM's Reports page sets each variation's show rate and close rate beside the meetings that got no Loom.
- `templates/follow-up-email.md`: the confirmation after a booked cold call (the LOCK step) and the day-before reminder.
- `.claude/skills/sdr/workflows/no-show.md` (added 2026-10-05): what happens when nobody comes. The no-show is logged on the company's file (the Booked step "show", answer No-show), which opens three more steps there; one rebook email on the confirmation's thread and one LinkedIn message go out the same day, both drafted for Jonathan to send; it ends rebooked or closed with a reason.
- `templates/booking-drip.md`: for bookings from monarcbuild.com: the confirmation with the Meet link, the day-before reminder (added 2026-10-03), the one-hour reminder, the notice to Jonathan. Sent by the booking backend `scripts/avmarketing-booking.gs` (`references/apps-script-booking.md`), which posts the booking to the CRM as a deal at Booked once its Airtable token is set (`connections.md` row 15, still to confirm).
- Calendar: "Monarc Build" (`connections.md` row 3). The AIOS can create the invite.

## Held

What happens: the 15 minute meeting from the offer page. Jonathan brings what buyers in the metro search for and where the prospect's site shows up for it. Close, or the objection that killed it, is logged.

- `context/offer.md`: the offer as it is stated on the call. Price is quoted on the call after the free value, never in an email first.
- The "Monarc Build Meeting Flow" one-pager in Google Drive is the $7,000 a month flow from August, superseded by the offer page on 2026-09-15. Do not draft from it.

## Proposed

What happens: the terms email goes out with the signing link. Follow-ups by the next action date.

- `references/mycopy.md`, the terms email: pilot terms on one screen with the DocuSeal link.
- `templates/Monarc_Pilot_Service_Agreement.pdf` and `templates/Monarc_Pilot_Service_Agreement.docx`: the agreement. The live signing template is on Jonathan's DocuSeal Pro account; the public link and the API notes are in `connections.md` row 2. A DocuSeal send emails the signer, so it runs only on Jonathan's go.

## Won

What happens: signed. Same day: the invoice, the deal to Won, the contract filed, the kickoff booked.

- CRM: the deal moves to Won with the close reason "Signed" (the dashboard's deal form).
- Invoice: the money book, `references/books.md` and `scripts/books.py` (Stripe: `references/stripe-api.md`).
- Contract: the signed PDF from DocuSeal into `records/contracts/<slug>/`, one row in `records/README.md`. Everything under `records/` except the index is git-ignored.
- `tasks.md`: copy the per-client checklist under the client's tier.
- Lost at any stage: a close reason from the Config list is required; the deal stays closed.

## Onboarding

What happens: signing day to the kickoff call, about five business days (the access clause in `context/offer.md` gives the client five business days to grant access). The client answers the questionnaire in their own words and sends the files, so the 45 minute call spends its time on decisions: the floor, lead handling, access, money, the video.

Sequence:

1. Prep day: `/kickoff prep` resolves the client, reads their site and listing, books the 45 minute Meet, creates the capture, and drafts the invite with the questionnaire under it. Jonathan sends.
2. Next business day: the asset-request email. Jonathan sends.
3. Three business days before the call: the questionnaire is due back. The AIOS copies each answer into the capture's "Already known" block and lists the blanks as the call's open questions.
4. The call: `/kickoff call`, seven blocks, one question at a time, checkpointed after every answer. Block 4 grants access live on a shared screen.
5. Wrap: `/kickoff wrap` scaffolds the client folder, fills the recap email with the "still need from you" list, moves the deal, files the contract, and sets the build deadline at kickoff plus 14 days.

Documents:

- `templates/onboarding-questionnaire.md`: the client-fill questionnaire. A cover note; Part 1, 15 items every trade answers (business, service area, offerings, floor, proof, reviews, primary search phrase); Part 2, one four-item block per trade (services ticked and ranked, brands carried, programs held, one trade question). Trade keys: integrator, electrician, hvac, plumbing, roofing. A mapping table sends every answer to one section of the brief.
- `templates/asset-request-email.md`: the email that asks for everything a website rebuild needs. Seven items hold up the build: job photos, logo, license number, domain, hosting and builder, email on the domain, Google Business Profile. Seven trail: video, certificate of insurance, badges, team photos, existing content, brand bits, warranty and financing paperwork. It never asks for a password. Files land in `projects/clients/<slug>/assets/`, git-ignored.
- `context/trades/` (one file per trade key): services, brands, and dealer programs per trade, the map Part 2 mirrors and the kickoff reads answers against. Integrators use `context/icp-brands.md`. The roofing, electrician, hvac, and plumbing files are AIOS drafts until Jonathan confirms each.
- `.claude/skills/kickoff/SKILL.md`: the skill, three modes (prep, call, wrap). Mirror at `.agents/skills/kickoff/SKILL.md`.
- `.claude/skills/kickoff/assets/questionnaire.md`: the 41 call questions in seven blocks. Blocks 1 and 2 are pre-filled by the client questionnaire; the file and access items of Block 4 by the asset email.
- `.claude/skills/kickoff/assets/access-checklist.md`: the 12 access rows (GBP, Ads, GA4, Search Console, GTM, domain, hosting, calendar, phone, lead email, social, photos), how the client grants each, what to record. Never a password.
- `.claude/skills/kickoff/templates/client-brief.md` and `.claude/skills/kickoff/templates/access.md`: the two files every client folder starts from.
- `templates/kickoff-recap-email.md`: the invite before the call and the recap after it.
- `templates/vsl-draft.md`: Block 7's targeting brief and the script skeleton. The client's v1 lands in the client folder as `vsl.md`.
- The capture: `brainstorms/` (`<date>-kickoff-<slug>.md`), every answer checkpointed.
- Output: `projects/clients/<slug>/` with `brief.md` (confirmed facts), `access.md` (IDs and status), `vsl.md` (v1, not approved), and `assets/` (the files).

## Build

What happens: 14 days from kickoff. Site (new build or takeover), one landing page per service and per city, GBP, Ads live. Hours logged.

- The client's `brief.md`, Build section: deadline, primary term, platform, blockers with owners. `access.md`: rows 1, 2, 6, 7, 8 must be granted or create before the build starts; row 12 (photos, logo) blocks the landing pages, not the ads.
- `references/github-skills-shortlist.md`: the one vetted skill per build capability (SEO, design, attribution) and what each needs from the client.
- `references/hostinger-api.md`: Monarc hosting; client staging subdomains and DNS pointing when a site moves to Monarc.
- `references/attribution.md` and `references/channel-connections.md`: UTM rules, tags per channel, what must be wired before a lead carries its source.
- Blockers become `tasks.md` lines with an owner and a date; anything still `requested` in `access.md` after 48 hours does too.

## Live

What happens: the Lead loop. Every form fill called within 5 minutes, 9am to 7pm Eastern, email follow-up, booked into the client's calendar. A weekly PDF. One 15 minute meeting a month.

- First Responder inputs: the client's `brief.md`, Qualification section (pricing floor, area, qualifying questions, calendar, after-hours rule), all from the questionnaire and Block 3.
- Lead log: the CRM. A lead is a deal on the board with its source (`references/attribution.md`).
- Weekly PDF: `context/roadmap.md` step 16. Not built yet; a `/level-up` candidate after the Friday tally.
- Monthly meeting and the day 60 review: the client's `brief.md`, Meetings section, booked at wrap.

## Day 60

What happens: results review, the 6 month term signed, one proof line pulled onto the offer page and into the call frame, two referrals asked.

- `context/roadmap.md` steps 18 and 19; the Proof loop.
- `tasks.md`, per-client checklist, last line.
- The client's `brief.md` header: the pilot day 60 date.
