// A Premiere-style number: drag it left/right to change the value, click to type. onChange(value, final).
import { el } from "../util.js";

export function numField({ value, step = 1, min = -Infinity, max = Infinity, digits = 1, suffix = "", onChange, title = "" }) {
  const span = el("span", { class: "num-field", tabindex: "0", title });
  let v = value, dragging = false, moved = false, startX = 0, startV = 0;
  const show = () => { span.textContent = (Math.round(v * 10 ** digits) / 10 ** digits).toFixed(digits) + suffix; };
  const set = (nv, final) => {
    nv = Math.max(min, Math.min(max, nv));
    if (nv === v && !final) return;
    v = nv; show(); onChange && onChange(v, final);
  };
  span.addEventListener("pointerdown", (e) => {
    if (span.querySelector("input")) return;
    dragging = true; moved = false; startX = e.clientX; startV = v;
    span.classList.add("is-drag");
    try { span.setPointerCapture(e.pointerId); } catch (err) { /* synthetic */ }
  });
  span.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const dx = e.clientX - startX;
    if (Math.abs(dx) > 2) moved = true;
    if (moved) set(startV + Math.round(dx) * step * (e.shiftKey ? 10 : 1), false);
  });
  span.addEventListener("pointerup", () => {
    if (!dragging) return;
    dragging = false;
    span.classList.remove("is-drag");
    if (moved) { onChange && onChange(v, true); return; }
    const inp = el("input", { class: "num-input", value: String(Math.round(v * 10 ** digits) / 10 ** digits) });
    span.textContent = "";
    span.append(inp);
    inp.focus(); inp.select();
    let finished = false;
    const done = (commit) => {
      if (finished) return;        // Enter removes the input, which fires blur: finish once
      finished = true;
      const nv = parseFloat(inp.value);
      inp.remove();
      if (commit && !Number.isNaN(nv)) set(nv, true); else show();
    };
    inp.addEventListener("keydown", (e) => { if (e.key === "Enter") done(true); if (e.key === "Escape") done(false); e.stopPropagation(); });
    inp.addEventListener("blur", () => done(true));
  });
  span.addEventListener("keydown", (e) => {
    if (e.key === "ArrowUp" || e.key === "ArrowRight") { set(v + step * (e.shiftKey ? 10 : 1), true); e.preventDefault(); e.stopPropagation(); }
    if (e.key === "ArrowDown" || e.key === "ArrowLeft") { set(v - step * (e.shiftKey ? 10 : 1), true); e.preventDefault(); e.stopPropagation(); }
  });
  show();
  span.update = (nv) => { if (!dragging && !span.querySelector("input")) { v = nv; show(); } };
  return span;
}
