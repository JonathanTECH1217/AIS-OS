# Kickoff questionnaire

Seven blocks, dependency order. Jonathan reads the bold line aloud. "Look up" marks questions the prep should answer from the client's site or listing before the call; confirm those in one line instead of asking. "Feeds" names the skill or loop that needs the answer (skills per `references/github-skills-shortlist.md`; loops per `context/roadmap.md`).

Target: 45 minutes. Blocks 1, 3, and 4 are required for the build to start. Blocks 2, 5, 6, and 7 can finish by email if time runs out.

The client-fill subset of Blocks 1 and 2 is `templates/onboarding-questionnaire.md` (repo root); the file and access subset of Block 4 is `templates/asset-request-email.md`. Returned answers sit in the capture's "Already known" block; confirm, do not re-ask.

## Block 1: business and offer

Feeds: service x city pages (`programmatic-seo`, `site-architecture`), ad groups (`ads`), First Responder qualification, `context/icp-brands.md` read-back.

1. **Which services do you sell, and which three make you the most money?** Look up: the site's service list. Ask for the ranking. Map to the categories in `context/icp-brands.md` (control, lighting, shades, distributed audio, theater, video, networking, security, energy).
2. **For each of those services, which brands do you spec first?** Read the answer against `context/icp-brands.md`. Note any brand not on the map; it goes on the page and into the ad copy.
3. **Which cities and neighborhoods do you actually want work in? Which do you turn down?** Output: an ordered city list (this is the "per service area" in the offer) and an exclusion list. Ask for the drive-time limit if the list is vague.
4. **What is the smallest project you want us to send you? Give me a dollar number.** This is the pricing floor First Responder qualifies against. Suggest a floor from the proof jobs if the client hesitates, labeled as a suggestion.
5. **What does a typical project run, and what was your biggest in the last two years?** Average ticket and ceiling. Used in ad bidding and on the proof tiles.
6. **Hours, and who picks up after hours?** Feeds the GBP listing and the after-hours rule (First Responder calls at 9am next business day).
7. **Licenses, certifications, dealer status we can put on the page?** Look up: dealer locators for Crestron, Control4, Savant, Lutron, Josh.ai. Confirm. Never print a claim the client cannot show.

## Block 2: proof

Feeds: landing page proof tiles (`landing-page`, `cro`), GBP posts and photos, `/seo local`.

8. **Name three finished projects you are proud of: what was in them, the dollar value, and whether we can use photos.** One per top service if possible. Ask for the photos to be sent to Jonathan's email today. No client names on the page without written permission; dollar figures and product names are fine.
9. **Where do your reviews live today, and how many?** Look up: GBP review count and rating, Houzz, Yelp. Confirm. Feeds the review-request step in local SEO.
10. **Who do you lose jobs to, and why?** Two or three competitor names. Feeds the competitor page check and the ad negatives.
11. **Which builders, architects, or designers send you work now?** Names go in the brief for the Proof loop and future referral asks. Not for outreach; that offer is off the menu.

## Block 3: lead handling

Feeds: attribution model (`attribution`), event plan (`analytics`), First Responder script, booking flow.

12. **When a lead comes in today, how does it arrive, who sees it, and how fast does someone call back?** Form to which inbox, phone to whose cell, DMs. This is the baseline the weekly PDF gets compared to.
13. **Where do leads get written down now?** CRM, D-Tools or Portal, a spreadsheet, nothing. Decides whether Monarc's lead log is the only log or syncs to theirs.
14. **What makes a lead qualified for you, beyond the dollar floor and the area?** Homeowner vs builder, new build vs retrofit, timeline. These become the First Responder qualifying questions.
15. **Which calendar should booked appointments land on, and who owns it?** Google Calendar, Outlook, iCloud. The owner grants sharing in block 4. If the client has no shared calendar, propose a Google Calendar appointment schedule.
16. **Is a tracking phone number on the site and the GBP listing acceptable?** Needed for call attribution. If no, calls are attributed by asking "how did you hear about us" on every First Responder call, and the brief says so.
17. **Who at your company can say yes to a landing page, and how fast?** One approver, one turnaround. Feeds the 14 day build.

## Block 4: access

Run `access-checklist.md` top to bottom on a shared screen. Record the ID and status for each row; never a password. Required before the build starts: Google Business Profile, Google Ads, domain and DNS, hosting or site source, calendar. GA4, Search Console, and GTM can be created by Monarc if the client has none.

18. **Let's open your Google Business Profile together and add jonathan@monarcbuild.com as a manager.**
19. **Do you have a Google Ads account? Read me the customer ID from the top right.** Monarc sends a manager link request; the client accepts it. Confirm who pays: the client's card on the account (ad spend is on top of the retainer).
20. **Google Analytics: do you have a property? If yes, add Jonathan as Editor. If no, we create one.**
21. **Search Console: same question.** Verified owner adds Jonathan as a full user.
22. **Google Tag Manager: same question.** Container ID and Publish permission, or Monarc creates the container.
23. **Where is your domain registered, and who has the login?** Registrar name. Monarc needs DNS access only if the site moves to Monarc hosting. Shared logins go to Jonathan's password manager, never to the AIOS.
24. **Who built the site, and do you have the source or an HTML export?** Platform (look up: fingerprint from the prep). Takeover needs the files or an export. If the builder is a third party, get their contact.
25. **Share the booking calendar with jonathan@monarcbuild.com with "make changes to events".**
26. **Which phone provider are you on, and who administers it?** Feeds call tracking when it is built. If a tracking number was approved in Q16, note the provider here.
27. **Any Facebook, Instagram, Houzz, or LinkedIn pages we should have admin on?** Optional. Record the handle and the admin.

## Block 5: reporting and money

Feeds: weekly PDF (`html-report-builder`, roadmap step 16), Money loop (step 17).

28. **Who gets the weekly report, and which weekday?** One or two emails. Suggest Monday.
29. **Monthly ad budget to start, and which card pays Google?** Confirm the $1,000/mo recommended minimum from the offer and the pilot match terms as Jonathan states them on the call. Record the number; the AIOS never adds a price the client did not hear.
30. **One 15 minute meeting a month: which week and time?** Book it recurring on the Monarc calendar after the call.

## Block 6: build

Feeds: roadmap step 14 (build deadline), Proof loop (step 13, day 60).

31. **The build goes live 14 days from today. That is {date}. Does anything on your side block that?** Photos, approvals, DNS. Flag blockers with owners.
32. **If we could rank you first for one search phrase in your area, which one?** The primary term. Cross-check with the top service from Q1. This is the day 60 proof line.
33. **Anything about the business we haven't touched?** Completeness backstop. Always the last question asked, after Block 7. Then stop.

## Block 7: VSL

Feeds: `templates/vsl-draft.md` (the targeting brief and script), the hero video on every landing page (`landing-page`, `cro`). Runs after Blocks 2 and 6 (needs the proof jobs and the primary term) and before Q33. One viewer per video; a second audience gets a second video. If the call runs long, send the client the "Fill-in brief" from `templates/vsl-draft.md` in the recap email with the draft lines pre-filled from Blocks 1, 2, 3, and 6; the eight questions below are the same eleven fields in call order.

34. **Who is the one person this video talks to: a homeowner, a builder, an architect, a designer?** Pick one. Becomes the HOOK and FILTER lines.
35. **When that person lands on the page, what do they want done? Say it the way they would.** Outcome, not service. Becomes NAME and ASK.
36. **What went wrong the last time they hired someone like you? Give me three.** The objections the script pre-empts. Fewer than three, ask again.
37. **Who is on camera, and what have they done with their hands that a homeowner would trust?** Credential in trade words. Cross-check Q7; never a claim they cannot show.
38. **Of the three projects from Q8, which one goes on screen, and do we have the photo or the proposal page?** One artifact. Permission confirmed and noted in the brief.
39. **When they act, what happens in the next five minutes?** Form then a call from a named person (Level 2), a phone number, or a booking link. Becomes LOCK.
40. **Anything we must never say on camera, and anything we must?** Competitor names, unbacked brand claims, price. Dealer status they want heard.
41. **Who records it, where, and by when? Any footage you already have?** Phone or camera, jobsite or showroom, existing walkthroughs. Deadline inside the 14 day build. Hosting (their site or Monarc's) is decided at build.

## After the call, without the client

- Fill `templates/client-brief.md` and `templates/access.md` from the capture.
- Draft the VSL v1 into `projects/clients/{slug}/vsl.md` from `templates/vsl-draft.md`. Jonathan approves before the client sees it.
- Every "flag" becomes a `tasks.md` line with an owner and a date.
- Book the monthly meeting and the day 60 review on the Monarc calendar.
