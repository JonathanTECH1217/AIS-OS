"""Word-timed transcript for Monarc Studio, on this laptop (2026-09-29).

Silero VAD cuts the audio into speech segments (at most 25 s, well under Parakeet's ~24 min attention limit), and
NVIDIA Parakeet TDT 0.6B v2 (int8, sherpa-onnx, CC-BY-4.0) writes each one with a start time per token. Tokens are
joined into words ("▁" starts a word; punctuation joins the word before it). Filler words are kept as written.

  python scripts/studio_transcribe.py <source> <asset_dir> --asset a_xxx [--resume]

Progress goes to stdout as JSON lines {"pos": seconds, "total": seconds}. Finished segments are appended to
<asset_dir>/transcript.partial.jsonl so --resume can pick up after a crash or restart. The result is
<asset_dir>/transcript.json:
  {"v":1,"asset","rev","model","duration","segments":[[start,end,first_word,last_word]],"words":[[start,end,"text"]]}
A word's id is its index in "words".
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_common as sc  # noqa: E402

SR = 16000
MODEL_NAME = "parakeet-tdt-0.6b-v2-int8"
PAD = 0.15          # seconds of audio kept either side of a VAD segment
BATCH = 8
WORD_TAIL = 0.6     # longest a last token is assumed to run when no duration is known
PUNCT = set(".,?!;:%)]}\"'")
# Parakeet hands back a number's first token without the word-start mark, so "get 15 minutes" came out "get15" (59 times
# in the first two recordings: "at5%", "press2", "December1st"). A number starts a word after two or more letters, or
# after "a"; a single letter keeps it ("C3 Electrical"), and so do these (lower case): Control4.
KEEP_JOINED = {"control"}


def number_starts_word(prev, core):
    """True when the token `core` (starting with a digit) is a new word after the word so far, `prev`."""
    return bool(core[:1].isdigit() and (re.fullmatch(r"[A-Za-z]{2,}", prev) or prev in ("a", "A"))
                and prev.lower() not in KEEP_JOINED)


def load_recognizer(threads=3):
    import sherpa_onnx
    d = sc.PARAKEET_DIR
    return sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=str(d / "encoder.int8.onnx"), decoder=str(d / "decoder.int8.onnx"),
        joiner=str(d / "joiner.int8.onnx"), tokens=str(d / "tokens.txt"),
        num_threads=threads, sample_rate=SR, feature_dim=80, decoding_method="greedy_search",
        model_type="nemo_transducer")


def load_vad():
    import sherpa_onnx
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = str(sc.SILERO_VAD)
    cfg.silero_vad.threshold = 0.5
    cfg.silero_vad.min_silence_duration = 0.35
    cfg.silero_vad.min_speech_duration = 0.25
    cfg.silero_vad.max_speech_duration = 25
    cfg.sample_rate = SR
    return sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=120), cfg.silero_vad.window_size


def pcm(src, start=0.0, dur=None):
    """Yield float32 mono 16 kHz chunks from ffmpeg (no WAV on disk)."""
    args = [sc.ffmpeg_exe(), "-hide_banner", "-loglevel", "error"]
    if start:
        args += ["-ss", f"{start:.3f}"]
    args += ["-i", str(src)]
    if dur:
        args += ["-t", f"{dur:.3f}"]
    args += ["-vn", "-af", "highpass=f=80", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                            creationflags=sc.NO_WINDOW | sc.BELOW_NORMAL)
    try:
        while True:
            raw = proc.stdout.read(SR * 4 * 2)  # 2 s per read
            if not raw:
                break
            n = len(raw) // 4 * 4
            yield np.frombuffer(raw[:n], dtype=np.float32)
    finally:
        proc.kill()
        proc.wait()


def speech_segments(chunks, offset=0.0):
    """VAD over a chunk stream. Yields (abs_start_seconds, samples) with PAD seconds of context either side."""
    vad, win = load_vad()
    ring = np.zeros(0, dtype=np.float32)
    ring_start = 0          # absolute sample index of ring[0], relative to offset
    fed = 0                 # samples fed to the VAD so far
    pad = int(PAD * SR)
    pending = np.zeros(0, dtype=np.float32)

    def cut(seg_start, n):
        a = max(seg_start - pad, ring_start)
        b = min(seg_start + n + pad, ring_start + len(ring))
        return a, ring[a - ring_start:b - ring_start].copy()

    def drain():
        while not vad.empty():
            seg = vad.front
            a, samples = cut(seg.start, len(seg.samples))
            vad.pop()
            yield offset + a / SR, samples

    for chunk in chunks:
        ring = np.concatenate([ring, chunk])
        pending = np.concatenate([pending, chunk])
        while len(pending) >= win:
            vad.accept_waveform(pending[:win])
            pending = pending[win:]
            fed += win
        yield from drain()
        keep = 90 * SR       # VAD segments are at most 25 s, so 90 s of history is plenty
        if len(ring) > keep:
            drop = len(ring) - keep
            ring = ring[drop:]
            ring_start += drop
    if len(pending):
        vad.accept_waveform(pending)
    vad.flush()
    yield from drain()


def tokens_to_words(tokens, times, durations, seg_start, seg_end):
    """Join sub-word tokens into [start, end, text] words, times absolute."""
    words = []
    cur = None
    for i, tok in enumerate(tokens):
        t = seg_start + float(times[i])
        dur = float(durations[i]) if durations is not None and i < len(durations) else None
        text = tok.replace("▁", " ")       # sherpa-onnx hands tokens back with a leading space, not the marker
        core = text.strip()
        if not core:
            continue
        is_punct = all(c in PUNCT for c in core)
        starts_word = (text[:1] == " " and not is_punct) or (cur is not None and number_starts_word(cur["text"], core))
        if cur is not None and not starts_word:
            cur["text"] += core
            cur["last"] = t
            cur["last_dur"] = dur
            continue
        if cur:
            words.append(cur)
        cur = {"start": t, "last": t, "last_dur": dur, "text": core}
    if cur:
        words.append(cur)
    out = []
    for i, w in enumerate(words):
        nxt = words[i + 1]["start"] if i + 1 < len(words) else seg_end
        if w["last_dur"]:
            end = w["last"] + w["last_dur"]
        else:
            end = w["last"] + WORD_TAIL
        end = max(w["start"] + 0.04, min(end, nxt, seg_end))
        if w["text"]:
            out.append([round(w["start"], 3), round(end, 3), w["text"]])
    return out


def decode_batch(rec, batch):
    streams = []
    for start, samples in batch:
        s = rec.create_stream()
        s.accept_waveform(SR, samples)
        streams.append(s)
    rec.decode_streams(streams)
    results = []
    for (start, samples), s in zip(batch, streams):
        r = s.result
        durs = getattr(r, "durations", None)
        durs = list(durs) if durs is not None and len(durs) else None
        end = start + len(samples) / SR
        words = tokens_to_words(list(r.tokens), list(r.timestamps), durs, start, end)
        results.append({"seg": [round(start, 3), round(end, 3)], "words": words})
    return results


def transcribe_range(rec, src, start, dur):
    """Used by studio_check --time-asr. Returns (words, segments) for one stretch of the file."""
    words, segs, batch = [], [], []
    for seg in speech_segments(pcm(src, start, dur), offset=start):
        batch.append(seg)
        if len(batch) == BATCH:
            for r in decode_batch(rec, batch):
                segs.append(r["seg"])
                words += r["words"]
            batch = []
    if batch:
        for r in decode_batch(rec, batch):
            segs.append(r["seg"])
            words += r["words"]
    return words, segs


def assemble(parts, asset, duration):
    parts = sorted(parts, key=lambda p: p["seg"][0])
    words, segments, last_end = [], [], -1.0
    for p in parts:
        if p["seg"][0] < last_end - 0.5:   # a resume can repeat a segment; keep the first copy
            continue
        w0 = len(words)
        for w in p["words"]:
            if words and w[0] < words[-1][0]:
                continue
            words.append(w)
        if len(words) > w0:
            segments.append([p["seg"][0], p["seg"][1], w0, len(words) - 1])
        last_end = p["seg"][1]
    rev = hashlib.sha1(json.dumps(words, separators=(",", ":")).encode()).hexdigest()[:16]
    return {"v": 1, "asset": asset, "rev": rev, "model": MODEL_NAME, "duration": duration,
            "segments": segments, "words": words}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("asset_dir")
    ap.add_argument("--asset", required=True)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--threads", type=int, default=3)
    a = ap.parse_args()
    src, out = Path(a.source), Path(a.asset_dir)
    out.mkdir(parents=True, exist_ok=True)
    partial = out / "transcript.partial.jsonl"
    duration = sc.probe(src)["duration"] or 0.0
    parts, resume_from = [], 0.0
    if a.resume and partial.exists():
        for ln in partial.read_text(encoding="utf-8").splitlines():
            try:
                parts.append(json.loads(ln))
            except ValueError:
                pass
        if parts:
            resume_from = max(p["seg"][1] for p in parts)
    elif partial.exists():
        partial.unlink()
    rec = load_recognizer(a.threads)
    start = max(0.0, resume_from - 1.0) if resume_from else 0.0
    batch = []
    with open(partial, "a", encoding="utf-8") as pf:
        def flush():
            for r in decode_batch(rec, batch):
                if r["seg"][1] <= resume_from:
                    continue
                parts.append(r)
                pf.write(json.dumps(r) + "\n")
            pf.flush()
            print(json.dumps({"pos": round(batch[-1][0], 1), "total": round(duration, 1)}), flush=True)
            batch.clear()

        for seg in speech_segments(pcm(src, start), offset=start):
            if seg[0] + len(seg[1]) / SR <= resume_from:
                continue
            batch.append(seg)
            if len(batch) == BATCH:
                flush()
        if batch:
            flush()
    result = assemble(parts, a.asset, duration)
    sc.write_json_atomic(out / "transcript.json", result)
    partial.unlink(missing_ok=True)
    print(json.dumps({"pos": round(duration, 1), "total": round(duration, 1), "done": True,
                      "words": len(result["words"])}), flush=True)


if __name__ == "__main__":
    main()
