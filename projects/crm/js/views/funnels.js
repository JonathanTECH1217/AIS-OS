// Funnels, the second tab on Pipeline (Jonathan, 2026-10-03: "under pipeline ... a funnels view"). First the whole
// funnel: every step from the first dial to signed, the counts in a strip, then one bar per step for the rate from that
// step to the next (0 to 100, so the narrow end of the funnel still shows) with a tick at the rate the plan assumes,
// and under each count what the goal (5 signed by December 1) needs there at the plan's rates. Then one funnel per
// channel in its own steps: ads run impressions, clicks, leads, booked, held, won; cold calling runs dials, connects,
// booked, held, won; LinkedIn runs requests, accepted, messaged, replied, booked, held, won; every other source runs
// companies, contacted, booked, held, won. Counts are what the Channels page shows (the base plus the call sheets);
// the plan's rates are goal.assumed_rates in Config. Every value is written out, so the bars add a picture, not a gate.
import { el, fmtDate } from "../util.js";
import { api } from "../api.js";
import { cfg, state } from "../state.js";
import { brandOf, logo } from "./channels.js";
import { tabs, PIPELINE_TABS } from "../components/tabs.js";

const MAIN = ["google-ads", "google-organic", "cold", "linkedin"];
const n = (v) => (v === null || v === undefined ? "–" : Number(v).toLocaleString("en-US"));
const rate = (a, b) => (b > 0 ? Math.round((a / b) * 1000) / 10 : null);

function count(label, value, sub) { return { label, value: Number(value) || 0, sub: sub || "" }; }
// One step between two counts: a of b, the rate, and the plan's rate when the plan has one. words: [a's name, b's name].
function step(label, a, b, words, plan) { return { label, a: Number(a) || 0, b: Number(b) || 0, words, plan: plan === undefined ? null : plan, rate: rate(a, b) }; }

// The counts in a strip, an arrow between each pair.
function strip(counts) {
  const kids = [];
  counts.forEach((c, i) => {
    if (i) kids.push(el("span", { class: "fn-arrow", "aria-hidden": "true" }, "→"));
    kids.push(el("div", { class: "fn-count" }, el("div", { class: "label" }, c.label), el("div", { class: "v" }, n(c.value)),
      el("div", { class: "fn-sub muted" }, c.sub)));
  });
  return el("div", { class: "fn-strip" }, ...kids);
}

// One step as a row: its name and "a of b" on the left, the bar (the rate, 0 to 100) with the plan's tick, the rate
// and the plan's rate on the right with a word on where it stands. The fill takes the card's accent (CSS).
function row(s) {
  const have = s.b > 0;
  const plan = s.plan === null ? null : Math.round(s.plan * 100);
  let word;
  if (!have) word = el("span", { class: "muted" }, `nothing at ${s.words[1]} yet`);
  else if (plan === null) word = el("span", { class: "muted" }, "no plan rate for this step");
  else {
    const diff = Math.round(s.rate - plan);
    word = diff >= 0 ? el("span", { class: "up" }, diff ? `${diff} points over plan` : "on plan") : el("span", { class: "down" }, `${-diff} points under plan`);
  }
  const title = `${s.label}: ${n(s.a)} ${s.words[0]} of ${n(s.b)} ${s.words[1]}` + (have ? ` = ${s.rate}%` : "") + (plan !== null ? `. The plan assumes ${plan}%.` : ".");
  return el("div", { class: "fn-row", title, tabindex: "0" },
    el("div", { class: "fn-k" }, el("div", { class: "strong" }, s.label), el("div", { class: "muted", style: "font-size:12px" }, `${n(s.a)} of ${n(s.b)} ${s.words[1]}`)),
    el("div", { class: "fn-track" },
      have ? el("b", { class: "fn-fill", style: `width:${Math.max(0, Math.min(100, s.rate))}%` }) : null,
      plan !== null ? el("i", { class: "fn-plan", style: `left:${plan}%` }) : null),
    el("div", { class: "fn-v" }, el("span", { class: "strong num" }, have ? `${s.rate}%` : "–"), plan !== null ? el("span", { class: "muted" }, ` · plan ${plan}%`) : null,
      el("div", { style: "font-size:12px" }, word)));
}

// ---- the whole funnel, every channel together

function wholeFunnel(data) {
  const t = data.total || {};
  const chans = data.channels || [];
  const sum = (k) => chans.reduce((a, c) => a + (Number(c[k]) || 0), 0);
  // the base's total plus the calls typed in the call sheets that the base does not hold (the Cold call card adds the
  // same; the total from the base alone showed 7 dials against 109 in the sheet, 2026-09-29)
  const dials = (t.dials || 0) + sum("sheet_dials");
  const connects = (t.connects || 0) + sum("sheet_connects");
  const booked = (t.booked || 0) + sum("sheet_booked");
  const conversations = Math.max(connects, t.contacted || 0);
  const held = t.held || 0, proposed = t.proposed || 0, won = t.won || 0;
  const ar = t.assumed_rates || {};
  const goal = cfg().goal || {};
  const want = Number(goal.won || 5);
  // what the goal takes at the plan's rates, from the end back to the first dial
  const need = { won: want };
  need.held = ar.close ? Math.ceil(want / ar.close) : null;
  need.booked = ar.show && need.held ? Math.ceil(need.held / ar.show) : null;
  need.conv = ar.book && need.booked ? Math.ceil(need.booked / ar.book) : null;
  need.dials = ar.connect && need.conv ? Math.ceil(need.conv / ar.connect) : null;
  const of = (v) => (v === null ? "" : `of ${n(v)} needed`);
  const counts = [
    count("Dials", dials, of(need.dials)), count("Connects", connects, of(need.conv)), count("Booked", booked, of(need.booked)),
    count("Held", held, of(need.held)), count("Proposed", proposed, ""), count("Won", won, `of ${want} by ${fmtDate(goal.by || "2026-12-01")}`),
  ];
  const steps = [
    step("Connect rate", connects, dials, ["connects", "dials"], ar.connect),
    step("Booking rate", booked, conversations, ["booked", "conversations"], ar.book),
    step("Show rate", held, booked, ["held", "booked"], ar.show),
    step("Close rate", won, held, ["won", "held"], ar.close),
  ];
  return el("section", { class: "panel fn-whole", "aria-label": "The whole funnel" },
    el("div", { class: "row" },
      el("div", { class: "grow" }, el("div", { class: "label" }, "Every channel together"), el("h2", {}, "From the first dial to signed")),
      el("span", { class: "tag " + (won >= want ? "won" : "faint") }, `${won} of ${want} signed`)),
    strip(counts),
    el("div", { class: "fn-rows" }, ...steps.map(row)),
    el("div", { class: "muted", style: "font-size:12px" },
      `Each bar is the rate from one step to the next, 0 to 100. The tick is the rate the plan assumes; "needed" is what ${want} signed takes at those rates, counted from zero. ` +
      `Counts are all time, from the base and the call sheets. A conversation is a connect or a deal that reached Contacted. ${n(t.lost || 0)} lost along the way.`));
}

// ---- one funnel per channel, in the channel's own steps

function channelSteps(ch, ar) {
  const held = ch.held || 0, won = ch.won || 0;
  const tail = (booked) => [step("Show rate", held, booked, ["held", "booked"], ar.show), step("Close rate", won, held, ["won", "held"], ar.close)];
  if (ch.type === "Cold call") {
    const conv = Math.max(ch.connects || 0, ch.contacted || 0);
    return {
      counts: [count("Dials", ch.dials), count("Connects", ch.connects), count("Booked", ch.booked), count("Held", held), count("Won", won)],
      steps: [step("Connect rate", ch.connects, ch.dials, ["connects", "dials"], ar.connect),
        step("Booking rate", ch.booked, conv, ["booked", "conversations"], ar.book), ...tail(ch.booked || 0)],
    };
  }
  if (ch.messaging) {
    const m = ch.messaging;
    const booked = Math.max(ch.booked || 0, m.booked || 0);
    return {
      counts: [count("Requests", m.requests), count("Accepted", m.accepted), count("Messaged", m.messaged), count("Replied", m.replied),
        count("Booked", booked), count("Held", held), count("Won", won)],
      steps: [step("Accept rate", m.accepted, m.requests, ["accepted", "requests"]), step("Reply rate", m.replied, m.messaged, ["replied", "messaged"]),
        step("Booking rate", booked, m.replied, ["booked", "replies"]), ...tail(booked)],
    };
  }
  const ads = ["Google Ads", "Google Organic", "Meta Ads", "Campaign"].includes(ch.type) || ch.impressions || ch.clicks;
  if (ads) {
    const booked = Math.max(ch.booked || 0, ch.leads_booked || 0);
    return {
      counts: [count("Impressions", ch.impressions), count("Clicks", ch.clicks), count("Leads", ch.leads), count("Booked", booked), count("Held", held), count("Won", won)],
      steps: [step("Click rate", ch.clicks, ch.impressions, ["clicks", "impressions"]), step("Lead rate", ch.leads, ch.clicks, ["leads", "clicks"]),
        step("Booking rate", booked, ch.leads, ["booked", "leads"]), ...tail(booked)],
    };
  }
  const booked = Math.max(ch.booked || 0, ch.leads_booked || 0);
  return {
    counts: [count("Companies", ch.companies), count("Contacted", ch.contacted), count("Booked", booked), count("Held", held), count("Won", won)],
    steps: [step("Contact rate", ch.contacted, ch.companies, ["contacted", "companies"]),
      step("Booking rate", booked, ch.contacted, ["booked", "contacted"], ar.book), ...tail(booked)],
  };
}

function card(ch, ar) {
  const b = brandOf(ch.name);
  const live = ch.type === "Cold call" || ch.type === "Google Organic" ? !!ch.active : (ch.campaigns_live || 0) > 0;
  const { counts, steps } = channelSteps(ch, ar);
  const empty = !counts.some((c) => c.value > 0);
  const path = `${counts[0].label} to ${counts[counts.length - 1].label.toLowerCase()}`;
  return el("section", { class: "fn-card" + (live ? "" : " paused"), style: `--accent:${b.color};--accent-tint:${b.tint}`, "aria-label": `${b.label || ch.label || ch.name}: ${path}` },
    el("div", { class: "ch-head" }, logo(ch.name, 36),
      el("div", { class: "grow" }, el("h3", {}, b.label || ch.label || ch.name), el("div", { class: "muted", style: "font-size:12px" }, path)),
      el("span", { class: "tag " + (live ? "won" : "faint") }, live ? "Live" : "Not live"),
      el("a", { class: "link", href: `#/channel/${encodeURIComponent(ch.name)}`, style: "font-size:13px" }, "Open")),
    strip(counts),
    empty ? el("div", { class: "muted", style: "font-size:13px" }, "No numbers yet. The funnel fills in as the channel runs.")
      : el("div", { class: "fn-rows" }, ...steps.map(row)));
}

export async function renderFunnels(root) {
  const data = await api.channels();
  const chans = data.channels || [];
  const ar = (data.total && data.total.assumed_rates) || {};
  const byName = new Map(chans.map((c) => [c.name, c]));
  const main = MAIN.map((nm) => byName.get(nm)).filter(Boolean);
  // the four acquisition channels always; any other source once it has a number
  const hasNumbers = (c) => ["companies", "leads", "deals", "dials", "impressions"].some((k) => Number(c[k]) > 0);
  const rest = chans.filter((c) => !MAIN.includes(c.name) && hasNumbers(c)).sort((a, b) => (a.sort || 99) - (b.sort || 99));
  root.append(
    el("div", { class: "head" },
      el("div", {}, el("div", { class: "label" }, "Pipeline"), el("h1", {}, "Where they fall out"),
        el("div", { class: "sub" }, "Every step from the first touch to signed, the rate at each step against what the plan assumes, and what the goal needs at each step."))),
    tabs(PIPELINE_TABS, "funnels", "Pipeline views"),
    wholeFunnel(data),
    el("div", {}, el("div", { class: "label" }, "By channel"), el("h2", {}, "Each channel in its own steps"),
      el("div", { class: "muted", style: "font-size:13px" }, "The numbers the Channels page shows, laid out as a funnel. Show and close rates carry the plan's tick on every channel.")),
    chans.length
      ? el("div", { class: "fn-grid" }, ...main.map((c) => card(c, ar)), ...rest.map((c) => card(c, ar)))
      : el("div", { class: "empty" }, state.health && !state.health.airtable_ready
        ? "Airtable is not connected yet. Add AIRTABLE_PAT and restart the server." : "No sources in the base yet."));
}
