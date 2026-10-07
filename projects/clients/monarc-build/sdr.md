# SDR: Monarc Build (the first install)

Install record for `/sdr`, Monarc's own line. Started as the outreach record; the intake below is cold outreach's and the other three workflows add to it. Started 2026-10-05. Monarc is not a client; this folder holds the runs of each skill on Monarc itself, the proof each one works before a client gets it (`references/agent-catalog.md`).

State: **intake open.** Nothing is built, nothing is sent.

## Settings

- Who is reached: buyers. Which buyers: open, fact 1.
- How: open. On file today: the dial hour (his, by phone), LinkedIn messaging (Patrick, from a sheet), no cold email.

## Intake: the seven facts

"On file" means written somewhere in this repo for the buyer before 2026-10-05. Each still needs Jonathan's yes, because the buyer and the offer were reopened that day.

| # | Fact | Answer | From |
|---|---|---|---|
| 1 | Who to reach | Part answered 2026-10-05: companies on Google Maps that could use a new site, a receptionist, email follow-up, an appointment setter, or a proposal builder. Open: which kinds of business the first pull searches for. | his to say |
| 2 | Where | Open. | his to say |
| 3 | The signals, and three marks of a bad one | Part answered 2026-10-05: reviews, and the website signals for the five (`/list-building`, qualify; the checks are the AIOS's first cut). Open: the review band (the 2026-09-11 rule was 0 to 30 reviews, written for integrators), and the marks of a bad one. | his to say |
| 4 | The one outcome offered | Open. `context/offer.md` is on hold. | his to say |
| 5 | The proof line | On file, for the old buyer: the Annapolis ranked page and the jobs it brought (`context/offer.md`, Proof). Keep, or name another. | confirm |
| 6 | The ask | On file: fifteen minutes, two times offered (`references/voice.md`, `references/mycopy.md`). | confirm |
| 7 | Who answers replies | The SDR, in patrick@monarcbuild.com (the inbox replies workflow); anything it has no approved answer for waits for Jonathan. Patrick left, so the LinkedIn messages have no sender today. | his word 2026-10-05 |

**Do-not-contact, on file, to confirm:** companies in DC, MD, and VA (the 2026-09-11 call-list rule); the 25 that turned him down in September; One Firefly's clients; his own addresses and phone (the self rule in `CLAUDE.md`).

**Two numbers, his to set:** the least rows the list must have: ___. Booked meetings a week that count as working: ___.

Signed off by Jonathan: ___ (date)

## Access

Never a secret on this page.

| Access | Status | Note |
|---|---|---|
| The mailbox that sends | named, not wired | patrick@monarcbuild.com, his word 2026-10-05; Patrick left and the address is the SDR's now. Checked the same day: it is its own Proton sign-in, not an address on Jonathan's (his reply to it never reached his INBOX). It needs signing in to Proton Bridge here, then `PROTON_SDR_USER` and `PROTON_SDR_BRIDGE_PASS` in `.env`. Open: the name shown on the mailbox, and whether cold mail rides on the main domain or a second one. |
| The LinkedIn seat | his own | No sending tool is wired. Today's messages go out by hand. |
| The calendar | granted | `scripts/google_calendar_api.py`, as jonathan@monarcbuild.com only. |
| The record | granted | The Monarc CRM and the Prospects base (`references/airtable-api.md`). |
| The data: Google Maps | granted | `GOOGLE_MAPS_API_KEY` is wired (`connections.md` row 12, `scripts/places_seed.py`). No pull is approved for this list. |
| The data: Clay | not connected | Jonathan, 2026-10-05: Clay gives the email, the owner's name, and the LinkedIn URL. No Clay account or key is on file (`connections.md` row 22). This settles the old Apollo question in `tasks.md`. |

## Approvals

| Date | What | His words |
|---|---|---|
| 2026-10-05 | The send rule | "Pre approved messages get sent" |
| 2026-10-05 | The SDR's mailbox | "This is going to be patrick@monarcbuild doing the SDR role for email. He left so we are repurposing this email." |
| 2026-10-05 | Who gets an automated answer; what ends a drip | "Only prospects in the pipeline get automated responses and a response cancels the drip sequence." |
| 2026-10-05 | A copy test in his inbox | "Hit my inbox as if I were an integrator that took 2 days to respond to a form submission": Email 1 with the slow-reply line laid in his INBOX at 2:06 pm, from patrick@monarcbuild.com, subject "Your contact form, two days". His read is not back yet. |
| 2026-10-05 | The inbox answers a question about times by itself | "this one's asking about availability, which should be an automated response that checks my calendar's availability and then schedules for a meeting." Built the same hour (`scripts/sdr_inbox.py`); his reply was answered at 2:18 pm with 3:30 or 4:30. `send` and `book` stay off. |
| 2026-10-05 | What a booked prospect gets | "as a response to my request for a booking time it should just respond with the meeting link. I was also not sent a confirmation email". The booked answer is now the time and the Meet link; a confirmation from "Monarc Build" goes with it. Both laid again at 2:52 pm for his 3:30 hold. |
| 2026-10-05 | No stop line in the cold email | "The not for you reply stop and I won't write again is an opt-in that makes it sound automated. So X that." |
| 2026-10-05 | Where the list comes from | "Linkedin and Email will be bought through a data company and used in conjunction with the list building skill which enriches and qualifies for signaling attributes" |
| 2026-10-05 | The list, spelled out | "The list is just a big pull from google maps api with a clay hookup for email, owner name, and linkedin url, and the few qualifications like reviews and website signals that they could use a new site, receptionist, email follow up, an appointment setter, and a proposal builder come next" |

No message is approved yet. The LinkedIn line (a sending tool breaks LinkedIn's rules; the seat can be limited or closed) has been put to him once, in chat on 2026-10-05; his yes for his own seat is not on file.

## The pass

Jonathan, 2026-10-05: "we go through each function and I approve that the copy matches what I would typically sound like."

| Workflow | Copy | His approval |
|---|---|---|
| Cold outreach | v2 drafted 2026-10-05 from his mark-up of v1 (`.claude/skills/sdr/workflows/cold-outreach.md`) | not yet |
| Lead form submission follow-up | not drafted | |
| Stale proposal follow-up | not drafted | |
| Appointment booking | the times offer and the booked note drafted 2026-10-05 (`projects/sdr/config.json`, "copy"), running on test threads; the reminder and the rebook not drafted | not yet |
| No-show | v1 drafted 2026-10-05 on its first case, Momentum Electrical Contractors (`.claude/skills/sdr/workflows/no-show.md`) | not yet |
| Inbox replies | the watcher sorts by plain rules; the answers for who we are, the price, not now, no, and wrong person are not drafted | not yet |

## Checks for cold outreach (not the pass)

**Before the first real send**

- [ ] The seven facts are on file and the owner signed off on them.
- [ ] The list has at least the intake number of rows, no doubles, none from the do-not-contact list. Every row carries its signals and the reason it was kept.
- [ ] The list passed `/list-building`'s own checklist: every email verified, the cost at or under the approved number.
- [ ] Of the 20 rows the owner checked, 18 or more are right.
- [ ] Every message is approved by the owner, with the date. Each line has one job. No first message over 120 words.
- [ ] Email: the sending domain passes SPF, DKIM, and DMARC. Every email carries an opt-out line and a postal address.
- [ ] Rehearsal: 10 of 10 test sends reach the inbox. A reply stops the sequence. A "stop" blocks the row. All of it shows on the record.
- [ ] The owner pauses it and starts it again himself, once.

**After 30 days**

- [ ] No day went over the cap.
- [ ] Every reply was on the record and sorted within one business day.
- [ ] Bounces under 3 in 100. Spam complaints under 1 in 1,000.
- [ ] Booked meetings a week at or over the intake number.
- [ ] Every booked meeting carries its source.
- [ ] The first monthly report went out.

**At the hand-off**

- [ ] The owner, or their person, changes one message and adds one row from the one-page guide with no help.

## Monthly checks

None yet.
