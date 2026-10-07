// One booker, start to finish (Jonathan, 2026-09-28: "a booker's full attribution and journey in a single view").
// The click that brought them (link tags, ad click ids, the site they came from), each page and booking step with its
// time (from assets/journey.js on the site, saved on the lead by the booking script), the booking, and what happened in
// the CRM after. Reached from a lead row on a channel page, or a deal that came from a booking.
import { el, append, money, fmtDateTime } from "../util.js";
import { api } from "../api.js";

const KIND = {
  page: (e) => `Viewed ${e.page || "a page"}`,
  open: (e) => `Opened the booking form on ${e.page || "the page"}`,
  time: () => "Picked a time",
  team: () => "Answered the team size",
  send: () => "Sent the booking",
};

function host(u) { try { return new URL(u).hostname.replace(/^www\./, ""); } catch (e) { return u || ""; } }

// "LinkedIn ad, campaign 123, ad 456" from the tags; else the site they came from; else direct
function describe(tags, ref) {
  const t = tags || {};
  const parts = [];
  if (t.utm_source) parts.push(t.utm_source + (t.utm_medium ? ` / ${t.utm_medium}` : ""));
  if (t.utm_campaign) parts.push(`campaign ${t.utm_campaign}`);
  if (t.utm_content) parts.push(`ad ${t.utm_content}`);
  if (t.utm_term) parts.push(`search "${t.utm_term}"`);
  if (t.li_fat_id) parts.push("LinkedIn ad click");
  if (t.gclid) parts.push("Google ad click");
  if (!parts.length && ref) parts.push(`from ${host(ref)}`);
  return parts.join(", ") || "typed the address or a bookmark";
}

function row(at, what, sub, cls) {
  return el("div", { class: "item" + (cls ? " " + cls : "") },
    el("div", { class: "when" }, at ? fmtDateTime(at) : ""),
    el("div", { class: "what" }, el("div", { class: "strong" }, what), sub ? el("div", { class: "muted", style: "font-size:13px" }, sub) : null));
}

export async function renderLead(root, params) {
  const d = await api.get("/api/lead/" + encodeURIComponent(params[0]));
  const l = d.lead;
  const f = d.first;
  const tagNames = { utm_source: "Source", utm_medium: "Medium", utm_campaign: "Campaign", utm_content: "Ad", utm_term: "Search term", utm_id: "Id", li_fat_id: "LinkedIn click id", gclid: "Google click id" };
  const clickTags = f ? f : d.tags;
  const facts = Object.keys(tagNames).filter((k) => clickTags && clickTags[k]).map((k) =>
    el("div", { class: "stat" }, el("div", { class: "label" }, tagNames[k]), el("div", { style: "font-size:14px;word-break:break-all" }, String(clickTags[k]))));

  const timeline = el("div", { class: "timeline" });
  for (const e of d.events) {
    if (e.kind === "arrive") timeline.append(row(e.at, `Arrived on ${e.page || "the site"}`, describe(e.tags, e.ref)));
    else timeline.append(row(e.at, (KIND[e.kind] || (() => e.kind))(e)));
  }
  if (!d.events.length) timeline.append(el("div", { class: "muted", style: "padding:12px 0" },
    "No journey recorded. Bookings made before the site started keeping one (2026-09-28) have only their link tags, shown above."));
  timeline.append(row(l.When, `Booked a call for ${l["Call at"] ? fmtDateTime(l["Call at"]) : "a time to confirm"}`,
    [l.Technicians ? `${l.Technicians} technicians` : "", l.Message || ""].filter(Boolean).join(" · "), "strong-row"));
  for (const a of d.after) timeline.append(row(a.at, a.summary || a.type, a.outcome || ""));
  if (d.deal) timeline.append(row(null, `Deal now at ${d.deal.stage || "no stage"}${d.deal.value ? `, ${money(d.deal.value, { mo: true })}` : ""}`, d.deal.next ? `Next: ${d.deal.next}` : ""));

  append(root, [
    el("div", { class: "head" },
      el("div", {},
        el("div", { class: "label" }, el("a", { href: "#/channels" }, "Channels"), " · ", d.source || "no source", d.medium ? ` · ${d.medium}` : "", d.campaign ? ` · ${d.campaign}` : ""),
        el("h1", {}, l.Name || "A booker"),
        el("div", { class: "sub" }, [l.Email, l.Phone, d.company ? d.company.name : ""].filter(Boolean).join(" · ")))),
    el("div", { class: "panel" },
      el("div", { class: "row" }, el("h2", { class: "grow" }, "The click that brought them"),
        f && f.at ? el("span", { class: "tag faint" }, fmtDateTime(f.at)) : null),
      el("div", {}, describe(clickTags, f ? f.ref : null), f && f.page ? el("span", { class: "muted" }, ` · landed on ${f.page}`) : null),
      facts.length ? el("div", { class: "kpis", style: "grid-template-columns:repeat(auto-fit,minmax(160px,1fr))" }, ...facts) : null,
      f && !l.UTM ? el("div", { class: "muted", style: "font-size:12px" }, "A return visit: this booking came in without tags, so the first click in the journey gets the credit.") : null),
    el("div", { class: "panel" }, el("h2", {}, "Journey"), timeline),
  ]);
}
