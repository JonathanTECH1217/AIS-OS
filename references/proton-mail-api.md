# Proton Mail (jonathan@monarcbuild.com)

Domains 2 and 4, `connections.md`. Started 2026-09-08. Goal: the AIOS can read the mailbox (leads from formsubmit.co, prospect replies, photo attachments) and later draft replies for approval.

## The short version

Proton has no third-party API and no claude.ai connector. The only programmatic door is **Proton Mail Bridge**, Proton's own desktop app, which runs on this machine and exposes the mailbox as local IMAP and SMTP (encrypted end to end on Proton's side, plain IMAP only on localhost). A small Python script reads it. No packages to install: `imaplib` and `email` are in the standard library.

Bridge requires a paid Proton plan (Mail Plus, Proton Unlimited, or Proton for Business). A custom-domain address like jonathan@monarcbuild.com already implies a paid plan.

## Setup, in order

1. **Install Proton Mail Bridge** from proton.me/mail/bridge (Windows). Sign in with the Proton account. Leave it running in the tray; it must be open for the script to work.
2. **Copy the Bridge password.** In Bridge, Mailbox configuration shows an IMAP host (`127.0.0.1`), port (`1143`), username (the Proton address), and a Bridge-generated password. That password is NOT the Proton login password. It only works locally through Bridge.
3. **Add to `.env`** (gitignored, never in chat):
   ```
   PROTON_IMAP_HOST=127.0.0.1
   PROTON_IMAP_PORT=1143
   PROTON_SMTP_PORT=1025
   PROTON_USER=jonathan@monarcbuild.com
   PROTON_BRIDGE_PASS=<bridge password>
   ```
4. **First contact, read only:** `python scripts/proton_mail.py folders`, then `python scripts/proton_mail.py recent 10`. Expect folder names and the ten newest subjects.
5. **Attachments:** `python scripts/proton_mail.py attachments "<subject or sender fragment>" <out_dir>` saves image and document attachments from matching messages.

## Fallbacks when Bridge is not an option today

- Forward the specific emails to sumreat17@gmail.com and authorize the Gmail connector in claude.ai (it's present but unauthorized). Same attachments, no local install.
- Save attachments from the Proton web app straight into `projects/monarcbuild-site/public_html/assets/georgian/` (for site photos) or `archives/` (for documents).

## Rules (Intern Rule)

- Read-only first. Sending through Bridge SMTP is a later step and only after a draft is approved; the AIOS never sends in Jonathan's name without a shown draft (`CLAUDE.md`, Voice).
- The Bridge password stays in `.env`. Rotate it in Bridge if it ever appears in chat.
- Bridge certificates are self-signed for localhost; the script talks plain IMAP to 127.0.0.1 as Bridge documents, never to the internet.

## Status

- [x] Paid plan confirmed (Bridge signed in)
- [x] Bridge installed and signed in (2026-09-08)
- [x] `.env` lines added (password cleaned of template brackets)
- [x] `folders` works (read): Spam, Folders/Permit Data, Folders/Assessment Roll, Drafts, Trash, Starred, Archive, All Mail, INBOX, Sent
- [ ] Attachments pulled for the Georgian photos
- [x] `connections.md` rows 2 and 4 updated to `script`

Notes: Bridge advertises STARTTLS with a self-signed localhost certificate; the script uses an unverified TLS context for 127.0.0.1 only. Search is by SUBJECT or FROM substring per folder.

Last checked: 2026-09-08. Connected, read-only.
