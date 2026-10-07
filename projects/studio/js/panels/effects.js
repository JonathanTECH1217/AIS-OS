// Effect Controls (G14, G15): the selected clip's settings at the playhead. Each keyframeable setting has a
// stopwatch (animate on/off), previous / add-remove / next keyframe buttons, a draggable number, and a lane of
// diamonds across the clip with the playhead. Right-click a diamond for Linear / Ease In / Ease Out / Hold.
import { S, subscribe, emit } from "../store.js";
import { el, clear, icon } from "../util.js";
import { clipById, clipEnd, clipLen, FPS, fmtTC } from "../model/doc.js";
import * as kf from "../model/keyframes.js";
import { numField } from "../components/numfield.js";
import { openMenu } from "../components/menu.js";
import * as history from "../history.js";
import * as ops from "../model/ops.js";
import { pb } from "../playback.js";
import { kfCommit } from "../actions.js";
import { lib } from "../media/library.js";

let host, body, fields = [], lanes = [];

export function mountEffects(h) {
  host = h;
  body = el("div", { class: "fx-body" });
  clear(host);
  host.append(body);
  subscribe("sel", render);
  subscribe("doc", () => { if (history.dragging() || busy()) update(); else render(); });
  subscribe("playhead", update);
  subscribe("focusText", () => { render(); const ta = body.querySelector("textarea"); if (ta) { ta.focus(); ta.select(); } });
  render();
}

// a field is being dragged or typed in: rebuilding the panel now would pull it out from under the pointer
function busy() {
  if (body.querySelector(".num-field.is-drag, .num-input")) return true;
  const a = document.activeElement;
  return !!(a && body.contains(a) && /^(TEXTAREA|INPUT|SELECT)$/.test(a.tagName));
}

function current() {
  if (!S.doc) return null;
  const ids = [...S.sel];
  const cs = ids.map((id) => clipById(S.doc, id)).filter(Boolean);
  return cs.find((c) => c.type !== "audio") || cs[0] || null;
}

function tNow(c) { return kf.srcFrame(c, Math.round(S.playhead)); }
function inRange(c) { const f = Math.round(S.playhead); return c.start <= f && f <= clipEnd(c); }

function propRow(c, name, label, { step = 1, digits = 1, suffix = "", min, max } = {}) {
  const animated = kf.isAnimated(c, name);
  const t = tNow(c);
  const onKey = animated && (kf.keysOf(c, name) || []).some((k) => k.t === Math.round(t));
  const nf = numField({ value: kf.valueAt(c, name, t), step, digits, suffix, min, max, title: label,
    onChange: (v, final) => kfCommit(label, c.id, (cc) => kf.setValue(cc, name, tNow(cc), v), final ? null : `fx:${c.id}:${name}`) });
  fields.push({ nf, id: c.id, name });
  const watch = el("button", { class: "fx-watch" + (animated ? " is-on" : ""), type: "button", title: animated ? "Stop animating (drops the keyframes)" : "Animate: add a keyframe at the playhead",
    onclick: () => kfCommit(animated ? "Stop Animating" : "Animate", c.id, (cc) => kf.toggleAnimate(cc, name, tNow(cc))) }, icon("timer"));
  const prev = el("button", { class: "fx-nav", type: "button", title: "Previous keyframe", disabled: !animated || null,
    onclick: () => { const k = kf.nextKey(c, name, tNow(c), -1); if (k !== null) pb.seek(c.start + (k - c.in)); } }, icon("keyboard_arrow_left"));
  const add = el("button", { class: "fx-diamond" + (onKey ? " is-on" : ""), type: "button", title: onKey ? "Remove keyframe" : "Add keyframe", disabled: !animated || !inRange(c) || null,
    onclick: () => kfCommit(onKey ? "Delete Keyframe" : "Add Keyframe", c.id, (cc) => (onKey ? kf.removeKey(cc, name, Math.round(tNow(cc))) : kf.addKey(cc, name, tNow(cc)))) }, icon("diamond"));
  const next = el("button", { class: "fx-nav", type: "button", title: "Next keyframe", disabled: !animated || null,
    onclick: () => { const k = kf.nextKey(c, name, tNow(c), 1); if (k !== null) pb.seek(c.start + (k - c.in)); } }, icon("keyboard_arrow_right"));
  const lane = el("canvas", { class: "fx-lane", height: "22" });
  lanes.push({ lane, id: c.id, name });
  lane.addEventListener("pointerdown", (e) => laneDown(e, c.id, name, lane));
  lane.addEventListener("contextmenu", (e) => laneMenu(e, c.id, name, lane));
  return el("div", { class: "fx-row" }, watch, el("span", { class: "fx-label" }, label), el("span", { class: "fx-keys" }, prev, add, next), nf, lane);
}

function laneGeom(c, lane) { const w = lane.clientWidth || 120; return { w, f2x: (t) => ((t - c.in) / Math.max(1, clipLen(c))) * w, x2t: (x) => c.in + (x / w) * clipLen(c) }; }

function drawLane(entry) {
  const c = S.doc && clipById(S.doc, entry.id);
  const cv = entry.lane;
  if (!c) return;
  const dpr = window.devicePixelRatio || 1;
  const w = cv.clientWidth || 120, h = 22;
  if (cv.width !== Math.round(w * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
  const g = cv.getContext("2d");
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, w, h);
  g.fillStyle = "rgba(255,255,255,.06)"; g.fillRect(0, 0, w, h);
  const { f2x } = laneGeom(c, cv);
  for (const k of kf.keysOf(c, entry.name) || []) {
    const x = f2x(k.t);
    g.fillStyle = k.e === "hold" ? "#f28b82" : k.e && k.e !== "linear" ? "#81c995" : "#fdd663";
    g.beginPath(); g.moveTo(x, 4); g.lineTo(x + 6, 11); g.lineTo(x, 18); g.lineTo(x - 6, 11); g.closePath(); g.fill();
  }
  const px = f2x(tNow(c));
  g.fillStyle = "#a8c7fa"; g.fillRect(px - 0.5, 0, 1.5, h);
}

function keyAt(c, name, lane, x) {
  const { f2x } = laneGeom(c, lane);
  return (kf.keysOf(c, name) || []).find((k) => Math.abs(f2x(k.t) - x) <= 6) || null;
}

function laneDown(e, id, name, lane) {
  const c = clipById(S.doc, id);
  const r = lane.getBoundingClientRect();
  const x = e.clientX - r.left;
  const k = keyAt(c, name, lane, x);
  const { x2t } = laneGeom(c, lane);
  if (!k) { pb.seek(c.start + (Math.round(x2t(x)) - c.in)); return; }
  try { lane.setPointerCapture(e.pointerId); } catch (err) { /* synthetic */ }
  const t0 = k.t;
  let started = false;
  const move = (ev) => {
    const nx = ev.clientX - r.left;
    if (!started && Math.abs(nx - x) < 3) return;
    if (!started) history.beginDrag("Move Keyframe");
    started = true;
    const t1 = Math.max(c.in, Math.min(c.out, Math.round(x2t(nx))));
    history.dragTo((d) => { kf.moveKey(clipById(d, id), name, t0, t1); return { ok: true }; });
  };
  const up = () => { lane.removeEventListener("pointermove", move); lane.removeEventListener("pointerup", up); if (started) history.endDrag(); else pb.seek(c.start + (t0 - c.in)); };
  lane.addEventListener("pointermove", move);
  lane.addEventListener("pointerup", up);
}

function laneMenu(e, id, name, lane) {
  e.preventDefault();
  const c = clipById(S.doc, id);
  const r = lane.getBoundingClientRect();
  const k = keyAt(c, name, lane, e.clientX - r.left);
  if (!k) return;
  openMenu({ x: e.clientX, y: e.clientY }, [...kf.EASES.map(([eid, label]) => ({ label, checked: (k.e || "linear") === eid,
    run: () => kfCommit("Keyframe Easing", id, (cc) => kf.setEase(cc, name, k.t, eid)) })), { sep: true },
  { label: "Delete keyframe", run: () => kfCommit("Delete Keyframe", id, (cc) => kf.removeKey(cc, name, k.t)) }]);
}

function section(title, ...rows) { return el("div", { class: "fx-sec" }, el("div", { class: "fx-sec-title" }, title), ...rows); }

function colorInput(value, onChange) {
  const i = el("input", { type: "color", value: value || "#ffffff", class: "fx-color" });
  i.addEventListener("input", () => onChange(i.value, false));
  i.addEventListener("change", () => onChange(i.value, true));
  return i;
}

function fieldRow(label, node) { return el("div", { class: "fx-row plain" }, el("span", { class: "fx-label wide" }, label), node); }

export function render() {
  if (!body) return;
  clear(body);
  fields = []; lanes = [];
  if (!S.doc) { body.append(el("div", { class: "empty" }, "Open a short to edit clip settings.")); return; }
  if (S.selTransition) {
    const t = S.doc.transitions.find((x) => x.id === S.selTransition);
    if (t) {
      body.append(section("Transition",
        fieldRow("Kind", el("select", { class: "fx-select", onchange: (e) => history.commit("Transition", (d) => { d.transitions.find((x) => x.id === t.id).kind = e.target.value; }) },
          el("option", { value: "dissolve", selected: t.kind === "dissolve" || null }, "Cross dissolve"), el("option", { value: "dip", selected: t.kind === "dip" || null }, "Dip to black"))),
        fieldRow("Duration (frames)", numField({ value: t.dur, step: 1, digits: 0, min: 2, max: 120,
          onChange: (v, final) => history.commit("Transition Duration", (d) => { const x = d.transitions.find((y) => y.id === t.id); x.dur = Math.round(v); }, { key: final ? null : "tdur" }) }))));
      return;
    }
  }
  const c = current();
  if (!c) { body.append(el("div", { class: "empty" }, "Select a clip to see its settings. Keyframes: click the stopwatch, move the playhead, change a value.")); return; }
  const a = c.asset && lib.asset(c.asset);
  const name = c.type === "text" ? "Text" : c.type === "shape" ? "Shape" : (a && a.name) || c.type;
  body.append(el("div", { class: "fx-head" }, el("span", { class: "strong" }, name), el("span", { class: "muted small" }, `${c.track} · ${fmtTC(clipLen(c))}`)));
  if (c.type !== "audio") {
    body.append(section("Motion",
      propRow(c, "posX", "Position X", { step: 1, digits: 0 }), propRow(c, "posY", "Position Y", { step: 1, digits: 0 }),
      propRow(c, "scale", "Scale", { step: 0.5, digits: 1, suffix: "%", min: 0 }), propRow(c, "rot", "Rotation", { step: 0.5, digits: 1, suffix: "°" })),
      section("Opacity", propRow(c, "opacity", "Opacity", { step: 0.5, digits: 1, suffix: "%", min: 0, max: 100 })));
  }
  if (c.type === "text") {
    const tx = c.text || {};
    const ta = el("textarea", { class: "fx-text", rows: "2" }, tx.str || "");
    ta.addEventListener("input", () => history.commit("Edit Text", (d) => { clipById(d, c.id).text.str = ta.value; }, { key: "text:" + c.id }));
    body.append(section("Text", ta,
      fieldRow("Size", numField({ value: tx.size || 110, step: 1, digits: 0, min: 8, max: 600, onChange: (v, fin) => history.commit("Text Size", (d) => { clipById(d, c.id).text.size = Math.round(v); }, { key: fin ? null : "tsize" }) })),
      fieldRow("Color", colorInput(tx.color, (v, fin) => history.commit("Text Color", (d) => { clipById(d, c.id).text.color = v; }, { key: fin ? null : "tcolor" }))),
      fieldRow("Outline", colorInput(tx.stroke || "#000000", (v, fin) => history.commit("Outline Color", (d) => { clipById(d, c.id).text.stroke = v; }, { key: fin ? null : "tstroke" }))),
      fieldRow("Outline width", numField({ value: tx.strokeW || 0, step: 1, digits: 0, min: 0, max: 40, onChange: (v, fin) => history.commit("Outline Width", (d) => { clipById(d, c.id).text.strokeW = Math.round(v); }, { key: fin ? null : "tsw" }) })),
      // a box behind the words (the Trailer headline: black on white)
      fieldRow("Box", el("span", { class: "fx-inline" },
        el("label", { class: "switch" }, el("input", { type: "checkbox", class: "fx-box-on", checked: tx.bg ? true : null,
          onchange: (e) => history.commit("Text Box", (d) => { const t = clipById(d, c.id).text; if (e.target.checked) t.bg = t.bg || "#FFFFFF"; else delete t.bg; }) }), el("span", {}, "")),
        tx.bg ? colorInput(tx.bg, (v, fin) => history.commit("Box Color", (d) => { clipById(d, c.id).text.bg = v; }, { key: fin ? null : "tbg" })) : null))));
  }
  if (c.type === "shape") {
    const sh = c.shape || {};
    const set = (k, label, conv = (v) => v) => (v, fin) => history.commit(label, (d) => { clipById(d, c.id).shape[k] = conv(v); }, { key: fin ? null : "sh" + k });
    body.append(section("Shape",
      fieldRow("Kind", el("select", { class: "fx-select", onchange: (e) => set("kind", "Shape Kind")(e.target.value, true) },
        ...[["rect", "Box"], ["ellipse", "Circle"], ["arrow", "Arrow"]].map(([v, l]) => el("option", { value: v, selected: sh.kind === v || null }, l)))),
      fieldRow("Width", numField({ value: sh.w, step: 2, digits: 0, min: 2, max: 3000, onChange: set("w", "Shape Width", Math.round) })),
      fieldRow("Height", numField({ value: sh.h, step: 2, digits: 0, min: 2, max: 3000, onChange: set("h", "Shape Height", Math.round) })),
      fieldRow("Fill", colorInput(sh.fill || "#FFD400", set("fill", "Shape Fill"))),
      fieldRow("Corner radius", numField({ value: sh.radius || 0, step: 1, digits: 0, min: 0, max: 500, onChange: set("radius", "Corner Radius", Math.round) }))));
  }
  if (c.type === "audio") {
    body.append(section("Volume", propRow(c, "volume", "Level", { step: 0.1, digits: 1, suffix: " dB", min: -60, max: 24 }),
      fieldRow("Fade in (frames)", numField({ value: c.fadeIn || 0, step: 1, digits: 0, min: 0, max: clipLen(c), onChange: (v, fin) => history.commit("Fade", (d) => ops.setFade(d, c.id, "fadeIn", v), { key: fin ? null : "fi" }) })),
      fieldRow("Fade out (frames)", numField({ value: c.fadeOut || 0, step: 1, digits: 0, min: 0, max: clipLen(c), onChange: (v, fin) => history.commit("Fade", (d) => ops.setFade(d, c.id, "fadeOut", v), { key: fin ? null : "fo" }) }))));
  }
  requestAnimationFrame(() => lanes.forEach(drawLane));
}

function update() {
  if (!S.doc) return;
  for (const f of fields) {
    const c = clipById(S.doc, f.id);
    if (c) f.nf.update(kf.valueAt(c, f.name, tNow(c)));
  }
  lanes.forEach(drawLane);
}
