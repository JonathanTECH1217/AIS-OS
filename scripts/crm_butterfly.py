"""Butterfly: the clone, opened from the CRM's logo (Jonathan, 2026-10-05: "It should literally just be a button.
That's the logo. When I click on the logo, there should just be three little options... One is to run a skill, one
is to create a new project, and one is to work on an existing project... A project can either be an artifact. It
can be a campaign or it can be a skill.").

The CRM server imports this. It reads three things and opens one:

  skills     .claude/skills/*/SKILL.md, the name and one line each.
  workflows  live under a skill (Jonathan, 2026-10-05: "workflows would live underneath of skills"): one file each in
             .claude/skills/<skill>/workflows/. The SDR skill holds the first four. A workflow file opens with its
             title, a "Status:" line, and a "One line:" line; those are what the menu shows.
  projects   projects/crm/butterfly.json (the ones made here, and any chat pinned by hand), the CRM's campaigns, the
             workflows, the skills, and the groups in projects/crm/artifacts.json
  chats      the Claude Code session files under ~/.claude/projects for this repo. A chat opened from here starts with
             a line that ends "(butterfly: <project id>)"; that tag in a chat's first message is how a project finds
             its chat again. A "session" on a butterfly.json row pins a chat that was started before the tag existed.
  open       VS Code's link vscode://anthropic.claude-code/open (session=<id> to go back into a chat, prompt=<text>
             for a new one with the first line typed and not sent). A chat only opens in the VS Code window of the
             folder it was started in, so that folder is brought to the front first.

BUTTERFLY_DRY=1 in the environment returns what would be opened and opens nothing (the tests).
"""
import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "projects" / "crm" / "butterfly.json"
SKILLS = ROOT / ".claude" / "skills"
SESSIONS = Path.home() / ".claude" / "projects"
URI = "vscode://anthropic.claude-code/open"
KINDS = ("artifact", "campaign", "skill", "workflow")
HEAD = 256 * 1024                     # a chat's first message sits in the first lines of its file
TAG_RE = re.compile(r"\(butterfly: ([a-z0-9][a-z0-9_.-]{1,80})\)")
SESSION_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
WAIT_OPEN, WAIT_NEW = 0.8, 6.0        # seconds for the folder's window to take the front: already open, or starting

_lock = threading.Lock()
_heads = {}                           # session file -> (bytes read, {"cwd", "tag"})


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:60]


# ---------------------------------------------------------------- the file

def load():
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"projects": []}


def save(cfg):
    FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- skills

def _one_line(desc):
    """What the skill does, not when to use it: the first sentence that does not open with "Use"."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", desc or "") if p.strip()]
    pick = next((p for p in parts if not re.match(r"Use (when|on|at|only)\b", p)), parts[0] if parts else "")
    return pick if len(pick) <= 150 else pick[:147].rstrip() + "..."


def skills():
    out = []
    for f in sorted(SKILLS.glob("*/SKILL.md")):
        m = re.match(r"^---\s*\n(.*?)\n---", f.read_text(encoding="utf-8", errors="replace"), re.S)
        if not m:
            continue
        meta = dict(re.findall(r"^([a-z-]+):\s*(.*)$", m.group(1), re.M))
        name = meta.get("name", f.parent.name).strip()
        out.append({"name": name, "kind": "skill", "label": "/" + name,
                    "line": _one_line(meta.get("description", "").strip().strip('"')),
                    "hint": meta.get("argument-hint", "").strip().strip('"')})
    return out


def workflows():
    """Every workflow file under a skill: .claude/skills/<skill>/workflows/<slug>.md, in the skill's own order."""
    out = []

    def order(f):  # the order the skill's own page names them in; a file it does not name goes last, by name
        try:
            named = re.findall(r"workflows/([a-z0-9-]+)\.md", (f.parent.parent / "SKILL.md").read_text(encoding="utf-8", errors="replace"))
        except OSError:
            named = []
        return (f.parent.parent.name, named.index(f.stem) if f.stem in named else len(named), f.stem)

    for f in sorted(SKILLS.glob("*/workflows/*.md"), key=order):
        text = f.read_text(encoding="utf-8", errors="replace")
        skill, slug = f.parent.parent.name, f.stem
        title = re.search(r"^#\s+(.+)$", text, re.M)
        line = re.search(r"^One line:\s*(.+)$", text, re.M)
        status = re.search(r"Status:\s*([^\n]+)", text)
        out.append({"name": f"{skill}:{slug}", "skill": skill, "slug": slug, "kind": "workflow",
                    "label": title.group(1).strip() if title else slug.replace("-", " ").capitalize(),
                    "line": line.group(1).strip() if line else "", "status": status.group(1).strip().rstrip(".") if status else ""})
    return out


# ---------------------------------------------------------------- chats

def _head(path, size):
    hit = _heads.get(path)
    if hit and hit[0] == min(size, HEAD):
        return hit[1]
    info = {"cwd": None, "tag": None}
    try:
        with open(path, "rb") as fh:
            raw = fh.read(HEAD).decode("utf-8", errors="ignore")
    except OSError:
        return info
    for ln in raw.splitlines():
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if not info["cwd"] and d.get("cwd"):
            info["cwd"] = d["cwd"]
        if d.get("type") == "user":      # the first thing he sent: the tag is looked for here and nowhere else
            c = (d.get("message") or {}).get("content")
            text = c if isinstance(c, str) else " ".join(x.get("text", "") for x in c or [] if isinstance(x, dict))
            m = TAG_RE.search(text)
            info["tag"] = m.group(1) if m else None
            break
    _heads[path] = (min(size, HEAD), info)
    return info


def chats():
    """Every Claude Code chat started in this repo or a folder under it, newest first."""
    want = re.sub(r"[^A-Za-z0-9]", "-", str(ROOT)).lower()
    out = []
    if not SESSIONS.is_dir():
        return out
    for d in SESSIONS.iterdir():
        if not d.is_dir() or not d.name.lower().startswith(want):
            continue
        for f in d.glob("*.jsonl"):
            if not SESSION_RE.match(f.stem):
                continue
            st = f.stat()
            h = _head(str(f), st.st_size)
            out.append({"id": f.stem, "cwd": h["cwd"], "tag": h["tag"], "mtime": st.st_mtime})
    return sorted(out, key=lambda c: c["mtime"], reverse=True)


def workspace(cfg, all_chats):
    """Where a new chat starts: the folder named in butterfly.json, else the folder of his latest chat, else the repo."""
    if cfg.get("workspace"):
        return str((ROOT / cfg["workspace"]).resolve())
    return next((c["cwd"] for c in all_chats if c["cwd"] and Path(c["cwd"]).is_dir()), str(ROOT))


# ---------------------------------------------------------------- projects

def projects(campaigns=(), sources=(), artifact_cfg=None):
    cfg, all_chats = load(), chats()
    by_id = {c["id"]: c for c in all_chats}
    by_tag = {}
    for c in all_chats:                   # newest first, so the first chat seen for a tag is the one to open
        if c["tag"]:
            by_tag.setdefault(c["tag"], c)
    rows, seen = [], set()

    def add(pid, kind, name, line, prompt, session=None):
        if pid in seen:
            return
        seen.add(pid)
        chat = (by_id.get(session) if session else None) or by_tag.get(pid)
        rows.append({"id": pid, "kind": kind, "name": name, "line": line or "", "prompt": prompt,
                     "chat": chat["id"] if chat else None, "cwd": chat["cwd"] if chat else None,
                     "when": datetime.fromtimestamp(chat["mtime"]).isoformat(timespec="minutes") if chat else None})

    for p in cfg.get("projects", []):     # the ones made here come first: they can take the place of a row below
        if p.get("campaign"):
            seen.add("campaign-" + p["campaign"].lower())
        add(p["id"], p.get("kind", "skill"), p.get("name", p["id"]), p.get("line", ""),
            f'{p.get("name", p["id"])}: {p.get("line", "")}'.rstrip(": "), p.get("session"))
    label = {s["id"]: s.get("Label") or s.get("Name") for s in sources}
    for c in campaigns:
        where = " · ".join(x for x in (label.get((c.get("Channel") or [None])[0]), c.get("Status")) if x)
        add("campaign-" + c["id"].lower(), "campaign", c.get("Name") or "(no name)", where,
            f'Work on the campaign "{c.get("Name")}".')
    for w in workflows():
        add(f'workflow-{w["skill"]}-{w["slug"]}', "workflow", w["label"],
            " · ".join(x for x in (w["skill"].upper() if len(w["skill"]) <= 4 else w["skill"], w["status"]) if x),
            f'Work on the {w["label"]} workflow of the /{w["skill"]} skill (.claude/skills/{w["skill"]}/workflows/{w["slug"]}.md).')
    for s in skills():
        add("skill-" + s["name"], "skill", "/" + s["name"], s["line"], f'Work on the skill /{s["name"]}.')
    for cat in (artifact_cfg or {}).get("categories", []):
        for g in cat.get("groups", []):
            paths = ", ".join(g.get("paths", []))
            add(f'artifact-{slug(cat.get("key"))}-{slug(g.get("title"))}', "artifact", g.get("title", ""), cat.get("label", ""),
                f'Work on the artifact "{g.get("title")}"' + (f" ({paths})." if paths else "."))
    # the ones with a chat first, newest on top; the rest stay in the order they were listed (the catalog's order)
    rows.sort(key=lambda r: (r["when"] is None, -datetime.fromisoformat(r["when"]).timestamp() if r["when"] else 0))
    return rows


def menu(campaigns=(), sources=(), artifact_cfg=None):
    rows = projects(campaigns, sources, artifact_cfg)
    flows = [dict(w, label=w["label"], line=" · ".join(x for x in ("under /" + w["skill"], w["line"]) if x)) for w in workflows()]
    return {"skills": skills() + flows, "projects": [{k: v for k, v in r.items() if k != "prompt"} for r in rows], "kinds": list(KINDS),
            "channels": sorted(({"id": s["id"], "label": s.get("Label") or s.get("Name")} for s in sources), key=lambda c: c["label"] or "")}


# ---------------------------------------------------------------- open

def _window_open(folder):
    """Is a VS Code window for this folder already up? Its title holds the folder's name."""
    name, found = Path(folder).name.lower(), []
    try:
        user32 = ctypes.windll.user32
        proto = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def each(hwnd, _):
            n = user32.GetWindowTextLengthW(hwnd)
            if n and user32.IsWindowVisible(hwnd):
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                t = buf.value.lower()
                if "visual studio code" in t and name in t:
                    found.append(t)
            return True

        user32.EnumWindows(proto(each), 0)
    except Exception:  # noqa: BLE001  (not Windows, or the call is refused: treat the window as not open)
        return False
    return bool(found)


def launch(folder, session=None, prompt=None):
    """Bring the folder's VS Code window to the front, then open the chat in it. Returns what it did (or would do)."""
    if session and not SESSION_RE.match(session):
        return 422, {"errors": ["That is not a chat id."]}
    folder = str(Path(folder or ROOT).resolve())
    if not Path(folder).is_dir():
        return 422, {"errors": [f"The folder this chat lives in is gone: {folder}"]}
    uri = URI + ("?session=" + session if session else ("?prompt=" + quote(prompt, safe="") if prompt else ""))
    code = shutil.which("code")
    mac_code = Path("/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code")
    if not code and mac_code.exists():           # a Mac without the `code` shell command installed (2026-10-07)
        code = str(mac_code)
    plan ={"ok": True, "folder": folder, "uri": uri, "resume": bool(session), "vscode": bool(code)}
    if os.environ.get("BUTTERFLY_DRY") == "1":
        return 200, dict(plan, dry=True)
    if not code:
        return 422, {"errors": ["VS Code's `code` command is not on this machine's PATH, so the chat cannot be opened from here."]}

    def go():
        wait = WAIT_OPEN if _window_open(folder) else WAIT_NEW
        subprocess.Popen([code, folder], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        time.sleep(wait)
        if sys.platform == "win32":
            os.startfile(uri)  # noqa: S606  (a fixed vscode:// link built above from a checked id or a quoted line)
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", uri])   # a Mac (2026-10-07)

    threading.Thread(target=go, daemon=True).start()
    return 200, plan


def open_project(pid, campaigns=(), sources=(), artifact_cfg=None):
    row = next((r for r in projects(campaigns, sources, artifact_cfg) if r["id"] == pid), None)
    if not row:
        return 404, {"errors": ["No such project."]}
    if row["chat"]:
        return launch(row["cwd"], session=row["chat"])
    return launch(workspace(load(), chats()), prompt=f'{row["prompt"]} (butterfly: {row["id"]})')


def run_skill(name):
    """A skill by its name, or a workflow as "<skill>:<slug>" (typed into the chat as "/sdr cold-outreach ")."""
    if ":" in name:
        w = next((w for w in workflows() if w["name"] == name), None)
        if not w:
            return 404, {"errors": ["No such workflow."]}
        return launch(workspace(load(), chats()), prompt=f'/{w["skill"]} {w["slug"]} ')
    if name not in {s["name"] for s in skills()}:
        return 404, {"errors": ["No such skill."]}
    return launch(workspace(load(), chats()), prompt=f"/{name} ")


def new_project(kind, name, line, campaign=None):
    """Add the row and open its chat with the first line typed. `campaign` is the Airtable id of the row just made."""
    kind, name, line = (kind or "").strip().lower(), (name or "").strip(), (line or "").strip()
    if kind not in KINDS:
        return 422, {"errors": ["Pick one: artifact, campaign, skill, or workflow."]}
    if not name:
        return 422, {"errors": ["Give it a name."]}
    with _lock:
        cfg = load()
        taken = {p["id"] for p in cfg.get("projects", [])}
        base = pid = f"{kind}-{slug(name)}"
        n = 2
        while pid in taken:
            pid, n = f"{base}-{n}", n + 1
        row = {"id": pid, "kind": kind, "name": name, "line": line, "created": datetime.now().date().isoformat()}
        if campaign:
            row["campaign"] = campaign
        cfg.setdefault("projects", []).append(row)
        save(cfg)
    first = {"artifact": "New artifact", "campaign": "New campaign", "skill": "New skill", "workflow": "New workflow"}[kind]
    status, out = launch(workspace(cfg, chats()), prompt=f"{first}, {name}: {line}".rstrip(": ") + f" (butterfly: {pid})")
    return status, dict(out, project=row)
