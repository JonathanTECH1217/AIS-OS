"""Monarc Studio prep stages (2026-09-29): what happens to a file after it lands in media/.

Per asset, in media/.studio/<asset-id>/:
  meta.json          probe facts, kind, media-relative path, which file plays as the original
  status.json        {"stages": {name: {"state": queued|running|done|error|skipped, "progress": 0..1, "error"}}}
  orig.mp4           remux of a non-MP4 video (stream copy, +faststart); MP4 sources play as they are
  peaks-100.i8       waveform: int8 [min,max] pairs per 10 ms, scaled so the loudest point is 127
  peaks-10.i8        the same per 100 ms
  proxy.mp4          540x960, 30 fps constant, a keyframe every 15 frames (Quick Sync, libx264 fallback)
  thumbs/t2-NNN.jpg  sprite sheets: 72x128 tiles, 10x10 per sheet, one tile per 2 s (a sheet covers 200 s)
  transcript.json    from studio_transcribe.py (inbox recordings only)
  speakers.json      the voice split from studio_speakers.py (inbox recordings only, after the transcript)
  blocks/<sr>/<i>.wav  30 s stereo PCM blocks at the browser's sample rate, made on request for playback

Stages per kind:  inbox video: remux, peaks, proxy, transcript, speakers.  assets video: remux, peaks, proxy.
                  audio: peaks.  image: none.
Every output is written as .part and renamed when complete, so a restart redoes only unfinished stages.

  python scripts/studio_prep.py <file>     run every stage for one file in the foreground (for testing)
"""
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_common as sc  # noqa: E402

BLOCK_S = 30
THUMB_EVERY = 2
THUMB_W, THUMB_H = 72, 128
THUMB_TILE = 10


def asset_dir(aid):
    return sc.CACHE / aid


def stages_for(kind, rel):
    if kind == "video":
        return (["remux", "peaks", "proxy", "transcript", "speakers"] if rel.startswith("inbox/")
                else ["remux", "peaks", "proxy"])
    if kind == "audio":
        return ["peaks"]
    return []


def orig_path(aid, meta):
    """The file the editor treats as the original: the remux for MKV and friends, the source for MP4. While the remux
    is missing (being made again, or lost) the source itself stands in; ffmpeg reads the MKV the same. 2026-10-02: a
    lost remux left every short from that recording silent, because the sound blocks read only the remux."""
    if meta.get("orig") == "cache":
        p = asset_dir(aid) / "orig.mp4"
        if p.exists():
            return p
    return sc.MEDIA / meta["rel"]


def done_file(aid, stage, meta):
    d = asset_dir(aid)
    return {"remux": (d / "orig.mp4") if meta.get("orig") == "cache" else sc.MEDIA / meta["rel"],
            "peaks": d / "peaks-10.i8",
            "proxy": d / "thumbs" / ".done",
            "transcript": d / "transcript.json",
            "speakers": d / "speakers.json"}.get(stage)


def missing_stages(aid, meta, status):
    """The stages that need a run: not marked done, or marked done while their output is gone (a file deleted by hand,
    a "Prepare again" that never got to run). The server checks this at start rather than trusting status.json."""
    out = []
    for s in stages_for((meta or {}).get("kind"), (meta or {}).get("rel") or ""):
        f = done_file(aid, s, meta)
        if ((status or {}).get(s) or {}).get("state") != "done" or (f is not None and not f.exists()):
            out.append(s)
    return out


# "Prepare again" (2026-10-02): the stages to make again wait in redo.json and each one's old output is removed only
# when that stage runs. It used to be deleted at the click, and prep can wait a long time (Monarc Calls holds it
# while OBS records; a restart loses the queue), which left the remux missing and the shorts silent.
def redo_path(aid):
    return asset_dir(aid) / "redo.json"


def request_redo(aid, stages):
    known = set(STAGE_FN)
    cur = set((sc.read_json(redo_path(aid), {}) or {}).get("stages") or [])
    cur |= {s for s in stages if s in known}
    sc.write_json_atomic(redo_path(aid), {"stages": sorted(cur), "t": time.time()})
    return sorted(cur)


def redo_stages(aid):
    return set((sc.read_json(redo_path(aid), {}) or {}).get("stages") or [])


def _redo_done(aid, stage):
    cur = redo_stages(aid)
    if stage in cur:
        cur.discard(stage)
        if cur:
            sc.write_json_atomic(redo_path(aid), {"stages": sorted(cur), "t": time.time()})
        else:
            redo_path(aid).unlink(missing_ok=True)


def make_meta(aid, path):
    rel = sc.rel_media(path)
    kind = sc.kind_of(path)
    meta = {"id": aid, "rel": rel, "name": Path(path).name, "kind": kind, "size": Path(path).stat().st_size,
            "mtime": Path(path).stat().st_mtime}
    if kind in ("video", "audio"):
        info = sc.probe(path)
        meta.update(duration=info["duration"], video=info["video"], audio=info["audio"])
        if kind == "video":
            v = info["video"] or {}
            meta["orig"] = "source" if Path(path).suffix.lower() in (".mp4", ".m4v") and v.get("codec") == "h264" else "cache"
            # Jonathan removed the full-size copy to free space (B20, 2026-10-01): a re-scan must not bring it back
            old = sc.read_json(asset_dir(aid) / "meta.json", {}) or {}
            if meta["orig"] == "cache" and old.get("orig") == "removed" and not (asset_dir(aid) / "orig.mp4").exists():
                meta["orig"] = "removed"
    elif kind == "image":
        try:
            from PIL import Image
            with Image.open(path) as im:
                meta["w"], meta["h"] = im.size
        except Exception:
            pass
    return meta


class Status:
    """status.json with a callback on every change (the server bumps the bin revision)."""

    def __init__(self, aid, stages, on_change=None):
        self.path = asset_dir(aid) / "status.json"
        self.on_change = on_change or (lambda: None)
        old = sc.read_json(self.path, {}) or {}
        self.data = {"stages": {s: old.get("stages", {}).get(s, {"state": "queued", "progress": 0}) for s in stages}}
        for s in self.data["stages"].values():
            if s["state"] == "running":
                s["state"] = "queued"
        self._last = 0
        self.save(force=True)

    def set(self, stage, force=False, **kw):
        self.data["stages"][stage].update(kw)
        self.save(force=force or kw.get("state") in ("done", "error", "running"))

    def save(self, force=False):
        now = time.time()
        if force or now - self._last > 0.5:
            self._last = now
            sc.write_json_atomic(self.path, self.data)
            self.on_change()


# ---------------------------------------------------------------- stages

def stage_remux(aid, meta, st, cancel):
    if meta.get("orig") != "cache":
        return
    d = asset_dir(aid)
    part = d / "orig.mp4.part"
    args = [sc.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error", "-i", sc.MEDIA / meta["rel"],
            "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy", "-movflags", "+faststart", "-f", "mp4",
            "-progress", "pipe:1", "-nostats", part]
    code, err = sc.run_proc(args, lambda p: st.set("remux", progress=p), cancel, total=meta.get("duration"))
    if code:
        raise RuntimeError(err[-400:] or f"ffmpeg exit {code}")
    part.replace(d / "orig.mp4")


def stage_peaks(aid, meta, st, cancel):
    d = asset_dir(aid)
    src = orig_path(aid, meta) if meta["kind"] == "video" else sc.MEDIA / meta["rel"]
    total = meta.get("duration") or 0
    if not meta.get("audio"):
        (d / "peaks-100.i8").write_bytes(b"")
        (d / "peaks-10.i8").write_bytes(b"")
        return
    args = [sc.ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
            "-f", "s16le", "-"]
    proc = sc.popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    mins, maxs, rest, got = [], [], np.zeros(0, np.int16), 0
    try:
        while True:
            if cancel is not None and cancel.is_set():
                raise sc.Cancelled()
            raw = proc.stdout.read(16000 * 2 * 20)
            if not raw:
                break
            a = np.concatenate([rest, np.frombuffer(raw[:len(raw) // 2 * 2], np.int16)])
            n = len(a) // 160
            blk = a[:n * 160].reshape(n, 160)
            mins.append(blk.min(axis=1))
            maxs.append(blk.max(axis=1))
            rest = a[n * 160:]
            got += n
            if total:
                st.set("peaks", progress=min(1.0, got / 100 / total))
    finally:
        proc.kill()
        proc.wait()
        sc.untrack(proc)
    lo = np.concatenate(mins).astype(np.float32) if mins else np.zeros(0, np.float32)
    hi = np.concatenate(maxs).astype(np.float32) if maxs else np.zeros(0, np.float32)
    ref = float(np.percentile(np.maximum(np.abs(lo), np.abs(hi)), 99.9)) if len(lo) else 1.0
    ref = max(ref, 1.0)

    def pack(lo, hi):
        out = np.empty(len(lo) * 2, np.int8)
        out[0::2] = np.clip(lo / ref * 127, -127, 127).astype(np.int8)
        out[1::2] = np.clip(hi / ref * 127, -127, 127).astype(np.int8)
        return out.tobytes()

    (d / "peaks-100.i8.part").write_bytes(pack(lo, hi))
    n10 = len(lo) // 10
    lo10 = lo[:n10 * 10].reshape(n10, 10).min(axis=1)
    hi10 = hi[:n10 * 10].reshape(n10, 10).max(axis=1)
    (d / "peaks-10.i8.part").write_bytes(pack(lo10, hi10))
    (d / "peaks-100.i8.part").replace(d / "peaks-100.i8")
    (d / "peaks-10.i8.part").replace(d / "peaks-10.i8")
    meta["peak_ref"] = ref / 32768.0
    cur = sc.read_json(d / "meta.json") or meta      # the file as it is now, so a change made since prep began stays
    cur["peak_ref"] = meta["peak_ref"]
    sc.write_json_atomic(d / "meta.json", cur)


def stage_proxy(aid, meta, st, cancel):
    """The small copy the monitor plays at 1/2 and 1/4. libx264 on the CPU, frames on an exact 30 fps grid (the fps
    filter, the same grid the exporter decodes on), the source's own shape fitted inside 540x960 (a 16:9 B-roll stays
    16:9), a keyframe every 15 frames for quick seeking. Quick Sync was tried first (2026-09-29) and dropped: it
    duplicated frames on some files (a 20 s test clip came out 37 s long) and was no faster (4.4 s vs 4.6 s per minute)."""
    d = asset_dir(aid)
    src = orig_path(aid, meta)
    total = meta.get("duration")
    part = d / "proxy.mp4.part"
    audio = ["-c:a", "aac", "-b:a", "128k", "-ac", "2"] if meta.get("audio") else ["-an"]
    ff = sc.ffmpeg_exe()
    if not (d / "proxy.mp4").exists():
        args = [ff, "-y", "-hide_banner", "-loglevel", "error", "-i", src,
                "-vf", "fps=30,scale=540:960:force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libx264", "-preset", "ultrafast", "-tune", "fastdecode",
                "-crf", "30", "-g", "15", "-keyint_min", "15", "-sc_threshold", "0", "-bf", "0",
                "-pix_fmt", "yuv420p"] + audio + ["-movflags", "+faststart", "-f", "mp4", "-progress", "pipe:1",
                                                  "-nostats", part]
        code, err = sc.run_proc(args, lambda p: st.set("proxy", progress=p * 0.9), cancel, total=total)
        if code:
            raise RuntimeError(err[-400:] or f"ffmpeg exit {code}")
        part.replace(d / "proxy.mp4")
    th = d / "thumbs"
    th.mkdir(exist_ok=True)
    for old in th.glob("t2-*.jpg"):
        old.unlink()
    args = [ff, "-y", "-hide_banner", "-loglevel", "error", "-skip_frame", "nokey", "-i", d / "proxy.mp4",
            "-vf", f"fps=1/{THUMB_EVERY},scale={THUMB_W}:{THUMB_H},tile={THUMB_TILE}x{THUMB_TILE}", "-q:v", "5",
            "-an", "-progress", "pipe:1", "-nostats", th / "t2-%03d.jpg"]
    code, err = sc.run_proc(args, lambda p: st.set("proxy", progress=0.9 + p * 0.1), cancel, total=total)
    if code:
        raise RuntimeError(err[-400:] or f"ffmpeg exit {code}")
    (th / ".done").write_text(json.dumps({"every": THUMB_EVERY, "w": THUMB_W, "h": THUMB_H, "tile": THUMB_TILE}))


def stage_transcript(aid, meta, st, cancel):
    if not (sc.PARAKEET_DIR / "encoder.int8.onnx").exists():
        raise RuntimeError("speech model missing: python scripts/studio_check.py --get-models")
    _run_child("studio_transcribe.py", "transcript", aid, meta, st, cancel)


def stage_speakers(aid, meta, st, cancel):
    if not (sc.SPK_SEG.exists() and sc.SPK_EMB.exists()):
        raise RuntimeError("speaker models missing: python scripts/studio_check.py --get-models")
    _run_child("studio_speakers.py", "speakers", aid, meta, st, cancel)


def _run_child(script, stage, aid, meta, st, cancel):
    """A Python child that prints {"pos", "total"} JSON lines and writes <stage>.json into the asset folder."""
    d = asset_dir(aid)
    src = sc.MEDIA / meta["rel"]
    proc = sc.popen([sc.python_exe(), "-u", str(Path(__file__).with_name(script)), str(src),
                     str(d), "--asset", aid, "--resume"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    err_tail = []

    def read_err():
        for ln in proc.stderr:
            err_tail.append(ln.decode("utf-8", "replace"))
            del err_tail[:-30]

    threading.Thread(target=read_err, daemon=True).start()
    try:
        for raw in proc.stdout:
            if cancel is not None and cancel.is_set():
                proc.kill()
                raise sc.Cancelled()
            try:
                msg = json.loads(raw)
                if msg.get("total"):
                    st.set(stage, progress=min(1.0, msg["pos"] / msg["total"]))
            except ValueError:
                pass
        proc.wait()
    finally:
        sc.untrack(proc)
    if proc.returncode or not done_file(aid, stage, meta).exists():
        raise RuntimeError("".join(err_tail)[-400:] or f"{script} exit {proc.returncode}")


STAGE_FN = {"remux": stage_remux, "peaks": stage_peaks, "proxy": stage_proxy, "transcript": stage_transcript,
            "speakers": stage_speakers}


def run_asset(aid, meta, on_change=None, cancel=None):
    """Run the asset's unfinished stages. Remux and peaks first; then the proxy beside transcript-then-voices (the
    voice split cuts its windows at the transcript's pauses)."""
    stages = stages_for(meta["kind"], meta["rel"])
    st = Status(aid, stages, on_change)
    if not stages:
        return st
    redo = redo_stages(aid)

    def run(stage):
        f = done_file(aid, stage, meta)
        if stage in redo and f is not None and f.exists() and f.is_relative_to(sc.CACHE):
            f.unlink()           # "Prepare again": the old output goes only now, as the stage starts over
        if f is not None and f.exists():
            st.set(stage, state="done", progress=1)
            _redo_done(aid, stage)
            return
        st.set(stage, state="running", progress=0)
        try:
            STAGE_FN[stage](aid, meta, st, cancel)
            st.set(stage, state="done", progress=1, error=None)
            _redo_done(aid, stage)
        except sc.Cancelled:
            st.set(stage, state="queued", progress=0)
            raise
        except Exception as e:  # noqa: BLE001
            st.set(stage, state="error", error=f"{type(e).__name__}: {e}"[-500:])

    for s in ("remux", "peaks"):
        if s in stages:
            run(s)
    speech = [s for s in ("transcript", "speakers") if s in stages]

    def run_speech():
        for s in speech:
            if s == "speakers" and st.data["stages"].get("transcript", {}).get("state") != "done":
                # the split cuts its windows at the transcript's pauses; 35 minutes on a guess is not worth it
                st.set("speakers", state="error", error="Waits for the transcript. Retry the transcript first.")
                continue
            run(s)

    if "proxy" in stages and speech:
        t = threading.Thread(target=run_speech, daemon=True)
        t.start()
        run("proxy")
        t.join()
    else:
        if "proxy" in stages:
            run("proxy")
        run_speech()
    return st


# ---------------------------------------------------------------- the dial tone (Trailer, 2026-09-30)

def find_ring(aid, meta, t, window=45.0, calls=None, cur=None):
    """Where the last ring (US ringback: 440 + 480 Hz, 2 s on) starts before source second t, or None. The search
    stays after the previous call ends (moments.json, or the calls given), so another call's ring never gets pulled
    in. On the Caitlin call the ring shows 4.9 to 3.2 s before she picks up. cur: the call t belongs to, when the
    caller knows it (calls can overlap, so guessing from t can pick the wrong one)."""
    import studio_transcribe as st
    if calls is None:
        calls = (sc.read_json(asset_dir(aid) / "moments.json", {}) or {}).get("calls", [])
    if cur is None:
        cur = next((c for c in calls if c["start"] - 1 <= t <= c["end"] + 1), None)
    before = cur["start"] if cur else t
    prev_end = max([c["end"] for c in calls if c["end"] <= before - 0.5] or [0.0])
    lo, hi = max(0.0, t - window, prev_end), t + 1.0
    if hi - lo < 1.0:
        return None
    x = np.concatenate(list(st.pcm(orig_path(aid, meta), lo, hi - lo)) or [np.zeros(0, np.float32)])
    sr, win, hop = 16000, 3200, 1600
    f = np.fft.rfftfreq(win, 1 / sr)
    tone = ((f >= 435) & (f <= 445)) | ((f >= 475) & (f <= 485))
    speech = (f >= 100) & (f <= 4000)
    hann = np.hanning(win)
    ring = []
    for i in range(0, max(0, len(x) - win), hop):
        seg = x[i:i + win]
        s = np.abs(np.fft.rfft(seg * hann)) ** 2
        db = 10 * np.log10(np.mean(seg ** 2) + 1e-12)
        ring.append(bool(db > -60 and s[tone].sum() / (s[speech].sum() + 1e-12) > 0.5))
    starts, run = [], 0
    for k, r in enumerate(ring + [False]):
        if r:
            run += 1
        else:
            if run * hop / sr >= 0.8:
                starts.append(k - run)
            run = 0
    return round(lo + starts[-1] * hop / sr, 3) if starts else None


# ---------------------------------------------------------------- playback blocks

_block_lock = threading.Lock()


def audio_block(aid, meta, i, sr):
    """Path of a 30 s stereo s16 WAV block at sample rate sr, made on first request."""
    sr = int(sr) if int(sr) in (22050, 32000, 44100, 48000, 88200, 96000) else 48000
    d = asset_dir(aid) / "blocks" / str(sr)
    out = d / f"{int(i)}.wav"
    if out.exists():
        return out
    d.mkdir(parents=True, exist_ok=True)
    src = orig_path(aid, meta) if meta["kind"] == "video" else sc.MEDIA / meta["rel"]
    part = out.with_suffix(f".{threading.get_ident()}.part")
    args = [sc.ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error", "-ss", str(int(i) * BLOCK_S), "-i", str(src),
            "-t", str(BLOCK_S), "-vn", "-ac", "2", "-ar", str(sr), "-c:a", "pcm_s16le", "-f", "wav", str(part)]
    r = subprocess.run(args, capture_output=True, creationflags=sc.NO_WINDOW)
    if r.returncode or not part.exists():
        part.unlink(missing_ok=True)
        raise RuntimeError(r.stderr.decode("utf-8", "replace")[-300:])
    with _block_lock:
        if not out.exists():
            part.replace(out)
        else:
            part.unlink(missing_ok=True)
    return out


if __name__ == "__main__":
    f = Path(sys.argv[1]).resolve()
    aid = sc.asset_id(f)
    asset_dir(aid).mkdir(parents=True, exist_ok=True)
    meta = make_meta(aid, f)
    sc.write_json_atomic(asset_dir(aid) / "meta.json", meta)
    t0 = time.time()
    st = run_asset(aid, meta, on_change=lambda: None)
    print(json.dumps(st.data, indent=1))
    print(f"{time.time() - t0:.0f} s")
