// Reports: the Friday tally and where calls die. Revenue by source lives on Channels (2026-09-27).
import { el, money, delta, copyText, fmtDate, addDays, pct } from "../util.js";
import { api } from "../api.js";
import { toast } from "../components/modal.js";

function tile(label, cur, prev, opts = {}) {
  return el("div", { class: "kpi" }, el("div", { class: "label" }, label),
    el("div", { class: "fig num" }, opts.money ? money(cur) : String(cur)), delta(cur, prev, opts));
}

function bars(map, order, { worst } = {}) {
  const keys = order && order.length ? order : Object.keys(map);
  const max = Math.max(1, ...keys.map((k) => map[k] || 0));
  return el("div", { class: "bars" }, ...keys.map((k) => el("div", { class: "bar" + (worst && k === worst && map[k] ? " worst" : "") },
    el("div", { class: "k" }, k), el("div", { class: "track" }, el("b", { style: `width:${((map[k] || 0) / max) * 100}%` })),
    el("div", { class: "v" }, String(map[k] || 0)))));
}

export async function renderReports(root, params) {
  let week = params[0] || null;
  const w = await api.weekly(week);
  const cur = w.current, prev = w.previous;
  const weekOf = cur.week_of;

  const nav = el("div", { class: "row" },
    el("button", { class: "btn quiet small", type: "button", onclick: () => { location.hash = `#/reports/${addDays(weekOf, -7)}`; } }, "← Previous week"),
    el("span", { class: "muted" }, `Week of ${fmtDate(weekOf)} to ${fmtDate(addDays(weekOf, 4))}`),
    el("button", { class: "btn quiet small", type: "button", onclick: () => { location.hash = `#/reports/${addDays(weekOf, 7)}`; } }, "Next week →"));

  const clean = cur.dials >= w.clean_week;
  const under = cur.dials < w.min_week;
  const verdict = el("div", { class: "kpi" }, el("div", { class: "label" }, "Week"),
    el("div", { class: "fig " + (clean ? "up" : under ? "down" : "") }, clean ? "Clean" : under ? "Under 100" : "Short"),
    el("div", { class: "muted", style: "font-size:13px" }, clean ? "110 or more dials logged. Reward earned if the tally is done." : under ? "Under 100 dials: no weekly reward, everything else pauses." : `${w.clean_week - cur.dials} more for a clean week.`));

  const kpis = el("div", { class: "kpis" },
    tile("Dials", cur.dials, prev.dials), tile("Connects", cur.connects, prev.connects), tile("Booked", cur.booked, prev.booked),
    tile("Held", cur.held, prev.held), tile("Signed", cur.signed, prev.signed), verdict);

  const fn = await api.funnel();
  const ar = fn.assumed_rates || {};
  const rateTile = (label, v, assumed, sub) => el("div", { class: "kpi" }, el("div", { class: "label" }, label),
    el("div", { class: "fig num " + (v === null ? "" : assumed !== undefined && v >= assumed * 100 ? "up" : "down") }, v === null ? "–" : `${v}%`),
    el("div", { class: "muted", style: "font-size:13px" }, sub));
  const allTime = el("div", { class: "stack" },
    el("div", {}, el("div", { class: "label" }, "All time, from the base"), el("h2", {}, "Connect, booking, show, close")),
    el("div", { class: "kpis" },
      rateTile("Connect rate", fn.rates.connect, ar.connect, `${fn.connects} connects on ${fn.dials} dials. Assumed ${Math.round((ar.connect || 0) * 100)}.`),
      rateTile("Booking rate", fn.rates.booking, ar.book, `${fn.booked} booked from ${Math.max(fn.connects, fn.contacted)} conversations. Assumed ${Math.round((ar.book || 0) * 100)}.`),
      rateTile("Show rate", fn.rates.show, ar.show, `${fn.held} held of ${fn.booked} booked. Assumed ${Math.round((ar.show || 0) * 100)}.`),
      rateTile("Close rate", fn.rates.close, ar.close, `${fn.won} won of ${fn.held} held. Assumed ${Math.round((ar.close || 0) * 100)}.`),
      el("div", { class: "kpi" }, el("div", { class: "label" }, "Funnel"),
        el("div", { class: "num", style: "font-size:14px;line-height:1.7" },
          `${fn.dialed} companies dialed · ${fn.contacted} contacted · ${fn.booked} booked · ${fn.held} held · ${fn.proposed} proposed · ${fn.won} won · ${fn.lost} lost`),
        el("div", { class: "muted", style: "font-size:13px" }, "A deal at Held counts as Booked too. Stages only move forward."))));

  // Loom briefs (2026-10-04, Jonathan: "analyze the Loom walkthrough, different variations of it, to see how that affects
  // show rate and close rate"): every booked meeting grouped by the Loom it got, with "No Loom" as the line to beat.
  const lr = await api.loomReport().catch(() => null);
  const rate = (v) => (v === null || v === undefined ? "–" : `${v}%`);
  const yn = (v) => (v === true ? "yes" : v === false ? "no-show" : "waiting");
  const looms = lr && lr.rows.length ? el("div", { class: "panel" },
    el("div", {}, el("div", { class: "label" }, "Loom briefs"), el("h2", {}, "Show rate and close rate by variation")),
    el("div", { class: "muted", style: "font-size:13px" }, `Every booked meeting, grouped by the Loom it got before the call. "No Loom" is the line to beat. A difference means something once a variation has about ${lr.enough} meetings with an answer; before that it is noise.`),
    el("div", { class: "table-wrap" }, el("table", {},
      el("thead", {}, el("tr", {}, ...["Variation", "Meetings", "Loom sent", "Watched", "Showed", "No-show", "Waiting", "Show rate", "Won", "Close rate"].map((t, i) => el("th", { class: i ? "num" : null }, t)))),
      el("tbody", {}, ...lr.groups.map((g) => el("tr", {},
        el("td", {}, g.key ? `${g.key}: ${g.variation}` : g.variation), el("td", { class: "num" }, String(g.meetings)), el("td", { class: "num" }, String(g.sent)),
        el("td", { class: "num" }, String(g.watched)), el("td", { class: "num" }, String(g.showed)), el("td", { class: "num" }, String(g.no_show)),
        el("td", { class: "num" }, String(g.pending)), el("td", { class: "num" }, rate(g.show_rate)), el("td", { class: "num" }, String(g.won)), el("td", { class: "num" }, rate(g.close_rate))))))),
    ...lr.variations.map((v) => el("div", { class: "muted", style: "font-size:12px" }, el("span", { class: "strong" }, `${v.key}: ${v.name}. `), v.what || "")),
    el("details", { class: "more" }, el("summary", {}, el("span", { class: "link", style: "font-size:12px" }, `Each meeting (${lr.rows.length})`)),
      el("div", { class: "table-wrap", style: "margin-top:8px" }, el("table", {},
        el("thead", {}, el("tr", {}, ...["Company", "Loom", "Sent", "Watched", "Stage", "Showed", "Won"].map((t) => el("th", {}, t)))),
        el("tbody", {}, ...lr.rows.map((r) => el("tr", {},
          el("td", {}, r.id ? el("a", { class: "link", href: `#/companies/${encodeURIComponent(r.id)}` }, r.company) : r.company),
          el("td", {}, r.loom ? (r.variation ? `${r.variation}: ${r.variation_name}` : r.variation_name) : "none"),
          el("td", {}, r.sent_on ? fmtDate(r.sent_on) : (r.loom ? "not yet" : "")), el("td", {}, r.watched || ""), el("td", {}, r.stage || ""),
          el("td", {}, yn(r.showed)), el("td", {}, r.won ? "yes" : ""))))))),
  ) : null;

  const rates = el("div", { class: "panel soft" }, el("div", { class: "label" }, "Rates this week"),
    el("div", { class: "row", style: "gap:24px" },
      el("span", { class: "num" }, `Connect ${pct(cur.connects, cur.dials)}%`, el("span", { class: "muted" }, " (assumed 30)")),
      el("span", { class: "num" }, `Book ${pct(cur.booked, cur.connects)}%`, el("span", { class: "muted" }, " of connects (assumed 10)")),
      el("span", { class: "num" }, `Show ${pct(cur.held, cur.booked)}%`, el("span", { class: "muted" }, " (assumed 50)")),
      el("span", { class: "num" }, `Recognized the name ${pct(cur.recognized, cur.connects)}%`)));

  const days = ["Mon", "Tue", "Wed", "Thu", "Fri"].map((d, i) => [d, addDays(weekOf, i)]);
  const perDay = {};
  for (const [d, iso] of days) perDay[d] = cur.per_day[iso] || 0;

  const died = el("div", { class: "panel" },
    el("h2", {}, "Where calls died"),
    el("div", { class: "muted", style: "font-size:13px" }, w.worst_line && cur.died_on[w.worst_line]
      ? `Most died on ${w.worst_line}. That is the one line to rewrite this Friday.`
      : "No connects logged with a line yet."),
    bars(cur.died_on, w.lines, { worst: w.worst_line }));

  const dayPanel = el("div", { class: "panel" }, el("h2", {}, "Dials by day"),
    el("div", { class: "muted", style: "font-size:13px" }, `Target ${w.target_week / 5} a day, 12:00 to 1:00 ET.`), bars(perDay, Object.keys(perDay)));

  const outcomesPanel = el("div", { class: "panel" }, el("h2", {}, "Outcomes"), bars(cur.outcomes, Object.keys(cur.outcomes).sort((a, b) => cur.outcomes[b] - cur.outcomes[a])));

  // The By source table left 2026-09-27: channels and sources show in one place, the Channels screen.
  const bySource = el("div", { class: "muted", style: "font-size:13px" }, "Which channel or source produced which job: ",
    el("a", { class: "link", href: "#/channels" }, "Channels"), ".");

  const copyBtn = el("button", { class: "btn quiet", type: "button" }, "Copy tally for tasks.md");
  copyBtn.addEventListener("click", () => {
    const line = `| ${weekOf} | ${cur.dials} | ${cur.booked} | ${cur.held} | yes | ${clean ? "yes" : "no"} | |`;
    const lines = w.lines.map((l) => `${l} ${cur.died_on[l] || 0}`).join(", ");
    copyText(`${line}\nDied on: ${lines}. Connects ${cur.connects}, signed ${cur.signed}. Rewrite: ${w.worst_line || "none"}.`).then(() => toast("Tally copied."));
  });

  root.append(
    el("div", { class: "head" },
      el("div", {}, el("div", { class: "label" }, "Reports"), el("h1", {}, "The Friday tally"),
        el("div", { class: "sub" }, "Dials, connects, booked, held, signed. Then the one line to rewrite.")),
      copyBtn),
    nav, kpis, rates, allTime, looms,
    el("div", { class: "two" }, died, dayPanel),
    outcomesPanel, bySource);
}
