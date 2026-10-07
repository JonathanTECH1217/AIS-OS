"""Move the AIOS keys from this PC to a Mac in one locked file (Jonathan, 2026-10-07: "securely transfer credentials to my Mac OS").

  python scripts/secrets_transfer.py pack            # on the PC: writes monarc-keys-<date>.locked to the Desktop
  python scripts/secrets_transfer.py names <file>    # either machine: the key names and files inside, never a value
  python3 scripts/secrets_transfer.py unpack <file>  # on the Mac: puts each file back in its place, owner-only

What goes in: ~/.monarc/secrets.env, ~/.monarc/kalshi.pem, and the repo's .env (any that exist), plus any --add <path>
under the home folder. The file is sealed with AES-256-GCM under a key made from a passphrase you type (scrypt, about
a second to make). The passphrase is never stored or printed. Carry the file by USB stick or Proton Drive; never send
the passphrase in the same place as the file. Delete the .locked file from both machines once the Mac is set up.

Git never sees any of it: the .locked file is written outside the repo and `*.locked` is in .gitignore.
"""
import argparse
import base64
import getpass
import io
import json
import os
import stat
import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAGIC = b"MONARC-KEYS-1\n"
N, R, P = 2 ** 15, 8, 1           # scrypt cost: ~32 MB, about a second


def home():
    return Path(os.environ.get("MONARC_HOME_OVERRIDE") or Path.home())


def repo():
    return Path(os.environ.get("MONARC_REPO_OVERRIDE") or ROOT)


def sources(extra):
    """(the place it goes back to, written relative to home or repo, the file on this machine)."""
    h, r = home(), repo()
    items = [("home:.monarc/secrets.env", h / ".monarc" / "secrets.env"),
             ("home:.monarc/kalshi.pem", h / ".monarc" / "kalshi.pem"),
             ("repo:.env", r / ".env")]
    for a in extra or []:
        p = Path(a).expanduser().resolve()
        try:
            items.append(("home:" + p.relative_to(h.resolve()).as_posix(), p))
        except ValueError:
            sys.exit(f"--add takes files under your home folder only: {a}")
    return [(k, p) for k, p in items if p.is_file()]


def passphrase(confirm):
    pw = os.environ.get("MONARC_KEYS_PASS")   # tests only; a person types it
    if pw:
        return pw
    pw = getpass.getpass("Passphrase (5 words or 20+ characters): ")
    if confirm:
        if len(pw) < 16:
            sys.exit("Too short. Use 16 characters or more; a few random words is easiest.")
        if getpass.getpass("Same passphrase again: ") != pw:
            sys.exit("The two did not match. Nothing written.")
    return pw


def key_from(pw, salt):
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    return Scrypt(salt=salt, length=32, n=N, r=R, p=P).derive(pw.encode("utf-8"))


def names_in(data):
    """The variable names in an env file, never the values."""
    out = []
    for line in data.decode("utf-8-sig", "replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            out.append(line.split("=", 1)[0].replace("export ", "").strip())
    return out


def cmd_pack(a):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    items = sources(a.add)
    if not items:
        sys.exit("No key files found on this machine.")
    buf = io.BytesIO()
    manifest = []
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for k, p in items:
            data = p.read_bytes()
            z.writestr(k.replace(":", "/", 1), data)
            manifest.append({"to": k, "bytes": len(data), "names": names_in(data) if p.suffix in (".env", "") or p.name.endswith(".env") else []})
        z.writestr("manifest.json", json.dumps({"made": date.today().isoformat(), "files": manifest}, indent=1))
    pw = passphrase(confirm=True)
    salt, nonce = os.urandom(16), os.urandom(12)
    sealed = AESGCM(key_from(pw, salt)).encrypt(nonce, buf.getvalue(), MAGIC)
    out = Path(a.out).expanduser() if a.out else (home() / "Desktop" / f"monarc-keys-{date.today().isoformat()}.locked")
    try:
        out.resolve().relative_to(repo().resolve())
        sys.exit("The locked file must not be written inside the repo. Pick a path outside it (the Desktop is the default).")
    except ValueError:
        pass
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(MAGIC + base64.b64encode(salt + nonce) + b"\n" + sealed)
    print(f"Sealed {len(items)} files into {out}")
    for m in manifest:
        print(f"  {m['to']}  ({len(m['names'])} keys)" if m["names"] else f"  {m['to']}")
    print("Carry it by USB stick or Proton Drive. Send the passphrase some other way, or just remember it.")


def open_file(path):
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    raw = Path(path).expanduser().read_bytes()
    if not raw.startswith(MAGIC):
        sys.exit("That is not a Monarc keys file.")
    head, sealed = raw[len(MAGIC):].split(b"\n", 1)
    sn = base64.b64decode(head)
    try:
        plain = AESGCM(key_from(passphrase(confirm=False), sn[:16])).decrypt(sn[16:28], sealed, MAGIC)
    except InvalidTag:
        sys.exit("Wrong passphrase, or the file was changed on the way. Nothing written.")
    return zipfile.ZipFile(io.BytesIO(plain))


def cmd_names(a):
    z = open_file(a.file)
    m = json.loads(z.read("manifest.json"))
    print(f"Made {m['made']}:")
    for f in m["files"]:
        print(f"  {f['to']}: " + (", ".join(f["names"]) if f["names"] else f"{f['bytes']} bytes"))


def cmd_unpack(a):
    z = open_file(a.file)
    m = json.loads(z.read("manifest.json"))
    for f in m["files"]:
        where, rel = f["to"].split(":", 1)
        dest = (home() if where == "home" else repo()) / rel
        data = z.read(f["to"].replace(":", "/", 1))
        if dest.exists() and dest.read_bytes() != data:
            if not a.force:
                print(f"  kept: {dest} already exists and differs (run again with --force to replace it; the old one is saved as .bak)")
                continue
            dest.with_name(dest.name + ".bak").write_bytes(dest.read_bytes())
        dest.parent.mkdir(parents=True, exist_ok=True)
        if where == "home":
            try:
                os.chmod(dest.parent, stat.S_IRWXU)
            except OSError:
                pass
        dest.write_bytes(data)
        try:
            os.chmod(dest, stat.S_IRUSR | stat.S_IWUSR)    # 600: only you can read it
        except OSError:
            pass
        print(f"  wrote {dest}")
    print("Done. Delete the .locked file from this Mac and from the PC's Desktop.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("pack"); s.add_argument("--out"); s.add_argument("--add", action="append")
    s = sub.add_parser("names"); s.add_argument("file")
    s = sub.add_parser("unpack"); s.add_argument("file"); s.add_argument("--force", action="store_true")
    a = ap.parse_args()
    {"pack": cmd_pack, "names": cmd_names, "unpack": cmd_unpack}[a.cmd](a)


if __name__ == "__main__":
    main()
