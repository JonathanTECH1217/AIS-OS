#!/usr/bin/env python3
"""
site_sync.py - pull, diff, and push monarcbuild.com files between Hostinger
public_html and the local mirror at projects/monarcbuild-site/public_html.

Commands:
  python scripts/site_sync.py list
  python scripts/site_sync.py pull
  python scripts/site_sync.py diff
  python scripts/site_sync.py push <path> [path ...]   (paths relative to the mirror)

Reads .env at the AIOS root. No third-party packages.
Transport: HOSTINGER_TRANSPORT=sftp (system sftp.exe, key auth) or ftps (ftplib).
Never deletes remote files. Push sends only the paths you name.

bike-method-phase: 1 (run by hand, watch everything)
"""

import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from ftplib import FTP_TLS, error_perm
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIRROR = ROOT / "projects" / "monarcbuild-site" / "public_html"
ARCHIVES = ROOT / "archives"


# ---------- config ----------

def load_env(path=ROOT / ".env"):
    if not path.exists():
        sys.exit(f".env not found at {path}. See references/hostinger-api.md.")
    env = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def cfg():
    env = load_env()
    transport = env.get("HOSTINGER_TRANSPORT", "sftp").lower()
    c = {
        "transport": transport,
        "host": env.get("HOSTINGER_HOST"),
        "port": int(env.get("HOSTINGER_PORT", "65002" if transport == "sftp" else "21")),
        "user": env.get("HOSTINGER_USER"),
        "password": env.get("HOSTINGER_PASS"),
        "key": env.get("HOSTINGER_KEY"),
        "remote_dir": env.get("HOSTINGER_REMOTE_DIR", "public_html" if transport == "sftp" else "/"),
    }
    missing = [k for k in ("host", "user") if not c[k]]
    if transport == "sftp" and not c["key"]:
        missing.append("key (HOSTINGER_KEY)")
    if transport == "ftps" and not c["password"]:
        missing.append("password (HOSTINGER_PASS)")
    if missing:
        sys.exit(f"Missing in .env: {', '.join(missing)}")
    return c


# ---------- sftp transport (system sftp.exe, batch mode) ----------

def sftp_run(c, batch_lines):
    with tempfile.NamedTemporaryFile("w", suffix=".sftp", delete=False, encoding="utf-8") as f:
        f.write("\n".join(batch_lines) + "\n")
        batch = f.name
    cmd = [
        "sftp", "-b", batch, "-P", str(c["port"]), "-i", c["key"],
        "-o", "StrictHostKeyChecking=accept-new", "-o", "BatchMode=yes",
        f"{c['user']}@{c['host']}",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        os.unlink(batch)
    if r.returncode != 0:
        sys.exit(f"sftp failed ({r.returncode}):\n{r.stdout}\n{r.stderr}")
    return r.stdout


def sftp_list(c):
    return sftp_run(c, [f"ls -la {c['remote_dir']}"])


def sftp_pull(c):
    MIRROR.mkdir(parents=True, exist_ok=True)
    # get -r copies the remote directory INTO the target, so pull into a temp
    # folder and move the contents up one level.
    tmp = MIRROR.parent / "_pull_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    sftp_run(c, [f"lcd {tmp}", f"get -r {c['remote_dir']}"])
    pulled = next(tmp.iterdir())
    for item in pulled.iterdir():
        dest = MIRROR / item.name
        if dest.exists():
            shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
        shutil.move(str(item), str(dest))
    shutil.rmtree(tmp)


def sftp_push(c, rel_paths):
    lines = []
    for rel in rel_paths:
        local = MIRROR / rel
        remote = f"{c['remote_dir'].rstrip('/')}/{rel.replace(os.sep, '/')}"
        remote_parent = remote.rsplit("/", 1)[0]
        lines.append(f"-mkdir {remote_parent}")
        lines.append(f"put {local} {remote}")
    return sftp_run(c, lines)


# ---------- ftps transport (ftplib) ----------

def ftps_connect(c):
    ftp = FTP_TLS()
    ftp.connect(c["host"], c["port"], timeout=30)
    ftp.login(c["user"], c["password"])
    ftp.prot_p()
    if c["remote_dir"] and c["remote_dir"] != "/":
        ftp.cwd(c["remote_dir"])
    return ftp


def ftps_walk(ftp, path="."):
    """Yield (dirpath, [files]) using MLSD when available, NLST fallback."""
    dirs, files = [], []
    try:
        for name, facts in ftp.mlsd(path):
            if name in (".", ".."):
                continue
            (dirs if facts.get("type") == "dir" else files).append(name)
    except error_perm:
        for name in ftp.nlst(path):
            base = name.rsplit("/", 1)[-1]
            try:
                ftp.cwd(f"{path}/{base}")
                ftp.cwd("..") if path == "." else ftp.cwd(path)
                dirs.append(base)
            except error_perm:
                files.append(base)
    yield path, files
    for d in dirs:
        yield from ftps_walk(ftp, f"{path}/{d}")


def ftps_list(c):
    ftp = ftps_connect(c)
    out = []
    ftp.retrlines("LIST", out.append)
    ftp.quit()
    return "\n".join(out)


def ftps_pull(c):
    ftp = ftps_connect(c)
    for dirpath, files in ftps_walk(ftp):
        local_dir = MIRROR / dirpath.lstrip("./")
        local_dir.mkdir(parents=True, exist_ok=True)
        for fn in files:
            with open(local_dir / fn, "wb") as fh:
                ftp.retrbinary(f"RETR {dirpath}/{fn}", fh.write)
    ftp.quit()


def ftps_push(c, rel_paths):
    ftp = ftps_connect(c)
    for rel in rel_paths:
        local = MIRROR / rel
        remote = rel.replace(os.sep, "/")
        parent = remote.rsplit("/", 1)[0] if "/" in remote else ""
        if parent:
            try:
                ftp.mkd(parent)
            except error_perm:
                pass
        with open(local, "rb") as fh:
            ftp.storbinary(f"STOR {remote}", fh)
    ftp.quit()
    return "ok"


# ---------- commands ----------

def backup_mirror():
    if not MIRROR.exists() or not any(MIRROR.iterdir()):
        return None
    ts = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    dest = ARCHIVES / f"site-{ts}"
    shutil.copytree(MIRROR, dest)
    return dest


def cmd_list(c):
    print(sftp_list(c) if c["transport"] == "sftp" else ftps_list(c))


def cmd_pull(c):
    b = backup_mirror()
    if b:
        print(f"Backed up previous mirror to {b}")
    (sftp_pull if c["transport"] == "sftp" else ftps_pull)(c)
    n = sum(1 for p in MIRROR.rglob("*") if p.is_file())
    print(f"Pulled {n} files into {MIRROR}")


def cmd_diff(c):
    """Compare the mirror against the most recent backup, if any."""
    backups = sorted(ARCHIVES.glob("site-*"))
    if not backups:
        print("No backup to compare against. Run pull twice, or edit then diff.")
        return
    last = backups[-1]
    changed = []
    for p in MIRROR.rglob("*"):
        if p.is_file():
            rel = p.relative_to(MIRROR)
            q = last / rel
            if not q.exists() or q.read_bytes() != p.read_bytes():
                changed.append(str(rel))
    print("\n".join(changed) if changed else "No changes vs last backup.")


def cmd_push(c, rel_paths):
    if not rel_paths:
        sys.exit("push needs at least one path relative to the mirror.")
    for rel in rel_paths:
        if not (MIRROR / rel).is_file():
            sys.exit(f"Not a file in the mirror: {rel}")
    print(f"Pushing {len(rel_paths)} file(s) to {c['host']}:{c['remote_dir']}")
    (sftp_push if c["transport"] == "sftp" else ftps_push)(c, rel_paths)
    print("Done. Verify live before pushing more.")


def main(argv):
    if len(argv) < 2 or argv[1] not in ("list", "pull", "diff", "push"):
        print(__doc__)
        sys.exit(1)
    c = cfg()
    {"list": lambda: cmd_list(c),
     "pull": lambda: cmd_pull(c),
     "diff": lambda: cmd_diff(c),
     "push": lambda: cmd_push(c, argv[2:])}[argv[1]]()


if __name__ == "__main__":
    main(sys.argv)
