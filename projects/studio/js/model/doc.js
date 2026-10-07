// The short (sequence) document: shape, defaults, and read helpers. Every time is a whole frame at 30 fps.
// Clip times: `start` on the timeline; `in`/`out` on the source's own frames (text, shape, image: in = 0).
// Keyframe `t` is on the same source frames as in/out, so trims and slips carry keyframes with the content.
// Shared with scripts/studio_render.py, which reads the same file.

export const FPS = 30;
export const W = 1080, H = 1920;
export const FX_DEFAULTS = { posX: 540, posY: 960, scale: 100, rot: 0, opacity: 100, volume: 0 };
export const VISUAL = new Set(["video", "image", "text", "shape"]);

export function clone(o) { return structuredClone(o); }

export function clipLen(c) { return c.out - c.in; }
export function clipEnd(c) { return c.start + (c.out - c.in); }
export function trackOf(doc, id) { return doc.tracks.find((t) => t.id === id); }
export function clipById(doc, id) { return doc.clips.find((c) => c.id === id); }
export function isVisual(c) { return VISUAL.has(c.type); }
export function isAudio(c) { return c.type === "audio"; }

export function clipsOn(doc, trackId) {
  return doc.clips.filter((c) => c.track === trackId).sort((a, b) => a.start - b.start);
}

export function seqEnd(doc) {
  let e = 0;
  for (const c of doc.clips) e = Math.max(e, clipEnd(c));
  return e;
}

export function videoTracks(doc) { return doc.tracks.filter((t) => t.kind === "video"); }
export function audioTracks(doc) { return doc.tracks.filter((t) => t.kind === "audio"); }

// top-to-bottom order is the tracks array; drawing order is bottom video track first
export function drawOrder(doc) { return videoTracks(doc).slice().reverse(); }

export function newId(doc, prefix = "c") {
  const used = new Set([...doc.clips.map((c) => c.id), ...(doc.transitions || []).map((t) => t.id),
    ...(doc.markers || []).map((m) => m.id)]);
  let n = used.size + 1;
  while (used.has(prefix + n)) n += 1;
  return prefix + n;
}

export function newLink(doc) {
  const used = new Set(doc.clips.map((c) => c.link).filter(Boolean));
  let n = used.size + 1;
  while (used.has("L" + n)) n += 1;
  return "L" + n;
}

// Linked partners (same `link` group) move, trim and split together unless Alt is held (G31).
export function withLinked(doc, ids, alt = false) {
  const set = new Set(ids);
  if (alt) return [...set];
  for (const id of ids) {
    const c = clipById(doc, id);
    if (!c || !c.link) continue;
    for (const o of doc.clips) if (o.link === c.link) set.add(o.id);
  }
  return [...set];
}

export function prop(c, name) {
  const p = c.fx && c.fx[name];
  if (!p) return { v: FX_DEFAULTS[name] };
  return p;
}

export function normalize(doc) {
  doc.v = doc.v || 1;
  doc.fps = FPS; doc.w = W; doc.h = H;
  doc.tracks = doc.tracks || [];
  doc.clips = doc.clips || [];
  doc.transitions = doc.transitions || [];
  doc.markers = doc.markers || [];
  doc.range = doc.range || { in: null, out: null };
  // colors come from the palette every short uses (S.config); an old short's own `hl` is ignored (2026-09-30)
  doc.captions = Object.assign({ on: true, size: 110, y: 1340, bord: 7, upper: true, evRev: 0, events: [] },
    doc.captions || {});
  if (!doc.tracks.some((t) => t.kind === "caption")) doc.tracks.unshift({ id: "C", kind: "caption" });
  for (const c of doc.clips) {
    c.fx = c.fx || {};
    if (c.on === undefined) c.on = true;
    if (isAudio(c)) { c.fadeIn = c.fadeIn || 0; c.fadeOut = c.fadeOut || 0; }
  }
  for (const t of doc.tracks) {
    if (t.mute === undefined) t.mute = false;
    if (t.solo === undefined) t.solo = false;
    if (t.lock === undefined) t.lock = false;
    if (t.hide === undefined) t.hide = false;
  }
  return doc;
}

// Source length in frames for media clips (Infinity for generated clips).
export function sourceFrames(c, lib) {
  if (c.type === "text" || c.type === "shape" || c.type === "image") return Infinity;
  const a = lib && lib.asset(c.asset);
  if (!a || !a.duration) return Infinity;
  return Math.floor(a.duration * FPS);
}

// Base size before scale: video fits inside the frame; images keep their pixels unless larger than the frame.
export function baseSize(c, lib, measureText) {
  if (c.type === "shape") return { w: c.shape.w, h: c.shape.h };
  if (c.type === "text") return measureText ? measureText(c) : { w: 600, h: 140 };
  const a = lib && lib.asset(c.asset);
  const sw = (a && a.w) || W, sh = (a && a.h) || H;
  if (c.type === "image" && sw <= W && sh <= H) return { w: sw, h: sh };
  const k = Math.min(W / sw, H / sh);
  return { w: sw * k, h: sh * k };
}

export function fmtTC(f, withFrames = true) {
  f = Math.max(0, Math.round(f));
  const s = Math.floor(f / FPS), fr = f % FPS;
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), ss = s % 60;
  const base = (h ? h + ":" + String(m).padStart(2, "0") : m) + ":" + String(ss).padStart(2, "0");
  return withFrames ? base + ":" + String(fr).padStart(2, "0") : base;
}

export function fmtLen(f) {
  const s = Math.round(f / FPS);
  return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
}
