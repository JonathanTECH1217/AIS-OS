# Stripe

Domain 1, Revenue / Financials. Started 2026-09-07 (Week 0, box 2). Business: Monarc Build, LLC, monarcbuild.com, digital marketing for custom home integrators. Products needed: Payments, Invoicing, Tax.

## Account facts (read live 2026-09-07)

- Account: `acct_1UDAOuRp9EARGZZs`, name "Monarc Build, LLC", live mode. The only account in the session; no sandbox listed.
- Products: none.
- Stripe Tax: status `pending`, missing `head_office`. No default tax code or tax behavior set.
- Activation: NOT activated. `charges_enabled: false`, `payouts_enabled: false`, `details_submitted: false`. Card and ACH capabilities inactive. No payout bank account attached. Account email jonathan@monarcbuild.com, timezone America/New_York, statement descriptor currently "MONARCBUILD.COM".
- **Read again 2026-10-05 with the restricted key: activated.** `charges_enabled: true`, `payouts_enabled: true`, `details_submitted: true`. Live mode, balance $0. Still empty: no products, customers, invoices, charges, or payouts. The 2026-09-07 lines above and below are the earlier read.
- Stripe's past-due list to activate: business type, MCC (industry code), product description, support phone, representative first and last name, date of birth, email, statement descriptor, terms of service acceptance. All of it is the Dashboard activation form.

## The short version

Two monthly retainers ($2,500 Level 1, $4,500 Level 2) with a 60 day pilot, then a 6 month term. This is a Dashboard setup, not a code integration. The AIOS reaches Stripe through the official MCP server for reporting and, with approval, for writes. No API keys live in this repo.

Boring is beautiful. Write a script only when a real need shows up that the Dashboard can't do.

## Planner-confirmed path (guide `iguide_61VMYs0D9c5riZcSE41Rp9EARGZZs`, accepted 2026-09-07)

Run through Stripe's implementation planner with the offer above. Choices and the docs for each:

| Area | Choice | Docs |
|---|---|---|
| Creating invoices | Dashboard, with an invoice rendering template for the repeated memo and footer. Subscriptions generate the monthly invoice; nothing is created by code. | https://docs.stripe.com/invoicing/dashboard#create-invoice · https://docs.stripe.com/invoicing/invoice-rendering-template |
| Invoice look | Branding: logo, color, footer, once in Settings. | https://docs.stripe.com/invoicing/customize#brand-customization |
| Collecting payment | Hosted Invoice Page. Client pays from the emailed link. No saved-card auto-charge at first. | https://docs.stripe.com/invoicing/hosted-invoice-page |
| Reconciliation | Dashboard only. No accounting system yet. Export CSV for the accountant. | https://docs.stripe.com/invoicing/dashboard |
| Subscriptions | No-code. Created per customer in the Dashboard with collection method "Send invoice" (the planner's no-code terminal is Payment Links, which cannot do sent invoices, so Dashboard subscriptions instead). | https://docs.stripe.com/billing/subscriptions/design-an-integration#select-billing-model |
| Pricing model | Flat rate. | https://docs.stripe.com/subscriptions/pricing-models/flat-rate-pricing?dashboard-or-api=dashboard |
| Billing model | Pay up front. The pilot is paid at full price, so no trial object. | same |
| Client self-service | Customer Portal: update payment method, view invoices. Cancel and plan changes turned OFF in the portal because Level 1 carries a 6 month term. | https://docs.stripe.com/customer-management/activate-no-code-customer-portal |
| Failed payments | Smart Retries plus automated emails, Dashboard defaults. | https://docs.stripe.com/billing/revenue-recovery |
| Sales-led sign-up | Quotes, optional. A quote sent after the sales call converts to the subscription on acceptance. Skip if DocuSeal handles the contract. | https://docs.stripe.com/quotes/create |
| Tax | Threshold monitoring to start (new LLC, no registrations known). Set head office and a service tax category. Switch to collection when registered in a state. | https://docs.stripe.com/tax/monitoring · https://docs.stripe.com/tax |

Two nuances the planner flagged:

- **ACH means ACH Direct Debit** (US bank account as a payment method on the hosted page), not "bank transfer" to a virtual account number. Bank transfer lands in a cash balance and needs manual reconciliation. Direct Debit reconciles on the invoice. ACH settles in 1 to 5 business days; "paid" is not cash in hand yet.
- **The 6 month term is a contract, not a Stripe object.** Price doesn't change at day 60, so no subscription schedule is needed. Cancellation is controlled by keeping self-cancel off in the portal and by the signed agreement.

## Objects to create

- Product `Level 1`, price $2,500.00 USD recurring monthly. Metadata: `tier=1`.
- Product `First Responder`, price $2,000.00 USD recurring monthly. Metadata: `tier=2-addon`, `standalone=no`. Added as a second line on the same subscription; dropped by removing the line at period end.
- No setup fee product. No trial. No pilot discount.
- Ad spend never enters Stripe. Client's own Google Ads account, their card.

## Setup checklist (Dashboard, in order)

1. **Activate the account.** Entity is Monarc Build, LLC. EIN, business address, payout bank account (same account as Week 0 box 1). Statement descriptor: MONARC BUILD.
2. **Payment methods.** Enable ACH Direct Debit (US bank account) and cards. ACH default on invoices. Fees: ACH 0.8% capped at $5; cards about 2.9% plus 30 cents. On $2,500 that's about $5 vs $73 per client per month.
3. **Products and prices.** The two above. The AIOS can create these through the MCP server with approval.
4. **Invoice template and branding.** Logo, color, footer with support email. One rendering template with the standard memo.
5. **Stripe Tax.** Set head office address. Pick the closest service tax category for both products (advertising or web design services). Leave collection off until registered somewhere. Confirm treatment with an accountant once, log it in `decisions/log.md`.
6. **Customer Portal.** On. Payment method updates and invoice history only. Cancellations off.
7. **First client.** Create Customer, start subscription, Level 1 line (plus First Responder if Level 2), collection "Send invoice", due on receipt, ACH and card allowed. Stripe emails the invoice and chases it.
8. **Dry run before the first real client.** Create yourself as a customer, send a $1 invoice or use the Dashboard's test mode, pay it, confirm the tax line and the PDF, then void or refund.

## How the AIOS reaches Stripe

Mechanism: `mcp`. Server `https://mcp.stripe.com`, configured in `.mcp.json`, OAuth through `/mcp`. Logged in 2026-09-07.

Reads: customers, subscriptions, invoices (open, paid, past due), balance, analytics. Used for the month-end money loop, client milestone dates (first invoice paid = Client 1 reward), and the owner dashboard later.

Writes: possible through the MCP server; the server asks for human approval on a URL for each write. Live mode. Rule: the AIOS proposes, Jonathan approves, then it writes. No writes to customers or invoices without an explicit ask.

Intern Rule: the MCP session carries the logged-in account's full permissions. If a script is ever needed, use a restricted key in the secrets file (gitignored), never in chat or in this file. Until 2026-10-05 that key was read-only; since then Jonathan has given it the right to make customers and invoices (Status, below).

## Status

- [x] Account activated (charges and payouts enabled; read 2026-10-05)
- [ ] ACH Direct Debit and cards enabled, ACH default
- [ ] Products and prices created
- [ ] Invoice template and branding set
- [ ] Stripe Tax head office set, service tax category chosen, threshold monitoring on
- [ ] Customer Portal on, cancellations off
- [ ] Dry run invoice paid end to end
- [x] MCP connected and planner run (2026-09-07). The login had lapsed by 2026-10-05; `/mcp` signs in again.
- [x] `STRIPE_SECRET_KEY` (restricted, `rk_live_`) in `%USERPROFILE%\.monarc\secrets.env` (2026-10-05). Reads tested: balance transactions, charges, payouts, invoices, customers, products, balance, account. Whether it can write was not tested.
- [x] **The key writes (2026-10-05, 12:2x pm).** Jonathan asked for an invoice sent to himself as a test, was told the connector had lapsed and the key was read-only by the Intern Rule above, and answered "updated". The AIOS read that as the key being allowed to write and tried: it made customer "Jonathan Beach (test run)" (`metadata.test=true`) and one **draft** invoice, `in_1UNEeTRp9EARGZZsaNdDuv74`: one line, "Outreach, month one", $4,859.00, send-invoice, due in 7 days, `auto_advance` off so it never finalizes or emails by itself. Not sent, not charged. These are the first objects in the account. It is a test: no row goes in the Books Invoices table, and it is deleted or voided when he has looked. **Decided, Jonathan, 2026-10-05:** "Stripe invoices can now be made. Right privileges are now enabled on Stripe. The key stays able to write." So the key on this machine may make customers and invoices, and this replaces the read-only line in the Intern Rule above for those two. What does not change: a write happens only on his explicit ask, an invoice is made as a draft unless he says send, and nothing is charged or refunded by the AIOS.

Last checked: 2026-10-05.
