// The timeline (G13, G28, G31-G33): track headers in HTML, clips on a canvas, playhead and drag feedback on a
// second canvas. x = (f - scrollF) * ppf. Tools follow Premiere: V select, C razor, H hand, Z zoom, B ripple,
// N rolling, Y slip, U slide, P pen, T text. Every drag recomputes from the pre-drag copy (history.dragTo).
import { S, emit, subscribe, selectOnly } from "../store.js";
import { el, clear, icon, cssVar, clamp } from "../util.js";
import { clipById, clipEnd, clipLen, clipsOn, FPS, fmtLen, fmtTC, seqEnd, withLinked, isVisual, trackOf } from "../model/doc.js";
import * as ops from "../model/ops.js";
import * as kf from "../model/keyframes.js";
import { colorsFor, genStatus, wordsOnTimeline } from "../model/captions.js";
import { gateFrames, isVoiceClip, plays } from "../model/voices.js";
import * as history from "../history.js";
import { lib } from "../media/library.js";
import { pb } from "../playback.js";
import { openMenu } from "../components/menu.js";
import { toast } from "../components/modal.js";
import { run as runAction } from "../actions.js";

const RULER = 26;
const HEIGHTS = { caption: 30, video: 60, audio: 60 };
const EXPANDED = 120;
const EDGE = 7;
const SNAP_PX = 8;
const LIMIT_90 = 90 * FPS;

export const view = { ppf: 3, scrollF: 0, scrollY: 0, expanded: new Set(JSON.parse(localStorage.getItem("studio.tl.expanded") || "[]")) };
const ADD_ROW = 44;       // the "+ Video / + Audio" row under the last track scrolls with the tracks
let root, headers, wrap, base, over, bctx, octx, hscroll, vscroll, lenEl;
let rows = [];
let snapLine = null, marquee = null, hover = null, dropGhost = null;
let W = 0, H = 0, dpr = 1;
const ctxOps = () => ({ lib });

// ------------------------------------------------------------------ geometry

export function xOf(f) { return (f - view.scrollF) * view.ppf; }
export function fOfX(x) { return x / view.ppf + view.scrollF; }

function layout() {
  rows = [];
  if (!S.doc) return;
  let y = RULER - view.scrollY;
  for (const t of S.doc.tracks) {
    const h = view.expanded.has(t.id) && t.kind !== "caption" ? EXPANDED : HEIGHTS[t.kind];
    rows.push({ id: t.id, kind: t.kind, y, h, track: t });
    y += h;
  }
}
function rowAt(y) { return rows.find((r) => y >= r.y && y < r.y + r.h) || null; }
function rowOf(id) { return rows.find((r) => r.id === id); }
export function yOfTrack(id) { const r = rowOf(id); return r ? r.y + r.h / 2 : 0; }
function contentHeight() { return rows.length ? rows[rows.length - 1].y + rows[rows.length - 1].h + view.scrollY - RULER : 0; }

// ------------------------------------------------------------------ mount

export function mountTimeline(host) {
  root = host;
  clear(root);
  lenEl = el("span", { class: "tl-len num" });
  const head = el("div", { class: "tl-top" },
    el("span", { class: "tl-title" }, "Timeline"), lenEl,
    el("span", { class: "grow" }),
    el("button", { class: "icon-btn", title: "Snap (S)", id: "tl-snap", onclick: () => runAction("snap") }, icon("vertical_align_center")),
    el("button", { class: "icon-btn", title: "Zoom out (-)", onclick: () => zoomBy(1 / 1.5) }, icon("zoom_out")),
    el("input", { type: "range", min: "0", max: "100", value: "50", class: "tl-zoom", id: "tl-zoom", title: "Zoom",
      oninput: (e) => setZoomSlider(+e.target.value) }),
    el("button", { class: "icon-btn", title: "Zoom in (=)", onclick: () => zoomBy(1.5) }, icon("zoom_in")),
    el("button", { class: "icon-btn", title: "Fit (\\)", onclick: () => zoomFit() }, icon("fit_screen")));
  headers = el("div", { class: "tl-heads" });
  base = el("canvas", { class: "tl-base" });
  over = el("canvas", { class: "tl-over" });
  hscroll = el("div", { class: "tl-hscroll" }, el("div", { class: "tl-hscroll-inner" }));
  vscroll = el("div", { class: "tl-vscroll", title: "Scroll the tracks" }, el("div", { class: "tl-vscroll-inner" }));
  wrap = el("div", { class: "tl-wrap", tabindex: "0" }, base, over);
  root.append(head, el("div", { class: "tl-body" }, headers, wrap, vscroll), hscroll);
  bctx = base.getContext("2d");
  octx = over.getContext("2d");
  new ResizeObserver(() => resize()).observe(wrap);
  hscroll.addEventListener("scroll", () => {
    const f = hscroll.scrollLeft / view.ppf;
    if (Math.abs(f - view.scrollF) > 0.5) { view.scrollF = f; redraw(); }
  });
  vscroll.addEventListener("scroll", () => { if (Math.abs(vscroll.scrollTop - view.scrollY) > 0.5) scrollTracksTo(vscroll.scrollTop); });
  wrap.addEventListener("wheel", onWheel, { passive: false });
  // over the track names a swipe or wheel moves the tracks up and down (nothing to zoom or scrub there)
  headers.addEventListener("wheel", (e) => { e.preventDefault(); if (!e.ctrlKey) scrollTracksTo(view.scrollY + (e.deltaY || e.deltaX)); }, { passive: false });
  wrap.addEventListener("pointerdown", onDown);
  wrap.addEventListener("pointermove", onHover);
  wrap.addEventListener("pointerleave", () => { hover = null; wrap.style.cursor = ""; drawOver(); });
  wrap.addEventListener("dblclick", onDbl);
  wrap.addEventListener("contextmenu", onContext);
  wrap.addEventListener("dragover", onDragOver);
  wrap.addEventListener("dragleave", () => { dropGhost = null; drawOver(); });
  wrap.addEventListener("drop", onDrop);
  subscribe("doc", () => { renderHeaders(); redraw(); });
  subscribe("sel", redraw);
  subscribe("tool", () => { wrap.dataset.tool = S.tool; });
  subscribe("playhead", () => { if (S.playing) follow(); drawOver(); });
  subscribe("view", () => { renderHeaders(); redraw(); });
  subscribe("transcript", redraw);
  subscribe("gencaps", () => { renderHeaders(); redraw(); });
  lib.onLoaded(() => redraw());
  renderHeaders();
  resize();
}

function resize() {
  dpr = window.devicePixelRatio || 1;
  const r = wrap.getBoundingClientRect();
  W = Math.max(10, r.width); H = Math.max(10, r.height);
  for (const c of [base, over]) {
    c.width = Math.round(W * dpr); c.height = Math.round(H * dpr);
    c.style.width = W + "px"; c.style.height = H + "px";
  }
  redraw();
}

// ------------------------------------------------------------------ headers

function renderHeaders() {
  clear(headers);
  layout();
  if (!S.doc) { headers.append(el("div", { class: "tl-empty" }, "")); return; }
  // the corner above the track names never scrolls, so "+" is always in reach
  headers.append(el("div", { class: "tl-head-ruler", style: { height: RULER + "px" } },
    el("button", { class: "tl-add-btn", type: "button", title: "Add a video or audio track", onclick: (e) => openMenu(e.currentTarget, [
      { label: "Add video track", run: () => runAction("addVideoTrack") },
      { label: "Add audio track", run: () => runAction("addAudioTrack") }]) }, icon("add"))));
  const inner = el("div", { class: "tl-heads-inner", style: { transform: `translateY(${-view.scrollY}px)` } });
  for (const r of rows) {
    const t = r.track;
    const h = el("div", { class: "tl-head kind-" + t.kind + (t.lock ? " is-locked" : ""), style: { height: r.h + "px" },
      ondblclick: () => { if (t.kind === "caption") return; view.expanded.has(t.id) ? view.expanded.delete(t.id) : view.expanded.add(t.id);
        localStorage.setItem("studio.tl.expanded", JSON.stringify([...view.expanded])); emit("view"); },
      oncontextmenu: (e) => { e.preventDefault(); trackMenu(e, t); } },
      el("span", { class: "tl-head-id" }, t.kind === "caption" ? icon("subtitles") : t.id),
      t.kind !== "caption" && t.name ? el("span", { class: "tl-head-name", title: t.voice ? `This track plays only ${t.voice === "me" ? "your" : "the other side's"} voice` : "" }, t.name) : null);
    if (t.kind === "caption") {
      const gs = genStatus(S.doc);
      h.append(el("span", { class: "tl-head-name" }, "Captions"));
      if (gs === "none" || gs === "part") h.append(tbtn("auto_awesome", gs === "none" ? "Generate captions" : "Generate captions again (some footage has none)",
        () => runAction("generateCaptions"), false, "gen"));
      h.append(tbtn(S.doc.captions.on ? "visibility" : "visibility_off", "Show captions", () =>
        history.commit("Captions on/off", (d) => { d.captions.on = !d.captions.on; }), !S.doc.captions.on));
    } else {
      if (t.kind === "video") h.append(tbtn(t.hide ? "visibility_off" : "visibility", "Show track", () => trackToggle(t.id, "hide"), t.hide));
      if (t.kind === "audio") {
        h.append(tbtn(t.mute ? "volume_off" : "volume_up", "Mute", () => trackToggle(t.id, "mute"), t.mute));
        h.append(tbtn("headphones", "Solo", () => trackToggle(t.id, "solo"), t.solo, "solo"));
      }
      h.append(tbtn(t.lock ? "lock" : "lock_open", "Lock", () => trackToggle(t.id, "lock"), t.lock));
    }
    inner.append(h);
  }
  const add = el("div", { class: "tl-add" },
    el("button", { class: "chip small", type: "button", title: "Add a video track", onclick: () => runAction("addVideoTrack") }, icon("add"), "Video"),
    el("button", { class: "chip small", type: "button", title: "Add an audio track", onclick: () => runAction("addAudioTrack") }, icon("add"), "Audio"));
  inner.append(add);
  headers.append(inner);
}

function tbtn(name, title, fn, on, extra = "") {
  return el("button", { class: "tl-tbtn " + extra + (on ? " is-on" : ""), type: "button", title, onclick: (e) => { e.stopPropagation(); fn(); } }, icon(name));
}

function trackToggle(id, key) {
  history.commit(key === "lock" ? "Lock track" : key === "mute" ? "Mute track" : key === "solo" ? "Solo track" : "Show track",
    (d) => { const t = d.tracks.find((x) => x.id === id); t[key] = !t[key]; });
}

function trackMenu(e, t) {
  openMenu({ x: e.clientX, y: e.clientY }, [
    { label: "Add video track", run: () => runAction("addVideoTrack") },
    { label: "Add audio track", run: () => runAction("addAudioTrack") },
    t.voice ? { sep: true } : null,
    t.voice ? { label: "Normalize voices", run: () => runAction("normalizeVoices") } : null,
    { sep: true },
    { label: `Delete ${t.id}`, disabled: ["C", "V1", "A1"].includes(t.id) || S.doc.clips.some((c) => c.track === t.id),
      run: () => { const r = history.commit("Delete track", (d) => ops.deleteTrack(d, t.id)); if (r.ok === false) toast(r.reason, true); } },
  ]);
}

// ------------------------------------------------------------------ zoom / scroll

function maxFrames() { return Math.max((S.doc ? seqEnd(S.doc) : 0) + 20 * FPS, 60 * FPS); }

function syncScrollbar() {
  const inner = hscroll.firstChild;
  inner.style.width = Math.max(W, maxFrames() * view.ppf + W / 2) + "px";
  const want = view.scrollF * view.ppf;
  if (Math.abs(hscroll.scrollLeft - want) > 1) hscroll.scrollLeft = want;
  const z = document.getElementById("tl-zoom");
  if (z) z.value = String(Math.round((Math.log(view.ppf / 0.01) / Math.log(24 / 0.01)) * 100));
  syncVScroll();
  // tracks deleted or the panel made taller: don't stay scrolled past the end
  if (view.scrollY > maxScrollY() + 0.5) requestAnimationFrame(() => scrollTracksTo(maxScrollY()));
}

export function setPpf(ppf, anchorX = null) {
  ppf = clamp(ppf, 0.01, 24);
  const ax = anchorX === null ? xOf(S.playhead) : anchorX;
  const fAt = fOfX(ax);
  view.ppf = ppf;
  view.scrollF = Math.max(0, fAt - ax / ppf);
  redraw();
}
export function zoomBy(k, anchorX = null) { setPpf(view.ppf * k, anchorX); }
function setZoomSlider(v) { setPpf(0.01 * Math.pow(24 / 0.01, v / 100)); }
export function zoomFit() {
  const len = S.doc ? Math.max(seqEnd(S.doc), 5 * FPS) : 60 * FPS;
  view.ppf = clamp((W - 40) / len, 0.01, 24);
  view.scrollF = 0;
  redraw();
}

function follow() {
  const x = xOf(S.playhead);
  if (x > W - 40 || x < 0) { view.scrollF = Math.max(0, S.playhead - 40 / view.ppf); redraw(); }
}

// Touchpad and wheel (2026-09-30, Jonathan): a swipe up or down moves the tracks up and down; a swipe sideways (or
// Shift+wheel) moves through time; a pinch (which arrives as Ctrl+wheel) or Ctrl/Alt+wheel zooms at the pointer.
function onWheel(e) {
  e.preventDefault();
  if (e.ctrlKey || e.altKey) { zoomBy(e.deltaY < 0 ? 1.2 : 1 / 1.2, e.offsetX); return; }
  let dx = e.deltaX, dy = e.deltaY;
  if (e.shiftKey && !dx) { dx = dy; dy = 0; }
  if (Math.abs(dx) > Math.abs(dy)) {
    view.scrollF = clamp(view.scrollF + dx / view.ppf, 0, maxFrames());
    redraw();
  } else if (dy) scrollTracksTo(view.scrollY + dy);
}

function maxScrollY() { return Math.max(0, contentHeight() + ADD_ROW - (H - RULER)); }
function scrollTracksTo(y) {
  y = clamp(y, 0, maxScrollY());
  if (Math.abs(y - view.scrollY) < 0.5) return;
  view.scrollY = y;
  renderHeaders();
  redraw();
}
function syncVScroll() {
  if (!vscroll) return;
  const vis = Math.max(1, H - RULER);
  vscroll.firstChild.style.height = (vis + maxScrollY()) + "px";
  vscroll.classList.toggle("is-empty", maxScrollY() <= 0);
  if (Math.abs(vscroll.scrollTop - view.scrollY) > 1) vscroll.scrollTop = view.scrollY;
}

// ------------------------------------------------------------------ drawing

let colors = {};
function readColors() {
  colors = {
    bg: cssVar("--tl-bg") || "#1b1c1d", row: cssVar("--tl-row") || "#232425", row2: cssVar("--tl-row2") || "#1f2021",
    line: cssVar("--line") || "#3c4043", text: cssVar("--on-surface") || "#e3e3e3", muted: cssVar("--muted") || "#8e918f",
    video: cssVar("--clip-video"), audio: cssVar("--clip-audio"), text_: cssVar("--clip-text"), shape: cssVar("--clip-shape"),
    image: cssVar("--clip-image"), caption: cssVar("--clip-caption"), sel: cssVar("--clip-sel") || "#fff",
    playhead: cssVar("--playhead") || "#a8c7fa", limit: cssVar("--limit") || "#f28b82", snap: cssVar("--snap") || "#fdd663",
    primary: cssVar("--primary") || "#a8c7fa",
  };
}

const MARK_COLORS = { green: "#81c995", red: "#f28b82", yellow: "#fdd663", blue: "#8ab4f8", purple: "#c58af9" };

export function redraw() {
  if (!bctx) return;
  layout();
  if (!colors.bg) readColors();
  const c = bctx;
  c.setTransform(dpr, 0, 0, dpr, 0, 0);
  c.fillStyle = colors.bg;
  c.fillRect(0, 0, W, H);
  if (lenEl) {
    const len = S.doc ? seqEnd(S.doc) : 0;
    lenEl.textContent = S.doc ? `${fmtLen(len)} / 1:30` : "";
    lenEl.classList.toggle("over", len > LIMIT_90);
  }
  const snapBtn = document.getElementById("tl-snap");
  if (snapBtn) snapBtn.classList.toggle("is-on", S.snap);
  if (!S.doc) {
    c.fillStyle = colors.muted;
    c.font = "14px 'Google Sans Text', sans-serif";
    c.fillText("Open a short from the bin, or open a recording, pick a call and press Make short.", 24, 60);
    drawOver();
    syncScrollbar();
    return;
  }
  // rows
  rows.forEach((r, i) => {
    c.fillStyle = r.kind === "caption" ? colors.row2 : i % 2 ? colors.row : colors.row2;
    c.fillRect(0, r.y, W, r.h);
    c.fillStyle = colors.line;
    c.fillRect(0, r.y + r.h - 1, W, 1);
  });
  // in/out range
  const rg = S.doc.range || {};
  if (rg.in !== null && rg.in !== undefined && rg.out !== null && rg.out !== undefined && rg.out > rg.in) {
    c.fillStyle = "rgba(168,199,250,.08)";
    c.fillRect(xOf(rg.in), RULER, (rg.out - rg.in) * view.ppf, H);
  }
  const f0 = Math.floor(fOfX(0)), f1 = Math.ceil(fOfX(W));
  for (const r of rows) {
    if (r.y + r.h < RULER || r.y > H) continue;
    c.save();
    c.beginPath(); c.rect(0, Math.max(RULER, r.y), W, r.h); c.clip();
    if (r.kind === "caption") drawCaptionRow(c, r, f0, f1);
    else for (const clip of clipsOn(S.doc, r.id)) if (clipEnd(clip) >= f0 && clip.start <= f1) drawClip(c, clip, r);
    c.restore();
  }
  // transitions and through edits
  for (const t of S.doc.transitions || []) {
    const r = rowOf(t.track); if (!r) continue;
    const w = ops.transitionWindow(S.doc, t);
    const x0 = xOf(w.s), x1 = xOf(w.e);
    const sel = S.selTransition === t.id;
    c.fillStyle = sel ? "rgba(253,214,99,.55)" : "rgba(255,255,255,.22)";
    c.strokeStyle = sel ? colors.snap : "rgba(255,255,255,.6)";
    c.lineWidth = 1;
    const y = r.y + r.h * 0.55, h = r.h * 0.36;
    c.fillRect(x0, y, Math.max(3, x1 - x0), h);
    c.strokeRect(x0 + 0.5, y + 0.5, Math.max(3, x1 - x0) - 1, h - 1);
    c.beginPath(); c.moveTo(x0, y + h); c.lineTo(x1, y); c.stroke();
  }
  for (const te of ops.throughEditsAt(S.doc)) {
    const r = rowOf(te.track); if (!r) continue;
    const x = xOf(te.f), y = r.y + 6;
    c.fillStyle = "rgba(255,255,255,.85)";
    c.beginPath(); c.moveTo(x - 5, y); c.lineTo(x, y + 4); c.lineTo(x - 5, y + 8); c.closePath(); c.fill();
    c.beginPath(); c.moveTo(x + 5, y); c.lineTo(x, y + 4); c.lineTo(x + 5, y + 8); c.closePath(); c.fill();
  }
  // 90 s line
  const x90 = xOf(LIMIT_90);
  if (x90 > 0 && x90 < W) { c.fillStyle = colors.limit; c.fillRect(x90, RULER, 1.5, H); }
  drawRuler(c);
  drawOver();
  syncScrollbar();
}

function tickStep() {
  const steps = [1, 2, 5, 10, 15, 30, 60, 150, 300, 600, 900, 1800, 3600, 9000, 18000, 36000, 108000];
  for (const s of steps) if (s * view.ppf >= 70) return s;
  return steps[steps.length - 1];
}

function drawRuler(c) {
  c.fillStyle = cssVar("--surface-1") || "#282a2c";
  c.fillRect(0, 0, W, RULER);
  c.fillStyle = colors.line; c.fillRect(0, RULER - 1, W, 1);
  const step = tickStep();
  const f0 = Math.floor(fOfX(0) / step) * step;
  c.font = "11px 'Google Sans Text', sans-serif";
  c.fillStyle = colors.muted; c.strokeStyle = colors.muted;
  for (let f = f0; xOf(f) < W; f += step) {
    const x = Math.round(xOf(f)) + 0.5;
    c.fillRect(x, RULER - 9, 1, 8);
    c.fillText(step < FPS ? fmtTC(f) : fmtTC(f, false), x + 4, 13);
    const sub = step / 5;
    if (sub * view.ppf > 8) for (let k = 1; k < 5; k += 1) c.fillRect(Math.round(xOf(f + sub * k)), RULER - 5, 1, 4);
  }
  for (const m of S.doc.markers || []) {
    const x = xOf(m.t);
    if (x < -10 || x > W + 10) continue;
    c.fillStyle = MARK_COLORS[m.color] || MARK_COLORS.green;
    c.beginPath(); c.moveTo(x - 5, 4); c.lineTo(x + 5, 4); c.lineTo(x + 5, 14); c.lineTo(x, 19); c.lineTo(x - 5, 14); c.closePath(); c.fill();
    if (S.selMarker === m.id) { c.strokeStyle = "#fff"; c.stroke(); }
  }
  const rg = S.doc.range || {};
  c.fillStyle = colors.primary;
  if (rg.in !== null && rg.in !== undefined) c.fillRect(xOf(rg.in), 0, 2, RULER);
  if (rg.out !== null && rg.out !== undefined) c.fillRect(xOf(rg.out) - 2, 0, 2, RULER);
}

function clipColor(clip) {
  return { video: colors.video, audio: colors.audio, text: colors.text_, shape: colors.shape, image: colors.image }[clip.type] || colors.video;
}

function clipLabel(clip) {
  if (clip.type === "text") return (clip.text && clip.text.str) || "Text";
  if (clip.type === "shape") return (clip.shape && clip.shape.kind) || "Shape";
  const a = lib.asset(clip.asset);
  return a ? a.name : clip.asset || clip.type;
}

function drawClip(c, clip, r) {
  const x0 = xOf(clip.start), x1 = xOf(clipEnd(clip));
  const y = r.y + 2, h = r.h - 4, w = Math.max(2, x1 - x0);
  const sel = S.sel.has(clip.id);
  c.globalAlpha = clip.on === false ? 0.45 : 1;
  c.fillStyle = clipColor(clip);
  c.beginPath(); c.roundRect(x0, y, w, h, 5); c.fill();
  c.save();
  c.beginPath(); c.roundRect(x0, y, w, h, 5); c.clip();
  if (clip.type === "video" && w > 20) drawFilmstrip(c, clip, x0, x1, y + 16, h - 18);
  if (clip.type === "image" && w > 20) { const bm = lib.bitmap(clip.asset); if (bm) { const th = h - 18, tw = th * (bm.width / bm.height); for (let x = x0; x < x1; x += tw + 2) c.drawImage(bm, x, y + 16, tw, th); } }
  if (clip.type === "audio" && w > 3) drawWave(c, clip, x0, x1, y + 14, h - 16);
  const gate = isVoiceClip(clip) ? gateFrames(clip, lib.transcript(clip.asset)) : null;
  if (gate) drawGate(c, clip, gate, x0, x1, y + 15, h - 15);
  if (clip.type === "audio" && (clip.track === "A1" || gate) && view.ppf * FPS >= 60) drawWords(c, clip, y + h - 4, gate);
  c.fillStyle = "rgba(0,0,0,.35)";
  c.fillRect(x0, y, w, 15);
  c.fillStyle = "#fff";
  c.font = "500 11px 'Google Sans Text', sans-serif";
  c.fillText(clipLabel(clip) + (clip.link ? "" : "") , x0 + 6, y + 11, Math.max(0, w - 12));
  if (clip.type === "audio") drawFades(c, clip, x0, x1, y, h);
  drawKeyBand(c, clip, x0, y, w, h, r);
  c.restore();
  if (sel) { c.strokeStyle = colors.sel; c.lineWidth = 2; c.beginPath(); c.roundRect(x0 + 1, y + 1, w - 2, h - 2, 5); c.stroke(); }
  c.globalAlpha = 1;
}

function drawFilmstrip(c, clip, x0, x1, y, h) {
  const tw = Math.max(12, Math.round((h * 9) / 16));
  const start = Math.max(x0, Math.floor((0 - x0) / tw) * tw + x0);
  for (let x = start; x < Math.min(x1, W); x += tw) {
    const f = clip.in + (x - x0) / view.ppf;
    const t = lib.thumb(clip.asset, f / FPS);
    if (t) c.drawImage(t.img, t.sx, t.sy, t.w, t.h, x, y, tw, h);
    else { c.fillStyle = "rgba(0,0,0,.15)"; c.fillRect(x, y, tw - 1, h); }
  }
}

function drawWave(c, clip, x0, x1, y, h) {
  const p = lib.peaks(clip.asset);
  if (!p) return;
  const perSec = view.ppf * FPS;
  const arr = perSec < 20 && p.p10.length ? p.p10 : p.p100;
  const rate = arr === p.p10 ? 10 : 100;
  const mid = y + h / 2;
  c.fillStyle = "rgba(255,255,255,.55)";
  const a = Math.max(x0, 0), b = Math.min(x1, W);
  for (let x = Math.floor(a); x < b; x += 1) {
    const s0 = (clip.in + (x - x0) / view.ppf) / FPS, s1 = (clip.in + (x + 1 - x0) / view.ppf) / FPS;
    let i0 = Math.floor(s0 * rate), i1 = Math.max(i0 + 1, Math.ceil(s1 * rate));
    let lo = 0, hi = 0;
    for (let i = i0; i < i1 && i * 2 + 1 < arr.length; i += 1) { lo = Math.min(lo, arr[i * 2]); hi = Math.max(hi, arr[i * 2 + 1]); }
    const gain = Math.pow(10, (clip.fx && clip.fx.volume && clip.fx.volume.v || 0) / 20);
    const top = mid - (hi / 127) * (h / 2) * gain, bot = mid - (lo / 127) * (h / 2) * gain;
    c.fillRect(x, Math.max(y, top), 1, Math.max(1, Math.min(y + h, bot) - Math.max(y, top)));
  }
}

// A voice track plays only its speaker: the stretches it doesn't play are shaded, so A1 and A2 read as a zipper
function drawGate(c, clip, gate, x0, x1, y, h) {
  c.fillStyle = "rgba(0,0,0,.55)";
  let f = clip.in;
  const shade = (a, b) => {
    const xa = Math.max(x0, xOf(clip.start + (a - clip.in))), xb = Math.min(x1, xOf(clip.start + (b - clip.in)));
    if (xb > xa && xb > 0 && xa < W) c.fillRect(xa, y, xb - xa, h);
  };
  for (const [a, b] of gate) { if (a > f) shade(f, a); f = Math.max(f, b); }
  if (f < clip.out) shade(f, clip.out);
}

function drawWords(c, clip, baseline, gate = null) {
  const tr = lib.transcript(clip.asset);
  if (!tr) return;
  c.fillStyle = "rgba(255,255,255,.62)";
  c.font = "10px 'Google Sans Text', sans-serif";
  const s0 = clip.in / FPS, s1 = clip.out / FPS;
  let lastX = -1e9;
  for (const w of tr.words) {
    if (w[1] <= s0) continue;
    if (w[0] >= s1) break;
    if (gate && !plays(gate, ((w[0] + w[1]) / 2) * FPS)) continue;
    const x = xOf(clip.start + (w[0] * FPS - clip.in));
    if (x < -40 || x > W) continue;
    if (x < lastX + 2) continue;
    c.fillText(w[2], x + 1, baseline);
    lastX = x + c.measureText(w[2]).width;
    c.fillRect(x, baseline - 18, 1, 5);
  }
}

function drawFades(c, clip, x0, x1, y, h) {
  const fi = (clip.fadeIn || 0) * view.ppf, fo = (clip.fadeOut || 0) * view.ppf;
  c.strokeStyle = "rgba(255,255,255,.8)"; c.lineWidth = 1;
  c.fillStyle = "rgba(0,0,0,.25)";
  if (fi > 0) { c.beginPath(); c.moveTo(x0, y + h); c.lineTo(x0 + fi, y + 15); c.lineTo(x0, y + 15); c.closePath(); c.fill(); c.beginPath(); c.moveTo(x0, y + h); c.lineTo(x0 + fi, y + 15); c.stroke(); }
  if (fo > 0) { c.beginPath(); c.moveTo(x1, y + h); c.lineTo(x1 - fo, y + 15); c.lineTo(x1, y + 15); c.closePath(); c.fill(); c.beginPath(); c.moveTo(x1, y + h); c.lineTo(x1 - fo, y + 15); c.stroke(); }
  c.fillStyle = "#fff";
  c.fillRect(x0 + fi - 3, y + 15, 6, 6);
  c.fillRect(x1 - fo - 3, y + 15, 6, 6);
}

export function bandProp(clip) {
  if (S.shownProp[clip.id]) return S.shownProp[clip.id];
  for (const [p] of kf.PROPS) if (kf.isAnimated(clip, p)) return p;
  return clip.type === "audio" ? "volume" : null;
}

// volume reaches +24 dB: Normalize voices lifts quiet phone audio past +12 (+13.1 dB on the 2026-09-28 session)
const PROP_RANGE = { posX: [-540, 1620], posY: [-960, 2880], scale: [0, 300], rot: [-180, 180], opacity: [0, 100], volume: [-40, 24] };
// dragging the volume line (2026-10-02): a fixed step, not the band's own scale (19 px for 64 dB at the normal track
// height would be over 3 dB a pixel); Ctrl for fine; a catch at 0 dB; the same limits as Effect Controls
const VOL_STEP = 0.2, VOL_FINE = 0.05, VOL_MIN = -60, VOL_MAX = 24, VOL_CATCH = 0.4;
let volInfo = null;       // {x, y, text}: the level shown beside the pointer while hovering or dragging the line
function bandY(prop, v, y, h) { const [lo, hi] = PROP_RANGE[prop]; return y + h - 4 - ((clamp(v, lo, hi) - lo) / (hi - lo)) * (h - 22); }
function bandV(prop, py, y, h) { const [lo, hi] = PROP_RANGE[prop]; return lo + ((y + h - 4 - py) / (h - 22)) * (hi - lo); }

// where the volume line of audio clip c crosses x (wrap pixels), and the level there
function volAt(c, x) { return kf.valueAt(c, "volume", c.in + (x - xOf(c.start)) / view.ppf); }
function volLineY(c, row, x) { return bandY("volume", volAt(c, x), row.y + 17, row.h - 19); }
const fmtDb = (v) => (v > 0.05 ? "+" : v < -0.05 ? "−" : "") + Math.abs(v).toFixed(1) + " dB";

function drawKeyBand(c, clip, x0, y, w, h) {
  const prop = bandProp(clip);
  if (!prop) return;
  const animated = kf.isAnimated(clip, prop);
  if (!animated && !(S.sel.has(clip.id) || S.tool === "pen")) return;
  // a selected audio clip's volume line is a handle (drag it up or down): yellow like the keys, so it reads as one
  const handle = prop === "volume" && S.sel.has(clip.id);
  c.strokeStyle = animated ? "rgba(253,214,99,.95)" : handle ? "rgba(253,214,99,.8)" : "rgba(255,255,255,.35)";
  c.lineWidth = 1.2;
  c.beginPath();
  const step = Math.max(2, Math.floor(w / 200));
  for (let x = 0; x <= w; x += step) {
    const t = clip.in + x / view.ppf;
    const py = bandY(prop, kf.valueAt(clip, prop, t), y + 15, h - 15);
    if (x === 0) c.moveTo(x0 + x, py); else c.lineTo(x0 + x, py);
  }
  c.stroke();
  const keys = kf.keysOf(clip, prop) || [];
  for (const k of keys) {
    const x = x0 + (k.t - clip.in) * view.ppf;
    const py = bandY(prop, k.v, y + 15, h - 15);
    c.fillStyle = "#fdd663"; c.strokeStyle = "#000";
    c.beginPath(); c.moveTo(x, py - 5); c.lineTo(x + 5, py); c.lineTo(x, py + 5); c.lineTo(x - 5, py); c.closePath(); c.fill(); c.stroke();
  }
}

function drawCaptionRow(c, r, f0, f1) {
  const cfg = S.doc.captions;
  const evs = cfg.events || [];
  c.font = "600 10px 'Google Sans Text', sans-serif";
  if (!evs.length && genStatus(S.doc) === "none") {      // a new short: no captions until Generate (G1, 2026-10-02)
    const job = S.genCaps && S.genCaps.pid === S.doc.id && S.genCaps.state === "running";
    c.fillStyle = "rgba(255,255,255,.55)";
    c.fillText(job ? "Making the captions…" : "No captions yet · trim the short, then Generate captions (the sparkle button, the Captions tab or the Clip menu)",
      Math.max(8, xOf(0) + 8), r.y + r.h / 2 + 3);
    return;
  }
  for (const ev of evs) {
    if (ev.e < f0 || ev.s > f1) continue;
    const x0 = xOf(ev.s), x1 = xOf(ev.e);
    c.globalAlpha = cfg.on ? 1 : 0.4;
    c.fillStyle = colors.caption || "#6b5e2a";
    c.beginPath(); c.roundRect(x0, r.y + 4, Math.max(2, x1 - x0 - 1), r.h - 8, 4); c.fill();
    // who is talking: a stripe in the voice's color along the bottom (one voice per group); text stays white
    c.fillStyle = colorsFor(ev.words[0].k, S.config && S.config.captionColors)[0];
    c.fillRect(x0 + 1, r.y + r.h - 7, Math.max(1, x1 - x0 - 3), 3);
    c.fillStyle = "#fff";
    c.fillText(ev.words.map((w) => w.w).join(" "), x0 + 4, r.y + r.h / 2 + 3, Math.max(0, x1 - x0 - 8));
    c.globalAlpha = 1;
  }
}

export function drawOver() {
  if (!octx) return;
  const c = octx;
  c.setTransform(dpr, 0, 0, dpr, 0, 0);
  c.clearRect(0, 0, W, H);
  if (!S.doc) return;
  if (snapLine !== null) { c.fillStyle = colors.snap; c.fillRect(xOf(snapLine) - 0.5, 0, 1, H); }
  if (marquee) { c.fillStyle = "rgba(168,199,250,.15)"; c.strokeStyle = colors.primary; const { x0, y0, x1, y1 } = marquee;
    c.fillRect(Math.min(x0, x1), Math.min(y0, y1), Math.abs(x1 - x0), Math.abs(y1 - y0)); c.strokeRect(Math.min(x0, x1) + 0.5, Math.min(y0, y1) + 0.5, Math.abs(x1 - x0), Math.abs(y1 - y0)); }
  if (dropGhost) { c.fillStyle = "rgba(168,199,250,.35)"; c.fillRect(dropGhost.x, dropGhost.y, dropGhost.w, dropGhost.h); }
  if (hover && hover.kind === "edit" && (S.tool === "rolling" || S.tool === "ripple" || S.tool === "select")) {
    const r = rowOf(hover.track); if (r) { c.fillStyle = colors.snap; c.fillRect(xOf(hover.f) - 1, r.y, 2, r.h); }
  }
  if (S.tool === "razor" && hover && hover.f !== undefined && hover.row) {
    const f = snapFrame(hover.f, { words: true });
    c.fillStyle = "#f28b82"; c.fillRect(xOf(f) - 0.5, hover.row.y, 1, hover.row.h);
  }
  if (volInfo) {                    // the volume line's level beside the pointer
    c.font = "500 11px 'Google Sans Text', sans-serif";
    const tw = c.measureText(volInfo.text).width + 12;
    const bx = Math.min(W - tw - 4, volInfo.x + 12), by = Math.max(2, volInfo.y - 26);
    c.fillStyle = "rgba(19,19,20,.92)"; c.beginPath(); c.roundRect(bx, by, tw, 20, 6); c.fill();
    c.fillStyle = "#fdd663"; c.fillText(volInfo.text, bx + 6, by + 14);
  }
  const x = Math.round(xOf(S.playhead)) + 0.5;
  c.fillStyle = colors.playhead;
  c.fillRect(x - 0.5, 0, 1.5, H);
  c.beginPath(); c.moveTo(x - 6, 0); c.lineTo(x + 6, 0); c.lineTo(x + 6, 8); c.lineTo(x, 14); c.lineTo(x - 6, 8); c.closePath(); c.fill();
}

// ------------------------------------------------------------------ snapping

function snapTargets(exclude = new Set(), { words = false } = {}) {
  const t = [0, Math.round(S.playhead)];
  for (const c of S.doc.clips) if (!exclude.has(c.id)) t.push(c.start, clipEnd(c));
  for (const m of S.doc.markers || []) t.push(m.t);
  const rg = S.doc.range || {};
  if (rg.in !== null && rg.in !== undefined) t.push(rg.in);
  if (rg.out !== null && rg.out !== undefined) t.push(rg.out);
  if (words) for (const w of wordsOnTimeline(S.doc, lib, { trim: true })) t.push(w.s, w.e);
  return t;
}

export function snapFrame(f, opts = {}) {
  f = Math.round(f);
  if (!S.snap) { snapLine = null; return f; }
  const targets = snapTargets(opts.exclude, opts);
  let best = null, bd = SNAP_PX / view.ppf;
  for (const t of targets) { const d = Math.abs(t - f); if (d <= bd) { bd = d; best = t; } }
  snapLine = best;
  return best === null ? f : best;
}

// snap a moving block: tries its start and its end against the targets; returns the adjusted delta
function snapDelta(dF, starts, ends, exclude) {
  if (!S.snap) { snapLine = null; return dF; }
  const targets = snapTargets(exclude);
  let best = null, bd = SNAP_PX / view.ppf;
  for (const p of [...starts, ...ends]) for (const t of targets) {
    const d = t - (p + dF);
    if (Math.abs(d) <= bd) { bd = Math.abs(d); best = { adj: d, t }; }
  }
  snapLine = best ? best.t : null;
  return best ? dF + best.adj : dF;
}

// ------------------------------------------------------------------ hit testing

export function hitAt(x, y) {
  if (!S.doc) return { kind: "none" };
  const f = fOfX(x);
  if (y < RULER) {
    const mk = (S.doc.markers || []).find((m) => Math.abs(xOf(m.t) - x) <= 6);
    return mk ? { kind: "marker", marker: mk, f } : { kind: "ruler", f };
  }
  const row = rowAt(y);
  if (!row) return { kind: "empty", f };
  if (row.kind === "caption") return { kind: "caption", f, row, track: row.id };
  const cs = clipsOn(S.doc, row.id);
  // keyframe diamonds on the band
  for (const c of cs) {
    const prop = bandProp(c);
    if (!prop || !(S.sel.has(c.id) || S.tool === "pen" || kf.isAnimated(c, prop))) continue;
    const keys = kf.keysOf(c, prop) || [];
    for (const k of keys) {
      const kx = xOf(c.start) + (k.t - c.in) * view.ppf;
      const ky = bandY(prop, k.v, row.y + 17, row.h - 19);
      if (Math.abs(kx - x) <= 6 && Math.abs(ky - y) <= 6) return { kind: "key", clip: c, prop, t: k.t, f, row, track: row.id };
    }
  }
  // fade handles
  for (const c of cs) {
    if (c.type !== "audio") continue;
    const x0 = xOf(c.start), x1 = xOf(clipEnd(c));
    const hy = row.y + 17;
    if (Math.abs(y - hy - 3) <= 6) {
      if (Math.abs(x - (x0 + (c.fadeIn || 0) * view.ppf)) <= 6) return { kind: "fade", clip: c, which: "fadeIn", f, row, track: row.id };
      if (Math.abs(x - (x1 - (c.fadeOut || 0) * view.ppf)) <= 6) return { kind: "fade", clip: c, which: "fadeOut", f, row, track: row.id };
    }
  }
  // the volume line on a selected audio clip, with the Selection tool: drag it up or down (2026-10-02). Only on
  // selected clips, so a click on another clip still selects and moves it; the ends stay trim handles.
  if (S.tool === "select") {
    for (const c of cs) {
      if (c.type !== "audio" || !S.sel.has(c.id)) continue;
      const x0 = xOf(c.start), x1 = xOf(clipEnd(c));
      if (x < x0 + EDGE || x > x1 - EDGE) continue;
      if (Math.abs(y - volLineY(c, row, x)) <= 4) return { kind: "volume", clip: c, f, row, track: row.id };
    }
  }
  // transitions
  for (const t of S.doc.transitions || []) {
    if (t.track !== row.id) continue;
    const w = ops.transitionWindow(S.doc, t);
    if (x >= xOf(w.s) - 2 && x <= xOf(w.e) + 2 && y >= row.y + row.h * 0.5) return { kind: "transition", transition: t, f, row, track: row.id };
  }
  // edit points and edges
  for (let i = 0; i < cs.length; i += 1) {
    const c = cs[i];
    const x0 = xOf(c.start), x1 = xOf(clipEnd(c));
    const next = cs[i + 1];
    if (next && next.start === clipEnd(c) && Math.abs(x - x1) <= EDGE) {
      return { kind: "edit", left: c, right: next, f: clipEnd(c), row, track: row.id, edge: x < x1 ? "out" : "in", clip: x < x1 ? c : next };
    }
    if (x >= x0 && x <= x1) {
      const ew = Math.min(EDGE, (x1 - x0) / 3);
      if (x - x0 <= ew) return { kind: "edge", clip: c, edge: "in", f, row, track: row.id };
      if (x1 - x <= ew) return { kind: "edge", clip: c, edge: "out", f, row, track: row.id };
      return { kind: "clip", clip: c, f, row, track: row.id };
    }
  }
  return { kind: "gap", f, row, track: row.id };
}

// ------------------------------------------------------------------ pointer

function cursorFor(h) {
  if (!h) return "";
  const t = S.tool;
  if (t === "hand") return "grab";
  if (t === "zoom") return "zoom-in";
  if (t === "razor") return h.clip || h.kind === "clip" ? "crosshair" : "default";
  if (h.kind === "key") return "pointer";
  if (h.kind === "volume") return "ns-resize";
  if (h.kind === "fade") return "ew-resize";
  if (h.kind === "edit") return t === "rolling" ? "col-resize" : "ew-resize";
  if (h.kind === "edge") return t === "ripple" ? "e-resize" : "ew-resize";
  if (h.kind === "clip") return t === "slip" || t === "slide" ? "ew-resize" : t === "pen" ? "copy" : "default";
  if (t === "text") return "text";
  return "default";
}

function onHover(e) {
  if (history.dragging()) return;
  const r = wrap.getBoundingClientRect();
  hover = hitAt(e.clientX - r.left, e.clientY - r.top);
  wrap.style.cursor = cursorFor(hover);
  // the level, beside the pointer, while it rests on a volume line
  volInfo = hover.kind === "volume" ? { x: e.clientX - r.left, y: e.clientY - r.top, text: fmtDb(volAt(hover.clip, e.clientX - r.left)) } : null;
  drawOver();
}

function selectClick(clip, e) {
  const ids = withLinked(S.doc, [clip.id], e.altKey);
  if (e.shiftKey || e.ctrlKey) {
    const s = new Set(S.sel);
    const has = ids.every((id) => s.has(id));
    for (const id of ids) has ? s.delete(id) : s.add(id);
    S.sel = s; S.selTransition = null; emit("sel");
  } else if (!S.sel.has(clip.id) || e.altKey) selectOnly(ids);   // Alt grabs just this side of a linked pair
}

function drag(e, onMove, onUp, label) {
  const r = wrap.getBoundingClientRect();
  const x0 = e.clientX - r.left, y0 = e.clientY - r.top;
  try { wrap.setPointerCapture(e.pointerId); } catch (err) { /* synthetic events in tests */ }
  let started = false;
  const move = (ev) => {
    const x = ev.clientX - r.left, y = ev.clientY - r.top;
    if (!started && Math.abs(x - x0) < 3 && Math.abs(y - y0) < 3) return;
    if (!started && label) history.beginDrag(label);
    started = true;
    onMove(x - x0, y - y0, ev, x, y);
    drawOver();
  };
  const up = (ev) => {
    wrap.removeEventListener("pointermove", move);
    wrap.removeEventListener("pointerup", up);
    wrap.removeEventListener("pointercancel", up);
    document.removeEventListener("keydown", esc, true);
    if (label && started) history.endDrag();
    snapLine = null;
    if (onUp) onUp(started, ev);
    drawOver();
  };
  const esc = (ev) => { if (ev.key === "Escape") { history.cancelDrag(); wrap.removeEventListener("pointermove", move); wrap.removeEventListener("pointerup", up); snapLine = null; marquee = null; drawOver(); } };
  wrap.addEventListener("pointermove", move);
  wrap.addEventListener("pointerup", up);
  wrap.addEventListener("pointercancel", up);
  document.addEventListener("keydown", esc, true);
}

function reportFail(res) { if (res && res.ok === false && res.reason) toast(res.reason, true); }

function onDown(e) {
  if (e.button === 1 || (e.button === 0 && S.tool === "hand")) return panDrag(e);
  if (e.button !== 0) return;
  wrap.focus();
  const r = wrap.getBoundingClientRect();
  const x = e.clientX - r.left, y = e.clientY - r.top;
  const h = hitAt(x, y);
  if (!S.doc) return;
  if (h.kind === "ruler" || h.kind === "marker") {
    if (h.kind === "marker") { S.selMarker = h.marker.id; emit("sel"); }
    if (S.playing) pb.pause();
    pb.seek(snapFrame(h.f));
    return drag(e, (dx, dy, ev, px) => pb.seek(snapFrame(fOfX(px))), () => { snapLine = null; });
  }
  const t = S.tool;
  if (t === "zoom") { zoomBy(e.altKey ? 1 / 1.6 : 1.6, x); return; }
  if (t === "razor") {
    if (!h.clip && h.kind !== "clip") return;
    const f = snapFrame(h.f, { words: true });
    const res = history.commit("Razor", (d) => (e.shiftKey ? ops.splitAll(d, ctxOps(), f) : ops.split(d, ctxOps(), withLinked(d, [h.clip.id], e.altKey), f)));
    snapLine = null; reportFail(res); return;
  }
  if (t === "text" && h.row && h.row.kind !== "audio") return addTextAt(snapFrame(h.f), h.row.id);
  if (h.kind === "key") return keyDrag(e, h);
  if (t === "pen" && (h.kind === "clip" || h.kind === "edge") && h.clip) return penAdd(e, h, y);
  if (h.kind === "fade") return fadeDrag(e, h);
  if (h.kind === "volume") return volumeDrag(e, h, x);
  if (h.kind === "transition") { S.selTransition = h.transition.id; S.sel = new Set(); emit("sel"); return; }
  if ((h.kind === "edit" || h.kind === "edge") && (t === "select" || t === "ripple" || t === "rolling")) {
    if (t === "rolling" && h.kind === "edit") return rollDrag(e, h);
    return trimDrag(e, h, t === "ripple" || e.ctrlKey);
  }
  if (h.kind === "clip" || h.kind === "edge" || h.kind === "edit") {
    const clip = h.clip;
    selectClick(clip, e);
    if (t === "slip") return slipDrag(e, clip);
    if (t === "slide") return slideDrag(e, clip);
    return moveDrag(e, h);
  }
  // empty: marquee (and clear selection unless shift). It starts from any spot without a clip: an empty stretch of a
  // track, the room below the last track, or the Captions row (2026-10-02: "I should also be able to drag select clips")
  if (!e.shiftKey) { S.sel = new Set(); S.selTransition = null; S.selMarker = null; emit("sel"); }
  if (t === "select" && (h.kind === "gap" || h.kind === "empty" || h.kind === "caption") && e.detail === 1) {
    marquee = { x0: x, y0: y, x1: x, y1: y };
    drag(e, (dx, dy, ev, px, py) => { marquee.x1 = px; marquee.y1 = py; selectMarquee(e.shiftKey); },
      (started) => { if (!started) pb.seek(snapFrame(h.f)); marquee = null; });
  }
}

function selectMarquee(add) {
  const { x0, y0, x1, y1 } = marquee;
  const fa = fOfX(Math.min(x0, x1)), fb = fOfX(Math.max(x0, x1));
  const ya = Math.min(y0, y1), yb = Math.max(y0, y1);
  const ids = [];
  for (const r of rows) {
    if (r.y + r.h < ya || r.y > yb || r.kind === "caption") continue;
    for (const c of clipsOn(S.doc, r.id)) if (clipEnd(c) > fa && c.start < fb) ids.push(c.id);
  }
  S.sel = new Set(add ? [...S.sel, ...ids] : ids);
  emit("sel");
}

function panDrag(e) {
  const sf = view.scrollF, sy = view.scrollY;
  wrap.style.cursor = "grabbing";
  drag(e, (dx, dy) => {
    view.scrollF = Math.max(0, sf - dx / view.ppf);
    view.scrollY = clamp(sy - dy, 0, Math.max(0, contentHeight() - (H - RULER) + 40));
    renderHeaders(); redraw();
  }, () => { wrap.style.cursor = ""; });
}

function rowsDelta(clip, py) {
  const row = rowAt(py);
  if (!row || row.kind === "caption") return 0;
  const kind = trackOf(S.doc, clip.track).kind;
  if (row.kind !== kind) return 0;
  const same = S.doc.tracks.filter((t) => t.kind === kind).map((t) => t.id);
  return same.indexOf(row.id) - same.indexOf(clip.track);
}

function moveDrag(e, h) {
  const ids = [...S.sel];
  const cs = ids.map((id) => clipById(S.doc, id));
  const starts = cs.map((c) => c.start), ends = cs.map((c) => clipEnd(c));
  const lead = h.clip;
  drag(e, (dx, dy, ev, px, py) => {
    let dF = Math.round(dx / view.ppf);
    dF = snapDelta(dF, starts, ends, new Set(ids));
    const dRow = rowsDelta(lead, py);
    const res = history.dragTo((d) => ops.moveClips(d, ctxOps(), [lead.id, ...ids.filter((i) => i !== lead.id)], dF, dRow, { insert: ev.ctrlKey }));
    if (res.ok === false) wrap.style.cursor = "not-allowed"; else wrap.style.cursor = ev.ctrlKey ? "copy" : "grabbing";
  }, (started) => { wrap.style.cursor = ""; if (!started && !e.shiftKey && !e.ctrlKey) selectOnly(withLinked(S.doc, [lead.id], e.altKey)); }, "Move");
}

function trimDrag(e, h, ripple) {
  const clip = h.clip, edge = h.edge;
  if (!S.sel.has(clip.id)) selectOnly(withLinked(S.doc, [clip.id], e.altKey));
  const ids = withLinked(S.doc, [clip.id], e.altKey);
  const edgeF = edge === "in" ? clip.start : clipEnd(clip);
  drag(e, (dx) => {
    let target = snapFrame(edgeF + dx / view.ppf, { exclude: new Set(ids), words: true });
    const d = target - edgeF;
    history.dragTo((doc) => (ripple ? ops.rippleTrim(doc, ctxOps(), ids, edge, edge === "in" ? d : d) : ops.trimEdge(doc, ctxOps(), ids, edge, d)));
  }, null, ripple ? "Ripple Trim" : "Trim");
}

function rollDrag(e, h) {
  const cut = h.f;
  drag(e, (dx) => {
    const target = snapFrame(cut + dx / view.ppf, { exclude: new Set([h.left.id, h.right.id]), words: true });
    history.dragTo((d) => ops.roll(d, ctxOps(), h.left.id, h.right.id, target - cut));
  }, null, "Rolling Edit");
}

function slipDrag(e, clip) {
  const ids = withLinked(S.doc, [clip.id], e.altKey);
  drag(e, (dx) => { const d = -Math.round(dx / view.ppf); history.dragTo((doc) => ops.slip(doc, ctxOps(), ids, d)); pb.seek(S.playhead); }, null, "Slip");
}

function slideDrag(e, clip) {
  drag(e, (dx) => { const d = Math.round(dx / view.ppf); history.dragTo((doc) => ops.slide(doc, ctxOps(), clip.id, d)); }, null, "Slide");
}

function fadeDrag(e, h) {
  const c0 = h.clip;
  drag(e, (dx, dy, ev, px) => {
    const x0 = xOf(c0.start), x1 = xOf(clipEnd(c0));
    const frames = h.which === "fadeIn" ? (px - x0) / view.ppf : (x1 - px) / view.ppf;
    history.dragTo((d) => ops.setFade(d, c0.id, h.which, frames));
  }, null, "Fade");
}

// the clips a volume drag or reset changes: every selected audio clip on an unlocked track (the grabbed one with them),
// so selecting several clips turns them all up or down by the same amount (Jonathan, 2026-10-02: "for select media")
function volumeTargets(clip) {
  const ids = S.sel.has(clip.id) ? [...S.sel] : [clip.id];
  return ids.filter((id) => { const c = clipById(S.doc, id); const t = c && trackOf(S.doc, c.track); return c && c.type === "audio" && !(t && t.lock); });
}

// shift a clip's level by d dB: the plain level, and every keyframe by the same amount so a fade keeps its shape
function shiftVolume(c, d) {
  c.fx = c.fx || {};
  const p = c.fx.volume || { v: 0 };
  const lim = (v) => Math.round(clamp(v + d, VOL_MIN, VOL_MAX) * 10) / 10;
  p.v = lim(p.v || 0);
  if (p.k) for (const k of p.k) k.v = lim(k.v);
  c.fx.volume = p;
}

function volumeDrag(e, h, x) {
  const clip = h.clip, ids = volumeTargets(clip);
  const v0 = volAt(clip, x);
  const n = ids.length;
  let delta = 0, lastY = e.clientY;
  drag(e, (dx, dy, ev, px, py) => {
    delta += (lastY - ev.clientY) * (ev.ctrlKey || ev.metaKey ? VOL_FINE : VOL_STEP);   // up is louder
    lastY = ev.clientY;
    let level = clamp(v0 + delta, VOL_MIN, VOL_MAX);
    if (!(ev.ctrlKey || ev.metaKey) && Math.abs(level) < VOL_CATCH) level = 0;          // a catch at unity
    const d = level - v0;
    history.dragTo((doc) => { for (const id of ids) { const c = clipById(doc, id); if (c) shiftVolume(c, d); } return { ok: true }; });
    volInfo = { x: px, y: py, text: fmtDb(level) + (n > 1 ? ` · ${n} clips ${d >= 0 ? "+" : "−"}${Math.abs(d).toFixed(1)}` : "") };
  }, () => { volInfo = null; drawOver(); }, n > 1 ? "Volume (" + n + " clips)" : "Volume");
}

function keyDrag(e, h) {
  const clip = h.clip, prop = h.prop, t0 = h.t;
  selectOnly(withLinked(S.doc, [clip.id], true));
  if (e.button === 0 && e.detail === 2) return;
  drag(e, (dx, dy, ev, px, py) => {
    const r = rowOf(clip.track);
    const t1 = Math.round(t0 + dx / view.ppf);
    const v = ev.shiftKey ? undefined : Math.round(bandV(prop, py, r.y + 17, r.h - 19) * 10) / 10;
    history.dragTo((d) => { const c = clipById(d, clip.id); kf.moveKey(c, prop, t0, clamp(t1, c.in, c.out), v); return { ok: true }; });
  }, null, "Move Keyframe");
}

function penAdd(e, h, y) {
  const clip = h.clip;
  let prop = bandProp(clip) || (clip.type === "audio" ? "volume" : "opacity");
  S.shownProp[clip.id] = prop;
  const r = rowOf(clip.track);
  const t = Math.round(clip.in + (h.f - clip.start));
  const v = Math.round(bandV(prop, y, r.y + 17, r.h - 19) * 10) / 10;
  history.commit("Add Keyframe", (d) => { const c = clipById(d, clip.id); kf.addKey(c, prop, t, v); return { ok: true }; });
  selectOnly([clip.id]);
}

function addTextAt(f, trackId) {
  const track = trackId && trackOf(S.doc, trackId) && trackOf(S.doc, trackId).kind === "video" ? trackId : "V2";
  runAction("newText", { f, track });
}

function onDbl(e) {
  const r = wrap.getBoundingClientRect();
  const h = hitAt(e.clientX - r.left, e.clientY - r.top);
  if (h.kind === "clip" && h.clip.type === "text") { selectOnly([h.clip.id]); emit("focusText"); }
  if (h.kind === "volume") {
    // double-click the volume line: that clip back to 0 dB; other selected clips move by the same amount, as in a drag
    const ids = volumeTargets(h.clip), d = -volAt(h.clip, e.clientX - r.left);
    history.commit(ids.length > 1 ? "Reset Volume (" + ids.length + " clips)" : "Reset Volume", (doc) => {
      for (const id of ids) { const c = clipById(doc, id); if (c) shiftVolume(c, d); }
      return { ok: true };
    });
  }
  if (h.kind === "marker") runAction("editMarker", h.marker.id);
  if (h.kind === "caption") { pb.seek(h.f); emit("focusCaptions"); }
}

function onContext(e) {
  e.preventDefault();
  if (!S.doc) return;
  const r = wrap.getBoundingClientRect();
  const h = hitAt(e.clientX - r.left, e.clientY - r.top);
  const at = { x: e.clientX, y: e.clientY };
  if (h.kind === "key") {
    return openMenu(at, [...kf.EASES.map(([id, label]) => ({ label, checked: () => { const k = (kf.keysOf(h.clip, h.prop) || []).find((x) => x.t === h.t); return k && (k.e || "linear") === id; },
      run: () => history.commit("Keyframe Easing", (d) => { kf.setEase(clipById(d, h.clip.id), h.prop, h.t, id); }) })),
    { sep: true }, { label: "Delete keyframe", run: () => history.commit("Delete Keyframe", (d) => { kf.removeKey(clipById(d, h.clip.id), h.prop, h.t); }) }]);
  }
  if (h.kind === "transition") {
    S.selTransition = h.transition.id; emit("sel");
    return openMenu(at, [
      { label: "Cross dissolve", checked: h.transition.kind === "dissolve", run: () => history.commit("Transition", (d) => { d.transitions.find((t) => t.id === h.transition.id).kind = "dissolve"; }) },
      { label: "Dip to black", checked: h.transition.kind === "dip", run: () => history.commit("Transition", (d) => { d.transitions.find((t) => t.id === h.transition.id).kind = "dip"; }) },
      { sep: true }, { label: "Delete transition", run: () => runAction("clear") }]);
  }
  if (h.kind === "marker") return openMenu(at, [{ label: "Edit marker…", run: () => runAction("editMarker", h.marker.id) },
    { label: "Delete marker", run: () => history.commit("Delete Marker", (d) => { d.markers = d.markers.filter((m) => m.id !== h.marker.id); }) }]);
  if (h.kind === "gap") {
    return openMenu(at, [{ label: "Ripple delete gap", run: () => { const res = history.commit("Ripple Delete Gap", (d) => ops.rippleGap(d, ctxOps(), h.track, Math.round(h.f))); reportFail(res); } }]);
  }
  if (h.kind === "edit") {
    return openMenu(at, [
      { label: "Join through edit", disabled: !ops.isThroughEdit(h.left, h.right), run: () => runAction("join", h.left.id) },
      { label: "Cross dissolve", run: () => runAction("dissolveAt", { track: h.track, f: h.f }) },
      { label: "Dip to black", run: () => runAction("dipAt", { track: h.track, f: h.f }) }]);
  }
  if (h.clip) {
    if (!S.sel.has(h.clip.id)) selectOnly(withLinked(S.doc, [h.clip.id], e.altKey));
    const props = kf.PROPS.filter(([p]) => (p === "volume") === (h.clip.type === "audio"));
    return openMenu(at, [
      { label: "Split here", keys: "C", run: () => { const f = snapFrame(h.f, { words: true }); snapLine = null; reportFail(history.commit("Razor", (d) => ops.split(d, ctxOps(), withLinked(d, [h.clip.id]), f))); } },
      { label: "Ripple delete", keys: "Shift+Del", run: () => runAction("rippleDelete") },
      { label: "Delete", keys: "Del", run: () => runAction("clear") },
      { sep: true },
      { label: h.clip.link ? "Unlink" : "Link", keys: "Ctrl+L", run: () => runAction("link") },
      { label: "Enable", checked: h.clip.on !== false, keys: "Shift+E", run: () => runAction("enable") },
      { label: "Join through edit", disabled: !canJoin(h.clip), run: () => runAction("join", h.clip.id) },
      { sep: true },
      { label: "Show keyframes", sub: props.map(([p, label]) => ({ label, checked: bandProp(h.clip) === p, run: () => { S.shownProp[h.clip.id] = p; redraw(); } })) },
      { label: "Reveal in bin", disabled: !h.clip.asset, run: () => { S.selectedAsset = h.clip.asset; emit("bin"); } },
    ]);
  }
}

function canJoin(clip) {
  const cs = clipsOn(S.doc, clip.track);
  const i = cs.findIndex((c) => c.id === clip.id);
  return ops.isThroughEdit(cs[i], cs[i + 1]) || ops.isThroughEdit(cs[i - 1], cs[i]);
}

// ------------------------------------------------------------------ drop from the bin

function dropTarget(e) {
  const r = wrap.getBoundingClientRect();
  const x = e.clientX - r.left, y = e.clientY - r.top;
  return { x, y, f: Math.max(0, Math.round(fOfX(x))), row: rowAt(y) };
}

function onDragOver(e) {
  if (!S.doc || !e.dataTransfer.types.includes("application/x-studio")) return;
  e.preventDefault();
  e.dataTransfer.dropEffect = "copy";
  const t = dropTarget(e);
  if (t.row && t.row.kind !== "caption") dropGhost = { x: xOf(snapFrame(t.f)), y: t.row.y + 2, w: 90, h: t.row.h - 4 };
  drawOver();
}

function onDrop(e) {
  dropGhost = null;
  if (!S.doc) return;
  const raw = e.dataTransfer.getData("application/x-studio");
  if (!raw) return;
  e.preventDefault();
  const item = JSON.parse(raw);
  const t = dropTarget(e);
  const f = snapFrame(t.f);
  snapLine = null;
  runAction("placeAsset", { item, f, track: t.row ? t.row.id : null, insert: e.ctrlKey });
  drawOver();
}

export function timelineApi() {
  return { xOf, fOfX, hitAt, redraw, rows: () => rows, view, snapFrame, zoomFit, setPpf, yOfTrack, bandProp,
    // where a keyframe diamond sits, in timeline-local pixels (tests aim the pointer with it)
    keyPoint(clip, prop, t) { const r = rowOf(clip.track); return { x: xOf(clip.start) + (t - clip.in) * view.ppf, y: bandY(prop, kf.valueAt(clip, prop, t), r.y + 17, r.h - 19) }; },
    bandValue(clip, prop, y) { const r = rowOf(clip.track); return bandV(prop, y, r.y + 17, r.h - 19); },
    // tests: where a clip's volume line sits at timeline frame f (wrap pixels)
    volY(clip, f) { const r = rowOf(clip.track); return volLineY(clip, r, xOf(f)); } };
}
export function sizeOf() { return { W, H }; }
export { RULER, bandY };
