// A section that folds away (Jonathan, 2026-10-02: "recent changes should be a collapsible log", the keyword and page
// attribution tables too). Closed until clicked; whether it is open is remembered for the session, so a redraw after an
// edit keeps it the way it was left.
import { el } from "../util.js";

const openFolds = new Set();

export function fold({ key, label, title, count, body }) {
  const d = el("details", { class: "fold", open: openFolds.has(key) ? true : null },
    el("summary", {},
      el("div", { class: "grow" }, label ? el("div", { class: "label" }, label) : null, el("h2", {}, title)),
      count !== undefined && count !== null ? el("span", { class: "tag faint" }, String(count)) : null,
      el("span", { class: "fold-chev", "aria-hidden": "true" })),
    el("div", { class: "fold-body stack" }, ...[].concat(body).filter(Boolean)));
  d.addEventListener("toggle", () => { if (d.open) openFolds.add(key); else openFolds.delete(key); });
  return d;
}
