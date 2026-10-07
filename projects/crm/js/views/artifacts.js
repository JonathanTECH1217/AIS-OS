// Records, Artifacts (Jonathan, 2026-10-02: "add artifacts on the left side of the record section, including the
// offering PDF, sales script, just cold email scripts, LinkedIn connection messages. This should also be segmented by
// categories that they're used for, I guess, by icon"). One section per use, each with its icon, from
// projects/crm/artifacts.json; a chip row on top shows one category at a time. A click opens the item read-only on the
// right (text, picture, or PDF). Something not written yet shows in yellow.
import { el } from "../util.js";
import { api } from "../api.js";
import { MARKS } from "../components/journey.js";
import { artifactViewer, groupBox } from "../components/artifact-view.js";

const ICONS = {
  offer: { logo: '<rect width="24" height="24" rx="5" fill="#137333"/><path fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linejoin="round" d="M7 4.5h7l3.5 3.5v11.5H7z"/><path fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round" d="M14 4.5V8h3.5M9.5 12h5M9.5 15h5"/>' },
  calls: MARKS.cold,
  email: MARKS["cold-email"],
  linkedin: MARKS["linkedin-inmail"],
  ads: MARKS["google-ads"],
};

function tile(key, size) {
  const m = ICONS[key] || ICONS.offer;
  const b = el("span", { class: "ch-logo", "aria-hidden": "true", style: `width:${size}px;height:${size}px` });
  b.innerHTML = `<svg viewBox="${m.viewBox || "0 0 24 24"}" width="${size}" height="${size}">${m.logo}</svg>`;
  return b;
}

// ready: items present; missing: groups with nothing in them yet; todo: open boxes in tasks.md that name a group's file
function counts(cat) {
  let ready = 0, missing = 0;
  const todo = new Set();  // one box can name two groups' files; it counts once
  for (const g of cat.groups || []) {
    const n = (g.items || []).length + (g.messages || []).length + (g.campaigns || []).length + (g.pages || []).length + (g.listings || []).length;
    if (n) ready += n; else missing += 1;
    (g.tasks || []).forEach((t) => todo.add(t.line));
  }
  return { ready, missing, todo: todo.size };
}

export async function renderArtifacts(root) {
  const data = await api.get("/api/artifacts");
  const cats = data.categories || [];
  const v = artifactViewer("Pick an item on the left to read it here.");
  const list = el("div", { class: "jr-alist art-list" });
  let pick = "all";

  const chips = el("div", { class: "row art-chips" });
  function paint() {
    chips.replaceChildren(
      el("button", { class: "chip" + (pick === "all" ? " is-on" : ""), type: "button", onclick: () => { pick = "all"; paint(); } }, "All"),
      ...cats.map((c) => { const n = counts(c); return el("button", { class: "chip" + (pick === c.key ? " is-on" : ""), type: "button", onclick: () => { pick = c.key; paint(); } },
        tile(c.icon, 18), c.label, el("span", { class: "muted num", style: "font-size:12px" },
          [String(n.ready), n.missing ? `${n.missing} to write` : "", n.todo ? `${n.todo} to do` : ""].filter(Boolean).join(" · "))); }));
    list.replaceChildren(...cats.filter((c) => pick === "all" || pick === c.key).map((c) => el("section", { class: "art-cat" },
      el("div", { class: "row art-cat-head" }, tile(c.icon, 32),
        el("div", { class: "grow" }, el("h2", {}, c.label), el("div", { class: "muted", style: "font-size:12px" }, c.use || ""))),
      ...(c.groups || []).map((g) => groupBox(g, v)))));
  }
  paint();

  root.append(
    el("div", { class: "head" },
      el("div", {}, el("div", { class: "label" }, "Records"), el("h1", {}, "Artifacts"),
        el("div", { class: "sub" }, "What the selling runs on, grouped by what it is used for. Click an item to read it here. Yellow means it is not written yet. To do is an open box in tasks.md that names the file; click it to read the whole box."))),
    chips,
    el("div", { class: "jr-split art-split" }, list, v.viewer));
}
