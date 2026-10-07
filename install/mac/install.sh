#!/bin/bash
# Monarc CRM and Monarc Flow on a Mac (2026-10-07). Run from the repo folder:
#   bash install/mac/install.sh            both apps
#   bash install/mac/install.sh crm        the CRM only
#   bash install/mac/install.sh flow       Flow only
# Safe to run again: it updates the packages and rebuilds the apps. Guide: references/mac-install.md.
set -euo pipefail
cd "$(dirname "$0")/../.."
REPO="$(pwd)"
WHAT="${1:-all}"

say() { printf "\n== %s\n" "$1"; }

say "Homebrew and Python"
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is not installed. Install it from https://brew.sh (one line in Terminal), then run this again."
  exit 1
fi
brew list python@3.12 >/dev/null 2>&1 || brew install python@3.12
brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg
PY="$(brew --prefix python@3.12)/bin/python3.12"

say "The repo's own Python (.venv)"
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/python3 -m pip install --upgrade pip --quiet
.venv/bin/python3 -m pip install -r install/mac/requirements.txt --quiet
mkdir -p "$HOME/.monarc"
chmod 700 "$HOME/.monarc"

say "Keys"
if [ -f "$HOME/.monarc/secrets.env" ] || [ -f "$REPO/.env" ]; then
  echo "Found keys on this Mac."
else
  echo "No keys yet. Bring the locked file from the PC, then run:"
  echo "  .venv/bin/python3 scripts/secrets_transfer.py unpack ~/Downloads/monarc-keys-<date>.locked"
fi

if [ "$WHAT" = "all" ] || [ "$WHAT" = "crm" ]; then
  say "Monarc CRM"
  .venv/bin/python3 -m playwright install chromium >/dev/null 2>&1 || echo "(the page-shot browser did not install; the CRM still runs)"
  .venv/bin/python3 scripts/crm_boot.pyw --install
fi

if [ "$WHAT" = "all" ] || [ "$WHAT" = "flow" ]; then
  say "Monarc Flow"
  .venv/bin/python3 scripts/flow_mac.py --install
fi

say "Done"
echo "Monarc CRM:  ~/Applications/Monarc CRM.app (opens http://127.0.0.1:8770/)"
echo "Monarc Flow: the MF in the menu bar. Hold Ctrl+Cmd to talk."
echo "Proton Mail Bridge for Mac signs in the same way as on the PC: https://proton.me/mail/bridge"
