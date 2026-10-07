// Keyframes: Linear, Ease In, Ease Out, Ease In & Out, Hold (G15). One easing definition, mirrored exactly in
// scripts/studio_render.py (ease_value) and checked by tests/vectors.json.
//   segment k0 -> k1, u in [0,1]:  hold on k0 -> stays at k0
//   a = k0 eases out (slow start), b = k1 eases in (slow arrival)
//   f = a && b ? 3u^2 - 2u^3 : a ? u^2 : b ? 1 - (1-u)^2 : u
import { FX_DEFAULTS, FPS } from "./doc.js";
import { gateAt } from "./voices.js";

export const EASES = [["linear", "Linear"], ["in", "Ease In"], ["out", "Ease Out"], ["both", "Ease In & Out"], ["hold", "Hold"]];
export const PROPS = [
  ["posX", "Position X", 1], ["posY", "Position Y", 1], ["scale", "Scale", 0.1], ["rot", "Rotation", 0.1],
  ["opacity", "Opacity", 0.1], ["volume", "Volume", 0.1],
];

export function easeFrac(u, e0, e1) {
  if (e0 === "hold") return 0;
  const a = e0 === "out" || e0 === "both";
  const b = e1 === "in" || e1 === "both";
  if (a && b) return 3 * u * u - 2 * u * u * u;
  if (a) return u * u;
  if (b) return 1 - (1 - u) * (1 - u);
  return u;
}

export function keysOf(clip, name) {
  const p = clip.fx && clip.fx[name];
  return p && p.k && p.k.length ? p.k : null;
}

export function isAnimated(clip, name) { return !!keysOf(clip, name); }

// t: the clip's source frame (clip.in + timeline offset), may be fractional
export function valueAt(clip, name, t) {
  const p = clip.fx && clip.fx[name];
  const base = p && p.v !== undefined ? p.v : FX_DEFAULTS[name];
  const k = p && p.k;
  if (!k || !k.length) return base;
  if (t <= k[0].t) return k[0].v;
  const last = k[k.length - 1];
  if (t >= last.t) return last.v;
  let i = 0;
  while (i < k.length - 1 && k[i + 1].t <= t) i += 1;
  const k0 = k[i], k1 = k[i + 1];
  const u = (t - k0.t) / (k1.t - k0.t);
  return k0.v + (k1.v - k0.v) * easeFrac(u, k0.e || "linear", k1.e || "linear");
}

export function srcFrame(clip, f) { return clip.in + (f - clip.start); }
export function valueAtTimeline(clip, name, f) { return valueAt(clip, name, srcFrame(clip, f)); }

function ensure(clip, name) {
  clip.fx = clip.fx || {};
  if (!clip.fx[name]) clip.fx[name] = { v: FX_DEFAULTS[name] };
  return clip.fx[name];
}

// Set a value at source frame t: a key when the property is animated, the constant otherwise.
export function setValue(clip, name, t, v) {
  const p = ensure(clip, name);
  if (p.k && p.k.length) addKey(clip, name, Math.round(t), v);
  else p.v = v;
}

export function addKey(clip, name, t, v, e) {
  const p = ensure(clip, name);
  p.k = p.k || [];
  t = Math.round(t);
  if (v === undefined) v = valueAt(clip, name, t);
  const i = p.k.findIndex((k) => k.t === t);
  if (i >= 0) { p.k[i].v = v; if (e) p.k[i].e = e; }
  else p.k.push({ t, v, e: e || "linear" });
  p.k.sort((a, b) => a.t - b.t);
  return p;
}

export function removeKey(clip, name, t) {
  const p = clip.fx && clip.fx[name];
  if (!p || !p.k) return;
  const v = valueAt(clip, name, t);
  p.k = p.k.filter((k) => k.t !== t);
  if (!p.k.length) { delete p.k; p.v = v; }
}

export function moveKey(clip, name, t0, t1, v) {
  const p = clip.fx && clip.fx[name];
  if (!p || !p.k) return;
  const k = p.k.find((x) => x.t === t0);
  if (!k) return;
  t1 = Math.round(t1);
  if (t1 !== t0 && p.k.some((x) => x.t === t1)) return;
  k.t = t1;
  if (v !== undefined) k.v = v;
  p.k.sort((a, b) => a.t - b.t);
}

export function setEase(clip, name, t, e) {
  const p = clip.fx && clip.fx[name];
  const k = p && p.k && p.k.find((x) => x.t === t);
  if (k) k.e = e;
}

// Stopwatch: on adds a key at t holding the current value; off drops all keys, keeping the value at t.
export function toggleAnimate(clip, name, t) {
  const p = ensure(clip, name);
  if (p.k && p.k.length) { const v = valueAt(clip, name, t); delete p.k; p.v = v; return false; }
  p.k = [{ t: Math.round(t), v: p.v !== undefined ? p.v : FX_DEFAULTS[name], e: "linear" }];
  return true;
}

export function nextKey(clip, name, t, dir) {
  const k = keysOf(clip, name);
  if (!k) return null;
  if (dir > 0) { const n = k.find((x) => x.t > t + 0.001); return n ? n.t : null; }
  const prev = k.filter((x) => x.t < t - 0.001);
  return prev.length ? prev[prev.length - 1].t : null;
}

// Linear gain samples for an audio clip over timeline frames [f0, f1) at hz samples per second: volume keyframes
// (dB) times the fades (linear in amplitude).
// gate (voice tracks, model/voices.js): the source stretches a voice clip plays, or null for an ordinary clip
export function gainAt(clip, f, gate = null) {
  const db = valueAtTimeline(clip, "volume", f);
  let g = Math.pow(10, db / 20);
  const off = f - clip.start, len = clip.out - clip.in;
  if (clip.fadeIn && off < clip.fadeIn) g *= Math.max(0, off / clip.fadeIn);
  if (clip.fadeOut && off > len - clip.fadeOut) g *= Math.max(0, (len - off) / clip.fadeOut);
  if (gate) g *= gateAt(gate, clip, clip.in + off);
  return g;
}

export function gainCurve(clip, f0, f1, hz = 100, gate = null) {
  const n = Math.max(2, Math.ceil(((f1 - f0) / FPS) * hz) + 1);
  const out = new Float32Array(n);
  for (let i = 0; i < n; i += 1) out[i] = gainAt(clip, f0 + ((f1 - f0) * i) / (n - 1), gate);
  return out;
}
