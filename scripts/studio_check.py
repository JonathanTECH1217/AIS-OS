"""Monarc Studio install and feature check (2026-09-29).

  python scripts/studio_check.py               every check, OK / FAIL per line
  python scripts/studio_check.py --get-models  download Parakeet TDT 0.6B v2 int8 + Silero VAD, and the voice split's
                                               pyannote segmentation 3.0 + WeSpeaker ResNet34-LM, into ~/.monarc/models
  python scripts/studio_check.py --time-asr    transcribe 60 s of the newest inbox recording, print the speed
  python scripts/studio_check.py --time-proxy  encode 60 s of it to the 540x960 proxy (CPU, as prep does; QSV for comparison)

Never prints a key's value, only which source it came from.
"""
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_common as sc  # noqa: E402

RELEASE = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/"
PARAKEET_TAR = "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2"
PARAKEET_FILES = ("encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx", "tokens.txt")
# the voice split (2026-09-30); the release tag really is spelled "recongition"
SEG_URL = ("https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-segmentation-models/"
           "sherpa-onnx-pyannote-segmentation-3-0.tar.bz2")
EMB_URL = ("https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/"
           "wespeaker_en_voxceleb_resnet34_LM.onnx")
FAILS = []


def line(ok, name, detail=""):
    print(f"{'OK  ' if ok else 'FAIL'}  {name}{('  ' + detail) if detail else ''}")
    if not ok:
        FAILS.append(name)


def download(url, dest):
    tmp = dest.with_name(dest.name + ".part")
    with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        got, last = 0, 0
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
            if total and got - last > 50 << 20:
                last = got
                print(f"  {dest.name}: {got >> 20} / {total >> 20} MB", flush=True)
    tmp.replace(dest)
    return got


def get_models():
    sc.MODELS.mkdir(parents=True, exist_ok=True)
    if not sc.SILERO_VAD.exists():
        n = download(RELEASE + "silero_vad.onnx", sc.SILERO_VAD)
        print(f"silero_vad.onnx  {n / 1e6:.1f} MB")
    if not all((sc.PARAKEET_DIR / f).exists() for f in PARAKEET_FILES):
        tar = sc.MODELS / PARAKEET_TAR
        if not tar.exists():
            n = download(RELEASE + PARAKEET_TAR, tar)
            print(f"{PARAKEET_TAR}  {n / 1e6:.0f} MB")
        with tarfile.open(tar, "r:bz2") as t:
            t.extractall(sc.MODELS, filter="data")
        tar.unlink()
    for f in PARAKEET_FILES:
        p = sc.PARAKEET_DIR / f
        print(f"{p.name:22} {p.stat().st_size / 1e6:8.1f} MB")
    if not sc.SPK_SEG.exists():
        tar = sc.MODELS / SEG_URL.rsplit("/", 1)[1]
        if not tar.exists():
            download(SEG_URL, tar)
        with tarfile.open(tar, "r:bz2") as t:
            t.extractall(sc.MODELS, filter="data")
        tar.unlink()
    if not sc.SPK_EMB.exists():
        download(EMB_URL, sc.SPK_EMB)
    for p in (sc.SPK_SEG, sc.SPK_EMB):
        print(f"{p.name:22} {p.stat().st_size / 1e6:8.1f} MB")


def newest_recording():
    vids = [p for p in sc.INBOX.glob("*") if sc.kind_of(p) == "video"]
    return max(vids, key=lambda p: p.stat().st_mtime) if vids else None


def time_asr():
    import studio_transcribe as st
    src = newest_recording()
    if not src:
        sys.exit("no recording in media/inbox")
    start = 3600.0 if (sc.probe(src)["duration"] or 0) > 3700 else 0.0
    t0 = time.time()
    rec = st.load_recognizer()
    t1 = time.time()
    words, segs = st.transcribe_range(rec, src, start, 60.0)
    t2 = time.time()
    print(f"model load {t1 - t0:.1f} s; 60 s of audio in {t2 - t1:.1f} s "
          f"({60 / max(t2 - t1, 0.01):.1f}x real time); {len(words)} words in {len(segs)} segments")
    total = sc.probe(src)["duration"] or 0
    print(f"projected for the whole file ({total / 3600:.2f} h): {total / 60 * (t2 - t1) / 60:.0f} min")
    print("sample:", " ".join(w[2] for w in words[:60]))


def time_proxy():
    src = newest_recording()
    if not src:
        sys.exit("no recording in media/inbox")
    ff = sc.ffmpeg_exe()
    out = Path(tempfile.gettempdir()) / "studio_proxy_test.mp4"
    runs = {
        "qsv": [ff, "-y", "-hide_banner", "-loglevel", "error", "-ss", "3600", "-t", "60", "-hwaccel", "qsv",
                "-hwaccel_output_format", "qsv", "-i", str(src), "-vf", "scale_qsv=w=540:h=960", "-c:v", "h264_qsv",
                "-preset", "veryfast", "-global_quality", "30", "-g", "15", "-bf", "0", "-c:a", "aac", str(out)],
        "cpu": [ff, "-y", "-hide_banner", "-loglevel", "error", "-ss", "3600", "-t", "60", "-i", str(src),
                "-vf", "fps=30,scale=540:960", "-c:v", "libx264", "-preset", "ultrafast", "-tune", "fastdecode",
                "-crf", "30", "-g", "15", "-bf", "0", "-c:a", "aac", str(out)],
    }
    for name, args in runs.items():
        t0 = time.time()
        r = subprocess.run(args, capture_output=True, text=True, creationflags=sc.NO_WINDOW)
        dt = time.time() - t0
        print(f"{name}: {'ok' if r.returncode == 0 else 'failed'} {dt:.1f} s for 60 s -> "
              f"{(sc.probe(src)['duration'] or 0) / 60 * dt / 60:.0f} min for the whole file"
              + ("" if r.returncode == 0 else f"  {r.stderr.strip()[-200:]}"))
    out.unlink(missing_ok=True)


def checks():
    ff = sc.ffmpeg_exe()
    line(bool(ff), "ffmpeg", ff)
    filt = subprocess.run([ff, "-hide_banner", "-filters"], capture_output=True, text=True,
                          creationflags=sc.NO_WINDOW).stdout
    enc = subprocess.run([ff, "-hide_banner", "-encoders"], capture_output=True, text=True,
                         creationflags=sc.NO_WINDOW).stdout
    for f in ("ass", "loudnorm", "xfade", "sendcmd", "amix", "afade"):
        line(f" {f} " in filt, f"ffmpeg filter {f}")
    for e in ("libx264", "aac"):
        line(f" {e} " in enc, f"ffmpeg encoder {e}")
    font = sc.STUDIO_DIR / "fonts" / "Montserrat-Black.ttf"
    if font.exists():
        with tempfile.TemporaryDirectory() as td:
            ass = Path(td) / "t.ass"
            ass.write_text("[Script Info]\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\n"
                           "Format: Name, Fontname, Fontsize, PrimaryColour, Bold\nStyle: D,Montserrat Black,80,&H00FFFFFF,0\n\n"
                           "[Events]\nFormat: Layer, Start, End, Style, Text\nDialogue: 0,0:00:00.00,0:00:01.00,D,TEST\n",
                           encoding="utf-8")
            shutil.copy(font, Path(td) / font.name)
            r = subprocess.run([ff, "-hide_banner", "-loglevel", "verbose", "-f", "lavfi", "-i",
                                "color=black:s=1080x1920:d=0.1", "-vf", "ass=t.ass:fontsdir=.", "-f", "null", "-"],
                               capture_output=True, text=True, cwd=td, creationflags=sc.NO_WINDOW)
            picked = [l for l in r.stderr.splitlines() if "fontselect" in l]
            line(any("Montserrat" in l and "Black" in l for l in picked), "libass picks Montserrat Black",
                 (picked[-1].split("]")[-1].strip() if picked else "no fontselect line"))
    else:
        line(False, "Montserrat-Black.ttf", "run python scripts/studio_fonts.py")
    for mod in ("sherpa_onnx", "numpy", "PIL", "anthropic"):
        try:
            m = __import__(mod)
            line(True, f"import {mod}", getattr(m, "__version__", ""))
        except Exception as e:
            line(False, f"import {mod}", str(e))
    line(sc.SILERO_VAD.exists(), "model silero_vad.onnx", str(sc.SILERO_VAD))
    for f in PARAKEET_FILES:
        p = sc.PARAKEET_DIR / f
        line(p.exists(), f"model parakeet {f}", f"{p.stat().st_size / 1e6:.0f} MB" if p.exists() else "run --get-models")
    for name, p in (("voice split pyannote segmentation", sc.SPK_SEG), ("voice split ResNet34 voiceprints", sc.SPK_EMB)):
        line(p.exists(), f"model {name}", f"{p.stat().st_size / 1e6:.0f} MB" if p.exists() else "run --get-models")
    try:
        from outreach_common import load_env
        _, src = load_env()
        line("ANTHROPIC_API_KEY" in src, "ANTHROPIC_API_KEY", f"from {src.get('ANTHROPIC_API_KEY', 'nowhere')}")
    except Exception as e:
        line(False, "ANTHROPIC_API_KEY", str(e))
    free = shutil.disk_usage(sc.MEDIA).free / 1e9
    line(free > 15, "free disk", f"{free:.0f} GB")
    s = socket.socket()
    try:
        s.settimeout(0.5)
        busy = s.connect_ex(("127.0.0.1", 8780)) == 0
    finally:
        s.close()
    line(True, "port 8780", "in use (Studio running?)" if busy else "free")
    print(f"\n{'All checks passed.' if not FAILS else str(len(FAILS)) + ' failed: ' + ', '.join(FAILS)}")


if __name__ == "__main__":
    if "--get-models" in sys.argv:
        get_models()
    elif "--time-asr" in sys.argv:
        time_asr()
    elif "--time-proxy" in sys.argv:
        time_proxy()
    else:
        checks()
        sys.exit(1 if FAILS else 0)
