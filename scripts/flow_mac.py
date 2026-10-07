"""Monarc Flow on a Mac (2026-10-07, Jonathan: "ship Monarc's CRM and Monarc Flow ... for installation on a Mac").

Hold Ctrl+Cmd, talk, let go, and the words land where the cursor is. The same pieces as on Windows where they carry
over: Parakeet through sherpa-onnx (scripts/studio_transcribe.py), the take and the voice finder (scripts/flow_mic.py),
the cleanup rules and word fixes (scripts/flow_clean.py, projects/flow/words.json), the settings
(projects/flow/config.json) and the history (~/.monarc/flow-history.jsonl). Nothing leaves the machine.

  python3 scripts/flow_mac.py              start it (the app ~/Applications/Monarc Flow.app runs this)
  python3 scripts/flow_mac.py --install    the models, the app, and start at log-in; then it opens
  python3 scripts/flow_mac.py --check      the mics, then the test clip written and timed
  python3 scripts/flow_mac.py --restart    stop the running copy and open the app again
  python3 scripts/flow_mac.py --quit       stop it

The keys (Cmd is the Mac's Win key):
  hold Ctrl+Cmd                 start; letting go of either stops
  Space while holding           hands-free; the Mac never sees that Space (so the emoji picker stays shut)
  Ctrl+Cmd again while locked   stop
  Esc while holding or locked   cancel
  Ctrl+Cmd plus any other key   cancel, and the key works as normal

What differs from Windows: a menu-bar icon in place of the tray (it reads REC while listening and ... while writing),
and no pop-up card. When the cursor is not in a text box (the Mac's Accessibility read decides), the words still go in
with Cmd+V and are also left on the clipboard, with a notice saying so.

macOS asks once for three permissions for "Monarc Flow" (System Settings, Privacy & Security): Microphone,
Accessibility (to paste and to see the text box), and Input Monitoring (to see the keys). Until both key permissions
are on, the menu says so.
"""
import json
import logging
import os
import queue
import signal
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
CONFIG = Path(os.environ.get("FLOW_CONFIG") or FLOW / "config.json")
HISTORY = Path(os.environ.get("FLOW_HISTORY") or HOME / "flow-history.jsonl")
LOG = Path(os.environ.get("FLOW_LOG") or HOME / "flow.log")
WORDS = FLOW / "words.json"
PNG = FLOW / "flow.png"
SOUNDS = FLOW / "sounds"
LOCK = HOME / "flow-mac.lock"
PIDFILE = HOME / "flow-mac.pid"
LABEL = "com.monarcbuild.flow"
APP_NAME = "Monarc Flow"
HISTORY_KEEP = 1000
SILENT = 0.003
DEFAULTS = {"mic": "", "sounds": True, "space_after": True, "min_hold_seconds": 0.3, "tail_ms": 200,
            "restore_clipboard_ms": 400, "one_go_seconds": 15, "pause_cut_seconds": 0.8, "min_piece_seconds": 6,
            "max_take_minutes": 10, "threads": 4}
KEY_SPACE, KEY_ESC, KEY_V = 49, 53, 9          # Mac virtual key codes
TAG = 0x4D464C57                                # "MFLW": a key Monarc Flow sent itself
log = logging.getLogger("flow")


# ---------------------------------------------------------------- settings, history, sounds, notices

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


def play(name):
    if os.environ.get("FLOW_NO_SOUND"):
        return
    f = SOUNDS / f"{name}.wav"
    if f.exists():
        subprocess.Popen(["afplay", str(f)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def notify(text, title=APP_NAME):
    esc = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')  # noqa: E731
    subprocess.Popen(["osascript", "-e", f'display notification "{esc(text[:220])}" with title "{esc(title)}"'],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------------------------------------------------------------- the hold (plain logic, tested on any machine)

class Hold:
    """Turns modifier and key events into start, lock, cancel, and stop for the app. emit(name, info)."""

    def __init__(self, emit):
        self.emit = emit
        self.ctrl = self.cmd = False
        self.active = self.locked = False
        self.t0 = 0.0
        self.swallowed = set()

    def flags(self, ctrl, cmd):
        was = self.ctrl and self.cmd
        self.ctrl, self.cmd = bool(ctrl), bool(cmd)
        now = self.ctrl and self.cmd
        if now and not was:
            if self.locked:
                self._end("stop")
            elif not self.active:
                self.active, self.t0 = True, time.time()
                self.emit("start", {})
        elif was and not now and self.active and not self.locked:
            self._end("stop")

    def key_down(self, code):
        """True when the key is Flow's and the Mac should not see it."""
        if self.active and not self.locked and self.ctrl and self.cmd:
            if code == KEY_SPACE:
                self.locked = True
                self.emit("lock", {})
                self.swallowed.add(code)
                return True
            if code == KEY_ESC:
                self._end("cancel", "Esc")
                self.swallowed.add(code)
                return True
            self._end("cancel", "another key")
            return False
        if self.locked and code == KEY_ESC:
            self._end("cancel", "Esc")
            self.swallowed.add(code)
            return True
        return False

    def key_up(self, code):
        if code in self.swallowed:
            self.swallowed.discard(code)
            return True
        return False

    def _end(self, name, why=""):
        info = {"held": time.time() - self.t0, "locked": self.locked} if name == "stop" else why
        self.active = self.locked = False
        self.emit(name, info)

    def reset(self):
        self.active = self.locked = False


# ---------------------------------------------------------------- the keys (a Quartz event tap on its own thread)

class Keys:
    def __init__(self, on_key):
        self.events = queue.Queue()
        self.hold = Hold(lambda n, i: self.events.put((n, i)))
        self.on_key = on_key
        self.tap = None
        self.ok = threading.Event()
        threading.Thread(target=self._dispatch, daemon=True, name="flow-keys-dispatch").start()
        threading.Thread(target=self._run, daemon=True, name="flow-keys").start()
        self.ok.wait(3)

    def _dispatch(self):
        while True:
            name, info = self.events.get()
            if name is None:
                return
            try:
                self.on_key(name, info)
            except Exception:  # noqa: BLE001
                log.exception("key event %s", name)

    def _run(self):
        import Quartz as Q
        h = self.hold

        def cb(proxy, kind, event, refcon):
            if kind in (Q.kCGEventTapDisabledByTimeout, Q.kCGEventTapDisabledByUserInput):
                Q.CGEventTapEnable(self.tap, True)               # macOS turns a slow tap off; turn it back on
                return event
            if Q.CGEventGetIntegerValueField(event, Q.kCGEventSourceUserData) == TAG:
                return event
            if kind == Q.kCGEventFlagsChanged:
                f = Q.CGEventGetFlags(event)
                h.flags(f & Q.kCGEventFlagMaskControl, f & Q.kCGEventFlagMaskCommand)
                return event
            code = Q.CGEventGetIntegerValueField(event, Q.kCGKeyboardEventKeycode)
            if kind == Q.kCGEventKeyDown:
                return None if h.key_down(code) else event
            if kind == Q.kCGEventKeyUp:
                return None if h.key_up(code) else event
            return event

        mask = (Q.CGEventMaskBit(Q.kCGEventKeyDown) | Q.CGEventMaskBit(Q.kCGEventKeyUp)
                | Q.CGEventMaskBit(Q.kCGEventFlagsChanged))
        self.tap = Q.CGEventTapCreate(Q.kCGSessionEventTap, Q.kCGHeadInsertEventTap, Q.kCGEventTapOptionDefault,
                                      mask, cb, None)
        if not self.tap:
            log.error("no key tap: turn on Monarc Flow in Privacy & Security, Accessibility and Input Monitoring")
            self.ok.set()
            return
        src = Q.CFMachPortCreateRunLoopSource(None, self.tap, 0)
        Q.CFRunLoopAddSource(Q.CFRunLoopGetCurrent(), src, Q.kCFRunLoopCommonModes)
        Q.CGEventTapEnable(self.tap, True)
        self.ok.set()
        Q.CFRunLoopRun()

    def reset(self):
        self.hold.reset()

    def stop(self):
        self.events.put((None, None))


def combo_down():
    import Quartz as Q
    f = Q.CGEventSourceFlagsState(Q.kCGEventSourceStateCombinedSessionState)
    return bool(f & Q.kCGEventFlagMaskControl) or bool(f & Q.kCGEventFlagMaskCommand)


# ---------------------------------------------------------------- clipboard and Cmd+V

def _board():
    from AppKit import NSPasteboard
    return NSPasteboard.generalPasteboard()


def copy_text(text):
    from AppKit import NSPasteboardTypeString
    pb = _board()
    pb.clearContents()
    pb.setString_forType_(text, NSPasteboardTypeString)
    return pb.changeCount()


def send_cmd_v():
    import Quartz as Q
    src = Q.CGEventSourceCreate(Q.kCGEventSourceStateHIDSystemState)
    for down in (True, False):
        ev = Q.CGEventCreateKeyboardEvent(src, KEY_V, down)
        Q.CGEventSetFlags(ev, Q.kCGEventFlagMaskCommand)
        Q.CGEventSetIntegerValueField(ev, Q.kCGEventSourceUserData, TAG)
        Q.CGEventPost(Q.kCGHIDEventTap, ev)
        time.sleep(0.01)


def paste(text, restore_ms, keep=False, on_sent=None):
    """Put text where the cursor is with Cmd+V. The old clipboard comes back after restore_ms unless keep."""
    from AppKit import NSPasteboardTypeString
    old = _board().stringForType_(NSPasteboardTypeString)
    mine = copy_text(text)
    time.sleep(0.03)
    send_cmd_v()
    if on_sent:
        on_sent()
    if not keep and old is not None:
        def put_back():
            time.sleep(restore_ms / 1000)
            if _board().changeCount() == mine:            # nothing else was copied since
                copy_text(old)
        threading.Thread(target=put_back, daemon=True).start()
    return True


# ---------------------------------------------------------------- is the cursor in a text box?

TEXT_ROLES = {"AXTextField", "AXTextArea", "AXComboBox", "AXSearchField"}


def text_box():
    """(True, False, or None for not sure; how it decided), from the Mac's Accessibility read."""
    try:
        import ApplicationServices as AS
        sysw = AS.AXUIElementCreateSystemWide()
        err, el = AS.AXUIElementCopyAttributeValue(sysw, AS.kAXFocusedUIElementAttribute, None)
        if err or el is None:
            return None, f"no focused element ({err})"
        err, role = AS.AXUIElementCopyAttributeValue(el, AS.kAXRoleAttribute, None)
        if role in TEXT_ROLES:
            return True, str(role)
        err2, settable = AS.AXUIElementIsAttributeSettable(el, AS.kAXValueAttribute, None)
        if not err2 and settable:
            return True, f"{role}, value can be set"
        return False, str(role)
    except Exception as e:  # noqa: BLE001
        return None, f"not asked ({type(e).__name__})"


class Ask:
    """The text-box look, started when he lets go, read once the words are ready."""

    def __init__(self):
        self.result = (None, "not ready")
        self.t = threading.Thread(target=self._go, daemon=True)
        self.t.start()

    def _go(self):
        self.result = text_box()

    def get(self, timeout=0.6):
        self.t.join(timeout)
        return self.result


# ---------------------------------------------------------------- the mic (sounddevice, resampled to 16 kHz)

class Mic:
    def __init__(self, name=""):
        self.name = name
        self.lock = threading.Lock()
        self.stream = self.rs = self.take = None

    def devices(self):
        import sounddevice as sd
        try:
            return [d["name"] for d in sd.query_devices() if int(d.get("max_input_channels") or 0) > 0]
        except Exception:  # noqa: BLE001
            return []

    def refresh(self):
        import sounddevice as sd
        with self.lock:
            if self.stream:
                return
            try:                                          # a fresh look for mics plugged in since
                sd._terminate()
                sd._initialize()
            except Exception:  # noqa: BLE001
                pass

    def _device(self):
        import sounddevice as sd
        if self.name:
            for i, d in enumerate(sd.query_devices()):
                if d["name"] == self.name and int(d.get("max_input_channels") or 0) > 0:
                    return i, d
        d = sd.query_devices(kind="input")
        if not d:
            raise RuntimeError("No microphone")
        return None, d

    def start(self, take, on_level):
        import numpy as np
        import sounddevice as sd
        import soxr
        import flow_mic
        with self.lock:
            idx, dev = self._device()
            rate = int(dev["default_samplerate"])
            ch = max(1, min(2, int(dev["max_input_channels"])))
            rs = soxr.ResampleStream(rate, flow_mic.SR, 1, dtype="float32")

            def cb(indata, frames, t, status):
                x = indata.mean(axis=1) if ch > 1 else indata[:, 0]
                x = np.ascontiguousarray(x, dtype=np.float32)
                if len(x):
                    on_level(float(np.sqrt(np.mean(x * x))))
                    y = rs.resample_chunk(x)
                    if len(y):
                        take.add(y.astype(np.float32))

            self.stream = sd.InputStream(device=idx, channels=ch, samplerate=rate, dtype="float32",
                                         blocksize=max(256, rate // 40), callback=cb)
            self.rs, self.take = rs, take
            self.stream.start()
            return dev["name"]

    def stop(self):
        import numpy as np
        with self.lock:
            stream, rs, take = self.stream, self.rs, self.take
            self.stream = self.rs = self.take = None
        if stream:
            try:
                stream.stop()
                stream.close()
            except Exception:  # noqa: BLE001
                pass
            tail = rs.resample_chunk(np.zeros(0, np.float32), last=True)
            if len(tail):
                take.add(tail.astype(np.float32))


def make_mic(name=""):
    import flow_mic
    fake = os.environ.get("FLOW_FAKE_MIC")
    if fake:
        return flow_mic.FakeMic(fake, float(os.environ.get("FLOW_FAKE_SPEED") or 1))
    return Mic(name)


# ---------------------------------------------------------------- the app

class Flow:
    """Everything but the menu: the keys, the mic, one take from start to paste."""

    def __init__(self):
        self.cfg = load_config()
        self.rec = None
        self.rec_lock = threading.Lock()
        self.paste_lock = threading.Lock()
        self.take = None
        self.last = ""
        self.state = "loading"            # loading, ready, listening, writing, no-keys
        self.mic = make_mic(self.cfg["mic"])
        threading.Thread(target=self.load, daemon=True, name="flow-load").start()
        self.keys = Keys(self.on_key)
        if not self.keys.tap:
            self.state = "no-keys"

    def load(self):
        import numpy as np
        import studio_transcribe as stt
        t = time.time()
        rec = stt.load_recognizer(threads=int(self.cfg["threads"]))
        with self.rec_lock:
            stt.decode_batch(rec, [(0.0, (np.random.default_rng(0).standard_normal(16000) * 0.001).astype(np.float32))])
        self.rec = rec
        if self.state == "loading":
            self.state = "ready"
        log.info("ready (Parakeet loaded in %.1f s)", time.time() - t)

    def decode(self, samples):
        import numpy as np
        import studio_transcribe as stt
        x = np.concatenate([samples, np.zeros(int(0.3 * stt.SR), np.float32)])
        with self.rec_lock:
            r = stt.decode_batch(self.rec, [(0.0, x)])[0]
        return " ".join(wd[2] for wd in r["words"])

    def on_key(self, name, info):
        if name == "start":
            self.start()
        elif name == "lock":
            if self.take:
                self.take.locked = True
                log.info("lock")
        elif name == "cancel":
            take, self.take = self.take, None
            if take:
                take.cancelled = True
                self.mic.stop()
                take.end()
                self.state = "ready"
                log.info("cancel (%s)", info)
        elif name == "stop":
            take, self.take = self.take, None
            if not take:
                return
            if not info["locked"] and info["held"] < float(self.cfg["min_hold_seconds"]):
                take.cancelled = True
                self.mic.stop()
                take.end()
                self.state = "ready"
                log.info("tap (%.2f s): nothing", info["held"])
                return
            take.t_stop = time.time()
            take.focus = Ask()
            time.sleep(int(self.cfg["tail_ms"]) / 1000)
            self.mic.stop()
            take.end()
            self.state = "writing"
            if self.cfg["sounds"]:
                play("stop")
            log.info("stop (%.1f s of talk%s)", take.seconds, ", hands-free" if info["locked"] else "")

    def start(self):
        import flow_mic
        if not self.rec:
            notify("Loading, one moment")
            return
        take = flow_mic.Take()
        try:
            name = self.mic.start(take, take.hear)
        except Exception:  # noqa: BLE001
            try:
                self.mic.refresh()
                name = self.mic.start(take, take.hear)
            except Exception as e:  # noqa: BLE001
                log.warning("mic did not open: %s", e)
                notify("No microphone (or Monarc Flow is not allowed to use it)")
                return
        self.take = take
        self.state = "listening"
        if self.cfg["sounds"]:
            play("start")
        log.info("start (%s)", name)
        threading.Thread(target=self.finish, args=(take,), daemon=True, name="flow-take").start()
        threading.Thread(target=self.limit, args=(take,), daemon=True).start()

    def limit(self, take):
        deadline = time.time() + float(self.cfg["max_take_minutes"]) * 60
        while take.live and time.time() < deadline:
            time.sleep(1)
        if take.live and self.take is take:
            log.info("time limit")
            self.keys.reset()
            self.on_key("stop", {"held": 999, "locked": True})

    def finish(self, take):
        import flow_clean
        import flow_mic
        try:
            raw, heard = flow_mic.write(take, self.decode, one_go=float(self.cfg["one_go_seconds"]),
                                        pause=float(self.cfg["pause_cut_seconds"]),
                                        min_piece=float(self.cfg["min_piece_seconds"]))
        except Exception:  # noqa: BLE001
            log.exception("writing the take")
            self.state = "ready"
            notify("Something went wrong")
            return
        self.state = "ready" if self.state == "writing" else self.state
        if take.cancelled:
            return
        text = flow_clean.clean(raw, space_after=bool(self.cfg["space_after"]))
        if not text.strip():
            if not raw:
                notify("Mic is silent: check its mute or plug" if take.peak < SILENT else "Didn't catch that")
            log.info("nothing to paste (heard speech: %s, loudest %.4f)", heard, take.peak)
            return
        box, where = take.focus.get() if take.focus else (None, "not asked")
        with self.paste_lock:
            self.last = text
            deadline = time.time() + 5
            while combo_down() and time.time() < deadline:      # Ctrl still down would make Cmd+V into Ctrl+Cmd+V
                time.sleep(0.02)
            if combo_down():
                copy_text(text.strip())
                notify("Not pasted (keys still down). It's on the clipboard.")
                log.info("keys still down: not pasted, left on the clipboard")
            else:
                paste(text, int(self.cfg["restore_clipboard_ms"]), keep=box is not True)
                log.info("pasted %d characters, %.2f s after letting go; cursor in a text box: %s (%s)", len(text),
                         time.time() - (take.t_stop or time.time()), {True: "yes", False: "no", None: "not sure"}[box], where)
                if box is not True:
                    notify("No text box here. It's on the clipboard.")
        add_history({"at": time.strftime("%Y-%m-%d %H:%M:%S"), "seconds": round(take.seconds, 1), "heard": raw,
                     "text": text})

    def quit(self):
        self.keys.stop()
        self.mic.stop()


def run_menu(flow):
    """The menu-bar icon. AppKit wants the main thread; a timer there redraws from flow.state."""
    import rumps
    titles = {"loading": "MF…", "ready": "MF", "listening": "REC", "writing": "MF…", "no-keys": "MF!"}

    class Menu(rumps.App):
        def __init__(self):
            super().__init__(APP_NAME, title="MF", quit_button=None)
            self.mics = rumps.MenuItem("Microphone")
            self.sounds = rumps.MenuItem("Sounds", callback=self.toggle_sounds)
            self.login = rumps.MenuItem("Start at log-in", callback=self.toggle_login)
            self.menu = [rumps.MenuItem("Hold Ctrl+Cmd to talk", callback=lambda _: notify("Ready")), None,
                         self.mics, self.sounds, rumps.MenuItem("Copy last dictation", callback=self.copy_last),
                         rumps.MenuItem("Open word list", callback=lambda _: subprocess.Popen(["open", str(WORDS)])),
                         rumps.MenuItem("Open history", callback=self.open_history), self.login, None,
                         rumps.MenuItem("Quit", callback=self.quit)]
            self.fill_mics()
            self.timer = rumps.Timer(self.tick, 0.15)
            self.timer.start()

        def tick(self, _):
            t = titles.get(flow.state, "MF")
            if self.title != t:
                self.title = t
            self.sounds.state = 1 if flow.cfg["sounds"] else 0
            import mac_app
            self.login.state = 1 if mac_app.login_item_on(LABEL) else 0

        def fill_mics(self):
            try:
                self.mics.clear()
            except Exception:  # noqa: BLE001  (rumps raises on a submenu that was never filled)
                pass
            for n in ["System default"] + flow.mic.devices():
                item = rumps.MenuItem(n, callback=self.pick_mic)
                item.state = 1 if (flow.cfg["mic"] or "System default") == n else 0
                self.mics.add(item)

        def pick_mic(self, item):
            flow.cfg["mic"] = "" if item.title == "System default" else item.title
            save_config(flow.cfg)
            if hasattr(flow.mic, "name"):
                flow.mic.name = flow.cfg["mic"]
            self.fill_mics()

        def toggle_sounds(self, _):
            flow.cfg["sounds"] = not flow.cfg["sounds"]
            save_config(flow.cfg)

        def toggle_login(self, _):
            import mac_app
            set_login(not mac_app.login_item_on(LABEL))

        def copy_last(self, _):
            if flow.last:
                copy_text(flow.last)

        def open_history(self, _):
            HISTORY.parent.mkdir(parents=True, exist_ok=True)
            HISTORY.touch()
            subprocess.Popen(["open", "-t", str(HISTORY)])

        def quit(self, _):
            log.info("quit")
            flow.quit()
            rumps.quit_application()

    m = Menu()
    signal.signal(signal.SIGTERM, lambda *a: m.quit(None))
    signal.signal(signal.SIGUSR1, lambda *a: (m.fill_mics(), notify("Ready")))
    if flow.state == "no-keys":
        notify("Turn on Monarc Flow in System Settings, Privacy & Security, under Accessibility and Input Monitoring. "
               "Then quit and reopen it.")
    m.run()


# ---------------------------------------------------------------- one copy, install, start

def app_path():
    import mac_app
    return mac_app.APPS / f"{APP_NAME}.app"


def running_pid():
    try:
        pid = int(PIDFILE.read_text().strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


def take_lock():
    import fcntl
    HOME.mkdir(parents=True, exist_ok=True)
    f = open(LOCK, "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return None
    PIDFILE.write_text(str(os.getpid()))
    return f


def stop_running(wait=10.0):
    pid = running_pid()
    if not pid:
        return False
    os.kill(pid, signal.SIGTERM)
    deadline = time.time() + wait
    while running_pid() and time.time() < deadline:
        time.sleep(0.1)
    return True


def set_login(on):
    """Start at log-in through the app, so macOS keeps one set of permissions (the app's)."""
    import mac_app
    import plistlib
    plist = mac_app.AGENTS / f"{LABEL}.plist"
    if plist.exists():
        subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
    if not on:
        plist.unlink(missing_ok=True)
        return
    mac_app.AGENTS.mkdir(parents=True, exist_ok=True)
    with open(plist, "wb") as f:
        plistlib.dump({"Label": LABEL, "ProgramArguments": ["/usr/bin/open", "-a", str(app_path())], "RunAtLoad": True}, f)
    subprocess.run(["launchctl", "load", str(plist)], capture_output=True)


def install():
    import mac_app
    import studio_check
    print("models (Parakeet and the voice finder, about 700 MB the first time) ...")
    studio_check.get_models()
    app = mac_app.make_app(APP_NAME, __file__, png=PNG if PNG.exists() else None)
    print(f"app       {app}")
    set_login(True)
    print(f"log-in    {mac_app.AGENTS / (LABEL + '.plist')}")
    stop_running()
    subprocess.run(["open", str(app)])
    print("Opened. macOS will ask for the Microphone. Then in System Settings, Privacy & Security, turn on\n"
          "Monarc Flow under Accessibility and under Input Monitoring, quit it from the menu bar (MF), and open it again.")


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


def check():
    import flow_clean
    import flow_mic
    import studio_common as sc
    import studio_transcribe as stt
    print("mics     ", ", ".join(Mic().devices()) or "none found")
    clip = sc.PARAKEET_DIR / "test_wavs" / "0.wav"
    if not clip.exists():
        print("no test clip: run --install first")
        return
    t = time.time()
    rec = stt.load_recognizer(threads=int(load_config()["threads"]))
    print(f"loaded    {time.time() - t:.1f} s")
    x = flow_mic.read_wav(clip)
    t = time.time()
    r = stt.decode_batch(rec, [(0.0, x)])[0]
    print(f"written   {time.time() - t:.2f} s for {len(x) / 16000:.1f} s of talk")
    print("text     ", flow_clean.clean(" ".join(w[2] for w in r["words"])))


def main():
    if sys.platform != "darwin":
        sys.exit("This is Monarc Flow for a Mac. On Windows run scripts/flow.pyw.")
    args = sys.argv[1:]
    if "--install" in args:
        return install()
    if "--check" in args:
        return check()
    if "--quit" in args:
        print("stopped" if stop_running() else "not running")
        return
    if "--restart" in args:
        stop_running()
        subprocess.run(["open", str(app_path())] if app_path().exists() else [sys.executable, __file__])
        return
    lock = take_lock()
    if not lock:
        pid = running_pid()
        if pid:
            os.kill(pid, signal.SIGUSR1)                     # the running one says "Ready"
        return
    setup_logging(console=sys.stdout.isatty())
    log.info("start (Mac)")
    run_menu(Flow())


if __name__ == "__main__":
    main()
