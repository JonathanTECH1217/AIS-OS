"""Make tap-stage.html: stage.html with extra functions exported on window.__ds (nothing else changes)."""
import os
SP = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(SP, "stage.html"), encoding="utf-8", newline="").read()
needle = "window.__ds = { "
assert src.count(needle) == 1, src.count(needle)
extra = ("window.__ds = { growNote: growNote, cutAt: cutAt, applyLength: applyLength, shove: shove, nudgeContact: nudgeContact, "
         "addBarToSelected: addBarToSelected, setSel: setSel, clearMarks: clearMarks, dropAt: dropAt, tapPause: tapPause, tapSlot: tapSlot, "
         "tapMark: tapMark, tapTarget: tapTarget, selected: selected, noteMenu: noteMenu, setSlots: setSlots, redrawLine: redrawLine, "
         "lenText: lenText, deleteSelected: deleteSelected, nudge: nudge, lineEnd: lineEnd, snapSlots: snapSlots, ")
out = src.replace(needle, extra, 1)
open(os.path.join(SP, "tap-stage.html"), "w", encoding="utf-8", newline="").write(out)
print("wrote tap-stage.html", len(out))
