# Records: the paper drawer

The papers that prove Monarc Build, LLC exists and what it has agreed to. Git tracks only this index; every file under `records/` is ignored so nothing with an EIN, an account number, or a signature reaches GitHub. **No identifying number is ever written in this file or in chat.** The number is on the paper.

Started 2026-09-16. Add a row when a paper arrives. Folders are made only when something goes in them.

## entity/ (formation and tax registration)

| Paper | Date | File | Notes |
|---|---|---|---|
| Articles of Organization, Maryland SDAT form SDAT40.2 | 2026-06-18 | `entity/2026-06-18-articles-of-organization.pdf` | Monarc Build, LLC. Department ID and acknowledgment number on the paper and in `context/about-business.md`. Resident agent: Jonathan Beach, 3074 Riva Rd, Riva, MD 21140-1318. No business license required. |
| IRS EIN assignment letter, form CP 575 G | on the letter | `entity/ein-letter-cp575.pdf` | The EIN is on this letter only. Banks, Stripe, and tax filings ask for it. |
| Operating agreement | not yet | | Maryland does not require one; banks and buyers ask. One-owner version to write and sign. |

## filings/ (yearly state filings)

| Filing | Due | File | Notes |
|---|---|---|---|
| Maryland Annual Report and Personal Property Return | April 15, 2027, then every April 15 | | Filed on Maryland Business Express. $300. Missing it forfeits the LLC. First one covers 2026. |

## tax/

| Paper | Due | File | Notes |
|---|---|---|---|
| Quarterly estimated tax, federal and Maryland | April 15, June 15, September 15, January 15 | | Single-member LLC: income lands on Schedule C of the 1040. Keep each payment confirmation here. |
| 1099-NEC to any contractor paid $600 or more in the year | January 31 | | Collect a W-9 from every contractor before the first payment; file the W-9 here. |
| Annual return (1040 with Schedule C; Maryland 502) | April 15 | | The tax preparer gets the Transactions and Months exports from the Books base (`references/books.md`). |

## contracts/ (one folder per client)

| Client | Agreement | Signed | File |
|---|---|---|---|
| | Pilot Service Agreement (template: `templates/Monarc_Pilot_Service_Agreement.pdf`, DocuSeal template 5897221) | | `contracts/<client-slug>/<date>-pilot-service-agreement-signed.pdf` when fully signed |

## insurance/

None yet. General liability and professional liability (errors and omissions) are the two an agency is asked for; add here when bought, with the renewal date.

## bank/

| Paper | Date | File | Notes |
|---|---|---|---|
| Business checking, account opening letter | | | Bring the Articles, the EIN letter, and ID to open it. Monthly statements go here as `bank/YYYY-MM-statement.pdf` and their CSV export feeds the Books base. |

## Dates that bite

- **April 15** every year: Maryland Annual Report ($300) and the annual tax return. Also a quarterly estimate.
- **June 15, September 15, January 15**: the other quarterly estimates.
- **January 31**: 1099s out.
- These are in `tasks.md` under the monthly section. Put them on the Monarc Build calendar with a two-week reminder.
