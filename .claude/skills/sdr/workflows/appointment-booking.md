# Appointment booking

Workflow of the SDR skill. Status: the times offer and the booked note are drafted and run on test threads (`scripts/sdr_inbox.py`); not approved. The reminder and the rebook are not drafted.

One line: Turns a yes, or a request for a time, into a meeting on the calendar that the person shows up to.

A response workflow, and its own thing (Jonathan, 2026-10-05: "lead form submission follow-up is different from appointment booking, which would be a response function as well").

## Objective

Every yes becomes a meeting on the calendar the same day, confirmed, reminded, and logged as shown or not.

## What sets it off

A reply sorted "interested", a yes on a call, or someone asking for a time. From cold outreach, from lead form follow-up, or from stale proposal follow-up.

## Steps

1. **Intake:** whose calendar; the meeting's length; the hours it may be booked; what the person must be told before it; who is on it.
2. **Offer two times** in the person's own time zone, or the booking link.
3. **Book it** the moment they pick: the event, the Meet link, the invite.
4. **The copy:** the reply that offers the times, the confirmation, the day-before reminder, the rebook after a miss. He approves it (the pass).
5. **Log** show or no-show.
6. **Monthly check:** yeses in, booked, shown, no-shows, rebooked.

At Monarc these rules already stand (`CLAUDE.md`, "How you work with me"): the time is shown in the prospect's zone with Eastern beside it; everything they see says "we" and "Monarc Build", never his name; the event comes from jonathan@monarcbuild.com only (`scripts/google_calendar_api.py`); the Loom brief goes out before the meeting. Copy on file to start from: `templates/follow-up-email.md`, `templates/booking-drip.md`, and the ask and rebook blocks in `references/mycopy.md`.

## The copy

Not drafted. To write: the times offer, the confirmation, the day-before reminder, the rebook.

## Approvals

None yet.
