"""The Ctrl+Win hold for Monarc Flow (2026-10-03). A low-level keyboard hook (Windows shows this program each key press
before the window with the cursor gets it) runs on a thread of its own.

  hold Ctrl+Win (either Ctrl, either Win)    start; letting go of either one stops
  Space while holding                        lock on (hands-free); Windows never sees that Space
  Ctrl+Win again while locked                stop
  Esc while holding or locked                cancel; Windows never sees that Esc
  Ctrl+Win plus any other key                cancel, and the key works as normal (Ctrl+Win+Left still switches desktops)

When a hold starts, one blank key (0xE8, a code no key uses) is sent, so Windows does not open Start when Win comes
up. Keys this program sends carry a tag (TAG) and the hook lets them by. The hook only flips its state and queues an
event; a second thread calls the app, so the keyboard never waits on Python. If a key-up was missed (the screen
locked mid-hold), a watcher notices both keys are up and stops the take. The hook is put back once a minute while
idle, since Windows drops a hook that once answered too slowly, without saying so.
"""
import ctypes
import ctypes.wintypes as w
import logging
import queue
import threading
import time

user32 = ctypes.WinDLL("user32", use_last_error=True)       # own copies: argtypes here never touch ctypes.windll
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
log = logging.getLogger("flow")

WH_KEYBOARD_LL = 13
WM_KEYDOWN, WM_SYSKEYDOWN = 0x0100, 0x0104
WM_QUIT, WM_APP = 0x0012, 0x8000
CTRL = {0xA2, 0xA3, 0x11}
WIN = {0x5B, 0x5C}
COMBO = (0xA2, 0xA3, 0x5B, 0x5C)
VK_SPACE, VK_ESCAPE, VK_MASK = 0x20, 0x1B, 0xE8
VK_CONTROL, VK_V = 0x11, 0x56
EXTENDED = {0x5B, 0x5C, 0xA3, 0xA5, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E}
TAG = 0x4D464C57                  # "MFLW" in dwExtraInfo: a key Monarc Flow sent itself
KEYEVENTF_EXTENDEDKEY, KEYEVENTF_KEYUP = 0x0001, 0x0002
INPUT_KEYBOARD = 1

LRESULT = w.LPARAM
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, w.WPARAM, w.LPARAM)


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", w.DWORD), ("scanCode", w.DWORD), ("flags", w.DWORD), ("time", w.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", w.WORD), ("wScan", w.WORD), ("dwFlags", w.DWORD), ("time", w.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", w.LONG), ("dy", w.LONG), ("mouseData", w.DWORD), ("dwFlags", w.DWORD), ("time", w.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", w.DWORD), ("u", _INPUTUNION)]


user32.SetWindowsHookExW.argtypes = (ctypes.c_int, HOOKPROC, w.HINSTANCE, w.DWORD)
user32.SetWindowsHookExW.restype = w.HHOOK
user32.CallNextHookEx.argtypes = (w.HHOOK, ctypes.c_int, w.WPARAM, w.LPARAM)
user32.CallNextHookEx.restype = LRESULT
user32.UnhookWindowsHookEx.argtypes = (w.HHOOK,)
user32.SendInput.argtypes = (w.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype = w.UINT
user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.MapVirtualKeyW.argtypes = (w.UINT, w.UINT)
user32.MapVirtualKeyW.restype = w.UINT
user32.GetMessageW.argtypes = (ctypes.POINTER(w.MSG), w.HWND, w.UINT, w.UINT)
user32.GetMessageW.restype = w.BOOL
user32.PostThreadMessageW.argtypes = (w.DWORD, w.UINT, w.WPARAM, w.LPARAM)
kernel32.GetModuleHandleW.argtypes = (w.LPCWSTR,)
kernel32.GetModuleHandleW.restype = w.HMODULE


def send_keys(seq, tag=TAG):
    """Press keys as if typed: seq is [(vk, up)], sent in one go. Returns how many went in."""
    arr = (INPUT * len(seq))()
    for i, (vk, up) in enumerate(seq):
        flags = (KEYEVENTF_KEYUP if up else 0) | (KEYEVENTF_EXTENDEDKEY if vk in EXTENDED else 0)
        arr[i].type = INPUT_KEYBOARD
        arr[i].u.ki = KEYBDINPUT(vk, user32.MapVirtualKeyW(vk, 0), flags, 0, tag)
    return user32.SendInput(len(seq), arr, ctypes.sizeof(INPUT))


def is_down(vk):
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def combo_down():
    """True while any Ctrl or Win key is physically down."""
    return any(is_down(vk) for vk in COMBO)


class Keys:
    """on_event(name, info) runs on the dispatcher thread: "start", "lock", "stop" (info {"held": seconds,
    "locked": bool}), "cancel" (info "key" or "esc")."""
    IDLE, HELD, LOCKED = "idle", "held", "locked"

    def __init__(self, on_event):
        self.on_event = on_event
        self.state = self.IDLE
        self.ctrl, self.win = set(), set()
        self.blocked = False       # a hold just ended: no new start until both keys are up
        self.rearmed = False       # locked: both keys have come up since, so the next Ctrl+Win means stop
        self.swallowed = set()     # keys whose press was swallowed: their repeats and their release are too
        self.t0 = 0.0
        self.lock = threading.Lock()
        self.events = queue.Queue()
        self.tid = None
        self.hook = None
        self._proc = HOOKPROC(self._hook)      # held here: Windows calls it for as long as the hook lives
        self.ready = threading.Event()
        threading.Thread(target=self._dispatch, daemon=True, name="flow-keys-events").start()
        threading.Thread(target=self._run, daemon=True, name="flow-keys-hook").start()
        threading.Thread(target=self._watch, daemon=True, name="flow-keys-watch").start()
        self.ready.wait(3)

    # ---- the hook thread
    def _run(self):
        self.tid = kernel32.GetCurrentThreadId()
        self._install()
        self.ready.set()
        msg = w.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_APP:
                self._install()
        if self.hook:
            user32.UnhookWindowsHookEx(self.hook)

    def _install(self):
        if self.hook:
            user32.UnhookWindowsHookEx(self.hook)
        self.hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, kernel32.GetModuleHandleW(None), 0)
        if not self.hook:
            log.error("keyboard hook refused (error %s)", ctypes.get_last_error())

    def _hook(self, code, wparam, lparam):
        if code == 0:
            k = KBDLLHOOKSTRUCT.from_address(lparam)
            if k.dwExtraInfo != TAG:
                try:
                    if self._key(k.vkCode, wparam in (WM_KEYDOWN, WM_SYSKEYDOWN)):
                        return 1
                except Exception:  # noqa: BLE001  (a bug here must never eat his keys)
                    log.exception("key hook")
        return user32.CallNextHookEx(None, code, wparam, lparam)

    def _key(self, vk, down):
        """True swallows the key."""
        now = time.monotonic()
        with self.lock:
            if vk in self.swallowed:
                if not down:
                    self.swallowed.discard(vk)
                return True
            if vk in CTRL or vk in WIN:
                group = self.ctrl if vk in CTRL else self.win
                if down:
                    group.add(vk)
                    self._drop_stale(vk)
                    if self.ctrl and self.win:
                        if self.state == self.IDLE and not self.blocked:
                            self.state, self.t0 = self.HELD, now
                            self._emit("mask")
                            self._emit("start")
                        elif self.state == self.LOCKED and self.rearmed:
                            self.state, self.blocked = self.IDLE, True
                            self._emit("mask")
                            self._emit("stop", {"held": now - self.t0, "locked": True})
                else:
                    group.discard(vk)
                    if self.state == self.HELD and not (self.ctrl and self.win):
                        self.state, self.blocked = self.IDLE, True
                        self._emit("stop", {"held": now - self.t0, "locked": False})
                    if not self.ctrl and not self.win:
                        self.blocked = False
                        if self.state == self.LOCKED:
                            self.rearmed = True
                return False
            if not down:
                return False
            if self.state == self.HELD:
                if vk == VK_SPACE:
                    self.state, self.rearmed = self.LOCKED, False
                    self.swallowed.add(vk)
                    self._emit("lock")
                    return True
                self.state, self.blocked = self.IDLE, True
                if vk == VK_ESCAPE:
                    self.swallowed.add(vk)
                    self._emit("cancel", "esc")
                    return True
                self._emit("cancel", "key")
                return False
            if self.state == self.LOCKED and vk == VK_ESCAPE:
                self.state = self.IDLE
                self.swallowed.add(vk)
                self._emit("cancel", "esc")
                return True
            return False

    def _drop_stale(self, current):
        """Forget a Ctrl or Win whose release was never seen (the screen locked mid-press)."""
        for group in (self.ctrl, self.win):
            for vk in list(group):
                if vk != current and not is_down(vk):
                    group.discard(vk)

    def _emit(self, name, info=None):
        self.events.put((name, info))

    # ---- the other two threads
    def _dispatch(self):
        while True:
            name, info = self.events.get()
            if name is None:
                return
            if name == "mask":
                send_keys([(VK_MASK, False), (VK_MASK, True)])
                continue
            try:
                self.on_event(name, info)
            except Exception:  # noqa: BLE001
                log.exception("on %s", name)

    def _watch(self):
        last_install, up_count = time.monotonic(), 0
        while True:
            time.sleep(0.1)
            if self.state == self.HELD:
                up_count = 0 if combo_down() else up_count + 1
                if up_count >= 3:                       # 0.3 s with both keys up and no release seen
                    with self.lock:
                        if self.state == self.HELD:
                            self.state, self.blocked = self.IDLE, False
                            self.ctrl.clear()
                            self.win.clear()
                            self._emit("stop", {"held": time.monotonic() - self.t0, "locked": False})
                    up_count = 0
            else:
                up_count = 0
            if self.state == self.IDLE and self.tid and time.monotonic() - last_install > 60:
                user32.PostThreadMessageW(self.tid, WM_APP, 0, 0)
                last_install = time.monotonic()

    def reset(self):
        """Back to waiting (a take the app ended itself, at its time limit)."""
        with self.lock:
            if self.state != self.IDLE:
                self.state, self.blocked = self.IDLE, combo_down()

    def stop(self):
        self._emit(None)
        if self.tid:
            user32.PostThreadMessageW(self.tid, WM_QUIT, 0, 0)
