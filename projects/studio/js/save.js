// Autosave (G26): about 700 ms after an edit (2 s at most), the short goes to the server with the revision it was
// based on; a stale revision gets a 409 and a reload prompt. Captions are rebuilt just before each save, stamped
// with the revision the server is about to give the file, so the exporter can tell they are current.
import { S, emit, subscribe } from "./store.js";
import { api } from "./api.js";
import { toast } from "./components/modal.js";

let timer = null, first = 0, inflight = null, lastJson = null, rebuild = () => {};

export function setCaptionBuilder(fn) { rebuild = fn; }

function schedule() {
  if (!S.doc) return;
  const now = Date.now();
  if (!timer) first = now;
  clearTimeout(timer);
  const wait = Math.max(0, Math.min(700, 2000 - (now - first)));
  timer = setTimeout(() => { timer = null; flush(); }, wait);
  if (S.saving !== "saving") { S.saving = "saving"; emit("save"); }
}

export async function flush(force = false) {
  clearTimeout(timer); timer = null;
  if (inflight) { await inflight.catch(() => {}); }
  if (!S.doc) return;
  const doc = S.doc;
  rebuild(doc);
  doc.captions.evRev = (S.baseRev || 0) + 1;
  const json = JSON.stringify(doc);
  if (json === lastJson && !force) { S.saving = "saved"; emit("save"); return; }
  S.saving = "saving"; emit("save");
  inflight = api.saveProject(doc.id, doc, S.baseRev);
  try {
    const r = await inflight;
    if (S.doc && S.doc.id === doc.id) { S.baseRev = r.rev; S.doc.rev = r.rev; }
    lastJson = JSON.stringify(Object.assign({}, doc, { rev: r.rev }));
    S.saving = "saved";
  } catch (e) {
    S.saving = "error";
    if (e.status === 409) toast("This short changed in another window. Reload the page to get the newest copy.", true);
    else toast("Couldn't save: " + e.message, true);
  } finally {
    inflight = null;
    emit("save");
  }
}

let closingSent = false;
function saveOnClose() {
  if (closingSent || !S.doc || (!timer && S.saving === "saved")) return;
  closingSent = true;
  clearTimeout(timer); timer = null;
  try {
    rebuild(S.doc);
    S.doc.captions.evRev = (S.baseRev || 0) + 1;
    fetch("/api/projects/" + encodeURIComponent(S.doc.id), { method: "PUT", keepalive: true,
      headers: { "Content-Type": "application/json" }, body: JSON.stringify({ doc: S.doc, baseRev: S.baseRev }) });
  } catch (e) { /* closing anyway */ }
}

export function initSave() {
  subscribe("doc", () => { if (S.doc) schedule(); });
  // closing the window with an edit still waiting: send it now (keepalive outlives the page)
  window.addEventListener("beforeunload", saveOnClose);
  window.addEventListener("pagehide", saveOnClose);
}

export function pending() { return !!timer || !!inflight; }
