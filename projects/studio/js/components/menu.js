// Menus: the top-bar menus and every right-click menu. Items: {label, keys, run, disabled, checked, sub, sep}.
import { el } from "../util.js";

let open = null;

export function closeMenu() {
  if (open) { open.remove(); open = null; document.removeEventListener("mousedown", outside, true); document.removeEventListener("keydown", esc, true); }
}
function outside(e) { if (open && !open.contains(e.target)) closeMenu(); }
function esc(e) { if (e.key === "Escape") { e.stopPropagation(); closeMenu(); } }

function build(items, depth = 0) {
  const m = el("div", { class: "menu", role: "menu" });
  for (const it of items) {
    if (!it) continue;
    if (it.sep) { m.append(el("div", { class: "menu-sep" })); continue; }
    const dis = typeof it.disabled === "function" ? it.disabled() : it.disabled;
    const chk = typeof it.checked === "function" ? it.checked() : it.checked;
    const label = typeof it.label === "function" ? it.label() : it.label;
    const row = el("button", { class: "menu-item" + (dis ? " is-disabled" : ""), type: "button", role: "menuitem", disabled: dis || null },
      el("span", { class: "menu-check" }, chk ? "✓" : ""),
      el("span", { class: "menu-label" }, label),
      el("span", { class: "menu-keys" }, it.sub ? "▸" : (it.keys || "")));
    if (it.sub) {
      row.addEventListener("mouseenter", () => {
        m.querySelectorAll(".menu.sub").forEach((s) => s.remove());
        const sub = build(it.sub, depth + 1);
        sub.classList.add("sub");
        m.append(sub);
        const r = row.getBoundingClientRect(), mr = m.getBoundingClientRect();
        sub.style.left = (r.right - mr.left - 4) + "px";
        sub.style.top = (r.top - mr.top - 6) + "px";
        // near the right or bottom edge (the Captions tab is the rightmost column): open to the left, and move up
        const sr = sub.getBoundingClientRect();
        if (sr.right > window.innerWidth - 8) sub.style.left = (r.left - mr.left - sr.width + 4) + "px";
        if (sr.bottom > window.innerHeight - 8) sub.style.top = (r.top - mr.top - 6 - (sr.bottom - window.innerHeight + 8)) + "px";
      });
    } else {
      row.addEventListener("mouseenter", () => m.querySelectorAll(".menu.sub").forEach((s) => s.remove()));
      row.addEventListener("click", (e) => { e.stopPropagation(); if (dis) return; closeMenu(); if (it.run) it.run(); });
    }
    m.append(row);
  }
  return m;
}

// at: an element (menu opens below it) or {x, y}
export function openMenu(at, items) {
  closeMenu();
  const m = build(items);
  document.body.append(m);
  let x, y;
  if (at instanceof Element) { const r = at.getBoundingClientRect(); x = r.left; y = r.bottom + 2; }
  else { x = at.x; y = at.y; }
  const r = m.getBoundingClientRect();
  x = Math.min(x, window.innerWidth - r.width - 8);
  y = Math.min(y, window.innerHeight - r.height - 8);
  m.style.left = Math.max(4, x) + "px";
  m.style.top = Math.max(4, y) + "px";
  open = m;
  setTimeout(() => { document.addEventListener("mousedown", outside, true); document.addEventListener("keydown", esc, true); }, 0);
  return m;
}

export function menuOpen() { return !!open; }
