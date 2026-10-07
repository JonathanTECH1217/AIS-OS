"""Paste for Monarc Flow (2026-10-03): put the text on the clipboard, press Ctrl+V for him, put his clipboard back.

What he had copied is saved first (text, rich text, web text, pictures, copied files) and put back after a short wait
(restore_clipboard_ms in projects/flow/config.json), unless he copied something new in the meantime. The text and the
put-back copy both carry Windows' "leave me out" marks, so clipboard history (Win+V) does not fill up with takes.

A window run as administrator can't take keys from a normal program, so nothing lands there; the text is still in
the history file and under Copy last dictation in the tray menu.
"""
import ctypes
import ctypes.wintypes as w
import time

import flow_keys as fk

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

CF_UNICODETEXT, CF_LOCALE, CF_HDROP, CF_DIB, CF_DIBV5 = 13, 16, 15, 8, 17
KEEP_IDS = {CF_UNICODETEXT, CF_LOCALE, CF_HDROP, CF_DIB, CF_DIBV5}
KEEP_NAMES = {"HTML Format", "Rich Text Format", "PNG", "image/png", "Preferred DropEffect", "Shell IDList Array",
              "FileNameW", "FileName"}
PRIVATE = ("ExcludeClipboardContentFromMonitorProcessing", "CanIncludeInClipboardHistory", "CanUploadToCloudClipboard")
LIMIT = 64 * 1024 * 1024          # one saved format at most; a bigger one is left out
GMEM_MOVEABLE = 0x0002
HWND_MESSAGE = w.HWND(-3)

user32.OpenClipboard.argtypes = (w.HWND,)
user32.OpenClipboard.restype = w.BOOL
user32.CloseClipboard.restype = w.BOOL
user32.EmptyClipboard.restype = w.BOOL
user32.EnumClipboardFormats.argtypes = (w.UINT,)
user32.EnumClipboardFormats.restype = w.UINT
user32.GetClipboardData.argtypes = (w.UINT,)
user32.GetClipboardData.restype = w.HANDLE
user32.SetClipboardData.argtypes = (w.UINT, w.HANDLE)
user32.SetClipboardData.restype = w.HANDLE
user32.RegisterClipboardFormatW.argtypes = (w.LPCWSTR,)
user32.RegisterClipboardFormatW.restype = w.UINT
user32.GetClipboardFormatNameW.argtypes = (w.UINT, w.LPWSTR, ctypes.c_int)
user32.GetClipboardFormatNameW.restype = ctypes.c_int
user32.GetClipboardSequenceNumber.restype = w.DWORD
user32.CreateWindowExW.argtypes = (w.DWORD, w.LPCWSTR, w.LPCWSTR, w.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, w.HWND, w.HMENU, w.HINSTANCE, w.LPVOID)
user32.CreateWindowExW.restype = w.HWND
user32.DestroyWindow.argtypes = (w.HWND,)
kernel32.GlobalAlloc.argtypes = (w.UINT, ctypes.c_size_t)
kernel32.GlobalAlloc.restype = w.HGLOBAL
kernel32.GlobalLock.argtypes = (w.HGLOBAL,)
kernel32.GlobalLock.restype = w.LPVOID
kernel32.GlobalUnlock.argtypes = (w.HGLOBAL,)
kernel32.GlobalSize.argtypes = (w.HGLOBAL,)
kernel32.GlobalSize.restype = ctypes.c_size_t
kernel32.GlobalFree.argtypes = (w.HGLOBAL,)


def _window():
    """A hidden window to own the clipboard: Windows refuses SetClipboardData after EmptyClipboard with no owner."""
    return user32.CreateWindowExW(0, "STATIC", None, 0, 0, 0, 0, 0, HWND_MESSAGE, None, None, None)


def _open(hwnd, tries=25):
    for _ in range(tries):                 # another program may hold it for a moment
        if user32.OpenClipboard(hwnd):
            return True
        time.sleep(0.02)
    return False


def _keep(fmt):
    if fmt in KEEP_IDS:
        return True
    if fmt < 0xC000:                       # the other built-in formats are handles, not bytes
        return False
    buf = ctypes.create_unicode_buffer(256)
    return user32.GetClipboardFormatNameW(fmt, buf, 256) > 0 and buf.value in KEEP_NAMES


def _save():
    saved, fmt = [], 0
    while True:
        fmt = user32.EnumClipboardFormats(fmt)
        if not fmt:
            return saved
        if not _keep(fmt):
            continue
        h = user32.GetClipboardData(fmt)
        size = kernel32.GlobalSize(h) if h else 0
        if not size or size > LIMIT:
            continue
        p = kernel32.GlobalLock(h)
        if not p:
            continue
        try:
            saved.append((fmt, ctypes.string_at(p, size)))
        finally:
            kernel32.GlobalUnlock(h)


def _put(fmt, data):
    h = kernel32.GlobalAlloc(GMEM_MOVEABLE, max(1, len(data)))
    if not h:
        return False
    p = kernel32.GlobalLock(h)
    ctypes.memmove(p, data, len(data))
    kernel32.GlobalUnlock(h)
    if not user32.SetClipboardData(fmt, h):
        kernel32.GlobalFree(h)
        return False
    return True                            # Windows owns it now


def _put_text(text):
    return _put(CF_UNICODETEXT, (text.replace("\r\n", "\n").replace("\n", "\r\n") + "\0").encode("utf-16-le"))


def _mark_private():
    for name in PRIVATE:
        _put(user32.RegisterClipboardFormatW(name), b"\0\0\0\0")


def paste(text, restore_ms=400, on_sent=None):
    """Paste text where the cursor is. False when the clipboard could not be opened."""
    hwnd = _window()
    try:
        if not _open(hwnd):
            return False
        try:
            saved = _save()
            user32.EmptyClipboard()
            _put_text(text)
            _mark_private()
        finally:
            user32.CloseClipboard()
        seq = user32.GetClipboardSequenceNumber()
        fk.send_keys([(fk.VK_CONTROL, False), (fk.VK_V, False), (fk.VK_V, True), (fk.VK_CONTROL, True)])
        if on_sent:
            on_sent()
        time.sleep(restore_ms / 1000)
        if user32.GetClipboardSequenceNumber() != seq:
            return True                    # he copied something new meanwhile: leave it be
        if _open(hwnd):
            try:
                user32.EmptyClipboard()
                for fmt, data in saved:
                    _put(fmt, data)
                if saved:
                    _mark_private()        # it is already in his history once
            finally:
                user32.CloseClipboard()
        return True
    finally:
        user32.DestroyWindow(hwnd)


def copy_text(text):
    """An ordinary copy (Copy last dictation): it shows in clipboard history like any other."""
    hwnd = _window()
    try:
        if not _open(hwnd):
            return False
        try:
            user32.EmptyClipboard()
            return _put_text(text)
        finally:
            user32.CloseClipboard()
    finally:
        user32.DestroyWindow(hwnd)


def read_text():
    """The clipboard's text, or None (tests)."""
    if not _open(None):
        return None
    try:
        h = user32.GetClipboardData(CF_UNICODETEXT)
        if not h:
            return None
        p = kernel32.GlobalLock(h)
        try:
            return ctypes.wstring_at(p)
        finally:
            kernel32.GlobalUnlock(h)
    finally:
        user32.CloseClipboard()
