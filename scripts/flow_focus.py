"""Is the cursor in a text box? For Monarc Flow (2026-10-03): when it isn't, the words also show in a card he can click
to copy (Jonathan: "nothing gets pasted into a text box. I want the text to be displayed as a copyable window").

Asks Windows UI Automation (the layer screen readers use) about the element that has the keyboard:
  a value it can change (ValuePattern, not read-only)            a text box: yes
  a read-only value                                              no (a web page with no box picked)
  no value, but an Edit or Document with text (Word, a terminal) yes
  anything else (the desktop, a list, a button)                  no
The look starts the moment he lets go, beside the writing, so it adds no wait. It runs on a thread of its own with
COM set up. An app that hangs answers nothing: after the timeout the answer is None ("not sure"), which shows the card,
and the next look gets a fresh thread.
"""
import logging
import queue
import threading

log = logging.getLogger("flow")
EDIT, DOCUMENT = 50004, 50030


class Focus:
    def __init__(self):
        self._q = None
        self._start()

    def _start(self):
        self._q = queue.Queue()
        threading.Thread(target=self._run, args=(self._q,), daemon=True, name="flow-focus").start()

    def _run(self, q):
        try:
            import comtypes
            import comtypes.client
            comtypes.CoInitialize()
            comtypes.client.GetModule("UIAutomationCore.dll")
            from comtypes.gen import UIAutomationClient as U
            uia = comtypes.client.CreateObject(U.CUIAutomation, interface=U.IUIAutomation)
        except Exception as e:  # noqa: BLE001
            log.warning("UI Automation unavailable: %s", e)
            uia = U = None
        while True:
            box = q.get()
            if uia is None:
                box.put((None, "no UI Automation"))
                continue
            try:
                box.put(self._look(uia, U))
            except Exception as e:  # noqa: BLE001
                box.put((None, f"error {type(e).__name__}"))

    @staticmethod
    def _look(uia, U):
        el = uia.GetFocusedElement()
        kind = el.CurrentControlType
        what = f"{kind} {el.CurrentFrameworkId or '-'} {el.CurrentClassName or '-'}"
        vp = el.GetCurrentPattern(U.UIA_ValuePatternId)
        if vp:
            ro = bool(vp.QueryInterface(U.IUIAutomationValuePattern).CurrentIsReadOnly)
            return (not ro, what + (" read-only" if ro else " editable"))
        if kind in (EDIT, DOCUMENT) and el.GetCurrentPattern(U.UIA_TextPatternId):
            return (True, what + " text")
        return (False, what)

    def ask(self):
        """Start a look now. answer.get(timeout) -> (True, False or None, what it found)."""
        box = queue.Queue(maxsize=1)
        self._q.put(box)
        return Answer(box, self)


class Answer:
    def __init__(self, box, focus):
        self.box, self.focus = box, focus

    def get(self, timeout=0.4):
        try:
            return self.box.get(timeout=timeout)
        except queue.Empty:
            self.focus._start()            # that thread is stuck in a hung app; the next look gets a new one
            return (None, "no answer")
