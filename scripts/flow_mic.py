"""Microphone and the take for Monarc Flow (2026-10-03).

The mic opens when the hold starts and closes when it ends, so the Windows mic light is on only while he talks. Same
chain as Monarc Calls (scripts/calls_mic.py): pyaudiowpatch over WASAPI, mixed to one channel, resampled to 16 kHz
with soxr. Each chunk's loudness goes to the pill's bars.

write() turns a take into words. A take of up to one_go seconds (15) is written in one go once he lets go, the most
accurate way. A longer one (hands-free) is cut at pauses of pause seconds (0.8) or more once a piece is min_piece
seconds (6) long; each piece is written while he is still talking, so only the last piece is left at the end. The
voice finder (Silero, as in studio_transcribe.load_vad) also tells a take with no speech in it: nothing is written.

FLOW_FAKE_MIC=<16 kHz wav> plays that clip instead of the mic, from its start on each take, then silence (tests);
FLOW_FAKE_SPEED=4 plays it 4 times as fast.
"""
import os
import threading
import time
import wave

import numpy as np

import studio_common as sc

SR = 16000


class Take:
    """The audio of one hold, added to by the mic's thread and read by write()."""

    def __init__(self):
        self.parts = []
        self.n = 0
        self.lock = threading.Lock()
        self.more = threading.Event()
        self.live = True
        self.locked = False
        self.cancelled = False
        self.t_start = time.time()
        self.t_stop = None
        self.peak = 0.0             # loudest chunk: near zero means the mic itself is silent (muted, plug half out)
        self.focus = None           # the look at where the cursor is, started when he lets go (flow_focus)

    def hear(self, rms):
        if rms > self.peak:
            self.peak = rms

    def add(self, x):
        with self.lock:
            self.parts.append(x)
            self.n += len(x)
        self.more.set()

    def end(self):
        self.t_stop = self.t_stop or time.time()
        self.live = False
        self.more.set()

    def audio(self, a=0, b=None):
        with self.lock:
            if len(self.parts) > 1:
                self.parts = [np.concatenate(self.parts)]
            x = self.parts[0] if self.parts else np.zeros(0, np.float32)
        return x[a:b]

    @property
    def seconds(self):
        return self.n / SR


def make_vad(pause):
    import sherpa_onnx
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = str(sc.SILERO_VAD)
    cfg.silero_vad.threshold = 0.5
    cfg.silero_vad.min_silence_duration = pause
    cfg.silero_vad.min_speech_duration = 0.2
    cfg.silero_vad.max_speech_duration = 25
    cfg.sample_rate = SR
    return sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=120), cfg.silero_vad.window_size


def write(take, decode, one_go=15.0, pause=0.8, min_piece=6.0):
    """(words, heard): what Parakeet wrote for the take, and whether any speech was found in it at all.
    decode(samples) -> text. Returns once the take has ended (take.end()) and its last piece is written."""
    vad, win = make_vad(pause)
    fed, cut, heard, texts = 0, 0, False, []

    def drain(n, final=False):
        nonlocal cut, heard
        while not vad.empty():
            seg = vad.front
            end = seg.start + len(seg.samples)
            vad.pop()
            heard = True
            if not final and n >= one_go * SR and end - cut >= min_piece * SR:
                at = min(end + int(0.4 * SR), n)         # halfway into the pause
                texts.append(decode(take.audio(cut, at)))
                cut = at

    while True:
        take.more.wait(0.25)
        take.more.clear()
        live = take.live
        if take.cancelled:
            return "", False
        n = take.n
        new = take.audio(fed, n)
        k = len(new) // win * win
        for i in range(0, k, win):
            vad.accept_waveform(new[i:i + win])
        fed += k
        drain(n)
        if not live:
            break
    rest = take.audio(fed)
    if len(rest):
        vad.accept_waveform(rest)
    vad.flush()
    drain(take.n, final=True)
    if heard and take.n - cut > 0.1 * SR and not take.cancelled:
        texts.append(decode(take.audio(cut)))
    return " ".join(t for t in texts if t).strip(), heard


class Mic:
    """The Windows default microphone, or the one named in config ("mic")."""

    def __init__(self, name=""):
        self.name = name
        self.lock = threading.Lock()
        self._pa = None
        self.stream = None
        self.rs = None
        self.take = None
        self.refresh()

    def refresh(self):
        """A fresh PyAudio sees mics plugged in or pulled since; run after each take and when a mic won't open.
        The old one is shut first: PortAudio counts its starts and only looks for mics again on a start from zero,
        so a second PyAudio made while the first is open still has the old list (his headset, 2026-10-03)."""
        import pyaudiowpatch as pa
        with self.lock:
            if self.stream:                     # a take is using the current one
                return
            if self._pa:
                self._pa.terminate()
                self._pa = None
            self._pa = pa.PyAudio()

    def _inputs(self, p):
        import pyaudiowpatch as pa
        wasapi = p.get_host_api_info_by_type(pa.paWASAPI)
        out = []
        for i in range(p.get_device_count()):
            d = p.get_device_info_by_index(i)
            if (d.get("hostApi") == wasapi["index"] and int(d.get("maxInputChannels") or 0) > 0
                    and not d.get("isLoopbackDevice")):
                out.append(d)
        return out, wasapi["defaultInputDevice"]

    def devices(self):
        with self.lock:
            try:
                return [d["name"] for d in self._inputs(self._pa)[0]]
            except Exception:  # noqa: BLE001
                return []

    def _device(self, p):
        inputs, default = self._inputs(p)
        for d in inputs:
            if self.name and d["name"] == self.name:
                return d
        for d in inputs:
            if d["index"] == default:
                return d
        raise RuntimeError("No microphone")

    def start(self, take, on_level):
        """Open the mic into take. Returns the mic's name; RuntimeError when there is none."""
        import pyaudiowpatch as pa
        import soxr
        with self.lock:
            p = self._pa
            dev = self._device(p)
            rate = int(dev["defaultSampleRate"])
            ch = max(1, min(2, int(dev["maxInputChannels"])))
            rs = soxr.ResampleStream(rate, SR, 1, dtype="float32")

            def cb(data, frames, info, status):
                x = np.frombuffer(data, dtype=np.float32)
                if ch > 1:
                    x = x.reshape(-1, ch).mean(axis=1)
                if len(x):
                    on_level(float(np.sqrt(np.mean(x * x))))
                    y = rs.resample_chunk(x)
                    if len(y):
                        take.add(y.astype(np.float32))
                return (None, pa.paContinue)

            self.stream = p.open(format=pa.paFloat32, channels=ch, rate=rate, input=True,
                                 input_device_index=dev["index"], frames_per_buffer=max(256, rate // 40),
                                 stream_callback=cb)
            self.rs, self.take = rs, take
            self.stream.start_stream()
            return dev["name"]

    def stop(self):
        with self.lock:
            stream, rs, take = self.stream, self.rs, self.take
            self.stream = self.rs = self.take = None
        if stream:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:  # noqa: BLE001
                pass
            tail = rs.resample_chunk(np.zeros(0, np.float32), last=True)
            if len(tail):
                take.add(tail.astype(np.float32))
        threading.Thread(target=self._refresh_quietly, daemon=True).start()

    def _refresh_quietly(self):
        try:
            self.refresh()
        except Exception:  # noqa: BLE001
            pass


def read_wav(path):
    with wave.open(str(path)) as f:
        if f.getframerate() != SR or f.getsampwidth() != 2:
            raise ValueError(f"{path}: needs 16 kHz, 16-bit")
        x = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        if f.getnchannels() > 1:
            x = x.reshape(-1, f.getnchannels()).mean(axis=1)
    return x


class FakeMic:
    """Plays a clip instead of the mic (tests): from its start on each take, then silence."""

    def __init__(self, path, speed=1.0):
        self.audio = read_wav(path)
        self.speed = speed
        self._stop = None
        self._thread = None

    def devices(self):
        return ["Test clip"]

    def refresh(self):
        pass

    def start(self, take, on_level):
        stop = self._stop = threading.Event()
        step = int(SR * 0.025)

        def play():
            pos = 0
            while not stop.is_set():
                x = self.audio[pos:pos + step]
                if len(x) < step:
                    x = np.concatenate([x, np.zeros(step - len(x), np.float32)])
                pos += step
                on_level(float(np.sqrt(np.mean(x * x))))
                take.add(x)
                time.sleep(0.025 / self.speed)

        self._thread = threading.Thread(target=play, daemon=True, name="flow-fake-mic")
        self._thread.start()
        return "Test clip"

    def stop(self):
        if self._stop:
            self._stop.set()
            self._thread.join()
            self._stop = None


def make_mic(name=""):
    fake = os.environ.get("FLOW_FAKE_MIC")
    if fake:
        return FakeMic(fake, float(os.environ.get("FLOW_FAKE_SPEED") or 1))
    return Mic(name)
