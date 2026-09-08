#!/usr/bin/env python3
"""
proton_mail.py - read jonathan@monarcbuild.com through Proton Mail Bridge (local IMAP).

Commands:
  python scripts/proton_mail.py folders
  python scripts/proton_mail.py recent [N] [folder]
  python scripts/proton_mail.py search "<text in subject or from>" [folder]
  python scripts/proton_mail.py attachments "<text in subject or from>" <out_dir> [folder]

Reads .env at the AIOS root (PROTON_IMAP_HOST, PROTON_IMAP_PORT, PROTON_USER, PROTON_BRIDGE_PASS).
Read-only. Never sends. No third-party packages. Requires Proton Mail Bridge running on this machine.

bike-method-phase: 1 (run by hand, watch everything)
"""

import email
import imaplib
import re
import ssl
import sys
from email.header import decode_header, make_header
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".tif", ".tiff"}
DOC_EXT = {".pdf", ".docx", ".xlsx", ".csv", ".txt", ".zip"}


def load_env(path=ROOT / ".env"):
    if not path.exists():
        sys.exit(f".env not found at {path}. See references/proton-mail-api.md.")
    env = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def connect():
    env = load_env()
    host = env.get("PROTON_IMAP_HOST", "127.0.0.1")
    port = int(env.get("PROTON_IMAP_PORT", "1143"))
    user, pw = env.get("PROTON_USER"), env.get("PROTON_BRIDGE_PASS")
    if not user or not pw:
        sys.exit("PROTON_USER and PROTON_BRIDGE_PASS must be set in .env")
    try:
        m = imaplib.IMAP4(host, port)
        # Bridge offers STARTTLS with a self-signed certificate for localhost. Verification is
        # skipped only because the peer is 127.0.0.1 on this machine; never reuse this for a remote host.
        if "STARTTLS" in m.capabilities:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            m.starttls(ssl_context=ctx)
        m.login(user, pw)
    except Exception as e:
        sys.exit(f"Could not reach Proton Mail Bridge at {host}:{port}: {e}\nIs Bridge open and signed in?")
    return m


def hdr(msg, name):
    raw = msg.get(name, "")
    try:
        return str(make_header(decode_header(raw)))
    except Exception:
        return raw


def safe_name(s):
    s = re.sub(r"[^\w.\- ]+", "_", s).strip()
    return s or "attachment"


def cmd_folders(m):
    typ, data = m.list()
    for line in data:
        print(line.decode(errors="replace"))


def fetch_ids(m, folder, criteria):
    m.select(f'"{folder}"', readonly=True)
    typ, data = m.search(None, criteria)
    ids = data[0].split() if data and data[0] else []
    return ids


def cmd_recent(m, n=10, folder="INBOX"):
    ids = fetch_ids(m, folder, "ALL")[-n:]
    for i in reversed(ids):
        typ, data = m.fetch(i, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
        msg = email.message_from_bytes(data[0][1])
        print(f"{i.decode():>6}  {hdr(msg,'Date')[:25]:25}  {hdr(msg,'From')[:40]:40}  {hdr(msg,'Subject')[:70]}")


def cmd_search(m, text, folder="INBOX"):
    ids = set(fetch_ids(m, folder, f'SUBJECT "{text}"')) | set(fetch_ids(m, folder, f'FROM "{text}"'))
    for i in sorted(ids, key=lambda b: int(b)):
        typ, data = m.fetch(i, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
        msg = email.message_from_bytes(data[0][1])
        print(f"{i.decode():>6}  {hdr(msg,'Date')[:25]:25}  {hdr(msg,'From')[:40]:40}  {hdr(msg,'Subject')[:70]}")
    return sorted(ids, key=lambda b: int(b))


def cmd_attachments(m, text, out_dir, folder="INBOX"):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ids = cmd_search(m, text, folder)
    saved = 0
    for i in ids:
        typ, data = m.fetch(i, "(BODY.PEEK[])")
        msg = email.message_from_bytes(data[0][1])
        for part in msg.walk():
            fn = part.get_filename()
            if not fn:
                continue
            fn = str(make_header(decode_header(fn)))
            ext = Path(fn).suffix.lower()
            if ext not in IMAGE_EXT | DOC_EXT:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            target = out / f"{i.decode()}-{safe_name(fn)}"
            target.write_bytes(payload)
            saved += 1
            print(f"saved {target} ({len(payload)} bytes)")
    print(f"{saved} attachment(s) saved to {out}")


def main(argv):
    if len(argv) < 2 or argv[1] not in ("folders", "recent", "search", "attachments"):
        print(__doc__)
        sys.exit(1)
    m = connect()
    try:
        if argv[1] == "folders":
            cmd_folders(m)
        elif argv[1] == "recent":
            n = int(argv[2]) if len(argv) > 2 else 10
            cmd_recent(m, n, argv[3] if len(argv) > 3 else "INBOX")
        elif argv[1] == "search":
            cmd_search(m, argv[2], argv[3] if len(argv) > 3 else "INBOX")
        elif argv[1] == "attachments":
            if len(argv) < 4:
                sys.exit('attachments needs "<text>" and <out_dir>')
            cmd_attachments(m, argv[2], argv[3], argv[4] if len(argv) > 4 else "INBOX")
    finally:
        try:
            m.logout()
        except Exception:
            pass


if __name__ == "__main__":
    main(sys.argv)
