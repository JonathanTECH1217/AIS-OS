// Test harness for Monarc Studio (G39). A test file calls test(name, async (t, st) => {...}); results go into
// <pre id="__out"> as PASS / FAIL lines and a DONE line, which tests/run.py reads. st is window.__studio.
const out = document.getElementById("__out");
const log = (line) => { out.textContent += line + "\n"; };

export const wait = (ms) => new Promise((r) => setTimeout(r, ms));
export async function until(fn, timeout = 8000, step = 50) {
  const t0 = performance.now();
  for (;;) {
    let v;
    try { v = await fn(); } catch (e) { v = null; }
    if (v) return v;
    if (performance.now() - t0 > timeout) return null;
    await wait(step);
  }
}

function makeT(st) {
  const t = { passes: 0, fails: 0 };
  t.ok = (name, cond, detail = "") => { if (cond) { t.passes += 1; log(`PASS ${name}`); } else { t.fails += 1; log(`FAIL ${name} ${detail}`); } return !!cond; };
  t.eq = (name, a, b) => t.ok(name, JSON.stringify(a) === JSON.stringify(b), `got ${JSON.stringify(a)} want ${JSON.stringify(b)}`);
  t.near = (name, a, b, tol) => t.ok(name, Math.abs(a - b) <= tol, `got ${a} want ${b} ±${tol}`);
  t.fail = (name, detail) => t.ok(name, false, detail);

  // a fresh short from the fixture's moment m01 (frames 30..210 of src20), opened in the editor. Its captions come
  // straight from the transcript (the way before 2026-10-02) unless {captions: "generate"}: a new short's default,
  // no captions until Generate captions (t-gencaptions.js)
  t.fresh = async (moment = "m01", { captions = "transcript" } = {}) => {
    const asset = st.lib.all().find((a) => a.name === "src20.mp4");
    const d = await st.api.newProject({ asset: asset.id, moment, captions });
    await st.openShort(d.id);
    await until(() => st.S.doc && st.S.doc.id === d.id);
    await until(() => st.lib.transcript(asset.id));
    st.emit("doc");
    await wait(80);
    return st.S.doc;
  };
  t.asset = (name) => st.lib.all().find((a) => a.name === name);
  t.clip = (track) => st.S.doc.clips.filter((c) => c.track === track).sort((a, b) => a.start - b.start);

  // keyboard: combo like "Ctrl+Shift+Z", "Space", "C"
  t.key = (combo, target = document.body) => {
    const parts = combo.split("+");
    const k = parts.pop();
    const map = { Space: " ", Left: "ArrowLeft", Right: "ArrowRight", Up: "ArrowUp", Down: "ArrowDown", Delete: "Delete", Backspace: "Backspace", Escape: "Escape", Home: "Home", End: "End" };
    const key = map[k] || (k.length === 1 ? (parts.includes("Shift") ? k.toUpperCase() : k.toLowerCase()) : k);
    const ev = new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true,
      ctrlKey: parts.includes("Ctrl"), shiftKey: parts.includes("Shift"), altKey: parts.includes("Alt") });
    target.dispatchEvent(ev);
  };

  // timeline pointer helpers: positions in frames and track ids
  const wrap = () => document.querySelector(".tl-wrap");
  t.tlPoint = (f, track, dy = 0) => {
    const r = wrap().getBoundingClientRect();
    return { x: r.left + st.tl.xOf(f), y: r.top + (track === "ruler" ? 10 : st.tl.yOfTrack(track)) + dy };
  };
  const pe = (type, p, opts = {}) => new PointerEvent(type, { bubbles: true, cancelable: true, clientX: p.x, clientY: p.y, button: 0,
    buttons: type === "pointerup" ? 0 : 1, pointerId: 1, pointerType: "mouse", isPrimary: true, detail: opts.detail || 1,
    shiftKey: !!opts.shift, ctrlKey: !!opts.ctrl, altKey: !!opts.alt });
  t.tlClick = async (f, track, opts = {}) => {
    const p = t.tlPoint(f, track, opts.dy || 0);
    wrap().dispatchEvent(pe("pointerdown", p, opts));
    wrap().dispatchEvent(pe("pointerup", p, opts));
    await wait(30);
  };
  t.tlDrag = async (from, to, opts = {}) => {
    const a = t.tlPoint(from.f, from.track, from.dy || 0), b = t.tlPoint(to.f, to.track, to.dy || 0);
    wrap().dispatchEvent(pe("pointerdown", a, opts));
    const n = 6;
    for (let i = 1; i <= n; i += 1) {
      wrap().dispatchEvent(pe("pointermove", { x: a.x + ((b.x - a.x) * i) / n, y: a.y + ((b.y - a.y) * i) / n }, opts));
      await wait(10);
    }
    wrap().dispatchEvent(pe("pointerup", b, opts));
    await wait(40);
  };
  t.tlContext = async (f, track, dy = 0) => {
    const p = t.tlPoint(f, track, dy);
    wrap().dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, cancelable: true, clientX: p.x, clientY: p.y }));
    await wait(40);
    return [...document.querySelectorAll(".menu .menu-label")].map((x) => x.textContent);
  };
  // close menus the way a person does (Esc), so the menu module knows it's closed
  t.closeMenus = () => document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  t.pe = pe;

  // which frame of src20 the monitor shows: decode the 12-bit barcode in the top band of the program canvas
  t.frameShown = () => {
    const cv = document.querySelector(".mon-program");
    const g = cv.getContext("2d");
    const k = cv.width / 1080;
    let n = 0;
    for (let i = 0; i < 12; i += 1) {
      const px = g.getImageData(Math.round((45 + 90 * i) * k), Math.round(40 * k), 1, 1).data;
      if ((px[0] + px[1] + px[2]) / 3 > 128) n |= 1 << i;
    }
    return n;
  };
  t.pixel = (x, y) => { const cv = document.querySelector(".mon-program"); const k = cv.width / 1080; return [...cv.getContext("2d").getImageData(Math.round(x * k), Math.round(y * k), 1, 1).data]; };
  // draw, wait until every video element has loaded and finished seeking, draw again
  t.settle = async () => {
    st.mon.draw();
    await wait(40);
    await until(() => { const p = st.mon.pool(); return p && p.items.every((i) => !i.seeking && (i.v.readyState >= 2 || i.used < p.stamp)); }, 6000);
    st.mon.draw();
    await wait(40);
    await until(() => { const p = st.mon.pool(); return p && p.items.every((i) => !i.seeking); }, 3000);
    st.mon.draw();
    await wait(20);
  };
  return t;
}

// Monarc Calls (calls.html?test=<name>): ca is window.__calls once the check lines are in
export async function testCalls(name, fn) {
  const ca = await until(() => window.__calls && window.__calls.ready && window.__calls.C.check && window.__calls, 15000);
  if (!ca) { log(`FAIL ${name} Monarc Calls never became ready`); log(`DONE ${name} pass=0 fail=1`); return; }
  const t = makeT(ca);
  window.addEventListener("error", (e) => t.fail("uncaught error", e.message));
  try { await fn(t, ca); } catch (e) { t.fail("exception", (e && (e.stack || e.message)) || String(e)); }
  log(`DONE ${name} pass=${t.passes} fail=${t.fails}`);
}

export async function test(name, fn) {
  const st = await until(() => window.__studio && window.__studio.ready && window.__studio.S.bin && window.__studio.lib.all().length && window.__studio, 15000);
  if (!st) { log(`FAIL ${name} studio never became ready`); log(`DONE ${name} pass=0 fail=1`); return; }
  const t = makeT(st);
  window.addEventListener("error", (e) => t.fail("uncaught error", e.message));
  try { await fn(t, st); } catch (e) { t.fail("exception", (e && (e.stack || e.message)) || String(e)); }
  log(`DONE ${name} pass=${t.passes} fail=${t.fails}`);
}
