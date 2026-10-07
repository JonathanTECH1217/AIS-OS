# About the business

Filled by `/onboard` on 2026-09-07 from `aios-intake.md` Q1 and Q4. Edit the intake and re-run `/onboard` to refresh.

## Monarc Build

**Legal entity (Articles of Organization, shared by Jonathan 2026-09-15):** Monarc Build, LLC, a Maryland limited liability company. SDAT department ID W27446186. Filed 2026-06-18 11:15 AM, acknowledgment 5000000013308092, form SDAT40.2. Principal office and resident agent address: 3074 Riva Rd, Riva, MD 21140-1318. Resident agent and authorized person: Jonathan Beach. No state or local business license required (item 3). The filed PDF and the IRS EIN letter (CP 575 G) are in `records/entity/` (git-ignored; index in `records/README.md`, which also carries the filing and tax dates: Maryland Annual Report every April 15, quarterly estimates, 1099s by January 31). The EIN is on the letter only, never in a tracked file or in chat. Use the exact name "Monarc Build, LLC" (with the comma) on contracts, invoices, the bank account, and Stripe. Governing law on the Pilot Service Agreement is Maryland, which matches.

Monarc Build sells managed Google Ads, SEO, and web management to home integrators (low voltage, AV, smart home) who serve the residential market in high profile homes. The brands and software those integrators spec and run on are listed in `context/icp-brands.md`. The public site's current state and its mismatches with the offer: `context/website.md`. Money: Stripe is the card processor and invoicing tool (connections row 1, live account, not yet activated). The books are an Airtable base, "Monarc Books" (Accounts, Transactions, Invoices, Months), run by `scripts/books.py` and read by the CRM's Money page; guide in `references/books.md`. QuickBooks is the later step, at about fifteen clients or when a tax preparer asks for a full ledger. Business bank account: not yet opened (2026-09-16).

## Offer

**Superseded 2026-09-15.** The offer is now the Pilot Service Agreement (60-day Google Ads pilot, $2,000/mo management with a $1,000/mo match, $2,000/mo ad spend to Google, then $2,500 plus $2,000 month to month; $3,000 onboarding fee waived for signatures by September 30, 2026). Canonical page: `context/offer.md`. The bullets below are the 2026-09-07 version, kept for history. Source interview: `brainstorms/2026-09-07-offer-doc.md`.

- Headline: booked appointments with high ticket prospects.
- Level 1, $2,500/mo plus client-paid ad spend ($1,000/mo minimum recommended): website (new build or HTML takeover onto Monarc hosting), one landing page per service and per service area, managed Google Ads, SEO (local, GBP, content, technical), weekly emailed PDF report, monthly 15 minute meeting.
- Level 2, $4,500/mo: Level 1 plus First Responder, a human who calls every lead within 5 minutes (9am to 7pm Eastern, Mon-Fri), emails a follow-up, qualifies on pricing floor and service area, and books into the client's calendar. Month to month; never sold alone.
- 60 day pilot on Level 1, no setup fee, $1,000 matched ad spend. Day 60: 6 month term or walk; client keeps the site, landing pages, and reporting data.
- Kickoff: one meeting with a questionnaire script (services, brands per service, pricing floor, service area, calendar access).
- Proof point: ranked a client #1 for "whole home audio in Annapolis", which led to a $90k+ James Loudspeaker sale and $500k+ LTV from one contractor. The client is Performance Home Automation (PHA), pha.systems, 2014 Renard Ct, Annapolis MD (identified 2026-09-09 from a "PHA Brief" in Sent and the live page "Whole Home Audio Installation in Annapolis, MD | PHA"; confirmation from Jonathan pending). The page still ranks in the top results as of 2026-09-09. **Jonathan's rule (2026-09-09): never name PHA or link pha.systems in outreach or on monarcbuild.com; the site's design would undercut the proof.** State the ranking and the result; show data on the call; offer the owner as a reference only with permission.

## Proof jobs (values from Jonathan, 2026-09-09)

Three jobs from his time at the Annapolis integrator, with the winning proposal values. Values are shareable in his words; the proposal documents are not sent to prospects (they carry the integrator's name and homeowner details).

| Job | Value | Scope | Photo / media |
|---|---|---|---|
| Waterfront great room | $91k | Lutron Ketra lighting job (the "$90k install" in the Derich and Criteria emails) | `assets/hero/hero-waterfront.jpg` (rendered), raw IMG_2485 |
| Georgian Colonial restoration | $69k | Whole home audio, James Loudspeaker indoors and out, wired from rough-in | `assets/hero/hero-rough-in.jpg`, `assets/georgian/exterior-01.jpg`, rear deck `assets/projects/colonial-rear-deck-01.jpg` (identity of that deck unconfirmed) |
| Baltimore city penthouse | $51k | Control4 and Lutron retrofit | 39s handheld night walkthrough video (`projects/outreach/high rise.mp4`), two frames in `assets/projects/` |

Values corrected by Jonathan 2026-09-23 in the /avmarketing live loop: the Georgian is $69k (was $70k) and the penthouse $51k (was $50k). The homepage, `context/offer.md`, and `references/mycopy.md` still print $70k and $50k; align them when he says. The $500k lifetime line came off the ad page the same day (his call); the figure stands here for the call and the emails.

**Ranking claim for the ad page (Jonathan, 2026-09-23, his words, tidied):** Monarc has ranked companies on the first page for terms including whole home audio, lighting control, home theater design, access control, security systems, outdoor audio, landscape lighting, and more. Broader than the single Annapolis #1 above; no per-term evidence is on file in the AIOS. Show the data on the call.

Proof pack for ads (built 2026-09-09, sent to Patrick as a Proton draft the same day): `projects/outreach/proof-pack/`. Real photos only, nine files: Georgian exterior and rough-in originals, the waterfront great room cropped from a phone screenshot (1107x1895, soft), the penthouse walkthrough compressed to 5 MB, and five stills pulled from it (720x1280). Two PHA exposures to handle before public use: a PHA logo on a shirt in the rough-in photo, and the installer's face plus PHA polo at seconds 12 to 16 of the video. The hero renders in `assets/hero/` are not proof. Rear deck (identity unconfirmed) and farmhouse (no value) left out.

Open inconsistency to resolve: the website proof section and `context/offer.md` say the Georgian contractor "bought over $90k in James Loudspeaker." Per the table, the colonial was $70k and $91k was the Ketra job. The $500k+ lifetime figure is the contractor relationship across jobs. Jonathan decides the wording; then the site and the offer doc get corrected together.

## Proposal dataset from the Annapolis integrator (added 2026-09-09)

Jonathan exported 404 Portal proposal CSVs (proposals #115 to #735, Sep 2024 to Aug 2026) from the integrator's account. Filed in `projects/proposals-pha/` (gitignored: homeowner names and the integrator's costs are inside). One workbook, a JSON summary, and `findings-2026-09-09.md` for the marketer. Headline: $10.5M proposed across 308 live versions; lighting control is the high ticket system ($47k median as headline), whole-home bundles are 54% of residential dollars, builder-attached budgets median $52k against $10k for the rest, a quarter of proposals are under $5k and carry 2% of dollars. Use the findings for landing page terms, ad copy, and the pricing floor. Never quote a client name from it.

## Active conversations (seen in the Proton inbox 2026-09-08, not yet confirmed by Jonathan)

- **WH Smart Home / WH Technologies (Dallas area):** Joey Milot, Captain of Operations, 972 521 1208, joey@whsmarthome.com; Johann Whitehouse, johann@whsmarthome.com. Johann accepted a Google Meet for Tue 2026-09-08 1:30 to 1:45pm EDT. At 1:36pm EDT Joey wrote "We have a scheduled meeting for now but no one else is on yet." This is the prospect who was about to review the website. Status of that meeting: unknown.
- **Criteria of Naples (Naples, FL):** smart home and AV integrator serving Southwest Florida. Dealer for Lutron, Vantage, Crestron, Control4, Savant, Sony, Hunter Douglas, Ubiquiti, Origin Acoustics, Sonance, SnapAV, SunBriteTV, Sonos, Stealth Acoustics, JBL Synthesis, Coastal Source, Leon. Contacts James, Don, Chris (criteriaofnaples.com), 239.593.1700, 6220 Taylor Rd Suite 106. Site is a single page, no service pages, no team or testimonials, phone hours 8 to 4. Added 2026-09-09; the three need convincing that $2,500/mo yields more high ticket work.
- **Digital Living (Bay Area):** Derich Marsh, derich@digitalliving.com. Thread "Luxury builder partner acquisition services for the Bay Area," Aug 20 to 24, six replies. The B2B outreach offer, since scratched.
- **Shade Shop:** logo files attached to the Aug 20 Bay Area thread; relationship unclear.
- **Patrick Beach (patrick@monarcbuild.com):** forwards Google Ads billing notices to Jonathan (Sep 1, "Payment was declined for 418-577-4900"); is CC'd on every website lead; owns the architectural style library in Drive as patrickbeach12@gmail.com. **Role confirmed by Jonathan 2026-09-23: account management.** He was named on the /av_marketing/ team block for part of that day; the block came off the page the same day (no team photos).
- **Riley Palmer:** account manager (Jonathan, 2026-09-23). Named on the /av_marketing/ team block for part of that day; the block came off the page the same day. No email, phone, or photo on file. Whether Patrick and Riley are staff or contractors: Jonathan has not said; the "runs it solo" line in `CLAUDE.md` and `context/about-me.md` stands until he does.
- Proton folders "Permit Data" and "Assessment Roll" hold the county permit and assessor exports from the July public-records request campaign (about 50 counties emailed 2026-07-20).

Not offered: B2B referral-partner outreach (the Excel workbook spine and broker permit monitoring from earlier proposals). Too much overhead. Private quote of $10,000/mo only if a client insists.
