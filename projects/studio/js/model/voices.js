// Voice tracks (Jonathan 2026-09-30, V1-V3): an audio clip with `voice` ("me" or "them") plays only its speaker's
// stretches of the recording, so A1 (You) and A2 (Them) hold the same audio twice and each can be leveled on its own.
// The stretches ("runs", seconds, end to end) come from the server with the transcript's voices
// (studio_speakers.voice_runs): the preview, the captions, the timeline and the exporter (studio_render.gate_expr) all
// cut in the same places, in the middle of the pause between two speakers, with 2-frame ramps.
import { clone, newId, trackOf, FPS } from "./doc.js";

export const RAMP = 2;            // frames a voice track takes to open or close

export function isVoiceClip(c) { return !!c && c.type === "audio" && (c.voice === "me" || c.voice === "them"); }
export function voiceTracks(doc) { return doc.tracks.filter((t) => t.kind === "audio" && (t.voice === "me" || t.voice === "them")); }

// The source frames [[f0, f1]] a voice clip plays; null for an ordinary clip (it plays everything). Without voice data
// "me" plays everything and "them" nothing, so no audio goes missing before the voices are labeled.
export function gateFrames(c, tr) {
  if (!isVoiceClip(c)) return null;
  const runs = tr && tr.voices && tr.voices.state === "ready" ? tr.voices.runs : null;
  if (!runs || !runs.length) return c.voice === "me" ? [[c.in, c.out]] : [];
  const s0 = c.in / FPS, s1 = c.out / FPS;
  let lo = 0, hi = runs.length;
  while (lo < hi) { const m = (lo + hi) >> 1; if (runs[m][1] <= s0) lo = m + 1; else hi = m; }
  const out = [];
  for (let i = lo; i < runs.length && runs[i][0] < s1; i += 1) {
    const [a, b, side] = runs[i];
    if (side !== c.voice) continue;
    const f0 = Math.max(c.in, a * FPS), f1 = Math.min(c.out, b * FPS);
    if (f1 > f0) out.push([f0, f1]);
  }
  return out;
}

// Gain 0..1 of a voice clip at source frame t (1 everywhere for an ordinary clip).
export function gateAt(gate, c, t) {
  if (!gate) return 1;
  for (const [a, b] of gate) {
    if (t < a - RAMP || t > b + RAMP) continue;
    const up = a <= c.in ? 1 : Math.max(0, Math.min(1, (t - a) / RAMP));
    const down = b >= c.out ? 1 : Math.max(0, Math.min(1, (b - t) / RAMP));
    const g = Math.min(up, down);
    if (g > 0) return g;
  }
  return 0;
}

// Is source frame t inside what this clip plays (captions and the timeline's dimming use the stretches themselves)?
export function plays(gate, t) {
  if (!gate) return true;
  for (const [a, b] of gate) if (t >= a && t < b) return true;
  return false;
}

// Split audio by voice (Clip menu): an older short's A1 speech clip becomes A1 "You" (voice me) plus a copy on
// A2 "Them" (voice them), linked to the same video. What was on A2 (sounds) moves to a new track first.
export function splitVoices(doc, ctx) {
  const speech = doc.clips.filter((c) => c.type === "audio" && c.track === "A1" && !isVoiceClip(c) && c.asset
    && ctx.lib && ctx.lib.asset(c.asset) && ctx.lib.asset(c.asset).transcript);
  if (!speech.length) return { ok: false, reason: "No speech on A1 to split (or it is split already)." };
  let a2 = trackOf(doc, "A2");
  if (a2 && a2.voice !== "them" && doc.clips.some((c) => c.track === "A2")) {
    const n = Math.max(0, ...doc.tracks.filter((t) => t.kind === "audio").map((t) => parseInt(t.id.slice(1), 10) || 0)) + 1;
    const sounds = { id: "A" + n, kind: "audio", name: "Sounds", mute: false, solo: false, lock: false, hide: false };
    doc.tracks.push(sounds);
    for (const c of doc.clips) if (c.track === "A2") c.track = sounds.id;
  }
  if (!a2) {
    a2 = { id: "A2", kind: "audio", mute: false, solo: false, lock: false, hide: false };
    doc.tracks.splice(doc.tracks.findIndex((t) => t.id === "A1") + 1, 0, a2);
  }
  Object.assign(trackOf(doc, "A1"), { voice: "me", name: "You" });
  Object.assign(a2, { voice: "them", name: "Them" });
  const made = [];
  for (const c of speech) {
    c.voice = "me";
    const t = clone(c);
    t.id = newId(doc);
    t.track = "A2";
    t.voice = "them";
    doc.clips.push(t);
    made.push(t.id);
  }
  return { ok: true, ids: made };
}

// Voice track volume for "Normalize voices": the clip's level set to `gain` dB, keyframes moved by the same amount.
export function setClipGain(c, gain) {
  c.fx = c.fx || {};
  const p = c.fx.volume || { v: 0 };
  const d = gain - (p.v || 0);
  p.v = Math.round(gain * 10) / 10;
  if (p.k) for (const k of p.k) k.v = Math.round((k.v + d) * 10) / 10;
  c.fx.volume = p;
}

export const NORMALIZE_TARGET = -20;     // LUFS each voice track's speech is set to; the export then masters to -14
