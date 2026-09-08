# Hostinger (monarcbuild.com, `public_html`)

Domain: Website hosting, `connections.md` row 8. Started 2026-09-08. Goal: the AIOS can pull the live site down, edit it locally with Jonathan, and push approved changes back to `public_html`.

## Read this first (2026-09-08 finding)

The site began in Higgsfield's website builder (project `monarc-build`, cloned to `projects/monarcbuild-site/` for reference), but what's live on monarcbuild.com is a static HTML export that has since diverged from that app (different form handler, no React). **The HTML in `public_html` is the live source of truth, and this SFTP or FTPS connection is the edit path.** Nothing overwrites `public_html` unless someone uploads to it. Do not deploy from Higgsfield onto this site without a deliberate decision.

## The short version

No Hostinger API is needed for files. Shared hosting exposes `public_html` over SFTP (SSH) or FTPS. The machine already has the Windows OpenSSH client (`sftp.exe`, `scp.exe`, `ssh-keygen.exe`), Python 3.13, and curl, so the connection is a small local script and one credential that lives in `.env`, never in chat or in this file.

Preferred transport: **SFTP with an SSH key** (own identity for the AIOS, no password stored, revocable in one click). Fallback: **FTPS with a dedicated FTP account scoped to `public_html`**.

Local mirror of the site: `projects/monarcbuild-site/public_html/`. Edits happen there, Jonathan approves, then the script pushes. Raw pulls are backed up to `archives/site-{timestamp}/` before being overwritten.

## Facts about Hostinger shared hosting (confirm in hPanel)

- SSH: hPanel, Websites, Manage, Advanced, SSH Access. Shows host (an IP), port (Hostinger uses 65002 for shared plans), and username (a `u` followed by digits). SSH keys are added on the same screen. Not every plan includes SSH; if the menu item is missing, use FTPS.
- FTP: hPanel, Websites, Manage, Files, FTP Accounts. Host, port 21, username, and the option to create an additional account with a directory limit. Create one limited to `public_html` for the AIOS rather than using the main account.
- File Manager in hPanel is the manual fallback for one-off edits.

## Setup, in order

### Path A: SFTP with a key (preferred)

1. AIOS generates a keypair: `ssh-keygen -t ed25519 -f ~/.ssh/monarc_hostinger -C "aios@monarcbuild"`. No passphrase prompt is possible in the sandbox, so Jonathan runs this in a normal terminal, or the AIOS runs it with `-N ""` (empty passphrase) and the key stays on this machine only.
2. Jonathan pastes the contents of `~/.ssh/monarc_hostinger.pub` into hPanel, SSH Access, Add SSH key.
3. Jonathan creates `.env` at the AIOS root:
   ```
   HOSTINGER_TRANSPORT=sftp
   HOSTINGER_HOST=<ip from hPanel>
   HOSTINGER_PORT=65002
   HOSTINGER_USER=<u-number username>
   HOSTINGER_KEY=C:\Users\sumre\.ssh\monarc_hostinger
   HOSTINGER_REMOTE_DIR=public_html
   ```
4. First contact, read only: `python scripts/site_sync.py list`. Expect the file list of `public_html`.
5. `python scripts/site_sync.py pull`. Expect a full local mirror plus a backup folder.
6. One harmless push to prove write access: `python scripts/site_sync.py push <one file>`. Verify live with a fetch. Then real edits.

### Path B: FTPS with a scoped account

1. Jonathan creates an FTP account in hPanel limited to `public_html`, username like `aios@monarcbuild.com`.
2. `.env`:
   ```
   HOSTINGER_TRANSPORT=ftps
   HOSTINGER_HOST=<ftp host from hPanel>
   HOSTINGER_PORT=21
   HOSTINGER_USER=<ftp username>
   HOSTINGER_PASS=<ftp password>
   HOSTINGER_REMOTE_DIR=/
   ```
   (With a scoped account the login root is already `public_html`, so the remote dir is `/`.)
3. Steps 4 to 6 as above.

## Hostinger API MCP servers (added 2026-09-08, not yet running)

`.mcp.json` now declares Hostinger's official MCP package (`hostinger-api-mcp`) as five servers: hosting, domains, dns, billing, reach. Verified against the package README 2026-09-08.

What `hostinger-hosting-mcp` can do with the site (exact tool names):
- Read: `hosting_listWebsitesV1`, `hosting_listWebsiteFilesAndDirectoriesV1`, `hosting_getWebsiteFileContentV1` (single text file, read-only, refuses secrets).
- Write: only whole-site. `hosting_deployStaticWebsite` / `hosting_deployStaticSiteArchiveV1` deploy a zip and **overwrite everything in the document root**. `hosting_generateUploadURLV1` gives a file-browser upload URL. There is no single-file write or edit tool, and no FTP or SSH account management.
- After any change: `hosting_clearWebsiteCacheV1` so hcdn serves the new HTML. `hosting_toggleCachelessModeV1` for a dev window.
- Also useful later: redirects (`hosting_createWebsiteRedirectV1`), subdomains for client staging, cron jobs, PHP settings.
- `hostinger-dns-mcp`: `DNS_getDNSRecordsV1`, `DNS_updateDNSRecordsV1` with snapshots. For pointing client domains.
- Not needed for Monarc: billing, reach (email marketing), mail (email is Proton).

How this fits with SFTP: SFTP is the per-file edit path (push one file, no rebuild). The MCP is the read path without SSH, the whole-site redeploy path (zip the local mirror, deploy, clear cache), and the DNS path. Both end up wired; SFTP first because it needs nothing installed.

Requirements before the MCP servers start:
1. Node.js **24 or higher** installed (`npx.cmd` is how they launch). Not present on this machine as of 2026-09-08.
2. A Hostinger API token from hPanel, Account, API. Stored as a Windows user environment variable `HOSTINGER_API_TOKEN` (Claude Code expands `${HOSTINGER_API_TOKEN}` from the process environment; it does not read `.env`). Set once in a normal terminal:
   `[Environment]::SetEnvironmentVariable('HOSTINGER_API_TOKEN', '<token>', 'User')`
3. Restart VS Code so `.mcp.json` and the environment reload, approve the project servers when prompted, check `/mcp`.

Trim to `hostinger-hosting` and `hostinger-dns` if five Node processes at startup feel heavy. Each one runs `npx` on session start.

## The script

`scripts/site_sync.py`. Commands: `list`, `pull`, `push <path> [path...]`, `diff`. Reads `.env` itself, no packages to install. SFTP goes through the system `sftp.exe` in batch mode; FTPS uses Python's `ftplib`. It never deletes remote files. Push only sends the paths named, so nothing goes live by accident.

## CDN behavior (observed 2026-09-08)

Hostinger's edge (`Server: hcdn`) re-encodes images: a 2400x1800 JPEG pushed to `public_html` was served at 1600x1200. It also caches with `Cache-Control: public, max-age=604800` (seven days). Consequences: size hero images to 1600px wide before pushing (no point pushing larger), and when replacing an image, use a new filename so browsers and the CDN don't serve the stale one. HTML pages have been served fresh on each push so far; if one doesn't, the Hostinger MCP `hosting_clearWebsiteCacheV1` tool (needs Node 24) or the hPanel cache button clears it.

## Rules (Intern Rule)

- The AIOS has its own identity (a key or a scoped FTP account), never Jonathan's main hPanel login.
- Push only after Jonathan has seen the change. Public site edits are external content.
- Pull before push, every session, so a local mirror never overwrites a change made in hPanel.
- Credentials in `.env` only. `.env` is gitignored. If a key or password ever lands in chat, rotate it.

## Status

- [x] Transport chosen: FTPS, port 21 (2026-09-08). The main FTP account was used; its login root is already `public_html`, so `HOSTINGER_REMOTE_DIR=/`.
- [x] AIOS SSH key generated (`~/.ssh/monarc_hostinger`), unused so far. Scoped FTP account: not yet created (Intern Rule follow-up).
- [x] `.env` created and cleaned (2026-09-08)
- [x] `list` works (read), 14 entries at root
- [x] `pull` done: 17 files into `projects/monarcbuild-site/public_html/`
- [x] One-file `push` verified live (robots.txt, unchanged content, 2026-09-08)
- [x] `connections.md` row 8 updated to `script`

Follow-ups: rotate the FTP password and the API token (both passed through a chat transcript on 2026-09-08 when the file surfaced on change); create a scoped FTP account named `aios` limited to `public_html` and switch `.env` to it.

Last checked: 2026-09-08. Connected.
