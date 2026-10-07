// One dial, one screen. Outcome, the line it died on, the person, the next action. Enter logs it.
import { el, telHref, copyText, nextWeekday } from "../util.js";
import { api } from "../api.js";
import { openModal, toast } from "./modal.js";
import { cfg, outcomes, outcome, stage, todayISO, sources, vertical } from "../state.js";

const DEFAULT_NEXT = {
  "Booked": (t) => ({ action: "Send the LOCK email: time restated, offer page attached", date: t }),
  "Callback": (t) => ({ action: "Call back", date: nextWeekday(t, 1) }),
  "Connect": (t) => ({ action: "Call back with one fresh time", date: nextWeekday(t, 2) }),
  "Gatekeeper": (t) => ({ action: "Call back and ask for the owner by name", date: nextWeekday(t, 1) }),
};

function field(label, input, required) {
  return el("div", { class: "field" }, el("label", {}, label, required ? el("span", { class: "req" }, " *") : null), input);
}

export function openDialModal(row, { onLogged, preset } = {}) {
  // row: a queue row ({key, name, phone, city, state, local_time, ...}) or a company bundle's company.
  // preset: an outcome name already picked (the inline dropdown on Today, 2026-09-24), so the caller lands on the details.
  const key = row.key || row.Key;
  const name = row.name || row.Name;
  const phone = row.phone || row.Phone || "";
  const place = [row.city || row.City, row.state || row.State].filter(Boolean).join(", ");
  const local = row.local_time || row["Local time at noon ET"];
  const t = todayISO();
  const st = { outcome: "", died: "", recognized: false };

  const outcomeChips = el("div", { class: "chips" });
  const diedChips = el("div", { class: "chips" });
  const recog = el("button", { class: "chip quiet", type: "button" }, "Recognized the name");
  const errors = el("div", { class: "errors" });
  const logBtn = el("button", { class: "btn", type: "submit" }, "Log dial");

  const person = {
    name: el("input", { type: "text", placeholder: "Who you spoke to" }),
    role: el("input", { type: "text", placeholder: "Owner, ops, office" }),
    email: el("input", { type: "email", placeholder: "For the LOCK email" }),
  };
  const next = {
    action: el("input", { type: "text" }),
    date: el("input", { type: "date", value: t }),
  };
  const closeReason = el("select", {}, el("option", { value: "" }, ""), ...(cfg().close_reasons || []).map((r) => el("option", { value: r }, r)));
  const notes = el("textarea", { placeholder: "What they said. Objection, brand, timing." });
  const srcSel = el("select", {}, ...sources().map((s) => el("option", { value: s.name, selected: s.name === (row.source || "cold") }, s.name)));

  const contactBlock = el("div", { class: "stack" },
    el("div", {}, el("div", { class: "label" }, "Where did it die?"), diedChips),
    el("div", { class: "fields" }, field("Person", person.name), field("Role", person.role), field("Email", person.email)),
  );
  const nextBlock = el("div", { class: "fields" }, field("Next action", next.action, true), field("Date", next.date, true));
  const closeBlock = el("div", { class: "fields" }, field("Reason", closeReason, true));

  function refresh() {
    const o = outcome(st.outcome);
    const contact = !!(o && o.class === "contact");
    const closes = !!(o && o.closes);
    const target = o && o.to_stage ? stage(o.to_stage) : null;
    const needsDied = contact && o.name !== "Booked" && !closes;
    contactBlock.hidden = !contact;
    diedChips.parentElement.hidden = !needsDied;
    nextBlock.hidden = !(contact && target && !target.closed);
    closeBlock.hidden = !(contact && target && target.closed);
    recog.hidden = !contact;
    outcomeChips.querySelectorAll(".chip").forEach((c) => c.classList.toggle("is-on", c.dataset.v === st.outcome));
    diedChips.querySelectorAll(".chip").forEach((c) => c.classList.toggle("is-on", c.dataset.v === st.died));
    recog.classList.toggle("is-on", st.recognized);
    const msgs = [];
    if (!st.outcome) msgs.push("Pick an outcome.");
    if (needsDied && !st.died) msgs.push("Which line did it die on?");
    if (!nextBlock.hidden && !next.action.value.trim()) msgs.push("A live conversation needs a next action.");
    if (!nextBlock.hidden && !next.date.value) msgs.push("The next action needs a date.");
    if (!closeBlock.hidden && !closeReason.value) msgs.push("Closing needs a reason.");
    errors.replaceChildren(...msgs.map((m) => el("div", {}, m)));
    logBtn.disabled = msgs.length > 0;
  }

  outcomes().forEach((o, i) => {
    const c = el("button", { class: "chip", type: "button", dataset: { v: o.name } }, el("span", { class: "key" }, String(i + 1)), " ", o.name);
    c.addEventListener("click", () => {
      st.outcome = o.name;
      const def = DEFAULT_NEXT[o.name];
      if (def && !next.action.dataset.touched) { const v = def(t); next.action.value = v.action; next.date.value = v.date; }
      refresh();
    });
    outcomeChips.append(c);
  });
  (cfg().died_on_lines || []).forEach((ln) => {
    const c = el("button", { class: "chip", type: "button", dataset: { v: ln } }, ln);
    c.addEventListener("click", () => { st.died = ln; refresh(); });
    diedChips.append(c);
  });
  recog.addEventListener("click", () => { st.recognized = !st.recognized; refresh(); });
  next.action.addEventListener("input", () => { next.action.dataset.touched = "1"; refresh(); });
  next.date.addEventListener("input", refresh);
  closeReason.addEventListener("change", refresh);

  const copyBtn = el("button", { class: "copy", type: "button" }, "COPY");
  copyBtn.addEventListener("click", () => copyText(phone).then(() => toast("Number copied.")));

  const form = el("form", { class: "stack" },
    el("div", { class: "row" },
      el("div", { class: "grow" },
        el("div", { class: "label" }, place || "Company", local ? ` · ${local} local at noon ET` : ""),
        el("h2", {}, name)),
      el("div", {},
        el("a", { class: "phone", href: telHref(phone) }, phone || "no phone"), copyBtn)),
    el("div", {}, el("div", { class: "label" }, "Outcome"), outcomeChips),
    contactBlock,
    nextBlock,
    closeBlock,
    el("div", { class: "fields" }, field("Notes", notes), field("Source", srcSel)),
    el("div", { class: "actions" }, errors, recog, logBtn));

  form.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && e.target.tagName !== "TEXTAREA" && !logBtn.disabled) { e.preventDefault(); form.requestSubmit(); }
    if (/^[1-8]$/.test(e.key) && e.target.tagName !== "INPUT" && e.target.tagName !== "TEXTAREA" && e.target.tagName !== "SELECT") {
      const chip = outcomeChips.querySelectorAll(".chip")[Number(e.key) - 1];
      if (chip) chip.click();
    }
  });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    logBtn.disabled = true;
    const body = {
      key, name, phone, website: row.website || row.Website,
      outcome: st.outcome, died_on: st.died || null, recognized: st.recognized, notes: notes.value,
      source: srcSel.value, vertical: row.vertical || vertical(),
      person_name: person.name.value.trim(), person_role: person.role.value.trim(), person_email: person.email.value.trim(),
      next_action: nextBlock.hidden ? "" : next.action.value.trim(),
      next_action_date: nextBlock.hidden ? null : next.date.value,
      close_reason: closeBlock.hidden ? null : closeReason.value,
    };
    try {
      const res = await api.dial(body);
      toast(res.note || `Logged: ${st.outcome}.`);
      modal.close();
      if (onLogged) onLogged(res);
    } catch (err) {
      errors.replaceChildren(...err.errors.map((m) => el("div", {}, m)));
      logBtn.disabled = false;
    }
  });
  const modal = openModal(form, { wide: true });
  if (preset && outcome(preset)) {
    const chip = outcomeChips.querySelector(`.chip[data-v="${preset}"]`);
    if (chip) chip.click();
  }
  refresh();
  return modal;
}

// Log a no-contact outcome straight from a row, no screen in between (the cold caller's dropdown, 2026-09-24).
export async function quickDial(row, outcomeName) {
  return api.dial({
    key: row.key || row.Key, name: row.name || row.Name, phone: row.phone || row.Phone || "", website: row.website || row.Website,
    outcome: outcomeName, source: row.source || "cold", vertical: row.vertical || vertical(),
  });
}
