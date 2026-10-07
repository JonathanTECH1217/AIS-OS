# Meta ads: the builder search check

Campaign "Meta: builder search check" (Airtable Campaigns, channel `meta-ads`). Planned 2026-10-03 from a 30-question interview (`brainstorms/2026-10-03-meta-ads-builder-search-check.md`). Status: Planned. Live target Tue 2026-10-20.

## The idea, in one line

A talking-head video on Facebook and Instagram tells AV integration owners that getting specified by builders is a search problem, not a relationship problem, and sends them to a thirty-second check: can a builder in your county find you tonight? The check ends on the booking calendar. The call sells the pilot as is.

## The funnel

1. **The ad.** Vertical video, 30 seconds or under, Jonathan to camera in a finished rack room (Higgsfield puts him there). Three hooks, one ASK: "Can a builder in your county find you tonight? Thirty seconds. Tap and see." Scripts: `scripts.md`.
2. **The page.** `https://monarcbuild.com/builder-check/`, the `/av_marketing/` look (the Google look, eyebrow "Marketing for AV integrators"), `noindex`, page label `builder-check`. Spec: `check.md`.
3. **The check.** Four tiles in the popup, no personal info first: which of these do you install; technicians; where did your last five jobs come from; are you running ads in your own account today. Keys A to D, a tile answer moves on by itself (the popup's existing pattern).
4. **The result.** One true line built from the answers, then "Fifteen minutes. Before the call we pull your county's search results and show you who he finds." No score, no email gate.
5. **The booking.** The five steps of Style Guide 6.10 unchanged: first name, email, phone, technicians (pre-filled from tile 2), the calendar. Confirm books the event, the invite, the confirmation, the day-before and one-hour reminders, the Leads row (with the four answers), and the deal at Booked.

The only Meta lead the CRM ever sees is a booked call. Non-bookers become a Pixel audience for round two.

## Audience, placements, objective

- One campaign, one ad set, three ads. Budget at the ad set, $30 a day.
- Audience: United States, all of it (Jonathan, 2026-10-03: the DMV included), ages 30 to 65, the "business owners" and "small business owners" behaviors, no interests, Advantage+ audience off. The first three seconds of the video and the four tiles do the targeting. Meta has removed most brand interests, and the matched lists land at 150 to 400 people, too few to carry spend.
- Round two, only after Jonathan uploads `projects/outreach/meta-customer-list-2026-09-24-integrators-strong.csv` as a customer list: a second ad set at $10 a day, that list plus a 1 percent lookalike.
- Placements: Facebook and Instagram, Feed, Reels, Stories. 9:16, captions burned in (sound off is the default).
- Objective: Leads, website conversions, conversion event **Lead**, fired when the fourth tile is answered (the result screen). Completers are 20 to 30 percent of clicks, enough for Meta to learn from; bookings are too rare (Meta wants about 50 events a week). Bookings are read in the CRM, not in Ads Manager. Accept "learning limited".
- Exclusions: anyone who booked (the Schedule event, 180 days); the self list is not needed on Meta since the booking script and the CRM drop Jonathan's own bookings.

## Links and attribution

Ad destination, one line, Meta fills the braces:

```
https://monarcbuild.com/builder-check/?utm_source=facebook&utm_medium=paid-social&utm_campaign={{campaign.id}}&utm_content={{ad.id}}
```

- The campaign id goes in the Campaigns row's **Platform id** before the ad runs. The booking script matches the lead's campaign by Platform id; a miss writes the raw id and can create a stray row.
- `utm_campaign` is the **campaign id**, not the ad set id (`references/attribution.md`, corrected 2026-10-03 to match `references/channel-connections.md`).
- `fbclid` is captured by the popup and the booking script (added 2026-10-03, ships with the pending push and republish).
- The CRM maps utm_source facebook, instagram, meta, fb, ig to the `meta-ads` channel (`_attribute_lead` in `scripts/crm_server.py`; `channelFor` in `scripts/avmarketing-booking.gs`).
- The Page's Book now button, the Instagram bio link, and the Page posts are not ads. They carry `utm_medium=social&utm_campaign=meta-page` and land on the Campaigns row "Facebook Page: button and posts" (Platform id `meta-page`), which the journey map shows under Organic social, not under Meta ads (`page-posts.md`, the button section).

## Spend, the read, the stop

| | |
|---|---|
| Daily budget | $30 |
| First read | at $500 spent, about 2026-11-05 |
| Stop | at $1,000 spent, about 2026-11-19, unless one qualified booking was held |
| Pass | one qualified booking held per $500; then the next $1,000 |
| Paid media total | $60 a day across Google Ads (07 at $30) and Meta; nothing else is added until one gate passes |
| Cost per booked, tolerated | under $400 (the Google review cadence's line) |

What the $500 read looks at, in order: link clicks, check starts (the custom event `CheckStarted`), check completes (Lead), bookings (Schedule, and the CRM), cost per booked, held, qualified (installs one of the brand tiles and 3 or more technicians), per ad. Expected at $30 a day: $2.50 to $4 a click, 1 to 3 percent of clicks booking, so 3 to 8 bookings in 30 days, about half qualified.

A qualified booking: installs Lutron or Ketra, Control4, or Crestron or Savant; 3 or more technicians; the owner on the call; residential high-profile work confirmed on the call; ready to run ads in his own account with his own budget (the `/av_marketing/` fit block). The tiles catch the first two before the call.

## The six gates before a dollar spends

- [ ] 1. The Meta accounts exist: Business Manager, ad account with a payment method, the Page "Monarc Build" (butterfly profile photo, cover from `projects/Landing Page Build/brand/export/`), a linked Instagram, the Pixel. Jonathan supplies the Pixel id and the ad account id.
- [ ] 2. The push: the two privacy lines approved; `assets/journey.js`, the popup changes, `fbclid` in the popup, the Pixel base code on every page, and `/builder-check/` pushed from the mirror on Jonathan's go.
- [ ] 3. The booking script republished (`scripts/avmarketing-booking.gs`): the no-name copy, `isSelf`, the journey, the `agenda` action, `fbclid`, the check answers on the lead, the day-before reminder.
- [ ] 4. The script and the "Monarc Build" calendar moved to jonathan@monarcbuild.com, so the invite never shows sumreat17.
- [ ] 5. A test booking on `/builder-check/` from a non-self address with the Meta labels: the Leads row carries Source meta-ads, the campaign, and the four answers; Events Manager's Test Events shows Lead on the result screen and Schedule on the booked state.
- [ ] 6. The Campaigns row carries the Platform id and the campaign is built paused in Ads Manager.

Then Jonathan presses go live. The AIOS never does.

## Production

1. **Record** (Jonathan): three takes of each script, 4K vertical, a good microphone, any room, each take 30.0 seconds or under, two seconds of silence at the head and the tail, the lens at eye level, hands still (big arm moves across the body fight the clothing swap), brim up so the eyes show, nothing with a logo in frame. Files into `media/inbox/` (Studio prepares them: MP4, waveform, transcript). Names: `meta-01-belief-t1.mp4`, `meta-02-honesty-t1.mp4`, `meta-03-referrals-t1.mp4`, and so on.
2. **Pick the takes** (Jonathan): one per script. A take over 30.0 seconds is cut to length in Studio first; Ad Multiplier refuses a longer source and never trims.
3. **Multiply** (AIOS): the Higgsfield Ad Multiplier workflow, one run per take: the background to a finished equipment or media room with the gear visible, the clothes to a plain black cap, blue jeans, and a button-down, his face, motion, framing, and audio kept. 1080p. Every run is quoted first; the cap for the campaign is 800 credits of the 2,402 on hand; retries after QA count against it. Whatever is finished at the cap ships; the rest runs as the raw take.
4. **Angles**: Ad Multiplier keeps the camera, so angle changes are digital punch-ins placed by hand in Studio (wide, medium at 1.3x, tight at 1.6x) from the 4K source. One Seedance 2.5 generated-angle experiment on one take, inside the cap, kept only if it passes the QA below.
5. **QA** (AIOS, then Jonathan): every frame of the first three seconds, then every cut point: hands, the cap's brim, the hair edge, the gear behind him, the shirt's buttons and collar, lip sync against the raw audio. Any miss: one retry, then the raw take.
6. **Cut, caption, export** (Jonathan, in Studio): the hook text on screen before he speaks, the punch-ins on the beats, captions in his blue, export 1080x1920 at -14 LUFS to `media/ready/`.
7. **Fallback**: the raw takes are kept in `media/projects/meta-ads/raw/`. If Meta labels the video "AI info" and the click rate dies, or a frame slips past QA, the raw cut swaps in without a reshoot.

## The Page before the ad

Three posts drafted in `page-posts.md`, approved and posted by Jonathan, so a prospect who taps the profile finds a company, not an empty page. The ad waits a week of Page age; new ad accounts and empty Pages are flagged and spend-limited more often.

## Who does what

Jonathan: the Meta accounts (about an hour); the proof span; the scripts approved; three takes; the style tile and the render approved; the privacy lines and the push; the republish or the account move; the Page posts; the Studio cut; the test booking; the campaign built paused; go live; the Friday numbers typed on the row until an API reads them.

The AIOS: this folder; the CRM row and the journey card; the Higgsfield pass; the page from `check.md` through `/landing-page`; the Pixel code and the privacy lines in the mirror; the booking-script changes; the read at $500 written to `projects/meta-ads/reports/`.

## The failure-point audit, and what each point became

1. **Promise versus product.** The ad promised exposure to specifiers; the call sells search. The bridge is in the proof: the Georgian came from a contractor who typed it. The script says specifiers search.
2. **The belief announced, never stated.** Now stated: "You think getting specified means knowing the builder."
3. **The callout at second five.** Now the first two words, on screen and spoken.
4. **House rules broken.** BOUND, PROVE, LOCK, and HOLD added; the service word and the hedges out; three objections per ASK written.
5. **"Quiz".** Gone. "Can a builder in your county find you tonight?"
6. **Meta cannot target integrators.** Broad audience; the hook and the tiles filter.
7. **No page, no Pixel.** `/builder-check/`, the Pixel with Lead and Schedule, the privacy lines, fbclid.
8. **The backend not ready.** The push, the republish, and the account move are gates 2 to 4.
9. **Attribution gaps.** Campaign id in Platform id; fbclid captured; the two old rows with fake estimated spend deleted.
10. **The old gate.** $30 a day, read at $500, stop at $1,000 unless one qualified booking held; Leads objective on check completion.
11. **One video.** Three.
12. **Copy rules.** No PHA, no dollar figure, no tenure on screen, no "no setup fee", no price, no name.
13. **Show rate.** The day-before reminder for every site booking; the tile answers on the lead.
14. **The decision trail.** Logged 2026-10-03; LinkedIn ads decoupled.

## Dates

| Date | What |
|---|---|
| Week of Oct 5 | Accounts, scripts approved, three takes, privacy lines, push, republish |
| Week of Oct 12 | Higgsfield pass, Studio cut, the page built and approved, Pixel test booking, Page posts, campaign built paused |
| Tue 2026-10-20 | Go live, $30 a day |
| About 2026-11-05 | $500 read, `projects/meta-ads/reports/` |
| About 2026-11-19 | $1,000: stop unless one qualified booking was held |

## Log

- 2026-10-03: planned. The Sept 11 ad sets (matched list and retargeting; lead form, free city search) deleted from the CRM; their plan stays in `projects/outreach/campaigns-2026-09-11.csv`. The hooks live in `brainstorms/2026-09-10-facebook-ad-hooks.md`.
