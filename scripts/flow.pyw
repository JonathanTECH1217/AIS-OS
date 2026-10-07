"""Monarc Flow (2026-10-03): hold Ctrl+Win, talk, let go, and the words land wherever the cursor is. Runs on this
laptop only: Parakeet writes the words (scripts/studio_transcribe.py), fixed rules clean them (scripts/flow_clean.py),
and nothing leaves the machine. Guide: references/flow.md.

  pythonw scripts/flow.pyw             start it (the Desktop and Startup shortcuts run this); a second copy only
                                       flashes "Ready" on the pill of the one already running
  python scripts/flow.pyw --install    icon, sounds, the Desktop shortcut "Monarc Flow" and the Startup shortcut, then start
  python scripts/flow.pyw --check      the mic's name, then the test clip written and timed
  pythonw scripts/flow.pyw --restart   stop the running copy and start a fresh one (the AIOS runs this after an edit)
  pythonw scripts/flow.pyw --quit      stop it

Pieces: flow_keys.py (the Ctrl+Win hold), flow_mic.py (mic and the take), flow_clean.py (the rules), flow_paste.py
(clipboard and Ctrl+V), flow_pill.py (the pill). Settings: projects/flow/config.json. Word fixes:
projects/flow/words.json. History: ~/.monarc/flow-history.jsonl (the last 1,000 takes). Log: ~/.monarc/flow.log.

For tests: FLOW_INSTANCE (another name, so a test copy can run), FLOW_CONFIG, FLOW_HISTORY, FLOW_LOG, FLOW_FAKE_MIC
(a WAV instead of the mic), FLOW_FAKE_SPEED, FLOW_NO_SOUND.
"""
import ctypes
import ctypes.wintypes as w
import json
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
FLOW = ROOT / "projects" / "flow"
HOME = Path.home() / ".monarc"
INSTANCE = os.environ.get("FLOW_INSTANCE") or "MonarcFlow"
CONFIG = Path(os.environ.get("FLOW_CONFIG") or FLOW / "config.json")
HISTORY = Path(os.environ.get("FLOW_HISTORY") or HOME / "flow-history.jsonl")
LOG = Path(os.environ.get("FLOW_LOG") or HOME / "flow.log")
WORDS = FLOW / "words.json"
ICO = FLOW / "flow.ico"
PNG = FLOW / "flow.png"
SOUNDS = FLOW / "sounds"
TEST_CLIP = HOME / "models" / "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8" / "test_wavs" / "0.wav"
HISTORY_KEEP = 1000
SILENT = 0.003        # a take whose loudest moment is under this: the mic sends nothing (2026-10-03: his headset
                      # read 0.0008 at most when it stopped, 0.026 while it worked)
DEFAULTS = {"mic": "", "sounds": True, "space_after": True, "min_hold_seconds": 0.3, "tail_ms": 200,
            "restore_clipboard_ms": 400, "one_go_seconds": 15, "pause_cut_seconds": 0.8, "min_piece_seconds": 6,
            "max_take_minutes": 10, "threads": 4}
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
log = logging.getLogger("flow")

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.CreateMutexW.argtypes = (w.LPVOID, w.BOOL, w.LPCWSTR)
k32.CreateMutexW.restype = w.HANDLE
k32.OpenMutexW.argtypes = (w.DWORD, w.BOOL, w.LPCWSTR)
k32.OpenMutexW.restype = w.HANDLE
k32.CreateEventW.argtypes = (w.LPVOID, w.BOOL, w.BOOL, w.LPCWSTR)
k32.CreateEventW.restype = w.HANDLE
k32.OpenEventW.argtypes = (w.DWORD, w.BOOL, w.LPCWSTR)
k32.OpenEventW.restype = w.HANDLE
k32.SetEvent.argtypes = (w.HANDLE,)
k32.CloseHandle.argtypes = (w.HANDLE,)
k32.WaitForMultipleObjects.argtypes = (w.DWORD, ctypes.POINTER(w.HANDLE), w.BOOL, w.DWORD)
k32.WaitForMultipleObjects.restype = w.DWORD
SYNCHRONIZE, EVENT_MODIFY_STATE, ERROR_ALREADY_EXISTS = 0x00100000, 0x0002, 183


# ---------------------------------------------------------------- one copy at a time

def _name(part=""):
    return f"Local\\{INSTANCE}{part}"


def running():
    h = k32.OpenMutexW(SYNCHRONIZE, False, _name())
    if h:
        k32.CloseHandle(h)
    return bool(h)


def signal(part):
    """Tell the running copy: "-show" (flash Ready) or "-quit". False when none runs."""
    h = k32.OpenEventW(EVENT_MODIFY_STATE, False, _name(part))
    if not h:
        return False
    k32.SetEvent(h)
    k32.CloseHandle(h)
    return True


def launch():
    pyw = Path(sys.executable).with_name("pythonw.exe")
    subprocess.Popen([str(pyw if pyw.exists() else sys.executable), str(Path(__file__).resolve())], cwd=str(ROOT),
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000008)  # DETACHED_PROCESS


def stop_running(wait=10.0):
    if not signal("-quit"):
        return False
    deadline = time.time() + wait
    while running() and time.time() < deadline:
        time.sleep(0.1)
    return True


# ---------------------------------------------------------------- settings, history, sounds

def load_config():
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads(CONFIG.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    try:
        CONFIG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    except OSError:
        log.exception("config not saved")


def add_history(entry):
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    try:
        lines = HISTORY.read_text(encoding="utf-8").splitlines()
        if len(lines) > HISTORY_KEEP + 200:
            HISTORY.write_text("\n".join(lines[-HISTORY_KEEP:]) + "\n", encoding="utf-8")
    except OSError:
        pass


def make_sounds():
    """Two soft clicks: up when it starts listening, down when it stops."""
    import wave
    import numpy as np
    SOUNDS.mkdir(parents=True, exist_ok=True)
    sr = 44100
    for name, notes in (("start", (660, 880)), ("stop", (880, 660))):
        out = []
        for f in notes:
            t = np.arange(int(sr * 0.045)) / sr
            env = np.minimum(1, t / 0.004) * np.exp(-t / 0.018)
            out.append(np.sin(2 * np.pi * f * t) * env * 0.16)
        x = (np.concatenate(out) * 32767).astype(np.int16)
        with wave.open(str(SOUNDS / f"{name}.wav"), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(x.tobytes())


def play(name):
    if os.environ.get("FLOW_NO_SOUND"):
        return
    import winsound
    path = SOUNDS / f"{name}.wav"
    if path.exists():
        winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)


# ---------------------------------------------------------------- shortcuts

def startup_dir():
    return Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))) / \
        "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _ps(script):
    """PowerShell for files under AppData: the Store Python's own writes there land in a private copy Windows never
    reads (studio_common.HOME), a separate PowerShell's do not."""
    return subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True,
                          creationflags=NO_WINDOW)


def shortcut(folder, name="Monarc Flow"):
    pyw = Path(sys.executable).with_name("pythonw.exe")
    lnk = Path(folder) / f"{name}.lnk"
    _ps(f"$l = (New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}'); "
        f"$l.TargetPath = '{pyw if pyw.exists() else sys.executable}'; "
        f"$l.Arguments = '\"{Path(__file__).resolve()}\"'; "
        f"$l.WorkingDirectory = '{ROOT}'; "
        f"$l.IconLocation = '{ICO},0'; "
        "$l.Description = 'Monarc Flow: hold Ctrl+Win to talk'; "
        "$l.Save()")
    return lnk


def startup_on():
    r = _ps(f"Test-Path -LiteralPath '{startup_dir() / 'Monarc Flow.lnk'}'")
    return r.stdout.strip() == "True"


def set_startup(on):
    if on:
        shortcut(startup_dir())
    else:
        _ps(f"Remove-Item -LiteralPath '{startup_dir() / 'Monarc Flow.lnk'}' -ErrorAction SilentlyContinue")


def install():
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader("studio_boot", str(SCRIPTS / "studio_boot.pyw"))
    boot = importlib.util.module_from_spec(importlib.util.spec_from_loader("studio_boot", loader))
    loader.exec_module(boot)
    boot.make_icon("F", (24, 128, 56), ICO)          # also writes flow.png, the tray's picture
    make_sounds()
    desktop = _ps("[Environment]::GetFolderPath('Desktop')").stdout.strip() or str(Path.home() / "Desktop")
    a = shortcut(desktop)
    set_startup(True)
    print(f"icon      {ICO}\nsounds    {SOUNDS}\nshortcuts {a}\n          {startup_dir() / 'Monarc Flow.lnk'}"
          f" (starts with Windows: {startup_on()})")
    if running():
        stop_running()
    launch()
    print("Monarc Flow is running. Hold Ctrl+Win to talk.")


# ---------------------------------------------------------------- the app

class App:
    def __init__(self):
        import flow_mic
        from flow_keys import Keys
        from flow_pill import Pill
        self.cfg = load_config()
        self.rec = None
        self.rec_lock = threading.Lock()
        self.paste_lock = threading.Lock()
        self.take = None
        self.last = ""
        self.icon = None
        self.quitting = threading.Event()
        self.pill = Pill()
        try:
            self.mic = flow_mic.make_mic(self.cfg["mic"])
        except Exception:  # noqa: BLE001  (no audio system yet: say so on the first hold)
            log.exception("mic")
            self.mic = None
        self.mics = self.mic.devices() if self.mic else []
        try:
            from flow_focus import Focus
            self.focus = Focus()
        except Exception:  # noqa: BLE001  (no comtypes: every take also shows the card)
            log.exception("focus check")
            self.focus = None
        threading.Thread(target=self.load, daemon=True, name="flow-load").start()
        self.keys = Keys(self.on_key)
        if not self.keys.hook:
            log.error("no keyboard hook: Ctrl+Win will not work")

    def load(self):
        import numpy as np
        import studio_transcribe as stt
        t = time.time()
        rec = stt.load_recognizer(threads=int(self.cfg["threads"]))
        with self.rec_lock:                               # one warm-up, so the first take is not slow
            stt.decode_batch(rec, [(0.0, (np.random.default_rng(0).standard_normal(16000) * 0.001)
                                    .astype(np.float32))])
        self.rec = rec
        log.info("ready (Parakeet loaded in %.1f s)", time.time() - t)

    def decode(self, samples):
        import numpy as np
        import studio_transcribe as stt
        x = np.concatenate([samples, np.zeros(int(0.3 * stt.SR), np.float32)])   # room for the last word
        with self.rec_lock:
            r = stt.decode_batch(self.rec, [(0.0, x)])[0]
        return " ".join(wd[2] for wd in r["words"])

    # ---- the keys (dispatcher thread)
    def on_key(self, name, info):
        if name == "start":
            self.start()
        elif name == "lock":
            if self.take:
                self.take.locked = True
                self.pill.listening(True)
                log.info("lock")
        elif name == "cancel":
            take, self.take = self.take, None
            if take:
                take.cancelled = True
                self.mic.stop()
                take.end()
                self.pill.hide()
                log.info("cancel (%s)", info)
        elif name == "stop":
            take, self.take = self.take, None
            if not take:
                return
            if not info["locked"] and info["held"] < float(self.cfg["min_hold_seconds"]):
                take.cancelled = True
                self.mic.stop()
                take.end()
                self.pill.hide()
                log.info("tap (%.2f s): nothing", info["held"])
                return
            take.t_stop = time.time()
            take.focus = self.focus.ask() if self.focus else None
            time.sleep(int(self.cfg["tail_ms"]) / 1000)   # the end of the last word, said as the keys came up
            self.mic.stop()
            take.end()
            self.pill.writing()
            if self.cfg["sounds"]:
                play("stop")
            log.info("stop (%.1f s of talk%s)", take.seconds, ", hands-free" if info["locked"] else "")

    def start(self):
        import flow_mic
        if not self.rec:
            self.pill.say("Loading, one moment")
            return
        if not self.mic:
            self.pill.say("No microphone")
            return
        take = flow_mic.Take()

        def on_level(rms):
            self.pill.level(rms)
            take.hear(rms)

        try:
            name = self.mic.start(take, on_level)
        except Exception:  # noqa: BLE001  (plugged in or swapped since the last look: look again, once)
            try:
                self.mic.refresh()
                self.mics = self.mic.devices()
                name = self.mic.start(take, on_level)
            except Exception as e:  # noqa: BLE001
                log.warning("mic did not open: %s", e)
                self.pill.say("No microphone")
                return
        self.take = take
        self.pill.listening(False)
        if self.cfg["sounds"]:
            play("start")
        log.info("start (%s)", name)
        threading.Thread(target=self.finish, args=(take,), daemon=True, name="flow-take").start()
        threading.Thread(target=self.limit, args=(take,), daemon=True).start()

    def limit(self, take):
        """A take ends by itself at max_take_minutes."""
        deadline = time.time() + float(self.cfg["max_take_minutes"]) * 60
        while take.live and time.time() < deadline:
            time.sleep(1)
        if take.live and self.take is take:
            log.info("time limit")
            self.keys.reset()
            self.on_key("stop", {"held": 999, "locked": True})

    # ---- one take, start to paste (its own thread)
    def finish(self, take):
        import flow_clean
        import flow_mic
        import flow_paste
        from flow_keys import combo_down
        try:
            raw, heard = flow_mic.write(take, self.decode, one_go=float(self.cfg["one_go_seconds"]),
                                        pause=float(self.cfg["pause_cut_seconds"]),
                                        min_piece=float(self.cfg["min_piece_seconds"]))
        except Exception:  # noqa: BLE001
            log.exception("writing the take")
            self.pill.say("Something went wrong")
            return
        if take.cancelled:
            return
        text = flow_clean.clean(raw, space_after=bool(self.cfg["space_after"]))
        if not text.strip():
            if raw:
                self.pill.hide()                          # "scratch that" left nothing
            elif take.peak < SILENT:
                self.pill.say("Mic is silent: check its mute or plug", 3.0)
            else:
                self.pill.say("Didn't catch that")
            log.info("nothing to paste (heard speech: %s, loudest %.4f)", heard, take.peak)
            return
        # a text box where the cursor is? asked when he let go, beside the writing; not one (or not sure): the card
        box, where = take.focus.get() if take.focus else (None, "not asked")
        card = text.strip()
        with self.paste_lock:
            self.last = text
            deadline = time.time() + 5
            while combo_down() and time.time() < deadline:   # Win still down would make Ctrl+V into Win+V
                time.sleep(0.02)
            if combo_down():
                self.pill.show_card(card, "Not pasted. Click to copy.", flow_paste.copy_text)
                log.info("keys still down: not pasted, shown to copy")
            else:
                sent = []

                def on_sent():
                    sent.append(time.time())
                    if box is True:
                        self.pill.hide()

                ok = flow_paste.paste(text, int(self.cfg["restore_clipboard_ms"]), on_sent=on_sent)
                lag = (sent[0] if sent else time.time()) - (take.t_stop or time.time())
                log.info("pasted %d characters, %.2f s after letting go%s; cursor in a text box: %s (%s)",
                         len(text), lag, "" if ok else " (clipboard busy: NOT pasted)",
                         {True: "yes", False: "no", None: "not sure"}[box], where)
                if not ok:
                    self.pill.show_card(card, "Not pasted. Click to copy.", flow_paste.copy_text)
                elif box is not True:
                    self.pill.show_card(card, "No text box here. Click to copy.", flow_paste.copy_text)
        if self.icon:
            self.icon.update_menu()
        add_history({"at": time.strftime("%Y-%m-%d %H:%M:%S"), "seconds": round(take.seconds, 1), "heard": raw,
                     "text": text})

    # ---- the tray
    def run(self):
        import pystray
        from PIL import Image
        img = Image.open(PNG) if PNG.exists() else Image.new("RGB", (64, 64), (24, 128, 56))
        M = pystray.MenuItem
        menu = pystray.Menu(
            M("Monarc Flow: hold Ctrl+Win to talk", lambda: self.pill.say("Ready", 1.2), default=True),
            pystray.Menu.SEPARATOR,
            M("Microphone", pystray.Menu(lambda: self.mic_items())),
            M("Sounds", self.toggle_sounds, checked=lambda item: bool(self.cfg["sounds"])),
            M("Copy last dictation", self.copy_last, enabled=lambda item: bool(self.last)),
            M("Open word list", lambda: os.startfile(WORDS)),
            M("Open history", self.open_history),
            M("Start with Windows", self.toggle_startup, checked=lambda item: self.startup),
            pystray.Menu.SEPARATOR,
            M("Quit", self.quit))
        self.startup = startup_on()
        self.icon = pystray.Icon(INSTANCE, img, "Monarc Flow: hold Ctrl+Win to talk", menu)
        threading.Thread(target=self.watch_signals, daemon=True).start()
        self.icon.run()

    def mic_items(self):
        import pystray
        names = ["Windows default"] + [n for n in self.mics if n]
        return [pystray.MenuItem(n, self.pick_mic(n), radio=True,
                                 checked=lambda item, n=n: (self.cfg["mic"] or "Windows default") == n)
                for n in names]

    def pick_mic(self, name):
        def pick():
            self.cfg["mic"] = "" if name == "Windows default" else name
            save_config(self.cfg)
            if self.mic and hasattr(self.mic, "name"):
                self.mic.name = self.cfg["mic"]
            self.icon.update_menu()
        return pick

    def toggle_sounds(self):
        self.cfg["sounds"] = not self.cfg["sounds"]
        save_config(self.cfg)
        self.icon.update_menu()

    def toggle_startup(self):
        set_startup(not self.startup)
        self.startup = startup_on()
        self.icon.update_menu()

    def copy_last(self):
        import flow_paste
        if self.last:
            flow_paste.copy_text(self.last)

    def open_history(self):
        if not HISTORY.exists():
            HISTORY.parent.mkdir(parents=True, exist_ok=True)
            HISTORY.touch()
        os.startfile(HISTORY)

    def watch_signals(self):
        handles = (w.HANDLE * 2)(self.ev_show, self.ev_quit)
        while True:
            r = k32.WaitForMultipleObjects(2, handles, False, 0xFFFFFFFF)
            if r == 0:
                if self.mic:
                    self.mics = self.mic.devices()
                    self.icon.update_menu()
                self.pill.say("Ready", 1.2)
            elif r == 1:
                self.quit()
                return
            else:
                time.sleep(1)

    def quit(self):
        if self.quitting.is_set():
            return
        self.quitting.set()
        log.info("quit")
        self.keys.stop()
        self.pill.quit()
        if self.icon:
            self.icon.stop()


# ---------------------------------------------------------------- start

def setup_logging(console):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    try:
        if LOG.exists() and LOG.stat().st_size > 1_000_000:
            LOG.write_text("", encoding="utf-8")
    except OSError:
        pass
    handlers = [logging.FileHandler(LOG, encoding="utf-8")]
    if console:
        handlers.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S", handlers=handlers,
                        force=True)
    logging.getLogger("comtypes").setLevel(logging.WARNING)      # its cache notes on every start


def check():
    import flow_clean
    import flow_mic
    import studio_transcribe as stt
    try:
        m = flow_mic.Mic(load_config()["mic"])
        print("mic      ", m._device(m._pa)["name"])
    except Exception as e:  # noqa: BLE001
        print("mic       none:", e)
    t = time.time()
    rec = stt.load_recognizer(threads=int(load_config()["threads"]))
    print(f"load      {time.time() - t:.1f} s")
    x = flow_mic.read_wav(TEST_CLIP)
    stt.decode_batch(rec, [(0.0, x[:16000])])
    t = time.time()
    words = " ".join(wd[2] for wd in stt.decode_batch(rec, [(0.0, x)])[0]["words"])
    print(f"write     {len(x) / 16000:.1f} s of talk in {time.time() - t:.2f} s")
    print("heard    ", words)
    print("pasted   ", repr(flow_clean.clean(words)))
    print("running  ", running())


def main():
    args = sys.argv[1:]
    if "--install" in args:
        install()
        return
    if "--check" in args:
        check()
        return
    if "--quit" in args:
        stop_running()
        return
    if "--restart" in args:
        stop_running()
        launch()
        return
    mutex = k32.CreateMutexW(None, False, _name())
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        signal("-show")
        return
    console = sys.stdout is not None
    if not console:                                       # pythonw: no console, keep stray prints out of the way
        sys.stdout = sys.stderr = open(os.devnull, "w")
    setup_logging(console)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)    # real pixels at 125 %, for the pill
    except Exception:  # noqa: BLE001
        pass
    app = App()
    app.ev_show = k32.CreateEventW(None, False, False, _name("-show"))
    app.ev_quit = k32.CreateEventW(None, True, False, _name("-quit"))
    log.info("Monarc Flow started (%s)", INSTANCE)
    try:
        app.run()
    finally:
        log.info("stopped")
        k32.CloseHandle(mutex)
        os._exit(0)


if __name__ == "__main__":
    main()
