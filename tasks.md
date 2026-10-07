# Tasks

The one task list, organized by what each tier of the incentive ladder pays for. Click a tier to open the tasks that earn it. Check a box, add the date. Tell the AIOS when something is done and it updates this file. Domain 5 (task tracking) lives here until a real tool replaces it.

Started 2026-09-07. Goal: 5 clients signed by 2026-12-01. Source: `context/roadmap.md`.

## Ladder rules

1. A reward is bought only after every box in its tier is checked and dated here.
2. Rewards are paid from the business account as an owner draw. Capped. Never from salary or the invest percent.
3. Name the reward in advance and write it on the tier line. A reward picked after the fact is just spending.
4. Miss a tier, the reward is gone. No rollover, no partial credit.
5. Under 100 dials in any week: no weekly reward, no exceptions.

---

## Today

The CRM's Today panel shows every open box here, in full, with its links (Jonathan, 2026-10-03: "write these as tasks in my CRM for today"). When a box is done it moves back to its tier below.

<details open>
<summary><b>Today · Fri 2026-10-03 · the listings, the Meta Page, the three organic posts, the ad scripts, the three ad videos, the check page</b></summary>

- [ ] Finish the NAP listings. The Google Voice number first ([voice.google.com](https://voice.google.com/), on the Monarc Google account; send the AIOS the number), then the 12 in order, each copied word for word from the Business Profile: [1 Google Business Profile](https://business.google.com/create) · [2 Bing Places](https://www.bingplaces.com/) · [3 Apple Business Connect](https://businessconnect.apple.com/) · [4 Yelp for Business](https://biz.yelp.com/signup) · [5 Facebook Page](https://www.facebook.com/pages/create) · [6 LinkedIn Company Page](https://www.linkedin.com/company/setup/new/) · [7 BBB](https://www.bbb.org/get-listed) · [8 Foursquare](https://foursquare.com/venue/claim) · [9 Data Axle](https://www.data-axle.com/what-we-do/local-listings) · [10 Yellow Pages](https://www.yellowpages.com/claim-your-listing) · [11 Clutch](https://clutch.co/get-listed) · [12 UpCity](https://upcity.com/providers). The NAP is on the campaign row: Monarc Build, Riva, MD with the street hidden, the Google Voice number, monarcbuild.com, jonathan@monarcbuild.com. Free listings only; skip every paid offer. Mark each row Submitted or Live on Channels, Google Organic, with the login email on the row, never a password. (you)
- [ ] Draft the listing copy as soon as the number exists: the business description, the categories, the services, and the hours, one version every directory copies, for your approval; then check each live listing against the NAP and tick NAP matches on its row. (AIOS)
- [ ] Set up the Meta business profile: [Business Manager](https://business.facebook.com/overview), the ad account with a payment method, the Page "Monarc Build" (profile photo `projects/Landing Page Build/brand/export/monarc-build-butterfly.png`; the About line, category, and the Riva, MD location in `projects/meta-ads/page-posts.md`, "Page setup"), a linked Instagram with the same photo and About line, and the Pixel in [Events Manager](https://business.facebook.com/events_manager2). Send the AIOS the Pixel id and the ad account id. The Page doubles as NAP listing 5. (you, about an hour)
- [ ] Three organic posts for the Page and Instagram, scripted in `projects/meta-ads/page-posts.md` (the proof photo, a talk to camera, who we are): read them, mark up or approve, and post them once the Page exists, each with its tagged link. The ad waits a week of Page age. (you)
- [ ] Draft the creative for the three organic posts: post 1 the great-room photo cropped 4:5 for the feed and 1:1 for the grid, nothing written on it; post 2 three candidate 20-second talk-to-camera clips cut from a calling session in Monarc Studio (his words in blue captions, no prospect's voice, no company named) for Jonathan to pick one; post 3 the butterfly with the wordmark on white, 1:1. Files to `projects/meta-ads/creative/` for approval. (AIOS)
- [ ] Build the ad script template: `templates/ad-script.md`, one slot for everything an ad creative script needs: the hook (the on-screen text and the first spoken line), the headline, the description (the ad's primary text), the person (who is on camera and who it speaks to), the setting, the lighting, the wardrobe, the framing and camera, the length, the line jobs from `references/cold-call-principles.md` (HOOK, BOUND, FILTER, PROVE, NAME, ASK, LOCK), the call to action, the captions, and the link with its tags. Then the three scripts in `projects/meta-ads/scripts.md` rewritten into it, so every ad script from here on starts from the same page. For your approval. (AIOS)
- [ ] Make the three ad videos. First approve the three scripts in `projects/meta-ads/scripts.md` and confirm the proof span ("Then years of his work"; the record says $500k+ lifetime from one contractor). Record three takes of each: 4K vertical, a good mic, any room, each take 30 seconds or under, two seconds of silence head and tail, into `media/inbox/` (recording notes at the end of `scripts.md`). Pick one take per script. After the Higgsfield pass, cut, caption, and export the three in Monarc Studio: the hook text on screen first, punch-ins on the beats, 1080x1920 to `media/ready/`. (you)
- [ ] Higgsfield Ad Multiplier pass on the three picked takes: the rack room, his wardrobe, every run quoted, 800 credits at most, frame QA, the raw takes kept in `media/projects/meta-ads/raw/`. (AIOS, after the takes land)
- [ ] Build the landing page with the check, the quiz form the ads land on: `/builder-check/` from `projects/meta-ads/check.md` through `/landing-page`, the style tile first, then the page with the four tiles, the result line, and the booking steps, the Pixel events, Style Guide 6.12, and the Section Spec entry. You approve the tile, then the render, then say go to push. (AIOS builds, you approve)
- [ ] Free campaign for a review (planned 2026-10-03, `projects/free-campaign/README.md`): open the DataForSEO account at [dataforseo.com](https://dataforseo.com/) ($50 minimum) and put `DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD` from [app.dataforseo.com/api-access](https://app.dataforseo.com/api-access) in `secrets.env`. Until then the audit shows the map results only and says so. (you, 10 minutes)
- [ ] Read and approve the second-window call script `references/free-campaign-call-script.md` and the two emails, `templates/free-campaign-delivery-email.md` and `templates/free-campaign-review-ask.md`; confirm the budget rule (the median top-of-page bid times three clicks a day, rounded up to $5, $10 floor). Mark up in the files or say go. (you)
- [ ] Log the second window's calls in the Prospects base, table "Free campaign calls" (made 2026-10-03): pick the company, type the outcome in Status (typed) as on Contacts, the email in Email. A "yes", "send it", or "build it" is what builds the delivery. (you, as you dial)
- [ ] Export campaign 07 from Google Ads Editor to a CSV (select the campaign, Account, Export, Export selected campaigns and ad groups) into `projects/free-campaign/`, so the import file's header row is checked against Google's own before the first delivery. (you, 5 minutes)
- [ ] The first three deliveries: open each on Channels, Cold call, "Free campaign for a review", read `audit.pdf` and `ads-editor.csv` in its folder, set the row's Stage to Approved, and the AIOS drafts the email; send it from Proton. After three, the drafts come without the stop. (you)
- [ ] When the Business Profile is live, paste its review link into `projects/free-campaign/config.json` as `review_url`. The review asks start the next morning, three a day, oldest delivery first; you send each from Proton. (you, one line)
- [x] Free campaign, the AIOS's part: `scripts/free_campaign.py` (build, queue, deliver, readback, asks, status, check) and `scripts/dataforseo.py`; two test builds from the caches with the PDF and the Editor file (`projects/free-campaign/MB-00000-*`); the Prospects table "Free campaign calls" and the Config row `call_sheets`; the Monarc CRM table "Free campaigns" and the campaign row on the Cold call channel with its deliveries group; the call script, the two email templates, the capture, the decisions entry. Done 2026-10-03. From here, daily: `queue`, `readback`, `asks`. (AIOS)

</details>

---

## The ladder

<details>
<summary><b>Week 0 · $100 · all nine boxes by Friday 2026-09-11</b> · Reward: ____</summary>

Stage 0, the plumbing. Ideas: steak dinner out, running shoes, the thing you've been putting off buying.

- [x] Open a business bank account. (you) Articles of Organization on file since 2026-06-18 (Monarc Build, LLC, SDAT W27446186, 3074 Riva Rd, Riva, MD 21140-1318; recorded in `context/about-business.md` 2026-09-15). The bank will ask for the Articles, the EIN letter, and your ID. Done 2026-09-29.
- [x] Pick and set up a payment and invoicing tool. Add it to `connections.md` row 1. (you) Done 2026-09-29.
- [x] Build the tracking sheet, four tabs: Dials, Pipeline, Leads, Money. **Built 2026-09-15 as the Monarc CRM** (Airtable base plus `python scripts/crm_server.py`, connections row 10): Dials = Today view and `projects/outreach/dial-log.jsonl`, Pipeline = Deals by stage, Leads = Companies and People with Source, Money = Reports by source (Won and Revenue). One step left for you: create the Airtable token and add `AIRTABLE_PAT=` to `%USERPROFILE%\.monarc\secrets.env` (`references/airtable-api.md`). Until then it runs offline and queues writes.
- [ ] Finish `context/offer.md`: contact line, confirm the match is $1,000 total. (you) 2026-10-05: the 9/15 offer is on hold; "The rewrite" under Required replaces this box.
- [ ] Script drill on the cold call: one job per line, cut 20%, three objections under every ask. Save as v1. (you, AIOS plays the prospect)
- [x] Follow-up email the script ends on. Drafted 2026-09-09, `templates/follow-up-email.md`. Edit there if you change it.
- [ ] Kickoff questionnaire script. Drafted 2026-09-13 as the `/kickoff` skill: 33 questions in six blocks, `.claude/skills/kickoff/assets/questionnaire.md`, access checklist alongside. Read it and approve or mark up. (AIOS drafted, you approve)
- [x] List of 200 integrators. Done, and then some: `projects/outreach/Integrator_List_2026-09-05.xlsx`, 2,000 integrators with address, state, county, phone, local time at noon ET, reviews, website, plus Status and Outcome columns for the dial log. Found in the mailbox 2026-09-09. LinkedIn seed list cut from it 2026-09-09 (One Firefly and commercial-leaning removed): `projects/outreach/seed-list-2026-09-09.xlsx`, upload CSVs alongside. **Call list qualified 2026-09-11** on Jonathan's rule (website required; not DC, MD, or VA; 0 to 30 Google reviews; one company per website domain, judged on its highest-reviewed listing): 887 companies in `projects/outreach/qualified-list-2026-09-11.xlsx` (sheets Qualified, Excluded with reasons, Method) and `.csv` for Airtable import. Rebuild: `python scripts/qualify_list.py`. Destination: the Airtable base (connections row 10).
- [x] **National LinkedIn seed. Built and run 2026-09-13.** Keys wired in `%USERPROFILE%\.monarc\secrets.env`. Places sweep: 213 locations, 1,540 pages, 10,077 rows, 7,842 unique domains, $53.90. Opus 5 batch: 6,461 sites read, zero errors, $75.58. Total $129.48 of the $200 cap. Result: 1,277 Tier A, 458 Tier B, 199 Tier C (review), 4,783 excluded (4,289 not integrators, 233 One Firefly, 261 commercial), 1,125 unverified. Files: `projects/outreach/places-seed-2026-09-13.xlsx`, `qualified-seed-2026-09-13.xlsx`, upload `linkedin-company-list-2026-09-13.csv` (1,735 companies, Tier A+B, 65 DMV rows kept) and `-no-dmv.csv` (1,670). Guides: `references/google-places-api.md`, `references/anthropic-api.md`, `references/credentials.md`.
- [ ] Upload the LinkedIn company list `projects/outreach/linkedin-company-list-2026-09-13.csv`. Header verified 2026-09-13 against LinkedIn's official Account Match Template (`stocksymbol`, `companycountry`, states spelled out); the 2026-09-09 CSVs have the old wrong header, do not upload those. Campaign Manager: Plan, Audiences, Create audience, Upload a list, Company. Then wait for the match count (expect 30 to 50 percent, so 500 to 850 companies). (you)
- [ ] Review Tier C: 199 companies in the Qualified sheet of `qualified-seed-2026-09-13.xlsx`, sorted after A and B. Promote or drop by hand; the model reason column says why each is borderline. (you, 30 minutes)
- [x] **Meta Ads seed list. Built 2026-09-14 to 15** by `python scripts/meta_seed.py`: Tier A+B (1,735) unioned with the 887 call list = 2,254 domains, each crawled for contact, about, and team pages. No paid data. Result: 574 owner or founder names, 388 with an owner name plus an email, 318 more with a named mailbox, 647 generic (info@) only, 887 phone only, 14 nothing. Social links: 1,367 Facebook pages, 1,041 Instagram, 609 LinkedIn. Files: `projects/outreach/meta-seed-2026-09-14.xlsx` (Seed sheet graded A to E, evidence line per owner name; Method sheet), `meta-customer-list-2026-09-14.csv` (2,247 rows, Meta column codes, upload as is), `meta-customer-list-2026-09-14-strong.csv` (388 rows, owner name plus email, the lookalike source). Cache `contact-cache-2026-09-14.jsonl`; a rerun crawls only new domains.
- [ ] Upload both Meta CSVs as separate customer-list audiences (Ads Manager, Audiences, Create, Customer list) and read the match size. A lookalike needs at least 100 matched people; expect 30 to 50 percent on the strong list. (you) **Round two of the Meta campaign** (the matched-list ad set at $10 a day, `projects/meta-ads/README.md`); the first ad set runs broad and does not wait on it (2026-10-03). The newer cut is `meta-customer-list-2026-09-24-integrators-strong.csv` (762 rows).
- [ ] Decide on paid enrichment for the 1,548 companies with no named contact (grades C, D, E): Apollo one month (about $60 to $100, owner name plus email by company domain and title) or leave the list as is. (you)
- [ ] Apollo hookup (2026-10-06, wired, waiting on you): sign up at apollo.io with jonathan@monarcbuild.com (free plan to start, 100 credits a month), create an API key with People Search and People Enrichment, and put it in `%USERPROFILE%/.monarc/secrets.env` as `APOLLO_API_KEY=...`. Then the AIOS runs `python scripts/apollo_enrich.py batch 2026-10-06` (free) for Fusion Tech, Sierra, and PAVS and quotes the credits before any reveal. `references/apollo-api.md`. (you, 10 minutes)
- [ ] Spot-check 20 owner names in the Seed sheet against the evidence column before the first upload. The rule is pattern matching, not a lookup; expect about one miss in ten. (you, 10 minutes)
- [ ] Two money rules written and dated: monthly salary, percent of profit invested. Log in `decisions/log.md`. (you)

Completed on: ____ · Reward taken: ____

</details>

<details>
<summary><b>Weekly · $50 · a clean week: 110+ dials logged and the Friday tally done</b> · Reward: ____</summary>

Runs every week until December 1. Ideas: Friday night fully off, no phone. A good bottle for the weekend. A round of golf.

Each week, all four:

- [ ] Monday to Friday: 22 dials in the first hour, every call logged (name, line where it died, outcome). (you)
- [ ] Friday: tally where calls died, rewrite one line only. (you, AIOS runs the tally once the sheet exists)
- [ ] Every booked meeting: confirmation same day, the Loom brief before the meeting (what we will set up so their lead flow runs smooth; added 2026-10-04), reminder the day before. Log show or no-show. The company's file in the CRM lists what is still open. (you, AIOS drafts; a site booking gets the confirmation and the reminder from the booking script once the 2026-10-03 republish is live)
- [ ] Every meeting held: log close or the objection that killed it. (you)

Week log:

| Week of | Dials | Booked | Held | Tally done | Clean? | Reward taken |
|---|---|---|---|---|---|---|
| 2026-09-14 | | | | | | |
| 2026-09-21 | | | | | | |
| 2026-09-28 | | | | | | |
| 2026-10-05 | | | | | | |
| 2026-10-12 | | | | | | |
| 2026-10-19 | | | | | | |
| 2026-10-26 | | | | | | |
| 2026-11-02 | | | | | | |
| 2026-11-09 | | | | | | |
| 2026-11-16 | | | | | | |
| 2026-11-23 | | | | | | |

</details>

<details>
<summary><b>Client 1 · $250 · first signed contract and first invoice paid</b> · Reward: ____</summary>

Ideas: something you use every day and see. A watch, headphones, a jacket.

- [ ] Read `templates/onboarding-questionnaire.md` and `templates/asset-request-email.md`; strike and add in the four `context/trades/` files. (you, 20 minutes)
- [ ] Contract signed. Date: ____
- [ ] Invoice sent same day. Date paid: ____
- [ ] Onboarding questionnaire back and in the capture. Asset list items 1 to 7 in `projects/clients/<slug>/assets/`.
- [ ] Kickoff meeting held, questionnaire run, calendar access received.
- [ ] Build live within 14 days of kickoff: site, one landing page per service and per area, GBP, Ads. Hours logged.
- [ ] First Responder on: every form fill called within 5 minutes, 9 to 7 Eastern, email follow-up, booked. Every lead logged.
- [ ] First weekly PDF report emailed.

Completed on: ____ · Reward taken: ____

</details>

<details>
<summary><b>Client 3 · $750 · third client signed</b> · Reward: ____</summary>

Ideas: a weekend trip with friends. A new phone or monitor. A tailored suit for the meetings.

- [ ] Client 2 signed. Date: ____ · Per-client checklist done (see template below).
- [ ] Client 3 signed. Date: ____ · Per-client checklist done.
- [ ] Client 1 still on the 5 minute promise and the weekly PDF, no misses.

Completed on: ____ · Reward taken: ____

</details>

<details>
<summary><b>Client 5 by December 1 · $2,500 · the goal</b> · Reward: ____</summary>

Ideas: one month of Level 1, spent on you. A ski trip in January. A big gear purchase. Whatever you'd brag about at 25.

- [ ] Client 4 signed. Date: ____ · Per-client checklist done.
- [ ] Client 5 signed on or before 2026-12-01. Date: ____ · Per-client checklist done.
- [ ] All five clients on the 5 minute promise and the weekly PDF.
- [ ] Money loop run for September, October, November (see below).

Completed on: ____ · Reward taken: ____

</details>

<details>
<summary><b>Client 5 late · $1,000 · signed December 2 to December 31</b> · Reward: ____</summary>

Same tasks as the tier above. Late still counts, at $1,000. Past December 31 it doesn't count at all.

Completed on: ____ · Reward taken: ____

</details>

---

## Required, no reward attached

<details open>
<summary><b>The rewrite (added 2026-10-05): a new buyer, each tool at market price, $3k+ a month per client</b></summary>

Jonathan, 2026-10-05: "I was offering too low to the wrong people." and "We go off of what people pay on the market for the tools." (`decisions/log.md`). Everything written for the old buyer and the 9/15 price gets rewritten once the first box is answered. Each box names its file, and the same box shows on that file in the CRM (Records, Artifacts), marked To do. Until the offer page is done, no new draft states a price.

- [ ] Name the buyer and the tool list: who the right people are, which tools they buy, and whether December 1 still stands. Every box below waits on this. (you)
  - 2026-10-05, two of three answered: the buyer is any business with the problem ("I am basically just handing off an agent that fixes a universal problem"), and the tool list is the 50 names he pasted, folded into 12 workflows (`references/agent-catalog.md`). Still open: whether December 1 stands, and whether each list price is one-time or per month.
- [ ] Rewrite the offer page `context/offer.md`: the new buyer, each tool at what the market pays for it, $3k+ a month per client. Then the offering PDF into `projects/artifacts/offer/`. (AIOS drafts, you approve)
- [ ] Rewrite the agreement `templates/Monarc_Pilot_Service_Agreement.pdf` (and its .docx) to the new offer. Then DocuSeal template 5897064 is replaced on your go. (AIOS drafts, you approve)
- [ ] Rewrite the price lines and the offer blocks in `references/mycopy.md`: the price rule, the offer sentence, the pilot block, the terms email, the decline block. (AIOS, after the offer page)
- [ ] Rewrite the cold call script for the new buyer. Today's is Sample 1 in `references/voice.md` ("I book jobs for home integrators"); with it come `references/objections.md` and `references/qualifying-questions.md`, neither written yet. (you, AIOS drafts on your word)
- [ ] Recut the call list for the new buyer: the Prospects base, Contacts, by Vertical, and the CRM's lists (`verticals` in `projects/crm/config.json`). (AIOS, after the buyer is named)
- [ ] Rewrite the free campaign for the new buyer: `references/free-campaign-call-script.md`, `templates/free-campaign-delivery-email.md`, `templates/free-campaign-review-ask.md`. (AIOS drafts, you approve)
- [ ] Rewrite the seven ad pages and their ads for the new buyer and the tool list: `/google-ads/`, `/website-build/`, `/seo/`, `/email-marketing/`, `/facebook-ads/`, `/ai-automation/`, `/av_marketing/`, one file each in `projects/google-ads/campaigns/`. Style Guide first, a render for approval, nothing pushed or published without your go. (AIOS builds, you approve)
- [ ] Rewrite the context pages that still carry the old buyer and price: `context/about-business.md`, `context/roadmap.md`, `context/website.md`, and the Knowledge base paragraph in `CLAUDE.md` and `AGENTS.md`. (AIOS, after the offer page)

</details>

<details open>
<summary><b>The SDR skill (added 2026-10-05): five workflows, passed one at a time when the copy sounds like you</b></summary>

Your word 2026-10-05: the SDR is one skill for the outbound, the follow-up, and the appointment setting, and it is the real build right now. Its workflows live under it (`.claude/skills/sdr/workflows/`). It does not audit the copy; that is the coach skill, to come. The pass: "we go through each function and I approve that the copy matches what I would typically sound like." One workflow at a time: the AIOS drafts every message it sends, you mark it up until it sounds like you, and your approval goes on the file. In the CRM, the butterfly logo lists them: Work on a project, Workflows. How the rest of your list of 50 folds in: `references/agent-catalog.md`; interview `brainstorms/2026-10-05-agent-skills.md`.

- [ ] 1a. In your inbox since 2:06 pm, 2026-10-05, unread: "Your contact form, two days", from patrick@monarcbuild.com. It is Email 1 written to you as an integrator who took two days to answer a form fill. Read it as that owner would and say what is off. Reply to it if you like; nothing answers you, since the mailbox is not wired. (you)
- [ ] 1. Cold outreach: read the rest of copy v2 in `.claude/skills/sdr/workflows/cold-outreach.md` (Email 2, the owner's evenings; Email 3, the cost of doing nothing; three connection notes; the message after they accept; the line each signal fills in). Approve or mark up. Yours to settle: the name shown on patrick@monarcbuild.com, the proof line, whether cold mail rides on monarcbuild.com or a second domain, and whether the slow-reply line is worth filling out prospects' forms for. (you)
- [ ] Cold outreach, the intake for Monarc's own run in `projects/clients/monarc-build/sdr.md`: which kinds of business and which cities the first pull searches for, the review band, the outcome offered, and two numbers (the least rows on the list, booked meetings a week that count as working); three facts on file to confirm. Also yours: the sending tool and a second domain for cold email, neither chosen, and your yes or no on a tool sending from your own LinkedIn seat. (you, then AIOS builds the list)
- [ ] The list: `/list-building`, written 2026-10-05 from your spec (a big Google Maps pull, a Clay hookup for email, owner name, and LinkedIn URL, then reviews and the website signals for a new site, a receptionist, email follow-up, an appointment setter, a proposal builder). Clay replaces the old Apollo question under Week 0. Yours: open the Clay account and tell the AIOS (how rows go in and come back, a table webhook or a key, is worked out then; never a password in chat); read the six signal checks in the skill and strike or add; set the review band; name the kinds of business and the cities for Monarc's first pull. (you)
- [ ] Build what `/list-building` still lacks: the Clay hookup with `references/clay-api.md`, the four site checks (chat, email tool, online booking, free-estimate form), and opening hours in the Maps pull. Then a 50-row trial against its pass list, quoted first. (AIOS, after the Clay key and your word on the signals)
- [ ] 2. Lead form submission follow-up: the copy (the first reply, the sequence, the last touch). (AIOS drafts once cold outreach is approved, you approve)
- [ ] 3. Stale proposal follow-up: the copy (three touches, the last one asks for a no). (AIOS drafts, you approve)
- [ ] 4. Appointment booking: the copy (the times offer, the confirmation, the day-before reminder, the rebook). (AIOS drafts, you approve)
- [ ] 5. Inbox replies: the SDR answers what lands in patrick@monarcbuild.com. The copy: one approved answer each for who we are, what it costs, not now, no, and wrong person. (AIOS drafts, you approve)
- [ ] 6. No-show: read the two messages in `.claude/skills/sdr/workflows/no-show.md` (the rebook email and the LinkedIn line). Approve or mark up. (you)
- [ ] Momentum Electrical Contractors, no-show Mon 2026-10-05 at 2:00 pm Pacific, logged at 5:05 pm. The ready draft is the newest one in Proton Drafts, Tue 10:48 am: "Re: Monday at 2:00 pm Pacific" to info@momentum-electric.com, Tuesday at 11:30 or Wednesday at 10:00 Pacific, the same Meet link, the 11-minute Loom. Send it, then send Tom the LinkedIn line (`.claude/skills/sdr/workflows/no-show.md`). Delete the five older Momentum drafts. When the 4:25 owner's cut is uploaded, it replaces the Loom line in the next touch. Tick the three no-show steps on their file as you go; still silent Friday, log the close reason. (you)
- [ ] The SDR test booked you at 3:30 pm today: a hold named "Monarc Build audit: Jonathan (SDR test)" is on your calendar and on the CRM's Today calendar, with a Meet link. Two messages are in your inbox since 2:52 pm: the answer on the thread (the time and the link) and "Booked: Monday at 3:30 pm with Monarc Build". Say what is still off, then delete the hold. The first booked note (2:47 pm) had no link; ignore it. (you)
- [ ] Read and approve, or mark up, the three answers the inbox sends by itself, in `projects/sdr/config.json` under "copy": the times offer, the booked answer (the time and the Meet link), and the confirmation from "Monarc Build". Also yours there: the hours a meeting may be booked (now 9 to 5 Eastern, the dial hour kept clear, 45 minutes ahead at least), the phrases that sort a reply, and the meeting's title ("Monarc Build audit: {first}" is the site's; the SDR's offer is not an audit). (you)
- [ ] Build for SDR-booked meetings what the site's bookings already have: the day-before and one-hour reminders, the deal moved to Booked on the board, and the notice to you. (AIOS, on your word; the reminders need the send step)
- [ ] Sign patrick@monarcbuild.com in to Proton Bridge on this machine and put its Bridge user and password in `.env` as `PROTON_SDR_USER` and `PROTON_SDR_BRIDGE_PASS`. It is its own Proton sign-in, so the watcher cannot see real replies until then. Then say whether the watcher starts with Windows; today it runs until the machine restarts. Patrick left, so also say who sends the LinkedIn messages now; the files still name him. (you, then AIOS reads the mailbox and adds a send step, off until your go)
- [ ] The coach skill: audits the copy the SDR sends. Not written; you said it gets baked in later. Say when. (you)
- [ ] Later, not started: the nine other groups from your list of 50 (sales desk, ops, web build, content, support, documents, analytics, finance, caller) wait for a skill of their own (`references/agent-catalog.md`). (you say which role comes after the SDR)
- [ ] Say where the list came from, whether the three numbers after each price are cost, profit, and margin, and whether each price is one-time or per month. (you, one line)
- [ ] The Outreach test run to yourself (2026-10-05, your number: $4,859 a month). In Proton Drafts: "Outreach: the proposal and the first invoice", with the proposal (two pages) and an invoice preview (one page); read it, mark it up, press send if you want it in your inbox. Files: `projects/artifacts/proposals/2026-10-05-outreach-test/`. The invoice is in Stripe as a draft (your word 2026-10-05: "Stripe invoices can now be made... The key stays able to write"): Dashboard, Invoices, Drafts, customer "Jonathan Beach (test run)", $4,859.00, not sent, not charged. To see it as a client would, open it and press Send invoice; do not pay it, and delete or void it when you have looked. Yours to change in the proposal: the billing day, the 7 days, month to month with 30 days notice, and the ownership line, all carried from the 9/15 agreement. (you)
- [ ] Butterfly, the first click (built 2026-10-05): in the CRM, click the butterfly logo at the top left, Work on a project, Skills, "Skills and workflows". It should bring VS Code up on the chat of 2026-10-05. Then Run on any skill: a new chat should open with the skill typed. Tell the AIOS what happened either way; the menu was checked in screenshots, the opening of a real chat was not. (you, one minute)

</details>

<details open>
<summary><b>Loom B and A (added 2026-10-06): the rebuild you talk over, cut so each change shows as you name it</b></summary>

Your word 2026-10-06: "We're going to make a skill called Loom B and A." Built the same day on the PHA review Loom (`.claude/skills/loom-b-and-a/SKILL.md`, `scripts/loom_ba.py`). Under five minutes; three is the mark.

- [ ] Watch the two PHA cuts on the Creative tab (Records, Creative): `loom-ba-A.mp4` (the changes one by one) and `loom-ba-B.mp4` (the finished page first and last), 1:04 each, from your 2026-10-04 review. Give notes with times. The picture is the page only; your face bubble is not in it yet: say if it should be. (you)
- [ ] Node for HyperFrames: yes or no. Free, one line (`winget install OpenJS.NodeJS.LTS`), five minutes. It gives the cuts real motion: the headline sliding to the middle, the button's words changing in place. `references/hyperframes.md`. (you, one word)
- [ ] The email: read `templates/loom-ba-email.md`, three subject lines and two bodies. Strike or mark up. Say where it sits: the cold sequence's Email 1 (your 2026-10-06 word: Email 1 carries the rebuilt page's link) or a touch of its own. (you)
- [ ] Record the next Loom on a hero-check lead with the changes said one at a time and a line on who you are (variation B wants it). The clone cuts both variations the same day. (you)
- [ ] The sections below the first screen (reviews under the button, the service cards, about us, the portfolio grid): the states show the first screen only today, so those changes are notes. Build them when you say the first screen is right. (AIOS, after your notes)

</details>

<details>
<summary><b>Pipeline (until the tracking sheet exists)</b></summary>

| Prospect | Contact | Fit | Last touch | Next step |
|---|---|---|---|---|
| WH Smart Home / WH Technologies, Dallas | Joey Milot (ops), Johann Whitehouse, Doug | ICP, two install teams | 2026-09-08 Meet held with Doug. Jonathan passed: two install teams is too little capacity to absorb more work | Parked. Revisit Mon 2026-10-05 as Source = warm; AIOS drafts a note to Doug with two times |
| Warehouse logistics company (name TBD) | Runs logistics, not the owner | Off-ICP, B2B buyer, no marketing today | 2026-09-09 conversation | Send the one-page email; only take a 15 min call if the owner joins; no custom material |
| Audio Video Solutions, Dallas TX (6518 Happy Ln; 5.0 stars, 23 reviews; Wix site with service pages, no area pages, one testimonial, no gallery; Sony, Yamaha, Sonance, Stewart, Kaleidescape) | info@audiovideosolutions.org; (214) 299-1765 on site, +1 214-293-3330 in the list | DFW. Owner wants commercial work and does not do bids (phone call, Jonathan 2026-09-15). Verticals: owner-run commercial buyers who search, houses of worship, funeral homes, restaurants and bars, private practices and offices. Not schools, hospitals, or senior living. Confirm with a Keyword Planner pull before building pages. No contact name yet | 2026-09-09 Jonathan sent "More high ticket work for your company" (his own cut, offered Tue 9/15 10:00 CT). No reply. 2026-09-11 bump placed in Drafts (now stale, Mon 9/14 has passed). **2026-09-15 9:19 PM ET, Jonathan sent "From our call yesterday."** (his own cut: no-bid commercial verticals, managed Google Ads, the pilot terms, $3,000 onboarding waived by 9/30, DocuSeal link, agreement PDF; no times offered). Deal at Proposed in the CRM | Bump Thursday 9/17 if no reply, two Central times. On a yes: AIOS books the Meet with them as guest and fills the LOCK email from `templates/follow-up-email.md` |
| Thoughtful Integrations, Addison TX (North Dallas; 5.0 stars, 18 reviews; catalog-style site with a page per residential service, commercial pages for bars, corporate, MDU, trade partner pages, no area pages; RTI on the homepage) | Steve@thoughtfulintegrations.com; +1 214-396-6290 | ICP, DFW. Central time (10am his = 11am ET) | 2026-09-09 "AV marketing for North Dallas" draft in Proton, Jonathan's cut (proof paragraph plus the ask), four proof files, Meet link in the email. Calendar hold created: Tue 9/15 11:00 to 11:15am ET, meet.google.com/vqd-daxw-ryr, no guests yet. Still in Drafts as of 2026-09-11. Invite description rewritten 2026-09-11 to one outcome line (was internal notes) | Jonathan sends today. On a yes, AIOS adds Steve as guest and fills the LOCK email |
| Criteria of Naples, Naples FL (SW Florida smart home integrator; Lutron, Crestron, Control4, Savant, Vantage dealer) | James, Don, Chris at criteriaofnaples.com; 239.593.1700 | ICP. Three decision-makers. Said on the call: no in-house marketer, want proof. Money not discussed. | 2026-09-09 Jonathan sent "Specialist AV Marketing to land more high ticket clients" (his own cut, four proof files, offered Thu 9/10 11:00 only). No reply; slot passed. 2026-09-11 bump placed in Drafts: Mon 9/14 10:00 or Wed 9/16 2:00 ET, Meet https://meet.google.com/ukx-wtxo-uqd. Calendar hold Mon 9/14 10:00 to 10:15am ET, no guests | Jonathan sends the bump. On a yes: AIOS adds James, Don, Chris as guests (moves the hold if Wednesday) and fills the LOCK email |
| Omni Audio Video LLC, Rockwall TX (6775 Horizon Rd; 5.0 stars, 16 reviews; omniav.com lists home theater, media rooms, lighting control, automation, networking; DFW service area) | Shawn (spoke 2026-09-10 on a dial); Jess (name from Shawn, title unknown); info@omniav.com; +1 214-346-9126 | ICP, DFW east. Central time | 2026-09-10 Jonathan emailed jess@omniav.com: bounced, address does not exist. 2026-09-11 re-draft placed in Drafts to info@omniav.com addressed to Jess, great room photo attached: Wed 9/16 10:00 CT or Thu 9/17 2:00 CT, Meet https://meet.google.com/aqw-geir-tbo. Calendar hold Wed 9/16 11:00 to 11:15am ET, no guest | Jonathan confirms Jess's real address with Shawn if he can, then sends. On a yes: AIOS adds the guest and fills the LOCK email |

</details>

<details>
<summary><b>Friday 2026-09-25: Trade Call List push, seven Marketing Consultations for Mon 2026-09-28</b></summary>

- [x] Airtable: campaign "Trade Call List" on the cold channel, every dial linked to it, Dials, Connects, Booked, Connect rate, Booking rate on the row. Config `active_campaign` set. Done 2026-09-25 (AIOS).
- [x] CRM: Today shows the push strip (booked of 7, dials, connects, the two rates). Done 2026-09-25 (AIOS).
- [ ] The seven Monday slots titled "Marketing Consultation" on the Monarc Build calendar. The AIOS found no events on Mon 2026-09-28 on either calendar the connector sees; tell it which account holds them, or the seven times, and it creates or renames them. (you, one line)
- [ ] Dial. Pick the outcome on each row; a live conversation gets the line it died on and the next step. (you)
- [ ] End of the hour: read the strip. Seven booked, or the connect rate and booking rate say which line to rewrite. (you, AIOS tallies)
- [ ] Every booking: prospect added as guest on the slot, confirmation same day, reminder Sunday night. (AIOS drafts, you send)
- [x] 2026-10-01: the AV integrators placed in the call list (Prospects, Contacts) right after your last call, Neely's Auto Electric (#3270): 7,269 rows, the 842 checked integrators first, then 25 that turned you down in September, then 6,402 from the national sweep (not yet checked; mark misfits Wrong vertical as you go). New columns Vertical (on every row), Owner, Queue, Call order. (AIOS)
- [ ] In Airtable, the Contacts grid: Sort, pick "Call order", 1 to 9. Once; the API cannot set a view's sort. Then hide Queue and Call order if you like. (you, one minute)

</details>

<details>
<summary><b>Google Ads, Monarc's own (added 2026-09-25): your items from the plan</b></summary>

Plan and checklists in `projects/google-ads/`. The AIOS does the keywords, tiles, images, pages, ads, and rows; these are the clicks and answers only you can give.

- [x] Fix the declined payment on the Google Ads account (notice of 2026-09-01) and confirm the account is not suspended. First gate; nothing else matters until it is done. (you) Done: Jonathan, 2026-10-01 ("Billing is fixed"); gate ticked with `ads_publish.py tick billing`.
- [x] Read the account's conversion actions and any live campaigns to the AIOS so `projects/google-ads/account.md` fills in; then make "Submit lead form (6)" the one Primary action and "Page view (9)" Secondary. (you, 10 minutes) Done 2026-10-02: the gate reads "main: Submit lead form (6)" only; all five gates pass for 07, so Go live is open (yours to press).
  - 2026-10-01: read by the AIOS. Two actions are on: "Submit lead form (6)" (keep) and "Page view (Page load monarcbuild.com/book) (4)". Your call: the page view is not a conversion any more. The API refuses any change to it (it was made in the Google Ads screen as a page-load rule), so remove it there: Goals, Summary, click the action, Remove (or Edit settings, Secondary action). Then the One main conversion gate passes on the next read. (you, 2 minutes)
- [ ] Account settings: final URL suffix (the one line in `account.md`), auto-tagging on, GA4 linked with `book_appointment` imported as Secondary, auto-apply recommendations off, your home and office IPs excluded. (you, 20 minutes)
- [x] Confirm the three new slugs: `/seo/`, `/facebook-ads/`, `/ai-automation/`. Confirmed 2026-09-25.
- [x] Confirm the image credit spend on the connected generator before the first batch (14 renders, four candidates each). Approved 2026-09-25: 112 credits.
- [x] Full-page build order after the tiles: Google Ads, Website, SEO, Email, Facebook, Automation. Confirmed 2026-09-25.
- [ ] Name the tool behind each automation card (proposals, follow-up and missed-call text-back, invoicing, bookkeeping) and run it on Monarc's own line first; nothing prints on `/ai-automation/` before that. (you)
- [ ] The footer phone number for the six pages. (you, one line)
- [ ] One call-script line per service outside the Pilot Service Agreement (website build, SEO, email, Facebook ads, automation), so the call can scope what the page invites. (you, AIOS drafts on your word)
- [ ] Keyword Planner, two runs per service line, six lines, about 20 minutes each; US, English, 12 months. The lists are ready in `projects/google-ads/keywords/paste/`: paste `<service>-discover.txt` (ten seeds) into "Discover new keywords" with `https://monarcbuild.com/website-build/` as the page, and `<service>-volume.txt` into "Get search volume and forecasts". Export both to `projects/google-ads/keywords/keyword-planner/`, dated. (you)
- [ ] SERP screenshots for the top 20 buy-now terms per funded campaign into `projects/google-ads/keywords/serps/`. (you, 20 minutes per campaign)
- [x] Render picks. Done 2026-09-26 (all six heroes, SEO and Facebook cards); exported to `public_html/assets/generated/`.
- [ ] Facebook card 3 (retargeting) has no render: pick one of the four boomerangs, rerun with another object, or use an icon. (you, one line)
- [ ] Approve the six style tiles (the looks themselves), and see the pending note below: `projects/Landing Page Build/renders/2026-09-25/tile-<theme>-1440.png` (google, editorial, saas, commercial, social, time), candidates side by side at the bottom of each; the recommended pick per image is in each `projects/Landing Page Build/pages/<slug>.md`. Then six page renders, then the push of each page. (you, as each lands)
- [x] Decide the h1 trade-word swap: one page per service serves several trade ad groups; recommended, each ad's link carries the trade (`?t=electricians`) and the h1 shows it. (you, one line; Section Spec "Service pages") Decided 2026-10-01: "headline swaps in the trade from the ad link".
- [ ] Build the trade swap on the six service pages and put the trade on each ad group's link; renders before the push. (AIOS, after the `/av_marketing/` copy round)
- [ ] **CRM: a Website card with one card per landing page (Jonathan, 2026-09-26).** In the CRM, a Website card that opens to a card for each landing page: `/google-ads/`, `/website-build/`, `/seo/`, `/email-marketing/`, `/facebook-ads/`, `/ai-automation/`, and `/av_marketing/`. Each page card shows impressions, clicks, average time on page, and the spend of the campaign that points at it, each against the previous period. Data sources: GA4 `G-JQ977C0MY7` for time on page, which GA4 calls average engagement time, read by page path; Google Ads for impressions, clicks, and spend per campaign, since GA4 does not count ad impressions. Until the Google Ads API is wired, spend, impressions, and clicks come from the numbers typed on the Airtable campaign rows each Friday. Needs first: the GA4 read access (the official GA4 MCP or the Data API, `references/github-skills-shortlist.md`) and the GA4 link to Google Ads. Build after the first page is live and has a week of data. (AIOS)
- [ ] The test click after the first page is live (item 13 in `projects/google-ads/tracking-checklist.md`): book a slot through the tagged link, then delete the test event. (you and AIOS)
- [ ] **Publish from the CRM (plan approved 2026-09-28).** About 12 keywords per campaign picked on buying intent (no volume tool, your call 2026-09-28), then an Ads screen in the CRM where you approve spend, keywords, negatives, and the ad, and publish. Your steps:
  - [x] Lock the keywords per campaign (`projects/google-ads/keywords/picks.json`). Locked 2026-09-28: 72, twelve per campaign.
  - [x] The Ads screen, the publisher, the negative lists, the six ads, and the morning pull: built and tested offline 2026-09-28 (AIOS).
  - [x] Google Cloud project as jonathan@monarcbuild.com: turn on the Google Ads API, press "Apply for access" (Explorer), make an OAuth client of type Desktop app, put `GOOGLE_ADS_CLIENT_ID` and `GOOGLE_ADS_CLIENT_SECRET` in `secrets.env`, then run `python scripts/google_ads_api.py --login` once. Step by step: `references/google-ads-api.md`. No manager account or developer token needed any more. (you, 20 minutes)
  - [x] Confirm the customer id 418-577-4900 in `projects/google-ads/account.md`. Confirmed 2026-09-29: the new login reaches exactly this one account.
  - [x] OAuth client (ID saved as `GOOGLE_ADS_API_KEY`, secret as `GOOGLE_ADS_CLIENT_SECRET`) and `--login` done 2026-09-29; refresh token saved.
  - [x] Explorer access for the Cloud project. `--check` on 2026-09-29: "CLOUD_PROJECT_NOT_APPROVED_FOR_PRODUCTION: only approved for use with test accounts". In the Cloud Console, Google Ads API page, apply for access (Explorer). Then the AIOS reruns `--check`. (you) Granted 2026-09-29 (Google's approval email, 3:58 pm); the API reads the account.
  - [ ] Publishing status "In production" on the consent screen, so the login does not expire every 7 days (Testing-mode logins do). (you, one click)
  - [x] In the CRM, Channels, the Google Ads card (the Ads tab moved there 2026-09-29): open each campaign, read and approve the spend, keywords, negative lists, and ad, starting with 01. X any headline you don't want and add your own. (you) Done 2026-09-30: you approved part in the CRM and said in chat all six are approved; the AIOS recorded the rest in your name (01 ad; 03 negatives and ad; 04 keywords and ad; 05 all four; 06 keywords and ad). All six ready, every check passes.
  - [x] Ready to publish 2026-09-30 (AIOS): 210 of the 213 places have Google location ids (Martha's Vineyard, Sea Island, and Lake Minnetonka have no Google place by that name; stand-ins below). Offline plans: 01 about 1,070 operations (it creates the 12 shared negative lists once), each later one about 320.
  - [ ] Publish, paused, from the Google Ads page (each campaign's ad card, Publish). Explorer access allows 2,880 operations a day and each Publish runs twice (Google rehearses first). Nothing spends until Go live. (you, or say go and the AIOS publishes)
    - [x] 03 SEO published paused 2026-09-30 (your call: "only publish SEO for now"). Google campaign 24300217869: $20 a day, search only, 24 keywords, 1 ad, 200 places; it created the 12 shared negative lists, so each later campaign is about 320 operations. The read-back found six wrong place matches (Denver had matched a Nebraska county, Northern Virginia a Chesapeake Bay county, Highlands NC a Raleigh ZIP, Franklin TN and Santa Rosa Beach FL the wrong counties, Providence all of Rhode Island); fixed and republished the same day.
    - [ ] 01, 02, 04, 05, 06: waiting on your go.
    - [ ] 07 AV marketing (new 2026-09-30, lands on `/av_marketing/`, $20 a day): read and approve its keywords, negatives, spend, and ad on the Google Ads page (open 07, the Advertising card). Then say go and the AIOS publishes it paused (286 operations). Drafted from your interview: `brainstorms/2026-09-30-av-marketing-google-look.md`. (you)
  - [x] `/av_marketing/` in the homepage look (built 2026-09-30, look only, every word kept, the eyebrow "Marketing for AV integrators" added): approve the renders in `projects/Landing Page Build/renders/2026-09-30/av_marketing-google-*.png`, then say go to push it. At the push, decide whether the journey tag rides along (it waits on your privacy-page lines). (you) Pushed 2026-09-30 on your "push", with the approved logo banner and the stylesheet's large-logo rules; the journey tag held back. Read back identical (`context/website.md`).
  - [x] Places: 78 of the metro names matched a whole TV market (Chicago = the Chicago DMA with its suburbs) and 107 matched city limits only (the enclaves, and some metros). Pick one rule for metros: whole metro (recommended: contractors' shops sit in the suburbs) or city limits. (you, one word) Your call 2026-09-30: city limits. Done: every name is now its own city (202), neighborhood (3), or, for the five that are not cities, its county (Fairfax for Northern Virginia, Westchester, Cape Cod, Nantucket, Walton for Santa Rosa Beach). The state check caught five more wrong matches (Washington DC had matched Rockville MD; San Jose and Oakland, San Francisco; Tacoma, Seattle; Leawood KS, Leawood MO). 03 republished with it; every later campaign takes the same list.
    - [x] 03 SEO budget $40 a day (your call 2026-09-30), set at Google; still paused.
  - [ ] The three places with no Google match: Martha's Vineyard (stand-in Dukes County, MA), Sea Island (Glynn County, GA, which holds St. Simons and Sea Island), Lake Minnetonka (Minnetonka, Wayzata, and Orono, MN). Say yes and the AIOS adds them. (you, one word)
  - [ ] The Keyword Planner and SERP screenshot items above are no longer needed for these keywords; keep them only if you want the wider lists read. (you, one line)
  - [x] Readiness check 2026-09-29 (AIOS): all six campaigns rehearse offline (about 1,050 to 1,100 Google operations each, so one new campaign a day on Explorer access); all six ads pass the copy check; no negative blocks a keyword (4,921 checked); all six live pages pass the 12-point wiring check (checklist item 12 ticked); six Campaigns rows (Planned) and six Landing pages rows added in Airtable under the Google Ads channel, named so Publish updates them. Blocked on: the Google Ads connection (no keys on the machine), the 24 approvals, and gates 1, 2, 3, and 5.

</details>

<details>
<summary><b>Prospects verticals (added 2026-10-01): every company labeled by the trade it covers</b></summary>

All 15,180 rows in Prospects, Contacts carry a Vertical (twelve choices), set by `scripts/label_verticals.py` and read back. Review file: `projects/outreach/vertical-labels-2026-10-01.csv`.

- [ ] Drag the Vertical column next to Name in the grid. Airtable's API cannot move a column. (you, one drag)
- [ ] While calling the integrator queue, filter the grid to Vertical is AV integrator: 3,792 of its 7,269 rows are integrators. (you, one filter)
- [ ] New lists: run `python scripts/label_verticals.py --ai --crawl` after an import, then `--write`. (AIOS)

</details>

<details>
<summary><b>Booker journey (added 2026-09-28): each booker's click, pages, and booking in one CRM view</b></summary>

Built and tested locally; nothing is live. The CRM side already works (lead page, LinkedIn booking rate by medium).

- [ ] Approve the two new privacy lines in `projects/monarcbuild-site/public_html/privacy/index.html` ("When you book: the pages you viewed..." and "The site also keeps a short list..."). (you)
- [ ] Say go to push: `assets/journey.js`, the homepage, `/about/`, the six service pages, `/book/`, `/privacy/`, and `/av_marketing/` from its staging copy. The AIOS diffs each against live first. Since 2026-10-01 the same push carries the popup changes (`scripts/popup_update.py`): your name out of the booking flow, the back arrows, and a picked day scrolling its times into view; `assets/site.css` goes with them. (you, one word; AIOS)
- [ ] Republish the booking script: paste `scripts/avmarketing-booking.gs` into the Apps Script project, Deploy, Manage deployments, pencil, New version, Deploy. Same address. Brings the journey, the first-click credit, the LinkedIn referrer rule, the `agenda` action, and (2026-10-01) the no-name copy live at once: event title "Monarc Build audit: {first name}", sender "Monarc Build", the confirmation and reminder without your name, and (2026-10-02) your own test bookings no longer written to Airtable. (you, 3 minutes)
- [ ] Better than a republish: move the booking script and the "Monarc Build" calendar from sumreat17@gmail.com to jonathan@monarcbuild.com (found 2026-10-01: the setup ran both as sumreat17, so site bookings and their Meet links can show sumreat17). A new Apps Script project signed in as jonathan@monarcbuild.com, the calendar shared to it or a new one made there, the new web app address on the pages. Say go and the AIOS writes the click-by-click steps and swaps the address on the pages. (you, about 20 minutes)
- [ ] Each Friday: type LinkedIn ad clicks on each ad campaign row and post clicks on the "LinkedIn posts" row, so the booking rates have their base. (you, until the LinkedIn and Google Analytics reads are wired)
- [ ] Links in DMs carry `?utm_source=linkedin&utm_medium=dm&utm_campaign=linkedin-messaging`; links in posts `?utm_source=linkedin&utm_medium=social&utm_campaign=linkedin-posts&utm_content=<post date>`. (you)
- [ ] `/about/`'s build parts carry another session's banner change that is not in the page yet; rebuild it only after that change is reviewed. (AIOS flags it at the next `/landing-page` pass)

</details>

<details>
<summary><b>Meta ads: the builder search check (added 2026-10-03): live Tue 2026-10-20, $30 a day</b></summary>

Plan, funnel, spend, and the six gates: `projects/meta-ads/README.md`. Interview: `brainstorms/2026-10-03-meta-ads-builder-search-check.md`. The campaign row "Meta: builder search check" is on the Meta ads card (Pipeline, the journey map; Channels). Nothing spends before the six gates are ticked; the AIOS never presses go live.

Yours:

- In Today's list since 2026-10-03: the Meta accounts (Business Manager, the ad account, the Page, Instagram, the Pixel; the Pixel id and the ad account id to the AIOS). (you, about an hour)
- In Today's list since 2026-10-03, under the three ad videos: confirm the proof span, approve the three scripts in `projects/meta-ads/scripts.md`, record three takes of each, then cut, caption, and export the three in Monarc Studio. (you)
- In Today's list since 2026-10-03, under the landing page: approve the `/builder-check/` style tile, then the page render. (you)
- [ ] The three boxes under Booker journey above: approve the privacy lines (now four tags, Meta added), say go to push, republish or move the booking script. All three are gates for this campaign. (you)
- In Today's list since 2026-10-03: approve and post the three Page posts in `projects/meta-ads/page-posts.md` once the AIOS brings the creative (pick one of the three clips for post 2). The ad waits a week of Page age. (you)
- [ ] Test booking on `/builder-check/` from a non-self address through the tagged link; check the Leads row (Source meta-ads, the campaign, the four answers) and Events Manager's Test Events (Lead, Schedule). Then delete the test event. (you and AIOS)
- [ ] Build the campaign paused in Ads Manager from the README (Leads objective, the Lead event, US 30 to 65 business owners, Feed, Reels, Stories, $30 a day, the three ads, the tagged link). Put the campaign id in the row's Platform id. (you; the AIOS fills the row)
- [ ] Go live Tue 2026-10-20. Each Friday type spend, impressions, and clicks on the row. The $500 read about Nov 5; stop at $1,000 about Nov 19 unless one qualified booking was held. (you)

The AIOS:

- [x] The brief, the scripts, the check, the Page posts (`projects/meta-ads/`), the Campaigns row, the journey card, the decisions, the attribution fix, `fbclid` in every popup, the Pixel script (`scripts/meta_pixel_update.py`), the privacy lines in the mirror, the booking-script changes (the check answers, the page path, the day-before reminder). Done 2026-10-03.
- In Today's list since 2026-10-03: the Higgsfield Ad Multiplier pass on the three picked takes, the creative for the three Page posts, the ad script template (`templates/ad-script.md`), and `/builder-check/` through `/landing-page` from `projects/meta-ads/check.md`. (AIOS)
- [ ] `python scripts/meta_pixel_update.py --pixel <id>` once the Pixel id arrives; the push on his go. (AIOS)
- [ ] The $500 read written to `projects/meta-ads/reports/`. (AIOS, about Nov 5)

</details>

<details>
<summary><b>Review Generation Farm (added 2026-09-28): free Fiverr builds for portfolio, prospects, reviews</b></summary>

Campaign "Review Generation Farm" in Airtable (Source Fiverr); one row per business in the Portfolio builds table. Rules on the campaign row: ask for the review after delivery, never as the price of the build; keep Fiverr talk on Fiverr.

- [ ] Fiverr seller profile and one website gig under Monarc Build (Fiverr's lowest order is $5; decide $5 or a free sample in messages). (you)
- [ ] First three requests found and offered; a row each in Portfolio builds. (you)
- [ ] Monarc's Google Business Profile live before any Google review is asked (NAP citations list, item 1). (you)
- [ ] Draft the after-delivery message: thanks, the portfolio ask, the review ask with no strings. For your approval. (AIOS)
- [ ] Each delivered build: link or create its CRM company with Source Fiverr so it joins the prospect list. (AIOS)

</details>

<details>
<summary><b>LinkedIn messaging (added 2026-09-28): the weekly export</b></summary>

- [ ] First run: LinkedIn, Settings & Privacy, Data privacy, Get a copy of your data; tick Connections, Invitations, Messages; Request archive. When the email arrives (about ten minutes), download the zip and tell the AIOS where it is. The AIOS runs `python scripts/linkedin_import.py <zip>` as a dry run, checks the list with you, then `--write`. (you, 5 minutes; AIOS)
- [ ] Every Friday after that, the same download; the AIOS loads it. (you and AIOS)
- [ ] On the LinkedIn page in the CRM, click a person to mark Booked or Not interested when it happens. (you)

</details>

<details>
<summary><b>NAP citations, Google Organic (added 2026-09-27): 12 directory listings</b></summary>

Campaign "NAP citations" in Airtable (Campaigns, channel google-organic); one row per directory in the Listings table, in order. The NAP: Monarc Build, service-area business in Riva, MD with the street hidden, the new Google Voice number, monarcbuild.com. The CRM's Google Organic page shows the list; click a row to mark it Submitted, Live, and so on.

- In Today's list since 2026-10-03, with a sign-up link for each directory: the Google Voice number, the Business Profile (service-area business, verification started first; it can take days), then the other 11 in order (Bing imports the profile once verified), each row marked as you go. (you)
- In Today's list since 2026-10-03: the listing copy for your approval once the number exists, and the NAP check on each live listing. (AIOS)
- [ ] The website's search markup says Annapolis and has no phone: change it to Riva, MD and add the Google Voice number, through `/landing-page`, pushed on your go. (AIOS)

</details>

<details>
<summary><b>URGENT 2026-09-08: WH Smart Home meeting</b></summary>

- [x] Resolved 2026-09-11: the meeting happened, with Doug. Jonathan passed on two install teams. Parked to Mon 2026-10-05.
- [x] Logged in the Pipeline table 2026-09-11.

</details>

<details>
<summary><b>Website: make monarcbuild.com match the offer (added 2026-09-08, prospect pending)</b></summary>

Findings in `context/website.md`. Site is on Hostinger, edits are Jonathan's.

- [x] Decide: two-tier offer on the site. Decided 2026-09-08, logged in `decisions/log.md`.
- [x] Homepage rebuilt with nine sections (hero, problem, solution, benefits, proof, FAQ, offer without prices, final CTA, footer). Approved and pushed live 2026-09-08. Original archived at `archives/site-2026-09-08-original/`.
- [x] First Responder on the page (in the draft).
- [ ] Hero strip: three rendered photos with the three outcome lines, built in the wireframe copy; push to the live page on Jonathan's approval (`assets/hero/*.jpg` plus `index.html`).
- [x] Handoff PDF for a designer and an SEO, one frame: `projects/monarcbuild-site/handoff/2026-09-08-homepage-handoff.pdf` (2026-09-08).
- [ ] From the handoff's SEO notes: canonical tag, FAQPage schema, meta description to ~155 chars, new og:image from the hero set, mobile nav, redirect or noindex /territories and /permit-intelligence.
- [x] Proof wording corrected on the homepage, the results page ($110K to $70K, $135K to $91K), and `context/offer.md` to Jonathan's values. Pushed 2026-09-09. Still unverified on /results: the $300K lunch-and-learn, $250K+ cold call, and $120K referral figures.
- [ ] Results page: the Annapolis story with the real numbers, named and dated where the client allows. Fix $110K vs $90k and "three years" vs "four years."
- [ ] Signal feed builders and permits: confirm real, or label as sample, or remove.
- [ ] Phone and email in the footer.
- [x] /book form delivers: two test submissions at 2:23pm on 2026-09-09 landed in the Proton inbox as "New Monarc Build lead" from formsubmit.co (test entry: PawPackz LLC, Dallas, 443-822-6004). Activation is done.
- [ ] /book: add a Google Calendar appointment link so a prospect can book a slot without waiting a business day.
- [x] Connect the AIOS to `public_html`: FTPS via `.env`, `list` and `pull` verified, 17 files mirrored. Done 2026-09-08. See `references/hostinger-api.md`.
- [ ] Security follow-up: rotate the FTP password and Hostinger API token; create a scoped `aios` FTP account limited to `public_html`.

LinkedIn ad page `/avmarketing/` (built locally 2026-09-13, form rebuilt 2026-09-14 to metro, name, email, team size, hourly afternoon times with automatic Meet invite; renders in `projects/Landing Page Build/renders/2026-09-14/`. **Pushed live 2026-09-14** with the placeholders below still empty; each fix is a one-line edit and a re-push of `avmarketing/index.html`):
- [ ] Approve the 2026-09-14 renders (step 1 metro, step 4 team size, step 5 sample times, sent booked, sent no slot, 1440 and 390) or mark up changes. (you)
- [ ] Deploy the booking backend, about 10 minutes: script.google.com as the calendar owner, paste `scripts/avmarketing-booking.gs`, add the Google Calendar API service, set `TOKEN`, run `selfTest`, deploy as a web app (execute as Me, access Anyone), paste the URL into `BOOKING_URL` and the token into `BOOKING_TOKEN` in the page. Steps in `references/apps-script-booking.md`. Until deployed the live page falls back to the calendar button. The public free/busy setting on the calendar is no longer needed and can be turned back off. (you, AIOS pastes the values)
- [ ] Decide: the applicant auto-reply text in `_autoresponse` (two lines, signs "My Best, Jonathan") is a draft in your voice. Approve or rewrite. (you)
- [ ] Decide: phone, company, and brands are no longer asked on the form. Asked on the call, or add one back. (you)
- [ ] VSL script: v1 drafted 2026-09-13 in `templates/vsl-draft.md` (Monarc worked example, 192 words). Approve or mark up, confirm the credential wording and the term, then record. Until then the slot shows the three hero stills with "Video coming." (AIOS drafted, you approve and record)
- [x] Dropped 2026-09-14: the calendar-link button came off the page (Jonathan). Booking runs through the Apps Script; with no time picked, Jonathan emails two times. No appointment schedule needed for this page.
- [ ] Set the flight deadline in `DEADLINE` in the page script (placeholder is 2026-10-01 Eastern). (you)
- [ ] LinkedIn Campaign Manager: confirm the destination is `https://monarcbuild.com/avmarketing/` with the trailing slash, and check on the ad preview whether `{{AD_SET_ID}}` is substituted or arrives as literal text (LinkedIn's macro is `{{CAMPAIGN_ID}}`). (you)
- [ ] After push: one test booking through the page from a non-Gmail address; confirm the event lands on "My Calendar " with a Meet link, the invite reaches the applicant address, and the formsubmit email carries metro, team size, the time in Eastern and local, booking status, the Meet link, reply-to, and the UTM rows. Then delete the test event. (AIOS drafts the test, you submit)
- [ ] Decide: keep `patrick@monarcbuild.com` on CC (carried over from /book), phone required on the application (was optional on /book), `noindex` on the ad page. (you)
- [ ] Decide: the Google Ads "Submit lead form" snippet fires only on `?sent=1` on this page (on /book it fires on every view). Add a LinkedIn Insight Tag or GA4, or neither. (you)
- [ ] Time the form on a phone and replace "Takes about a minute" with the measured number. (you)
- [x] Push: `avmarketing/index.html` plus the three `assets/hero/*.jpg` stills, via `scripts/site_sync.py push`. Done 2026-09-14 on Jonathan's "publish". Verified live: page 200 with UTMs intact, images 200, no-slash 301 keeps the query string.
- [ ] Re-push `avmarketing/index.html` after each placeholder above is filled. (AIOS, on your go)

</details>

<details>
<summary><b>Monthly, last business day</b></summary>

- [ ] Papers and dates (added 2026-09-16, `records/README.md`): Maryland Annual Report due **April 15, 2027** ($300, Maryland Business Express); quarterly estimated tax **January 15, April 15, June 15, September 15**; 1099-NEC to any contractor paid $600 or more by **January 31**, W-9 collected first. Put all four on the Monarc Build calendar with a two-week reminder. (you)
- [ ] Operating agreement, one-owner version, signed and filed in `records/entity/`. Banks ask for it. (AIOS drafts, you sign)
- [ ] Money in and out on the CRM's Money page (2026-10-06): one click first, add the base "Monarc Books" to the Airtable token at airtable.com/create/tokens (Edit token, Access, add a base). Then the AIOS runs `books.py stripe-sync` and `books.py spend-sync --write` ($2,119.48 of known charges: Google Places, Anthropic, AI Acquisition; confirm the $1,990 against the receipt) and the page shows them. Then export the September and October bank CSVs so every other charge lands too. (you: the click and the CSVs; AIOS: the runs)
- [ ] September: money loop, 15 minutes. Revenue, costs, pay salary, invest the percent, hours per client. Run `python scripts/books.py month-end 2026-09` after the bank CSV is loaded (`references/books.md`). (you, AIOS summarizes)
- [ ] September: capacity check. Hours per client, your build hours. (you)
- [ ] October: money loop.
- [ ] October: capacity check.
- [ ] November: money loop.
- [ ] November: capacity check.

</details>

<details>
<summary><b>Per-client checklist (copy for each client)</b></summary>

- [ ] Invoice same day.
- [ ] Kickoff with questionnaire, calendar access. Onboarding questionnaire back and in the capture; asset list items 1 to 7 in `projects/clients/<slug>/assets/`.
- [ ] Build live within 14 days, hours logged.
- [ ] First Responder on, every lead logged.
- [ ] Weekly PDF every week.
- [ ] Day 60: results review, 6 month term signed, one proof line pulled onto the offer page, two referrals asked.

</details>

<details>
<summary><b>Backlog: Stage 2 and later, do not start yet</b></summary>

- [ ] Hire part-time First Responder at 3 Level 2 clients or the first missed 5 minute week.
- [ ] Hire build and SEO contractor at 20+ build hours a week.
- [ ] Raise new-client price after a month with close rate above 40%.
- [ ] Account manager at 15 clients.
- [ ] SOPs in `references/sops/` for each loop handed off.
- [ ] Owner dashboard: MRR, month-6 churn, gross margin, owner profit, referral percent, net worth.
- [ ] Valuation at 30 clients and 24 months of clean books.

</details>

---

## The stake

Stronger than any reward. One person asks you every Friday how many dials you logged. Two missed or dishonest weeks in a row, you owe them $200.

Stake person: ____
