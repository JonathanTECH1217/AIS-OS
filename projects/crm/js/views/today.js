// Today. First screen (Jonathan, 2026-09-29): "a brief on my email inbox, any draft emails that I need to approve for
// send, as well as a view of my Google Calendar": the inbox and drafts from Proton (components/mail.js) and the day as
// an hour grid (meetings through the booking script's agenda action, the dial hour, booked calls). Below it: the clock
// and today's dials, the campaign, what has to get done (next actions due, the open boxes in tasks.md), and the CRM's
// own call list, folded. Today's calls from the Airtable sheet live on the Cold call channel page (2026-10-01).
import { el, money, fmtDate, fmtDateTime, telHref, copyText, debounce, addDays } from "../util.js";
import { api } from "../api.js";
import { openDialModal, quickDial } from "../components/dial-modal.js";
import { openDealForm } from "../components/deal-form.js";
import { toast } from "../components/modal.js";
import { cfg, numbers, refreshHealth, todayISO, sourceName, outcomes, outcome } from "../state.js";
import { navigate, rerender as redraw } from "../router.js";
import { mailPanels, openReader } from "../components/mail.js";

const ET = "America/New_York";
const fClock = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", timeZone: ET });
const fHM = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: ET });
const fDay = new Intl.DateTimeFormat("en-CA", { timeZone: ET });
function clock(iso) { return fClock.format(new Date(iso)); }
function hm(iso) { return fHM.format(new Date(iso)); }
function etDay(iso) { try { return fDay.format(new Date(iso)); } catch (e) { return String(iso || "").slice(0, 10); } }
function norm(r) { return r && r.fields ? { ...r.fields, id: r.id } : r; }

function clockBlock() {
  const hour = cfg().dial_hour || { start: "12:00", end: "13:00" };
  const t = el("div", { class: "t num" });
  const s = el("div", { class: "muted", style: "font-size:12px" });
  function tick() {
    const now = new Date();
    t.textContent = fClock.format(now) + " ET";
    const cur = fHM.format(now);
    if (cur >= hour.start && cur < hour.end) s.textContent = `Dial hour. Ends at ${hour.end} ET.`;
    else if (cur < hour.start) s.textContent = `Dial hour starts at ${hour.start} ET.`;
    else s.textContent = "Dial hour is over. Log what you have.";
  }
  tick();
  const node = el("div", { class: "clock" }, el("div", { class: "label" }, "Now"), t, s);
  const id = setInterval(() => { if (!document.body.contains(node)) clearInterval(id); else tick(); }, 15000);
  return node;
}

// One time-ordered list for a day: calendar events, the dial hour, and (when the calendar is offline) booked calls from leads.
function dayRows(day, agenda, leads, dialed, target) {
  const rows = [];
  const hour = cfg().dial_hour || { start: "12:00", end: "13:00" };
  const events = (agenda.events || []).filter((ev) => !ev.error && (ev.all_day ? String(ev.start).slice(0, 10) === day : etDay(ev.start) === day));
  for (const ev of events) {
    rows.push({ key: ev.all_day ? "00:00" : hm(ev.start), endKey: ev.all_day ? "" : hm(ev.end), all_day: ev.all_day, kind: "meeting",
      time: ev.all_day ? "All day" : `${clock(ev.start)} to ${clock(ev.end)}`, title: ev.title, sub: [ev.calendar, ...(ev.guests || [])].filter(Boolean).join(" · "),
      meet: ev.meet, link: ev.link, invite: ev.invite || null });
  }
  if (agenda.source !== "ok") {
    for (const l of leads.map(norm)) {
      if (l.Status === "Booked" && l["Call at"] && etDay(l["Call at"]) === day) {
        rows.push({ key: hm(l["Call at"]), endKey: hm(new Date(new Date(l["Call at"]).getTime() + 15 * 60000).toISOString()), kind: "meeting", time: clock(l["Call at"]), title: `Call with ${l.Name || "a prospect"}`,
          sub: [l.Technicians ? `${l.Technicians} technicians` : "", sourceName((l.Source || [])[0])].filter(Boolean).join(" · "), phone: l.Phone });
      }
    }
  }
  const wd = new Date(day + "T12:00:00").getDay();
  if (wd !== 0 && wd !== 6) {
    rows.push({ key: hour.start, endKey: hour.end, kind: "dial", time: `${to12(hour.start)} to ${to12(hour.end)}`, title: "Dial hour",
      sub: `${dialed} of ${target} logged`, done: dialed >= target });
  }
  rows.sort((a, b) => a.key.localeCompare(b.key));
  return rows;
}
function to12(hmStr) { const [h, m] = hmStr.split(":").map(Number); const d = new Date(2000, 0, 1, h, m); return d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" }); }

// The calendar on Today's first screen (2026-09-29): today as an hour grid with a line at now, the dial hour shaded,
// then tomorrow's meetings. Events come from Google Calendar through the booking script's agenda action; when that is
// offline, booked calls from the site's leads stand in.
const GCAL = "https://calendar.google.com/calendar/r/day";
const mins = (s) => { const [h, m] = String(s).split(":").map(Number); return h * 60 + (m || 0); };
function hourLabel(t) { const h = Math.floor(t / 60) % 24; return `${h % 12 || 12} ${h < 12 ? "am" : "pm"}`; }

function timeline(rows) {
  const PX = 40 / 60; // 40 px an hour
  const timed = rows.filter((r) => !r.all_day && r.key);
  let lo = 8 * 60, hi = 18 * 60;
  for (const r of timed) {
    lo = Math.min(lo, Math.floor(mins(r.key) / 60) * 60);
    hi = Math.max(hi, Math.ceil(mins(r.endKey || r.key) / 60) * 60 + (r.endKey ? 0 : 60));
  }
  hi = Math.min(hi, 24 * 60);
  const tl = el("div", { class: "tl", style: `height:${(hi - lo) * PX}px` });
  for (let t = lo; t <= hi; t += 60) tl.append(el("div", { class: "tl-hour", style: `top:${(t - lo) * PX}px` }, el("span", { class: "num" }, hourLabel(t))));
  const nowM = mins(fHM.format(new Date()));
  // Blocks that overlap sit side by side (a meeting inside the dial hour, 2026-10-05): each takes the first free lane,
  // and a run of overlapping blocks shares the width.
  const spans = timed.map((r) => { const s = mins(r.key); return { r, s, e: r.endKey ? Math.max(mins(r.endKey), s + 15) : s + 30 }; })
    .sort((a, b) => a.s - b.s || b.e - a.e);
  let run = [], runEnd = -1;
  const close = () => { const n = Math.max(...run.map((x) => x.lane)) + 1; run.forEach((x) => { x.lanes = n; }); run = []; runEnd = -1; };
  for (const x of spans) {
    if (run.length && x.s >= runEnd) close();
    const taken = new Set(run.filter((y) => y.e > x.s).map((y) => y.lane));
    x.lane = 0;
    while (taken.has(x.lane)) x.lane++;
    run.push(x);
    runEnd = Math.max(runEnd, x.e);
  }
  if (run.length) close();
  for (const { r, s, e, lane, lanes } of spans) {
    const href = r.meet || (r.phone ? telHref(r.phone) : r.link || null);
    const inv = r.invite;
    const side = lanes > 1 ? `;left:calc(6px + (100% - 10px) * ${lane} / ${lanes});right:auto;width:calc((100% - 10px) / ${lanes} - 2px)` : "";
    tl.append(el(href ? "a" : "div", { class: `tl-ev ${r.kind}${inv ? " inv-" + inv.status : ""}${e <= nowM || r.done ? " past" : ""}`, href,
      target: href && href.startsWith("http") ? "_blank" : null, rel: href && href.startsWith("http") ? "noopener" : null,
      title: `${inv ? inviteWord(inv) + " · " : ""}${r.time} · ${r.title}${r.sub ? " · " + r.sub : ""}`, style: `top:${(s - lo) * PX}px;height:${Math.max(18, (e - s) * PX - 2)}px${side}` },
      inv ? el("span", { class: "tl-st" }, inviteWord(inv) + " ") : null,
      el("span", { class: "strong" }, r.title), el("span", { class: "tl-t" }, ` ${r.time}`),
      e - s >= 45 && r.sub ? el("div", { class: "tl-sub" }, r.sub) : null,
      r.meet ? el("span", { class: "tl-join" }, "Join") : null));
  }
  if (nowM >= lo && nowM <= hi) tl.append(el("div", { class: "tl-now", style: `top:${(nowM - lo) * PX}px`, title: `Now, ${fClock.format(new Date())}` }));
  return tl;
}

// The answer to an invite he sent (Jonathan, 2026-10-05: "a yellow status for pending confirmation, green for
// confirmed on the receiver side and red for decline"). The server reads it from the event's guests, or, for an invite
// sent as a calendar file on a Proton email, from the replies in the inbox (agenda in crm_server.py).
const INVITE = { pending: ["Pending", "wait"], confirmed: ["Confirmed", "won"], declined: ["Declined", "lost"] };
function inviteWord(inv) { return inv.status === "pending" && (inv.guests || []).some((g) => g.maybe) ? "Maybe" : (INVITE[inv.status] || INVITE.pending)[0]; }
function inviteTag(inv) { return el("span", { class: "tag " + (INVITE[inv.status] || INVITE.pending)[1] }, inviteWord(inv)); }
const fShort = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", timeZone: ET });
const fWeekday = new Intl.DateTimeFormat("en-US", { weekday: "short", month: "short", day: "numeric", timeZone: ET });

// Every invite out for a meeting still ahead, soonest first, with who it went to and what came back.
function invitesBlock(agenda) {
  const today = todayISO(), tomorrow = addDays(today, 1), now = Date.now();
  const out = (agenda.events || []).filter((ev) => ev.invite && !ev.all_day && new Date(ev.end || ev.start).getTime() >= now);
  const day = (iso) => { const d = etDay(iso); return d === today ? "Today" : d === tomorrow ? "Tomorrow" : fWeekday.format(new Date(iso)); };
  const rows = out.map((ev) => {
    const inv = ev.invite;
    const read = inv.reply_uid ? el("button", { class: "link", type: "button", style: "font-size:12px" }, `They wrote back ${fShort.format(new Date(inv.replied_at))}. Read it.`) : null;
    if (read) read.addEventListener("click", () => openReader("INBOX", inv.reply_uid));
    return el("div", { class: "invite-row" }, inviteTag(inv),
      el("div", { class: "what" }, el("div", { class: "strong" }, ev.title),
        el("div", { class: "muted" }, [(inv.guests || []).map((g) => g.name).join(", "), inv.sent_at ? `sent ${fShort.format(new Date(inv.sent_at))} by email` : ""].filter(Boolean).join(" · ")),
        read),
      el("div", { class: "time num" }, `${day(ev.start)}, ${clock(ev.start)}`));
  });
  return [el("div", { class: "label" }, "Invites sent"),
    ...(rows.length ? rows : [el("div", { class: "muted", style: "font-size:12px" }, "No invite is out for a meeting ahead.")]),
    agenda.invites_mail && agenda.invites_mail !== "ok" ? el("div", { class: "muted", style: "font-size:11px" }, "Invites sent by email are not checked while Proton Bridge is closed.") : null];
}

function calendarPanel(agenda, leads, dialed, target) {
  const today = todayISO(), tomorrow = addDays(today, 1);
  const rows = dayRows(today, agenda, leads, dialed, target);
  const later = dayRows(tomorrow, agenda, leads, 0, target).filter((r) => r.kind === "meeting");
  const meetings = rows.filter((r) => r.kind === "meeting").length;
  const allDay = rows.filter((r) => r.all_day);
  return el("section", { class: "panel top-panel", "aria-label": "Calendar" },
    el("div", { class: "row" }, el("h2", { class: "grow" }, "Calendar"),
      el("span", { class: "tag" + (meetings ? " solid" : " faint") }, `${meetings} meeting${meetings === 1 ? "" : "s"} today`),
      el("a", { class: "link", href: GCAL, target: "_blank", rel: "noopener", style: "font-size:13px" }, "Open Google Calendar")),
    agenda.source !== "ok" ? el("div", { class: "down", style: "font-size:12px" }, agenda.note || "Calendar offline.",
      agenda.source === "old script" ? " Until then only calls booked on the site show here." : "") : null,
    ...invitesBlock(agenda),
    allDay.length ? el("div", { class: "row", style: "gap:6px" }, ...allDay.map((r) => el("span", { class: "tag" }, r.title))) : null,
    timeline(rows),
    el("div", { class: "label", style: "margin-top:4px" }, "Tomorrow"),
    ...(later.length ? later.map((r) => el("div", { class: "agenda-row small" }, el("div", { class: "time num" }, r.time),
      el("div", { class: "what" }, r.invite ? inviteTag(r.invite) : null, r.invite ? " " : null, r.title, r.sub ? el("span", { class: "muted" }, ` · ${r.sub}`) : null),
      r.meet ? el("a", { class: "link", href: r.meet, target: "_blank", rel: "noopener", style: "font-size:12px" }, "Join") : el("span")))
      : [el("div", { class: "muted", style: "font-size:12px" }, "Nothing booked yet.")]));
}

function todoPanel(pipe, tasks, rerender) {
  const today = todayISO();
  const panel = el("div", { class: "panel" });
  const open = pipe ? pipe.columns.filter((c) => !c.closed).flatMap((c) => c.deals.map((d) => ({ ...d, stage: c.stage }))) : [];
  const due = open.filter((d) => d["Next action date"] && d["Next action date"] <= today)
    .sort((a, b) => String(a["Next action date"]).localeCompare(String(b["Next action date"])));
  const noNext = open.filter((d) => !d["Next action"]);
  const list = (tasks && tasks.tasks) || [];
  // A "Today" section in tasks.md (Jonathan, 2026-10-03: "write these as tasks in my CRM for today") shows whole, each
  // box in full with its links; without one, the first six boxes of the Week 0 and Weekly tiers, as before.
  const todays = list.filter((t) => /^Today/i.test(t.section));
  const near = list.filter((t) => /^(Week 0|Weekly)/i.test(t.section));
  const shown = todays.length ? todays : (near.length ? near : list).slice(0, 6);
  panel.append(el("div", { class: "row" }, el("h2", { class: "grow" }, "To do"),
    el("span", { class: "tag" + (due.length ? " lost" : " faint") }, `${due.length} deal${due.length === 1 ? "" : "s"} due`),
    el("a", { class: "link", href: "#/pipeline" }, "Pipeline")));
  if (!due.length) panel.append(el("div", { class: "muted", style: "font-size:13px" }, "No deal action due today."));
  for (const d of due) {
    const late = d["Next action date"] < today;
    const row = el("div", { class: "task-row clickable", tabindex: "0", role: "button" },
      el("div", {}, el("div", {}, el("span", { class: "strong" }, d.company_name || d.Deal), el("span", { class: "muted" }, ` · ${d.stage} · ${money(d.Value, { mo: true })}`)),
        el("div", { class: "muted", style: "font-size:12px" }, d["Next action"])),
      el("span", { class: "tag" + (late ? " lost" : "") }, late ? `${fmtDate(d["Next action date"])} · overdue` : "today"));
    const open_ = () => openDealForm(d, { company: { id: d.company_id, Name: d.company_name, Source: d.Source }, onSaved: rerender });
    row.addEventListener("click", open_);
    row.addEventListener("keydown", (e) => { if (e.key === "Enter") open_(); });
    panel.append(row);
  }
  if (noNext.length) panel.append(el("div", { class: "down", style: "font-size:12px" }, `${noNext.length} open deal${noNext.length === 1 ? "" : "s"} with no next step.`));
  panel.append(el("div", { class: "label", style: "margin-top:6px" }, "Open tasks"));
  if (!shown.length) panel.append(el("div", { class: "muted", style: "font-size:12px" }, "Nothing open in tasks.md."));
  for (const t of shown) {
    const done = el("button", { class: "btn quiet small", type: "button" }, "Done");
    done.addEventListener("click", async () => {
      done.disabled = true;
      try { await api.post("/api/tasks/done", { line: t.line, full: t.full }); toast("Checked off in tasks.md."); rerender(); }
      catch (e) { toast((e.errors || [String(e)]).join(" ")); done.disabled = false; }
    });
    const whole = /^Today/i.test(t.section);
    panel.append(el("div", { class: "task-row" }, el("div", {}, el("div", { style: "font-size:13px" }, ...(whole ? taskNodes(t.full) : [t.text])), el("div", { class: "muted", style: "font-size:11px" }, t.section)), done));
  }
  if (list.length > shown.length) panel.append(el("div", { class: "muted", style: "font-size:12px" }, `${list.length - shown.length} more open in tasks.md.`));
  return panel;
}

// The full text of a Today box: its markdown links become links (new tab), the backticks and bold marks drop.
function taskNodes(text) {
  const s = String(text || "");
  const re = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;
  const plain = (x) => x.replace(/[`*]/g, "");
  const out = [];
  let last = 0, m;
  while ((m = re.exec(s))) {
    if (m.index > last) out.push(plain(s.slice(last, m.index)));
    out.push(el("a", { class: "link", href: m[2], target: "_blank", rel: "noopener" }, m[1]));
    last = m.index + m[0].length;
  }
  if (last < s.length) out.push(plain(s.slice(last)));
  return out;
}

export async function renderToday(root) {
  const target = Number(numbers().dials_per_day || 22);
  // The calendar comes from Google through the booking script (about 3 seconds when not cached), so the page no longer
  // waits for it: it draws at once and the calendar panel fills in when it lands (2026-10-02, the slow-render fix).
  const agendaP = api.get("/api/agenda?days=2").catch(() => ({ source: "offline", events: [], note: "The local server could not fetch the calendar." }));
  const [home, pipe, leads, tasks, queue] = await Promise.all([
    api.home().catch(() => null), api.pipeline().catch(() => null), api.records("Leads").catch(() => []),
    api.get("/api/tasks").catch(() => ({ tasks: [] })),
    api.queue({ limit: target }).catch(() => ({ dialed_today: 0, target, rows: [] })),  // every trade's list in one (2026-10-03)
  ]);
  const rerender = redraw; // in place, keeping the scroll position

  const search = el("input", { class: "search", type: "search", placeholder: "Find any company on the list" });
  const showAll = el("button", { class: "btn quiet small", type: "button" }, "Show the whole list");
  const tableWrap = el("div", { class: "table-wrap", id: "dials" });
  const counter = el("div", { class: "fig num" });
  const progress = el("div", { class: "progress" }, el("b", { style: "width:0%" }));
  const counterTile = el("div", { class: "kpi" }, el("div", { class: "label" }, "Dials today"), counter, progress,
    el("div", { class: "muted", style: "font-size:12px" }, `${target} a day, counted from what you type in Airtable today. Under 100 in a week, everything else pauses.`));

  // Today's dials (the Airtable rows typed today) moved to the Cold call channel page on 2026-10-01
  // (components/sheet-today.js).

  // The campaign card (2026-09-25, Trade Call List; scorecards 2026-09-26): every dial links to the campaign named in
  // Config active_campaign, no-answer included, and a row typed straight into Airtable with the campaign picked counts
  // too. Connect rate = connects / dials. Booking rate = booked / connects. Hidden when no campaign is set.
  const campaignCard = el("section", { class: "panel campaign", hidden: true, "aria-label": "Campaign" });
  function paintCampaign(c) {
    campaignCard.hidden = !c;
    if (!c) return;
    const pct = (v) => (v === null || v === undefined ? "–" : `${v}%`);
    const plural = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;
    const goal = c.goal_booked || 0;
    const refresh = el("button", { class: "btn quiet small", type: "button", title: "Pull in calls typed straight into Airtable" },
      el("span", { class: "ms", "aria-hidden": "true" }, "refresh"), "Refresh");
    refresh.addEventListener("click", async () => {
      refresh.disabled = true;
      try { await api.refresh(); await load(); toast("Up to date with Airtable."); }
      catch (e) { toast((e.errors || [String(e)]).join(" ")); refresh.disabled = false; }
    });
    const score = (cls, label, fig, sub, extra) => el("div", { class: "score " + cls },
      el("div", { class: "label" }, label), el("div", { class: "fig num" }, ...fig), el("div", { class: "sub" }, sub), extra || null);
    const bar = el("div", { class: "progress" + (goal && c.booked >= goal ? " full" : "") }, el("b", { style: `width:${goal ? Math.min(100, Math.round((c.booked / goal) * 100)) : 0}%` }));
    // A call sheet in its own base (2026-09-26): say when it was pulled, what it could not sort, and if it failed.
    const sheets = c.sheets || [];
    const odd = Object.entries(c.unsorted || {});
    const warnings = [
      odd.length ? el("div", { class: "down", style: "font-size:12px" },
        `${odd.reduce((a, [, n]) => a + n, 0)} row${odd.length === 1 && odd[0][1] === 1 ? "" : "s"} in the call sheet have a Status the CRM does not count: ${odd.map(([v, n]) => `${v} (${n})`).join(", ")}. Pick one of the outcomes instead.`) : null,
      ...(c.sheet_errors || []).map((m) => el("div", { class: "down", style: "font-size:12px" }, `Could not read the call sheet. ${m}`)),
    ];
    campaignCard.replaceChildren(
      el("div", { class: "row" },
        el("div", { class: "grow" }, el("div", { class: "label" }, "Campaign"), el("h2", {}, c.name)),
        el("span", { class: "tag won" }, "Live"), refresh),
      el("div", { class: "scorecards" },
        score("blue", "Connect rate", [pct(c.connect_rate)], `${plural(c.connects, "connect")} from ${plural(c.dials, "dial")}`),
        score("green", "Booking rate", [pct(c.booking_rate)], `${c.booked} booked from ${plural(c.connects, "connect")}`),
        score("yellow", "Booked", [String(c.booked), goal ? el("small", {}, ` of ${goal}`) : null], goal ? `${Math.max(0, goal - c.booked)} to go` : "", goal ? bar : null),
        score("red", "Dials", [String(c.dials)], sheets.length
          ? `${c.dials_today || 0} today · ${pct(c.booked_of_dials)} of dials booked · pulled ${c.pulled_at ? clock(c.pulled_at) : "–"}`
          : `${c.dials_today || 0} today · ${pct(c.booked_of_dials)} of dials booked`)),
      ...warnings.filter(Boolean),
      el("div", { class: "muted", style: "font-size:12px" }, sheets.length
        ? [`Reads what you type in Status (typed) in the call sheet (`, ...sheets.flatMap((sh, i) => [i ? ", " : "", sh.url ? el("a", { class: "link", href: sh.url, target: "_blank", rel: "noopener" }, sh.label || "sheet") : sh.label]),
          `): every outcome but Wrong vertical is a dial. Calls logged here count too. Refresh pulls the sheet now; otherwise every 15 minutes.`]
        : `Counts every call logged here, and every Activities row typed in Airtable with Campaign set to ${c.name} and an Outcome picked.`));
  }

  let everything = false;
  function paintCounter(data) {
    counter.replaceChildren(String(data.dialed_today), el("small", {}, ` of ${data.target}`));
    const p = Math.min(100, Math.round((data.dialed_today / data.target) * 100));
    progress.firstChild.style.width = p + "%";
    progress.classList.toggle("full", data.dialed_today >= data.target);
    paintCampaign(data.campaign);
  }
  async function load() {
    const params = { limit: everything ? 0 : target, q: search.value.trim() };
    if (everything || search.value.trim()) params.all = "1";
    const data = await api.queue(params);
    paintCounter(data);
    tableWrap.replaceChildren(table(data.rows));
  }
  function table(rows) {
    if (!rows.length) return el("div", { class: "empty" }, queue.list_rows
      ? "Nothing left on the list for today. Search to find anyone."
      : "No call list yet. Drop a list CSV in projects/outreach and restart the server.");
    const tb = el("tbody");
    rows.forEach((r, i) => {
      const copy = el("button", { class: "copy", type: "button", title: "Copy number" }, "COPY");
      copy.addEventListener("click", (e) => { e.stopPropagation(); copyText(r.phone).then(() => toast("Number copied.")); });
      const tr = el("tr", { class: "clickable" + (r.dialed_today ? " done" : "") },
        el("td", { class: "num muted" }, String(everything || search.value ? r.n : i + 1)),
        el("td", {}, r.name, el("span", { class: "sub" }, [r.city, r.state].filter(Boolean).join(", "), r.county ? ` · ${r.county}` : "")),
        el("td", {}, r.local_time),
        el("td", {}, r.phone ? el("a", { class: "tel", href: telHref(r.phone), onclick: (e) => e.stopPropagation() }, r.phone) : el("span", { class: "muted" }, "no phone"), r.phone ? copy : null),
        el("td", { class: "num" }, r.reviews ? `${r.rating || "–"} (${r.reviews})` : el("span", { class: "muted" }, "0")),
        el("td", { class: "num" }, String(r.attempts || 0), r.last_dial ? el("span", { class: "sub" }, `last ${r.last_dial}`) : null),
        el("td", {}, r.phase ? el("span", { class: "tag" + (r.phase === "Signed" ? " won" : r.phase === "Meeting booked" ? " solid" : "") }, r.phase) : (r.csv_status ? el("span", { class: "tag faint", title: r.csv_status }, "note") : null)),
        el("td", { class: "outcome-cell" }, outcomeSelect(r)));
      tr.addEventListener("click", () => (r.company_id ? navigate(`#/companies/${r.company_id}`) : dial(r)));
      tb.append(tr);
    });
    return el("table", {},
      el("thead", {}, el("tr", {}, el("th", {}, "#"), el("th", {}, "Company"), el("th", {}, "Local at noon ET"), el("th", {}, "Phone"),
        el("th", { class: "num" }, "Reviews"), el("th", { class: "num" }, "Dials"), el("th", {}, "Phase"), el("th", {}, "Outcome"))),
      tb);
  }
  function dial(r, preset) { openDialModal(r, { preset, onLogged: async () => { await load(); refreshHealth(); } }); }
  // The cold caller's dropdown (Jonathan, 2026-09-24): pick the outcome on the row. A no-contact outcome logs at once;
  // a live conversation opens the dial screen with that outcome already picked, for the line it died on and the next step.
  function outcomeSelect(r) {
    const sel = el("select", { class: "outcome", title: "Log this dial" },
      el("option", { value: "" }, "Outcome"),
      ...outcomes().map((o) => el("option", { value: o.name }, o.name)));
    sel.addEventListener("click", (e) => e.stopPropagation());
    sel.addEventListener("change", async (e) => {
      e.stopPropagation();
      const name = sel.value;
      if (!name) return;
      const o = outcome(name);
      if (o && o.class === "contact") { sel.value = ""; dial(r, name); return; }
      sel.disabled = true;
      try {
        const res = await quickDial(r, name);
        toast(res.note || `Logged: ${name}.`);
        await load();
        refreshHealth();
      } catch (err) {
        toast((err.errors || [String(err)]).join(" "));
        sel.disabled = false;
        sel.value = "";
      }
    });
    return sel;
  }
  search.addEventListener("input", debounce(load, 200));
  showAll.addEventListener("click", () => { everything = !everything; showAll.textContent = everything ? "Back to today" : "Show the whole list"; load(); });

  const goal = (home && home.goal) || {};
  const t = home && home.total;
  const sub = t
    ? `${t.won} of ${goal.won || 5} signed by ${fmtDate(goal.by || "2026-12-01")}. ${money(t.open_value)}/mo open across ${t.open} deal${t.open === 1 ? "" : "s"}.`
    : "One line per call. Log where it died. Friday, rewrite that line.";

  paintCounter(queue);
  // First screen (2026-09-29): the inbox brief, the drafts to approve, and the calendar. The calls, the campaign, and
  // the to-do list follow below.
  const mail = mailPanels();
  const calSlot = el("section", { class: "panel top-panel", "aria-label": "Calendar" },
    el("div", { class: "row" }, el("h2", { class: "grow" }, "Calendar")), el("div", { class: "muted", style: "font-size:13px" }, "Reading the calendar..."));
  agendaP.then((agenda) => { if (calSlot.isConnected) calSlot.replaceWith(calendarPanel(agenda, leads, queue.dialed_today || 0, target)); });
  root.append(
    el("div", { class: "head" },
      el("div", {}, el("div", { class: "label" }, new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })),
        el("h1", {}, "Today"),
        el("div", { class: "sub" }, sub))),
    el("div", { class: "today-top" }, mail.inbox, mail.drafts, calSlot),
    el("div", { class: "row today-calls" }, clockBlock(), counterTile),
    campaignCard,
    todoPanel(pipe, tasks, rerender),
    el("details", { class: "call-list" },
      el("summary", {}, "The CRM's call list", queue.list_file ? el("span", { class: "muted", style: "font-size:12px;font-weight:400;margin-left:8px" }, `${queue.list_rows} on the list, every trade, for dialing and logging here`) : null),
      el("div", { class: "row" }, el("span", { class: "grow" }), search, showAll),
      tableWrap));
  tableWrap.replaceChildren(table(queue.rows || []));
}
