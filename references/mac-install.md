# Monarc CRM and Monarc Flow on a Mac

Set up 2026-10-07 (Jonathan: "ship Monarc's CRM and Monarc Flow into the GitHub repository for installation on a Mac operating system. I would also like to securely transfer credentials to my Mac OS.").

## Order

1. **On the PC, seal the keys.** Run `python scripts/secrets_transfer.py pack`. Type a passphrase of five random words, twice. A file named `monarc-keys-<date>.locked` lands on the Desktop.
2. **Carry the file** on a USB stick or through Proton Drive. Never send the passphrase with it.
3. **On the Mac, get the repo.** Sign in to GitHub Desktop for Mac and clone the private repo. Or run `git clone <url>` in Terminal.
4. **Install.** In Terminal, in the repo folder, run `bash install/mac/install.sh`. It installs Homebrew's Python and ffmpeg, makes the repo's `.venv`, and builds both apps. Flow also downloads its speech model, about 700 MB.
5. **Unseal the keys.** Run `.venv/bin/python3 scripts/secrets_transfer.py unpack <path to the .locked file>`. It writes `~/.monarc/secrets.env`, `~/.monarc/kalshi.pem`, and the repo's `.env`, each readable by you only.
6. **Delete the .locked file** from the Mac and from the PC's Desktop.
7. **Give Flow its permissions.** In System Settings, open Privacy & Security. Turn on Monarc Flow under Microphone, Accessibility, and Input Monitoring. Then quit Flow from the menu bar (MF) and open it again.
8. **Proton Mail Bridge for Mac.** Install it and sign in. The CRM reads the inbox through it, as on the PC.

## What each app is on a Mac

| App | Opens from | Runs |
|---|---|---|
| Monarc CRM | `~/Applications/Monarc CRM.app` | `scripts/crm_boot.pyw`, the same server, http://127.0.0.1:8770/ |
| Monarc Flow | the MF in the menu bar, and at log-in | `scripts/flow_mac.py` |

## What differs on a Mac

- **Flow's keys are Ctrl+Cmd.** Cmd is the Mac's Win key. Space locks hands-free and Esc cancels, as on Windows.
- **Flow has no pop-up card.** When the cursor is not in a text box, the words still paste and are also left on the clipboard. A notice says so.
- **Flow's menu bar** reads MF when ready, REC while listening, and MF… while writing. MF! means the key permissions are off.
- **The CRM's chat panel** finds Claude Code in the VS Code extension or as `claude` on the PATH.
- **The Butterfly menu** opens VS Code through `open`. Install VS Code's `code` command from its command palette ("Shell Command: Install 'code' command in PATH"), or keep VS Code in Applications.

## Not tested on a Mac yet

All of this was written and checked on the PC. The Flow key logic passes its tests (`python projects/flow/tests/mac_hold.py`). The Mac-only parts have not run on a Mac yet: the key tap, the paste, the text-box read, the mic, the menu bar, and the app bundles. The first run on the Mac is the test. Logs:

- `~/.monarc/flow.log`
- `~/.monarc/crm-server.log`
- `~/.monarc/monarc-flow-app.log`
- `~/.monarc/monarc-crm-app.log`

## Keys, in short

- The locked file is AES-256-GCM. The key comes from the passphrase through scrypt. The passphrase is never stored.
- `names <file>` lists the key names inside without showing a value.
- Git never holds a key. `.env`, `*.env.txt`, `credentials*`, `*.locked`, and `*.pem` are in `.gitignore`.
