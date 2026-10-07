# The money book: Airtable base "Monarc Books"

Written 2026-09-16. Base id `appWhmipZx6UGHiqT`, workspace "My First Workspace" (same account as Monarc CRM). Kept as its own base so the CRM's 1,000-record cap is not spent on transactions. Read and written by `scripts/books.py` and read by the CRM's Money page (`/api/money`). The same `AIRTABLE_PAT` works once this base is added to its access list at airtable.com/create/tokens.

Why Airtable and not QuickBooks: decision 2026-09-16 in `decisions/log.md`. Stage 1 books. QuickBooks (it has the API; Wave does not) is the move at about fifteen clients, or when a tax preparer asks for a double-entry ledger; the Transactions export is the migration.

## Tables

| Table | id | What it holds |
|---|---|---|
| Accounts | `tblnyj8bGlzihuxJY` | The labels. Name, Type (Revenue, Cost, Asset, Equity), Tax line (the Schedule C line for the preparer), Active, Notes. Seeded with the agency chart below. |
| Transactions | `tbluCHtJftYdHps3r` | The book. Memo (primary), Date, Amount (money in positive, out negative), Counterparty, Client, Source (Stripe, Bank CSV, Manual), External id (dedupe key), Receipt (attachments), Reconciled, Notes, Account (link). |
| Invoices | `tblrVz8YvcsvqxItk` | Number, Client (link to Clients, since 2026-09-28; the old text column is "Client (old text)", empty, safe to delete), Amount, Issued, Due, Paid on, Status (Draft, Sent, Paid, Late, Void), Stripe invoice id, Deal, Notes, and three formulas the Clients rollups sum: Billed amount (not Draft or Void), Paid amount (Status Paid), Open amount (Sent or Late). Stripe sends and collects; this mirrors it. |
| Clients | `tblvn0CEhaOosGZef` | Added 2026-09-28 (Jonathan: the Books base as "a reflection of the CRM", the money side). One row per won deal in Monarc CRM, written by `scripts/crm_server.py` (`sync_books_clients`) when a deal is saved at Won and on every Money page load; matched on CRM deal id. The CRM owns Client, Monthly fee (the deal's Value), Offer, Signed on (the day the stage changed, set once), Source, CRM deal id, CRM company id; Status (Active, Paused, Ended) and Notes are Jonathan's and never overwritten. Invoices link here; rollups Invoiced, Paid, Open. The Money page shows monthly recurring (active fees) and the table. |
| Months | `tblVfW4s092CR1Mwg` | Month (YYYY-MM), Revenue, Costs, Profit, Salary paid, Invested, Cash at month end, Clients, Hours per client, Tally done, Notes. One row per month-end run. |
| Recurring | `tblL9HmU8ophvrEVU` | Added 2026-09-28 (Jonathan: "add a new expense, recurring monthly, for LinkedIn"; he picked this base over a new "Bookkeeping" base). One row per repeating expense: Name, Monthly cost, Billed (Monthly, Annually), Charge amount (what hits the bank each time), Next charge, Account (link), Active, Notes, Yearly cost (formula, Monthly cost x 12). The list, not the book: each charge still lands in Transactions from the bank CSV. Rows: LinkedIn, $19.99/mo billed annually ($239.88), Software. |

Rule: never a bank account number, routing number, card number, or the EIN in any field. Amounts, dates, and names only.

## The chart (Accounts)

Revenue: Management fees, Setup fees, Ad spend passthrough (off unless a client ever pays ads through Monarc). Cost: Advertising (Monarc's own), Software, Contractors (1099 at $600), Professional services, Fees (Stripe, bank), Home office (year end only), Travel, Meals (50 percent). Asset: Business checking, Stripe balance (a payout is a transfer between these two, not revenue). Equity: Owner draw (salary and ladder rewards), Owner investment.

## The monthly routine (fifteen minutes, last business day)

1. Export the month's bank statement as CSV from the bank site. Save the PDF statement as `records/bank/YYYY-MM-statement.pdf`.
2. `python scripts/books.py stripe-sync` (needs `STRIPE_SECRET_KEY` in `secrets.env`). Charges, fees, refunds, payouts land in Transactions with their Stripe id.
2b. `python scripts/books.py spend-sync`, then `--write` (added 2026-10-06; Jonathan: "update my spend in the CRM to reflect any money out or in"). Money out the AIOS can read itself: Google Ads spend by campaign and day from the Ads API (External id `gads:<campaign>:<date>`, Account Advertising), and the charges in `projects/books/known-spend.json` (API bills, courses, anything known before the statement; add a row there when a charge is known). Dedupe on External id. In a month that has the daily Ads rows, import-bank skips the bank's Google Ads charge so it is not counted twice. The CRM's Money page reads the same Transactions, so it shows the spend the moment the rows are in.
3. `python scripts/books.py import-bank <csv>` shows every new row with a proposed label. Read it. Then run again with `--write`. Rows with no label are saved unlabeled: pick the Account in Airtable.
4. In Airtable: attach the receipt to any row over $75 (photo or PDF onto the Receipt field); tick Reconciled as you match rows to the statement. Stripe payouts arriving in checking are the Stripe balance account, not revenue.
5. `python scripts/books.py month-end YYYY-MM`, then `--write`. It prints revenue, costs, profit, the salary and invest lines from the two money rules, open invoices, and the counts of unlabeled and unmatched rows. Copy the tally into `tasks.md`.
6. The Money page in the CRM shows the same numbers and the months side by side.

The two money rules live in `projects/crm/config.json` under `books`: `salary` (monthly dollars) and `invest_pct` (percent of profit). Until Jonathan writes and logs them (`tasks.md`, Week 0), the tally says "rule not set" instead of guessing.

## Invoicing

Stripe Invoicing sends the invoice and collects the card or ACH payment (`references/stripe-api.md`). After each invoice, add its row to Invoices (Number, Client, Amount, Issued, Due, Stripe invoice id, Deal). When Stripe marks it paid, set Paid on and Status. `stripe-sync` brings the payment into Transactions by itself.

## What the tax preparer will ask for at year end

Export Transactions and Months to CSV (Airtable: view menu, Download CSV). Plus: the bank statements from `records/bank/`, the Stripe annual summary, 1099s issued, the home office square footage, and mileage if any. Everything else is in `records/`.

## Status

- [x] Base and four tables created 2026-09-16; Accounts seeded.
- [ ] Add the Books base to the `AIRTABLE_PAT` access list (Jonathan). Then `python scripts/books.py --check`. Until then the CRM's Money page says the base is not on the token, and won deals cannot reach the Clients table (checked 2026-09-28 and again 2026-10-06: the token opens Monarc CRM only).
- [x] `spend-sync` written 2026-10-06; dry run read the Ads account ($0 in 30 days, every campaign paused) and three known charges, $2,119.48 ($53.90 Google Places 9/13, $75.58 Anthropic 9/13, $1,990 AI Acquisition 10/4). Not saved: the base is not on the token.
- [x] Clients table, Invoices link and rollups, CRM sync and Money page clients, 2026-09-28 (AIOS). Sync tested against stubs; first live run on the first Money page load after the token grant.
- [x] `STRIPE_SECRET_KEY` restricted read key in `secrets.env` (Jonathan) for `stripe-sync`. Added 2026-10-05; Stripe answers. `stripe-sync` still waits on the Books base being on `AIRTABLE_PAT` (403 on 2026-10-05).
- [ ] Money rules in `config.json` (Jonathan).
- [ ] First bank CSV at the end of September.
