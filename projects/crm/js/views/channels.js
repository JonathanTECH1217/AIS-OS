// Channels: the one place a channel shows (Jonathan, 2026-09-27: channels repeated on four screens). Four cards,
// Google Ads, Google Organic (the website), Cold call, LinkedIn, each with inputs, outputs, campaign status, and the
// last few things that happened; a click opens the channel in depth. Every other source is one row in the table below
// (it replaced the "Show all sources" cards and the By source table on Reports). Under the cards, every campaign sits
// under its channel; a click opens its outcomes, where it stands, and its tasks (2026-09-29).
import { el, money, fmtDateTime } from "../util.js";
import { api } from "../api.js";
import { state } from "../state.js";
import { navigate, rerender } from "../router.js";
import { campaignList } from "../components/campaigns.js";

// Brand marks, keyed by Source.Name. Google Ads is the real mark (yellow and blue legs meeting at the top, green dot
// at the foot; fixed 2026-09-27, the first drawing crossed the legs). Google Organic is Monarc's butterfly, from
// projects/monarcbuild-site/public_html/assets/brand/butterfly.svg. viewBox defaults to 0 0 24 24.
export const BRAND = {
  "google-ads": { label: "Google Ads", color: "#4285F4", tint: "#E8F0FE", viewBox: "6 0 184 184",
    logo: '<path fill="#FBBC04" d="M9.27,122.84l52.73-91.3c6.68,3.94,40.43,22.61,45.88,26.16l-52.73,91.31C49.38,156.66,4.62,130.51,9.27,122.84z"/><path fill="#4285F4" d="M182.3,122.84L129.57,31.55c-9.22-15.34-29.07-20.92-45.39-11.85c-16.31,9.07-21.28,28.6-12.06,44.74l52.73,91.33c9.22,15.33,29.08,20.92,45.39,11.85C185.75,158.54,191.52,138.97,182.3,122.84z"/><circle fill="#34A853" cx="42.34" cy="138.76" r="32.34"/>' },
  "google-organic": { label: "Google Organic", color: "#1F5ED8", tint: "#E8EFFC", viewBox: "2.29 0.61 59.41 59.41",
    logo: '<path d="M30.20,31.00 L17.19,31.20 A12.20,12.20 0 1 1 29.16,18.03 Z" fill="#1F5ED8" stroke="#1F5ED8" stroke-width="2.6" stroke-linejoin="round"/><path d="M33.80,31.00 L34.84,18.03 A12.20,12.20 0 1 1 46.81,31.20 Z" fill="#E8604C" stroke="#E8604C" stroke-width="2.6" stroke-linejoin="round"/><path d="M30.20,35.00 L29.59,45.69 A8.60,8.60 0 1 1 19.63,36.71 Z" fill="#169C86" stroke="#169C86" stroke-width="2.6" stroke-linejoin="round"/><path d="M33.80,35.00 L44.37,36.71 A8.60,8.60 0 1 1 34.41,45.69 Z" fill="#F2A93B" stroke="#F2A93B" stroke-width="2.6" stroke-linejoin="round"/>' },
  cold: { label: "Cold call", color: "#2F334D", tint: "#EEF0F6",
    logo: '<rect width="24" height="24" rx="5" fill="#2F334D"/><path fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" d="M7.2 5.6h2.5l1.3 3.1-1.6 1a7.4 7.4 0 0 0 3.4 3.4l1-1.6 3.1 1.3v2.5a1.3 1.3 0 0 1-1.3 1.3A11.3 11.3 0 0 1 5.9 6.9a1.3 1.3 0 0 1 1.3-1.3z"/>' },
  linkedin: { label: "LinkedIn", color: "#0A66C2", tint: "#E7F0FA",
    logo: '<rect width="24" height="24" rx="4" fill="#0A66C2"/><path fill="#FFFFFF" d="M6.9 9.6h2.5V17H6.9zM8.1 5.9a1.45 1.45 0 1 1 0 2.9 1.45 1.45 0 0 1 0-2.9zM10.9 9.6h2.4v1c.4-.7 1.3-1.3 2.5-1.3 2.5 0 3 1.7 3 3.8V17h-2.5v-3.5c0-.9 0-2-1.2-2s-1.4.9-1.4 1.9V17h-2.5z"/>' },
  // Meta Ads (2026-10-03): a people mark in Meta's blue, not Meta's logo (Style Guide Media 7 keeps their marks off the site; this is the CRM)
  "meta-ads": { label: "Meta Ads", color: "#0866FF", tint: "#E7EFFF",
    logo: '<rect width="24" height="24" rx="5" fill="#0866FF"/><g fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="9.2" cy="9.4" r="2.5"/><circle cx="15.6" cy="10.4" r="2"/><path d="M4.8 17.6c.4-2.9 2.2-4.5 4.4-4.5s4 1.6 4.4 4.5"/><path d="M14 17.2c.4-1.9 1.4-2.9 2.7-2.9 1.4 0 2.4 1.2 2.7 3.3"/></g>' },
};
const MAIN = ["google-ads", "google-organic", "cold", "linkedin"];
const GENERIC = { color: "#616161", tint: "#F0F0F0",
  logo: '<rect width="24" height="24" rx="5" fill="#616161"/><path fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" d="M6 10.5v3h2.5l5 3.5V7l-5 3.5z"/><path fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round" d="M16 9.5a3.5 3.5 0 0 1 0 5"/>' };

// Line icons for the other sources (kept for the channel workspace header). Keyed by Source.Type.
export const ICONS = {
  Cold: '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
  "Cold call": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
  "Google Ads": '<path d="M4 17l6-11a3 3 0 0 1 5.2 3L9 20a3 3 0 0 1-5-3z"/><circle cx="17" cy="17" r="3"/><path d="M10 6l5 8.5"/>',
  "Google Organic": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/><path d="M8 10.5h5M10.5 8v5"/>',
  Email: '<rect x="3" y="5" width="18" height="14" rx="1"/><path d="M3 7l9 6 9-6"/>',
  LinkedIn: '<rect x="3" y="3" width="18" height="18" rx="1"/><path d="M8 10v7M8 7v.5M12 17v-4a2 2 0 0 1 4 0v4M12 10v7"/>',
  "Meta Ads": '<path d="M3 15c0-5 2.5-9 5-9s4 4 4 4 2-4 4-4 5 4 5 9c0 2-1 3-2.5 3S16 15 16 15s-1.5 3-4 3-4-3-4-3-1 3-2.5 3S3 17 3 15z"/>',
  Warm: '<path d="M12 3c1 3 5 5 5 10a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3 0-6 1-9z"/>',
  Referral: '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><path d="M16 4l3 3-3 3"/><path d="M19 7h-5"/>',
  Rep: '<path d="M3 12l4-4 4 4-4 4z"/><path d="M11 12h10"/><path d="M17 8l4 4-4 4"/>',
  Inbound: '<path d="M4 4h16v10H4z"/><path d="M4 14l4 6h8l4-6"/><path d="M12 7v5"/><path d="M9.5 9.5L12 12l2.5-2.5"/>',
  Campaign: '<path d="M3 10v4h3l8 5V5L6 10z"/><path d="M17 9a4 4 0 0 1 0 6"/><path d="M19.5 6.5a8 8 0 0 1 0 11"/>',
  Keyword: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/>',
  Content: '<rect x="3" y="5" width="18" height="14" rx="1"/><path d="M10 9l5 3-5 3z"/>',
};

export function icon(type) {
  const wrap = el("span", { class: "icon", "aria-hidden": "true" });
  wrap.innerHTML = `<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${ICONS[type] || ICONS.Campaign}</svg>`;
  return wrap;
}

export function brandOf(name) { return BRAND[name] || GENERIC; }

export function logo(name, size = 44) {
  const b = brandOf(name);
  const wrap = el("span", { class: "ch-logo", "aria-hidden": "true", style: `width:${size}px;height:${size}px` });
  wrap.innerHTML = `<svg viewBox="${b.viewBox || "0 0 24 24"}" width="${size}" height="${size}">${b.logo}</svg>`;
  return wrap;
}

const n = (v) => (v === null || v === undefined ? "–" : typeof v === "number" ? v.toLocaleString("en-US") : String(v));
const pctOf = (v) => (v === null || v === undefined ? "–" : `${v}%`);

function stat(label, value, sub, cls) {
  return el("div", { class: "stat" }, el("div", { class: "label" }, label), el("div", { class: "v num " + (cls || "") }, value), sub ? el("div", { class: "muted", style: "font-size:11px" }, sub) : null);
}

const isOrganic = (ch) => ch.type === "Google Organic";

function statusLine(ch) {
  const st = ch.campaign_status || {};
  const parts = ["Live", "Planned", "Paused", "Ended"].filter((k) => st[k]).map((k) => `${st[k]} ${k.toLowerCase()}`);
  if (ch.type === "Cold call") return ch.active ? "Running: the dial hour, 22 a day" : "Paused";
  if (isOrganic(ch)) return "The website: monarcbuild.com in search and Maps";
  if (!parts.length) return ch.active ? "No campaigns yet" : "Not live yet";
  return parts.join(" · ");
}

function statusTag(ch) {
  const live = ch.type === "Cold call" || isOrganic(ch) ? ch.active : (ch.campaigns_live || 0) > 0;
  if (live) return el("span", { class: "tag won" }, "Live");
  if ((ch.campaign_status || {}).Paused) return el("span", { class: "tag" }, "Paused");
  if ((ch.campaign_status || {}).Planned) return el("span", { class: "tag" }, "Planned");
  return el("span", { class: "tag faint" }, "Not live");
}

function inputs(ch) {
  const spend = ch.spend ? money(ch.spend) + (ch.spend_is_estimate ? " est." : "") : "$0";
  if (ch.type === "Cold call") {
    return [stat("Dials", n(ch.dials)), stat("Connects", n(ch.connects)), stat("Connect %", pctOf(ch.rates && ch.rates.connect)),
      stat("Booked", n(ch.booked)), stat("Book %", pctOf(ch.rates && ch.rates.booking))];
  }
  if (isOrganic(ch)) {
    // no spend and no cost per click: the website's pages, its directory listings (NAP citations, 2026-09-27),
    // and search impressions and clicks (typed until Search Console is wired)
    return [stat("Pages live", n(ch.pages_live)), stat("Listings live", n(ch.listings_live), ch.listings ? `of ${ch.listings}` : ""),
      stat("Impressions", n(ch.impressions)), stat("Clicks", n(ch.clicks))];
  }
  return [stat("Spend", spend, ch.daily_budget ? `${money(ch.daily_budget)}/day` : ""), stat("Impressions", n(ch.impressions)),
    stat("Clicks", n(ch.clicks)), stat("CTR", pctOf(ch.ctr)), stat("CPC", ch.cpc !== null && ch.cpc !== undefined ? `$${ch.cpc}` : "–")];
}

// The messaging medium (LinkedIn, 2026-09-28): request to booked, from LinkedIn's data export loaded weekly.
export function messages(m) {
  const rate = (v, word) => (v === null || v === undefined ? "" : `${v}% ${word}`);
  return [stat("Requests", n(m.requests)), stat("Accepted", n(m.accepted), rate(m.accept_rate, "accept")),
    stat("Messaged", n(m.messaged)), stat("Replied", n(m.replied), rate(m.reply_rate, "reply")),
    stat("Booked", n(m.booked), rate(m.booking_rate, "of replies"), m.booked ? "up" : "")];
}

function outputs(ch) {
  if (ch.type === "Cold call") {
    return [stat("Held", n(ch.held), pctOf(ch.rates && ch.rates.show) + " show"), stat("Won", n(ch.won), null, ch.won ? "up" : ""),
      stat("Open /mo", money(ch.open_value), `${ch.open || 0} open`), stat("Revenue /mo", money(ch.revenue))];
  }
  return [stat("Leads", n(ch.leads), ch.cost_per_lead ? `${money(ch.cost_per_lead)} each` : ""),
    stat("Booked", n(Math.max(ch.booked || 0, ch.leads_booked || 0)), ch.cost_per_booked ? `${money(ch.cost_per_booked)} each` : ""),
    stat("Won", n(ch.won), ch.cost_per_won ? `${money(ch.cost_per_won)} each` : "", ch.won ? "up" : ""),
    stat("Revenue /mo", money(ch.revenue), ch.open_value ? `${money(ch.open_value)}/mo open` : "")];
}

function activity(ch) {
  const list = el("div", { class: "ch-act" });
  if (!ch.recent || !ch.recent.length) { list.append(el("div", { class: "muted", style: "font-size:12px" }, "Nothing yet.")); return list; }
  for (const r of ch.recent.slice(0, 3)) {
    list.append(el("div", { class: "ch-act-row" },
      el("span", { class: "muted num" }, fmtDateTime(r.when)),
      el("span", {}, r.summary || r.kind, r.company ? el("span", { class: "muted" }, ` · ${r.company}`) : null),
      r.outcome ? el("span", { class: "tag" + (r.outcome === "Booked" || r.outcome === "Sold" ? " won" : r.outcome === "Dead" || r.outcome === "Not interested" ? " lost" : " faint") }, r.outcome) : null));
  }
  return list;
}

function card(ch) {
  const b = brandOf(ch.name);
  const a = el("a", { class: "ch-card brand" + (ch.active ? "" : " paused"), href: `#/channel/${encodeURIComponent(ch.name)}`, style: `--accent:${b.color};--accent-tint:${b.tint}` },
    el("div", { class: "ch-head" }, logo(ch.name, 44),
      el("div", { class: "grow" }, el("h3", {}, b.label || ch.label || ch.name), el("div", { class: "muted", style: "font-size:12px" }, statusLine(ch))),
      statusTag(ch)),
    el("div", { class: "ch-sec" }, el("div", { class: "label" }, ch.messaging ? "Ads" : "Inputs"), el("div", { class: "ch-funnel " + (isOrganic(ch) ? "four" : "five") }, ...inputs(ch))),
    ch.messaging ? el("div", { class: "ch-sec" }, el("div", { class: "label" }, "Messages"), el("div", { class: "ch-funnel five" }, ...messages(ch.messaging))) : null,
    el("div", { class: "ch-sec" }, el("div", { class: "label" }, "Outputs"), el("div", { class: "ch-funnel four" }, ...outputs(ch))),
    el("div", { class: "ch-sec" }, el("div", { class: "label" }, "Activity"), activity(ch)),
    el("div", { class: "ch-open" }, `Open ${ch.campaigns ? `${ch.campaigns} campaign${ch.campaigns === 1 ? "" : "s"}` : "the workspace"} →`));
  return a;
}

export async function renderChannels(root) {
  const data = await api.channels();
  const byName = new Map(data.channels.map((c) => [c.name, c]));
  const main = MAIN.map((nm) => byName.get(nm)).filter(Boolean);
  const rest = data.channels.filter((c) => !MAIN.includes(c.name));
  // the strip sums the four channels only; the other sources are not part of the acquisition machine
  const sum = (k) => main.reduce((a, c) => a + (Number(c[k]) || 0), 0);
  const t = { spend: sum("spend"), leads: sum("leads"), booked: main.reduce((a, c) => a + Math.max(c.booked || 0, c.leads_booked || 0), 0), won: sum("won"), revenue: sum("revenue") };
  const strip = el("div", { class: "kpis" },
    el("div", { class: "kpi" }, el("div", { class: "label" }, "Spend to date"), el("div", { class: "fig num" }, money(t.spend)), el("div", { class: "muted", style: "font-size:12px" }, "Google Ads and LinkedIn")),
    el("div", { class: "kpi" }, el("div", { class: "label" }, "Leads"), el("div", { class: "fig num" }, n(t.leads)), el("div", { class: "muted", style: "font-size:12px" }, t.spend && t.leads ? `${money(Math.round(t.spend / t.leads))} each` : "")),
    el("div", { class: "kpi" }, el("div", { class: "label" }, "Booked"), el("div", { class: "fig num" }, n(t.booked)), el("div", { class: "muted", style: "font-size:12px" }, t.spend && t.booked ? `${money(Math.round(t.spend / t.booked))} each` : "")),
    el("div", { class: "kpi" }, el("div", { class: "label" }, "Won"), el("div", { class: "fig num" }, n(t.won), el("small", {}, t.revenue ? ` ${money(t.revenue)}/mo` : ""))));
  const grid = el("div", { class: "ch-grid four" }, ...(main.length ? main.map(card) : [el("div", { class: "empty" }, state.health && !state.health.airtable_ready
    ? "Airtable is not connected yet. Add AIRTABLE_PAT and restart the server." : "No sources named google-ads, google-organic, cold, or linkedin in the base.")]));
  // every other source, one row each: what it brought in. A click opens its page.
  const others = [...rest].sort((a, b) => (a.sort || 99) - (b.sort || 99));
  const table = el("div", { class: "table-wrap" }, el("table", {},
    el("thead", {}, el("tr", {}, el("th", {}, "Source"), el("th", { class: "num" }, "Companies"), el("th", { class: "num" }, "Leads"),
      el("th", { class: "num" }, "Deals"), el("th", { class: "num" }, "Open /mo"), el("th", { class: "num" }, "Won"), el("th", { class: "num" }, "Revenue /mo"))),
    el("tbody", {}, ...others.map((c) => {
      const tr = el("tr", { class: "clickable" + (c.active ? "" : " done") },
        el("td", {}, c.label || c.name, el("span", { class: "sub" }, (c.notes || "").split(". ")[0])),
        el("td", { class: "num" }, n(c.companies)), el("td", { class: "num" }, n(c.leads)), el("td", { class: "num" }, n(c.deals)),
        el("td", { class: "num" }, money(c.open_value)), el("td", { class: "num " + (c.won ? "up" : "") }, n(c.won)),
        el("td", { class: "num " + (c.revenue ? "up" : "") }, money(c.revenue)));
      tr.addEventListener("click", () => navigate(`#/channel/${encodeURIComponent(c.name)}`));
      return tr;
    }))));
  // every campaign under its channel: the four main channels in card order, then the others
  const reload = rerender; // in place, keeping the scroll position
  const rank = (g) => (MAIN.includes(g.channel) ? MAIN.indexOf(g.channel) : 10 + (g.sort || 99));
  const groups = [...(data.campaign_groups || [])].sort((a, b) => rank(a) - rank(b));
  const nCamps = groups.reduce((a, g) => a + g.campaigns.length, 0);
  const campaigns = el("div", { class: "stack" },
    el("div", {}, el("div", { class: "label" }, "Campaigns"), el("h2", {}, `Every campaign, under its channel (${nCamps})`),
      el("div", { class: "muted", style: "font-size:13px" }, "Click a campaign to open it: the outcomes we want, where it stands, and its tasks.")),
    ...(groups.length ? groups.map((g) => {
      const b = brandOf(g.channel);
      return el("section", { class: "camp-group", style: `--accent:${b.color}` },
        el("a", { class: "camp-group-head", href: `#/channel/${encodeURIComponent(g.channel)}` }, logo(g.channel, 28),
          el("h3", {}, b.label || g.label), el("span", { class: "muted" }, `${g.campaigns.length} campaign${g.campaigns.length === 1 ? "" : "s"}`),
          el("span", { class: "grow" }), el("span", { class: "ch-open" }, "Open channel →")),
        campaignList(g.campaigns, { onSaved: reload }));
    }) : [el("div", { class: "empty" }, "No campaigns yet. Add one on a channel's page.")]));
  root.append(
    el("div", { class: "head" },
      el("div", {}, el("div", { class: "label" }, "Channels"), el("h1", {}, "Where the work comes from"),
        el("div", { class: "sub" }, "Google Ads, Google Organic (the website), Cold call, LinkedIn. Inputs are what you put in, outputs are what came back. Click a card for the channel in depth."))),
    strip, grid, campaigns,
    ...(others.length ? [el("div", { class: "stack" },
      el("div", {}, el("div", { class: "label" }, "Other sources"), el("h2", {}, "Everything else that brings in work")), table)] : []));
}
