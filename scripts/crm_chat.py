"""The chat box inside the CRM (Jonathan, 2026-10-05: "Option to open up a chat window inside of the operating
system... a chat box that sends a message to Claude").

The CRM server imports this. A chat here is the same clone as a chat in VS Code: the Claude Code program that the
VS Code extension ships, started without a window in the repo's folder, so it reads CLAUDE.md, the skills, and the
memory, and signs in with the same Claude account (no API key, no API bill). The page sends a line; this hands it to
the program on its input, reads what comes back line by line, and keeps it as a list of events the page asks for.

  ask      before a tool that needs his go (an edit, a command, a send), the program asks its host. The ask shows
           in the chat as a card with Allow and Deny, and the program waits. Nothing runs on a guess.
  session  each chat is a Claude Code session file under ~/.claude/projects, the same kind VS Code writes, so a chat
           started here opens in VS Code (crm_butterfly.launch) and goes on here after the server restarts (--resume).
  history  a chat picked up again is read back from its session file: what he typed and what the clone said.

CHAT_DRY=1 in the environment answers without starting the program (the page tests).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SESSIONS = Path.home() / ".claude" / "projects"
SESSION_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
IDLE = 20 * 60          # seconds without a message before a chat's program is closed (the chat itself stays)
KEEP = 1500             # events kept per chat
# Said to the clone once, at the start of a chat opened here.
HOUSE = ("This chat is the chat box inside the Monarc CRM, a narrow panel beside the page, not VS Code. "
         "Do not run the /inbox boot pass here unless Jonathan asks for it. Keep replies short. Use plain text and "
         "simple markdown (short lists, bold); no wide tables. File links are not clickable here, so name a file by its path.")

_lock = threading.Lock()
_chats = {}


def find_cli():
    """The Claude Code program: the newest one the VS Code extension ships, else `claude` on PATH."""
    ext = Path.home() / ".vscode" / "extensions"
    exe = "claude.exe" if sys.platform == "win32" else "claude"     # a Mac's extension ships it without .exe (2026-10-07)
    found = sorted(ext.glob(f"anthropic.claude-code-*/resources/native-binary/{exe}"),
                   key=lambda p: [int(n) for n in re.findall(r"\d+", p.parts[-4])[:3]])
    return str(found[-1]) if found else shutil.which("claude")


def _env():
    """The server's environment without the names a running Claude session leaves behind (the server is often started
    from one) and without an API key, so the chat signs in with his account and stands on its own."""
    return {k: v for k, v in os.environ.items() if not (k.startswith("CLAUDE") or k.startswith("ANTHROPIC"))}


def _tool_line(name, inp):
    """One short line for a tool the clone is using: what, and on what."""
    inp = inp or {}
    what = (inp.get("file_path") or inp.get("path") or inp.get("pattern") or inp.get("command") or inp.get("url")
            or inp.get("query") or inp.get("skill") or inp.get("description") or "")
    what = re.sub(r"\s+", " ", str(what))
    try:
        if what and Path(what).is_absolute():
            what = str(Path(what).resolve().relative_to(ROOT)).replace("\\", "/")
    except (OSError, ValueError):
        pass
    return name.replace("mcp__", "").replace("__", ": "), what[:200]


class Chat:
    def __init__(self, cwd, session=None):
        self.id = uuid.uuid4().hex[:12]
        self.cwd, self.session = cwd, session
        self.events, self.seq = [], 0
        self.cond = threading.Condition()
        self.proc, self.busy, self.asks, self.stopping = None, False, {}, False
        self.touched = time.time()
        self.wlock = threading.Lock()
        self.errs = []

    # ---- events

    def emit(self, kind, **data):
        with self.cond:
            if kind == "text":  # the whole reply has landed: the pieces it arrived in go
                while self.events and self.events[-1]["kind"] == "delta":
                    self.events.pop()
            self.seq += 1
            self.events.append(dict(data, kind=kind, seq=self.seq))
            del self.events[:-KEEP]
            self.cond.notify_all()

    def wait(self, since, timeout):
        """Events after `since`, waiting up to `timeout` seconds for the first one."""
        end = time.time() + timeout
        with self.cond:
            while self.seq <= since and time.time() < end:
                self.cond.wait(max(0.05, end - time.time()))
            return {"chat": self.id, "session": self.session, "busy": self.busy, "seq": self.seq,
                    "events": [e for e in self.events if e["seq"] > since]}

    # ---- the program

    def _write(self, obj):
        with self.wlock:
            self.proc.stdin.write((json.dumps(obj) + "\n").encode("utf-8"))
            self.proc.stdin.flush()

    def _start(self):
        exe = find_cli()
        if not exe:
            raise RuntimeError("Claude Code is not on this machine: no VS Code extension folder holds it, and `claude` is not on PATH.")
        args = [exe, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
                "--include-partial-messages", "--permission-prompt-tool", "stdio",
                "--disallowedTools", "AskUserQuestion",  # a question comes as words in the chat, which he answers there
                "--append-system-prompt", HOUSE]
        if self.session:
            args += ["--resume", self.session]
        self.proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.cwd,
                                     env=_env(), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        threading.Thread(target=self._read, args=(self.proc,), daemon=True).start()
        threading.Thread(target=self._read_err, args=(self.proc,), daemon=True).start()
        self._write({"type": "control_request", "request_id": "init", "request": {"subtype": "initialize", "hooks": None}})

    def _read_err(self, proc):
        for line in iter(proc.stderr.readline, b""):
            self.errs = (self.errs + [line.decode("utf-8", "replace").strip()])[-8:]

    def _read(self, proc):
        for line in iter(proc.stdout.readline, b""):
            try:
                self._take(json.loads(line))
            except ValueError:
                continue
            except Exception as e:  # noqa: BLE001  one odd line must not end the chat
                self.errs = (self.errs + [f"{type(e).__name__}: {e}"])[-8:]
        proc.wait()
        if self.proc is proc:
            self.proc, self.asks = None, {}
            if self.busy:
                self.busy = False
                said = " ".join(x for x in self.errs[-3:] if x)
                self.emit("error", text="The chat stopped before it finished." + (f" {said}" if said else ""))

    def _take(self, d):
        t = d.get("type")
        if d.get("session_id") and SESSION_RE.match(str(d["session_id"])):
            self.session = d["session_id"]
        top = not d.get("parent_tool_use_id")  # a helper agent's own talk stays out of the chat
        if t == "stream_event" and top:
            ev = d.get("event") or {}
            delta = ev.get("delta") or {}
            if ev.get("type") == "content_block_delta" and delta.get("type") == "text_delta" and delta.get("text"):
                self.emit("delta", text=delta["text"])
        elif t == "assistant" and top:
            for b in (d.get("message") or {}).get("content") or []:
                if b.get("type") == "text" and (b.get("text") or "").strip():
                    self.emit("text", text=b["text"])
                elif b.get("type") == "tool_use":
                    name, what = _tool_line(b.get("name") or "", b.get("input"))
                    self.emit("tool", name=name, what=what)
        elif t == "control_request":
            r = d.get("request") or {}
            if r.get("subtype") == "can_use_tool":
                self.asks[d["request_id"]] = r
                name, what = _tool_line(r.get("tool_name") or "", r.get("input"))
                inp = r.get("input") or {}
                detail = inp.get("command") or inp.get("new_string") or inp.get("content") or inp.get("prompt") or ""
                self.emit("ask", id=d["request_id"], name=name, what=what, detail=str(detail)[:1500],
                          always=bool(r.get("permission_suggestions")))
            else:  # a request this host has no answer for
                self._write({"type": "control_response", "response": {"subtype": "error", "request_id": d.get("request_id"),
                                                                     "error": "not supported by the CRM chat"}})
        elif t == "result":
            self.busy = False
            if self.stopping:  # his Stop ends the turn as an error in the program's words; in the chat it is a stop
                self.emit("note", text="Stopped.")
            elif d.get("is_error"):
                self.emit("error", text=str(d.get("result") or d.get("subtype") or "The chat ended on an error.")[:600])
            self.stopping = False
            self.emit("done")

    # ---- what the page asks for

    def send(self, text):
        self.touched = time.time()
        self.emit("user", text=text)
        self.busy, self.stopping = True, False
        if os.environ.get("CHAT_DRY") == "1":
            self.emit("text", text="Test mode: the clone was not started.")
            self.busy = False
            self.emit("done")
            return
        try:
            if not self.proc or self.proc.poll() is not None:
                self._start()
            self._write({"type": "user", "message": {"role": "user", "content": text}, "parent_tool_use_id": None,
                         "session_id": self.session or "default"})
        except Exception as e:  # noqa: BLE001
            self.busy = False
            self.emit("error", text=f"Could not reach the clone: {e}")
            self.emit("done")

    def answer(self, rid, allow, always=False):
        r = self.asks.pop(rid, None)
        if not r or not self.proc:
            return False
        if allow:
            res = {"behavior": "allow", "updatedInput": r.get("input") or {}}
            if always and r.get("permission_suggestions"):
                res["updatedPermissions"] = r["permission_suggestions"]
        else:
            res = {"behavior": "deny", "message": "Jonathan said no to this in the CRM chat. Do not try it another way; ask him what he wants instead."}
        self._write({"type": "control_response", "response": {"subtype": "success", "request_id": rid, "response": res}})
        self.emit("answered", id=rid, allow=bool(allow), always=bool(allow and always))
        return True

    def stop(self):
        if self.proc and self.busy:
            self.stopping = True
            for rid in list(self.asks):
                self.answer(rid, False)
            self._write({"type": "control_request", "request_id": "stop-" + uuid.uuid4().hex[:8], "request": {"subtype": "interrupt"}})

    def close(self):
        proc, self.proc = self.proc, None
        if proc:
            try:
                proc.stdin.close()
                proc.wait(timeout=5)
            except Exception:  # noqa: BLE001
                proc.kill()


# ---------------------------------------------------------------- the chats

def _reap():
    """Close the program of any chat left idle; its session file stays, so the next line picks it up again."""
    now = time.time()
    for c in list(_chats.values()):
        if c.proc and not c.busy and now - c.touched > IDLE:
            c.close()


def history(session):
    """What he typed and what the clone said, read from a session file, oldest first."""
    f = next(SESSIONS.glob(f"*/{session}.jsonl"), None) if SESSION_RE.match(session or "") else None
    out, cwd = [], None
    if not f:
        return out, cwd
    with open(f, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            cwd = cwd or d.get("cwd")
            if d.get("isSidechain") or d.get("isMeta") or d.get("type") not in ("user", "assistant"):
                continue
            c = (d.get("message") or {}).get("content")
            if d["type"] == "user":
                text = c if isinstance(c, str) else " ".join(b.get("text", "") for b in c or [] if isinstance(b, dict) and b.get("type") == "text")
                if text.strip() and not text.lstrip().startswith(("<", "[Request interrupted")):  # tool results and system notes are not his words
                    out.append(("user", text.strip()))
            else:
                for b in c or []:
                    if isinstance(b, dict) and b.get("type") == "text" and (b.get("text") or "").strip():
                        out.append(("text", b["text"]))
    return out[-80:], cwd


def get(cid):
    return _chats.get(cid)


def open_chat(cwd, session=None):
    """A new chat, or one picked up again by its session id with what was said read back in."""
    with _lock:
        _reap()
        if session:
            live = next((c for c in _chats.values() if c.session == session), None)
            if live:
                return live
            said, was = history(session)
            if not said:
                session = None  # the session file is gone: start fresh
        c = Chat(cwd, session)
        if session:
            c.cwd = was if was and Path(was).is_dir() else cwd  # a session resumes only from the folder it began in
            for kind, text in said:
                c.emit(kind, text=text, old=True)
        _chats[c.id] = c
        return c
