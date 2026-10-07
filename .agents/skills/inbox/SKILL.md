---
name: inbox
description: Use at the start of every session (boot), or when Jonathan says "inbox", "check my email", "summarize my inbox", "draft replies". Reads jonathan@monarcbuild.com through Proton Mail Bridge, summarizes what needs him, drafts replies in his copy into the Drafts folder, and leaves one flagged report email in the inbox. Never sends.
argument-hint: "[N messages, default 30] | report only | draft <id>"
---

# Inbox pass (boot)

Runs at the start of every session and on request. Reads the inbox, drafts what can be drafted, reports once. **Nothing is ever sent.** Drafts sit in Proton's Drafts folder for Jonathan to send or delete.

## Read first
1. `references/mycopy.md`: the copy every draft is built from. If a reply needs a block that is not there, draft the shortest honest version and say in the report that mycopy.md has no block for it.
2. `references/voice.md`: register rules (no hedges, no em dashes, 60 to 120 words, the ask is two times and a length).
3. `context/offer.md` for any fact a reply states. Never print a number that is not on that page or in the prospect's own email.

## Steps

1. **Triage.** `python scripts/proton_mail.py triage 30`. The script classifies each message:
   - `self`: from Jonathan's own address. Skip. Photos, notes to self, forwards.
   - `patrick`: from patrick@monarcbuild.com. Skip.
   - `chain`: on a thread (In-Reply-To or References header, or a Re:/Fwd: subject). Skip. Jonathan handles live threads himself.
   - `report`: an earlier inbox report. Skip.
   - `review`: everything else. These are the only messages to summarize and draft for.
   If Bridge is signed out ("no such user" or connection refused), stop and tell Jonathan to open Bridge and sign in. Do not guess at the inbox.

2. **Read each `review` message.** `python scripts/proton_mail.py read <id>`. Decide one of: reply (a prospect, a client, a partner, a real question), no reply (newsletters, receipts, notifications, cold vendor pitches), or needs Jonathan (anything asking for a price not on the offer page, a contract, a complaint, a date he has to pick).

3. **Draft replies.** For each "reply" message, write a spec file in the scratchpad:
   ```
   To: <their address>
   Subject: Re: <their subject>
   In-Reply-To: <their Message-ID>
   References: <their Message-ID>

   <body in mycopy.md blocks>
   ```
   Then `python scripts/proton_mail.py draft <spec.txt>`. One draft per message. Do not draft for `self`, `patrick`, or `chain` rows even if they look like they need one; list them in the report instead.

4. **Report.** Write one spec file and run `python scripts/proton_mail.py report <spec.txt>`. It lands in INBOX flagged (starred), from "AIOS" to Jonathan, subject "AIOS inbox report YYYY-MM-DD". Body, in this order, plain text, short:
   - Drafted (N): one line each: who, what they wanted, what the draft says, in Drafts.
   - Needs you (N): one line each: who, why the AIOS did not draft it.
   - Skipped (N): counts by rule (self, patrick, chain), plus any chain that looks urgent, one line.
   - Noise (N): one line, the count of newsletters and notifications.
   If there is nothing to draft and nothing that needs him, still send the report with one line: "Nothing needs you."

5. **Tell Jonathan in chat** the same summary in three lines or fewer, and that the drafts are in Drafts.

## House rules
- Never send. The script cannot send; do not find another way.
- Never reply on a chain. Never reply to Patrick. Never reply to Jonathan's own mail.
- Never invent a fact, a price, or a time. Times in an ask come from the Monarc Build calendar (`connections.md` row 3) when a booking is needed; otherwise use "{day} at {time}" placeholders and say so in the report.
- One report per pass. If a pass is re-run the same day, the new report replaces nothing; it is a second flagged email, so only re-run when asked.
- After editing this skill, mirror it to `.agents/skills/inbox/` (same file, no path rewrite needed).
