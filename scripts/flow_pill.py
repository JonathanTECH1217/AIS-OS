"""The pill and the copy card for Monarc Flow (2026-10-03), at the bottom center of the screen he is working on.

The pill:
  listening    moving sound bars, newest on the right; a small lock in front when hands-free
  writing      three soft dots
  a message    "Didn't catch that", "Ready", "No microphone", for a moment
It never takes the cursor and lets clicks fall through.

The card (Jonathan, 2026-10-03: "displayed as a copyable window for around five seconds and then slowly fade away"):
the words, when they had no text box to land in. A click anywhere on it copies them. It stays 5 s, then fades over
1.5 s; while the mouse is on it, it stays. It takes clicks but never the cursor, so the window he was in keeps it.

Both are see-through windows (Windows blends their soft edges and shadow over whatever is behind), drawn with Pillow
on a thread of their own, 30 times a second, only while one shows.
"""
import ctypes
import ctypes.wintypes as w
import logging
import queue
import threading
import time
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
log = logging.getLogger("flow")

WS_POPUP = 0x80000000
WS_EX_LAYERED, WS_EX_TRANSPARENT, WS_EX_TOPMOST = 0x00080000, 0x00000020, 0x00000008
WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE = 0x00000080, 0x08000000
ULW_ALPHA, AC_SRC_ALPHA = 2, 1
SW_HIDE, SW_SHOWNOACTIVATE = 0, 4
SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE = 0x0001, 0x0002, 0x0010
HWND_TOPMOST = w.HWND(-1)
PM_REMOVE = 1
MONITOR_DEFAULTTOPRIMARY = 1
WM_SETCURSOR, WM_MOUSEACTIVATE, WM_MOUSEMOVE, WM_LBUTTONUP, WM_MOUSELEAVE = 0x0020, 0x0021, 0x0200, 0x0202, 0x02A3
MA_NOACTIVATE, TME_LEAVE, IDC_HAND = 3, 0x0002, 32649

BARS = 13
SS = 3                        # drawn this many times larger, then shrunk: smooth edges
BG = (26, 26, 30, 242)
EDGE = (255, 255, 255, 34)
INK = (255, 255, 255, 255)
DIM = (176, 176, 186, 255)
GOOD = (134, 222, 156, 255)
CARD_LIFE, CARD_FADE = 5.0, 1.5
CARD_LINES = 6

WNDPROC = ctypes.WINFUNCTYPE(w.LPARAM, w.HWND, w.UINT, w.WPARAM, w.LPARAM)


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [("cbSize", w.UINT), ("style", w.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int), ("hInstance", w.HINSTANCE), ("hIcon", w.HICON),
                ("hCursor", w.HANDLE), ("hbrBackground", w.HBRUSH), ("lpszMenuName", w.LPCWSTR),
                ("lpszClassName", w.LPCWSTR), ("hIconSm", w.HICON)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [("BlendOp", ctypes.c_ubyte), ("BlendFlags", ctypes.c_ubyte), ("SourceConstantAlpha", ctypes.c_ubyte),
                ("AlphaFormat", ctypes.c_ubyte)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", w.DWORD), ("biWidth", w.LONG), ("biHeight", w.LONG), ("biPlanes", w.WORD),
                ("biBitCount", w.WORD), ("biCompression", w.DWORD), ("biSizeImage", w.DWORD),
                ("biXPelsPerMeter", w.LONG), ("biYPelsPerMeter", w.LONG), ("biClrUsed", w.DWORD),
                ("biClrImportant", w.DWORD)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", w.DWORD), ("rcMonitor", w.RECT), ("rcWork", w.RECT), ("dwFlags", w.DWORD)]


class TRACKMOUSEEVENT(ctypes.Structure):
    _fields_ = [("cbSize", w.DWORD), ("dwFlags", w.DWORD), ("hwndTrack", w.HWND), ("dwHoverTime", w.DWORD)]


user32.DefWindowProcW.argtypes = (w.HWND, w.UINT, w.WPARAM, w.LPARAM)
user32.DefWindowProcW.restype = w.LPARAM
user32.RegisterClassExW.argtypes = (ctypes.POINTER(WNDCLASSEXW),)
user32.RegisterClassExW.restype = w.ATOM
user32.CreateWindowExW.argtypes = (w.DWORD, w.LPCWSTR, w.LPCWSTR, w.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, w.HWND, w.HMENU, w.HINSTANCE, w.LPVOID)
user32.CreateWindowExW.restype = w.HWND
user32.UpdateLayeredWindow.argtypes = (w.HWND, w.HDC, ctypes.POINTER(w.POINT), ctypes.POINTER(w.SIZE), w.HDC,
                                       ctypes.POINTER(w.POINT), w.DWORD, ctypes.POINTER(BLENDFUNCTION), w.DWORD)
user32.UpdateLayeredWindow.restype = w.BOOL
user32.GetDC.argtypes = (w.HWND,)
user32.GetDC.restype = w.HDC
user32.ReleaseDC.argtypes = (w.HWND, w.HDC)
user32.ShowWindow.argtypes = (w.HWND, ctypes.c_int)
user32.SetWindowPos.argtypes = (w.HWND, w.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, w.UINT)
user32.PeekMessageW.argtypes = (ctypes.POINTER(w.MSG), w.HWND, w.UINT, w.UINT, w.UINT)
user32.TranslateMessage.argtypes = (ctypes.POINTER(w.MSG),)
user32.DispatchMessageW.argtypes = (ctypes.POINTER(w.MSG),)
user32.GetForegroundWindow.restype = w.HWND
user32.MonitorFromWindow.argtypes = (w.HWND, w.DWORD)
user32.MonitorFromWindow.restype = w.HMONITOR
user32.GetMonitorInfoW.argtypes = (w.HMONITOR, ctypes.POINTER(MONITORINFO))
user32.GetDpiForSystem.restype = w.UINT
user32.TrackMouseEvent.argtypes = (ctypes.POINTER(TRACKMOUSEEVENT),)
user32.LoadCursorW.argtypes = (w.HINSTANCE, w.LPVOID)
user32.LoadCursorW.restype = w.HANDLE
user32.SetCursor.argtypes = (w.HANDLE,)
gdi32.CreateCompatibleDC.argtypes = (w.HDC,)
gdi32.CreateCompatibleDC.restype = w.HDC
gdi32.CreateDIBSection.argtypes = (w.HDC, ctypes.POINTER(BITMAPINFOHEADER), w.UINT, ctypes.POINTER(ctypes.c_void_p),
                                   w.HANDLE, w.DWORD)
gdi32.CreateDIBSection.restype = w.HBITMAP
gdi32.SelectObject.argtypes = (w.HDC, w.HGDIOBJ)
gdi32.SelectObject.restype = w.HGDIOBJ
gdi32.DeleteObject.argtypes = (w.HGDIOBJ,)
kernel32.GetModuleHandleW.argtypes = (w.LPCWSTR,)
kernel32.GetModuleHandleW.restype = w.HMODULE


def _font(px, bold=False):
    for name in (("seguisb.ttf", "segoeuib.ttf") if bold else ()) + ("segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", px)
        except OSError:
            continue
    return ImageFont.load_default()


def _register(name, proc):
    wc = WNDCLASSEXW()
    wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
    wc.lpfnWndProc = proc
    wc.hInstance = kernel32.GetModuleHandleW(None)
    wc.lpszClassName = name
    user32.RegisterClassExW(ctypes.byref(wc))


class Surface:
    """One see-through window and the picture it shows."""

    def __init__(self, cls, ex):
        self.hwnd = user32.CreateWindowExW(ex, cls, "Monarc Flow", WS_POPUP, 0, 0, 1, 1, None, None,
                                           kernel32.GetModuleHandleW(None), None)
        if not self.hwnd:
            raise OSError(f"CreateWindowExW failed ({ctypes.get_last_error()})")
        self.mem = gdi32.CreateCompatibleDC(None)
        self.dib = self.bits = None
        self.size = (0, 0)
        self.shown = False

    def load(self, img):
        W, H = img.size
        if (W, H) != self.size:
            if self.dib:
                gdi32.DeleteObject(self.dib)
            bi = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), W, -H, 1, 32, 0, 0, 0, 0, 0, 0)
            bits = ctypes.c_void_p()
            self.dib = gdi32.CreateDIBSection(self.mem, ctypes.byref(bi), 0, ctypes.byref(bits), None, 0)
            gdi32.SelectObject(self.mem, self.dib)
            self.bits, self.size = bits, (W, H)
        a = np.asarray(img, dtype=np.uint16)
        alpha = a[..., 3]
        bgra = np.empty((H, W, 4), np.uint8)               # Windows wants blue-green-red, scaled by see-through
        for i, c in enumerate((2, 1, 0)):
            bgra[..., i] = (a[..., c] * alpha + 127) // 255
        bgra[..., 3] = alpha
        ctypes.memmove(self.bits, bgra.ctypes.data, W * H * 4)

    def show(self, x, y, alpha=255):
        W, H = self.size
        blend = BLENDFUNCTION(0, 0, max(0, min(255, int(alpha))), AC_SRC_ALPHA)
        screen = user32.GetDC(None)
        user32.UpdateLayeredWindow(self.hwnd, screen, ctypes.byref(w.POINT(x, y)), ctypes.byref(w.SIZE(W, H)),
                                   self.mem, ctypes.byref(w.POINT(0, 0)), 0, ctypes.byref(blend), ULW_ALPHA)
        user32.ReleaseDC(None, screen)
        if not self.shown:
            user32.ShowWindow(self.hwnd, SW_SHOWNOACTIVATE)
            user32.SetWindowPos(self.hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
            self.shown = True

    def hide(self):
        if self.shown:
            user32.ShowWindow(self.hwnd, SW_HIDE)
            self.shown = False


class Pill:
    def __init__(self):
        self.q = queue.Queue()
        self.peak = 0.0
        self.levels = deque([0.0] * BARS, maxlen=BARS)
        self.scale = (user32.GetDpiForSystem() or 96) / 96
        self.pill = self.card = None
        self.anchor = (0, 0)
        self._bases = {}
        self._pill_proc = WNDPROC(lambda h, m, wp, lp: user32.DefWindowProcW(h, m, wp, lp))
        self._card_proc = WNDPROC(self._card_msg)
        self._hand = user32.LoadCursorW(None, ctypes.c_void_p(IDC_HAND))
        self.hover = False
        self.clicked = False
        self.font = _font(int(13 * self.scale * SS), bold=True)
        self.card_head = _font(int(11.5 * self.scale * SS))
        self.card_body = _font(int(14 * self.scale * SS))
        threading.Thread(target=self._run, daemon=True, name="flow-pill").start()

    # ---- called from any thread
    def listening(self, locked=False):
        self.q.put(("listen", locked))

    def writing(self):
        self.q.put(("write", None))

    def say(self, text, seconds=1.8):
        self.q.put(("say", (text, seconds)))

    def hide(self):
        self.q.put(("hide", None))

    def show_card(self, text, head, on_copy):
        """The words in a card he can click to copy (on_copy(text) runs on the click)."""
        self.q.put(("card", (text, head, on_copy)))

    def quit(self):
        self.q.put(("quit", None))

    def level(self, rms):
        if rms > self.peak:
            self.peak = rms

    # ---- the windows' thread
    def _run(self):
        try:
            _register("MonarcFlowPill", self._pill_proc)
            _register("MonarcFlowCard", self._card_proc)
            self.pill = Surface("MonarcFlowPill", WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST
                                | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
            self.card = Surface("MonarcFlowCard", WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
        except Exception:  # noqa: BLE001
            log.exception("pill window")
            return
        mode, locked, text, until, t_mode, next_frame = None, False, "", 0.0, 0.0, 0.0
        card = None
        while True:
            busy = mode or card
            wait = max(0.0, next_frame - time.monotonic()) if busy else 0.1
            try:
                cmd, arg = self.q.get(timeout=wait)
            except queue.Empty:
                cmd, arg = None, None
            now = time.monotonic()
            if cmd == "quit":
                break
            if cmd == "listen":
                if mode != "listen":
                    self.levels.extend([0.0] * BARS)
                    self._aim()
                mode, locked = "listen", arg
                card = self._drop_card(card)
            elif cmd == "write":
                mode, t_mode = "write", now
            elif cmd == "say":
                if not mode:
                    self._aim()
                mode, text, until = "say", arg[0], now + arg[1]
            elif cmd == "hide":
                mode = None
            elif cmd == "card":
                mode = None
                self._aim()
                self.clicked = False
                card = {"text": arg[0], "head": arg[1], "on_copy": arg[2], "t0": now, "copied": False}
                self._draw_card(card)
            self._pump()
            if mode == "say" and now > until:
                mode = None
            if not mode:
                self.pill.hide()
            if not (mode or card) or not (now >= next_frame or cmd):
                continue
            next_frame = now + 1 / 30
            try:
                if mode:
                    self._frame(mode, locked, text, now - t_mode)
                if card:
                    card = self._card_frame(card, now)
            except Exception:  # noqa: BLE001
                log.exception("pill frame")
                mode, card = None, self._drop_card(card)
        for s in (self.pill, self.card):
            s.hide()

    def _pump(self):
        msg = w.MSG()
        while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def _aim(self):
        """Bottom center of the work area (the screen less the taskbar) of the monitor he is working on."""
        mon = user32.MonitorFromWindow(user32.GetForegroundWindow(), MONITOR_DEFAULTTOPRIMARY)
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        user32.GetMonitorInfoW(mon, ctypes.byref(mi))
        r = mi.rcWork
        self.anchor = ((r.left + r.right) // 2, r.bottom - int(18 * self.scale))

    def _px(self, v):
        return int(round(v * self.scale))

    # ---- the pill
    def _base(self, wide, high, margin, radius):
        """A dark rounded shape with its shadow, kept per size."""
        key = (wide, high, radius)
        if key not in self._bases:
            W, H = wide + 2 * margin, high + 2 * margin
            shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(shadow).rounded_rectangle((margin, margin + self._px(2), margin + wide - 1,
                                                      margin + high - 1 + self._px(2)), radius=radius,
                                                     fill=(0, 0, 0, 90))
            shadow = shadow.filter(ImageFilter.GaussianBlur(self._px(5)))
            big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
            ImageDraw.Draw(big).rounded_rectangle((margin * SS, margin * SS, (margin + wide) * SS - 1,
                                                   (margin + high) * SS - 1), radius=radius * SS, fill=BG,
                                                  outline=EDGE, width=max(1, SS))
            self._bases[key] = Image.alpha_composite(shadow, big.resize((W, H), Image.LANCZOS))
            if len(self._bases) > 24:
                self._bases.pop(next(iter(self._bases)))
        return self._bases[key]

    def _frame(self, mode, locked, text, t):
        high, margin = self._px(34), self._px(12)
        if mode == "listen":
            self.levels.append(self.peak)
            self.peak = 0.0
            wide = self._px(112 + (18 if locked else 0))
        elif mode == "write":
            wide = self._px(72)
        else:
            wide = self.font.getbbox(text)[2] // SS + self._px(36)
        W, H = wide + 2 * margin, high + 2 * margin
        over = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        cy = (margin + high / 2) * SS
        if mode == "listen":
            x = margin + self._px(18)
            if locked:
                self._lock(d, (x + self._px(5)) * SS, cy)
                x += self._px(18)
            bw, gap = self._px(3), self._px(3)
            lo, hi = self._px(3), self._px(18)
            for i, v in enumerate(self.levels):
                amt = min(1.0, max(0.0, (np.log10(v + 1e-7) + 3.2) / 2.4))
                h = (lo + (hi - lo) * amt) * SS
                left = (x + i * (bw + gap)) * SS
                d.rounded_rectangle((left, cy - h / 2, left + bw * SS, cy + h / 2), radius=bw * SS // 2, fill=INK)
        elif mode == "write":
            for i in range(3):
                a = 0.35 + 0.65 * (0.5 + 0.5 * np.sin(t * 7 - i * 0.9))
                r = self._px(3) * SS
                cx = (margin + wide / 2 + (i - 1) * self._px(12)) * SS
                d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, int(255 * a)))
        else:
            d.text(((margin + wide / 2) * SS, cy), text, font=self.font, fill=INK, anchor="mm")
        img = Image.alpha_composite(self._base(wide, high, margin, high // 2), over.resize((W, H), Image.LANCZOS))
        self.pill.load(img)
        ax, ay = self.anchor
        self.pill.show(ax - W // 2, ay - H)

    def _lock(self, d, cx, cy):
        s = self.scale * SS
        d.rounded_rectangle((cx - 5 * s, cy - 1 * s, cx + 5 * s, cy + 6 * s), radius=int(1.5 * s), fill=INK)
        d.arc((cx - 3.5 * s, cy - 7 * s, cx + 3.5 * s, cy + 1 * s), 180, 360, fill=INK, width=max(1, int(1.6 * s)))
        d.line((cx - 3.5 * s, cy - 3 * s, cx - 3.5 * s, cy), fill=INK, width=max(1, int(1.6 * s)))
        d.line((cx + 3.5 * s, cy - 3 * s, cx + 3.5 * s, cy), fill=INK, width=max(1, int(1.6 * s)))

    # ---- the card
    def _card_msg(self, hwnd, msg, wp, lp):
        try:
            if msg == WM_MOUSEACTIVATE:
                return MA_NOACTIVATE                     # a click copies; the window he was in keeps the cursor
            if msg == WM_SETCURSOR:
                user32.SetCursor(self._hand)
                return 1
            if msg == WM_MOUSEMOVE:
                if not self.hover:
                    self.hover = True
                    tme = TRACKMOUSEEVENT(ctypes.sizeof(TRACKMOUSEEVENT), TME_LEAVE, hwnd, 0)
                    user32.TrackMouseEvent(ctypes.byref(tme))
                return 0
            if msg == WM_MOUSELEAVE:
                self.hover = False
                return 0
            if msg == WM_LBUTTONUP:
                self.clicked = True
                return 0
        except Exception:  # noqa: BLE001
            log.exception("card message")
        return user32.DefWindowProcW(hwnd, msg, wp, lp)

    def _wrap(self, text, width):
        """Lines of text that fit width (drawn size), at most CARD_LINES; the last one cut with an ellipsis."""
        lines = []
        for para in text.strip().split("\n"):
            line = ""
            for word in para.split():
                trial = f"{line} {word}".strip()
                if line and self.card_body.getlength(trial) > width:
                    lines.append(line)
                    line = word
                else:
                    line = trial
            lines.append(line)
        if len(lines) > CARD_LINES:
            last = lines[CARD_LINES - 1]
            while last and self.card_body.getlength(last + " …") > width:
                last = last[:-1]
            lines = lines[:CARD_LINES - 1] + [last.rstrip() + " …"]
        return lines

    def _draw_card(self, card):
        pad, margin, radius = self._px(16), self._px(12), self._px(14)
        wide_max, wide_min = self._px(560), self._px(320)
        one_line = self.card_body.getlength(" ".join(card["text"].split())) / SS
        wide = int(min(wide_max, max(wide_min, one_line + 2 * pad)))
        lines = self._wrap(card["text"], (wide - 2 * pad) * SS)
        head_h, line_h, gap = self._px(16), self._px(21), self._px(8)
        high = pad + head_h + gap + line_h * len(lines) + pad - self._px(4)
        W, H = wide + 2 * margin, high + 2 * margin
        over = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        x, y = (margin + pad) * SS, (margin + pad) * SS
        head = "Copied" if card["copied"] else card["head"]
        d.text((x, y), head, font=self.card_head, fill=GOOD if card["copied"] else DIM, anchor="lt")
        y += (head_h + gap) * SS
        for ln in lines:
            d.text((x, y), ln, font=self.card_body, fill=INK, anchor="lt")
            y += line_h * SS
        img = Image.alpha_composite(self._base(wide, high, margin, radius), over.resize((W, H), Image.LANCZOS))
        self.card.load(img)

    def _card_frame(self, card, now):
        if self.clicked:
            self.clicked = False
            if not card["copied"]:
                try:
                    card["on_copy"](card["text"])
                except Exception:  # noqa: BLE001
                    log.exception("copy")
                card["copied"] = True
                self._draw_card(card)
                card["t0"] = now - (CARD_LIFE - 0.9)        # "Copied" for a moment, then the fade
        if self.hover and not card["copied"]:
            card["t0"] = now - (CARD_LIFE - 1.5)            # held while the mouse is on it
        age = now - card["t0"]
        if age >= CARD_LIFE + CARD_FADE:
            return self._drop_card(card)
        fade = max(0.0, (age - CARD_LIFE) / CARD_FADE)
        alpha = 255 * (1 - fade * fade * (3 - 2 * fade))     # eased, slow at both ends
        W, H = self.card.size
        ax, ay = self.anchor
        self.card.show(ax - W // 2, ay - H, alpha)
        return card

    def _drop_card(self, card):
        if self.card:
            self.card.hide()
        self.hover = False
        return None
