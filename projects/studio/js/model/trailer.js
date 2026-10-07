// The Trailer (Jonathan 2026-09-30, T1-T4): the short opens on the peak, cut before the reward (the In to Out marks),
// then hard cuts to the dial tone, with a riser that starts the call. A black-on-white headline sits in the top third
// through the peak (so it is the thumbnail); it fades in over 6 frames and never moves. Built by Clip > Make trailer,
// one undo step; every piece is an ordinary clip Jonathan can change.
import { clipEnd, clipsOn, clone, newId, newLink, FPS } from "./doc.js";
import { insertSpace } from "./ops.js";
import { voiceTracks } from "./voices.js";

export const HEADLINE = { size: 84, y: 480, maxW: 860, fadeFrames: 6, color: "#000000", bg: "#FFFFFF" };
export const RING_PAD = 6;      // frames kept before the ring starts

// Break a headline into lines no wider than maxW (measure(s) gives a line's width at the headline's size), evened
// out so no word sits alone on the last line ("She said no / four times", not "She said no four / times").
export function wrapHeadline(str, measure, maxW = HEADLINE.maxW) {
  const words = String(str).trim().split(/\s+/).filter(Boolean);
  const greedy = (lim) => {
    const out = [];
    let line = "";
    for (const w of words) {
      const next = line ? line + " " + w : w;
      if (line && measure(next) > lim) { out.push(line); line = w; } else line = next;
    }
    if (line) out.push(line);
    return out;
  };
  const lines = greedy(maxW);
  if (lines.length < 2) return lines.join("\n");
  let lo = measure(words.join(" ")) / lines.length, hi = maxW;
  for (let i = 0; i < 14; i += 1) { const mid = (lo + hi) / 2; if (greedy(mid).length <= lines.length) hi = mid; else lo = mid; }
  return greedy(hi).join("\n");
}

// opts: { a, b } the peak on the timeline (frames); ringFrame (source frame the last ring starts, or null);
// headline (already wrapped); riser { id, frames } or null; soundsTrack(doc) -> track id for the riser.
export function makeTrailer(doc, ctx, { a, b, ringFrame, headline, riser, soundsTrack }) {
  if (!(b > a)) return { ok: false, reason: "Mark the peak first: I at its start, O just before the reward." };
  const tease = b - a;
  // 1. copies of what plays under the peak: the video and the speech (not overlays, not sounds)
  const speech = new Set(["V1", "A1", ...voiceTracks(doc).map((t) => t.id)]);
  const pieces = [];
  for (const c of doc.clips) {
    if (!speech.has(c.track) || c.start >= b || clipEnd(c) <= a || (c.type !== "video" && c.type !== "audio")) continue;
    const s = Math.max(a, c.start), e = Math.min(b, clipEnd(c));
    const p = clone(c);
    p.in = c.in + (s - c.start);
    p.out = p.in + (e - s);
    p.start = s - a;
    if (p.type === "audio") { p.fadeIn = 0; p.fadeOut = 0; }
    pieces.push(p);
  }
  if (!pieces.some((p) => p.type === "video")) return { ok: false, reason: "There's no video under the marks." };
  // 2. the call from its last ring: the first video clip and its partners reach back to just before the ring
  const first = clipsOn(doc, "V1").filter((c) => c.type === "video")[0];
  let lead = 0;
  if (ringFrame !== null && ringFrame !== undefined && first && ringFrame < first.in && first.in - ringFrame <= 60 * FPS) {
    lead = first.in - Math.max(0, ringFrame - RING_PAD);
  }
  const partners = first ? doc.clips.filter((c) => c.start === first.start && (c.id === first.id || (first.link && c.link === first.link))) : [];
  // 3. room at the front for the peak and the lead-in; everything else moves right
  insertSpace(doc, 0, tease + lead);
  if (lead) for (const c of partners) { c.in -= lead; c.start -= lead; }
  // 4. the peak at the front, its pieces linked to each other
  const link = newLink(doc);
  const ids = [];
  for (const p of pieces) { p.id = newId(doc); p.link = link; doc.clips.push(p); ids.push(p.id); }
  // 5. the riser on the sounds track, from the hard cut into the call
  if (riser) {
    const tr = soundsTrack(doc);
    const r = { id: newId(doc), track: tr, type: "audio", asset: riser.id, in: 0, out: Math.max(1, riser.frames), start: tease,
      on: true, fadeIn: 0, fadeOut: 0, fx: {} };
    doc.clips.push(r);
    ids.push(r.id);
  }
  // 6. the headline: top third, black on white, fades in and stays put, through the peak
  const top = doc.tracks.find((t) => t.kind === "video" && t.id !== "V1" && !doc.clips.some((c) => c.track === t.id && c.start < tease));
  const trackId = top ? top.id : "V2";
  const h = { id: newId(doc), track: trackId, type: "text", in: 0, out: tease, start: 0, on: true,
    text: { str: headline, size: HEADLINE.size, color: HEADLINE.color, bg: HEADLINE.bg, strokeW: 0 },
    fx: { posX: { v: 540 }, posY: { v: HEADLINE.y },
      opacity: { v: 100, k: [{ t: 0, v: 0, e: "out" }, { t: HEADLINE.fadeFrames, v: 100, e: "linear" }] } } };
  doc.clips.push(h);
  ids.push(h.id);
  doc.range = { in: null, out: null };
  return { ok: true, ids, tease, lead, headlineTrack: trackId };
}
