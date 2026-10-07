// The top bar (G42): Google Docs style. Mark and short name on the left with File / Edit / Clip / Sequence under
// them (every item shows its shortcut); save status, Undo / Redo and a blue Export button on the right.
import { S, subscribe } from "./store.js";
import { el, clear, icon } from "./util.js";
import { get, run, TOOLS } from "./actions.js";
import { openMenu } from "./components/menu.js";
import * as history from "./history.js";
import { api } from "./api.js";

function item(id, extra = {}) {
  const a = get(id);
  if (!a) return null;
  return { label: a.label, keys: a.keys, run: () => run(id), disabled: () => (a.enabled ? !a.enabled() : false), checked: a.checked, ...extra };
}

const MENUS = {
  File: () => [item("newShort"), item("open"), { sep: true }, item("save"), item("versions"), item("rename"), item("markDone"), { sep: true }, item("export"), item("exportAll")],
  Edit: () => [item("undo"), item("redo"), { sep: true }, item("cut"), item("copy"), item("paste"), item("pasteInsert"), item("clear"), item("rippleDelete"),
    { sep: true }, item("selectAll"), item("deselect"), { sep: true }, item("shortcuts"), item("resetLayout")],
  Clip: () => [item("link"), item("enable"), item("split"), item("join"), { sep: true }, item("newText"),
    { label: "New shape", sub: [item("newBox"), item("newBar"), item("newCircle"), item("newArrow")] },
    { sep: true }, item("splitVoices"), item("normalizeVoices"), { sep: true }, item("generateCaptions"), item("makeTrailer")],
  Sequence: () => [item("split"), item("splitAll"), item("rippleTrimPrev"), item("rippleTrimNext"), { sep: true },
    item("markIn"), item("markOut"), item("clearInOut"), item("lift"), item("extract"), { sep: true },
    item("dissolve"), item("dip"), item("addMarker"), { sep: true }, item("snap"), item("zoomIn"), item("zoomOut"), item("zoomFit"),
    { sep: true }, item("addVideoTrack"), item("addAudioTrack"), { sep: true }, item("safe"),
    { label: "Playback quality", sub: [item("quality.full"), item("quality.half"), item("quality.quarter")] }],
};

export function mountTopbar(host) {
  clear(host);
  const name = el("button", { class: "tb-name", type: "button", title: "Rename", onclick: () => run("rename") }, "Monarc Studio");
  const status = el("span", { class: "chip-status" });
  const saving = el("span", { class: "tb-saving muted small" });
  const menus = el("nav", { class: "tb-menus" }, Object.keys(MENUS).map((m) =>
    el("button", { class: "tb-menu", type: "button", onclick: (e) => openMenu(e.currentTarget, MENUS[m]()) }, m)));
  const undoBtn = el("button", { class: "icon-btn", type: "button", title: "Undo (Ctrl+Z)", onclick: () => run("undo") }, icon("undo"));
  const redoBtn = el("button", { class: "icon-btn", type: "button", title: "Redo (Ctrl+Shift+Z)", onclick: () => run("redo") }, icon("redo"));
  const exportBtn = el("button", { class: "btn", type: "button", title: "Export (Ctrl+M)", onclick: () => run("export") }, icon("file_export"), "Export");
  // Monarc Calls (reworked 2026-10-03): opens Airtable and the notes window side by side; shows the session's state
  const recLabel = el("span", {}, "Calls");
  const recBtn = el("button", { class: "btn quiet tb-rec", type: "button", title: "Monarc Calls: Airtable beside live key notes",
    onclick: () => api.post("/api/session/window").catch(() => window.open("calls.html", "_blank")) }, el("span", { class: "tb-rec-dot" }), recLabel);
  const syncRec = () => {
    const s = S.bin && S.bin.session;
    recBtn.classList.toggle("is-rec", !!(s && s.listening));
    recLabel.textContent = !s || !s.active ? "Calls" : `${s.listening ? "Listening" : "Paused"} · ${s.calls} call${s.calls === 1 ? "" : "s"}`;
  };
  const queue = el("span", { class: "tb-queue muted small" });
  // Studio was updated while this window was open: one click loads the new version (the short is saved first)
  const update = el("button", { class: "chip small tb-update", type: "button", hidden: true, title: "Studio was updated. Reload to get the new version.",
    onclick: async () => { const save = await import("./save.js"); await save.flush(); location.reload(); } }, icon("refresh"), "Update ready · Reload");
  host.append(
    el("div", { class: "tb-left" }, el("div", { class: "mark" }, "S"),
      el("div", { class: "tb-titles" }, el("div", { class: "tb-row" }, name, status, saving), menus)),
    el("div", { class: "tb-right" }, update, queue, undoBtn, redoBtn, recBtn, exportBtn));
  subscribe("update", () => { update.hidden = !S.updateReady; });
  subscribe("bin", syncRec);
  const sync = () => {
    name.textContent = S.doc ? S.doc.name : "Monarc Studio";
    name.disabled = !S.doc;
    status.hidden = !S.doc;
    if (S.doc) { status.textContent = S.doc.status === "done" ? "Done" : "Draft"; status.className = "chip-status " + (S.doc.status || "draft"); }
    undoBtn.disabled = !history.undoLabel();
    redoBtn.disabled = !history.redoLabel();
    undoBtn.title = history.undoLabel() ? `Undo ${history.undoLabel()} (Ctrl+Z)` : "Undo (Ctrl+Z)";
    redoBtn.title = history.redoLabel() ? `Redo ${history.redoLabel()} (Ctrl+Shift+Z)` : "Redo (Ctrl+Shift+Z)";
    exportBtn.disabled = !S.doc;
    document.title = S.doc ? `${S.doc.name} · Monarc Studio` : "Monarc Studio";
  };
  const syncSave = () => {
    saving.textContent = !S.doc ? "" : { saving: "Saving…", saved: "Saved", error: "Not saved", offline: "Offline: can't reach the Studio server" }[S.saving] || "";
    saving.classList.toggle("bad", S.saving === "error" || S.saving === "offline");
  };
  const syncQueue = () => {
    const jobs = (S.bin && S.bin.exports) || [];
    const running = jobs.find((j) => j.state === "running");
    const queued = jobs.filter((j) => j.state === "queued").length;
    queue.textContent = running ? `Exporting ${running.name} ${Math.round((running.progress || 0) * 100)}%${queued ? ` · ${queued} queued` : ""}` : queued ? `${queued} queued` : "";
  };
  subscribe("doc", sync); subscribe("sel", sync); subscribe("save", syncSave); subscribe("bin", syncQueue);
  sync(); syncSave();
}

export function mountTools(host) {
  clear(host);
  const btns = TOOLS.map(([id, label, key, ic]) => el("button", { class: "tool", type: "button", title: `${label} (${key})`, dataset: { tool: id },
    onclick: () => run("tool." + id) }, icon(ic)));
  host.append(...btns);
  const sync = () => btns.forEach((b) => b.classList.toggle("is-on", b.dataset.tool === S.tool));
  subscribe("tool", sync);
  sync();
}
