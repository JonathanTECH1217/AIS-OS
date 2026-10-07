// Campaign rows (2026-09-29, Jonathan: "all campaigns should be listed underneath the channels"; a click opens the
// campaign in place with the tasks and the outcomes we want). One shape on Channels (every campaign, under its channel)
// and on each channel's page (its own campaigns). The server's brief carries the headline, the counted numbers, the
// typed outcomes, and the task groups: typed tasks first, then what the CRM reads itself (directories, builds, Ads screen).
import { el } from "../util.js";
import { api } from "../api.js";
import { toast, openModal } from "./modal.js";
import { navigate } from "../router.js";
import { openRecordForm, campaignSpec, listingSpec, freeCampaignSpec } from "./record-form.js";

const CHEVRON = '<svg viewBox="0 0 24 24" width="20" height="20"><path d="M7 10l5 5 5-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const DONE = '<svg viewBox="0 0 24 24" width="20" height="20"><circle cx="12" cy="12" r="9" fill="currentColor"/><path d="M8 12.4l2.7 2.7L16.2 9.6" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const OPEN = '<svg viewBox="0 0 24 24" width="20" height="20"><circle cx="12" cy="12" r="8.4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>';

// which campaigns are open, kept across a reload after a save
const opened = new Set();

const svg = (html, cls) => el("span", { class: cls, "aria-hidden": "true", html });

function statusTag(s) {
  return el("span", { class: "tag" + (s === "Live" ? " won" : s === "Paused" ? "" : " faint") }, s || "Planned");
}

function taskTag(t) {
  const s = t.status;
  if (!s) return null;
  const cls = t.done ? " won" : /needs fix|changed/i.test(s) ? " lost" : /^(open|to do|locked|request found)$/i.test(s) ? " faint" : "";
  return el("span", { class: "tag" + cls }, s);
}

// tick a typed task: add or drop "[x] " on its line of the Tasks field
async function toggleTyped(c, t, onSaved) {
  const lines = (c.Tasks || "").split(/\r?\n/);
  const ln = lines[t.line] || "";
  const bare = ln.replace(/^\s*(?:[-*•]\s+)?(?:\[[ xX]\]\s*)?/, "");
  lines[t.line] = t.done ? bare : `[x] ${bare}`;
  try {
    await api.saveRecord("Campaigns", { id: c.id, Tasks: lines.join("\n") });
    toast(t.done ? "Marked open." : "Done.");
    onSaved();
  } catch (err) {
    toast(err.errors ? err.errors.join(" ") : "Could not save.");
  }
}

function taskRow(c, t, onSaved) {
  const clickable = t.typed || t.table || t.href;
  const li = el("li", { class: "camp-task" + (t.done ? " done" : "") + (clickable ? " clickable" : ""), tabindex: clickable ? "0" : null,
    title: t.typed ? (t.done ? "Click to mark open" : "Click to mark done") : null },
    svg(t.done ? DONE : OPEN, "camp-check" + (t.done ? " up" : "")),
    el("div", { class: "camp-task-text" }, el("div", {}, t.text), t.sub ? el("div", { class: "sub" }, t.sub) : null),
    t.typed ? null : taskTag(t));
  const go = () => {
    if (t.typed) toggleTyped(c, t, onSaved);
    else if (t.table === "Listings") openRecordForm({ table: "Listings", title: t.text, onSaved, spec: listingSpec(),
      record: { ...t.record, "NAP matches": t.record && t.record["NAP matches"] ? "true" : "" } });
    // a free-campaign delivery (2026-10-03): its stage from Built to Review left
    else if (t.table === "Free campaigns") openRecordForm({ table: "Free campaigns", title: t.text, onSaved, spec: freeCampaignSpec(), record: t.record });
    else if (t.href) navigate(t.href);
  };
  if (clickable) {
    li.addEventListener("click", go);
    li.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
  }
  return li;
}

function body(c, { onSaved, onChannelPage, extra }) {
  const b = c.brief || {};
  // extra: the Google Ads page puts the campaign's approve-and-edit controls here, in place of the read-only checklist
  const controls = extra ? extra(c) : null;
  const outcomes = el("div", { class: "camp-sec" }, el("div", { class: "label" }, "Outcomes we want"),
    b.outcomes && b.outcomes.length ? el("ul", { class: "camp-outcomes" }, ...b.outcomes.map((o) => el("li", {}, o)))
      : el("div", { class: "muted", style: "font-size:13px" }, "None written yet. Edit campaign, one per line."));
  const stands = el("div", { class: "camp-sec" }, el("div", { class: "label" }, "Where it stands"),
    el("div", { class: "camp-measures" }, ...(b.measures || []).map((m) => el("div", { class: "stat" },
      el("div", { class: "label" }, m.label), el("div", { class: "v num" }, String(m.value)),
      m.sub ? el("div", { class: "muted", style: "font-size:11px" }, m.sub) : null))));
  const groups = (b.groups || []).filter((g) => !(controls && g.kind === "ads")).map((g) => el("div", { class: "camp-sec" },
    el("div", { class: "label" }, g.title, el("span", { class: "muted" }, ` · ${g.items.filter((i) => i.done).length} of ${g.items.length} done`)),
    g.note ? el("div", { class: "muted", style: "font-size:12px" }, g.note) : null,
    el("ul", { class: "camp-tasks" }, ...g.items.map((t) => taskRow(c, t, onSaved)))));
  const ch = { id: c.channel_id, label: c.channel_label };
  return el("div", { class: "camp-body" },
    c.Objective ? el("div", { class: "camp-why" }, c.Objective) : null,
    el("div", { class: "camp-cols" }, outcomes, stands),
    controls,
    ...(groups.length || controls ? groups : [el("div", { class: "camp-sec" }, el("div", { class: "label" }, "Tasks"),
      el("div", { class: "muted", style: "font-size:13px" }, "None written yet. Edit campaign, one per line."))]),
    c.Notes ? el("div", { class: "camp-sec" }, el("div", { class: "label" }, "Notes"), el("div", { class: "camp-notes" }, c.Notes)) : null,
    el("div", { class: "row" },
      el("button", { class: "btn quiet small", type: "button", onclick: () => openRecordForm({ table: "Campaigns", title: c.Name, record: c, onSaved, spec: campaignSpec(ch) }) }, "Edit campaign"),
      onChannelPage ? null : el("a", { class: "btn quiet small", href: `#/channel/${encodeURIComponent(c.channel_name)}` }, `Open ${c.channel_label}`)));
}

// ---- Google Ads campaigns (2026-09-29, Jonathan): the closed row shows only impressions, clicks, bookings, CPL, and
// conversion rate; open, it is two cards, the advertising (the ad's headlines and descriptions) and the creative asset
// (a copy of the landing page). On the Google Ads page the advertising card opens the approve-and-edit controls.

// which card is open under a campaign ("ad"), kept across the reload after an edit
const openedPart = new Map();
const PIN_ORDER = (hs) => {
  // the three headlines Google would most likely show first: slot 1, 2, 3 pins, else the next unpinned ones
  const free = hs.filter((h) => !h.pin);
  return [1, 2, 3].map((s) => (hs.find((h) => h.pin === s) || free.shift() || {}).text).filter(Boolean);
};
const num = (v) => (v === null || v === undefined || v === "" ? "–" : Number(v).toLocaleString("en-US"));
const usd = (v) => (v ? `$${Number(v).toLocaleString("en-US")}` : "–");

function adsStats(c) {
  const cell = (label, v) => el("div", { class: "camp-stat" }, el("div", { class: "label" }, label), el("div", { class: "v num" }, v));
  return [cell("Impressions", num(c.Impressions || 0)), cell("Clicks", num(c.Clicks || 0)), cell("Bookings", num(c.booked || 0)),
    cell("CPL", usd(c.cost_per_lead)), cell("Conv. rate", c.conv_rate === null || c.conv_rate === undefined ? "–" : `${c.conv_rate}%`)];
}

const STATE = { approved: "Approved", changed: "Changed since approved", open: "Not approved" };

function adPreview(ad) {
  return el("div", { class: "serp" },
    el("div", { class: "serp-top" }, el("span", { class: "serp-spon" }, "Sponsored"), el("span", { class: "serp-url" }, ad.path)),
    el("div", { class: "serp-h" }, PIN_ORDER(ad.headlines).join(" | ")),
    el("div", { class: "serp-d" }, ad.descriptions[0] || ""));
}

function lines(title, items) {
  return el("div", { class: "camp-sec" }, el("div", { class: "label" }, `${title} (${items.length})`),
    el("ol", { class: "ad-lines" }, ...items.map((t) => el("li", {}, t.pin ? el("span", { class: "pin-tag" }, `slot ${t.pin}`) : null, t.text || t,
      el("span", { class: "len num" }, String((t.text || t).length))))));
}

// the whole page, desktop or phone, from the copy the server took
function openPageCopy(c, shot, onSaved) {
  const box = el("div", { class: "page-copy" });
  const tabs = el("div", { class: "row" });
  const body = el("div", { class: "stack" });
  let view = "desktop";
  function paint(s) {
    tabs.replaceChildren(
      ...["desktop", "phone"].map((v) => el("button", { class: "chip" + (v === view ? " is-on" : ""), type: "button", onclick: () => { view = v; paint(s); } }, v === "desktop" ? "Desktop" : "Phone")),
      el("span", { class: "grow" }),
      el("span", { class: "muted", style: "font-size:12px" }, s.taken_at ? `Copy taken ${new Date(s.taken_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit", timeZone: "America/New_York" })} ET` : ""),
      fresh,
      el("a", { class: "btn quiet small", href: s.url, target: "_blank", rel: "noopener" }, "Open the live page"));
    box.replaceChildren(el("img", { class: "page-img " + view, src: view === "desktop" ? s.desktop : s.phone, alt: `A copy of ${s.url}, ${view}` }));
  }
  const fresh = el("button", { class: "btn quiet small", type: "button" }, "Take a fresh copy");
  fresh.addEventListener("click", async () => {
    fresh.disabled = true; fresh.textContent = "Taking a copy...";
    try { const s = await api.post("/api/page-shot", { url: shot.url || c.brief.ad.page }); c.brief.ad.shot = s; paint(s); toast("Fresh copy taken."); }
    catch (err) { toast((err.errors || [String(err)]).join(" ")); }
    fresh.disabled = false; fresh.textContent = "Take a fresh copy";
  });
  body.append(el("div", {}, el("div", { class: "label" }, "Landing page"), el("h2", {}, c.brief.ad.page.replace(/^https?:\/\//, ""))), tabs, box);
  paint(shot);
  openModal(body, { wide: true });
}

function adsBody(c, { onSaved, onChannelPage, extra }) {
  const ad = c.brief.ad;
  const a = ad.approvals || {};
  const nOk = ["spend", "keywords", "negatives", "ad"].filter((p) => a[p] === "approved").length;
  const detail = el("div", { class: "camp-detail" });
  const adCard = el("div", { class: "asset-card", role: "button", tabindex: "0", "aria-expanded": "false" },
    el("div", { class: "row" }, el("div", { class: "grow" }, el("div", { class: "label" }, "Advertising"), el("h3", {}, "The search ad")),
      el("span", { class: "tag" + (a.ad === "approved" ? " won" : a.ad === "changed" ? " lost" : " faint") }, `Ad: ${STATE[a.ad] || "Not approved"}`)),
    adPreview(ad),
    el("div", { class: "muted", style: "font-size:12px" }, `${ad.headlines.length} headlines · ${ad.descriptions.length} descriptions · ${nOk} of 4 approvals · ${ad.published ? (ad.status === "ENABLED" ? "live on Google" : "built, paused") : "not published"}`),
    el("div", { class: "asset-open" }, onChannelPage && extra ? "See every headline and description, approve, and edit" : "See every headline and description"));
  const shotImg = el("div", { class: "asset-thumb" });
  const pageCard = el("div", { class: "asset-card", role: "button", tabindex: "0" },
    el("div", { class: "row" }, el("div", { class: "grow" }, el("div", { class: "label" }, "Creative asset"), el("h3", {}, "The landing page")),
      el("span", { class: "tag faint" }, ad.page.replace(/^https?:\/\/[^/]+/, "") || "/")),
    shotImg,
    el("div", { class: "asset-open" }, "See the whole page"));
  function paintShot(s) {
    if (s && s.ok) shotImg.replaceChildren(el("img", { src: s.desktop, alt: `The top of ${ad.page}` }));
    else shotImg.replaceChildren(el("div", { class: "muted", style: "font-size:13px" }, s && s.errors ? s.errors.join(" ") : "Taking a copy of the page..."));
  }
  paintShot(ad.shot);
  if (!ad.shot || !ad.shot.ok) {
    api.post("/api/page-shot", { url: ad.page }).then((s) => { ad.shot = s; paintShot(s); }).catch((err) => paintShot({ errors: err.errors || [String(err)] }));
  }
  function showAd(open) {
    adCard.classList.toggle("is-open", open);
    adCard.setAttribute("aria-expanded", open ? "true" : "false");
    if (!open) { detail.replaceChildren(); openedPart.delete(c.id); return; }
    openedPart.set(c.id, "ad");
    const controls = extra ? extra(c) : null;
    detail.replaceChildren(controls || el("div", { class: "stack" },
      lines("Headlines", ad.headlines), lines("Descriptions", ad.descriptions),
      el("div", { class: "row" }, el("button", { class: "btn small", type: "button", onclick: () => { opened.add(c.id); openedPart.set(c.id, "ad"); navigate("#/channel/google-ads"); } }, "Approve and edit on the Google Ads page"))));
  }
  const toggleAd = () => showAd(!adCard.classList.contains("is-open"));
  const openPage = () => (ad.shot && ad.shot.ok ? openPageCopy(c, ad.shot, onSaved) : toast("The copy of the page is still being taken."));
  for (const [card, go] of [[adCard, toggleAd], [pageCard, openPage]]) {
    card.addEventListener("click", go);
    card.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
  }
  if (openedPart.get(c.id) === "ad") showAd(true);
  const b = c.brief;
  const ch = { id: c.channel_id, label: c.channel_label };
  return el("div", { class: "camp-body" },
    el("div", { class: "asset-cards" }, adCard, pageCard),
    detail,
    b.outcomes && b.outcomes.length ? el("details", { class: "camp-more" }, el("summary", {}, "Outcomes we want"),
      el("ul", { class: "camp-outcomes" }, ...b.outcomes.map((o) => el("li", {}, o)))) : null,
    el("div", { class: "row" },
      el("button", { class: "btn quiet small", type: "button", onclick: () => openRecordForm({ table: "Campaigns", title: c.Name, record: c, onSaved, spec: campaignSpec(ch) }) }, "Edit campaign"),
      onChannelPage ? null : el("a", { class: "btn quiet small", href: `#/channel/${encodeURIComponent(c.channel_name)}` }, `Open ${c.channel_label}`)));
}

function campaignRow(c, opts) {
  const b = c.brief || {};
  const isAds = !!b.ad;
  const d = el("details", { class: "camp" + (isAds ? " ads" : "") + (c.Status === "Live" ? "" : " quiet"), open: opened.has(c.id) || null },
    isAds
      ? el("summary", {},
        el("div", { class: "camp-name" }, el("div", { class: "strong" }, c.Name)),
        statusTag(c.Status), ...adsStats(c), svg(CHEVRON, "camp-chev"))
      : el("summary", {},
        el("div", { class: "camp-name" }, el("div", { class: "strong" }, c.Name), c.Objective ? el("div", { class: "sub" }, c.Objective) : null),
        statusTag(c.Status),
        el("div", { class: "camp-head num" }, b.headline || ""),
        el("div", { class: "camp-count muted num" }, b.total ? `${b.done} of ${b.total} tasks` : ""),
        svg(CHEVRON, "camp-chev")));
  let built = false;
  const build = () => { if (!built) { d.append(isAds ? adsBody(c, opts) : body(c, opts)); built = true; } };
  if (d.open) build();
  d.addEventListener("toggle", () => {
    if (d.open) { opened.add(c.id); build(); } else opened.delete(c.id);
  });
  return d;
}

// camps: campaign rows from the server (with brief, channel_id, channel_label, channel_name). extra(c) may return
// more controls for a campaign's open row (the Google Ads page's approvals and ad edits).
export function campaignList(camps, { onSaved, onChannelPage = false, extra = null } = {}) {
  return el("div", { class: "camp-list" }, ...camps.map((c) => campaignRow(c, { onSaved, onChannelPage, extra })));
}
