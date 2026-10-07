// The journey map on the Pipeline page (Jonathan, 2026-10-01: "an interactive icon map showing the flow of how a
// customer can go from unaware to aware to won"). Left to right: the trades who don't know us yet, the acquisition
// channels (top of the funnel, in his order, from projects/crm/journey.json), then the deal stages from the board. A
// channel with a Live campaign is in its colors; one with nothing live is grayed out.
// A click on a channel opens its card: what is happening now, what it should produce, its numbers as one horizontal
// bar (Organic shows its landing pages instead; Cold calling shows today's quota), the tasks to get it running, and the
// names of its campaigns. The card's Artifacts button opens the deeper view: everything the channel needs to work
// (Google Ads: per campaign, the page's HTML, its current copy, and every earlier copy; LinkedIn: the message copy;
// cold calling: the script, objections, qualifying questions), each opened read-only beside the list.
// A click on a stage lists the deals sitting in it.
import { el, money } from "../util.js";
import { api } from "../api.js";
import { openModal, toast } from "./modal.js";
import { navigate } from "../router.js";
import { BRAND } from "../views/channels.js";
import { artifactViewer, groupBox } from "./artifact-view.js";

const NS = "http://www.w3.org/2000/svg";
function s(tag, attrs = {}, ...kids) {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== null && v !== undefined) n.setAttribute(k, v);
  for (const k of kids) if (k !== null && k !== undefined) n.append(k);
  return n;
}

// Marks for the channels the Channels page has no brand mark for (24 x 24, a tile in the channel's color). The two
// LinkedIn channels (Jonathan, 2026-10-01): the ads carry a dollar sign, the InMail a message bubble, each with a small
// LinkedIn "in" badge in the corner.
const IN_BADGE = '<rect x="13.5" y="13.5" width="9" height="9" rx="2" fill="#FFFFFF" stroke="#0A66C2" stroke-width="1"/>' +
  '<circle cx="15.6" cy="15.7" r=".75" fill="#0A66C2"/><rect x="14.95" y="16.9" width="1.3" height="4" fill="#0A66C2"/>' +
  '<path fill="#0A66C2" d="M17.4 16.9h1.25v.6c.3-.45.85-.75 1.5-.75 1.2 0 1.6.8 1.6 1.9v2.25h-1.3v-2c0-.55-.15-.95-.65-.95s-.85.4-.85 1v1.95H17.4z"/>';
export const MARKS = {
  "google-ads": BRAND["google-ads"],
  "linkedin-ads": { color: "#0A66C2", logo: '<rect width="24" height="24" rx="4" fill="#0A66C2"/><path fill="none" stroke="#FFFFFF" stroke-width="1.7" stroke-linecap="round" d="M12.8 8c-.6-.9-1.5-1.4-2.8-1.4-1.6 0-2.8.8-2.8 2.1 0 1.4 1.3 1.8 2.9 2.2 1.7.4 2.9.9 2.9 2.3 0 1.3-1.2 2.2-3 2.2-1.3 0-2.4-.5-3-1.5M10 4.6v14.2"/>' + IN_BADGE },
  "linkedin-inmail": { color: "#0A66C2", logo: '<rect width="24" height="24" rx="4" fill="#0A66C2"/><path fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linejoin="round" d="M4.5 5h11a1.5 1.5 0 0 1 1.5 1.5v6a1.5 1.5 0 0 1-1.5 1.5H9.5L6 17v-3H4.5A1.5 1.5 0 0 1 3 12.5v-6A1.5 1.5 0 0 1 4.5 5z"/><circle cx="7" cy="9.5" r="1" fill="#FFFFFF"/><circle cx="10" cy="9.5" r="1" fill="#FFFFFF"/><circle cx="13" cy="9.5" r="1" fill="#FFFFFF"/>' + IN_BADGE },
  organic: BRAND["google-organic"],
  cold: BRAND.cold,
  "cold-email": { color: "#E8710A", logo: '<rect width="24" height="24" rx="5" fill="#E8710A"/><path fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linejoin="round" d="M5 11.6 18.6 5.6l-3.4 13-3.6-3.9-3.4 2.2.6-4.6z"/><path fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round" d="M11.6 14.7 18.6 5.6"/>' },
  youtube: { color: "#FF0000", logo: '<rect width="24" height="24" rx="5" fill="#FF0000"/><path fill="#FFFFFF" d="M10 8.2v7.6l6.2-3.8z"/>' },
  meta: { color: "#0866FF", logo: '<rect width="24" height="24" rx="5" fill="#0866FF"/><path fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linejoin="round" d="M4.5 14c0-3.6 1.8-6.4 3.6-6.4S11 10.4 12 12.2c1-1.8 2.2-4.6 3.9-4.6s3.6 2.8 3.6 6.4c0 1.4-.7 2.2-1.8 2.2-1.6 0-2.7-2.2-3.7-4-1 1.8-2.1 4-3.9 4s-2.9-2.2-3.9-4c-1 1.8-1.9 4-3.6 4-1.1 0-1.6-.8-1.6-2.2z"/>' },
  "organic-social": { color: "#9334E6", logo: '<rect width="24" height="24" rx="5" fill="#9334E6"/><rect x="8" y="4.5" width="8" height="15" rx="1.6" fill="none" stroke="#FFFFFF" stroke-width="1.6"/><path fill="#FFFFFF" d="M10.8 9.6v4.8l3.8-2.4z"/>' },
};
const GENERIC = { color: "#616161", logo: '<rect width="24" height="24" rx="5" fill="#616161"/>' };
// The open stages from the board, in order (Contacted added 2026-10-03: the map started at Booked call, so most of the
// open pipeline, the deals in conversation, never showed on it).
const STAGES = [
  { stage: "Contacted", label: "Contacted", icon: '<path d="M4 5h16v11H9l-4 3v-3H4z"/><path d="M8 9.5h8M8 12.5h5"/>' },
  { stage: "Booked", label: "Booked call", icon: '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 9h16M8 3v4M16 3v4"/><path d="M9 14.5l2 2 4-4"/>' },
  { stage: "Held", label: "Held", icon: '<rect x="3" y="7" width="12" height="10" rx="2"/><path d="M15 10.5l6-3.5v10l-6-3.5"/>' },
  { stage: "Proposed", label: "Proposed", icon: '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>' },
  { stage: "Won", label: "Won", icon: '<path d="M8 4h8v5a4 4 0 0 1-8 0z"/><path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8.5 20h7M10 17h4"/>' },
];
const PEOPLE = '<circle cx="9" cy="8" r="3"/><path d="M3 19c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.4"/><path d="M15.5 13.6c3 .1 5.5 2.3 5.5 5.4"/>';

const num = (v) => (v === null || v === undefined || v === "" ? "–" : Number(v).toLocaleString("en-US"));
const pct = (v) => (v === null || v === undefined ? "–" : `${v}%`);
const firstLines = (text, n) => String(text || "").split(/\n+/).map((x) => x.replace(/^\s*[-*]\s*/, "").replace(/^\[[ x]\]\s*/i, "").trim()).filter(Boolean).slice(0, n);
const markOf = (node) => MARKS[node.key] || GENERIC;

// The full journey (with the artifacts) is read once, the first time a card opens.
let fullJourney = null;
function loadFull() {
  if (!fullJourney) fullJourney = api.get("/api/journey").catch((e) => { fullJourney = null; throw e; });
  return fullJourney;
}

// One node's state: its campaigns across its sources, whether any is live, and the first CRM channel row behind it.
function nodeState(node, channels, groups) {
  let ch = null;
  const camps = [];
  for (const src of node.sources || []) {
    ch = ch || channels.find((c) => c.name === src.channel) || null;
    const g = groups.find((x) => x.channel === src.channel);
    const re = src.pick ? new RegExp(src.pick, "i") : null;
    camps.push(...((g && g.campaigns) || []).filter((c) => !re || re.test(c.Name || "")));
  }
  const live = camps.filter((c) => c.Status === "Live");
  return { ch, camps, live, running: live.length > 0 };
}

// The numbers for one channel, as label/value pairs for the horizontal bar.
function kpis(node, st) {
  const ch = st.ch || {};
  const booked = st.ch ? num(Math.max(ch.booked || 0, ch.leads_booked || 0)) : "–";
  switch (node.key) {
    case "google-ads": case "meta": return [["Impressions", num(ch.impressions)], ["Clicks", num(ch.clicks)], ["Leads", num(ch.leads)], ["Booked", booked], ["Spend", ch.spend ? money(ch.spend) : "–"]];
    case "cold": return [["Dials", num(ch.dials)], ["Connects", num(ch.connects)], ["Connect rate", pct(ch.rates && ch.rates.connect)], ["Booked", num(ch.booked)], ["Held", num(ch.held)]];
    case "linkedin-inmail": {
      const m = ch.messaging || {};
      return [["Requests", num(m.requests)], ["Accepted", num(m.accepted)], ["Replied", num(m.replied)], ["Reply rate", pct(m.reply_rate)], ["Booked", num(m.booked)]];
    }
    case "linkedin-ads": return [["Impressions", "–"], ["Clicks", "–"], ["Leads", "–"], ["Booked", "–"], ["Campaigns live", num(st.live.length)]];
    case "cold-email": return [["Sent", "–"], ["Replies", "–"], ["Contacted", num(ch.contacted)], ["Booked", num(ch.booked)]];
    case "organic-social": return [["Posts", "–"], ["Views", "–"], ["Leads", num(ch.leads)], ["Booked", booked]];
    default: return [["Leads", num(ch.leads)], ["Booked", booked], ["Held", num(ch.held)], ["Won", num(ch.won)]];
  }
}

function logoBox(node, size) {
  const mark = markOf(node);
  const b = el("span", { class: "ch-logo", "aria-hidden": "true", style: `width:${size}px;height:${size}px` });
  b.innerHTML = `<svg viewBox="${mark.viewBox || "0 0 24 24"}" width="${size}" height="${size}">${mark.logo}</svg>`;
  return b;
}
const statusTag = (stt) => el("span", { class: "tag" + (stt === "Live" ? " won" : stt === "Paused" ? " lost" : " faint") }, stt || "Planned");

// ---- the card

function openChannel(node, st) {
  const planned = st.camps.filter((c) => c.Status !== "Live");
  const notes = st.ch && st.ch.notes ? st.ch.notes.split(/\.\s+/).map((x) => x.replace(/\.$/, "")).filter((x) => x && !/workflow to be defined/i.test(x)).slice(0, 2).map((x) => x + ".").join(" ") : "";
  const now = st.running
    ? `${st.live.length} campaign${st.live.length === 1 ? "" : "s"} live${planned.length ? `, ${planned.length} not running yet` : ""}.`
    : st.camps.length ? `Nothing live. ${st.camps.length} campaign${st.camps.length === 1 ? "" : "s"} waiting: ${[...new Set(planned.map((c) => (c.Status || "Planned").toLowerCase()))].join(" or ")}.`
      : "Not set up. No campaign on this channel yet.";
  // one line per kind of goal: the Google Ads campaigns share one goal with only the page changing
  const byKind = new Map();
  for (const line of (st.live.length ? st.live : st.camps).flatMap((c) => firstLines(c.Outcomes || c.Objective, 1))) {
    const k = line.replace(/\/[\w-]+\//g, "/");
    byKind.set(k, byKind.has(k) ? { line: byKind.get(k).line, n: byKind.get(k).n + 1 } : { line, n: 1 });
  }
  const goals = (node.produce || []).concat([...byKind.values()].slice(0, 4).map((g) => (g.n > 1 ? g.line.replace(/from \/[\w-]+\//, "from each service page") : g.line)));

  // Cold calling: today's quota, read when the card opens
  const quota = node.quota ? el("div", { class: "jr-quota" }, el("div", { class: "muted", style: "font-size:13px" }, "Reading today's dials...")) : null;
  if (quota) {
    api.queue({ limit: 1 }).then((q) => {
      const done = q.dialed_today || 0, target = q.target || 22;
      quota.replaceChildren(
        el("div", { class: "row" }, el("span", { class: "strong" }, `Today: ${done} of ${target} dials`), el("span", { class: "grow" }),
          el("span", { class: "tag " + (done >= target ? "won" : "faint") }, done >= target ? "Quota met" : `${target - done} to go`)),
        el("div", { class: "progress" + (done >= target ? " full" : "") }, el("b", { style: `width:${Math.min(100, Math.round((done / target) * 100))}%` })));
    }).catch(() => quota.replaceChildren(el("div", { class: "muted" }, "Could not read today's dials.")));
  }

  // Organic: the landing pages instead of the numbers
  const pages = node.show === "pages" ? el("div", { class: "muted", style: "font-size:13px" }, "Reading the pages...") : null;
  if (pages) {
    loadFull().then((j) => {
      const full = (j.nodes || []).find((n) => n.key === node.key) || {};
      const g = (full.artifacts || []).find((x) => x.kind === "site-pages");
      const list = (g && g.pages) || [];
      pages.replaceChildren(list.length ? el("ul", { class: "jr-camps" }, ...list.map((p) => el("li", {},
        el("span", { class: "grow" }, p.name), el("a", { class: "link", href: p.url, target: "_blank", rel: "noopener" }, "Open")))) : el("div", { class: "muted" }, "No pages found."));
    }).catch(() => pages.replaceChildren(el("div", { class: "muted" }, "Could not read the pages.")));
  }

  const tasks = node.tasks || [];
  const taskList = el("ul", { class: "jr-tasks" }, ...tasks.map((t, i) => {
    const box = el("input", { type: "checkbox", checked: t.done ? true : null, "aria-label": t.text });
    box.addEventListener("change", async () => {
      box.disabled = true;
      try { await api.post("/api/journey/task", { node: node.key, i, done: box.checked }); t.done = box.checked; li.classList.toggle("done", box.checked); }
      catch (e) { box.checked = !box.checked; toast((e.errors || [String(e)]).join(" "), true); }
      box.disabled = false;
    });
    const li = el("li", { class: t.done ? "done" : "" }, el("label", {}, box, el("span", { class: "grow" }, t.text)), t.who ? el("span", { class: "tag faint" }, t.who) : null);
    return li;
  }));
  const openTasks = tasks.filter((t) => !t.done).length;

  let modal;
  const body = el("div", { class: "stack jr-pop" },
    el("div", { class: "row" }, logoBox(node, 40),
      el("div", { class: "grow" }, el("div", { class: "label" }, "Acquisition channel"), el("h2", {}, node.label)),
      el("span", { class: "tag " + (st.running ? "won" : "faint") }, st.running ? "Running" : "Not running")),
    el("div", {}, el("div", { class: "label" }, "What is happening now"), el("div", {}, now), notes ? el("div", { class: "muted", style: "font-size:13px" }, notes) : null),
    el("div", {}, el("div", { class: "label" }, "What it should produce"),
      goals.length ? el("ul", { class: "jr-goals" }, ...goals.map((x) => el("li", {}, x))) : el("div", { class: "muted" }, "No outcome written yet."), quota),
    pages ? el("div", {}, el("div", { class: "label" }, "Landing pages"), pages)
      : el("div", {}, el("div", { class: "label" }, "Numbers"), el("div", { class: "jr-bar" }, ...kpis(node, st).map(([k, v]) => el("div", { class: "jr-kpi" }, el("div", { class: "label" }, k), el("div", { class: "v num" }, v))))),
    el("div", {}, el("div", { class: "label" }, st.running ? `To do (${openTasks} open)` : `To get it running (${openTasks} open)`),
      tasks.length ? taskList : el("div", { class: "muted" }, node.quota ? "Nothing to set up. Meet the daily quota." : "No tasks written yet.")),
    el("div", {}, el("div", { class: "label" }, `Campaigns (${st.camps.length})`),
      st.camps.length ? el("ul", { class: "jr-camps" }, ...st.camps.map((c) => el("li", {}, el("span", { class: "grow" }, c.Name), statusTag(c.Status))))
        : el("div", { class: "muted" }, "None yet.")),
    el("div", { class: "row" },
      el("button", { class: "btn quiet small", type: "button", onclick: () => { modal.close(); openArtifacts(node, st); } }, "Artifacts"),
      el("span", { class: "grow" }),
      st.ch ? el("button", { class: "btn small", type: "button", onclick: () => { modal.close(); navigate(`#/channel/${encodeURIComponent(st.ch.name)}`); } }, "Open the channel") : null));
  modal = openModal(body);
}

// ---- the deeper view: the artifacts, a list on the left and the one opened on the right

function openArtifacts(node, st) {
  const v = artifactViewer();
  const list = el("div", { class: "jr-alist" }, el("div", { class: "muted" }, "Reading the artifacts..."));
  let modal;
  const body = el("div", { class: "stack jr-art" },
    el("div", { class: "row" }, logoBox(node, 32),
      el("div", { class: "grow" }, el("div", { class: "label" }, "Artifacts"), el("h2", {}, node.label)),
      el("button", { class: "btn quiet small", type: "button", onclick: () => { modal.close(); openChannel(node, st); } }, "Back to the card")),
    el("div", { class: "jr-split" }, list, v.viewer));
  modal = openModal(body, { wide: true });
  loadFull().then((j) => {
    const full = (j.nodes || []).find((n) => n.key === node.key) || { artifacts: [] };
    const groups = full.artifacts || [];
    list.replaceChildren(...(groups.length ? groups.map((g) => groupBox(g, v)) : [el("div", { class: "muted" }, "No artifacts listed for this channel.")]));
  }).catch((e) => list.replaceChildren(el("div", { class: "down" }, `Could not read the artifacts: ${(e.errors || [String(e)]).join(" ")}`)));
}

function openStage(def, col) {
  const deals = (col && col.deals) || [];
  openModal(el("div", { class: "stack jr-pop" },
    el("div", {}, el("div", { class: "label" }, "Stage"), el("h2", {}, `${def.label} · ${deals.length}`)),
    deals.length ? el("ul", { class: "jr-camps" }, ...deals.map((d) => el("li", {}, el("span", { class: "grow" }, d.company_name || d.Deal),
      el("span", { class: "muted num" }, money(d.Value, { mo: true }))))) : el("div", { class: "muted" }, "No deal in this stage now."),
    el("div", { class: "muted", style: "font-size:12px" }, "The same deals sit in the board below.")));
}

// ---- the map

export function journeyMap(channelsData, pipeline, journey) {
  const channels = (channelsData && channelsData.channels) || [];
  const groups = (channelsData && channelsData.campaign_groups) || [];
  const NODES = (journey && journey.nodes) || [];
  const W = 1100, top = 64, step = 62, H = top + step * Math.max(0, NODES.length - 1) + 36;
  const midY = top + (step * Math.max(0, NODES.length - 1)) / 2;
  const chipX = 250, chipW = 210, chipH = 46;
  const stageX = [600, 715, 830, 945, 1060];
  const svg = s("svg", { viewBox: `0 0 ${W} ${H}`, class: "jr-svg", role: "group", "aria-label": "How a customer goes from unaware to won" });
  const lines = s("g", { class: "jr-lines" });
  svg.append(lines);

  // column headings
  [["Unaware", 80], ["Aware: the channels", chipX + chipW / 2], ...STAGES.map((d, i) => [d.stage, stageX[i]])]
    .forEach(([t, x]) => svg.append(s("text", { x, y: 22, class: "jr-head", "text-anchor": "middle" }, t)));

  // unaware
  const un = s("g", { class: "jr-unaware" }, s("circle", { cx: 80, cy: midY, r: 34 }));
  const unIcon = s("svg", { x: 80 - 16, y: midY - 16, width: 32, height: 32, viewBox: "0 0 24 24", class: "jr-ico" });
  unIcon.innerHTML = PEOPLE;
  un.append(unIcon, s("text", { x: 80, y: midY + 54, "text-anchor": "middle", class: "jr-label" }, "Trades who"), s("text", { x: 80, y: midY + 70, "text-anchor": "middle", class: "jr-label" }, "don't know us"));
  svg.append(un);

  // stages, with the line that runs through them
  const cols = (pipeline && pipeline.columns) || [];
  const bookedLeft = stageX[0] - 32;
  lines.append(s("path", { d: `M${stageX[0]} ${midY} H${stageX[STAGES.length - 1]}`, class: "jr-spine" }));
  STAGES.forEach((def, i) => {
    const col = cols.find((c) => c.stage === def.stage);
    const n = col ? col.count : 0;
    const g = s("g", { class: "jr-stage" + (n ? " has" : ""), tabindex: "0", role: "button", "aria-label": `${def.label}: ${n} deal${n === 1 ? "" : "s"}` },
      s("circle", { cx: stageX[i], cy: midY, r: 32 }));
    const ic = s("svg", { x: stageX[i] - 12, y: midY - 22, width: 24, height: 24, viewBox: "0 0 24 24", class: "jr-ico" });
    ic.innerHTML = def.icon;
    g.append(ic, s("text", { x: stageX[i], y: midY + 18, "text-anchor": "middle", class: "jr-count" }, String(n)),
      s("text", { x: stageX[i], y: midY + 52, "text-anchor": "middle", class: "jr-label" }, def.label));
    const open = () => openStage(def, col);
    g.addEventListener("click", open);
    g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } });
    svg.append(g);
  });

  // channels
  let running = 0;
  NODES.forEach((node, i) => {
    const st = nodeState(node, channels, groups);
    if (st.running) running += 1;
    const mark = markOf(node);
    const y = top + step * i;
    const color = mark.color || "#616161";
    const open = (node.tasks || []).filter((t) => !t.done).length;
    // the unaware audience reaches every channel; a running channel carries on to a booked call
    lines.append(s("path", { d: `M114 ${midY} C${(114 + chipX) / 2} ${midY}, ${(114 + chipX) / 2} ${y}, ${chipX} ${y}`, class: "jr-in" + (st.running ? "" : " off") }));
    lines.append(s("path", { d: `M${chipX + chipW} ${y} C${(chipX + chipW + bookedLeft) / 2} ${y}, ${(chipX + chipW + bookedLeft) / 2} ${midY}, ${bookedLeft} ${midY}`,
      class: "jr-out" + (st.running ? "" : " off"), style: st.running ? `stroke:${color}` : null }));
    const g = s("g", { class: "jr-node" + (st.running ? " on" : " off"), tabindex: "0", role: "button", "aria-label": `${node.label}: ${st.running ? "running" : "not running"}` },
      s("rect", { class: "jr-chip", x: chipX, y: y - chipH / 2, width: chipW, height: chipH, rx: 12, style: st.running ? `stroke:${color}` : null }));
    const logo = s("svg", { x: chipX + 10, y: y - 14, width: 28, height: 28, viewBox: mark.viewBox || "0 0 24 24", class: "jr-logo" });
    logo.innerHTML = mark.logo;
    g.append(logo,
      s("text", { x: chipX + 48, y: y - 2, class: "jr-name" }, node.label),
      s("text", { x: chipX + 48, y: y + 14, class: "jr-state" },
        (st.running ? `Running · ${st.live.length} live` : st.camps.length ? "Not running" : "Not set up") + (open ? ` · ${open} to do` : "")));
    const go = () => openChannel(node, st);
    g.addEventListener("click", go);
    g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
    svg.append(g);
  });

  return el("section", { class: "panel jr", "aria-label": "Journey" },
    el("div", { class: "row" },
      el("div", { class: "grow" }, el("div", { class: "label" }, "Journey"), el("h2", {}, "From unaware to won"),
        el("div", { class: "muted", style: "font-size:13px" }, `${running} of ${NODES.length} channels running. In color: a campaign is live. Gray: nothing live. Click any icon.`))),
    el("div", { class: "jr-wrap" }, svg));
}
