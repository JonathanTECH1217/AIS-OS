// The media bin (G7, G8, G24, G34-G38): the media/ folders as they are, prep progress per file, Find calls, sounds you
// click to hear, the shorts with Draft / Done / Exported chips, and the export queue. Drop files from Explorer onto it to
// copy them in; drag anything from it onto the timeline. Clicking a recording opens its calls (js/panels/browse.js,
// 2026-10-01); while one is open this panel hands the bin feed to that view.
import { S, subscribe, emit } from "../store.js";
import { el, clear, icon, fmtDur, fmtBytes } from "../util.js";
import { api } from "../api.js";
import { lib } from "../media/library.js";
import { audio } from "../media/audio.js";
import { openShort, run } from "../actions.js";
import { confirmDialog, toast } from "../components/modal.js";
import { openMenu } from "../components/menu.js";
import { mountBrowse, isBrowsing, onBin, openRecording, recordingTitle, recordedDate, fmtHours, callsLine } from "./browse.js";

const STAGE_NAME = { remux: "Copy", peaks: "Waveform", proxy: "Preview copy", transcript: "Transcript", speakers: "Voices" };
const LOW_DISK_GB = 15;     // B20: a note in the panel under this much free space

// Find calls waits for the voice split, so Claude labels the voices in the same pass (grill C8)
function voicesPending(a) {
  const sp = (a.stages || {}).speakers;
  return sp && (sp.state === "queued" || sp.state === "running") ? sp : null;
}

let host, list, drop;
const open = new Set(JSON.parse(localStorage.getItem("studio.bin.open") || '["inbox","shorts","sfx"]'));
let auditioning = null;

function saveOpen() { localStorage.setItem("studio.bin.open", JSON.stringify([...open])); }

export function mountBin(el_) {
  host = el_;
  clear(host);
  const up = el("input", { type: "file", multiple: true, hidden: true, onchange: (e) => uploadFiles([...e.target.files]) });
  host.append(el("div", { class: "panel-head" }, el("span", { class: "panel-title" }, "Media"), el("span", { class: "grow" }),
    el("button", { class: "icon-btn", title: "Add files (or drop them here)", onclick: () => up.click() }, icon("upload_file")),
    el("button", { class: "icon-btn", title: "New empty short", onclick: () => run("newShort") }, icon("add")), up));
  list = el("div", { class: "bin-list" });
  drop = el("div", { class: "bin-drop", hidden: true }, icon("upload_file"), "Drop to copy into media/");
  host.append(list, drop);
  mountBrowse(host, { findCalls });
  host.addEventListener("dragover", (e) => { if (e.dataTransfer.types.includes("Files")) { e.preventDefault(); drop.hidden = false; } });
  host.addEventListener("dragleave", (e) => { if (!host.contains(e.relatedTarget)) drop.hidden = true; });
  host.addEventListener("drop", (e) => { if (!e.dataTransfer.files.length) return; e.preventDefault(); drop.hidden = true;
    const dir = e.target.closest("[data-dir]") && e.target.closest("[data-dir]").dataset.dir; uploadFiles([...e.dataTransfer.files], dir); });
  subscribe("bin", render);
  render();
}

async function uploadFiles(files, dir) {
  for (const f of files) {
    try { toast(`Copying ${f.name}…`); await api.upload(f, dir || ""); toast(`${f.name} added.`); }
    catch (e) { toast(`${f.name}: ${e.message}`, true); }
  }
}

function section(key, title, count, body, extra) {
  const isOpen = open.has(key);
  const head = el("button", { class: "bin-sec-head", type: "button", onclick: () => { isOpen ? open.delete(key) : open.add(key); saveOpen(); render(); } },
    icon(isOpen ? "expand_more" : "chevron_right"), el("span", { class: "bin-sec-title" }, title), el("span", { class: "muted small" }, count), el("span", { class: "grow" }), extra || null);
  return el("section", { class: "bin-sec", dataset: { dir: key } }, head, isOpen ? body : null);
}

function stageBar(a) {
  const st = a.stages || {};
  const names = Object.keys(st);
  if (!names.length) return null;
  const running = names.find((n) => st[n].state === "running");
  const err = names.find((n) => st[n].state === "error");
  const done = names.every((n) => st[n].state === "done");
  if (done) return null;
  if (err) return el("div", { class: "bin-stage error", title: st[err].error || "" }, icon("error"), `${STAGE_NAME[err] || err} failed`,
    el("button", { class: "link", type: "button", onclick: (e) => { e.stopPropagation(); api.post(`/api/asset/${a.id}/reprep`, { stages: [err] }); } }, "Retry"));
  const cur = running || names.find((n) => st[n].state !== "done");
  const p = st[cur] ? st[cur].progress || 0 : 0;
  return el("div", { class: "bin-stage" }, el("span", { class: "small" }, `${STAGE_NAME[cur] || cur} ${Math.round(p * 100)}%`),
    el("div", { class: "progress" }, el("b", { style: { width: Math.round(p * 100) + "%" } })));
}

function draggable(node, payload) {
  node.draggable = true;
  node.addEventListener("dragstart", (e) => { e.dataTransfer.setData("application/x-studio", JSON.stringify(payload)); e.dataTransfer.effectAllowed = "copy"; });
  return node;
}

function assetRow(a) {
  const kindIcon = { video: "video_file", audio: "audio_file", image: "image" }[a.kind] || "movie";
  const sel = S.selectedAsset === a.id;
  const row = el("div", { class: "bin-item" + (sel ? " is-sel" : ""), onclick: () => { S.selectedAsset = a.id; render(); } },
    el("div", { class: "bin-item-main" },
      a.kind === "audio" ? el("button", { class: "icon-btn small" + (auditioning === a.id ? " is-on" : ""), title: "Listen", type: "button",
        onclick: (e) => { e.stopPropagation(); audition(a); } }, icon(auditioning === a.id ? "stop" : "play_arrow")) : icon(kindIcon, "bin-kind"),
      el("span", { class: "bin-name", title: a.rel }, a.name),
      el("span", { class: "muted small num" }, a.duration ? fmtDur(a.duration) : a.w ? `${a.w}×${a.h}` : ""),
      el("button", { class: "icon-btn small", title: "More", type: "button", onclick: (e) => { e.stopPropagation(); assetMenu(e, a); } }, icon("more_vert"))),
    stageBar(a));
  draggable(row, { kind: "asset", id: a.id });
  return row;
}

async function audition(a) {
  if (auditioning === a.id) { audio.stopAudition(); auditioning = null; render(); return; }
  auditioning = a.id; render();
  try {
    const d = await audio.auditionUrl(a.urls.source);
    setTimeout(() => { if (auditioning === a.id) { auditioning = null; render(); } }, d * 1000 + 100);
  } catch (e) { auditioning = null; render(); toast("Couldn't play that sound.", true); }
}

function assetMenu(e, a) {
  const rec = a.kind === "video" && a.rel.startsWith("inbox/");
  const gb = (b) => (b / 1e9).toFixed(1);
  openMenu({ x: e.clientX, y: e.clientY }, [
    rec ? { label: "Open its calls", run: () => openRecording(a.id) } : null,
    { label: "Add to timeline at playhead", disabled: !S.doc, run: () => run("placeAsset", { item: { kind: "asset", id: a.id }, f: Math.round(S.playhead), track: null }) },
    rec ? { label: a.moments ? "Find calls again…" : "Find calls…", disabled: !a.transcript || !!voicesPending(a), run: () => findCalls(a) } : null,
    // labels only (calls untouched): for a recording whose calls came before its voice split, or after a new split
    rec ? { label: "Label voices with Claude…", disabled: !a.speakers, run: () => labelVoices(a) } : null,
    // the transcript and the voice split are slow and carry fixes and labels: "Prepare again" leaves them alone
    { label: "Prepare again", disabled: !Object.keys(a.stages || {}).length, run: () => api.post(`/api/asset/${a.id}/reprep`, { stages: Object.keys(a.stages || {}).filter((s) => s !== "transcript" && s !== "speakers") }) },
    a.copy === "cache" ? { sep: true } : null,
    a.copy === "cache" ? { label: `Remove full-size copy (frees ${gb(a.copyBytes || 0)} GB)`, run: () => removeCopy(a) } : null,
    a.copy === "removed" ? { sep: true } : null,
    a.copy === "removed" ? { label: "Restore full-size copy", run: () => restoreCopy(a) } : null,
  ]);
}

// B20: free a recording's full-size MP4 copy; exports still come from the original file, Full plays the preview copy
async function removeCopy(a) {
  const ok = await confirmDialog("Remove full-size copy",
    el("div", { class: "stack" },
      el("p", {}, `Frees ${(a.copyBytes / 1e9).toFixed(1)} GB. Exports still come from the original file (${a.name}), so they look the same.`),
      el("p", { class: "muted" }, "The monitor plays the preview copy instead, even at Full. \"Restore full-size copy\" in this menu makes it again.")),
    "Remove");
  if (!ok) return;
  try { const r = await api.post(`/api/asset/${a.id}/orig`, { keep: false }); toast(`Freed ${(r.freed / 1e9).toFixed(1)} GB.`); }
  catch (err) { toast(err.message, true); }
}

async function restoreCopy(a) {
  try { await api.post(`/api/asset/${a.id}/orig`, { keep: true }); toast("Making the full-size copy again. It shows as Copy in the list."); }
  catch (err) { toast(err.message, true); }
}

async function labelVoices(a) {
  let est;
  try { toast("Counting tokens…"); est = await api.post(`/api/asset/${a.id}/voices/estimate`); }
  catch (e) { toast(e.status === 409 ? e.message : "Couldn't reach Claude: " + e.message, true); return; }
  const ok = await confirmDialog("Label voices",
    el("div", { class: "stack" },
      el("p", {}, `Claude reads the transcript with its voice tags (${est.input_tokens.toLocaleString()} tokens) and says which voice is you and whether each other voice is a woman or a man, with names and roles. That colors the captions. Your calls stay as they are.`),
      el("p", { class: "strong" }, `Estimated cost: $${est.low.toFixed(2)} to $${est.high.toFixed(2)} (${est.model}, ${est.prices}).`),
      el("p", { class: "muted" }, "Only the transcript text and the voice table (seconds, pitch) are sent, not the audio. Your own voice fixes still win.")),
    "Label voices");
  if (!ok) return;
  await api.post(`/api/asset/${a.id}/voices`);
  toast("Claude is labeling the voices. About a minute.");
}

// Claude's pass: the calls, the best bits and the voice labels, the cost shown first (it also runs by itself when a new
// recording is prepared and the estimate is under autoFindMax, B16)
export async function findCalls(a) {
  let est;
  try { toast("Counting tokens…"); est = await api.post(`/api/asset/${a.id}/moments/estimate`); }
  catch (e) { toast(e.status === 409 ? e.message : "Couldn't reach Claude: " + e.message, true); return; }
  const had = a.moments;
  const ok = await confirmDialog("Find calls",
    el("div", { class: "stack" },
      el("p", {}, `Claude reads the transcript (${est.lines.toLocaleString()} lines, ${est.input_tokens.toLocaleString()} tokens), splits it into calls with a title each, and marks the best bits: objections, bookings, funny or awkward bits, and your best lines.` +
        (est.voices ? " In the same pass it labels the voices (you, each woman, each man) that color the captions." : "")),
      el("p", { class: "strong" }, `Estimated cost: $${est.low.toFixed(2)} to $${est.high.toFixed(2)} (${est.model}, ${est.prices}).`),
      el("p", { class: "muted" }, "Only the transcript text is sent, not the audio." + (had ? " This replaces the current calls; watched marks follow their calls." : ""))),
    "Find calls");
  if (!ok) return;
  await api.post(`/api/asset/${a.id}/moments`);
  toast("Claude is reading the transcript. A few minutes for a long recording.");
}

// Recordings, newest first by the date they were recorded; the newest stays in view and the earlier ones fold under
// "Previous recordings" (closed until opened, remembered; Jonathan, 2026-10-01: "I should be able to collapse the
// previous recordings")
function recordingsBody(items) {
  const when = (a) => { const d = recordedDate(a); return d ? d.getTime() : 0; };
  const recs = items.filter((a) => a.kind === "video").sort((x, y) => when(y) - when(x) || (y.name || "").localeCompare(x.name || ""));
  const others = items.filter((a) => a.kind !== "video");
  const body = el("div", { class: "bin-items" });
  if (!recs.length && !others.length) { body.append(el("div", { class: "muted small pad" }, "Drop a recording into media/inbox (or here).")); return body; }
  if (recs.length) body.append(recordingRow(recs[0]));
  if (recs.length > 1) {
    const isOpen = open.has("inbox-prev");
    body.append(el("button", { class: "bin-sub-head", type: "button", title: isOpen ? "Fold the earlier recordings away" : "Show the earlier recordings",
      onclick: () => { isOpen ? open.delete("inbox-prev") : open.add("inbox-prev"); saveOpen(); render(); } },
      icon(isOpen ? "expand_more" : "chevron_right"), el("span", {}, "Previous recordings"), el("span", { class: "muted small" }, String(recs.length - 1))));
    if (isOpen) body.append(el("div", { class: "bin-prev" }, recs.slice(1).map(recordingRow)));
  }
  for (const a of others) body.append(assetRow(a));
  return body;
}

function recordingRow(a) {
  const sel = S.selectedAsset === a.id;
  const job = S.bin && S.bin.moments && S.bin.moments[a.id];
  const from = a.recordedFrom === "file time" ? "\nThe name has no date: this is when the file was last written, less its length." : "";
  const row = el("div", { class: "bin-item rec" + (sel ? " is-sel" : ""), dataset: { id: a.id }, title: a.rel + from + "\nClick to open its calls.",
    onclick: () => { S.selectedAsset = a.id; openRecording(a.id); } },
    el("div", { class: "bin-item-main" }, icon("video_file", "bin-kind"),
      el("span", { class: "bin-name" }, recordingTitle(a)),
      el("span", { class: "muted small num" }, a.duration ? fmtHours(a.duration) : ""),
      el("button", { class: "icon-btn small", title: "More", type: "button", onclick: (e) => { e.stopPropagation(); assetMenu(e, a); } }, icon("more_vert"))),
    stageBar(a));
  draggable(row, { kind: "asset", id: a.id });
  const sub = [];
  if (a.calls) sub.push(el("span", {}, callsLine(a)));
  if (job && job.state === "running") sub.push(el("span", { class: "strong" }, "Finding calls… " + (job.msg || "")));
  else if (job && job.state === "error") sub.push(el("span", { class: "bin-stage error", title: job.error }, "Find calls failed (hover for why)"));
  else if (!a.moments && a.transcript) {
    const vp = voicesPending(a);
    if (a.auto && a.auto.decision === "wait") sub.push(el("span", { title: `Estimate $${(+a.auto.low).toFixed(2)} to $${(+a.auto.high).toFixed(2)}` }, `Over your $${(+a.auto.cap).toFixed(2)} line:`));
    sub.push(el("button", { class: "btn small", type: "button", disabled: vp ? true : null,
      title: vp ? `Waits for the voice split (${Math.round((vp.progress || 0) * 100)} %), so Claude can label the voices in the same pass.` : null,
      onclick: (e) => { e.stopPropagation(); findCalls(a); } }, icon("auto_awesome"), "Find calls"));
  }
  const vj = S.bin && S.bin.voiceJobs && S.bin.voiceJobs[a.id];
  if (vj && vj.state === "running") sub.push(el("span", {}, "Labeling voices: " + (vj.msg || "…")));
  if (vj && vj.state === "error") sub.push(el("span", { class: "bin-stage error", title: vj.error }, "Labeling voices failed"));
  if (a.copy === "removed") sub.push(el("span", { class: "muted", title: "Removed to free space. Exports use the original file." }, "No full-size copy"));
  if (a.copy === "missing") sub.push(el("span", { class: "muted", title: "Studio is making its full-size copy again. Meanwhile sound, exports and the monitor use the original file and the preview copy." }, "Full-size copy being made"));
  if (sub.length) row.append(el("div", { class: "bin-rec-sub" }, sub));
  return row;
}

function shortRow(s) {
  const active = S.doc && S.doc.id === s.id;
  const row = el("div", { class: "bin-item short" + (active ? " is-sel" : ""), onclick: () => { if (!active) openShort(s.id); } },
    el("div", { class: "bin-item-main" }, icon("movie", "bin-kind"), el("span", { class: "bin-name" }, s.name),
      el("span", { class: "chip-status " + s.status }, { draft: "Draft", done: "Done", exported: "Exported" }[s.status] || s.status),
      el("span", { class: "muted small num" }, fmtDur(s.frames / 30)),
      el("button", { class: "icon-btn small", type: "button", title: "More", onclick: (e) => { e.stopPropagation(); shortMenu(e, s); } }, icon("more_vert"))));
  const ex = s.export;
  if (ex && (ex.state === "running" || ex.state === "queued")) row.append(el("div", { class: "bin-stage" }, el("span", { class: "small" }, ex.state === "queued" ? "Export queued" : `Exporting ${Math.round((ex.progress || 0) * 100)}%`),
    el("div", { class: "progress" }, el("b", { style: { width: Math.round((ex.progress || 0) * 100) + "%" } }))));
  if (ex && ex.state === "error") row.append(el("div", { class: "bin-stage error small", title: ex.error }, icon("error"), "Export failed (hover for why)"));
  // notes from the exporter (over 90 s, voices changed since the short was saved, ...)
  if (ex && ex.state === "done" && ex.warn && ex.warn.length) row.append(el("div", { class: "bin-stage small", title: ex.warn.join("\n") }, icon("info"), "Exported with a note (hover to read)"));
  return row;
}

function shortMenu(e, s) {
  openMenu({ x: e.clientX, y: e.clientY }, [
    { label: "Open", run: () => openShort(s.id) },
    { label: s.own === "done" ? "Mark draft" : "Mark done", run: async () => {
      if (S.doc && S.doc.id === s.id) { run("markDone"); return; }
      const d = await api.project(s.id); d.status = d.status === "done" ? "draft" : "done"; await api.saveProject(s.id, d, d.rev); } },
    { label: "Export", run: async () => { if (S.doc && S.doc.id === s.id) run("export"); else { await api.exportShort(s.id); toast("Export queued."); } } },
    s.export && s.export.url ? { label: "Play the export", run: () => window.open(s.export.url, "_blank") } : null,
    { sep: true },
    { label: "Delete (moves to media/projects/.trash)", run: async () => {
      if (!(await confirmDialog("Delete short", `Move "${s.name}" to the trash folder?`, "Delete"))) return;
      await api.del("/api/projects/" + encodeURIComponent(s.id));
      if (S.doc && S.doc.id === s.id) { S.doc = null; emit("doc"); }
    } },
  ]);
}

export function render() {
  if (!list) return;
  if (isBrowsing()) { onBin(); return; }     // a recording's calls are open: that view patches itself
  const b = S.bin;
  clear(list);
  if (!b) { list.append(el("div", { class: "muted pad" }, "Connecting…")); return; }
  const f = Object.fromEntries(b.folders.map((x) => [x.dir, x]));
  const shorts = b.shorts || [];
  if (typeof b.diskFreeGb === "number" && b.diskFreeGb < LOW_DISK_GB) {
    list.append(el("div", { class: "bin-note" }, `Only ${b.diskFreeGb.toFixed(1)} GB free. A 3-hour recording takes about 8 GB. `
      + "A recording's ⋮ menu can remove its full-size copy (about 3.6 GB for 3 hours); exports still come from the original file."));
  }
  const exAll = el("button", { class: "link small", type: "button", title: "Export every short marked Done", onclick: (e) => { e.stopPropagation(); run("exportAll"); } }, "Export all done");
  list.append(section("shorts", "Shorts", shorts.length, el("div", { class: "bin-items" },
    shorts.length ? shorts.map(shortRow) : el("div", { class: "muted small pad" }, "Open a recording, pick a call, then Make short.")), shorts.some((s) => s.own === "done" && s.status !== "exported") ? exAll : null));
  list.append(section("inbox", "Recordings", f.inbox.items.length, recordingsBody(f.inbox.items), null));
  list.append(section("sfx", "Sounds", f.sfx.items.length, el("div", { class: "bin-items" },
    f.sfx.items.length ? f.sfx.items.map(assetRow) : el("div", { class: "muted small pad" }, "Drop sound effects into media/sfx.")), null));
  list.append(section("assets", "Assets", f.assets.items.length, el("div", { class: "bin-items" },
    f.assets.items.length ? f.assets.items.map(assetRow) : el("div", { class: "muted small pad" }, "Logos, screenshots and B-roll for overlays go in media/assets.")), null));
  list.append(section("ready", "Ready to post", f.ready.items.length, el("div", { class: "bin-items" },
    f.ready.items.length ? f.ready.items.map((r) => el("div", { class: "bin-item", title: r.rel },
      el("div", { class: "bin-item-main" }, icon("check_circle", "bin-kind ok"), el("span", { class: "bin-name" }, r.name), el("span", { class: "muted small" }, fmtBytes(r.size)),
        el("button", { class: "icon-btn small", type: "button", title: "Play", onclick: () => window.open(r.url, "_blank") }, icon("play_circle"))))) :
      el("div", { class: "muted small pad" }, "Exports land in media/ready for your scheduler.")), null));
}

export function binApi() { return { render, findCalls }; }
