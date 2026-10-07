// Activity: everything that landed on a record, newest first.
import { el, fmtDateTime } from "../util.js";
import { api } from "../api.js";
import { navigate } from "../router.js";
import { state } from "../state.js";

export async function renderActivity(root) {
  const rows = await api.activity(300);
  const typeSel = el("select", {}, el("option", { value: "" }, "All types"), ...["Dial", "Email", "Text", "DM", "Meeting", "Note"].map((t) => el("option", { value: t }, t)));
  const bySel = el("select", {}, el("option", { value: "" }, "Logged by anyone"), ...["Dashboard", "AIOS inbox", "AIOS calendar", "Manual"].map((t) => el("option", { value: t }, t)));
  const wrap = el("div", { class: "table-wrap" });
  function draw() {
    const list = rows.filter((a) => (!typeSel.value || a.Type === typeSel.value) && (!bySel.value || a["Logged by"] === bySel.value));
    if (!list.length) {
      wrap.replaceChildren(el("div", { class: "empty" }, state.health && !state.health.airtable_ready
        ? "Airtable is not connected yet. Add AIRTABLE_PAT and restart the server."
        : "Nothing here yet. Connects, emails, and meetings land here as they happen."));
      return;
    }
    const tb = el("tbody", {}, ...list.map((a) => {
      const tr = el("tr", { class: "clickable" },
        el("td", { class: "num" }, fmtDateTime(a.When)),
        el("td", {}, el("span", { class: "tag faint" }, a.Type)),
        el("td", {}, a.company_name || "", a.person_name ? el("span", { class: "sub" }, a.person_name) : null),
        el("td", {}, a.Summary, a.Notes ? el("span", { class: "sub" }, a.Notes.length > 140 ? a.Notes.slice(0, 140) + "…" : a.Notes) : null),
        el("td", { class: "muted" }, a["Logged by"] || ""));
      tr.addEventListener("click", () => { if (a.company_id) navigate(`#/companies/${a.company_id}`); });
      return tr;
    }));
    wrap.replaceChildren(el("table", {}, el("thead", {}, el("tr", {}, el("th", {}, "When"), el("th", {}, "Type"), el("th", {}, "Who"), el("th", {}, "What"), el("th", {}, "Logged by"))), tb));
  }
  typeSel.addEventListener("change", draw);
  bySel.addEventListener("change", draw);
  root.append(
    el("div", { class: "head" },
      el("div", {}, el("div", { class: "label" }, "Activity"), el("h1", {}, "What landed on the records"),
        el("div", { class: "sub" }, "Dials from this screen. Emails from the inbox pass. Meetings from the calendar. Phone calls are the one thing still typed."))),
    el("div", { class: "row" }, typeSel, bySel), wrap);
  draw();
}
