---
name: sdr
description: Use when Jonathan says "SDR", "the SDR skill", "cold outreach", "lead form follow-up", "stale proposal", "appointment booking", "the SDR inbox", "answer the replies", or asks to draft, approve, install, or check any of them for Monarc or a client. The SDR role as one skill: it does the outbound, the follow-up, the appointment setting, and answers the replies in its own mailbox (patrick@monarcbuild.com at Monarc). Its workflows live under it (cold outreach, lead form submission follow-up, stale proposal follow-up, appointment booking, inbox replies, no-show). Also use when he says "report a no-show" or "they didn't show". It writes and sends approved copy; it does not audit copy, that is the coach skill. Pre-approved messages get sent; nothing else is.
argument-hint: "<cold-outreach | lead-form-follow-up | stale-proposal-follow-up | appointment-booking | inbox-replies | no-show> [company slug] [draft | approve | install | check]"
---

# SDR

One skill for the role a sales development rep fills. Jonathan, 2026-10-05: "this would be an SDR role, because they do outbound and follow-up and appointment setting. I guess those are the main functions and should be lumped into one agent or one skill... workflows would live underneath of skills... the SDR is the real build right now."

It is the first build. It runs inside Monarc first, then ships into a client's business by the same steps.

## Its workflows

Each is one file in `workflows/`. Read the one you are running before you start.

| Workflow | Kind | What sets it off | File |
|---|---|---|---|
| Cold outreach | outbound | A list of people who have never heard of the company | `workflows/cold-outreach.md` |
| Lead form submission follow-up | response | Someone fills out a form on the site | `workflows/lead-form-follow-up.md` |
| Stale proposal follow-up | follow-up | A proposal went out and no answer came back | `workflows/stale-proposal-follow-up.md` |
| Appointment booking | response | Someone says yes, or asks for a time | `workflows/appointment-booking.md` |
| Inbox replies | response | A message lands in the SDR's mailbox | `workflows/inbox-replies.md` |
| No-show | follow-up | A booked meeting nobody came to | `workflows/no-show.md` |

Lead form follow-up and appointment booking are two things (his word): one answers a form fill, the other turns a yes into a time on the calendar. Inbox replies was added the same day: "This SDR skill also needs to be baked in to respond to messages over my email inbox."

## The SDR's mailbox

At Monarc the SDR works from **patrick@monarcbuild.com** (Jonathan, 2026-10-05: "This is going to be patrick@monarcbuild doing the SDR role for email. He left so we are repurposing this email."). Cold outreach goes out from it and every reply comes back to it.

- Patrick left. Nothing goes out under his name. The name shown on the mailbox and the name at the foot of the copy must match, and must be someone who is there to answer. Who that is, is his to say.
- jonathan@monarcbuild.com stays his own. `/inbox` is the boot pass on that mailbox and never sends; it is not this skill.
- Not wired yet: reading and sending for this address (`workflows/inbox-replies.md`, "what is not there yet").
- At a client: the owner names the mailbox at intake.

## What the SDR does not do

It does not audit the copy. "The SDR is not auditing the copy. That is a coach skill that we will bake in." The SDR writes copy for his approval and sends what he approved. Judging whether the copy is good, and what to change after the numbers come in, is the coach's job. The coach skill is not written yet.

## The pass

His words: "The pass for this would be we go through each function and I approve that the copy matches what I would typically sound like."

- One workflow at a time. The AIOS drafts every message that workflow sends. He reads it and marks it up until it sounds like him.
- A workflow passes when he approves its copy. The approval, with the date, goes on the workflow's file and on the install record.
- The SDR passes when all six have passed.
- How he reads an email (2026-10-05): objection stealing, permission, the angle, experience, the offer with a small ask. No footnote. A follow-up is a new angle, never a nudge; the last one uses the cost of doing nothing. Drafts are labeled with those words.

At a client the same pass holds, with the owner in his place: the copy must sound like the owner.

## Rules every workflow follows

- **Voice.** At Monarc: `references/voice.md`, `references/mycopy.md`, and `references/cold-call-principles.md` (every line has one job). At a client: three samples the owner hands over. No hedges, no em dashes, 60 to 120 words, the ask is two times and a length.
- **The send rule.** "Pre approved messages get sent." A message he approved goes out by itself inside the daily cap. An approval covers the words, the list, and the cap; a change to any of the three needs a new approval. Anything not approved is drafted and waits.
- **Who gets an automated answer.** "Only prospects in the pipeline get automated responses" (Jonathan, 2026-10-05). In the pipeline means a company with an open deal on the CRM's Pipeline board, or a row on a list the SDR is working (that is the Cold stage). The second half is the AIOS's reading of "pipeline", his to change. Mail from anyone else is sorted and left for him; nothing automated goes back to it.
- **A response cancels the drip.** "A response cancels the drip sequence" (same day). Any answer from the prospect, on any channel, ends every sequence that prospect is in, at once. What happens next is a person's call or the inbox replies workflow, never the next touch of the drip.
- **Copy tests land in his inbox.** "Hit my inbox as if I were an integrator..." (same day). To let him read copy the way a prospect would: `python scripts/proton_mail.py inbox-test <spec.txt>` lays one unread message in his own INBOX from the SDR's address. Nothing goes to anyone. The scene he names (the trade, the signal) fills the slots.
- **Price.** No message states a price until the offer page is rewritten (`context/offer.md`, on hold since 2026-10-05). Price is said on the call.
- **The list** comes from `/list-building`: a Google Maps pull, Clay for the owner's name, email, and LinkedIn URL, then the signals. The signal beside a row picks which line the message carries.
- **The record.** Every touch, reply, and booking is logged with its source. Replies are sorted: interested, not now, no, wrong person, stop. A stop is never contacted again, by any workflow.
- **Booking, at Monarc.** Every time is offered in the prospect's time zone with Eastern beside it. Everything they see from booking to the call says "we" and "Monarc Build", never his name. Events come from jonathan@monarcbuild.com only (`CLAUDE.md`, "How you work with me").
- **Never without a go.** The first real send of any workflow. Raising a cap. Paying for data or a tool. And never, with or without a go: a message to anyone sorted "stop" or on the do-not-contact list.

## Modes

- `draft`: write or rewrite the copy of one workflow, for his read.
- `approve`: record his approval on the workflow's file and the install record.
- `install`: put an approved workflow in place at Monarc or a client (the steps are in the workflow's file).
- `check`: the monthly read of one workflow's numbers. What to change in the copy is the coach's call once that skill exists; until then it is his.

## The install record

`projects/clients/<slug>/sdr.md`, one per company. Monarc's own is `projects/clients/monarc-build/sdr.md`: the intake, the access table, his approvals with dates, and the four workflows' state.
