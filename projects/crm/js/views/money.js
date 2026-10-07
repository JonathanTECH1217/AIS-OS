// Money: the money side of the CRM (2026-09-28). The clients (every won deal, mirrored into the Books base's Clients
// table by the server), what they pay each month, this month's money in and out, open invoices, and the months side by side.
import { el, money, delta } from "../util.js";
import { api } from "../api.js";

function tile(label, value, sub, cls = "") {
  return el("div", { class: "kpi" }, el("div", { class: "label" }, label), el("div", { class: "fig num " + cls }, value), sub ? el("div", { class: "muted", style: "font-size:13px" }, sub) : null);
}

export async function renderMoney(root) {
  const d = await api.money();
  if (!d.ready) {
    root.append(el("div", { class: "head" }, el("div", {}, el("div", { class: "label" }, "Money"), el("h1", {}, "The money book"))),
      el("div", { class: "empty" }, d.reason || "The Books base is not reachable. Add it to the Airtable token and set books_base_id in config.json."));
    return;
  }
  const m = d.this_month, p = d.last_month;
  const clients = d.clients || [];
  const clientPanel = el("div", { class: "stack" },
    el("div", {}, el("div", { class: "label" }, "Clients"), el("h2", {}, "Every won deal, and what it pays")),
    d.sync_note ? el("div", { class: "down", style: "font-size:12px" }, d.sync_note) : null,
    clients.length ? el("div", { class: "table-wrap" }, el("table", {},
      el("thead", {}, el("tr", {}, el("th", {}, "Client"), el("th", {}, "Status"), el("th", { class: "num" }, "Monthly fee"), el("th", {}, "Signed on"),
        el("th", { class: "num" }, "Invoiced"), el("th", { class: "num" }, "Paid"), el("th", { class: "num" }, "Open"))),
      el("tbody", {}, ...clients.map((c) => el("tr", { class: c.Status === "Ended" ? "done" : "" },
        el("td", {}, c.Client, el("span", { class: "sub" }, [c.Offer, c.Source].filter(Boolean).join(" · "))),
        el("td", {}, el("span", { class: "tag" + (c.Status === "Ended" ? " faint" : c.Status === "Paused" ? "" : " won") }, c.Status || "Active")),
        el("td", { class: "num" }, money(c["Monthly fee"] || 0)), el("td", {}, c["Signed on"] || ""),
        el("td", { class: "num" }, money(c.Invoiced || 0)), el("td", { class: "num up" }, money(c.Paid || 0)),
        el("td", { class: "num " + ((c.Open || 0) > 0 ? "down" : "") }, money(c.Open || 0)))))))
      : el("div", { class: "empty" }, "No clients yet. When a deal reaches Won in the CRM, it shows up here and in the Books base's Clients table."));
  root.append(
    el("div", { class: "head" },
      el("div", {}, el("div", { class: "label" }, "Money · " + m.month), el("h1", {}, "The money book"),
        el("div", { class: "sub" }, "Every dollar in and out, labeled, matched to the statement once a month. Fifteen minutes at month end.")),
      el("div", { class: "muted", style: "font-size:13px;max-width:360px" }, "Load the bank CSV and run month end with scripts/books.py. Receipts attach to the row in Airtable.")),
    el("div", { class: "kpis" },
      tile("Monthly recurring", money(d.mrr || 0), `${d.active_clients || 0} active client${d.active_clients === 1 ? "" : "s"}`),
      el("div", { class: "kpi" }, el("div", { class: "label" }, "Revenue"), el("div", { class: "fig num" }, money(m.revenue)), delta(m.revenue, p ? p.revenue : undefined, { suffix: "" })),
      el("div", { class: "kpi" }, el("div", { class: "label" }, "Costs"), el("div", { class: "fig num" }, money(m.costs)), delta(m.costs, p ? p.costs : undefined, { invert: true })),
      el("div", { class: "kpi" }, el("div", { class: "label" }, "Profit"), el("div", { class: "fig num " + (m.profit > 0 ? "up" : m.profit < 0 ? "down" : "") }, money(m.profit)), delta(m.profit, p ? p.profit : undefined)),
      tile("Open invoices", money(d.open_invoices_value), `${d.open_invoices} sent, ${d.late_invoices} late`, d.late_invoices ? "down" : ""),
      tile("Unlabeled rows", String(m.unlabeled), m.unlabeled ? "pick an account in Airtable" : "all labeled", m.unlabeled ? "down" : ""),
      tile("Not matched", String(m.unreconciled), "rows not yet ticked against the statement")),
    clientPanel,
    el("div", { class: "two" },
      el("div", { class: "panel" }, el("h2", {}, "By account, " + m.month),
        m.by_account.length ? el("div", { class: "table-wrap", style: "border:0" }, el("table", {}, el("thead", {}, el("tr", {}, el("th", {}, "Account"), el("th", {}, "Type"), el("th", { class: "num" }, "Amount"))),
          el("tbody", {}, ...m.by_account.map((a) => el("tr", {}, el("td", {}, a.name), el("td", { class: "muted" }, a.type), el("td", { class: "num " + (a.amount > 0 ? "" : "") }, money(a.amount)))))))
          : el("div", { class: "muted" }, "No labeled rows this month.")),
      el("div", { class: "panel" }, el("h2", {}, "Months"),
        d.months.length ? el("div", { class: "table-wrap", style: "border:0" }, el("table", {}, el("thead", {}, el("tr", {}, el("th", {}, "Month"), el("th", { class: "num" }, "Revenue"), el("th", { class: "num" }, "Costs"), el("th", { class: "num" }, "Profit"), el("th", { class: "num" }, "Salary"), el("th", { class: "num" }, "Invested"), el("th", {}, "Done"))),
          el("tbody", {}, ...d.months.map((r) => el("tr", {}, el("td", { class: "num" }, r.Month), el("td", { class: "num" }, money(r.Revenue || 0)), el("td", { class: "num" }, money(r.Costs || 0)), el("td", { class: "num " + ((r.Profit || 0) > 0 ? "up" : (r.Profit || 0) < 0 ? "down" : "") }, money(r.Profit || 0)), el("td", { class: "num" }, r["Salary paid"] ? money(r["Salary paid"]) : ""), el("td", { class: "num" }, r.Invested ? money(r.Invested) : ""), el("td", {}, r["Tally done"] ? "yes" : ""))))))
          : el("div", { class: "muted" }, "No month closed yet. The first month-end run writes the first row."))),
    el("div", { class: "panel soft" }, el("div", { class: "label" }, "Invoices"),
      d.invoices.length ? el("div", { class: "table-wrap", style: "border:0" }, el("table", {}, el("thead", {}, el("tr", {}, el("th", {}, "Number"), el("th", {}, "Client"), el("th", { class: "num" }, "Amount"), el("th", {}, "Issued"), el("th", {}, "Due"), el("th", {}, "Status"))),
        el("tbody", {}, ...d.invoices.map((i) => el("tr", {}, el("td", {}, i.Number), el("td", {}, i.client_name || ""), el("td", { class: "num" }, money(i.Amount || 0)), el("td", {}, i.Issued || ""), el("td", {}, i.Due || ""), el("td", {}, el("span", { class: "tag" + (i.Status === "Paid" ? " won" : i.Status === "Late" ? " lost" : " faint") }, i.Status || "Draft")))))))
        : el("div", { class: "muted" }, "No invoices yet. Stripe sends them; this table mirrors them.")));
}
