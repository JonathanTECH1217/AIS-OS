# Connections

Registry of every system your AIOS can reach. Filled by `/onboard` from Q4-Q7 answers; expanded over time as you wire new tools. `/audit` checks this file for domain coverage and freshness.

| # | Domain | Tool | Mechanism | Auth | Last checked |
|---|---|---|---|---|---|
| 1 | Revenue / Financials | Stripe, account "Monarc Build, LLC" (live mode). Setup plan: `references/stripe-api.md` | mcp (`.mcp.json`, official server) | OAuth via `/mcp`, logged in | 2026-09-07 |
| 2 | Customer interactions | Proton Mail (jonathan@monarcbuild.com) via Proton Mail Bridge, read verified 2026-09-08: 12 folders incl. "Folders/Permit Data" and "Folders/Assessment Roll". `scripts/proton_mail.py`, see `references/proton-mail-api.md`. Cold calls (phone), Google Meet. DocuSeal for contracts (claude.ai connector) | Proton: script (local IMAP through Bridge), read-only. DocuSeal: mcp (claude.ai) | Bridge password in `.env` | 2026-09-08 |
| 3 | Calendar | Google Calendar, verified: primary calendar `sumreat17@gmail.com`, America/New_York | mcp (claude.ai) | claude.ai connector | 2026-09-07 |
| 4 | Communication | Proton Mail (same Bridge connection as row 2), Google Meet. patrick@monarcbuild.com is a second address on the domain. Gmail connector present but needs auth. | Proton: script, read-only | Bridge password in `.env` | 2026-09-08 |
| 5 | Project / task tracking | `tasks.md` in this AIOS (checkbox list from the roadmap); tracking sheet to be linked | local file | — | 2026-09-07 |
| 6 | Meeting intelligence | Google Meet recordings in a local video folder on another machine | not yet connected | — | — |
| 7 | Knowledge / files | Local files: docs, proposals, Excel outreach workbook. Google Drive verified 2026-09-08: "Monarc Drive" folder, "DC - Annapolis (DMV)" folder, and a 20-folder architectural style library (Georgian, Federal, Craftsman, etc.) plus a doc "High-End American Architectural Styles", owned by patrickbeach12@gmail.com. Five iPhone photos IMG_1902 to 1906 (March 2026) in the Drive root. | Drive: mcp (claude.ai), verified. Local: not yet connected | claude.ai connector | 2026-09-08 |

| 8 | Website | monarcbuild.com = static HTML in Hostinger `public_html` (live source of truth). Edit path: `scripts/site_sync.py` over SFTP/FTPS, see `references/hostinger-api.md`. Origin: Higgsfield project `monarc-build` (claude.ai "Jonathan" connector, verified; repo cloned to `projects/monarcbuild-site/`), reference only. Lead form: formsubmit.co to jonathan@monarcbuild.com, CC patrick@monarcbuild.com. | Hostinger: script (FTPS, `scripts/site_sync.py`), connected, pull verified 17 files. Higgsfield: mcp (claude.ai). Hostinger API MCP: declared in `.mcp.json`, waiting on Node 24 | Hostinger FTP creds in `.env`; API token in Windows user env; Higgsfield via connector | 2026-09-08 |

Seen at session start 2026-09-07 but not authorized: claude.ai Gmail, claude.ai Docusign. Authorize in claude.ai connector settings if wanted.

Filled 2026-09-07 by `/onboard`.

**Mechanism options:** `mcp` (MCP server), `script` (Python/Bash hitting an API, in `scripts/`), `export` (CSV/JSON dump pipeline), `key+ref` (`.env` key + `references/{tool}-api.md` guide), `not yet connected`.

When you wire a new tool, also save `references/{tool}-api.md` capturing endpoints, auth flow, and common queries — researched-once-saved-forever.
