// Monarc Studio (2026-09-29): boot. Lays out the panels, wires the modules, reopens the last short, and runs a
// test when the page is loaded with ?test=<name> (projects/studio/tests/run.py).
import { S, emit, subscribe } from "./js/store.js";
import { el } from "./js/util.js";
import { initLayout, bindDivider } from "./js/components/split.js";
import { mountTopbar, mountTools } from "./js/topbar.js";
import { mountBin } from "./js/panels/bin.js";
import { mountMonitor } from "./js/panels/monitor.js";
import { mountEffects } from "./js/panels/effects.js";
import { mountCaptions } from "./js/panels/captions.js";
import { mountTimeline, timelineApi, zoomBy } from "./js/timeline/timeline.js";
import { setTimeline, openShort } from "./js/actions.js";
import { initKeys } from "./js/keys.js";
import { initSave, setCaptionBuilder } from "./js/save.js";
import { lib, startBinFeed } from "./js/media/library.js";
import { loadFontMetrics } from "./js/fontmetrics.js";
import { buildCaptionEvents } from "./js/model/captions.js";
import { measureCaption } from "./js/compositor.js";
import { installHook } from "./js/test-hook.js";

let fontsReady = false;

export function rebuildCaptions(doc = S.doc) {
  if (!doc || !fontsReady) return;
  const ev = buildCaptionEvents(doc, lib, measureCaption(doc.captions.size));
  if (ev) doc.captions.events = ev;       // null: a transcript is still loading, keep what the short has
}

function sideTabs(host) {
  const fx = el("div", { class: "tab-body", id: "fx" });
  const cap = el("div", { class: "tab-body", id: "cap", hidden: true });
  const tabs = [["Effect Controls", fx], ["Captions", cap]];
  const btns = tabs.map(([label, body], i) => el("button", { class: "tab" + (i === 0 ? " is-on" : ""), type: "button", role: "tab",
    onclick: () => show(i) }, label));
  function show(i) { btns.forEach((b, j) => b.classList.toggle("is-on", i === j)); tabs.forEach(([, b], j) => { b.hidden = i !== j; }); localStorage.setItem("studio.tab", String(i)); }
  host.append(el("div", { class: "tabs", role: "tablist" }, btns), fx, cap);
  subscribe("focusText", () => show(0));
  subscribe("focusCaptions", () => show(1));
  show(+(localStorage.getItem("studio.tab") || 0));
  return { fx, cap };
}

async function boot() {
  const app = document.getElementById("app");
  initLayout(app, () => window.dispatchEvent(new Event("resize")));
  bindDivider(document.getElementById("div-bin"), () => (app.classList.contains("browsing") ? "binBrowse" : "bin"), "x", 1);
  bindDivider(document.getElementById("div-side"), "side", "x", -1);
  bindDivider(document.getElementById("div-tl"), "tl", "y", -1);

  // captions are derived from the doc: rebuild before any view draws the change
  subscribe("doc", () => rebuildCaptions());
  subscribe("transcript", () => { rebuildCaptions(); emit("view"); });
  setCaptionBuilder(rebuildCaptions);

  mountTopbar(document.getElementById("topbar"));
  mountTools(document.getElementById("tools"));
  mountBin(document.getElementById("bin"));
  mountMonitor(document.getElementById("monitor"));
  const { fx, cap } = sideTabs(document.getElementById("side"));
  mountEffects(fx);
  mountCaptions(cap);
  mountTimeline(document.getElementById("timeline"));
  setTimeline({ ...timelineApi(), zoomBy });
  initKeys();
  initSave();

  try {
    await loadFontMetrics("fonts/Montserrat-Black.ttf");
    await document.fonts.load('88px "Montserrat Black"');
  } catch (e) { console.warn("caption font", e); }
  fontsReady = true;
  rebuildCaptions();
  emit("view");

  const params = new URLSearchParams(location.search);
  S.test = !!params.get("test");
  installHook();
  startBinFeed();
  const m = /short=([^&]+)/.exec(location.hash);
  if (m && !S.test) openShort(decodeURIComponent(m[1])).catch(() => {});
  if (params.get("test")) {
    const name = params.get("test");
    try { await import(`./tests/t-${name}.js`); }
    catch (e) { const out = document.getElementById("__out"); out.textContent += `FAIL load ${name}: ${e.message}\nDONE\n`; }
  }
}

boot();
