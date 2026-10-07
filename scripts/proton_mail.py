#!/usr/bin/env python3
"""
proton_mail.py - read jonathan@monarcbuild.com through Proton Mail Bridge (local IMAP).

Commands:
  python scripts/proton_mail.py folders
  python scripts/proton_mail.py recent [N] [folder]
  python scripts/proton_mail.py search "<text in subject or from>" [folder]
  python scripts/proton_mail.py attachments "<text in subject or from>" <out_dir> [folder]
  python scripts/proton_mail.py draft <spec.txt> [attachment ...] [--force]
  python scripts/proton_mail.py triage [N]            (the /inbox boot pass: last N inbox messages with skip rules applied)
  python scripts/proton_mail.py read <id>             (plain-text body of one message, for drafting a reply)
  python scripts/proton_mail.py report <spec.txt>     (append a FLAGGED message to INBOX, addressed to Jonathan: the /inbox report)
  python scripts/proton_mail.py inbox-test <spec.txt> (append an UNREAD message to INBOX as a prospect would get it: a copy test)

inbox-test (Jonathan, 2026-10-05: "Hit my inbox as if I were an integrator..."): how he reads the SDR's copy the way a
prospect would. The spec has From: (the SDR's mailbox, an @monarcbuild.com address) and Subject:, a blank line, the body.
The message is laid into his own INBOX; nothing goes over the wire to anyone, so "never sends" still holds. It carries
the header X-Monarc-Test so it can be told from real mail.

draft: places an unsent message in the Drafts folder. The spec file has header lines (To:, Cc:, Subject:,
optional In-Reply-To: and References: so the draft threads under the original), a blank line, then the body.
Attachments are file paths. Before placing it, Drafts and Sent are checked for mail to the same address with the
same subject in the last 7 days (Re: and Fwd: stripped); a match stops the draft and lists what is there, and --force
places it anyway (2026-10-05, after two chats each drafted a rebook email to the same company). Nothing is ever sent by this script. The body goes out as plain text plus an
HTML part set in Times New Roman, 12pt (Jonathan's rule, 2026-09-15): blank line = new paragraph, URLs become links.

triage skip rules (Jonathan, 2026-09-14): "self" = From is Jonathan's own address (photos, notes, junk he
forwards to himself); "patrick" = From patrick@monarcbuild.com; "chain" = the message is on a thread
(In-Reply-To or References header, or a Re:/Fwd: subject); "report" = an earlier /inbox report. Everything
else is "review" and gets a snippet.

Reads .env at the AIOS root (PROTON_IMAP_HOST, PROTON_IMAP_PORT, PROTON_USER, PROTON_BRIDGE_PASS).
Reads mail and writes drafts only. Never sends. No third-party packages. Requires Proton Mail Bridge running on this machine.

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


REPORT_SUBJECT_PREFIX = "AIOS inbox report"
SKIP_SENDERS = ("patrick@monarcbuild.com",)


def body_text(msg, limit=4000):
    """Plain text of a message: text/plain part first, else tags stripped from text/html."""
    plain, html = "", ""
    for part in msg.walk():
        ctype = part.get_content_type()
        if part.get_filename() or ctype not in ("text/plain", "text/html"):
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        charset = part.get_content_charset() or "utf-8"
        try:
            text = payload.decode(charset, errors="replace")
        except LookupError:
            text = payload.decode("utf-8", errors="replace")
        if ctype == "text/plain" and not plain:
            plain = text
        elif ctype == "text/html" and not html:
            html = text
    if not plain and html:
        html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
        html = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", html)
        plain = re.sub(r"<[^>]+>", " ", html)
        plain = re.sub(r"&nbsp;", " ", plain)
    plain = re.sub(r"[ \t]+", " ", plain)
    plain = re.sub(r"\n\s*\n+", "\n\n", plain).strip()
    return plain[:limit]


def classify(msg, own_address):
    frm = hdr(msg, "From").lower()
    subject = hdr(msg, "Subject")
    if subject.startswith(REPORT_SUBJECT_PREFIX):
        return "report"
    if own_address and own_address.lower() in frm:
        return "self"
    if any(s in frm for s in SKIP_SENDERS):
        return "patrick"
    if _threaded(msg) or re.match(r"^\s*(re|fwd?|fw)\s*:", subject, re.I):
        return "chain"
    return "review"


def _threaded(msg):
    """True when the message answers or continues another. Proton Bridge stamps a References header ending in
    @protonmail.internalid on every message, newsletters included (seen 2026-09-25, when all 30 rows came back
    'chain'); those ids are Proton's own and do not mean a thread."""
    for h in ("In-Reply-To", "References"):
        ids = re.findall(r"<([^>]+)>", str(msg.get(h) or ""))
        if any(not i.lower().endswith("@protonmail.internalid") for i in ids):
            return True
    return False


def cmd_triage(m, n=30, folder="INBOX"):
    env = load_env()
    own = env.get("PROTON_USER", "")
    m.select(f'"{folder}"', readonly=True)
    typ, data = m.search(None, "ALL")
    ids = (data[0].split() if data and data[0] else [])[-n:]
    counts = {}
    rows = []
    for i in reversed(ids):
        typ, data = m.fetch(i, "(FLAGS BODY.PEEK[])")
        raw = b""
        flags = ""
        for item in data:
            if isinstance(item, tuple):
                flags = item[0].decode(errors="replace")
                raw = item[1]
        msg = email.message_from_bytes(raw)
        status = classify(msg, own)
        counts[status] = counts.get(status, 0) + 1
        seen = "\\Seen" in flags
        answered = "\\Answered" in flags
        rows.append((i.decode(), status, seen, answered, msg))
    print(f"{len(rows)} messages in {folder}. " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    print()
    for uid, status, seen, answered, msg in rows:
        mark = ("  " if seen else "* ") + ("A " if answered else "  ")
        print(f"{uid:>6}  {status:7}  {mark}{hdr(msg,'Date')[:25]:25}  {hdr(msg,'From')[:44]:44}  {hdr(msg,'Subject')[:60]}")
        if status == "review":
            snippet = body_text(msg, 600).replace("\n", " ")
            print(f"        to: {hdr(msg,'To')[:60]}   message-id: {msg.get('Message-ID','')[:70]}")
            print(f"        {snippet[:300]}")
    print()
    print("* unread, A answered. Draft replies only for 'review' rows. Never send.")


def cmd_read(m, uid, folder="INBOX"):
    m.select(f'"{folder}"', readonly=True)
    typ, data = m.fetch(uid.encode(), "(BODY.PEEK[])")
    if typ != "OK" or not data or not isinstance(data[0], tuple):
        sys.exit(f"message {uid} not found in {folder}")
    msg = email.message_from_bytes(data[0][1])
    for h in ("Date", "From", "To", "Cc", "Subject", "Message-ID", "In-Reply-To", "References"):
        if msg.get(h):
            print(f"{h}: {hdr(msg, h)}")
    atts = [str(make_header(decode_header(p.get_filename()))) for p in msg.walk() if p.get_filename()]
    if atts:
        print("Attachments: " + ", ".join(atts))
    print()
    print(body_text(msg, 6000))


def cmd_report(m, spec_path):
    """Append a flagged (starred) message to INBOX, from Jonathan to Jonathan. This is the /inbox report."""
    import time
    from email.message import EmailMessage
    from email.utils import formatdate, make_msgid

    env = load_env()
    text = Path(spec_path).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    head, _, body = text.partition("\n\n")
    headers = {}
    for line in head.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    subject = headers.get("subject") or f"{REPORT_SUBJECT_PREFIX} {time.strftime('%Y-%m-%d')}"
    if not subject.startswith(REPORT_SUBJECT_PREFIX):
        subject = f"{REPORT_SUBJECT_PREFIX}: {subject}"
    msg = EmailMessage()
    msg["From"] = f"AIOS <{env['PROTON_USER']}>"
    msg["To"] = env["PROTON_USER"]
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=env["PROTON_USER"].split("@")[-1])
    msg.set_content(body.strip() + "\n")
    typ, resp = m.append("INBOX", "\\Flagged", imaplib.Time2Internaldate(time.time()), msg.as_bytes())
    if typ != "OK":
        sys.exit(f"APPEND to INBOX failed: {resp}")
    print(f"flagged report placed in INBOX: {subject}")


EMAIL_FONT = "'Times New Roman', Times, serif"  # Jonathan, 2026-09-15: email copy is always Times New Roman


def body_html(body):
    """Plain paragraphs to an HTML part in Times New Roman. Blank line = paragraph break; URLs become links."""
    import html as h
    import re
    paras = [p.strip() for p in body.strip().split("\n\n") if p.strip()]
    out = []
    for p in paras:
        esc = h.escape(p).replace("\n", "<br>")
        esc = re.sub(r"(https?://[^\s<]+)", lambda mm: f'<a href="{mm.group(1)}" style="color:#2F334D">{mm.group(1)}</a>', esc)
        out.append(f'<p style="font-family:{EMAIL_FONT};font-size:12pt;line-height:1.4;margin:0 0 1em">{esc}</p>')
    return (f'<html><body style="font-family:{EMAIL_FONT};font-size:12pt;color:#000000">'
            + "".join(out) + "</body></html>")


def same_mail(m, to, subject, days=7):
    """Mail already in Drafts or Sent to this address with this subject (Re: and Fwd: stripped) in the last days.
    Jonathan, 2026-10-05, after two chats each drafted a rebook email to the same company: "Is there a check that
    email sends are not duplicates". Returns [(folder, date, subject)]."""
    import time
    from email.utils import parseaddr

    def norm(s):
        s = str(make_header(decode_header(s or "")))
        return re.sub(r"^\s*((re|fwd?|aw)\s*:\s*)+", "", s, flags=re.I).strip().lower()

    addr = parseaddr(to)[1].lower()
    want = norm(subject)
    since = time.strftime("%d-%b-%Y", time.localtime(time.time() - days * 86400))
    hits = []
    for folder in ("Drafts", "Sent"):
        try:
            m.select(f'"{folder}"', readonly=True)
            typ, data = m.search(None, "TO", f'"{addr}"', "SINCE", since)
        except Exception:  # noqa: BLE001  a folder that cannot be read is not a reason to refuse the draft
            continue
        for i in (data[0].split() if typ == "OK" else []):
            typ, d = m.fetch(i, "(BODY.PEEK[HEADER.FIELDS (SUBJECT DATE)])")
            if typ != "OK" or not d or not d[0]:
                continue
            h = email.message_from_bytes(d[0][1])
            if norm(h.get("Subject")) == want:
                hits.append((folder, h.get("Date", ""), str(make_header(decode_header(h.get("Subject", ""))))))
    return hits


def cmd_draft(m, spec_path, attachments, force=False):
    import mimetypes
    import time
    from email.message import EmailMessage
    from email.utils import formatdate, make_msgid

    env = load_env()
    text = Path(spec_path).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    head, _, body = text.partition("\n\n")
    headers = {}
    for line in head.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    if "to" not in headers or "subject" not in headers:
        sys.exit("spec needs at least To: and Subject: header lines, then a blank line, then the body")
    dupes = same_mail(m, headers["to"], headers["subject"])
    if dupes and not force:
        lines = "\n".join(f"  {f}: {d} | {s}" for f, d, s in dupes)
        print(f"NOT drafted: {len(dupes)} message(s) to {headers['to']} with this subject already in the last 7 days:\n{lines}\n"
              f"Read them first. To place it anyway: draft <spec.txt> --force")
        return False
    msg = EmailMessage()
    msg["From"] = f"Jonathan <{env['PROTON_USER']}>"
    msg["To"] = headers["to"]
    if headers.get("cc"):
        msg["Cc"] = headers["cc"]
    msg["Subject"] = headers["subject"]
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=env["PROTON_USER"].split("@")[-1])
    if headers.get("in-reply-to"):
        msg["In-Reply-To"] = headers["in-reply-to"]
        msg["References"] = headers.get("references") or headers["in-reply-to"]
    msg.set_content(body.strip() + "\n")
    msg.add_alternative(body_html(body), subtype="html")
    for path in attachments:
        p = Path(path)
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        msg.add_attachment(p.read_bytes(), maintype=maintype, subtype=subtype, filename=p.name)
    typ, resp = m.append("Drafts", "\\Draft", imaplib.Time2Internaldate(time.time()), msg.as_bytes())
    if typ != "OK":
        sys.exit(f"APPEND to Drafts failed: {resp}")
    print(f"draft placed in Drafts: To {msg['To']} | Cc {msg.get('Cc','')} | Subject {msg['Subject']} | {len(attachments)} attachment(s)")
    return True


def cmd_inbox_test(m, spec_path):
    """Lay one unread message in Jonathan's own INBOX, as a prospect would get it. A copy test; nothing is sent."""
    import time
    from email.message import EmailMessage
    from email.utils import formatdate, make_msgid, parseaddr

    env = load_env()
    domain = env["PROTON_USER"].split("@")[-1].lower()
    text = Path(spec_path).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    head, _, body = text.partition("\n\n")
    headers = {}
    for line in head.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    if "from" not in headers or "subject" not in headers:
        sys.exit("spec needs From: and Subject: header lines, then a blank line, then the body")
    if not parseaddr(headers["from"])[1].lower().endswith("@" + domain):
        sys.exit(f"From must be an @{domain} address: this is a test of our own copy, never mail made to look like someone else's")
    msg = EmailMessage()
    msg["From"] = headers["from"]
    msg["To"] = env["PROTON_USER"]
    msg["Subject"] = headers["subject"]
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=domain)
    msg["X-Monarc-Test"] = headers.get("test", "copy")
    msg.set_content(body.strip() + "\n")
    msg.add_alternative(body_html(body), subtype="html")
    typ, resp = m.append("INBOX", "", imaplib.Time2Internaldate(time.time()), msg.as_bytes())
    if typ != "OK":
        sys.exit(f"APPEND to INBOX failed: {resp}")
    print(f"test message placed in INBOX, unread: From {msg['From']} | Subject {msg['Subject']}")


def main(argv):
    if len(argv) < 2 or argv[1] not in ("folders", "recent", "search", "attachments", "draft", "triage", "read", "report", "inbox-test"):
        print(__doc__)
        sys.exit(1)
    m = connect()
    try:
        if argv[1] == "draft":
            if len(argv) < 3:
                sys.exit("draft needs <spec.txt> [attachment ...]")
            force = "--force" in argv
            if not cmd_draft(m, argv[2], [a for a in argv[3:] if a != "--force"], force=force):
                sys.exit(1)
        elif argv[1] == "triage":
            n = int(argv[2]) if len(argv) > 2 else 30
            cmd_triage(m, n, argv[3] if len(argv) > 3 else "INBOX")
        elif argv[1] == "read":
            if len(argv) < 3:
                sys.exit("read needs <id>")
            cmd_read(m, argv[2], argv[3] if len(argv) > 3 else "INBOX")
        elif argv[1] == "report":
            if len(argv) < 3:
                sys.exit("report needs <spec.txt>")
            cmd_report(m, argv[2])
        elif argv[1] == "inbox-test":
            if len(argv) < 3:
                sys.exit("inbox-test needs <spec.txt>")
            cmd_inbox_test(m, argv[2])
        elif argv[1] == "folders":
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
