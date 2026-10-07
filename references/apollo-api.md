# Apollo API

The owner's email and LinkedIn for a company, by its domain. Jonathan, 2026-10-06: "lets hook up a clay account or apollo." Apollo was picked over Clay for the hookup: Clay takes rows in by a table webhook on any plan, but sending enriched rows back out to a script takes its HTTP API, on the Growth plan (about $495 a month); Apollo answers a key over plain HTTP. Clay stays the right tool for a big list built inside its own tables (`connections.md` row 22).

Script: `scripts/apollo_enrich.py` (check, search, batch).

## The two calls

| Step | Endpoint | Cost | Gives |
|---|---|---|---|
| Find the owner | `POST https://api.apollo.io/api/v1/mixed_people/api_search` with `q_organization_domains_list[]` and `person_seniorities[]` (owner, founder, c_suite, partner) | free, no credits | id, first name, title, `has_email`; no email |
| Get the email and LinkedIn | `POST https://api.apollo.io/api/v1/people/bulk_match` with `details: [{"id": ...}]`, 10 a call | credits | `email`, `linkedin_url`, `title`, `organization` |

Headers: `X-Api-Key`, `Content-Type: application/json`, `Cache-Control: no-cache`. The search needs a master key or one scoped to `mixed_people/api_search`; a free account needs a work email to use it. Sources: [Enrich people data](https://docs.apollo.io/docs/enrich-people-data), [People API search](https://docs.apollo.io/reference/people-api-search).

## Plans (read 2026-10-06, third-party pages; check the live page before buying)

Free: 100 credits a month, **no API access**: checked 2026-10-07 with his key, Apollo answered 403 "not included in your Free plan... All paid plans include full API access." On free, emails are revealed by hand in Apollo's web app. Basic: about $49 a seat a month billed yearly (about $59 month to month). Professional: about $79 billed yearly. Credits do not roll over. Sources: [zeliq.com](https://www.zeliq.com/blog/apolloio-pricing), [11x.ai](https://www.11x.ai/guides/apollo-io-pricing).

## Setup, his part

1. Sign up at apollo.io with jonathan@monarcbuild.com. The API needs a paid plan (Basic is the least); the key is in `secrets.env` since 2026-10-07 on the free plan.
2. Settings, Integrations, API, create a key with access to People Search and People Enrichment (or a master key).
3. Put it in `%USERPROFILE%/.monarc/secrets.env` as `APOLLO_API_KEY=...`. Never in chat.
4. Then `python scripts/apollo_enrich.py check`.

## Rules

- The search is free and runs without asking. A reveal spends credits: the script quotes the count and runs only with `--reveal --yes`, on his go.
- What comes back is saved once in `projects/research/<slug>/apollo.json`; a company is never revealed twice.
- An email found here is a business contact for one cold email from his own mailbox, inside his 20 a day; no list is bought or resold.
