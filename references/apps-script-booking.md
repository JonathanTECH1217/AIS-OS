# Google Apps Script booking backend (monarcbuild.com/av_marketing/ and the homepage popup)

Domain: booking, `connections.md` row 15. Added 2026-09-14; extended 2026-09-23 with the calendar action, the bookings sheet, the email to Jonathan, and the drip to the prospect. Goal: when a prospect confirms a time on the page, the event lands on the business calendar with a Google Meet link, the invite goes to the prospect, Jonathan gets the details, and the prospect gets a confirmation, an enrichment email, and a reminder, with no server and no secret on Hostinger.

## What it is

One Apps Script web app in Jonathan's Google account (the account that owns "My Calendar ", `connections.md` row 3). Source: `scripts/avmarketing-booking.gs`. Two pages use it: the ad page `/av_marketing/` (calendar step) and the homepage booking popup (first open day). Same URL and token in both pages' `BOOKING_URL` and `BOOKING_TOKEN`.

- `GET <url>?action=calendar` returns every open afternoon slot for the next `DAYS_AHEAD` (14) days, keyed by Eastern date, as ISO instants. The ad page groups them by the prospect's local date and draws the month grid.
- `GET <url>?action=slots` returns the first weekday with open afternoon slots (the homepage popup still uses this).
- `GET <url>?action=agenda&days=2` returns the events on the business calendar and the account's own calendar for today and the next day (title, start, end, calendar, Meet link, guests). The CRM's Today screen reads this through the local server (`/api/agenda`, cached five minutes) to lay the day out: meetings, the dial hour, booked calls. Added 2026-09-23; needs the file pasted and published as a new version before it answers. Since 2026-10-05 Today no longer waits on it: the CRM reads both calendars with the Monarc login (`scripts/google_calendar_api.py`), and this action is only the fallback when that login is missing.
- `POST <url>` with `{token, start, name, email, phone, technicians, page, viewer_timezone, utm_*}` creates the 15 minute event on the business calendar with a Meet link and lets Google Calendar send the invite (`sendUpdates: all`). Then, in order: the confirmation email to the prospect, a row in the "Monarc bookings" sheet, the details and Meet link emailed to `NOTIFY_TO` (reply-to set to the prospect). Returns the event id and the Meet link, which the page also puts into the formsubmit email.
- **CRM (2026-09-23):** after the sheet row, `postLead` writes one row to the Monarc CRM Leads table (`references/airtable-api.md`) with the name, email, phone, Status Booked, the call's start in `Call at`, the team-size answer in `Technicians`, the raw UTM string, the calendar event id as External id, and links by name for Source (channel read from the UTMs, `references/attribution.md`), Campaign (by Platform id, else name), Keyword, and Landing page (by URL). The CRM turns each such lead into a deal on the pipeline board the next time the board is read (Booked stage, "Hold the call" dated the call day, company and contact by the key rules, a Meeting activity on the timeline); Today's "Booked calls" panel reads the call time. Off until `AIRTABLE_TOKEN` is set in the script's properties; the notification email says "CRM: posted", "skipped", or the error. Company is left to the dashboard and the inbox pass. `crmSelfTest` reads the Sources table and writes nothing.
- `processQueue()` runs every 5 minutes from one recurring trigger. It reads the sheet, sends the reminders when they come due, marks a booking cancelled when the event is deleted or the prospect declined, and marks it done an hour after the call.
- **2026-10-03 (the Meta plan, in the file, live at the next republish):** a second reminder the afternoon before the call (4:00 pm Eastern the day before, `DAYBEFORE_HOUR`; skipped when the booking lands after that); `fbclid` captured like `gclid`; the builder search check's answers (`installs`, `last_five`, `ads_today` from `/builder-check/`) written to the Leads row (fields Installs, Last five, Ads today, created 2026-10-03) and to a "Check: ... Fit: ok | not a fit" line in Notes and in the notification; the landing page path from the page label by `pagePath` (`facebook_ads` reads as `/facebook-ads/`, `home` as the root, `av_marketing` kept). The bookings sheet grows by itself: `sheet()` appends the six new header cells (`daybefore_due`, `daybefore_sent`, `installs`, `last_five`, `ads_today`, `fbclid`) at the end of the header on the first run, so no sheet edit is needed. `dripSelfTest` now sends four sample emails.

Email flow (Jonathan's spec, 2026-09-23): the prospect gets a confirmation at once with the Google Meet link, the time, and who they will be speaking with (Jonathan Beach, head consultant); one hour before the call they get a reminder with the same link (skipped when the booking itself lands inside that hour); Jonathan gets the details with the confirmation. The "Before our call" email stays in the script behind `ENRICH_ENABLED = false`. Copy: `templates/booking-drip.md` (the script holds a copy of each email; change both together).

Conflicts are checked against every calendar in `BUSY_CALENDARS` (business plus the account's primary). A script lock and a re-check at booking time stop two prospects taking the same slot. The script runs as Jonathan, so the calendar does not need to be public.

## Setup, click by click (Jonathan, 2026-09-23, about 20 minutes)

What you are making: a small program that lives inside your Google account. The web page asks it two things: "what times are open" and "book this one." It answers by reading and writing your calendar as you. Google runs it; there is nothing to install and nothing to pay. The page cannot do this itself because it would need your Google login.

### Part 1. Make the program (5 minutes)

1. In Chrome, sign out of any other Google account, or open a new Incognito window. Sign in as the account that owns the business calendar: `sumreat17@gmail.com`.
2. Go to https://script.google.com. You see "Apps Script" with a list of projects, probably empty.
3. Top left, click **New project**. A code editor opens. The tab says "Untitled project". The big box holds a few lines starting `function myFunction()`.
4. Click "Untitled project" at the top. A rename box opens. Type `monarc-avmarketing-booking`. Click **Rename**.
5. On this machine, open `scripts/avmarketing-booking.gs` in VS Code. Press Ctrl+A, then Ctrl+C. It is the whole file, about 450 lines.
6. Back in the browser, click inside the big code box. Press Ctrl+A, then Ctrl+V. The default lines vanish and the file takes their place. The first line should read `/**` and the second should mention "Monarc Build booking backend".
7. Press Ctrl+S, or click the floppy disk icon above the code. The word "Saved" flashes near the top.

### Part 2. Turn on the calendar service (1 minute)

8. On the left rail, find **Services**. It has a plus sign next to it. Click the plus.
9. A window titled "Add a service" opens with a long list. Scroll to **Google Calendar API** and click it once. On the right it shows Identifier `Calendar`, version `v3`. Click **Add**.
10. "Calendar" now appears under Services on the left rail. Without this the program cannot make Google Meet links.

### Part 3. Run the four checks (5 minutes)

Above the code there is a toolbar: **Run**, **Debug**, then a dropdown that names a function (it starts on `doGet`). Each check below is: pick the name in that dropdown, click Run, read the log that opens at the bottom.

11. Pick `setup`. Click **Run**. The first time, a box says "Authorization required". Click **Review permissions**. Pick the `sumreat17@gmail.com` account. Google then says "Google hasn't verified this app". Click **Advanced** (small text, bottom left), then **Go to monarc-avmarketing-booking (unsafe)**. It is your own program; "unsafe" is Google's word for "not reviewed by us". Click **Allow**. The run finishes and the log at the bottom shows a line "Bookings sheet:" with a link. That link is a new Google Sheet named "Monarc bookings" in your Drive. Every booking lands there as a row. Bookmark it.
12. Pick `selfTest`. Click **Run**. Another permission box may appear for the calendar; approve it the same way. The log shows three lines: the next open afternoon times, "Open days in the window: N", and "Book calendar: Monarc Build" (the calendar's name; Jonathan's run on 2026-09-23 at 4:58 pm showed Thursday's four slots and ten open days). If it says "NOT FOUND", the calendar id at the top of the file is wrong; stop and tell me.
13. Pick `installQueue`. Click **Run**. The log says "processQueue runs every 5 minutes." On the left rail, the clock icon (**Triggers**) now lists one row. That is the timer that sends the one-hour reminder.
14. Pick `dripSelfTest`. Click **Run**. Three emails arrive in the inbox of the account the script runs under within a minute: the confirmation, the one-hour reminder, and the notification you would get. Read them. They are the words a prospect will get. Changes go in `templates/booking-drip.md` and I put them into the file.

### Part 4. Publish it and get its address (3 minutes)

15. Top right, blue button **Deploy**. Click it, then **New deployment**.
16. A window opens. Next to "Select type" there is a gear icon. Click it and pick **Web app**.
17. Three fields appear. Description: type `v1`. Execute as: leave **Me (sumreat17@gmail.com)**. Who has access: change to **Anyone**. This lets the public web page call it. It still cannot read anything except open times, and it cannot book without the shared password in the file.
18. Click **Deploy**. It may ask for permission once more; approve. A window shows "Deployment ID" and, under it, **Web app URL**, a long address that starts `https://script.google.com/macros/s/` and ends `/exec`. Click **Copy** next to it. Click **Done**.

### Part 5. Prove it answers (1 minute)

19. Open a new browser tab. Paste the address and add `?action=calendar` to the end. Press Enter. You should see text like `{"ok":true,"days":{"2026-09-24":["2026-09-24T17:00:00.000Z", ...`. Plain text, no styling, is right. If you see a Google sign-in page or "Sorry, unable to open the file", the "Who has access" setting was not Anyone; do Part 4 again.

### Part 6. Hand the address to the AIOS (1 minute)

20. In VS Code, open the file `.env` in the AIOS root folder (`C:\Users\sumre\Documents\GitHub\AIS-OS\.env`). It already has Hostinger lines. Add one line at the bottom: `BOOKING_URL=` followed by the address you copied, no spaces, no quotes. Save.
21. In this chat, type: **wire it**. I read the address from `.env`, write it into the ad page (and the homepage draft), push the ad page, and check the live page. From that moment the three buttons open the popup and its last step shows your live calendar. Nothing else changes.

Why `.env` and not chat: the transcript is kept; the address is not a secret exactly, but anyone holding it can post junk bookings, so it stays out of text that gets copied around.

### Part 7. The CRM hookup (optional, 5 minutes, needed before the LinkedIn flight)

This makes each booking appear in your CRM dashboard as a lead with its ad source.

22. Go to https://airtable.com/create/tokens. Click **Create new token**. Name: `Monarc booking script`.
23. Under Scopes, click **Add a scope** twice and pick `data.records:read` and `data.records:write`.
24. Under Access, click **Add a base** and pick **Monarc CRM**. Click **Create token**. A long string starting `pat` shows once. Click **Copy**.
25. Back in the Apps Script tab, left rail, gear icon **Project Settings**. Scroll down to **Script Properties**. Click **Add script property**. Property: `AIRTABLE_TOKEN`. Value: paste the token. Click **Save script properties**.
26. Back in the editor (the `< >` icon on the left rail), pick `crmSelfTest` in the dropdown, click **Run**. The log lists your channels: cold, google-ads, google-organic, email, linkedin, meta-ads, and a few more. That proves the token reaches the base. Nothing was written.
27. In Airtable, open the Monarc CRM base, the **Landing pages** table. Add a row: URL `https://monarcbuild.com/av_marketing/`, Name `AV contractor booking page`, Status `Live`. Leads then link to a named page.

### Part 8. One real test (5 minutes)

28. Open the live page in an Incognito window with the LinkedIn parameters on the address, for example `https://monarcbuild.com/av_marketing/?utm_source=linkedin&utm_medium=paid-social&utm_campaign=test`.
29. Click **Book an appointment**. Fill the five steps with a personal email of yours as the prospect. Pick a time. Click **Confirm appointment**.
30. Expect, within a minute: the event on the business calendar with a Meet link; an invite in the personal inbox; the confirmation email in the personal inbox; a row in the "Monarc bookings" sheet; the notification in jonathan@monarcbuild.com saying "CRM: posted" (or "skipped" if Part 7 was not done); and, if Part 7 was done, a lead in the CRM under the LinkedIn channel with `utm_campaign=test` on it.
31. Delete the test event from the calendar. Within 15 minutes the sheet row reads `cancelled` and no follow-up emails go out. Delete the test lead in Airtable.

### Later changes to the program

When I change the file, you repeat steps 5 to 7 (paste the new file, save), then **Deploy**, **Manage deployments**, the pencil icon, **Version: New version**, **Deploy**. The address stays the same, so the page needs nothing.

## Setup, the short list (same steps, terse)

1. Open https://script.google.com signed in as the calendar owner (`sumreat17@gmail.com`). New project. Name it `monarc-avmarketing-booking`. (An existing project from the 2026-09-14 version: replace its code and re-run steps 4 to 7, then Deploy, Manage deployments, New version; the URL stays.)
2. Replace the editor contents with `scripts/avmarketing-booking.gs`.
3. Left sidebar, Services (+), add **Google Calendar API** (identifier `Calendar`). This is the advanced service that can create Meet links; the plain `CalendarApp` cannot.
4. `TOKEN` is already set in the file (the AIOS generated it 2026-09-23 and wrote the same value into `BOOKING_TOKEN` on the ad page and the homepage draft). Nothing to do here unless it ever leaks; then change both.
5. Run `setup` from the editor toolbar. Approve the permission prompt (Sheets). The log shows the URL of the new "Monarc bookings" sheet. Bookmark it: it is the lead log.
6. Run `selfTest`. Approve the calendar prompt. The log lists today's open slots, the number of open days in the window, and the calendar name.
7. Run `installQueue`. Approve the trigger prompt. This creates the one recurring trigger (`processQueue`, every 15 minutes).
8. Run `dripSelfTest`. Approve the mail prompt. Four sample emails arrive in the script account's inbox: confirmation, enrichment, reminder, and the notification. Read them against `templates/booking-drip.md`. If the copy needs a change, change the template and the script together.
9. CRM, optional now, needed before the LinkedIn flight: Project Settings, Script properties, add `AIRTABLE_TOKEN` with a personal access token scoped to `data.records:read` and `data.records:write` on the Monarc CRM base only (the same kind of token as `AIRTABLE_PAT` in `secrets.env`; make a second one so a leak here does not touch the dashboard). Run `crmSelfTest`; the log should list the channel rows (cold, google-ads, google-organic, email, linkedin, meta-ads, and the rest). In Airtable, add a Landing pages row with URL `https://monarcbuild.com/av_marketing/`, Status Live, Channel linkedin, so leads link to a named page instead of one typecast creates.
10. Deploy, New deployment, type **Web app**. Execute as **Me**. Who has access **Anyone**. Deploy. Copy the web app URL (ends in `/exec`).
11. Put the URL on its own line in `.env` at the AIOS root as `BOOKING_URL=https://script.google.com/macros/s/.../exec` (not in chat), then tell the AIOS "wire it": it reads `.env`, writes the URL into `BOOKING_URL` on `.../av_marketing/index.html` and the homepage draft, and pushes the ad page. From then on the popup's last step shows the live calendar instead of opening the Google booking page.
12. Verify: open `<url>?action=calendar` in a browser. Expect JSON with `ok: true` and a `days` object.
13. One test booking from the live ad page with a personal email as the prospect, opened through a link that carries the LinkedIn UTMs: event on the calendar, invite received, row in the sheet, a Booked lead in the CRM under the LinkedIn channel with the UTM string on it, notification in Jonathan's inbox saying "CRM: posted", confirmation in the test inbox. Delete the test event and the test lead; within 15 minutes the sheet row reads `cancelled` and no further emails go out.

Changing the script later: Deploy, Manage deployments, edit the existing deployment, Version: New version. The URL stays the same. A brand new deployment gets a new URL and both pages would need it.

## The sender address (Jonathan's call)

The drip sends from the script's Google account (`sumreat17@gmail.com`) with the display name "Jonathan Beach" and reply-to `jonathan@monarcbuild.com`. To send from `jonathan@monarcbuild.com` itself, set `SEND_AS` in the script to that address and add it in Gmail as a "Send mail as" alias (Gmail, Settings, Accounts). Gmail needs SMTP credentials for the alias; Proton gives those only through Proton Bridge or a Business plan SMTP token, so this may not be worth it. Reply-to already lands replies in the Proton inbox.

## Facts to know

- Apps Script web app responses carry `Access-Control-Allow-Origin: *`, so the page can call it from monarcbuild.com. The POST is sent as `text/plain` so the browser does not preflight; the script parses the JSON body itself.
- The URL redirects once (script.google.com to a googleusercontent host). The page's `fetch` follows it.
- Quotas: calendar events 5,000 a day; `MailApp` 100 recipients a day on a consumer Gmail account (about 25 bookings a day at four emails each), 1,500 on Workspace. Time-based triggers are capped at 20 per script, which is why the drip runs from one recurring trigger and a sheet, not one trigger per booking.
- `TOKEN` is visible in the page source. It stops drive-by posts to the script URL, not a determined person. Worst case is a junk event on the calendar and four junk emails, which Jonathan deletes.
- The Meet link is generated by Google when the event is created (`conferenceData.createRequest`). It is the standard Meet code, in the invite email, on the event, and in every drip email.
- Time zone: slots are computed in Eastern inside the script. The page formats them in the prospect's zone and shows Eastern beside them when they differ; the emails do the same using `viewer_timezone` from the page.
- The sheet id lives in the script's properties (`SHEET_ID`). Deleting the sheet makes `setup` create a new one on the next run.

## Rules

- The invite comes from Google Calendar as the organizer. The drip and the notification come from the script account (or `SEND_AS`), reply-to Jonathan. (Rule changed 2026-09-23; until then the script never sent mail.)
- The formsubmit.co email to Jonathan still goes out from the page with the UTMs and the Meet link, so a booking arrives twice: once from the script with the drip schedule, once from formsubmit with the ad set. Drop the formsubmit post from the page only after the script has run clean for a month.
- Do not put the script URL or token in chat once set. If either leaks, redeploy and rotate.
- No price, no terms, no "no setup fee", no PHA name in any email the script sends.

## Status

- [x] Script created and Calendar API service added (Jonathan, 2026-09-23, about 4:50 pm)
- [ ] `setup` run, bookings sheet created, URL bookmarked (not in the logs Jonathan pasted; check Drive for "Monarc bookings"; the first booking creates it anyway)
- [x] `selfTest` run, calendar scopes granted (4:58 pm: Thursday's four slots, 10 open days, calendar "Monarc Build")
- [ ] `installQueue` run, one recurring trigger in place (not in the logs pasted; check the clock icon on the left rail; without it no follow-up or reminder goes out)
- [x] `dripSelfTest` run, four sample emails sent to the script account (4:59 pm); Jonathan to read and approve the wording
- [x] `AIRTABLE_TOKEN` set in Script properties; `crmSelfTest` listed all eleven sources (Jonathan, 2026-09-23, 9:56 pm). The Landing pages row for /av_marketing/ is created by the first booking (typecast on the link field).
- [x] Deployed as web app; URL in `BOOKING_URL` on the ad page and the homepage draft, and in `.env`; token in both pages. First deployment 5:05 pm under `sumreat17`; a second deployment address arrived about 5:40 pm (the file with the three-email flow and the five-minute queue, and, if Jonathan did the move, the `jonathan@monarcbuild.com` account) and was wired and pushed; the first address answers still and should be archived in its project, with its trigger deleted, so only one queue runs
- [x] `?action=calendar` returns JSON (checked from the AIOS: `ok: true`, days from 2026-09-24)
- [ ] `?action=agenda` returns JSON. Added to the file 2026-09-23 about 6:20 pm for the CRM's Today screen; the address online still answers `unknown action`. Paste the current `scripts/avmarketing-booking.gs` over the project's Code.gs, Deploy, Manage deployments, pencil, Version: New version, Deploy. Same address, no page change. The CRM checks again within a minute.
- [x] One test booking from the live page (Jonathan, 2026-09-23, about 5:10 pm, with the LinkedIn test parameters): the event landed on the Monarc Build calendar with name, phone, technicians, page, time zone, and the UTMs. Not yet confirmed: the invite and confirmation in the test inbox, the sheet row, the notification in Proton, and the cancel test. Jonathan's note: the event reads "Created by: sumreat17@gmail.com" and he wants jonathan@monarcbuild.com (see "Whose name is on it" below).

## Whose name is on it (Jonathan, 2026-09-23)

"Created by" on a Google Calendar event is always the Google account that made it, and the program makes it as the account it runs under. To read `jonathan@monarcbuild.com`, that address has to be a Google account and the program has to run there. Two ways, and what each changes:

- **Google Workspace for monarcbuild.com (about $7 a month, Business Starter).** `jonathan@monarcbuild.com` becomes a full Google account: calendar, Meet, Apps Script, and Gmail sending. Mail keeps arriving in Proton as long as the domain's MX records are left alone; only a TXT record is added to prove the domain. Result: the event's creator, the invite's organizer, and the From line on the three prospect emails all read `jonathan@monarcbuild.com`. This is the complete fix.
- **A free Google account that signs in with the Proton address.** At accounts.google.com/signup, "Use my current email address instead" makes a Google account whose login is `jonathan@monarcbuild.com`, with no Gmail. Calendar and Apps Script work, so the event reads created by that address. Open question: Apps Script's mail service on an account with no Gmail mailbox; `dripSelfTest` answers it in one run. If it cannot send, the three prospect emails would have to stay on the Gmail account.

Either way the moves are the same: make the account, share the "Monarc Build" calendar to it with "Make changes and manage sharing" (or make a fresh calendar there and change `BOOK_CALENDAR`), create the script project there (Parts 1 to 5 of the walkthrough), deploy, and hand the new address to the AIOS. The old deployment under `sumreat17` is then deleted. The claude.ai calendar connector stays on `sumreat17`, which keeps reading the shared calendar.

What the prospect sees today: the invite comes from the calendar, "Monarc Build", and the three emails come from "Jonathan Beach" with the Gmail address behind the name and reply-to Proton. "Created by" shows only inside Jonathan's own calendar.

### Moving the program to the `jonathan@monarcbuild.com` Google account (Jonathan already has one, no Gmail; 2026-09-23)

1. In the `sumreat17@gmail.com` calendar (calendar.google.com): left rail, hover "Monarc Build", the three dots, **Settings and sharing**. Under "Share with specific people or groups", **Add people and groups**, type `jonathan@monarcbuild.com`, permission **Make changes and manage sharing**, **Send**.
2. Open an Incognito window, sign in to Google as `jonathan@monarcbuild.com`. Open calendar.google.com there. The shared "Monarc Build" calendar should appear under "Other calendars" (Google emails an invitation; if it is not there, left rail, the plus next to "Other calendars", **Subscribe to calendar**, paste the calendar id from the top of the script file, the long address ending `@group.calendar.google.com`).
3. Still signed in as `jonathan@monarcbuild.com`, do Parts 1 to 3 of the walkthrough again: script.google.com, New project, name it, paste the file, save, add the Google Calendar API service, run `setup`, `selfTest`, `installQueue`, `dripSelfTest`. Same file, same token; nothing in it changes. `selfTest` must say "Book calendar: Monarc Build"; if it says NOT FOUND, step 2 did not take.
4. `dripSelfTest` is the one that can fail here: an account with no Gmail box may not be allowed to send. If the log shows an error instead of "Four sample emails sent", stop and tell me; the calendar part still works and the emails get another route.
5. Part 4 and 5: Deploy as a Web app, Anyone, copy the new address, check it with `?action=calendar` in an Incognito tab.
6. Put the new address in `.env` on the `BOOKING_URL` line (replace the old one) and say "wire it". The AIOS writes it into the page, pushes, and checks.
7. Back in `sumreat17`'s script: **Deploy**, **Manage deployments**, the old deployment, the archive icon. Delete its trigger under the clock icon too, so two queues never run. The "Monarc bookings" sheet in the new account becomes the log; the old one stays as history.
8. The claude.ai calendar connector stays on `sumreat17`; it still reads the shared calendar. The Google booking page behind the no-JavaScript fallback also stays on `sumreat17`; move it later if wanted.

Last checked: 2026-09-23, about 5:05 pm. Deployed and wired; the live calendar step is on.
