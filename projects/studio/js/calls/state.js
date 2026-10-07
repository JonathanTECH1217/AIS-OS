// Monarc Calls (2026-10-01; reworked 2026-10-03): the notes window's state. The server holds the session
// (scripts/studio_session.py); this keeps what the page shows, long-polls /api/session for changes, and sends every
// click with its own id (cid). When the server can't be reached, clicks wait in localStorage and go in order once it's
// back; the server ignores a cid it has seen, so a resend never counts twice. Card edits are kept here (and in
// localStorage) until he pushes, so a reload or a crash doesn't lose them.
import { api } from "../api.js";

export const C = {
  view: null,          // GET /api/session: listening, live notes, cards to file, filed, Airtable writes
  check: null,         // GET /api/session/check: the mic, the phrase file, the Prospects base, in plain words
  offline: false, queued: 0,
  startError: null,
  clockOffset: 0,      // server time minus this page's time (same laptop: about 0)
};

const subs = new Map();
export function on(topic, fn) { if (!subs.has(topic)) subs.set(topic, new Set()); subs.get(topic).add(fn); }
export function emit(topic) { for (const fn of subs.get(topic) || []) { try { fn(); } catch (e) { console.error(e); } } }

const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const uuid = () => (crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2) + Date.now().toString(36));
const QKEY = "calls.queue";
const DKEY = "calls.drafts";

function load(key, empty) { try { return JSON.parse(localStorage.getItem(key) || "") || empty; } catch (e) { return empty; } }
function store(key, v) { try { localStorage.setItem(key, JSON.stringify(v)); } catch (e) { /* private window: memory only */ } }
const queue = load(QKEY, []);
function saveQueue() { store(QKEY, queue); C.queued = queue.length; }
let flushing = false;

export function apply(v) {
  if (!v || typeof v !== "object" || !("active" in v)) return;
  C.view = v;
  C.clockOffset = (v.now || Date.now() / 1000) - Date.now() / 1000;
  emit("view");
}

const isNetwork = (e) => !(e && e.status);

// one click to the server: {cid, at} added; returns the session view, or {queued: true} when it had to wait
export async function send(action, body = {}) {
  const msg = { cid: uuid(), at: Date.now() / 1000, ...body };
  if (queue.length && action !== "start" && action !== "window") { queue.push({ action, body: msg }); saveQueue(); flush(); emit("view"); return { queued: true }; }
  try {
    const v = await api.post(`/api/session/${action}`, msg);
    C.offline = false;
    apply(v);
    return v;
  } catch (e) {
    if (!isNetwork(e) || action === "start" || action === "window") throw e;    // the server said no: the caller says why
    queue.push({ action, body: msg }); saveQueue();
    C.offline = true; emit("view");
    flush();
    return { queued: true };
  }
}

async function flush() {
  if (flushing) return;
  flushing = true;
  try {
    while (queue.length) {
      const { action, body } = queue[0];
      try {
        const v = await api.post(`/api/session/${action}`, body);
        queue.shift(); saveQueue();
        C.offline = false;
        apply(v);
      } catch (e) {
        if (isNetwork(e)) { C.offline = true; emit("view"); await wait(2000); continue; }
        queue.shift(); saveQueue();          // refused (the card was filed meanwhile): drop it
        console.warn("refused", action, e.message);
      }
    }
  } finally { flushing = false; emit("view"); }
}

export async function poll() {
  let rev = 0;
  if (queue.length) flush();
  for (;;) {
    try {
      const v = await api.get("/api/session" + (rev ? `?since=${rev}` : ""));
      if (C.offline && !queue.length) C.offline = false;
      rev = v.rev;
      apply(v);
    } catch (e) {
      C.offline = true; emit("view");
      rev = 0;
      await wait(2000);
    }
  }
}

export async function loadCheck() {
  try { C.check = await api.get("/api/session/check"); }
  catch (e) { C.check = { mic: { ok: false, text: "Can't reach the Studio server." }, airtable: { ok: false, text: e.message } }; }
  emit("check");
}

// ---- his edits to a card, until he pushes: "sid#n" -> [{kind, text}]
const drafts = load(DKEY, {});
export const cardKey = (c) => `${c.sid}#${c.n}`;
export function draftOf(c) {
  const k = cardKey(c);
  if (!drafts[k]) drafts[k] = (c.notes || []).map((n) => ({ kind: n.kind, text: artifactText(n), line: n.text, match: n.match || null, flag: n.flag || null }));
  return drafts[k];
}
export function saveDraft(c, list) { drafts[cardKey(c)] = list; store(DKEY, drafts); }
export function dropDraft(c) { delete drafts[cardKey(c)]; store(DKEY, drafts); }

// email, name, phone and meeting notes are edited as the value (the address, the name), the line heard stays beside it
export const ARTIFACTS = ["email", "name", "phone", "meeting"];
export function artifactText(n) { return ARTIFACTS.includes(n.kind) && n.value ? n.value : n.text; }
