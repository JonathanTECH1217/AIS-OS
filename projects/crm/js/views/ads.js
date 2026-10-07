// Ads (Jonathan, 2026-09-28): publish Monarc's own Google Ads from the OS. Four approvals per campaign (spend,
// keywords, negatives by list, the ad), then Publish, which builds the campaign in Google Ads paused, then Go live,
// locked until the five gates are done and held to $100 a day with one test campaign at a time. Every change that
// reaches Google sits behind a confirm. The rules live in scripts/ads_publish.py; this file only asks and shows.
// Since 2026-09-29 these parts live on the Google Ads channel page (Jonathan: the paid ads card should open the
// campaign details to approve, disapprove, and edit), inside each campaign's row; #/ads sends you there. The ad's
// headlines and descriptions carry an X to take one out and a box to add your own; any change needs the ad approved again.
import { el, money, fmtDateTime } from "../util.js";
import { api } from "../api.js";
import { openModal, toast } from "../components/modal.js";
import { rerender } from "../router.js";
import { fold } from "../components/fold.js";

const PARTS = [
  ["spend", "Spend"],
  ["keywords", "Keywords"],
  ["negatives", "Negatives"],
  ["ad", "The ad"],
];
const STATE_WORD = { approved: "Approved", changed: "Changed since approval", open: "Not approved" };

function tagFor(st) {
  return el("span", { class: "tag " + (st === "approved" ? "won" : st === "changed" ? "lost" : "faint") }, STATE_WORD[st] || st);
}

function statusTag(c) {
  if (c.status === "ENABLED") return el("span", { class: "tag won" }, "Live");
  if (c.status === "PAUSED") return el("span", { class: "tag" }, c.waiting.length ? "Paused, changes waiting" : "Built, paused");
  return el("span", { class: "tag faint" }, "Not published");
}

// A confirm step for every change: say what happens in plain words, then do it.
function confirmStep(title, lines, label, run, { danger = false, input = null } = {}) {
  const errs = el("div", { class: "errors" });
  const go = el("button", { class: "btn" + (danger ? " danger" : ""), type: "submit" }, label);
  const form = el("form", { class: "stack" },
    el("h2", {}, title),
    ...lines.map((ln) => el("p", { class: "body" }, ln)),
    input,
    el("div", { class: "actions" }, errs, el("button", { class: "btn quiet", type: "button", onclick: () => m.close() }, "Cancel"), go));
  const m = openModal(form);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    go.disabled = true;
    errs.replaceChildren();
    try {
      await run(form);
      m.close();
    } catch (err) {
      errs.replaceChildren(...(err.errors || [String(err)]).map((x) => el("div", {}, x)));
      go.disabled = false;
    }
  });
}

async function act(nn, action, body, done) {
  const r = await api.post(`/api/ads/${nn}/${action}`, body || {});
  if (done) toast(done);
  window.dispatchEvent(new HashChangeEvent("hashchange"));
  return r;
}

const errText = (err) => (err.errors || [String(err)]).join(" ");

function approveBtn(c, part, group) {
  return el("button", { class: "btn small", type: "button", onclick: async (e) => {
    e.target.disabled = true;
    try { await act(c.nn, "approve", { part, group }, group ? `Approved: ${group}` : "Approved"); }
    catch (err) { toast(errText(err), true); e.target.disabled = false; }
  } }, "Approve");
}

// Disapprove (2026-09-29): take an approval back. Publish waits until it is approved again.
function takeBackBtn(c, part, group, shared) {
  return el("button", { class: "btn quiet small", type: "button", onclick: () => confirmStep(`Take back: ${group || part}`, [
    shared ? `This list is shared, so it goes back to not approved on every campaign that uses it.` : `${c.name} goes back to not approved for ${group || part}.`,
    c.status === "ENABLED" ? "The campaign keeps running until you pause it; the next Publish waits for your approval." : "Publish waits until you approve it again."],
  "Take back", () => act(c.nn, "unapprove", { part, group }, "Approval taken back")) }, "Take back");
}

function partRow(c, part, label, summary, extra) {
  const st = c.approvals[part];
  const when = c.approved_at && c.approved_at[part];
  return el("div", { class: "appr-row" },
    el("div", { class: "appr-head" },
      el("span", { class: "appr-label" }, label), tagFor(st),
      st === "approved" && when ? el("span", { class: "muted", style: "font-size:12px" }, fmtDateTime(when)) : null,
      el("span", { class: "grow" }),
      part === "negatives" ? null : st === "approved" ? takeBackBtn(c, part) : approveBtn(c, part)),
    summary, extra || null);
}

function spendRow(c) {
  const change = el("button", { class: "link", type: "button", onclick: () => {
    const input = el("div", { class: "field" }, el("label", { for: "amt" }, "Dollars a day"),
      el("input", { id: "amt", name: "amount", type: "number", min: "1", step: "1", value: String(c.daily_budget) }));
    confirmStep(`Budget for ${c.name}`, [
      `Now ${money(c.daily_budget)} a day. Running campaigns may not pass ${money(c.cap)} a day together ($3,000 a month).`,
      c.published ? "The new budget goes to Google at once." : "It goes to Google when you publish."],
    "Set budget", (f) => act(c.nn, "budget", { amount: Number(f.elements.amount.value) }, "Budget set"), { input });
  } }, "Change budget");
  return partRow(c, "spend", "Spend",
    el("div", { class: "body" }, `${money(c.daily_budget)} a day (${c.slot === "test" ? "the test slot" : "funded"}). `,
      `Maximize clicks, at most $${c.max_cpc} a click. Search only, no partners, no display. `,
      `${c.places} places, people in them only. English.`),
    el("div", {}, change));
}

// The keywords as one editor (Jonathan, 2026-10-01: "I should be able to delete and add keywords to the google ads
// campaigns as well"): X takes one out (it waits under "Taken out"), the box adds your own, Save changes sends the list
// once. The server refuses a keyword a negative blocks (it would never show) and asks before saving one that misses
// the buying-intent test (a trade and this campaign's service, no how, best, cost, or free words): Save anyway.
const kwDrafts = new Map(); // campaign nn -> the edited keyword list, until saved or discarded

function keywordsRow(c) {
  const saved = [...c.keywords];
  const st = kwDrafts.get(c.nn) || [...saved];
  const editor = el("div", { class: "stack" });
  const row = partRow(c, "keywords", `Keywords (${saved.length})`,
    el("div", { class: "muted", style: "font-size:12px" }, "Each goes in exactly as written and as a phrase with words around it. Take out, add, and put back as many as you like, then Save changes once. Saving asks for the keywords' approval again" + (c.published ? "; Publish changes sends them to Google." : ".")),
    editor);
  const approve = row.querySelector(".appr-head .btn:not(.quiet)");
  const label = row.querySelector(".appr-label");
  const norm = (s) => s.toLowerCase().replace(/\s+/g, " ").trim();
  let weak = null; // {keyword: [reasons]} from the server, when it asked before saving

  async function save(allowWeak, btn) {
    btn.disabled = true;
    try {
      const r = await api.post(`/api/ads/${c.nn}/kw_set`, { keywords: st, allow_weak: allowWeak });
      kwDrafts.delete(c.nn);
      toast((r.result && r.result.note) || "Saved.");
      rerender();
    } catch (err) {
      if (err.body && err.body.weak) { weak = err.body.weak; paint(); }
      else { toast(errText(err), true); btn.disabled = false; }
    }
  }

  function paint() {
    const dirty = JSON.stringify(st) !== JSON.stringify(saved);
    if (dirty) kwDrafts.set(c.nn, st); else kwDrafts.delete(c.nn);
    if (label) label.textContent = `Keywords (${st.length})`;
    if (approve) { approve.disabled = dirty; approve.title = dirty ? "Save or discard your changes first" : ""; }
    const chips = el("div", { class: "kw-chips" }, ...st.map((k, i) => el("span", { class: "kw-chip" + (saved.includes(k) ? "" : " new") + (weak && weak[k] ? " weak" : ""),
      title: weak && weak[k] ? weak[k].join("; ") : "" }, k,
      el("button", { class: "ad-x", type: "button", "aria-label": `Take out: ${k}`, title: "Take this keyword out",
        onclick: () => { st.splice(i, 1); weak = null; paint(); } }, "×"))));
    const bench = [...new Set([...(c.bench || []), ...saved])].filter((b) => !st.includes(b));
    const benchRow = bench.length ? el("div", { class: "ad-bench" }, el("span", { class: "muted" }, "Taken out:"),
      ...bench.map((b) => el("button", { class: "chip quiet", type: "button", title: "Put it back", onclick: () => { st.push(b); paint(); } }, `+ ${b}`))) : null;
    const input = el("input", { type: "text", maxlength: "80", placeholder: "Add a keyword: the trade and the service they'd hire", "aria-label": "New keyword" });
    const form = el("form", { class: "ad-add" }, input, el("button", { class: "btn quiet small", type: "submit" }, "Add keyword"));
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const k = norm(input.value);
      if (!k) return;
      if (st.includes(k)) { toast(`"${k}" is already a keyword.`, true); return; }
      st.push(k); weak = null; paint();
      const again = editor.querySelector('input[aria-label="New keyword"]');
      if (again) again.focus();
    });
    let bar = null;
    if (dirty) {
      const added = st.filter((k) => !saved.includes(k)).length;
      const removed = saved.filter((k) => !st.includes(k)).length;
      const saveBtn = el("button", { class: "btn small", type: "button", disabled: st.length ? null : true }, "Save changes");
      saveBtn.addEventListener("click", () => save(false, saveBtn));
      const anyway = weak ? el("button", { class: "btn small", type: "button" }, "Save anyway") : null;
      if (anyway) anyway.addEventListener("click", () => save(true, anyway));
      bar = el("div", { class: "ad-savebar" },
        el("div", { class: "grow" }, el("div", { class: "strong" }, `Unsaved: ${[added ? `${added} added` : "", removed ? `${removed} taken out` : ""].filter(Boolean).join(", ") || "order changed"}`),
          weak ? el("div", { class: "down", style: "font-size:12px" }, "These miss the buying-intent test: " + Object.entries(weak).map(([k, v]) => `"${k}" (${v.join(", ")})`).join("; ") + ". Save anyway if you want them.")
            : el("div", { class: "muted", style: "font-size:12px" }, st.length ? "Nothing reaches Google until you approve the keywords and publish." : "A campaign needs at least one keyword.")),
        el("button", { class: "btn quiet small", type: "button", onclick: () => { kwDrafts.delete(c.nn); st.splice(0, st.length, ...saved); weak = null; paint(); } }, "Discard"),
        weak ? anyway : saveBtn);
    }
    editor.replaceChildren(...[chips, benchRow, form, bar].filter(Boolean));
  }
  paint();
  return row;
}

function negativesRow(c) {
  const total = c.groups.reduce((a, g) => a + g.count, 0);
  const openCount = c.groups.filter((g) => g.state !== "approved").length;
  const rows = el("div", { class: "neg-list" }, ...c.groups.map((g) => el("div", { class: "neg-row" },
    el("div", { class: "grow" },
      el("div", {}, el("span", { class: "strong" }, g.name), el("span", { class: "muted" }, ` · ${g.count} · ${g.scope === "shared" ? "every campaign" : "this campaign"}`)),
      el("div", { class: "muted", style: "font-size:12px" }, g.examples.join(" · "))),
    tagFor(g.state),
    el("button", { class: "btn quiet small", type: "button", onclick: () => readList(c, g) }, "Read"),
    g.state !== "approved" ? approveBtn(c, "negatives", g.name) : takeBackBtn(c, "negatives", g.name, g.scope === "shared"))));
  const all = openCount > 1 ? el("button", { class: "btn quiet small", type: "button", onclick: async (e) => {
    e.target.disabled = true;
    try { await act(c.nn, "approve", { part: "negatives" }, "All lists approved"); } catch (err) { toast((err.errors || [String(err)]).join(" "), true); e.target.disabled = false; }
  } }, `Approve all ${openCount}`) : null;
  const block = el("button", { class: "link", type: "button", onclick: () => blockDialog(c) }, "Block a search");
  return partRow(c, "negatives", `Negatives (${c.groups.length} lists, ${total} words)`,
    el("div", { class: "muted", style: "font-size:12px" }, "Searches the ad must never show on. Shared lists are approved once for every campaign. None of them may block a keyword; the server checks."),
    el("div", { class: "stack" }, rows, el("div", { class: "row" }, all, block)));
}

function readList(c, g) {
  openModal(el("div", { class: "stack" },
    el("h2", {}, g.name),
    el("div", { class: "muted" }, `${g.count} words · ${g.scope === "shared" ? "shared by every campaign it applies to" : "this campaign only"}. Plain = every word, any order; "quoted" = side by side; [bracketed] = that exact search.`),
    el("pre", { class: "neg-words" }, g.terms.join("\n")),
    el("div", { class: "actions" }, g.state !== "approved" ? approveBtn(c, "negatives", g.name) : el("span", { class: "tag won" }, "Approved"))), { wide: true });
}

function blockDialog(c, preset = "", lists = []) {
  const term = el("input", { name: "term", value: preset, placeholder: "the search words" });
  const kind = el("select", { name: "kind" }, el("option", { value: "phrase" }, "Side by side (phrase)"), el("option", { value: "exact" }, "Only that exact search"), el("option", { value: "broad" }, "Every word, any order"));
  const where = el("select", { name: "shared" }, el("option", { value: "" }, "This campaign only"), ...lists.map((n) => el("option", { value: n }, `Shared: ${n}`)));
  const input = el("div", { class: "fields" }, el("div", { class: "field" }, el("label", {}, "Search"), term), el("div", { class: "field" }, el("label", {}, "How"), kind), el("div", { class: "field" }, el("label", {}, "List"), where));
  confirmStep(`Block a search on ${c.name}`, [
    "Refused if it would block one of the keywords.",
    c.published ? "It goes to Google at once." : "It goes to Google when you publish."],
  "Block it", (f) => {
    const w = f.elements.term.value.trim().toLowerCase();
    const k = f.elements.kind.value;
    const raw = k === "phrase" ? `"${w}"` : k === "exact" ? `[${w}]` : w;
    return act(c.nn, "negative", { term: raw, shared: f.elements.shared.value }, "Blocked");
  }, { input });
}

// The ad's lines as one editor (Jonathan, 2026-09-29: "delete and move as many headlines and create as many new ones as
// I want, up to 15, and then save changes instead of having to do them one by one"). Every change stays on this screen
// until Save changes: X takes a line out (it waits under "Taken out" and can be put back), the slot badge cycles
// any slot, 1, 2, 3, a line is dragged to a new place, and the boxes add new ones. Save sends the whole set once; the
// server checks it all (3 to 15 headlines, 2 to 4 descriptions, the lengths, the copy rules). Unsaved edits survive a
// redraw of the page, and Approve waits until they are saved or discarded.
const WORD = { headlines: "headline", descriptions: "description" };
const LIMITS = { headlines: { min: 3, max: 15, chars: 30 }, descriptions: { min: 2, max: 4, chars: 90 } };
const lineText = (line) => (typeof line === "string" ? line : line.text);
const adDrafts = new Map(); // campaign nn -> the edited {headlines, descriptions}, until saved or discarded
const adEdits = new Map(); // campaign nn -> how many lines had their words changed in place (2026-10-02), for the save bar

function savedAd(c) {
  return { headlines: c.ad.headlines.map((h) => ({ text: h.text, ...(h.pin ? { pin: h.pin } : {}) })), descriptions: [...c.ad.descriptions] };
}

function adRow(c) {
  const lim = c.ad_limits || LIMITS;
  const saved = savedAd(c);
  const st = adDrafts.get(c.nn) || JSON.parse(JSON.stringify(saved));
  const editor = el("div", { class: "stack ad-editor" });
  const row = partRow(c, "ad", "The ad",
    el("div", { class: "muted", style: "font-size:12px" }, `Google shows three headlines at a time; a "slot" one always sits in that place. Lands on ${c.page}. Click any line to change its words; take out, add, re-slot, and drag as many as you like, then Save changes once. Saving asks for the ad's approval again.`),
    editor);
  const approve = row.querySelector(".appr-head .btn:not(.quiet)");
  let drag = null;

  const low = (s) => s.toLowerCase();
  const changed = () => JSON.stringify(st) !== JSON.stringify(saved);
  const inAd = (text) => [...st.headlines.map((h) => h.text), ...st.descriptions].some((t) => low(t) === low(text));

  function problems() {
    const out = [];
    for (const kind of ["headlines", "descriptions"]) {
      const n = st[kind].length, L = lim[kind];
      if (n < L.min) out.push(`Add ${L.min - n} more ${n === L.min - 1 ? WORD[kind] : kind}: an ad takes at least ${L.min}.`);
      for (const t of st[kind].map(lineText)) if (t.length > L.chars) out.push(`"${t}" is ${t.length} characters; the most is ${L.chars}.`);
    }
    return out;
  }

  function summary() {
    const before = new Set([...saved.headlines.map((h) => low(h.text)), ...saved.descriptions.map(low)]);
    const after = new Set([...st.headlines.map((h) => low(h.text)), ...st.descriptions.map(low)]);
    const added = [...after].filter((t) => !before.has(t)).length;
    const removed = [...before].filter((t) => !after.has(t)).length;
    // an edit in place shows up as one line out and one in; count it as edited instead
    const edited = Math.min(adEdits.get(c.nn) || 0, added, removed);
    const parts = [];
    if (edited) parts.push(`${edited} edited`);
    if (added - edited) parts.push(`${added - edited} added`);
    if (removed - edited) parts.push(`${removed - edited} taken out`);
    if (!added && !removed) parts.push("moved or re-slotted");
    else if (JSON.stringify(st.headlines.filter((h) => before.has(low(h.text)))) !== JSON.stringify(saved.headlines.filter((h) => after.has(low(h.text))))) parts.push("moved or re-slotted");
    return parts.join(", ");
  }

  function item(kind, i) {
    const line = st[kind][i];
    const text = lineText(line);
    const over = text.length > lim[kind].chars;
    const x = el("button", { class: "ad-x", type: "button", title: `Take this ${WORD[kind]} out`, "aria-label": `Take out: ${text}`,
      onclick: (e) => { e.stopPropagation(); st[kind].splice(i, 1); paint(); } }, "×");
    const slot = kind === "headlines" ? el("button", { class: "slot" + (line.pin ? " on" : ""), type: "button",
      title: "Where Google shows it: click to cycle any slot, slot 1, 2, 3", "aria-label": line.pin ? `Slot ${line.pin}, change` : "Any slot, change",
      onclick: (e) => { e.stopPropagation(); const next = ((line.pin || 0) + 1) % 4; if (next) line.pin = next; else delete line.pin; paint(); } }, line.pin ? `slot ${line.pin}` : "any") : null;
    // the words, edited in place (Jonathan, 2026-10-02: "I should be able to edit my descriptions as well"): a click turns
    // the line into a box; Enter or clicking away keeps the change, Escape drops it. The old wording goes to "Taken out"
    // when the set is saved, so it can be put back.
    const words = el("span", { class: "ad-t", tabindex: "0", role: "button", title: `Click to edit this ${WORD[kind]}` }, text);
    const len = el("span", { class: "len" + (over ? " down" : "") }, String(text.length));
    function edit(e) {
      if (e) e.stopPropagation();
      node.draggable = false;
      const box = el("input", { class: "ad-edit", type: "text", value: text, "aria-label": `Edit ${WORD[kind]}` });
      box.style.width = `${Math.max(12, Math.min(text.length + 4, kind === "headlines" ? 34 : 96))}ch`;
      let done = false;
      const count = () => { const n = box.value.length; len.textContent = String(n); len.classList.toggle("down", n > lim[kind].chars); };
      function finish(keep) {
        if (done) return;
        const next = box.value.replace(/\s+/g, " ").trim();
        if (keep && next && next !== text) {
          const clash = [...st.headlines.map((h) => h.text), ...st.descriptions].some((t, j) => low(t) === low(next) && t !== text);
          if (clash) { toast(`"${next}" is already in the ad.`, true); box.focus(); return; }
          done = true;
          if (kind === "headlines") st.headlines[i] = { ...line, text: next };
          else st.descriptions[i] = next;
          adEdits.set(c.nn, (adEdits.get(c.nn) || 0) + 1);
        }
        done = true;
        paint();
      }
      box.addEventListener("input", count);
      box.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter") { ev.preventDefault(); finish(true); }
        if (ev.key === "Escape") { ev.preventDefault(); ev.stopPropagation(); finish(false); }
      });
      box.addEventListener("blur", () => finish(true));
      box.addEventListener("click", (ev) => ev.stopPropagation());
      words.replaceWith(box);
      box.focus();
      box.setSelectionRange(text.length, text.length);
    }
    words.addEventListener("click", edit);
    words.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); edit(e); } });
    const node = el("span", { class: (kind === "headlines" ? "ad-h" : "ad-d") + (line.pin ? " pinned" : "") + (over ? " over" : ""), draggable: "true", title: "Drag to move" },
      el("span", { class: "grip", "aria-hidden": "true" }, "⠿"), slot, words, len, x);
    node.addEventListener("dragstart", (e) => { drag = { kind, i }; e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", text); node.classList.add("dragging"); });
    node.addEventListener("dragend", () => { drag = null; node.classList.remove("dragging"); });
    node.addEventListener("dragover", (e) => { if (drag && drag.kind === kind && drag.i !== i) { e.preventDefault(); node.classList.add("drop"); } });
    node.addEventListener("dragleave", () => node.classList.remove("drop"));
    node.addEventListener("drop", (e) => {
      e.preventDefault();
      if (!drag || drag.kind !== kind) return;
      const [moved] = st[kind].splice(drag.i, 1);
      st[kind].splice(i, 0, moved);
      drag = null;
      paint();
    });
    return node;
  }

  function bench(kind) {
    // lines taken out: the ones saved before, and the ones taken out on this screen
    const pool = [...((c.ad_bench || {})[kind] || []), ...saved[kind]];
    const seen = new Set();
    const out = pool.filter((l) => { const k = low(lineText(l)); if (seen.has(k) || inAd(lineText(l))) return false; seen.add(k); return true; });
    if (!out.length) return null;
    const full = st[kind].length >= lim[kind].max;
    return el("div", { class: "ad-bench" }, el("span", { class: "muted" }, "Taken out:"), ...out.map((l) => el("button", {
      class: "chip quiet", type: "button", title: full ? "The ad is full; take one out first" : "Put it back", disabled: full ? true : null,
      onclick: () => { st[kind].push(kind === "headlines" ? { text: lineText(l), ...(l.pin ? { pin: l.pin } : {}) } : lineText(l)); paint(); } }, `+ ${lineText(l)}`)));
  }

  function adder(kind) {
    const L = lim[kind];
    const full = st[kind].length >= L.max;
    const input = el("input", { type: "text", maxlength: String(L.chars), disabled: full ? true : null, "aria-label": `New ${WORD[kind]}`,
      placeholder: full ? `${L.max} ${kind}, the most Google takes: take one out to add another` : `Your ${WORD[kind]}, up to ${L.chars} characters` });
    const count = el("span", { class: "muted num ad-count" }, `0/${L.chars}`);
    input.addEventListener("input", () => { count.textContent = `${input.value.length}/${L.chars}`; });
    const pin = kind === "headlines" ? el("select", { "aria-label": "Where it shows", disabled: full ? true : null },
      el("option", { value: "" }, "Any slot"), ...[1, 2, 3].map((s) => el("option", { value: String(s) }, `Always slot ${s}`))) : null;
    const form = el("form", { class: "ad-add" }, input, count, pin, el("button", { class: "btn quiet small", type: "submit", disabled: full ? true : null }, `Add ${WORD[kind]}`));
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const text = input.value.replace(/\s+/g, " ").trim();
      if (!text) return;
      if (inAd(text)) { toast(`"${text}" is already in the ad.`, true); return; }
      st[kind].push(kind === "headlines" ? { text, ...(pin && pin.value ? { pin: Number(pin.value) } : {}) } : text);
      paint();
      const again = editor.querySelector(`input[aria-label="New ${WORD[kind]}"]`);
      if (again && !again.disabled) again.focus();
    });
    return form;
  }

  function paint() {
    const dirty = changed();
    if (dirty) adDrafts.set(c.nn, st); else adDrafts.delete(c.nn);
    const probs = problems();
    if (approve) {
      approve.disabled = dirty;
      approve.title = dirty ? "Save or discard your changes first" : "";
    }
    const save = el("button", { class: "btn small", type: "button", disabled: probs.length ? true : null }, "Save changes");
    save.addEventListener("click", async () => {
      save.disabled = true;
      try {
        const r = await api.post(`/api/ads/${c.nn}/ad_set`, { headlines: st.headlines, descriptions: st.descriptions });
        adDrafts.delete(c.nn);
        adEdits.delete(c.nn);
        toast((r.result && r.result.note) || "Saved.");
        rerender();
      } catch (err) { toast(errText(err), true); save.disabled = false; }
    });
    const discard = el("button", { class: "btn quiet small", type: "button", onclick: () => { adDrafts.delete(c.nn); adEdits.delete(c.nn); st.headlines = JSON.parse(JSON.stringify(saved.headlines)); st.descriptions = [...saved.descriptions]; paint(); } }, "Discard");
    editor.replaceChildren(...[
      el("div", { class: "ad-url" }, `monarcbuild.com/${c.ad.path1 || ""}${c.ad.path2 ? "/" + c.ad.path2 : ""}`),
      el("div", { class: "label" }, `Headlines: ${st.headlines.length} of ${lim.headlines.max}`),
      el("div", { class: "ad-heads" }, ...st.headlines.map((_, i) => item("headlines", i))),
      bench("headlines"), adder("headlines"),
      el("div", { class: "label" }, `Descriptions: ${st.descriptions.length} of ${lim.descriptions.max}`),
      el("div", { class: "stack", style: "gap:4px" }, ...st.descriptions.map((_, i) => item("descriptions", i))),
      bench("descriptions"), adder("descriptions"),
      !dirty && c.ad_problems.length ? el("div", { class: "errors" }, ...c.ad_problems.map((p) => el("div", {}, p))) : null,
      dirty ? el("div", { class: "ad-savebar" },
        el("div", { class: "grow" }, el("div", { class: "strong" }, `Unsaved: ${summary()}`),
          probs.length ? el("div", { class: "down", style: "font-size:12px" }, probs.join(" ")) : el("div", { class: "muted", style: "font-size:12px" }, "Nothing reaches Google until you approve the ad and publish.")),
        discard, save) : null,
    ].filter(Boolean));
  }
  paint();
  return row;
}

function actions(c) {
  const why = [];
  if (!c.ready) why.push("approve all four first");
  const pubLabel = c.published ? (c.waiting.length ? "Publish changes" : "Published") : "Publish (paused)";
  const pub = el("button", { class: "btn", type: "button", disabled: !c.ready || (c.published && !c.waiting.length) ? true : null, onclick: () => {
    confirmStep(`Publish ${c.name}`, [
      c.published ? `Sends what changed since the last publish: ${c.waiting.join(", ")}.` : "Builds the campaign in Google Ads, turned off: the budget, the places, the keywords, the negative lists, and the ad.",
      "Google checks every step first and nothing is built if it refuses. No money moves until you press Go live."],
    "Publish", () => act(c.nn, "publish", {}, "Published: built and paused"));
  } }, pubLabel);
  const liveWhy = [];
  if (!c.published) liveWhy.push("publish first");
  if (c.waiting.length && c.published) liveWhy.push("publish the changes");
  if (!c.gates_ok) liveWhy.push("finish the gates");
  if (c.cap_note && c.status !== "ENABLED") liveWhy.push(c.cap_note);
  const live = c.status === "ENABLED"
    ? el("button", { class: "btn quiet", type: "button", onclick: () => confirmStep(`Pause ${c.name}`, ["The ads stop showing at once. Nothing is deleted."], "Pause", () => act(c.nn, "pause", {}, "Paused")) }, "Pause")
    : el("button", { class: "btn go", type: "button", disabled: liveWhy.length ? true : null, onclick: () => confirmStep(`Go live: ${c.name}`, [
      `Spending starts: up to ${money(c.daily_budget)} a day, at most $${c.max_cpc} a click.`,
      `Running after this: ${money(c.running_total + c.daily_budget)} of ${money(c.cap)} a day.`],
    "Go live", () => act(c.nn, "golive", {}, "Live"), { danger: true }) }, "Go live");
  return el("div", { class: "ads-actions" },
    el("div", { class: "muted grow", style: "font-size:12px" }, c.status === "ENABLED" ? `Live. Published ${fmtDateTime(c.published_at)}.` : [...why, ...liveWhy].length ? "To go live: " + [...why, ...liveWhy].join("; ") + "." : "Ready to go live."),
    pub, live);
}

// One campaign's controls, opened from its Advertising card on the Google Ads channel page: the ad first (headlines and
// descriptions, each with an X, and the add boxes), then the keywords, the negatives, the spend, and Publish and Go live.
// Every approval can be taken back.
export function adsControls(c) {
  return el("div", { class: "ads-body in-camp" },
    el("div", { class: "appr-head" }, el("span", { class: "appr-label" }, "Approve and edit"), statusTag(c),
      ...PARTS.map(([p, lb]) => el("span", { class: "dot " + c.approvals[p], title: `${lb}: ${STATE_WORD[c.approvals[p]]}` })),
      el("span", { class: "muted", style: "font-size:12px" }, `${money(c.daily_budget)}/day · ${c.slot === "test" ? "test slot" : "funded"}`)),
    adRow(c), keywordsRow(c), negativesRow(c), spendRow(c), actions(c));
}

function gatesPanel(data) {
  // the h1 gate is per page: done when every page names its service; the note lists each page
  const h1s = data.cards.map((c) => ({ nn: c.nn, g: c.gates.find((x) => x.key === "h1") || {} }));
  const gates = ((data.cards[0] || {}).gates || []).map((g) => g.key !== "h1" ? g : { ...g,
    ok: h1s.every((x) => x.g.ok),
    note: h1s.map((x) => `${x.nn} ${x.g.ok ? "yes" : x.g.note && x.g.note.startsWith("h1:") ? "no" : "not read"}`).join(" · ") });
  const done = gates.filter((g) => g.ok).length;
  const rows = gates.map((g) => el("div", { class: "gate-row" },
    el("span", { class: "tag " + (g.ok ? "won" : "faint") }, g.ok ? "Done" : "Open"),
    el("div", { class: "grow" }, el("div", {}, g.name), el("div", { class: "muted", style: "font-size:12px" }, g.note)),
    !g.ok && g.fixable && data.connected ? el("button", { class: "btn quiet small", type: "button", onclick: () => confirmStep(`Fix: ${g.name}`, [
      g.key === "clicks" ? "Turns on auto-tagging and sets the final URL suffix in account.md, so every ad click carries its campaign and keyword into the CRM." : 'Makes "Submit lead form (6)" the one main conversion; every other action becomes secondary.',
      "Then reads it back from Google and ticks the tracking checklist."], "Fix it", () => api.post("/api/ads/gates/fix", { gate: g.key }).then(() => { toast("Fixed"); window.dispatchEvent(new HashChangeEvent("hashchange")); })) }, "Fix") : null,
    !g.ok && g.tickable ? el("button", { class: "btn quiet small", type: "button", onclick: () => confirmStep("Billing is fixed", ["You confirm the declined payment is sorted and the account is not suspended. This ticks item 1 of the tracking checklist."], "Yes, it's fixed", () => api.post("/api/ads/gates/tick", { gate: "billing" }).then(() => window.dispatchEvent(new HashChangeEvent("hashchange")))) }, "It's fixed") : null));
  const check = el("button", { class: "btn quiet small", type: "button", onclick: async (e) => {
    e.target.disabled = true;
    try { await api.post("/api/ads/gates/refresh", {}); toast("Gates read again"); window.dispatchEvent(new HashChangeEvent("hashchange")); }
    catch (err) { toast((err.errors || [String(err)]).join(" "), true); e.target.disabled = false; }
  } }, "Check again");
  return el("div", { class: "panel" },
    el("div", { class: "row" }, el("h2", { class: "grow" }, `Before any campaign goes live: ${done} of ${gates.length} done`), check),
    el("div", { class: "muted", style: "font-size:12px" }, data.gates_read_at ? `Last read ${fmtDateTime(data.gates_read_at)}.` : "Not read yet: press Check again."),
    ...rows);
}

function termsPanel(data) {
  if (!data.search_terms.length) return null;
  const card = new Map(data.cards.map((c) => [c.nn, c]));
  return el("div", { class: "panel" },
    el("h2", {}, "What people searched (last 7 days)"),
    el("div", { class: "muted", style: "font-size:12px" }, `From ${data.search_terms_file}. Block any that cost money and were not buyers.`),
    el("div", { class: "table-wrap" }, el("table", {},
      el("thead", {}, el("tr", {}, el("th", {}, "Search"), el("th", {}, "Campaign"), el("th", { class: "num" }, "Clicks"), el("th", { class: "num" }, "Cost"), el("th", { class: "num" }, "Booked"), el("th", {}, ""))),
      el("tbody", {}, ...data.search_terms.slice(0, 60).map((t) => el("tr", {},
        el("td", {}, t.term), el("td", {}, (card.get(t.nn) || {}).name || t.nn), el("td", { class: "num" }, String(t.clicks)),
        el("td", { class: "num" }, money(t.cost)), el("td", { class: "num" + (t.conversions ? " up" : "") }, String(t.conversions || 0)),
        el("td", {}, card.get(t.nn) && !t.conversions ? el("button", { class: "btn quiet small", type: "button", onclick: () => blockDialog(card.get(t.nn), t.term, data.shared_lists) }, "Block") : null)))))));
}

// Recent changes, folded away until clicked (2026-10-02)
export function logPanel(data) {
  if (!data.log.length) return null;
  return fold({ key: "ads-log", label: "Log", title: "Recent changes", count: data.log.length,
    body: data.log.map((r) => el("div", { class: "log-row" }, el("span", { class: "muted num" }, fmtDateTime(r.at)), el("span", {}, `${r.nn !== "--" ? r.nn + " " : ""}${r.action}`), el("span", { class: "muted" }, r.detail || ""))) });
}

// The old Ads screen (#/ads) now opens the Google Ads channel page, where these parts live (2026-09-29).
export function renderAds() {
  location.replace("#/channel/google-ads");
}

// The top of the Google Ads channel page: what is running against the cap, Pull numbers, the five gates, and
// the search terms to block. Returns a list of nodes (nulls skipped by el).
export function adsTop(data) {
  const live = data.cards.filter((c) => c.status === "ENABLED");
  const approved = data.cards.filter((c) => c.ready).length;
  const strip = el("div", { class: "kpis" },
    el("div", { class: "kpi" }, el("div", { class: "label" }, "Running"), el("div", { class: "fig num" }, money(data.running_total), el("small", {}, ` of ${money(data.cap)}/day`)),
      el("div", { class: "gauge" + (data.running_total > data.cap ? " warn" : "") }, el("b", { style: `width:${Math.min(100, (100 * data.running_total) / data.cap)}%` }))),
    el("div", { class: "kpi" }, el("div", { class: "label" }, "Live"), el("div", { class: "fig num" }, String(live.length), el("small", {}, ` of ${data.cards.length}`)), el("div", { class: "muted", style: "font-size:12px" }, live.map((c) => c.nn).join(", ") || "none yet")),
    el("div", { class: "kpi" }, el("div", { class: "label" }, "Fully approved"), el("div", { class: "fig num" }, String(approved), el("small", {}, ` of ${data.cards.length}`))),
    el("div", { class: "kpi" }, el("div", { class: "label" }, "Google Ads"), el("div", { class: "fig", style: "font-size:20px;line-height:40px" }, data.connected ? "Connected" : "Not connected"),
      el("div", { class: "muted", style: "font-size:12px" }, data.connected ? "Publishing works." : "You can approve now; Publish needs the login (references/google-ads-api.md).")));
  const anyPublished = data.cards.some((c) => c.published);
  const pull = data.connected && anyPublished ? el("div", { class: "stack", style: "gap:4px;justify-items:end" },
    el("button", { class: "btn quiet small", type: "button", onclick: async (e) => {
      e.target.disabled = true;
      try { const r = await api.post("/api/ads/pull/run", {}); toast(`Pulled: ${r.result.campaigns} campaigns, ${r.result.search_terms} searches to read`); window.dispatchEvent(new HashChangeEvent("hashchange")); }
      catch (err) { toast((err.errors || [String(err)]).join(" "), true); e.target.disabled = false; }
    } }, "Pull numbers now"),
    el("div", { class: "muted", style: "font-size:12px" }, data.last_pull ? `Last pulled ${fmtDateTime(data.last_pull)}; every morning after 6 am.` : "Pulls every morning after 6 am.")) : null;
  return [
    el("div", { class: "row" }, el("div", { class: "grow" }, el("div", { class: "label" }, "Publishing"),
      el("h2", {}, "Approve each campaign, then publish"),
      el("div", { class: "muted", style: "font-size:13px" }, "Open a campaign below to approve, take back, or edit its spend, keywords, negatives, and ad. Campaigns land paused; Go live is a second step, locked until the gates are done.")), pull),
    strip, gatesPanel(data), termsPanel(data)];
}
