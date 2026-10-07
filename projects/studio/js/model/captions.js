// Captions built from the words under each A1 clip, so they follow every cut (G21). 2-4 word groups
// (G18); a group breaks on a pause over 0.35 s, after . , ? !, at a clip edge, when the voice changes, or when wider
// than 900 px. Each word carries its own x (center) and its voice class k (me, f, m, u) so the exporter burns each
// word where and in the color the preview drew it. Colors: one palette for every short (grill C1-C11, 2026-09-30).
// The words: a short made since 2026-10-02 (captions.mode "generate") has none until Generate captions puts its own
// in captions.gen[asset] (second listen plus Claude's picks, scripts/studio_gencaps.py; grill G1-G7), in the
// recording's seconds, so they follow the cuts the same way. An older short reads the first transcript, as before.
import { clipEnd, clipsOn, FPS } from "./doc.js";
import { gateFrames, isVoiceClip, plays } from "./voices.js";

// the clips captions read words from: speech on A1, and the voice tracks (A1 You, A2 Them, 2026-09-30)
export function speechClips(doc) {
  return doc.clips.filter((c) => c.type === "audio" && c.on !== false && c.asset && (c.track === "A1" || isVoiceClip(c)))
    .sort((a, b) => a.start - b.start);
}

export const MAX_W = 900;
export const GAP_BREAK = Math.round(0.35 * FPS);
export const HOLD = 15;   // frames a group lingers after its last word, if the next group has not started

// the same defaults as scripts/studio_captions.py DEFAULT_PALETTE (their spoken word white since 2026-09-30)
export const DEFAULT_PALETTE = { you: "#4D80E6", youWord: "#FFFFFF", woman: "#FF5FA2", man: "#FF3B30", themWord: "#FFFFFF", unknown: "#FFFFFF" };

// [text color, spoken-word color] for a voice class
export function colorsFor(k, pal) {
  const p = Object.assign({}, DEFAULT_PALETTE, pal || {});
  if (k === "me") return [p.you, p.youWord];
  if (k === "f") return [p.woman, p.themWord];
  if (k === "m") return [p.man, p.themWord];
  return [p.unknown, p.themWord];
}

function lowerBound(words, sec) {
  let lo = 0, hi = words.length;
  while (lo < hi) { const m = (lo + hi) >> 1; if (words[m][1] <= sec) lo = m + 1; else hi = m; }
  return lo;
}

// A word's voice: {key, cls} from the transcript's resolved voices (studio_speakers.resolve), or null.
export function voiceOf(tr, i) {
  const v = tr && tr.voices;
  if (!v || v.state !== "ready" || !v.spk) return null;
  const idx = v.spk[i];
  return idx >= 0 ? v.speakers[idx] : null;
}

export function genMode(doc) { return !!(doc && doc.captions && doc.captions.mode === "generate"); }

// A generated word [s, e, text, donor, group, fix]: its voice is the one Jonathan set on this short, else that of the
// first-transcript word it overlaps (while the transcript is the one the words were made against), else the voice
// split's group at its time. The same rules as scripts/studio_gencaps.py gen_classes, which the exporter uses.
export function genVoice(tr, gen, w) {
  const v = tr && tr.voices;
  if (!v || v.state !== "ready" || !v.speakers) return null;
  if (w[5]) { const o = v.speakers.find((s) => s.key === w[5]); if (o) return o; }
  if (w[3] !== null && w[3] !== undefined && gen.trRev === tr.rev && v.spk && w[3] < v.spk.length && v.spk[w[3]] >= 0) return v.speakers[v.spk[w[3]]];
  if (w[4]) return v.speakers.find((s) => (s.groups || []).includes(w[4])) || null;
  return null;
}

// a caption word's voice, generated or from the transcript (the Captions tab's voices list)
export function eventVoice(doc, lib, w) {
  const tr = lib && lib.transcript(w.asset);
  if (w.gi !== undefined && w.gi !== null) {
    const gen = doc.captions.gen && doc.captions.gen[w.asset];
    return gen && gen.words[w.gi] ? genVoice(tr, gen, gen.words[w.gi]) : null;
  }
  return voiceOf(tr, w.id);
}

// {asset: [[s, e]]}: the stretches of each recording the speech clips keep, in seconds (what Generate listens to)
export function keptRanges(doc) {
  const out = {};
  for (const c of speechClips(doc)) (out[c.asset] = out[c.asset] || []).push([c.in / FPS, c.out / FPS]);
  return out;
}

// seconds of the ranges rs that no range in cover holds
export function uncovered(rs, cover) {
  let total = 0;
  for (const [s, e] of rs) {
    let left = [[s, e]];
    for (const [a, b] of cover) {
      const nxt = [];
      for (const [x, y] of left) {
        if (b <= x || a >= y) { nxt.push([x, y]); continue; }
        if (a > x) nxt.push([x, a]);
        if (b < y) nxt.push([b, y]);
      }
      left = nxt;
    }
    for (const [x, y] of left) total += y - x;
  }
  return total;
}

// null: an older short (captions from the first transcript); "none": no generated words for some of its speech yet;
// "part": footage reaches past what was generated (over half a second); "ok". As studio_gencaps.missing on the server.
export function genStatus(doc) {
  if (!genMode(doc)) return null;
  const gen = doc.captions.gen || {};
  let st = "ok";
  for (const [asset, rs] of Object.entries(keptRanges(doc))) {
    const g = gen[asset];
    if (!g) return "none";
    if (uncovered(rs, g.ranges || []) > 0.5) st = "part";
  }
  return st;
}

// The words under the speech clips mapped to timeline frames. A voice clip gives only the words its speaker says
// (its stretches), so the same word never comes from both A1 and A2. {trim: true} (the razor and trims snapping to
// word edges): a recording with no generated words yet gives its first-transcript words, so a new short still snaps
// while it's being trimmed, before its captions exist.
export function wordsOnTimeline(doc, lib, { trim = false } = {}) {
  const out = [];
  const seen = new Set();
  for (const c of speechClips(doc)) {
    const tr = lib && lib.transcript(c.asset);
    const gen = genMode(doc) && doc.captions.gen ? doc.captions.gen[c.asset] : null;
    const gm = !!gen || (genMode(doc) && !trim);
    if (gm ? !gen : !tr) continue;
    const words = gm ? gen.words : tr.words;
    const gate = gateFrames(c, tr);
    if (gate && !gate.length) continue;
    const s0 = c.in / FPS, s1 = c.out / FPS;
    for (let i = lowerBound(words, s0); i < words.length && words[i][0] < s1; i += 1) {
      const w = words[i];
      const ws = Math.max(w[0], s0), we = Math.min(w[1], s1);
      if (we - ws < 0.02) continue;
      if (gate && !plays(gate, ((w[0] + w[1]) / 2) * FPS)) continue;
      const key = c.asset + ":" + (gm ? "g" : "") + i + ":" + c.start;
      if (seen.has(key)) continue;
      seen.add(key);
      const f0 = Math.round(c.start + (ws * FPS - c.in));
      const f1 = Math.max(f0 + 1, Math.round(c.start + (we * FPS - c.in)));
      const v = gm ? genVoice(tr, gen, w) : voiceOf(tr, i);
      const t = { text: w[2], s: f0, e: Math.min(f1, clipEnd(c)), id: gm ? null : i, asset: c.asset, clip: c.link || c.id,
        spk: v ? c.asset + ":" + v.key : null, k: v ? v.cls : "u" };
      if (gm) t.gi = i;
      out.push(t);
    }
  }
  const n = (t) => (t.gi !== undefined ? t.gi : t.id);
  out.sort((a, b) => a.s - b.s || n(a) - n(b));
  return out;
}

export const WORD_GAP = 1.35;   // times the font's space: Montserrat Black's own space reads cramped at caption size

// Returns null while a transcript the A1 clips need is still loading: the caller keeps the captions it has, so a save
// or export made in that moment can't wipe them.
export function buildCaptionEvents(doc, lib, measure) {
  const cfg = doc.captions;
  for (const c of speechClips(doc)) if (lib.transcriptPending && lib.transcriptPending(c.asset)) return null;
  const toks = wordsOnTimeline(doc, lib);
  const space = measure(" ") * WORD_GAP;
  const events = [];
  let cur = null, curW = 0;
  const flush = () => { if (cur && cur.words.length) events.push(cur); cur = null; curW = 0; };
  for (const t of toks) {
    const text = cfg.upper ? t.text.toUpperCase() : t.text;
    const w = measure(text);
    const last = cur && cur.words[cur.words.length - 1];
    const brk = !cur || cur.words.length >= 4 || t.clip !== cur.clip || t.spk !== cur.spk || t.s - last.e > GAP_BREAK
      || /[.?!,;:]["')]*$/.test(last.w) || curW + space + w > MAX_W;
    if (brk) { flush(); cur = { clip: t.clip, spk: t.spk, words: [] }; }
    const word = { w: text, s: t.s, e: t.e, id: t.id, asset: t.asset, k: t.k, width: w };
    if (t.gi !== undefined) word.gi = t.gi;     // a generated word: its place in captions.gen[asset].words
    cur.words.push(word);
    curW += (cur.words.length > 1 ? space : 0) + w;
  }
  flush();
  for (const ev of events) ev.s = ev.words[0].s;
  for (let i = 0; i < events.length; i += 1) {
    const ev = events[i];
    const widths = ev.words.map((x) => x.width);
    const total = widths.reduce((a, b) => a + b, 0) + space * (widths.length - 1);
    let x = 540 - total / 2;
    for (const wd of ev.words) { wd.x = Math.round(x + wd.width / 2); x += wd.width + space; delete wd.width; }
    const lastE = ev.words[ev.words.length - 1].e;
    const next = events[i + 1];
    ev.e = Math.min(next ? next.s : Infinity, lastE + HOLD);
    ev.e = Math.max(ev.e, lastE);
    delete ev.clip;
    delete ev.spk;
  }
  return events;
}

export function activeEvent(events, f) {
  let lo = 0, hi = events.length - 1;
  while (lo <= hi) {
    const m = (lo + hi) >> 1;
    if (events[m].e <= f) lo = m + 1; else if (events[m].s > f) hi = m - 1; else return events[m];
  }
  return null;
}

export const POP = 0.08;               // +8 % over 110 ms, the same as \t(0,110,\fscx108\fscy108)
export const POP_FRAMES = 0.11 * FPS;
export function popScale(w, f) { return w.s <= f && f < w.e ? 1 + POP * Math.min(1, (f - w.s) / POP_FRAMES) : 1; }
