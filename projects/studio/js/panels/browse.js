// The calls view (2026-10-01, brainstorms/2026-10-01-clip-browser.md): clicking a recording turns the Media panel into
// its calls, ring to hang-up (B1, B3). While it's open the panel runs full height and widens (B13): the player on the
// left, the calls on the right. Only the playing call is loaded: one <video> on the preview copy for the whole recording
// (switching calls only moves it inside the same file, the address never changes per call), that call's words for its
// captions, and the list's titles. Leaving the recording empties the player, which frees its buffer.
import { S, emit, subscribe } from "../store.js";
import { el, clear, icon, fmtDur } from "../util.js";
import { api } from "../api.js";
import { lib } from "../media/library.js";
import { pb } from "../playback.js";
import { openShort } from "../actions.js";
import { toast } from "../components/modal.js";
import { FPS, normalize } from "../model/doc.js";
import { buildCaptionEvents } from "../model/captions.js";
import { measureCaption, drawCaptions } from "../compositor.js";

export const OUTCOME = { booked: "Booked", callback: "Callback", gatekeeper: "Gatekeeper", not_interested: "Not interested",
  voicemail: "Voicemail", no_answer: "No answer", other: "Other", between: "Between calls", not_a_call: "Not a call" };
const ORDER = ["booked", "callback", "gatekeeper", "not_interested", "voicemail", "no_answer", "other", "between", "not_a_call"];
const SPEEDS = [1, 1.5, 2];
const WATCH_AFTER = 3;        // seconds of play before a call counts as watched, so stepping through with Down marks nothing
const SEARCH_LEAD = 1.5;      // with a search on, a click plays from just before the first match
const STAGE_NAME = { remux: "Copy", peaks: "Waveform", proxy: "Preview copy", transcript: "Transcript", speakers: "Voices" };
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

let host = null, opts = {};
let root, stage, video, caps, emptyEl, bar, fillEl, rangeEl, headEl, marksEl, controls, playBtn, timeEl, speedBtn, marksTxt,
  clearBtn, makeBtn, nowEl, titleEl, searchEl, statusEl, tagsEl, listEl, footEl;
let st = null;                // the open recording (null when the Media panel shows the recordings)
const last = new Map();       // asset id -> {id, scroll}: opening the recording again comes back to that call
let rvfc = 0, searchTimer = 0, pendingSeek = null;

// When a recording was made: the server's `recorded` (from the date OBS writes into the file name, else the file's own
// time; studio_calls.recorded_at), or the name itself while the server is older (2026-10-01)
export function recordedDate(a) {
  const iso = a && a.recorded;
  const m = (iso && /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})/.exec(iso))
    || /(\d{4})-(\d{2})-(\d{2})[ _T](\d{2})[-.:](\d{2})[-.:](\d{2})/.exec((a && a.name) || "");
  return m ? new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6]) : null;
}

// a recording's title is the date it was recorded: "Mon Sep 28, 10:38 AM" (B15; Jonathan, 2026-10-01: "that should just
// be what the title of the video is"); the file name only if no date is known
export function recordingTitle(a) {
  const d = recordedDate(a);
  if (!d) return (a && a.name) || "";
  const h = d.getHours() % 12 || 12, ap = d.getHours() < 12 ? "AM" : "PM";
  return `${DAYS[d.getDay()]} ${MONTHS[d.getMonth()]} ${d.getDate()}, ${h}:${String(d.getMinutes()).padStart(2, "0")} ${ap}`;
}

export function fmtHours(sec) {
  const mins = Math.round((sec || 0) / 60), h = Math.floor(mins / 60), m = mins % 60;
  return h ? `${h} h ${String(m).padStart(2, "0")} m` : `${m} m`;
}

// "20 calls · 1 booked"
export function callsLine(a) {
  if (!a || !a.calls) return "";
  return `${a.calls.n} call${a.calls.n === 1 ? "" : "s"}` + (a.calls.booked ? ` · ${a.calls.booked} booked` : "");
}

const kindOf = (r) => (r.between ? "between" : r.outcome in OUTCOME ? r.outcome : "other");
const overlap = (a0, a1, b0, b1) => Math.max(0, Math.min(a1, b1) - Math.max(a0, b0));
const r3 = (x) => Math.round(x * 1000) / 1000;

export function isBrowsing() { return !!st; }

export function mountBrowse(panel, options = {}) {
  host = panel;
  opts = options;
  video = el("video", { class: "br-video", playsinline: true, preload: "metadata" });
  caps = el("canvas", { class: "br-caps" });
  emptyEl = el("div", { class: "br-empty", hidden: true });
  stage = el("div", { class: "br-stage" }, video, caps, emptyEl);
  fillEl = el("div", { class: "br-fill" });
  rangeEl = el("div", { class: "br-range", hidden: true });
  marksEl = el("div", { class: "br-marks-layer" });
  headEl = el("div", { class: "br-head-pos" });
  bar = el("div", { class: "br-bar", title: "Click or drag to move. A diamond is one of Claude's best bits: click it to mark it." },
    el("div", { class: "br-track" }), fillEl, rangeEl, headEl, marksEl);
  playBtn = el("button", { class: "icon-btn", type: "button", title: "Play / pause (Space)", onclick: () => togglePlay() }, icon("play_arrow"));
  timeEl = el("span", { class: "br-time num" }, "");
  speedBtn = el("button", { class: "chip small br-speed", type: "button", title: "Speed (voices keep their pitch)", onclick: () => cycleSpeed() }, speedLabel());
  marksTxt = el("span", { class: "br-marks num" }, "");
  clearBtn = el("button", { class: "icon-btn small", type: "button", title: "Clear the marks", hidden: true, onclick: () => clearMarks() }, icon("close"));
  makeBtn = el("button", { class: "btn small br-make", type: "button", title: "A short of the marked part (I and O), or of the whole call", onclick: () => makeShort() },
    icon("movie"), "Make short");
  controls = el("div", { class: "br-controls" }, playBtn, timeEl, speedBtn, el("span", { class: "grow" }), marksTxt, clearBtn, makeBtn);
  nowEl = el("div", { class: "br-now" }, "");
  const player = el("div", { class: "br-player" }, stage, bar, controls, nowEl);
  titleEl = el("span", { class: "br-title" }, "");
  searchEl = el("input", { class: "br-search", type: "search", placeholder: "Search what was said", spellcheck: "false" });
  statusEl = el("div", { class: "br-status" });
  tagsEl = el("div", { class: "br-tags" });
  listEl = el("div", { class: "br-list", role: "list" });
  footEl = el("div", { class: "br-foot" });
  const back = el("button", { class: "icon-btn", type: "button", title: "Back to the recordings", onclick: () => closeBrowse() }, icon("arrow_back"));
  const side = el("div", { class: "br-side" }, el("div", { class: "br-head" }, back, titleEl, searchEl), statusEl, tagsEl, listEl, footEl);
  root = el("div", { class: "browse", tabindex: "-1", hidden: true }, player, side);
  host.append(root);

  video.addEventListener("play", () => { if (S.playing) pb.pause(); playBtn.firstChild.textContent = "pause"; startLoop(); });
  video.addEventListener("pause", () => { playBtn.firstChild.textContent = "play_arrow"; stopLoop(); onTime(video.currentTime); });
  video.addEventListener("seeked", () => onTime(video.currentTime));
  video.addEventListener("loadedmetadata", () => {
    if (pendingSeek !== null) { video.currentTime = pendingSeek; pendingSeek = null; }
    fitCaps();
  });
  subscribe("play", () => { if (S.playing && !video.paused) video.pause(); });   // the short plays: the call stops
  subscribe("config", () => { if (st) onTime(video.currentTime); });               // a palette change repaints
  bindBar();
  searchEl.addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(runSearch, 250); });
  searchEl.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && searchEl.value) { e.stopPropagation(); searchEl.value = ""; runSearch(); }
    if (e.key === "Enter") { const r = visibleRows()[0]; if (r) select(r, { play: true }); }
  });
  new ResizeObserver(() => layoutPlayer()).observe(root);
}

// ------------------------------------------------------------------ open / leave

export async function openRecording(aid) {
  const a = lib.asset(aid);
  if (!a || !host) return;
  if (st && st.aid === aid) return;
  if (st) leave(false);
  st = { aid, view: null, nodes: new Map(), cur: null, inMark: null, outMark: null, filter: "", hits: null, showHidden: false,
    rev: a.callsRev || null, seq: 0, sseq: 0, capDoc: null, wordsKey: null, played: 0, lastTick: 0, watchedSent: new Set() };
  document.getElementById("app").classList.add("browsing");
  const list = host.querySelector(".bin-list");
  if (list) list.hidden = true;
  root.hidden = false;
  titleEl.textContent = recordingTitle(a);
  searchEl.value = "";
  clear(listEl); clear(tagsEl); clear(footEl);
  renderStatus();
  layoutPlayer();
  root.focus({ preventScroll: true });
  await refresh(true);
}

export function closeBrowse() { leave(true); }

function leave(redraw) {
  if (!st) return;
  if (st.cur) last.set(st.aid, { id: st.cur.id, scroll: listEl.scrollTop });
  stopLoop();
  clearTimeout(searchTimer);
  pendingSeek = null;
  video.pause();
  video.removeAttribute("src");       // drops the file's index and read-ahead (setting src="" would fetch the page)
  delete video.dataset.src;
  video.load();
  st = null;
  clearCaps();
  root.hidden = true;
  document.getElementById("app").classList.remove("browsing");
  const list = host.querySelector(".bin-list");
  if (list) list.hidden = false;
  if (redraw) emit("bin");
}

// the bin feed while a recording is open: patch in place, so playback, scroll, focus and the search survive
export function onBin() {
  if (!st) return;
  const a = lib.asset(st.aid);
  if (!a) { leave(true); return; }      // the recording went away
  titleEl.textContent = recordingTitle(a);
  renderStatus();
  markShorts();
  const rev = a.callsRev || null;
  if (rev !== st.rev) { st.rev = rev; refresh(false); }
}

async function refresh(first) {
  const aid = st.aid, seq = ++st.seq;
  let v;
  try { v = await api.get(`/api/asset/${aid}/calls`); }
  catch (e) { if (st && st.aid === aid) statusLine(e.message); return; }
  if (!st || st.aid !== aid || seq !== st.seq) return;
  st.view = v;
  buildRows();
  renderTags();
  applyFilter();
  renderStatus();
  if (st.hits) runSearch();
  if (first) {
    const back = last.get(aid);
    const r = (back && v.calls.find((x) => x.id === back.id)) || visibleRows()[0];
    if (r) select(r, { play: false });
    if (back) listEl.scrollTop = back.scroll;
  } else if (st.cur) {
    const prev = st.cur;
    const same = v.calls.find((x) => x.id === prev.id)
      || v.calls.slice().sort((x, y) => overlap(y.start, y.end, prev.start, prev.end) - overlap(x.start, x.end, prev.start, prev.end))[0];
    if (same) { st.cur = same; markCur(); drawBar(); }
  }
  if (!v.calls.length) showEmpty(noCallsText());
}

// ------------------------------------------------------------------ the list

function buildRows() {
  clear(listEl);
  st.nodes.clear();
  for (const r of st.view.calls) {
    const extra = el("span", { class: "br-extra" });
    // viral potential (2026-10-02, Jonathan: "I also miss the little summary and star rating"): a call with a best bit
    // shows its strongest bit's stars and, on a second line, why it would work as a short; the rest stay one line
    const top = st.view.bits.filter((b) => b.call === r.id).sort((a, b) => (b.strength || 0) - (a.strength || 0) || a.start - b.start)[0];
    const node = el("div", { class: "br-row" + (r.watched ? " watched" : "") + (r.hidden ? " is-hidden" : "") + (top ? " has-bit" : ""), role: "listitem",
      dataset: { id: r.id }, title: (r.summary ? r.summary + "\n" : "") + "Click to play. Drag onto the timeline.",
      onclick: () => select(r, { play: true }) },
      el("span", { class: "br-dot", title: "Not watched yet" }), el("span", { class: "br-at num" }, fmtDur(r.play[0])),
      el("span", { class: "br-name" }, r.label || "Untitled"),
      el("span", { class: "br-stars", title: top ? `Viral potential ${top.strength} of 5: "${top.title}"` : null }, top ? "★".repeat(Math.max(1, Math.min(5, top.strength || 1))) : ""),
      el("span", { class: "br-len num" }, fmtDur(r.play[1] - r.play[0])),
      el("span", { class: "br-tag t-" + kindOf(r) }, OUTCOME[kindOf(r)]), extra,
      top ? el("div", { class: "br-why", title: `${top.title}: ${top.reason || ""}` }, top.reason || top.title) : null);
    node.draggable = true;
    node.addEventListener("dragstart", (e) => {
      const [s, en] = st && st.cur && st.cur.id === r.id ? markedSpan() : r.play;
      e.dataTransfer.setData("application/x-studio", JSON.stringify({ kind: "moment", asset: st.aid, id: r.id, start: s, end: en }));
      e.dataTransfer.effectAllowed = "copy";
    });
    st.nodes.set(r.id, { r, node, extra });
    listEl.append(node);
  }
  markShorts();
  markCur();
}

function renderTags() {
  clear(tagsEl);
  const shown = st.view.calls.filter((r) => !r.hidden || st.showHidden);
  const n = {};
  for (const r of shown) n[kindOf(r)] = (n[kindOf(r)] || 0) + 1;
  const chip = (k, label, count) => el("button", { class: "chip small" + (st.filter === k ? " is-on" : ""), type: "button",
    onclick: () => { st.filter = st.filter === k || !k ? "" : k; renderTags(); applyFilter(); } }, label, el("span", { class: "muted num" }, String(count)));
  tagsEl.append(chip("", "All", shown.length));
  for (const k of ORDER) if (n[k]) tagsEl.append(chip(k, OUTCOME[k], n[k]));
}

function applyFilter() {
  for (const { r, node, extra } of st.nodes.values()) {
    const hit = st.hits ? st.hits[r.id] : null;
    const ok = (!r.hidden || st.showHidden || !!hit) && (!st.filter || kindOf(r) === st.filter) && (!st.hits || !!hit);
    node.hidden = !ok;
    extra.querySelector(".br-hits") && extra.querySelector(".br-hits").remove();
    if (hit) extra.prepend(el("span", { class: "br-hits num" }, `${hit.n} hit${hit.n === 1 ? "" : "s"}`));
  }
  clear(footEl);
  const hid = st.view ? st.view.hidden : 0;
  if (hid) footEl.append(el("button", { class: "link small", type: "button", onclick: () => { st.showHidden = !st.showHidden; renderTags(); applyFilter(); } },
    st.showHidden ? `Hide the ${hid} stretch${hid === 1 ? "" : "es"} that aren't calls` : `Show ${hid} hidden (not calls)`));
  if (st.hits && !Object.keys(st.hits).length) footEl.append(el("span", { class: "muted" }, "Nothing found."));
}

function visibleRows() {
  return st ? [...st.nodes.values()].filter((x) => !x.node.hidden).map((x) => x.r) : [];
}

// "Short" once a short was made from (most of) a row; worked out from the shorts list, so older shorts count too and a
// deleted short takes its tag with it
function markShorts() {
  if (!st) return;
  const shorts = ((S.bin && S.bin.shorts) || []).map((s) => s.moment).filter((m) => m && m.asset === st.aid && m.end > m.start);
  for (const { r, extra } of st.nodes.values()) {
    const has = shorts.some((m) => overlap(m.start, m.end, r.start, r.end) >= 0.5 * (m.end - m.start));
    const tag = extra.querySelector(".br-short");
    if (has && !tag) extra.append(el("span", { class: "br-short" }, "Short"));
    if (!has && tag) tag.remove();
  }
}

function markCur() {
  for (const { r, node } of st.nodes.values()) node.classList.toggle("is-cur", !!st.cur && r.id === st.cur.id);
}

async function runSearch() {
  if (!st) return;
  const q = searchEl.value.trim();
  const sseq = ++st.sseq;
  if (!q) { st.hits = null; applyFilter(); return; }
  try {
    const r = await api.get(`/api/asset/${st.aid}/calls/search?q=${encodeURIComponent(q)}`);
    if (!st || sseq !== st.sseq) return;        // a newer search is on its way
    st.hits = r.hits || {};
    applyFilter();
  } catch (e) { /* keep the list as it is */ }
}

// ------------------------------------------------------------------ status line

function statusLine(...parts) { clear(statusEl); statusEl.append(...parts); }

function noCallsText() {
  const a = lib.asset(st.aid) || {};
  const done = Object.values(a.stages || {}).every((s) => s.state === "done");
  return done ? "No calls yet. Find calls lists them." : "No calls yet. The recording is still being prepared.";
}

function renderStatus() {
  if (!st) return;
  const a = lib.asset(st.aid) || {};
  const stg = a.stages || {};
  const names = Object.keys(stg);
  const running = names.find((n) => stg[n].state === "running") || names.find((n) => stg[n].state !== "done" && stg[n].state !== "error");
  const job = S.bin && S.bin.moments && S.bin.moments[st.aid];
  const parts = [];
  if (running) {
    const p = Math.round((stg[running].progress || 0) * 100);
    parts.push(el("span", {}, `Preparing: ${STAGE_NAME[running] || running} ${p} %`), el("div", { class: "progress" }, el("b", { style: { width: p + "%" } })));
  }
  if (job && job.state === "running") parts.push(el("span", { class: "strong" }, "Finding calls… " + (job.msg || "")));
  else if (job && job.state === "error") parts.push(el("span", { class: "err" }, "Find calls failed: " + (job.error || "").slice(0, 120)));
  else if (!a.moments && a.transcript) {
    const au = a.auto;
    if (au && au.decision === "wait") parts.push(el("span", {}, `Claude's pass waits for you: estimate $${(+au.low).toFixed(2)} to $${(+au.high).toFixed(2)}, over your $${(+au.cap).toFixed(2)} line.`));
    const vp = stg.speakers && (stg.speakers.state === "queued" || stg.speakers.state === "running");
    parts.push(el("button", { class: "btn small", type: "button", disabled: vp ? true : null,
      title: vp ? "Waits for the voice split, so Claude can label the voices in the same pass." : null,
      onclick: () => opts.findCalls && opts.findCalls(a) }, icon("auto_awesome"), "Find calls"));
  }
  if (st.view && st.view.bounding) parts.push(el("span", { class: "muted" }, "Finding where each call rings…"));
  if (a.proxy === false && !(stg.remux && stg.remux.state === "done")) showEmpty("The preview copy isn't ready yet.");
  statusLine(...parts);
}

// ------------------------------------------------------------------ the player

function mediaUrl() {
  const a = lib.asset(st.aid);
  if (!a || !a.urls) return null;
  if (a.proxy) return a.urls.proxy;                          // light and quick to jump in (a keyframe every 0.5 s)
  const remux = !a.stages || !a.stages.remux || a.stages.remux.state === "done";
  return remux ? a.urls.orig || null : null;
}

function showEmpty(text) { emptyEl.textContent = text; emptyEl.hidden = !text; }

function select(r, o = {}) {
  if (!st) return;
  if (!(st.cur && st.cur.id === r.id)) { st.played = 0; }
  st.cur = r;
  st.inMark = st.outMark = null;
  markCur();
  nowEl.textContent = r.label || "";
  const node = st.nodes.get(r.id);
  if (node) node.node.scrollIntoView({ block: "nearest" });
  const url = mediaUrl();
  if (!url) { showEmpty("The preview copy isn't ready yet."); drawBar(); return; }
  showEmpty("");
  if (video.dataset.src !== url) {
    video.src = url; video.dataset.src = url;
    const sp = speed(); video.defaultPlaybackRate = sp; video.playbackRate = sp;
  }
  const hit = st.hits && st.hits[r.id];
  const from = o.from !== undefined ? o.from : hit ? Math.max(r.play[0], hit.first - SEARCH_LEAD) : r.from;
  seekTo(from);
  loadWords(r);
  drawBar();
  if (o.play) playNow(); else video.pause();
}

function seekTo(t) {
  if (video.readyState >= 1) { video.currentTime = t; pendingSeek = null; } else pendingSeek = t;
  onTime(t);
}

function playNow() {
  if (!st || !st.cur) return;
  if (S.playing) pb.pause();
  st.lastTick = performance.now();
  const p = video.play();
  if (p && p.catch) p.catch(() => {});
}

function togglePlay() {
  if (!st || !st.cur) return;
  if (video.paused) {
    const t = video.currentTime;
    if (t >= st.cur.play[1] - 0.05 || t < st.cur.play[0] - 0.5) seekTo(st.cur.from);      // at the hang-up: from the ring
    playNow();
  } else video.pause();
}

function speed() {
  let s = 1;
  try { s = +localStorage.getItem("studio.browse.speed") || 1; } catch (e) { /* private mode */ }
  return SPEEDS.includes(s) ? s : 1;
}
function speedLabel() { return speed() + "x"; }
function cycleSpeed() {
  const s = SPEEDS[(SPEEDS.indexOf(speed()) + 1) % SPEEDS.length];
  try { localStorage.setItem("studio.browse.speed", String(s)); } catch (e) { /* private mode */ }
  video.defaultPlaybackRate = s; video.playbackRate = s;
  speedBtn.textContent = s + "x";
}

// each shown frame: captions, the bar, the stop at the hang-up, the watched mark. requestVideoFrameCallback, so the stop
// lands on the frame (timeupdate fires every 250 ms: half a second late at 2x)
function startLoop() {
  stopLoop();
  const tick = (now, meta) => {
    if (!st) return;
    onTime(meta ? meta.mediaTime : video.currentTime);
    if (!video.paused) rvfc = video.requestVideoFrameCallback(tick);
  };
  rvfc = video.requestVideoFrameCallback(tick);
}
function stopLoop() {
  if (rvfc && video.cancelVideoFrameCallback) video.cancelVideoFrameCallback(rvfc);
  rvfc = 0;
}

function onTime(t) {
  if (!st || !st.cur) { clearCaps(); return; }
  const r = st.cur;
  if (!video.paused) {
    const now = performance.now();
    st.played += Math.min(0.25, (now - (st.lastTick || now)) / 1000);
    st.lastTick = now;
    if (st.played >= WATCH_AFTER && !r.watched && !st.watchedSent.has(r.id)) markWatched(r);
    if (t >= r.play[1]) { video.pause(); video.currentTime = r.play[1]; t = r.play[1]; }     // the hang-up (B10)
  }
  drawCaps(t);
  drawBar(t);
}

function markWatched(r) {
  st.watchedSent.add(r.id);
  r.watched = true;
  const n = st.nodes.get(r.id);
  if (n) n.node.classList.add("watched");
  api.patch(`/api/asset/${st.aid}/calls/${encodeURIComponent(r.id)}`, { watched: true }).catch(() => {});
}

// ------------------------------------------------------------------ the bar, marks and Make short

function bindBar() {
  bar.addEventListener("pointerdown", (e) => {
    if (!st || !st.cur || e.button !== 0 || e.target.closest(".br-mark")) return;
    const at = (ev) => { const b = bar.getBoundingClientRect(); const [p0, p1] = st.cur.play; return p0 + Math.max(0, Math.min(1, (ev.clientX - b.left) / b.width)) * (p1 - p0); };
    try { bar.setPointerCapture(e.pointerId); } catch (err) { /* synthetic */ }
    seekTo(at(e));
    const move = (ev) => seekTo(at(ev));
    const up = () => { bar.removeEventListener("pointermove", move); bar.removeEventListener("pointerup", up); bar.removeEventListener("pointercancel", up); };
    bar.addEventListener("pointermove", move);
    bar.addEventListener("pointerup", up);
    bar.addEventListener("pointercancel", up);
  });
}

function markedSpan() {
  const [p0, p1] = st.cur.play;
  return [st.inMark !== null ? st.inMark : p0, st.outMark !== null ? st.outMark : p1];
}

function mark(isIn) {
  if (!st || !st.cur) return;
  const [p0, p1] = st.cur.play;
  const t = Math.max(p0, Math.min(p1, video.currentTime));
  if (isIn) { st.inMark = r3(t); if (st.outMark !== null && st.outMark <= st.inMark) st.outMark = null; }
  else { st.outMark = r3(t); if (st.inMark !== null && st.inMark >= st.outMark) st.inMark = null; }
  drawBar();
}

function clearMarks() { if (!st) return; st.inMark = st.outMark = null; drawBar(); }

function drawBar(t = video.currentTime) {
  if (!st || !st.cur) { timeEl.textContent = ""; marksTxt.textContent = ""; clear(marksEl); return; }
  const [p0, p1] = st.cur.play, len = Math.max(0.001, p1 - p0);
  const pct = (x) => (Math.max(0, Math.min(1, (x - p0) / len)) * 100).toFixed(3) + "%";
  headEl.style.left = pct(t);
  fillEl.style.left = "0"; fillEl.style.width = pct(t);
  const has = st.inMark !== null || st.outMark !== null;
  rangeEl.hidden = !has;
  if (has) { const [a, b] = markedSpan(); rangeEl.style.left = pct(a); rangeEl.style.width = `calc(${pct(b)} - ${pct(a)})`; }
  timeEl.textContent = `${fmtDur(Math.max(0, t - p0))} / ${fmtDur(len)}`;
  marksTxt.textContent = has ? `In ${fmtDur(markedSpan()[0] - p0)} · Out ${fmtDur(markedSpan()[1] - p0)}` : "";
  clearBtn.hidden = !has;
  const id = st.cur.id;
  if (marksEl.dataset.for !== id) {
    clear(marksEl);
    marksEl.dataset.for = id;
    for (const b of st.view.bits.filter((x) => x.call === id)) {
      const m = el("button", { class: "br-mark", type: "button", title: `${b.title} (${"★".repeat(b.strength || 0)})\nClick to mark it and play it.`,
        style: { left: pct(Math.max(p0, Math.min(p1, b.start))) },
        onclick: (e) => { e.stopPropagation(); st.inMark = r3(Math.max(p0, b.start)); st.outMark = r3(Math.min(p1, b.end)); seekTo(st.inMark); playNow(); drawBar(); } });
      marksEl.append(m);
    }
  }
}

async function makeShort() {
  if (!st || !st.cur) return;
  const r = st.cur;
  const [s, e] = markedSpan();
  if (e - s < 0.5) { toast("Mark at least half a second (I and O).", true); return; }
  const bit = st.view.bits.find((b) => b.call === r.id && Math.abs(Math.max(r.play[0], b.start) - s) < 0.05 && Math.abs(Math.min(r.play[1], b.end) - e) < 0.05);
  const body = { asset: st.aid, call: r.id.startsWith("x") ? null : r.id, start: r3(s), end: r3(e), name: bit ? bit.title : r.label };
  if (bit) body.bit = bit.id;
  makeBtn.disabled = true;
  try {
    const doc = await api.newProject(body);
    leave(true);
    await openShort(doc.id);
    toast(`Opened "${doc.name}"`);
  } catch (err) { toast(err.message, true); }
  finally { makeBtn.disabled = false; }
}

// ------------------------------------------------------------------ captions on the picture (B17)

async function loadWords(r) {
  const aid = st.aid, key = r.id + ":" + r.play.join("-");
  if (st.wordsKey === key && st.capDoc) return;
  st.wordsKey = key;
  st.capDoc = null;
  clearCaps();
  let w;
  try { w = await api.get(`/api/asset/${aid}/words?s=${r.play[0]}&e=${r.play[1]}`); }
  catch (e) { return; }                        // no transcript: the call plays without captions
  if (!st || st.aid !== aid || st.wordsKey !== key) return;
  // a stand-in short: one A1 clip whose timeline frames are the recording's own, fed only this call's words
  const f0 = Math.floor(r.play[0] * FPS), f1 = Math.ceil(r.play[1] * FPS);
  const doc = normalize({ id: "browse", clips: [{ id: "b1", track: "A1", type: "audio", asset: aid, in: f0, out: f1, start: f0 }] });
  const tr = { words: w.words, voices: w.voices };
  const ev = buildCaptionEvents(doc, { transcript: () => tr, transcriptPending: () => false }, measureCaption(doc.captions.size));
  doc.captions.events = ev || [];
  st.capDoc = doc;
  drawCaps(video.currentTime);
}

function drawCaps(t) {
  const g = caps.getContext("2d");
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.clearRect(0, 0, caps.width, caps.height);
  if (!st || !st.capDoc) return;
  const k = caps.width / 1080;
  g.setTransform(k, 0, 0, k, 0, 0);
  drawCaptions(g, st.capDoc, Math.floor(t * FPS + 1e-6));
  g.setTransform(1, 0, 0, 1, 0, 0);
}

function clearCaps() {
  const g = caps && caps.getContext("2d");
  if (g) { g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, caps.width, caps.height); }
}

// ------------------------------------------------------------------ layout

function layoutPlayer() {
  if (!st || root.hidden) return;
  const rr = root.getBoundingClientRect();
  if (!rr.height) return;
  const chrome = bar.offsetHeight + controls.offsetHeight + nowEl.offsetHeight + 3 * 6 + 20;
  let w = Math.round(Math.max(120, rr.height - chrome) * 9 / 16);
  w = Math.max(160, Math.min(w, Math.round(rr.width * 0.6)));
  root.style.setProperty("--pw", w + "px");
  requestAnimationFrame(fitCaps);
}

// the caption canvas covers the picture itself: the video's own shape fitted inside the stage
function fitCaps() {
  const s = stage.getBoundingClientRect();
  if (!s.width || !s.height) return;
  const ar = video.videoWidth && video.videoHeight ? video.videoWidth / video.videoHeight : 9 / 16;
  let w = s.width, h = w / ar;
  if (h > s.height) { h = s.height; w = h * ar; }
  Object.assign(caps.style, { left: (s.width - w) / 2 + "px", top: (s.height - h) / 2 + "px", width: w + "px", height: h + "px" });
  const dpr = window.devicePixelRatio || 1;
  caps.width = Math.max(1, Math.round(w * dpr));
  caps.height = Math.max(1, Math.round(h * dpr));
  if (st) drawCaps(video.currentTime);
}

// ------------------------------------------------------------------ keys (B9, B11, B12)

// keys.js asks first while the calls view has focus: Space, Up, Down, I and O are the view's; everything else (Left,
// Right, J, K, L, Delete...) still acts on the open short
export function browseKey(e, combo) {
  if (!st || !root.contains(e.target)) return false;
  if (combo === "Space") { togglePlay(); return true; }
  if (combo === "Down" || combo === "Up") {
    const rows = visibleRows();
    const i = st.cur ? rows.findIndex((r) => r.id === st.cur.id) : -1;
    const r = rows[Math.max(0, Math.min(rows.length - 1, i + (combo === "Down" ? 1 : -1)))];
    if (r && (!st.cur || r.id !== st.cur.id)) select(r, { play: true });
    return true;
  }
  if (combo === "I" || combo === "O") { mark(combo === "I"); return true; }
  return false;
}

export function browseApi() {
  return { open: openRecording, close: closeBrowse, isOpen: isBrowsing, state: () => st, video: () => video, root: () => root,
    caps: () => caps, select: (id, o) => { const r = st && st.view.calls.find((x) => x.id === id); if (r) select(r, o || {}); },
    recordingTitle, fmtHours };
}
