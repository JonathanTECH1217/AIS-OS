// Small DOM and formatting helpers. No framework.

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else if (k === "dataset") Object.assign(node.dataset, v);
    else if (v === true) node.setAttribute(k, "");
    else node.setAttribute(k, v);
  }
  append(node, children);
  return node;
}

export function append(node, children) {
  for (const c of children.flat(Infinity)) {
    if (c === null || c === undefined || c === false) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return node;
}

export function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); return node; }

export function money(n, opts = {}) {
  const v = Number(n || 0);
  return "$" + v.toLocaleString("en-US", { maximumFractionDigits: 0 }) + (opts.mo ? "/mo" : "");
}

export function fmtDate(iso) {
  if (!iso) return "";
  const d = /^\d{4}-\d{2}-\d{2}$/.test(iso) ? new Date(iso + "T12:00:00") : new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function fmtDateTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit", timeZone: "America/New_York" }) + " ET";
}

export function addDays(iso, n) {
  const d = new Date(iso + "T12:00:00");
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

export function nextWeekday(iso, n) {
  let d = iso, left = n;
  while (left > 0) {
    d = addDays(d, 1);
    const wd = new Date(d + "T12:00:00").getDay();
    if (wd !== 0 && wd !== 6) left -= 1;
  }
  return d;
}

export function digits(phone) { return (phone || "").replace(/\D/g, "").slice(-10); }

export function telHref(phone) { const d = digits(phone); return d.length === 10 ? `tel:+1${d}` : `tel:${phone}`; }

export function pct(a, b) { return b ? Math.round((a / b) * 100) : 0; }

export function delta(cur, prev, { invert = false, suffix = "" } = {}) {
  // Motion: muted sage up, muted brick down, always with a glyph and a word.
  if (prev === undefined || prev === null) return el("span", { class: "delta muted" }, "first week");
  const diff = cur - prev;
  if (diff === 0) return el("span", { class: "delta muted" }, "same as last week");
  const good = invert ? diff < 0 : diff > 0;
  const glyph = diff > 0 ? "↑" : "↓";
  return el("span", { class: "delta " + (good ? "up" : "down") }, `${glyph} ${Math.abs(diff)}${suffix} vs last week`);
}

export function copyText(text) {
  return navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject(new Error("no clipboard"));
}

export function debounce(fn, ms = 250) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}
