---
name: kickoff
description: Use when Jonathan signs a client and says "kickoff", "onboard a client", "new client", "run the questionnaire", or "kickoff call". Books the Google Meet, pre-fills what is already known, runs the seven-block questionnaire one question at a time with a checkpoint after every answer, and scaffolds the client brief and access table. Collects access grants and IDs, never passwords.
argument-hint: "<client name or slug> [prep | call | wrap]"
---

# Client kickoff

The one meeting the offer promises: "We run a questionnaire covering your services, the brands you spec per service, your pricing floor, your service area, and calendar access. Then we build" (`context/offer.md`, Kickoff). Roadmap step 13 fires it on every yes. This skill runs it so every client produces the same inputs for the build, the First Responder, the ads, and the weekly report.

This is not `/onboard`. That one sets up the AIOS. This one sets up a client.

## Read first

1. `AGENTS.md` and `CLAUDE.md`, then `context/offer.md` and `context/icp-brands.md`.
2. `assets/questionnaire.md`: the question bank, seven blocks, with why each question exists and which downstream skill needs it.
3. `templates/vsl-draft.md` (repo root): the VSL targeting brief and script skeleton that Block 7 fills.
4. `assets/access-checklist.md`: per tool, what to ask for, how the client grants it, the ID to record.
5. `templates/onboarding-questionnaire.md` and `templates/asset-request-email.md` (repo root), and `context/trades/{key}.md` for the client's trade; integrators use `context/icp-brands.md`.
6. Anything already on file for this client: the Airtable Pipeline row (`connections.md` row 10) or `tasks.md` Pipeline table, `projects/outreach/Integrator_List_2026-09-05.xlsx`, and the `brainstorms/` capture from the sales call if one exists.

## Modes

Pick from `$ARGUMENTS` or the request. Default is the next mode that has not run for this client.

### prep (before the call)

1. Resolve the client: legal name, slug (`lowercase-hyphens`), contact name and email, website, metro, time zone. Ask only for what is missing.
2. Look up before asking. Read the client's live site (services listed, cities named, brands named, phone, existing Google tags, form endpoint, booking widget) and their GBP listing if the browser driver is running (`scripts/browser_cmd.py`). Write findings into the capture as "already known, confirm on the call". Never ask the client for a fact a page already gives.
3. Book the Meet. Use the Google Calendar connector (`connections.md` row 3) to create a 45 minute event on the primary calendar with a Google Meet link and the client as guest. Title: "Monarc Build kickoff: {Client}". Description: one outcome line, bare, the way Jonathan writes invites (`references/voice.md`). Confirm the time with Jonathan before creating it.
4. Create the capture file `brainstorms/{YYYY-MM-DD}-kickoff-{slug}.md`. Get the date from the shell (`Get-Date -Format yyyy-MM-dd`). Never overwrite an existing capture; add a time suffix if the name collides. Header per the grill-me structure: title, date, goal, status, context sources, an "Already known" block, an empty Q&A log, an empty "Open flags" section.
5. Draft the invite email from `templates/kickoff-recap-email.md` (the pre-call variant). Paste Part 1 and the client's trade block from `templates/onboarding-questionnaire.md` under the invite signature with the draft lines filled from step 2, or send the questionnaire's own cover note if the call is not booked yet. Draft `templates/asset-request-email.md` for the next business day with its "what I see" lines filled from `Resolve-DnsName` and the fingerprint. Jonathan sends all of it. The AIOS never sends: the Gmail connector is unauthorized and the Proton script is read-only.
6. Tell Jonathan the capture path and the three questions the prep already answered. When the questionnaire comes back, copy each answer into the capture's "Already known" block, one line per item number, and list the blanks as the call's open questions.

### call (during the Meet)

Jonathan has the questionnaire on screen and reads the questions. The AIOS is in the chat window logging answers.

- One question at a time, in the block order in `assets/questionnaire.md`. Dependencies run upstream first: services before brands, service area before pricing floor, lead handling before calendar access, Block 7 (VSL) after Blocks 2 and 6 and before Q33.
- Skip any question the "Already known" block answers. Confirm it in one line instead.
- **Checkpoint after every answer, before the next question.** Append a Q&A entry: topic, what the client said (their words where wording matters), decisions, flags. Read the saved entry back. If the write fails, say so and keep the answer visible in chat; do not continue without a working checkpoint. Never batch answers.
- When the client cannot answer, capture a flag with the owner and the follow-up ("GBP owner is the previous web guy; client will email him tonight") and move on. Do not stall.
- Block 4, access, is a live walk-through. The client shares a screen and grants access while on the call where possible. Record the ID and the status (requested, granted, verified). See the credential rule below.
- For decisions (pricing floor, one primary term, report weekday), offer a suggestion grounded in `context/icp-brands.md` and the prep findings, labeled as a suggestion. For facts, ask neutrally.
- Near the end: "Anything about the business we haven't touched?" Then stop. If Jonathan says stop earlier, stop; no extra question.

### wrap (after the call)

1. Read the capture for contradictions and gaps. Mark unresolved conflicts; do not decide a business fact for the client.
2. Scaffold the client folder `projects/clients/{slug}/` from the templates in this skill:
   - `brief.md` from `templates/client-brief.md`: confirmed facts only, one dated link back to the capture.
   - `access.md` from `templates/access.md`: the tool, ID, status table. No secrets.
   - `vsl.md` from the repo-root `templates/vsl-draft.md`: the filled targeting brief, the script v1, objections, and shot list. Header line "v1, not approved." Jonathan approves before the client sees it.
   Create `projects/clients/` on the first client.
3. Fill `templates/kickoff-recap-email.md` (post-call variant) with what was captured, the pending access items and exactly how to grant each, and the build deadline. If Block 7 did not run on the call, attach the "Fill-in brief" from the repo-root `templates/vsl-draft.md` with the draft lines pre-filled from the capture. "Still need from you" lists only asset-list items not yet in `projects/clients/{slug}/assets/` and access rows still `requested`. Show Jonathan the draft. He sends.
4. Register the client: the Deal in the Monarc CRM base moves to Won (`connections.md` row 10, the dashboard's deal form, which asks for the close reason "Signed"); one line per pending access item under the client's tier in `tasks.md`.
4b. File the contract: pull the fully signed PDF from DocuSeal (`references/airtable-api.md` row 2 has the account; the API key in `secrets.env` reads `/submissions/<id>/documents`) into `records/contracts/{slug}/{YYYY-MM-DD}-pilot-service-agreement-signed.pdf`, add the row to `records/README.md`, and log an Activity "Contract signed" on the deal. Never commit the PDF; `records/` is git-ignored.
5. Set the build deadline: 14 days from the call date unless Jonathan says otherwise (`context/roadmap.md` step 14). Put it in `brief.md` and `tasks.md`.
6. Recap in chat: capture path, brief path, pending access list with owners, build deadline. Suggest logging the pricing floor and service area in `decisions/log.md`.
7. Route: `projects/clients/` is already in the operating manuals. Individual clients do not need a root entry.

## Credential rule (non-negotiable)

- Never write a password, API key, token, or recovery code into the repo, the capture, or chat. Same boundary as `/grill-me`.
- Grant-access first. Every Google product (Business Profile, Ads, Analytics, Search Console, Tag Manager) adds a user by email. The client adds `jonathan@monarcbuild.com`. Record the account or property ID and the status.
- If a client insists on a shared login (hosting, registrar, a legacy CMS), Jonathan puts it in his password manager. `access.md` records "in password manager" and the date. Nothing else.
- Photos, logos, and documents the client hands over go to `projects/clients/{slug}/assets/`, never into `brainstorms/`.

## What the questionnaire feeds

Every question maps to a downstream skill or loop; the mapping is in `assets/questionnaire.md`. In short: block 1 feeds the service x city pages and ad groups; block 2 feeds the landing pages and GBP; block 3 feeds the attribution model and First Responder; block 4 feeds every MCP row; block 5 feeds the weekly PDF and the Money loop; block 6 feeds the build deadline and the Proof loop; block 7 feeds the hero VSL on every landing page through `templates/vsl-draft.md`. The skills themselves are listed in `references/github-skills-shortlist.md`.

## Boundaries and verification

- Local files, one calendar event, and drafts only. No sends, no purchases, no changes to client accounts.
- After editing this skill, mirror it to `.agents/skills/kickoff/` (what `scripts/sync-codex-skills.sh` does; on this Windows machine without bash, copy the folder with PowerShell and rewrite `.claude/skills/` to `.agents/skills/` inside the copied `.md` files).
- Dry run with a fake client: capture created before Q1, one question per turn, checkpoint visible after each answer, one flagged unknown with an owner, a stop honored, `brief.md` and `access.md` produced with IDs only. Delete the test calendar event afterward.
