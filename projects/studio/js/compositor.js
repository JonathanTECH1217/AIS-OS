// The monitor's picture: every visible layer at timeline frame f, bottom video track first, captions on top.
// Transform per layer: move to (posX, posY), rotate (degrees, clockwise), scale (percent), anchored at the center,
// opacity times any transition. scripts/studio_render.py composes exports with the same rules.
import { S } from "./store.js";
import { baseSize, clipEnd, clipsOn, drawOrder, FPS, W, H } from "./model/doc.js";
import { srcFrame, valueAt } from "./model/keyframes.js";
import { activeEvent, colorsFor, popScale } from "./model/captions.js";
import { transitionWindow } from "./model/ops.js";
import { assEmPx, baselineFromCenter, metrics } from "./fontmetrics.js";
import { lib } from "./media/library.js";

const TEXT_FONT = '"Montserrat Black", "Google Sans", Arial, sans-serif';
let measureCtx = null;

// Titles are laid out without kerning: the exporter's Pillow has no shaping engine here (no raqm) and Montserrat's
// kerning lives in GPOS, so a kerned preview would run a few px narrower than the export. Captions keep kerning
// (libass shapes them, and the page measures them kerned).
// A text clip can sit on a box (text.bg, the Trailer headline: black on white, 2026-09-30): pad px around the
// lines, radius px corners. studio_render.py text_image draws the same box.
export const BOX_PAD = 32, BOX_RADIUS = 20;
function boxPad(t) { return t.bg ? (t.pad !== undefined ? t.pad : BOX_PAD) : 0; }

export function textMetrics(clip) {
  if (!measureCtx) measureCtx = document.createElement("canvas").getContext("2d");
  const t = clip.text || {};
  measureCtx.fontKerning = "none";
  measureCtx.font = `${t.size || 110}px ${TEXT_FONT}`;
  const lines = String(t.str || "").split("\n");
  const w = Math.max(20, ...lines.map((l) => measureCtx.measureText(l).width)) + (t.strokeW || 0) * 2 + boxPad(t) * 2;
  const h = (t.size || 110) * 1.2 * lines.length + (t.strokeW || 0) * 2 + boxPad(t) * 2;
  return { w, h };
}

export function measureCaption(size) {
  if (!measureCtx) measureCtx = document.createElement("canvas").getContext("2d");
  measureCtx.fontKerning = "normal";
  measureCtx.font = `${assEmPx(size)}px "Montserrat Black"`;
  return (s) => measureCtx.measureText(s).width;
}

// Layers on screen at frame f: [{clip, alpha}], bottom first. Transitions add the outgoing or incoming clip.
export function layersAt(doc, f) {
  const out = [];
  for (const tr of drawOrder(doc)) {
    if (tr.hide) continue;
    const cs = clipsOn(doc, tr.id);
    const items = new Map();
    for (const c of cs) if (c.start <= f && f < clipEnd(c) && c.on !== false) items.set(c.id, { clip: c, alpha: 1 });
    for (const t of doc.transitions || []) {
      if (t.track !== tr.id) continue;
      const w = transitionWindow(doc, t);
      if (f < w.s || f >= w.e) continue;
      const p = (f - w.s) / (w.e - w.s);
      const A = t.a && cs.find((c) => c.id === t.a), B = t.b && cs.find((c) => c.id === t.b);
      if (t.kind === "dissolve" && A && B) {
        items.set(A.id, { clip: A, alpha: 1 - p });
        items.set(B.id, { clip: B, alpha: p });
      } else if (A && B) {
        if (p < 0.5) { items.set(A.id, { clip: A, alpha: 1 - p * 2 }); items.delete(B.id); }
        else { items.set(B.id, { clip: B, alpha: p * 2 - 1 }); items.delete(A.id); }
      } else if (A) items.set(A.id, { clip: A, alpha: 1 - p });
      else if (B) items.set(B.id, { clip: B, alpha: p });
    }
    // outgoing clip first so the incoming one draws over it
    out.push(...[...items.values()].sort((x, y) => x.clip.start - y.clip.start));
  }
  return out;
}

export function transformOf(clip, f) {
  const t = srcFrame(clip, f);
  return { x: valueAt(clip, "posX", t), y: valueAt(clip, "posY", t), s: valueAt(clip, "scale", t),
    r: valueAt(clip, "rot", t), o: valueAt(clip, "opacity", t) };
}

function drawShape(ctx, sh, w, h) {
  ctx.beginPath();
  if (sh.kind === "ellipse") ctx.ellipse(0, 0, w / 2, h / 2, 0, 0, Math.PI * 2);
  else if (sh.kind === "arrow") {
    const hw = w / 2, hh = h / 2, head = Math.min(w * 0.35, h * 1.2), shaft = h * 0.36;
    ctx.moveTo(-hw, -shaft / 2); ctx.lineTo(hw - head, -shaft / 2); ctx.lineTo(hw - head, -hh); ctx.lineTo(hw, 0);
    ctx.lineTo(hw - head, hh); ctx.lineTo(hw - head, shaft / 2); ctx.lineTo(-hw, shaft / 2); ctx.closePath();
  } else ctx.roundRect(-w / 2, -h / 2, w, h, Math.min(sh.radius || 0, w / 2, h / 2));
  if (sh.fill) { ctx.fillStyle = sh.fill; ctx.fill(); }
  if (sh.stroke && sh.strokeW) { ctx.lineWidth = sh.strokeW; ctx.strokeStyle = sh.stroke; ctx.stroke(); }
}

// Text titles: each line's baseline sits (winAscent - winDescent) / 2 em below the line's center, the same rule
// studio_render.py text_image uses, so title and export line up (browsers disagree on what "middle" means).
export function textBaselineOffset(size) { const m = metrics(); return ((m.asc - m.desc) / (2 * m.upm)) * size; }

function drawText(ctx, t) {
  const size = t.size || 110;
  ctx.font = `${size}px ${TEXT_FONT}`;
  ctx.fontKerning = "none";
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.lineJoin = "round";
  const lines = String(t.str || "").split("\n");
  const lh = size * 1.2;
  const off = textBaselineOffset(size);
  if (t.bg) {
    const pad = boxPad(t), sw = t.strokeW || 0;
    const w = Math.max(20, ...lines.map((l) => ctx.measureText(l).width)) + sw * 2 + pad * 2;
    const h = lh * lines.length + sw * 2 + pad * 2;
    ctx.fillStyle = t.bg;
    ctx.beginPath();
    ctx.roundRect(-w / 2, -h / 2, w, h, Math.min(t.radius !== undefined ? t.radius : BOX_RADIUS, w / 2, h / 2));
    ctx.fill();
  }
  lines.forEach((ln, i) => {
    const y = (i - (lines.length - 1) / 2) * lh + off;
    if (t.stroke && t.strokeW) { ctx.lineWidth = t.strokeW * 2; ctx.strokeStyle = t.stroke; ctx.strokeText(ln, 0, y); }
    ctx.fillStyle = t.color || "#FFFFFF";
    ctx.fillText(ln, 0, y);
  });
}

export function drawCaptions(ctx, doc, f) {
  const cfg = doc.captions;
  if (!cfg || !cfg.on || !cfg.events) return;
  const ev = activeEvent(cfg.events, f);
  if (!ev) return;
  const em = assEmPx(cfg.size);
  const base = baselineFromCenter(cfg.size);
  ctx.font = `${em}px "Montserrat Black"`;
  ctx.fontKerning = "normal";
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.lineJoin = "round";
  const pal = S.config && S.config.captionColors;
  for (const w of ev.words) {
    const sc = popScale(w, f);
    const active = w.s <= f && f < w.e;
    const [text, word] = colorsFor(w.k, pal);
    ctx.save();
    ctx.translate(w.x, cfg.y);
    ctx.scale(sc, sc);
    ctx.lineWidth = (cfg.bord || 6) * 2;
    ctx.strokeStyle = "#000000";
    ctx.strokeText(w.w, 0, base);
    ctx.fillStyle = active ? word : text;
    ctx.fillText(w.w, 0, base);
    ctx.restore();
  }
}

// Draw frame f. getVideo(clip, mediaTime) returns a drawable <video> (or null while it loads).
export function renderFrame(ctx, doc, f, getVideo) {
  const k = ctx.canvas.width / W;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1;
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  if (!doc) return;
  for (const { clip, alpha } of layersAt(doc, f)) {
    const tf = transformOf(clip, f);
    const a = Math.max(0, Math.min(1, (tf.o / 100) * alpha));
    if (a <= 0) continue;
    const size = baseSize(clip, lib, textMetrics);
    ctx.setTransform(k, 0, 0, k, 0, 0);
    ctx.translate(tf.x, tf.y);
    if (tf.r) ctx.rotate((tf.r * Math.PI) / 180);
    ctx.scale(tf.s / 100, tf.s / 100);
    ctx.globalAlpha = a;
    if (clip.type === "video") {
      // aim at the middle of the frame: files keep millisecond timestamps, so f/30 can land on the frame before
      const v = getVideo(clip, (srcFrame(clip, f) + 0.5) / FPS);
      if (v) ctx.drawImage(v, -size.w / 2, -size.h / 2, size.w, size.h);
    } else if (clip.type === "image") {
      const bm = lib.bitmap(clip.asset);
      if (bm) ctx.drawImage(bm, -size.w / 2, -size.h / 2, size.w, size.h);
    } else if (clip.type === "text") drawText(ctx, clip.text || {});
    else if (clip.type === "shape") drawShape(ctx, clip.shape || {}, size.w, size.h);
  }
  ctx.globalAlpha = 1;
  ctx.setTransform(k, 0, 0, k, 0, 0);
  drawCaptions(ctx, doc, f);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
}

// Safe zones (G40): what TikTok, Reels and Shorts cover, combined. Drawn on the guides canvas, never exported.
export const SAFE = { top: 220, bottom: 480, right: 150, left: 60 };
export function drawSafe(ctx) {
  const k = ctx.canvas.width / W;
  ctx.save();
  ctx.setTransform(k, 0, 0, k, 0, 0);
  ctx.fillStyle = "rgba(242,139,130,.14)";
  ctx.fillRect(0, 0, W, SAFE.top);
  ctx.fillRect(0, H - SAFE.bottom, W, SAFE.bottom);
  ctx.fillRect(W - SAFE.right, SAFE.top, SAFE.right, H - SAFE.top - SAFE.bottom);
  ctx.fillRect(0, SAFE.top, SAFE.left, H - SAFE.top - SAFE.bottom);
  ctx.strokeStyle = "rgba(242,139,130,.8)";
  ctx.setLineDash([12, 10]);
  ctx.lineWidth = 3;
  ctx.strokeRect(SAFE.left, SAFE.top, W - SAFE.left - SAFE.right, H - SAFE.top - SAFE.bottom);
  ctx.restore();
}
