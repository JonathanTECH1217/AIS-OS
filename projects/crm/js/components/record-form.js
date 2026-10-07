// A small form for the workspace tables (moved out of the channel view 2026-09-29 so Channels can edit campaigns and
// listings too). spec: [{name, label, type, options, required, value}]
import { el } from "../util.js";
import { api } from "../api.js";
import { openModal, toast } from "./modal.js";

function field(label, input, required) {
  return el("div", { class: "field" }, el("label", {}, label, required ? el("span", { class: "req" }, " *") : null), input);
}

export function openRecordForm({ table, title, spec, record, onSaved }) {
  const r = record || {};
  const inputs = {};
  const rows = spec.map((f) => {
    let input;
    const v = r[f.name] !== undefined && r[f.name] !== null ? (Array.isArray(r[f.name]) ? r[f.name][0] : r[f.name]) : (f.value !== undefined ? f.value : "");
    if (f.type === "select") input = el("select", {}, el("option", { value: "" }, ""), ...f.options.map((o) => el("option", { value: o.value !== undefined ? o.value : o, selected: (o.value !== undefined ? o.value : o) === v }, o.label !== undefined ? o.label : o)));
    else if (f.type === "textarea") input = el("textarea", { rows: f.rows || null }, v);
    else input = el("input", { type: f.type || "text", value: v, step: f.type === "number" ? "1" : null });
    inputs[f.name] = input;
    return field(f.label, input, f.required);
  });
  const errors = el("div", { class: "errors" });
  const save = el("button", { class: "btn", type: "submit" }, r.id ? "Save" : "Add");
  const form = el("form", { class: "stack" }, el("div", {}, el("div", { class: "label" }, table), el("h2", {}, title)), el("div", { class: "fields" }, ...rows), el("div", { class: "actions" }, errors, save));
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {};
    for (const [k, i] of Object.entries(inputs)) body[k] = i.value;
    if (r.id) body.id = r.id;
    save.disabled = true;
    try {
      await api.saveRecord(table, body);
      toast(r.id ? "Saved." : "Added.");
      modal.close();
      onSaved();
    } catch (err) {
      errors.replaceChildren(...err.errors.map((m) => el("div", {}, m)));
      save.disabled = false;
    }
  });
  const modal = openModal(form);
  return modal;
}

// ch: the channel the campaign sits on, {id, label}
export function campaignSpec(ch) {
  return [
    { name: "Name", label: "Name", required: true },
    { name: "Status", label: "Status", type: "select", options: ["Planned", "Live", "Paused", "Ended"], value: "Planned" },
    { name: "Platform id", label: "Platform id (utm_campaign)" },
    { name: "Objective", label: "Objective" },
    { name: "Outcomes", label: "Outcomes we want (one per line)", type: "textarea", rows: 4 },
    { name: "Tasks", label: "Tasks (one per line; start with [x] when done)", type: "textarea", rows: 5 },
    { name: "Daily budget", label: "Daily budget", type: "number" },
    { name: "Started", label: "Started", type: "date" },
    { name: "Ended", label: "Ended", type: "date" },
    { name: "Spend to date", label: "Spend to date", type: "number" },
    { name: "Impressions", label: "Impressions", type: "number" },
    { name: "Clicks", label: "Clicks", type: "number" },
    { name: "Channel", label: "Channel", type: "select", options: [{ value: ch.id, label: ch.label }], value: ch.id },
    { name: "Notes", label: "Notes", type: "textarea" },
  ];
}

// one free-campaign delivery (2026-10-03): the stage is what Jonathan sets; the dates come from the script's read-back
export function freeCampaignSpec() {
  return [
    { name: "Stage", label: "Stage", type: "select", options: ["Built", "Approved", "Delivery drafted", "Delivered", "Ask drafted", "Ask sent", "Review left", "Declined"], value: "Built" },
    { name: "Email", label: "Email the files go to", type: "email" },
    { name: "Delivered on", label: "Delivered on", type: "date" },
    { name: "Ask due", label: "Review ask due", type: "date" },
    { name: "Ask sent on", label: "Ask sent on", type: "date" },
    { name: "Review left on", label: "Review left on", type: "date" },
    { name: "Notes", label: "Notes", type: "textarea" },
  ];
}

export function listingSpec() {
  return [
    { name: "Status", label: "Status", type: "select", options: ["To do", "Submitted", "Verifying", "Live", "Needs fix"], value: "To do" },
    { name: "Live on", label: "Live on", type: "date" },
    { name: "Listing URL", label: "Listing URL", type: "url" },
    { name: "Link", label: "Link to monarcbuild.com", type: "select", options: ["Followed", "Nofollow", "No link"] },
    { name: "NAP matches", label: "Name, city, phone match exactly", type: "select", options: [{ value: "true", label: "Yes" }, { value: "", label: "No" }] },
    { name: "Login email", label: "Login email (never a password)", type: "email" },
    { name: "Notes", label: "Notes", type: "textarea" },
  ];
}
