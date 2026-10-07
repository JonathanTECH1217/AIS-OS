// Monarc Edge (2026-10-04): the page. One file, no framework. Reads the state bundle from scripts/edge_server.py
// (projects/edge/API.md), draws the three tabs, and long-polls /api/state for changes. Jonathan reads each card in
// plain words ("Bet: Chelsea wins", "We think 38 out of 100"), clicks "Yes, bet it" or "Skip", and watches the record
// build toward the gate that unlocks auto mode. The trader numbers stay under "Show the math".
// ?test=<name> loads tests/t-<name>.js instead of starting; the test fakes fetch and calls window.__edge.boot().

const NY = "America/New_York";
const params = new URLSearchParams(location.search);
const TEST = params.get("test");

// ---------------------------------------------------------------- DOM helpers
// Text only: every string becomes a text node, never markup, so a team name or a reasoning line cannot inject.
function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "value") node.value = v;
    else if (k === "checked") node.checked = !!v;
    else if (k === "disabled") node.disabled = !!v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else if (k === "dataset") Object.assign(node.dataset, v);
    else if (v === true) node.setAttribute(k, "");
    else node.setAttribute(k, v);
  }
  append(node, children);
  return node;
}
function append(node, children) {
  for (const c of children.flat(Infinity)) {
    if (c === null || c === undefined || c === false) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return node;
}
function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); return node; }
function icon(name, cls = "") { return el("span", { class: "ms " + cls, "aria-hidden": "true" }, name); }
function svgEl(tag, attrs = {}, ...children) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== null && v !== undefined) node.setAttribute(k, v);
  for (const c of children) node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return node;
}
const $ = (sel, root = document) => root.querySelector(sel);
const clone = (o) => JSON.parse(JSON.stringify(o));
const isNum = (v) => typeof v === "number" && !Number.isNaN(v);
const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;

// ---------------------------------------------------------------- numbers and times
const usdFmt = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2, maximumFractionDigits: 2 });
const usd0Fmt = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const intFmt = new Intl.NumberFormat("en-US");
function usd(n) { return isNum(n) ? usdFmt.format(n) : "n/a"; }
function usdSigned(n) { return isNum(n) ? (n > 0 ? "+" : "") + usdFmt.format(n) : "n/a"; }
function usdRound(n) { return isNum(n) ? usd0Fmt.format(n) : "n/a"; }
function cents(p) { return isNum(p) ? Math.round(p * 100) + "c" : "n/a"; }
function pts(x, d = 1) { if (!isNum(x)) return "n/a"; const s = x.toFixed(d); return x > 0 ? "+" + s : s; }
function pctOf(frac, d = 0) { return isNum(frac) ? (frac * 100).toFixed(d) + "%" : "n/a"; }
function num(n) { return isNum(n) ? intFmt.format(n) : "n/a"; }
function bandWords(b) { return String(b || "").replace(/^(\d+)-(\d+)$/, "$1 to $2"); }
const HOURS_WORDS = { "0-1h": "under 1 hour before", "1-3h": "1 to 3 hours before", "3-12h": "3 to 12 hours before", "12-24h": "12 to 24 hours before", "1-3d": "1 to 3 days before", "3d+": "3 or more days before" };
function hoursWords(b) { return HOURS_WORDS[b] || String(b || ""); }

function parts(iso, opts) {
  const d = iso instanceof Date ? iso : new Date(iso);
  if (!iso || Number.isNaN(d.getTime())) return null;
  const p = new Intl.DateTimeFormat("en-US", { timeZone: NY, ...opts }).formatToParts(d);
  const get = (t) => (p.find((x) => x.type === t) || {}).value || "";
  return { get, d };
}
// "Sun 2:30 PM"
function fmtKick(iso) {
  const p = parts(iso, { weekday: "short", hour: "numeric", minute: "2-digit" });
  return p ? `${p.get("weekday")} ${p.get("hour")}:${p.get("minute")} ${p.get("dayPeriod")}` : "";
}
// "6:12 PM"
function fmtTime(iso) {
  const p = parts(iso, { hour: "numeric", minute: "2-digit" });
  return p ? `${p.get("hour")}:${p.get("minute")} ${p.get("dayPeriod")}` : "n/a";
}
// "Oct 10, 6:12 PM"
function fmtStamp(iso) {
  const p = parts(iso, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
  return p ? `${p.get("month")} ${p.get("day")}, ${p.get("hour")}:${p.get("minute")} ${p.get("dayPeriod")}` : "n/a";
}
// "Oct 10"
function fmtDay(iso) {
  const p = parts(iso, { month: "short", day: "numeric" });
  return p ? `${p.get("month")} ${p.get("day")}` : "";
}
// "14:05"
function fmtClock(d) {
  const p = parts(d, { hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
  return p ? `${p.get("hour")}:${p.get("minute")}` : "";
}
// "in 20 hours", "in 45 minutes", "in 6 days", "started", "over"; measured from the bundle's clock, not the laptop's
function fmtUntil(kickIso, nowIso) {
  const k = new Date(kickIso).getTime(), n = new Date(nowIso || Date.now()).getTime();
  if (Number.isNaN(k) || Number.isNaN(n)) return "";
  const h = (k - n) / 3.6e6;
  if (h < -2.2) return "over";
  if (h <= 0) return "started";
  if (h < 1) return "in " + plural(Math.max(1, Math.round(h * 60)), "minute", "minutes");
  if (h < 48) return "in " + plural(Math.round(h), "hour", "hours");
  return "in " + plural(Math.round(h / 24), "day", "days");
}

// ---------------------------------------------------------------- state
const State = {
  rev: 0, bundle: null, record: null, config: null, draft: null, health: null, backtest: null,
  tab: "today", open: {}, busy: {}, errors: {}, connected: true, ask: false, haltOpen: false,
  saving: false, saveMsg: "", saveErrors: [], ticking: false, btTimer: null, recordLoading: false,
};
const cfg = () => (State.bundle && State.bundle.config) || {};

async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
  const r = await fetch(path, opts);
  let data = null;
  try { data = await r.json(); } catch (e) { data = null; }
  return { ok: r.ok, status: r.status, data };
}

function applyBundle(b) {
  if (!b || typeof b !== "object") return;
  const gateWas = State.bundle && State.bundle.gate ? State.bundle.gate.passed : null;
  State.bundle = b;
  State.rev = b.rev || 0;
  if (!b.halted) { State.ask = false; State.haltOpen = false; }
  renderTopbar();
  renderBanner();
  if (State.tab === "today") renderToday();
  else if (State.tab === "record") { renderRecord(); loadRecord(); }
  else if (State.tab === "settings" && State.draft && gateWas !== b.gate.passed) renderSettings();
}

// ---------------------------------------------------------------- routing
const TABS = [["today", "Today"], ["record", "Record"], ["settings", "Settings"]];
function tabFromHash() {
  const m = /^#\/(today|record|settings)/.exec(location.hash);
  if (m) return m[1];
  try { const t = localStorage.getItem("edge.tab"); if (TABS.some(([k]) => k === t)) return t; } catch (e) { /* storage may be off */ }
  return "today";
}
function go(tab) {
  if (!TABS.some(([k]) => k === tab)) tab = "today";
  State.tab = tab;
  try { localStorage.setItem("edge.tab", tab); } catch (e) { /* storage may be off */ }
  if (location.hash !== "#/" + tab) history.replaceState(null, "", "#/" + tab);
  render();
}
window.addEventListener("hashchange", () => { const t = tabFromHash(); if (t !== State.tab) go(t); });

// ---------------------------------------------------------------- top bar
function renderTopbar() {
  const host = clear($("#topbar"));
  const b = State.bundle || {};
  const c = b.config || {};
  const bank = (b.record && b.record.bankroll) || {};
  const env = c.env || "demo";
  host.append(
    el("div", { class: "tb-left" },
      el("div", { class: "mark", "aria-hidden": "true" }, "E"),
      el("span", { class: "tb-name" }, "Monarc Edge"),
      el("span", { class: "badge env-" + env, title: env === "prod" ? "The real Kalshi exchange, real money" : "Kalshi's practice exchange, play money" },
        env === "prod" ? "Live account" : "Practice account"),
      el("span", { class: "badge mode-" + (c.mode || "approve") }, c.mode === "auto" ? "Auto" : "You approve each bet"),
      c.dry_run ? el("span", { class: "badge paper", title: c.paper_auto !== false
        ? "No real order leaves the machine; ready cards are paper-bet by themselves"
        : "Dry run: orders are written to a file, not sent" }, "Paper money") : null),
    el("nav", { class: "tb-tabs", role: "tablist" },
      TABS.map(([k, label]) => el("button", { class: "tab" + (State.tab === k ? " is-on" : ""), type: "button", role: "tab",
        "aria-selected": State.tab === k ? "true" : "false", onclick: () => go(k) }, label))),
    el("div", { class: "tb-right" },
      el("span", { class: "tb-bal num", title: c.dry_run ? "Paper money, counting open bets at what they cost" : "Money, counting open bets at what they cost" }, icon("account_balance_wallet"), (c.dry_run ? "Paper " : "") + usd(isNum(bank.equity) ? bank.equity : bank.balance)),
      isNum(b.sync && b.sync.football_remaining) ? el("span", { class: "tb-calls num", title: "API-Football calls left today" }, `Football calls left: ${num(b.sync.football_remaining)}`) : null,
      el("button", { class: "icon-btn" + (State.ticking ? " spin" : ""), type: "button", title: "Check the markets now", "aria-label": "Refresh", disabled: State.ticking, onclick: tick }, icon("refresh")),
      el("span", { class: "tb-clock num", id: "clock", title: "New York time" }, fmtClock(new Date()))));
}

async function tick() {
  if (State.ticking) return;
  State.ticking = true; renderTopbar();
  try { await api("POST", "/api/tick"); } catch (e) { /* the long poll reports a lost server */ }
  State.ticking = false; renderTopbar();
}

const HALT_WORDS = {
  sports_gone: "Kalshi lists no Premier League markets right now. Check the app and the Maryland case.",
  state_block: "Kalshi refused an order for this account's location. Check the app and Maryland v. Kalshi.",
  drawdown: "The balance fell 25% below its peak. Auto mode is off.",
};

function renderBanner() {
  const host = clear($("#banner"));
  const b = State.bundle;
  if (!b || !b.halted) return;
  const halts = (b.halts || []).filter((h) => !h.cleared_at);
  const h = (halts.length ? halts : b.halts || []).slice().sort((x, y) => String(y.ts).localeCompare(String(x.ts)))[0] || {};
  let words = HALT_WORDS[h.reason] || `The agent stopped (${h.reason || "no reason given"}).`;
  if (h.reason === "drawdown" && b.config && b.config.drawdown) words = words.replace("25%", `${b.config.drawdown.pct}%`);
  const right = State.ask
    ? el("span", { class: "halt-ask" }, "Resume trading?",
        el("button", { class: "btn halt-resume", type: "button", onclick: clearHalt }, "Yes"),
        el("button", { class: "link", type: "button", onclick: () => { State.ask = false; renderBanner(); } }, "No"))
    : el("button", { class: "btn halt-resume", type: "button", onclick: () => { State.ask = true; renderBanner(); } }, "Resume");
  host.append(el("div", { class: "halt", role: "alert" },
    icon("error"),
    el("span", { class: "halt-text" }, words),
    h.detail ? el("button", { class: "link", type: "button", "aria-expanded": State.haltOpen ? "true" : "false",
      onclick: () => { State.haltOpen = !State.haltOpen; renderBanner(); } }, State.haltOpen ? "Hide details" : "Details") : null,
    el("span", { class: "grow" }),
    right,
    State.haltOpen && h.detail ? el("div", { class: "halt-detail" }, `${fmtStamp(h.ts)}: ${h.detail}`) : null));
}

async function clearHalt() {
  State.ask = false;
  const r = await api("POST", "/api/halt/clear");
  if (r.ok && State.bundle) { State.bundle.halted = false; renderBanner(); renderToday(); }
  else renderBanner();
}

// ---------------------------------------------------------------- Today: a card in plain words
const STATE_WORDS = {
  watching: "Watching", ready: "Ready to bet", no_edge: "No bet", approved: "Sending", placed: "Bet placed, waiting",
  partial: "Partly on", filled: "Bet on", unfilled: "Did not fill", passed: "Skipped", expired: "Missed (kickoff passed)",
  delisted: "Market pulled", halted: "Stopped", error: "Problem",
};
const LIVE = new Set(["approved", "placed", "partial", "filled"]);

function cardWon(c) {
  if (isNum(c.pnl_usd)) return c.pnl_usd > 0;
  return c.result != null && c.side != null && c.result === c.side;
}
function isPaper(c) { return c.paper === 1 || !!cfg().dry_run; }
function stateChip(c) {
  let words = STATE_WORDS[c.state] || c.state, cls = "st-" + c.state;
  if (c.state === "settled") { const won = cardWon(c); words = won ? "Won" : "Lost"; cls = won ? "st-won" : "st-lost"; }
  else if (c.state === "filled" && c.paper === 1) words = "Paper bet on";
  return el("span", { class: "chip-status " + cls }, words);
}
// "Bet: Chelsea wins", "Bet: Chelsea does not win", "Bet: it ends in a draw", "Bet: it does not end in a draw";
// with no side (nothing to bet) a plain label: "Chelsea wins", "It ends in a draw"
function betWords(c) {
  const name = c.outcome === "draw" ? null : (c.outcome_name || (c.outcome === "home" ? c.home : c.away) || "The team");
  if (c.side === "yes") return name ? `Bet: ${name} wins` : "Bet: it ends in a draw";
  if (c.side === "no") return name ? `Bet: ${name} does not win` : "Bet: it does not end in a draw";
  return name ? `${name} wins` : "It ends in a draw";
}
function sideChance(c) { return c.side === "no" ? 1 - c.model_p : c.model_p; }
function gapClass(color) { return color === "green" ? "up" : color === "red" ? "down" : (color === "amber" || color === "yellow") ? "warn" : ""; }
function gapWords(c) {
  const g = Math.round(c.gap_points || 0);
  const floor = isNum(cfg().gap_floor_points) ? cfg().gap_floor_points : 7;
  if (c.color === "green") return { main: plural(g, "point", "points") + " in our favor", small: "after Kalshi's fee" };
  if (c.color === "yellow") return { main: plural(g, "point", "points") + " in our favor", small: "big gap: the model may be wrong" };
  if (c.color === "amber") { const short = Math.max(1, Math.round(floor - (c.gap_points || 0))); return { main: plural(short, "point", "points") + " short", small: `we need ${floor}` }; }
  return { main: "Not in our favor", small: "Kalshi's price is better than ours" };
}
function isOpen(c) {
  if (c.id in State.open) return State.open[c.id];
  return c.color === "green" || LIVE.has(c.state);
}
function pricePaid(c) {
  if (isNum(c.avg_fill) && c.avg_fill > 0) return c.avg_fill;
  if (isNum(c.limit_price)) return c.limit_price;
  return c.market_price;
}
function expectedFee(c) {
  if (isNum(c.fees_paid) && c.fees_paid > 0) return c.fees_paid;
  const rate = (cfg().fees && cfg().fees.taker_rate) || 0.07;
  const p = pricePaid(c);
  if (!isNum(c.count) || !isNum(p)) return null;
  return c.count * rate * p * (1 - p);
}
// "Paper: risk $71 to win $188"
function moneyWords(c) {
  const p = pricePaid(c);
  if (!isNum(c.count) || c.count <= 0 || !isNum(p)) return null;
  const fee = expectedFee(c) || 0;
  const risk = Math.round(c.count * p + fee), win = Math.round(c.count * (1 - p) - fee);
  return `${isPaper(c) ? "Paper: risk" : "Risk"} $${num(risk)} to win $${num(win)}`;
}
// the server's flags in sixth-grade words; null hides one
function flagWords(f, all) {
  const s = String(f || "").trim();
  const hasLineups = all.some((x) => /lineup/i.test(x) && !/feed/i.test(x));
  if (/^no lineups?( yet)?$/i.test(s)) return "Lineups not out yet";
  if (/^(no lineup feed|lineup feed missing)$/i.test(s)) return hasLineups ? null : "Lineups not out yet";
  if (/^lineups posted$/i.test(s)) return "Lineups are out";
  if (/^(polymarket disagrees|second witness disagrees)$/i.test(s)) return "Polymarket agrees with Kalshi, not with us";
  if (/^kickoff from kalshi$/i.test(s)) return "Kickoff time is a guess";
  if (/^thin market/i.test(s)) return "Too few people trading this";
  if (/^big gap/i.test(s)) return "Big gap: the model may be wrong, check the news";
  if (/^paper fill at the ask$/i.test(s)) return "Paper bet";
  const m = /^larger edge on (.+)$/i.exec(s);
  if (m) return `Better bet on ${m[1]} in this match`;
  if (/^expired at kickoff$/i.test(s)) return null;
  if (/^reasoning failed/i.test(s)) return "No note yet";
  return s;
}
function flagKind(words) { return /are out|Paper bet|Better bet/.test(words) ? "info" : "warn"; }

// the trader line, under "Show the math"
function mathLine(c) {
  const no = c.side === "no";
  const n = (k, v, title) => el("span", { class: "n", title }, el("span", { class: "k" }, k), el("span", { class: "v" }, v));
  const kalshi = no
    ? `No ${cents(c.market_price != null ? c.market_price : 1 - c.market_yes_bid)} ask (Yes ${cents(c.market_yes_bid)} / ${cents(c.market_yes_ask)})`
    : `${cents(c.market_yes_ask)} ask, ${cents(c.market_yes_bid)} bid`;
  const out = [
    n(no ? "Our chance of No" : "Our chance", pctOf(sideChance(c)), "The model's chance for the side we would buy"),
    n("Kalshi", kalshi, "Kalshi's book for the Yes contract"),
    n("Break-even", pctOf(c.break_even, 1), "The chance the price needs to be fair, after the fee"),
    n("Polymarket", isNum(c.poly_mid) ? cents(c.poly_mid) : "no read", "The second witness's mid price for Yes"),
    n("Gap", pts(c.gap_points) + " pts", "Our chance minus the break-even"),
  ];
  if (isNum(c.stake_usd) && isNum(c.count)) out.push(n("Stake", `${usd(c.stake_usd)} = ${num(c.count)} at ${isNum(c.limit_price) ? c.limit_price.toFixed(2) : "n/a"}`, "Dollars, contracts, and the limit price"));
  const fee = expectedFee(c);
  if (isNum(fee)) out.push(n("Fee", usd(fee), isNum(c.fees_paid) && c.fees_paid > 0 ? "Fees paid" : "Kalshi's taker fee if filled at the limit"));
  if (c.band) out.push(n("Band", bandWords(c.band), "Which chance band this card counts in"));
  if (c.hours_band) out.push(n("Timing", hoursWords(c.hours_band), "Hours to kickoff when priced"));
  if (isNum(c.clv_points)) out.push(n("CLV", pts(c.clv_points) + " pts", "Closing line value: how far the market moved our way by kickoff"));
  return el("div", { class: "nums num" }, out);
}

function renderCard(c) {
  const b = State.bundle || {};
  const open = isOpen(c), fold = !(c.color === "green" || LIVE.has(c.state));
  const busy = !!State.busy[c.id];
  const canApprove = !!c.can_approve && !b.halted;
  const gw = gapWords(c);
  const card = el("article", { class: ["card", c.color, LIVE.has(c.state) ? "is-live" : "", fold ? "is-fold" : "", open ? "is-open" : ""].join(" ").trim(), dataset: { id: c.id, state: c.state } });
  const toggle = () => { State.open[c.id] = !open; rerenderCard(c.id); };
  const r1 = el("div", { class: "card-r1", onclick: fold ? (e) => { if (e.target.closest("button")) return; toggle(); } : null },
    el("span", { class: "card-title" }, betWords(c)),
    stateChip(c),
    el("span", { class: "grow" }),
    fold ? el("button", { class: "icon-btn small fold", type: "button", "aria-expanded": open ? "true" : "false", title: open ? "Show less" : "Show more",
      onclick: toggle }, icon(open ? "expand_less" : "expand_more")) : null);
  const big = (k, v) => el("div", { class: "bignum" }, el("span", { class: "k" }, k), el("b", {}, isNum(v) ? String(Math.round(v * 100)) : "?"), el("span", { class: "of" }, "out of 100"));
  const r2 = el("div", { class: "card-r2" },
    el("div", { class: "bignums" }, big("We think", sideChance(c)), big("Kalshi's price says", c.market_price)),
    el("span", { class: "gap " + gapClass(c.color), title: `Gap ${pts(c.gap_points)} points after the fee` }, el("b", {}, gw.main), el("small", {}, gw.small)));
  card.append(r1, r2);
  // a refused request shows even on a folded card
  const errs = State.errors[c.id] || [];
  if (errs.length) card.append(el("div", { class: "card-errors", role: "alert" }, errs.map((x) => el("div", {}, x))));
  if (!fold || open) {
    const raw = (c.flags || []).slice();
    if (c.busy_ok === 0 && c.busy_reason) raw.unshift("thin market: " + c.busy_reason);
    const seen = new Set();
    const flags = raw.map((f) => flagWords(f, raw)).filter((w) => w && !seen.has(w) && seen.add(w))
      .map((w) => el("span", { class: "chip flag-" + flagKind(w) }, icon(flagKind(w) === "info" ? "info" : "warning"), w));
    const money = moneyWords(c);
    const result = c.state === "settled" && isNum(c.pnl_usd) ? el("span", { class: "result " + (c.pnl_usd > 0 ? "up" : "down") }, `${c.pnl_usd > 0 ? "Won" : "Lost"} ${usd(Math.abs(c.pnl_usd))}`) : null;
    const math = el("details", { class: "math" },
      el("summary", {}, icon("expand_more"), "Show the math"),
      el("div", { class: "math-body" }, mathLine(c),
        el("div", { class: "sources" }, (c.sources || []).length ? "Sources: " + c.sources.join("; ") : "Sources not recorded")));
    math.addEventListener("toggle", () => { const s = math.querySelector("summary"); clear(s).append(icon(math.open ? "expand_less" : "expand_more"), math.open ? "Hide the math" : "Show the math"); });
    const more = el("div", { class: "card-more" },
      money || result ? el("div", { class: "money" }, money, result) : null,
      el("div", { class: "why" }, el("span", { class: "lbl" }, "Why"),
        c.reasoning ? el("p", { class: "reasoning" }, c.reasoning) : el("p", { class: "reasoning muted" }, "No note yet. The agent writes one when the card is ready to bet.")),
      flags.length ? el("div", { class: "flags" }, flags) : null,
      math);
    const actions = [];
    if (canApprove) {
      actions.push(el("button", { class: "btn small btn-approve", type: "button", disabled: busy, onclick: () => act(c.id, "approve") }, icon("check"), cfg().dry_run ? "Yes, paper bet" : "Yes, bet it"));
      actions.push(el("button", { class: "link btn-pass", type: "button", disabled: busy, onclick: () => act(c.id, "pass") }, "Skip"));
    }
    if (c.state === "placed" || c.state === "partial") {
      actions.push(el("button", { class: "link btn-cancel", type: "button", disabled: busy, onclick: () => act(c.id, "cancel") }, "Cancel bet"));
    }
    if (actions.length) more.append(el("div", { class: "card-actions" }, actions));
    card.append(more);
  }
  return card;
}

function rerenderCard(id) {
  const old = $(`.card[data-id="${CSS.escape(id)}"]`);
  const c = (State.bundle.cards || []).find((x) => x.id === id);
  if (old && c) old.replaceWith(renderCard(c)); else renderToday();
}

// approve, pass, cancel: one request at a time per card; the answer's card replaces ours
async function act(id, what) {
  if (State.busy[id]) return;
  State.busy[id] = true; delete State.errors[id]; rerenderCard(id);
  let r;
  try { r = await api("POST", `/api/cards/${encodeURIComponent(id)}/${what}`); }
  catch (e) { r = { ok: false, status: 0, data: { errors: ["The agent did not answer. Is the server running?"] } }; }
  delete State.busy[id];
  const cards = State.bundle.cards || [];
  const i = cards.findIndex((x) => x.id === id);
  const fresh = r.ok ? r.data : r.data && r.data.card;
  if (fresh && fresh.id && i >= 0) cards[i] = fresh;
  if (!r.ok) State.errors[id] = (r.data && r.data.errors) || [`The request failed (${r.status || "no answer"}).`];
  if (r.ok && what === "approve") State.open[id] = true;
  rerenderCard(id);
}

function fixturesOf(cards) {
  const map = new Map();
  for (const c of cards) {
    const key = c.fixture_id || `${c.home}|${c.away}|${c.kickoff_utc}`;
    if (!map.has(key)) map.set(key, { id: key, home: c.home, away: c.away, kickoff: c.kickoff_utc, event: c.event_ticker, cards: [] });
    map.get(key).cards.push(c);
  }
  const out = [...map.values()];
  const now = new Date((State.bundle && State.bundle.now) || Date.now()).getTime();
  for (const f of out) {
    f.cards.sort((a, b) => (isNum(b.gap_points) ? b.gap_points : -999) - (isNum(a.gap_points) ? a.gap_points : -999));
    f.needsHim = f.cards.some((c) => c.can_approve) ? 0 : 1;
    f.ended = new Date(f.kickoff).getTime() < now - 2.2 * 3.6e6 ? 1 : 0;
  }
  // what needs his click first, then by kickoff, matches that are over last
  out.sort((a, b) => a.needsHim - b.needsHim || a.ended - b.ended || String(a.kickoff).localeCompare(String(b.kickoff)));
  return out;
}
function priceChip(f) {
  const b = State.bundle || {};
  const unl = (b.unlinked || []).some((u) => u.fixture_id && u.fixture_id === f.id);
  const poly = f.cards.some((c) => isNum(c.poly_mid));
  if (unl) return el("span", { class: "chip flag-warn", title: "A team name did not match; see Could not match" }, icon("warning"), "Could not match this match");
  if (!f.event) return el("span", { class: "chip" }, "No Kalshi market yet");
  return el("span", { class: "chip", title: f.event }, poly ? "Prices from Kalshi and Polymarket" : "Prices from Kalshi");
}

function renderToday() {
  const main = $("#main");
  if (State.tab !== "today") return;
  const prev = $("#cards"); const scroll = prev ? prev.scrollTop : 0;
  const b = State.bundle || {};
  const cards = b.cards || [];
  const col = el("div", { class: "cards", id: "cards" });
  if (!cards.length) {
    col.append(el("div", { class: "empty" }, icon("sports_soccer"),
      el("div", {}, "No Premier League markets priced yet. The agent looks 16 days ahead and prices cards from 24 hours before kickoff.")));
  } else {
    for (const f of fixturesOf(cards)) {
      col.append(el("section", { class: "fixture", dataset: { fixture: f.id } },
        el("div", { class: "fx-head" },
          el("h2", {}, `${f.home} vs ${f.away}`),
          el("span", { class: "chip num", title: "Kickoff, New York time" }, icon("schedule"), fmtKick(f.kickoff)),
          el("span", { class: "chip num" }, icon("timer"), fmtUntil(f.kickoff, b.now)),
          priceChip(f)),
        f.cards.map(renderCard)));
    }
  }
  clear(main).append(el("div", { class: "view today" }, col, renderSide()));
  $("#cards").scrollTop = scroll;
}

function lightColors(g, rec) {
  const L = (g && g.lights) || {};
  const count = L.count || {}, cal = L.calibration || {}, profit = L.profit || {}, clv = L.clv || {};
  const bands = cal.bands || (rec && rec.bands) || [];
  const judged = bands.filter((x) => x.light && x.light !== "grey");
  const settled = isNum(count.value) ? count.value : (rec && rec.settled) || 0;
  const worst = judged.map((x) => ({ band: x.band, off: Math.abs((x.model_mean || 0) - (x.hit_rate || 0)) * 100 })).sort((a, b) => b.off - a.off)[0] || null;
  return {
    count: count.ok ? "up" : settled > 0 ? "down" : "muted",
    calibration: cal.ok ? "up" : judged.some((x) => x.light === "red") || (cal.pooled && cal.pooled.n > 0 && cal.pooled.within === false && judged.length) ? "down" : "muted",
    profit: profit.ok ? "up" : settled > 0 ? "down" : "muted",
    clv: clv.ok ? "up" : clv.n > 0 ? "down" : "muted",
    judged, within: judged.filter((x) => x.within).length, worst,
  };
}
// "yes", "not enough bets yet", "no, the 30 to 40 band is off"
function matchWords(g, lc) {
  const cal = (g.lights || {}).calibration || {};
  if (cal.ok) return "yes";
  if (!lc.judged.length) return "not enough bets yet";
  if (lc.judged.every((x) => x.within) && cal.pooled && cal.pooled.within === false) return "no, all bets together are off";
  return lc.worst ? `no, the ${bandWords(lc.worst.band)} band is off` : "no";
}

function renderSide() {
  const b = State.bundle || {};
  const c = b.config || {};
  const g = b.gate || { lights: {} }, rec = b.record || {}, bank = rec.bankroll || {}, sync = b.sync || {};
  const L = g.lights || {};
  const lc = lightColors(g, rec);
  const row = (cls, words) => el("div", { class: "light-row" }, el("span", { class: "dot " + cls }), el("span", { class: "num" }, words));
  const clv = L.clv || {};
  const gate = el("section", { class: "panel gate-mini", "aria-label": "Gate" },
    el("h3", {}, "Before auto mode can turn on"),
    row(lc.count, `Bets settled: ${num((L.count || {}).value)} of ${num((L.count || {}).need)}`),
    row(lc.calibration, `Our guesses match results: ${matchWords(g, lc)}`),
    row(lc.profit, `Money made after fees: ${usdSigned((L.profit || {}).value)}`),
    row(lc.clv, `Beat the closing price: ${clv.n > 0 && isNum(clv.value) ? `${pts(clv.value)} points, need ${isNum(clv.need) ? clv.need : 5}` : "no data yet"}`),
    el("div", { class: "lock-line" + (g.passed ? " ok" : "") }, icon(g.passed ? "lock_open" : "lock"), g.passed ? "All four are green. Auto mode can turn on." : "Auto mode stays off until all four are green"));
  const kv = (k, v, cls = "") => el("div", { class: "kv" }, el("span", { class: "k" }, k), el("span", { class: "v " + cls }, v));
  const acct = b.account || null;
  const bankroll = el("section", { class: "panel", "aria-label": "Bankroll" },
    el("h3", {}, c.dry_run ? "Paper money" : "Money"),
    el("div", { class: "grid2" },
      kv("Balance", usd(bank.balance), "big"), kv("With open bets", usd(bank.equity), "big"),
      kv("Best so far", usd(bank.peak)), kv("Drop from best", isNum(bank.drawdown_pct) ? bank.drawdown_pct.toFixed(1) + "%" : "n/a", bank.drawdown_pct > 0 ? "down" : "")),
    acct ? [el("div", { class: "grid2", style: "margin-top:8px" },
      kv("Kalshi account (" + (acct.env || "").toUpperCase() + ")", acct.error ? "no read" : usd(acct.balance_usd), acct.error ? "down" : ""),
      kv("Open positions", acct.error ? "no read" : String(acct.positions == null ? 0 : acct.positions), acct.error ? "down" : "")),
      acct.error ? el("div", { class: "warn small", style: "padding-top:4px" }, String(acct.error)) : null]
      : el("div", { class: "muted small", style: "margin-top:8px" }, "No Kalshi account key: paper only."));
  const r = (k, v, cls = "") => el("div", { class: "r" }, el("span", { class: "muted" }, k), el("span", { class: cls }, v));
  const checks = el("section", { class: "panel", "aria-label": "Checks" },
    el("h3", {}, "Checks"),
    el("div", { class: "sync-list" },
      r("Last market check", fmtTime(sync.markets_at)),
      r("Last match list check", fmtTime(sync.fixtures_at)),
      r("Markets open", num(sync.open_markets)),
      r("Polymarket", sync.poly_ok ? "working" : "not answering", sync.poly_ok ? "up" : "warn"),
      sync.last_error ? el("div", { class: "warn small", style: "padding-top:4px" }, sync.last_error) : null));
  const unl = b.unlinked || [];
  const unlinked = el("section", { class: "panel", "aria-label": "Could not match" },
    el("h3", {}, "Could not match"),
    unl.length
      ? el("div", { class: "unl" }, unl.map((u) => el("div", {}, el("code", {}, (u.names || []).join(" / ") || u.kalshi_event || u.poly_slug || "?"),
          u.kalshi_event && (u.names || []).length ? ` (${u.kalshi_event})` : "", "; fix in teams.json")))
      : el("div", { class: "unl" }, "Every market matched a fixture."));
  return el("aside", { class: "side", id: "side" }, gate, bankroll, checks, unlinked);
}

// ---------------------------------------------------------------- Record
async function loadRecord() {
  if (State.recordLoading) return;
  State.recordLoading = true;
  try {
    const r = await api("GET", "/api/record");
    if (r.ok && r.data) { State.record = r.data; if (State.tab === "record") renderRecord(); }
  } catch (e) { /* the summary in the bundle stands in */ }
  State.recordLoading = false;
}

function gateReadings(g, rec, c) {
  const L = (g && g.lights) || {};
  const gc = (c && c.gate) || {};
  const minN = gc.min_band_n != null ? gc.min_band_n : 30, tol = gc.band_tolerance_points != null ? gc.band_tolerance_points : 5;
  const lc = lightColors(g, rec);
  const count = L.count || {}, cal = L.calibration || {}, profit = L.profit || {}, clv = L.clv || {};
  const toGo = Math.max(0, (count.need || 0) - (count.value || 0));
  let calWords;
  if (cal.ok) { calWords = `Every band with ${minN} or more cards is within ${tol} points.`; }
  else if (!lc.judged.length) { calWords = `No band has ${minN} cards yet.`; }
  else {
    calWords = cal.pooled && cal.pooled.within === false && lc.judged.every((x) => x.within)
      ? `All cards together are ${(Math.abs((cal.pooled.model_mean || 0) - (cal.pooled.hit_rate || 0)) * 100).toFixed(1)} points off.`
      : `The ${bandWords(lc.worst.band)} band is ${lc.worst.off.toFixed(1)} points off.`;
  }
  const calVal = lc.judged.length ? `${lc.within} of ${lc.judged.length}` : "0 of 0";
  return [
    { key: "count", label: "Bets settled", cls: lc.count, value: num(count.value), need: `of ${num(count.need)} needed`,
      words: count.ok ? `${num(count.value)} settled cards. Gate met.` : `${num(count.value)} settled cards. ${num(toGo)} to go.` },
    { key: "calibration", label: "Our guesses match results", cls: lc.calibration, value: calVal, need: `bands with ${minN} or more bets within ${tol} points`, words: calWords },
    { key: "profit", label: "Money made after fees", cls: lc.profit, value: usdSigned(profit.value), need: "must be above zero",
      words: `Return after fees: ${usdSigned(rec.pnl_usd)} on ${usdRound(rec.staked_usd)} staked (${pts(rec.return_pct)}%).` },
    { key: "clv", label: "Beat the closing price", cls: lc.clv, value: isNum(clv.value) ? pts(clv.value) + " pts" : "n/a", need: `${isNum(clv.need) ? clv.need.toFixed(1) : "5.0"} points needed`,
      words: clv.n > 0 ? `Average closing line value ${pts(clv.value)} points over ${num(clv.n)} cards; ${isNum(clv.need) ? clv.need : 5} needed.`
        : `No closing lines yet; ${isNum(clv.need) ? clv.need : 5} points needed.` },
  ];
}

function table(heads, rows, cls = "") {
  return el("table", { class: "tbl " + cls },
    el("thead", {}, el("tr", {}, heads.map((h) => el("th", {}, h)))),
    el("tbody", {}, rows.length ? rows.map((r) => el("tr", {}, r.map((x) => (x instanceof Node && x.tagName === "TD") ? x : el("td", {}, x))))
      : el("tr", {}, el("td", { class: "txt muted", colspan: String(heads.length) }, "Nothing yet."))));
}
const td = (content, cls) => el("td", { class: cls }, content);

function equityChart(points, start) {
  // drawn at about the width it shows at (1536 wide minus the gutters), so the text keeps its shape
  const W = 1440, H = 200, padL = 56, padR = 16, padT = 14, padB = 22;
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: "xMidYMid meet", role: "img", "aria-label": "Balance over time" });
  const pts2 = (points || []).filter((p) => isNum(p.balance)).map((p) => ({ t: new Date(p.ts).getTime(), y: p.balance })).filter((p) => !Number.isNaN(p.t));
  if (pts2.length < 2) {
    svg.append(svgEl("text", { x: W / 2, y: H / 2, class: "axis", "text-anchor": "middle" }, "The line starts after the first settled bet."));
    return svg;
  }
  const t0 = pts2[0].t, t1 = pts2[pts2.length - 1].t || t0 + 1;
  let lo = Math.min(...pts2.map((p) => p.y), isNum(start) ? start : Infinity), hi = Math.max(...pts2.map((p) => p.y), isNum(start) ? start : -Infinity);
  // never zoom tighter than 5% of the start on each side: a $3 fee must not look like a cliff
  const minSpan = isNum(start) && start > 0 ? start * 0.05 : 25;
  if (hi - lo < minSpan) { const mid = (hi + lo) / 2; lo = mid - minSpan / 2; hi = mid + minSpan / 2; }
  const pad = (hi - lo) * 0.1; lo -= pad; hi += pad;
  const X = (t) => padL + ((t - t0) / Math.max(1, t1 - t0)) * (W - padL - padR);
  const Y = (y) => padT + (1 - (y - lo) / (hi - lo)) * (H - padT - padB);
  const d = pts2.map((p, i) => `${i ? "L" : "M"}${X(p.t).toFixed(1)},${Y(p.y).toFixed(1)}`).join(" ");
  svg.append(svgEl("path", { class: "area", d: `${d} L${X(t1).toFixed(1)},${(H - padB).toFixed(1)} L${X(t0).toFixed(1)},${(H - padB).toFixed(1)} Z` }));
  if (isNum(start)) svg.append(svgEl("line", { class: "start", x1: padL, x2: W - padR, y1: Y(start).toFixed(1), y2: Y(start).toFixed(1) }));
  svg.append(svgEl("path", { class: "line", d, "vector-effect": "non-scaling-stroke" }));
  const peak = pts2.reduce((m, p) => (p.y > m.y ? p : m), pts2[0]);
  svg.append(svgEl("circle", { class: "peak", cx: X(peak.t).toFixed(1), cy: Y(peak.y).toFixed(1), r: 4 }));
  const anchor = X(peak.t) > W - 140 ? "end" : "start";
  svg.append(svgEl("text", { class: "peak-lbl", x: (X(peak.t) + (anchor === "end" ? -8 : 8)).toFixed(1), y: Math.max(12, Y(peak.y) - 8).toFixed(1), "text-anchor": anchor }, `best ${usd(peak.y)}`));
  for (const [v, lab] of [[hi - pad, usdRound(hi - pad)], [lo + pad, usdRound(lo + pad)]]) {
    svg.append(svgEl("text", { class: "axis", x: padL - 8, y: (Y(v) + 4).toFixed(1), "text-anchor": "end" }, lab));
  }
  svg.append(svgEl("text", { class: "axis", x: padL, y: H - 6 }, fmtDay(pts2[0].t)));
  svg.append(svgEl("text", { class: "axis", x: W - padR, y: H - 6, "text-anchor": "end" }, fmtDay(pts2[pts2.length - 1].t)));
  return svg;
}

function renderRecord() {
  const main = $("#main");
  if (State.tab !== "record") return;
  const b = State.bundle || {};
  const rec = State.record || b.record || {};
  const g = b.gate || { lights: {} };
  const c = b.config || {};
  const view = el("div", { class: "view" });
  const page = el("div", { class: "record" });
  page.append(el("div", { class: "gate-row" }, gateReadings(g, rec, c).map((x) =>
    el("section", { class: "panel gate-card " + x.cls, dataset: { light: x.key } },
      el("div", { class: "lbl" }, x.label), el("div", { class: "val num" }, x.value), el("div", { class: "need" }, x.need), el("div", { class: "read" }, x.words)))));
  const bands = rec.bands || [];
  const ourRows = bands.map((x) => [bandWords(x.band), num(x.n), pctOf(x.model_mean, 1), pctOf(x.hit_rate, 1), `${pctOf(x.lo, 0)} to ${pctOf(x.hi, 0)}`,
    td(el("span", { class: "dot " + (x.light === "green" ? "up" : x.light === "red" ? "down" : "muted"), title: x.light }), "")]);
  const mkt = rec.market_bands || [];
  const mktRows = mkt.map((x) => [bandWords(x.band), num(x.n), pctOf(x.market_mean, 1), pctOf(x.hit_rate, 1)]);
  const loading = () => el("div", { class: "muted small" }, "Loading the full record.");
  page.append(el("div", { class: "two" },
    el("section", { class: "panel", id: "bands" }, el("h3", {}, "Do our guesses come true as often as we say?"),
      table(["We said (out of 100)", "Bets", "We said on average", "Came true", "Likely range", "Light"], ourRows, "bands-tbl"),
      el("div", { class: "help", style: "padding-top:6px" }, "A band is green when the share that came true sits close to what we said, with enough bets. Grey means too few bets to judge yet.")),
    el("section", { class: "panel" }, el("h3", {}, "Does Kalshi's price come true as often as it says?"),
      State.record ? table(["Kalshi said (out of 100)", "Bets", "Kalshi said on average", "Came true"], mktRows, "market-tbl") : loading())));
  const bank = rec.bankroll || {};
  page.append(el("section", { class: "panel equity" }, el("h3", {}, c.dry_run ? "Paper money over time" : "Money over time"),
    State.record ? equityChart(rec.equity, bank.start) : loading(),
    el("div", { class: "row small muted num" }, [`Start ${usd(bank.start)}`, `Now ${usd(bank.equity)}`, `Best ${usd(bank.peak)}`,
      `Drop from best ${isNum(bank.drawdown_pct) ? bank.drawdown_pct.toFixed(1) + "%" : "n/a"}`].flatMap((w, i) => [i ? el("span", {}, "·") : null, el("span", {}, w)]))));
  const clv = rec.clv || {};
  const by = clv.by_hours || [];
  const maxAbs = Math.max(0.1, ...by.map((x) => Math.abs(x.mean || 0)));
  const bars = el("div", { class: "bars" }, by.flatMap((x) => [
    el("span", {}, hoursWords(x.band)), el("span", { class: "muted" }, `${num(x.n)} bets`),
    el("span", { class: "bar" }, el("b", { class: (x.mean || 0) >= 0 ? "up" : "down", style: `width:${Math.max(2, (Math.abs(x.mean || 0) / maxAbs) * 100).toFixed(0)}%` })),
    el("span", { class: (x.mean || 0) >= 0 ? "up" : "down" }, pts(x.mean) + " pts")]));
  const ledger = rec.ledger || [];
  const ledgerRows = ledger.map((x) => [fmtStamp(x.ts), x.kind, x.card_id || "", td(usdSigned(x.amount_usd), isNum(x.amount_usd) ? (x.amount_usd > 0 ? "up" : x.amount_usd < 0 ? "down" : "") : ""), usd(x.balance_after), td(x.note || "", "txt")]);
  const sideName = (s) => (s === "yes" ? "Yes bets" : s === "no" ? "No bets" : String(s));
  const outName = (o) => (o === "draw" ? "Draw" : o === "home" ? "Home win" : o === "away" ? "Away win" : String(o));
  const pnlTd = (v) => td(usdSigned(v), v > 0 ? "up" : v < 0 ? "down" : "");
  page.append(el("div", { class: "two" },
    el("section", { class: "panel" }, el("h3", {}, "Did the price move our way by kickoff?"),
      by.length ? bars : el("div", { class: "muted small" }, "No data yet. The agent writes down the closing price at each kickoff."),
      el("div", { class: "help", style: "padding-top:8px" }, `On average ${isNum(clv.mean) ? pts(clv.mean) : "n/a"} points over ${num(clv.n || 0)} bets; ${isNum(clv.positive_share) ? pctOf(clv.positive_share) : "n/a"} moved our way. A plus means the price moved toward ours by kickoff, which is the sign we were right early.`)),
    el("section", { class: "panel" }, el("h3", {}, "Guess score (lower is better)"),
      el("div", { class: "brier" }, rec.brier && isNum(rec.brier.model)
        ? `Ours ${rec.brier.model.toFixed(4)}, Kalshi's ${isNum(rec.brier.market) ? rec.brier.market.toFixed(4) : "n/a"}, over ${num(rec.brier.n)} bets. Lower is better; we beat Kalshi when our number is smaller.`
        : "No settled bets yet. Lower is better."),
      el("div", { class: "two", style: "margin-top:10px" },
        el("div", {}, el("h3", {}, "By bet type"), table(["Bet", "Bets", "Made"], (rec.by_side || []).map((x) => [sideName(x.side), num(x.n), pnlTd(x.pnl_usd)]), "side-tbl")),
        el("div", {}, el("h3", {}, "By result bet on"), table(["On", "Bets", "Made"], (rec.by_outcome || []).map((x) => [outName(x.outcome), num(x.n), pnlTd(x.pnl_usd)]), "outcome-tbl"))),
      el("div", { style: "margin-top:10px" }, el("h3", {}, "By size of the gap"),
        el("div", { class: "muted small" }, "Points between what we think and Kalshi's price. Big gaps on a league this heavily bet usually mean the model missed something."),
        table(["Gap", "Bets", "Came true", "Made"], (rec.by_gap || []).map((x) => [x.gap + " points", num(x.n), isNum(x.hit_rate) ? x.hit_rate.toFixed(0) + "%" : "n/a", pnlTd(x.pnl_usd)]), "gap-tbl")))));
  page.append(el("section", { class: "panel" }, el("h3", {}, `Money log (latest ${num(ledger.length)})`),
    State.record ? table(["Time", "What", "Card", "Amount", "Balance after", "Note"], ledgerRows, "ledger-tbl") : loading()));
  view.append(page);
  clear(main).append(view);
}

// ---------------------------------------------------------------- Settings
// Every field: its key path in the config, how it is shown, and a plain line on what it does.
const GROUPS = [
  { title: "Mode", fields: [{ key: "mode", type: "mode", label: "Who places the bets",
    help: "Approve: every card waits for your click. Auto: the agent places green cards by itself. Auto unlocks when the four gate lights are green." }] },
  { title: "Exchange", fields: [
    { key: "env", type: "radio", options: [["demo", "Practice"], ["prod", "Live"]], label: "Account", help: "Practice is Kalshi's demo exchange with play money. Live is the real one." },
    { key: "dry_run", type: "bool", label: "Paper money", help: "Paper money: no real order leaves the machine. Turn it off only after the rehearsal." }] },
  { title: "Money", fields: [
    { key: "bankroll_usd", type: "number", step: 10, label: "Bankroll ($)", help: "Bankroll: the money the agent sizes bets from, in dollars." },
    { key: "gap_floor_points", type: "number", step: 0.5, label: "Gap floor (points)", help: "Gap floor: how many points better than the price our chance must be, after the fee, for a card to turn green." },
    { key: "stake.floor_pct", type: "number", step: 0.5, label: "Smallest bet (%)", help: "Smallest bet: percent of the match-day bankroll on a card that just clears the gap floor." },
    { key: "stake.cap_pct", type: "number", step: 0.5, label: "Biggest bet (%)", help: "Biggest bet: the most percent of the bankroll on one card." },
    { key: "stake.cap_from_points", type: "number", step: 0.5, label: "Biggest bet from (points)", help: "The gap at which the bet reaches its biggest size. Between the floor and here it rises on a straight line." },
    { key: "drawdown.on", type: "bool", label: "Losing-streak stop", help: "Stop placing bets when the money falls this far below its best." },
    { key: "drawdown.auto_only", type: "bool", label: "Stop auto mode only", help: "The stop only halts auto mode. Approve mode keeps asking you." },
    { key: "drawdown.pct", type: "number", step: 1, label: "Stop after a drop of (%)", help: "How far below the best, in percent, trips the stop." }] },
  { title: "Busy market", fields: [
    { key: "busy.min_volume_contracts", type: "number", step: 1000, label: "Min contracts traded", help: "A market needs this many contracts traded before we touch it." },
    { key: "busy.max_spread_cents", type: "number", step: 1, label: "Max spread (cents)", help: "The gap between the buy and sell price, in cents, can be at most this." },
    { key: "busy.min_depth_multiple", type: "number", step: 0.5, label: "Depth multiple", help: "The contracts waiting at the price must be at least this many times our count." }] },
  { title: "Window", fields: [
    { key: "window.snapshot_minutes", type: "number", step: 5, label: "Check the book every (min)", help: "How often the agent reads the prices for each card in its window, in minutes." },
    { key: "window.lineup_from_minutes", type: "number", step: 5, label: "Watch for lineups from (min)", help: "Minutes before kickoff when the agent starts asking for the lineups." },
    { key: "window.lineup_poll_minutes", type: "number", step: 1, label: "Lineup check every (min)", help: "Minutes between lineup checks once the watch starts." },
    { key: "window.decide_by_minutes", type: "number", step: 5, label: "Decide by (min)", help: "Minutes before kickoff when a card must be approved or it is missed." },
    { key: "window.decide_without_lineups", type: "bool", label: "Decide without lineups", help: "Let a card go green even when no lineup has posted." },
    { key: "window.cancel_before_kickoff_minutes", type: "number", step: 1, label: "Cancel before kickoff (min)", help: "Minutes before kickoff when waiting orders are pulled." },
    { key: "window.listing_lookahead_days", type: "number", step: 1, label: "Look ahead (days)", help: "How many days ahead the agent looks for matches and markets." }] },
  { title: "Auto windows", fields: [
    { key: "auto_windows.lineup_hour", type: "bool", label: "Lineup hour", help: "Auto mode may bet in the hour after the lineups post." },
    { key: "auto_windows.clv_proven_bands", type: "bool", label: "Proven time bands", help: "Auto mode may also bet in any hours-to-kickoff band where the price has moved our way on average." },
    { key: "auto_windows.min_band_cards", type: "number", step: 5, label: "Bets a band needs", help: "How many settled bets a time band needs before it counts as proven." }] },
  { title: "Gate", fields: [
    { key: "gate.min_settled", type: "number", step: 10, label: "Settled bets needed", help: "Settled bets needed before auto mode can turn on." },
    { key: "gate.band_width_points", type: "number", step: 5, label: "Band width (points)", help: "Our chances are grouped in bands this wide (10 means 30 to 40, 40 to 50)." },
    { key: "gate.band_tolerance_points", type: "number", step: 0.5, label: "Band tolerance (points)", help: "A band passes when the share that came true is within this many points of what we said." },
    { key: "gate.min_band_n", type: "number", step: 5, label: "Bets a band needs", help: "A band needs this many bets before it is judged." },
    { key: "gate.pooled_tolerance_points", type: "number", step: 0.5, label: "All-bets tolerance (points)", help: "All bets together must be within this many points." },
    { key: "gate.min_clv_points", type: "number", step: 0.5, label: "Closing price edge needed (points)", help: "How far, on average, the price must move our way by kickoff for auto mode to turn on." }] },
  { title: "Witness", fields: [
    { key: "polymarket.on", type: "bool", label: "Check Polymarket", help: "Read Polymarket's price for the same match as a second opinion." },
    { key: "polymarket.disagree_points", type: "number", step: 0.5, label: "Disagree at (points)", help: "Polymarket counts as disagreeing when it sits this far from our chance." },
    { key: "polymarket.block_when_disagree", type: "bool", label: "Block when it disagrees", help: "A disagreeing Polymarket keeps the card from turning green, not only a flag." }] },
  { title: "Claude", fields: [
    { key: "claude.on", type: "bool", label: "Claude writes the Why", help: "Claude writes the Why note on green cards. It never sets a number." },
    { key: "claude.max_usd_per_day", type: "number", step: 0.5, label: "Max $ a day", help: "The most dollars Claude may spend in one day." },
    { key: "claude.model", type: "text", label: "Model id", help: "Model id. Blank uses the server's default." }] },
  { title: "Legal watch", fields: [
    { key: "legal_watch.note", type: "textarea", label: "Note", wide: true, help: "Your note on the Maryland case. The agent shows it and never changes it." },
    { key: "legal_watch.checked", type: "date", label: "Checked on", help: "The date you last checked the case." }] },
];

function getPath(obj, key) { return key.split(".").reduce((o, k) => (o && typeof o === "object" ? o[k] : undefined), obj); }
function setPath(obj, key, v) {
  const ks = key.split("."); let o = obj;
  for (const k of ks.slice(0, -1)) { if (!o[k] || typeof o[k] !== "object") o[k] = {}; o = o[k]; }
  o[ks[ks.length - 1]] = v;
}
function diffConfig() {
  const out = {};
  for (const g of GROUPS) for (const f of g.fields) {
    const a = getPath(State.config, f.key), b = getPath(State.draft, f.key);
    if (JSON.stringify(a) !== JSON.stringify(b)) setPath(out, f.key, b);
  }
  return out;
}

async function openSettings() {
  const r = await api("GET", "/api/config");
  if (r.ok && r.data) { State.config = r.data; State.draft = clone(r.data); }
  else if (State.bundle && State.bundle.config) { State.config = clone(State.bundle.config); State.draft = clone(State.bundle.config); State.saveErrors = ["Could not read the settings from the server; showing the last bundle's copy."]; }
  renderSettings();
  loadHealth(); loadBacktest();
}
async function loadHealth() {
  try { const r = await api("GET", "/api/health"); if (r.ok) State.health = r.data; } catch (e) { State.health = null; }
  if (State.tab === "settings") renderHealthLine();
}
async function loadBacktest() {
  try { const r = await api("GET", "/api/backtest"); if (r.ok) State.backtest = r.data; } catch (e) { /* leave as is */ }
  if (State.tab === "settings") renderBacktestBox();
  clearTimeout(State.btTimer);
  if (State.backtest && State.backtest.status === "running" && State.tab === "settings" && !TEST) State.btTimer = setTimeout(loadBacktest, 3000);
}
async function runBacktest() {
  const field = $("#bt-seasons");
  const seasons = (field ? field.value : "").split(/[\s,]+/).map((s) => s.trim()).filter(Boolean);
  const r = await api("POST", "/api/backtest", { seasons });
  if (!r.ok) { State.backtest = { ...(State.backtest || {}), status: State.backtest && State.backtest.status, error: ((r.data && r.data.errors) || ["Could not start"]).join(" ") }; renderBacktestBox(); return; }
  State.backtest = { status: "running", started: new Date().toISOString() };
  renderBacktestBox();
  if (!TEST) State.btTimer = setTimeout(loadBacktest, 1500);
}

async function saveSettings() {
  const changes = diffConfig();
  if (!Object.keys(changes).length) { State.saveMsg = "Nothing changed."; State.saveErrors = []; renderSettings(); return; }
  State.saving = true; State.saveMsg = "Saving"; renderSettings();
  let r;
  try { r = await api("PUT", "/api/config", changes); }
  catch (e) { r = { ok: false, status: 0, data: { errors: ["The agent did not answer. Is the server running?"] } }; }
  State.saving = false;
  if (r.ok && r.data) { State.config = r.data; State.draft = clone(r.data); State.saveErrors = []; State.saveMsg = `Saved at ${fmtTime(new Date())}.`; }
  else {
    State.saveMsg = "";
    State.saveErrors = (r.data && r.data.errors) || [`Save failed (${r.status || "no answer"}).`];
    if (r.data && r.data.gate && Array.isArray(r.data.gate.reasons) && r.data.gate.reasons.length) State.saveErrors = State.saveErrors.concat(r.data.gate.reasons.map((x) => "Gate: " + x));
  }
  renderSettings();
}

function fieldNode(f) {
  const v = getPath(State.draft, f.key);
  const id = "f-" + f.key.replace(/\./g, "-");
  const set = (val) => { setPath(State.draft, f.key, val); State.saveMsg = ""; };
  let control;
  if (f.type === "mode") {
    const g = (State.bundle && State.bundle.gate) || { passed: false, reasons: [] };
    const reasons = (g.reasons || []).length ? g.reasons : failingLights(g);
    const locked = !g.passed && v !== "auto";
    control = el("div", { class: "mode-switch" },
      el("label", { class: "switch", title: locked ? "Auto mode is locked: " + reasons.join("; ") : "Auto mode is allowed" },
        el("input", { type: "checkbox", role: "switch", id: "f-mode", dataset: { key: "mode" }, checked: v === "auto", disabled: locked,
          title: locked ? "Auto mode is locked: " + reasons.join("; ") : "Auto mode is allowed",
          onchange: (e) => { set(e.target.checked ? "auto" : "approve"); renderSettingsBar(); } }),
        el("span", {}, "Auto mode")),
      el("span", { class: "now" }, v === "auto" ? "Now: Auto" : "Now: You approve each bet"),
      locked ? el("span", { class: "help" }, "Locked: " + reasons.join("; ")) : null);
  } else if (f.type === "radio") {
    control = el("div", { class: "radios", role: "radiogroup" }, f.options.map(([val, lab]) =>
      el("label", {}, el("input", { type: "radio", name: id, id: id + "-" + val, dataset: { key: f.key }, value: val, checked: v === val,
        onchange: () => { set(val); renderSettingsBar(); } }), lab)));
  } else if (f.type === "bool") {
    control = el("label", { class: "switch" }, el("input", { type: "checkbox", id, dataset: { key: f.key }, checked: !!v,
      onchange: (e) => { set(e.target.checked); renderSettingsBar(); } }), el("span", {}, v ? "On" : "Off"));
    control.querySelector("input").addEventListener("change", (e) => { control.querySelector("span").textContent = e.target.checked ? "On" : "Off"; });
  } else if (f.type === "number") {
    control = el("input", { type: "number", id, dataset: { key: f.key }, step: String(f.step || 1), value: v == null ? "" : String(v),
      oninput: (e) => { const n = e.target.value === "" ? null : Number(e.target.value); set(Number.isNaN(n) ? v : n); renderSettingsBar(); } });
  } else if (f.type === "textarea") {
    control = el("textarea", { id, dataset: { key: f.key }, oninput: (e) => { set(e.target.value); renderSettingsBar(); } }, v == null ? "" : String(v));
  } else {
    control = el("input", { type: f.type === "date" ? "date" : "text", id, dataset: { key: f.key }, value: v == null ? "" : String(v),
      oninput: (e) => { set(e.target.value); renderSettingsBar(); } });
  }
  return el("div", { class: "field" + (f.wide ? " wide" : "") }, el("label", { for: f.type === "radio" || f.type === "mode" ? null : id }, f.label), control, el("div", { class: "help" }, f.help));
}
function failingLights(g) {
  const L = (g && g.lights) || {};
  const names = { count: "Bets settled", calibration: "Our guesses match results", profit: "Money made after fees", clv: "Beat the closing price" };
  return Object.keys(names).filter((k) => !(L[k] && L[k].ok)).map((k) => names[k]);
}

function renderSettingsBar() {
  const bar = $("#sbar"); if (!bar) return;
  const dirty = Object.keys(diffConfig()).length > 0;
  clear(bar).append(
    el("h2", {}, "Settings"),
    el("span", { class: "smsg" }, State.saving ? "Saving" : State.saveMsg || (dirty ? "Unsaved changes" : "")),
    el("span", { class: "grow" }),
    el("button", { class: "btn quiet small", type: "button", disabled: !dirty || State.saving, onclick: () => { State.draft = clone(State.config); State.saveMsg = ""; State.saveErrors = []; renderSettings(); } }, "Undo changes"),
    el("button", { class: "btn small", type: "button", id: "save", disabled: State.saving, onclick: saveSettings }, icon("done_all"), "Save"));
}
function renderHealthLine() {
  const box = $("#keys-line"); if (!box) return;
  const h = State.health;
  const labels = { kalshi_demo: "Kalshi practice", kalshi: "Kalshi live", football: "API-Football", anthropic: "Anthropic" };
  clear(box);
  if (!h) { box.append(el("span", { class: "muted" }, "Health not read yet. ")); }
  else {
    const keys = h.keys || {};
    box.append(el("span", {}, `${h.app || "Monarc Edge"} ${h.version || ""}, ${h.env === "prod" ? "live" : "practice"} account, ${h.mode === "auto" ? "auto" : "you approve each bet"}${h.dry_run ? ", paper money" : ""}. Keys: `),
      ...Object.keys(labels).flatMap((k, i) => [i ? ", " : "", el("span", { class: keys[k] ? "" : "missing" }, `${labels[k]} ${keys[k] ? "from " + keys[k] : "missing"}`)]), ". ");
  }
  box.append(el("button", { class: "link", type: "button", onclick: loadHealth }, "Check"));
}
function renderBacktestBox() {
  const box = $("#bt-box"); if (!box) return;
  const bt = State.backtest || { status: "idle" };
  let words = "No backtest run yet.";
  if (bt.status === "running") words = `Running since ${fmtTime(bt.started)}.`;
  else if (bt.status === "done") words = `Done at ${fmtTime(bt.finished)}.` + (bt.report_path ? ` Report: ${bt.report_path}` : "");
  else if (bt.status === "error") words = `Failed: ${bt.error || "no detail"}`;
  if (bt.error && bt.status !== "error") words += ` ${bt.error}`;
  clear(box).append(
    el("div", { class: "bt-status" + (bt.status === "error" ? " warn" : "") }, words),
    bt.metrics && typeof bt.metrics === "object" ? el("div", { class: "help" }, Object.entries(bt.metrics).map(([k, v]) => `${k}: ${typeof v === "number" ? +v.toFixed(4) : v}`).join("; ")) : null,
    bt.report_md ? el("details", { class: "fold" }, el("summary", {}, icon("expand_more"), "Report"), el("pre", {}, bt.report_md)) : null);
}

function renderSettings() {
  const main = $("#main");
  if (State.tab !== "settings") return;
  if (!State.draft) { clear(main).append(el("div", { class: "view" }, el("div", { class: "muted" }, "Reading the settings."))); return; }
  const view = el("div", { class: "view settings" });
  view.append(el("div", { class: "sbar", id: "sbar" }));
  if (State.saveErrors.length) view.append(el("div", { class: "save-errors", role: "alert" }, State.saveErrors.map((x) => el("div", {}, x))));
  const groups = el("div", { class: "sgroups" });
  for (const g of GROUPS) {
    groups.append(el("section", { class: "panel sgroup" + (g.fields.some((f) => f.wide) ? " wide" : "") }, el("h3", {}, g.title),
      el("div", { class: "fields" }, g.fields.map(fieldNode))));
  }
  groups.append(el("section", { class: "panel sgroup wide" }, el("h3", {}, "Backtest"),
    el("div", { class: "fields" },
      el("div", { class: "field" }, el("label", { for: "bt-seasons" }, "Seasons"),
        el("input", { type: "text", id: "bt-seasons", value: "1920,2021,2122,2223,2324,2425,2526" }),
        el("div", { class: "help" }, "football-data.co.uk season codes, comma separated. 2526 is 2025/26.")),
      el("div", { class: "field" }, el("label", {}, "Run"),
        el("div", {}, el("button", { class: "btn quiet small", type: "button", id: "bt-run", onclick: runBacktest }, icon("play_arrow"), "Run backtest")),
        el("div", { class: "help" }, "Replays the model over those seasons against the closing odds and writes a report. Nothing is placed."))),
    el("div", { id: "bt-box" })));
  groups.append(el("section", { class: "panel sgroup wide" }, el("h3", {}, "Keys and health"),
    el("div", { class: "keys-line", id: "keys-line" }),
    el("div", { class: "help" }, "Labels only: where each key comes from, never the key itself.")));
  view.append(groups);
  clear(main).append(view);
  renderSettingsBar(); renderHealthLine(); renderBacktestBox();
}

// ---------------------------------------------------------------- render, boot, long poll
function render() {
  renderTopbar();
  renderBanner();
  if (State.tab === "today") renderToday();
  else if (State.tab === "record") { renderRecord(); loadRecord(); }
  else if (State.tab === "settings") { if (State.draft) renderSettings(); else { renderSettings(); openSettings(); } }
  if (State.tab !== "settings") { clearTimeout(State.btTimer); State.btTimer = null; }
}

let polling = false;
async function poll() {
  if (polling) return;
  polling = true;
  let backoff = 1000;
  for (;;) {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), 40000);
    try {
      const r = await fetch(`/api/state?since=${State.rev}`, { signal: ctl.signal });
      clearTimeout(timer);
      if (!r.ok) throw new Error("status " + r.status);
      const b = await r.json();
      if (!State.connected) { State.connected = true; $("#reconnect").hidden = true; }
      backoff = 1000;
      if (b && isNum(b.rev) && b.rev > State.rev) applyBundle(b);
      else if (b && isNum(b.rev) && b.rev === State.rev) await new Promise((res) => setTimeout(res, 500));
    } catch (e) {
      clearTimeout(timer);
      State.connected = false; $("#reconnect").hidden = false;
      await new Promise((res) => setTimeout(res, backoff));
      backoff = Math.min(backoff * 2, 15000);
    }
  }
}

async function iconsReady() {
  try {
    await document.fonts.ready;
    const faces = []; document.fonts.forEach((f) => faces.push(f));
    if (!faces.some((f) => /Material Symbols/i.test(f.family))) return;
    await document.fonts.load('20px "Material Symbols Outlined"');
    if (document.fonts.check('20px "Material Symbols Outlined"')) document.documentElement.classList.add("icons-ready");
  } catch (e) { /* no icons, the layout keeps their 1em boxes */ }
}

async function boot() {
  State.tab = tabFromHash();
  if (location.hash !== "#/" + State.tab) history.replaceState(null, "", "#/" + State.tab);
  let r;
  try { r = await api("GET", "/api/state?since=0"); }
  catch (e) { r = { ok: false }; }
  if (r.ok && r.data) { State.connected = true; $("#reconnect").hidden = true; applyBundle(r.data); }
  else { State.connected = false; $("#reconnect").hidden = false; }
  render();
  if (!TEST) {
    poll();
    setInterval(() => { const c = $("#clock"); if (c) c.textContent = fmtClock(new Date()); }, 15000);
  }
  return State;
}

window.__edge = { boot, render, state: State, go, fmt: { usd, usdSigned, cents, pts, pctOf, fmtKick, fmtUntil, fmtClock, betWords, gapWords, moneyWords, flagWords } };
iconsReady();
if (TEST) {
  const out = document.getElementById("__out");
  out.hidden = false;
  const s = document.createElement("script");
  s.type = "module";
  s.src = `tests/t-${encodeURIComponent(TEST)}.js`;
  s.onerror = () => { out.textContent += `FAIL load ${TEST}: the test script did not load\nDONE\n`; };
  document.body.append(s);
} else {
  boot();
}
