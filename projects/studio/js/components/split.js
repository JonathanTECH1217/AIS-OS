// Draggable dividers between the panels (G41). Sizes live in CSS variables on the app element and in
// localStorage["studio.layout.v1"]; Reset layout puts the defaults back. binBrowse is the Media panel's width while a
// recording's calls are open (2026-10-01, B13); the same divider drags it then, and the CSS caps it so the viewer
// keeps 260 px.
const KEY = "studio.layout.v1";
export const DEFAULTS = { bin: 300, side: 340, tl: 320, binBrowse: 800 };
const LIMITS = { bin: [200, 560], side: [260, 600], tl: [180, 700], binBrowse: [480, 1400] };

let app = null, sizes = { ...DEFAULTS }, onChange = () => {};

function load() {
  try { return Object.assign({ ...DEFAULTS }, JSON.parse(localStorage.getItem(KEY) || "{}")); } catch (e) { return { ...DEFAULTS }; }
}
function save() { try { localStorage.setItem(KEY, JSON.stringify(sizes)); } catch (e) { /* private mode */ } }
function apply() {
  for (const [k, v] of Object.entries(sizes)) app.style.setProperty("--" + k, v + "px");
  onChange();
}

export function initLayout(appEl, changed) {
  app = appEl;
  onChange = changed || onChange;
  sizes = load();
  apply();
}

export function resetLayout() { sizes = { ...DEFAULTS }; save(); apply(); }
export function layoutSizes() { return { ...sizes }; }

// handle: the divider element; name: bin | side | tl | binBrowse, or a function giving the name when a drag starts;
// axis: x or y; sign: +1 if dragging right/down grows it
export function bindDivider(handle, nameOf, axis, sign) {
  const pick = () => (typeof nameOf === "function" ? nameOf() : nameOf);
  handle.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    try { handle.setPointerCapture(e.pointerId); } catch (err) { /* synthetic */ }
    const name = pick();
    const start = axis === "x" ? e.clientX : e.clientY;
    // what the screen shows can be less than the saved size (the CSS cap): start the drag from what's shown
    const shown = name === "binBrowse" ? Math.round(document.getElementById("bin").getBoundingClientRect().width) : null;
    const base = shown || sizes[name];
    handle.classList.add("is-drag");
    const move = (ev) => {
      const d = (axis === "x" ? ev.clientX : ev.clientY) - start;
      const [lo, hi] = LIMITS[name];
      sizes[name] = Math.round(Math.max(lo, Math.min(hi, base + sign * d)));
      apply();
    };
    const up = () => {
      handle.classList.remove("is-drag");
      handle.removeEventListener("pointermove", move);
      handle.removeEventListener("pointerup", up);
      handle.removeEventListener("pointercancel", up);
      save();
    };
    handle.addEventListener("pointermove", move);
    handle.addEventListener("pointerup", up);
    handle.addEventListener("pointercancel", up);
  });
  handle.addEventListener("dblclick", () => { const name = pick(); sizes[name] = DEFAULTS[name]; save(); apply(); });
}

export function setSize(name, v) { sizes[name] = v; save(); apply(); }
