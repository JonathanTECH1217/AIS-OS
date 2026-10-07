"""Monarc Calls sessions (2026-10-01; reworked 2026-10-03 from Jonathan's Q32-Q45, brainstorms/2026-10-01-live-call-notes.md).

Two windows side by side: his real Airtable grid on the left (he types Status there as always) and the notes window
(projects/studio/calls.html) on the right. He presses Start. The mic child (scripts/calls_mic.py) turns whatever
microphone Windows uses into live words; nothing is recorded. Key notes come from plain rules (scripts/calls_notes.py)
and show live under "This call".

The cut (Q33): every few seconds while listening, the Prospects base is asked which rows' Status changed since the
last look (studio_prospects.Prospects.changes). Typing Status ends the call: everything heard since the last cut,
by each stretch's start, belongs to that row. Exceptions: blank Status (cleared), the words the CRM reads as "judged
from the listing, never dialed" (wrong vertical, unqualified, bad fit, commercial, no website, zip code), and a row
already cut this session (a fix) make no cut. A cut queues the dial's Outreach Log row. With key notes it becomes a
card under "To file" that he edits and pushes (Q36-Q37); without, its words are filed at once (Q44); with no speech
at all nothing is filed. Push writes the doc (Q38), fills a blank Email and Owner, and puts the kept notes in the log
row's Transcript (Q39). F9 anywhere, or the Pause button, pauses and resumes listening (Q40).

The session file, media/sessions/<YYYY-MM-DD HH-MM-SS>.jsonl, is the record: one line per event, flushed before
anything goes over the network, never rewritten; a half-written last line is skipped when it's read back.
  start  {id, airtable}        listen / pause         mic {device | error}
  seg    {start, end, words}   wall-clock seconds, from the mic child
  status {rec, at, words}      every Status change seen (the poll's watermark)
  cut    {n, rec, mb, name, status, at, from_t, website, email, owner, phone}
  card   {n, notes}            push {n, notes, path}   discard {n}   filed {n, path}
  write  {w, kind: log | set | log_note, ...}   wrote / fail / stuck {w, ...}
  stop   {why}
Docs land in projects/prospects/<MB-ID> <Company>/<YYYY-MM-DD HH-MM> call.md (STUDIO_PROSPECTS for tests).
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import studio_common as sc

SCRIPTS = Path(__file__).resolve().parent
POLL = float(os.environ.get("STUDIO_POLL_SECONDS") or 5)
# a Status edit is acted on once it has sat this long, so a half-typed word ("w" on the way to "wrong vertical") is
# never read; the next look sees the finished words with Airtable's final timestamp
SETTLE = float(os.environ.get("STUDIO_SETTLE_SECONDS") or 3)
REPLAY_MAX_AGE = 24 * 3600
CARD_DAYS = 3                    # open cards from session files this recent stay under "To file"
EASTERN = ZoneInfo("America/New_York")
EMAIL_RX = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", re.I)


class ActionError(Exception):
    def __init__(self, status, msg, **extra):
        super().__init__(msg)
        self.status = status
        self.extra = extra


# ---------------------------------------------------------------- the session file

def read_lines(path):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
                try:
                    out.append(json.loads(raw))
                except ValueError:
                    continue          # a line cut short by a crash
    except OSError:
        pass
    return out


def new_state():
    return {"id": None, "started": None, "listening": False, "paused": [], "segs": [], "cuts": [], "cards": {},
            "filed": {}, "writes": {}, "logids": {}, "cids": set(), "since": None, "stopped": None, "mic": None,
            "airtable": None}


def apply(st, ln):
    """One line onto the state (the session as it stands)."""
    k = ln.get("k")
    if ln.get("cid"):
        st["cids"].add(ln["cid"])
    if k == "start":
        st.update(id=ln.get("id"), started=ln.get("t"), since=ln.get("t"), airtable=ln.get("airtable"))
    elif k == "listen":
        st["listening"] = True
        if st["paused"] and st["paused"][-1][1] is None:
            st["paused"][-1][1] = ln.get("t")
    elif k == "pause":
        st["listening"] = False
        st["paused"].append([ln.get("t"), None])
    elif k == "mic":
        st["mic"] = {"device": ln.get("device"), "error": ln.get("error")}
    elif k == "seg":
        st["segs"].append({"start": ln["start"], "end": ln["end"], "words": ln.get("words") or []})
    elif k == "status":
        if ln.get("at") and (st["since"] is None or ln["at"] > st["since"]):
            st["since"] = ln["at"]
        for c in st["cuts"]:                  # a later fix to a row already cut: its card shows the new words
            if c["rec"] == ln.get("rec") and ln.get("words"):
                c["status"] = ln["words"]
    elif k == "cut":
        st["cuts"].append({x: ln.get(x) for x in ("n", "rec", "mb", "name", "status", "at", "from_t", "website",
                                                   "email", "owner", "phone")})
    elif k == "card":
        st["cards"][ln["n"]] = {"notes": ln.get("notes") or [], "state": "open", "t": ln.get("t")}
    elif k == "push" and ln.get("n") in st["cards"]:
        st["cards"][ln["n"]].update(state="pushed", path=ln.get("path"), notes=ln.get("notes") or [])
        st["filed"][ln["n"]] = {"path": ln.get("path"), "how": "pushed", "notes": len(ln.get("notes") or [])}
    elif k == "discard" and ln.get("n") in st["cards"]:
        st["cards"][ln["n"]]["state"] = "discarded"
    elif k == "filed":
        st["filed"][ln["n"]] = {"path": ln.get("path"), "how": "words", "notes": 0}
    elif k == "write":
        st["writes"][ln["w"]] = dict(ln, state="pending")
    elif k in ("wrote", "fail", "stuck") and ln.get("w") in st["writes"]:
        w = st["writes"][ln["w"]]
        if k == "wrote":
            w["state"] = "kept" if ln.get("kept") else "ok"
            w["kept"] = ln.get("kept")
            if w.get("kind") == "log" and ln.get("id"):
                st["logids"][w.get("n")] = ln["id"]
        else:
            w["state"] = k
            w["err"] = ln.get("err")
    elif k == "stop":
        st["stopped"] = {"t": ln.get("t"), "why": ln.get("why")}
        st["listening"] = False
    return st


def fold(lines):
    st = new_state()
    for ln in lines:
        apply(st, ln)
    return st


def call_segs(st, cut):
    """The stretches heard in one call: started at or after the cut before it, and before this one."""
    lo, hi = cut.get("from_t") or 0, cut.get("at") or 0
    return [s for s in st["segs"] if lo <= s["start"] < hi]


def running_segs(st):
    lo = st["cuts"][-1]["at"] if st["cuts"] else (st["started"] or 0)
    return [s for s in st["segs"] if s["start"] >= lo]


def is_skip(words):
    """The CRM's own reading of his words (crm_server.Api.CALL_TEXT_RULES): judged from the listing, never dialed."""
    from crm_server import Api
    return Api.call_outcome_from_text(words or "") == "Wrong vertical"


# ---------------------------------------------------------------- the doc

def safe_name(text):
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", str(text or "")).strip()
    s = re.sub(r"\s+", " ", s).rstrip(". ")
    return s[:80] or "Unnamed"


def unique_path(path):
    p, n = Path(path), 2
    while p.exists():
        p = path.with_name(f"{path.stem} ({n}){path.suffix}")
        n += 1
    return p


def note_line(n):
    from calls_notes import LABELS
    return f"- {LABELS.get(n.get('kind'), str(n.get('kind', '')).title())}: {str(n.get('text') or '').strip()}"


def write_doc(sid, cut, notes, segs):
    """projects/prospects/<MB-ID> <Company>/<YYYY-MM-DD HH-MM> call.md: who and when, his kept key notes, then every
    line heard with its time (laptop time, Eastern)."""
    when = datetime.fromtimestamp(segs[0]["start"] if segs else cut["at"])
    folder = sc.PROSPECTS / safe_name(f"{cut.get('mb') or 'MB-?'} {cut.get('name') or ''}")
    folder.mkdir(parents=True, exist_ok=True)
    path = unique_path(folder / f"{when:%Y-%m-%d %H-%M} call.md")
    out = [f"# {cut.get('name') or 'Unnamed'} · {cut.get('mb') or ''}".rstrip(" ·"), "",
           f"- Call: {when:%Y-%m-%d %H:%M} · Status typed: {cut.get('status') or ''}",
           f"- Airtable record: {cut.get('rec')} · Session: {sid} #{cut.get('n')}", "", "## Key notes", ""]
    out += [note_line(n) for n in notes] or ["(none)"]
    out += ["", "## Words heard", ""]
    for s in segs:
        text = " ".join(w[2] for w in s.get("words") or [])
        out.append(f"[{datetime.fromtimestamp(s['start']):%H:%M:%S}] {text}")
    if not segs:
        out.append("(nothing heard)")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text("\n".join(out) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path


def rel(path):
    try:
        return Path(path).resolve().relative_to(sc.ROOT).as_posix()
    except ValueError:
        return str(path)


# ---------------------------------------------------------------- F9, Windows-wide

class Hotkey:
    """F9 registered with Windows (RegisterHotKey) on a thread of its own, so it works while Airtable has focus."""
    VK_F9, MOD_NOREPEAT, WM_HOTKEY, WM_QUIT = 0x78, 0x4000, 0x0312, 0x0012

    def __init__(self, on_press):
        self.on_press = on_press
        self.tid = None
        self.ok = None
        self.ready = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()
        self.ready.wait(2)

    def _run(self):
        import ctypes
        import ctypes.wintypes as w
        user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
        self.tid = kernel32.GetCurrentThreadId()
        self.ok = bool(user32.RegisterHotKey(None, 1, self.MOD_NOREPEAT, self.VK_F9))
        self.ready.set()
        if not self.ok:
            return
        msg = w.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == self.WM_HOTKEY:
                    threading.Thread(target=self._press, daemon=True).start()
        finally:
            user32.UnregisterHotKey(None, 1)

    def _press(self):
        try:
            self.on_press()
        except Exception:  # noqa: BLE001
            traceback.print_exc()

    def stop(self):
        if self.tid and self.ok:
            import ctypes
            ctypes.windll.user32.PostThreadMessageW(self.tid, self.WM_QUIT, 0, 0)


# ---------------------------------------------------------------- the controller

class Controller:
    """One session at a time. The page's clicks are post(action, body) with a cid; a cid seen before is ignored, so
    the page can resend safely after a dropped connection."""

    def __init__(self, port, feed):
        self.port = port
        self.feed = feed
        self.lock = threading.RLock()
        self.idle = threading.Event()        # set when not listening: Studio prepares files only then
        self.idle.set()
        self.file, self.lines, self.st = None, [], new_state()
        self.others = {}                     # sid -> {"file", "st"}: earlier sessions with cards still open
        self.p, self.writer, self.phrases = None, None, None
        self.mic, self.level, self.mic_error = None, False, None
        self.poll_stop, self.poll_error = threading.Event(), None
        self.hotkey = None
        self._live = (None, [])

    # ---- plumbing
    def _prospects(self):
        if self.p is None:
            import studio_prospects as sp
            self.p = sp.Prospects()
            self.writer = sp.Writer(self.p, self._on_write)
        return self.p

    def _append(self, path, line):
        line = dict(line, t=line.get("t") or time.time())
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return line

    def _log(self, line):
        line = self._append(self.file, line)
        self.lines.append(line)
        apply(self.st, line)
        self.feed.bump()
        return line

    def _log_to(self, sid, line):
        """A line for whichever session it belongs to (a card from an earlier session, a late write result)."""
        if self.file and sid == self.st["id"]:
            return self._log(line)
        o = self.others.get(sid)
        path = o["file"] if o else sc.SESSIONS / f"{sid}.jsonl"
        if not Path(path).exists():
            return None
        line = self._append(path, line)
        if o:
            apply(o["st"], line)
        self.feed.bump()
        return line

    def active(self):
        return bool(self.file and self.st["id"] and not self.st["stopped"])

    def listening(self):
        return self.active() and self.st["listening"]

    # ---- the page's actions
    def post(self, action, body):
        body = body if isinstance(body, dict) else {}
        cid = body.get("cid")
        with self.lock:
            if cid and (cid in self.st["cids"] or any(cid in o["st"]["cids"] for o in self.others.values())):
                return 200, self.view()
            fn = getattr(self, "_a_" + action, None)
            if fn is None:
                return 404, {"errors": ["Unknown action."]}
            try:
                return 200, fn(body) or self.view()
            except ActionError as e:
                return e.status, dict({"errors": [str(e)]}, **e.extra)

    def _a_window(self, body):
        import studio_prospects as sp
        threading.Thread(target=sc.open_side_by_side, daemon=True,
                         args=(sp.GRID_URL, f"http://127.0.0.1:{self.port}/calls.html")).start()
        return {"ok": True}

    def _a_retry(self, body):
        if self.writer:
            self.writer.retry_now()
        return None

    def _a_start(self, body):
        if self.active():
            raise ActionError(409, "A session is already on.")
        import calls_notes as cn
        import studio_prospects as sp
        try:
            self.phrases = cn.load_phrases()
        except OSError as e:
            raise ActionError(409, f"Can't read the phrase file {cn.PHRASES} ({e}).")
        try:
            s = self._prospects().open(add_key=True)
        except sp.SchemaError as e:
            raise ActionError(409, str(e))
        except Exception as e:  # noqa: BLE001
            raise ActionError(502, f"Can't read the Prospects base ({type(e).__name__}: {str(e)[:160]}).")
        sid = time.strftime("%Y-%m-%d %H-%M-%S")
        self.file, self.lines, self.st = unique_session_file(sid), [], new_state()
        self.mic_error, self.poll_error, self._live = None, None, (None, [])
        brief = s.brief()
        self._log({"k": "start", "v": 2, "cid": body.get("cid"), "id": sid,
                   "airtable": {"base": sp.BASE, "table": sp.CONTACTS, "ids": brief["ids"], "names": brief["names"],
                                "logError": brief["logError"]}})
        self._start_mic()
        self._log({"k": "listen"})
        self.idle.clear()
        self.poll_stop.clear()
        threading.Thread(target=self._poll_loop, args=(self.st["id"],), daemon=True).start()
        self._hotkey_on()
        return None

    def _a_pause(self, body):
        if not self.listening():
            return None
        self._mic_send("pause")
        self._log({"k": "pause", "cid": body.get("cid")})
        self.idle.set()
        return None

    def _a_resume(self, body):
        if not self.active() or self.st["listening"]:
            return None
        if self.mic is None or self.mic.poll() is not None:
            self._start_mic()
        else:
            self._mic_send("resume")
        self._log({"k": "listen", "cid": body.get("cid")})
        self.idle.clear()
        return None

    def _a_toggle(self, body):
        """F9."""
        return self._a_pause(body) if self.listening() else self._a_resume(body)

    def _card(self, sid, n):
        st = self.st if sid in (None, self.st["id"]) else (self.others.get(sid) or {}).get("st")
        if not st or n not in st["cards"]:
            raise ActionError(404, "That card isn't there any more.")
        card = st["cards"][n]
        if card["state"] != "open":
            raise ActionError(409, "That card was already filed.")
        cut = next((c for c in st["cuts"] if c["n"] == n), None)
        return st, card, cut

    def _a_push(self, body):
        sid, n = body.get("sid") or self.st["id"], body.get("n")
        st, card, cut = self._card(sid, n)
        notes = []
        for x in body.get("notes") or []:
            kind, text = str(x.get("kind") or "").strip(), str(x.get("text") or "").strip()
            if kind and text:
                notes.append({"kind": kind[:20], "text": text[:600]})
        path = write_doc(sid, cut, notes, call_segs(st, cut))
        self._log_to(sid, {"k": "push", "cid": body.get("cid"), "n": n, "notes": notes, "path": rel(path)})
        email = next((m.group(0).lower() for x in notes if x["kind"] == "email" for m in [EMAIL_RX.search(x["text"])] if m), None)
        name = next((x["text"] for x in notes if x["kind"] == "name" and len(x["text"].split()) <= 4), None)
        for role, value in (("email", email), ("owner", name)):
            if value:
                self._queue(sid, {"kind": "set", "rec": cut["rec"], "role": role, "value": value, "rule": "blank_only",
                                  "n": n})
        if notes:
            import calls_notes as cn
            self._queue(sid, {"kind": "log_note", "key": f"{sid} #{n}", "n": n, "text": cn.as_text(notes),
                              "log_id": st["logids"].get(n)})
        return None

    def _a_discard(self, body):
        sid, n = body.get("sid") or self.st["id"], body.get("n")
        self._card(sid, n)
        self._log_to(sid, {"k": "discard", "cid": body.get("cid"), "n": n})
        return None

    def _a_stop(self, body):
        if not self.active():
            raise ActionError(409, "No session is on.")
        self._stop(body.get("cid"), "stopped")
        return None

    def _stop(self, cid, why):
        self.poll_stop.set()
        self._stop_mic()
        if self.hotkey:
            self.hotkey.stop()
            self.hotkey = None
        self._log({"k": "stop", "cid": cid, "why": why})
        self.idle.set()
        if any(c["state"] == "open" for c in self.st["cards"].values()):
            self.others[self.st["id"]] = {"file": self.file, "st": self.st}    # its cards wait under "To file"

    def _queue(self, sid, op):
        w = uuid.uuid4().hex[:12]
        op = dict(op, w=w)
        self._log_to(sid, dict(op, k="write"))
        p = self._prospects()
        if p.schema is None:              # after a restart nothing has read the columns yet
            try:
                p.open(add_key=False)
            except Exception:  # noqa: BLE001  (offline: the writer waits for the columns)
                traceback.print_exc()
        self.writer.add(dict(op, sid=sid, t=time.time()))

    # ---- the mic child
    def _start_mic(self):
        args = [sc.python_exe(), "-u", str(SCRIPTS / "calls_mic.py")]
        if os.environ.get("STUDIO_FAKE_MIC"):
            args.append("--fake")
        log = open(sc.HOME / "calls-mic.log", "a", encoding="utf-8")
        self.mic = sc.popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, bufsize=1,
                            text=True, encoding="utf-8")
        self.mic_error = None
        threading.Thread(target=self._read_mic, args=(self.mic, self.st["id"]), daemon=True).start()

    def _mic_send(self, cmd):
        try:
            if self.mic and self.mic.poll() is None:
                self.mic.stdin.write(cmd + "\n")
                self.mic.stdin.flush()
        except OSError:
            pass

    def _stop_mic(self):
        m, self.mic = self.mic, None
        if not m:
            return
        try:
            m.stdin.write("quit\n")
            m.stdin.flush()
            m.wait(3)
        except Exception:  # noqa: BLE001
            sc.kill_tree(m.pid)
        sc.untrack(m)
        self.level = False

    def _read_mic(self, proc, sid):
        for raw in proc.stdout:
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            kind = msg.get("type")
            with self.lock:
                if sid != self.st["id"] or not self.active():
                    continue
                if kind == "level":
                    self.level = bool(msg.get("speech"))
                    self.feed.bump(0.2)
                elif kind == "ready":
                    self._log({"k": "mic", "device": msg.get("device")})
                elif kind == "error":
                    self.mic_error = msg.get("error")
                    self._log({"k": "mic", "error": self.mic_error})
                elif kind == "seg" and self.st["listening"] and msg.get("words"):
                    self._log({"k": "seg", "start": msg["start"], "end": msg["end"], "words": msg["words"]})
        with self.lock:
            if proc is self.mic and self.active() and self.st["listening"]:
                self.mic_error = self.mic_error or "The microphone stopped. Press Resume to start it again."
                self._log({"k": "pause", "why": "mic stopped"})
                self.idle.set()
            self.level = False
            self.feed.bump()

    # ---- the poll and the cut
    def _poll_loop(self, sid):
        while not self.poll_stop.wait(POLL):
            with self.lock:
                if sid != self.st["id"] or not self.active():
                    return
                if not self.st["listening"]:
                    continue
                since = self.st["since"]
            try:
                rows = self.p.changes(since)
                self.poll_error = None
            except Exception as e:  # noqa: BLE001
                self.poll_error = f"Can't reach Airtable to see your Status ({type(e).__name__}); trying again."
                self.feed.bump()
                continue
            settled = time.time() - SETTLE
            for row in rows:                       # oldest first; stop at one still being typed (looked at again next time)
                if (row.get("changed_t") or 0) > settled:
                    break
                with self.lock:
                    if sid == self.st["id"] and self.active():
                        self.handle_change(row)

    def handle_change(self, row):
        """One Status change seen in Airtable (Q33)."""
        at = row.get("changed_t")
        if at is None or (self.st["since"] is not None and at <= self.st["since"]):
            return
        words = (row.get("status") or "").strip()
        self._log({"k": "status", "rec": row["id"], "at": at, "words": words})
        if not words or is_skip(words) or any(c["rec"] == row["id"] for c in self.st["cuts"]):
            return
        n = len(self.st["cuts"]) + 1
        from_t = self.st["cuts"][-1]["at"] if self.st["cuts"] else self.st["started"]
        cut = self._log({"k": "cut", "n": n, "rec": row["id"], "mb": row.get("mb"), "name": row.get("name"),
                         "status": words, "at": at, "from_t": from_t, "website": row.get("website"),
                         "email": row.get("email"), "owner": row.get("owner"), "phone": row.get("phone")})
        sid = self.st["id"]
        if row.get("mb"):
            self._queue(sid, {"kind": "log", "rec": row["id"], "mb": row["mb"], "n": n, "key": f"{sid} #{n}",
                              "day": datetime.fromtimestamp(at, EASTERN).date().isoformat()})
        segs = call_segs(self.st, cut)
        import calls_notes as cn
        notes = cn.extract(segs, self.phrases or cn.load_phrases(), website=row.get("website"), phone=row.get("phone"))
        if notes:
            self._log({"k": "card", "n": n, "notes": notes})
        elif any(s.get("words") for s in segs):
            self._log({"k": "filed", "n": n, "path": rel(write_doc(sid, cut, [], segs))})

    # ---- the Prospects base's answers (on the writer's thread)
    def _on_write(self, op, state, info):
        info = info or {}
        line = {"k": {"ok": "wrote", "kept": "wrote", "fail": "fail", "stuck": "stuck"}[state], "w": op["w"]}
        if state == "kept":
            line["kept"] = info.get("kept")
        if state in ("fail", "stuck"):
            line["err"] = info.get("error")
            if "retry_in" in info:
                line["retry_in"] = info["retry_in"]
        if info.get("id"):
            line["id"] = info["id"]
        with self.lock:
            self._log_to(op.get("sid"), line)

    # ---- the hotkey
    def _hotkey_on(self):
        if os.environ.get("STUDIO_FAKE_MIC") or os.environ.get("STUDIO_NO_HOTKEY") or self.hotkey:
            return
        try:
            self.hotkey = Hotkey(lambda: self.post("toggle", {}))
        except Exception:  # noqa: BLE001
            traceback.print_exc()
            self.hotkey = None

    # ---- after a restart
    def recover(self):
        """Writes the Prospects base never confirmed go again (older than a day: shown as stuck instead); open cards
        from the last few days come back under "To file"; a session the last server left on is closed (press Start)."""
        files = sorted(sc.SESSIONS.glob("*.jsonl"))
        replay = []
        cutoff = time.time() - CARD_DAYS * 86400
        for f in files[-20:]:
            st = fold(read_lines(f))
            if st.get("id") is None:
                continue
            if not st["stopped"]:
                self._append(f, {"k": "stop", "why": "the server restarted"})
                st = fold(read_lines(f))
            for w in st["writes"].values():
                if w["state"] not in ("pending", "fail"):
                    continue
                if time.time() - (w.get("t") or 0) > REPLAY_MAX_AGE:
                    self._append(f, {"k": "stuck", "w": w["w"], "err": "not confirmed within a day; not sent again"})
                else:
                    op = {x: w.get(x) for x in ("w", "kind", "rec", "role", "value", "mb", "day", "key", "n", "text",
                                                "log_id")}
                    replay.append(dict({k: v for k, v in op.items() if v is not None}, sid=st["id"], t=w.get("t")))
            if (st["started"] or 0) >= cutoff and any(c["state"] == "open" for c in st["cards"].values()):
                with self.lock:
                    self.others[st["id"]] = {"file": f, "st": st}
        if replay:
            try:
                self._prospects().open(add_key=False)
            except Exception:  # noqa: BLE001  (offline: the writer waits for the columns)
                traceback.print_exc()
            for op in replay:
                self.writer.add(op)
        self.feed.bump()

    # ---- what the page and Studio read
    def check(self):
        """The start panel's check lines, in plain words. Opens nothing."""
        import calls_notes as cn
        out = {}
        if os.environ.get("STUDIO_FAKE_MIC"):
            out["mic"] = {"ok": True, "text": "Test microphone (tests)"}
        else:
            import calls_mic
            name = calls_mic.device_name()
            out["mic"] = {"ok": bool(name), "text": f"Microphone: {name}" if name else calls_mic.NO_MIC}
        try:
            ph = cn.load_phrases()
            count = sum(len(ph[k]) for k in ("offering", "services", "constraint", "objection"))
            out["phrases"] = {"ok": True, "text": f"Phrase file: {count} phrases ({rel(cn.PHRASES)})"}
        except OSError as e:
            out["phrases"] = {"ok": False, "text": f"Can't read the phrase file ({e})."}
        try:
            s = self._prospects().open(add_key=False)
            out["airtable"] = {"ok": True, "text": "Prospects base: columns OK, Status changed found",
                               "logError": s.log_error}
        except Exception as e:  # noqa: BLE001
            out["airtable"] = {"ok": False, "text": str(e)[:300] if "column" in str(e) else
                               f"Can't read the Prospects base ({type(e).__name__})."}
        return out

    def brief(self):
        """For Studio's top bar."""
        return {"active": self.active(), "listening": self.listening(), "calls": len(self.st["cuts"])}

    def live_notes(self):
        segs = running_segs(self.st)
        key = (len(self.st["segs"]), len(self.st["cuts"]))
        if self._live[0] != key:
            import calls_notes as cn
            self._live = (key, cn.extract(segs, self.phrases or cn.load_phrases()) if segs else [])
        return self._live[1], segs

    def view(self):
        with self.lock:
            st = self.st
            cards = []
            for sid, s in [(st["id"], st)] + [(k, o["st"]) for k, o in self.others.items() if k != st["id"]]:
                if not sid:
                    continue
                for n, c in s["cards"].items():
                    if c["state"] != "open":
                        continue
                    cut = next((x for x in s["cuts"] if x["n"] == n), {}) or {}
                    cards.append({"sid": sid, "n": n, "rec": cut.get("rec"), "mb": cut.get("mb"), "name": cut.get("name"),
                                  "status": cut.get("status"), "at": cut.get("at"), "notes": c["notes"]})
            cards.sort(key=lambda c: c["at"] or 0)
            notes, segs = self.live_notes() if self.active() else ([], [])
            filed = []
            for n, f in sorted(st["filed"].items(), key=lambda kv: kv[0], reverse=True)[:8]:
                cut = next((x for x in st["cuts"] if x["n"] == n), {}) or {}
                filed.append({"n": n, "name": cut.get("name"), "mb": cut.get("mb"), "path": f["path"], "how": f["how"],
                              "notes": f["notes"]})
            writes = list(st["writes"].values()) + [w for o in self.others.values() for w in o["st"]["writes"].values()]
            stuck = [{"w": w["w"], "kind": w.get("kind"), "role": w.get("role"), "value": w.get("value"),
                      "err": w.get("err")} for w in writes if w["state"] == "stuck"]
            return {"active": self.active(), "listening": self.listening(), "id": st["id"], "started": st["started"],
                    "now": time.time(), "level": bool(self.level and self.listening()), "paused": st["paused"],
                    "device": (st["mic"] or {}).get("device"), "micError": self.mic_error, "pollError": self.poll_error,
                    "hotkey": None if not self.hotkey else bool(self.hotkey.ok),
                    "live": {"notes": notes, "since": st["cuts"][-1]["at"] if st["cuts"] else st["started"],
                             "heard": len(segs)},
                    "cards": cards, "filed": filed, "calls": len(st["cuts"]), "stopped": st["stopped"],
                    "writes": {"pending": self.writer.pending() if self.writer else 0, "stuck": stuck[-10:],
                               "failing": sum(1 for w in writes if w["state"] == "fail")},
                    "rev": self.feed.rev}


def unique_session_file(sid):
    p, n = sc.SESSIONS / f"{sid}.jsonl", 2
    while p.exists():
        p = sc.SESSIONS / f"{sid} ({n}).jsonl"
        n += 1
    return p
