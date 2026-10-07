# Decisions Log

Append-only record of meaningful decisions and why they were made. `/level-up` Phase 2 (Method interview) writes scoped automation specs here. You can also append manually whenever you decide something worth remembering.

**Format per entry:**

```
## YYYY-MM-DD — Short title

**Decision:** what was decided.

**Why:** the reasoning, constraints, and what would change your mind.

**Alternatives considered:** what else was on the table.

**Owner:** who's accountable.
```

Keep it terse. Future-you will thank present-you for capturing the *why*, not just the *what*.

---

## 2026-09-06 - Audit evidence and routing maintenance

**Decision:** Ship audit rubric v2 and a small /link skill. Audit scores working evidence across the Four Cs, checks operating-manual routing and freshness, and passes one concrete gap into /level-up. A selected repair can improve an existing workflow instead of creating another skill.

**Why:** File counts, configured keys, named rituals, and recent edits do not prove an operational AIOS. Source findability and freshness need explicit checks.

**Alternatives considered:** Keeping presence-based scoring or requiring a hot cache. Neither reliably establishes retrieval quality or successful execution.

## 2026-09-06 - Portable skills and automatic audit history

**Decision:** Ship all four skills for Claude Code and Codex, with bundled resources, matching operating manuals, and a script for regenerating Codex copies. Audit reports are saved automatically, preserve previous runs, and track findings across comparable inspections.

**Why:** Students need the same shared guidance when switching assistants and evidence of actual improvements over time. Intentional runtime adaptations, unknown verification, and confirmed defects are reported separately.

## 2026-09-06 - Portable 3D Brain skill

**Decision:** Add `/3d-brain` for Claude Code and Codex. Ask for a name and categories, map selected local folders, and scaffold a bundled, configurable application with spherical placement, Cinema, and interactive growth replay.

**Why:** Shipping the working renderer preserves the intended appearance and interactions across AIOS installations. A prose-only prompt would produce inconsistent recreations. User config and graph data remain local; the public package includes only code, documentation, dependency notices, and fictional test inputs.

## 2026-09-06 - Add ongoing context interviews

**Decision:** Adapt Herk-2's grill-me skill for the student kit and ship matching Claude/Codex packages. Save every answer to brainstorms/, preserve resumable Q&A history, and update canonical context only with confirmed facts during requested context-building sessions.

**Why:** Onboarding is an initial snapshot. Ongoing interviews capture changing priorities, decisions, and preferences while keeping tentative ideas distinct from current business facts.

## 2026-09-07 - Two-tier offer, B2B outreach dropped

**Decision:** Monarc Build sells two tiers. Level 1 at $2,500/mo (site, landing pages per service and area, managed Google Ads, SEO, weekly PDF report, monthly meeting) with a 60 day pilot, no setup fee, $1,000 matched ad spend, then a 6 month term. Level 2 at $4,500/mo adds First Responder, a human who calls leads within 5 minutes during 9am to 7pm Eastern weekdays and books into the client's calendar; month to month, never sold alone. B2B referral-partner outreach is off the offer.

**Why:** B2B outreach is too much overhead to deliver as a standard tier. First Responder depends on Monarc managing the site and forms, so it can't stand alone. The pilot lowers the barrier for the first 5 clients (due December 1, 2026); the 6 month term protects the retainer after proof.

**Alternatives considered:** Three-tier stack with B2B spine and permit monitoring (the earlier proposal structure). Selling First Responder standalone at $2,000/mo.

**Owner:** Jonathan Beach. Full offer in `context/offer.md`; interview in `brainstorms/2026-09-07-offer-doc.md`.

## 2026-09-08 - Landing page moves to the two-tier offer

**Decision:** Rebuild the monarcbuild.com homepage around nine sections (hero, problem, solution, benefits, proof, FAQ, pricing, final CTA, footer). Problem: integrators want predictable high ticket work but have no time to run top of funnel. Solution: sign with Monarc. Primary CTA "Apply now" to /book. Amended same day: the two tiers and their contents are on the page, but the dollar amounts are not. Prices are quoted on the call and on the offer doc. Permit intelligence and territory exclusivity come off the homepage.

**Why:** The page was selling the B2B permit offer that was scratched on 2026-09-07, with no prices and no First Responder. A prospect reading the site and hearing the offer on a call would hear two different companies.

**Alternatives considered:** Keep the territory story and quote the offer verbally.

**Owner:** Jonathan Beach. Draft lives in the local mirror until approved; site state in `context/website.md`.

## 2026-09-11 - Airtable is the campaign management layer

**Decision:** Outreach campaigns (dial log, pipeline, leads, weekly tally) are managed in Jonathan's Airtable account. The AIOS connects through Airtable's official hosted MCP server (`https://mcp.airtable.com/mcp`), declared in `.mcp.json`, authorized by OAuth via `/mcp`.

**Why:** Official MCP with search, create, update, and table and interface building; available on every Airtable plan; nothing to install locally (no Node on this machine); a real mobile app and form view for logging dials between calls. Google Sheets has no write path through the claude.ai connector. An AIOS-built page would be bespoke. Free plan caps at 1,000 records per base, so the 2,000-row integrator list stays in `projects/outreach/Integrator_List_2026-09-05.xlsx` unless the plan moves to Team.

**Alternatives considered:** Google Sheets through Google's preview Sheets MCP or a service-account server; a claude.ai artifact page with a shared database; xlsx on disk through Python.

**Owner:** Jonathan Beach. Base schema built by the AIOS after authorization.

## 2026-09-13 - Homepage SOP: style guide first, seven blocks, one page site

**Decision:** monarcbuild.com is rebuilt as a one-page site from a checkable style guide and section spec in `projects/Landing Page Build/`, governed by the `/landing-page` skill (build, render, drift check). Blocks in order: Hero (headline, sub, VSL centered), About (founder credibility, no tenure figure), How it Works (7 steps, step 5 labeled Level 2, step 7 a loop), Similar Results (three case tiles, numbers only, no testimonials until a real one exists), Portfolio (Monarc's work product, not room photos), Upsell (the two tiers and pilot, no dollar amounts), Final ask. One button label, "Book a 15 minute call," linking to a Google Calendar appointment schedule; appears in the hero and the final ask. Accent color Dark Oak `#61534E` on the button only. Serif headlines, sans body, regular and italic only. Content column two thirds of the viewport. Headlines 8 words max, subs 25 max. All six old subpages 301 to the homepage. The problem statement moves into the hero sub; the FAQ is cut. Section alignment is chosen from rendered variations, not decided in the abstract.

**Why:** The 2026-09-08 nine-section page and the client-site wireframe were two sources of truth with three competing style systems. A spec that can be linted keeps the page honest as it is edited. No tenure figure because the site said three years and the script said four. Numbers only in proof because the old results page promised named and dated case studies and delivered neither.

**Supersedes:** the 2026-09-08 amendment that the CTA is "Apply now" to the /book form. Tiers still appear without dollar amounts.

**Alternatives considered:** SOP for client pages first (the repeating Level 1 deliverable); staging path on the live host for approval (chose local renders); keeping /book and /results as subpages.

**Owner:** Jonathan Beach. Interview in `brainstorms/2026-09-13-landing-page-sop.md`, paused at Q23; resumes after he picks an alignment variation.

## 2026-09-13 - LinkedIn ad landing page at /avmarketing

**Decision:** The LinkedIn campaign destination is a standalone ad page at `monarcbuild.com/avmarketing/`, modeled on a ScaleClients.io application page: timer bar, brand mark, audience eyebrow, h1, sub, instruction line, VSL slot, then a one-question-at-a-time application form (six steps) posting to formsubmit.co with the LinkedIn UTMs in hidden fields. The sent state shows the one "Book a 15 minute call" button to the Google Calendar link. Scarcity on ad pages is regional exclusivity, "One integrator per metro," plus a countdown to one fixed deadline Jonathan sets per flight. The setup fee is never printed; Jonathan waives it live on the call as a concession. Terms at the foot: pilot, day 60, exclusivity, ad spend on top. Every Style Guide rule applies, with one exception: form step buttons "OK", "Back", "Send" (Style Guide section 6, `drift.py --type ad`).

**Why:** The campaign already carries `utm_source=linkedin` to a URL that did not exist, and the homepage rebuild is paused at the alignment pick. An application form captures the ad set per lead, which a calendar link cannot. Exclusivity and a deadline give a cold LinkedIn click a reason to act now; the pilot terms alone do not.

**Supersedes:** nothing on the homepage. The 2026-09-08 removal of territory exclusivity still holds for the homepage; exclusivity is stated on ad pages only. The countdown is the test of the offer.md internal note that a decision deadline is untested.

**Alternatives considered:** button only to the calendar (loses attribution); replacing /book or the homepage; a pay-after-results guarantee like the reference page (not on file, not introduced).

**Owner:** Jonathan Beach. Built locally, not pushed. Pending before push: deadline date, calendar link, VSL, test submission, LinkedIn macro check.

## 2026-09-14 - Inbox pass on boot, drafts from mycopy.md, never send

**Decision:** Every AIOS session starts with `/inbox`: read jonathan@monarcbuild.com through Proton Mail Bridge, summarize what needs Jonathan, draft replies into Proton's Drafts folder using the copy in `references/mycopy.md`, and leave one flagged report email in the inbox (subject "AIOS inbox report YYYY-MM-DD"). Skip rules: mail from Jonathan's own address (photos, notes, forwards), mail from patrick@monarcbuild.com, and anything on a chain (In-Reply-To or References header, or a Re:/Fwd: subject). The script cannot send and the skill never tries another way. Boot line in `CLAUDE.md` and `AGENTS.md`.

**Why:** Outreach replies are the task that eats the week. Drafts in his voice waiting in Drafts turn a reply into a read-and-send. Live threads stay his because the AIOS cannot see what was said on the call. The flagged report is the one place he checks for what the AIOS did.

**Alternatives considered:** a SessionStart hook (the script needs Bridge signed in, so a human-readable boot line that can say "Bridge is signed out" beat a silent hook); sending replies automatically (never).

**Owner:** Jonathan Beach. `references/mycopy.md` is his to edit; the AIOS invents no copy block. Script commands `triage`, `read`, `report` added to `scripts/proton_mail.py`; first live run pending Bridge sign-in.

## 2026-09-15 - Meta Ads seed from the integrator lists, crawled not bought

**Decision:** The Meta customer-list seed is built from the companies already on file (Tier A and B of the national seed plus the 887 call list, 2,254 domains) by crawling each company's own contact, about, and team pages for the owner's name, emails, phones, and Facebook and Instagram pages. `scripts/meta_seed.py`, no paid data source. Two uploads: every company with an email or phone (2,247 rows) and the strong cut with an owner name plus an email (388 rows) as the lookalike source. Paid enrichment for the 1,548 companies with no named contact is a separate decision, not yet made.

**Why:** The lists already carried name, phone, city, state, zip, and website; the only missing Meta identifiers were an email and a person's name, and roughly a third of integrator sites print both. A crawl is free and repeatable. Meta matches on personal identifiers, so business landlines and info@ boxes match poorly; the strong cut is what a lookalike needs, and it is thin (30 to 50 percent of 388 matched), which is the argument for enrichment if the audience comes back under a few hundred.

**Alternatives considered:** Apollo or Hunter first (about $60 to $150 for a month, owner name and work email by domain); using the LinkedIn company list as is (Meta has no company-list audience type).

**Owner:** Jonathan Beach. Files in `projects/outreach/`; task list has the upload, the spot-check, and the enrichment decision.

## 2026-09-13 - National integrator seed from Google Places, qualified by Opus 5, for the LinkedIn company list

**Decision:** The LinkedIn Matched Audience seed is built by two scripts. `scripts/places_seed.py` sweeps the Places API (New) Text Search across 213 locations (top US metros plus the enclaves where $2M to $25M homes cluster) with six query templates, capped at 3 pages per query with early stop, cached, and deduped against the 2026-09-05 list and the Monarc OS company repository (read only). `scripts/qualify_sites.py` fetches each unique website once, fingerprints the platform deterministically, then has `claude-opus-5` return fixed JSON (integrator yes/no, residential vs commercial, offerings, ICP brands, site quality) through the Batches API. Tier A = residential integrator with 2+ core offerings on a weak platform (WordPress, Wix, Squarespace, GoDaddy, Shopify, Weebly, Duda); Tier B = same on a custom platform; Tier C = review by hand; One Firefly, commercial, and non-integrators excluded. The upload file is Tier A+B. DC, MD, VA stay in the ad seed (flagged `DMV`); the dial list still excludes them. The 0 to 30 review rule does not apply to the ad seed. Combined spend cap for the first run: $200, enforced by the scripts before each paid step.

**Why:** LinkedIn needs 300+ matched companies and the 29-metro list was the whole universe. Regex scoring could not see platform, offerings, or brands, which are the hooks for the web-management offer. Weak-platform sites are the prospects who need Monarc most. DMV kept because the Annapolis agreement covers direct outreach, and Jonathan chose to keep them for ads on 2026-09-13.

**Credentials:** keys live in `%USERPROFILE%\.monarc\secrets.env`, the Monarc OS convention, under Monarc OS key names (`GOOGLE_MAPS_API_KEY`, `ANTHROPIC_API_KEY`). The AIOS reads that file after its own `.env`. One file, both OSes. See `references/credentials.md`.

**Alternatives considered:** dealer-locator scraping through the browser driver (free, slower, deferred as a follow-up); Haiku or Sonnet for the read (Jonathan named Opus 5); applying the review filter to the ad seed (would risk falling under 300 matches).

**Owner:** Jonathan Beach. Blocked on copying `secrets.env` to this machine; scripts verified without spend 2026-09-13.

## 2026-09-13 - GitHub skills shortlist, one winner per capability, and the /kickoff skill

**Decision:** SEO, design, and attribution skills come from GitHub, vetted against a fixed checklist and cut to one winner per capability in `references/github-skills-shortlist.md`. Winners: `AgriciDaniel/claude-seo` (plugin) for local SEO, audits, and schema; `coreyhaines31/marketingskills` for `programmatic-seo`, `site-architecture`, `cro`, `analytics`, `attribution`, `ads`; Anthropic `frontend-design`; boraoztunc `landing-page`; hardikpandya `stop-slop`; thatrebeccarae `wasted-spend-finder` and `html-report-builder`; ekusiadadus `gtm-javascript`. MCPs: the official GA4 server first, then Search Console, `cohnen/mcp-google-ads`, and `paolobietolini/gtm-mcp-server`. Nothing is installed until a client makes it necessary. The inputs those skills need from a client are collected by one skill, `/kickoff`, which books the Google Meet, runs a six-block questionnaire one question at a time with a checkpoint after every answer, and scaffolds `projects/clients/<slug>/brief.md` and `access.md`. Credential rule: grant-access and IDs only; no password, token, or key ever enters the repo, a capture, or chat; unavoidable shared logins go to Jonathan's password manager.

**Why:** Three repos ship the same `page-cro` and `analytics-tracking` text; two auditors disagree and double the work. The kickoff already exists in the offer and roadmap step 7 but had no script, and every downstream skill stalls without the same dozen access grants. One questionnaire makes client 1 through client 5 produce identical inputs, which is what the 14 day build and a part-time First Responder depend on.

**Rejected:** boraoztunc `service-booking-flow` (written for salons and clinics); arturseo and Spillwave UTM schemes (conflict with the LinkedIn template set 2026-09-13); Synter GTM agent (routes through a third-party key); `freema/mcp-google-marketing` (discontinued); alirezarezvani 380-skill bundle (violates "add only when it solves a real need"). Call tracking: no usable GitHub skill; build our own when Level 2 needs it.

**Alternatives considered:** installing whole bundles and pruning later; a separate onboarding skill per tool; storing client logins in `.env`.

**Owner:** Jonathan Beach. Winners are AIOS picks from reading the files; he approves the install order before Phase B runs.

## 2026-09-13 - VSL drafting template, run inside the client kickoff

**Decision:** One template, `templates/vsl-draft.md`, drafts the hero video for monarcbuild.com and for every client landing page. Length 60 to 90 seconds, under 220 words. Structure adapts the cold call jobs to video: HOOK, BOUND, FILTER, PROVE, NAME, ASK, LOCK, HOLD, one job per line. One viewer per video. The targeting brief (viewer, term, area, project band, outcome, three fears, speaker, artifact, next step, banned words, logistics) is collected as Block 7 of the `/kickoff` questionnaire (Q34 to Q41), asked by Jonathan on the call after the proof and build blocks and before the closing question. The AIOS drafts v1 into `projects/clients/{slug}/vsl.md`; Jonathan approves before the client sees it. Monarc's own VSL uses the same template; v1 is in the file, awaiting Jonathan's approval on the credential wording (no years, per the site rule) and the term.

**Why:** Every landing page Monarc builds has a 16:9 VSL slot, and no script existed for Monarc's or a client's. The kickoff already captures most of the targeting facts; eight more questions make the video repeatable across clients. One job-per-line system across call, email, and video means one set of rules to drill.

**Alternatives considered:** classic hook, problem, agitate, solution, proof, CTA beats (familiar, but a second vocabulary to maintain); a separate `/vsl` skill (the template plus Block 7 is the whole mechanism, same as the follow-up email); the client filling a doc alone (loses the "their words" answers the NAME line depends on); two cuts, short and long (the hero slot only needs one).

**Owner:** Jonathan Beach. Approves the Monarc v1 and decides hosting (self-hosted mp4 vs embed, still open from Q7).

## 2026-09-14 - /avmarketing application funnel: three questions, then live afternoon times

**Decision:** The LinkedIn ad page's form is four steps, one question each: name, email, team size, then a set of open afternoon times read live from the business calendar (Google Calendar, connections.md row 3). Afternoon is 1:00 pm to 5:00 pm Eastern, 15 minute calls every 30 minutes, nothing sooner than 45 minutes out; a full afternoon rolls to the next weekday. The applicant picks a time or "None of these work." Send posts to formsubmit.co with the LinkedIn UTMs and the held time, Jonathan gets the email with reply-to set to the applicant, and the applicant gets a one-line auto-reply. The sent state names the held time; the "Book a 15 minute call" button appears only when no time was picked. Style Guide 6.2 amended, 6.10 added.

**Why:** Jonathan's words, 2026-09-14: UTM parameters on the submit, a multi step funnel with name, then email, then team size, then open times that afternoon from his calendar, and an email notification on submission. Three questions instead of six cuts the form to the decision the call needs (who, where to send the invite, how big the shop) and puts the booking inside the attributed form instead of behind a calendar link that drops the UTMs.

**Supersedes:** the six-step form in the 2026-09-13 ad page decision (business, project size, metro, brands, name and company, email and phone). Metro, phone, and the brand list now get asked on the call.

**Alternatives considered:** embedding the Google Calendar appointment schedule (books automatically, but drops the UTMs, re-asks name and email, and is not styled); a PHP endpoint on Hostinger with a service account (books automatically, but a secret on the shared host and no way to test it locally); keeping metro as a fourth question (Jonathan did not ask for it; flagged on tasks.md).

**Owner:** Jonathan Beach. Built locally, not pushed. Pending before push: calendar shared as free/busy, restricted API key, deadline, auto-reply text, the decision on metro.

## 2026-09-14 - /avmarketing funnel amended: metro as the call to action, hourly slots, automatic Meet invite

**Decision:** Amends the entry above, same day, Jonathan's words. Team size options are Just me, 2-5, 6-10, 11+. Slots are one per hour (1, 2, 3, 4 pm Eastern), not every 30 minutes. Metro comes back as step 1 and is the page's call to action, "Check your metro's availability." Times display in the applicant's own time zone, Eastern beside them when different. Picking a time must create the calendar event and send the invite with the Meet code by itself. Mechanism: a Google Apps Script web app in the calendar owner's account (`scripts/avmarketing-booking.gs`) serves the open slots and books the picked one on the business calendar with a Google Meet link, `sendUpdates: all`. The page then posts the application to formsubmit.co with the booking status and Meet link. Style Guide 6.10 rewritten; `connections.md` row 15; setup in `references/apps-script-booking.md`.

**Why:** A held time that only arrives as an email leaves the invite to Jonathan's hands and delays the confirmation the applicant is waiting on. Apps Script writes to the calendar as Jonathan with no server, no key on Hostinger, and no public calendar. Hourly slots keep four clean choices on one screen and leave gaps between calls. Metro first restores the exclusivity check and gives the form a reason to start.

**Supersedes:** the browser API key and public free/busy calendar approach from the morning entry (never deployed). The calendar's public setting is no longer required.

**Alternatives considered:** Google Calendar appointment schedule embed (books, but drops UTMs and re-asks the fields); PHP on Hostinger with a service account (a secret on shared hosting, and service accounts cannot mint Meet links on a consumer account); a scheduled AIOS job reading the Proton inbox and booking through the Calendar connector (minutes of delay, not "triggered by the slot").

**Owner:** Jonathan Beach. Built locally, not pushed. Pending: deploy the script, paste URL and token, deadline, calendar link, auto-reply text, test booking.

## 2026-09-15 - Monarc CRM: Airtable base behind a local dashboard in the style guide

**Decision:** The CRM is an Airtable base ("Monarc CRM", six tables: Companies, People, Deals, Activities, Sources, Config) behind a custom dashboard served locally by `scripts/crm_server.py` from `projects/crm/`. Jonathan's five jobs, in his words, are the spec: one record per person tied to a company with no duplicates; a pipeline with stage, dollar value, and close date on every deal, totals by stage on one screen; an activity log that fills itself; a next action on every open deal, enforced; source on every lead and revenue by source. Stages, outcomes, offers, and numbers are Config rows so each signed client gets a duplicated base with integrator stages. The style guide tokens are used as on `/avmarketing/`, with a Charcoal Blue top bar for contrast and two muted colors added for motion only: sage `#566E58` up, brick `#8C5A55` down, always with a word or glyph.

**Why:** Jonathan chose Airtable as the store and "both" as the audience (Monarc now, clients later). A claude.ai artifact cannot reach Airtable (sandbox blocks fetch; its connector bridge only reaches claude.ai connectors, and Airtable here is a `.mcp.json` server), so the page runs locally with the token in the Python process. Airtable Free caps a base at 1,000 records and the workspace at about 1,000 API calls a month, so the design is local-first: the 887-row queue and the dial log live on disk, a Company record exists only once touched, no-contact dials do not create Activities, the base is cached, and offline writes replay from an outbox.

**Supersedes:** the 2026-09-11 planned base layout (Campaigns, Integrators, Dials, Pipeline, Leads, Money). Campaigns became Sources rows; Dials became the local log plus Activities; Pipeline became Deals.

**Alternatives considered:** a claude.ai artifact with its shared database (works today, but the store would not be Airtable); Airtable Interface Designer (cannot follow the style guide); a local HTML file with JSON (no shared store, nothing for the AIOS to write into).

**Owner:** Jonathan Beach. Pending: the personal access token in `secrets.env`, and confirming the Airtable plan. Phone calls are the one activity still typed; a VoIP number is the future fix.

## 2026-09-15 - The Pilot Service Agreement is the offer

**Decision:** Jonathan, 2026-09-15: "This retainer setup is the new offer locked." The offer is the Pilot Service Agreement (`Downloads\Monarc_Pilot_Service_Agreement.docx`, DocuSeal template 5897064): a 60-day Google Ads pilot at $2,000 per month management with a $1,000 per month Monarc match credited against it, $2,000 per month ad spend paid by the client to Google ($3,000 a month all in, $6,000 for the pilot), then month to month at $2,500 management plus $2,000 minimum ad spend with 30 days notice. Onboarding fee $3,000, waived for signatures on or before September 30, 2026. Access within 5 business days starts the clock. Maryland law. `context/offer.md` rewritten; the Level 1 / Level 2 page is kept there as history. `references/mycopy.md` price and pilot blocks updated. CRM Config `offers` row updated.

**Why:** It is the document Jonathan is putting in front of Chisholm Security today, with his own math (16 leads at $125, one install covers the month). One document, one set of numbers, on the call, in the email, and in the CRM.

**Supersedes:** the 2026-09-07 two-tier offer (Level 1 $2,500, Level 2 $4,500, no setup fee, $1,000 total match) and the 2026-09-08 two-tier decision for the site.

**Open:** First Responder is not in the agreement (keep as an add-on or drop). What the waiver line becomes on October 1.

**Owner:** Jonathan Beach.

## 2026-09-15 - CRM Home: six acquisition channels, each with a workspace; UTMs on every controlled link

**Decision:** Jonathan named the channels worth his time: Cold call, Google Ads, Google Organic, Email, LinkedIn, Meta Ads. The CRM opens on a Home of six cards, one per channel, each a door into its own workspace. Cold call opens the call list. Google Ads opens campaigns with their keywords and landing pages and shows attribution: which keyword and page produced which lead, booked call, and signed deal. The other four hold campaigns and leads until their workflow is defined. Four tables carry it (Campaigns, Keywords, Landing pages, Leads); a lead saved with its UTM string is attributed by the server. Every paid link and every link Monarc controls carries utm_source, utm_medium, utm_campaign, utm_term, utm_content, and the click id; the Google Ads tracking template is in `references/attribution.md`. Warm, referral, rep, inbound, and content stay as sources on deals but are not channel cards.

**Why:** Job five of the CRM in Jonathan's words: source on every lead, revenue by source, so spend turns into "that keyword produced that job." Without UTMs a form fill says nothing about where it came from.

**Owner:** Jonathan Beach. His steps: set the tracking template in Google Ads; the /book form reads the parameters on his go.

## 2026-09-16 - Papers in records/, the money book in Airtable

**Decision:** Two systems, kept apart. The papers (Articles, EIN letter, operating agreement, yearly filings, tax, signed contracts, insurance, bank statements) live in `records/` at the repo root; git tracks only the index, `records/README.md`, which also carries the dates that bite (Maryland Annual Report April 15, quarterly estimates, 1099s January 31). No EIN, account number, or card number is ever written into a tracked file or into chat. The money book is a second Airtable base, "Monarc Books" (Accounts, Transactions, Invoices, Months), separate from the CRM base so the CRM's record cap stays untouched. `scripts/books.py` pulls Stripe, loads the monthly bank CSV, and runs month end; the CRM gets a Money page. Stripe stays the card processor and invoicing tool.

**Why:** Jonathan asked where the founding papers go and how businesses do this, then asked why bookkeeping is not just an Airtable base. At five clients and a few invoices a month, Airtable holds every dollar with a receipt on the row and the AIOS reads and writes it; what it lacks (a bank feed, double-entry balances) is not worth $35 a month yet. The repo is on GitHub, so anything identifying stays out of git.

**Alternatives considered:** QuickBooks Online now (has the API Jonathan asked about; deferred to about fifteen clients or the first tax preparer request; the Transactions export is the migration); Wave (free, but its API covers only invoices and customers and is in maintenance mode); keeping papers in Downloads (unfindable, unbacked).

**Owner:** Jonathan Beach. His steps: open the business bank account, add the Books base to the Airtable token, write the two money rules, export the first bank CSV at month end.

## 2026-09-23 - /avmarketing rebuilt as the AV contractor booking page

**Decision:** Jonathan's brief: a headline with a booking button, an estate photo in the hero, a short About from the business context, an "Our impact" block showing the jobs, and a second booking button, shaped in the live preview loop. Four calls he made on the rules the brief crossed: (1) the page is `/avmarketing/`, and the button opens the four-step booking popup already built on the homepage (first name, email, phone, time), so attribution and the Meet invite keep working; (2) Copy 6 changes site-wide to "Book an appointment", the homepage keeps "Book a 15 minute call" until he asks; (3) the h1 is "Want more quality leads as an AV contractor?", his line cut to the 8 word cap, sub "Schedule an appointment with our team."; (4) the timer bar, the "One integrator per metro" scarcity claim, and the metro and team size steps are dropped. Style Guide section 6 rules 2, 5, 6, 7, 8, and 10 rewritten and dated; `drift.py` checks the new label and two buttons in ad mode; the Section Spec gains an "Ad page /avmarketing/" block. Standing rule added to `CLAUDE.md` and `AGENTS.md`: read the Style Guide, then the Section Spec, before touching any monarcbuild.com page. Built local, not pushed.

**Why:** The LinkedIn application funnel never went live with its backend (`BOOKING_URL` empty, timer at a placeholder deadline). A simpler ask, one photo and one question, is what Jonathan wants to test first. Keeping the popup rather than a bare calendar link keeps the ad set on every booking.

**Supersedes:** the 2026-09-13 ad page decision on the timer and scarcity, and the 2026-09-14 five-step funnel (metro as the call to action, team size). The popup pattern (2026-09-14) and the Apps Script booking backend stand.

**Alternatives considered:** a plain link to the Google Calendar appointment schedule (drops the UTMs); a new page at a new path (leaves a dead funnel live); keeping the timer only.

**Owner:** Jonathan Beach. His steps: approve the renders, then say push. Open: relabel the homepage button, set `BOOKING_URL` and `BOOKING_TOKEN` before the ad flight.


## 2026-09-23 - Dictation Sheet: pickup lines join the line before, VexFlow stays 3.0.9, sweep fixes I to IV shipped

**Decision:** Three calls Jonathan made on the ten-agent sweep of the Dictation Sheet (`projects/dictation-sheet/sweep-2026-09-23/analysis.md`): (1) a lyric line that starts inside a bar the line before still uses joins that line at its true slots, so the sheet's lines no longer match the lyric lines one to one; (2) dots and ties are fixed on the VexFlow 3.0.9 build the page really runs, the upgrade to a real 4.x build waits; (3) this round ships groups I to IV (Place words honesty, notation, placement, playhead) plus the cheap safety fixes, about 20 of the 32 items. Shipped the same day; what went in and what is left is in `sweep-2026-09-23/fixes-2026-09-23.md`.

**Why:** Merging was tested at 479 of 480 syllables within a sixteenth on Blurry; letting a line start mid-bar would touch bar counting, drawing, chips, exports and undo. The 3.0.9 fix is small and safe and keeps the engine that has drawn everything so far. The deeper analysis rework (onset picker, tempo aliasing, splitter rules) needs more retesting than one round allows.

**Alternatives considered:** a sheet model where two lines share a bar; keeping the line but not packing it (still plays late); loading the genuine 4.2.5 from jsdelivr now; shipping all seven groups.

**Owner:** Jonathan Beach. His steps: open the desktop copy, put Blurry on a fresh sheet with the listener on, and say whether the merged chorus lines read well enough or the mid-bar model is worth its cost.

## 2026-09-23 - /avmarketing round 2: calendar picker, booking drip, conversion sections, team, styling

**Decision:** On the round-1 render Jonathan asked for the calendar back, the headline up by the logo, the estate photo out of the hero, a team block, a brainstorm of conversion sections, then styling and scroll ideas. His calls: (1) h1 "Book more quality leads as an AV contractor."; (2) the popup's time step becomes an in-page calendar in the palette, the last button reads "Confirm appointment", and on confirm the Apps Script books the event, writes a "Monarc bookings" sheet row, emails Jonathan the details and Meet link, emails the prospect a confirmation, and queues an enrichment email and a reminder from one 15-minute trigger (`templates/booking-drip.md`, drafts until he approves); (3) the estate photo heads a team block: Jonathan Beach, Head consultant; Patrick Beach, Account management; Riley Palmer, Account manager, placeholders until headshots; (4) sections picked from the brainstorm: proof stack (replaces the tiles), the audit block, fit (for and not for), the math without an ad spend figure, a seven-service block (his six plus Local SEO and Google Business Profile as the assistant's seventh, his to cut), brands strip, four-question FAQ as accordions, floating pill; (5) styling: labels with hairline rules, h1 64px, 72px lining figures, button hover and focus states, numbered services, Sand and White photo frames; (6) scroll: reveal once on scroll, count-up figures (against the assistant's advice), no pill animation, no progress line. Style Guide Type 5 and 6, Copy 6, section 6 rules 1, 2, 3, 7, 8, 10, 11 and new 12 to 15; `drift.py` allows "Confirm appointment" and counts three buttons on an ad page; Section Spec ad page table rewritten; `references/apps-script-booking.md` rewritten; `context/about-business.md` names Patrick's role and Riley; `context/offer.md` notes the services beyond the Pilot Agreement. Brainstorm and picks: `brainstorms/2026-09-23-avmarketing-conversion.md`. Built local, not pushed; the script is written, not deployed.

**Why:** One calendar in the page beats a link out to Google's booking page: the prospect never leaves, the ad set stays attached, and the drip starts the moment they confirm. The sections answer the four things a cold LinkedIn click asks in order: what do I get, can you prove it, is this for me, what does it cost. The team block answers "who am I talking to" now that the page names a team.

**Supersedes:** the round-1 entry of the same day on the hero photo, the Our impact tiles, the two-button count, and the plain time list. The 2026-09-14 rule that the script never sends mail.

**Alternatives considered:** buttons straight to the Google Calendar booking page (no attribution, no drip); one trigger per booking (Apps Script caps at 20); Meta-style FAQ with terms printed (kept off the page per 6.7); a split hero with the photo (photo moved to the team block instead).

**Owner:** Jonathan Beach. His steps: approve the renders and the four email drafts; send headshots; say whether Patrick and Riley are staff or contractors; run the Apps Script setup (about 15 minutes) and paste `BOOKING_URL` and `BOOKING_TOKEN`; then say push. Open: reconcile the seven services with the Pilot Agreement; relabel the homepage button.

## 2026-09-23 - /av_marketing/ live; the old /avmarketing/ funnel stays up for now

**Decision:** Jonathan: "Upload this to the public html with the url slug av_marketing." The round-2 page went live at https://monarcbuild.com/av_marketing/ as a new folder, one file pushed through `scripts/site_sync.py`, verified live (200, UTF-8, noindex, the three buttons, the calendar step). The new slug means the 2026-09-14 funnel at `/avmarketing/` is untouched and still live; the mirror's `avmarketing/index.html` was pulled back from the server so the mirror matches. The loop's edits earlier the same day (the $500k line out, one audit line, the brands ticker, the first-page ranking claim, flip cards, $69k and $51k, the hero on the colonial house) are in the live file. Live with placeholders: no `BOOKING_URL`, no `AIRTABLE_TOKEN`, drip not deployed, placeholder photos, formsubmit activation unconfirmed.

**Why:** A new slug is the safe push: nothing on the server is overwritten, and the LinkedIn campaign can point at the new URL whenever Jonathan flips it. The "pull before push" rule was skipped on purpose: a full pull would overwrite the unpushed homepage draft in the mirror, and a new folder cannot collide with anything live.

**Supersedes:** nothing. The 2026-09-14 page stands until Jonathan retires it or asks for a 301 from `/avmarketing/` to `/av_marketing/` that carries the query string.

**Owner:** Jonathan Beach. His steps: point the LinkedIn ad at `https://monarcbuild.com/av_marketing/` with the trailing slash; deploy the Apps Script and paste the URL and token; set `AIRTABLE_TOKEN`; decide the old funnel's fate.

## 2026-09-23 - Old /avmarketing/ removed; 301 to /av_marketing/; calendar live; booking emails set

**Decision:** Later the same day. (1) Jonathan: "get rid of the old avmarketing url." The 2026-09-14 funnel was deleted from the server after a 301 with the query string kept went into `.htaccess`, so any link or ad still pointing at `/avmarketing/` lands on the new page with its UTMs; last copy in `archives/site-avmarketing-2026-09-23/`. (2) Jonathan deployed the Apps Script from `sumreat17@gmail.com`; the calendar step on `/av_marketing/` is live and a test booking landed with every field. He wants the event and the emails under `jonathan@monarcbuild.com`, which he already has as a Google account with no Gmail; the move (share the calendar, redo the project there, redeploy, rewire) is his next step, with one open question: whether that account can send mail. (3) The booking emails are three, by his spec: a confirmation with the Meet link, the time, and who they speak with; a reminder one hour before the call; his notification with the prospect's details. The "Before our call" email is switched off in the script. The queue runs every five minutes. (4) The popup asks how many technicians are on the team before the calendar. (5) No callback-time promise anywhere on a page (Copy 9), enforced by drift.

**Why:** One live address, one funnel, one set of numbers. A 301 that carries the query string costs nothing and keeps the attribution the whole build was for. The reminder an hour out is what he asked for; the enrichment email was mine, not his.

**Owner:** Jonathan Beach. His steps: finish the move to the `jonathan@monarcbuild.com` account and hand over the new address; set `AIRTABLE_TOKEN` for the CRM; delete today's test event; read the three emails.

## 2026-09-23 - CRM styled like a Microsoft product and reorganized around a left rail

**Decision:** Jonathan: "style it like a Microsoft product" and "the CRM is organized pretty horribly." The dashboard in `projects/crm/` now uses the Fluent look (Segoe UI, semibold headings, brand blue `#0F6CBD` on a neutral canvas, white cards with soft shadows, 4px controls, 8px cards); every class from the first build is kept, so the views needed no restyle of their own. Four picks on the organization, all the recommended ones: a left rail in three groups, Work (Today, Pipeline, Leads), Records (Companies, Activity), Performance (Channels, Reports, Money), Settings at the foot; Today as the first screen and the daily cockpit (goal line, next actions due or overdue from the pipeline, calls booked for today and tomorrow, new leads, the dial list), with Home removed; Channels showing live sources only with the rest behind "Show all sources"; a new Leads view, newest first, with status chips and row buttons Called, Booked, Dead ("Called" stamps First call at). Two fields added to the Leads table in Airtable, `Call at` and `Technicians`, written by the booking script. Two server fixes: the lead save path no longer overwrites When or re-attributes the lead on a status update, and the default port moved from 8765 (the Dictation Sheet's) to 8770.

**Why:** The old Home was a scoreboard of zeros that repeated Channels; nine flat tabs hid the two things that matter each day, the dial list and the overdue next steps; and the bookings the new page sends had nowhere to land.

**Owner:** Jonathan Beach. His steps: tick Active on the LinkedIn source when the ad goes live so it surfaces on Channels; set `AIRTABLE_TOKEN` in the booking script so leads arrive.

**Amended the same evening:** Jonathan: "Remove the leads section, this kind of just exists as the pipeline." The Leads view came off the rail and out of the code. In its place the server turns every lead without a deal into one on the board whenever the pipeline is read: a Booked lead lands at the Booked stage with "Hold the call" dated the call day, a form fill with no time lands at Contacted with "Reply with two times" due today; company and contact come from the existing key rules, the deal carries the lead's source, and a Meeting activity marks the booking. The Leads table stays as the attribution record behind the channel numbers. Work is now Today and Pipeline.

**Amended again the same evening, Channels:** Jonathan: "These are the only channels right now: Google, cold call, and LinkedIn. They should all be their respective colors with identifiable logos and show the KPIs and activity for each. I want to see output variables, campaign status, and when I click on the card it reveals the campaigns in depth." The Channels page is now three brand cards in a row, Google Ads (the four-color mark, Google blue), Cold call (a handset on Monarc's Charcoal Blue), LinkedIn (the "in" mark on LinkedIn blue), each with a colored top edge, a status tag (Live, Planned, Paused, Not live), a status line from its campaigns, an Inputs row (spend, impressions, clicks, CTR, CPC; for cold call dials, connects, connect rate, booked, booking rate), an Outputs row (leads and cost per lead, booked and cost per booked, won and cost per won, revenue), and the last three things that happened. A click opens the channel workspace, whose campaign table now carries impressions, clicks, CTR, and CPC beside spend, leads, booked, sold, and won. The other eight sources sit behind "Show all sources." The totals strip sums the three channels only. Impressions, clicks, and spend are typed on each campaign from the ad platform until an API fills them.

**Amended again, Today:** Jonathan: "Today should show me my calendar, a mix of the meetings I have and the tasks I need to get done in the day." Today now lays the day out in time order: meetings from Google Calendar (the business calendar and the account's own, read through a new `agenda` action on the booking script, since the CRM has no Google login of its own; the local server fetches and caches it five minutes), the dial hour with its count, and, when the calendar is offline, booked calls from the leads; a Join button on any meeting with a Meet link; tomorrow's meetings under it. Beside it, To do: deal next actions due or overdue (click opens the deal), then the open boxes from `tasks.md` (Week 0 and Weekly tiers first) with a Done button that checks the box in the file with the date. The dial list stays below. Until the script's new version is published, the day panel says so and shows the rest.

## 2026-09-24 - Channels wired one at a time, Google Analytics first

**Decision:** Jonathan: "Lets hook these up one at a time." The order is Google Analytics, then the LinkedIn Insight Tag on the pages that lack it, then the Google Ads tracking template, then the LinkedIn ad link. Each step ends with a push on his go and a read-back of the live pages. The full list, with what is live, is `references/channel-connections.md`.

**Google Analytics (done):** Jonathan created the GA4 property and gave the measurement id `G-JQ977C0MY7`. One config line sits next to the Google Ads tag on all eight pages, and a `book_appointment` event fires on the sent state of the ad page, the homepage popup, and `/book/`. While gating that event, the `/book/` Google Ads "lead form" conversion was found firing on every view of the page; it now fires only on the sent state. Pushed on his go just after midnight, read back on every page.

**Why the mirror was refreshed:** the pull before the push showed the live pages carry the LinkedIn Insight Tag (partner id 9685362) on about, book, how-it-works, permit-intelligence, and territories, placed by Jonathan on the server, and that the local copies of those pages carried instead a `/assets/site.css` link that was never pushed (the file 404s live). Live is the source of truth, so the six mirror pages were refreshed from live plus the tag; the old copies sit in `archives/site-mirror-2026-09-23/`. The homepage got the tag on its live version through a direct upload; the unpushed homepage draft stayed local and carries the tag too.

**Site cut to four pages, same night:** Jonathan, after seeing the page map: "results can go, how it works can go, territories can go, permit intelligence can go and the 301 can go." The four Higgsfield-era pages carried the old permit-intelligence offer. Removed from the server and the mirror (archived in `archives/site-pages-removed-2026-09-24/`), the `/avmarketing` redirect dropped from `.htaccess`, the dead links pulled out of the homepage, about, and book, and `llms.txt` trimmed to the four pages that stay. What is live: the homepage, about, book, and the ad page. Flagged: an ad still pointing at `/avmarketing/` now lands on a 404, and the homepage still funnels to the `/book/` email form until the homepage draft is approved.

**Privacy page and the second push, same night:** asked whether the site was ready for Google Ads, the answer was "nearly": Google Ads requires a privacy policy on any page that collects a name, email, or phone, and the site had none. Jonathan: "write a privacy policy page." Written at `/privacy/` in the ad page's type and palette, eight short sections, dated, `noindex`; a "legal" page type added to `drift.py` so the homepage anchor and button checks skip it; Style Guide section 7 records the pattern and rule 6.1 allows the one footer link on the ad page. Pushed on his go with the Privacy footer links, the LinkedIn Insight Tag on the homepage and the ad page (the two pages that lacked it), and two `.htaccess` rules that send `www.` and `/index.html` addresses to the bare folder address, so the tag list Jonathan pasted ("untag any unnecessary") stops showing the same page twice. Entries in that list cannot be removed by hand; the removed pages drop off on their own, and the old Higgsfield copy of the site, still published with the Google Ads tag on its book page, is Jonathan's to unpublish.

**Google Ads through the CRM (asked, not started):** Jonathan: "Can we integrate a google ads API to control ads through the CRM as well." Yes, in two halves, read then control, scoped in `references/channel-connections.md`. Blocked on his side until a Manager account, a developer token with Basic access, and an OAuth client exist.

**Electricians, a second vertical (2026-09-24, after midnight):** Jonathan: "Build me a list of electricians just like the list for integrators using the Places API key and tell me what my spend will be for it." Priced by dry run at $39 to $116 for 1,102 searches over the same 213-location grid (six phrases: electrician, electrical contractor, residential electrician, lighting installation electrician, EV charger installation, home generator installation), about 20,000 companies; run on his "go" with a $120 cap once the Places key answered again (a console change on his side had it refusing for a few minutes; the sweep script now waits out a stray 403). Then: "Lump companies by vertical so separate this list in the CRM from the integrators." Airtable Companies got a Vertical single select (Integrator, Electrician; the twelve existing rows set to Integrator). The CRM got a switch under the brand mark, one call list per vertical from its own CSV (`verticals` in `config.json`), the vertical stamped on every company the dial log creates and carried in the dial log itself, and Today, Companies, and Pipeline filtered by the pick. `scripts/seed_to_list.py` turns a sweep workbook into a call list without the Opus pass (one row per company, most-reviewed listing wins, DMV dropped like the integrator list unless `--keep-dmv`). Not yet: Channels and Reports by vertical, and the API spend itself is not on the Money page (a spend ledger was offered).

**The cold caller's dropdown (same hour):** Jonathan: "We need an outcome dropdown for my cold call guy to fill out." Each row on Today's dial list now ends in an Outcome dropdown with the eight outcomes from the config. A no-contact pick (No answer, Voicemail, Bad number) logs the dial at once, with the vertical, and the row drops off the day's list. A live-conversation pick (owner, non-owner, callback, booked, not interested) opens the dial screen with that outcome already chosen, so the caller only fills the line it died on and the next step; the rules there did not loosen. The "Log dial" button went away; the row click still opens the company. The caller can only use this on a machine that runs the CRM, which is the repo-and-launcher step from the same night.

**The sweep landed (about 2:30 pm):** 1,838 pages, $64.33, 16,148 electrician listings, 8,636 unique domains; the call list came to 7,900 companies with a phone (1,986 integrator rows the sweep merges in for dedupe were cut, 1,186 had no phone, 730 sit in DC, MD, VA). Lower than the 20,000 estimated: the six phrases overlapped more than the integrator ones and most searches stopped early. Jonathan: "When this is done package it and send it to riley@monarcbuild.com as a zip file" and "Send the seed list to Patrick at Monarch. Build as a zip file." Both zips (call list CSV or workbooks, plus a README) sit in `projects/outreach/`, and both emails sit in Proton Drafts in Jonathan's register with the zip attached; the AIOS never sends, so Jonathan sends each with one click. Sending from the AIOS would need SMTP through Bridge added to `scripts/proton_mail.py`, offered, not built. Jonathan sent Riley's himself within the hour.

**Patrick's template (same afternoon):** Patrick shared a Google Sheet, "original", holding the LinkedIn company-list header (companyname, companywebsite, companyemaildomain, linkedincompanypageurl, stocksymbol, industry, city, state, companycountry, zipcode); the AIOS could not open it (shared with jonathan@monarcbuild.com only, the Drive connector runs as sumreat17), so Jonathan pasted the header. It is the header the 2026-09-13 upload already used. Jonathan: "make the seed list as a draft again for patrick with this updated format." New `scripts/seed_to_linkedin.py` writes a sweep workbook in that template, one row per website domain, US states only; run on the integrator seed with his own list folded in: 7,837 companies. The workbook draft to Patrick was removed from Drafts and replaced with the CSV zip (181 KB) under "Integrator seed list, LinkedIn format".

**Every column (Jonathan: "i need the company name, company website, company email domain, linkedin company page url, stock symbol, industry, city, state, and zip code"):** name, website, email domain, city, state, zip were already on every row. Stock symbol stays blank: private companies. Industry is set to "Consumer Electronics" on every row, the label most integrators carry on LinkedIn; a weak signal, blank is allowed. The LinkedIn page URL came from the 2026-09-14 website crawl (609 of 2,254 sites linked their page): 526 rows in the file. To fill the rest for free, `meta_seed.py` got `--raw` (crawl a whole sweep, no tiers) and `--reuse-cache` (skip domains an earlier crawl fetched), and the crawl of the remaining 5,588 integrator sites started at once (about two hours, 24 threads, no paid calls); when it lands, the CSV is rebuilt with both crawls and the draft replaced again. Clay was discussed and parked: the list is usable for a LinkedIn company audience and for cold calling without it; Clay earns its fee only for owner emails, a people audience, or a Meta list, and then on the tiered cut, not the whole pile.

**Ten crawlers (Jonathan: "deploy 10 sub agents across this list to increase the speed"):** agents do not speed a network crawl, parallel crawlers do. `meta_seed.py` got `--shard i/n` (each copy crawls one slice into its own cache file, then a plain run with every shard file on `--reuse-cache` merges and writes the outputs). Ten copies ran side by side, 240 fetches in flight, and finished the 5,129 remaining sites in about 45 minutes against the single crawler's 35 a minute. The machine was sluggish meanwhile; simple shell commands timed out. Result for the integrator sweep, all 7,842 sites read: LinkedIn company page on 1,275 rows of Patrick's CSV (was 526), and as a by-product `meta-seed-2026-09-24-integrators.xlsx` with an owner name and email for 762 companies, a named email for 685 more, a generic address for 1,210, phone only for 5,098; the Meta customer-list CSVs for the whole sweep sit next to it. Patrick's draft replaced a third time. Riley, meanwhile: "convert rileys list into a csv and send it as a draft," done as the electricians in the LinkedIn template, 6,913 companies, industry Construction, CSV attached (not zipped), no crawl yet on those sites.

**What the CRM does and does not read:** Jonathan asked whether the CRM now reads Google Analytics. It does not. Analytics counts visits and where they came from; the CRM knows a person only when they book or fill a form. Joining the two (visits and clicks per channel beside the bookings) is a later wire through Google's reporting interface, after the tag has a week of data.

## 2026-09-24 - Onboarding questionnaire and asset-request email, five trades

**Decision:** Jonathan: "We are going to make an onboarding questionnaire for various home service businesses being roofing, electrician, hvac, plumbing, av contractor. Lets just start with this. It will need to collect service areas, brands they carry, their primary offerings, as well as an email requesting the basic stuff necessary for rebuilding their website like installation media, their logo, the team photos, license #, insurance, anything needed for transfering the website." Two templates at repo root: `templates/onboarding-questionnaire.md` (15 shared items plus a four-item block per trade; the client fills it before the kickoff) and `templates/asset-request-email.md` (one email, a 14-item list under the signature, seven items block the build). Trade maps in `context/trades/{key}.md` for roofing, electrician, hvac, plumbing, drafted by the AIOS and marked so until Jonathan confirms each; integrator points at `context/icp-brands.md`. AV contractor is the existing integrator vertical. Five trade keys reserved (integrator, electrician, hvac, plumbing, roofing) so the CRM's `verticals` config lines up later without renaming. The kickoff skill sends the questionnaire with the invite and the asset email the next business day; `client-brief.md` gained "Warranty and financing" and "Credentials on the page" lines so every answer has a home.

**Why:** the kickoff bank is a 45 minute call script written for integrators. A contractor answers 19 items in their own words before the call, and the call spends its time on decisions (floor, lead handling, access, money, VSL). Files get their own email with one job because photos are the long pole of the 14 day build. Markdown templates cost nothing and the content is needed under any delivery format.

**Alternatives considered:** a client-fills page on monarcbuild.com through the site's form-to-email path; an Airtable form in the CRM base. Both deferred; either can be built from the templates.

**Flag, not resolved:** the Pilot Service Agreement covers Google Ads management only; the ad page advertises website build and design; the asset email assumes a rebuild. Reconcile before the first client receives it (`context/offer.md`, internal notes).

**Owner:** Jonathan Beach. His steps: read both templates; strike and add in the four trade files; decide the rebuild scope in the agreement.

## 2026-09-24 - Pipeline process page, one section per stage

**Decision:** Jonathan: "Add this to the documents under onboarding for the pipeline process." No such page existed (checked the repo, the Airtable CRM base, Google Drive, and Claude Docs), so `references/pipeline-process.md` was created: one section per stage from Cold to Day 60, each with what happens, the documents, scripts, and skills it uses, and what moves it on. Onboarding lists the client questionnaire, the asset-request email, the trade maps, and the kickoff skill files in sequence. Linked from the `references/` line in CLAUDE.md and AGENTS.md.

**Why:** the stages lived in three places (the CRM config, the roadmap, the kickoff skill) with no page saying which document belongs to which stage. One page keeps a new template from being filed nowhere.

**Alternatives considered:** a Google Drive Onboarding folder next to the June pipeline workbook; a Documents table in the CRM base. Jonathan picked the repo page.

**Owner:** Jonathan Beach. Rule for the AIOS: when a template, script, or skill is added or moved, add or move its line on that page in the same edit.


## 2026-09-24 - Dictation Sheet: cut down to the one path

**Decision:** Jonathan: the app has too many things going on. The one path is: paste the song and its words, the words are split into syllables from the word list, each syllable gets a note where it is sung, with its start and its end. Everything else on the screen that moved words or bar 1 by hand is taken out: Tap words, Mark bar 1, the bar-1 box, Detect, Lock, Listen, Preview, the Line up tool (built 2026-09-23), Beat here, count-in, Click plays, Practice, the Tones panel, the Mic, the loop lane. Hearing the song and following its beats still run on their own inside Place words. Left: link the song, paste the words, Place words, Play and Stop, click a bar to start there, loops, Move, Edit, Cut, Undo, Save, the views.

**Why:** With one path there is one thing to get right and one thing to test. The extra tools fought each other, and on the real song Place words was still not close; the first job now is to see what the app heard on his machine (a saved sheet after one Place words run on Blurry).

**Alternatives considered:** keeping the tools behind an "advanced" switch (still there to trip over); keeping the Line up tool as the fix-up path (a second path to the same result).

**Owner:** Jonathan Beach. His steps: open the desktop copy, put Blurry on a fresh sheet, press Place words after the song has played through once, then File, Save as, into the Dictation Sheets folder, and say whether the words are early or late.


## 2026-09-24 - Dictation Sheet: the words fitted by a speech model, not by loudness

**Decision:** Jonathan asked whether an existing solution could be copied, and said go. Place words now fits the known words to the song's sound with torchaudio's wav2vec2 speech model and its forced alignment, cuts words into syllables with the CMU pronouncing dictionary and the pyphen hyphenation list, and reads the beats with librosa, all inside `align.py` run by the desktop copy's local server. An attached file is fitted at once; a Spotify song plays through first while the server records the sound card, in memory only. The hand-made loudness reading stays only as the fallback where the tools are missing (the claude.ai artifact).

**Why:** The loudness reading never heard the words, only bumps in volume, and on the real song it was still off after every fix. Forced alignment listens for the sounds of the words themselves; on a spoken test every syllable landed within a sixteenth.

**Alternatives considered:** WhisperX (heavier: needs pyannote and ctranslate2), the Montreal Forced Aligner (conda only), madmom for beats (does not build on Python 3.13), Demucs to pull the singer out first (not yet; add if the fit struggles on the mix).

## 2026-09-25 - Monarc's own Google Ads: six themed service pages, one campaign plan, a theme layer on the style guide

**Decision:** Jonathan: "We are going to plan out a google ads campaign that is going to run ontop of these landing pages," five service lines (website design, managed Google Ads, email marketing, Meta ads, AI business automation), later a sixth ("We are also going to build an SEO page with these core parts. GMBP, Organic Search, AEO, Copywriting"). Settled in two interviews the same day (`brainstorms/2026-09-25-google-ads-campaign.md`, `brainstorms/2026-09-25-google-ads-pages.md`, 47 questions on the pages alone) and an approved plan, working copy in `projects/google-ads/README.md`:

- Audience all five trades at once. Budget $1,500 to $4,000 a month, planned at $3,000: two funded campaigns (Google Ads management, website build) plus one rotating 30-day test slot (SEO first, then email, Facebook, automation). Geo the 213-location metro seed, "Presence" only. Keywords: AIOS drafts, Jonathan validates in Keyword Planner. Reading level grade 8, brand names and trade terms exempt.
- Every page books the same 15-minute call; the service is scoped and priced on the call; the agreement is amended per client. "Meta Ads" is built as `/facebook-ads/` because searchers type "facebook."
- AI Business Automation means time back for the owner: proposals, email automation, lead follow-up with missed-call text-back, invoicing, bookkeeping.
- Each page in its own style: "My spacing rules and ratios should remain the same but as far as color and typography I want it to match the channel that it is targetted at." The Style Guide now has two layers: invariants (layout, spacing, ratios, contrast, copy caps, ad-page bones, media honesty) and a theme per page (`projects/Landing Page Build/themes/*.json`; `drift.py` reads the page's `mb-theme`). Six themes: google, editorial, saas, commercial, social, time; the house theme keeps the homepage and `/av_marketing/`.
- Less is more: a six-block skeleton on every page (split hero with a 3D cartoonish render as a visual metaphor, four static cards, one proof or walk-through block, a Works-for and Not-for block in green and red, three FAQs, final ask). Two button labels per page, the pill on the hero label. v2 blocks only when day 30 asks.
- Generated images: "I want images generated for each website using google nano bananna or whatever the leading image generation is right now." Nano Banana Pro on the connected generator; six hero renders, eight card renders; all six style tiles approved before any page is built. No stock anywhere (a licensed putt photo was chosen and then superseded the same day).
- The Google page reads as Google through Roboto, the four colors, Material icons, and a search bar, never the wordmark; no Meta, Facebook, or Instagram logo on the Facebook page.

**Why:** Outreach eats the week; paid search runs while Jonathan dials. The offer covers Google Ads only, so the call carries scope. Themed pages double as the design portfolio the website page shows. Head terms are agency-dominated at $20 to $60 a click, so the structure bids by trade, outcome, and pain with exact and phrase only until 30 conversions.

**Alternatives considered:** one campaign with five ad groups (too thin at $3,000 for learning); five funded campaigns (under a click a day each); national geo (Jonathan chose the seed; a widen option sits at day 30); one house style on every page (rejected: "showcase a breadth of styles"); Material Symbols and Lucide everywhere (Jonathan chose small 3D renders on the SEO and Facebook cards); a licensed stock photo for the putt (superseded by the render).

**Gates before spend:** billing fixed (a payment was declined 2026-09-01); one Primary conversion action with the homepage page-view label retired; final URL suffix and auto-tagging; each h1 mirrors its ad group's term; a test booking in Airtable with the UTM string. `projects/google-ads/tracking-checklist.md`.

**Owner:** Jonathan Beach. His steps: the tracking checklist's account items; six Keyword Planner runs; the SERP screenshots; confirm the three slugs, the automation tools, the footer phone, the call-script lines, and the image credit spend; approve six tiles, then six renders.

**Amended the same night (2026-09-25 into 26):** Jonathan confirmed the three slugs (`/seo/`, `/facebook-ads/`, `/ai-automation/`), the full-page build order (Google Ads, Website, SEO, Email, Facebook, Automation), and the image spend ("Run the full batch, 112 credits"). The batch ran: 56 generations, 24 hero and 32 card candidates, 112 credits (two jobs failed uncharged and were rerun). Every job came back labeled `nano_banana_2` although each request named `nano_banana_pro`; the charge matched the Pro preflight; logged in `projects/Landing Page Build/candidates/jobs-2026-09-25.json`. The seven style tiles are rendered with the candidates; the six page specs (`projects/Landing Page Build/pages/`) carry the block lists, the first copy drafts, and the recommended picks. The keyword research ran for all six lines (75 to 85 sourced rows each, no invented volumes) and merged into the keyword lists with paste files for the Planner. Two findings changed the plan: the Facebook page and ads say "Facebook ads" (owners and 44 of 72 ranking titles; Meta runs as a small test group), and most automation searches belong to software sellers with monthly prices, so that campaign bids only the back office, follow-up, and trade searches where done-for-you sellers rank.

**Render picks (2026-09-26):** Jonathan picked a hero render for every page and the SEO and Facebook card renders (`brainstorms/2026-09-25-google-ads-pages.md` Q51 to Q54); the picks are exported to `public_html/assets/generated/`. The automation house is a sticker (cut out on the generator, 1 credit). The email page's headline sits over the beige sky of the putt render instead of beside it. The citations logo strip is full color, a dated exception to Color 4 in Style Guide Media 6. Open: Facebook card 3 has no render. Next: Jonathan picks the renders and approves the tiles; then the pages are built in the confirmed order.

**`/google-ads/` live, then round 2 (2026-09-26):** pushed on Jonathan's go and read back. Round 2, his words: "Mobile headers and copy and the CTA should be centered. And make the google letters in the google colors. Fix the fishing line naturally fall into the water and have a salmon jumping out of the water," and "Have it be managed google ads." The h1 is now "Managed Google Ads for contractors." with "Google" set letter by letter in the four colors, a dated exception to Style Guide Media 7 (no wordmark): Roboto, inside the sentence, never alone or in an ad asset. Risk: a reviewer can read it as the wordmark; if a Misrepresentation disapproval comes, the letters go back to ink. The yellow letter measures 1.71:1 on white, under the 3:1 heading floor; open for Jonathan (AIOS recommends keeping it). The hero is an edit of his pick with the line on the water and a salmon jumping (four edits, 8 credits). Heads, hero copy, and buttons center under 768px on every service page. Built and rendered, not pushed.

**SEO hero redone (2026-09-26):** Jonathan: "The SEO page should be a map, pin icon, five star reviews, and jumbled up being lassoed by who looks like a contractor in the same cartoon style." After nine questions (brainstorm Q59 to Q67): a contractor in a hard hat on a clay town map hauls in the card 1 pin and a five-star review card on a tight rope; gold only on the stars; the folded map dropped because the town is the map; card 1 unchanged. Replaces the house mid-build. Four candidates, 8 credits; AIOS pick hero 6 in the page, pending his confirm. Not pushed. Jonathan picked hero 7 instead (sent the image back; matched by pixels).

**Three pages live, Services menu live (2026-09-26):** Jonathan: "go with posting the pages and sticking them under the services tab." `/google-ads/` round 2, `/website-build/`, and `/seo/` pushed and read back; the homepage, `/about/`, and `/book/` carry a Services dropdown listing the live pages. Details in `context/website.md`. The yellow Google letter stays `#FBBC04` (pushed as recommended; the contrast exception stands). The call-script lines for website build and SEO are still owed before ads point at those pages. Next: "render the other pages and get them ready for the next round of iteration": Email, Facebook, Automation.

**Email, Facebook, Automation built for the next round (2026-09-26):** all three built from their page specs, drift and readability clean, rendered at 1440 and 390 with the popup; not pushed. The email headline sits over the sky on desktop and stacks above the render under 1024px (the sky is too narrow there). Facebook card 3 carries an AIOS boomerang pick. Icons are the real Phosphor Bold and Lucide files. The button weight now comes from the theme (`--weight-button`, 600 on the slab and feed themes, 500 elsewhere). The new theme rules in `site.css` are local until these pages ship. Open for Jonathan per page spec: the tablet and phone email hero, card 3, the automation h1 line breaks, and "Bring nothing" against the FAQ lines that ask the reader to bring a number.

**The homepage becomes a search page; a butterfly mark (2026-09-26):** Jonathan: "The home page style should be rebuilt with the new copy, and google style guideline", then "we need a new favicon and logo to match the google app style". After a 22-question interview (`brainstorms/2026-09-26-homepage-google-rebuild.md`) and an approved plan: the homepage is a Google-style results page for "marketing for contractors", new copy built around the six service pages (the six as results with render thumbnails, the three jobs as local results, People also ask, a business panel, the h1 "Marketing for contractors. Built by installers." in a featured answer box), the popup on every button, and no page-view conversion (bookings only, tracking checklist item 4). The mark is a four-wing monarch butterfly in Monarc's own four hues (Jonathan picked candidate A of five), "Monarc Build" in Outfit 500 outlines beside it, on every page and as the favicon. Guard: Monarc Build where Google's logo would be; no Google logo, buttons, or product names as UI; no star ratings; the butterfly is mirror-symmetric so it reads as neither Google Photos' pinwheel nor Gmail's M. Style Guide: theme `search`, Layout 2 and Media 7 dated exceptions. Built and rendered, not pushed. **Round 2 (2026-09-27):** Jonathan: "It looking like google does not really work well. I think it should use that style but be a different theme." It read as a copy of Google (Q24). The layout stays; the page wears a theme of Monarc's own from the butterfly (`themes/monarc.json`: a warm off-white ground with white cards, Outfit headings, Inter body, the four hues as a band across the answer box), and "People also ask" became "Questions contractors ask" (Q25 to Q28). The `search` theme retired before it shipped. **Round 3 (the same day):** Jonathan: "I meant that it should use the google type and copy but not look like a google search results page." Round 2 had read him backwards. The homepage is now a Google product-site layout (Q29: "googles product site but make it include a who its for and who its not for section"): a centered hero with the search bar typing "marketing for contractors" (Q31), the six services as render cards, the three jobs as photo cards, Who it is for and Who it is not for, about, the questions, the closing ask; Roboto on white with the butterfly's four hues (Q30); the round 1 copy. `themes/monarc.json` redefined; rounds 1 and 2 never shipped. **Pushed 2026-09-27** on "go and make the favicon the butterfly": the homepage, the butterfly favicon, and the lockup on all eleven pages, read back live. `/av_marketing/` went up as the live page plus the mark only, so the unapproved logo strip in the mirror stays off the site. **Figures off, the same day:** Jonathan: "Take the number figures out of the jobs and replace the gerogian colonial picture to the interior photo", then "remove the figures and keep scope". No job shows its dollar value or the ad spend on any page (Style Guide Copy 4, amended); each shows its scope and where the lead came from; the "Page 1" and "#1 page" ranking claims stay. The homepage's Georgian card shows the interior rough-in, and the homepage gained the rolling citations strip under the hero ("Add the rolling citation banner with big brand names to the section right below the fold"). Built on the homepage, `/google-ads/`, `/seo/`, and `/av_marketing/`; not pushed. **About page and cross-links, the same day:** Jonathan: "Rebuild the about page with a more aligned offering and new style as used in the home page" and "Each page should also link internally to the other service pages." After six questions (`brainstorms/2026-09-27-about-page-rebuild.md`): `/about/` in the homepage's theme, his first-person story with the butterfly large beside it, the credentials, how we work in four steps, the six service cards, no years, no team block; each service page gains a quiet "Other services" row above its footer, a dated exception to Style Guide 6.1. Built, not pushed. **Pushed 2026-09-27** on "push the updates": the figures off on the homepage, `/google-ads/`, `/seo/`, and `/av_marketing/` (again from `staging/`), the Georgian interior, the citations strip, the new `/about/`, and the Other services rows, read back live (`context/website.md`). **Dots off, banner slower (the same day):** Jonathan: "remove this icon from these sections. also dont make the banner stop on hover but decrease speed by 20%". The four hue dots before every section label on the homepage and `/about/` came off (plain tracked caps; the one hue dot on each service card stays), and the citations banner runs 45 seconds a loop instead of 36 and keeps moving under the pointer (it stands still under reduced motion). Then "push and the few color icons should go from my page": asked which, he picked the Google-colored dots on `/google-ads/`, which came off its six labels too; the card dots, the `/about/` dots and rings, and the fit marks stay. **Pushed the same day** (`assets/site.css`, `/`, `/about/`, `/google-ads/`), read back identical; old live copies in `archives/site-updates-2026-09-27c/`.

**All six live (2026-09-26):** Jonathan: "Push them. Good enough." Email, Facebook, and Automation pushed as rendered, with card 3's boomerang; the Services menu lists all six; the website page's portfolio shows the other four. The open points above move to the next round, not blockers. Still before any ad spends: the call-script line per service, the automation tools named, and the tracking checklist.

**Owner:** Jonathan Beach. His steps: open the desktop copy from the shortcut, link Blurry (or attach its file), press Place words once, wait for the bottom bar to say it is done, and say how the words sit.


## 2026-09-24 - Dictation Sheet: write it down by hand first

**Decision:** Jonathan: he had been avoiding learning the skill by having the app do the placing. The tool's plain path is a note place: set the tempo, click a bar where a word is sung, type the word in the box that opens, Tab for the next. Built as the Add tool (W), a Start a line button on the empty sheet, and a new-line button at every line's end. Place words (the speech-model fit) stays as the other way in, not the main one.

**Why:** Placing the words himself is the skill he wants; the app should make each note one click and one word, then get out of the way. The automatic fit had already cost two days and was still not right on the real song.

**Owner:** Jonathan Beach. His steps: open the desktop copy, new sheet, set the tempo in the clock, Start a line, and write the first verse of Blurry by hand against the song.


## 2026-09-25 - Trade Call List: the Friday push is a campaign, and a campaign counts every dial

**Decision:** Friday 2026-09-25 is one push: fill seven "Marketing Consultation" slots on Monday 2026-09-28 from the trade call lists. Calls log in the Monarc CRM base under the Campaigns row "Trade Call List" (channel cold). While Config `active_campaign` names it, every dial becomes an Activities row linked to the campaign, no-answer included, and the campaign row sums Dials, Connects, and Booked. Connect rate = connects / dials. Booking rate = booked / connects, the same definition the Channels card uses. Booked of dials sits beside them so the cost of one meeting in dials is a glance. Today shows the same strip.

**Why:** A rate needs the misses counted, and the CRM's Free-plan design skipped the Activities row on a no-answer. Tying the exception to a named campaign keeps the record count down outside a push and makes the push's numbers honest inside it. Rows typed straight into Airtable count the same way, so the dashboard is not required.

**Alternatives considered:** Hand-kept Dials, Connects, Booked numbers on the campaign row (drift, no per-call evidence); counting dials from the local dial log only (misses anything typed into Airtable); a separate table for the push (a second place to look).

**Owner:** Jonathan Beach. His steps: run `python scripts/crm_server.py`, pick the outcome on each row, and read the strip on Today or the campaign row in Airtable at the end of the hour. The AIOS blanks `active_campaign` when he says the push is over.


## 2026-09-28 - The logo banner on every ad landing page, labeled "We list your business on"

**Decision:** Jonathan: "add the "We Work With" banner to each of the landing pages." After nine questions (`brainstorms/2026-09-28-landing-pages-banner.md`):
- The homepage's logo banner goes on the six service pages, right under the hero, and on `/av_marketing/` after its services (away from its brand-name bar).
- It ships now, a dated exception to Style Guide 6.16, which held the citations strip back until the day 30 review.
- The label is "We list your business on" on every page, the homepage included (was "National citations we work with").
- `/google-ads/` leaves out the Google logo and `/facebook-ads/` the Facebook logo.
- The logos stay full color on the dark `/ai-automation/`.
- `/google-ads/` runs 410 visible words against the 400 budget.

Built, rendered, not pushed.

**Why:**
- Trust at the fold on every page an ad points at; no ad had run yet, so the first version simply carries it.
- He wanted "We work with if it does not risk me getting striked". Google's Misrepresentation policy ("Unacceptable business practices") bans ads that "Make it seem like you're supported by another brand, organization or government entity when you're not", and the penalty is account suspension without warning. So the label says what Monarc does on those sites and claims no partnership, and the two pages that sell a platform's ads drop that platform's logo.

**Alternatives considered:**
- "We work with" (the partner read).
- Keeping "National citations we work with" (still "work with").
- Keeping all seven logos everywhere.
- White logos or a light strip on the dark page.
- Waiting for the day 30 review.
- Trimming `/google-ads/` to 400.

**Owner:** Jonathan Beach. His step: say go on the renders in `projects/Landing Page Build/renders/2026-09-28/`.


## 2026-09-29 - Monarc Studio: a desktop video editor for short-form, built on the laptop

**Decision:** Jonathan asked for a desktop shortcut that opens an editor that "functions like an Adobe product, but also looks like a Google product," then answered 44 grill questions (`brainstorms/2026-09-28-short-form-video-process.md`). Built and tested the same week:
- Monarc Studio: a local Python server plus one browser page in its own Edge window, Desktop shortcut "Monarc Studio". Premiere Pro behavior and shortcuts, the CRM's Material 3 look in dark.
- The full tool set ships at once (G29): ten tools, linked video/audio, keyframes on five settings with easing, overlays (images, video, text, shapes), audio fades, markers, cross dissolve and dip, autosave with 10-minute versions, undo/redo.
- Every edit is manual (G16, G17, G37). Automation stays in preparing files and in Claude's moment list.
- The transcript is made on the laptop (sherpa-onnx + Parakeet), not in the cloud: 4 hours in 16.8 minutes, free, prospects' voices stay on the machine.
- Find moments is one Claude Opus 5 call per recording that answers with transcript line numbers, mapped to times by the script, so no timestamp can be made up. First run $0.355.
- Exports go through a Python compositor (Pillow) that uses the preview's rules, with ffmpeg for decode, libass captions, the audio mix and the encode, so export matches preview (checked: positions within 2 px).
- Preview copies are made with libx264 on the CPU, not Quick Sync, which duplicated frames on some files.
- Posting stays in a third-party scheduler; the editor stops at `media/ready/`. No consent tools in the editor; that policy is Jonathan's (G22).

**Why:**
- Outreach eats the week; cold-call sessions are already being recorded, and each holds material for dozens of shorts.
- Local tools keep it free and private; the one paid step (moments) costs cents and runs only on a click after showing the price.
- A pure ffmpeg filter graph for export was harder to keep in step with the canvas preview; a shared compositor rule and shared easing test vectors keep them the same.

**Alternatives considered:**
- Separate open-source tools driven by hand (auto-editor, Shotcut). Jonathan wanted one simple tool.
- Groq hosted Whisper for the transcript (fast, $0.16 per 4 hours) and Postiz for posting. The laptop turned out fast enough, and posting went to a scheduler.
- A "super basic" editor first, phased. Jonathan chose everything at once.
- Automatic zooms, sound effects and pause/"um" removal. Jonathan chose manual.

**Owner:** Jonathan Beach. His steps: open the shortcut, cut his first shorts from the 2026-09-28 session, pick a scheduler, and settle the consent policy for prospects' voices before posting.

## 2026-09-30 - Monarc Studio captions colored by who is talking

**Decision:** Jonathan asked for his captions "always blue", women gatekeepers pink and men owners or service reps red, with the spoken word yellow. He then answered 14 grill questions (`brainstorms/2026-09-30-caption-colors-by-speaker.md`). Built and tested:
- **One palette for every short** (`projects/studio/config.json`): his words `#4D80E6` (the butterfly blue made lighter to read on a phone), his spoken word white; women `#FF5FA2`, men `#FF3B30`, their spoken word `#FFD400`. The per-short highlight picker is gone.
- **Gender decides the other side's color, not role.** Recorded voices follow the same rule. Captions stay in one spot, and a caption group breaks where the voice changes.
- **Voice split on the laptop.** A new prep step, "Voices", after the transcript: sherpa-onnx with pyannote segmentation 3.0 and WeSpeaker ResNet34-LM, about 35 minutes per 4-hour session.
- **Claude labels the voices inside Find moments.** Which voice is Jonathan; for everyone else gender, name and role. "Label voices with Claude…" does the labels alone. The first labels-only run on the 4-hour session cost $1.72, over its $0.54 to $1.04 estimate (the thinking ran to 57,000 tokens); the estimate is now built from that run.
- **Local guess before the labels land:** his saved voiceprint first, then pitch. With no voiceprint yet, voices stay white rather than guess him red.
- **Jonathan's fixes win** and cover the whole recording: a voice list in the Captions tab, plus "said by" on selected words.
- **Export looks the voices up again,** so a fix made after a short was saved still colors right.

**Why:**
- The recordings have one mixed audio track, so nothing knew who said a word.
- In a test on the real session, the voice split kept Jonathan and the prospect apart, but voiceprint scores between two people ran as close as for one person. So the words decide who is Jonathan, read by Claude: he gives his name and pitches Monarc Build. The voiceprint is only a fallback.
- Gender reads from names, "sir" and "ma'am" and pitch far more surely than role, and it is what the viewer hears.

**Alternatives considered:**
- Color by role. Jonathan chose gender.
- Tagging by hand only. He chose automatic with fixes.
- A faster voiceprint model (3D-Speaker CAM++). Dropped: it merged Jonathan and the prospect.
- Different caption heights per side. He chose one spot.
- A name tag on the video. Not wanted.

**Owner:** Jonathan Beach. His steps: open a short from the 2026-09-28 session and check the colors; fix any voice that is off in the Captions tab.

## 2026-09-30 - Monarc Studio: each voice on its own track, one click to even them

**Decision:** Jonathan asked for "two tracks per speaker" so he can normalize the audio. On the Caitlin clip, the gatekeeper runs 8 dB under him (-30.0 against -21.8 LUFS). He answered three grill questions (`brainstorms/2026-09-30-voice-tracks.md`):
- **V1:** every new short starts split. "Split audio by voice" does the same for older shorts.
- **V2:** A1 is You, A2 is Them, and sounds move to A3.
- **V3:** "Normalize voices" evens both tracks in one click, at -20 LUFS each.

How it works:
- Both voice tracks hold the same audio.
- Each one plays only its speaker's stretches, read from the voice labels and cut mid-pause with 2-frame ramps.
- The preview, the captions and the export all read the same stretches.

**Why:**
- Chopping the audio into dozens of clips would break trims, razor cuts and quick fixes.
- Two full-length clips linked to the video keep every edit tool working.
- A voice fix in the Captions tab moves the split too.

**Also the same day:**
- Touchpad scrolling on the timeline.
- A "+" for adding tracks that stays in view.
- The Caitlin clip's missed words filled in (this clip only).

**Owner:** Jonathan Beach. His step: on older shorts, run Clip → "Split audio by voice", then "Normalize voices".

## 2026-09-30 - Monarc Studio: Make trailer, the first short archetype

**Decision:** Jonathan named the Trailer, the first of several short archetypes: open on the peak without the reward, hard cut to the dial tone with a riser that starts the call, and a black-on-white headline for the thumbnail that is keyframed but never moves. He picked in the grill (T1-T4):
- **T1:** a Make trailer button.
- **T2:** the headline sits in the top third and fades in.
- **T3:** it stays on through the peak.
- **T4:** Claude drafts three headlines for him to pick from.

Built and tested:
- Mark the peak with I and O, then Clip → Make trailer.
- The call reaches back to its last ring (the dial tone is found automatically; 4.9 s before pickup on the Caitlin call).
- The Riser lands at the hard cut.
- The headline goes in a white box (text clips can now carry a box).
- One undo step.
- Headline drafts cost about $0.004.

**Why:** He builds these by hand today. The button lays out the archetype in one click and leaves every piece editable, so his edits stay manual.

**Owner:** Jonathan Beach. His step: try it on the Caitlin short; say what the next archetype is.

**Same day, after using it:**
- Their spoken word is white like his ("It looks better").
- Dragging a clip's start back past the timeline's beginning now reaches into the earlier recording, so the dial tone can be pulled in.
- Older shorts split into voice tracks on their own when opened.
- An open window says "Update ready · Reload" when Studio changes.
- No more black flashes on playback ("on playback, sometimes the screen goes black"). The cause: a video that finished a catch-up jump got pulled back to its old paused spot, over and over (478 jumps in a 12 s play), and at Full a slow jump was started over before it could land. Now a jumping video shows its last picture, small drifts are fixed by speed, and a quality drop no longer swaps the file mid-play.


## 2026-10-01 - Service pages: the headline takes the trade from the ad's link

**Decision:** Jonathan: "headline swaps in the trade from the ad link". Each Google Ads ad group's final URL carries a trade word (`?t=electricians`). The service page swaps it into the h1 from a fixed list of five trade words, falling back to "contractors". Nothing else on the page changes.

**Why:** One page per service serves several trade ad groups, and one fixed h1 cannot mirror every trade's search (Style Guide Copy 10). A fixed list keeps the swap from printing whatever a link says.

**Alternatives considered:** One page per trade per service (thirty pages); a fixed "contractors" h1 for every ad group.

**Owner:** AIOS builds the swap on the six pages and puts the trade on each ad group's link, after the `/av_marketing/` copy round; renders go to Jonathan before the push.


## 2026-10-01 - /av_marketing/ services speak in outcomes; the eyebrow names the person

**Decision:** Jonathan: "get rid of the seventh service being the posted analytics or monitor analytics, as well as make the copy about being outcome-based. I want this to feel like they're getting something returned from this." After eight questions and his reference screenshot (`brainstorms/2026-10-01-av-marketing-outcome-copy.md`):
- The services block on `/av_marketing/` becomes six static cards: the icon, the bold service name, one or two sentences on what the buyer gets back. No flip, no counters, no promised numbers.
- Monitored analytics comes off. Its lead tagging and monthly report, which the Pilot agreement covers, close the Google Ads card.
- Block copy: label "What you get back", h2 "Six services. One return: booked installs.", sub "Each one built to put high ticket buyers from your service area on your calendar."
- Hero sub: "Booked appointments with high ticket prospects in your service area." (his offer line; was "Schedule an appointment with our team.").
- Appointment setting stays; First Responder moves to "keep selling" in `context/offer.md`.
- Standing rule (mid-interview): "the eyebrow should always be naming the person this is targeted toward" (Style Guide Copy 11).

Built in the three copies, rendered, not pushed.

**Why:**
- His own cold-call rule 4: their outcome, never your service.
- His reference card grid showed the shape: the service name, then the return in the buyer's terms.
- No numbers, because the agreement guarantees no lead count or closed job.

**Alternatives considered:**
- Tying the fee to results (the offer stays a flat fee).
- Rewriting the whole page.
- The outcome as the big line with the service as a small tag, plus a flip for how (his Q3 and Q4 picks, replaced after his reference).
- Naming the real jobs or the math on the cards.

**Owner:** Jonathan Beach. His step: approve the copy on `projects/Landing Page Build/renders/2026-10-01/av_marketing-outcome-*.png` and say push.


## 2026-10-01 - Every company in the Prospects call list carries the trade it covers

**Decision:** Jonathan: "I want all of the companies in the Airtable list to be given a vertical that they cover", with electrical, AV/integrator, HVAC, plumbing, and roofer, plus any that show up commonly. His pick of the full set: twelve choices on the Vertical column of Prospects, Contacts.

The choices: Electrician, AV integrator, HVAC, Plumber, Roofer, Security, Low voltage / IT, Generator, Automotive, General contractor, Multi-trade, Not a contractor.

All 15,180 rows labeled by `scripts/label_verticals.py` and read back; 5,074 labels changed. Rules, in order:
- His hand-checked integrators.
- The 2026-09-13 site reads: integrator, or the AI picks from the read's reason.
- Trade words in the name, web address, and site title.
- Google's category.
- The homepage's title and description, read by the AI.
- Else the list the company came from.

**Why:** The labels came from the list a company was imported from, not from what it does. The site reads showed only 3,792 of the 7,269 rows in the "integrator" queue are integrators. The rest are stores, makers, and venues (2,087), alarm companies (535), IT and cabling (277), general contractors (198), car audio (157), and others. A label per row lets him call one trade at a time and skip the rest.

**Alternatives considered:**
- His five choices only (security and IT companies would hide under AV integrator).
- Five plus three (generator dealers and multi-trade shops folded in).
- Name words only (4,321 names say nothing about the trade).

**Cost:** about $3.85 of AI reads (claude-opus-5, effort low) and about 860 Airtable calls.

**Owner:** Jonathan Beach. His steps: drag the Vertical column next to Name (the API cannot move columns); filter the grid to AV integrator while calling the integrator queue. Undo: `projects/outreach/vertical-before-2026-10-01.json`.


## 2026-10-01 - Monarc Studio: a recording opens to its calls

**Decision:** Jonathan asked to import another 3-hour recording, have it split into clips, open the recording and see its clips as titles, and load only the clip he's watching ("100 different titles would be the only thing in memory, and then those titles are linked to the media"). His picks in the grill (B1-B22, `brainstorms/2026-10-01-clip-browser.md`):
- Clips are calls, ring to hang-up. Claude finds and titles them in the pass that labels the voices.
- Clicking a recording turns the Media panel into its calls. The panel then runs full height and widens: player on the left, one-line rows on the right (time, title, length, how it ended).
- Claude's best bits become diamonds on the player's bar. Stretches that aren't calls hide, except one that holds a best bit ("Between calls").
- A click plays from the ring and stops at the hang-up. Up/Down step through calls, I and O mark a part, Make short.
- Tags and a search over what was said. Colored captions on the player. Speed 1x/1.5x/2x. An unwatched dot and a Short tag.
- Claude's pass runs by itself on a new recording when the estimate is under $3.
- A low-disk note and "Remove full-size copy".

**Why:**
- A clip was already a bookmark into the recording; what he lacked was a screen that lists them all and plays one at a time.
- One player on the preview copy keeps memory flat: stepping through 20 calls on the 4-hour session kept the browser between 758 and 785 MB.
- A review against the real data found overlapping calls and best bits pinned to the wrong call. So call margins only add time, and bits go to calls by time.
- His strongest bits (five 5★) were talks to camera between dials, which is why B22 keeps those stretches.

**Alternatives considered:**
- Best bits as the list, or calls with bits nested.
- The big viewer as the player.
- Splitting the recording into separate small files.
- Finding calls from ring tones alone (free, but "Call 1" titles).

**Owner:** Jonathan Beach. His steps: drop the 3-hour file into `media/inbox` (or onto the Media panel); about 45 minutes later its calls appear by themselves if the estimate is under $3. The 4-hour session keeps its current titles unless he runs Find calls again (about $2).

**Same day, after the second recording came in:** "I should be able to collapse the previous recordings. They should effectively be saved by the date that they were recorded." Each recording is titled by its recorded date (from OBS's file name, else the file's own time) and listed newest first. The earlier ones fold under "Previous recordings", closed until opened. Files keep their names on disk.

**2026-10-02, "I can't hear audio during playback for the clip":** shorts from the 3-hour recording were silent. Its full-size copy (`orig.mp4`) was missing while prep said done. "Prepare again" had deleted it at the click, the rebuild waited behind Monarc Calls' hold on prep, and a restart lost it. Now:
- "Prepare again" removes old outputs only as each stage reruns.
- The server checks the outputs at start.
- Sound falls back to the OBS file while the copy is missing.

The copy was rebuilt the same day.


## 2026-10-01 - Monarc Calls: a record window in Studio that ties each call to its Airtable row

**Decision:** Jonathan asked for a note-taking tool for his cold-call sessions that keeps a file per company, ties it to the company's Airtable ID, catches what owners say (an email, "mixed resi and commercial, short on techs"), and drafts the follow-up in his voice without repeating what he said on the phone. His picks in the grill (31 answers, `brainstorms/2026-10-01-live-call-notes.md`):
- A separate module inside Monarc Studio: its own window ("Monarc Calls" shortcut, or Record in Studio). OBS stays the recorder, run from the window.
- He dials on his cell on speaker, so the laptop never sees the number. He clicks the company's row as he dials; the next click ends the call; Esc or End call ends the last one.
- The window carries the Prospects list (one trade, blank rows in Call order, search for anyone); the Airtable tab goes away during sessions.
- During a call it shows the company (website, name, phone, their time) and three slots, Email, Owner, Status, and no live words.
- Airtable gets Status (typed), Email and Owner (only when blank) on the Contacts row, and one Outreach Log row per dial with its columns filled.
- After Stop, his clicks become Studio's call splits, named by company with the MB ID; Claude's pass only marks the best bits.
- Four stages, one real session between each: 1 the record window (built), 2 live words, the tool filling the slots, a page per company (`projects/prospects/<MB-ID>-<slug>.md`) and cards only for calls that need him, 3 the Booked flow (time in their zone, calendar hold from jonathan@monarcbuild.com, invite, Proton draft, CRM deal) and "send me something" drafts, 4 the objection bank, where calls die, a session report on CRM Today, and a meeting brief the night before.
- New copy rule in `references/mycopy.md`: after a call, the email never repeats what he said on the call.

**Why:**
- The laptop can't see what the cell dials, so his click is the only sure join between a call and a company; it also replaces typing the outcome in Airtable.
- Every click is written to a session file before anything goes over the network, so a dropped connection or a crash loses nothing.
- Studio stops preparing other files while recording: OBS skipped 97 frames on 10/1 with nothing else running.

**Alternatives considered:**
- Matching calls to companies by listening for the name (misses voicemails and front desks).
- Matching on his Status entry after the call (nothing live).
- Studio recording by itself without OBS.
- Notes in Airtable only, or the CRM only.

**Owner:** Jonathan Beach. His steps before the first session: in OBS, Tools, WebSocket Server Settings, tick Enable WebSocket server; the first time in the window, press "Live picture" and pick OBS Virtual Camera. Before stage 2: switch OBS's encoder to Hardware (QSV). Open question: what Role codes GT, PM, PR and TC mean.


## 2026-10-02 - Monarc Studio: drag a clip's volume on the timeline

**Decision:** Jonathan: "Make so I can drag the volume up and down on the timeline for select media." Built as follows:
- A selected audio clip's volume line is a handle: drag it up or down.
- Every selected audio clip moves by the same amount, and one drag is one undo step.
- 0.2 dB a pixel (Ctrl 0.05), a catch at 0 dB, the level shown beside the pointer.
- Double-click the line to reset to 0 dB.
- Keyframes move together. The volume limit is now +24 dB here and in Effect Controls (Normalize voices goes past +12).

**Why:**
- Only selected clips get the handle, so a click on any other clip still selects and moves it.
- A fixed step instead of following the pointer, because the line has 19 px for the whole range at normal track height.

**Alternatives considered:**
- The handle on every audio clip (easy to grab by accident when moving clips).
- Moving only the keyframes either side of the pointer, as Premiere does.

**Owner:** Jonathan Beach. Reload Studio to get it. `references/studio.md` "Volume on the timeline".


## 2026-10-02 - Monarc Studio: captions are generated after the trim

**Decision:** Jonathan: "Captions should only be generated after I trim a video to its best parts. So the transcript is the only thing that is weighed for contextual accuracy." Grill G1-G7 in `brainstorms/2026-10-02-captions-after-trim.md`. Built as follows:
- A new short has no captions until he presses Generate captions (the Captions tab, the sparkle on the timeline's Captions row, or the Clip menu). Trimming still snaps to the transcript's words.
- Generate listens again to just the kept parts (whole sentences, no voice detector). Where the two listens differ, Claude reads the short's own words and picks A or B; it never writes its own. About 1 to 2 cents a short.
- The words are saved in the short in the recording's seconds, so later cuts keep them right. Footage pulled past what was generated shows a "Generate again" note.
- Word fixes after Generate (spelling, who said it) are saved on the short.
- Export asks "Generate captions first?" (Generate and export / Export without captions); Export all names the shorts that went out without captions.
- Older shorts keep their captions from the transcript, with Generate captions to replace them. The calls view's player keeps its rough captions.
- Numbers start their own word now ("get15" was written 59 times in the first two recordings; "C3" and "Control4" stay joined).

**Why:**
- Call c23 of the Sep 30 recording: the voice split heard 254.8 s of speech, the transcript's words covered 172.1 s, and where a second listen differed it was right most of the time.
- Claude only choosing between two things heard keeps the words his callers really said.
- The real run on c23's first best bit: 216 words became 230, 1 to 1.9 cents, 25 to 33 s; it filled the far side's missed "No, I do not, I do not have 15 minutes".

**Alternatives considered:**
- The second listen's words everywhere, no Claude.
- Letting Claude rewrite words to fit the sentence.
- Rough captions marked as a draft until Generate.
- Generating again after every edit, or locking a short once generated.

**Owner:** Jonathan Beach. Reload Studio to get it. `references/studio.md` "Generate captions".
- Same day, built without questions (his other asks): a star rating with a "why" line on calls that have best bits (he picked "On the rows that have best bits"), and box-select from the Captions row and below the tracks ("I should also be able to drag select clips").


## 2026-10-03 - Monarc Calls reworked: his Airtable grid beside live key notes, no recording


## 2026-10-05 - The hero check, the lead-review pipeline, and the reading budget

**Decision:** Jonathan (2026-10-05): "filter my seed list, make it a skill, and we want to be monitoring for a call to action in a booking form in the hero section, centered text, a headline that matches buyer intent. And if it doesn't have that, that's our leads. Each of them we're going to build a loom video for and then export those videos as long form for YouTube. Cut them in the short form for Instagram and Facebook." Built as: the hero check, a workflow of `/list-building` (`scripts/hero_check.py`: the niche gate from the existing site reads, the rendered first screen in headless Edge, one click to see what the button opens, a small Claude read of the headline's words; the leads become the integrator call list on his go); `/research review-brief` for his recording; `/social-content long-form` and `review-short` for the cuts; `scripts/youtube_api.py` for upload (private) and publish, each on his go.
- Lutron is a sort key, not a gate, until he says which (about 128 Lutron-named leads against about 400 residential).
- Meta's posting API is not built: "I dont need metas API." He posts the shorts himself.
- A review Loom on a company's file is kind "Page review", off the Loom-brief show-rate report.
- The reading budget: "Relevance should be a skill used whenever prompting so I don't load too much context from .md files... around 35% max of the remaining window at a time." `.claude/skills/relevance/SKILL.md`, one line in CLAUDE.md and AGENTS.md.

**Why:** his words above. The three hero rules are his page rules (Taste Log, Style Guide Copy 11), so a site that breaks them is a site he can show the fix for on a Loom. The first 40 rows: 17 leads, 17 not, 6 held, 19 cents.

**Alternatives considered:** a vision read of every first screen (costlier, slower; the DOM read is free and the picture is the fallback); Meta's content publishing API (needs a Meta app, a Page, a public file URL; he said no); a title card on the YouTube cut (nothing he did not say goes on screen).

**Owner:** Jonathan: the Lutron question, the go on the full run (about $6.40), the YouTube sign-in and the Cloud console steps, the 20-row check before the CSV is written.

**Decision:** Jonathan (2026-10-02): scrap the whole recording part and the OBS WebSocket; listen to whatever mic Windows uses; a text document per call; "it should literally just be the Airtable view... displayed next to a transcription of key notes". Key notes: an offering, a constraint or an objection about the company, plus an email, a name, a phone number. His picks in the second grill (Q32-Q45, `brainstorms/2026-10-01-live-call-notes.md`):
- His real Airtable grid in its own window on the left two-thirds; the notes window on the right third. One shortcut opens both.
- "When I type anything under status the last transcript is attributed to that row." Typing Status ends the call.
- Notes show live. Kinds: offering, constraint, objection, email, name, phone, and a meeting agreed.
- The notes come from a plain Python script that runs the same way every time, no Claude ("it is just a python script that runs deterministically"). The phrase lists were seeded from his 9/28 calls into a file he edits.
- "I have the option to edit the notes before pushing to their file": each call's notes become a card he edits and pushes. A call with no notes files its words by itself.
- A doc per call in a folder per company: `projects/prospects/<MB-ID> <Company>/<date time> call.md`.
- Airtable: an Outreach Log row per dial; on push, a blank Email and Owner filled and the notes in the log row's Transcript. The tool never writes Status.
- Start, with Pause on F9 (works while Airtable has focus).
- Gone: OBS control, the picture strip, Studio splitting recordings by clicks, "Find best bits", the custom list and status chips.

**Why:**
- He already works in Airtable all day; a copy of it was one more thing to learn. His Status entry is the one sure join between a call and a row, since his cell can't tell the laptop who he dialed.
- Rules over a model keep it free, offline and predictable, and he can fix a miss by adding a phrase.
- On the 9/28 calls the rules caught "months behind", "can't find anybody", "we're handling it ourselves", "me and Dad", the names and "Tomorrow 5:00"; one mic hears both sides, so his own pitch lines are ignored by phrase.

**Alternatives considered:**
- An Airtable copy in one window (the first build), or Airtable's read-only embed.
- Matching calls by the name in his opener.
- Claude reading each call live (about $2 to $10 a session by model).
- Filing notes at Status with no review.

**Owner:** Jonathan Beach. Before the first session: plug the mic in (none was connected on 2026-10-03), open "Monarc Calls", sign in to Airtable in that window once if asked. Edit `references/call-note-phrases.md` as calls show what it misses. Open: what Role codes GT, PM, PR and TC mean; check Airtable's monthly API allowance (the Status check is about 2,900 calls a 4-hour session).


## 2026-10-03 - Monarc Flow: Wispr Flow rebuilt to run on the laptop, cleanup by rules

**Decision:** Jonathan (2026-10-03): "rebuild wispr flow to run locally on my machine using the ctrl and windows button as the shortcut to speak. It should be lightweight and grammatically accurate." His picks:
- Cleanup by fixed rules on the laptop, nothing leaves it: Parakeet writes the periods, commas and capitals; the rules take out fillers and stutters, act on "scratch that" and "new line", fix brand names from `projects/flow/words.json`, and drop em dashes.
- A small pill at the bottom center of the screen while he talks, plus a tray icon.
- Hands-free: Space while holding Ctrl+Win locks it on; Ctrl+Win again stops.

**Why:**
- Parakeet (already on the laptop for Studio) writes 7.4 s of talk in about 0.6 s here, and the key watcher keeps running while it works, so one small program does it all.
- Rules are free, instant, private and predictable; a miss is fixed by adding a line to the word list.
- Measured on 2026-10-03: words land 0.93 s after letting go of an 8.8 s hold; a 50 s hands-free take is out 0.68 s after it ends, because pieces are written at pauses while he talks. About 750 MB of memory while running, almost all of it the speech model.

**Alternatives considered:**
- Claude Haiku polishing the text (fixes grammar and changes of mind, about 1 s more, needs the internet, about $1 per 2,000 takes).
- A small AI model on the laptop (2 to 4 s more per take, 1.5 GB more memory, weaker than Claude).
- Sound only, no pill. Hold only, no hands-free.

**Owner:** Jonathan Beach. Plug in a mic (none was connected on 2026-10-03; the pill says "No microphone" until one is). Add a line to `projects/flow/words.json` when a brand or name comes out wrong. If the rules fall short on grammar, the Claude polish can slot in after `flow_clean.clean`.


## 2026-10-03 - CRM: the Integrators/Electricians switch goes, Pipeline gets a Funnels tab

**Decision:** Jonathan (2026-10-03): "Under pipeline, the tab should have a funnels view. And the integrators and electricians tab at the top can go. I don't even know what that's for."
- The switch above the rail is gone. Today, Companies, and Pipeline show every trade together, and the CRM's call list on Today is every list in one (8,787 rows across the two CSVs). A company still carries its trade on its record; a new one defaults to Integrator.
- Pipeline has two tabs: Board (the journey map, the KPIs, the stage columns, as before) and Funnels.
- Funnels shows the whole funnel first: dials, connects, booked, held, proposed, won, from the base plus the call sheets. Each step's rate is a bar from 0 to 100 with a tick at the rate the plan assumes and a word on where it stands (over plan, under plan, on plan). Under each count sits what 5 signed takes at the plan's rates: 1,334 dials, 400 conversations, 40 booked, 20 held. Then one card per channel in its own steps (ads: impressions to won; cold call: dials to won; LinkedIn: requests to won; other sources: companies to won).

**Why:**
- A funnel drawn with widths scaled to the top count hides the bottom: 5 won beside 1,000 dials is a hairline. A bar per step rate keeps every step readable and puts the leak where he can see it (today: booking rate 3.4% against a 10% plan; connect rate 53.7% against 30%).
- The counts are the ones the Channels page shows (the base plus the call sheets), so the two screens agree.
- Removing the switch while leaving the filter on would have hidden the electricians on every screen. Merging the lists keeps every record reachable.

**Alternatives considered:**
- A trapezoid funnel picture (hides the small end).
- Hiding the switch but keeping the filter on the first trade (the electricians vanish).
- Putting the funnel on Reports (he asked for Pipeline).

**Owner:** Jonathan Beach. The plan's rates live in Config `goal.assumed_rates`; change them there and the ticks and the "needed" counts follow. If a trade should show on its own again, the Vertical field is still on every company.


## 2026-10-03 - Meta ads reopened: a talking-head video to the builder search check, which ends on the calendar

**Decision:** Jonathan (2026-10-03) brought a Meta video idea ("AV Integration business owners looking to get specified by Architects, builders, and designers... take this 30 second quiz") and asked for it grilled "so I have no chance in failing to get at least one meeting with a qualified buyer." Thirty questions (`brainstorms/2026-10-03-meta-ads-builder-search-check.md`). His picks:
- The call sells the pilot as is. The ad's bridge is the proof: the Georgian came from a contractor who typed "whole home audio Annapolis"; specifiers search too. The belief to break: getting specified is a relationship game.
- The ask is "Can a builder in your county find you tonight?", never "quiz". A new page `/builder-check/` in the `/av_marketing/` look: four tiles (installs, technicians, last five jobs, ads today), one true result line, then the five booking steps. No email gate; the only Meta lead the CRM sees is a booked call.
- Three videos, one ASK: the belief, hook 30 (honesty), hook 16 (referrals). No name spoken. The Georgian proof with no dollar figure.
- Audience broad (US, 30 to 65, business-owner behaviors, the DMV included, his call against the recommendation); the hook and the tiles filter. Objective Leads on the check's result screen.
- Production: the raw take in any room with a good mic; Higgsfield Ad Multiplier puts him in a finished rack room in the black hat, jeans, and button-down; cuts by hand in Studio; frame QA; the raw take kept as the fallback.
- Six gates before spend: the Meta accounts (none existed); the privacy lines and the push; the booking script republished; the script and calendar moved to jonathan@monarcbuild.com; a Pixel test booking; the Platform id on the row. Live target Tue 2026-10-20. A day-before reminder for every site booking ships in the same republish.
- Reverses the 2026-09-23 "only channels" decision for Meta only. The campaign: "Meta: builder search check", `projects/meta-ads/`.

**Why:**
- The draft promised exposure to specifiers while the call sells search; the bridge in the proof makes the ad true and the call consistent.
- "Quiz" is learner intent (it is a Google Ads negative) and the draft's result ("are you on the right channels") was predictable; a check named by what it measures, with a true read, is free value first.
- Meta cannot target AV integrators by interest any more and the matched lists land at 150 to 400 people; the first three seconds and the four tiles are the targeting.
- A website check that ends on the calendar has no follow-up loop; an Instant Form would hand him leads to chase by hand, the thing that eats his week.

**Alternatives considered:**
- A specifier product (LinkedIn to architects); an Instant Form; gating the result behind an email; a score out of ten; "quiz" kept; the DMV excluded; one video; his name on camera; a real-room shoot.

**Owner:** Jonathan Beach. His parts, the week of Oct 5: the Meta accounts, the proof span, the scripts approved, three takes, the privacy lines, the push, the republish. The AIOS never presses go live.


## 2026-10-03 - Paid media: $60 a day across Google and Meta; Meta reads at $500 and stops at $1,000

**Decision:** Jonathan (2026-10-03): Meta runs at $30 a day beside Google Ads 07 at $30, $60 a day in total, each on its own gate; nothing else is added to paid media until one passes. Meta's first read at $500 spent (about 2026-11-05): clicks, check starts, check completes, bookings, cost per booked, per ad. Stop at $1,000 (about 2026-11-19) unless one qualified booking was held; pass is one qualified held per $500, then the next $1,000. The Sept 11 gate (5 booked and 1 closed at $1,000) is retired.

**Why:** at $2.50 to $4 a click and 1 to 3 percent of clicks booking, $1,000 buys 3 to 8 bookings, about half qualified; one qualified meeting is a fair test at that spend and five plus a close is not. Google's own $100 a day rule stays separate so 07's learning is not disturbed.

**Alternatives considered:** a shared $100 a day; pausing 07 while Meta tests; $50 a day (the Sept 11 pace); $15 a day.

**Owner:** Jonathan Beach. The numbers live on the Campaigns row (Outcomes) and in `projects/meta-ads/README.md`; the read is written to `projects/meta-ads/reports/`.


## 2026-10-03 - The Sept 11 Meta ad sets deleted; LinkedIn ads decoupled; the ad made in Higgsfield under an 800-credit cap

**Decision:** Jonathan (2026-10-03):
- The two Sept 11 Campaigns rows ("Meta ad set 1: matched list and retargeting", "Meta ad set 2: lead form, free city search", Planned since 2026-09-16, Started 2026-09-21) are deleted, his call against the recommendation to end them with a note. They showed about $650 of estimated spend that never happened. Their plan stays in `projects/outreach/campaigns-2026-09-11.csv`.
- LinkedIn ads no longer wait on a Meta result; the "waits on ad set 2" task came off the LinkedIn card.
- The three videos are post-produced in Higgsfield's Ad Multiplier (the "Jonathan" connector) from his raw takes, every run quoted first, 800 credits at most for the campaign; whatever is finished at the cap ships, the rest runs as the raw take. Angle changes are punch-ins placed by hand in Studio; one generated-angle experiment, kept only if it passes the frame QA.

**Why:** the old rows mis-stated spend on the Meta card; the LinkedIn linkage was a Sept 11 sequencing idea with no evidence behind it; Ad Multiplier keeps his motion, framing, and audio and swaps the room and clothes, which is what he asked for, and the cap keeps a third of the balance for everything else this month.

**Alternatives considered:** ending the rows; renaming ad set 2 into the new campaign; keeping the LinkedIn gate re-pointed at this campaign; 1,500 credits or no cap; generated angles as the base.

**Owner:** Jonathan Beach (the credit cap, the fallback call). The AIOS (the runs, the QA).


## 2026-10-03 - Free campaign for a review: an audit of their area plus a Google Ads campaign they load themselves, offered on a second call window, the review asked after

**Decision:** Jonathan (2026-10-03, a 13-question grill, `brainstorms/2026-10-03-free-campaign-for-reviews.md`):
- The free thing given to ICP prospects to earn Google reviews on the new Business Profile is an audit of their area (the three searches a buyer types, who shows up on the real Google page, their reviews against the market, the page the campaign lands on and its three fixes) plus a free Google Ads campaign for one service and one city, handed over as a Google Ads Editor import file they load themselves, paused. Not a landing page: "they already have a website."
- Built by the AIOS from the call list row for about $0.10 a company and none of his time (`scripts/free_campaign.py`, `projects/free-campaign/`). The real results page comes from DataForSEO by city (an account he opens, $50); Places from the cache for review counts.
- Offered on calls only, in a second call window with its own script (`references/free-campaign-call-script.md`) and its own log (Prospects, table "Free campaign calls"), beside the dial hour's meeting ask. He says it straight on the call: free, "I'll ask you for a Google review after", then the retainer. No cold email wave; riley@monarcbuild.com stays out of it.
- The review ask is an email from him two days after the delivery was sent, held until the profile is live, three a day, oldest first. The review is never the price of the free thing.
- Target 12 to 15 reviews in two weeks from about 25 dials a day in the second window, then a drip (30 in two weeks would need 60 dials a day; the target gave).
- In the CRM: campaign "Free campaign for a review" on the Cold call channel, Platform id `free-campaign`; a Config row `call_sheets` so a second campaign reads its own call sheet; a Monarc CRM table "Free campaigns", one row per company from Built to Review left; the first three deliveries need his Approved on the row.

**Why:** the Review Generation Farm's rule already fits (ask after delivery, never as the price); a built file earns a stronger review than advice on paper and sets up the retainer in one line; the data for the audit is mostly bought already; a new profile filters review bursts, so the pace matters more than the count.

**Alternatives considered:** a free landing page (they have a site); a Google Business Profile rewrite; a review kit for them; a 15-minute call per delivery; an email wave from riley@ at 20 or 50 a day; the review ask on the delivery email or on a callback; telling the two windows apart by the clock.

**Owner:** Jonathan Beach: the DataForSEO account, the second log's name, the script and the two templates approved, the first three deliveries approved, the review link once the profile is live, the sends. The AIOS: the builds, the drafts, the CRM rows, the read-back.

## 2026-10-04 - Monarc Edge: a Kalshi Premier League betting agent, approve mode first, auto behind a four-light gate

**Decision:** Jonathan (2026-10-03 to 04, an 18-question grill, `brainstorms/2026-10-03-betting-market-agent.md`; plan approved 2026-10-04):
- An agent that uses his cash on Kalshi and bets against English Premier League match-winner prices (series `KXEPLGAME`: home, away and Tie markets, six tradable sides, one position a match) when the market sits 7 points or more from the real chance after Kalshi's taker fee, in busy markets only (10,000 contracts traded, 2-cent spread).
- The real chance comes from his own model built in his five stages (define the outcome; define the variables from data that is posted and proven legit; build a win probability per test group; observe if the win rate scales with the market's prediction; post the offset as a green +% or red -% with the reasoning). A Dixon-Coles goals model on football-data.co.uk now, API-Football Pro ($19 a month) for possession, tackles and interceptions vs take-ons, lineups and injuries once the key exists. Market prices never enter the model. Claude writes each card's reasoning and may not change a number.
- Stake: 6% of the match-day bankroll at the 7-point floor, a straight line to 8% at 17 points or more, from a $1,000 bankroll. No cap on cash at risk, his words: "We are only constrained by the amount of upsided bets we can take and the capital we have to stake." A 25% drawdown stop stays in config, auto mode only, his to turn off.
- Timing in his words: "when the market is the least sharp." The loop snapshots hourly and the record keeps closing line value by hours-to-kickoff band so the proof learns the softest hour.
- Approve mode first: every card waits for his click. Auto mode unlocks only when four lights are green on the Record page: 200 settled cards (paper counts), hit rate within 5 points of our chance in every band of 30 or more, return after fees above zero, average CLV above 5 points (his number; a high bar, said so).
- Kalshi holds the cash, demo exchange and dry-run first, production only after a seven-line rehearsal checklist. Polymarket's public feed is the read-only second witness. He trades from Maryland, where sports contracts sit inside Maryland v. Kalshi (4th Cir., argued 2026-05-07, enforcement paused); the agent halts on a delisting, on zero EPL markets, or on an order refused for location. Trading sports from Maryland while the case runs is his decision, taken when he funds the account.
- Its own window like Studio ("Monarc Edge", port 8800), its own folder `projects/edge/`, its own tests.

**Why:** his stages ask for a measurable gap between a model and the market, which needs a model that does not read the market; approve-first and the gate make the agent earn auto mode with evidence instead of a feeling; the busy-market floor keeps a 7-point gap from being just an empty book; CLV is the honest test of edge when 200 bets is too few for profit to mean much; Kalshi is the one exchange that lists soccer in Maryland today and has signed API keys and a known fee; the Tie market is the cheapest way to bet the draw, the outcome retail books misprice most.

**Alternatives considered:** a second market as the yardstick; an AI probability estimate (rejected: not calibrated); Polymarket US as the venue (blocks sports in Maryland); national team matches (too few games); the top five leagues (five times the data work); free scraped stats (he chose a paid feed); a flat $20 stake and a $50 cap (replaced by the 6 to 8% line); a cap on cash at risk (he declined); a CRM tab or a daily email instead of a window; waiting a full paper season before any real money.

**Owner:** Jonathan Beach: the Kalshi account and keys (demo, then production after the rehearsal), the API-Football account, the fee PDF read once, funding, every Approve click, the flips of `env`, `dry_run` and `mode`, the Maryland call. The AIOS: the model, the backtest and its honest report, the cards and their reasoning, the ledger and the lights, the halts, the tests, the daily reconcile in the first live week.

## 2026-10-04 - Monarc Edge runs paper on the live account, with auto paper fills and a sixth-grade light page

**Decision:** Jonathan (2026-10-04, in chat: "saved as KALSHI_API_KEY", "Lets run paper on an account", "I need a 6th grader view of this screen and make it light mode like a google product"):
- He made a production Kalshi key (not a demo one). The AIOS switched `env` to prod at his word, with `dry_run` kept on: the agent reads his real account (balance, positions) and real prices, and no order can leave the machine until the rehearsal checklist is ticked and he turns dry-run off himself.
- While dry-run is on, every card that turns green and busy is paper-filled at the ask by itself (`paper_auto`), one position a match, so the 200-card record builds without a click. His click matters once dry-run is off. First paper bet 2026-10-04: Chelsea v Bournemouth, "Chelsea does not win" at 44 cents, 176 paper contracts.
- Paper cards settle from the market's own result (they never reach the account's settlement list).
- The page is light (Material 3 light, the CRM's tokens) and written for a sixth grader: the bet in words, "we think N out of 100" against "Kalshi's price says N out of 100", "risk $X to win $Y", a "Why" note whose numbers are written by code and whose reasons Claude adds, flags in plain words, the trader numbers folded under "Show the math".
- After a review of the first card (pasted by Jonathan 2026-10-04: an 18-point disagreement with two markets on a Premier League game is a warning, not an edge; real edges on big games are 2 to 5 points): a card at 10 points or more turns yellow, "the model may be wrong, check the news". Paper logs it anyway (the data that tells us whether to trust the model), he may click it after a look at the news, live auto never takes it, and the Record tab splits bets by gap size. Notes now say which way each reason cuts for the bet. Pinnacle's live line goes on the card when the API-Football key exists; the price after lineups was already recorded (snapshots every 5 minutes inside 75 minutes, CLV by hour). The review's last line stands: the tool is good enough for the paper test; stop building and let it log.

**Why:** the record is the proof and it cannot build if every paper card waits for a click; reading the real account while trading paper keeps the two books side by side from day one; a card he cannot read is a card he cannot judge, and the numbers are safer written by code than by a model.

**Alternatives considered:** keep `env` demo with no demo key (account calls fail, nothing gained); make him a demo key first (still useful for an order rehearsal with play money, optional now); leave approve-click for paper (the gate would take a year); let Claude write the whole note (it mixed up which side a price belonged to on the first try).

**Owner:** Jonathan Beach: the demo key if he wants an order rehearsal with play money, the fee PDF row, the API-Football key, funding the bankroll, turning dry-run off after the checklist. The AIOS: the paper loop, the notes, the page, the tests.


## 2026-10-04 - The company page becomes a file with a triage; the Loom brief joins the Booked steps

**Decision:** Jonathan (2026-10-04): "When I search for a company, it displays me a neatly organized file. On the contacts that have been made with that company, maybe any key people that I've spoken with... it should be like a triage of things that I need to do. Right now, I called them and scheduled a meeting, but I haven't sent over the Loom video that goes over a brief on what I'm going to be effectively operationalizing for the company to make sure lead flow is smooth for them."
- The CRM's company page is now that file: a to-do list for the company (the steps of the stage it is in, flags the CRM reads itself, his own to-dos), the people spoken with, every contact made from every record in one log (CRM activities, the Prospects call sheet and Outreach Log, site bookings, LinkedIn, call notes, Proton mail), deals, notes, files.
- The search also finds companies that are only in the Prospects call list (most of the 15,000), and their file opens without adding them to the CRM. One match from the top bar opens the file at once.
- The steps per stage live in `projects/crm/playbook.json`, drawn from `references/pipeline-process.md`, his to edit. New step at Booked, his: **send the Loom brief before the meeting** (what we will set up so their lead flow runs smooth). A sent email to them with a loom.com link ticks it by itself.
- A meeting on file counts as Booked for the to-dos even while the deal on the board still says Contacted; the file flags the deal to be moved. The AIOS did not move any deal.
- Ticks and his own to-dos are kept in `projects/crm/triage.json` by company key, not in Airtable (no record cap, works before a company is in the CRM). The Companies page lists every company waiting on him.

**Why:** his calls live in the Prospects sheet, so the old page (CRM activities only) showed a called and booked company as untouched and the search missed it. A stage tells him where a company stands; it did not tell him what he still owes it.

**Alternatives considered:** a Tasks field on the Airtable Companies table (needs the company in the CRM first, and the base is capped at 1,000 records); adding every called company to the CRM on open; moving the Momentum deal to Booked for him; a roll-up on Today instead of Companies.

**Owner:** Jonathan Beach (the steps in the playbook, the ticks). The AIOS (the page, the readers).


## 2026-10-04 - Loom briefs are tracked by variation against show rate and close rate

**Decision:** Jonathan (2026-10-04), with the first Loom brief made (Momentum Electrical Contractors, "Boosting Leads With High Converting Landing Pages", 11 minutes 23 seconds, a full review of their landing page): "I should also analyze the Loom walkthrough, like different variations of it, to see how that affects things like show rate and close rate."
- Every Loom brief is pasted on the company's file in the CRM and kept in `projects/crm/looms.json`: the link, its title and length, its variation, the day it went out (read from Sent), whether they watched it (his to mark).
- Variation A is this one: the full page review, about 11 minutes, every change named before the call. The next variation is named when it is made; one thing changes at a time.
- Show or no-show is answered on the company file's Booked step. Reports, "Loom briefs" sets each variation's show rate and close rate beside the meetings that got no Loom (two held of two answered so far).
- A difference is read at about 20 answered meetings per variation, not before. Watched or not is the faster signal.

**Why:** a comparison made later needs the record made now; three booked meetings before this one carry no note of what was sent. At about one booked meeting a week the show-rate difference between two variations takes months to show, so only a large change is worth testing (length first: 11 minutes against 3).

**Alternatives considered:** Loom fields on the Airtable Deals table (a schema change, and a company may not have a deal yet); reading Loom's viewer data by API (needs his Loom login; not wired).

**Owner:** Jonathan Beach (the variations, the watched mark, the show or no-show answer). The AIOS (the record, the report).

## 2026-10-05 - The price and the buyer are reopened: 5 AI clients at $3k+ MRR each

**Decision:** Jonathan (2026-10-05), asked whether "5 paying AI clients at $3k+ MRR each" in the orchestrator he pasted on 2026-10-04 was a new target or an example: "I was offering too low to the wrong people."
- Goal 1 is now 5 paying AI clients at $3k+ MRR each (`CLAUDE.md` and `AGENTS.md`, "The orchestrator").
- The 2026-09-15 Pilot Service Agreement (`context/offer.md`: $1,000 a month to Monarc in the pilot after the match, $2,500 a month after) is on hold for new quotes. No new draft states a price from it; the price line in `references/mycopy.md` is on hold with it.
- Not decided yet, his to answer: who the right people are, what they buy at $3k+, whether December 1, 2026 still stands, and what happens with prospects already holding the 9/15 terms.

**Why:** his words above. On file beside them: five clients on the 9/15 terms is $5k a month in the pilot and $12.5k after; five at $3k+ is $15k or more. He joined AI Acquisition (Incubator + DFY Package, $1,990) on 2026-10-04, with the intro call on 2026-10-05.

**Alternatives considered:** none stated.

**Owner:** Jonathan Beach (the buyer, the offer, the price, the deadline). The AIOS (holds the old price out of new drafts, rewrites the pages once he sets them).

## 2026-10-05 - Price rule: what people pay on the market for the tools

**Decision:** Jonathan (2026-10-05), asked who the right people are: "We go off of what people pay on the market for the tools." Each tool is priced at what the market already pays for it. No number is carried over from the 9/15 agreement.

**Why:** his words above; no further reason given. Open: which tools are on the list, and who the buyer is.

**Alternatives considered:** none stated.

**Owner:** Jonathan Beach (the tool list, the final numbers). The AIOS (pulls the market prices with sources once the list is named).

## 2026-10-05 - The tool list: 50 names folded into 12 agent skills the clone runs

**Decision:** Jonathan (2026-10-05) pasted a list of 50 AI services with a price each and said to make them things we build, "but first, we want to X out the ones that are unnecessary". Then, in the interview:
- They are skills, not project folders: "these should be skills for jonathan the orchestrator clone of me to run".
- The buyer is any business with the problem, not one trade: "Dont x out the other high ticket. I am basically just handing off an agent that fixes a universal problem."
- Only the doubles are cut. The 50 names fold into 12 problems, one skill each; the industry is a setting inside the skill. No name is dropped (`references/agent-catalog.md`).
- A skill's job: build the agent in the company's own tools, hand it off, then check it each month. Selling stays with him on the call.
- The skills are taken one at a time, three parts each: "Number one is to name its primary objective. Number two is going to name... the procedure of how it gets put into place. Because this is going to be repeatable and a deliverable that not only works within my company but also gets shipped to other companies inside of their business. And the criteria for passing."
- The AIOS drafts the three parts, he marks up. Outbound goes first.

**Why:** his words above. The fold keeps one procedure and one pass list per problem, so a skill proven at Monarc ships to a client in any industry by the same steps. This answers two of the open lines in the two entries above: which tools are on the list, and who the buyer is.

**Alternatives considered:** cut to what the trades buy; cut to what runs Monarc's own selling; also cut the seven one-time site builds; also cut everything under $3,500; one skill per name (50 skills); a brief for all 12 at once before any is finished.

**Owner:** Jonathan Beach (each skill's three parts, the order, the final price). The AIOS (the drafts, the skill files, the pass record of each install). Still open, his: where the list came from and what its last three numbers are, whether each price is one-time or per month, and whether December 1, 2026 still stands.

## 2026-10-05 - The outbound agent sends pre-approved messages by itself

**Decision:** Jonathan (2026-10-05), asked whether the outbound agent sends by itself once the messages are approved or only queues them for a person: "Pre approved messages get sent."
- In `/agent-outbound`, a message the owner approved goes out by itself, on every channel, inside the daily cap. Nobody presses send each day.
- The AIOS's reading, his to change: an approval covers the words, the list they go to, and the cap, and a change to any of the three needs a new approval; anything not approved (a one-off reply, a new message) is drafted and waits.
- This is the agent skill's rule. `/inbox` still never sends, and nothing else in the AIOS sends on this word.

**Why:** his words above; no further reason given. Put to him with the question: tools that send LinkedIn messages break LinkedIn's rules and the seat can be limited or closed. The skill tells each owner that line before they approve LinkedIn messages and records their yes.

**Alternatives considered:** queue every message for a person to send (as Patrick does for Monarc's LinkedIn today); the AIOS's pick, email sent by itself and LinkedIn queued.

**Owner:** Jonathan Beach (the rule; his yes or no on a tool sending from his own LinkedIn seat is not on file). The AIOS (the skill, the approvals on each install record).

## 2026-10-05 - Outbound lists are bought data, run through a list-building skill

**Decision:** Jonathan (2026-10-05): "Linkedin and Email will be bought through a data company and used in conjunction with the list building skill which enriches and qualifies for signaling attributes."
- The outbound agent's list starts as bought LinkedIn profiles and emails, not a sweep.
- A list-building skill enriches each row and qualifies it on the signals set at intake. It is a shared part the agent skills use, outside the list of 50 (`references/agent-catalog.md`, "Shared skills"). First cut drafted the same day, not approved.
- Added by the AIOS, his to strike: every bought email is verified before it stays on a list, and the cost of each data pull is quoted and approved before the pull.

**Why:** his words above; no further reason given. On file beside them: the Places sweep found companies but 1,548 of 2,254 had no named contact (`tasks.md`, Week 0), which is the gap bought data closes.

**Alternatives considered:** none stated. Until now lists were built by `scripts/places_seed.py` and its followers at about $130 a national sweep; one month of Apollo was an open question, never decided.

**Owner:** Jonathan Beach (the data company, whose account buys, the signals). The AIOS (the list-building skill's draft, the verification, the cost line on each install record).

## 2026-10-05 - The list: a Google Maps pull, Clay for the contact, five website signals

**Decision:** Jonathan (2026-10-05), on the list-building first cut: "The list is just a big pull from google maps api with a clay hookup for email, owner name, and linkedin url, and the few qualifications like reviews and website signals that they could use a new site, receptionist, email follow up, an appointment setter, and a proposal builder come next."
- The list starts as a Google Maps API pull (`scripts/places_seed.py`), not a bought contact file. This corrects the entry above.
- Clay is the data company: it adds the email, the owner's name, and the LinkedIn URL. The Apollo question open since September is closed by this.
- The qualifications are few: reviews, and website signals for five things a company could use: a new site, a receptionist, email follow-up, an appointment setter, a proposal builder.
- `/list-building` was written to this (`.claude/skills/list-building/SKILL.md`). The check behind each signal is the AIOS's first cut, his to change.

**Why:** his words above; no further reason given. The five signals name what the list is for: each yes is a reason to sell that company one of the agents.

**Alternatives considered:** the AIOS's first cut (buy LinkedIn and email rows from a data company, then enrich); `scripts/meta_seed.py` alone for owner names (free, an owner name on about one company in four, no owner LinkedIn).

**Owner:** Jonathan Beach (the Clay account, the signals, the review band, what the first pull searches for). The AIOS (the Clay hookup, the site checks, the cost quote before each pull). Open: where a receptionist sits among the 12 skills, and whether a client's list is pulled on Monarc's accounts or the client's own.

## 2026-10-05 - Butterfly: the CRM's logo is a button that opens the clone

**Decision:** Jonathan (2026-10-05, dictated; the word came through as "the claw" and the AIOS read it as "the clone"): "I'd like to make the claw a function of this and just call it butterfly. And it be a symbol of the butterfly logo. And it would just link directly to the chat we're currently having right now." Then, after five questions: "this is way too many questions. It should literally just be a button. That's the logo. When I click on the logo, there should just be three little options that I can select from. One is to run a skill, one is to create a new project, and one is to work on an existing project. Upon clicking on the projects one, I will get a list of the existing projects. That we're working on. A project can either be an artifact. It can be a campaign or it can be a skill."
- It lives in the Monarc CRM (his pick). The butterfly logo at the top left is the button; it replaced the blue M.
- Three options: Run a skill, New project, Work on a project. A project is an artifact, a campaign, or a skill.
- The project list holds the CRM's campaigns too (his pick), with the skills and the artifact groups.
- New project: a name and one line, then the chat opens with that line typed (his pick). A campaign also gets its row in the base as Planned.
- The name Butterfly is the CRM item only (his pick). The files and the chat still say the AIOS and the clone.

**Why:** his words above. One click from the CRM into the right chat, instead of finding the chat in VS Code.

**Alternatives considered:** its own Desktop window; a rail item with a full page; every folder under `projects/` listed; a blank chat with no form; a fuller form; the name carried into the instruction files.

**Owner:** Jonathan Beach. The AIOS (the menu, `scripts/crm_butterfly.py`). Limits, said plainly: a chat opens only in the VS Code window of the folder it was started in, so the server brings that window up first; the menu was checked in headless screenshots and dry runs, and the opening of a real chat had not been clicked when this was written.

## 2026-10-05 - Skills and workflows are two things

**Decision:** Jonathan (2026-10-05): "There should be skills and then workflows which are the deliverables like outreach, follow up, appointment setting and so on."
- A **workflow** is a deliverable a company gets. The 12 folded from his list of 50 are workflows: outreach, follow-up, appointment setting, and the rest (`references/agent-catalog.md`).
- A **skill** is a part a workflow is built from (`/list-building`), or one of the AIOS's own (`/inbox`, `/kickoff`, and so on).
- The names follow his words. `agent-outbound` is now `workflow-outreach`; the install record is `projects/clients/monarc-build/workflow-outreach.md`; `agent-booking` became `workflow-appointment-setting`; the other ten took `workflow-` in place of `agent-`. Entries above this one keep the names they were written with.
- A workflow is still kept as a skill file under `.claude/skills/` so the clone can run it. The `workflow-` at the front of the folder's name is what marks it.
- Butterfly shows the two apart: Run a skill has two tabs, Skills and then Workflows; Work on a project lists Workflows (all 12, written or not), Skills, Campaigns, Artifacts; New project offers all four.

**Why:** his words above. A workflow is what is sold and checked each month; a skill is reused across workflows and is not sold by itself.

**Alternatives considered:** one list of skills with the deliverables marked by a tag; a separate `workflows/` folder outside `.claude/skills/` (the clone could not run those by name).

**Owner:** Jonathan Beach (which is which, the names). The AIOS (the files, the menu).

## 2026-10-05 - Outreach test run to himself at $4,859 a month

**Decision:** Jonathan (2026-10-05): "Send me an invoice and a proposal." Asked what for and at what number, he picked a test run to himself at full price, then "$4,859 a month" (Account-Based Outbound on his list, the name closest to the Outreach workflow), billed monthly.
- The proposal (two pages) and an invoice preview (one page) for the Outreach workflow were drafted to him as the client: `projects/artifacts/proposals/2026-10-05-outreach-test/`, and one email in Proton Drafts with both attached. Not sent.
- This is the first price put on a workflow. It is the number for this test, not a locked offer: `context/offer.md` stays on hold and the price line in `references/mycopy.md` stays on hold until he writes the new offer.
- Carried from the 2026-09-15 agreement, his to change: billed on the first, due in 7 days, month to month with 30 days written notice, the client owns the list, messages, accounts, and data once fees are paid.
- The real invoice was not made. It belongs in Stripe; the connector's sign-in had lapsed, and the key on the machine is for reads only (`references/stripe-api.md`, the Intern Rule), so the AIOS did not write with it.

**Why:** his words above; to see what a client would be sent.

**Alternatives considered:** a $1 Stripe invoice paid and refunded (the dry run on the Stripe checklist, still open); a named prospect; templates only; $5,038 or $3,473 a month; a one-time fee with a smaller monthly fee.

**Owner:** Jonathan Beach (the number, the terms, the send). The AIOS (the documents; the Stripe draft once he signs the connector in and says go).

## 2026-10-05 - Stripe invoices can be made by the AIOS

**Decision:** Jonathan (2026-10-05): "Stripe invoices can now be made. Right privileges are now enabled on Stripe. The key stays able to write."
- The AIOS may make customers and invoices in Stripe. This replaces the read-only line in `references/stripe-api.md` for those two.
- Unchanged: only on his explicit ask; an invoice is a draft unless he says send; the AIOS charges and refunds nothing.
- First use, the same day: the test customer "Jonathan Beach (test run)" and one draft invoice for the Outreach test run, $4,859.00, not sent, not charged. His own are tests, so no row went into the Books.

**Why:** his words above; so an invoice can go out the day a client says yes.

**Alternatives considered:** writes only through the Stripe connector, with a click per write (the rule until today).

**Owner:** Jonathan Beach (the privileges, each ask). The AIOS (drafts on his ask, the read-back after each one).

## 2026-10-05 - The SDR is one skill; workflows live under skills; the pass is his approval of the copy

**Decision:** Jonathan (2026-10-05): "This would be an SDR role, because they do outbound and follow-up and appointment setting. I guess those are the main functions and should be lumped into one agent or one skill is the SDR skill... workflows would live underneath of skills. The SDR is not auditing the copy. That is a coach skill that we will bake in. But the SDR is the real build right now and cold outreach, lead form submission follow-up, stale proposal follow-up, I guess lead form submission follow-up is different from appointment booking, which would be a response function as well. The pass for this would be we go through each function and I approve that the copy matches what I would typically sound like."
- A skill is a role. A workflow is one thing the role does, kept as a file under the skill (`.claude/skills/<skill>/workflows/`). This replaces the entry "Skills and workflows are two things" above, where a workflow was a skill folder of its own.
- `/sdr` is the build now, with four workflows: cold outreach, lead form submission follow-up, stale proposal follow-up, appointment booking. `workflow-outreach` was folded into the first; its folder is gone.
- The SDR writes and sends approved copy. Auditing copy is the coach skill, later, not written.
- The pass is his approval, workflow by workflow, that the copy sounds like him. The counted checks written for outreach earlier (18 of 20 rows, the mail records, the rehearsal) stay as checks before a real send; they are not the pass.
- Cold outreach's copy v1 was drafted the same day for his read. Not approved.

**Why:** his words above. One role with its workflows under it is how the work is sold and how he thinks of it; the copy is the part only he can judge.

**Alternatives considered:** twelve separate workflow skills (the layout until this entry); a pass list of counted checks per workflow.

**Owner:** Jonathan Beach (each approval, when the coach is built, which role follows the SDR). The AIOS (the drafts, the files, the menu). Open: the nine other groups from his list of 50 are not placed under a skill.

## 2026-10-05 - The SDR works from patrick@monarcbuild.com and answers its inbox; how a cold email is built

**Decision:** Jonathan (2026-10-05), marking up cold outreach's copy v1:
- How he reads Email 1: "objection stealing, permission, angle, experience. Offer with a small ask. And then, footnote." The footnote goes: "The not for you reply stop and I won't write again is an opt-in that makes it sound automated. So X that."
- "Email number two should be just a new angle. Email number three should just be another new angle. Maybe use cost of inaction. That's the last one."
- LinkedIn: the connection note only establishes him, says he has an offer for their company and that he used to work in the space, with the experience stronger ("high end residential work"). The gap and the ask were "a little bit too much of an ask for the connection". "We can try different connect variations."
- "This SDR skill also needs to be baked in to respond to messages over my email inbox. This is going to be patrick@monarcbuild doing the SDR role for email. He left so we are repurposing this email."

What was done: copy v2 written to that (three connection notes to try; the gap and the ask moved to the message after they accept); a fifth workflow, inbox replies, added under `/sdr`; patrick@monarcbuild.com named as the SDR's mailbox.

**Why:** his words above.

**Alternatives considered:** keeping the stop line in his own words; follow-ups that point back at the first email; one connection note.

**Owner:** Jonathan Beach. Put to him by the AIOS, his to weigh: United States law on sales email asks for a way to say stop and a postal address in each one, and the stop line is now out; cold mail from patrick@monarcbuild.com rides on the main domain's name; Patrick left, so nothing may go out under his name and the name on the mailbox is his to set; the files still name Patrick as the sender of the LinkedIn messages. Not wired: reading and sending for that address.

## 2026-10-05 - Automated answers only for prospects in the pipeline; a response cancels the drip; copy is tested in his inbox

**Decision:** Jonathan (2026-10-05): "Only prospects in the pipeline get automated responses and a response cancels the drip sequence. Hit my inbox as if I were an integrator that took 2 days to respond to a form submission."
- The SDR sends an automated answer only to a prospect in the pipeline. The AIOS's reading of "in the pipeline": an open deal on the CRM's Pipeline board, or a row on a list the SDR is working. Mail from anyone else is sorted and left for him.
- Any response from a prospect ends every sequence that prospect is in.
- Copy is read the way a prospect would read it: he names the scene and one unread message is laid in his own INBOX from the SDR's address (`python scripts/proton_mail.py inbox-test`). It goes to no one; the script still never sends.
- First test, 2:06 pm: Email 1 to him as an integrator who took two days to answer a form fill. That line ("I filled out the contact form on your site last Wednesday. Your reply came Friday.") is a new row in cold outreach's copy and is only ever sent when it is true.

**Why:** his words above. An automated answer to a stranger is how a mailbox embarrasses its owner; a drip that keeps going after a reply reads as a machine.

**Alternatives considered:** none stated.

**Owner:** Jonathan Beach (what counts as in the pipeline, each read of a test). The AIOS (the check before any automated answer, the test sends). Open, his: whether the SDR fills out prospects' forms to time their replies, which the slow-reply line needs.

## 2026-10-05 - The SDR's inbox answers a question about times from the calendar and books the pick

**Decision:** Jonathan (2026-10-05), after answering the test email with "What is your availability this afternoon?": "there's currently no automation in place when I receive something in my inbox that automatically checks for the response and then automates a reply. So this one's asking about availability, which should be an automated response that checks my calendar's availability and then schedules for a meeting."
- Built: `scripts/sdr_inbox.py`. A reply on one of the SDR's threads cancels the drip and is sorted by plain rules. A question about times is answered with two open times read from his two calendars; a picked time is put on the calendar; stop blocks the thread; anything else waits for him.
- Sorting is by phrases in `projects/sdr/config.json`, no model, so a reply costs nothing to handle. A reply no rule fits is left for him, never guessed at.
- `send` and `book` are off, and the AIOS never turns them on (the same footing as Monarc Edge's dry run). On a test thread the answer is laid in his own INBOX and a pick makes a quiet hold; on a real thread the answer would go to Drafts.
- First run: his reply was answered at 2:18 pm with "This afternoon I have 3:30 or 4:30, Eastern." A watcher was started to pass once a minute; it stops when the machine restarts.
- Found on the way: patrick@monarcbuild.com is its own Proton sign-in, not an address on his. The watcher cannot see real replies until that mailbox is in Bridge.

**Why:** his words above. A person who asks for a time and waits a day has moved on.

**Alternatives considered:** a model to sort each reply (reads odd wording better; costs a little and can guess wrong with confidence); a booking link in place of two times; running the pass from the CRM server while the CRM is open.

**Owner:** Jonathan Beach (the two answers' copy, the hours, the phrases, turning `send` and `book` on, the mailbox sign-in). The AIOS (the watcher, the log). Not approved yet: the times offer and the booked note.

## 2026-10-05 - A booked prospect gets the meeting link on the thread and a confirmation of its own

**Decision:** Jonathan (2026-10-05), after answering "Book me for 3:30" on the test thread: "I got an email sent without the calendar link saying as a response to my request for a booking time it should just respond with the meeting link. I was also not sent a confirmation email."
- The answer on the thread is now the time and the Google Meet link and nothing else. The first version said "the invite is on its way with the link" and carried no link; on a test thread no invite comes, because he is both the calendar's owner and the guest.
- A confirmation goes with it as a message of its own, from "Monarc Build" with no person's name, using the first line of the site's own confirmation (`templates/booking-drip.md`).
- For a real prospect the Google Calendar invite from jonathan@monarcbuild.com is the third piece, once `send` is on.
- His booking stood: the hold was on his calendar at 3:30 pm and on the CRM's Today calendar. The two corrected messages were laid in his INBOX at 2:52 pm.

**Why:** his words above. The AIOS's reading: "request for a booking time" is his "Book me for 3:30", and "the meeting link" is the Google Meet link.

**Alternatives considered:** a booking page link in place of two offered times; the calendar file attached to the confirmation (skipped on a test, where it would double the hold).

**Owner:** Jonathan Beach (the three answers' copy, the meeting's title). The AIOS (the watcher). Not built: reminders for a meeting the SDR books, the deal moved to Booked, the notice to him.

## 2026-10-05 - A no-show is logged the same day and gets one email and one LinkedIn message

**Decision:** Jonathan (2026-10-05, 5:05 pm, five minutes into the Momentum Electrical Contractors meeting): "Report a no-show for Momentum Electric. So this needs to be tracked as well. And we need a protocol for the no show. Maybe it's just like a LinkedIn message and an email that gets sent."
- Tracked: the Booked step "show" on the company's file is answered No-show. It counts in the show rate on Reports and puts the company under "Waiting on you".
- The protocol is a sixth workflow under `/sdr` (`.claude/skills/sdr/workflows/no-show.md`): log it; read what went out before the meeting; one email the same day on the confirmation's thread with two new times in their zone and the same Meet link; one LinkedIn message the same day that points at the email; three business days; then rebooked, or closed with a reason. No drip after a no-show.
- The words name no cause: "we missed each other".
- The company's file shows the protocol as three more steps once No-show is answered (`when` on a step in `projects/crm/playbook.json`).
- Momentum: logged. The rebook email is in Proton Drafts (Tuesday at 10:00 or Wednesday at 11:30 Pacific); the LinkedIn line is drafted for him. Nothing was sent by the AIOS.

**Found while logging it:** Reports read this no-show against Loom variation A, though the Loom email was still in Drafts and the company never got it. Fixed: a Loom counts for a meeting only if it went out on or before the meeting's day. On the record for this meeting: the confirmation went out Oct 1; the Loom brief and the day-before reminder did not go out.

**Why:** his words above.

**Alternatives considered:** a longer rebook sequence; a call as the first touch; closing the deal on the first no-show.

**Owner:** Jonathan Beach (the two messages' copy, each send, the close reason). The AIOS (the log, the drafts, the steps on the file).

## 2026-10-05 - Every output short; every reply ends with two suggestions

**Decision:** Jonathan (2026-10-05): "In the text output write instructions make the language short and to the point." Then: "This should be made happen across all outputs and make a 2 suggestions to the goal of the projects after an output instead of the want me to refine draft 2 or move on."
- All outputs, chat and files alike: the next action first, one line per change, no report.
- The closing line "Want me to refine, draft v2, or move on?" is gone. Each reply ends with two concrete suggestions toward the goal of the project at hand.

**Why:** his words above.

**Alternatives considered:** none stated.

**Owner:** Jonathan Beach. The AIOS (`CLAUDE.md`, `AGENTS.md`, the memory).

## 2026-10-05 - No draft is placed twice

**Decision:** Jonathan (2026-10-05), after two chats each drafted a rebook email to Momentum within two seconds of each other: "Is there a check that email sends are not duplicates". There was none. Now `scripts/proton_mail.py draft` looks in Drafts and Sent for mail to the same address with the same subject (Re: and Fwd: stripped) in the last 7 days; a match stops the draft and lists what is there; `--force` places it anyway. The free campaign's deliveries and the SDR inbox's drafts go through the same check.

**Why:** his question above. Two chats share no memory of each other's drafts; the mailbox is the one record they both can read.

**Alternatives considered:** a shared log of every draft the AIOS places (would miss what he drafts by hand); a check on the body (two rewrites of the same email differ in words, not in who and what).

**Owner:** The AIOS. Jonathan picks which of the five Momentum drafts to send and deletes the rest.

## 2026-10-05 - The Loom brief has a script

**Decision:** Jonathan (2026-10-05): "draft the momentum message and the loom scripts are going to be a script as well."
- `templates/loom-brief-script.md`: the words for the Loom a booked prospect gets, built from his two Momentum Looms and his cut rules. Variation A is the full page review (about 11 minutes); variation B is the page reviewed and rebuilt (about 4 minutes). The Booked step on the company file opens it.
- The Momentum message v2 carries the rebuilt page's walkthrough; it is in `.claude/skills/sdr/workflows/no-show.md`, not placed in Drafts, because five drafts to Momentum are already there and the duplicate check would refuse it. He pastes it into one and deletes the rest.

**Why:** his words above. A script is what makes the Loom repeatable and its variations comparable.

**Alternatives considered:** none stated.

**Owner:** Jonathan Beach (the script's words, the upload of the owner's cut). The AIOS (the template, the record of variations).

## 2026-10-06 - Money out the AIOS knows goes into the book by itself

**Decision:** Jonathan (2026-10-06): "Can we also update my spend in the CRM to reflect any money out or in."
- `scripts/books.py spend-sync`: Google Ads spend by campaign and day from the Ads API, and the charges in `projects/books/known-spend.json`, into the Books Transactions table; dry run unless `--write`. The Money page reads the same table.
- A bank row for Google Ads is skipped by import-bank in a month that has the daily rows, so the same money is not counted twice.
- Money in: `stripe-sync` and the bank CSV, as before.
- Blocked today: the Books base is not on the Airtable token (403). His one click opens all of it.

**Why:** his words above. The month-end tally and the Money page were waiting on a bank CSV for every dollar; the Ads API and the AIOS's own bills can be read now.

**Alternatives considered:** waiting for the bank CSV alone; writing the known charges by hand in Airtable.

**Owner:** Jonathan Beach (the token, the bank CSVs, the receipt for the $1,990). The AIOS (the runs, `known-spend.json`).

## 2026-10-06 - Twenty a day, the same people on every channel

**Decision:** Jonathan (2026-10-06), after the lead-gen order was laid out (LinkedIn connect, then the call, then email, the Loom after a booking) and a 100-a-day avatar video idea was weighed against rebuilt pages in each brand: "I'll just do 20 a day along with connecting on LI and cold call but we do it for the same people across different channels."
- Twenty new companies a day enter the sequence; the same twenty get every channel: LinkedIn connect day 0, the call day 1, Email 1 day 2, the LinkedIn message day 4, Email 2 day 5, Email 3 day 8. A reply on any channel ends the rest.
- Email 1 carries the rebuilt page's link once the first batch of rebuilds exists; the Loom brief stays after the booking.
- `projects/sdr/config.json` holds the cap and the days; the sequence is in `.claude/skills/sdr/workflows/cold-outreach.md`.

**Why:** his words above. Twenty a day on three channels keeps the sending under the spam line, fits the dial hour, and makes every touch to a company land on a name they have seen.

**Alternatives considered:** 100 avatar videos a day (the rendering is cheap; the sending at that pace is not); the Loom in the cold sequence; email alone.

**Owner:** Jonathan Beach (the dials, the LinkedIn sends until a tool is wired, the twenty rows a day once the list exists). The AIOS (the emails from the SDR mailbox once wired, the record, the cancel).

## 2026-10-06 - Loom B and A is a skill of its own

**Decision:** Jonathan (2026-10-06): "We're going to make a skill called Loom B and A." One Loom in which he talks over a company's page becomes a video where each change shows the second he names it (variation A), or the finished page first, then who he is, then the changes, then the finished page (variation B). Under five minutes: "Three minutes is really really good." Then an email draft that carries the link, with subject lines and short bodies tested against each other.
- `.claude/skills/loom-b-and-a/` (the skill and three workflows), `scripts/loom_ba.py` (states, cut, record), `templates/loom-ba-email.md`, `projects/loom-b-and-a/`. Rules 8 and 9 in `references/content-rules.md`.
- Built on what is here: Playwright on headless Edge for the page states, ffmpeg for the cut, Parakeet for the words. He asked for "the latest and greatest tools"; the search (`references/hyperframes.md`) names HyperFrames (HeyGen, free, Apache-2.0, made for coding agents) as the step up for real motion. It needs Node, which this laptop does not have; installing waits on his go.
- A page is changed only in the browser's copy; the live site is never touched; nothing is typed into a form.

**Why:** his words above. A video that shows the change as he says it does the selling the page review does, in a third of the time, and a rebuilt first screen is the proof the cold sequence's Email 1 is to carry (2026-10-06, "Twenty a day").

**Alternatives considered:** a workflow under the social content skill (he named a skill); HyperFrames first (no Node here, and no install without his go); OpusClip (his verdict of 2026-10-05 stands).

**Owner:** Jonathan Beach (the Loom, the notes, the Node yes or no, the subject lines, the send). The AIOS (the plan, the states, the cut, the draft, the record).

## 2026-10-06 - Loom B and A runs as a batch SOP into the cold email channel

**Decision:** Jonathan (2026-10-06): "save all of these by date folders in a Loom B&A folder with the final stitches that get attached as links to the email drafts. When a batch is done I should get an email notification saying batch looms done and this is part of the SOP." Then: "these are also getting added to the cold email channel. Make a campaign update for this in airtable." And on the cut itself: his face on the same cuts (content rule 10), and every live change at the render's size (rule 11).
- Each audit gets a director's script before the edit; the cut lives in `media/loom-ba/<date>/<slug>/`; `scripts/loom_ba_batch.py` builds the index, a monarcbuild.com page a video, a Proton draft a company with the link, and the "Batch looms done" notice in his inbox (`.claude/skills/loom-b-and-a/workflows/batch.md`).
- The video pages are built locally and go live only when he says push; the drafts carry the links and must not be sent before.
- Airtable: campaign "Loom B and A: cold audits" (`recSBUxwNpumAhvYO`) on the Email channel, Planned, with outcomes and tasks.

**Why:** his words above. The video is the proof; the email only gets it watched, and a page on our own site can count the watches Proton cannot.

**Alternatives considered:** links to Loom (no upload API; each cut would be uploaded by hand); YouTube unlisted (about six uploads a day on the default quota); the video attached to the email (too large, and cold mail with a 30 MB file lands in spam).

**Owner:** Jonathan Beach (the email copy, the push, the send). The AIOS (the scripts, the cuts, the drafts, the notice, the campaign row).

## 2026-10-06 - Apollo is wired first for owner emails and LinkedIn

**Decision:** Jonathan (2026-10-06): "Do a free crawl and lets hook up a clay account or apollo." Apollo is wired first: `scripts/apollo_enrich.py` searches a domain's owners and founders for free and reveals the email and LinkedIn URL for credits, only with `--reveal --yes`. The free crawl ran the same day on the five batch companies with no address and found two (PHA sales@, VME victor@); both drafts are placed.

**Why:** Apollo answers a key over plain HTTP, and its owner search costs nothing, so the clone can quote before it spends. Clay sends enriched rows back to a script only on its Growth plan, about $495 a month.

**Alternatives considered:** Clay now (the Growth plan for the return path, or a hand export each batch); the free crawl alone (it stops at what a site prints).

**Owner:** Jonathan Beach (the Apollo account, the key, the go on each reveal). The AIOS (the script, the searches, the drafts).


## 2026-10-07 - His notes on the first Loom B and A batch become standing rules

**Decision:** Jonathan's 14 notes on the 10/6 videos apply to every video, not only the two he named (VME, Q Northwest). They are written as rules 12 to 24 in `references/content-rules.md`, into the page engine (`scripts/prospect_page.py`: the Google banner under the button, Google on every review, a header menu, a dark header when theirs is dark, three benefit cards, "Start your project", the calendar picture, the eyebrow as a brand shade, a white-on-dark hero), and into the cut engine (`scripts/loom_ba.py`: `header` and `click` steps; `scripts/loom_ba_rules.py` for final-version-only, banner versus section, the calendar, and the header).

**Why:** "I will leave notes on each video for where it went wrong so the SOP can be adjusted." A note fixed in one plan would come back in the next batch.

**Alternatives considered:** fixing only VME and Q Northwest; asking which notes were meant for every page.

**Owner:** Jonathan Beach (the notes, the go on the push and the drafts). The AIOS (the rules, the engines, the recut).
