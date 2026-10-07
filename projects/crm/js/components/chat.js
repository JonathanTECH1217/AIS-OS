// The chat box (Jonathan, 2026-10-05: "Option to open up a chat window inside of the operating system... a chat box
// that sends a message to Claude"). A panel on the right of every page, opened from the top bar. It talks to the same
// clone as a chat in VS Code: the server starts Claude Code without a window (scripts/crm_chat.py), hands it each
// line, and keeps what comes back as events this panel asks for. Before a tool that needs his go, a card asks here.
import { el, append, clear } from "../util.js";
import { api } from "../api.js";
import { toast } from "./modal.js";

const KEY = { open: "crm.chat.open", session: "crm.chat.session" };
const ICON = {
  chat: '<path d="M4.5 5.5h15a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H10l-4.5 3.5v-3.5h-1a1 1 0 0 1-1-1v-10a1 1 0 0 1 1-1z"/>',
  add: '<path d="M12 5v14M5 12h14"/>',
  out: '<path d="M14 4.5h5.5V10M19.5 4.5l-8 8M10 6.5H5.5a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1V14"/>',
  close: '<path d="M6 6l12 12M18 6L6 18"/>',
  send: '<path d="M12 19V5M5.5 11.5L12 5l6.5 6.5"/>',
  stop: '<rect x="7" y="7" width="10" height="10" rx="1.5"/>',
};
const svg = (d, size = 20) => `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>`;
const store = { get: (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set: (k, v) => { try { if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { /* private window */ } } };

// The clone's words as simple HTML: paragraphs, lists, bold, code, links. Everything is escaped first.
function md(text) {
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  const inline = (s) => s
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (m, t, u) => (/^https?:\/\//.test(u) ? `<a href="${u}" target="_blank" rel="noopener">${t}</a>` : t));
  const out = [];
  let list = null, pre = null, para = [];
  const flush = () => {
    if (para.length) out.push(`<p>${para.join("<br>")}</p>`);
    para = [];
    if (list) out.push(`</${list}>`);
    list = null;
  };
  for (const raw of esc(String(text || "")).split("\n")) {
    if (/^\s*```/.test(raw)) {
      if (pre === null) { flush(); pre = []; } else { out.push(`<pre>${pre.join("\n")}</pre>`); pre = null; }
      continue;
    }
    if (pre !== null) { pre.push(raw); continue; }
    const line = raw.trimEnd();
    const head = line.match(/^#{1,4}\s+(.*)$/), item = line.match(/^\s*(?:[-*]|(\d+)[.)])\s+(.*)$/);
    if (!line.trim()) flush();
    else if (/^\s*\|.*\|\s*$/.test(line)) { flush(); out.push(`<pre>${line}</pre>`); }
    else if (head) { flush(); out.push(`<p><b>${inline(head[1])}</b></p>`); }
    else if (item) {
      const kind = item[1] ? "ol" : "ul";
      if (para.length || (list && list !== kind)) flush();
      if (!list) { list = kind; out.push(`<${kind}>`); }
      out.push(`<li>${inline(item[2])}</li>`);
    } else {
      if (list) flush();
      para.push(inline(line));
    }
  }
  if (pre !== null) out.push(`<pre>${pre.join("\n")}</pre>`);
  flush();
  return out.join("");
}

export function mountChat() {
  const app = document.querySelector(".app");
  const refresh = document.getElementById("refresh-all");
  if (!app || !refresh) return;
  const openBtn = el("button", { class: "icon-btn", id: "chat-open", type: "button", title: "Chat with the clone", "aria-label": "Chat with the clone", html: svg(ICON.chat, 24) });
  refresh.before(openBtn);

  const log = el("div", { class: "chat-log", "aria-live": "polite" });
  const box = el("textarea", { rows: "1", placeholder: "Message the clone", "aria-label": "Message the clone" });
  const go = el("button", { class: "chat-go", type: "submit", title: "Send", "aria-label": "Send", html: svg(ICON.send) });
  const form = el("form", { class: "chat-form" }, box, go);
  const working = el("div", { class: "chat-working", hidden: true }, "Working");
  const headBtn = (icon, title, fn) => el("button", { class: "icon-btn", type: "button", title, "aria-label": title, html: svg(icon), onclick: fn });
  const panel = el("aside", { class: "chat", id: "chat", "aria-label": "Chat with the clone", hidden: true },
    el("div", { class: "chat-head" }, el("span", { class: "t" }, "Clone"),
      headBtn(ICON.add, "New chat", fresh), headBtn(ICON.out, "Open this chat in VS Code", toCode), headBtn(ICON.close, "Close", () => show(false))),
    log, working, form);
  app.append(panel);

  let chat = null;                       // the server's id for the chat this panel shows
  let session = store.get(KEY.session);  // its Claude Code session, so it goes on after a reload or a server restart
  let seq = 0, busy = false, polling = false, live = null;
  const asks = new Map();

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const nearEnd = () => log.scrollHeight - log.scrollTop - log.clientHeight < 80;
  function add(node) {
    const stick = nearEnd();
    const empty = log.querySelector(".chat-empty");
    if (empty) empty.remove();
    log.append(node);
    if (stick) log.scrollTop = log.scrollHeight;
    return node;
  }
  function hello() {
    clear(log);
    log.append(el("div", { class: "chat-empty" },
      el("div", { class: "strong" }, "Ask the clone, or tell it what to do."),
      el("div", {}, "It is the same Claude as in VS Code, with the same files and skills. Before it edits a file, runs a command, or sends anything, it asks here.")));
  }
  function setBusy(b) {
    busy = b;
    working.hidden = !b;
    go.innerHTML = svg(b ? ICON.stop : ICON.send);
    go.title = b ? "Stop" : "Send";
    go.setAttribute("aria-label", go.title);
    go.classList.toggle("is-stop", b);
  }

  function askCard(e) {
    const said = el("div", { class: "chat-ask-said", hidden: true });
    const answer = async (allow, always) => {
      buttons.querySelectorAll("button").forEach((b) => { b.disabled = true; });
      try { await api.post("/api/chat/answer", { chat, id: e.id, allow, always }); }
      catch (err) { toast((err.errors || [String(err)]).join(" "), true); }
    };
    const buttons = el("div", { class: "chat-ask-btns" },
      el("button", { class: "btn small", type: "button", onclick: () => answer(true, false) }, "Allow"),
      e.always ? el("button", { class: "btn quiet small", type: "button", onclick: () => answer(true, true) }, "Always in this chat") : null,
      el("button", { class: "btn quiet small", type: "button", onclick: () => answer(false, false) }, "Deny"));
    const card = el("div", { class: "chat-ask" },
      el("div", { class: "label" }, "The clone asks to use"),
      el("div", {}, el("span", { class: "strong" }, e.name), e.what ? ` · ${e.what}` : ""),
      e.detail && e.detail !== e.what ? el("pre", {}, e.detail) : null, buttons, said);
    asks.set(e.id, { buttons, said });
    return card;
  }

  function apply(r) {
    for (const e of r.events || []) {
      if (e.kind === "user") { live = null; add(el("div", { class: "msg user" }, e.text)); }
      else if (e.kind === "delta") {
        if (!live) live = { node: add(el("div", { class: "msg bot" })), raw: "" };
        live.raw += e.text;
        const stick = nearEnd();
        live.node.innerHTML = md(live.raw);
        if (stick) log.scrollTop = log.scrollHeight;
      } else if (e.kind === "text") {
        const node = live ? live.node : add(el("div", { class: "msg bot" }));
        const stick = nearEnd();
        node.innerHTML = md(e.text);
        if (stick) log.scrollTop = log.scrollHeight;
        live = null;
      } else if (e.kind === "tool") { live = null; add(el("div", { class: "chat-tool" }, el("span", { class: "strong" }, e.name), e.what ? ` ${e.what}` : "")); }
      else if (e.kind === "ask") { live = null; add(askCard(e)); log.scrollTop = log.scrollHeight; }
      else if (e.kind === "answered") {
        const a = asks.get(e.id);
        if (a) { a.buttons.hidden = true; a.said.hidden = false; a.said.textContent = e.allow ? (e.always ? "Allowed for this chat." : "Allowed.") : "Denied."; }
      } else if (e.kind === "error") { live = null; add(el("div", { class: "chat-error" }, e.text)); }
      else if (e.kind === "note") { live = null; add(el("div", { class: "chat-tool" }, e.text)); }
      else if (e.kind === "done") live = null;
    }
    seq = r.seq;
    if (r.session && r.session !== session) { session = r.session; store.set(KEY.session, session); }
    setBusy(!!r.busy);
  }

  // One read to catch up, then it keeps asking only while the clone is answering: a chat at rest has nothing new to say.
  async function poll() {
    if (polling) return;
    polling = true;
    let first = true;
    while (chat && !panel.hidden && (busy || first)) {
      const mine = chat;
      try {
        const r = await api.get(`/api/chat/events?chat=${mine}&since=${seq}&wait=${busy ? 1 : 0}`);
        first = false;
        if (chat === mine) apply(r);
      } catch (e) {
        if (e.status === 404) { if (chat === mine) { chat = null; setBusy(false); } break; }  // the server restarted: the next line picks the session up
        await sleep(1500);
      }
    }
    polling = false;
  }

  // Back into the chat he left: what was said is read from its session file.
  async function attach() {
    if (chat || !session) return;
    try {
      const r = await api.post("/api/chat/attach", { session });
      chat = r.chat; seq = 0; asks.clear(); live = null;
      clear(log);
      if (!r.session) { session = null; store.set(KEY.session, null); hello(); }
      poll();
    } catch (e) { hello(); }
  }

  async function send(text) {
    try {
      const r = await api.post("/api/chat/send", { chat, session, text });
      if (r.chat !== chat) { chat = r.chat; seq = 0; clear(log); asks.clear(); live = null; }  // a chat picked up again comes back whole
      setBusy(true);
      poll();
    } catch (e) {
      toast((e.errors || [String(e)]).join(" "), true);
      box.value = text;
    }
  }

  function fresh() {
    if (busy) { toast("The clone is still answering. Press Stop first."); return; }
    chat = null; session = null; seq = 0; live = null; asks.clear();
    store.set(KEY.session, null);
    hello();
    box.focus();
  }
  async function toCode() {
    if (!chat) { toast("Send a line first; there is no chat to open yet."); return; }
    try { const r = await api.post("/api/chat/open", { chat }); toast(r.dry ? "Test mode: nothing was opened." : "Opening this chat in VS Code."); }
    catch (e) { toast((e.errors || [String(e)]).join(" "), true); }
  }
  function show(on, focus = true) {
    panel.hidden = !on;
    app.classList.toggle("chat-open", on);
    openBtn.classList.toggle("is-on", on);
    store.set(KEY.open, on ? "1" : null);
    if (!on) return;
    if (chat) poll(); else if (session) attach(); else hello();
    if (focus) box.focus();
  }

  const grow = () => { box.style.height = "auto"; box.style.height = Math.min(160, box.scrollHeight) + "px"; };
  box.addEventListener("input", grow);
  box.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); form.requestSubmit(); }
  });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (busy) { try { await api.post("/api/chat/stop", { chat }); } catch (err) { toast((err.errors || [String(err)]).join(" "), true); } return; }
    const text = box.value.trim();
    if (!text) return;
    box.value = "";
    grow();
    send(text);
  });
  openBtn.addEventListener("click", () => show(panel.hidden));
  hello();
  if (store.get(KEY.open) === "1") show(true, false);  // left open last time: open again, the cursor stays where it was
}
