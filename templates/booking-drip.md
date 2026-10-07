# Booking emails (the /av_marketing/ calendar step)

Jonathan's spec, 2026-09-23: the prospect gets a confirmation with the Google Meet link, the time, and who they will be speaking with; one hour before the call they get a reminder; Jonathan gets an email with their details. Added 2026-10-03 (the Meta plan, Q25): a second reminder the afternoon before the call, for every site booking. Sent by the Apps Script backend (`scripts/avmarketing-booking.gs`) when a prospect confirms a time on monarcbuild.com/av_marketing/. The script holds a copy of each email, so change both together, then paste the file into the script project again and redeploy as a new version.

Rules they follow: first name, comma, the point; under 120 words; no hedges; no em dashes; no callback-time promise; one job per email; no person's name anywhere the prospect reads (Jonathan, 2026-10-01: "My name should not be used throughout this process"), so "My Best, Monarc Build" on the first touch, "Monarc Build" after; Times New Roman 12pt HTML part with a plain text twin. Reply-to is jonathan@monarcbuild.com. The sender is the Google account the script runs under, display name "Monarc Build" (was "Jonathan Beach" until 2026-10-01).

Placeholders: `{first}` first name; `{when}` the time in the prospect's zone, with Eastern in brackets when the zones differ ("Thursday, Sep 24, 11:00 am PDT (2:00 pm EDT Eastern)"); `{time}` the clock only; `{meet}` the Google Meet link.

## 1. Confirmation, sent the moment the booking lands

Subject: Booked: {weekday} at {time} with Monarc Build

```
{first},

Booked. {when}. Fifteen minutes on Google Meet: {meet}

Before the call we pull your search results, your pages, and your ad account. Reply with your site URL and the metro you sell in and the audit goes deeper.

Reminders with the same link come the afternoon before and an hour before. Bring nothing.

My Best,
Monarc Build
```

The Google Calendar invite (with the same Meet link) arrives separately from the calendar itself. Its headline is Google's format around our title: "Invitation: Monarc Build audit: {first name} @ {time}". Its description reads, to the prospect:

```
Fifteen minutes on Google Meet with Monarc Build.

Before the call we pull your search results, your pages, and your ad account. You leave with the audit either way. Bring nothing.

Questions before then: jonathan@monarcbuild.com
```

The internal fields (phone, technicians, page, time zone, UTMs, landing URL) are stored on the event as private properties the invite never shows (Jonathan, 2026-09-23: "the unnecessary parts should be removed"); they stay in the notification email and the sheet.

## 2. Reminder, the afternoon before (added 2026-10-03; sent at 4:00 pm Eastern the day before the call, skipped when the booking lands after that; a Monday call gets it on Sunday)

Subject: {day} at {time}: your Monarc Build call

`{day}` is "Tomorrow" or the weekday ("Monday"), from the script's `dayWord`.

```
{first},

{day}, {when}. Fifteen minutes on Google Meet: {meet}

Before the call we pull your search results and your pages. If the time no longer works, reply with two others.

Monarc Build
```

## 3. Reminder, one hour before the call (skipped when the booking is made inside that hour; the confirmation already carries the link)

Subject: In one hour: your Monarc Build call, {time}

```
{first},

Your Monarc Build call is in one hour, at {time}. Fifteen minutes on Google Meet: {meet}

If the time no longer works, reply with two others.

Monarc Build
```

The queue checks every five minutes, so the reminder lands 55 to 60 minutes before the call.

## 4. Notification to Jonathan, sent with the confirmation

Subject: Booked: {name}, {Eastern day and time}

```
{name} booked {Eastern day and time}.

Email: {email}
Phone: {phone}
Technicians: {technicians}
Check: installs {installs}; last five {last five}; ads today {ads today}. Fit: {ok or not a fit}   (only for a /builder-check/ booking, 2026-10-03)
Their time: {local time} ({time zone})
Meet: {meet}
Event: {event id}
Page: av_marketing  Source: {utm_source}  Campaign: {utm_campaign}  Content: {utm_content}  Id: {utm_id}
Landing URL: {landing_url}

Drip: confirmation sent now; enrichment off; day-before {due or skipped}; reminder {due or skipped}.
CRM: {posted, skipped, or the error}.
Sheet: Monarc bookings (script properties SHEET_ID).
```

Reply-to on this one is the prospect, so a reply from Jonathan goes straight to them.

## Switched off: "Before our call" (enrichment)

Kept in the script behind `ENRICH_ENABLED = false`. Setting it to `true` sends this three hours after booking (or 8:00 am Eastern the next morning when booked after 5 pm):

```
{first},

One example of what we look for. We ranked an integrator #1 for "whole home audio in Annapolis." A contractor restoring a Georgian Colonial found the page: $70k of James Loudspeaker, wired from rough-in. That one contractor is now over $500k in lifetime value.

On the call we walk your search results the same way: what ranks, what the ads are buying, and what a page per service would change. You leave with the audit either way.

{when}. Meet link: {meet}

Monarc Build
```

## What is not in the emails

- No price, no terms, no "no setup fee" (Style Guide 6.7; the terms are stated on the call).
- No PHA name or link.
- No callback-time promise (Style Guide Copy 9).
- No second follow-up after a no-show; Jonathan sends "Rebook after a miss" from `references/mycopy.md` by hand.
