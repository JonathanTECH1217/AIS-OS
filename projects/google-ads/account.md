# Google Ads account

Filled as Jonathan confirms each line. Never a card number, password, or token here (`records/` and `secrets.env` hold those).

| Item | Value | Confirmed |
|---|---|---|
| Customer id | 418-577-4900, "Monarc Build", USD, America/New_York, status ENABLED | 2026-09-29, read through the API (the only account the login reaches) |
| Admin users | Jonathan (jonathan@monarcbuild.com); Patrick (billing notices) | pending |
| Billing owner and payment method state | A payment was declined 2026-09-01 | pending: fix, then confirm the account is not suspended (the API cannot read billing on Explorer access) |
| Manager account (MCC) | none; not needed for the API since 2026-09-09 | not needed |
| Existing campaigns | Monarc Build Ad Pilot (24088864246, paused); MB AP Exp1 (24092305402, enabled but its end date passed, serving ENDED); MB AP Headlines (24100320424, paused); LV Sample Ad Set (24282249983, paused); Ad Pilot Test 2 removed. No impressions or spend on any in the last 30 days. | 2026-09-29 read; Exp1 is the trial arm of an ended experiment, which Google will not pause by API (CANNOT_MODIFY_FOR_TRIAL_CAMPAIGN); it cannot serve |
| Existing conversion actions | Enabled: "Submit lead form (6)" (7721027718, primary, the one to keep) and "Page view (Page load monarcbuild.com/book) (4)" (7724677103, codeless, primary: to make secondary). GA4 imports hidden: book_appointment (7804988528), qualify_lead, close_convert_lead, purchase. "Page view (9)" and about 45 older actions are removed. | 2026-09-29 read |

## Settings that must hold

| Setting | Value | State |
|---|---|---|
| Primary conversion action | "Submit lead form (6)", label `9mMKCIaR1uEcEMnqkLJE`, category Book appointment, one per click, 30-day click window, data-driven attribution if offered | pending |
| "Page view (9)" (`xvGlCMOiweMcEMnqkLJE`) | Secondary or removed; the homepage snippet removed or guarded by `?sent=1` | pending |
| Final URL suffix (Admin, Account settings, Tracking) | `utm_source=google&utm_medium=cpc&utm_campaign={campaignid}&utm_term={keyword}&utm_content={creative}` | set, read back 2026-09-29 |
| Auto-tagging | on | on, read back 2026-09-29 |
| GA4 link | `G-JQ977C0MY7` linked; `book_appointment` a key event, imported as Secondary | pending |
| Auto-apply recommendations | off | pending |
| IP exclusions | Jonathan's home and office, on every campaign | pending |
| Search partners, Display expansion | off, on every campaign | pending |
| Location option | "Presence" only | pending |
| Language | English | pending |

## Log

- 2026-09-25: file created from the plan. Nothing confirmed yet.
- 2026-09-29: API connected (OAuth client in secrets.env as GOOGLE_ADS_API_KEY and GOOGLE_ADS_CLIENT_SECRET; Explorer access granted the same day). Account, campaigns, and conversion actions read; auto-tagging and the suffix confirmed. Gates: click stamping done, h1 done; billing, one main conversion, test booking open.
