// Popup with the ad page treatment: Charcoal Blue ground at 55 percent, Paper panel, round close.
import { el } from "../util.js";

export function openModal(content, { wide = false } = {}) {
  const root = document.getElementById("modal-root");
  const dialog = el("div", { class: "dialog" + (wide ? " wide" : ""), role: "dialog", "aria-modal": "true" });
  const closeBtn = el("button", { class: "close", type: "button", "aria-label": "Close" }, "×");
  const overlay = el("div", { class: "modal" }, dialog);
  dialog.append(closeBtn, content);
  function close() {
    overlay.remove();
    document.body.classList.remove("modal-open");
    document.removeEventListener("keydown", onKey);
  }
  function onKey(e) { if (e.key === "Escape") close(); }
  closeBtn.addEventListener("click", close);
  overlay.addEventListener("mousedown", (e) => { if (e.target === overlay) close(); });
  document.addEventListener("keydown", onKey);
  root.append(overlay);
  document.body.classList.add("modal-open");
  const first = dialog.querySelector("input,select,textarea,button:not(.close)");
  if (first) first.focus();
  return { close, dialog };
}

let toastTimer;
export function toast(msg, bad = false) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = "toast" + (bad ? " bad" : "");
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, bad ? 6000 : 2800);
}
