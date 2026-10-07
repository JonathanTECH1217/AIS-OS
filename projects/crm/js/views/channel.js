// One channel's workspace. Cold call = the call list. Google Ads = campaigns, keywords, landing pages, leads with attribution.
// Every other channel gets the same frame with its campaigns and leads, workflow to be defined. Campaigns sit first,
// right under the numbers, each opening into its outcomes, where it stands, and its tasks (2026-09-29).
import { el, money, fmtDate, fmtDateTime } from "../util.js";
import { api } from "../api.js";
import { logo, brandOf } from "./channels.js";
import { navigate, rerender } from "../router.js";
import { openRecordForm, campaignSpec } from "../components/record-form.js";
import { campaignList } from "../components/campaigns.js";
import { adsTop, adsControls, logPanel } from "./ads.js";
import { sheetTodayPanel } from "../components/sheet-today.js";
import { toast } from "../components/modal.js";
import { fold } from "../components/fold.js";

function tile(label, value, sub, cls = "") {
  return el("div", { class: "kpi" }, el("div", { class: "label" }, label), el("div", { class: "fig num " + cls, style: "font-size:32px" }, value), sub ? el("div", { class: "muted", style: "font-size:13px" }, sub) : null);
}

function table(headers, rows) {
  return el("div", { class: "table-wrap" }, el("table", {}, el("thead", {}, el("tr", {}, ...headers.map((h) => el("th", { class: h.num ? "num" : "" }, h.label || h)))), el("tbody", {}, ...rows)));
}

export async function renderChannel(root, params) {
  const name = params[0];
  // the Google Ads page also carries the publishing controls that were the Ads screen (2026-09-29)
  const [data, ads] = await Promise.all([api.channel(name), name === "google-ads" ? api.get("/api/ads") : null]);
  const ch = data.channel;
  const reload = rerender; // in place, keeping the scroll position
  const isCold = ch.type === "Cold call";
  const isSearch = ch.type === "Google Ads";
  const isOrganic = ch.type === "Google Organic"; // the website (2026-09-27): pages, leads, and no spend
  const hasKeywords = isSearch;
  const spend = ch.spend ? money(ch.spend) + (ch.spend_is_estimate ? " est." : "") : "–";

  const brand = brandOf(ch.name);
  root.append(el("div", { class: "head", style: `--accent:${brand.color}` },
    el("div", { class: "row" }, logo(ch.name, 52),
      el("div", {}, el("div", { class: "label" }, el("a", { href: "#/channels" }, "Channels"), " · ", ch.type, ch.active ? "" : " · not live"),
        el("h1", {}, brand.label || ch.label), el("div", { class: "sub" }, (ch.notes || "").split(". ").slice(0, 2).join(". ")))),
    el("div", { class: "row" },
      isCold ? null : el("button", { class: "btn quiet", type: "button", onclick: () => openRecordForm({ table: "Leads", title: "New lead", onSaved: reload, spec: leadSpec(ch) }) }, "Add lead"),
      el("button", { class: "btn", type: "button", onclick: () => openRecordForm({ table: "Campaigns", title: "New campaign", onSaved: reload, spec: campaignSpec(ch) }) }, "Add campaign"))));

  const fmtN = (v) => (v === null || v === undefined ? "–" : Number(v).toLocaleString("en-US"));
  root.append(el("div", { class: "kpis" },
    isOrganic ? tile("Listings live", String(ch.listings_live || 0), ch.listings ? `of ${ch.listings} directories` : "") : null,
    isCold ? tile("Dials", String(ch.dials)) : isOrganic ? tile("Pages live", String(ch.pages_live || 0), "rows marked Live in Landing pages") : tile("Spend", spend, ch.campaigns_live ? `${ch.campaigns_live} live campaign${ch.campaigns_live === 1 ? "" : "s"}` : `${ch.campaigns} campaign${ch.campaigns === 1 ? "" : "s"}`),
    isCold ? tile("Connects", String(ch.connects), ch.rates.connect === null ? "" : `${ch.rates.connect}% connect rate`) : tile("Impressions", fmtN(ch.impressions), ch.ctr !== null && ch.ctr !== undefined ? `${ch.ctr}% CTR` : ""),
    isCold ? null : tile("Clicks", fmtN(ch.clicks), ch.cpc !== null && ch.cpc !== undefined ? `$${ch.cpc} per click` : ""),
    isCold ? null : tile("Leads", String(ch.leads), ch.cost_per_lead ? `${money(ch.cost_per_lead)} per lead` : (ch.minutes_to_call !== null && ch.minutes_to_call !== undefined ? `${ch.minutes_to_call} min to first call` : "")),
    tile("Booked", String(Math.max(ch.booked, ch.leads_booked)), ch.cost_per_booked ? `${money(ch.cost_per_booked)} per booked` : (ch.rates.booking !== null ? `${ch.rates.booking}% of conversations` : "")),
    tile("Held", String(ch.held), ch.rates.show !== null ? `${ch.rates.show}% show` : ""),
    tile("Won", String(ch.won), ch.revenue ? `${money(ch.revenue)}/mo` : (ch.rates.close !== null ? `${ch.rates.close}% close` : ""), ch.won ? "up" : ""),
    tile("Open", money(ch.open_value), `${ch.open} deal${ch.open === 1 ? "" : "s"}`)));

  // campaigns (2026-09-29): one row each, opening into the outcomes we want, where it stands, and its tasks. The NAP
  // citations directories and the Ads screen's approvals and gates are tasks inside their campaign now.
  if (ads) root.append(el("div", { class: "stack" }, ...adsTop(ads)));
  const adCard = ads ? (c) => { const k = ads.cards.find((x) => x.name === c.Name); return k ? adsControls(k) : null; } : null;
  root.append(el("div", { class: "stack" },
    el("div", {}, el("div", { class: "label" }, "Campaigns"), el("h2", {}, `${data.campaigns.length} campaign${data.campaigns.length === 1 ? "" : "s"}`),
      data.campaigns.length ? el("div", { class: "muted", style: "font-size:13px" }, ads
        ? "Open a campaign for its two cards: the ad (click it to see every headline and description, approve, and edit) and the landing page (click it for a copy of the whole page). CPL is spend over leads; conversion rate is leads over clicks."
        : "Click a campaign to open it: the outcomes we want, where it stands, and its tasks.") : null),
    data.campaigns.length ? campaignList(data.campaigns, { onSaved: reload, onChannelPage: true, extra: adCard })
      : el("div", { class: "empty" }, isCold ? "No call campaigns yet. Add one, then name it in Config active_campaign." : "No campaigns yet. Add one with Add campaign."),
    isCold ? el("div", { class: "muted", style: "font-size:12px" }, "Connect rate is connects over dials. Booking rate is booked over connects. A call typed in Airtable counts once Campaign and Outcome are picked.",
      ...data.campaigns.filter((c) => c.calls && c.calls.sheets && c.calls.sheets.length).map((c) =>
        ` ${c.Name} also reads the outcome words in its call sheet (${c.calls.sheet_dials} dials there); Wrong vertical is not a dial.`)) : null));

  const changes = ads ? logPanel(ads) : null;
  if (changes) root.append(changes);

  if (isCold) {
    // Today's dials live here only (Jonathan, 2026-10-01: "only be revealed under the cold calls")
    const sheet = await api.get("/api/sheet-today").catch((e) => ({ rows: [], sheets: [{ label: "the call sheet", error: (e.errors || [String(e)]).join(" ") }] }));
    const refresh = el("button", { class: "btn quiet small", type: "button", title: "Pull the calls typed in Airtable now" },
      el("span", { class: "ms", "aria-hidden": "true" }, "refresh"), "Refresh");
    refresh.addEventListener("click", async () => {
      refresh.disabled = true;
      try { await api.refresh(); toast("Up to date with Airtable."); reload(); }
      catch (e) { toast((e.errors || [String(e)]).join(" ")); refresh.disabled = false; }
    });
    root.append(sheetTodayPanel(sheet, refresh));
    root.append(el("div", { class: "panel" },
      el("h2", {}, "The call list lives on Today"),
      el("div", { class: "muted" }, "Twenty-two a day, the dial hour clock, one tap to log. Every dial here rolls up into the numbers above."),
      el("div", { class: "row" }, el("a", { class: "btn", href: "#/today" }, "Open Today"))));
    return;
  }

  // LinkedIn by medium (2026-09-28): ads, posts, DMs, each with its booking rate. A booking is sorted by its link tags
  // or, on a return visit, by the first click in its journey.
  if (data.mediums) {
    const pctOf = (v) => (v === null || v === undefined ? "–" : `${v}%`);
    const how = { Ads: "Clicks typed on the ad campaign rows from Campaign Manager", Posts: "Clicks typed on the LinkedIn posts row from LinkedIn's post analytics", DMs: "Replies, from the weekly LinkedIn export" };
    root.append(el("div", { class: "stack" },
      el("div", {}, el("div", { class: "label" }, "By medium"), el("h2", {}, "Booking rate: ads, posts, DMs")),
      table(["Medium", { label: "Clicks or replies", num: true }, { label: "Leads", num: true }, { label: "Booked", num: true }, { label: "Booking rate", num: true }, "Counted from"],
        data.mediums.map((m) => el("tr", {},
          el("td", { class: "strong" }, m.medium),
          el("td", { class: "num" }, `${m.base} ${m.base_label}`),
          el("td", { class: "num" }, String(m.leads)),
          el("td", { class: "num" + (m.booked ? " up" : "") }, String(m.booked)),
          el("td", { class: "num strong" }, pctOf(m.rate)),
          el("td", { class: "muted", style: "font-size:12px" }, how[m.medium])))),
      el("div", { class: "muted", style: "font-size:12px" },
        "Tag each link so the booking lands in the right row: posts ?utm_source=linkedin&utm_medium=social&utm_campaign=linkedin-posts, DMs ?utm_source=linkedin&utm_medium=dm&utm_campaign=linkedin-messaging. Ads carry LinkedIn's own click id.")));
  }

  // the messaging medium (LinkedIn, 2026-09-28): request to booked, one row per person, from LinkedIn's export
  if (ch.messaging) {
    const m = ch.messaging;
    const rate = (v, word) => (v === null || v === undefined ? "" : `${v}% ${word}`);
    const stageTag = (s) => el("span", { class: "tag" + (s === "Replied" ? "" : s === "Request sent" ? " faint" : "") }, s || "");
    const thRows = (data.threads || []).map((t) => {
      const tr = el("tr", { class: "clickable" + (t.outcome === "Not interested" ? " done" : "") },
        el("td", {}, t.Person, el("span", { class: "sub" }, [t.Position, t["Company on LinkedIn"]].filter(Boolean).join(" · "))),
        el("td", {}, t.company_name || el("span", { class: "muted" }, "not linked")),
        el("td", {}, stageTag(t.Stage)),
        el("td", {}, t.outcome ? el("span", { class: "tag " + (t.outcome === "Booked" ? "won" : "lost") }, t.outcome) : ""),
        el("td", { class: "num" }, t["Request sent"] ? fmtDate(t["Request sent"]) : ""), el("td", { class: "num" }, t.Accepted ? fmtDate(t.Accepted) : ""),
        el("td", { class: "num" }, t["First message"] ? fmtDate(t["First message"]) : ""), el("td", { class: "num" }, t.Replied ? fmtDate(t.Replied) : ""),
        el("td", { class: "num" }, t["Last message"] ? fmtDate(t["Last message"]) : ""));
      tr.addEventListener("click", () => openRecordForm({ table: "LinkedIn threads", title: t.Person, record: t, onSaved: reload, spec: [
        { name: "Outcome", label: "Outcome", type: "select", options: ["Booked", "Not interested"] },
        { name: "Notes", label: "Notes", type: "textarea" }] }));
      return tr;
    });
    root.append(el("div", { class: "stack" },
      el("div", { class: "row" }, el("div", { class: "grow" }, el("div", { class: "label" }, "LinkedIn messaging"), el("h2", {}, "Messages: request to booked"))),
      el("div", { class: "kpis" },
        tile("Requests", String(m.requests), `${m.people} people reached`),
        tile("Accepted", String(m.accepted), rate(m.accept_rate, "accept rate")),
        tile("Messaged", String(m.messaged), ""),
        tile("Replied", String(m.replied), rate(m.reply_rate, "reply rate")),
        tile("Booked", String(m.booked), rate(m.booking_rate, "of replies"), m.booked ? "up" : "")),
      thRows.length ? table(["Person", "CRM company", "Stage", "Outcome", { label: "Request", num: true }, { label: "Accepted", num: true },
        { label: "Messaged", num: true }, { label: "Replied", num: true }, { label: "Last", num: true }], thRows)
        : el("div", { class: "empty" }, "No threads yet. Download LinkedIn's data export (Connections, Invitations, Messages) and run the import."),
      el("div", { class: "muted", style: "font-size:12px" },
        `${m.imported ? `Last import ${fmtDate(m.imported)}. ` : ""}Weekly: LinkedIn, Settings, Data privacy, Get a copy of your data; then python scripts/linkedin_import.py <the zip> --write. `
        + "Click a person to mark Booked or Not interested; a Booked or Lost deal on the linked company counts the same.")));
  }

  // keywords
  if (hasKeywords) {
    const kwRows = data.keywords.map((k) => {
      const tr = el("tr", { class: "clickable" + (k.Status === "Paused" ? " done" : "") },
        el("td", {}, k.Keyword, el("span", { class: "sub" }, k["Match type"] || "")), el("td", {}, k.campaign_name),
        el("td", { class: "num" }, k.Clicks ? String(k.Clicks) : ""), el("td", { class: "num" }, k["Spend to date"] ? money(k["Spend to date"]) : ""),
        el("td", { class: "num" }, String(k.leads)), el("td", { class: "num" }, String(k.leads_booked)), el("td", { class: "num " + (k.leads_sold ? "up" : "") }, String(k.leads_sold)),
        el("td", { class: "num" }, k.won_value ? money(k.won_value) : ""));
      tr.addEventListener("click", () => openRecordForm({ table: "Keywords", title: k.Keyword, record: k, onSaved: reload, spec: keywordSpec(data) }));
      return tr;
    });
    root.append(fold({ key: `kw-${name}`, label: "Keywords", title: "Which search paid for the job", count: data.keywords.length, body: [
      el("div", { class: "row" }, el("span", { class: "grow" }),
        el("button", { class: "btn quiet small", type: "button", onclick: () => openRecordForm({ table: "Keywords", title: "New keyword", onSaved: reload, spec: keywordSpec(data) }) }, "Add keyword")),
      data.keywords.length ? table(["Keyword", "Campaign", { label: "Clicks", num: true }, { label: "Spend", num: true }, { label: "Leads", num: true }, { label: "Booked", num: true }, { label: "Sold", num: true }, { label: "Won $/mo", num: true }], kwRows)
        : el("div", { class: "empty" }, "No keywords yet. A lead's utm_term matches here.")] }));
  }

  // landing pages
  const pgRows = data.landing_pages.map((p) => {
    const tr = el("tr", { class: "clickable" + (p.Status === "Live" ? "" : " done") },
      el("td", {}, p.Name || p.URL, el("span", { class: "sub" }, (p.URL || "").replace(/^https?:\/\/(www\.)?/, ""))),
      el("td", {}, [p.Service, p.Area].filter(Boolean).join(" · ")), el("td", {}, el("span", { class: "tag" + (p.Status === "Live" ? " won" : " faint") }, p.Status || "Draft")),
      el("td", { class: "num" }, p["Form fields"] ? String(p["Form fields"]) : ""), el("td", {}, p.campaign_name),
      el("td", { class: "num" }, String(p.leads)), el("td", { class: "num" }, String(p.leads_booked)), el("td", { class: "num " + (p.leads_sold ? "up" : "") }, String(p.leads_sold)),
      el("td", { class: "num" }, p.won_value ? money(p.won_value) : ""));
    tr.addEventListener("click", () => openRecordForm({ table: "Landing pages", title: p.Name || p.URL, record: p, onSaved: reload, spec: pageSpec(data) }));
    return tr;
  });
  root.append(fold({ key: `pages-${name}`, label: "Landing pages", title: "Attribution by page", count: data.landing_pages.length, body: [
    el("div", { class: "row" }, el("span", { class: "grow" }),
      el("button", { class: "btn quiet small", type: "button", onclick: () => openRecordForm({ table: "Landing pages", title: "New landing page", onSaved: reload, spec: pageSpec(data) }) }, "Add page")),
    data.landing_pages.length ? table(["Page", "Service · Area", "Status", { label: "Fields", num: true }, "Campaign", { label: "Leads", num: true }, { label: "Booked", num: true }, { label: "Sold", num: true }, { label: "Won $/mo", num: true }], pgRows)
      : el("div", { class: "empty" }, "No pages yet. One per service and per area.")] }));

  // leads
  const leadRows = data.leads.map((l) => {
    const tr = el("tr", { class: "clickable" },
      el("td", { class: "num" }, fmtDateTime(l.When)), el("td", {}, l.Name, l.company_name ? el("span", { class: "sub" }, l.company_name) : null),
      el("td", {}, el("span", { class: "tag" + (l.Status === "Sold" ? " won" : l.Status === "Dead" ? " lost" : l.Status === "Booked" ? " solid" : " faint") }, l.Status || "New")),
      el("td", {}, l.campaign_name || (l.medium ? `LinkedIn ${l.medium.toLowerCase()}` : ""), l.keyword_text ? el("span", { class: "sub" }, l.keyword_text) : null),
      el("td", {}, l.page_url ? (l.page_url || "").replace(/^https?:\/\/(www\.)?[^/]+/, "") : ""),
      el("td", { class: "num" }, l["First call at"] && l.When ? `${Math.round((new Date(l["First call at"]) - new Date(l.When)) / 60000)} min` : el("span", { class: l.Status === "New" ? "down" : "muted" }, l.Status === "New" ? "not called" : "")),
      el("td", {}, el("button", { class: "btn quiet small", type: "button", onclick: (e) => { e.stopPropagation(); openRecordForm({ table: "Leads", title: l.Name, record: l, onSaved: reload, spec: leadSpec(ch, data) }); } }, "Edit")));
    // a click opens the booker's journey (2026-09-28); Edit keeps the old form
    tr.addEventListener("click", () => navigate(`#/lead/${l.id}`));
    return tr;
  });
  root.append(el("div", { class: "stack" },
    el("div", { class: "row" }, el("div", { class: "grow" }, el("div", { class: "label" }, "Leads"), el("h2", {}, "Every form fill, with where it came from"))),
    data.leads.length ? table(["When", "Lead", "Status", "Campaign · keyword", "Page", { label: "To first call", num: true }, ""], leadRows)
      : el("div", { class: "empty" }, isSearch ? "No leads yet. When the form posts its UTMs, each one lands here with its campaign, keyword, and page."
        : isOrganic ? "No leads from search yet." : "No leads yet. Workflow for this channel to be defined.")));

  if (isOrganic) root.append(el("div", { class: "muted", style: "font-size:13px" }, "A lead counts here when it arrives with utm_medium=organic, or with no UTM and no other source set. Search impressions and clicks come in once Search Console is wired."));
  else if (!isSearch) root.append(el("div", { class: "muted", style: "font-size:13px" }, "Workflow for this channel to be defined. Campaigns and leads already track here; attribution reads utm_source and utm_medium."));
}

function keywordSpec(data) {
  return [
    { name: "Keyword", label: "Keyword (utm_term)", required: true },
    { name: "Match type", label: "Match type", type: "select", options: ["Exact", "Phrase", "Broad"], value: "Phrase" },
    { name: "Status", label: "Status", type: "select", options: ["Active", "Paused"], value: "Active" },
    { name: "Campaign", label: "Campaign", type: "select", options: data.campaigns.map((c) => ({ value: c.id, label: c.Name })), required: true },
    { name: "Landing page", label: "Landing page", type: "select", options: data.landing_pages.map((p) => ({ value: p.id, label: p.Name || p.URL })) },
    { name: "Clicks", label: "Clicks", type: "number" },
    { name: "Spend to date", label: "Spend to date", type: "number" },
    { name: "Notes", label: "Notes", type: "textarea" },
  ];
}
function pageSpec(data) {
  return [
    { name: "URL", label: "URL", type: "url", required: true },
    { name: "Name", label: "Name" },
    { name: "Service", label: "Service" },
    { name: "Area", label: "Area" },
    { name: "Status", label: "Status", type: "select", options: ["Draft", "Live", "Retired"], value: "Draft" },
    { name: "Form fields", label: "Form fields", type: "number", value: 3 },
    { name: "Campaign", label: "Campaign", type: "select", options: data.campaigns.map((c) => ({ value: c.id, label: c.Name })) },
    { name: "Notes", label: "Notes", type: "textarea" },
  ];
}
function leadSpec(ch, data) {
  return [
    { name: "Name", label: "Name", required: true },
    { name: "Email", label: "Email", type: "email" },
    { name: "Phone", label: "Phone", type: "tel" },
    { name: "Status", label: "Status", type: "select", options: ["New", "Called", "Qualified", "Booked", "Sold", "Dead"], value: "New" },
    { name: "When", label: "Came in (ISO)", value: new Date().toISOString() },
    { name: "First call at", label: "First call at (ISO)" },
    { name: "UTM", label: "Landing URL or UTM string", type: "textarea" },
    { name: "Source", label: "Channel", type: "select", options: [{ value: ch.id, label: ch.label }], value: ch.id },
    { name: "Campaign", label: "Campaign", type: "select", options: (data ? data.campaigns : []).map((c) => ({ value: c.id, label: c.Name })) },
    { name: "Message", label: "Message", type: "textarea" },
    { name: "Notes", label: "Notes", type: "textarea" },
  ];
}
