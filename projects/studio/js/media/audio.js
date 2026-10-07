// Audio engine and the timeline clock. An AudioContext keeps time; every audio clip plays from 30 s WAV blocks the
// server cuts at the context's sample rate, scheduled a little ahead (the Dictation Sheet's lookahead pattern) with
// a gain curve per piece (volume keyframes x fades). Video elements are muted and only supply pictures.
import { S } from "../store.js";
import { clipEnd, FPS } from "../model/doc.js";
import { gainCurve } from "../model/keyframes.js";
import { gateFrames, isVoiceClip } from "../model/voices.js";
import { lib } from "./library.js";

const BLOCK_S = 30;
const TICK_MS = 25;
const AHEAD_S = 1.2;          // schedule pieces starting within this window
const CACHE_BYTES = 256e6;

class AudioEngine {
  constructor() {
    this.ctx = null;
    this.master = null;
    this.blocks = new Map();     // key -> {buf, p, used, bytes}
    this.bytes = 0;
    this.live = new Set();
    this.scheduled = new Set();
    this.playing = false;
    this.rate = 1;
    this.t0 = 0; this.ac0 = 0; this.perf0 = 0;
    this.timer = null;
    this.log = [];               // tests read what was scheduled
    this.audition = null;
  }

  ensure() {
    if (!this.ctx) {
      this.ctx = new AudioContext({ latencyHint: "interactive" });
      this.master = this.ctx.createGain();
      this.master.connect(this.ctx.destination);
    }
    if (this.ctx.state === "suspended") this.ctx.resume().catch(() => {});
    return this.ctx;
  }

  now() {
    if (!this.playing) return S.playhead;
    if (this.rate === 1 && this.ctx) return this.t0 + Math.max(0, this.ctx.currentTime - this.ac0) * FPS;
    return this.t0 + ((performance.now() - this.perf0) / 1000) * FPS * this.rate;
  }

  start(fromFrame, rate = 1) {
    this.stop();
    this.ensure();
    this.rate = rate;
    this.t0 = fromFrame;
    this.ac0 = this.ctx.currentTime + 0.06;
    this.perf0 = performance.now() + 60;
    this.playing = true;
    this.log = [];
    if (rate === 1) { this.tick(); this.timer = setInterval(() => this.tick(), TICK_MS); }
  }

  stop() {
    this.playing = false;
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    for (const n of this.live) { try { n.src.stop(); } catch (e) { /* already stopped */ } try { n.src.disconnect(); n.g.disconnect(); } catch (e) { /* gone */ } }
    this.live.clear();
    this.scheduled.clear();
  }

  audible(doc) {
    const tr = doc.tracks.filter((t) => t.kind === "audio");
    const solo = tr.some((t) => t.solo);
    return new Set(tr.filter((t) => (solo ? t.solo : !t.mute)).map((t) => t.id));
  }

  key(asset, i) { return `${asset}:${this.ctx.sampleRate}:${i}`; }

  block(asset, i) {
    const k = this.key(asset, i);
    let b = this.blocks.get(k);
    if (b) { b.used = performance.now(); return b.buf ? b : null; }
    b = { buf: null, used: performance.now(), bytes: 0 };
    this.blocks.set(k, b);
    b.p = fetch(`/api/audio_block?asset=${encodeURIComponent(asset)}&i=${i}&sr=${this.ctx.sampleRate}`)
      .then((r) => { if (!r.ok) throw new Error("block " + r.status); return r.arrayBuffer(); })
      .then((ab) => this.ctx.decodeAudioData(ab))
      .then((buf) => { b.buf = buf; b.bytes = buf.length * buf.numberOfChannels * 4; this.bytes += b.bytes; this.trim(); })
      .catch(() => { this.blocks.delete(k); });
    return null;
  }

  trim() {
    if (this.bytes < CACHE_BYTES) return;
    const arr = [...this.blocks.entries()].filter(([, b]) => b.buf).sort((a, b) => a[1].used - b[1].used);
    for (const [k, b] of arr) {
      if (this.bytes < CACHE_BYTES * 0.8) break;
      this.blocks.delete(k); this.bytes -= b.bytes;
    }
  }

  // load the blocks a stretch of the timeline needs (called while paused, so play starts without a gap)
  prefetch(doc, f0, f1) {
    if (!doc) return;
    this.ensure();
    for (const c of doc.clips) {
      if (c.type !== "audio" || !c.asset || c.on === false) continue;
      const a = Math.max(f0, c.start), b = Math.min(f1, clipEnd(c));
      if (b <= a) continue;
      const s0 = (c.in + (a - c.start)) / FPS, s1 = (c.in + (b - c.start)) / FPS;
      for (let i = Math.floor(s0 / BLOCK_S); i <= Math.floor(s1 / BLOCK_S); i += 1) this.block(c.asset, i);
    }
  }

  tick() {
    const doc = S.doc;
    if (!doc || !this.playing) return;
    const tNow = this.now();
    const horizon = tNow + AHEAD_S * FPS;
    const audible = this.audible(doc);
    for (const c of doc.clips) {
      if (c.type !== "audio" || !c.asset || c.on === false || !audible.has(c.track)) continue;
      const cs = c.start, ce = clipEnd(c);
      if (ce <= tNow || cs >= horizon) continue;
      // a voice track plays only its speaker's stretches (model/voices.js); nothing of them here: nothing to play
      const gate = isVoiceClip(c) ? gateFrames(c, lib.transcript(c.asset)) : null;
      if (gate && !gate.length) continue;
      const s0 = (c.in + (Math.max(tNow, cs) - cs)) / FPS;
      const s1 = (c.in + (Math.min(horizon, ce) - cs)) / FPS;
      for (let i = Math.floor(s0 / BLOCK_S); i <= Math.floor(s1 / BLOCK_S); i += 1) {
        const sk = `${c.id}:${i}`;
        if (this.scheduled.has(sk)) continue;
        const b = this.block(c.asset, i);
        if (!b) continue;
        // the piece of this clip that block i covers, on the timeline
        const blkTl0 = cs + (i * BLOCK_S * FPS - c.in);
        const blkTl1 = blkTl0 + BLOCK_S * FPS;
        let p0 = Math.max(cs, blkTl0), p1 = Math.min(ce, blkTl1);
        if (p1 <= tNow) { this.scheduled.add(sk); continue; }
        const nowTl = this.t0 + Math.max(0, this.ctx.currentTime - this.ac0) * FPS;
        if (p0 < nowTl + 1) p0 = Math.min(p1, nowTl + 1);   // late: start inside the piece
        if (p1 - p0 < 1) { this.scheduled.add(sk); continue; }
        const when = this.ac0 + (p0 - this.t0) / FPS;
        const offset = (c.in + (p0 - cs)) / FPS - i * BLOCK_S;
        const dur = (p1 - p0) / FPS;
        const src = this.ctx.createBufferSource();
        src.buffer = b.buf;
        const g = this.ctx.createGain();
        const curve = gainCurve(c, p0, p1, 100, gate);
        try { g.gain.setValueCurveAtTime(curve, Math.max(when, this.ctx.currentTime), dur); } catch (e) { g.gain.value = curve[0]; }
        src.connect(g); g.connect(this.master);
        src.start(Math.max(when, this.ctx.currentTime), Math.max(0, offset), dur);
        const node = { src, g };
        this.live.add(node);
        src.onended = () => { this.live.delete(node); try { g.disconnect(); } catch (e) { /* gone */ } };
        this.scheduled.add(sk);
        this.log.push({ clip: c.id, block: i, when, offset, dur, p0, p1, gated: !!gate });
      }
    }
  }

  // click a sound in the bin to hear it
  async auditionUrl(url) {
    this.ensure();
    if (this.audition) { try { this.audition.stop(); } catch (e) { /* done */ } this.audition = null; }
    const buf = await fetch(url).then((r) => r.arrayBuffer()).then((ab) => this.ctx.decodeAudioData(ab));
    const src = this.ctx.createBufferSource();
    src.buffer = buf;
    src.connect(this.master);
    src.start();
    this.audition = src;
    return buf.duration;
  }
  stopAudition() { if (this.audition) { try { this.audition.stop(); } catch (e) { /* done */ } this.audition = null; } }
}

export const audio = new AudioEngine();
