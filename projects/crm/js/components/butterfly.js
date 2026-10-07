// Butterfly: the logo in the top bar is a button (Jonathan, 2026-10-05: "It should literally just be a button. That's
// the logo. When I click on the logo, there should just be three little options"). Run a skill, make a new project, or
// work on one. A project is an artifact, a campaign, or a skill. Each opens its chat with the clone in VS Code; the
// server does the opening (scripts/crm_butterfly.py), so the browser never asks "Open Visual Studio Code?".
import { el, append, clear } from "../util.js";
import { api } from "../api.js";
import { toast } from "./modal.js";
import { BRAND } from "../views/channels.js";

// Skills and workflows (Jonathan, 2026-10-05): a skill is a role, like the SDR; its workflows live under it (cold
// outreach, lead form follow-up, stale proposal follow-up, appointment booking).
const KIND = { workflow: "Workflow", skill: "Skill", campaign: "Campaign", artifact: "Artifact" };
const PLURAL = { workflow: "Workflows", skill: "Skills", campaign: "Campaigns", artifact: "Artifacts" };
// line icons for the three options (the icon font holds only the rail's names)
const ICON = {
  run: '<path d="M8 5.5v13l10.5-6.5z"/>',
  add: '<path d="M12 5v14M5 12h14"/>',
  open: '<path d="M3.5 7.5a2 2 0 0 1 2-2h4l2 2.5h7a2 2 0 0 1 2 2v7.5a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z"/>',
  back: '<path d="M14.5 6l-6 6 6 6"/>',
  next: '<path d="M9.5 6l6 6-6 6"/>',
};
const line = (d) => `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>`;

function ago(iso) {
  if (!iso) return "";
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
  if (days <= 0) return "today";
  if (days === 1) return "yesterday";
  return days < 30 ? `${days} days ago` : new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function mountButterfly() {
  const btn = document.getElementById("butterfly");
  if (!btn) return;
  const mark = BRAND["google-organic"];
  btn.innerHTML = `<svg viewBox="${mark.viewBox}" width="30" height="30" aria-hidden="true">${mark.logo}</svg>`;
  const menu = el("div", { class: "bfly-menu", role: "menu", hidden: true });
  btn.after(menu);
  let data = null;      // the skills and the projects, asked for once each time the menu opens
  let kind = null;      // the tab the project list shows: the kind he last worked on, until he picks another
  let runKind = "skill"; // the tab the run list shows: skills first, then workflows

  function close() {
    menu.hidden = true;
    btn.setAttribute("aria-expanded", "false");
  }
  function open() {
    data = null;
    menu.hidden = false;
    btn.setAttribute("aria-expanded", "true");
    root();
  }
  async function load() {
    if (!data) data = await api.get("/api/butterfly");
    return data;
  }
  function head(title) {
    return el("div", { class: "bfly-head" },
      el("button", { class: "bfly-back", type: "button", title: "Back", html: line(ICON.back), onclick: root }),
      el("span", {}, title));
  }
  function fail(e) {
    toast((e.errors || [String(e)]).join(" "), true);
  }
  async function send(path, body, said) {
    try {
      const r = await api.post(path, body);
      close();
      toast(r.dry ? "Test mode: nothing was opened." : said(r));
      return r;
    } catch (e) {
      fail(e);
      return null;
    }
  }
  const saidOpen = (r) => (r.resume ? "Opening the chat in VS Code." : "A new chat is opening in VS Code with the first line typed. Press Enter there.");

  function option(icon, title, sub, go) {
    return el("button", { class: "bfly-opt", type: "button", role: "menuitem", onclick: go },
      el("span", { class: "bfly-ico", html: line(icon) }),
      el("span", { class: "bfly-txt" }, el("span", { class: "t" }, title), el("span", { class: "s" }, sub)),
      el("span", { class: "bfly-next", html: line(ICON.next) }));
  }

  function root() {
    clear(menu);
    append(menu, [
      option(ICON.run, "Run a skill", "A skill, or one of its workflows; a new chat opens with it typed", skills),
      option(ICON.add, "New project", "A workflow, a skill, a campaign, or an artifact", fresh),
      option(ICON.open, "Work on a project", "Back into its chat", projects),
    ]);
  }

  function row(title, sub, tag, go) {
    return el("button", { class: "bfly-row", type: "button", onclick: go },
      el("span", { class: "bfly-txt" }, el("span", { class: "t" }, title), sub ? el("span", { class: "s" }, sub) : null),
      tag ? el("span", { class: "tag faint" }, tag) : null);
  }

  async function skills() {
    clear(menu);
    const chips = el("div", { class: "bfly-chips" });
    const list = el("div", { class: "bfly-list" }, el("div", { class: "bfly-note" }, "Loading"));
    append(menu, [head("Run a skill"), chips, list]);
    let d;
    try { d = await load(); } catch (e) { clear(list); fail(e); return; }
    function draw() {
      clear(chips);
      append(chips, ["skill", "workflow"].map((k) => el("button", { class: "chip" + (k === runKind ? " is-on" : ""), type: "button",
        onclick: () => { runKind = k; draw(); } }, `${PLURAL[k]} ${d.skills.filter((s) => s.kind === k).length}`)));
      clear(list);
      const rows = d.skills.filter((s) => s.kind === runKind);
      if (!rows.length) append(list, [el("div", { class: "bfly-note" }, `No ${PLURAL[runKind].toLowerCase()} written yet.`)]);
      append(list, rows.map((s) => row(s.label, s.line, null,
        () => send("/api/butterfly/open", { skill: s.name }, saidOpen))));
    }
    draw();
  }

  async function projects() {
    clear(menu);
    const chips = el("div", { class: "bfly-chips" });
    const list = el("div", { class: "bfly-list" }, el("div", { class: "bfly-note" }, "Loading"));
    append(menu, [head("Work on a project"), chips, list]);
    let d;
    try { d = await load(); } catch (e) { clear(list); fail(e); return; }
    if (!kind) kind = (d.projects.find((p) => p.chat) || {}).kind || "campaign";   // rows with a chat come first, newest on top
    function draw() {
      clear(chips);
      append(chips, Object.keys(PLURAL).map((k) => el("button", { class: "chip" + (k === kind ? " is-on" : ""), type: "button",
        onclick: () => { kind = k; draw(); } }, `${PLURAL[k]} ${d.projects.filter((p) => p.kind === k).length}`)));
      clear(list);
      const rows = d.projects.filter((p) => p.kind === kind);
      if (!rows.length) append(list, [el("div", { class: "bfly-note" }, `No ${PLURAL[kind].toLowerCase()} yet.`)]);
      append(list, rows.map((p) => row(p.name, p.line, p.chat ? "chat " + ago(p.when) : "no chat yet",
        () => send("/api/butterfly/open", { id: p.id }, saidOpen))));
    }
    draw();
  }

  async function fresh() {
    clear(menu);
    let pick = "workflow";
    const chips = el("div", { class: "bfly-chips" });
    const name = el("input", { type: "text", placeholder: "Name", "aria-label": "Name", autocomplete: "off" });
    const what = el("input", { type: "text", placeholder: "One line: what we are building", "aria-label": "What we are building", autocomplete: "off" });
    const channel = el("select", { "aria-label": "Channel" }, el("option", { value: "" }, "Channel it runs on"));
    const channelField = el("div", { class: "field" }, channel);
    const go = el("button", { class: "btn small", type: "submit" }, "Open the chat");
    const form = el("form", { class: "bfly-form" }, chips, el("div", { class: "field" }, name), el("div", { class: "field" }, what), channelField,
      el("div", { class: "bfly-actions" }, go));
    function draw() {
      clear(chips);
      append(chips, Object.keys(KIND).map((k) => el("button", { class: "chip" + (k === pick ? " is-on" : ""), type: "button",
        onclick: () => { pick = k; draw(); } }, KIND[k])));
      channelField.hidden = pick !== "campaign";
    }
    draw();
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      go.disabled = true;
      const r = await send("/api/butterfly/new", { kind: pick, name: name.value.trim(), line: what.value.trim(), channel: channel.value }, saidOpen);
      if (!r) go.disabled = false;
    });
    append(menu, [head("New project"), form]);
    name.focus();
    try {
      const d = await load();
      append(channel, d.channels.map((c) => el("option", { value: c.id }, c.label)));
    } catch (e) { fail(e); }
  }

  btn.addEventListener("click", () => (menu.hidden ? open() : close()));
  document.addEventListener("mousedown", (e) => { if (!menu.hidden && !menu.contains(e.target) && !btn.contains(e.target)) close(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !menu.hidden) close(); });
}
