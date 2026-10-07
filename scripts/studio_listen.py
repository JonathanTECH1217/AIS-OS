"""The second listen for Generate captions (Monarc Studio, 2026-10-02; brainstorms/2026-10-02-captions-after-trim.md).

The first transcript (studio_transcribe.py) puts a voice detector in front of Parakeet, so it hears the recording in
short pieces and drops quiet far-side words. This listens again to just the parts a short keeps: Parakeet on 20 s
windows every 15 s, no voice detector, so it hears whole sentences. Each window keeps its middle (the next window
has its tail); a word heard twice at the same time is kept once. Measured on call c23 of the Sep 30 recording (5:23):
+156 words, and where the two listens differ the second was right most of the time.

  python scripts/studio_listen.py <asset-id> --ranges 12.5:40.0,61.0:75.5 --out <file.json>

Progress goes to stdout as JSON lines {"pos": seconds done, "total": seconds}. The result:
  {"words": [[start, end, "text"]], "ranges": [[s, e]], "model", "seconds"}
STUDIO_FAKE_LISTEN (tests): no model; the words come from listen-fake.json in the recording's cache folder.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_common as sc  # noqa: E402

WIN, HOP = 20.0, 15.0       # seconds per window and between window starts
EDGE = 2.5                  # seconds trimmed from each inner side of a window (its neighbour hears them mid-window)


def parse_ranges(text):
    out = []
    for part in (text or "").split(","):
        if ":" not in part:
            continue
        a, b = part.split(":", 1)
        s, e = float(a), float(b)
        if e > s >= 0:
            out.append([s, e])
    return sorted(out)


def samples(src, s0, s1):
    """float32 mono 16 kHz samples of [s0, s1) of the file (the same filter the first transcript uses)."""
    import numpy as np
    import studio_transcribe as st
    args = [sc.ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-ss", f"{s0:.3f}", "-i", str(src),
            "-t", f"{s1 - s0:.3f}", "-vn", "-af", "highpass=f=80", "-ac", "1", "-ar", str(st.SR), "-f", "f32le", "-"]
    raw = subprocess.run(args, capture_output=True, creationflags=sc.NO_WINDOW | sc.BELOW_NORMAL).stdout
    return np.frombuffer(raw[:len(raw) // 4 * 4], dtype=np.float32)


def listen(rec, src, s0, s1):
    """Words of [s0, s1) from overlapping windows, each window's middle kept, repeats dropped."""
    import studio_transcribe as st
    x = samples(src, s0, s1)
    total = len(x) / st.SR
    batch, got, k = [], [], 0.0
    while k < total:
        batch.append((s0 + k, x[int(k * st.SR):int(min(len(x), (k + WIN) * st.SR))].copy()))
        if k + WIN >= total:
            break
        k += HOP
    for i in range(0, len(batch), st.BATCH):
        for r in st.decode_batch(rec, batch[i:i + st.BATCH]):
            ws, we = r["seg"]
            lo = ws + (EDGE if ws > s0 + 0.01 else 0)
            hi = we - (EDGE if we < s0 + total - 0.01 else 0)
            got += [w for w in r["words"] if lo <= (w[0] + w[1]) / 2 < hi]
    got.sort()
    out = []
    for w in got:
        if out and abs(w[0] - out[-1][0]) < 0.08 and w[2].lower() == out[-1][2].lower():
            continue
        out.append(w)
    return out


def fake_words(aid, ranges):
    data = sc.read_json(sc.CACHE / aid / "listen-fake.json", {}) or {}
    return [w for w in data.get("words", []) if any(s <= (w[0] + w[1]) / 2 < e for s, e in ranges)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("asset")
    ap.add_argument("--ranges", required=True, help="s:e,s:e in source seconds")
    ap.add_argument("--out", required=True)
    ap.add_argument("--threads", type=int, default=3)
    a = ap.parse_args()
    ranges = parse_ranges(a.ranges)
    total = round(sum(e - s for s, e in ranges), 1)
    t0 = time.time()
    if os.environ.get("STUDIO_FAKE_LISTEN"):
        words, model = fake_words(a.asset, ranges), "fake"
        time.sleep(0.3)
    else:
        import studio_prep as prep
        import studio_transcribe as st
        meta = sc.read_json(sc.CACHE / a.asset / "meta.json")
        if not meta:
            raise SystemExit("no such recording")
        src = prep.orig_path(a.asset, meta)
        rec = st.load_recognizer(a.threads)
        words, done, model = [], 0.0, st.MODEL_NAME
        print(json.dumps({"pos": 0, "total": total}), flush=True)
        for s, e in ranges:
            words += listen(rec, src, s, e)
            done += e - s
            print(json.dumps({"pos": round(done, 1), "total": total}), flush=True)
    sc.write_json_atomic(Path(a.out), {"words": words, "ranges": ranges, "model": model,
                                       "seconds": round(time.time() - t0, 1)})
    print(json.dumps({"pos": total, "total": total, "done": True, "words": len(words)}), flush=True)


if __name__ == "__main__":
    main()
