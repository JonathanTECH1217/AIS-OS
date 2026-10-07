// The deal form enforces the rules the server also enforces:
// stage, value, close date, source on every deal; next action with owner and date while open; reason when closed.
import { el, addDays } from "../util.js";
import { api } from "../api.js";
import { openModal, toast } from "./modal.js";
import { cfg, stages, isClosedStage, sources, offers, todayISO, numbers } from "../state.js";

export function validateDeal(f) {
  const msgs = [];
  if (!f["Stage"]) msgs.push("Pick a stage.");
  if (f["Value"] === "" || f["Value"] === null || f["Value"] === undefined) msgs.push("Every deal has a dollar value.");
  if (!f["Close date"]) msgs.push("Every deal has a close date.");
  if (!f["Source"]) msgs.push("Every deal has a source.");
  if (f["Stage"] && isClosedStage(f["Stage"])) {
    if (!f["Close reason"]) msgs.push("A closed deal needs a reason.");
  } else if (f["Stage"]) {
    if (!(f["Next action"] || "").trim()) msgs.push("An open deal needs a next action.");
    if (!f["Next action date"]) msgs.push("The next action needs a date.");
    if (!(f["Owner"] || "").trim()) msgs.push("The next action needs an owner.");
  }
  return msgs;
}

function field(label, input, required) {
  return el("div", { class: "field" }, el("label", {}, label, required ? el("span", { class: "req" }, " *") : null), input);
}

function select(name, options, value, { blank = "" } = {}) {
  const s = el("select", { name });
  if (blank !== null) s.append(el("option", { value: "" }, blank));
  for (const o of options) {
    const opt = typeof o === "string" ? { value: o, label: o } : o;
    s.append(el("option", { value: opt.value, selected: opt.value === value }, opt.label));
  }
  return s;
}

export function openDealForm(deal, { company, onSaved } = {}) {
  const d = deal || {};
  const isNew = !d.id;
  const src = (d.Source && d.Source[0]) || (company && company.Source && company.Source[0]) || "";
  const defaultOffer = offers()[0] || {};
  const init = {
    "Stage": d.Stage || (stages()[0] || {}).name || "",
    "Offer": d.Offer || defaultOffer.name || "",
    "Value": d.Value !== undefined ? d.Value : (defaultOffer.value || 0),
    "Close date": d["Close date"] || addDays(todayISO(), Number(numbers().default_close_days || 30)),
    "Source": src,
    "Owner": d.Owner || cfg().owner_default || "",
    "Next action": d["Next action"] || "",
    "Next action date": d["Next action date"] || todayISO(),
    "Close reason": d["Close reason"] || "",
    "Close note": d["Close note"] || "",
  };
  const inputs = {
    "Stage": select("Stage", stages().map((s) => s.name), init.Stage, { blank: null }),
    "Offer": select("Offer", offers().map((o) => o.name), init.Offer),
    "Value": el("input", { name: "Value", type: "number", min: "0", step: "100", value: init.Value }),
    "Close date": el("input", { name: "Close date", type: "date", value: init["Close date"] }),
    "Source": select("Source", sources().map((s) => ({ value: s.id, label: s.name })), init.Source),
    "Owner": el("input", { name: "Owner", type: "text", value: init.Owner }),
    "Next action": el("input", { name: "Next action", type: "text", value: init["Next action"], placeholder: "Send the LOCK email with two times" }),
    "Next action date": el("input", { name: "Next action date", type: "date", value: init["Next action date"] }),
    "Close reason": select("Close reason", cfg().close_reasons || [], init["Close reason"]),
    "Close note": el("textarea", { name: "Close note" }, init["Close note"]),
  };
  inputs.Offer.addEventListener("change", () => {
    const o = offers().find((x) => x.name === inputs.Offer.value);
    if (o && (!inputs.Value.value || Number(inputs.Value.value) === 0 || isNew)) inputs.Value.value = o.value;
  });

  const errors = el("div", { class: "errors" });
  const save = el("button", { class: "btn", type: "submit" }, isNew ? "Create deal" : "Save deal");
  const openBlock = el("div", { class: "fields" },
    field("Next action", inputs["Next action"], true), field("Owner", inputs.Owner, true), field("Date", inputs["Next action date"], true));
  const closedBlock = el("div", { class: "fields" },
    field("Reason", inputs["Close reason"], true), field("Note", inputs["Close note"]));

  function values() {
    const out = {};
    for (const [k, i] of Object.entries(inputs)) out[k] = i.value;
    return out;
  }
  function refresh() {
    const v = values();
    const closed = isClosedStage(v.Stage);
    openBlock.hidden = closed;
    closedBlock.hidden = !closed;
    const msgs = validateDeal(v);
    errors.replaceChildren(...msgs.map((m) => el("div", {}, m)));
    save.disabled = msgs.length > 0;
  }
  for (const i of Object.values(inputs)) { i.addEventListener("input", refresh); i.addEventListener("change", refresh); }

  const title = company ? company.Name : (d.Deal || "Deal");
  const form = el("form", { class: "stack" },
    el("div", {}, el("div", { class: "label" }, isNew ? "New deal" : "Deal"), el("h2", {}, title),
      // a deal that came from a booking links to the booker's journey (2026-09-28)
      d.Leads && d.Leads.length ? el("a", { class: "link", href: `#/lead/${d.Leads[0]}`, onclick: () => modal.close() }, "See the booker's journey") : null),
    el("div", { class: "fields" },
      field("Stage", inputs.Stage, true), field("Offer", inputs.Offer), field("Value per month", inputs.Value, true),
      field("Close date", inputs["Close date"], true), field("Source", inputs.Source, true)),
    el("hr", { class: "hr" }),
    openBlock, closedBlock,
    el("div", { class: "actions" }, errors, save));
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = values();
    if (d.id) body.id = d.id;
    if (company && company.id) body.Company = [company.id];
    else if (d.Company) body.Company = d.Company;
    if (d.Contact) body.Contact = d.Contact;
    body.Source = body.Source ? [body.Source] : [];
    if (!isClosedStage(body.Stage)) { body["Close reason"] = ""; body["Close note"] = ""; }
    save.disabled = true;
    try {
      const res = await api.saveDeal(body);
      toast(isNew ? "Deal created." : "Deal saved.");
      modal.close();
      if (onSaved) onSaved(res.deal);
    } catch (err) {
      errors.replaceChildren(...err.errors.map((m) => el("div", {}, m)));
      save.disabled = false;
    }
  });
  const modal = openModal(form);
  refresh();
  return modal;
}
