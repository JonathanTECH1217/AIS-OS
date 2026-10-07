// App state and a tiny change feed. Views subscribe by kind: doc, sel, playhead, tool, bin, view, play, save, layout.

export const S = {
  doc: null,              // the open short (see model/doc.js)
  baseRev: null,          // server revision the doc was loaded or last saved at
  sel: new Set(),         // selected clip ids
  selTransition: null,    // selected transition id
  selMarker: null,
  tool: "select",
  playhead: 0,            // timeline frame
  playing: false,
  snap: true,
  quality: localStorage.getItem("studio.quality") || "half",   // full | half | quarter
  playQuality: null,      // the quality a play started at: which file plays stays put until the next pause
  safe: false,
  scrub: false,
  shownProp: {},          // clip id -> fx name drawn in the clip's keyframe band
  bin: null,              // last /api/bin answer
  config: null,           // Studio settings from the server: {captionColors} (one palette for every short)
  configPending: false,   // a palette color is being picked or saved; the bin feed leaves S.config alone
  version: null,          // the server version this page loaded against
  updateReady: false,     // the server has a newer version: the top bar offers a reload
  selectedAsset: null,    // bin selection
  clipboard: null,
  genCaps: null,          // Generate captions in flight or just finished: {pid, state, msg, progress, error}
  saving: "saved",        // saved | saving | error | offline
  test: false,
};

const subs = new Map();

export function subscribe(kind, fn) {
  if (!subs.has(kind)) subs.set(kind, new Set());
  subs.get(kind).add(fn);
  return () => subs.get(kind).delete(fn);
}

let pending = new Set(), scheduled = false;
export function emit(kind, now = false) {
  if (now) { for (const fn of subs.get(kind) || []) fn(); return; }
  pending.add(kind);
  if (!scheduled) {
    scheduled = true;
    queueMicrotask(() => {
      scheduled = false;
      const kinds = pending; pending = new Set();
      for (const k of kinds) for (const fn of subs.get(k) || []) { try { fn(); } catch (e) { console.error(e); } }
    });
  }
}

export function selectOnly(ids) { S.sel = new Set(ids); S.selTransition = null; emit("sel"); }
export function selected() { return S.doc ? S.doc.clips.filter((c) => S.sel.has(c.id)) : []; }
