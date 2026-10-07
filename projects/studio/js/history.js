// Undo / redo: a full copy of the short per edit (a short is small, so a copy costs well under a millisecond).
// Edits with the same key within 1.2 s merge into one step (nudges, number drags, typing). One drag = one step.
// The Edit menu names the step ("Undo Ripple Delete").
import { S, emit } from "./store.js";
import { clone } from "./model/doc.js";

const CAP = 100;
const MERGE_MS = 1200;
let undoStack = [], redoStack = [];
let last = { key: null, t: 0 };
let dragPre = null, dragLabel = "", dragChanged = false;

export function reset() { undoStack = []; redoStack = []; last = { key: null, t: 0 }; dragPre = null; emit("doc"); }

function push(label, before, selBefore, key) {
  const now = performance.now();
  if (key && last.key === key && now - last.t < MERGE_MS && undoStack.length) {
    last.t = now;
    undoStack[undoStack.length - 1].label = label;
  } else {
    undoStack.push({ label, doc: before, sel: selBefore });
    if (undoStack.length > CAP) undoStack.shift();
    last = { key, t: now };
  }
  redoStack = [];
}

// Run fn on a copy of the short; keep it (and an undo step) when fn reports ok.
export function commit(label, fn, { key = null, silent = false } = {}) {
  if (!S.doc) return { ok: false, reason: "Open a short first." };
  const before = S.doc;
  const draft = clone(before);
  const res = fn(draft) || { ok: true };
  if (res.ok === false) return res;
  if (JSON.stringify(draft) === JSON.stringify(before)) return res;
  push(label, before, new Set(S.sel), key);
  S.doc = draft;
  if (!silent) emit("doc");
  return res;
}

// Drags: every move recomputes from the pre-drag copy, so nothing accumulates; Esc puts the copy back.
export function beginDrag(label) { dragPre = S.doc; dragLabel = label; dragChanged = false; }
export function dragTo(fn) {
  if (!dragPre) return { ok: false };
  const draft = clone(dragPre);
  const res = fn(draft) || { ok: true };
  if (res.ok === false) return res;
  S.doc = draft;
  dragChanged = true;
  emit("doc");
  return res;
}
export function endDrag() {
  if (!dragPre) return;
  if (dragChanged && JSON.stringify(S.doc) !== JSON.stringify(dragPre)) push(dragLabel, dragPre, new Set(S.sel), null);
  else S.doc = dragPre;
  dragPre = null;
  emit("doc");
}
export function cancelDrag() { if (dragPre) { S.doc = dragPre; dragPre = null; emit("doc"); } }
export function dragging() { return !!dragPre; }

export function undo() {
  if (!undoStack.length) return false;
  const e = undoStack.pop();
  redoStack.push({ label: e.label, doc: S.doc, sel: new Set(S.sel) });
  S.doc = e.doc;
  S.sel = new Set([...e.sel].filter((id) => S.doc.clips.some((c) => c.id === id)));
  last = { key: null, t: 0 };
  emit("doc"); emit("sel");
  return true;
}

export function redo() {
  if (!redoStack.length) return false;
  const e = redoStack.pop();
  undoStack.push({ label: e.label, doc: S.doc, sel: new Set(S.sel) });
  S.doc = e.doc;
  S.sel = new Set([...e.sel].filter((id) => S.doc.clips.some((c) => c.id === id)));
  emit("doc"); emit("sel");
  return true;
}

export function undoLabel() { return undoStack.length ? undoStack[undoStack.length - 1].label : null; }
export function redoLabel() { return redoStack.length ? redoStack[redoStack.length - 1].label : null; }
export function depth() { return { undo: undoStack.length, redo: redoStack.length }; }
