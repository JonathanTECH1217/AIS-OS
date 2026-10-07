// Monarc Calls (reworked 2026-10-03, Q32-Q45): the notes window, about 510 x 780 beside Airtable's grid.
// Bar: the dot (pulses while it hears speech), Listening / Paused, the session clock, F9, Pause, Stop.
// This call: key notes as they're heard, by kind, the matched phrase in bold.
// To file: one card per call that had key notes, made when he types Status in Airtable; every note an editable line,
// "+ Add", Push to file, Discard. Cards are built once and kept, so a line he is typing in never loses its text.
// Filed: the last few docs written. Footer: what's waiting for Airtable.
import { el, clear, icon, append } from "../util.js";
import { confirmDialog, toast } from "../components/modal.js";
import { C, on, send, loadCheck, draftOf, saveDraft, dropDraft, cardKey, ARTIFACTS } from "./state.js";

const KINDS = ["offering", "constraint", "objection", "email", "name", "phone", "meeting"];
const LABEL = { offering: "Offering", constraint: "Constraint", objection: "Objection", email: "Email", name: "Name", phone: "Phone", meeting: "Meeting" };

let barEl, mainEl, footEl, startEl, liveEl, cardsHead, cardsEl, filedEl, bannerEl;
let dot, stateLabel, clock, hotkeyChip, pauseBtn, stopBtn;
const cardNodes = new Map();          // "sid#n" -> {node, rows}

export function mountNotes(bar, main, foot) {
  barEl = bar; mainEl = main; footEl = foot;
  dot = el("span", { class: "cl-dot" });
  stateLabel = el("span", { class: "cl-state-label" }, "Ready");
  clock = el("span", { class: "cl-clock" });
  hotkeyChip = el("span", { class: "chip small cl-key", hidden: true });
  pauseBtn = el("button", { class: "btn small quiet", type: "button", hidden: true, onclick: togglePause }, icon("pause"), "Pause");
  stopBtn = el("button", { class: "btn small cl-stop", type: "button", hidden: true, onclick: stop }, icon("stop"), "Stop");
  barEl.append(dot, stateLabel, clock, el("span", { class: "grow" }), hotkeyChip, pauseBtn, stopBtn);
  bannerEl = el("div", { class: "cl-banners" });
  startEl = el("section", { class: "cl-start" });
  liveEl = el("section", { class: "cl-live" });
  cardsHead = el("div", { class: "cl-sec-head" });
  cardsEl = el("div", { class: "cl-cards" });
  filedEl = el("section", { class: "cl-filed" });
  mainEl.append(bannerEl, startEl, liveEl, el("section", { class: "cl-tofile" }, cardsHead, cardsEl), filedEl);
  on("view", render); on("check", render);
  setInterval(tick, 1000);
  render();
}

// ---------------------------------------------------------------- the bar

function fmtClock(t) {
  t = Math.max(0, Math.floor(t));
  return `${Math.floor(t / 3600)}:${String(Math.floor((t % 3600) / 60)).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}`;
}

function tick() {
  const v = C.view;
  clock.textContent = v && v.active && v.started ? fmtClock(Date.now() / 1000 + C.clockOffset - v.started) : "";
}

function renderBar() {
  const v = C.view || {};
  dot.className = "cl-dot" + (v.listening ? " on" : "") + (v.listening && v.level ? " hear" : "") + (v.active && !v.listening ? " paused" : "");
  stateLabel.textContent = !v.active ? "Ready" : v.listening ? "Listening" : "Paused";
  pauseBtn.hidden = stopBtn.hidden = !v.active;
  clear(pauseBtn).append(icon(v.listening ? "pause" : "play_arrow"), v.listening ? "Pause" : "Resume");
  pauseBtn.title = v.listening ? "Stop listening for now (F9)" : "Start listening again (F9)";
  hotkeyChip.hidden = !v.active || v.hotkey === null || v.hotkey === undefined;
  hotkeyChip.textContent = v.hotkey ? "F9" : "F9 taken";
  hotkeyChip.title = v.hotkey ? "F9 pauses and resumes, even while Airtable has focus." : "Another program holds F9. Use the Pause button.";
  tick();
}

async function togglePause() {
  const v = C.view;
  if (!v || !v.active) return;
  try { await send(v.listening ? "pause" : "resume"); } catch (e) { toast(e.message, true); }
}

async function stop() {
  const v = C.view || {};
  const open = (v.cards || []).length;
  const ok = await confirmDialog("End the session?",
    el("p", {}, `Listening stops. Words after your last Status aren't filed.${open ? ` Your ${open} card${open === 1 ? "" : "s"} to file stay here.` : ""}`),
    "End session");
  if (!ok) return;
  try { await send("stop"); } catch (e) { toast(e.message, true); }
}

// ---------------------------------------------------------------- banners and the start panel

function banner(kind, ic, text, extra) {
  return el("div", { class: "cl-banner " + kind }, icon(ic), el("span", { class: "grow" }, text), extra || null);
}

function renderBanners() {
  clear(bannerEl);
  const v = C.view || {};
  if (C.offline || C.queued) bannerEl.append(banner("warn", "warning", C.queued ? `Can't reach the Studio server. ${C.queued} click${C.queued === 1 ? "" : "s"} waiting; they go in order once it's back.` : "Can't reach the Studio server. Trying again…"));
  if (v.active && v.micError) bannerEl.append(banner("", "error", v.micError));
  if (v.active && v.pollError) bannerEl.append(banner("warn", "schedule", v.pollError));
}

function checkLine(c) {
  if (!c) return null;
  return el("div", { class: "cl-check " + (c.ok ? "ok" : "bad") }, icon(c.ok ? "check_circle" : "error"), el("span", {}, c.text));
}

function renderStart() {
  const v = C.view || {};
  startEl.hidden = !!v.active;
  if (v.active) return;
  clear(startEl);
  const ch = C.check;
  const ready = ch && ch.mic && ch.mic.ok && ch.airtable && ch.airtable.ok;
  append(startEl, [
    el("h1", {}, "Monarc Calls"),
    el("p", { class: "cl-hint" }, "Press Start, then dial and talk as usual. Type Status in Airtable after each call: what was heard since the last Status goes to that row."),
    el("div", { class: "row" },
      el("button", { class: "btn cl-go", type: "button", disabled: ready ? null : true, onclick: start }, icon("play_arrow"), "Start"),
      el("button", { class: "btn small quiet", type: "button", title: "Look again", onclick: loadCheck }, icon("refresh"), "Check again")),
    C.startError ? banner("", "error", C.startError) : null,
    el("div", { class: "cl-checks" }, !ch ? el("div", { class: "cl-check" }, icon("progress_activity"), el("span", {}, "Checking the mic and the Prospects base…"))
      : [checkLine(ch.mic), checkLine(ch.phrases), checkLine(ch.airtable), ch.airtable && ch.airtable.logError ? checkLine({ ok: false, text: ch.airtable.logError }) : null]),
    v.stopped && v.id ? el("p", { class: "cl-hint" }, `Last session: ${v.calls} call${v.calls === 1 ? "" : "s"}.`) : null]);
}

async function start() {
  C.startError = null;
  try { await send("start"); } catch (e) { C.startError = e.message; renderStart(); }
}

// ---------------------------------------------------------------- this call

function highlighted(text, match) {
  if (!match || match[1] <= match[0]) return [text];
  return [text.slice(0, match[0]), el("b", {}, text.slice(match[0], match[1])), text.slice(match[1])];
}

function renderLive() {
  const v = C.view || {};
  liveEl.hidden = !v.active;
  if (!v.active) return;
  clear(liveEl);
  const live = v.live || { notes: [] };
  const since = live.since ? new Date((live.since - C.clockOffset) * 1000).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) : "";
  liveEl.append(el("div", { class: "cl-sec-head" }, el("span", { class: "cl-sec-title" }, "This call"),
    el("span", { class: "muted small" }, `since ${since}${live.heard ? ` · ${live.heard} line${live.heard === 1 ? "" : "s"} heard` : ""}`)));
  if (!live.notes.length) {
    liveEl.append(el("p", { class: "cl-empty" }, v.listening ? "Key notes show here as they're said." : "Paused. Nothing is heard until you resume."));
    return;
  }
  for (const k of KINDS) {
    const ns = live.notes.filter((n) => n.kind === k);
    if (!ns.length) continue;
    liveEl.append(el("div", { class: "cl-group" }, el("div", { class: "cl-kind k-" + k }, LABEL[k]),
      ns.map((n) => el("div", { class: "cl-note" + (n.flag ? " flag" : "") },
        ARTIFACTS.includes(k) && n.value ? [el("b", {}, n.value), n.flag ? el("span", { class: "cl-flag" }, " · " + n.flag) : null, el("div", { class: "cl-heard" }, n.text)]
          : [highlighted(n.text, n.match), n.flag ? el("span", { class: "cl-flag" }, " · " + n.flag) : null]))));
  }
}

// ---------------------------------------------------------------- to file

function when(t) {
  return t ? new Date((t - C.clockOffset) * 1000).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) : "";
}

function noteRow(card, list, i, rebuild) {
  const item = list[i];
  const kind = el("select", { class: "cl-row-kind", "aria-label": "Kind", onchange: () => { item.kind = kind.value; saveDraft(card, list); } },
    KINDS.map((k) => el("option", { value: k, selected: k === item.kind ? true : null }, LABEL[k])));
  const input = el("textarea", { class: "cl-row-text", rows: 1, spellcheck: "true", "aria-label": "Note",
    oninput: () => { item.text = input.value; saveDraft(card, list); fit(input); } });
  input.value = item.text || "";
  const del = el("button", { class: "icon-btn small", type: "button", title: "Take this note out", onclick: () => { list.splice(i, 1); saveDraft(card, list); rebuild(); } }, icon("close"));
  const row = el("div", { class: "cl-row" + (item.flag ? " flag" : "") }, kind, input, del);
  const under = [];
  if (item.flag) under.push(el("span", { class: "cl-flag" }, item.flag));
  if (ARTIFACTS.includes(item.kind) && item.line && item.line !== item.text) under.push(el("span", { class: "cl-heard" }, "heard: " + item.line));
  setTimeout(() => fit(input), 0);
  return el("div", { class: "cl-row-wrap" }, row, under.length ? el("div", { class: "cl-row-under" }, under) : null);
}

function fit(t) { t.style.height = "auto"; t.style.height = Math.min(160, t.scrollHeight + 2) + "px"; }

function buildCard(card) {
  const list = draftOf(card);
  const rowsEl = el("div", { class: "cl-rows" });
  const rebuild = () => { clear(rowsEl); list.forEach((_, i) => rowsEl.append(noteRow(card, list, i, rebuild))); if (!list.length) rowsEl.append(el("p", { class: "cl-empty" }, "No notes left. Push files the words only.")); };
  rebuild();
  const add = el("button", { class: "btn small quiet", type: "button", onclick: () => {
    list.push({ kind: "offering", text: "" }); saveDraft(card, list); rebuild();
    const last = rowsEl.querySelectorAll(".cl-row-text"); if (last.length) last[last.length - 1].focus();
  } }, icon("add"), "Add");
  const discard = el("button", { class: "btn small quiet", type: "button", onclick: async () => {
    const ok = await confirmDialog("Discard these notes?", el("p", {}, `Nothing is filed for ${card.name || "this call"}. Its Outreach Log row stays.`), "Discard");
    if (!ok) return;
    try { await send("discard", { sid: card.sid, n: card.n }); dropDraft(card); } catch (e) { toast(e.message, true); }
  } }, "Discard");
  const push = el("button", { class: "btn small", type: "button", onclick: async () => {
    const notes = list.filter((x) => (x.text || "").trim()).map((x) => ({ kind: x.kind, text: x.text.trim() }));
    try { push.disabled = true; await send("push", { sid: card.sid, n: card.n, notes }); dropDraft(card); toast(`Filed ${card.name || "the call"}.`); }
    catch (e) { push.disabled = false; toast(e.message, true); }
  } }, icon("check"), "Push to file");
  const head = el("div", { class: "cl-card-head" });
  const node = el("article", { class: "cl-card", dataset: { key: cardKey(card) } }, head, rowsEl,
    el("div", { class: "cl-card-actions" }, add, el("span", { class: "grow" }), discard, push));
  return { node, head };
}

function renderCards() {
  const v = C.view || {};
  const cards = v.cards || [];
  clear(cardsHead).append(el("span", { class: "cl-sec-title" }, `To file${cards.length ? ` (${cards.length})` : ""}`),
    el("span", { class: "muted small" }, cards.length ? "edit, then push" : "a card appears when you type Status"));
  const keep = new Set(cards.map(cardKey));
  for (const [k, c] of cardNodes) if (!keep.has(k)) { c.node.remove(); cardNodes.delete(k); }
  for (const card of cards) {
    const k = cardKey(card);
    let c = cardNodes.get(k);
    if (!c) { c = buildCard(card); cardNodes.set(k, c); }
    append(clear(c.head), [el("span", { class: "cl-card-name", title: card.rec || "" }, card.name || "(no name)"),
      el("span", { class: "cl-mb" }, card.mb || ""), card.status ? el("span", { class: "chip-status" }, card.status) : null,
      el("span", { class: "grow" }), el("span", { class: "muted small" }, when(card.at))]);
    cardsEl.append(c.node);              // in order (append moves an existing node)
  }
}

function renderFiled() {
  clear(filedEl);
  const v = C.view || {};
  const f = v.filed || [];
  if (!f.length) return;
  filedEl.append(el("div", { class: "cl-sec-head" }, el("span", { class: "cl-sec-title" }, "Filed")),
    ...f.map((x) => el("div", { class: "cl-filed-row", title: x.path || "" }, icon(x.how === "pushed" ? "task_alt" : "subtitles"),
      el("span", { class: "grow" }, x.name || "(no name)", el("span", { class: "cl-mb" }, " " + (x.mb || ""))),
      el("span", { class: "muted small" }, x.how === "pushed" ? `${x.notes} note${x.notes === 1 ? "" : "s"}` : "words only"))));
}

function renderFoot() {
  clear(footEl);
  const v = C.view || {};
  const w = v.writes || {};
  if (w.pending) footEl.append(el("span", { class: "cl-foot-warn" }, icon("schedule"), `${w.pending} waiting for Airtable${w.failing ? " (it didn't answer; trying again)" : ""}`),
    el("button", { class: "btn small quiet", type: "button", onclick: () => send("retry").catch(() => {}) }, "Retry now"));
  else if ((w.stuck || []).length) footEl.append(el("span", { class: "cl-foot-bad", title: w.stuck.map((s) => `${s.kind}${s.role ? " " + s.role : ""}: ${s.err || ""}`).join("\n") },
    icon("error"), `${w.stuck.length} change${w.stuck.length === 1 ? "" : "s"} Airtable refused (hover for why)`));
  else if (v.id) footEl.append(el("span", { class: "muted small" }, icon("check"), "Airtable is up to date"));
}

function render() {
  renderBar();
  renderBanners();
  renderStart();
  renderLive();
  renderCards();
  renderFiled();
  renderFoot();
}

export function notesApi() { return { render, cardNodes }; }
