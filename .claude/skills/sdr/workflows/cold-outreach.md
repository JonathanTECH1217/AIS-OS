# Cold outreach

Workflow of the SDR skill. Status: copy v2 drafted 2026-10-05 from his mark-up of v1, not approved.

One line: Starts new conversations with people who have never heard of the company.

First written 2026-10-05 as its own skill (`agent-outbound`, then `workflow-outreach`); moved under the SDR the same day.

## Objective

Every week the company starts new conversations with the people it most wants to reach, and every booked meeting lands on its calendar with where it came from. The owner builds no list and writes no first message.

## What sets it off

A list from `/list-building`, approved by the owner's 20-row check.

## Steps

1. **Intake**, one sitting, seven facts: who to reach; where; the signals (the review band, and which of the five website signals count) and three marks of a bad one; the one outcome offered; the proof line; the ask; who answers replies. With it, the do-not-contact list.
2. **The list** from `/list-building`. The cost is quoted and approved before the pull.
3. **The copy** below. He approves it (the pass).
4. **The sending**, in the company's own accounts: a daily cap, stop on any reply. At Monarc the mailbox is patrick@monarcbuild.com (the SDR's address since 2026-10-05; `SKILL.md`, "The SDR's mailbox"). The mail records that prove the sender is real (SPF, DKIM, DMARC) must pass for the sending domain.
5. **A rehearsal.** Ten sends to the owner's own addresses. Then the first 50 real ones, read the next day before the cap goes up.
6. **The record.** Every touch, reply, and booking with its source. A reply goes to the inbox replies workflow; an interested one goes on to appointment booking.
7. **Monthly check.** Sent, delivered, replies by sort, booked, stops, bounces.

## The sequence (Jonathan, 2026-10-06: "I'll just do 20 a day along with connecting on LI and cold call but we do it for the same people across different channels.")

Twenty new companies a day enter it. The same twenty get every channel, in this order. Any reply, on any channel, ends the rest for that company; a yes goes to appointment booking.

| Day | Channel | What |
|---|---|---|
| 0 | LinkedIn | The connection note to the owner. No ask. |
| 1 | Phone | The call in the dial hour. "I sent you a connect yesterday." Book on the call. |
| 2 | Email | Email 1 to everyone the phone did not reach: the signal line, and the rebuilt page's link once batch one exists. |
| 4 | LinkedIn | The message after they accept: the gap and the ask. Skipped if they did not accept. |
| 5 | Email | Email 2, a new angle. |
| 8 | Email | Email 3, the cost of doing nothing. The last touch. |

Twenty a day is the cap in `projects/sdr/config.json` (`daily_new`). The dials ride on the dial hour's quota of 22. The Loom brief comes after a booking, not in the sequence.

## How an email is built (his words, 2026-10-05)

Email 1, in order: **objection stealing**, **permission**, **the angle**, **experience**, **the offer with a small ask**. No footnote: the "Not for you? Reply stop" line is out ("an opt-in that makes it sound automated").

Emails 2 and 3 are not nudges. Each one is **a new angle**. The last one uses **the cost of doing nothing**.

LinkedIn: the connection note only **establishes him**: an introduction, objection stealing, experience (stronger: "high end residential work"), that he used to work in the space, and that he has an offer for their company. No gap line and no ask in the note; those wait for the message after they accept. Several notes are tried against each other.

## The copy, v2 (AIOS draft, not approved)

The job of each line is in brackets and is not sent. `{...}` is filled per row.

### Email 1, day 0

Subject: Your estimate form

```
{First name},

This is a cold email.                                                      [objection stealing]
Delete it anytime.                                                         [permission]

{What I saw.} {The question.}                                               [the angle]

I spent 4 years marketing, selling, and installing low voltage systems
in high end homes.                                                          [experience]

Now I build the follow-up for owners: {what I build}. You approve every
word it sends. Fifteen minutes on Google Meet, and I'll try to sell you
on it: {day} at {time} or {day} at {time}, {their zone}.                    [the offer, a small ask]

My Best,
Jonathan
```

### Email 2, day 3: a new angle, the owner's evenings

```
{First name},

Different angle. When do your leads get answered? If it's at night,
after the job, that's your evening, every evening.

I build it so the answer goes out while you're still on site, in your
words, and the ones that fit land on your calendar. You stay in the
field without missing a call.

Fifteen minutes: {day} at {time} or {day} at {time}, {their zone}.

Jonathan.
```

### Email 3, day 7: the last one, the cost of doing nothing

```
{First name},

Last one from me. One sum to run yourself: what is one job worth to
you? Now count the form fills last month that never got a call back.
That is what the form costs you as it stands.

Fifteen minutes, and I'll show you how I close that gap: {day} at
{time} or {day} at {time}, {their zone}.

Jonathan.
```

### LinkedIn, the connection note: three to try against each other

Each is under 300 characters. None names a gap or asks for a meeting.

```
A.  {First name}, Jonathan with Monarc Build. This is a cold connect.
    I spent 4 years marketing, selling, and installing in high end
    residential work. I have an offer for {company} and wanted to
    connect first.

B.  {First name}, cold connect. I used to work in your space: 4 years
    on high end residential installs. I have an offer for {company}.
    No pitch in this note.

C.  {First name}, we haven't met. I came up in high end residential
    work, 4 years selling and installing it. I built something for
    shops like {company} and I'd like it in front of you.
```

### LinkedIn, after they accept: the gap and the ask

```
Thanks for connecting. The offer: {what I saw} I build the fix:
{what I build}. And so it's said plainly: I'd like 15 minutes to try
to sell you on it. {day} at {time} or {day} at {time}, {their zone}.
```

### The line each signal fills in

One row of the list carries one signal. That signal picks the three slots.

| Signal on the row | What I saw | The question | What I build |
|---|---|---|---|
| An appointment setter | Your site takes estimate requests through a form, and I found no way to book a time on it. | You're on a job when that form comes in. Who answers it? | every form fill gets an answer and a time on your calendar |
| Email follow-up | Your site has a contact form, and I found no email tool behind it. | A lead fills it out Friday night. What do they hear before Monday? | every lead gets a reply and a sequence until they answer |
| A receptionist | Your site has no chat, and I found no sign the phone is answered after hours. | A call comes in at 7 pm. Who picks up? | every call and chat gets answered, and the ones that fit get booked |
| A proposal builder | Your site offers a free estimate and takes it by a plain form. | You walk the job Tuesday. When does the proposal go out? | your notes become a proposal draft the same day, and you review it and send it |
| A new site | Your site is on {builder}. | A buyer lands on it from a search. What do they do next? | a site built to turn that visit into a call |
| A slow reply to a form fill (measured) | I filled out the contact form on your site last {day}. Your reply came {day}. | A homeowner planning a {job} does not wait {N} days. They call the next {trade} on the list. | every form fill gets an answer in your words while you're still on the job, and a walkthrough time on your calendar |

The last row is the one he asked to see first (2026-10-05: "as if I were an integrator that took 2 days to respond to a form submission"). It is only ever sent when it is true: someone at Monarc filled out that company's form, and the two days are on the record. It is not one of `/list-building`'s five signals yet; adding it means filling out forms on prospects' sites and timing the replies, which is his call.

### Test sends to his own inbox

| Date | What | Scene |
|---|---|---|
| 2026-10-05 | Email 1, the slow-reply row, subject "Your contact form, two days", from patrick@monarcbuild.com | An integrator who took two days to answer a form fill |

### Open in this copy, his to settle

- **Who signs.** The mail goes from patrick@monarcbuild.com and the copy is signed Jonathan. The name shown on the mailbox must match the name at the foot, and it must be a person who is there to answer.
- **The proof.** His real proof on file is from ads and a ranked page for an integrator. None of it is about follow-up or booking, so the experience line carries his four years and nothing else.
- **The stop line is out, on his word.** Said once: United States law on sales email (CAN-SPAM) asks each one to carry a way to say stop and a postal address. "Delete it anytime" is not that. Any reply that says no or stop is still honored and blocks the row.
- **Sending from the main domain.** Cold mail from patrick@monarcbuild.com rides on monarcbuild.com's name. If receivers mark it as spam, mail from jonathan@monarcbuild.com can suffer with it. A second domain keeps the two apart.

## Checks before a real send

Not the pass. The pass is his approval of the copy above.

- The owner checked 20 rows of the list and 18 or more were right.
- The sending domain passes SPF, DKIM, and DMARC.
- 10 of 10 rehearsal sends reached the inbox; a reply stopped the sequence; a "stop" blocked the row.
- The owner paused it and started it again himself.

## Approvals

None yet. v1 was marked up by him on 2026-10-05; v2 above carries that mark-up.
