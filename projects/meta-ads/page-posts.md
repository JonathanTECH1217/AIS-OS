# Three posts for the Monarc Build Page before the ad runs

Drafted 2026-10-03 (interview Q23, Q29). The Page is new; a prospect who taps the ad's profile should find a company, not an empty page. Jonathan approves each post here, then posts it on Facebook and Instagram himself. The ad waits a week of Page age.

Rules: no person's name; no dollar figure; no PHA; no price; no "no setup fee"; no tenure; the register of `references/voice.md`. Each post carries a link to the site with its own labels so a booking counts: `?utm_source=facebook&utm_medium=social&utm_campaign=meta-page&utm_content=post-1` (post-2, post-3; Instagram has no links in captions, so the bio link only). The Campaigns row "Facebook Page: button and posts" (Platform id `meta-page`, 2026-10-03) catches every booking from the button, the bio, and the posts, under Organic social on the journey map.

## The Page's action button (Jonathan asked 2026-10-03: "How should I make my Facebook button?")

- **Book now**, with "Link to website" (not "Appointments on Facebook"; the calendar lives on the site, and a Messenger or WhatsApp button would make every lead a chat to chase by hand, and chats never reach the CRM).
- The link, until `/builder-check/` is live:

  ```
  https://monarcbuild.com/av_marketing/?utm_source=facebook&utm_medium=social&utm_campaign=meta-page&utm_content=button
  ```

  Once `/builder-check/` is live, the same labels on that address. One edit.
- The Instagram bio link is the same address with `utm_source=instagram&utm_content=bio`. Instagram's own "Book now" button only works through partner apps, so the bio link is the booking path there.
- A click lands on the page, and the visitor taps "Book an appointment" (the page opens its popup only from its buttons). Facebook adds `fbclid` to the link on its own; the popup keeps it from the pending push onward.
- Not "Call now" (no footer phone yet, and a call is unqualified), not "Learn more" (says nothing), not "Send message" or "WhatsApp" (a manual loop).
- Write a one-line test after the Page exists: tap the button on your phone, book a slot from a non-Monarc address, check the Leads row carries Source meta-ads, campaign "Facebook Page: button and posts", and `utm_content=button`; then delete the test event.

## Post 1: the proof photo

Media: `media/assets/proof/waterfront-great-room.jpg` (the Lutron Ketra great room; crop 4:5 for the feed, 1:1 for the grid).

Caption:

> A waterfront great room. Lutron Ketra lighting, tuned to the water and the time of day.
>
> The homeowner found the integrator on a search. Not a referral, not a lunch and learn. A search.
>
> We put integrators on the first page for the systems they sell, in the towns they sell them in. monarcbuild.com/av_marketing/

Link in the post: `https://monarcbuild.com/av_marketing/?utm_source=facebook&utm_medium=social&utm_campaign=meta-page&utm_content=post-1`

## Post 2: a talk to camera

Media: one 20-second talk-to-camera cut from a recorded calling session (Monarc Studio, `media/projects/`; his words in blue captions, no prospect's voice, no company named). Jonathan picks the clip; the AIOS has none picked yet. Pick a bit where he explains why integrators are not on page one, between dials.

Caption:

> Between calls. Every integrator says the same thing: most of our work is referrals.
>
> Then we search their city. They're not there.
>
> monarcbuild.com/av_marketing/

Link in the post: `https://monarcbuild.com/av_marketing/?utm_source=facebook&utm_medium=social&utm_campaign=meta-page&utm_content=post-2`

## Post 3: who we are

Media: the butterfly on white, `media/assets/brand/monarc-build-butterfly.png`, with the wordmark under it (`media/assets/brand/monarc-build-logo.png`), 1:1.

Caption:

> Monarc Build. Marketing for AV integrators, built by installers.
>
> Google Ads, websites, and local search for shops that install Lutron, Control4, Crestron, and Savant in high profile homes.
>
> Fifteen minutes on Google Meet. Before the call we pull your search results. You leave with the audit. monarcbuild.com/av_marketing/

Link in the post: `https://monarcbuild.com/av_marketing/?utm_source=facebook&utm_medium=social&utm_campaign=meta-page&utm_content=post-3`

## Page setup, so the posts land on something

- Profile photo: `media/assets/brand/monarc-build-butterfly.png`. Cover: the wordmark on white (`media/assets/brand/monarc-build-logo.png`), or the Georgian exterior (`media/assets/proof/georgian-exterior.jpg`) with the wordmark; no job figure on it.
- About: "Marketing for AV integrators, built by installers. Google Ads, websites, and local search for home integrators." Website `https://monarcbuild.com/`. Email jonathan@monarcbuild.com. No phone until the footer number exists (`tasks.md`).
- Category: Marketing agency. Location: Riva, Maryland, with the street hidden (the NAP in `tasks.md`, NAP citations).
- Instagram: the same photo, the same About line, the site link in the bio, linked to the Page in Business Manager.
