"""Monarc Flow checks (2026-10-03).

  python projects/flow/tests/run.py                   all of them
  python projects/flow/tests/run.py rules speech      just these (rules, speech, long, card, keys)

rules   the cleanup table (flow_clean.clean)
speech  Parakeet's test clip through load, write and cleanup: its words, in under 1.2 s
long    a 50 s hands-free take (the clip six times, a second's pause between) played 4 times as fast: pieces are
        written while it plays, and the words are out under 1.5 s after it ends
card    the copy card (words with no text box to land in): where the cursor is gets an answer; the card shows; a
        real click on it copies its words without taking the cursor; then it fades and goes. Moves the mouse for
        about 2 s and puts it back; clicks only once the pointer is on the card.
keys    the whole path with real key presses sent by this test, into a small test window, against a test copy of
        Monarc Flow (FLOW_INSTANCE MonarcFlowTest, the clip for a mic at 4 times speed, no sounds, its own config,
        history and log):
          hold 2.2 s     the clip's words land in the window, Start stays shut, the clipboard comes back
          a tap          nothing
          Ctrl+Win+0x88  cancelled (0x88 is a key code no key uses), and the key still reaches the window
          Space lock     Space never reaches the window; Ctrl+Win again stops it and the words land
        His own copy, if running, is stopped first and started again after: its hook would hear the test keys too.
        Skipped when the test window can't get the cursor, since the keys would land wherever it is.
"""
import ctypes
import ctypes.wintypes
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import flow_clean  # noqa: E402
import flow_mic  # noqa: E402

_loader = importlib.machinery.SourceFileLoader("flow_app", str(SCRIPTS / "flow.pyw"))
app = importlib.util.module_from_spec(importlib.util.spec_from_loader("flow_app", _loader))
_loader.exec_module(app)
CLIP = app.TEST_CLIP
PHRASE = "I don't wish to see it any more"
TEST_TAG = 0x54455354                     # "TEST": keys from this test, which the hook must treat as his own

FAILS, PASSES = [], [0]


def check(name, ok, detail=""):
    if ok:
        PASSES[0] += 1
        print(f"ok   {name}" + (f"  ({detail})" if detail else ""))
    else:
        FAILS.append(name)
        print(f"FAIL {name}  {detail}")


# ---------------------------------------------------------------- rules

RULES = [
    ("Um, I think we should call them.", "I think we should call them. "),
    ("So, um, I think, uh, we should go.", "So, I think we should go. "),
    ("I I think the the plan works.", "I think the plan works. "),
    ("I, I think it works.", "I think it works. "),
    ("I know that that works and he had had enough.", "I know that that works and he had had enough. "),
    ("It was very, very good.", "It was very, very good. "),
    ("The theory holds.", "The theory holds. "),
    ("Call 443 443 1234.", "Call 443 443 1234. "),
    ("uh-huh, that works.", "Uh-huh, that works. "),
    ("The ER was busy.", "The ER was busy. "),
    ("It was, um. Fine.", "It was. Fine. "),
    ("Uh", ""),
    ("Let's meet Tuesday. Scratch that. Let's meet Wednesday.", "Let's meet Wednesday. "),
    ("Let's meet Tuesday. Scratch that, let's do Wednesday.", "Let's do Wednesday. "),
    ("Scratch that.", ""),
    ("Hi Patrick, new line. Thanks for the call.", "Hi Patrick,\nThanks for the call. "),
    ("That works. New paragraph. Talk soon.", "That works.\n\nTalk soon. "),
    ("Best, new paragraph, Jonathan.", "Best,\n\nJonathan. "),
    ("New line. New line. Hello.", "\n\nHello. "),
    ("We have a new line of speakers.", "We have a new line of speakers. "),
    ("We install control four and savant for monarch build clients.",
     "We install Control4 and Savant for Monarc Build clients. "),
    ("Kaleidoscope and Josh AI with Lutron home works.", "Kaleidescape and Josh.ai with Lutron HomeWorks. "),
    ("We need control for the lights.", "We need control for the lights. "),
    ("It's fast — really fast.", "It's fast, really fast. "),
    ("i think i'm ready.", "I think I'm ready. "),
]


def test_rules():
    rules = flow_clean.compile_fixes(json.loads((ROOT / "projects" / "flow" / "words.json")
                                                .read_text(encoding="utf-8"))["fixes"])
    for said, want in RULES:
        got = flow_clean.clean(said, rules)
        check(f"rules: {said[:48]!r}", got == want, "" if got == want else f"got {got!r}, want {want!r}")
    check("rules: no trailing space when space_after is off", flow_clean.clean("Okay.", rules, False) == "Okay.")


# ---------------------------------------------------------------- speech and the long take

_rec = {}


def recognizer():
    if "rec" not in _rec:
        import studio_transcribe as stt
        _rec["rec"] = stt.load_recognizer(threads=4)
        stt.decode_batch(_rec["rec"], [(0.0, np.zeros(16000, np.float32))])
    return _rec["rec"]


def decode(samples):
    import studio_transcribe as stt
    x = np.concatenate([samples, np.zeros(4800, np.float32)])
    return " ".join(wd[2] for wd in stt.decode_batch(recognizer(), [(0.0, x)])[0]["words"])


def test_speech():
    x = flow_mic.read_wav(CLIP)
    recognizer()
    t = time.time()
    text = flow_clean.clean(decode(x))
    took = time.time() - t
    check("speech: the clip's words", PHRASE.lower() in text.lower() and "portrait" in text, text)
    check("speech: 7.4 s of talk written in under 1.2 s", took < 1.2, f"{took:.2f} s")


def test_long():
    clip = flow_mic.read_wav(CLIP)
    audio = np.concatenate([np.concatenate([clip, np.zeros(16000, np.float32)]) for _ in range(6)])
    recognizer()
    take = flow_mic.Take()
    pieces = []

    def counted(samples):
        pieces.append(len(samples) / 16000)
        return decode(samples)

    def feed():
        step = 400
        for i in range(0, len(audio), step):
            take.add(audio[i:i + step])
            time.sleep(0.025 / 4)
        take.end()

    out = {}
    worker = threading.Thread(target=lambda: out.update(r=flow_mic.write(take, counted)))
    worker.start()
    feed()
    t = time.time()
    worker.join()
    lag = time.time() - t
    text, heard = out["r"]
    check("long: speech found", heard)
    check("long: all six repeats written", text.count("portrait") == 6, f"{text.count('portrait')} found")
    check("long: written in pieces while it played", len(pieces) >= 3, f"pieces {[round(p, 1) for p in pieces]}")
    check("long: words out under 1.5 s after the end", lag < 1.5, f"{lag:.2f} s")


# ---------------------------------------------------------------- the keys, end to end

def test_keys():
    import tkinter as tk
    import flow_keys as fk
    import flow_paste as fp
    user32 = ctypes.windll.user32

    def press(*vks):
        fk.send_keys([(v, False) for v in vks], tag=TEST_TAG)

    def release(*vks):
        fk.send_keys([(v, True) for v in reversed(vks)], tag=TEST_TAG)

    def tap(vk):
        fk.send_keys([(vk, False), (vk, True)], tag=TEST_TAG)

    CTRL, WIN, SPACE, NOKEY = 0xA2, 0x5B, 0x20, 0x88

    root = tk.Tk()
    root.title("Monarc Flow test")
    root.geometry("760x220+240+240")
    root.attributes("-topmost", True)
    box = tk.Text(root, font=("Segoe UI", 11))
    box.pack(fill="both", expand=True)
    seen = []
    root.bind_all("<KeyPress>", lambda e: seen.append(e.keycode))

    def pump(seconds, until=None):
        end = time.time() + seconds
        while time.time() < end:
            root.update()
            if until and until():
                return True
            time.sleep(0.01)
        return bool(until and until())

    def text():
        return box.get("1.0", "end-1c")

    def ours():
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), ctypes.byref(pid))
        return pid.value == os.getpid()

    def clipboard_put(s):
        hwnd = fp._window()
        try:
            if fp._open(hwnd):
                try:
                    fp.user32.EmptyClipboard()
                    fp._put_text(s)
                    fp._mark_private()
                finally:
                    fp.user32.CloseClipboard()
        finally:
            fp.user32.DestroyWindow(hwnd)

    class LostCursor(Exception):
        pass

    def reset():
        box.delete("1.0", "end")
        seen.clear()
        box.focus_force()
        pump(0.2)
        if not ours():                    # never press keys into some other window
            raise LostCursor()

    # his own copy hears every key: stop it for the test, start it again after
    his = app.running()
    if his:
        app.stop_running()
        print("     (stopped his Monarc Flow for the test; it starts again after)")
    tmp = Path(tempfile.mkdtemp(prefix="flow-test-"))
    shutil.copy(ROOT / "projects" / "flow" / "config.json", tmp / "config.json")
    env = dict(os.environ, FLOW_INSTANCE="MonarcFlowTest", FLOW_CONFIG=str(tmp / "config.json"),
               FLOW_HISTORY=str(tmp / "history.jsonl"), FLOW_LOG=str(tmp / "flow.log"), FLOW_FAKE_MIC=str(CLIP),
               FLOW_FAKE_SPEED="4", FLOW_NO_SOUND="1")
    proc = subprocess.Popen([sys.executable, "-u", str(SCRIPTS / "flow.pyw")], env=env, cwd=str(ROOT),
                            stdout=subprocess.DEVNULL, stderr=open(tmp / "stderr.txt", "w"))
    flog = tmp / "flow.log"

    def logged(s):
        try:
            return s in flog.read_text(encoding="utf-8")
        except OSError:
            return False

    hwnd_save = fp._window()
    saved = []
    if fp._open(hwnd_save):
        try:
            saved = fp._save()
        finally:
            fp.user32.CloseClipboard()
    try:
        ready = pump(40, lambda: logged("ready"))
        check("keys: the test copy started and loaded Parakeet", ready, tail(flog))
        if not ready:
            return
        tap(NOKEY)                                    # input from this process lets its window take the cursor
        user32.SetForegroundWindow(int(root.wm_frame(), 16))
        if not pump(2, ours):
            print("SKIP keys: the test window could not get the cursor (click it and run again)")
            return

        # hold
        reset()
        clipboard_put("flow-test-sentinel")
        press(CTRL, WIN)
        pump(2.2)
        let_go = time.time()
        release(CTRL, WIN)
        got = pump(6, lambda: "portrait" in text())
        lag = time.time() - let_go
        check("keys: hold, the clip's words land in the window", got and PHRASE in text(), repr(text()[:120]))
        check("keys: hold, words land under 1.8 s after letting go", got and lag < 1.8, f"{lag:.2f} s")
        pump(0.6)
        check("keys: hold, Start stays shut (the window keeps the cursor)", ours())
        pump(0.6)
        check("keys: hold, his clipboard comes back", fp.read_text() == "flow-test-sentinel", repr(fp.read_text()))

        # a tap
        reset()
        press(CTRL, WIN)
        pump(0.08)
        release(CTRL, WIN)
        pump(2.0)
        check("keys: a tap pastes nothing", text() == "", repr(text()))
        check("keys: a tap leaves Start shut", ours())

        # cancel by another key
        reset()
        press(CTRL, WIN)
        pump(0.6)
        tap(NOKEY)
        pump(0.3)
        release(CTRL, WIN)
        pump(2.5)
        check("keys: Ctrl+Win plus another key pastes nothing", text() == "", repr(text()))
        check("keys: ... and that key still reaches the window", NOKEY in seen, f"seen {seen}")
        check("keys: ... and the take is logged as cancelled", logged("cancel (key)"))

        # hands-free
        reset()
        press(CTRL, WIN)
        pump(0.4)
        tap(SPACE)
        pump(0.2)
        release(CTRL, WIN)
        pump(3.0)
        check("keys: hands-free, still listening after letting go", text() == "" and logged("lock"), repr(text()))
        press(CTRL, WIN)
        stop_at = time.time()
        pump(0.05)
        release(CTRL, WIN)
        got = pump(6, lambda: "portrait" in text())
        lag = time.time() - stop_at
        check("keys: hands-free, Ctrl+Win again stops it and the words land", got and text().startswith("Well"),
              repr(text()[:120]))
        check("keys: hands-free, words land under 1.8 s after the stop", got and lag < 1.8, f"{lag:.2f} s")
        check("keys: hands-free, the Space never reached the window", SPACE not in seen, f"seen {seen}")
        pump(0.6)
        check("keys: hands-free, Start stays shut", ours())
    except LostCursor:
        check("keys: the test window kept the cursor (stopped early, no keys sent elsewhere)", False)
    finally:
        app.INSTANCE = "MonarcFlowTest"
        app.stop_running(5)
        app.INSTANCE = "MonarcFlow"
        if proc.poll() is None:
            proc.kill()
        root.destroy()
        if fp._open(hwnd_save):                        # his clipboard as it was before the test
            try:
                fp.user32.EmptyClipboard()
                for fmt, data in saved:
                    fp._put(fmt, data)
                if saved:
                    fp._mark_private()
            finally:
                fp.user32.CloseClipboard()
        fp.user32.DestroyWindow(hwnd_save)
        if his:
            app.launch()
        print(f"     (test copy's log: {flog})")


def test_card():
    """The copy card: shows, a click copies its words, then it fades and goes. Moves the mouse onto it for a moment
    (put back after); clicks only once the window under the pointer is the card itself."""
    import flow_keys as fk
    import flow_paste as fp
    from flow_focus import Focus
    from flow_pill import Pill
    user32 = ctypes.windll.user32
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:  # noqa: BLE001
        pass
    t = time.time()
    found, what = Focus().ask().get(5)
    check("card: where the cursor is, answered", found in (True, False, None) and what != "no answer",
          f"{found} {what}, {time.time() - t:.2f} s")
    words = "Card test: these words should land on the clipboard."
    hwnd_save = fp._window()
    saved = []
    if fp._open(hwnd_save):
        try:
            saved = fp._save()
        finally:
            fp.user32.CloseClipboard()
    was = ctypes.wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(was))
    pill = Pill()
    time.sleep(0.3)
    try:
        pill.show_card(words, "No text box here. Click to copy.", fp.copy_text)
        time.sleep(0.5)
        check("card: shows", pill.card and pill.card.shown)
        r = ctypes.wintypes.RECT()
        user32.GetWindowRect(pill.card.hwnd, ctypes.byref(r))
        x, y = (r.left + r.right) // 2, (r.top + r.bottom) // 2
        user32.SetCursorPos(x, y)
        time.sleep(0.25)
        under = user32.WindowFromPoint(ctypes.wintypes.POINT(x, y))
        if under != pill.card.hwnd:
            check("card: the pointer is on the card (no click sent elsewhere)", False, f"window {under}")
            return
        fg = user32.GetForegroundWindow()
        arr = (fk.INPUT * 2)()
        for i, flag in enumerate((0x0002, 0x0004)):          # left button down, up
            arr[i].type = 0
            arr[i].u.mi = fk.MOUSEINPUT(0, 0, 0, flag, 0, TEST_TAG)
        fk.user32.SendInput(2, arr, ctypes.sizeof(fk.INPUT))
        time.sleep(0.4)
        check("card: a click copies its words", fp.read_text() == words, repr(fp.read_text()))
        check("card: the click leaves the cursor where it was", user32.GetForegroundWindow() == fg)
        user32.SetCursorPos(was.x, was.y)
        deadline = time.time() + 4
        while pill.card.shown and time.time() < deadline:
            time.sleep(0.1)
        check("card: fades and goes after the copy", not pill.card.shown)
    finally:
        user32.SetCursorPos(was.x, was.y)
        pill.quit()
        if fp._open(hwnd_save):
            try:
                fp.user32.EmptyClipboard()
                for fmt, data in saved:
                    fp._put(fmt, data)
                if saved:
                    fp._mark_private()
            finally:
                fp.user32.CloseClipboard()
        fp.user32.DestroyWindow(hwnd_save)


def tail(path, n=8):
    try:
        return " | ".join(path.read_text(encoding="utf-8").strip().splitlines()[-n:])
    except OSError:
        return "(no log)"


TESTS = {"rules": test_rules, "speech": test_speech, "long": test_long, "card": test_card, "keys": test_keys}


def main():
    for name in sys.argv[1:] or list(TESTS):
        TESTS[name]()
    print(f"\n{PASSES[0]} passed, {len(FAILS)} failed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
