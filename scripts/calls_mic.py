"""Live words from the Windows default microphone, for Monarc Calls (2026-10-03, brainstorms/2026-10-01-live-call-notes.md).

Started by the session (scripts/studio_session.py) as a child process at below-normal priority. It opens whatever
microphone Windows is using as its default input (WASAPI, through pyaudiowpatch), mixes to mono, resamples to 16 kHz
(soxr) and runs the same speech model Studio uses on recordings: Silero VAD cuts the stream into stretches of speech
(studio_transcribe.speech_segments), Parakeet writes each one with word times (decode_batch). A stretch arrives a
second or two after it ends. Nothing is recorded: the audio is dropped once its words are out.

stdout, one JSON object per line:
  {"type": "ready", "device": "Microphone (HD Pro Webcam C920)", "rate": 48000}
  {"type": "level", "speech": true}                 on a change, for the window's dot (at most 4 a second)
  {"type": "seg", "start": 1759500000.12, "end": ..., "words": [[start, end, "text"], ...]}   wall-clock seconds
  {"type": "error", "error": "..."}
stdin: "pause", "resume", "quit"; with --fake also "say <text>" (speaks that line now).

  python scripts/calls_mic.py --check        the device, then 10 s of your words
  python scripts/calls_mic.py --fake         no mic, no model: lines come from "say" commands (STUDIO_FAKE_MIC)
"""
import json
import queue
import sys
import threading
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import studio_transcribe as stt  # noqa: E402

SR = stt.SR
LEVEL_ON = 0.012          # chunk loudness (RMS) above this counts as someone talking, for the dot only
_out_lock = threading.Lock()


def emit(obj):
    with _out_lock:
        sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
        sys.stdout.flush()


class Control:
    """pause / resume / quit from stdin (and say, in fake mode)."""

    def __init__(self):
        self.listening = threading.Event()
        self.listening.set()
        self.quit = threading.Event()
        self.said = queue.Queue()

    def read_stdin(self):
        for raw in sys.stdin:
            cmd = raw.strip()
            if cmd == "pause":
                self.listening.clear()
            elif cmd == "resume":
                self.listening.set()
            elif cmd.startswith("say "):
                self.said.put(cmd[4:])
            elif cmd == "quit":
                break
        self.quit.set()
        self.listening.set()


NO_MIC = ("No microphone: Windows has no default input right now. Plug in the mic (the C920 webcam), or pick one in "
          "Settings, System, Sound, Input.")


def default_device():
    import pyaudiowpatch as pa
    p = pa.PyAudio()
    try:
        w = p.get_host_api_info_by_type(pa.paWASAPI)
        if w["defaultInputDevice"] < 0:
            raise RuntimeError(NO_MIC)
        dev = p.get_device_info_by_index(w["defaultInputDevice"])
        if dev.get("isLoopbackDevice") or int(dev.get("maxInputChannels") or 0) < 1:
            raise RuntimeError(NO_MIC)
        return p, dev
    except Exception:
        p.terminate()
        raise


def device_name():
    """The default microphone's name, or None (for the start panel's check line). Never opens it."""
    try:
        p, dev = default_device()
        p.terminate()
        return dev["name"]
    except Exception:  # noqa: BLE001
        return None


def mic_chunks(ctl, dev, p, level):
    """16 kHz mono float32 chunks until a pause or quit; also the wall time of the first sample."""
    import pyaudiowpatch as pa
    import soxr
    rate = int(dev["defaultSampleRate"])
    ch = max(1, min(2, int(dev["maxInputChannels"])))
    q = queue.Queue()

    def cb(in_data, frame_count, time_info, status):
        q.put(in_data)
        return (None, pa.paContinue)

    stream = p.open(format=pa.paFloat32, channels=ch, rate=rate, input=True, input_device_index=dev["index"],
                    frames_per_buffer=rate // 10, stream_callback=cb)
    rs = soxr.ResampleStream(rate, SR, 1, dtype="float32")
    first = {"t": None}
    stream.start_stream()

    def gen():
        try:
            while ctl.listening.is_set() and not ctl.quit.is_set():
                try:
                    raw = q.get(timeout=0.5)
                except queue.Empty:
                    continue
                if first["t"] is None:
                    first["t"] = time.time() - 0.1        # the buffer just handed over held ~0.1 s
                x = np.frombuffer(raw, dtype=np.float32)
                if ch > 1:
                    x = x.reshape(-1, ch).mean(axis=1)
                level(float(np.sqrt(np.mean(x * x))) if len(x) else 0.0)
                y = rs.resample_chunk(x)
                if len(y):
                    yield y.astype(np.float32)
        finally:
            stream.stop_stream()
            stream.close()
    return gen(), first


class Level:
    def __init__(self):
        self.on = False
        self.last = 0.0
        self.quiet_since = 0.0

    def __call__(self, rms):
        now = time.time()
        if rms >= LEVEL_ON:
            self.quiet_since = 0.0
            if not self.on and now - self.last >= 0.25:
                self.on, self.last = True, now
                emit({"type": "level", "speech": True})
        else:
            self.quiet_since = self.quiet_since or now
            if self.on and now - self.quiet_since >= 0.5:
                self.on, self.last = False, now
                emit({"type": "level", "speech": False})


def run_live(ctl, check_seconds=None):
    p, dev = default_device()
    emit({"type": "ready", "device": dev["name"], "rate": int(dev["defaultSampleRate"])})
    rec = stt.load_recognizer(threads=2)
    level = Level()
    t_end = time.time() + check_seconds if check_seconds else None
    try:
        while not ctl.quit.is_set():
            ctl.listening.wait()
            if ctl.quit.is_set():
                break
            chunks, first = mic_chunks(ctl, dev, p, level)
            # speech_segments counts seconds from the first chunk; adding the first sample's wall time makes them
            # wall-clock seconds, the clock Airtable's "Status changed" is compared with
            for start, samples in stt.speech_segments(chunks, offset=0.0):
                base = first["t"] or time.time()
                for r in stt.decode_batch(rec, [(start, samples)]):
                    if r["words"]:
                        emit({"type": "seg", "start": round(base + r["seg"][0], 3), "end": round(base + r["seg"][1], 3),
                              "words": [[round(base + w[0], 3), round(base + w[1], 3), w[2]] for w in r["words"]]})
                if t_end and time.time() > t_end:
                    ctl.quit.set()
                    break
            if level.on:
                level.on = False
                emit({"type": "level", "speech": False})
    finally:
        p.terminate()


def run_fake(ctl):
    """Tests: each "say <text>" is a line heard now, its words spread over 0.35 s each."""
    emit({"type": "ready", "device": "Test microphone", "rate": 16000})
    while not ctl.quit.is_set():
        try:
            text = ctl.said.get(timeout=0.2)
        except queue.Empty:
            continue
        if not ctl.listening.is_set():
            continue                                    # paused: nothing is heard
        t0 = time.time()
        words = [[round(t0 + i * 0.35, 3), round(t0 + i * 0.35 + 0.3, 3), w] for i, w in enumerate(text.split())]
        if words:
            emit({"type": "level", "speech": True})
            emit({"type": "seg", "start": words[0][0], "end": words[-1][1], "words": words})
            emit({"type": "level", "speech": False})


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    ctl = Control()
    if "--check" in sys.argv:
        print("Listening for 10 s on the Windows default microphone. Say something.", file=sys.stderr)
        try:
            run_live(ctl, check_seconds=10)
        except RuntimeError as e:
            print(e, file=sys.stderr)
            sys.exit(2)
        return
    threading.Thread(target=ctl.read_stdin, daemon=True).start()
    try:
        if "--fake" in sys.argv:
            run_fake(ctl)
        else:
            run_live(ctl)
    except RuntimeError as e:          # said in plain words (no microphone)
        emit({"type": "error", "error": str(e)[:400]})
        sys.exit(2)
    except Exception as e:  # noqa: BLE001
        emit({"type": "error", "error": f"{type(e).__name__}: {e}"[:400]})
        raise


if __name__ == "__main__":
    main()
