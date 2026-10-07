// His notes on a Loom B and A cut (2026-10-07, Jonathan: "I will leave notes on each video for where it went wrong so the
// SOP can be adjusted"). Under the player: the notes so far, each with the second it was left at (a click jumps there), and
// a box that saves a new one at the second the video is on. Saved by the server in projects/loom-b-and-a/notes/<date>.json;
// the clone reads them in the batch workflow's notes step.
import { el } from "../util.js";
import { api } from "../api.js";
import { toast } from "./modal.js";

const mmss = (s) => (s === null || s === undefined ? "" : `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`);

export function loomNotes({ date, slug }, video) {
  const list = el("div", { class: "ln-list" }, el("div", { class: "muted", style: "font-size:12px" }, "Reading notes..."));
  const text = el("textarea", { class: "ln-text", rows: "2", placeholder: "What went wrong here? Pause the video at the moment, then write." });
  const at = el("span", { class: "num" }, "0:00");
  const save = el("button", { class: "btn small", type: "button" }, "Save note at ", at);
  const box = el("div", { class: "loom-notes", onclick: (e) => e.stopPropagation(), onkeydown: (e) => e.stopPropagation() },
    el("div", { class: "label" }, "Your notes for the SOP"), list, text, el("div", { class: "row", style: "gap:8px;align-items:center" }, save,
      el("span", { class: "muted", style: "font-size:12px" }, "Saved to the batch's notes; the next pass reads them.")));
  const tick = () => { at.textContent = mmss(video ? video.currentTime : 0); };
  if (video) { video.addEventListener("timeupdate", tick); video.addEventListener("seeked", tick); }

  function paint(notes) {
    if (!notes.length) { list.replaceChildren(el("div", { class: "muted", style: "font-size:12px" }, "No notes yet.")); return; }
    list.replaceChildren(...notes.map((n, i) => el("div", { class: "ln-note" },
      n.at !== null && n.at !== undefined
        ? el("button", { class: "tag ln-at", type: "button", title: "Jump to this second", onclick: () => { if (video) { video.currentTime = n.at; video.play(); } } }, mmss(n.at))
        : el("span", { class: "tag faint" }, "general"),
      el("span", { class: "grow" }, n.text),
      el("button", { class: "icon-btn", type: "button", title: "Take this note back", "aria-label": "Take this note back",
        onclick: async () => { try { paint((await api.post("/api/loom-ba/notes", { date, slug, remove: i })).notes); } catch (e) { toast((e.errors || [String(e)]).join(" "), true); } } },
        el("span", { class: "ms", "aria-hidden": "true" }, "close")))));
  }

  save.addEventListener("click", async () => {
    const t = text.value.trim();
    if (!t) { text.focus(); return; }
    save.disabled = true;
    try {
      const d = await api.post("/api/loom-ba/notes", { date, slug, text: t, at: video ? video.currentTime : null });
      text.value = "";
      paint(d.notes);
      toast("Note saved.");
    } catch (e) { toast((e.errors || [String(e)]).join(" "), true); }
    save.disabled = false;
  });

  api.get(`/api/loom-ba/notes?date=${encodeURIComponent(date)}&slug=${encodeURIComponent(slug)}`)
    .then((d) => paint(d.notes || [])).catch(() => paint([]));
  return box;
}
