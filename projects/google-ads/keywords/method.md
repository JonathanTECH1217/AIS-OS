# Keyword research method

One track per service line, six in all. The AIOS drafts and expands; Jonathan validates in Keyword Planner (decision 2026-09-25). Output per track: `keywords/<service>.csv` with a status on every row, the shared and campaign negatives, and the h1 target term for the page.

## Steps

1. **Seeds (AIOS).** 8 to 12 per service line, written as a contractor types them. The starting lists are in the campaign briefs (`campaigns/NN-*.md`, "Target term and ad groups").
2. **Modifier matrix (AIOS, stdlib one-off).** `[channel word] x [trade word] x [intent word]`, every combination to the CSV with `source=matrix`. Channel words per service (Google Ads: google ads, ppc, adwords, paid search, search ads; website: website design, web design, website, landing pages; SEO: seo, local seo, google business profile, gbp, search ranking, aeo; email: email marketing, email automation, drip campaign, email sequence, lead nurture; Facebook: facebook ads, instagram ads, meta ads, social media ads, facebook advertising; automation: ai automation, automation, ai receptionist, missed call text back, invoicing automation, bookkeeping automation, proposal automation). Trade words: av company, av integrator, home automation company, smart home installer, home theater company, low voltage contractor, integrator, electrician, electrical contractor, hvac company, heating and air, roofing company, roofer, plumber, plumbing company, contractor, home services. Intent words: agency, company, management, services, marketing, lead generation, leads, for. Most rows will show zero volume and get parked; that is what the Planner run is for.
3. **Expansion by web research (AIOS).** For each seed: the organic SERP titles (agency phrasing); the "People also ask" questions (compare and learn tiers); forum threads where contractors ask about marketing (r/CEDIA, r/electricians, r/HVAC, r/Roofing, r/Plumbing, ContractorTalk, CE Pro comments) for pain phrasing; competitor agency pages (One Firefly; Hook Agency, Blue Corona, Scorpion, RYNO, Contractor Dynamics, Roofer Marketers) read for their titles and h1s, never copied. Autocomplete has no clean read path; the Planner's "Discover new keywords" stands in.
4. **Keyword Planner (Jonathan, about 20 minutes per line).** Two runs per line, US, English, last 12 months. "Discover new keywords": up to 10 seeds from the CSV plus `https://monarcbuild.com/website-build/` as the page; export. "Get search volume and forecasts": the whole matrix pasted; export. Both files to `keyword-planner/`, dated (`2026-10-DD-<service>-discover.csv`, `-volume.csv`), untouched. The AIOS merges by keyword into the `planner_*` columns.
5. **SERP read (Jonathan, top 20 buy-now terms per funded campaign).** Search the term in his own Chrome, screenshot the top of the results page into `serps/`; the AIOS records `serp_ad_count` and `serp_advertisers`. By hand, because scripted Google queries break Google's terms.
6. **Tier and status (AIOS, Jonathan approves Tier 1).** See the tiers and the exclusion order below.
7. **The h1 target term per page**: the highest-volume approved buy-now term whose phrasing is natural in 8 words. Handed to `projects/Landing Page Build/pages/<slug>.md`.

## The keywords per campaign (2026-09-28)

Jonathan first cut each campaign to about 5 keywords ("the few keywords responsible for the highest intent conversions"), then widened it the same day: "5 was too hard a limit. Let's expand that a bit to make more positive keywords available to get clicked on." About 12 per campaign now, each in exact and phrase: every trade gets at least one, and the core trades get a second wording (agency, company, services, management). The picks and a short bench sit in `picks.json`; every one is a row in its CSV.

**Picked on buying intent, no volume tool** (Jonathan, 2026-09-28): "just go based on transactional assumptions for high-intent buyers." His example: an AV installer bids "whole home audio installation" into a whole home audio page. The searcher names the exact thing they would pay for, and the ad lands on the page that sells it. A keyword makes the list when it has all three:

1. **The trade that buys**: av integrator, home automation or smart home company, electrician, hvac, roofing, plumbing, contractor, home services.
2. **The service they would hire, said as a service**: google ads management or agency, ppc management, website design, seo company or agency or services, email marketing services, facebook ads agency or management, ai automation agency, back office automation, lead follow up service. A bare channel plus a trade ("google ads for electricians") is out: guides own that search.
3. **One page that sells exactly that**: the campaign's own service page, so the ad, the keyword, and the h1 say the same thing.

Out, whatever the wording: how, what, best, top, cost, price, vs, tips, guide, examples, template, software, tool, app, jobs, course, free.

The mix per campaign: integrator terms first (the offer and the proof are built for them), then electricians, HVAC, and a contractor or home services catch-all that carries roofing and plumbing. The AI automation list has no integrator term: "av" and "automation" together pull commercial AV and factory controls.

The DataForSEO volume check built the same day was dropped before it ran (`archives/dataforseo-check-2026-09-28/`). **The live search terms are the check:** after 14 and 30 days of spend, the morning read-back shows what people actually typed; a keyword that spends without booking goes out for the next bench term, and a search term that books comes in. **Nothing is final until Jonathan locks the list.**

## The CSV

`keyword, service, trade, intent, searcher, match_type, source, planner_avg_monthly, planner_competition, planner_bid_low, planner_bid_high, serp_ad_count, serp_advertisers, status, ad_group, landing_page, notes`

- `intent`: buy, compare, learn. `searcher`: contractor, homeowner, jobseeker, learner, vendor. `match_type`: exact, phrase, broad, negative. `source`: seed, matrix, serp, paa, forum, competitor, planner. `status`: candidate, approved, negative, parked.

## Tiers

| Tier | Signals in the query | What it gets |
|---|---|---|
| Buy now | agency, company, management, services, hire, "for [trade]" with a channel word, "near me" with a marketing word | Exact and phrase in the main ad groups; the headline mirror |
| Compare | best, top, reviews, vs, pricing, how much does it cost | Phrase only, in a "compare" ad group with a proof-led ad; funded once campaign 01 has data |
| Learn | how to, tips, guide, examples, template, checklist, what is, diy | Negative at launch; a content candidate for the SEO page |

## Exclusion order

1. Homeowner intent: install, installer, installation, repair, replacement, cost to install, near me without a marketing word, hire an electrician. The trap: "home automation company" is a homeowner; "google ads for home automation companies" is the contractor. Every approved term carries a channel or marketing word or a "for [trade]" phrase.
2. Job seekers: jobs, hiring, salary, career, resume, intern.
3. Learners: course, certification, training, tutorial, class, free, template, how to, what is.
4. Vendors and software: software, tool, app, crm, platform, saas, zapier, hubspot. A watch term, not a negative, inside the automation campaign only, where "software" is ambiguous.
5. Wrong country: canada, uk, australia, india, philippines, ontario, london.
6. Labor shoppers: white label, reseller, for agencies, freelancer, upwork, fiverr.
7. Under 10 searches a month: parked, or kept as exact in a "low volume" ad group when clearly buy-now.

"near me" is not a blanket negative: "google ads agency near me" is a contractor wanting a local agency.

## The head-term risk

"google ads management", "ppc agency", "facebook ads agency", "website design company", "seo company" run $20 to $60 a click with ten national agencies on the page. Monarc never bids the head term. The counter, in order: by trade ("google ads for av integrators"), by outcome ("more high ticket installs"), by pain ("missed calls in the field"), brand-adjacent trade terms ("control4 dealer marketing", "lutron dealer leads"), exact and phrase only until 30 conversions, the term-headline-h1 mirror for Quality Score, and the line the big agencies cannot say ("Built by a low voltage guy"). The automation terms are owned by SaaS products (Ruby, Smith.ai, Podium, Jobber) whose searcher expects a price the page cannot show; that line runs as a test, not a pillar.
