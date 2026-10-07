// The Captions tab (G18-G21; voices 2026-09-30, grill C1-C13): the look (on/off, UPPERCASE, size, height, outline),
// the palette every short uses (you, your spoken word, women, men, their spoken word), the voices heard in this short,
// and the words line by line in their voice's color. The playing word lights up; click a word to jump there (Shift+
// click selects a run); double-click to fix its spelling; right-click to say who said it. On an older short, spelling
// and voice fixes are saved on the recording, so every short cut from it gets them.
// Generate captions (2026-10-02, grill G1-G7): a new short has none until he presses Generate captions, here, in the
// Clip menu or at export. Once generated, word fixes (spelling, who said it) are saved on this short (G7); a whole
// voice's fixes still go on the recording.
import { S, subscribe, emit } from "../store.js";
import { el, clear, icon } from "../util.js";
import { api } from "../api.js";
import { lib } from "../media/library.js";
import { numField } from "../components/numfield.js";
import { toast } from "../components/modal.js";
import { openMenu } from "../components/menu.js";
import * as history from "../history.js";
import { flush } from "../save.js";
import { pb } from "../playback.js";
import { run as runAction } from "../actions.js";
import { colorsFor, DEFAULT_PALETTE, eventVoice, genMode, genStatus, speechClips } from "../model/captions.js";

const PALETTE_ROWS = [["you", "You", "Your words"], ["youWord", "Your word", "The word you are saying"], ["woman", "Women", "Women's words"],
  ["man", "Men", "Men's words"], ["themWord", "Their word", "The word a woman or man is saying"]];
const GENDER = { woman: "woman", man: "man" };
const SOURCE = { you: "you set this", claude: "from Claude", auto: "guessed from the voice" };
let host, genBox, controls, voicesBox, words, spans = [], lastActive = null;
let sel = new Set(), anchor = null;        // selected words as keyOf(word)

// a caption word's key: "asset:id" from the transcript, "asset:g<n>" for a generated word
const isGen = (w) => w.gi !== undefined && w.gi !== null;
const keyOf = (w) => w.asset + ":" + (isGen(w) ? "g" + w.gi : w.id);
function genWord(w, doc = S.doc) {
  const g = isGen(w) && doc && doc.captions.gen && doc.captions.gen[w.asset];
  return g ? g.words[w.gi] || null : null;
}

export function mountCaptions(h) {
  host = h;
  clear(host);
  genBox = el("div", { class: "cap-gen" });
  controls = el("div", { class: "cap-controls" });
  voicesBox = el("div", { class: "cap-voices" });
  words = el("div", { class: "cap-words" });
  host.append(genBox, controls, voicesBox, words);
  subscribe("doc", () => { if (!busy()) render(); });
  subscribe("transcript", () => { if (!busy()) render(); });
  subscribe("config", () => { if (!busy()) render(); });
  subscribe("gencaps", renderGen);
  subscribe("bin", () => { if (voicesBox.querySelector(".voice-note.is-live")) renderVoices(); });
  subscribe("playhead", highlight);
  subscribe("focusCaptions", () => { render(); const a = words.querySelector(".is-active"); if (a) a.scrollIntoView({ block: "center" }); });
  render();
}

// ---------------------------------------------------------------- Generate captions

function fmtAt(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return "";
  const today = new Date().toDateString() === d.toDateString();
  return (today ? "today" : d.toLocaleDateString("en-US", { month: "short", day: "numeric" })) + " at " + d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
}

function genButton(label, quiet) {
  return el("button", { class: "btn small gen-btn" + (quiet ? " quiet" : ""), type: "button", onclick: () => runAction("generateCaptions") }, icon("auto_awesome"), label);
}

function renderGen() {
  if (!genBox) return;
  clear(genBox);
  if (!S.doc) return;
  const job = S.genCaps && S.genCaps.pid === S.doc.id ? S.genCaps : null;
  if (job && job.state === "running") {
    const pct = job.progress > 0 && job.progress < 1 ? ` ${Math.round(job.progress * 100)} %` : "…";
    genBox.append(el("div", { class: "gen-row is-busy" }, el("span", { class: "gen-spin", "aria-hidden": "true" }),
      el("span", { class: "small grow" }, (job.msg || "Working") + pct)));
    return;
  }
  if (!speechClips(S.doc).length) return;
  const st = genStatus(S.doc);
  const gen = S.doc.captions.gen || {};
  if (st === null) {
    genBox.append(el("div", { class: "gen-row" }, el("span", { class: "small muted grow" }, "These captions come straight from the first transcript."),
      genButton("Generate captions", true)));
  } else if (st === "none") {
    genBox.append(el("div", { class: "gen-empty" },
      el("div", { class: "strong" }, "No captions yet"),
      el("div", { class: "small muted" }, "Trim the short to its best parts, then make them. It listens again to just what you kept; where the two listens differ, Claude picks the reading that makes sense. About 1 to 2 cents."),
      genButton("Generate captions", false)));
  } else if (st === "part") {
    genBox.append(el("div", { class: "gen-row is-warn" }, icon("warning"),
      el("span", { class: "small grow" }, "Some footage was added after the captions were made and has none yet."), genButton("Generate again", false)));
  } else {
    const at = Object.values(gen).map((g) => g.at).filter(Boolean).sort().pop();
    genBox.append(el("div", { class: "gen-row" }, el("span", { class: "small muted grow" }, `Captions made ${fmtAt(at)}.`), genButton("Generate again", true)));
  }
  const note = st !== "none" && Object.values(gen).map((g) => g.note).find(Boolean);
  if (note) genBox.append(el("div", { class: "small muted gen-note" }, note));
  if (job && job.state === "error") genBox.append(el("div", { class: "small bad gen-note" }, "Couldn't make the captions: " + job.error));
}

function busy() { const a = document.activeElement; return !!(a && host.contains(a) && (a.isContentEditable || a.tagName === "INPUT")) || !!host.querySelector(".num-field.is-drag"); }

function set(label, fn, key) { history.commit(label, (d) => { fn(d.captions); }, { key }); }

function palette() { return Object.assign({}, DEFAULT_PALETTE, (S.config && S.config.captionColors) || {}); }

export function render() {
  if (!controls) return;
  clear(controls); clear(words);
  spans = []; lastActive = null;
  renderGen();
  renderPalette();
  if (!S.doc) { clear(voicesBox); words.append(el("div", { class: "empty" }, "Open a short to see its captions.")); return; }
  const cfg = S.doc.captions;
  controls.prepend(
    el("div", { class: "row" },
      el("label", { class: "switch" }, el("input", { type: "checkbox", checked: cfg.on || null, onchange: (e) => set("Captions on/off", (c) => { c.on = e.target.checked; }) }), el("span", {}, "Show captions")),
      el("label", { class: "switch" }, el("input", { type: "checkbox", checked: cfg.upper || null, onchange: (e) => set("Uppercase", (c) => { c.upper = e.target.checked; }) }), el("span", {}, "UPPERCASE"))));
  controls.append(
    el("div", { class: "row" },
      el("span", { class: "fx-label" }, "Size"), numField({ value: cfg.size, step: 1, digits: 0, min: 30, max: 200, onChange: (v, fin) => set("Caption Size", (c) => { c.size = Math.round(v); }, fin ? null : "csize") }),
      el("span", { class: "fx-label" }, "Height"), numField({ value: cfg.y, step: 2, digits: 0, min: 100, max: 1820, onChange: (v, fin) => set("Caption Height", (c) => { c.y = Math.round(v); }, fin ? null : "cy") }),
      el("span", { class: "fx-label" }, "Outline"), numField({ value: cfg.bord, step: 0.5, digits: 1, min: 0, max: 20, onChange: (v, fin) => set("Caption Outline", (c) => { c.bord = v; }, fin ? null : "cb") })));
  renderVoices();
  const evs = cfg.events || [];
  if (!evs.length) {
    const a1 = S.doc.clips.filter((c) => (c.track === "A1" || c.voice) && c.type === "audio");
    if (a1.length && genStatus(S.doc) === "none") return;      // the Generate box above says it
    const why = !a1.length ? "Captions come from the words under A1 and the voice tracks. Put a clip with speech there." :
      a1.every((c) => !(lib.asset(c.asset) || {}).transcript) ? "The transcript isn't ready yet. It appears in the bin as the recording is prepared." : "No words under the speech clips.";
    words.append(el("div", { class: "empty" }, why));
    return;
  }
  const pal = palette();
  const onShort = genMode(S.doc);
  for (const ev of evs) {
    const line = el("div", { class: "cap-line" }, el("span", { class: "cap-time num muted" }, fmt(ev.s)));
    for (const w of ev.words) {
      const idx = spans.length;
      const key = keyOf(w);
      const s = el("span", { class: "cap-word" + (sel.has(key) ? " is-sel" : ""), title: "Click to jump, Shift+click to select, double-click to fix, right-click to say who said it"
        + (onShort ? " (fixes are saved on this short)" : ""),
        style: { color: colorsFor(w.k, pal)[0] }, dataset: { k: w.k || "u" },
        onclick: (e) => clickWord(e, idx), ondblclick: (e) => editWord(e.currentTarget, w),
        oncontextmenu: (e) => { e.preventDefault(); wordMenu(e, idx); } }, w.w);
      s._w = w;
      spans.push(s);
      line.append(s, " ");
    }
    words.append(line);
  }
  highlight();
}

// ---------------------------------------------------------------- the palette (every short)

function renderPalette() {
  const pal = palette();
  const box = el("div", { class: "cap-colors" },
    el("div", { class: "row" }, el("span", { class: "fx-label wide" }, "Colors · every short"), el("span", { class: "grow" }),
      el("button", { class: "link small", type: "button", title: "Back to blue, white, pink, red and yellow", onclick: resetColors }, "Reset colors")));
  const grid = el("div", { class: "cap-color-grid" });
  for (const [k, label, long] of PALETTE_ROWS) {
    const input = el("input", { type: "color", value: pal[k].toLowerCase(), class: "fx-color", title: `${long}: ${pal[k]}. Changes every short.`, dataset: { key: k } });
    let picked = false;       // an "input" not yet saved by "change" (closing the picker with Esc skips "change")
    input.addEventListener("input", () => { picked = true; liveColor(k, input.value.toUpperCase()); });
    input.addEventListener("change", () => { picked = false; saveColor(k, input.value.toUpperCase()); });
    input.addEventListener("blur", () => { if (picked) { picked = false; saveColor(k, input.value.toUpperCase()); } });
    grid.append(el("label", { class: "cap-color" }, input, el("span", { class: "small" }, label)));
  }
  box.append(grid);
  controls.append(box);
}

function liveColor(k, v) {
  S.configPending = true;
  S.config = S.config || { captionColors: Object.assign({}, DEFAULT_PALETTE) };
  S.config.captionColors = Object.assign({}, palette(), { [k]: v });
  const pal = palette();
  for (const s of spans) s.style.color = colorsFor(s._w.k, pal)[0];
  for (const d of voicesBox.querySelectorAll(".voice-dot")) d.style.background = colorsFor(d.dataset.k, pal)[0];
  emit("view");
}

async function saveColor(k, v) {
  liveColor(k, v);
  try { const r = await api.put("/api/config", { captionColors: { [k]: v } }); S.config = r; }
  catch (e) { toast("Couldn't save the color: " + e.message, true); }
  finally { S.configPending = false; }
}

async function resetColors() {
  try { S.config = await api.put("/api/config", { reset: true }); emit("config"); emit("view"); }
  catch (e) { toast("Couldn't reset the colors: " + e.message, true); }
}

// ---------------------------------------------------------------- the voices in this short

// [{asset, tr, voices: [{v, n}]}] for the recordings under this short's captions
function shortVoices() {
  const per = new Map();
  for (const ev of (S.doc && S.doc.captions.events) || []) {
    for (const w of ev.words) {
      if (!per.has(w.asset)) per.set(w.asset, new Map());
      const v = eventVoice(S.doc, lib, w);
      if (!v) continue;
      const m = per.get(w.asset);
      m.set(v.key, (m.get(v.key) || 0) + 1);
    }
  }
  const out = [];
  for (const [asset, counts] of per) {
    const tr = lib.transcript(asset);
    const all = (tr && tr.voices && tr.voices.speakers) || [];
    out.push({ asset, tr, voices: all.filter((v) => counts.has(v.key)).map((v) => ({ v, n: counts.get(v.key) })) });
  }
  return out;
}

function renderVoices() {
  clear(voicesBox);
  if (!S.doc || !(S.doc.captions.events || []).length) return;
  voicesBox.append(el("div", { class: "fx-label wide" }, "Voices in this short"));
  const pal = palette();
  for (const { asset, tr, voices } of shortVoices()) {
    const a = lib.asset(asset) || {};
    if (!tr || !tr.voices || tr.voices.state !== "ready") {
      const st = (a.stages || {}).speakers;
      const live = st && (st.state === "queued" || st.state === "running");
      const note = tr && tr.voices && tr.voices.state === "error" ? "The voice data couldn't be read (" + (tr.voices.error || "no reason given").slice(0, 120) + ")."
        : !st ? "No voice data for this recording: only recordings in the inbox get the voice split."
        : st.state === "error" ? "The voice split failed (" + (st.error || "no reason given").slice(0, 120) + "). Retry it from the bin."
        : live ? `The voices are being split (${Math.round((st.progress || 0) * 100)} %). The captions color in when it finishes.`
        : "The voices are ready; loading them.";
      voicesBox.append(el("div", { class: "voice-note small muted" + (live ? " is-live" : "") }, note));
      continue;
    }
    for (const { v, n } of voices) {
      const meta = [v.key === "me" ? "" : (GENDER[v.gender] || "not sure"), v.role && v.name !== roleName(v.role) ? roleName(v.role) : "",
        `${n} word${n === 1 ? "" : "s"}`, SOURCE[v.source] || ""].filter(Boolean).join(" · ");
      const row = el("div", { class: "voice-row", dataset: { key: v.key } },
        el("span", { class: "voice-dot", dataset: { k: v.cls }, style: { background: colorsFor(v.cls, pal)[0] } }),
        el("span", { class: "voice-name" }, v.name),
        el("span", { class: "voice-meta small muted" }, meta),
        v.key === "me" ? el("span", { class: "voice-hint", title: "Your voice can come in several parts. Right-click one of the words to fix a part that isn't you." }, icon("info"))
          : el("button", { class: "icon-btn small", type: "button", title: "Fix this voice", onclick: (e) => voiceMenu(e, asset, v, voices) }, icon("more_vert")));
      voicesBox.append(row);
    }
  }
}

function roleName(r) { return { gatekeeper: "Gatekeeper", owner: "Owner", service_rep: "Service rep", voicemail_greeting: "Voicemail greeting", phone_menu: "Phone menu" }[r] || ""; }

function voiceMenu(e, asset, v, voices) {
  const others = voices.filter((o) => o.v.key !== v.key);
  openMenu({ x: e.clientX, y: e.clientY }, [
    { label: "This is me", run: () => fix(asset, { groups: { [v.key]: { who: "me" } } }, `${v.name} is you now.`) },
    { label: "Woman", checked: v.gender === "woman", run: () => fix(asset, { groups: { [v.key]: { who: "other", gender: "woman" } } }, `${v.name} is a woman now.`) },
    { label: "Man", checked: v.gender === "man", run: () => fix(asset, { groups: { [v.key]: { who: "other", gender: "man" } } }, `${v.name} is a man now.`) },
    { label: "Same person as", disabled: !others.length, sub: others.map((o) => ({ label: o.v.name, run: () => fix(asset, { merge: { [v.key]: o.v.key } }, `${v.name} joined ${o.v.name}.`) })) },
    { sep: true },
    { label: "Reset to automatic", run: () => fix(asset, { groups: { [v.key]: null }, merge: { [v.key]: null } }, `${v.name} is back to automatic.`) },
  ]);
}

// ---------------------------------------------------------------- words: select and say who said them

function clickWord(e, idx) {
  const w = spans[idx]._w;
  if (e.shiftKey && anchor) {
    const a = spans.findIndex((s) => keyOf(s._w) === anchor);
    if (a >= 0) {
      const asset = spans[a]._w.asset;
      sel = new Set();
      for (let i = Math.min(a, idx); i <= Math.max(a, idx); i += 1) if (spans[i]._w.asset === asset) sel.add(keyOf(spans[i]._w));
      paintSel();
      return;
    }
  }
  anchor = keyOf(w);
  sel = new Set([anchor]);
  paintSel();
  pb.seek(w.s);
}

function paintSel() { for (const s of spans) s.classList.toggle("is-sel", sel.has(keyOf(s._w))); }

// who said generated words: saved on this short (G7), one undo step; null puts them back to automatic
function sayOnShort(asset, picked, vkey, msg) {
  history.commit("Said By", (d) => {
    const g = d.captions.gen && d.captions.gen[asset];
    if (!g) return { ok: false };
    for (const x of picked) {
      const gw = g.words[x.gi];
      if (!gw) continue;
      while (gw.length < 5) gw.push(null);
      if (vkey) gw[5] = vkey; else gw.length = 5;
    }
    return { ok: true };
  });
  toast(msg + " Saved on this short.");
}

function wordMenu(e, idx) {
  const w = spans[idx]._w;
  const key = keyOf(w);
  if (!sel.has(key)) { sel = new Set([key]); anchor = key; paintSel(); }
  const asset = w.asset;
  const picked = spans.map((s) => s._w).filter((x) => x.asset === asset && sel.has(keyOf(x)));
  const tr = lib.transcript(asset);
  const vo = tr && tr.voices;
  if (!vo || vo.state !== "ready") { toast("This recording has no voice data yet.", true); return; }
  const inShort = (shortVoices().find((x) => x.asset === asset) || { voices: [] }).voices;
  if (isGen(w)) {
    const gw = genWord(w);
    const g = gw && gw[4];
    const n = picked.length === 1 ? "this word" : `these ${picked.length} words`;
    const gens = picked.filter(isGen);
    openMenu({ x: e.clientX, y: e.clientY }, [
      { label: "Said by", sub: [
        { label: "You", run: () => sayOnShort(asset, gens, "me", `You said ${n}.`) },
        ...inShort.filter((o) => o.v.key !== "me").map((o) => ({ label: o.v.name, run: () => sayOnShort(asset, gens, o.v.key, `${o.v.name} said ${n}.`) })),
        { sep: true },
        { label: "Reset to automatic", run: () => sayOnShort(asset, gens, null, `${n[0].toUpperCase() + n.slice(1)} ${gens.length === 1 ? "is" : "are"} back to automatic.`) }] },
      { label: "This whole voice is", disabled: !g, sub: g ? wholeVoice(asset, g, inShort) : [] },
    ]);
    return;
  }
  const ids = picked.map((x) => x.id);
  const n = ids.length === 1 ? "this word" : `these ${ids.length} words`;
  const saidBy = [
    { label: "You", run: () => fix(asset, { words: Object.fromEntries(ids.map((i) => [i, "me"])) }, `You said ${n}.`) },
    ...inShort.filter((o) => o.v.key !== "me").map((o) => ({ label: o.v.name, run: () => fix(asset, { words: Object.fromEntries(ids.map((i) => [i, o.v.key])) }, `${o.v.name} said ${n}.`) })),
    { sep: true },
    { label: "New voice (woman)", run: () => fix(asset, { new_voice: { gender: "woman", words: ids } }, `A new voice (woman) said ${n}.`) },
    { label: "New voice (man)", run: () => fix(asset, { new_voice: { gender: "man", words: ids } }, `A new voice (man) said ${n}.`) },
    { sep: true },
    { label: "Reset to automatic", run: () => fix(asset, { words: Object.fromEntries(ids.map((i) => [i, null])) }, `${n[0].toUpperCase() + n.slice(1)} ${ids.length === 1 ? "is" : "are"} back to automatic.`) },
  ];
  // the word's own group from the split, so a part wrongly lumped into "You" (or anyone) can be fixed for good
  const ri = vo.raw ? vo.raw[w.id] : -1;
  const g = ri >= 0 ? vo.rawKeys[ri] : null;
  openMenu({ x: e.clientX, y: e.clientY }, [
    { label: "Said by", sub: saidBy },
    { label: "This whole voice is", disabled: !g, sub: g ? wholeVoice(asset, g, inShort) : [] },
  ]);
}

// a whole voice group's fix: saved on the recording, so every short (and every generated word) follows
function wholeVoice(asset, g, inShort) {
  return [
    { label: "Me", run: () => fix(asset, { groups: { [g]: { who: "me" } }, merge: { [g]: g } }, "That whole voice is you now.") },
    { label: "A woman", run: () => fix(asset, { groups: { [g]: { who: "other", gender: "woman" } }, merge: { [g]: g } }, "That whole voice is a woman now.") },
    { label: "A man", run: () => fix(asset, { groups: { [g]: { who: "other", gender: "man" } }, merge: { [g]: g } }, "That whole voice is a man now.") },
    { label: "Same person as", disabled: !inShort.length, sub: inShort.map((o) => ({ label: o.v.name, run: () => fix(asset, { merge: { [g]: o.v.key } }, `That whole voice joined ${o.v.name}.`) })) },
  ];
}

// a voice fix is saved on the recording; the captions regroup and recolor, and the short saves
async function fix(asset, body, msg) {
  try {
    const r = await api.patch(`/api/asset/${asset}/speakers`, body);
    lib.setVoices(asset, r);
    emit("transcript");
    flush();
    toast(msg + " Every short from this recording follows.");
  } catch (e) { toast(e.message, true); }
}

function fmt(f) { const s = Math.floor(f / 30); return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); }

function highlight() {
  if (!spans.length) return;
  const f = Math.floor(S.playhead);
  let lo = 0, hi = spans.length - 1, hit = null;
  while (lo <= hi) { const m = (lo + hi) >> 1; const w = spans[m]._w; if (w.e <= f) lo = m + 1; else if (w.s > f) hi = m - 1; else { hit = spans[m]; break; } }
  if (hit === lastActive) return;
  if (lastActive) lastActive.classList.remove("is-active");
  if (hit) { hit.classList.add("is-active"); if (S.playing) hit.scrollIntoView({ block: "nearest" }); }
  lastActive = hit;
}

function editWord(span, w) {
  const gw = genWord(w);
  span.contentEditable = "true";
  span.textContent = gw ? gw[2] : lib.transcript(w.asset) ? lib.transcript(w.asset).words[w.id][2] : w.w;
  span.focus();
  document.getSelection().selectAllChildren(span);
  const done = async (commit) => {
    span.contentEditable = "false";
    span.removeEventListener("keydown", key);
    span.removeEventListener("blur", blur);
    const text = span.textContent.trim();
    if (!commit || !text) { render(); return; }
    if (gw) {        // a generated word: the fix is saved on this short (G7), one undo step
      if (text === gw[2]) { render(); return; }
      history.commit("Fix Caption Word", (d) => { const x = genWord(w, d); if (x) x[2] = text.slice(0, 80); });
      toast("Word fixed on this short.");
      return;
    }
    try {
      const r = await api.patch(`/api/asset/${w.asset}/transcript`, { edits: { [w.id]: text } });
      lib.setWord(w.asset, w.id, text);
      lib.setTrev(w.asset, r.trev);
      emit("transcript");
      emit("doc");
      toast("Word fixed on the recording's transcript.");
    } catch (e) { toast(e.message, true); render(); }
  };
  const key = (e) => { e.stopPropagation(); if (e.key === "Enter") { e.preventDefault(); done(true); } if (e.key === "Escape") done(false); };
  const blur = () => done(true);
  span.addEventListener("keydown", key);
  span.addEventListener("blur", blur);
}
