// Timeline edits as functions on a doc (the caller hands in a copy; history keeps the before). Each returns
// { ok, reason?, ids? }. ctx = { lib } gives source lengths. Locked tracks are never changed.
import { clipById, clipEnd, clipLen, clipsOn, clone, newId, newLink, sourceFrames, trackOf, FPS } from "./doc.js";

const fail = (reason) => ({ ok: false, reason });
const okr = (extra = {}) => Object.assign({ ok: true }, extra);

function locked(doc, trackId) { const t = trackOf(doc, trackId); return !t || t.lock; }
function unlockedTracks(doc) { return doc.tracks.filter((t) => t.kind !== "caption" && !t.lock).map((t) => t.id); }

function prevOn(doc, c) {
  let best = null;
  for (const o of doc.clips) if (o.track === c.track && o.id !== c.id && o.start < c.start && (!best || o.start > best.start)) best = o;
  return best;
}
function nextOn(doc, c) {
  let best = null;
  for (const o of doc.clips) if (o.track === c.track && o.id !== c.id && o.start > c.start && (!best || o.start < best.start)) best = o;
  return best;
}
function srcLen(c, ctx) { return sourceFrames(c, ctx && ctx.lib); }

// Drop transitions whose clips are gone or no longer meet at a cut.
export function cleanTransitions(doc) {
  doc.transitions = (doc.transitions || []).filter((t) => {
    const a = t.a && clipById(doc, t.a), b = t.b && clipById(doc, t.b);
    if (t.a && !a) return false;
    if (t.b && !b) return false;
    if (!a && !b) return false;
    if (a && b) return a.track === b.track && clipEnd(a) === b.start;
    return true;
  });
}

// Clear [a, b) on a track: remove, trim or split what is there (overwrite edit). except: ids left alone.
export function clearRange(doc, trackId, a, b, except = new Set()) {
  if (b <= a) return;
  const add = [];
  doc.clips = doc.clips.filter((c) => {
    if (c.track !== trackId || except.has(c.id)) return true;
    const s = c.start, e = clipEnd(c);
    if (e <= a || s >= b) return true;
    if (s >= a && e <= b) return false;
    if (s < a && e > b) {
      const right = clone(c);
      right.id = newId({ clips: doc.clips.concat(add), transitions: doc.transitions, markers: doc.markers });
      right.in = c.in + (b - s);
      right.start = b;
      if (right.fadeIn !== undefined) right.fadeIn = 0;
      c.out = c.in + (a - s);
      if (c.fadeOut !== undefined) c.fadeOut = 0;
      if (c.link) right.link = null;
      add.push(right);
      return true;
    }
    if (s < a) { c.out = c.in + (a - s); return true; }
    const d = b - s; c.in += d; c.start = b; return true;
  });
  doc.clips.push(...add);
}

function shiftAfter(doc, f, d, except = new Set(), tracks = null) {
  const allow = new Set(tracks || unlockedTracks(doc));
  for (const c of doc.clips) if (!except.has(c.id) && allow.has(c.track) && c.start >= f) c.start += d;
  for (const m of doc.markers || []) if (m.t >= f) m.t = Math.max(0, m.t + d);
}

// Clips on other tracks that straddle [a, b) (would collide when later material shifts left): ripple blocker.
// Clips on unlocked tracks overlapping [a, b): closing that stretch would collide with them (ripple blocker).
function blockers(doc, a, b, except) {
  const allow = new Set(unlockedTracks(doc));
  return doc.clips.filter((c) => !except.has(c.id) && allow.has(c.track) && clipEnd(c) > a && c.start < b);
}

// ------------------------------------------------------------------ move / place

// Move clips by dF frames and dRow tracks (rows count within the lead clip's kind). Overwrite on drop;
// insert (Ctrl) pushes everything at the drop point right instead.
export function moveClips(doc, ctx, ids, dF, dRow = 0, { insert = false } = {}) {
  const moving = ids.map((id) => clipById(doc, id)).filter(Boolean);
  if (!moving.length) return fail("Nothing selected.");
  if (moving.some((c) => locked(doc, c.track))) return fail("That track is locked.");
  const leadKind = trackOf(doc, moving[0].track).kind;
  const minStart = Math.min(...moving.map((c) => c.start));
  if (minStart + dF < 0) dF = -minStart;
  const rows = { video: doc.tracks.filter((t) => t.kind === "video").map((t) => t.id),
    audio: doc.tracks.filter((t) => t.kind === "audio").map((t) => t.id) };
  const targets = new Map();
  for (const c of moving) {
    const kind = trackOf(doc, c.track).kind;
    let tr = c.track;
    if (dRow && kind === leadKind) {
      const i = rows[kind].indexOf(c.track) + dRow;
      if (i < 0 || i >= rows[kind].length) return fail("No track there.");
      tr = rows[kind][i];
    }
    if (locked(doc, tr)) return fail("That track is locked.");
    targets.set(c.id, tr);
  }
  const except = new Set(moving.map((c) => c.id));
  const starts = new Map(moving.map((c) => [c.id, c.start + dF]));
  if (insert) {
    const f = minStart + dF;
    const len = Math.max(...moving.map((c) => clipEnd(c))) - minStart;
    for (const c of moving) c.start = -1e9;          // parked, so the split and the shift leave them alone
    for (const t of unlockedTracks(doc)) splitTrackAt(doc, t, f, except);
    shiftAfter(doc, f, len, except);
  }
  for (const c of moving) { c.start = starts.get(c.id); c.track = targets.get(c.id); }
  if (!insert) for (const c of moving) clearRange(doc, c.track, c.start, clipEnd(c), except);
  cleanTransitions(doc);
  return okr();
}

// Open len frames at f on every unlocked track (split what straddles f, push the rest right).
export function insertSpace(doc, f, len) {
  for (const t of unlockedTracks(doc)) splitTrackAt(doc, t, f, new Set());
  shiftAfter(doc, f, len);
  return okr();
}

export function placeClip(doc, ctx, clip, { insert = false } = {}) {
  if (locked(doc, clip.track)) return fail("That track is locked.");
  clip.id = clip.id || newId(doc);
  if (insert) {
    for (const t of unlockedTracks(doc)) splitTrackAt(doc, t, clip.start, new Set());
    shiftAfter(doc, clip.start, clipLen(clip));
  } else {
    clearRange(doc, clip.track, clip.start, clipEnd(clip));
  }
  doc.clips.push(clip);
  cleanTransitions(doc);
  return okr({ ids: [clip.id] });
}

// ------------------------------------------------------------------ trims

function trimLimits(doc, ctx, c, edge) {
  // allowed [lo, hi] for d on this clip alone
  if (edge === "in") {
    const p = prevOn(doc, c);
    const lo = Math.max(-c.in, (p ? clipEnd(p) : 0) - c.start);
    const hi = clipLen(c) - 1;
    return [lo, hi];
  }
  const n = nextOn(doc, c);
  const lo = -(clipLen(c) - 1);
  const hi = Math.min(srcLen(c, ctx) - c.out, (n ? n.start : Infinity) - clipEnd(c));
  return [lo, hi];
}

export function trim(doc, ctx, ids, edge, d) {
  const cs = ids.map((id) => clipById(doc, id)).filter(Boolean);
  if (cs.some((c) => locked(doc, c.track))) return fail("That track is locked.");
  let lo = -Infinity, hi = Infinity;
  for (const c of cs) { const [a, b] = trimLimits(doc, ctx, c, edge); lo = Math.max(lo, a); hi = Math.min(hi, b); }
  d = Math.max(lo, Math.min(hi, d));
  for (const c of cs) {
    if (edge === "in") { c.in += d; c.start += d; c.fadeIn = c.fadeIn ? Math.min(c.fadeIn, clipLen(c)) : c.fadeIn; }
    else { c.out += d; c.fadeOut = c.fadeOut ? Math.min(c.fadeOut, clipLen(c)) : c.fadeOut; }
  }
  cleanTransitions(doc);
  return okr({ d });
}

// The Select tool's edge drag (2026-09-30, Jonathan: "dragging the clip from the backside should also make it extend
// further back so I can hear the dial tone"): pulling a clip's start back past the room before it (the first clip on
// the timeline, or one butted against another) extends it like a ripple trim: it keeps its place, more of the source
// shows at its front, and everything after it moves right. Any other edge drag is a plain trim.
export function trimEdge(doc, ctx, ids, edge, d) {
  if (edge === "in" && d < 0) {
    const cs = ids.map((id) => clipById(doc, id)).filter(Boolean);
    let lo = -Infinity;
    for (const c of cs) lo = Math.max(lo, trimLimits(doc, ctx, c, "in")[0]);
    if (d < lo) return rippleTrim(doc, ctx, ids, "in", d);
  }
  return trim(doc, ctx, ids, edge, d);
}

// Ripple trim (B, Q, W): the edge moves and everything after it on unlocked tracks follows.
export function rippleTrim(doc, ctx, ids, edge, d) {
  const cs = ids.map((id) => clipById(doc, id)).filter(Boolean);
  if (!cs.length) return fail("Nothing to trim.");
  if (cs.some((c) => locked(doc, c.track))) return fail("That track is locked.");
  let lo = -Infinity, hi = Infinity;
  for (const c of cs) {
    if (edge === "in") { lo = Math.max(lo, -c.in); hi = Math.min(hi, clipLen(c) - 1); }
    else { lo = Math.max(lo, -(clipLen(c) - 1)); hi = Math.min(hi, srcLen(c, ctx) - c.out); }
  }
  d = Math.max(lo, Math.min(hi, d));
  if (!d) return okr({ d: 0 });
  const except = new Set(cs.map((c) => c.id));
  const oldEnd = Math.max(...cs.map((c) => clipEnd(c)));
  const shift = edge === "in" ? -d : d;
  if (shift < 0) {
    const bl = blockers(doc, oldEnd + shift, oldEnd, except).filter((b) => b.start < oldEnd);
    if (bl.length) return fail(`${bl[0].track} has a clip in the way. Lock ${bl[0].track} or select it.`);
  }
  for (const c of cs) {
    if (edge === "in") c.in += d; else c.out += d;
  }
  shiftAfter(doc, oldEnd, shift, except);
  cleanTransitions(doc);
  return okr({ d });
}

// Rolling edit (N): move the cut between two touching clips; total length unchanged.
export function roll(doc, ctx, leftId, rightId, d) {
  const L = clipById(doc, leftId), R = clipById(doc, rightId);
  if (!L || !R || clipEnd(L) !== R.start) return fail("Pick a cut between two clips.");
  if (locked(doc, L.track)) return fail("That track is locked.");
  const pairs = [[L, R]];
  if (L.link && R.link) {
    for (const pl of doc.clips.filter((c) => c.link === L.link && c.id !== L.id)) {
      const pr = doc.clips.find((c) => c.link === R.link && c.track === pl.track && c.start === clipEnd(pl));
      if (pr) pairs.push([pl, pr]);
    }
  }
  let lo = -Infinity, hi = Infinity;
  for (const [a, b] of pairs) {
    lo = Math.max(lo, -(clipLen(a) - 1), -b.in);
    hi = Math.min(hi, srcLen(a, ctx) - a.out, clipLen(b) - 1);
  }
  d = Math.max(lo, Math.min(hi, d));
  for (const [a, b] of pairs) { a.out += d; b.in += d; b.start += d; }
  cleanTransitions(doc);
  return okr({ d });
}

// Slip (Y): change which part of the source plays; position and length unchanged.
export function slip(doc, ctx, ids, d) {
  const cs = ids.map((id) => clipById(doc, id)).filter((c) => c && c.type !== "text" && c.type !== "shape");
  if (!cs.length) return fail("Slip needs a video or audio clip.");
  let lo = -Infinity, hi = Infinity;
  for (const c of cs) { lo = Math.max(lo, -c.in); hi = Math.min(hi, srcLen(c, ctx) - c.out); }
  d = Math.max(lo, Math.min(hi, d));
  for (const c of cs) {
    c.in += d; c.out += d;
    for (const name in c.fx || {}) if (c.fx[name].k) for (const k of c.fx[name].k) k.t += d;
  }
  return okr({ d });
}

// Slide (U): move a clip between its neighbours; they give and take length.
export function slide(doc, ctx, id, d) {
  const c = clipById(doc, id);
  if (!c) return fail("Nothing to slide.");
  const p = prevOn(doc, c), n = nextOn(doc, c);
  const pAdj = p && clipEnd(p) === c.start, nAdj = n && n.start === clipEnd(c);
  let lo = -c.start, hi = Infinity;
  if (pAdj) { lo = Math.max(lo, -(clipLen(p) - 1)); hi = Math.min(hi, srcLen(p, ctx) - p.out); }
  else if (p) lo = Math.max(lo, clipEnd(p) - c.start);
  if (nAdj) { lo = Math.max(lo, -n.in); hi = Math.min(hi, clipLen(n) - 1); }
  else if (n) hi = Math.min(hi, n.start - clipEnd(c));
  d = Math.max(lo, Math.min(hi, d));
  c.start += d;
  if (pAdj) p.out += d;
  if (nAdj) { n.in += d; n.start += d; }
  cleanTransitions(doc);
  return okr({ d });
}

// ------------------------------------------------------------------ split / join

function splitClip(doc, c, f) {
  if (!(c.start < f && f < clipEnd(c))) return null;
  const right = clone(c);
  right.id = newId(doc);
  right.in = c.in + (f - c.start);
  right.start = f;
  c.out = right.in;
  if (c.fadeOut !== undefined) { right.fadeIn = 0; c.fadeOut = 0; }
  for (const t of doc.transitions || []) if (t.a === c.id) t.a = right.id;
  doc.clips.push(right);
  return right;
}

function splitTrackAt(doc, trackId, f, except = new Set()) {
  for (const c of doc.clips.slice()) if (c.track === trackId && !except.has(c.id)) splitClip(doc, c, f);
}

export function split(doc, ctx, ids, f) {
  const made = [];
  const groups = new Map();
  for (const id of ids) {
    const c = clipById(doc, id);
    if (!c || locked(doc, c.track)) continue;
    const r = splitClip(doc, c, f);
    if (r) {
      made.push(r.id);
      if (c.link) {
        if (!groups.has(c.link)) groups.set(c.link, newLink(doc));
        r.link = groups.get(c.link);
      }
    }
  }
  return made.length ? okr({ ids: made }) : fail("Nothing under the playhead to split.");
}

export function splitAll(doc, ctx, f) {
  const ids = doc.clips.filter((c) => !locked(doc, c.track) && c.start < f && f < clipEnd(c)).map((c) => c.id);
  return split(doc, ctx, ids, f);
}

function sameSource(a, b) {
  if (a.type !== b.type) return false;
  if (a.asset || b.asset) return a.asset === b.asset;
  return JSON.stringify(a.text || a.shape) === JSON.stringify(b.text || b.shape);
}

// A cut that Join Through Edits can heal: same source, the right piece starts where the left one stops.
export function isThroughEdit(a, b) {
  return a && b && a.track === b.track && clipEnd(a) === b.start && a.out === b.in && sameSource(a, b);
}

function joinPair(doc, a, b) {
  a.out = b.out;
  for (const name in b.fx || {}) {
    if (!b.fx[name].k) continue;
    a.fx[name] = a.fx[name] || { v: b.fx[name].v };
    const have = new Set((a.fx[name].k || []).map((k) => k.t));
    a.fx[name].k = (a.fx[name].k || []).concat(b.fx[name].k.filter((k) => !have.has(k.t))).sort((x, y) => x.t - y.t);
  }
  if (b.fadeOut !== undefined) a.fadeOut = b.fadeOut;
  doc.transitions = (doc.transitions || []).filter((t) => !(t.a === a.id && t.b === b.id));
  for (const t of doc.transitions) if (t.a === b.id) t.a = a.id;
  doc.clips = doc.clips.filter((c) => c.id !== b.id);
}

// Join Through Edits (G30): heal a razor cut. Pass the clip left of the cut (or the cut's right clip).
export function joinThrough(doc, ctx, id) {
  let a = clipById(doc, id);
  if (!a) return fail("Nothing selected.");
  let b = nextOn(doc, a);
  if (!isThroughEdit(a, b)) {
    const p = prevOn(doc, a);
    if (isThroughEdit(p, a)) { b = a; a = p; } else return fail("That cut isn't a through edit (same clip on both sides).");
  }
  const partnersA = a.link ? doc.clips.filter((c) => c.link === a.link && c.id !== a.id) : [];
  joinPair(doc, a, b);
  for (const pa of partnersA) {
    const pb = nextOn(doc, pa);
    if (isThroughEdit(pa, pb)) joinPair(doc, pa, pb);
  }
  return okr({ ids: [a.id] });
}

export function throughEditsAt(doc) {
  const out = [];
  for (const t of doc.tracks) {
    const cs = clipsOn(doc, t.id);
    for (let i = 0; i + 1 < cs.length; i += 1) if (isThroughEdit(cs[i], cs[i + 1])) out.push({ track: t.id, f: cs[i + 1].start, a: cs[i].id, b: cs[i + 1].id });
  }
  return out;
}

// ------------------------------------------------------------------ delete

export function lift(doc, ctx, ids) {
  const set = new Set(ids.filter((id) => { const c = clipById(doc, id); return c && !locked(doc, c.track); }));
  if (!set.size) return fail("Nothing to delete.");
  doc.clips = doc.clips.filter((c) => !set.has(c.id));
  cleanTransitions(doc);
  return okr();
}

// Ripple delete (Shift+Delete): remove and close the gap on every unlocked track, unless something straddles it.
export function rippleDelete(doc, ctx, ids) {
  const cs = ids.map((id) => clipById(doc, id)).filter((c) => c && !locked(doc, c.track));
  if (!cs.length) return fail("Nothing to delete.");
  const except = new Set(cs.map((c) => c.id));
  const spans = cs.map((c) => [c.start, clipEnd(c)]).sort((x, y) => x[0] - y[0]);
  const merged = [];
  for (const s of spans) {
    const last = merged[merged.length - 1];
    if (last && s[0] <= last[1]) last[1] = Math.max(last[1], s[1]); else merged.push([s[0], s[1]]);
  }
  for (const [a, b] of merged) {
    const bl = blockers(doc, a, b, except).filter((c) => c.start < b);
    if (bl.length) return fail(`${bl[0].track} has a clip in the way. Lock ${bl[0].track} or select it.`);
  }
  doc.clips = doc.clips.filter((c) => !except.has(c.id));
  for (const [a, b] of merged.reverse()) shiftAfter(doc, b, -(b - a), new Set());
  cleanTransitions(doc);
  return okr();
}

// Ripple a gap out (Backspace/Shift+Delete on an empty stretch of a track).
export function rippleGap(doc, ctx, trackId, f) {
  const cs = clipsOn(doc, trackId);
  let a = 0, b = null;
  for (const c of cs) {
    if (clipEnd(c) <= f) a = Math.max(a, clipEnd(c));
    else if (c.start > f) { b = c.start; break; } else return fail("That's not a gap.");
  }
  if (b === null || b <= a) return fail("That's not a gap.");
  const bl = blockers(doc, a, b, new Set()).filter((c) => c.start < b);
  if (bl.length) return fail(`${bl[0].track} has a clip in the way. Lock ${bl[0].track} or select it.`);
  shiftAfter(doc, b, -(b - a));
  cleanTransitions(doc);
  return okr();
}

// Lift / extract the In-Out range on every unlocked track.
export function rangeCut(doc, ctx, extract) {
  const { in: a, out: b } = doc.range || {};
  if (a === null || b === null || a === undefined || b === undefined || b <= a) return fail("Mark an In and an Out first (I, O).");
  for (const t of unlockedTracks(doc)) { splitTrackAt(doc, t, a); splitTrackAt(doc, t, b); }
  const allow = new Set(unlockedTracks(doc));
  doc.clips = doc.clips.filter((c) => !(allow.has(c.track) && c.start >= a && clipEnd(c) <= b));
  if (extract) { shiftAfter(doc, b, -(b - a)); doc.range = { in: a, out: a }; }
  cleanTransitions(doc);
  return okr();
}

// ------------------------------------------------------------------ tracks

export function addTrack(doc, kind) {
  const same = doc.tracks.filter((t) => t.kind === kind);
  const prefix = kind === "video" ? "V" : "A";
  const n = Math.max(0, ...same.map((t) => parseInt(t.id.slice(1), 10) || 0)) + 1;
  const tr = { id: prefix + n, kind, mute: false, solo: false, lock: false, hide: false };
  if (kind === "video") {
    const i = doc.tracks.findIndex((t) => t.kind === "video");
    doc.tracks.splice(i < 0 ? 1 : i, 0, tr);
  } else doc.tracks.push(tr);
  return okr({ id: tr.id });
}

export function deleteTrack(doc, id) {
  if (["C", "V1", "A1"].includes(id)) return fail("C, V1 and A1 stay.");
  if (doc.clips.some((c) => c.track === id)) return fail("Empty the track first.");
  doc.tracks = doc.tracks.filter((t) => t.id !== id);
  return okr();
}

// ------------------------------------------------------------------ transitions, fades, markers

// Cross dissolve / dip to black at a cut (Ctrl+D). Centered on the cut; each side needs dur/2 spare frames.
export function addTransition(doc, ctx, trackId, f, kind = "dissolve", dur = 15) {
  const cs = clipsOn(doc, trackId);
  const a = cs.find((c) => clipEnd(c) === f) || null;
  const b = cs.find((c) => c.start === f) || null;
  if (!a && !b) return fail("Put the playhead on a cut.");
  if (kind === "dissolve" && !(a && b)) return fail("A cross dissolve needs a clip on both sides.");
  let half = Math.floor(dur / 2);
  if (a && b) {
    const spareA = srcLen(a, ctx) - a.out, spareB = b.in;
    half = Math.min(half, spareA, spareB);
    if (half < 1) return fail("Not enough extra footage past the cut for a transition. Trim the clips first.");
  }
  doc.transitions = (doc.transitions || []).filter((t) => !(t.track === trackId && ((a && t.a === a.id) || (b && t.b === b.id))));
  const t = { id: newId(doc, "t"), track: trackId, a: a ? a.id : null, b: b ? b.id : null, kind, dur: a && b ? half * 2 : dur };
  doc.transitions.push(t);
  return okr({ id: t.id, dur: t.dur });
}

export function transitionWindow(doc, t) {
  const a = t.a && clipById(doc, t.a), b = t.b && clipById(doc, t.b);
  const cut = a ? clipEnd(a) : b.start;
  if (a && b) return { cut, s: cut - t.dur / 2, e: cut + t.dur / 2 };
  if (a) return { cut, s: cut - t.dur, e: cut };
  return { cut, s: cut, e: cut + t.dur };
}

export function setFade(doc, id, which, frames) {
  const c = clipById(doc, id);
  if (!c || c.type !== "audio") return fail("Fades are for audio clips.");
  c[which] = Math.max(0, Math.min(clipLen(c), Math.round(frames)));
  const other = which === "fadeIn" ? "fadeOut" : "fadeIn";
  if (c[which] + c[other] > clipLen(c)) c[other] = clipLen(c) - c[which];
  return okr();
}

export function addMarker(doc, f, color = "green", note = "") {
  doc.markers = doc.markers || [];
  const hit = doc.markers.find((m) => m.t === f);
  if (hit) return okr({ id: hit.id });
  const m = { id: newId(doc, "m"), t: Math.max(0, Math.round(f)), color, note };
  doc.markers.push(m);
  doc.markers.sort((a, b) => a.t - b.t);
  return okr({ id: m.id });
}

export function toggleEnable(doc, ids) {
  const cs = ids.map((id) => clipById(doc, id)).filter(Boolean);
  const on = !cs.every((c) => c.on !== false);
  for (const c of cs) c.on = on;
  return okr();
}

export function setLink(doc, ids, linked) {
  const cs = ids.map((id) => clipById(doc, id)).filter(Boolean);
  if (linked) { const l = newLink(doc); for (const c of cs) c.link = l; }
  else for (const c of cs) c.link = null;
  return okr();
}

export function durationOf(doc) { return Math.max(0, ...doc.clips.map(clipEnd)); }

export const seconds = (f) => f / FPS;
