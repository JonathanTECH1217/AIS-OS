"""Who said each word, for Monarc Studio's speaker-colored captions (2026-09-30).

The recordings have one mixed audio track, so the voices are split on this laptop: sherpa-onnx runs pyannote
segmentation 3.0 (who speaks when, MIT) and WeSpeaker ResNet34-LM voiceprints (trained on VoxCeleb) over ~10-minute
windows, cut at the longest transcript pause near each 10-minute mark so a call is rarely cut in two. Each window's
voices become groups S1, S2, ... (never reused across windows); a person usually lands in 2 or 3 groups, which the
labels join back up. Measured on the 4 h 03 m session: about 7x real time, so ~35 minutes after the transcript.
CAM++ voiceprints were tried and dropped (they put Jonathan and a prospect in one group).

  python scripts/studio_speakers.py <source> <asset_dir> --asset a_xxx [--resume]   the split (a prep stage)

Files per recording, next to transcript.json:
  speakers.json         the split, never edited: {v, asset, rev, model, windows, turns: [[start, end, key]],
                        groups: {key: {win, sec, turns, f0, emb}}}
  speaker-labels.json   Claude's labels (studio_moments.py): {rev, model, jonathan: [keys], voices: {key: {gender,
                        name, role, same_as}}}
  speaker-edits.json    Jonathan's fixes: {rev, groups: {key: {who, gender}}, merge: {key: key}, words: {id: key},
                        new: {N1: {gender}}}
Labels and fixes carry the split's rev; after a new split they are set aside as *.stale-<rev>.json (word fixes that
point at "me" or a new voice are kept).

resolve(asset) decides each word's voice. Per group the first source with an answer wins: Jonathan's fix, Claude's
label, then a local guess (his saved voiceprint, then pitch: 165 Hz and up is a woman). Every group that resolves to
Jonathan becomes one voice, "me". Classes: me, f (woman), m (man), u (unknown: today's white look).

His voiceprint (~/.monarc/studio-voiceprint.json, STUDIO_VOICEPRINT for tests) is rebuilt from the groups Claude or
he marked as him, never from guesses; voiceprint scores between two people run close to scores for the same person
on these calls (0.65 to 0.85), so it is only the fallback, with a threshold set from the labeled groups.
"""
import argparse
import bisect
import hashlib
import json
import sys
import threading
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_common as sc  # noqa: E402

SR = 16000
MODEL_TAG = "pyannote-seg-3.0+wespeaker-resnet34-LM"
THRESHOLD = 0.5          # clustering; looser settings merged Jonathan with the prospect in the 2026-09-30 test
MIN_ON, MIN_OFF = 0.3, 0.5
WINDOW = 600             # seconds
WINDOW_SLACK = 90        # a cut may move this far from the 10-minute mark to land in a pause
MIN_LAST = 120           # a shorter last window joins the one before
EMB_MIN_TURN = 0.8       # turns used for a group's voiceprint
EMB_MAX = 30.0           # seconds of audio per group voiceprint
NEAR = 0.3               # a word in a gap takes the nearest turn within this many seconds
FILL_GAP = 0.6           # a word still without a voice takes its neighbour's if no pause over this sits between
WOMAN_HZ = 165.0
CLASSES = ("me", "f", "m", "u")
ROLE_NAMES = {"gatekeeper": "Gatekeeper", "owner": "Owner", "service_rep": "Service rep",
              "voicemail_greeting": "Voicemail greeting", "phone_menu": "Phone menu"}


# ------------------------------------------------------------------ the split

def plan_windows(duration, segments=None, window=WINDOW):
    """[(start, end)] covering the file; cuts sit in the longest pause between transcript segments near each mark."""
    gaps = []
    segs = segments or []
    for a, b in zip(segs, segs[1:]):
        if b[0] > a[1]:
            gaps.append((a[1], b[0]))
    cuts, last = [], 0.0
    k = 1
    while k * window < duration - MIN_LAST:
        mark = k * window
        near = [g for g in gaps if abs((g[0] + g[1]) / 2 - mark) <= WINDOW_SLACK and (g[0] + g[1]) / 2 > last + MIN_LAST]
        cut = (max(near, key=lambda g: g[1] - g[0]) if near else None)
        cut = round((cut[0] + cut[1]) / 2, 3) if cut else float(mark)
        if cut > last + MIN_LAST and cut < duration - MIN_LAST:
            cuts.append(cut)
            last = cut
        k += 1
    edges = [0.0] + cuts + [round(float(duration), 3)]
    return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1) if edges[i + 1] > edges[i]]


def pitch_median(x, sr=SR, fmin=65.0, fmax=400.0, frame=1024, hop=256, thresh=0.15):
    """Median voice pitch in Hz (YIN over the louder 40 % of frames), or None when too little is voiced."""
    x = np.asarray(x, dtype=np.float64)
    if len(x) < frame * 2:
        return None
    n = 1 + (len(x) - frame) // hop
    fr = x[np.arange(frame)[None, :] + hop * np.arange(n)[:, None]]
    rms = np.sqrt((fr ** 2).mean(axis=1))
    fr = fr[rms > max(np.percentile(rms, 60), 1e-4)]
    if len(fr) < 5:
        return None
    fr = fr - fr.mean(axis=1, keepdims=True)
    w = frame // 2
    tau_min, tau_max = int(sr / fmax), min(int(sr / fmin), frame - w)
    nfft = 2048
    acf = np.fft.irfft(np.conj(np.fft.rfft(fr[:, :w], nfft)) * np.fft.rfft(fr, nfft), nfft)[:, :tau_max + 1]
    cs = np.concatenate([np.zeros((len(fr), 1)), np.cumsum(fr ** 2, axis=1)], axis=1)
    d = cs[:, w][:, None] + (cs[:, w:w + tau_max + 1] - cs[:, :tau_max + 1]) - 2 * acf
    d[:, 0] = 0
    taus = np.arange(1, tau_max + 1)
    cmndf = np.ones_like(d)
    cmndf[:, 1:] = d[:, 1:] * taus / np.maximum(np.cumsum(d[:, 1:], axis=1), 1e-12)
    f0 = []
    for row in cmndf:
        hit = np.nonzero(row[tau_min:] < thresh)[0]
        if not len(hit):
            continue
        t = int(hit[0]) + tau_min
        while t + 1 <= tau_max and row[t + 1] < row[t]:
            t += 1
        tt = float(t)
        if 1 <= t < tau_max:
            a, b, c = row[t - 1], row[t], row[t + 1]
            den = a - 2 * b + c
            if abs(den) > 1e-12:
                tt = t + 0.5 * (a - c) / den
        f0.append(sr / tt)
    return float(np.median(f0)) if len(f0) >= 5 else None


def load_models(threads=3):
    import sherpa_onnx
    if not sc.SPK_SEG.exists() or not sc.SPK_EMB.exists():
        raise RuntimeError("speaker models missing: python scripts/studio_check.py --get-models")
    cfg = sherpa_onnx.OfflineSpeakerDiarizationConfig(
        segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
            pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(model=str(sc.SPK_SEG)),
            num_threads=threads),
        embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=str(sc.SPK_EMB), num_threads=threads),
        clustering=sherpa_onnx.FastClusteringConfig(num_clusters=-1, threshold=THRESHOLD),
        min_duration_on=MIN_ON, min_duration_off=MIN_OFF)
    if not cfg.validate():
        raise RuntimeError("speaker split config did not validate")
    ex = sherpa_onnx.SpeakerEmbeddingExtractor(
        sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=str(sc.SPK_EMB), num_threads=threads))
    return sherpa_onnx.OfflineSpeakerDiarization(cfg), ex


def embed(ex, x):
    s = ex.create_stream()
    s.accept_waveform(SR, x)
    s.input_finished()
    v = np.asarray(ex.compute(s), dtype=np.float32)
    return v / (np.linalg.norm(v) + 1e-9)


def group_audio(audio, w0, spans):
    """Up to EMB_MAX seconds of a group's audio, longest turns first (turns under EMB_MIN_TURN only if nothing else)."""
    spans = sorted(spans, key=lambda t: t[0] - t[1])
    use = [t for t in spans if t[1] - t[0] >= EMB_MIN_TURN] or spans
    out, got = [], 0.0
    for s, e in use:
        take = min(e - s, EMB_MAX - got)
        a = int((s - w0) * SR)
        out.append(audio[max(0, a):max(0, a + int(take * SR))])
        got += take
        if got >= EMB_MAX:
            break
    return np.concatenate(out) if out else np.zeros(0, np.float32)


def split_window(sd, ex, audio, w0, wi, first_key):
    """Diarize one window. Returns (turns, groups, next_key)."""
    res = sd.process(audio).sort_by_start_time()
    local, turns = {}, []
    for r in res:
        if r.speaker not in local:
            local[r.speaker] = f"S{first_key + len(local)}"
        turns.append([round(w0 + r.start, 3), round(w0 + r.end, 3), local[r.speaker]])
    groups = {}
    for key in local.values():
        spans = [(s, e) for s, e, k in turns if k == key]
        clip = group_audio(audio, w0, spans)
        emb = None
        if len(clip) >= SR // 2:
            try:
                emb = [round(float(v), 5) for v in embed(ex, clip)]
            except Exception:  # noqa: BLE001  (a clip the extractor refuses: no voiceprint for this group)
                emb = None
        f0 = pitch_median(clip)
        groups[key] = {"win": wi, "sec": round(sum(e - s for s, e in spans), 2), "turns": len(spans),
                       "f0": round(f0, 1) if f0 else None, "emb": emb}
    return turns, groups, first_key + len(local)


def finalize(out_dir, result):
    """Write speakers.json; labels and fixes made for an older split are set aside (word fixes to "me"/N* kept)."""
    rev = result["rev"]
    for name in ("speaker-labels.json", "speaker-edits.json"):
        p = out_dir / name
        old = sc.read_json(p)
        if not old or old.get("rev") in (None, rev):
            continue
        p.replace(out_dir / f"{p.stem}.stale-{old.get('rev')}.json")
        if name == "speaker-edits.json":
            keep = {k: v for k, v in (old.get("words") or {}).items() if v == "me" or str(v).startswith("N")}
            if keep or old.get("new"):
                sc.write_json_atomic(p, {"rev": rev, "groups": {}, "merge": {}, "words": keep, "new": old.get("new") or {}})
    sc.write_json_atomic(out_dir / "speakers.json", result)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("asset_dir")
    ap.add_argument("--asset", required=True)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--threads", type=int, default=3)
    a = ap.parse_args()
    import studio_transcribe as st
    src, out = Path(a.source), Path(a.asset_dir)
    info = sc.probe(src)
    duration = info["duration"] or 0.0
    tr = sc.read_json(out / "transcript.json") or {}
    wins = plan_windows(duration, tr.get("segments"))
    partial = out / "speakers.partial.jsonl"
    done = {}
    if a.resume and partial.exists():
        for ln in partial.read_text(encoding="utf-8").splitlines():
            try:
                p = json.loads(ln)
            except ValueError:
                continue
            if p.get("windows") == [list(w) for w in wins]:
                done[p["win"]] = p
    elif partial.exists():
        partial.unlink()
    next_key = 1 + max([int(k[1:]) for p in done.values() for k in p["groups"]] or [0])
    if info.get("audio") and wins:
        sd, ex = load_models(a.threads)
        with open(partial, "a", encoding="utf-8") as pf:
            for wi, (w0, w1) in enumerate(wins):
                if wi in done:
                    continue
                audio = np.concatenate(list(st.pcm(src, w0, w1 - w0)) or [np.zeros(0, np.float32)])
                turns, groups, next_key = split_window(sd, ex, audio, w0, wi, next_key)
                rec = {"win": wi, "windows": [list(w) for w in wins], "turns": turns, "groups": groups}
                done[wi] = rec
                pf.write(json.dumps(rec) + "\n")
                pf.flush()
                print(json.dumps({"pos": round(w1, 1), "total": round(duration, 1)}), flush=True)
    turns = sorted((t for p in done.values() for t in p["turns"]), key=lambda t: (t[0], t[1]))
    groups = {k: v for p in sorted(done.values(), key=lambda p: p["win"]) for k, v in p["groups"].items()}
    rev = hashlib.sha1(json.dumps(turns, separators=(",", ":")).encode()).hexdigest()[:12]
    result = {"v": 1, "asset": a.asset, "rev": rev, "model": MODEL_TAG, "threshold": THRESHOLD,
              "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "duration": duration,
              "windows": [list(w) for w in wins], "turns": turns, "groups": groups}
    finalize(out, result)
    partial.unlink(missing_ok=True)
    print(json.dumps({"pos": round(duration, 1), "total": round(duration, 1), "done": True,
                      "groups": len(groups), "turns": len(turns)}), flush=True)


# ------------------------------------------------------------------ reading the labels

def asset_dir(aid):
    return sc.CACHE / aid


def load(aid):
    """(speakers, labels, edits) for a recording, with labels and fixes from another split dropped."""
    d = asset_dir(aid)
    sp = sc.read_json(d / "speakers.json")
    if not sp:
        return None, {}, {}
    labels = sc.read_json(d / "speaker-labels.json", {}) or {}
    edits = sc.read_json(d / "speaker-edits.json", {}) or {}
    if labels.get("rev") != sp["rev"]:
        labels = {}
    if edits.get("rev") not in (None, sp["rev"]):
        edits = {}
    for k in ("groups", "merge", "words", "new"):
        edits.setdefault(k, {})
    return sp, labels, edits


def load_words(aid):
    tr = sc.read_json(asset_dir(aid) / "transcript.json") or {}
    return tr.get("words") or []


def voices_rev(aid):
    """Changes whenever anything that decides a word's voice changes (the split, Claude's labels, the fixes, the
    voiceprint), so the page knows to fetch the voices again."""
    d = asset_dir(aid)
    parts = []
    for p in (d / "speakers.json", d / "speaker-labels.json", d / "speaker-edits.json", sc.VOICEPRINT):
        try:
            parts.append(str(int(p.stat().st_mtime * 1000)))
        except OSError:
            parts.append("0")
    return "-".join(parts)


_VP = {"mtime": None, "data": None}


def voiceprint():
    try:
        m = sc.VOICEPRINT.stat().st_mtime
    except OSError:
        return None
    if _VP["mtime"] != m:
        _VP["mtime"], _VP["data"] = m, sc.read_json(sc.VOICEPRINT)
        if _VP["data"]:
            _VP["data"]["vec"] = np.asarray(_VP["data"]["emb"], dtype=np.float32)
    return _VP["data"]


def raw_assign(turns, words):
    """Each word's group from the split alone: the turn overlapping it most, else the nearest within NEAR, else None."""
    if not turns:
        return [None] * len(words)
    starts = [t[0] for t in turns]
    maxend, m = [], -1e9
    for t in turns:
        m = max(m, t[1])
        maxend.append(m)
    out = []
    for ws, we, _ in words:
        j = bisect.bisect_right(starts, we) - 1
        best, bo, near, nd = None, 0.0, None, NEAR
        k = j
        while k >= 0 and maxend[k] > ws - NEAR:
            ts, te, key = turns[k]
            o = min(te, we) - max(ts, ws)
            if o > bo:
                best, bo = key, o
            elif o <= 0 and ws - te < nd and te <= ws:
                near, nd = key, ws - te
            k -= 1
        if best is None and j + 1 < len(turns) and turns[j + 1][0] - we < nd:
            near = turns[j + 1][2]
        out.append(best or near)
    # a word the split missed (a short gap in its turns) takes its neighbour's voice when it sits right beside it,
    # so a caption doesn't break or go white in the middle of a sentence
    for i, g in enumerate(out):
        if g is not None:
            continue
        prev = next((j for j in range(i - 1, -1, -1) if out[j] is not None), None)
        if prev is not None and words[i][0] - words[i - 1][1] <= FILL_GAP and all(
                words[j + 1][0] - words[j][1] <= FILL_GAP for j in range(prev, i)):
            out[i] = out[prev]
            continue
        nxt = next((j for j in range(i + 1, len(out)) if out[j] is not None), None)
        if nxt is not None and nxt - i <= 3 and all(words[j + 1][0] - words[j][1] <= FILL_GAP for j in range(i, nxt)):
            out[i] = out[nxt]
    return out


def _roots(groups, labels, edits):
    parent = {}
    for key, v in (labels.get("voices") or {}).items():
        t = v.get("same_as")
        if t and t != key and key in groups and t in groups:
            parent[key] = t
    for key, t in edits["merge"].items():
        if t is None or t == key:
            parent.pop(key, None)       # "not the same person": undo any merge, Claude's included
        else:
            parent[key] = t

    def root(k):
        seen = set()
        while k in parent and k not in seen:
            seen.add(k)
            k = parent[k]
        return k
    return root


def _label(r, sp, labels, edits, vp, local=True):
    """(who, gender, source, name, role) for a root voice key."""
    groups = sp["groups"]
    if r == "me":
        return "me", None, "you", "", ""
    fix = edits["groups"].get(r)
    cl = (labels.get("voices") or {}).get(r) or {}
    name, role = (cl.get("name") or "").strip(), cl.get("role") or ""
    if fix:
        return fix["who"], fix.get("gender"), "you", name, role
    if r in (labels.get("jonathan") or []):
        return "me", None, "claude", "", ""
    new = edits["new"].get(r)
    if new:
        return "other", new.get("gender"), "you", "", ""
    g = groups.get(r) or {}
    if cl:
        gender = cl.get("gender")
        if gender not in ("woman", "man"):
            gender = _pitch_gender(g.get("f0"))
        return "other", gender, "claude", name, role
    if not local:
        return None, None, None, "", ""
    # a guess only once Jonathan's voiceprint exists: without it he would be guessed by pitch too, and show up red
    if not vp or vp.get("model") != sp.get("model") or g.get("emb") is None or len(g["emb"]) != len(vp["vec"]):
        return None, None, "auto", "", ""
    if float(np.dot(vp["vec"], np.asarray(g["emb"], dtype=np.float32))) >= vp.get("thr", 0.9):
        return "me", None, "auto", "", ""
    return "other", _pitch_gender(g.get("f0")), "auto", "", ""


def _pitch_gender(f0):
    if not f0:
        return None
    return "woman" if f0 >= WOMAN_HZ else "man"


def cls_of(who, gender):
    if who == "me":
        return "me"
    return {"woman": "f", "man": "m"}.get(gender, "u")


def resolve(aid, words=None):
    """{"state", "rev", "spk": [voice index per word or -1], "raw": [group index per word or -1], "rawKeys",
    "speakers": [{key, cls, name, gender, role, sec, words, source, groups}]}"""
    vrev = voices_rev(aid)
    sp, labels, edits = load(aid)
    if words is None:
        words = load_words(aid)
    if not sp:
        return {"state": "none", "rev": None, "vrev": vrev, "spk": None, "raw": None, "rawKeys": [], "speakers": []}
    raw = raw_assign(sp["turns"], words)
    root = _roots(sp["groups"], labels, edits)
    vp = voiceprint()
    fixes = edits["words"]
    voices, spk, guessed = [], [], []
    info = {}
    for i, g in enumerate(raw):
        k = fixes.get(str(i), g)
        if k is None:
            spk.append(None)
            guessed.append(False)
            continue
        r = root(k)
        if r not in info:
            info[r] = _label(r, sp, labels, edits, vp)
        spk.append("me" if info[r][0] == "me" else r)
        guessed.append(info[r][2] == "auto" and str(i) not in fixes)
    # a scrap of a group Claude left out (a word or two the split cut off) takes the voice of the labeled words
    # around it rather than a pitch guess, so a red word can't land in the middle of Jonathan's blue sentence
    if labels:
        for i in range(len(spk)):
            if not guessed[i]:
                continue
            p = i - 1
            while p >= 0 and guessed[p] and words[p + 1][0] - words[p][1] <= FILL_GAP:
                p -= 1
            n = i + 1
            while n < len(spk) and guessed[n] and words[n][0] - words[n - 1][1] <= FILL_GAP:
                n += 1
            left = spk[p] if p >= 0 and not guessed[p] and all(
                words[j + 1][0] - words[j][1] <= FILL_GAP for j in range(p, i)) else None
            right = spk[n] if n < len(spk) and not guessed[n] and all(
                words[j + 1][0] - words[j][1] <= FILL_GAP for j in range(i, n)) else None
            if left is not None and (right is None or right == left):
                spk[i] = left
            elif right is not None and left is None:
                spk[i] = right
    keys_seen, order = {}, []
    for v in spk:
        if v is not None and v not in keys_seen:
            keys_seen[v] = len(order)
            order.append(v)
    # the voice list: Jonathan first, then in order of first word
    members = {}
    for g in sp["groups"]:
        r = root(g)
        v = "me" if (info.get(r) or _label(r, sp, labels, edits, vp))[0] == "me" else r
        members.setdefault(v, []).append(g)
    ordered = sorted(order, key=lambda v: (v != "me", keys_seen[v]))
    index = {v: i for i, v in enumerate(ordered)}
    counts = {}
    for v in spk:
        if v is not None:
            counts[v] = counts.get(v, 0) + 1
    n_plain, n_new = 0, 0
    for v in ordered:
        if v == "me":
            voices.append({"key": "me", "cls": "me", "name": "You", "gender": None, "role": "",
                           "sec": round(sum(sp["groups"][g]["sec"] for g in members.get("me", []) if g in sp["groups"]), 1),
                           "words": counts.get(v, 0), "source": _me_source(members.get("me", []), sp, labels, edits),
                           "groups": members.get("me", [])})
            continue
        who, gender, source, name, role = info[v]
        if not name:
            if role in ROLE_NAMES:
                name = ROLE_NAMES[role]
            elif str(v).startswith("N"):
                n_new += 1
                name = f"New voice {n_new}"
            else:
                n_plain += 1
                name = f"Voice {n_plain}"
        voices.append({"key": v, "cls": cls_of(who, gender), "name": name, "gender": gender, "role": role,
                       "sec": round(sum(sp["groups"][g]["sec"] for g in members.get(v, []) if g in sp["groups"]), 1),
                       "words": counts.get(v, 0), "source": source, "groups": members.get(v, [])})
    raw_keys = sorted({g for g in raw if g is not None}, key=lambda k: int(k[1:]))
    rk = {k: i for i, k in enumerate(raw_keys)}
    cls_of_voice = {v: voices[index[v]]["cls"] for v in ordered}
    sides = [None if v is None else ("me" if cls_of_voice[v] == "me" else ("them" if cls_of_voice[v] in ("f", "m") else None))
             for v in spk]
    return {"state": "ready", "rev": sp["rev"], "vrev": vrev,
            "spk": [index[v] if v is not None else -1 for v in spk],
            "raw": [rk[g] if g is not None else -1 for g in raw],
            "rawKeys": raw_keys, "speakers": voices, "runs": voice_runs(words, sides)}


def voice_runs(words, sides):
    """The recording split into stretches that are Jonathan's ("me") or the other side's ("them"): [[start, end, side]]
    in seconds, end to end with no gaps. A word with no side goes with the words before it. The cut between two
    stretches sits in the middle of the pause between their words. The voice tracks play these (2026-09-30)."""
    runs, cur, first, last = [], None, None, None
    for w, side in zip(words, sides):
        side = side or cur
        if side is None:
            continue
        if side != cur:
            if cur is not None:
                runs.append([first, last, cur])
            cur, first = side, w[0]
        last = w[1]
    if cur is not None:
        runs.append([first, last, cur])
    out = []
    for j, (s, e, side) in enumerate(runs):
        a = 0.0 if j == 0 else round((runs[j - 1][1] + s) / 2, 3)
        b = 1e9 if j == len(runs) - 1 else round((e + runs[j + 1][0]) / 2, 3)
        out.append([a, b, side])
    return out


def runs_for(aid):
    """voice_runs for a recording from its current labels, or None without voice data (the exporter's view)."""
    r = resolve(aid)
    return r["runs"] if r["state"] == "ready" else None


def gate(runs, side, s0, s1):
    """The stretches of [s0, s1) (source seconds) a voice track plays: those of its side. Without voice data "me"
    plays everything and "them" nothing, so nothing is lost before the voices are labeled."""
    if not runs:
        return [[s0, s1]] if side == "me" else []
    return [[max(a, s0), min(b, s1)] for a, b, sd in runs if sd == side and b > s0 and a < s1 and min(b, s1) > max(a, s0)]


def _me_source(groups, sp, labels, edits):
    srcs = set()
    for g in groups:
        if edits["groups"].get(g, {}).get("who") == "me" or edits["merge"].get(g) == "me":
            srcs.add("you")
        elif g in (labels.get("jonathan") or []):
            srcs.add("claude")
        else:
            srcs.add("auto")
    for s in ("you", "claude", "auto"):
        if s in srcs:
            return s
    return "auto"


def word_classes(aid, words=None):
    """Class per word id ("me", "f", "m", "u"), or None when the recording has no voice data."""
    r = resolve(aid, words)
    if r["state"] != "ready":
        return None
    cls = [s["cls"] for s in r["speakers"]]
    return [cls[i] if i >= 0 else "u" for i in r["spk"]]


# ------------------------------------------------------------------ writing labels and fixes

def write_labels(aid, jonathan, voices, model, rev=None):
    """Claude's answer (studio_moments.py) to speaker-labels.json. Unknown tags are dropped. rev: the split the
    request was built from; if the voices were split again meanwhile, the tags no longer match and nothing is saved."""
    sp = sc.read_json(asset_dir(aid) / "speakers.json")
    if not sp:
        raise RuntimeError("no voice split for this recording")
    if rev is not None and sp["rev"] != rev:
        raise RuntimeError("the voices were split again while Claude was reading; run it once more")
    keys = set(sp["groups"])
    tag = lambda t: str(t or "").strip().strip("[]").strip()  # noqa: E731
    jon = sorted({tag(t) for t in jonathan if tag(t) in keys}, key=lambda k: int(k[1:]))
    vs = {}
    for v in voices:
        k = tag(v.get("tag"))
        if k not in keys or k in jon:
            continue
        same = tag(v.get("same_as"))
        vs[k] = {"gender": v.get("gender") if v.get("gender") in ("woman", "man") else "unknown",
                 "name": (v.get("name") or "").strip()[:40], "role": v.get("role") or "other",
                 "same_as": same if same in keys and same != k else ""}
    out = {"v": 1, "rev": sp["rev"], "model": model, "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "jonathan": jon, "voices": vs}
    sc.write_json_atomic(asset_dir(aid) / "speaker-labels.json", out)
    rebuild_voiceprint()
    return out


_PATCH_LOCK = threading.Lock()


def apply_patch(aid, body):
    """Jonathan's fixes (PATCH /api/asset/<id>/speakers). Raises ValueError on a bad key or word id.
    The last action on a voice wins: labeling it detaches it from any "same person as" (Claude's included), and
    joining it to another voice drops its own label."""
    with _PATCH_LOCK:
        return _apply_patch(aid, body)


def _apply_patch(aid, body):
    sp, _, edits = load(aid)
    if not sp:
        raise ValueError("This recording has no voice data yet.")
    words = load_words(aid)
    groups = set(sp["groups"])
    g_body, m_body = body.get("groups") or {}, body.get("merge") or {}

    def voice_ok(k):
        return k == "me" or k in groups or k in edits["new"]

    for k, v in g_body.items():
        if k not in groups and k not in edits["new"]:
            raise ValueError(f"Unknown voice {k}.")
        if v is None:
            edits["groups"].pop(k, None)
            continue
        if v.get("who") == "me":
            edits["groups"][k] = {"who": "me"}
        elif v.get("who") == "other" and v.get("gender") in ("woman", "man"):
            edits["groups"][k] = {"who": "other", "gender": v["gender"]}
        else:
            raise ValueError("A voice is me, or a woman or a man.")
        if k not in m_body:
            edits["merge"][k] = k          # labeled on its own: no longer "the same person as" anyone
    for k, t in m_body.items():
        if k not in groups and k not in edits["new"]:
            raise ValueError(f"Unknown voice {k}.")
        if t is None:
            edits["merge"].pop(k, None)
        elif t == k or voice_ok(t):
            edits["merge"][k] = t
            if t != k and k not in g_body:
                edits["groups"].pop(k, None)   # joined to another voice: that voice's label now speaks for it
        else:
            raise ValueError(f"Unknown voice {t}.")
    for i, k in (body.get("words") or {}).items():
        i = int(i)
        if not 0 <= i < len(words):
            raise ValueError(f"No word {i}.")
        if k is None:
            edits["words"].pop(str(i), None)
        elif voice_ok(k):
            edits["words"][str(i)] = k
        else:
            raise ValueError(f"Unknown voice {k}.")
    nv = body.get("new_voice")
    if nv:
        if nv.get("gender") not in ("woman", "man"):
            raise ValueError("A new voice is a woman or a man.")
        n = 1 + max([int(k[1:]) for k in edits["new"]] or [0])
        key = f"N{n}"
        edits["new"][key] = {"gender": nv["gender"]}
        for i in nv.get("words") or []:
            i = int(i)
            if not 0 <= i < len(words):
                raise ValueError(f"No word {i}.")
            edits["words"][str(i)] = key
    edits["rev"] = sp["rev"]
    sc.write_json_atomic(asset_dir(aid) / "speaker-edits.json", edits)
    if g_body or m_body:                  # only whole-voice fixes can change who is Jonathan
        rebuild_voiceprint()
    return resolve(aid, words)


def rebuild_voiceprint():
    """Jonathan's voiceprint from every group Claude or he marked as him (seconds-weighted), with a match threshold
    set between his groups and the others'. Guesses never feed it."""
    me, other = [], []
    for d in sorted(sc.CACHE.glob("a_*")):
        sp, labels, edits = load(d.name)
        if not sp or sp.get("model") != MODEL_TAG:
            continue
        root = _roots(sp["groups"], labels, edits)
        for g, v in sp["groups"].items():
            if v.get("emb") is None:
                continue
            who = _label(root(g), sp, labels, edits, None, local=False)[0]
            if who == "me":
                me.append((np.asarray(v["emb"], np.float32), v["sec"]))
            elif who == "other":
                other.append((np.asarray(v["emb"], np.float32), v["sec"]))
    if not me:
        sc.VOICEPRINT.unlink(missing_ok=True)
        return None
    vec = sum(e * s for e, s in me)
    vec = vec / (np.linalg.norm(vec) + 1e-9)
    sm = [float(e @ vec) for e, _ in me]
    so = [float(e @ vec) for e, _ in other]
    thr = 0.9
    if len(sm) >= 3 and len(so) >= 3:
        lo, hi = float(np.percentile(sm, 10)), float(np.percentile(so, 95))
        thr = (lo + hi) / 2 if lo > hi else hi
    thr = max(0.5, min(0.97, thr))
    out = {"v": 1, "model": MODEL_TAG, "emb": [round(float(x), 5) for x in vec], "thr": round(thr, 4),
           "sec": round(sum(s for _, s in me), 1), "groups": len(me), "others": len(other),
           "me_p10": round(float(np.percentile(sm, 10)), 4) if sm else None,
           "other_p95": round(float(np.percentile(so, 95)), 4) if so else None,
           "updated": time.strftime("%Y-%m-%dT%H:%M:%S")}
    sc.write_json_atomic(sc.VOICEPRINT, out)
    return out


# ------------------------------------------------------------------ for Claude (studio_moments.py)

def voice_table(aid):
    """Lines "S3: 41 s, 118 Hz, voiceprint 0.82" for every group with speech, or [] without a split."""
    sp, _, _ = load(aid)
    if not sp:
        return []
    vp = voiceprint()
    rows = []
    for k, g in sorted(sp["groups"].items(), key=lambda kv: int(kv[0][1:])):
        if g["sec"] < 0.3:
            continue
        bits = [f"{g['sec']:.0f} s"]
        bits.append(f"{g['f0']:.0f} Hz" if g.get("f0") else "pitch unknown")
        if vp and g.get("emb") is not None and vp.get("model") == sp.get("model"):
            bits.append(f"voiceprint {float(vp['vec'] @ np.asarray(g['emb'], np.float32)):.2f}")
        rows.append(f"{k}: " + ", ".join(bits))
    return rows


def raw_tags(aid, words):
    """Each word's split group (before labels and fixes), for the inline tags Claude reads; None without a split."""
    sp, _, _ = load(aid)
    if not sp:
        return None
    return raw_assign(sp["turns"], words)


if __name__ == "__main__":
    main()
