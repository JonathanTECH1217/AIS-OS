// Settings: the connection, the record budget, and the config this instance runs on.
import { el } from "../util.js";
import { api } from "../api.js";
import { state, refreshHealth, cfg } from "../state.js";
import { toast } from "../components/modal.js";

export async function renderSettings(root) {
  const h = await refreshHealth();
  const total = h.records || 0, cap = h.record_cap || 1000, warn = h.record_warn || 850;
  const counts = el("div", { class: "row", style: "gap:18px;font-size:13px" }, ...Object.entries(h.counts || {}).map(([t, n]) => el("span", { class: "num" }, `${t} ${n}`)));
  const gauge = el("div", { class: "gauge" + (total >= warn ? " warn" : "") }, el("b", { style: `width:${Math.min(100, (total / cap) * 100)}%` }));
  const refresh = el("button", { class: "btn quiet", type: "button" }, "Refresh from Airtable");
  refresh.addEventListener("click", async () => { refresh.disabled = true; await api.refresh(); await refreshHealth(); toast("Cache refreshed."); root.replaceChildren(); renderSettings(root); });

  root.append(
    el("div", { class: "head" },
      el("div", {}, el("div", { class: "label" }, "Settings"), el("h1", {}, h.instance || "Instance"),
        el("div", { class: "sub" }, "Stages, outcomes, and numbers live in the Config table of the base. Edit there, then refresh.")),
      refresh),
    el("div", { class: "kpis" },
      el("div", { class: "kpi" }, el("div", { class: "label" }, "Airtable"),
        el("div", { class: "fig " + (h.airtable_ready ? "" : "down"), style: "font-size:28px" }, h.airtable_ready ? "Connected" : "Not connected"),
        el("div", { class: "muted", style: "font-size:13px" }, h.airtable_ready ? `Token from ${h.pat_source}. ${h.api_calls} API calls this session.` : "Add AIRTABLE_PAT to %USERPROFILE%\\.monarc\\secrets.env and restart.")),
      el("div", { class: "kpi" }, el("div", { class: "label" }, "Records in the base"),
        el("div", { class: "fig num" }, String(total), el("small", {}, ` of ${cap}`)), gauge,
        el("div", { class: (total >= warn ? "down" : "muted"), style: "font-size:13px" }, total >= warn ? "Past the warning line. Set create_company_on to connect, or move to Team." : "Free plan cap. Warning at " + warn + ".")),
      el("div", { class: "kpi" }, el("div", { class: "label" }, "Queue"),
        el("div", { class: "fig num" }, String(h.queue_rows || 0)), el("div", { class: "muted", style: "font-size:13px" }, h.queue_file || "no list file")),
      el("div", { class: "kpi" }, el("div", { class: "label" }, "Pending writes"),
        el("div", { class: "fig num " + (h.outbox ? "down" : "") }, String(h.outbox || 0)),
        el("div", { class: "muted", style: "font-size:13px" }, h.outbox ? "Queued in outbox.jsonl, replayed on the next request once Airtable answers." : "Nothing waiting."))),
    el("div", { class: "panel soft" }, counts,
      el("div", { class: "row", style: "font-size:13px" },
        el("span", { class: "muted" }, `Base ${h.base_id}`), h.base_url ? el("a", { class: "tel", href: h.base_url, target: "_blank", rel: "noopener" }, "Open in Airtable") : null,
        el("span", { class: "muted" }, `Config from ${h.config_source}`), h.cache_age !== null ? el("span", { class: "muted" }, `cache ${h.cache_age}s old`) : null),
      h.last_error ? el("div", { class: "down", style: "font-size:13px" }, `Last Airtable error: ${h.last_error}`) : null),
    el("div", { class: "stack" }, el("div", { class: "label" }, "Config"), el("pre", {}, JSON.stringify(Object.fromEntries(Object.entries(cfg()).filter(([k]) => k !== "sources")), null, 2))));
}
