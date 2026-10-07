// Every command in one registry: menus, keyboard shortcuts, right-click menus and the tests all call run(id).
// Keys follow Premiere Pro's defaults (G4).
import { S, emit, selectOnly, selected } from "./store.js";
import * as history from "./history.js";
import * as ops from "./model/ops.js";
import * as kf from "./model/keyframes.js";
import { clipById, clipEnd, clipsOn, clone, FPS, newId, newLink, normalize, seqEnd, withLinked } from "./model/doc.js";
import { lib } from "./media/library.js";
import { pb } from "./playback.js";
import { api } from "./api.js";
import { toast, openModal, confirmDialog, promptDialog } from "./components/modal.js";
import { el, fmtDur } from "./util.js";
import { resetLayout } from "./components/split.js";
import * as save from "./save.js";
import { gateFrames, isVoiceClip, NORMALIZE_TARGET, setClipGain, splitVoices, voiceTracks } from "./model/voices.js";
import { HEADLINE, makeTrailer, wrapHeadline } from "./model/trailer.js";
import { genStatus, keptRanges } from "./model/captions.js";

const ctx = () => ({ lib });
const A = new Map();
let tl = null;            // timeline api, set by app.js
export function setTimeline(api_) { tl = api_; }

function def(id, label, keys, run, extra = {}) { A.set(id, { id, label, keys, run, ...extra }); }
export function get(id) { return A.get(id); }
export function all() { return [...A.values()]; }
export function run(id, arg) {
  const a = A.get(id);
  if (!a) { console.warn("no action", id); return; }
  if (a.enabled && !a.enabled()) return;
  return a.run(arg);
}
function fail(res) { if (res && res.ok === false && res.reason) toast(res.reason, true); return res; }
const hasDoc = () => !!S.doc;
const hasSel = () => !!S.doc && S.sel.size > 0;
const ph = () => Math.round(S.playhead);

// clips under the playhead on the given tracks (default V1, A1 and the voice tracks), or the selected ones under it
function targetsAt(f, tracks = null) {
  const sel = selected().filter((c) => c.start <= f && f < clipEnd(c));
  if (sel.length) return sel.map((c) => c.id);
  const on = tracks || ["V1", "A1", ...voiceTracks(S.doc).map((t) => t.id)];
  return S.doc.clips.filter((c) => on.includes(c.track) && c.start <= f && f < clipEnd(c)).map((c) => c.id);
}

// ------------------------------------------------------------------ shorts

export async function openShort(id) {
  await save.flush();
  const doc = await api.project(id);
  normalize(doc);
  pb.pause();
  S.doc = doc;
  S.baseRev = doc.rev;
  S.sel = new Set(); S.selTransition = null; S.selMarker = null;
  S.playhead = 0;
  history.reset();
  for (const c of doc.clips) if (c.asset) lib.transcript(c.asset);
  try { window.history.replaceState(null, "", "#short=" + encodeURIComponent(id)); } catch (e) { /* ignore */ }
  emit("doc"); emit("sel"); emit("playhead"); emit("bin");
  setTimeout(() => tl && tl.zoomFit(), 30);
  // a short made before the voice tracks (2026-09-30) splits itself the first time it opens: your voice on A1,
  // theirs on A2. It's the first undo step, so Ctrl+Z puts the old layout back.
  if (needsVoiceSplit(doc)) {
    const r = history.commit("Split Audio by Voice", (d) => splitVoices(d, ctx()));
    if (r && r.ok !== false) toast("Your voice is on A1 (You) and theirs on A2 (Them) now. Ctrl+Z puts it back.");
  }
  return doc;
}

function needsVoiceSplit(doc) {
  if (voiceTracks(doc).length) return false;
  return doc.clips.some((c) => c.type === "audio" && c.track === "A1" && !isVoiceClip(c) && c.asset
    && lib.asset(c.asset) && lib.asset(c.asset).transcript && lib.asset(c.asset).speakers);
}

export async function newShortFromMoment(asset, mid) {
  try {
    const doc = await api.newProject({ asset, moment: mid });
    await openShort(doc.id);
    toast(`Opened "${doc.name}"`);
  } catch (e) { toast(e.message, true); }
}

// ------------------------------------------------------------------ File

def("newShort", "New empty short", "", async () => {
  const name = await promptDialog("New short", "Untitled short", "Name");
  if (name === null) return;
  const doc = await api.newProject({ name });
  await openShort(doc.id);
});
def("open", "Open short…", "Ctrl+O", () => {
  const shorts = (S.bin && S.bin.shorts) || [];
  const list = el("div", { class: "open-list" }, shorts.length ? shorts.map((s) => el("button", { class: "open-row", type: "button",
    onclick: () => { m.close(); openShort(s.id); } }, el("span", { class: "strong" }, s.name), el("span", { class: "chip-status " + s.status }, s.status),
    el("span", { class: "muted num" }, fmtDur(s.frames / FPS)))) : el("div", { class: "empty" }, "No shorts yet. Open a recording in the bin, pick a call, then Make short."));
  const m = openModal(el("div", { class: "stack" }, el("h2", {}, "Open a short"), list));
});
def("save", "Save", "Ctrl+S", () => save.flush(true), { enabled: hasDoc });
def("versions", "Versions…", "", async () => {
  const vs = await api.versions(S.doc.id);
  const list = el("div", { class: "open-list" }, vs.length ? vs.map((v) => el("button", { class: "open-row", type: "button", onclick: async () => {
    m.close();
    await save.flush();
    const d = await api.get(`/api/projects/${encodeURIComponent(S.doc.id)}/versions/${v.ts}`);
    history.commit("Restore Version", (draft) => { const keep = { id: draft.id, rev: draft.rev }; Object.keys(draft).forEach((k) => delete draft[k]); Object.assign(draft, normalize(d), keep); });
    toast("Version restored. Undo puts it back.");
  } }, el("span", { class: "strong" }, v.ts.replace(/^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2}).*/, "$2/$3 $4:$5")), el("span", { class: "muted" }, `${v.clips} clips`))) : el("div", { class: "empty" }, "No saved versions yet (one is kept every 10 minutes)."));
  const m = openModal(el("div", { class: "stack" }, el("h2", {}, "Versions"), el("div", { class: "body" }, "A copy of this short is kept every 10 minutes. Restoring one is an ordinary edit, so Undo puts it back."), list));
}, { enabled: hasDoc });
def("rename", "Rename…", "", async () => {
  const name = await promptDialog("Rename short", S.doc.name, "Name");
  if (name) history.commit("Rename", (d) => { d.name = name; });
}, { enabled: hasDoc });
def("markDone", "Mark done", "", () => history.commit(S.doc.status === "done" ? "Mark Draft" : "Mark Done", (d) => { d.status = d.status === "done" ? "draft" : "done"; }),
  { enabled: hasDoc, label: () => (S.doc && S.doc.status === "done" ? "Mark draft" : "Mark done") });
// G5 (2026-10-02): a short whose captions haven't been generated asks before it goes out
function askGenerate(st) {
  return new Promise((resolve) => {
    let done = false;
    const end = (v) => { done = true; m.close(); resolve(v); };
    const without = el("button", { class: "btn quiet", type: "button", onclick: () => end("export") }, st === "part" ? "Export as it is" : "Export without captions");
    const gen = el("button", { class: "btn", type: "button", onclick: () => end("generate") }, "Generate and export");
    const m = openModal(el("div", { class: "stack gen-ask" }, el("h2", {}, "Generate captions first?"),
      el("div", { class: "body" }, st === "part" ? "Some footage was added after the captions were made, so part of this short has none."
        : "This short has no captions yet. They're made once it's trimmed: a second listen to what you kept, then Claude picks the reading that makes sense. About 1 to 2 cents."),
      el("div", { class: "actions" }, without, gen)), { onClose: () => { if (!done) resolve(null); } });
  });
}

def("export", "Export", "Ctrl+M", async () => {
  // captions come from the transcripts: let them arrive before the last save (a just-opened short may still be loading)
  await lib.whenTranscripts([...new Set(S.doc.clips.filter((c) => c.track === "A1" && c.asset).map((c) => c.asset))]);
  const len = seqEnd(S.doc);
  if (!len) { toast("Nothing on the timeline to export.", true); return; }
  const st = S.doc.captions.on ? genStatus(S.doc) : null;
  if (st === "none" || st === "part") {
    const pick = await askGenerate(st);
    if (!pick) return;
    if (pick === "generate" && !(await generateCaptions())) return;
  }
  await save.flush(true);
  if (len > 90 * FPS) toast(`This short runs ${fmtDur(len / FPS)}, over the 90 s Facebook Reels limit. Exporting anyway.`, true);
  try { await api.exportShort(S.doc.id); toast("Export queued. It lands in media/ready."); } catch (e) { toast(e.message, true); }
}, { enabled: hasDoc });
def("exportAll", "Export all done shorts", "Ctrl+Shift+M", async () => {
  await save.flush(true);
  const r = await api.exportAll();
  const names = (xs) => xs.map((n) => `"${n}"`).join(", ");
  const notes = [(r.noCaptions || []).length ? `Without captions: ${names(r.noCaptions)}.` : "",
    (r.partCaptions || []).length ? `Part of the footage uncaptioned: ${names(r.partCaptions)}.` : ""].filter(Boolean).join(" ");
  toast((r.queued ? `${r.queued} short${r.queued > 1 ? "s" : ""} queued for export.` : "No shorts marked done are waiting.") + (notes ? " " + notes : ""), !!notes);
  return r;
});

// Generate captions (G1-G7, 2026-10-02): the server listens again to just the parts the speech clips keep, then
// Claude picks where the two listens differ (studio_gencaps.py). The words go into the short as one undo step, tied
// to the recording's seconds, so later cuts keep them right (G3). Resolves true when the captions are in.
export async function generateCaptions() {
  if (!S.doc) return false;
  if (S.genCaps && S.genCaps.state === "running") { toast("The captions are already being made.", true); return false; }
  const pid = S.doc.id;
  const kept = keptRanges(S.doc);
  const assets = Object.keys(kept).filter((a) => { const x = lib.asset(a); return !x || x.transcript; });
  if (!assets.length) { toast("Nothing to caption: put a clip with speech on A1 (You) or A2 (Them).", true); return false; }
  const job = { pid, state: "running", msg: "Starting", progress: 0 };
  S.genCaps = job;
  emit("gencaps");
  const results = {};
  try {
    for (const asset of assets) {
      const j = await api.genCaptions(asset, kept[asset]);
      for (;;) {
        await new Promise((r) => setTimeout(r, 500));
        const s = await api.captionJob(j.id);
        job.msg = s.msg; job.progress = s.progress || 0;
        emit("gencaps");
        if (s.state === "done") { results[asset] = s.result; break; }
        if (s.state === "error") throw new Error(s.error || "the job stopped");
      }
    }
  } catch (e) {
    Object.assign(job, { state: "error", error: e.message });
    emit("gencaps");
    toast("Couldn't make the captions: " + e.message, true);
    return false;
  }
  job.state = "done";
  emit("gencaps");
  if (!S.doc || S.doc.id !== pid) { toast("The captions finished after that short was closed. Open it and generate them again.", true); return false; }
  history.commit("Generate Captions", (d) => {
    d.captions.mode = "generate";
    d.captions.gen = Object.assign({}, d.captions.gen || {}, results);
    d.captions.on = true;
  });
  const rs = Object.values(results);
  const words = rs.reduce((n, r) => n + r.words.length, 0), added = rs.reduce((n, r) => n + (r.added || 0), 0);
  const cost = rs.reduce((n, r) => n + (r.cost || 0), 0);
  toast(`Captions made: ${words} words${added ? `, ${added} more than the first transcript heard` : ""}${cost ? `, ${(cost * 100).toFixed(1)} cents` : ""}.`
    + (rs.some((r) => r.note) ? " " + rs.find((r) => r.note).note : ""));
  return true;
}
def("generateCaptions", "Generate captions", "", () => generateCaptions(), {
  enabled: () => hasDoc() && Object.keys(keptRanges(S.doc)).length > 0 && !(S.genCaps && S.genCaps.state === "running"),
  label: () => (S.doc && genStatus(S.doc) === "ok" ? "Generate captions again" : "Generate captions") });

// ------------------------------------------------------------------ Edit

def("undo", "Undo", "Ctrl+Z", () => history.undo(), { enabled: () => !!history.undoLabel(), label: () => (history.undoLabel() ? "Undo " + history.undoLabel() : "Undo") });
def("redo", "Redo", "Ctrl+Shift+Z", () => history.redo(), { enabled: () => !!history.redoLabel(), label: () => (history.redoLabel() ? "Redo " + history.redoLabel() : "Redo") });
def("copy", "Copy", "Ctrl+C", () => {
  const cs = selected();
  const t0 = Math.min(...cs.map((c) => c.start));
  S.clipboard = cs.map((c) => { const x = clone(c); x.start -= t0; return x; });
  toast(`Copied ${cs.length} clip${cs.length > 1 ? "s" : ""}.`);
}, { enabled: hasSel });
def("cut", "Cut", "Ctrl+X", () => { run("copy"); run("clear"); }, { enabled: hasSel });
function paste(insert) {
  if (!S.clipboard || !S.clipboard.length) return;
  const f = ph();
  const res = history.commit(insert ? "Paste Insert" : "Paste", (d) => {
    const links = new Map();
    const ids = [];
    const len = Math.max(...S.clipboard.map((c) => c.start + c.out - c.in));
    if (insert) ops.insertSpace(d, f, len);
    for (const c0 of S.clipboard) {
      const c = clone(c0);
      c.id = newId(d); c.start += f;
      if (c.link) { if (!links.has(c.link)) links.set(c.link, newLink(d)); c.link = links.get(c.link); }
      if (!d.tracks.some((t) => t.id === c.track)) c.track = c.type === "audio" ? "A1" : "V1";
      ops.placeClip(d, ctx(), c);
      ids.push(c.id);
    }
    return { ok: true, ids };
  });
  if (res.ids) selectOnly(res.ids);
}
def("paste", "Paste", "Ctrl+V", () => paste(false), { enabled: () => hasDoc() && !!S.clipboard });
def("pasteInsert", "Paste insert", "Ctrl+Shift+V", () => paste(true), { enabled: () => hasDoc() && !!S.clipboard });
def("clear", "Delete", "Delete", () => {
  if (S.selTransition) { history.commit("Delete Transition", (d) => { d.transitions = d.transitions.filter((t) => t.id !== S.selTransition); }); S.selTransition = null; return; }
  if (S.selMarker && !S.sel.size) { history.commit("Delete Marker", (d) => { d.markers = d.markers.filter((m) => m.id !== S.selMarker); }); S.selMarker = null; return; }
  fail(history.commit("Delete", (d) => ops.lift(d, ctx(), [...S.sel])));
  S.sel = new Set(); emit("sel");
}, { enabled: () => hasDoc() && (S.sel.size > 0 || !!S.selTransition || !!S.selMarker) });
def("rippleDelete", "Ripple delete", "Shift+Delete", () => {
  if (!S.sel.size) { fail(history.commit("Ripple Delete Gap", (d) => ops.rippleGap(d, ctx(), "V1", ph()))); return; }
  const r = fail(history.commit("Ripple Delete", (d) => ops.rippleDelete(d, ctx(), [...S.sel])));
  if (r.ok !== false) { S.sel = new Set(); emit("sel"); }
}, { enabled: hasDoc });
def("selectAll", "Select all", "Ctrl+A", () => selectOnly(S.doc.clips.map((c) => c.id)), { enabled: hasDoc });
def("deselect", "Deselect all", "Ctrl+Shift+A", () => { S.sel = new Set(); S.selTransition = null; S.selMarker = null; emit("sel"); }, { enabled: hasDoc });
def("shortcuts", "Keyboard shortcuts", "?", () => {
  const rows = all().filter((a) => a.keys).map((a) => el("div", { class: "kb-row" }, el("span", {}, typeof a.label === "function" ? a.label() : a.label), el("span", { class: "key" }, a.keys)));
  openModal(el("div", { class: "stack" }, el("h2", {}, "Keyboard shortcuts"), el("div", { class: "kb-grid" }, rows)), { wide: true });
});
def("resetLayout", "Reset layout", "", () => resetLayout());

// ------------------------------------------------------------------ Clip

def("link", "Link / unlink", "Ctrl+L", () => {
  const cs = selected();
  const linked = cs.length > 1 && cs.every((c) => c.link && c.link === cs[0].link);
  history.commit(linked || (cs.length === 1 && cs[0].link) ? "Unlink" : "Link", (d) => ops.setLink(d, cs.map((c) => c.id), !(linked || (cs.length === 1 && cs[0].link))));
}, { enabled: hasSel });
def("enable", "Enable", "Shift+E", () => history.commit("Enable", (d) => ops.toggleEnable(d, [...S.sel])), { enabled: hasSel });
def("split", "Add edit", "Ctrl+K", () => fail(history.commit("Add Edit", (d) => ops.split(d, ctx(), withLinked(d, targetsAt(ph())), ph()))), { enabled: hasDoc });
def("splitAll", "Add edit to all tracks", "Ctrl+Shift+K", () => fail(history.commit("Add Edit", (d) => ops.splitAll(d, ctx(), ph()))), { enabled: hasDoc });
def("join", "Join through edits", "", (id) => {
  const cid = typeof id === "string" ? id : [...S.sel][0];
  if (!cid) { toast("Select a clip beside the cut, or right-click the cut.", true); return; }
  fail(history.commit("Join Through Edit", (d) => ops.joinThrough(d, ctx(), cid)));
}, { enabled: hasDoc });
def("newText", "New text", "", (arg = {}) => {
  const f = arg.f !== undefined ? arg.f : ph();
  const track = arg.track || "V2";
  const res = history.commit("New Text", (d) => {
    if (!d.tracks.some((t) => t.id === track)) ops.addTrack(d, "video");
    return ops.placeClip(d, ctx(), { track: d.tracks.some((t) => t.id === track) ? track : "V2", type: "text", in: 0, out: 3 * FPS, start: f, on: true,
      text: { str: "Your title", size: 110, color: "#FFFFFF", stroke: "#000000", strokeW: 8 }, fx: { posY: { v: 420 } } });
  });
  if (res.ids) { selectOnly(res.ids); setTimeout(() => emit("focusText"), 50); }
}, { enabled: hasDoc });
function newShape(kind) {
  const sizes = { rect: [900, 140], ellipse: [320, 320], arrow: [420, 160], bar: [1080, 24] };
  const [w, h] = sizes[kind];
  const res = history.commit("New Shape", (d) => ops.placeClip(d, ctx(), { track: "V2", type: "shape", in: 0, out: 3 * FPS, start: ph(), on: true,
    shape: { kind: kind === "bar" ? "rect" : kind, w, h, fill: "#FFD400", radius: kind === "rect" ? 24 : 0, stroke: null, strokeW: 0 }, fx: {} }));
  if (res.ids) selectOnly(res.ids);
}
def("newBox", "Box", "", () => newShape("rect"), { enabled: hasDoc });
def("newBar", "Bar", "", () => newShape("bar"), { enabled: hasDoc });
def("newCircle", "Circle", "", () => newShape("ellipse"), { enabled: hasDoc });
def("newArrow", "Arrow", "", () => newShape("arrow"), { enabled: hasDoc });

// drop from the bin (or the bin's "Add to timeline"): a recording, a moment, a sound or an image
def("placeAsset", "Place", "", ({ item, f, track, insert }) => {
  const a = lib.asset(item.asset || item.id);
  if (!a) { toast("That file isn't ready yet.", true); return; }
  let fin = 0, fout = a.duration ? Math.floor(a.duration * FPS) : 5 * FPS;
  if (item.kind === "moment") { fin = Math.round(item.start * FPS); fout = Math.round(item.end * FPS); }
  if (a.kind === "image") fout = 5 * FPS;
  const kindOf = (id) => { const t = S.doc.tracks.find((x) => x.id === id); return t && t.kind; };
  // sounds go on the first audio track that isn't a voice track (A3 "Sounds" in a new short), made if missing
  const soundsTrack = (d) => {
    const t = d.tracks.find((x) => x.kind === "audio" && x.id !== "A1" && !x.voice);
    if (t) return t.id;
    const r = ops.addTrack(d, "audio");
    const made = d.tracks.find((x) => x.id === r.id);
    if (made && voiceTracks(d).length) made.name = "Sounds";
    return r.id;
  };
  const res = history.commit("Place Clip", (d) => {
    const ids = [];
    if (a.kind === "audio") {
      // dropped on a voice track it would cut a hole in that voice: it goes on the sounds track instead
      const onVoice = d.tracks.some((t) => t.id === track && t.voice);
      const tr = kindOf(track) === "audio" && !onVoice ? track : soundsTrack(d);
      if (!d.tracks.some((t) => t.id === tr)) ops.addTrack(d, "audio");
      const r = ops.placeClip(d, ctx(), { track: tr, type: "audio", asset: a.id, in: fin, out: fout, start: f, on: true, fadeIn: 0, fadeOut: 0, fx: {} }, { insert });
      ids.push(...(r.ids || []));
    } else if (a.kind === "image") {
      const tr = kindOf(track) === "video" ? track : "V2";
      const r = ops.placeClip(d, ctx(), { track: tr, type: "image", asset: a.id, in: 0, out: fout, start: f, on: true, fx: {} }, { insert });
      ids.push(...(r.ids || []));
    } else {
      const audioOnly = kindOf(track) === "audio";
      const link = a.hasAudio && !audioOnly ? newLink(d) : null;
      if (!audioOnly) {
        const tr = kindOf(track) === "video" ? track : "V1";
        const r = ops.placeClip(d, ctx(), { track: tr, type: "video", asset: a.id, in: fin, out: fout, start: f, link, on: true, fx: {} }, { insert });
        ids.push(...(r.ids || []));
      }
      if (a.hasAudio) {
        const tr = audioOnly ? track : "A1";
        // a short with voice tracks keeps them: speech lands as You on A1 and Them on the other side's track
        const them = !audioOnly && a.transcript ? voiceTracks(d).find((t) => t.voice === "them") : null;
        const me = them && voiceTracks(d).some((t) => t.id === "A1" && t.voice === "me");
        const base = { type: "audio", asset: a.id, in: fin, out: fout, start: f, link, on: true, fadeIn: 0, fadeOut: 0, fx: {} };
        const r = ops.placeClip(d, ctx(), Object.assign({ track: tr }, base, me ? { voice: "me" } : {}), { insert: false });
        ids.push(...(r.ids || []));
        if (me) {
          const r2 = ops.placeClip(d, ctx(), Object.assign({ track: them.id, voice: "them" }, base), { insert: false });
          ids.push(...(r2.ids || []));
        }
      }
    }
    return { ok: true, ids };
  });
  if (res.ids) selectOnly(res.ids);
  if (a.kind === "video") lib.transcript(a.id);
});

// ------------------------------------------------------------------ Sequence

def("rippleTrimPrev", "Ripple trim previous edit to playhead", "Q", () => {
  const f = ph();
  const ids = targetsAt(f);
  if (!ids.length) return;
  const c = clipById(S.doc, ids[0]);
  const d0 = f - c.start;
  const res = fail(history.commit("Ripple Trim", (d) => ops.rippleTrim(d, ctx(), withLinked(d, ids), "in", d0)));
  if (res.ok !== false) pb.seek(c.start);
}, { enabled: hasDoc });
def("rippleTrimNext", "Ripple trim next edit to playhead", "W", () => {
  const f = ph();
  const ids = targetsAt(f);
  if (!ids.length) return;
  const c = clipById(S.doc, ids[0]);
  fail(history.commit("Ripple Trim", (d) => ops.rippleTrim(d, ctx(), withLinked(d, ids), "out", -(clipEnd(c) - f))));
}, { enabled: hasDoc });
def("markIn", "Mark in", "I", () => history.commit("Mark In", (d) => { d.range = d.range || {}; d.range.in = ph(); if (d.range.out !== null && d.range.out !== undefined && d.range.out <= d.range.in) d.range.out = null; }, { key: "range" }), { enabled: hasDoc });
def("markOut", "Mark out", "O", () => history.commit("Mark Out", (d) => { d.range = d.range || {}; d.range.out = ph(); if (d.range.in !== null && d.range.in !== undefined && d.range.in >= d.range.out) d.range.in = null; }, { key: "range" }), { enabled: hasDoc });
def("clearInOut", "Clear in and out", "Ctrl+Shift+X", () => history.commit("Clear In/Out", (d) => { d.range = { in: null, out: null }; }), { enabled: hasDoc });
def("lift", "Lift", ";", () => fail(history.commit("Lift", (d) => ops.rangeCut(d, ctx(), false))), { enabled: hasDoc });
def("extract", "Extract", "'", () => fail(history.commit("Extract", (d) => ops.rangeCut(d, ctx(), true))), { enabled: hasDoc });
function transitionAt(kind, arg) {
  let track = arg && arg.track, f = arg && arg.f;
  if (!track) {
    // the cut nearest the playhead on V1 (or on the selected clip's track)
    const tr = (selected()[0] && selected()[0].type !== "audio") ? selected()[0].track : "V1";
    const cuts = [];
    for (const c of clipsOn(S.doc, tr)) cuts.push(c.start, clipEnd(c));
    if (!cuts.length) { toast("No clips on " + tr + ".", true); return; }
    f = cuts.reduce((a, b) => (Math.abs(b - ph()) < Math.abs(a - ph()) ? b : a));
    track = tr;
  }
  const res = fail(history.commit(kind === "dip" ? "Dip to Black" : "Cross Dissolve", (d) => ops.addTransition(d, ctx(), track, f, kind, 15)));
  if (res.ok && res.dur < 15) toast(`Transition shortened to ${res.dur} frames (not enough extra footage).`);
}
def("dissolve", "Cross dissolve", "Ctrl+D", () => transitionAt("dissolve"), { enabled: hasDoc });
def("dip", "Dip to black", "", () => transitionAt("dip"), { enabled: hasDoc });
def("dissolveAt", "Cross dissolve", "", (arg) => transitionAt("dissolve", arg));
def("dipAt", "Dip to black", "", (arg) => transitionAt("dip", arg));
def("addMarker", "Add marker", "M", () => history.commit("Add Marker", (d) => ops.addMarker(d, ph())), { enabled: hasDoc });

// Voice tracks (Jonathan 2026-09-30, V1-V3)
def("splitVoices", "Split audio by voice", "", () => {
  const r = fail(history.commit("Split Audio by Voice", (d) => splitVoices(d, ctx())));
  if (r && r.ok !== false) toast("Your voice is on A1 (You), the other side's on A2 (Them). Sounds go on the track below.");
  return r;
}, { enabled: () => hasDoc() && S.doc.clips.some((c) => c.type === "audio" && c.track === "A1" && !isVoiceClip(c)) });

// Make trailer (T1-T4): Claude drafts three headlines, Jonathan picks one (or types his own), then the peak goes
// to the front, the call reaches back to its last ring, the Riser lands at the hard cut, and the headline goes on.
function chooseHeadline(options) {
  return new Promise((resolve) => {
    let done = false;
    const name = "hl" + Date.now();
    const radios = options.map((o, i) => el("label", { class: "hl-opt" },
      el("input", { type: "radio", name, value: o, checked: i === 0 ? true : null }), el("span", {}, o)));
    const own = el("input", { type: "text", placeholder: "Or type your own", class: "hl-own" });
    const ok = el("button", { class: "btn", type: "button" }, "Make trailer");
    const cancel = el("button", { class: "btn quiet", type: "button" }, "Cancel");
    const m = openModal(el("div", { class: "stack" }, el("h2", {}, "Pick the headline"),
      el("p", { class: "muted" }, "It sits in a white box at the top through the peak, so it is the thumbnail."),
      el("div", { class: "hl-list" }, radios, own), el("div", { class: "actions" }, cancel, ok)), { onClose: () => { if (!done) resolve(null); } });
    ok.onclick = () => {
      done = true;
      const pick = own.value.trim() || ((m.el || document).querySelector(`input[name="${name}"]:checked`) || {}).value;
      m.close();
      resolve(pick || null);
    };
    cancel.onclick = () => { done = true; m.close(); resolve(null); };
  });
}
let headlineCtx = null;
function measureHeadline(s) {
  if (!headlineCtx) headlineCtx = document.createElement("canvas").getContext("2d");
  headlineCtx.fontKerning = "none";
  headlineCtx.font = `${HEADLINE.size}px "Montserrat Black", "Google Sans", Arial, sans-serif`;
  return headlineCtx.measureText(s).width;
}
def("makeTrailer", "Make trailer", "", async (arg = {}) => {
  const { in: a, out: b } = S.doc.range || {};
  if (a === null || b === null || a === undefined || b === undefined || b <= a) { toast("Mark the peak first: I at its start, O just before the reward.", true); return; }
  const under = clipsOn(S.doc, "V1").filter((c) => c.type === "video" && c.start < b && clipEnd(c) > a);
  if (!under.length) { toast("There's no video under the marks.", true); return; }
  const asset = under[0].asset;
  const last = under[under.length - 1];
  const s0 = (under[0].in + Math.max(0, a - under[0].start)) / FPS, s1 = (last.in + (Math.min(b, clipEnd(last)) - last.start)) / FPS;
  const title = (S.doc.moment && S.doc.moment.title) || S.doc.name || "";
  let options = arg.options || null;
  if (!options) {
    toast("Claude is writing three headlines…");
    try { options = (await api.post(`/api/asset/${asset}/headlines`, { from: s0, to: s1, title: title.replace(/^['"]|['"]$/g, "") })).headlines; }
    catch (e) { options = null; }
  }
  if (!options || !options.length) options = [title.replace(/^['"]|['"]$/g, "") || "Your headline"];
  const pick = arg.pick || await chooseHeadline(options);
  if (!pick) return;
  const first = clipsOn(S.doc, "V1").filter((c) => c.type === "video")[0];
  let ring = arg.ring !== undefined ? arg.ring : null;
  if (arg.ring === undefined && first && first.asset) {
    try { ring = (await api.get(`/api/asset/${first.asset}/ring?t=${(first.in / FPS).toFixed(3)}`)).ring; } catch (e) { ring = null; }
  }
  const riserAsset = lib.all().find((x) => x.kind === "audio" && /riser/i.test(x.name || ""));
  const soundsTrack = (d) => {
    const t = d.tracks.find((x) => x.kind === "audio" && x.id !== "A1" && !x.voice);
    if (t) return t.id;
    const r = ops.addTrack(d, "audio");
    const made = d.tracks.find((x) => x.id === r.id);
    if (made) made.name = "Sounds";
    return r.id;
  };
  const res = fail(history.commit("Make Trailer", (d) => makeTrailer(d, ctx(), {
    a, b, ringFrame: ring !== null && ring !== undefined ? Math.round(ring * FPS) : null,
    headline: wrapHeadline(pick, measureHeadline),
    riser: riserAsset ? { id: riserAsset.id, frames: Math.floor((riserAsset.duration || 2) * FPS) } : null, soundsTrack })));
  if (!res || res.ok === false) return res;
  S.playhead = 0; emit("playhead");
  toast(`Trailer made: the peak (${(res.tease / FPS).toFixed(1)} s) opens, then ${res.lead ? `the dial tone (${(res.lead / FPS).toFixed(1)} s before the pickup)` : "the call (no ring found before it)"}`
    + `${riserAsset ? ", the Riser on the cut" : ", no Riser in media/sfx to place"}. The headline is on ${res.headlineTrack}.`);
  return res;
}, { enabled: () => hasDoc() && !!(S.doc.range && S.doc.range.in !== null && S.doc.range.out !== null) });

// Normalize voices: each voice track's speech measured on the server (EBU R128 loudness over the stretches it plays)
// and its clips set so both land on the same level. One undo step.
def("normalizeVoices", "Normalize voices", "", async () => {
  const tracks = voiceTracks(S.doc);
  const report = [];
  const gains = new Map();
  for (const t of tracks) {
    const clips = S.doc.clips.filter((c) => c.track === t.id && c.type === "audio" && c.asset && c.on !== false);
    const byAsset = new Map();
    for (const c of clips) {
      const gate = gateFrames(c, lib.transcript(c.asset)) || [[c.in, c.out]];
      const list = byAsset.get(c.asset) || [];
      for (const [a, b] of gate) list.push([a / FPS, b / FPS]);
      byAsset.set(c.asset, list);
    }
    let sum = 0, secs = 0;
    for (const [asset, ranges] of byAsset) {
      if (!ranges.length) continue;
      const r = await api.post("/api/loudness", { asset, ranges });
      if (typeof r.lufs === "number" && isFinite(r.lufs) && r.seconds > 0) { sum += r.lufs * r.seconds; secs += r.seconds; }
    }
    if (!secs) { report.push(`${t.name || t.id}: nothing to measure`); continue; }
    const lufs = sum / secs;
    const gain = Math.max(-20, Math.min(24, NORMALIZE_TARGET - lufs));
    gains.set(t.id, gain);
    report.push(`${t.name || t.id} ${lufs.toFixed(1)} LUFS, ${gain >= 0 ? "+" : ""}${gain.toFixed(1)} dB`);
  }
  if (!gains.size) { toast("No voice to measure yet.", true); return; }
  history.commit("Normalize Voices", (d) => {
    for (const c of d.clips) if (gains.has(c.track) && c.type === "audio") setClipGain(c, gains.get(c.track));
    return { ok: true };
  });
  toast(`Voices evened to ${NORMALIZE_TARGET} LUFS: ${report.join(" · ")}`);
  return { gains: Object.fromEntries(gains), report };
}, { enabled: () => hasDoc() && voiceTracks(S.doc).length > 0 });
def("editMarker", "Edit marker", "", async (id) => {
  const m = S.doc.markers.find((x) => x.id === (id || S.selMarker));
  if (!m) return;
  const colors = ["green", "red", "yellow", "blue", "purple"];
  let color = m.color;
  const note = el("input", { value: m.note || "", placeholder: "Note (e.g. hook ends)" });
  const sw = el("div", { class: "chips" }, colors.map((c) => el("button", { class: "chip" + (c === color ? " is-on" : ""), type: "button", onclick: (e) => { color = c; sw.querySelectorAll(".chip").forEach((b) => b.classList.remove("is-on")); e.currentTarget.classList.add("is-on"); } }, c)));
  const ok = el("button", { class: "btn", type: "button" }, "Save");
  const md = openModal(el("div", { class: "stack" }, el("h2", {}, "Marker"), el("div", { class: "field" }, el("label", {}, "Note"), note), sw, el("div", { class: "actions" }, ok)));
  ok.onclick = () => { md.close(); history.commit("Edit Marker", (d) => { const x = d.markers.find((y) => y.id === m.id); x.note = note.value; x.color = color; }); };
}, { enabled: hasDoc });
def("snap", "Snap", "S", () => { S.snap = !S.snap; emit("view"); toast(S.snap ? "Snapping on" : "Snapping off"); }, { checked: () => S.snap });
def("zoomIn", "Zoom in", "=", () => tl && tl.zoomBy(1.5));
def("zoomOut", "Zoom out", "-", () => tl && tl.zoomBy(1 / 1.5));
def("zoomFit", "Zoom to sequence", "\\", () => tl && tl.zoomFit());
def("addVideoTrack", "Add video track", "", () => history.commit("Add Track", (d) => ops.addTrack(d, "video")), { enabled: hasDoc });
def("addAudioTrack", "Add audio track", "", () => history.commit("Add Track", (d) => ops.addTrack(d, "audio")), { enabled: hasDoc });
def("safe", "Safe zones", "", () => { S.safe = !S.safe; emit("view"); }, { checked: () => S.safe });
for (const [q, label] of [["full", "Full"], ["half", "1/2"], ["quarter", "1/4"]]) {
  def("quality." + q, label, "", () => { S.quality = q; try { localStorage.setItem("studio.quality", q); } catch (e) { /* */ } emit("view"); }, { checked: () => S.quality === q });
}

// ------------------------------------------------------------------ transport and tools

def("play", "Play / pause", "Space", () => pb.toggle(), { enabled: hasDoc });
def("shuttleJ", "Shuttle back", "J", () => pb.shuttle(-1), { enabled: hasDoc });
def("shuttleK", "Stop", "K", () => pb.shuttle(0), { enabled: hasDoc });
def("shuttleL", "Shuttle forward", "L", () => pb.shuttle(1), { enabled: hasDoc });
def("stepBack", "Back one frame", "Left", () => pb.step(-1), { enabled: hasDoc });
def("stepFwd", "Forward one frame", "Right", () => pb.step(1), { enabled: hasDoc });
def("stepBack5", "Back five frames", "Shift+Left", () => pb.step(-5), { enabled: hasDoc });
def("stepFwd5", "Forward five frames", "Shift+Right", () => pb.step(5), { enabled: hasDoc });
function edits() { const s = new Set([0, seqEnd(S.doc)]); for (const c of S.doc.clips) { s.add(c.start); s.add(clipEnd(c)); } return [...s].sort((a, b) => a - b); }
def("prevEdit", "Previous edit", "Up", () => { const f = ph(); const e = edits().filter((x) => x < f); pb.seek(e.length ? e[e.length - 1] : 0); }, { enabled: hasDoc });
def("nextEdit", "Next edit", "Down", () => { const f = ph(); const e = edits().find((x) => x > f); if (e !== undefined) pb.seek(e); }, { enabled: hasDoc });
def("home", "Go to start", "Home", () => pb.seek(0), { enabled: hasDoc });
def("end", "Go to end", "End", () => pb.seek(seqEnd(S.doc)), { enabled: hasDoc });

export const TOOLS = [
  ["select", "Selection", "V", "arrow_selector_tool"], ["razor", "Razor", "C", "content_cut"], ["hand", "Hand", "H", "pan_tool"],
  ["zoom", "Zoom", "Z", "zoom_in"], ["ripple", "Ripple edit", "B", "start"], ["rolling", "Rolling edit", "N", "sync_alt"],
  ["slip", "Slip", "Y", "swap_horiz"], ["slide", "Slide", "U", "width"], ["pen", "Pen (keyframes)", "P", "ink_pen"], ["text", "Type", "T", "title"],
];
for (const [id, label, key] of TOOLS) def("tool." + id, label + " tool", key, () => { S.tool = id; emit("tool"); }, { checked: () => S.tool === id });

// keyframe helpers used by Effect Controls
export function kfCommit(label, clipId, fn, key) {
  return history.commit(label, (d) => { const c = clipById(d, clipId); if (!c) return { ok: false }; fn(c, d); return { ok: true }; }, { key });
}
export { kf };
