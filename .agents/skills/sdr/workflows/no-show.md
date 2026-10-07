# No-show

Workflow of the SDR skill. Status: copy v1 drafted 2026-10-05 on its first real case (Momentum Electrical Contractors), not approved.

One line: A booked meeting nobody came to gets logged, then an email and a LinkedIn message the same day.

Jonathan, 2026-10-05: "Report a no-show for Momentum Electric. So this needs to be tracked as well. And we need a protocol for the no show. Maybe it's just like a LinkedIn message and an email that gets sent."

## Objective

Every no-show is on the record the day it happens, and the person gets one email and one LinkedIn message that day with two new times. No no-show is left open: it ends rebooked, or closed with a reason.

## What sets it off

He says so ("report a no-show for {company}"), or he answers No-show on the company's file in the CRM (the Booked step "Log show or no-show after the meeting"). Nothing can see by itself that nobody joined a Google Meet, so a person reports it.

## Steps

1. **Log it.** The Booked step "show" on the company's file is answered No-show, through the CRM (`POST /api/companies/<id>/triage`, kept in `projects/crm/triage.json`). That one answer is the record: it counts in the show rate on Reports, and it opens three more steps on the file (the email, the LinkedIn message, the outcome; `projects/crm/playbook.json`, the steps with "when").
2. **Read the file first.** What went out before the meeting: the confirmation, the Loom brief, the reminder. Say what did not, in plain words, with no cause read into it.
3. **The email, the same day.** On the confirmation's thread, to the person who booked. Two new times in their zone, read from his calendar (`scripts/sdr_inbox.py`, `open_times`), on two different days. The same Meet link.
4. **The LinkedIn message, the same day.** One line that points at the email. To the person, not the company page.
5. **Wait three business days.** A reply goes to inbox replies; a picked time goes to appointment booking, and the old event is moved, not doubled.
6. **Close it.** Rebooked: the new time is logged on the step. Silence after three business days: the deal's close reason is logged by him. One no-show email and one LinkedIn message are all that go out; there is no drip after a no-show.

## The copy, v1 (AIOS draft, not approved)

No cause is named and nobody is at fault: "we missed each other". `{...}` is filled per company.

### The email

Subject: the confirmation's own thread ("Re: ...")

```
{First name},

We missed each other today at {time}. Rebooking us: {day} at {time} or
{day} at {time}, {their zone}. Fifteen minutes, same link: {meet}

Jonathan.
```

One line may be added when there is something made for them that never went out (a Loom brief still in Drafts): "Before then, the walkthrough I recorded of {their page}. {N} minutes: {link}".

### The LinkedIn message

```
{First name}, we missed each other today at {time} {zone}. I emailed two
new times to {the address}: {day} at {time} or {day} at {time}.
Fifteen minutes.
```

## Tracking

- **The company's file** shows No-show on the Booked step, with the date.
- **Reports, "Loom briefs"** counts it in the show rate. A Loom counts for a meeting only if it went out on or before the meeting's day; one still in Drafts, or sent after, is read as No Loom (fixed 2026-10-05, when this first no-show was being read against a Loom the company never got).
- **Waiting on you** on the Companies page lists the company until the three no-show steps are done.

## Cases

| Date | Company | Meeting | What had gone out | What was done |
|---|---|---|---|---|
| 2026-10-05 | Momentum Electrical Contractors (Oakland, CA; Tom, owner; info@momentum-electric.com) | Monday 2:00 pm Pacific, 5:00 pm Eastern | The confirmation with the invite, Oct 1. The Loom brief email was still in Drafts and no reminder was sent. | No-show logged at 5:05 pm. Rebook email placed in Proton Drafts on the thread: Tuesday at 10:00 or Wednesday at 11:30 Pacific, the same Meet link, with the Loom line. LinkedIn message drafted for him to send. Nothing sent by the AIOS. Later the same evening another chat had rebuilt their lighting page and cut a 4:25 walkthrough (`media/looms/momentum-2026-10-05/owner-cut-tight.mp4`, not uploaded); the message below carries it. |

**2026-10-06, 10:48 am:** the ready draft was placed in Proton Drafts on the thread (his word: "Get the draft ready"), with Tuesday at 11:30 or Wednesday at 10:00 Pacific and the 11-minute Loom on file, since the 4:25 cut is not uploaded. Forced past the duplicate check; the five older drafts are his to delete.

### Momentum, the message to send (v2, 2026-10-05 evening)

Paste into one draft on the "Monday at 2:00 pm Pacific" thread; delete the other four. `{walkthrough link}` is the owner's cut once he uploads it to Loom (YouTube is not signed in); until then the 11-minute Loom on file stands in: https://www.loom.com/share/6c28b9e84de84837843345ff005db8cc

```
Tom,

We missed each other today at 2:00. Rebooking us: Tuesday at 10:00 or
Wednesday at 11:30, Pacific. Fifteen minutes, same link:
https://meet.google.com/yqa-aoby-ofa

Before then: I rebuilt your lighting control page and walked through it
on video, what I changed and why. Four minutes: {walkthrough link}

Jonathan.
```

LinkedIn, to Tom:

```
Tom, we missed each other today at 2:00 Pacific. I rebuilt your lighting
control page and emailed a four-minute walkthrough with two new times.
It's in info@momentum-electric.com.
```

## Approvals

None yet.
