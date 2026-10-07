// M3 tabs under a page head (2026-10-03, Pipeline's Board and Funnels): text tabs, the underline on the open one.
// Each tab is a link, so the view has its own hash and the rail item stays lit (router HIGHLIGHT reads the first part).
import { el } from "../util.js";

export function tabs(items, active, label) {
  return el("nav", { class: "tabs", role: "tablist", "aria-label": label || "Views" }, ...items.map((t) =>
    el("a", { class: "tab" + (t.key === active ? " is-on" : ""), href: t.href, role: "tab", "aria-selected": String(t.key === active) }, t.label)));
}

export const PIPELINE_TABS = [
  { key: "board", label: "Board", href: "#/pipeline" },
  { key: "funnels", label: "Funnels", href: "#/pipeline/funnels" },
];
