"""Monarc Studio local server (2026-09-29): the short-form video editor behind the Desktop shortcut.

  python scripts/studio_server.py [--port 8780] [--no-open]

Serves the page (projects/studio/), media with HTTP Range (media/), and a JSON API. Background threads: a folder
scanner (new files in media/ get prepared), the prep queue, Find moments, and the export queue. Heavy work runs in
child processes (ffmpeg, studio_transcribe.py, studio_render.py) at below-normal priority, so the page stays quick.
Opened hidden by scripts/studio_boot.pyw; see references/studio.md.
"""
import argparse
import gzip
import hashlib
import json
import mimetypes
import os
import re
import shutil
import socketserver
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_calls as calls  # noqa: E402
import studio_common as sc  # noqa: E402
import studio_prep as prep  # noqa: E402
import studio_session  # noqa: E402

PORT = 8780
SCRIPTS = Path(__file__).resolve().parent
CTYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
          ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
          ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png",
          ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif",
          ".ico": "image/x-icon", ".woff2": "font/woff2", ".ttf": "font/ttf", ".txt": "text/plain; charset=utf-8",
          ".mp4": "video/mp4", ".m4v": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm",
          ".mkv": "video/x-matroska", ".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4",
          ".aac": "audio/aac", ".flac": "audio/flac", ".ogg": "audio/ogg", ".i8": "application/octet-stream",
          ".ass": "text/plain; charset=utf-8"}
VERSION_FILES = ("studio_server.py", "studio_common.py", "studio_prep.py", "studio_moments.py", "studio_speakers.py",
                 "studio_captions.py", "studio_calls.py", "studio_session.py", "studio_prospects.py", "calls_mic.py",
                 "calls_notes.py", "studio_gencaps.py", "studio_listen.py", "studio_transcribe.py")
VERSION = hashlib.md5(b"".join((SCRIPTS / f).read_bytes() for f in VERSION_FILES if (SCRIPTS / f).exists())
                      ).hexdigest()[:10]
VERSION_EVERY = 600       # seconds between saved versions of a short
VERSION_KEEP = 100


# ---------------------------------------------------------------- change feed

class Feed:
    """A revision number the page long-polls; anything that changes the bin bumps it."""

    def __init__(self):
        self.rev = 1
        self.cv = threading.Condition()
        self._last = 0
        self._pending = None

    def bump(self, throttle=0.0):
        """Throttled bumps (progress) are coalesced, never lost: one inside the window is sent when it closes."""
        now = time.time()
        if throttle and now - self._last < throttle:
            if self._pending is None:
                self._pending = threading.Timer(throttle - (now - self._last), self._fire)
                self._pending.daemon = True
                self._pending.start()
            return
        self._fire()

    def _fire(self):
        self._pending = None
        self._last = time.time()
        with self.cv:
            self.rev += 1
            self.cv.notify_all()

    def wait(self, since, timeout=25):
        with self.cv:
            if self.rev <= since:
                self.cv.wait(timeout)
            return self.rev


FEED = Feed()
SESSION_FEED = Feed()      # Monarc Calls' own feed: a click there doesn't wake the editor's bin poll


# ---------------------------------------------------------------- assets

def file_rev(*paths):
    """A stamp that changes when any of these files changes (modified times; "0" for a missing file)."""
    out = []
    for p in paths:
        try:
            out.append(str(int(Path(p).stat().st_mtime * 1000)))
        except OSError:
            out.append("0")
    return "-".join(out)


class Assets:
    """Every file under media/inbox, media/sfx and media/assets, with its asset id, meta and prep status."""
    DIRS = ("inbox", "sfx", "assets")

    def __init__(self):
        self.lock = threading.RLock()
        self.index = sc.read_json(sc.CACHE / "index.json", {}) or {}
        self.by_rel = {v["rel"]: k for k, v in self.index.items()}
        self.seen = {}          # rel -> (size, t_last_change)
        self.first = True

    def save(self):
        sc.write_json_atomic(sc.CACHE / "index.json", self.index)

    def meta(self, aid):
        return sc.read_json(sc.CACHE / aid / "meta.json") if aid in self.index else None

    def status(self, aid):
        return (sc.read_json(sc.CACHE / aid / "status.json", {}) or {}).get("stages", {})

    def scan(self):
        now = time.time()
        found = {}
        for d in self.DIRS:
            base = sc.MEDIA / d
            if not base.exists():
                continue
            for p in base.rglob("*"):
                if not p.is_file() or p.name.startswith(("~$", ".")) or p.suffix in (".part", ".tmp"):
                    continue
                if not sc.kind_of(p):
                    continue
                try:
                    stt = p.stat()
                except OSError:
                    continue
                found[sc.rel_media(p)] = (p, stt.st_size, stt.st_mtime)
        changed = False
        with self.lock:
            for rel, (p, size, mtime) in found.items():
                aid = self.by_rel.get(rel)
                if aid and self.index[aid]["size"] == size and abs(self.index[aid]["mtime"] - mtime) < 1:
                    continue
                prev = self.seen.get(rel)
                if prev is None or prev[0] != size:
                    old_enough = self.first and now - mtime > 60
                    self.seen[rel] = (size, now - (1e6 if old_enough else 0))
                    if not old_enough:
                        continue
                settle = 15 if size > 200e6 else 2
                if now - self.seen[rel][1] < settle:
                    continue
                self.register(p)
                changed = True
            for rel in list(self.by_rel):
                if rel not in found:
                    aid = self.by_rel.pop(rel)
                    self.index.pop(aid, None)
                    changed = True
            if changed:
                self.save()
        self.first = False
        if changed:
            FEED.bump()

    def register(self, path):
        aid = sc.asset_id(path)
        d = sc.CACHE / aid
        d.mkdir(parents=True, exist_ok=True)
        meta = prep.make_meta(aid, path)
        sc.write_json_atomic(d / "meta.json", meta)
        with self.lock:
            old_rel = self.index.get(aid, {}).get("rel")
            if old_rel and old_rel != meta["rel"]:
                self.by_rel.pop(old_rel, None)
            self.index[aid] = {"rel": meta["rel"], "size": meta["size"], "mtime": meta["mtime"], "kind": meta["kind"]}
            self.by_rel[meta["rel"]] = aid
        PREP.enqueue(aid)
        return aid

    def summary(self, aid):
        meta = self.meta(aid) or {}
        st = self.status(aid)
        d = sc.CACHE / aid
        out = {"id": aid, "rel": meta.get("rel"), "name": meta.get("name"), "kind": meta.get("kind"),
               "duration": meta.get("duration"), "stages": st, "urls": self.urls(aid, meta)}
        v = meta.get("video") or {}
        out["w"], out["h"] = v.get("w") or meta.get("w"), v.get("h") or meta.get("h")
        out["hasAudio"] = bool(meta.get("audio"))
        out["transcript"] = (d / "transcript.json").exists()
        if out["transcript"]:       # changes when the words change (a spelling fix, words filled in): the page refetches
            out["transcriptRev"] = file_rev(d / "transcript.json", d / "transcript-edits.json")
        out["speakers"] = (d / "speakers.json").exists()
        if out["speakers"]:
            import studio_speakers as ss
            out["voicesRev"] = ss.voices_rev(aid)     # the page fetches the voices again when this changes
        out["proxy"] = (d / "proxy.mp4").exists()
        out["moments"] = (d / "moments.json").exists()
        if out["moments"]:     # the recording's row and its calls view (2026-10-01)
            out["calls"] = calls.counts(aid)
            out["callsRev"] = calls.calls_rev(aid)
        elif meta.get("kind") == "video":
            out["auto"] = calls.auto_info(aid)       # why Claude's pass hasn't run by itself (over the $ line), if so
        if meta.get("kind") == "video":
            # when it was recorded: the title and the order in the Recordings list (2026-10-01)
            out["recorded"], out["recordedFrom"] = calls.recorded_at(meta)
            # the full-size copy (B20): "cache" (Studio's MP4 copy of an MKV), "source" (an MP4 that plays as it is),
            # "removed" (taken out to free space; the OBS file stands in)
            orig = meta.get("orig")
            out["copy"] = orig if orig in ("cache", "source", "removed") else "source"
            try:
                out["copyBytes"] = (d / "orig.mp4").stat().st_size if orig == "cache" else 0
            except OSError:
                out["copyBytes"] = 0
                if orig == "cache":
                    out["copy"] = "missing"     # being made again (or lost): the OBS file stands in meanwhile
        return out

    def urls(self, aid, meta):
        if not meta:
            return {}
        base = "/media/.studio/" + aid + "/"
        src = "/media/" + quote(meta["rel"])
        u = {"source": src}
        if meta.get("kind") == "video":
            # removed, or a copy not there (yet): no full-size address, so the page plays the preview copy
            if meta.get("orig") != "removed" and not (meta.get("orig") == "cache" and not (sc.CACHE / aid / "orig.mp4").exists()):
                u["orig"] = base + "orig.mp4" if meta.get("orig") == "cache" else src
            u["proxy"] = base + "proxy.mp4"
            th = sc.read_json(sc.CACHE / aid / "thumbs" / ".done")
            if th:
                th["count"] = len(list((sc.CACHE / aid / "thumbs").glob("t2-*.jpg")))
                th["base"] = base + "thumbs/t2-"
                u["thumbs"] = th
        if meta.get("kind") in ("video", "audio"):
            u["peaks100"] = base + "peaks-100.i8"
            u["peaks10"] = base + "peaks-10.i8"
        return u

    def tree(self):
        with self.lock:
            items = dict(self.index)
        folders = []
        for d, label in (("inbox", "Inbox"), ("sfx", "Sounds"), ("assets", "Assets")):
            rows = [self.summary(aid) for aid, v in items.items() if v["rel"].split("/", 1)[0] == d]
            rows.sort(key=lambda r: (r["rel"] or "").lower())
            folders.append({"dir": d, "name": label, "items": rows})
        ready = []
        if sc.READY.exists():
            for p in sorted(sc.READY.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
                ready.append({"name": p.name, "rel": sc.rel_media(p), "size": p.stat().st_size,
                              "mtime": p.stat().st_mtime, "url": "/media/" + quote(sc.rel_media(p))})
        folders.append({"dir": "ready", "name": "Ready", "items": ready})
        return folders


# ---------------------------------------------------------------- prep queue

class PrepQueue:
    def __init__(self):
        self.q = []
        self.cv = threading.Condition()
        self.current = None
        self.cancel = threading.Event()

    def enqueue(self, aid, front=False):
        with self.cv:
            if aid in self.q or aid == self.current:
                return
            self.q.insert(0, aid) if front else self.q.append(aid)
            self.cv.notify()

    def busy(self):
        return bool(self.current or self.q)

    def loop(self):
        while True:
            with self.cv:
                while not self.q:
                    self.cv.wait()
            # while Monarc Calls listens, its live words need the CPU (a 4-hour transcript beside them would make the
            # notes lag). Prep picks up again on Pause or Stop.
            if SESSION is not None:
                SESSION.idle.wait()
            with self.cv:
                if not self.q:
                    continue
                aid = self.q.pop(0)
                self.current = aid
            try:
                meta = ASSETS.meta(aid)
                if meta:
                    self.cancel.clear()
                    prep.run_asset(aid, meta, on_change=lambda: FEED.bump(0.4), cancel=self.cancel)
                    MOMENTS.maybe_auto(aid)      # a new recording: Claude's pass by itself, under the $ line (B16)
            except sc.Cancelled:
                pass
            except Exception:  # noqa: BLE001
                traceback.print_exc()
            finally:
                self.current = None
                FEED.bump()


# ---------------------------------------------------------------- moments

class MomentJobs:
    def __init__(self):
        self.state = {}
        self.voices = {}        # labels-only runs (studio_moments.label_voices), per asset
        self.auto_busy = set()  # assets whose auto-run token count is in flight
        self.auto_lock = threading.Lock()

    def busy(self, aid):
        return (self.state.get(aid, {}).get("state") == "running"
                or self.voices.get(aid, {}).get("state") == "running")

    def maybe_auto(self, aid):
        """Claude's pass by itself once a recording is prepared (Jonathan, B16, 2026-10-01): the free token count first,
        then the run only if the top of the estimate is under autoFindMax in config.json. Decided once per recording
        (auto-find.json, written only after a good count, so a network or key failure tries again next start)."""
        meta, stages = ASSETS.meta(aid), ASSETS.status(aid)
        cap = CONFIG.auto_cap()
        if calls.auto_check(aid, meta, stages, has_key(), cap) or self.busy(aid):
            return
        with self.auto_lock:
            if aid in self.auto_busy:
                return
            self.auto_busy.add(aid)

        def work():
            import studio_moments as sm
            try:
                est = sm.estimate(aid)
                decision = calls.auto_decide(est, cap)
                if decision == "run" and ((sc.CACHE / aid / "moments.json").exists() or self.busy(aid)):
                    return                       # someone pressed Find calls meanwhile
                calls.auto_record(aid, decision, est, cap)
                sm._log(aid, {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": "auto", "decision": decision,
                              "low": est["low"], "high": est["high"], "cap": cap, "input_tokens": est["input_tokens"]})
                if decision == "run":
                    self.run(aid)
                FEED.bump()
            except Exception:  # noqa: BLE001
                traceback.print_exc()
            finally:
                with self.auto_lock:
                    self.auto_busy.discard(aid)

        threading.Thread(target=work, daemon=True).start()

    def run_voices(self, aid):
        if self.voices.get(aid, {}).get("state") == "running":
            return
        self.voices[aid] = {"state": "running", "msg": "starting", "t": time.time()}
        FEED.bump()

        def work():
            import studio_moments as sm
            try:
                r = sm.label_voices(aid, on_status=lambda m: (self.voices[aid].update(msg=m), FEED.bump(1.0)))
                self.voices[aid] = {"state": "done", "msg": f"{len(r['voices']) + 1} voices labeled, ${r['cost']}",
                                    "cost": r["cost"], "t": time.time()}
            except Exception as e:  # noqa: BLE001
                traceback.print_exc()
                self.voices[aid] = {"state": "error", "error": f"{type(e).__name__}: {e}"[:600], "t": time.time()}
            FEED.bump()

        threading.Thread(target=work, daemon=True).start()

    def run(self, aid):
        if self.state.get(aid, {}).get("state") == "running":
            return
        self.state[aid] = {"state": "running", "msg": "starting", "t": time.time()}
        FEED.bump()

        def work():
            import studio_moments as sm
            try:
                r = sm.find(aid, on_status=lambda m: (self.state[aid].update(msg=m), FEED.bump(1.0)))
                n = sum(1 for c in r["calls"] if c.get("outcome") != "not_a_call")
                self.state[aid] = {"state": "done", "msg": f"{n} calls, {len(r['moments'])} best bits, ${r['cost']}",
                                   "cost": r["cost"], "t": time.time()}
                calls.ensure_bounds(aid, ASSETS.meta(aid), done=FEED.bump)    # each call's ring, on the laptop
            except Exception as e:  # noqa: BLE001
                traceback.print_exc()
                self.state[aid] = {"state": "error", "error": f"{type(e).__name__}: {e}"[:600], "t": time.time()}
            FEED.bump()

        threading.Thread(target=work, daemon=True).start()


# ---------------------------------------------------------------- projects (shorts)

class Projects:
    def __init__(self):
        self.lock = threading.RLock()

    def path(self, pid):
        if not pid or "/" in pid or "\\" in pid or pid.startswith("."):
            raise ValueError("bad project id")
        return sc.PROJECTS / f"{pid}.json"

    def list(self):
        out = []
        exports = EXPORTS.latest_by_project()
        for p in sorted(sc.PROJECTS.glob("*.json")):
            d = sc.read_json(p)
            if not d:
                continue
            ex = exports.get(d["id"])
            status = d.get("status", "draft")
            mtime = p.stat().st_mtime
            if ex and ex.get("state") == "done" and ex.get("done", 0) >= d.get("savedAt", 0) - 1:
                status = "exported"
            clips = [c for c in d.get("clips", []) if c.get("track") == "V1"]
            dur = max([c["start"] + c["out"] - c["in"] for c in d.get("clips", [])] or [0])
            out.append({"id": d["id"], "name": d.get("name"), "status": status, "own": d.get("status", "draft"),
                        "moment": d.get("moment"), "frames": dur, "clips": len(clips), "mtime": mtime,
                        "export": ex})
        out.sort(key=lambda r: r["mtime"], reverse=True)
        return out

    def get(self, pid):
        return sc.read_json(self.path(pid))

    def put(self, pid, doc, base_rev):
        with self.lock:
            p = self.path(pid)
            cur = sc.read_json(p)
            if cur and base_rev is not None and int(cur.get("rev", 0)) != int(base_rev):
                return 409, {"errors": ["This short changed in another window."], "rev": cur.get("rev")}
            doc["id"] = pid
            doc["rev"] = int(base_rev or 0) + 1 if cur else int(doc.get("rev", 1))
            doc["savedAt"] = time.time()
            sc.write_json_atomic(p, doc)
            self.maybe_version(pid, doc)
        FEED.bump(0.5)
        return 200, {"rev": doc["rev"], "savedAt": doc["savedAt"]}

    def maybe_version(self, pid, doc):
        vd = sc.PROJECTS / ".versions" / pid
        vd.mkdir(parents=True, exist_ok=True)
        vers = sorted(vd.glob("*.json"))
        if vers and time.time() - vers[-1].stat().st_mtime < VERSION_EVERY:
            return
        sc.write_json_atomic(vd / (time.strftime("%Y%m%d-%H%M%S") + ".json"), doc)
        for old in vers[:max(0, len(vers) + 1 - VERSION_KEEP)]:
            old.unlink(missing_ok=True)

    def versions(self, pid):
        vd = sc.PROJECTS / ".versions" / pid
        rows = []
        for p in sorted(vd.glob("*.json"), reverse=True):
            d = sc.read_json(p) or {}
            rows.append({"ts": p.stem, "rev": d.get("rev"), "mtime": p.stat().st_mtime,
                         "clips": len(d.get("clips", []))})
        return rows

    def version(self, pid, ts):
        if not ts.replace("-", "").isdigit():
            raise ValueError("bad version")
        return sc.read_json(sc.PROJECTS / ".versions" / pid / f"{ts}.json")

    def delete(self, pid):
        p = self.path(pid)
        tr = sc.PROJECTS / ".trash"
        tr.mkdir(exist_ok=True)
        if p.exists():
            shutil.move(str(p), str(tr / f"{pid}-{time.strftime('%Y%m%d-%H%M%S')}.json"))
        FEED.bump()

    def unique_id(self, base):
        pid, n = base, 2
        while self.path(pid).exists():
            pid = f"{base}-{n}"
            n += 1
        return pid

    @staticmethod
    def _clips(aid, meta, fin, fout):
        clips = [{"id": "c1", "track": "V1", "type": "video", "asset": aid, "in": fin, "out": fout,
                  "start": 0, "link": "L1", "on": True, "fx": {}}]
        if meta.get("audio"):
            # the voices on their own tracks (Jonathan 2026-09-30, V1-V2): the same audio twice, A1 plays only his
            # stretches, A2 only the other side's, so each can be leveled on its own
            clips.append({"id": "c2", "track": "A1", "type": "audio", "asset": aid, "in": fin, "out": fout,
                          "start": 0, "link": "L1", "on": True, "fadeIn": 0, "fadeOut": 0, "fx": {}, "voice": "me"})
            clips.append({"id": "c3", "track": "A2", "type": "audio", "asset": aid, "in": fin, "out": fout,
                          "start": 0, "link": "L1", "on": True, "fadeIn": 0, "fadeOut": 0, "fx": {}, "voice": "them"})
        return clips

    @staticmethod
    def _keep(aid, mo, mid):
        """A short made from a best bit marks it kept (the old moments list showed it; the calls view's Short tag
        comes from the shorts list instead)."""
        for x in mo.get("moments", []):
            if x["id"] == mid:
                x["state"] = "kept"
        sc.write_json_atomic(sc.CACHE / aid / "moments.json", mo)

    def create(self, body):
        """A new short from a moment, from a stretch of a recording (the calls view's Make short: start and end in
        seconds, plus the call and, when the marks are exactly a best bit, that bit), or empty. The default tracks:
        Captions, V2, V1, A1 You, A2 Them, A3 Sounds (G13)."""
        aid, mid = body.get("asset"), body.get("moment")
        name = body.get("name") or "Untitled short"
        clips, moment = [], None
        if aid and mid:
            mo = sc.read_json(sc.CACHE / aid / "moments.json", {}) or {}
            m = next((x for x in mo.get("moments", []) if x["id"] == mid), None)
            if not m:
                return 404, {"errors": ["No such moment."]}
            name = body.get("name") or m["title"]
            fin, fout = int(round(m["start"] * sc.FPS)), int(round(m["end"] * sc.FPS))
            clips = self._clips(aid, ASSETS.meta(aid) or {}, fin, fout)
            moment = {"asset": aid, "mid": mid, "type": m["type"], "title": m["title"], "reason": m["reason"],
                      "start": m["start"], "end": m["end"]}
            self._keep(aid, mo, mid)
        elif aid:
            meta = ASSETS.meta(aid)
            if not meta:
                return 404, {"errors": ["No such asset."]}
            try:
                s, e = float(body["start"]), float(body["end"])
            except (KeyError, TypeError, ValueError):
                return 400, {"errors": ["Give a moment, or a start and an end in seconds."]}
            dur = float(meta.get("duration") or 0)
            if not (0 <= s < e and (not dur or e <= dur + 0.5)):
                return 400, {"errors": ["That stretch isn't inside the recording."]}
            e = min(e, dur) if dur else e
            mo = sc.read_json(sc.CACHE / aid / "moments.json", {}) or {}
            cid, bid = body.get("call"), body.get("bit")
            c = calls.row(aid, cid) if cid else None
            b = next((x for x in mo.get("moments", []) if x["id"] == bid), None) if bid else None
            name = body.get("name") or (b and b["title"]) or (c and c["label"]) or "Untitled short"
            clips = self._clips(aid, meta, int(round(s * sc.FPS)), int(round(e * sc.FPS)))
            moment = {"asset": aid, "call": cid, "mid": b["id"] if b else None,
                      "type": b["type"] if b else "call", "title": name,
                      "reason": (b and b.get("reason")) or (c and c.get("summary")) or "", "start": s, "end": e}
            if b:
                self._keep(aid, mo, b["id"])
        pid = self.unique_id(time.strftime("%m%d-") + sc.slugify(name))
        doc = {"v": 1, "id": pid, "name": name, "status": "draft", "fps": sc.FPS, "w": 1080, "h": 1920, "rev": 1,
               "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "moment": moment,
               "tracks": [{"id": "C", "kind": "caption"}, {"id": "V2", "kind": "video"},
                          {"id": "V1", "kind": "video"}, {"id": "A1", "kind": "audio", "voice": "me", "name": "You"},
                          {"id": "A2", "kind": "audio", "voice": "them", "name": "Them"},
                          {"id": "A3", "kind": "audio", "name": "Sounds"}],
               "clips": clips, "transitions": [], "markers": [],
               "captions": {"on": True, "size": 110, "y": 1340, "bord": 7, "upper": True, "evRev": 0, "events": []}}
        # no captions until he presses Generate captions, once the short is trimmed (G1, 2026-10-02); "transcript"
        # keeps the old way (captions straight from the first transcript), which the tests of that path ask for
        if body.get("captions") != "transcript":
            doc["captions"]["mode"] = "generate"
        doc["savedAt"] = time.time()
        sc.write_json_atomic(self.path(pid), doc)
        self.maybe_version(pid, doc)
        FEED.bump()
        return 200, doc


# ---------------------------------------------------------------- export queue

class Exports:
    FILE = None

    def __init__(self):
        self.FILE = sc.CACHE / "exports.json"
        self.jobs = sc.read_json(self.FILE, []) or []
        for j in self.jobs:
            if j["state"] == "running":
                j["state"] = "queued"
        self.cv = threading.Condition()
        self.proc = None
        self.cancel_id = None

    def save(self):
        sc.write_json_atomic(self.FILE, self.jobs[-200:])

    def latest_by_project(self):
        out = {}
        for j in self.jobs:
            out[j["project"]] = j
        return out

    def busy(self):
        return any(j["state"] in ("queued", "running") for j in self.jobs)

    def add(self, pid, front=False):
        doc = PROJECTS.get(pid)
        if not doc:
            return 404, {"errors": ["No such short."]}
        jid = f"x{int(time.time() * 1000)}"
        jd = sc.CACHE / "renders" / pid / jid
        jd.mkdir(parents=True, exist_ok=True)
        import studio_captions as caps
        doc.setdefault("captions", {})["palette"] = caps.load_palette()   # a job rerun by hand keeps its colors
        sc.write_json_atomic(jd / "project.json", doc)
        job = {"id": jid, "project": pid, "name": doc.get("name"), "state": "queued", "progress": 0,
               "stage": "queued", "dir": str(jd), "created": time.time(), "rev": doc.get("rev")}
        with self.cv:
            for j in self.jobs:   # one pending job per short: a newer request replaces the older
                if j["project"] == pid and j["state"] == "queued":
                    j["state"] = "replaced"
            if front:
                idx = next((i for i, j in enumerate(self.jobs) if j["state"] == "queued"), len(self.jobs))
                self.jobs.insert(idx, job)
            else:
                self.jobs.append(job)
            self.save()
            self.cv.notify()
        FEED.bump()
        return 200, job

    def add_done(self):
        """Export all: every short marked done and not exported since. None is skipped for want of captions (G5);
        the answer names the ones going out without them, or with some footage uncaptioned."""
        import studio_gencaps as gc
        out, bare, part = [], [], []
        for p in PROJECTS.list():
            if p["own"] == "done" and p["status"] != "exported":
                miss = gc.missing(PROJECTS.get(p["id"]) or {})
                (bare if miss == "none" else part if miss == "part" else []).append(p.get("name") or p["id"])
                out.append(self.add(p["id"])[1])
        return 200, {"queued": len(out), "noCaptions": bare, "partCaptions": part}

    def cancel(self, jid):
        with self.cv:
            for j in self.jobs:
                if j["id"] == jid and j["state"] == "queued":
                    j["state"] = "cancelled"
                elif j["id"] == jid and j["state"] == "running":
                    self.cancel_id = jid
                    if self.proc:
                        sc.kill_tree(self.proc.pid)     # the render and its ffmpeg children
            self.save()
        FEED.bump()
        return 200, {"ok": True}

    def loop(self):
        while True:
            with self.cv:
                job = None
                while job is None:
                    job = next((j for j in self.jobs if j["state"] == "queued"), None)
                    if job is None:
                        self.cv.wait()
                job["state"] = "running"
                job["started"] = time.time()
                self.save()
            FEED.bump()
            self.run(job)

    def run(self, job):
        doc = sc.read_json(Path(job["dir"]) / "project.json") or {}
        out = sc.READY / f"{sc.slugify(doc.get('name') or job['project'], job['project'])}.mp4"
        args = [sc.python_exe(), "-u", str(SCRIPTS / "studio_render.py"), str(Path(job["dir"]) / "project.json"),
                "--out", str(out), "--job", job["dir"]]
        try:
            self.proc = sc.popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            err = []
            threading.Thread(target=lambda: [err.append(l.decode("utf-8", "replace")) for l in self.proc.stderr],
                             daemon=True).start()
            for raw in self.proc.stdout:
                try:
                    msg = json.loads(raw)
                except ValueError:
                    continue
                if "progress" in msg:
                    job["progress"] = msg["progress"]
                if "stage" in msg:
                    job["stage"] = msg["stage"]
                if msg.get("warn"):
                    job.setdefault("warn", []).append(msg["warn"])
                if msg.get("out"):
                    job["out"] = msg["out"]
                FEED.bump(0.5)
            self.proc.wait()
            sc.untrack(self.proc)
            if self.cancel_id == job["id"]:
                job["state"] = "cancelled"
            elif self.proc.returncode == 0 and job.get("out"):
                job["state"] = "done"
                job["done"] = time.time()
                job["progress"] = 1
                job["url"] = "/media/" + quote(sc.rel_media(job["out"]))
            else:
                job["state"] = "error"
                job["error"] = "".join(err)[-1500:] or f"render exit {self.proc.returncode}"
        except Exception as e:  # noqa: BLE001
            job["state"] = "error"
            job["error"] = f"{type(e).__name__}: {e}"
        finally:
            self.proc = None
            self.cancel_id = None
            self.save()
            FEED.bump()


# ---------------------------------------------------------------- settings

class Config:
    """projects/studio/config.json (STUDIO_CONFIG for tests): the caption palette every short uses (2026-09-30)."""

    def __init__(self):
        self.lock = threading.Lock()

    def get(self):
        import studio_captions as caps
        return {"captionColors": caps.load_palette(), "autoFindMax": self.auto_cap()}

    def auto_cap(self):
        """autoFindMax: the most Claude's pass may cost by estimate to run by itself (B16); None turns it off."""
        v = (sc.read_json(sc.CONFIG, {}) or {}).get("autoFindMax")
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    def put(self, body):
        import studio_captions as caps
        if body.get("reset"):
            cur = dict(caps.DEFAULT_PALETTE)
        else:
            cc = body.get("captionColors")
            if not isinstance(cc, dict):
                raise ValueError("Missing captionColors.")
            cur = caps.load_palette()
            for k, v in cc.items():
                if k not in caps.DEFAULT_PALETTE:
                    raise ValueError(f"Unknown color {k}.")
                if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(v)):
                    raise ValueError(f"{k}: colors are written #RRGGBB.")
                cur[k] = str(v).upper()
        with self.lock:
            data = sc.read_json(sc.CONFIG, {}) or {}
            data["captionColors"] = cur
            sc.write_json_atomic(sc.CONFIG, data, indent=1)
        FEED.bump()
        return {"captionColors": cur}


# ---------------------------------------------------------------- Generate captions

class CaptionJobs:
    """Generate captions (2026-10-02, studio_gencaps.py): one job per press, per recording under the short. The page
    polls the job and puts the words into the short itself, as one undo step; the server never writes the short."""

    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()

    def busy(self):
        return any(j["state"] == "running" for j in list(self.jobs.values()))

    def get(self, jid):
        return self.jobs.get(jid)

    def start(self, aid, kept):
        jid = f"g{int(time.time() * 1000)}{len(self.jobs)}"
        job = {"id": jid, "asset": aid, "state": "running", "msg": "Starting", "progress": 0, "t": time.time()}
        with self.lock:
            for k in [k for k, j in self.jobs.items() if j["state"] != "running" and time.time() - j["t"] > 900]:
                del self.jobs[k]
            self.jobs[jid] = job

        def status(msg, progress=None):
            job["msg"] = msg
            if progress is not None:
                job["progress"] = round(progress, 3)

        def work():
            import studio_gencaps as gc
            try:
                r = gc.generate(aid, kept, on_status=status)
                job.update(state="done", result=r, progress=1, t=time.time(),
                           msg=f"{len(r['words'])} words" + (f", ${r['cost']}" if r.get("cost") else ""))
            except Exception as e:  # noqa: BLE001
                traceback.print_exc()
                job.update(state="error", error=f"{type(e).__name__}: {e}"[:600], t=time.time())

        threading.Thread(target=work, daemon=True).start()
        return job


ASSETS = PREP = MOMENTS = PROJECTS = EXPORTS = SESSION = None
CONFIG = Config()
CAPTIONS = CaptionJobs()


def remove_or_restore_copy(aid, keep):
    """Free the space of a recording's full-size MP4 copy, or make it again (Jonathan, B20, 2026-10-01). Meanwhile
    exports, the editor's sound blocks, loudness and the ring finder read the OBS file (studio_prep.orig_path treats
    anything but "cache" that way), and the page plays the preview copy, even at Full (urls() leaves out orig)."""
    meta = ASSETS.meta(aid)
    if not meta or meta.get("kind") != "video":
        return 404, {"errors": ["No such recording."]}
    orig = meta.get("orig")
    if orig not in ("cache", "removed"):
        return 400, {"errors": ["This file plays as it is; there's no full-size copy."]}
    with PREP.cv:
        preparing = aid == PREP.current or aid in PREP.q
    if preparing:
        return 409, {"errors": ["It's still being prepared. Try again when that's done."]}
    d = sc.CACHE / aid
    if not keep:
        if orig == "removed":
            return 200, {"ok": True, "copy": "removed", "freed": 0}
        f = d / "orig.mp4"
        size = f.stat().st_size if f.exists() else 0
        meta["orig"] = "removed"
        sc.write_json_atomic(d / "meta.json", meta)
        try:
            f.unlink(missing_ok=True)
            (d / "orig.mp4.part").unlink(missing_ok=True)
        except PermissionError:       # Windows: a player or an export still has it open
            meta["orig"] = "cache"
            sc.write_json_atomic(d / "meta.json", meta)
            return 409, {"errors": ["The full-size copy is in use (a player or an export). Pause, wait a moment and "
                                    "try again."]}
        FEED.bump()
        return 200, {"ok": True, "copy": "removed", "freed": size}
    if orig == "cache":
        return 200, {"ok": True, "copy": "cache"}
    need = float(meta.get("size") or 0) * 1.05 + 1e9
    free = shutil.disk_usage(sc.MEDIA).free
    if free < need:
        return 409, {"errors": [f"Not enough free space: the copy needs about {need / 1e9:.1f} GB and "
                                f"{free / 1e9:.1f} GB is free."]}
    meta["orig"] = "cache"
    sc.write_json_atomic(d / "meta.json", meta)
    PREP.enqueue(aid, front=True)
    FEED.bump()
    return 200, {"ok": True, "copy": "cache"}


def startup_calls():
    """At start: each prepared recording's call bounds (rings), then Claude's pass by itself where it's due (B16),
    so a recording dropped in while the server was older gets its pass too. One recording at a time."""
    for aid in list(ASSETS.index):
        meta = ASSETS.meta(aid) or {}
        if meta.get("kind") != "video" or not str(meta.get("rel") or "").startswith("inbox/"):
            continue
        with PREP.cv:
            if aid == PREP.current or aid in PREP.q:
                continue
        try:
            calls.ensure_bounds(aid, meta, done=FEED.bump, wait=True)
            MOMENTS.maybe_auto(aid)
        except Exception:  # noqa: BLE001
            traceback.print_exc()


def key_source():
    """Where ANTHROPIC_API_KEY comes from (a file name or "environment"), never the key itself; None without one."""
    try:
        from outreach_common import load_env
        _, src = load_env()
        return src.get("ANTHROPIC_API_KEY")
    except Exception:  # noqa: BLE001
        return None


def has_key():
    return bool(key_source())


def health():
    key = key_source()
    return {"app": "Monarc Studio", "version": VERSION, "media": str(sc.MEDIA), "ffmpeg": sc.ffmpeg_exe(),
            "model": (sc.PARAKEET_DIR / "encoder.int8.onnx").exists(), "key": key,
            "disk_free_gb": round(shutil.disk_usage(sc.MEDIA).free / 1e9, 1),
            # a session recording counts as busy, so the boot script never restarts the server in the middle of one
            "busy": bool(PREP.busy() or EXPORTS.busy() or CAPTIONS.busy() or (SESSION is not None and SESSION.active())
                         or any(v.get("state") == "running"
                                for v in list(MOMENTS.state.values()) + list(MOMENTS.voices.values()))),
            "rev": FEED.rev}


_PAGE_REV = {"t": 0.0, "v": ""}


def page_rev():
    """A stamp of the page's own files (js, css, html), so an open window learns the page changed (re-read every 2 s)."""
    now = time.time()
    if now - _PAGE_REV["t"] > 2:
        files = [p for p in sc.STUDIO_DIR.rglob("*") if p.suffix in (".js", ".css", ".html") and "tests" not in p.parts]
        _PAGE_REV["v"] = str(int(max((p.stat().st_mtime for p in files), default=0)))
        _PAGE_REV["t"] = now
    return _PAGE_REV["v"]


def bin_state():
    h = health()
    return {"rev": FEED.rev, "folders": ASSETS.tree(), "shorts": PROJECTS.list(), "moments": MOMENTS.state,
            "voiceJobs": MOMENTS.voices, "version": VERSION + "-" + page_rev(),
            "exports": [j for j in EXPORTS.jobs[-30:] if j["state"] != "replaced"], "busy": h["busy"],
            "config": CONFIG.get(), "diskFreeGb": h["disk_free_gb"],
            "session": SESSION.brief() if SESSION is not None else None}


# ---------------------------------------------------------------- http

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        status = str(args[1]) if len(args) > 1 else ""
        if not status.isdigit() or int(status) < 400:     # log only failures
            return
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def handle(self):
        try:
            super().handle()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def _send(self, status, data, ctype, extra=None):
        try:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            self.close_connection = True       # the page went away (a long poll outliving its tab)

    def _json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        if len(data) > 4096 and "gzip" in (self.headers.get("Accept-Encoding") or ""):
            return self._send(status, gzip.compress(data, 5), "application/json; charset=utf-8",
                              {"Content-Encoding": "gzip"})
        self._send(status, data, "application/json; charset=utf-8")

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except ValueError:
            return {}

    def _file(self, file, cache=False):
        """Serve a file with HTTP Range (206/416), streamed in 1 MiB chunks."""
        size = file.stat().st_size
        ctype = CTYPES.get(file.suffix.lower()) or mimetypes.guess_type(str(file))[0] or "application/octet-stream"
        etag = f'"{int(file.stat().st_mtime)}-{size}"'
        rng = self.headers.get("Range")
        start, end = 0, size - 1
        status = 200
        if rng and rng.startswith("bytes="):
            spec = rng[6:].split(",")[0].strip()
            try:
                a, b = spec.split("-", 1)
                if a == "":
                    start, end = max(0, size - int(b)), size - 1
                else:
                    start = int(a)
                    end = int(b) if b else size - 1
                end = min(end, size - 1)
                if start > end or start >= size:
                    raise ValueError
                status = 206
            except ValueError:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
        length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        self.send_header("ETag", etag)
        self.send_header("Cache-Control", "max-age=3600" if cache else "no-cache")
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if self.command == "HEAD":
            return
        try:
            with open(file, "rb") as f:
                f.seek(start)
                left = length
                while left > 0:
                    chunk = f.read(min(1 << 20, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def _static(self, path):
        rel = "index.html" if path in ("", "/") else unquote(path.lstrip("/"))
        file = (sc.STUDIO_DIR / rel).resolve()
        if not file.is_relative_to(sc.STUDIO_DIR.resolve()) or not file.is_file():
            return self._send(404, b"not found", "text/plain")
        return self._file(file)

    def _media(self, path):
        rel = unquote(path[len("/media/"):])
        try:
            file = sc.media_path(rel)
        except ValueError:
            return self._send(403, b"forbidden", "text/plain")
        if not file.is_file():
            return self._send(404, b"not found", "text/plain")
        return self._file(file, cache="/.studio/" in path)

    # ---- GET / HEAD
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path.startswith("/media/"):
            return self._media(u.path)
        if not u.path.startswith("/api/"):
            return self._static(u.path)
        p = u.path[len("/api/"):]
        try:
            if p == "health":
                return self._json(200, health())
            if p == "session" or p.startswith("session/"):
                return self._session_get(p, q)
            if p == "config":
                return self._json(200, CONFIG.get())
            if p == "bin":
                since = int(q.get("since", 0))
                if since:
                    FEED.wait(since, timeout=min(25, float(q.get("wait", 25))))
                return self._json(200, bin_state())
            if p.startswith("asset/"):
                parts = p.split("/")
                aid = parts[1]
                if not ASSETS.meta(aid):
                    return self._json(404, {"errors": ["No such asset."]})
                if len(parts) == 2:
                    s = ASSETS.summary(aid)
                    s["meta"] = ASSETS.meta(aid)
                    return self._json(200, s)
                if parts[2] == "transcript":
                    import studio_moments as sm
                    import studio_speakers as ss
                    try:
                        tr = sm.load_transcript(aid)
                    except RuntimeError:
                        return self._json(404, {"errors": ["No transcript yet."]})
                    tr["edits"] = sc.read_json(sc.CACHE / aid / "transcript-edits.json", {}) or {}
                    tr["trev"] = file_rev(sc.CACHE / aid / "transcript.json", sc.CACHE / aid / "transcript-edits.json")
                    try:
                        tr["voices"] = ss.resolve(aid, tr["words"])
                    except Exception as e:  # noqa: BLE001  (the words must still arrive, or the captions go empty)
                        traceback.print_exc()
                        tr["voices"] = {"state": "error", "error": f"{type(e).__name__}: {e}"[:300],
                                        "vrev": ss.voices_rev(aid), "spk": None, "speakers": []}
                    return self._json(200, tr)
                if parts[2] == "moments":
                    mo = sc.read_json(sc.CACHE / aid / "moments.json")
                    return self._json(200 if mo else 404, mo or {"errors": ["No moments yet."]})
                if parts[2] == "voices":
                    import studio_speakers as ss
                    return self._json(200, ss.resolve(aid))
                if parts[2] == "ring":            # Make trailer: the last ring before source second t
                    return self._json(200, {"ring": prep.find_ring(aid, ASSETS.meta(aid), float(q.get("t", 0)))})
                if parts[2:] == ["calls"]:        # the calls view (2026-10-01): rows, best bits, watched marks
                    finding = calls.ensure_bounds(aid, ASSETS.meta(aid), done=FEED.bump)
                    v = calls.view(aid)
                    v["bounding"] = bool(v["bounding"] and (finding or calls.bounding(aid)))
                    return self._json(200, v)
                if parts[2:] == ["calls", "search"]:
                    try:
                        return self._json(200, {"hits": calls.search(aid, q.get("q", "")[:200])})
                    except RuntimeError:
                        return self._json(404, {"errors": ["No transcript yet."]})
                if parts[2] == "words":           # one call's words and voices, for the captions on its player
                    try:
                        return self._json(200, calls.words(aid, q.get("s", 0), q.get("e", 0)))
                    except ValueError as e:
                        return self._json(400, {"errors": [str(e)]})
                    except RuntimeError:
                        return self._json(404, {"errors": ["No transcript yet."]})
            if p == "audio_block":
                aid = q.get("asset", "")
                meta = ASSETS.meta(aid)
                if not meta:
                    return self._json(404, {"errors": ["No such asset."]})
                f = prep.audio_block(aid, meta, int(q.get("i", 0)), int(q.get("sr", 48000)))
                return self._file(f, cache=True)
            if p == "projects":
                return self._json(200, PROJECTS.list())
            if p.startswith("projects/"):
                parts = p.split("/")
                pid = parts[1]
                if len(parts) == 2:
                    d = PROJECTS.get(pid)
                    return self._json(200 if d else 404, d or {"errors": ["No such short."]})
                if parts[2] == "versions" and len(parts) == 3:
                    return self._json(200, PROJECTS.versions(pid))
                if parts[2] == "versions" and len(parts) == 4:
                    d = PROJECTS.version(pid, parts[3])
                    return self._json(200 if d else 404, d or {"errors": ["No such version."]})
                if parts[2] == "still":
                    return self._still(pid, int(q.get("f", 0)), q.get("scale", "1"))
            if p == "exports":
                return self._json(200, EXPORTS.jobs[-50:])
            if p.startswith("captions/"):           # a Generate captions job (2026-10-02)
                job = CAPTIONS.get(p.split("/")[1])
                return self._json(200 if job else 404, job or {"errors": ["No such caption job (the server restarted?)."]})
            return self._json(404, {"errors": ["Unknown endpoint."]})
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            return self._json(500, {"errors": [f"{type(e).__name__}: {e}"]})

    def _session_get(self, p, q):
        """Monarc Calls (reworked 2026-10-03): the session (long-poll with since=), the start panel's checks, and in
        tests what the stand-in base holds."""
        if p == "session":
            since = int(q.get("since", 0) or 0)
            if since:
                SESSION_FEED.wait(since, timeout=min(25, float(q.get("wait", 25))))
            return self._json(200, SESSION.view())
        if p == "session/check":
            return self._json(200, SESSION.check())
        if p == "session/fake" and os.environ.get("STUDIO_FAKE_AIRTABLE"):
            be = SESSION._prospects().be
            return self._json(200, be.dump() if hasattr(be, "dump") else {})
        return self._json(404, {"errors": ["Unknown endpoint."]})

    def _session_fake(self, body):
        """Tests only: {say: text} is a line the test microphone hears; {status: {rec, words}} is Jonathan typing
        Status in Airtable."""
        if not (os.environ.get("STUDIO_FAKE_AIRTABLE") and os.environ.get("STUDIO_FAKE_MIC")):
            return self._json(404, {"errors": ["Unknown endpoint."]})
        if body.get("say"):
            SESSION._mic_send("say " + str(body["say"]).replace("\n", " "))
        st = body.get("status")
        if isinstance(st, dict):
            at = SESSION._prospects().be.fake_status(st.get("rec"), str(st.get("words") or ""), st.get("at"))
            return self._json(200, {"ok": True, "at": at})
        return self._json(200, {"ok": True})

    def _still(self, pid, f, scale):
        src = PROJECTS.path(pid)
        if not src.exists():
            return self._json(404, {"errors": ["No such short."]})
        out = sc.CACHE / "renders" / pid / f"still-{f}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([sc.python_exe(), str(SCRIPTS / "studio_render.py"), str(src), "--still", str(f),
                            "--png", str(out), "--scale", scale], capture_output=True, text=True,
                           creationflags=sc.NO_WINDOW)
        if r.returncode or not out.exists():
            return self._json(500, {"errors": [r.stderr[-800:] or "still failed"]})
        return self._send(200, out.read_bytes(), "image/png")

    # ---- PUT
    def do_PUT(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        p = u.path[len("/api/"):] if u.path.startswith("/api/") else ""
        try:
            if p == "upload":
                return self._upload(q)
            if p == "config":
                try:
                    return self._json(200, CONFIG.put(self._body()))
                except ValueError as e:
                    return self._json(400, {"errors": [str(e)]})
            if p.startswith("projects/"):
                pid = p.split("/")[1]
                body = self._body()
                doc = body.get("doc")
                if not isinstance(doc, dict):
                    return self._json(400, {"errors": ["Missing doc."]})
                return self._json(*PROJECTS.put(pid, doc, body.get("baseRev")))
            return self._json(404, {"errors": ["Unknown endpoint."]})
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            return self._json(500, {"errors": [f"{type(e).__name__}: {e}"]})

    def _upload(self, q):
        folder = q.get("dir", "")
        name = Path(unquote(q.get("name", ""))).name
        kind = sc.kind_of(name)
        if not name or not kind:
            return self._json(400, {"errors": ["Unsupported file type."]})
        if folder not in ("inbox", "sfx", "assets"):
            folder = {"video": "inbox", "audio": "sfx", "image": "assets"}[kind]
        dest_dir = sc.MEDIA / folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / name
        stem, n = dest.stem, 2
        while dest.exists():
            dest = dest_dir / f"{stem} ({n}){dest.suffix}"
            n += 1
        n_bytes = int(self.headers.get("Content-Length") or 0)
        part = dest.with_name(dest.name + ".part")
        left = n_bytes
        with open(part, "wb") as f:
            while left > 0:
                chunk = self.rfile.read(min(1 << 20, left))
                if not chunk:
                    break
                f.write(chunk)
                left -= len(chunk)
        if left:
            part.unlink(missing_ok=True)
            return self._json(400, {"errors": ["Upload cut short."]})
        part.replace(dest)
        aid = ASSETS.register(dest)
        ASSETS.save()
        FEED.bump()
        return self._json(200, {"rel": sc.rel_media(dest), "asset": aid})

    # ---- POST / PATCH / DELETE
    def do_POST(self):
        u = urlparse(self.path)
        p = u.path[len("/api/"):] if u.path.startswith("/api/") else ""
        body = self._body()
        try:
            if p == "session/fake":               # tests: a line heard, a Status typed
                return self._session_fake(body)
            if p.startswith("session/"):          # Monarc Calls: start, pause, resume, push, discard, stop, retry, window
                return self._json(*SESSION.post(p.split("/", 1)[1], body))
            if p == "import":
                src = Path(body.get("path", ""))
                if not src.is_file() or not sc.kind_of(src):
                    return self._json(400, {"errors": ["No such file, or unsupported type."]})
                folder = body.get("dir") or {"video": "inbox", "audio": "sfx", "image": "assets"}[sc.kind_of(src)]
                dest = sc.MEDIA / folder / src.name
                shutil.copy2(src, dest)
                return self._json(200, {"rel": sc.rel_media(dest), "asset": ASSETS.register(dest)})
            if p.startswith("asset/"):
                parts = p.split("/")
                aid = parts[1]
                if not ASSETS.meta(aid):
                    return self._json(404, {"errors": ["No such asset."]})
                if parts[2:] == ["orig"]:           # remove or restore the full-size copy (B20)
                    return self._json(*remove_or_restore_copy(aid, bool(body.get("keep"))))
                if parts[2:] == ["reprep"]:
                    # the old outputs stay until each stage runs again (prep can wait on a Monarc Calls session or
                    # a restart; deleting them at the click once left a recording without sound, 2026-10-02)
                    redo = prep.request_redo(aid, body.get("stages") or [])
                    PREP.enqueue(aid, front=True)
                    return self._json(200, {"ok": True, "redo": redo})
                if parts[2:] in (["moments", "estimate"], ["moments"]):
                    sp = ASSETS.status(aid).get("speakers")
                    if sp and sp.get("state") in ("queued", "running"):
                        return self._json(409, {"errors": [
                            f"The voices are still being split ({int((sp.get('progress') or 0) * 100)} %). Find calls "
                            "waits so Claude can label them in the same pass."]})
                if parts[2:] == ["moments", "estimate"]:
                    import studio_moments as sm
                    return self._json(200, sm.estimate(aid))
                if parts[2:] == ["moments"]:
                    MOMENTS.run(aid)
                    return self._json(200, {"ok": True})
                if parts[2:] == ["headlines"]:     # Make trailer: three headline drafts from Claude (under a cent)
                    if os.environ.get("STUDIO_NO_CLAUDE"):
                        return self._json(503, {"errors": ["Claude is off for this run."]})
                    import studio_moments as sm
                    try:
                        return self._json(200, sm.headlines(aid, float(body.get("from", 0)), float(body.get("to", 0)),
                                                            str(body.get("title") or "")[:200]))
                    except RuntimeError as e:
                        return self._json(502, {"errors": [str(e)]})
                if parts[2:] == ["captions"]:      # Generate captions: {ranges: [[s, e]]} the short keeps (G2)
                    if not (sc.CACHE / aid / "transcript.json").exists():
                        return self._json(409, {"errors": ["This recording has no transcript yet."]})
                    try:
                        kept = [[float(r[0]), float(r[1])] for r in body.get("ranges") or []][:500]
                    except (TypeError, ValueError, IndexError):
                        return self._json(400, {"errors": ["ranges are [[start, end], ...] in seconds."]})
                    dur = float(ASSETS.meta(aid).get("duration") or 0)
                    kept = [r for r in kept if 0 <= r[0] < r[1] and (not dur or r[0] < dur)]
                    if not kept:
                        return self._json(400, {"errors": ["Nothing of this recording is on the speech tracks."]})
                    return self._json(200, CAPTIONS.start(aid, kept))
                if parts[2:] in (["voices", "estimate"], ["voices"]):
                    if not (sc.CACHE / aid / "speakers.json").exists():
                        return self._json(409, {"errors": ["This recording's voices haven't been split yet."]})
                    if parts[3:] == ["estimate"]:
                        import studio_moments as sm
                        return self._json(200, sm.estimate(aid, voices_only=True))
                    MOMENTS.run_voices(aid)
                    return self._json(200, {"ok": True})
            if p == "projects":
                return self._json(*PROJECTS.create(body))
            if p.startswith("projects/") and p.endswith("/restore"):
                pid = p.split("/")[1]
                d = PROJECTS.version(pid, body.get("ts", ""))
                cur = PROJECTS.get(pid) or {}
                if not d:
                    return self._json(404, {"errors": ["No such version."]})
                return self._json(*PROJECTS.put(pid, d, cur.get("rev")))
            if p == "loudness":            # Normalize voices: {asset, ranges: [[s, e], ...]} -> {lufs, seconds}
                meta = ASSETS.meta(body.get("asset", ""))
                if not meta:
                    return self._json(404, {"errors": ["No such asset."]})
                import studio_render as sr
                ranges = [r for r in body.get("ranges") or [] if isinstance(r, list) and len(r) == 2][:2000]
                src = prep.orig_path(meta["id"], meta) if meta["kind"] == "video" else sc.MEDIA / meta["rel"]
                lufs = sr.range_loudness(src, ranges)
                return self._json(200, {"lufs": lufs, "seconds": round(sum(max(0.0, float(b) - float(a)) for a, b in ranges), 2)})
            if p == "export":
                return self._json(*EXPORTS.add(body.get("project", ""), front=True))
            if p == "export/all":
                return self._json(*EXPORTS.add_done())
            if p == "export/cancel":
                return self._json(*EXPORTS.cancel(body.get("id", "")))
            return self._json(404, {"errors": ["Unknown endpoint."]})
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            return self._json(500, {"errors": [f"{type(e).__name__}: {e}"]})

    def do_PATCH(self):
        u = urlparse(self.path)
        p = u.path[len("/api/"):] if u.path.startswith("/api/") else ""
        body = self._body()
        try:
            parts = p.split("/")
            if parts[0] == "asset" and len(parts) >= 3:
                aid = parts[1]
                if not ASSETS.meta(aid):
                    return self._json(404, {"errors": ["No such asset."]})
                if parts[2] == "transcript":
                    f = sc.CACHE / aid / "transcript-edits.json"
                    edits = sc.read_json(f, {}) or {}
                    for k, v in (body.get("edits") or {}).items():
                        if v is None:
                            edits.pop(str(int(k)), None)
                        else:
                            edits[str(int(k))] = str(v)[:80]
                    sc.write_json_atomic(f, edits)
                    FEED.bump()
                    return self._json(200, {"edits": edits,
                                            "trev": file_rev(sc.CACHE / aid / "transcript.json", f)})
                if parts[2] == "speakers":
                    import studio_speakers as ss
                    try:
                        r = ss.apply_patch(aid, body)
                    except ValueError as e:
                        return self._json(400, {"errors": [str(e)]})
                    FEED.bump()
                    return self._json(200, r)
                if parts[2] == "calls" and len(parts) == 4:    # {watched: true} after a few seconds of play (B19)
                    r = calls.row(aid, parts[3])
                    if not r:
                        return self._json(404, {"errors": ["No such call."]})
                    if body.get("watched") is not True:
                        return self._json(400, {"errors": ["Only {watched: true} is saved."]})
                    calls.mark_watched(aid, r["start"], r["end"])
                    return self._json(200, {"ok": True, "id": r["id"]})
                if parts[2] == "moments" and len(parts) == 4:
                    f = sc.CACHE / aid / "moments.json"
                    mo = sc.read_json(f)
                    if not mo:
                        return self._json(404, {"errors": ["No moments."]})
                    for m in mo["moments"]:
                        if m["id"] == parts[3]:
                            for k in ("state", "start", "end", "title"):
                                if k in body:
                                    m[k] = body[k]
                    sc.write_json_atomic(f, mo)
                    FEED.bump()
                    return self._json(200, {"ok": True})
            return self._json(404, {"errors": ["Unknown endpoint."]})
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            return self._json(500, {"errors": [f"{type(e).__name__}: {e}"]})

    def do_DELETE(self):
        u = urlparse(self.path)
        p = u.path[len("/api/"):] if u.path.startswith("/api/") else ""
        try:
            if p.startswith("projects/"):
                PROJECTS.delete(p.split("/")[1])
                return self._json(200, {"ok": True})
            return self._json(404, {"errors": ["Unknown endpoint."]})
        except Exception as e:  # noqa: BLE001
            return self._json(500, {"errors": [f"{type(e).__name__}: {e}"]})


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False   # never two servers on one port (Windows lets a second bind beside the first)


def scanner():
    while True:
        try:
            ASSETS.scan()
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        time.sleep(2)


def main():
    global ASSETS, PREP, MOMENTS, PROJECTS, EXPORTS, SESSION
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--no-scan", action="store_true", help="tests: do not prepare files automatically")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    sc.ensure_dirs()
    sc.kill_orphans()
    socketserver.TCPServer.allow_reuse_address = False
    ASSETS, PREP, MOMENTS, PROJECTS, EXPORTS = Assets(), PrepQueue(), MomentJobs(), Projects(), Exports()
    SESSION = studio_session.Controller(args.port, SESSION_FEED)
    try:
        httpd = Server(("127.0.0.1", args.port), Handler)
    except OSError as e:
        sys.exit(f"Port {args.port} is busy ({e}).")
    threading.Thread(target=SESSION.recover, daemon=True).start()   # unconfirmed writes, cards still to file
    threading.Thread(target=PREP.loop, daemon=True).start()
    threading.Thread(target=EXPORTS.loop, daemon=True).start()
    for aid in list(ASSETS.index):   # finish anything a previous run left unprepared, or a stage added since
        st = ASSETS.status(aid)
        meta = ASSETS.meta(aid) or {}
        # a stage marked done whose output is gone counts too (2026-10-02: a "Prepare again" lost to a restart left a
        # recording's remux missing while status.json still said done), as does a "Prepare again" still waiting
        if (not st or any(s.get("state") != "done" for s in st.values()) or prep.missing_stages(aid, meta, st)
                or prep.redo_stages(aid)):
            PREP.enqueue(aid)
    threading.Thread(target=startup_calls, daemon=True).start()
    if not args.no_scan:
        threading.Thread(target=scanner, daemon=True).start()
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Monarc Studio at {url}  (media {sc.MEDIA}, version {VERSION})", flush=True)
    if not args.no_open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
