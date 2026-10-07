# Inbox replies

Workflow of the SDR skill. Status: the watcher runs on test threads and answers a question about times from the calendar; its two answers are drafted, not approved; the SDR's own mailbox is not wired.

One line: Answers the messages that land in the SDR's mailbox.

Jonathan, 2026-10-05: "This SDR skill also needs to be baked in to respond to messages over my email inbox. This is going to be patrick@monarcbuild doing the SDR role for email. He left so we are repurposing this email."

A response workflow. It is where every reply to cold outreach, lead form follow-up, and stale proposal follow-up lands first.

## Objective

Every message in the SDR's mailbox is sorted and answered the same business day. An answer he approved goes out by itself. Anything else is drafted and waits for him.

## What sets it off

A new message in the SDR's mailbox. At Monarc: patrick@monarcbuild.com.

## Steps

1. **Read** what is new, without marking anything read.
2. **Check the pipeline first.** "Only prospects in the pipeline get automated responses" (Jonathan, 2026-10-05). If the sender is not a prospect in the pipeline (`SKILL.md`, "Who gets an automated answer"), sort the message, log it, and leave it for him. Nothing automated goes back.
3. **Cancel the drip.** A response from a prospect ends every sequence that prospect is in, before anything else is done with it.
4. **Sort** each one: interested, a question, not now, no, wrong person, stop, or not a prospect (a vendor, a receipt, a bounce, an out-of-office).
5. **Answer** (prospects in the pipeline only):
   - Interested, or asks for a time: hand to appointment booking.
   - A question with an approved answer: send it.
   - A question with no approved answer, a price question, anything about terms: draft it and wait for him.
   - Not now: log the date they gave, and write again then.
   - No, or stop: block the row for every workflow. One approved line back, or nothing.
   - Wrong person: ask who is, once.
6. **Log** the reply and its sort on the record, on the company's file.
7. **Tell him** what was sent, what waits for him, and what was blocked: one short note a day.

## What is built (2026-10-05)

Jonathan, after answering the test email with "What is your availability this afternoon?": "there's currently no automation in place when I receive something in my inbox that automatically checks for the response and then automates a reply. So this one's asking about availability, which should be an automated response that checks my calendar's availability and then schedules for a meeting."

`scripts/sdr_inbox.py`, settings in `projects/sdr/config.json`, threads in `projects/sdr/threads.json`, every act in `projects/sdr/log.jsonl`.

- `check` is one pass; `watch 60` is a pass a minute; `status` lists the threads. The watcher's process is noted in `~/.monarc/sdr-inbox.json`. It does not start with Windows.
- A reply on one of the SDR's threads: the drip is cancelled, then the reply is sorted by plain rules (the phrases in the config; no model, so no cost per reply).
- A question about times: his two calendars are read with the Monarc login, and two open times are picked inside the hours in the config (9 to 5, the dial hour kept clear, 45 minutes ahead at least, inside working hours on the prospect's clock too). The day and the part of day they asked for is tried first.
- A picked time ("4:30 works", "the first one", "Book me for 3:30"): the meeting goes on the calendar with a Google Meet link, and two messages are written. The answer on the thread is the time and the Meet link and nothing else (Jonathan, 2026-10-05: "it should just respond with the meeting link"). The confirmation is a message of its own in the booking's voice, from "Monarc Build" with no person's name, as on the site ("I was also not sent a confirmation email"). For a real prospect the Google Calendar invite goes out as well, from jonathan@monarcbuild.com, once `send` is on; on a test thread Google sends none, because he is both the owner and the guest.
- Not built: the day-before and one-hour reminders for a meeting the SDR books (the site's booking script sends those only for bookings made on the site), and moving the prospect's deal to Booked on the CRM board.
- Stop: the thread is blocked and nothing goes back. Anything no rule fits waits for him.
- `send` and `book` are off, and the AIOS never turns them on. So today an answer on a test thread is laid in his own INBOX, an answer on a real thread would be laid in Drafts, and only a test thread puts anything on the calendar (a quiet hold, no guest).

First run, 2:18 pm: his reply was read from his Sent folder, the drip was cancelled, and "This afternoon I have 3:30 or 4:30, Eastern. Fifteen minutes on Google Meet. Give me the word and I'll send the invite." was laid in his INBOX. At 2:46 pm he answered "Book me for 3:30"; inside a minute the hold was on his calendar (it shows on the CRM's Today calendar) and a booked note was in his INBOX. That note had no Meet link and there was no confirmation, which he caught; both were fixed and laid again at 2:52 pm.

## The copy

Three answers are drafted in `projects/sdr/config.json` ("copy"), none approved: **times** ("{first}, {the two times}. Fifteen minutes on Google Meet. Give me the word and I'll send the invite. Jonathan."), **booked** ("{first}, Booked. {when}. Fifteen minutes on Google Meet: {the link} Jonathan."), and **confirmation** (subject "Booked: {weekday} at {time} with Monarc Build"; "{first}, Booked. {when}. Fifteen minutes on Google Meet: {the link} Bring nothing. My Best, Monarc Build", the first line of the site's own confirmation in `templates/booking-drip.md`). Still to write, one approved answer each: who we are and how we found them; what it costs (the price is said on the call); not now; no; wrong person. He approves each (the pass).

## At Monarc, what is not there yet

- **Reaching the mailbox.** Checked 2026-10-05: patrick@monarcbuild.com is its own Proton sign-in, not an address on Jonathan's. His reply to it showed in his Sent folder and never came back to his INBOX. So it has to be signed in to Proton Bridge on this machine, with its Bridge user and password put in `.env` as `PROTON_SDR_USER` and `PROTON_SDR_BRIDGE_PASS` (never in chat). Until then the watcher reads test threads only, where he plays the prospect.
- **Sending.** The script places drafts and sends nothing. The send rule ("Pre approved messages get sent") needs a send step for this mailbox, with his go on the first real one.
- **The name on the mailbox.** Patrick left. Mail from this address must not go out under his name.
- **`/inbox`** is a different thing and does not change: it is the boot pass on Jonathan's own mailbox, and it never sends. It still skips mail that comes from patrick@monarcbuild.com, which is now the SDR's own outgoing mail.
- **The form on the site** copies patrick@monarcbuild.com on every lead (`connections.md` row 8), so form fills already land in this mailbox. That is where lead form follow-up picks them up.

## Approvals

None yet.
