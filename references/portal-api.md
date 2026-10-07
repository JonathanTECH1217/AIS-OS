# Portal (portal.io): getting proposal data out

Researched 2026-09-09. Not connected. Portal is the proposal and quoting tool many Monarc prospects run on (`context/icp-brands.md`, Business software). This page records the three doors out of it, so the AIOS can capture a client's proposal data for lead-to-revenue reporting without re-researching.

## Three doors

| Door | What you get | Gate | Effort |
|---|---|---|---|
| Public API (`api.portal.io`) | Everything: list and search proposals (filter by status, contact, date, text; paginated), full proposal detail with totals, every line item with qty, sell price, supplier cost, MSRP, area and option, client and installer notes, change orders, contacts, locations, catalog | Unlimited plan only. App key and secret come from a Portal rep. Production access is reviewed, not automatic. Sandbox at sandbox.portal.io | Half a day to wire once keys exist |
| Webhooks and Zapier | Push on events: proposal status change (sent, accepted, declined), payment status, order status, change order status, contact modified | Zapier trigger is native; API webhook subscriptions need the API above | An hour in Zapier or a small script |
| In-app downloads | Per proposal: client PDF, installer version, pick list, CSV | Any plan, manual | One proposal at a time. No bulk export documented |

## API mechanics

- Base URLs: `https://api.portal.io` (prod), `https://sandbox.api.portal.io` (sandbox).
- Auth: exchange the Portal username and password at `GET /authenticate/apikeyexchange` for a User API Key. Send `X-MSS-API-APPID` (app key) and `X-MSS-API-USERKEY` on every call and sign each request with HMAC-SHA256 using the secret.
- Proposals: `GET /public/proposals` (list and search), `GET /public/proposals/{ProposalId}` (detail, totals inside), items under `/public/proposals/{ProposalId}/items`. Change orders: `GET .../changeorders` per the docs index.
- Webhook subscriptions: create, list, update, delete. Event reference page lists proposal status, payment status, order status, change order status, contact modification, AI build events.
- Docs: https://docs.portal.io/ (index at https://docs.portal.io/llms.txt, Postman collection available). Support: support@portal.io.
- Zapier triggers, exact names: Update Proposal Status, Update Payment Status, Update Order Status, Update Change Order Status, Contact Modification. No Portal actions on Zapier (no create or find).

## Why Monarc cares

The weekly PDF promises the client "booked appointments with high ticket prospects." Proposal data closes the loop: form fill, First Responder call, booked appointment, Portal proposal sent, proposal accepted, dollar value. That last step is the number the client renews on, and it is the number Jonathan's own proof is built from ($2.5k of ads to a $91k job).

Minimum viable version: one Zap on "Update Proposal Status" filtered to Accepted, writing proposal name, client, total, and date to the tracking sheet's Money or Leads tab. Match on client email or name against the lead log. No API keys, no Unlimited plan needed if the client already has Zapier.

Full version: API pull nightly for every proposal (status, total, items, salesperson, dates) into a per-client table. Needs the client to be on Unlimited and to request keys from their Portal rep.

## Where it plugs in

- Kickoff questionnaire (`tasks.md`, Week 0): add "Which proposal tool? Portal, D-Tools, Jetbuilt, Simpro, ProjX360, or none. Will you add Monarc to Zapier or share API keys?"
- `connections.md`: add a row per client tool once the first client is on. Mechanism `key+ref`.
- Jonathan's own past proposals (the three proof jobs) live in a former employer's Portal account. Nothing here reaches them; the values are already recorded in `context/about-business.md`.

## Open

- Whether Zapier triggers are gated to a plan tier (the API access article gates the API to Unlimited but lists Zapier as a native integration without a tier).
- What fields the "Update Proposal Status" trigger carries. Not documented on Zapier's page; test with a sandbox account.
- Rate limits: not published.
