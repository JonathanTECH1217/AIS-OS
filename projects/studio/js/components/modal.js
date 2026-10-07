// M3 dialog on a scrim (the CRM's), plus the snackbar.
import { el } from "../util.js";

export function openModal(content, { wide = false, onClose } = {}) {
  const root = document.getElementById("modal-root");
  const dialog = el("div", { class: "dialog" + (wide ? " wide" : ""), role: "dialog", "aria-modal": "true" });
  const closeBtn = el("button", { class: "close", type: "button", "aria-label": "Close" }, "×");
  const overlay = el("div", { class: "modal" }, dialog);
  dialog.append(closeBtn, content);
  function close() {
    overlay.remove();
    if (!root.children.length) document.body.classList.remove("modal-open");
    document.removeEventListener("keydown", onKey, true);
    if (onClose) onClose();
  }
  function onKey(e) { if (e.key === "Escape") { e.stopPropagation(); close(); } }
  closeBtn.addEventListener("click", close);
  overlay.addEventListener("mousedown", (e) => { if (e.target === overlay) close(); });
  document.addEventListener("keydown", onKey, true);
  root.append(overlay);
  document.body.classList.add("modal-open");
  const first = dialog.querySelector("input,select,textarea,button:not(.close)");
  if (first) setTimeout(() => first.focus(), 0);
  return { close, dialog };
}

export function confirmDialog(title, body, okLabel = "OK") {
  return new Promise((resolve) => {
    let done = false;
    const ok = el("button", { class: "btn", type: "button" }, okLabel);
    const cancel = el("button", { class: "btn quiet", type: "button" }, "Cancel");
    const m = openModal(el("div", { class: "stack" }, el("h2", {}, title), el("div", { class: "body" }, body),
      el("div", { class: "actions" }, cancel, ok)), { onClose: () => { if (!done) resolve(false); } });
    ok.onclick = () => { done = true; m.close(); resolve(true); };
    cancel.onclick = () => { done = true; m.close(); resolve(false); };
  });
}

export function promptDialog(title, value = "", label = "") {
  return new Promise((resolve) => {
    let done = false;
    const input = el("input", { value, type: "text" });
    const ok = el("button", { class: "btn", type: "button" }, "OK");
    const cancel = el("button", { class: "btn quiet", type: "button" }, "Cancel");
    const m = openModal(el("div", { class: "stack" }, el("h2", {}, title),
      el("div", { class: "field" }, label ? el("label", {}, label) : null, input),
      el("div", { class: "actions" }, cancel, ok)), { onClose: () => { if (!done) resolve(null); } });
    const go = () => { done = true; m.close(); resolve(input.value); };
    ok.onclick = go;
    input.onkeydown = (e) => { if (e.key === "Enter") go(); };
    cancel.onclick = () => { done = true; m.close(); resolve(null); };
    setTimeout(() => { input.focus(); input.select(); }, 0);
  });
}

let toastTimer;
export function toast(msg, bad = false) {
  const t = document.getElementById("toast");
  if (!t) return;
  t.textContent = msg;
  t.className = "toast" + (bad ? " bad" : "");
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, bad ? 6000 : 2800);
}
