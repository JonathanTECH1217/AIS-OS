// Companies: the list with search, the companies waiting on him, and the company file.
// The file (Jonathan, 2026-10-04: "when I search for a company, it displays me a neatly organized file"): what he still
// owes the company (a triage: the steps of the stage it is in, flags the CRM reads itself, his own to-dos), the key
// people spoken with, every contact made with it from every record (the CRM, the Prospects call sheet and its Outreach
// Log, site bookings, LinkedIn, call notes, mail), the deals, and its files. It opens for a company in the CRM and for
// one that is only in the Prospects call list (id "mb:MB-00258"), so the search finds every company he has called.
import { el, fmtDate, fmtDateTime, telHref, debounce, money } from "../util.js";
import { api } from "../api.js";
import { openDealForm } from "../components/deal-form.js";
import { openDialModal } from "../components/dial-modal.js";
import { openModal, toast } from "../components/modal.js";
import { artifactViewer } from "../components/artifact-view.js";
import { sources, state, verticals, verticalAirtable, takePendingSearch } from "../state.js";
import { navigate, rerender } from "../router.js";

const DONE = '<svg viewBox="0 0 24 24" width="20" height="20"><circle cx="12" cy="12" r="9" fill="currentColor"/><path d="M8 12.4l2.7 2.7L16.2 9.6" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const OPEN = '<svg viewBox="0 0 24 24" width="20" height="20"><circle cx="12" cy="12" r="8.4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>';
const WARN = '<svg viewBox="0 0 24 24" width="20" height="20"><path d="M12 4l8.5 15h-17z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M12 10v4.2M12 16.8v.2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';

function field(label, input, required) {
  return el("div", { class: "field" }, el("label", {}, label, required ? el("span", { class: "req" }, " *") : null), input);
}
function sourceSelect(value) {
  return el("select", { name: "Source" }, el("option", { value: "" }, ""), ...sources().map((s) => el("option", { value: s.id, selected: s.id === value }, s.name)));
}
function verticalSelect(value) {
  const cur = value || verticalAirtable();
  return el("select", { name: "Vertical" }, ...verticals().map((v) => el("option", { value: v.airtable, selected: v.airtable === cur }, v.label)));
}
const fileHash = (id) => `#/companies/${encodeURIComponent(id)}`;
const stageTag = (s) => el("span", { class: "tag" + (s === "Won" ? " won" : s === "Lost" ? " lost" : s === "Cold" ? " faint" : " solid") }, s);

// Every company with steps still open for the stage it is in, on top of the list (2026-10-04).
async function waitingPanel() {
  let board;
  try { board = await api.triageBoard(); } catch (e) { return null; }
  const rows = board.rows || [];
  if (!rows.length) return null;
  return el("div", { class: "panel" },
    el("div", { class: "row" }, el("h2", { class: "grow" }, "Waiting on you"), el("span", { class: "tag" }, `${rows.length} compan${rows.length === 1 ? "y" : "ies"}`)),
    el("div", { class: "muted", style: "font-size:12px" }, "Companies with steps still open for the stage they are in: overdue first, then booked meetings. Click one to open its file."),
    el("div", {}, ...rows.map((r) => {
      const row = el("div", { class: "task-row clickable", tabindex: "0", role: "button" },
        el("div", {},
          el("div", {}, el("span", { class: "strong" }, r.name), el("span", { class: "muted" }, [r.stage, r.from === "the call sheet" ? "in the call sheet, not on the board" : ""].filter(Boolean).map((x) => ` · ${x}`).join(""))),
          el("div", { class: "muted", style: "font-size:12px" }, r.next || "")),
        el("span", { class: "tag" + (r.overdue ? " lost" : "") }, `${r.open} to do`));
      const go = () => navigate(fileHash(r.id));
      row.addEventListener("click", go);
      row.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
      return row;
    })));
}

export async function renderCompanies(root, params) {
  if (params[0]) return renderCompany(root, params[0]);
  const fromTop = takePendingSearch();
  const search = el("input", { class: "search", type: "search", placeholder: "Name, city, state", value: fromTop });
  const wrap = el("div", { class: "table-wrap" });
  const more = el("div", { class: "stack" });
  const waiting = el("div", {});
  let straight = !!fromTop;   // a search from the top bar with one match opens its file at once
  async function load() {
    const q = search.value.trim();
    // every trade in one list since 2026-10-03; the Prospects call list by name since 2026-10-04 (three letters or more)
    const [rows, found] = await Promise.all([api.companies(q), q.length >= 3 ? api.prospects(q).catch(() => []) : Promise.resolve([])]);
    const extra = found.filter((p) => !p.crm_id && p.mb);
    if (straight && rows.length + extra.length === 1) {
      straight = false;
      navigate(fileHash(rows.length ? rows[0].id : `mb:${extra[0].mb}`));
      return;
    }
    straight = false;
    waiting.hidden = !!q;
    if (!rows.length) {
      wrap.replaceChildren(el("div", { class: "empty" }, state.health && !state.health.airtable_ready
        ? "Airtable is not connected yet. Add AIRTABLE_PAT and restart the server."
        : q ? "No company in the CRM by that name." : "No company touched yet. Log a dial from Today and the company appears here."));
    } else {
      const tb = el("tbody");
      for (const c of rows) {
        const tr = el("tr", { class: "clickable" },
          el("td", {}, c.Name, el("span", { class: "sub" }, [c.City, c.State].filter(Boolean).join(", "))),
          el("td", {}, c.Phone ? el("a", { class: "tel", href: telHref(c.Phone), onclick: (e) => e.stopPropagation() }, c.Phone) : ""),
          el("td", {}, el("span", { class: "tag" + (c.phase_calc === "Signed" ? " won" : c.phase_calc === "Untouched" ? " faint" : c.phase_calc === "Meeting booked" ? " solid" : "") }, c.phase_calc || "Untouched"), c.channels ? el("span", { class: "sub" }, `${c.channels} channel${c.channels === 1 ? "" : "s"}`) : null),
          el("td", {}, c.stage ? el("span", { class: "tag" + (c.stage === "Won" ? " won" : c.stage === "Lost" ? " lost" : "") }, c.stage) : el("span", { class: "muted" }, "no deal")),
          el("td", {}, c.source_name || ""),
          el("td", { class: "num" }, String(c.people || 0)),
          el("td", { class: "num" }, String(c["Dial attempts"] || 0)),
          el("td", {}, c["Last touch"] ? fmtDate(c["Last touch"]) : (c["Last dial"] ? `dial ${fmtDate(c["Last dial"])}` : "")));
        tr.addEventListener("click", () => navigate(fileHash(c.id)));
        tb.append(tr);
      }
      wrap.replaceChildren(el("table", {}, el("thead", {}, el("tr", {}, el("th", {}, "Company"), el("th", {}, "Phone"), el("th", {}, "Phase"), el("th", {}, "Stage"),
        el("th", {}, "Source"), el("th", { class: "num" }, "People"), el("th", { class: "num" }, "Dials"), el("th", {}, "Last touch"))), tb));
    }
    if (!extra.length) { more.replaceChildren(); return; }
    const tb = el("tbody");
    for (const p of extra) {
      const tr = el("tr", { class: "clickable" },
        el("td", {}, p.name, el("span", { class: "sub" }, [p.city, p.state].filter(Boolean).join(", "))),
        el("td", {}, p.phone ? el("a", { class: "tel", href: telHref(p.phone), onclick: (e) => e.stopPropagation() }, p.phone) : ""),
        el("td", {}, p.typed ? el("span", {}, `"${p.typed}"`) : el("span", { class: "muted" }, "not called yet")),
        el("td", {}, p.vertical || ""),
        el("td", { class: "num" }, p.mb));
      tr.addEventListener("click", () => navigate(fileHash(`mb:${p.mb}`)));
      tb.append(tr);
    }
    more.replaceChildren(
      el("div", {}, el("div", { class: "label" }, "In your call list"), el("div", { class: "muted", style: "font-size:12px" }, "From the Prospects base by name. Not in the CRM yet; the file opens all the same.")),
      el("div", { class: "table-wrap" }, el("table", {}, el("thead", {}, el("tr", {}, el("th", {}, "Company"), el("th", {}, "Phone"), el("th", {}, "Call sheet status"), el("th", {}, "Trade"), el("th", { class: "num" }, "ID"))), tb)));
  }
  search.addEventListener("input", debounce(load, 250));
  root.append(
    el("div", { class: "head" },
      el("div", {}, el("div", { class: "label" }, "Companies"), el("h1", {}, "Every company you have touched"),
        el("div", { class: "sub" }, "Search by name: the CRM first, then your call list. A company opens as a file: what you owe it, who you spoke with, every contact made.")),
      el("button", { class: "btn quiet", type: "button", onclick: () => openCompanyForm({ onSaved: (c) => navigate(fileHash(c.id)) }) }, "Add a company")),
    el("div", { class: "row" }, search), waiting, wrap, more);
  waitingPanel().then((p) => { if (p) waiting.append(p); });
  await load();
}

// company: the CRM record being edited; prefill: values for a new one (a company from the call list)
export function openCompanyForm({ company, prefill, onSaved } = {}) {
  const c = company || {};
  const v = Object.assign({}, prefill || {}, c);
  const inputs = {
    Name: el("input", { type: "text", value: v.Name || "" }),
    Website: el("input", { type: "url", value: v.Website || "", placeholder: "https://" }),
    Phone: el("input", { type: "tel", value: v.Phone || "" }),
    City: el("input", { type: "text", value: v.City || "" }),
    State: el("input", { type: "text", value: v.State || "", maxlength: "2" }),
    Source: sourceSelect((v.Source || [])[0] || ""),
    Vertical: verticalSelect(v.Vertical || ""),
    Notes: el("textarea", {}, v.Notes || ""),
  };
  const errors = el("div", { class: "errors" });
  const save = el("button", { class: "btn", type: "submit" }, c.id ? "Save company" : "Add company");
  const form = el("form", { class: "stack" },
    el("div", {}, el("div", { class: "label" }, c.id ? "Company" : "New company"), el("h2", {}, v.Name || "A company")),
    el("div", { class: "fields" }, field("Name", inputs.Name, true), field("Website", inputs.Website), field("Phone", inputs.Phone),
      field("City", inputs.City), field("State", inputs.State), field("Source", inputs.Source), field("Vertical", inputs.Vertical)),
    field("Notes", inputs.Notes),
    el("div", { class: "actions" }, errors, save));
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {};
    for (const [k, i] of Object.entries(inputs)) body[k] = i.value.trim();
    if (c.id) body.id = c.id;
    save.disabled = true;
    try {
      const res = await api.saveCompany(body);
      toast(c.id ? "Company saved." : "Company added.");
      modal.close();
      if (onSaved) onSaved(res.company);
    } catch (err) {
      errors.replaceChildren(...err.errors.map((m) => el("div", {}, m)));
      if (err.body && err.body.duplicate) errors.append(el("button", { class: "link", type: "button", onclick: () => { modal.close(); navigate(fileHash(err.body.duplicate.id)); } }, "Open the existing record"));
      save.disabled = false;
    }
  });
  const modal = openModal(form);
  return modal;
}

export function openPersonForm({ company, person, onSaved } = {}) {
  const p = person || {};
  const inputs = {
    "Full name": el("input", { type: "text", value: p["Full name"] || "" }),
    Role: el("input", { type: "text", value: p.Role || "", placeholder: "Owner, ops, office" }),
    Email: el("input", { type: "email", value: p.Email || "" }),
    Phone: el("input", { type: "tel", value: p.Phone || "" }),
    Source: sourceSelect((p.Source || company.Source || [])[0] || ""),
    Notes: el("textarea", {}, p.Notes || ""),
  };
  const primary = el("input", { type: "checkbox", checked: !!p["Primary contact"] });
  const errors = el("div", { class: "errors" });
  const save = el("button", { class: "btn", type: "submit" }, p.id ? "Save person" : "Add person");
  const form = el("form", { class: "stack" },
    el("div", {}, el("div", { class: "label" }, company.Name), el("h2", {}, p.id ? p["Full name"] : (p["Full name"] || "New person"))),
    el("div", { class: "fields" }, field("Full name", inputs["Full name"], true), field("Role", inputs.Role), field("Email", inputs.Email),
      field("Phone", inputs.Phone), field("Source", inputs.Source)),
    field("Notes", inputs.Notes),
    el("label", { class: "row", style: "font-size:14px" }, primary, " Primary contact"),
    el("div", { class: "actions" }, errors, save));
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = { Company: company.id, "Primary contact": primary.checked };
    for (const [k, i] of Object.entries(inputs)) body[k] = i.value.trim();
    if (p.id) body.id = p.id;
    save.disabled = true;
    try {
      await api.savePerson(body);
      toast(p.id ? "Person saved." : "Person added.");
      modal.close();
      if (onSaved) onSaved();
    } catch (err) {
      errors.replaceChildren(...err.errors.map((m) => el("div", {}, m)));
      save.disabled = false;
    }
  });
  const modal = openModal(form);
  return modal;
}

function openNoteForm({ company, onSaved }) {
  const type = el("select", {}, ...["Note", "Email", "Text", "DM", "Meeting"].map((t) => el("option", { value: t }, t)));
  const summary = el("input", { type: "text", placeholder: "One line" });
  const notes = el("textarea", {});
  const save = el("button", { class: "btn", type: "submit" }, "Add to the record");
  const errors = el("div", { class: "errors" });
  const form = el("form", { class: "stack" },
    el("div", {}, el("div", { class: "label" }, company.Name), el("h2", {}, "Add to the contact log")),
    el("div", { class: "fields" }, field("Type", type), field("Summary", summary, true)),
    field("Notes", notes),
    el("div", { class: "actions" }, errors, save));
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!summary.value.trim()) { errors.replaceChildren(el("div", {}, "Give it one line.")); return; }
    save.disabled = true;
    try {
      await api.saveActivity({ Company: company.id, Type: type.value, Summary: summary.value.trim(), Notes: notes.value });
      toast("Added.");
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

// ---------------------------------------------------------------- the company file

const when = (at) => (!at ? "" : /^\d{4}-\d{2}-\d{2}$/.test(at) ? fmtDate(at) : fmtDateTime(at));
const mmss = (sec) => `${Math.floor((sec || 0) / 60)}:${String((sec || 0) % 60).padStart(2, "0")}`;
const KIND = { Call: "", Email: " solid", Meeting: " won", Form: " solid", LinkedIn: "", Loom: "" };
const svg = (html, cls) => el("span", { class: cls, "aria-hidden": "true", html });

function notesBlock(text) {
  const t = String(text || "").trim();
  if (!t) return null;
  if (t.length <= 320) return el("div", { class: "notes" }, t);
  return el("details", { class: "more" },
    el("summary", {}, el("span", { class: "notes preview" }, `${t.slice(0, 300)}… `), el("span", { class: "link" }, "more")),
    el("div", { class: "notes" }, t));
}

function openFile(item) {
  const v = artifactViewer("Opening...");
  openModal(el("div", { class: "stack file-modal" }, v.viewer), { wide: true });
  v.show(item, item.name);
}

async function renderCompany(root, id) {
  const f = await api.companyFile(id);
  if (f.redirect) { navigate(fileHash(f.redirect)); return; }
  const h = f.head, c = f.company, inCrm = h.in_crm;
  const reload = () => rerender();
  const openDeal = (f.deals || []).find((d) => !d.Closed);
  const trade = /integrat/i.test(h.vertical) ? "Integrator" : /electric/i.test(h.vertical) ? "Electrician" : "";
  const addToCrm = () => openCompanyForm({
    prefill: { Name: h.name, Website: h.website, Phone: h.phone, City: h.city, State: h.state, Vertical: trade },
    onSaved: (made) => navigate(fileHash(made.id)),
  });
  const post = async (body) => {
    try { await api.triage(id, body); reload(); } catch (e) { toast((e.errors || [String(e)]).join(" "), true); }
  };

  // ---- what he owes this company
  const triageBox = el("div", { class: "panel" });
  function paintTriage(mail) {
    const t = f.triage;
    const seenMail = (mail && mail.seen) || {};
    const steps = t.steps.map((s) => (seenMail[s.id] ? Object.assign({}, s, { done: true, seen: seenMail[s.id] }) : s));
    const openSteps = steps.filter((s) => !s.done), doneSteps = steps.filter((s) => s.done);
    const openCustom = t.custom.filter((x) => !x.done), doneCustom = t.custom.filter((x) => x.done);
    const drafts = (mail && mail.drafts) || [];
    const acts = {
      deal: ["Open the deal", () => openDealForm(openDeal, { company: c, onSaved: reload })],
      add: ["Add to the CRM", addToCrm],
      "new-deal": ["New deal", () => openDealForm(null, { company: c, onSaved: reload })],
      sheet: ["Open the call sheet", () => { if (h.sheet && h.sheet.url) window.open(h.sheet.url, "_blank", "noopener"); }],
      person: [inCrm ? "Add a person" : "Add to the CRM", () => (inCrm ? openPersonForm({ company: c, onSaved: reload }) : addToCrm())],
    };
    const flagRow = (fl) => {
      const a = acts[fl.act];
      return el("li", { class: "camp-task flag" }, svg(WARN, "camp-check"), el("div", { class: "camp-task-text" }, el("div", {}, fl.text)),
        a ? el("button", { class: "btn quiet small act", type: "button", onclick: a[1] }, a[0]) : null);
    };
    const stepRow = (s) => {
      const fixed = !!s.seen;                              // the CRM saw it for itself: nothing to tick
      const asks = !s.done && s.ask && s.ask.length;       // a step with an answer (showed or no-show): two buttons, not a tick
      const loom = /:loom-brief$/.test(s.id) && !s.done ? (f.looms || [])[0] : null;
      const sub = s.done ? (s.seen || [s.answer, s.done_on ? `done ${fmtDate(s.done_on)}` : "done"].filter(Boolean).join(", "))
        : loom ? `Recorded: ${loom.title || "the Loom"} (${mmss(loom.seconds)}). Not in Sent yet; send it and this ticks by itself.` : (s.why || "");
      const li = el("li", { class: "camp-task" + (s.done ? " done" : "") + (fixed || asks ? "" : " clickable"), tabindex: fixed || asks ? null : "0",
        title: fixed ? "The CRM saw this for itself" : asks ? null : s.done ? "Click to mark open" : "Click to mark done" },
        svg(s.done ? DONE : OPEN, "camp-check" + (s.done ? " up" : "")),
        el("div", { class: "camp-task-text" }, el("div", {}, s.text), el("div", { class: "sub" }, sub)),
        asks ? el("span", { class: "row act", style: "gap:6px" }, ...s.ask.map((a) => el("button", { class: "btn quiet small", type: "button", onclick: () => post({ step: s.id, done: true, answer: a }) }, a)))
          : s.doc && !s.done ? el("button", { class: "link act", type: "button", style: "font-size:12px", onclick: (e) => { e.stopPropagation(); openFile({ path: s.doc, name: s.doc.split("/").pop() }); } }, "Open the template") : null);
      if (!fixed && !asks) {
        const go = () => post({ step: s.id, done: !s.done });
        li.addEventListener("click", go);
        li.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
      }
      return li;
    };
    const customRow = (x) => {
      const li = el("li", { class: "camp-task clickable" + (x.done ? " done" : ""), tabindex: "0", title: x.done ? "Click to mark open" : "Click to mark done" },
        svg(x.done ? DONE : OPEN, "camp-check" + (x.done ? " up" : "")),
        el("div", { class: "camp-task-text" }, el("div", {}, x.text), el("div", { class: "sub" }, x.done ? `done ${fmtDate(x.done_on)}` : `yours, added ${fmtDate(x.added)}`)),
        el("button", { class: "link act", type: "button", style: "font-size:12px", onclick: (e) => { e.stopPropagation(); post({ custom: x.id, remove: true }); } }, "Remove"));
      const go = () => post({ custom: x.id, done: !x.done });
      li.addEventListener("click", go);
      li.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
      return li;
    };
    const draftRow = (d) => el("li", { class: "camp-task flag" }, svg(WARN, "camp-check"),
      el("div", { class: "camp-task-text" }, el("div", {}, `A draft to them is waiting in Proton: ${d.subject || "(no subject)"}`), el("div", { class: "sub" }, "Read it and send it from Proton.")));
    const openRows = [...t.flags.map(flagRow), ...drafts.map(draftRow), ...openSteps.map(stepRow), ...openCustom.map(customRow)];
    const doneRows = [...doneSteps.map(stepRow), ...doneCustom.map(customRow)];
    const input = el("input", { type: "text", placeholder: "Add a to-do for this company", "aria-label": "Add a to-do" });
    const add = el("form", { class: "triage-add" }, input, el("button", { class: "btn quiet small", type: "submit" }, "Add"));
    add.addEventListener("submit", (e) => { e.preventDefault(); if (input.value.trim()) post({ add: input.value.trim() }); });
    const facts = el("div", { class: "triage-facts" },
      el("div", {}, el("b", {}, "Stage: "), `${t.stage}, from ${h.stage_from}.`),
      h.meeting ? el("div", {}, el("b", {}, "Meeting: "), `${h.meeting.text || when(h.meeting.at)} (${h.meeting.from}).`) : null,
      h.sheet && h.sheet.typed ? el("div", {}, el("b", {}, "Call sheet: "), `"${h.sheet.typed}"${h.sheet.changed ? `, ${when(h.sheet.changed)}` : ""}.`) : null);
    // the DOM's own replaceChildren writes a null as the word "null", so the empty slots are dropped first
    triageBox.replaceChildren(...[
      el("div", { class: "row" }, el("h2", { class: "grow" }, "To do for this company"),
        el("span", { class: "tag" + (openRows.length ? "" : " won") }, openRows.length ? `${openRows.length} open` : "Nothing open")),
      facts,
      openRows.length ? el("ul", { class: "camp-tasks" }, ...openRows)
        : el("div", { class: "muted", style: "font-size:13px" }, t.steps.length ? "Every step for this stage is done." : `No steps are written for the ${t.stage} stage (projects/crm/playbook.json).`),
      add,
      doneRows.length ? el("details", { class: "more" }, el("summary", {}, el("span", { class: "link", style: "font-size:12px" }, `Done (${doneRows.length})`)), el("ul", { class: "camp-tasks", style: "margin-top:8px" }, ...doneRows)) : null,
    ].filter(Boolean));
  }

  // ---- every contact made with it
  const logBox = el("div", { class: "panel" });
  function paintLog(mail) {
    const items = f.log.slice();
    for (const m of (mail && mail.items) || []) {
      items.push({ at: m.at || "", kind: "Email", src: m.folder === "INBOX" ? "Inbox" : m.folder,
        summary: `${m.folder === "INBOX" ? "From them" : m.folder === "Drafts" ? (m.superseded ? "Earlier draft of a sent email" : "Draft, not sent") : "Sent"}: ${m.subject || "(no subject)"}`,
        who: m.folder === "INBOX" ? m.from : `to ${m.to}`, notes: m.snippet + (m.attachments ? `\n${m.attachments} attachment${m.attachments === 1 ? "" : "s"}` : "") });
    }
    // by the moment itself: the CRM's times are UTC, the mailbox's Eastern, the Outreach Log's a bare day (taken as noon)
    const ts = (at) => { const d = /^\d{4}-\d{2}-\d{2}$/.test(at) ? new Date(`${at}T12:00:00`) : new Date(at); return isNaN(d) ? 0 : d.getTime(); };
    items.sort((a, b) => ts(b.at) - ts(a.at));
    const mailNote = !mail ? "Looking in the mailbox..." : mail.note || (mail.bridge === "ok" ? `${mail.items.length} email${mail.items.length === 1 ? "" : "s"} found in Proton.` : "");
    logBox.replaceChildren(
      el("div", { class: "row" }, el("h2", { class: "grow" }, "Contact log"), el("span", { class: "tag faint" }, `${items.length}`),
        inCrm ? el("button", { class: "btn quiet small", type: "button", onclick: () => openNoteForm({ company: c, onSaved: reload }) }, "Add a note") : null),
      el("div", { class: "muted", style: "font-size:12px" }, `Every call, email, meeting, form, and note on record, newest first. ${mailNote}`),
      items.length ? el("div", { class: "timeline" }, ...items.map((a) => {
        const item = el("div", { class: "item" + (a.path ? " clickable" : "") },
          el("div", { class: "when" }, when(a.at), el("span", { class: "sub muted", style: "display:block" }, a.src || "")),
          el("div", { class: "what" },
            el("div", {}, el("span", { class: "tag" + (KIND[a.kind] !== undefined ? KIND[a.kind] : " faint") }, a.kind), " ", a.summary, a.who ? el("span", { class: "muted" }, ` · ${a.who}`) : null),
            notesBlock(a.notes)));
        if (a.path) item.addEventListener("click", (e) => { if (!e.target.closest("details")) openFile({ path: a.path, name: a.summary }); });
        return item;
      })) : el("div", { class: "muted" }, "Nothing on record yet.", (h.dials ? ` ${h.dials} no-contact dial${h.dials === 1 ? "" : "s"}.` : "")));
  }

  // ---- the people
  const people = el("div", { class: "panel" },
    el("div", { class: "row" }, el("h2", { class: "grow" }, "People"),
      inCrm ? el("button", { class: "btn quiet small", type: "button", onclick: () => openPersonForm({ company: c, onSaved: reload }) }, "Add person") : null),
    f.people.length ? el("div", {}, ...f.people.map((p) => {
      const sub = [p.last ? `last ${fmtDate(p.last)}` : null, p.touches ? `${p.touches} touchpoint${p.touches === 1 ? "" : "s"}` : null, p.sources.join(", ")].filter(Boolean).join(" · ");
      const can = inCrm;
      const row = el("div", { class: "person-row" + (can ? " clickable" : ""), title: can ? (p.crm ? "Click to edit" : "Click to add to the CRM") : null },
        el("div", {},
          el("div", {}, el("span", { class: "strong" }, p.name), p.role ? el("span", { class: "muted" }, ` · ${p.role}`) : null, p.primary ? el("span", { class: "tag faint", style: "margin-left:8px" }, "primary") : null,
            inCrm && !p.crm ? el("span", { class: "tag faint", style: "margin-left:8px" }, "not in the CRM") : null),
          el("div", { class: "muted", style: "font-size:12px" }, sub)),
        el("div", { class: "person-links" },
          p.email ? el("a", { class: "tel", href: `mailto:${p.email}`, onclick: (e) => e.stopPropagation() }, p.email) : null,
          p.phone ? el("a", { class: "tel", href: telHref(p.phone), onclick: (e) => e.stopPropagation() }, p.phone) : null));
      if (can) row.addEventListener("click", () => openPersonForm({ company: c, person: p.crm || { "Full name": p.name, Role: p.role, Email: p.email, Phone: p.phone }, onSaved: reload }));
      return row;
    })) : el("div", { class: "muted" }, "No one on record yet. Log who you spoke with after the next call."));

  // ---- deals (only once it is in the CRM)
  const deals = inCrm ? el("div", { class: "panel" },
    el("div", { class: "row" }, el("h2", { class: "grow" }, "Deals"),
      el("button", { class: "btn quiet small", type: "button", disabled: !!openDeal, title: openDeal ? "One open deal per company" : "", onclick: () => openDealForm(null, { company: c, onSaved: reload }) }, "New deal")),
    f.deals.length ? el("div", { class: "stack" }, ...f.deals.map((d) => {
      const overdue = !d.Closed && d["Next action date"] && d["Next action date"] < (state.health.today || "");
      const card = el("div", { class: "card", tabindex: "0", role: "button" },
        el("div", { class: "row" }, el("span", { class: "tag" + (d.Won ? " won" : d.Closed ? " lost" : " solid") }, d.Stage), el("span", { class: "num" }, money(d.Value, { mo: true })), el("span", { class: "muted" }, d.Offer || ""), el("span", { class: "muted" }, d.source_name ? `via ${d.source_name}` : "")),
        el("div", { class: "meta" }, el("span", {}, `Close ${fmtDate(d["Close date"])}`), el("span", {}, d.Owner ? `Owner ${d.Owner}` : "")),
        d.Closed ? el("div", { class: "next muted" }, d["Close reason"] || "", d["Close note"] ? ` · ${d["Close note"]}` : "")
          : el("div", { class: "next" + (overdue ? " overdue" : "") }, d["Next action"] ? `${d["Next action"]} · ${fmtDate(d["Next action date"])}${overdue ? " · overdue" : ""}` : "No next action"));
      card.addEventListener("click", () => openDealForm(d, { company: c, onSaved: reload }));
      card.addEventListener("keydown", (e) => { if (e.key === "Enter") openDealForm(d, { company: c, onSaved: reload }); });
      return card;
    })) : el("div", { class: "muted" }, "No deal yet."))
    : el("div", { class: "panel soft" }, el("h2", {}, "Not in the CRM yet"),
      el("div", { class: "muted", style: "font-size:13px" }, "This company lives in your call list only. Add it to put a deal on the board; the to-dos and this file carry over."),
      el("div", {}, el("button", { class: "btn small", type: "button", onclick: addToCrm }, "Add to the CRM")));

  // ---- the Loom brief sent before the meeting (2026-10-04): the link, which variation it is, whether they watched it.
  // Show rate and close rate by variation are on Reports.
  const loomPost = async (body) => {
    try { await api.loom(id, body); reload(); } catch (e) { toast((e.errors || [String(e)]).join(" "), true); }
  };
  const loomPanel = (f.looms || []).length || ["Booked", "Held", "Proposed", "Won"].includes(h.stage) ? (() => {
    const vars = f.loom_variations || [];
    const rows = (f.looms || []).map((l) => {
      // kind (2026-10-05): a brief before a meeting, or a page review of a lead (kept off the show-rate report)
      const ksel = el("select", { "aria-label": "Kind" }, ...[["brief", "Brief before the meeting"], ["review", "Page review (lead)"]].map(([v, t]) => el("option", { value: v, selected: v === (l.kind || "brief") }, t)));
      ksel.addEventListener("change", () => loomPost({ id: l.id, kind: ksel.value }));
      const vsel = el("select", { "aria-label": "Variation" }, el("option", { value: "" }, "No variation"),
        ...vars.map((v) => el("option", { value: v.key, selected: v.key === l.variation }, `${v.key}: ${v.name}`)), el("option", { value: "__new" }, "New variation..."));
      vsel.addEventListener("change", () => {
        if (vsel.value !== "__new") { loomPost({ id: l.id, variation: vsel.value }); return; }
        const name = window.prompt("Name the new variation: what is different about this walkthrough?");
        if (name && name.trim()) loomPost({ id: l.id, new_variation: name.trim() }); else vsel.value = l.variation || "";
      });
      const wsel = el("select", { "aria-label": "Watched" }, ...[["", "Watched: not known"], ["yes", "They watched it"], ["no", "Not watched"]].map(([v, t]) => el("option", { value: v, selected: v === (l.watched || "") }, t)));
      wsel.addEventListener("change", () => loomPost({ id: l.id, watched: wsel.value }));
      return el("div", { class: "loom-row" },
        el("div", {}, el("a", { class: "link", href: l.url, target: "_blank", rel: "noopener" }, l.title || "Loom"), el("span", { class: "muted num" }, ` · ${mmss(l.seconds)}`)),
        el("div", { class: "muted", style: "font-size:12px" }, l.sent_on ? `Sent ${fmtDate(l.sent_on)}` : `Recorded ${fmtDate(l.made)}, not in Sent yet`),
        el("div", { class: "row", style: "gap:8px;flex-wrap:wrap" }, ksel, l.kind === "review" ? null : vsel, wsel, el("button", { class: "link", type: "button", style: "font-size:12px", onclick: () => loomPost({ id: l.id, remove: true }) }, "Remove")));
    });
    const input = el("input", { type: "url", placeholder: "Paste a Loom link", "aria-label": "Loom link" });
    const kind = el("select", { "aria-label": "Kind of Loom" }, el("option", { value: "brief" }, "Brief"), el("option", { value: "review" }, "Page review"));
    const form = el("form", { class: "triage-add" }, input, kind, el("button", { class: "btn quiet small", type: "submit" }, "Add"));
    form.addEventListener("submit", (e) => { e.preventDefault(); if (input.value.trim()) loomPost({ url: input.value.trim(), kind: kind.value }); });
    return el("div", { class: "panel" },
      el("div", { class: "row" }, el("h2", { class: "grow" }, "Loom brief"), el("a", { class: "link", href: "#/reports", style: "font-size:12px" }, "Show rate by variation")),
      rows.length ? el("div", {}, ...rows) : el("div", { class: "muted", style: "font-size:13px" }, "None on this file yet. Paste the link once it is recorded."),
      form);
  })() : null;

  const notes = h.notes || h.sheet_notes ? el("div", { class: "panel soft" }, el("div", { class: "label" }, "Notes"),
    h.notes ? el("div", { style: "white-space:pre-wrap" }, h.notes) : null,
    h.sheet_notes ? el("div", { style: "white-space:pre-wrap" }, el("span", { class: "muted" }, "Call sheet: "), h.sheet_notes) : null) : null;

  const files = f.files.length ? el("div", { class: "panel" }, el("h2", {}, "Files"),
    el("div", { class: "file-list" }, ...f.files.map((it) => el("button", { type: "button", onclick: () => openFile(it) },
      el("span", { class: "grow" }, it.name), el("span", { class: "muted" }, it.group), el("span", { class: "muted num" }, it.at ? fmtDate(it.at.slice(0, 10)) : ""))))) : null;

  const site = h.website ? (/^https?:/i.test(h.website) ? h.website : `https://${h.website}`) : "";
  root.append(
    el("div", { class: "head" },
      el("div", {},
        el("div", { class: "label" }, el("a", { href: "#/companies" }, "Companies"), " · ", [h.city, h.state].filter(Boolean).join(", "), h.local_noon ? ` · ${h.local_noon} local at noon ET` : ""),
        el("h1", {}, h.name),
        el("div", { class: "file-tags" },
          h.phone ? el("a", { class: "tel", href: telHref(h.phone) }, h.phone) : null,
          site ? el("a", { class: "tel", href: site, target: "_blank", rel: "noopener" }, site.replace(/^https?:\/\/(www\.)?/, "").replace(/\/.*$/, "")) : null,
          stageTag(h.stage),
          h.phase && h.phase !== "Untouched" ? el("span", { class: "tag" + (h.phase === "Signed" ? " won" : "") }, h.phase) : null,
          h.vertical ? el("span", { class: "tag faint" }, h.vertical) : null,
          h.mb ? el("span", { class: "tag faint num" }, h.mb) : null,
          h.source ? el("span", { class: "tag faint" }, `source: ${h.source}`) : null,
          h.reviews ? el("span", { class: "muted num" }, `${h.rating || ""} stars, ${h.reviews} reviews`) : null,
          h.dials ? el("span", { class: "muted num" }, `${h.dials} dial${h.dials === 1 ? "" : "s"} in the CRM`) : null,
          h.sheet && h.sheet.url ? el("a", { class: "link", href: h.sheet.url, target: "_blank", rel: "noopener", style: "font-size:12px" }, "Call sheet row") : null)),
      el("div", { class: "row" },
        inCrm ? el("button", { class: "btn quiet", type: "button", onclick: () => openCompanyForm({ company: c, onSaved: reload }) }, "Edit") : null,
        inCrm ? el("button", { class: "btn", type: "button", onclick: () => openDialModal(Object.assign({ key: c.Key, source: c.source_name }, c, f.queue || {}), { onLogged: reload }) }, "Log dial")
          : el("button", { class: "btn", type: "button", onclick: addToCrm }, "Add to the CRM"))),
    el("div", { class: "file-grid" }, el("div", { class: "stack", style: "gap:24px" }, triageBox, logBox), el("div", { class: "stack", style: "gap:24px" }, people, loomPanel, deals, notes, files)));
  paintTriage(null);
  paintLog(null);
  // the mailbox answers after the page has drawn: emails join the log, a sent Loom link ticks its step, waiting drafts show
  api.companyMail(id).then((mail) => { paintTriage(mail); paintLog(mail); }).catch(() => paintLog({ items: [], note: "The mailbox could not be read." }));
}
