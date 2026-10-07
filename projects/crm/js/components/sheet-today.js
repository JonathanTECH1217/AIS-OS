// Today's dials (2026-09-29, Jonathan: "This can just be a reflection of the status of the Airtable"): the rows whose
// Status (typed) changed today in the active campaign's call sheet, newest first, and how the CRM reads each. Shown only
// on the Cold call channel page (Jonathan, 2026-10-01: "today's dials should only be revealed under the cold calls").
import { el, telHref } from "../util.js";

const fClock = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", timeZone: "America/New_York" });
const clock = (iso) => fClock.format(new Date(iso));

export function sheetTodayPanel(st, refresh) {
  st = st || { rows: [], sheets: [] };
  const links = (st.sheets || []).flatMap((sh, i) => [i ? ", " : "", sh.url ? el("a", { class: "link", href: sh.url, target: "_blank", rel: "noopener" }, sh.label || "the sheet") : (sh.label || "the sheet")]);
  const dials = st.rows.filter((r) => r.kind === "dial").length;
  const meta = el("div", { class: "muted", style: "font-size:12px" }, ...(links.length
    ? ["From ", ...links, `, the rows whose Status (typed) changed today. Pulled ${st.pulled_at ? clock(st.pulled_at) : "–"}; Refresh pulls now, otherwise every 15 minutes.`,
      ...(st.sheets || []).filter((sh) => sh.error).map((sh) => el("span", { class: "down" }, ` Could not read it: ${sh.error}`))]
    : ["No call sheet is set for the active campaign."]));
  const tag = (r) => r.kind === "skipped" ? el("span", { class: "tag faint" }, "Skipped, not a dial")
    : r.kind === "not counted" ? el("span", { class: "tag lost", title: "No rule reads these words; pick clearer words, such as no answer, voicemail, not interested, booked" }, "Not counted")
    : el("span", { class: "tag" + (r.outcome === "Booked" ? " won" : r.outcome === "Not interested" || r.outcome === "Bad number" ? " lost" : "") }, r.outcome);
  const body = st.rows.length
    ? el("div", { class: "table-wrap" }, el("table", {},
      el("thead", {}, el("tr", {}, el("th", {}, "Time"), el("th", {}, "Company"), el("th", {}, "Phone"), el("th", {}, "What you typed"), el("th", {}, "Counts as"))),
      el("tbody", {}, ...st.rows.map((r) => el("tr", { class: r.kind === "dial" ? "" : "done" },
        el("td", { class: "num muted" }, clock(r.at)),
        el("td", {}, r.name || "–", r.mb ? el("span", { class: "sub" }, r.mb) : null),
        el("td", {}, r.phone ? el("a", { class: "tel", href: telHref(r.phone) }, r.phone) : ""),
        el("td", {}, r.typed || ""),
        el("td", {}, tag(r)))))))
    : el("div", { class: "empty" }, "Nothing typed in Airtable yet today.");
  return el("div", { class: "stack" },
    el("div", { class: "row" },
      el("div", { class: "grow" }, el("div", { class: "label" }, st.campaign || "Cold call"), el("h2", {}, `Today's dials · ${dials} in Airtable`), meta),
      refresh || null),
    body);
}
