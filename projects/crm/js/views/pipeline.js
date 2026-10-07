// Pipeline: every stage, count and monthly value, on one screen. A card opens the deal form.
// Two tabs since 2026-10-03: Board (this file: the journey map, the KPIs, the stage columns) and Funnels
// (#/pipeline/funnels, views/funnels.js). Every trade shows together; the vertical switch left the rail the same day.
import { el, money, fmtDate } from "../util.js";
import { api } from "../api.js";
import { openDealForm } from "../components/deal-form.js";
import { navigate } from "../router.js";
import { journeyMap } from "../components/journey.js";
import { tabs, PIPELINE_TABS } from "../components/tabs.js";
import { renderFunnels } from "./funnels.js";

export async function renderPipeline(root, params) {
  if ((params || [])[0] === "funnels") return renderFunnels(root);
  // the journey map on top (2026-10-01) reads the channels and their campaigns
  const [data, channels, journey] = await Promise.all([api.pipeline(), api.channels().catch(() => null),
    api.get("/api/journey?light=1").catch(() => null)]);
  const goal = data.goal || { won: 5, by: "2026-12-01" };
  const overdue = data.columns.flatMap((c) => c.deals).filter((d) => d.overdue).length;
  const openCount = data.columns.filter((c) => !c.closed).reduce((n, c) => n + c.count, 0);
  const noNext = data.columns.filter((c) => !c.closed).flatMap((c) => c.deals).filter((d) => !d["Next action"]).length;

  const kpis = el("div", { class: "kpis" },
    el("div", { class: "kpi" }, el("div", { class: "label" }, "Open pipeline"), el("div", { class: "fig num" }, money(data.open_value), el("small", {}, "/mo")),
      el("div", { class: "muted", style: "font-size:13px" }, `${openCount} open deal${openCount === 1 ? "" : "s"}`)),
    el("div", { class: "kpi" }, el("div", { class: "label" }, "Signed"), el("div", { class: "fig num" }, String(data.won_count), el("small", {}, ` of ${goal.won}`)),
      el("div", { class: "gauge" }, el("b", { style: `width:${Math.min(100, (data.won_count / goal.won) * 100)}%` })),
      el("div", { class: "muted", style: "font-size:13px" }, `by ${fmtDate(goal.by)}`)),
    el("div", { class: "kpi" }, el("div", { class: "label" }, "Won, monthly"), el("div", { class: "fig num" }, money(data.won_value), el("small", {}, "/mo"))),
    el("div", { class: "kpi" }, el("div", { class: "label" }, "Next actions overdue"),
      el("div", { class: "fig num " + (overdue ? "down" : "") }, String(overdue)),
      el("div", { class: (noNext ? "down" : "muted"), style: "font-size:13px" }, noNext ? `${noNext} open deal${noNext === 1 ? "" : "s"} with no next step` : "Every open deal has a next step")));

  const board = el("div", { class: "board" });
  for (const col of data.columns) {
    const cards = el("div", { class: "cards" });
    for (const d of col.deals) {
      const card = el("div", { class: "card", tabindex: "0", role: "button" },
        el("div", { class: "name" }, d.company_name || d.Deal),
        el("div", { class: "meta" }, el("span", { class: "num" }, money(d.Value, { mo: true })), el("span", {}, d.source_name || "")),
        col.closed
          ? el("div", { class: "next muted" }, d["Close reason"] || (col.won ? "Signed" : "Closed"))
          : el("div", { class: "next" + (d.overdue ? " overdue" : "") },
            d["Next action"] ? `${d["Next action"]} · ${fmtDate(d["Next action date"])}${d.overdue ? " · overdue" : ""}` : "No next action"));
      const open = () => openDealForm(d, { company: { id: d.company_id, Name: d.company_name, Source: d.Source }, onSaved: () => renderPipeline(clearRoot(root)) });
      card.addEventListener("click", open);
      card.addEventListener("keydown", (e) => { if (e.key === "Enter") open(); });
      cards.append(card);
    }
    if (!col.deals.length) cards.append(el("div", { class: "muted", style: "font-size:13px;padding:6px 2px" }, "none"));
    board.append(el("div", { class: "stage" + (col.closed ? " closed" : "") },
      el("header", {}, el("div", { class: "label" }, col.stage), el("div", { class: "n" }, String(col.count)),
        el("div", { class: "sum" }, money(col.value, { mo: true }))),
      cards));
  }

  root.append(
    el("div", { class: "head" },
      el("div", {}, el("div", { class: "label" }, "Pipeline"), el("h1", {}, "Every deal, by stage"),
        el("div", { class: "sub" }, "A deal with no next step is dying quietly. The form will not save one.")),
      el("button", { class: "btn quiet", type: "button", onclick: () => navigate("#/companies") }, "New deal from a company")),
    tabs(PIPELINE_TABS, "board", "Pipeline views"),
    ...(channels && journey ? [journeyMap(channels, data, journey)] : []), kpis, board);
}

function clearRoot(root) { root.replaceChildren(); return root; }
