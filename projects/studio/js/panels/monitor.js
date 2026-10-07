// The program monitor: the frame under the playhead (9:16), transport buttons, Full / 1/2 / 1/4 quality (G25),
// safe zones (G40). With the Selection tool, drag an overlay on the picture to move it; with Type, click to add text.
import { S, emit, subscribe, selectOnly } from "../store.js";
import { el, clear, icon } from "../util.js";
import { renderFrame, drawSafe, layersAt, transformOf, textMetrics } from "../compositor.js";
import { baseSize, clipById, clipEnd, fmtTC, seqEnd, FPS, W, H } from "../model/doc.js";
import { srcFrame, valueAt, setValue } from "../model/keyframes.js";
import { VideoPool } from "../media/videopool.js";
import { lib } from "../media/library.js";
import { pb } from "../playback.js";
import * as history from "../history.js";
import { run } from "../actions.js";
import { openMenu } from "../components/menu.js";

const SIZES = { full: [1080, 1920], half: [540, 960], quarter: [270, 480] };
let stage, frame, program, guides, pctx, gctx, pool, tcEl, durEl, playBtn, qBtn, safeBtn;
let drawMs = [];
let pendingDraw = false;

export function mountMonitor(host) {
  clear(host);
  program = el("canvas", { class: "mon-program" });
  guides = el("canvas", { class: "mon-guides" });
  const poolHost = el("div", { class: "pool-host", "aria-hidden": "true" });
  frame = el("div", { class: "mon-frame" }, program, guides);
  stage = el("div", { class: "mon-stage" }, frame, poolHost);
  tcEl = el("span", { class: "mon-tc num" }, "0:00:00");
  durEl = el("span", { class: "mon-dur num muted" }, "");
  playBtn = el("button", { class: "icon-btn big", title: "Play / pause (Space)", onclick: () => run("play") }, icon("play_arrow"));
  qBtn = el("button", { class: "chip small", title: "Playback quality", onclick: (e) => openMenu(e.currentTarget, [
    { label: "Full", checked: () => S.quality === "full", run: () => run("quality.full") },
    { label: "1/2", checked: () => S.quality === "half", run: () => run("quality.half") },
    { label: "1/4", checked: () => S.quality === "quarter", run: () => run("quality.quarter") }]) }, "1/2");
  safeBtn = el("button", { class: "icon-btn", title: "Safe zones: what TikTok, Reels and Shorts cover", onclick: () => run("safe") }, icon("crop_free"));
  const bar = el("div", { class: "mon-bar" },
    el("div", { class: "mon-time" }, tcEl, durEl),
    el("div", { class: "mon-transport" },
      el("button", { class: "icon-btn", title: "Go to start (Home)", onclick: () => run("home") }, icon("first_page")),
      el("button", { class: "icon-btn", title: "Previous edit (Up)", onclick: () => run("prevEdit") }, icon("skip_previous")),
      el("button", { class: "icon-btn", title: "Back one frame (Left)", onclick: () => run("stepBack") }, icon("chevron_left")),
      playBtn,
      el("button", { class: "icon-btn", title: "Forward one frame (Right)", onclick: () => run("stepFwd") }, icon("chevron_right")),
      el("button", { class: "icon-btn", title: "Next edit (Down)", onclick: () => run("nextEdit") }, icon("skip_next")),
      el("button", { class: "icon-btn", title: "Go to end (End)", onclick: () => run("end") }, icon("last_page"))),
    el("div", { class: "mon-opts" }, qBtn, safeBtn));
  host.append(el("div", { class: "panel-head" }, el("span", { class: "panel-title" }, "Program"), el("span", { class: "grow" }), el("span", { class: "muted small", id: "mon-note" }, "")), stage, bar);
  pctx = program.getContext("2d", { alpha: false });
  gctx = guides.getContext("2d");
  pool = new VideoPool(poolHost, () => request());
  new ResizeObserver(fit).observe(stage);
  setQuality();
  guides.addEventListener("pointerdown", onDown);
  guides.addEventListener("dblclick", onDbl);
  subscribe("playhead", () => { if (S.playing) draw(); else request(); });
  subscribe("doc", request);
  subscribe("sel", request);
  subscribe("view", () => { setQuality(); request(); });
  // the file the monitor plays (proxy or original) stays the same through a play; a quality drop switches it at the
  // next pause, since a new file mid-play means a moment with nothing to draw
  subscribe("play", () => { S.playQuality = S.playing ? S.quality : null; playBtn.firstChild.textContent = S.playing ? "pause" : "play_arrow"; if (!S.playing) request(); });
  lib.onLoaded(request);
  document.fonts && document.fonts.ready.then(request);
  request();
}

function setQuality() {
  const [w, h] = SIZES[S.quality] || SIZES.half;
  if (program.width !== w) {
    // a canvas clears when resized: carry the picture over, so a quality change (or the drop while playing) never
    // flashes black
    let old = null;
    if (hasPicture) { old = el("canvas", { width: program.width, height: program.height }); old.getContext("2d").drawImage(program, 0, 0); }
    program.width = w; program.height = h; guides.width = w; guides.height = h;
    if (old) pctx.drawImage(old, 0, 0, w, h);
  }
  qBtn.textContent = { full: "Full", half: "1/2", quarter: "1/4" }[S.quality];
  safeBtn.classList.toggle("is-on", S.safe);
}

function fit() {
  const r = stage.getBoundingClientRect();
  const h = Math.max(50, r.height - 16), w = Math.max(30, r.width - 16);
  let fh = h, fw = (h * 9) / 16;
  if (fw > w) { fw = w; fh = (w * 16) / 9; }
  frame.style.width = fw + "px";
  frame.style.height = fh + "px";
}

function request() {
  if (pendingDraw) return;
  pendingDraw = true;
  requestAnimationFrame(() => { pendingDraw = false; draw(); });
}

function getVideo(clip, mediaTime) {
  const url = lib.videoUrl(clip.asset);
  if (!url) return null;
  const playing = S.playing && pb.rate() === 1;
  return pool.picture(pool.sync(clip.id, url, mediaTime, playing));   // the video, or its last picture while it seeks
}

// A clip whose video has nothing to show at all yet (a new element at a cut, a file still opening): the whole last
// frame holds for a moment instead of flashing black (2026-09-30, Jonathan: "on playback, sometimes the screen goes
// black"). A video that never comes (a missing file) stops being waited for after HOLD_MS.
export const HOLD_MS = 1500;
let hasPicture = false, heldSince = 0, pictureDoc = null;

export function draw() {
  const t0 = performance.now();
  const doc = S.doc;
  const f = Math.max(0, Math.floor(S.playhead + 1e-6));
  pool.beginFrame();
  if (!doc || doc.id !== pictureDoc) { hasPicture = false; pictureDoc = doc ? doc.id : null; }
  const got = new Map();
  const video = (clip, t) => { if (!got.has(clip.id)) got.set(clip.id, getVideo(clip, t)); return got.get(clip.id); };
  let waiting = false;
  if (doc) {
    for (const { clip } of layersAt(doc, f)) {
      if (clip.type === "video" && !video(clip, (srcFrame(clip, f) + 0.5) / FPS)) waiting = true;
    }
    // pre-seek clips that start soon so the cut lands on time: 1.5 s ahead, more in a file slow to seek (up to 4 s)
    for (const c of doc.clips) {
      if (c.type !== "video" || c.on === false || c.start <= f) continue;
      const url = lib.videoUrl(c.asset);
      if (!url) continue;
      const lead = Math.min(4, Math.max(1.5, 0.5 + 2 * pool.seekTime(url)));
      if (c.start <= f + Math.round(lead * FPS)) pool.prepare(c.id, url, (c.in + 0.5) / FPS);
    }
  }
  const now = performance.now();
  if (waiting && hasPicture) {
    if (!heldSince) heldSince = now;
    if (now - heldSince < HOLD_MS) {
      pool.endFrame();
      drawGuides(f);
      tcEl.textContent = fmtTC(f);
      if (!S.playing) setTimeout(request, 50);    // paused: look again shortly (seeked also redraws)
      return;
    }
    // held long enough: draw what there is, and keep drawing (captions, text) until the video comes
  } else heldSince = 0;
  renderFrame(pctx, doc, f, video);
  if (!waiting) hasPicture = true;
  pool.endFrame();
  drawGuides(f);
  tcEl.textContent = fmtTC(f);
  durEl.textContent = doc ? " / " + fmtTC(seqEnd(doc)) : "";
  const ms = performance.now() - t0;
  drawMs.push(ms); if (drawMs.length > 60) drawMs.shift();
  if (S.playing && drawMs.length === 60 && S.quality !== "quarter") {
    const avg = drawMs.reduce((a, b) => a + b, 0) / drawMs.length;
    if (avg > 12) {
      S.quality = S.quality === "full" ? "half" : "quarter";
      drawMs = [];
      const note = document.getElementById("mon-note");
      if (note) note.textContent = "Quality lowered to keep playback smooth";
      setQuality();
    }
  }
}

function corners(clip, f) {
  const tf = transformOf(clip, f);
  const sz = baseSize(clip, lib, textMetrics);
  const s = tf.s / 100, a = (tf.r * Math.PI) / 180, cos = Math.cos(a), sin = Math.sin(a);
  return [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sy]) => {
    const x = (sx * sz.w) / 2 * s, y = (sy * sz.h) / 2 * s;
    return [tf.x + x * cos - y * sin, tf.y + x * sin + y * cos];
  });
}

function drawGuides(f) {
  const k = guides.width / W;
  gctx.setTransform(1, 0, 0, 1, 0, 0);
  gctx.clearRect(0, 0, guides.width, guides.height);
  if (S.safe) drawSafe(gctx);
  if (!S.doc || S.playing) return;
  for (const id of S.sel) {
    const c = clipById(S.doc, id);
    if (!c || c.type === "audio" || !(c.start <= f && f < clipEnd(c))) continue;
    const pts = corners(c, f);
    gctx.setTransform(k, 0, 0, k, 0, 0);
    gctx.strokeStyle = "#A8C7FA"; gctx.lineWidth = 3 / Math.max(k, 0.25) * 0.5;
    gctx.beginPath(); pts.forEach(([x, y], i) => (i ? gctx.lineTo(x, y) : gctx.moveTo(x, y))); gctx.closePath(); gctx.stroke();
    const tf = transformOf(c, f);
    gctx.fillStyle = "#A8C7FA";
    gctx.beginPath(); gctx.arc(tf.x, tf.y, 10, 0, Math.PI * 2); gctx.fill();
  }
}

function toFrame(e) {
  const r = guides.getBoundingClientRect();
  return { x: ((e.clientX - r.left) / r.width) * W, y: ((e.clientY - r.top) / r.height) * H };
}

function inside(pt, poly) {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i, i += 1) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > pt.y) !== (yj > pt.y) && pt.x < ((xj - xi) * (pt.y - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}

export function clipAtPoint(pt, f) {
  const layers = layersAt(S.doc, f).map((l) => l.clip).reverse();
  return layers.find((c) => inside(pt, corners(c, f))) || null;
}

function onDown(e) {
  if (!S.doc || e.button !== 0) return;
  const f = Math.floor(S.playhead);
  const pt = toFrame(e);
  if (S.tool === "text") {
    run("newText", { f, track: "V2" });
    const id = [...S.sel][0];
    if (id) history.commit("Move", (d) => { const c = clipById(d, id); if (c) { c.fx.posX = { v: Math.round(pt.x) }; c.fx.posY = { v: Math.round(pt.y) }; } });
    return;
  }
  const hit = clipAtPoint(pt, f);
  if (!hit) { S.sel = new Set(); emit("sel"); return; }
  if (!S.sel.has(hit.id)) selectOnly([hit.id]);
  if (pb.rate()) pb.pause();
  const t = srcFrame(hit, f);
  const x0 = valueAt(hit, "posX", t), y0 = valueAt(hit, "posY", t);
  try { guides.setPointerCapture(e.pointerId); } catch (err) { /* synthetic */ }
  let started = false;
  const move = (ev) => {
    const p = toFrame(ev);
    if (!started && Math.hypot(p.x - pt.x, p.y - pt.y) < 4) return;
    if (!started) history.beginDrag("Move");
    started = true;
    let nx = x0 + (p.x - pt.x), ny = y0 + (p.y - pt.y);
    if (ev.shiftKey) { if (Math.abs(p.x - pt.x) > Math.abs(p.y - pt.y)) ny = y0; else nx = x0; }
    history.dragTo((d) => { const c = clipById(d, hit.id); setValue(c, "posX", t, Math.round(nx)); setValue(c, "posY", t, Math.round(ny)); return { ok: true }; });
  };
  const up = () => {
    guides.removeEventListener("pointermove", move);
    guides.removeEventListener("pointerup", up);
    if (started) history.endDrag();
  };
  guides.addEventListener("pointermove", move);
  guides.addEventListener("pointerup", up);
}

function onDbl(e) {
  if (!S.doc) return;
  const hit = clipAtPoint(toFrame(e), Math.floor(S.playhead));
  if (hit && hit.type === "text") { selectOnly([hit.id]); emit("focusText"); }
}

export function monitorApi() { return { draw, pool: () => pool, canvas: () => program, clipAtPoint }; }
