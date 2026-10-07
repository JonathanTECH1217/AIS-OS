// What the page knows about media: asset summaries (from the bin feed), transcripts, waveform peaks, thumbnail
// sheets and still images, each loaded once on demand. A load that finishes calls onLoaded() so views redraw.
import { api } from "../api.js";
import { S, emit } from "../store.js";

const assets = new Map();
const transcripts = new Map();   // id -> transcript | "loading" | "none"
const peaks = new Map();         // id -> {p100: Int8Array, p10: Int8Array} | "loading"
const sheets = new Map();        // url -> HTMLImageElement (complete) | "loading"
const bitmaps = new Map();       // asset id -> ImageBitmap | "loading"
const refreshing = new Set();    // asset ids whose voices are being fetched again
let listeners = new Set();

function loaded() { for (const fn of listeners) fn(); }

export const lib = {
  onLoaded(fn) { listeners.add(fn); return () => listeners.delete(fn); },

  asset(id) { return assets.get(id) || null; },
  all() { return [...assets.values()]; },
  setFromBin(bin) {
    for (const f of bin.folders || []) for (const a of f.items || []) if (a.id) assets.set(a.id, a);
    for (const [id, t] of transcripts) if (t === "none" && assets.get(id) && assets.get(id).transcript) transcripts.delete(id);
    for (const [id, t] of transcripts) {
      if (!t || typeof t !== "object") continue;
      const a = assets.get(id);
      // the words changed on the server (a spelling fix from another window, words filled in): fetch the whole
      // transcript again, voices included; the old copy stays in use until the new one is here
      if (a && a.transcriptRev && t.trev !== a.transcriptRev) this.reloadTranscript(id);
      // only the voices changed (the split landed, Claude's labels, a fix from another window, a new voiceprint)
      else if (this.voicesStale(id)) this.refreshVoices(id);
    }
  },
  async reloadTranscript(id) {
    if (refreshing.has(id)) return;
    refreshing.add(id);
    try {
      const tr = await api.transcript(id);
      transcripts.set(id, tr);
      loaded();
      emit("transcript");
    } catch (e) { /* keep the copy we have */ }
    finally { refreshing.delete(id); }
  },
  async refreshVoices(id) {
    if (refreshing.has(id)) return;
    refreshing.add(id);
    let whole = false;
    try {
      const v = await api.get(`/api/asset/${id}/voices`);
      const t = transcripts.get(id);
      // voices are one per word: if the counts differ the words changed too, so take both together
      if (t && typeof t === "object" && v.spk && v.spk.length !== t.words.length) whole = true;
      else if (t && typeof t === "object") { t.voices = v; loaded(); emit("transcript"); }
    } catch (e) { /* keep the voices we have */ }
    finally { refreshing.delete(id); }
    if (whole) this.reloadTranscript(id);
  },
  setTrev(id, trev) {       // after this window's own spelling fix: no need to fetch its own change back
    const t = transcripts.get(id);
    if (t && typeof t === "object" && trev) t.trev = trev;
  },

  transcript(id) {
    const t = transcripts.get(id);
    if (t && typeof t === "object") return t;
    if (!t) this.loadTranscript(id);
    return null;
  },
  async loadTranscript(id, force = false) {
    if (!force && transcripts.get(id) === "loading") return null;
    const a = assets.get(id);
    if (a && !a.transcript && !force) { transcripts.set(id, "none"); return null; }
    transcripts.set(id, "loading");
    try {
      const tr = await api.transcript(id);
      transcripts.set(id, tr);
      loaded();
      emit("transcript");
      return tr;
    } catch (e) {
      transcripts.set(id, "none");
      return null;
    }
  },
  // true while a transcript this asset should have isn't here yet (unknown asset counts as pending)
  transcriptPending(id) {
    const t = transcripts.get(id);
    if (t && typeof t === "object") return false;
    if (t === "none") return false;
    const a = assets.get(id);
    if (a && !a.transcript) return false;
    if (!t) this.loadTranscript(id);
    return true;
  },
  async whenTranscripts(ids, timeout = 5000) {
    const t0 = performance.now();
    while (ids.some((id) => this.transcriptPending(id)) && performance.now() - t0 < timeout) await new Promise((r) => setTimeout(r, 50));
    return !ids.some((id) => this.transcriptPending(id));
  },
  setWord(id, i, text) {
    const t = transcripts.get(id);
    if (t && typeof t === "object") { t.words[i][2] = text; t.edits = t.edits || {}; t.edits[i] = text; }
  },
  // who said each word (studio_speakers.resolve), after a fix or once the voice split lands
  setVoices(id, voices) {
    const t = transcripts.get(id);
    if (t && typeof t === "object") t.voices = voices;
  },
  voicesStale(id) {
    const t = transcripts.get(id), a = assets.get(id);
    if (!(t && typeof t === "object" && a && a.voicesRev)) return false;
    return !t.voices || t.voices.vrev !== a.voicesRev;
  },

  peaks(id) {
    const p = peaks.get(id);
    if (p && p !== "loading") return p;
    if (!p) {
      const a = assets.get(id);
      if (!a || !a.urls || !a.urls.peaks100 || !(a.stages && a.stages.peaks && a.stages.peaks.state === "done")) return null;
      peaks.set(id, "loading");
      Promise.all([fetch(a.urls.peaks100), fetch(a.urls.peaks10)])
        .then((rs) => Promise.all(rs.map((r) => (r.ok ? r.arrayBuffer() : new ArrayBuffer(0)))))
        .then(([b100, b10]) => { peaks.set(id, { p100: new Int8Array(b100), p10: new Int8Array(b10) }); loaded(); })
        .catch(() => peaks.delete(id));
    }
    return null;
  },

  // thumbnail sheet holding source second `sec`; returns {img, sx, sy, w, h} or null while loading
  thumb(id, sec) {
    const a = assets.get(id);
    const th = a && a.urls && a.urls.thumbs;
    if (!th) return null;
    // the last stretch after the final 2 s mark has no tile of its own: show the last one
    const lastIdx = Math.max(0, Math.floor(((a.duration || 0) - 0.01) / th.every) - 1);
    const idx = Math.min(Math.floor(Math.max(0, sec) / th.every), lastIdx);
    const per = th.tile * th.tile;
    const sheet = Math.floor(idx / per);
    if (sheet >= th.count) return null;
    const url = th.base + String(sheet + 1).padStart(3, "0") + ".jpg";
    let img = sheets.get(url);
    if (!img) {
      const im = new Image();
      sheets.set(url, "loading");
      im.onload = () => { sheets.set(url, im); loaded(); };
      im.onerror = () => sheets.delete(url);
      im.src = url;
      return null;
    }
    if (img === "loading") return null;
    const cell = idx % per;
    return { img, sx: (cell % th.tile) * th.w, sy: Math.floor(cell / th.tile) * th.h, w: th.w, h: th.h };
  },

  bitmap(id) {
    const b = bitmaps.get(id);
    if (b && b !== "loading") return b;
    if (!b) {
      const a = assets.get(id);
      if (!a) return null;
      bitmaps.set(id, "loading");
      fetch(a.urls.source).then((r) => r.blob()).then((bl) => createImageBitmap(bl))
        .then((bm) => { bitmaps.set(id, bm); loaded(); }).catch(() => bitmaps.delete(id));
    }
    return null;
  },

  // which file the monitor plays for a video asset at the chosen quality
  videoUrl(id) {
    const a = assets.get(id);
    if (!a || !a.urls) return null;
    const st = a.stages || {};
    const remuxDone = !st.remux || st.remux.state === "done";
    const mp4 = /\.(mp4|m4v)$/i.test(a.rel || "");
    const orig = remuxDone ? a.urls.orig : (mp4 ? a.urls.source : null);   // Edge can't be trusted with MKV
    const q = S.playing && S.playQuality ? S.playQuality : S.quality;      // no file switch in the middle of a play
    if (q !== "full" && a.proxy) return a.urls.proxy;
    return orig || (a.proxy ? a.urls.proxy : null);
  },
};

// The bin feed: a long poll on /api/bin; every answer refreshes asset summaries and the bin view.
export async function startBinFeed() {
  let since = 0;
  for (;;) {
    try {
      const b = await api.bin(since);
      // the server was updated since this page loaded: say so (the page keeps its old code until a reload)
      if (b.version) {
        if (!S.version) S.version = b.version;
        else if (b.version !== S.version && !S.updateReady) { S.updateReady = true; emit("update"); }
      }
      S.bin = b;
      lib.setFromBin(b);
      since = b.rev;
      emit("bin");
      // the palette (every short): not while a color is being picked here, or it would snap back mid-pick
      if (b.config && !S.configPending && JSON.stringify(b.config) !== JSON.stringify(S.config)) { S.config = b.config; emit("config"); emit("view"); }
      if (S.saving === "offline") { S.saving = "saved"; emit("save"); }
    } catch (e) {
      if (S.saving !== "offline") { S.saving = "offline"; emit("save"); }
      await new Promise((r) => setTimeout(r, 2000));
    }
  }
}
